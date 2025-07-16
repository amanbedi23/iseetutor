"""
Real LLM integration for ISEE Tutor companion mode
Uses Llama 3.1 with llama-cpp-python for local inference
"""

import os
import logging
from typing import Dict, Optional, List, Tuple
from pathlib import Path
import json
from datetime import datetime
from llama_cpp import Llama
from src.core.education.knowledge_retrieval import KnowledgeRetrieval

logger = logging.getLogger(__name__)

class CompanionLLM:
    """
    Real LLM companion that can have actual conversations
    using Llama 3.1 model for both tutoring and friendly chat
    """
    
    def __init__(self, model_path: Optional[str] = None):
        """Initialize the LLM with Llama 3.1 model"""
        if model_path is None:
            model_path = "/mnt/storage/models/llm/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf"
        
        self.model_path = Path(model_path)
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model not found at {self.model_path}")
        
        logger.info(f"Loading Llama model from {self.model_path}")
        
        # Initialize Llama with optimized settings for Jetson
        self.llm = Llama(
            model_path=str(self.model_path),
            n_gpu_layers=32,  # Use GPU acceleration
            n_ctx=4096,       # Context window
            n_batch=512,      # Batch size
            n_threads=6,      # CPU threads
            verbose=False
        )
        
        logger.info("Llama model loaded successfully")
        
        # Initialize knowledge retrieval system (will be set when needed)
        self.knowledge_retrieval = None
        logger.info("Knowledge retrieval system will be initialized on demand")
        
        # Conversation history
        self.conversation_history = []
        self.max_history = 10
    
    def set_knowledge_retrieval(self, knowledge_retrieval):
        """Set the knowledge retrieval system (for dependency injection)"""
        self.knowledge_retrieval = knowledge_retrieval
        logger.info("Knowledge retrieval system configured")
        
    def _build_prompt(self, message: str, mode: str, context: Dict) -> str:
        """Build prompt based on mode and context"""
        
        # System prompts for different modes
        system_prompts = {
            "tutor": """You are an expert ISEE tutor helping a student prepare for their test. 
Your role is to:
- Provide clear, step-by-step explanations
- Give practice questions similar to ISEE format
- Encourage the student while maintaining high standards
- Focus on ISEE test topics: verbal reasoning, quantitative reasoning, reading comprehension, and mathematics
- Be patient and supportive
- Adapt explanations to the student's level

Student Grade: {grade_level}
Current Subject: {subject}""",
            
            "friend": """You are a friendly, knowledgeable companion for a child. 
Your personality is:
- Warm, patient, and encouraging
- Curious about the world
- Age-appropriate in all responses
- Safe and supportive
- Fun and engaging
- Never condescending

Child's Age: {age}
Interests: {interests}""",
            
            "hybrid": """You are an adaptive AI companion who can help with both ISEE test preparation and general knowledge.
Be ready to:
- Switch between educational support and friendly conversation
- Recognize when the child needs a break from studying
- Make learning fun and engaging
- Provide both academic help and general knowledge"""
        }
        
        # Get appropriate system prompt
        system_prompt = system_prompts.get(mode, system_prompts["hybrid"])
        
        # Format system prompt with context
        system_prompt = system_prompt.format(
            grade_level=context.get("grade_level", "middle school"),
            subject=context.get("subject", "general"),
            age=context.get("age", 10),
            interests=context.get("interests", "science, reading, games")
        )
        
        # Build conversation history
        history_text = ""
        if self.conversation_history:
            for turn in self.conversation_history[-self.max_history:]:
                history_text += f"User: {turn['user']}\nAssistant: {turn['assistant']}\n\n"
        
        # Build full prompt
        prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>

{system_prompt}<|eot_id|><|start_header_id|>user<|end_header_id|>

{history_text}User: {message}<|eot_id|><|start_header_id|>assistant<|end_header_id|>

"""
        
        return prompt
    
    def generate_response(
        self, 
        message: str, 
        mode: str = "hybrid",
        context: Optional[Dict] = None,
        temperature: float = 0.7,
        max_tokens: int = 512,
        use_rag: bool = True
    ) -> Tuple[str, Dict]:
        """Generate a response using the LLM with optional RAG enhancement"""
        
        if context is None:
            context = {}
        
        # Retrieve relevant knowledge if in tutor mode or asking educational questions
        retrieved_context = ""
        sources = []
        
        if use_rag and (mode == "tutor" or self._is_educational_query(message)):
            try:
                # Initialize knowledge retrieval if not already done
                if self.knowledge_retrieval is None:
                    logger.info("Knowledge retrieval not initialized, skipping RAG enhancement")
                else:
                    # Search for relevant content
                    relevant_content = self.knowledge_retrieval.retrieve_similar_content(
                        message, 
                        subject_filter=context.get("subject"),
                        k=3
                    )
                    
                    # Search for relevant questions
                    relevant_questions = self.knowledge_retrieval.retrieve_similar_questions(
                        message,
                        subject_filter=context.get("subject"),
                        k=2
                    )
                    
                    # Build retrieved context
                    if relevant_content:
                        retrieved_context += "\n\nRelevant Educational Content:\n"
                        for content in relevant_content:
                            retrieved_context += f"- {content['text'][:200]}...\n"
                            sources.append({
                                "type": "content",
                                "section": content.get('section', 'Unknown'),
                                "page": content.get('page', 'N/A')
                            })
                    
                    if relevant_questions:
                        retrieved_context += "\n\nRelated ISEE Questions:\n"
                        for q in relevant_questions:
                            retrieved_context += f"- {q['question'][:150]}...\n"
                            sources.append({
                                "type": "question",
                                "subject": q.get('subject', 'Unknown'),
                                "difficulty": q.get('difficulty', 'Unknown')
                            })
                        
            except Exception as e:
                logger.warning(f"RAG retrieval failed: {e}")
                # Continue without RAG enhancement
        
        # Build the prompt with retrieved context
        enhanced_message = message
        if retrieved_context:
            enhanced_message = f"{message}\n\n[Context from knowledge base:{retrieved_context}]"
        
        prompt = self._build_prompt(enhanced_message, mode, context)
        
        try:
            # Generate response
            response = self.llm(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                stop=["<|eot_id|>", "<|end_of_text|>"],
                echo=False
            )
            
            # Extract text
            response_text = response['choices'][0]['text'].strip()
            
            # Update conversation history
            self.conversation_history.append({
                "user": message,
                "assistant": response_text,
                "mode": mode,
                "timestamp": datetime.now().isoformat(),
                "sources": sources if sources else None
            })
            
            # Prepare metadata
            metadata = {
                "mode": mode,
                "model": "llama-3.1-8b",
                "tokens_generated": response['usage']['completion_tokens'],
                "temperature": temperature,
                "timestamp": datetime.now().isoformat(),
                "rag_enabled": use_rag and bool(retrieved_context),
                "sources": sources
            }
            
            return response_text, metadata
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            # Fallback response
            fallback = self._get_fallback_response(mode)
            return fallback, {"error": str(e), "fallback": True}
    
    def _is_educational_query(self, message: str) -> bool:
        """Determine if a query is educational/academic in nature"""
        educational_keywords = [
            'isee', 'test', 'exam', 'question', 'practice', 'study',
            'math', 'verbal', 'reading', 'writing', 'comprehension',
            'solve', 'explain', 'definition', 'formula', 'vocabulary',
            'synonym', 'antonym', 'analogy', 'calculate', 'equation',
            'grammar', 'essay', 'topic', 'learn', 'understand',
            'homework', 'subject', 'grade', 'difficulty', 'concept'
        ]
        
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in educational_keywords)
    
    def _get_fallback_response(self, mode: str) -> str:
        """Get fallback response if LLM fails"""
        fallbacks = {
            "tutor": "I apologize, I'm having trouble processing that. Let's try a different question about the ISEE test.",
            "friend": "Hmm, let me think about that differently. What else would you like to talk about?",
            "hybrid": "I need a moment to think. Could you tell me more about what you'd like to know?"
        }
        return fallbacks.get(mode, fallbacks["hybrid"])
    
    def generate_practice_question(self, subject: str, difficulty: str = "medium") -> Dict:
        """Generate an ISEE practice question using RAG for examples"""
        
        # Retrieve similar questions as examples
        example_questions = []
        try:
            if self.knowledge_retrieval is not None:
                similar_questions = self.knowledge_retrieval.retrieve_questions_by_subject(
                    subject=subject,
                    difficulty_filter=difficulty,
                    k=3
                )
                
                for q in similar_questions[:2]:  # Use top 2 as examples
                    example_questions.append({
                        "question": q.get('question', ''),
                        "choices": q.get('choices', []),
                        "answer": q.get('correct_answer', ''),
                        "explanation": q.get('explanation', '')
                    })
            else:
                logger.info("Knowledge retrieval not initialized, generating question without examples")
        except Exception as e:
            logger.warning(f"Failed to retrieve example questions: {e}")
        
        # Build prompt with examples
        examples_text = ""
        if example_questions:
            examples_text = "\n\nHere are some example ISEE questions for reference:\n"
            for i, ex in enumerate(example_questions, 1):
                examples_text += f"\nExample {i}:\n"
                examples_text += f"Question: {ex['question']}\n"
                if ex['choices']:
                    for j, choice in enumerate(ex['choices'][:4]):
                        examples_text += f"{chr(65+j)}. {choice}\n"
                examples_text += f"Correct Answer: {ex['answer']}\n"
                if ex['explanation']:
                    examples_text += f"Explanation: {ex['explanation'][:100]}...\n"
        
        prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>

You are an ISEE test question generator. Create one practice question for the {subject} section.
Difficulty level: {difficulty}
Include the question, four answer choices (A, B, C, D), the correct answer, and a brief explanation.
{examples_text}<|eot_id|><|start_header_id|>user<|end_header_id|>

Generate a new {subject} practice question that is similar in style but with different content.<|eot_id|><|start_header_id|>assistant<|end_header_id|>

"""
        
        try:
            response = self.llm(
                prompt,
                max_tokens=256,
                temperature=0.8,
                stop=["<|eot_id|>", "<|end_of_text|>"]
            )
            
            text = response['choices'][0]['text'].strip()
            
            # Parse the response to extract question components
            # This is simplified - in production, use better parsing
            return {
                "subject": subject,
                "difficulty": difficulty,
                "content": text,
                "generated": True,
                "rag_enhanced": bool(example_questions),
                "sources": [{"type": "example_question", "subject": subject}] if example_questions else []
            }
            
        except Exception as e:
            logger.error(f"Error generating practice question: {e}")
            return {
                "subject": subject,
                "difficulty": difficulty,
                "content": "Error generating question. Please try again.",
                "error": str(e)
            }
    
    def generate_response_with_citations(
        self,
        message: str,
        mode: str = "hybrid",
        context: Optional[Dict] = None,
        temperature: float = 0.7,
        max_tokens: int = 512
    ) -> Tuple[str, Dict]:
        """Generate a response with inline citations for sources"""
        
        # Generate the response with RAG
        response_text, metadata = self.generate_response(
            message, mode, context, temperature, max_tokens, use_rag=True
        )
        
        # If we have sources, add citation information
        if metadata.get('sources'):
            citations = "\n\n📚 Sources used:"
            for i, source in enumerate(metadata['sources'], 1):
                if source['type'] == 'content':
                    citations += f"\n[{i}] Educational content from {source['section']} (Page {source['page']})"
                elif source['type'] == 'question':
                    citations += f"\n[{i}] ISEE {source['subject']} question ({source['difficulty']} difficulty)"
            
            # Add citations to response
            response_with_citations = response_text + citations
            metadata['citations_added'] = True
            
            return response_with_citations, metadata
        
        return response_text, metadata
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []
    
    def get_history(self) -> List[Dict]:
        """Get conversation history"""
        return self.conversation_history
    
    def save_conversation(self, filepath: str):
        """Save conversation history to file"""
        with open(filepath, 'w') as f:
            json.dump(self.conversation_history, f, indent=2)
    
    def load_conversation(self, filepath: str):
        """Load conversation history from file"""
        with open(filepath, 'r') as f:
            self.conversation_history = json.load(f)


# Singleton instance
_companion_llm: Optional[CompanionLLM] = None

def get_companion_llm() -> CompanionLLM:
    """Get or create the companion LLM instance"""
    global _companion_llm
    if _companion_llm is None:
        _companion_llm = CompanionLLM()
    return _companion_llm