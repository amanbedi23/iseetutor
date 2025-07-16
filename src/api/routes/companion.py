"""
API routes for companion mode functionality
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, List
import os
import sys
import json
import sqlite3
from pathlib import Path
from datetime import datetime
import random

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.core.companion.mode_manager import TutorMode, ModeManager
from src.core.llm import get_companion_llm

router = APIRouter()

# Global instances
mode_manager = ModeManager()
knowledge_path = Path(os.getenv("KNOWLEDGE_PATH", "./data/knowledge"))
companion_llm = None  # Will be initialized on first use

class ChatRequest(BaseModel):
    message: str
    mode: Optional[str] = None
    user_context: Dict = {}

class ModeChangeRequest(BaseModel):
    new_mode: str
    reason: Optional[str] = None

class KnowledgeQuery(BaseModel):
    query: str
    category: Optional[str] = None
    limit: int = 5

class PracticeQuestionRequest(BaseModel):
    subject: str
    difficulty: str = "medium"

def get_knowledge_response(query: str, mode: TutorMode, context: Dict) -> Dict:
    """Get response from knowledge base based on query and mode"""
    
    if mode == TutorMode.TUTOR:
        return get_isee_response(query, context)
    elif mode == TutorMode.FRIEND:
        return get_friend_response(query, context)
    else:  # HYBRID
        # Determine based on query content
        if any(word in query.lower() for word in ['isee', 'test', 'practice', 'study', 'math', 'verbal']):
            return get_isee_response(query, context)
        else:
            return get_friend_response(query, context)

def get_isee_response(query: str, context: Dict) -> Dict:
    """Get ISEE tutoring response from knowledge base"""
    
    db_path = knowledge_path / "databases" / "isee_content.db"
    if not db_path.exists():
        return {
            "response": "I'm having trouble accessing my study materials. Let's try a different topic!",
            "source": "error"
        }
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check for specific topics
    query_lower = query.lower()
    
    # Look for questions about specific subjects
    if any(word in query_lower for word in ['synonym', 'word', 'vocabulary']):
        # Get vocabulary help
        cursor.execute("""
            SELECT question, correct_answer, explanation 
            FROM questions 
            WHERE question_type = 'multiple_choice' 
            AND topic_id IN (SELECT id FROM topics WHERE topic = 'synonyms')
            ORDER BY RANDOM() LIMIT 1
        """)
        result = cursor.fetchone()
        
        if result:
            response = f"Let's practice synonyms! {result[0]}\n\nThe answer is: {result[1]}\n\nExplanation: {result[2]}"
        else:
            response = "Let's practice synonyms! A synonym is a word that means the same as another word. For example, 'happy' and 'joyful' are synonyms."
    
    elif any(word in query_lower for word in ['math', 'fraction', 'add', 'subtract', 'multiply']):
        # Get math help
        cursor.execute("""
            SELECT question, correct_answer, explanation 
            FROM questions 
            WHERE topic_id IN (SELECT id FROM topics WHERE subject = 'mathematics')
            ORDER BY RANDOM() LIMIT 1
        """)
        result = cursor.fetchone()
        
        if result:
            response = f"Here's a math practice question: {result[0]}\n\nAnswer: {result[1]}\n\nLet me explain: {result[2]}"
        else:
            response = "Let's work on math! What specific topic would you like to practice - fractions, algebra, or geometry?"
    
    elif 'tip' in query_lower or 'help' in query_lower:
        # Get study tips
        cursor.execute("""
            SELECT tip, example 
            FROM study_tips 
            ORDER BY RANDOM() LIMIT 1
        """)
        result = cursor.fetchone()
        
        if result:
            response = f"Here's a helpful study tip: {result[0]}\n\nFor example: {result[1]}"
        else:
            response = "Here's a tip: Practice a little bit every day rather than cramming. Consistent practice helps you remember better!"
    
    else:
        # General ISEE help
        response = """I'm here to help you prepare for the ISEE test! I can help with:
        
• Verbal Reasoning (synonyms, analogies, sentence completion)
• Quantitative Reasoning (math concepts and problem solving)  
• Reading Comprehension strategies
• Mathematics Achievement practice

What would you like to work on today?"""
    
    conn.close()
    
    return {
        "response": response,
        "source": "isee_content",
        "mode": "tutor"
    }

def get_friend_response(query: str, context: Dict) -> Dict:
    """Get friendly companion response from knowledge base"""
    
    db_path = knowledge_path / "databases" / "general_knowledge.db"
    if not db_path.exists():
        return {
            "response": "Let me think about that! What else would you like to talk about?",
            "source": "error"
        }
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    query_lower = query.lower()
    
    # Check for specific topics
    if any(word in query_lower for word in ['animal', 'cat', 'dog', 'pet']):
        cursor.execute("""
            SELECT fact, explanation 
            FROM facts 
            WHERE category = 'animals'
            ORDER BY RANDOM() LIMIT 1
        """)
    elif any(word in query_lower for word in ['space', 'planet', 'star', 'moon']):
        cursor.execute("""
            SELECT fact, explanation 
            FROM facts 
            WHERE category = 'space'
            ORDER BY RANDOM() LIMIT 1
        """)
    elif any(word in query_lower for word in ['experiment', 'science', 'try']):
        # Get science experiment
        exp_db = knowledge_path / "databases" / "science_facts.db"
        if exp_db.exists():
            exp_conn = sqlite3.connect(exp_db)
            exp_cursor = exp_conn.cursor()
            exp_cursor.execute("""
                SELECT name, materials, instructions, explanation 
                FROM experiments 
                ORDER BY RANDOM() LIMIT 1
            """)
            exp_result = exp_cursor.fetchone()
            exp_conn.close()
            
            if exp_result:
                response = f"Here's a fun experiment: {exp_result[0]}!\n\nYou'll need: {exp_result[1]}\n\nSteps:\n{exp_result[2]}\n\nWhy it works: {exp_result[3]}"
                conn.close()
                return {
                    "response": response,
                    "source": "science_experiments",
                    "mode": "friend"
                }
    elif 'fact' in query_lower or 'tell me' in query_lower:
        cursor.execute("""
            SELECT fact, explanation 
            FROM facts 
            ORDER BY RANDOM() LIMIT 1
        """)
    else:
        # General response
        cursor.execute("""
            SELECT fact, explanation 
            FROM facts 
            WHERE fun_level >= 4
            ORDER BY RANDOM() LIMIT 1
        """)
    
    result = cursor.fetchone()
    conn.close()
    
    if result:
        response = f"Did you know: {result[0]}\n\n{result[1] if result[1] else ''}"
    else:
        response = "That's interesting! Tell me more about what you're curious about!"
    
    return {
        "response": response,
        "source": "general_knowledge",
        "mode": "friend"
    }

@router.post("/chat")
async def chat(request: ChatRequest):
    """Handle chat messages in current mode"""
    
    global companion_llm
    
    # Initialize LLM on first use
    if companion_llm is None:
        try:
            companion_llm = get_companion_llm()
        except Exception as e:
            # Fall back to knowledge base if LLM fails to load
            kb_response = get_knowledge_response(
                request.message,
                mode_manager.current_mode,
                request.user_context
            )
            return {
                "response": kb_response["response"],
                "mode": mode_manager.current_mode.value,
                "source": "knowledge_base_fallback",
                "error": f"LLM initialization failed: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    
    # Update mode if specified
    if request.mode:
        try:
            new_mode = TutorMode(request.mode)
            await mode_manager.switch_mode(new_mode)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid mode")
    
    # Get current mode
    current_mode = mode_manager.current_mode
    
    try:
        # Generate response using real LLM with citations
        response_text, metadata = companion_llm.generate_response_with_citations(
            message=request.message,
            mode=current_mode.value,
            context=request.user_context,
            temperature=0.7 if current_mode == TutorMode.FRIEND else 0.5
        )
        
        # Format response based on mode
        formatted_response = mode_manager.format_response(
            response_text,
            'explanation' if current_mode == TutorMode.TUTOR else 'general'
        )
        
        # Check if mode switch should be suggested
        suggested_mode = mode_manager.should_suggest_mode_switch(request.user_context)
        
        return {
            "response": formatted_response,
            "mode": current_mode.value,
            "source": "llm",
            "model_metadata": metadata,
            "suggested_mode": suggested_mode.value if suggested_mode else None,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        # Fall back to knowledge base if LLM fails
        kb_response = get_knowledge_response(
            request.message,
            current_mode,
            request.user_context
        )
        
        return {
            "response": kb_response["response"],
            "mode": current_mode.value,
            "source": "knowledge_base_fallback",
            "error": str(e),
            "suggested_mode": mode_manager.should_suggest_mode_switch(request.user_context).value if mode_manager.should_suggest_mode_switch(request.user_context) else None,
            "timestamp": datetime.now().isoformat()
        }

@router.post("/switch-mode")
async def switch_mode(request: ModeChangeRequest):
    """Explicitly switch between modes"""
    
    try:
        new_mode = TutorMode(request.new_mode)
        message = await mode_manager.switch_mode(new_mode, request.reason)
        
        return {
            "success": True,
            "message": message,
            "new_mode": new_mode.value,
            "config": mode_manager.get_mode_config()
        }
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid mode")

@router.get("/current-mode")
async def get_current_mode():
    """Get current mode and configuration"""
    
    return {
        "mode": mode_manager.current_mode.value,
        "config": mode_manager.get_mode_config(),
        "mode_history": mode_manager.mode_history[-5:] if mode_manager.mode_history else []
    }

@router.get("/modes")
async def get_available_modes():
    """Get all available modes and their configurations"""
    
    modes = {}
    for mode in TutorMode:
        modes[mode.value] = mode_manager.mode_configs[mode]
    
    return {
        "modes": modes,
        "current": mode_manager.current_mode.value
    }

@router.post("/knowledge/query")
async def query_knowledge(request: KnowledgeQuery):
    """Query knowledge bases directly"""
    
    results = []
    
    # Search ISEE content
    isee_db = knowledge_path / "databases" / "isee_content.db"
    if isee_db.exists():
        conn = sqlite3.connect(isee_db)
        cursor = conn.cursor()
        
        # Search questions
        cursor.execute("""
            SELECT question, correct_answer, explanation 
            FROM questions 
            WHERE question LIKE ? 
            LIMIT ?
        """, (f"%{request.query}%", request.limit))
        
        for row in cursor.fetchall():
            results.append({
                "type": "isee_question",
                "content": {
                    "question": row[0],
                    "answer": row[1],
                    "explanation": row[2]
                }
            })
        
        conn.close()
    
    # Search general knowledge
    general_db = knowledge_path / "databases" / "general_knowledge.db"
    if general_db.exists() and len(results) < request.limit:
        conn = sqlite3.connect(general_db)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT fact, explanation, category 
            FROM facts 
            WHERE fact LIKE ? OR explanation LIKE ?
            LIMIT ?
        """, (f"%{request.query}%", f"%{request.query}%", request.limit - len(results)))
        
        for row in cursor.fetchall():
            results.append({
                "type": "fun_fact",
                "content": {
                    "fact": row[0],
                    "explanation": row[1],
                    "category": row[2]
                }
            })
        
        conn.close()
    
    return {
        "query": request.query,
        "results": results,
        "count": len(results)
    }

@router.post("/practice-question")
async def generate_practice_question(request: PracticeQuestionRequest):
    """Generate a practice question using the LLM"""
    
    global companion_llm
    
    # Initialize LLM if needed
    if companion_llm is None:
        try:
            companion_llm = get_companion_llm()
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"LLM not available: {str(e)}")
    
    try:
        # Generate practice question
        question_data = companion_llm.generate_practice_question(
            subject=request.subject,
            difficulty=request.difficulty
        )
        
        return {
            "success": True,
            "question": question_data,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate question: {str(e)}")

@router.get("/stats")
async def get_session_stats():
    """Get session statistics"""
    
    mode_history = mode_manager.mode_history
    
    # Calculate time in each mode
    mode_times = {"tutor": 0, "friend": 0, "hybrid": 0}
    
    if mode_history:
        for i in range(len(mode_history)):
            start_time = mode_history[i]["timestamp"]
            end_time = mode_history[i+1]["timestamp"] if i+1 < len(mode_history) else datetime.now()
            duration = (end_time - start_time).total_seconds() / 60  # minutes
            mode_times[mode_history[i]["to"].value] += duration
    
    return {
        "mode_switches": len(mode_history),
        "current_mode": mode_manager.current_mode.value,
        "mode_times_minutes": mode_times,
        "session_start": mode_manager.session_start.isoformat(),
        "mode_history": mode_history[-10:] if mode_history else []
    }