"""
LocalAI Plugin
OpenAI-compatible local AI server
"""

from typing import Dict, Any, Optional, List
import os


class LocalAIPlugin:
    """Plugin for LocalAI server"""

    name = "localai"
    version = "1.0.0"
    description = "Integration with LocalAI for OpenAI-compatible local models"
    author = "Windows AI Team"

    def __init__(self):
        self.base_url: str = "http://localhost:8080"
        self.client = None
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the LocalAI plugin"""
        try:
            import requests

            self.base_url = (
                config.get("base_url") if config
                else os.getenv("LOCALAI_HOST", "http://localhost:8080")
            )

            self.client = requests
            self._initialized = True
            return True

        except ImportError:
            print("requests package not installed. Install with: pip install requests")
            return False
        except Exception as e:
            print(f"Error initializing LocalAI plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a LocalAI action"""
        if not self._initialized:
            return {"success": False, "error": "Plugin not initialized"}

        try:
            if action == "chat":
                return self._chat(params)
            elif action == "completion":
                return self._completion(params)
            elif action == "image":
                return self._generate_image(params)
            elif action == "audio":
                return self._transcribe_audio(params)
            elif action == "embeddings":
                return self._get_embeddings(params)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _chat(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate chat completion"""
        messages = params.get("messages", [])
        model = params.get("model", "gpt-3.5-turbo")

        response = self.client.post(
            f"{self.base_url}/v1/chat/completions",
            json={
                "model": model,
                "messages": messages
            }
        )

        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "response": data.get("choices", [{}])[0].get("message", {}).get("content", "")
            }
        return {"success": False, "error": response.text}

    def _completion(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate text completion"""
        prompt = params.get("prompt", "")
        model = params.get("model", "gpt-3.5-turbo")

        response = self.client.post(
            f"{self.base_url}/v1/completions",
            json={
                "model": model,
                "prompt": prompt
            }
        )

        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "response": data.get("choices", [{}])[0].get("text", "")
            }
        return {"success": False, "error": response.text}

    def _generate_image(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate image"""
        prompt = params.get("prompt", "")
        model = params.get("model", "stablediffusion")

        response = self.client.post(
            f"{self.base_url}/v1/images/generations",
            json={
                "prompt": prompt,
                "model": model
            }
        )

        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "images": data.get("data", [])
            }
        return {"success": False, "error": response.text}

    def _transcribe_audio(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Transcribe audio"""
        file_path = params.get("file_path", "")

        with open(file_path, "rb") as audio_file:
            response = self.client.post(
                f"{self.base_url}/v1/audio/transcriptions",
                files={"file": audio_file}
            )

        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "text": data.get("text", "")
            }
        return {"success": False, "error": response.text}

    def _get_embeddings(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get text embeddings"""
        text = params.get("text", "")
        model = params.get("model", "text-embedding-ada-002")

        response = self.client.post(
            f"{self.base_url}/v1/embeddings",
            json={
                "model": model,
                "input": text
            }
        )

        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "embedding": data.get("data", [{}])[0].get("embedding", [])
            }
        return {"success": False, "error": response.text}

    def shutdown(self) -> bool:
        """Cleanup plugin resources"""
        self._initialized = False
        self.client = None
        return True
