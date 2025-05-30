"""
Integration Tests for AID-US-001B: JWT Authentication Utilities & Password Hashing

This module contains integration tests for complete authentication flows:
- User registration and login flow
- Token refresh flow
- Password reset flow
- Email verification flow
- Multi-step authentication scenarios

These tests focus on testing how different security functions work together.
"""

import pytest
import time
from datetime import datetime, timedelta, timezone

# Import the security module
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.security import (
    # Exceptions
    TokenError, PasswordError,
    
    # Password functions
    hash_password, verify_password, validate_password_strength,
    
    # JWT functions
    create_access_token, create_refresh_token, verify_token,
    extract_user_info, is_token_expired,
    
    # Security utilities
    create_password_reset_token, verify_password_reset_token,
    create_email_verification_token, verify_email_verification_token,
    
    # Authentication helpers
    create_user_tokens, refresh_access_token,
)


class TestCompleteAuthenticationFlow:
    """Integration tests for complete authentication flow."""
    
    def test_user_registration_and_login_flow(self):
        """Test complete user registration and login flow."""
        # Step 1: User Registration
        username = "testuser"
        email = "test@example.com"
        password = "SecurePassword123"
        
        # Validate password meets requirements
        validation = validate_password_strength(password)
        assert validation["valid"] is True, f"Password validation failed: {validation['errors']}"
        
        # Hash password for storage
        hashed_password = hash_password(password)
        assert hashed_password is not None
        assert hashed_password != password
        
        # Step 2: User Login
        login_password = "SecurePassword123"
        
        # Verify password
        password_valid = verify_password(login_password, hashed_password)
        assert password_valid is True, "Password verification failed during login"
        
        # Step 3: Create authentication tokens
        tokens = create_user_tokens(
            user_id="user_12345",
            username=username,
            email=email,
            role="user",
            permissions=["read_profile", "update_profile"],
            remember_me=False
        )
        
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert tokens["token_type"] == "bearer"
        assert "expires_in" in tokens
        
        # Step 4: Validate access token can be used for API calls
        access_payload = verify_token(tokens["access_token"], "access")
        assert access_payload["sub"] == "user_12345"
        assert access_payload["username"] == username
        assert access_payload["email"] == email
        
        # Step 5: Extract user information from token
        user_info = extract_user_info(tokens["access_token"])
        assert user_info["user_id"] == "user_12345"
        assert user_info["username"] == username
        assert user_info["email"] == email
        assert user_info["role"] == "user"
        assert user_info["permissions"] == ["read_profile", "update_profile"]
    
    def test_token_refresh_flow(self):
        """Test token refresh flow."""
        # Step 1: Create initial tokens
        user_data = {
            "user_id": "user_67890",
            "username": "refreshuser",
            "email": "refresh@example.com",
            "role": "admin",
            "permissions": ["read", "write", "admin"]
        }
        
        initial_tokens = create_user_tokens(
            user_id=user_data["user_id"],
            username=user_data["username"],
            email=user_data["email"],
            role=user_data["role"],
            permissions=user_data["permissions"],
            remember_me=True
        )
        
        # Step 2: Verify initial access token works
        initial_payload = verify_token(initial_tokens["access_token"], "access")
        assert initial_payload["sub"] == user_data["user_id"]
        
        # Step 3: Use refresh token to get new access token
        new_tokens = refresh_access_token(initial_tokens["refresh_token"])
        
        assert "access_token" in new_tokens
        assert new_tokens["token_type"] == "bearer"
        assert "expires_in" in new_tokens
        
        # Step 4: Verify new access token works and contains same user data
        new_payload = verify_token(new_tokens["access_token"], "access")
        assert new_payload["sub"] == user_data["user_id"]
        assert new_payload["username"] == user_data["username"]
        assert new_payload["role"] == user_data["role"]
        assert new_payload["permissions"] == user_data["permissions"]
        
        # Step 5: Verify tokens are different (new token was created)
        assert new_tokens["access_token"] != initial_tokens["access_token"]
    
    def test_remember_me_functionality(self):
        """Test remember me functionality with longer token expiry."""
        # Create tokens without remember me
        regular_tokens = create_user_tokens(
            user_id="user_111",
            username="regularuser",
            email="regular@example.com",
            remember_me=False
        )
        
        # Create tokens with remember me
        remember_tokens = create_user_tokens(
            user_id="user_222",
            username="rememberuser", 
            email="remember@example.com",
            remember_me=True
        )
        
        # Extract expiry information
        regular_payload = verify_token(regular_tokens["refresh_token"], "refresh")
        remember_payload = verify_token(remember_tokens["refresh_token"], "refresh")
        
        regular_expiry = datetime.fromtimestamp(regular_payload["exp"], timezone.utc)
        remember_expiry = datetime.fromtimestamp(remember_payload["exp"], timezone.utc)
        
        # Remember me token should have much longer expiry
        time_difference = remember_expiry - regular_expiry
        assert time_difference.days > 20, "Remember me token should have significantly longer expiry"
        
        # Verify remember_me flag is set correctly
        assert regular_payload["remember_me"] is False
        assert remember_payload["remember_me"] is True
    
    def test_login_failure_scenarios(self):
        """Test various login failure scenarios."""
        # Set up user with valid password
        correct_password = "CorrectPassword123"
        hashed_password = hash_password(correct_password)
        
        # Test wrong password
        wrong_password_valid = verify_password("WrongPassword123", hashed_password)
        assert wrong_password_valid is False, "Wrong password should not be accepted"
        
        # Test empty password
        empty_password_valid = verify_password("", hashed_password)
        assert empty_password_valid is False, "Empty password should not be accepted"
        
        # Test with invalid hash
        invalid_hash_valid = verify_password(correct_password, "invalid_hash")
        assert invalid_hash_valid is False, "Invalid hash should not validate"
    
    def test_token_expiry_scenarios(self):
        """Test token expiry scenarios."""
        # Create short-lived access token
        short_lived_data = {"sub": "user_333"}
        short_token = create_access_token(
            short_lived_data, 
            expires_delta=timedelta(seconds=1)
        )
        
        # Verify token is initially valid
        assert is_token_expired(short_token) is False
        
        # Wait for token to expire
        time.sleep(2)
        
        # Verify token is now expired
        assert is_token_expired(short_token) is True
        
        # Verify expired token cannot be verified
        with pytest.raises(TokenError, match="Token has expired"):
            verify_token(short_token, "access")


class TestPasswordResetFlow:
    """Integration tests for password reset flow."""
    
    def test_complete_password_reset_flow(self):
        """Test complete password reset flow."""
        user_id = "user_reset_123"
        user_email = "reset@example.com"
        old_password = "OldPassword123"
        new_password = "NewPassword456"
        
        # Step 1: Set up user with old password
        old_hashed = hash_password(old_password)
        
        # Verify old password works
        assert verify_password(old_password, old_hashed) is True
        
        # Step 2: User requests password reset
        reset_token = create_password_reset_token(user_id, expires_minutes=30)
        assert reset_token is not None
        
        # Step 3: Verify reset token is valid
        verified_user_id = verify_password_reset_token(reset_token)
        assert verified_user_id == user_id
        
        # Step 4: User provides new password
        # Validate new password meets requirements
        new_password_validation = validate_password_strength(new_password)
        assert new_password_validation["valid"] is True
        
        # Step 5: Hash new password and update
        new_hashed = hash_password(new_password)
        
        # Step 6: Verify old password no longer works
        assert verify_password(old_password, new_hashed) is False
        
        # Step 7: Verify new password works
        assert verify_password(new_password, new_hashed) is True
        
        # Step 8: Verify reset token can only be used once (in real implementation)
        # This would be handled by marking the token as used in database
        assert verify_password_reset_token(reset_token) == user_id  # Still valid in this test
    
    def test_password_reset_token_expiry(self):
        """Test that password reset tokens expire correctly."""
        user_id = "user_expire_test"
        
        # Create reset token with very short expiry
        short_reset_token = create_password_reset_token(
            user_id, 
            expires_minutes=0  # Expires immediately
        )
        
        # Small delay to ensure expiry
        time.sleep(1)
        
        # Token should be expired and verification should fail
        verified_user_id = verify_password_reset_token(short_reset_token)
        assert verified_user_id is None, "Expired reset token should not be valid"
    
    def test_password_reset_security(self):
        """Test password reset security features."""
        user_id = "user_security_test"
        
        # Create reset token
        reset_token = create_password_reset_token(user_id)
        
        # Verify that access tokens cannot be used as reset tokens
        access_token = create_access_token({"sub": user_id})
        assert verify_password_reset_token(access_token) is None
        
        # Verify that refresh tokens cannot be used as reset tokens
        refresh_token = create_refresh_token({"sub": user_id})
        assert verify_password_reset_token(refresh_token) is None
        
        # Verify that completely invalid tokens are rejected
        assert verify_password_reset_token("invalid.token") is None


class TestEmailVerificationFlow:
    """Integration tests for email verification flow."""
    
    def test_complete_email_verification_flow(self):
        """Test complete email verification flow."""
        user_id = "user_email_123"
        email = "verify@example.com"
        
        # Step 1: Create email verification token
        verification_token = create_email_verification_token(user_id, email)
        assert verification_token is not None
        
        # Step 2: Verify token contains correct information
        token_info = verify_email_verification_token(verification_token)
        assert token_info is not None
        assert token_info["user_id"] == user_id
        assert token_info["email"] == email
        
        # Step 3: Test that verification completes successfully
        # In real implementation, this would mark email as verified in database
        assert token_info["user_id"] == user_id
        assert token_info["email"] == email
    
    def test_email_verification_security(self):
        """Test email verification security features."""
        user_id = "user_email_security"
        email = "security@example.com"
        
        # Create verification token
        verification_token = create_email_verification_token(user_id, email)
        
        # Verify that other token types cannot be used for email verification
        access_token = create_access_token({"sub": user_id, "email": email})
        assert verify_email_verification_token(access_token) is None
        
        # Verify that invalid tokens are rejected
        assert verify_email_verification_token("invalid.token") is None


class TestMultiUserScenarios:
    """Integration tests for multi-user scenarios."""
    
    def test_multiple_users_different_tokens(self):
        """Test that different users get different tokens."""
        # Create tokens for multiple users
        user1_tokens = create_user_tokens(
            user_id="user_001",
            username="user1",
            email="user1@example.com"
        )
        
        user2_tokens = create_user_tokens(
            user_id="user_002", 
            username="user2",
            email="user2@example.com"
        )
        
        # Verify tokens are different
        assert user1_tokens["access_token"] != user2_tokens["access_token"]
        assert user1_tokens["refresh_token"] != user2_tokens["refresh_token"]
        
        # Verify each token contains correct user information
        user1_info = extract_user_info(user1_tokens["access_token"])
        user2_info = extract_user_info(user2_tokens["access_token"])
        
        assert user1_info["user_id"] == "user_001"
        assert user1_info["username"] == "user1"
        assert user2_info["user_id"] == "user_002"
        assert user2_info["username"] == "user2"
    
    def test_user_roles_and_permissions(self):
        """Test authentication with different user roles and permissions."""
        # Create admin user
        admin_tokens = create_user_tokens(
            user_id="admin_001",
            username="admin",
            email="admin@example.com",
            role="admin",
            permissions=["read", "write", "delete", "admin"],
            is_superuser=True
        )
        
        # Create regular user
        user_tokens = create_user_tokens(
            user_id="user_001",
            username="regularuser",
            email="user@example.com", 
            role="user",
            permissions=["read", "write"],
            is_superuser=False
        )
        
        # Verify admin token contains admin information
        admin_info = extract_user_info(admin_tokens["access_token"])
        assert admin_info["role"] == "admin"
        assert admin_info["is_superuser"] is True
        assert "admin" in admin_info["permissions"]
        
        # Verify regular user token contains user information
        user_info = extract_user_info(user_tokens["access_token"])
        assert user_info["role"] == "user"
        assert user_info["is_superuser"] is False
        assert "admin" not in user_info["permissions"]


class TestSecurityScenarios:
    """Integration tests for security scenarios."""
    
    def test_token_isolation(self):
        """Test that tokens are properly isolated."""
        user_id = "isolation_test"
        
        # Create different types of tokens
        access_token = create_access_token({"sub": user_id})
        refresh_token = create_refresh_token({"sub": user_id})
        reset_token = create_password_reset_token(user_id)
        
        # Verify each token can only be used for its intended purpose
        
        # Access token should only work as access token
        assert verify_token(access_token, "access")["sub"] == user_id
        with pytest.raises(TokenError):
            verify_token(access_token, "refresh")
        
        # Refresh token should only work as refresh token
        assert verify_token(refresh_token, "refresh")["sub"] == user_id
        with pytest.raises(TokenError):
            verify_token(refresh_token, "access")
        
        # Reset token should only work for password reset
        assert verify_password_reset_token(reset_token) == user_id
        assert verify_password_reset_token(access_token) is None
    
    def test_password_security_requirements(self):
        """Test that password security requirements are enforced."""
        # Test various password scenarios
        test_cases = [
            ("StrongPassword123", True),   # Valid password
            ("weak", False),               # Too short
            ("nouppercase123", False),     # No uppercase
            ("NOLOWERCASE123", False),     # No lowercase  
            ("NoDigitsHere", False),       # No digits
            ("", False),                   # Empty
        ]
        
        for password, should_be_valid in test_cases:
            if should_be_valid:
                # Should not raise exception
                hashed = hash_password(password)
                assert verify_password(password, hashed) is True
                
                validation = validate_password_strength(password)
                assert validation["valid"] is True
            else:
                if password:  # Non-empty passwords that are just weak
                    # Can still be hashed, but validation should fail
                    validation = validate_password_strength(password)
                    assert validation["valid"] is False
                    assert len(validation["errors"]) > 0
                else:  # Empty password
                    with pytest.raises(PasswordError):
                        hash_password(password)


class TestPerformanceScenarios:
    """Integration tests for performance scenarios."""
    
    def test_concurrent_token_operations(self):
        """Test multiple token operations in sequence."""
        import time
        
        start_time = time.time()
        
        # Perform multiple operations quickly
        for i in range(10):
            user_id = f"perf_user_{i}"
            
            # Create tokens
            tokens = create_user_tokens(
                user_id=user_id,
                username=f"user{i}",
                email=f"user{i}@example.com"
            )
            
            # Verify tokens
            verify_token(tokens["access_token"], "access")
            verify_token(tokens["refresh_token"], "refresh")
            
            # Refresh access token
            refresh_access_token(tokens["refresh_token"])
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should complete reasonably quickly (less than 5 seconds for 10 users)
        assert total_time < 5.0, f"Token operations took too long: {total_time} seconds"
    
    def test_password_hashing_performance(self):
        """Test password hashing performance."""
        import time
        
        passwords = [f"TestPassword{i}123" for i in range(5)]
        
        start_time = time.time()
        
        for password in passwords:
            hashed = hash_password(password)
            verify_password(password, hashed)
        
        end_time = time.time()
        total_time = end_time - start_time
        avg_time = total_time / len(passwords)
        
        # Each password hash should take reasonable time (less than 2 seconds)
        assert avg_time < 2.0, f"Password hashing too slow: {avg_time} seconds per password"


if __name__ == "__main__":
    # Run tests if script is executed directly
    pytest.main([__file__, "-v", "--tb=short"])
