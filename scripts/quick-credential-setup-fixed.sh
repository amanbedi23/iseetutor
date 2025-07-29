#!/bin/bash

# Quick Credential Setup Script for ISEE Tutor
# This script helps you gather all required credentials

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
NC='\033[0m'

# Functions
print_header() {
    echo -e "\n${MAGENTA}========================================${NC}"
    echo -e "${MAGENTA}$1${NC}"
    echo -e "${MAGENTA}========================================${NC}\n"
}

print_step() {
    echo -e "${BLUE}▶ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Check if credential is already set
check_credential() {
    local var_name=$1
    if [ -n "${!var_name}" ]; then
        print_success "$var_name is already set"
        return 0
    else
        return 1
    fi
}

# Main script
clear
echo -e "${MAGENTA}🚀 ISEE Tutor Quick Credential Setup${NC}"
echo -e "${MAGENTA}=====================================${NC}\n"
echo "This script will help you set up all required credentials."
echo "Have these ready:"
echo "  • AWS account with admin access"
echo "  • Credit card for API services"
echo "  • About 15-20 minutes"
echo ""
read -p "Ready to start? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 0
fi

# Create credentials file
CREDS_FILE="$HOME/.iseetutor-credentials"
echo "# ISEE Tutor Credentials - $(date)" > $CREDS_FILE
echo "# Source this file: source $CREDS_FILE" >> $CREDS_FILE
chmod 600 $CREDS_FILE

print_header "Step 1: AWS Credentials"
if ! check_credential "AWS_ACCESS_KEY_ID"; then
    echo "Let's set up AWS credentials."
    echo ""
    print_step "1. Go to: https://console.aws.amazon.com/iam"
    print_step "2. Create a new IAM user named 'iseetutor-admin'"
    print_step "3. Attach policy: AdministratorAccess"
    print_step "4. Create access key"
    echo ""
    read -p "Enter AWS Access Key ID: " AWS_KEY
    read -s -p "Enter AWS Secret Access Key: " AWS_SECRET
    echo
    
    echo "export AWS_ACCESS_KEY_ID=\"$AWS_KEY\"" >> $CREDS_FILE
    echo "export AWS_SECRET_ACCESS_KEY=\"$AWS_SECRET\"" >> $CREDS_FILE
    export AWS_ACCESS_KEY_ID="$AWS_KEY"
    export AWS_SECRET_ACCESS_KEY="$AWS_SECRET"
    
    # Test AWS credentials
    if aws sts get-caller-identity >/dev/null 2>&1; then
        print_success "AWS credentials verified!"
    else
        print_error "AWS credentials invalid. Please check and try again."
        exit 1
    fi
fi

print_header "Step 2: OpenAI API Key"
if ! check_credential "OPENAI_API_KEY"; then
    echo "Let's set up OpenAI API access."
    echo ""
    print_step "1. Go to: https://platform.openai.com/signup"
    print_step "2. Create account (or login)"
    print_step "3. Go to: https://platform.openai.com/api-keys"
    print_step "4. Click 'Create new secret key'"
    print_step "5. Copy the key (starts with sk-)"
    echo ""
    print_warning "Recommended: Add $50-100 credit to start"
    echo ""
    read -p "Enter OpenAI API Key: " OPENAI_KEY
    
    echo "export OPENAI_API_KEY=\"$OPENAI_KEY\"" >> $CREDS_FILE
    export OPENAI_API_KEY="$OPENAI_KEY"
    print_success "OpenAI API key saved!"
fi

print_header "Step 3: Google Cloud (Speech-to-Text)"
if ! check_credential "GOOGLE_CLOUD_KEY"; then
    echo "Let's set up Google Cloud Speech API."
    echo ""
    print_step "1. Go to: https://console.cloud.google.com"
    print_step "2. Create new project called 'iseetutor'"
    print_step "3. Enable Speech-to-Text API:"
    echo "     https://console.cloud.google.com/apis/library/speech.googleapis.com"
    print_step "4. Create service account:"
    echo "     https://console.cloud.google.com/iam-admin/serviceaccounts"
    print_step "5. Download JSON key file"
    echo ""
    read -p "Enter path to Google Cloud JSON key file: " GOOGLE_KEY_PATH
    
    if [ -f "$GOOGLE_KEY_PATH" ]; then
        # Option 1: Try using Python to parse JSON (works on Mac by default)
        if command -v python3 >/dev/null 2>&1; then
            GOOGLE_KEY_CONTENT=$(python3 -c "import json; print(json.dumps(json.load(open('$GOOGLE_KEY_PATH'))))" 2>/dev/null || cat "$GOOGLE_KEY_PATH")
        else
            # Option 2: Just read the file as is
            GOOGLE_KEY_CONTENT=$(cat "$GOOGLE_KEY_PATH")
        fi
        
        # Save to credentials file - need to escape single quotes
        ESCAPED_CONTENT=$(echo "$GOOGLE_KEY_CONTENT" | sed "s/'/'\\\\''/g")
        echo "export GOOGLE_CLOUD_KEY='$ESCAPED_CONTENT'" >> $CREDS_FILE
        export GOOGLE_CLOUD_KEY="$GOOGLE_KEY_CONTENT"
        
        # Also save the file path as an alternative
        echo "export GOOGLE_APPLICATION_CREDENTIALS=\"$GOOGLE_KEY_PATH\"" >> $CREDS_FILE
        export GOOGLE_APPLICATION_CREDENTIALS="$GOOGLE_KEY_PATH"
        
        print_success "Google Cloud credentials saved!"
    else
        print_error "File not found: $GOOGLE_KEY_PATH"
        exit 1
    fi
fi

print_header "Step 4: Pinecone Vector Database"
if ! check_credential "PINECONE_API_KEY"; then
    echo "Let's set up Pinecone for vector search."
    echo ""
    print_step "1. Go to: https://www.pinecone.io"
    print_step "2. Sign up for free account"
    print_step "3. Create a project"
    print_step "4. Go to API Keys section"
    print_step "5. Copy your API key"
    echo ""
    read -p "Enter Pinecone API Key: " PINECONE_KEY
    read -p "Enter Pinecone Environment (default: us-east-1): " PINECONE_ENV
    PINECONE_ENV=${PINECONE_ENV:-us-east-1}
    
    echo "export PINECONE_API_KEY=\"$PINECONE_KEY\"" >> $CREDS_FILE
    echo "export PINECONE_ENVIRONMENT=\"$PINECONE_ENV\"" >> $CREDS_FILE
    export PINECONE_API_KEY="$PINECONE_KEY"
    export PINECONE_ENVIRONMENT="$PINECONE_ENV"
    print_success "Pinecone credentials saved!"
fi

print_header "Step 5: Additional Configuration"

# Email for alerts
if [ -z "$ALARM_EMAIL" ]; then
    read -p "Enter email for system alerts: " ALARM_EMAIL
    echo "export ALARM_EMAIL=\"$ALARM_EMAIL\"" >> $CREDS_FILE
    export ALARM_EMAIL="$ALARM_EMAIL"
fi

# Optional: Slack webhook
read -p "Do you have a Slack webhook URL? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    read -p "Enter Slack Webhook URL: " SLACK_WEBHOOK
    echo "export SLACK_WEBHOOK_URL=\"$SLACK_WEBHOOK\"" >> $CREDS_FILE
    export SLACK_WEBHOOK_URL="$SLACK_WEBHOOK"
fi

# Optional: Custom domain
read -p "Do you have a custom domain? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    read -p "Enter domain name (e.g., iseetutor.com): " DOMAIN
    echo "export DOMAIN_NAME=\"$DOMAIN\"" >> $CREDS_FILE
    export DOMAIN_NAME="$DOMAIN"
fi

print_header "Step 6: Validate Credentials"

# Install validation requirements if needed
if ! python3 -c "import colorama" 2>/dev/null; then
    print_warning "Installing required Python packages..."
    pip3 install -r requirements-validation.txt || pip install -r requirements-validation.txt
fi

# Source the credentials file
source $CREDS_FILE

# Run validation
echo "Running credential validation..."
python3 validate-credentials.py

if [ $? -eq 0 ]; then
    print_header "✅ Setup Complete!"
    echo "Your credentials are saved in: $CREDS_FILE"
    echo ""
    echo "To use these credentials in the future:"
    echo "  source $CREDS_FILE"
    echo ""
    echo "Next steps:"
    echo "1. Set up GitHub secrets: ./setup-github-secrets.sh"
    echo "2. Deploy to AWS: cd ../terraform/scripts && ./deploy.sh dev"
    echo ""
    print_success "You're ready to deploy ISEE Tutor! 🎉"
else
    print_error "Some credentials failed validation. Please check and try again."
    exit 1
fi

# Create quick-start script
cat > quick-deploy.sh << 'EOF'
#!/bin/bash
# Quick deployment script

# Load credentials
source $HOME/.iseetutor-credentials

# Deploy
cd ../terraform/scripts
./deploy.sh dev

# Initialize data
./init-database.sh dev
python3 init-pinecone.py --env dev

echo "Deployment complete!"
EOF

chmod +x quick-deploy.sh

echo ""
echo "Created quick-deploy.sh for easy deployment!"