"""
Database utility functions
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func

from .models import User, Progress, Question, Quiz, QuizResult, Subject
from .base import get_db

def create_user(
    db: Session,
    username: str,
    email: Optional[str] = None,
    full_name: Optional[str] = None,
    grade_level: Optional[int] = None,
    age: Optional[int] = None
) -> User:
    """Create a new user"""
    user = User(
        username=username,
        email=email,
        full_name=full_name,
        grade_level=grade_level,
        age=age
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """Get user by username"""
    return db.query(User).filter(User.username == username).first()

def get_user_progress(
    db: Session,
    user_id: int,
    subject: Optional[Subject] = None
) -> List[Progress]:
    """Get user progress records"""
    query = db.query(Progress).filter(Progress.user_id == user_id)
    if subject:
        query = query.filter(Progress.subject == subject)
    return query.all()

def update_user_progress(
    db: Session,
    user_id: int,
    subject: Subject,
    topic: str,
    correct: int,
    total: int,
    time_spent: float
) -> Progress:
    """Update or create user progress"""
    progress = db.query(Progress).filter(
        Progress.user_id == user_id,
        Progress.subject == subject,
        Progress.topic == topic
    ).first()
    
    if not progress:
        progress = Progress(
            user_id=user_id,
            subject=subject,
            topic=topic
        )
        db.add(progress)
    
    # Update statistics
    progress.total_questions = (progress.total_questions or 0) + total
    progress.correct_answers = (progress.correct_answers or 0) + correct
    progress.time_spent_minutes = (progress.time_spent_minutes or 0) + time_spent
    progress.accuracy_rate = progress.correct_answers / progress.total_questions
    progress.last_activity = datetime.utcnow()
    
    db.commit()
    db.refresh(progress)
    return progress

def get_questions_by_criteria(
    db: Session,
    subject: Optional[Subject] = None,
    difficulty: Optional[str] = None,
    grade_level: Optional[int] = None,
    limit: int = 10
) -> List[Question]:
    """Get questions matching criteria"""
    query = db.query(Question)
    
    if subject:
        query = query.filter(Question.subject == subject)
    if difficulty:
        query = query.filter(Question.difficulty == difficulty)
    if grade_level:
        query = query.filter(Question.grade_level == grade_level)
    
    return query.limit(limit).all()

def create_quiz_result(
    db: Session,
    user_id: int,
    quiz_id: int,
    score: float,
    answers: Dict[str, Any],
    time_taken: float
) -> QuizResult:
    """Create quiz result"""
    result = QuizResult(
        user_id=user_id,
        quiz_id=quiz_id,
        score=score,
        answers=answers,
        time_taken_minutes=time_taken,
        completed_at=datetime.utcnow()
    )
    db.add(result)
    db.commit()
    db.refresh(result)
    return result

def get_user_statistics(db: Session, user_id: int) -> Dict[str, Any]:
    """Get comprehensive user statistics"""
    # Get user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return {}
    
    # Get progress summary
    progress = db.query(Progress).filter(Progress.user_id == user_id).all()
    
    # Get quiz results
    quiz_results = db.query(QuizResult).filter(
        QuizResult.user_id == user_id
    ).all()
    
    # Calculate statistics
    total_questions = sum(p.total_questions for p in progress)
    correct_answers = sum(p.correct_answers for p in progress)
    total_time = sum(p.time_spent_minutes for p in progress)
    
    stats = {
        'user': {
            'username': user.username,
            'grade_level': user.grade_level,
            'created_at': user.created_at
        },
        'overall': {
            'total_questions': total_questions,
            'correct_answers': correct_answers,
            'accuracy_rate': correct_answers / total_questions if total_questions > 0 else 0,
            'total_time_minutes': total_time,
            'subjects_studied': len(set(p.subject for p in progress))
        },
        'by_subject': {},
        'quiz_performance': {
            'total_quizzes': len(quiz_results),
            'average_score': sum(q.score for q in quiz_results) / len(quiz_results) if quiz_results else 0
        }
    }
    
    # Group by subject
    for p in progress:
        if p.subject.value not in stats['by_subject']:
            stats['by_subject'][p.subject.value] = {
                'total_questions': 0,
                'correct_answers': 0,
                'time_spent_minutes': 0
            }
        
        stats['by_subject'][p.subject.value]['total_questions'] += p.total_questions
        stats['by_subject'][p.subject.value]['correct_answers'] += p.correct_answers
        stats['by_subject'][p.subject.value]['time_spent_minutes'] += p.time_spent_minutes
    
    return stats