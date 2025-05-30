"""
Unit Tests for AID-US-001B: JWT Authentication Utilities & Password Hashing

This module contains unit tests for individual security functions:
- Password hashing and verification
- JWT token generation and validation
- Security utilities
- Configuration integration

These tests focus on testing individual functions in isolation.
"""

import pytest
import re
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

# Import the security module
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.security import (
    # Exceptions
    SecurityError, TokenError, PasswordError,
    
    # Password functions
    hash_password, verify_password, validate_password_strength,
    
    # JWT functions
    create_access_token, create_refresh_token, verify_token, decode_token,
    extract_user_id, extract_user_info, is_token_expired, get_token_expiry,
    
    # Security utilities
    generate_secure_token, create_password_reset_token, verify_password_reset_token,
    create_email_verification_token, verify_email_verification_token,
)

from app.core.config import settings


class TestPasswordHashing:
    """Unit tests for password hashing functions."""
    
    def test_hash_password_success(self):
        """Test successful password hashing."""
        password = "TestPassword123"
        hashed = hash_password(password)
        
        assert hashed is not None
        assert len(hashed) > 0
        assert hashed != password
        assert hashed.startswith("$2b$")  # bcrypt format
    
    def test_hash_password_empty_raises_error(self):
        """Test that hashing empty password raises PasswordError."""
        with pytest.raises(PasswordError, match="Password cannot be empty"):
            hash_password("")
    
    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        password = "TestPassword123"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True
    
    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password."""
        password = "TestPassword123"
        hashed = hash_password(password)
        assert verify_password("WrongPassword", hashed) is False
    
    def test_verify_password_empty_inputs(self):
        """Test password verification with empty inputs."""
        hashed = hash_password("test123")
        assert verify_password("", hashed) is False
        assert verify_password("test123", "") is False
        assert verify_password("", "") is False
    
    def test_verify_password_invalid_hash(self):
        """Test password verification with invalid hash."""
        assert verify_password("test123", "invalid_hash") is False
    
    def test_password_hashing_uses_salt(self):
        """Test that password hashing uses salt (same password produces different hashes)."""
        password = "TestPassword123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        
        assert hash1 != hash2  # Different due to salt
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True


class TestPasswordValidation:
    """Unit tests for password strength validation."""
    
    def test_validate_strong_password(self):
        """Test validation of a strong password."""
        result = validate_password_strength("StrongPass123")
        
        assert result["valid"] is True
        assert len(result["errors"]) == 0
        assert result["requirements"]["min_length"] is True
        assert result["requirements"]["has_uppercase"] is True
        assert result["requirements"]["has_lowercase"] is True
        assert result["requirements"]["has_digit"] is True
    
    def test_validate_empty_password(self):
        """Test validation of empty password."""
        result = validate_password_strength("")
        
        assert result["valid"] is False
        assert "Password is required" in result["errors"]
    
    def test_validate_short_password(self):
        """Test validation of password that's too short."""
        result = validate_password_strength("short")
        
        assert result["valid"] is False
        assert any("at least" in error for error in result["errors"])
        assert result["requirements"]["min_length"] is False
    
    def test_validate_no_uppercase(self):
        """Test validation of password without uppercase letters."""
        result = validate_password_strength("alllowercase123")
        
        assert result["valid"] is False
        assert any("uppercase" in error for error in result["errors"])
        assert result["requirements"]["has_uppercase"] is False
    
    def test_validate_no_lowercase(self):
        """Test validation of password without lowercase letters."""
        result = validate_password_strength("ALLUPPERCASE123")
        
        assert result["valid"] is False
        assert any("lowercase" in error for error in result["errors"])
        assert result["requirements"]["has_lowercase"] is False
    
    def test_validate_no_digits(self):
        """Test validation of password without digits."""
        result = validate_password_strength("NoDigitsHere")
        
        assert result["valid"] is False
        assert any("digit" in error for error in result["errors"])
        assert result["requirements"]["has_digit"] is False
    
    def test_validate_requirements_can_be_disabled(self):
        """Test that password requirements can be disabled via configuration."""
        with patch.object(settings, 'PASSWORD_REQUIRE_UPPERCASE', False):
            with patch.object(settings, 'PASSWORD_REQUIRE_DIGITS', False):
                result = validate_password_strength("lowercase")
                
                assert result["requirements"]["has_uppercase"] is True
                assert result["requirements"]["has_digit"] is True


class TestJWTTokenGeneration:
    """Unit tests for JWT token generation."""
    
    def test_create_access_token_basic(self):
        """Test basic access token creation."""
        data = {"sub": "user123", "username": "testuser"}
        token = create_access_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Verify token structure
        payload = decode_token(token)
        assert payload["sub"] == "user123"
        assert payload["username"] == "testuser"
        assert payload["type"] == "access"
        assert "exp" in payload
        assert "iat" in payload
        assert "jti" in payload
    
    def test_create_access_token_with_custom_expiry(self):
        """Test access token creation with custom expiration time."""
        data = {"sub": "user123"}
        custom_expiry = timedelta(hours=2)
        token = create_access_token(data, expires_delta=custom_expiry)
        
        payload = decode_token(token)
        exp_time = datetime.fromtimestamp(payload["exp"], timezone.utc)
        now = datetime.now(timezone.utc)
        time_diff = exp_time - now
        
        # Should be approximately 2 hours
        assert 7000 < time_diff.total_seconds() < 7300
    
    def test_create_refresh_token_basic(self):
        """Test basic refresh token creation."""
        data = {"sub": "user123", "username": "testuser"}
        token = create_refresh_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        payload = decode_token(token)
        assert payload["sub"] == "user123"
        assert payload["type"] == "refresh"
        assert payload["remember_me"] is False
    
    def test_create_refresh_token_remember_me(self):
        """Test refresh token creation with remember me option."""
        data = {"sub": "user123"}
        token = create_refresh_token(data, remember_me=True)
        
        payload = decode_token(token)
        assert payload["remember_me"] is True
        
        # Should have longer expiration
        exp_time = datetime.fromtimestamp(payload["exp"], timezone.utc)
        now = datetime.now(timezone.utc)
        time_diff = exp_time - now
        
        # Should be close to 30 days
        assert time_diff.days >= 29
    
    def test_token_includes_standard_claims(self):
        """Test that tokens include standard JWT claims."""
        data = {"sub": "user123"}
        token = create_access_token(data)
        payload = decode_token(token)
        
        assert payload["iss"] == settings.JWT_ISSUER
        assert payload["aud"] == settings.JWT_AUDIENCE
        assert "exp" in payload
        assert "iat" in payload
        assert "jti" in payload


class TestJWTTokenValidation:
    """Unit tests for JWT token validation."""
    
    def test_verify_valid_access_token(self):
        """Test verification of a valid access token."""
        data = {"sub": "user123", "username": "testuser"}
        token = create_access_token(data)
        
        payload = verify_token(token, "access")
        assert payload["sub"] == "user123"
        assert payload["username"] == "testuser"
        assert payload["type"] == "access"
    
    def test_verify_valid_refresh_token(self):
        """Test verification of a valid refresh token."""
        data = {"sub": "user123"}
        token = create_refresh_token(data)
        
        payload = verify_token(token, "refresh")
        assert payload["sub"] == "user123"
        assert payload["type"] == "refresh"
    
    def test_verify_token_wrong_type(self):
        """Test that verification fails for wrong token type."""
        data = {"sub": "user123"}
        access_token = create_access_token(data)
        
        with pytest.raises(TokenError, match="Invalid token type"):
            verify_token(access_token, "refresh")
    
    def test_verify_invalid_token(self):
        """Test verification of completely invalid token."""
        with pytest.raises(TokenError, match="Invalid token"):
            verify_token("invalid.token.here", "access")
    
    def test_verify_expired_token(self):
        """Test verification of expired token."""
        data = {"sub": "user123"}
        expired_token = create_access_token(data, expires_delta=timedelta(seconds=-1))
        
        with pytest.raises(TokenError, match="Token has expired"):
            verify_token(expired_token, "access")
    
    def test_decode_token_without_verification(self):
        """Test token decoding without signature verification."""
        data = {"sub": "user123", "custom_field": "test_value"}
        token = create_access_token(data)
        
        payload = decode_token(token)
        assert payload["sub"] == "user123"
        assert payload["custom_field"] == "test_value"
    
    def test_decode_invalid_token_raises_error(self):
        """Test that decoding invalid token raises TokenError."""
        with pytest.raises(TokenError):
            decode_token("completely.invalid.token")


class TestTokenUtilities:
    """Unit tests for token utility functions."""
    
    def test_extract_user_id_valid_token(self):
        """Test extracting user ID from valid token."""
        data = {"sub": "user123"}
        token = create_access_token(data)
        
        user_id = extract_user_id(token)
        assert user_id == "user123"
    
    def test_extract_user_id_invalid_token(self):
        """Test extracting user ID from invalid token returns None."""
        assert extract_user_id("invalid.token") is None
    
    def test_extract_user_info_complete(self):
        """Test extracting complete user info from token."""
        data = {
            "sub": "user123",
            "username": "testuser",
            "email": "test@example.com",
            "role": "admin",
            "permissions": ["read", "write"],
            "is_superuser": True
        }
        token = create_access_token(data)
        
        user_info = extract_user_info(token)
        assert user_info["user_id"] == "user123"
        assert user_info["username"] == "testuser"
        assert user_info["email"] == "test@example.com"
        assert user_info["role"] == "admin"
        assert user_info["permissions"] == ["read", "write"]
        assert user_info["is_superuser"] is True
        assert user_info["token_type"] == "access"
        assert "expires_at" in user_info
        assert "issued_at" in user_info
    
    def test_extract_user_info_invalid_token(self):
        """Test extracting user info from invalid token returns empty dict."""
        user_info = extract_user_info("invalid.token")
        assert user_info == {}
    
    def test_is_token_expired_valid_token(self):
        """Test expiry check on valid token."""
        data = {"sub": "user123"}
        token = create_access_token(data)
        assert is_token_expired(token) is False
    
    def test_is_token_expired_expired_token(self):
        """Test expiry check on expired token."""
        data = {"sub": "user123"}
        expired_token = create_access_token(data, expires_delta=timedelta(seconds=-1))
        assert is_token_expired(expired_token) is True
    
    def test_is_token_expired_invalid_token(self):
        """Test expiry check on invalid token returns True."""
        assert is_token_expired("invalid.token") is True
    
    def test_get_token_expiry_valid_token(self):
        """Test getting expiry time from valid token."""
        data = {"sub": "user123"}
        token = create_access_token(data)
        
        expiry = get_token_expiry(token)
        assert isinstance(expiry, datetime)
        assert expiry > datetime.now(timezone.utc)
    
    def test_get_token_expiry_invalid_token(self):
        """Test getting expiry time from invalid token returns None."""
        assert get_token_expiry("invalid.token") is None


class TestSecurityUtilities:
    """Unit tests for security utility functions."""
    
    def test_generate_secure_token_default_length(self):
        """Test secure token generation with default length."""
        token = generate_secure_token()
        
        assert isinstance(token, str)
        assert len(token) > 0
        assert re.match(r'^[A-Za-z0-9_-]+$', token)  # URL-safe base64
    
    def test_generate_secure_token_custom_length(self):
        """Test secure token generation with custom length."""
        short_token = generate_secure_token(8)
        long_token = generate_secure_token(64)
        
        assert len(long_token) > len(short_token)
        assert re.match(r'^[A-Za-z0-9_-]+$', short_token)
        assert re.match(r'^[A-Za-z0-9_-]+$', long_token)
    
    def test_generate_secure_token_uniqueness(self):
        """Test that generated tokens are unique."""
        token1 = generate_secure_token()
        token2 = generate_secure_token()
        assert token1 != token2
    
    def test_create_password_reset_token(self):
        """Test password reset token creation."""
        user_id = "user123"
        reset_token = create_password_reset_token(user_id)
        
        assert isinstance(reset_token, str)
        assert len(reset_token) > 0
        
        # Verify it's a valid JWT with correct claims
        payload = decode_token(reset_token)
        assert payload["sub"] == user_id
        assert payload["type"] == "password_reset"
    
    def test_verify_password_reset_token_valid(self):
        """Test verification of valid password reset token."""
        user_id = "user123"
        reset_token = create_password_reset_token(user_id)
        
        verified_user_id = verify_password_reset_token(reset_token)
        assert verified_user_id == user_id
    
    def test_verify_password_reset_token_invalid(self):
        """Test verification of invalid password reset token."""
        assert verify_password_reset_token("invalid.token") is None
    
    def test_verify_password_reset_token_wrong_type(self):
        """Test that access tokens are not accepted as password reset tokens."""
        access_token = create_access_token({"sub": "user123"})
        assert verify_password_reset_token(access_token) is None
    
    def test_create_email_verification_token(self):
        """Test email verification token creation."""
        user_id = "user123"
        email = "test@example.com"
        verification_token = create_email_verification_token(user_id, email)
        
        assert isinstance(verification_token, str)
        assert len(verification_token) > 0
        
        payload = decode_token(verification_token)
        assert payload["sub"] == user_id
        assert payload["email"] == email
        assert payload["type"] == "email_verification"
    
    def test_verify_email_verification_token_valid(self):
        """Test verification of valid email verification token."""
        user_id = "user123"
        email = "test@example.com"
        verification_token = create_email_verification_token(user_id, email)
        
        result = verify_email_verification_token(verification_token)
        assert result is not None
        assert result["user_id"] == user_id
        assert result["email"] == email
    
    def test_verify_email_verification_token_invalid(self):
        """Test verification of invalid email verification token."""
        assert verify_email_verification_token("invalid.token") is None


class TestConfigurationIntegration:
    """Unit tests for configuration integration."""
    
    def test_settings_are_loaded(self):
        """Test that security settings are properly loaded."""
        assert hasattr(settings, 'JWT_SECRET_KEY')
        assert hasattr(settings, 'JWT_ALGORITHM')
        assert hasattr(settings, 'JWT_ACCESS_TOKEN_EXPIRE_MINUTES')
        assert hasattr(settings, 'BCRYPT_ROUNDS')
        assert hasattr(settings, 'PASSWORD_MIN_LENGTH')
    
    def test_jwt_settings_in_tokens(self):
        """Test that JWT settings are reflected in tokens."""
        data = {"sub": "user123"}
        token = create_access_token(data)
        payload = decode_token(token)
        
        assert payload["iss"] == settings.JWT_ISSUER
        assert payload["aud"] == settings.JWT_AUDIENCE
    
    def test_bcrypt_rounds_configuration(self):
        """Test that bcrypt rounds configuration is used."""
        # This is hard to test directly, but we can verify the setting exists
        assert isinstance(settings.BCRYPT_ROUNDS, int)
        assert settings.BCRYPT_ROUNDS >= 10  # Reasonable minimum


class TestErrorHandling:
    """Unit tests for error handling."""
    
    def test_password_error_inheritance(self):
        """Test that PasswordError inherits from SecurityError."""
        assert issubclass(PasswordError, SecurityError)
    
    def test_token_error_inheritance(self):
        """Test that TokenError inherits from SecurityError."""
        assert issubclass(TokenError, SecurityError)
    
    def test_password_error_message(self):
        """Test PasswordError with custom message."""
        try:
            raise PasswordError("Custom password error")
        except PasswordError as e:
            assert str(e) == "Custom password error"
    
    def test_token_error_message(self):
        """Test TokenError with custom message."""
        try:
            raise TokenError("Custom token error")
        except TokenError as e:
            assert str(e) == "Custom token error"


if __name__ == "__main__":
    # Run tests if script is executed directly
    pytest.main([__file__, "-v", "--tb=short"])
