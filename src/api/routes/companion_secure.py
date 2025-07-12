"""
Secured API routes for companion mode functionality
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from typing import Optional, Dict, List
import os
import json
import sqlite3
from pathlib import Path
from datetime import datetime
import random
from sqlalchemy.orm import Session

from src.core.companion.mode_manager import TutorMode, ModeManager
from src.core.security.auth import get_current_active_user
from src.core.security.validation import (
    ChatMessageRequest, ModeSwitchRequest, ContentSearchRequest,
    validate_table_name, sanitize_text
)
from src.core.security.middleware import limiter
from src.database.base import get_db
from src.database.models import User, AudioLog, Session as DBSession

router = APIRouter()

# Global instances
mode_manager = ModeManager()
knowledge_path = Path(os.getenv("KNOWLEDGE_PATH", "./data/knowledge"))

@router.post("/chat")
@limiter.limit("30/minute")
async def chat(
    request: Request,
    chat_request: ChatMessageRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Handle chat messages in current mode with authentication"""
    
    # Set mode if specified
    if chat_request.mode:
        mode_manager.set_mode(chat_request.mode)
    
    message = chat_request.message.strip()
    user_context = chat_request.user_context or {}
    
    # Add user info to context
    user_context.update({
        "user_id": current_user.id,
        "age": current_user.age,
        "grade_level": current_user.grade_level
    })
    
    # Get current mode
    current_mode = mode_manager.get_current_mode()
    
    # Log the interaction
    audio_log = AudioLog(
        user_id=current_user.id,
        transcription=message,
        response="",  # Will be updated below
        mode=current_mode.value,
        metadata={"user_context": user_context}
    )
    
    # Generate response based on mode
    try:
        if current_mode == TutorMode.TUTOR:
            response = await _handle_tutor_mode(message, user_context)
        elif current_mode == TutorMode.FRIEND:
            response = await _handle_friend_mode(message, user_context)
        else:  # HYBRID
            suggested_mode = mode_manager.analyze_intent(message)
            if suggested_mode != current_mode:
                response = await _handle_hybrid_mode(message, user_context, suggested_mode)
            else:
                response = await _handle_friend_mode(message, user_context)
        
        # Update audio log with response
        audio_log.response = response["response"]
        db.add(audio_log)
        db.commit()
        
        return response
        
    except Exception as e:
        # Log error but don't expose internal details
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to process message")

@router.post("/switch-mode")
@limiter.limit("10/minute")
async def switch_mode(
    request: Request,
    mode_request: ModeSwitchRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Switch between companion modes with authentication"""
    new_mode = mode_request.new_mode.lower()
    
    try:
        mode_enum = TutorMode(new_mode)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid mode. Choose from: {[m.value for m in TutorMode]}"
        )
    
    previous_mode = mode_manager.get_current_mode()
    mode_manager.set_mode(new_mode)
    
    return {
        "previous_mode": previous_mode.value,
        "current_mode": mode_enum.value,
        "message": f"Switched to {mode_enum.value} mode!"
    }

@router.get("/current-mode")
async def get_current_mode(
    current_user: User = Depends(get_current_active_user)
):
    """Get the current companion mode"""
    return {
        "mode": mode_manager.get_current_mode().value,
        "description": mode_manager.get_mode_description()
    }

@router.post("/search-knowledge")
@limiter.limit("20/minute")
async def search_knowledge(
    request: Request,
    search_request: ContentSearchRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Search the knowledge base with authentication"""
    results = []
    
    # Validate and sanitize query
    query = search_request.query
    
    # Search in appropriate database based on subject
    if search_request.subject:
        db_name = f"{search_request.subject}_resources.db"
    else:
        db_name = "general_knowledge.db"
    
    db_path = knowledge_path / "databases" / db_name
    
    if not db_path.exists():
        raise HTTPException(status_code=404, detail="Knowledge database not found")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Use parameterized query to prevent SQL injection
        cursor.execute("""
            SELECT question, correct_answer, explanation 
            FROM questions 
            WHERE question LIKE ? 
            LIMIT ?
        """, (f"%{query}%", search_request.limit))
        
        for row in cursor.fetchall():
            results.append({
                "question": row[0],
                "answer": row[1],
                "explanation": row[2] if len(row) > 2 else None
            })
        
        conn.close()
        
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail="Database error")
    
    return {
        "query": query,
        "results": results,
        "count": len(results)
    }

@router.get("/learning-stats/{user_id}")
@limiter.limit("10/minute")
async def get_learning_stats(
    request: Request,
    user_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get learning statistics for a user with proper authorization"""
    
    # Check authorization - users can only access their own stats unless they're a parent/teacher
    if str(current_user.id) != user_id and current_user.role not in ["parent", "teacher", "admin"]:
        raise HTTPException(status_code=403, detail="Not authorized to view these stats")
    
    # Get user stats from database
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get recent sessions
    recent_sessions = db.query(DBSession).filter(
        DBSession.user_id == user_id
    ).order_by(DBSession.started_at.desc()).limit(10).all()
    
    # Calculate stats
    total_time = sum((s.ended_at - s.started_at).total_seconds() 
                     for s in recent_sessions if s.ended_at) / 3600  # hours
    
    return {
        "user_id": user_id,
        "total_sessions": len(recent_sessions),
        "total_time_hours": round(total_time, 2),
        "current_level": target_user.grade_level,
        "age": target_user.age,
        "recent_activity": [
            {
                "date": s.started_at.isoformat(),
                "duration_minutes": ((s.ended_at - s.started_at).total_seconds() / 60) if s.ended_at else 0,
                "mode": s.mode
            }
            for s in recent_sessions
        ]
    }

# Helper functions
async def _handle_tutor_mode(message: str, context: dict) -> dict:
    """Handle messages in tutor mode"""
    # Check for ISEE-related keywords
    isee_keywords = ["test", "practice", "question", "problem", "solve", "answer", "explain"]
    
    if any(keyword in message.lower() for keyword in isee_keywords):
        # Search for relevant practice questions
        results = await _search_practice_questions(message)
        if results:
            return {
                "response": f"Here's a practice question: {results[0]['question']}",
                "mode": "tutor",
                "practice_question": results[0]
            }
    
    return {
        "response": "I'm in tutor mode! I can help you practice for the ISEE test. What subject would you like to work on?",
        "mode": "tutor",
        "suggestions": ["Math problems", "Vocabulary", "Reading comprehension", "Verbal reasoning"]
    }

async def _handle_friend_mode(message: str, context: dict) -> dict:
    """Handle messages in friend mode"""
    fun_facts = [
        "Did you know that octopuses have three hearts?",
        "A group of flamingos is called a 'flamboyance'!",
        "Bananas are berries, but strawberries aren't!",
        "Wombat poop is cube-shaped!"
    ]
    
    if "fact" in message.lower() or "tell me" in message.lower():
        return {
            "response": random.choice(fun_facts),
            "mode": "friend",
            "type": "fun_fact"
        }
    
    return {
        "response": f"That's interesting! In friend mode, I love chatting about all sorts of things. {random.choice(fun_facts)}",
        "mode": "friend"
    }

async def _handle_hybrid_mode(message: str, context: dict, suggested_mode: TutorMode) -> dict:
    """Handle messages in hybrid mode"""
    if suggested_mode == TutorMode.TUTOR:
        response = await _handle_tutor_mode(message, context)
        response["suggested_mode"] = "tutor"
        response["suggestion_reason"] = "This seems like a study question"
    else:
        response = await _handle_friend_mode(message, context)
        response["suggested_mode"] = "friend"
        response["suggestion_reason"] = "This seems like casual conversation"
    
    return response

async def _search_practice_questions(query: str) -> List[dict]:
    """Search for practice questions in the knowledge base"""
    # This is a simplified version - in production, use proper search
    return [{
        "question": "If 3x + 7 = 22, what is the value of x?",
        "answer": "5",
        "explanation": "Subtract 7 from both sides: 3x = 15, then divide by 3: x = 5"
    }]