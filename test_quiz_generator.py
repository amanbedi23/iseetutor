#!/usr/bin/env python3
"""Test the quiz generator"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from src.core.education import AdaptiveQuizGenerator, QuizType, QuizConfig, DifficultyStrategy
from src.database import SessionLocal, Subject, User
import json

def create_test_user(db):
    """Create a test user if needed"""
    user = db.query(User).filter(User.username == "test_student").first()
    if not user:
        user = User(
            username="test_student",
            email="test@example.com",
            hashed_password="dummy",
            full_name="Test Student",
            grade_level=5,
            age=10
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user

def main():
    db = SessionLocal()
    generator = AdaptiveQuizGenerator(db)
    
    # Create test user
    user = create_test_user(db)
    print(f"Using test user: {user.username} (ID: {user.id})")
    
    # Test different quiz types
    quiz_configs = [
        # 1. Diagnostic quiz
        QuizConfig(
            quiz_type=QuizType.DIAGNOSTIC,
            num_questions=20,
            subjects=[Subject.VERBAL_REASONING, Subject.MATH, Subject.READING, Subject.QUANTITATIVE_REASONING],
            difficulty_strategy=DifficultyStrategy.PROGRESSIVE
        ),
        
        # 2. Verbal reasoning practice
        QuizConfig(
            quiz_type=QuizType.SECTION_FOCUS,
            num_questions=10,
            subjects=[Subject.VERBAL_REASONING],
            difficulty_strategy=DifficultyStrategy.ADAPTIVE
        ),
        
        # 3. Math practice
        QuizConfig(
            quiz_type=QuizType.SECTION_FOCUS,
            num_questions=10,
            subjects=[Subject.MATH],
            difficulty_strategy=DifficultyStrategy.ADAPTIVE
        ),
        
        # 4. Mixed practice
        QuizConfig(
            quiz_type=QuizType.MIXED,
            num_questions=15,
            subjects=[Subject.VERBAL_REASONING, Subject.MATH, Subject.READING],
            difficulty_strategy=DifficultyStrategy.ADAPTIVE
        )
    ]
    
    print("\n" + "="*60)
    print("TESTING QUIZ GENERATOR")
    print("="*60)
    
    for i, config in enumerate(quiz_configs, 1):
        print(f"\n--- Test {i}: {config.quiz_type.value} ---")
        
        quiz = generator.generate_quiz(user.id, config)
        
        if quiz:
            print(f"✓ Generated Quiz: {quiz.title}")
            print(f"  ID: {quiz.id}")
            print(f"  Questions: {len(quiz.questions)}")
            print(f"  Time Limit: {quiz.time_limit_minutes} minutes")
            print(f"  Difficulty: {quiz.difficulty}")
            print(f"  Description: {quiz.description}")
            
            # Show question breakdown
            subject_counts = {}
            difficulty_counts = {}
            
            for q in quiz.questions:
                # Count by subject
                subject = q.subject.value
                subject_counts[subject] = subject_counts.get(subject, 0) + 1
                
                # Count by difficulty
                diff = q.difficulty_level
                difficulty_counts[diff] = difficulty_counts.get(diff, 0) + 1
            
            print("\n  Question Breakdown:")
            print("  By Subject:")
            for subject, count in sorted(subject_counts.items()):
                print(f"    - {subject}: {count}")
            
            print("  By Difficulty:")
            for diff in sorted(difficulty_counts.keys()):
                print(f"    - Level {diff}: {difficulty_counts[diff]}")
            
            # Show sample questions
            print("\n  Sample Questions:")
            for j, q in enumerate(quiz.questions[:3], 1):
                print(f"    {j}. {q.question_text[:60]}...")
                if q.question_metadata and 'choices' in q.question_metadata:
                    choices = q.question_metadata['choices']
                    print(f"       ({len(choices)} choices)")
        else:
            print("✗ Failed to generate quiz")
    
    # Show overall statistics
    print("\n" + "="*60)
    print("DATABASE STATISTICS")
    print("="*60)
    
    from src.database import Question
    total_questions = db.query(Question).count()
    
    print(f"Total Questions Available: {total_questions}")
    print("\nQuestions by Subject:")
    
    for subject in [Subject.VERBAL_REASONING, Subject.QUANTITATIVE_REASONING, 
                   Subject.READING, Subject.MATH]:
        count = db.query(Question).filter(Question.subject == subject).count()
        print(f"  {subject.value}: {count}")
    
    db.close()

if __name__ == "__main__":
    main()