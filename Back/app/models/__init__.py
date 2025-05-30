"""
SQLAlchemy models for the AI Dock application.
"""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey, Integer, String, Text, 
    DECIMAL, JSON, UniqueConstraint, Index
)
from sqlalchemy.dialects.postgresql import UUID, INET
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base

# Import models from separate files
from .user import User
from .refresh_token import RefreshToken
from .role import Role
from .department import Department


class LLMConfiguration(Base):
    """LLM configuration model."""
    
    __tablename__ = "llm_configurations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_name = Column(String(100), nullable=False)
    provider = Column(String(50), nullable=False)
    api_key_encrypted = Column(Text)
    base_url = Column(Text)
    enabled = Column(Boolean, default=True)
    config_json = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    quotas = relationship("DepartmentQuota", back_populates="llm_config", cascade="all, delete-orphan")
    usage_logs = relationship("UsageLog", back_populates="llm_config")
    
    def __repr__(self):
        return f"<LLMConfiguration(id={self.id}, model_name={self.model_name}, provider={self.provider})>"


class DepartmentQuota(Base):
    """Department quota model."""
    
    __tablename__ = "department_quotas"
    
    __table_args__ = (
        UniqueConstraint('department_id', 'llm_config_id', name='uq_department_llm_quota'),
    )
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id", ondelete="CASCADE"), nullable=False, index=True)
    llm_config_id = Column(UUID(as_uuid=True), ForeignKey("llm_configurations.id", ondelete="CASCADE"), nullable=False, index=True)
    monthly_limit_tokens = Column(Integer, nullable=False, default=0)
    current_usage_tokens = Column(Integer, nullable=False, default=0)
    last_reset = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    department = relationship("Department", back_populates="department_quotas")
    llm_config = relationship("LLMConfiguration", back_populates="quotas")
    
    @hybrid_property
    def usage_percentage(self):
        """Calculate usage percentage."""
        if self.monthly_limit_tokens == 0:
            return 0
        return (self.current_usage_tokens / self.monthly_limit_tokens) * 100
    
    @hybrid_property
    def is_quota_exceeded(self):
        """Check if quota is exceeded."""
        return self.current_usage_tokens >= self.monthly_limit_tokens
    
    def __repr__(self):
        return f"<DepartmentQuota(id={self.id}, department_id={self.department_id}, llm_config_id={self.llm_config_id})>"


class UsageLog(Base):
    """Usage log model for tracking LLM usage."""
    
    __tablename__ = "usage_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id"), nullable=False, index=True)
    llm_config_id = Column(UUID(as_uuid=True), ForeignKey("llm_configurations.id"), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    tokens_prompt = Column(Integer, nullable=False, default=0)
    tokens_completion = Column(Integer, nullable=False, default=0)
    cost_estimated = Column(DECIMAL(10, 4), default=0.0000)
    request_details = Column(JSON, default=dict)
    response_details = Column(JSON, default=dict)
    
    # Relationships
    user = relationship("User", back_populates="usage_logs")
    department = relationship("Department", back_populates="usage_logs")
    llm_config = relationship("LLMConfiguration", back_populates="usage_logs")
    
    @hybrid_property
    def tokens_total(self):
        """Calculate total tokens used."""
        return self.tokens_prompt + self.tokens_completion
    
    def __repr__(self):
        return f"<UsageLog(id={self.id}, user_id={self.user_id}, timestamp={self.timestamp})>"


# Export all models for easy importing
__all__ = [
    "User",
    "RefreshToken", 
    "Role",
    "Department",
    "LLMConfiguration",
    "DepartmentQuota",
    "UsageLog",
]
