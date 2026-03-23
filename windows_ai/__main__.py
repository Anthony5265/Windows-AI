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
        '--setup',
        action='store_true',
        help='Run first-time setup wizard'
    )

    parser.add_argument(
        '--skip-setup',
        action='store_true',
        help='Skip automatic setup check'
    )

    parser.add_argument(
        'command',
        nargs='?',
        choices=['interactive', 'chat', 'status', 'capabilities'],
        help='Subcommand to run'
    )

    parser.add_argument(
        'message',
        nargs='?',
        default=None,
        help='Message for chat command'
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
        # Dispatch commands that should NOT be blocked by first-run setup
        if args.api:
            start_api_server()
            return
        if args.setup:
            run_setup()
            return
        if args.list_plugins:
            list_plugins()
            return
        if args.plugin:
            run_plugin(args.plugin)
            return
        if args.gui:
            launch_gui()
            return
        if args.tray:
            launch_tray()
            return

        # Handle subcommands
        if args.command == 'interactive':
            run_interactive_cli()
            return
        if args.command == 'chat':
            if args.message:
                run_chat(args.message)
            else:
                print("Usage: windows-ai chat \"your message\"")
            return
        if args.command == 'status':
            show_status()
            return
        if args.command == 'capabilities':
            show_capabilities()
            return

        # Default behavior: check first-run, then interactive mode
        if not args.skip_setup:
            try:
                from windows_ai.core.auto_setup import AutoSetup
                setup = AutoSetup()
                if setup.is_first_run():
                    logger.info("[*] First run detected - running setup...")
                    print("\n" + "="*60)
                    print("WELCOME TO WINDOWS AI!")
                    print("="*60)
                    print("\nFirst-time setup is needed.")
                    print("Run: windows-ai --setup")
                    print("\nOr skip setup and start the API server:")
                    print("  windows-ai --api")
                    print("  windows-ai --skip-setup interactive")
                    print("="*60 + "\n")
                    return
            except Exception as e:
                logger.debug(f"Auto-setup check skipped: {e}")

        # Default: interactive mode
        run_interactive_cli()

    except KeyboardInterrupt:
        logger.info("\nShutdown requested by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=args.verbose)
        sys.exit(1)


def run_setup():
    """Run the interactive setup wizard"""
    from windows_ai.core.auto_setup import AutoSetup

    print("\n" + "="*60)
    print("WINDOWS AI SETUP WIZARD")
    print("="*60)
    print("\nRunning first-time setup...")

    setup = AutoSetup()
    result = asyncio.run(setup.run_first_time_setup())

    if result.get("directories_created"):
        print("\n" + "="*60)
        print("SETUP COMPLETE!")
        print("="*60)
        print("\nWindows AI is now ready to use.")
        print("\nYou can now:")
        print("  windows-ai --api          Start the API server")
        print("  windows-ai interactive    Start interactive CLI")
        print("  windows-ai --gui          Launch GUI (if Electron is installed)")
        print("="*60 + "\n")
    else:
        logger.error("Setup failed. Please check logs for details.")
        sys.exit(1)


def list_plugins():
    """List all available plugins"""
    try:
        import json

        registry_path = Path(__file__).parent / "plugins" / "QUALITY_PLUGINS_REGISTRY.json"

        if registry_path.exists():
            with open(registry_path) as f:
                registry = json.load(f)

            print(f"\n[*] Available Plugins: {registry.get('total_plugins', 'unknown')}\n")

            for category, plugins in sorted(registry.get('categories', {}).items()):
                print(f"  {category.upper()}: {len(plugins)} plugins")

            print(f"\nFor detailed plugin information, see: windows_ai/plugins/QUALITY_PLUGINS_REGISTRY.json")
        else:
            # Fallback: count plugin directories
            plugins_dir = Path(__file__).parent / "plugins" / "builtin"
            if plugins_dir.exists():
                categories = [d for d in plugins_dir.iterdir() if d.is_dir() and not d.name.startswith('_')]
                total = sum(
                    len([f for f in cat.glob("*.py") if f.name != "__init__.py"])
                    for cat in categories
                )
                print(f"\n[*] Plugin Categories: {len(categories)}")
                print(f"[*] Total Plugins: {total}")
                for cat in sorted(categories, key=lambda c: c.name):
                    count = len([f for f in cat.glob("*.py") if f.name != "__init__.py"])
                    if count:
                        print(f"  {cat.name}: {count} plugins")
            else:
                print("[!] Plugin directory not found")

    except Exception as e:
        logger.error(f"Error listing plugins: {e}")


def launch_gui():
    """Launch GUI interface"""
    print("\n[*] Launching GUI...")
    import subprocess

    # Try Electron GUI first
    gui_path = Path(__file__).parent.parent / "apps" / "gui"
    if gui_path.exists() and (gui_path / "package.json").exists():
        try:
            print("[*] Starting Electron GUI...")
            subprocess.run(["npm", "start"], cwd=gui_path, check=True)
            return
        except FileNotFoundError:
            logger.warning("npm not found. Install Node.js to use the GUI.")
        except subprocess.CalledProcessError as e:
            logger.warning(f"Electron GUI failed to start: {e}")
        except Exception as e:
            logger.warning(f"Could not start Electron GUI: {e}")

    # Fallback to interactive CLI
    print("[!] GUI not available. Starting interactive CLI mode...")
    run_interactive_cli()


def run_interactive_cli():
    """Run an interactive CLI session"""
    print("\n" + "="*60)
    print("WINDOWS AI - Interactive Mode")
    print("="*60)
    print("\nType 'help' for commands, 'quit' to exit.\n")

    while True:
        try:
            user_input = input("Windows AI> ").strip()

            if not user_input:
                continue
            elif user_input.lower() in ('quit', 'exit', 'q'):
                print("\nGoodbye!")
                break
            elif user_input.lower() == 'help':
                print("\nAvailable commands:")
                print("  help         - Show this help")
                print("  status       - Show system status")
                print("  plugins      - List available plugins")
                print("  setup        - Run setup wizard")
                print("  capabilities - Show AI capabilities")
                print("  quit         - Exit Windows AI")
            elif user_input.lower() == 'status':
                show_status()
            elif user_input.lower() == 'plugins':
                list_plugins()
            elif user_input.lower() == 'setup':
                run_setup()
            elif user_input.lower() == 'capabilities':
                show_capabilities()
            else:
                # Try to handle as a chat message
                run_chat(user_input)
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except EOFError:
            print("\nGoodbye!")
            break


def run_chat(message: str):
    """Run a single chat message through the AI"""
    try:
        from windows_ai.core.orchestrator import WindowsAI

        async def _chat():
            ai = WindowsAI()
            await ai.initialize()
            response = await ai.chat(message)
            print(f"\n{response}\n")

        asyncio.run(_chat())
    except Exception as e:
        logger.error(f"Chat failed: {e}")
        print(f"[!] Chat unavailable: {e}")
        print("Tip: Set OPENAI_API_KEY or configure an AI provider first.")


def show_capabilities():
    """Show available AI capabilities"""
    print("\n--- Windows AI Capabilities ---")
    print("  Chat & Text Generation")
    print("  Image Generation & Analysis")
    print("  Audio Transcription & TTS")
    print("  Code Generation & Review")
    print("  Document Processing & OCR")
    print("  Windows Automation")
    print("  IoT Device Management")
    print("  Multi-Agent Coordination")
    print("  RAG (Retrieval-Augmented Generation)")
    print("  Plugin Ecosystem (2000+ plugins)")
    print("-------------------------------\n")


def show_status():
    """Show Windows AI status"""
    import json

    config_dir = Path.home() / ".windows_ai"
    config_file = config_dir / "config.json"

    print("\n--- Windows AI Status ---")
    print(f"Config directory: {config_dir}")
    print(f"Config exists: {config_file.exists()}")

    if config_file.exists():
        try:
            with open(config_file) as f:
                config = json.load(f)
            print(f"Setup complete: {config.get('setup_complete', False)}")
            print(f"Setup date: {config.get('setup_date', 'Unknown')}")
        except Exception as e:
            print(f"Error reading config: {e}")

    # Check API server
    try:
        import httpx
        response = httpx.get("http://127.0.0.1:8010/health", timeout=2.0)
        if response.status_code == 200:
            print("API Server: Running on port 8010")
        else:
            print("API Server: Not running")
    except Exception:
        print("API Server: Not running")

    print("------------------------\n")


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

    # Ensure setup directories exist (non-blocking)
    try:
        config_dir = Path.home() / ".windows_ai"
        config_dir.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass

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
        print("    pip install windows-ai")
        print("    # or: pip install -r requirements.txt")
    except Exception as e:
        logger.error(f"Failed to start API server: {e}", exc_info=True)
        print("[!] API server failed to start")


def run_plugin(plugin_name):
    """Run a specific plugin"""
    print(f"\n[*] Running plugin: {plugin_name}")
    try:
        from windows_ai.core.plugin_manager import PluginManager

        async def _run():
            pm = PluginManager()
            await pm.initialize()
            result = await pm.execute_plugin(plugin_name)
            print(f"Result: {result}")

        asyncio.run(_run())
    except Exception as e:
        logger.error(f"Plugin execution failed: {e}")
        print(f"[!] Failed to run plugin '{plugin_name}': {e}")


if __name__ == '__main__':
    main()
