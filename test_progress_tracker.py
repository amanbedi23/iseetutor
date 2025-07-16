#!/usr/bin/env python3
"""Test the progress tracking system"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from src.core.education import (
    AdaptiveQuizGenerator, 
    QuizType, 
    QuizConfig, 
    DifficultyStrategy,
    ProgressTracker
)
from src.database import SessionLocal, Subject, User, QuizResult, Quiz
import json
from datetime import datetime

def create_test_user(db):
    """Create a test user if needed"""
    user = db.query(User).filter(User.username == "progress_test_student").first()
    if not user:
        user = User(
            username="progress_test_student",
            email="progress@example.com",
            hashed_password="dummy",
            full_name="Progress Test Student",
            grade_level=5,
            age=10
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user

def simulate_quiz_completion(db, user_id, quiz_id, score_percentage):
    """Simulate completing a quiz with a given score"""
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        return None
    
    # Create mock answers
    answers = {}
    correct_count = 0
    
    for i, question in enumerate(quiz.questions):
        # Simulate correct/incorrect based on score percentage
        is_correct = (i / len(quiz.questions)) < (score_percentage / 100)
        
        if question.question_metadata and 'correct_answer' in question.question_metadata:
            correct_answer = question.question_metadata['correct_answer']
            user_answer = correct_answer if is_correct else 'A'  # Wrong answer
        else:
            user_answer = 'B'
            is_correct = False
        
        answers[str(question.id)] = {
            'user_answer': user_answer,
            'correct_answer': question.question_metadata.get('correct_answer', 'B'),
            'is_correct': is_correct,
            'time_spent': 60  # 1 minute per question
        }
        
        if is_correct:
            correct_count += 1
    
    # Create quiz result
    result = QuizResult(
        user_id=user_id,
        quiz_id=quiz_id,
        started_at=datetime.utcnow(),
        completed_at=datetime.utcnow(),
        score=score_percentage / 100,
        total_questions=len(quiz.questions),
        correct_answers=correct_count,
        time_taken_minutes=len(quiz.questions),
        answers=answers,
        feedback={
            'correct_answers': [int(qid) for qid, a in answers.items() if a['is_correct']],
            'incorrect_answers': [int(qid) for qid, a in answers.items() if not a['is_correct']]
        }
    )
    
    db.add(result)
    db.commit()
    db.refresh(result)
    
    return result

def main():
    db = SessionLocal()
    generator = AdaptiveQuizGenerator(db)
    tracker = ProgressTracker(db)
    
    # Create test user
    user = create_test_user(db)
    print(f"Using test user: {user.username} (ID: {user.id})")
    
    print("\n" + "="*60)
    print("TESTING PROGRESS TRACKING SYSTEM")
    print("="*60)
    
    # Step 1: Generate and complete several quizzes
    print("\n1. Generating and simulating quiz completions...")
    
    quiz_scenarios = [
        # (quiz_type, subjects, score_percentage)
        (QuizType.DIAGNOSTIC, [Subject.VERBAL_REASONING, Subject.MATH, Subject.READING], 65),
        (QuizType.SECTION_FOCUS, [Subject.VERBAL_REASONING], 75),
        (QuizType.SECTION_FOCUS, [Subject.MATH], 55),
        (QuizType.SECTION_FOCUS, [Subject.READING], 80),
        (QuizType.MIXED, [Subject.VERBAL_REASONING, Subject.MATH], 70),
        (QuizType.SECTION_FOCUS, [Subject.MATH], 60),  # Improving math
        (QuizType.SECTION_FOCUS, [Subject.MATH], 65),  # More improvement
    ]
    
    for i, (quiz_type, subjects, score) in enumerate(quiz_scenarios, 1):
        print(f"\n   Quiz {i}: {quiz_type.value}")
        
        # Generate quiz
        config = QuizConfig(
            quiz_type=quiz_type,
            num_questions=10,
            subjects=subjects,
            difficulty_strategy=DifficultyStrategy.ADAPTIVE
        )
        
        quiz = generator.generate_quiz(user.id, config)
        if quiz:
            print(f"   - Generated: {quiz.title}")
            
            # Simulate completion
            result = simulate_quiz_completion(db, user.id, quiz.id, score)
            print(f"   - Completed with score: {score}%")
            
            # Update progress
            progress_update = tracker.update_quiz_progress(user.id, result.id)
            print(f"   - Progress updated: {len(progress_update.get('updated_subjects', []))} subjects")
    
    # Step 2: Get mastery report
    print("\n" + "-"*60)
    print("2. MASTERY REPORT")
    print("-"*60)
    
    mastery_report = tracker.get_mastery_report(user.id)
    
    print(f"\nStudent: {mastery_report['user']['name']}")
    print(f"Grade Level: {mastery_report['user']['grade_level']}")
    print(f"Overall Mastery: {mastery_report['overall_mastery']:.1f}%")
    print(f"Total Questions Attempted: {mastery_report['total_questions_attempted']}")
    print(f"Total Time Spent: {mastery_report['total_time_spent_hours']:.1f} hours")
    print(f"Current Streak: {mastery_report['current_streak']['current']} days")
    
    print("\nSubject Mastery:")
    for subject, data in mastery_report['subject_mastery'].items():
        print(f"  {subject}:")
        print(f"    - Mastery: {data['mastery_level']:.1f}% ({data['mastery_category']})")
        print(f"    - Accuracy: {data['accuracy']:.1f}%")
        print(f"    - Questions: {data['questions_attempted']}")
    
    # Step 3: Identify weaknesses
    print("\n" + "-"*60)
    print("3. WEAKNESSES")
    print("-"*60)
    
    weaknesses = tracker.identify_weaknesses(user.id)
    if weaknesses:
        for weakness in weaknesses:
            print(f"\n  {weakness['subject']}:")
            print(f"    - Mastery: {weakness['mastery_level']:.1f}%")
            print(f"    - Accuracy: {weakness['accuracy']:.1f}%")
            print(f"    - Questions Attempted: {weakness['questions_attempted']}")
    else:
        print("\n  No significant weaknesses identified!")
    
    # Step 4: Identify strengths
    print("\n" + "-"*60)
    print("4. STRENGTHS")
    print("-"*60)
    
    strengths = tracker.identify_strengths(user.id, threshold=75)
    if strengths:
        for strength in strengths:
            print(f"\n  {strength['subject']}:")
            print(f"    - Mastery: {strength['mastery_level']:.1f}%")
            print(f"    - Accuracy: {strength['accuracy']:.1f}%")
    else:
        print("\n  No strong areas identified yet (keep practicing!)")
    
    # Step 5: Progress summary
    print("\n" + "-"*60)
    print("5. 7-DAY PROGRESS SUMMARY")
    print("-"*60)
    
    summary = tracker.get_progress_summary(user.id, days=7)
    print(f"\nLast 7 days:")
    print(f"  - Quizzes Completed: {summary['total_quizzes']}")
    print(f"  - Questions Answered: {summary['total_questions']}")
    print(f"  - Overall Accuracy: {summary['accuracy']:.1f}%")
    print(f"  - Average Score: {summary['average_score']:.1f}%")
    print(f"  - Time Spent: {summary['time_spent_hours']:.1f} hours")
    
    if summary['subject_performance']:
        print("\n  Subject Performance:")
        for subject, perf in summary['subject_performance'].items():
            print(f"    {subject}: {perf['accuracy']:.1f}% ({perf['questions']} questions)")
    
    # Step 6: Recommendations
    print("\n" + "-"*60)
    print("6. RECOMMENDED FOCUS AREAS")
    print("-"*60)
    
    if 'recommended_focus' in mastery_report:
        for rec in mastery_report['recommended_focus']:
            print(f"\n  {rec['subject']}:")
            print(f"    - Reason: {rec['reason']}")
            print(f"    - Suggestion: {rec['suggested_practice']}")
    
    print("\n" + "="*60)
    print("Progress tracking test completed!")
    print("="*60)
    
    db.close()

if __name__ == "__main__":
    main()