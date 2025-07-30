#!/bin/bash

# Script to run ISEE Tutor locally with cloud services

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting ISEE Tutor Local Development${NC}"
echo ""

# Check if .env.local exists
if [ ! -f .env.local ]; then
    echo -e "${RED}Error: .env.local file not found!${NC}"
    echo "Please create .env.local with your cloud service credentials"
    exit 1
fi

# Check if google-service-account.json exists
if [ ! -f google-service-account.json ]; then
    echo -e "${RED}Error: google-service-account.json file not found!${NC}"
    echo "Please create google-service-account.json with your Google Cloud credentials"
    exit 1
fi

# Build and start containers
echo -e "${YELLOW}Building Docker images...${NC}"
docker compose --env-file .env.local -f docker-compose.local.yml build

echo -e "${YELLOW}Starting containers...${NC}"
docker compose --env-file .env.local -f docker-compose.local.yml up -d

# Wait for backend to be healthy
echo -e "${YELLOW}Waiting for backend to be ready...${NC}"
max_attempts=30
attempt=1
while [ $attempt -le $max_attempts ]; do
    if docker compose --env-file .env.local -f docker-compose.local.yml exec backend curl -f http://localhost:8000/health >/dev/null 2>&1; then
        echo -e "${GREEN}✓ Backend is ready!${NC}"
        break
    fi
    echo -n "."
    sleep 2
    attempt=$((attempt + 1))
done

if [ $attempt -gt $max_attempts ]; then
    echo -e "${RED}Backend failed to start. Check logs with: docker compose --env-file .env.local -f docker-compose.local.yml logs backend${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}✅ ISEE Tutor is running!${NC}"
echo ""
echo "🌐 Frontend: http://localhost:3000"
echo "🚀 Backend API: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "📋 Useful commands:"
echo "  View logs:    docker compose --env-file .env.local -f docker-compose.local.yml logs -f"
echo "  Stop:         docker compose --env-file .env.local -f docker-compose.local.yml down"
echo "  Restart:      docker compose --env-file .env.local -f docker-compose.local.yml restart"
echo "  Backend logs: docker compose --env-file .env.local -f docker-compose.local.yml logs -f backend"
echo "  Frontend logs: docker compose --env-file .env.local -f docker-compose.local.yml logs -f frontend"
echo ""