#!/usr/bin/env python3
"""
Entry point for running the Sentinel API server.
Run this script from the python directory.
"""

import sys
import os

# Add the current directory to Python path so imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

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