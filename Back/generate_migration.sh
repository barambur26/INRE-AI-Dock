#!/bin/bash

# Script to generate initial database migration for AI Dock App
# Run this from the backend directory: /Users/blas/Desktop/INRE/INRE-AI-Dock/Back/

echo "=== AI Dock App - Initial Database Migration Generator ==="
echo "Current directory: $(pwd)"
echo

# Check if we're in the right directory
if [ ! -f "alembic.ini" ]; then
    echo "❌ Error: alembic.ini not found. Make sure you're in the backend directory."
    echo "Expected path: /Users/blas/Desktop/INRE/INRE-AI-Dock/Back/"
    exit 1
fi

echo "✅ Found alembic.ini - proceeding with migration generation..."
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

# Check PostgreSQL connection (optional - the migration can be generated without DB connection)
echo "🔍 Checking PostgreSQL connection..."
if command -v pg_isready &> /dev/null; then
    if pg_isready -h localhost -p 5432 -U aidock -d aidock 2>/dev/null; then
        echo "✅ PostgreSQL is ready"
    else
        echo "⚠️  PostgreSQL connection failed - migration will still be generated"
        echo "   Make sure PostgreSQL is running before applying the migration"
    fi
else
    echo "⚠️  pg_isready not found - skipping connection check"
fi

echo

# Generate the migration
echo "🚀 Generating initial database migration..."
echo "Command: alembic revision --autogenerate -m 'Initial tables'"
echo

alembic revision --autogenerate -m "Initial tables"

if [ $? -eq 0 ]; then
    echo
    echo "✅ Migration generated successfully!"
    echo
    echo "📁 Generated migration file location:"
    ls -la alembic/versions/*.py 2>/dev/null | tail -1
    echo
    echo "🔍 Next steps:"
    echo "1. Review the generated migration file"
    echo "2. Run 'alembic upgrade head' to apply the migration"
    echo "3. Verify tables were created in your PostgreSQL database"
else
    echo
    echo "❌ Migration generation failed!"
    echo "Check the error messages above and ensure:"
    echo "- All Python dependencies are installed"
    echo "- Models are properly imported"
    echo "- Database connection string is correct (in alembic.ini)"
fi

echo
echo "=== Migration Generation Complete ==="
