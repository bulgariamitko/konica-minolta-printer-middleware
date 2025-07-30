# 🖨️ Universal Konica Minolta Printer Middleware

A powerful, universal middleware framework for **automatically discovering and managing Konica Minolta printers** across any network. This solution provides a unified REST API interface that abstracts the complexity of different printer models, firmware versions, administrative interfaces, and Fiery controllers.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)

## ✨ Key Features

### 🔍 **Automatic Device Discovery**
- **Network Scanning**: Automatically discovers Konica Minolta printers on your network
- **SNMP Detection**: Uses SNMP to identify device models, capabilities, and status
- **Fiery Controller Support**: Detects and manages EFI Fiery controllers (C759, C754e)
- **Password Testing**: Automatically tests common admin passwords for each device model
- **Zero Configuration**: No need to manually configure IP addresses or credentials

### 🌐 **Universal Compatibility**
- **Multi-Model Support**: Works with C654e, C759, C754e, 2100, and other KM models
- **Fiery Controllers**: Full support for EFI Fiery RIP controllers
- **Firmware Agnostic**: Handles different firmware versions and UI variations
- **Protocol Support**: HTTP/WCD, SNMP, IPP, and direct printing (port 9100)
- **Smart Adaptation**: Automatically adapts to each device's specific capabilities

### 🔗 **Remote Integration**
- **Webhook Support**: Send real-time notifications to your remote servers
- **Polling**: Continuously check remote endpoints for new print jobs
- **Secure Authentication**: HMAC signatures and API key validation
- **Bidirectional Communication**: Receive commands and jobs from remote systems

### ⚡ **Production Ready**
- **Cron Scheduling**: Automatic startup/shutdown during business hours
- **Health Monitoring**: Comprehensive health checks and status reporting  
- **Error Handling**: Robust error handling with retry mechanisms
- **Scalable Architecture**: Handles multiple devices and concurrent operations

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Your Platform  │────┤ Middleware API   │────┤ Device Adapters │
│  (PHP/Web)      │    │  (FastAPI)       │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                               │                         │
                               │                         ├─ Direct KM (WCD)
                               │                         ├─ Fiery Controllers
                               │                         ├─ SNMP
                               │                         ├─ IPP  
                               │                         └─ Direct Print
                               │
                      ┌──────────────────┐
                      │ Network Discovery│
                      │ & Auto-Config    │
                      └──────────────────┘
```

## 🚀 Quick Start

### 1. Installation

```bash
git clone https://github.com/bulgariamitko/konica-minolta-printer-middleware.git
cd konica-minolta-printer-middleware
pip install -r requirements.txt
```

### 2. Configuration

```bash
# Copy and customize the environment file
cp .env.example .env

# Edit .env with your specific settings
nano .env
```

**Example Configuration Options:**

```bash
# Device Discovery Mode - Choose one approach:

# Option 1: Predefined Machine List (Recommended for production)
AUTO_DISCOVER=false
MACHINE_LIST=192.168.1.100:password1,192.168.1.101:,192.168.1.102:password2

# Option 2: Automatic Network Discovery (Great for initial setup)
AUTO_DISCOVER=true
DISCOVERY_NETWORK=192.168.1.0/24

# Authentication (optional but recommended)
API_KEY=your-secure-api-key-here
SECRET_KEY=your-secret-key-for-hmac-signatures

# Remote Communication (optional)
WEBHOOK_ENDPOINTS=https://your-server.com/webhook
POLLING_ENDPOINTS=https://your-server.com/api/jobs
REMOTE_API_KEY=your-remote-server-api-key

# SNMP Configuration
SNMP_COMMUNITY=public

# Logging
LOG_LEVEL=INFO
LOG_FILE=./logs/middleware.log
```

### 3. Start the Middleware

```bash
# Method 1: Direct start
python -m uvicorn src.konika_middleware.api.main:app --host 0.0.0.0 --port 8000

# Method 2: Using the startup script
./lib/start_middleware.sh start

# Method 3: For development
python tests/test_server.py
```

### 4. Discover Your Printers

The middleware will automatically discover printers when it starts, or you can trigger discovery manually:

```bash
# Discover all printers on your network
curl -X POST "http://localhost:8000/api/v1/devices/discover/network" \
  -H "Content-Type: application/json" \
  -d '{"network": null}'

# Or discover specific IP addresses
curl -X POST "http://localhost:8000/api/v1/devices/discover/ips" \
  -H "Content-Type: application/json" \
  -d '{"ip_addresses": ["192.168.1.200", "192.168.1.210"]}'
```

### 5. View Your Devices

```bash
# List all discovered devices
curl "http://localhost:8000/api/v1/devices/"

# Check device status
curl "http://localhost:8000/api/v1/devices/{device-id}/status"

# Test device connectivity
curl -X POST "http://localhost:8000/api/v1/devices/{device-id}/test"
```

## 🚀 System Service Installation (Recommended)

For production use, install the middleware as a system service with system tray monitoring. **Choose your platform:**

### 🪟 Windows Installation

**🎯 Easy Installation (Double-click):**
```
📁 Double-click: win/install.bat
🗑️ To uninstall: win/uninstall.bat
```

**🔧 Command Line Installation:**
```cmd
# From project root directory
python lib/install_service.py install

# Or run the Windows installer
win\install.bat
```

**💡 What Windows Installation Does:**
- ✅ Creates Windows Service "konica-minolta-middleware"
- ✅ Auto-starts service on Windows boot
- ✅ Installs system tray app in notification area
- ✅ Adds tray app to Windows startup
- ✅ Sets up proper Windows service management

### 🍎 macOS Installation

**🎯 Easy Installation (Terminal):**
```bash
# Make executable and run
chmod +x mac/install.sh
./mac/install.sh
```

**🔧 Command Line Installation:**
```bash
# From project root directory
python3 lib/install_service.py install

# Or run the macOS installer
./mac/install.sh
```

**💡 What macOS Installation Does:**
- ✅ Creates LaunchAgent "com.konicaminolta.middleware"
- ✅ Auto-starts service on macOS login
- ✅ Installs menu bar app
- ✅ Adds menu bar app to macOS startup
- ✅ Sets up proper LaunchAgent management

### 🖥️ System Tray/Menu Bar Features

**📊 Real-time Monitoring:**
- 🟢 Green icon when service + devices are online
- 🔴 Red icon when service is offline
- 📱 Device count indicator in tooltip
- 🔄 Auto-refresh every 10 seconds

**🎛️ Control Menu:**
- 📊 **Dashboard** - Opens web interface (http://localhost:8000)
- 🖨️ **Devices** - Shows connected printers with status
- ⏸️ **Pause/Resume** - Control service state
- 🔄 **Restart Service** - Restart middleware service
- ⚙️ **Settings** - Opens .env configuration file
- 📋 **Logs** - Opens logs directory
- ❌ **Exit** - Quit tray application

### 🧪 Test System Tray/Menu Bar

**Windows:**
```cmd
win\test_tray.bat
```

**macOS:**
```bash
./mac/test_tray.sh
```

**Manual Test (Both Platforms):**
```bash
python3 lib/test_tray.py
```

### 🚀 Start Tray/Menu Bar Manually

**Windows:**
```cmd
win\start_tray.bat
```

**macOS:**
```bash
./mac/start_tray.sh
```

**Manual Start (Both Platforms):**
```bash
python3 lib/system_tray.py
```

### 🗑️ Uninstallation

**Windows:**
```cmd
# Double-click uninstaller
win\uninstall.bat

# Or command line
python lib/install_service.py uninstall
```

**macOS:**
```bash
# Run uninstaller script
./mac/uninstall.sh

# Or command line
python3 lib/install_service.py uninstall
```

## 📡 API Documentation

Once running, visit:
- **Interactive API Docs**: `http://localhost:8000/docs`
- **ReDoc Documentation**: `http://localhost:8000/redoc`
- **Health Check**: `http://localhost:8000/api/v1/health`

### Core Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/devices/` | GET | List all discovered devices |
| `/api/v1/devices/discover/network` | POST | Discover devices on network |
| `/api/v1/devices/discover/ips` | POST | Discover specific IP addresses |
| `/api/v1/devices/{id}/status` | GET | Get device status |
| `/api/v1/devices/{id}/test` | POST | Test device connectivity |
| `/api/v1/devices/{id}/capabilities` | GET | Get device capabilities |
| `/api/v1/jobs/print` | POST | Submit print job |
| `/api/v1/jobs/{id}` | GET | Get job status |
| `/api/v1/remote/webhooks/add` | POST | Add webhook endpoint |
| `/api/v1/remote/status` | GET | Remote communication status |

## 🔧 Configuration Options

### Device Discovery Options

**🎯 Predefined Machine List (AUTO_DISCOVER=false)**
- **Best for**: Production environments with known printer IPs
- **Format**: `IP:PASSWORD,IP:PASSWORD` (password optional)  
- **Example**: `MACHINE_LIST=192.168.1.100:admin123,192.168.1.101:,192.168.1.102:`
- **Benefits**: Fast startup, predictable, secure

**🔍 Automatic Discovery (AUTO_DISCOVER=true)**
- **Best for**: Initial setup, dynamic environments
- **Scans**: Entire network range for KM devices
- **Example**: `DISCOVERY_NETWORK=192.168.1.0/24`
- **Benefits**: Finds all devices automatically, tests common passwords

### Supported Konica Minolta Models

The middleware automatically detects and configures:

| Model Series | Common Models | Interface Type | Admin Passwords |
|--------------|---------------|----------------|-----------------|
| **C654 Series** | C654, C654e | Direct KM (WCD) | 1234567812345678 |
| **C754 Series** | C754, C754e | Fiery Controller | 12345678 |
| **C759 Series** | C759 | Fiery Controller | 1234567812345678 |
| **2100 Series** | 2100 | Direct KM | 12345678 |
| **Other Models** | bizhub, magicolor | Auto-detected | Common passwords tested |

## 🔥 Fiery Controller Support

This middleware includes comprehensive support for EFI Fiery controllers commonly found on C759 and C754e models:

### Automatic Detection
- **Fiery ES IC-418** (typically on C759)
- **Fiery E100 60-55C-KM** (typically on C754e)
- **Other Fiery Controllers** via web service endpoints

### Fiery Features
- **RIP Processing**: Advanced color management and processing
- **Professional Printing**: High-quality output with finishing options
- **Job Management**: Submit, track, and manage complex print jobs
- **Color Management**: Advanced color profiles and calibration

## 🏢 Production Deployment

### Cron Scheduling

Automatically start/stop during business hours:

```bash
# Add to crontab (crontab -e)
# Start at 8 AM on weekdays
0 8 * * 1-5 /path/to/project/lib/start_middleware.sh cron-start

# Stop at 6 PM on weekdays  
0 18 * * 1-5 /path/to/project/lib/start_middleware.sh cron-stop
```

### Remote Server Integration

Configure your PHP server to communicate with the middleware:

```php
// PHP example for webhook integration
$webhookData = [
    'event_type' => 'print_job_request',
    'data' => [
        'job_id' => '12345',
        'title' => 'Document.pdf',
        'device_preference' => 'color',
        'copies' => 2
    ]
];

$ch = curl_init('http://your-middleware-server:8000/api/v1/remote/webhook/receive');
curl_setopt($ch, CURLOPT_POST, true);
curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($webhookData));
curl_setopt($ch, CURLOPT_HTTPHEADER, [
    'Content-Type: application/json',
    'X-API-Key: your-api-key'
]);
curl_exec($ch);
```

### Docker Deployment (Optional)

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY src/ ./src/
COPY .env .

EXPOSE 8000
CMD ["python", "-m", "uvicorn", "src.konika_middleware.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 🧪 Testing

### Test Device Discovery

```bash
# Run the comprehensive testing suite
python tests/test_real_machines.py

# Test device discovery
python tests/test_discovery.py

# Test Fiery controller detection
python tests/test_fiery_detection.py

# Test specific device connectivity
python tests/test_device.py

# Verify complete setup
python tests/verify_working.py
```

### Test API Endpoints

```bash
# Test health
curl "http://localhost:8000/api/v1/health"

# Test device discovery
curl -X POST "http://localhost:8000/api/v1/devices/discover/network" \
  -H "Content-Type: application/json" -d '{}'

# Test webhook
curl -X POST "http://localhost:8000/api/v1/remote/webhook/test" \
  -H "Content-Type: application/json" \
  -d '{"event_type": "test", "test_data": {"message": "Hello"}}'
```

### Configuration Testing

```bash
# Test different configuration modes
python tests/test_config_modes.py

# Test your specific configuration
python tests/test_your_config.py
```

## 📁 Project Structure

```
konica-minolta-printer-middleware/
├── 🪟 Windows Platform
│   ├── install.bat            # Double-click installer for Windows
│   ├── uninstall.bat          # Double-click uninstaller for Windows
│   ├── start_tray.bat         # Start system tray manually
│   └── test_tray.bat          # Test system tray functionality
├── 🍎 macOS Platform
│   ├── install.sh             # Shell installer for macOS  
│   ├── uninstall.sh           # Shell uninstaller for macOS
│   ├── start_tray.sh          # Start menu bar app manually
│   └── test_tray.sh           # Test menu bar app functionality
├── 📚 Core Library Files
│   ├── install_service.py     # Cross-platform service installer
│   ├── system_tray.py         # Cross-platform tray/menu bar app
│   ├── test_tray.py           # Cross-platform tray test
│   ├── start_middleware.sh    # Advanced startup/management script
│   └── stop_server.py         # Server stop utility
├── 📂 Core Application
│   └── src/konika_middleware/
│       ├── api/               # FastAPI REST API
│       │   ├── main.py        # Application entry point
│       │   └── routers/       # API route handlers
│       ├── devices/           # Device-specific adapters
│       │   ├── base_adapter.py    # Base adapter interface
│       │   ├── km_c654e.py       # C654e direct KM adapter
│       │   ├── fiery_adapter.py  # Fiery controller adapter
│       │   ├── fiery_client.py   # Fiery communication client  
│       │   └── snmp_client.py    # SNMP discovery client
│       ├── core/              # Core business logic
│       │   ├── device_manager.py  # Device lifecycle management
│       │   ├── discovery.py       # Network discovery engine
│       │   ├── remote_client.py   # Remote server integration
│       │   └── exceptions.py      # Custom exceptions
│       └── models/            # Data models
│           ├── device.py         # Device data models
│           ├── job.py            # Print job models
│           └── config.py         # Configuration models
├── 🧪 Tests & Verification
│   └── tests/
│       ├── test_real_machines.py  # Real device testing
│       ├── test_fiery_detection.py # Fiery controller tests
│       ├── verify_working.py      # Complete verification
│       └── ...                   # Additional test files
└── 📋 Configuration & Docs
    ├── .env                      # Environment configuration
    ├── requirements.txt          # Python dependencies
    ├── README.md                 # This comprehensive guide
    └── logs/                     # Runtime logs directory
```

### 🎯 Platform-Specific Entry Points

**🪟 Windows Users:**
- **Install**: Double-click `win/install.bat`
- **Test Tray**: Double-click `win/test_tray.bat`  
- **Start Tray**: Double-click `win/start_tray.bat`
- **Uninstall**: Double-click `win/uninstall.bat`

**🍎 macOS Users:**
- **Install**: Run `./mac/install.sh` in Terminal
- **Test Menu Bar**: Run `./mac/test_tray.sh`
- **Start Menu Bar**: Run `./mac/start_tray.sh`
- **Uninstall**: Run `./mac/uninstall.sh`

**🔧 Advanced Users (Both Platforms):**
- **Service Control**: `python3 lib/install_service.py [install|uninstall]`
- **Tray/Menu Bar**: `python3 lib/system_tray.py`
- **Test Suite**: `python3 lib/test_tray.py`
- **Manual Server Control**: `./lib/start_middleware.sh [start|stop|restart|status]`
- **Stop Server**: `python3 lib/stop_server.py`

## 📋 Requirements

- **Python**: 3.8 or higher
- **Network Access**: Local network access for device discovery
- **SNMP**: Access to SNMP community (usually "public")
- **Ports**: Access to printer ports (80, 443, 631, 9100)

## 🐛 Troubleshooting

### Common Issues

**Q: No devices discovered**
- Check network connectivity and SNMP community string
- Verify printers are powered on and connected to network
- Try specific IP discovery first: `curl -X POST .../discover/ips`

**Q: Fiery controllers not detected**
- Fiery controllers may not respond to standard SNMP
- Check if web interface is accessible on port 80/443
- Verify Fiery controller is powered on and initialized

**Q: Authentication fails**
- Check if admin passwords have been changed from defaults
- Try manual password configuration in device admin interface
- For Fiery controllers, check Command WorkStation access

**Q: Remote communication not working**
- Verify webhook URLs are accessible
- Check API keys and authentication settings
- Review logs for connection errors

**Q: Permission denied on startup script**
- Run: `chmod +x lib/start_middleware.sh`
- Check file permissions and ownership

### Debug Mode

```bash
# Enable debug logging
export DEBUG=true
export LOG_LEVEL=DEBUG

# View logs
tail -f logs/middleware.log
```

### Device-Specific Troubleshooting

**C654e Issues:**
- Usually uses direct KM interface via /wcd/ endpoints
- Check admin password: typically `1234567812345678`

**C759/C754e Issues (Fiery Controllers):**
- These use EFI Fiery controllers, not direct KM interface
- SNMP descriptions: "Fiery ES IC-418" or "Fiery E100 60-55C-KM"
- Access via web interface, not /wcd/ endpoints

**KM2100 Issues:**
- Monochrome printer with direct KM interface
- Admin password: typically `12345678`

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Thanks to the Konica Minolta community for device specifications
- EFI Fiery controller documentation and reverse engineering
- Inspired by various printer management solutions
- Built with FastAPI, aiohttp, and other excellent Python libraries

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/bulgariamitko/konica-minolta-printer-middleware/issues)
- **Discussions**: [GitHub Discussions](https://github.com/bulgariamitko/konica-minolta-printer-middleware/discussions)

---

**Made with ❤️ for the printing community**