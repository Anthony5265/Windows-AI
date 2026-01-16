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
        # Check for first-run setup (unless explicitly skipped)
        if not args.skip_setup and not args.setup:
            from windows_ai.core.auto_setup import AutoSetup
            setup = AutoSetup()
            
            if setup.is_first_run():
                logger.info("\n[*] First run detected - starting automatic setup...")
                print("\n" + "="*60)
                print("WELCOME TO WINDOWS AI!")
                print("="*60)
                print("\nThis is your first time running Windows AI.")
                print("I'll now set up everything you need:")
                print("  1. Create configuration directories")
                print("  2. Download a small local AI model (Ollama)")
                print("  3. Configure system integration")
                print("  4. Launch the GUI interface")
                print("\nThis will take 2-5 minutes...")
                print("="*60 + "\n")
                
                # Run automatic setup
                asyncio.run(setup.run_first_time_setup())
                
                print("\n" + "="*60)
                print("SETUP COMPLETE!")
                print("="*60)
                print("\nWindows AI is now ready to use.")
                print("Launching GUI interface...")
                print("="*60 + "\n")
                
                # Auto-launch GUI after setup
                launch_gui()
                return
        
        if args.setup:
            run_setup()
        elif args.list_plugins:
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
            # Default behavior: launch GUI if already setup, otherwise show help
            from windows_ai.core.auto_setup import AutoSetup
            setup = AutoSetup()
            
            if not setup.is_first_run():
                logger.info("[*] Launching Windows AI GUI...")
                launch_gui()
            else:
                # First run without arguments - show help
                parser.print_help()
                print("\nStatus: Alpha Development")
                print("For more information, see: README.md")
                print("\nQuick Start:")
                print("  windows-ai              Run first-time setup & launch GUI")
                print("  windows-ai --gui        Launch GUI")
                print("  windows-ai --tray       Launch system tray")
                print("  windows-ai --api        Start API server")
                print("  windows-ai --setup      Run setup wizard")
                print("  windows-ai --list-plugins  List available plugins")

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
    
    if result.get("status") == "success":
        print("\n" + "="*60)
        print("SETUP COMPLETE!")
        print("="*60)
        print("\nWindows AI is now ready to use.")
        print("\nYou can now:")
        print("  - Double-click WindowsAI.exe to launch GUI")
        print("  - Run 'windows-ai --tray' for system tray")
        print("  - Run 'windows-ai --api' for API server")
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
        # Try to launch the Tkinter-based ChatGUI
        from control_center.gui import ChatGUI
        import tkinter as tk
        
        print("[*] Starting Windows AI Control Center...")
        root = tk.Tk()
        root.title("Windows AI Control Center")
        app = ChatGUI(root)
        root.mainloop()
        
    except ImportError as e:
        logger.warning(f"Could not import GUI components: {e}")
        print("[!] GUI components not available.")
        print("\nStarting interactive CLI mode instead...")
        run_interactive_cli()
    except Exception as e:
        logger.error(f"Failed to launch GUI: {e}")
        print(f"[!] GUI launch failed: {e}")
        print("\nStarting interactive CLI mode instead...")
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
                print("  help     - Show this help")
                print("  status   - Show system status")
                print("  plugins  - List available plugins")
                print("  setup    - Run setup wizard")
                print("  quit     - Exit Windows AI")
            elif user_input.lower() == 'status':
                show_status()
            elif user_input.lower() == 'plugins':
                list_plugins()
            elif user_input.lower() == 'setup':
                run_setup()
            else:
                print(f"Unknown command: {user_input}")
                print("Type 'help' for available commands.")
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except EOFError:
            print("\nGoodbye!")
            break


def show_status():
    """Show Windows AI status"""
    from pathlib import Path
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
    
    # Check Ollama
    try:
        import subprocess
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print(f"Ollama: Available")
            models = result.stdout.strip().split('\n')[1:]  # Skip header
            print(f"Models: {len(models)} installed")
        else:
            print("Ollama: Not running")
    except Exception:
        print("Ollama: Not installed")
    
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
