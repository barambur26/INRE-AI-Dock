"""
Admin authorization utilities and decorators.
"""
from functools import wraps
from typing import Optional

from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import verify_token, extract_user_info
from app.models import User


security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user from token."""
    try:
        # Extract token from credentials
        token = credentials.credentials
        
        # Verify and decode token
        token_data = verify_token(token, token_type="access")
        user_info = extract_user_info(token)
        
        # Get user from database
        user = db.query(User).filter(User.id == user_info["user_id"]).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Inactive user",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        return user
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )


async def get_current_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current user and verify admin privileges."""
    if not (current_user.is_superuser or (current_user.role and current_user.role.name == "admin")):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    
    return current_user


def require_admin_permission(permission: str):
    """Decorator to require specific admin permission."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract current_user from kwargs
            current_user = kwargs.get('current_user')
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            # Check if user is superuser (has all permissions)
            if current_user.is_superuser:
                return await func(*args, **kwargs)
            
            # Check if user has the required permission
            if not current_user.has_permission(permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission '{permission}' required"
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def require_admin_or_self(func):
    """Decorator to require admin privileges or user acting on their own data."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        current_user = kwargs.get('current_user')
        target_user_id = kwargs.get('user_id') or kwargs.get('id')
        
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        # Allow if user is admin
        if current_user.is_superuser or (current_user.role and current_user.role.name == "admin"):
            return await func(*args, **kwargs)
        
        # Allow if user is acting on their own data
        if target_user_id and str(current_user.id) == str(target_user_id):
            return await func(*args, **kwargs)
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required or user can only access their own data"
        )
    
    return wrapper


class AdminPermissions:
    """Admin permission constants."""
    
    # System permissions
    ALL = "*"
    
    # User management
    MANAGE_USERS = "manage_users"
    MANAGE_DEPARTMENTS = "manage_departments"
    MANAGE_ROLES = "manage_roles"
    
    # LLM management
    MANAGE_LLMS = "manage_llms"
    MANAGE_QUOTAS = "manage_quotas"
    
    # Reporting
    VIEW_ALL_USAGE = "view_all_usage"
    VIEW_REPORTS = "view_reports"
    
    # Department management
    MANAGE_DEPARTMENT_USERS = "manage_department_users"
    
    # Basic user permissions
    CHAT = "chat"
    VIEW_PROFILE = "view_profile"
    VIEW_USAGE = "view_usage"


def check_user_permission(user: User, permission: str) -> bool:
    """Check if user has a specific permission."""
    if user.is_superuser:
        return True
    
    if user.role and user.role.permissions:
        # Check for wildcard permission
        if "*" in user.role.permissions:
            return True
        
        # Check for specific permission
        if permission in user.role.permissions:
            return True
    
    return False


def get_user_permissions(user: User) -> list:
    """Get all permissions for a user."""
    if user.is_superuser:
        return ["*"]
    
    if user.role and user.role.permissions:
        return user.role.permissions
    
    return []


# Dependency for admin-only endpoints
def get_admin_user():
    """Dependency function for admin-only endpoints."""
    return Depends(get_current_admin_user)


# Dependency with permission check
def require_permission(permission: str):
    """Dependency factory for permission-specific endpoints."""
    async def permission_dependency(current_user: User = Depends(get_current_user)):
        if not check_user_permission(current_user, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' required"
            )
        return current_user
    
    return permission_dependency
