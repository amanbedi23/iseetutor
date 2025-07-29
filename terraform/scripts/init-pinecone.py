#!/usr/bin/env python3
"""
Initialize Pinecone Vector Database for ISEE Tutor

This script creates the necessary indexes and loads initial content
into Pinecone for the ISEE Tutor application.
"""

import os
import sys
import json
import time
import argparse
from typing import List, Dict, Any
import pinecone
from sentence_transformers import SentenceTransformer
import boto3
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PineconeInitializer:
    """Initialize and populate Pinecone vector database"""
    
    def __init__(self, api_key: str, environment: str, index_name: str = "iseetutor-content"):
        """
        Initialize Pinecone connection
        
        Args:
            api_key: Pinecone API key
            environment: Pinecone environment (e.g., 'us-east-1')
            index_name: Name of the Pinecone index
        """
        self.api_key = api_key
        self.environment = environment
        self.index_name = index_name
        self.dimension = 384  # for all-MiniLM-L6-v2
        
        # Initialize Pinecone
        pinecone.init(api_key=self.api_key, environment=self.environment)
        
        # Initialize sentence transformer
        logger.info("Loading sentence transformer model...")
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        
    def create_index(self):
        """Create Pinecone index if it doesn't exist"""
        existing_indexes = pinecone.list_indexes()
        
        if self.index_name in existing_indexes:
            logger.info(f"Index '{self.index_name}' already exists")
            return
        
        logger.info(f"Creating index '{self.index_name}'...")
        pinecone.create_index(
            name=self.index_name,
            dimension=self.dimension,
            metric='cosine',
            pods=1,
            replicas=1,
            pod_type='p1.x1'
        )
        
        # Wait for index to be ready
        while not pinecone.describe_index(self.index_name).status['ready']:
            time.sleep(1)
        
        logger.info(f"Index '{self.index_name}' created successfully")
    
    def get_sample_content(self) -> List[Dict[str, Any]]:
        """Get sample educational content for initial population"""
        return [
            # General ISEE Information
            {
                "id": "isee-overview-1",
                "text": "The Independent School Entrance Examination (ISEE) is a standardized test used by many independent schools as part of their admission process. It assesses students' academic abilities and readiness for rigorous coursework.",
                "metadata": {
                    "type": "information",
                    "subject": "general",
                    "topic": "overview",
                    "grade_level": "all"
                }
            },
            {
                "id": "isee-levels-1",
                "text": "The ISEE has four levels: Primary Level (entering grades 2-4), Lower Level (entering grades 5-6), Middle Level (entering grades 7-8), and Upper Level (entering grades 9-12). Each level is tailored to be age and grade appropriate.",
                "metadata": {
                    "type": "information",
                    "subject": "general",
                    "topic": "test_levels",
                    "grade_level": "all"
                }
            },
            
            # Math Content
            {
                "id": "math-algebra-1",
                "text": "To solve a linear equation, isolate the variable on one side. For example, in 2x + 5 = 13, subtract 5 from both sides to get 2x = 8, then divide by 2 to find x = 4.",
                "metadata": {
                    "type": "concept",
                    "subject": "math",
                    "topic": "algebra",
                    "difficulty": "medium",
                    "grade_level": "7-8"
                }
            },
            {
                "id": "math-geometry-1",
                "text": "The area of a triangle is calculated using the formula A = (1/2) × base × height. The base and height must be perpendicular to each other.",
                "metadata": {
                    "type": "formula",
                    "subject": "math",
                    "topic": "geometry",
                    "difficulty": "easy",
                    "grade_level": "5-6"
                }
            },
            {
                "id": "math-fractions-1",
                "text": "To add fractions with different denominators, first find the least common denominator (LCD), convert both fractions to have the LCD, then add the numerators.",
                "metadata": {
                    "type": "concept",
                    "subject": "math",
                    "topic": "fractions",
                    "difficulty": "medium",
                    "grade_level": "5-6"
                }
            },
            
            # Reading Comprehension
            {
                "id": "reading-main-idea-1",
                "text": "The main idea of a passage is the central point or message that the author wants to convey. It's often supported by details, examples, and evidence throughout the text.",
                "metadata": {
                    "type": "strategy",
                    "subject": "reading",
                    "topic": "comprehension",
                    "difficulty": "easy",
                    "grade_level": "all"
                }
            },
            {
                "id": "reading-inference-1",
                "text": "Making inferences means drawing conclusions based on evidence and reasoning rather than explicit statements. Look for clues in the text and combine them with your background knowledge.",
                "metadata": {
                    "type": "strategy",
                    "subject": "reading",
                    "topic": "inference",
                    "difficulty": "medium",
                    "grade_level": "7-8"
                }
            },
            
            # Verbal Reasoning
            {
                "id": "verbal-synonyms-1",
                "text": "Synonyms are words with similar meanings. When answering synonym questions, consider the context and choose the word that best matches the meaning of the given word.",
                "metadata": {
                    "type": "concept",
                    "subject": "verbal",
                    "topic": "vocabulary",
                    "difficulty": "easy",
                    "grade_level": "all"
                }
            },
            {
                "id": "verbal-analogies-1",
                "text": "Analogies show relationships between pairs of words. Common relationships include: part to whole, cause and effect, synonym, antonym, and function. Identify the relationship in the first pair to solve the analogy.",
                "metadata": {
                    "type": "strategy",
                    "subject": "verbal",
                    "topic": "analogies",
                    "difficulty": "hard",
                    "grade_level": "7-12"
                }
            },
            
            # Writing Skills
            {
                "id": "writing-essay-structure-1",
                "text": "A well-structured essay includes an introduction with a thesis statement, body paragraphs with topic sentences and supporting evidence, and a conclusion that reinforces the main argument.",
                "metadata": {
                    "type": "concept",
                    "subject": "writing",
                    "topic": "essay_structure",
                    "difficulty": "medium",
                    "grade_level": "7-12"
                }
            },
            
            # Test-Taking Strategies
            {
                "id": "strategy-time-management-1",
                "text": "Effective time management on the ISEE involves pacing yourself, not spending too long on difficult questions, and leaving time to review your answers. Mark questions you're unsure about and return to them if time permits.",
                "metadata": {
                    "type": "strategy",
                    "subject": "general",
                    "topic": "test_taking",
                    "difficulty": "easy",
                    "grade_level": "all"
                }
            },
            {
                "id": "strategy-elimination-1",
                "text": "Process of elimination is a powerful strategy for multiple choice questions. Cross out answers you know are wrong to improve your chances of selecting the correct answer from the remaining options.",
                "metadata": {
                    "type": "strategy",
                    "subject": "general",
                    "topic": "test_taking",
                    "difficulty": "easy",
                    "grade_level": "all"
                }
            }
        ]
    
    def get_sample_questions(self) -> List[Dict[str, Any]]:
        """Get sample ISEE practice questions"""
        return [
            # Math Questions
            {
                "id": "math-q-1",
                "text": "If 3x + 7 = 22, what is the value of x? A) 3 B) 5 C) 7 D) 9",
                "metadata": {
                    "type": "question",
                    "subject": "math",
                    "topic": "algebra",
                    "difficulty": "easy",
                    "answer": "B",
                    "grade_level": "7-8"
                }
            },
            {
                "id": "math-q-2",
                "text": "What is the area of a rectangle with length 8 cm and width 5 cm? A) 13 cm² B) 26 cm² C) 40 cm² D) 80 cm²",
                "metadata": {
                    "type": "question",
                    "subject": "math",
                    "topic": "geometry",
                    "difficulty": "easy",
                    "answer": "C",
                    "grade_level": "5-6"
                }
            },
            {
                "id": "math-q-3",
                "text": "Simplify: 2/3 + 1/4. A) 3/7 B) 3/12 C) 8/12 D) 11/12",
                "metadata": {
                    "type": "question",
                    "subject": "math",
                    "topic": "fractions",
                    "difficulty": "medium",
                    "answer": "D",
                    "grade_level": "5-6"
                }
            },
            
            # Verbal Questions
            {
                "id": "verbal-q-1",
                "text": "Choose the word most similar in meaning to ABUNDANT: A) scarce B) plentiful C) tiny D) expensive",
                "metadata": {
                    "type": "question",
                    "subject": "verbal",
                    "topic": "synonyms",
                    "difficulty": "easy",
                    "answer": "B",
                    "grade_level": "5-8"
                }
            },
            {
                "id": "verbal-q-2",
                "text": "Complete the analogy - Book : Reading :: Fork : ___ A) Kitchen B) Metal C) Eating D) Spoon",
                "metadata": {
                    "type": "question",
                    "subject": "verbal",
                    "topic": "analogies",
                    "difficulty": "medium",
                    "answer": "C",
                    "grade_level": "7-12"
                }
            }
        ]
    
    def populate_index(self):
        """Populate the index with sample content"""
        index = pinecone.Index(self.index_name)
        
        # Get all sample data
        all_content = []
        
        # Add educational content
        content_items = self.get_sample_content()
        for item in content_items:
            all_content.append(("content", item))
        
        # Add practice questions
        question_items = self.get_sample_questions()
        for item in question_items:
            all_content.append(("questions", item))
        
        # Process in batches
        batch_size = 100
        total_items = len(all_content)
        
        logger.info(f"Indexing {total_items} items...")
        
        for i in range(0, total_items, batch_size):
            batch = all_content[i:i + batch_size]
            vectors = []
            
            for namespace, item in batch:
                # Generate embedding
                embedding = self.model.encode(item['text']).tolist()
                
                # Prepare vector
                vectors.append({
                    'id': item['id'],
                    'values': embedding,
                    'metadata': item['metadata']
                })
            
            # Upsert to appropriate namespace
            if vectors:
                # Group by namespace
                namespace_groups = {}
                for j, (namespace, _) in enumerate(batch):
                    if namespace not in namespace_groups:
                        namespace_groups[namespace] = []
                    namespace_groups[namespace].append(vectors[j])
                
                # Upsert each namespace
                for namespace, namespace_vectors in namespace_groups.items():
                    index.upsert(vectors=namespace_vectors, namespace=namespace)
                    logger.info(f"Indexed {len(namespace_vectors)} items in namespace '{namespace}'")
        
        # Get index stats
        stats = index.describe_index_stats()
        logger.info(f"Index stats: {stats}")
    
    def create_metadata_schema(self):
        """Create metadata configuration for filtering"""
        # Note: Pinecone automatically indexes metadata fields
        # This is just for documentation purposes
        metadata_schema = {
            "content": {
                "type": ["information", "concept", "formula", "strategy"],
                "subject": ["general", "math", "reading", "verbal", "writing"],
                "topic": "string",
                "difficulty": ["easy", "medium", "hard"],
                "grade_level": "string"
            },
            "questions": {
                "type": "question",
                "subject": ["math", "reading", "verbal", "writing"],
                "topic": "string",
                "difficulty": ["easy", "medium", "hard"],
                "answer": "string",
                "grade_level": "string"
            }
        }
        
        logger.info("Metadata schema defined:")
        logger.info(json.dumps(metadata_schema, indent=2))
        
        return metadata_schema
    
    def test_search(self):
        """Test the search functionality"""
        index = pinecone.Index(self.index_name)
        
        test_queries = [
            "How do I solve algebra equations?",
            "What is the main idea of a passage?",
            "Tips for time management on tests",
            "How to calculate area of shapes"
        ]
        
        logger.info("\nTesting search functionality...")
        
        for query in test_queries:
            logger.info(f"\nQuery: '{query}'")
            
            # Generate embedding
            query_embedding = self.model.encode(query).tolist()
            
            # Search in content namespace
            results = index.query(
                vector=query_embedding,
                top_k=3,
                namespace="content",
                include_metadata=True
            )
            
            for match in results.matches:
                logger.info(f"  - Score: {match.score:.3f}, ID: {match.id}")
                logger.info(f"    Subject: {match.metadata.get('subject')}, "
                          f"Topic: {match.metadata.get('topic')}")


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description="Initialize Pinecone for ISEE Tutor")
    parser.add_argument(
        "--env",
        default="dev",
        choices=["dev", "prod"],
        help="Environment (dev or prod)"
    )
    parser.add_argument(
        "--api-key",
        default=os.getenv("PINECONE_API_KEY"),
        help="Pinecone API key"
    )
    parser.add_argument(
        "--environment",
        default=os.getenv("PINECONE_ENVIRONMENT", "us-east-1"),
        help="Pinecone environment"
    )
    parser.add_argument(
        "--test-only",
        action="store_true",
        help="Only run search tests"
    )
    
    args = parser.parse_args()
    
    if not args.api_key:
        logger.error("Pinecone API key is required. Set PINECONE_API_KEY or use --api-key")
        sys.exit(1)
    
    # Initialize Pinecone
    index_name = f"iseetutor-{args.env}"
    initializer = PineconeInitializer(
        api_key=args.api_key,
        environment=args.environment,
        index_name=index_name
    )
    
    if args.test_only:
        # Just run tests
        initializer.test_search()
    else:
        # Full initialization
        logger.info(f"Initializing Pinecone for {args.env} environment...")
        
        # Create index
        initializer.create_index()
        
        # Define metadata schema
        initializer.create_metadata_schema()
        
        # Populate with sample data
        initializer.populate_index()
        
        # Test search
        initializer.test_search()
        
        logger.info("\nPinecone initialization complete!")
        logger.info(f"Index name: {index_name}")
        logger.info(f"Environment: {args.environment}")
        logger.info("\nYou can now use this index in your application.")


if __name__ == "__main__":
    main()