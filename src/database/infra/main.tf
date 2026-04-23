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
  component = "database"

  common_tags = {
    Project      = local.project
    Environment  = var.environment_name
    Component    = local.component
    ManagedBy    = "terraform"
    CostCenter   = "Devops-Eafit"
    SupportEmail = "shiguitau1@eafit.edu.co, icamayaa@eafit.edu.co, sarozos@eafit.edu.co, soviedop@eafit.edu.co"
  }
}

# -------------------- Security Group del RDS -----------------------
# Solo acepta tráfico del ECS backend en el puerto 5432
resource "aws_security_group" "rds_sg" {
  name        = "${local.prefix}-${local.component}-sg"
  description = "Permite trafico al RDS solo desde el ECS backend"
  vpc_id      = var.vpc_id

  ingress {
    description     = "PostgreSQL desde el ECS backend"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [var.backend_ecs_sg_id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = local.common_tags
}

# -------------------- Subnet Group para RDS ------------------------
# RDS requiere subnets en al menos 2 AZs
resource "aws_db_subnet_group" "main" {
  name       = "${local.prefix}-${local.component}-subnet-group"
  subnet_ids = var.subnet_ids

  tags = local.common_tags
}

# -------------------- RDS PostgreSQL -------------------------------
resource "aws_db_instance" "main" {
  identifier        = "${local.prefix}-${local.component}"
  engine            = "postgres"
  engine_version    = "16"
  instance_class    = "db.t3.micro"  # Minimo disponible en AWS Academy
  allocated_storage = 20             # GB minimo

  db_name  = "splitwise"
  username = var.db_username
  password = var.db_password

  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds_sg.id]

  publicly_accessible = false  # No expuesto a internet
  skip_final_snapshot = true   # Para facilitar destroy en entorno academico

  tags = local.common_tags
}
