"""
Health check endpoints
"""

from fastapi import APIRouter
from datetime import datetime
import os
from pathlib import Path

router = APIRouter()

@router.get("/health")
async def health_check():
    """System health check"""
    
    # Check knowledge bases
    knowledge_path = Path(os.getenv("KNOWLEDGE_PATH", "./data/knowledge"))
    databases = []
    
    if knowledge_path.exists():
        db_path = knowledge_path / "databases"
        if db_path.exists():
            databases = [f.name for f in db_path.glob("*.db")]
    
    # Check model availability
    model_path = Path(os.getenv("MODEL_PATH", "./data/models/Llama-3.2-8B-Instruct-Q4_K_M.gguf"))
    model_available = model_path.exists() if model_path.parent.exists() else False
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "environment": os.getenv("APP_ENV", "development"),
        "knowledge_bases": {
            "available": len(databases) > 0,
            "databases": databases
        },
        "model": {
            "available": model_available,
            "path": str(model_path) if model_available else "Not found"
        },
        "features": {
            "companion_mode": True,
            "offline_mode": True,
            "voice_interaction": False  # Not yet implemented
        }
    }

@router.get("/health/detailed")
async def detailed_health():
    """Detailed system status"""
    
    knowledge_path = Path(os.getenv("KNOWLEDGE_PATH", "./data/knowledge"))
    
    # Count content in databases
    db_stats = {}
    if (knowledge_path / "databases").exists():
        import sqlite3
        
        for db_file in (knowledge_path / "databases").glob("*.db"):
            try:
                conn = sqlite3.connect(db_file)
                cursor = conn.cursor()
                
                # Get table names
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                
                stats = {}
                for table in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
                    count = cursor.fetchone()[0]
                    stats[table[0]] = count
                
                db_stats[db_file.stem] = stats
                conn.close()
                
            except Exception as e:
                db_stats[db_file.stem] = {"error": str(e)}
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "database_stats": db_stats,
        "configuration": {
            "default_mode": os.getenv("DEFAULT_MODE", "tutor"),
            "allow_mode_switch": os.getenv("ALLOW_MODE_SWITCH", "true") == "true",
            "offline_mode": os.getenv("OFFLINE_MODE", "true") == "true"
        }
    }