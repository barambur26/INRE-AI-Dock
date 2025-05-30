#!/usr/bin/env python3
"""
Advanced diagnostic script for AID-001-F Python import issues
This script will systematically test each import step to identify the exact problem
"""

import sys
import os
import traceback
from pathlib import Path

print("=== Advanced Python Import Diagnostic ===")
print(f"Python executable: {sys.executable}")
print(f"Python version: {sys.version}")
print(f"Current working directory: {os.getcwd()}")

# Add current directory to Python path
current_dir = Path.cwd()
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))
    print(f"✅ Added to Python path: {current_dir}")

print(f"\nPython path entries:")
for i, path in enumerate(sys.path):
    print(f"  {i}: {path}")

print("\n" + "="*60)
print("STEP 1: Testing Core Dependencies")
print("="*60)

# Test core dependencies
dependencies = [
    ('sqlalchemy', 'SQLAlchemy ORM'),
    ('alembic', 'Database migrations'),
    ('pydantic', 'Data validation'),
    ('pydantic_settings', 'Settings management'),
    ('uuid', 'UUID generation'),
    ('datetime', 'Date/time handling'),
]

failed_deps = []
for module_name, description in dependencies:
    try:
        __import__(module_name)
        print(f"✅ {module_name:15} - {description}")
    except ImportError as e:
        print(f"❌ {module_name:15} - FAILED: {e}")
        failed_deps.append(module_name)

if failed_deps:
    print(f"\n⚠️  Missing dependencies: {', '.join(failed_deps)}")
    print("Run: pip install -r requirements.txt")

print("\n" + "="*60)
print("STEP 2: Testing File Structure")
print("="*60)

required_files = [
    "app/__init__.py",
    "app/core/__init__.py",
    "app/core/config.py", 
    "app/core/database.py",
    "app/models/__init__.py",
    "app/models/user.py",
    "app/models/refresh_token.py"
]

missing_files = []
for file_path in required_files:
    full_path = current_dir / file_path
    if full_path.exists():
        print(f"✅ {file_path}")
        
        # Check if file has content (not empty)
        if full_path.stat().st_size == 0:
            print(f"   ⚠️  File is empty!")
            
    else:
        print(f"❌ {file_path} - MISSING")
        missing_files.append(file_path)

if missing_files:
    print(f"\n⚠️  Creating missing __init__.py files...")
    for file_path in missing_files:
        if "__init__.py" in file_path:
            full_path = current_dir / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.touch()
            print(f"   Created: {file_path}")

print("\n" + "="*60)
print("STEP 3: Testing Individual Module Imports")
print("="*60)

# Test imports step by step
import_tests = [
    ("app", "Base app module"),
    ("app.core", "Core module"),
    ("app.core.config", "Configuration module"),
    ("app.core.database", "Database module"),
    ("app.core.database.Base", "SQLAlchemy Base class"),
    ("app.models", "Models module"),
]

for module_path, description in import_tests:
    try:
        if "." in module_path:
            parts = module_path.split(".")
            if len(parts) == 3:  # e.g., app.core.database.Base
                module_name = ".".join(parts[:-1])
                attr_name = parts[-1]
                module = __import__(module_name, fromlist=[attr_name])
                getattr(module, attr_name)
            else:
                __import__(module_path)
        else:
            __import__(module_path)
        print(f"✅ {module_path:25} - {description}")
    except Exception as e:
        print(f"❌ {module_path:25} - FAILED: {type(e).__name__}: {e}")
        if "app.core.config" in module_path or "app.core.database" in module_path:
            print(f"   Full traceback:")
            traceback.print_exc()

print("\n" + "="*60)
print("STEP 4: Testing Model File Syntax")
print("="*60)

model_files = [
    ("app/models/user.py", "User model"),
    ("app/models/refresh_token.py", "RefreshToken model"),
]

for file_path, description in model_files:
    try:
        full_path = current_dir / file_path
        if full_path.exists():
            # Try to compile the file to check for syntax errors
            with open(full_path, 'r') as f:
                content = f.read()
            compile(content, str(full_path), 'exec')
            print(f"✅ {file_path:30} - Syntax OK")
        else:
            print(f"❌ {file_path:30} - File not found")
    except SyntaxError as e:
        print(f"❌ {file_path:30} - Syntax Error: {e}")
        print(f"   Line {e.lineno}: {e.text}")
    except Exception as e:
        print(f"❌ {file_path:30} - Error: {e}")

print("\n" + "="*60)
print("STEP 5: Testing Individual Model Imports")
print("="*60)

# Test individual model imports
individual_models = [
    ("app.models.user", "User", "User model class"),
    ("app.models.refresh_token", "RefreshToken", "RefreshToken model class"),
]

for module_path, class_name, description in individual_models:
    try:
        module = __import__(module_path, fromlist=[class_name])
        model_class = getattr(module, class_name)
        print(f"✅ {class_name:15} from {module_path:25} - {description}")
        print(f"   Class: {model_class}")
    except ImportError as e:
        print(f"❌ {class_name:15} from {module_path:25} - Import Error: {e}")
        traceback.print_exc()
    except AttributeError as e:
        print(f"❌ {class_name:15} from {module_path:25} - Attribute Error: {e}")
    except Exception as e:
        print(f"❌ {class_name:15} from {module_path:25} - Other Error: {type(e).__name__}: {e}")
        traceback.print_exc()

print("\n" + "="*60)
print("STEP 6: Testing Aggregate Import")
print("="*60)

try:
    # Test the full import that's failing
    print("Attempting: from app.models import User, RefreshToken, Role, Department, LLMConfiguration, DepartmentQuota, UsageLog")
    from app.models import User, RefreshToken, Role, Department, LLMConfiguration, DepartmentQuota, UsageLog
    print("✅ SUCCESS! All models imported successfully")
    print(f"   Models: {[cls.__name__ for cls in [User, RefreshToken, Role, Department, LLMConfiguration, DepartmentQuota, UsageLog]]}")
except ImportError as e:
    print(f"❌ FAILED - Import Error: {e}")
    print("\nDetailed traceback:")
    traceback.print_exc()
    
    # Try importing just app.models to see what's available
    try:
        import app.models
        print(f"\n📋 Available in app.models: {dir(app.models)}")
    except Exception as e2:
        print(f"❌ Can't even import app.models: {e2}")
        traceback.print_exc()

except Exception as e:
    print(f"❌ FAILED - Other Error: {type(e).__name__}: {e}")
    print("\nDetailed traceback:")
    traceback.print_exc()

print("\n" + "="*60)
print("DIAGNOSTIC COMPLETE")
print("="*60)
print("If models still can't be imported, check the detailed error messages above.")
print("Common issues:")
print("1. Missing dependencies - run: pip install -r requirements.txt")
print("2. Syntax errors in model files")
print("3. Import errors within the model files")
print("4. Missing database configuration")
