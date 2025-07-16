"""
Input validation and sanitization for ISEE Tutor.
Prevents SQL injection, XSS, and other input-based attacks.
"""

import re
import html
from typing import Optional, List, Any
from pydantic import BaseModel, field_validator, Field
import bleach

# Allowed HTML tags for content that may contain formatting
ALLOWED_TAGS = ['p', 'br', 'strong', 'em', 'u', 'li', 'ul', 'ol']
ALLOWED_ATTRIBUTES = {}

# Regex patterns for validation
USERNAME_PATTERN = re.compile(r'^[a-zA-Z0-9_]{3,20}$')
SAFE_FILENAME_PATTERN = re.compile(r'^[a-zA-Z0-9_\-\.]{1,255}$')
SQL_INJECTION_PATTERN = re.compile(
    r'(\b(union|select|insert|update|delete|drop|create|alter|exec|execute|script|javascript|onclick)\b)',
    re.IGNORECASE
)

class ChatMessageRequest(BaseModel):
    """Validated chat message request."""
    message: str = Field(..., min_length=1, max_length=1000)
    mode: str = Field(..., pattern='^(tutor|friend|hybrid)$')
    user_context: Optional[dict] = Field(default_factory=dict)
    
    @field_validator('message')
    def sanitize_message(cls, v):
        # Remove any HTML tags
        v = bleach.clean(v, tags=[], strip=True)
        # Check for SQL injection attempts
        if SQL_INJECTION_PATTERN.search(v):
            raise ValueError('Invalid message content')
        return v.strip()
    
    @field_validator('user_context')
    def validate_context(cls, v):
        if v:
            # Ensure only allowed keys
            allowed_keys = {'age', 'grade_level', 'session_id'}
            if not all(k in allowed_keys for k in v.keys()):
                raise ValueError('Invalid context keys')
            
            # Validate values
            if 'age' in v and not (5 <= v['age'] <= 18):
                raise ValueError('Invalid age')
            if 'grade_level' in v and not (1 <= v['grade_level'] <= 12):
                raise ValueError('Invalid grade level')
        return v

class ModeSwitchRequest(BaseModel):
    """Validated mode switch request."""
    new_mode: str = Field(..., pattern='^(tutor|friend|hybrid)$')

class QuizAnswerRequest(BaseModel):
    """Validated quiz answer submission."""
    quiz_id: str = Field(..., min_length=1, max_length=50)
    question_id: str = Field(..., min_length=1, max_length=50)
    answer: str = Field(..., min_length=1, max_length=500)
    time_taken: int = Field(..., ge=0, le=3600)  # Max 1 hour per question
    
    @field_validator('quiz_id', 'question_id')
    def validate_ids(cls, v):
        # Ensure IDs are alphanumeric with dashes/underscores
        if not re.match(r'^[a-zA-Z0-9_\-]+$', v):
            raise ValueError('Invalid ID format')
        return v
    
    @field_validator('answer')
    def sanitize_answer(cls, v):
        return bleach.clean(v, tags=[], strip=True).strip()

class ContentSearchRequest(BaseModel):
    """Validated content search request."""
    query: str = Field(..., min_length=1, max_length=200)
    subject: Optional[str] = Field(None, pattern='^(math|verbal|reading|quantitative)$')
    limit: int = Field(10, ge=1, le=50)
    
    @field_validator('query')
    def sanitize_query(cls, v):
        # Remove special characters that could be used for injection
        v = re.sub(r'[^\w\s\-]', '', v)
        if SQL_INJECTION_PATTERN.search(v):
            raise ValueError('Invalid search query')
        return v.strip()

class UserPreferencesUpdate(BaseModel):
    """Validated user preferences update."""
    volume: Optional[float] = Field(None, ge=0.0, le=1.0)
    speech_rate: Optional[float] = Field(None, ge=0.5, le=2.0)
    difficulty_level: Optional[int] = Field(None, ge=1, le=5)
    subjects: Optional[List[str]] = None
    
    @field_validator('subjects')
    def validate_subjects(cls, v):
        if v:
            valid_subjects = {'math', 'verbal', 'reading', 'quantitative', 'science'}
            if not all(s in valid_subjects for s in v):
                raise ValueError('Invalid subject')
        return v

class FileUploadRequest(BaseModel):
    """Validated file upload parameters."""
    filename: str = Field(..., min_length=1, max_length=255)
    content_type: str = Field(..., pattern='^(application/pdf|image/png|image/jpeg)$')
    size: int = Field(..., gt=0, le=10*1024*1024)  # Max 10MB
    
    @field_validator('filename')
    def validate_filename(cls, v):
        if not SAFE_FILENAME_PATTERN.match(v):
            raise ValueError('Invalid filename')
        # Prevent directory traversal
        if '..' in v or '/' in v or '\\' in v:
            raise ValueError('Invalid filename')
        return v

# Utility functions
def sanitize_html(content: str, allowed_tags: List[str] = None) -> str:
    """Sanitize HTML content, keeping only allowed tags."""
    if allowed_tags is None:
        allowed_tags = ALLOWED_TAGS
    return bleach.clean(
        content,
        tags=allowed_tags,
        attributes=ALLOWED_ATTRIBUTES,
        strip=True
    )

def sanitize_text(text: str) -> str:
    """Sanitize plain text, removing all HTML and escaping special characters."""
    # Remove all HTML
    text = bleach.clean(text, tags=[], strip=True)
    # Escape any remaining HTML entities
    text = html.escape(text)
    return text.strip()

def validate_table_name(table_name: str) -> bool:
    """Validate database table name to prevent SQL injection."""
    # Whitelist of allowed table names
    allowed_tables = {
        'users', 'sessions', 'progress', 'questions', 
        'quizzes', 'quiz_results', 'content', 'audio_logs'
    }
    return table_name in allowed_tables

def validate_column_name(column_name: str) -> bool:
    """Validate database column name to prevent SQL injection."""
    # Only allow alphanumeric and underscore
    return re.match(r'^[a-zA-Z0-9_]+$', column_name) is not None

def validate_sort_order(order: str) -> bool:
    """Validate sort order parameter."""
    return order.upper() in ['ASC', 'DESC']

def sanitize_path(path: str) -> Optional[str]:
    """Sanitize file path to prevent directory traversal."""
    # Remove any directory traversal attempts
    if '..' in path or path.startswith('/'):
        return None
    
    # Only allow alphanumeric, dash, underscore, and forward slash
    if not re.match(r'^[a-zA-Z0-9_\-/]+$', path):
        return None
    
    return path

def validate_message(message: str) -> str:
    """
    Validate and sanitize a message.
    
    Args:
        message: Raw message string
        
    Returns:
        Sanitized message
        
    Raises:
        ValueError: If message is invalid
    """
    if not message or not message.strip():
        raise ValueError("Message cannot be empty")
    
    # Sanitize the message
    return sanitize_text(message)

def validate_json_structure(data: dict, required_keys: set, optional_keys: set = None) -> bool:
    """Validate JSON structure has required keys and no extra keys."""
    if optional_keys is None:
        optional_keys = set()
    
    allowed_keys = required_keys | optional_keys
    data_keys = set(data.keys())
    
    # Check all required keys are present
    if not required_keys.issubset(data_keys):
        return False
    
    # Check no extra keys
    if not data_keys.issubset(allowed_keys):
        return False
    
    return True

# Rate limiting helpers
class RateLimitExceeded(Exception):
    """Raised when rate limit is exceeded."""
    pass

def get_rate_limit_key(user_id: str, endpoint: str) -> str:
    """Generate rate limit key for Redis."""
    return f"rate_limit:{user_id}:{endpoint}"