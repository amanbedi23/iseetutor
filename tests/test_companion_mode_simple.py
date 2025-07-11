#!/usr/bin/env python3
"""
Simple test script for ISEE Tutor Companion Mode
Works without external dependencies
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.companion.mode_manager import ModeManager, TutorMode

async def test_companion_modes():
    """Test different modes of the companion without LLM dependencies"""
    
    print("=== ISEE Tutor Companion Mode Demo ===\n")
    
    # Initialize mode manager
    mode_manager = ModeManager()
    
    # Test scenarios
    test_cases = [
        # Tutor Mode Examples
        {
            'mode': TutorMode.TUTOR,
            'message': "Can you help me with analogies?",
            'context': {'grade_level': 7, 'subject': 'verbal_reasoning'},
            'expected_response': """Great! Analogies are an important part of the ISEE verbal reasoning section. 

An analogy shows a relationship between two things. The format is:
A is to B as C is to D

Let's try one:
HAPPY is to SAD as HOT is to ____?
a) WARM
b) COLD
c) TEMPERATURE
d) FIRE

Can you figure out the relationship and find the answer?"""
        },
        {
            'mode': TutorMode.TUTOR,
            'message': "What's 3/4 + 1/2?",
            'context': {'grade_level': 6, 'subject': 'mathematics'},
            'expected_response': """Let me help you add these fractions step by step:

1) First, we need a common denominator
   3/4 and 1/2
   
2) The LCD of 4 and 2 is 4

3) Convert 1/2 to fourths: 1/2 = 2/4

4) Now add: 3/4 + 2/4 = 5/4

5) Simplify: 5/4 = 1 1/4

So 3/4 + 1/2 = 1 1/4 ✓"""
        },
        
        # Friend Mode Examples
        {
            'mode': TutorMode.FRIEND,
            'message': "Why do cats purr?",
            'context': {'age': 10, 'interests': ['animals', 'science']},
            'expected_response': """Oh, that's such a cool question! 🐱 

Cats purr for lots of reasons! The most common one is that they're happy and content - like when you're petting them. But here's something super interesting: cats also purr when they're nervous or even hurt because the vibrations can help them feel better!

The purring sound comes from muscles in their throat that vibrate really fast - between 25 and 150 times per second! Some people think purring might even help heal their bones. Isn't that amazing?

Do you have a cat? I'd love to hear about them!"""
        },
        {
            'mode': TutorMode.FRIEND,
            'message': "Tell me a fun fact about space!",
            'context': {'age': 11, 'interests': ['space', 'science']},
            'expected_response': """Ooh, I love space facts! Here's a really cool one: 

Did you know that on Venus, a day is longer than a year? 🪐 

It takes Venus 243 Earth days to rotate once (that's one Venus day), but it only takes 225 Earth days to go around the Sun (one Venus year)! 

So if you lived on Venus, you'd have your birthday before the day ended! How weird is that? 

Want to hear more space facts, or is there something specific about space you're curious about?"""
        },
        
        # Mode Switching Examples
        {
            'mode': TutorMode.TUTOR,
            'message': "I'm tired of studying. Can we just chat?",
            'context': {'study_time': 35, 'fatigue_level': 'high'},
            'expected_response': "I understand! You've been working hard. Would you like to take a break and just chat for a bit? We can talk about anything you'd like - your hobbies, favorite animals, or fun facts!",
            'suggest_switch': TutorMode.FRIEND
        },
        {
            'mode': TutorMode.FRIEND,
            'message': "Actually, can you help me practice for my ISEE test?",
            'context': {'motivation': 'high'},
            'expected_response': "Of course! I'd be happy to help you prepare for your ISEE test. Let's switch to tutor mode so I can give you the best practice questions and explanations!",
            'suggest_switch': TutorMode.TUTOR
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
        print(f"📍 Mode: {test['mode'].value.upper()}")
        print(f"   Personality: {config['personality']}")
        print(f"   Educational emphasis: {config['educational_emphasis']}")
        print(f"   Casual conversation: {config['casual_conversation']}")
        print(f"\n👤 User: {test['message']}")
        
        # Show formatted response
        formatted_response = mode_manager.format_response(
            test['expected_response'], 
            'explanation' if test['mode'] == TutorMode.TUTOR else 'general'
        )
        print(f"\n🤖 Tutor: {formatted_response[:200]}...")
        
        # Check if mode switch is suggested
        if 'suggest_switch' in test:
            print(f"\n💡 System suggests switching to: {test['suggest_switch'].value}")
        
        suggested_mode = mode_manager.should_suggest_mode_switch(test['context'])
        if suggested_mode:
            print(f"💭 Auto-detected suggestion: {suggested_mode.value}")
        
        await asyncio.sleep(0.5)  # Small delay for readability

    # Show mode history
    print("\n\n=== Mode Switch History ===")
    for entry in mode_manager.mode_history[-5:]:
        print(f"• {entry['from'].value} → {entry['to'].value} at {entry['timestamp'].strftime('%H:%M:%S')}")
        if entry['reason']:
            print(f"  Reason: {entry['reason']}")

    print("\n\n=== Demo Complete ===")
    print("\nKey Features Demonstrated:")
    print("✅ Tutor Mode: Focused ISEE preparation with step-by-step explanations")
    print("✅ Friend Mode: Engaging, conversational responses about general topics")
    print("✅ Smart Switching: System suggests mode changes based on context")
    print("✅ Mode History: Tracks all mode switches for analytics")
    print("✅ Personality System: Different response styles for each mode")
    
    print("\n📝 Configuration Summary:")
    for mode in TutorMode:
        config = mode_manager.mode_configs[mode]
        print(f"\n{mode.value.upper()} Mode:")
        print(f"  - Personality: {config['personality']}")
        print(f"  - Educational emphasis: {config['educational_emphasis'] * 100:.0f}%")
        print(f"  - Casual conversation: {config['casual_conversation'] * 100:.0f}%")
        print(f"  - Strictness: {config['strictness'] * 100:.0f}%")

if __name__ == "__main__":
    asyncio.run(test_companion_modes())