#!/usr/bin/env python3
"""
Comprehensive test suite for AID-US-001B: JWT Authentication Utilities

This script tests all JWT and password hashing functionality without requiring a database.
"""

import sys
import traceback
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Test results tracking
TESTS_PASSED = 0
TESTS_FAILED = 0
TOTAL_TESTS = 0

def test_assert(description: str, condition: bool) -> None:
    """Assert a test condition and track results."""
    global TESTS_PASSED, TESTS_FAILED, TOTAL_TESTS
    TOTAL_TESTS += 1
    
    if condition:
        print(f"✅ {description}")
        TESTS_PASSED += 1
    else:
        print(f"❌ {description}")
        TESTS_FAILED += 1

def test_exception(description: str, func, expected_exception=None) -> None:
    """Test that a function raises an expected exception."""
    global TESTS_PASSED, TESTS_FAILED, TOTAL_TESTS
    TOTAL_TESTS += 1
    
    try:
        func()
        print(f"❌ {description} (Expected exception but none was raised)")
        TESTS_FAILED += 1
    except Exception as e:
        if expected_exception and isinstance(e, expected_exception):
            print(f"✅ {description}")
            TESTS_PASSED += 1
        elif expected_exception:
            print(f"❌ {description} (Expected {expected_exception.__name__}, got {type(e).__name__})")
            TESTS_FAILED += 1
        else:
            print(f"✅ {description}")
            TESTS_PASSED += 1

def main():
    print("🔐 AID-US-001B: JWT Authentication Utilities Test Suite")
    print("=" * 60)
    
    try:
        # Import security module
        from app.core.security import (
            hash_password, verify_password, create_access_token, create_refresh_token,
            parse_token, validate_token, get_token_subject, is_token_expired,
            get_token_expiration, generate_secure_secret, generate_jwt_secret,
            create_password_reset_token, validate_password_reset_token,
            blacklist_token, is_token_blacklisted, clear_blacklist,
            create_token_pair, refresh_access_token, create_test_tokens,
            InvalidTokenError, TokenExpiredError
        )
        print("✅ Security module imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import security module: {e}")
        return False
    
    print("\n" + "="*60)
    print("🔒 TESTING PASSWORD HASHING")
    print("="*60)
    
    # Test password hashing
    test_password = "test_password_123!@#"
    hashed_password = hash_password(test_password)
    
    test_assert("Password can be hashed", len(hashed_password) > 50)
    test_assert("Password verification works (correct password)", 
                verify_password(test_password, hashed_password))
    test_assert("Password verification works (incorrect password)", 
                not verify_password("wrong_password", hashed_password))
    test_assert("Empty password verification fails", 
                not verify_password("", hashed_password))
    test_assert("Password verification with empty hash fails", 
                not verify_password(test_password, ""))
    
    # Test password edge cases
    test_exception("Empty password hashing raises ValueError", 
                   lambda: hash_password(""), ValueError)
    
    print(f"\n📊 Password hashing tests: {TESTS_PASSED - (TOTAL_TESTS - 6)}/6 passed")
    
    print("\n" + "="*60)
    print("🎫 TESTING JWT ACCESS TOKENS")
    print("="*60)
    
    # Test access token creation
    user_id = "test_user_123"
    access_token = create_access_token(user_id)
    
    test_assert("Access token can be created", len(access_token) > 100)
    test_assert("Access token subject can be extracted", 
                get_token_subject(access_token) == user_id)
    test_assert("Access token is not expired", not is_token_expired(access_token))
    
    # Test token parsing
    claims = parse_token(access_token)
    test_assert("Token claims contain subject", claims.get("sub") == user_id)
    test_assert("Token claims contain type", claims.get("type") == "access")
    test_assert("Token claims contain expiration", "exp" in claims)
    test_assert("Token claims contain issued at", "iat" in claims)
    
    # Test token validation
    validated_claims = validate_token(access_token, "access")
    test_assert("Token validation returns claims", validated_claims.get("sub") == user_id)
    
    # Test custom expiration
    short_token = create_access_token(user_id, expires_delta=timedelta(seconds=1))
    test_assert("Custom expiration token created", len(short_token) > 100)
    
    # Wait for token to expire (in real scenario, we'd mock time)
    import time
    time.sleep(1.1)
    test_assert("Short-lived token expires", is_token_expired(short_token))
    
    print(f"\n📊 Access token tests: {TESTS_PASSED - (TOTAL_TESTS - 9)}/9 passed")
    
    print("\n" + "="*60)
    print("🔄 TESTING JWT REFRESH TOKENS") 
    print("="*60)
    
    # Test refresh token creation
    refresh_token = create_refresh_token(user_id, remember_me=False)
    remember_token = create_refresh_token(user_id, remember_me=True)
    
    test_assert("Refresh token can be created", len(refresh_token) > 100)
    test_assert("Remember me token can be created", len(remember_token) > 100)
    
    # Test refresh token claims
    refresh_claims = parse_token(refresh_token)
    remember_claims = parse_token(remember_token)
    
    test_assert("Refresh token has correct type", refresh_claims.get("type") == "refresh")
    test_assert("Refresh token has remember_me flag", refresh_claims.get("remember_me") is False)
    test_assert("Remember token has remember_me flag", remember_claims.get("remember_me") is True)
    
    # Test token type validation
    test_exception("Wrong token type validation fails",
                   lambda: validate_token(refresh_token, "access"), InvalidTokenError)
    
    print(f"\n📊 Refresh token tests: {TESTS_PASSED - (TOTAL_TESTS - 5)}/5 passed")
    
    print("\n" + "="*60)
    print("🔐 TESTING TOKEN UTILITIES")
    print("="*60)
    
    # Test token expiration checking
    exp_time = get_token_expiration(access_token)
    test_assert("Token expiration can be extracted", 
                exp_time and exp_time > datetime.now(timezone.utc))
    
    # Test secure secret generation
    secret1 = generate_secure_secret()
    secret2 = generate_secure_secret()
    jwt_secret = generate_jwt_secret()
    
    test_assert("Secure secrets are generated", len(secret1) > 40)
    test_assert("Secure secrets are unique", secret1 != secret2)
    test_assert("JWT secret is long enough", len(jwt_secret) > 80)
    
    # Test password reset tokens
    reset_token = create_password_reset_token(user_id)
    reset_user_id = validate_password_reset_token(reset_token)
    
    test_assert("Password reset token created", len(reset_token) > 100)
    test_assert("Password reset token validated", reset_user_id == user_id)
    
    # Test token blacklisting
    clear_blacklist()  # Start clean
    test_assert("Token not initially blacklisted", not is_token_blacklisted(access_token))
    
    blacklist_token(access_token)
    test_assert("Token can be blacklisted", is_token_blacklisted(access_token))
    
    print(f"\n📊 Token utility tests: {TESTS_PASSED - (TOTAL_TESTS - 8)}/8 passed")
    
    print("\n" + "="*60)
    print("🎯 TESTING CONVENIENCE FUNCTIONS")
    print("="*60)
    
    # Test token pair creation
    token_pair = create_token_pair(user_id, remember_me=True)
    
    test_assert("Token pair contains access token", "access_token" in token_pair)
    test_assert("Token pair contains refresh token", "refresh_token" in token_pair)
    test_assert("Token pair contains token type", token_pair.get("token_type") == "bearer")
    test_assert("Access token subject matches", 
                get_token_subject(token_pair["access_token"]) == user_id)
    test_assert("Refresh token subject matches", 
                get_token_subject(token_pair["refresh_token"]) == user_id)
    
    # Test token refresh
    clear_blacklist()  # Clear blacklist for clean test
    new_access = refresh_access_token(token_pair["refresh_token"])
    test_assert("New access token created from refresh", len(new_access) > 100)
    test_assert("New access token has correct subject", 
                get_token_subject(new_access) == user_id)
    
    # Test test token creation
    test_tokens = create_test_tokens("test_user")
    test_assert("Test tokens created", len(test_tokens) == 3)  # access, refresh, token_type
    
    # Test refresh with blacklisted token
    blacklist_token(token_pair["refresh_token"])
    test_exception("Blacklisted refresh token fails",
                   lambda: refresh_access_token(token_pair["refresh_token"]), InvalidTokenError)
    
    print(f"\n📊 Convenience function tests: {TESTS_PASSED - (TOTAL_TESTS - 9)}/9 passed")
    
    print("\n" + "="*60)
    print("⚠️  TESTING ERROR HANDLING")
    print("="*60)
    
    # Test invalid tokens
    test_exception("Invalid token raises error", 
                   lambda: parse_token("invalid.token.here"), InvalidTokenError)
    test_exception("Empty token raises error", 
                   lambda: parse_token(""), InvalidTokenError)  
    test_exception("Wrong algorithm token raises error",
                   lambda: parse_token("eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiYWRtaW4iOnRydWV9.TJVA95OrM7E2cBab30RMHrHDcEfxjoYZgeFONFh7HgQ"), 
                   InvalidTokenError)
    
    # Test wrong password reset token
    test_exception("Wrong token type for password reset",
                   lambda: validate_password_reset_token(access_token), InvalidTokenError)
    
    print(f"\n📊 Error handling tests: {TESTS_PASSED - (TOTAL_TESTS - 4)}/4 passed")
    
    print("\n" + "="*60)
    print("🧪 TESTING INTEGRATION SCENARIOS")
    print("="*60)
    
    # Test complete authentication flow
    password = "user_secure_password_123"
    hashed = hash_password(password)
    
    # Login simulation
    if verify_password(password, hashed):
        tokens = create_token_pair("integration_user", remember_me=True)
        test_assert("Login flow: tokens created", len(tokens) == 3)
        
        # API request simulation
        try:
            claims = validate_token(tokens["access_token"], "access")
            test_assert("API request: access token validated", claims["sub"] == "integration_user")
        except InvalidTokenError:
            test_assert("API request: access token validation failed", False)
        
        # Token refresh simulation
        try:
            new_access = refresh_access_token(tokens["refresh_token"])
            test_assert("Token refresh: new access token created", len(new_access) > 100)
        except InvalidTokenError:
            test_assert("Token refresh: failed", False)
        
        # Logout simulation
        blacklist_token(tokens["access_token"])
        blacklist_token(tokens["refresh_token"])
        test_assert("Logout: tokens blacklisted", 
                    is_token_blacklisted(tokens["access_token"]) and 
                    is_token_blacklisted(tokens["refresh_token"]))
    
    print(f"\n📊 Integration tests: {TESTS_PASSED - (TOTAL_TESTS - 5)}/5 passed")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        
        print("\n" + "="*60)
        print("📊 FINAL TEST RESULTS")
        print("="*60)
        print(f"Total Tests: {TOTAL_TESTS}")
        print(f"✅ Passed: {TESTS_PASSED}")
        print(f"❌ Failed: {TESTS_FAILED}")
        print(f"Success Rate: {(TESTS_PASSED/TOTAL_TESTS)*100:.1f}%")
        
        if TESTS_FAILED == 0:
            print("\n🎉 ALL TESTS PASSED!")
            print("✅ JWT Authentication Utilities are working correctly!")
            print("\n🚀 Ready for next steps:")
            print("   1. AID-US-001C: Authentication API Endpoints")
            print("   2. AID-US-001D: Frontend Authentication Integration")
            print("   3. Update backlog with completion status")
            sys.exit(0)
        else:
            print(f"\n💥 {TESTS_FAILED} TESTS FAILED!")
            print("Please review the failed tests above.")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n💥 Test suite crashed: {e}")
        traceback.print_exc()
        sys.exit(1)
