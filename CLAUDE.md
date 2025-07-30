# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ISEE Tutor is an AI-powered educational companion for children, featuring ISEE test preparation and general knowledge companion modes. The system uses a hybrid architecture with cloud services for AI processing and local deployment for the user interface.

## Architecture Overview

### Cloud Services (AWS/Google Cloud/OpenAI)
- **AI Processing**: OpenAI API for LLM (replaced Llama)
- **Vector Database**: Pinecone for RAG (replaced ChromaDB)
- **Speech Services**: Google Cloud Speech-to-Text and Text-to-Speech
- **Database**: AWS RDS PostgreSQL for user data and progress tracking
- **Cache**: AWS ElastiCache Redis for session management
- **Wake Word**: Picovoice for wake word detection (to be implemented)

### Local Development
- **Frontend**: React 18 with TypeScript (port 3000)
- **Backend**: FastAPI with Python 3.10+ (port 8000)
- **Containerization**: Docker for both frontend and backend
- **Development Mode**: Local containers connect to cloud services

## Common Development Commands

### Local Development with Cloud Services
```bash
# Run containers locally with cloud services
./run-local.sh

# View logs
docker compose --env-file .env.local -f docker-compose.local.yml logs -f

# Stop containers
docker compose --env-file .env.local -f docker-compose.local.yml down

# Rebuild and restart
docker compose --env-file .env.local -f docker-compose.local.yml build
docker compose --env-file .env.local -f docker-compose.local.yml up -d
```

### Cloud Deployment (AWS ECS)
```bash
# Deploy to AWS ECS
cd terraform
./scripts/deploy.sh dev

# Check ECS service status
aws ecs describe-services --cluster isee-tutor-dev --services isee-tutor-dev-backend isee-tutor-dev-frontend

# View CloudWatch logs
aws logs tail /ecs/isee-tutor-dev/backend --follow
aws logs tail /ecs/isee-tutor-dev/frontend --follow
```

### Testing
```bash
# Run tests inside backend container
docker compose --env-file .env.local -f docker-compose.local.yml exec backend pytest

# Test specific component
docker compose --env-file .env.local -f docker-compose.local.yml exec backend pytest tests/test_api.py

# Test API endpoints
curl http://localhost:8000/health
curl http://localhost:8000/docs
```

## Environment Configuration

### Required Environment Variables (.env.local)
```bash
# Database
DATABASE_URL=postgresql://username:password@hostname:5432/iseetutor_db

# Redis
REDIS_URL=redis://hostname:6379/0

# OpenAI
OPENAI_API_KEY=sk-...

# Google Cloud
GOOGLE_APPLICATION_CREDENTIALS=/app/google-service-account.json
GOOGLE_CLOUD_PROJECT=project-id

# Pinecone
PINECONE_API_KEY=...
PINECONE_ENVIRONMENT=us-east-1

# AWS (for deployment)
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=us-east-1

# Picovoice (for wake word - to be implemented)
PICOVOICE_ACCESS_KEY=...
```

### Google Service Account
Create `google-service-account.json` with credentials for:
- Cloud Speech-to-Text API
- Cloud Text-to-Speech API

## High-Level Architecture

### Core Components

1. **API Layer** (`src/api/`)
   - FastAPI server handling HTTP/WebSocket connections
   - Main entry point: `src/api/main.py`
   - Endpoints for tutor mode, companion mode, and system control

2. **Core Services** (`src/core/`)
   - `audio/`: Audio processing (optional in cloud deployment)
   - `companion/`: Companion mode logic and conversation handling
   - `hardware/`: Hardware interfaces (mocked in cloud)
   - `llm/`: OpenAI integration for language models
   - `education/`: Quiz generation, progress tracking, knowledge retrieval

3. **Cloud AI Integration**
   - **LLM**: OpenAI GPT-4/GPT-3.5 via API
   - **STT**: Google Cloud Speech-to-Text
   - **TTS**: Google Cloud Text-to-Speech
   - **Vector Search**: Pinecone for educational content RAG

4. **Data Layer**
   - **PostgreSQL (RDS)**: User profiles, progress, quiz results
   - **Redis (ElastiCache)**: Session management, caching
   - **Pinecone**: Vector embeddings for educational content
   - **S3**: Static content and file storage

### Key Architectural Patterns

1. **Cloud-First AI Pipeline**
   - Speech → Google STT → OpenAI LLM → Google TTS → Audio
   - Pinecone for RAG-enhanced educational responses
   - All heavy processing offloaded to cloud services

2. **Event-Driven Communication**
   - Redis for pub/sub between components
   - WebSocket for real-time UI updates
   - Async/await throughout for non-blocking operations

3. **Security & Privacy**
   - JWT authentication with refresh tokens
   - Role-based access control (student, parent, teacher, admin)
   - All API calls use HTTPS/WSS
   - Sensitive data encrypted at rest in RDS

4. **Scalability**
   - ECS Fargate for auto-scaling containers
   - RDS with read replicas for database scaling
   - CloudFront CDN for static assets
   - API rate limiting and caching

## Development Workflow

### 1. Local Development Setup
```bash
# Clone repository
git clone https://github.com/yourusername/iseetutor.git
cd iseetutor

# Create .env.local with cloud credentials
cp .env.example .env.local
# Edit .env.local with your credentials

# Get Google service account key
# Save as google-service-account.json

# Start local development
./run-local.sh
```

### 2. Making Changes
- Frontend changes: Edit files in `frontend/src/`
- Backend changes: Edit files in `src/`
- Changes are hot-reloaded in development mode

### 3. Testing Changes
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### 4. Deploying to Cloud
```bash
cd terraform
./scripts/deploy.sh dev
```

## Current Implementation Status

### ✅ Phase 1: Core Infrastructure (COMPLETED)
- AWS ECS deployment with Fargate
- RDS PostgreSQL database
- ElastiCache Redis
- Docker multi-platform builds
- CI/CD pipeline with GitHub Actions

### ✅ Phase 2: Cloud AI Integration (COMPLETED)
- OpenAI API integration for LLM
- Pinecone vector database for RAG
- Google Cloud Speech services
- WebSocket real-time communication

### ✅ Phase 3: User Experience (COMPLETED)
- Student learning dashboard with charts
- Achievement system with 12 badges
- Parent portal with reporting
- User onboarding wizard
- Celebration animations

### 🚧 Phase 4: Functionality Implementation (IN PROGRESS)
- [ ] **Companion Chat with OpenAI** - Wire up chat interface to OpenAI API
- [ ] **Quiz System** - Connect quiz generator to frontend
- [ ] **Progress Tracking** - Real-time updates to dashboard
- [ ] **Voice Interaction** - Integrate Google STT/TTS
- [ ] **Wake Word Detection** - Implement Picovoice
- [ ] **Parent Reports** - Generate and email weekly reports

### 📋 Next Development Tasks

1. **Companion Chat Integration**
   - Connect `/api/companion/chat` to OpenAI
   - Implement conversation memory with Redis
   - Add mode switching (tutor/friend/hybrid)

2. **Quiz Functionality**
   - Create quiz UI components
   - Connect to quiz generator API
   - Implement adaptive difficulty

3. **Voice Pipeline**
   - Integrate Google Cloud Speech-to-Text
   - Implement Google Cloud Text-to-Speech
   - Add Picovoice wake word detection
   - Create voice activity indicator

4. **Progress Dashboard**
   - Connect charts to real data
   - Implement real-time updates via WebSocket
   - Add achievement notifications

5. **Parent Features**
   - Weekly report generation
   - Email notifications
   - Goal setting interface

## API Endpoints

### Authentication
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `POST /api/auth/refresh` - Refresh access token
- `GET /api/auth/me` - Get current user

### Companion Mode
- `POST /api/companion/chat` - Send message to AI companion
- `GET /api/companion/mode` - Get current mode
- `PUT /api/companion/mode` - Change mode (tutor/friend/hybrid)

### Quiz System
- `POST /api/quiz/generate` - Generate adaptive quiz
- `POST /api/quiz/submit` - Submit quiz answers
- `GET /api/quiz/history` - Get quiz history
- `GET /api/quiz/knowledge/search` - Search educational content

### Progress Tracking
- `GET /api/progress/summary` - Get progress summary
- `GET /api/progress/subjects/{subject}` - Get subject progress
- `GET /api/progress/achievements` - Get achievements

### Parent Portal
- `GET /api/parent/children` - List children
- `GET /api/parent/children/{id}/progress` - Get child progress
- `GET /api/parent/reports/weekly/{id}` - Generate weekly report

### WebSocket Events
- `connection` - Client connected/disconnected
- `voice_start` - Start voice interaction
- `voice_stop` - Stop voice interaction
- `voice_transcript` - Real-time speech transcription
- `voice_response` - AI response text
- `progress_update` - Real-time progress updates

## Security Considerations

1. **Authentication**: JWT tokens with refresh mechanism
2. **Authorization**: Role-based access control
3. **Input Validation**: Pydantic models for all inputs
4. **Rate Limiting**: API endpoint throttling
5. **CORS**: Configured for specific origins
6. **HTTPS/WSS**: All communications encrypted

## Troubleshooting

### Container Issues
```bash
# Check container status
docker ps

# View container logs
docker logs iseetutor-backend-1
docker logs iseetutor-frontend-1

# Restart containers
docker compose --env-file .env.local -f docker-compose.local.yml restart
```

### Database Connection
```bash
# Test database connection
docker compose --env-file .env.local -f docker-compose.local.yml exec backend python -c "from src.database.base import engine; print(engine.url)"

# Run database migrations
docker compose --env-file .env.local -f docker-compose.local.yml exec backend alembic upgrade head
```

### API Issues
```bash
# Test API health
curl http://localhost:8000/health

# Check API logs
docker compose --env-file .env.local -f docker-compose.local.yml logs backend
```

## Contributing

1. Create feature branch: `git checkout -b feature/your-feature`
2. Make changes and test locally
3. Commit with clear messages
4. Push and create pull request
5. Ensure CI/CD passes before merging

## Production Deployment Notes

- Uses AWS ECS Fargate for container orchestration
- Auto-scaling configured based on CPU/memory
- CloudWatch for logging and monitoring
- Secrets stored in AWS Systems Manager Parameter Store
- Database backups configured with 7-day retention
- Redis configured with automatic failover