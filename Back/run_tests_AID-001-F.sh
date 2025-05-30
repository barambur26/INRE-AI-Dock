#!/bin/bash

# Test Runner for AID-001-F: Initial Database Migration
# Runs all available tests for the migration functionality

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}======================================================${NC}"
echo -e "${BLUE}  AID-001-F: Initial Database Migration Test Suite${NC}"
echo -e "${BLUE}======================================================${NC}"
echo

# Available tests
TESTS=(
    "bash:test_AID-001-F.sh:Complete Bash Test Suite"
    "python:test_AID-001-F.py:Python Unit Tests"
    "integration:tests/integration/test_AID-001-F_migration.sh:Integration Tests"
)

# Test results
TOTAL_TESTS=${#TESTS[@]}
PASSED_TESTS=0
FAILED_TESTS=0

run_test() {
    local test_type="$1"
    local test_file="$2"
    local test_description="$3"
    
    echo -e "${YELLOW}Running: $test_description${NC}"
    echo "File: $test_file"
    echo "Type: $test_type"
    echo "----------------------------------------"
    
    if [ ! -f "$test_file" ]; then
        echo -e "${RED}❌ Test file not found: $test_file${NC}"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        return 1
    fi
    
    # Make script executable if it's a bash script
    if [[ "$test_type" == "bash" || "$test_type" == "integration" ]]; then
        chmod +x "$test_file"
    fi
    
    # Run the test based on type
    case "$test_type" in
        "bash"|"integration")
            if bash "$test_file"; then
                echo -e "${GREEN}✅ $test_description PASSED${NC}"
                PASSED_TESTS=$((PASSED_TESTS + 1))
                return 0
            else
                echo -e "${RED}❌ $test_description FAILED${NC}"
                FAILED_TESTS=$((FAILED_TESTS + 1))
                return 1
            fi
            ;;
        "python")
            if python "$test_file"; then
                echo -e "${GREEN}✅ $test_description PASSED${NC}"
                PASSED_TESTS=$((PASSED_TESTS + 1))
                return 0
            else
                echo -e "${RED}❌ $test_description FAILED${NC}"
                FAILED_TESTS=$((FAILED_TESTS + 1))
                return 1
            fi
            ;;
        *)
            echo -e "${RED}❌ Unknown test type: $test_type${NC}"
            FAILED_TESTS=$((FAILED_TESTS + 1))
            return 1
            ;;
    esac
}

# Parse command line arguments
TEST_FILTER=""
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --filter)
            TEST_FILTER="$2"
            shift 2
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo
            echo "Options:"
            echo "  --filter TYPE    Run only tests of specific type (bash|python|integration)"
            echo "  --verbose        Show detailed output"
            echo "  --help          Show this help message"
            echo
            echo "Available tests:"
            for test in "${TESTS[@]}"; do
                IFS=':' read -r type file desc <<< "$test"
                echo "  [$type] $desc"
            done
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Change to backend directory
cd "$BACKEND_DIR" || exit 1

# Add current directory to Python path for imports
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
echo "Added to PYTHONPATH: $(pwd)"

echo "Working directory: $(pwd)"
echo "Test filter: ${TEST_FILTER:-"all"}"
echo

# Check prerequisites
echo -e "${BLUE}Checking Prerequisites...${NC}"
echo "----------------------------------------"

# Check virtual environment
if [ -d "venv" ]; then
    echo "✅ Virtual environment found"
    source venv/bin/activate
    echo "✅ Virtual environment activated"
else
    echo "⚠️  Virtual environment not found - make sure dependencies are installed"
fi

# Ensure __init__.py files exist
touch app/__init__.py
touch app/core/__init__.py
touch app/models/__init__.py

# Check PostgreSQL
if command -v psql >/dev/null 2>&1; then
    echo "✅ PostgreSQL client available"
else
    echo "⚠️  PostgreSQL client not found - some tests may skip database checks"
fi

# Check Python imports
if python -c "from app.models import User" >/dev/null 2>&1; then
    echo "✅ Python models can be imported"
else
    echo "❌ Cannot import Python models - check your setup"
    echo
    echo "🔧 Quick fixes to try:"
    echo "   1. Install PostgreSQL dependencies: ./transition_to_postgresql.sh"
    echo "   2. Or use SQLite testing mode: ./comprehensive_fix_v2.sh"
    echo "   3. Or run diagnostic: python advanced_diagnostic.py"
    echo
    echo "💡 If you just installed PostgreSQL, run:"
    echo "   ./setup_postgresql_db.sh"
    echo "   ./transition_to_postgresql.sh"
    echo
    read -p "Continue with tests anyway? Some may fail. (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Exiting. Fix the import issue first."
        exit 1
    fi
fi

echo
echo -e "${BLUE}Running Tests...${NC}"
echo "========================================"

# Run tests
for test in "${TESTS[@]}"; do
    IFS=':' read -r test_type test_file test_description <<< "$test"
    
    # Apply filter if specified
    if [[ -n "$TEST_FILTER" && "$test_type" != "$TEST_FILTER" ]]; then
        continue
    fi
    
    echo
    run_test "$test_type" "$test_file" "$test_description"
    echo
done

# Final results
echo
echo -e "${BLUE}======================================================${NC}"
echo -e "${BLUE}  TEST RESULTS SUMMARY${NC}"
echo -e "${BLUE}======================================================${NC}"
echo "Total Tests: $TOTAL_TESTS"
echo -e "Passed: ${GREEN}$PASSED_TESTS${NC}"
echo -e "Failed: ${RED}$FAILED_TESTS${NC}"

if [ $FAILED_TESTS -eq 0 ]; then
    echo
    echo -e "${GREEN}🎉 ALL TESTS PASSED!${NC}"
    echo -e "${GREEN}AID-001-F: Initial Database Migration is working correctly.${NC}"
    echo
    echo "Next steps:"
    echo "1. Mark AID-001-F as completed in backlog"
    echo "2. Proceed to AID-US-001B (JWT Authentication Utilities)"
    exit 0
else
    echo
    echo -e "${RED}💥 SOME TESTS FAILED!${NC}"
    echo "Please review the failed tests and fix any issues."
    echo
    echo "Common troubleshooting:"
    echo "- Ensure PostgreSQL is running"
    echo "- Check database permissions"
    echo "- Verify virtual environment is activated"
    echo "- Make sure all dependencies are installed"
    exit 1
fi
