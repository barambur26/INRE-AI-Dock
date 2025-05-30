#!/bin/bash

# =============================================================================
# AI Dock App - Test Setup Script
# =============================================================================
# This script sets up the test environment and makes scripts executable
# =============================================================================

echo "Setting up AI Dock App Test Environment..."
echo "==========================================="

# Make test scripts executable
echo "Making test scripts executable..."

if [[ -f "tests/integration/test_AID-001-E_alembic_setup.sh" ]]; then
    chmod +x tests/integration/test_AID-001-E_alembic_setup.sh
    echo "✅ Made test_AID-001-E_alembic_setup.sh executable"
else
    echo "❌ test_AID-001-E_alembic_setup.sh not found"
fi

if [[ -f "run_tests.sh" ]]; then
    chmod +x run_tests.sh
    echo "✅ Made run_tests.sh executable"
else
    echo "❌ run_tests.sh not found"
fi

echo ""
echo "Test environment setup complete!"
echo ""
echo "Available commands:"
echo "  ./run_tests.sh --help              Show help"
echo "  ./run_tests.sh --list              List available tests"
echo "  ./run_tests.sh AID-001-E           Run Alembic setup test"
echo "  ./run_tests.sh --integration       Run all integration tests"
echo ""
echo "Direct test execution:"
echo "  ./tests/integration/test_AID-001-E_alembic_setup.sh"
