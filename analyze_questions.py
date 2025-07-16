#!/usr/bin/env python3
"""Analyze ISEE questions by section and topic"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from src.database import SessionLocal, Question, Subject
from sqlalchemy import func
import json

def main():
    db = SessionLocal()
    
    print("\n" + "="*60)
    print("ISEE QUESTION ANALYSIS")
    print("="*60)
    
    # Total questions
    total = db.query(Question).count()
    print(f"\nTotal Questions: {total}")
    
    # Questions by subject
    print("\n--- Questions by Section ---")
    subject_stats = db.query(
        Question.subject, 
        func.count(Question.id)
    ).group_by(Question.subject).order_by(func.count(Question.id).desc()).all()
    
    for subject, count in subject_stats:
        percentage = (count / total * 100) if total > 0 else 0
        print(f"{str(subject).replace('Subject.', ''):25} {count:4d} questions ({percentage:5.1f}%)")
    
    # Questions by difficulty
    print("\n--- Questions by Difficulty Level ---")
    difficulty_stats = db.query(
        Question.difficulty_level,
        func.count(Question.id)
    ).group_by(Question.difficulty_level).order_by(Question.difficulty_level).all()
    
    for difficulty, count in difficulty_stats:
        print(f"Level {difficulty}: {count} questions")
    
    # Questions by type
    print("\n--- Questions by Type ---")
    type_stats = db.query(
        Question.question_type,
        func.count(Question.id)
    ).group_by(Question.question_type).all()
    
    for q_type, count in type_stats:
        print(f"{str(q_type).replace('QuestionType.', '')}: {count}")
    
    # Sample questions from each subject
    print("\n--- Sample Questions by Section ---")
    for subject in [Subject.VERBAL_REASONING, Subject.QUANTITATIVE_REASONING, 
                   Subject.READING, Subject.MATH, Subject.GENERAL]:
        questions = db.query(Question).filter(Question.subject == subject).limit(2).all()
        if questions:
            print(f"\n{str(subject).replace('Subject.', '')}:")
            for i, q in enumerate(questions, 1):
                print(f"  {i}. {q.question_text[:80]}...")
                if q.question_metadata and 'choices' in q.question_metadata:
                    choices = q.question_metadata['choices']
                    if choices:
                        print(f"     Choices: {len(choices)} options")
    
    # Check for questions with answers
    questions_with_answers = db.query(Question).filter(
        Question.question_metadata.op('->>')('correct_answer') != None
    ).count()
    print(f"\n--- Answer Coverage ---")
    print(f"Questions with answers: {questions_with_answers}/{total} ({questions_with_answers/total*100:.1f}%)")
    
    # Topics analysis
    print("\n--- Question Topics ---")
    all_questions = db.query(Question).all()
    topic_counts = {}
    
    for q in all_questions:
        if q.topic:
            topic_counts[q.topic] = topic_counts.get(q.topic, 0) + 1
    
    for topic, count in sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"{topic:30} {count:3d} questions")
    
    db.close()

if __name__ == "__main__":
    main()