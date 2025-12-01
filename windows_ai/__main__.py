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
==========================================================
                    WINDOWS AI
          AI Integration Platform for Windows
                  Version 2.0.0-alpha
==========================================================
"""
    try:
        print(banner)
    except UnicodeEncodeError:
        # Fallback for terminals that don't support UTF-8
        print("========== WINDOWS AI ==========")
        print("AI Integration Platform for Windows")
        print("Version 2.0.0-alpha")
        print("================================")


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

        registry_path = Path(__file__).parent / "plugins" / "QUALITY_PLUGINS_REGISTRY.json"

        if registry_path.exists():
            with open(registry_path) as f:
                registry = json.load(f)

            print(f"\n[*] Available Plugins: {registry['total_plugins']}\n")

            for category, plugins in sorted(registry['categories'].items()):
                print(f"  {category.upper()}: {len(plugins)} plugins")

            print(f"\nFor detailed plugin information, see: windows_ai/plugins/QUALITY_PLUGINS_REGISTRY.json")
        else:
            print("[!] Plugin registry not found")
            print("Run from repository root or install package properly")

    except Exception as e:
        logger.error(f"Error listing plugins: {e}")


def launch_gui():
    """Launch GUI interface"""
    print("\n[*] Launching GUI...")
    try:
        import subprocess
        gui_path = Path(__file__).parent.parent / "apps" / "gui"

        if not gui_path.exists():
            print("[!] GUI directory not found at:", gui_path)
            print("Make sure you're running from the repository root")
            return

        # Check if node_modules exists
        node_modules = gui_path / "node_modules"
        if not node_modules.exists():
            print("[*] Installing GUI dependencies...")
            subprocess.run(["npm", "install"], cwd=gui_path, check=True)

        # Launch Electron
        print("[*] Starting Electron GUI...")
        subprocess.run(["npm", "start"], cwd=gui_path)

    except FileNotFoundError:
        print("[!] Node.js/npm not found. Please install Node.js to run the GUI")
        print("Download from: https://nodejs.org/")
    except Exception as e:
        logger.error(f"Failed to launch GUI: {e}")
        print("[!] GUI launch failed. You can manually run it with:")
        print(f"    cd apps/gui && npm start")


def launch_tray():
    """Launch system tray"""
    print("\n[*] Launching system tray...")
    try:
        import subprocess
        gui_path = Path(__file__).parent.parent / "apps" / "gui"

        if not gui_path.exists():
            print("[!] GUI directory not found")
            return

        # The Electron app includes tray functionality
        print("[*] Starting GUI with system tray...")
        subprocess.run(["npm", "start"], cwd=gui_path)

    except Exception as e:
        logger.error(f"Failed to launch tray: {e}")
        print("[!] Tray launch failed")


def start_api_server():
    """Start API server"""
    print("\n[*] Starting API server...")
    try:
        import uvicorn
        from windows_ai.api.server import app
        
        print("[+] Windows AI API Server")
        print("    - Listening on: http://127.0.0.1:8010")
        print("    - API Documentation: http://127.0.0.1:8010/docs")
        print("    - Health Check: http://127.0.0.1:8010/health")
        print("\n[*] Server starting...")
        
        uvicorn.run(
            app,
            host="127.0.0.1",
            port=8010,
            log_level="info"
        )
    except ImportError as e:
        logger.error(f"Failed to import required modules: {e}")
        print("[!] Please install required packages:")
        print("    pip install fastapi uvicorn")
    except Exception as e:
        logger.error(f"Failed to start API server: {e}", exc_info=True)
        print("[!] API server failed to start")


def run_plugin(plugin_name):
    """Run a specific plugin"""
    print(f"\n[*] Running plugin: {plugin_name}")
    print("[!] Direct plugin execution in progress")
    print("Use plugin system API for now")


if __name__ == '__main__':
    main()
