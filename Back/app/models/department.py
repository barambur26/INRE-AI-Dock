"""
Department model for the AI Dock application.
"""
import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Column, DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Department(Base):
    """Department model for organizational structure and quota management."""
    
    __tablename__ = "departments"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Basic department information
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    users = relationship("User", back_populates="department")
    department_quotas = relationship("DepartmentQuota", back_populates="department", cascade="all, delete-orphan")
    usage_logs = relationship("UsageLog", back_populates="department")
    
    def __repr__(self):
        """String representation of Department object."""
        return f"<Department(id={self.id}, name={self.name})>"
    
    @property
    def user_count(self) -> int:
        """Get the number of users in this department."""
        return len(self.users) if self.users else 0
    
    @property
    def active_user_count(self) -> int:
        """Get the number of active users in this department."""
        if not self.users:
            return 0
        return len([user for user in self.users if user.is_active])
    
    def get_users_by_role(self, role_name: str) -> List:
        """Get users in this department with a specific role."""
        if not self.users:
            return []
        return [user for user in self.users if user.role and user.role.name == role_name]
    
    def get_admin_users(self) -> List:
        """Get admin users in this department."""
        return self.get_users_by_role("admin")
    
    def get_standard_users(self) -> List:
        """Get standard users in this department."""
        return self.get_users_by_role("user")
    
    def has_active_users(self) -> bool:
        """Check if department has any active users."""
        return self.active_user_count > 0
    
    def get_total_usage_tokens(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> int:
        """Get total token usage for this department within a date range."""
        if not self.usage_logs:
            return 0
        
        logs = self.usage_logs
        
        if start_date:
            logs = [log for log in logs if log.timestamp >= start_date]
        
        if end_date:
            logs = [log for log in logs if log.timestamp <= end_date]
        
        return sum(log.tokens_total for log in logs if log.tokens_total)
    
    def get_quota_for_llm(self, llm_config_id: str):
        """Get quota information for a specific LLM configuration."""
        if not self.department_quotas:
            return None
        
        for quota in self.department_quotas:
            if str(quota.llm_config_id) == str(llm_config_id):
                return quota
        
        return None
    
    def has_quota_for_llm(self, llm_config_id: str) -> bool:
        """Check if department has a quota set for a specific LLM."""
        return self.get_quota_for_llm(llm_config_id) is not None
    
    @property
    def is_default_department(self) -> bool:
        """Check if this is the default department."""
        return self.name.lower() == "general"
    
    @classmethod
    def get_default_departments(cls) -> List[dict]:
        """Get list of default departments to create."""
        return [
            {"name": "General", "description": "Default department for new users"},
            {"name": "IT", "description": "Information Technology Department"},
            {"name": "Finance", "description": "Finance Department"},
            {"name": "HR", "description": "Human Resources Department"},
            {"name": "Marketing", "description": "Marketing Department"},
            {"name": "Operations", "description": "Operations Department"}
        ]
