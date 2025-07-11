# ISEE Tutor Implementation Guide

## Quick Framework Decisions

### Core Stack
- **Backend**: FastAPI + Celery + Redis
- **Frontend**: React + TypeScript + Material-UI
- **AI/ML**: LangChain + Llama 3.2 + Whisper + ChromaDB
- **Database**: PostgreSQL + Redis + MinIO
- **Audio**: PyAudio + WebRTC VAD + Porcupine
- **Deployment**: Docker + Supervisor + Nginx

## Phase 1: Foundation Setup (Current Phase)

### 1.1 Development Environment
```bash
# Install system dependencies
sudo apt update
sudo apt install -y \
    python3.10-dev python3.10-venv \
    postgresql postgresql-contrib \
    redis-server \
    portaudio19-dev \
    tesseract-ocr \
    ffmpeg \
    nodejs npm \
    docker.io docker-compose

# Python environment
cd /home/tutor/iseetutor
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip wheel setuptools

# Core Python packages
pip install \
    fastapi uvicorn[standard] \
    celery[redis] \
    sqlalchemy alembic psycopg2-binary \
    langchain chromadb \
    openai-whisper faster-whisper \
    torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118 \
    transformers accelerate \
    pydantic python-multipart \
    redis hiredis \
    minio \
    pandas numpy scipy \
    pytesseract pdf2image PyPDF2 \
    python-dotenv click \
    pytest pytest-asyncio pytest-cov
```

### 1.2 Project Structure Setup
```bash
# Create comprehensive directory structure
mkdir -p src/{api,core,education,ui,tasks,models,utils}
mkdir -p src/api/{routes,models,schemas,services,middleware}
mkdir -p src/core/{audio,speech,nlp,hardware}
mkdir -p src/education/{content,quiz,progress,adaptive}
mkdir -p src/models/{llm,embeddings,tts,stt}
mkdir -p web/{src,public,build}
mkdir -p web/src/{components,hooks,services,store,styles,types}
mkdir -p tests/{unit,integration,e2e}
mkdir -p scripts/{setup,maintenance,deployment}
mkdir -p docs/{api,user,developer}
mkdir -p config/{development,production,test}

# Storage directories
sudo mkdir -p /mnt/storage/{content,models,user_data}
sudo chown -R $USER:$USER /mnt/storage
```

### 1.3 Database Setup
```sql
-- Create database schema
CREATE DATABASE isee_tutor;

-- User profiles and authentication
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL,
    user_type VARCHAR(20) NOT NULL CHECK (user_type IN ('student', 'parent', 'admin')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Student profiles
CREATE TABLE student_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    age INTEGER,
    grade_level INTEGER,
    target_test_date DATE,
    learning_style VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Learning sessions
CREATE TABLE learning_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID REFERENCES student_profiles(id),
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP,
    mode VARCHAR(20) CHECK (mode IN ('tutorial', 'practice', 'test', 'review')),
    subject VARCHAR(50),
    metadata JSONB
);

-- Content library
CREATE TABLE content_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    content_type VARCHAR(50) NOT NULL,
    subject VARCHAR(50) NOT NULL,
    grade_level INTEGER NOT NULL,
    difficulty_level INTEGER CHECK (difficulty_level BETWEEN 1 AND 10),
    source_file VARCHAR(255),
    content_text TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Quiz questions
CREATE TABLE questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content_id UUID REFERENCES content_items(id),
    question_type VARCHAR(50) NOT NULL,
    question_text TEXT NOT NULL,
    options JSONB,
    correct_answer TEXT NOT NULL,
    explanation TEXT,
    difficulty_level INTEGER CHECK (difficulty_level BETWEEN 1 AND 10),
    metadata JSONB
);

-- Student progress
CREATE TABLE student_progress (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID REFERENCES student_profiles(id),
    question_id UUID REFERENCES questions(id),
    session_id UUID REFERENCES learning_sessions(id),
    answered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    student_answer TEXT,
    is_correct BOOLEAN,
    time_taken INTEGER, -- seconds
    hints_used INTEGER DEFAULT 0
);

-- Create indexes for performance
CREATE INDEX idx_student_progress_student ON student_progress(student_id);
CREATE INDEX idx_student_progress_session ON student_progress(session_id);
CREATE INDEX idx_questions_subject ON questions(question_type, difficulty_level);
CREATE INDEX idx_content_subject_grade ON content_items(subject, grade_level);
```

## Phase 2: Core Services Implementation

### 2.1 FastAPI Application Structure
```python
# src/api/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

from .routes import auth, content, quiz, progress, voice
from .middleware import TimingMiddleware, ErrorHandlerMiddleware
from ..core import AudioManager, SpeechRecognition, Hardware
from ..models import load_models

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await load_models()
    AudioManager.initialize()
    Hardware.initialize()
    yield
    # Shutdown
    AudioManager.cleanup()
    Hardware.cleanup()

app = FastAPI(
    title="ISEE Tutor API",
    version="1.0.0",
    lifespan=lifespan
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(TimingMiddleware)
app.add_middleware(ErrorHandlerMiddleware)

# Routes
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(content.router, prefix="/api/content", tags=["content"])
app.include_router(quiz.router, prefix="/api/quiz", tags=["quiz"])
app.include_router(progress.router, prefix="/api/progress", tags=["progress"])
app.include_router(voice.router, prefix="/api/voice", tags=["voice"])

# WebSocket for real-time updates
from .websocket import ws_router
app.include_router(ws_router, prefix="/ws")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### 2.2 Audio Pipeline Implementation
```python
# src/core/audio/pipeline.py
import asyncio
import numpy as np
from typing import Optional, Callable
import pyaudio
import webrtcvad
from collections import deque

class AudioPipeline:
    def __init__(
        self,
        sample_rate: int = 16000,
        chunk_duration_ms: int = 30,
        vad_mode: int = 3  # 0-3, 3 is most aggressive
    ):
        self.sample_rate = sample_rate
        self.chunk_size = int(sample_rate * chunk_duration_ms / 1000)
        self.vad = webrtcvad.Vad(vad_mode)
        
        # Audio setup
        self.pa = pyaudio.PyAudio()
        self.stream = None
        
        # Buffers
        self.audio_buffer = deque(maxlen=100)  # ~3 seconds
        self.voice_buffer = []
        
        # State
        self.is_recording = False
        self.voice_detected = False
        self.callbacks = {}
        
    def start_listening(self):
        """Start continuous audio capture"""
        self.stream = self.pa.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=self.chunk_size,
            stream_callback=self._audio_callback
        )
        self.stream.start_stream()
        self.is_recording = True
        
    def _audio_callback(self, in_data, frame_count, time_info, status):
        """Process audio chunks in real-time"""
        audio_chunk = np.frombuffer(in_data, dtype=np.int16)
        
        # Add to circular buffer
        self.audio_buffer.append(audio_chunk)
        
        # Voice Activity Detection
        is_speech = self.vad.is_speech(in_data, self.sample_rate)
        
        if is_speech:
            if not self.voice_detected:
                self.voice_detected = True
                self._trigger_callback('voice_start')
                # Include pre-buffer for context
                self.voice_buffer = list(self.audio_buffer)[-10:]
            self.voice_buffer.append(audio_chunk)
        else:
            if self.voice_detected:
                # Add post-buffer
                self.voice_buffer.extend(list(self.audio_buffer)[:5])
                self.voice_detected = False
                self._trigger_callback('voice_end', 
                    np.concatenate(self.voice_buffer))
                self.voice_buffer = []
                
        return (in_data, pyaudio.paContinue)
    
    def register_callback(self, event: str, callback: Callable):
        """Register event callbacks"""
        self.callbacks[event] = callback
        
    def _trigger_callback(self, event: str, data=None):
        """Trigger registered callbacks"""
        if event in self.callbacks:
            asyncio.create_task(self.callbacks[event](data))
```

### 2.3 Speech Recognition Service
```python
# src/core/speech/recognition.py
import whisper
import faster_whisper
import numpy as np
from typing import Optional, Dict
import torch

class SpeechRecognition:
    def __init__(self, model_size: str = "base", device: str = "cuda"):
        self.device = device
        
        # Use faster-whisper for better performance on Jetson
        self.model = faster_whisper.WhisperModel(
            model_size,
            device=device,
            compute_type="int8_float16" if device == "cuda" else "int8"
        )
        
        # Wake word detection
        self.wake_word = "hey tutor"
        self.wake_word_threshold = 0.7
        
    async def transcribe(
        self, 
        audio: np.ndarray, 
        language: str = "en"
    ) -> Dict:
        """Transcribe audio to text"""
        # Normalize audio
        audio = audio.astype(np.float32) / 32768.0
        
        # Transcribe
        segments, info = self.model.transcribe(
            audio,
            language=language,
            beam_size=5,
            vad_filter=True,
            vad_parameters=dict(
                min_silence_duration_ms=500
            )
        )
        
        # Collect results
        text = " ".join([s.text for s in segments])
        
        return {
            "text": text.strip(),
            "language": info.language,
            "confidence": info.language_probability
        }
    
    def detect_wake_word(self, audio: np.ndarray) -> bool:
        """Check if audio contains wake word"""
        result = self.transcribe(audio)
        text = result['text'].lower()
        
        # Simple check - can be enhanced with phonetic matching
        return self.wake_word in text
```

### 2.4 LLM Integration with RAG
```python
# src/models/llm/tutor_llm.py
from langchain.llms import LlamaCpp
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferWindowMemory
from langchain.prompts import PromptTemplate

class TutorLLM:
    def __init__(self, model_path: str, vector_store_path: str):
        # Initialize quantized Llama model
        self.llm = LlamaCpp(
            model_path=model_path,
            n_gpu_layers=32,  # Offload to GPU
            n_ctx=2048,
            n_batch=256,
            temperature=0.7,
            max_tokens=512,
            verbose=False
        )
        
        # Initialize embeddings
        self.embeddings = HuggingFaceEmbeddings(
            model_name="BAAI/bge-small-en-v1.5",
            model_kwargs={'device': 'cuda'},
            encode_kwargs={'normalize_embeddings': True}
        )
        
        # Load vector store
        self.vector_store = Chroma(
            persist_directory=vector_store_path,
            embedding_function=self.embeddings
        )
        
        # Setup memory
        self.memory = ConversationBufferWindowMemory(
            memory_key="chat_history",
            k=5,  # Keep last 5 exchanges
            return_messages=True
        )
        
        # Create retrieval chain
        self.qa_chain = self._create_qa_chain()
        
    def _create_qa_chain(self):
        """Create the conversational retrieval chain"""
        
        # Custom prompt for tutoring
        template = """You are an expert ISEE tutor helping a student prepare for their test. 
        Use the following context to answer the question. If you don't know the answer, 
        say so and offer to explain a related concept.
        
        Context: {context}
        
        Student: {question}
        Tutor: Let me help you with that."""
        
        prompt = PromptTemplate(
            template=template,
            input_variables=["context", "question"]
        )
        
        return ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=self.vector_store.as_retriever(
                search_kwargs={"k": 3}
            ),
            memory=self.memory,
            combine_docs_chain_kwargs={"prompt": prompt},
            verbose=False
        )
    
    async def get_response(
        self, 
        question: str, 
        subject: Optional[str] = None,
        grade_level: Optional[int] = None
    ) -> str:
        """Get tutoring response with context"""
        
        # Add metadata filters if provided
        if subject or grade_level:
            # Update retriever with filters
            search_kwargs = {"k": 3}
            if subject:
                search_kwargs["filter"] = {"subject": subject}
            
            self.qa_chain.retriever.search_kwargs = search_kwargs
        
        # Get response
        result = await self.qa_chain.acall({"question": question})
        
        return result["answer"]
```

### 2.5 Content Processing Service
```python
# src/education/content/processor.py
import asyncio
from pathlib import Path
from typing import List, Dict
import PyPDF2
import pytesseract
from pdf2image import convert_from_path
import numpy as np
from langchain.text_splitter import RecursiveCharacterTextSplitter
from ..models import embeddings, vector_store

class ContentProcessor:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", ".", "!", "?", " ", ""]
        )
        
    async def process_pdf(self, pdf_path: Path) -> Dict:
        """Process PDF and extract content"""
        
        # Extract text
        text_content = self._extract_text_from_pdf(pdf_path)
        
        # If text extraction fails, try OCR
        if len(text_content.strip()) < 100:
            text_content = await self._ocr_pdf(pdf_path)
        
        # Extract metadata
        metadata = self._extract_metadata(text_content)
        
        # Split into chunks
        chunks = self.text_splitter.split_text(text_content)
        
        # Generate embeddings
        embeddings = await self._generate_embeddings(chunks)
        
        # Store in vector database
        doc_ids = await self._store_content(
            chunks, embeddings, metadata, pdf_path.name
        )
        
        # Generate questions
        questions = await self._generate_questions(chunks, metadata)
        
        return {
            "file": pdf_path.name,
            "chunks": len(chunks),
            "metadata": metadata,
            "questions_generated": len(questions),
            "doc_ids": doc_ids
        }
    
    def _extract_text_from_pdf(self, pdf_path: Path) -> str:
        """Extract text using PyPDF2"""
        text = ""
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        return text
    
    async def _ocr_pdf(self, pdf_path: Path) -> str:
        """OCR PDF pages"""
        images = convert_from_path(pdf_path)
        text = ""
        
        for i, image in enumerate(images):
            # Convert to numpy array
            img_array = np.array(image)
            
            # OCR with Tesseract
            page_text = pytesseract.image_to_string(
                img_array,
                config='--psm 3'  # Fully automatic page segmentation
            )
            text += f"\n--- Page {i+1} ---\n{page_text}"
            
        return text
    
    def _extract_metadata(self, text: str) -> Dict:
        """Extract metadata from content"""
        # Use LLM to extract metadata
        metadata_prompt = """
        Extract the following from this educational content:
        - Subject (math, verbal, reading, etc.)
        - Grade level (elementary, middle, high)
        - Topics covered
        - Difficulty level (1-10)
        
        Content: {text[:1000]}
        """
        
        # This would call the LLM to extract metadata
        # For now, return placeholder
        return {
            "subject": "mathematics",
            "grade_level": 7,
            "topics": ["algebra", "geometry"],
            "difficulty": 5
        }
    
    async def _generate_questions(
        self, 
        chunks: List[str], 
        metadata: Dict
    ) -> List[Dict]:
        """Generate practice questions from content"""
        questions = []
        
        for chunk in chunks[:10]:  # Limit for demo
            question_prompt = f"""
            Generate 2 ISEE-style questions based on this content:
            {chunk}
            
            Format each question as:
            Question: [question text]
            A) [option]
            B) [option]
            C) [option]
            D) [option]
            Answer: [correct letter]
            Explanation: [why this answer is correct]
            """
            
            # This would call LLM to generate questions
            # Store in database
            
        return questions
```

### 2.6 React Frontend Structure
```typescript
// web/src/App.tsx
import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';

import { AuthProvider } from './contexts/AuthContext';
import { VoiceProvider } from './contexts/VoiceContext';
import { WebSocketProvider } from './contexts/WebSocketContext';

import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Learning from './pages/Learning';
import Progress from './pages/Progress';
import Settings from './pages/Settings';

import theme from './styles/theme';

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AuthProvider>
        <WebSocketProvider>
          <VoiceProvider>
            <Router>
              <Layout>
                <Routes>
                  <Route path="/" element={<Dashboard />} />
                  <Route path="/learn/:subject" element={<Learning />} />
                  <Route path="/progress" element={<Progress />} />
                  <Route path="/settings" element={<Settings />} />
                </Routes>
              </Layout>
            </Router>
          </VoiceProvider>
        </WebSocketProvider>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;
```

```typescript
// web/src/components/VoiceInterface.tsx
import React, { useState, useEffect } from 'react';
import { Box, IconButton, Typography, CircularProgress } from '@mui/material';
import { Mic, MicOff } from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';
import { useVoice } from '../contexts/VoiceContext';

const VoiceInterface: React.FC = () => {
  const { isListening, transcript, response, startListening, stopListening } = useVoice();
  const [showWaveform, setShowWaveform] = useState(false);

  useEffect(() => {
    setShowWaveform(isListening);
  }, [isListening]);

  return (
    <Box
      sx={{
        position: 'fixed',
        bottom: 20,
        right: 20,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: 2,
      }}
    >
      <AnimatePresence>
        {showWaveform && (
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.8 }}
          >
            <Box
              sx={{
                width: 200,
                height: 60,
                bgcolor: 'background.paper',
                borderRadius: 2,
                p: 2,
                boxShadow: 3,
              }}
            >
              {/* Waveform visualization would go here */}
              <Typography variant="caption">
                {transcript || "Listening..."}
              </Typography>
            </Box>
          </motion.div>
        )}
      </AnimatePresence>

      <IconButton
        onClick={isListening ? stopListening : startListening}
        sx={{
          width: 64,
          height: 64,
          bgcolor: isListening ? 'error.main' : 'primary.main',
          color: 'white',
          '&:hover': {
            bgcolor: isListening ? 'error.dark' : 'primary.dark',
          },
        }}
      >
        {isListening ? <MicOff /> : <Mic />}
      </IconButton>
    </Box>
  );
};

export default VoiceInterface;
```

## Phase 3: Hardware Integration

### 3.1 LED Ring Controller
```python
# src/core/hardware/led_controller.py
import time
import threading
from typing import Tuple, List
import board
import neopixel

class LEDController:
    def __init__(self, pin=board.D18, num_leds=16):
        self.pixels = neopixel.NeoPixel(
            pin, num_leds, brightness=0.3, auto_write=False
        )
        self.num_leds = num_leds
        self.animation_thread = None
        self.stop_animation = False
        
    def set_color(self, color: Tuple[int, int, int]):
        """Set all LEDs to a single color"""
        self.pixels.fill(color)
        self.pixels.show()
        
    def listening_animation(self):
        """Breathing blue animation for listening state"""
        self.stop_animation = False
        
        def animate():
            while not self.stop_animation:
                # Breathing effect
                for brightness in range(0, 100, 2):
                    if self.stop_animation:
                        break
                    b = int(brightness * 2.55)
                    self.pixels.fill((0, 0, b))
                    self.pixels.show()
                    time.sleep(0.02)
                    
                for brightness in range(100, 0, -2):
                    if self.stop_animation:
                        break
                    b = int(brightness * 2.55)
                    self.pixels.fill((0, 0, b))
                    self.pixels.show()
                    time.sleep(0.02)
        
        self.animation_thread = threading.Thread(target=animate)
        self.animation_thread.start()
        
    def thinking_animation(self):
        """Spinning animation for processing"""
        self.stop_animation = False
        
        def animate():
            position = 0
            while not self.stop_animation:
                self.pixels.fill((0, 0, 0))
                # Create comet effect
                for i in range(5):
                    pos = (position - i) % self.num_leds
                    brightness = 255 - (i * 50)
                    self.pixels[pos] = (brightness, brightness, 0)
                self.pixels.show()
                position = (position + 1) % self.num_leds
                time.sleep(0.05)
        
        self.animation_thread = threading.Thread(target=animate)
        self.animation_thread.start()
        
    def success_animation(self):
        """Green pulse for correct answers"""
        for _ in range(3):
            self.pixels.fill((0, 255, 0))
            self.pixels.show()
            time.sleep(0.2)
            self.pixels.fill((0, 0, 0))
            self.pixels.show()
            time.sleep(0.2)
            
    def stop(self):
        """Stop current animation"""
        self.stop_animation = True
        if self.animation_thread:
            self.animation_thread.join()
        self.pixels.fill((0, 0, 0))
        self.pixels.show()
```

### 3.2 Button Handler
```python
# src/core/hardware/button.py
import Jetson.GPIO as GPIO
import asyncio
from typing import Callable

class ButtonHandler:
    def __init__(self, pin: int = 18):
        self.pin = pin
        self.callbacks = []
        
        # Setup GPIO
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(
            self.pin, 
            GPIO.FALLING, 
            callback=self._button_callback,
            bouncetime=300
        )
        
    def _button_callback(self, channel):
        """Handle button press"""
        for callback in self.callbacks:
            asyncio.create_task(callback())
            
    def on_press(self, callback: Callable):
        """Register button press callback"""
        self.callbacks.append(callback)
        
    def cleanup(self):
        """Cleanup GPIO"""
        GPIO.cleanup()
```

## Phase 4: Deployment Configuration

### 4.1 Docker Setup
```dockerfile
# Dockerfile
FROM nvcr.io/nvidia/l4t-pytorch:r35.2.1-pth2.0-py3

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3-dev \
    portaudio19-dev \
    tesseract-ocr \
    ffmpeg \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose ports
EXPOSE 8000 3000

# Start services
CMD ["supervisord", "-c", "/app/config/supervisord.conf"]
```

### 4.2 Nginx Configuration
```nginx
# /etc/nginx/sites-available/iseetutor
server {
    listen 80;
    server_name localhost;

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Host $host;
    }

    # WebSocket
    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## Next Implementation Steps

1. **Immediate** (Today):
   - Install Python dependencies
   - Set up PostgreSQL database
   - Create basic FastAPI structure
   - Test audio recording

2. **Week 1**:
   - Implement audio pipeline
   - Integrate Whisper for speech recognition
   - Set up React frontend scaffold
   - Create WebSocket communication

3. **Week 2**:
   - Download and quantize Llama 3.2 model
   - Set up ChromaDB vector store
   - Implement PDF processing pipeline
   - Create basic quiz generation

4. **Week 3**:
   - Build learning UI components
   - Implement progress tracking
   - Add LED and button integration
   - Create parent dashboard

5. **Week 4**:
   - Testing and optimization
   - Performance tuning for Jetson
   - Documentation
   - Deployment setup

This implementation guide provides a concrete roadmap with actual code examples and configurations to get started immediately.