"""
VM Automation for Installer Testing

Automates testing of installers on clean Windows VMs using:
- Hyper-V
- VirtualBox
- VMware (future)
- Cloud VMs (Azure, AWS) (future)

Provides:
- VM provisioning
- Snapshot management
- Test execution
- Result collection
- Cleanup
"""

import subprocess
import time
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum


logger = logging.getLogger(__name__)


class VMProvider(Enum):
    """VM provider types"""
    HYPERV = "hyperv"
    VIRTUALBOX = "virtualbox"
    VMWARE = "vmware"
    AZURE = "azure"
    AWS = "aws"


@dataclass
class VMConfig:
    """VM configuration"""
    name: str
    provider: VMProvider
    os: str  # "Windows 10", "Windows 11", "Windows Server 2019"
    memory_mb: int = 4096
    cpus: int = 2
    disk_gb: int = 60
    base_image: Optional[str] = None


@dataclass
class TestResult:
    """Test execution result"""
    vm_name: str
    test_name: str
    success: bool
    duration_seconds: float
    output: str
    error: Optional[str] = None


class VMAutomation:
    """
    Automates VM-based installer testing
    """

    def __init__(self, provider: VMProvider = VMProvider.HYPERV):
        """
        Initialize VM automation

        Args:
            provider: VM provider to use
        """
        self.provider = provider
        self.vms: Dict[str, Any] = {}

        logger.info(f"VMAutomation initialized with provider: {provider.value}")

    def create_vm(self, config: VMConfig) -> bool:
        """
        Create a new VM

        Args:
            config: VM configuration

        Returns:
            True if successful
        """
        logger.info(f"Creating VM: {config.name}")

        if self.provider == VMProvider.HYPERV:
            return self._create_hyperv_vm(config)
        elif self.provider == VMProvider.VIRTUALBOX:
            return self._create_virtualbox_vm(config)
        else:
            logger.error(f"Provider {self.provider} not implemented")
            return False

    def _create_hyperv_vm(self, config: VMConfig) -> bool:
        """Create Hyper-V VM"""
        try:
            # PowerShell script to create VM
            ps_script = f'''
            $VMName = "{config.name}"
            $Memory = {config.memory_mb}MB
            $CPUs = {config.cpus}

            # Create VM
            New-VM -Name $VMName -MemoryStartupBytes $Memory -Generation 2

            # Set CPU count
            Set-VMProcessor -VMName $VMName -Count $CPUs

            # Create virtual disk if needed
            $VHDPath = "C:\\Users\\Public\\Documents\\Hyper-V\\Virtual Hard Disks\\$VMName.vhdx"
            New-VHD -Path $VHDPath -SizeBytes {config.disk_gb}GB -Dynamic

            # Add disk to VM
            Add-VMHardDiskDrive -VMName $VMName -Path $VHDPath

            Write-Host "VM created successfully"
            '''

            result = subprocess.run(
                ["powershell", "-Command", ps_script],
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode == 0:
                logger.info(f"Hyper-V VM created: {config.name}")
                self.vms[config.name] = config
                return True
            else:
                logger.error(f"Failed to create Hyper-V VM: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"Error creating Hyper-V VM: {e}")
            return False

    def _create_virtualbox_vm(self, config: VMConfig) -> bool:
        """Create VirtualBox VM"""
        try:
            # Create VM
            result = subprocess.run(
                [
                    "VBoxManage", "createvm",
                    "--name", config.name,
                    "--ostype", "Windows10_64",
                    "--register"
                ],
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                logger.error(f"Failed to create VM: {result.stderr}")
                return False

            # Configure VM
            commands = [
                ["VBoxManage", "modifyvm", config.name, "--memory", str(config.memory_mb)],
                ["VBoxManage", "modifyvm", config.name, "--cpus", str(config.cpus)],
                ["VBoxManage", "modifyvm", config.name, "--vram", "128"],
                ["VBoxManage", "modifyvm", config.name, "--nic1", "nat"],
            ]

            for cmd in commands:
                subprocess.run(cmd, capture_output=True, text=True)

            # Create virtual disk
            disk_path = Path.home() / "VirtualBox VMs" / config.name / f"{config.name}.vdi"
            subprocess.run(
                [
                    "VBoxManage", "createhd",
                    "--filename", str(disk_path),
                    "--size", str(config.disk_gb * 1024)
                ],
                capture_output=True,
                text=True
            )

            # Add storage controller
            subprocess.run(
                [
                    "VBoxManage", "storagectl", config.name,
                    "--name", "SATA",
                    "--add", "sata"
                ],
                capture_output=True,
                text=True
            )

            # Attach disk
            subprocess.run(
                [
                    "VBoxManage", "storageattach", config.name,
                    "--storagectl", "SATA",
                    "--port", "0",
                    "--device", "0",
                    "--type", "hdd",
                    "--medium", str(disk_path)
                ],
                capture_output=True,
                text=True
            )

            logger.info(f"VirtualBox VM created: {config.name}")
            self.vms[config.name] = config
            return True

        except Exception as e:
            logger.error(f"Error creating VirtualBox VM: {e}")
            return False

    def start_vm(self, vm_name: str) -> bool:
        """
        Start a VM

        Args:
            vm_name: Name of VM to start

        Returns:
            True if successful
        """
        logger.info(f"Starting VM: {vm_name}")

        if self.provider == VMProvider.HYPERV:
            return self._start_hyperv_vm(vm_name)
        elif self.provider == VMProvider.VIRTUALBOX:
            return self._start_virtualbox_vm(vm_name)
        else:
            return False

    def _start_hyperv_vm(self, vm_name: str) -> bool:
        """Start Hyper-V VM"""
        try:
            result = subprocess.run(
                ["powershell", "-Command", f"Start-VM -Name '{vm_name}'"],
                capture_output=True,
                text=True
            )

            return result.returncode == 0

        except Exception as e:
            logger.error(f"Error starting Hyper-V VM: {e}")
            return False

    def _start_virtualbox_vm(self, vm_name: str) -> bool:
        """Start VirtualBox VM"""
        try:
            result = subprocess.run(
                ["VBoxManage", "startvm", vm_name, "--type", "headless"],
                capture_output=True,
                text=True
            )

            return result.returncode == 0

        except Exception as e:
            logger.error(f"Error starting VirtualBox VM: {e}")
            return False

    def stop_vm(self, vm_name: str) -> bool:
        """
        Stop a VM

        Args:
            vm_name: Name of VM to stop

        Returns:
            True if successful
        """
        logger.info(f"Stopping VM: {vm_name}")

        if self.provider == VMProvider.HYPERV:
            subprocess.run(
                ["powershell", "-Command", f"Stop-VM -Name '{vm_name}' -Force"],
                capture_output=True
            )
            return True
        elif self.provider == VMProvider.VIRTUALBOX:
            subprocess.run(
                ["VBoxManage", "controlvm", vm_name, "poweroff"],
                capture_output=True
            )
            return True
        else:
            return False

    def delete_vm(self, vm_name: str) -> bool:
        """
        Delete a VM

        Args:
            vm_name: Name of VM to delete

        Returns:
            True if successful
        """
        logger.info(f"Deleting VM: {vm_name}")

        # Stop VM first
        self.stop_vm(vm_name)
        time.sleep(2)

        if self.provider == VMProvider.HYPERV:
            subprocess.run(
                ["powershell", "-Command", f"Remove-VM -Name '{vm_name}' -Force"],
                capture_output=True
            )
        elif self.provider == VMProvider.VIRTUALBOX:
            subprocess.run(
                ["VBoxManage", "unregistervm", vm_name, "--delete"],
                capture_output=True
            )

        if vm_name in self.vms:
            del self.vms[vm_name]

        return True

    def copy_file_to_vm(self, vm_name: str, local_path: Path, vm_path: str) -> bool:
        """
        Copy file to VM

        Args:
            vm_name: Name of VM
            local_path: Local file path
            vm_path: Path on VM

        Returns:
            True if successful
        """
        logger.info(f"Copying {local_path} to {vm_name}:{vm_path}")

        if self.provider == VMProvider.HYPERV:
            # Use PowerShell Direct
            ps_script = f'''
            Copy-VMFile -Name "{vm_name}" -SourcePath "{local_path}" -DestinationPath "{vm_path}" -FileSource Host
            '''

            result = subprocess.run(
                ["powershell", "-Command", ps_script],
                capture_output=True,
                text=True
            )

            return result.returncode == 0

        elif self.provider == VMProvider.VIRTUALBOX:
            # Use VBoxManage guestcontrol
            result = subprocess.run(
                [
                    "VBoxManage", "guestcontrol", vm_name,
                    "copyto", str(local_path), vm_path,
                    "--username", "Administrator",
                    "--password", "Password123"  # This should come from config
                ],
                capture_output=True,
                text=True
            )

            return result.returncode == 0

        return False

    def run_command_in_vm(self, vm_name: str, command: str, timeout: int = 300) -> Optional[str]:
        """
        Run command in VM

        Args:
            vm_name: Name of VM
            command: Command to run
            timeout: Timeout in seconds

        Returns:
            Command output, or None on error
        """
        logger.info(f"Running command in {vm_name}: {command}")

        if self.provider == VMProvider.HYPERV:
            ps_script = f'''
            Invoke-Command -VMName "{vm_name}" -ScriptBlock {{ {command} }}
            '''

            result = subprocess.run(
                ["powershell", "-Command", ps_script],
                capture_output=True,
                text=True,
                timeout=timeout
            )

            if result.returncode == 0:
                return result.stdout

        elif self.provider == VMProvider.VIRTUALBOX:
            result = subprocess.run(
                [
                    "VBoxManage", "guestcontrol", vm_name,
                    "run", "--exe", "cmd.exe",
                    "--username", "Administrator",
                    "--password", "Password123",
                    "--", "/c", command
                ],
                capture_output=True,
                text=True,
                timeout=timeout
            )

            if result.returncode == 0:
                return result.stdout

        return None

    def run_installer_test(
        self,
        vm_name: str,
        installer_path: Path,
        test_type: str = "install"
    ) -> TestResult:
        """
        Run installer test on VM

        Args:
            vm_name: Name of VM
            installer_path: Path to installer
            test_type: Type of test (install, upgrade, uninstall)

        Returns:
            TestResult
        """
        start_time = time.time()
        logger.info(f"Running {test_type} test on {vm_name}")

        try:
            # Start VM
            if not self.start_vm(vm_name):
                return TestResult(
                    vm_name=vm_name,
                    test_name=test_type,
                    success=False,
                    duration_seconds=time.time() - start_time,
                    output="",
                    error="Failed to start VM"
                )

            # Wait for VM to boot
            time.sleep(30)

            # Copy installer to VM
            vm_installer_path = "C:\\Temp\\installer.exe"
            if not self.copy_file_to_vm(vm_name, installer_path, vm_installer_path):
                return TestResult(
                    vm_name=vm_name,
                    test_name=test_type,
                    success=False,
                    duration_seconds=time.time() - start_time,
                    output="",
                    error="Failed to copy installer to VM"
                )

            # Run installer
            output = self.run_command_in_vm(vm_name, f"{vm_installer_path} /S", timeout=600)

            if output is None:
                return TestResult(
                    vm_name=vm_name,
                    test_name=test_type,
                    success=False,
                    duration_seconds=time.time() - start_time,
                    output="",
                    error="Failed to run installer"
                )

            # Verify installation
            verify_output = self.run_command_in_vm(
                vm_name,
                'dir "C:\\Program Files\\Windows AI"'
            )

            success = verify_output is not None and "Uninstall.exe" in verify_output

            return TestResult(
                vm_name=vm_name,
                test_name=test_type,
                success=success,
                duration_seconds=time.time() - start_time,
                output=output or "",
                error=None if success else "Installation verification failed"
            )

        except Exception as e:
            logger.error(f"Error running installer test: {e}")
            return TestResult(
                vm_name=vm_name,
                test_name=test_type,
                success=False,
                duration_seconds=time.time() - start_time,
                output="",
                error=str(e)
            )

        finally:
            # Stop VM
            self.stop_vm(vm_name)


# Example usage
if __name__ == "__main__":
    # Create VM automation instance
    automation = VMAutomation(provider=VMProvider.HYPERV)

    # Create test VM
    config = VMConfig(
        name="WindowsAI-Test-VM",
        provider=VMProvider.HYPERV,
        os="Windows 10",
        memory_mb=4096,
        cpus=2
    )

    if automation.create_vm(config):
        print("VM created successfully")

        # Run installer test
        installer_path = Path("dist/WindowsAI-Setup-0.5.0.exe")
        if installer_path.exists():
            result = automation.run_installer_test("WindowsAI-Test-VM", installer_path)
            print(f"Test result: {'SUCCESS' if result.success else 'FAILED'}")
            print(f"Duration: {result.duration_seconds:.2f}s")

        # Clean up
        automation.delete_vm("WindowsAI-Test-VM")
