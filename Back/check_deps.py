#!/usr/bin/env python3
"""
Quick dependency checker for AID-001-F
"""

import subprocess
import sys

print("=== Checking Python Dependencies ===")

# List of required packages from requirements.txt
required_packages = [
    'fastapi==0.104.1',
    'sqlalchemy==2.0.23', 
    'alembic==1.12.1',
    'psycopg2-binary==2.9.9',
    'pydantic==2.5.0',
    'pydantic-settings==2.1.0',
    'python-dotenv==1.0.0',
]

print("Checking critical packages...")

for package in required_packages:
    package_name = package.split('==')[0].replace('-', '_')
    try:
        __import__(package_name)
        print(f"✅ {package_name}")
    except ImportError:
        print(f"❌ {package_name} - MISSING")
        print(f"   Install with: pip install {package}")

print("\n=== Testing Specific Import Chain ===")

# Test the import chain that's failing
test_imports = [
    "import uuid",
    "from datetime import datetime", 
    "import sqlalchemy",
    "from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String",
    "from sqlalchemy.dialects.postgresql import UUID",
    "from sqlalchemy.orm import relationship",
    "from sqlalchemy.sql import func",
    "from pydantic_settings import BaseSettings",
    "import app.core.config",
    "from app.core.config import settings",
    "import app.core.database",
    "from app.core.database import Base",
]

for import_statement in test_imports:
    try:
        exec(import_statement)
        print(f"✅ {import_statement}")
    except Exception as e:
        print(f"❌ {import_statement}")
        print(f"   Error: {type(e).__name__}: {e}")
        if 'app.core' in import_statement:
            import traceback
            traceback.print_exc()
        break

print("\n=== Dependency Check Complete ===")
