output "alb_arn" {
  description = "ARN del ALB compartido"
  value       = aws_lb.main.arn
}

output "alb_dns_name" {
  description = "DNS Name del ALB compartido"
  value       = aws_lb.main.dns_name
}

output "alb_url" {
  description = "URL completa del ALB (con http://)"
  value       = "http://${aws_lb.main.dns_name}"
}

output "alb_listener_arn" {
  description = "ARN del listener HTTP — backend y frontend agregan sus reglas aquí"
  value       = aws_lb_listener.http.arn
}

output "alb_sg_id" {
  description = "ID del security group del ALB — backend y frontend lo referencian en sus ECS sg"
  value       = aws_security_group.alb_sg.id
}

output "ecs_cluster_name" {
  description = "Nombre del ECS cluster compartido"
  value       = aws_ecs_cluster.main.name
}

output "ecs_cluster_arn" {
  description = "ARN del ECS cluster compartido"
  value       = aws_ecs_cluster.main.arn
}

output "ecs_backend_sg_id" {
  description = "ID del security group del ECS backend — usado por database para restringir acceso al RDS"
  value       = aws_security_group.ecs_backend_sg.id
}
