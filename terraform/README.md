# ISEE Tutor AWS Infrastructure with Terraform

This directory contains Terraform configurations for deploying ISEE Tutor infrastructure on AWS with separate dev and production environments.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        Internet                              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Application Load Balancer                 │
│                         (HTTPS/WSS)                          │
└─────────────────────────────────────────────────────────────┘
                              │
                ┌─────────────┴─────────────┐
                ▼                           ▼
┌─────────────────────────┐   ┌─────────────────────────┐
│     Frontend Service    │   │     Backend Service     │
│   (React + Nginx)       │   │    (FastAPI)            │
│   ECS Fargate           │   │    ECS Fargate          │
└─────────────────────────┘   └─────────────────────────┘
                                            │
                    ┌───────────────────────┼───────────────┐
                    ▼                       ▼               ▼
┌─────────────────────────┐   ┌─────────────────┐   ┌─────────────┐
│   RDS PostgreSQL        │   │ ElastiCache     │   │  S3 Bucket  │
│   (Multi-AZ for Prod)   │   │    Redis        │   │  (Storage)  │
└─────────────────────────┘   └─────────────────┘   └─────────────┘
                              
                        External AI Services
┌─────────────────────────────────────────────────────────────┐
│  • OpenAI (LLM)           • Google Cloud Speech (STT)       │
│  • Amazon Polly (TTS)     • Pinecone (Vector DB)           │
└─────────────────────────────────────────────────────────────┘
```

## Prerequisites

1. **AWS Account** with appropriate permissions
2. **Terraform** >= 1.5.0 installed
3. **AWS CLI** configured with credentials
4. **Docker** for building container images
5. **Domain name** (optional, for HTTPS)
6. **AI Service Accounts**:
   - OpenAI API key
   - Google Cloud service account
   - AWS IAM user for Polly
   - Pinecone API key

## Directory Structure

```
terraform/
├── modules/
│   ├── vpc/          # VPC and networking
│   ├── rds/          # RDS PostgreSQL
│   ├── redis/        # ElastiCache Redis
│   ├── ecs/          # ECS cluster and services
│   ├── alb/          # Application Load Balancer
│   ├── s3/           # S3 buckets
│   ├── iam/          # IAM roles and policies
│   └── monitoring/   # CloudWatch monitoring
├── environments/
│   ├── dev/          # Development environment
│   └── prod/         # Production environment
└── scripts/          # Deployment scripts
```

## Quick Start

### 1. Initial Setup

```bash
# Clone the repository
git clone <repository-url>
cd iseetutor/terraform

# Create S3 bucket for Terraform state
aws s3 mb s3://iseetutor-terraform-state --region us-east-1

# Create DynamoDB table for state locking
aws dynamodb create-table \
  --table-name iseetutor-terraform-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5 \
  --region us-east-1
```

### 2. Configure Environment Variables

Create `terraform.tfvars` in the environment directory:

```hcl
# terraform/environments/dev/terraform.tfvars
project_name = "iseetutor"
region       = "us-east-1"

# Domain (optional)
domain_name     = "dev.iseetutor.com"
certificate_arn = "arn:aws:acm:us-east-1:123456789:certificate/xxx"

# Container images
backend_image_tag  = "latest"
frontend_image_tag = "latest"

# AI Service Keys (sensitive - use environment variables in CI/CD)
openai_api_key                   = "sk-..."
google_cloud_key                 = "path/to/service-account.json"
aws_access_key_id_for_services   = "AKIA..."
aws_secret_access_key_for_services = "..."
pinecone_api_key                 = "..."

# Monitoring
alarm_email = "alerts@example.com"
```

### 3. Deploy Infrastructure

```bash
# Navigate to environment
cd environments/dev

# Initialize Terraform
terraform init

# Review plan
terraform plan

# Apply infrastructure
terraform apply

# Get outputs
terraform output -json > outputs.json
```

## Deployment Steps

### Step 1: Build and Push Docker Images

```bash
# Build images
docker build -t iseetutor/backend:latest -f Dockerfile.backend ../..
docker build -t iseetutor/frontend:latest -f Dockerfile.frontend ../..

# Get ECR login
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

# Tag images
docker tag iseetutor/backend:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/iseetutor-dev-backend:latest
docker tag iseetutor/frontend:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/iseetutor-dev-frontend:latest

# Push images
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/iseetutor-dev-backend:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/iseetutor-dev-frontend:latest
```

### Step 2: Deploy Infrastructure

```bash
cd terraform/environments/dev
terraform init
terraform plan -out=tfplan
terraform apply tfplan
```

### Step 3: Update ECS Services

```bash
# Force new deployment with latest images
aws ecs update-service \
  --cluster iseetutor-dev-cluster \
  --service iseetutor-dev-backend \
  --force-new-deployment

aws ecs update-service \
  --cluster iseetutor-dev-cluster \
  --service iseetutor-dev-frontend \
  --force-new-deployment
```

## Environment-Specific Configurations

### Development
- Single NAT Gateway (cost optimization)
- Smaller instance sizes
- Shorter backup retention
- No read replicas

### Production
- Multi-AZ deployment
- NAT Gateway per AZ
- Enhanced monitoring
- Read replicas for RDS
- Longer backup retention
- Deletion protection

## Cost Optimization

### Estimated Monthly Costs

#### Development Environment
- VPC + NAT Gateway: $45
- ALB: $25
- ECS Fargate: $50-100
- RDS (db.t3.micro): $15
- ElastiCache (cache.t3.micro): $15
- S3 + Data Transfer: $10-20
- **Total: ~$160-230/month**

#### Production Environment
- VPC + NAT Gateways: $90
- ALB: $25
- ECS Fargate: $200-400
- RDS (db.t3.small, Multi-AZ): $70
- ElastiCache (cache.t3.small): $35
- S3 + Data Transfer: $50-100
- CloudWatch: $20-50
- **Total: ~$490-770/month**

### Cost Saving Tips
1. Use Spot instances for non-critical workloads
2. Enable S3 lifecycle policies
3. Use Reserved Instances for production
4. Schedule dev environment shutdown
5. Use VPC endpoints to reduce NAT Gateway costs

## Monitoring and Alerts

### CloudWatch Dashboards
- ECS service metrics
- RDS performance metrics
- Redis cache hit ratio
- ALB request metrics

### Alarms Configured
- High CPU/Memory usage
- Database connection limits
- Redis evictions
- ECS task failures
- ALB unhealthy targets

## Security Best Practices

1. **Secrets Management**
   - All secrets in SSM Parameter Store
   - Encrypted at rest
   - IAM role-based access

2. **Network Security**
   - Private subnets for compute
   - Security groups with least privilege
   - VPC endpoints for AWS services

3. **Data Encryption**
   - RDS encryption at rest
   - Redis encryption in transit
   - S3 bucket encryption

4. **Access Control**
   - IAM roles for services
   - No hardcoded credentials
   - CloudTrail logging enabled

## Troubleshooting

### Common Issues

1. **ECS Tasks Not Starting**
   ```bash
   # Check task logs
   aws logs tail /ecs/iseetutor-dev --follow
   
   # Describe task failures
   aws ecs describe-tasks --cluster iseetutor-dev-cluster --tasks <task-arn>
   ```

2. **Database Connection Issues**
   - Verify security groups
   - Check RDS endpoint in SSM
   - Ensure task role has SSM permissions

3. **ALB Health Check Failures**
   - Verify health check path
   - Check security group rules
   - Review container health check

## Maintenance

### Daily
- Monitor CloudWatch dashboards
- Check for alarm notifications

### Weekly
- Review AWS Cost Explorer
- Update container images
- Check for security updates

### Monthly
- Rotate API keys
- Review and optimize resources
- Update documentation

## Disaster Recovery

### Backup Strategy
- RDS automated backups (7-30 days)
- S3 cross-region replication
- Infrastructure as Code in Git

### Recovery Procedures
1. **Database Recovery**
   ```bash
   # Restore from snapshot
   aws rds restore-db-instance-from-db-snapshot \
     --db-instance-identifier iseetutor-dev-restored \
     --db-snapshot-identifier <snapshot-id>
   ```

2. **Full Environment Recovery**
   ```bash
   # Deploy from scratch
   cd terraform/environments/dev
   terraform apply
   ```

## CI/CD Integration

### GitHub Actions Example
```yaml
name: Deploy to AWS
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      
      - name: Build and push Docker images
        run: |
          ./scripts/build-and-push.sh
      
      - name: Deploy with Terraform
        run: |
          cd terraform/environments/${{ github.ref == 'refs/heads/main' && 'prod' || 'dev' }}
          terraform init
          terraform apply -auto-approve
```

## Clean Up

To destroy all resources:
```bash
cd terraform/environments/dev
terraform destroy
```

**Warning**: This will delete all resources including databases. Ensure backups exist!

## Support

For issues or questions:
1. Check CloudWatch logs
2. Review Terraform state
3. Consult AWS documentation
4. Open GitHub issue