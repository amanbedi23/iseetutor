"""
Specialized question extractor for ISEE test PDFs
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ISEEQuestion:
    """Structured ISEE question"""
    number: int
    question_text: str
    choices: List[str]
    section: str  # VR, QR, RC, MA
    question_type: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'number': self.number,
            'question': self.question_text,
            'choices': self.choices,
            'section': self.section,
            'type': self.question_type,
            'answer': None  # Will be filled from answer key if available
        }

class ISEEQuestionExtractor:
    """Extract questions from ISEE test PDFs with proper formatting"""
    
    def __init__(self):
        # Section markers
        self.section_markers = {
            'VR': ['Verbal Reasoning', 'Section 1'],
            'QR': ['Quantitative Reasoning', 'Section 2'], 
            'RC': ['Reading Comprehension', 'Section 3'],
            'MA': ['Mathematics Achievement', 'Section 4']
        }
        
        # Question patterns - ISEE uses numbered questions with specific formatting
        # Handle both single line questions and multi-line questions
        self.question_pattern = re.compile(
            r'^(\d+)\.\s\s(.+?)(?=\n\([A-E]\)|\n\d+\.|\n©|\nGo on|$)', 
            re.MULTILINE | re.DOTALL
        )
        
        # Choice patterns - ISEE uses (A), (B), (C), (D), sometimes (E)
        self.choice_pattern = re.compile(
            r'^\([A-E]\)\s+(.+?)$',
            re.MULTILINE
        )
    
    def extract_questions(self, text: str) -> List[Dict[str, Any]]:
        """Extract all questions from ISEE PDF text"""
        questions = []
        
        # Split text into sections
        sections = self._split_into_sections(text)
        
        for section_name, section_text in sections.items():
            if not section_text:
                continue
                
            # Extract questions from this section
            section_questions = self._extract_section_questions(
                section_text, 
                section_name
            )
            questions.extend(section_questions)
        
        logger.info(f"Extracted {len(questions)} total questions")
        return questions
    
    def _split_into_sections(self, text: str) -> Dict[str, str]:
        """Split the PDF text into ISEE sections"""
        sections = {}
        current_section = None
        current_text = []
        
        lines = text.split('\n')
        
        for line in lines:
            # Check if this line marks a new section
            section_found = False
            for section_code, markers in self.section_markers.items():
                if any(marker in line for marker in markers):
                    # Save previous section
                    if current_section:
                        sections[current_section] = '\n'.join(current_text)
                    
                    # Start new section
                    current_section = section_code
                    current_text = []
                    section_found = True
                    break
            
            if not section_found and current_section:
                current_text.append(line)
        
        # Save last section
        if current_section:
            sections[current_section] = '\n'.join(current_text)
        
        logger.info(f"Found sections: {list(sections.keys())}")
        return sections
    
    def _extract_section_questions(self, text: str, section: str) -> List[Dict[str, Any]]:
        """Extract questions from a specific section"""
        questions = []
        
        # Clean the text
        text = self._clean_text(text)
        
        # Find all questions
        question_matches = list(self.question_pattern.finditer(text))
        
        for i, match in enumerate(question_matches):
            question_num = int(match.group(1))
            question_text = match.group(2).strip()
            
            # Find the end position for choices
            start_pos = match.end()
            if i + 1 < len(question_matches):
                end_pos = question_matches[i + 1].start()
            else:
                # Last question - search for common end markers
                end_match = re.search(
                    r'(STOP\.|© \d{4}|Go on to the next page)',
                    text[start_pos:]
                )
                end_pos = start_pos + (end_match.start() if end_match else len(text[start_pos:]))
            
            # Extract choices for this question
            choices_text = text[start_pos:end_pos]
            choices = self._extract_choices(choices_text)
            
            # Determine question type
            question_type = self._determine_question_type(
                question_text, 
                section,
                choices
            )
            
            question = ISEEQuestion(
                number=question_num,
                question_text=question_text,
                choices=choices,
                section=section,
                question_type=question_type
            )
            
            questions.append(question.to_dict())
        
        logger.info(f"Extracted {len(questions)} questions from section {section}")
        return questions
    
    def _clean_text(self, text: str) -> str:
        """Clean text for better extraction"""
        # Remove null characters
        text = text.replace('\x00', '')
        
        # Don't normalize whitespace too aggressively - keep line breaks
        text = re.sub(r'[ \t]+', ' ', text)  # Only normalize spaces/tabs, not newlines
        
        return text
    
    def _extract_choices(self, text: str) -> List[str]:
        """Extract answer choices from text"""
        choices = []
        
        # Find all choices
        choice_matches = self.choice_pattern.findall(text)
        
        for choice_text in choice_matches:
            choice_text = choice_text.strip()
            if choice_text:
                choices.append(choice_text)
        
        return choices
    
    def _determine_question_type(
        self, 
        question_text: str, 
        section: str,
        choices: List[str]
    ) -> str:
        """Determine the type of question"""
        question_lower = question_text.lower()
        
        # Section-specific types
        if section == 'VR':
            if len(choices) == 4 and all(len(c.split()) <= 3 for c in choices):
                return 'synonym'
            elif '-------' in question_text or '------' in question_text:
                return 'sentence_completion'
            else:
                return 'verbal_reasoning'
        
        elif section == 'QR':
            return 'quantitative_reasoning'
        
        elif section == 'RC':
            if 'passage' in question_lower:
                return 'reading_passage_based'
            elif 'main' in question_lower and 'idea' in question_lower:
                return 'main_idea'
            elif 'infer' in question_lower:
                return 'inference'
            elif 'tone' in question_lower or 'attitude' in question_lower:
                return 'tone'
            elif 'most nearly means' in question_lower:
                return 'vocabulary_in_context'
            else:
                return 'reading_comprehension'
        
        elif section == 'MA':
            if 'equation' in question_lower or 'solve' in question_lower:
                return 'algebra'
            elif 'perimeter' in question_lower or 'area' in question_lower:
                return 'geometry'
            elif 'probability' in question_lower:
                return 'probability'
            elif 'fraction' in question_lower or 'decimal' in question_lower:
                return 'arithmetic'
            else:
                return 'mathematics'
        
        return 'general'
    
    def extract_with_context(self, text: str) -> Dict[str, Any]:
        """Extract questions with additional context"""
        questions = self.extract_questions(text)
        
        # Count by section
        section_counts = {}
        for q in questions:
            section = q.get('section', 'unknown')
            section_counts[section] = section_counts.get(section, 0) + 1
        
        # Count by type
        type_counts = {}
        for q in questions:
            q_type = q.get('type', 'unknown')
            type_counts[q_type] = type_counts.get(q_type, 0) + 1
        
        return {
            'questions': questions,
            'total_count': len(questions),
            'by_section': section_counts,
            'by_type': type_counts,
            'has_complete_test': len(questions) >= 120  # ISEE has ~127 questions
        }