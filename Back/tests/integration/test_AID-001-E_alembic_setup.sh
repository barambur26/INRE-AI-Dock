#!/bin/bash

# =============================================================================
# AID-001-E: Alembic Migration Setup - Integration Test
# =============================================================================
# This test validates that Alembic is correctly configured for database 
# migrations with proper model detection and database connectivity.
#
# Prerequisites:
# - Virtual environment activated
# - PostgreSQL running with aidock database and user
# - All dependencies installed
# =============================================================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Function to print test headers
print_header() {
    echo -e "${BLUE}======================================================${NC}"
    echo -e "${BLUE} AID-001-E: Alembic Migration Setup Test${NC}"
    echo -e "${BLUE}======================================================${NC}"
    echo "Date: $(date)"
    echo "Directory: $(pwd)"
    echo ""
}

# Function to run a test
run_test() {
    local test_name="$1"
    local test_command="$2"
    local expected_pattern="$3"  # Optional: pattern to check in output
    
    TESTS_RUN=$((TESTS_RUN + 1))
    echo -e "${YELLOW}Test $TESTS_RUN: $test_name${NC}"
    echo "Command: $test_command"
    
    if output=$(eval "$test_command" 2>&1); then
        if [[ -z "$expected_pattern" ]] || echo "$output" | grep -q "$expected_pattern"; then
            echo -e "${GREEN}✅ PASSED${NC}"
            TESTS_PASSED=$((TESTS_PASSED + 1))
            if [[ ! -z "$output" ]]; then
                echo "Output: $output" | head -3
            fi
        else
            echo -e "${RED}❌ FAILED - Expected pattern '$expected_pattern' not found${NC}"
            echo "Output: $output"
            TESTS_FAILED=$((TESTS_FAILED + 1))
        fi
    else
        echo -e "${RED}❌ FAILED - Command execution failed${NC}"
        echo "Error: $output"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
    echo ""
}

# Function to check prerequisites
check_prerequisites() {
    echo -e "${BLUE}Checking Prerequisites...${NC}"
    
    # Check if we're in the right directory
    if [[ ! -f "alembic.ini" ]]; then
        echo -e "${RED}❌ ERROR: alembic.ini not found. Are you in the backend directory?${NC}"
        exit 1
    fi
    
    # Check if virtual environment is activated
    if [[ -z "$VIRTUAL_ENV" ]]; then
        echo -e "${YELLOW}⚠️  WARNING: Virtual environment not detected${NC}"
    else
        echo -e "${GREEN}✅ Virtual environment active: $VIRTUAL_ENV${NC}"
    fi
    
    # Check if alembic is installed
    if ! command -v alembic &> /dev/null; then
        echo -e "${RED}❌ ERROR: Alembic not installed${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Prerequisites check completed${NC}"
    echo ""
}

# Function to print final results
print_results() {
    echo -e "${BLUE}======================================================${NC}"
    echo -e "${BLUE} Test Results Summary${NC}"
    echo -e "${BLUE}======================================================${NC}"
    echo "Total Tests Run: $TESTS_RUN"
    echo -e "Passed: ${GREEN}$TESTS_PASSED${NC}"
    echo -e "Failed: ${RED}$TESTS_FAILED${NC}"
    
    if [[ $TESTS_FAILED -eq 0 ]]; then
        echo -e "${GREEN}🎉 ALL TESTS PASSED! Alembic is properly configured.${NC}"
        echo ""
        echo -e "${BLUE}Next Step:${NC} You can now proceed with AID-001-F (Initial Database Migration)"
        exit 0
    else
        echo -e "${RED}❌ Some tests failed. Please check the configuration.${NC}"
        exit 1
    fi
}

# Function to test file existence
test_file_structure() {
    echo -e "${BLUE}Testing File Structure...${NC}"
    echo ""
    
    local files=(
        "alembic.ini:Alembic main configuration"
        "alembic/env.py:Alembic environment setup"
        "alembic/script.py.mako:Migration script template"
        "alembic/versions/.gitkeep:Versions directory placeholder"
    )
    
    for file_info in "${files[@]}"; do
        IFS=':' read -r file_path description <<< "$file_info"
        if [[ -f "$file_path" ]]; then
            echo -e "${GREEN}✅ $description: $file_path${NC}"
        else
            echo -e "${RED}❌ Missing: $description: $file_path${NC}"
            TESTS_FAILED=$((TESTS_FAILED + 1))
        fi
        TESTS_RUN=$((TESTS_RUN + 1))
    done
    
    if [[ -f "alembic.ini" ]]; then
        TESTS_PASSED=$((TESTS_PASSED + 1))
    fi
    echo ""
}

# Main test execution
main() {
    print_header
    check_prerequisites
    test_file_structure
    
    # Test 1: Alembic help command
    run_test "Alembic Help Command" "alembic --help" "usage: alembic"
    
    # Test 2: Alembic configuration validation
    run_test "Configuration Validation" "alembic list_templates" "generic"
    
    # Test 3: Current migration status
    run_test "Current Migration Status" "alembic current" ""
    
    # Test 4: Model detection (check command)
    run_test "Model Detection" "alembic check" ""
    
    # Test 5: Environment connection test
    run_test "Database Connection Test" "timeout 10s alembic show current" ""
    
    # Test 6: Migration generation dry run
    run_test "Migration Generation Test" "alembic revision --autogenerate -m 'Test migration' --sql" "CREATE TABLE"
    
    # Test 7: Configuration file validation
    run_test "Configuration File Content" "grep -q 'postgresql://aidock:aidock@localhost:5432/aidock' alembic.ini" ""
    
    # Test 8: Environment file validation  
    run_test "Environment File Validation" "python -c 'import alembic.env'" ""
    
    print_results
}

# Handle script interruption
trap 'echo -e "\n${RED}Test interrupted by user${NC}"; exit 1' INT

# Run main function
main "$@"
