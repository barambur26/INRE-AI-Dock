# AID-001-F: Initial Database Migration - Test Suite

## Overview

This test suite comprehensively validates the **AID-001-F: Initial Database Migration** implementation. It ensures that:

1. ✅ Migration files can be generated correctly
2. ✅ All expected database tables are created
3. ✅ Table structures match the SQLAlchemy models
4. ✅ Foreign key relationships work properly
5. ✅ Migrations can be applied and rolled back
6. ✅ Sample data can be inserted and relationships work

## Test Files Created

### 🔧 **Main Test Runner**
- **`run_tests_AID-001-F.sh`** - Master test runner that executes all tests

### 🧪 **Individual Test Files**
1. **`test_AID-001-F.sh`** - Complete bash-based test suite
2. **`test_AID-001-F.py`** - Python unit tests with detailed model testing
3. **`tests/integration/test_AID-001-F_migration.sh`** - Integration test following project patterns

### 📚 **Support Files**
- **`MIGRATION_GUIDE.md`** - Complete migration documentation
- **`generate_migration.sh`** - Helper script to generate migrations
- **`apply_migration.sh`** - Helper script to apply migrations

## Test Categories

### 🏗️ **Prerequisites Tests**
- Backend directory structure validation
- Required files existence (models, alembic config)
- Python import capabilities
- Database connectivity

### 🔄 **Migration Generation Tests**
- Alembic migration file generation
- Migration file content validation
- Expected table definitions presence
- Upgrade/downgrade function verification

### 💾 **Database Structure Tests**
- All expected tables creation
- Correct column types and constraints
- Primary key and foreign key relationships
- Index creation validation

### 🔗 **Model Integration Tests**
- SQLAlchemy model functionality
- Relationship mappings
- Model utility methods
- Data insertion and retrieval

### ↩️ **Migration Lifecycle Tests**
- Migration application (`alembic upgrade head`)
- Migration rollback (`alembic downgrade base`)
- Re-application after rollback
- Migration status tracking

## How to Run Tests

### 🚀 **Quick Start (Recommended)**
```bash
cd /Users/blas/Desktop/INRE/INRE-AI-Dock/Back
chmod +x run_tests_AID-001-F.sh
./run_tests_AID-001-F.sh
```

### 🎯 **Run Specific Test Types**
```bash
# Run only bash tests
./run_tests_AID-001-F.sh --filter bash

# Run only Python tests  
./run_tests_AID-001-F.sh --filter python

# Run only integration tests
./run_tests_AID-001-F.sh --filter integration
```

### 🔍 **Run Individual Tests**
```bash
# Comprehensive bash test
chmod +x test_AID-001-F.sh
./test_AID-001-F.sh

# Python model tests
python test_AID-001-F.py

# Integration test
chmod +x tests/integration/test_AID-001-F_migration.sh
./tests/integration/test_AID-001-F_migration.sh
```

### ⚙️ **Manual Migration Testing**
```bash
# Generate migration
chmod +x generate_migration.sh
./generate_migration.sh

# Apply migration
chmod +x apply_migration.sh  
./apply_migration.sh
```

## Expected Test Results

### ✅ **Successful Test Run Output**
```
======================================================
  AID-001-F: Initial Database Migration Test Suite
======================================================

✅ Complete Bash Test Suite PASSED
✅ Python Unit Tests PASSED  
✅ Integration Tests PASSED

======================================================
  TEST RESULTS SUMMARY
======================================================
Total Tests: 3
Passed: 3
Failed: 0

🎉 ALL TESTS PASSED!
AID-001-F: Initial Database Migration is working correctly.
```

### 📊 **Database Tables Created**
After successful migration, these tables should exist:
- `users` - User accounts and authentication
- `refresh_tokens` - JWT session management
- `roles` - RBAC role definitions
- `departments` - Organizational structure
- `llm_configurations` - LLM provider settings
- `department_quotas` - Usage quotas per department
- `usage_logs` - API usage tracking
- `alembic_version` - Migration version tracking

## Prerequisites

### 🐘 **PostgreSQL Setup**
```bash
# Ensure PostgreSQL is running
pg_isready -h localhost -p 5432

# Create database and user (if not exists)
createdb aidock
createuser aidock
psql -c "ALTER USER aidock WITH PASSWORD 'aidock';"
psql -c "GRANT ALL PRIVILEGES ON DATABASE aidock TO aidock;"
```

### 🐍 **Python Environment**
```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Verify model imports work
python -c "from app.models import User, RefreshToken"
```

## Troubleshooting

### ❌ **Common Issues**

#### "No module named 'app'"
```bash
# Ensure you're in the backend directory
cd /Users/blas/Desktop/INRE/INRE-AI-Dock/Back

# Activate virtual environment
source venv/bin/activate
```

#### "Database connection failed"
```bash
# Check PostgreSQL is running
pg_isready -h localhost -p 5432 -U aidock -d aidock

# Check credentials in alembic.ini
grep sqlalchemy.url alembic.ini
```

#### "Migration file not found"
```bash
# Generate migration first
alembic revision --autogenerate -m "Initial tables"

# Check migration was created
ls -la alembic/versions/
```

#### "Permission denied"
```bash
# Make scripts executable
chmod +x *.sh tests/integration/*.sh
```

### 🔧 **Test Database Cleanup**
Tests create temporary databases with names like:
- `aidock_test`
- `aidock_test_python`
- `aidock_test_integration`

If tests fail unexpectedly, cleanup with:
```bash
dropdb aidock_test 2>/dev/null || true
dropdb aidock_test_python 2>/dev/null || true
dropdb aidock_test_integration 2>/dev/null || true
```

## Test Coverage

### 🎯 **What's Tested**
- ✅ Migration file generation
- ✅ All 7 database tables creation
- ✅ Column types and constraints
- ✅ Primary/foreign key relationships
- ✅ Index creation
- ✅ Model relationships and methods
- ✅ Data insertion and retrieval
- ✅ Migration rollback functionality

### 🔍 **Test Statistics**
- **Total Test Cases**: ~50+ individual assertions
- **Test Files**: 3 main test suites
- **Coverage**: Migration lifecycle, database structure, model functionality
- **Test Types**: Unit, integration, end-to-end

## Success Criteria

The test suite passes when:
1. ✅ All migration files generate without errors
2. ✅ All 7 expected tables are created with correct structure
3. ✅ Foreign key relationships are established properly
4. ✅ Sample data can be inserted and retrieved
5. ✅ Migrations can be applied and rolled back successfully
6. ✅ Model utility methods work as expected

## Next Steps After Passing

When all tests pass:
1. **Update Backlog**: Mark AID-001-F as ✅ completed
2. **Proceed to Next Task**: Begin AID-US-001B (JWT Authentication Utilities)
3. **Optional**: Add seed data scripts for development
4. **Documentation**: Update project_details.md if needed

## Integration with CI/CD

These tests are designed to be integrated into continuous integration:

```yaml
# Example GitHub Actions step
- name: Test Database Migration
  run: |
    cd Back
    source venv/bin/activate
    ./run_tests_AID-001-F.sh
```

---

**📝 Note**: This test suite is specifically designed for AID-001-F and validates the complete database migration functionality. It serves as both a validation tool and documentation of expected behavior.
