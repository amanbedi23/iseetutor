#!/usr/bin/env python3
"""List imported content"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from src.database import SessionLocal, Content

def main():
    db = SessionLocal()
    
    content_items = db.query(Content).all()
    
    print(f"\nImported Content ({len(content_items)} items):")
    print("-" * 80)
    
    for item in content_items:
        metadata = item.content_metadata or {}
        print(f"\nTitle: {item.title}")
        print(f"Subject: {item.subject}")
        print(f"Level: {item.grade_level}")
        print(f"Pages: {metadata.get('page_count', 'Unknown')}")
        print(f"Words: {metadata.get('word_count', 'Unknown')}")
        if 'key_concepts' in metadata:
            concepts = metadata['key_concepts'][:5]  # Show first 5
            if concepts:
                print(f"Key concepts: {', '.join(concepts)}")
    
    db.close()

if __name__ == "__main__":
    main()