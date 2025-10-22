# ElyterraX Backend API

Global Real Estate Investment Platform - Backend API with proper layered architecture.

## 🏗️ Architecture

**Layered Architecture Pattern:**
```
Request → Controller → Service → Repository → Database
          ↓          ↓          ↓
         DTOs    Business    Data Access
                   Logic
```

## 📁 Project Structure

```
app/
├── controllers/     # HTTP endpoints (routes)
├── services/       # Business logic
├── repositories/   # Database operations
├── models/         # SQLAlchemy ORM models
├── dto/           # Pydantic schemas (validation)
└── core/          # Configuration and database
```

## 🚀 Quick Start

### Prerequisites
- Python 3.13+
- PostgreSQL
- Virtual environment activated

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env with your database credentials
```

### 3. Run Migrations
```bash
./migrate.sh up
```

### 4. Start Server
```bash
./run.sh
```

### 5. Access API
- **API:** http://localhost:8000
- **Docs:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

## 📚 Documentation

- **[QUICKSTART.md](QUICKSTART.md)** - Quick setup guide
- **[PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)** - Detailed architecture docs

## 🗄️ Database Migrations

```bash
# Create new migration
./migrate.sh create "description"

# Apply migrations
./migrate.sh up

# Rollback migration
./migrate.sh down

# View history
./migrate.sh history
```

## 🛠️ Development

### Run Development Server
```bash
./run.sh
```

### Run Production Server
```bash
./run-prod.sh
```

## 📋 API Endpoints

### Health & Status
- `GET /` - API root
- `GET /health` - Health check
- `GET /db/health` - Database health

### Users
- `POST /api/users/` - Create user
- `GET /api/users/{id}` - Get user
- `GET /api/users/` - List users
- `PUT /api/users/{id}` - Update user
- `PUT /api/users/{id}/password` - Update password
- `DELETE /api/users/{id}` - Delete user

## 🔐 Environment Variables

```bash
ENV=development
DATABASE_URL=postgresql+psycopg://admin:admin@localhost:5432/realestate_dev
CORS_ORIGINS=http://localhost:3000
SECRET_KEY=your-secret-key
```

## 📦 Tech Stack

- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - ORM for database operations
- **Alembic** - Database migrations
- **Pydantic** - Data validation
- **PostgreSQL** - Database (via psycopg3)
- **Uvicorn** - ASGI server

## 🎯 Features

✅ Layered architecture (Controller-Service-Repository)
✅ Proper separation of concerns
✅ Database migrations with Alembic
✅ Pydantic validation for all requests/responses
✅ Auto-generated API documentation
✅ CORS configuration
✅ PostgreSQL with psycopg3
✅ Environment-based configuration
✅ Health check endpoints

## 🔄 Adding New Features

See [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) for detailed guide on:
- Creating new modules
- Adding database tables
- Writing migrations
- Best practices

## 📝 License

Proprietary - ElyterraX Platform
