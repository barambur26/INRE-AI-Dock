"""
Pydantic schemas for quota management operations.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field, validator


class QuotaType(str, Enum):
    """Types of quotas supported."""
    MONTHLY_TOKENS = "monthly_tokens"
    DAILY_TOKENS = "daily_tokens" 
    MONTHLY_REQUESTS = "monthly_requests"
    DAILY_REQUESTS = "daily_requests"


class QuotaTemplate(str, Enum):
    """Predefined quota templates."""
    SMALL_DEPARTMENT = "small_department"
    MEDIUM_DEPARTMENT = "medium_department"
    LARGE_DEPARTMENT = "large_department"
    UNLIMITED = "unlimited"


class QuotaEnforcement(str, Enum):
    """Quota enforcement modes."""
    SOFT_WARNING = "soft_warning"  # Allow usage with warnings
    HARD_BLOCK = "hard_block"      # Block usage when exceeded


# Base Quota Schemas
class QuotaBase(BaseModel):
    """Base quota schema with common fields."""
    department_id: UUID = Field(..., description="Department ID this quota applies to")
    llm_config_id: UUID = Field(..., description="LLM configuration ID this quota applies to")
    monthly_limit_tokens: int = Field(default=0, ge=0, description="Monthly token limit (0 = unlimited)")
    daily_limit_tokens: int = Field(default=0, ge=0, description="Daily token limit (0 = unlimited)")
    monthly_limit_requests: int = Field(default=0, ge=0, description="Monthly request limit (0 = unlimited)")
    daily_limit_requests: int = Field(default=0, ge=0, description="Daily request limit (0 = unlimited)")
    enforcement_mode: QuotaEnforcement = Field(default=QuotaEnforcement.SOFT_WARNING, description="Enforcement mode for quota violations")
    warning_threshold_percent: int = Field(default=80, ge=0, le=100, description="Warning threshold percentage (0-100)")


class QuotaCreate(QuotaBase):
    """Schema for creating a new quota."""
    
    @validator('monthly_limit_tokens', 'daily_limit_tokens', 'monthly_limit_requests', 'daily_limit_requests')
    def validate_limits(cls, v):
        """Ensure limits are non-negative."""
        if v < 0:
            raise ValueError('Quota limits must be non-negative')
        return v


class QuotaUpdate(BaseModel):
    """Schema for updating a quota."""
    monthly_limit_tokens: Optional[int] = Field(None, ge=0)
    daily_limit_tokens: Optional[int] = Field(None, ge=0) 
    monthly_limit_requests: Optional[int] = Field(None, ge=0)
    daily_limit_requests: Optional[int] = Field(None, ge=0)
    enforcement_mode: Optional[QuotaEnforcement] = None
    warning_threshold_percent: Optional[int] = Field(None, ge=0, le=100)
    
    @validator('monthly_limit_tokens', 'daily_limit_tokens', 'monthly_limit_requests', 'daily_limit_requests')
    def validate_limits(cls, v):
        """Ensure limits are non-negative if provided."""
        if v is not None and v < 0:
            raise ValueError('Quota limits must be non-negative')
        return v


class QuotaResponse(QuotaBase):
    """Schema for quota response."""
    id: UUID
    current_usage_tokens: int = Field(default=0, description="Current month token usage")
    current_daily_usage_tokens: int = Field(default=0, description="Current day token usage")
    current_usage_requests: int = Field(default=0, description="Current month request usage")
    current_daily_usage_requests: int = Field(default=0, description="Current day request usage")
    last_reset: datetime
    created_at: datetime
    updated_at: datetime
    
    # Calculated fields
    monthly_usage_percentage: float = Field(default=0.0, description="Monthly token usage percentage")
    daily_usage_percentage: float = Field(default=0.0, description="Daily token usage percentage")
    is_quota_exceeded: bool = Field(default=False, description="Whether any quota is exceeded")
    is_warning_threshold_reached: bool = Field(default=False, description="Whether warning threshold is reached")
    
    class Config:
        from_attributes = True


class QuotaWithDetails(QuotaResponse):
    """Schema for quota response with department and LLM details."""
    department_name: str
    llm_model_name: str
    llm_provider: str


class QuotaUsageStats(BaseModel):
    """Schema for quota usage statistics."""
    quota_id: UUID
    department_name: str
    llm_model_name: str
    monthly_tokens_used: int
    monthly_tokens_limit: int
    daily_tokens_used: int
    daily_tokens_limit: int
    monthly_requests_used: int
    monthly_requests_limit: int
    daily_requests_used: int
    daily_requests_limit: int
    usage_percentage: float
    enforcement_mode: QuotaEnforcement
    is_exceeded: bool
    days_until_reset: int


# Bulk Operations Schemas
class BulkQuotaCreate(BaseModel):
    """Schema for bulk quota creation."""
    department_ids: List[UUID] = Field(..., description="List of department IDs")
    llm_config_ids: List[UUID] = Field(..., description="List of LLM configuration IDs")
    quota_template: Optional[QuotaTemplate] = Field(None, description="Template to apply")
    quota_settings: Optional[QuotaBase] = Field(None, description="Custom quota settings")
    
    @validator('department_ids', 'llm_config_ids')
    def validate_non_empty_lists(cls, v):
        """Ensure lists are not empty."""
        if not v:
            raise ValueError('Lists cannot be empty')
        return v


class BulkQuotaUpdate(BaseModel):
    """Schema for bulk quota updates."""
    quota_ids: List[UUID] = Field(..., description="List of quota IDs to update")
    updates: QuotaUpdate = Field(..., description="Updates to apply")


class BulkQuotaResponse(BaseModel):
    """Schema for bulk quota operation response."""
    success_count: int
    error_count: int
    created_quotas: List[UUID] = Field(default_factory=list)
    errors: List[Dict[str, Any]] = Field(default_factory=list)


# Template Schemas
class QuotaTemplateSettings(BaseModel):
    """Schema for quota template settings."""
    name: str
    description: str
    monthly_limit_tokens: int
    daily_limit_tokens: int
    monthly_limit_requests: int
    daily_limit_requests: int
    enforcement_mode: QuotaEnforcement
    warning_threshold_percent: int


class QuotaTemplatesResponse(BaseModel):
    """Schema for available quota templates."""
    templates: List[QuotaTemplateSettings]


# List and Filter Schemas
class QuotaListResponse(BaseModel):
    """Schema for paginated quota list response."""
    quotas: List[QuotaWithDetails]
    total: int
    page: int
    page_size: int
    total_pages: int


class QuotaFilters(BaseModel):
    """Schema for quota filtering options."""
    department_id: Optional[UUID] = None
    llm_config_id: Optional[UUID] = None
    enforcement_mode: Optional[QuotaEnforcement] = None
    exceeded_only: Optional[bool] = False
    warning_only: Optional[bool] = False


# Statistics and Dashboard Schemas
class QuotaOverviewStats(BaseModel):
    """Schema for quota overview statistics."""
    total_quotas: int
    quotas_exceeded: int
    quotas_at_warning: int
    departments_with_quotas: int
    llm_configs_with_quotas: int
    average_usage_percentage: float
    top_usage_departments: List[Dict[str, Any]]
    quota_enforcement_breakdown: Dict[str, int]


class DepartmentQuotaSummary(BaseModel):
    """Schema for department quota summary."""
    department_id: UUID
    department_name: str
    total_quotas: int
    exceeded_quotas: int
    warning_quotas: int
    total_monthly_tokens_used: int
    total_monthly_tokens_limit: int
    overall_usage_percentage: float


class QuotaAlert(BaseModel):
    """Schema for quota alerts."""
    quota_id: UUID
    department_name: str
    llm_model_name: str
    alert_type: str  # "warning", "exceeded", "reset"
    message: str
    usage_percentage: float
    timestamp: datetime


class QuotaAlertsResponse(BaseModel):
    """Schema for quota alerts response."""
    alerts: List[QuotaAlert]
    total_alerts: int
    unread_alerts: int


# Reset and Management Schemas
class QuotaResetRequest(BaseModel):
    """Schema for quota reset request."""
    quota_ids: List[UUID] = Field(..., description="List of quota IDs to reset")
    reset_type: str = Field(default="monthly", description="Type of reset: monthly, daily, or both")


class QuotaResetResponse(BaseModel):
    """Schema for quota reset response."""
    success_count: int
    error_count: int
    reset_quotas: List[UUID] = Field(default_factory=list)
    errors: List[Dict[str, Any]] = Field(default_factory=list)
