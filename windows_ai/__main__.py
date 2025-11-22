#!/usr/bin/env python3
"""
Windows AI - Main Entry Point
"""

import sys
import asyncio
import argparse
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def print_banner():
    """Print Windows AI banner"""
    banner = """
╔═══════════════════════════════════════════════════════╗
║                    WINDOWS AI                         ║
║          AI Integration Platform for Windows          ║
║                  Version 2.0.0-alpha                  ║
╚═══════════════════════════════════════════════════════╝
"""
    print(banner)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Windows AI - AI Integration Platform for Windows',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--version',
        action='version',
        version='Windows AI 2.0.0-alpha'
    )

    parser.add_argument(
        '--gui',
        action='store_true',
        help='Launch GUI interface'
    )

    parser.add_argument(
        '--tray',
        action='store_true',
        help='Launch system tray'
    )

    parser.add_argument(
        '--api',
        action='store_true',
        help='Start API server'
    )

    parser.add_argument(
        '--list-plugins',
        action='store_true',
        help='List all available plugins'
    )

    parser.add_argument(
        '--plugin',
        type=str,
        metavar='NAME',
        help='Run specific plugin'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    print_banner()

    try:
        if args.list_plugins:
            list_plugins()
        elif args.gui:
            launch_gui()
        elif args.tray:
            launch_tray()
        elif args.api:
            start_api_server()
        elif args.plugin:
            run_plugin(args.plugin)
        else:
            # Default: show help and status
            parser.print_help()
            print("\nStatus: Alpha Development")
            print("For more information, see: README.md")
            print("\nQuick Start:")
            print("  windows-ai --gui        Launch GUI")
            print("  windows-ai --tray       Launch system tray")
            print("  windows-ai --api        Start API server")
            print("  windows-ai --list-plugins  List available plugins")

    except KeyboardInterrupt:
        logger.info("\nShutdown requested by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=args.verbose)
        sys.exit(1)


def list_plugins():
    """List all available plugins"""
    try:
        import json
        from windows_ai.plugins import QUALITY_PLUGINS_REGISTRY

        registry_path = Path(__file__).parent / "plugins" / "QUALITY_PLUGINS_REGISTRY.json"

        if registry_path.exists():
            with open(registry_path) as f:
                registry = json.load(f)

            print(f"\n📦 Available Plugins: {registry['total_plugins']}\n")

            for category, plugins in sorted(registry['categories'].items()):
                print(f"  {category.upper()}: {len(plugins)} plugins")

            print(f"\nFor detailed plugin information, see: windows_ai/plugins/QUALITY_PLUGINS_REGISTRY.json")
        else:
            print("⚠️  Plugin registry not found")
            print("Run from repository root or install package properly")

    except Exception as e:
        logger.error(f"Error listing plugins: {e}")


def launch_gui():
    """Launch GUI interface"""
    print("\n🚀 Launching GUI...")
    print("⚠️  GUI implementation in progress")
    print("See: apps/gui/ for current development status")


def launch_tray():
    """Launch system tray"""
    print("\n🚀 Launching system tray...")
    print("⚠️  Tray implementation in progress")
    print("See: windows-ai-tray/ for current development status")


def start_api_server():
    """Start API server"""
    print("\n🚀 Starting API server...")
    try:
        from windows_ai.app import WindowsAIApp
        app = WindowsAIApp()
        asyncio.run(app.run())
    except ImportError as e:
        logger.warning(f"Full app not available: {e}")
        try:
            from windows_ai.api.server import run_server
            asyncio.run(run_server())
        except ImportError:
            print("⚠️  API module not found")
            print("See: windows_ai/api/ for current development status")


def run_plugin(plugin_name):
    """Run a specific plugin"""
    print(f"\n🔌 Running plugin: {plugin_name}")
    print("⚠️  Direct plugin execution in progress")
    print("Use plugin system API for now")


if __name__ == '__main__':
    main()
