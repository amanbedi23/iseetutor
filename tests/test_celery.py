#!/usr/bin/env python3
"""Test Celery task execution"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.tasks import celery_app
from src.core.tasks.audio_tasks import process_audio_chunk
from src.core.tasks.content_tasks import extract_questions_async
from src.core.tasks.learning_tasks import generate_quiz
from src.core.tasks.maintenance import check_system_health

def test_celery_connection():
    """Test Celery/Redis connection"""
    print("Testing Celery Connection")
    print("-" * 50)
    
    try:
        # Test debug task
        result = celery_app.send_task('src.core.tasks.celery_app.debug_task')
        print(f"✅ Task sent successfully: {result.id}")
        
        # Try to get result (will fail if worker not running)
        try:
            result.get(timeout=2)
            print("✅ Worker is running and processing tasks")
        except:
            print("⚠️  Worker not running or task timed out")
            print("   Start worker with: python3 celery_worker.py")
        
        return True
    except Exception as e:
        print(f"❌ Celery connection failed: {e}")
        return False

def test_audio_task():
    """Test audio processing task"""
    print("\nTesting Audio Task")
    print("-" * 50)
    
    try:
        # Create dummy audio data
        import numpy as np
        sample_rate = 16000
        duration = 1  # 1 second
        audio_data = (np.random.randn(sample_rate * duration) * 32768).astype(np.int16).tobytes()
        
        # Send task
        result = process_audio_chunk.delay(audio_data, sample_rate)
        print(f"✅ Audio task sent: {result.id}")
        
        # Get result
        try:
            output = result.get(timeout=5)
            print(f"✅ Audio processed: speech={output['is_speech']}, duration={output['duration']:.2f}s")
        except Exception as e:
            print(f"⚠️  Audio task failed or timed out: {e}")
        
    except Exception as e:
        print(f"❌ Error testing audio task: {e}")

def test_content_task():
    """Test content extraction task"""
    print("\nTesting Content Task")
    print("-" * 50)
    
    try:
        sample_text = """
        Chapter 1: Mathematics
        
        1. What is the greatest common factor of 24 and 36?
        A. 6
        B. 8
        C. 12
        D. 24
        
        2. Solve for x: 2x + 5 = 17
        A. x = 6
        B. x = 11
        C. x = 12
        D. x = 24
        """
        
        # Send task
        result = extract_questions_async.delay(sample_text, 'isee')
        print(f"✅ Content task sent: {result.id}")
        
        # Get result
        try:
            questions = result.get(timeout=5)
            print(f"✅ Extracted {len(questions)} questions")
            for q in questions[:2]:
                print(f"   - {q['question'][:50]}...")
        except Exception as e:
            print(f"⚠️  Content task failed or timed out: {e}")
        
    except Exception as e:
        print(f"❌ Error testing content task: {e}")

def test_learning_task():
    """Test learning task"""
    print("\nTesting Learning Task")
    print("-" * 50)
    
    try:
        # Send task
        result = generate_quiz.delay(
            user_id='test_user',
            topic='mathematics',
            difficulty='medium',
            question_count=5
        )
        print(f"✅ Learning task sent: {result.id}")
        
        # Get result
        try:
            quiz_data = result.get(timeout=5)
            if quiz_data['success']:
                quiz = quiz_data['quiz']
                print(f"✅ Generated quiz with {len(quiz['questions'])} questions")
            else:
                print("⚠️  Quiz generation failed")
        except Exception as e:
            print(f"⚠️  Learning task failed or timed out: {e}")
        
    except Exception as e:
        print(f"❌ Error testing learning task: {e}")

def test_maintenance_task():
    """Test maintenance task"""
    print("\nTesting Maintenance Task")
    print("-" * 50)
    
    try:
        # Send task
        result = check_system_health.delay()
        print(f"✅ Maintenance task sent: {result.id}")
        
        # Get result
        try:
            health = result.get(timeout=5)
            if health['success']:
                status = health['health_status']
                print(f"✅ System health check completed")
                print(f"   CPU: {status['cpu_percent']}%")
                print(f"   Memory: {status['memory']['percent']}%")
                print(f"   Disk: {status['disk']['percent']}%")
                print(f"   Redis: {'✅' if status['services']['redis'] else '❌'}")
            else:
                print("⚠️  Health check failed")
        except Exception as e:
            print(f"⚠️  Maintenance task failed or timed out: {e}")
        
    except Exception as e:
        print(f"❌ Error testing maintenance task: {e}")

if __name__ == "__main__":
    print("Celery Task Test Suite")
    print("=" * 50)
    
    # Test connection first
    if test_celery_connection():
        # Test individual task types
        test_audio_task()
        test_content_task()
        test_learning_task()
        test_maintenance_task()
    
    print("\n" + "=" * 50)
    print("Test complete!")
    print("\nTo start Celery worker:")
    print("  python3 celery_worker.py")
    print("\nTo start Celery beat (for periodic tasks):")
    print("  python3 celery_beat.py")