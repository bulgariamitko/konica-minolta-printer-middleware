"""Base adapter class for all device types."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging

from ..models.device import Device
from ..models.job import PrintJob, PrintSettings
from ..models.config import Settings


logger = logging.getLogger(__name__)


class BaseDeviceAdapter(ABC):
    """Base class for all device adapters."""
    
    def __init__(self, device: Device, settings: Settings):
        self.device = device
        self.settings = settings
        self.logger = logging.getLogger(f"{self.__class__.__name__}({device.id})")
    
    @abstractmethod
    async def test_connection(self) -> Dict[str, Any]:
        """Test connection to the device and return status."""
        pass
    
    @abstractmethod
    async def get_status(self) -> Dict[str, Any]:
        """Get current device status and information."""
        pass
    
    @abstractmethod
    async def print_document(self, job: PrintJob) -> Dict[str, Any]:
        """Submit a print job to the device."""
        pass
    
    @abstractmethod
    async def get_capabilities(self) -> Dict[str, Any]:
        """Get device capabilities and supported features."""
        pass
    
    @abstractmethod
    async def authenticate(self) -> bool:
        """Authenticate with the device if required."""
        pass
    
    # Optional methods that can be overridden
    
    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a print job. Default implementation returns False."""
        self.logger.warning(f"Job cancellation not implemented for {self.device.type}")
        return False
    
    async def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific job. Default implementation returns None."""
        self.logger.warning(f"Job status checking not implemented for {self.device.type}")
        return None
    
    async def get_queue_status(self) -> Dict[str, Any]:
        """Get print queue status. Default implementation returns empty queue."""
        return {
            "queue_length": 0,
            "current_job": None,
            "jobs": []
        }
    
    def _log_operation(self, operation: str, **kwargs):
        """Log device operations for debugging."""
        details = " ".join([f"{k}={v}" for k, v in kwargs.items()])
        self.logger.info(f"{operation} - {details}")
    
    def _handle_error(self, operation: str, error: Exception) -> Dict[str, Any]:
        """Standard error handling for device operations."""
        error_msg = f"{operation} failed: {str(error)}"
        self.logger.error(error_msg, exc_info=True)
        
        return {
            "status": "error",
            "operation": operation,
            "message": error_msg,
            "error_type": type(error).__name__
        }