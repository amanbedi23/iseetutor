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
