#!/usr/bin/env python3
"""
Start Celery beat scheduler for periodic tasks
"""

import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core.tasks import celery_app

if __name__ == '__main__':
    # Beat configuration
    beat_args = [
        'beat',
        '--loglevel=info',
        '--schedule=/tmp/celerybeat-schedule',  # Schedule database
    ]
    
    # Start beat scheduler
    celery_app.start(beat_args)