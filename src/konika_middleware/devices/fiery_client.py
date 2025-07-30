"""
Fiery Controller Client for Konica Minolta printers with Fiery RIP.
Handles communication with EFI Fiery controllers on C759, C754e, and other models.
"""

import aiohttp
import asyncio
import logging
from typing import Dict, Any, Optional, List
import xml.etree.ElementTree as ET
import json

logger = logging.getLogger(__name__)


class FieryClient:
    """Client for communicating with EFI Fiery controllers."""
    
    def __init__(self, ip_address: str, username: str = "admin", password: str = ""):
        self.ip_address = ip_address
        self.username = username
        self.password = password
        self.base_url = f"http://{ip_address}"
        self.session_cookies = {}
        
        # Common Fiery endpoints
        self.endpoints = {
            'status': '/status',
            'info': '/info',
            'capabilities': '/capabilities',
            'jobs': '/jobs',
            'print': '/print',
            'login': '/login',
            'command': '/command',
            # Fiery-specific endpoints
            'fiery_status': '/wsi/status',
            'fiery_info': '/wsi/deviceinfo',
            'fiery_jobs': '/wsi/jobs',
            'fiery_capabilities': '/wsi/capabilities',
            'fiery_print': '/wsi/print',
        }
    
    async def detect_fiery(self) -> Dict[str, Any]:
        """Detect if this is a Fiery controller and get basic info."""
        timeout = aiohttp.ClientTimeout(total=10)
        
        detection_result = {
            'is_fiery': False,
            'fiery_type': None,
            'version': None,
            'model': None,
            'accessible_endpoints': [],
            'error': None
        }
        
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                # Check common Fiery detection endpoints
                fiery_indicators = [
                    ('/', 'Fiery'),
                    ('/wsi/', 'Fiery Web Services'),
                    ('/status', 'EFI'),
                    ('/info', 'Fiery'),
                    ('/command', 'Command')
                ]
                
                for endpoint, indicator in fiery_indicators:
                    try:
                        url = f"{self.base_url}{endpoint}"
                        async with session.get(url) as response:
                            if response.status in [200, 301, 302]:
                                content = await response.text()
                                if indicator.lower() in content.lower():
                                    detection_result['is_fiery'] = True
                                    detection_result['accessible_endpoints'].append(endpoint)
                                    logger.info(f"Fiery indicator '{indicator}' found at {endpoint}")
                    except Exception as e:
                        logger.debug(f"Fiery detection failed for {endpoint}: {e}")
                
                # Try to get Fiery version info
                if detection_result['is_fiery']:
                    await self._get_fiery_info(session, detection_result)
                    
        except Exception as e:
            detection_result['error'] = str(e)
            logger.error(f"Fiery detection failed for {self.ip_address}: {e}")
        
        return detection_result
    
    async def _get_fiery_info(self, session: aiohttp.ClientSession, result: Dict[str, Any]):
        """Get detailed Fiery information."""
        info_endpoints = ['/wsi/deviceinfo', '/info', '/status', '/command/deviceinfo']
        
        for endpoint in info_endpoints:
            try:
                url = f"{self.base_url}{endpoint}"
                async with session.get(url) as response:
                    if response.status == 200:
                        content = await response.text()
                        
                        # Parse XML if it's XML
                        if content.strip().startswith('<?xml') or content.strip().startswith('<'):
                            try:
                                root = ET.fromstring(content)
                                result['fiery_type'] = 'XML_API'
                                result['version'] = root.get('version') or 'Unknown'
                                result['model'] = root.find('.//model')
                                if result['model'] is not None:
                                    result['model'] = result['model'].text
                                break
                            except ET.ParseError:
                                pass
                        
                        # Parse JSON if it's JSON
                        elif content.strip().startswith('{'):
                            try:
                                data = json.loads(content)
                                result['fiery_type'] = 'JSON_API'
                                result['version'] = data.get('version', 'Unknown')
                                result['model'] = data.get('model', 'Unknown')
                                break
                            except json.JSONDecodeError:
                                pass
                        
                        # Look for common Fiery strings
                        elif any(keyword in content.lower() for keyword in ['fiery', 'efi', 'command workstation']):
                            result['fiery_type'] = 'Web_Interface'
                            # Try to extract version from HTML
                            import re
                            version_match = re.search(r'version\s*[:\s]+([0-9\.]+)', content, re.IGNORECASE)
                            if version_match:
                                result['version'] = version_match.group(1)
                            break
                            
            except Exception as e:
                logger.debug(f"Failed to get info from {endpoint}: {e}")
    
    async def authenticate(self) -> bool:
        """Authenticate with the Fiery controller."""
        if not self.password:
            logger.info("No password provided for Fiery authentication")
            return True  # Some Fiery controllers don't require auth
        
        timeout = aiohttp.ClientTimeout(total=10)
        
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                # Try different authentication methods
                auth_methods = [
                    self._try_basic_auth,
                    self._try_form_auth,
                    self._try_fiery_api_auth
                ]
                
                for auth_method in auth_methods:
                    try:
                        if await auth_method(session):
                            logger.info(f"Fiery authentication successful using {auth_method.__name__}")
                            return True
                    except Exception as e:
                        logger.debug(f"Auth method {auth_method.__name__} failed: {e}")
                
                logger.warning(f"All Fiery authentication methods failed for {self.ip_address}")
                return False
                
        except Exception as e:
            logger.error(f"Fiery authentication error for {self.ip_address}: {e}")
            return False
    
    async def _try_basic_auth(self, session: aiohttp.ClientSession) -> bool:
        """Try HTTP Basic authentication."""
        auth = aiohttp.BasicAuth(self.username, self.password)
        async with session.get(f"{self.base_url}/status", auth=auth) as response:
            return response.status in [200, 301, 302]
    
    async def _try_form_auth(self, session: aiohttp.ClientSession) -> bool:
        """Try form-based authentication."""
        login_data = {
            'username': self.username,
            'password': self.password,
            'login': 'Login'
        }
        
        async with session.post(f"{self.base_url}/login", data=login_data) as response:
            if response.status in [200, 301, 302]:
                # Store session cookies
                for cookie in session.cookie_jar:
                    self.session_cookies[cookie.key] = cookie.value
                return True
        return False
    
    async def _try_fiery_api_auth(self, session: aiohttp.ClientSession) -> bool:
        """Try Fiery-specific API authentication."""
        # Some Fiery controllers use specific API endpoints
        auth_endpoints = ['/wsi/login', '/command/login', '/api/login']
        
        for endpoint in auth_endpoints:
            try:
                auth_data = {
                    'user': self.username,
                    'pass': self.password
                }
                
                async with session.post(f"{self.base_url}{endpoint}", json=auth_data) as response:
                    if response.status in [200, 201]:
                        content = await response.text()
                        if 'success' in content.lower() or 'authenticated' in content.lower():
                            return True
            except Exception:
                continue
        
        return False
    
    async def get_status(self) -> Dict[str, Any]:
        """Get Fiery controller status."""
        timeout = aiohttp.ClientTimeout(total=10)
        
        try:
            async with aiohttp.ClientSession(
                cookies=self.session_cookies,
                timeout=timeout
            ) as session:
                
                # Try different status endpoints
                status_endpoints = ['/wsi/status', '/status', '/command/status']
                
                for endpoint in status_endpoints:
                    try:
                        async with session.get(f"{self.base_url}{endpoint}") as response:
                            if response.status == 200:
                                content = await response.text()
                                return self._parse_status_response(content)
                    except Exception as e:
                        logger.debug(f"Status endpoint {endpoint} failed: {e}")
                
                # Default status if no endpoint works
                return {
                    'status': 'online',
                    'ready': True,
                    'fiery_controller': True,
                    'jobs_pending': 0,
                    'error': None
                }
                
        except Exception as e:
            logger.error(f"Failed to get Fiery status for {self.ip_address}: {e}")
            return {
                'status': 'error',
                'ready': False,
                'error': str(e)
            }
    
    def _parse_status_response(self, content: str) -> Dict[str, Any]:
        """Parse status response from Fiery controller."""
        status = {
            'status': 'online',
            'ready': True,
            'fiery_controller': True,
            'jobs_pending': 0
        }
        
        try:
            # Try XML parsing
            if content.strip().startswith('<?xml') or content.strip().startswith('<'):
                root = ET.fromstring(content)
                status['status'] = root.get('status', 'online')
                status['ready'] = root.get('ready', 'true').lower() == 'true'
                
                jobs_elem = root.find('.//jobs')
                if jobs_elem is not None:
                    status['jobs_pending'] = int(jobs_elem.get('count', 0))
            
            # Try JSON parsing
            elif content.strip().startswith('{'):
                data = json.loads(content)
                status.update(data)
            
            # Parse HTML/text response
            else:
                if 'ready' in content.lower():
                    status['ready'] = True
                if 'busy' in content.lower() or 'processing' in content.lower():
                    status['ready'] = False
                if 'error' in content.lower():
                    status['status'] = 'error'
                    
        except Exception as e:
            logger.debug(f"Failed to parse status response: {e}")
        
        return status
    
    async def get_capabilities(self) -> Dict[str, Any]:
        """Get Fiery controller capabilities."""
        return {
            'supports_color': True,
            'supports_duplex': True,
            'max_paper_size': 'A3',
            'supported_formats': ['PDF', 'PS', 'PCL', 'TIFF', 'JPEG'],
            'fiery_controller': True,
            'rip_processing': True,
            'color_management': True,
            'finishing_options': True,
            'authentication_required': bool(self.password)
        }
    
    async def submit_print_job(self, file_path: str, job_settings: Dict[str, Any] = None) -> Dict[str, Any]:
        """Submit a print job to the Fiery controller."""
        if job_settings is None:
            job_settings = {}
        
        timeout = aiohttp.ClientTimeout(total=60)  # Longer timeout for file uploads
        
        try:
            async with aiohttp.ClientSession(
                cookies=self.session_cookies,
                timeout=timeout
            ) as session:
                
                # Prepare multipart form data
                data = aiohttp.FormData()
                
                # Add file
                with open(file_path, 'rb') as f:
                    data.add_field('file', f.read(), filename=file_path.split('/')[-1])
                
                # Add job settings
                for key, value in job_settings.items():
                    data.add_field(key, str(value))
                
                # Try different print endpoints
                print_endpoints = ['/wsi/print', '/print', '/command/print']
                
                for endpoint in print_endpoints:
                    try:
                        async with session.post(f"{self.base_url}{endpoint}", data=data) as response:
                            if response.status in [200, 201, 202]:
                                content = await response.text()
                                return {
                                    'status': 'submitted',
                                    'job_id': self._extract_job_id(content),
                                    'message': 'Job submitted to Fiery controller'
                                }
                    except Exception as e:
                        logger.debug(f"Print endpoint {endpoint} failed: {e}")
                
                return {
                    'status': 'error',
                    'message': 'Failed to submit job to any Fiery endpoint'
                }
                
        except Exception as e:
            logger.error(f"Failed to submit print job to Fiery {self.ip_address}: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def _extract_job_id(self, response_content: str) -> Optional[str]:
        """Extract job ID from Fiery response."""
        try:
            # Try XML
            if response_content.strip().startswith('<?xml') or response_content.strip().startswith('<'):
                root = ET.fromstring(response_content)
                job_elem = root.find('.//job')
                if job_elem is not None:
                    return job_elem.get('id')
            
            # Try JSON
            elif response_content.strip().startswith('{'):
                data = json.loads(response_content)
                return data.get('job_id') or data.get('id')
            
            # Try to find job ID in text
            else:
                import re
                job_match = re.search(r'job[_\s]*id[:\s]*([a-zA-Z0-9\-_]+)', response_content, re.IGNORECASE)
                if job_match:
                    return job_match.group(1)
                    
        except Exception as e:
            logger.debug(f"Failed to extract job ID: {e}")
        
        return None