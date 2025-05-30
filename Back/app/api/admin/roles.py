"""
Admin API endpoints for role management.
"""
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import User, Role
from app.schemas.admin import (
    RoleCreate, RoleUpdate, RoleResponse, 
    RoleListResponse, AvailablePermissionsResponse
)
from app.services.admin_service import AdminService
from app.utils.admin_auth import get_current_admin_user


router = APIRouter(prefix="/roles", tags=["Admin - Roles"])


@router.get("/", response_model=RoleListResponse)
async def list_roles(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get all roles.
    
    **Requires:** Admin privileges
    """
    admin_service = AdminService(db)
    
    try:
        roles = await admin_service.get_roles()
        
        # Format roles with user counts
        roles_with_counts = []
        for role in roles:
            role_dict = {
                'id': role.id,
                'name': role.name,
                'description': role.description,
                'permissions': role.permissions,
                'created_at': role.created_at,
                'updated_at': role.updated_at,
                'user_count': role.user_count,
                'is_admin_role': role.is_admin_role
            }
            roles_with_counts.append(role_dict)
        
        return RoleListResponse(
            roles=roles_with_counts,
            total=len(roles)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve roles: {str(e)}"
        )


@router.get("/permissions", response_model=AvailablePermissionsResponse)
async def get_available_permissions(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get all available permissions.
    
    **Requires:** Admin privileges
    """
    admin_service = AdminService(db)
    
    try:
        permissions = await admin_service.get_available_permissions()
        
        # Group permissions by category
        categories = list(set([p.category for p in permissions]))
        
        return AvailablePermissionsResponse(
            permissions=permissions,
            categories=categories
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve permissions: {str(e)}"
        )


@router.get("/{role_id}", response_model=RoleResponse)
async def get_role(
    role_id: UUID,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific role by ID.
    
    **Requires:** Admin privileges
    """
    admin_service = AdminService(db)
    
    role = await admin_service.get_role_by_id(role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role with ID {role_id} not found"
        )
    
    return {
        'id': role.id,
        'name': role.name,
        'description': role.description,
        'permissions': role.permissions,
        'created_at': role.created_at,
        'updated_at': role.updated_at,
        'user_count': role.user_count,
        'is_admin_role': role.is_admin_role
    }


@router.post("/", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role(
    role_data: RoleCreate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Create a new role.
    
    **Requires:** Admin privileges
    """
    admin_service = AdminService(db)
    
    try:
        role = await admin_service.create_role(role_data)
        
        return {
            'id': role.id,
            'name': role.name,
            'description': role.description,
            'permissions': role.permissions,
            'created_at': role.created_at,
            'updated_at': role.updated_at,
            'user_count': 0,
            'is_admin_role': role.is_admin_role
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create role: {str(e)}"
        )


@router.put("/{role_id}", response_model=RoleResponse)
async def update_role(
    role_id: UUID,
    role_data: RoleUpdate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Update an existing role.
    
    **Requires:** Admin privileges
    """
    admin_service = AdminService(db)
    
    try:
        role = await admin_service.update_role(role_id, role_data)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role with ID {role_id} not found"
            )
        
        return {
            'id': role.id,
            'name': role.name,
            'description': role.description,
            'permissions': role.permissions,
            'created_at': role.created_at,
            'updated_at': role.updated_at,
            'user_count': role.user_count,
            'is_admin_role': role.is_admin_role
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update role: {str(e)}"
        )


@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(
    role_id: UUID,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Delete a role.
    
    **Requires:** Admin privileges
    
    **Note:** Cannot delete roles that have users assigned or the admin role.
    """
    admin_service = AdminService(db)
    
    try:
        success = await admin_service.delete_role(role_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role with ID {role_id} not found"
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete role: {str(e)}"
        )


@router.get("/{role_id}/users")
async def get_role_users(
    role_id: UUID,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get all users with a specific role.
    
    **Requires:** Admin privileges
    """
    admin_service = AdminService(db)
    
    role = await admin_service.get_role_by_id(role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role with ID {role_id} not found"
        )
    
    # Get users with this role
    users = db.query(User).filter(User.role_id == role_id).all()
    
    # Format user data
    users_data = []
    for user in users:
        user_dict = {
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
        users_data.append(user_dict)
    
    return {
        'role': {
            'id': role.id,
            'name': role.name,
            'description': role.description,
            'permissions': role.permissions
        },
        'users': users_data,
        'total_users': len(users_data)
    }


@router.post("/{role_id}/users/{user_id}")
async def assign_role_to_user(
    role_id: UUID,
    user_id: UUID,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Assign a role to a user.
    
    **Requires:** Admin privileges
    """
    admin_service = AdminService(db)
    
    # Verify role exists
    role = await admin_service.get_role_by_id(role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role with ID {role_id} not found"
        )
    
    # Update user's role
    try:
        from app.schemas.admin import UserUpdate
        user = await admin_service.update_user(user_id, UserUpdate(role_id=role_id))
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found"
            )
        
        return {
            'message': f"Role {role.name} assigned to user {user.username}",
            'user_id': user_id,
            'role_id': role_id
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to assign role to user: {str(e)}"
        )


@router.delete("/{role_id}/users/{user_id}")
async def remove_role_from_user(
    role_id: UUID,
    user_id: UUID,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Remove a role from a user.
    
    **Requires:** Admin privileges
    """
    admin_service = AdminService(db)
    
    try:
        from app.schemas.admin import UserUpdate
        user = await admin_service.update_user(user_id, UserUpdate(role_id=None))
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found"
            )
        
        return {
            'message': f"Role removed from user {user.username}",
            'user_id': user_id
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove role from user: {str(e)}"
        )


@router.post("/{role_id}/permissions")
async def add_permission_to_role(
    role_id: UUID,
    permission: str,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Add a permission to a role.
    
    **Requires:** Admin privileges
    """
    admin_service = AdminService(db)
    
    role = await admin_service.get_role_by_id(role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role with ID {role_id} not found"
        )
    
    try:
        # Add permission to role
        role.add_permission(permission)
        db.commit()
        
        return {
            'message': f"Permission '{permission}' added to role {role.name}",
            'role_id': role_id,
            'permission': permission,
            'current_permissions': role.get_permissions()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add permission to role: {str(e)}"
        )


@router.delete("/{role_id}/permissions/{permission}")
async def remove_permission_from_role(
    role_id: UUID,
    permission: str,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Remove a permission from a role.
    
    **Requires:** Admin privileges
    """
    admin_service = AdminService(db)
    
    role = await admin_service.get_role_by_id(role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role with ID {role_id} not found"
        )
    
    try:
        # Remove permission from role
        role.remove_permission(permission)
        db.commit()
        
        return {
            'message': f"Permission '{permission}' removed from role {role.name}",
            'role_id': role_id,
            'permission': permission,
            'current_permissions': role.get_permissions()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove permission from role: {str(e)}"
        )
