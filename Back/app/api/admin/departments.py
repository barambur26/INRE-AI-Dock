"""
Admin API endpoints for department management.
"""
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import User, Department
from app.schemas.admin import (
    DepartmentCreate, DepartmentUpdate, DepartmentResponse, 
    DepartmentListResponse
)
from app.services.admin_service import AdminService
from app.utils.admin_auth import get_current_admin_user


router = APIRouter(prefix="/departments", tags=["Admin - Departments"])


@router.get("/", response_model=DepartmentListResponse)
async def list_departments(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get all departments.
    
    **Requires:** Admin privileges
    """
    admin_service = AdminService(db)
    
    try:
        departments = await admin_service.get_departments()
        
        # Format departments with user counts
        departments_with_counts = []
        for dept in departments:
            dept_dict = {
                'id': dept.id,
                'name': dept.name,
                'description': dept.description,
                'created_at': dept.created_at,
                'updated_at': dept.updated_at,
                'user_count': dept.user_count,
                'active_user_count': dept.active_user_count
            }
            departments_with_counts.append(dept_dict)
        
        return DepartmentListResponse(
            departments=departments_with_counts,
            total=len(departments)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve departments: {str(e)}"
        )


@router.get("/{department_id}", response_model=DepartmentResponse)
async def get_department(
    department_id: UUID,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific department by ID.
    
    **Requires:** Admin privileges
    """
    admin_service = AdminService(db)
    
    department = await admin_service.get_department_by_id(department_id)
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Department with ID {department_id} not found"
        )
    
    return {
        'id': department.id,
        'name': department.name,
        'description': department.description,
        'created_at': department.created_at,
        'updated_at': department.updated_at,
        'user_count': department.user_count,
        'active_user_count': department.active_user_count
    }


@router.post("/", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
async def create_department(
    department_data: DepartmentCreate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Create a new department.
    
    **Requires:** Admin privileges
    """
    admin_service = AdminService(db)
    
    try:
        department = await admin_service.create_department(department_data)
        
        return {
            'id': department.id,
            'name': department.name,
            'description': department.description,
            'created_at': department.created_at,
            'updated_at': department.updated_at,
            'user_count': 0,
            'active_user_count': 0
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create department: {str(e)}"
        )


@router.put("/{department_id}", response_model=DepartmentResponse)
async def update_department(
    department_id: UUID,
    department_data: DepartmentUpdate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Update an existing department.
    
    **Requires:** Admin privileges
    """
    admin_service = AdminService(db)
    
    try:
        department = await admin_service.update_department(department_id, department_data)
        if not department:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Department with ID {department_id} not found"
            )
        
        return {
            'id': department.id,
            'name': department.name,
            'description': department.description,
            'created_at': department.created_at,
            'updated_at': department.updated_at,
            'user_count': department.user_count,
            'active_user_count': department.active_user_count
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update department: {str(e)}"
        )


@router.delete("/{department_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_department(
    department_id: UUID,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Delete a department.
    
    **Requires:** Admin privileges
    
    **Note:** Cannot delete departments that have users assigned.
    """
    admin_service = AdminService(db)
    
    try:
        success = await admin_service.delete_department(department_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Department with ID {department_id} not found"
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete department: {str(e)}"
        )


@router.get("/{department_id}/users")
async def get_department_users(
    department_id: UUID,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get all users in a specific department.
    
    **Requires:** Admin privileges
    """
    admin_service = AdminService(db)
    
    department = await admin_service.get_department_by_id(department_id)
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Department with ID {department_id} not found"
        )
    
    # Get users in this department
    users = db.query(User).filter(User.department_id == department_id).all()
    
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
        'department': {
            'id': department.id,
            'name': department.name,
            'description': department.description
        },
        'users': users_data,
        'total_users': len(users_data)
    }


@router.post("/{department_id}/users/{user_id}")
async def assign_user_to_department(
    department_id: UUID,
    user_id: UUID,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Assign a user to a department.
    
    **Requires:** Admin privileges
    """
    admin_service = AdminService(db)
    
    # Verify department exists
    department = await admin_service.get_department_by_id(department_id)
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Department with ID {department_id} not found"
        )
    
    # Update user's department
    try:
        from app.schemas.admin import UserUpdate
        user = await admin_service.update_user(user_id, UserUpdate(department_id=department_id))
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found"
            )
        
        return {
            'message': f"User {user.username} assigned to department {department.name}",
            'user_id': user_id,
            'department_id': department_id
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to assign user to department: {str(e)}"
        )


@router.delete("/{department_id}/users/{user_id}")
async def remove_user_from_department(
    department_id: UUID,
    user_id: UUID,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Remove a user from a department.
    
    **Requires:** Admin privileges
    """
    admin_service = AdminService(db)
    
    try:
        from app.schemas.admin import UserUpdate
        user = await admin_service.update_user(user_id, UserUpdate(department_id=None))
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found"
            )
        
        return {
            'message': f"User {user.username} removed from department",
            'user_id': user_id
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove user from department: {str(e)}"
        )
