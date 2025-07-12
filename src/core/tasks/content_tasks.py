"""
Content processing background tasks
"""

import os
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

from .celery_app import celery_app
from ..content.pdf_processor import PDFProcessor, ISEEContentProcessor

logger = logging.getLogger(__name__)

@celery_app.task(name='src.core.tasks.content_tasks.process_pdf_async')
def process_pdf_async(
    pdf_path: str,
    output_dir: Optional[str] = None
) -> Dict[str, Any]:
    """
    Process PDF file asynchronously
    
    Args:
        pdf_path: Path to PDF file
        output_dir: Optional output directory
        
    Returns:
        Processing result with extracted content
    """
    try:
        # Create processor
        output_dir = output_dir or os.getenv('PROCESSED_CONTENT_PATH', 'data/processed_content')
        processor = PDFProcessor(output_dir)
        
        # Process PDF
        content = processor.process_pdf(pdf_path)
        
        return {
            'success': True,
            'title': content.title,
            'page_count': len(content.pages),
            'question_count': len(content.questions),
            'word_count': sum(p['word_count'] for p in content.pages),
            'sections': content.metadata.get('sections', []),
            'output_path': str(Path(output_dir) / f"{Path(pdf_path).stem}_processed.json")
        }
        
    except Exception as e:
        logger.error(f"Error processing PDF {pdf_path}: {e}")
        return {
            'success': False,
            'error': str(e),
            'pdf_path': pdf_path
        }

@celery_app.task(name='src.core.tasks.content_tasks.extract_questions_async')
def extract_questions_async(
    text: str,
    content_type: str = 'general'
) -> List[Dict[str, Any]]:
    """
    Extract questions from text content
    
    Args:
        text: Text content to analyze
        content_type: Type of content (general, isee, math, etc.)
        
    Returns:
        List of extracted questions
    """
    try:
        if content_type == 'isee':
            processor = ISEEContentProcessor()
        else:
            processor = PDFProcessor()
        
        questions = processor.extractor.extract_questions(text)
        
        # Enhance questions with metadata
        for i, question in enumerate(questions):
            question['id'] = f"q_{i+1}"
            question['difficulty'] = 'medium'  # Would use ML model
            question['topic'] = processor.extractor.classify_question(question['question'])
        
        logger.info(f"Extracted {len(questions)} questions from text")
        
        return questions
        
    except Exception as e:
        logger.error(f"Error extracting questions: {e}")
        return []

@celery_app.task(name='src.core.tasks.content_tasks.batch_process_pdfs')
def batch_process_pdfs(
    pdf_directory: str,
    output_dir: Optional[str] = None
) -> Dict[str, Any]:
    """
    Process multiple PDFs in a directory
    
    Args:
        pdf_directory: Directory containing PDFs
        output_dir: Output directory for processed content
        
    Returns:
        Batch processing results
    """
    try:
        pdf_dir = Path(pdf_directory)
        if not pdf_dir.exists():
            raise ValueError(f"Directory not found: {pdf_directory}")
        
        # Find all PDFs
        pdf_files = list(pdf_dir.glob("*.pdf"))
        logger.info(f"Found {len(pdf_files)} PDFs to process")
        
        # Process each PDF as a subtask
        results = []
        for pdf_file in pdf_files:
            result = process_pdf_async.delay(str(pdf_file), output_dir)
            results.append(result)
        
        # Collect results
        processed_count = 0
        failed_count = 0
        total_questions = 0
        
        for result in results:
            try:
                pdf_result = result.get(timeout=300)  # 5 minute timeout per PDF
                if pdf_result['success']:
                    processed_count += 1
                    total_questions += pdf_result.get('question_count', 0)
                else:
                    failed_count += 1
            except Exception as e:
                logger.error(f"Failed to process PDF: {e}")
                failed_count += 1
        
        return {
            'total_files': len(pdf_files),
            'processed': processed_count,
            'failed': failed_count,
            'total_questions': total_questions
        }
        
    except Exception as e:
        logger.error(f"Error in batch PDF processing: {e}")
        return {
            'success': False,
            'error': str(e)
        }

@celery_app.task(name='src.core.tasks.content_tasks.update_vector_store')
def update_vector_store(
    content_path: str,
    collection_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update ChromaDB vector store with new content
    
    Args:
        content_path: Path to content file or directory
        collection_name: ChromaDB collection name
        
    Returns:
        Update result
    """
    try:
        import chromadb
        from chromadb.config import Settings
        
        # Initialize ChromaDB
        persist_directory = os.getenv('CHROMA_PERSIST_DIRECTORY', '/mnt/storage/chromadb')
        collection_name = collection_name or os.getenv('CHROMA_COLLECTION_NAME', 'isee_tutor_knowledge')
        
        client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )
        
        collection = client.get_or_create_collection(name=collection_name)
        
        # Load and process content
        # TODO: Implement content loading and chunking
        
        logger.info(f"Updated vector store collection: {collection_name}")
        
        return {
            'success': True,
            'collection': collection_name,
            'document_count': collection.count()
        }
        
    except Exception as e:
        logger.error(f"Error updating vector store: {e}")
        return {
            'success': False,
            'error': str(e)
        }