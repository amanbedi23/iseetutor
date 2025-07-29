# CI/CD Pipeline Guide for ISEE Tutor

## Overview

ISEE Tutor uses GitHub Actions for continuous integration and deployment. The pipeline automates testing, building, and deploying to AWS infrastructure.

## Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        GitHub Repository                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Push to develop ──► CI Pipeline ──► Deploy to Dev          │
│                      │                                       │
│                      ├── Tests                               │
│                      ├── Security Scan                       │
│                      ├── Linting                             │
│                      └── Build Images                        │
│                                                              │
│  Push to main ────► CI Pipeline ──► Deploy to Prod          │
│                                     │                        │
│                                     ├── Approval Required    │
│                                     ├── Database Backup      │
│                                     ├── Canary Deployment    │
│                                     └── Full Deployment      │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Workflows

### 1. CI Pipeline (`ci.yml`)

Runs on every push and pull request.

**Steps:**
1. **Testing**
   - Unit tests with pytest
   - Frontend tests with Jest
   - Code coverage reporting

2. **Security Scanning**
   - Trivy vulnerability scanning
   - Snyk dependency scanning
   - SAST analysis

3. **Linting**
   - Python: Black, Flake8, MyPy
   - JavaScript: ESLint

4. **Build & Push**
   - Docker image building
   - Push to Amazon ECR
   - Multi-architecture support

### 2. Development Deployment (`deploy-dev.yml`)

Triggered on push to `develop` branch.

**Steps:**
1. Deploy infrastructure (Terraform)
2. Update ECS services
3. Run database migrations
4. Initialize data (Pinecone)
5. Smoke tests
6. Slack notification

### 3. Production Deployment (`deploy-prod.yml`)

Triggered on push to `main` branch.

**Features:**
- Manual approval required
- Database backup before deployment
- Canary deployment (10% traffic first)
- Automatic rollback on failure
- Production smoke tests

### 4. Rollback Workflow (`rollback.yml`)

Manual trigger for emergency rollbacks.

**Options:**
- ECS services only
- Full Terraform rollback
- Target specific version

## Setup Requirements

### GitHub Secrets

Configure these secrets in your repository:

```yaml
# AWS Credentials
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY

# API Keys (Dev)
OPENAI_API_KEY
GOOGLE_CLOUD_KEY
PINECONE_API_KEY
PINECONE_ENVIRONMENT

# API Keys (Production)
PROD_OPENAI_API_KEY
PROD_GOOGLE_CLOUD_KEY
PROD_PINECONE_API_KEY

# Service Credentials
AWS_ACCESS_KEY_ID_FOR_SERVICES
AWS_SECRET_ACCESS_KEY_FOR_SERVICES
PROD_AWS_ACCESS_KEY_ID_FOR_SERVICES
PROD_AWS_SECRET_ACCESS_KEY_FOR_SERVICES

# Configuration
ALARM_EMAIL
PROD_ALARM_EMAIL
PROD_DOMAIN_NAME
PROD_CERTIFICATE_ARN

# Monitoring
SLACK_WEBHOOK_URL
SNYK_TOKEN

# API URLs
DEV_API_URL
PROD_API_URL
```

### Environment Protection Rules

1. **Development Environment**
   - No approval required
   - Auto-deploy on push

2. **Production Environment**
   - Required reviewers
   - Deployment protection rules
   - Environment secrets

## Deployment Process

### Development Deployment

```bash
# Automatic on push to develop
git push origin develop

# Manual trigger
gh workflow run deploy-dev.yml
```

### Production Deployment

```bash
# Merge to main (requires PR approval)
git checkout main
git merge develop
git push origin main

# Deployment requires manual approval in GitHub
```

### Emergency Rollback

```bash
# Via GitHub UI or CLI
gh workflow run rollback.yml \
  -f environment=prod \
  -f rollback_type=ecs_only
```

## Pipeline Features

### 1. **Automated Testing**
- Unit tests with coverage
- Integration tests
- E2E tests (Playwright)
- Performance benchmarks

### 2. **Security**
- Container scanning
- Dependency vulnerability checks
- SAST/DAST analysis
- Secret scanning

### 3. **Quality Gates**
- Minimum 80% code coverage
- No high/critical vulnerabilities
- All tests must pass
- Linting compliance

### 4. **Deployment Safety**
- Blue-green deployments
- Canary releases
- Automatic rollback
- Health checks

### 5. **Monitoring**
- CloudWatch integration
- Slack notifications
- Deployment tracking
- Performance metrics

## Best Practices

### 1. **Branch Strategy**
```
main ────────► Production
  │
  └── develop ► Development
       │
       └── feature/* ► Feature branches
```

### 2. **Commit Messages**
```
feat: Add new quiz generation algorithm
fix: Resolve WebSocket connection issue
docs: Update API documentation
test: Add unit tests for auth module
```

### 3. **Pull Request Process**
1. Create feature branch
2. Make changes
3. Run tests locally
4. Create PR to develop
5. Code review required
6. Merge after approval

### 4. **Release Process**
1. Test thoroughly in dev
2. Create PR from develop to main
3. Get approval from team lead
4. Deploy to production
5. Monitor for 24 hours

## Monitoring & Alerts

### CloudWatch Dashboards
- Deployment metrics
- Error rates
- Performance metrics
- Cost tracking

### Slack Notifications
- Deployment status
- Test failures
- Security alerts
- Rollback notifications

## Troubleshooting

### Common Issues

1. **Build Failures**
   ```bash
   # Check logs
   gh run view <run-id> --log
   
   # Re-run failed jobs
   gh run rerun <run-id>
   ```

2. **Deployment Stuck**
   ```bash
   # Check ECS service
   aws ecs describe-services \
     --cluster iseetutor-dev-cluster \
     --services iseetutor-dev-backend
   ```

3. **Test Failures**
   ```bash
   # Run tests locally
   pytest tests/ -v
   npm test
   ```

### Debug Commands

```bash
# View workflow runs
gh run list --workflow=ci.yml

# Watch deployment
gh run watch

# Download artifacts
gh run download <run-id>

# View secrets (names only)
gh secret list
```

## Cost Optimization

### Pipeline Costs
- GitHub Actions: 2,000 minutes/month free
- Additional: $0.008/minute

### Optimization Tips
1. Use build caching
2. Parallel job execution
3. Skip unchanged services
4. Use spot instances for tests

## Security Considerations

### Secret Management
- Rotate keys quarterly
- Use least privilege IAM
- Separate dev/prod credentials
- Audit access logs

### Deployment Security
- Signed commits required
- Protected branches
- Deployment approvals
- Audit trail

## Future Improvements

1. **GitOps Integration**
   - ArgoCD for Kubernetes
   - Flux for automation

2. **Advanced Testing**
   - Load testing
   - Chaos engineering
   - Security scanning

3. **Multi-Region**
   - Cross-region replication
   - Disaster recovery
   - Global load balancing

## Support

For pipeline issues:
1. Check GitHub Actions status
2. Review workflow logs
3. Verify AWS permissions
4. Contact DevOps team

## Appendix

### Useful Commands

```bash
# Trigger workflow manually
gh workflow run deploy-dev.yml

# List all workflows
gh workflow list

# View specific run
gh run view <run-id>

# Cancel running workflow
gh run cancel <run-id>

# Re-run failed jobs
gh run rerun <run-id> --failed

# Download logs
gh run download <run-id> -n logs
```

### Pipeline Metrics

Track these KPIs:
- Deployment frequency
- Lead time for changes
- Mean time to recovery
- Change failure rate