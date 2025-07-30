"""
Knowledge Retrieval System for Educational Content
Uses Pinecone for vector storage and retrieval of educational materials
"""

import os
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import pinecone
import openai
import hashlib
import json

logger = logging.getLogger(__name__)

class KnowledgeRetrieval:
    """Manages educational content indexing and retrieval using Pinecone"""
    
    def __init__(self, index_name: str = "isee-knowledge"):
        self.index_name = index_name
        
        # Initialize Pinecone
        api_key = os.getenv('PINECONE_API_KEY')
        if not api_key:
            raise ValueError("PINECONE_API_KEY not found in environment")
            
        # Initialize Pinecone with new client
        self.pc = pinecone.Pinecone(api_key=api_key)
        
        # Get or create index
        try:
            # Check if index exists
            if index_name not in self.pc.list_indexes().names():
                # Create index with dimension 1536 for OpenAI embeddings
                self.pc.create_index(
                    name=index_name,
                    dimension=1536,
                    metric='cosine',
                    spec=pinecone.ServerlessSpec(
                        cloud='aws',
                        region='us-east-1'
                    )
                )
                logger.info(f"Created new Pinecone index: {index_name}")
            
            self.index = self.pc.Index(index_name)
            logger.info(f"Connected to Pinecone index: {index_name}")
            
        except Exception as e:
            logger.error(f"Error initializing Pinecone: {e}")
            raise
        
        # Initialize OpenAI for embeddings
        openai.api_key = os.getenv('OPENAI_API_KEY')
        if not openai.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")
    
    def _get_embedding(self, text: str) -> List[float]:
        """Get OpenAI embedding for text"""
        try:
            response = openai.Embedding.create(
                model="text-embedding-ada-002",
                input=text
            )
            return response['data'][0]['embedding']
        except Exception as e:
            logger.error(f"Error getting embedding: {e}")
            raise
    
    def index_content(self, content_id: str, text: str, metadata: Dict) -> bool:
        """
        Index educational content in Pinecone
        
        Args:
            content_id: Unique identifier for the content
            text: The content text to index
            metadata: Metadata about the content (subject, topic, type, etc.)
            
        Returns:
            bool: Success status
        """
        try:
            # Get embedding for the text
            embedding = self._get_embedding(text)
            
            # Prepare metadata (Pinecone has limits on metadata)
            clean_metadata = {
                'text': text[:1000],  # Store first 1000 chars in metadata
                'subject': metadata.get('subject', 'general'),
                'topic': metadata.get('topic', ''),
                'type': metadata.get('type', 'content'),
                'grade_level': metadata.get('grade_level', ''),
                'source': metadata.get('source', ''),
                'indexed_at': datetime.utcnow().isoformat()
            }
            
            # Upsert to Pinecone
            self.index.upsert(
                vectors=[(content_id, embedding, clean_metadata)]
            )
            
            logger.info(f"Indexed content: {content_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error indexing content {content_id}: {e}")
            return False
    
    def search_content(self, query: str, top_k: int = 5, 
                      filter_dict: Optional[Dict] = None) -> Dict[str, List[Dict]]:
        """
        Search for relevant educational content
        
        Args:
            query: Search query
            top_k: Number of results to return
            filter_dict: Optional metadata filters
            
        Returns:
            Dict with 'content' list of matching results
        """
        try:
            # Get embedding for query
            query_embedding = self._get_embedding(query)
            
            # Build filter if provided
            pinecone_filter = {}
            if filter_dict:
                if 'subject' in filter_dict:
                    pinecone_filter['subject'] = filter_dict['subject']
                if 'type' in filter_dict:
                    pinecone_filter['type'] = filter_dict['type']
                if 'grade_level' in filter_dict:
                    pinecone_filter['grade_level'] = filter_dict['grade_level']
            
            # Search Pinecone
            results = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True,
                filter=pinecone_filter if pinecone_filter else None
            )
            
            # Format results
            content_results = []
            for match in results['matches']:
                content_results.append({
                    'id': match['id'],
                    'score': match['score'],
                    'text': match['metadata'].get('text', ''),
                    'metadata': {
                        'subject': match['metadata'].get('subject', ''),
                        'topic': match['metadata'].get('topic', ''),
                        'type': match['metadata'].get('type', ''),
                        'source': match['metadata'].get('source', '')
                    }
                })
            
            return {'content': content_results}
            
        except Exception as e:
            logger.error(f"Error searching content: {e}")
            return {'content': []}
    
    def search_questions(self, query: str, top_k: int = 5,
                        subject: Optional[str] = None) -> Dict[str, List[Dict]]:
        """
        Search for similar practice questions
        
        Args:
            query: Search query
            top_k: Number of results to return
            subject: Optional subject filter
            
        Returns:
            Dict with 'questions' list of matching results
        """
        # Use search_content with type filter for questions
        filter_dict = {'type': 'question'}
        if subject:
            filter_dict['subject'] = subject
            
        results = self.search_content(query, top_k=top_k, filter_dict=filter_dict)
        
        # Rename 'content' to 'questions' for consistency
        return {'questions': results['content']}
    
    def get_similar_concepts(self, concept: str, top_k: int = 3) -> List[Dict]:
        """
        Find concepts similar to the given one
        
        Args:
            concept: The concept to find similar ones for
            top_k: Number of results to return
            
        Returns:
            List of similar concepts with scores
        """
        results = self.search_content(
            query=concept,
            top_k=top_k,
            filter_dict={'type': 'concept'}
        )
        return results['content']
    
    def delete_content(self, content_ids: List[str]) -> bool:
        """
        Delete content from Pinecone index
        
        Args:
            content_ids: List of content IDs to delete
            
        Returns:
            bool: Success status
        """
        try:
            self.index.delete(ids=content_ids)
            logger.info(f"Deleted {len(content_ids)} items from index")
            return True
        except Exception as e:
            logger.error(f"Error deleting content: {e}")
            return False
    
    def get_index_stats(self) -> Dict:
        """Get statistics about the Pinecone index"""
        try:
            stats = self.index.describe_index_stats()
            return {
                'total_vectors': stats['total_vector_count'],
                'dimension': stats['dimension'],
                'index_fullness': stats.get('index_fullness', 0),
                'namespaces': stats.get('namespaces', {})
            }
        except Exception as e:
            logger.error(f"Error getting index stats: {e}")
            return {}