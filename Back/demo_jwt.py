#!/usr/bin/env python3
"""
Interactive demonstration of AID-US-001B: JWT Authentication Utilities

This script provides an interactive demo of all JWT functionality.
Run this to see the security module in action!
"""

import sys
from pathlib import Path
from datetime import datetime, timezone

# Add backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

def print_header(title: str) -> None:
    """Print a formatted header."""
    print(f"\n{'='*60}")
    print(f"🔐 {title}")
    print(f"{'='*60}")

def print_section(title: str) -> None:
    """Print a formatted section header."""
    print(f"\n🔹 {title}")
    print("-" * 50)

def demo_password_hashing():
    """Demonstrate password hashing functionality."""
    from app.core.security import hash_password, verify_password
    
    print_section("Password Hashing & Verification")
    
    # Demo password
    password = "MySecurePassword123!@#"
    print(f"Original password: {password}")
    
    # Hash the password
    hashed = hash_password(password)
    print(f"Hashed password: {hashed}")
    print(f"Hash length: {len(hashed)} characters")
    
    # Verify correct password
    is_valid = verify_password(password, hashed)
    print(f"✅ Correct password verification: {is_valid}")
    
    # Verify incorrect password
    is_invalid = verify_password("WrongPassword", hashed)
    print(f"❌ Incorrect password verification: {is_invalid}")
    
    return hashed

def demo_jwt_tokens():
    """Demonstrate JWT token creation and validation."""
    from app.core.security import (
        create_access_token, create_refresh_token, parse_token, 
        validate_token, get_token_subject, get_token_expiration
    )
    
    print_section("JWT Token Creation & Validation")
    
    user_id = "demo_user_12345"
    print(f"Creating tokens for user: {user_id}")
    
    # Create access token
    access_token = create_access_token(user_id)
    print(f"\n📄 Access Token:")
    print(f"   Token: {access_token[:50]}...")
    print(f"   Length: {len(access_token)} characters")
    
    # Parse access token
    access_claims = parse_token(access_token)
    print(f"   Subject: {access_claims['sub']}")
    print(f"   Type: {access_claims['type']}")
    print(f"   Expires: {datetime.fromtimestamp(access_claims['exp'], tz=timezone.utc)}")
    
    # Create refresh token
    refresh_token = create_refresh_token(user_id, remember_me=True)
    print(f"\n🔄 Refresh Token (Remember Me):")
    print(f"   Token: {refresh_token[:50]}...")
    print(f"   Length: {len(refresh_token)} characters")
    
    # Parse refresh token
    refresh_claims = parse_token(refresh_token)
    print(f"   Subject: {refresh_claims['sub']}")
    print(f"   Type: {refresh_claims['type']}")
    print(f"   Remember Me: {refresh_claims['remember_me']}")
    print(f"   Expires: {datetime.fromtimestamp(refresh_claims['exp'], tz=timezone.utc)}")
    
    return access_token, refresh_token

def demo_token_utilities():
    """Demonstrate token utility functions."""
    from app.core.security import (
        create_token_pair, refresh_access_token, blacklist_token,
        is_token_blacklisted, clear_blacklist
    )
    
    print_section("Token Utility Functions")
    
    user_id = "utility_demo_user"
    
    # Create token pair
    tokens = create_token_pair(user_id, remember_me=True)
    print("📦 Token Pair Created:")
    print(f"   Access Token: {tokens['access_token'][:30]}...")
    print(f"   Refresh Token: {tokens['refresh_token'][:30]}...")
    print(f"   Token Type: {tokens['token_type']}")
    
    # Refresh access token
    new_access = refresh_access_token(tokens['refresh_token'])
    print(f"\n🔄 New Access Token (from refresh):")
    print(f"   Token: {new_access[:30]}...")
    print(f"   Different from original: {new_access != tokens['access_token']}")
    
    # Demonstrate blacklisting
    clear_blacklist()
    print(f"\n🚫 Token Blacklisting:")
    print(f"   Initially blacklisted: {is_token_blacklisted(tokens['access_token'])}")
    
    blacklist_token(tokens['access_token'])
    print(f"   After blacklisting: {is_token_blacklisted(tokens['access_token'])}")
    
    return tokens

def demo_security_features():
    """Demonstrate advanced security features."""
    from app.core.security import (
        generate_secure_secret, generate_jwt_secret,
        create_password_reset_token, validate_password_reset_token
    )
    
    print_section("Advanced Security Features")
    
    # Secure secret generation
    secret1 = generate_secure_secret()
    secret2 = generate_secure_secret(64)  # Custom length
    jwt_secret = generate_jwt_secret()
    
    print("🔑 Secure Secret Generation:")
    print(f"   Standard secret: {secret1}")
    print(f"   Custom length secret: {secret2[:50]}...")
    print(f"   JWT secret: {jwt_secret[:50]}...")
    print(f"   All secrets unique: {len({secret1, secret2, jwt_secret}) == 3}")
    
    # Password reset tokens
    user_id = "reset_demo_user"
    reset_token = create_password_reset_token(user_id, expires_minutes=30)
    
    print(f"\n🔄 Password Reset Token:")
    print(f"   Token: {reset_token[:50]}...")
    print(f"   Valid for user: {validate_password_reset_token(reset_token)}")

def demo_error_handling():
    """Demonstrate error handling."""
    from app.core.security import (
        parse_token, validate_token, InvalidTokenError, TokenExpiredError
    )
    
    print_section("Error Handling")
    
    print("🚫 Testing Invalid Tokens:")
    
    # Test invalid token
    try:
        parse_token("invalid.token.string")
        print("   ❌ Should have failed for invalid token")
    except InvalidTokenError:
        print("   ✅ Invalid token correctly rejected")
    
    # Test empty token
    try:
        parse_token("")
        print("   ❌ Should have failed for empty token")
    except InvalidTokenError:
        print("   ✅ Empty token correctly rejected")
    
    # Test wrong token type
    from app.core.security import create_access_token
    access_token = create_access_token("test_user")
    
    try:
        validate_token(access_token, "refresh")  # Wrong type
        print("   ❌ Should have failed for wrong token type")
    except InvalidTokenError:
        print("   ✅ Wrong token type correctly rejected")

def demo_integration_scenario():
    """Demonstrate a complete authentication flow."""
    from app.core.security import (
        hash_password, verify_password, create_token_pair,
        validate_token, refresh_access_token, blacklist_token
    )
    
    print_section("Complete Authentication Flow")
    
    # User registration scenario
    print("👤 User Registration:")
    username = "john_doe"
    password = "SecurePassword123!"
    hashed_password = hash_password(password)
    print(f"   Username: {username}")
    print(f"   Password hashed and stored: ✅")
    
    # Login scenario
    print("\n🔐 User Login:")
    login_password = "SecurePassword123!"  # User enters password
    
    if verify_password(login_password, hashed_password):
        print("   Password verified: ✅")
        
        # Create tokens
        tokens = create_token_pair(username, remember_me=True)
        print("   Tokens created: ✅")
        print(f"   Access token: {tokens['access_token'][:30]}...")
        print(f"   Refresh token: {tokens['refresh_token'][:30]}...")
    else:
        print("   Password verification failed: ❌")
        return
    
    # API request scenario
    print("\n📡 API Request:")
    try:
        claims = validate_token(tokens['access_token'], 'access')
        print(f"   Access token validated: ✅")
        print(f"   User authenticated as: {claims['sub']}")
    except Exception as e:
        print(f"   Token validation failed: ❌ {e}")
        return
    
    # Token refresh scenario
    print("\n🔄 Token Refresh:")
    try:
        new_access_token = refresh_access_token(tokens['refresh_token'])
        print("   New access token created: ✅")
        print(f"   New token: {new_access_token[:30]}...")
    except Exception as e:
        print(f"   Token refresh failed: ❌ {e}")
    
    # Logout scenario
    print("\n👋 User Logout:")
    blacklist_token(tokens['access_token'])
    blacklist_token(tokens['refresh_token'])
    print("   Tokens blacklisted: ✅")
    print("   User logged out successfully: ✅")

def main():
    """Run the complete demonstration."""
    print_header("JWT Authentication Utilities - Interactive Demo")
    
    try:
        # Import and test basic functionality
        from app.core.security import hash_password
        print("✅ Security module imported successfully")
        
        # Load configuration
        from app.core.config import settings
        print(f"✅ Configuration loaded (JWT Algorithm: {settings.JWT_ALGORITHM})")
        
    except ImportError as e:
        print(f"❌ Failed to import required modules: {e}")
        print("\n💡 Make sure to run the build script first:")
        print("   ./build_AID-US-001B.sh")
        return False
    
    # Run demonstrations
    print("\n🚀 Starting demonstrations...")
    
    # 1. Password hashing
    hashed_password = demo_password_hashing()
    
    # 2. JWT tokens
    access_token, refresh_token = demo_jwt_tokens()
    
    # 3. Token utilities
    token_pair = demo_token_utilities()
    
    # 4. Security features
    demo_security_features()
    
    # 5. Error handling
    demo_error_handling()
    
    # 6. Integration scenario
    demo_integration_scenario()
    
    # Summary
    print_header("Demo Complete!")
    print("🎉 All JWT authentication utilities demonstrated successfully!")
    print("\n📋 Features demonstrated:")
    print("   ✅ Password hashing and verification")
    print("   ✅ JWT access token creation and validation")
    print("   ✅ JWT refresh token creation and validation")
    print("   ✅ Token utility functions")
    print("   ✅ Security features (secrets, password reset)")
    print("   ✅ Error handling")
    print("   ✅ Complete authentication flow")
    
    print("\n🚀 Ready for production use!")
    print("💡 Next steps: Build authentication API endpoints")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        if success:
            sys.exit(0)
        else:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n💥 Demo crashed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
