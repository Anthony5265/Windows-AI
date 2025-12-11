#!/usr/bin/env python3
"""
Windows AI MCP Server
Exposes Windows AI functionality through the Model Context Protocol
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add the Windows-AI root directory to the path for windows_ai imports
ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))
# Add entry scripts directory for windows_ai_simple
sys.path.insert(0, str(Path(__file__).parent))

from windows_ai_simple import SimpleWindowsAI

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
except ImportError:
    print("Error: mcp package not installed. Install with: pip install mcp", file=sys.stderr)
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('windows_ai_mcp.log')
    ]
)
logger = logging.getLogger(__name__)

# Global Windows AI instance
windows_ai: SimpleWindowsAI = None


async def initialize_windows_ai():
    """Initialize Windows AI instance"""
    global windows_ai
    if windows_ai is None:
        logger.info("Initializing Windows AI...")
        windows_ai = SimpleWindowsAI()
        await windows_ai.initialize()
        logger.info("Windows AI initialized successfully")
    return windows_ai


async def main():
    """Run the MCP server"""
    logger.info("Starting Windows AI MCP Server...")
    
    # Create MCP server
    server = Server("windows-ai")
    
    @server.list_tools()
    async def list_tools() -> list[Tool]:
        """List available tools"""
        return [
            Tool(
                name="chat",
                description="Chat with Windows AI using various AI providers (OpenAI, Anthropic, Google, etc.)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "message": {
                            "type": "string",
                            "description": "The message to send to the AI"
                        },
                        "provider": {
                            "type": "string",
                            "description": "AI provider to use (default: openai)",
                            "enum": ["openai"],
                            "default": "openai"
                        }
                    },
                    "required": ["message"]
                }
            ),
            Tool(
                name="list_models",
                description="List all available AI models from loaded plugins",
                inputSchema={
                    "type": "object",
                    "properties": {}
                }
            ),
            Tool(
                name="get_status",
                description="Get the current status of Windows AI (loaded plugins, API keys, etc.)",
                inputSchema={
                    "type": "object",
                    "properties": {}
                }
            )
        ]
    
    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        """Handle tool calls"""
        try:
            # Initialize Windows AI if needed
            ai = await initialize_windows_ai()
            
            if name == "chat":
                message = arguments.get("message", "")
                provider = arguments.get("provider", "openai")
                
                if not message:
                    return [TextContent(
                        type="text",
                        text="Error: message parameter is required"
                    )]
                
                logger.info(f"Processing chat request: {message[:50]}...")
                response = await ai.chat(message, provider)
                
                return [TextContent(
                    type="text",
                    text=response
                )]
            
            elif name == "list_models":
                logger.info("Listing available models...")
                models = ai.list_models()
                
                if not models:
                    return [TextContent(
                        type="text",
                        text="No models available. Make sure plugins are loaded."
                    )]
                
                models_text = "Available AI Models:\n\n"
                for model in models:
                    models_text += f"- **{model['name']}** ({model['provider']})\n"
                    models_text += f"  {model.get('description', 'No description')}\n\n"
                
                return [TextContent(
                    type="text",
                    text=models_text
                )]
            
            elif name == "get_status":
                logger.info("Getting Windows AI status...")
                status = ai.get_status()
                
                status_text = "Windows AI Status:\n\n"
                status_text += f"- Initialized: {status['initialized']}\n"
                status_text += f"- API Keys Loaded: {status['api_keys_loaded']}\n"
                status_text += f"- Available Keys: {', '.join(status['available_keys'])}\n"
                status_text += f"- Plugins Loaded: {status['plugins_loaded']}\n"
                status_text += f"- Models Available: {status['models_available']}\n"
                
                return [TextContent(
                    type="text",
                    text=status_text
                )]
            
            else:
                return [TextContent(
                    type="text",
                    text=f"Error: Unknown tool '{name}'"
                )]
        
        except Exception as e:
            logger.error(f"Error calling tool '{name}': {e}", exc_info=True)
            return [TextContent(
                type="text",
                text=f"Error: {str(e)}"
            )]
    
    # Run the server
    async with stdio_server() as (read_stream, write_stream):
        logger.info("MCP Server running on stdio...")
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
