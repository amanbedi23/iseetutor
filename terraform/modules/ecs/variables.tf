# Variables for ECS Module

variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
}

variable "region" {
  description = "AWS region"
  type        = string
}

variable "vpc_id" {
  description = "ID of the VPC"
  type        = string
}

variable "private_subnet_ids" {
  description = "List of private subnet IDs for ECS tasks"
  type        = list(string)
}

variable "alb_security_group_id" {
  description = "Security group ID of the ALB"
  type        = string
}

variable "backend_target_group_arn" {
  description = "ARN of the backend target group"
  type        = string
}

variable "frontend_target_group_arn" {
  description = "ARN of the frontend target group"
  type        = string
}

variable "alb_listener_arn" {
  description = "ARN of the ALB HTTPS listener"
  type        = string
}

variable "alb_dns_name" {
  description = "DNS name of the ALB"
  type        = string
}

variable "backend_ecr_repository_url" {
  description = "URL of the backend ECR repository"
  type        = string
}

variable "frontend_ecr_repository_url" {
  description = "URL of the frontend ECR repository"
  type        = string
}

variable "s3_bucket_arn" {
  description = "ARN of the S3 bucket"
  type        = string
}

# Task configuration
variable "backend_cpu" {
  description = "CPU units for backend task"
  type        = string
  default     = "512"
}

variable "backend_memory" {
  description = "Memory for backend task"
  type        = string
  default     = "1024"
}

variable "backend_desired_count" {
  description = "Desired number of backend tasks"
  type        = number
  default     = 2
}

variable "frontend_cpu" {
  description = "CPU units for frontend task"
  type        = string
  default     = "256"
}

variable "frontend_memory" {
  description = "Memory for frontend task"
  type        = string
  default     = "512"
}

variable "frontend_desired_count" {
  description = "Desired number of frontend tasks"
  type        = number
  default     = 2
}

# Image tags
variable "backend_image_tag" {
  description = "Docker image tag for backend"
  type        = string
  default     = "latest"
}

variable "frontend_image_tag" {
  description = "Docker image tag for frontend"
  type        = string
  default     = "latest"
}

# Ports
variable "backend_port" {
  description = "Port for backend container"
  type        = number
  default     = 8000
}

# SSM Parameters
variable "database_url_ssm_arn" {
  description = "ARN of SSM parameter for database URL"
  type        = string
}

variable "redis_url_ssm_arn" {
  description = "ARN of SSM parameter for Redis URL"
  type        = string
}

variable "openai_api_key_ssm_arn" {
  description = "ARN of SSM parameter for OpenAI API key"
  type        = string
}

variable "google_cloud_key_ssm_arn" {
  description = "ARN of SSM parameter for Google Cloud key"
  type        = string
}

variable "aws_access_key_id_ssm_arn" {
  description = "ARN of SSM parameter for AWS access key ID"
  type        = string
}

variable "aws_secret_access_key_ssm_arn" {
  description = "ARN of SSM parameter for AWS secret access key"
  type        = string
}

variable "pinecone_api_key_ssm_arn" {
  description = "ARN of SSM parameter for Pinecone API key"
  type        = string
}

# Other settings
variable "enable_container_insights" {
  description = "Enable CloudWatch Container Insights"
  type        = bool
  default     = true
}

variable "app_environment_variables" {
  description = "Additional environment variables for the application"
  type        = map(string)
  default     = {}
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}