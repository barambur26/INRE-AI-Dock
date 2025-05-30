"""
Admin API endpoints for LLM configuration management.
"""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import User
from app.schemas.llm_config import (
    LLMConfigCreate, LLMConfigUpdate, LLMConfigResponse, 
    LLMConfigListResponse, LLMConfigurationJSONInput, LLMConfigValidationResponse,
    BulkLLMConfigUpdate, BulkLLMConfigResponse, LLMConfigStats, ProvidersResponse
)
from app.services.llm_config_service import LLMConfigService
from app.utils.admin_auth import get_current_admin_user


router = APIRouter(prefix="/llm-configurations", tags=["Admin - LLM Configurations"])


@router.get("/", response_model=LLMConfigListResponse)
async def list_configurations(
    skip: int = Query(0, ge=0, description="Number of configurations to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of configurations to return"),
    enabled_only: Optional[bool] = Query(None, description="Filter by enabled status"),
    provider: Optional[str] = Query(None, description="Filter by provider"),
    search: Optional[str] = Query(None, description="Search by model name, provider, or base URL"),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get paginated list of LLM configurations with optional filters.
    
    **Requires:** Admin privileges
    """
    llm_service = LLMConfigService(db)
    
    try:
        result = await llm_service.get_configurations(
            skip=skip,
            limit=limit,
            enabled_only=enabled_only,
            provider=provider,
            search=search
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve LLM configurations: {str(e)}"
        )


@router.get("/{config_id}", response_model=LLMConfigResponse)
async def get_configuration(
    config_id: UUID,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific LLM configuration by ID.
    
    **Requires:** Admin privileges
    """
    llm_service = LLMConfigService(db)
    
    config = await llm_service.get_configuration_by_id(config_id)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"LLM configuration with ID {config_id} not found"
        )
    
    # Get additional stats
    quota_count = db.query(db.query(config).first().quotas).count() if hasattr(config, 'quotas') else 0
    usage_count = db.query(db.query(config).first().usage_logs).count() if hasattr(config, 'usage_logs') else 0
    
    return {
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


@router.post("/", response_model=LLMConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_configuration(
    config_data: LLMConfigCreate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Create a new LLM configuration.
    
    **Requires:** Admin privileges
    """
    llm_service = LLMConfigService(db)
    
    try:
        config = await llm_service.create_configuration(config_data)
        return config
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create LLM configuration: {str(e)}"
        )


@router.put("/{config_id}", response_model=LLMConfigResponse)
async def update_configuration(
    config_id: UUID,
    config_data: LLMConfigUpdate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Update an existing LLM configuration.
    
    **Requires:** Admin privileges
    """
    llm_service = LLMConfigService(db)
    
    try:
        config = await llm_service.update_configuration(config_id, config_data)
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"LLM configuration with ID {config_id} not found"
            )
        return config
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update LLM configuration: {str(e)}"
        )


@router.delete("/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_configuration(
    config_id: UUID,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Delete an LLM configuration.
    
    **Requires:** Admin privileges
    
    **Note:** Cannot delete configurations that have associated quotas or usage logs.
    """
    llm_service = LLMConfigService(db)
    
    try:
        success = await llm_service.delete_configuration(config_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"LLM configuration with ID {config_id} not found"
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete LLM configuration: {str(e)}"
        )


@router.post("/{config_id}/enable", response_model=LLMConfigResponse)
async def enable_configuration(
    config_id: UUID,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Enable an LLM configuration.
    
    **Requires:** Admin privileges
    """
    llm_service = LLMConfigService(db)
    
    try:
        config = await llm_service.toggle_configuration_status(config_id, enabled=True)
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"LLM configuration with ID {config_id} not found"
            )
        return config
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to enable LLM configuration: {str(e)}"
        )


@router.post("/{config_id}/disable", response_model=LLMConfigResponse)
async def disable_configuration(
    config_id: UUID,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Disable an LLM configuration.
    
    **Requires:** Admin privileges
    """
    llm_service = LLMConfigService(db)
    
    try:
        config = await llm_service.toggle_configuration_status(config_id, enabled=False)
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"LLM configuration with ID {config_id} not found"
            )
        return config
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to disable LLM configuration: {str(e)}"
        )


@router.post("/validate-json", response_model=LLMConfigValidationResponse)
async def validate_json_configuration(
    json_input: LLMConfigurationJSONInput,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Validate LLM configuration JSON input without creating configurations.
    
    **Requires:** Admin privileges
    
    **Features:**
    - Validates JSON structure and required fields
    - Checks for duplicate model names
    - Validates provider-specific settings
    - Provides suggestions for improvements
    - Returns detailed validation results
    """
    llm_service = LLMConfigService(db)
    
    try:
        validation_result = await llm_service.validate_json_configuration(json_input)
        return validation_result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate JSON configuration: {str(e)}"
        )


@router.post("/import-json", response_model=BulkLLMConfigResponse)
async def import_json_configurations(
    json_input: LLMConfigurationJSONInput,
    validate_only: bool = Query(False, description="Only validate without creating configurations"),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Import LLM configurations from JSON input.
    
    **Requires:** Admin privileges
    
    **Features:**
    - Validates JSON before import
    - Creates multiple configurations in batch
    - Returns detailed results with success/error counts
    - Supports validate-only mode for testing
    """
    llm_service = LLMConfigService(db)
    
    try:
        if validate_only:
            # Only validate, don't create
            validation_result = await llm_service.validate_json_configuration(json_input)
            return {
                'success_count': 0,
                'error_count': 0,
                'errors': [],
                'updated_configurations': [],
                'validation_result': validation_result
            }
        else:
            # Validate and create
            result = await llm_service.create_configurations_from_json(json_input)
            return result
            
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to import JSON configurations: {str(e)}"
        )


@router.post("/bulk-update", response_model=BulkLLMConfigResponse)
async def bulk_update_configurations(
    bulk_data: BulkLLMConfigUpdate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Bulk update multiple LLM configurations.
    
    **Requires:** Admin privileges
    """
    llm_service = LLMConfigService(db)
    
    try:
        result = await llm_service.bulk_update_configurations(bulk_data.config_ids, bulk_data.updates)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to bulk update configurations: {str(e)}"
        )


@router.post("/bulk-enable")
async def bulk_enable_configurations(
    config_ids: List[UUID] = Body(..., description="List of configuration IDs to enable"),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Bulk enable multiple LLM configurations.
    
    **Requires:** Admin privileges
    """
    llm_service = LLMConfigService(db)
    
    try:
        result = await llm_service.bulk_toggle_configurations(config_ids, enabled=True)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to bulk enable configurations: {str(e)}"
        )


@router.post("/bulk-disable")
async def bulk_disable_configurations(
    config_ids: List[UUID] = Body(..., description="List of configuration IDs to disable"),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Bulk disable multiple LLM configurations.
    
    **Requires:** Admin privileges
    """
    llm_service = LLMConfigService(db)
    
    try:
        result = await llm_service.bulk_toggle_configurations(config_ids, enabled=False)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to bulk disable configurations: {str(e)}"
        )


@router.get("/stats/overview", response_model=LLMConfigStats)
async def get_configuration_stats(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get LLM configuration statistics and analytics.
    
    **Requires:** Admin privileges
    
    **Returns:**
    - Total configurations count
    - Enabled/disabled breakdown
    - Configurations by provider
    - Usage statistics
    - Most used models
    - Recent configurations count
    """
    llm_service = LLMConfigService(db)
    
    try:
        stats = await llm_service.get_configuration_stats()
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get configuration statistics: {str(e)}"
        )


@router.get("/providers", response_model=ProvidersResponse)
async def get_available_providers(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get information about available LLM providers.
    
    **Requires:** Admin privileges
    
    **Returns:**
    - Supported providers list
    - Default configurations for each provider
    - Required environment variables
    - Supported models
    - Documentation links
    """
    llm_service = LLMConfigService(db)
    
    try:
        providers = llm_service.get_available_providers()
        
        total_providers = len(providers)
        total_models = sum(len(p.supported_models) for p in providers)
        
        return ProvidersResponse(
            providers=providers,
            total_providers=total_providers,
            total_models=total_models
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get provider information: {str(e)}"
        )


@router.get("/{config_id}/usage-summary")
async def get_configuration_usage_summary(
    config_id: UUID,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get usage summary for a specific LLM configuration.
    
    **Requires:** Admin privileges
    
    **Returns:**
    - Total tokens used
    - Total requests count  
    - Recent usage (last 30 days)
    - Department quotas count
    - Active quotas status
    """
    llm_service = LLMConfigService(db)
    
    try:
        summary = await llm_service.get_configuration_usage_summary(config_id)
        if not summary:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"LLM configuration with ID {config_id} not found"
            )
        
        return summary
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get configuration usage summary: {str(e)}"
        )


@router.get("/models/enabled")
async def get_enabled_configurations(
    provider: Optional[str] = Query(None, description="Filter by provider"),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get all enabled LLM configurations.
    
    **Requires:** Admin privileges
    
    **Returns:** List of enabled configurations, optionally filtered by provider
    """
    llm_service = LLMConfigService(db)
    
    try:
        if provider:
            configs = await llm_service.get_configurations_by_provider(provider)
            configs = [c for c in configs if c.enabled]
        else:
            configs = await llm_service.get_enabled_configurations()
        
        return {
            'configurations': configs,
            'total': len(configs),
            'provider_filter': provider
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get enabled configurations: {str(e)}"
        )
