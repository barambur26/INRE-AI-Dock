"""
Quota service layer for department quota management.
"""
import uuid
from datetime import datetime, timedelta, date
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc, or_

from app.models import DepartmentQuota, Department, LLMConfiguration, UsageLog, User
from app.schemas.quota import (
    QuotaCreate, QuotaUpdate, QuotaResponse, QuotaWithDetails,
    QuotaTemplate, QuotaEnforcement, QuotaTemplateSettings,
    QuotaFilters, QuotaUsageStats, QuotaOverviewStats,
    DepartmentQuotaSummary, QuotaAlert, BulkQuotaCreate,
    BulkQuotaUpdate, QuotaResetRequest
)
from app.schemas.quota import QuotaBase


class QuotaService:
    """Service class for quota management operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    # Basic CRUD Operations
    async def get_quotas(
        self, 
        skip: int = 0, 
        limit: int = 100,
        filters: Optional[QuotaFilters] = None
    ) -> Dict[str, Any]:
        """Get paginated list of quotas with filters."""
        query = self.db.query(DepartmentQuota)
        
        # Apply filters
        if filters:
            if filters.department_id:
                query = query.filter(DepartmentQuota.department_id == filters.department_id)
            
            if filters.llm_config_id:
                query = query.filter(DepartmentQuota.llm_config_id == filters.llm_config_id)
            
            if filters.enforcement_mode:
                # Note: enforcement_mode is not in the original model, but we'll add it in extended version
                pass
            
            if filters.exceeded_only:
                query = query.filter(DepartmentQuota.current_usage_tokens >= DepartmentQuota.monthly_limit_tokens)
            
            if filters.warning_only:
                # Quotas at 80%+ usage (default warning threshold)
                query = query.filter(
                    and_(
                        DepartmentQuota.monthly_limit_tokens > 0,
                        DepartmentQuota.current_usage_tokens >= (DepartmentQuota.monthly_limit_tokens * 0.8)
                    )
                )
        
        # Get total count
        total = query.count()
        
        # Apply pagination and get results
        quotas = query.offset(skip).limit(limit).all()
        
        # Format quotas with department and LLM details
        quotas_with_details = []
        for quota in quotas:
            quota_dict = await self._format_quota_with_details(quota)
            quotas_with_details.append(quota_dict)
        
        return {
            'quotas': quotas_with_details,
            'total': total,
            'page': (skip // limit) + 1 if limit > 0 else 1,
            'page_size': limit,
            'total_pages': (total + limit - 1) // limit if limit > 0 else 1
        }
    
    async def get_quota_by_id(self, quota_id: uuid.UUID) -> Optional[DepartmentQuota]:
        """Get quota by ID."""
        return self.db.query(DepartmentQuota).filter(DepartmentQuota.id == quota_id).first()
    
    async def get_quota_by_department_and_llm(
        self, 
        department_id: uuid.UUID, 
        llm_config_id: uuid.UUID
    ) -> Optional[DepartmentQuota]:
        """Get quota by department and LLM configuration."""
        return self.db.query(DepartmentQuota).filter(
            and_(
                DepartmentQuota.department_id == department_id,
                DepartmentQuota.llm_config_id == llm_config_id
            )
        ).first()
    
    async def create_quota(self, quota_data: QuotaCreate) -> DepartmentQuota:
        """Create a new quota."""
        # Check if quota already exists for this department-LLM combination
        existing_quota = await self.get_quota_by_department_and_llm(
            quota_data.department_id, 
            quota_data.llm_config_id
        )
        if existing_quota:
            raise ValueError(
                f"Quota already exists for department {quota_data.department_id} "
                f"and LLM configuration {quota_data.llm_config_id}"
            )
        
        # Validate department exists
        department = self.db.query(Department).filter(Department.id == quota_data.department_id).first()
        if not department:
            raise ValueError(f"Department with ID {quota_data.department_id} not found")
        
        # Validate LLM configuration exists
        llm_config = self.db.query(LLMConfiguration).filter(LLMConfiguration.id == quota_data.llm_config_id).first()
        if not llm_config:
            raise ValueError(f"LLM configuration with ID {quota_data.llm_config_id} not found")
        
        # Create quota with extended fields (we'll need to extend the model)
        db_quota = DepartmentQuota(
            department_id=quota_data.department_id,
            llm_config_id=quota_data.llm_config_id,
            monthly_limit_tokens=quota_data.monthly_limit_tokens,
            current_usage_tokens=0,
            last_reset=datetime.utcnow()
        )
        
        self.db.add(db_quota)
        self.db.commit()
        self.db.refresh(db_quota)
        
        return db_quota
    
    async def update_quota(self, quota_id: uuid.UUID, quota_data: QuotaUpdate) -> Optional[DepartmentQuota]:
        """Update an existing quota."""
        db_quota = await self.get_quota_by_id(quota_id)
        if not db_quota:
            return None
        
        # Update fields
        update_data = quota_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(db_quota, field):
                setattr(db_quota, field, value)
        
        db_quota.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(db_quota)
        
        return db_quota
    
    async def delete_quota(self, quota_id: uuid.UUID) -> bool:
        """Delete a quota."""
        db_quota = await self.get_quota_by_id(quota_id)
        if not db_quota:
            return False
        
        self.db.delete(db_quota)
        self.db.commit()
        
        return True
    
    # Bulk Operations
    async def create_bulk_quotas(self, bulk_data: BulkQuotaCreate) -> Dict[str, Any]:
        """Create multiple quotas in bulk."""
        success_count = 0
        error_count = 0
        created_quotas = []
        errors = []
        
        # Get quota settings from template or custom settings
        quota_settings = await self._get_quota_settings_from_template_or_custom(
            bulk_data.quota_template,
            bulk_data.quota_settings
        )
        
        # Create quotas for each department-LLM combination
        for department_id in bulk_data.department_ids:
            for llm_config_id in bulk_data.llm_config_ids:
                try:
                    quota_create = QuotaCreate(
                        department_id=department_id,
                        llm_config_id=llm_config_id,
                        **quota_settings
                    )
                    
                    quota = await self.create_quota(quota_create)
                    created_quotas.append(quota.id)
                    success_count += 1
                    
                except Exception as e:
                    error_count += 1
                    errors.append({
                        'department_id': str(department_id),
                        'llm_config_id': str(llm_config_id),
                        'error': str(e)
                    })
        
        return {
            'success_count': success_count,
            'error_count': error_count,
            'created_quotas': created_quotas,
            'errors': errors
        }
    
    async def update_bulk_quotas(self, bulk_data: BulkQuotaUpdate) -> Dict[str, Any]:
        """Update multiple quotas in bulk."""
        success_count = 0
        error_count = 0
        errors = []
        
        for quota_id in bulk_data.quota_ids:
            try:
                await self.update_quota(quota_id, bulk_data.updates)
                success_count += 1
            except Exception as e:
                error_count += 1
                errors.append({
                    'quota_id': str(quota_id),
                    'error': str(e)
                })
        
        return {
            'success_count': success_count,
            'error_count': error_count,
            'errors': errors
        }
    
    # Department-specific methods
    async def get_department_quotas(self, department_id: uuid.UUID) -> List[DepartmentQuota]:
        """Get all quotas for a specific department."""
        return self.db.query(DepartmentQuota).filter(
            DepartmentQuota.department_id == department_id
        ).all()
    
    async def get_department_quota_summary(self, department_id: uuid.UUID) -> DepartmentQuotaSummary:
        """Get quota summary for a department."""
        quotas = await self.get_department_quotas(department_id)
        
        # Get department name
        department = self.db.query(Department).filter(Department.id == department_id).first()
        department_name = department.name if department else "Unknown"
        
        total_quotas = len(quotas)
        exceeded_quotas = sum(1 for q in quotas if q.is_quota_exceeded)
        warning_quotas = sum(1 for q in quotas if q.usage_percentage >= 80 and not q.is_quota_exceeded)
        
        total_monthly_tokens_used = sum(q.current_usage_tokens for q in quotas)
        total_monthly_tokens_limit = sum(q.monthly_limit_tokens for q in quotas if q.monthly_limit_tokens > 0)
        
        overall_usage_percentage = 0.0
        if total_monthly_tokens_limit > 0:
            overall_usage_percentage = (total_monthly_tokens_used / total_monthly_tokens_limit) * 100
        
        return DepartmentQuotaSummary(
            department_id=department_id,
            department_name=department_name,
            total_quotas=total_quotas,
            exceeded_quotas=exceeded_quotas,
            warning_quotas=warning_quotas,
            total_monthly_tokens_used=total_monthly_tokens_used,
            total_monthly_tokens_limit=total_monthly_tokens_limit,
            overall_usage_percentage=overall_usage_percentage
        )
    
    # Usage and Statistics
    async def update_quota_usage(
        self, 
        department_id: uuid.UUID, 
        llm_config_id: uuid.UUID, 
        tokens_used: int
    ) -> Optional[DepartmentQuota]:
        """Update quota usage after an LLM request."""
        quota = await self.get_quota_by_department_and_llm(department_id, llm_config_id)
        if not quota:
            # Create a default quota if none exists
            quota = await self.create_quota(QuotaCreate(
                department_id=department_id,
                llm_config_id=llm_config_id,
                monthly_limit_tokens=0,  # Unlimited by default
                daily_limit_tokens=0,
                monthly_limit_requests=0,
                daily_limit_requests=0
            ))
        
        # Update usage
        quota.current_usage_tokens += tokens_used
        quota.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(quota)
        
        return quota
    
    # ============================================================================
    # AID-US-007 Phase 1: Enhanced Quota Enforcement Methods
    # ============================================================================
    
    async def validate_request_quota(
        self,
        department_id: uuid.UUID,
        llm_config_id: uuid.UUID,
        estimated_tokens: int,
        include_response_estimate: bool = True
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Comprehensive quota validation for incoming requests (AID-US-007 Phase 1).
        
        This is the main method used by chat_service for pre-request quota checking.
        
        Args:
            department_id: Department making the request
            llm_config_id: LLM model being used
            estimated_tokens: Estimated tokens for the request
            include_response_estimate: Whether to include response tokens in estimation
            
        Returns:
            (can_proceed: bool, message: str, quota_details: dict)
        """
        quota = await self.get_quota_by_department_and_llm(department_id, llm_config_id)
        
        # If no quota exists, create a default one
        if not quota:
            quota = await self._create_default_quota_if_missing(
                department_id, llm_config_id
            )
        
        # If quota is unlimited (0), allow request
        if quota.monthly_limit_tokens == 0:
            return True, "No quota limits applied", {
                "quota_id": str(quota.id),
                "unlimited": True,
                "current_usage": quota.current_usage_tokens,
                "estimated_tokens": estimated_tokens
            }
        
        # Calculate projected usage
        would_be_usage = quota.current_usage_tokens + estimated_tokens
        current_percentage = (quota.current_usage_tokens / quota.monthly_limit_tokens) * 100
        projected_percentage = (would_be_usage / quota.monthly_limit_tokens) * 100
        
        quota_details = {
            "quota_id": str(quota.id),
            "current_usage": quota.current_usage_tokens,
            "limit": quota.monthly_limit_tokens,
            "estimated_tokens": estimated_tokens,
            "would_be_usage": would_be_usage,
            "usage_percentage_now": current_percentage,
            "usage_percentage_after": projected_percentage,
            "remaining_tokens": max(0, quota.monthly_limit_tokens - quota.current_usage_tokens),
            "warning_threshold": quota.monthly_limit_tokens * 0.8,
            "is_currently_exceeded": quota.current_usage_tokens >= quota.monthly_limit_tokens
        }
        
        # Check hard limit violation
        if would_be_usage > quota.monthly_limit_tokens:
            excess_tokens = would_be_usage - quota.monthly_limit_tokens
            message = (
                f"Request would exceed monthly quota limit. "
                f"Current usage: {quota.current_usage_tokens:,}/{quota.monthly_limit_tokens:,} tokens "
                f"({current_percentage:.1f}%). "
                f"Estimated request: {estimated_tokens:,} tokens. "
                f"Would exceed by {excess_tokens:,} tokens."
            )
            return False, message, quota_details
        
        # Check warning threshold (80% by default)
        warning_threshold = quota.monthly_limit_tokens * 0.8
        if would_be_usage >= warning_threshold:
            message = (
                f"Quota warning: After this request, you will have used "
                f"{projected_percentage:.1f}% of your monthly quota "
                f"({would_be_usage:,}/{quota.monthly_limit_tokens:,} tokens). "
                f"Consider monitoring usage carefully."
            )
            return True, message, quota_details
        
        # All clear
        message = (
            f"Within quota limits. Current usage: {current_percentage:.1f}% "
            f"({quota.current_usage_tokens:,}/{quota.monthly_limit_tokens:,} tokens). "
            f"After request: {projected_percentage:.1f}%."
        )
        return True, message, quota_details
    
    async def get_quota_enforcement_status(
        self,
        department_id: uuid.UUID,
        llm_config_id: uuid.UUID
    ) -> Dict[str, Any]:
        """
        Get detailed quota enforcement status for a department-model combination.
        
        Returns comprehensive quota information for monitoring and display.
        """
        quota = await self.get_quota_by_department_and_llm(department_id, llm_config_id)
        
        if not quota:
            return {
                "exists": False,
                "message": "No quota configured",
                "enforcement_active": False,
                "can_create_default": True
            }
        
        # Get department and LLM details
        department = self.db.query(Department).filter(Department.id == department_id).first()
        llm_config = self.db.query(LLMConfiguration).filter(LLMConfiguration.id == llm_config_id).first()
        
        current_percentage = quota.usage_percentage if quota.monthly_limit_tokens > 0 else 0
        is_exceeded = quota.is_quota_exceeded
        is_warning = current_percentage >= 80 and not is_exceeded
        remaining_tokens = max(0, quota.monthly_limit_tokens - quota.current_usage_tokens)
        
        # Determine status color and message
        if is_exceeded:
            status_color = "red"
            status_message = "Quota Exceeded"
        elif is_warning:
            status_color = "yellow"
            status_message = "Quota Warning"
        elif quota.monthly_limit_tokens == 0:
            status_color = "gray"
            status_message = "Unlimited"
        else:
            status_color = "green"
            status_message = "Within Limits"
        
        return {
            "exists": True,
            "quota_id": str(quota.id),
            "department_name": department.name if department else "Unknown",
            "llm_model_name": llm_config.model_name if llm_config else "Unknown",
            "monthly_limit": quota.monthly_limit_tokens,
            "current_usage": quota.current_usage_tokens,
            "usage_percentage": current_percentage,
            "remaining_tokens": remaining_tokens,
            "is_exceeded": is_exceeded,
            "is_warning": is_warning,
            "is_unlimited": quota.monthly_limit_tokens == 0,
            "status_color": status_color,
            "status_message": status_message,
            "enforcement_active": quota.monthly_limit_tokens > 0,
            "last_updated": quota.updated_at or quota.created_at,
            "last_reset": quota.last_reset,
            "can_send_requests": not is_exceeded
        }
    
    async def estimate_request_cost(
        self,
        department_id: uuid.UUID,
        llm_config_id: uuid.UUID,
        estimated_tokens: int
    ) -> Dict[str, Any]:
        """
        Estimate the quota cost of a request without actually using tokens.
        
        Useful for pre-request planning and user feedback.
        """
        quota = await self.get_quota_by_department_and_llm(department_id, llm_config_id)
        
        if not quota or quota.monthly_limit_tokens == 0:
            return {
                "has_quota": quota is not None,
                "is_unlimited": True,
                "estimated_cost_tokens": estimated_tokens,
                "estimated_cost_percentage": 0.0,
                "impact": "none"
            }
        
        current_percentage = (quota.current_usage_tokens / quota.monthly_limit_tokens) * 100
        projected_percentage = ((quota.current_usage_tokens + estimated_tokens) / quota.monthly_limit_tokens) * 100
        percentage_impact = projected_percentage - current_percentage
        
        # Determine impact level
        if projected_percentage > 100:
            impact = "exceeds_quota"
        elif projected_percentage >= 95:
            impact = "high"
        elif projected_percentage >= 80:
            impact = "medium"
        elif percentage_impact >= 10:
            impact = "low"
        else:
            impact = "minimal"
        
        return {
            "has_quota": True,
            "is_unlimited": False,
            "estimated_cost_tokens": estimated_tokens,
            "estimated_cost_percentage": percentage_impact,
            "current_percentage": current_percentage,
            "projected_percentage": projected_percentage,
            "impact": impact,
            "would_exceed": projected_percentage > 100,
            "would_trigger_warning": projected_percentage >= 80 and current_percentage < 80
        }
    
    async def _create_default_quota_if_missing(
        self,
        department_id: uuid.UUID,
        llm_config_id: uuid.UUID,
        default_limit: int = 10000
    ) -> DepartmentQuota:
        """
        Create a default quota if none exists for a department-model combination.
        
        This prevents requests from failing due to missing quota configuration.
        """
        try:
            quota_data = QuotaCreate(
                department_id=department_id,
                llm_config_id=llm_config_id,
                monthly_limit_tokens=default_limit,
                daily_limit_tokens=0,  # No daily limit by default
                monthly_limit_requests=0,  # No request limit by default
                daily_limit_requests=0,
                enforcement_mode=QuotaEnforcement.SOFT_WARNING,
                warning_threshold_percent=80
            )
            
            return await self.create_quota(quota_data)
            
        except Exception as e:
            # If creation fails (e.g., department doesn't exist), create a minimal quota
            minimal_quota = DepartmentQuota(
                department_id=department_id,
                llm_config_id=llm_config_id,
                monthly_limit_tokens=default_limit,
                current_usage_tokens=0,
                last_reset=datetime.utcnow()
            )
            
            self.db.add(minimal_quota)
            self.db.commit()
            self.db.refresh(minimal_quota)
            
            return minimal_quota
    
    # Enhanced version of existing method for AID-US-007
    async def check_quota_limits(
        self, 
        department_id: uuid.UUID, 
        llm_config_id: uuid.UUID, 
        tokens_requested: int = 0
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Enhanced quota checking method (wrapper around validate_request_quota).
        
        Maintained for backward compatibility but delegates to the new enhanced method.
        """
        return await self.validate_request_quota(
            department_id=department_id,
            llm_config_id=llm_config_id,
            estimated_tokens=tokens_requested,
            include_response_estimate=True
        )
    
    async def get_quota_overview_stats(self) -> QuotaOverviewStats:
        """Get overview statistics for all quotas."""
        quotas = self.db.query(DepartmentQuota).all()
        
        total_quotas = len(quotas)
        quotas_exceeded = sum(1 for q in quotas if q.is_quota_exceeded)
        quotas_at_warning = sum(1 for q in quotas if q.usage_percentage >= 80 and not q.is_quota_exceeded)
        
        departments_with_quotas = len(set(q.department_id for q in quotas))
        llm_configs_with_quotas = len(set(q.llm_config_id for q in quotas))
        
        # Calculate average usage percentage (excluding unlimited quotas)
        limited_quotas = [q for q in quotas if q.monthly_limit_tokens > 0]
        average_usage_percentage = 0.0
        if limited_quotas:
            average_usage_percentage = sum(q.usage_percentage for q in limited_quotas) / len(limited_quotas)
        
        # Top usage departments
        department_usage = {}
        for quota in quotas:
            dept_id = quota.department_id
            if dept_id not in department_usage:
                dept = self.db.query(Department).filter(Department.id == dept_id).first()
                department_usage[dept_id] = {
                    'name': dept.name if dept else 'Unknown',
                    'usage': 0,
                    'limit': 0
                }
            department_usage[dept_id]['usage'] += quota.current_usage_tokens
            department_usage[dept_id]['limit'] += quota.monthly_limit_tokens
        
        # Sort by usage percentage
        top_usage_departments = []
        for dept_id, data in department_usage.items():
            if data['limit'] > 0:
                percentage = (data['usage'] / data['limit']) * 100
                top_usage_departments.append({
                    'department_name': data['name'],
                    'usage_percentage': percentage,
                    'tokens_used': data['usage'],
                    'tokens_limit': data['limit']
                })
        
        top_usage_departments.sort(key=lambda x: x['usage_percentage'], reverse=True)
        top_usage_departments = top_usage_departments[:5]  # Top 5
        
        # Quota enforcement breakdown - for now, assume all are soft warning
        quota_enforcement_breakdown = {
            'soft_warning': total_quotas,
            'hard_block': 0
        }
        
        return QuotaOverviewStats(
            total_quotas=total_quotas,
            quotas_exceeded=quotas_exceeded,
            quotas_at_warning=quotas_at_warning,
            departments_with_quotas=departments_with_quotas,
            llm_configs_with_quotas=llm_configs_with_quotas,
            average_usage_percentage=average_usage_percentage,
            top_usage_departments=top_usage_departments,
            quota_enforcement_breakdown=quota_enforcement_breakdown
        )
    
    # Alerts and Monitoring
    async def get_quota_alerts(self, limit: int = 50) -> List[QuotaAlert]:
        """Get quota alerts for exceeded or warning quotas."""
        quotas = self.db.query(DepartmentQuota).all()
        alerts = []
        
        for quota in quotas:
            # Get department and LLM names
            department = self.db.query(Department).filter(Department.id == quota.department_id).first()
            llm_config = self.db.query(LLMConfiguration).filter(LLMConfiguration.id == quota.llm_config_id).first()
            
            department_name = department.name if department else "Unknown"
            llm_model_name = llm_config.model_name if llm_config else "Unknown"
            
            if quota.is_quota_exceeded:
                alerts.append(QuotaAlert(
                    quota_id=quota.id,
                    department_name=department_name,
                    llm_model_name=llm_model_name,
                    alert_type="exceeded",
                    message=f"Monthly quota exceeded: {quota.current_usage_tokens}/{quota.monthly_limit_tokens} tokens",
                    usage_percentage=quota.usage_percentage,
                    timestamp=datetime.utcnow()
                ))
            elif quota.usage_percentage >= 80:
                alerts.append(QuotaAlert(
                    quota_id=quota.id,
                    department_name=department_name,
                    llm_model_name=llm_model_name,
                    alert_type="warning",
                    message=f"Quota warning: {quota.usage_percentage:.1f}% used ({quota.current_usage_tokens}/{quota.monthly_limit_tokens} tokens)",
                    usage_percentage=quota.usage_percentage,
                    timestamp=datetime.utcnow()
                ))
        
        # Sort by usage percentage (highest first)
        alerts.sort(key=lambda x: x.usage_percentage, reverse=True)
        
        return alerts[:limit]
    
    # Templates and Presets
    async def get_quota_templates(self) -> List[QuotaTemplateSettings]:
        """Get available quota templates."""
        templates = [
            QuotaTemplateSettings(
                name="Small Department",
                description="Suitable for small teams (5-10 users)",
                monthly_limit_tokens=100000,  # 100K tokens
                daily_limit_tokens=5000,      # 5K tokens
                monthly_limit_requests=1000,  # 1K requests
                daily_limit_requests=50,      # 50 requests
                enforcement_mode=QuotaEnforcement.SOFT_WARNING,
                warning_threshold_percent=80
            ),
            QuotaTemplateSettings(
                name="Medium Department",
                description="Suitable for medium teams (10-25 users)",
                monthly_limit_tokens=250000,  # 250K tokens
                daily_limit_tokens=10000,     # 10K tokens
                monthly_limit_requests=2500,  # 2.5K requests
                daily_limit_requests=100,     # 100 requests
                enforcement_mode=QuotaEnforcement.SOFT_WARNING,
                warning_threshold_percent=80
            ),
            QuotaTemplateSettings(
                name="Large Department",
                description="Suitable for large teams (25+ users)",
                monthly_limit_tokens=500000,  # 500K tokens
                daily_limit_tokens=20000,     # 20K tokens
                monthly_limit_requests=5000,  # 5K requests
                daily_limit_requests=200,     # 200 requests
                enforcement_mode=QuotaEnforcement.SOFT_WARNING,
                warning_threshold_percent=85
            ),
            QuotaTemplateSettings(
                name="Unlimited",
                description="No limits (use with caution)",
                monthly_limit_tokens=0,       # 0 = unlimited
                daily_limit_tokens=0,         # 0 = unlimited
                monthly_limit_requests=0,     # 0 = unlimited
                daily_limit_requests=0,       # 0 = unlimited
                enforcement_mode=QuotaEnforcement.SOFT_WARNING,
                warning_threshold_percent=90
            )
        ]
        return templates
    
    # Reset and Maintenance
    async def reset_quotas(self, reset_request: QuotaResetRequest) -> Dict[str, Any]:
        """Reset quota usage counters."""
        success_count = 0
        error_count = 0
        reset_quotas = []
        errors = []
        
        for quota_id in reset_request.quota_ids:
            try:
                quota = await self.get_quota_by_id(quota_id)
                if not quota:
                    raise ValueError(f"Quota {quota_id} not found")
                
                # Reset based on type
                if reset_request.reset_type in ["monthly", "both"]:
                    quota.current_usage_tokens = 0
                    quota.last_reset = datetime.utcnow()
                
                # Note: daily reset would require additional fields in the model
                
                self.db.commit()
                reset_quotas.append(quota_id)
                success_count += 1
                
            except Exception as e:
                error_count += 1
                errors.append({
                    'quota_id': str(quota_id),
                    'error': str(e)
                })
        
        return {
            'success_count': success_count,
            'error_count': error_count,
            'reset_quotas': reset_quotas,
            'errors': errors
        }
    
    async def auto_reset_monthly_quotas(self):
        """Automatically reset monthly quotas (to be called by scheduler)."""
        today = date.today()
        if today.day == 1:  # First day of month
            quotas = self.db.query(DepartmentQuota).all()
            for quota in quotas:
                quota.current_usage_tokens = 0
                quota.last_reset = datetime.utcnow()
            
            self.db.commit()
    
    # Helper Methods
    async def _format_quota_with_details(self, quota: DepartmentQuota) -> Dict[str, Any]:
        """Format quota with department and LLM details."""
        # Get department and LLM configuration
        department = self.db.query(Department).filter(Department.id == quota.department_id).first()
        llm_config = self.db.query(LLMConfiguration).filter(LLMConfiguration.id == quota.llm_config_id).first()
        
        return {
            'id': quota.id,
            'department_id': quota.department_id,
            'llm_config_id': quota.llm_config_id,
            'monthly_limit_tokens': quota.monthly_limit_tokens,
            'current_usage_tokens': quota.current_usage_tokens,
            'last_reset': quota.last_reset,
            'created_at': quota.created_at,
            'updated_at': quota.updated_at,
            'department_name': department.name if department else 'Unknown',
            'llm_model_name': llm_config.model_name if llm_config else 'Unknown',
            'llm_provider': llm_config.provider if llm_config else 'Unknown',
            'monthly_usage_percentage': quota.usage_percentage,
            'is_quota_exceeded': quota.is_quota_exceeded,
            'is_warning_threshold_reached': quota.usage_percentage >= 80,
            # Extended fields for future use
            'daily_limit_tokens': 0,
            'current_daily_usage_tokens': 0,
            'monthly_limit_requests': 0,
            'current_usage_requests': 0,
            'daily_limit_requests': 0,
            'current_daily_usage_requests': 0,
            'daily_usage_percentage': 0.0,
            'enforcement_mode': 'soft_warning',
            'warning_threshold_percent': 80
        }
    
    async def _get_quota_settings_from_template_or_custom(
        self, 
        template: Optional[QuotaTemplate], 
        custom_settings: Optional[QuotaBase]
    ) -> Dict[str, Any]:
        """Get quota settings from template or custom settings."""
        if custom_settings:
            return custom_settings.dict()
        
        if template:
            templates = await self.get_quota_templates()
            template_map = {
                QuotaTemplate.SMALL_DEPARTMENT: "Small Department",
                QuotaTemplate.MEDIUM_DEPARTMENT: "Medium Department", 
                QuotaTemplate.LARGE_DEPARTMENT: "Large Department",
                QuotaTemplate.UNLIMITED: "Unlimited"
            }
            
            template_name = template_map.get(template)
            if template_name:
                for t in templates:
                    if t.name == template_name:
                        return {
                            'monthly_limit_tokens': t.monthly_limit_tokens,
                            'daily_limit_tokens': t.daily_limit_tokens,
                            'monthly_limit_requests': t.monthly_limit_requests,
                            'daily_limit_requests': t.daily_limit_requests,
                            'enforcement_mode': t.enforcement_mode,
                            'warning_threshold_percent': t.warning_threshold_percent
                        }
        
        # Default settings if no template or custom settings
        return {
            'monthly_limit_tokens': 100000,
            'daily_limit_tokens': 5000,
            'monthly_limit_requests': 1000,
            'daily_limit_requests': 50,
            'enforcement_mode': QuotaEnforcement.SOFT_WARNING,
            'warning_threshold_percent': 80
        }
