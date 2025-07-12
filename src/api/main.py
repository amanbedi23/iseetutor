"""
ISEE Tutor API - Main Application
Provides endpoints for companion mode, chat, and learning
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
import sys
from pathlib import Path
import json
from typing import List

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.api.routes import companion, health, auth
from src.core.companion.mode_manager import ModeManager
from src.core.security.middleware import setup_security_middleware
from src.core.security.auth import get_current_active_user
from src.core.security.validation import ChatMessageRequest, sanitize_text
from src.database.models import User
import secrets

# Global mode manager instance
mode_manager = None

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

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
    lifespan=lifespan,
    docs_url=None if os.getenv("ENVIRONMENT") == "production" else "/docs",
    redoc_url=None if os.getenv("ENVIRONMENT") == "production" else "/redoc",
    openapi_url=None if os.getenv("ENVIRONMENT") == "production" else "/openapi.json"
)

# Generate API keys if not in environment
API_KEY = os.getenv("SERVICE_API_KEY", secrets.token_urlsafe(32))
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", secrets.token_urlsafe(32))

# Setup security middleware (includes CORS)
limiter = setup_security_middleware(app, API_KEY, WEBHOOK_SECRET)

# Include routers
app.include_router(health.router, tags=["health"])
app.include_router(auth.router, tags=["authentication"])
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
            "auth": "/api/auth",
            "docs": "/docs" if os.getenv("ENVIRONMENT") != "production" else "disabled",
            "websocket": "/ws"
        }
    }

@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = None
):
    """WebSocket endpoint for real-time communication"""
    # Optional authentication for WebSocket
    # In production, you may want to require authentication
    # For now, we'll allow unauthenticated connections but limit functionality
    
    await manager.connect(websocket)
    authenticated = False
    
    # Check if token provided in query params
    if token:
        from src.core.security.auth import decode_token
        payload = decode_token(token)
        if payload and payload.get("type") == "access":
            authenticated = True
    
    try:
        while True:
            data = await websocket.receive_text()
            
            # Validate and sanitize input
            try:
                message = json.loads(data)
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON"
                }))
                continue
            
            # Sanitize message content
            if "data" in message and isinstance(message["data"], str):
                message["data"] = sanitize_text(message["data"])
            
            # Handle different message types
            if message.get("type") == "test":
                response = {
                    "type": "test_response",
                    "data": f"Echo: {message.get('data', '')}"
                }
                await manager.send_personal_message(json.dumps(response), websocket)
            
            elif message.get("type") == "status":
                response = {
                    "type": "status_response",
                    "data": f"Status received: {message.get('data', '')}"
                }
                await manager.send_personal_message(json.dumps(response), websocket)
                
            elif message.get("type") == "broadcast":
                # Broadcast to all connected clients
                await manager.broadcast(json.dumps({
                    "type": "broadcast",
                    "data": message.get("data", "")
                }))
            
            else:
                # Default echo response
                response = {
                    "type": "echo",
                    "data": message
                }
                await manager.send_personal_message(json.dumps(response), websocket)
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(json.dumps({
            "type": "connection",
            "data": "A client disconnected"
        }))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("APP_PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port, reload=True)