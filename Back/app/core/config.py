"""
FastAPI application configuration and settings.
"""
from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # Database
    DATABASE_URL: str = "postgresql://aidock:aidock@localhost:5432/aidock"
    DATABASE_URL_ASYNC: str = "postgresql+asyncpg://aidock:aidock@localhost:5432/aidock"
    
    # JWT Settings
    JWT_SECRET_KEY: str = "your-super-secret-jwt-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    JWT_REFRESH_TOKEN_REMEMBER_ME_EXPIRE_DAYS: int = 30
    
    # JWT Security Settings
    JWT_TOKEN_URL: str = "/auth/login"
    JWT_REFRESH_URL: str = "/auth/refresh"
    JWT_ISSUER: str = "ai-dock-app"
    JWT_AUDIENCE: str = "ai-dock-users"
    
    # Security
    BCRYPT_ROUNDS: int = 12
    BCRYPT_SCHEMES: list[str] = ["bcrypt"]
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_LOWERCASE: bool = True
    PASSWORD_REQUIRE_DIGITS: bool = True
    PASSWORD_REQUIRE_SPECIAL: bool = False
    
    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "AI Dock App"
    PROJECT_VERSION: str = "1.0.0"
    
    # CORS
    BACKEND_CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
        "http://localhost:5173",
    ]
    
    # Rate Limiting
    RATE_LIMIT_LOGIN: str = "5/minute"
    RATE_LIMIT_REFRESH: str = "10/minute"
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # LLM API Keys and Configuration
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_ORGANIZATION: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    AZURE_OPENAI_API_KEY: Optional[str] = None
    AZURE_OPENAI_ENDPOINT: Optional[str] = None
    AZURE_OPENAI_API_VERSION: str = "2023-05-15"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    
    # Redis (for caching, rate limiting, and background tasks)
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_PASSWORD: Optional[str] = None
    REDIS_DB: int = 0
    
    # Background Tasks (Celery)
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"
    
    # Token Cleanup Settings
    TOKEN_CLEANUP_ENABLED: bool = True
    TOKEN_CLEANUP_INTERVAL_HOURS: int = 1
    TOKEN_MAX_RETENTION_DAYS: int = 90
    
    # Rate Limiting Settings
    RATE_LIMITING_ENABLED: bool = True
    RATE_LIMIT_LOGIN_REQUESTS: int = 5
    RATE_LIMIT_LOGIN_WINDOW: int = 900  # 15 minutes
    RATE_LIMIT_REFRESH_REQUESTS: int = 30
    RATE_LIMIT_REFRESH_WINDOW: int = 300  # 5 minutes
    RATE_LIMIT_GENERAL_REQUESTS: int = 100
    RATE_LIMIT_GENERAL_WINDOW: int = 300  # 5 minutes
    
    # Security Headers
    SECURITY_HEADERS_ENABLED: bool = True
    HSTS_MAX_AGE: int = 31536000  # 1 year
    CONTENT_SECURITY_POLICY: str = "default-src 'self'"
    
    # Monitoring and Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    ENABLE_SECURITY_LOGGING: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()


# Global settings instance
settings = get_settings()
