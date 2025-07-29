output "redis_endpoint" {
  description = "Redis primary endpoint"
  value       = aws_elasticache_replication_group.redis.primary_endpoint_address
}

output "redis_port" {
  description = "Redis port"
  value       = 6379
}

output "redis_configuration_endpoint" {
  description = "Redis configuration endpoint"
  value       = aws_elasticache_replication_group.redis.configuration_endpoint_address
}

output "redis_security_group_id" {
  description = "Security group ID for Redis"
  value       = aws_security_group.redis.id
}

output "redis_auth_token_ssm_parameter_name" {
  description = "SSM parameter name for Redis auth token"
  value       = var.auth_token_enabled ? aws_ssm_parameter.redis_auth_token[0].name : null
}

output "redis_url" {
  description = "Redis connection URL"
  value = var.auth_token_enabled ? (
    "redis://:${random_password.redis_auth_token[0].result}@${aws_elasticache_replication_group.redis.primary_endpoint_address}:6379/0"
  ) : (
    "redis://${aws_elasticache_replication_group.redis.primary_endpoint_address}:6379/0"
  )
  sensitive = true
}

output "redis_url_ssm_arn" {
  description = "ARN of the SSM parameter containing the Redis URL"
  value       = aws_ssm_parameter.redis_url.arn
}