"""
Pydantic schemas for authentication endpoints.

This module defines request and response models for:
- User login (with remember me support)
- Token refresh
- User logout
- User profile retrieval
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field, validator


# =============================================================================
# REQUEST SCHEMAS
# =============================================================================

class LoginRequest(BaseModel):
    """Request schema for user login."""
    
    username: str = Field(
        ..., 
        min_length=3, 
        max_length=50,
        description="Username or email address"
    )
    password: str = Field(
        ..., 
        min_length=8, 
        max_length=100,
        description="User password"
    )
    remember_me: bool = Field(
        default=False,
        description="If true, refresh token will have extended expiry"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "username": "admin",
                "password": "AdminPassword123",
                "remember_me": False
            }
        }


class RefreshTokenRequest(BaseModel):
    """Request schema for token refresh."""
    
    refresh_token: str = Field(
        ...,
        description="Valid refresh token to exchange for new access token"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }


class LogoutRequest(BaseModel):
    """Request schema for user logout."""
    
    refresh_token: str = Field(
        ...,
        description="Refresh token to invalidate during logout"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }


# =============================================================================
# RESPONSE SCHEMAS
# =============================================================================

class TokenResponse(BaseModel):
    """Response schema for successful authentication."""
    
    access_token: str = Field(
        ...,
        description="JWT access token for API authentication"
    )
    refresh_token: str = Field(
        ...,
        description="JWT refresh token for obtaining new access tokens"
    )
    token_type: str = Field(
        default="bearer",
        description="Token type (always 'bearer')"
    )
    expires_in: int = Field(
        ...,
        description="Access token expiration time in seconds"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 900
            }
        }


class AccessTokenResponse(BaseModel):
    """Response schema for token refresh (only access token)."""
    
    access_token: str = Field(
        ...,
        description="New JWT access token"
    )
    token_type: str = Field(
        default="bearer",
        description="Token type (always 'bearer')"
    )
    expires_in: int = Field(
        ...,
        description="Access token expiration time in seconds"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 900
            }
        }


class UserProfile(BaseModel):
    """Response schema for user profile information."""
    
    user_id: str = Field(
        ...,
        description="Unique user identifier"
    )
    username: str = Field(
        ...,
        description="Username"
    )
    email: EmailStr = Field(
        ...,
        description="User email address"
    )
    role: str = Field(
        ...,
        description="User role (e.g., 'admin', 'user')"
    )
    department: Optional[str] = Field(
        default=None,
        description="User department (if assigned)"
    )
    permissions: List[str] = Field(
        default_factory=list,
        description="List of user permissions"
    )
    is_superuser: bool = Field(
        default=False,
        description="Whether user has superuser privileges"
    )
    is_active: bool = Field(
        default=True,
        description="Whether user account is active"
    )
    created_at: Optional[datetime] = Field(
        default=None,
        description="Account creation timestamp"
    )
    last_login: Optional[datetime] = Field(
        default=None,
        description="Last login timestamp"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "user_id": "admin_001",
                "username": "admin",
                "email": "admin@aidock.com",
                "role": "admin",
                "department": "IT",
                "permissions": ["read", "write", "admin", "manage_users"],
                "is_superuser": True,
                "is_active": True,
                "created_at": "2024-01-01T00:00:00Z",
                "last_login": "2024-12-01T10:30:00Z"
            }
        }


class LogoutResponse(BaseModel):
    """Response schema for successful logout."""
    
    message: str = Field(
        default="Successfully logged out",
        description="Logout confirmation message"
    )
    logged_out_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Logout timestamp"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "message": "Successfully logged out",
                "logged_out_at": "2024-12-01T15:30:45Z"
            }
        }


# =============================================================================
# ERROR SCHEMAS
# =============================================================================

class ErrorDetail(BaseModel):
    """Error detail schema."""
    
    type: str = Field(
        ...,
        description="Error type"
    )
    message: str = Field(
        ...,
        description="Human-readable error message"
    )
    code: Optional[str] = Field(
        default=None,
        description="Error code for programmatic handling"
    )


class ErrorResponse(BaseModel):
    """Standard error response schema."""
    
    error: str = Field(
        ...,
        description="Error category"
    )
    message: str = Field(
        ...,
        description="Error message"
    )
    details: Optional[List[ErrorDetail]] = Field(
        default=None,
        description="Additional error details"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Error timestamp"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "error": "authentication_failed",
                "message": "Invalid username or password",
                "details": [
                    {
                        "type": "validation_error",
                        "message": "Username not found",
                        "code": "USER_NOT_FOUND"
                    }
                ],
                "timestamp": "2024-12-01T15:30:45Z"
            }
        }


# =============================================================================
# VALIDATION SCHEMAS
# =============================================================================

class PasswordStrengthCheck(BaseModel):
    """Schema for password strength validation."""
    
    valid: bool = Field(
        ...,
        description="Whether password meets requirements"
    )
    errors: List[str] = Field(
        default_factory=list,
        description="List of validation errors"
    )
    requirements: dict = Field(
        default_factory=dict,
        description="Password requirement check results"
    )


# =============================================================================
# UTILITY SCHEMAS
# =============================================================================

class HealthCheck(BaseModel):
    """Health check response schema."""
    
    status: str = Field(
        default="healthy",
        description="Service health status"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Health check timestamp"
    )
    version: str = Field(
        default="1.0.0",
        description="API version"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "status": "healthy",
                "timestamp": "2024-12-01T15:30:45Z",
                "version": "1.0.0"
            }
        }


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Request schemas
    "LoginRequest",
    "RefreshTokenRequest", 
    "LogoutRequest",
    
    # Response schemas
    "TokenResponse",
    "AccessTokenResponse",
    "UserProfile",
    "LogoutResponse",
    
    # Error schemas
    "ErrorDetail",
    "ErrorResponse",
    
    # Validation schemas
    "PasswordStrengthCheck",
    
    # Utility schemas
    "HealthCheck",
]
