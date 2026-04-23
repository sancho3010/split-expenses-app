output "ecs_service_name" {
  description = "Nombre del ECS Service del frontend"
  value       = aws_ecs_service.main.name
}

output "ecs_service_arn" {
  description = "ARN del ECS Service del frontend"
  value       = aws_ecs_service.main.id
}
