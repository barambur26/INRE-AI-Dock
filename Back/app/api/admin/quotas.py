"""
Admin API endpoints for quota management.
"""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.models import User, DepartmentQuota
from app.schemas.quota import (
    QuotaCreate, QuotaUpdate, QuotaResponse, QuotaWithDetails,
    QuotaListResponse, QuotaFilters, BulkQuotaCreate, BulkQuotaUpdate,
    BulkQuotaResponse, QuotaTemplatesResponse, QuotaOverviewStats,
    DepartmentQuotaSummary, QuotaAlertsResponse, QuotaResetRequest,
    QuotaResetResponse, QuotaUsageStats, QuotaTemplate, QuotaEnforcement
)
from app.services.quota_service import QuotaService
from app.utils.admin_auth import get_current_admin_user


router = APIRouter(prefix="/quotas", tags=["Admin - Quotas"])


@router.get("/", response_model=QuotaListResponse)
async def list_quotas(
    skip: int = Query(0, ge=0, description="Number of quotas to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of quotas to return"),
    department_id: Optional[UUID] = Query(None, description="Filter by department ID"),
    llm_config_id: Optional[UUID] = Query(None, description="Filter by LLM configuration ID"),
    enforcement_mode: Optional[QuotaEnforcement] = Query(None, description="Filter by enforcement mode"),
    exceeded_only: bool = Query(False, description="Show only exceeded quotas"),
    warning_only: bool = Query(False, description="Show only quotas at warning threshold"),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get paginated list of quotas with optional filters.
    
    **Requires:** Admin privileges
    """
    quota_service = QuotaService(db)
    
    try:
        filters = QuotaFilters(
            department_id=department_id,
            llm_config_id=llm_config_id,
            enforcement_mode=enforcement_mode,
            exceeded_only=exceeded_only,
            warning_only=warning_only
        )
        
        result = await quota_service.get_quotas(skip=skip, limit=limit, filters=filters)
        
        return QuotaListResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve quotas: {str(e)}"
        )


@router.get("/overview", response_model=QuotaOverviewStats)
async def get_quota_overview(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get quota overview statistics for admin dashboard.
    
    **Requires:** Admin privileges
    """
    quota_service = QuotaService(db)
    
    try:
        stats = await quota_service.get_quota_overview_stats()
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve quota overview: {str(e)}"
        )


@router.get("/alerts", response_model=QuotaAlertsResponse)
async def get_quota_alerts(
    limit: int = Query(50, ge=1, le=200, description="Maximum number of alerts to return"),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get quota alerts for exceeded or warning quotas.
    
    **Requires:** Admin privileges
    """
    quota_service = QuotaService(db)
    
    try:
        alerts = await quota_service.get_quota_alerts(limit=limit)
        
        return QuotaAlertsResponse(
            alerts=alerts,
            total_alerts=len(alerts),
            unread_alerts=len([a for a in alerts if a.alert_type == "exceeded"])
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve quota alerts: {str(e)}"
        )


@router.get("/templates", response_model=QuotaTemplatesResponse)
async def get_quota_templates(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get available quota templates.
    
    **Requires:** Admin privileges
    """
    quota_service = QuotaService(db)
    
    try:
        templates = await quota_service.get_quota_templates()
        return QuotaTemplatesResponse(templates=templates)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve quota templates: {str(e)}"
        )


@router.get("/{quota_id}", response_model=QuotaWithDetails)
async def get_quota(
    quota_id: UUID,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific quota by ID.
    
    **Requires:** Admin privileges
    """
    quota_service = QuotaService(db)
    
    quota = await quota_service.get_quota_by_id(quota_id)
    if not quota:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Quota with ID {quota_id} not found"
        )
    
    try:
        quota_details = await quota_service._format_quota_with_details(quota)
        return QuotaWithDetails(**quota_details)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve quota details: {str(e)}"
        )


@router.post("/", response_model=QuotaResponse, status_code=status.HTTP_201_CREATED)
async def create_quota(
    quota_data: QuotaCreate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Create a new quota.
    
    **Requires:** Admin privileges
    """
    quota_service = QuotaService(db)
    
    try:
        quota = await quota_service.create_quota(quota_data)
        quota_details = await quota_service._format_quota_with_details(quota)
        return QuotaResponse(**quota_details)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create quota: {str(e)}"
        )


@router.put("/{quota_id}", response_model=QuotaResponse)
async def update_quota(
    quota_id: UUID,
    quota_data: QuotaUpdate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Update an existing quota.
    
    **Requires:** Admin privileges
    """
    quota_service = QuotaService(db)
    
    try:
        quota = await quota_service.update_quota(quota_id, quota_data)
        if not quota:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Quota with ID {quota_id} not found"
            )
        
        quota_details = await quota_service._format_quota_with_details(quota)
        return QuotaResponse(**quota_details)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update quota: {str(e)}"
        )


@router.delete("/{quota_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_quota(
    quota_id: UUID,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Delete a quota.
    
    **Requires:** Admin privileges
    """
    quota_service = QuotaService(db)
    
    try:
        success = await quota_service.delete_quota(quota_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Quota with ID {quota_id} not found"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete quota: {str(e)}"
        )


@router.post("/bulk", response_model=BulkQuotaResponse, status_code=status.HTTP_201_CREATED)
async def create_bulk_quotas(
    bulk_data: BulkQuotaCreate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Create multiple quotas in bulk.
    
    **Requires:** Admin privileges
    """
    quota_service = QuotaService(db)
    
    try:
        result = await quota_service.create_bulk_quotas(bulk_data)
        return BulkQuotaResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create bulk quotas: {str(e)}"
        )


@router.put("/bulk", response_model=BulkQuotaResponse)
async def update_bulk_quotas(
    bulk_data: BulkQuotaUpdate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Update multiple quotas in bulk.
    
    **Requires:** Admin privileges
    """
    quota_service = QuotaService(db)
    
    try:
        result = await quota_service.update_bulk_quotas(bulk_data)
        return BulkQuotaResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update bulk quotas: {str(e)}"
        )


@router.post("/reset", response_model=QuotaResetResponse)
async def reset_quotas(
    reset_request: QuotaResetRequest,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Reset quota usage counters.
    
    **Requires:** Admin privileges
    """
    quota_service = QuotaService(db)
    
    try:
        result = await quota_service.reset_quotas(reset_request)
        return QuotaResetResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset quotas: {str(e)}"
        )


# Department-specific endpoints
@router.get("/department/{department_id}", response_model=List[QuotaWithDetails])
async def get_department_quotas(
    department_id: UUID,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get all quotas for a specific department.
    
    **Requires:** Admin privileges
    """
    quota_service = QuotaService(db)
    
    try:
        quotas = await quota_service.get_department_quotas(department_id)
        
        quotas_with_details = []
        for quota in quotas:
            quota_details = await quota_service._format_quota_with_details(quota)
            quotas_with_details.append(QuotaWithDetails(**quota_details))
        
        return quotas_with_details
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve department quotas: {str(e)}"
        )


@router.get("/department/{department_id}/summary", response_model=DepartmentQuotaSummary)
async def get_department_quota_summary(
    department_id: UUID,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get quota summary for a specific department.
    
    **Requires:** Admin privileges
    """
    quota_service = QuotaService(db)
    
    try:
        summary = await quota_service.get_department_quota_summary(department_id)
        return summary
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve department quota summary: {str(e)}"
        )


# Quota checking endpoints (for internal use by chat service)
@router.get("/check/{department_id}/{llm_config_id}")
async def check_quota_limits(
    department_id: UUID,
    llm_config_id: UUID,
    tokens_requested: int = Query(0, ge=0, description="Number of tokens requested"),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Check quota limits for a department and LLM configuration.
    
    **Requires:** Admin privileges
    """
    quota_service = QuotaService(db)
    
    try:
        can_proceed, message, quota_info = await quota_service.check_quota_limits(
            department_id, llm_config_id, tokens_requested
        )
        
        return {
            'can_proceed': can_proceed,
            'message': message,
            'quota_info': quota_info,
            'department_id': department_id,
            'llm_config_id': llm_config_id,
            'tokens_requested': tokens_requested
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check quota limits: {str(e)}"
        )


# Usage tracking endpoints (for internal use by chat service)
@router.post("/usage/{department_id}/{llm_config_id}")
async def update_quota_usage(
    department_id: UUID,
    llm_config_id: UUID,
    tokens_used: int = Query(..., gt=0, description="Number of tokens used"),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Update quota usage after an LLM request.
    
    **Requires:** Admin privileges
    """
    quota_service = QuotaService(db)
    
    try:
        quota = await quota_service.update_quota_usage(
            department_id, llm_config_id, tokens_used
        )
        
        if quota:
            quota_details = await quota_service._format_quota_with_details(quota)
            return {
                'updated': True,
                'quota': QuotaResponse(**quota_details),
                'tokens_used': tokens_used
            }
        else:
            return {
                'updated': False,
                'message': 'Failed to update quota usage',
                'tokens_used': tokens_used
            }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update quota usage: {str(e)}"
        )


# Statistics and monitoring endpoints
@router.get("/stats/usage")
async def get_usage_statistics(
    days: int = Query(30, ge=1, le=365, description="Number of days to include in statistics"),
    department_id: Optional[UUID] = Query(None, description="Filter by department ID"),
    llm_config_id: Optional[UUID] = Query(None, description="Filter by LLM configuration ID"),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get usage statistics for quotas.
    
    **Requires:** Admin privileges
    """
    quota_service = QuotaService(db)
    
    try:
        # This would require additional implementation for time-based statistics
        # For now, return basic quota information
        filters = QuotaFilters(
            department_id=department_id,
            llm_config_id=llm_config_id
        )
        
        result = await quota_service.get_quotas(skip=0, limit=1000, filters=filters)
        
        # Calculate basic statistics
        quotas = result['quotas']
        total_usage = sum(q.get('current_usage_tokens', 0) for q in quotas)
        total_limit = sum(q.get('monthly_limit_tokens', 0) for q in quotas if q.get('monthly_limit_tokens', 0) > 0)
        
        return {
            'period_days': days,
            'total_quotas': len(quotas),
            'total_usage_tokens': total_usage,
            'total_limit_tokens': total_limit,
            'average_usage_percentage': (total_usage / total_limit * 100) if total_limit > 0 else 0,
            'quotas_exceeded': len([q for q in quotas if q.get('is_quota_exceeded', False)]),
            'quotas_at_warning': len([q for q in quotas if q.get('is_warning_threshold_reached', False)]),
            'department_filter': department_id,
            'llm_config_filter': llm_config_id
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve usage statistics: {str(e)}"
        )


@router.post("/maintenance/auto-reset")
async def trigger_auto_reset(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Manually trigger auto-reset of monthly quotas (normally done by scheduler).
    
    **Requires:** Admin privileges
    """
    quota_service = QuotaService(db)
    
    try:
        await quota_service.auto_reset_monthly_quotas()
        return {
            'message': 'Monthly quota auto-reset completed',
            'timestamp': quota_service.db.query(func.now()).scalar()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger auto-reset: {str(e)}"
        )
