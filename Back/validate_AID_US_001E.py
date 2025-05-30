#!/usr/bin/env python3
"""
AID-US-001E Final Validation Script
This script validates all security enhancements and components
"""

import os
import sys
import subprocess
import json
import importlib.util
from pathlib import Path
from datetime import datetime

# Colors for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(title):
    print(f"\n{Colors.BLUE}{Colors.BOLD}{'='*60}")
    print(f"🔒 {title}")
    print(f"{'='*60}{Colors.END}")

def print_success(message):
    print(f"{Colors.GREEN}✅ {message}{Colors.END}")

def print_error(message):
    print(f"{Colors.RED}❌ {message}{Colors.END}")

def print_warning(message):
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.END}")

def print_info(message):
    print(f"{Colors.BLUE}ℹ️  {message}{Colors.END}")

def check_file_exists(file_path, description):
    """Check if a file exists and is readable"""
    if Path(file_path).exists():
        print_success(f"{description}: {file_path}")
        return True
    else:
        print_error(f"{description} missing: {file_path}")
        return False

def check_python_imports(module_path, imports_to_check):
    """Check if Python module can be imported and has required components"""
    try:
        spec = importlib.util.spec_from_file_location("module", module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        missing_imports = []
        for import_name in imports_to_check:
            if not hasattr(module, import_name):
                missing_imports.append(import_name)
        
        if missing_imports:
            print_warning(f"Missing imports in {module_path}: {missing_imports}")
            return False
        else:
            print_success(f"All imports found in {module_path}")
            return True
            
    except Exception as e:
        print_error(f"Cannot import {module_path}: {e}")
        return False

def validate_file_structure():
    """Validate that all required files exist"""
    print_header("Step 1: File Structure Validation")
    
    required_files = {
        "Rate Limiting Middleware": "/Users/blas/Desktop/INRE/INRE-AI-Dock/Back/app/middleware/rate_limit.py",
        "Token Cleanup Tasks": "/Users/blas/Desktop/INRE/INRE-AI-Dock/Back/app/tasks/cleanup.py", 
        "Comprehensive Test Suite": "/Users/blas/Desktop/INRE/INRE-AI-Dock/Back/tests/test_auth.py",
        "Integration Test Script": "/Users/blas/Desktop/INRE/INRE-AI-Dock/Back/test_AID_US_001E.sh",
        "Main Application": "/Users/blas/Desktop/INRE/INRE-AI-Dock/Back/app/main.py",
        "Security Configuration": "/Users/blas/Desktop/INRE/INRE-AI-Dock/Back/app/core/security.py",
        "App Configuration": "/Users/blas/Desktop/INRE/INRE-AI-Dock/Back/app/core/config.py",
    }
    
    all_files_exist = True
    for description, file_path in required_files.items():
        if not check_file_exists(file_path, description):
            all_files_exist = False
    
    return all_files_exist

def validate_python_modules():
    """Validate that Python modules have required components"""
    print_header("Step 2: Python Module Validation")
    
    modules_to_check = {
        "/Users/blas/Desktop/INRE/INRE-AI-Dock/Back/app/middleware/rate_limit.py": [
            "RateLimitMiddleware", "get_rate_limit_stats", "clear_rate_limits", "rate_limit_storage"
        ],
        "/Users/blas/Desktop/INRE/INRE-AI-Dock/Back/app/tasks/cleanup.py": [
            "cleanup_expired_tokens", "cleanup_user_sessions", "security_monitoring_task", "celery_app"
        ],
        "/Users/blas/Desktop/INRE/INRE-AI-Dock/Back/app/core/security.py": [
            "hash_password", "verify_password", "create_access_token", "create_refresh_token", "verify_token"
        ],
    }
    
    all_modules_valid = True
    for module_path, required_imports in modules_to_check.items():
        if not check_python_imports(module_path, required_imports):
            all_modules_valid = False
    
    return all_modules_valid

def validate_configuration():
    """Validate security configuration settings"""
    print_header("Step 3: Security Configuration Validation")
    
    try:
        # Check if we can import and validate config
        sys.path.append("/Users/blas/Desktop/INRE/INRE-AI-Dock/Back")
        
        # Try to import config (may fail due to dependencies)
        config_content = Path("/Users/blas/Desktop/INRE/INRE-AI-Dock/Back/app/core/config.py").read_text()
        
        # Check for required security settings
        required_settings = [
            "RATE_LIMITING_ENABLED",
            "SECURITY_HEADERS_ENABLED", 
            "TOKEN_CLEANUP_ENABLED",
            "JWT_SECRET_KEY",
            "BCRYPT_ROUNDS",
            "PASSWORD_MIN_LENGTH",
            "RATE_LIMIT_LOGIN_REQUESTS",
            "RATE_LIMIT_LOGIN_WINDOW",
        ]
        
        missing_settings = []
        for setting in required_settings:
            if setting not in config_content:
                missing_settings.append(setting)
        
        if missing_settings:
            print_error(f"Missing configuration settings: {missing_settings}")
            return False
        else:
            print_success("All required security settings found in configuration")
            
        # Check security defaults
        security_checks = [
            ("BCRYPT_ROUNDS: int = 12", "Strong password hashing"),
            ("JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15", "Short access token expiry"),
            ("PASSWORD_MIN_LENGTH: int = 8", "Minimum password length"),
            ("RATE_LIMITING_ENABLED: bool = True", "Rate limiting enabled by default"),
            ("SECURITY_HEADERS_ENABLED: bool = True", "Security headers enabled"),
        ]
        
        for check, description in security_checks:
            if check in config_content:
                print_success(f"{description}: {check.split('=')[0].strip()}")
            else:
                print_warning(f"May need review - {description}")
        
        return True
        
    except Exception as e:
        print_error(f"Configuration validation error: {e}")
        return False

def validate_test_suite():
    """Validate the comprehensive test suite"""
    print_header("Step 4: Test Suite Validation")
    
    test_file = "/Users/blas/Desktop/INRE/INRE-AI-Dock/Back/tests/test_auth.py"
    
    if not Path(test_file).exists():
        print_error(f"Test file not found: {test_file}")
        return False
    
    test_content = Path(test_file).read_text()
    
    # Check for required test classes and methods
    required_test_components = [
        "class TestAuthenticationFlow",
        "class TestRateLimiting", 
        "class TestSecurityValidation",
        "class TestTokenCleanup",
        "class TestIntegrationScenarios",
        "def test_successful_login_flow",
        "def test_login_with_remember_me",
        "def test_token_refresh_flow",
        "def test_login_rate_limiting",
        "def test_admin_vs_user_access",
    ]
    
    missing_components = []
    for component in required_test_components:
        if component not in test_content:
            missing_components.append(component)
    
    if missing_components:
        print_error(f"Missing test components: {missing_components}")
        return False
    else:
        print_success("All required test components found")
    
    # Count test methods
    test_methods = test_content.count("def test_")
    print_info(f"Total test methods found: {test_methods}")
    
    if test_methods >= 15:
        print_success("Comprehensive test coverage (15+ test methods)")
        return True
    else:
        print_warning(f"Limited test coverage: {test_methods} test methods")
        return False

def validate_integration_scripts():
    """Validate integration and testing scripts"""
    print_header("Step 5: Integration Scripts Validation")
    
    script_file = "/Users/blas/Desktop/INRE/INRE-AI-Dock/Back/test_AID_US_001E.sh"
    
    if not Path(script_file).exists():
        print_error(f"Integration test script not found: {script_file}")
        return False
    
    script_content = Path(script_file).read_text()
    
    # Check for required test functions
    required_functions = [
        "test_security_features",
        "test_rate_limiting", 
        "test_rate_limit_stats",
        "test_secure_auth_flow",
        "test_remember_me",
        "test_admin_functionality",
        "test_input_validation",
        "test_token_refresh_security",
    ]
    
    missing_functions = []
    for func in required_functions:
        if func not in script_content:
            missing_functions.append(func)
    
    if missing_functions:
        print_error(f"Missing test functions in integration script: {missing_functions}")
        return False
    else:
        print_success("All required integration test functions found")
        return True

def check_dependencies():
    """Check if required dependencies are available"""
    print_header("Step 6: Dependencies Check")
    
    required_packages = [
        "fastapi",
        "uvicorn", 
        "pydantic",
        "sqlalchemy",
        "bcrypt",
        "python-jose",
        "pytest",
        "httpx",
    ]
    
    optional_packages = [
        "redis",
        "celery",
        "slowapi",
    ]
    
    missing_required = []
    missing_optional = []
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print_success(f"Required: {package}")
        except ImportError:
            missing_required.append(package)
            print_error(f"Missing required: {package}")
    
    for package in optional_packages:
        try:
            __import__(package.replace("-", "_"))
            print_success(f"Optional: {package}")
        except ImportError:
            missing_optional.append(package)
            print_warning(f"Missing optional: {package}")
    
    if missing_required:
        print_error(f"Install required packages: pip install {' '.join(missing_required)}")
        return False
    
    if missing_optional:
        print_info(f"Optional packages for full functionality: pip install {' '.join(missing_optional)}")
    
    return True

def generate_test_instructions():
    """Generate comprehensive testing instructions"""
    print_header("Step 7: Testing Instructions")
    
    instructions = """
🚀 COMPREHENSIVE TESTING INSTRUCTIONS for AID-US-001E

1. BACKEND SETUP:
   cd /Users/blas/Desktop/INRE/INRE-AI-Dock/Back
   
   # Install dependencies (if needed)
   pip install -r requirements.txt
   
   # Start the backend server
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

2. RUN PYTHON TEST SUITE:
   # Run all authentication tests
   pytest tests/test_auth.py -v
   
   # Run specific test classes
   pytest tests/test_auth.py::TestAuthenticationFlow -v
   pytest tests/test_auth.py::TestRateLimiting -v
   pytest tests/test_auth.py::TestSecurityValidation -v

3. RUN INTEGRATION TESTS:
   # Make script executable
   chmod +x test_AID_US_001E.sh
   
   # Run comprehensive integration tests
   ./test_AID_US_001E.sh

4. MANUAL TESTING:
   # Open API documentation
   Open: http://localhost:8000/docs
   
   # Test endpoints manually:
   - POST /api/v1/auth/login
   - POST /api/v1/auth/refresh  
   - GET /api/v1/auth/me
   - POST /api/v1/auth/logout
   - GET /api/v1/security/rate-limits

5. RATE LIMITING TESTING:
   # Test rate limits with curl (make 10 rapid requests)
   for i in {1..10}; do
     curl -X POST http://localhost:8000/api/v1/auth/login \\
       -H "Content-Type: application/json" \\
       -d '{"username":"user1","password":"wrongpass","remember_me":false}'
     echo " - Request $i"
   done

6. SECURITY HEADERS TESTING:
   # Check security headers
   curl -I http://localhost:8000/
   
   # Should include:
   # X-Content-Type-Options: nosniff
   # X-Frame-Options: DENY
   # X-XSS-Protection: 1; mode=block

7. BACKGROUND TASKS (Optional - requires Redis):
   # Start Redis (if available)
   redis-server
   
   # Start Celery worker (in another terminal)
   cd /Users/blas/Desktop/INRE/INRE-AI-Dock/Back
   celery -A app.tasks.cleanup worker --loglevel=info
   
   # Start Celery beat (in another terminal)
   celery -A app.tasks.cleanup beat --loglevel=info

8. LOAD TESTING (Basic):
   # Install Apache Bench (if available)
   # Test login endpoint under load
   ab -n 100 -c 10 -p login_data.json -T application/json http://localhost:8000/api/v1/auth/login
   
   # Where login_data.json contains:
   # {"username":"user1","password":"user123","remember_me":false}

✅ SUCCESS CRITERIA:
- All pytest tests pass (15+ test methods)
- Integration script runs without critical errors
- Rate limiting triggers after configured attempts
- Security headers present in responses
- No critical security vulnerabilities in audit

🔍 TROUBLESHOOTING:
- If tests fail, check backend is running on port 8000
- For dependency errors, install missing packages
- For Redis/Celery errors, they're optional for core functionality
- Check logs for detailed error information
"""
    
    print(instructions)

def main():
    """Main validation function"""
    print_header("AID-US-001E Security Enhancements - Final Validation")
    print_info(f"Validation started at: {datetime.now().isoformat()}")
    
    validation_results = []
    
    # Run all validation steps
    validation_results.append(("File Structure", validate_file_structure()))
    validation_results.append(("Python Modules", validate_python_modules()))
    validation_results.append(("Configuration", validate_configuration()))
    validation_results.append(("Test Suite", validate_test_suite()))
    validation_results.append(("Integration Scripts", validate_integration_scripts()))
    validation_results.append(("Dependencies", check_dependencies()))
    
    # Generate testing instructions
    generate_test_instructions()
    
    # Summary
    print_header("VALIDATION SUMMARY")
    
    passed = 0
    failed = 0
    
    for test_name, result in validation_results:
        if result:
            print_success(f"{test_name}: PASSED")
            passed += 1
        else:
            print_error(f"{test_name}: FAILED")
            failed += 1
    
    print(f"\n{Colors.BOLD}Results: {passed} passed, {failed} failed{Colors.END}")
    
    if failed == 0:
        print_success("🎉 ALL VALIDATIONS PASSED - AID-US-001E IS READY FOR COMPLETION!")
        return True
    else:
        print_error(f"❌ {failed} validation(s) failed - review and fix issues before completion")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
