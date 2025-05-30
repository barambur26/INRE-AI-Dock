#!/bin/bash

# Quick SQLAlchemy Compatibility Fix for Python 3.13
# This script updates SQLAlchemy to a compatible version

echo "🔧 Fixing SQLAlchemy Python 3.13 Compatibility Issue"
echo "====================================================="

# Check Python version
python_version=$(python --version)
echo "📍 Python version: $python_version"

# Check if we're in the right directory
if [ ! -f "requirements.txt" ]; then
    echo "❌ Error: requirements.txt not found. Please run from the backend directory."
    exit 1
fi

echo "🔄 Upgrading SQLAlchemy to Python 3.13 compatible version..."

# Upgrade SQLAlchemy and related packages
pip install --upgrade sqlalchemy>=2.0.25
pip install --upgrade alembic>=1.13.0
pip install --upgrade psycopg2-binary>=2.9.9
pip install --upgrade asyncpg>=0.29.0

echo "✅ SQLAlchemy packages upgraded"

# Test that the upgrade worked
echo "🧪 Testing SQLAlchemy import..."
python -c "
import sqlalchemy
print(f'✅ SQLAlchemy version: {sqlalchemy.__version__}')
try:
    from sqlalchemy import create_engine
    print('✅ SQLAlchemy import working')
except Exception as e:
    print(f'❌ SQLAlchemy import failed: {e}')
    exit(1)
"

if [ $? -eq 0 ]; then
    echo "🎉 SQLAlchemy compatibility fix successful!"
    echo "   You should now be able to import the full security module."
else
    echo "❌ SQLAlchemy fix failed. Manual intervention may be needed."
    echo "   Try: pip install --upgrade --force-reinstall sqlalchemy alembic"
fi
