"""
Knowledge Retrieval System for Educational Content
Uses ChromaDB for vector storage and retrieval of educational materials
"""

import os
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import chromadb
from chromadb.utils import embedding_functions
from sqlalchemy.orm import Session
import hashlib

from src.database import Content, Question, Subject

logger = logging.getLogger(__name__)

class KnowledgeRetrieval:
    """Manages educational content indexing and retrieval using ChromaDB"""
    
    def __init__(self, db_session: Session, collection_name: str = "isee_knowledge"):
        self.db = db_session
        self.collection_name = collection_name
        
        # Initialize ChromaDB client
        persist_path = os.getenv('CHROMADB_PATH', './data/knowledge/chromadb')
        self.client = chromadb.PersistentClient(path=persist_path)
        
        # Use default embedding function (all-MiniLM-L6-v2)
        self.embedding_function = embedding_functions.DefaultEmbeddingFunction()
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_function,
            metadata={"description": "ISEE educational content and questions"}
        )
        
        logger.info(f"Initialized KnowledgeRetrieval with collection: {collection_name}")
    
    def index_content(self, content: Content) -> bool:
        """
        Index a piece of educational content in ChromaDB
        
        Args:
            content: Content object from database
            
        Returns:
            bool: Success status
        """
        try:
            # Generate unique ID for the content
            doc_id = f"content_{content.id}"
            
            # Prepare document text
            document_text = self._prepare_content_text(content)
            
            # Prepare metadata
            metadata = {
                'content_id': content.id,
                'type': 'content',
                'content_type': content.content_type or 'unknown',
                'title': content.title,
                'subject': content.subject or 'general',
                'grade_level': content.grade_level or 'unknown',
                'created_at': content.created_at.isoformat() if content.created_at else None
            }
            
            # Add to collection
            self.collection.add(
                documents=[document_text],
                metadatas=[metadata],
                ids=[doc_id]
            )
            
            logger.info(f"Indexed content {content.id}: {content.title}")
            return True
            
        except Exception as e:
            logger.error(f"Error indexing content {content.id}: {e}")
            return False
    
    def index_question(self, question: Question) -> bool:
        """
        Index a question in ChromaDB for retrieval
        
        Args:
            question: Question object from database
            
        Returns:
            bool: Success status
        """
        try:
            # Generate unique ID for the question
            doc_id = f"question_{question.id}"
            
            # Prepare document text
            document_text = self._prepare_question_text(question)
            
            # Prepare metadata
            metadata = {
                'question_id': question.id,
                'type': 'question',
                'subject': question.subject.value if question.subject else 'general',
                'topic': question.topic or 'general',
                'difficulty_level': question.difficulty_level,
                'question_type': question.question_type.value if question.question_type else 'unknown'
            }
            
            # Add source information from metadata if available
            if question.question_metadata and 'source' in question.question_metadata:
                metadata['source'] = question.question_metadata['source']
            
            # Add to collection
            self.collection.add(
                documents=[document_text],
                metadatas=[metadata],
                ids=[doc_id]
            )
            
            logger.info(f"Indexed question {question.id}")
            return True
            
        except Exception as e:
            logger.error(f"Error indexing question {question.id}: {e}")
            return False
    
    def retrieve_similar_content(
        self, 
        query: str, 
        n_results: int = 5,
        subject_filter: Optional[str] = None,
        content_type_filter: Optional[str] = None
    ) -> List[Dict]:
        """
        Retrieve similar educational content based on query
        
        Args:
            query: Search query
            n_results: Number of results to return
            subject_filter: Optional subject filter
            content_type_filter: Optional content type filter
            
        Returns:
            List of similar content with metadata
        """
        try:
            # Build where clause for filtering
            where_clause = {'type': 'content'}
            if subject_filter:
                where_clause['subject'] = subject_filter
            if content_type_filter:
                where_clause['content_type'] = content_type_filter
            
            # Query the collection
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where_clause
            )
            
            # Format results
            formatted_results = []
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    metadata = results['metadatas'][0][i] if results['metadatas'] else {}
                    distance = results['distances'][0][i] if results['distances'] else 0
                    
                    formatted_results.append({
                        'content': doc,
                        'metadata': metadata,
                        'relevance_score': 1 - distance  # Convert distance to similarity
                    })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error retrieving content: {e}")
            return []
    
    def retrieve_similar_questions(
        self,
        query: str,
        n_results: int = 10,
        subject_filter: Optional[Subject] = None,
        difficulty_range: Optional[Tuple[int, int]] = None
    ) -> List[Dict]:
        """
        Retrieve similar questions based on query
        
        Args:
            query: Search query
            n_results: Number of results to return
            subject_filter: Optional subject filter
            difficulty_range: Optional (min, max) difficulty range
            
        Returns:
            List of similar questions with metadata
        """
        try:
            # Build where clause
            where_clause = {'type': 'question'}
            if subject_filter:
                where_clause['subject'] = subject_filter.value
            
            # Note: ChromaDB doesn't support range queries directly,
            # so we'll filter difficulty after retrieval
            
            # Query the collection
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results * 2 if difficulty_range else n_results,  # Get extra if filtering
                where=where_clause
            )
            
            # Format and filter results
            formatted_results = []
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    metadata = results['metadatas'][0][i] if results['metadatas'] else {}
                    distance = results['distances'][0][i] if results['distances'] else 0
                    
                    # Apply difficulty filter if specified
                    if difficulty_range:
                        difficulty = metadata.get('difficulty_level', 5)
                        if difficulty < difficulty_range[0] or difficulty > difficulty_range[1]:
                            continue
                    
                    formatted_results.append({
                        'content': doc,
                        'metadata': metadata,
                        'relevance_score': 1 - distance,
                        'question_id': metadata.get('question_id')
                    })
                    
                    if len(formatted_results) >= n_results:
                        break
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error retrieving questions: {e}")
            return []
    
    def get_explanation_context(
        self,
        question_id: int,
        include_similar: bool = True
    ) -> Dict:
        """
        Get educational context for explaining a question
        
        Args:
            question_id: The question to get context for
            include_similar: Whether to include similar questions/content
            
        Returns:
            Dictionary with explanation context
        """
        try:
            # Get the question
            question = self.db.query(Question).filter(Question.id == question_id).first()
            if not question:
                return {}
            
            context = {
                'question': {
                    'text': question.question_text,
                    'subject': question.subject.value if question.subject else 'general',
                    'topic': question.topic,
                    'difficulty': question.difficulty_level
                },
                'related_content': [],
                'similar_questions': [],
                'concepts': []
            }
            
            if include_similar:
                # Get similar educational content
                similar_content = self.retrieve_similar_content(
                    question.question_text,
                    n_results=3,
                    subject_filter=question.subject.value if question.subject else None
                )
                context['related_content'] = similar_content
                
                # Get similar questions
                similar_questions = self.retrieve_similar_questions(
                    question.question_text,
                    n_results=3,
                    subject_filter=question.subject
                )
                context['similar_questions'] = similar_questions
                
                # Extract key concepts (simple keyword extraction for now)
                context['concepts'] = self._extract_concepts(question.question_text)
            
            return context
            
        except Exception as e:
            logger.error(f"Error getting explanation context: {e}")
            return {}
    
    def index_all_content(self) -> Dict[str, int]:
        """
        Index all content and questions from the database
        
        Returns:
            Dictionary with counts of indexed items
        """
        counts = {
            'content_indexed': 0,
            'questions_indexed': 0,
            'errors': 0
        }
        
        # Index all content
        content_items = self.db.query(Content).filter(Content.processed == True).all()
        for content in content_items:
            if self.index_content(content):
                counts['content_indexed'] += 1
            else:
                counts['errors'] += 1
        
        # Index all questions
        questions = self.db.query(Question).all()
        for question in questions:
            if self.index_question(question):
                counts['questions_indexed'] += 1
            else:
                counts['errors'] += 1
        
        logger.info(f"Indexing complete: {counts}")
        return counts
    
    def _prepare_content_text(self, content: Content) -> str:
        """Prepare content text for indexing"""
        parts = [content.title]
        
        if content.text_content:
            # Limit text content to first 1000 characters
            parts.append(content.text_content[:1000])
        
        if content.content_metadata:
            # Add relevant metadata
            if 'description' in content.content_metadata:
                parts.append(content.content_metadata['description'])
            if 'topics' in content.content_metadata:
                parts.append(' '.join(content.content_metadata['topics']))
        
        return '\n'.join(parts)
    
    def _prepare_question_text(self, question: Question) -> str:
        """Prepare question text for indexing"""
        parts = [question.question_text]
        
        # Add choices if available
        if question.question_metadata and 'choices' in question.question_metadata:
            choices = question.question_metadata['choices']
            parts.append("Choices: " + " | ".join(choices))
        
        # Add explanation if available
        if question.question_metadata and 'explanation' in question.question_metadata:
            parts.append("Explanation: " + question.question_metadata['explanation'])
        
        # Add topic info
        if question.topic:
            parts.append(f"Topic: {question.topic}")
        
        # Add source from metadata if available
        if question.question_metadata and 'source' in question.question_metadata:
            parts.append(f"Source: {question.question_metadata['source']}")
        
        return '\n'.join(parts)
    
    def _extract_concepts(self, text: str, max_concepts: int = 5) -> List[str]:
        """
        Simple concept extraction from text
        This is a placeholder - in production, use NLP libraries
        """
        # Simple keyword extraction based on common educational terms
        educational_keywords = {
            'equation', 'formula', 'theorem', 'definition', 'principle',
            'rule', 'law', 'concept', 'property', 'method', 'technique',
            'process', 'procedure', 'algorithm', 'pattern', 'relationship',
            'function', 'variable', 'constant', 'expression', 'term'
        }
        
        words = text.lower().split()
        concepts = []
        
        for word in words:
            cleaned_word = word.strip('.,!?;:')
            if cleaned_word in educational_keywords and cleaned_word not in concepts:
                concepts.append(cleaned_word)
                if len(concepts) >= max_concepts:
                    break
        
        return concepts
    
    def search_by_concept(self, concept: str, n_results: int = 10) -> List[Dict]:
        """
        Search for content and questions by concept
        
        Args:
            concept: Concept to search for
            n_results: Number of results to return
            
        Returns:
            List of relevant items
        """
        try:
            # Search in both content and questions
            results = self.collection.query(
                query_texts=[concept],
                n_results=n_results
            )
            
            # Format results
            formatted_results = []
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    metadata = results['metadatas'][0][i] if results['metadatas'] else {}
                    distance = results['distances'][0][i] if results['distances'] else 0
                    
                    formatted_results.append({
                        'content': doc,
                        'metadata': metadata,
                        'relevance_score': 1 - distance,
                        'type': metadata.get('type', 'unknown')
                    })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching by concept: {e}")
            return []
    
    def get_quiz_explanations(self, quiz_result_id: int) -> Dict[str, Dict]:
        """
        Get explanations for all questions in a quiz result
        
        Args:
            quiz_result_id: ID of the quiz result
            
        Returns:
            Dictionary mapping question IDs to explanations
        """
        from src.database import QuizResult, Quiz
        
        try:
            # Get quiz result
            result = self.db.query(QuizResult).filter(
                QuizResult.id == quiz_result_id
            ).first()
            
            if not result:
                return {}
            
            # Get quiz
            quiz = self.db.query(Quiz).filter(Quiz.id == result.quiz_id).first()
            if not quiz:
                return {}
            
            explanations = {}
            
            # Get explanations for each question
            for question in quiz.questions:
                # Focus on incorrect answers
                question_id_str = str(question.id)
                if result.answers and question_id_str in result.answers:
                    answer_data = result.answers[question_id_str]
                    
                    # Get explanation context
                    context = self.get_explanation_context(question.id, include_similar=True)
                    
                    explanations[question_id_str] = {
                        'question_text': question.question_text,
                        'user_answer': answer_data.get('user_answer'),
                        'correct_answer': answer_data.get('correct_answer'),
                        'is_correct': answer_data.get('is_correct', False),
                        'context': context,
                        'explanation': question.question_metadata.get('explanation', '') 
                                      if question.question_metadata else ''
                    }
            
            return explanations
            
        except Exception as e:
            logger.error(f"Error getting quiz explanations: {e}")
            return {}