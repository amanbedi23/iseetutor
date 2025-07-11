# ISEE Tutor Deployment Strategy

## Overview

The ISEE Tutor is designed as an **edge-first** system - the device operates independently without requiring cloud services for core functionality. However, optional cloud services can enhance certain features.

## Development vs Production Architecture

### Development (Current - Local on Jetson)
All services run locally on the Jetson device:
```
Jetson Orin Nano (Development)
├── /home/tutor/iseetutor/     # Main codebase on SD card
├── /mnt/storage/ (1TB SSD)     # Large files and models
│   ├── models/                 # AI models (30-50GB)
│   ├── content/                # Educational PDFs and materials
│   └── user_data/              # User progress and recordings
└── Local Services:
    ├── PostgreSQL              # Running locally
    ├── Redis                   # Running locally
    ├── ChromaDB                # Running locally
    └── MinIO                   # Running locally
```

### Production (Edge Device with Optional Cloud)

```
┌─────────────────────────────────────────────────────────────────┐
│                        Edge Device (Jetson)                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Core Services (Always Local):                                   │
│  ├── LLM (Llama 3.2)         # Privacy-first, no cloud needed  │
│  ├── Speech Recognition      # Real-time, low latency          │
│  ├── TTS                     # Immediate responses             │
│  ├── Educational Engine      # Offline learning                │
│  ├── PostgreSQL (SQLite alt) # Local user data                │
│  ├── ChromaDB               # Local vector store               │
│  └── MinIO/Local FS         # Local content storage           │
│                                                                  │
└─────────────────────────────────────┬───────────────────────────┘
                                      │ Optional
                    ┌─────────────────▼───────────────────┐
                    │        Cloud Services (Optional)     │
                    ├──────────────────────────────────────┤
                    │  ├── Content CDN                     │
                    │  ├── Backup & Sync                   │
                    │  ├── Analytics & Telemetry           │
                    │  ├── Parent Dashboard Access         │
                    │  └── Content Marketplace              │
                    └──────────────────────────────────────┘
```

## Storage Strategy with 1TB SSD

### Optimal Storage Layout
```bash
# SD Card (256GB) - OS and frequently accessed files
/home/tutor/iseetutor/
├── src/                    # Application code
├── web/                    # Frontend code
├── config/                 # Configuration
└── logs/                   # Application logs

# SSD (1TB) - Large files and databases
/mnt/storage/
├── models/                 # 30-50GB
│   ├── llama-3.2-3b-q4/   # Quantized LLM (~2-4GB)
│   ├── whisper-base/       # Speech recognition (~150MB)
│   ├── piper-tts/          # Text-to-speech (~100MB)
│   └── embeddings/         # BGE models (~200MB)
├── databases/              # 10-50GB
│   ├── postgresql/         # Main database
│   ├── chromadb/           # Vector embeddings
│   └── redis/              # Cache persistence
├── content/                # 100-500GB
│   ├── pdfs/              # Original educational PDFs
│   ├── processed/         # Extracted and indexed content
│   ├── questions/         # Generated question banks
│   ├── audio_cache/       # Pre-generated TTS audio
│   └── images/            # Extracted images from PDFs
└── user_data/              # 50-100GB
    ├── profiles/           # User learning profiles
    ├── progress/           # Detailed progress tracking
    ├── recordings/         # Voice recordings (temp)
    └── backups/           # Local backups
```

### Mount Configuration
```bash
# /etc/fstab entry for SSD
UUID=your-ssd-uuid /mnt/storage ext4 defaults,noatime 0 2

# Create symbolic links for better performance
ln -s /mnt/storage/databases/postgresql /var/lib/postgresql/data
ln -s /mnt/storage/databases/redis /var/lib/redis
ln -s /mnt/storage/models /home/tutor/iseetutor/models
```

## Why Edge-First?

### 1. **Privacy & Security**
- Children's data never leaves the device
- COPPA compliance by design
- No internet required for learning

### 2. **Performance**
- Zero-latency LLM responses
- Real-time voice processing
- No network dependencies

### 3. **Reliability**
- Works anywhere, anytime
- No subscription required
- No service interruptions

### 4. **Cost Efficiency**
- No cloud API costs
- No bandwidth costs
- One-time purchase model

## Optional Cloud Services

### 1. **Content Delivery Network (CDN)**
```python
# Optional content sync service
class ContentSync:
    """Sync educational content from cloud when available"""
    
    def __init__(self):
        self.cdn_url = "https://content.iseetutor.com"
        self.local_path = "/mnt/storage/content"
    
    async def sync_content(self):
        """Download new content when connected"""
        if self.is_online():
            new_content = await self.check_updates()
            await self.download_content(new_content)
```

### 2. **Backup & Sync Service**
```python
# Optional progress backup
class ProgressBackup:
    """Backup learning progress to parent's account"""
    
    def __init__(self):
        self.sync_enabled = False  # Opt-in only
    
    async def backup_progress(self, user_id: str):
        """Encrypted backup to cloud"""
        if self.sync_enabled and self.is_online():
            encrypted_data = self.encrypt_user_data(user_id)
            await self.upload_to_cloud(encrypted_data)
```

### 3. **Parent Dashboard (Web Access)**
```nginx
# Remote access to parent dashboard
server {
    listen 443 ssl;
    server_name parent.iseetutor.local;
    
    # Local network only by default
    allow 192.168.0.0/16;
    deny all;
    
    location / {
        proxy_pass http://localhost:3000/parent;
    }
}
```

### 4. **Analytics Service (Opt-in)**
```python
# Anonymous usage analytics
class Analytics:
    """Collect anonymous usage data for improvements"""
    
    def __init__(self):
        self.enabled = False  # Opt-in only
        self.endpoint = "https://analytics.iseetutor.com"
    
    async def log_event(self, event_type: str, metadata: dict):
        """Log anonymous events"""
        if self.enabled and self.is_online():
            # Strip all PII
            anonymous_event = self.anonymize(event_type, metadata)
            await self.send_event(anonymous_event)
```

## Development to Production Transition

### Phase 1: Local Development (Current)
```bash
# Everything runs locally on Jetson
docker-compose up -d  # PostgreSQL, Redis, MinIO, ChromaDB
npm run dev          # Frontend development server
uvicorn src.api.main:app --reload  # Backend API
```

### Phase 2: Production on Device
```bash
# Optimize for production
# Use SQLite instead of PostgreSQL for simplicity
# Use local filesystem instead of MinIO
# Run ChromaDB in persistent mode
# Use supervisor for process management
```

### Phase 3: Optional Cloud Enhancement
```yaml
# Optional cloud services configuration
cloud:
  enabled: false  # Disabled by default
  services:
    content_cdn:
      enabled: true
      url: "https://cdn.iseetutor.com"
      sync_interval: "daily"
    
    backup:
      enabled: false  # Opt-in
      encryption: "aes-256"
      endpoint: "https://backup.iseetutor.com"
    
    analytics:
      enabled: false  # Opt-in
      anonymous: true
      endpoint: "https://analytics.iseetutor.com"
```

## Database Considerations

### Development (PostgreSQL)
- Full-featured for complex queries
- Better for multi-user testing
- Easier debugging with tools

### Production (SQLite)
- Simpler deployment
- No daemon required
- Sufficient for single-device use
- Backup is just file copy

### Migration Path
```python
# Easy migration between databases
DATABASES = {
    'development': {
        'engine': 'postgresql',
        'host': 'localhost',
        'name': 'isee_tutor'
    },
    'production': {
        'engine': 'sqlite',
        'path': '/mnt/storage/databases/isee_tutor.db'
    }
}
```

## Model Deployment Strategy

### Model Optimization for Edge
```python
# Model quantization for Jetson
def prepare_models_for_edge():
    """Optimize models for edge deployment"""
    
    # Quantize Llama 3.2 to 4-bit
    quantize_model(
        input="llama-3.2-3b",
        output="/mnt/storage/models/llama-3.2-3b-q4",
        quantization="q4_k_m"
    )
    
    # Convert Whisper to ONNX for TensorRT
    convert_to_onnx(
        model="whisper-base",
        output="/mnt/storage/models/whisper-base-onnx"
    )
    
    # Optimize embeddings model
    optimize_embeddings(
        model="BAAI/bge-small-en-v1.5",
        output="/mnt/storage/models/bge-small-optimized"
    )
```

## Security Model

### Edge Security
- Disk encryption (LUKS) for SSD
- User data encrypted at rest
- No external connections required
- Local firewall rules

### Optional Cloud Security
- TLS 1.3 for all connections
- Certificate pinning
- OAuth2 for parent accounts
- End-to-end encryption for backups

## Cost Analysis

### Edge-Only Deployment
- **One-time cost**: Hardware only
- **Recurring cost**: $0
- **Privacy**: 100% local
- **Reliability**: No dependencies

### With Optional Cloud
- **CDN**: ~$10/month (optional)
- **Backup**: ~$5/month (optional)
- **Analytics**: Free tier
- **Total**: $0-15/month (all optional)

## Summary

The ISEE Tutor is designed to be a **fully functional edge device** that requires no cloud services. All AI processing, content storage, and user data remain on the device. Cloud services are purely optional enhancements for:

1. Content updates (new educational materials)
2. Parent access from other devices
3. Backup redundancy
4. Anonymous analytics for improvement

This approach ensures:
- Maximum privacy for children
- No recurring costs
- Complete offline functionality
- Optional cloud benefits when desired

For development, everything runs locally on your Jetson with the 1TB SSD providing ample storage for all models, content, and databases.