"""
Security Module for Octagon Pro
Implements input validation, data sanitization, password hashing, and rate limiting
"""

import re
import hashlib
import secrets
import json
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Dict, Optional
from html import escape
import hmac

# ============================================================================
# PASSWORD HASHING & VALIDATION
# ============================================================================

class PasswordManager:
    """Handles secure password generation, hashing, and verification"""
    
    @staticmethod
    def hash_password(password: str, salt: Optional[str] = None) -> Dict[str, str]:
        """
        Hash password using PBKDF2-SHA256 with salt
        Returns dict with hashed password and salt for storage
        """
        if not password or len(password) < 6:
            raise ValueError("Password must be at least 6 characters long")
        
        if salt is None:
            salt = secrets.token_hex(32)  # Generate random salt
        
        # PBKDF2 with SHA256
        hashed = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            iterations=100000,
            dklen=32
        )
        
        # Format: pbkdf2_sha256$iterations$salt$hash
        encoded = f"pbkdf2_sha256$100000${salt}${hashed.hex()}"
        
        return {
            'hash': hashed.hex(),
            'salt': salt,
            'encoded': encoded  # Full format for storage
        }
    
    @staticmethod
    def verify_password(password: str, encoded_hash: str) -> bool:
        """Verify password against encoded hash (format: pbkdf2_sha256$iterations$salt$hash)"""
        try:
            if not encoded_hash.startswith('pbkdf2_sha256$'):
                return False
            
            parts = encoded_hash.split('$')
            if len(parts) != 4:
                return False
            
            algorithm, iterations, salt, stored_hash = parts
            iterations = int(iterations)
            
            # Compute hash with stored salt
            computed = hashlib.pbkdf2_hmac(
                'sha256',
                password.encode('utf-8'),
                salt.encode('utf-8'),
                iterations=iterations,
                dklen=32
            ).hex()
            
            return hmac.compare_digest(computed, stored_hash)
        except Exception as e:
            print(f"❌ Password verification error: {e}")
            return False
    
    @staticmethod
    def generate_temporary_password(length: int = 12) -> str:
        """Generate temporary secure password"""
        chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%"
        return ''.join(secrets.choice(chars) for _ in range(length))


# ============================================================================
# INPUT VALIDATION & SANITIZATION
# ============================================================================

class InputValidator:
    """Validates and sanitizes user input"""
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email)) if email else False
    
    @staticmethod
    def validate_username(username: str) -> bool:
        """Validate username (alphanumeric, dots, underscores, hyphens only)"""
        if not username or len(username) < 3 or len(username) > 32:
            return False
        pattern = r'^[a-zA-Z0-9._-]+$'
        return bool(re.match(pattern, username))
    
    @staticmethod
    def validate_phone(phone: str) -> bool:
        """Validate phone number (basic international and Spanish formats)"""
        if not phone:
            return False
        normalized = re.sub(r'[^0-9+]', '', phone)
        digits = re.sub(r'[^0-9]', '', normalized)
        if not digits:
            return False
        if len(digits) < 9 or len(digits) > 12:
            return False
        pattern = r'^\+?[0-9]{9,12}$'
        return bool(re.match(pattern, normalized))
    
    @staticmethod
    def validate_dni(dni: str) -> bool:
        """Validate Spanish DNI/NIE format"""
        pattern = r'^[XYZ]?\d{7,8}[A-Z]$'
        return bool(re.match(pattern, dni.upper())) if dni else False
    
    @staticmethod
    def validate_date(date_str: str) -> bool:
        """Validate ISO date format (YYYY-MM-DD)"""
        try:
            datetime.fromisoformat(date_str)
            return True
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validate_number(value: Any, min_val: float = None, max_val: float = None) -> bool:
        """Validate numeric value within range"""
        try:
            num = float(value)
            if min_val is not None and num < min_val:
                return False
            if max_val is not None and num > max_val:
                return False
            return True
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def sanitize_text(text: str, max_length: int = 500) -> str:
        """Sanitize text input"""
        if not isinstance(text, str):
            return ""
        
        # Remove leading/trailing whitespace
        text = text.strip()
        
        # HTML encode to prevent XSS
        text = escape(text)
        
        # Truncate if too long
        if len(text) > max_length:
            text = text[:max_length]
        
        return text
    
    @staticmethod
    def sanitize_email(email: str) -> str:
        """Sanitize and normalize email"""
        if not isinstance(email, str):
            return ""
        
        email = email.strip().lower()
        if InputValidator.validate_email(email):
            return email
        return ""
    
    @staticmethod
    def sanitize_username(username: str) -> str:
        """Sanitize username"""
        if not isinstance(username, str):
            return ""
        
        username = username.strip().lower()
        # Remove any non-alphanumeric except ._-
        username = re.sub(r'[^a-z0-9._-]', '', username)
        
        if InputValidator.validate_username(username):
            return username
        return ""
    
    @staticmethod
    def sanitize_json(data: str) -> Optional[Dict]:
        """Safely parse and validate JSON"""
        try:
            parsed = json.loads(data)
            # Basic validation - don't allow nested structures deeper than 5 levels
            if InputValidator._check_json_depth(parsed) > 5:
                return None
            return parsed
        except (json.JSONDecodeError, TypeError):
            return None
    
    @staticmethod
    def _check_json_depth(obj, depth=0):
        """Check maximum depth of JSON object"""
        if depth > 10:  # Safety limit
            return depth
        
        if isinstance(obj, dict):
            if obj:
                return max(InputValidator._check_json_depth(v, depth + 1) for v in obj.values())
            return depth
        elif isinstance(obj, list):
            if obj:
                return max(InputValidator._check_json_depth(item, depth + 1) for item in obj)
            return depth
        return depth


# ============================================================================
# RATE LIMITING
# ============================================================================

class RateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(self):
        self.requests: Dict[str, list] = {}
    
    def is_allowed(self, identifier: str, max_requests: int = 10, 
                   time_window: int = 60) -> bool:
        """
        Check if request is allowed based on rate limit
        
        Args:
            identifier: User ID, IP, or unique identifier
            max_requests: Maximum requests allowed
            time_window: Time window in seconds
        
        Returns:
            True if request is allowed, False if rate limited
        """
        now = datetime.now()
        
        # Initialize if not exists
        if identifier not in self.requests:
            self.requests[identifier] = []
        
        # Remove old requests outside time window
        cutoff_time = now - timedelta(seconds=time_window)
        self.requests[identifier] = [
            req_time for req_time in self.requests[identifier]
            if req_time > cutoff_time
        ]
        
        # Check if limit exceeded
        if len(self.requests[identifier]) >= max_requests:
            return False
        
        # Add current request
        self.requests[identifier].append(now)
        return True
    
    def get_remaining(self, identifier: str, max_requests: int = 10,
                      time_window: int = 60) -> int:
        """Get remaining requests for identifier"""
        now = datetime.now()
        
        if identifier not in self.requests:
            return max_requests
        
        cutoff_time = now - timedelta(seconds=time_window)
        recent_requests = [
            req_time for req_time in self.requests[identifier]
            if req_time > cutoff_time
        ]
        
        return max(0, max_requests - len(recent_requests))


# Global rate limiter instance
rate_limiter = RateLimiter()


# ============================================================================
# SECURITY DECORATORS
# ============================================================================

def require_valid_input(**validators):
    """
    Decorator to validate function arguments
    
    Usage:
        @require_valid_input(
            email=InputValidator.validate_email,
            username=InputValidator.validate_username
        )
        def create_user(email, username):
            pass
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Validate keyword arguments
            for param, validator in validators.items():
                if param in kwargs:
                    if not validator(kwargs[param]):
                        raise ValueError(f"Invalid {param}: {kwargs[param]}")
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


def rate_limit(max_requests: int = 10, time_window: int = 60):
    """
    Decorator to apply rate limiting
    
    Usage:
        @rate_limit(max_requests=5, time_window=60)
        def api_endpoint(user_id):
            pass
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            user_id = kwargs.get('user_id') or (args[0] if args else 'anonymous')
            
            if not rate_limiter.is_allowed(str(user_id), max_requests, time_window):
                raise Exception(f"Rate limit exceeded for {user_id}")
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


# ============================================================================
# CSRF TOKEN MANAGEMENT
# ============================================================================

class CSRFTokenManager:
    """CSRF token generation and validation"""
    
    def __init__(self):
        self.tokens: Dict[str, tuple] = {}  # token -> (session_id, expiry)
    
    def generate_token(self, session_id: str, expiry_hours: int = 24) -> str:
        """Generate CSRF token for session"""
        token = secrets.token_urlsafe(32)
        expiry = datetime.now() + timedelta(hours=expiry_hours)
        self.tokens[token] = (session_id, expiry)
        
        # Clean expired tokens
        self._cleanup_expired()
        
        return token
    
    def validate_token(self, token: str, session_id: str) -> bool:
        """Validate CSRF token"""
        if token not in self.tokens:
            return False
        
        stored_session, expiry = self.tokens[token]
        
        # Check expiry
        if datetime.now() > expiry:
            del self.tokens[token]
            return False
        
        # Check session matches
        return stored_session == session_id
    
    def invalidate_token(self, token: str) -> None:
        """Invalidate a token"""
        if token in self.tokens:
            del self.tokens[token]
    
    def _cleanup_expired(self) -> None:
        """Remove expired tokens"""
        now = datetime.now()
        expired = [
            token for token, (_, expiry) in self.tokens.items()
            if now > expiry
        ]
        for token in expired:
            del self.tokens[token]


# Global CSRF manager
csrf_manager = CSRFTokenManager()


# ============================================================================
# SESSION SECURITY
# ============================================================================

class SessionManager:
    """Secure session management"""
    
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
    
    def create_session(self, user_id: str, user_data: Dict[str, Any],
                      duration_hours: int = 24) -> str:
        """Create secure session"""
        session_id = secrets.token_urlsafe(32)
        expiry = datetime.now() + timedelta(hours=duration_hours)
        
        self.sessions[session_id] = {
            'user_id': user_id,
            'user_data': user_data,
            'created': datetime.now(),
            'expiry': expiry,
            'last_activity': datetime.now()
        }
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve session if valid"""
        if session_id not in self.sessions:
            return None
        
        session = self.sessions[session_id]
        
        # Check if expired
        if datetime.now() > session['expiry']:
            del self.sessions[session_id]
            return None
        
        # Update last activity
        session['last_activity'] = datetime.now()
        
        return session
    
    def invalidate_session(self, session_id: str) -> None:
        """Invalidate/logout session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
    
    def cleanup_expired(self) -> None:
        """Remove expired sessions"""
        now = datetime.now()
        expired = [
            session_id for session_id, data in self.sessions.items()
            if now > data['expiry']
        ]
        for session_id in expired:
            del self.sessions[session_id]


# Global session manager
session_manager = SessionManager()
