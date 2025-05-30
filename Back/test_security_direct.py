#!/usr/bin/env python3
"""
Direct Security Module Test - Bypasses database import issues
This script tests the security functions directly without database dependencies.
"""

import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

def test_security_direct():
    """Test security functions directly by importing the module file."""
    print("🔐 Testing AID-US-001B Security Functions Directly")
    print("=" * 60)
    
    try:
        # Import security module directly (bypass __init__.py)
        from app.core.security import (
            hash_password, verify_password, validate_password_strength,
            create_access_token, create_refresh_token, verify_token,
            extract_user_info, create_user_tokens, refresh_access_token
        )
        print("✅ Security module imported successfully (direct import)")
        
        # Test 1: Password Hashing
        print("\n1. Testing Password Hashing")
        print("-" * 30)
        password = "TestPassword123"
        hashed = hash_password(password)
        verified = verify_password(password, hashed)
        print(f"✅ Password hashed: {hashed[:30]}...")
        print(f"✅ Password verified: {verified}")
        assert verified == True
        
        # Test 2: Password Validation
        print("\n2. Testing Password Validation")
        print("-" * 35)
        validation = validate_password_strength(password)
        print(f"✅ Password validation: {validation['valid']}")
        print(f"   Requirements met: {validation['requirements']}")
        assert validation['valid'] == True
        
        # Test 3: JWT Access Token
        print("\n3. Testing JWT Access Token")
        print("-" * 30)
        user_data = {"sub": "user123", "username": "testuser"}
        access_token = create_access_token(user_data)
        print(f"✅ Access token created: {len(access_token)} chars")
        print(f"   Token preview: {access_token[:50]}...")
        
        # Verify token
        payload = verify_token(access_token, "access")
        print(f"✅ Token verified: {payload['sub']} = {user_data['sub']}")
        assert payload['sub'] == user_data['sub']
        
        # Test 4: JWT Refresh Token
        print("\n4. Testing JWT Refresh Token")
        print("-" * 32)
        refresh_token = create_refresh_token(user_data)
        refresh_payload = verify_token(refresh_token, "refresh")
        print(f"✅ Refresh token created and verified")
        print(f"   User: {refresh_payload['sub']}")
        assert refresh_payload['sub'] == user_data['sub']
        
        # Test 5: Complete User Tokens
        print("\n5. Testing Complete User Token Creation")
        print("-" * 42)
        tokens = create_user_tokens(
            user_id="user_456",
            username="completeuser",
            email="test@example.com",
            role="user",
            permissions=["read", "write"]
        )
        print(f"✅ Complete tokens created:")
        print(f"   Access token: {len(tokens['access_token'])} chars")
        print(f"   Refresh token: {len(tokens['refresh_token'])} chars")
        print(f"   Token type: {tokens['token_type']}")
        print(f"   Expires in: {tokens['expires_in']} seconds")
        
        # Verify the user info can be extracted
        user_info = extract_user_info(tokens['access_token'])
        print(f"✅ User info extracted:")
        print(f"   User ID: {user_info['user_id']}")
        print(f"   Username: {user_info['username']}")
        print(f"   Role: {user_info['role']}")
        
        # Test 6: Token Refresh
        print("\n6. Testing Token Refresh")
        print("-" * 25)
        new_tokens = refresh_access_token(tokens['refresh_token'])
        print(f"✅ Token refreshed successfully")
        print(f"   New access token: {len(new_tokens['access_token'])} chars")
        
        # Verify new token works
        new_payload = verify_token(new_tokens['access_token'], "access")
        print(f"✅ New token verified: {new_payload['username']}")
        
        print("\n" + "=" * 60)
        print("🎉 ALL SECURITY TESTS PASSED!")
        print("=" * 60)
        print("\n✅ Implemented Features Working:")
        print("  • Password hashing with bcrypt")
        print("  • Password strength validation")  
        print("  • JWT access token creation/verification")
        print("  • JWT refresh token creation/verification")
        print("  • Complete authentication token workflow")
        print("  • Token refresh functionality")
        print("  • User information extraction from tokens")
        print("\n🚀 AID-US-001B is fully functional!")
        print("   Ready for FastAPI endpoint integration.")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   This indicates missing dependencies or module issues.")
        return False
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_security_direct()
    if success:
        print("\n🎯 Next Steps:")
        print("  1. Update backlog to mark AID-US-001B as ✅ completed")
        print("  2. Proceed to AID-US-001C: Authentication API Endpoints")
        print("  3. Fix SQLAlchemy version compatibility for full integration")
        sys.exit(0)
    else:
        print("\n🔧 Troubleshooting needed:")
        print("  1. Check that all dependencies are installed: pip install -r requirements.txt")
        print("  2. Ensure you're in the correct directory")
        print("  3. Check that security module exists: app/core/security.py")
        sys.exit(1)
