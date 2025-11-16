#!/usr/bin/env python3
"""
Backend API startup script for PocketMusec Desktop Application
"""

import sys
import os
import argparse
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Parse command line arguments
parser = argparse.ArgumentParser(description="Start PocketMusec API")
parser.add_argument("--port", type=int, help="Port to run the server on")
parser.add_argument(
    "--electron-mode", action="store_true", help="Running in Electron mode"
)
args = parser.parse_args()

# Import and run the FastAPI app
if __name__ == "__main__":
    import uvicorn
    from backend.api.main import app
    from backend.config import config

    # Get configuration from centralized settings or command line
    host = config.api.host
    port = args.port or config.api.port
    reload = (
        config.api.reload and not args.electron_mode
    )  # Disable reload in Electron mode

    print(f"Starting PocketMusec API on {host}:{port}")
    if args.electron_mode:
        print("Running in Electron mode")

    uvicorn.run(
        "backend.api.main:app", host=host, port=port, reload=reload, log_level="info"
    )
