#!/usr/bin/env python3
"""Quick script to check database statistics"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from src.database import SessionLocal, Question, Content
from sqlalchemy import func

def main():
    db = SessionLocal()
    
    # Get counts
    question_count = db.query(Question).count()
    content_count = db.query(Content).count()
    
    print(f"\nDatabase Statistics:")
    print(f"Total questions: {question_count}")
    print(f"Total content items: {content_count}")
    
    # Questions by subject
    subject_stats = db.query(
        Question.subject, 
        func.count(Question.id)
    ).group_by(Question.subject).all()
    
    if subject_stats:
        print("\nQuestions by subject:")
        for subject, count in subject_stats:
            print(f"  {subject}: {count}")
    
    # Content by grade level
    level_stats = db.query(
        Content.grade_level,
        func.count(Content.id)
    ).group_by(Content.grade_level).all()
    
    if level_stats:
        print("\nContent by level:")
        for level, count in level_stats:
            print(f"  {level}: {count}")
    
    db.close()

if __name__ == "__main__":
    main()