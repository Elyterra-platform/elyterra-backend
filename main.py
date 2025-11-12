"""
ElyterraX Backend - Main Application Entry Point
Proper layered architecture with Controllers, Services, Repositories, DTOs
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from app.core.config import settings
from app.core.database import check_database_connection
from app.middleware.request_logger import log_api_request

# Import controllers/routers
from app.controllers import user_controller, auth_controller, project_controller, document_controller, lead_controller

# Create FastAPI app
app = FastAPI(
    title=settings.api_title,
    description="Global Real Estate Platform - Proper Architecture with Controllers, Services, Repositories, DTOs",
    version=settings.api_version,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Request Logging Middleware
app.middleware("http")(log_api_request)

# Include routers/controllers
app.include_router(auth_controller.router, prefix="/api")
app.include_router(user_controller.router, prefix="/api")
app.include_router(project_controller.router)
app.include_router(document_controller.router)
app.include_router(lead_controller.router)

# Root endpoints
@app.get("/")
async def root():
    """API root endpoint with system information"""
    return {
        "message": "Welcome to ElyterraX API",
        "version": settings.api_version,
        "status": "operational",
        "architecture": "Layered Architecture (Controller → Service → Repository)",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "ok",
        "service": "elyterra-api",
        "environment": settings.env,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/db/health")
async def database_health():
    """Check database connectivity"""
    is_connected = await check_database_connection()

    return {
        "status": "ok" if is_connected else "error",
        "database": "postgresql",
        "connected": is_connected,
        "host": settings.postgres_host,
        "port": settings.postgres_port,
        "database": settings.postgres_db,
        "message": "Database connected successfully" if is_connected else "Database connection failed",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/api/health")
async def api_health():
    """Alternative health endpoint for monitoring"""
    return {
        "status": "healthy",
        "checks": {
            "api": "up",
            "database": "connected" if await check_database_connection() else "disconnected"
        }
    }
