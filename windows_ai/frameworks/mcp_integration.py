"""
MCP (Model Context Protocol) Integration for Windows AI
Full implementation of Anthropic's Model Context Protocol
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class MCPTool:
    name: str
    description: str
    input_schema: Dict[str, Any]
    handler: Optional[Callable] = None

@dataclass
class MCPResource:
    uri: str
    name: str
    description: str
    mime_type: str = "text/plain"

@dataclass
class MCPServer:
    name: str
    command: str
    args: List[str] = field(default_factory=list)
    env: Dict[str, str] = field(default_factory=dict)

class MCPManager:
    """Manages MCP (Model Context Protocol) integration"""

    def __init__(self):
        self.servers: Dict[str, MCPServer] = {}
        self.tools: Dict[str, MCPTool] = {}
        self.resources: Dict[str, MCPResource] = {}
        self.active_connections: Dict[str, Any] = {}
        self._initialized = False

    async def initialize(self, config: Optional[Dict[str, Any]] = None):
        """Initialize MCP manager"""
        if self._initialized:
            return

        # Register built-in tools
        await self._register_builtin_tools()

        # Register built-in servers
        await self._register_builtin_servers()

        self._initialized = True
        logger.info("MCP integration initialized successfully")

    async def _register_builtin_tools(self):
        """Register built-in MCP tools"""
        # File system tool
        self.register_tool(MCPTool(
            name="read_file",
            description="Read contents of a file",
            input_schema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the file"}
                },
                "required": ["path"]
            },
            handler=self._read_file_handler
        ))

        self.register_tool(MCPTool(
            name="write_file",
            description="Write contents to a file",
            input_schema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the file"},
                    "content": {"type": "string", "description": "Content to write"}
                },
                "required": ["path", "content"]
            },
            handler=self._write_file_handler
        ))

        self.register_tool(MCPTool(
            name="list_directory",
            description="List contents of a directory",
            input_schema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the directory"}
                },
                "required": ["path"]
            },
            handler=self._list_directory_handler
        ))

        self.register_tool(MCPTool(
            name="execute_command",
            description="Execute a shell command",
            input_schema={
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Command to execute"},
                    "cwd": {"type": "string", "description": "Working directory"}
                },
                "required": ["command"]
            },
            handler=self._execute_command_handler
        ))

        self.register_tool(MCPTool(
            name="web_search",
            description="Search the web",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"}
                },
                "required": ["query"]
            },
            handler=self._web_search_handler
        ))

        self.register_tool(MCPTool(
            name="fetch_url",
            description="Fetch content from a URL",
            input_schema={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to fetch"}
                },
                "required": ["url"]
            },
            handler=self._fetch_url_handler
        ))

    async def _register_builtin_servers(self):
        """Register built-in MCP servers"""
        self.servers["filesystem"] = MCPServer(
            name="filesystem",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem", "/"]
        )

        self.servers["github"] = MCPServer(
            name="github",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-github"]
        )

        self.servers["puppeteer"] = MCPServer(
            name="puppeteer",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-puppeteer"]
        )

        self.servers["postgres"] = MCPServer(
            name="postgres",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-postgres"]
        )

        self.servers["sqlite"] = MCPServer(
            name="sqlite",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-sqlite"]
        )

        self.servers["slack"] = MCPServer(
            name="slack",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-slack"]
        )

        self.servers["google-drive"] = MCPServer(
            name="google-drive",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-gdrive"]
        )

        self.servers["brave-search"] = MCPServer(
            name="brave-search",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-brave-search"]
        )

        self.servers["fetch"] = MCPServer(
            name="fetch",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-fetch"]
        )

        self.servers["memory"] = MCPServer(
            name="memory",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-memory"]
        )

    def register_tool(self, tool: MCPTool):
        """Register an MCP tool"""
        self.tools[tool.name] = tool
        logger.debug(f"Registered MCP tool: {tool.name}")

    def register_resource(self, resource: MCPResource):
        """Register an MCP resource"""
        self.resources[resource.uri] = resource
        logger.debug(f"Registered MCP resource: {resource.uri}")

    def register_server(self, server: MCPServer):
        """Register an MCP server"""
        self.servers[server.name] = server
        logger.debug(f"Registered MCP server: {server.name}")

    async def start_server(self, server_name: str) -> bool:
        """Start an MCP server"""
        server = self.servers.get(server_name)
        if not server:
            raise ValueError(f"Server '{server_name}' not found")

        try:
            process = await asyncio.create_subprocess_exec(
                server.command,
                *server.args,
                env={**dict(asyncio.os.environ), **server.env},
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            self.active_connections[server_name] = process
            logger.info(f"Started MCP server: {server_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to start server {server_name}: {e}")
            return False

    async def stop_server(self, server_name: str):
        """Stop an MCP server"""
        process = self.active_connections.get(server_name)
        if process:
            process.terminate()
            await process.wait()
            del self.active_connections[server_name]
            logger.info(f"Stopped MCP server: {server_name}")

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Call an MCP tool"""
        tool = self.tools.get(tool_name)
        if not tool:
            raise ValueError(f"Tool '{tool_name}' not found")

        if tool.handler:
            return await tool.handler(arguments)

        raise ValueError(f"Tool '{tool_name}' has no handler")

    async def get_resource(self, uri: str) -> Any:
        """Get an MCP resource"""
        resource = self.resources.get(uri)
        if not resource:
            raise ValueError(f"Resource '{uri}' not found")

        # Handle different resource types
        if uri.startswith("file://"):
            path = uri[7:]
            return Path(path).read_text()

        return resource

    # Built-in tool handlers
    async def _read_file_handler(self, args: Dict[str, Any]) -> str:
        path = Path(args["path"])
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        return path.read_text()

    async def _write_file_handler(self, args: Dict[str, Any]) -> str:
        path = Path(args["path"])
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(args["content"])
        return f"Written to {path}"

    async def _list_directory_handler(self, args: Dict[str, Any]) -> List[str]:
        path = Path(args["path"])
        if not path.exists():
            raise FileNotFoundError(f"Directory not found: {path}")
        return [str(p) for p in path.iterdir()]

    async def _execute_command_handler(self, args: Dict[str, Any]) -> str:
        import subprocess
        result = subprocess.run(
            args["command"],
            shell=True,
            cwd=args.get("cwd"),
            capture_output=True,
            text=True
        )
        return result.stdout + result.stderr

    async def _web_search_handler(self, args: Dict[str, Any]) -> str:
        # Placeholder - integrate with actual search API
        return f"Search results for: {args['query']}"

    async def _fetch_url_handler(self, args: Dict[str, Any]) -> str:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get(args["url"]) as response:
                return await response.text()

    def list_tools(self) -> List[Dict[str, Any]]:
        """List all registered tools"""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.input_schema
            }
            for tool in self.tools.values()
        ]

    def list_resources(self) -> List[Dict[str, Any]]:
        """List all registered resources"""
        return [
            {
                "uri": res.uri,
                "name": res.name,
                "description": res.description,
                "mime_type": res.mime_type
            }
            for res in self.resources.values()
        ]

    def list_servers(self) -> List[Dict[str, Any]]:
        """List all registered servers"""
        return [
            {
                "name": server.name,
                "command": server.command,
                "args": server.args,
                "active": server.name in self.active_connections
            }
            for server in self.servers.values()
        ]

    def get_mcp_config(self) -> Dict[str, Any]:
        """Generate MCP configuration file format"""
        return {
            "mcpServers": {
                name: {
                    "command": server.command,
                    "args": server.args,
                    "env": server.env
                }
                for name, server in self.servers.items()
            }
        }

    async def shutdown(self):
        """Shutdown all MCP connections"""
        for name in list(self.active_connections.keys()):
            await self.stop_server(name)
        logger.info("MCP manager shutdown complete")
