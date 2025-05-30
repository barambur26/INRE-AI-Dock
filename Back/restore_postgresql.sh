#!/bin/bash

# Restore Original PostgreSQL Configuration
# Run this after installing PostgreSQL to switch back from SQLite testing mode

echo "🔄 Restoring Original PostgreSQL Configuration"
echo "============================================="

# Check if we're in the right directory
if [ ! -f "requirements.txt" ] || [ ! -d "app" ]; then
    echo "❌ Error: Please run this script from the backend directory"
    echo "   Expected: /Users/blas/Desktop/INRE/INRE-AI-Dock/Back"
    exit 1
fi

echo "✅ In correct backend directory: $(pwd)"

# Check if backup files exist
missing_backups=()
if [ ! -f "app/core/config_original.py" ]; then
    missing_backups+=("app/core/config_original.py")
fi

if [ ! -f "alembic_original.ini" ]; then
    missing_backups+=("alembic_original.ini")
fi

if [ ! -f "app/models/refresh_token_original.py" ]; then
    missing_backups+=("app/models/refresh_token_original.py")
fi

if [ ${#missing_backups[@]} -gt 0 ]; then
    echo "⚠️  Some backup files are missing:"
    for file in "${missing_backups[@]}"; do
        echo "   - $file"
    done
    echo
    echo "This might mean you haven't run the testing setup yet, or backups were deleted."
    echo "You can still proceed, but original configurations may not be available."
    echo
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Cancelled."
        exit 1
    fi
fi

echo
echo "🔧 Restoring configurations..."

# Restore config.py
if [ -f "app/core/config_original.py" ]; then
    mv app/core/config_original.py app/core/config.py
    echo "✅ Restored app/core/config.py (PostgreSQL configuration)"
else
    echo "⚠️  app/core/config_original.py not found - skipping"
fi

# Restore alembic.ini
if [ -f "alembic_original.ini" ]; then
    mv alembic_original.ini alembic.ini
    echo "✅ Restored alembic.ini (PostgreSQL configuration)"
else
    echo "⚠️  alembic_original.ini not found - skipping"
fi

# Restore refresh_token model
if [ -f "app/models/refresh_token_original.py" ]; then
    mv app/models/refresh_token_original.py app/models/refresh_token.py
    echo "✅ Restored app/models/refresh_token.py (PostgreSQL INET support)"
else
    echo "⚠️  app/models/refresh_token_original.py not found - skipping"
fi

echo
echo "📦 Installing PostgreSQL dependencies..."
source venv/bin/activate 2>/dev/null || true

# Try to install PostgreSQL dependencies
pip install psycopg2-binary asyncpg --quiet

if [ $? -eq 0 ]; then
    echo "✅ PostgreSQL dependencies installed successfully"
else
    echo "❌ Failed to install PostgreSQL dependencies"
    echo "   Make sure PostgreSQL is installed: brew install postgresql"
    echo "   Or install manually: pip install psycopg2-binary asyncpg"
fi

echo
echo "🧪 Testing PostgreSQL configuration..."
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

python -c "
import sys
sys.path.insert(0, '.')

try:
    from app.core.config import settings
    print(f'✅ Configuration loaded')
    print(f'   Database URL: {settings.DATABASE_URL.split('@')[-1]}')
    
    from app.core.database import Base
    print('✅ Database configuration loaded')
    
    from app.models import User, RefreshToken, Role, Department, LLMConfiguration, DepartmentQuota, UsageLog  
    print('✅ All models imported successfully')
    
    print('\\n🎉 PostgreSQL configuration restored successfully!')
    print('\\nNext steps:')
    print('1. Ensure PostgreSQL is running: brew services start postgresql')
    print('2. Create database: createdb aidock')
    print('3. Create user: createuser aidock')
    print('4. Set password: psql -c \"ALTER USER aidock WITH PASSWORD \\'aidock\\';\"')
    print('5. Grant permissions: psql -c \"GRANT ALL PRIVILEGES ON DATABASE aidock TO aidock;\"')
    print('6. Run migrations: alembic upgrade head')
    
except ImportError as e:
    print(f'❌ Configuration test failed: {e}')
    print('\\nYou may need to:')
    print('1. Install PostgreSQL: brew install postgresql')
    print('2. Install dependencies: pip install psycopg2-binary asyncpg')
    print('3. Start PostgreSQL: brew services start postgresql')
    print('4. Create database and user')
except Exception as e:
    print(f'❌ Other error: {e}')
"

echo
echo "============================================="
echo "PostgreSQL Configuration Restore Complete"
echo "============================================="
