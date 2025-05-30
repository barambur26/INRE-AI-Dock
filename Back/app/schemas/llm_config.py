"""
Pydantic schemas for LLM configuration operations.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from uuid import UUID

from pydantic import BaseModel, Field, validator, root_validator


# LLM Configuration Base Schemas
class LLMConfigBase(BaseModel):
    """Base LLM configuration schema with common fields."""
    model_name: str = Field(..., min_length=1, max_length=100, description="Model name (e.g., 'gpt-4', 'claude-3')")
    provider: str = Field(..., min_length=1, max_length=50, description="Provider name (e.g., 'openai', 'anthropic')")
    display_name: Optional[str] = Field(None, max_length=150, description="Human-readable display name")
    base_url: Optional[str] = Field(None, description="Custom API base URL (optional)")
    enabled: bool = Field(default=True, description="Whether this LLM configuration is enabled")
    api_key_env_var: Optional[str] = Field(None, description="Environment variable name for API key")
    config_json: Dict[str, Any] = Field(default_factory=dict, description="Additional configuration options")


class LLMConfigCreate(LLMConfigBase):
    """Schema for creating a new LLM configuration."""
    
    @validator('model_name')
    def validate_model_name(cls, v):
        """Validate model name format."""
        if not v.strip():
            raise ValueError('Model name cannot be empty')
        # Basic validation - can be extended with specific provider rules
        return v.strip()
    
    @validator('provider')
    def validate_provider(cls, v):
        """Validate provider name."""
        valid_providers = ['openai', 'anthropic', 'google', 'cohere', 'mistral', 'ollama', 'azure', 'huggingface', 'custom']
        if v.lower() not in valid_providers:
            # Allow custom providers but warn
            pass
        return v.lower().strip()
    
    @validator('api_key_env_var')
    def validate_api_key_env_var(cls, v):
        """Validate environment variable name format."""
        if v is None:
            return v
        # Basic validation for environment variable naming
        if not v.isupper() or not all(c.isalnum() or c == '_' for c in v):
            raise ValueError('Environment variable name should be uppercase and contain only letters, numbers, and underscores')
        return v
    
    @validator('config_json')
    def validate_config_json(cls, v):
        """Validate configuration JSON structure."""
        if not isinstance(v, dict):
            raise ValueError('config_json must be a valid dictionary')
        
        # Validate common configuration fields
        allowed_keys = {
            'max_tokens', 'temperature', 'top_p', 'frequency_penalty', 'presence_penalty',
            'supported_roles', 'cost_per_token', 'rate_limit', 'timeout', 'model_version',
            'system_prompt', 'max_context_length', 'streaming', 'tools_enabled'
        }
        
        for key in v.keys():
            if not isinstance(key, str):
                raise ValueError(f'Configuration key must be string, got {type(key)}')
        
        # Validate specific fields if present
        if 'temperature' in v:
            temp = v['temperature']
            if not isinstance(temp, (int, float)) or temp < 0 or temp > 2:
                raise ValueError('temperature must be a number between 0 and 2')
        
        if 'max_tokens' in v:
            max_tokens = v['max_tokens']
            if not isinstance(max_tokens, int) or max_tokens <= 0:
                raise ValueError('max_tokens must be a positive integer')
        
        if 'supported_roles' in v:
            roles = v['supported_roles']
            if not isinstance(roles, list):
                raise ValueError('supported_roles must be a list')
            valid_roles = ['admin', 'user', 'analyst', 'manager']
            for role in roles:
                if role not in valid_roles:
                    # Allow custom roles but don't fail validation
                    pass
        
        return v


class LLMConfigUpdate(BaseModel):
    """Schema for updating an LLM configuration."""
    model_name: Optional[str] = Field(None, min_length=1, max_length=100)
    provider: Optional[str] = Field(None, min_length=1, max_length=50)
    display_name: Optional[str] = Field(None, max_length=150)
    base_url: Optional[str] = None
    enabled: Optional[bool] = None
    api_key_env_var: Optional[str] = None
    config_json: Optional[Dict[str, Any]] = None
    
    @validator('model_name')
    def validate_model_name(cls, v):
        """Validate model name format."""
        if v is not None and not v.strip():
            raise ValueError('Model name cannot be empty')
        return v.strip() if v else v
    
    @validator('provider')
    def validate_provider(cls, v):
        """Validate provider name."""
        if v is not None:
            return v.lower().strip()
        return v
    
    @validator('api_key_env_var')
    def validate_api_key_env_var(cls, v):
        """Validate environment variable name format."""
        if v is not None and v != "":
            if not v.isupper() or not all(c.isalnum() or c == '_' for c in v):
                raise ValueError('Environment variable name should be uppercase and contain only letters, numbers, and underscores')
        return v
    
    @validator('config_json')
    def validate_config_json(cls, v):
        """Validate configuration JSON structure."""
        if v is not None:
            if not isinstance(v, dict):
                raise ValueError('config_json must be a valid dictionary')
            # Apply same validation as in create schema
            if 'temperature' in v:
                temp = v['temperature']
                if not isinstance(temp, (int, float)) or temp < 0 or temp > 2:
                    raise ValueError('temperature must be a number between 0 and 2')
            
            if 'max_tokens' in v:
                max_tokens = v['max_tokens']
                if not isinstance(max_tokens, int) or max_tokens <= 0:
                    raise ValueError('max_tokens must be a positive integer')
        
        return v


class LLMConfigResponse(LLMConfigBase):
    """Schema for LLM configuration response."""
    id: UUID
    created_at: datetime
    updated_at: datetime
    quota_count: int = Field(default=0, description="Number of department quotas using this configuration")
    usage_count: int = Field(default=0, description="Number of usage log entries for this configuration")
    
    class Config:
        from_attributes = True


# JSON Configuration Schemas
class LLMConfigurationJSON(BaseModel):
    """Schema for individual LLM configuration in JSON format."""
    model_name: str = Field(..., description="Model identifier")
    provider: str = Field(..., description="Provider name")
    display_name: Optional[str] = Field(None, description="Human-readable name")
    api_key_env_var: Optional[str] = Field(None, description="Environment variable for API key")
    base_url: Optional[str] = Field(None, description="Custom API endpoint")
    enabled: bool = Field(default=True, description="Whether this configuration is active")
    config: Dict[str, Any] = Field(default_factory=dict, description="Provider-specific configuration")


class LLMConfigurationJSONInput(BaseModel):
    """Schema for JSON input containing multiple LLM configurations."""
    configurations: List[LLMConfigurationJSON] = Field(..., description="List of LLM configurations")
    
    @validator('configurations')
    def validate_configurations(cls, v):
        """Validate configurations list."""
        if not v:
            raise ValueError('At least one configuration must be provided')
        
        # Check for duplicate model names
        model_names = [config.model_name for config in v]
        if len(model_names) != len(set(model_names)):
            raise ValueError('Duplicate model names are not allowed')
        
        return v


# Validation Schemas
class ValidationIssue(BaseModel):
    """Schema for validation issue."""
    level: str = Field(..., description="Issue level: 'error', 'warning', 'info'")
    message: str = Field(..., description="Issue description")
    field: Optional[str] = Field(None, description="Field that caused the issue")
    suggestion: Optional[str] = Field(None, description="Suggested fix")


class ValidationResult(BaseModel):
    """Schema for configuration validation result."""
    is_valid: bool = Field(..., description="Whether the configuration is valid")
    issues: List[ValidationIssue] = Field(default_factory=list, description="List of validation issues")
    suggestions: List[str] = Field(default_factory=list, description="General suggestions for improvement")


class LLMConfigValidationResponse(BaseModel):
    """Schema for LLM configuration validation response."""
    configurations: List[Dict[str, Any]] = Field(..., description="Validated configurations")
    validation_results: List[ValidationResult] = Field(..., description="Validation results for each configuration")
    overall_valid: bool = Field(..., description="Whether all configurations are valid")
    summary: Dict[str, Any] = Field(..., description="Validation summary")


# List Response Schemas
class LLMConfigListResponse(BaseModel):
    """Schema for LLM configuration list response."""
    configurations: List[LLMConfigResponse]
    total: int
    enabled_count: int
    disabled_count: int
    providers: List[str] = Field(default_factory=list, description="List of unique providers")


# Bulk Operations Schemas
class BulkLLMConfigUpdate(BaseModel):
    """Schema for bulk LLM configuration updates."""
    config_ids: List[UUID] = Field(..., description="List of configuration IDs to update")
    updates: LLMConfigUpdate = Field(..., description="Updates to apply")


class BulkLLMConfigResponse(BaseModel):
    """Schema for bulk operation response."""
    success_count: int
    error_count: int
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    updated_configurations: List[LLMConfigResponse] = Field(default_factory=list)


# Provider Information Schemas
class ProviderInfo(BaseModel):
    """Schema for LLM provider information."""
    name: str = Field(..., description="Provider name")
    display_name: str = Field(..., description="Human-readable provider name")
    supported_models: List[str] = Field(default_factory=list, description="List of supported model names")
    default_config: Dict[str, Any] = Field(default_factory=dict, description="Default configuration template")
    required_env_vars: List[str] = Field(default_factory=list, description="Required environment variables")
    documentation_url: Optional[str] = Field(None, description="Provider documentation URL")


class ProvidersResponse(BaseModel):
    """Schema for available providers response."""
    providers: List[ProviderInfo]
    total_providers: int
    total_models: int


# Statistics Schema
class LLMConfigStats(BaseModel):
    """Schema for LLM configuration statistics."""
    total_configurations: int
    enabled_configurations: int
    disabled_configurations: int
    configurations_by_provider: Dict[str, int]
    total_usage_logs: int
    total_quotas: int
    most_used_models: List[Dict[str, Any]]
    recent_configurations: int  # Configurations created in last 30 days
