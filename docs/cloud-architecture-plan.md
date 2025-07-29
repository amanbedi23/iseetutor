# Cloud-Native Architecture for ISEE Tutor on Raspberry Pi 5

## Overview

This architecture runs only the UI on Raspberry Pi 5, with all backend services, databases, and AI in the cloud.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Raspberry Pi 5 (16GB)                     │
├─────────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────────────────┐ │
│ │               Docker Container: Frontend                  │ │
│ │                                                          │ │
│ │  - React App (Static Files)                             │ │
│ │  - Nginx Web Server                                     │ │
│ │  - Touch UI Optimized                                   │ │
│ │  - WebSocket Client                                     │ │
│ │  - Port: 80/443                                         │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                               │
                               │ HTTPS/WSS
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                  Cloud Infrastructure (AWS/GCP/Azure)        │
├─────────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────────────────┐ │
│ │              Container Orchestration (ECS/GKE/AKS)       │ │
│ ├─────────────────────────────────────────────────────────┤ │
│ │                                                          │ │
│ │  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐ │ │
│ │  │  Backend    │  │   Celery     │  │   Celery Beat  │ │ │
│ │  │  API        │  │   Workers    │  │   Scheduler    │ │ │
│ │  │  (FastAPI)  │  │              │  │                │ │ │
│ │  └─────────────┘  └──────────────┘  └────────────────┘ │ │
│ │                                                          │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                              │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │                   Managed Services                       │ │
│ ├─────────────────────────────────────────────────────────┤ │
│ │                                                          │ │
│ │  ┌──────────────┐  ┌────────────────┐  ┌─────────────┐ │ │
│ │  │  PostgreSQL  │  │     Redis      │  │   S3/GCS    │ │ │
│ │  │  (RDS/Cloud  │  │  (ElastiCache/ │  │  (Object    │ │ │
│ │  │     SQL)     │  │   MemoryStore) │  │   Storage)  │ │ │
│ │  └──────────────┘  └────────────────┘  └─────────────┘ │ │
│ │                                                          │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                              │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │                    AI Services                           │ │
│ ├─────────────────────────────────────────────────────────┤ │
│ │                                                          │ │
│ │  ┌──────────────┐  ┌────────────────┐  ┌─────────────┐ │ │
│ │  │   OpenAI/    │  │  Google Cloud  │  │   Amazon    │ │ │
│ │  │  Anthropic   │  │   Speech API   │  │    Polly    │ │ │
│ │  │    (LLM)     │  │     (STT)      │  │    (TTS)    │ │ │
│ │  └──────────────┘  └────────────────┘  └─────────────┘ │ │
│ │                                                          │ │
│ │  ┌──────────────┐  ┌────────────────┐                  │ │
│ │  │   Pinecone   │  │    CloudAMQP   │                  │ │
│ │  │  (Vector DB) │  │  (Message Queue)│                  │ │
│ │  └──────────────┘  └────────────────┘                  │ │
│ │                                                          │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Benefits of This Architecture

1. **Minimal Pi Requirements**
   - Only runs static web files
   - No databases or heavy processing
   - ~500MB RAM usage maximum
   - No heat/cooling issues

2. **Scalability**
   - Backend scales independently
   - Multi-user support built-in
   - Easy updates without touching Pi

3. **Reliability**
   - Cloud uptime guarantees
   - Automatic backups
   - No SD card corruption risks

4. **Cost Optimization**
   - Pay-per-use AI services
   - Managed database backups
   - No local storage needs

## Cloud Service Recommendations

### For AWS:
- **Compute**: ECS Fargate (serverless containers)
- **Database**: RDS PostgreSQL
- **Cache**: ElastiCache Redis
- **Storage**: S3
- **CDN**: CloudFront
- **AI**: Bedrock (LLM), Transcribe (STT), Polly (TTS)

### For Google Cloud:
- **Compute**: Cloud Run (serverless containers)
- **Database**: Cloud SQL PostgreSQL
- **Cache**: MemoryStore Redis
- **Storage**: Cloud Storage
- **CDN**: Cloud CDN
- **AI**: Vertex AI (LLM), Speech-to-Text, Text-to-Speech

### For Azure:
- **Compute**: Container Instances
- **Database**: Azure Database for PostgreSQL
- **Cache**: Azure Cache for Redis
- **Storage**: Blob Storage
- **CDN**: Azure CDN
- **AI**: OpenAI Service, Speech Services

## Raspberry Pi Setup

### What Runs on Pi:
1. **Single Docker Container**:
   - Nginx serving React build
   - Environment variables for API endpoint
   - Auto-restart on failure
   - Kiosk mode browser

### Pi Requirements:
- Raspberry Pi 5 (4GB would suffice, 16GB is overkill)
- 32GB SD card (8GB would work)
- Touch display via HDMI/USB
- Stable internet connection

## Implementation Steps

1. **Frontend Container Only**:
   ```dockerfile
   FROM node:20-alpine AS builder
   WORKDIR /app
   COPY frontend/package*.json ./
   RUN npm ci
   COPY frontend/ ./
   ARG REACT_APP_API_URL
   ENV REACT_APP_API_URL=$REACT_APP_API_URL
   RUN npm run build

   FROM nginx:alpine
   COPY --from=builder /app/build /usr/share/nginx/html
   COPY nginx.conf /etc/nginx/conf.d/default.conf
   ```

2. **Simple Docker Compose for Pi**:
   ```yaml
   version: '3.8'
   services:
     frontend:
       image: iseetutor/frontend:latest
       ports:
         - "80:80"
       environment:
         - API_URL=https://api.iseetutor.cloud
       restart: always
   ```

3. **Cloud Backend Deployment**:
   - Use Terraform/CloudFormation for infrastructure
   - Deploy backend containers to managed service
   - Configure auto-scaling policies
   - Set up monitoring and alerts

## Cost Estimates (Monthly)

### Cloud Services:
- **Compute**: $50-100 (auto-scaling containers)
- **Database**: $50-100 (managed PostgreSQL)
- **Redis**: $25-50 (managed cache)
- **AI APIs**: 
  - OpenAI: $50-200 (usage-based)
  - Google STT: $20-50
  - Amazon Polly: $10-20
  - Pinecone: $70+
- **Total**: $275-590/month

### vs Original Architecture:
- No Jetson hardware cost ($400-600)
- No local maintenance
- Pay-per-use instead of fixed capacity
- Multi-user capable

## Security Considerations

1. **API Security**:
   - HTTPS only
   - API key authentication
   - Rate limiting
   - IP allowlisting (optional)

2. **Data Privacy**:
   - Encrypted in transit (TLS)
   - Encrypted at rest (cloud provider)
   - COPPA compliance for children's data
   - Regional data residency options

3. **Pi Security**:
   - Read-only filesystem
   - No sensitive data stored
   - Auto-updates for security patches
   - Kiosk mode lockdown

## Migration Path

1. **Phase 1**: Deploy backend to cloud (keep AI local)
2. **Phase 2**: Migrate AI to cloud services
3. **Phase 3**: Move databases to managed services
4. **Phase 4**: Deploy lightweight frontend to Pi

This architecture is ideal for Raspberry Pi deployment and provides better scalability, reliability, and maintenance compared to the original edge-computing approach.