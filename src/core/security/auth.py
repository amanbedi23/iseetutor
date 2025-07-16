"""
Authentication and authorization module for ISEE Tutor.
Implements JWT-based authentication with role-based access control.
"""

from datetime import datetime, timedelta
from typing import Optional, Union, List
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, validator
import secrets
import os

from src.database.base import get_db
from src.database.models import User

# Security configuration
SECRET_KEY = os.environ.get("SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

# Pydantic models
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    username: Optional[str] = None
    scopes: List[str] = []

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    age: int
    grade_level: int
    parent_email: Optional[EmailStr] = None
    
    @validator('username')
    def username_alphanumeric(cls, v):
        assert v.isalnum(), 'Username must be alphanumeric'
        assert len(v) >= 3, 'Username must be at least 3 characters'
        assert len(v) <= 20, 'Username must be at most 20 characters'
        return v
    
    @validator('password')
    def password_strength(cls, v):
        assert len(v) >= 8, 'Password must be at least 8 characters'
        assert any(c.isupper() for c in v), 'Password must contain uppercase letter'
        assert any(c.islower() for c in v), 'Password must contain lowercase letter'
        assert any(c.isdigit() for c in v), 'Password must contain digit'
        return v
    
    @validator('age')
    def age_valid(cls, v):
        assert 5 <= v <= 18, 'Age must be between 5 and 18'
        return v
    
    @validator('grade_level')
    def grade_valid(cls, v):
        assert 1 <= v <= 12, 'Grade level must be between 1 and 12'
        return v

class UserLogin(BaseModel):
    username: str
    password: str

# Utility functions
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict) -> str:
    """Create a JWT refresh token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_token(token: str) -> dict:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

# Database functions
def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """Get user by username."""
    return db.query(User).filter(User.username == username).first()

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get user by email."""
    return db.query(User).filter(User.email == email).first()

def create_user(db: Session, user: UserCreate) -> User:
    """Create a new user."""
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=get_password_hash(user.password),
        age=user.age,
        grade_level=user.grade_level,
        parent_email=user.parent_email,
        role="student",  # Default role
        metadata={}
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """Authenticate a user."""
    user = get_user_by_username(db, username)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user

# Dependency functions
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Get the current authenticated user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = decode_token(token)
    if payload is None or payload.get("type") != "access":
        raise credentials_exception
    
    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception
    
    user = get_user_by_username(db, username=username)
    if user is None:
        raise credentials_exception
    
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get the current active user."""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# Role-based access control
class RoleChecker:
    """Check if user has required role."""
    
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles
    
    def __call__(self, user: User = Depends(get_current_active_user)) -> User:
        if user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        return user

# Create role dependencies
require_student = RoleChecker(["student", "parent", "teacher", "admin"])

def require_role(role: str):
    """Create a dependency that requires a specific role or higher."""
    role_hierarchy = {
        "student": ["student", "parent", "teacher", "admin"],
        "parent": ["parent", "teacher", "admin"],
        "teacher": ["teacher", "admin"],
        "admin": ["admin"]
    }
    allowed_roles = role_hierarchy.get(role, [role])
    return RoleChecker(allowed_roles)
require_parent = RoleChecker(["parent", "teacher", "admin"])
require_teacher = RoleChecker(["teacher", "admin"])
require_admin = RoleChecker(["admin"])

# API Key authentication for services
class APIKeyAuth:
    """API key authentication for internal services."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    def __call__(self, api_key: str = Depends(oauth2_scheme)) -> bool:
        if api_key != self.api_key:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid API key"
            )
        return True

# Create service API key
SERVICE_API_KEY = os.environ.get("SERVICE_API_KEY", secrets.token_urlsafe(32))
require_service_auth = APIKeyAuth(SERVICE_API_KEY)