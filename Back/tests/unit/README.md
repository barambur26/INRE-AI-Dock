# Unit Tests Directory

This directory will contain Python unit tests using pytest for individual components.

## Structure
- `test_models/` - Database model tests
- `test_services/` - Business logic service tests  
- `test_utils/` - Utility function tests
- `test_core/` - Core configuration and database tests

## Example test file structure:
```
test_models/
├── test_user_model.py
├── test_refresh_token_model.py
└── __init__.py

test_services/
├── test_auth_service.py
└── __init__.py
```

## Running unit tests:
```bash
# From backend directory
python -m pytest tests/unit/ -v

# With coverage
python -m pytest tests/unit/ --cov=app --cov-report=html
```
