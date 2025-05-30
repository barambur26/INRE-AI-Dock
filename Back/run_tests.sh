#!/bin/bash

# =============================================================================
# AI Dock App - Test Runner
# =============================================================================
# Simple script to run specific tests or all tests in the test suite
# =============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Function to show usage
show_usage() {
    echo -e "${BLUE}AI Dock App Test Runner${NC}"
    echo ""
    echo "Usage: $0 [OPTION] [TEST_ID]"
    echo ""
    echo "Options:"
    echo "  -h, --help          Show this help message" 
    echo "  -l, --list          List available tests"
    echo "  -a, --all           Run all integration tests"
    echo "  -i, --integration   Run all integration tests"
    echo "  -u, --unit          Run all unit tests (pytest)"
    echo ""
    echo "Test IDs:"
    echo "  AID-001-E          Test Alembic Migration Setup"
    echo ""
    echo "Examples:"
    echo "  $0 AID-001-E       Run specific test"
    echo "  $0 --all           Run all tests"
    echo "  $0 --integration   Run integration tests only"
}

# Function to list available tests
list_tests() {
    echo -e "${BLUE}Available Tests:${NC}"
    echo ""
    echo -e "${YELLOW}Integration Tests:${NC}"
    
    if [[ -d "tests/integration" ]]; then
        find tests/integration -name "test_*.sh" | while read -r test_file; do
            test_name=$(basename "$test_file" .sh)
            test_id=$(echo "$test_name" | grep -o 'AID-[0-9A-Z-]*' || echo "Unknown")
            echo "  $test_id - $test_file"
        done
    else
        echo "  No integration tests found"
    fi
    
    echo ""
    echo -e "${YELLOW}Unit Tests:${NC}"
    if [[ -d "tests/unit" ]]; then
        find tests/unit -name "test_*.py" | while read -r test_file; do
            echo "  $test_file"
        done
    else
        echo "  No unit tests found"
    fi
}

# Function to run integration tests  
run_integration_tests() {
    echo -e "${BLUE}Running Integration Tests...${NC}"
    echo ""
    
    local test_files
    test_files=$(find tests/integration -name "test_*.sh" 2>/dev/null || true)
    
    if [[ -z "$test_files" ]]; then
        echo -e "${YELLOW}No integration tests found${NC}"
        return 0
    fi
    
    local total=0
    local passed=0
    
    while IFS= read -r test_file; do
        if [[ -f "$test_file" ]]; then
            echo -e "${BLUE}Running: $test_file${NC}"
            chmod +x "$test_file"
            
            if "$test_file"; then
                echo -e "${GREEN}✅ $test_file - PASSED${NC}"
                passed=$((passed + 1))
            else
                echo -e "${RED}❌ $test_file - FAILED${NC}"
            fi
            
            total=$((total + 1))
            echo ""
        fi
    done <<< "$test_files"
    
    echo -e "${BLUE}Integration Tests Summary: $passed/$total passed${NC}"
}

# Function to run unit tests
run_unit_tests() {
    echo -e "${BLUE}Running Unit Tests...${NC}"
    
    if [[ -d "tests/unit" ]] && [[ -n "$(ls -A tests/unit)" ]]; then
        python -m pytest tests/unit/ -v
    else
        echo -e "${YELLOW}No unit tests found${NC}"
    fi
}

# Function to run specific test
run_specific_test() {
    local test_id="$1"
    
    # Look for integration test
    local test_file="tests/integration/test_${test_id}_*.sh"
    local found_files
    found_files=$(find tests/integration -name "test_${test_id}_*.sh" 2>/dev/null || true)
    
    if [[ -n "$found_files" ]]; then
        echo -e "${BLUE}Running Test: $test_id${NC}"
        while IFS= read -r file; do
            chmod +x "$file"
            "$file"
        done <<< "$found_files"
    else
        echo -e "${RED}Test not found: $test_id${NC}"
        echo "Available tests:"
        list_tests
        exit 1
    fi
}

# Main execution
main() {
    # Check if we're in the right directory
    if [[ ! -f "alembic.ini" ]] && [[ ! -d "tests" ]]; then
        echo -e "${RED}❌ ERROR: Please run this script from the backend directory${NC}"
        exit 1
    fi
    
    case "${1:-}" in
        -h|--help)
            show_usage
            exit 0
            ;;
        -l|--list)
            list_tests
            exit 0
            ;;
        -a|--all)
            run_integration_tests
            run_unit_tests
            exit 0
            ;;
        -i|--integration)
            run_integration_tests
            exit 0
            ;;
        -u|--unit)
            run_unit_tests
            exit 0
            ;;
        "")
            show_usage
            exit 1
            ;;
        *)
            run_specific_test "$1"
            ;;
    esac
}

main "$@"
