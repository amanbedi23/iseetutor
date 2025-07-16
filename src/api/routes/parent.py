"""
Parent portal API routes for monitoring children's progress.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc

from src.database.base import get_db
from src.database.models import User, Progress, Session as LearningSession, QuizResult, Question, Quiz
from src.core.security.auth import get_current_active_user, require_role
from src.core.security.validation import validate_message
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/parent", tags=["parent"])

class ChildSummary(BaseModel):
    """Summary information for a child."""
    id: str
    name: str
    age: int
    grade_level: int
    last_active: Optional[datetime]
    current_streak: int
    total_questions: int
    accuracy_rate: float
    weekly_progress: float
    strongest_subject: Optional[str]
    needs_attention: bool

class DetailedProgress(BaseModel):
    """Detailed progress report for a child."""
    child_id: str
    date_range: Dict[str, datetime]
    subjects: Dict[str, Dict[str, Any]]
    daily_activity: List[Dict[str, Any]]
    quiz_results: List[Dict[str, Any]]
    achievements: List[Dict[str, Any]]
    recommendations: List[str]

class StudyGoal(BaseModel):
    """Study goal configuration."""
    goal_type: str = Field(..., pattern="^(questions|time|accuracy|streak)$")
    target_value: int = Field(..., ge=1, le=1000)
    time_period: str = Field(..., pattern="^(daily|weekly|monthly)$")
    subject: Optional[str] = None

class ParentNotification(BaseModel):
    """Parent notification preferences."""
    daily_summary: bool = True
    achievement_alerts: bool = True
    inactivity_alerts: bool = True
    weekly_report: bool = True
    alert_threshold_days: int = Field(default=3, ge=1, le=7)

@router.get("/children", response_model=List[ChildSummary])
async def get_children(
    current_user: User = Depends(require_role("parent")),
    db: Session = Depends(get_db)
):
    """Get summary of all children for the parent."""
    # Get children linked to this parent
    parent_metadata = current_user.user_metadata or {}
    child_ids = parent_metadata.get("linked_children", [])
    
    if not child_ids:
        return []
    
    children = db.query(User).filter(
        and_(
            User.id.in_(child_ids),
            User.role == "student"
        )
    ).all()
    
    summaries = []
    for child in children:
        # Calculate current streak
        today = datetime.utcnow().date()
        streak = calculate_streak(db, child.id, today)
        
        # Get total questions and accuracy
        quiz_results = db.query(QuizResult).filter(
            QuizResult.user_id == child.id
        ).all()
        
        total_questions = sum(r.total_questions for r in quiz_results)
        correct_answers = sum(r.correct_answers for r in quiz_results)
        accuracy_rate = (correct_answers / total_questions * 100) if total_questions > 0 else 0
        
        # Get weekly progress
        week_ago = datetime.utcnow() - timedelta(days=7)
        weekly_results = db.query(QuizResult).filter(
            and_(
                QuizResult.user_id == child.id,
                QuizResult.created_at >= week_ago
            )
        ).all()
        
        weekly_questions = sum(r.total_questions for r in weekly_results)
        weekly_progress = min((weekly_questions / 100) * 100, 100)  # Target: 100 questions/week
        
        # Get strongest subject
        subject_scores = db.query(
            Progress.subject,
            func.avg(Progress.mastery_score).label('avg_score')
        ).filter(
            Progress.user_id == child.id
        ).group_by(Progress.subject).order_by(desc('avg_score')).first()
        
        strongest_subject = subject_scores.subject if subject_scores else None
        
        # Check if needs attention
        last_session = db.query(LearningSession).filter(
            LearningSession.user_id == child.id
        ).order_by(desc(LearningSession.ended_at)).first()
        
        last_active = last_session.ended_at if last_session else child.created_at
        days_inactive = (datetime.utcnow() - last_active).days
        needs_attention = days_inactive > 2 or streak == 0 or accuracy_rate < 70
        
        summaries.append(ChildSummary(
            id=str(child.id),
            name=child.name,
            age=child.age,
            grade_level=child.grade_level,
            last_active=last_active,
            current_streak=streak,
            total_questions=total_questions,
            accuracy_rate=round(accuracy_rate, 1),
            weekly_progress=round(weekly_progress, 1),
            strongest_subject=strongest_subject,
            needs_attention=needs_attention
        ))
    
    return summaries

@router.get("/children/{child_id}/progress", response_model=DetailedProgress)
async def get_child_progress(
    child_id: str,
    days: int = Query(default=30, ge=1, le=90),
    current_user: User = Depends(require_role("parent")),
    db: Session = Depends(get_db)
):
    """Get detailed progress report for a specific child."""
    # Verify parent has access to this child
    parent_metadata = current_user.user_metadata or {}
    child_ids = parent_metadata.get("linked_children", [])
    
    if child_id not in child_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this child's data"
        )
    
    # Get child user
    child = db.query(User).filter(User.id == child_id).first()
    if not child:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Child not found"
        )
    
    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Get progress by subject
    subjects_data = {}
    subjects = ["Verbal Reasoning", "Quantitative Reasoning", "Reading Comprehension", "Mathematics"]
    
    for subject in subjects:
        progress_records = db.query(Progress).filter(
            and_(
                Progress.user_id == child_id,
                Progress.subject == subject,
                Progress.updated_at >= start_date
            )
        ).all()
        
        if progress_records:
            latest = max(progress_records, key=lambda p: p.updated_at)
            subjects_data[subject] = {
                "mastery_score": round(latest.mastery_score, 1),
                "questions_attempted": latest.questions_attempted,
                "correct_answers": latest.correct_answers,
                "last_practiced": latest.updated_at,
                "topics": latest.topic_scores or {}
            }
    
    # Get daily activity
    daily_activity = []
    current_date = start_date.date()
    while current_date <= end_date.date():
        day_start = datetime.combine(current_date, datetime.min.time())
        day_end = day_start + timedelta(days=1)
        
        # Count questions for this day
        day_results = db.query(QuizResult).filter(
            and_(
                QuizResult.user_id == child_id,
                QuizResult.created_at >= day_start,
                QuizResult.created_at < day_end
            )
        ).all()
        
        questions_count = sum(r.total_questions for r in day_results)
        accuracy = 0
        if questions_count > 0:
            correct = sum(r.correct_answers for r in day_results)
            accuracy = round((correct / questions_count) * 100, 1)
        
        daily_activity.append({
            "date": current_date.isoformat(),
            "questions": questions_count,
            "accuracy": accuracy,
            "time_spent": sum(r.time_spent for r in day_results) if day_results else 0
        })
        
        current_date += timedelta(days=1)
    
    # Get recent quiz results
    recent_quizzes = db.query(QuizResult).filter(
        and_(
            QuizResult.user_id == child_id,
            QuizResult.created_at >= start_date
        )
    ).order_by(desc(QuizResult.created_at)).limit(10).all()
    
    quiz_results = []
    for quiz_result in recent_quizzes:
        quiz = db.query(Quiz).filter(Quiz.id == quiz_result.quiz_id).first()
        quiz_results.append({
            "date": quiz_result.created_at,
            "subject": quiz.subject if quiz else "Unknown",
            "score": round((quiz_result.correct_answers / quiz_result.total_questions) * 100, 1),
            "questions": quiz_result.total_questions,
            "time_spent": quiz_result.time_spent
        })
    
    # Get achievements (simplified for now)
    achievements = [
        {"name": "Week Warrior", "earned": True, "date": (end_date - timedelta(days=5)).isoformat()},
        {"name": "Math Master", "earned": False, "progress": 75}
    ]
    
    # Generate recommendations
    recommendations = generate_recommendations(child, subjects_data, daily_activity)
    
    return DetailedProgress(
        child_id=child_id,
        date_range={"start": start_date, "end": end_date},
        subjects=subjects_data,
        daily_activity=daily_activity,
        quiz_results=quiz_results,
        achievements=achievements,
        recommendations=recommendations
    )

@router.post("/children/{child_id}/goals", response_model=dict)
async def set_study_goals(
    child_id: str,
    goals: List[StudyGoal],
    current_user: User = Depends(require_role("parent")),
    db: Session = Depends(get_db)
):
    """Set study goals for a child."""
    # Verify parent has access
    parent_metadata = current_user.user_metadata or {}
    child_ids = parent_metadata.get("linked_children", [])
    
    if child_id not in child_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this child's data"
        )
    
    # Get child and update goals
    child = db.query(User).filter(User.id == child_id).first()
    if not child:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Child not found"
        )
    
    # Store goals in user metadata
    child.user_metadata = child.user_metadata or {}
    child.user_metadata["study_goals"] = [goal.dict() for goal in goals]
    child.user_metadata["goals_updated_at"] = datetime.utcnow().isoformat()
    child.user_metadata["goals_set_by"] = current_user.id
    
    db.commit()
    
    return {
        "message": "Study goals updated successfully",
        "goals_count": len(goals)
    }

@router.post("/children/{child_id}/message", response_model=dict)
async def send_encouragement(
    child_id: str,
    message: str = Query(..., min_length=1, max_length=500),
    current_user: User = Depends(require_role("parent")),
    db: Session = Depends(get_db)
):
    """Send an encouraging message to a child."""
    # Validate message
    validate_message(message)
    
    # Verify parent has access
    parent_metadata = current_user.user_metadata or {}
    child_ids = parent_metadata.get("linked_children", [])
    
    if child_id not in child_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this child"
        )
    
    # Get child
    child = db.query(User).filter(User.id == child_id).first()
    if not child:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Child not found"
        )
    
    # Store message in child's metadata
    child.user_metadata = child.user_metadata or {}
    messages = child.user_metadata.get("parent_messages", [])
    messages.append({
        "from": current_user.name,
        "message": message,
        "timestamp": datetime.utcnow().isoformat(),
        "read": False
    })
    
    # Keep only last 10 messages
    child.user_metadata["parent_messages"] = messages[-10:]
    db.commit()
    
    return {
        "message": "Encouragement sent successfully",
        "recipient": child.name
    }

@router.get("/reports/weekly/{child_id}", response_model=dict)
async def get_weekly_report(
    child_id: str,
    current_user: User = Depends(require_role("parent")),
    db: Session = Depends(get_db)
):
    """Generate a weekly report for a child."""
    # Verify access
    parent_metadata = current_user.user_metadata or {}
    child_ids = parent_metadata.get("linked_children", [])
    
    if child_id not in child_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this child's data"
        )
    
    # Get detailed progress for last 7 days
    progress = await get_child_progress(child_id, 7, current_user, db)
    
    # Calculate weekly stats
    total_questions = sum(day["questions"] for day in progress.daily_activity)
    active_days = sum(1 for day in progress.daily_activity if day["questions"] > 0)
    avg_accuracy = sum(day["accuracy"] for day in progress.daily_activity if day["questions"] > 0)
    avg_accuracy = avg_accuracy / active_days if active_days > 0 else 0
    
    return {
        "week_ending": datetime.utcnow().date().isoformat(),
        "child_id": child_id,
        "summary": {
            "total_questions": total_questions,
            "active_days": active_days,
            "average_accuracy": round(avg_accuracy, 1),
            "subjects_practiced": list(progress.subjects.keys()),
            "achievements_earned": len([a for a in progress.achievements if a.get("earned")])
        },
        "subjects": progress.subjects,
        "recommendations": progress.recommendations,
        "next_week_goals": [
            f"Maintain {active_days}+ active days",
            f"Complete at least {max(100, total_questions)} questions",
            "Focus on " + (progress.recommendations[0] if progress.recommendations else "all subjects")
        ]
    }

@router.put("/notifications", response_model=dict)
async def update_notification_preferences(
    preferences: ParentNotification,
    current_user: User = Depends(require_role("parent")),
    db: Session = Depends(get_db)
):
    """Update parent notification preferences."""
    current_user.user_metadata = current_user.user_metadata or {}
    current_user.user_metadata["notification_preferences"] = preferences.dict()
    db.commit()
    
    return {
        "message": "Notification preferences updated",
        "preferences": preferences.dict()
    }

# Helper functions
def calculate_streak(db: Session, user_id: str, current_date) -> int:
    """Calculate current learning streak for a user."""
    streak = 0
    check_date = current_date
    
    while True:
        # Check if user had activity on this date
        day_start = datetime.combine(check_date, datetime.min.time())
        day_end = day_start + timedelta(days=1)
        
        activity = db.query(QuizResult).filter(
            and_(
                QuizResult.user_id == user_id,
                QuizResult.created_at >= day_start,
                QuizResult.created_at < day_end
            )
        ).first()
        
        if activity:
            streak += 1
            check_date -= timedelta(days=1)
        else:
            # Check if we should continue (allow 1 day gap for today)
            if check_date == current_date:
                check_date -= timedelta(days=1)
                continue
            break
    
    return streak

def generate_recommendations(child: User, subjects_data: dict, daily_activity: list) -> List[str]:
    """Generate personalized recommendations for a child."""
    recommendations = []
    
    # Check for weak subjects
    if subjects_data:
        weak_subjects = [s for s, data in subjects_data.items() 
                        if data["mastery_score"] < 70]
        if weak_subjects:
            recommendations.append(f"Focus on improving {weak_subjects[0]} with extra practice")
    
    # Check activity patterns
    active_days = sum(1 for day in daily_activity if day["questions"] > 0)
    if active_days < 5:
        recommendations.append("Encourage daily practice to build consistency")
    
    # Check accuracy trends
    recent_accuracy = [day["accuracy"] for day in daily_activity[-7:] 
                      if day["questions"] > 0]
    if recent_accuracy and sum(recent_accuracy) / len(recent_accuracy) < 75:
        recommendations.append("Review incorrect answers together to improve accuracy")
    
    # Always add a positive recommendation
    if not recommendations:
        recommendations.append("Great progress! Keep up the excellent work")
    
    return recommendations[:3]  # Return top 3 recommendations