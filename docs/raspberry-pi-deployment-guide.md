# Raspberry Pi 5 Deployment Guide for ISEE Tutor

## Overview

This guide walks you through deploying ISEE Tutor on a Raspberry Pi 5 (16GB) with cloud-based AI services.

## Architecture

```
┌─────────────────────────────┐
│    Raspberry Pi 5 (16GB)    │
├─────────────────────────────┤
│ • Frontend (React + Nginx)  │
│ • Backend API (FastAPI)     │
│ • Local Redis Cache         │
│ • Docker Containers         │
└─────────────────────────────┘
            ↕ API
┌─────────────────────────────┐
│      Cloud Services         │
├─────────────────────────────┤
│ • PostgreSQL Database       │
│ • OpenAI/Anthropic (LLM)    │
│ • Google Cloud Speech (STT) │
│ • Amazon Polly (TTS)        │
│ • Pinecone (Vector DB)      │
└─────────────────────────────┘
```

## Prerequisites

### 1. Raspberry Pi Setup

- Raspberry Pi 5 with 16GB RAM
- 64GB+ SD card (Class 10 or better)
- Raspberry Pi OS (64-bit) installed
- Stable internet connection
- Touch display connected via HDMI/USB

### 2. Cloud Services Setup

#### PostgreSQL Database
- **AWS RDS**: Create a PostgreSQL 14+ instance
- **Google Cloud SQL**: Create a PostgreSQL instance
- **Or any PostgreSQL provider**

#### AI Services
1. **OpenAI API**
   - Sign up at https://platform.openai.com
   - Create API key
   - Add billing (usage-based)

2. **Google Cloud Speech-to-Text**
   - Create GCP project
   - Enable Speech-to-Text API
   - Create service account key

3. **Amazon Polly**
   - Create AWS account
   - Generate access keys
   - Enable Polly service

4. **Pinecone Vector Database**
   - Sign up at https://pinecone.io
   - Create API key
   - Note your environment region

## Installation Steps

### Step 1: Prepare Raspberry Pi

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -sSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt install docker-compose -y

# Reboot to apply changes
sudo reboot
```

### Step 2: Configure Environment

1. Copy `.env.docker` to `.env`:
```bash
cp .env.docker .env
```

2. Edit `.env` with your cloud service credentials:
```bash
nano .env
```

Required values:
- `DATABASE_URL`: Your cloud PostgreSQL connection string
- `OPENAI_API_KEY`: Your OpenAI API key
- `GOOGLE_CLOUD_KEY`: Path to Google service account JSON
- `AWS_ACCESS_KEY_ID` & `AWS_SECRET_ACCESS_KEY`: AWS credentials
- `PINECONE_API_KEY`: Your Pinecone API key

### Step 3: Deploy Using Script

```bash
# Set Pi hostname (if not raspberrypi.local)
export PI_HOST=your-pi-hostname.local

# Run deployment
./scripts/deploy-to-pi.sh
```

### Step 4: Manual Deployment (Alternative)

If the script doesn't work, deploy manually:

```bash
# On your development machine
# Build for ARM64
docker buildx build --platform linux/arm64 -t iseetutor/frontend:latest -f Dockerfile.frontend .
docker buildx build --platform linux/arm64 -t iseetutor/backend:latest -f Dockerfile.backend .

# Save images
docker save iseetutor/frontend:latest | gzip > frontend.tar.gz
docker save iseetutor/backend:latest | gzip > backend.tar.gz

# Copy to Pi
scp frontend.tar.gz backend.tar.gz docker-compose.yml .env pi@raspberrypi.local:~/

# On Raspberry Pi
ssh pi@raspberrypi.local

# Load images
docker load < frontend.tar.gz
docker load < backend.tar.gz

# Start services
docker-compose up -d
```

## Configuration

### 1. Kiosk Mode Setup

Create auto-start script:
```bash
sudo nano /etc/xdg/lxsession/LXDE-pi/autostart
```

Add:
```
@chromium-browser --kiosk --incognito --disable-pinch --overscroll-history-navigation=0 http://localhost
```

### 2. Performance Tuning

Edit `/boot/config.txt`:
```
# Overclock for better performance (optional)
over_voltage=4
arm_freq=2400
gpu_freq=800
```

### 3. Touch Display Calibration

```bash
sudo apt install xinput-calibrator
xinput_calibrator
```

## Monitoring

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
```

### Check Service Health
```bash
# Service status
docker-compose ps

# API health
curl http://localhost:8000/health

# Frontend
curl http://localhost
```

### Resource Usage
```bash
# Docker stats
docker stats

# System resources
htop
```

## Troubleshooting

### Common Issues

1. **Services won't start**
   - Check logs: `docker-compose logs`
   - Verify environment variables
   - Ensure cloud services are accessible

2. **Out of memory**
   - Reduce Docker memory limits in docker-compose.yml
   - Enable swap: `sudo dphys-swapfile swapconfig`

3. **Slow performance**
   - Check internet connection
   - Monitor cloud API latency
   - Reduce concurrent workers

4. **Touch not working**
   - Calibrate touch screen
   - Check USB connection
   - Update touch drivers

### Debug Commands

```bash
# Test cloud connections
# PostgreSQL
psql $DATABASE_URL -c "SELECT 1"

# Redis
redis-cli -h your-redis-host ping

# Test API endpoints
curl -X POST http://localhost:8000/api/companion/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "mode": "tutor"}'
```

## Maintenance

### Updates

```bash
# Pull latest code
git pull

# Rebuild and deploy
./scripts/deploy-to-pi.sh
```

### Backups

Cloud services handle data backups automatically. For local Redis cache:
```bash
# Backup Redis
docker exec iseetutor-redis redis-cli SAVE
docker cp iseetutor-redis:/data/dump.rdb ./redis-backup.rdb
```

### Monitoring Costs

Monitor your cloud service usage:
- OpenAI: https://platform.openai.com/usage
- AWS: CloudWatch billing alerts
- Google Cloud: Billing console
- Pinecone: Dashboard usage metrics

## Security

1. **Network Security**
   - Use firewall rules
   - Enable HTTPS with Let's Encrypt
   - Restrict cloud service access by IP

2. **API Keys**
   - Never commit `.env` file
   - Rotate keys regularly
   - Use least privilege access

3. **Updates**
   - Keep Docker updated
   - Update base images regularly
   - Monitor security advisories

## Performance Optimization

1. **Caching**
   - Redis caches API responses
   - Frontend assets cached by Nginx
   - Browser caching for static files

2. **API Optimization**
   - Batch requests when possible
   - Use streaming for real-time features
   - Implement request queuing

3. **Resource Limits**
   ```yaml
   # In docker-compose.yml
   services:
     backend:
       deploy:
         resources:
           limits:
             memory: 2G
           reservations:
             memory: 1G
   ```

## Cost Estimation

Monthly costs (approximate):
- PostgreSQL: $25-50
- OpenAI: $50-200 (usage-based)
- Google STT: $20-50
- Amazon Polly: $10-20
- Pinecone: $70+
- **Total**: $175-390/month

## Support

For issues:
1. Check logs first
2. Review this guide
3. Check cloud service status pages
4. Open issue on GitHub

## Next Steps

1. Set up monitoring dashboards
2. Configure alerts for errors
3. Implement usage analytics
4. Plan for scaling multiple devices