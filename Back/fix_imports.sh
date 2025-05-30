#!/bin/bash

# Quick Fix Script for Python Import Issues in AID-001-F Tests
# This addresses the "Cannot import Python models" error

echo "=== AID-001-F: Python Import Fix ==="
echo "Current directory: $(pwd)"

# Check if we're in the right directory
if [ ! -f "app/models/user.py" ]; then
    echo "❌ Error: Not in the backend directory. Please run from:"
    echo "   cd /Users/blas/Desktop/INRE/INRE-AI-Dock/Back"
    exit 1
fi

echo "✅ In correct backend directory"

# Activate virtual environment
if [ -d "venv" ]; then
    echo "🔄 Activating virtual environment..."
    source venv/bin/activate
    echo "✅ Virtual environment activated"
fi

# Install missing dependencies if needed
echo "🔍 Checking Python dependencies..."
pip install -r requirements.txt --quiet

# Create __init__.py files if missing
echo "🔧 Ensuring __init__.py files exist..."
touch app/__init__.py
touch app/core/__init__.py
touch app/models/__init__.py

# Set Python path to include current directory
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
echo "✅ Added current directory to PYTHONPATH: $(pwd)"

# Test the import
echo "🧪 Testing Python model imports..."
python -c "
import sys
sys.path.insert(0, '.')
try:
    from app.models import User, RefreshToken, Role, Department, LLMConfiguration, DepartmentQuota, UsageLog
    print('✅ All models imported successfully!')
    print('Models available:', [User.__name__, RefreshToken.__name__, Role.__name__, Department.__name__, LLMConfiguration.__name__, DepartmentQuota.__name__, UsageLog.__name__])
except ImportError as e:
    print('❌ Import error:', e)
    import traceback
    traceback.print_exc()
except Exception as e:
    print('❌ Other error:', e)
    import traceback
    traceback.print_exc()
"

if [ $? -eq 0 ]; then
    echo
    echo "🎉 Python import issue fixed!"
    echo "You can now run the tests successfully:"
    echo "   ./run_tests_AID-001-F.sh"
else
    echo
    echo "❌ Import issue persists. Run the debug script for more details:"
    echo "   python debug_imports.py"
fi
