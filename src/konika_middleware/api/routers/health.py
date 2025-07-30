"""Health check endpoints."""

from typing import Dict, Any
from fastapi import APIRouter, Request

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> Dict[str, str]:
    """Basic health check endpoint."""
    return {"status": "healthy", "service": "konika-minolta-middleware"}


@router.get("/health/detailed")
async def detailed_health_check(request: Request) -> Dict[str, Any]:
    """Detailed health check with device status."""
    device_manager = request.app.state.device_manager
    
    # Get device statistics
    device_stats = device_manager.get_device_statistics()
    
    # Determine overall health
    overall_status = "healthy"
    if device_stats["online_count"] == 0:
        overall_status = "degraded"
    elif device_stats["error_count"] > 0:
        overall_status = "warning"
    
    return {
        "status": overall_status,
        "service": "konika-minolta-middleware",
        "version": "0.1.0",
        "devices": device_stats,
        "checks": {
            "devices_available": device_stats["online_count"] > 0,
            "all_devices_healthy": device_stats["error_count"] == 0
        }
    }