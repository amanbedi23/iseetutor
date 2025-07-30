#!/bin/bash

# ISEE Tutor Docker Build and ECS Update Script
# This script builds Docker images and updates ECS services
# Terraform infrastructure is now managed via Terraform Cloud

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
ENVIRONMENT="${1:-dev}"
AWS_REGION="${AWS_REGION:-us-east-1}"
PROJECT_NAME="iseetutor"
TERRAFORM_DIR="../environments/${ENVIRONMENT}"

# Functions
print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[i]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    echo "Checking prerequisites..."
    
    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI is not installed"
        exit 1
    fi
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        exit 1
    fi
    
    # Check docker buildx
    if ! docker buildx version &> /dev/null; then
        print_error "Docker buildx is not installed"
        print_info "Install with: docker buildx install"
        exit 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        print_error "AWS credentials not configured"
        exit 1
    fi
    
    # Ensure we're using the correct AWS profile
    CURRENT_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
    if [ "${CURRENT_ACCOUNT}" != "391959657675" ]; then
        print_warning "Wrong AWS account detected. Expected: 391959657675, Got: ${CURRENT_ACCOUNT}"
        print_info "Setting AWS_PROFILE=iseetutor"
        export AWS_PROFILE=iseetutor
        
        # Verify again
        CURRENT_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
        if [ "${CURRENT_ACCOUNT}" != "391959657675" ]; then
            print_error "Failed to switch to correct AWS account"
            exit 1
        fi
    fi
    
    print_status "All prerequisites met"
}

# This function is no longer needed as Terraform is managed by Terraform Cloud
# Keeping as comment for reference
# setup_backend() {
#     print_info "Terraform backend is now managed by Terraform Cloud"
# }

# Build Docker images for multiple platforms
build_docker_images() {
    echo -e "\nBuilding Docker images for AMD64 platform..."
    
    # Get AWS account ID
    AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    ECR_REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
    
    # ECR repositories should already exist from Terraform
    # Just verify they exist
    for repo in backend frontend; do
        if ! aws ecr describe-repositories --repository-names "${PROJECT_NAME}-${ENVIRONMENT}-${repo}" &> /dev/null; then
            print_error "ECR repository ${PROJECT_NAME}-${ENVIRONMENT}-${repo} not found"
            print_info "Please ensure Terraform has been applied successfully"
            exit 1
        fi
    done
    
    # Login to ECR
    print_info "Logging into ECR..."
    aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ECR_REGISTRY}
    
    # Setup buildx for multi-platform builds
    print_info "Setting up Docker buildx..."
    docker buildx create --use --name multiplatform-builder || docker buildx use multiplatform-builder
    
    # Build and push backend for AMD64
    print_info "Building backend image for linux/amd64..."
    docker buildx build \
        --platform linux/amd64 \
        -t ${ECR_REGISTRY}/${PROJECT_NAME}-${ENVIRONMENT}-backend:latest \
        -f ../../Dockerfile.backend \
        --push \
        ../..
    
    # Build and push frontend for AMD64
    print_info "Building frontend image for linux/amd64..."
    docker buildx build \
        --platform linux/amd64 \
        -t ${ECR_REGISTRY}/${PROJECT_NAME}-${ENVIRONMENT}-frontend:latest \
        -f ../../Dockerfile.frontend \
        --push \
        ../..
    
    print_status "Docker images built and pushed for linux/amd64 platform"
}

# This function is no longer needed as Terraform is managed by Terraform Cloud
# deploy_infrastructure() {
#     print_info "Infrastructure is now managed by Terraform Cloud"
#     print_info "Visit https://app.terraform.io to manage infrastructure"
# }

# Update ECS services
update_ecs_services() {
    echo -e "\nUpdating ECS services..."
    
    CLUSTER_NAME="${PROJECT_NAME}-${ENVIRONMENT}-cluster"
    
    # Force new deployment for backend
    print_info "Updating backend service..."
    aws ecs update-service \
        --cluster ${CLUSTER_NAME} \
        --service ${PROJECT_NAME}-${ENVIRONMENT}-backend \
        --force-new-deployment \
        --region ${AWS_REGION}
    
    # Force new deployment for frontend
    print_info "Updating frontend service..."
    aws ecs update-service \
        --cluster ${CLUSTER_NAME} \
        --service ${PROJECT_NAME}-${ENVIRONMENT}-frontend \
        --force-new-deployment \
        --region ${AWS_REGION}
    
    # Wait for services to stabilize
    print_info "Waiting for services to stabilize..."
    aws ecs wait services-stable \
        --cluster ${CLUSTER_NAME} \
        --services ${PROJECT_NAME}-${ENVIRONMENT}-backend ${PROJECT_NAME}-${ENVIRONMENT}-frontend \
        --region ${AWS_REGION}
    
    print_status "ECS services updated"
}

# Run database migrations
run_migrations() {
    echo -e "\nRunning database migrations..."
    
    # Get subnet and security group from AWS (since we can't access Terraform outputs)
    print_info "Getting network configuration..."
    SUBNET_ID=$(aws ec2 describe-subnets \
        --filters "Name=tag:Name,Values=${PROJECT_NAME}-${ENVIRONMENT}-private-subnet-*" \
        --query 'Subnets[0].SubnetId' \
        --output text)
    
    SECURITY_GROUP_ID=$(aws ec2 describe-security-groups \
        --filters "Name=tag:Name,Values=${PROJECT_NAME}-${ENVIRONMENT}-ecs-tasks-*" \
        --query 'SecurityGroups[0].GroupId' \
        --output text)
    
    if [ "${SUBNET_ID}" == "None" ] || [ "${SECURITY_GROUP_ID}" == "None" ]; then
        print_error "Could not find required network resources"
        print_info "Skipping database migrations - run manually if needed"
        return
    fi
    
    # Run migrations using ECS task
    print_info "Executing migration task..."
    TASK_ARN=$(aws ecs run-task \
        --cluster ${PROJECT_NAME}-${ENVIRONMENT}-cluster \
        --task-definition ${PROJECT_NAME}-${ENVIRONMENT}-backend \
        --launch-type FARGATE \
        --network-configuration "awsvpcConfiguration={subnets=[${SUBNET_ID}],securityGroups=[${SECURITY_GROUP_ID}]}" \
        --overrides '{"containerOverrides":[{"name":"backend","command":["alembic","upgrade","head"]}]}' \
        --query 'tasks[0].taskArn' \
        --output text)
    
    if [ "${TASK_ARN}" == "None" ]; then
        print_error "Failed to start migration task"
        return
    fi
    
    # Wait for task to complete
    print_info "Waiting for migration task to complete..."
    aws ecs wait tasks-stopped --cluster ${PROJECT_NAME}-${ENVIRONMENT}-cluster --tasks ${TASK_ARN}
    
    # Check task exit code
    EXIT_CODE=$(aws ecs describe-tasks \
        --cluster ${PROJECT_NAME}-${ENVIRONMENT}-cluster \
        --tasks ${TASK_ARN} \
        --query 'tasks[0].containers[0].exitCode' \
        --output text)
    
    if [ "${EXIT_CODE}" -eq "0" ]; then
        print_status "Database migrations completed"
    else
        print_error "Database migrations failed with exit code ${EXIT_CODE}"
        print_info "Check ECS task logs for details"
    fi
}

# Display deployment info
display_info() {
    echo -e "\n${GREEN}========================================${NC}"
    echo -e "${GREEN}Deployment Complete!${NC}"
    echo -e "${GREEN}========================================${NC}\n"
    
    # Get ALB DNS from AWS
    ALB_DNS=$(aws elbv2 describe-load-balancers \
        --query "LoadBalancers[?contains(LoadBalancerName, '${PROJECT_NAME}-${ENVIRONMENT}')].DNSName" \
        --output text)
    
    echo "Environment: ${ENVIRONMENT}"
    echo "Region: ${AWS_REGION}"
    echo ""
    
    if [ -n "${ALB_DNS}" ]; then
        echo "Access your application at:"
        echo "  HTTP:  http://${ALB_DNS}"
        echo ""
        echo "API Documentation:"
        echo "  http://${ALB_DNS}/docs"
    else
        echo "Could not retrieve ALB DNS name"
    fi
    
    echo ""
    echo "To view logs:"
    echo "  aws logs tail /ecs/${PROJECT_NAME}-${ENVIRONMENT} --follow"
    echo ""
    echo "To check service status:"
    echo "  aws ecs describe-services --cluster ${PROJECT_NAME}-${ENVIRONMENT}-cluster --services ${PROJECT_NAME}-${ENVIRONMENT}-backend ${PROJECT_NAME}-${ENVIRONMENT}-frontend"
    echo ""
    echo "Infrastructure is managed via Terraform Cloud:"
    echo "  https://app.terraform.io/app/iseetutor/workspaces/iseetutor-${ENVIRONMENT}"
    echo ""
}

# Main execution
main() {
    echo "🚀 ISEE Tutor Docker Build & Deploy Script"
    echo "=========================================="
    echo "Environment: ${ENVIRONMENT}"
    echo "Region: ${AWS_REGION}"
    echo ""
    echo "Note: Infrastructure is managed via Terraform Cloud"
    echo ""
    
    check_prerequisites
    build_docker_images
    update_ecs_services
    
    # Ask if user wants to run migrations
    read -p "Do you want to run database migrations? (yes/no): " -n 3 -r
    echo
    if [[ $REPLY =~ ^[Yy]es$ ]]; then
        run_migrations
    fi
    
    display_info
}

# Run main function
main