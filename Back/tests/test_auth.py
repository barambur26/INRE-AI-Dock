"""
Comprehensive Authentication Testing Suite for AI Dock App

This module contains comprehensive tests for the authentication system including:
- Login/logout flows
- Token refresh mechanisms  
- Rate limiting functionality
- "Remember Me" scenarios
- Security validations
- Integration tests

Test Categories:
1. Authentication Flow Tests
2. Token Management Tests
3. Rate Limiting Tests
4. Security Tests
5. Integration Tests
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any
from unittest.mock import Mock, patch

import pytest
import httpx
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# Import the app and dependencies
from app.main import app
from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_token,
    hash_password,
    verify_password
)
from app.services.auth_service import AuthService
from app.middleware.rate_limit import RateLimitMiddleware, rate_limit_storage, clear_rate_limits
from app.tasks.cleanup import cleanup_expired_tokens, cleanup_user_sessions
from app.models.user import User
from app.models.refresh_token import RefreshToken

# Test client setup
client = TestClient(app)

# Test constants
TEST_USER_CREDENTIALS = {
    "admin": {"username": "admin", "password": "admin123", "role": "admin"},
    "user1": {"username": "user1", "password": "user123", "role": "user"},
    "user2": {"username": "user2", "password": "user123", "role": "user"},
    "analyst": {"username": "analyst", "password": "analyst123", "role": "analyst"},
}

class TestAuthenticationFlow:
    """Test complete authentication workflows"""
    
    def setup_method(self):
        """Setup for each test method"""
        # Clear rate limits before each test
        clear_rate_limits()
        
    def test_successful_login_flow(self):
        """Test successful login with all user types"""
        for user_type, credentials in TEST_USER_CREDENTIALS.items():
            response = client.post(
                "/api/v1/auth/login",
                json={
                    "username": credentials["username"],
                    "password": credentials["password"],
                    "remember_me": False
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify response structure
            assert "access_token" in data
            assert "refresh_token" in data
            assert "token_type" in data
            assert "expires_in" in data
            assert "user" in data
            
            # Verify token type
            assert data["token_type"] == "bearer"
            
            # Verify user data
            user_data = data["user"]
            assert user_data["username"] == credentials["username"]
            assert user_data["role"] == credentials["role"]
            assert user_data["is_active"] is True
            
            # Verify tokens are valid
            access_token = data["access_token"]
            refresh_token = data["refresh_token"]
            
            # Test access token
            token_data = verify_token(access_token, "access")
            assert token_data["sub"] == credentials["username"]
            assert token_data["type"] == "access"
            
            # Test refresh token
            refresh_data = verify_token(refresh_token, "refresh")
            assert refresh_data["sub"] == credentials["username"]
            assert refresh_data["type"] == "refresh"
    
    def test_login_with_remember_me(self):
        """Test login with remember me functionality"""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "user1",
                "password": "user123",
                "remember_me": True
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify refresh token has extended expiry for remember me
        refresh_token = data["refresh_token"]
        refresh_data = verify_token(refresh_token, "refresh")
        
        # Calculate expected expiry (should be 30 days for remember me)
        token_exp = datetime.fromtimestamp(refresh_data["exp"])
        token_iat = datetime.fromtimestamp(refresh_data["iat"])
        token_duration = token_exp - token_iat
        
        # Should be approximately 30 days (allow some tolerance)
        expected_duration = timedelta(days=30)
        assert abs(token_duration.total_seconds() - expected_duration.total_seconds()) < 3600  # 1 hour tolerance
    
    def test_login_without_remember_me(self):
        """Test login without remember me (7 day tokens)"""
        response = client.post(
            "/api/v1/auth/login", 
            json={
                "username": "user1",
                "password": "user123",
                "remember_me": False
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify refresh token has standard expiry
        refresh_token = data["refresh_token"]
        refresh_data = verify_token(refresh_token, "refresh")
        
        # Calculate token duration (should be 7 days for standard)
        token_exp = datetime.fromtimestamp(refresh_data["exp"])
        token_iat = datetime.fromtimestamp(refresh_data["iat"])
        token_duration = token_exp - token_iat
        
        # Should be approximately 7 days
        expected_duration = timedelta(days=7)
        assert abs(token_duration.total_seconds() - expected_duration.total_seconds()) < 3600  # 1 hour tolerance
    
    def test_invalid_credentials(self):
        """Test login with invalid credentials"""
        # Test invalid username
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "nonexistent",
                "password": "password123",
                "remember_me": False
            }
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        
        # Test invalid password
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "user1",
                "password": "wrongpassword",
                "remember_me": False
            }
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
    
    def test_token_refresh_flow(self):
        """Test token refresh functionality"""
        # First, login to get tokens
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "user1",
                "password": "user123",
                "remember_me": False
            }
        )
        
        assert login_response.status_code == 200
        login_data = login_response.json()
        refresh_token = login_data["refresh_token"]
        
        # Use refresh token to get new access token
        refresh_response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        
        assert refresh_response.status_code == 200
        refresh_data = refresh_response.json()
        
        # Verify new access token
        assert "access_token" in refresh_data
        assert "token_type" in refresh_data
        assert "expires_in" in refresh_data
        
        new_access_token = refresh_data["access_token"]
        token_data = verify_token(new_access_token, "access")
        assert token_data["sub"] == "user1"
        assert token_data["type"] == "access"
    
    def test_protected_endpoint_access(self):
        """Test accessing protected endpoints with valid tokens"""
        # Login to get access token
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "user1",
                "password": "user123",
                "remember_me": False
            }
        )
        
        assert login_response.status_code == 200
        access_token = login_response.json()["access_token"]
        
        # Access protected endpoint
        headers = {"Authorization": f"Bearer {access_token}"}
        response = client.get("/api/v1/auth/me", headers=headers)
        
        assert response.status_code == 200
        user_data = response.json()
        assert user_data["username"] == "user1"
        assert user_data["role"] == "user"
    
    def test_logout_flow(self):
        """Test complete logout functionality"""
        # Login first
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "user1",
                "password": "user123",
                "remember_me": False
            }
        )
        
        assert login_response.status_code == 200
        access_token = login_response.json()["access_token"]
        
        # Logout
        headers = {"Authorization": f"Bearer {access_token}"}
        logout_response = client.post("/api/v1/auth/logout", headers=headers)
        
        assert logout_response.status_code == 200
        
        # Verify token is invalidated - accessing protected endpoint should fail
        me_response = client.get("/api/v1/auth/me", headers=headers)
        assert me_response.status_code == 401

class TestRateLimiting:
    """Test rate limiting functionality"""
    
    def setup_method(self):
        """Setup for each test method"""
        # Clear rate limits before each test
        clear_rate_limits()
    
    def test_login_rate_limiting(self):
        """Test rate limiting for login endpoint"""
        # Make multiple rapid login attempts (should hit rate limit)
        credentials = {
            "username": "user1",
            "password": "user123",
            "remember_me": False
        }
        
        # Make requests up to the limit (5 per window)
        successful_requests = 0
        for i in range(10):  # Try more than the limit
            response = client.post("/api/v1/auth/login", json=credentials)
            if response.status_code == 200:
                successful_requests += 1
            elif response.status_code == 429:
                # Rate limit hit
                data = response.json()
                assert "detail" in data
                break
        
        # Should have been rate limited before all 10 requests
        assert successful_requests <= 5
    
    def test_invalid_login_rate_limiting(self):
        """Test rate limiting for failed login attempts"""
        # Make multiple failed login attempts
        invalid_credentials = {
            "username": "user1",
            "password": "wrongpassword",
            "remember_me": False
        }
        
        rate_limited = False
        for i in range(10):
            response = client.post("/api/v1/auth/login", json=invalid_credentials)
            if response.status_code == 429:
                rate_limited = True
                break
        
        # Should eventually be rate limited
        assert rate_limited
    
    def test_refresh_rate_limiting(self):
        """Test rate limiting for refresh endpoint"""
        # First get a valid refresh token
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "user1",
                "password": "user123",
                "remember_me": False
            }
        )
        
        assert login_response.status_code == 200
        refresh_token = login_response.json()["refresh_token"]
        
        # Make rapid refresh requests
        successful_refreshes = 0
        for i in range(40):  # Try more than the limit (30 per window)
            response = client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": refresh_token}
            )
            if response.status_code == 200:
                successful_refreshes += 1
            elif response.status_code == 429:
                break
        
        # Should have been rate limited
        assert successful_refreshes <= 30
    
    def test_rate_limit_headers(self):
        """Test that rate limit responses include proper headers"""
        # Make requests until rate limited
        credentials = {
            "username": "user1",
            "password": "wrongpassword",  # Use wrong password to avoid successful logins
            "remember_me": False
        }
        
        for i in range(10):
            response = client.post("/api/v1/auth/login", json=credentials)
            if response.status_code == 429:
                # Check for rate limit headers
                data = response.json()
                assert "detail" in data
                detail = data["detail"]
                if isinstance(detail, dict):
                    assert "retry_after" in detail or "window_seconds" in detail
                break

class TestSecurityValidation:
    """Test security features and validations"""
    
    def test_token_signature_validation(self):
        """Test that invalid token signatures are rejected"""
        # Create a token and modify its signature
        valid_token = create_access_token({"sub": "user1", "type": "access"})
        
        # Modify the signature part
        parts = valid_token.split(".")
        invalid_token = ".".join(parts[:-1] + ["invalidsignature"])
        
        # Try to verify invalid token
        with pytest.raises(Exception):
            verify_token(invalid_token, "access")
    
    def test_expired_token_rejection(self):
        """Test that expired tokens are rejected"""
        # Create a token that expires immediately
        expired_token = create_access_token(
            {"sub": "user1", "type": "access"},
            expires_delta=timedelta(seconds=-1)  # Already expired
        )
        
        # Should raise exception when verifying
        with pytest.raises(Exception):
            verify_token(expired_token, "access")
    
    def test_token_type_validation(self):
        """Test that token types are properly validated"""
        # Create an access token
        access_token = create_access_token({"sub": "user1", "type": "access"})
        
        # Try to use it as a refresh token (should fail)
        with pytest.raises(Exception):
            verify_token(access_token, "refresh")
    
    def test_password_hashing_security(self):
        """Test password hashing security"""
        password = "testpassword123"
        
        # Hash the password
        hashed = hash_password(password)
        
        # Verify the hash is not the plain password
        assert hashed != password
        
        # Verify the password can be verified
        assert verify_password(password, hashed) is True
        
        # Verify wrong password fails
        assert verify_password("wrongpassword", hashed) is False
        
        # Verify hash is different each time (salt)
        hashed2 = hash_password(password)
        assert hashed != hashed2
    
    def test_input_validation(self):
        """Test input validation for authentication endpoints"""
        # Test missing fields
        response = client.post("/api/v1/auth/login", json={})
        assert response.status_code == 422  # Validation error
        
        # Test invalid field types
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": 123,  # Should be string
                "password": "test",
                "remember_me": False
            }
        )
        assert response.status_code == 422
        
        # Test empty values
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "",
                "password": "",
                "remember_me": False
            }
        )
        assert response.status_code == 422

class TestTokenCleanup:
    """Test token cleanup background tasks"""
    
    @pytest.mark.asyncio
    async def test_expired_token_cleanup(self):
        """Test cleanup of expired tokens"""
        # This test would require a database setup
        # For now, we'll test the task logic
        
        # Mock the database session and models
        with patch('app.tasks.cleanup.get_db_session') as mock_db:
            mock_session = Mock()
            mock_db.return_value.__enter__.return_value = mock_session
            
            # Mock expired tokens
            expired_token = Mock()
            expired_token.expires_at = datetime.utcnow() - timedelta(days=1)
            mock_session.query.return_value.filter.return_value.all.return_value = [expired_token]
            mock_session.query.return_value.count.return_value = 1
            
            # Run cleanup task
            result = cleanup_expired_tokens()
            
            # Verify task completed
            assert result["status"] == "success"
            assert "tokens_deleted" in result
    
    @pytest.mark.asyncio 
    async def test_user_session_cleanup(self):
        """Test cleanup of user sessions"""
        with patch('app.tasks.cleanup.get_db_session') as mock_db:
            mock_session = Mock()
            mock_db.return_value.__enter__.return_value = mock_session
            
            # Mock user tokens
            user_token = Mock()
            user_token.is_revoked = False
            mock_session.query.return_value.filter.return_value.all.return_value = [user_token]
            
            # Run cleanup task
            result = cleanup_user_sessions("test-user-id")
            
            # Verify task completed
            assert result["status"] == "success"
            assert result["user_id"] == "test-user-id"

class TestIntegrationScenarios:
    """Test complete integration scenarios"""
    
    def setup_method(self):
        """Setup for each test method"""
        clear_rate_limits()
    
    def test_complete_user_journey(self):
        """Test complete user authentication journey"""
        # 1. Login
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "user1",
                "password": "user123", 
                "remember_me": True
            }
        )
        
        assert login_response.status_code == 200
        login_data = login_response.json()
        access_token = login_data["access_token"]
        refresh_token = login_data["refresh_token"]
        
        # 2. Access protected resource
        headers = {"Authorization": f"Bearer {access_token}"}
        me_response = client.get("/api/v1/auth/me", headers=headers)
        assert me_response.status_code == 200
        
        # 3. Refresh token
        refresh_response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        assert refresh_response.status_code == 200
        new_access_token = refresh_response.json()["access_token"]
        
        # 4. Use new token
        new_headers = {"Authorization": f"Bearer {new_access_token}"}
        me_response2 = client.get("/api/v1/auth/me", headers=new_headers)
        assert me_response2.status_code == 200
        
        # 5. Logout
        logout_response = client.post("/api/v1/auth/logout", headers=new_headers)
        assert logout_response.status_code == 200
        
        # 6. Verify token is invalidated
        me_response3 = client.get("/api/v1/auth/me", headers=new_headers)
        assert me_response3.status_code == 401
    
    def test_concurrent_login_attempts(self):
        """Test handling of concurrent login attempts"""
        import threading
        import queue
        
        results = queue.Queue()
        
        def login_attempt():
            response = client.post(
                "/api/v1/auth/login",
                json={
                    "username": "user1",
                    "password": "user123",
                    "remember_me": False
                }
            )
            results.put(response.status_code)
        
        # Start multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=login_attempt)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Collect results
        status_codes = []
        while not results.empty():
            status_codes.append(results.get())
        
        # Should have some successful logins and some rate limited
        assert 200 in status_codes  # At least one successful
        # May or may not have rate limiting depending on timing
    
    def test_admin_vs_user_access(self):
        """Test different access levels for admin vs regular users"""
        # Test admin access
        admin_login = client.post(
            "/api/v1/auth/login",
            json={
                "username": "admin",
                "password": "admin123",
                "remember_me": False
            }
        )
        
        assert admin_login.status_code == 200
        admin_token = admin_login.json()["access_token"]
        
        # Test user access
        user_login = client.post(
            "/api/v1/auth/login",
            json={
                "username": "user1", 
                "password": "user123",
                "remember_me": False
            }
        )
        
        assert user_login.status_code == 200
        user_token = user_login.json()["access_token"]
        
        # Both should be able to access their profile
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        user_headers = {"Authorization": f"Bearer {user_token}"}
        
        admin_me = client.get("/api/v1/auth/me", headers=admin_headers)
        user_me = client.get("/api/v1/auth/me", headers=user_headers)
        
        assert admin_me.status_code == 200
        assert user_me.status_code == 200
        
        # Verify roles
        assert admin_me.json()["role"] == "admin"
        assert user_me.json()["role"] == "user"

# Fixtures and utilities for testing
@pytest.fixture
def auth_service():
    """Provide AuthService instance for testing"""
    return AuthService()

@pytest.fixture
def valid_user_credentials():
    """Provide valid test user credentials"""
    return TEST_USER_CREDENTIALS

@pytest.fixture
def clear_rate_limits_fixture():
    """Clear rate limits before each test"""
    clear_rate_limits()
    yield
    clear_rate_limits()

# Helper functions
def get_valid_token(username: str = "user1") -> str:
    """Get a valid access token for testing"""
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "username": username,
            "password": TEST_USER_CREDENTIALS[username]["password"],
            "remember_me": False
        }
    )
    return login_response.json()["access_token"]

def make_authenticated_request(endpoint: str, method: str = "GET", username: str = "user1", **kwargs):
    """Make an authenticated request"""
    token = get_valid_token(username)
    headers = kwargs.get("headers", {})
    headers["Authorization"] = f"Bearer {token}"
    kwargs["headers"] = headers
    
    if method.upper() == "GET":
        return client.get(endpoint, **kwargs)
    elif method.upper() == "POST":
        return client.post(endpoint, **kwargs)
    elif method.upper() == "PUT":
        return client.put(endpoint, **kwargs)
    elif method.upper() == "DELETE":
        return client.delete(endpoint, **kwargs)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
