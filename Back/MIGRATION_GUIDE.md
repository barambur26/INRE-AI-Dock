# AID-001-F: Initial Database Migration Guide

## Overview
This task creates the first Alembic migration to set up all the initial database tables for the AI Dock application.

## What This Migration Will Create

### Tables to be Created:
1. **users** - User accounts and authentication
2. **refresh_tokens** - JWT refresh tokens for session management  
3. **roles** - User roles for RBAC (Role-Based Access Control)
4. **departments** - Department organization structure
5. **llm_configurations** - LLM provider configurations
6. **department_quotas** - Usage quotas per department per LLM
7. **usage_logs** - Tracking of LLM API usage
8. **alembic_version** - Migration version tracking (created automatically)

### Key Relationships:
- Users belong to Roles and Departments
- RefreshTokens are linked to Users
- DepartmentQuotas link Departments to LLM Configurations
- UsageLogs track usage by User, Department, and LLM Configuration

## Prerequisites

### Database Setup:
```sql
-- If PostgreSQL is not set up, run these commands:
createdb aidock
createuser aidock
psql -c "ALTER USER aidock WITH PASSWORD 'aidock';"
psql -c "GRANT ALL PRIVILEGES ON DATABASE aidock TO aidock;"
```

### Python Environment:
```bash
# Make sure virtual environment is activated and dependencies installed
cd /Users/blas/Desktop/INRE/INRE-AI-Dock/Back
source venv/bin/activate
pip install -r requirements.txt
```

## Migration Commands

### Option 1: Using Helper Scripts (Recommended)
```bash
cd /Users/blas/Desktop/INRE/INRE-AI-Dock/Back
chmod +x generate_migration.sh apply_migration.sh
./generate_migration.sh
# Review the generated migration file
./apply_migration.sh
```

### Option 2: Direct Alembic Commands
```bash
cd /Users/blas/Desktop/INRE/INRE-AI-Dock/Back
source venv/bin/activate
alembic revision --autogenerate -m "Initial tables"
alembic upgrade head
```

## What to Expect

### Generated Migration File:
- Location: `alembic/versions/[timestamp]_initial_tables.py`
- Contains: `upgrade()` and `downgrade()` functions
- Creates all tables with proper columns, indexes, and foreign keys

### Success Indicators:
- ✅ Migration file generated without errors
- ✅ All 7 tables created in database
- ✅ Foreign key relationships established
- ✅ Indexes created for performance
- ✅ `alembic current` shows the migration ID

### Verification Commands:
```bash
# Check current migration
alembic current

# List tables in database
psql postgresql://aidock:aidock@localhost:5432/aidock -c "\dt"

# Check migration history
alembic history
```

## Troubleshooting

### Common Issues:
1. **"No module named 'app'"** - Run from correct directory with venv activated
2. **Database connection error** - Ensure PostgreSQL is running and credentials are correct
3. **Permission denied** - Check database user permissions
4. **Migration already exists** - Check `alembic/versions/` directory

### Recovery Commands:
```bash
# If migration fails, you can downgrade and try again
alembic downgrade base
# Then re-run the migration
alembic upgrade head
```

## Next Steps After Completion

Once this migration runs successfully:
1. ✅ Mark AID-001-F as completed in backlog
2. ➡️ Proceed to AID-US-001B (JWT Authentication Utilities)
3. 🧪 Consider adding some initial seed data for testing

## Files Created/Modified:
- `alembic/versions/[timestamp]_initial_tables.py` (generated)
- `generate_migration.sh` (helper script)
- `apply_migration.sh` (helper script)
- This guide: `MIGRATION_GUIDE.md`
