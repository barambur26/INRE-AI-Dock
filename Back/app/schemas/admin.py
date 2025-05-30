"""
Pydantic schemas for admin operations.
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, EmailStr, validator


# User Schemas
class UserBase(BaseModel):
    """Base user schema with common fields."""
    username: str = Field(..., min_length=3, max_length=50, description="Username must be 3-50 characters")
    email: EmailStr = Field(..., description="Valid email address")
    is_active: bool = Field(default=True, description="Whether the user is active")
    is_superuser: bool = Field(default=False, description="Whether the user has superuser privileges")


class UserCreate(UserBase):
    """Schema for creating a new user."""
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")
    role_id: Optional[UUID] = Field(None, description="Role ID to assign to the user")
    department_id: Optional[UUID] = Field(None, description="Department ID to assign to the user")
    
    @validator('password')
    def validate_password(cls, v):
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v


class UserUpdate(BaseModel):
    """Schema for updating a user."""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None
    role_id: Optional[UUID] = None
    department_id: Optional[UUID] = None
    password: Optional[str] = Field(None, min_length=8, description="New password (optional)")
    
    @validator('password')
    def validate_password(cls, v):
        """Validate password strength if provided."""
        if v is None:
            return v
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v


class UserResponse(UserBase):
    """Schema for user response."""
    id: UUID
    role_id: Optional[UUID] = None
    department_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class UserWithDetails(UserResponse):
    """Schema for user response with role and department details."""
    role_name: Optional[str] = None
    department_name: Optional[str] = None


# Department Schemas
class DepartmentBase(BaseModel):
    """Base department schema."""
    name: str = Field(..., min_length=2, max_length=100, description="Department name must be 2-100 characters")
    description: Optional[str] = Field(None, max_length=500, description="Department description (optional)")


class DepartmentCreate(DepartmentBase):
    """Schema for creating a new department."""
    pass


class DepartmentUpdate(BaseModel):
    """Schema for updating a department."""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = Field(None, max_length=500)


class DepartmentResponse(DepartmentBase):
    """Schema for department response."""
    id: UUID
    created_at: datetime
    updated_at: datetime
    user_count: int = Field(default=0, description="Number of users in this department")
    active_user_count: int = Field(default=0, description="Number of active users in this department")
    
    class Config:
        from_attributes = True


# Role Schemas
class RoleBase(BaseModel):
    """Base role schema."""
    name: str = Field(..., min_length=2, max_length=50, description="Role name must be 2-50 characters")
    description: Optional[str] = Field(None, max_length=500, description="Role description (optional)")
    permissions: List[str] = Field(default_factory=list, description="List of permissions for this role")


class RoleCreate(RoleBase):
    """Schema for creating a new role."""
    pass


class RoleUpdate(BaseModel):
    """Schema for updating a role."""
    name: Optional[str] = Field(None, min_length=2, max_length=50)
    description: Optional[str] = Field(None, max_length=500)
    permissions: Optional[List[str]] = None


class RoleResponse(RoleBase):
    """Schema for role response."""
    id: UUID
    created_at: datetime
    updated_at: datetime
    user_count: int = Field(default=0, description="Number of users with this role")
    is_admin_role: bool = Field(default=False, description="Whether this is an admin role")
    
    class Config:
        from_attributes = True


# List Response Schemas
class UserListResponse(BaseModel):
    """Schema for paginated user list response."""
    users: List[UserWithDetails]
    total: int
    page: int
    page_size: int
    total_pages: int


class DepartmentListResponse(BaseModel):
    """Schema for department list response."""
    departments: List[DepartmentResponse]
    total: int


class RoleListResponse(BaseModel):
    """Schema for role list response."""
    roles: List[RoleResponse]
    total: int


# Admin Statistics Schema
class AdminStatsResponse(BaseModel):
    """Schema for admin dashboard statistics."""
    total_users: int
    active_users: int
    total_departments: int
    total_roles: int
    users_by_role: dict
    users_by_department: dict
    recent_users_count: int  # Users created in last 30 days


# Bulk Operations Schemas
class BulkUserUpdate(BaseModel):
    """Schema for bulk user updates."""
    user_ids: List[UUID]
    updates: UserUpdate


class BulkUserResponse(BaseModel):
    """Schema for bulk operation response."""
    success_count: int
    error_count: int
    errors: List[dict] = Field(default_factory=list)


# Permission Management Schemas
class PermissionInfo(BaseModel):
    """Schema for permission information."""
    name: str
    description: str
    category: str


class AvailablePermissionsResponse(BaseModel):
    """Schema for available permissions response."""
    permissions: List[PermissionInfo]
    categories: List[str]
