#!/usr/bin/env python3
"""
Test script for RAG integration with CompanionLLM
"""

import asyncio
import logging
from src.core.llm import get_companion_llm
from src.core.education import KnowledgeRetrieval

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_rag_integration():
    """Test the RAG integration with various queries"""
    
    print("🧪 Testing RAG Integration with CompanionLLM\n")
    
    # Initialize LLM
    try:
        llm = get_companion_llm()
        print("✅ LLM initialized successfully\n")
    except Exception as e:
        print(f"❌ Failed to initialize LLM: {e}")
        return
    
    # Test queries
    test_queries = [
        {
            "message": "What is a synonym?",
            "mode": "tutor",
            "context": {"subject": "verbal_reasoning", "grade_level": 6}
        },
        {
            "message": "Can you give me an example of an ISEE math question about fractions?",
            "mode": "tutor",
            "context": {"subject": "mathematics", "grade_level": 5}
        },
        {
            "message": "Tell me about space!",
            "mode": "friend",
            "context": {"age": 10, "interests": "astronomy, science"}
        },
        {
            "message": "How do I solve analogy questions on the ISEE?",
            "mode": "hybrid",
            "context": {"subject": "verbal_reasoning"}
        }
    ]
    
    for i, test in enumerate(test_queries, 1):
        print(f"📝 Test {i}: {test['message']}")
        print(f"   Mode: {test['mode']}")
        print(f"   Context: {test['context']}")
        
        try:
            # Test regular response
            response, metadata = llm.generate_response(
                message=test['message'],
                mode=test['mode'],
                context=test['context'],
                use_rag=True
            )
            
            print(f"\n📢 Response (without citations):")
            print(f"   {response[:200]}..." if len(response) > 200 else f"   {response}")
            print(f"\n📊 Metadata:")
            print(f"   RAG Enabled: {metadata.get('rag_enabled', False)}")
            print(f"   Sources: {len(metadata.get('sources', []))} found")
            
            # Test response with citations
            response_cited, metadata_cited = llm.generate_response_with_citations(
                message=test['message'],
                mode=test['mode'],
                context=test['context']
            )
            
            print(f"\n📚 Response (with citations):")
            print(f"   {response_cited[:300]}..." if len(response_cited) > 300 else f"   {response_cited}")
            
            if metadata_cited.get('sources'):
                print(f"\n📖 Sources used:")
                for source in metadata_cited['sources']:
                    print(f"   - {source['type']}: {source.get('section', source.get('subject', 'N/A'))}")
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
        
        print("\n" + "="*60 + "\n")
    
    # Test direct knowledge retrieval
    print("🔍 Testing Direct Knowledge Retrieval\n")
    
    try:
        kr = KnowledgeRetrieval()
        
        # Search for content
        content_results = kr.retrieve_similar_content("vocabulary strategies", k=2)
        print(f"📄 Found {len(content_results)} content results for 'vocabulary strategies'")
        if content_results:
            print(f"   Top result: {content_results[0]['text'][:100]}...")
        
        # Search for questions
        question_results = kr.retrieve_similar_questions("synonym", k=2)
        print(f"\n❓ Found {len(question_results)} question results for 'synonym'")
        if question_results:
            print(f"   Top result: {question_results[0]['question'][:100]}...")
        
    except Exception as e:
        print(f"❌ Knowledge retrieval error: {e}")
    
    print("\n✅ RAG Integration Test Complete!")

if __name__ == "__main__":
    asyncio.run(test_rag_integration())