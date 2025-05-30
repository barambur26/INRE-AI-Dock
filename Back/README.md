# AI Dock App - Backend

A secure internal web application backend for accessing multiple LLMs with role-based permissions, departmental usage quotas, and comprehensive usage tracking.

## Overview

The AI Dock App backend provides:
- **Multi-LLM Integration**: Support for OpenAI, Claude, Mistral, and other LLM providers
- **Role-Based Access Control**: Granular permissions for different user roles
- **Department Management**: Organize users by departments with individual quotas
- **Usage Tracking**: Comprehensive logging and monitoring of LLM usage
- **Quota Management**: Set and enforce usage limits per department
- **Secure Authentication**: JWT-based authentication with refresh tokens

## Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 14+
- Redis 6+ (for caching and background tasks)

### Installation

1. **Clone and navigate to the backend directory:**
   ```bash
   cd /Users/blas/Desktop/INRE/INRE-AI-Dock/Back
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your actual configuration values
   ```

5. **Set up the database:**
   ```bash
   # Create PostgreSQL database
   createdb ai_dock_db
   
   # Run migrations (when available)
   alembic upgrade head
   ```

6. **Start the development server:**
   ```bash
   python app/main.py
   # OR
   uvicorn app.main:app --reload --port 8000
   ```

The API will be available at:
- **API**: http://localhost:8000
- **Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## Project Structure

```
Back/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── api/                 # API route handlers
│   ├── core/                # Core configuration and utilities
│   ├── models/              # SQLAlchemy database models
│   ├── schemas/             # Pydantic models for API
│   ├── services/            # Business logic layer
│   └── utils/               # Utility functions
├── alembic/                 # Database migrations
├── scripts/                 # Deployment and utility scripts
├── tests/                   # Test suites
├── requirements.txt         # Python dependencies
├── .env.example            # Environment variables template
└── README.md               # This file
```

## API Endpoints

### System Endpoints
- `GET /` - API information
- `GET /health` - Health check

### Authentication (Coming Soon)
- `POST /auth/login` - User login
- `POST /auth/refresh` - Refresh access token
- `POST /auth/logout` - User logout
- `GET /auth/me` - Get current user profile

### Admin Endpoints (Coming Soon)
- `GET /admin/users` - List users
- `POST /admin/users` - Create user
- `PUT /admin/users/{id}` - Update user
- `DELETE /admin/users/{id}` - Delete user
- `GET /admin/departments` - List departments
- `POST /admin/departments` - Create department

### LLM Endpoints (Coming Soon)
- `POST /chat` - Send message to LLM
- `GET /models` - List available models
- `POST /admin/llm-config` - Update LLM configuration

## Development

### Code Style
```bash
# Format code
black app/

# Lint code
flake8 app/

# Type checking
mypy app/
```

### Testing
```bash
# Run tests
pytest

# Run tests with coverage
pytest --cov=app tests/
```

### Database Migrations
```bash
# Create a new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## Configuration

Key environment variables (see `.env.example` for complete list):

- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: JWT signing secret
- `OPENAI_API_KEY`: OpenAI API key
- `ANTHROPIC_API_KEY`: Claude API key
- `REDIS_URL`: Redis connection string

## Security Considerations

- All API keys should be stored as environment variables
- JWT tokens have short expiration times (15 minutes for access tokens)
- Rate limiting is implemented for authentication endpoints
- CORS is configured for frontend domains only
- All database queries use parameterized statements

## Deployment

### Docker (Recommended)
```bash
# Build image
docker build -t ai-dock-backend .

# Run container
docker run -p 8000:8000 --env-file .env ai-dock-backend
```

### Manual Deployment
```bash
# Install production dependencies
pip install -r requirements.txt

# Run with production server
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

## Support

For development questions or issues, please refer to:
- API Documentation: http://localhost:8000/docs
- Project Issues: Contact your development team
- Technical Details: See `/Users/blas/Desktop/INRE/INRE-AI-Dock/Helpers/project_details.md`

## License

Internal use only. All rights reserved.
