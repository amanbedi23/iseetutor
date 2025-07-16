"""
Security middleware for ISEE Tutor.
Implements rate limiting, security headers, and request validation.
"""

from fastapi import Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.middleware.base import BaseHTTPMiddleware
import time
import logging
import hashlib
import hmac
from typing import Callable

logger = logging.getLogger(__name__)

# Rate limiter configuration
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/minute", "1000/hour"],
    headers_enabled=True
)

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(self), camera=()"
        
        # Content Security Policy
        # Allow CDN for Swagger UI on docs endpoints
        if request.url.path in ["/docs", "/redoc", "/openapi.json"]:
            csp = (
                "default-src 'self' https://cdn.jsdelivr.net https://fastapi.tiangolo.com; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "img-src 'self' data: blob: https://fastapi.tiangolo.com; "
                "font-src 'self' https://cdn.jsdelivr.net; "
                "connect-src 'self' ws: wss: https://cdn.jsdelivr.net; "
                "frame-ancestors 'none';"
            )
        else:
            csp = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: blob:; "
                "font-src 'self'; "
                "connect-src 'self' ws: wss:; "
                "frame-ancestors 'none';"
            )
        response.headers["Content-Security-Policy"] = csp
        
        # Remove server header
        if "server" in response.headers:
            del response.headers["server"]
        
        return response

class RequestValidationMiddleware(BaseHTTPMiddleware):
    """Validate incoming requests for common attack patterns."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip validation for WebSocket endpoints
        if request.url.path == "/ws":
            return await call_next(request)
            
        # Check content length
        content_length = request.headers.get("content-length")
        if content_length:
            if int(content_length) > 10 * 1024 * 1024:  # 10MB limit
                raise HTTPException(status_code=413, detail="Request too large")
        
        # Check for suspicious patterns in URL
        suspicious_patterns = [
            "../", "..\\",  # Directory traversal
            "<script", "javascript:",  # XSS attempts
            "union select", "drop table",  # SQL injection
            "\x00", "%00",  # Null byte injection
        ]
        
        url_path = str(request.url)
        for pattern in suspicious_patterns:
            if pattern.lower() in url_path.lower():
                logger.warning(f"Suspicious pattern detected: {pattern} from {request.client.host}")
                raise HTTPException(status_code=400, detail="Invalid request")
        
        # Log request
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        
        logger.info(
            f"{request.method} {request.url.path} - "
            f"{response.status_code} - {process_time:.3f}s"
        )
        
        return response

class APIKeyMiddleware(BaseHTTPMiddleware):
    """Validate API key for service-to-service communication."""
    
    def __init__(self, app, api_key: str, exclude_paths: list = None):
        super().__init__(app)
        self.api_key = api_key
        self.exclude_paths = exclude_paths or ["/health", "/docs", "/openapi.json", "/ws"]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip validation for excluded paths
        if request.url.path in self.exclude_paths:
            return await call_next(request)
        
        # Skip validation for authenticated user endpoints
        if request.url.path.startswith("/api/") and "Authorization" in request.headers:
            return await call_next(request)
        
        # Validate API key for service endpoints
        if request.url.path.startswith("/service/"):
            api_key = request.headers.get("X-API-Key")
            if not api_key or api_key != self.api_key:
                raise HTTPException(status_code=403, detail="Invalid API key")
        
        return await call_next(request)

class RequestSignatureMiddleware(BaseHTTPMiddleware):
    """Validate request signatures for webhook endpoints."""
    
    def __init__(self, app, secret: str):
        super().__init__(app)
        self.secret = secret.encode()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Only validate webhook endpoints
        if not request.url.path.startswith("/webhook/"):
            return await call_next(request)
        
        # Get signature from header
        signature = request.headers.get("X-Signature")
        if not signature:
            raise HTTPException(status_code=401, detail="Missing signature")
        
        # Get request body
        body = await request.body()
        
        # Calculate expected signature
        expected_signature = hmac.new(
            self.secret,
            body,
            hashlib.sha256
        ).hexdigest()
        
        # Validate signature
        if not hmac.compare_digest(signature, expected_signature):
            raise HTTPException(status_code=401, detail="Invalid signature")
        
        return await call_next(request)

def setup_cors(app):
    """Configure CORS with security in mind."""
    origins = [
        "http://localhost:3000",  # React dev server
        "http://localhost:8000",  # API server
        "http://192.168.10.118:3000",  # React dev server on Jetson IP
        "http://192.168.10.118:8000",  # API server on Jetson IP
        "http://192.168.10.144:3000",  # Client machine accessing the app
        "http://192.168.10.144:8000",  # Client machine API access
        # Add production URLs here
    ]
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["Content-Type", "Authorization", "X-API-Key"],
        expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining"],
        max_age=86400,  # 24 hours
    )

def setup_trusted_hosts(app, allowed_hosts: list):
    """Configure trusted host validation."""
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=allowed_hosts
    )

def setup_security_middleware(app, api_key: str, webhook_secret: str):
    """Setup all security middleware."""
    # Add middleware in reverse order (last added is first executed)
    app.add_middleware(RequestValidationMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(APIKeyMiddleware, api_key=api_key)
    app.add_middleware(RequestSignatureMiddleware, secret=webhook_secret)
    
    # Setup CORS
    setup_cors(app)
    
    # Setup trusted hosts
    setup_trusted_hosts(app, ["localhost", "127.0.0.1", "iseetutor.local"])
    
    # Add rate limit exceeded handler
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    
    return limiter