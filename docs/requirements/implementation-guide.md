# Implementation Guide: Making ISEE Tutor Functional

This guide provides step-by-step instructions for implementing the missing features, referencing the requirements in `product-requirements.md` and `technical-requirements.md`.

## Priority 1: Complete Voice Pipeline (VR-001 to VR-004)

### 1.1 Implement TTS Engine (VR-003)

**File**: Create `src/core/audio/tts_engine.py`
```python
# Requirements:
# - Use Piper TTS for local, fast synthesis
# - Child-friendly voice
# - Adjustable speed
# - Queue management for responses
```

**Update**: `src/core/tasks/audio_tasks.py`
- Replace "TTS not yet implemented" with actual Piper call
- Add voice selection logic based on user preference
- Implement audio caching for common phrases

### 1.2 Connect Voice Pipeline (SYS-001)

**File**: Create `src/core/audio/voice_pipeline.py`
```python
# Implement the complete flow:
# 1. Wake word triggers recording
# 2. Audio streams to STT
# 3. Text sent to LLM with context
# 4. Response generated
# 5. TTS speaks response
# 6. UI updates throughout
```

**Integration Points**:
- Update `src/api/main.py` WebSocket to handle voice events
- Modify `frontend/src/contexts/AudioContext.tsx` for streaming

## Priority 2: Real AI Integration (AI-001 to AI-003)

### 2.1 Fix LLM Integration (AI-001)

**File**: Update `src/models/companion_llm.py`
- Remove SQLite database lookups
- Implement proper Llama model initialization
- Add system prompts for each mode:
  - Tutor: "You are an encouraging ISEE test prep tutor for children..."
  - Friend: "You are a fun, educational companion for children..."
- Add context window management

### 2.2 Connect Chat Endpoint (AI-002)

**File**: Update `src/api/routes/companion.py`
- Replace `_search_knowledge_base()` with `companion_llm.generate()`
- Implement conversation history tracking
- Add safety filters for child-appropriate content
- Connect to progress tracking for educational insights

### 2.3 Implement RAG for Education (AI-003)

**File**: Create `src/core/education/knowledge_retrieval.py`
- Use ChromaDB to search educational content
- Implement relevance scoring
- Add source attribution to responses
- Cache frequently accessed content

## Priority 3: Educational Content System (ED-001 to ED-003)

### 3.1 Content Import Tools (ED-001)

**File**: Create `scripts/import_isee_content.py`
```python
# Import ISEE questions from various sources:
# - PDF files with practice tests
# - CSV files with question banks
# - JSON files with structured content
# Validate and store in database
```

**Database Population**:
- Questions table with proper categorization
- Difficulty levels aligned with ISEE standards
- Explanations for each answer
- Cross-references for related concepts

### 3.2 Quiz Generation Engine (ED-002)

**File**: Create `src/core/education/quiz_generator.py`
```python
# Implement adaptive quiz generation:
# - Select questions based on user level
# - Mix topics according to weaknesses
# - Adjust difficulty dynamically
# - Track time per question
```

**File**: Create `src/core/education/adaptive_engine.py`
- Implement IRT (Item Response Theory) basics
- Calculate user ability estimates
- Select next question optimally
- Identify knowledge gaps

### 3.3 Progress Tracking System (ED-003)

**File**: Create `src/core/education/progress_tracker.py`
- Connect to database models
- Real-time progress updates
- Calculate mastery scores
- Generate learning insights

**Update**: `src/database/utils.py`
- Add progress calculation functions
- Implement streak tracking
- Create achievement checking

## Priority 4: User Interface Completion (UI-001 to UI-003)

### 4.1 Voice Interaction UI (UI-001)

**Update**: `frontend/src/components/VoiceInteraction.tsx`
- Add proper state management for voice pipeline
- Implement visual feedback for each state
- Show real-time transcription
- Display response with formatting

**Create**: `frontend/src/components/VoiceVisualizer.tsx`
- Audio waveform during recording
- Thinking animation during processing
- Speaking indicator during TTS

### 4.2 Learning Dashboard (UI-002)

**Create**: `frontend/src/components/ProgressCharts.tsx`
- Subject progress over time
- Accuracy trends
- Topics mastered visualization
- Study time tracking

**Create**: `frontend/src/components/AchievementBadges.tsx`
- Badge display grid
- Progress towards next badge
- Celebration animations
- Sharing capabilities

### 4.3 Parent Portal (UI-003)

**Create**: `frontend/src/components/ParentDashboard.tsx`
- Overview of all children
- Detailed progress reports
- Content control settings
- Export capabilities

**Create**: `src/api/routes/parent.py`
- Parent authentication endpoints
- Report generation endpoints
- Settings management
- Email report scheduling

## Priority 5: System Integration (SYS-001 to SYS-003)

### 5.1 Voice Loop Implementation

**Create**: `src/core/integration/voice_controller.py`
- Orchestrate all voice components
- Handle state transitions
- Manage timeouts and errors
- Coordinate UI updates

### 5.2 Database Connections

**Update**: All route handlers to actually use database
- Store user interactions
- Update progress in real-time
- Cache for performance
- Handle concurrent updates

### 5.3 Background Task Integration

**Update**: Celery task scheduling
- Audio processing priority queue
- Batch content processing
- Scheduled report generation
- Progress analytics jobs

## Testing Requirements

### Unit Tests
Create test files for each new component:
- `tests/test_tts_engine.py`
- `tests/test_quiz_generator.py`
- `tests/test_progress_tracker.py`
- `tests/test_voice_pipeline.py`

### Integration Tests
- End-to-end voice interaction
- Complete quiz session
- Progress tracking accuracy
- Parent dashboard data flow

### Performance Tests
- Voice pipeline latency
- Concurrent user handling
- Database query optimization
- Memory usage monitoring

## Data Requirements

### ISEE Content Needed
1. **Vocabulary Lists**: 2000+ words with definitions
2. **Practice Questions**: 500+ per subject/level
3. **Reading Passages**: 100+ with questions
4. **Math Problems**: 1000+ with solutions
5. **Explanations**: For every question

### Where to Source Content
- ISEE official guides (with permission)
- Educational content providers
- Create original content
- Open education resources

## Success Criteria

Each implementation should meet:
1. **Functional**: Feature works as specified
2. **Performance**: Meets latency requirements
3. **Reliable**: <1% error rate
4. **Testable**: >80% test coverage
5. **Documented**: Code and user docs

## Next Steps

1. Start with TTS implementation (highest impact)
2. Connect real LLM (enables AI features)
3. Import educational content (makes it useful)
4. Complete voice pipeline (core experience)
5. Build dashboards (user value)