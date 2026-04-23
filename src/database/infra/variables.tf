
# infra rebuild trigger v2
variable "environment_name" {
  description = "Nombre del entorno (ej: staging, production). Usado para nombrar recursos."
  type        = string
  validation {
    condition     = contains(["staging", "production"], var.environment_name)
    error_message = "El entorno debe ser 'staging' o 'production'."
  }
}

variable "lab_role_arn" {
  description = "ARN completo del rol IAM 'LabRole' existente en la cuenta."
  type        = string
}

variable "vpc_id" {
  description = "ID de la VPC por defecto donde desplegar."
  type        = string
}

variable "subnet_ids" {
  description = "Lista de al menos DOS IDs de subredes públicas de la VPC por defecto en diferentes AZs."
  type        = list(string)
}

variable "aws_region" {
  description = "Región de AWS a usar."
  type        = string
  default     = "us-east-1"
}

variable "db_username" {
  description = "Usuario de la BD. Es sensible."
  type        = string
  sensitive   = true
}

variable "db_password" {
  description = "Contraseña de la BD. Es sensible."
  type        = string
  sensitive   = true
}

variable "backend_ecs_sg_id" {
  description = "ID del Security Group del ECS backend, para restringir acceso al RDS."
  type        = string
}