# AI Dock App - Test Suite

This directory contains tests for the AI Dock App backend components, organized by development phases and user stories.

## Test Structure

### Integration Tests (`/integration/`)
- **Purpose:** Test complete workflows and component interactions
- **Scope:** Database migrations, API endpoints, authentication flows
- **Files:** Named by user story ID (e.g., `test_AID-001-E_alembic_setup.sh`)

### Unit Tests (`/unit/`)
- **Purpose:** Test individual components in isolation
- **Scope:** Models, services, utilities
- **Files:** Python pytest files (e.g., `test_user_model.py`)

### API Tests (`/api/`)
- **Purpose:** Test REST API endpoints
- **Scope:** Request/response validation, authentication, permissions
- **Files:** HTTP client tests (e.g., `test_auth_endpoints.py`)

## Naming Convention

- **Integration tests:** `test_[USER-STORY-ID]_[description].sh`
- **Unit tests:** `test_[component]_[feature].py`
- **API tests:** `test_[endpoint-group]_[method].py`

## Current Tests

### Completed User Stories
- ✅ **AID-001-E:** Alembic Migration Setup - `integration/test_AID-001-E_alembic_setup.sh`

### Upcoming Tests
- 🔄 **AID-001-F:** Initial Database Migration
- 🔄 **AID-US-001B:** JWT Authentication Utilities
- 🔄 **AID-US-001C:** Authentication API Endpoints

## Running Tests

### All Integration Tests
```bash
cd /Users/blas/Desktop/INRE/INRE-AI-Dock/Back
find tests/integration -name "*.sh" -exec chmod +x {} \; -exec {} \;
```

### Specific Test
```bash
cd /Users/blas/Desktop/INRE/INRE-AI-Dock/Back
./tests/integration/test_AID-001-E_alembic_setup.sh
```

### Python Unit Tests (when available)
```bash
cd /Users/blas/Desktop/INRE/INRE-AI-Dock/Back
python -m pytest tests/unit/ -v
```

## Test Environment Setup

Before running tests, ensure:
1. Virtual environment is activated: `source venv/bin/activate`
2. Dependencies are installed: `pip install -r requirements.txt`
3. PostgreSQL is running and database exists
4. Environment variables are set (see `.env.example`)
