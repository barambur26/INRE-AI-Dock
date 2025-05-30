"""
Authentication API endpoints for AI Dock App.

This module provides FastAPI route handlers for:
- POST /auth/login - User authentication with remember me support
- POST /auth/refresh - Access token refresh
- POST /auth/logout - User logout with token blacklisting
- GET /auth/me - Current user profile retrieval

Integrates with authentication service layer and security utilities.
"""

from datetime import datetime
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.schemas.auth import (
    LoginRequest,
    RefreshTokenRequest,
    LogoutRequest,
    TokenResponse,
    AccessTokenResponse,
    UserProfile,
    LogoutResponse,
    ErrorResponse,
    HealthCheck,
)
from app.services.auth_service import (
    authenticate_user,
    refresh_token,
    logout_user,
    get_current_user,
    get_mock_users,
    InvalidCredentialsError,
    UserNotFoundError,
    InactiveUserError,
    InvalidTokenError,
    TokenBlacklistedError,
)


# =============================================================================
# ROUTER SETUP
# =============================================================================

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
    responses={
        404: {"description": "Not found"},
        422: {"description": "Validation error"},
    },
)

# Security scheme for Bearer token authentication
security = HTTPBearer()


# =============================================================================
# DEPENDENCY FUNCTIONS
# =============================================================================

async def get_current_user_dependency(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> UserProfile:
    """
    FastAPI dependency to extract current user from JWT token.
    
    Args:
        credentials: HTTP Bearer credentials from Authorization header
        
    Returns:
        UserProfile object for authenticated user
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    try:
        access_token = credentials.credentials
        user_profile = get_current_user(access_token)
        return user_profile
        
    except InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except UserNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except InactiveUserError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )


# =============================================================================
# AUTHENTICATION ENDPOINTS
# =============================================================================

@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="User Login",
    description="Authenticate user with username/email and password. Returns access and refresh tokens.",
    responses={
        200: {
            "description": "Login successful",
            "model": TokenResponse,
        },
        401: {
            "description": "Invalid credentials",
            "model": ErrorResponse,
        },
        403: {
            "description": "Account inactive",
            "model": ErrorResponse,
        },
        404: {
            "description": "User not found",
            "model": ErrorResponse,
        },
    }
)
async def login(request: LoginRequest) -> TokenResponse:
    """
    User login endpoint.
    
    Authenticates user with username/email and password.
    Returns JWT access token (15 min expiry) and refresh token (7-30 days expiry).
    
    - **username**: Username or email address
    - **password**: User password  
    - **remember_me**: If true, refresh token will have extended expiry (30 days vs 7 days)
    """
    try:
        tokens = authenticate_user(
            username=request.username,
            password=request.password,
            remember_me=request.remember_me
        )
        
        return TokenResponse(**tokens)
        
    except InvalidCredentialsError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    except UserNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    except InactiveUserError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}",
        )


@router.post(
    "/refresh",
    response_model=AccessTokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh Access Token",
    description="Exchange valid refresh token for new access token.",
    responses={
        200: {
            "description": "Token refresh successful",
            "model": AccessTokenResponse,
        },
        401: {
            "description": "Invalid or expired refresh token",
            "model": ErrorResponse,
        },
        403: {
            "description": "Token has been revoked",
            "model": ErrorResponse,
        },
    }
)
async def refresh_access_token(request: RefreshTokenRequest) -> AccessTokenResponse:
    """
    Token refresh endpoint.
    
    Exchanges a valid refresh token for a new access token.
    The refresh token remains valid and can be used multiple times until expiry.
    
    - **refresh_token**: Valid JWT refresh token
    """
    try:
        new_tokens = refresh_token(request.refresh_token)
        
        return AccessTokenResponse(**new_tokens)
        
    except InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )
    except TokenBlacklistedError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Refresh token has been revoked",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token refresh failed: {str(e)}",
        )


@router.post(
    "/logout",
    response_model=LogoutResponse,
    status_code=status.HTTP_200_OK,
    summary="User Logout",
    description="Logout user by blacklisting refresh token.",
    responses={
        200: {
            "description": "Logout successful",
            "model": LogoutResponse,
        },
    }
)
async def logout(request: LogoutRequest) -> LogoutResponse:
    """
    User logout endpoint.
    
    Invalidates the provided refresh token by adding it to a blacklist.
    The access token will remain valid until its natural expiry (15 minutes).
    
    Note: In production, you should also blacklist the access token and
    implement token cleanup to prevent memory growth.
    
    - **refresh_token**: Refresh token to invalidate
    """
    try:
        logout_user(request.refresh_token)
        
        return LogoutResponse(
            message="Successfully logged out",
            logged_out_at=datetime.utcnow()
        )
        
    except Exception as e:
        # Even if logout fails, we return success for security
        # (don't reveal information about token validity)
        return LogoutResponse(
            message="Successfully logged out",
            logged_out_at=datetime.utcnow()
        )


@router.get(
    "/me",
    response_model=UserProfile,
    status_code=status.HTTP_200_OK,
    summary="Get Current User Profile",
    description="Get current user profile information from JWT access token.",
    responses={
        200: {
            "description": "User profile retrieved successfully",
            "model": UserProfile,
        },
        401: {
            "description": "Invalid or expired access token",
            "model": ErrorResponse,
        },
        403: {
            "description": "Account inactive",
            "model": ErrorResponse,
        },
        404: {
            "description": "User not found",
            "model": ErrorResponse,
        },
    }
)
async def get_user_profile(
    current_user: UserProfile = Depends(get_current_user_dependency)
) -> UserProfile:
    """
    Get current user profile endpoint.
    
    Returns detailed user profile information for the authenticated user.
    Requires valid JWT access token in Authorization header.
    
    **Authorization**: Bearer <access_token>
    """
    return current_user


# =============================================================================
# UTILITY ENDPOINTS (for testing and development)
# =============================================================================

@router.get(
    "/health",
    response_model=HealthCheck,
    status_code=status.HTTP_200_OK,
    summary="Authentication Service Health Check",
    description="Check if authentication service is healthy.",
    tags=["Health"],
)
async def health_check() -> HealthCheck:
    """
    Health check endpoint for authentication service.
    
    Returns service status and version information.
    Useful for monitoring and debugging.
    """
    return HealthCheck(
        status="healthy",
        timestamp=datetime.utcnow(),
        version="1.0.0"
    )


@router.get(
    "/users",
    response_model=list[UserProfile],
    status_code=status.HTTP_200_OK,
    summary="List All Users (Development Only)",
    description="Get list of all users in mock database. For development and testing only.",
    tags=["Development"],
    responses={
        200: {
            "description": "Users retrieved successfully",
            "model": list[UserProfile],
        },
        401: {
            "description": "Authentication required",
            "model": ErrorResponse,
        },
        403: {
            "description": "Admin privileges required",
            "model": ErrorResponse,
        },
    }
)
async def list_users(
    current_user: UserProfile = Depends(get_current_user_dependency)
) -> list[UserProfile]:
    """
    List all users endpoint (development only).
    
    Returns list of all users in the mock database.
    Requires authentication and admin privileges.
    
    **Note**: This endpoint is for development and testing only.
    In production, this would have proper pagination and filtering.
    
    **Authorization**: Bearer <access_token>
    **Required Role**: admin
    """
    # Check if user has admin privileges
    if not current_user.is_superuser and "admin" not in current_user.permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    
    return get_mock_users()


# =============================================================================
# TEST DATA ENDPOINT (for development)
# =============================================================================

@router.get(
    "/test-credentials",
    response_model=Dict[str, str],
    status_code=status.HTTP_200_OK,
    summary="Get Test User Credentials (Development Only)",
    description="Get test user credentials for development and testing.",
    tags=["Development"],
)
async def get_test_credentials() -> Dict[str, str]:
    """
    Get test user credentials endpoint (development only).
    
    Returns username/password combinations for testing authentication.
    
    **Note**: This endpoint should be removed in production!
    """
    return {
        "admin": "AdminPassword123",
        "user1": "UserPassword123", 
        "user2": "UserPassword456",
        "analyst": "AnalystPassword789",
        "note": "Use these credentials to test the /auth/login endpoint"
    }


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "router",
    "get_current_user_dependency",
]
