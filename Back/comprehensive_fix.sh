#!/bin/bash

# Comprehensive Fix Script for AID-001-F Python Import Issues
# This script addresses all common import problems

set -e  # Exit on first error

echo "🔧 AID-001-F: Comprehensive Import Fix"
echo "======================================"

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

# Step 2: Install Dependencies
echo
echo "📦 Step 2: Installing/updating dependencies..."
echo "   This may take a moment..."
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
echo "✅ Dependencies installed"

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

# Step 4: Python Path
echo
echo "🛤️  Step 4: Setting up Python path..."
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
echo "   Added to PYTHONPATH: $(pwd)"

# Step 5: Test Critical Imports
echo
echo "🧪 Step 5: Testing critical imports..."
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
    print('  Full traceback:')
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    import app.core.database
    print('  ✅ app.core.database')
except ImportError as e:
    print(f'  ❌ app.core.database: {e}')
    print('  Full traceback:')
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
    print('  Full traceback:')
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
    echo "🔧 Or run migration commands:"
    echo "   alembic revision --autogenerate -m 'Initial tables'"
    echo "   alembic upgrade head"
    echo
    echo "📝 Environment setup complete!"
    echo "   Python path: $PYTHONPATH"
    echo "   Virtual env: $(which python)"
else
    echo "❌ Import tests failed!"
    echo
    echo "🔍 For detailed diagnosis, run:"
    echo "   python advanced_diagnostic.py"
    echo
    echo "📋 Common solutions:"
    echo "   1. Ensure PostgreSQL is installed (even if not running for imports)"
    echo "   2. Check for syntax errors in model files"
    echo "   3. Verify all dependencies are installed: pip install -r requirements.txt"
    echo "   4. Check that app/core/config.py has valid configuration"
fi
