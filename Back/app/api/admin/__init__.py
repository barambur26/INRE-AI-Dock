"""
Main admin router that includes all admin endpoints.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import User
from app.schemas.admin import AdminStatsResponse
from app.services.admin_service import AdminService
from app.utils.admin_auth import get_current_admin_user

from .users import router as users_router
from .departments import router as departments_router
from .roles import router as roles_router
from .llm_configurations import router as llm_configs_router


# Main admin router
router = APIRouter(prefix="/admin", tags=["Admin"])

# Include sub-routers
router.include_router(users_router)
router.include_router(departments_router)
router.include_router(roles_router)
router.include_router(llm_configs_router)


@router.get("/stats", response_model=AdminStatsResponse)
async def get_admin_stats(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get admin dashboard statistics.
    
    **Requires:** Admin privileges
    """
    admin_service = AdminService(db)
    
    try:
        stats = await admin_service.get_admin_stats()
        return stats
    except Exception as e:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve admin statistics: {str(e)}"
        )


@router.post("/initialize")
async def initialize_default_data(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Initialize default roles and departments.
    
    **Requires:** Admin privileges
    
    This endpoint creates default roles (admin, user, analyst, manager) 
    and departments (General, IT, Finance, HR, Marketing, Operations) 
    if they don't already exist.
    """
    admin_service = AdminService(db)
    
    try:
        await admin_service.create_default_data()
        
        return {
            'message': 'Default data initialized successfully',
            'created': {
                'roles': ['admin', 'user', 'analyst', 'manager'],
                'departments': ['General', 'IT', 'Finance', 'HR', 'Marketing', 'Operations']
            }
        }
    except Exception as e:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize default data: {str(e)}"
        )


@router.get("/health")
async def admin_health_check(
    current_user: User = Depends(get_current_admin_user)
):
    """
    Admin API health check.
    
    **Requires:** Admin privileges
    """
    return {
        'status': 'healthy',
        'admin_user': current_user.username,
        'user_id': str(current_user.id),
        'is_superuser': current_user.is_superuser,
        'role': current_user.role.name if current_user.role else None
    }
