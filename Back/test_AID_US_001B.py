"""
Comprehensive test suite for AID-US-001B: JWT Authentication Utilities & Password Hashing

This test suite validates:
- Password hashing and verification
- Password strength validation  
- JWT access token generation and validation
- JWT refresh token generation and validation
- Token utilities and security helpers
- Authentication flow functions
"""

import pytest
import re
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

# Import the security module we just created
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
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
    
    # Authentication helpers
    create_user_tokens, refresh_access_token
)

from app.core.config import settings


class TestPasswordHashing:
    """Test password hashing and verification functions."""
    
    def test_hash_password_success(self):
        """Test successful password hashing."""
        password = "TestPassword123"
        hashed = hash_password(password)
        
        assert hashed is not None
        assert len(hashed) > 0
        assert hashed != password  # Should be different from original
        assert hashed.startswith("$2b$")  # bcrypt format
    
    def test_hash_password_empty(self):
        """Test hashing empty password raises error."""
        with pytest.raises(PasswordError, match="Password cannot be empty"):
            hash_password("")
    
    def test_verify_password_success(self):
        """Test successful password verification."""
        password = "TestPassword123"
        hashed = hash_password(password)
        
        assert verify_password(password, hashed) is True
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
    
    def test_password_hashing_consistency(self):
        """Test that same password produces different hashes."""
        password = "TestPassword123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        
        # Hashes should be different due to salt
        assert hash1 != hash2
        
        # But both should verify correctly
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True


class TestPasswordValidation:
    """Test password strength validation."""
    
    def test_validate_strong_password(self):
        """Test validation of strong password."""
        result = validate_password_strength("StrongPass123")
        
        assert result["valid"] is True
        assert len(result["errors"]) == 0
        assert result["requirements"]["min_length"] is True
        assert result["requirements"]["has_uppercase"] is True
        assert result["requirements"]["has_lowercase"] is True
        assert result["requirements"]["has_digit"] is True
    
    def test_validate_weak_passwords(self):
        """Test validation of various weak passwords."""
        test_cases = [
            ("", ["Password is required"]),
            ("short", ["Password must be at least 8 characters long"]),
            ("alllowercase123", ["Password must contain at least one uppercase letter"]),
            ("ALLUPPERCASE123", ["Password must contain at least one lowercase letter"]),
            ("NoDigitsHere", ["Password must contain at least one digit"]),
        ]
        
        for password, expected_errors in test_cases:
            result = validate_password_strength(password)
            assert result["valid"] is False
            for error in expected_errors:
                assert error in result["errors"]
    
    def test_validate_password_requirements_disabled(self):
        """Test password validation with disabled requirements."""
        # Mock settings to disable some requirements
        with patch.object(settings, 'PASSWORD_REQUIRE_UPPERCASE', False):
            with patch.object(settings, 'PASSWORD_REQUIRE_DIGITS', False):
                result = validate_password_strength("lowercase")
                
                # Should pass because uppercase and digits are not required
                assert result["requirements"]["has_uppercase"] is True
                assert result["requirements"]["has_digit"] is True


class TestJWTTokenGeneration:
    """Test JWT token generation functions."""
    
    def test_create_access_token(self):
        """Test access token creation."""
        data = {"sub": "user123", "username": "testuser"}
        token = create_access_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Decode and verify structure
        payload = decode_token(token)
        assert payload["sub"] == "user123"
        assert payload["username"] == "testuser"
        assert payload["type"] == "access"
        assert payload["iss"] == settings.JWT_ISSUER
        assert payload["aud"] == settings.JWT_AUDIENCE
        assert "exp" in payload
        assert "iat" in payload
        assert "jti" in payload
    
    def test_create_refresh_token(self):
        """Test refresh token creation."""
        data = {"sub": "user123", "username": "testuser"}
        token = create_refresh_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Decode and verify structure
        payload = decode_token(token)
        assert payload["sub"] == "user123"
        assert payload["username"] == "testuser"
        assert payload["type"] == "refresh"
        assert payload["remember_me"] is False
        assert "jti" in payload
    
    def test_create_refresh_token_remember_me(self):
        """Test refresh token creation with remember me."""
        data = {"sub": "user123"}
        token = create_refresh_token(data, remember_me=True)
        
        payload = decode_token(token)
        assert payload["remember_me"] is True
        
        # Should have longer expiration
        exp_time = datetime.fromtimestamp(payload["exp"], timezone.utc)
        now = datetime.now(timezone.utc)
        time_diff = exp_time - now
        
        # Should be close to 30 days (remember me expiry)
        assert time_diff.days >= 29  # Allow some tolerance
    
    def test_create_token_with_custom_expiry(self):
        """Test token creation with custom expiration."""
        data = {"sub": "user123"}
        custom_expiry = timedelta(hours=2)
        token = create_access_token(data, expires_delta=custom_expiry)
        
        payload = decode_token(token)
        exp_time = datetime.fromtimestamp(payload["exp"], timezone.utc)
        now = datetime.now(timezone.utc)
        time_diff = exp_time - now
        
        # Should be approximately 2 hours
        assert 7000 < time_diff.total_seconds() < 7300  # Allow some tolerance


class TestJWTTokenValidation:
    """Test JWT token validation functions."""
    
    def test_verify_valid_access_token(self):
        """Test verification of valid access token."""
        data = {"sub": "user123", "username": "testuser"}
        token = create_access_token(data)
        
        payload = verify_token(token, "access")
        assert payload["sub"] == "user123"
        assert payload["username"] == "testuser"
        assert payload["type"] == "access"
    
    def test_verify_valid_refresh_token(self):
        """Test verification of valid refresh token."""
        data = {"sub": "user123", "username": "testuser"}
        token = create_refresh_token(data)
        
        payload = verify_token(token, "refresh")
        assert payload["sub"] == "user123"
        assert payload["type"] == "refresh"
    
    def test_verify_wrong_token_type(self):
        """Test verification fails for wrong token type."""
        data = {"sub": "user123"}
        access_token = create_access_token(data)
        
        with pytest.raises(TokenError, match="Invalid token type"):
            verify_token(access_token, "refresh")
    
    def test_verify_invalid_token(self):
        """Test verification of invalid token."""
        with pytest.raises(TokenError, match="Invalid token"):
            verify_token("invalid.token.here", "access")
    
    def test_verify_expired_token(self):
        """Test verification of expired token."""
        data = {"sub": "user123"}
        expired_delta = timedelta(seconds=-1)  # Already expired
        token = create_access_token(data, expires_delta=expired_delta)
        
        with pytest.raises(TokenError, match="Token has expired"):
            verify_token(token, "access")
    
    def test_decode_token_without_verification(self):
        """Test token decoding without verification."""
        data = {"sub": "user123", "custom_field": "test"}
        token = create_access_token(data)
        
        payload = decode_token(token)
        assert payload["sub"] == "user123"
        assert payload["custom_field"] == "test"
    
    def test_is_token_expired(self):
        """Test token expiration checking."""
        # Valid token
        data = {"sub": "user123"}
        valid_token = create_access_token(data)
        assert is_token_expired(valid_token) is False
        
        # Expired token
        expired_token = create_access_token(data, expires_delta=timedelta(seconds=-1))
        assert is_token_expired(expired_token) is True
        
        # Invalid token
        assert is_token_expired("invalid.token") is True


class TestTokenUtilities:
    """Test token utility functions."""
    
    def test_extract_user_id(self):
        """Test user ID extraction from token."""
        data = {"sub": "user123"}
        token = create_access_token(data)
        
        user_id = extract_user_id(token)
        assert user_id == "user123"
        
        # Test with invalid token
        assert extract_user_id("invalid.token") is None
    
    def test_extract_user_info(self):
        """Test user info extraction from token."""
        data = {
            "sub": "user123",
            "username": "testuser",
            "email": "test@example.com",
            "role": "admin",
            "permissions": ["read", "write"]
        }
        token = create_access_token(data)
        
        user_info = extract_user_info(token)
        assert user_info["user_id"] == "user123"
        assert user_info["username"] == "testuser"
        assert user_info["email"] == "test@example.com"
        assert user_info["role"] == "admin"
        assert user_info["permissions"] == ["read", "write"]
        assert user_info["token_type"] == "access"
        assert "expires_at" in user_info
        assert "issued_at" in user_info
    
    def test_get_token_expiry(self):
        """Test token expiry extraction."""
        data = {"sub": "user123"}
        token = create_access_token(data)
        
        expiry = get_token_expiry(token)
        assert isinstance(expiry, datetime)
        assert expiry > datetime.now(timezone.utc)
        
        # Test with invalid token
        assert get_token_expiry("invalid.token") is None


class TestSecurityUtilities:
    """Test security utility functions."""
    
    def test_generate_secure_token(self):
        """Test secure token generation."""
        token1 = generate_secure_token()
        token2 = generate_secure_token()
        
        # Should be different
        assert token1 != token2
        
        # Should be URL-safe base64
        assert re.match(r'^[A-Za-z0-9_-]+$', token1)
        assert re.match(r'^[A-Za-z0-9_-]+$', token2)
        
        # Test custom length
        long_token = generate_secure_token(64)
        assert len(long_token) > len(token1)  # Should be longer
    
    def test_password_reset_token(self):
        """Test password reset token creation and verification."""
        user_id = "user123"
        reset_token = create_password_reset_token(user_id)
        
        # Verify token
        verified_user_id = verify_password_reset_token(reset_token)
        assert verified_user_id == user_id
        
        # Test invalid token
        assert verify_password_reset_token("invalid.token") is None
        
        # Test wrong token type
        access_token = create_access_token({"sub": user_id})
        assert verify_password_reset_token(access_token) is None
    
    def test_email_verification_token(self):
        """Test email verification token creation and verification."""
        user_id = "user123"
        email = "test@example.com"
        verification_token = create_email_verification_token(user_id, email)
        
        # Verify token
        result = verify_email_verification_token(verification_token)
        assert result is not None
        assert result["user_id"] == user_id
        assert result["email"] == email
        
        # Test invalid token
        assert verify_email_verification_token("invalid.token") is None


class TestAuthenticationHelpers:
    """Test authentication helper functions."""
    
    def test_create_user_tokens(self):
        """Test user token creation."""
        tokens = create_user_tokens(
            user_id="user123",
            username="testuser",
            email="test@example.com",
            role="admin",
            permissions=["read", "write"],
            remember_me=True
        )
        
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert tokens["token_type"] == "bearer"
        assert "expires_in" in tokens
        
        # Verify access token
        access_payload = decode_token(tokens["access_token"])
        assert access_payload["sub"] == "user123"
        assert access_payload["username"] == "testuser"
        assert access_payload["type"] == "access"
        
        # Verify refresh token
        refresh_payload = decode_token(tokens["refresh_token"])
        assert refresh_payload["sub"] == "user123"
        assert refresh_payload["type"] == "refresh"
        assert refresh_payload["remember_me"] is True
    
    def test_refresh_access_token(self):
        """Test access token refresh."""
        # Create initial tokens
        user_data = {
            "sub": "user123",
            "username": "testuser",
            "email": "test@example.com",
            "role": "user"
        }
        refresh_token = create_refresh_token(user_data)
        
        # Refresh access token
        new_tokens = refresh_access_token(refresh_token)
        
        assert "access_token" in new_tokens
        assert new_tokens["token_type"] == "bearer"
        assert "expires_in" in new_tokens
        
        # Verify new access token
        payload = decode_token(new_tokens["access_token"])
        assert payload["sub"] == "user123"
        assert payload["username"] == "testuser"
        assert payload["type"] == "access"
    
    def test_refresh_with_invalid_token(self):
        """Test refresh with invalid token."""
        with pytest.raises(TokenError):
            refresh_access_token("invalid.refresh.token")
        
        # Test with access token (wrong type)
        access_token = create_access_token({"sub": "user123"})
        with pytest.raises(TokenError):
            refresh_access_token(access_token)


class TestSecurityConfiguration:
    """Test security configuration integration."""
    
    def test_settings_loaded_correctly(self):
        """Test that security settings are loaded correctly."""
        assert hasattr(settings, 'JWT_SECRET_KEY')
        assert hasattr(settings, 'JWT_ALGORITHM')
        assert hasattr(settings, 'JWT_ACCESS_TOKEN_EXPIRE_MINUTES')
        assert hasattr(settings, 'BCRYPT_ROUNDS')
        assert hasattr(settings, 'PASSWORD_MIN_LENGTH')
        
        # Check default values
        assert settings.JWT_ALGORITHM == "HS256"
        assert settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES == 15
        assert settings.BCRYPT_ROUNDS == 12
        assert settings.PASSWORD_MIN_LENGTH == 8
    
    def test_token_includes_security_settings(self):
        """Test that tokens include configured security settings."""
        data = {"sub": "user123"}
        token = create_access_token(data)
        payload = decode_token(token)
        
        assert payload["iss"] == settings.JWT_ISSUER
        assert payload["aud"] == settings.JWT_AUDIENCE


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestAuthenticationFlow:
    """Test complete authentication flow integration."""
    
    def test_complete_login_flow(self):
        """Test complete login flow from password creation to token validation."""
        # 1. Create user with hashed password
        plain_password = "UserPassword123"
        hashed_password = hash_password(plain_password)
        
        # 2. Verify password (login attempt)
        assert verify_password(plain_password, hashed_password) is True
        
        # 3. Create tokens after successful login
        tokens = create_user_tokens(
            user_id="user123",
            username="testuser",
            email="test@example.com",
            role="user"
        )
        
        # 4. Verify access token can be used
        access_payload = verify_token(tokens["access_token"], "access")
        assert access_payload["sub"] == "user123"
        
        # 5. Refresh access token using refresh token
        new_tokens = refresh_access_token(tokens["refresh_token"])
        
        # 6. Verify new access token works
        new_payload = verify_token(new_tokens["access_token"], "access")
        assert new_payload["sub"] == "user123"
    
    def test_password_reset_flow(self):
        """Test password reset flow."""
        user_id = "user123"
        
        # 1. Create password reset token
        reset_token = create_password_reset_token(user_id)
        
        # 2. Verify reset token
        verified_user_id = verify_password_reset_token(reset_token)
        assert verified_user_id == user_id
        
        # 3. Create new password
        new_password = "NewPassword456"
        new_hashed = hash_password(new_password)
        
        # 4. Verify new password works
        assert verify_password(new_password, new_hashed) is True


# =============================================================================
# PERFORMANCE TESTS
# =============================================================================

class TestPerformance:
    """Test performance of security functions."""
    
    def test_password_hashing_performance(self):
        """Test password hashing performance."""
        import time
        
        password = "TestPassword123"
        start_time = time.time()
        
        # Hash 10 passwords
        for _ in range(10):
            hash_password(password)
        
        end_time = time.time()
        avg_time = (end_time - start_time) / 10
        
        # Should take reasonable time (less than 1 second per hash with bcrypt rounds=12)
        assert avg_time < 1.0
    
    def test_token_generation_performance(self):
        """Test token generation performance."""
        import time
        
        data = {"sub": "user123", "username": "testuser"}
        start_time = time.time()
        
        # Generate 100 tokens
        for _ in range(100):
            create_access_token(data)
        
        end_time = time.time()
        avg_time = (end_time - start_time) / 100
        
        # Should be very fast (less than 10ms per token)
        assert avg_time < 0.01


if __name__ == "__main__":
    # Run tests if script is executed directly
    pytest.main([__file__, "-v", "--tb=short"])
