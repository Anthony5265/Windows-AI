"""
Windows AI - Command Line Interface
Simple, user-friendly CLI for all AI capabilities
"""

import asyncio
import sys
import argparse
import logging
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)


class WindowsAICLI:
    """Command-line interface for Windows AI"""

    def __init__(self):
        self.orchestrator = None

    async def initialize(self):
        """Initialize Windows AI"""
        from windows_ai.core.orchestrator import quick_start

        logger.info("Initializing Windows AI...")
        self.orchestrator = await quick_start()
        return self.orchestrator

    async def chat(self, message: str, provider: str = "openai"):
        """Chat with AI"""
        if not self.orchestrator:
            await self.initialize()

        response = await self.orchestrator.chat(message, provider)
        print(f"\n🤖 AI: {response}\n")

    async def generate_image(self, prompt: str, output: str = "output.png"):
        """Generate an image"""
        if not self.orchestrator:
            await self.initialize()

        image_bytes = await self.orchestrator.generate_image(prompt)
        with open(output, "wb") as f:
            f.write(image_bytes)
        print(f"\n✓ Image saved to {output}\n")

    async def transcribe(self, audio_file: str):
        """Transcribe audio file"""
        if not self.orchestrator:
            await self.initialize()

        text = await self.orchestrator.transcribe(audio_file)
        print(f"\n📝 Transcription: {text}\n")

    async def speak(self, text: str, output: str = "output.mp3"):
        """Convert text to speech"""
        if not self.orchestrator:
            await self.initialize()

        audio_bytes = await self.orchestrator.speak(text)
        with open(output, "wb") as f:
            f.write(audio_bytes)
        print(f"\n✓ Audio saved to {output}\n")

    async def search(self, query: str):
        """Search the web"""
        if not self.orchestrator:
            await self.initialize()

        results = await self.orchestrator.search_web(query)
        print(f"\n🔍 Search results for '{query}':\n")
        for i, result in enumerate(results[:5], 1):
            print(f"{i}. {result.get('title', 'No title')}")
            print(f"   {result.get('url', '')}\n")

    async def analyze_image(self, image_path: str, task: str = "describe"):
        """Analyze an image"""
        if not self.orchestrator:
            await self.initialize()

        result = await self.orchestrator.analyze_image(image_path, task)
        print(f"\n📸 Image analysis:\n{result}\n")

    async def automate(self, task: str):
        """Automate a task"""
        if not self.orchestrator:
            await self.initialize()

        result = await self.orchestrator.automate_task(task)
        print(f"\n⚡ Automation result:\n{result}\n")

    def list_capabilities(self):
        """List all available capabilities"""
        if not self.orchestrator:
            asyncio.run(self.initialize())

        capabilities = self.orchestrator.list_capabilities()
        print("\n📋 Windows AI Capabilities:\n")
        for category, caps in capabilities.items():
            print(f"  {category.upper()}: {len(caps)} features")
        print(f"\n  Total: {sum(len(c) for c in capabilities.values())} capabilities\n")

    def status(self):
        """Show system status"""
        if not self.orchestrator:
            asyncio.run(self.initialize())

        status = self.orchestrator.status()
        print("\n📊 Windows AI Status:\n")
        print(f"  Initialized: {status['initialized']}")
        print(f"  Managers: {status['managers_loaded']}")
        print(f"  Performance mode: {status['config'].get('performance_mode', 'balanced')}")
        print(f"  Privacy mode: {status['config'].get('privacy_mode', 'standard')}\n")


async def interactive_mode():
    """Run Windows AI in interactive mode"""
    cli = WindowsAICLI()
    await cli.initialize()

    print("\n" + "="*60)
    print("🚀 Windows AI - Interactive Mode")
    print("="*60)
    print("\nCommands:")
    print("  chat <message>     - Chat with AI")
    print("  image <prompt>     - Generate image")
    print("  search <query>     - Search the web")
    print("  status             - Show system status")
    print("  help               - Show this help")
    print("  exit               - Exit interactive mode\n")

    while True:
        try:
            user_input = input("windows-ai> ").strip()

            if not user_input:
                continue

            if user_input.lower() in ["exit", "quit", "q"]:
                print("\n👋 Goodbye!\n")
                break

            if user_input.lower() == "help":
                print("\nCommands:")
                print("  chat <message>     - Chat with AI")
                print("  image <prompt>     - Generate image")
                print("  search <query>     - Search the web")
                print("  status             - Show system status")
                print("  exit               - Exit interactive mode\n")
                continue

            if user_input.lower() == "status":
                cli.status()
                continue

            parts = user_input.split(maxsplit=1)
            command = parts[0].lower()
            args = parts[1] if len(parts) > 1 else ""

            if command == "chat":
                await cli.chat(args)
            elif command == "image":
                await cli.generate_image(args)
            elif command == "search":
                await cli.search(args)
            else:
                # Default to chat
                await cli.chat(user_input)

        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!\n")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}\n")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Windows AI - Unified AI Platform",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  windows-ai chat "Hello, how are you?"
  windows-ai image "A beautiful sunset over mountains"
  windows-ai search "latest AI news"
  windows-ai transcribe audio.mp3
  windows-ai speak "Hello world" -o output.mp3
  windows-ai analyze-image photo.jpg
  windows-ai status
  windows-ai interactive
        """
    )

    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--provider", default="openai", help="AI provider (default: openai)")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Chat command
    chat_parser = subparsers.add_parser("chat", help="Chat with AI")
    chat_parser.add_argument("message", nargs="+", help="Message to send")

    # Image generation
    image_parser = subparsers.add_parser("image", help="Generate image")
    image_parser.add_argument("prompt", nargs="+", help="Image prompt")
    image_parser.add_argument("-o", "--output", default="output.png", help="Output file")

    # Search
    search_parser = subparsers.add_parser("search", help="Search the web")
    search_parser.add_argument("query", nargs="+", help="Search query")

    # Transcribe
    transcribe_parser = subparsers.add_parser("transcribe", help="Transcribe audio")
    transcribe_parser.add_argument("file", help="Audio file path")

    # Speak
    speak_parser = subparsers.add_parser("speak", help="Text to speech")
    speak_parser.add_argument("text", nargs="+", help="Text to speak")
    speak_parser.add_argument("-o", "--output", default="output.mp3", help="Output file")

    # Analyze image
    analyze_parser = subparsers.add_parser("analyze-image", help="Analyze image")
    analyze_parser.add_argument("file", help="Image file path")
    analyze_parser.add_argument("--task", default="describe", help="Analysis task")

    # Automate
    automate_parser = subparsers.add_parser("automate", help="Automate a task")
    automate_parser.add_argument("task", nargs="+", help="Task description")

    # List capabilities
    subparsers.add_parser("capabilities", help="List all capabilities")

    # Status
    subparsers.add_parser("status", help="Show system status")

    # Interactive mode
    subparsers.add_parser("interactive", help="Start interactive mode")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    cli = WindowsAICLI()

    # Handle commands
    if args.command == "chat":
        message = " ".join(args.message)
        asyncio.run(cli.chat(message, args.provider))

    elif args.command == "image":
        prompt = " ".join(args.prompt)
        asyncio.run(cli.generate_image(prompt, args.output))

    elif args.command == "search":
        query = " ".join(args.query)
        asyncio.run(cli.search(query))

    elif args.command == "transcribe":
        asyncio.run(cli.transcribe(args.file))

    elif args.command == "speak":
        text = " ".join(args.text)
        asyncio.run(cli.speak(text, args.output))

    elif args.command == "analyze-image":
        asyncio.run(cli.analyze_image(args.file, args.task))

    elif args.command == "automate":
        task = " ".join(args.task)
        asyncio.run(cli.automate(task))

    elif args.command == "capabilities":
        cli.list_capabilities()

    elif args.command == "status":
        cli.status()

    elif args.command == "interactive":
        asyncio.run(interactive_mode())

    else:
        # Default to interactive mode
        asyncio.run(interactive_mode())


if __name__ == "__main__":
    main()
