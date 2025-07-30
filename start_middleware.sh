#!/bin/bash

# Konica Minolta Middleware Startup Script
# This script can be called from cron to start the middleware during working hours

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="$SCRIPT_DIR/logs/startup.log"
PID_FILE="$SCRIPT_DIR/middleware.pid"
VENV_PATH="$SCRIPT_DIR/venv"  # Optional: if using virtual environment

# Create logs directory if it doesn't exist
mkdir -p "$SCRIPT_DIR/logs"

# Function to log messages
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Function to check if middleware is already running
is_running() {
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            return 0  # Process is running
        else
            # PID file exists but process is not running, remove stale PID file
            rm -f "$PID_FILE"
            return 1
        fi
    fi
    return 1  # Not running
}

# Function to start the middleware
start_middleware() {
    log "Starting Konica Minolta Middleware..."
    
    # Change to script directory
    cd "$SCRIPT_DIR"
    
    # Activate virtual environment if it exists
    if [ -d "$VENV_PATH" ]; then
        log "Activating virtual environment..."
        source "$VENV_PATH/bin/activate"
    fi
    
    # Start the middleware server
    python -m uvicorn src.konika_middleware.api.main:app \
        --host 0.0.0.0 \
        --port 8000 \
        --log-level info \
        --access-log \
        >> "$LOG_FILE" 2>&1 &
    
    # Save the PID
    echo $! > "$PID_FILE"
    
    log "Middleware started with PID $(cat $PID_FILE)"
    
    # Wait a moment to check if it started successfully
    sleep 3
    
    if is_running; then
        log "Middleware startup successful"
        
        # Test the API endpoint
        if curl -s http://localhost:8000/api/v1/health > /dev/null; then
            log "Health check passed - middleware is responding"
        else
            log "WARNING: Health check failed - middleware may not be fully operational"
        fi
    else
        log "ERROR: Middleware failed to start"
        exit 1
    fi
}

# Function to stop the middleware
stop_middleware() {
    if is_running; then
        local pid=$(cat "$PID_FILE")
        log "Stopping middleware (PID: $pid)..."
        
        # Try graceful shutdown first
        kill -TERM "$pid" 2>/dev/null || true
        
        # Wait for graceful shutdown
        local count=0
        while [ $count -lt 10 ] && ps -p "$pid" > /dev/null 2>&1; do
            sleep 1
            count=$((count + 1))
        done
        
        # Force kill if still running
        if ps -p "$pid" > /dev/null 2>&1; then
            log "Force stopping middleware..."
            kill -KILL "$pid" 2>/dev/null || true
        fi
        
        rm -f "$PID_FILE"
        log "Middleware stopped"
    else
        log "Middleware is not running"
    fi
}

# Function to restart the middleware
restart_middleware() {
    stop_middleware
    sleep 2
    start_middleware
}

# Function to check status
status_middleware() {
    if is_running; then
        local pid=$(cat "$PID_FILE")
        log "Middleware is running (PID: $pid)"
        
        # Test API health
        if curl -s http://localhost:8000/api/v1/health > /dev/null; then
            log "API health check: PASSED"
        else
            log "API health check: FAILED"
        fi
    else
        log "Middleware is not running"
    fi
}

# Function to check if we're in working hours (optional feature)
is_working_hours() {
    local current_hour=$(date +%H)
    local current_day=$(date +%u)  # 1=Monday, 7=Sunday
    
    # Working hours: Monday-Friday, 8 AM - 6 PM
    if [ "$current_day" -ge 1 ] && [ "$current_day" -le 5 ]; then
        if [ "$current_hour" -ge 8 ] && [ "$current_hour" -lt 18 ]; then
            return 0  # In working hours
        fi
    fi
    
    return 1  # Outside working hours
}

# Function for cron-friendly start (only starts if not running and in working hours)
cron_start() {
    # Check if we should be running (working hours)
    if ! is_working_hours; then
        log "Outside working hours - not starting middleware"
        return 0
    fi
    
    # Start only if not already running
    if is_running; then
        log "Middleware already running - no action needed"
    else
        log "Starting middleware for working hours..."
        start_middleware
    fi
}

# Function for cron-friendly stop (stops if outside working hours)
cron_stop() {
    if is_working_hours; then
        log "Still in working hours - not stopping middleware"
        return 0
    fi
    
    if is_running; then
        log "Outside working hours - stopping middleware"
        stop_middleware
    else
        log "Middleware not running - no action needed"
    fi
}

# Main script logic
case "${1:-}" in
    start)
        start_middleware
        ;;
    stop)
        stop_middleware
        ;;
    restart)
        restart_middleware
        ;;
    status)
        status_middleware
        ;;
    cron-start)
        cron_start
        ;;
    cron-stop)
        cron_stop
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|cron-start|cron-stop}"
        echo ""
        echo "Commands:"
        echo "  start      - Start the middleware"
        echo "  stop       - Stop the middleware"
        echo "  restart    - Restart the middleware"
        echo "  status     - Check middleware status"
        echo "  cron-start - Start middleware only during working hours (for cron)"
        echo "  cron-stop  - Stop middleware outside working hours (for cron)"
        echo ""
        echo "Cron examples:"
        echo "  # Start at 8 AM on weekdays"
        echo "  0 8 * * 1-5 /path/to/start_middleware.sh cron-start"
        echo "  # Stop at 6 PM on weekdays"
        echo "  0 18 * * 1-5 /path/to/start_middleware.sh cron-stop"
        exit 1
        ;;
esac