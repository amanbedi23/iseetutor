#!/usr/bin/env python3
"""
Start Celery worker for ISEE Tutor
"""

import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core.tasks import celery_app

if __name__ == '__main__':
    # Worker configuration
    worker_args = [
        'worker',
        '--loglevel=info',
        '--concurrency=4',  # Number of worker processes
        '--queues=default,audio,content,learning',
        '--hostname=iseetutor@%h',
        '--max-tasks-per-child=100',  # Restart worker after 100 tasks
    ]
    
    # Start worker
    celery_app.start(worker_args)