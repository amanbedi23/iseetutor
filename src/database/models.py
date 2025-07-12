"""
Database models for ISEE Tutor
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column, Integer, String, DateTime, Float, Boolean,
    Text, JSON, ForeignKey, Table, Enum
)
from sqlalchemy.orm import relationship
import enum

from .base import Base

# Association table for many-to-many relationship between Quiz and Question
quiz_questions = Table(
    'quiz_questions',
    Base.metadata,
    Column('quiz_id', Integer, ForeignKey('quizzes.id'), primary_key=True),
    Column('question_id', Integer, ForeignKey('questions.id'), primary_key=True)
)

class UserRole(enum.Enum):
    """User roles"""
    STUDENT = "student"
    PARENT = "parent"
    TEACHER = "teacher"
    ADMIN = "admin"

class QuestionType(enum.Enum):
    """Question types"""
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    FILL_BLANK = "fill_blank"
    SHORT_ANSWER = "short_answer"
    ESSAY = "essay"

class Subject(enum.Enum):
    """Academic subjects"""
    MATH = "math"
    READING = "reading"
    VOCABULARY = "vocabulary"
    VERBAL_REASONING = "verbal_reasoning"
    QUANTITATIVE_REASONING = "quantitative_reasoning"
    GENERAL = "general"

class User(Base):
    """User model"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True)
    hashed_password = Column(String(200), nullable=False)
    full_name = Column(String(100))
    role = Column(Enum(UserRole), default=UserRole.STUDENT)
    grade_level = Column(Integer)
    age = Column(Integer)
    parent_email = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    metadata = Column(JSON, default=dict)
    
    # Relationships
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    progress = relationship("Progress", back_populates="user", cascade="all, delete-orphan")
    quiz_results = relationship("QuizResult", back_populates="user", cascade="all, delete-orphan")
    audio_logs = relationship("AudioLog", back_populates="user", cascade="all, delete-orphan")

class Session(Base):
    """Learning session model"""
    __tablename__ = 'sessions'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    session_id = Column(String(100), unique=True, index=True, nullable=False)
    mode = Column(String(20), default='tutor')  # tutor or companion
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime)
    duration_minutes = Column(Float)
    activities = Column(JSON)  # Store activity log
    
    # Relationships
    user = relationship("User", back_populates="sessions")

class Progress(Base):
    """User progress tracking"""
    __tablename__ = 'progress'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    subject = Column(Enum(Subject), nullable=False)
    topic = Column(String(100))
    skill_level = Column(Float, default=0.5)  # 0-1 scale
    accuracy_rate = Column(Float)
    total_questions = Column(Integer, default=0)
    correct_answers = Column(Integer, default=0)
    time_spent_minutes = Column(Float, default=0)
    last_activity = Column(DateTime, default=datetime.utcnow)
    extra_data = Column(JSON)  # Additional tracking data
    
    # Relationships
    user = relationship("User", back_populates="progress")

class Question(Base):
    """Question bank"""
    __tablename__ = 'questions'
    
    id = Column(Integer, primary_key=True, index=True)
    question_text = Column(Text, nullable=False)
    question_type = Column(Enum(QuestionType), nullable=False)
    subject = Column(Enum(Subject), nullable=False)
    topic = Column(String(100))
    difficulty = Column(String(20))  # easy, medium, hard
    grade_level = Column(Integer)
    choices = Column(JSON)  # For multiple choice
    correct_answer = Column(Text)
    explanation = Column(Text)
    points = Column(Integer, default=1)
    tags = Column(JSON)  # List of tags
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    quizzes = relationship("Quiz", secondary=quiz_questions, back_populates="questions")

class Quiz(Base):
    """Quiz model"""
    __tablename__ = 'quizzes'
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    subject = Column(Enum(Subject))
    difficulty = Column(String(20))
    time_limit_minutes = Column(Integer)
    passing_score = Column(Float, default=0.7)  # Percentage
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    questions = relationship("Question", secondary=quiz_questions, back_populates="quizzes")
    results = relationship("QuizResult", back_populates="quiz", cascade="all, delete-orphan")

class QuizResult(Base):
    """Quiz results and attempts"""
    __tablename__ = 'quiz_results'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    quiz_id = Column(Integer, ForeignKey('quizzes.id'), nullable=False)
    session_id = Column(String(100))
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    score = Column(Float)  # Percentage
    total_questions = Column(Integer)
    correct_answers = Column(Integer)
    time_taken_minutes = Column(Float)
    answers = Column(JSON)  # Store user answers
    feedback = Column(JSON)  # AI-generated feedback
    
    # Relationships
    user = relationship("User", back_populates="quiz_results")
    quiz = relationship("Quiz", back_populates="results")

class Content(Base):
    """Educational content storage"""
    __tablename__ = 'content'
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    content_type = Column(String(50))  # pdf, video, text, etc.
    file_path = Column(String(500))
    subject = Column(Enum(Subject))
    grade_level = Column(Integer)
    topics = Column(JSON)  # List of topics covered
    extra_data = Column(JSON)  # Extracted metadata
    processed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class AudioLog(Base):
    """Audio interaction logging"""
    __tablename__ = 'audio_logs'
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    timestamp = Column(DateTime, default=datetime.utcnow)
    audio_file_path = Column(String(500))
    transcription = Column(Text)
    wake_word_detected = Column(Boolean, default=False)
    command_type = Column(String(50))
    response = Column(Text)
    processing_time_ms = Column(Float)
    extra_data = Column(JSON)