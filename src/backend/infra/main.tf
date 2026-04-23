# Infra: Main Definition

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
  component = "backend"

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
# El cluster, ALB y su security group son creados por infra/base
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
  retention_in_days = 14
  tags              = local.common_tags
}

# -------------------- Security Group del ECS -----------------------
# Creado en base/ para evitar dependencia circular con database.
# Solo acepta tráfico del ALB en el puerto 8000.
data "aws_security_group" "ecs_sg" {
  name   = "${local.prefix}-backend-ecs-sg"
  vpc_id = var.vpc_id
}

# -------------------- Target Group ---------------------------------
resource "aws_lb_target_group" "ecs_tg" {
  name        = "${local.prefix}-be-tg"
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"

  health_check {
    enabled             = true
    path                = "/health"
    port                = "8000"
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
# Enruta /api/* al backend
resource "aws_lb_listener_rule" "backend" {
  listener_arn = data.aws_lb_listener.http.arn
  priority     = 100

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.ecs_tg.arn
  }

  condition {
    path_pattern {
      values = ["/api/*", "/health"]
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

  container_definitions = jsonencode([
    {
      name  = "${local.prefix}-${local.component}-container"
      image = var.docker_image_uri

      portMappings = [
        {
          containerPort = 8000
          protocol      = "tcp"
        }
      ]

      environment = [
        {
          name  = "COMPONENT"
          value = local.component
        },
        {
          name  = "DATABASE_URL"
          value = var.database_url
        },
        {
          name  = "APP_ENV"
          value = var.environment_name
        },
        {
          name  = "CORS_ORIGINS"
          value = jsonencode(var.cors_origins)
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
  name            = "${local.prefix}-${local.component}-service"
  cluster         = data.aws_ecs_cluster.main.arn
  task_definition = aws_ecs_task_definition.app.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.subnet_ids
    security_groups  = [data.aws_security_group.ecs_sg.id]
    assign_public_ip = true
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.ecs_tg.arn
    container_name   = "${local.prefix}-${local.component}-container"
    container_port   = 8000
  }

  deployment_minimum_healthy_percent = 50
  deployment_maximum_percent         = 200

  lifecycle {
    ignore_changes = [desired_count]
  }

  depends_on = [aws_lb_listener_rule.backend]

  tags = local.common_tags
}
