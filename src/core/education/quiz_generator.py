"""
Adaptive Quiz Generator for ISEE Tutor
Generates personalized quizzes based on student performance and learning goals
"""

import random
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass

from sqlalchemy import func, and_, or_
from sqlalchemy.orm import Session

from src.database import Question, Quiz, Progress, QuizResult, Subject, User
from src.database import SessionLocal

logger = logging.getLogger(__name__)

class QuizType(Enum):
    """Types of quizzes available"""
    PRACTICE = "practice"           # General practice
    DIAGNOSTIC = "diagnostic"       # Initial assessment
    SECTION_FOCUS = "section_focus" # Focus on one section
    MIXED = "mixed"                 # Mix of all sections
    WEAKNESS = "weakness"           # Focus on weak areas
    TIMED_TEST = "timed_test"       # Full timed test simulation
    REVIEW = "review"               # Review missed questions

class DifficultyStrategy(Enum):
    """Difficulty adjustment strategies"""
    ADAPTIVE = "adaptive"           # Adjust based on performance
    PROGRESSIVE = "progressive"     # Start easy, get harder
    FIXED = "fixed"                 # Stay at one level
    CHALLENGE = "challenge"         # Always at upper limit

@dataclass
class QuizConfig:
    """Configuration for quiz generation"""
    quiz_type: QuizType
    num_questions: int
    subjects: List[Subject]
    difficulty_strategy: DifficultyStrategy = DifficultyStrategy.ADAPTIVE
    time_limit_minutes: Optional[int] = None
    user_grade_level: int = 5  # Default to grade 5 (lower ISEE)
    focus_topics: Optional[List[str]] = None
    exclude_recent_hours: int = 24  # Don't repeat questions from last 24 hours

class AdaptiveQuizGenerator:
    """Generate adaptive quizzes based on student performance"""
    
    def __init__(self, db_session: Session = None):
        self.db = db_session or SessionLocal()
        
        # ISEE section requirements
        self.isee_structure = {
            Subject.VERBAL_REASONING: {
                'questions': 34,
                'time_minutes': 20,
                'subtypes': ['synonym', 'sentence_completion']
            },
            Subject.QUANTITATIVE_REASONING: {
                'questions': 38,
                'time_minutes': 35,
                'subtypes': ['quantitative_reasoning']
            },
            Subject.READING: {
                'questions': 25,
                'time_minutes': 25,
                'subtypes': ['reading_comprehension', 'main_idea', 'inference']
            },
            Subject.MATH: {
                'questions': 30,
                'time_minutes': 30,
                'subtypes': ['arithmetic', 'algebra', 'geometry', 'probability']
            }
        }
    
    def generate_quiz(
        self, 
        user_id: int, 
        config: QuizConfig
    ) -> Optional[Quiz]:
        """Generate a quiz based on configuration and user history"""
        try:
            # Get user's progress and history
            user_progress = self._get_user_progress(user_id)
            recent_questions = self._get_recent_questions(
                user_id, 
                config.exclude_recent_hours
            )
            
            # Select questions based on quiz type
            if config.quiz_type == QuizType.DIAGNOSTIC:
                questions = self._select_diagnostic_questions(config)
            elif config.quiz_type == QuizType.WEAKNESS:
                questions = self._select_weakness_questions(
                    user_id, 
                    config, 
                    user_progress
                )
            elif config.quiz_type == QuizType.SECTION_FOCUS:
                questions = self._select_section_questions(
                    config, 
                    user_progress, 
                    recent_questions
                )
            elif config.quiz_type == QuizType.TIMED_TEST:
                questions = self._select_full_test_questions(
                    config,
                    recent_questions
                )
            else:
                questions = self._select_mixed_questions(
                    config, 
                    user_progress, 
                    recent_questions
                )
            
            if not questions:
                logger.warning("No questions found for quiz generation")
                return None
            
            # Create quiz
            quiz = self._create_quiz(user_id, config, questions)
            
            return quiz
            
        except Exception as e:
            logger.error(f"Error generating quiz: {e}")
            return None
    
    def _get_user_progress(self, user_id: int) -> Dict[Subject, Dict[str, Any]]:
        """Get user's progress by subject"""
        progress_data = {}
        
        progress_records = self.db.query(Progress).filter(
            Progress.user_id == user_id
        ).all()
        
        for record in progress_records:
            progress_data[record.subject] = {
                'skill_level': record.skill_level,
                'accuracy_rate': record.accuracy_rate,
                'total_questions': record.total_questions,
                'correct_answers': record.correct_answers,
                'last_activity': record.last_activity,
                'weak_topics': record.extra_data.get('weak_topics', []) if record.extra_data else []
            }
        
        return progress_data
    
    def _get_recent_questions(
        self, 
        user_id: int, 
        hours: int
    ) -> List[int]:
        """Get IDs of questions answered recently"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        recent_results = self.db.query(QuizResult).filter(
            and_(
                QuizResult.user_id == user_id,
                QuizResult.started_at >= cutoff_time
            )
        ).all()
        
        question_ids = set()
        for result in recent_results:
            if result.answers:
                question_ids.update(result.answers.keys())
        
        return list(question_ids)
    
    def _calculate_target_difficulty(
        self, 
        config: QuizConfig,
        user_progress: Dict[Subject, Dict[str, Any]],
        subject: Subject
    ) -> Tuple[int, int]:
        """Calculate target difficulty range based on strategy and progress"""
        base_difficulty = 3  # Middle difficulty
        
        if subject in user_progress:
            skill_level = user_progress[subject]['skill_level']
            accuracy = user_progress[subject]['accuracy_rate'] or 0.5
            
            # Adjust based on performance
            if accuracy > 0.8:
                base_difficulty = min(5, base_difficulty + 1)
            elif accuracy < 0.5:
                base_difficulty = max(1, base_difficulty - 1)
            
            # Apply skill level
            base_difficulty = int(base_difficulty * (0.7 + skill_level * 0.6))
        
        # Apply strategy
        if config.difficulty_strategy == DifficultyStrategy.ADAPTIVE:
            return (max(1, base_difficulty - 1), min(5, base_difficulty + 1))
        elif config.difficulty_strategy == DifficultyStrategy.PROGRESSIVE:
            return (1, base_difficulty)
        elif config.difficulty_strategy == DifficultyStrategy.CHALLENGE:
            return (max(3, base_difficulty), 5)
        else:  # FIXED
            return (base_difficulty, base_difficulty)
    
    def _select_diagnostic_questions(
        self, 
        config: QuizConfig
    ) -> List[Question]:
        """Select questions for initial diagnostic assessment"""
        questions = []
        questions_per_subject = config.num_questions // len(config.subjects)
        
        for subject in config.subjects:
            # Get a range of difficulties
            for difficulty in range(1, 6):
                subject_questions = self.db.query(Question).filter(
                    and_(
                        Question.subject == subject,
                        Question.difficulty_level == difficulty,
                        Question.grade_level <= config.user_grade_level
                    )
                ).limit(questions_per_subject // 5).all()
                
                questions.extend(subject_questions)
        
        # Shuffle and trim to exact number
        random.shuffle(questions)
        return questions[:config.num_questions]
    
    def _select_weakness_questions(
        self, 
        user_id: int,
        config: QuizConfig,
        user_progress: Dict[Subject, Dict[str, Any]]
    ) -> List[Question]:
        """Select questions focusing on weak areas"""
        questions = []
        
        # Find weak topics
        weak_topics = []
        for subject, progress in user_progress.items():
            if progress['accuracy_rate'] and progress['accuracy_rate'] < 0.6:
                weak_topics.extend(progress.get('weak_topics', []))
        
        if weak_topics:
            # Focus on weak topics
            questions = self.db.query(Question).filter(
                and_(
                    Question.topic.in_(weak_topics),
                    Question.grade_level <= config.user_grade_level
                )
            ).limit(config.num_questions).all()
        
        # If not enough questions, add from low-accuracy subjects
        if len(questions) < config.num_questions:
            for subject, progress in sorted(
                user_progress.items(), 
                key=lambda x: x[1].get('accuracy_rate', 1)
            ):
                if progress['accuracy_rate'] and progress['accuracy_rate'] < 0.7:
                    diff_min, diff_max = self._calculate_target_difficulty(
                        config, user_progress, subject
                    )
                    
                    additional = self.db.query(Question).filter(
                        and_(
                            Question.subject == subject,
                            Question.difficulty_level.between(diff_min, diff_max),
                            Question.grade_level <= config.user_grade_level,
                            ~Question.id.in_([q.id for q in questions])
                        )
                    ).limit(config.num_questions - len(questions)).all()
                    
                    questions.extend(additional)
                    
                    if len(questions) >= config.num_questions:
                        break
        
        random.shuffle(questions)
        return questions[:config.num_questions]
    
    def _select_section_questions(
        self,
        config: QuizConfig,
        user_progress: Dict[Subject, Dict[str, Any]],
        recent_questions: List[int]
    ) -> List[Question]:
        """Select questions for a specific section"""
        questions = []
        subject = config.subjects[0]  # Should only have one subject for section focus
        
        diff_min, diff_max = self._calculate_target_difficulty(
            config, user_progress, subject
        )
        
        # Build query
        query = self.db.query(Question).filter(
            and_(
                Question.subject == subject,
                Question.difficulty_level.between(diff_min, diff_max),
                Question.grade_level <= config.user_grade_level
            )
        )
        
        # Exclude recent questions
        if recent_questions:
            query = query.filter(~Question.id.in_(recent_questions))
        
        # Filter by topics if specified
        if config.focus_topics:
            query = query.filter(Question.topic.in_(config.focus_topics))
        
        questions = query.limit(config.num_questions * 2).all()
        
        # Select diverse questions
        selected = self._select_diverse_questions(questions, config.num_questions)
        
        return selected
    
    def _select_full_test_questions(
        self,
        config: QuizConfig,
        recent_questions: List[int]
    ) -> List[Question]:
        """Select questions for a full ISEE test simulation"""
        questions = []
        
        for subject, requirements in self.isee_structure.items():
            # Get questions for this section
            section_questions = self.db.query(Question).filter(
                and_(
                    Question.subject == subject,
                    Question.grade_level <= config.user_grade_level
                )
            )
            
            if recent_questions:
                section_questions = section_questions.filter(
                    ~Question.id.in_(recent_questions)
                )
            
            # Get all available questions
            available = section_questions.all()
            
            # Select appropriate number
            if len(available) >= requirements['questions']:
                selected = random.sample(available, requirements['questions'])
            else:
                selected = available
                logger.warning(
                    f"Only {len(available)} questions available for {subject}, "
                    f"need {requirements['questions']}"
                )
            
            questions.extend(selected)
        
        return questions
    
    def _select_mixed_questions(
        self,
        config: QuizConfig,
        user_progress: Dict[Subject, Dict[str, Any]],
        recent_questions: List[int]
    ) -> List[Question]:
        """Select a mix of questions from all subjects"""
        questions = []
        questions_per_subject = config.num_questions // len(config.subjects)
        remainder = config.num_questions % len(config.subjects)
        
        for i, subject in enumerate(config.subjects):
            # Add extra question to first subjects if there's a remainder
            subject_count = questions_per_subject + (1 if i < remainder else 0)
            
            diff_min, diff_max = self._calculate_target_difficulty(
                config, user_progress, subject
            )
            
            subject_questions = self.db.query(Question).filter(
                and_(
                    Question.subject == subject,
                    Question.difficulty_level.between(diff_min, diff_max),
                    Question.grade_level <= config.user_grade_level
                )
            )
            
            if recent_questions:
                subject_questions = subject_questions.filter(
                    ~Question.id.in_(recent_questions)
                )
            
            available = subject_questions.all()
            
            if len(available) >= subject_count:
                selected = random.sample(available, subject_count)
            else:
                selected = available
            
            questions.extend(selected)
        
        random.shuffle(questions)
        return questions[:config.num_questions]
    
    def _select_diverse_questions(
        self, 
        questions: List[Question], 
        count: int
    ) -> List[Question]:
        """Select diverse questions from a pool"""
        if len(questions) <= count:
            return questions
        
        # Group by topic
        by_topic = {}
        for q in questions:
            topic = q.topic or 'general'
            if topic not in by_topic:
                by_topic[topic] = []
            by_topic[topic].append(q)
        
        selected = []
        topics = list(by_topic.keys())
        
        # Round-robin selection from topics
        while len(selected) < count and any(by_topic.values()):
            for topic in topics:
                if by_topic[topic] and len(selected) < count:
                    q = by_topic[topic].pop(
                        random.randint(0, len(by_topic[topic]) - 1)
                    )
                    selected.append(q)
        
        return selected
    
    def _create_quiz(
        self, 
        user_id: int,
        config: QuizConfig,
        questions: List[Question]
    ) -> Quiz:
        """Create quiz in database"""
        # Calculate time limit
        if config.time_limit_minutes:
            time_limit = config.time_limit_minutes
        elif config.quiz_type == QuizType.TIMED_TEST:
            # Sum up section times
            time_limit = sum(
                self.isee_structure[s]['time_minutes'] 
                for s in config.subjects
            )
        else:
            # Estimate 1-2 minutes per question
            time_limit = len(questions) * 1.5
        
        # Create quiz
        quiz = Quiz(
            title=self._generate_quiz_title(config),
            description=self._generate_quiz_description(config, questions),
            subject=config.subjects[0] if len(config.subjects) == 1 else None,
            difficulty=self._calculate_overall_difficulty(questions),
            time_limit_minutes=int(time_limit),
            passing_score=0.7
        )
        
        # Add questions
        quiz.questions = questions
        
        self.db.add(quiz)
        self.db.commit()
        self.db.refresh(quiz)
        
        logger.info(
            f"Created quiz {quiz.id} with {len(questions)} questions "
            f"for user {user_id}"
        )
        
        return quiz
    
    def _generate_quiz_title(self, config: QuizConfig) -> str:
        """Generate descriptive quiz title"""
        if config.quiz_type == QuizType.DIAGNOSTIC:
            return "Diagnostic Assessment"
        elif config.quiz_type == QuizType.TIMED_TEST:
            return "Full ISEE Practice Test"
        elif config.quiz_type == QuizType.SECTION_FOCUS:
            subject_name = config.subjects[0].value.replace('_', ' ').title()
            return f"{subject_name} Practice"
        elif config.quiz_type == QuizType.WEAKNESS:
            return "Weakness Review Quiz"
        else:
            return f"Practice Quiz - {datetime.now().strftime('%Y-%m-%d')}"
    
    def _generate_quiz_description(
        self, 
        config: QuizConfig,
        questions: List[Question]
    ) -> str:
        """Generate quiz description"""
        subject_counts = {}
        for q in questions:
            subject = q.subject.value
            subject_counts[subject] = subject_counts.get(subject, 0) + 1
        
        parts = []
        for subject, count in subject_counts.items():
            parts.append(f"{count} {subject.replace('_', ' ')} questions")
        
        return f"This quiz contains {', '.join(parts)}."
    
    def _calculate_overall_difficulty(self, questions: List[Question]) -> str:
        """Calculate overall difficulty label"""
        if not questions:
            return "medium"
        
        avg_difficulty = sum(q.difficulty_level for q in questions) / len(questions)
        
        if avg_difficulty <= 2:
            return "easy"
        elif avg_difficulty <= 3.5:
            return "medium"
        else:
            return "hard"