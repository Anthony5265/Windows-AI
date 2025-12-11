"""
Plugin Lifecycle Manager

Handles installation, configuration, updates, and dependency management for plugins.
"""

import os
import json
import logging
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class PluginState(str, Enum):
    """Plugin lifecycle states"""
    UNINSTALLED = "uninstalled"
    INSTALLED = "installed"
    CONFIGURED = "configured"
    ENABLED = "enabled"
    DISABLED = "disabled"
    ERROR = "error"
    UPDATING = "updating"


@dataclass
class PluginConfig:
    """Plugin configuration and state"""
    plugin_id: str
    state: PluginState
    version: str
    installed_at: Optional[str] = None
    configured_at: Optional[str] = None
    last_enabled: Optional[str] = None
    last_disabled: Optional[str] = None
    last_error: Optional[str] = None
    settings: Dict[str, Any] = None
    required_credentials: List[str] = None
    dependencies: List[str] = None
    
    def __post_init__(self):
        if self.settings is None:
            self.settings = {}
        if self.required_credentials is None:
            self.required_credentials = []
        if self.dependencies is None:
            self.dependencies = []
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['state'] = self.state.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PluginConfig":
        data['state'] = PluginState(data['state'])
        return cls(**data)


class PluginLifecycleManager:
    """
    Manages complete plugin lifecycle:
    - Installation and uninstallation
    - Configuration management
    - Credential requirements
    - Dependency resolution
    - Updates and versioning
    - Enable/disable state
    """
    
    def __init__(self, credential_manager, plugins_dir: Optional[Path] = None):
        self.credential_manager = credential_manager
        self.plugins_dir = plugins_dir or Path.home() / ".windows_ai" / "plugins"
        self.plugins_dir.mkdir(parents=True, exist_ok=True)
        
        self.config_file = self.plugins_dir / "plugin_configs.json"
        self.configs: Dict[str, PluginConfig] = {}
        
        self._load_configs()
        logger.info(f"Plugin Lifecycle Manager initialized with {len(self.configs)} configured plugins")
    
    def _load_configs(self):
        """Load plugin configurations from disk"""
        if not self.config_file.exists():
            return
        
        try:
            with open(self.config_file, 'r') as f:
                data = json.load(f)
                for plugin_id, config_data in data.items():
                    self.configs[plugin_id] = PluginConfig.from_dict(config_data)
            logger.debug(f"Loaded {len(self.configs)} plugin configurations")
        except Exception as e:
            logger.error(f"Failed to load plugin configurations: {e}")
    
    def _save_configs(self):
        """Save plugin configurations to disk"""
        try:
            data = {
                plugin_id: config.to_dict()
                for plugin_id, config in self.configs.items()
            }
            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.debug(f"Saved {len(self.configs)} plugin configurations")
        except Exception as e:
            logger.error(f"Failed to save plugin configurations: {e}")
    
    async def install_plugin(
        self,
        plugin_id: str,
        version: str,
        metadata: Dict[str, Any]
    ) -> bool:
        """
        Install a plugin
        
        Args:
            plugin_id: Unique plugin identifier
            version: Plugin version
            metadata: Plugin metadata including dependencies and requirements
            
        Returns:
            True if installed successfully
        """
        try:
            logger.info(f"Installing plugin: {plugin_id} v{version}")
            
            # Check if already installed
            if plugin_id in self.configs:
                existing = self.configs[plugin_id]
                if existing.state != PluginState.UNINSTALLED:
                    logger.warning(f"Plugin {plugin_id} already installed")
                    return False
            
            # Extract requirements from metadata
            required_credentials = metadata.get('requirements', {}).get('credentials', [])
            dependencies = metadata.get('requirements', {}).get('plugins', [])
            
            # Create plugin configuration
            config = PluginConfig(
                plugin_id=plugin_id,
                state=PluginState.INSTALLED,
                version=version,
                installed_at=datetime.now().isoformat(),
                required_credentials=required_credentials,
                dependencies=dependencies
            )
            
            self.configs[plugin_id] = config
            self._save_configs()
            
            logger.info(f"Plugin {plugin_id} installed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to install plugin {plugin_id}: {e}")
            return False
    
    async def uninstall_plugin(self, plugin_id: str) -> bool:
        """
        Uninstall a plugin
        
        Args:
            plugin_id: Unique plugin identifier
            
        Returns:
            True if uninstalled successfully
        """
        try:
            if plugin_id not in self.configs:
                logger.warning(f"Plugin {plugin_id} not found")
                return False
            
            config = self.configs[plugin_id]
            
            # Check for dependent plugins
            dependents = self._get_dependent_plugins(plugin_id)
            if dependents:
                logger.error(f"Cannot uninstall {plugin_id}: Required by {dependents}")
                return False
            
            # Mark as uninstalled
            config.state = PluginState.UNINSTALLED
            self._save_configs()
            
            logger.info(f"Plugin {plugin_id} uninstalled successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to uninstall plugin {plugin_id}: {e}")
            return False
    
    def _get_dependent_plugins(self, plugin_id: str) -> List[str]:
        """Get list of plugins that depend on this plugin"""
        dependents = []
        for pid, config in self.configs.items():
            if plugin_id in config.dependencies:
                if config.state not in [PluginState.UNINSTALLED, PluginState.DISABLED]:
                    dependents.append(pid)
        return dependents
    
    async def configure_plugin(
        self,
        plugin_id: str,
        settings: Dict[str, Any],
        credentials: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Configure a plugin with settings and credentials
        
        Args:
            plugin_id: Unique plugin identifier
            settings: Plugin-specific settings
            credentials: Dictionary of credential names to values
            
        Returns:
            True if configured successfully
        """
        try:
            if plugin_id not in self.configs:
                logger.error(f"Plugin {plugin_id} not installed")
                return False
            
            config = self.configs[plugin_id]
            
            # Store credentials
            if credentials:
                for cred_name, cred_value in credentials.items():
                    await self.credential_manager.store_credential(
                        service_id=plugin_id,
                        key_name=cred_name,
                        key_value=cred_value,
                        description=f"Credential for {plugin_id}"
                    )
            
            # Validate required credentials are present
            missing_creds = await self._check_missing_credentials(plugin_id)
            if missing_creds:
                logger.warning(f"Plugin {plugin_id} missing credentials: {missing_creds}")
                config.last_error = f"Missing credentials: {', '.join(missing_creds)}"
                config.state = PluginState.ERROR
                self._save_configs()
                return False
            
            # Update settings
            config.settings.update(settings)
            config.configured_at = datetime.now().isoformat()
            config.state = PluginState.CONFIGURED
            config.last_error = None
            
            self._save_configs()
            
            logger.info(f"Plugin {plugin_id} configured successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to configure plugin {plugin_id}: {e}")
            return False
    
    async def _check_missing_credentials(self, plugin_id: str) -> List[str]:
        """Check which required credentials are missing"""
        if plugin_id not in self.configs:
            return []
        
        config = self.configs[plugin_id]
        missing = []
        
        for cred_name in config.required_credentials:
            value = await self.credential_manager.get_credential(plugin_id, cred_name)
            if not value:
                missing.append(cred_name)
        
        return missing
    
    async def enable_plugin(self, plugin_id: str) -> bool:
        """
        Enable a plugin
        
        Args:
            plugin_id: Unique plugin identifier
            
        Returns:
            True if enabled successfully
        """
        try:
            if plugin_id not in self.configs:
                logger.error(f"Plugin {plugin_id} not installed")
                return False
            
            config = self.configs[plugin_id]
            
            # Check if configured
            if config.state not in [PluginState.CONFIGURED, PluginState.DISABLED]:
                logger.error(f"Plugin {plugin_id} must be configured before enabling")
                return False
            
            # Check dependencies
            unmet_deps = await self._check_unmet_dependencies(plugin_id)
            if unmet_deps:
                logger.error(f"Plugin {plugin_id} has unmet dependencies: {unmet_deps}")
                config.last_error = f"Unmet dependencies: {', '.join(unmet_deps)}"
                config.state = PluginState.ERROR
                self._save_configs()
                return False
            
            # Enable plugin
            config.state = PluginState.ENABLED
            config.last_enabled = datetime.now().isoformat()
            config.last_error = None
            
            self._save_configs()
            
            logger.info(f"Plugin {plugin_id} enabled successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to enable plugin {plugin_id}: {e}")
            return False
    
    async def disable_plugin(self, plugin_id: str) -> bool:
        """
        Disable a plugin
        
        Args:
            plugin_id: Unique plugin identifier
            
        Returns:
            True if disabled successfully
        """
        try:
            if plugin_id not in self.configs:
                logger.error(f"Plugin {plugin_id} not installed")
                return False
            
            config = self.configs[plugin_id]
            config.state = PluginState.DISABLED
            config.last_disabled = datetime.now().isoformat()
            
            self._save_configs()
            
            logger.info(f"Plugin {plugin_id} disabled successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to disable plugin {plugin_id}: {e}")
            return False
    
    async def _check_unmet_dependencies(self, plugin_id: str) -> List[str]:
        """Check which plugin dependencies are not met"""
        if plugin_id not in self.configs:
            return []
        
        config = self.configs[plugin_id]
        unmet = []
        
        for dep_id in config.dependencies:
            if dep_id not in self.configs:
                unmet.append(f"{dep_id} (not installed)")
            elif self.configs[dep_id].state != PluginState.ENABLED:
                unmet.append(f"{dep_id} (not enabled)")
        
        return unmet
    
    async def update_plugin(
        self,
        plugin_id: str,
        new_version: str,
        metadata: Dict[str, Any]
    ) -> bool:
        """
        Update a plugin to a new version
        
        Args:
            plugin_id: Unique plugin identifier
            new_version: New version to update to
            metadata: Updated plugin metadata
            
        Returns:
            True if updated successfully
        """
        try:
            if plugin_id not in self.configs:
                logger.error(f"Plugin {plugin_id} not installed")
                return False
            
            config = self.configs[plugin_id]
            old_version = config.version
            
            logger.info(f"Updating plugin {plugin_id} from {old_version} to {new_version}")
            
            # Mark as updating
            old_state = config.state
            config.state = PluginState.UPDATING
            self._save_configs()
            
            try:
                # Update version and metadata
                config.version = new_version
                config.required_credentials = metadata.get('requirements', {}).get('credentials', [])
                config.dependencies = metadata.get('requirements', {}).get('plugins', [])
                
                # Restore previous state
                config.state = old_state
                self._save_configs()
                
                logger.info(f"Plugin {plugin_id} updated successfully to {new_version}")
                return True
                
            except Exception as e:
                # Restore old state on failure
                config.state = old_state
                config.last_error = str(e)
                self._save_configs()
                raise
            
        except Exception as e:
            logger.error(f"Failed to update plugin {plugin_id}: {e}")
            return False
    
    def get_plugin_config(self, plugin_id: str) -> Optional[PluginConfig]:
        """Get configuration for a plugin"""
        return self.configs.get(plugin_id)
    
    def get_all_configs(self) -> Dict[str, PluginConfig]:
        """Get all plugin configurations"""
        return self.configs.copy()
    
    def get_enabled_plugins(self) -> List[str]:
        """Get list of enabled plugin IDs"""
        return [
            plugin_id for plugin_id, config in self.configs.items()
            if config.state == PluginState.ENABLED
        ]
    
    def resolve_dependencies(self, plugin_ids: List[str]) -> List[str]:
        """
        Resolve plugin dependencies and return sorted list
        
        Args:
            plugin_ids: List of plugin IDs to resolve
            
        Returns:
            Sorted list with dependencies first
        """
        resolved = []
        seen = set()
        
        def resolve(plugin_id: str):
            if plugin_id in seen:
                return
            if plugin_id not in self.configs:
                logger.warning(f"Dependency not found: {plugin_id}")
                return
            
            seen.add(plugin_id)
            config = self.configs[plugin_id]
            
            # Resolve dependencies first
            for dep_id in config.dependencies:
                resolve(dep_id)
            
            resolved.append(plugin_id)
        
        for plugin_id in plugin_ids:
            resolve(plugin_id)
        
        return resolved
    
    async def validate_plugin(self, plugin_id: str) -> Dict[str, Any]:
        """
        Validate plugin configuration and readiness
        
        Returns:
            Validation results with status and issues
        """
        if plugin_id not in self.configs:
            return {
                'valid': False,
                'issues': ['Plugin not installed']
            }
        
        config = self.configs[plugin_id]
        issues = []
        
        # Check credentials
        missing_creds = await self._check_missing_credentials(plugin_id)
        if missing_creds:
            issues.append(f"Missing credentials: {', '.join(missing_creds)}")
        
        # Check dependencies
        unmet_deps = await self._check_unmet_dependencies(plugin_id)
        if unmet_deps:
            issues.append(f"Unmet dependencies: {', '.join(unmet_deps)}")
        
        # Check state
        if config.state == PluginState.ERROR:
            issues.append(f"Plugin in error state: {config.last_error}")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'state': config.state.value,
            'version': config.version
        }
