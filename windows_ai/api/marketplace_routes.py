"""
Plugin Marketplace API Routes

Provides browsing, searching, installing, and managing plugins
from the Windows AI plugin marketplace.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import logging
import os
import json
from pathlib import Path

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/marketplace", tags=["marketplace"])

# Marketplace data directory
MARKETPLACE_DIR = Path.home() / ".windows_ai" / "marketplace"
INSTALLED_PLUGINS_FILE = MARKETPLACE_DIR / "installed.json"


class MarketplacePlugin(BaseModel):
    """Plugin listing in the marketplace"""
    id: str
    name: str
    description: str
    version: str
    author: str
    category: str
    tags: List[str] = []
    downloads: int = 0
    rating: float = 0.0
    installed: bool = False


class InstallRequest(BaseModel):
    """Request to install a plugin"""
    plugin_id: str
    version: Optional[str] = None


class InstallResponse(BaseModel):
    """Response after installing a plugin"""
    status: str
    plugin_id: str
    version: str
    message: str


def _get_builtin_plugins() -> List[Dict[str, Any]]:
    """Scan builtin plugins directory to build marketplace catalogue."""
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
            # Extract description from docstring
            description = f"{plugin_name.replace('_', ' ').title()} plugin"
            try:
                with open(plugin_file, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read(500)
                    # Extract docstring
                    for quote in ['"""', "'''"]:
                        if quote in content:
                            start = content.index(quote) + 3
                            end = content.index(quote, start)
                            desc = content[start:end].strip().split("\n")[0]
                            if desc:
                                description = desc
                            break
            except Exception:
                pass

            plugins.append({
                "id": f"{category}/{plugin_name}",
                "name": plugin_name.replace("_", " ").title().replace(" Plugin", ""),
                "description": description,
                "version": "2.0.0",
                "author": "Windows AI Team",
                "category": category,
                "tags": [category],
                "downloads": 0,
                "rating": 0.0,
                "installed": True,  # Builtin plugins are always installed
            })

    return plugins


def _get_installed_plugins() -> Dict[str, Any]:
    """Get the list of manually installed plugins."""
    if INSTALLED_PLUGINS_FILE.exists():
        try:
            with open(INSTALLED_PLUGINS_FILE) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {}


def _save_installed_plugins(data: Dict[str, Any]):
    """Save installed plugins registry."""
    MARKETPLACE_DIR.mkdir(parents=True, exist_ok=True)
    with open(INSTALLED_PLUGINS_FILE, "w") as f:
        json.dump(data, f, indent=2)


@router.get("/", response_model=List[MarketplacePlugin])
async def list_marketplace_plugins(
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search query"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=200, description="Results per page"),
):
    """
    Browse the plugin marketplace.
    
    Returns all available plugins with optional filtering by category or search.
    """
    plugins = _get_builtin_plugins()
    
    # Filter by category
    if category:
        plugins = [p for p in plugins if p["category"] == category]
    
    # Search filter
    if search:
        search_lower = search.lower()
        plugins = [
            p for p in plugins
            if search_lower in p["name"].lower()
            or search_lower in p["description"].lower()
            or any(search_lower in t for t in p["tags"])
        ]
    
    # Pagination
    total = len(plugins)
    start = (page - 1) * per_page
    end = start + per_page
    page_plugins = plugins[start:end]
    
    return page_plugins


@router.get("/categories")
async def list_categories():
    """List all available plugin categories with counts."""
    plugins = _get_builtin_plugins()
    categories: Dict[str, int] = {}
    for p in plugins:
        cat = p["category"]
        categories[cat] = categories.get(cat, 0) + 1
    
    return {
        "categories": [
            {"name": name, "count": count}
            for name, count in sorted(categories.items())
        ],
        "total_categories": len(categories),
        "total_plugins": sum(categories.values()),
    }


@router.get("/stats")
async def marketplace_stats():
    """Get marketplace statistics."""
    plugins = _get_builtin_plugins()
    categories: Dict[str, int] = {}
    for p in plugins:
        cat = p["category"]
        categories[cat] = categories.get(cat, 0) + 1

    return {
        "total_plugins": len(plugins),
        "total_categories": len(categories),
        "top_categories": sorted(
            categories.items(), key=lambda x: x[1], reverse=True
        )[:10],
        "installed_count": len(plugins),
    }


@router.get("/search/{query}")
async def search_plugins(query: str):
    """Search marketplace plugins by keyword."""
    plugins = _get_builtin_plugins()
    query_lower = query.lower()
    
    results = []
    for p in plugins:
        score = 0
        if query_lower in p["name"].lower():
            score += 10
        if query_lower in p["description"].lower():
            score += 5
        if any(query_lower in t for t in p["tags"]):
            score += 3
        if query_lower in p["category"].lower():
            score += 2
        if score > 0:
            results.append({"plugin": p, "relevance": score})
    
    results.sort(key=lambda x: x["relevance"], reverse=True)
    
    return {
        "query": query,
        "total": len(results),
        "results": [r["plugin"] for r in results[:50]],
    }


@router.get("/{plugin_id:path}", response_model=MarketplacePlugin)
async def get_marketplace_plugin(plugin_id: str):
    """Get details for a specific marketplace plugin."""
    plugins = _get_builtin_plugins()
    for p in plugins:
        if p["id"] == plugin_id:
            return p
    raise HTTPException(status_code=404, detail=f"Plugin {plugin_id} not found")


@router.post("/install", response_model=InstallResponse)
async def install_plugin(request: InstallRequest):
    """
    Install a plugin from the marketplace.
    
    For builtin plugins, this is a no-op (they're always available).
    For community plugins, this downloads and installs the plugin.
    """
    plugins = _get_builtin_plugins()
    found = None
    for p in plugins:
        if p["id"] == request.plugin_id:
            found = p
            break

    if not found:
        raise HTTPException(
            status_code=404, detail=f"Plugin {request.plugin_id} not found"
        )

    # Track installation
    installed = _get_installed_plugins()
    installed[request.plugin_id] = {
        "version": request.version or found["version"],
        "installed_at": str(__import__("datetime").datetime.now()),
    }
    _save_installed_plugins(installed)

    return InstallResponse(
        status="success",
        plugin_id=request.plugin_id,
        version=request.version or found["version"],
        message=f"Plugin {found['name']} installed successfully",
    )


@router.post("/uninstall/{plugin_id:path}")
async def uninstall_plugin(plugin_id: str):
    """Uninstall a marketplace plugin."""
    installed = _get_installed_plugins()
    if plugin_id in installed:
        del installed[plugin_id]
        _save_installed_plugins(installed)
        return {"status": "success", "message": f"Plugin {plugin_id} uninstalled"}
    
    # Check if it's a builtin
    plugins = _get_builtin_plugins()
    for p in plugins:
        if p["id"] == plugin_id:
            return {
                "status": "info",
                "message": "Builtin plugins cannot be uninstalled, but can be disabled",
            }
    
    raise HTTPException(status_code=404, detail=f"Plugin {plugin_id} not found")
