"""FastAPI application main module"""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import os
import logging
from pathlib import Path

from .routes import auth, images, settings
from .middleware import RateLimitMiddleware, AuthRateLimitMiddleware, SecurityHeadersMiddleware
from ..repositories.migrations import MigrationManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="PocketMusec API",
    description="AI-powered lesson planning assistant for music teachers",
    version="0.3.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)


# CORS middleware - configure for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# Rate limiting middleware
app.add_middleware(RateLimitMiddleware, requests_per_minute=60)
app.add_middleware(AuthRateLimitMiddleware, max_attempts=5)


# Include routers
app.include_router(auth.router)
app.include_router(images.router)
app.include_router(settings.router)


# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    logger.warning(f"Validation error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors(), "body": str(exc.body)}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors"""
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )


# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    logger.info("Starting PocketMusec API...")

    # Check database and run migrations
    db_path = os.getenv("DATABASE_PATH", "data/standards/standards.db")
    migration_manager = MigrationManager(db_path)

    # Ensure database directory exists
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    # Run migrations
    try:
        migration_manager.migrate_to_milestone3()
        logger.info("Database migrations completed")

        # Check if default admin exists
        if not migration_manager.check_users_exist():
            logger.warning("No users in database. Create an admin user via POST /api/setup/init-admin")
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise

    # Check JWT secret
    if not os.getenv("JWT_SECRET_KEY"):
        logger.warning("JWT_SECRET_KEY not set. Using default (INSECURE for production!)")
        logger.warning("Set JWT_SECRET_KEY environment variable for production use")

    logger.info("PocketMusec API started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down PocketMusec API...")


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "PocketMusec API",
        "version": "0.3.0"
    }


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "PocketMusec API",
        "version": "0.3.0",
        "docs": "/api/docs"
    }


# Setup endpoint for initial admin creation
@app.post("/api/setup/init-admin", tags=["setup"])
async def initialize_admin(
    email: str,
    password: str,
    full_name: str = "Admin User"
):
    """
    Create initial admin user (only works if no users exist)

    This is a setup endpoint for bootstrapping the system.
    After the first admin is created, use the regular /api/auth/register endpoint.
    """
    from ..auth.password import hash_password

    db_path = os.getenv("DATABASE_PATH", "data/standards/standards.db")
    migration_manager = MigrationManager(db_path)

    # Check if users already exist
    if migration_manager.check_users_exist():
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": "Admin user already exists. Use /api/auth/register to create additional users."}
        )

    try:
        # Hash password and create admin
        password_hash = hash_password(password)
        admin_id = migration_manager.create_default_admin(
            email=email,
            password_hash=password_hash,
            full_name=full_name
        )

        logger.info(f"Initial admin user created: {email}")

        return {
            "message": "Admin user created successfully",
            "admin_id": admin_id,
            "email": email
        }

    except ValueError as e:
        # Password validation error
        raise JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": str(e)}
        )
    except Exception as e:
        logger.error(f"Failed to create admin: {e}")
        raise JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Failed to create admin user"}
        )


if __name__ == "__main__":
    import uvicorn

    # Get configuration from environment
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    reload = os.getenv("API_RELOAD", "true").lower() == "true"

    uvicorn.run(
        "backend.api.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )
