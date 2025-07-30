"""Main FastAPI application."""

import logging
import os
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from ..models.config import Config
from ..core.device_manager import DeviceManager
from ..core.remote_client import RemoteClient
from ..core.exceptions import MiddlewareError
from .routers import devices, jobs, health, remote

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Global managers (will be initialized during startup)
device_manager: DeviceManager = None
remote_client: RemoteClient = None
config: Config = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global device_manager, remote_client, config
    
    # Startup
    logger.info("Starting Konica Minolta Middleware...")
    
    # Load configuration
    config = Config.load()
    logger.info(f"Configuration loaded, API will run on {config.api.host}:{config.api.port}")
    
    # Create logs directory if it doesn't exist
    if config.logging.file:
        log_dir = os.path.dirname(config.logging.file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
    
    # Initialize remote client
    remote_client = RemoteClient(config.settings)
    await remote_client.start_polling()
    
    # Initialize device manager
    device_manager = DeviceManager(config.settings)
    await device_manager.start()
    
    # Send startup notification
    await remote_client.notify_system_started()
    
    # Store managers in app state
    app.state.device_manager = device_manager
    app.state.remote_client = remote_client
    app.state.config = config
    
    logger.info("Middleware startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Konica Minolta Middleware...")
    
    if remote_client:
        await remote_client.stop_polling()
    
    if device_manager:
        await device_manager.stop()
    
    logger.info("Middleware shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="Konica Minolta Printer Middleware",
    description="Middleware API for integrating Konica Minolta printers with external platforms",
    version="0.1.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/api/v1")
app.include_router(devices.router, prefix="/api/v1")
app.include_router(jobs.router, prefix="/api/v1")
app.include_router(remote.router, prefix="/api/v1")


@app.exception_handler(MiddlewareError)
async def middleware_exception_handler(request, exc: MiddlewareError):
    """Handle middleware-specific exceptions."""
    return JSONResponse(
        status_code=400,
        content={
            "error": exc.error_code,
            "message": exc.message,
            "details": exc.details
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "INTERNAL_SERVER_ERROR",
            "message": "An internal server error occurred"
        }
    )


@app.get("/")
async def root():
    """Root endpoint with basic information."""
    return {
        "name": "Konica Minolta Printer Middleware",
        "version": "0.1.0",
        "status": "running",
        "api_docs": "/docs",
        "health_check": "/api/v1/health"
    }


@app.get("/api/v1/status")
async def get_api_status() -> Dict[str, Any]:
    """Get API and system status."""
    device_stats = app.state.device_manager.get_device_statistics()
    
    return {
        "api_status": "healthy",
        "version": "0.1.0",
        "uptime_seconds": 0,  # TODO: Implement uptime tracking
        "devices": device_stats,
        "configuration": {
            "max_concurrent_jobs": app.state.config.jobs.max_concurrent_jobs,
            "job_timeout": app.state.config.jobs.job_timeout_seconds,
            "retry_attempts": app.state.config.jobs.retry_attempts
        }
    }