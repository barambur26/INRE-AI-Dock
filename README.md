# AI Dock App

A secure internal web application that provides a unified interface for enterprise users to access multiple Large Language Models (LLMs) with role-based access control, departmental usage quotas, and comprehensive usage tracking.

## 🎯 Overview

AI Dock App is designed for organizations (particularly those handling sensitive information like banks) to safely access various LLMs through a single, controlled interface. It features:

- **Unified LLM Access**: Connect to OpenAI, Claude, Mistral, and other LLM providers
- **Role-Based Security**: Granular permissions and access controls
- **Usage Management**: Department-based quotas and real-time monitoring
- **Private Deployment**: Designed for intranet or private cloud hosting
- **Comprehensive Logging**: Full audit trail of all LLM interactions

## 🏗️ Architecture

### Frontend
- **React 18** with TypeScript and Vite
- **Tailwind CSS** with shadcn/ui components
- **React Router** for navigation
- **React Query** for state management

### Backend
- **FastAPI** (Python) for API development
- **PostgreSQL** database with SQLAlchemy ORM
- **JWT** authentication with refresh tokens
- **Redis** for caching and background tasks

## 📁 Project Structure

```
AI-Dock/
├── Front/                    # React frontend application
│   ├── src/
│   │   ├── components/       # Reusable UI components
│   │   ├── pages/           # Application pages
│   │   ├── hooks/           # Custom React hooks
│   │   ├── lib/             # Utility functions
│   │   ├── services/        # API communication
│   │   └── types/           # TypeScript definitions
│   └── public/              # Static assets
├── Back/                     # FastAPI backend application
│   ├── app/
│   │   ├── api/             # API routes and endpoints
│   │   ├── core/            # Configuration and security
│   │   ├── models/          # Database models
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── services/        # Business logic
│   │   └── utils/           # Utility functions
│   ├── alembic/             # Database migrations
│   ├── tests/               # Backend tests
│   └── scripts/             # Utility scripts
├── Helpers/                  # Documentation and development aids
│   ├── project_details.md   # Technical specifications
│   ├── backlog.md          # Product backlog
│   └── assistant_prompt.md # Development guidelines
└── docs/                    # Additional documentation
```

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Node.js 18+
- PostgreSQL 13+
- Redis (optional, for production)

### Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd AI-Dock
   ```

2. **Backend Setup**
   ```bash
   cd Back
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   
   # Setup database
   alembic upgrade head
   
   # Start backend server
   uvicorn app.main:app --reload --port 8000
   ```

3. **Frontend Setup**
   ```bash
   cd Front
   npm install
   npm run dev
   ```

4. **Access the application**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## 📋 Current Status

**Phase 1: MVP Development (In Progress)**
- ✅ Project structure setup
- 🚧 Enhanced authentication system
- 📋 User and department management
- 📋 Basic LLM integration
- 📋 Usage tracking and quotas

See `Helpers/backlog.md` for detailed feature status and roadmap.

## 🔒 Security Features

- JWT-based authentication with refresh tokens
- Role-based access control (RBAC)
- Department-based usage quotas
- Comprehensive audit logging
- Secure API key management
- Private deployment ready

## 🎯 Target Users

- **End Users**: Employees who need access to LLMs for their work
- **Department Managers**: Monitor and manage team usage
- **System Administrators**: Configure LLMs, manage users, and monitor system health
- **IT Security**: Audit usage and ensure compliance

## 📊 Key Features

### For Users
- Clean, intuitive chat interface
- Access to multiple LLM providers
- Conversation history and management
- Real-time usage monitoring

### For Administrators
- User and department management
- LLM configuration and routing
- Usage quota management
- Comprehensive analytics dashboard
- Automated alerts and notifications

## 🛠️ Development

### Technology Stack
- **Frontend**: React, TypeScript, Tailwind CSS, Vite
- **Backend**: FastAPI, SQLAlchemy, PostgreSQL, Redis
- **Authentication**: JWT with refresh tokens
- **Deployment**: Docker, Docker Compose

### Development Workflow
1. Check current backlog in `Helpers/backlog.md`
2. Follow development guidelines in `Helpers/assistant_prompt.md`
3. Refer to technical details in `Helpers/project_details.md`

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Follow the development guidelines
4. Submit a pull request

## 📞 Support

For questions or support, please refer to the project documentation in the `Helpers/` directory or create an issue in the repository.
