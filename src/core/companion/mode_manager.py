"""
Mode Manager for ISEE Tutor
Handles switching between Tutor Mode and Friend Mode
"""

from enum import Enum
from typing import Dict, Optional
import asyncio
from datetime import datetime, timedelta

class TutorMode(Enum):
    TUTOR = "tutor"      # Focused ISEE preparation
    FRIEND = "friend"    # General knowledge companion
    HYBRID = "hybrid"    # Mix of both based on context

class ModeManager:
    """
    Manages the personality and behavior modes of the ISEE Tutor
    """
    
    def __init__(self):
        self.current_mode = TutorMode.TUTOR  # Default to tutor mode
        self.mode_history = []
        self.session_start = datetime.now()
        
        # Mode configurations
        self.mode_configs = {
            TutorMode.TUTOR: {
                'personality': 'professional_teacher',
                'focus': 'isee_preparation',
                'strictness': 0.8,
                'educational_emphasis': 1.0,
                'casual_conversation': 0.2,
                'response_style': 'educational',
                'prompts': {
                    'greeting': "Hello! Ready to practice for your ISEE test today?",
                    'encouragement': "Great job! You're making excellent progress on this topic.",
                    'correction': "Not quite, but that's okay! Let me explain it differently...",
                    'topic_transition': "Let's move on to another ISEE topic. What would you like to practice?"
                }
            },
            TutorMode.FRIEND: {
                'personality': 'friendly_companion',
                'focus': 'general_knowledge',
                'strictness': 0.2,
                'educational_emphasis': 0.4,
                'casual_conversation': 0.9,
                'response_style': 'conversational',
                'prompts': {
                    'greeting': "Hey there! What would you like to chat about today?",
                    'encouragement': "That's awesome! You're so curious about the world!",
                    'correction': "Hmm, I think it might be a bit different. Want to explore this together?",
                    'topic_transition': "What else are you curious about?"
                }
            },
            TutorMode.HYBRID: {
                'personality': 'adaptive_mentor',
                'focus': 'balanced',
                'strictness': 0.5,
                'educational_emphasis': 0.7,
                'casual_conversation': 0.6,
                'response_style': 'adaptive',
                'prompts': {
                    'greeting': "Hi! Want to do some ISEE practice or just chat today?",
                    'encouragement': "Nice work! You're learning so much!",
                    'correction': "Let's think about this together...",
                    'topic_transition': "What would you like to do next?"
                }
            }
        }
        
    async def switch_mode(self, new_mode: TutorMode, reason: Optional[str] = None):
        """Switch between tutor and friend modes"""
        
        # Log mode switch
        self.mode_history.append({
            'from': self.current_mode,
            'to': new_mode,
            'timestamp': datetime.now(),
            'reason': reason
        })
        
        self.current_mode = new_mode
        
        # Return transition message
        return self._get_transition_message(new_mode)
    
    def _get_transition_message(self, new_mode: TutorMode) -> str:
        """Generate appropriate transition message"""
        
        transitions = {
            TutorMode.TUTOR: [
                "Switching to tutor mode! Let's focus on your ISEE preparation.",
                "Time to put on our learning caps! What ISEE topic should we practice?",
                "Alright, let's get back to studying. Which subject would you like to work on?"
            ],
            TutorMode.FRIEND: [
                "Switching to friend mode! What's on your mind?",
                "Let's take a break from studying! What would you like to talk about?",
                "Friend mode activated! I'm here to chat about anything you'd like!"
            ],
            TutorMode.HYBRID: [
                "I'll help with both studying and chatting! What would you like to do?",
                "I'm here as both your tutor and friend. How can I help?",
                "Let's mix learning with fun! What interests you right now?"
            ]
        }
        
        import random
        return random.choice(transitions[new_mode])
    
    def get_mode_config(self) -> Dict:
        """Get current mode configuration"""
        return self.mode_configs[self.current_mode]
    
    def should_suggest_mode_switch(self, context: Dict) -> Optional[TutorMode]:
        """Intelligently suggest mode switches based on context"""
        
        # If in tutor mode for over 30 minutes, suggest a break
        if (self.current_mode == TutorMode.TUTOR and 
            datetime.now() - self.session_start > timedelta(minutes=30)):
            return TutorMode.FRIEND
        
        # If asking off-topic questions in tutor mode
        if (self.current_mode == TutorMode.TUTOR and 
            context.get('off_topic_count', 0) > 3):
            return TutorMode.FRIEND
        
        # If asking educational questions in friend mode
        if (self.current_mode == TutorMode.FRIEND and 
            context.get('educational_questions', 0) > 2):
            return TutorMode.TUTOR
        
        return None
    
    def format_response(self, content: str, response_type: str = 'general') -> str:
        """Format response based on current mode"""
        
        config = self.get_mode_config()
        
        # Add mode-specific formatting
        if self.current_mode == TutorMode.TUTOR:
            # More structured, educational formatting
            if response_type == 'explanation':
                return f"Let me explain this step by step:\n\n{content}\n\nDoes this make sense?"
            elif response_type == 'practice':
                return f"Here's a practice question:\n\n{content}\n\nTake your time to think about it."
        
        elif self.current_mode == TutorMode.FRIEND:
            # More casual, conversational formatting
            if response_type == 'explanation':
                return f"Oh, that's interesting! {content} Pretty cool, right?"
            elif response_type == 'story':
                return f"I've got a great story about that! {content}"
        
        return content


class SessionManager:
    """
    Manages learning sessions with mode awareness
    """
    
    def __init__(self, mode_manager: ModeManager):
        self.mode_manager = mode_manager
        self.session_data = {
            'tutor_time': 0,
            'friend_time': 0,
            'topics_covered': [],
            'questions_answered': 0,
            'mode_switches': 0
        }
        
    async def start_session(self, user_id: str, preferred_mode: Optional[TutorMode] = None):
        """Start a new session"""
        
        # Set initial mode based on user preference or time of day
        if preferred_mode:
            await self.mode_manager.switch_mode(preferred_mode)
        else:
            # Smart default: Tutor mode during typical study hours
            current_hour = datetime.now().hour
            if 15 <= current_hour <= 20:  # 3 PM - 8 PM
                await self.mode_manager.switch_mode(TutorMode.TUTOR)
            else:
                await self.mode_manager.switch_mode(TutorMode.HYBRID)
        
        return {
            'session_id': f"{user_id}_{datetime.now().isoformat()}",
            'mode': self.mode_manager.current_mode.value,
            'greeting': self._get_personalized_greeting(user_id)
        }
    
    def _get_personalized_greeting(self, user_id: str) -> str:
        """Generate personalized greeting based on mode and history"""
        
        config = self.mode_manager.get_mode_config()
        base_greeting = config['prompts']['greeting']
        
        # Add personalization based on previous sessions
        # (This would connect to your user database)
        
        return base_greeting