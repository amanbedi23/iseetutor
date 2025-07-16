#!/usr/bin/env python3
"""
Index all educational content and questions in ChromaDB for RAG
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.education import KnowledgeRetrieval
from src.database import SessionLocal
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Index all content and questions"""
    db = SessionLocal()
    
    try:
        print("="*60)
        print("INDEXING KNOWLEDGE BASE FOR RAG")
        print("="*60)
        
        # Initialize knowledge retrieval
        kr = KnowledgeRetrieval(db)
        
        print("\nStarting indexing process...")
        
        # Index all content
        counts = kr.index_all_content()
        
        print(f"\nIndexing complete!")
        print(f"  Content indexed: {counts['content_indexed']}")
        print(f"  Questions indexed: {counts['questions_indexed']}")
        print(f"  Errors: {counts['errors']}")
        
        # Test retrieval
        print("\n" + "-"*60)
        print("TESTING RETRIEVAL")
        print("-"*60)
        
        # Test content retrieval
        test_query = "synonyms and vocabulary"
        print(f"\nSearching for content about: '{test_query}'")
        results = kr.retrieve_similar_content(test_query, n_results=3)
        
        if results:
            print(f"Found {len(results)} relevant content items:")
            for i, result in enumerate(results, 1):
                print(f"\n  {i}. {result['metadata'].get('title', 'Unknown')}")
                print(f"     Type: {result['metadata'].get('content_type', 'unknown')}")
                print(f"     Subject: {result['metadata'].get('subject', 'unknown')}")
                print(f"     Relevance: {result['relevance_score']:.2f}")
        else:
            print("No relevant content found")
        
        # Test question retrieval
        test_query = "math equation solving"
        print(f"\n\nSearching for questions about: '{test_query}'")
        results = kr.retrieve_similar_questions(test_query, n_results=3)
        
        if results:
            print(f"Found {len(results)} relevant questions:")
            for i, result in enumerate(results, 1):
                print(f"\n  {i}. Question ID: {result.get('question_id', 'unknown')}")
                print(f"     Subject: {result['metadata'].get('subject', 'unknown')}")
                print(f"     Difficulty: {result['metadata'].get('difficulty_level', 'unknown')}")
                print(f"     Relevance: {result['relevance_score']:.2f}")
                print(f"     Preview: {result['content'][:100]}...")
        else:
            print("No relevant questions found")
        
        # Test concept search
        test_concept = "equation"
        print(f"\n\nSearching for concept: '{test_concept}'")
        results = kr.search_by_concept(test_concept, n_results=5)
        
        if results:
            print(f"Found {len(results)} items related to '{test_concept}':")
            for i, result in enumerate(results, 1):
                item_type = result['metadata'].get('type', 'unknown')
                if item_type == 'content':
                    title = result['metadata'].get('title', 'Unknown content')
                else:
                    title = f"Question {result['metadata'].get('question_id', '?')}"
                print(f"  {i}. [{item_type}] {title} (relevance: {result['relevance_score']:.2f})")
        
        print("\n" + "="*60)
        print("Knowledge base indexing completed successfully!")
        print("="*60)
        
    except Exception as e:
        logger.error(f"Error during indexing: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    main()