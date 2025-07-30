"""Remote server communication endpoints."""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Request, HTTPException, Depends, Body, Header
from pydantic import BaseModel
import hashlib
import hmac
import time

from ...core.exceptions import MiddlewareError


router = APIRouter(prefix="/remote", tags=["remote"])


def get_remote_client(request: Request):
    """Dependency to get remote client."""
    return getattr(request.app.state, 'remote_client', None)


def verify_api_key(x_api_key: Optional[str] = Header(None)):
    """Verify API key for authentication."""
    import os
    expected_key = os.getenv('API_KEY')
    
    if not expected_key:
        return True  # No authentication required if no key is set
    
    if not x_api_key or x_api_key != expected_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    return True


def verify_signature(
    request: Request,
    x_signature: Optional[str] = Header(None),
    x_timestamp: Optional[str] = Header(None)
):
    """Verify HMAC signature for secure communication."""
    import os
    secret_key = os.getenv('SECRET_KEY')
    
    if not secret_key:
        return True  # No signature verification if no secret is set
    
    if not x_signature or not x_timestamp:
        raise HTTPException(status_code=401, detail="Missing signature or timestamp")
    
    # Check timestamp (prevent replay attacks)
    try:
        timestamp = int(x_timestamp)
        current_time = int(time.time())
        if abs(current_time - timestamp) > 300:  # 5 minutes tolerance
            raise HTTPException(status_code=401, detail="Request timestamp too old")
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid timestamp")
    
    # Verify signature
    # Note: In a real implementation, you'd need to reconstruct the exact string that was signed
    # This is a simplified example
    string_to_sign = f"{request.method}\\n{request.url}\\n{x_timestamp}"
    
    expected_signature = hmac.new(
        secret_key.encode(),
        string_to_sign.encode(),
        hashlib.sha256
    ).hexdigest()
    
    if not hmac.compare_digest(x_signature, expected_signature):
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    return True


# Request/Response models
class WebhookEndpoint(BaseModel):
    url: str
    enabled: bool = True


class PollingEndpoint(BaseModel):
    url: str
    interval: int = 30  # seconds
    enabled: bool = True


class RemoteCredentials(BaseModel):
    api_key: str
    secret_key: Optional[str] = None


class WebhookTestPayload(BaseModel):
    event_type: str = "test"
    test_data: Dict[str, Any] = {"message": "Test webhook"}


# Configuration endpoints
@router.post("/webhooks/add")
async def add_webhook(
    webhook: WebhookEndpoint = Body(...),
    remote_client=Depends(get_remote_client),
    _auth=Depends(verify_api_key)
) -> Dict[str, str]:
    """Add a webhook endpoint."""
    if not remote_client:
        raise HTTPException(status_code=503, detail="Remote client not available")
    
    remote_client.add_webhook(webhook.url)
    return {"message": f"Webhook added: {webhook.url}"}


@router.post("/polling/add")
async def add_polling_endpoint(
    endpoint: PollingEndpoint = Body(...),
    remote_client=Depends(get_remote_client),
    _auth=Depends(verify_api_key)
) -> Dict[str, str]:
    """Add a polling endpoint."""
    if not remote_client:
        raise HTTPException(status_code=503, detail="Remote client not available")
    
    remote_client.add_polling_endpoint(endpoint.url)
    return {"message": f"Polling endpoint added: {endpoint.url}"}


@router.post("/credentials")
async def set_remote_credentials(
    credentials: RemoteCredentials = Body(...),
    remote_client=Depends(get_remote_client),
    _auth=Depends(verify_api_key)
) -> Dict[str, str]:
    """Set remote API credentials."""
    if not remote_client:
        raise HTTPException(status_code=503, detail="Remote client not available")
    
    remote_client.set_credentials(credentials.api_key, credentials.secret_key)
    return {"message": "Remote credentials updated"}


# Control endpoints
@router.post("/polling/start")
async def start_polling(
    remote_client=Depends(get_remote_client),
    _auth=Depends(verify_api_key)
) -> Dict[str, str]:
    """Start polling remote endpoints."""
    if not remote_client:
        raise HTTPException(status_code=503, detail="Remote client not available")
    
    await remote_client.start_polling()
    return {"message": "Polling started"}


@router.post("/polling/stop")
async def stop_polling(
    remote_client=Depends(get_remote_client),
    _auth=Depends(verify_api_key)
) -> Dict[str, str]:
    """Stop polling remote endpoints."""
    if not remote_client:
        raise HTTPException(status_code=503, detail="Remote client not available")
    
    await remote_client.stop_polling()
    return {"message": "Polling stopped"}


# Testing endpoints
@router.post("/webhook/test")
async def test_webhook(
    payload: WebhookTestPayload = Body(...),
    remote_client=Depends(get_remote_client),
    _auth=Depends(verify_api_key)
) -> Dict[str, str]:
    """Send a test webhook to all configured endpoints."""
    if not remote_client:
        raise HTTPException(status_code=503, detail="Remote client not available")
    
    await remote_client.send_webhook(payload.event_type, payload.test_data)
    return {"message": f"Test webhook sent: {payload.event_type}"}


@router.get("/health")
async def check_remote_health(
    remote_client=Depends(get_remote_client),
    _auth=Depends(verify_api_key)
) -> Dict[str, Any]:
    """Check health of all remote endpoints."""
    if not remote_client:
        raise HTTPException(status_code=503, detail="Remote client not available")
    
    return await remote_client.health_check_endpoints()


# Status endpoints
@router.get("/status")
async def get_remote_status(
    remote_client=Depends(get_remote_client),
    _auth=Depends(verify_api_key)
) -> Dict[str, Any]:
    """Get status of remote communication."""
    if not remote_client:
        return {
            "status": "disabled",
            "message": "Remote client not configured"
        }
    
    return {
        "status": "active",
        "webhooks_configured": len(remote_client.webhook_endpoints),
        "polling_endpoints_configured": len(remote_client.polling_endpoints),
        "polling_active": remote_client.polling_task is not None and not remote_client.polling_task.done(),
        "has_credentials": remote_client.api_key is not None
    }


# Webhook receiving endpoint (for bidirectional communication)
@router.post("/webhook/receive")
async def receive_webhook(
    request: Request,
    payload: Dict[str, Any] = Body(...),
    remote_client=Depends(get_remote_client),
    _signature_auth=Depends(verify_signature)
) -> Dict[str, str]:
    """Receive webhooks from remote servers."""
    if not remote_client:
        raise HTTPException(status_code=503, detail="Remote client not available")
    
    try:
        event_type = payload.get('event_type', 'unknown')
        data = payload.get('data', {})
        
        # Process the incoming webhook
        await remote_client._trigger_event(f"webhook_{event_type}", data)
        
        return {"message": f"Webhook received and processed: {event_type}"}
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing webhook: {str(e)}")


# Event notification endpoints (for manual triggering)
@router.post("/notify/device-discovered")
async def notify_device_discovered(
    device_data: Dict[str, Any] = Body(...),
    remote_client=Depends(get_remote_client),
    _auth=Depends(verify_api_key)
) -> Dict[str, str]:
    """Manually trigger device discovered notification."""
    if not remote_client:
        raise HTTPException(status_code=503, detail="Remote client not available")
    
    await remote_client.notify_device_discovered(device_data)
    return {"message": "Device discovered notification sent"}


@router.post("/notify/system-started")
async def notify_system_started(
    remote_client=Depends(get_remote_client),
    _auth=Depends(verify_api_key)
) -> Dict[str, str]:
    """Manually trigger system started notification."""
    if not remote_client:
        raise HTTPException(status_code=503, detail="Remote client not available")
    
    await remote_client.notify_system_started()
    return {"message": "System started notification sent"}