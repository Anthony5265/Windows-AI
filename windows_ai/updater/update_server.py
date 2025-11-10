"""
Windows AI Update Server

FastAPI server for serving update manifests and installer downloads.
Can be deployed standalone or integrated with the main Windows AI backend.
"""

import os
import json
import hashlib
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .version_manager import VersionManager


logger = logging.getLogger(__name__)


# =====================================================================
# Pydantic Models
# =====================================================================

class UpdateCheckRequest(BaseModel):
    """Request for checking updates"""
    current_version: str
    channel: str = "stable"
    platform: str = "windows"
    arch: str = "x64"


class UpdateCheckResponse(BaseModel):
    """Response for update check"""
    update_available: bool
    latest_version: Optional[str] = None
    current_version: str
    release: Optional[Dict[str, Any]] = None


class ManifestInfo(BaseModel):
    """Manifest metadata"""
    version: str
    last_updated: str
    total_releases: int
    channels: List[str]


# =====================================================================
# Update Server
# =====================================================================

class UpdateServer:
    """
    Update server for Windows AI
    """

    def __init__(
        self,
        manifest_path: Path,
        downloads_dir: Path,
        base_url: str = "http://localhost:8011"
    ):
        """
        Initialize update server

        Args:
            manifest_path: Path to manifest.json file
            downloads_dir: Directory containing installer files
            base_url: Base URL for this server
        """
        self.manifest_path = manifest_path
        self.downloads_dir = downloads_dir
        self.base_url = base_url.rstrip('/')

        # Load manifest
        self.manifest = self._load_manifest()

        # Statistics
        self.stats = {
            "total_checks": 0,
            "total_downloads": 0,
            "checks_by_version": {},
            "downloads_by_version": {}
        }

        logger.info(f"UpdateServer initialized - manifest={manifest_path}, downloads={downloads_dir}")

    def _load_manifest(self) -> dict:
        """Load manifest from file"""
        try:
            if not self.manifest_path.exists():
                logger.warning(f"Manifest not found at {self.manifest_path}, creating empty manifest")
                return self._create_empty_manifest()

            with open(self.manifest_path, 'r') as f:
                manifest = json.load(f)

            logger.info(f"Loaded manifest with {len(manifest.get('releases', []))} releases")
            return manifest

        except Exception as e:
            logger.error(f"Error loading manifest: {e}")
            return self._create_empty_manifest()

    def _create_empty_manifest(self) -> dict:
        """Create empty manifest structure"""
        return {
            "version": "1.0",
            "lastUpdated": datetime.now().isoformat(),
            "releases": [],
            "channels": {
                "stable": {
                    "name": "Stable",
                    "description": "Production-ready releases",
                    "latestVersion": None,
                    "updateFrequency": "monthly",
                    "autoUpdate": True
                }
            },
            "updateServer": {
                "baseUrl": self.base_url
            }
        }

    def reload_manifest(self):
        """Reload manifest from file"""
        self.manifest = self._load_manifest()
        logger.info("Manifest reloaded")

    def check_for_updates(
        self,
        current_version: str,
        channel: str = "stable"
    ) -> Dict[str, Any]:
        """
        Check if updates are available

        Args:
            current_version: Client's current version
            channel: Release channel

        Returns:
            Update check response
        """
        self.stats["total_checks"] += 1
        self.stats["checks_by_version"][current_version] = \
            self.stats["checks_by_version"].get(current_version, 0) + 1

        try:
            # Find latest release in channel
            latest_release = self._find_latest_release(channel)

            if not latest_release:
                return {
                    "update_available": False,
                    "current_version": current_version,
                    "latest_version": current_version,
                    "release": None
                }

            latest_version = latest_release["version"]

            # Compare versions
            if VersionManager.is_newer(latest_version, current_version):
                # Update available
                return {
                    "update_available": True,
                    "current_version": current_version,
                    "latest_version": latest_version,
                    "release": latest_release
                }
            else:
                # Up to date
                return {
                    "update_available": False,
                    "current_version": current_version,
                    "latest_version": latest_version,
                    "release": None
                }

        except Exception as e:
            logger.error(f"Error checking for updates: {e}")
            raise HTTPException(status_code=500, detail="Error checking for updates")

    def _find_latest_release(self, channel: str) -> Optional[dict]:
        """Find latest release in channel"""
        releases = self.manifest.get("releases", [])

        # Filter by channel
        channel_releases = [
            r for r in releases
            if r.get("channel", "stable") == channel
        ]

        if not channel_releases:
            return None

        # Sort by version
        channel_releases.sort(
            key=lambda r: VersionManager.parse(r["version"]),
            reverse=True
        )

        return channel_releases[0]

    def get_manifest(self) -> dict:
        """Get full manifest"""
        return self.manifest

    def get_manifest_info(self) -> dict:
        """Get manifest metadata"""
        releases = self.manifest.get("releases", [])
        channels = list(self.manifest.get("channels", {}).keys())

        return {
            "version": self.manifest.get("version", "1.0"),
            "last_updated": self.manifest.get("lastUpdated", ""),
            "total_releases": len(releases),
            "channels": channels
        }

    def get_release(self, version: str) -> Optional[dict]:
        """Get specific release by version"""
        releases = self.manifest.get("releases", [])

        for release in releases:
            if release["version"] == version:
                return release

        return None

    def get_download_path(self, version: str) -> Optional[Path]:
        """Get file path for installer download"""
        # Find release
        release = self.get_release(version)
        if not release:
            return None

        # Get installer info
        installer_info = release.get("files", {}).get("installer", {})
        if not installer_info:
            return None

        # Get URL and convert to file path
        url = installer_info.get("url", "")
        if url.startswith('/'):
            url = url[1:]

        # Try to find file
        file_path = self.downloads_dir / f"WindowsAI-Setup-{version}.exe"

        if file_path.exists():
            return file_path

        # Try alternative path from URL
        alt_path = self.downloads_dir / url
        if alt_path.exists():
            return alt_path

        return None

    def record_download(self, version: str):
        """Record download statistics"""
        self.stats["total_downloads"] += 1
        self.stats["downloads_by_version"][version] = \
            self.stats["downloads_by_version"].get(version, 0) + 1

    def get_statistics(self) -> dict:
        """Get server statistics"""
        return {
            "total_checks": self.stats["total_checks"],
            "total_downloads": self.stats["total_downloads"],
            "checks_by_version": self.stats["checks_by_version"],
            "downloads_by_version": self.stats["downloads_by_version"],
            "manifest_info": self.get_manifest_info()
        }


# =====================================================================
# FastAPI Application
# =====================================================================

def create_update_server_app(
    manifest_path: Path,
    downloads_dir: Path,
    base_url: str = "http://localhost:8011"
) -> FastAPI:
    """
    Create FastAPI application for update server

    Args:
        manifest_path: Path to manifest.json
        downloads_dir: Directory containing installers
        base_url: Base URL for this server

    Returns:
        FastAPI application
    """
    app = FastAPI(
        title="Windows AI Update Server",
        description="Serves update manifests and installer downloads for Windows AI",
        version="1.0.0"
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Create server instance
    server = UpdateServer(manifest_path, downloads_dir, base_url)

    # =====================================================================
    # Routes
    # =====================================================================

    @app.get("/")
    async def root():
        """Root endpoint"""
        return {
            "service": "Windows AI Update Server",
            "version": "1.0.0",
            "status": "running"
        }

    @app.get("/health")
    async def health():
        """Health check endpoint"""
        return {
            "status": "healthy",
            "manifest_loaded": bool(server.manifest.get("releases")),
            "total_releases": len(server.manifest.get("releases", []))
        }

    @app.get("/manifest.json")
    async def get_manifest():
        """Get full update manifest"""
        return server.get_manifest()

    @app.get("/manifest/info")
    async def get_manifest_info():
        """Get manifest metadata"""
        return server.get_manifest_info()

    @app.post("/manifest/reload")
    async def reload_manifest():
        """Reload manifest from file (admin endpoint)"""
        server.reload_manifest()
        return {"status": "reloaded", "releases": len(server.manifest.get("releases", []))}

    @app.get("/updates/check")
    async def check_updates(
        current_version: str = Query(..., description="Current version"),
        channel: str = Query("stable", description="Release channel")
    ):
        """
        Check for available updates

        Args:
            current_version: Client's current version
            channel: Release channel (stable, beta, alpha)

        Returns:
            Update availability and release information
        """
        return server.check_for_updates(current_version, channel)

    @app.get("/updates/latest")
    async def get_latest_version(
        channel: str = Query("stable", description="Release channel")
    ):
        """Get latest version in channel"""
        latest_release = server._find_latest_release(channel)

        if not latest_release:
            raise HTTPException(status_code=404, detail=f"No releases found in {channel} channel")

        return {
            "channel": channel,
            "latest_version": latest_release["version"],
            "release_date": latest_release.get("releaseDate"),
            "release": latest_release
        }

    @app.get("/releases/{version}")
    async def get_release(version: str):
        """Get specific release information"""
        release = server.get_release(version)

        if not release:
            raise HTTPException(status_code=404, detail=f"Release {version} not found")

        return release

    @app.get("/releases/{version}/download")
    async def download_release(version: str):
        """
        Download installer for specific version

        Args:
            version: Version to download

        Returns:
            Installer file
        """
        # Get file path
        file_path = server.get_download_path(version)

        if not file_path:
            raise HTTPException(
                status_code=404,
                detail=f"Installer for version {version} not found"
            )

        # Record download
        server.record_download(version)

        # Return file
        return FileResponse(
            path=file_path,
            filename=file_path.name,
            media_type="application/octet-stream"
        )

    @app.get("/releases/{version}/checksum")
    async def get_checksum(version: str):
        """Get checksum for release"""
        release = server.get_release(version)

        if not release:
            raise HTTPException(status_code=404, detail=f"Release {version} not found")

        installer_info = release.get("files", {}).get("installer", {})

        return {
            "version": version,
            "sha256": installer_info.get("sha256"),
            "md5": installer_info.get("md5"),
            "size": installer_info.get("size")
        }

    @app.get("/statistics")
    async def get_statistics():
        """Get server statistics"""
        return server.get_statistics()

    @app.get("/channels")
    async def get_channels():
        """Get available release channels"""
        channels = server.manifest.get("channels", {})
        return {
            "channels": channels
        }

    return app


# =====================================================================
# Standalone Server
# =====================================================================

if __name__ == "__main__":
    import uvicorn
    import argparse

    parser = argparse.ArgumentParser(description="Windows AI Update Server")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("manifest.json"),
        help="Path to manifest.json"
    )
    parser.add_argument(
        "--downloads",
        type=Path,
        default=Path("downloads"),
        help="Directory containing installer files"
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind to"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8011,
        help="Port to bind to"
    )
    parser.add_argument(
        "--base-url",
        default="http://localhost:8011",
        help="Base URL for this server"
    )

    args = parser.parse_args()

    # Create app
    app = create_update_server_app(
        manifest_path=args.manifest,
        downloads_dir=args.downloads,
        base_url=args.base_url
    )

    # Run server
    print(f"Starting Windows AI Update Server...")
    print(f"  Manifest: {args.manifest}")
    print(f"  Downloads: {args.downloads}")
    print(f"  Base URL: {args.base_url}")
    print(f"  Listening on: http://{args.host}:{args.port}")

    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        log_level="info"
    )
