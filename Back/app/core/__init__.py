"""
Core application modules for AI Dock App.

This package contains core configuration, database setup, and security utilities.
"""

from .config import settings, get_settings
from .database import (
    Base,
    engine,
    async_engine, 
    SessionLocal,
    AsyncSessionLocal,
    get_db,
    get_async_db,
    check_database_connection,
    check_async_database_connection,
    get_database_health_status
)
from .security import (
    verify_password,
    hash_password,
    create_access_token,
    create_refresh_token,
    verify_token,
    # get_current_user - will be implemented in API endpoints
)

__all__ = [
    # Configuration
    "settings",
    "get_settings",
    
    # Database
    "Base",
    "engine", 
    "async_engine",
    "SessionLocal",
    "AsyncSessionLocal",
    "get_db",
    "get_async_db",
    "check_database_connection",
    "check_async_database_connection", 
    "get_database_health_status",
    
    # Security
    "verify_password",
    "hash_password", 
    "create_access_token",
    "create_refresh_token",
    "verify_token",
    # "get_current_user" - will be implemented in API endpoints
]
