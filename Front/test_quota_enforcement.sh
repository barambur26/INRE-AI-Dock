#!/bin/bash

# AID-US-007 Quick Test Runner
# Quick validation script for quota enforcement system

echo "🧪 AID-US-007 Quota Enforcement Quick Test Runner"
echo "=================================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
BACKEND_URL="http://localhost:8000"
FRONTEND_URL="http://localhost:8080"

echo "📋 Testing Configuration:"
echo "Backend URL: $BACKEND_URL"
echo "Frontend URL: $FRONTEND_URL"
echo ""

# Function to check if service is running
check_service() {
    local url=$1
    local name=$2
    
    if curl -s "$url" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ $name is running${NC}"
        return 0
    else
        echo -e "${RED}❌ $name is not accessible at $url${NC}"
        return 1
    fi
}

# Check if services are running
echo "🔍 Checking Service Availability:"
backend_running=0
frontend_running=0

if check_service "$BACKEND_URL/health" "Backend"; then
    backend_running=1
fi

if check_service "$FRONTEND_URL" "Frontend"; then
    frontend_running=1
fi

echo ""

# Backend Tests (if backend is running)
if [ $backend_running -eq 1 ]; then
    echo "🚀 Running Backend Quota Tests:"
    echo "--------------------------------"
    
    # Test 1: Health Check
    echo -n "Test 1: Backend Health Check... "
    if response=$(curl -s "$BACKEND_URL/health" 2>/dev/null); then
        echo -e "${GREEN}PASS${NC}"
    else
        echo -e "${RED}FAIL${NC}"
    fi
    
    # Test 2: Chat Health Check
    echo -n "Test 2: Chat Service Health... "
    if response=$(curl -s "$BACKEND_URL/api/v1/chat/health" 2>/dev/null); then
        if echo "$response" | grep -q "available_models"; then
            echo -e "${GREEN}PASS${NC}"
        else
            echo -e "${YELLOW}PARTIAL - No models configured${NC}"
        fi
    else
        echo -e "${RED}FAIL${NC}"
    fi
    
    # Test 3: Authentication Endpoints
    echo -n "Test 3: Auth Endpoints Available... "
    if response=$(curl -s "$BACKEND_URL/api/v1/auth/health" 2>/dev/null); then
        echo -e "${GREEN}PASS${NC}"
    else
        echo -e "${RED}FAIL${NC}"
    fi
    
    echo ""
else
    echo -e "${YELLOW}⚠️  Skipping backend tests - Backend not accessible${NC}"
    echo ""
fi

# Frontend Tests (basic connectivity)
if [ $frontend_running -eq 1 ]; then
    echo "🌐 Running Frontend Connectivity Tests:"
    echo "---------------------------------------"
    
    # Test 1: Frontend loads
    echo -n "Test 1: Frontend Accessibility... "
    if curl -s "$FRONTEND_URL" > /dev/null 2>&1; then
        echo -e "${GREEN}PASS${NC}"
    else
        echo -e "${RED}FAIL${NC}"
    fi
    
    echo ""
else
    echo -e "${YELLOW}⚠️  Skipping frontend tests - Frontend not accessible${NC}"
    echo ""
fi

# Manual Test Instructions
echo "📖 Manual Testing Instructions:"
echo "==============================="
echo ""
echo "1. 🔐 AUTHENTICATION TEST:"
echo "   - Open: $FRONTEND_URL"
echo "   - Login with test credentials"
echo "   - Verify successful authentication"
echo ""

echo "2. 💬 QUOTA DISPLAY TEST:"
echo "   - Navigate to Chat Interface"
echo "   - Verify QuotaStatusIndicator is visible"
echo "   - Check quota percentage and status"
echo ""

echo "3. 📊 ADMIN MONITORING TEST:"
echo "   - Login as admin user"
echo "   - Go to Admin Settings > Usage Monitor"
echo "   - Verify usage statistics display"
echo ""

echo "4. ⚠️  QUOTA ENFORCEMENT TEST:"
echo "   - Send multiple messages to approach quota limit"
echo "   - Verify warning messages appear at 80%+"
echo "   - Test quota exceeded blocking (if applicable)"
echo ""

echo "5. 🔄 REAL-TIME UPDATES TEST:"
echo "   - Open chat in multiple tabs"
echo "   - Send messages in one tab"
echo "   - Verify quota updates in other tabs"
echo ""

# Test Results Summary
echo "📊 Quick Test Summary:"
echo "====================="
echo ""

if [ $backend_running -eq 1 ] && [ $frontend_running -eq 1 ]; then
    echo -e "${GREEN}✅ Both services are running - Ready for manual testing${NC}"
    echo ""
    echo "📖 Next Steps:"
    echo "1. Follow the manual testing instructions above"
    echo "2. Refer to AID_US_007_COMPREHENSIVE_TESTING_GUIDE.md for detailed test scenarios"
    echo "3. Report any issues using the bug report template in the testing guide"
elif [ $backend_running -eq 1 ]; then
    echo -e "${YELLOW}⚠️  Backend running, but frontend needs to be started${NC}"
    echo "Start frontend with: cd /Front && npm run dev"
elif [ $frontend_running -eq 1 ]; then
    echo -e "${YELLOW}⚠️  Frontend running, but backend needs to be started${NC}"
    echo "Start backend with: cd /Back && uvicorn app.main:app --reload"
else
    echo -e "${RED}❌ Both services need to be started before testing${NC}"
    echo ""
    echo "🚀 Quick Start Commands:"
    echo "Backend: cd /Back && uvicorn app.main:app --reload"
    echo "Frontend: cd /Front && npm run dev"
fi

echo ""
echo "📚 For comprehensive testing, see:"
echo "   AID_US_007_COMPREHENSIVE_TESTING_GUIDE.md"
echo ""
echo "🎯 Test completed at: $(date)"
