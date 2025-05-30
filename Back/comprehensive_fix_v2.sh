#!/bin/bash

# Updated Comprehensive Fix Script for AID-001-F Python Import Issues
# This version handles PostgreSQL dependency issues

set -e  # Exit on first error

echo "🔧 AID-001-F: Comprehensive Import Fix (v2)"
echo "==========================================="

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

# Step 2: Handle PostgreSQL Dependency Issue
echo
echo "🔧 Step 2: Handling PostgreSQL dependencies..."
echo "   Detected PostgreSQL installation issue (pg_config not found)"
echo "   Installing dependencies without PostgreSQL drivers for testing..."

# Install dependencies excluding problematic PostgreSQL packages
pip install --upgrade pip --quiet

# Install core dependencies first
echo "   Installing core dependencies..."
pip install fastapi==0.104.1 --quiet
pip install uvicorn[standard]==0.24.0 --quiet
pip install sqlalchemy==2.0.23 --quiet
pip install alembic==1.12.1 --quiet
pip install pydantic==2.5.0 --quiet
pip install pydantic-settings==2.1.0 --quiet
pip install python-dotenv==1.0.0 --quiet
pip install python-jose[cryptography]==3.3.0 --quiet
pip install passlib[bcrypt]==1.7.4 --quiet

echo "✅ Core dependencies installed (PostgreSQL drivers skipped for now)"

# Step 3: File Structure
echo
echo "📁 Step 3: Ensuring proper file structure..."
required_dirs=(
    "app"
    "app/core"
    "app/models"
    "alembic"
    "alembic/versions"
)

for dir in "${required_dirs[@]}"; do
    if [ ! -d "$dir" ]; then
        mkdir -p "$dir"
        echo "   Created directory: $dir"
    fi
done

required_files=(
    "app/__init__.py"
    "app/core/__init__.py"
    "app/models/__init__.py"
)

for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        touch "$file"
        echo "   Created file: $file"
    else
        echo "   ✅ $file exists"
    fi
done

# Step 4: Setup Testing Configuration
echo
echo "⚙️  Step 4: Setting up testing configuration..."

# Backup original config if needed
if [ -f "app/core/config.py" ] && [ ! -f "app/core/config_original.py" ]; then
    cp app/core/config.py app/core/config_original.py
    echo "   ✅ Backed up original config"
fi

# Use testing config temporarily
if [ -f "app/core/config_testing.py" ]; then
    cp app/core/config_testing.py app/core/config.py
    echo "   ✅ Using testing configuration (SQLite instead of PostgreSQL)"
fi

# Backup and use testing alembic configuration
if [ -f "alembic.ini" ] && [ ! -f "alembic_original.ini" ]; then
    cp alembic.ini alembic_original.ini
    echo "   ✅ Backed up original alembic.ini"
fi

if [ -f "alembic_testing.ini" ]; then
    cp alembic_testing.ini alembic.ini
    echo "   ✅ Using testing alembic configuration (SQLite)"
fi

# Create aiosqlite installation for async SQLite support
echo "   Installing SQLite async support..."
pip install aiosqlite --quiet

# Backup and use compatible models
if [ -f "app/models/refresh_token.py" ] && [ ! -f "app/models/refresh_token_original.py" ]; then
    cp app/models/refresh_token.py app/models/refresh_token_original.py
    echo "   ✅ Backed up original refresh_token model"
fi

if [ -f "app/models/refresh_token_compatible.py" ]; then
    cp app/models/refresh_token_compatible.py app/models/refresh_token.py
    echo "   ✅ Using SQLite-compatible refresh_token model (String instead of INET)"
fi

# Step 5: Python Path
echo
echo "🛤️  Step 5: Setting up Python path..."
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
echo "   Added to PYTHONPATH: $(pwd)"

# Step 6: Test Critical Imports
echo
echo "🧪 Step 6: Testing critical imports..."
python -c "
import sys
sys.path.insert(0, '.')

print('Testing basic imports...')
try:
    import sqlalchemy
    print('  ✅ SQLAlchemy')
except ImportError as e:
    print(f'  ❌ SQLAlchemy: {e}')
    sys.exit(1)

try:
    from pydantic_settings import BaseSettings
    print('  ✅ Pydantic Settings')
except ImportError as e:
    print(f'  ❌ Pydantic Settings: {e}')
    sys.exit(1)

print('Testing app imports...')
try:
    import app
    print('  ✅ app module')
except ImportError as e:
    print(f'  ❌ app module: {e}')
    sys.exit(1)

try:
    import app.core.config
    print('  ✅ app.core.config')
except ImportError as e:
    print(f'  ❌ app.core.config: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    import app.core.database
    print('  ✅ app.core.database')
except ImportError as e:
    print(f'  ❌ app.core.database: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    from app.core.database import Base
    print('  ✅ Base class')
except ImportError as e:
    print(f'  ❌ Base class: {e}')
    sys.exit(1)

print('Testing model imports...')
try:
    from app.models import User, RefreshToken, Role, Department, LLMConfiguration, DepartmentQuota, UsageLog
    print('  ✅ All models imported successfully!')
    print(f'  Models: {[cls.__name__ for cls in [User, RefreshToken, Role, Department, LLMConfiguration, DepartmentQuota, UsageLog]]}')
except ImportError as e:
    print(f'  ❌ Model import failed: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)

print('\\n🎉 All imports successful!')
"

echo
if [ $? -eq 0 ]; then
    echo "✅ All import tests passed!"
    echo
    echo "🎯 Ready to run tests:"
    echo "   ./run_tests_AID-001-F.sh"
    echo
    echo "📝 Testing Environment Setup Complete!"
    echo "   ✅ Models can be imported successfully"
    echo "   ✅ Using SQLite for testing (no PostgreSQL required)"
    echo "   ✅ Ready for migration testing"
    echo
    echo "🔧 To install PostgreSQL later (for production):"
    echo "   brew install postgresql"
    echo "   pip install psycopg2-binary"
    echo "   # Then restore original configurations:"
    echo "   mv app/core/config_original.py app/core/config.py"
    echo "   mv alembic_original.ini alembic.ini"
    echo "   mv app/models/refresh_token_original.py app/models/refresh_token.py"
    echo
    echo "🚀 Next steps:"
    echo "   1. Run: ./run_tests_AID-001-F.sh"
    echo "   2. Test migration generation: alembic revision --autogenerate -m 'Initial tables'"
else
    echo "❌ Import tests failed!"
    echo
    echo "🔍 For detailed diagnosis, run:"
    echo "   python advanced_diagnostic.py"
    echo
    echo "📋 Common solutions:"
    echo "   1. Install missing dependencies"
    echo "   2. Check for syntax errors in model files"
    echo "   3. Verify Python version compatibility"
fi
