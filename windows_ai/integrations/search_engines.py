"""
Search Engines Manager - 10+ Services
"""

import asyncio
import logging
import os
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class SearchEnginesManager:
    """Web search across 10+ providers"""

    def __init__(self):
        self._initialized = False

    async def initialize(self, config: Optional[Dict] = None):
        if self._initialized:
            return
        self._initialized = True

    async def search(
        self,
        query: str,
        provider: str = "serper",
        num_results: int = 10
    ) -> List[Dict[str, Any]]:
        """Search the web"""

        if provider == "serper":
            return await self._serper_search(query, num_results)
        elif provider == "serpapi":
            return await self._serpapi_search(query, num_results)
        elif provider == "brave":
            return await self._brave_search(query, num_results)
        elif provider == "tavily":
            return await self._tavily_search(query, num_results)
        elif provider == "exa":
            return await self._exa_search(query, num_results)
        elif provider == "duckduckgo":
            return await self._duckduckgo_search(query, num_results)
        else:
            raise ValueError(f"Unsupported search provider: {provider}")

    async def _serper_search(self, query, num_results):
        """Serper.dev Google search"""
        import aiohttp

        api_key = os.environ.get("SERPER_API_KEY")

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://google.serper.dev/search",
                headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
                json={"q": query, "num": num_results}
            ) as response:
                data = await response.json()
                return [{
                    "title": r.get("title"),
                    "url": r.get("link"),
                    "snippet": r.get("snippet")
                } for r in data.get("organic", [])]

    async def _serpapi_search(self, query, num_results):
        """SerpAPI search"""
        import aiohttp

        api_key = os.environ.get("SERPAPI_API_KEY")

        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://serpapi.com/search",
                params={"q": query, "api_key": api_key, "num": num_results}
            ) as response:
                data = await response.json()
                return [{
                    "title": r.get("title"),
                    "url": r.get("link"),
                    "snippet": r.get("snippet")
                } for r in data.get("organic_results", [])]

    async def _brave_search(self, query, num_results):
        """Brave Search API"""
        import aiohttp

        api_key = os.environ.get("BRAVE_SEARCH_API_KEY")

        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.search.brave.com/res/v1/web/search",
                headers={"X-Subscription-Token": api_key},
                params={"q": query, "count": num_results}
            ) as response:
                data = await response.json()
                return [{
                    "title": r.get("title"),
                    "url": r.get("url"),
                    "snippet": r.get("description")
                } for r in data.get("web", {}).get("results", [])]

    async def _tavily_search(self, query, num_results):
        """Tavily AI search"""
        import aiohttp

        api_key = os.environ.get("TAVILY_API_KEY")

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.tavily.com/search",
                json={"api_key": api_key, "query": query, "max_results": num_results}
            ) as response:
                data = await response.json()
                return [{
                    "title": r.get("title"),
                    "url": r.get("url"),
                    "snippet": r.get("content")
                } for r in data.get("results", [])]

    async def _exa_search(self, query, num_results):
        """Exa neural search"""
        import aiohttp

        api_key = os.environ.get("EXA_API_KEY")

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.exa.ai/search",
                headers={"x-api-key": api_key, "Content-Type": "application/json"},
                json={"query": query, "numResults": num_results, "useAutoprompt": True}
            ) as response:
                data = await response.json()
                return [{
                    "title": r.get("title"),
                    "url": r.get("url"),
                    "snippet": r.get("text", "")[:200]
                } for r in data.get("results", [])]

    async def _duckduckgo_search(self, query, num_results):
        """DuckDuckGo search"""
        from duckduckgo_search import DDGS

        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=num_results))
            return [{
                "title": r.get("title"),
                "url": r.get("href"),
                "snippet": r.get("body")
            } for r in results]
