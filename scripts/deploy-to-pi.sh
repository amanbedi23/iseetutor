#!/bin/bash

# ISEE Tutor Deployment Script for Raspberry Pi 5
# This script deploys the dockerized application to a Raspberry Pi

set -e  # Exit on error

echo "🚀 ISEE Tutor Raspberry Pi Deployment Script"
echo "==========================================="

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PI_HOST="${PI_HOST:-raspberrypi.local}"
PI_USER="${PI_USER:-pi}"
DEPLOY_PATH="/home/${PI_USER}/iseetutor"
COMPOSE_FILE="docker-compose.yml"
ENV_FILE=".env"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to print colored output
print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

# Check prerequisites
echo "Checking prerequisites..."

if ! command_exists docker; then
    print_error "Docker is not installed locally. Please install Docker."
    exit 1
fi

if ! command_exists docker-compose; then
    print_error "Docker Compose is not installed locally. Please install Docker Compose."
    exit 1
fi

if [ ! -f "$ENV_FILE" ]; then
    print_error "Environment file (.env) not found. Please copy .env.docker to .env and configure it."
    exit 1
fi

print_status "Prerequisites checked"

# Build images for ARM64
echo -e "\nBuilding Docker images for ARM64..."

# Set up Docker buildx for multi-platform builds
if ! docker buildx ls | grep -q "iseetutor-builder"; then
    echo "Creating buildx builder for ARM64..."
    docker buildx create --name iseetutor-builder --use
    docker buildx inspect --bootstrap
fi

# Build frontend image for ARM64
echo "Building frontend image..."
docker buildx build \
    --platform linux/arm64 \
    --tag iseetutor/frontend:latest \
    --file Dockerfile.frontend \
    --load \
    .

print_status "Frontend image built"

# Build backend image for ARM64
echo "Building backend image..."
docker buildx build \
    --platform linux/arm64 \
    --tag iseetutor/backend:latest \
    --file Dockerfile.backend \
    --load \
    .

print_status "Backend image built"

# Save images to transfer
echo -e "\nSaving Docker images..."
mkdir -p ./deploy

docker save iseetutor/frontend:latest | gzip > ./deploy/frontend.tar.gz
docker save iseetutor/backend:latest | gzip > ./deploy/backend.tar.gz

print_status "Images saved"

# Prepare deployment files
echo -e "\nPreparing deployment files..."
cp docker-compose.yml ./deploy/
cp .env ./deploy/
cp -r scripts ./deploy/

# Create deployment archive
tar -czf iseetutor-deploy.tar.gz ./deploy

print_status "Deployment archive created"

# Deploy to Raspberry Pi
echo -e "\nDeploying to Raspberry Pi at ${PI_HOST}..."

# Check if we can connect to Pi
if ! ssh -o ConnectTimeout=5 ${PI_USER}@${PI_HOST} "echo 'Connected'" > /dev/null 2>&1; then
    print_error "Cannot connect to Raspberry Pi at ${PI_HOST}"
    echo "Please ensure:"
    echo "  1. Raspberry Pi is powered on and connected to network"
    echo "  2. SSH is enabled on the Pi"
    echo "  3. You can ping ${PI_HOST}"
    exit 1
fi

# Copy files to Pi
echo "Copying files to Raspberry Pi..."
scp iseetutor-deploy.tar.gz ${PI_USER}@${PI_HOST}:~/

# Execute deployment on Pi
echo "Executing deployment on Raspberry Pi..."
ssh ${PI_USER}@${PI_HOST} << 'ENDSSH'
set -e

echo "Setting up ISEE Tutor on Raspberry Pi..."

# Extract deployment files
tar -xzf ~/iseetutor-deploy.tar.gz
cd ~/deploy

# Create application directory
mkdir -p /home/pi/iseetutor
cp -r * /home/pi/iseetutor/
cd /home/pi/iseetutor

# Load Docker images
echo "Loading Docker images..."
docker load < frontend.tar.gz
docker load < backend.tar.gz

# Check if Docker is installed
if ! command -v docker >/dev/null 2>&1; then
    echo "Docker not found on Pi. Installing Docker..."
    curl -sSL https://get.docker.com | sh
    sudo usermod -aG docker $USER
    echo "Please log out and back in for Docker permissions to take effect"
fi

# Start services
echo "Starting ISEE Tutor services..."
docker-compose down || true
docker-compose up -d

# Wait for services to start
echo "Waiting for services to start..."
sleep 10

# Check service health
if docker-compose ps | grep -q "Up"; then
    echo "✅ Services started successfully!"
else
    echo "❌ Some services failed to start"
    docker-compose logs
fi

# Clean up
rm -f ~/iseetutor-deploy.tar.gz
rm -f frontend.tar.gz backend.tar.gz

echo "Deployment complete!"
ENDSSH

print_status "Deployment completed"

# Clean up local files
rm -rf ./deploy
rm -f iseetutor-deploy.tar.gz

# Display status
echo -e "\n${GREEN}================================${NC}"
echo -e "${GREEN}Deployment Successful!${NC}"
echo -e "${GREEN}================================${NC}"
echo ""
echo "ISEE Tutor is now running on your Raspberry Pi"
echo ""
echo "Access the application at:"
echo "  - Web UI: http://${PI_HOST}"
echo "  - API Docs: http://${PI_HOST}:8000/docs"
echo ""
echo "To view logs:"
echo "  ssh ${PI_USER}@${PI_HOST} 'cd /home/pi/iseetutor && docker-compose logs -f'"
echo ""
echo "To stop services:"
echo "  ssh ${PI_USER}@${PI_HOST} 'cd /home/pi/iseetutor && docker-compose down'"
echo ""

# Optional: Set up as system service
read -p "Would you like to set up ISEE Tutor to start on boot? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Setting up systemd service..."
    ssh ${PI_USER}@${PI_HOST} << 'ENDSSH'
    # Create systemd service
    sudo tee /etc/systemd/system/iseetutor.service > /dev/null << EOF
[Unit]
Description=ISEE Tutor Educational Companion
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/pi/iseetutor
ExecStart=/usr/bin/docker-compose up -d
ExecStop=/usr/bin/docker-compose down
User=pi
Group=pi

[Install]
WantedBy=multi-user.target
EOF

    # Enable service
    sudo systemctl daemon-reload
    sudo systemctl enable iseetutor.service
    echo "✅ ISEE Tutor will now start automatically on boot"
ENDSSH
fi

echo -e "\n${GREEN}All done! Enjoy ISEE Tutor on your Raspberry Pi 5! 🎉${NC}"