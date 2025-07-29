# IAM Module for ISEE Tutor

# Use existing ECR repositories
data "aws_ecr_repository" "backend" {
  name = "${var.project_name}-${var.environment}-backend"
}

data "aws_ecr_repository" "frontend" {
  name = "${var.project_name}-${var.environment}-frontend"
}

# If you need to create the repositories when they don't exist, uncomment below:
# resource "aws_ecr_repository" "backend" {
#   count                = var.create_ecr_repos ? 1 : 0
#   name                 = "${var.project_name}-${var.environment}-backend"
#   image_tag_mutability = "MUTABLE"
# 
#   image_scanning_configuration {
#     scan_on_push = true
#   }
# 
#   encryption_configuration {
#     encryption_type = "AES256"
#   }
# 
#   tags = var.tags
# }
# 
# resource "aws_ecr_repository" "frontend" {
#   count                = var.create_ecr_repos ? 1 : 0
#   name                 = "${var.project_name}-${var.environment}-frontend"
#   image_tag_mutability = "MUTABLE"
# 
#   image_scanning_configuration {
#     scan_on_push = true
#   }
# 
#   encryption_configuration {
#     encryption_type = "AES256"
#   }
# 
#   tags = var.tags
# }

# ECR Lifecycle Policy
resource "aws_ecr_lifecycle_policy" "backend" {
  repository = data.aws_ecr_repository.backend.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last 10 images"
        selection = {
          tagStatus     = "tagged"
          tagPrefixList = ["v"]
          countType     = "imageCountMoreThan"
          countNumber   = 10
        }
        action = {
          type = "expire"
        }
      },
      {
        rulePriority = 2
        description  = "Remove untagged images after 1 day"
        selection = {
          tagStatus   = "untagged"
          countType   = "sinceImagePushed"
          countUnit   = "days"
          countNumber = 1
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}

resource "aws_ecr_lifecycle_policy" "frontend" {
  repository = data.aws_ecr_repository.frontend.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last 10 images"
        selection = {
          tagStatus     = "tagged"
          tagPrefixList = ["v"]
          countType     = "imageCountMoreThan"
          countNumber   = 10
        }
        action = {
          type = "expire"
        }
      },
      {
        rulePriority = 2
        description  = "Remove untagged images after 1 day"
        selection = {
          tagStatus   = "untagged"
          countType   = "sinceImagePushed"
          countUnit   = "days"
          countNumber = 1
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}

# IAM User for CI/CD
resource "aws_iam_user" "ci_cd" {
  name = "${var.project_name}-${var.environment}-ci-cd"
  path = "/"

  tags = var.tags
}

# IAM Policy for CI/CD
resource "aws_iam_policy" "ci_cd" {
  name        = "${var.project_name}-${var.environment}-ci-cd-policy"
  description = "Policy for CI/CD pipeline"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ecr:GetAuthorizationToken",
          "ecr:BatchCheckLayerAvailability",
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage",
          "ecr:PutImage",
          "ecr:InitiateLayerUpload",
          "ecr:UploadLayerPart",
          "ecr:CompleteLayerUpload"
        ]
        Resource = [
          data.aws_ecr_repository.backend.arn,
          data.aws_ecr_repository.frontend.arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "ecr:GetAuthorizationToken"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "ecs:UpdateService",
          "ecs:DescribeServices",
          "ecs:DescribeTasks",
          "ecs:ListTasks",
          "ecs:RunTask"
        ]
        Resource = [
          "arn:aws:ecs:${var.region}:*:service/${var.project_name}-${var.environment}-*",
          "arn:aws:ecs:${var.region}:*:task-definition/${var.project_name}-${var.environment}-*:*",
          "arn:aws:ecs:${var.region}:*:task/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "iam:PassRole"
        ]
        Resource = [
          "arn:aws:iam::*:role/${var.project_name}-${var.environment}-*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          "arn:aws:s3:::${var.project_name}-${var.environment}-*",
          "arn:aws:s3:::${var.project_name}-${var.environment}-*/*"
        ]
      }
    ]
  })
}

# Attach policy to CI/CD user
resource "aws_iam_user_policy_attachment" "ci_cd" {
  user       = aws_iam_user.ci_cd.name
  policy_arn = aws_iam_policy.ci_cd.arn
}

# Access key for CI/CD user
resource "aws_iam_access_key" "ci_cd" {
  user = aws_iam_user.ci_cd.name
}

# Store CI/CD credentials in SSM
resource "aws_ssm_parameter" "ci_cd_access_key" {
  name  = "/${var.project_name}/${var.environment}/ci-cd/access-key-id"
  type  = "SecureString"
  value = aws_iam_access_key.ci_cd.id

  tags = var.tags
}

resource "aws_ssm_parameter" "ci_cd_secret_key" {
  name  = "/${var.project_name}/${var.environment}/ci-cd/secret-access-key"
  type  = "SecureString"
  value = aws_iam_access_key.ci_cd.secret

  tags = var.tags
}

# Lambda execution role for custom resources
resource "aws_iam_role" "lambda_execution" {
  name = "${var.project_name}-${var.environment}-lambda-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = var.tags
}

# Lambda basic execution policy
resource "aws_iam_role_policy_attachment" "lambda_basic" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  role       = aws_iam_role.lambda_execution.name
}

# Lambda VPC access policy
resource "aws_iam_role_policy_attachment" "lambda_vpc" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
  role       = aws_iam_role.lambda_execution.name
}

# Policy for AI services access
resource "aws_iam_policy" "ai_services" {
  name        = "${var.project_name}-${var.environment}-ai-services-policy"
  description = "Policy for accessing AWS AI services"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "polly:SynthesizeSpeech",
          "polly:DescribeVoices",
          "polly:GetLexicon",
          "polly:ListLexicons"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "transcribe:StartTranscriptionJob",
          "transcribe:GetTranscriptionJob",
          "transcribe:ListTranscriptionJobs",
          "transcribe:DeleteTranscriptionJob",
          "transcribe:StartStreamTranscription"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "comprehend:DetectSentiment",
          "comprehend:DetectEntities",
          "comprehend:DetectKeyPhrases",
          "comprehend:DetectDominantLanguage"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream"
        ]
        Resource = "arn:aws:bedrock:*:*:model/*"
      }
    ]
  })
}