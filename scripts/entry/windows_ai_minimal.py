"""
Windows AI - Ultra Minimal Standalone
No external dependencies - just works!
"""

import sys
import os
import logging
from pathlib import Path

# Setup logging
log_file = Path.home() / "windows_ai.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_file)
    ]
)

logger = logging.getLogger(__name__)


def print_banner():
    """Print welcome banner"""
    print("\n" + "="*60)
    print("            WINDOWS AI v2.0")
    print("      Minimal Standalone Version")
    print("="*60 + "\n")


def check_dependencies():
    """Check what's available"""
    deps = {}
    
    try:
        import openai
        deps['openai'] = openai.__version__
    except:
        deps['openai'] = None
        
    try:
        import anthropic
        deps['anthropic'] = anthropic.__version__
    except:
        deps['anthropic'] = None
        
    try:
        import fastapi
        deps['fastapi'] = fastapi.__version__
    except:
        deps['fastapi'] = None
        
    return deps


def show_status():
    """Show system status"""
    print_banner()
    
    print(f"Python Version: {sys.version.split()[0]}")
    print(f"Platform: {sys.platform}")
    print(f"Log file: {Path.home() / 'windows_ai.log'}")
    print()
    
    # Check API keys
    api_keys = {}
    key_names = ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY"]
    
    for key in key_names:
        val = os.getenv(key)
        if val:
            api_keys[key] = f"{val[:8]}..."
    
    if api_keys:
        print("API Keys Found:")
        for key, val in api_keys.items():
            print(f"  ✓ {key}: {val}")
    else:
        print("No API keys found in environment")
        print("Set keys like: set OPENAI_API_KEY=sk-...")
    
    print()
    
    # Check dependencies
    deps = check_dependencies()
    print("Dependencies:")
    for name, version in deps.items():
        if version:
            print(f"  ✓ {name}: {version}")
        else:
            print(f"  ✗ {name}: not installed")
    
    print("\n" + "="*60)
    print("\nUsage:")
    print("  WindowsAI.exe status     - Show this status")
    print("  WindowsAI.exe help       - Show help")
    print("\nTo use AI features, install:")
    print("  pip install openai anthropic")
    print("\nFor API server:")
    print("  pip install fastapi uvicorn")
    print()


def show_help():
    """Show help"""
    print_banner()
    print("Windows AI - Minimal Standalone Version")
    print()
    print("This is a minimal version that checks your Python environment")
    print("and shows what AI capabilities are available.")
    print()
    print("Commands:")
    print("  status   - Show system status and available features")
    print("  help     - Show this help message")
    print()
    print("Setup:")
    print("  1. Install Python 3.8+ from python.org")
    print("  2. Install dependencies:")
    print("     pip install openai anthropic fastapi uvicorn")
    print("  3. Set API keys:")
    print("     set OPENAI_API_KEY=your-key-here")
    print("  4. Run: WindowsAI.exe status")
    print()
    print("For the full version with all features, clone the repository:")
    print("  git clone https://github.com/Anthony5265/Windows-AI.git")
    print()


def main():
    """Main entry point"""
    logger.info("WindowsAI started")
    
    args = sys.argv[1:]
    
    if not args or args[0] == "status":
        show_status()
    elif args[0] in ["help", "--help", "-h"]:
        show_help()
    else:
        print(f"Unknown command: {args[0]}")
        print("Run 'WindowsAI.exe help' for usage")
    
    logger.info("WindowsAI finished")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted")
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        print(f"\nError: {e}")
        print(f"Check log file: {Path.home() / 'windows_ai.log'}")
