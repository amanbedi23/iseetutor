# ISEE Tutor System Architecture

## Table of Contents
1. [System Overview](#system-overview)
2. [Architecture Diagram](#architecture-diagram)
3. [Technology Stack](#technology-stack)
4. [Component Details](#component-details)
5. [Data Flow](#data-flow)
6. [Content Processing Pipeline](#content-processing-pipeline)
7. [UI Architecture](#ui-architecture)
8. [Deployment Architecture](#deployment-architecture)

## System Overview

The ISEE Tutor is designed as a modular, event-driven system with clear separation between hardware interfaces, AI services, educational logic, and user interfaces.

### Core Design Principles
- **Modularity**: Each component has a single responsibility
- **Scalability**: Can add new content types and learning modes
- **Offline-First**: Core functionality works without internet
- **Real-Time**: Low-latency voice and touch responses
- **Privacy-First**: All data processing happens locally

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                 ISEE Tutor System                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────┐          ┌──────────────────────┐                │
│  │   Hardware Layer    │          │    User Interfaces   │                │
│  ├─────────────────────┤          ├──────────────────────┤                │
│  │ • ReSpeaker Mic     │          │ • Web UI (React)     │                │
│  │ • USB Speaker       │          │ • Touch UI           │                │
│  │ • Touchscreen       │          │ • Voice UI           │                │
│  │ • LED Ring          │          │ • Parent Dashboard   │                │
│  │ • Push Button       │          └──────────┬───────────┘                │
│  └──────────┬──────────┘                     │                            │
│             │                                 │                            │
│  ┌──────────▼──────────────────────────────────▼─────────────┐           │
│  │                    Communication Layer                      │           │
│  ├────────────────────────────────────────────────────────────┤           │
│  │  WebSocket Server  │  REST API  │  Event Bus (Redis)       │           │
│  └──────────┬─────────────────────────────────┬──────────────┘           │
│             │                                  │                           │
│  ┌──────────▼──────────┐          ┌───────────▼──────────────┐           │
│  │   Core Services     │          │   Educational Engine     │           │
│  ├────────────────────┤          ├──────────────────────────┤           │
│  │ • Audio Manager    │          │ • Content Manager        │           │
│  │ • Speech Recognition│          │ • Quiz Generator        │           │
│  │ • Text-to-Speech   │          │ • Progress Tracker      │           │
│  │ • Wake Word Detect │          │ • Adaptive Learning     │           │
│  │ • LED Controller   │          │ • Session Manager       │           │
│  └──────────┬─────────┘          └───────────┬──────────────┘           │
│             │                                 │                           │
│  ┌──────────▼─────────────────────────────────▼──────────────┐           │
│  │                      AI/ML Layer                           │           │
│  ├────────────────────────────────────────────────────────────┤           │
│  │ • Local LLM (Llama 3.2)  │  • Whisper (Speech-to-Text)   │           │
│  │ • RAG System            │  • Piper (Text-to-Speech)      │           │
│  │ • Embeddings (BGE)      │  • OCR (Tesseract/EasyOCR)    │           │
│  └──────────┬─────────────────────────────────┬──────────────┘           │
│             │                                 │                           │
│  ┌──────────▼─────────────────────────────────▼──────────────┐           │
│  │                    Data Layer                              │           │
│  ├────────────────────────────────────────────────────────────┤           │
│  │ • PostgreSQL (Main DB)  │  • ChromaDB (Vector Store)      │           │
│  │ • Redis (Cache/Queue)   │  • MinIO (Object Storage)       │           │
│  └────────────────────────────────────────────────────────────┘           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Technology Stack

### Core Framework
- **Python 3.10+**: Main application language
- **FastAPI**: High-performance async REST API and WebSocket server
- **Celery**: Distributed task queue for background processing
- **Redis**: Message broker, cache, and session store

### AI/ML Stack
- **LLM**: 
  - Llama 3.2 3B (quantized to 4-bit for Jetson)
  - LangChain for orchestration
  - vLLM or llama.cpp for inference
- **Speech Recognition**: 
  - OpenAI Whisper (base model)
  - Faster-whisper for optimized inference
- **Text-to-Speech**: 
  - Piper TTS (fast, local)
  - Coqui TTS as backup
- **Wake Word**: 
  - Picovoice Porcupine (lightweight)
  - Custom model with OpenWakeWord
- **Embeddings**: 
  - BGE-small for document embeddings
  - ChromaDB for vector storage
- **OCR**: 
  - Tesseract for text extraction
  - EasyOCR for complex layouts

### UI Framework
- **Frontend**:
  - React 18 with TypeScript
  - Material-UI or Ant Design for components
  - Socket.io for real-time updates
  - Framer Motion for animations
  - React Native Web for touch optimization
- **Styling**:
  - Tailwind CSS for utility-first styling
  - CSS-in-JS with Emotion
- **State Management**:
  - Zustand for global state
  - React Query for server state
  - IndexedDB for offline storage

### Data Storage
- **PostgreSQL**: 
  - User profiles and progress
  - Content metadata
  - Quiz questions and results
- **ChromaDB**: 
  - Vector embeddings for RAG
  - Semantic search capabilities
- **MinIO**: 
  - PDF storage
  - Audio recordings
  - Generated content
- **Redis**:
  - Session management
  - Real-time event bus
  - Cache layer

### Hardware Integration
- **GPIO Control**: Jetson.GPIO for button/LED
- **Audio**: PyAudio + sounddevice
- **Display**: Electron or native fullscreen browser

## Component Details

### 1. Audio Pipeline
```python
# Audio flow architecture
class AudioPipeline:
    """
    Mic Array → Noise Reduction → VAD → Buffer → 
    Wake Word Detection → Speech Recognition → NLU
    """
    
    components = {
        'input': 'ReSpeaker 4-mic array',
        'preprocessing': 'WebRTC VAD + noise suppression',
        'wake_word': 'Porcupine or OpenWakeWord',
        'asr': 'Whisper base model',
        'output': 'Piper TTS → Speaker'
    }
```

### 2. Content Processing Pipeline
```python
# Content ingestion flow
class ContentPipeline:
    """
    PDF/Web → Text Extraction → Chunking → 
    Embedding → Vector Store → Metadata Extraction
    """
    
    stages = {
        'extraction': {
            'pdf': 'PyPDF2 + Tesseract OCR',
            'web': 'BeautifulSoup + Readability',
            'docx': 'python-docx'
        },
        'chunking': {
            'method': 'Semantic chunking with langchain',
            'size': '512 tokens with 50 token overlap'
        },
        'embedding': {
            'model': 'BGE-small-en-v1.5',
            'dimension': 384
        },
        'storage': {
            'vectors': 'ChromaDB',
            'metadata': 'PostgreSQL',
            'files': 'MinIO'
        }
    }
```

### 3. Educational Engine
```python
# Core educational logic
class EducationalEngine:
    """
    Manages learning sessions, adaptive difficulty,
    and progress tracking
    """
    
    modules = {
        'question_generator': 'LLM + template system',
        'difficulty_adapter': 'Item Response Theory (IRT)',
        'progress_tracker': 'Spaced repetition algorithm',
        'content_selector': 'Multi-armed bandit approach'
    }
```

### 4. Session Management
```python
# User session architecture
class SessionManager:
    """
    Handles multi-modal sessions with context preservation
    """
    
    features = {
        'voice_context': 'Last 10 interactions',
        'visual_context': 'Current screen state',
        'learning_context': 'Topic, difficulty, progress',
        'persistence': 'Redis with PostgreSQL backup'
    }
```

## Data Flow

### 1. Voice Interaction Flow
```
User Speech → Mic Array → Audio Buffer → Wake Word Detection
    ↓
If wake word detected:
    ↓
Speech Recognition → Text → Intent Classification
    ↓
Educational Engine → Response Generation → TTS → Speaker
    ↓
Update UI + LED Feedback
```

### 2. Content Processing Flow
```
PDF Upload → Text Extraction → Content Analysis
    ↓
Chunk into passages → Generate embeddings
    ↓
Store in ChromaDB → Index metadata in PostgreSQL
    ↓
Generate questions → Validate with LLM → Store in DB
```

### 3. Learning Session Flow
```
User Login → Load Profile → Select Topic
    ↓
Adaptive Algorithm → Select appropriate content
    ↓
Present Question → Capture Response → Evaluate
    ↓
Update progress → Adjust difficulty → Next question
```

## Content Processing Pipeline

### PDF Processing Architecture
```python
# Detailed PDF processing system
class PDFProcessor:
    def __init__(self):
        self.ocr = EasyOCR(['en'])
        self.text_extractor = PyPDF2
        self.chunker = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
    
    async def process_pdf(self, pdf_path):
        # 1. Extract text and images
        text = await self.extract_text(pdf_path)
        images = await self.extract_images(pdf_path)
        
        # 2. OCR on images if needed
        image_text = await self.ocr_images(images)
        
        # 3. Combine and structure content
        structured = await self.structure_content(text + image_text)
        
        # 4. Extract metadata (subject, grade, topics)
        metadata = await self.extract_metadata(structured)
        
        # 5. Generate embeddings
        chunks = self.chunker.split_text(structured)
        embeddings = await self.generate_embeddings(chunks)
        
        # 6. Store in vector DB with metadata
        await self.store_content(chunks, embeddings, metadata)
        
        # 7. Generate practice questions
        questions = await self.generate_questions(chunks, metadata)
        
        return {
            'content_id': uuid4(),
            'chunks': len(chunks),
            'questions': len(questions),
            'metadata': metadata
        }
```

### Content Storage Structure
```
/mnt/storage/
├── content/
│   ├── pdfs/           # Original PDFs
│   ├── processed/      # Extracted text/images
│   ├── questions/      # Generated questions
│   └── audio/          # Pre-generated TTS audio
├── models/
│   ├── llm/           # Quantized LLMs
│   ├── whisper/       # Speech models
│   ├── embeddings/    # Embedding models
│   └── tts/           # TTS models
└── user_data/
    ├── profiles/      # User profiles
    ├── progress/      # Learning progress
    └── recordings/    # Voice recordings
```

## UI Architecture

### Component Structure
```
src/ui/
├── web/
│   ├── components/
│   │   ├── common/        # Shared components
│   │   ├── learning/      # Quiz, lessons, etc.
│   │   ├── dashboard/     # Progress views
│   │   └── voice/         # Voice interaction UI
│   ├── hooks/            # Custom React hooks
│   ├── services/         # API clients
│   ├── store/           # State management
│   └── styles/          # Global styles
└── touch/
    └── electron/        # Electron wrapper for kiosk mode
```

### Real-time Updates
```typescript
// WebSocket connection for real-time updates
class RealtimeService {
    constructor() {
        this.socket = io('ws://localhost:8000', {
            transports: ['websocket'],
            reconnection: true
        });
    }
    
    subscribeToVoiceEvents() {
        this.socket.on('voice:listening', this.handleListening);
        this.socket.on('voice:processing', this.handleProcessing);
        this.socket.on('voice:response', this.handleResponse);
    }
    
    subscribeToLearningEvents() {
        this.socket.on('question:new', this.handleNewQuestion);
        this.socket.on('answer:feedback', this.handleFeedback);
        this.socket.on('progress:update', this.handleProgress);
    }
}
```

### Touch Optimization
```typescript
// Touch-optimized components
const TouchButton = styled.button`
    min-height: 48px;  // Minimum touch target
    min-width: 48px;
    padding: 12px 24px;
    
    @media (hover: none) {
        // Remove hover effects on touch devices
        &:hover {
            background: inherit;
        }
    }
`;

// Gesture handling
const useGestures = () => {
    const handlers = useSwipeable({
        onSwipedLeft: () => navigateNext(),
        onSwipedRight: () => navigatePrevious(),
        preventDefaultTouchmoveEvent: true,
        trackMouse: true
    });
    
    return handlers;
};
```

## Deployment Architecture

### Service Configuration
```yaml
# docker-compose.yml for local development
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: isee_tutor
      POSTGRES_USER: tutor
      POSTGRES_PASSWORD: secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data

  chromadb:
    image: chromadb/chroma:latest
    volumes:
      - chroma_data:/chroma/chroma

  minio:
    image: minio/minio:latest
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    volumes:
      - minio_data:/data

  api:
    build: .
    depends_on:
      - postgres
      - redis
      - chromadb
      - minio
    volumes:
      - ./src:/app/src
      - /dev/bus/usb:/dev/bus/usb  # USB devices
      - /dev/snd:/dev/snd          # Audio devices
    devices:
      - /dev/snd
    privileged: true  # For GPIO access

volumes:
  postgres_data:
  redis_data:
  chroma_data:
  minio_data:
```

### Process Management
```ini
# supervisord.conf
[program:api]
command=/home/tutor/iseetutor/venv/bin/python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000
directory=/home/tutor/iseetutor
autostart=true
autorestart=true
stderr_logfile=/var/log/iseetutor/api.err.log
stdout_logfile=/var/log/iseetutor/api.out.log

[program:celery]
command=/home/tutor/iseetutor/venv/bin/celery -A src.tasks worker --loglevel=info
directory=/home/tutor/iseetutor
autostart=true
autorestart=true

[program:ui]
command=/usr/bin/npm start
directory=/home/tutor/iseetutor/web
autostart=true
autorestart=true
```

## Security Considerations

### Data Protection
- All user data encrypted at rest (LUKS for SSD)
- TLS for all network communication
- JWT tokens for session management
- Role-based access control (student/parent/admin)

### Privacy
- No data leaves the device without explicit consent
- Voice recordings deleted after processing
- Parental controls for content access
- COPPA compliance for child users

## Performance Optimization

### Jetson-Specific Optimizations
- Use TensorRT for model optimization
- Enable GPU acceleration for all ML models
- Use NVIDIA's optimized libraries (cuDNN, NCCL)
- Memory-mapped model loading

### Caching Strategy
- Redis for session data (TTL: 24 hours)
- Pre-computed embeddings for common content
- TTS audio caching for frequent phrases
- Browser caching for static assets

## Monitoring and Logging

### Metrics Collection
```python
# Prometheus metrics
from prometheus_client import Counter, Histogram, Gauge

# Track key metrics
voice_interactions = Counter('voice_interactions_total', 
                           'Total voice interactions')
response_time = Histogram('response_time_seconds', 
                         'Response time distribution')
active_sessions = Gauge('active_sessions', 
                       'Number of active sessions')
```

### Logging Strategy
- Structured logging with JSON format
- Log aggregation with Loki or ELK
- Error tracking with Sentry
- Performance monitoring with Grafana

## Next Steps

1. Set up development environment with Docker
2. Implement core audio pipeline
3. Integrate Whisper for speech recognition
4. Set up FastAPI backend structure
5. Create React frontend scaffold
6. Implement PDF processing pipeline
7. Set up vector database for RAG
8. Integrate local LLM with LangChain
9. Build adaptive learning algorithms
10. Create parent dashboard

This architecture provides a solid foundation that can scale with the project's needs while maintaining good performance on the Jetson hardware.