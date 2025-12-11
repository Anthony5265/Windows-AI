"""
Windows Containers/Docker Integration - PRODUCTION

Provides comprehensive container management capabilities including:
- Container lifecycle management (create, start, stop, remove)
- Image management (pull, build, list, remove)
- Volume and network management
- Docker Compose operations
- Container inspection and logging
"""
import asyncio
import json
from typing import Dict, Any, List, Optional
from windows_ai.plugins.base import IntegrationPlugin, PluginMetadata, PluginType
import logging

logger = logging.getLogger(__name__)


class WindowsContainersPlugin(IntegrationPlugin):
    """Windows Containers/Docker integration plugin with comprehensive management."""
    
    def __init__(self):
        metadata = PluginMetadata(
            id="windows_containers",
            name="Windows Containers",
            description="Docker/container management - images, containers, volumes, networks, compose",
            version="2.0.0",
            author="Windows AI Team",
            plugin_type=PluginType.INTEGRATION,
            tags=["windows", "docker", "containers", "virtualization"]
        )
        super().__init__(metadata)
        self.connected = False
        self._docker_available = False
        self._docker_version = None

    async def initialize(self) -> bool:
        """Initialize the Docker plugin and check availability."""
        result = await self._run_command(["docker", "--version"])
        self._docker_available = result["success"]
        if self._docker_available:
            self._docker_version = result.get("output", "unknown")
            logger.info(f"Docker version: {self._docker_version}")
        else:
            logger.warning("Docker not available on this system")
        self._initialized = True
        return True

    async def connect(self, credentials: Dict[str, str]) -> bool:
        """Connect (local access, no credentials needed for local Docker)."""
        self.connected = True
        return True

    async def disconnect(self) -> bool:
        """Disconnect."""
        self.connected = False
        return True

    async def _run_command(self, cmd: List[str], timeout: int = 120) -> Dict[str, Any]:
        """Execute a Docker command and return results."""
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
            return {
                "success": process.returncode == 0,
                "output": stdout.decode('utf-8', errors='replace').strip(),
                "error": stderr.decode('utf-8', errors='replace').strip() if stderr else None,
                "return_code": process.returncode
            }
        except asyncio.TimeoutError:
            return {"success": False, "error": "Command timed out"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def execute(self, action: str, parameters: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Execute a Docker operation."""
        if not self.connected:
            return {"success": False, "error": "Not connected"}
        
        if not self._docker_available and action != "status":
            return {"success": False, "error": "Docker not available on this system"}

        actions = {
            # Container operations
            "list_containers": self._list_containers,
            "create_container": self._create_container,
            "start_container": self._start_container,
            "stop_container": self._stop_container,
            "restart_container": self._restart_container,
            "remove_container": self._remove_container,
            "container_logs": self._get_container_logs,
            "container_inspect": self._inspect_container,
            "exec_container": self._exec_in_container,
            # Image operations
            "list_images": self._list_images,
            "pull_image": self._pull_image,
            "build_image": self._build_image,
            "remove_image": self._remove_image,
            "image_inspect": self._inspect_image,
            # Volume operations
            "list_volumes": self._list_volumes,
            "create_volume": self._create_volume,
            "remove_volume": self._remove_volume,
            # Network operations
            "list_networks": self._list_networks,
            "create_network": self._create_network,
            "remove_network": self._remove_network,
            # Compose operations
            "compose_up": self._compose_up,
            "compose_down": self._compose_down,
            "compose_ps": self._compose_ps,
            # System operations
            "status": self._get_status,
            "system_info": self._get_system_info,
            "system_prune": self._system_prune,
        }

        if action not in actions:
            return {"success": False, "error": f"Unknown action: {action}. Available: {list(actions.keys())}"}

        try:
            return await actions[action](parameters)
        except Exception as e:
            logger.error(f"Docker operation failed: {e}")
            return {"success": False, "error": str(e)}

    # Container operations
    async def _list_containers(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List containers."""
        all_containers = params.get("all", False)
        cmd = ["docker", "ps", "--format", "{{json .}}"]
        if all_containers:
            cmd.insert(2, "-a")
        
        result = await self._run_command(cmd)
        if result["success"]:
            containers = []
            for line in result["output"].split('\n'):
                if line.strip():
                    try:
                        containers.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
            return {"success": True, "containers": containers, "count": len(containers)}
        return result

    async def _create_container(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new container."""
        image = params.get("image")
        if not image:
            return {"success": False, "error": "Image parameter required"}
        
        name = params.get("name")
        ports = params.get("ports", [])
        volumes = params.get("volumes", [])
        env_vars = params.get("env", [])
        detach = params.get("detach", True)
        command = params.get("command", "")
        
        cmd = ["docker", "create"]
        if name:
            cmd.extend(["--name", name])
        for port in ports:
            cmd.extend(["-p", port])
        for vol in volumes:
            cmd.extend(["-v", vol])
        for env in env_vars:
            cmd.extend(["-e", env])
        cmd.append(image)
        if command:
            cmd.extend(command.split())
        
        return await self._run_command(cmd)

    async def _start_container(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Start a container."""
        container = params.get("container") or params.get("id") or params.get("name")
        if not container:
            return {"success": False, "error": "Container ID or name required"}
        return await self._run_command(["docker", "start", container])

    async def _stop_container(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Stop a container."""
        container = params.get("container") or params.get("id") or params.get("name")
        if not container:
            return {"success": False, "error": "Container ID or name required"}
        timeout = params.get("timeout", 10)
        return await self._run_command(["docker", "stop", "-t", str(timeout), container])

    async def _restart_container(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Restart a container."""
        container = params.get("container") or params.get("id") or params.get("name")
        if not container:
            return {"success": False, "error": "Container ID or name required"}
        return await self._run_command(["docker", "restart", container])

    async def _remove_container(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Remove a container."""
        container = params.get("container") or params.get("id") or params.get("name")
        if not container:
            return {"success": False, "error": "Container ID or name required"}
        cmd = ["docker", "rm"]
        if params.get("force", False):
            cmd.append("-f")
        if params.get("volumes", False):
            cmd.append("-v")
        cmd.append(container)
        return await self._run_command(cmd)

    async def _get_container_logs(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get container logs."""
        container = params.get("container") or params.get("id") or params.get("name")
        if not container:
            return {"success": False, "error": "Container ID or name required"}
        
        cmd = ["docker", "logs"]
        if params.get("tail"):
            cmd.extend(["--tail", str(params["tail"])])
        if params.get("since"):
            cmd.extend(["--since", params["since"]])
        cmd.append(container)
        
        return await self._run_command(cmd)

    async def _inspect_container(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Inspect a container."""
        container = params.get("container") or params.get("id") or params.get("name")
        if not container:
            return {"success": False, "error": "Container ID or name required"}
        
        result = await self._run_command(["docker", "inspect", container])
        if result["success"]:
            try:
                info = json.loads(result["output"])
                return {"success": True, "info": info}
            except json.JSONDecodeError:
                return result
        return result

    async def _exec_in_container(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a command in a running container."""
        container = params.get("container") or params.get("id") or params.get("name")
        command = params.get("command")
        if not container or not command:
            return {"success": False, "error": "Container and command parameters required"}
        
        cmd = ["docker", "exec", container]
        cmd.extend(command.split())
        
        return await self._run_command(cmd, timeout=params.get("timeout", 60))

    # Image operations
    async def _list_images(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List images."""
        result = await self._run_command(["docker", "images", "--format", "{{json .}}"])
        if result["success"]:
            images = []
            for line in result["output"].split('\n'):
                if line.strip():
                    try:
                        images.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
            return {"success": True, "images": images, "count": len(images)}
        return result

    async def _pull_image(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Pull an image."""
        image = params.get("image")
        if not image:
            return {"success": False, "error": "Image parameter required"}
        return await self._run_command(["docker", "pull", image], timeout=600)

    async def _build_image(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Build an image from a Dockerfile."""
        context = params.get("context", ".")
        tag = params.get("tag")
        dockerfile = params.get("dockerfile")
        
        cmd = ["docker", "build"]
        if tag:
            cmd.extend(["-t", tag])
        if dockerfile:
            cmd.extend(["-f", dockerfile])
        cmd.append(context)
        
        return await self._run_command(cmd, timeout=1800)

    async def _remove_image(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Remove an image."""
        image = params.get("image")
        if not image:
            return {"success": False, "error": "Image parameter required"}
        cmd = ["docker", "rmi"]
        if params.get("force", False):
            cmd.append("-f")
        cmd.append(image)
        return await self._run_command(cmd)

    async def _inspect_image(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Inspect an image."""
        image = params.get("image")
        if not image:
            return {"success": False, "error": "Image parameter required"}
        
        result = await self._run_command(["docker", "image", "inspect", image])
        if result["success"]:
            try:
                info = json.loads(result["output"])
                return {"success": True, "info": info}
            except json.JSONDecodeError:
                return result
        return result

    # Volume operations
    async def _list_volumes(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List volumes."""
        result = await self._run_command(["docker", "volume", "ls", "--format", "{{json .}}"])
        if result["success"]:
            volumes = []
            for line in result["output"].split('\n'):
                if line.strip():
                    try:
                        volumes.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
            return {"success": True, "volumes": volumes, "count": len(volumes)}
        return result

    async def _create_volume(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a volume."""
        name = params.get("name")
        if not name:
            return {"success": False, "error": "Name parameter required"}
        return await self._run_command(["docker", "volume", "create", name])

    async def _remove_volume(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Remove a volume."""
        name = params.get("name")
        if not name:
            return {"success": False, "error": "Name parameter required"}
        cmd = ["docker", "volume", "rm"]
        if params.get("force", False):
            cmd.append("-f")
        cmd.append(name)
        return await self._run_command(cmd)

    # Network operations
    async def _list_networks(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List networks."""
        result = await self._run_command(["docker", "network", "ls", "--format", "{{json .}}"])
        if result["success"]:
            networks = []
            for line in result["output"].split('\n'):
                if line.strip():
                    try:
                        networks.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
            return {"success": True, "networks": networks, "count": len(networks)}
        return result

    async def _create_network(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a network."""
        name = params.get("name")
        if not name:
            return {"success": False, "error": "Name parameter required"}
        
        cmd = ["docker", "network", "create"]
        if params.get("driver"):
            cmd.extend(["--driver", params["driver"]])
        cmd.append(name)
        
        return await self._run_command(cmd)

    async def _remove_network(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Remove a network."""
        name = params.get("name")
        if not name:
            return {"success": False, "error": "Name parameter required"}
        return await self._run_command(["docker", "network", "rm", name])

    # Compose operations
    async def _compose_up(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Start Docker Compose services."""
        compose_file = params.get("file", "docker-compose.yml")
        project = params.get("project")
        
        cmd = ["docker", "compose"]
        if compose_file:
            cmd.extend(["-f", compose_file])
        if project:
            cmd.extend(["-p", project])
        cmd.extend(["up", "-d"])
        
        if params.get("build", False):
            cmd.append("--build")
        
        return await self._run_command(cmd, timeout=600)

    async def _compose_down(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Stop Docker Compose services."""
        compose_file = params.get("file", "docker-compose.yml")
        project = params.get("project")
        
        cmd = ["docker", "compose"]
        if compose_file:
            cmd.extend(["-f", compose_file])
        if project:
            cmd.extend(["-p", project])
        cmd.append("down")
        
        if params.get("volumes", False):
            cmd.append("-v")
        
        return await self._run_command(cmd, timeout=300)

    async def _compose_ps(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List Docker Compose services."""
        compose_file = params.get("file", "docker-compose.yml")
        
        cmd = ["docker", "compose", "-f", compose_file, "ps", "--format", "json"]
        return await self._run_command(cmd)

    # System operations
    async def _get_status(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get Docker status."""
        return {
            "success": True,
            "docker_available": self._docker_available,
            "docker_version": self._docker_version
        }

    async def _get_system_info(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get Docker system info."""
        result = await self._run_command(["docker", "system", "info", "--format", "json"])
        if result["success"]:
            try:
                info = json.loads(result["output"])
                return {"success": True, "info": info}
            except json.JSONDecodeError:
                return result
        return result

    async def _system_prune(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Remove unused Docker resources."""
        cmd = ["docker", "system", "prune", "-f"]
        if params.get("all", False):
            cmd.append("-a")
        if params.get("volumes", False):
            cmd.append("--volumes")
        return await self._run_command(cmd, timeout=300)

    async def shutdown(self):
        """Shutdown the plugin."""
        self._initialized = False

    def get_schema(self) -> Dict[str, Any]:
        """Get the plugin schema."""
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["list_containers", "create_container", "start_container",
                            "stop_container", "restart_container", "remove_container",
                            "container_logs", "container_inspect", "exec_container",
                            "list_images", "pull_image", "build_image", "remove_image",
                            "image_inspect", "list_volumes", "create_volume", "remove_volume",
                            "list_networks", "create_network", "remove_network",
                            "compose_up", "compose_down", "compose_ps",
                            "status", "system_info", "system_prune"]
                },
                "parameters": {
                    "type": "object",
                    "properties": {
                        "container": {"type": "string"},
                        "image": {"type": "string"},
                        "name": {"type": "string"},
                        "command": {"type": "string"},
                        "ports": {"type": "array"},
                        "volumes": {"type": "array"}
                    }
                }
            }
        }


plugin = WindowsContainersPlugin()
