"""Device models for printer management."""

from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator


class DeviceType(str, Enum):
    """Supported device types."""
    C654E = "C654e"
    C759 = "C759"
    C754E = "C754e"
    KM2100 = "2100"


class DeviceStatus(str, Enum):
    """Device status states."""
    ONLINE = "online"
    OFFLINE = "offline"
    BUSY = "busy"
    ERROR = "error"
    MAINTENANCE = "maintenance"


class DeviceCapabilities(BaseModel):
    """Device capabilities and features."""
    supports_color: bool = True
    supports_duplex: bool = True
    max_paper_size: str = "A3"
    supported_formats: list[str] = ["PDF", "JPEG", "PNG", "TIFF"]
    max_dpi: int = 1200
    has_finisher: bool = False
    has_stapler: bool = False
    has_hole_punch: bool = False


class Device(BaseModel):
    """Device model representing a Konica Minolta printer."""
    
    id: str = Field(..., description="Unique device identifier")
    name: str = Field(..., description="Human-readable device name")
    type: DeviceType = Field(..., description="Device model type")
    ip_address: str = Field(..., description="Device IP address")
    status: DeviceStatus = Field(default=DeviceStatus.OFFLINE, description="Current status")
    
    # Authentication
    admin_password: Optional[str] = Field(None, description="Admin password for the device")
    
    # Capabilities
    capabilities: DeviceCapabilities = Field(default_factory=DeviceCapabilities)
    
    # Status information
    last_seen: Optional[datetime] = Field(None, description="Last successful communication")
    error_message: Optional[str] = Field(None, description="Current error message if any")
    
    # Device information from SNMP/API
    firmware_version: Optional[str] = None
    serial_number: Optional[str] = None
    page_count: Optional[int] = None
    toner_levels: Optional[Dict[str, int]] = None
    paper_levels: Optional[Dict[str, int]] = None
    
    # Configuration
    snmp_community: str = Field(default="public", description="SNMP community string")
    web_port: int = Field(default=80, description="Web interface port")
    ipp_port: int = Field(default=631, description="IPP port")
    direct_print_port: int = Field(default=9100, description="Direct printing port")
    
    @validator('ip_address')
    def validate_ip_address(cls, v):
        """Validate IP address format."""
        import re
        ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        if not re.match(ip_pattern, v):
            raise ValueError('Invalid IP address format')
        return v
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class DeviceStatusResponse(BaseModel):
    """Response model for device status queries."""
    
    device_id: str
    status: DeviceStatus
    last_updated: datetime
    
    # Current job information
    current_job_id: Optional[str] = None
    jobs_in_queue: int = 0
    
    # Resource levels
    toner_levels: Optional[Dict[str, int]] = None
    paper_levels: Optional[Dict[str, int]] = None
    
    # Error information
    has_errors: bool = False
    error_messages: list[str] = Field(default_factory=list)
    
    # Performance metrics
    pages_printed_today: Optional[int] = None
    uptime_hours: Optional[float] = None


class DeviceListResponse(BaseModel):
    """Response model for device listing."""
    
    devices: list[Device]
    total_count: int
    online_count: int
    offline_count: int