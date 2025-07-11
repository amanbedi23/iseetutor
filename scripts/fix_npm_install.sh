#!/bin/bash
# Fix npm/nodejs conflict and install dependencies

echo "=== Fixing npm/nodejs conflict ==="

# First, let's check what's installed
echo "Checking current nodejs/npm status..."
node --version 2>/dev/null && echo "Node.js is installed" || echo "Node.js not found"
npm --version 2>/dev/null && echo "npm is installed" || echo "npm not found"

echo ""
echo "The issue is that nodejs from nodesource conflicts with Ubuntu's npm package."
echo "Since you have Node.js v20 from nodesource, npm should already be included."
echo ""

# Check if npm is actually available
if command -v npm &> /dev/null; then
    echo "✅ npm is already available (version $(npm --version))"
else
    echo "npm not found in PATH. Let's check if it's installed with Node.js..."
    
    # Sometimes npm is installed but not in PATH
    if [ -f "/usr/bin/npm" ]; then
        echo "✅ npm found at /usr/bin/npm"
    elif [ -f "/usr/local/bin/npm" ]; then
        echo "✅ npm found at /usr/local/bin/npm"
    else
        echo "❌ npm not found. Installing npm that comes with Node.js..."
        
        # Try to reinstall nodejs to get npm
        echo "Reinstalling Node.js to ensure npm is included..."
        echo "Run: sudo apt install --reinstall nodejs"
    fi
fi

echo ""
echo "=== Installing remaining dependencies ==="
echo "Run these commands to install the remaining packages:"
echo ""
echo "sudo apt install -y \\"
echo "    portaudio19-dev \\"
echo "    ffmpeg \\"
echo "    tesseract-ocr \\"
echo "    postgresql \\"
echo "    postgresql-contrib \\"
echo "    redis-server"
echo ""
echo "After fixing npm, continue with the Python packages installation."