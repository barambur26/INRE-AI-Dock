#!/bin/bash

# Transition to PostgreSQL after PostgreSQL installation
# Run this after installing PostgreSQL to switch from SQLite testing mode

echo "🔄 Transitioning to PostgreSQL Configuration"
echo "============================================="

# Check if we're in the right directory
if [ ! -f "requirements.txt" ] || [ ! -d "app" ]; then
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
    echo "❌ Virtual environment not found!"
    exit 1
fi

# Step 1: Install PostgreSQL Python dependencies
echo
echo "📦 Step 1: Installing PostgreSQL Python dependencies..."
echo "   Now that PostgreSQL is installed, we can install psycopg2..."

pip install psycopg2-binary==2.9.9 --quiet
if [ $? -eq 0 ]; then
    echo "✅ psycopg2-binary installed successfully"
else
    echo "❌ Failed to install psycopg2-binary"
    echo "   Trying alternative installation..."
    pip install psycopg2-binary --quiet
fi

pip install asyncpg==0.29.0 --quiet
if [ $? -eq 0 ]; then
    echo "✅ asyncpg installed successfully"
else
    echo "❌ Failed to install asyncpg"
fi

# Step 2: Restore original configurations if backups exist
echo
echo "🔧 Step 2: Restoring original PostgreSQL configurations..."

# Restore config.py
if [ -f "app/core/config_original.py" ]; then
    cp app/core/config_original.py app/core/config.py
    echo "✅ Restored app/core/config.py (PostgreSQL configuration)"
else
    echo "⚠️  No backup found - using current configuration"
fi

# Restore alembic.ini
if [ -f "alembic_original.ini" ]; then
    cp alembic_original.ini alembic.ini
    echo "✅ Restored alembic.ini (PostgreSQL configuration)"
else
    echo "⚠️  No backup found - using current configuration"
fi

# Restore refresh_token model
if [ -f "app/models/refresh_token_original.py" ]; then
    cp app/models/refresh_token_original.py app/models/refresh_token.py
    echo "✅ Restored app/models/refresh_token.py (PostgreSQL INET support)"
else
    echo "⚠️  No backup found - using current model"
fi

# Step 3: Set up Python path
echo
echo "🛤️  Step 3: Setting up Python path..."
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
echo "   Added to PYTHONPATH: $(pwd)"

# Step 4: Test imports
echo
echo "🧪 Step 4: Testing Python imports with PostgreSQL..."
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
    import psycopg2
    print('  ✅ psycopg2 (PostgreSQL driver)')
except ImportError as e:
    print(f'  ❌ psycopg2: {e}')
    print('     This is expected if psycopg2 installation failed')

try:
    from pydantic_settings import BaseSettings
    print('  ✅ Pydantic Settings')
except ImportError as e:
    print(f'  ❌ Pydantic Settings: {e}')
    sys.exit(1)

print('Testing app imports...')
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

print('\\n🎉 All imports successful with PostgreSQL!')
"

echo
if [ $? -eq 0 ]; then
    echo "✅ PostgreSQL transition successful!"
    echo
    echo "🎯 Ready to run tests:"
    echo "   ./run_tests_AID-001-F.sh"
    echo
    echo "💾 PostgreSQL Database Setup (if not done yet):"
    echo "   1. Start PostgreSQL: brew services start postgresql"
    echo "   2. Create database: createdb aidock"
    echo "   3. Create user: createuser aidock"
    echo "   4. Set password: psql -c \"ALTER USER aidock WITH PASSWORD 'aidock';\""
    echo "   5. Grant permissions: psql -c \"GRANT ALL PRIVILEGES ON DATABASE aidock TO aidock;\""
    echo
    echo "🔧 Test database connection:"
    echo "   psql postgresql://aidock:aidock@localhost:5432/aidock -c \"SELECT 1;\""
    echo
    echo "🚀 Generate migration:"
    echo "   alembic revision --autogenerate -m \"Initial tables\""
    echo "   alembic upgrade head"
else
    echo "❌ PostgreSQL transition failed!"
    echo
    echo "🔍 Try running the advanced diagnostic:"
    echo "   python advanced_diagnostic.py"
    echo
    echo "🔄 Or use SQLite testing mode:"
    echo "   ./comprehensive_fix_v2.sh"
fi
