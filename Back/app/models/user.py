"""
User model for the AI Dock application.
"""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class User(Base):
    """User model for authentication and authorization."""
    
    __tablename__ = "users"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Basic user information
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    
    # Status flags
    is_active = Column(Boolean, default=True, index=True)
    is_superuser = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Foreign Keys
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id"), index=True)
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id"), index=True)
    
    # Relationships
    role = relationship("Role", back_populates="users")
    department = relationship("Department", back_populates="users")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    usage_logs = relationship("UsageLog", back_populates="user")
    
    def __repr__(self):
        """String representation of User object."""
        return f"<User(id={self.id}, username={self.username}, email={self.email})>"
    
    def is_admin(self) -> bool:
        """Check if user has admin role."""
        return self.role and self.role.name == "admin"
    
    def can_access_model(self, model_name: str) -> bool:
        """Check if user can access a specific LLM model."""
        if self.is_superuser:
            return True
            
        if self.role and self.role.permissions:
            # Check if user has wildcard permission or specific model permission
            permissions = self.role.permissions
            return "*" in permissions or f"model:{model_name}" in permissions
            
        return False
    
    def has_permission(self, permission: str) -> bool:
        """Check if user has a specific permission."""
        if self.is_superuser:
            return True
            
        if self.role and self.role.permissions:
            permissions = self.role.permissions
            return "*" in permissions or permission in permissions
            
        return False
    
    @property
    def display_name(self) -> str:
        """Get display name for the user."""
        return self.username
    
    @property
    def is_department_member(self) -> bool:
        """Check if user belongs to a department."""
        return self.department_id is not None
