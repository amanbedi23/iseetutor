variable "project_name" {
  default = "iseetutor"
}

variable "region" {
  default = "us-east-1"
}

variable "domain_name" {
  description = "Domain name for the application"
  type        = string
  default     = ""
}

variable "certificate_arn" {
  description = "ACM certificate ARN"
  type        = string
  default     = ""
}

variable "route53_zone_id" {
  description = "Route53 hosted zone ID"
  type        = string
  default     = ""
}

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

variable "alarm_email" {
  description = "Email for CloudWatch alarms"
  type        = string
  default     = ""
}

# Sensitive variables - should be provided via environment variables or terraform.tfvars
variable "openai_api_key" {
  description = "OpenAI API key"
  type        = string
  sensitive   = true
}

variable "google_cloud_key" {
  description = "Google Cloud service account key"
  type        = string
  sensitive   = true
}

variable "aws_access_key_id_for_services" {
  description = "AWS access key for services"
  type        = string
  sensitive   = true
}

variable "aws_secret_access_key_for_services" {
  description = "AWS secret key for services"
  type        = string
  sensitive   = true
}

variable "pinecone_api_key" {
  description = "Pinecone API key"
  type        = string
  sensitive   = true
}