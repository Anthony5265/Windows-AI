"""Simple FastAPI service exposing the plugin marketplace.

The service reads from the ``plugins/catalog.json`` file and allows
listing or publishing new plugins. Publishing appends entries to the
catalog for demonstration purposes only and performs no authentication.
"""

from __future__ import annotations

from pathlib import Path
import json
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

CATALOG_PATH = Path(__file__).resolve().parent.parent / "plugins" / "catalog.json"

app = FastAPI()


def _load_catalog() -> Dict[str, Any]:
    try:
        return json.loads(CATALOG_PATH.read_text())
    except Exception as exc:  # pragma: no cover - I/O errors
        raise HTTPException(status_code=500, detail=str(exc)) from exc


def _save_catalog(data: Dict[str, Any]) -> None:
    CATALOG_PATH.write_text(json.dumps(data, indent=2))


class Plugin(BaseModel):
    """Metadata describing a plugin entry."""

    name: str
    description: str
    command: str
    paid: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)
    rating: Optional[float] = None
    dependencies: List[str] = Field(default_factory=list)
    signature: Optional[str] = None


@app.get("/plugins")
def list_plugins() -> Dict[str, Any]:
    """Return the full plugin catalog."""

    return _load_catalog()


@app.post("/plugins")
def publish_plugin(plugin: Plugin) -> Dict[str, bool]:
    """Publish a plugin by appending it to the catalog."""

    data = _load_catalog()
    data.setdefault("plugins", []).append(plugin.model_dump())
    _save_catalog(data)
    return {"ok": True}
