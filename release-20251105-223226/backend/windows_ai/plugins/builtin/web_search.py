"""
Web Search Plugin

Allows the AI to search the web for current information.
"""

from typing import Dict, Any, Optional
import httpx
import logging

from windows_ai.plugins.base import ToolPlugin, PluginMetadata, PluginType

logger = logging.getLogger(__name__)


class WebSearchPlugin(ToolPlugin):
    """
    Web search tool plugin using DuckDuckGo.
    Allows the AI to search the web for current information.
    """

    @staticmethod
    def get_metadata() -> PluginMetadata:
        return PluginMetadata(
            id="web_search",
            name="Web Search",
            description="Search the web for current information using DuckDuckGo",
            version="1.0.0",
            author="Windows AI",
            plugin_type=PluginType.TOOL,
            icon="🔍",
            tags=["search", "web", "information"]
        )

    async def initialize(self) -> bool:
        """Initialize the web search plugin"""
        self._initialized = True
        logger.info("Web Search plugin initialized")
        return True

    async def execute(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute a web search.

        Args:
            query: Search query
            parameters: Optional parameters (max_results, etc.)

        Returns:
            Search results
        """
        if not parameters:
            parameters = {}

        max_results = parameters.get("max_results", 5)

        try:
            # Use DuckDuckGo Instant Answer API
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.duckduckgo.com/",
                    params={
                        "q": query,
                        "format": "json",
                        "no_html": 1,
                        "skip_disambig": 1
                    },
                    timeout=10.0
                )

                if response.status_code == 200:
                    data = response.json()

                    # Extract relevant information
                    results = {
                        "query": query,
                        "abstract": data.get("Abstract", ""),
                        "abstract_text": data.get("AbstractText", ""),
                        "abstract_source": data.get("AbstractSource", ""),
                        "abstract_url": data.get("AbstractURL", ""),
                        "answer": data.get("Answer", ""),
                        "related_topics": []
                    }

                    # Extract related topics
                    for topic in data.get("RelatedTopics", [])[:max_results]:
                        if isinstance(topic, dict) and "Text" in topic:
                            results["related_topics"].append({
                                "text": topic.get("Text", ""),
                                "url": topic.get("FirstURL", "")
                            })

                    return {
                        "success": True,
                        "result": results,
                        "message": f"Found information about: {query}"
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Search failed with status {response.status_code}",
                        "message": "Web search failed"
                    }

        except Exception as e:
            logger.error(f"Web search error: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Error performing web search"
            }

    def get_schema(self) -> Dict[str, Any]:
        """Return parameter schema for web search"""
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results to return",
                    "default": 5,
                    "minimum": 1,
                    "maximum": 10
                }
            },
            "required": ["query"]
        }

    def get_function_definition(self) -> Dict[str, Any]:
        """Return OpenAI function definition"""
        return {
            "name": "web_search",
            "description": "Search the web for current information. Use this when you need up-to-date information or facts about current events, news, or topics that may have changed since your training data.",
            "parameters": self.get_schema()
        }
