"""
Chat business logic service for handling chat operations, quota management, and usage logging.
Enhanced with comprehensive quota enforcement for AID-US-007.
"""
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.models import (
    User, Department, LLMConfiguration, DepartmentQuota, UsageLog
)
from app.schemas.auth import UserProfile
from app.schemas.chat import (
    ChatSendRequest, ChatSendResponse, AvailableModelsResponse, ModelInfo,
    UsageQuotaInfo, ChatStatsResponse, ChatHealthResponse
)
from app.schemas.quota import QuotaEnforcement
from app.services.llm_service import llm_service, LLMProviderError, LLMQuotaExceededError
from app.core.database import get_async_session


class ChatServiceError(Exception):
    """Base exception for chat service errors."""
    pass


class NoAvailableModelsError(ChatServiceError):
    """Exception when no LLM models are available."""
    pass


class QuotaExceededError(ChatServiceError):
    """Exception when department quota is exceeded."""
    def __init__(self, message: str, quota_info: Dict[str, Any] = None):
        super().__init__(message)
        self.quota_info = quota_info or {}


class QuotaWarningError(ChatServiceError):
    """Exception for quota warnings (when near limits)."""
    def __init__(self, message: str, quota_info: Dict[str, Any] = None):
        super().__init__(message)
        self.quota_info = quota_info or {}


class ChatService:
    """Service for managing chat operations and business logic."""
    
    def __init__(self):
        self.default_model_cache = None
        self.cache_expiry = None
    
    async def send_message(
        self, 
        request: ChatSendRequest, 
        user: UserProfile,
        db: AsyncSession
    ) -> ChatSendResponse:
        """
        Send a chat message to an LLM and handle all business logic.
        
        Args:
            request: Chat request with message and optional model_id
            user: Current user information
            db: Database session
            
        Returns:
            Chat response with LLM response and usage information
            
        Raises:
            NoAvailableModelsError: When no LLM models are available
            QuotaExceededError: When department quota is exceeded
            QuotaWarningError: When quota warning threshold is reached
            ChatServiceError: For other chat service errors
        """
        try:
            # 1. Select LLM model (specific or default)
            if request.model_id:
                llm_config = await self._get_model_by_id(db, request.model_id)
                if not llm_config or not llm_config.enabled:
                    raise ChatServiceError(f"Model {request.model_id} not found or disabled")
            else:
                llm_config = await self._get_default_model(db)
            
            # 2. Estimate tokens for quota check (more accurate than fixed value)
            estimated_tokens = await self._estimate_request_tokens(request.message, llm_config)
            
            # 3. Check department quota BEFORE making LLM request
            can_proceed, quota_message, quota_info = await self._check_quota_comprehensive(
                db, user.department_id, llm_config.id, estimated_tokens
            )
            
            # 3a. Handle quota enforcement
            if not can_proceed:
                raise QuotaExceededError(quota_message, quota_info)
            
            # 3b. Check for warnings (but still proceed)
            if "warning" in quota_message.lower():
                # Log warning but continue with request
                print(f"Quota warning for department {user.department_id}: {quota_message}")
            
            # 4. Send message to LLM
            response_text, prompt_tokens, completion_tokens, estimated_cost = await llm_service.send_message(
                message=request.message,
                llm_config=llm_config
            )
            
            # 5. Log usage
            usage_log = await self._log_usage(
                db=db,
                user_id=user.id,
                department_id=user.department_id,
                llm_config_id=llm_config.id,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                estimated_cost=estimated_cost,
                request_details={
                    "message": request.message,
                    "conversation_id": str(request.conversation_id) if request.conversation_id else None,
                    "user_message_length": len(request.message),
                    "estimated_tokens": estimated_tokens,
                    "actual_tokens": prompt_tokens + completion_tokens
                },
                response_details={
                    "response": response_text,
                    "response_length": len(response_text),
                    "model_used": llm_config.model_name
                }
            )
            
            # 6. Update department quota usage
            await self._update_quota_usage(
                db=db,
                department_id=user.department_id,
                llm_config_id=llm_config.id,
                tokens_used=prompt_tokens + completion_tokens
            )
            
            # 7. Create response with quota information
            return ChatSendResponse(
                response=response_text,
                model_used=llm_config.model_name,
                model_id=llm_config.id,
                provider=llm_config.provider,
                tokens_prompt=prompt_tokens,
                tokens_completion=completion_tokens,
                tokens_total=prompt_tokens + completion_tokens,
                cost_estimated=estimated_cost,
                conversation_id=request.conversation_id,
                usage_log_id=usage_log.id
            )
            
        except LLMProviderError as e:
            raise ChatServiceError(f"LLM Provider Error: {e}")
        except QuotaExceededError:
            # Re-raise quota errors as-is
            raise
        except QuotaWarningError:
            # Re-raise warning errors as-is
            raise
        except Exception as e:
            raise ChatServiceError(f"Unexpected error: {e}")
    
    async def get_available_models(self, db: AsyncSession) -> AvailableModelsResponse:
        """Get list of available LLM models."""
        try:
            # Get all enabled LLM configurations
            result = await db.execute(
                select(LLMConfiguration)
                .where(LLMConfiguration.enabled == True)
                .order_by(LLMConfiguration.created_at)
            )
            configurations = result.scalars().all()
            
            # Convert to ModelInfo objects
            models = []
            for config in configurations:
                models.append({
                    "id": str(config.id),
                    "model_name": config.model_name,
                    "provider": config.provider,
                    "enabled": config.enabled,
                    "description": config.config_json.get("description") if config.config_json else None,
                    "capabilities": config.config_json.get("capabilities") if config.config_json else None
                })
            
            # Get default model
            default_model = None
            if models:
                default_config = configurations[0]  # First enabled model
                default_model = {
                    "id": str(default_config.id),
                    "model_name": default_config.model_name,
                    "provider": default_config.provider,
                    "enabled": default_config.enabled
                }
            
            return AvailableModelsResponse(
                models=models,
                default_model=default_model,
                total_count=len(models)
            )
            
        except Exception as e:
            raise ChatServiceError(f"Error getting available models: {e}")
    
    async def get_usage_quota_info(
        self, 
        user: UserProfile, 
        db: AsyncSession
    ) -> UsageQuotaInfo:
        """Get usage quota information for user's department."""
        try:
            # Get department quota for the default model
            default_model = await self._get_default_model(db)
            
            result = await db.execute(
                select(DepartmentQuota)
                .where(
                    DepartmentQuota.department_id == user.department_id,
                    DepartmentQuota.llm_config_id == default_model.id
                )
            )
            quota = result.scalar_one_or_none()
            
            if not quota:
                # Create default quota if not exists
                quota = DepartmentQuota(
                    department_id=user.department_id,
                    llm_config_id=default_model.id,
                    monthly_limit_tokens=10000,  # Default limit
                    current_usage_tokens=0
                )
                db.add(quota)
                await db.commit()
                await db.refresh(quota)
            
            # Calculate remaining tokens
            remaining_tokens = max(0, quota.monthly_limit_tokens - quota.current_usage_tokens)
            
            return UsageQuotaInfo(
                department_name=user.department_name or "Unknown",
                monthly_limit=quota.monthly_limit_tokens,
                current_usage=quota.current_usage_tokens,
                usage_percentage=quota.usage_percentage,
                quota_exceeded=quota.is_quota_exceeded,
                remaining_tokens=remaining_tokens
            )
            
        except Exception as e:
            raise ChatServiceError(f"Error getting quota info: {e}")
    
    async def get_chat_stats(
        self, 
        user: UserProfile, 
        db: AsyncSession
    ) -> ChatStatsResponse:
        """Get chat statistics for the user."""
        try:
            # Get user's usage logs
            result = await db.execute(
                select(
                    func.count(UsageLog.id).label("total_messages"),
                    func.sum(UsageLog.tokens_prompt + UsageLog.tokens_completion).label("total_tokens"),
                    func.sum(UsageLog.cost_estimated).label("total_cost"),
                    func.avg(UsageLog.tokens_prompt + UsageLog.tokens_completion).label("avg_tokens")
                )
                .where(UsageLog.user_id == user.id)
            )
            stats = result.first()
            
            # Get most used model
            result = await db.execute(
                select(
                    LLMConfiguration.model_name,
                    func.count(UsageLog.id).label("usage_count")
                )
                .join(LLMConfiguration, UsageLog.llm_config_id == LLMConfiguration.id)
                .where(UsageLog.user_id == user.id)
                .group_by(LLMConfiguration.model_name)
                .order_by(func.count(UsageLog.id).desc())
                .limit(1)
            )
            most_used_result = result.first()
            most_used_model = most_used_result[0] if most_used_result else None
            
            return ChatStatsResponse(
                total_conversations=1,  # Placeholder - would need conversation tracking
                total_messages=stats.total_messages or 0,
                total_tokens_used=int(stats.total_tokens or 0),
                total_cost=float(stats.total_cost or 0.0),
                most_used_model=most_used_model,
                avg_tokens_per_message=float(stats.avg_tokens or 0.0)
            )
            
        except Exception as e:
            raise ChatServiceError(f"Error getting chat stats: {e}")
    
    async def get_health_status(self, db: AsyncSession) -> ChatHealthResponse:
        """Get chat service health status."""
        try:
            # Count total and enabled models
            total_result = await db.execute(
                select(func.count(LLMConfiguration.id))
            )
            total_models = total_result.scalar() or 0
            
            enabled_result = await db.execute(
                select(func.count(LLMConfiguration.id))
                .where(LLMConfiguration.enabled == True)
            )
            enabled_models = enabled_result.scalar() or 0
            
            # Get default model
            default_model_name = None
            try:
                default_model = await self._get_default_model(db)
                default_model_name = default_model.model_name
            except NoAvailableModelsError:
                pass
            
            status = "healthy" if enabled_models > 0 else "no_models_available"
            
            # Enhanced quota status check
            quota_status = await self._get_overall_quota_status(db)
            
            return ChatHealthResponse(
                status=status,
                available_models=total_models,
                enabled_models=enabled_models,
                default_model=default_model_name,
                quota_status=quota_status,
                timestamp=datetime.now(timezone.utc)
            )
            
        except Exception as e:
            raise ChatServiceError(f"Error getting health status: {e}")
    
    async def _get_default_model(self, db: AsyncSession) -> LLMConfiguration:
        """Get the default (first enabled) LLM model."""
        result = await db.execute(
            select(LLMConfiguration)
            .where(LLMConfiguration.enabled == True)
            .order_by(LLMConfiguration.created_at)
            .limit(1)
        )
        model = result.scalar_one_or_none()
        
        if not model:
            raise NoAvailableModelsError("No enabled LLM models available")
        
        return model
    
    async def _get_model_by_id(self, db: AsyncSession, model_id: UUID) -> Optional[LLMConfiguration]:
        """Get LLM model by ID."""
        result = await db.execute(
            select(LLMConfiguration)
            .where(LLMConfiguration.id == model_id)
        )
        return result.scalar_one_or_none()
    
    async def _estimate_request_tokens(self, message: str, llm_config: LLMConfiguration) -> int:
        """
        Estimate tokens for a request more accurately than using a fixed value.
        This is a simple estimation - in production, you might use tiktoken or similar.
        """
        # Basic estimation: ~4 characters per token (rough average for most models)
        # Add buffer for system prompts and response
        message_tokens = len(message) // 4
        system_prompt_tokens = 50  # Estimated system prompt overhead
        response_buffer = max(100, message_tokens // 2)  # Conservative response estimate
        
        total_estimated = message_tokens + system_prompt_tokens + response_buffer
        
        # Add model-specific adjustments
        if llm_config.provider.lower() == "openai":
            if "gpt-4" in llm_config.model_name.lower():
                total_estimated = int(total_estimated * 1.1)  # GPT-4 tends to use slightly more tokens
            elif "gpt-3.5" in llm_config.model_name.lower():
                total_estimated = int(total_estimated * 0.9)  # GPT-3.5 is more efficient
        
        return max(100, total_estimated)  # Minimum 100 tokens
    
    async def _check_quota_comprehensive(
        self, 
        db: AsyncSession, 
        department_id: UUID, 
        llm_config_id: UUID,
        estimated_tokens: int
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Comprehensive quota checking with detailed information using the enhanced quota service.
        
        This method integrates with the quota_service for AID-US-007 Phase 1.
        
        Returns:
            (can_proceed, message, quota_info)
        """
        from app.services.quota_service import QuotaService
        from sqlalchemy.orm import sessionmaker
        
        # Create a sync session for quota_service (temporary solution for Phase 1)
        # TODO: Convert quota_service to fully async in Phase 2
        sync_session = sessionmaker(bind=db.bind.sync_engine if hasattr(db.bind, 'sync_engine') else None)()
        
        try:
            quota_service = QuotaService(sync_session)
            
            # Use the enhanced quota validation method
            can_proceed, message, quota_details = await quota_service.validate_request_quota(
                department_id=department_id,
                llm_config_id=llm_config_id,
                estimated_tokens=estimated_tokens,
                include_response_estimate=True
            )
            
            return can_proceed, message, quota_details
            
        except Exception as e:
            # Fallback to the original quota checking logic if quota service fails
            print(f"Quota service error, using fallback: {e}")
            return await self._check_quota_fallback(db, department_id, llm_config_id, estimated_tokens)
        finally:
            if sync_session:
                sync_session.close()
    
    async def _check_quota_fallback(
        self, 
        db: AsyncSession, 
        department_id: UUID, 
        llm_config_id: UUID,
        estimated_tokens: int
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Fallback quota checking method using direct database queries.
        
        This is used when the quota service is unavailable.
        """
        result = await db.execute(
            select(DepartmentQuota)
            .where(
                DepartmentQuota.department_id == department_id,
                DepartmentQuota.llm_config_id == llm_config_id
            )
        )
        quota = result.scalar_one_or_none()
        
        if not quota:
            # Create default quota if not exists
            quota = DepartmentQuota(
                department_id=department_id,
                llm_config_id=llm_config_id,
                monthly_limit_tokens=10000,  # Default limit
                current_usage_tokens=0
            )
            db.add(quota)
            await db.commit()
            await db.refresh(quota)
        
        # If quota is unlimited (0), allow request
        if quota.monthly_limit_tokens == 0:
            return True, "No quota limits applied", {
                "quota_id": str(quota.id),
                "unlimited": True,
                "current_usage": quota.current_usage_tokens,
                "estimated_tokens": estimated_tokens
            }
        
        # Calculate would-be usage
        would_be_usage = quota.current_usage_tokens + estimated_tokens
        usage_percentage_now = (quota.current_usage_tokens / quota.monthly_limit_tokens) * 100
        usage_percentage_after = (would_be_usage / quota.monthly_limit_tokens) * 100
        
        quota_info = {
            "quota_id": str(quota.id),
            "current_usage": quota.current_usage_tokens,
            "limit": quota.monthly_limit_tokens,
            "estimated_tokens": estimated_tokens,
            "would_be_usage": would_be_usage,
            "usage_percentage_now": usage_percentage_now,
            "usage_percentage_after": usage_percentage_after,
            "remaining_tokens": max(0, quota.monthly_limit_tokens - quota.current_usage_tokens)
        }
        
        # Check hard limit
        if would_be_usage > quota.monthly_limit_tokens:
            return False, (
                f"Monthly quota exceeded. Current usage: {quota.current_usage_tokens:,} tokens, "
                f"Limit: {quota.monthly_limit_tokens:,} tokens, "
                f"Estimated request: {estimated_tokens:,} tokens. "
                f"This request would exceed the limit by {would_be_usage - quota.monthly_limit_tokens:,} tokens."
            ), quota_info
        
        # Check warning threshold (80% by default)
        warning_threshold = quota.monthly_limit_tokens * 0.8
        if would_be_usage >= warning_threshold:
            return True, (
                f"Quota warning: After this request, you will have used "
                f"{usage_percentage_after:.1f}% of your monthly quota "
                f"({would_be_usage:,}/{quota.monthly_limit_tokens:,} tokens)"
            ), quota_info
        
        # All good
        return True, (
            f"Within quota limits. Current usage: {usage_percentage_now:.1f}% "
            f"({quota.current_usage_tokens:,}/{quota.monthly_limit_tokens:,} tokens)"
        ), quota_info
    
    async def _check_quota(
        self, 
        db: AsyncSession, 
        department_id: UUID, 
        llm_config_id: UUID,
        estimated_tokens: int = 1000  # Conservative estimate
    ) -> None:
        """
        Legacy quota check method (kept for backward compatibility).
        Use _check_quota_comprehensive for new implementations.
        """
        can_proceed, message, quota_info = await self._check_quota_comprehensive(
            db, department_id, llm_config_id, estimated_tokens
        )
        
        if not can_proceed:
            raise QuotaExceededError(message, quota_info)
    
    async def _get_overall_quota_status(self, db: AsyncSession) -> str:
        """Get overall quota status for health checks."""
        try:
            # Count quotas that are exceeded
            result = await db.execute(
                select(func.count(DepartmentQuota.id))
                .where(
                    DepartmentQuota.monthly_limit_tokens > 0,  # Exclude unlimited quotas
                    DepartmentQuota.current_usage_tokens >= DepartmentQuota.monthly_limit_tokens
                )
            )
            exceeded_count = result.scalar() or 0
            
            # Count total limited quotas
            result = await db.execute(
                select(func.count(DepartmentQuota.id))
                .where(DepartmentQuota.monthly_limit_tokens > 0)
            )
            total_limited_quotas = result.scalar() or 0
            
            if total_limited_quotas == 0:
                return "no_quotas_configured"
            elif exceeded_count == 0:
                return "all_within_limits"
            elif exceeded_count / total_limited_quotas >= 0.5:
                return "many_quotas_exceeded"
            else:
                return "some_quotas_exceeded"
                
        except Exception:
            return "quota_check_error"
    
    async def _log_usage(
        self,
        db: AsyncSession,
        user_id: UUID,
        department_id: UUID,
        llm_config_id: UUID,
        prompt_tokens: int,
        completion_tokens: int,
        estimated_cost: float,
        request_details: Dict[str, Any],
        response_details: Dict[str, Any]
    ) -> UsageLog:
        """Log LLM usage to the database."""
        usage_log = UsageLog(
            id=uuid.uuid4(),
            user_id=user_id,
            department_id=department_id,
            llm_config_id=llm_config_id,
            timestamp=datetime.now(timezone.utc),
            tokens_prompt=prompt_tokens,
            tokens_completion=completion_tokens,
            cost_estimated=estimated_cost,
            request_details=request_details,
            response_details=response_details
        )
        
        db.add(usage_log)
        await db.commit()
        await db.refresh(usage_log)
        
        return usage_log
    
    async def _update_quota_usage(
        self,
        db: AsyncSession,
        department_id: UUID,
        llm_config_id: UUID,
        tokens_used: int
    ) -> None:
        """Update department quota usage."""
        result = await db.execute(
            select(DepartmentQuota)
            .where(
                DepartmentQuota.department_id == department_id,
                DepartmentQuota.llm_config_id == llm_config_id
            )
        )
        quota = result.scalar_one_or_none()
        
        if quota:
            quota.current_usage_tokens += tokens_used
            await db.commit()


# Global chat service instance
chat_service = ChatService()
