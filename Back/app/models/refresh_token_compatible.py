"""
RefreshToken model for JWT authentication and session management - Compatible Version
This version works with both PostgreSQL and SQLite.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class RefreshToken(Base):
    """RefreshToken model for JWT refresh token management."""
    
    __tablename__ = "refresh_tokens"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Token information
    token_hash = Column(String(255), unique=True, nullable=False, index=True)
    
    # User association
    user_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("users.id", ondelete="CASCADE"), 
        nullable=False, 
        index=True
    )
    
    # Token lifecycle
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    is_revoked = Column(Boolean, default=False, index=True)
    remember_me = Column(Boolean, default=False)
    
    # Security metadata - using String instead of INET for SQLite compatibility
    user_agent = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)  # IPv6 max length is 45 chars
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="refresh_tokens")
    
    def __repr__(self):
        """String representation of RefreshToken object."""
        return f"<RefreshToken(id={self.id}, user_id={self.user_id}, expires_at={self.expires_at}, is_revoked={self.is_revoked})>"
    
    def is_expired(self) -> bool:
        """Check if the refresh token has expired."""
        return datetime.now(timezone.utc) > self.expires_at.replace(tzinfo=timezone.utc)
    
    def is_valid(self) -> bool:
        """Check if the refresh token is valid (not expired and not revoked)."""
        return not self.is_revoked and not self.is_expired()
    
    def revoke(self) -> None:
        """Revoke the refresh token."""
        self.is_revoked = True
    
    @property
    def is_remember_me_token(self) -> bool:
        """Check if this is a remember me token."""
        return self.remember_me
    
    @property
    def days_until_expiry(self) -> int:
        """Get the number of days until token expiry."""
        if self.is_expired():
            return 0
        
        now = datetime.now(timezone.utc)
        expires_at_utc = self.expires_at.replace(tzinfo=timezone.utc)
        delta = expires_at_utc - now
        return max(0, delta.days)
    
    @property
    def security_info(self) -> dict:
        """Get security information for the token."""
        return {
            "user_agent": self.user_agent,
            "ip_address": self.ip_address,
            "created_at": self.created_at,
            "remember_me": self.remember_me
        }
    
    @classmethod
    def create_token(
        cls,
        user_id: uuid.UUID,
        token_hash: str,
        expires_at: datetime,
        remember_me: bool = False,
        user_agent: str = None,
        ip_address: str = None
    ) -> "RefreshToken":
        """Create a new refresh token instance."""
        return cls(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            remember_me=remember_me,
            user_agent=user_agent,
            ip_address=ip_address
        )
