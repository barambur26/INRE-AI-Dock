"""
Authentication service layer for AI Dock App.

This module provides business logic for authentication operations:
- User authentication and login
- Token refresh and validation  
- User logout and token invalidation
- User profile retrieval
- Mock user database for testing (no persistence required)

Integrates with security utilities from app.core.security (AID-US-001B).
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Set
from uuid import uuid4

from app.core.security import (
    hash_password,
    verify_password,
    validate_password_strength,
    create_user_tokens,
    refresh_access_token,
    verify_token,
    extract_user_info,
    TokenError,
    PasswordError,
)
from app.schemas.auth import UserProfile


# =============================================================================
# MOCK USER DATABASE
# =============================================================================

class MockUser:
    """Mock user model for testing authentication without database."""
    
    def __init__(
        self,
        user_id: str,
        username: str,
        email: str,
        password: str,  # Will be hashed
        role: str = "user",
        department: Optional[str] = None,
        permissions: Optional[List[str]] = None,
        is_superuser: bool = False,
        is_active: bool = True,
    ):
        self.user_id = user_id
        self.username = username
        self.email = email
        self.hashed_password = hash_password(password)  # Hash on creation
        self.role = role
        self.department = department
        self.permissions = permissions or []
        self.is_superuser = is_superuser
        self.is_active = is_active
        self.created_at = datetime.now(timezone.utc)
        self.last_login: Optional[datetime] = None
    
    def to_profile(self) -> UserProfile:
        """Convert to UserProfile schema."""
        return UserProfile(
            user_id=self.user_id,
            username=self.username,
            email=self.email,
            role=self.role,
            department=self.department,
            permissions=self.permissions,
            is_superuser=self.is_superuser,
            is_active=self.is_active,
            created_at=self.created_at,
            last_login=self.last_login,
        )
    
    def verify_password(self, password: str) -> bool:
        """Verify password against stored hash."""
        return verify_password(password, self.hashed_password)
    
    def update_last_login(self) -> None:
        """Update last login timestamp."""
        self.last_login = datetime.now(timezone.utc)


class MockUserDatabase:
    """In-memory user database for testing."""
    
    def __init__(self):
        self.users: Dict[str, MockUser] = {}
        self.username_index: Dict[str, str] = {}  # username -> user_id
        self.email_index: Dict[str, str] = {}     # email -> user_id
        self._populate_test_users()
    
    def _populate_test_users(self) -> None:
        """Create test users for authentication testing."""
        test_users = [
            MockUser(
                user_id="admin_001",
                username="admin",
                email="admin@aidock.com",
                password="AdminPassword123",
                role="admin",
                department="IT",
                permissions=["read", "write", "admin", "manage_users", "manage_llms", "view_usage"],
                is_superuser=True,
            ),
            MockUser(
                user_id="user_002",
                username="user1",
                email="user1@aidock.com", 
                password="UserPassword123",
                role="user",
                department="Engineering",
                permissions=["read", "write", "use_llm"],
                is_superuser=False,
            ),
            MockUser(
                user_id="user_003",
                username="user2",
                email="user2@aidock.com",
                password="UserPassword456",
                role="user", 
                department="Marketing",
                permissions=["read", "use_llm"],
                is_superuser=False,
            ),
            MockUser(
                user_id="analyst_004",
                username="analyst",
                email="analyst@aidock.com",
                password="AnalystPassword789",
                role="analyst",
                department="Data Science",
                permissions=["read", "write", "use_llm", "view_usage"],
                is_superuser=False,
            ),
        ]
        
        for user in test_users:
            self.add_user(user)
    
    def add_user(self, user: MockUser) -> None:
        """Add user to database."""
        self.users[user.user_id] = user
        self.username_index[user.username.lower()] = user.user_id
        self.email_index[user.email.lower()] = user.user_id
    
    def get_user_by_id(self, user_id: str) -> Optional[MockUser]:
        """Get user by ID."""
        return self.users.get(user_id)
    
    def get_user_by_username(self, username: str) -> Optional[MockUser]:
        """Get user by username."""
        user_id = self.username_index.get(username.lower())
        return self.users.get(user_id) if user_id else None
    
    def get_user_by_email(self, email: str) -> Optional[MockUser]:
        """Get user by email."""
        user_id = self.email_index.get(email.lower())
        return self.users.get(user_id) if user_id else None
    
    def get_user_by_username_or_email(self, identifier: str) -> Optional[MockUser]:
        """Get user by username or email."""
        # Try username first
        user = self.get_user_by_username(identifier)
        if user:
            return user
        
        # Try email if username lookup failed
        return self.get_user_by_email(identifier)
    
    def list_users(self) -> List[MockUser]:
        """List all users."""
        return list(self.users.values())


# Global mock database instance
mock_db = MockUserDatabase()


# =============================================================================
# TOKEN BLACKLIST (Simple in-memory implementation)
# =============================================================================

class SimpleTokenBlacklist:
    """Simple in-memory token blacklist for logout functionality."""
    
    def __init__(self):
        self.blacklisted_tokens: Set[str] = set()
    
    def add_token(self, token: str) -> None:
        """Add token to blacklist."""
        self.blacklisted_tokens.add(token)
    
    def is_blacklisted(self, token: str) -> bool:
        """Check if token is blacklisted."""
        return token in self.blacklisted_tokens
    
    def cleanup_expired_tokens(self) -> None:
        """Remove expired tokens from blacklist (placeholder)."""
        # In a real implementation, this would parse JWT exp claims
        # and remove expired tokens to prevent memory growth
        pass


# Global blacklist instance
token_blacklist = SimpleTokenBlacklist()


# =============================================================================
# AUTHENTICATION SERVICE EXCEPTIONS
# =============================================================================

class AuthenticationError(Exception):
    """Base exception for authentication errors."""
    pass


class InvalidCredentialsError(AuthenticationError):
    """Exception raised for invalid login credentials."""
    pass


class UserNotFoundError(AuthenticationError):
    """Exception raised when user is not found."""
    pass


class InactiveUserError(AuthenticationError):
    """Exception raised when user account is inactive."""
    pass


class InvalidTokenError(AuthenticationError):
    """Exception raised for invalid or expired tokens."""
    pass


class TokenBlacklistedError(AuthenticationError):
    """Exception raised for blacklisted tokens."""
    pass


# =============================================================================
# AUTHENTICATION SERVICE
# =============================================================================

class AuthenticationService:
    """Service class for authentication operations."""
    
    def __init__(self):
        self.db = mock_db
        self.blacklist = token_blacklist
    
    def authenticate_user(self, username: str, password: str) -> MockUser:
        """
        Authenticate user with username/email and password.
        
        Args:
            username: Username or email address
            password: Plain text password
            
        Returns:
            MockUser object if authentication successful
            
        Raises:
            InvalidCredentialsError: If credentials are invalid
            UserNotFoundError: If user doesn't exist
            InactiveUserError: If user account is inactive
        """
        # Find user by username or email
        user = self.db.get_user_by_username_or_email(username)
        
        if not user:
            raise UserNotFoundError(f"User '{username}' not found")
        
        if not user.is_active:
            raise InactiveUserError(f"User account '{username}' is inactive")
        
        # Verify password
        if not user.verify_password(password):
            raise InvalidCredentialsError("Invalid password")
        
        return user
    
    def login_user(
        self, 
        username: str, 
        password: str, 
        remember_me: bool = False
    ) -> Dict[str, str]:
        """
        Perform user login and return tokens.
        
        Args:
            username: Username or email address
            password: Plain text password
            remember_me: If True, refresh token will have extended expiry
            
        Returns:
            Dictionary containing access_token, refresh_token, token_type, expires_in
            
        Raises:
            InvalidCredentialsError: If credentials are invalid
            UserNotFoundError: If user doesn't exist
            InactiveUserError: If user account is inactive
        """
        # Authenticate user
        user = self.authenticate_user(username, password)
        
        # Update last login timestamp
        user.update_last_login()
        
        # Create tokens
        tokens = create_user_tokens(
            user_id=user.user_id,
            username=user.username,
            email=user.email,
            role=user.role,
            department=user.department,
            permissions=user.permissions,
            is_superuser=user.is_superuser,
            remember_me=remember_me
        )
        
        return tokens
    
    def refresh_user_token(self, refresh_token: str) -> Dict[str, str]:
        """
        Refresh access token using valid refresh token.
        
        Args:
            refresh_token: Valid refresh token
            
        Returns:
            Dictionary containing new access_token, token_type, expires_in
            
        Raises:
            InvalidTokenError: If refresh token is invalid
            TokenBlacklistedError: If token is blacklisted
        """
        # Check if token is blacklisted
        if self.blacklist.is_blacklisted(refresh_token):
            raise TokenBlacklistedError("Refresh token has been revoked")
        
        try:
            # Use security utility to refresh token
            new_tokens = refresh_access_token(refresh_token)
            return new_tokens
            
        except TokenError as e:
            raise InvalidTokenError(f"Invalid refresh token: {str(e)}")
    
    def logout_user(self, refresh_token: str) -> None:
        """
        Logout user by blacklisting refresh token.
        
        Args:
            refresh_token: Refresh token to blacklist
            
        Note:
            In a production system, this would also blacklist the access token
            and store blacklisted tokens in Redis with expiration.
        """
        # Add token to blacklist
        self.blacklist.add_token(refresh_token)
    
    def get_current_user(self, access_token: str) -> UserProfile:
        """
        Get current user profile from access token.
        
        Args:
            access_token: Valid access token
            
        Returns:
            UserProfile object
            
        Raises:
            InvalidTokenError: If access token is invalid
            UserNotFoundError: If user doesn't exist
        """
        try:
            # Verify and decode token
            payload = verify_token(access_token, "access")
            user_id = payload.get("sub")
            
            if not user_id:
                raise InvalidTokenError("Token missing user ID")
            
            # Get user from database
            user = self.db.get_user_by_id(user_id)
            if not user:
                raise UserNotFoundError(f"User '{user_id}' not found")
            
            if not user.is_active:
                raise InactiveUserError(f"User account is inactive")
            
            return user.to_profile()
            
        except TokenError as e:
            raise InvalidTokenError(f"Invalid access token: {str(e)}")
    
    def validate_password_strength(self, password: str) -> Dict:
        """
        Validate password strength using security utilities.
        
        Args:
            password: Password to validate
            
        Returns:
            Dictionary with validation results
        """
        return validate_password_strength(password)
    
    def get_user_list(self) -> List[UserProfile]:
        """
        Get list of all users (for admin/testing purposes).
        
        Returns:
            List of UserProfile objects
        """
        return [user.to_profile() for user in self.db.list_users()]


# =============================================================================
# SERVICE INSTANCE
# =============================================================================

# Global service instance
auth_service = AuthenticationService()


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def authenticate_user(username: str, password: str, remember_me: bool = False) -> Dict[str, str]:
    """Convenience function for user authentication."""
    return auth_service.login_user(username, password, remember_me)


def refresh_token(refresh_token: str) -> Dict[str, str]:
    """Convenience function for token refresh."""
    return auth_service.refresh_user_token(refresh_token)


def logout_user(refresh_token: str) -> None:
    """Convenience function for user logout."""
    return auth_service.logout_user(refresh_token)


def get_current_user(access_token: str) -> UserProfile:
    """Convenience function to get current user."""
    return auth_service.get_current_user(access_token)


def get_mock_users() -> List[UserProfile]:
    """Get list of all mock users for testing."""
    return auth_service.get_user_list()


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Service classes
    "AuthenticationService",
    "MockUser", 
    "MockUserDatabase",
    "SimpleTokenBlacklist",
    
    # Exceptions
    "AuthenticationError",
    "InvalidCredentialsError",
    "UserNotFoundError",
    "InactiveUserError", 
    "InvalidTokenError",
    "TokenBlacklistedError",
    
    # Service instance
    "auth_service",
    
    # Convenience functions
    "authenticate_user",
    "refresh_token",
    "logout_user",
    "get_current_user",
    "get_mock_users",
]
