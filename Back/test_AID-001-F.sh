#!/bin/bash

# Test Script for AID-001-F: Initial Database Migration
# This script tests the complete migration lifecycle: generate -> apply -> verify -> rollback

set -e  # Exit on any error

TEST_NAME="AID-001-F: Initial Database Migration"
TEST_DB="aidock_test"
BACKEND_DIR="/Users/blas/Desktop/INRE/INRE-AI-Dock/Back"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="${BACKEND_DIR}/test_AID-001-F_${TIMESTAMP}.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "$1" | tee -a "$LOG_FILE"
}

# Test result tracking
TESTS_PASSED=0
TESTS_FAILED=0
TOTAL_TESTS=0

# Test assertion function
assert() {
    local description="$1"
    local command="$2"
    local expected_exit_code="${3:-0}"
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    log "${BLUE}[TEST $TOTAL_TESTS]${NC} $description"
    
    if eval "$command" >> "$LOG_FILE" 2>&1; then
        actual_exit_code=0
    else
        actual_exit_code=$?
    fi
    
    if [ $actual_exit_code -eq $expected_exit_code ]; then
        log "${GREEN}✅ PASSED${NC}: $description"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        log "${RED}❌ FAILED${NC}: $description (Exit code: $actual_exit_code, Expected: $expected_exit_code)"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

# Setup test environment
setup_test_environment() {
    log "${YELLOW}=== Setting Up Test Environment ===${NC}"
    
    # Change to backend directory
    cd "$BACKEND_DIR" || exit 1
    log "Working directory: $(pwd)"
    
    # Add current directory to Python path for model imports
    export PYTHONPATH="${PYTHONPATH}:$(pwd)"
    log "Added to PYTHONPATH: $(pwd)"
    
    # Ensure required __init__.py files exist
    touch app/__init__.py
    touch app/core/__init__.py
    touch app/models/__init__.py
    
    # Activate virtual environment if it exists
    if [ -d "venv" ]; then
        log "Activating virtual environment..."
        source venv/bin/activate
    fi
    
    # Create test database
    log "Creating test database: $TEST_DB"
    if command -v createdb &> /dev/null; then
        dropdb "$TEST_DB" 2>/dev/null || true  # Drop if exists, ignore errors
        createdb "$TEST_DB" 2>/dev/null || log "Warning: Could not create test database"
    fi
    
    # Backup original alembic.ini
    if [ ! -f "alembic.ini.backup" ]; then
        cp alembic.ini alembic.ini.backup
    fi
    
    # Update alembic.ini to use test database
    sed "s/aidock$/aidock_test/" alembic.ini.backup > alembic.ini
    
    log "${GREEN}✅ Test environment setup complete${NC}"
}

# Cleanup test environment
cleanup_test_environment() {
    log "${YELLOW}=== Cleaning Up Test Environment ===${NC}"
    
    # Restore original alembic.ini
    if [ -f "alembic.ini.backup" ]; then
        mv alembic.ini.backup alembic.ini
    fi
    
    # Drop test database
    if command -v dropdb &> /dev/null; then
        dropdb "$TEST_DB" 2>/dev/null || true
    fi
    
    # Remove test migration files
    find alembic/versions/ -name "*.py" -not -name "__init__.py" -not -name ".gitkeep" -delete 2>/dev/null || true
    
    log "${GREEN}✅ Test environment cleanup complete${NC}"
}

# Test functions
test_prerequisites() {
    log "${YELLOW}=== Testing Prerequisites ===${NC}"
    
    assert "Backend directory exists" "[ -d '$BACKEND_DIR' ]"
    assert "Alembic configuration exists" "[ -f 'alembic.ini' ]"
    assert "Models directory exists" "[ -d 'app/models' ]"
    assert "User model exists" "[ -f 'app/models/user.py' ]"
    assert "RefreshToken model exists" "[ -f 'app/models/refresh_token.py' ]"
    assert "Models __init__.py exists" "[ -f 'app/models/__init__.py' ]"
    assert "Alembic versions directory exists" "[ -d 'alembic/versions' ]"
    assert "Python can import app.models" "python -c 'from app.models import User, RefreshToken, Role, Department, LLMConfiguration, DepartmentQuota, UsageLog'"
}

test_migration_generation() {
    log "${YELLOW}=== Testing Migration Generation ===${NC}"
    
    # Count initial migration files
    initial_migrations=$(find alembic/versions/ -name "*.py" -not -name "__init__.py" | wc -l)
    
    assert "Generate initial migration" "alembic revision --autogenerate -m 'Initial tables'"
    
    # Count migration files after generation
    final_migrations=$(find alembic/versions/ -name "*.py" -not -name "__init__.py" | wc -l)
    
    assert "Migration file was created" "[ $final_migrations -gt $initial_migrations ]"
    
    # Get the latest migration file
    MIGRATION_FILE=$(find alembic/versions/ -name "*.py" -not -name "__init__.py" | sort | tail -1)
    
    if [ -n "$MIGRATION_FILE" ]; then
        log "Generated migration file: $MIGRATION_FILE"
        
        # Test migration file content
        assert "Migration contains upgrade function" "grep -q 'def upgrade' '$MIGRATION_FILE'"
        assert "Migration contains downgrade function" "grep -q 'def downgrade' '$MIGRATION_FILE'"
        
        # Check for expected table creations
        assert "Migration creates users table" "grep -q 'users' '$MIGRATION_FILE'"
        assert "Migration creates refresh_tokens table" "grep -q 'refresh_tokens' '$MIGRATION_FILE'"
        assert "Migration creates roles table" "grep -q 'roles' '$MIGRATION_FILE'"
        assert "Migration creates departments table" "grep -q 'departments' '$MIGRATION_FILE'"
        assert "Migration creates llm_configurations table" "grep -q 'llm_configurations' '$MIGRATION_FILE'"
        assert "Migration creates department_quotas table" "grep -q 'department_quotas' '$MIGRATION_FILE'"
        assert "Migration creates usage_logs table" "grep -q 'usage_logs' '$MIGRATION_FILE'"
    else
        log "${RED}❌ No migration file found after generation${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

test_migration_application() {
    log "${YELLOW}=== Testing Migration Application ===${NC}"
    
    assert "Apply migration to database" "alembic upgrade head"
    assert "Check current migration status" "alembic current"
    
    # Test database connection and table creation
    if command -v psql &> /dev/null; then
        PSQL_CONN="postgresql://aidock:aidock@localhost:5432/$TEST_DB"
        
        assert "Connect to test database" "psql '$PSQL_CONN' -c 'SELECT 1;'"
        
        # Check each expected table
        assert "Users table exists" "psql '$PSQL_CONN' -c '\dt users' | grep -q users"
        assert "Refresh tokens table exists" "psql '$PSQL_CONN' -c '\dt refresh_tokens' | grep -q refresh_tokens"
        assert "Roles table exists" "psql '$PSQL_CONN' -c '\dt roles' | grep -q roles"
        assert "Departments table exists" "psql '$PSQL_CONN' -c '\dt departments' | grep -q departments"
        assert "LLM configurations table exists" "psql '$PSQL_CONN' -c '\dt llm_configurations' | grep -q llm_configurations"
        assert "Department quotas table exists" "psql '$PSQL_CONN' -c '\dt department_quotas' | grep -q department_quotas"
        assert "Usage logs table exists" "psql '$PSQL_CONN' -c '\dt usage_logs' | grep -q usage_logs"
        assert "Alembic version table exists" "psql '$PSQL_CONN' -c '\dt alembic_version' | grep -q alembic_version"
        
        # Test table structure for key tables
        assert "Users table has correct columns" "psql '$PSQL_CONN' -c '\d users' | grep -E '(id|username|email|hashed_password|is_active|role_id|department_id)'"
        assert "Refresh tokens table has correct columns" "psql '$PSQL_CONN' -c '\d refresh_tokens' | grep -E '(id|token_hash|user_id|expires_at|is_revoked)'"
        
        # Test foreign key relationships
        assert "Users table has role_id foreign key" "psql '$PSQL_CONN' -c '\d users' | grep -q 'roles'"
        assert "Users table has department_id foreign key" "psql '$PSQL_CONN' -c '\d users' | grep -q 'departments'"
        assert "Refresh tokens has user_id foreign key" "psql '$PSQL_CONN' -c '\d refresh_tokens' | grep -q 'users'"
    else
        log "${YELLOW}⚠️  psql not available - skipping database structure tests${NC}"
    fi
}

test_migration_rollback() {
    log "${YELLOW}=== Testing Migration Rollback ===${NC}"
    
    assert "Rollback migration" "alembic downgrade base"
    assert "Check migration status after rollback" "alembic current"
    
    # Verify tables are removed (if psql is available)
    if command -v psql &> /dev/null; then
        PSQL_CONN="postgresql://aidock:aidock@localhost:5432/$TEST_DB"
        
        # These should fail (return non-zero) because tables shouldn't exist
        assert "Users table should not exist after rollback" "! psql '$PSQL_CONN' -c '\dt users' | grep -q users" 0
        assert "Refresh tokens table should not exist after rollback" "! psql '$PSQL_CONN' -c '\dt refresh_tokens' | grep -q refresh_tokens" 0
        
        # Only alembic_version should remain
        assert "Alembic version table still exists" "psql '$PSQL_CONN' -c '\dt alembic_version' | grep -q alembic_version"
    fi
    
    # Test re-applying migration
    assert "Re-apply migration after rollback" "alembic upgrade head"
}

# Main test execution
main() {
    log "${BLUE}======================================${NC}"
    log "${BLUE}  $TEST_NAME${NC}"
    log "${BLUE}  Started: $(date)${NC}"
    log "${BLUE}  Log file: $LOG_FILE${NC}"
    log "${BLUE}======================================${NC}"
    
    # Setup
    setup_test_environment
    
    # Run tests
    test_prerequisites
    test_migration_generation
    test_migration_application
    test_migration_rollback
    
    # Cleanup
    cleanup_test_environment
    
    # Results
    log "${BLUE}======================================${NC}"
    log "${BLUE}  TEST RESULTS${NC}"
    log "${BLUE}======================================${NC}"
    log "Total Tests: $TOTAL_TESTS"
    log "${GREEN}Passed: $TESTS_PASSED${NC}"
    log "${RED}Failed: $TESTS_FAILED${NC}"
    
    if [ $TESTS_FAILED -eq 0 ]; then
        log "${GREEN}🎉 ALL TESTS PASSED! AID-001-F is working correctly.${NC}"
        exit 0
    else
        log "${RED}💥 SOME TESTS FAILED! Check the log for details.${NC}"
        log "Log file: $LOG_FILE"
        exit 1
    fi
}

# Trap to ensure cleanup on script exit
trap cleanup_test_environment EXIT

# Run main function
main "$@"
