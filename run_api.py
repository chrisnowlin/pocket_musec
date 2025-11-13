#!/usr/bin/env python3
"""
Run the PocketMusec API server

Usage:
    python run_api.py

Environment variables:
    API_HOST: Host to bind to (default: 0.0.0.0)
    API_PORT: Port to bind to (default: 8000)
    API_RELOAD: Enable auto-reload on code changes (default: true)
    DATABASE_PATH: Path to SQLite database (default: data/pocket_musec.db)
    JWT_SECRET_KEY: Secret key for JWT tokens (REQUIRED)
"""

import os
import sys
import secrets
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()


def main():
    """Run the FastAPI server"""

    # Check JWT secret
    jwt_secret = os.getenv("JWT_SECRET_KEY")
    if not jwt_secret or jwt_secret == "your-secret-key-here-change-this-in-production":
        print("=" * 70)
        print("WARNING: JWT_SECRET_KEY not set or using default!")
        print("=" * 70)
        print("\nFor development, generating a temporary secret key...")
        temp_secret = secrets.token_urlsafe(32)
        os.environ["JWT_SECRET_KEY"] = temp_secret
        print(f"Using temporary key: {temp_secret[:20]}...")
        print("\nFor production, set JWT_SECRET_KEY in your .env file:")
        print(f"  JWT_SECRET_KEY={secrets.token_urlsafe(32)}")
        print("=" * 70)
        print()

    # Get configuration
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    reload = os.getenv("API_RELOAD", "true").lower() == "true"

    # Print startup info
    print(f"Starting PocketMusec API server...")
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"Auto-reload: {reload}")
    print(f"API Docs: http://{host}:{port}/api/docs")
    print()

    # Run server
    import uvicorn
    uvicorn.run(
        "backend.api.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )


if __name__ == "__main__":
    main()
