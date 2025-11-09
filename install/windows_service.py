"""
Windows AI Service
Runs Windows AI backend as a Windows service with auto-start capability
"""

import sys
import os
import time
import logging
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    import win32serviceutil
    import win32service
    import win32event
    import servicemanager
    import win32api
    WINDOWS_SERVICE_AVAILABLE = True
except ImportError:
    WINDOWS_SERVICE_AVAILABLE = False
    print("pywin32 not installed. Install with: pip install pywin32")

# Setup logging
LOG_DIR = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / 'windows_service.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('WindowsAIService')


class WindowsAIService(win32serviceutil.ServiceFramework):
    """Windows service for Windows AI backend"""

    _svc_name_ = "WindowsAI"
    _svc_display_name_ = "Windows AI Assistant"
    _svc_description_ = "AI-powered intelligent assistant for Windows"

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        self.running = True
        self.backend_process = None
        self.watchdog_process = None

    def SvcStop(self):
        """Stop the service"""
        logger.info("Service stop requested")
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.stop_event)
        self.running = False

        # Stop backend and watchdog
        self._stop_processes()

        logger.info("Service stopped")

    def SvcDoRun(self):
        """Main service loop"""
        logger.info("=" * 60)
        logger.info("Windows AI Service Starting")
        logger.info("=" * 60)

        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, '')
        )

        self.main()

    def main(self):
        """Main service execution"""
        try:
            # Start backend server
            self._start_backend()

            # Start watchdog (monitors backend)
            self._start_watchdog()

            # Service loop - just wait for stop event
            logger.info("Service running - waiting for stop event")
            while self.running:
                # Wait for stop event with 5 second timeout
                rc = win32event.WaitForSingleObject(self.stop_event, 5000)
                if rc == win32event.WAIT_OBJECT_0:
                    # Stop event triggered
                    break

                # Check if processes are still running
                if not self._check_processes():
                    logger.warning("Processes died, attempting restart")
                    self._restart_processes()

        except Exception as e:
            logger.error(f"Service error: {e}", exc_info=True)
            servicemanager.LogErrorMsg(f"Windows AI Service error: {str(e)}")
        finally:
            self._stop_processes()

    def _start_backend(self):
        """Start the FastAPI backend"""
        logger.info("Starting Windows AI backend...")

        import subprocess

        # Python executable
        python_exe = sys.executable

        # Backend command
        backend_cmd = [
            python_exe,
            "-m", "uvicorn",
            "windows_ai.main:app",
            "--host", "0.0.0.0",
            "--port", "8010",
            "--log-level", "info"
        ]

        # Start backend process
        try:
            self.backend_process = subprocess.Popen(
                backend_cmd,
                cwd=str(PROJECT_ROOT),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW
            )

            # Wait a moment for startup
            time.sleep(3)

            if self.backend_process.poll() is None:
                logger.info(f"Backend started successfully (PID: {self.backend_process.pid})")
            else:
                logger.error("Backend failed to start")
                raise Exception("Backend startup failed")

        except Exception as e:
            logger.error(f"Failed to start backend: {e}")
            raise

    def _start_watchdog(self):
        """Start the watchdog service"""
        logger.info("Starting watchdog service...")

        import subprocess

        python_exe = sys.executable

        watchdog_cmd = [
            python_exe,
            str(PROJECT_ROOT / "watchdog.py")
        ]

        try:
            self.watchdog_process = subprocess.Popen(
                watchdog_cmd,
                cwd=str(PROJECT_ROOT),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW
            )

            time.sleep(2)

            if self.watchdog_process.poll() is None:
                logger.info(f"Watchdog started successfully (PID: {self.watchdog_process.pid})")
            else:
                logger.warning("Watchdog failed to start (non-critical)")

        except Exception as e:
            logger.warning(f"Failed to start watchdog: {e}")
            # Watchdog is optional, don't fail service

    def _check_processes(self):
        """Check if backend is still running"""
        if self.backend_process:
            return self.backend_process.poll() is None
        return False

    def _restart_processes(self):
        """Restart failed processes"""
        logger.info("Restarting processes...")

        self._stop_processes()
        time.sleep(2)

        try:
            self._start_backend()
            self._start_watchdog()
        except Exception as e:
            logger.error(f"Failed to restart processes: {e}")

    def _stop_processes(self):
        """Stop backend and watchdog processes"""
        logger.info("Stopping processes...")

        # Stop watchdog
        if self.watchdog_process:
            try:
                self.watchdog_process.terminate()
                self.watchdog_process.wait(timeout=10)
                logger.info("Watchdog stopped")
            except Exception as e:
                logger.warning(f"Error stopping watchdog: {e}")
                try:
                    self.watchdog_process.kill()
                except:
                    pass
            self.watchdog_process = None

        # Stop backend
        if self.backend_process:
            try:
                self.backend_process.terminate()
                self.backend_process.wait(timeout=10)
                logger.info("Backend stopped")
            except Exception as e:
                logger.warning(f"Error stopping backend: {e}")
                try:
                    self.backend_process.kill()
                except:
                    pass
            self.backend_process = None


def install_service():
    """Install the Windows service"""
    if not WINDOWS_SERVICE_AVAILABLE:
        print("ERROR: pywin32 not installed")
        print("Install with: pip install pywin32")
        return False

    try:
        print("Installing Windows AI Service...")

        # Install service
        win32serviceutil.InstallService(
            WindowsAIService._svc_reg_class_,
            WindowsAIService._svc_name_,
            WindowsAIService._svc_display_name_,
            description=WindowsAIService._svc_description_,
            startType=win32service.SERVICE_AUTO_START
        )

        print(f"✓ Service '{WindowsAIService._svc_display_name_}' installed successfully")
        print("✓ Configured to start automatically on boot")
        print("")
        print("To start now: net start WindowsAI")
        print("To stop: net stop WindowsAI")
        print("To uninstall: python install/windows_service.py remove")

        return True

    except Exception as e:
        print(f"ERROR: Failed to install service: {e}")
        return False


def remove_service():
    """Remove the Windows service"""
    if not WINDOWS_SERVICE_AVAILABLE:
        print("ERROR: pywin32 not installed")
        return False

    try:
        print("Removing Windows AI Service...")

        # Stop service if running
        try:
            win32serviceutil.StopService(WindowsAIService._svc_name_)
            print("✓ Service stopped")
        except:
            pass

        # Remove service
        win32serviceutil.RemoveService(WindowsAIService._svc_name_)
        print(f"✓ Service '{WindowsAIService._svc_display_name_}' removed successfully")

        return True

    except Exception as e:
        print(f"ERROR: Failed to remove service: {e}")
        return False


def start_service():
    """Start the Windows service"""
    if not WINDOWS_SERVICE_AVAILABLE:
        print("ERROR: pywin32 not installed")
        return False

    try:
        print("Starting Windows AI Service...")
        win32serviceutil.StartService(WindowsAIService._svc_name_)
        print(f"✓ Service '{WindowsAIService._svc_display_name_}' started")
        return True
    except Exception as e:
        print(f"ERROR: Failed to start service: {e}")
        return False


def stop_service():
    """Stop the Windows service"""
    if not WINDOWS_SERVICE_AVAILABLE:
        print("ERROR: pywin32 not installed")
        return False

    try:
        print("Stopping Windows AI Service...")
        win32serviceutil.StopService(WindowsAIService._svc_name_)
        print(f"✓ Service '{WindowsAIService._svc_display_name_}' stopped")
        return True
    except Exception as e:
        print(f"ERROR: Failed to stop service: {e}")
        return False


def restart_service():
    """Restart the Windows service"""
    stop_service()
    time.sleep(2)
    start_service()


if __name__ == '__main__':
    if not WINDOWS_SERVICE_AVAILABLE:
        print("=" * 60)
        print("Windows Service Support Not Available")
        print("=" * 60)
        print("")
        print("To enable Windows service support:")
        print("  pip install pywin32")
        print("")
        print("After installation, run:")
        print("  python install/windows_service.py install")
        print("")
        sys.exit(1)

    if len(sys.argv) == 1:
        # Run as service
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(WindowsAIService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        # Command line interface
        command = sys.argv[1].lower()

        if command == 'install':
            install_service()
        elif command == 'remove' or command == 'uninstall':
            remove_service()
        elif command == 'start':
            start_service()
        elif command == 'stop':
            stop_service()
        elif command == 'restart':
            restart_service()
        else:
            print("Windows AI Service Manager")
            print("")
            print("Usage:")
            print("  python install/windows_service.py install   - Install service")
            print("  python install/windows_service.py remove    - Remove service")
            print("  python install/windows_service.py start     - Start service")
            print("  python install/windows_service.py stop      - Stop service")
            print("  python install/windows_service.py restart   - Restart service")
            print("")
            print("Or use Windows commands:")
            print("  net start WindowsAI")
            print("  net stop WindowsAI")
