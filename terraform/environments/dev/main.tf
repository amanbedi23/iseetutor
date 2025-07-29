# ISEE Tutor Development Environment Infrastructure

# Backend configuration moved to backend.tf for Terraform Cloud

provider "aws" {
  region = var.region

  default_tags {
    tags = local.common_tags
  }
}

locals {
  environment = "dev"
  
  common_tags = {
    Project     = var.project_name
    Environment = local.environment
    ManagedBy   = "Terraform"
    CreatedAt   = timestamp()
  }
}

# VPC Module
module "vpc" {
  source = "../../modules/vpc"

  project_name          = var.project_name
  environment           = local.environment
  region               = var.region
  vpc_cidr             = "10.0.0.0/16"
  public_subnet_cidrs  = ["10.0.1.0/24", "10.0.2.0/24"]
  private_subnet_cidrs = ["10.0.10.0/24", "10.0.20.0/24"]
  database_subnet_cidrs = ["10.0.30.0/24", "10.0.40.0/24"]
  availability_zones   = data.aws_availability_zones.available.names
  tags                 = local.common_tags
}

# S3 Bucket for application storage
module "s3" {
  source = "../../modules/s3"

  project_name = var.project_name
  environment  = local.environment
  tags         = local.common_tags
}

# IAM Module
module "iam" {
  source = "../../modules/iam"

  project_name = var.project_name
  environment  = local.environment
  region       = var.region
  tags         = local.common_tags
}

# Security Group for ALB
resource "aws_security_group" "alb" {
  name_prefix = "${var.project_name}-${local.environment}-alb-"
  vpc_id      = module.vpc.vpc_id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, {
    Name = "${var.project_name}-${local.environment}-alb-sg"
  })
}

# Application Load Balancer
module "alb" {
  source = "../../modules/alb"

  project_name       = var.project_name
  environment        = local.environment
  vpc_id            = module.vpc.vpc_id
  public_subnet_ids = module.vpc.public_subnet_ids
  security_group_id = aws_security_group.alb.id
  certificate_arn   = var.certificate_arn
  domain_name       = var.domain_name
  route53_zone_id   = var.route53_zone_id
  logs_bucket_name  = module.s3.logs_bucket_id
  tags              = local.common_tags
}

# ECS Cluster
module "ecs" {
  source = "../../modules/ecs"

  project_name               = var.project_name
  environment                = local.environment
  region                     = var.region
  vpc_id                     = module.vpc.vpc_id
  private_subnet_ids         = module.vpc.private_subnet_ids
  alb_security_group_id      = aws_security_group.alb.id
  backend_target_group_arn   = module.alb.backend_target_group_arn
  frontend_target_group_arn  = module.alb.frontend_target_group_arn
  alb_listener_arn          = module.alb.https_listener_arn
  alb_dns_name              = module.alb.alb_dns_name
  ecr_repository_url        = module.iam.ecr_repository_url
  s3_bucket_arn             = module.s3.bucket_arn
  
  # Task configuration
  backend_cpu               = "512"
  backend_memory            = "1024"
  backend_desired_count     = 2
  frontend_cpu              = "256"
  frontend_memory           = "512"
  frontend_desired_count    = 2
  
  # Image tags
  backend_image_tag         = var.backend_image_tag
  frontend_image_tag        = var.frontend_image_tag
  
  # Ports
  backend_port              = 8000
  
  # SSM Parameters
  database_url_ssm_arn      = module.rds.database_url_ssm_arn
  redis_url_ssm_arn         = module.redis.redis_url_ssm_arn
  openai_api_key_ssm_arn    = aws_ssm_parameter.openai_api_key.arn
  google_cloud_key_ssm_arn  = aws_ssm_parameter.google_cloud_key.arn
  aws_access_key_id_ssm_arn = aws_ssm_parameter.aws_access_key_id.arn
  aws_secret_access_key_ssm_arn = aws_ssm_parameter.aws_secret_access_key.arn
  pinecone_api_key_ssm_arn  = aws_ssm_parameter.pinecone_api_key.arn
  
  enable_container_insights = true
  tags                      = local.common_tags
}

# RDS PostgreSQL
module "rds" {
  source = "../../modules/rds"

  project_name          = var.project_name
  environment           = local.environment
  vpc_id                = module.vpc.vpc_id
  database_subnet_ids   = module.vpc.database_subnet_ids
  app_security_group_id = module.ecs.ecs_tasks_security_group_id
  
  # Database configuration
  db_instance_class     = "db.t3.micro"
  db_allocated_storage  = 20
  db_name              = "iseetutor"
  db_username          = "iseetutor_admin"
  
  enable_monitoring     = true
  create_read_replica   = false
  sns_topic_arn        = module.monitoring.sns_topic_arn
  tags                 = local.common_tags
}

# ElastiCache Redis
module "redis" {
  source = "../../modules/redis"

  project_name          = var.project_name
  environment           = local.environment
  vpc_id                = module.vpc.vpc_id
  private_subnet_ids    = module.vpc.private_subnet_ids
  app_security_group_id = module.ecs.ecs_tasks_security_group_id
  
  # Redis configuration
  redis_node_type       = "cache.t3.micro"
  redis_num_cache_nodes = 1
  auth_token_enabled    = true
  transit_encryption_enabled = true
  
  enable_monitoring     = true
  sns_topic_arn        = module.monitoring.sns_topic_arn
  tags                 = local.common_tags
}

# Monitoring
module "monitoring" {
  source = "../../modules/monitoring"

  project_name     = var.project_name
  environment      = local.environment
  alarm_email      = var.alarm_email
  ecs_cluster_name = module.ecs.cluster_name
  tags             = local.common_tags
}

# Data sources
data "aws_availability_zones" "available" {
  state = "available"
}

# SSM Parameters for secrets
resource "aws_ssm_parameter" "openai_api_key" {
  name  = "/${var.project_name}/${local.environment}/openai-api-key"
  type  = "SecureString"
  value = var.openai_api_key
  tags  = local.common_tags
}

resource "aws_ssm_parameter" "google_cloud_key" {
  name  = "/${var.project_name}/${local.environment}/google-cloud-key"
  type  = "SecureString"
  value = var.google_cloud_key
  tags  = local.common_tags
}

resource "aws_ssm_parameter" "aws_access_key_id" {
  name  = "/${var.project_name}/${local.environment}/aws-access-key-id"
  type  = "SecureString"
  value = var.aws_access_key_id_for_services
  tags  = local.common_tags
}

resource "aws_ssm_parameter" "aws_secret_access_key" {
  name  = "/${var.project_name}/${local.environment}/aws-secret-access-key"
  type  = "SecureString"
  value = var.aws_secret_access_key_for_services
  tags  = local.common_tags
}

resource "aws_ssm_parameter" "pinecone_api_key" {
  name  = "/${var.project_name}/${local.environment}/pinecone-api-key"
  type  = "SecureString"
  value = var.pinecone_api_key
  tags  = local.common_tags
}