"""
Fiery Controller Device Adapter for Konica Minolta printers.
Handles C759, C754e and other models with EFI Fiery controllers.
"""

import logging
from typing import Dict, Any
import asyncio

from .base_adapter import BaseDeviceAdapter
from .fiery_client import FieryClient
from ..models.device import Device
from ..models.job import PrintJob
from ..models.config import Settings

logger = logging.getLogger(__name__)


class FieryDeviceAdapter(BaseDeviceAdapter):
    """Device adapter for Konica Minolta printers with Fiery controllers."""
    
    def __init__(self, device: Device, settings: Settings):
        super().__init__(device, settings)
        self.fiery_client = FieryClient(
            ip_address=device.ip_address,
            username="admin",
            password=device.admin_password or ""
        )
        self.fiery_info = None
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test connection to the Fiery controller."""
        self._log_operation("test_connection", device=self.device.id)
        
        try:
            # Detect if this is actually a Fiery controller
            detection_result = await self.fiery_client.detect_fiery()
            
            if not detection_result['is_fiery']:
                return {
                    'status': 'error',
                    'message': 'Device does not appear to have a Fiery controller',
                    'fiery_detected': False
                }
            
            # Store Fiery info for later use
            self.fiery_info = detection_result
            
            # Test authentication
            auth_success = await self.fiery_client.authenticate()
            
            # Get basic status
            status = await self.fiery_client.get_status()
            
            return {
                'status': 'success',
                'message': 'Fiery controller connection successful',
                'fiery_detected': True,
                'fiery_type': detection_result.get('fiery_type'),
                'fiery_version': detection_result.get('version'),
                'authentication': 'success' if auth_success else 'failed',
                'controller_status': status.get('status'),
                'ready': status.get('ready', False)
            }
            
        except Exception as e:
            return self._handle_error("test_connection", e)
    
    async def authenticate(self) -> bool:
        """Authenticate with the Fiery controller."""
        try:
            return await self.fiery_client.authenticate()
        except Exception as e:
            logger.error(f"Fiery authentication failed for {self.device.id}: {e}")
            return False
    
    async def get_status(self) -> Dict[str, Any]:
        """Get current device status from Fiery controller."""
        self._log_operation("get_status", device=self.device.id)
        
        try:
            status = await self.fiery_client.get_status()
            
            # Convert Fiery status to our standard format
            device_status = {
                'device_id': self.device.id,
                'status': status.get('status', 'unknown'),
                'ready': status.get('ready', False),
                'fiery_controller': True,
                'jobs_in_queue': status.get('jobs_pending', 0),
                'last_updated': 'now',
                'capabilities': {
                    'color': True,
                    'duplex': True,
                    'finishing': True,
                    'rip_processing': True
                }
            }
            
            # Add Fiery-specific information
            if self.fiery_info:
                device_status['fiery_type'] = self.fiery_info.get('fiery_type')
                device_status['fiery_version'] = self.fiery_info.get('version')
            
            return device_status
            
        except Exception as e:
            return self._handle_error("get_status", e)
    
    async def get_capabilities(self) -> Dict[str, Any]:
        """Get device capabilities from Fiery controller."""
        self._log_operation("get_capabilities", device=self.device.id)
        
        try:
            capabilities = await self.fiery_client.get_capabilities()
            
            # Add device-specific capabilities based on model
            if 'C759' in (self.device.name or ''):
                capabilities.update({
                    'max_paper_size': 'A3+',
                    'max_resolution': '1200x1200',
                    'advanced_color_management': True,
                    'professional_finishing': True
                })
            elif 'C754' in (self.device.name or ''):
                capabilities.update({
                    'max_paper_size': 'A3',
                    'max_resolution': '1200x1200',
                    'standard_finishing': True
                })
            
            return capabilities
            
        except Exception as e:
            return self._handle_error("get_capabilities", e)
    
    async def print_document(self, job: PrintJob) -> Dict[str, Any]:
        """Submit a print job to the Fiery controller."""
        self._log_operation("print_document", 
                          device=self.device.id, 
                          job_id=job.id,
                          file_path=job.file_path)
        
        try:
            # Prepare Fiery-specific job settings
            fiery_settings = self._convert_to_fiery_settings(job.settings)
            
            # Submit job to Fiery controller
            result = await self.fiery_client.submit_print_job(
                file_path=job.file_path,
                job_settings=fiery_settings
            )
            
            if result.get('status') == 'submitted':
                return {
                    'status': 'success',
                    'job_id': result.get('job_id'),
                    'message': f'Job submitted to Fiery controller on {self.device.name}',
                    'fiery_job_id': result.get('job_id'),
                    'estimated_processing_time': self._estimate_processing_time(job)
                }
            else:
                return {
                    'status': 'error',
                    'message': result.get('message', 'Unknown Fiery error'),
                    'fiery_error': True
                }
                
        except Exception as e:
            return self._handle_error("print_document", e)
    
    def _convert_to_fiery_settings(self, settings) -> Dict[str, Any]:
        """Convert print settings to Fiery-specific format."""
        fiery_settings = {}
        
        if hasattr(settings, 'copies'):
            fiery_settings['copies'] = settings.copies
        
        if hasattr(settings, 'duplex') and settings.duplex:
            fiery_settings['duplex'] = 'DuplexTumble'
        
        if hasattr(settings, 'color_mode'):
            if settings.color_mode == 'color':
                fiery_settings['color'] = 'Color'
            else:
                fiery_settings['color'] = 'Grayscale'
        
        if hasattr(settings, 'paper_size'):
            fiery_settings['media'] = settings.paper_size
        
        if hasattr(settings, 'quality'):
            quality_map = {
                'draft': 'Draft',
                'normal': 'Normal',
                'high': 'Best'
            }
            fiery_settings['quality'] = quality_map.get(settings.quality, 'Normal')
        
        # Add Fiery-specific advanced settings
        fiery_settings.update({
            'hold_queue': 'false',  # Process immediately
            'color_management': 'auto',
            'rip_priority': 'normal'
        })
        
        return fiery_settings
    
    def _estimate_processing_time(self, job: PrintJob) -> int:
        """Estimate processing time for Fiery RIP."""
        # Fiery controllers typically take longer due to RIP processing
        base_time = 30  # Base 30 seconds for RIP
        
        if hasattr(job.settings, 'copies'):
            base_time += job.settings.copies * 5
        
        if hasattr(job.settings, 'color_mode') and job.settings.color_mode == 'color':
            base_time += 15  # Color processing takes longer
        
        if hasattr(job.settings, 'quality') and job.settings.quality == 'high':
            base_time += 20  # High quality takes longer
        
        return base_time
    
    async def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get status of a specific job from Fiery controller."""
        # This would require implementing job tracking in FieryClient
        return {
            'job_id': job_id,
            'status': 'processing',
            'fiery_controller': True,
            'message': 'Job status tracking available on Fiery Command WorkStation'
        }
    
    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a job on the Fiery controller."""
        # This would require implementing job cancellation in FieryClient
        logger.warning(f"Job cancellation for Fiery controllers not yet implemented: {job_id}")
        return False
    
    async def get_queue_status(self) -> Dict[str, Any]:
        """Get print queue status from Fiery controller."""
        try:
            status = await self.fiery_client.get_status()
            
            return {
                'queue_length': status.get('jobs_pending', 0),
                'current_job': None,  # Would need specific implementation
                'jobs': [],  # Would need specific implementation
                'fiery_controller': True,
                'rip_queue': True
            }
            
        except Exception as e:
            logger.error(f"Failed to get Fiery queue status for {self.device.id}: {e}")
            return {
                'queue_length': 0,
                'current_job': None,
                'jobs': [],
                'error': str(e)
            }