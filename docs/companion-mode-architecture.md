# ISEE Tutor: Companion Mode Architecture

## Overview
Transforming the ISEE Tutor from a test-prep device into a knowledgeable, friendly AI companion for children while maintaining privacy and safety.

## The Challenge: General Knowledge on Edge

### Model Size vs Knowledge Trade-offs

| Model Type | Size | Knowledge Cutoff | General Knowledge | Local Performance |
|------------|------|------------------|-------------------|-------------------|
| Llama 3.2 3B (Q4) | 2-3GB | Recent | Good for size | Excellent on Jetson |
| Llama 3.2 8B (Q4) | 4-6GB | Recent | Better | Good on Jetson |
| Mixtral 8x7B (Q4) | 26GB | Recent | Excellent | Slow on Jetson |
| Local Wikipedia | 20GB | Current | Factual only | Fast lookup |
| Local Wikibooks | 10GB | Current | Educational | Fast lookup |

### Hybrid Approach: Best of Both Worlds

```python
class CompanionAI:
    """
    Hybrid system combining local models with structured knowledge bases
    """
    
    def __init__(self):
        # Core conversational AI (always local)
        self.llm = Llama32_3B(quantized=True)  # 3GB
        
        # Local knowledge bases
        self.knowledge_bases = {
            'wikipedia': LocalWikipedia(),      # 20GB compressed
            'wikibooks': LocalWikibooks(),      # 10GB
            'science': KidsScience(),           # 5GB
            'stories': StoryDatabase(),         # 2GB
            'jokes': KidsJokes(),              # 100MB
            'facts': FunFacts()                # 500MB
        }
        
        # Optional cloud fallback (parent-controlled)
        self.cloud_enabled = False
        self.cloud_llm = None  # Only if enabled
        
    async def respond(self, query: str, context: dict):
        # First, try local knowledge
        local_answer = await self._local_response(query, context)
        
        if local_answer.confidence > 0.8:
            return local_answer
            
        # If enabled and needed, enhance with cloud
        if self.cloud_enabled and local_answer.needs_more_info:
            return await self._hybrid_response(query, local_answer)
            
        return local_answer
```

## Storage Architecture for Companion Mode

### Expanded Storage Layout (1TB SSD)
```
/mnt/storage/
├── models/                     # 40-60GB
│   ├── llama-3.2-3b-q4/       # Base conversational (3GB)
│   ├── llama-3.2-8b-q4/       # Better reasoning (6GB)
│   ├── stable-diffusion/       # Image generation (4GB)
│   ├── whisper-medium/         # Better speech (1.5GB)
│   └── embeddings/            # Multiple models (2GB)
├── knowledge/                  # 100-150GB
│   ├── wikipedia-kids/         # Filtered Wikipedia (20GB)
│   ├── wikibooks/             # Educational content (10GB)
│   ├── science-facts/         # Kid-friendly science (5GB)
│   ├── stories/               # Story collection (10GB)
│   ├── educational-videos/     # Transcripts (20GB)
│   └── safe-web-content/      # Curated web data (30GB)
├── personality/                # 5-10GB
│   ├── conversation-styles/    # Different personalities
│   ├── age-appropriate/       # Age-specific responses
│   ├── interests/             # Topic preferences
│   └── memory/                # Long-term memory
└── content/                    # Rest of space
```

## Making It Work Locally

### 1. **Smart Knowledge Retrieval**
```python
class LocalKnowledgeBase:
    """
    Efficient local knowledge retrieval using RAG
    """
    
    def __init__(self):
        # Use DuckDB for fast SQL queries on large datasets
        self.db = duckdb.connect('/mnt/storage/knowledge/knowledge.db')
        
        # ChromaDB for semantic search
        self.vector_store = ChromaDB(
            persist_directory='/mnt/storage/knowledge/vectors'
        )
        
        # Caching layer
        self.cache = Redis(maxmemory='2gb', policy='lru')
        
    async def search(self, query: str, context: dict):
        # Check cache first
        cached = await self.cache.get(query)
        if cached:
            return cached
            
        # Semantic search
        relevant_docs = await self.vector_store.similarity_search(
            query, k=5, filter={'age_appropriate': True}
        )
        
        # SQL search for specific facts
        sql_results = self.db.execute("""
            SELECT * FROM facts 
            WHERE content ILIKE ? 
            AND age_rating <= ?
            LIMIT 10
        """, [f'%{query}%', context['user_age']])
        
        return self._combine_results(relevant_docs, sql_results)
```

### 2. **Personality System**
```python
class CompanionPersonality:
    """
    Configurable personality for the AI companion
    """
    
    def __init__(self, profile: dict):
        self.traits = {
            'friendliness': 0.9,      # Very friendly
            'humor': 0.7,             # Good sense of humor
            'patience': 1.0,          # Infinitely patient
            'curiosity': 0.8,         # Encourages questions
            'education_focus': 0.6    # Balance fun and learning
        }
        
        self.styles = {
            'tutor': "Helpful teacher who makes learning fun",
            'friend': "Supportive friend who loves to chat",
            'explorer': "Curious companion for adventures",
            'storyteller': "Creative friend who tells stories"
        }
        
        self.current_style = profile.get('preferred_style', 'friend')
        
    def format_response(self, content: str, context: dict):
        """Adjust response based on personality"""
        style_prompt = f"""
        You are a {self.styles[self.current_style]}.
        The child is {context['age']} years old and interested in {context['interests']}.
        
        Respond in a way that is:
        - Age-appropriate and safe
        - {self._get_trait_description()}
        - Encouraging and supportive
        
        Content: {content}
        """
        
        return self.llm.generate(style_prompt)
```

### 3. **Safety & Moderation**
```python
class ChildSafetyFilter:
    """
    Ensure all content is child-appropriate
    """
    
    def __init__(self):
        # Local safety model
        self.safety_model = load_model('child-safety-bert')
        
        # Blocked topics
        self.blocked_topics = load_json('blocked_topics.json')
        
        # Age-appropriate content filters
        self.age_filters = {
            '5-7': 'very_strict',
            '8-10': 'strict', 
            '11-13': 'moderate',
            '14-17': 'light'
        }
        
    async def filter_response(self, response: str, age: int):
        # Check for inappropriate content
        safety_score = self.safety_model.predict(response)
        
        if safety_score < 0.95:
            return self.get_safe_alternative(response)
            
        return response
```

## Comparison: Local vs Cloud for Companion Mode

### Local-Only Approach
**Pros:**
- Complete privacy - conversations never leave device
- No recurring costs
- Works offline
- Consistent personality
- Parent has full control

**Cons:**
- Limited to pre-loaded knowledge
- Can't answer about very recent events
- Larger storage requirements
- May struggle with obscure topics

### Hybrid Approach (Recommended)
```python
class HybridCompanion:
    """
    Local-first with optional cloud enhancement
    """
    
    def __init__(self):
        # Always available locally
        self.local_llm = Llama32_8B()  # Better model for general knowledge
        self.local_knowledge = LocalKnowledgeBase()
        
        # Optional cloud (parent controlled)
        self.cloud_config = {
            'enabled': False,
            'api': 'claude-3-haiku',  # Fast, cheap
            'monthly_limit': 1000,    # Request limit
            'content_filter': 'strict'
        }
        
    async def get_response(self, query: str):
        # Always try local first
        local_response = await self.local_llm.generate(
            query, 
            context=self.local_knowledge.search(query)
        )
        
        # Determine if cloud would help
        needs_cloud = self._assess_query(query, local_response)
        
        if needs_cloud and self.cloud_config['enabled']:
            # Enhance with cloud knowledge
            cloud_response = await self._safe_cloud_query(query)
            return self._merge_responses(local_response, cloud_response)
            
        return local_response
```

## Practical Implementation Tips

### 1. **Pre-load Common Knowledge**
```bash
# Download and process kid-friendly content
python scripts/download_wikipedia_kids.py
python scripts/process_science_facts.py
python scripts/index_story_collection.py
```

### 2. **Optimize for Conversation**
```python
# Use smaller, faster models for chat
config = {
    'chat_model': 'llama-3.2-3b-q4',     # Fast responses
    'knowledge_model': 'llama-3.2-8b-q4', # Deeper questions
    'context_window': 4096,               # Plenty for conversation
    'response_time_target': 2.0           # seconds
}
```

### 3. **Memory System**
```python
class CompanionMemory:
    """
    Remember conversations and build relationships
    """
    
    def __init__(self, child_id: str):
        self.child_id = child_id
        self.memory_db = SQLite(f'/mnt/storage/memory/{child_id}.db')
        
    async def remember(self, interaction: dict):
        # Store important information
        if self._is_important(interaction):
            await self.memory_db.insert({
                'timestamp': datetime.now(),
                'topic': interaction['topic'],
                'sentiment': interaction['sentiment'],
                'facts_learned': interaction['facts'],
                'interests_shown': interaction['interests']
            })
    
    async def recall(self, topic: str):
        # Retrieve relevant memories
        memories = await self.memory_db.query(
            "SELECT * FROM memories WHERE topic LIKE ? ORDER BY timestamp DESC LIMIT 5",
            [f'%{topic}%']
        )
        return memories
```

## Recommended Configuration

For a companion that's both knowledgeable and safe:

1. **Use Llama 3.2 8B (Q4)** - Good balance of knowledge and speed
2. **Pre-load 100GB of curated content** - Wikipedia, science, stories
3. **Enable hybrid mode** - Local-first with optional cloud for current events
4. **Implement strong safety filters** - Age-appropriate content only
5. **Add personality system** - Make it feel like a real friend

## Example Interactions

```python
# Educational companion
Child: "Why is the sky blue?"
Tutor: "Great question! The sky looks blue because of something really cool..."

# Friendly chat
Child: "I'm bored"
Tutor: "Oh no! Let's fix that! Would you like to hear a story, play a word game, or learn about something amazing?"

# Current events (hybrid mode)
Child: "What happened in the Olympics?"
Tutor: [Local] "The Olympics are amazing sports competitions..."
Tutor: [Cloud-enhanced] "The most recent Olympics in Paris had some incredible moments..."

# Creative companion
Child: "Let's make up a story about dragons!"
Tutor: "I love dragon stories! Let's create one together. What color should our dragon be?"
```

## Storage Requirements Summary

For a full companion mode:
- **Models**: 40-60GB (conversational + specialized)
- **Knowledge**: 100-150GB (Wikipedia, books, facts)
- **ISEE Content**: 50-100GB (test prep materials)
- **User Data**: 50-100GB (progress, memories)
- **Cache/Buffer**: 100GB

Total: ~400-500GB used of your 1TB SSD - plenty of room!

## Conclusion

Yes, local models can absolutely work for a general knowledge companion! The key is:
1. Choose the right model size (8B recommended)
2. Pre-load relevant knowledge bases
3. Implement smart retrieval (RAG)
4. Add optional cloud for current events
5. Focus on child-safe, engaging interactions

This gives you a knowledgeable, friendly companion that maintains privacy while being genuinely helpful and fun for kids.