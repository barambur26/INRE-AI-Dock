"""
Admin API endpoints for user management.
"""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import User
from app.schemas.admin import (
    UserCreate, UserUpdate, UserResponse, UserWithDetails, 
    UserListResponse, BulkUserUpdate, BulkUserResponse
)
from app.services.admin_service import AdminService
from app.utils.admin_auth import get_current_admin_user, AdminPermissions


router = APIRouter(prefix="/users", tags=["Admin - Users"])


@router.get("/", response_model=UserListResponse)
async def list_users(
    skip: int = Query(0, ge=0, description="Number of users to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of users to return"),
    search: Optional[str] = Query(None, description="Search by username or email"),
    role_id: Optional[UUID] = Query(None, description="Filter by role ID"),
    department_id: Optional[UUID] = Query(None, description="Filter by department ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get paginated list of users with optional filters.
    
    **Requires:** Admin privileges
    """
    admin_service = AdminService(db)
    
    try:
        result = await admin_service.get_users(
            skip=skip,
            limit=limit,
            search=search,
            role_id=role_id,
            department_id=department_id,
            is_active=is_active
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve users: {str(e)}"
        )


@router.get("/{user_id}", response_model=UserWithDetails)
async def get_user(
    user_id: UUID,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific user by ID.
    
    **Requires:** Admin privileges
    """
    admin_service = AdminService(db)
    
    user = await admin_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    # Format response with role and department names
    return {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'is_active': user.is_active,
        'is_superuser': user.is_superuser,
        'role_id': user.role_id,
        'department_id': user.department_id,
        'created_at': user.created_at,
        'updated_at': user.updated_at,
        'role_name': user.role.name if user.role else None,
        'department_name': user.department.name if user.department else None
    }


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Create a new user.
    
    **Requires:** Admin privileges
    """
    admin_service = AdminService(db)
    
    try:
        user = await admin_service.create_user(user_data)
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}"
        )


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    user_data: UserUpdate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Update an existing user.
    
    **Requires:** Admin privileges
    """
    admin_service = AdminService(db)
    
    try:
        user = await admin_service.update_user(user_id, user_data)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found"
            )
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user: {str(e)}"
        )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Delete a user.
    
    **Requires:** Admin privileges
    
    **Note:** Cannot delete the last admin user.
    """
    admin_service = AdminService(db)
    
    # Prevent admin from deleting themselves
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    try:
        success = await admin_service.delete_user(user_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found"
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete user: {str(e)}"
        )


@router.post("/{user_id}/activate", response_model=UserResponse)
async def activate_user(
    user_id: UUID,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Activate a user account.
    
    **Requires:** Admin privileges
    """
    admin_service = AdminService(db)
    
    try:
        user = await admin_service.update_user(user_id, UserUpdate(is_active=True))
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found"
            )
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to activate user: {str(e)}"
        )


@router.post("/{user_id}/deactivate", response_model=UserResponse)
async def deactivate_user(
    user_id: UUID,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Deactivate a user account.
    
    **Requires:** Admin privileges
    
    **Note:** Cannot deactivate your own account or the last admin user.
    """
    admin_service = AdminService(db)
    
    # Prevent admin from deactivating themselves
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account"
        )
    
    try:
        user = await admin_service.update_user(user_id, UserUpdate(is_active=False))
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found"
            )
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to deactivate user: {str(e)}"
        )


@router.post("/{user_id}/reset-password")
async def reset_user_password(
    user_id: UUID,
    new_password: str = Query(..., min_length=8, description="New password"),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Reset a user's password.
    
    **Requires:** Admin privileges
    """
    admin_service = AdminService(db)
    
    try:
        user = await admin_service.update_user(user_id, UserUpdate(password=new_password))
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found"
            )
        
        return {"message": f"Password reset successfully for user {user.username}"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset password: {str(e)}"
        )


@router.post("/bulk-update", response_model=BulkUserResponse)
async def bulk_update_users(
    bulk_data: BulkUserUpdate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Bulk update multiple users.
    
    **Requires:** Admin privileges
    """
    admin_service = AdminService(db)
    
    success_count = 0
    error_count = 0
    errors = []
    
    for user_id in bulk_data.user_ids:
        try:
            user = await admin_service.update_user(user_id, bulk_data.updates)
            if user:
                success_count += 1
            else:
                error_count += 1
                errors.append({
                    "user_id": str(user_id),
                    "error": "User not found"
                })
        except Exception as e:
            error_count += 1
            errors.append({
                "user_id": str(user_id),
                "error": str(e)
            })
    
    return BulkUserResponse(
        success_count=success_count,
        error_count=error_count,
        errors=errors
    )
