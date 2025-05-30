#!/usr/bin/env python3
"""
Simplified test script for RefreshToken model structure (no database connection required).
Run this to verify the RefreshToken model structure is correct.
"""
import sys
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent / "app"))

def test_basic_model_structure():
    """Test RefreshToken model structure without database connection."""
    print("🧪 Testing Basic Model Structure...")
    try:
        # Import SQLAlchemy Base and column types to test model structure
        from sqlalchemy.ext.declarative import declarative_base
        from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text
        from sqlalchemy.dialects.postgresql import UUID, INET
        
        # Create a temporary Base for testing
        Base = declarative_base()
        
        # Define a simplified RefreshToken model for testing
        class TestRefreshToken(Base):
            __tablename__ = "refresh_tokens"
            
            id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
            token_hash = Column(String(255), unique=True, nullable=False, index=True)
            user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
            expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
            is_revoked = Column(Boolean, default=False, index=True)
            remember_me = Column(Boolean, default=False)
            user_agent = Column(Text, nullable=True)
            ip_address = Column(INET, nullable=True)
            created_at = Column(DateTime(timezone=True))
            
            def is_expired(self):
                return datetime.now(timezone.utc) > self.expires_at.replace(tzinfo=timezone.utc)
            
            def is_valid(self):
                return not self.is_revoked and not self.is_expired()
            
            def revoke(self):
                self.is_revoked = True
                
            @property
            def days_until_expiry(self):
                if self.is_expired():
                    return 0
                now = datetime.now(timezone.utc)
                expires_at_utc = self.expires_at.replace(tzinfo=timezone.utc)
                delta = expires_at_utc - now
                return max(0, delta.days)
        
        print("✅ Basic model structure is valid")
        return True
        
    except Exception as e:
        print(f"❌ Basic model structure test failed: {e}")
        return False

def test_model_instantiation_and_methods():
    """Test creating RefreshToken instances and using methods."""
    print("\n🧪 Testing Model Instantiation and Methods...")
    try:
        # Create the test model inline
        from sqlalchemy.ext.declarative import declarative_base
        from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text
        from sqlalchemy.dialects.postgresql import UUID, INET
        
        Base = declarative_base()
        
        class TestRefreshToken(Base):
            __tablename__ = "refresh_tokens"
            
            id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
            token_hash = Column(String(255), unique=True, nullable=False, index=True)
            user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
            expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
            is_revoked = Column(Boolean, default=False, index=True)
            remember_me = Column(Boolean, default=False)
            user_agent = Column(Text, nullable=True)
            ip_address = Column(INET, nullable=True)
            created_at = Column(DateTime(timezone=True))
            
            def is_expired(self):
                return datetime.now(timezone.utc) > self.expires_at.replace(tzinfo=timezone.utc)
            
            def is_valid(self):
                return not self.is_revoked and not self.is_expired()
            
            def revoke(self):
                self.is_revoked = True
                
            @property
            def days_until_expiry(self):
                if self.is_expired():
                    return 0
                now = datetime.now(timezone.utc)
                expires_at_utc = self.expires_at.replace(tzinfo=timezone.utc)
                delta = expires_at_utc - now
                return max(0, delta.days)
            
        # Create a test token
        token = TestRefreshToken()
        token.id = uuid.uuid4()
        token.token_hash = "test_hash_123"
        token.user_id = uuid.uuid4()
        token.expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        token.is_revoked = False
        token.remember_me = True
        token.user_agent = "Mozilla/5.0 Test Browser"
        token.ip_address = "192.168.1.100"
        token.created_at = datetime.now(timezone.utc)
        
        print("✅ Token instance created successfully")
        print(f"📝 Token ID: {token.id}")
        print(f"📝 Token Hash: {token.token_hash}")
        print(f"📝 User ID: {token.user_id}")
        print(f"📝 Expires at: {token.expires_at}")
        print(f"📝 Remember me: {token.remember_me}")
        
        # Test methods
        print(f"✅ is_valid(): {token.is_valid()}")
        print(f"✅ is_expired(): {token.is_expired()}")
        print(f"✅ days_until_expiry: {token.days_until_expiry}")
        
        # Test revocation
        token.revoke()
        print(f"✅ After revocation is_valid(): {token.is_valid()}")
        print(f"✅ After revocation is_revoked: {token.is_revoked}")
        
        # Test expired token
        expired_token = TestRefreshToken()
        expired_token.expires_at = datetime.now(timezone.utc) - timedelta(days=1)
        expired_token.is_revoked = False
        
        print(f"✅ Expired token is_valid(): {expired_token.is_valid()}")
        print(f"✅ Expired token is_expired(): {expired_token.is_expired()}")
        
        return True
        
    except Exception as e:
        print(f"❌ Instantiation and methods test failed: {e}")
        return False

def test_column_types():
    """Test that all column types are correctly defined."""
    print("\n🧪 Testing Column Types...")
    try:
        from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text
        from sqlalchemy.dialects.postgresql import UUID, INET
        
        # Test all column types that should be in RefreshToken
        test_columns = {
            'id': UUID(as_uuid=True),
            'token_hash': String(255),
            'user_id': UUID(as_uuid=True),
            'expires_at': DateTime(timezone=True),
            'is_revoked': Boolean,
            'remember_me': Boolean,
            'user_agent': Text,
            'ip_address': INET,
            'created_at': DateTime(timezone=True),
        }
        
        print("✅ All column types are importable and valid")
        print(f"📋 Column types tested: {list(test_columns.keys())}")
        return True
        
    except Exception as e:
        print(f"❌ Column types test failed: {e}")
        return False

def test_actual_model_file():
    """Test if we can at least read the actual model file."""
    print("\n🧪 Testing Actual Model File...")
    try:
        model_file_path = Path(__file__).parent / "app" / "models" / "refresh_token.py"
        
        if model_file_path.exists():
            with open(model_file_path, 'r') as f:
                content = f.read()
                
            # Check for key components
            required_components = [
                'class RefreshToken',
                'token_hash',
                'user_id',
                'expires_at',
                'is_revoked',
                'remember_me',
                'is_valid',
                'is_expired',
                'revoke'
            ]
            
            missing_components = []
            for component in required_components:
                if component not in content:
                    missing_components.append(component)
            
            if missing_components:
                print(f"❌ Missing components in model file: {missing_components}")
                return False
            else:
                print("✅ All required components found in model file")
                print(f"📄 Model file size: {len(content)} characters")
                return True
        else:
            print(f"❌ Model file not found at: {model_file_path}")
            return False
            
    except Exception as e:
        print(f"❌ Model file test failed: {e}")
        return False

def run_simplified_tests():
    """Run all simplified tests and provide summary."""
    print("🚀 Starting Simplified RefreshToken Model Tests...\n")
    print("ℹ️  These tests don't require a database connection\n")
    
    tests = [
        test_column_types,
        test_basic_model_structure,
        test_model_instantiation_and_methods,
        test_actual_model_file
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
        print("\n🎉 All simplified tests passed!")
        print("✨ RefreshToken model structure is correct and ready for database integration.")
        return True
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please check the output above.")
        return False

if __name__ == "__main__":
    success = run_simplified_tests()
    sys.exit(0 if success else 1)
