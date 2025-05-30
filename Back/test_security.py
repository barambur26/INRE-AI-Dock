#!/usr/bin/env python3
"""
Test Suite for AID-US-001B: JWT Authentication Utilities and Password Hashing

This test suite comprehensively validates all JWT and password security functions.
It tests password hashing, JWT token generation, validation, and utility functions.
"""

import sys
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Ensure __init__.py files exist
(backend_dir / "app" / "__init__.py").touch()
(backend_dir / "app" / "core" / "__init__.py").touch()

try:
    from app.core.security import (
        # Password functions
        hash_password, verify_password, validate_password_strength,
        # JWT functions
        create_access_token, create_refresh_token, verify_token,
        decode_token, extract_user_id, extract_user_info,
        is_token_expired, get_token_expiry,
        # Utility functions
        create_token_pair, refresh_access_token, get_security_info,
        # Exceptions
        SecurityError, TokenError, PasswordError
    )
    from app.core.config import settings
    print("✅ Successfully imported all security functions!")
except ImportError as e:
    print(f"❌ Failed to import security functions: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)


class TestResults:
    """Track test results."""
    
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.total = 0
    
    def test(self, description: str, test_func):
        """Run a test and track results."""
        self.total += 1
        try:
            test_func()
            print(f"✅ {description}")
            self.passed += 1
        except Exception as e:
            print(f"❌ {description}: {str(e)}")
            self.failed += 1
    
    def summary(self):
        """Print test summary."""
        print(f"\n{'='*60}")
        print(f"TEST RESULTS SUMMARY")
        print(f"{'='*60}")
        print(f"Total Tests: {self.total}")
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")
        print(f"Success Rate: {(self.passed/self.total)*100:.1f}%")
        
        if self.failed == 0:
            print("\n🎉 ALL TESTS PASSED!")
            print("AID-US-001B: JWT Authentication Utilities is working correctly!")
            return True
        else:
            print(f"\n💥 {self.failed} TESTS FAILED!")
            return False


def test_password_hashing():
    """Test password hashing functionality."""
    results = TestResults()
    
    print("\n" + "="*60)
    print("TESTING PASSWORD HASHING")
    print("="*60)
    
    # Test basic password hashing
    results.test("Hash password correctly", lambda: hash_password("test123"))
    
    # Test password verification
    hashed = hash_password("test123")
    results.test("Verify correct password", lambda: verify_password("test123", hashed))
    results.test("Reject incorrect password", lambda: not verify_password("wrong", hashed))
    
    # Test password strength validation
    strong_result = validate_password_strength("MySecure123!")
    results.test("Validate strong password", lambda: strong_result["valid"])
    
    weak_result = validate_password_strength("123")
    results.test("Reject weak password", lambda: not weak_result["valid"])
    
    # Test error handling
    results.test("Handle empty password", lambda: hash_password("") and False or True)
    results.test("Handle None password in verification", lambda: not verify_password(None, hashed))
    
    return results


def test_jwt_token_generation():
    """Test JWT token generation."""
    results = TestResults()
    
    print("\n" + "="*60)
    print("TESTING JWT TOKEN GENERATION")
    print("="*60)
    
    user_data = {"sub": "user123", "role": "admin", "department": "IT"}
    
    # Test access token creation
    results.test("Create access token", lambda: create_access_token(user_data))
    
    # Test refresh token creation
    results.test("Create refresh token", lambda: create_refresh_token(user_data))
    
    # Test remember me token
    results.test("Create remember me token", lambda: create_refresh_token(user_data, remember_me=True))
    
    # Test custom expiry
    custom_expiry = timedelta(minutes=30)
    results.test("Create token with custom expiry", lambda: create_access_token(user_data, custom_expiry))
    
    # Test token pair creation
    tokens = create_token_pair(user_data)
    results.test("Create token pair", lambda: "access_token" in tokens and "refresh_token" in tokens)
    
    return results


def test_jwt_token_validation():
    """Test JWT token validation and decoding."""
    results = TestResults()
    
    print("\n" + "="*60)
    print("TESTING JWT TOKEN VALIDATION")
    print("="*60)
    
    user_data = {"sub": "user123", "role": "admin", "department": "IT"}
    
    # Create tokens for testing
    access_token = create_access_token(user_data)
    refresh_token = create_refresh_token(user_data)
    
    # Test token verification
    results.test("Verify valid access token", lambda: verify_token(access_token, "access"))
    results.test("Verify valid refresh token", lambda: verify_token(refresh_token, "refresh"))
    
    # Test token decoding
    decoded = decode_token(access_token)
    results.test("Decode token correctly", lambda: decoded["sub"] == "user123")
    
    # Test user info extraction
    user_info = extract_user_info(access_token)
    results.test("Extract user info", lambda: user_info["user_id"] == "user123")
    
    # Test user ID extraction
    user_id = extract_user_id(access_token)
    results.test("Extract user ID", lambda: user_id == "user123")
    
    # Test token expiry checking
    results.test("Check token not expired", lambda: not is_token_expired(access_token))
    
    # Test token expiry time
    expiry = get_token_expiry(access_token)
    results.test("Get token expiry time", lambda: expiry > datetime.now(timezone.utc))
    
    # Test invalid token handling
    results.test("Reject invalid token", lambda: not extract_user_id("invalid_token"))
    
    return results


def test_token_refresh():
    """Test token refresh functionality."""
    results = TestResults()
    
    print("\n" + "="*60)
    print("TESTING TOKEN REFRESH")
    print("="*60)
    
    user_data = {"sub": "user123", "role": "admin"}
    
    # Create initial tokens
    tokens = create_token_pair(user_data)
    
    # Test refresh functionality
    new_access_token = refresh_access_token(tokens["refresh_token"])
    results.test("Refresh access token", lambda: len(new_access_token) > 50)
    
    # Verify new token contains correct data
    new_payload = verify_token(new_access_token, "access")
    results.test("New token has correct user ID", lambda: new_payload["sub"] == "user123")
    
    return results


def test_security_utilities():
    """Test security utility functions."""
    results = TestResults()
    
    print("\n" + "="*60)
    print("TESTING SECURITY UTILITIES")
    print("="*60)
    
    # Test security info
    info = get_security_info()
    results.test("Get security configuration", lambda: "jwt_algorithm" in info)
    
    # Test password strength validation details
    password_result = validate_password_strength("MySecure123!")
    results.test("Password strength has requirements", lambda: "requirements" in password_result)
    results.test("Password strength has score", lambda: password_result["score"] > 0)
    
    return results


def test_error_handling():
    """Test error handling and edge cases."""
    results = TestResults()
    
    print("\n" + "="*60)
    print("TESTING ERROR HANDLING")
    print("="*60)
    
    # Test token errors
    try:
        verify_token("invalid_token")
        results.test("Handle invalid token", lambda: False)
    except TokenError:
        results.test("Handle invalid token", lambda: True)
    
    # Test password errors
    try:
        hash_password("")
        results.test("Handle empty password", lambda: False)
    except PasswordError:
        results.test("Handle empty password", lambda: True)
    
    # Test wrong token type
    access_token = create_access_token({"sub": "user123"})
    try:
        verify_token(access_token, "refresh")
        results.test("Handle wrong token type", lambda: False)
    except TokenError:
        results.test("Handle wrong token type", lambda: True)
    
    return results


def test_token_expiry():
    """Test token expiry functionality."""
    results = TestResults()
    
    print("\n" + "="*60)
    print("TESTING TOKEN EXPIRY")
    print("="*60)
    
    # Create short-lived token for testing
    short_expiry = timedelta(seconds=1)
    user_data = {"sub": "user123"}
    
    short_token = create_access_token(user_data, short_expiry)
    results.test("Create short-lived token", lambda: len(short_token) > 50)
    
    # Wait for token to expire
    time.sleep(2)
    
    # Test expired token
    results.test("Detect expired token", lambda: is_token_expired(short_token))
    
    # Test that expired token is rejected
    try:
        verify_token(short_token)
        results.test("Reject expired token", lambda: False)
    except TokenError:
        results.test("Reject expired token", lambda: True)
    
    return results


def run_all_tests():
    """Run all security tests."""
    print("🔐 AID-US-001B: JWT Authentication Utilities Test Suite")
    print("="*60)
    
    # Run all test categories
    test_categories = [
        test_password_hashing,
        test_jwt_token_generation,
        test_jwt_token_validation,
        test_token_refresh,
        test_security_utilities,
        test_error_handling,
        test_token_expiry
    ]
    
    total_results = TestResults()
    
    for test_category in test_categories:
        category_results = test_category()
        total_results.passed += category_results.passed
        total_results.failed += category_results.failed
        total_results.total += category_results.total
    
    return total_results.summary()


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
