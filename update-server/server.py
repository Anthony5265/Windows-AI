"""
Windows AI Update Server - Standalone Deployment

Production-ready update server for serving Windows AI updates.
Can be deployed to various platforms (cloud, on-premises, etc.)
"""

import sys
from pathlib import Path

# Add parent directory to path to import windows_ai modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from windows_ai.updater.update_server import create_update_server_app
import uvicorn


def main():
    """Main entry point for update server"""
    import argparse

    parser = argparse.ArgumentParser(description="Windows AI Update Server")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path(__file__).parent / "manifest.json",
        help="Path to manifest.json"
    )
    parser.add_argument(
        "--downloads",
        type=Path,
        default=Path(__file__).parent / "downloads",
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
        default=None,
        help="Base URL for this server (auto-detected if not specified)"
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload (development only)"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Number of worker processes"
    )

    args = parser.parse_args()

    # Auto-detect base URL if not specified
    if args.base_url is None:
        args.base_url = f"http://{args.host}:{args.port}"

    # Create downloads directory if it doesn't exist
    args.downloads.mkdir(parents=True, exist_ok=True)

    # Create app
    app = create_update_server_app(
        manifest_path=args.manifest,
        downloads_dir=args.downloads,
        base_url=args.base_url
    )

    # Print startup info
    print("=" * 60)
    print("Windows AI Update Server")
    print("=" * 60)
    print(f"Manifest: {args.manifest}")
    print(f"Downloads: {args.downloads}")
    print(f"Base URL: {args.base_url}")
    print(f"Listening on: http://{args.host}:{args.port}")
    print("=" * 60)
    print()

    # Run server
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        log_level="info",
        reload=args.reload,
        workers=args.workers if not args.reload else 1
    )


if __name__ == "__main__":
    main()
