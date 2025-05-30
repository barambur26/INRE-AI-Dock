"""
LLM Configuration service layer for managing LLM configurations.
"""
import uuid
import json
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc

from app.models import LLMConfiguration, DepartmentQuota, UsageLog, Department, Role
from app.schemas.llm_config import (
    LLMConfigCreate, LLMConfigUpdate, LLMConfigurationJSONInput, 
    ValidationResult, ValidationIssue, LLMConfigStats, ProviderInfo
)


class LLMConfigService:
    """Service class for LLM configuration operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    # Basic CRUD Operations
    async def get_configurations(
        self, 
        skip: int = 0, 
        limit: int = 100,
        enabled_only: Optional[bool] = None,
        provider: Optional[str] = None,
        search: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get paginated list of LLM configurations with filters."""
        query = self.db.query(LLMConfiguration)
        
        # Apply filters
        if enabled_only is not None:
            query = query.filter(LLMConfiguration.enabled == enabled_only)
        
        if provider:
            query = query.filter(LLMConfiguration.provider.ilike(f"%{provider}%"))
        
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                LLMConfiguration.model_name.ilike(search_term) |
                LLMConfiguration.provider.ilike(search_term) |
                LLMConfiguration.base_url.ilike(search_term)
            )
        
        # Get total count
        total = query.count()
        
        # Apply pagination and ordering
        configurations = query.order_by(desc(LLMConfiguration.created_at)).offset(skip).limit(limit).all()
        
        # Get counts
        enabled_count = self.db.query(LLMConfiguration).filter(LLMConfiguration.enabled == True).count()
        disabled_count = total - enabled_count
        
        # Get unique providers
        providers = [p[0] for p in self.db.query(LLMConfiguration.provider.distinct()).all()]
        
        # Format configurations with additional info
        configs_with_details = []
        for config in configurations:
            # Get quota count
            quota_count = self.db.query(DepartmentQuota).filter(DepartmentQuota.llm_config_id == config.id).count()
            # Get usage count
            usage_count = self.db.query(UsageLog).filter(UsageLog.llm_config_id == config.id).count()
            
            config_dict = {
                'id': config.id,
                'model_name': config.model_name,
                'provider': config.provider,
                'api_key_encrypted': config.api_key_encrypted,
                'base_url': config.base_url,
                'enabled': config.enabled,
                'config_json': config.config_json,
                'created_at': config.created_at,
                'updated_at': config.updated_at,
                'quota_count': quota_count,
                'usage_count': usage_count
            }
            configs_with_details.append(config_dict)
        
        return {
            'configurations': configs_with_details,
            'total': total,
            'enabled_count': enabled_count,
            'disabled_count': disabled_count,
            'providers': providers
        }
    
    async def get_configuration_by_id(self, config_id: uuid.UUID) -> Optional[LLMConfiguration]:
        """Get LLM configuration by ID."""
        return self.db.query(LLMConfiguration).filter(LLMConfiguration.id == config_id).first()
    
    async def get_configuration_by_model_name(self, model_name: str) -> Optional[LLMConfiguration]:
        """Get LLM configuration by model name."""
        return self.db.query(LLMConfiguration).filter(LLMConfiguration.model_name == model_name).first()
    
    async def create_configuration(self, config_data: LLMConfigCreate) -> LLMConfiguration:
        """Create a new LLM configuration."""
        # Check if model name already exists
        existing_config = await self.get_configuration_by_model_name(config_data.model_name)
        if existing_config:
            raise ValueError(f"Model name '{config_data.model_name}' already exists")
        
        # Create configuration
        db_config = LLMConfiguration(
            model_name=config_data.model_name,
            provider=config_data.provider,
            api_key_encrypted=None,  # Will be handled separately for security
            base_url=config_data.base_url,
            enabled=config_data.enabled,
            config_json=config_data.config_json
        )
        
        self.db.add(db_config)
        self.db.commit()
        self.db.refresh(db_config)
        
        return db_config
    
    async def update_configuration(self, config_id: uuid.UUID, config_data: LLMConfigUpdate) -> Optional[LLMConfiguration]:
        """Update an existing LLM configuration."""
        db_config = await self.get_configuration_by_id(config_id)
        if not db_config:
            return None
        
        # Check for model name conflicts
        if config_data.model_name and config_data.model_name != db_config.model_name:
            existing_config = await self.get_configuration_by_model_name(config_data.model_name)
            if existing_config:
                raise ValueError(f"Model name '{config_data.model_name}' already exists")
        
        # Update fields
        update_data = config_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_config, field, value)
        
        db_config.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(db_config)
        
        return db_config
    
    async def delete_configuration(self, config_id: uuid.UUID) -> bool:
        """Delete an LLM configuration."""
        db_config = await self.get_configuration_by_id(config_id)
        if not db_config:
            return False
        
        # Check if configuration has associated quotas
        quota_count = self.db.query(DepartmentQuota).filter(DepartmentQuota.llm_config_id == config_id).count()
        if quota_count > 0:
            raise ValueError(f"Cannot delete configuration '{db_config.model_name}' because it has {quota_count} department quotas")
        
        # Check if configuration has usage logs
        usage_count = self.db.query(UsageLog).filter(UsageLog.llm_config_id == config_id).count()
        if usage_count > 0:
            raise ValueError(f"Cannot delete configuration '{db_config.model_name}' because it has {usage_count} usage logs")
        
        self.db.delete(db_config)
        self.db.commit()
        
        return True
    
    async def toggle_configuration_status(self, config_id: uuid.UUID, enabled: bool) -> Optional[LLMConfiguration]:
        """Enable or disable an LLM configuration."""
        db_config = await self.get_configuration_by_id(config_id)
        if not db_config:
            return None
        
        db_config.enabled = enabled
        db_config.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(db_config)
        
        return db_config
    
    # JSON Configuration Management
    async def validate_json_configuration(self, json_input: LLMConfigurationJSONInput) -> Dict[str, Any]:
        """Validate LLM configuration JSON input."""
        validation_results = []
        overall_valid = True
        configurations = []
        
        for i, config in enumerate(json_input.configurations):
            issues = []
            suggestions = []
            is_valid = True
            
            # Validate model name uniqueness
            existing_config = await self.get_configuration_by_model_name(config.model_name)
            if existing_config:
                issues.append(ValidationIssue(
                    level="error",
                    message=f"Model name '{config.model_name}' already exists",
                    field="model_name",
                    suggestion=f"Use a unique model name like '{config.model_name}_v2'"
                ))
                is_valid = False
            
            # Validate provider
            known_providers = self._get_known_providers()
            if config.provider.lower() not in [p.lower() for p in known_providers]:
                issues.append(ValidationIssue(
                    level="warning",
                    message=f"Provider '{config.provider}' is not in the list of known providers",
                    field="provider",
                    suggestion=f"Consider using one of: {', '.join(known_providers[:5])}"
                ))
            
            # Validate API key environment variable
            if config.api_key_env_var:
                if not config.api_key_env_var.isupper():
                    issues.append(ValidationIssue(
                        level="warning",
                        message="API key environment variable should be uppercase",
                        field="api_key_env_var",
                        suggestion=f"Use '{config.api_key_env_var.upper()}' instead"
                    ))
                
                # Check for common naming patterns
                if not any(pattern in config.api_key_env_var.upper() for pattern in ['KEY', 'TOKEN', 'SECRET']):
                    suggestions.append(f"Consider including 'KEY' in the environment variable name for clarity")
            
            # Validate configuration fields
            if 'temperature' in config.config:
                temp = config.config['temperature']
                if not isinstance(temp, (int, float)) or temp < 0 or temp > 2:
                    issues.append(ValidationIssue(
                        level="error",
                        message="Temperature must be between 0 and 2",
                        field="config.temperature"
                    ))
                    is_valid = False
            
            if 'max_tokens' in config.config:
                max_tokens = config.config['max_tokens']
                if not isinstance(max_tokens, int) or max_tokens <= 0:
                    issues.append(ValidationIssue(
                        level="error",
                        message="max_tokens must be a positive integer",
                        field="config.max_tokens"
                    ))
                    is_valid = False
            
            # Provider-specific validations
            if config.provider.lower() == 'openai':
                if not config.base_url or 'openai.com' not in config.base_url:
                    issues.append(ValidationIssue(
                        level="warning",
                        message="OpenAI configurations typically use 'https://api.openai.com/v1' as base URL",
                        field="base_url",
                        suggestion="Set base_url to 'https://api.openai.com/v1'"
                    ))
            
            elif config.provider.lower() == 'anthropic':
                if not config.base_url or 'anthropic.com' not in config.base_url:
                    issues.append(ValidationIssue(
                        level="warning",
                        message="Anthropic configurations typically use 'https://api.anthropic.com' as base URL",
                        field="base_url",
                        suggestion="Set base_url to 'https://api.anthropic.com'"
                    ))
            
            # Add general suggestions
            if not config.display_name:
                suggestions.append("Consider adding a display_name for better user experience")
            
            if not config.config:
                suggestions.append("Consider adding configuration parameters like max_tokens, temperature, etc.")
            
            # Create validation result
            validation_result = ValidationResult(
                is_valid=is_valid,
                issues=issues,
                suggestions=suggestions
            )
            validation_results.append(validation_result)
            
            if not is_valid:
                overall_valid = False
            
            # Add configuration to results
            configurations.append(config.dict())
        
        return {
            'configurations': configurations,
            'validation_results': validation_results,
            'overall_valid': overall_valid,
            'summary': {
                'total_configurations': len(json_input.configurations),
                'valid_configurations': sum(1 for r in validation_results if r.is_valid),
                'configurations_with_warnings': sum(1 for r in validation_results if any(i.level == 'warning' for i in r.issues)),
                'configurations_with_errors': sum(1 for r in validation_results if any(i.level == 'error' for i in r.issues))
            }
        }
    
    async def create_configurations_from_json(self, json_input: LLMConfigurationJSONInput) -> Dict[str, Any]:
        """Create LLM configurations from JSON input."""
        # First validate the input
        validation_result = await self.validate_json_configuration(json_input)
        
        if not validation_result['overall_valid']:
            raise ValueError("Configuration validation failed. Please fix the errors before proceeding.")
        
        created_configs = []
        errors = []
        
        for config_data in json_input.configurations:
            try:
                # Create LLMConfigCreate schema
                create_data = LLMConfigCreate(
                    model_name=config_data.model_name,
                    provider=config_data.provider,
                    display_name=config_data.display_name,
                    base_url=config_data.base_url,
                    enabled=config_data.enabled,
                    api_key_env_var=config_data.api_key_env_var,
                    config_json=config_data.config
                )
                
                # Create configuration
                db_config = await self.create_configuration(create_data)
                created_configs.append(db_config)
                
            except Exception as e:
                errors.append({
                    'model_name': config_data.model_name,
                    'error': str(e)
                })
        
        return {
            'success_count': len(created_configs),
            'error_count': len(errors),
            'errors': errors,
            'created_configurations': created_configs
        }
    
    # Bulk Operations
    async def bulk_update_configurations(self, config_ids: List[uuid.UUID], updates: LLMConfigUpdate) -> Dict[str, Any]:
        """Bulk update multiple LLM configurations."""
        updated_configs = []
        errors = []
        
        for config_id in config_ids:
            try:
                updated_config = await self.update_configuration(config_id, updates)
                if updated_config:
                    updated_configs.append(updated_config)
                else:
                    errors.append({
                        'config_id': str(config_id),
                        'error': 'Configuration not found'
                    })
            except Exception as e:
                errors.append({
                    'config_id': str(config_id),
                    'error': str(e)
                })
        
        return {
            'success_count': len(updated_configs),
            'error_count': len(errors),
            'errors': errors,
            'updated_configurations': updated_configs
        }
    
    async def bulk_toggle_configurations(self, config_ids: List[uuid.UUID], enabled: bool) -> Dict[str, Any]:
        """Bulk enable/disable multiple LLM configurations."""
        updated_configs = []
        errors = []
        
        for config_id in config_ids:
            try:
                updated_config = await self.toggle_configuration_status(config_id, enabled)
                if updated_config:
                    updated_configs.append(updated_config)
                else:
                    errors.append({
                        'config_id': str(config_id),
                        'error': 'Configuration not found'
                    })
            except Exception as e:
                errors.append({
                    'config_id': str(config_id),
                    'error': str(e)
                })
        
        return {
            'success_count': len(updated_configs),
            'error_count': len(errors),
            'errors': errors,
            'updated_configurations': updated_configs
        }
    
    # Statistics and Analytics
    async def get_configuration_stats(self) -> LLMConfigStats:
        """Get LLM configuration statistics."""
        total_configurations = self.db.query(LLMConfiguration).count()
        enabled_configurations = self.db.query(LLMConfiguration).filter(LLMConfiguration.enabled == True).count()
        disabled_configurations = total_configurations - enabled_configurations
        
        # Configurations by provider
        configurations_by_provider = {}
        providers = self.db.query(LLMConfiguration.provider, func.count(LLMConfiguration.id)).group_by(LLMConfiguration.provider).all()
        for provider, count in providers:
            configurations_by_provider[provider] = count
        
        # Total usage logs and quotas
        total_usage_logs = self.db.query(UsageLog).count()
        total_quotas = self.db.query(DepartmentQuota).count()
        
        # Most used models (based on usage logs)
        most_used_models = []
        usage_by_model = (
            self.db.query(
                LLMConfiguration.model_name,
                LLMConfiguration.provider,
                func.count(UsageLog.id).label('usage_count')
            )
            .join(UsageLog, LLMConfiguration.id == UsageLog.llm_config_id)
            .group_by(LLMConfiguration.id, LLMConfiguration.model_name, LLMConfiguration.provider)
            .order_by(desc('usage_count'))
            .limit(10)
            .all()
        )
        
        for model_name, provider, usage_count in usage_by_model:
            most_used_models.append({
                'model_name': model_name,
                'provider': provider,
                'usage_count': usage_count
            })
        
        # Recent configurations (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_configurations = self.db.query(LLMConfiguration).filter(LLMConfiguration.created_at >= thirty_days_ago).count()
        
        return LLMConfigStats(
            total_configurations=total_configurations,
            enabled_configurations=enabled_configurations,
            disabled_configurations=disabled_configurations,
            configurations_by_provider=configurations_by_provider,
            total_usage_logs=total_usage_logs,
            total_quotas=total_quotas,
            most_used_models=most_used_models,
            recent_configurations=recent_configurations
        )
    
    # Provider Information
    def get_available_providers(self) -> List[ProviderInfo]:
        """Get information about available LLM providers."""
        providers = [
            ProviderInfo(
                name="openai",
                display_name="OpenAI",
                supported_models=["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo", "gpt-3.5-turbo-16k"],
                default_config={
                    "max_tokens": 2000,
                    "temperature": 0.7,
                    "top_p": 1.0,
                    "frequency_penalty": 0,
                    "presence_penalty": 0
                },
                required_env_vars=["OPENAI_API_KEY"],
                documentation_url="https://platform.openai.com/docs"
            ),
            ProviderInfo(
                name="anthropic",
                display_name="Anthropic",
                supported_models=["claude-3-opus", "claude-3-sonnet", "claude-3-haiku", "claude-2.1"],
                default_config={
                    "max_tokens": 2000,
                    "temperature": 0.7
                },
                required_env_vars=["ANTHROPIC_API_KEY"],
                documentation_url="https://docs.anthropic.com"
            ),
            ProviderInfo(
                name="google",
                display_name="Google AI",
                supported_models=["gemini-pro", "gemini-pro-vision", "text-bison", "chat-bison"],
                default_config={
                    "max_tokens": 2000,
                    "temperature": 0.7,
                    "top_p": 0.95,
                    "top_k": 40
                },
                required_env_vars=["GOOGLE_API_KEY"],
                documentation_url="https://ai.google.dev/docs"
            ),
            ProviderInfo(
                name="cohere",
                display_name="Cohere",
                supported_models=["command", "command-light", "command-nightly"],
                default_config={
                    "max_tokens": 2000,
                    "temperature": 0.7,
                    "p": 0.9,
                    "k": 0
                },
                required_env_vars=["COHERE_API_KEY"],
                documentation_url="https://docs.cohere.ai"
            ),
            ProviderInfo(
                name="mistral",
                display_name="Mistral AI",
                supported_models=["mistral-large", "mistral-medium", "mistral-small", "mixtral-8x7b"],
                default_config={
                    "max_tokens": 2000,
                    "temperature": 0.7,
                    "top_p": 1.0
                },
                required_env_vars=["MISTRAL_API_KEY"],
                documentation_url="https://docs.mistral.ai"
            ),
            ProviderInfo(
                name="ollama",
                display_name="Ollama (Local)",
                supported_models=["llama2", "codellama", "mistral", "neural-chat"],
                default_config={
                    "temperature": 0.7,
                    "num_predict": 2000
                },
                required_env_vars=[],
                documentation_url="https://ollama.ai/docs"
            )
        ]
        
        return providers
    
    # Helper Methods
    def _get_known_providers(self) -> List[str]:
        """Get list of known provider names."""
        return ["openai", "anthropic", "google", "cohere", "mistral", "ollama", "azure", "huggingface"]
    
    async def get_enabled_configurations(self) -> List[LLMConfiguration]:
        """Get all enabled LLM configurations."""
        return self.db.query(LLMConfiguration).filter(LLMConfiguration.enabled == True).all()
    
    async def get_configurations_by_provider(self, provider: str) -> List[LLMConfiguration]:
        """Get all configurations for a specific provider."""
        return self.db.query(LLMConfiguration).filter(LLMConfiguration.provider.ilike(f"%{provider}%")).all()
    
    async def get_configuration_usage_summary(self, config_id: uuid.UUID) -> Dict[str, Any]:
        """Get usage summary for a specific configuration."""
        config = await self.get_configuration_by_id(config_id)
        if not config:
            return None
        
        # Get usage statistics
        total_usage = self.db.query(func.sum(UsageLog.tokens_total)).filter(UsageLog.llm_config_id == config_id).scalar() or 0
        usage_count = self.db.query(UsageLog).filter(UsageLog.llm_config_id == config_id).count()
        
        # Get department quotas
        quotas = self.db.query(DepartmentQuota).filter(DepartmentQuota.llm_config_id == config_id).all()
        
        # Get recent usage (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_usage = (
            self.db.query(func.sum(UsageLog.tokens_total))
            .filter(UsageLog.llm_config_id == config_id)
            .filter(UsageLog.timestamp >= thirty_days_ago)
            .scalar() or 0
        )
        
        return {
            'configuration': config,
            'total_tokens_used': total_usage,
            'total_requests': usage_count,
            'recent_tokens_used': recent_usage,
            'department_quotas': len(quotas),
            'active_quotas': len([q for q in quotas if not q.is_quota_exceeded])
        }
