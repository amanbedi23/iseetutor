#!/usr/bin/env python3
"""
Simple Credential Validation for ISEE Tutor
Minimal dependencies version
"""

import os
import sys
import json
import subprocess

# Simple color codes (no colorama needed)
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
MAGENTA = '\033[95m'
RESET = '\033[0m'

def print_header(msg):
    print(f"\n{MAGENTA}{'='*60}")
    print(msg)
    print(f"{'='*60}{RESET}")

def print_success(msg):
    print(f"{GREEN}✓ {msg}{RESET}")

def print_error(msg):
    print(f"{RED}✗ {msg}{RESET}")

def print_warning(msg):
    print(f"{YELLOW}⚠ {msg}{RESET}")

def print_info(msg):
    print(f"{BLUE}ℹ {msg}{RESET}")

def validate_aws():
    """Validate AWS credentials using AWS CLI"""
    print_header("Validating AWS Credentials")
    
    key = os.environ.get("AWS_ACCESS_KEY_ID")
    secret = os.environ.get("AWS_SECRET_ACCESS_KEY")
    
    if not key or not secret:
        print_error("AWS credentials not found in environment")
        print_info("Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY")
        return False
    
    try:
        result = subprocess.run(
            ["aws", "sts", "get-caller-identity"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            identity = json.loads(result.stdout)
            print_success("AWS credentials valid")
            print_info(f"  Account: {identity['Account']}")
            print_info(f"  User: {identity['Arn'].split('/')[-1]}")
            return True
        else:
            print_error("AWS credentials invalid")
            return False
    except FileNotFoundError:
        print_error("AWS CLI not installed")
        print_info("Install with: pip install awscli")
        return False
    except Exception as e:
        print_error(f"AWS validation error: {str(e)}")
        return False

def validate_openai():
    """Check if OpenAI key is set"""
    print_header("Checking OpenAI API Key")
    
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print_error("OPENAI_API_KEY not found")
        return False
    
    if api_key.startswith("sk-"):
        print_success("OpenAI API key format looks correct")
        print_info("  Run full validation script to test connection")
        return True
    else:
        print_error("OpenAI API key should start with 'sk-'")
        return False

def validate_google():
    """Check Google Cloud credentials"""
    print_header("Checking Google Cloud Credentials")
    
    creds_file = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    creds_json = os.environ.get("GOOGLE_CLOUD_KEY")
    
    if not creds_file and not creds_json:
        print_error("Google Cloud credentials not found")
        return False
    
    if creds_file:
        if os.path.exists(creds_file):
            print_success(f"Google Cloud credentials file exists: {creds_file}")
            try:
                with open(creds_file, 'r') as f:
                    data = json.load(f)
                print_info(f"  Project ID: {data.get('project_id', 'N/A')}")
                print_info(f"  Service Account: {data.get('client_email', 'N/A')}")
                return True
            except:
                print_error("Could not parse Google Cloud JSON file")
                return False
        else:
            print_error(f"Google Cloud file not found: {creds_file}")
            return False
    
    if creds_json:
        try:
            data = json.loads(creds_json)
            print_success("Google Cloud credentials in environment")
            print_info(f"  Project ID: {data.get('project_id', 'N/A')}")
            return True
        except:
            print_error("Invalid Google Cloud JSON in environment")
            return False

def validate_pinecone():
    """Check Pinecone credentials"""
    print_header("Checking Pinecone Credentials")
    
    api_key = os.environ.get("PINECONE_API_KEY")
    environment = os.environ.get("PINECONE_ENVIRONMENT", "us-east-1")
    
    if not api_key:
        print_error("PINECONE_API_KEY not found")
        return False
    
    print_success("Pinecone API key found")
    print_info(f"  Environment: {environment}")
    print_info("  Run full validation to test connection")
    return True

def check_optional():
    """Check optional configurations"""
    print_header("Optional Configurations")
    
    # Email
    email = os.environ.get("ALARM_EMAIL")
    if email:
        print_success(f"Alert email: {email}")
    else:
        print_info("Alert email not configured")
    
    # Slack
    if os.environ.get("SLACK_WEBHOOK_URL"):
        print_success("Slack webhook configured")
    else:
        print_info("Slack webhook not configured")
    
    # Domain
    domain = os.environ.get("DOMAIN_NAME")
    if domain:
        print_success(f"Domain: {domain}")
    else:
        print_info("Custom domain not configured")

def generate_env_file():
    """Generate .env file template"""
    print_header("Generating .env.simple")
    
    env_content = f"""# ISEE Tutor Environment Configuration
# Generated by simple validator

# AWS
AWS_ACCESS_KEY_ID={os.environ.get('AWS_ACCESS_KEY_ID', 'your-key-here')}
AWS_SECRET_ACCESS_KEY={os.environ.get('AWS_SECRET_ACCESS_KEY', 'your-secret-here')}

# OpenAI
OPENAI_API_KEY={os.environ.get('OPENAI_API_KEY', 'sk-...')}

# Google Cloud (use one of these)
GOOGLE_APPLICATION_CREDENTIALS={os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', '/path/to/key.json')}
# GOOGLE_CLOUD_KEY='paste-json-content-here'

# Pinecone
PINECONE_API_KEY={os.environ.get('PINECONE_API_KEY', 'your-pinecone-key')}
PINECONE_ENVIRONMENT={os.environ.get('PINECONE_ENVIRONMENT', 'us-east-1')}

# Optional
ALARM_EMAIL={os.environ.get('ALARM_EMAIL', 'your-email@example.com')}
"""
    
    with open('.env.simple', 'w') as f:
        f.write(env_content)
    
    print_success("Created .env.simple")

def main():
    print(f"\n{MAGENTA}🔍 ISEE Tutor Simple Credential Validator{RESET}")
    print(f"{MAGENTA}{'='*60}{RESET}\n")
    
    # Check each service
    aws_ok = validate_aws()
    openai_ok = validate_openai()
    google_ok = validate_google()
    pinecone_ok = validate_pinecone()
    
    # Optional
    check_optional()
    
    # Summary
    print_header("Summary")
    
    all_ok = aws_ok and openai_ok and google_ok and pinecone_ok
    
    if aws_ok:
        print_success("AWS: Ready")
    else:
        print_error("AWS: Not configured")
    
    if openai_ok:
        print_success("OpenAI: Ready")
    else:
        print_error("OpenAI: Not configured")
    
    if google_ok:
        print_success("Google Cloud: Ready")
    else:
        print_error("Google Cloud: Not configured")
    
    if pinecone_ok:
        print_success("Pinecone: Ready")
    else:
        print_error("Pinecone: Not configured")
    
    print()
    
    if all_ok:
        print(f"{GREEN}✅ All credentials configured!{RESET}")
        generate_env_file()
        print(f"\n{GREEN}Ready to deploy!{RESET}")
        print("\nNext steps:")
        print("1. cd ../terraform/scripts")
        print("2. ./deploy.sh dev")
    else:
        print(f"{RED}❌ Some credentials missing{RESET}")
        print("\nMissing credentials:")
        
        if not aws_ok:
            print("\nAWS:")
            print("export AWS_ACCESS_KEY_ID=your-key")
            print("export AWS_SECRET_ACCESS_KEY=your-secret")
        
        if not openai_ok:
            print("\nOpenAI:")
            print("export OPENAI_API_KEY=sk-...")
        
        if not google_ok:
            print("\nGoogle Cloud:")
            print("export GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json")
        
        if not pinecone_ok:
            print("\nPinecone:")
            print("export PINECONE_API_KEY=your-key")
    
    return 0 if all_ok else 1

if __name__ == "__main__":
    sys.exit(main())