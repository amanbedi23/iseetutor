#!/bin/bash
# Master setup script for ISEE Tutor
# This script guides through the complete setup process

set -e

echo "======================================"
echo "   ISEE Tutor Complete Setup Guide    "
echo "======================================"
echo ""
echo "This script will help you set up the ISEE Tutor with:"
echo "- Python dependencies"
echo "- Llama 3.2 8B model for AI responses"
echo "- Knowledge bases for tutoring and companion mode"
echo "- Database setup"
echo ""
echo "Prerequisites:"
echo "- sudo access for installing system packages"
echo "- ~50GB free space on /mnt/storage"
echo "- Internet connection for downloads"
echo ""
read -p "Ready to begin? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
fi

# Step 1: Install system dependencies
echo ""
echo "=== Step 1: Installing System Dependencies ==="
echo "This requires sudo access."
echo ""
echo "Run the following command:"
echo "  sudo bash scripts/install_dependencies.sh"
echo ""
read -p "Press Enter after you've run the command..."

# Check if pip is now available
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 not found. Please install Python dependencies first."
    echo "Run: sudo apt install python3-pip"
    exit 1
fi

echo "✅ Python pip installed"

# Step 2: Create virtual environment (optional)
echo ""
echo "=== Step 2: Python Virtual Environment (Optional) ==="
echo "Do you want to use a virtual environment? (recommended)"
read -p "(y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [ ! -d "venv" ]; then
        echo "Creating virtual environment..."
        python3 -m venv venv
    fi
    echo "Activating virtual environment..."
    source venv/bin/activate
    echo "✅ Virtual environment activated"
fi

# Step 3: Install Python packages
echo ""
echo "=== Step 3: Installing Python Packages ==="
echo "This will install all required Python packages..."
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    pip3 install -r requirements.txt || echo "Some packages failed to install. Continue anyway..."
fi

# Step 4: Set up directories
echo ""
echo "=== Step 4: Creating Directory Structure ==="
mkdir -p /mnt/storage/{models,knowledge,content,user_data}
mkdir -p logs
mkdir -p data/{models,content,users}
echo "✅ Directories created"

# Step 5: Download Llama model
echo ""
echo "=== Step 5: Downloading Llama 3.2 8B Model ==="
echo "This will download a 5-6GB model file."
read -p "Download now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    python3 scripts/download_llama_model.py
else
    echo "⚠️  Skipping model download. You'll need to download it later."
fi

# Step 6: Set up knowledge bases
echo ""
echo "=== Step 6: Setting Up Knowledge Bases ==="
echo "This will create local databases for tutoring content."
read -p "Set up knowledge bases? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    python3 scripts/setup_knowledge_bases.py
else
    echo "⚠️  Skipping knowledge base setup."
fi

# Step 7: Database setup
echo ""
echo "=== Step 7: Database Configuration ==="
echo "Setting up PostgreSQL database..."
echo ""
echo "Run these commands with sudo:"
echo "  sudo -u postgres createuser iseetutor -P"
echo "  sudo -u postgres createdb iseetutor_db -O iseetutor"
echo ""
read -p "Press Enter after you've created the database..."

# Step 8: Environment configuration
echo ""
echo "=== Step 8: Environment Configuration ==="
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env 2>/dev/null || cat > .env << 'EOF'
# ISEE Tutor Environment Configuration
APP_ENV=development
APP_DEBUG=True
APP_PORT=8000

# Database
DATABASE_URL=postgresql://iseetutor:iseetutor123@localhost/iseetutor_db

# Model paths
MODEL_PATH=/mnt/storage/models/Llama-3.2-8B-Instruct-Q4_K_M.gguf
KNOWLEDGE_PATH=/mnt/storage/knowledge

# Audio settings
AUDIO_SAMPLE_RATE=16000
AUDIO_CHANNELS=1

# API Keys (optional)
# OPENAI_API_KEY=your_key_here

# Mode settings
DEFAULT_MODE=tutor
ALLOW_MODE_SWITCH=true
EOF
    echo "✅ Created .env file"
    echo "⚠️  Please edit .env to add your database password"
else
    echo "✅ .env file already exists"
fi

# Step 9: Test the setup
echo ""
echo "=== Step 9: Testing Setup ==="
echo "Running companion mode test..."
python3 test_companion_mode_simple.py

# Final summary
echo ""
echo "======================================"
echo "      Setup Complete Summary          "
echo "======================================"
echo ""
echo "✅ Completed:"

# Check what's installed
[ -f "/mnt/storage/models/Llama-3.2-8B-Instruct-Q4_K_M.gguf" ] && echo "  - Llama model downloaded" || echo "  ❌ Llama model not found"
[ -d "/mnt/storage/knowledge/databases" ] && echo "  - Knowledge bases created" || echo "  ❌ Knowledge bases not found"
[ -f ".env" ] && echo "  - Environment configured" || echo "  ❌ .env file not found"
command -v pip3 &> /dev/null && echo "  - Python packages available" || echo "  ❌ pip3 not installed"

echo ""
echo "📝 Next Steps:"
echo "1. Edit .env file with your database password"
echo "2. Start the API server: python3 src/api/main.py"
echo "3. Start the web UI: cd web && npm start"
echo "4. Test voice interaction with hardware"
echo ""
echo "To run the ISEE Tutor:"
echo "  python3 src/main.py"
echo ""
echo "For help, check the documentation in the docs/ folder"