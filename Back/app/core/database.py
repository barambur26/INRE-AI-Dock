"""
Database configuration and session management.
"""
import asyncio
from typing import Dict, Any
from contextlib import asynccontextmanager
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# Create synchronous engine
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
)

# Create asynchronous engine
async_engine = create_async_engine(
    settings.DATABASE_URL_ASYNC,
    pool_pre_ping=True,
    pool_recycle=300,
)

# Create session makers
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

AsyncSessionLocal = sessionmaker(
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    bind=async_engine
)

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
    try:
        async with async_engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            return result.fetchone()[0] == 1
    except Exception:
        return False


async def get_database_health_status() -> Dict[str, Any]:
    """Get comprehensive database health status."""
    health_status = {
        "database_url": settings.DATABASE_URL.split("@")[-1],  # Hide credentials
        "sync_connection": False,
        "async_connection": False,
        "pool_size": engine.pool.size(),
        "checked_in_connections": engine.pool.checkedin(),
        "checked_out_connections": engine.pool.checkedout(),
        "overflow": engine.pool.overflow(),
        "invalid_connections": engine.pool.invalidated(),
    }
    
    # Test synchronous connection
    health_status["sync_connection"] = check_database_connection()
    
    # Test asynchronous connection
    health_status["async_connection"] = await check_async_database_connection()
    
    # Overall health
    health_status["healthy"] = (
        health_status["sync_connection"] and 
        health_status["async_connection"]
    )
    
    return health_status


@asynccontextmanager
async def get_async_session():
    """Context manager for async database sessions."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
