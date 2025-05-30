#!/bin/bash

# Script to apply the initial database migration for AI Dock App
# Run this AFTER generating the migration with generate_migration.sh

echo "=== AI Dock App - Database Migration Application ==="
echo "Current directory: $(pwd)"
echo

# Check if we're in the right directory
if [ ! -f "alembic.ini" ]; then
    echo "❌ Error: alembic.ini not found. Make sure you're in the backend directory."
    echo "Expected path: /Users/blas/Desktop/INRE/INRE-AI-Dock/Back/"
    exit 1
fi

# Check if migration files exist
if [ ! "$(ls -A alembic/versions/*.py 2>/dev/null)" ]; then
    echo "❌ Error: No migration files found in alembic/versions/"
    echo "Run generate_migration.sh first to create the initial migration."
    exit 1
fi

echo "✅ Found migration files - proceeding with database setup..."
echo

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "🔄 Activating virtual environment..."
    source venv/bin/activate
    echo "✅ Virtual environment activated"
else
    echo "⚠️  Virtual environment not found - make sure dependencies are installed"
fi

echo

# Check PostgreSQL connection
echo "🔍 Checking PostgreSQL connection..."
if command -v pg_isready &> /dev/null; then
    if pg_isready -h localhost -p 5432 -U aidock -d aidock 2>/dev/null; then
        echo "✅ PostgreSQL is ready"
    else
        echo "❌ PostgreSQL connection failed!"
        echo "Please ensure:"
        echo "- PostgreSQL is installed and running"
        echo "- Database 'aidock' exists"
        echo "- User 'aidock' has access to the database"
        echo
        echo "To set up PostgreSQL (if needed):"
        echo "  createdb aidock"
        echo "  createuser aidock"
        echo "  psql -c \"ALTER USER aidock WITH PASSWORD 'aidock';\""
        echo "  psql -c \"GRANT ALL PRIVILEGES ON DATABASE aidock TO aidock;\""
        exit 1
    fi
else
    echo "⚠️  pg_isready not found - attempting migration anyway"
fi

echo

# Show current migration status
echo "📊 Current migration status:"
alembic current

echo

# Apply the migration
echo "🚀 Applying database migration..."
echo "Command: alembic upgrade head"
echo

alembic upgrade head

if [ $? -eq 0 ]; then
    echo
    echo "✅ Migration applied successfully!"
    echo
    echo "📊 New migration status:"
    alembic current
    echo
    echo "🔍 Verifying tables were created..."
    
    # Try to connect and list tables
    if command -v psql &> /dev/null; then
        echo "Tables in database:"
        psql postgresql://aidock:aidock@localhost:5432/aidock -c "\dt" 2>/dev/null || echo "Could not connect to list tables"
    fi
    
    echo
    echo "✅ Database migration completed successfully!"
    echo
    echo "Expected tables created:"
    echo "  - users"
    echo "  - refresh_tokens"  
    echo "  - roles"
    echo "  - departments"
    echo "  - llm_configurations"
    echo "  - department_quotas"
    echo "  - usage_logs"
    echo "  - alembic_version (migration tracking)"
else
    echo
    echo "❌ Migration failed!"
    echo "Check the error messages above for details."
    echo "Common issues:"
    echo "- Database connection problems"
    echo "- Permission issues"
    echo "- Invalid migration file"
fi

echo
echo "=== Migration Application Complete ==="
