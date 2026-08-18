#!/usr/bin/env python3
"""Windows AI command-line entry point."""
from __future__ import annotations

import argparse
import asyncio
import logging
import subprocess
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def print_banner() -> None:
    """Print the Windows AI banner."""
    print("\n" + "=" * 58)
    print("                         WINDOWS AI")
    print("              AI Integration Platform for Windows")
    print("                         Version 2.0.0-alpha")
    print("=" * 58)


def main() -> None:
    """Run the Windows AI command-line interface."""
    parser = argparse.ArgumentParser(
        description="Windows AI - AI Integration Platform for Windows",
    )
    parser.add_argument("--version", action="version", version="Windows AI 2.0.0-alpha")
    parser.add_argument("--gui", action="store_true", help="Launch GUI interface")
    parser.add_argument("--tray", action="store_true", help="Launch system tray")
    parser.add_argument("--api", action="store_true", help="Start API server")
    parser.add_argument("--setup", action="store_true", help="Run first-time setup wizard")
    parser.add_argument("--skip-setup", action="store_true", help="Skip automatic setup check")
    parser.add_argument("--list-plugins", action="store_true", help="List available plugins")
    parser.add_argument("--plugin", metavar="NAME", help="Run a specific plugin")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    parser.add_argument(
        "command",
        nargs="?",
        choices=("interactive", "chat", "status", "capabilities"),
        help="Subcommand to run",
    )
    parser.add_argument("message", nargs="?", help="Message for the chat command")
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    print_banner()

    try:
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
        if args.command == "interactive":
            run_interactive_cli()
        elif args.command == "chat":
            run_chat(args.message) if args.message else print('Usage: windows-ai chat "your message"')
        elif args.command == "status":
            show_status()
        elif args.command == "capabilities":
            show_capabilities()
        else:
            if not args.skip_setup and check_first_run():
                print("\nFirst-time setup is needed. Run: windows-ai --setup\n")
                return
            run_interactive_cli()
    except KeyboardInterrupt:
        logger.info("Shutdown requested by user")
    except Exception as exc:
        logger.error("Error: %s", exc, exc_info=args.verbose)
        sys.exit(1)


def check_first_run() -> bool:
    """Return whether first-run setup is required."""
    try:
        from windows_ai.core.auto_setup import AutoSetup
        return AutoSetup().is_first_run()
    except Exception as exc:
        logger.debug("Auto-setup check skipped: %s", exc)
        return False


def run_setup() -> None:
    """Run the first-time setup wizard."""
    from windows_ai.core.auto_setup import AutoSetup

    result = asyncio.run(AutoSetup().run_first_time_setup())
    if not result.get("directories_created"):
        raise RuntimeError("Setup failed. Check the application logs for details.")
    print("\nSetup complete. Windows AI is ready to use.\n")


def list_plugins() -> None:
    """List registered plugin categories without duplicating plugin discovery."""
    import json

    registry_path = Path(__file__).parent / "plugins" / "QUALITY_PLUGINS_REGISTRY.json"
    if not registry_path.exists():
        print("No plugin registry is available.")
        return
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    print(f"\nAvailable plugins: {registry.get('total_plugins', 'unknown')}\n")
    for category, plugins in sorted(registry.get("categories", {}).items()):
        print(f"  {category}: {len(plugins)}")


def launch_gui() -> None:
    """Launch the GUI application, falling back to the CLI when unavailable."""
    gui_path = Path(__file__).parent.parent / "apps" / "gui"
    if gui_path.exists() and (gui_path / "package.json").exists():
        try:
            subprocess.run(["npm", "start"], cwd=gui_path, check=True)
            return
        except (FileNotFoundError, subprocess.CalledProcessError) as exc:
            logger.warning("GUI could not be started: %s", exc)
    run_interactive_cli()


def run_interactive_cli() -> None:
    """Run the interactive CLI."""
    print("\nType 'help' for commands, or 'quit' to exit.\n")
    while True:
        try:
            user_input = input("Windows AI> ").strip()
            if not user_input:
                continue
            command = user_input.lower()
            if command in {"quit", "exit", "q"}:
                print("Goodbye!")
                return
            if command == "help":
                print("help | status | plugins | setup | capabilities | quit")
            elif command == "status":
                show_status()
            elif command == "plugins":
                list_plugins()
            elif command == "setup":
                run_setup()
            elif command == "capabilities":
                show_capabilities()
            else:
                run_chat(user_input)
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            return


def run_chat(message: str | None) -> None:
    """Send a message through the canonical runtime."""
    if not message:
        return

    from windows_ai.bootstrap import create_runtime

    async def _chat() -> None:
        runtime = create_runtime()
        try:
            response = await runtime.chat(agent_id="default", message=message)
            print(f"\n{response}\n")
        finally:
            runtime.stop()

    try:
        asyncio.run(_chat())
    except Exception as exc:
        logger.error("Chat failed: %s", exc)
        print(f"[!] Chat unavailable: {exc}")


def show_capabilities() -> None:
    """Display capabilities exposed by the canonical runtime."""
    from windows_ai.bootstrap import create_runtime

    runtime = create_runtime()
    try:
        snapshot = runtime.capabilities()
        print("\n--- Windows AI Capabilities ---")
        for key, value in snapshot.items():
            print(f"{key}: {value}")
        print("--------------------------------\n")
    finally:
        runtime.stop()


def show_status() -> None:
    """Display local setup and API status."""
    import json
    import urllib.request

    config_file = Path.home() / ".windows_ai" / "config.json"
    print("\n--- Windows AI Status ---")
    print(f"Config file: {config_file}")
    print(f"Config exists: {config_file.exists()}")
    if config_file.exists():
        try:
            config = json.loads(config_file.read_text(encoding="utf-8"))
            print(f"Setup complete: {config.get('setup_complete', False)}")
        except (OSError, ValueError) as exc:
            print(f"Config error: {exc}")
    try:
        with urllib.request.urlopen("http://127.0.0.1:8010/health", timeout=2) as response:
            print(f"API server: running (HTTP {response.status})")
    except Exception:
        print("API server: not running")
    print("--------------------------\n")


def launch_tray() -> None:
    """Launch the GUI's tray mode."""
    launch_gui()


def start_api_server() -> None:
    """Start the canonical API application."""
    import uvicorn
    from windows_ai.api.server import app

    uvicorn.run(app, host="127.0.0.1", port=8010, log_level="info")


def run_plugin(plugin_name: str) -> None:
    """Execute a named plugin through the existing plugin manager."""
    from windows_ai.core.plugin_manager import PluginManager

    async def _run() -> None:
        manager = PluginManager()
        await manager.initialize()
        print(await manager.execute_plugin(plugin_name))

    try:
        asyncio.run(_run())
    except Exception as exc:
        logger.error("Plugin execution failed: %s", exc)
        print(f"[!] Failed to run plugin '{plugin_name}': {exc}")


if __name__ == "__main__":
    main()
