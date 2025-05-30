#!/bin/bash

# AID-US-001E Redis/Celery Setup Validation
echo "🔍 Checking Redis/Celery Dependencies for AID-US-001E"
echo "====================================================="

# Check if Redis is available
echo "📦 Checking Redis availability..."
if command -v redis-server &> /dev/null; then
    echo "✅ Redis server is installed"
    
    # Try to ping Redis
    if redis-cli ping &> /dev/null; then
        echo "✅ Redis is running and accessible"
    else
        echo "⚠️  Redis is installed but not running"
        echo "   To start Redis: redis-server"
    fi
else
    echo "ℹ️  Redis not installed (optional for development)"
    echo "   Background tasks will use in-memory fallback"
fi

# Check if Celery is available  
echo ""
echo "📦 Checking Celery availability..."
if python3 -c "import celery" 2>/dev/null; then
    echo "✅ Celery is available"
else
    echo "ℹ️  Celery not installed (optional for development)"
    echo "   Install with: pip install celery"
fi

# Check if slowapi is available (for rate limiting)
echo ""
echo "📦 Checking slowapi for rate limiting..."
if python3 -c "import slowapi" 2>/dev/null; then
    echo "✅ slowapi is available"
else
    echo "⚠️  slowapi not installed (required for rate limiting)"
    echo "   Install with: pip install slowapi"
fi

echo ""
echo "📋 Summary:"
echo "  • Redis: Optional for production background tasks"
echo "  • Celery: Optional for production background tasks"  
echo "  • slowapi: Required for rate limiting functionality"
echo ""
echo "🚀 For development:"
echo "  • Rate limiting works without Redis (in-memory)"
echo "  • Token cleanup can be manual without Celery"
echo "  • All core security features are functional"
