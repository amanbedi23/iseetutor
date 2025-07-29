#!/bin/bash

# ISEE Tutor Credential Setup Script
# More robust version with better error handling

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
NC='\033[0m'

# Don't exit on error
set +e

# Functions
print_header() {
    echo -e "\n${MAGENTA}========================================${NC}"
    echo -e "${MAGENTA}$1${NC}"
    echo -e "${MAGENTA}========================================${NC}\n"
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

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# Main script
clear
echo -e "${MAGENTA}🚀 ISEE Tutor Credential Setup${NC}"
echo -e "${MAGENTA}================================${NC}\n"

# Create credentials file
CREDS_FILE="$HOME/.iseetutor-credentials"
echo "# ISEE Tutor Credentials - $(date)" > $CREDS_FILE
echo "# Source this file: source $CREDS_FILE" >> $CREDS_FILE
chmod 600 $CREDS_FILE

# Track what's configured
AWS_CONFIGURED=false
OPENAI_CONFIGURED=false
GOOGLE_CONFIGURED=false
PINECONE_CONFIGURED=false

print_header "Checking Existing Credentials"

# Check AWS
if [ -n "$AWS_ACCESS_KEY_ID" ] && [ -n "$AWS_SECRET_ACCESS_KEY" ]; then
    print_success "AWS credentials found in environment"
    echo "export AWS_ACCESS_KEY_ID=\"$AWS_ACCESS_KEY_ID\"" >> $CREDS_FILE
    echo "export AWS_SECRET_ACCESS_KEY=\"$AWS_SECRET_ACCESS_KEY\"" >> $CREDS_FILE
    AWS_CONFIGURED=true
else
    print_warning "AWS credentials not found"
fi

# Check OpenAI
if [ -n "$OPENAI_API_KEY" ]; then
    print_success "OpenAI API key found in environment"
    echo "export OPENAI_API_KEY=\"$OPENAI_API_KEY\"" >> $CREDS_FILE
    OPENAI_CONFIGURED=true
else
    print_warning "OpenAI API key not found"
fi

# Check Google Cloud
if [ -n "$GOOGLE_APPLICATION_CREDENTIALS" ] || [ -n "$GOOGLE_CLOUD_KEY" ]; then
    print_success "Google Cloud credentials found in environment"
    if [ -n "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
        echo "export GOOGLE_APPLICATION_CREDENTIALS=\"$GOOGLE_APPLICATION_CREDENTIALS\"" >> $CREDS_FILE
    fi
    if [ -n "$GOOGLE_CLOUD_KEY" ]; then
        echo "export GOOGLE_CLOUD_KEY='$GOOGLE_CLOUD_KEY'" >> $CREDS_FILE
    fi
    GOOGLE_CONFIGURED=true
else
    print_warning "Google Cloud credentials not found"
fi

# Check Pinecone
if [ -n "$PINECONE_API_KEY" ]; then
    print_success "Pinecone API key found in environment"
    echo "export PINECONE_API_KEY=\"$PINECONE_API_KEY\"" >> $CREDS_FILE
    echo "export PINECONE_ENVIRONMENT=\"${PINECONE_ENVIRONMENT:-us-east-1}\"" >> $CREDS_FILE
    PINECONE_CONFIGURED=true
else
    print_warning "Pinecone API key not found"
fi

# Now let's set up missing credentials
print_header "Setting Up Missing Credentials"

# AWS Setup
if [ "$AWS_CONFIGURED" = false ]; then
    echo -e "\n${YELLOW}AWS Credentials Setup${NC}"
    echo "1. Go to: https://console.aws.amazon.com/iam"
    echo "2. Create IAM user 'iseetutor-admin' with AdministratorAccess"
    echo "3. Create access key"
    echo ""
    read -p "Enter AWS Access Key ID (or press Enter to skip): " AWS_KEY
    if [ -n "$AWS_KEY" ]; then
        read -s -p "Enter AWS Secret Access Key: " AWS_SECRET
        echo
        echo "export AWS_ACCESS_KEY_ID=\"$AWS_KEY\"" >> $CREDS_FILE
        echo "export AWS_SECRET_ACCESS_KEY=\"$AWS_SECRET\"" >> $CREDS_FILE
        export AWS_ACCESS_KEY_ID="$AWS_KEY"
        export AWS_SECRET_ACCESS_KEY="$AWS_SECRET"
        print_success "AWS credentials saved"
    else
        print_info "Skipping AWS setup"
    fi
fi

# OpenAI Setup
if [ "$OPENAI_CONFIGURED" = false ]; then
    echo -e "\n${YELLOW}OpenAI API Key Setup${NC}"
    echo "1. Go to: https://platform.openai.com/api-keys"
    echo "2. Create new secret key"
    echo ""
    read -p "Enter OpenAI API Key (or press Enter to skip): " OPENAI_KEY
    if [ -n "$OPENAI_KEY" ]; then
        echo "export OPENAI_API_KEY=\"$OPENAI_KEY\"" >> $CREDS_FILE
        export OPENAI_API_KEY="$OPENAI_KEY"
        print_success "OpenAI API key saved"
    else
        print_info "Skipping OpenAI setup"
    fi
fi

# Google Cloud Setup - Special handling for your case
if [ "$GOOGLE_CONFIGURED" = false ]; then
    echo -e "\n${YELLOW}Google Cloud Setup${NC}"
    
    # Check if the file you mentioned exists
    KNOWN_FILE="/Users/amanbedi/VSCode/iseetutor/docs/keys/iseetutor-3a7999ec1e31.json"
    if [ -f "$KNOWN_FILE" ]; then
        print_success "Found Google Cloud key file at: $KNOWN_FILE"
        echo "export GOOGLE_APPLICATION_CREDENTIALS=\"$KNOWN_FILE\"" >> $CREDS_FILE
        export GOOGLE_APPLICATION_CREDENTIALS="$KNOWN_FILE"
        
        # Also try to read the content
        if [ -r "$KNOWN_FILE" ]; then
            GOOGLE_CONTENT=$(cat "$KNOWN_FILE" 2>/dev/null)
            if [ -n "$GOOGLE_CONTENT" ]; then
                # Escape single quotes by replacing ' with '\''
                ESCAPED_CONTENT=$(echo "$GOOGLE_CONTENT" | sed "s/'/'\\\\''/g")
                echo "export GOOGLE_CLOUD_KEY='$ESCAPED_CONTENT'" >> $CREDS_FILE
                export GOOGLE_CLOUD_KEY="$GOOGLE_CONTENT"
                print_success "Google Cloud credentials configured!"
            fi
        fi
    else
        echo "Enter path to Google Cloud JSON key file"
        echo "(or press Enter to skip): "
        read -p "> " GOOGLE_KEY_PATH
        if [ -n "$GOOGLE_KEY_PATH" ] && [ -f "$GOOGLE_KEY_PATH" ]; then
            echo "export GOOGLE_APPLICATION_CREDENTIALS=\"$GOOGLE_KEY_PATH\"" >> $CREDS_FILE
            export GOOGLE_APPLICATION_CREDENTIALS="$GOOGLE_KEY_PATH"
            print_success "Google Cloud path saved"
        else
            print_info "Skipping Google Cloud setup"
        fi
    fi
fi

# Pinecone Setup
if [ "$PINECONE_CONFIGURED" = false ]; then
    echo -e "\n${YELLOW}Pinecone Setup${NC}"
    echo "1. Go to: https://www.pinecone.io"
    echo "2. Sign up and get API key"
    echo ""
    read -p "Enter Pinecone API Key (or press Enter to skip): " PINECONE_KEY
    if [ -n "$PINECONE_KEY" ]; then
        read -p "Enter Pinecone Environment (default: us-east-1): " PINECONE_ENV
        PINECONE_ENV=${PINECONE_ENV:-us-east-1}
        echo "export PINECONE_API_KEY=\"$PINECONE_KEY\"" >> $CREDS_FILE
        echo "export PINECONE_ENVIRONMENT=\"$PINECONE_ENV\"" >> $CREDS_FILE
        export PINECONE_API_KEY="$PINECONE_KEY"
        export PINECONE_ENVIRONMENT="$PINECONE_ENV"
        print_success "Pinecone credentials saved"
    else
        print_info "Skipping Pinecone setup"
    fi
fi

# Additional settings
print_header "Additional Settings"

if [ -z "$ALARM_EMAIL" ]; then
    read -p "Enter email for alerts (or press Enter to skip): " ALARM_EMAIL
    if [ -n "$ALARM_EMAIL" ]; then
        echo "export ALARM_EMAIL=\"$ALARM_EMAIL\"" >> $CREDS_FILE
        export ALARM_EMAIL="$ALARM_EMAIL"
    fi
fi

# Summary
print_header "Setup Summary"

echo "Credentials file created: $CREDS_FILE"
echo ""
echo "Configured services:"

# Check what we have
source $CREDS_FILE

if [ -n "$AWS_ACCESS_KEY_ID" ]; then
    print_success "AWS credentials"
else
    print_error "AWS credentials missing"
fi

if [ -n "$OPENAI_API_KEY" ]; then
    print_success "OpenAI API key"
else
    print_error "OpenAI API key missing"
fi

if [ -n "$GOOGLE_APPLICATION_CREDENTIALS" ] || [ -n "$GOOGLE_CLOUD_KEY" ]; then
    print_success "Google Cloud credentials"
else
    print_error "Google Cloud credentials missing"
fi

if [ -n "$PINECONE_API_KEY" ]; then
    print_success "Pinecone API key"
else
    print_error "Pinecone API key missing"
fi

echo ""
echo "To use these credentials:"
echo "  ${GREEN}source $CREDS_FILE${NC}"
echo ""
echo "To validate credentials:"
echo "  ${GREEN}python3 validate-credentials.py${NC}"
echo ""
echo "To add to GitHub:"
echo "  ${GREEN}./setup-github-secrets.sh${NC}"

# Create minimal test script
cat > test-credentials.sh << 'EOF'
#!/bin/bash
source $HOME/.iseetutor-credentials

echo "Testing credentials..."
echo ""

# Test AWS
if [ -n "$AWS_ACCESS_KEY_ID" ]; then
    if aws sts get-caller-identity >/dev/null 2>&1; then
        echo "✓ AWS: Working"
    else
        echo "✗ AWS: Failed"
    fi
else
    echo "- AWS: Not configured"
fi

# Test OpenAI
if [ -n "$OPENAI_API_KEY" ]; then
    echo "✓ OpenAI: Configured (run validate-credentials.py to test)"
else
    echo "- OpenAI: Not configured"
fi

# Test Google
if [ -n "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
    if [ -f "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
        echo "✓ Google Cloud: File exists"
    else
        echo "✗ Google Cloud: File not found"
    fi
else
    echo "- Google Cloud: Not configured"
fi

# Test Pinecone
if [ -n "$PINECONE_API_KEY" ]; then
    echo "✓ Pinecone: Configured (run validate-credentials.py to test)"
else
    echo "- Pinecone: Not configured"
fi
EOF

chmod +x test-credentials.sh

echo ""
echo "Created test-credentials.sh for quick testing"
echo ""
print_success "Setup complete! (partial configuration is OK)"