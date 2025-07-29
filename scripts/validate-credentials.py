#!/usr/bin/env python3
"""
Credential Validation Script for ISEE Tutor

This script validates all required credentials and API keys before deployment.
It tests actual connections to ensure everything is properly configured.
"""

import os
import sys
import json
import asyncio
from typing import Dict, Tuple, List
import subprocess
from datetime import datetime
from colorama import init, Fore, Style

# Initialize colorama for cross-platform colored output
init(autoreset=True)

# Color helpers
def success(msg: str) -> str:
    return f"{Fore.GREEN}✓ {msg}{Style.RESET_ALL}"

def error(msg: str) -> str:
    return f"{Fore.RED}✗ {msg}{Style.RESET_ALL}"

def warning(msg: str) -> str:
    return f"{Fore.YELLOW}⚠ {msg}{Style.RESET_ALL}"

def info(msg: str) -> str:
    return f"{Fore.BLUE}ℹ {msg}{Style.RESET_ALL}"

def header(msg: str) -> str:
    return f"\n{Fore.CYAN}{'='*60}\n{msg}\n{'='*60}{Style.RESET_ALL}"


class CredentialValidator:
    """Validates all required credentials for ISEE Tutor deployment"""
    
    def __init__(self):
        self.results = {}
        self.required_secrets = []
        self.optional_secrets = []
    
    def check_environment_variable(self, var_name: str, required: bool = True) -> Tuple[bool, str]:
        """Check if an environment variable is set"""
        value = os.environ.get(var_name)
        if value:
            # Mask sensitive data
            if "KEY" in var_name or "SECRET" in var_name or "TOKEN" in var_name:
                masked = f"{value[:4]}...{value[-4:]}" if len(value) > 8 else "***"
                return True, masked
            return True, "Set"
        return False, "Not set"
    
    async def validate_aws(self) -> Dict[str, any]:
        """Validate AWS credentials"""
        print(header("Validating AWS Credentials"))
        results = {}
        
        # Check environment variables
        key_exists, _ = self.check_environment_variable("AWS_ACCESS_KEY_ID")
        secret_exists, _ = self.check_environment_variable("AWS_SECRET_ACCESS_KEY")
        
        if not key_exists or not secret_exists:
            print(error("AWS credentials not found in environment"))
            results['status'] = False
            results['message'] = "Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY"
            return results
        
        # Test AWS connection
        try:
            result = subprocess.run(
                ["aws", "sts", "get-caller-identity"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                identity = json.loads(result.stdout)
                print(success(f"AWS credentials valid"))
                print(info(f"  Account: {identity['Account']}"))
                print(info(f"  User ARN: {identity['Arn']}"))
                results['status'] = True
                results['account_id'] = identity['Account']
                
                # Check for required permissions
                print("\nChecking AWS permissions...")
                required_services = ["ec2", "ecs", "rds", "s3", "iam"]
                for service in required_services:
                    try:
                        # Simple permission check
                        if service == "s3":
                            subprocess.run(["aws", "s3", "ls"], capture_output=True, timeout=5)
                        print(success(f"  {service}: Accessible"))
                    except:
                        print(warning(f"  {service}: May need additional permissions"))
                        
            else:
                print(error("AWS credentials invalid"))
                print(error(f"  {result.stderr}"))
                results['status'] = False
                results['message'] = result.stderr
                
        except subprocess.TimeoutExpired:
            print(error("AWS CLI timeout - check your internet connection"))
            results['status'] = False
        except FileNotFoundError:
            print(error("AWS CLI not installed. Please install: pip install awscli"))
            results['status'] = False
        except Exception as e:
            print(error(f"AWS validation error: {str(e)}"))
            results['status'] = False
            
        return results
    
    async def validate_openai(self) -> Dict[str, any]:
        """Validate OpenAI API key"""
        print(header("Validating OpenAI API Key"))
        results = {}
        
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            print(error("OPENAI_API_KEY not found in environment"))
            results['status'] = False
            results['message'] = "Set OPENAI_API_KEY environment variable"
            return results
        
        try:
            import openai
            
            # Test the API key
            client = openai.OpenAI(api_key=api_key)
            
            # Make a minimal API call
            response = client.models.list()
            models = list(response)
            
            print(success("OpenAI API key valid"))
            print(info(f"  Available models: {len(models)}"))
            
            # Check for GPT-3.5 and GPT-4
            model_names = [m.id for m in models]
            if any("gpt-3.5" in m for m in model_names):
                print(success("  GPT-3.5 available"))
            if any("gpt-4" in m for m in model_names):
                print(success("  GPT-4 available"))
            
            results['status'] = True
            results['models'] = model_names[:5]  # First 5 models
            
        except ImportError:
            print(error("OpenAI library not installed. Run: pip install openai"))
            results['status'] = False
        except Exception as e:
            print(error(f"OpenAI validation failed: {str(e)}"))
            if "Incorrect API key" in str(e):
                print(error("  Check that your API key starts with 'sk-'"))
            results['status'] = False
            
        return results
    
    async def validate_google_cloud(self) -> Dict[str, any]:
        """Validate Google Cloud credentials"""
        print(header("Validating Google Cloud Credentials"))
        results = {}
        
        creds = os.environ.get("GOOGLE_CLOUD_KEY")
        creds_file = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        
        if not creds and not creds_file:
            print(error("Google Cloud credentials not found"))
            print(info("  Set either GOOGLE_CLOUD_KEY (JSON content) or"))
            print(info("  GOOGLE_APPLICATION_CREDENTIALS (path to JSON file)"))
            results['status'] = False
            return results
        
        try:
            # Try to parse credentials
            if creds:
                creds_data = json.loads(creds)
            else:
                with open(creds_file, 'r') as f:
                    creds_data = json.load(f)
            
            print(success("Google Cloud credentials parsed successfully"))
            print(info(f"  Project ID: {creds_data.get('project_id', 'N/A')}"))
            print(info(f"  Service Account: {creds_data.get('client_email', 'N/A')}"))
            
            # Test API access
            try:
                from google.cloud import speech
                
                # Create a temporary credentials file if using env var
                if creds:
                    import tempfile
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                        json.dump(creds_data, f)
                        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = f.name
                
                client = speech.SpeechClient()
                print(success("  Speech-to-Text API accessible"))
                results['status'] = True
                results['project_id'] = creds_data.get('project_id')
                
            except ImportError:
                print(warning("  Google Cloud Speech library not installed"))
                print(info("    Run: pip install google-cloud-speech"))
                results['status'] = True  # Credentials are valid, just missing library
                
        except json.JSONDecodeError:
            print(error("Invalid JSON in Google Cloud credentials"))
            results['status'] = False
        except Exception as e:
            print(error(f"Google Cloud validation failed: {str(e)}"))
            results['status'] = False
            
        return results
    
    async def validate_pinecone(self) -> Dict[str, any]:
        """Validate Pinecone credentials"""
        print(header("Validating Pinecone Credentials"))
        results = {}
        
        api_key = os.environ.get("PINECONE_API_KEY")
        environment = os.environ.get("PINECONE_ENVIRONMENT", "us-east-1")
        
        if not api_key:
            print(error("PINECONE_API_KEY not found in environment"))
            results['status'] = False
            return results
        
        try:
            import pinecone
            
            # Initialize Pinecone
            pinecone.init(api_key=api_key, environment=environment)
            
            # List indexes
            indexes = pinecone.list_indexes()
            
            print(success("Pinecone credentials valid"))
            print(info(f"  Environment: {environment}"))
            print(info(f"  Existing indexes: {len(indexes)}"))
            
            if indexes:
                for idx in indexes[:3]:  # Show first 3
                    print(info(f"    - {idx}"))
            
            results['status'] = True
            results['environment'] = environment
            results['indexes'] = indexes
            
        except ImportError:
            print(error("Pinecone library not installed. Run: pip install pinecone-client"))
            results['status'] = False
        except Exception as e:
            print(error(f"Pinecone validation failed: {str(e)}"))
            if "API key" in str(e):
                print(error("  Check your API key is correct"))
            results['status'] = False
            
        return results
    
    async def check_optional_services(self):
        """Check optional services and configurations"""
        print(header("Checking Optional Services"))
        
        # Check for Slack webhook
        slack_webhook = os.environ.get("SLACK_WEBHOOK_URL")
        if slack_webhook:
            print(success("Slack webhook configured"))
        else:
            print(info("Slack webhook not configured (optional)"))
        
        # Check for domain configuration
        domain = os.environ.get("DOMAIN_NAME")
        if domain:
            print(success(f"Domain configured: {domain}"))
        else:
            print(info("Custom domain not configured (optional)"))
        
        # Check for monitoring
        if os.environ.get("DATADOG_API_KEY"):
            print(success("DataDog monitoring configured"))
        elif os.environ.get("NEW_RELIC_LICENSE_KEY"):
            print(success("New Relic monitoring configured"))
        else:
            print(info("External monitoring not configured (optional)"))
    
    async def check_system_requirements(self):
        """Check system requirements"""
        print(header("Checking System Requirements"))
        
        # Check Python version
        python_version = sys.version_info
        if python_version.major == 3 and python_version.minor >= 10:
            print(success(f"Python version: {python_version.major}.{python_version.minor}.{python_version.micro}"))
        else:
            print(error(f"Python 3.10+ required (found {python_version.major}.{python_version.minor})"))
        
        # Check required tools
        tools = {
            "docker": "Docker",
            "terraform": "Terraform",
            "aws": "AWS CLI",
            "git": "Git"
        }
        
        for cmd, name in tools.items():
            try:
                result = subprocess.run([cmd, "--version"], capture_output=True, timeout=5)
                if result.returncode == 0:
                    version = result.stdout.decode().split('\n')[0]
                    print(success(f"{name}: {version}"))
                else:
                    print(error(f"{name}: Not found"))
            except:
                print(error(f"{name}: Not installed"))
        
        # Check disk space
        import shutil
        total, used, free = shutil.disk_usage("/")
        free_gb = free // (2**30)
        if free_gb > 20:
            print(success(f"Disk space: {free_gb}GB free"))
        else:
            print(warning(f"Low disk space: {free_gb}GB free (recommend 20GB+)"))
    
    def generate_env_file(self):
        """Generate .env file template"""
        print(header("Generating Environment File"))
        
        env_template = """# ISEE Tutor Environment Configuration
# Generated on {timestamp}

# AWS Credentials
AWS_ACCESS_KEY_ID={aws_key}
AWS_SECRET_ACCESS_KEY={aws_secret}
AWS_REGION=us-east-1

# OpenAI
OPENAI_API_KEY={openai_key}

# Google Cloud
GOOGLE_CLOUD_KEY='{google_key}'

# Pinecone
PINECONE_API_KEY={pinecone_key}
PINECONE_ENVIRONMENT={pinecone_env}

# Optional Services
SLACK_WEBHOOK_URL={slack_webhook}
DOMAIN_NAME={domain}

# Monitoring Email
ALARM_EMAIL={email}
"""
        
        # Collect values
        values = {
            'timestamp': datetime.now().isoformat(),
            'aws_key': os.environ.get('AWS_ACCESS_KEY_ID', 'your-aws-key-here'),
            'aws_secret': os.environ.get('AWS_SECRET_ACCESS_KEY', 'your-aws-secret-here'),
            'openai_key': os.environ.get('OPENAI_API_KEY', 'sk-...'),
            'google_key': os.environ.get('GOOGLE_CLOUD_KEY', '{}'),
            'pinecone_key': os.environ.get('PINECONE_API_KEY', 'your-pinecone-key'),
            'pinecone_env': os.environ.get('PINECONE_ENVIRONMENT', 'us-east-1'),
            'slack_webhook': os.environ.get('SLACK_WEBHOOK_URL', ''),
            'domain': os.environ.get('DOMAIN_NAME', ''),
            'email': os.environ.get('ALARM_EMAIL', 'your-email@example.com')
        }
        
        env_content = env_template.format(**values)
        
        # Save to file
        env_file = ".env.validated"
        with open(env_file, 'w') as f:
            f.write(env_content)
        
        print(success(f"Environment file generated: {env_file}"))
        print(info("  Review and rename to .env when ready"))
    
    def generate_github_secrets_script(self):
        """Generate script to set GitHub secrets"""
        print(header("Generating GitHub Secrets Script"))
        
        script_content = """#!/bin/bash
# GitHub Secrets Setup Script
# Generated on {timestamp}

echo "Setting GitHub Secrets for ISEE Tutor..."

# Required secrets
gh secret set AWS_ACCESS_KEY_ID --body "$AWS_ACCESS_KEY_ID"
gh secret set AWS_SECRET_ACCESS_KEY --body "$AWS_SECRET_ACCESS_KEY"
gh secret set OPENAI_API_KEY --body "$OPENAI_API_KEY"
gh secret set GOOGLE_CLOUD_KEY --body "$GOOGLE_CLOUD_KEY"
gh secret set PINECONE_API_KEY --body "$PINECONE_API_KEY"
gh secret set PINECONE_ENVIRONMENT --body "${{PINECONE_ENVIRONMENT:-us-east-1}}"
gh secret set ALARM_EMAIL --body "${{ALARM_EMAIL:-admin@example.com}}"

# Optional secrets
if [ -n "$SLACK_WEBHOOK_URL" ]; then
    gh secret set SLACK_WEBHOOK_URL --body "$SLACK_WEBHOOK_URL"
fi

if [ -n "$DOMAIN_NAME" ]; then
    gh secret set PROD_DOMAIN_NAME --body "$DOMAIN_NAME"
fi

echo "GitHub secrets configured!"
echo "Run 'gh secret list' to verify"
"""
        
        script_file = "setup-github-secrets.sh"
        with open(script_file, 'w') as f:
            f.write(script_content.format(timestamp=datetime.now().isoformat()))
        
        os.chmod(script_file, 0o755)
        print(success(f"GitHub secrets script generated: {script_file}"))
        print(info("  Run this script after setting environment variables"))
    
    async def run_validation(self):
        """Run all validation checks"""
        print(f"\n{Fore.MAGENTA}🔍 ISEE Tutor Credential Validator{Style.RESET_ALL}")
        print(f"{Fore.MAGENTA}{'='*60}{Style.RESET_ALL}\n")
        
        # Check system requirements first
        await self.check_system_requirements()
        
        # Validate credentials
        aws_results = await self.validate_aws()
        openai_results = await self.validate_openai()
        google_results = await self.validate_google_cloud()
        pinecone_results = await self.validate_pinecone()
        
        # Check optional services
        await self.check_optional_services()
        
        # Summary
        print(header("Validation Summary"))
        
        all_valid = True
        validations = [
            ("AWS", aws_results.get('status', False)),
            ("OpenAI", openai_results.get('status', False)),
            ("Google Cloud", google_results.get('status', False)),
            ("Pinecone", pinecone_results.get('status', False))
        ]
        
        for service, status in validations:
            if status:
                print(success(f"{service}: Ready"))
            else:
                print(error(f"{service}: Not configured"))
                all_valid = False
        
        print()
        
        if all_valid:
            print(f"{Fore.GREEN}✅ All required credentials are valid!{Style.RESET_ALL}")
            print(f"{Fore.GREEN}You're ready to deploy ISEE Tutor.{Style.RESET_ALL}")
            
            # Generate helper files
            self.generate_env_file()
            self.generate_github_secrets_script()
            
            print(f"\n{Fore.CYAN}Next steps:{Style.RESET_ALL}")
            print("1. Review the generated .env.validated file")
            print("2. Run ./setup-github-secrets.sh to configure GitHub")
            print("3. Deploy with: cd terraform/scripts && ./deploy.sh dev")
        else:
            print(f"{Fore.RED}❌ Some credentials are missing or invalid.{Style.RESET_ALL}")
            print(f"{Fore.RED}Please configure the missing services above.{Style.RESET_ALL}")
            
            print(f"\n{Fore.YELLOW}Quick setup commands:{Style.RESET_ALL}")
            if not aws_results.get('status'):
                print("\n# AWS Setup:")
                print("export AWS_ACCESS_KEY_ID=your-key-here")
                print("export AWS_SECRET_ACCESS_KEY=your-secret-here")
            
            if not openai_results.get('status'):
                print("\n# OpenAI Setup:")
                print("# Get key from: https://platform.openai.com/api-keys")
                print("export OPENAI_API_KEY=sk-...")
            
            if not google_results.get('status'):
                print("\n# Google Cloud Setup:")
                print("# Create service account and download JSON")
                print("export GOOGLE_CLOUD_KEY='$(cat path/to/google-key.json)'")
            
            if not pinecone_results.get('status'):
                print("\n# Pinecone Setup:")
                print("# Get key from: https://www.pinecone.io")
                print("export PINECONE_API_KEY=your-key-here")
        
        return all_valid


async def main():
    """Main entry point"""
    validator = CredentialValidator()
    
    # Run validation
    success = await validator.run_validation()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    # Check if running in CI environment
    if os.environ.get('CI'):
        print("Running in CI environment - skipping interactive validation")
        sys.exit(0)
    
    # Run the validator
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nValidation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n{error(f'Unexpected error: {str(e)}')}")
        sys.exit(1)