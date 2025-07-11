#!/usr/bin/env python3
"""
Test script for ISEE Tutor Companion Mode
Demonstrates mode switching and different response styles
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.companion.mode_manager import ModeManager, TutorMode
from src.models.companion_llm import CompanionLLM, ISEEContentManager

async def test_companion_modes():
    """Test different modes of the companion"""
    
    print("=== ISEE Tutor Companion Mode Demo ===\n")
    
    # Initialize components
    mode_manager = ModeManager()
    content_manager = ISEEContentManager()
    
    # Note: This would normally use the actual LLM
    # For demo purposes, we'll simulate responses
    
    # Test scenarios
    test_cases = [
        # Tutor Mode Examples
        {
            'mode': TutorMode.TUTOR,
            'message': "Can you help me with analogies?",
            'context': {'grade_level': 7, 'subject': 'verbal_reasoning'}
        },
        {
            'mode': TutorMode.TUTOR,
            'message': "What's 3/4 + 1/2?",
            'context': {'grade_level': 6, 'subject': 'mathematics'}
        },
        
        # Friend Mode Examples
        {
            'mode': TutorMode.FRIEND,
            'message': "Why do cats purr?",
            'context': {'age': 10, 'interests': ['animals', 'science']}
        },
        {
            'mode': TutorMode.FRIEND,
            'message': "Tell me a fun fact about space!",
            'context': {'age': 11, 'interests': ['space', 'science']}
        },
        
        # Mode Switching Examples
        {
            'mode': TutorMode.TUTOR,
            'message': "I'm tired of studying. Can we just chat?",
            'context': {'study_time': 35, 'fatigue_level': 'high'}
        },
        {
            'mode': TutorMode.FRIEND,
            'message': "Actually, can you help me practice for my ISEE test?",
            'context': {'motivation': 'high'}
        }
    ]
    
    for i, test in enumerate(test_cases):
        print(f"\n--- Test Case {i+1} ---")
        
        # Switch mode if needed
        if mode_manager.current_mode != test['mode']:
            switch_msg = await mode_manager.switch_mode(test['mode'])
            print(f"🔄 {switch_msg}")
        
        # Show current mode
        config = mode_manager.get_mode_config()
        print(f"📍 Mode: {test['mode'].value}")
        print(f"👤 User: {test['message']}")
        
        # Classify query
        category, topic = content_manager.classify_query(test['message'])
        print(f"🏷️  Category: {category}, Topic: {topic}")
        
        # Simulate response based on mode
        if test['mode'] == TutorMode.TUTOR:
            if "analogies" in test['message'].lower():
                response = """Great! Analogies are an important part of the ISEE verbal reasoning section. 

An analogy shows a relationship between two things. The format is:
A is to B as C is to D

Let's try one:
HAPPY is to SAD as HOT is to ____?
a) WARM
b) COLD
c) TEMPERATURE
d) FIRE

Can you figure out the relationship and find the answer?"""
            
            elif "3/4 + 1/2" in test['message']:
                response = """Let me help you add these fractions step by step:

1) First, we need a common denominator
   3/4 and 1/2
   
2) The LCD of 4 and 2 is 4

3) Convert 1/2 to fourths: 1/2 = 2/4

4) Now add: 3/4 + 2/4 = 5/4

5) Simplify: 5/4 = 1 1/4

So 3/4 + 1/2 = 1 1/4 ✓"""
            
            elif "tired" in test['message'].lower():
                response = "I understand! You've been working hard. Would you like to take a break and just chat for a bit? We can talk about anything you'd like - your hobbies, favorite animals, or fun facts!"
                # Suggest mode switch
                print(f"💡 Suggested mode switch to: {TutorMode.FRIEND.value}")
            else:
                response = "Let's work on this together..."
                
        else:  # Friend mode
            if "cats purr" in test['message'].lower():
                response = """Oh, that's such a cool question! 🐱 

Cats purr for lots of reasons! The most common one is that they're happy and content - like when you're petting them. But here's something super interesting: cats also purr when they're nervous or even hurt because the vibrations can help them feel better!

The purring sound comes from muscles in their throat that vibrate really fast - between 25 and 150 times per second! Some people think purring might even help heal their bones. Isn't that amazing?

Do you have a cat? I'd love to hear about them!"""
            
            elif "space" in test['message'].lower():
                response = """Ooh, I love space facts! Here's a really cool one: 

Did you know that on Venus, a day is longer than a year? 🪐 

It takes Venus 243 Earth days to rotate once (that's one Venus day), but it only takes 225 Earth days to go around the Sun (one Venus year)! 

So if you lived on Venus, you'd have your birthday before the day ended! How weird is that? 

Want to hear more space facts, or is there something specific about space you're curious about?"""
            
            elif "practice" in test['message'].lower() and "ISEE" in test['message']:
                response = "Of course! I'd be happy to help you prepare for your ISEE test. Let's switch to tutor mode so I can give you the best practice questions and explanations!"
                print(f"💡 Suggested mode switch to: {TutorMode.TUTOR.value}")
            else:
                response = "That's interesting! Tell me more..."
        
        # Format response based on mode
        formatted_response = mode_manager.format_response(response, 'general')
        print(f"🤖 Tutor: {formatted_response[:200]}...")  # Show first 200 chars
        
        # Check if mode switch is suggested
        suggested_mode = mode_manager.should_suggest_mode_switch(test['context'])
        if suggested_mode:
            print(f"💭 System suggests switching to: {suggested_mode.value}")
        
        await asyncio.sleep(0.5)  # Small delay for readability

    print("\n\n=== Demo Complete ===")
    print("\nKey Features Demonstrated:")
    print("✅ Tutor Mode: Focused ISEE preparation with step-by-step explanations")
    print("✅ Friend Mode: Engaging, conversational responses about general topics")
    print("✅ Smart Switching: System suggests mode changes based on context")
    print("✅ Content Classification: Automatically identifies ISEE vs general queries")
    print("✅ Age-Appropriate: Responses tailored to child's age and interests")

if __name__ == "__main__":
    asyncio.run(test_companion_modes())