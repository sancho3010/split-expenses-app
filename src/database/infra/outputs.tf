# Outputs for Database

output "db_endpoint" {
  description = "Endpoint del RDS — usado como DATABASE_URL en el backend"
  value       = aws_db_instance.main.endpoint
}

output "db_name" {
  description = "Nombre de la base de datos"
  value       = aws_db_instance.main.db_name
}
