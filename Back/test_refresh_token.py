#!/usr/bin/env python3
"""
Test script for RefreshToken model functionality.
Run this to verify the RefreshToken model is working correctly.
"""
import sys
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent / "app"))

def test_model_import():
    """Test that all models can be imported successfully."""
    print("🧪 Testing Model Import...")
    try:
        from app.models import User, RefreshToken, Role, Department
        print("✅ All models imported successfully")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_model_structure():
    """Test RefreshToken model structure and attributes."""
    print("\n🧪 Testing Model Structure...")
    try:
        from app.models import RefreshToken
        
        # Check if all required attributes exist
        required_attrs = [
            'id', 'token_hash', 'user_id', 'expires_at', 'is_revoked', 
            'remember_me', 'user_agent', 'ip_address', 'created_at'
        ]
        
        model_attrs = [attr for attr in dir(RefreshToken) if not attr.startswith('_')]
        
        missing_attrs = [attr for attr in required_attrs if attr not in model_attrs]
        if missing_attrs:
            print(f"❌ Missing attributes: {missing_attrs}")
            return False
            
        print("✅ All required attributes present")
        print(f"📋 Model attributes: {sorted(model_attrs)}")
        return True
        
    except Exception as e:
        print(f"❌ Structure test failed: {e}")
        return False

def test_model_instantiation():
    """Test creating RefreshToken instances."""
    print("\n🧪 Testing Model Instantiation...")
    try:
        from app.models import RefreshToken
        
        # Create a RefreshToken instance
        token = RefreshToken(
            token_hash="test_hash_123",
            user_id=uuid.uuid4(),
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
            remember_me=True,
            user_agent="Mozilla/5.0 Test Browser",
            ip_address="192.168.1.100"
        )
        
        print("✅ RefreshToken instance created successfully")
        print(f"📝 Token ID: {token.id}")
        print(f"📝 Token Hash: {token.token_hash}")
        print(f"📝 User ID: {token.user_id}")
        print(f"📝 Expires at: {token.expires_at}")
        print(f"📝 Remember me: {token.remember_me}")
        return True
        
    except Exception as e:
        print(f"❌ Instantiation test failed: {e}")
        return False

def test_utility_methods():
    """Test RefreshToken utility methods."""
    print("\n🧪 Testing Utility Methods...")
    try:
        from app.models import RefreshToken
        
        # Test with valid token
        valid_token = RefreshToken(
            token_hash="valid_token_hash",
            user_id=uuid.uuid4(),
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
            is_revoked=False,
            remember_me=True
        )
        
        print(f"✅ is_valid(): {valid_token.is_valid()}")
        print(f"✅ is_expired(): {valid_token.is_expired()}")
        print(f"✅ days_until_expiry: {valid_token.days_until_expiry}")
        print(f"✅ is_remember_me_token: {valid_token.is_remember_me_token}")
        
        # Test with expired token
        expired_token = RefreshToken(
            token_hash="expired_token_hash",
            user_id=uuid.uuid4(),
            expires_at=datetime.now(timezone.utc) - timedelta(days=1),  # Yesterday
            is_revoked=False
        )
        
        print(f"✅ Expired token is_valid(): {expired_token.is_valid()}")
        print(f"✅ Expired token is_expired(): {expired_token.is_expired()}")
        
        # Test revocation
        valid_token.revoke()
        print(f"✅ After revocation is_valid(): {valid_token.is_valid()}")
        print(f"✅ After revocation is_revoked: {valid_token.is_revoked}")
        
        # Test security info
        security_info = valid_token.security_info
        print(f"✅ Security info keys: {list(security_info.keys())}")
        
        return True
        
    except Exception as e:
        print(f"❌ Utility methods test failed: {e}")
        return False

def test_class_method():
    """Test RefreshToken class method."""
    print("\n🧪 Testing Class Method...")
    try:
        from app.models import RefreshToken
        
        user_id = uuid.uuid4()
        expires_at = datetime.now(timezone.utc) + timedelta(days=30)
        
        token = RefreshToken.create_token(
            user_id=user_id,
            token_hash="class_method_token_hash",
            expires_at=expires_at,
            remember_me=True,
            user_agent="Test User Agent",
            ip_address="10.0.0.1"
        )
        
        print("✅ Token created via class method")
        print(f"📝 Token user_id: {token.user_id}")
        print(f"📝 Token hash: {token.token_hash}")
        print(f"📝 Remember me: {token.remember_me}")
        print(f"📝 User agent: {token.user_agent}")
        print(f"📝 IP address: {token.ip_address}")
        
        return True
        
    except Exception as e:
        print(f"❌ Class method test failed: {e}")
        return False

def test_model_repr():
    """Test model string representation."""
    print("\n🧪 Testing Model Representation...")
    try:
        from app.models import RefreshToken
        
        token = RefreshToken(
            token_hash="repr_test_hash",
            user_id=uuid.uuid4(),
            expires_at=datetime.now(timezone.utc) + timedelta(days=7)
        )
        
        repr_str = repr(token)
        print(f"✅ Model repr: {repr_str}")
        
        # Check if repr contains expected information
        if "RefreshToken" in repr_str and "user_id" in repr_str:
            print("✅ Repr format is correct")
            return True
        else:
            print("❌ Repr format is incomplete")
            return False
            
    except Exception as e:
        print(f"❌ Repr test failed: {e}")
        return False

def test_relationships():
    """Test model relationships (without database)."""
    print("\n🧪 Testing Model Relationships...")
    try:
        from app.models import RefreshToken, User
        
        # Check if relationships are defined
        if hasattr(RefreshToken, 'user'):
            print("✅ RefreshToken has 'user' relationship")
        else:
            print("❌ RefreshToken missing 'user' relationship")
            return False
            
        if hasattr(User, 'refresh_tokens'):
            print("✅ User has 'refresh_tokens' relationship")
        else:
            print("❌ User missing 'refresh_tokens' relationship")
            return False
            
        # Check relationship properties
        refresh_token_rel = RefreshToken.user.property
        print(f"✅ RefreshToken.user relationship: {refresh_token_rel}")
        
        user_rel = User.refresh_tokens.property
        print(f"✅ User.refresh_tokens relationship: {user_rel}")
        
        return True
        
    except Exception as e:
        print(f"❌ Relationship test failed: {e}")
        return False

def run_all_tests():
    """Run all tests and provide summary."""
    print("🚀 Starting RefreshToken Model Tests...\n")
    
    tests = [
        test_model_import,
        test_model_structure,
        test_model_instantiation,
        test_utility_methods,
        test_class_method,
        test_model_repr,
        test_relationships
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    print("\n" + "="*50)
    print("📊 TEST SUMMARY")
    print("="*50)
    
    passed = sum(results)
    total = len(results)
    
    print(f"✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {total - passed}/{total}")
    
    if passed == total:
        print("\n🎉 All tests passed! RefreshToken model is working correctly.")
        return True
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please check the output above.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
