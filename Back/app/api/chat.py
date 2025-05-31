"""
Chat API endpoints for LLM interactions.
Enhanced with comprehensive quota enforcement for AID-US-007.
"""
from typing import Dict, Any
from uuid import UUID
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.schemas.auth import UserProfile
from app.schemas.chat import (
    ChatSendRequest, ChatSendResponse, AvailableModelsResponse,
    UsageQuotaInfo, ChatStatsResponse, ChatHealthResponse,
    ChatErrorResponse, QuotaExceededError, QuotaWarningResponse,
    QuotaStatusResponse, EnhancedChatErrorResponse
)
from app.services.chat_service import (
    chat_service, ChatServiceError, NoAvailableModelsError, 
    QuotaExceededError as ServiceQuotaExceededError,
    QuotaWarningError
)
from app.services.llm_service import LLMProviderError
from app.utils.admin_auth import get_current_user

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


@router.post("/send", response_model=ChatSendResponse)
async def send_chat_message(
    request: ChatSendRequest,
    current_user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Send a chat message to an LLM and receive a response.
    
    Enhanced with comprehensive quota enforcement that checks usage limits
    before processing requests and provides detailed quota information in responses.
    
    This endpoint:
    1. Selects the appropriate LLM (specific model or default)
    2. Estimates token usage for accurate quota checking
    3. Checks department quota limits with detailed validation
    4. Sends the message to the LLM (only if quota allows)
    5. Logs usage statistics with enhanced details
    6. Updates quota usage accurately
    7. Returns the LLM response with metadata
    """
    try:
        response = await chat_service.send_message(
            request=request,
            user=current_user,
            db=db
        )
        return response
        
    except NoAvailableModelsError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "no_models_available",
                "message": str(e),
                "error_code": "NO_MODELS",
                "suggestions": [
                    "Contact your administrator to configure LLM models",
                    "Check if any models are enabled in the admin settings"
                ],
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
    except ServiceQuotaExceededError as e:
        # Enhanced quota exceeded error with detailed information
        suggested_actions = [
            "Wait until next month for quota reset",
            "Contact your administrator to increase quota limits"
        ]
        
        # Add specific suggestions based on quota info
        if hasattr(e, 'quota_info') and e.quota_info:
            quota_info = e.quota_info
            if quota_info.get('remaining_tokens', 0) > 0:
                suggested_actions.insert(0, f"Try a shorter message (you have {quota_info.get('remaining_tokens')} tokens remaining)")
            if quota_info.get('usage_percentage_now', 0) > 95:
                suggested_actions.insert(1, "Your department is very close to the monthly limit")
        
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "quota_exceeded",
                "message": str(e),
                "error_code": "QUOTA_EXCEEDED",
                "quota_info": getattr(e, 'quota_info', {}),
                "suggested_actions": suggested_actions,
                "retry_after": None,  # Could be enhanced with reset date
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
    except QuotaWarningError as e:
        # Handle quota warnings (this shouldn't prevent the request, but log it)
        # In practice, warnings are handled within the service and don't raise exceptions
        # This is here for completeness
        raise HTTPException(
            status_code=status.HTTP_200_OK,  # Success but with warning
            detail={
                "warning": "quota_warning",
                "message": str(e),
                "quota_info": getattr(e, 'quota_info', {}),
                "suggestions": [
                    "Monitor your usage carefully",
                    "Consider requesting a quota increase if needed"
                ]
            }
        )
    except LLMProviderError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "error": "llm_provider_error",
                "message": f"LLM service error: {str(e)}",
                "error_code": "LLM_PROVIDER_ERROR",
                "details": getattr(e, 'details', {}),
                "suggestions": [
                    "Try again in a few moments",
                    "Try using a different model if available",
                    "Contact support if the issue persists"
                ],
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
    except ChatServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "chat_service_error",
                "message": str(e),
                "error_code": "CHAT_SERVICE_ERROR",
                "suggestions": [
                    "Please try again",
                    "Contact support if the issue persists"
                ],
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_server_error",
                "message": "An unexpected error occurred",
                "error_code": "INTERNAL_ERROR",
                "suggestions": [
                    "Please try again",
                    "Contact support if the issue persists"
                ],
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )


@router.get("/models", response_model=AvailableModelsResponse)
async def get_available_models(
    current_user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Get list of available LLM models for the current user.
    
    Returns all enabled LLM configurations with their details.
    """
    try:
        models = await chat_service.get_available_models(db)
        return models
        
    except ChatServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "service_error",
                "message": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )


@router.get("/quota", response_model=UsageQuotaInfo)
async def get_usage_quota(
    current_user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Get current usage quota information for the user's department.
    
    Returns quota limits, current usage, and remaining allowance.
    Enhanced with real-time quota status for AID-US-007.
    """
    try:
        quota_info = await chat_service.get_usage_quota_info(
            user=current_user,
            db=db
        )
        return quota_info
        
    except ChatServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "service_error",
                "message": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )


@router.get("/quota/status", response_model=QuotaStatusResponse)
async def get_quota_status(
    model_id: UUID = None,
    current_user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Get detailed quota status for a specific model or the default model.
    
    New endpoint for AID-US-007 that provides real-time quota monitoring.
    """
    try:
        # Get the model to check quota for
        if model_id:
            # Use specific model
            from sqlalchemy import select
            from app.models import LLMConfiguration, Department
            
            result = await db.execute(
                select(LLMConfiguration)
                .where(LLMConfiguration.id == model_id)
            )
            llm_config = result.scalar_one_or_none()
            if not llm_config:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={"error": "model_not_found", "message": f"Model {model_id} not found"}
                )
        else:
            # Use default model
            llm_config = await chat_service._get_default_model(db)
        
        # Get department info
        from sqlalchemy import select
        from app.models import Department, DepartmentQuota
        
        result = await db.execute(
            select(Department)
            .where(Department.id == current_user.department_id)
        )
        department = result.scalar_one_or_none()
        
        # Get quota
        result = await db.execute(
            select(DepartmentQuota)
            .where(
                DepartmentQuota.department_id == current_user.department_id,
                DepartmentQuota.llm_config_id == llm_config.id
            )
        )
        quota = result.scalar_one_or_none()
        
        if not quota:
            # Create default quota if not exists
            from app.models import DepartmentQuota
            quota = DepartmentQuota(
                department_id=current_user.department_id,
                llm_config_id=llm_config.id,
                monthly_limit_tokens=10000,
                current_usage_tokens=0
            )
            db.add(quota)
            await db.commit()
            await db.refresh(quota)
        
        # Calculate status
        usage_percentage = quota.usage_percentage if quota.monthly_limit_tokens > 0 else 0
        is_exceeded = quota.is_quota_exceeded
        is_warning = usage_percentage >= 80 and not is_exceeded
        remaining_tokens = max(0, quota.monthly_limit_tokens - quota.current_usage_tokens)
        
        return QuotaStatusResponse(
            quota_id=quota.id,
            department_name=department.name if department else "Unknown",
            llm_model_name=llm_config.model_name,
            monthly_limit=quota.monthly_limit_tokens,
            current_usage=quota.current_usage_tokens,
            usage_percentage=usage_percentage,
            is_exceeded=is_exceeded,
            is_warning=is_warning,
            remaining_tokens=remaining_tokens,
            last_updated=quota.updated_at or quota.created_at
        )
        
    except ChatServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "service_error",
                "message": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )


@router.get("/stats", response_model=ChatStatsResponse)
async def get_chat_stats(
    current_user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Get chat usage statistics for the current user.
    
    Returns metrics like total messages, tokens used, costs, etc.
    """
    try:
        stats = await chat_service.get_chat_stats(
            user=current_user,
            db=db
        )
        return stats
        
    except ChatServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "service_error",
                "message": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )


@router.get("/health", response_model=ChatHealthResponse)
async def get_chat_health(
    db: AsyncSession = Depends(get_async_session)
):
    """
    Get chat service health status.
    
    Enhanced for AID-US-007 with quota system health monitoring.
    Public endpoint that shows service availability and model status.
    No authentication required for health checks.
    """
    try:
        health = await chat_service.get_health_status(db)
        return health
        
    except ChatServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "service_error",
                "message": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )


@router.post("/test", response_model=Dict[str, Any])
async def test_chat_endpoint(
    current_user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Test endpoint for chat functionality validation.
    
    Enhanced for AID-US-007 with quota enforcement testing.
    Returns service status and user information for testing.
    """
    try:
        # Get available models
        models = await chat_service.get_available_models(db)
        
        # Get quota info
        quota = await chat_service.get_usage_quota_info(current_user, db)
        
        # Get health status
        health = await chat_service.get_health_status(db)
        
        # Test quota checking
        quota_check_result = None
        if models.default_model:
            try:
                # Get default model for quota check
                default_model = await chat_service._get_default_model(db)
                can_proceed, message, quota_info = await chat_service._check_quota_comprehensive(
                    db, current_user.department_id, default_model.id, 100  # Test with 100 tokens
                )
                quota_check_result = {
                    "can_proceed": can_proceed,
                    "message": message,
                    "quota_info": quota_info
                }
            except Exception as e:
                quota_check_result = {
                    "error": str(e)
                }
        
        return {
            "status": "chat_service_ready",
            "user": {
                "id": str(current_user.id),
                "username": current_user.username,
                "department": current_user.department_name
            },
            "models_available": models.total_count,
            "default_model": models.default_model.get("model_name") if models.default_model else None,
            "quota_status": {
                "limit": quota.monthly_limit,
                "used": quota.current_usage,
                "remaining": quota.remaining_tokens,
                "exceeded": quota.quota_exceeded,
                "percentage": quota.usage_percentage
            },
            "quota_enforcement": quota_check_result,
            "service_health": health.status,
            "quota_system_status": health.quota_status,
            "ready_for_chat": (
                health.status == "healthy" and 
                not quota.quota_exceeded and 
                quota_check_result and 
                quota_check_result.get("can_proceed", False)
            ),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "ready_for_chat": False,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
