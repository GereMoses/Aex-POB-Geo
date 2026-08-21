"""
Production-ready input validation and sanitization utilities
"""

import re
import html
import json
import time
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, validator, Field
from fastapi import HTTPException, status
import logging

logger = logging.getLogger(__name__)

class SecurityValidator:
    """Security-focused input validation and sanitization"""
    
    @staticmethod
    def sanitize_string(value: str, max_length: int = 1000) -> str:
        """Sanitize string input to prevent XSS and injection attacks"""
        if not isinstance(value, str):
            return str(value)
        
        # Remove null bytes
        value = value.replace('\x00', '')
        
        # HTML entity encoding
        value = html.escape(value)
        
        # Limit length
        if len(value) > max_length:
            value = value[:max_length]
        
        # Remove potentially dangerous characters
        dangerous_chars = ['<', '>', '"', "'", '&', '\x00', '\n', '\r', '\t']
        for char in dangerous_chars:
            value = value.replace(char, '')
        
        return value.strip()
    
    @staticmethod
    def validate_email(email: str) -> str:
        """Validate and sanitize email address"""
        if not isinstance(email, str):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid email format"
            )
        
        email = email.strip().lower()
        
        # Basic email regex validation
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid email format"
            )
        
        # Length validation
        if len(email) > 254:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email address too long"
            )
        
        return email
    
    @staticmethod
    def validate_phone(phone: str) -> str:
        """Validate and sanitize phone number"""
        if not isinstance(phone, str):
            return str(phone)
        
        # Remove non-numeric characters except +, -, (, ), and space
        phone = re.sub(r'[^\d\+\-\(\)\s]', '', phone)
        
        # Basic phone validation (at least 10 digits)
        digits = re.sub(r'\D', '', phone)
        if len(digits) < 10 or len(digits) > 15:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid phone number format"
            )
        
        return phone
    
    @staticmethod
    def validate_username(username: str) -> str:
        """Validate and sanitize username"""
        if not isinstance(username, str):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid username format"
            )
        
        username = username.strip()
        
        # Length validation
        if len(username) < 3 or len(username) > 50:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username must be between 3 and 50 characters"
            )
        
        # Allowed characters (alphanumeric, underscore, hyphen)
        if not re.match(r'^[a-zA-Z0-9_-]+$', username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username can only contain letters, numbers, underscores, and hyphens"
            )
        
        return username.lower()
    
    @staticmethod
    def validate_id(id_value: Union[int, str], field_name: str = "ID") -> int:
        """Validate ID parameter"""
        try:
            if isinstance(id_value, str):
                id_value = int(id_value)
            elif isinstance(id_value, int):
                pass
            else:
                raise ValueError(f"Invalid {field_name} type")
            
            if id_value <= 0:
                raise ValueError(f"{field_name} must be positive")
            
            return id_value
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid {field_name} format"
            )
    
    @staticmethod
    def validate_pagination(skip: int = 0, limit: int = 100) -> tuple[int, int]:
        """Validate pagination parameters"""
        # Validate skip
        if skip < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Skip parameter must be non-negative"
            )
        
        # Validate limit
        if limit <= 0 or limit > 1000:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Limit parameter must be between 1 and 1000"
            )
        
        return skip, limit
    
    @staticmethod
    def sanitize_json_input(data: Any) -> Any:
        """Sanitize JSON input to prevent injection"""
        if isinstance(data, str):
            try:
                # Parse and re-serialize to ensure valid JSON
                parsed = json.loads(data)
                return SecurityValidator.sanitize_json_input(parsed)
            except json.JSONDecodeError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid JSON format"
                )
        elif isinstance(data, dict):
            return {
                SecurityValidator.sanitize_string(str(k)): SecurityValidator.sanitize_json_input(v)
                for k, v in data.items()
            }
        elif isinstance(data, list):
            return [SecurityValidator.sanitize_json_input(item) for item in data]
        elif isinstance(data, str):
            return SecurityValidator.sanitize_string(data)
        else:
            return data
    
    @staticmethod
    def validate_sql_keywords(value: str) -> str:
        """Check for SQL injection patterns"""
        if not isinstance(value, str):
            return str(value)
        
        # Common SQL injection patterns
        sql_patterns = [
            r'(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION|SCRIPT)\b)',
            r'(--|#|/\*|\*/|;)',
            r'(\bOR\b|\bAND\b).*=.*\bOR\b',
            r'(\bWHERE\b.*\bOR\b)',
            r'(\bWHERE\b.*\bAND\b)',
            r'(\bWHERE\b.*--)',
            r'(\bWHERE\b.*#)'
        ]
        
        value_lower = value.lower()
        for pattern in sql_patterns:
            if re.search(pattern, value_lower, re.IGNORECASE):
                logger.warning(f"Potential SQL injection detected: {value}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid input detected"
                )
        
        return value

class PaginationParams(BaseModel):
    """Standardized pagination parameters"""
    skip: int = Field(0, ge=0, le=10000, description="Number of items to skip")
    limit: int = Field(100, ge=1, le=1000, description="Number of items to return")
    
    @validator('skip')
    def validate_skip(cls, v):
        return max(0, v)
    
    @validator('limit')
    def validate_limit(cls, v):
        return max(1, min(1000, v))

class SearchParams(BaseModel):
    """Standardized search parameters"""
    query: Optional[str] = Field(None, min_length=1, max_length=100, description="Search query")
    sort_by: Optional[str] = Field(None, max_length=50, description="Field to sort by")
    sort_order: Optional[str] = Field("asc", regex="^(asc|desc)$", description="Sort order")
    
    @validator('query')
    def validate_query(cls, v):
        if v:
            return SecurityValidator.sanitize_string(v)
        return v

def validate_input_data(data: Dict[str, Any], schema: BaseModel) -> Dict[str, Any]:
    """Validate input data against Pydantic schema"""
    try:
        # Sanitize all string values
        sanitized_data = {}
        for key, value in data.items():
            if isinstance(value, str):
                sanitized_data[key] = SecurityValidator.sanitize_string(value)
            else:
                sanitized_data[key] = value
        
        # Validate against schema
        validated = schema(**sanitized_data)
        return validated.dict(exclude_unset=True)
    except Exception as e:
        logger.error(f"Input validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid input data: {str(e)}"
        )

def validate_file_upload(file_data: bytes, max_size: int = 10 * 1024 * 1024, allowed_types: List[str] = None) -> bytes:
    """Validate uploaded file"""
    if len(file_data) > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size is {max_size} bytes"
        )
    
    # Check file type if provided
    if allowed_types:
        # Simple file type detection (in production, use python-magic)
        file_header = file_data[:100] if len(file_data) > 100 else file_data
        
        # Check for common file signatures
        file_signatures = {
            'image/jpeg': b'\xff\xd8\xff',
            'image/png': b'\x89PNG\r\n\x1a\n',
            'application/pdf': b'%PDF',
            'text/plain': b'\xef\xbb\xbf'  # UTF-8 BOM
        }
        
        detected_type = None
        for file_type, signature in file_signatures.items():
            if file_header.startswith(signature):
                detected_type = file_type
                break
        
        if detected_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type {detected_type} not allowed"
            )
    
    return file_data

class AuditLogger:
    """Audit logging for security events"""
    
    @staticmethod
    def log_security_event(event_type: str, details: Dict[str, Any], user_id: Optional[int] = None, ip_address: Optional[str] = None):
        """Log security events for audit trail"""
        log_entry = {
            "timestamp": time.time(),
            "event_type": event_type,
            "user_id": user_id,
            "ip_address": ip_address,
            "details": details
        }
        
        logger.warning(f"SECURITY EVENT: {event_type} - {json.dumps(log_entry)}")
        
        # In production, this would go to a secure audit log
        # For now, we'll use the regular logger
