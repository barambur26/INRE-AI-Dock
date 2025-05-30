"""
Service layer for AI Dock App.

This package contains business logic and service classes.
"""

from .auth_service import (
    # Service classes
    AuthenticationService,
    auth_service,
    
    # Convenience functions
    authenticate_user,
    refresh_token,
    logout_user,
    get_current_user,
    get_mock_users,
    
    # Exceptions
    AuthenticationError,
    InvalidCredentialsError,
    UserNotFoundError,
    InactiveUserError,
    InvalidTokenError,
    TokenBlacklistedError,
)

__all__ = [
    # Authentication service
    "AuthenticationService",
    "auth_service",
    "authenticate_user",
    "refresh_token", 
    "logout_user",
    "get_current_user",
    "get_mock_users",
    
    # Exceptions
    "AuthenticationError",
    "InvalidCredentialsError", 
    "UserNotFoundError",
    "InactiveUserError",
    "InvalidTokenError",
    "TokenBlacklistedError",
]
