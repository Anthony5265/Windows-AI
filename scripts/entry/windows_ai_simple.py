#!/usr/bin/env python3
"""
Windows AI - Simplified Working Version
A minimal, functional AI integration platform that actually works
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional

from windows_ai.core.plugin_manager import PluginManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('windows_ai.log')
    ]
)
logger = logging.getLogger(__name__)


class SimpleWindowsAI:
    """Simplified Windows AI that actually works"""
    
    def __init__(self):
        self.initialized = False
        self.config = {}
        self.api_keys = {}
        self.plugin_manager: Optional[PluginManager] = None
        
    async def initialize(self):
        """Initialize with error handling"""
        logger.info("=" * 60)
        logger.info("Windows AI - Starting...")
        logger.info("=" * 60)
        
        try:
            # Load API keys from environment
            self._load_api_keys()
            logger.info(f"Loaded {len(self.api_keys)} API keys")
            
            # Test basic imports
            self._test_imports()
            
            # Initialize Plugin Manager
            logger.info("Initializing Plugin Manager...")
            self.plugin_manager = PluginManager()
            await self.plugin_manager.initialize()
            
            # Log discovered models
            models = self.plugin_manager.get_all_supported_models()
            logger.info(f"Discovered {len(models)} AI models from plugins")
            for model in models:
                logger.info(f"  - {model['name']} ({model['provider']})")
            
            self.initialized = True
            logger.info("=" * 60)
            logger.info("Windows AI initialized successfully!")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"✗ Initialization failed: {e}", exc_info=True)
            raise
    
    def _load_api_keys(self):
        """Load API keys from environment"""
        import os
        
        key_names = [
            "OPENAI_API_KEY",
            "ANTHROPIC_API_KEY", 
            "GOOGLE_API_KEY",
            "GROQ_API_KEY",
            "MISTRAL_API_KEY",
            "COHERE_API_KEY",
        ]
        
        for key_name in key_names:
            value = os.getenv(key_name)
            if value:
                self.api_keys[key_name] = value
                logger.info(f"  Found: {key_name}")
    
    def _test_imports(self):
        """Test that core dependencies are available"""
        try:
            import fastapi
            logger.info(f"FastAPI {fastapi.__version__}")
        except ImportError:
            logger.warning("✗ FastAPI not available")
            
        try:
            import uvicorn
            logger.info(f"Uvicorn available")
        except ImportError:
            logger.warning("✗ Uvicorn not available")
            
        try:
            import openai
            logger.info(f"OpenAI SDK {openai.__version__}")
        except ImportError:
            logger.warning("✗ OpenAI SDK not available")
    
    async def chat(self, message: str, provider: str = "openai") -> str:
        """Simple chat interface"""
        if not self.initialized:
            await self.initialize()
        
        if provider == "openai":
            return await self._chat_openai(message)
        else:
            return f"Provider '{provider}' not yet implemented"
    
    async def _chat_openai(self, message: str) -> str:
        """Chat with OpenAI"""
        try:
            import openai
            
            api_key = self.api_keys.get("OPENAI_API_KEY")
            if not api_key:
                return "Error: OPENAI_API_KEY not set"
            
            client = openai.AsyncOpenAI(api_key=api_key)
            
            response = await client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": message}]
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"OpenAI chat error: {e}")
            return f"Error: {e}"
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status"""
        return {
            "initialized": self.initialized,
            "api_keys_loaded": len(self.api_keys),
            "available_keys": list(self.api_keys.keys()),
            "plugins_loaded": len(self.plugin_manager.plugins) if self.plugin_manager else 0,
            "models_available": len(self.plugin_manager.get_all_supported_models()) if self.plugin_manager else 0
        }

    def list_models(self) -> list:
        """List all available models from plugins"""
        if self.plugin_manager:
            return self.plugin_manager.get_all_supported_models()
        return []

    async def shutdown(self):
        """Shutdown and cleanup resources"""
        if self.plugin_manager:
            await self.plugin_manager.shutdown()
        self.initialized = False
        logger.info("Windows AI shutdown complete")


async def run_api_server(host: str = "127.0.0.1", port: int = 8765):
    """Run FastAPI server"""
    try:
        from fastapi import FastAPI, HTTPException
        from fastapi.responses import JSONResponse
        from pydantic import BaseModel
        import uvicorn
        
        app = FastAPI(title="Windows AI", version="2.0.0")
        ai = SimpleWindowsAI()
        await ai.initialize()
        
        class ChatRequest(BaseModel):
            message: str
            provider: str = "openai"
        
        @app.get("/")
        async def root():
            return {"status": "running", "version": "2.0.0"}
        
        @app.get("/status")
        async def status():
            return ai.get_status()

        @app.get("/models")
        async def list_models():
            return {"models": ai.list_models()}
        
        @app.post("/chat")
        async def chat(request: ChatRequest):
            try:
                response = await ai.chat(request.message, request.provider)
                return {"response": response}
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.get("/health")
        async def health():
            return {"status": "healthy"}
        
        logger.info(f"Starting API server on http://{host}:{port}")
        logger.info(f"Documentation available at http://{host}:{port}/docs")
        
        config = uvicorn.Config(app, host=host, port=port, log_level="info")
        server = uvicorn.Server(config)
        await server.serve()
        
    except ImportError as e:
        logger.error(f"Missing dependency: {e}")
        logger.error("Install with: pip install fastapi uvicorn[standard]")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        sys.exit(1)


async def run_interactive():
    """Run interactive chat mode"""
    ai = SimpleWindowsAI()
    await ai.initialize()
    
    print("\n" + "=" * 60)
    print("Windows AI - Interactive Mode")
    print("Type 'quit' or 'exit' to quit")
    print("Type '/models' to list available AI models")
    print("=" * 60 + "\n")
    
    while True:
        try:
            user_input = input("\nYou: ").strip()
            
            if user_input.lower() in ['quit', 'exit']:
                print("Goodbye!")
                break
            
            if user_input.lower() == '/models':
                models = ai.list_models()
                print(f"\nAvailable Models ({len(models)}):")
                for model in models:
                    print(f"- {model['name']} ({model['provider']}): {model['description']}")
                continue
            
            if not user_input:
                continue
            
            print("\nAI: ", end="", flush=True)
            response = await ai.chat(user_input)
            print(response)
            
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Windows AI - Simplified Working Version",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument("--api", action="store_true", help="Start API server")
    parser.add_argument("--interactive", action="store_true", help="Interactive chat mode")
    parser.add_argument("--host", default="127.0.0.1", help="API server host")
    parser.add_argument("--port", type=int, default=8765, help="API server port")
    parser.add_argument("--version", action="version", version="Windows AI 2.0.0")
    
    args = parser.parse_args()
    
    try:
        if args.api:
            asyncio.run(run_api_server(args.host, args.port))
        elif args.interactive:
            asyncio.run(run_interactive())
        else:
            print("Windows AI v2.0.0 - Simplified Working Version")
            print("\nUsage:")
            print("  --api          Start API server")
            print("  --interactive  Interactive chat mode")
            print("  --version      Show version")
            print("\nExamples:")
            print("  python windows_ai_simple.py --api")
            print("  python windows_ai_simple.py --interactive")
            
    except KeyboardInterrupt:
        print("\nShutdown requested")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
