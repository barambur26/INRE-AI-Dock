#!/bin/bash

# Test Runner for AID-US-001B: JWT Authentication Utilities & Password Hashing
# This script runs comprehensive tests for all security functions

echo "🔐 AID-US-001B: JWT Authentication Utilities Test Suite"
echo "======================================================="

# Check if we're in the right directory
if [ ! -f "app/core/security.py" ]; then
    echo "❌ Error: Please run this script from the backend directory"
    echo "   Expected: /Users/blas/Desktop/INRE/INRE-AI-Dock/Back"
    exit 1
fi

echo "✅ In correct backend directory: $(pwd)"

# Activate virtual environment
if [ -d "venv" ]; then
    echo "🔄 Activating virtual environment..."
    source venv/bin/activate
    echo "✅ Virtual environment activated"
else
    echo "⚠️  Virtual environment not found - make sure dependencies are installed"
fi

# Set Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
echo "✅ Python path configured"

# Check if required dependencies are installed
echo
echo "📦 Checking dependencies..."
python -c "
import sys
sys.path.insert(0, '.')

required_modules = [
    ('jose', 'python-jose'),
    ('passlib', 'passlib'),
    ('pydantic_settings', 'pydantic-settings'),
    ('pytest', 'pytest'),
]

missing = []
for module, package in required_modules:
    try:
        __import__(module)
        print(f'✅ {package}')
    except ImportError:
        print(f'❌ {package} - MISSING')
        missing.append(package)

if missing:
    print(f'\\n⚠️  Missing dependencies: {missing}')
    print('Install with: pip install ' + ' '.join(missing))
    sys.exit(1)
else:
    print('\\n✅ All dependencies available')
"

if [ $? -ne 0 ]; then
    echo "❌ Dependency check failed. Install missing packages first."
    exit 1
fi

# Test security module imports
echo
echo "🧪 Testing security module imports..."
python -c "
import sys
sys.path.insert(0, '.')

try:
    from app.core.security import (
        hash_password, verify_password, validate_password_strength,
        create_access_token, create_refresh_token, verify_token,
        create_user_tokens, refresh_access_token
    )
    print('✅ All security functions imported successfully')
    
    # Quick smoke test
    password = 'TestPassword123'
    hashed = hash_password(password)
    verified = verify_password(password, hashed)
    assert verified == True
    print('✅ Password hashing/verification working')
    
    token = create_access_token({'sub': 'test_user'})
    payload = verify_token(token, 'access')
    assert payload['sub'] == 'test_user'
    print('✅ JWT token creation/verification working')
    
    print('\\n🎉 Security module is ready!')
    
except Exception as e:
    print(f'❌ Security module test failed: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
"

if [ $? -ne 0 ]; then
    echo "❌ Security module test failed."
    exit 1
fi

# Run comprehensive test suite
echo
echo "🚀 Running comprehensive test suite..."
echo "======================================"

# Run pytest with verbose output
python -m pytest test_AID_US_001B.py -v --tb=short --no-header

if [ $? -eq 0 ]; then
    echo
    echo "🎉 ALL TESTS PASSED!"
    echo "✅ AID-US-001B: JWT Authentication Utilities implementation is complete and working correctly"
    echo
    echo "📋 Summary of implemented features:"
    echo "  ✅ Password hashing with bcrypt (configurable rounds)"
    echo "  ✅ Password strength validation"
    echo "  ✅ JWT access token generation (15 min expiry)" 
    echo "  ✅ JWT refresh token generation (7-30 days expiry)"
    echo "  ✅ Token validation and decoding"
    echo "  ✅ Token utilities (extract user info, check expiry)"
    echo "  ✅ Security utilities (password reset, email verification)"
    echo "  ✅ Authentication helpers (complete login flow)"
    echo "  ✅ Comprehensive error handling"
    echo "  ✅ Full test coverage"
    echo
    echo "🔧 Next steps:"
    echo "  1. Mark AID-US-001B as ✅ completed in backlog"
    echo "  2. Proceed to AID-US-001C (Authentication API Endpoints)"
    echo "  3. Or work on frontend authentication integration"
    echo
    echo "📚 Usage examples available in: examples_AID_US_001B.py"
else
    echo
    echo "💥 SOME TESTS FAILED!"
    echo "Please review the failed tests and fix any issues."
    echo
    echo "🔍 Common troubleshooting:"
    echo "  - Ensure all dependencies are installed: pip install -r requirements.txt"
    echo "  - Check JWT secret key configuration"
    echo "  - Verify bcrypt is working correctly"
    echo "  - Check Python path and module imports"
fi
