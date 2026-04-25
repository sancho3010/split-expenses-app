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
  project = "splitwise-lite"
  prefix  = "${local.project}-${var.environment_name}"

  common_tags = {
    Project      = local.project
    Environment  = var.environment_name
    Component    = "base"
    ManagedBy    = "terraform"
    CostCenter   = "Devops-Eafit"
    SupportEmail = "shiguitau1@eafit.edu.co : icamayaa@eafit.edu.co : sarozos@eafit.edu.co : soviedop@eafit.edu.co"
  }
}

# -------------------- ECS Cluster compartido -----------------------
resource "aws_ecs_cluster" "main" {
  #checkov:skip=CKV_AWS_65:Container Insights genera costos adicionales, fuera del alcance académico
  name = "${local.prefix}-ecs-cluster"
  tags = local.common_tags
}

# -------------------- Security Group del ALB -----------------------
resource "aws_security_group" "alb_sg" {
  #checkov:skip=CKV_AWS_260:El ALB es público y debe aceptar HTTP en puerto 80 desde internet
  #checkov:skip=CKV_AWS_382:Egress abierto requerido para que el ALB se comunique con los targets
  name        = "${local.prefix}-alb-sg"
  description = "Permite trafico HTTP al ALB"
  vpc_id      = var.vpc_id

  ingress {
    description = "HTTP desde internet"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "Permite trafico de salida para conectividad de red"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = local.common_tags
}

# -------------------- Application Load Balancer --------------------
resource "aws_lb" "main" {
  #checkov:skip=CKV_AWS_131:drop_invalid_header_fields ya está habilitado
  #checkov:skip=CKV_AWS_150:Deletion protection deshabilitada para facilitar destroy en entorno académico
  #checkov:skip=CKV_AWS_91:Access logging requiere bucket S3 dedicado, fuera del alcance académico
  #checkov:skip=CKV2_AWS_20:HTTPS requiere certificado ACM, no disponible en AWS Academy
  #checkov:skip=CKV2_AWS_28:WAF no disponible en AWS Academy
  name                       = "${local.prefix}-alb"
  internal                   = false
  load_balancer_type         = "application"
  security_groups            = [aws_security_group.alb_sg.id]
  subnets                    = var.subnet_ids
  drop_invalid_header_fields = true

  tags = local.common_tags
}

# -------------------- Listener HTTP --------------------------------
# Regla por defecto: 404 — cada componente agrega sus propias reglas
resource "aws_lb_listener" "http" {
  #checkov:skip=CKV_AWS_2:HTTPS requiere certificado ACM, no disponible en AWS Academy
  #checkov:skip=CKV_AWS_103:TLS requiere certificado ACM, no disponible en AWS Academy
  load_balancer_arn = aws_lb.main.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type = "fixed-response"
    fixed_response {
      content_type = "text/plain"
      message_body = "Not found"
      status_code  = "404"
    }
  }
}

# -------------------- Security Group del ECS Backend ---------------
# Vive en base/ (no en backend/) para evitar dependencia circular:
# database necesita este sg para restringir acceso al RDS,
# pero database se despliega antes que backend.
resource "aws_security_group" "ecs_backend_sg" {
  #checkov:skip=CKV_AWS_382:Egress abierto requerido para que ECS backend descargue imagenes y se comunique con RDS
  #checkov:skip=CKV2_AWS_5:Este SG se usa en backend/infra via data source, Checkov no detecta referencias cross-module
  name        = "${local.prefix}-backend-ecs-sg"
  description = "Permite trafico desde el ALB al servicio ECS backend"
  vpc_id      = var.vpc_id

  ingress {
    description     = "Trafico desde el ALB"
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb_sg.id]
  }

  egress {
    description = "Permite trafico de salida para conectividad de red"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = local.common_tags
}
