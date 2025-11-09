"""
Docker DevOps Plugin
Plugin for managing Docker containers, images, and volumes
"""

from typing import Dict, Any, Optional, List
import os
import subprocess
import logging
import json


class DockerPlugin:
    """Plugin for Docker container management"""

    name = "docker"
    version = "1.0.0"
    description = "Plugin for managing Docker containers, images, and volumes"
    author = "Windows AI Team"

    def __init__(self):
        self.docker_available = False
        self._initialized = False
        self.logger = logging.getLogger(__name__)

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Docker plugin"""
        try:
            # Check if Docker is installed and available
            result = subprocess.run(
                ["docker", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                self.docker_available = True
                self._initialized = True
                self.logger.info("Docker plugin initialized successfully")
                return True
            else:
                self.logger.error("Docker is not installed or not accessible")
                return False

        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            self.logger.error(f"Error initializing Docker plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Docker action"""
        if not self._initialized:
            return {"error": "Plugin not initialized. Docker may not be installed."}

        try:
            if action == "build":
                return self._build_image(params)
            elif action == "run":
                return self._run_container(params)
            elif action == "ps":
                return self._list_containers(params)
            elif action == "images":
                return self._list_images(params)
            elif action == "stop":
                return self._stop_container(params)
            elif action == "rm":
                return self._remove_container(params)
            elif action == "rmi":
                return self._remove_image(params)
            elif action == "logs":
                return self._get_logs(params)
            else:
                return {"error": f"Unknown action: {action}"}

        except Exception as e:
            self.logger.error(f"Error executing action {action}: {e}")
            return {"error": str(e)}

    def _run_docker_command(self, command: List[str], cwd: Optional[str] = None) -> Dict[str, Any]:
        """Run a Docker command and return the result"""
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                cwd=cwd,
                timeout=300  # 5 minutes timeout
            )

            if result.returncode == 0:
                return {
                    "success": True,
                    "output": result.stdout.strip(),
                    "error": result.stderr.strip()
                }
            else:
                return {
                    "success": False,
                    "error": result.stderr.strip() or result.stdout.strip(),
                    "returncode": result.returncode
                }

        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Command timed out"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _build_image(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Build a Docker image"""
        dockerfile = params.get("dockerfile", "Dockerfile")
        tag = params.get("tag", "latest")
        context = params.get("context", ".")

        command = ["docker", "build", "-f", dockerfile, "-t", tag, context]
        return self._run_docker_command(command, cwd=context)

    def _run_container(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Run a Docker container"""
        image = params.get("image", "")
        if not image:
            return {"error": "Image name is required"}

        command = ["docker", "run"]

        # Add options
        if params.get("detached", False):
            command.append("-d")
        if params.get("rm", False):
            command.append("--rm")

        # Add port mappings
        ports = params.get("ports", [])
        for port in ports:
            command.extend(["-p", port])

        # Add environment variables
        env = params.get("env", [])
        for e in env:
            command.extend(["-e", e])

        # Add volumes
        volumes = params.get("volumes", [])
        for vol in volumes:
            command.extend(["-v", vol])

        # Add container name
        name = params.get("name")
        if name:
            command.extend(["--name", name])

        command.append(image)

        # Add command arguments
        cmd_args = params.get("command", [])
        command.extend(cmd_args)

        return self._run_docker_command(command)

    def _list_containers(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List Docker containers"""
        command = ["docker", "ps"]
        if params.get("all", False):
            command.append("-a")

        result = self._run_docker_command(command)
        if result["success"]:
            # Parse the output into a list of containers
            lines = result["output"].split('\n')
            if len(lines) > 1:  # Skip header
                containers = []
                for line in lines[1:]:
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 7:
                            containers.append({
                                "container_id": parts[0],
                                "image": parts[1],
                                "command": ' '.join(parts[2:-4]),
                                "created": ' '.join(parts[-4:-2]),
                                "status": parts[-2],
                                "ports": parts[-1],
                                "names": parts[-3] if len(parts) > 7 else ""
                            })
                result["containers"] = containers

        return result

    def _list_images(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List Docker images"""
        command = ["docker", "images"]
        result = self._run_docker_command(command)
        if result["success"]:
            # Parse the output
            lines = result["output"].split('\n')
            if len(lines) > 1:
                images = []
                for line in lines[1:]:
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 5:
                            images.append({
                                "repository": parts[0],
                                "tag": parts[1],
                                "image_id": parts[2],
                                "created": ' '.join(parts[3:-1]),
                                "size": parts[-1]
                            })
                result["images"] = images

        return result

    def _stop_container(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Stop a Docker container"""
        container = params.get("container", "")
        if not container:
            return {"error": "Container name or ID is required"}

        command = ["docker", "stop", container]
        return self._run_docker_command(command)

    def _remove_container(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Remove a Docker container"""
        container = params.get("container", "")
        if not container:
            return {"error": "Container name or ID is required"}

        command = ["docker", "rm"]
        if params.get("force", False):
            command.append("-f")
        command.append(container)

        return self._run_docker_command(command)

    def _remove_image(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Remove a Docker image"""
        image = params.get("image", "")
        if not image:
            return {"error": "Image name or ID is required"}

        command = ["docker", "rmi"]
        if params.get("force", False):
            command.append("-f")
        command.append(image)

        return self._run_docker_command(command)

    def _get_logs(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get logs from a Docker container"""
        container = params.get("container", "")
        if not container:
            return {"error": "Container name or ID is required"}

        command = ["docker", "logs"]
        if params.get("follow", False):
            command.append("-f")
        if params.get("tail"):
            command.extend(["--tail", str(params["tail"])])
        command.append(container)

        return self._run_docker_command(command)

    def cleanup(self):
        """Cleanup resources"""
        self.docker_available = False
        self._initialized = False


# Plugin metadata
PLUGIN_CLASS = DockerPlugin
PLUGIN_NAME = "docker"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Plugin for managing Docker containers, images, and volumes"
PLUGIN_ACTIONS = ["build", "run", "ps", "images", "stop", "rm", "rmi", "logs"]