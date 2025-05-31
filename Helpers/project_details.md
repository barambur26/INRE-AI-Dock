---

## AI Dock App - Technical Project Details

### Project Overview

**Name:** AI Dock App
**Type:** Full-Stack Application
**Purpose:** To provide a unified and secure interface for enterprise users to access multiple LLMs, featuring role-based access control, departmental usage quotas, and usage tracking.
**Current State:** Full-stack application with a planned React frontend and a future backend.

### What This Application Does

The AI Dock App is a secure internal web application designed for users within a bank (handling private information) to access various Large Language Models (LLMs) such as OpenAI, Claude, Mistral, etc., through a unified interface. It manages user access with role-based permissions, establishes and monitors departmental usage quotas, and tracks LLM usage. It will be hosted privately on an intranet or private cloud and is engineered for scalability and modularity.

### Core Workflow

* **Hub Configuration:** The user (administrator) inputs a JSON configuration for enabled LLMs and departmental quotas. AI validates and suggests improvements.
* **Access Control Setup:** The administrator defines departments, users, and roles with quota limits.
* **Model Routing Logic:** AI sets up routing for LLM APIs (OpenAI, Claude, Mistral, etc.) based on the configuration.
* **Usage Logging:** AI logs API usage by user, department, and timestamp.
* **Quota Monitoring:** AI monitors usage and suggests quota adjustments or alerts when thresholds are reached.

---

### Technical Architecture

#### Frontend Stack

* **Framework:** React 18 + TypeScript + Vite
* **UI Library:** Radix UI components via shadcn/ui + Tailwind CSS
* **Routing:** React Router DOM v6
* **State:** React Query for server state, React hooks for local state
* **Forms:** React Hook Form + Zod validation
* **Icons:** Lucide React

#### Backend Stack (Future)

* **API Framework:** FastAPI (Python)
* **Database:** PostgreSQL with SQLAlchemy ORM
* **Caching/Queue:** Redis + Celery for background tasks
* **Authentication:** JWT with FastAPI-Users
* **AI Integration:** OpenAI API / Anthropic Claude API (and other LLMs)
* **Deployment:** Docker + Docker Compose

---

### Project Structure

#### Frontend (`/Users/blas/Desktop/INRE/INRE-AI-Dock/Front`)

```
src/
├── components/
│   ├── Layout.tsx           # Main app shell with sidebar
│   ├── Sidebar.tsx          # Left navigation menu
│   ├── TopBar.tsx           # Header with breadcrumbs
│   └── ui/                  # shadcn/ui components (40+ components)
├── pages/
│   ├── Login.tsx            # Login page
│   ├── Dashboard.tsx        # Main application dashboard
│   ├── ChatInterface.tsx    # Unified chat interface for LLMs
│   └── AdminSettings.tsx    # User, department, quota management
├── hooks/                   # Custom React hooks
└── lib/utils.ts            # Utility functions
```

#### Backend (Future) (`/Users/blas/Desktop/INRE/INRE-AI-Dock/Back`)

```
app/
├── api/                     # API route handlers
├── core/
│   └── config.py           # Application configuration
├── models/                  # Database models (SQLAlchemy)
├── services/                # Business logic and AI services
└── main.py                 # FastAPI application entry point
```

---

### Data Models (Database Schema - Reference: `/Users/blas/Desktop/INRE/INRE-AI-Dock/Back/DATABASE_MODELS.md`)

*The exact models will be detailed in `DATABASE_MODELS.md`, but key entities include:*

**User**
```json
{
  "id": "UUID",
  "username": "string",
  "email": "string",
  "hashed_password": "string",
  "role_id": "UUID",
  "department_id": "UUID",
  "is_active": "boolean"
}
```

**Role**
```json
{
  "id": "UUID",
  "name": "string",
  "permissions": ["array of strings"]
}
```

**Department**
```json
{
  "id": "UUID",
  "name": "string",
  "description": "string"
}
```

**LLMConfiguration**
```json
{
  "id": "UUID",
  "model_name": "string",
  "provider": "string",
  "api_key_encrypted": "string",
  "enabled": "boolean",
  "config_json": "JSONB"
}
```

**DepartmentQuota**
```json
{
  "id": "UUID",
  "department_id": "UUID",
  "llm_config_id": "UUID",
  "monthly_limit_tokens": "integer",
  "current_usage_tokens": "integer",
  "last_reset": "timestamp"
}
```

**UsageLog**
```json
{
  "id": "UUID",
  "user_id": "UUID",
  "department_id": "UUID",
  "llm_config_id": "UUID",
  "timestamp": "timestamp",
  "tokens_used": "integer",
  "cost_estimated": "float",
  "request_details": "JSONB"
}
```

---

### Key Features

#### Access & Configuration Management

* **Basic User Authentication & Session Management:** Core user and session handling.
* **Admin Interface for User & Department Management:** CRUD operations for users and departments.
* **Admin Configuration of Enabled LLMs:** Manual JSON input for LLM setup and enablement.
* **Department-Based Usage Quotas:** Setting and enforcing usage limits per department.

#### LLM Interaction

* **Unified Chat Interface:** For interacting with configured LLMs.
* **Dynamic Model Selection and Routing:** Logic to select and route requests to the appropriate LLM.
* **AI-Powered Validation & Suggestions:** AI validates and suggests improvements for LLM configurations.

#### Monitoring & Auditing

* **Basic Usage Logging:** Detailed API usage logs by user, department, timestamp, and model.
* **Real-time Quota Monitoring with Automated Alerts:** Live tracking with threshold alerts.
* **Comprehensive Usage Tracking Dashboard:** An all-encompassing dashboard for administrators.

#### Scalability & Security

* **Advanced Role-Based Access Control (RBAC):** Granular permissions.
* **Secure Hosting Setup Guidance & Documentation:** Guidelines for private cloud/intranet deployment.
* **Scalable Architecture Review and Initial Optimizations:** Ensuring the application's growth potential.

---

### Current Implementation Details (Frontend)

Currently, the focus is on building the frontend and simulating functionalities to validate the user flow.

#### AI Simulation Method

All AI features are **simulated** using `setTimeout()` with 2-3 second delays. Mock responses are hardcoded within components. For example, in the future `AdminSettings.tsx` for LLM configuration:

```typescript
const handleLLMConfigSubmit = async () => {
  setIsValidating(true);
  setTimeout(() => {
    const mockSuggestions = [/* mock AI validation suggestions */];
    setValidationSuggestions(mockSuggestions);
    setIsValidating(false);
    // Logic to display suggestions or proceed to next step
  }, 2000);
};
```

#### State Management Pattern

* **Server State:** React Query (prepared for future backend integrations).
* **Local State:** React hooks (`useState`, `useEffect`).
* **Form State:** React Hook Form with Zod schemas.
* **No Global State:** Each page currently manages its own state.

#### Component Patterns

* **Compound Components:** E.g., Cards with Header/Content structure.
* **Render Props:** For form components with validation.
* **Custom Hooks:** Reusable stateful logic (e.g., `use-toast`).
* **Conditional Rendering:** Based on loading/error/success states.

#### Key File Locations (Frontend)

* `src/pages/Dashboard.tsx` - Main application dashboard.
* `src/pages/AdminSettings.tsx` - Interface for user, department, and LLM/quota configuration.
* `src/pages/ChatInterface.tsx` - Primary interface for interacting with models.
* `src/pages/Login.tsx` - Authentication page.

#### Configuration Files

* `components.json` - shadcn/ui configuration.
* `tailwind.config.ts` - Tailwind CSS setup.
* `vite.config.ts` - Build configuration.
* `tsconfig.json` - TypeScript configuration.

---

### Current Implementation Status

* **✅ Full-Stack Application:** Complete frontend and backend integration
* **✅ Real Authentication:** JWT-based authentication with refresh tokens
* **✅ Real AI Integration:** Multi-LLM provider support (OpenAI, Claude, etc.)
* **✅ Database Ready:** SQLAlchemy models and schema defined (persistence optional)
* **✅ Production Features:** Rate limiting, security headers, usage tracking

#### Data Persistence (Optional)
* Database models are defined but PostgreSQL setup is optional for demo
* In-memory mock data provides full functionality for testing and demos
* Can be easily switched to persistent storage when needed

#### Mock Data

* Hardcoded user, department, and LLM configuration data in components.
* Simulated AI responses with `setTimeout`.
* No real validation or business logic implemented yet.

#### Missing Features (Refer to High-Level User Stories for the complete list)

* Real-time collaboration.
* File uploads or attachments.
* Integration with external tools.
* Reporting or analytics.

---

### Development Workflow

#### Running the Application

Both frontend and backend are fully functional.

**Backend Setup:**

```bash
# Backend setup (from /Users/blas/Desktop/INRE/INRE-AI-Dock/Back)
cd /Users/blas/Desktop/INRE/INRE-AI-Dock/Back
pip install -r requirements.txt

# Option 1 (Recommended - FastAPI Best Practice):
uvicorn app.main:app --reload --port 8000

# Option 2 (Alternative - Direct Python):
python app/main.py
```

**Frontend Setup:**

```bash
# Frontend setup (from /Users/blas/Desktop/INRE/INRE-AI-Dock/Front)
cd /Users/blas/Desktop/INRE/INRE-AI-Dock/Front
npm install
npm run dev
```

**Application URLs:**
- **Frontend:** `http://localhost:8080`
- **Backend API:** `http://localhost:8000`
- **API Documentation:** `http://localhost:8000/docs`

#### Code Organization

* Each page is self-contained with its own mock data.
* Shared UI components in `components/ui/`.
* Layout components handle navigation and structure.
* No global state management needed due to mock data.

#### Styling Approach

* Tailwind utility classes for all styling.
* shadcn/ui components for a consistent design system.
* Responsive design with a mobile-first approach.
* Dark mode support available but not implemented.

---

### Integration Points (Future)

#### AI Services

* Ready for OpenAI API, Claude API, or local LLM integration.
* Mock functions can be replaced with real API calls.
* Error handling prepared for network failures.

#### Backend API

* React Query setup ready for REST API integration.
* Components structured for easy data fetching integration.
* Form submissions prepared for API endpoints.

#### Database Schema

* Data models defined and ready for the persistence layer.
* Relationships between User, Role, Department, LLMConfiguration, DepartmentQuota, and UsageLog established.
* User management and permissions structure planned.

---

This document serves as a detailed description of the AI Dock App project, its architecture, features, and current implementation status, acting as a functional prototype for future backend integrations and real AI service implementation.

---

Now that this technical details document is tailored to your project, which of the high-level User Stories would you like to work on first?