# Windows AI Watchdog Service

## Overview

The Windows AI Watchdog Service is a production-grade monitoring and auto-restart system that ensures the backend remains healthy and operational. It continuously monitors the backend process, performs health checks, tracks resource usage, and automatically restarts the backend if it becomes unresponsive or crashes.

## Features

### Health Monitoring
- **HTTP Health Checks**: Regularly pings the `/health` endpoint
- **Process Monitoring**: Verifies the backend process is running
- **Automatic Recovery**: Restarts the backend after multiple failed health checks
- **Configurable Thresholds**: Customizable failure limits before restart

### Resource Monitoring
- **CPU Usage Tracking**: Monitors CPU consumption
- **Memory Usage Tracking**: Monitors memory consumption
- **Thread Count Monitoring**: Tracks active threads
- **Uptime Tracking**: Records process uptime
- **Resource Alerts**: Warns when thresholds are exceeded

### Auto-Restart Protection
- **Restart Cooldown**: Prevents rapid restart loops
- **Maximum Restart Attempts**: Limits restarts within a time window
- **Graceful Shutdown**: Attempts graceful termination before force kill
- **Startup Verification**: Ensures process started successfully

### Logging
- **Comprehensive Logging**: All events logged to `watchdog.log`
- **Console Output**: Real-time status updates
- **Structured Logging**: Timestamped events with log levels
- **Error Tracking**: Detailed error messages and stack traces

## Usage

### Starting the Watchdog

**Linux/Mac:**
```bash
./start-watchdog.sh
```

**Windows:**
```cmd
start-watchdog.bat
```

**Direct Python:**
```bash
python watchdog.py
```

### Stopping the Watchdog

Press `Ctrl+C` to gracefully shutdown the watchdog. It will stop the backend process before exiting.

### Automatic Startup

To run the watchdog automatically on system boot:

**Linux (systemd):**
1. Create a systemd service file at `/etc/systemd/system/windows-ai-watchdog.service`:
```ini
[Unit]
Description=Windows AI Watchdog Service
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/Windows-AI
ExecStart=/usr/bin/python3 /path/to/Windows-AI/watchdog.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

2. Enable and start the service:
```bash
sudo systemctl enable windows-ai-watchdog
sudo systemctl start windows-ai-watchdog
```

**Windows (Task Scheduler):**
1. Open Task Scheduler
2. Create a new task
3. Set trigger to "At startup"
4. Set action to run `start-watchdog.bat`
5. Configure to run whether user is logged in or not

## Configuration

The watchdog can be configured through environment variables or by modifying the `WatchdogConfig` class in `watchdog.py`:

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `BACKEND_URL` | `http://127.0.0.1:8010` | Backend base URL |

### Configuration Parameters

Edit these in the `WatchdogConfig` class:

#### Health Check Settings
```python
HEALTH_CHECK_INTERVAL = 30        # Seconds between health checks
HEALTH_TIMEOUT = 10               # Timeout for health check requests
MAX_FAILED_CHECKS = 3             # Failed checks before restart
```

#### Resource Monitoring
```python
RESOURCE_CHECK_INTERVAL = 60      # Seconds between resource checks
MAX_MEMORY_PERCENT = 85.0         # Memory usage warning threshold
MAX_CPU_PERCENT = 90.0            # CPU usage warning threshold
```

#### Restart Protection
```python
RESTART_COOLDOWN = 10             # Seconds to wait before restart
MAX_RESTART_ATTEMPTS = 5          # Max restarts in time window
RESTART_WINDOW_SECONDS = 300      # Time window (5 minutes)
```

## How It Works

### Monitoring Loop

```
┌─────────────────────────────────┐
│   Start Backend Process         │
└───────────┬─────────────────────┘
            │
            ▼
┌─────────────────────────────────┐
│   Health Check Loop (30s)       │
│   - Check process running       │
│   - HTTP GET /health            │
│   - Track failures              │
└───────────┬─────────────────────┘
            │
            ├──[Healthy]─────────► Continue
            │
            ├──[Unhealthy]───────► Restart Backend
            │
            └──[Process Dead]────► Restart Backend

┌─────────────────────────────────┐
│   Resource Check Loop (60s)     │
│   - Monitor CPU usage           │
│   - Monitor memory usage        │
│   - Monitor thread count        │
│   - Log resource stats          │
└─────────────────────────────────┘
```

### Restart Process

1. **Detection**: Failed health checks or dead process detected
2. **Termination**: Attempt graceful shutdown (SIGTERM)
3. **Force Kill**: If not stopped after 10s, force kill (SIGKILL)
4. **Cooldown**: Wait for configured cooldown period
5. **Startup**: Start new backend process
6. **Verification**: Confirm process started successfully
7. **Reset**: Clear failed check counter

### Restart Protection

To prevent infinite restart loops:
- Tracks restart attempts within a sliding time window
- Stops restarting if too many attempts in the window
- Logs critical error and shuts down watchdog

## Monitoring Output

### Console Output Example
```
2025-11-09 10:15:30 - watchdog - INFO - Starting Windows AI Watchdog Service
2025-11-09 10:15:30 - watchdog - INFO - Backend URL: http://127.0.0.1:8010
2025-11-09 10:15:30 - watchdog - INFO - Starting backend: python -m uvicorn windows_ai.main:app --host 0.0.0.0 --port 8010
2025-11-09 10:15:32 - watchdog - INFO - Backend started successfully (PID: 12345)
2025-11-09 10:16:00 - watchdog - INFO - Backend resources - CPU: 5.2%, Memory: 12.3% (456.7 MB), Threads: 8, Uptime: 28s
2025-11-09 10:16:30 - watchdog - DEBUG - Health check passed
```

### Log File Location
All events are logged to `watchdog.log` in the Windows-AI directory.

## Troubleshooting

### Watchdog Won't Start
**Problem**: Script fails to start watchdog
**Solutions**:
- Ensure Python 3.7+ is installed
- Install dependencies: `pip install psutil aiohttp`
- Check file permissions on `watchdog.py`

### Backend Keeps Restarting
**Problem**: Backend repeatedly crashes and restarts
**Solutions**:
- Check `watchdog.log` for error messages
- Review backend logs for crash causes
- Increase `MAX_MEMORY_PERCENT` if memory issues
- Adjust `HEALTH_TIMEOUT` if network is slow

### Too Many Restarts Error
**Problem**: Watchdog gives up after too many restarts
**Solutions**:
- Fix underlying backend crash issue
- Increase `MAX_RESTART_ATTEMPTS` if needed
- Increase `RESTART_WINDOW_SECONDS` for longer window
- Check system resources (disk space, memory, etc.)

### High Resource Usage Warnings
**Problem**: Constant warnings about CPU/memory
**Solutions**:
- Adjust thresholds in `WatchdogConfig`
- Optimize backend performance
- Allocate more system resources
- Check for resource leaks in backend

## Integration with Other Components

### With Backend
- Monitors `/health` endpoint
- Auto-starts backend on system boot
- Restarts backend on crashes
- Logs backend resource usage

### With Tray App
The tray app independently monitors backend status via its own health checks. The watchdog ensures the backend stays running so the tray app can connect to it.

### With Start Scripts
You can still use `start-all.sh` to start all components. The watchdog is an optional enhancement that adds automatic monitoring and restart capabilities.

## Best Practices

1. **Production Deployment**: Always run watchdog in production environments
2. **Monitoring**: Regularly review `watchdog.log` for issues
3. **Resource Limits**: Set appropriate thresholds for your system
4. **Alerts**: Set up external monitoring to alert on watchdog failures
5. **Graceful Shutdown**: Always use `Ctrl+C` to stop the watchdog
6. **System Service**: Configure watchdog as a system service for auto-start

## Dependencies

- **Python 3.7+**
- **psutil**: Process and system monitoring
- **aiohttp**: Async HTTP client for health checks
- **asyncio**: Async I/O and concurrency

Install dependencies:
```bash
pip install psutil aiohttp
```

## Security Considerations

- Watchdog runs with same permissions as user who starts it
- Backend process inherits watchdog's permissions
- No network exposure - local monitoring only
- Logs may contain sensitive process information
- Restrict access to `watchdog.log` in production

## Future Enhancements

Potential improvements for future versions:
- Web dashboard for real-time monitoring
- Email/SMS alerts on failures
- Metrics export (Prometheus, etc.)
- Multiple service monitoring
- Custom health check scripts
- Automatic log rotation
- Performance trending and analysis

## Related Documentation

- [Getting Started](../GETTING_STARTED.md) - Initial setup guide
- [Phase Tracking Sheet](Phase_Tracking_Sheet.md) - Project phase status
- [Roadmap](ROADMAP.md) - Project roadmap and future plans
