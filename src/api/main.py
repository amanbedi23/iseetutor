"""
ISEE Tutor API - Main Application
Provides endpoints for companion mode, chat, and learning
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.api.routes import companion, health
from src.core.companion.mode_manager import ModeManager

# Global mode manager instance
mode_manager = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup application resources"""
    # Startup
    global mode_manager
    mode_manager = ModeManager()
    print("🚀 ISEE Tutor API starting...")
    print(f"📚 Knowledge base: {os.getenv('KNOWLEDGE_PATH', './data/knowledge')}")
    print(f"🤖 Default mode: {os.getenv('DEFAULT_MODE', 'tutor')}")
    
    yield
    
    # Shutdown
    print("👋 ISEE Tutor API shutting down...")

app = FastAPI(
    title="ISEE Tutor API",
    description="AI-powered ISEE test preparation with companion mode",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware for web UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["health"])
app.include_router(companion.router, prefix="/api/companion", tags=["companion"])

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to ISEE Tutor API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "companion": "/api/companion",
            "docs": "/docs"
        }
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("APP_PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port, reload=True)