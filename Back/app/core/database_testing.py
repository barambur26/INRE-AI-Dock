"""
Database configuration and session management - Testing Version
This version uses SQLite and works without PostgreSQL dependencies.
"""
import asyncio
from typing import Dict, Any
from contextlib import asynccontextmanager
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Import testing config that doesn't require PostgreSQL
try:
    from app.core.config import settings
except ImportError:
    # Fallback to testing config if main config fails
    from app.core.config_testing import settings

# Create synchronous engine (SQLite for testing)
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    # SQLite-specific settings
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
)

# Create asynchronous engine
try:
    async_engine = create_async_engine(
        settings.DATABASE_URL_ASYNC,
        pool_pre_ping=True,
        # SQLite-specific settings for async
        connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL_ASYNC else {},
    )
except Exception:
    # Fallback if async engine fails
    async_engine = None

# Create session makers
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

if async_engine:
    AsyncSessionLocal = sessionmaker(
        class_=AsyncSession,
        autocommit=False,
        autoflush=False,
        bind=async_engine
    )
else:
    AsyncSessionLocal = None

# Base class for SQLAlchemy models
Base = declarative_base()


# Dependency for getting database session
def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db():
    """Get async database session."""
    if AsyncSessionLocal is None:
        raise RuntimeError("Async database not configured")
    async with AsyncSessionLocal() as session:
        yield session


# Database health checking utilities
def check_database_connection() -> bool:
    """Check if the synchronous database connection is working."""
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            return result.fetchone()[0] == 1
    except Exception:
        return False


async def check_async_database_connection() -> bool:
    """Check if the asynchronous database connection is working."""
    if async_engine is None:
        return False
    try:
        async with async_engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            return result.fetchone()[0] == 1
    except Exception:
        return False


async def get_database_health_status() -> Dict[str, Any]:
    """Get comprehensive database health status."""
    # Hide credentials in URL
    db_url_safe = settings.DATABASE_URL
    if "@" in db_url_safe:
        db_url_safe = db_url_safe.split("@")[-1]
    
    health_status = {
        "database_url": db_url_safe,
        "sync_connection": False,
        "async_connection": False,
        "database_type": "sqlite" if "sqlite" in settings.DATABASE_URL else "postgresql",
    }
    
    # Add pool info if available (not available for SQLite)
    if hasattr(engine.pool, 'size'):
        health_status.update({
            "pool_size": engine.pool.size(),
            "checked_in_connections": engine.pool.checkedin(),
            "checked_out_connections": engine.pool.checkedout(),
            "overflow": engine.pool.overflow(),
            "invalid_connections": engine.pool.invalidated(),
        })
    
    # Test synchronous connection
    health_status["sync_connection"] = check_database_connection()
    
    # Test asynchronous connection
    health_status["async_connection"] = await check_async_database_connection()
    
    # Overall health
    health_status["healthy"] = health_status["sync_connection"]
    
    return health_status


@asynccontextmanager
async def get_async_session():
    """Context manager for async database sessions."""
    if AsyncSessionLocal is None:
        raise RuntimeError("Async database not configured")
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
