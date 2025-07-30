"""Remote server communication for connecting middleware to external platforms."""

import asyncio
import aiohttp
import logging
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta
import json
import hashlib
import hmac

from ..models.config import Settings


logger = logging.getLogger(__name__)


class RemoteClient:
    """Handles communication with remote servers (webhooks, polling, etc.)."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.webhook_endpoints: List[str] = []
        self.polling_endpoints: List[str] = []
        self.api_key: Optional[str] = None
        self.secret_key: Optional[str] = None
        
        # Event handlers
        self.event_handlers: Dict[str, List[Callable]] = {
            'device_discovered': [],
            'device_status_changed': [],
            'job_completed': [],
            'job_failed': [],
            'system_started': [],
            'system_error': []
        }
        
        # Polling settings
        self.polling_interval = 30  # seconds
        self.polling_task: Optional[asyncio.Task] = None
        
        # Load configuration
        self._load_remote_config()
    
    def _load_remote_config(self) -> None:
        """Load remote server configuration from environment or settings."""
        # These would come from environment variables
        import os
        
        self.webhook_endpoints = os.getenv('WEBHOOK_ENDPOINTS', '').split(',')
        self.webhook_endpoints = [url.strip() for url in self.webhook_endpoints if url.strip()]
        
        self.polling_endpoints = os.getenv('POLLING_ENDPOINTS', '').split(',')
        self.polling_endpoints = [url.strip() for url in self.polling_endpoints if url.strip()]
        
        self.api_key = os.getenv('REMOTE_API_KEY')
        self.secret_key = os.getenv('REMOTE_SECRET_KEY')
        
        logger.info(f"Remote client configured: {len(self.webhook_endpoints)} webhooks, {len(self.polling_endpoints)} polling endpoints")
    
    def add_webhook(self, url: str) -> None:
        """Add a webhook endpoint."""
        if url not in self.webhook_endpoints:
            self.webhook_endpoints.append(url)
            logger.info(f"Added webhook endpoint: {url}")
    
    def add_polling_endpoint(self, url: str) -> None:
        """Add a polling endpoint."""
        if url not in self.polling_endpoints:
            self.polling_endpoints.append(url)
            logger.info(f"Added polling endpoint: {url}")
    
    def set_credentials(self, api_key: str, secret_key: Optional[str] = None) -> None:
        """Set API credentials for remote communication."""
        self.api_key = api_key
        self.secret_key = secret_key
        logger.info("Remote API credentials updated")
    
    async def start_polling(self) -> None:
        """Start polling remote endpoints for jobs/commands."""
        if not self.polling_endpoints:
            logger.info("No polling endpoints configured")
            return
        
        logger.info("Starting remote polling...")
        self.polling_task = asyncio.create_task(self._polling_loop())
    
    async def stop_polling(self) -> None:
        """Stop polling."""
        if self.polling_task:
            self.polling_task.cancel()
            try:
                await self.polling_task
            except asyncio.CancelledError:
                pass
            logger.info("Remote polling stopped")
    
    async def _polling_loop(self) -> None:
        """Main polling loop."""
        while True:
            try:
                await asyncio.sleep(self.polling_interval)
                await self._poll_all_endpoints()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in polling loop: {e}")
    
    async def _poll_all_endpoints(self) -> None:
        """Poll all configured endpoints."""
        tasks = [self._poll_endpoint(url) for url in self.polling_endpoints]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _poll_endpoint(self, url: str) -> None:
        """Poll a single endpoint for new jobs/commands."""
        try:
            headers = self._create_auth_headers('GET', url)
            
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        await self._process_polling_response(url, data)
                    elif response.status != 204:  # 204 = no content (no jobs)
                        logger.warning(f"Polling endpoint {url} returned status {response.status}")
        
        except Exception as e:
            logger.error(f"Error polling endpoint {url}: {e}")
    
    async def _process_polling_response(self, url: str, data: Dict[str, Any]) -> None:
        """Process response from polling endpoint."""
        # Handle different types of responses
        if 'jobs' in data:
            await self._handle_new_jobs(data['jobs'])
        
        if 'commands' in data:
            await self._handle_remote_commands(data['commands'])
        
        if 'config_updates' in data:
            await self._handle_config_updates(data['config_updates'])
    
    async def _handle_new_jobs(self, jobs: List[Dict[str, Any]]) -> None:
        """Handle new print jobs from remote server."""
        logger.info(f"Received {len(jobs)} new jobs from remote server")
        
        for job_data in jobs:
            try:
                # This would integrate with the job manager
                # For now, just log the job
                logger.info(f"New remote job: {job_data.get('title', 'Untitled')} from {job_data.get('source', 'Unknown')}")
                
                # TODO: Convert to PrintJob and submit to job manager
                # job = PrintJob(**job_data)
                # await job_manager.submit_job(job)
                
            except Exception as e:
                logger.error(f"Error processing remote job: {e}")
    
    async def _handle_remote_commands(self, commands: List[Dict[str, Any]]) -> None:
        """Handle remote commands."""
        for command in commands:
            try:
                cmd_type = command.get('type')
                cmd_data = command.get('data', {})
                
                if cmd_type == 'discover_devices':
                    await self._trigger_event('discover_devices_requested', cmd_data)
                elif cmd_type == 'get_device_status':
                    await self._trigger_event('device_status_requested', cmd_data)
                elif cmd_type == 'restart_service':
                    await self._trigger_event('restart_requested', cmd_data)
                
                logger.info(f"Processed remote command: {cmd_type}")
                
            except Exception as e:
                logger.error(f"Error processing remote command: {e}")
    
    async def _handle_config_updates(self, updates: Dict[str, Any]) -> None:
        """Handle configuration updates from remote server."""
        logger.info(f"Received configuration updates: {list(updates.keys())}")
        
        # TODO: Apply configuration updates
        # This would update settings and restart services as needed
    
    async def send_webhook(self, event_type: str, data: Dict[str, Any]) -> None:
        """Send webhook notification to all configured endpoints."""
        if not self.webhook_endpoints:
            return
        
        webhook_data = {
            'event_type': event_type,
            'timestamp': datetime.utcnow().isoformat(),
            'data': data,
            'source': 'konika-minolta-middleware'
        }
        
        tasks = [self._send_single_webhook(url, webhook_data) for url in self.webhook_endpoints]
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _send_single_webhook(self, url: str, data: Dict[str, Any]) -> None:
        """Send webhook to a single endpoint."""
        try:
            headers = self._create_auth_headers('POST', url, json.dumps(data))
            headers['Content-Type'] = 'application/json'
            
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, json=data, headers=headers) as response:
                    if response.status in [200, 201, 202]:
                        logger.debug(f"Webhook sent successfully to {url}")
                    else:
                        logger.warning(f"Webhook to {url} returned status {response.status}")
        
        except Exception as e:
            logger.error(f"Error sending webhook to {url}: {e}")
    
    def _create_auth_headers(self, method: str, url: str, body: str = '') -> Dict[str, str]:
        """Create authentication headers for requests."""
        headers = {}
        
        if self.api_key:
            headers['X-API-Key'] = self.api_key
        
        if self.secret_key:
            # Create HMAC signature
            timestamp = str(int(datetime.utcnow().timestamp()))
            string_to_sign = f"{method}\\n{url}\\n{timestamp}\\n{body}"
            
            signature = hmac.new(
                self.secret_key.encode(),
                string_to_sign.encode(),
                hashlib.sha256
            ).hexdigest()
            
            headers['X-Timestamp'] = timestamp
            headers['X-Signature'] = signature
        
        return headers
    
    def register_event_handler(self, event_type: str, handler: Callable) -> None:
        """Register an event handler."""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        
        self.event_handlers[event_type].append(handler)
        logger.debug(f"Registered handler for event: {event_type}")
    
    async def _trigger_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Trigger event handlers."""
        handlers = self.event_handlers.get(event_type, [])
        
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(data)
                else:
                    handler(data)
            except Exception as e:
                logger.error(f"Error in event handler for {event_type}: {e}")
    
    # Public methods for triggering events
    async def notify_device_discovered(self, device_data: Dict[str, Any]) -> None:
        """Notify remote servers about discovered devices."""
        data = {
            'device_id': device_data.get('id'),
            'device_name': device_data.get('name'),
            'ip_address': device_data.get('ip_address'),
            'device_type': device_data.get('type'),
            'capabilities': device_data.get('capabilities', {})
        }
        
        await self.send_webhook('device_discovered', data)
        await self._trigger_event('device_discovered', data)
    
    async def notify_device_status_changed(self, device_id: str, old_status: str, new_status: str) -> None:
        """Notify about device status changes."""
        data = {
            'device_id': device_id,
            'old_status': old_status,
            'new_status': new_status,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        await self.send_webhook('device_status_changed', data)
        await self._trigger_event('device_status_changed', data)
    
    async def notify_job_completed(self, job_id: str, job_details: Dict[str, Any]) -> None:
        """Notify about completed jobs."""
        data = {
            'job_id': job_id,
            'status': 'completed',
            'details': job_details
        }
        
        await self.send_webhook('job_completed', data)
        await self._trigger_event('job_completed', data)
    
    async def notify_job_failed(self, job_id: str, error_message: str) -> None:
        """Notify about failed jobs."""
        data = {
            'job_id': job_id,
            'status': 'failed',
            'error_message': error_message
        }
        
        await self.send_webhook('job_failed', data)
        await self._trigger_event('job_failed', data)
    
    async def notify_system_started(self) -> None:
        """Notify that the middleware system has started."""
        data = {
            'message': 'Konica Minolta Middleware started',
            'timestamp': datetime.utcnow().isoformat(),
            'version': '0.1.0'
        }
        
        await self.send_webhook('system_started', data)
        await self._trigger_event('system_started', data)
    
    async def health_check_endpoints(self) -> Dict[str, Any]:
        """Check health of all configured remote endpoints."""
        results = {
            'webhooks': {},
            'polling_endpoints': {}
        }
        
        # Test webhook endpoints
        for url in self.webhook_endpoints:
            try:
                timeout = aiohttp.ClientTimeout(total=5)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.get(url) as response:
                        results['webhooks'][url] = {
                            'status': 'reachable',
                            'http_status': response.status
                        }
            except Exception as e:
                results['webhooks'][url] = {
                    'status': 'unreachable',
                    'error': str(e)
                }
        
        # Test polling endpoints
        for url in self.polling_endpoints:
            try:
                headers = self._create_auth_headers('GET', url)
                timeout = aiohttp.ClientTimeout(total=5)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.get(url, headers=headers) as response:
                        results['polling_endpoints'][url] = {
                            'status': 'reachable',
                            'http_status': response.status
                        }
            except Exception as e:
                results['polling_endpoints'][url] = {
                    'status': 'unreachable',
                    'error': str(e)
                }
        
        return results