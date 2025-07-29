# Complete Infrastructure Setup Guide for ISEE Tutor

This guide covers the complete setup of all infrastructure components including cloud services, databases, and external APIs.

## Prerequisites Checklist

- [ ] AWS Account with administrative access
- [ ] Domain name (optional but recommended)
- [ ] Credit card for cloud services
- [ ] Basic knowledge of AWS and Terraform

## Step 1: External Cloud Services Setup

### 1.1 OpenAI Setup (LLM)
1. Go to https://platform.openai.com/signup
2. Create an account and add billing information
3. Generate API key:
   - Navigate to API Keys section
   - Click "Create new secret key"
   - Copy and save the key (starts with `sk-`)
4. Set usage limits (recommended):
   - Go to Usage Limits
   - Set monthly budget ($100-200 for testing)

### 1.2 Google Cloud Setup (Speech-to-Text)
1. Create Google Cloud account: https://console.cloud.google.com
2. Create new project named "iseetutor"
3. Enable required APIs:
   ```bash
   gcloud services enable speech.googleapis.com
   gcloud services enable texttospeech.googleapis.com
   ```
4. Create service account:
   ```bash
   gcloud iam service-accounts create iseetutor-stt \
     --display-name="ISEE Tutor STT Service"
   
   gcloud iam service-accounts keys create ~/iseetutor-gcp-key.json \
     --iam-account=iseetutor-stt@YOUR_PROJECT_ID.iam.gserviceaccount.com
   ```
5. Grant necessary permissions:
   ```bash
   gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
     --member="serviceAccount:iseetutor-stt@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
     --role="roles/speech.client"
   ```

### 1.3 AWS Services Setup (Already included in Terraform)
- Amazon Polly (TTS) - Automatically available with AWS account
- Amazon Transcribe - Automatically available
- S3 - Created by Terraform

### 1.4 Pinecone Vector Database Setup
1. Sign up at https://www.pinecone.io
2. Create new project:
   - Name: "iseetutor"
   - Environment: "us-east-1" (match your AWS region)
3. Create index:
   ```python
   import pinecone
   
   pinecone.init(api_key="YOUR_API_KEY", environment="us-east-1")
   
   pinecone.create_index(
       name="iseetutor-content",
       dimension=384,  # for all-MiniLM-L6-v2 embeddings
       metric="cosine",
       pods=1,
       replicas=1,
       pod_type="p1.x1"
   )
   ```
4. Note your API key and environment

## Step 2: AWS Infrastructure Deployment

### 2.1 Configure AWS CLI
```bash
aws configure
# Enter your AWS Access Key ID
# Enter your AWS Secret Access Key
# Default region: us-east-1
# Default output format: json
```

### 2.2 Set Environment Variables
```bash
# Create a secure environment file
cat > ~/.iseetutor-env << EOF
export TF_VAR_openai_api_key="sk-..."
export TF_VAR_google_cloud_key='$(cat ~/iseetutor-gcp-key.json)'
export TF_VAR_pinecone_api_key="..."
export TF_VAR_pinecone_environment="us-east-1"
export TF_VAR_aws_access_key_id_for_services="AKIA..."
export TF_VAR_aws_secret_access_key_for_services="..."
EOF

# Source the environment
source ~/.iseetutor-env
```

### 2.3 Deploy Infrastructure
```bash
cd terraform/scripts
./deploy.sh dev
```

## Step 3: Database Setup and Initialization

### 3.1 Connect to RDS PostgreSQL
```bash
# Get database connection info
cd terraform/environments/dev
DB_ENDPOINT=$(terraform output -raw db_endpoint)
DB_PASSWORD=$(aws ssm get-parameter --name "/iseetutor/dev/rds/password" --with-decryption --query 'Parameter.Value' --output text)

# Connect using psql
psql -h $DB_ENDPOINT -U iseetutor_admin -d iseetutor
# Enter password when prompted
```

### 3.2 Initialize Database Schema
```sql
-- Create schemas
CREATE SCHEMA IF NOT EXISTS app;
CREATE SCHEMA IF NOT EXISTS analytics;

-- Set search path
SET search_path TO app, public;

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Grant permissions
GRANT ALL ON SCHEMA app TO iseetutor_admin;
GRANT ALL ON SCHEMA analytics TO iseetutor_admin;
```

### 3.3 Run Alembic Migrations
```bash
# The deploy script automatically runs migrations, but you can run manually:
aws ecs run-task \
  --cluster iseetutor-dev-cluster \
  --task-definition iseetutor-dev-backend \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx]}" \
  --overrides '{"containerOverrides":[{"name":"backend","command":["alembic","upgrade","head"]}]}'
```

## Step 4: Initial Data Setup

### 4.1 Create Admin User
```bash
# Run this through ECS task
aws ecs run-task \
  --cluster iseetutor-dev-cluster \
  --task-definition iseetutor-dev-backend \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx]}" \
  --overrides '{"containerOverrides":[{"name":"backend","command":["python","-c","
from src.database.models import User
from src.core.security.auth import get_password_hash
from src.database.session import SessionLocal

db = SessionLocal()
admin = User(
    username=\"admin\",
    email=\"admin@iseetutor.com\",
    full_name=\"Admin User\",
    hashed_password=get_password_hash(\"changeme123\"),
    role=\"admin\",
    is_active=True
)
db.add(admin)
db.commit()
print(\"Admin user created\")
"]}]}'
```

### 4.2 Initialize Vector Database
```python
# Create a script: init_pinecone.py
import pinecone
import os
from sentence_transformers import SentenceTransformer

# Initialize
pinecone.init(
    api_key=os.getenv("PINECONE_API_KEY"),
    environment=os.getenv("PINECONE_ENVIRONMENT")
)

# Get or create index
index_name = "iseetutor-content"
if index_name not in pinecone.list_indexes():
    pinecone.create_index(
        name=index_name,
        dimension=384,
        metric="cosine"
    )

index = pinecone.Index(index_name)

# Create namespaces
namespaces = ["questions", "content", "concepts"]

# Initialize with sample data
model = SentenceTransformer('all-MiniLM-L6-v2')

sample_content = [
    {
        "id": "sample-1",
        "text": "The ISEE (Independent School Entrance Examination) is a test used for admission to private schools.",
        "metadata": {"type": "definition", "subject": "general"}
    },
    {
        "id": "sample-2", 
        "text": "ISEE has four levels: Primary (grades 2-4), Lower (grades 5-6), Middle (grades 7-8), and Upper (grades 9-12).",
        "metadata": {"type": "information", "subject": "general"}
    }
]

# Index sample content
for item in sample_content:
    embedding = model.encode(item["text"])
    index.upsert(
        vectors=[(item["id"], embedding.tolist(), item["metadata"])],
        namespace="content"
    )

print("Pinecone initialized with sample data")
```

### 4.3 Import Educational Content
```bash
# Copy ISEE PDFs to S3
aws s3 cp ./isee-content/ s3://iseetutor-dev-data/content/ --recursive

# Run content import task
aws ecs run-task \
  --cluster iseetutor-dev-cluster \
  --task-definition iseetutor-dev-backend \
  --launch-type FARGATE \
  --overrides '{"containerOverrides":[{"name":"backend","command":["python","scripts/import_isee_content.py"]}]}'
```

## Step 5: Configure Application Settings

### 5.1 Update SSM Parameters
```bash
# Set application configuration
aws ssm put-parameter \
  --name "/iseetutor/dev/app/config" \
  --type "String" \
  --value '{
    "max_tokens": 1000,
    "temperature": 0.7,
    "voice_speed": 1.0,
    "session_timeout": 3600,
    "max_file_size": 104857600
  }'

# Set feature flags
aws ssm put-parameter \
  --name "/iseetutor/dev/features" \
  --type "String" \
  --value '{
    "enable_voice": true,
    "enable_parent_portal": true,
    "enable_achievements": true,
    "enable_analytics": true
  }'
```

### 5.2 Configure Redis Cache
```bash
# Connect to Redis
REDIS_ENDPOINT=$(cd terraform/environments/dev && terraform output -raw redis_endpoint)
redis-cli -h $REDIS_ENDPOINT

# Set initial cache values
SET app:config:voice_models '["en-US-Wavenet-A", "en-US-Wavenet-B", "en-US-Wavenet-C"]'
SET app:config:difficulty_levels '["beginner", "intermediate", "advanced"]'
SET app:config:subjects '["math", "reading", "writing", "verbal"]'
```

## Step 6: Verification

### 6.1 Health Checks
```bash
# Check ALB health
ALB_DNS=$(cd terraform/environments/dev && terraform output -raw alb_dns_name)
curl -s https://$ALB_DNS/health | jq

# Check API docs
open https://$ALB_DNS/docs
```

### 6.2 Test API Endpoints
```bash
# Test chat endpoint
curl -X POST https://$ALB_DNS/api/companion/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "mode": "tutor"}'

# Test quiz generation
curl -X POST https://$ALB_DNS/api/quiz/generate \
  -H "Content-Type: application/json" \
  -d '{"subject": "math", "difficulty": "intermediate", "count": 5}'
```

### 6.3 Monitor Services
```bash
# View ECS service status
aws ecs describe-services \
  --cluster iseetutor-dev-cluster \
  --services iseetutor-dev-backend iseetutor-dev-frontend

# Check CloudWatch logs
aws logs tail /ecs/iseetutor-dev --follow

# Monitor RDS metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/RDS \
  --metric-name DatabaseConnections \
  --dimensions Name=DBInstanceIdentifier,Value=iseetutor-dev-db \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average
```

## Step 7: Production Deployment

### 7.1 Differences for Production
- Multi-AZ RDS deployment
- Read replicas for database
- Multiple ECS tasks for high availability
- WAF enabled for DDoS protection
- Enhanced monitoring and alarms

### 7.2 Deploy to Production
```bash
cd terraform/scripts
./deploy.sh prod

# Use different API keys for production
export TF_VAR_openai_api_key="sk-prod-..."
```

## Troubleshooting

### Common Issues

1. **ECS Tasks Not Starting**
   - Check security groups
   - Verify IAM roles
   - Check container logs

2. **Database Connection Failed**
   - Verify RDS security group
   - Check SSM parameter permissions
   - Ensure VPC connectivity

3. **External API Errors**
   - Verify API keys in SSM
   - Check service quotas
   - Monitor CloudWatch logs

### Debug Commands
```bash
# Get task failure reason
aws ecs describe-tasks \
  --cluster iseetutor-dev-cluster \
  --tasks $(aws ecs list-tasks --cluster iseetutor-dev-cluster --query 'taskArns[0]' --output text)

# View container logs
aws logs get-log-events \
  --log-group-name /ecs/iseetutor-dev \
  --log-stream-name backend/iseetutor-dev-backend/$(aws ecs list-tasks --cluster iseetutor-dev-cluster --query 'taskArns[0]' --output text | cut -d'/' -f3)

# Test database connectivity
aws ecs run-task \
  --cluster iseetutor-dev-cluster \
  --task-definition iseetutor-dev-backend \
  --overrides '{"containerOverrides":[{"name":"backend","command":["python","-c","import psycopg2; print(\"DB connection successful\")"]}]}'
```

## Maintenance

### Daily Tasks
- Monitor CloudWatch dashboards
- Check for alarms
- Review error logs

### Weekly Tasks
- Review AWS costs
- Check for security updates
- Backup verification

### Monthly Tasks
- Rotate API keys
- Update container images
- Performance optimization

## Cost Optimization Tips

1. **Development Environment**
   - Use scheduled Lambda to stop/start resources
   - Implement auto-shutdown after hours
   - Use Spot instances for non-critical tasks

2. **Production Environment**
   - Purchase Reserved Instances
   - Enable S3 lifecycle policies
   - Use CloudFront for static assets
   - Implement caching strategies

## Security Checklist

- [ ] All secrets in SSM Parameter Store
- [ ] VPC endpoints configured
- [ ] Security groups follow least privilege
- [ ] WAF enabled for production
- [ ] API keys rotated regularly
- [ ] CloudTrail logging enabled
- [ ] GuardDuty activated
- [ ] Regular security audits

## Support Resources

- AWS Support: https://console.aws.amazon.com/support
- OpenAI Support: https://help.openai.com
- Google Cloud Support: https://cloud.google.com/support
- Pinecone Support: https://docs.pinecone.io/docs/support