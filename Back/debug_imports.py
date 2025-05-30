#!/usr/bin/env python3
"""
Debug script to identify Python import issues for AID-001-F models
"""

import sys
import os
from pathlib import Path

print("=== Python Import Debug for AID-001-F ===")
print(f"Python version: {sys.version}")
print(f"Current working directory: {os.getcwd()}")
print(f"Python path:")
for p in sys.path:
    print(f"  - {p}")

# Add current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))
print(f"\nAdded to Python path: {current_dir}")

print("\n=== Testing Individual Imports ===")

# Test basic imports first
try:
    import sqlalchemy
    print("✅ SQLAlchemy import successful")
    print(f"   Version: {sqlalchemy.__version__}")
except ImportError as e:
    print(f"❌ SQLAlchemy import failed: {e}")
    sys.exit(1)

try:
    import alembic
    print("✅ Alembic import successful")
    print(f"   Version: {alembic.__version__}")
except ImportError as e:
    print(f"❌ Alembic import failed: {e}")

# Test database core imports
try:
    from app.core.database import Base
    print("✅ Database Base import successful")
except ImportError as e:
    print(f"❌ Database Base import failed: {e}")
    print("   Check app/core/database.py")

# Test individual model imports
models_to_test = [
    ('User', 'app.models.user'),
    ('RefreshToken', 'app.models.refresh_token'),
]

for model_name, module_path in models_to_test:
    try:
        module = __import__(module_path, fromlist=[model_name])
        model_class = getattr(module, model_name)
        print(f"✅ {model_name} import successful from {module_path}")
    except ImportError as e:
        print(f"❌ {model_name} import failed from {module_path}: {e}")
    except AttributeError as e:
        print(f"❌ {model_name} not found in {module_path}: {e}")

# Test aggregate models import
try:
    from app.models import User, RefreshToken, Role, Department, LLMConfiguration, DepartmentQuota, UsageLog
    print("✅ All models import successful from app.models")
    
    print(f"\nModel classes found:")
    print(f"  - User: {User}")
    print(f"  - RefreshToken: {RefreshToken}")
    print(f"  - Role: {Role}")
    print(f"  - Department: {Department}")
    print(f"  - LLMConfiguration: {LLMConfiguration}")
    print(f"  - DepartmentQuota: {DepartmentQuota}")
    print(f"  - UsageLog: {UsageLog}")
    
except ImportError as e:
    print(f"❌ Models aggregate import failed: {e}")
    print("   This is the main issue preventing tests from running")
    
    # Try to debug the specific import issue
    try:
        print("\n=== Debugging app.models import ===")
        import app.models
        print("✅ app.models module imported successfully")
        print(f"   Available attributes: {dir(app.models)}")
    except ImportError as e:
        print(f"❌ app.models module import failed: {e}")
        
        # Check if app module exists
        try:
            import app
            print("✅ app module imported successfully")
            print(f"   App module path: {app.__file__}")
        except ImportError as e:
            print(f"❌ app module import failed: {e}")
            print("   Make sure app/__init__.py exists")

print("\n=== File Structure Check ===")
required_files = [
    "app/__init__.py",
    "app/core/__init__.py", 
    "app/core/database.py",
    "app/models/__init__.py",
    "app/models/user.py",
    "app/models/refresh_token.py"
]

for file_path in required_files:
    full_path = Path(current_dir) / file_path
    if full_path.exists():
        print(f"✅ {file_path} exists")
    else:
        print(f"❌ {file_path} missing")

print(f"\n{'='*50}")
print("Debug completed. Check the errors above to identify the issue.")
