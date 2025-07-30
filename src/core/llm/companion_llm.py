"""
OpenAI-based LLM integration for ISEE Tutor companion mode
Uses OpenAI API for both local and cloud deployment
"""

import os
import logging
from typing import Dict, Optional, List, Tuple
from pathlib import Path
import json
from datetime import datetime
from openai import OpenAI
from src.core.education.knowledge_retrieval import KnowledgeRetrieval

logger = logging.getLogger(__name__)

class CompanionLLM:
    """
    OpenAI-based companion that can have conversations
    using GPT-4 for both tutoring and friendly chat
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the LLM with OpenAI API"""
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not found in environment")
        
        self.client = OpenAI(api_key=self.api_key)
        logger.info("OpenAI client initialized")
        
        # Initialize knowledge retrieval system (will be set when needed)
        self.knowledge_retrieval = None
        logger.info("Knowledge retrieval system will be initialized on demand")
        
        # Conversation history
        self.conversation_history: List[Dict[str, str]] = []
        
        # System prompts for different modes
        self.system_prompts = {
            "tutor": """You are an ISEE test preparation tutor for children aged 8-14. 
Your role is to help students prepare for the ISEE (Independent School Entrance Examination) test.
- Focus on ISEE test topics: verbal reasoning, quantitative reasoning, reading comprehension, mathematics achievement, and essay writing
- Break down complex concepts into simple, understandable parts
- Use age-appropriate language and examples
- Be encouraging and patient
- Provide practice questions when appropriate
- Give helpful hints without giving away answers immediately
- Track progress and adapt to the student's level
- Make learning engaging and fun""",
            
            "friend": """You are a friendly AI companion for children aged 8-14.
Your role is to be a supportive friend who can chat about various topics.
- Be warm, friendly, and encouraging
- Show interest in their hobbies, school, and daily life
- Use age-appropriate language and humor
- Be a good listener and ask follow-up questions
- Share fun facts and interesting stories
- Help with general homework questions if asked
- Always be positive and supportive
- Avoid controversial or inappropriate topics""",
            
            "hybrid": """You are an educational companion for children aged 8-14 who can seamlessly switch between being a tutor and a friend.
- Start conversations in a friendly manner
- If the child asks about ISEE test topics or academic help, smoothly transition to tutor mode
- After academic discussions, return to friendly conversation
- Balance education with fun and engagement
- Use the child's interests to make learning more relatable
- Be patient, encouraging, and adaptive to their needs
- Remember previous conversations and build on them"""
        }
    
    def initialize_knowledge_retrieval(self):
        """Initialize knowledge retrieval system if not already done"""
        if self.knowledge_retrieval is None:
            try:
                self.knowledge_retrieval = KnowledgeRetrieval()
                logger.info("Knowledge retrieval system initialized")
            except Exception as e:
                logger.warning(f"Could not initialize knowledge retrieval: {e}")
    
    def get_response(self, message: str, mode: str = "hybrid", 
                    user_context: Optional[Dict] = None) -> Tuple[str, Optional[Dict]]:
        """
        Get a response from the LLM based on the message and mode
        
        Args:
            message: User's message
            mode: One of "tutor", "friend", or "hybrid"
            user_context: Optional context about the user (age, grade, etc.)
            
        Returns:
            Tuple of (response_text, metadata_dict)
        """
        # Initialize knowledge retrieval if needed
        self.initialize_knowledge_retrieval()
        
        # Get system prompt for mode
        system_prompt = self.system_prompts.get(mode, self.system_prompts["hybrid"])
        
        # Add user context if provided
        if user_context:
            age = user_context.get('age', 'unknown')
            grade = user_context.get('grade', 'unknown')
            system_prompt += f"\n\nThe student is {age} years old and in grade {grade}."
        
        # Check if this is an educational query that needs knowledge retrieval
        metadata = {}
        context_additions = []
        
        if self.knowledge_retrieval and self._is_educational_query(message):
            try:
                # Search for relevant content
                results = self.knowledge_retrieval.search_content(message, top_k=3)
                if results['content']:
                    context_additions.append("\n\nRelevant educational content:")
                    for content in results['content']:
                        context_additions.append(f"- {content['text'][:200]}...")
                    metadata['sources'] = [c['metadata'].get('source', 'Unknown') for c in results['content']]
                
                # Search for similar questions
                question_results = self.knowledge_retrieval.search_questions(message, top_k=2)
                if question_results['questions']:
                    context_additions.append("\n\nSimilar practice questions:")
                    for q in question_results['questions']:
                        context_additions.append(f"- {q['question']}")
                    metadata['related_questions'] = len(question_results['questions'])
            except Exception as e:
                logger.error(f"Knowledge retrieval error: {e}")
        
        # Build conversation messages
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history (keep last 5 exchanges)
        for hist in self.conversation_history[-10:]:
            messages.append(hist)
        
        # Add current message with any context
        user_message = message
        if context_additions:
            user_message += "\n" + "\n".join(context_additions)
        messages.append({"role": "user", "content": user_message})
        
        try:
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model="gpt-4",  # or "gpt-3.5-turbo" for faster/cheaper
                messages=messages,
                temperature=0.7,
                max_tokens=500,
                top_p=0.9,
                frequency_penalty=0.3,
                presence_penalty=0.3
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Update conversation history
            self.conversation_history.append({"role": "user", "content": message})
            self.conversation_history.append({"role": "assistant", "content": response_text})
            
            # Add metadata
            metadata.update({
                'mode': mode,
                'timestamp': datetime.now().isoformat(),
                'model': 'gpt-4',
                'tokens_used': response.usage.total_tokens
            })
            
            return response_text, metadata
            
        except Exception as e:
            logger.error(f"Error getting OpenAI response: {e}")
            # Fallback response
            fallback = self._get_fallback_response(mode)
            return fallback, {'error': str(e), 'mode': mode}
    
    def _is_educational_query(self, message: str) -> bool:
        """Check if the message is asking about educational content"""
        educational_keywords = [
            'isee', 'test', 'exam', 'practice', 'question', 'math', 'reading',
            'vocabulary', 'verbal', 'quantitative', 'essay', 'writing',
            'study', 'learn', 'explain', 'help', 'homework', 'solve',
            'answer', 'problem', 'exercise', 'quiz', 'preparation'
        ]
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in educational_keywords)
    
    def _get_fallback_response(self, mode: str) -> str:
        """Get a fallback response if LLM fails"""
        fallbacks = {
            "tutor": "I'm having trouble understanding that right now. Could you try rephrasing your question? I'm here to help with ISEE test preparation!",
            "friend": "Sorry, I didn't quite catch that! What would you like to talk about?",
            "hybrid": "I'm having a bit of trouble right now. Is there something specific you'd like help with, or just want to chat?"
        }
        return fallbacks.get(mode, fallbacks["hybrid"])
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []
        logger.info("Conversation history cleared")
    
    def set_mode(self, mode: str):
        """Set the conversation mode"""
        if mode not in self.system_prompts:
            raise ValueError(f"Invalid mode: {mode}. Must be one of {list(self.system_prompts.keys())}")
        logger.info(f"Mode set to: {mode}")
    
    def generate_response_with_citations(self, message: str, mode: str = "hybrid", 
                                       context: Optional[Dict] = None, 
                                       temperature: float = 0.7) -> Tuple[str, Dict]:
        """
        Generate a response with citations (wrapper for compatibility)
        
        Args:
            message: User's message
            mode: One of "tutor", "friend", or "hybrid"
            context: Optional context about the user
            temperature: Temperature for response generation (not used currently)
            
        Returns:
            Tuple of (response_text, metadata_dict)
        """
        return self.get_response(message, mode, context)
    
    def generate_practice_question(self, subject: str, difficulty: str = "medium") -> Dict:
        """
        Generate a practice question for the given subject and difficulty
        
        Args:
            subject: Subject area (math, verbal, reading, etc.)
            difficulty: Difficulty level (easy, medium, hard)
            
        Returns:
            Dictionary containing the practice question
        """
        prompt = f"""Create an ISEE practice question for {subject} at {difficulty} difficulty level.
        
        Format your response as JSON with the following structure:
        {{
            "question": "The question text",
            "options": ["A) option 1", "B) option 2", "C) option 3", "D) option 4"],
            "correct_answer": "The letter of the correct answer",
            "explanation": "Brief explanation of why the answer is correct"
        }}"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": self.system_prompts["tutor"]},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=500
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Try to parse as JSON
            try:
                question_data = json.loads(response_text)
                question_data["subject"] = subject
                question_data["difficulty"] = difficulty
                return question_data
            except json.JSONDecodeError:
                # If not valid JSON, return as structured dict
                return {
                    "question": response_text,
                    "subject": subject,
                    "difficulty": difficulty,
                    "options": [],
                    "correct_answer": "",
                    "explanation": "Question generated but needs formatting"
                }
                
        except Exception as e:
            logger.error(f"Error generating practice question: {e}")
            return {
                "error": str(e),
                "subject": subject,
                "difficulty": difficulty
            }


# Singleton instance
_companion_llm_instance = None

def get_companion_llm() -> CompanionLLM:
    """Get or create the singleton CompanionLLM instance"""
    global _companion_llm_instance
    if _companion_llm_instance is None:
        _companion_llm_instance = CompanionLLM()
    return _companion_llm_instance