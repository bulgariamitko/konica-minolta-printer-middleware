# 🖨️ Universal Konica Minolta Printer Middleware

A powerful, universal middleware framework for **automatically discovering and managing Konica Minolta printers** across any network. This solution provides a unified REST API interface that abstracts the complexity of different printer models, firmware versions, and administrative interfaces.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)

## ✨ Key Features

### 🔍 **Automatic Device Discovery**
- **Network Scanning**: Automatically discovers Konica Minolta printers on your network
- **SNMP Detection**: Uses SNMP to identify device models, capabilities, and status
- **Password Testing**: Automatically tests common admin passwords for each device model
- **Zero Configuration**: No need to manually configure IP addresses or credentials

### 🌐 **Universal Compatibility**
- **Multi-Model Support**: Works with C654e, C759, C754e, 2100, and other KM models
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

## 🚀 Quick Start

### 1. Installation

```bash
git clone https://github.com/yourusername/konika-minolta-middleware.git
cd konika-minolta-middleware
pip install -r requirements.txt
```

### 2. Configuration

```bash
# Copy and customize the environment file
cp .env.example .env

# Edit .env with your specific settings (most settings are optional)
nano .env
```

### 3. Start the Middleware

```bash
# Method 1: Direct start
python -m uvicorn src.konika_middleware.api.main:app --host 0.0.0.0 --port 8000

# Method 2: Using the startup script
./start_middleware.sh start

# Method 3: For development
python test_server.py
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
| `/api/v1/jobs/print` | POST | Submit print job |
| `/api/v1/remote/webhooks/add` | POST | Add webhook endpoint |
| `/api/v1/remote/status` | GET | Remote communication status |

## 🔧 Configuration Options

### Environment Variables

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

| Model Series | Common Models | Auto-Discovery | Admin Passwords |
|--------------|---------------|----------------|-----------------|
| **C654 Series** | C654, C654e | ✅ | 1234567812345678 |
| **C754 Series** | C754, C754e | ✅ | 12345678 |
| **C759 Series** | C759 | ✅ | 1234567812345678 |
| **2100 Series** | 2100 | ✅ | 12345678 |
| **Other Models** | bizhub, magicolor | ✅ | Common passwords tested |

## 🏢 Production Deployment

### Cron Scheduling

Automatically start/stop during business hours:

```bash
# Add to crontab (crontab -e)
# Start at 8 AM on weekdays
0 8 * * 1-5 /path/to/start_middleware.sh cron-start

# Stop at 6 PM on weekdays  
0 18 * * 1-5 /path/to/start_middleware.sh cron-stop
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
# Run the discovery test
python test_discovery.py

# Test specific device connectivity
python test_device.py
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

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Your Platform  │────┤ Middleware API   │────┤ Device Adapters │
│  (PHP/Web)      │    │  (FastAPI)       │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                               │                         │
                               │                         ├─ HTTP/WCD
                               │                         ├─ SNMP
                               │                         ├─ IPP  
                               │                         └─ Direct Print
                               │
                      ┌──────────────────┐
                      │ Network Discovery│
                      │ & Auto-Config    │
                      └──────────────────┘
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📋 Requirements

- **Python**: 3.8 or higher
- **Network Access**: Local network access for device discovery
- **SNMP**: Access to SNMP community (usually "public")
- **Ports**: Access to printer ports (80, 631, 9100)

## 🐛 Troubleshooting

### Common Issues

**Q: No devices discovered**
- Check network connectivity and SNMP community string
- Verify printers are powered on and connected to network
- Try specific IP discovery first: `curl -X POST .../discover/ips`

**Q: Authentication fails**
- Check if admin passwords have been changed from defaults
- Try manual password configuration in device admin interface

**Q: Remote communication not working**
- Verify webhook URLs are accessible
- Check API keys and authentication settings
- Review logs for connection errors

**Q: Permission denied on startup script**
- Run: `chmod +x start_middleware.sh`
- Check file permissions and ownership

### Debug Mode

```bash
# Enable debug logging
export DEBUG=true
export LOG_LEVEL=DEBUG

# View logs
tail -f logs/middleware.log
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Thanks to the Konica Minolta community for device specifications
- Inspired by various printer management solutions
- Built with FastAPI, aiohttp, and other excellent Python libraries

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/konika-minolta-middleware/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/konika-minolta-middleware/discussions)
- **Email**: your-email@example.com

---

**Made with ❤️ for the printing community**