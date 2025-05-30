#!/bin/bash

# Integration Test for AID-001-F: Initial Database Migration
# This test follows the same pattern as existing integration tests

TEST_NAME="AID-001-F: Initial Database Migration"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"
TEST_DB="aidock_test_integration"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "============================================"
echo "Integration Test: $TEST_NAME"
echo "Backend Directory: $BACKEND_DIR"
echo "============================================"

# Change to backend directory
cd "$BACKEND_DIR" || exit 1

# Test Results
PASSED=0
FAILED=0

# Test function
test_step() {
    local description="$1"
    local command="$2"
    
    echo -n "Testing: $description... "
    
    if eval "$command" >/dev/null 2>&1; then
        echo -e "${GREEN}PASSED${NC}"
        PASSED=$((PASSED + 1))
        return 0
    else
        echo -e "${RED}FAILED${NC}"
        FAILED=$((FAILED + 1))
        return 1
    fi
}

# Setup test environment
setup_test() {
    echo "Setting up test environment..."
    
    # Add current directory to Python path for model imports
    export PYTHONPATH="${PYTHONPATH}:$(pwd)"
    
    # Ensure required __init__.py files exist
    touch app/__init__.py
    touch app/core/__init__.py
    touch app/models/__init__.py
    
    # Activate virtual environment
    if [ -d "venv" ]; then
        source venv/bin/activate
    fi
    
    # Create test database
    dropdb "$TEST_DB" 2>/dev/null || true
    createdb "$TEST_DB" 2>/dev/null || echo "Warning: Could not create test database"
    
    # Backup and modify alembic.ini
    cp alembic.ini alembic.ini.test_backup
    sed "s/aidock$/aidock_test_integration/" alembic.ini.test_backup > alembic.ini
}

# Cleanup test environment
cleanup_test() {
    echo "Cleaning up test environment..."
    
    # Restore alembic.ini
    if [ -f "alembic.ini.test_backup" ]; then
        mv alembic.ini.test_backup alembic.ini
    fi
    
    # Drop test database
    dropdb "$TEST_DB" 2>/dev/null || true
    
    # Remove test migration files
    find alembic/versions/ -name "*.py" -not -name "__pycache__" -not -name ".gitkeep" -delete 2>/dev/null || true
}

# Run tests
run_tests() {
    echo "Running integration tests..."
    echo
    
    # Test 1: Prerequisites
    test_step "Backend directory structure" "[ -d app/models ] && [ -f app/models/user.py ]"
    test_step "Alembic configuration" "[ -f alembic.ini ] && [ -d alembic/versions ]"
    test_step "Python can import models" "python -c 'from app.models import User, RefreshToken'"
    
    # Test 2: Migration Generation
    test_step "Generate migration file" "alembic revision --autogenerate -m 'Test initial tables'"
    test_step "Migration file was created" "[ \$(find alembic/versions/ -name '*.py' -not -name '__pycache__' | wc -l) -gt 0 ]"
    
    # Get migration file for content testing
    MIGRATION_FILE=$(find alembic/versions/ -name "*.py" -not -name "__pycache__" | head -1)
    if [ -n "$MIGRATION_FILE" ]; then
        test_step "Migration contains upgrade function" "grep -q 'def upgrade' '$MIGRATION_FILE'"
        test_step "Migration contains table creations" "grep -q 'create_table' '$MIGRATION_FILE'"
        test_step "Migration creates users table" "grep -q 'users' '$MIGRATION_FILE'"
        test_step "Migration creates refresh_tokens table" "grep -q 'refresh_tokens' '$MIGRATION_FILE'"
    fi
    
    # Test 3: Migration Application
    test_step "Apply migration to database" "alembic upgrade head"
    test_step "Check migration status" "alembic current | grep -q '[0-9a-f]'"
    
    # Test 4: Database Structure (if psql available)
    if command -v psql >/dev/null 2>&1; then
        PSQL_CONN="postgresql://aidock:aidock@localhost:5432/$TEST_DB"
        test_step "Connect to test database" "psql '$PSQL_CONN' -c 'SELECT 1;'"
        test_step "Users table exists" "psql '$PSQL_CONN' -c '\\dt users' | grep -q users"
        test_step "Refresh tokens table exists" "psql '$PSQL_CONN' -c '\\dt refresh_tokens' | grep -q refresh_tokens"
        test_step "Foreign key relationships exist" "psql '$PSQL_CONN' -c '\\d users' | grep -q 'Foreign-key'"
    fi
    
    # Test 5: Migration Rollback
    test_step "Rollback migration" "alembic downgrade base"
    test_step "Migration status after rollback" "alembic current"
    
    # Test 6: Re-apply migration
    test_step "Re-apply migration" "alembic upgrade head"
}

# Main execution
main() {
    setup_test
    run_tests
    cleanup_test
    
    echo
    echo "============================================"
    echo "Integration Test Results"
    echo "============================================"
    echo -e "Passed: ${GREEN}$PASSED${NC}"
    echo -e "Failed: ${RED}$FAILED${NC}"
    echo "Total: $((PASSED + FAILED))"
    
    if [ $FAILED -eq 0 ]; then
        echo -e "\n${GREEN}🎉 All integration tests passed!${NC}"
        echo "AID-001-F: Initial Database Migration is working correctly."
        exit 0
    else
        echo -e "\n${RED}💥 Some integration tests failed!${NC}"
        echo "Please check the setup and try again."
        exit 1
    fi
}

# Trap cleanup on exit
trap cleanup_test EXIT

# Run main function
main
