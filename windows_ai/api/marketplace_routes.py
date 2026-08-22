"""Plugin marketplace API routes."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/marketplace", tags=["marketplace"])
MARKETPLACE_DIR = Path.home() / ".windows_ai" / "marketplace"
INSTALLED_PLUGINS_FILE = MARKETPLACE_DIR / "installed.json"


class MarketplacePlugin(BaseModel):
    id: str
    name: str
    description: str
    version: str
    author: str
    category: str
    tags: List[str] = Field(default_factory=list)
    downloads: int = Field(default=0, ge=0)
    rating: float = Field(default=0.0, ge=0.0, le=5.0)
    installed: bool = False


class InstallRequest(BaseModel):
    plugin_id: str = Field(..., min_length=1, max_length=200)
    version: Optional[str] = Field(default=None, min_length=1, max_length=50)


class InstallResponse(BaseModel):
    status: str
    plugin_id: str
    version: str
    message: str


def _get_builtin_plugins() -> List[Dict[str, Any]]:
    plugins = []
    builtin_dir = Path(__file__).parent.parent / "plugins" / "builtin"
    if not builtin_dir.exists():
        return plugins
    for category_dir in sorted(builtin_dir.iterdir()):
        if not category_dir.is_dir() or category_dir.name.startswith("_"):
            continue
        category = category_dir.name
        for plugin_file in sorted(category_dir.glob("*.py")):
            if plugin_file.name.startswith("_"):
                continue
            plugin_name = plugin_file.stem
            description = f"{plugin_name.replace('_', ' ').title()} plugin"
            try:
                content = plugin_file.read_text(encoding="utf-8", errors="ignore")[:500]
                for quote in ('"""', "'''"):
                    if quote in content:
                        start = content.index(quote) + 3
                        end = content.index(quote, start)
                        desc = content[start:end].strip().splitlines()[0] if content[start:end].strip() else ""
                        if desc:
                            description = desc
                        break
            except (OSError, UnicodeError, ValueError):
                logger.debug("Unable to read plugin metadata: %s", plugin_file, exc_info=True)
            plugins.append({"id": f"{category}/{plugin_name}", "name": plugin_name.replace("_", " ").title().replace(" Plugin", ""), "description": description, "version": "2.0.0", "author": "Windows AI Team", "category": category, "tags": [category], "downloads": 0, "rating": 0.0, "installed": True})
    return plugins


def _get_installed_plugins() -> Dict[str, Any]:
    if not INSTALLED_PLUGINS_FILE.exists():
        return {}
    try:
        data = json.loads(INSTALLED_PLUGINS_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError):
        logger.warning("Ignoring invalid marketplace registry: %s", INSTALLED_PLUGINS_FILE)
        return {}


def _save_installed_plugins(data: Dict[str, Any]):
    MARKETPLACE_DIR.mkdir(parents=True, exist_ok=True)
    temp = INSTALLED_PLUGINS_FILE.with_suffix(".tmp")
    temp.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
    temp.replace(INSTALLED_PLUGINS_FILE)


@router.get("/", response_model=List[MarketplacePlugin])
async def list_marketplace_plugins(category: Optional[str] = Query(None), search: Optional[str] = Query(None), page: int = Query(1, ge=1), per_page: int = Query(50, ge=1, le=200)):
    plugins = _get_builtin_plugins()
    if category:
        plugins = [p for p in plugins if p["category"] == category]
    if search:
        search_lower = search.casefold()
        plugins = [p for p in plugins if search_lower in p["name"].casefold() or search_lower in p["description"].casefold() or any(search_lower in t.casefold() for t in p["tags"])]
    start = (page - 1) * per_page
    return plugins[start:start + per_page]


@router.get("/categories")
async def list_categories():
    plugins = _get_builtin_plugins()
    categories: Dict[str, int] = {}
    for plugin in plugins:
        categories[plugin["category"]] = categories.get(plugin["category"], 0) + 1
    return {"categories": [{"name": name, "count": count} for name, count in sorted(categories.items())], "total_categories": len(categories), "total_plugins": len(plugins)}


@router.get("/stats")
async def marketplace_stats():
    plugins = _get_builtin_plugins()
    categories: Dict[str, int] = {}
    for plugin in plugins:
        categories[plugin["category"]] = categories.get(plugin["category"], 0) + 1
    return {"total_plugins": len(plugins), "total_categories": len(categories), "top_categories": sorted(categories.items(), key=lambda x: x[1], reverse=True)[:10], "installed_count": len(plugins)}


@router.get("/search/{query}")
async def search_plugins(query: str):
    query_lower = query.casefold()
    results = []
    for plugin in _get_builtin_plugins():
        score = (10 if query_lower in plugin["name"].casefold() else 0) + (5 if query_lower in plugin["description"].casefold() else 0) + (3 if any(query_lower in tag.casefold() for tag in plugin["tags"]) else 0) + (2 if query_lower in plugin["category"].casefold() else 0)
        if score:
            results.append({"plugin": plugin, "relevance": score})
    results.sort(key=lambda item: (-item["relevance"], item["plugin"]["id"]))
    return {"query": query, "total": len(results), "results": [item["plugin"] for item in results[:50]]}


@router.get("/{plugin_id:path}", response_model=MarketplacePlugin)
async def get_marketplace_plugin(plugin_id: str):
    for plugin in _get_builtin_plugins():
        if plugin["id"] == plugin_id:
            return plugin
    raise HTTPException(status_code=404, detail=f"Plugin {plugin_id} not found")


@router.post("/install", response_model=InstallResponse)
async def install_plugin(request: InstallRequest):
    found = next((plugin for plugin in _get_builtin_plugins() if plugin["id"] == request.plugin_id), None)
    if not found:
        raise HTTPException(status_code=404, detail=f"Plugin {request.plugin_id} not found")
    installed = _get_installed_plugins()
    version = request.version or found["version"]
    installed[request.plugin_id] = {"version": version, "installed_at": datetime.now(timezone.utc).isoformat()}
    _save_installed_plugins(installed)
    return InstallResponse(status="installed", plugin_id=request.plugin_id, version=version, message=f"Plugin {request.plugin_id} is available")
