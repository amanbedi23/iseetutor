"""
PDF content processing pipeline for educational materials
"""

import os
import re
import json
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
import hashlib

import PyPDF2
from pdf2image import convert_from_path
from PIL import Image
import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class PDFContent:
    """Structured representation of PDF content"""
    title: str
    text: str
    pages: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    images: List[Dict[str, Any]]
    questions: List[Dict[str, Any]]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage"""
        return {
            "title": self.title,
            "text": self.text,
            "pages": self.pages,
            "metadata": self.metadata,
            "images": self.images,
            "questions": self.questions
        }

class ContentExtractor:
    """Extract structured content from educational PDFs"""
    
    def __init__(self):
        self.question_patterns = [
            r'^\d+\.\s+(.+\?)',  # Numbered questions
            r'^[A-Z]\.\s+(.+\?)',  # Letter-indexed questions
            r'Question\s+\d+:?\s+(.+)',  # "Question N:" format
            r'Problem\s+\d+:?\s+(.+)',  # "Problem N:" format
        ]
        
        self.section_patterns = [
            r'^(Chapter|Section|Unit|Lesson)\s+\d+',
            r'^(Introduction|Summary|Review|Practice)',
            r'^(Reading|Mathematics|Verbal|Quantitative)\s+\w+',
        ]
    
    def extract_questions(self, text: str) -> List[Dict[str, Any]]:
        """Extract questions and answers from text"""
        questions = []
        lines = text.split('\n')
        
        current_question = None
        current_choices = []
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # Check if this is a question
            is_question = False
            for pattern in self.question_patterns:
                match = re.match(pattern, line, re.IGNORECASE)
                if match:
                    # Save previous question if exists
                    if current_question:
                        questions.append({
                            "question": current_question,
                            "choices": current_choices,
                            "answer": None,  # Would need answer key
                            "type": self.classify_question(current_question)
                        })
                    
                    current_question = match.group(1) if match.lastindex else line
                    current_choices = []
                    is_question = True
                    break
            
            # Check if this is a choice (A., B., C., etc.)
            if not is_question and current_question and re.match(r'^[A-E]\.\s+', line):
                current_choices.append(line)
        
        # Don't forget the last question
        if current_question:
            questions.append({
                "question": current_question,
                "choices": current_choices,
                "answer": None,
                "type": self.classify_question(current_question)
            })
        
        return questions
    
    def classify_question(self, question: str) -> str:
        """Classify question type"""
        question_lower = question.lower()
        
        if any(word in question_lower for word in ['calculate', 'solve', 'find the value']):
            return 'math'
        elif any(word in question_lower for word in ['define', 'meaning', 'synonym', 'antonym']):
            return 'vocabulary'
        elif any(word in question_lower for word in ['passage', 'author', 'main idea', 'infer']):
            return 'reading_comprehension'
        elif any(word in question_lower for word in ['which', 'what', 'when', 'where', 'who']):
            return 'factual'
        else:
            return 'general'
    
    def extract_sections(self, text: str) -> List[Dict[str, str]]:
        """Extract sections and chapters"""
        sections = []
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            line = line.strip()
            for pattern in self.section_patterns:
                if re.match(pattern, line, re.IGNORECASE):
                    sections.append({
                        "title": line,
                        "line_number": i,
                        "type": pattern.split('(')[1].split('|')[0].lower()
                    })
                    break
        
        return sections
    
    def extract_key_concepts(self, text: str) -> List[str]:
        """Extract key concepts and terms"""
        # Look for bolded terms, definitions, etc.
        concepts = []
        
        # Common patterns for key terms
        patterns = [
            r'\*\*(.+?)\*\*',  # Markdown bold
            r'__(.+?)__',  # Alternative bold
            r'"([A-Z][^"]+?)"',  # Quoted capitalized terms
            r'(?:is|are)\s+defined\s+as',  # Definition patterns
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            concepts.extend(matches)
        
        # Remove duplicates and clean
        concepts = list(set(c.strip() for c in concepts if len(c.strip()) > 3))
        
        return concepts

class PDFProcessor:
    """Process PDF files for educational content"""
    
    def __init__(self, output_dir: str = "data/processed_content"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.extractor = ContentExtractor()
        
        # Image output directory
        self.image_dir = self.output_dir / "images"
        self.image_dir.mkdir(exist_ok=True)
    
    def process_pdf(self, pdf_path: str) -> PDFContent:
        """Process a PDF file and extract content"""
        pdf_path = Path(pdf_path)
        
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        logger.info(f"Processing PDF: {pdf_path}")
        
        # Extract text content
        text, pages = self.extract_text(pdf_path)
        
        # Extract metadata
        metadata = self.extract_metadata(pdf_path)
        
        # Extract images (if needed)
        images = self.extract_images(pdf_path)
        
        # Extract questions
        questions = self.extractor.extract_questions(text)
        
        # Extract sections
        sections = self.extractor.extract_sections(text)
        
        # Create structured content
        content = PDFContent(
            title=metadata.get('title', pdf_path.stem),
            text=text,
            pages=pages,
            metadata={
                **metadata,
                'sections': sections,
                'key_concepts': self.extractor.extract_key_concepts(text),
                'file_hash': self.calculate_hash(pdf_path)
            },
            images=images,
            questions=questions
        )
        
        # Save processed content
        self.save_content(content, pdf_path.stem)
        
        return content
    
    def extract_text(self, pdf_path: Path) -> Tuple[str, List[Dict]]:
        """Extract text from PDF"""
        full_text = []
        pages = []
        
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    page_text = page.extract_text()
                    full_text.append(page_text)
                    
                    pages.append({
                        'page_number': page_num + 1,
                        'text': page_text,
                        'word_count': len(page_text.split())
                    })
                except Exception as e:
                    logger.error(f"Error extracting page {page_num}: {e}")
                    pages.append({
                        'page_number': page_num + 1,
                        'text': '',
                        'word_count': 0,
                        'error': str(e)
                    })
        
        return '\n\n'.join(full_text), pages
    
    def extract_metadata(self, pdf_path: Path) -> Dict[str, Any]:
        """Extract PDF metadata"""
        metadata = {}
        
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                if pdf_reader.metadata:
                    metadata = {
                        'title': pdf_reader.metadata.get('/Title', ''),
                        'author': pdf_reader.metadata.get('/Author', ''),
                        'subject': pdf_reader.metadata.get('/Subject', ''),
                        'creator': pdf_reader.metadata.get('/Creator', ''),
                        'producer': pdf_reader.metadata.get('/Producer', ''),
                        'creation_date': str(pdf_reader.metadata.get('/CreationDate', '')),
                        'modification_date': str(pdf_reader.metadata.get('/ModDate', '')),
                    }
                
                metadata['page_count'] = len(pdf_reader.pages)
                metadata['file_size'] = pdf_path.stat().st_size
                
        except Exception as e:
            logger.error(f"Error extracting metadata: {e}")
        
        return metadata
    
    def extract_images(self, pdf_path: Path, max_images: int = 10) -> List[Dict[str, Any]]:
        """Extract images from PDF (for diagrams, charts, etc.)"""
        images = []
        
        try:
            # Convert PDF pages to images
            pdf_images = convert_from_path(
                pdf_path,
                dpi=150,  # Lower DPI for faster processing
                fmt='jpeg'
            )
            
            for i, img in enumerate(pdf_images[:max_images]):
                # Save image
                img_filename = f"{pdf_path.stem}_page_{i+1}.jpg"
                img_path = self.image_dir / img_filename
                img.save(img_path, 'JPEG', quality=85)
                
                images.append({
                    'page': i + 1,
                    'path': str(img_path),
                    'width': img.width,
                    'height': img.height,
                    'format': 'JPEG'
                })
                
        except Exception as e:
            logger.warning(f"Could not extract images: {e}")
            logger.info("Make sure poppler-utils is installed: sudo apt-get install poppler-utils")
        
        return images
    
    def calculate_hash(self, file_path: Path) -> str:
        """Calculate file hash for deduplication"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def save_content(self, content: PDFContent, basename: str):
        """Save processed content to JSON"""
        output_path = self.output_dir / f"{basename}_processed.json"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(content.to_dict(), f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved processed content to: {output_path}")
    
    def batch_process(self, pdf_directory: str) -> List[PDFContent]:
        """Process all PDFs in a directory"""
        pdf_dir = Path(pdf_directory)
        results = []
        
        for pdf_file in pdf_dir.glob("*.pdf"):
            try:
                content = self.process_pdf(pdf_file)
                results.append(content)
                logger.info(f"Successfully processed: {pdf_file.name}")
            except Exception as e:
                logger.error(f"Failed to process {pdf_file.name}: {e}")
        
        return results

class ISEEContentProcessor(PDFProcessor):
    """Specialized processor for ISEE test prep materials"""
    
    def __init__(self, output_dir: str = "data/isee_content"):
        super().__init__(output_dir)
        
        # ISEE-specific patterns
        self.isee_sections = [
            "Verbal Reasoning",
            "Quantitative Reasoning", 
            "Reading Comprehension",
            "Mathematics Achievement",
            "Essay"
        ]
    
    def classify_content(self, text: str) -> str:
        """Classify content by ISEE section"""
        text_lower = text.lower()
        
        for section in self.isee_sections:
            if section.lower() in text_lower:
                return section
        
        # Try to infer from content
        if any(word in text_lower for word in ['synonym', 'antonym', 'analogy']):
            return "Verbal Reasoning"
        elif any(word in text_lower for word in ['passage', 'author', 'main idea']):
            return "Reading Comprehension"
        elif any(word in text_lower for word in ['equation', 'solve', 'calculate']):
            return "Mathematics Achievement"
        
        return "General"
    
    def extract_difficulty_level(self, text: str) -> str:
        """Extract difficulty level (Lower, Middle, Upper)"""
        patterns = [
            r'(Lower|Middle|Upper)\s+Level',
            r'Grade[s]?\s+(\d+)-(\d+)',
            r'(Elementary|Middle|High)\s+School'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)
        
        return "Unknown"