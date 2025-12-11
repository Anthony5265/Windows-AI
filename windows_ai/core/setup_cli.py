"""
Command-Line Interface for First-Run Setup Wizard

Provides interactive CLI for initial system configuration
"""

import asyncio
import sys
from pathlib import Path
from typing import Optional
import logging

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from windows_ai.core.setup_orchestrator import SetupOrchestrator
from windows_ai.core.credential_manager import CredentialManager
from windows_ai.core.app_database import ApplicationDatabase

logger = logging.getLogger(__name__)


class SetupCLI:
    """Command-line interface for setup wizard"""
    
    def __init__(self):
        self.credential_manager = CredentialManager()
        
        # Initialize database
        db_path = Path.home() / ".windows_ai" / "windows_ai.db"
        self.app_database = ApplicationDatabase(str(db_path))
        
        self.orchestrator = SetupOrchestrator(
            self.credential_manager,
            self.app_database
        )
    
    def print_header(self):
        """Print welcome header"""
        print("\n" + "=" * 60)
        print("       Windows AI - First Run Setup Wizard")
        print("=" * 60)
        print("\nWelcome! This wizard will help you set up Windows AI.")
        print("The setup process includes:")
        print("  • Dependency verification")
        print("  • Database initialization")
        print("  • Directory configuration")
        print("  • API key collection (optional)")
        print("  • System optimization")
        print("\n" + "-" * 60 + "\n")
    
    def progress_callback(self, step_data: dict):
        """Display progress updates"""
        name = step_data.get('name', 'Unknown')
        progress = step_data.get('progress', 0)
        completed = step_data.get('completed', False)
        error = step_data.get('error')
        
        if error:
            print(f"  ✗ {name}: FAILED - {error}")
        elif completed:
            print(f"  ✓ {name}: COMPLETE")
        else:
            bar_length = 30
            filled = int(bar_length * progress / 100)
            bar = "█" * filled + "░" * (bar_length - filled)
            print(f"  ⟳ {name}: [{bar}] {progress}%", end='\r')
    
    async def run_interactive_setup(self):
        """Run interactive setup with user prompts"""
        self.print_header()
        
        # Check if already completed
        if self.orchestrator.is_setup_complete():
            print("✓ Setup has already been completed!")
            print("\nIf you want to run setup again, use: --reset")
            return True
        
        # Get current status
        status = self.orchestrator.get_setup_status()
        if status['completed_steps'] > 0:
            print(f"Setup in progress: {status['completed_steps']}/{status['total_steps']} steps completed")
            response = input("\nContinue from where you left off? (Y/n): ").strip().lower()
            if response == 'n':
                print("Setup cancelled.")
                return False
            print()
        
        print("Starting setup process...\n")
        
        # Run setup with progress callback
        success = await self.orchestrator.run_setup(
            progress_callback=self.progress_callback
        )
        
        print("\n\n" + "=" * 60)
        
        if success:
            print("✓ Setup completed successfully!")
            print("\nWindows AI is ready to use.")
            print("\nNext steps:")
            print("  • Add API keys: windowsai config set-key <service> <key>")
            print("  • Start the server: windowsai start")
            print("  • Open the GUI: windowsai gui")
        else:
            print("✗ Setup failed.")
            print("\nSome steps did not complete successfully.")
            print("Check the logs for details: ~/.windows_ai/logs/")
            print("\nYou can retry setup by running this command again.")
        
        print("=" * 60 + "\n")
        
        return success
    
    async def collect_api_keys(self):
        """Interactive API key collection"""
        print("\n" + "-" * 60)
        print("API Key Configuration (Optional)")
        print("-" * 60)
        print("\nYou can add API keys now or later through the GUI.")
        
        response = input("\nWould you like to add API keys now? (y/N): ").strip().lower()
        if response != 'y':
            print("Skipping API key setup. You can add them later.")
            return
        
        services = [
            ('openai', 'OpenAI (GPT-4, GPT-3.5)'),
            ('anthropic', 'Anthropic (Claude)'),
            ('google', 'Google (Gemini)'),
            ('cohere', 'Cohere'),
            ('azure_openai', 'Azure OpenAI'),
        ]
        
        print("\nAvailable services:")
        for i, (service_id, name) in enumerate(services, 1):
            print(f"  {i}. {name}")
        
        print("\nEnter API keys (press Enter to skip each service):")
        
        for service_id, name in services:
            print(f"\n{name}:")
            key = input(f"  API Key: ").strip()
            
            if key:
                try:
                    await self.credential_manager.store_credential(
                        service=service_id,
                        key='api_key',
                        value=key,
                        description=f"API key for {name}"
                    )
                    print(f"  ✓ Saved {name} API key")
                except Exception as e:
                    print(f"  ✗ Failed to save: {e}")
        
        print("\n✓ API key configuration complete")
    
    async def show_status(self):
        """Show current setup status"""
        status = self.orchestrator.get_setup_status()
        
        print("\n" + "=" * 60)
        print("Setup Status")
        print("=" * 60)
        
        if status['is_complete']:
            print("\n✓ Setup is COMPLETE")
        else:
            print(f"\n⟳ Setup in progress: {status['progress_percent']}%")
            print(f"   {status['completed_steps']}/{status['total_steps']} steps completed")
        
        print("\nSteps:")
        for step in status['steps']:
            name = step['name']
            completed = step['completed']
            error = step.get('error')
            required = step['required']
            
            if error:
                status_icon = "✗"
                status_text = f"FAILED: {error}"
            elif completed:
                status_icon = "✓"
                status_text = "COMPLETE"
            else:
                status_icon = "○"
                status_text = "PENDING"
            
            req_text = " [REQUIRED]" if required else " [OPTIONAL]"
            print(f"  {status_icon} {name}{req_text}: {status_text}")
        
        print("=" * 60 + "\n")
    
    async def reset_setup(self):
        """Reset setup progress"""
        print("\n⚠ Warning: This will reset all setup progress.")
        response = input("Are you sure? (yes/N): ").strip().lower()
        
        if response == 'yes':
            await self.orchestrator.reset_setup()
            print("✓ Setup progress has been reset.")
        else:
            print("Cancelled.")


async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Windows AI First-Run Setup Wizard"
    )
    parser.add_argument(
        '--status',
        action='store_true',
        help='Show current setup status'
    )
    parser.add_argument(
        '--reset',
        action='store_true',
        help='Reset setup progress'
    )
    parser.add_argument(
        '--api-keys',
        action='store_true',
        help='Configure API keys interactively'
    )
    parser.add_argument(
        '--auto',
        action='store_true',
        help='Run setup without prompts (use defaults)'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        cli = SetupCLI()
        
        if args.status:
            await cli.show_status()
        elif args.reset:
            await cli.reset_setup()
        elif args.api_keys:
            await cli.collect_api_keys()
        else:
            # Run interactive setup
            success = await cli.run_interactive_setup()
            
            # Optionally collect API keys
            if success and not args.auto:
                await cli.collect_api_keys()
            
            sys.exit(0 if success else 1)
    
    except KeyboardInterrupt:
        print("\n\nSetup interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Setup failed with error: {e}")
        logger.exception("Setup error")
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())
