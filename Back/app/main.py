"""
AI Dock App - FastAPI Main Application with Security Enhancements
"""

import sys
import os
from pathlib import Path

# Add parent directory to Python path for direct execution
# This allows 'python app/main.py' to work by ensuring the 'app' module can be found
if __name__ == "__main__":
    # Get the Back directory (parent of app directory)
    back_dir = Path(__file__).parent.parent
    if str(back_dir) not in sys.path:
        sys.path.insert(0, str(back_dir))

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import uvicorn
from datetime import datetime
import logging

# Import API routers
from app.api.auth import router as auth_router
from app.api.admin import router as admin_router
from app.api.chat import router as chat_router
from app.core.config import settings
from app.middleware.rate_limit import (
    RateLimitMiddleware, 
    rate_limit_exceeded_handler,
    get_rate_limit_stats,
    clear_rate_limits
)

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI application instance
app = FastAPI(
    title="AI Dock API",
    description="A secure internal web application for accessing multiple LLMs with role-based permissions and advanced security features",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {
            "name": "Authentication",
            "description": "User authentication and token management with rate limiting",
        },
        {
            "name": "Admin",
            "description": "Administrative operations for user and department management",
        },
        {
            "name": "Admin - Users",
            "description": "User management operations (CRUD, roles, departments)",
        },
        {
            "name": "Admin - Departments",
            "description": "Department management operations (CRUD, user assignments)",
        },
        {
            "name": "Admin - Roles",
            "description": "Role management operations (CRUD, permissions, user assignments)",
        },
        {
            "name": "chat",
            "description": "Chat interface for LLM interactions with usage tracking and quota management",
        },
        {
            "name": "System", 
            "description": "System health and status endpoints",
        },
        {
            "name": "Security",
            "description": "Security monitoring and rate limiting endpoints",
        },
        {
            "name": "Health",
            "description": "Service health monitoring",
        },
        {
            "name": "Development",
            "description": "Development and testing utilities",
        },
    ]
)

# Add security middleware
if settings.SECURITY_HEADERS_ENABLED:
    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):
        """Add security headers to all responses"""
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = settings.CONTENT_SECURITY_POLICY
        
        # HSTS for HTTPS (only in production)
        if settings.ENVIRONMENT == "production":
            response.headers["Strict-Transport-Security"] = f"max-age={settings.HSTS_MAX_AGE}; includeSubDomains"
        
        return response

# Add rate limiting middleware
if settings.RATE_LIMITING_ENABLED:
    app.add_middleware(
        RateLimitMiddleware,
        enable_rate_limiting=True
    )
    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# Add trusted host middleware (security)
if settings.ENVIRONMENT == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*.yourdomain.com", "localhost", "127.0.0.1"]
    )

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(admin_router, prefix=settings.API_V1_STR)
app.include_router(chat_router, prefix=settings.API_V1_STR)

# Security monitoring endpoints
@app.get("/api/v1/security/rate-limits", tags=["Security"])
async def get_rate_limit_stats_endpoint():
    """
    Get current rate limiting statistics (admin only in production)
    """
    try:
        stats = get_rate_limit_stats()
        return {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "rate_limit_stats": stats
        }
    except Exception as e:
        logger.error(f"Error getting rate limit stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get rate limit statistics")

@app.post("/api/v1/security/rate-limits/clear", tags=["Security"])
async def clear_rate_limits_endpoint(ip: str = None):
    """
    Clear rate limits (admin only - development/testing)
    """
    if settings.ENVIRONMENT == "production":
        raise HTTPException(status_code=403, detail="Not available in production")
    
    try:
        result = clear_rate_limits(ip)
        logger.info(f"Rate limits cleared: {result}")
        return {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "result": result
        }
    except Exception as e:
        logger.error(f"Error clearing rate limits: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear rate limit statistics")

# Health check endpoint
@app.get("/health", tags=["System"])
async def health_check():
    """
    Health check endpoint to verify the API is running with security status
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "service": "AI Dock API",
        "authentication": "enabled",
        "security_features": {
            "rate_limiting": settings.RATE_LIMITING_ENABLED,
            "security_headers": settings.SECURITY_HEADERS_ENABLED,
            "token_cleanup": settings.TOKEN_CLEANUP_ENABLED,
            "environment": settings.ENVIRONMENT
        },
        "endpoints": {
            "auth": f"{settings.API_V1_STR}/auth",
            "admin": f"{settings.API_V1_STR}/admin",
            "chat": f"{settings.API_V1_STR}/chat",
            "security": f"{settings.API_V1_STR}/security",
            "docs": "/docs",
            "health": "/health"
        }
    }

# Root endpoint
@app.get("/", tags=["System"])
async def root():
    """
    Root endpoint with comprehensive API information including security features
    """
    return {
        "message": "Welcome to AI Dock API - Secure LLM Gateway",
        "version": "1.0.0",
        "description": "Secure internal LLM gateway with authentication and advanced security features",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health",
        "authentication": f"{settings.API_V1_STR}/auth",
        "admin": f"{settings.API_V1_STR}/admin",
        "chat": f"{settings.API_V1_STR}/chat",
        "security": f"{settings.API_V1_STR}/security",
        "features": [
            "JWT Authentication",
            "Role-based Access Control",
            "Admin User Management",
            "Department Management",
            "Role & Permission Management",
            "LLM Chat Interface",
            "Usage Tracking & Quotas",
            "Multi-LLM Provider Support",
            "Token Refresh & Cleanup",
            "Password Security",
            "Rate Limiting",
            "Security Headers",
            "Background Tasks",
            "Security Monitoring"
        ],
        "security_status": {
            "rate_limiting": "enabled" if settings.RATE_LIMITING_ENABLED else "disabled",
            "security_headers": "enabled" if settings.SECURITY_HEADERS_ENABLED else "disabled",
            "token_cleanup": "enabled" if settings.TOKEN_CLEANUP_ENABLED else "disabled",
            "environment": settings.ENVIRONMENT
        }
    }

# Exception handler for general errors
@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "timestamp": datetime.utcnow().isoformat()
        }
    )

# Run the application
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )
