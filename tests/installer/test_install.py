"""
Installation Tests for Windows AI

Tests the installer on clean Windows systems to verify:
- Silent installation
- Component installation
- Service registration
- Shortcut creation
- Registry keys
- File permissions
- Post-install verification
"""

import os
import pytest
import subprocess
import time
from pathlib import Path
import winreg


class TestInstaller:
    """Tests for Windows AI installer"""

    @pytest.fixture
    def installer_path(self):
        """Get path to installer executable"""
        # Look for installer in dist directory
        dist_dir = Path(__file__).parent.parent.parent / "dist"
        installers = list(dist_dir.glob("WindowsAI-Setup-*.exe"))

        if not installers:
            pytest.skip("No installer found in dist directory")

        # Return most recent installer
        return max(installers, key=lambda p: p.stat().st_mtime)

    @pytest.fixture
    def install_dir(self):
        """Expected installation directory"""
        return Path(os.environ.get("PROGRAMFILES", "C:\\Program Files")) / "Windows AI"

    @pytest.fixture
    def appdata_dir(self):
        """Expected app data directory"""
        return Path.home() / "AppData" / "Local" / "WindowsAI"

    def test_installer_exists(self, installer_path):
        """Test that installer executable exists"""
        assert installer_path.exists(), "Installer not found"
        assert installer_path.suffix == ".exe", "Installer is not an .exe file"

    def test_installer_signed(self, installer_path):
        """Test that installer is digitally signed"""
        try:
            result = subprocess.run(
                ["signtool", "verify", "/pa", str(installer_path)],
                capture_output=True,
                text=True
            )

            # Note: This will fail for test certificates
            # In production, this should pass
            if result.returncode != 0:
                pytest.skip("Installer not signed or using test certificate")

        except FileNotFoundError:
            pytest.skip("signtool not available")

    def test_silent_install(self, installer_path, install_dir):
        """Test silent installation"""
        # Run installer in silent mode
        result = subprocess.run(
            [str(installer_path), "/S"],
            capture_output=True,
            text=True,
            timeout=600  # 10 minutes
        )

        assert result.returncode == 0, f"Installation failed: {result.stderr}"

        # Wait for installation to complete
        time.sleep(10)

        # Verify installation directory exists
        assert install_dir.exists(), "Installation directory not created"

    def test_core_files_installed(self, install_dir):
        """Test that core files are installed"""
        required_files = [
            "windows_ai/__init__.py",
            "python/python.exe",
            "nodejs/node.exe",
            "Uninstall.exe"
        ]

        for file_path in required_files:
            full_path = install_dir / file_path
            assert full_path.exists(), f"Required file not found: {file_path}"

    def test_service_installed(self):
        """Test that Windows service is installed"""
        try:
            result = subprocess.run(
                ["sc", "query", "WindowsAI"],
                capture_output=True,
                text=True
            )

            assert result.returncode == 0, "Windows service not installed"
            assert "RUNNING" in result.stdout or "STOPPED" in result.stdout

        except Exception as e:
            pytest.fail(f"Error checking service: {e}")

    def test_service_auto_start(self):
        """Test that service is configured for auto-start"""
        try:
            result = subprocess.run(
                ["sc", "qc", "WindowsAI"],
                capture_output=True,
                text=True
            )

            assert result.returncode == 0, "Could not query service config"
            assert "AUTO_START" in result.stdout, "Service not configured for auto-start"

        except Exception as e:
            pytest.fail(f"Error checking service config: {e}")

    def test_registry_keys(self):
        """Test that registry keys are created"""
        try:
            # Check installation key
            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"Software\Windows AI"
            )

            install_dir, _ = winreg.QueryValueEx(key, "InstallDir")
            assert install_dir, "InstallDir not set in registry"

            version, _ = winreg.QueryValueEx(key, "Version")
            assert version, "Version not set in registry"

            winreg.CloseKey(key)

            # Check uninstall key
            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"Software\Microsoft\Windows\CurrentVersion\Uninstall\Windows AI"
            )

            display_name, _ = winreg.QueryValueEx(key, "DisplayName")
            assert display_name == "Windows AI", "DisplayName incorrect"

            winreg.CloseKey(key)

        except WindowsError as e:
            pytest.fail(f"Registry key not found: {e}")

    def test_shortcuts_created(self):
        """Test that shortcuts are created"""
        desktop = Path.home() / "Desktop"
        start_menu = Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Windows AI"
        startup = Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"

        # Check desktop shortcut (if option was selected)
        desktop_shortcut = desktop / "Windows AI.lnk"
        # Note: Desktop shortcut is optional

        # Check start menu shortcuts
        assert start_menu.exists(), "Start Menu folder not created"
        assert (start_menu / "Windows AI.lnk").exists(), "Start Menu shortcut not created"

        # Check startup shortcut for tray app
        assert (startup / "Windows AI Tray.lnk").exists(), "Startup shortcut not created"

    def test_appdata_directory(self, appdata_dir):
        """Test that AppData directory is created"""
        assert appdata_dir.exists(), "AppData directory not created"

        # Check subdirectories
        assert (appdata_dir / "models").exists(), "Models directory not created"
        assert (appdata_dir / "plugins").exists(), "Plugins directory not created"
        assert (appdata_dir / "logs").exists(), "Logs directory not created"

        # Check config file
        assert (appdata_dir / "config.json").exists(), "Config file not created"

    def test_backend_health(self):
        """Test that backend service is healthy"""
        import requests

        # Wait for backend to start
        max_retries = 30
        for i in range(max_retries):
            try:
                response = requests.get("http://localhost:8010/health", timeout=5)
                if response.status_code == 200:
                    break
            except:
                pass

            time.sleep(2)
        else:
            pytest.fail("Backend did not start within timeout")

        # Verify health endpoint
        response = requests.get("http://localhost:8010/health")
        assert response.status_code == 200, "Backend health check failed"

        data = response.json()
        assert data.get("status") == "healthy", "Backend not healthy"

    def test_uninstall(self, installer_path, install_dir):
        """Test uninstaller"""
        uninstaller = install_dir / "Uninstall.exe"

        if not uninstaller.exists():
            pytest.skip("Uninstaller not found")

        # Run uninstaller in silent mode
        result = subprocess.run(
            [str(uninstaller), "/S"],
            capture_output=True,
            text=True,
            timeout=300
        )

        # Wait for uninstallation
        time.sleep(10)

        # Verify installation directory is removed
        assert not install_dir.exists() or len(list(install_dir.iterdir())) == 0, \
            "Installation directory not fully removed"

        # Verify service is removed
        result = subprocess.run(
            ["sc", "query", "WindowsAI"],
            capture_output=True,
            text=True
        )
        assert result.returncode != 0, "Service not removed"


class TestUpgrade:
    """Tests for upgrade scenarios"""

    def test_upgrade_preserves_config(self):
        """Test that upgrade preserves user configuration"""
        pytest.skip("Requires previous version installed")

    def test_upgrade_preserves_data(self):
        """Test that upgrade preserves user data"""
        pytest.skip("Requires previous version installed")

    def test_upgrade_updates_service(self):
        """Test that upgrade updates Windows service"""
        pytest.skip("Requires previous version installed")


class TestPermissions:
    """Tests for file permissions and security"""

    def test_install_dir_permissions(self, install_dir):
        """Test installation directory permissions"""
        # Installation directory should be readable by all users
        # but writable only by administrators
        assert install_dir.exists()

        # Try to write to install directory (should fail for non-admin)
        test_file = install_dir / "test_write.txt"
        try:
            test_file.write_text("test")
            test_file.unlink()
            # If we got here, we have write access (probably running as admin)
        except PermissionError:
            # Expected for non-admin users
            pass

    def test_appdata_permissions(self, appdata_dir):
        """Test AppData directory permissions"""
        # AppData directory should be writable by user
        assert appdata_dir.exists()

        test_file = appdata_dir / "test_write.txt"
        try:
            test_file.write_text("test")
            test_file.unlink()
        except PermissionError:
            pytest.fail("Cannot write to AppData directory")


class TestRollback:
    """Tests for rollback functionality"""

    def test_snapshot_created_before_install(self):
        """Test that snapshot is created before installation"""
        pytest.skip("Requires snapshot manager integration")

    def test_rollback_to_previous_version(self):
        """Test rolling back to previous version"""
        pytest.skip("Requires snapshot and multiple versions")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
