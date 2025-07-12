"""
System maintenance background tasks
"""

import os
import logging
from datetime import datetime, timedelta
from pathlib import Path
import shutil
from typing import Dict, Any

from .celery_app import celery_app

logger = logging.getLogger(__name__)

@celery_app.task(name='src.core.tasks.maintenance.cleanup_old_sessions')
def cleanup_old_sessions() -> Dict[str, Any]:
    """
    Clean up old session data
    
    Returns:
        Cleanup result
    """
    try:
        # Session timeout from environment
        timeout_minutes = int(os.getenv('SESSION_TIMEOUT_MINUTES', 45))
        cutoff_time = datetime.now() - timedelta(minutes=timeout_minutes)
        
        # TODO: Implement actual session cleanup
        # For now, just log
        logger.info(f"Cleaning up sessions older than {cutoff_time}")
        
        cleaned_count = 0  # Would be actual count
        
        return {
            'success': True,
            'cleaned_sessions': cleaned_count,
            'cutoff_time': cutoff_time.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error cleaning up sessions: {e}")
        return {
            'success': False,
            'error': str(e)
        }

@celery_app.task(name='src.core.tasks.maintenance.update_knowledge_base')
def update_knowledge_base() -> Dict[str, Any]:
    """
    Update knowledge base with new content
    
    Returns:
        Update result
    """
    try:
        content_path = Path(os.getenv('CONTENT_PATH', '/mnt/storage/content'))
        
        # Check for new content
        new_files = []
        for ext in ['*.pdf', '*.txt', '*.md']:
            new_files.extend(content_path.glob(f'new/{ext}'))
        
        logger.info(f"Found {len(new_files)} new files to process")
        
        # Process new files
        processed_count = 0
        for file_path in new_files:
            try:
                # Process file (would use content_tasks)
                logger.info(f"Processing: {file_path.name}")
                
                # Move to processed directory
                processed_dir = content_path / 'processed'
                processed_dir.mkdir(exist_ok=True)
                shutil.move(str(file_path), str(processed_dir / file_path.name))
                
                processed_count += 1
            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")
        
        return {
            'success': True,
            'files_found': len(new_files),
            'files_processed': processed_count
        }
        
    except Exception as e:
        logger.error(f"Error updating knowledge base: {e}")
        return {
            'success': False,
            'error': str(e)
        }

@celery_app.task(name='src.core.tasks.maintenance.cleanup_temp_files')
def cleanup_temp_files() -> Dict[str, Any]:
    """
    Clean up temporary files
    
    Returns:
        Cleanup result
    """
    try:
        temp_dirs = [
            '/tmp',
            'temp',
            'data/temp'
        ]
        
        total_cleaned = 0
        total_size = 0
        
        for temp_dir in temp_dirs:
            temp_path = Path(temp_dir)
            if not temp_path.exists():
                continue
            
            # Find old temporary files (older than 1 day)
            cutoff_time = datetime.now() - timedelta(days=1)
            
            for file_path in temp_path.glob('iseetutor_*'):
                try:
                    stat = file_path.stat()
                    if datetime.fromtimestamp(stat.st_mtime) < cutoff_time:
                        size = stat.st_size
                        file_path.unlink()
                        total_cleaned += 1
                        total_size += size
                except Exception as e:
                    logger.warning(f"Could not clean {file_path}: {e}")
        
        logger.info(f"Cleaned {total_cleaned} temp files, freed {total_size / 1024 / 1024:.1f} MB")
        
        return {
            'success': True,
            'files_cleaned': total_cleaned,
            'space_freed_mb': round(total_size / 1024 / 1024, 1)
        }
        
    except Exception as e:
        logger.error(f"Error cleaning temp files: {e}")
        return {
            'success': False,
            'error': str(e)
        }

@celery_app.task(name='src.core.tasks.maintenance.check_system_health')
def check_system_health() -> Dict[str, Any]:
    """
    Check system health and resources
    
    Returns:
        Health check result
    """
    try:
        import psutil
        
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Memory usage
        memory = psutil.virtual_memory()
        
        # Disk usage
        disk = psutil.disk_usage('/mnt/storage')
        
        # Check services
        services_healthy = True
        
        # Redis check
        try:
            import redis
            r = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379/0'))
            r.ping()
            redis_healthy = True
        except:
            redis_healthy = False
            services_healthy = False
        
        health_status = {
            'timestamp': datetime.now().isoformat(),
            'cpu_percent': cpu_percent,
            'memory': {
                'percent': memory.percent,
                'available_gb': round(memory.available / 1024 / 1024 / 1024, 1)
            },
            'disk': {
                'percent': disk.percent,
                'free_gb': round(disk.free / 1024 / 1024 / 1024, 1)
            },
            'services': {
                'redis': redis_healthy,
                'all_healthy': services_healthy
            }
        }
        
        # Log warnings if needed
        if cpu_percent > 80:
            logger.warning(f"High CPU usage: {cpu_percent}%")
        if memory.percent > 80:
            logger.warning(f"High memory usage: {memory.percent}%")
        if disk.percent > 80:
            logger.warning(f"High disk usage: {disk.percent}%")
        
        return {
            'success': True,
            'healthy': services_healthy and cpu_percent < 90 and memory.percent < 90,
            'health_status': health_status
        }
        
    except Exception as e:
        logger.error(f"Error checking system health: {e}")
        return {
            'success': False,
            'error': str(e)
        }