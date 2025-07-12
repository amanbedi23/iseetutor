#!/usr/bin/env python3
"""Test database models and operations"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import SessionLocal, User, Question, Quiz, Subject, QuestionType
from src.database.utils import (
    create_user, get_user_by_username, update_user_progress,
    get_questions_by_criteria, get_user_statistics
)

def test_database_connection():
    """Test database connection"""
    print("Testing Database Connection")
    print("-" * 50)
    
    try:
        db = SessionLocal()
        # Test query
        from sqlalchemy import text
        result = db.execute(text("SELECT 1"))
        print("✅ Database connection successful")
        db.close()
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_user_operations():
    """Test user CRUD operations"""
    print("\nTesting User Operations")
    print("-" * 50)
    
    db = SessionLocal()
    
    try:
        # Create user
        user = create_user(
            db,
            username="test_student",
            email="test@example.com",
            full_name="Test Student",
            grade_level=6,
            age=11
        )
        print(f"✅ Created user: {user.username} (ID: {user.id})")
        
        # Retrieve user
        retrieved = get_user_by_username(db, "test_student")
        if retrieved:
            print(f"✅ Retrieved user: {retrieved.full_name}")
        
        # Update progress
        progress = update_user_progress(
            db,
            user_id=user.id,
            subject=Subject.MATH,
            topic="fractions",
            correct=8,
            total=10,
            time_spent=15.5
        )
        print(f"✅ Updated progress: {progress.accuracy_rate:.2%} accuracy")
        
        # Get statistics
        stats = get_user_statistics(db, user.id)
        print(f"✅ User statistics: {stats['overall']['total_questions']} questions attempted")
        
        # Cleanup
        db.delete(progress)
        db.delete(user)
        db.commit()
        print("✅ Cleanup completed")
        
        return True
        
    except Exception as e:
        print(f"❌ User operations failed: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def test_question_operations():
    """Test question operations"""
    print("\nTesting Question Operations")
    print("-" * 50)
    
    db = SessionLocal()
    
    try:
        # Create sample question
        question = Question(
            question_text="What is 2 + 2?",
            question_type=QuestionType.MULTIPLE_CHOICE,
            subject=Subject.MATH,
            topic="addition",
            difficulty="easy",
            grade_level=1,
            choices=["2", "3", "4", "5"],
            correct_answer="4",
            explanation="2 + 2 equals 4"
        )
        db.add(question)
        db.commit()
        print(f"✅ Created question: {question.question_text}")
        
        # Query questions
        questions = get_questions_by_criteria(
            db,
            subject=Subject.MATH,
            difficulty="easy"
        )
        print(f"✅ Found {len(questions)} math questions")
        
        # Cleanup
        db.delete(question)
        db.commit()
        print("✅ Cleanup completed")
        
        return True
        
    except Exception as e:
        print(f"❌ Question operations failed: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def test_quiz_operations():
    """Test quiz operations"""
    print("\nTesting Quiz Operations")
    print("-" * 50)
    
    db = SessionLocal()
    
    try:
        # Create quiz
        quiz = Quiz(
            title="Math Basics Quiz",
            description="Test your basic math skills",
            subject=Subject.MATH,
            difficulty="easy",
            time_limit_minutes=30
        )
        db.add(quiz)
        db.commit()
        print(f"✅ Created quiz: {quiz.title}")
        
        # Create and associate questions
        for i in range(3):
            q = Question(
                question_text=f"Question {i+1}",
                question_type=QuestionType.MULTIPLE_CHOICE,
                subject=Subject.MATH,
                topic="basics",
                difficulty="easy",
                choices=["A", "B", "C", "D"],
                correct_answer="A"
            )
            db.add(q)
            quiz.questions.append(q)
        
        db.commit()
        print(f"✅ Added {len(quiz.questions)} questions to quiz")
        
        # Cleanup
        for q in quiz.questions:
            db.delete(q)
        db.delete(quiz)
        db.commit()
        print("✅ Cleanup completed")
        
        return True
        
    except Exception as e:
        print(f"❌ Quiz operations failed: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    print("Database Test Suite")
    print("=" * 50)
    
    # Test connection first
    if test_database_connection():
        # Run tests
        test_user_operations()
        test_question_operations()
        test_quiz_operations()
    
    print("\n" + "=" * 50)
    print("Database tests complete!")