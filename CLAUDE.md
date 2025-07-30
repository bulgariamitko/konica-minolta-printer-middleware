# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Universal Konica Minolta Printer Middleware - a FastAPI-based service that automatically discovers and manages Konica Minolta printers across networks. The middleware provides a unified REST API that abstracts the complexity of different printer models, firmware versions, and administrative interfaces.

### Key Capabilities
- **Automatic Device Discovery**: Network scanning with SNMP detection and automatic admin password testing
- **Universal Compatibility**: Works with C654e, C759, C754e, 2100, and other KM models
- **Remote Integration**: Webhook/polling support for bidirectional communication with external servers
- **Production Ready**: Cron scheduling, health monitoring, authentication, and error handling

## Development Commands

### Running the Application
```bash
# Development server
python test_server.py

# Production server via uvicorn
python -m uvicorn src.konika_middleware.api.main:app --host 0.0.0.0 --port 8000

# Using startup script (with cron support)
./start_middleware.sh start
./start_middleware.sh stop
./start_middleware.sh cron-start  # Only starts during business hours
```

### Testing
```bash
# Test device connectivity and discovery
python test_device.py

# Test discovery and remote communication features
python test_discovery.py

# Test API endpoints manually
curl "http://localhost:8000/api/v1/health"
curl "http://localhost:8000/api/v1/devices/"
```

### Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env as needed (most settings are optional due to auto-discovery)
```

## Architecture Overview

### Core Components

**FastAPI Application** (`src/konika_middleware/api/main.py`)
- Main application entry point with lifespan management
- Integrates DeviceManager, RemoteClient, and configuration
- Includes routers for devices, jobs, health, and remote communication

**Device Manager** (`src/konika_middleware/core/device_manager.py`)
- Central coordinator for all printer devices
- Manages device discovery, status monitoring, and adapter creation
- Runs periodic status checks every 30 seconds
- Integrates with NetworkDiscovery for automatic device detection

**Network Discovery** (`src/konika_middleware/core/discovery.py`)
- Automatically scans networks for Konica Minolta devices using SNMP
- Tests common admin passwords (12345678, 1234567812345678) by model
- Identifies device capabilities and creates Device objects
- Supports both network-wide scanning and specific IP testing

**Remote Client** (`src/konika_middleware/core/remote_client.py`)
- Handles webhook notifications and polling for external server integration
- Supports HMAC authentication and API key validation
- Manages bidirectional communication with remote platforms

### Device Architecture

**Base Adapter Pattern** (`src/konika_middleware/devices/base_adapter.py`)
- Abstract base class defining device interaction interface
- All device adapters inherit from BaseDeviceAdapter
- Standardizes methods: test_connection, get_status, print_document, authenticate

**Device-Specific Adapters**:
- `km_c654e.py`: Full implementation with HTTP/WCD interface, SNMP, authentication
- `km_c759.py`, `km_c754e.py`: Inherit from C654e adapter with model-specific capabilities
- `km_2100.py`: Monochrome device with simpler interface

**Protocol Support**:
- HTTP/WCD: Web Control Daemon interface for admin functions
- SNMP: Device monitoring and status (SNMPClient in `snmp_client.py`)
- IPP: Internet Printing Protocol (basic support)
- Direct Print: Raw printing via port 9100

### Data Models

**Device Model** (`src/konika_middleware/models/device.py`)
- Device, DeviceStatus, DeviceType, DeviceCapabilities
- Includes validation and configuration for different device types

**Job Model** (`src/konika_middleware/models/job.py`)
- PrintJob, PrintSettings with support for various print options
- Job status tracking and queue management

**Configuration** (`src/konika_middleware/models/config.py`)
- Environment-based configuration with pydantic-settings
- Supports optional device IPs (since auto-discovery is primary method)

## Key Development Patterns

### Device Discovery Flow
1. NetworkDiscovery scans network range or specific IPs
2. Uses SNMP to identify Konica Minolta devices
3. Tests common admin passwords based on detected model
4. Creates Device objects with discovered capabilities
5. DeviceManager adds devices and creates appropriate adapters

### Authentication Pattern
Devices use cookie-based authentication with the WCD interface:
- Set base cookies (browser info, language, etc.)
- POST to `/wcd/login.cgi` with admin password
- Store session cookies for subsequent authenticated requests

### Remote Communication
- Webhooks: Send notifications about device discovery, job completion, etc.
- Polling: Check remote endpoints for new jobs/commands
- Authentication: HMAC signatures with timestamp validation

### Async Architecture
- All device operations are async to handle multiple devices concurrently
- DeviceManager runs background tasks for periodic status monitoring
- RemoteClient handles polling in background tasks

## Environment Configuration

Most configuration is optional due to auto-discovery:

**Required**: None (fully auto-discovery capable)

**Optional**:
- `API_KEY`, `SECRET_KEY`: For secure remote access
- `WEBHOOK_ENDPOINTS`, `POLLING_ENDPOINTS`: For remote integration
- `SNMP_COMMUNITY`: Default "public" works for most networks
- Specific printer IPs: Only needed to override auto-discovery

## Production Deployment

**Cron Integration**: Use `start_middleware.sh cron-start/cron-stop` for business hours operation

**Remote Server Communication**: Configure webhooks/polling for integration with external platforms (e.g., PHP servers)

**Monitoring**: Health endpoints at `/api/v1/health` and `/api/v1/remote/health`

The middleware is designed to be universally deployable - clone, run, and it will automatically discover and configure any Konica Minolta printers on the network.