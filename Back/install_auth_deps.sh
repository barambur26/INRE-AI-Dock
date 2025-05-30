#!/bin/bash

# Install Authentication Dependencies for AID-US-001B
# This script installs the specific JWT and security packages needed

echo "📦 Installing AID-US-001B Authentication Dependencies"
echo "===================================================="

# Check if we're in virtual environment
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  Warning: Virtual environment not detected"
    echo "   Consider activating: source venv/bin/activate"
fi

echo "🔄 Installing core authentication packages..."

# Install JWT and security packages
pip install python-jose[cryptography]==3.3.0
echo "✅ python-jose installed"

pip install passlib[bcrypt]==1.7.4
echo "✅ passlib installed"

pip install bcrypt==4.1.2
echo "✅ bcrypt installed"

pip install pytest>=8.0.0
echo "✅ pytest installed"

pip install python-multipart==0.0.6
echo "✅ python-multipart installed"

# Install configuration packages
pip install python-dotenv>=1.0.0
pip install pydantic>=2.8.0
pip install pydantic-settings>=2.4.0
echo "✅ Configuration packages installed"

echo
echo "🧪 Testing installed packages..."
python -c "
import sys
try:
    import jose
    print('✅ python-jose imported successfully')
except ImportError as e:
    print(f'❌ python-jose import failed: {e}')

try:
    import passlib
    print('✅ passlib imported successfully')
except ImportError as e:
    print(f'❌ passlib import failed: {e}')

try:
    import bcrypt
    print('✅ bcrypt imported successfully')
except ImportError as e:
    print(f'❌ bcrypt import failed: {e}')

try:
    import pytest
    print('✅ pytest imported successfully')
except ImportError as e:
    print(f'❌ pytest import failed: {e}')
"

echo
echo "📋 Checking package versions..."
pip list | grep -E "(jose|passlib|bcrypt|pytest|pydantic|dotenv)"

echo
echo "🎉 Authentication dependencies installation complete!"
echo "   You can now run: python test_security_direct.py"
