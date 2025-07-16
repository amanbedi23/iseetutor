# Technical Requirements for ISEE Tutor Implementation

## 1. Voice Pipeline Requirements

### 1.1 Wake Word Detection
**Requirement ID**: VR-001
- **Implementation**: OpenWakeWord with custom "Hey Tutor" model
- **Accuracy Target**: > 95% detection, < 1% false positive
- **Latency**: < 300ms to activation
- **Files**: 
  - `src/core/audio/openwakeword_detector.py`
  - Model file: `data/models/wake_word/hey_tutor.tflite`

### 1.2 Speech-to-Text (STT)
**Requirement ID**: VR-002
- **Implementation**: Whisper base model
- **Languages**: English (US/UK)
- **Accuracy Target**: > 90% for children's speech
- **Processing**: Real-time streaming
- **Files**: 
  - `src/core/audio/audio_processor.py`
  - `src/core/tasks/audio_tasks.py`

### 1.3 Text-to-Speech (TTS)
**Requirement ID**: VR-003
- **Implementation**: Piper TTS (local, fast)
- **Voice Requirements**:
  - Child-friendly tone
  - Adjustable speed (0.8x - 1.2x)
  - Clear pronunciation
  - Expressive for engagement
- **Files to implement**:
  - `src/core/audio/tts_engine.py`
  - Update `src/core/tasks/audio_tasks.py`

### 1.4 Voice Activity Detection (VAD)
**Requirement ID**: VR-004
- **Current**: WebRTC VAD implemented
- **Requirements**:
  - Detect speech end for processing
  - Handle background noise
  - Support barge-in interruption

## 2. AI/LLM Integration Requirements

### 2.1 Language Model Integration
**Requirement ID**: AI-001
- **Model**: Llama 3.1 8B (quantized Q4_K_M)
- **Context Window**: 8192 tokens
- **System Prompts**:
  - Tutor mode: Educational, encouraging, ISEE-focused
  - Friend mode: Fun, engaging, age-appropriate
- **Files to update**:
  - `src/models/companion_llm.py` - Replace stub with real integration
  - `src/api/routes/companion.py` - Connect to LLM not SQLite

### 2.2 Response Generation
**Requirement ID**: AI-002
- **Requirements**:
  - Context-aware (remember conversation)
  - Mode-specific personality
  - Safety filters for children
  - Educational value emphasis
- **Response Time**: < 2 seconds
- **Token Limits**: 
  - Tutor mode: 150-200 tokens
  - Friend mode: 100-150 tokens

### 2.3 Content Understanding
**Requirement ID**: AI-003
- **RAG Integration**: ChromaDB with educational content
- **Embedding Model**: all-MiniLM-L6-v2
- **Requirements**:
  - Search relevant educational content
  - Cite sources when teaching
  - Fact-check responses

## 3. Educational Content Requirements

### 3.1 ISEE Content Structure
**Requirement ID**: ED-001
- **Database Schema**:
  ```sql
  questions (
    id, subject, topic, difficulty, 
    question_text, options, correct_answer,
    explanation, grade_level, question_type
  )
  ```
- **Content Categories**:
  - Verbal: synonyms, analogies, sentence_completion
  - Quantitative: arithmetic, algebra, geometry, data
  - Reading: passages with comprehension questions
  - Math Achievement: grade-aligned problems

### 3.2 Quiz Generation
**Requirement ID**: ED-002
- **Adaptive Algorithm**:
  - Start at grade level
  - Adjust ±1 difficulty per 3 questions
  - Mix topics based on weaknesses
- **Quiz Formats**:
  - Quick practice: 5 questions
  - Topic focus: 10 questions  
  - Full practice: 20-30 questions
- **Files to implement**:
  - `src/core/education/quiz_generator.py`
  - `src/core/education/adaptive_engine.py`

### 3.3 Progress Tracking
**Requirement ID**: ED-003
- **Metrics to Track**:
  - Questions attempted/correct by topic
  - Time spent per question type
  - Improvement trends
  - Concept mastery (>80% = mastered)
- **Database Updates**:
  - Real-time progress updates
  - Session summaries
  - Learning analytics
- **Files to implement**:
  - `src/core/education/progress_tracker.py`
  - Update `src/database/utils.py`

## 4. User Interface Requirements

### 4.1 Frontend Voice Interface
**Requirement ID**: UI-001
- **Voice Interaction States**:
  - Idle (waiting for wake word)
  - Listening (recording user)
  - Processing (thinking)
  - Speaking (playing response)
  - Error (gentle feedback)
- **Visual Feedback**:
  - Waveform during recording
  - Thinking animation
  - Text transcription display
- **Files to update**:
  - `frontend/src/components/VoiceInteraction.tsx`
  - `frontend/src/contexts/AudioContext.tsx`

### 4.2 Learning Dashboard
**Requirement ID**: UI-002
- **Student View**:
  - Today's progress
  - Streak counter
  - Recent achievements
  - Next lesson suggestion
- **Data Visualization**:
  - Progress charts by subject
  - Accuracy trends
  - Time spent learning
- **Files to implement**:
  - `frontend/src/components/ProgressCharts.tsx`
  - `frontend/src/components/AchievementBadges.tsx`

### 4.3 Parent Dashboard
**Requirement ID**: UI-003
- **Access**: Separate login with parent role
- **Features**:
  - Child's progress overview
  - Detailed reports
  - Content settings
  - Session limits
- **Files to implement**:
  - `frontend/src/components/ParentDashboard.tsx`
  - `src/api/routes/parent.py`

## 5. System Integration Requirements

### 5.1 Complete Voice Loop
**Requirement ID**: SYS-001
- **Flow**: Wake word → STT → LLM → TTS → Speaker
- **Latency Budget**:
  - Wake word: 300ms
  - STT: 500ms
  - LLM: 1500ms
  - TTS: 200ms
  - Total: < 2.5 seconds
- **Implementation Tasks**:
  1. Connect wake word to audio recording
  2. Stream audio to STT
  3. Send text to LLM with context
  4. Generate TTS from response
  5. Play audio and update UI

### 5.2 Database Integration
**Requirement ID**: SYS-002
- **Connect Models to Logic**:
  - User sessions tracking
  - Question history
  - Progress updates
  - Audio logs
- **Caching Strategy**:
  - Redis for active sessions
  - Recent questions in memory
  - User preferences cached

### 5.3 Background Tasks
**Requirement ID**: SYS-003
- **Celery Tasks**:
  - Audio processing pipeline
  - Content indexing
  - Progress analytics
  - Report generation
- **Task Priorities**:
  - High: Audio processing
  - Medium: Progress updates
  - Low: Analytics, reports

## 6. Performance Requirements

### 6.1 Response Times
**Requirement ID**: PERF-001
- Wake word detection: < 300ms
- First byte of audio: < 1000ms
- Complete response: < 2500ms
- UI updates: < 100ms

### 6.2 Resource Usage
**Requirement ID**: PERF-002
- RAM usage: < 4GB
- GPU memory: < 2GB
- CPU usage: < 50% average
- Storage: < 20GB total

### 6.3 Scalability
**Requirement ID**: PERF-003
- Concurrent users: 1 (local device)
- Questions per session: Unlimited
- Session duration: Up to 2 hours
- Daily usage: 4-6 hours

## Implementation Checklist

### Phase 1: Core Voice (Week 1-2)
- [ ] Implement Piper TTS engine
- [ ] Connect wake word to recording
- [ ] Integrate STT with streaming
- [ ] Connect real LLM for responses
- [ ] Complete voice pipeline testing

### Phase 2: Educational Core (Week 3-4)
- [ ] Import ISEE question bank
- [ ] Implement quiz generator
- [ ] Build adaptive algorithm
- [ ] Connect progress tracking
- [ ] Create practice modes

### Phase 3: User Experience (Week 5-6)
- [ ] Update voice interaction UI
- [ ] Build progress dashboards
- [ ] Implement achievements
- [ ] Create parent portal
- [ ] Add session management

### Phase 4: Polish & Testing (Week 7-8)
- [ ] Performance optimization
- [ ] Comprehensive testing
- [ ] Content review
- [ ] Beta testing
- [ ] Production preparation