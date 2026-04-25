# Infra: Main Definition for Frontend (AWS Cloud).

terraform {
  required_version = ">= 1.6.0"
  backend "s3" {}

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

locals {
  project   = "splitwise-lite"
  prefix    = "${local.project}-${var.environment_name}"
  component = "frontend"

  common_tags = {
    Project      = local.project
    Environment  = var.environment_name
    Component    = local.component
    ManagedBy    = "terraform"
    CostCenter   = "Devops-Eafit"
    SupportEmail = "shiguitau1@eafit.edu.co : icamayaa@eafit.edu.co : sarozos@eafit.edu.co : soviedop@eafit.edu.co"
  }
}

# -------------------- Referencias a recursos de base ---------------
data "aws_ecs_cluster" "main" {
  cluster_name = "${local.prefix}-ecs-cluster"
}

data "aws_lb" "main" {
  name = "${local.prefix}-alb"
}

data "aws_lb_listener" "http" {
  load_balancer_arn = data.aws_lb.main.arn
  port              = 80
}

data "aws_security_group" "alb_sg" {
  name   = "${local.prefix}-alb-sg"
  vpc_id = var.vpc_id
}

# -------------------- Grupo de Logs para ECS -----------------------
resource "aws_cloudwatch_log_group" "ecs_logs" {
  name              = "/ecs/${local.prefix}-${local.component}-task"
  retention_in_days = 365 # CKV_AWS_338: retención mínima de 1 año
  #checkov:skip=CKV_AWS_158:Encriptación KMS requiere CMK dedicada, fuera del alcance académico
  tags = local.common_tags
}

# -------------------- Security Group del ECS -----------------------
# Solo acepta tráfico del ALB en el puerto 80 (nginx)
resource "aws_security_group" "ecs_sg" {
  #checkov:skip=CKV_AWS_382:Egress abierto requerido para que Fargate descargue imagenes de Docker Hub
  name        = "${local.prefix}-${local.component}-ecs-sg"
  description = "Permite trafico desde el ALB al servicio ECS frontend"
  vpc_id      = var.vpc_id

  ingress {
    description     = "Trafico desde el ALB"
    from_port       = 8080
    to_port         = 8080
    protocol        = "tcp"
    security_groups = [data.aws_security_group.alb_sg.id]
  }

  egress {
    description = "Permite trafico de salida para descargar imagenes y DNS"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = local.common_tags
}

# -------------------- Target Group ---------------------------------
resource "aws_lb_target_group" "ecs_tg" {
  #checkov:skip=CKV_AWS_378:HTTPS interno requiere certificado ACM, fuera del alcance académico
  name        = "${local.prefix}-fe-tg"
  port        = 8080
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"

  health_check {
    enabled             = true
    path                = "/"
    port                = "8080"
    protocol            = "HTTP"
    healthy_threshold   = 2
    unhealthy_threshold = 2
    interval            = 15
    timeout             = 5
    matcher             = "200"
  }

  tags = local.common_tags
}

# -------------------- Listener Rule --------------------------------
# Enruta todo lo que no sea /api/* al frontend (catch-all, prioridad baja)
resource "aws_lb_listener_rule" "frontend" {
  listener_arn = data.aws_lb_listener.http.arn
  priority     = 200

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.ecs_tg.arn
  }

  condition {
    path_pattern {
      values = ["/*"]
    }
  }
}

# -------------------- Task Definition ------------------------------
resource "aws_ecs_task_definition" "app" {
  family                   = "${local.prefix}-${local.component}-task"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = "256"
  memory                   = "512"
  task_role_arn            = var.lab_role_arn
  execution_role_arn       = var.lab_role_arn
  #checkov:skip=CKV_AWS_249:AWS Academy solo provee un LabRole, no es posible separar task y execution roles (NO TENEMOS PERMISOS)
  #checkov:skip=CKV_AWS_336:Nginx requiere escribir en /var/cache/nginx y /var/run, no compatible con readonlyRootFilesystem

  container_definitions = jsonencode([
    {
      name      = "${local.prefix}-${local.component}-container"
      image     = var.docker_image_uri

      portMappings = [
        {
          containerPort = 8080
          protocol      = "tcp"
        }
      ]

      environment = [
        {
          name  = "COMPONENT"
          value = local.component
        },
        {
          name  = "APP_ENV"
          value = var.environment_name
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.ecs_logs.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "ecs"
        }
      }
    }
  ])

  tags = local.common_tags
}

# -------------------- ECS Service ----------------------------------
resource "aws_ecs_service" "main" {
  #checkov:skip=CKV_AWS_333:IP pública requerida en subnets públicas de AWS Academy (no hay NAT Gateway)
  name            = "${local.prefix}-${local.component}-service"
  cluster         = data.aws_ecs_cluster.main.arn
  task_definition = aws_ecs_task_definition.app.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.subnet_ids
    security_groups  = [aws_security_group.ecs_sg.id]
    assign_public_ip = true
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.ecs_tg.arn
    container_name   = "${local.prefix}-${local.component}-container"
    container_port   = 8080
  }

  deployment_minimum_healthy_percent = 50
  deployment_maximum_percent         = 200

  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }

  lifecycle {
    ignore_changes = [desired_count]
  }

  depends_on = [aws_lb_listener_rule.frontend]

  tags = local.common_tags
}
