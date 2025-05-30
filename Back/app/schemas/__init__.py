"""
Pydantic schemas for AI Dock App API.

This package contains request and response models for data validation.
"""

from .auth import (
    # Request schemas
    LoginRequest,
    RefreshTokenRequest,
    LogoutRequest,
    
    # Response schemas  
    TokenResponse,
    AccessTokenResponse,
    UserProfile,
    LogoutResponse,
    
    # Error schemas
    ErrorDetail,
    ErrorResponse,
    
    # Validation schemas
    PasswordStrengthCheck,
    
    # Utility schemas
    HealthCheck,
)

from .llm_config import (
    # Base schemas
    LLMConfigBase,
    LLMConfigCreate,
    LLMConfigUpdate,
    LLMConfigResponse,
    
    # JSON configuration schemas
    LLMConfigurationJSON,
    LLMConfigurationJSONInput,
    
    # Validation schemas
    ValidationIssue,
    ValidationResult,
    LLMConfigValidationResponse,
    
    # List and bulk response schemas
    LLMConfigListResponse,
    BulkLLMConfigUpdate,
    BulkLLMConfigResponse,
    
    # Statistics and provider schemas
    LLMConfigStats,
    ProviderInfo,
    ProvidersResponse,
)

from .chat import (
    # Message schemas
    ChatMessage,
    ChatSendRequest,
    ChatSendResponse,
    
    # Model schemas
    AvailableModelsResponse,
    ModelInfo,
    
    # Error and stats schemas
    ChatErrorResponse,
    ChatStatsResponse,
    UsageQuotaInfo,
    ChatHealthResponse,
)

__all__ = [
    # Authentication schemas
    "LoginRequest",
    "RefreshTokenRequest",
    "LogoutRequest",
    "TokenResponse", 
    "AccessTokenResponse",
    "UserProfile",
    "LogoutResponse",
    
    # Common schemas
    "ErrorDetail",
    "ErrorResponse",
    "PasswordStrengthCheck",
    "HealthCheck",
    
    # LLM Configuration schemas
    "LLMConfigBase",
    "LLMConfigCreate",
    "LLMConfigUpdate",
    "LLMConfigResponse",
    "LLMConfigurationJSON",
    "LLMConfigurationJSONInput",
    "ValidationIssue",
    "ValidationResult",
    "LLMConfigValidationResponse",
    "LLMConfigListResponse",
    "BulkLLMConfigUpdate",
    "BulkLLMConfigResponse",
    "LLMConfigStats",
    "ProviderInfo",
    "ProvidersResponse",
    
    # Chat schemas
    "ChatMessage",
    "ChatSendRequest",
    "ChatSendResponse",
    "AvailableModelsResponse",
    "ModelInfo",
    "ChatErrorResponse",
    "ChatStatsResponse",
    "UsageQuotaInfo",
    "ChatHealthResponse",
]
