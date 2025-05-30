# AI Dock App - Database Models

## Database Schema Documentation

### Overview
This document defines the database schema for the AI Dock App using PostgreSQL with SQLAlchemy ORM.

## Core Models

### User Model
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role_id UUID REFERENCES roles(id),
    department_id UUID REFERENCES departments(id),
    is_active BOOLEAN DEFAULT true,
    is_superuser BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### RefreshToken Model
```sql
CREATE TABLE refresh_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    token_hash VARCHAR(255) UNIQUE NOT NULL,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    is_revoked BOOLEAN DEFAULT false,
    remember_me BOOLEAN DEFAULT false,
    user_agent TEXT,
    ip_address INET,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### Role Model
```sql
CREATE TABLE roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    permissions JSONB DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### Department Model
```sql
CREATE TABLE departments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### LLMConfiguration Model
```sql
CREATE TABLE llm_configurations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_name VARCHAR(100) NOT NULL,
    provider VARCHAR(50) NOT NULL,
    api_key_encrypted TEXT,
    base_url TEXT,
    enabled BOOLEAN DEFAULT true,
    config_json JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### DepartmentQuota Model
```sql
CREATE TABLE department_quotas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    department_id UUID NOT NULL REFERENCES departments(id) ON DELETE CASCADE,
    llm_config_id UUID NOT NULL REFERENCES llm_configurations(id) ON DELETE CASCADE,
    monthly_limit_tokens INTEGER NOT NULL DEFAULT 0,
    current_usage_tokens INTEGER NOT NULL DEFAULT 0,
    last_reset TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(department_id, llm_config_id)
);
```

### UsageLog Model
```sql
CREATE TABLE usage_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    department_id UUID NOT NULL REFERENCES departments(id),
    llm_config_id UUID NOT NULL REFERENCES llm_configurations(id),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    tokens_prompt INTEGER NOT NULL DEFAULT 0,
    tokens_completion INTEGER NOT NULL DEFAULT 0,
    tokens_total INTEGER GENERATED ALWAYS AS (tokens_prompt + tokens_completion) STORED,
    cost_estimated DECIMAL(10, 4) DEFAULT 0.0000,
    request_details JSONB DEFAULT '{}',
    response_details JSONB DEFAULT '{}'
);
```

## Indexes

```sql
-- User indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_role_id ON users(role_id);
CREATE INDEX idx_users_department_id ON users(department_id);
CREATE INDEX idx_users_active ON users(is_active);

-- Refresh token indexes
CREATE INDEX idx_refresh_tokens_user_id ON refresh_tokens(user_id);
CREATE INDEX idx_refresh_tokens_expires_at ON refresh_tokens(expires_at);
CREATE INDEX idx_refresh_tokens_revoked ON refresh_tokens(is_revoked);
CREATE INDEX idx_refresh_tokens_token_hash ON refresh_tokens(token_hash);

-- Usage log indexes
CREATE INDEX idx_usage_logs_user_id ON usage_logs(user_id);
CREATE INDEX idx_usage_logs_department_id ON usage_logs(department_id);
CREATE INDEX idx_usage_logs_timestamp ON usage_logs(timestamp);
CREATE INDEX idx_usage_logs_llm_config_id ON usage_logs(llm_config_id);

-- Department quota indexes
CREATE INDEX idx_department_quotas_department_id ON department_quotas(department_id);
CREATE INDEX idx_department_quotas_llm_config_id ON department_quotas(llm_config_id);
```

## Default Data

### Default Roles
```sql
INSERT INTO roles (name, description, permissions) VALUES 
('admin', 'System Administrator', '["*"]'),
('user', 'Standard User', '["chat", "view_profile"]');
```

### Default Departments
```sql
INSERT INTO departments (name, description) VALUES 
('General', 'Default department for new users'),
('IT', 'Information Technology Department'),
('Finance', 'Finance Department'),
('HR', 'Human Resources Department');
```

## Authentication Flow

### JWT Token Structure
- **Access Token**: Short-lived (15 minutes), contains user claims
- **Refresh Token**: Long-lived (7-30 days), stored in database with metadata

### Token Claims
```json
{
  "sub": "user_id",
  "email": "user@example.com",
  "role": "user|admin",
  "department_id": "uuid",
  "exp": "expiration_timestamp",
  "iat": "issued_at_timestamp",
  "jti": "token_id"
}
```

### Security Features
- Password hashing with bcrypt
- Refresh token rotation on each use
- Token blacklisting on logout
- Automatic cleanup of expired tokens
- Rate limiting on authentication endpoints
- User agent and IP tracking for sessions

## Migration Notes
- Use Alembic for database migrations
- Ensure proper foreign key constraints
- Add appropriate indexes for performance
- Use UUIDs for all primary keys
- Implement soft delete where appropriate

## Future Enhancements
- Session management for concurrent logins
- OAuth2/OIDC integration
- Multi-factor authentication
- Password policy enforcement
- Account lockout mechanisms
