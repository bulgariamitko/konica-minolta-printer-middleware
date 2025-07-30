"""Device management endpoints."""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Request, HTTPException, Depends, Body
from pydantic import BaseModel

from ...models.device import Device, DeviceListResponse, DeviceStatusResponse
from ...core.exceptions import DeviceNotFoundError, DeviceError

router = APIRouter(prefix="/devices", tags=["devices"])


def get_device_manager(request: Request):
    """Dependency to get device manager."""
    return request.app.state.device_manager


@router.get("/", response_model=DeviceListResponse)
async def list_devices(device_manager=Depends(get_device_manager)) -> DeviceListResponse:
    """Get list of all configured devices."""
    devices = device_manager.list_devices()
    
    online_count = len([d for d in devices if d.status.value == "online"])
    offline_count = len([d for d in devices if d.status.value == "offline"])
    
    return DeviceListResponse(
        devices=devices,
        total_count=len(devices),
        online_count=online_count,
        offline_count=offline_count
    )


@router.get("/{device_id}", response_model=Device)
async def get_device(device_id: str, device_manager=Depends(get_device_manager)) -> Device:
    """Get details of a specific device."""
    try:
        return device_manager.get_device(device_id)
    except DeviceNotFoundError:
        raise HTTPException(status_code=404, detail=f"Device not found: {device_id}")


@router.get("/{device_id}/status", response_model=DeviceStatusResponse)
async def get_device_status(device_id: str, device_manager=Depends(get_device_manager)) -> DeviceStatusResponse:
    """Get current status of a specific device."""
    try:
        return await device_manager.refresh_device_status(device_id)
    except DeviceNotFoundError:
        raise HTTPException(status_code=404, detail=f"Device not found: {device_id}")
    except DeviceError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{device_id}/test")
async def test_device_connection(device_id: str, device_manager=Depends(get_device_manager)) -> Dict[str, Any]:
    """Test connectivity and functionality of a specific device."""
    try:
        return await device_manager.test_device_connection(device_id)
    except DeviceNotFoundError:
        raise HTTPException(status_code=404, detail=f"Device not found: {device_id}")
    except DeviceError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/refresh")
async def refresh_all_devices(device_manager=Depends(get_device_manager)) -> Dict[str, str]:
    """Refresh status of all devices."""
    try:
        await device_manager.refresh_all_devices()
        return {"message": "All devices refreshed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error refreshing devices: {str(e)}")


@router.get("/online/list", response_model=List[Device])
async def list_online_devices(device_manager=Depends(get_device_manager)) -> List[Device]:
    """Get list of online devices."""
    return device_manager.get_online_devices()


@router.get("/available/list", response_model=List[Device]) 
async def list_available_devices(device_manager=Depends(get_device_manager)) -> List[Device]:
    """Get list of devices available for printing."""
    return device_manager.get_available_devices()


@router.get("/statistics/summary")
async def get_device_statistics(device_manager=Depends(get_device_manager)) -> Dict[str, Any]:
    """Get device statistics summary."""
    return device_manager.get_device_statistics()


# Request models for discovery endpoints
class NetworkDiscoveryRequest(BaseModel):
    network: Optional[str] = None
    

class IPListRequest(BaseModel):
    ip_addresses: List[str]


class ManualDeviceRequest(BaseModel):
    device: Device


# Discovery endpoints
@router.post("/discover/network")
async def discover_network_devices(
    request: NetworkDiscoveryRequest = Body(...),
    device_manager=Depends(get_device_manager)
) -> Dict[str, Any]:
    """Discover Konica Minolta devices on the network."""
    try:
        discovered_devices = await device_manager.discover_devices(request.network)
        return {
            "success": True,
            "message": f"Discovered {len(discovered_devices)} devices",
            "discovered_count": len(discovered_devices),
            "devices": discovered_devices
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Discovery failed: {str(e)}")


@router.post("/discover/ips")
async def discover_specific_ips(
    request: IPListRequest = Body(...),
    device_manager=Depends(get_device_manager)
) -> Dict[str, Any]:
    """Discover devices at specific IP addresses."""
    try:
        discovered_devices = await device_manager.discover_specific_ips(request.ip_addresses)
        return {
            "success": True,
            "message": f"Scanned {len(request.ip_addresses)} IPs, found {len(discovered_devices)} devices",
            "scanned_count": len(request.ip_addresses),
            "discovered_count": len(discovered_devices),
            "devices": discovered_devices
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"IP discovery failed: {str(e)}")


@router.get("/discovery/info")
async def get_discovery_info(device_manager=Depends(get_device_manager)) -> List[Dict[str, Any]]:
    """Get raw discovery information from last scan."""
    return device_manager.get_discovery_info()


@router.post("/add")
async def add_device_manually(
    device: Device = Body(...),
    device_manager=Depends(get_device_manager)
) -> Dict[str, str]:
    """Manually add a device to the manager."""
    try:
        device_manager.add_device_manually(device)
        return {"message": f"Device {device.id} added successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to add device: {str(e)}")


@router.delete("/{device_id}")
async def remove_device(
    device_id: str,
    device_manager=Depends(get_device_manager)
) -> Dict[str, str]:
    """Remove a device from the manager."""
    if device_manager.remove_device(device_id):
        return {"message": f"Device {device_id} removed successfully"}
    else:
        raise HTTPException(status_code=404, detail=f"Device not found: {device_id}")