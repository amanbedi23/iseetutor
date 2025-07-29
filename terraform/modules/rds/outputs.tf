output "db_instance_id" {
  description = "The RDS instance ID"
  value       = aws_db_instance.main.id
}

output "db_instance_endpoint" {
  description = "The connection endpoint"
  value       = aws_db_instance.main.endpoint
}

output "db_instance_address" {
  description = "The hostname of the RDS instance"
  value       = aws_db_instance.main.address
}

output "db_instance_port" {
  description = "The database port"
  value       = aws_db_instance.main.port
}

output "db_instance_name" {
  description = "The database name"
  value       = aws_db_instance.main.db_name
}

output "db_instance_username" {
  description = "The master username"
  value       = aws_db_instance.main.username
  sensitive   = true
}

output "db_password_ssm_parameter_name" {
  description = "The SSM parameter name for the database password"
  value       = aws_ssm_parameter.db_password.name
}

output "db_security_group_id" {
  description = "The security group ID for the database"
  value       = aws_security_group.rds.id
}

output "read_replica_endpoint" {
  description = "The read replica endpoint (if created)"
  value       = var.create_read_replica && var.environment == "prod" ? aws_db_instance.read_replica[0].endpoint : null
}

output "database_url" {
  description = "PostgreSQL connection URL"
  value       = "postgresql://${aws_db_instance.main.username}:${random_password.db_password.result}@${aws_db_instance.main.endpoint}/${aws_db_instance.main.db_name}"
  sensitive   = true
}

output "database_url_ssm_arn" {
  description = "ARN of the SSM parameter containing the database URL"
  value       = aws_ssm_parameter.db_url.arn
}