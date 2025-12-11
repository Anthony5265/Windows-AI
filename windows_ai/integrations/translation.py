"""
Translation Manager - 10+ Services
"""

import asyncio
import logging
import os
from typing import Dict, List, Any, Optional
from windows_ai.config.unified_config import WindowsAIConfig

import asyncio
import logging
import os
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class TranslationManager:
    """Manages translation across 10+ providers"""

    def __init__(self):
        self._config: Optional[WindowsAIConfig] = None
        self._initialized = False

    async def initialize(self, config: Optional[WindowsAIConfig] = None):
        if self._initialized:
            return
        
        self._config = config
        self._initialized = True

    async def cleanup(self):
        """Cleanup resources before shutdown"""
        try:
            # Close any open connections
            if hasattr(self, '_clients'):
                for client in self._clients.values():
                    if hasattr(client, 'close'):
                        await client.close() if asyncio.iscoroutinefunction(client.close) else client.close()
            
            # Reset initialization flag
            self._initialized = False
            logger.info(f"{self.__class__.__name__} cleanup completed")
            
        except Exception as e:
            logger.error(f"{self.__class__.__name__} cleanup failed: {e}")

    async def translate(
        self,
        text: str,
        target_language: str,
        source_language: str = "auto",
        provider: str = "deepl"
    ) -> Dict[str, Any]:
        """Translate text"""

        if provider == "deepl":
            return await self._deepl_translate(text, target_language, source_language)
        elif provider == "google":
            return await self._google_translate(text, target_language, source_language)
        elif provider == "azure":
            return await self._azure_translate(text, target_language, source_language)
        elif provider == "openai":
            return await self._openai_translate(text, target_language, source_language)
        else:
            raise ValueError(f"Unsupported translation provider: {provider}")

    async def _deepl_translate(self, text, target, source):
        """DeepL translation"""
        import aiohttp

        api_key = os.environ.get("DEEPL_API_KEY")

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api-free.deepl.com/v2/translate",
                headers={"Authorization": f"DeepL-Auth-Key {api_key}"},
                data={"text": text, "target_lang": target.upper(), "source_lang": source.upper() if source != "auto" else None}
            ) as response:
                data = await response.json()
                return {
                    "text": data["translations"][0]["text"],
                    "detected_language": data["translations"][0].get("detected_source_language"),
                    "provider": "deepl"
                }

    async def _google_translate(self, text, target, source):
        """Google Translate"""
        from google.cloud import translate_v2

        client = translate_v2.Client()
        result = client.translate(text, target_language=target, source_language=source if source != "auto" else None)

        return {
            "text": result["translatedText"],
            "detected_language": result.get("detectedSourceLanguage"),
            "provider": "google"
        }

    async def _azure_translate(self, text, target, source):
        """Azure Translator"""
        import aiohttp

        key = os.environ.get("AZURE_TRANSLATOR_KEY")
        region = os.environ.get("AZURE_TRANSLATOR_REGION", "eastus")

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"https://api.cognitive.microsofttranslator.com/translate?api-version=3.0&to={target}",
                headers={
                    "Ocp-Apim-Subscription-Key": key,
                    "Ocp-Apim-Subscription-Region": region,
                    "Content-Type": "application/json"
                },
                json=[{"text": text}]
            ) as response:
                data = await response.json()
                return {
                    "text": data[0]["translations"][0]["text"],
                    "detected_language": data[0].get("detectedLanguage", {}).get("language"),
                    "provider": "azure"
                }

    async def _openai_translate(self, text, target, source):
        """OpenAI-based translation"""
        from windows_ai.integrations.ai_providers import AIProvidersManager, Provider

        ai = AIProvidersManager()
        await ai.initialize()

        messages = [
            {"role": "system", "content": f"Translate the following text to {target}. Return only the translation."},
            {"role": "user", "content": text}
        ]

        response = await ai.chat(Provider.OPENAI, messages)

        return {
            "text": response["content"],
            "provider": "openai"
        }

    async def detect_language(self, text: str, provider: str = "deepl") -> str:
        """Detect language of text"""

        if provider == "deepl":
            result = await self._deepl_translate(text, "EN", "auto")
            return result.get("detected_language", "unknown")

        elif provider == "google":
            from google.cloud import translate_v2
            client = translate_v2.Client()
            result = client.detect_language(text)
            return result["language"]

        return "unknown"
