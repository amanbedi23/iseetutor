"""
Companion LLM with dual-mode capabilities
Handles both ISEE tutoring and general knowledge conversations
"""

import asyncio
from typing import Dict, List, Optional, Tuple
from langchain.llms import LlamaCpp
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferWindowMemory
from langchain.chains import LLMChain
from ..core.companion.mode_manager import TutorMode, ModeManager


class CompanionLLM:
    """
    Dual-mode LLM that can switch between ISEE tutor and friendly companion
    """
    
    def __init__(self, model_path: str = "/mnt/storage/models/llama-3.2-8b-q4.gguf"):
        # Initialize the quantized model
        self.llm = LlamaCpp(
            model_path=model_path,
            n_gpu_layers=32,
            n_ctx=4096,
            n_batch=512,
            temperature=0.7,
            max_tokens=512,
            verbose=False
        )
        
        # Mode manager
        self.mode_manager = ModeManager()
        
        # Separate memories for different modes
        self.memories = {
            TutorMode.TUTOR: ConversationBufferWindowMemory(
                k=10,  # Remember more in tutor mode
                memory_key="tutor_history"
            ),
            TutorMode.FRIEND: ConversationBufferWindowMemory(
                k=5,   # Shorter memory in friend mode
                memory_key="friend_history"
            )
        }
        
        # Initialize prompt templates
        self.prompts = self._init_prompts()
        
    def _init_prompts(self) -> Dict[TutorMode, PromptTemplate]:
        """Initialize mode-specific prompts"""
        
        tutor_prompt = PromptTemplate(
            input_variables=["question", "subject", "grade_level", "tutor_history"],
            template="""You are an expert ISEE tutor helping a student prepare for their test. 
Your role is to:
- Provide clear, step-by-step explanations
- Give practice questions similar to ISEE format
- Encourage the student while maintaining high standards
- Focus on ISEE test topics: verbal reasoning, quantitative reasoning, reading comprehension, and mathematics

Student Grade Level: {grade_level}
Current Subject: {subject}

Previous conversation:
{tutor_history}

Student: {question}
Tutor: """
        )
        
        friend_prompt = PromptTemplate(
            input_variables=["question", "interests", "age", "friend_history"],
            template="""You are a friendly, knowledgeable companion for a child. 
Your personality is:
- Warm, patient, and encouraging
- Curious about the world
- Age-appropriate in all responses
- Safe and supportive

Child's Age: {age}
Interests: {interests}

Previous conversation:
{friend_history}

Child: {question}
Friend: """
        )
        
        hybrid_prompt = PromptTemplate(
            input_variables=["question", "context", "history"],
            template="""You are an adaptive AI companion who can help with both ISEE test preparation and general knowledge.
Determine from the context whether to focus on education or casual conversation.

Context: {context}
Previous conversation:
{history}

User: {question}
Assistant: """
        )
        
        return {
            TutorMode.TUTOR: tutor_prompt,
            TutorMode.FRIEND: friend_prompt,
            TutorMode.HYBRID: hybrid_prompt
        }
    
    async def get_response(
        self,
        question: str,
        user_context: Dict,
        force_mode: Optional[TutorMode] = None
    ) -> Tuple[str, Dict]:
        """
        Get response based on current mode or forced mode
        """
        
        # Check if mode switch is needed
        if force_mode and force_mode != self.mode_manager.current_mode:
            switch_message = await self.mode_manager.switch_mode(force_mode)
            # Prepend switch message to response
            question = f"[Mode switched to {force_mode.value}] {question}"
        
        # Detect if automatic mode switch is suggested
        suggested_mode = self.mode_manager.should_suggest_mode_switch(user_context)
        
        # Get current mode and configuration
        current_mode = self.mode_manager.current_mode
        mode_config = self.mode_manager.get_mode_config()
        
        # Prepare mode-specific inputs
        if current_mode == TutorMode.TUTOR:
            chain_inputs = {
                'question': question,
                'subject': user_context.get('subject', 'general'),
                'grade_level': user_context.get('grade_level', 'middle school'),
                'tutor_history': self.memories[TutorMode.TUTOR].buffer
            }
        elif current_mode == TutorMode.FRIEND:
            chain_inputs = {
                'question': question,
                'interests': user_context.get('interests', 'science, reading, games'),
                'age': user_context.get('age', 10),
                'friend_history': self.memories[TutorMode.FRIEND].buffer
            }
        else:  # HYBRID
            chain_inputs = {
                'question': question,
                'context': str(user_context),
                'history': self.memories[TutorMode.TUTOR].buffer + self.memories[TutorMode.FRIEND].buffer
            }
        
        # Create chain with appropriate prompt
        chain = LLMChain(
            llm=self.llm,
            prompt=self.prompts[current_mode],
            verbose=False
        )
        
        # Get response
        response = await chain.arun(**chain_inputs)
        
        # Save to appropriate memory
        if current_mode in [TutorMode.TUTOR, TutorMode.HYBRID]:
            self.memories[TutorMode.TUTOR].save_context(
                {"input": question}, {"output": response}
            )
        if current_mode in [TutorMode.FRIEND, TutorMode.HYBRID]:
            self.memories[TutorMode.FRIEND].save_context(
                {"input": question}, {"output": response}
            )
        
        # Prepare metadata
        metadata = {
            'mode': current_mode.value,
            'suggested_mode_switch': suggested_mode.value if suggested_mode else None,
            'response_style': mode_config['response_style'],
            'educational_emphasis': mode_config['educational_emphasis']
        }
        
        return response, metadata
    
    def clear_memory(self, mode: Optional[TutorMode] = None):
        """Clear conversation memory for specific mode or all modes"""
        if mode:
            self.memories[mode].clear()
        else:
            for memory in self.memories.values():
                memory.clear()


class ISEEContentManager:
    """
    Manages ISEE-specific content while allowing general knowledge queries
    """
    
    def __init__(self, content_path: str = "/mnt/storage/content"):
        self.content_path = content_path
        
        # ISEE content categories
        self.isee_topics = {
            'verbal_reasoning': [
                'synonyms', 'sentence_completion', 'analogies'
            ],
            'quantitative_reasoning': [
                'numbers_operations', 'algebraic_concepts', 
                'geometry', 'measurement', 'data_analysis'
            ],
            'reading_comprehension': [
                'main_idea', 'supporting_ideas', 'inference',
                'vocabulary', 'tone', 'figurative_language'
            ],
            'mathematics': [
                'arithmetic', 'algebra', 'geometry', 
                'data_interpretation', 'word_problems'
            ]
        }
        
        # General knowledge categories (for friend mode)
        self.general_topics = {
            'science': ['biology', 'physics', 'chemistry', 'astronomy'],
            'history': ['world_history', 'us_history', 'ancient_civilizations'],
            'geography': ['countries', 'capitals', 'landmarks', 'cultures'],
            'arts': ['music', 'painting', 'literature', 'dance'],
            'fun_facts': ['animals', 'space', 'inventions', 'records']
        }
    
    def classify_query(self, query: str) -> Tuple[str, str]:
        """
        Classify if query is ISEE-related or general knowledge
        Returns: (category, topic)
        """
        
        query_lower = query.lower()
        
        # Check for ISEE keywords
        isee_keywords = ['isee', 'test', 'practice', 'question', 'exam', 'prepare']
        if any(keyword in query_lower for keyword in isee_keywords):
            return 'isee', self._identify_isee_topic(query)
        
        # Check for subject-specific keywords
        for subject, topics in self.isee_topics.items():
            for topic in topics:
                if topic.replace('_', ' ') in query_lower:
                    return 'isee', subject
        
        # Otherwise, it's general knowledge
        return 'general', self._identify_general_topic(query)
    
    def _identify_isee_topic(self, query: str) -> str:
        """Identify specific ISEE topic from query"""
        # Implementation would use NLP or keyword matching
        return 'verbal_reasoning'  # Default
    
    def _identify_general_topic(self, query: str) -> str:
        """Identify general knowledge topic from query"""
        # Implementation would use NLP or keyword matching
        return 'science'  # Default