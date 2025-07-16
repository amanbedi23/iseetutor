#!/usr/bin/env python3
"""
ISEE Content Import Script
Processes practice test PDFs and imports questions into the database
"""

import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import re

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.content.pdf_processor import ISEEContentProcessor, ContentExtractor
from src.core.content.isee_question_extractor import ISEEQuestionExtractor
from src.database import Question, Content, Quiz, SessionLocal, QuestionType, Subject
import chromadb

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ISEEContentImporter:
    """Import ISEE content from various sources"""
    
    def __init__(self, db_session=None):
        self.processor = ISEEContentProcessor()
        self.isee_extractor = ISEEQuestionExtractor()
        self.db = db_session or SessionLocal()
        self.stats = {
            'files_processed': 0,
            'questions_imported': 0,
            'content_indexed': 0,
            'errors': 0
        }
        self._db_needs_rollback = False
        
        # Initialize ChromaDB for vector storage
        self.chroma_client = chromadb.PersistentClient(
            path="data/knowledge/isee_vectors"
        )
        
        # Create or get collection
        try:
            self.collection = self.chroma_client.create_collection("isee_content")
        except:
            self.collection = self.chroma_client.get_collection("isee_content")
    
    def import_pdf(self, pdf_path: Path) -> Dict[str, Any]:
        """Import a single PDF file"""
        logger.info(f"Importing PDF: {pdf_path}")
        
        # Create a fresh session for each file
        if self._db_needs_rollback:
            self.db.rollback()
            self.db.close()
            self.db = SessionLocal()
            self._db_needs_rollback = False
        
        try:
            # Process PDF
            content = self.processor.process_pdf(pdf_path)
            
            # Determine level and subject from path or content
            level = self._determine_level(pdf_path, content)
            subject = self._determine_subject(pdf_path, content)
            
            # Clean text content - remove NUL characters
            clean_text = content.text[:5000].replace('\x00', '')
            
            # Store content in database
            db_content = Content(
                title=content.title or pdf_path.stem,
                content_type='pdf',
                subject=subject,
                grade_level=level,
                text_content=clean_text,  # Store first 5000 chars
                content_metadata={
                    'page_count': len(content.pages),
                    'word_count': sum(p['word_count'] for p in content.pages),
                    'sections': content.metadata.get('sections', []),
                    'key_concepts': content.metadata.get('key_concepts', []),
                    'file_hash': content.metadata.get('file_hash'),
                    'source_file': str(pdf_path)
                }
            )
            self.db.add(db_content)
            self.db.commit()
            
            # Import questions - use ISEE-specific extractor for better results
            if 'test' in pdf_path.name.lower() and level == 'lower':
                # This is likely an ISEE test PDF - use specialized extractor
                extracted_data = self.isee_extractor.extract_with_context(content.text)
                questions_to_import = extracted_data['questions']
                logger.info(f"ISEE extractor found {len(questions_to_import)} questions")
                logger.info(f"By section: {extracted_data['by_section']}")
            else:
                # Use regular extraction
                questions_to_import = content.questions
            
            questions_imported = self._import_questions(questions_to_import, db_content.id, level, subject)
            
            # Index content for RAG
            self._index_content(content, db_content.id)
            
            # Generate additional practice questions using LLM
            if questions_imported < 10:  # If we found few questions, generate more
                self._generate_practice_questions(content.text[:2000], level, subject, db_content.id)
            
            self.stats['files_processed'] += 1
            self.stats['questions_imported'] += questions_imported
            
            return {
                'success': True,
                'content_id': db_content.id,
                'questions_imported': questions_imported,
                'level': level,
                'subject': subject
            }
            
        except Exception as e:
            logger.error(f"Error importing {pdf_path}: {e}")
            self.stats['errors'] += 1
            
            # Rollback session if needed
            if "rolled back" in str(e) or self._db_needs_rollback:
                self.db.rollback()
                self._db_needs_rollback = True
            
            return {
                'success': False,
                'error': str(e)
            }
    
    def _determine_level(self, file_path: Path, content: Any) -> str:
        """Determine ISEE level from file path or content"""
        path_str = str(file_path).lower()
        text_sample = content.text[:1000].lower() if hasattr(content, 'text') else ''
        
        if 'lower' in path_str or 'lower' in text_sample or 'grades 4-5' in text_sample:
            return 'lower'
        elif 'middle' in path_str or 'middle' in text_sample or 'grades 6-7' in text_sample:
            return 'middle'
        elif 'upper' in path_str or 'upper' in text_sample or 'grades 8-11' in text_sample:
            return 'upper'
        
        # Try to infer from difficulty
        if hasattr(content, 'metadata'):
            diff = content.metadata.get('difficulty_level', '').lower()
            if diff:
                return diff
        
        return 'unknown'
    
    def _determine_subject(self, file_path: Path, content: Any) -> str:
        """Determine subject from file path or content"""
        path_str = str(file_path).lower()
        text_sample = content.text[:2000].lower() if hasattr(content, 'text') else ''
        
        # Check file path
        subject_map = {
            'verbal': 'verbal_reasoning',
            'quantitative': 'quantitative_reasoning',
            'reading': 'reading_comprehension',
            'math': 'mathematics_achievement',
            'writing': 'essay',
            'essay': 'essay'
        }
        
        for key, value in subject_map.items():
            if key in path_str:
                return value
        
        # Check content
        if hasattr(content, 'metadata') and content.metadata.get('section'):
            return self.processor.classify_content(content.metadata['section'])
        
        # Analyze text content
        if 'synonym' in text_sample or 'antonym' in text_sample or 'analogy' in text_sample:
            return 'verbal_reasoning'
        elif 'passage' in text_sample and ('author' in text_sample or 'main idea' in text_sample):
            return 'reading_comprehension'
        elif 'solve' in text_sample or 'calculate' in text_sample or 'equation' in text_sample:
            if 'reasoning' in text_sample:
                return 'quantitative_reasoning'
            else:
                return 'mathematics_achievement'
        
        return 'general'
    
    def _import_questions(self, questions: List[Dict], content_id: int, level: str, default_subject: str) -> int:
        """Import questions into database"""
        imported = 0
        
        for q_data in questions:
            try:
                # Create question
                # Map question type to QuestionType enum
                q_type_map = {
                    'multiple_choice': QuestionType.MULTIPLE_CHOICE,
                    'true_false': QuestionType.TRUE_FALSE,
                    'vocabulary': QuestionType.MULTIPLE_CHOICE,
                    'math': QuestionType.MULTIPLE_CHOICE,
                    'reading_comprehension': QuestionType.MULTIPLE_CHOICE,
                    'general': QuestionType.MULTIPLE_CHOICE
                }
                
                # Determine subject - use section info if available
                section = q_data.get('section', '')
                if section:
                    # Map ISEE sections to subjects
                    section_to_subject = {
                        'VR': 'verbal_reasoning',
                        'QR': 'quantitative_reasoning', 
                        'RC': 'reading_comprehension',
                        'MA': 'mathematics_achievement'
                    }
                    subject = section_to_subject.get(section, default_subject)
                else:
                    subject = default_subject
                
                # Map subject to Subject enum
                subject_enum_map = {
                    'verbal_reasoning': Subject.VERBAL_REASONING,
                    'quantitative_reasoning': Subject.QUANTITATIVE_REASONING,
                    'reading_comprehension': Subject.READING,
                    'mathematics_achievement': Subject.MATH,
                    'essay': Subject.GENERAL,
                    'general': Subject.GENERAL
                }
                
                question = Question(
                    question_text=q_data['question'],
                    question_type=q_type_map.get(q_data.get('type', 'multiple_choice'), QuestionType.MULTIPLE_CHOICE),
                    subject=subject_enum_map.get(subject, Subject.GENERAL),
                    topic=q_data.get('type', subject),  # Use specific type as topic
                    difficulty_level=self._calculate_difficulty(q_data['question'], level),
                    grade_level=self._level_to_grade(level),
                    points=self._calculate_points(q_data.get('type', 'general')),
                    time_limit=self._calculate_time_limit(q_data.get('type', 'general')),
                    question_metadata={
                        'choices': q_data.get('choices', []),
                        'correct_answer': q_data.get('answer'),
                        'explanation': q_data.get('explanation', ''),
                        'source_content_id': content_id,
                        'concepts': self._extract_concepts(q_data['question'])
                    }
                )
                
                self.db.add(question)
                imported += 1
                
            except Exception as e:
                logger.error(f"Error importing question: {e}")
        
        if imported > 0:
            self.db.commit()
            
        return imported
    
    def _calculate_difficulty(self, question_text: str, level: str) -> int:
        """Calculate difficulty level (1-5)"""
        # Base difficulty on level
        base_difficulty = {
            'lower': 2,
            'middle': 3,
            'upper': 4,
            'unknown': 3
        }.get(level, 3)
        
        # Adjust based on question complexity
        words = len(question_text.split())
        if words > 50:
            base_difficulty += 1
        
        # Look for complexity indicators
        if any(word in question_text.lower() for word in ['analyze', 'evaluate', 'synthesize']):
            base_difficulty += 1
        
        return min(5, max(1, base_difficulty))
    
    def _level_to_grade(self, level: str) -> int:
        """Convert ISEE level to approximate grade"""
        return {
            'lower': 5,
            'middle': 7,
            'upper': 10,
            'unknown': 7
        }.get(level, 7)
    
    def _calculate_points(self, question_type: str) -> int:
        """Calculate points based on question type"""
        return {
            'math': 2,
            'reading_comprehension': 3,
            'vocabulary': 1,
            'general': 1
        }.get(question_type, 1)
    
    def _calculate_time_limit(self, question_type: str) -> int:
        """Calculate time limit in seconds"""
        return {
            'math': 90,
            'reading_comprehension': 180,
            'vocabulary': 30,
            'general': 60
        }.get(question_type, 60)
    
    def _extract_concepts(self, question_text: str) -> List[str]:
        """Extract key concepts from question"""
        concepts = []
        
        # Math concepts
        math_concepts = ['fraction', 'decimal', 'percentage', 'algebra', 'geometry', 
                        'ratio', 'proportion', 'equation', 'angle', 'perimeter', 'area']
        
        # Verbal concepts  
        verbal_concepts = ['synonym', 'antonym', 'analogy', 'vocabulary', 'definition']
        
        # Reading concepts
        reading_concepts = ['main idea', 'inference', 'author', 'tone', 'theme', 'summary']
        
        question_lower = question_text.lower()
        
        for concept in math_concepts + verbal_concepts + reading_concepts:
            if concept in question_lower:
                concepts.append(concept)
        
        return concepts
    
    def _index_content(self, content: Any, content_id: int):
        """Index content in ChromaDB for RAG"""
        try:
            # Index each page separately for better retrieval
            for i, page in enumerate(content.pages):
                # Clean page text - remove NUL characters
                clean_page_text = page['text'].replace('\x00', '').strip()
                if clean_page_text:
                    self.collection.add(
                        documents=[clean_page_text],
                        metadatas=[{
                            'content_id': content_id,
                            'page_number': page['page_number'],
                            'title': content.title,
                            'subject': self._determine_subject(Path(content.title), content),
                            'level': self._determine_level(Path(content.title), content)
                        }],
                        ids=[f"content_{content_id}_page_{page['page_number']}"]
                    )
            
            self.stats['content_indexed'] += len(content.pages)
            
        except Exception as e:
            logger.error(f"Error indexing content: {e}")
    
    def _generate_practice_questions(self, text_sample: str, level: str, subject: str, content_id: int):
        """Generate additional practice questions using LLM"""
        # This will be implemented to use the LLM to generate questions
        # based on the content. For now, it's a placeholder.
        logger.info(f"Would generate practice questions for {subject} at {level} level")
        pass
    
    def import_directory(self, directory: Path) -> Dict[str, Any]:
        """Import all PDFs from a directory"""
        logger.info(f"Importing from directory: {directory}")
        
        pdf_files = list(directory.rglob("*.pdf"))
        logger.info(f"Found {len(pdf_files)} PDF files")
        
        results = []
        for pdf_file in pdf_files:
            result = self.import_pdf(pdf_file)
            results.append(result)
        
        return {
            'total_files': len(pdf_files),
            'stats': self.stats,
            'results': results
        }
    
    def generate_sample_questions(self):
        """Generate sample ISEE questions for testing"""
        sample_questions = [
            # Verbal Reasoning - Synonyms
            {
                'question': 'Choose the word that is most similar in meaning to DILIGENT:',
                'choices': ['A. Lazy', 'B. Careful', 'C. Hardworking', 'D. Quick'],
                'answer': 'C',
                'type': 'vocabulary',
                'subject': 'verbal_reasoning',
                'level': 'middle'
            },
            # Verbal Reasoning - Analogies
            {
                'question': 'Book is to reading as fork is to:',
                'choices': ['A. Eating', 'B. Cooking', 'C. Kitchen', 'D. Spoon'],
                'answer': 'A',
                'type': 'vocabulary',
                'subject': 'verbal_reasoning',
                'level': 'lower'
            },
            # Quantitative Reasoning
            {
                'question': 'If 3x + 7 = 22, what is the value of x?',
                'choices': ['A. 5', 'B. 7', 'C. 9', 'D. 15'],
                'answer': 'A',
                'type': 'math',
                'subject': 'quantitative_reasoning',
                'level': 'upper'
            },
            # Mathematics Achievement
            {
                'question': 'What is 3/4 + 1/2?',
                'choices': ['A. 4/6', 'B. 5/4', 'C. 1 1/4', 'D. 3/8'],
                'answer': 'C',
                'type': 'math',
                'subject': 'mathematics_achievement',
                'level': 'middle'
            },
            # Reading Comprehension
            {
                'question': 'Based on the passage, what is the main idea the author is trying to convey?',
                'choices': [
                    'A. Technology has made life easier',
                    'B. Nature is important for human wellbeing',
                    'C. Education should be accessible to all',
                    'D. History repeats itself'
                ],
                'answer': 'B',
                'type': 'reading_comprehension',
                'subject': 'reading_comprehension',
                'level': 'upper'
            }
        ]
        
        imported = 0
        for q_data in sample_questions:
            level = q_data.pop('level')
            
            # Map to enums
            q_type_map = {
                'vocabulary': QuestionType.MULTIPLE_CHOICE,
                'math': QuestionType.MULTIPLE_CHOICE,
                'reading_comprehension': QuestionType.MULTIPLE_CHOICE
            }
            
            subject_enum_map = {
                'verbal_reasoning': Subject.VERBAL_REASONING,
                'quantitative_reasoning': Subject.QUANTITATIVE_REASONING,
                'reading_comprehension': Subject.READING,
                'mathematics_achievement': Subject.MATH
            }
            
            question = Question(
                question_text=q_data['question'],
                question_type=q_type_map.get(q_data['type'], QuestionType.MULTIPLE_CHOICE),
                subject=subject_enum_map.get(q_data['subject'], Subject.GENERAL),
                topic=q_data['subject'],
                difficulty_level=self._calculate_difficulty(q_data['question'], level),
                grade_level=self._level_to_grade(level),
                points=self._calculate_points(q_data['type']),
                time_limit=self._calculate_time_limit(q_data['type']),
                question_metadata={
                    'choices': q_data['choices'],
                    'correct_answer': q_data['answer'],
                    'is_sample': True
                }
            )
            self.db.add(question)
            imported += 1
        
        self.db.commit()
        logger.info(f"Generated {imported} sample questions")
        return imported

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Import ISEE content')
    parser.add_argument('path', nargs='?', help='Path to PDF file or directory')
    parser.add_argument('--generate-samples', action='store_true', 
                       help='Generate sample questions for testing')
    parser.add_argument('--stats', action='store_true',
                       help='Show import statistics')
    
    args = parser.parse_args()
    
    importer = ISEEContentImporter()
    
    try:
        if args.generate_samples:
            count = importer.generate_sample_questions()
            print(f"Generated {count} sample questions")
        
        elif args.path:
            path = Path(args.path)
            if path.is_file():
                result = importer.import_pdf(path)
                print(json.dumps(result, indent=2))
            elif path.is_dir():
                result = importer.import_directory(path)
                print("\nImport Summary:")
                print(f"Files processed: {result['stats']['files_processed']}")
                print(f"Questions imported: {result['stats']['questions_imported']}")
                print(f"Content indexed: {result['stats']['content_indexed']}")
                print(f"Errors: {result['stats']['errors']}")
        
        else:
            # Default: import from standard content directory
            content_dir = Path("data/content/isee/raw")
            if content_dir.exists():
                result = importer.import_directory(content_dir)
                print("\nImport Summary:")
                print(f"Files processed: {result['stats']['files_processed']}")
                print(f"Questions imported: {result['stats']['questions_imported']}")
                print(f"Content indexed: {result['stats']['content_indexed']}")
                print(f"Errors: {result['stats']['errors']}")
            else:
                print(f"No content directory found at {content_dir}")
                print("Place your PDFs in data/content/isee/raw/ and run again")
                print("\nDirectory structure:")
                print("  data/content/isee/raw/lower/    - Lower level PDFs")
                print("  data/content/isee/raw/middle/   - Middle level PDFs")
                print("  data/content/isee/raw/upper/    - Upper level PDFs")
        
        if args.stats:
            # Show database statistics
            db = SessionLocal()
            question_count = db.query(Question).count()
            content_count = db.query(Content).count()
            print(f"\nDatabase Statistics:")
            print(f"Total questions: {question_count}")
            print(f"Total content items: {content_count}")
            
            # Questions by subject
            from sqlalchemy import func
            subject_stats = db.query(
                Question.subject, 
                func.count(Question.id)
            ).group_by(Question.subject).all()
            
            print("\nQuestions by subject:")
            for subject, count in subject_stats:
                print(f"  {subject}: {count}")
    
    except KeyboardInterrupt:
        print("\nImport cancelled")
    except Exception as e:
        logger.error(f"Import failed: {e}")
        raise

if __name__ == "__main__":
    main()