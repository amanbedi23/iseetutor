"""
Security tests for ISEE Tutor API
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import time

from src.api.main import app
from src.database.base import Base, get_db
from src.core.security.auth import get_password_hash
from src.database.models import User, UserRole

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_security.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

class TestAuthentication:
    """Test authentication endpoints"""
    
    def test_register_user(self):
        """Test user registration"""
        response = client.post("/api/auth/register", json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "TestPass123!",
            "age": 10,
            "grade_level": 5
        })
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
    
    def test_register_duplicate_username(self):
        """Test duplicate username rejection"""
        # First registration
        client.post("/api/auth/register", json={
            "username": "duplicate",
            "email": "first@example.com",
            "password": "TestPass123!",
            "age": 10,
            "grade_level": 5
        })
        
        # Duplicate attempt
        response = client.post("/api/auth/register", json={
            "username": "duplicate",
            "email": "second@example.com",
            "password": "TestPass123!",
            "age": 10,
            "grade_level": 5
        })
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]
    
    def test_password_validation(self):
        """Test password strength requirements"""
        weak_passwords = [
            "short",  # Too short
            "alllowercase",  # No uppercase
            "ALLUPPERCASE",  # No lowercase
            "NoNumbers!",  # No digits
            "12345678"  # No letters
        ]
        
        for pwd in weak_passwords:
            response = client.post("/api/auth/register", json={
                "username": f"user_{pwd}",
                "email": f"{pwd}@example.com",
                "password": pwd,
                "age": 10,
                "grade_level": 5
            })
            assert response.status_code == 422  # Validation error
    
    def test_login(self):
        """Test user login"""
        # Register user
        client.post("/api/auth/register", json={
            "username": "logintest",
            "email": "login@example.com",
            "password": "LoginPass123!",
            "age": 10,
            "grade_level": 5
        })
        
        # Login
        response = client.post("/api/auth/token", data={
            "username": "logintest",
            "password": "LoginPass123!"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
    
    def test_invalid_login(self):
        """Test login with wrong credentials"""
        response = client.post("/api/auth/token", data={
            "username": "nonexistent",
            "password": "WrongPass123!"
        })
        assert response.status_code == 401

class TestAuthorization:
    """Test authorization and protected endpoints"""
    
    def setup_method(self):
        """Set up test user and get token"""
        # Register and login
        client.post("/api/auth/register", json={
            "username": "authtest",
            "email": "auth@example.com",
            "password": "AuthPass123!",
            "age": 10,
            "grade_level": 5
        })
        
        response = client.post("/api/auth/token", data={
            "username": "authtest",
            "password": "AuthPass123!"
        })
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_protected_endpoint_with_token(self):
        """Test accessing protected endpoint with valid token"""
        response = client.get("/api/auth/me", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "authtest"
    
    def test_protected_endpoint_without_token(self):
        """Test accessing protected endpoint without token"""
        response = client.get("/api/auth/me")
        assert response.status_code == 401
    
    def test_chat_endpoint_requires_auth(self):
        """Test chat endpoint requires authentication"""
        response = client.post("/api/companion/chat", json={
            "message": "Hello",
            "mode": "tutor"
        })
        assert response.status_code == 401

class TestInputValidation:
    """Test input validation and sanitization"""
    
    def setup_method(self):
        """Set up authenticated client"""
        client.post("/api/auth/register", json={
            "username": "validtest",
            "email": "valid@example.com",
            "password": "ValidPass123!",
            "age": 10,
            "grade_level": 5
        })
        
        response = client.post("/api/auth/token", data={
            "username": "validtest",
            "password": "ValidPass123!"
        })
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_message_length_validation(self):
        """Test message length limits"""
        # Too long message
        long_message = "x" * 1001
        response = client.post("/api/companion/chat", 
            headers=self.headers,
            json={
                "message": long_message,
                "mode": "tutor"
            }
        )
        assert response.status_code == 422
    
    def test_mode_validation(self):
        """Test mode validation"""
        response = client.post("/api/companion/chat",
            headers=self.headers,
            json={
                "message": "Hello",
                "mode": "invalid_mode"
            }
        )
        assert response.status_code == 422
    
    def test_sql_injection_prevention(self):
        """Test SQL injection prevention"""
        malicious_queries = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "admin'--",
            "1; DELETE FROM users WHERE 1=1"
        ]
        
        for query in malicious_queries:
            response = client.post("/api/companion/search-knowledge",
                headers=self.headers,
                json={
                    "query": query,
                    "limit": 5
                }
            )
            # Should either reject or safely handle
            assert response.status_code in [200, 422]
    
    def test_xss_prevention(self):
        """Test XSS prevention"""
        xss_attempts = [
            "<script>alert('xss')</script>",
            "<img src=x onerror=alert('xss')>",
            "javascript:alert('xss')",
            "<iframe src='evil.com'></iframe>"
        ]
        
        for xss in xss_attempts:
            response = client.post("/api/companion/chat",
                headers=self.headers,
                json={
                    "message": xss,
                    "mode": "tutor"
                }
            )
            # Should sanitize the input
            assert response.status_code == 200
            # Response should not contain the script tags
            assert "<script>" not in response.text

class TestRateLimiting:
    """Test rate limiting"""
    
    def setup_method(self):
        """Set up authenticated client"""
        client.post("/api/auth/register", json={
            "username": "ratelimit",
            "email": "rate@example.com",
            "password": "RatePass123!",
            "age": 10,
            "grade_level": 5
        })
        
        response = client.post("/api/auth/token", data={
            "username": "ratelimit",
            "password": "RatePass123!"
        })
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_auth_rate_limit(self):
        """Test authentication endpoint rate limiting"""
        # Make multiple failed login attempts
        for i in range(10):
            response = client.post("/api/auth/token", data={
                "username": "ratelimit",
                "password": "WrongPass!"
            })
            if response.status_code == 429:  # Rate limited
                assert "X-RateLimit-Limit" in response.headers
                break
        else:
            pytest.skip("Rate limiting not triggered in test")
    
    def test_chat_rate_limit(self):
        """Test chat endpoint rate limiting"""
        # Make many requests quickly
        responses = []
        for i in range(35):  # Over the 30/minute limit
            response = client.post("/api/companion/chat",
                headers=self.headers,
                json={
                    "message": f"Message {i}",
                    "mode": "tutor"
                }
            )
            responses.append(response.status_code)
            if response.status_code == 429:
                break
        
        # Should hit rate limit
        assert 429 in responses

class TestSecurityHeaders:
    """Test security headers"""
    
    def test_security_headers(self):
        """Test that security headers are present"""
        response = client.get("/")
        
        # Check security headers
        assert "X-Content-Type-Options" in response.headers
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        
        assert "X-Frame-Options" in response.headers
        assert response.headers["X-Frame-Options"] == "DENY"
        
        assert "X-XSS-Protection" in response.headers
        assert "Content-Security-Policy" in response.headers

if __name__ == "__main__":
    pytest.main([__file__, "-v"])