# Konica Minolta Printer Middleware

A comprehensive middleware framework for integrating Konica Minolta printers with external platforms and services. This solution provides a unified API interface for managing multiple printer models with different UIs and firmware versions.

## Features

- **Unified API**: Single REST API interface for all printer operations
- **Multi-Device Support**: Handle different Konica Minolta models (C654e, C759, C754e, 2100)
- **Multiple Protocols**: HTTP/WCD, IPP, SNMP, and direct printing support
- **Job Management**: Queue, track, and monitor print jobs across all devices
- **Error Handling**: Robust error handling with retry mechanisms
- **Authentication**: Secure device authentication and session management

## Supported Devices

- Konica Minolta C654e (192.168.1.200)
- Konica Minolta C759 (192.168.1.210)  
- Konica Minolta C754e (192.168.1.220)
- Konica Minolta 2100 (192.168.1.131)

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Your Platform  │────┤ Middleware API   │────┤ Device Adapters │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                │                        ├─ HTTP/WCD
                                │                        ├─ IPP
                                │                        ├─ SNMP
                                │                        └─ Direct Print
                                │
                       ┌──────────────────┐
                       │   Job Queue &    │
                       │   Tracking       │
                       └──────────────────┘
```

## Quick Start

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configuration**
   ```bash
   cp .env.example .env
   # Edit .env with your printer IPs and settings
   ```

3. **Run the Middleware**
   ```bash
   python -m uvicorn src.konika_middleware.api.main:app --reload
   ```

4. **Test the API**
   ```bash
   curl http://localhost:8000/api/v1/devices
   ```

## API Endpoints

### Device Management
- `GET /api/v1/devices` - List all available devices
- `GET /api/v1/devices/{device_id}/status` - Get device status
- `POST /api/v1/devices/{device_id}/test` - Test device connectivity

### Print Jobs
- `POST /api/v1/print` - Submit a print job
- `GET /api/v1/jobs` - List all jobs
- `GET /api/v1/jobs/{job_id}` - Get job status
- `DELETE /api/v1/jobs/{job_id}` - Cancel job

### Configuration
- `GET /api/v1/config` - Get current configuration
- `PUT /api/v1/config` - Update configuration

## Development

### Project Structure
```
src/konika_middleware/
├── api/                 # FastAPI application
├── devices/            # Device-specific adapters
├── core/               # Core business logic
└── models/             # Data models
```

### Running Tests
```bash
pytest tests/
```

### Code Formatting
```bash
black src/ tests/
flake8 src/ tests/
```

## License

MIT License - see LICENSE file for details.