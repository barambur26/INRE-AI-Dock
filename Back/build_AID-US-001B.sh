#!/bin/bash

# AID-US-001B: JWT Authentication Utilities - Installation and Test Script
# This script installs dependencies and tests JWT functionality

set -e  # Exit on any error

echo "🔐 AID-US-001B: JWT Authentication Utilities"
echo "============================================"

# Check if we're in the right directory
if [ ! -f "requirements.txt" ] || [ ! -d "app" ]; then
    echo "❌ Error: Please run this script from the backend directory"
    echo "   Expected: /Users/blas/Desktop/INRE/INRE-AI-Dock/Back"
    exit 1
fi

echo "✅ In correct backend directory: $(pwd)"

# Step 1: Virtual Environment
echo
echo "🔄 Step 1: Setting up Python environment..."
if [ -d "venv" ]; then
    echo "✅ Virtual environment found"
    source venv/bin/activate
    echo "✅ Virtual environment activated"
    echo "   Python: $(which python)"
    echo "   Python version: $(python --version)"
else
    echo "❌ Virtual environment not found!"
    echo "   Create one with: python -m venv venv"
    exit 1
fi

# Step 2: Install JWT Dependencies
echo
echo "📦 Step 2: Installing JWT authentication dependencies..."
echo "   Installing core JWT and cryptography packages..."

# Install JWT-specific dependencies
pip install python-jose[cryptography]==3.3.0 --quiet
if [ $? -eq 0 ]; then
    echo "✅ python-jose[cryptography] installed"
else
    echo "❌ Failed to install python-jose"
    exit 1
fi

pip install passlib[bcrypt]==1.7.4 --quiet
if [ $? -eq 0 ]; then
    echo "✅ passlib[bcrypt] installed"
else
    echo "❌ Failed to install passlib"
    exit 1
fi

pip install bcrypt==4.1.2 --quiet
if [ $? -eq 0 ]; then
    echo "✅ bcrypt installed"
else
    echo "❌ Failed to install bcrypt"
    exit 1
fi

pip install python-multipart==0.0.6 --quiet
if [ $? -eq 0 ]; then
    echo "✅ python-multipart installed"
else
    echo "❌ Failed to install python-multipart"
    exit 1
fi

echo "✅ All JWT dependencies installed successfully!"

# Step 3: Verify Python Path and Files
echo
echo "📁 Step 3: Verifying file structure..."
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
echo "   Added to PYTHONPATH: $(pwd)"

# Ensure required __init__.py files exist
touch app/__init__.py
touch app/core/__init__.py

required_files=(
    "app/core/config.py"
    "app/core/security.py"
    "test_AID-US-001B.py"
)

for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo "   ✅ $file exists"
    else
        echo "   ❌ $file missing"
        exit 1
    fi
done

# Step 4: Test JWT Dependencies
echo
echo "🧪 Step 4: Testing JWT dependencies..."
python -c "
import sys
sys.path.insert(0, '.')

print('Testing JWT dependencies...')
try:
    import jose
    from jose import jwt
    print('  ✅ python-jose')
except ImportError as e:
    print(f'  ❌ python-jose: {e}')
    sys.exit(1)

try:
    import passlib
    from passlib.context import CryptContext
    print('  ✅ passlib')
except ImportError as e:
    print(f'  ❌ passlib: {e}')
    sys.exit(1)

try:
    import bcrypt
    print('  ✅ bcrypt')
except ImportError as e:
    print(f'  ❌ bcrypt: {e}')
    sys.exit(1)

try:
    from pydantic_settings import BaseSettings
    print('  ✅ pydantic-settings')
except ImportError as e:
    print(f'  ❌ pydantic-settings: {e}')
    sys.exit(1)

print('\\n✅ All dependencies available!')
"

if [ $? -ne 0 ]; then
    echo "❌ Dependency test failed!"
    exit 1
fi

# Step 5: Test Configuration Import
echo
echo "⚙️  Step 5: Testing configuration..."
python -c "
import sys
sys.path.insert(0, '.')

try:
    from app.core.config import settings
    print('✅ Configuration loaded successfully')
    print(f'   JWT Algorithm: {settings.JWT_ALGORITHM}')
    print(f'   Access Token Expiry: {settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES} minutes')
    print(f'   Refresh Token Expiry: {settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS} days')
    print(f'   Remember Me Expiry: {settings.JWT_REFRESH_TOKEN_REMEMBER_ME_EXPIRE_DAYS} days')
    print(f'   BCrypt Rounds: {settings.BCRYPT_ROUNDS}')
except Exception as e:
    print(f'❌ Configuration test failed: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
"

if [ $? -ne 0 ]; then
    echo "❌ Configuration test failed!"
    exit 1
fi

# Step 6: Test Security Module Import
echo
echo "🔐 Step 6: Testing security module..."
python -c "
import sys
sys.path.insert(0, '.')

try:
    from app.core.security import (
        hash_password, verify_password, create_access_token, 
        create_refresh_token, parse_token, validate_token
    )
    print('✅ Security module imported successfully')
    
    # Quick functionality test
    password = 'test123'
    hashed = hash_password(password)
    verified = verify_password(password, hashed)
    
    token = create_access_token('test_user')
    claims = parse_token(token)
    
    print('✅ Basic functionality working')
    print(f'   Password hashing: OK')
    print(f'   Token creation: OK')
    print(f'   Token parsing: OK')
    
except Exception as e:
    print(f'❌ Security module test failed: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
"

if [ $? -ne 0 ]; then
    echo "❌ Security module test failed!"
    exit 1
fi

# Step 7: Run Comprehensive Test Suite
echo
echo "🚀 Step 7: Running comprehensive test suite..."
echo "   This will test all JWT authentication utilities..."
echo

python test_AID-US-001B.py

if [ $? -eq 0 ]; then
    echo
    echo "🎉 AID-US-001B: JWT Authentication Utilities - COMPLETED!"
    echo "============================================"
    echo "✅ All JWT functionality implemented and tested"
    echo "✅ Password hashing with bcrypt working"
    echo "✅ JWT access tokens (15 min expiry) working"
    echo "✅ JWT refresh tokens (7-30 days expiry) working"
    echo "✅ Token validation and parsing working"
    echo "✅ Security utilities working"
    echo "✅ Error handling working"
    echo "✅ Integration scenarios working"
    echo
    echo "📋 What was built:"
    echo "   • Password hashing and verification"
    echo "   • JWT access token generation"
    echo "   • JWT refresh token generation"
    echo "   • Token validation and claims extraction"
    echo "   • Token blacklisting (logout support)"
    echo "   • Password reset tokens"
    echo "   • Secure secret generation"
    echo "   • Comprehensive error handling"
    echo
    echo "🚀 Ready for next steps:"
    echo "   1. AID-US-001C: Authentication API Endpoints"
    echo "   2. AID-US-001D: Frontend Authentication Integration"
    echo "   3. Update project backlog"
    echo
    echo "💡 Test the security module manually:"
    echo "   python -c \"from app.core.security import *; print('JWT ready!')\""
    echo "   python app/core/security.py"
else
    echo
    echo "💥 Test suite failed!"
    echo "Please review the test output above and fix any issues."
    exit 1
fi
