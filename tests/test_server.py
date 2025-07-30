#!/usr/bin/env python3
"""Test script to run the middleware server."""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    import uvicorn
    from konika_middleware.api.main import app
    
    if __name__ == "__main__":
        print("Starting Konica Minolta Middleware Server...")
        print("API documentation will be available at: http://localhost:8000/docs")
        
        uvicorn.run(
            "konika_middleware.api.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )

except ImportError as e:
    print(f"Import error: {e}")
    print("Please install requirements: pip install -r requirements.txt")
    sys.exit(1)
except Exception as e:
    print(f"Error starting server: {e}")
    sys.exit(1)