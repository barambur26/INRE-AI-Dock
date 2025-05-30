"""
Admin service layer for user and department management.
"""
import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc

from app.models import User, Role, Department, RefreshToken
from app.core.security import hash_password, verify_password
from app.schemas.admin import (
    UserCreate, UserUpdate, DepartmentCreate, DepartmentUpdate,
    RoleCreate, RoleUpdate, AdminStatsResponse, PermissionInfo
)


class AdminService:
    """Service class for admin operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    # User Management
    async def get_users(
        self, 
        skip: int = 0, 
        limit: int = 100, 
        search: Optional[str] = None,
        role_id: Optional[uuid.UUID] = None,
        department_id: Optional[uuid.UUID] = None,
        is_active: Optional[bool] = None
    ) -> Dict[str, Any]:
        """Get paginated list of users with filters."""
        query = self.db.query(User)
        
        # Apply filters
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                User.username.ilike(search_term) | 
                User.email.ilike(search_term)
            )
        
        if role_id:
            query = query.filter(User.role_id == role_id)
        
        if department_id:
            query = query.filter(User.department_id == department_id)
        
        if is_active is not None:
            query = query.filter(User.is_active == is_active)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        users = query.offset(skip).limit(limit).all()
        
        # Format users with role and department names
        users_with_details = []
        for user in users:
            user_dict = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'is_active': user.is_active,
                'is_superuser': user.is_superuser,
                'role_id': user.role_id,
                'department_id': user.department_id,
                'created_at': user.created_at,
                'updated_at': user.updated_at,
                'role_name': user.role.name if user.role else None,
                'department_name': user.department.name if user.department else None
            }
            users_with_details.append(user_dict)
        
        return {
            'users': users_with_details,
            'total': total,
            'page': (skip // limit) + 1 if limit > 0 else 1,
            'page_size': limit,
            'total_pages': (total + limit - 1) // limit if limit > 0 else 1
        }
    
    async def get_user_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        """Get user by ID."""
        return self.db.query(User).filter(User.id == user_id).first()
    
    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        return self.db.query(User).filter(User.username == username).first()
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        return self.db.query(User).filter(User.email == email).first()
    
    async def create_user(self, user_data: UserCreate) -> User:
        """Create a new user."""
        # Check if username or email already exists
        if await self.get_user_by_username(user_data.username):
            raise ValueError(f"Username '{user_data.username}' already exists")
        
        if await self.get_user_by_email(user_data.email):
            raise ValueError(f"Email '{user_data.email}' already exists")
        
        # Validate role and department if provided
        if user_data.role_id:
            role = self.db.query(Role).filter(Role.id == user_data.role_id).first()
            if not role:
                raise ValueError(f"Role with ID {user_data.role_id} not found")
        
        if user_data.department_id:
            department = self.db.query(Department).filter(Department.id == user_data.department_id).first()
            if not department:
                raise ValueError(f"Department with ID {user_data.department_id} not found")
        
        # Hash password
        hashed_password = hash_password(user_data.password)
        
        # Create user
        db_user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password,
            is_active=user_data.is_active,
            is_superuser=user_data.is_superuser,
            role_id=user_data.role_id,
            department_id=user_data.department_id
        )
        
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        
        return db_user
    
    async def update_user(self, user_id: uuid.UUID, user_data: UserUpdate) -> Optional[User]:
        """Update an existing user."""
        db_user = await self.get_user_by_id(user_id)
        if not db_user:
            return None
        
        # Check for username conflicts
        if user_data.username and user_data.username != db_user.username:
            existing_user = await self.get_user_by_username(user_data.username)
            if existing_user:
                raise ValueError(f"Username '{user_data.username}' already exists")
        
        # Check for email conflicts
        if user_data.email and user_data.email != db_user.email:
            existing_user = await self.get_user_by_email(user_data.email)
            if existing_user:
                raise ValueError(f"Email '{user_data.email}' already exists")
        
        # Validate role and department if provided
        if user_data.role_id:
            role = self.db.query(Role).filter(Role.id == user_data.role_id).first()
            if not role:
                raise ValueError(f"Role with ID {user_data.role_id} not found")
        
        if user_data.department_id:
            department = self.db.query(Department).filter(Department.id == user_data.department_id).first()
            if not department:
                raise ValueError(f"Department with ID {user_data.department_id} not found")
        
        # Update fields
        update_data = user_data.dict(exclude_unset=True)
        
        # Handle password update separately
        if 'password' in update_data:
            update_data['hashed_password'] = hash_password(update_data.pop('password'))
        
        for field, value in update_data.items():
            setattr(db_user, field, value)
        
        self.db.commit()
        self.db.refresh(db_user)
        
        return db_user
    
    async def delete_user(self, user_id: uuid.UUID) -> bool:
        """Delete a user."""
        db_user = await self.get_user_by_id(user_id)
        if not db_user:
            return False
        
        # Don't allow deleting the last admin user
        if db_user.is_superuser or (db_user.role and db_user.role.name == 'admin'):
            admin_count = self.db.query(User).filter(
                (User.is_superuser == True) | 
                (User.role.has(Role.name == 'admin'))
            ).count()
            
            if admin_count <= 1:
                raise ValueError("Cannot delete the last admin user")
        
        self.db.delete(db_user)
        self.db.commit()
        
        return True
    
    # Department Management
    async def get_departments(self) -> List[Department]:
        """Get all departments."""
        return self.db.query(Department).all()
    
    async def get_department_by_id(self, department_id: uuid.UUID) -> Optional[Department]:
        """Get department by ID."""
        return self.db.query(Department).filter(Department.id == department_id).first()
    
    async def get_department_by_name(self, name: str) -> Optional[Department]:
        """Get department by name."""
        return self.db.query(Department).filter(Department.name == name).first()
    
    async def create_department(self, department_data: DepartmentCreate) -> Department:
        """Create a new department."""
        # Check if department name already exists
        if await self.get_department_by_name(department_data.name):
            raise ValueError(f"Department '{department_data.name}' already exists")
        
        db_department = Department(
            name=department_data.name,
            description=department_data.description
        )
        
        self.db.add(db_department)
        self.db.commit()
        self.db.refresh(db_department)
        
        return db_department
    
    async def update_department(self, department_id: uuid.UUID, department_data: DepartmentUpdate) -> Optional[Department]:
        """Update an existing department."""
        db_department = await self.get_department_by_id(department_id)
        if not db_department:
            return None
        
        # Check for name conflicts
        if department_data.name and department_data.name != db_department.name:
            existing_department = await self.get_department_by_name(department_data.name)
            if existing_department:
                raise ValueError(f"Department '{department_data.name}' already exists")
        
        # Update fields
        update_data = department_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_department, field, value)
        
        self.db.commit()
        self.db.refresh(db_department)
        
        return db_department
    
    async def delete_department(self, department_id: uuid.UUID) -> bool:
        """Delete a department."""
        db_department = await self.get_department_by_id(department_id)
        if not db_department:
            return False
        
        # Check if department has users
        if db_department.user_count > 0:
            raise ValueError(f"Cannot delete department '{db_department.name}' because it has {db_department.user_count} users")
        
        self.db.delete(db_department)
        self.db.commit()
        
        return True
    
    # Role Management
    async def get_roles(self) -> List[Role]:
        """Get all roles."""
        return self.db.query(Role).all()
    
    async def get_role_by_id(self, role_id: uuid.UUID) -> Optional[Role]:
        """Get role by ID."""
        return self.db.query(Role).filter(Role.id == role_id).first()
    
    async def get_role_by_name(self, name: str) -> Optional[Role]:
        """Get role by name."""
        return self.db.query(Role).filter(Role.name == name).first()
    
    async def create_role(self, role_data: RoleCreate) -> Role:
        """Create a new role."""
        # Check if role name already exists
        if await self.get_role_by_name(role_data.name):
            raise ValueError(f"Role '{role_data.name}' already exists")
        
        db_role = Role(
            name=role_data.name,
            description=role_data.description,
            permissions=role_data.permissions
        )
        
        self.db.add(db_role)
        self.db.commit()
        self.db.refresh(db_role)
        
        return db_role
    
    async def update_role(self, role_id: uuid.UUID, role_data: RoleUpdate) -> Optional[Role]:
        """Update an existing role."""
        db_role = await self.get_role_by_id(role_id)
        if not db_role:
            return None
        
        # Check for name conflicts
        if role_data.name and role_data.name != db_role.name:
            existing_role = await self.get_role_by_name(role_data.name)
            if existing_role:
                raise ValueError(f"Role '{role_data.name}' already exists")
        
        # Update fields
        update_data = role_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_role, field, value)
        
        self.db.commit()
        self.db.refresh(db_role)
        
        return db_role
    
    async def delete_role(self, role_id: uuid.UUID) -> bool:
        """Delete a role."""
        db_role = await self.get_role_by_id(role_id)
        if not db_role:
            return False
        
        # Check if role has users
        if db_role.user_count > 0:
            raise ValueError(f"Cannot delete role '{db_role.name}' because it has {db_role.user_count} users")
        
        # Don't allow deleting the admin role
        if db_role.name == 'admin':
            raise ValueError("Cannot delete the admin role")
        
        self.db.delete(db_role)
        self.db.commit()
        
        return True
    
    # Statistics and Analytics
    async def get_admin_stats(self) -> AdminStatsResponse:
        """Get admin dashboard statistics."""
        # Basic counts
        total_users = self.db.query(User).count()
        active_users = self.db.query(User).filter(User.is_active == True).count()
        total_departments = self.db.query(Department).count()
        total_roles = self.db.query(Role).count()
        
        # Users by role
        users_by_role = {}
        roles = self.db.query(Role).all()
        for role in roles:
            count = self.db.query(User).filter(User.role_id == role.id).count()
            users_by_role[role.name] = count
        
        # Users by department
        users_by_department = {}
        departments = self.db.query(Department).all()
        for department in departments:
            count = self.db.query(User).filter(User.department_id == department.id).count()
            users_by_department[department.name] = count
        
        # Recent users (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_users_count = self.db.query(User).filter(User.created_at >= thirty_days_ago).count()
        
        return AdminStatsResponse(
            total_users=total_users,
            active_users=active_users,
            total_departments=total_departments,
            total_roles=total_roles,
            users_by_role=users_by_role,
            users_by_department=users_by_department,
            recent_users_count=recent_users_count
        )
    
    # Permissions Management
    async def get_available_permissions(self) -> List[PermissionInfo]:
        """Get list of available permissions."""
        permissions = [
            PermissionInfo(name="*", description="All permissions (admin)", category="system"),
            PermissionInfo(name="chat", description="Access to chat interface", category="chat"),
            PermissionInfo(name="view_profile", description="View own profile", category="user"),
            PermissionInfo(name="view_usage", description="View own usage statistics", category="user"),
            PermissionInfo(name="view_reports", description="View usage reports", category="reporting"),
            PermissionInfo(name="manage_users", description="Manage users", category="admin"),
            PermissionInfo(name="manage_departments", description="Manage departments", category="admin"),
            PermissionInfo(name="manage_roles", description="Manage roles", category="admin"),
            PermissionInfo(name="manage_llms", description="Manage LLM configurations", category="admin"),
            PermissionInfo(name="manage_quotas", description="Manage department quotas", category="admin"),
            PermissionInfo(name="view_all_usage", description="View all users' usage", category="admin"),
            PermissionInfo(name="manage_department_users", description="Manage users in own department", category="manager"),
        ]
        return permissions
    
    # Initialization Helper
    async def create_default_data(self):
        """Create default roles and departments if they don't exist."""
        # Create default roles
        default_roles = [
            {"name": "admin", "description": "System Administrator", "permissions": ["*"]},
            {"name": "user", "description": "Standard User", "permissions": ["chat", "view_profile", "view_usage"]},
            {"name": "analyst", "description": "Data Analyst", "permissions": ["chat", "view_profile", "view_usage", "view_reports"]},
            {"name": "manager", "description": "Department Manager", "permissions": ["chat", "view_profile", "view_usage", "view_reports", "manage_department_users"]}
        ]
        
        for role_data in default_roles:
            existing_role = await self.get_role_by_name(role_data["name"])
            if not existing_role:
                await self.create_role(RoleCreate(**role_data))
        
        # Create default departments
        default_departments = Department.get_default_departments()
        
        for dept_data in default_departments:
            existing_dept = await self.get_department_by_name(dept_data["name"])
            if not existing_dept:
                await self.create_department(DepartmentCreate(**dept_data))
