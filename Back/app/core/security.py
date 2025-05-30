"""
Security utilities for JWT authentication and password hashing.

This module provides:
- Password hashing and verification using bcrypt
- JWT access token generation and validation
- JWT refresh token generation and validation
- Token utilities and security helpers
"""

import secrets
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Union
from uuid import UUID

from jose import JWTError, jwt
from passlib.context import CryptContext
from passlib.exc import InvalidHashError

from app.core.config import settings


# Password hashing context
pwd_context = CryptContext(
    schemes=settings.BCRYPT_SCHEMES,
    default="bcrypt",
    bcrypt__rounds=settings.BCRYPT_ROUNDS,
)


class SecurityError(Exception):
    """Base exception for security-related errors."""
    pass


class TokenError(SecurityError):
    """Exception raised for token-related errors."""
    pass


class PasswordError(SecurityError):
    """Exception raised for password-related errors."""
    pass


# =============================================================================
# PASSWORD HASHING AND VALIDATION
# =============================================================================

def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: Plain text password to hash
        
    Returns:
        Hashed password string
        
    Raises:
        PasswordError: If password hashing fails
    """
    try:
        if not password:
            raise PasswordError("Password cannot be empty")
        
        return pwd_context.hash(password)
    except Exception as e:
        raise PasswordError(f"Failed to hash password: {str(e)}")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.
    
    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password to verify against
        
    Returns:
        True if password matches, False otherwise
        
    Raises:
        PasswordError: If password verification fails
    """
    try:
        if not plain_password or not hashed_password:
            return False
            
        return pwd_context.verify(plain_password, hashed_password)
    except InvalidHashError:
        return False
    except Exception as e:
        raise PasswordError(f"Failed to verify password: {str(e)}")


def validate_password_strength(password: str) -> Dict[str, Union[bool, list]]:
    """
    Validate password strength according to security requirements.
    
    Args:
        password: Password to validate
        
    Returns:
        Dictionary with validation results:
        {
            "valid": bool,
            "errors": list[str],
            "requirements": dict
        }
    """
    errors = []
    requirements = {
        "min_length": False,
        "has_uppercase": False,
        "has_lowercase": False,
        "has_digit": False,
        "has_special": False,
    }
    
    if not password:
        errors.append("Password is required")
        return {"valid": False, "errors": errors, "requirements": requirements}
    
    # Check minimum length
    if len(password) >= settings.PASSWORD_MIN_LENGTH:
        requirements["min_length"] = True
    else:
        errors.append(f"Password must be at least {settings.PASSWORD_MIN_LENGTH} characters long")
    
    # Check uppercase requirement
    if settings.PASSWORD_REQUIRE_UPPERCASE:
        if re.search(r'[A-Z]', password):
            requirements["has_uppercase"] = True
        else:
            errors.append("Password must contain at least one uppercase letter")
    else:
        requirements["has_uppercase"] = True
    
    # Check lowercase requirement
    if settings.PASSWORD_REQUIRE_LOWERCASE:
        if re.search(r'[a-z]', password):
            requirements["has_lowercase"] = True
        else:
            errors.append("Password must contain at least one lowercase letter")
    else:
        requirements["has_lowercase"] = True
    
    # Check digit requirement
    if settings.PASSWORD_REQUIRE_DIGITS:
        if re.search(r'[0-9]', password):
            requirements["has_digit"] = True
        else:
            errors.append("Password must contain at least one digit")
    else:
        requirements["has_digit"] = True
    
    # Check special character requirement
    if settings.PASSWORD_REQUIRE_SPECIAL:
        if re.search(r'[!@#$%^&*(),.?\":{}|<>]', password):
            requirements["has_special"] = True
        else:
            errors.append("Password must contain at least one special character")
    else:
        requirements["has_special"] = True
    
    valid = len(errors) == 0
    
    return {
        "valid": valid,
        "errors": errors,
        "requirements": requirements
    }


# =============================================================================
# JWT TOKEN GENERATION AND VALIDATION
# =============================================================================

def create_access_token(
    data: Dict[str, Any], 
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Dictionary of claims to include in the token
        expires_delta: Optional custom expiration time
        
    Returns:
        JWT token string
        
    Raises:
        TokenError: If token creation fails
    """
    try:
        to_encode = data.copy()
        
        # Set expiration time
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(
                minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
            )
        
        # Add standard JWT claims
        to_encode.update({
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "iss": settings.JWT_ISSUER,
            "aud": settings.JWT_AUDIENCE,
            "type": "access",
            "jti": secrets.token_urlsafe(16),  # JWT ID for uniqueness
        })
        
        encoded_jwt = jwt.encode(
            to_encode, 
            settings.JWT_SECRET_KEY, 
            algorithm=settings.JWT_ALGORITHM
        )
        
        return encoded_jwt
    except Exception as e:
        raise TokenError(f"Failed to create access token: {str(e)}")


def create_refresh_token(
    data: Dict[str, Any], 
    expires_delta: Optional[timedelta] = None,
    remember_me: bool = False
) -> str:
    """
    Create a JWT refresh token.
    
    Args:
        data: Dictionary of claims to include in the token
        expires_delta: Optional custom expiration time
        remember_me: If True, use extended expiration time
        
    Returns:
        JWT refresh token string
        
    Raises:
        TokenError: If token creation fails
    """
    try:
        to_encode = data.copy()
        
        # Set expiration time based on remember_me
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        elif remember_me:
            expire = datetime.now(timezone.utc) + timedelta(
                days=settings.JWT_REFRESH_TOKEN_REMEMBER_ME_EXPIRE_DAYS
            )
        else:
            expire = datetime.now(timezone.utc) + timedelta(
                days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
            )
        
        # Add standard JWT claims
        to_encode.update({
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "iss": settings.JWT_ISSUER,
            "aud": settings.JWT_AUDIENCE,
            "type": "refresh",
            "remember_me": remember_me,
            "jti": secrets.token_urlsafe(32),  # Longer JTI for refresh tokens
        })
        
        encoded_jwt = jwt.encode(
            to_encode, 
            settings.JWT_SECRET_KEY, 
            algorithm=settings.JWT_ALGORITHM
        )
        
        return encoded_jwt
    except Exception as e:
        raise TokenError(f"Failed to create refresh token: {str(e)}")


def verify_token(token: str, token_type: str = "access") -> Dict[str, Any]:
    """
    Verify and decode a JWT token.
    
    Args:
        token: JWT token string to verify
        token_type: Expected token type ("access" or "refresh")
        
    Returns:
        Decoded token payload
        
    Raises:
        TokenError: If token verification fails
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            audience=settings.JWT_AUDIENCE,
            issuer=settings.JWT_ISSUER,
        )
        
        # Verify token type
        if payload.get("type") != token_type:
            raise TokenError(f"Invalid token type. Expected {token_type}")
        
        # Check if token is expired
        exp = payload.get("exp")
        if exp and datetime.fromtimestamp(exp, timezone.utc) < datetime.now(timezone.utc):
            raise TokenError("Token has expired")
        
        return payload
        
    except JWTError as e:
        raise TokenError(f"Invalid token: {str(e)}")
    except Exception as e:
        raise TokenError(f"Token verification failed: {str(e)}")


def decode_token(token: str) -> Dict[str, Any]:
    """
    Decode a JWT token without verification (for inspection).
    
    Args:
        token: JWT token string to decode
        
    Returns:
        Decoded token payload
        
    Raises:
        TokenError: If token decoding fails
    """
    try:
        # Decode without verification
        payload = jwt.decode(
            token,
            options={"verify_signature": False, "verify_exp": False}
        )
        return payload
    except Exception as e:
        raise TokenError(f"Failed to decode token: {str(e)}")


def extract_user_id(token: str) -> Optional[str]:
    """
    Extract user ID from a JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        User ID if found, None otherwise
    """
    try:
        payload = decode_token(token)
        return payload.get("sub")  # Subject claim typically contains user ID
    except TokenError:
        return None


def extract_user_info(token: str) -> Dict[str, Any]:
    """
    Extract user information from a JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        Dictionary with user information
    """
    try:
        payload = decode_token(token)
        return {
            "user_id": payload.get("sub"),
            "username": payload.get("username"),
            "email": payload.get("email"),
            "role": payload.get("role"),
            "department": payload.get("department"),
            "permissions": payload.get("permissions", []),
            "is_superuser": payload.get("is_superuser", False),
            "expires_at": payload.get("exp"),
            "issued_at": payload.get("iat"),
            "token_type": payload.get("type"),
            "remember_me": payload.get("remember_me", False),
        }
    except TokenError:
        return {}


def is_token_expired(token: str) -> bool:
    """
    Check if a JWT token is expired.
    
    Args:
        token: JWT token string
        
    Returns:
        True if token is expired, False otherwise
    """
    try:
        payload = decode_token(token)
        exp = payload.get("exp")
        if not exp:
            return True
        
        return datetime.fromtimestamp(exp, timezone.utc) < datetime.now(timezone.utc)
    except TokenError:
        return True


def get_token_expiry(token: str) -> Optional[datetime]:
    """
    Get the expiration time of a JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        Expiration datetime if found, None otherwise
    """
    try:
        payload = decode_token(token)
        exp = payload.get("exp")
        if exp:
            return datetime.fromtimestamp(exp, timezone.utc)
        return None
    except TokenError:
        return None


# =============================================================================
# SECURITY UTILITIES
# =============================================================================

def generate_secure_token(length: int = 32) -> str:
    """
    Generate a cryptographically secure random token.
    
    Args:
        length: Length of the token in bytes
        
    Returns:
        URL-safe base64 encoded token string
    """
    return secrets.token_urlsafe(length)


def create_password_reset_token(user_id: str, expires_minutes: int = 30) -> str:
    """
    Create a password reset token.
    
    Args:
        user_id: User ID for whom to create the token
        expires_minutes: Token expiration time in minutes
        
    Returns:
        Password reset token
    """
    data = {
        "sub": user_id,
        "type": "password_reset",
        "purpose": "reset_password",
    }
    expires_delta = timedelta(minutes=expires_minutes)
    return create_access_token(data, expires_delta)


def verify_password_reset_token(token: str) -> Optional[str]:
    """
    Verify a password reset token and extract user ID.
    
    Args:
        token: Password reset token
        
    Returns:
        User ID if token is valid, None otherwise
    """
    try:
        payload = verify_token(token, "access")
        if payload.get("type") == "password_reset":
            return payload.get("sub")
    except TokenError:
        pass
    return None


def create_email_verification_token(user_id: str, email: str) -> str:
    """
    Create an email verification token.
    
    Args:
        user_id: User ID
        email: Email address to verify
        
    Returns:
        Email verification token
    """
    data = {
        "sub": user_id,
        "email": email,
        "type": "email_verification",
        "purpose": "verify_email",
    }
    expires_delta = timedelta(hours=24)  # 24 hour expiry for email verification
    return create_access_token(data, expires_delta)


def verify_email_verification_token(token: str) -> Optional[Dict[str, str]]:
    """
    Verify an email verification token.
    
    Args:
        token: Email verification token
        
    Returns:
        Dictionary with user_id and email if valid, None otherwise
    """
    try:
        payload = verify_token(token, "access")
        if payload.get("type") == "email_verification":
            return {
                "user_id": payload.get("sub"),
                "email": payload.get("email")
            }
    except TokenError:
        pass
    return None


# =============================================================================
# AUTHENTICATION HELPERS
# =============================================================================

def create_user_tokens(
    user_id: str,
    username: str,
    email: str,
    role: str = None,
    department: str = None,
    permissions: list = None,
    is_superuser: bool = False,
    remember_me: bool = False
) -> Dict[str, str]:
    """
    Create both access and refresh tokens for a user.
    
    Args:
        user_id: User ID
        username: Username
        email: User email
        role: User role
        department: User department
        permissions: List of user permissions
        is_superuser: Whether user is superuser
        remember_me: Whether to create long-lived refresh token
        
    Returns:
        Dictionary containing access_token and refresh_token
    """
    token_data = {
        "sub": user_id,
        "username": username,
        "email": email,
        "role": role,
        "department": department,
        "permissions": permissions or [],
        "is_superuser": is_superuser,
    }
    
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data, remember_me=remember_me)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # seconds
    }


def refresh_access_token(refresh_token: str) -> Dict[str, str]:
    """
    Create a new access token from a valid refresh token.
    
    Args:
        refresh_token: Valid refresh token
        
    Returns:
        Dictionary containing new access_token
        
    Raises:
        TokenError: If refresh token is invalid
    """
    try:
        # Verify refresh token
        payload = verify_token(refresh_token, "refresh")
        
        # Extract user data for new access token
        token_data = {
            "sub": payload.get("sub"),
            "username": payload.get("username"),
            "email": payload.get("email"),
            "role": payload.get("role"),
            "department": payload.get("department"),
            "permissions": payload.get("permissions", []),
            "is_superuser": payload.get("is_superuser", False),
        }
        
        new_access_token = create_access_token(token_data)
        
        return {
            "access_token": new_access_token,
            "token_type": "bearer",
            "expires_in": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }
        
    except TokenError:
        raise
    except Exception as e:
        raise TokenError(f"Failed to refresh access token: {str(e)}")


# =============================================================================
# TOKEN BLACKLIST UTILITIES (For future implementation)
# =============================================================================

class TokenBlacklist:
    """
    Token blacklist for managing revoked tokens.
    Note: This is a placeholder for future Redis-based implementation.
    """
    
    @staticmethod
    def add_to_blacklist(token: str, expires_at: datetime) -> None:
        """Add a token to the blacklist."""
        # TODO: Implement with Redis
        pass
    
    @staticmethod
    def is_blacklisted(token: str) -> bool:
        """Check if a token is blacklisted."""
        # TODO: Implement with Redis
        return False
    
    @staticmethod
    def cleanup_expired_tokens() -> None:
        """Remove expired tokens from blacklist."""
        # TODO: Implement with Redis
        pass


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Exceptions
    "SecurityError",
    "TokenError", 
    "PasswordError",
    
    # Password functions
    "hash_password",
    "verify_password",
    "validate_password_strength",
    
    # JWT functions
    "create_access_token",
    "create_refresh_token",
    "verify_token",
    "decode_token",
    "extract_user_id",
    "extract_user_info",
    "is_token_expired",
    "get_token_expiry",
    
    # Security utilities
    "generate_secure_token",
    "create_password_reset_token",
    "verify_password_reset_token",
    "create_email_verification_token",
    "verify_email_verification_token",
    
    # Authentication helpers
    "create_user_tokens",
    "refresh_access_token",
    
    # Blacklist utilities
    "TokenBlacklist",
]
