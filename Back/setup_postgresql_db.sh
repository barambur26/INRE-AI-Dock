#!/bin/bash

# PostgreSQL Database Setup for AI Dock App
# Run this after installing PostgreSQL to create the database and user

echo "🐘 PostgreSQL Database Setup for AI Dock App"
echo "============================================="

# Check if PostgreSQL is running
if ! pg_isready -q; then
    echo "🔄 Starting PostgreSQL..."
    brew services start postgresql
    
    # Wait a moment for PostgreSQL to start
    sleep 3
    
    if ! pg_isready -q; then
        echo "❌ PostgreSQL failed to start"
        echo "   Try manually: brew services start postgresql"
        exit 1
    fi
fi

echo "✅ PostgreSQL is running"

# Check if database already exists
if psql -lqt | cut -d \| -f 1 | grep -qw aidock; then
    echo "✅ Database 'aidock' already exists"
else
    echo "🔄 Creating database 'aidock'..."
    createdb aidock
    if [ $? -eq 0 ]; then
        echo "✅ Database 'aidock' created successfully"
    else
        echo "❌ Failed to create database"
        exit 1
    fi
fi

# Check if user already exists
if psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='aidock'" | grep -q 1; then
    echo "✅ User 'aidock' already exists"
else
    echo "🔄 Creating user 'aidock'..."
    createuser aidock
    if [ $? -eq 0 ]; then
        echo "✅ User 'aidock' created successfully"
    else
        echo "❌ Failed to create user"
        exit 1
    fi
fi

# Set password for user
echo "🔄 Setting password for user 'aidock'..."
psql -c "ALTER USER aidock WITH PASSWORD 'aidock';" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ Password set for user 'aidock'"
else
    echo "⚠️  Password might already be set"
fi

# Grant permissions
echo "🔄 Granting permissions to user 'aidock'..."
psql -c "GRANT ALL PRIVILEGES ON DATABASE aidock TO aidock;" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ Permissions granted to user 'aidock'"
else
    echo "⚠️  Permissions might already be granted"
fi

# Test connection
echo
echo "🧪 Testing database connection..."
psql postgresql://aidock:aidock@localhost:5432/aidock -c "SELECT 'Connection successful!' AS status;" 2>/dev/null

if [ $? -eq 0 ]; then
    echo "✅ Database connection test successful!"
    echo
    echo "🎯 Database setup complete!"
    echo "   Database: aidock"
    echo "   User: aidock"
    echo "   Password: aidock"
    echo "   Connection: postgresql://aidock:aidock@localhost:5432/aidock"
    echo
    echo "🚀 Next steps:"
    echo "   1. Run: ./transition_to_postgresql.sh"
    echo "   2. Run: ./run_tests_AID-001-F.sh"
    echo "   3. Generate migration: alembic revision --autogenerate -m 'Initial tables'"
else
    echo "❌ Database connection test failed!"
    echo
    echo "🔍 Troubleshooting:"
    echo "   1. Check PostgreSQL is running: pg_isready"
    echo "   2. Check database exists: psql -l | grep aidock"
    echo "   3. Check user exists: psql -c \"\\du\" | grep aidock"
    echo "   4. Try manual connection: psql -U aidock -d aidock -h localhost"
fi
