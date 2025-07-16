"""
Progress Tracking System for ISEE Tutor
Tracks student progress, identifies weaknesses, and calculates mastery scores
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
import logging

from src.database import (
    User, Progress, QuizResult, Question, Subject, 
    Session as LearningSession, Quiz
)

logger = logging.getLogger(__name__)

class ProgressTracker:
    """Tracks and analyzes student learning progress"""
    
    # Mastery level thresholds
    MASTERY_LEVELS = {
        'beginner': (0, 50),
        'developing': (50, 70),
        'proficient': (70, 85),
        'advanced': (85, 95),
        'mastered': (95, 100)
    }
    
    # Minimum attempts before calculating mastery
    MIN_ATTEMPTS_FOR_MASTERY = 3
    
    # Weight for recent performance (higher = more weight on recent)
    RECENCY_WEIGHT = 0.7
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def update_quiz_progress(self, user_id: int, quiz_result_id: int) -> Dict:
        """
        Update progress based on quiz results
        
        Args:
            user_id: The user's ID
            quiz_result_id: The completed quiz result ID
            
        Returns:
            Dictionary with updated progress info
        """
        # Get quiz result
        result = self.db.query(QuizResult).filter(
            QuizResult.id == quiz_result_id,
            QuizResult.user_id == user_id
        ).first()
        
        if not result:
            logger.error(f"Quiz result {quiz_result_id} not found for user {user_id}")
            return {}
        
        # Get quiz questions
        quiz = self.db.query(Quiz).filter(Quiz.id == result.quiz_id).first()
        if not quiz:
            logger.error(f"Quiz {result.quiz_id} not found")
            return {}
        
        # Update progress for each subject
        updated_subjects = []
        subject_scores = self._calculate_subject_scores(result, quiz)
        
        for subject, score_data in subject_scores.items():
            progress = self._update_subject_progress(
                user_id, 
                subject, 
                score_data['score'],
                score_data['questions_answered'],
                score_data['time_spent']
            )
            updated_subjects.append({
                'subject': subject.value,
                'new_mastery': progress.skill_level * 100,  # Convert back to percentage
                'score': score_data['score']
            })
        
        # Update overall progress
        overall_progress = self._update_overall_progress(user_id)
        
        # Identify new weaknesses
        weaknesses = self.identify_weaknesses(user_id)
        
        # Calculate streak
        streak = self._update_streak(user_id)
        
        return {
            'updated_subjects': updated_subjects,
            'overall_mastery': overall_progress,
            'weaknesses': weaknesses,
            'streak': streak
        }
    
    def _calculate_subject_scores(self, result: QuizResult, quiz: Quiz) -> Dict:
        """Calculate scores broken down by subject"""
        subject_scores = {}
        
        # Initialize subjects
        for question in quiz.questions:
            if question.subject not in subject_scores:
                subject_scores[question.subject] = {
                    'correct': 0,
                    'total': 0,
                    'time_spent': 0,
                    'points_earned': 0,
                    'points_possible': 0
                }
        
        # Process answers
        for question in quiz.questions:
            subject_data = subject_scores[question.subject]
            subject_data['total'] += 1
            subject_data['points_possible'] += question.points
            
            # Check if answered correctly
            if result.answers and str(question.id) in result.answers:
                answer_data = result.answers[str(question.id)]
                if answer_data.get('is_correct'):
                    subject_data['correct'] += 1
                    subject_data['points_earned'] += question.points
                
                # Add time spent if available
                if 'time_spent' in answer_data:
                    subject_data['time_spent'] += answer_data['time_spent']
        
        # Calculate final scores
        for subject, data in subject_scores.items():
            if data['total'] > 0:
                data['score'] = (data['correct'] / data['total']) * 100
                data['questions_answered'] = data['total']
            else:
                data['score'] = 0
                data['questions_answered'] = 0
        
        return subject_scores
    
    def _update_subject_progress(
        self, 
        user_id: int, 
        subject: Subject,
        new_score: float,
        questions_answered: int,
        time_spent: int
    ) -> Progress:
        """Update progress for a specific subject"""
        # Get or create progress record
        progress = self.db.query(Progress).filter(
            Progress.user_id == user_id,
            Progress.subject == subject
        ).first()
        
        if not progress:
            progress = Progress(
                user_id=user_id,
                subject=subject,
                topic='general',  # Can be more specific later
                skill_level=0.5,  # Start at 50%
                accuracy_rate=0,
                total_questions=0,
                correct_answers=0,
                time_spent_minutes=0,
                last_activity=datetime.utcnow(),
                extra_data={}
            )
            self.db.add(progress)
        
        # Update statistics
        old_total = progress.total_questions
        old_correct = progress.correct_answers
        
        # Calculate new correct count
        new_correct = int(questions_answered * (new_score / 100))
        
        progress.total_questions += questions_answered
        progress.correct_answers += new_correct
        progress.time_spent_minutes += int(time_spent / 60)
        progress.last_activity = datetime.utcnow()
        
        # Calculate new mastery level with recency weighting
        if progress.total_questions >= self.MIN_ATTEMPTS_FOR_MASTERY:
            # Historical average
            historical_avg = (old_correct / old_total * 100) if old_total > 0 else 0
            
            # Weighted average (recent performance weighted more)
            mastery_level = (
                self.RECENCY_WEIGHT * new_score + 
                (1 - self.RECENCY_WEIGHT) * historical_avg
            )
            progress.skill_level = mastery_level / 100  # Convert to 0-1 scale
        else:
            # Simple average for few attempts
            mastery_level = (
                (progress.correct_answers / progress.total_questions) * 100
                if progress.total_questions > 0 else 0
            )
            progress.skill_level = mastery_level / 100
        
        # Update accuracy rate
        progress.accuracy_rate = (
            progress.correct_answers / progress.total_questions
            if progress.total_questions > 0 else 0
        )
        
        self.db.commit()
        return progress
    
    def _update_overall_progress(self, user_id: int) -> float:
        """Calculate overall mastery across all subjects"""
        progress_records = self.db.query(Progress).filter(
            Progress.user_id == user_id
        ).all()
        
        if not progress_records:
            return 0
        
        total_mastery = sum(p.skill_level * 100 for p in progress_records)  # Convert to percentage
        return total_mastery / len(progress_records)
    
    def identify_weaknesses(self, user_id: int, threshold: float = 70) -> List[Dict]:
        """
        Identify areas where student needs improvement
        
        Args:
            user_id: The user's ID
            threshold: Mastery level below which a topic is considered weak
            
        Returns:
            List of weak areas with details
        """
        weak_areas = []
        
        # Get all progress records below threshold
        progress_records = self.db.query(Progress).filter(
            Progress.user_id == user_id,
            Progress.skill_level < threshold / 100,  # Convert threshold to 0-1 scale
            Progress.total_questions >= self.MIN_ATTEMPTS_FOR_MASTERY
        ).all()
        
        for progress in progress_records:
            weak_areas.append({
                'subject': progress.subject.value,
                'topic': progress.topic,
                'mastery_level': progress.skill_level * 100,  # Convert to percentage
                'accuracy': (progress.correct_answers / progress.total_questions * 100)
                           if progress.total_questions > 0 else 0,
                'questions_attempted': progress.total_questions,
                'last_activity': progress.last_activity
            })
        
        # Sort by mastery level (weakest first)
        weak_areas.sort(key=lambda x: x['mastery_level'])
        
        return weak_areas
    
    def get_mastery_report(self, user_id: int) -> Dict:
        """Generate comprehensive mastery report for a user"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return {}
        
        # Get all progress records
        progress_records = self.db.query(Progress).filter(
            Progress.user_id == user_id
        ).all()
        
        # Get recent quiz results
        recent_results = self.db.query(QuizResult).filter(
            QuizResult.user_id == user_id
        ).order_by(QuizResult.completed_at.desc()).limit(10).all()
        
        # Calculate statistics
        subject_mastery = {}
        for progress in progress_records:
            mastery_percentage = progress.skill_level * 100
            subject_mastery[progress.subject.value] = {
                'mastery_level': mastery_percentage,
                'mastery_category': self._get_mastery_category(mastery_percentage),
                'questions_attempted': progress.total_questions,
                'questions_correct': progress.correct_answers,
                'accuracy': (progress.correct_answers / progress.total_questions * 100)
                           if progress.total_questions > 0 else 0,
                'time_spent_hours': progress.time_spent_minutes / 60,
                'last_activity': progress.last_activity
            }
        
        # Calculate trends
        performance_trend = self._calculate_performance_trend(recent_results)
        
        # Get current streak
        streak = self._get_current_streak(user_id)
        
        return {
            'user': {
                'name': user.full_name,
                'grade_level': user.grade_level,
                'age': user.age
            },
            'overall_mastery': self._update_overall_progress(user_id),
            'subject_mastery': subject_mastery,
            'weaknesses': self.identify_weaknesses(user_id),
            'strengths': self.identify_strengths(user_id),
            'performance_trend': performance_trend,
            'total_questions_attempted': sum(p.total_questions for p in progress_records),
            'total_time_spent_hours': sum(p.time_spent_minutes for p in progress_records) / 60,
            'current_streak': streak,
            'recommended_focus': self._get_recommended_focus(user_id)
        }
    
    def identify_strengths(self, user_id: int, threshold: float = 85) -> List[Dict]:
        """Identify areas where student excels"""
        strong_areas = []
        
        progress_records = self.db.query(Progress).filter(
            Progress.user_id == user_id,
            Progress.skill_level >= threshold / 100,  # Convert threshold to 0-1 scale
            Progress.total_questions >= self.MIN_ATTEMPTS_FOR_MASTERY
        ).all()
        
        for progress in progress_records:
            strong_areas.append({
                'subject': progress.subject.value,
                'topic': progress.topic,
                'mastery_level': progress.skill_level * 100,  # Convert to percentage
                'accuracy': (progress.correct_answers / progress.total_questions * 100)
                           if progress.total_questions > 0 else 0,
                'questions_attempted': progress.total_questions
            })
        
        # Sort by mastery level (strongest first)
        strong_areas.sort(key=lambda x: x['mastery_level'], reverse=True)
        
        return strong_areas
    
    def _calculate_performance_trend(self, recent_results: List[QuizResult]) -> str:
        """Analyze recent performance trend"""
        if len(recent_results) < 3:
            return "insufficient_data"
        
        # Get scores from recent quizzes
        recent_scores = [r.score * 100 for r in recent_results[:5]]
        
        # Calculate trend
        if len(recent_scores) >= 2:
            # Simple linear trend
            first_half_avg = sum(recent_scores[len(recent_scores)//2:]) / (len(recent_scores) - len(recent_scores)//2)
            second_half_avg = sum(recent_scores[:len(recent_scores)//2]) / (len(recent_scores)//2)
            
            if second_half_avg > first_half_avg + 5:
                return "improving"
            elif second_half_avg < first_half_avg - 5:
                return "declining"
            else:
                return "stable"
        
        return "stable"
    
    def _get_mastery_category(self, mastery_level: float) -> str:
        """Get mastery category name for a given level"""
        for category, (min_level, max_level) in self.MASTERY_LEVELS.items():
            if min_level <= mastery_level < max_level:
                return category
        return 'mastered'
    
    def _update_streak(self, user_id: int) -> int:
        """Update and return current learning streak"""
        # Get recent sessions
        recent_sessions = self.db.query(LearningSession).filter(
            LearningSession.user_id == user_id
        ).order_by(LearningSession.started_at.desc()).limit(30).all()
        
        if not recent_sessions:
            return 0
        
        # Count consecutive days
        streak = 0
        last_date = None
        
        for session in recent_sessions:
            session_date = session.started_at.date()
            
            if last_date is None:
                # First session
                if (datetime.utcnow().date() - session_date).days <= 1:
                    streak = 1
                    last_date = session_date
                else:
                    break
            else:
                # Check if consecutive
                if (last_date - session_date).days == 1:
                    streak += 1
                    last_date = session_date
                else:
                    break
        
        return streak
    
    def _get_current_streak(self, user_id: int) -> Dict:
        """Get detailed streak information"""
        streak_days = self._update_streak(user_id)
        
        # Get best streak
        # This would require additional tracking in production
        best_streak = max(streak_days, 7)  # Placeholder
        
        return {
            'current': streak_days,
            'best': best_streak,
            'status': 'active' if streak_days > 0 else 'broken'
        }
    
    def _get_recommended_focus(self, user_id: int) -> List[str]:
        """Get recommended areas to focus on"""
        weaknesses = self.identify_weaknesses(user_id, threshold=75)
        recommendations = []
        
        # Prioritize by weakness and recency
        for weakness in weaknesses[:3]:  # Top 3 weak areas
            recommendations.append({
                'subject': weakness['subject'],
                'reason': f"Mastery at {weakness['mastery_level']:.1f}%",
                'suggested_practice': f"Try 10-15 {weakness['subject']} questions daily"
            })
        
        return recommendations
    
    def get_progress_summary(self, user_id: int, days: int = 7) -> Dict:
        """Get progress summary for the last N days"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Get recent quiz results
        recent_results = self.db.query(QuizResult).filter(
            QuizResult.user_id == user_id,
            QuizResult.completed_at >= cutoff_date
        ).all()
        
        # Calculate statistics
        total_quizzes = len(recent_results)
        total_questions = sum(r.total_questions for r in recent_results)
        total_correct = sum(r.correct_answers for r in recent_results)
        avg_score = sum(r.score for r in recent_results) / total_quizzes if total_quizzes > 0 else 0
        
        # Get time spent
        total_time = sum(r.time_taken_minutes for r in recent_results)
        
        # Get subject breakdown
        subject_performance = {}
        for result in recent_results:
            if result.feedback and 'by_subject' in result.feedback:
                for subject, data in result.feedback['by_subject'].items():
                    if subject not in subject_performance:
                        subject_performance[subject] = {'correct': 0, 'total': 0}
                    
                    subject_performance[subject]['correct'] += data.get('correct', 0)
                    subject_performance[subject]['total'] += data.get('total', 0)
        
        return {
            'period_days': days,
            'total_quizzes': total_quizzes,
            'total_questions': total_questions,
            'total_correct': total_correct,
            'accuracy': (total_correct / total_questions * 100) if total_questions > 0 else 0,
            'average_score': avg_score * 100,
            'time_spent_hours': total_time / 60,
            'subject_performance': {
                subject: {
                    'accuracy': (data['correct'] / data['total'] * 100) if data['total'] > 0 else 0,
                    'questions': data['total']
                }
                for subject, data in subject_performance.items()
            }
        }