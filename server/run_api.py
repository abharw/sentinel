#!/usr/bin/env python3
"""
Entry point for running the Sentinel API server.
Run this script from the python directory.
"""

import sys
import os
from pathlib import Path

# Add the current directory to Python path so imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables from shared config
shared_config_path = Path(__file__).parent.parent / "shared" / "config" / ".env"
if shared_config_path.exists():
    from dotenv import load_dotenv
    load_dotenv(shared_config_path)
    print(f"Loaded environment from: {shared_config_path}")
else:
    print("Shared config not found, using system environment variables")

import uvicorn
from api.main import app

if __name__ == "__main__":
    uvicorn.run(
        "api.main:app",
        host="127.0.0.1",
        port=8080,
        reload=True,
        log_level="info"
    ) 