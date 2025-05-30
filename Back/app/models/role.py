"""
Role model for the AI Dock application.
"""
import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Column, DateTime, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Role(Base):
    """Role model for user permissions and access control."""
    
    __tablename__ = "roles"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Basic role information
    name = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Permissions stored as JSON array
    permissions = Column(JSONB, default=list, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    users = relationship("User", back_populates="role")
    
    def __repr__(self):
        """String representation of Role object."""
        return f"<Role(id={self.id}, name={self.name})>"
    
    def has_permission(self, permission: str) -> bool:
        """Check if role has a specific permission."""
        if not self.permissions:
            return False
        
        # Check for wildcard permission
        if "*" in self.permissions:
            return True
            
        # Check for exact permission match
        return permission in self.permissions
    
    def add_permission(self, permission: str) -> None:
        """Add a permission to the role."""
        if not self.permissions:
            self.permissions = []
        
        if permission not in self.permissions:
            # Create a new list to trigger SQLAlchemy change detection
            self.permissions = list(self.permissions) + [permission]
    
    def remove_permission(self, permission: str) -> None:
        """Remove a permission from the role."""
        if self.permissions and permission in self.permissions:
            # Create a new list to trigger SQLAlchemy change detection
            self.permissions = [p for p in self.permissions if p != permission]
    
    def get_permissions(self) -> List[str]:
        """Get all permissions for this role."""
        return list(self.permissions) if self.permissions else []
    
    def set_permissions(self, permissions: List[str]) -> None:
        """Set permissions for this role."""
        self.permissions = list(permissions) if permissions else []
    
    @property
    def is_admin_role(self) -> bool:
        """Check if this is an admin role."""
        return self.name == "admin" or "*" in (self.permissions or [])
    
    @property
    def user_count(self) -> int:
        """Get the number of users with this role."""
        return len(self.users) if self.users else 0
    
    @classmethod
    def get_default_permissions(cls, role_name: str) -> List[str]:
        """Get default permissions for common role types."""
        default_permissions = {
            "admin": ["*"],
            "user": ["chat", "view_profile", "view_usage"],
            "analyst": ["chat", "view_profile", "view_usage", "view_reports"],
            "manager": ["chat", "view_profile", "view_usage", "view_reports", "manage_department_users"]
        }
        return default_permissions.get(role_name.lower(), ["chat", "view_profile"])
