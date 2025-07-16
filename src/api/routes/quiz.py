"""
Quiz API routes for generating and managing quizzes
"""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.database import get_db, User, Quiz, QuizResult, Subject, Question
from src.core.education import (
    AdaptiveQuizGenerator, 
    QuizType, 
    DifficultyStrategy,
    QuizConfig,
    ProgressTracker,
    KnowledgeRetrieval
)
from src.core.security.auth import get_current_user

router = APIRouter(prefix="/api/quiz", tags=["quiz"])

# Pydantic models
class QuizGenerateRequest(BaseModel):
    """Request model for quiz generation"""
    quiz_type: str = Field(
        default="mixed",
        description="Type of quiz: diagnostic, section_focus, mixed, weakness, timed_test, review"
    )
    num_questions: int = Field(
        default=10,
        ge=1,
        le=127,
        description="Number of questions in the quiz"
    )
    subjects: List[str] = Field(
        default=["verbal_reasoning"],
        description="List of subjects to include"
    )
    difficulty_strategy: str = Field(
        default="adaptive",
        description="Difficulty strategy: adaptive, progressive, fixed, challenge"
    )
    time_limit_minutes: Optional[int] = Field(
        default=None,
        description="Time limit in minutes (optional)"
    )
    focus_topics: Optional[List[str]] = Field(
        default=None,
        description="Specific topics to focus on"
    )

class QuestionResponse(BaseModel):
    """Response model for a question"""
    id: int
    question_text: str
    choices: List[str]
    subject: str
    topic: Optional[str]
    difficulty_level: int
    time_limit: int
    points: int

class QuizResponse(BaseModel):
    """Response model for a generated quiz"""
    id: int
    title: str
    description: str
    time_limit_minutes: int
    passing_score: float
    questions: List[QuestionResponse]
    created_at: datetime

class QuizSubmitAnswer(BaseModel):
    """Model for submitting an answer"""
    question_id: int
    answer: str
    time_spent_seconds: Optional[int] = None

class QuizSubmitRequest(BaseModel):
    """Request model for submitting quiz answers"""
    quiz_id: int
    answers: List[QuizSubmitAnswer]
    time_taken_minutes: float

class QuizResultResponse(BaseModel):
    """Response model for quiz results"""
    id: int
    quiz_id: int
    score: float
    total_questions: int
    correct_answers: int
    time_taken_minutes: float
    passed: bool
    feedback: dict
    completed_at: datetime

# Helper functions
def map_quiz_type(quiz_type_str: str) -> QuizType:
    """Map string to QuizType enum"""
    mapping = {
        'diagnostic': QuizType.DIAGNOSTIC,
        'section_focus': QuizType.SECTION_FOCUS,
        'mixed': QuizType.MIXED,
        'weakness': QuizType.WEAKNESS,
        'timed_test': QuizType.TIMED_TEST,
        'review': QuizType.REVIEW,
        'practice': QuizType.PRACTICE
    }
    return mapping.get(quiz_type_str.lower(), QuizType.MIXED)

def map_difficulty_strategy(strategy_str: str) -> DifficultyStrategy:
    """Map string to DifficultyStrategy enum"""
    mapping = {
        'adaptive': DifficultyStrategy.ADAPTIVE,
        'progressive': DifficultyStrategy.PROGRESSIVE,
        'fixed': DifficultyStrategy.FIXED,
        'challenge': DifficultyStrategy.CHALLENGE
    }
    return mapping.get(strategy_str.lower(), DifficultyStrategy.ADAPTIVE)

def map_subject(subject_str: str) -> Subject:
    """Map string to Subject enum"""
    mapping = {
        'verbal_reasoning': Subject.VERBAL_REASONING,
        'quantitative_reasoning': Subject.QUANTITATIVE_REASONING,
        'reading': Subject.READING,
        'reading_comprehension': Subject.READING,
        'math': Subject.MATH,
        'mathematics': Subject.MATH,
        'mathematics_achievement': Subject.MATH,
        'general': Subject.GENERAL
    }
    return mapping.get(subject_str.lower(), Subject.GENERAL)

# API Endpoints
@router.post("/generate", response_model=QuizResponse)
async def generate_quiz(
    request: QuizGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate a personalized quiz for the current user"""
    # Map request to config
    config = QuizConfig(
        quiz_type=map_quiz_type(request.quiz_type),
        num_questions=request.num_questions,
        subjects=[map_subject(s) for s in request.subjects],
        difficulty_strategy=map_difficulty_strategy(request.difficulty_strategy),
        time_limit_minutes=request.time_limit_minutes,
        user_grade_level=current_user.grade_level or 5,
        focus_topics=request.focus_topics
    )
    
    # Generate quiz
    generator = AdaptiveQuizGenerator(db)
    quiz = generator.generate_quiz(current_user.id, config)
    
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to generate quiz with the specified parameters"
        )
    
    # Format response
    questions = []
    for q in quiz.questions:
        choices = []
        if q.question_metadata and 'choices' in q.question_metadata:
            choices = q.question_metadata['choices']
        
        questions.append(QuestionResponse(
            id=q.id,
            question_text=q.question_text,
            choices=choices,
            subject=q.subject.value,
            topic=q.topic,
            difficulty_level=q.difficulty_level,
            time_limit=q.time_limit,
            points=q.points
        ))
    
    return QuizResponse(
        id=quiz.id,
        title=quiz.title,
        description=quiz.description or "",
        time_limit_minutes=quiz.time_limit_minutes,
        passing_score=quiz.passing_score,
        questions=questions,
        created_at=quiz.created_at
    )

@router.get("/available-subjects", response_model=List[str])
async def get_available_subjects(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get list of subjects with available questions"""
    subjects = db.query(Question.subject).distinct().all()
    return [s[0].value for s in subjects]

@router.get("/quiz/{quiz_id}", response_model=QuizResponse)
async def get_quiz(
    quiz_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific quiz by ID"""
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found"
        )
    
    # Check if user has access (for now, any logged-in user can access any quiz)
    # In production, you'd check if the user has taken this quiz or has permission
    
    # Format response
    questions = []
    for q in quiz.questions:
        choices = []
        if q.question_metadata and 'choices' in q.question_metadata:
            choices = q.question_metadata['choices']
        
        questions.append(QuestionResponse(
            id=q.id,
            question_text=q.question_text,
            choices=choices,
            subject=q.subject.value,
            topic=q.topic,
            difficulty_level=q.difficulty_level,
            time_limit=q.time_limit,
            points=q.points
        ))
    
    return QuizResponse(
        id=quiz.id,
        title=quiz.title,
        description=quiz.description or "",
        time_limit_minutes=quiz.time_limit_minutes,
        passing_score=quiz.passing_score,
        questions=questions,
        created_at=quiz.created_at
    )

@router.post("/submit", response_model=QuizResultResponse)
async def submit_quiz(
    submission: QuizSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit quiz answers and get results"""
    # Get the quiz
    quiz = db.query(Quiz).filter(Quiz.id == submission.quiz_id).first()
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found"
        )
    
    # Process answers
    correct_count = 0
    total_points = 0
    earned_points = 0
    answers_dict = {}
    feedback = {
        'correct_answers': [],
        'incorrect_answers': [],
        'by_subject': {}
    }
    
    # Create lookup for submitted answers
    answer_lookup = {a.question_id: a.answer for a in submission.answers}
    
    for question in quiz.questions:
        total_points += question.points
        
        if question.id in answer_lookup:
            user_answer = answer_lookup[question.id]
            correct_answer = None
            
            if question.question_metadata and 'correct_answer' in question.question_metadata:
                correct_answer = question.question_metadata['correct_answer']
            
            answers_dict[str(question.id)] = {
                'user_answer': user_answer,
                'correct_answer': correct_answer,
                'is_correct': user_answer == correct_answer if correct_answer else None
            }
            
            if user_answer == correct_answer:
                correct_count += 1
                earned_points += question.points
                feedback['correct_answers'].append(question.id)
            else:
                feedback['incorrect_answers'].append(question.id)
            
            # Track by subject
            subject = question.subject.value
            if subject not in feedback['by_subject']:
                feedback['by_subject'][subject] = {'correct': 0, 'total': 0}
            
            feedback['by_subject'][subject]['total'] += 1
            if user_answer == correct_answer:
                feedback['by_subject'][subject]['correct'] += 1
    
    # Calculate score
    score = (earned_points / total_points) if total_points > 0 else 0
    passed = score >= quiz.passing_score
    
    # Create quiz result
    result = QuizResult(
        user_id=current_user.id,
        quiz_id=quiz.id,
        started_at=datetime.utcnow(),  # Should track actual start time
        completed_at=datetime.utcnow(),
        score=score,
        total_questions=len(quiz.questions),
        correct_answers=correct_count,
        time_taken_minutes=submission.time_taken_minutes,
        answers=answers_dict,
        feedback=feedback
    )
    
    db.add(result)
    db.commit()
    db.refresh(result)
    
    # Update progress tracking
    progress_tracker = ProgressTracker(db)
    progress_update = progress_tracker.update_quiz_progress(current_user.id, result.id)
    
    # Add progress info to feedback
    feedback['progress_update'] = progress_update
    
    return QuizResultResponse(
        id=result.id,
        quiz_id=result.quiz_id,
        score=result.score,
        total_questions=result.total_questions,
        correct_answers=result.correct_answers,
        time_taken_minutes=result.time_taken_minutes,
        passed=passed,
        feedback=feedback,
        completed_at=result.completed_at
    )

@router.get("/history", response_model=List[QuizResultResponse])
async def get_quiz_history(
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's quiz history"""
    results = db.query(QuizResult).filter(
        QuizResult.user_id == current_user.id
    ).order_by(QuizResult.completed_at.desc()).limit(limit).all()
    
    history = []
    for result in results:
        quiz = db.query(Quiz).filter(Quiz.id == result.quiz_id).first()
        passed = result.score >= quiz.passing_score if quiz else False
        
        history.append(QuizResultResponse(
            id=result.id,
            quiz_id=result.quiz_id,
            score=result.score,
            total_questions=result.total_questions,
            correct_answers=result.correct_answers,
            time_taken_minutes=result.time_taken_minutes,
            passed=passed,
            feedback=result.feedback or {},
            completed_at=result.completed_at
        ))
    
    return history

# Progress tracking endpoints
@router.get("/progress/mastery", response_model=dict)
async def get_mastery_report(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive mastery report for current user"""
    tracker = ProgressTracker(db)
    return tracker.get_mastery_report(current_user.id)

@router.get("/progress/summary")
async def get_progress_summary(
    days: int = 7,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get progress summary for the last N days"""
    tracker = ProgressTracker(db)
    return tracker.get_progress_summary(current_user.id, days)

@router.get("/progress/weaknesses", response_model=List[dict])
async def get_weaknesses(
    threshold: float = 70,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get areas where student needs improvement"""
    tracker = ProgressTracker(db)
    return tracker.identify_weaknesses(current_user.id, threshold)

@router.get("/progress/strengths", response_model=List[dict])
async def get_strengths(
    threshold: float = 85,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get areas where student excels"""
    tracker = ProgressTracker(db)
    return tracker.identify_strengths(current_user.id, threshold)

# Knowledge search endpoints
class KnowledgeSearchRequest(BaseModel):
    """Request model for knowledge search"""
    query: str = Field(
        description="Search query text"
    )
    search_type: str = Field(
        default="content",
        description="Type of search: content, questions, concepts"
    )
    subject_filter: Optional[str] = Field(
        default=None,
        description="Filter by subject"
    )
    k: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Number of results to return"
    )

class ContentSearchResult(BaseModel):
    """Result model for content search"""
    text: str
    section: str
    page: Optional[int]
    relevance_score: float
    metadata: dict

class QuestionSearchResult(BaseModel):
    """Result model for question search"""
    question: str
    subject: str
    topic: Optional[str]
    difficulty: str
    choices: List[str]
    correct_answer: Optional[str]
    explanation: Optional[str]
    relevance_score: float

class ConceptSearchResult(BaseModel):
    """Result model for concept search"""
    concept: str
    related_questions: List[int]
    content_references: List[str]
    relevance_score: float

@router.post("/knowledge/search")
async def search_knowledge(
    request: KnowledgeSearchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search the knowledge base for relevant content"""
    knowledge = KnowledgeRetrieval()
    
    if request.search_type == "content":
        results = knowledge.retrieve_similar_content(
            request.query,
            subject_filter=request.subject_filter,
            k=request.k
        )
        
        return [
            ContentSearchResult(
                text=r['text'],
                section=r.get('section', 'Unknown'),
                page=r.get('page'),
                relevance_score=r.get('distance', 0),
                metadata=r.get('metadata', {})
            )
            for r in results
        ]
    
    elif request.search_type == "questions":
        results = knowledge.retrieve_similar_questions(
            request.query,
            subject_filter=request.subject_filter,
            k=request.k
        )
        
        return [
            QuestionSearchResult(
                question=r['question'],
                subject=r.get('subject', 'Unknown'),
                topic=r.get('topic'),
                difficulty=r.get('difficulty', 'Unknown'),
                choices=r.get('choices', []),
                correct_answer=r.get('correct_answer'),
                explanation=r.get('explanation'),
                relevance_score=r.get('distance', 0)
            )
            for r in results
        ]
    
    elif request.search_type == "concepts":
        # Search by concept
        results = knowledge.search_by_concept(
            request.query,
            k=request.k
        )
        
        return [
            ConceptSearchResult(
                concept=r['concept'],
                related_questions=r.get('question_ids', []),
                content_references=r.get('content_refs', []),
                relevance_score=r.get('distance', 0)
            )
            for r in results
        ]
    
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid search type: {request.search_type}"
        )

@router.get("/knowledge/quiz-context/{question_id}")
async def get_quiz_context(
    question_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get educational context for a specific quiz question"""
    # Verify question exists
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )
    
    knowledge = KnowledgeRetrieval()
    context = knowledge.get_quiz_explanation_context(
        question.question_text,
        subject=question.subject.value
    )
    
    return {
        "question_id": question_id,
        "educational_context": context.get('content', []),
        "similar_questions": context.get('similar_questions', []),
        "concepts": context.get('concepts', [])
    }

@router.get("/knowledge/subject-topics/{subject}")
async def get_subject_topics(
    subject: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all topics available for a subject"""
    knowledge = KnowledgeRetrieval()
    
    # Map subject string to Subject enum
    subject_enum = map_subject(subject)
    
    # Get questions for this subject
    questions = knowledge.retrieve_questions_by_subject(
        subject=subject_enum.value,
        k=100  # Get many to extract topics
    )
    
    # Extract unique topics
    topics = set()
    for q in questions:
        if q.get('topic'):
            topics.add(q['topic'])
    
    return {
        "subject": subject,
        "topics": sorted(list(topics)),
        "total_questions": len(questions)
    }