"""
Chat-related Pydantic schemas for request/response validation.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """Individual chat message schema."""
    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Message timestamp")


class ChatSendRequest(BaseModel):
    """Request schema for sending a chat message."""
    message: str = Field(..., min_length=1, max_length=10000, description="User message to send to LLM")
    model_id: Optional[UUID] = Field(None, description="Optional specific LLM model ID (defaults to first available)")
    conversation_id: Optional[UUID] = Field(None, description="Optional conversation ID for multi-turn chats")


class ChatSendResponse(BaseModel):
    """Response schema for chat message."""
    response: str = Field(..., description="LLM response message")
    model_used: str = Field(..., description="Name of the LLM model that generated the response")
    model_id: UUID = Field(..., description="ID of the LLM configuration used")
    provider: str = Field(..., description="LLM provider (e.g., 'openai', 'claude')")
    tokens_prompt: int = Field(..., description="Number of tokens in the prompt")
    tokens_completion: int = Field(..., description="Number of tokens in the completion")
    tokens_total: int = Field(..., description="Total tokens used")
    cost_estimated: float = Field(..., description="Estimated cost of the request")
    conversation_id: Optional[UUID] = Field(None, description="Conversation ID if part of a multi-turn chat")
    usage_log_id: UUID = Field(..., description="ID of the usage log entry")


class AvailableModelsResponse(BaseModel):
    """Response schema for available LLM models."""
    models: List[Dict[str, Any]] = Field(..., description="List of available LLM models")
    default_model: Optional[Dict[str, Any]] = Field(None, description="Default model information")
    total_count: int = Field(..., description="Total number of available models")


class ModelInfo(BaseModel):
    """Individual model information schema."""
    id: UUID = Field(..., description="Model configuration ID")
    model_name: str = Field(..., description="Model name")
    provider: str = Field(..., description="Provider name")
    enabled: bool = Field(..., description="Whether the model is enabled")
    description: Optional[str] = Field(None, description="Model description")
    capabilities: Optional[Dict[str, Any]] = Field(None, description="Model capabilities")


class ChatErrorResponse(BaseModel):
    """Error response schema for chat operations."""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    suggestions: Optional[List[str]] = Field(None, description="Suggested actions to resolve the error")


class ChatStatsResponse(BaseModel):
    """Response schema for chat statistics."""
    total_conversations: int = Field(..., description="Total number of conversations")
    total_messages: int = Field(..., description="Total number of messages sent")
    total_tokens_used: int = Field(..., description="Total tokens consumed")
    total_cost: float = Field(..., description="Total estimated cost")
    most_used_model: Optional[str] = Field(None, description="Most frequently used model")
    avg_tokens_per_message: float = Field(..., description="Average tokens per message")


class UsageQuotaInfo(BaseModel):
    """Schema for usage quota information."""
    department_name: str = Field(..., description="Department name")
    monthly_limit: int = Field(..., description="Monthly token limit")
    current_usage: int = Field(..., description="Current month usage")
    usage_percentage: float = Field(..., description="Usage percentage (0-100)")
    quota_exceeded: bool = Field(..., description="Whether quota is exceeded")
    remaining_tokens: int = Field(..., description="Remaining tokens this month")


class ChatHealthResponse(BaseModel):
    """Response schema for chat service health check."""
    status: str = Field(..., description="Service status")
    available_models: int = Field(..., description="Number of available models")
    enabled_models: int = Field(..., description="Number of enabled models")
    default_model: Optional[str] = Field(None, description="Default model name")
    quota_status: str = Field(..., description="Quota enforcement status")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Health check timestamp")
