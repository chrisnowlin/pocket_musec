"""FastAPI application main module"""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging
from pathlib import Path

from .routes import (
    images,
    settings,
    sessions,
    standards,
    drafts,
    embeddings,
    citations,
    lessons,
    presentations,
    styles,
    workspace,
)
from .middleware import (
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
)
from backend.repositories.migrations import MigrationManager
from backend.config import config

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.logging.level.upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="PocketMusec API",
    description="AI-powered lesson planning assistant for music teachers",
    version=config.api.version,
    docs_url=config.api.docs_url,
    redoc_url=config.api.redoc_url,
    openapi_url=config.api.openapi_url,
)


# Add middleware in reverse order (last added runs first)
# Rate limiting middleware
app.add_middleware(RateLimitMiddleware, requests_per_minute=60)

# Security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# CORS middleware - must be added last so it runs first
cors_origins = config.api.cors_origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in cors_origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(images.router)
app.include_router(settings.router)
app.include_router(sessions.router)
app.include_router(standards.router)
app.include_router(drafts.router)
app.include_router(embeddings.router)
app.include_router(citations.router)
app.include_router(lessons.router)
app.include_router(presentations.router)
app.include_router(styles.router)
app.include_router(workspace.router)


# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    logger.warning(f"Validation error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors(), "body": str(exc.body)},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors"""
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )


# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    logger.info("Starting PocketMusec API...")

    # Check database and run migrations
    db_path = config.database.path
    migration_manager = MigrationManager(db_path)

    # Ensure database directory exists
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    # Run migrations
    try:
        migration_manager.migrate()
        logger.info("Database migrations completed")
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise

    logger.info("PocketMusec API started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down PocketMusec API...")


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "PocketMusec API", "version": "0.3.0"}


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "PocketMusec API", "version": "0.3.0", "docs": "/api/docs"}


if __name__ == "__main__":
    import uvicorn

    # Get configuration from centralized settings
    host = config.api.host
    port = config.api.port
    reload = config.api.reload

    uvicorn.run(
        "backend.api.main:app", host=host, port=port, reload=reload, log_level="info"
    )
