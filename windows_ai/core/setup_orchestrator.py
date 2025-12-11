"""
First-Run Setup Wizard for Windows AI

Guides users through initial setup:
- Dependency verification
- API key collection
- Model downloads
- System optimization
- Initial configuration
"""

import os
import sys
import logging
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, asdict
import json

logger = logging.getLogger(__name__)


@dataclass
class SetupStep:
    """Represents a single setup step"""
    id: str
    name: str
    description: str
    required: bool = True
    completed: bool = False
    error: Optional[str] = None
    progress: int = 0  # 0-100
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class SetupOrchestrator:
    """
    Orchestrates the first-run setup process
    
    Manages setup steps, tracks progress, and handles errors
    """
    
    def __init__(self, credential_manager, app_database):
        self.credential_manager = credential_manager
        self.app_database = app_database
        
        self.setup_dir = Path.home() / ".windows_ai" / "setup"
        self.setup_dir.mkdir(parents=True, exist_ok=True)
        
        self.progress_file = self.setup_dir / "setup_progress.json"
        self.steps: Dict[str, SetupStep] = {}
        self.current_step: Optional[str] = None
        
        self._init_setup_steps()
        self._load_progress()
        
        logger.info("Setup Orchestrator initialized")
    
    def _init_setup_steps(self):
        """Initialize all setup steps"""
        steps = [
            SetupStep(
                id="check_dependencies",
                name="Check Dependencies",
                description="Verify required Python packages are installed",
                required=True
            ),
            SetupStep(
                id="create_database",
                name="Initialize Database",
                description="Create application database and tables",
                required=True
            ),
            SetupStep(
                id="configure_directories",
                name="Configure Directories",
                description="Set up configuration and data directories",
                required=True
            ),
            SetupStep(
                id="collect_api_keys",
                name="Collect API Keys",
                description="Gather API keys for AI services (optional)",
                required=False
            ),
            SetupStep(
                id="download_models",
                name="Download Models",
                description="Download recommended AI models (optional)",
                required=False
            ),
            SetupStep(
                id="optimize_system",
                name="Optimize System",
                description="Apply system optimizations for best performance",
                required=False
            ),
            SetupStep(
                id="create_default_user",
                name="Create User Profile",
                description="Set up default user profile",
                required=True
            ),
            SetupStep(
                id="finalize_setup",
                name="Finalize Setup",
                description="Complete setup and prepare system for first use",
                required=True
            )
        ]
        
        for step in steps:
            self.steps[step.id] = step
    
    def _load_progress(self):
        """Load setup progress from disk"""
        if not self.progress_file.exists():
            return
        
        try:
            with open(self.progress_file, 'r') as f:
                data = json.load(f)
                
            for step_id, step_data in data.get('steps', {}).items():
                if step_id in self.steps:
                    self.steps[step_id].completed = step_data.get('completed', False)
                    self.steps[step_id].error = step_data.get('error')
                    self.steps[step_id].progress = step_data.get('progress', 0)
            
            self.current_step = data.get('current_step')
            logger.debug(f"Loaded setup progress: {len([s for s in self.steps.values() if s.completed])} steps completed")
            
        except Exception as e:
            logger.error(f"Failed to load setup progress: {e}")
    
    def _save_progress(self):
        """Save setup progress to disk"""
        try:
            data = {
                'current_step': self.current_step,
                'steps': {
                    step_id: step.to_dict()
                    for step_id, step in self.steps.items()
                }
            }
            
            with open(self.progress_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save setup progress: {e}")
    
    async def run_setup(self, progress_callback: Optional[Callable] = None) -> bool:
        """
        Run the complete setup process
        
        Args:
            progress_callback: Optional callback for progress updates
            
        Returns:
            True if setup completed successfully
        """
        logger.info("Starting first-run setup...")
        
        try:
            # Run each step in order
            for step_id, step in self.steps.items():
                if step.completed:
                    logger.debug(f"Skipping completed step: {step.name}")
                    continue
                
                self.current_step = step_id
                self._save_progress()
                
                if progress_callback:
                    progress_callback(step.to_dict())
                
                logger.info(f"Running setup step: {step.name}")
                
                try:
                    # Execute the step
                    success = await self._execute_step(step_id)
                    
                    if success:
                        step.completed = True
                        step.progress = 100
                        step.error = None
                        logger.info(f"Step completed: {step.name}")
                    else:
                        if step.required:
                            step.error = "Required step failed"
                            logger.error(f"Required step failed: {step.name}")
                            self._save_progress()
                            return False
                        else:
                            logger.warning(f"Optional step failed: {step.name}")
                            step.completed = True  # Mark as completed to continue
                    
                except Exception as e:
                    logger.error(f"Error in setup step {step.name}: {e}")
                    step.error = str(e)
                    
                    if step.required:
                        self._save_progress()
                        return False
                    else:
                        step.completed = True  # Mark as completed to continue
                
                self._save_progress()
                
                if progress_callback:
                    progress_callback(step.to_dict())
            
            # Mark setup as complete
            await self._mark_setup_complete()
            
            logger.info("First-run setup completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Setup failed: {e}")
            return False
    
    async def _execute_step(self, step_id: str) -> bool:
        """Execute a specific setup step"""
        step = self.steps.get(step_id)
        if not step:
            return False
        
        if step_id == "check_dependencies":
            return await self._check_dependencies(step)
        elif step_id == "create_database":
            return await self._create_database(step)
        elif step_id == "configure_directories":
            return await self._configure_directories(step)
        elif step_id == "collect_api_keys":
            return await self._collect_api_keys(step)
        elif step_id == "download_models":
            return await self._download_models(step)
        elif step_id == "optimize_system":
            return await self._optimize_system(step)
        elif step_id == "create_default_user":
            return await self._create_default_user(step)
        elif step_id == "finalize_setup":
            return await self._finalize_setup(step)
        else:
            logger.warning(f"Unknown setup step: {step_id}")
            return False
    
    async def _check_dependencies(self, step: SetupStep) -> bool:
        """Check that required dependencies are installed"""
        try:
            required_packages = [
                'fastapi',
                'uvicorn',
                'pydantic',
                'sqlalchemy',
                'aiohttp'
            ]
            
            missing = []
            for package in required_packages:
                step.progress = int((required_packages.index(package) + 1) / len(required_packages) * 100)
                
                try:
                    __import__(package)
                    logger.debug(f"Dependency found: {package}")
                except ImportError:
                    missing.append(package)
                    logger.warning(f"Missing dependency: {package}")
            
            if missing:
                logger.error(f"Missing required dependencies: {', '.join(missing)}")
                step.error = f"Missing packages: {', '.join(missing)}"
                return False
            
            logger.info("All dependencies verified")
            return True
            
        except Exception as e:
            logger.error(f"Dependency check failed: {e}")
            step.error = str(e)
            return False
    
    async def _create_database(self, step: SetupStep) -> bool:
        """Initialize the application database"""
        try:
            step.progress = 50
            
            # Database is already initialized in constructor
            # Just verify it's working
            user_id = self.app_database.create_user("default", "user@localhost")
            
            if not user_id:
                step.error = "Failed to create default user"
                return False
            
            step.progress = 100
            logger.info("Database initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            step.error = str(e)
            return False
    
    async def _configure_directories(self, step: SetupStep) -> bool:
        """Set up configuration and data directories"""
        try:
            dirs = [
                Path.home() / ".windows_ai",
                Path.home() / ".windows_ai" / "plugins",
                Path.home() / ".windows_ai" / "models",
                Path.home() / ".windows_ai" / "logs",
                Path.home() / ".windows_ai" / "cache"
            ]
            
            for i, directory in enumerate(dirs):
                directory.mkdir(parents=True, exist_ok=True)
                step.progress = int((i + 1) / len(dirs) * 100)
                logger.debug(f"Created directory: {directory}")
            
            logger.info("Directories configured successfully")
            return True
            
        except Exception as e:
            logger.error(f"Directory configuration failed: {e}")
            step.error = str(e)
            return False
    
    async def _collect_api_keys(self, step: SetupStep) -> bool:
        """Collect API keys from user (optional step)"""
        try:
            # Check if any API keys are already configured
            services = ['openai', 'anthropic', 'google']
            configured_count = 0
            
            for service in services:
                key = await self.credential_manager.get_credential(service, 'api_key')
                if key:
                    configured_count += 1
            
            step.progress = 100
            
            if configured_count > 0:
                logger.info(f"{configured_count} API keys already configured")
                return True
            
            # No keys configured - this is OK for optional step
            # GUI will prompt user to add keys later
            logger.info("No API keys configured yet (can be added later)")
            return True
            
        except Exception as e:
            logger.error(f"API key collection failed: {e}")
            step.error = str(e)
            return False
    
    async def _download_models(self, step: SetupStep) -> bool:
        """Download recommended AI models (optional)"""
        try:
            # For now, just check if models directory exists
            models_dir = Path.home() / ".windows_ai" / "models"
            
            step.progress = 50
            
            if models_dir.exists():
                logger.info("Models directory ready")
                step.progress = 100
                return True
            
            step.progress = 100
            logger.info("Model downloads skipped (can be done later)")
            return True
            
        except Exception as e:
            logger.error(f"Model download failed: {e}")
            step.error = str(e)
            return False
    
    async def _optimize_system(self, step: SetupStep) -> bool:
        """Apply system optimizations"""
        try:
            optimizations = [
                ("Set cache size", lambda: self.app_database.set_system_config("cache_size_mb", 500, "int")),
                ("Enable compression", lambda: self.app_database.set_system_config("enable_compression", True, "bool")),
                ("Set max threads", lambda: self.app_database.set_system_config("max_threads", 4, "int")),
            ]
            
            for i, (name, func) in enumerate(optimizations):
                try:
                    func()
                    logger.debug(f"Applied optimization: {name}")
                except Exception as e:
                    logger.warning(f"Failed to apply {name}: {e}")
                
                step.progress = int((i + 1) / len(optimizations) * 100)
            
            logger.info("System optimizations applied")
            return True
            
        except Exception as e:
            logger.error(f"System optimization failed: {e}")
            step.error = str(e)
            return False
    
    async def _create_default_user(self, step: SetupStep) -> bool:
        """Create default user profile"""
        try:
            step.progress = 50
            
            # Check if default user already exists
            user = self.app_database.get_user_by_username("default")
            
            if not user:
                user_id = self.app_database.create_user("default", "user@localhost")
                if not user_id:
                    step.error = "Failed to create default user"
                    return False
                logger.info("Default user created")
            else:
                logger.info("Default user already exists")
            
            step.progress = 100
            return True
            
        except Exception as e:
            logger.error(f"User creation failed: {e}")
            step.error = str(e)
            return False
    
    async def _finalize_setup(self, step: SetupStep) -> bool:
        """Finalize setup process"""
        try:
            # Set setup completion flag
            step.progress = 50
            
            self.app_database.set_system_config(
                "setup_completed",
                True,
                "bool",
                "Indicates first-run setup has been completed"
            )
            
            self.app_database.set_system_config(
                "setup_completed_at",
                str(datetime.now().isoformat()),
                "string",
                "Timestamp when setup was completed"
            )
            
            step.progress = 100
            logger.info("Setup finalized")
            return True
            
        except Exception as e:
            logger.error(f"Setup finalization failed: {e}")
            step.error = str(e)
            return False
    
    async def _mark_setup_complete(self):
        """Mark setup as fully complete"""
        completion_file = self.setup_dir / "setup_complete.json"
        
        try:
            data = {
                'completed': True,
                'completed_at': datetime.now().isoformat(),
                'steps_completed': len([s for s in self.steps.values() if s.completed]),
                'total_steps': len(self.steps)
            }
            
            with open(completion_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to mark setup complete: {e}")
    
    def is_setup_complete(self) -> bool:
        """Check if setup has been completed"""
        try:
            if self.app_database:
                return self.app_database.get_system_config("setup_completed") == True
            
            completion_file = self.setup_dir / "setup_complete.json"
            return completion_file.exists()
            
        except Exception:
            return False
    
    def get_setup_status(self) -> Dict[str, Any]:
        """Get current setup status"""
        completed_steps = [s for s in self.steps.values() if s.completed]
        failed_steps = [s for s in self.steps.values() if s.error and not s.completed]
        
        return {
            'is_complete': self.is_setup_complete(),
            'current_step': self.current_step,
            'total_steps': len(self.steps),
            'completed_steps': len(completed_steps),
            'failed_steps': len(failed_steps),
            'progress_percent': int(len(completed_steps) / len(self.steps) * 100),
            'steps': [step.to_dict() for step in self.steps.values()]
        }
    
    async def reset_setup(self):
        """Reset setup progress (for testing)"""
        logger.warning("Resetting setup progress")
        
        for step in self.steps.values():
            step.completed = False
            step.error = None
            step.progress = 0
        
        self.current_step = None
        self._save_progress()
        
        # Remove completion file
        completion_file = self.setup_dir / "setup_complete.json"
        if completion_file.exists():
            completion_file.unlink()


from datetime import datetime
