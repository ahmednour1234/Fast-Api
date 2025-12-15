from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from sqlalchemy.exc import IntegrityError

from app.core.config import settings
from app.core.exceptions import AppException
from app.core.error_handler import (
    app_exception_handler,
    validation_exception_handler,
    integrity_error_handler,
    general_exception_handler
)
from app.api.routes import auth, users, admin, admin_auth, audit_logs, app_settings, collections, dashboard, roles

app = FastAPI(
    title="FastAPI Production Scaffold",
    description="Production-ready FastAPI with PostgreSQL, JWT Auth, and Clean Architecture",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allows all headers
)

# Register exception handlers
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(IntegrityError, integrity_error_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Mount static files for uploads
upload_dir = Path(settings.UPLOAD_DIR)
upload_dir.mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(admin_auth.router, prefix="/admin/auth", tags=["Admin Authentication"])
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])
app.include_router(audit_logs.router, prefix="/admin", tags=["Audit Logs"])
app.include_router(app_settings.router, prefix="/settings", tags=["Settings"])
app.include_router(collections.router, prefix="/collections", tags=["Collections"])
app.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
app.include_router(roles.router, prefix="/admin", tags=["Roles & Permissions"])

@app.get("/")
async def root():
    return {"message": "FastAPI Production Scaffold", "version": "1.0.0"}

@app.get("/health")
async def health():
    return {"status": "healthy"}
