# Konica Minolta Middleware - Usage Guide

## 🚀 Quick Start

### 1. Start the Middleware Server
```bash
python test_server.py
```

The server will start on `http://localhost:8000` with:
- API documentation at: `http://localhost:8000/docs`
- Interactive API explorer at: `http://localhost:8000/redoc`

### 2. Test Basic Connectivity
```bash
python test_device.py
```

## 📡 API Endpoints

### Health Check
```bash
curl http://localhost:8000/api/v1/health
```

### List All Devices
```bash
curl http://localhost:8000/api/v1/devices/
```

### Get Device Status
```bash
curl http://localhost:8000/api/v1/devices/c654e-main/status
```

### Test Device Connection
```bash
curl -X POST http://localhost:8000/api/v1/devices/c654e-main/test
```

## 🖨️ Current Device Status

Based on the test results, all 4 devices are online and responding:

| Device | Model | IP Address | Status | Features |
|--------|-------|------------|---------|----------|
| c654e-main | C654e | 192.168.1.200 | ✅ Online | Color, Duplex, A3, Auth |
| c759-main | C759 | 192.168.1.210 | ✅ Online | Color, Duplex, A3+ |
| c754e-main | C754e | 192.168.1.220 | ✅ Online | Color, Duplex, A3 |
| km2100-main | 2100 | 192.168.1.131 | ✅ Online | Monochrome, A4 |

## 🔧 Integration Examples

### Check All Devices
```bash
curl -s http://localhost:8000/api/v1/devices/ | jq '.devices[] | {id, name, status, ip_address}'
```

### Get Device Statistics
```bash
curl http://localhost:8000/api/v1/devices/statistics/summary
```

### Submit a Print Job (Basic)
```bash
curl -X POST "http://localhost:8000/api/v1/jobs/print" \
  -F "title=Test Document" \
  -F "file=@your_document.pdf" \
  -F "device_id=c654e-main" \
  -F "copies=1" \
  -F "color_mode=color"
```

## 🛠️ Configuration

### Environment Variables (.env)
```bash
# Printer IPs
PRINTER_C654E_IP=192.168.1.200
PRINTER_C654E_PASSWORD=1234567812345678
PRINTER_C759_IP=192.168.1.210
PRINTER_C754E_IP=192.168.1.220
PRINTER_KM2100_IP=192.168.1.131

# API Settings
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=true

# SNMP Settings
SNMP_COMMUNITY=public
```

## 📊 Monitoring

### Real-time Device Status
The middleware continuously monitors all devices every 30 seconds via:
- HTTP connectivity checks
- SNMP status queries
- Device capability detection
- Toner level monitoring (where supported)

### Health Endpoints
- `/api/v1/health` - Basic health check
- `/api/v1/health/detailed` - Detailed system status
- `/api/v1/status` - Full API and device statistics

## 🔌 Integration with Your Platform

Your file and order management platform can now:

1. **Query Available Devices**
   ```bash
   GET /api/v1/devices/available/list
   ```

2. **Submit Print Jobs**
   ```bash
   POST /api/v1/jobs/print
   ```

3. **Monitor Job Status**
   ```bash
   GET /api/v1/jobs/{job_id}
   ```

4. **Check Device Health**
   ```bash
   GET /api/v1/devices/{device_id}/status
   ```

## 🚨 Error Handling

The API returns proper HTTP status codes:
- `200` - Success
- `400` - Bad Request (validation errors)
- `404` - Device/Job not found
- `500` - Server errors

Example error response:
```json
{
  "error": "DEVICE_NOT_FOUND",
  "message": "Device not found: invalid-device-id"
}
```

## 📈 Next Steps

The middleware is now ready to serve as the bridge between your platform and the Konica Minolta printers. All device communication complexity is abstracted into simple REST API calls.