"""Background task processing with Celery"""

from .celery_app import celery_app
from .audio_tasks import process_audio_chunk, transcribe_audio
from .content_tasks import process_pdf_async, extract_questions_async
from .learning_tasks import update_user_progress, generate_quiz

__all__ = [
    'celery_app',
    'process_audio_chunk',
    'transcribe_audio',
    'process_pdf_async',
    'extract_questions_async',
    'update_user_progress',
    'generate_quiz'
]