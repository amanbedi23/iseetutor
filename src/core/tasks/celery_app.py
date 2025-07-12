"""
Celery application configuration for ISEE Tutor
"""

import os
from celery import Celery
from kombu import Exchange, Queue
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create Celery app
celery_app = Celery('iseetutor')

# Configure Celery
celery_app.conf.update(
    # Broker settings (Redis)
    broker_url=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
    result_backend=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
    
    # Task settings
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    
    # Task routing
    task_routes={
        'src.core.tasks.audio_tasks.*': {'queue': 'audio'},
        'src.core.tasks.content_tasks.*': {'queue': 'content'},
        'src.core.tasks.learning_tasks.*': {'queue': 'learning'},
    },
    
    # Queue configuration
    task_queues=(
        Queue('default', Exchange('default'), routing_key='default'),
        Queue('audio', Exchange('audio'), routing_key='audio'),
        Queue('content', Exchange('content'), routing_key='content'),
        Queue('learning', Exchange('learning'), routing_key='learning'),
    ),
    
    # Worker settings
    worker_prefetch_multiplier=2,
    worker_max_tasks_per_child=1000,
    
    # Task execution settings
    task_soft_time_limit=300,  # 5 minutes
    task_time_limit=600,  # 10 minutes
    
    # Result backend settings
    result_expires=3600,  # 1 hour
    
    # Beat schedule (periodic tasks)
    beat_schedule={
        'cleanup-old-sessions': {
            'task': 'src.core.tasks.maintenance.cleanup_old_sessions',
            'schedule': 3600.0,  # Every hour
        },
        'update-knowledge-base': {
            'task': 'src.core.tasks.maintenance.update_knowledge_base',
            'schedule': 86400.0,  # Daily
        },
    },
)

# Auto-discover tasks
celery_app.autodiscover_tasks(['src.core.tasks'])

@celery_app.task(bind=True)
def debug_task(self):
    """Debug task to test Celery is working"""
    print(f'Request: {self.request!r}')