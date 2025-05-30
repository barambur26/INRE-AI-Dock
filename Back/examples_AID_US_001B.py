"""
Usage Examples for AID-US-001B: JWT Authentication Utilities & Password Hashing

This file demonstrates how to use the security utilities in practice.
These examples show common authentication patterns and use cases.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.core.security import (
    # Password functions
    hash_password, verify_password, validate_password_strength,
    
    # JWT functions
    create_access_token, create_refresh_token, verify_token,
    extract_user_info, is_token_expired,
    
    # Security utilities
    generate_secure_token, create_password_reset_token, verify_password_reset_token,
    
    # Authentication helpers
    create_user_tokens, refresh_access_token,
    
    # Exceptions
    PasswordError, TokenError
)


def example_password_operations():
    """Demonstrate password hashing and validation."""
    print("=" * 60)
    print("PASSWORD OPERATIONS EXAMPLES")
    print("=" * 60)
    
    # Example 1: Hash and verify password
    print("\n1. Password Hashing and Verification")
    print("-" * 40)
    
    password = "UserPassword123"
    print(f"Original password: {password}")
    
    # Hash the password
    hashed = hash_password(password)
    print(f"Hashed password: {hashed[:30]}...")
    
    # Verify correct password
    is_valid = verify_password(password, hashed)
    print(f"Correct password verification: {is_valid}")
    
    # Verify incorrect password
    is_invalid = verify_password("WrongPassword", hashed)
    print(f"Incorrect password verification: {is_invalid}")
    
    # Example 2: Password strength validation
    print("\n2. Password Strength Validation")
    print("-" * 40)
    
    test_passwords = [
        "weak",
        "StrongPassword123",
        "NoDigits",
        "noupppercase123",
        "NOLOWERCASE123"
    ]
    
    for pwd in test_passwords:
        result = validate_password_strength(pwd)
        print(f"Password: '{pwd}'")
        print(f"  Valid: {result['valid']}")
        if result['errors']:
            print(f"  Errors: {result['errors']}")
        print()


def example_jwt_operations():
    """Demonstrate JWT token operations."""
    print("=" * 60)
    print("JWT TOKEN OPERATIONS EXAMPLES")
    print("=" * 60)
    
    # Example 1: Create and verify access token
    print("\n1. Access Token Creation and Verification")
    print("-" * 50)
    
    user_data = {
        "sub": "user_12345",
        "username": "johndoe",
        "email": "john@example.com",
        "role": "user",
        "permissions": ["read_profile", "update_profile"]
    }
    
    # Create access token
    access_token = create_access_token(user_data)
    print(f"Access token created (length: {len(access_token)} chars)")
    print(f"Token preview: {access_token[:50]}...")
    
    # Verify and decode token
    try:
        payload = verify_token(access_token, "access")
        print(f"Token verified successfully!")
        print(f"User ID: {payload['sub']}")
        print(f"Username: {payload['username']}")
        print(f"Expires at: {datetime.fromtimestamp(payload['exp'])}")
    except TokenError as e:
        print(f"Token verification failed: {e}")
    
    # Example 2: Create refresh token
    print("\n2. Refresh Token Creation")
    print("-" * 30)
    
    # Regular refresh token
    refresh_token = create_refresh_token(user_data)
    print(f"Regular refresh token created")
    
    # Remember me refresh token (longer expiry)
    remember_me_token = create_refresh_token(user_data, remember_me=True)
    print(f"Remember me refresh token created")
    
    # Compare expiry times
    regular_payload = verify_token(refresh_token, "refresh")
    remember_payload = verify_token(remember_me_token, "refresh")
    
    regular_expiry = datetime.fromtimestamp(regular_payload['exp'])
    remember_expiry = datetime.fromtimestamp(remember_payload['exp'])
    
    print(f"Regular token expires: {regular_expiry}")
    print(f"Remember me token expires: {remember_expiry}")
    print(f"Difference: {remember_expiry - regular_expiry}")


def example_authentication_flow():
    """Demonstrate complete authentication flow."""
    print("=" * 60)
    print("COMPLETE AUTHENTICATION FLOW EXAMPLE")
    print("=" * 60)
    
    # Simulate user registration
    print("\n1. User Registration")
    print("-" * 25)
    
    username = "newuser"
    email = "newuser@example.com"
    password = "SecurePassword123"
    
    print(f"Registering user: {username}")
    print(f"Email: {email}")
    
    # Hash password for storage
    hashed_password = hash_password(password)
    print(f"Password hashed for database storage")
    
    # Simulate user login
    print("\n2. User Login")
    print("-" * 15)
    
    login_username = "newuser"
    login_password = "SecurePassword123"
    
    print(f"Login attempt for: {login_username}")
    
    # Verify password
    if verify_password(login_password, hashed_password):
        print("✅ Password verified - login successful")
        
        # Create user tokens
        tokens = create_user_tokens(
            user_id="user_67890",
            username=login_username,
            email=email,
            role="user",
            permissions=["read_profile", "update_profile"],
            remember_me=True
        )
        
        print(f"✅ Tokens created:")
        print(f"  Access token: {tokens['access_token'][:30]}...")
        print(f"  Refresh token: {tokens['refresh_token'][:30]}...")
        print(f"  Token type: {tokens['token_type']}")
        print(f"  Expires in: {tokens['expires_in']} seconds")
        
    else:
        print("❌ Password verification failed - login denied")
        return
    
    # Simulate API request with access token
    print("\n3. API Request with Access Token")
    print("-" * 35)
    
    try:
        # Extract user info from token
        user_info = extract_user_info(tokens['access_token'])
        print(f"✅ Token validated for user: {user_info['username']}")
        print(f"  User ID: {user_info['user_id']}")
        print(f"  Role: {user_info['role']}")
        print(f"  Permissions: {user_info['permissions']}")
        
    except TokenError as e:
        print(f"❌ Token validation failed: {e}")
    
    # Simulate token refresh
    print("\n4. Token Refresh")
    print("-" * 18)
    
    try:
        new_tokens = refresh_access_token(tokens['refresh_token'])
        print(f"✅ Access token refreshed successfully")
        print(f"  New access token: {new_tokens['access_token'][:30]}...")
        
    except TokenError as e:
        print(f"❌ Token refresh failed: {e}")


def example_password_reset_flow():
    """Demonstrate password reset flow."""
    print("=" * 60)
    print("PASSWORD RESET FLOW EXAMPLE")
    print("=" * 60)
    
    user_id = "user_12345"
    user_email = "user@example.com"
    
    print(f"\n1. Password Reset Requested")
    print("-" * 30)
    print(f"User ID: {user_id}")
    print(f"Email: {user_email}")
    
    # Create password reset token
    reset_token = create_password_reset_token(user_id, expires_minutes=30)
    print(f"✅ Password reset token created")
    print(f"  Token: {reset_token[:50]}...")
    print(f"  Expires in: 30 minutes")
    
    # Simulate email with reset link
    reset_link = f"https://app.example.com/reset-password?token={reset_token}"
    print(f"✅ Reset link: {reset_link[:60]}...")
    
    print(f"\n2. Password Reset Token Verification")
    print("-" * 40)
    
    # Verify reset token
    verified_user_id = verify_password_reset_token(reset_token)
    if verified_user_id:
        print(f"✅ Reset token verified for user: {verified_user_id}")
        
        # Create new password
        new_password = "NewSecurePassword456"
        new_hashed = hash_password(new_password)
        
        print(f"✅ New password hashed and ready to save")
        print(f"✅ Password reset completed successfully")
        
    else:
        print(f"❌ Invalid or expired reset token")


def example_security_utilities():
    """Demonstrate security utility functions."""
    print("=" * 60)
    print("SECURITY UTILITIES EXAMPLES")
    print("=" * 60)
    
    # Example 1: Generate secure tokens
    print("\n1. Secure Token Generation")
    print("-" * 30)
    
    # Generate various secure tokens
    short_token = generate_secure_token(16)
    medium_token = generate_secure_token(32)
    long_token = generate_secure_token(64)
    
    print(f"Short token (16 bytes): {short_token}")
    print(f"Medium token (32 bytes): {medium_token}")
    print(f"Long token (64 bytes): {long_token}")
    
    # Example 2: Token expiry checking
    print("\n2. Token Expiry Checking")
    print("-" * 25)
    
    # Create tokens with different expiry times
    short_lived = create_access_token(
        {"sub": "user123"}, 
        expires_delta=timedelta(seconds=1)
    )
    long_lived = create_access_token(
        {"sub": "user123"}, 
        expires_delta=timedelta(hours=1)
    )
    
    print(f"Short-lived token expired: {is_token_expired(short_lived)}")
    print(f"Long-lived token expired: {is_token_expired(long_lived)}")
    
    # Wait a moment and check again
    import time
    time.sleep(2)
    
    print(f"After 2 seconds:")
    print(f"Short-lived token expired: {is_token_expired(short_lived)}")
    print(f"Long-lived token expired: {is_token_expired(long_lived)}")


def example_error_handling():
    """Demonstrate error handling in security operations."""
    print("=" * 60)
    print("ERROR HANDLING EXAMPLES")
    print("=" * 60)
    
    print("\n1. Password Error Handling")
    print("-" * 30)
    
    try:
        # Try to hash empty password
        hash_password("")
    except PasswordError as e:
        print(f"✅ Password error caught: {e}")
    
    print("\n2. Token Error Handling")
    print("-" * 25)
    
    try:
        # Try to verify invalid token
        verify_token("invalid.jwt.token", "access")
    except TokenError as e:
        print(f"✅ Token error caught: {e}")
    
    try:
        # Try to use access token as refresh token
        access_token = create_access_token({"sub": "user123"})
        verify_token(access_token, "refresh")
    except TokenError as e:
        print(f"✅ Token type error caught: {e}")
    
    try:
        # Try to refresh with invalid token
        refresh_access_token("invalid.refresh.token")
    except TokenError as e:
        print(f"✅ Refresh error caught: {e}")


def main():
    """Run all examples."""
    print("🔐 AID-US-001B: JWT Authentication Utilities - Usage Examples")
    print("=" * 70)
    print("This script demonstrates how to use the security utilities.")
    print("=" * 70)
    
    try:
        example_password_operations()
        example_jwt_operations()
        example_authentication_flow()
        example_password_reset_flow()
        example_security_utilities()
        example_error_handling()
        
        print("\n" + "=" * 70)
        print("🎉 ALL EXAMPLES COMPLETED SUCCESSFULLY!")
        print("=" * 70)
        print("\n📚 Key Features Demonstrated:")
        print("  ✅ Password hashing and verification")
        print("  ✅ Password strength validation")
        print("  ✅ JWT access and refresh token creation")
        print("  ✅ Token verification and validation")
        print("  ✅ Complete authentication flow")
        print("  ✅ Password reset functionality")
        print("  ✅ Security utilities and helpers")
        print("  ✅ Comprehensive error handling")
        print("\n🔧 Ready for integration with:")
        print("  • FastAPI authentication endpoints")
        print("  • User registration and login systems")
        print("  • API middleware for token validation")
        print("  • Password reset and email verification")
        
    except Exception as e:
        print(f"\n❌ Example execution failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
