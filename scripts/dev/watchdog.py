#!/usr/bin/env python3
"""
Windows AI Watchdog Service
Monitors the backend health and auto-restarts if needed
"""

import asyncio
import logging
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional
import psutil
import aiohttp
import signal

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('watchdog.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('watchdog')

class WatchdogConfig:
    """Watchdog configuration"""

    # Backend configuration
    BACKEND_URL = os.getenv('BACKEND_URL', 'http://127.0.0.1:8010')
    BACKEND_HEALTH_ENDPOINT = '/health'
    BACKEND_COMMAND = [
        sys.executable, '-m', 'uvicorn',
        'windows_ai.main:app',
        '--host', '0.0.0.0',
        '--port', '8010'
    ]

    # Monitoring intervals (seconds)
    HEALTH_CHECK_INTERVAL = 30
    RESOURCE_CHECK_INTERVAL = 60
    RESTART_COOLDOWN = 10

    # Health check settings
    HEALTH_TIMEOUT = 10
    MAX_FAILED_CHECKS = 3

    # Resource limits
    MAX_MEMORY_PERCENT = 85.0
    MAX_CPU_PERCENT = 90.0

    # Restart settings
    MAX_RESTART_ATTEMPTS = 5
    RESTART_WINDOW_SECONDS = 300  # 5 minutes


class BackendProcess:
    """Manages the backend process"""

    def __init__(self):
        self.process: Optional[subprocess.Popen] = None
        self.pid: Optional[int] = None
        self.start_time: Optional[datetime] = None
        self.restart_count = 0
        self.restart_times = []

    def start(self) -> bool:
        """Start the backend process"""
        try:
            if self.is_running():
                logger.warning("Backend process is already running")
                return True

            logger.info(f"Starting backend: {' '.join(WatchdogConfig.BACKEND_COMMAND)}")

            self.process = subprocess.Popen(
                WatchdogConfig.BACKEND_COMMAND,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=Path(__file__).parent
            )

            self.pid = self.process.pid
            self.start_time = datetime.now()

            # Wait a moment to ensure it started
            time.sleep(2)

            if self.is_running():
                logger.info(f"Backend started successfully (PID: {self.pid})")
                return True
            else:
                logger.error("Backend failed to start")
                return False

        except Exception as e:
            logger.error(f"Failed to start backend: {e}")
            return False

    def stop(self) -> bool:
        """Stop the backend process"""
        try:
            if not self.is_running():
                logger.warning("Backend process is not running")
                return True

            logger.info(f"Stopping backend (PID: {self.pid})")

            if self.process:
                self.process.terminate()
                try:
                    self.process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    logger.warning("Backend didn't stop gracefully, forcing kill")
                    self.process.kill()
                    self.process.wait()

            self.process = None
            self.pid = None
            self.start_time = None

            logger.info("Backend stopped")
            return True

        except Exception as e:
            logger.error(f"Failed to stop backend: {e}")
            return False

    def restart(self) -> bool:
        """Restart the backend process"""
        now = datetime.now()

        # Track restart attempts
        self.restart_times.append(now)
        self.restart_count += 1

        # Clean old restart times outside the window
        cutoff = now.timestamp() - WatchdogConfig.RESTART_WINDOW_SECONDS
        self.restart_times = [
            t for t in self.restart_times
            if t.timestamp() > cutoff
        ]

        # Check if too many restarts in window
        if len(self.restart_times) > WatchdogConfig.MAX_RESTART_ATTEMPTS:
            logger.error(
                f"Too many restart attempts ({len(self.restart_times)}) "
                f"in {WatchdogConfig.RESTART_WINDOW_SECONDS} seconds. Giving up."
            )
            return False

        logger.info(f"Restarting backend (attempt {self.restart_count})")

        self.stop()
        time.sleep(WatchdogConfig.RESTART_COOLDOWN)
        return self.start()

    def is_running(self) -> bool:
        """Check if the backend process is running"""
        if self.process is None:
            return False

        # Check if process is still alive
        poll = self.process.poll()
        if poll is not None:
            return False

        # Double-check via psutil
        if self.pid:
            try:
                return psutil.pid_exists(self.pid)
            except:
                return False

        return True

    def get_resource_usage(self) -> Optional[dict]:
        """Get CPU and memory usage of the backend process"""
        if not self.is_running() or not self.pid:
            return None

        try:
            proc = psutil.Process(self.pid)
            return {
                'cpu_percent': proc.cpu_percent(interval=1),
                'memory_percent': proc.memory_percent(),
                'memory_mb': proc.memory_info().rss / (1024 * 1024),
                'num_threads': proc.num_threads(),
                'uptime_seconds': (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
            }
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            logger.warning(f"Failed to get resource usage: {e}")
            return None


class HealthChecker:
    """Performs health checks on the backend"""

    def __init__(self):
        self.failed_checks = 0
        self.last_successful_check: Optional[datetime] = None

    async def check_health(self) -> bool:
        """Check backend health via HTTP endpoint"""
        try:
            url = f"{WatchdogConfig.BACKEND_URL}{WatchdogConfig.BACKEND_HEALTH_ENDPOINT}"

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    timeout=aiohttp.ClientTimeout(total=WatchdogConfig.HEALTH_TIMEOUT)
                ) as response:
                    if response.status == 200:
                        self.failed_checks = 0
                        self.last_successful_check = datetime.now()
                        logger.debug(f"Health check passed")
                        return True
                    else:
                        self.failed_checks += 1
                        logger.warning(f"Health check failed with status {response.status}")
                        return False

        except asyncio.TimeoutError:
            self.failed_checks += 1
            logger.warning("Health check timed out")
            return False
        except aiohttp.ClientError as e:
            self.failed_checks += 1
            logger.warning(f"Health check failed: {e}")
            return False
        except Exception as e:
            self.failed_checks += 1
            logger.error(f"Health check error: {e}")
            return False

    def is_unhealthy(self) -> bool:
        """Check if backend is unhealthy based on failed checks"""
        return self.failed_checks >= WatchdogConfig.MAX_FAILED_CHECKS


class Watchdog:
    """Main watchdog service"""

    def __init__(self):
        self.backend = BackendProcess()
        self.health_checker = HealthChecker()
        self.running = False
        self.shutdown_event = asyncio.Event()

    async def monitor_health(self):
        """Continuously monitor backend health"""
        while self.running:
            try:
                # Check if process is running
                if not self.backend.is_running():
                    logger.error("Backend process is not running!")
                    if not self.backend.restart():
                        logger.critical("Failed to restart backend, shutting down watchdog")
                        await self.shutdown()
                        break
                    continue

                # Perform health check
                healthy = await self.health_checker.check_health()

                if not healthy and self.health_checker.is_unhealthy():
                    logger.error(
                        f"Backend is unhealthy after {self.health_checker.failed_checks} "
                        f"failed checks. Restarting..."
                    )
                    if not self.backend.restart():
                        logger.critical("Failed to restart backend, shutting down watchdog")
                        await self.shutdown()
                        break

                    # Reset health checker after restart
                    self.health_checker.failed_checks = 0

            except Exception as e:
                logger.error(f"Error in health monitoring: {e}")

            # Wait before next check
            await asyncio.sleep(WatchdogConfig.HEALTH_CHECK_INTERVAL)

    async def monitor_resources(self):
        """Continuously monitor backend resource usage"""
        while self.running:
            try:
                usage = self.backend.get_resource_usage()

                if usage:
                    logger.info(
                        f"Backend resources - "
                        f"CPU: {usage['cpu_percent']:.1f}%, "
                        f"Memory: {usage['memory_percent']:.1f}% ({usage['memory_mb']:.1f} MB), "
                        f"Threads: {usage['num_threads']}, "
                        f"Uptime: {usage['uptime_seconds']:.0f}s"
                    )

                    # Check for resource issues
                    if usage['memory_percent'] > WatchdogConfig.MAX_MEMORY_PERCENT:
                        logger.warning(
                            f"High memory usage: {usage['memory_percent']:.1f}% "
                            f"(threshold: {WatchdogConfig.MAX_MEMORY_PERCENT}%)"
                        )

                    if usage['cpu_percent'] > WatchdogConfig.MAX_CPU_PERCENT:
                        logger.warning(
                            f"High CPU usage: {usage['cpu_percent']:.1f}% "
                            f"(threshold: {WatchdogConfig.MAX_CPU_PERCENT}%)"
                        )

            except Exception as e:
                logger.error(f"Error in resource monitoring: {e}")

            # Wait before next check
            await asyncio.sleep(WatchdogConfig.RESOURCE_CHECK_INTERVAL)

    async def shutdown(self):
        """Gracefully shutdown the watchdog"""
        logger.info("Shutting down watchdog...")
        self.running = False
        self.shutdown_event.set()
        self.backend.stop()

    def handle_signal(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, initiating shutdown")
        asyncio.create_task(self.shutdown())

    async def run(self):
        """Run the watchdog service"""
        logger.info("Starting Windows AI Watchdog Service")
        logger.info(f"Backend URL: {WatchdogConfig.BACKEND_URL}")
        logger.info(f"Health check interval: {WatchdogConfig.HEALTH_CHECK_INTERVAL}s")
        logger.info(f"Resource check interval: {WatchdogConfig.RESOURCE_CHECK_INTERVAL}s")

        # Setup signal handlers
        signal.signal(signal.SIGINT, self.handle_signal)
        signal.signal(signal.SIGTERM, self.handle_signal)

        # Start backend
        if not self.backend.start():
            logger.error("Failed to start backend on initial startup")
            return

        self.running = True

        # Start monitoring tasks
        try:
            await asyncio.gather(
                self.monitor_health(),
                self.monitor_resources(),
                self.shutdown_event.wait()
            )
        except Exception as e:
            logger.error(f"Error in watchdog main loop: {e}")
        finally:
            await self.shutdown()

        logger.info("Watchdog service stopped")


async def main():
    """Main entry point"""
    watchdog = Watchdog()
    await watchdog.run()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Watchdog interrupted by user")
    except Exception as e:
        logger.error(f"Watchdog crashed: {e}")
        sys.exit(1)
