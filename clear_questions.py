#!/usr/bin/env python3
"""Clear questions from database for reimport"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from src.database import SessionLocal, Question, Content

def main():
    db = SessionLocal()
    
    # Count current questions
    question_count = db.query(Question).count()
    content_count = db.query(Content).count()
    
    print(f"Current database has {question_count} questions and {content_count} content items")
    
    response = input("Delete all questions and content? (yes/no): ")
    
    if response.lower() == 'yes':
        # Delete all questions
        db.query(Question).delete()
        # Delete all content
        db.query(Content).delete()
        db.commit()
        print("All questions and content deleted")
    else:
        print("Cancelled")
    
    db.close()

if __name__ == "__main__":
    main()