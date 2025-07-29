# Security Notice - Sensitive Files Removed

## Summary
This repository has been cleaned of sensitive files that should never be in version control.

## Removed Files
The following files have been removed from Git tracking:
- `docs/keys/iseetutor-3a7999ec1e31.json` - Google Cloud service account key
- `scripts/.env.simple` - Environment variables
- `.env.docker` - Docker environment configuration
- `terraform/environments/dev/terraform.tfvars` - Contains AWS credentials

## Security Best Practices

### 1. Never Commit Credentials
- API keys, passwords, and tokens should NEVER be in Git
- Use environment variables or secure vaults (AWS Secrets Manager, etc.)
- Check files before committing: `git diff --staged`

### 2. Use .gitignore
- Always add sensitive file patterns to .gitignore
- See `.gitignore.example` for comprehensive patterns
- Test with: `git status` to ensure files are ignored

### 3. Environment Files
- Use `.env.example` files as templates
- Copy to `.env` locally and add real values
- Never commit the actual `.env` files

### 4. If You Accidentally Commit Secrets
1. Remove from staging: `git reset HEAD <file>`
2. Remove from history: `git filter-branch` or `BFG Repo-Cleaner`
3. Rotate all exposed credentials immediately
4. Force push to overwrite history (coordinate with team)

### 5. Credential Management
- **Local Development**: Use `.env` files (git-ignored)
- **CI/CD**: Use GitHub Secrets or environment variables
- **Production**: Use AWS Secrets Manager, Parameter Store, or similar
- **Docker**: Pass secrets via environment variables or mounted files

## Setting Up Credentials

1. Copy example files:
   ```bash
   cp .env.example .env
   cp .env.docker.example .env.docker
   cp terraform/environments/dev/terraform.tfvars.example terraform/environments/dev/terraform.tfvars
   ```

2. Edit the copied files with your actual credentials

3. Verify they're ignored:
   ```bash
   git status  # Should not show your .env files
   ```

## AWS Credentials Warning
The AWS credentials that were exposed in terraform.tfvars should be:
1. Immediately deactivated in AWS IAM console
2. New credentials generated
3. All systems using these credentials updated

## Tools for Secret Scanning
- [git-secrets](https://github.com/awslabs/git-secrets) - Prevents commits with secrets
- [truffleHog](https://github.com/trufflesecurity/trufflehog) - Scans for secrets
- [detect-secrets](https://github.com/Yelp/detect-secrets) - Pre-commit hook

## Contact
If you find any security issues, please report them immediately to the project maintainers.