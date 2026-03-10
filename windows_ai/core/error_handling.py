"""
Comprehensive Error Handling and Logging System

Provides structured logging, error tracking, and user-friendly error messages
"""

import logging
import json
import sys
import traceback
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
import threading


class ErrorSeverity(Enum):
    """Error severity levels"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for classification"""
    PLUGIN = "plugin"
    API = "api"
    DATABASE = "database"
    NETWORK = "network"
    CONFIGURATION = "configuration"
    AUTHENTICATION = "authentication"
    SYSTEM = "system"
    UNKNOWN = "unknown"


class StructuredLogger:
    """
    Structured logging with JSON output and context tracking
    
    Provides consistent logging format across the application
    """
    
    def __init__(self, name: str, log_dir: Optional[Path] = None):
        self.name = name
        self.logger = logging.getLogger(name)
        
        # Set up log directory
        if log_dir is None:
            log_dir = Path.home() / ".windows_ai" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        self.log_dir = log_dir
        self.context: Dict[str, Any] = {}
        
        # Thread-local storage for request context
        self.local = threading.local()
        
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Set up log handlers"""
        # Console handler with simple format
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        
        # JSON file handler for structured logs
        json_log_file = self.log_dir / f"{self.name}.json"
        json_handler = logging.FileHandler(json_log_file)
        json_handler.setLevel(logging.DEBUG)
        json_handler.setFormatter(JSONFormatter())
        
        # Text file handler for human-readable logs
        text_log_file = self.log_dir / f"{self.name}.log"
        text_handler = logging.FileHandler(text_log_file)
        text_handler.setLevel(logging.DEBUG)
        text_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s\n'
            'Context: %(context)s\n'
            '%(exc_text)s'
        )
        text_handler.setFormatter(text_formatter)
        
        # Add handlers
        self.logger.addHandler(console_handler)
        self.logger.addHandler(json_handler)
        self.logger.addHandler(text_handler)
        
        self.logger.setLevel(logging.DEBUG)
    
    def set_context(self, **kwargs):
        """Set persistent context for all log messages"""
        self.context.update(kwargs)
    
    def clear_context(self):
        """Clear persistent context"""
        self.context.clear()
    
    def set_request_context(self, **kwargs):
        """Set context for current request/thread"""
        if not hasattr(self.local, 'context'):
            self.local.context = {}
        self.local.context.update(kwargs)
    
    def clear_request_context(self):
        """Clear request/thread context"""
        if hasattr(self.local, 'context'):
            self.local.context.clear()
    
    def _get_full_context(self) -> Dict[str, Any]:
        """Get combined context from persistent and thread-local"""
        full_context = self.context.copy()
        if hasattr(self.local, 'context'):
            full_context.update(self.local.context)
        return full_context
    
    def debug(self, message: str, **kwargs):
        """Log debug message"""
        extra = {'context': {**self._get_full_context(), **kwargs}}
        self.logger.debug(message, extra=extra)
    
    def info(self, message: str, **kwargs):
        """Log info message"""
        extra = {'context': {**self._get_full_context(), **kwargs}}
        self.logger.info(message, extra=extra)
    
    def warning(self, message: str, **kwargs):
        """Log warning message"""
        extra = {'context': {**self._get_full_context(), **kwargs}}
        self.logger.warning(message, extra=extra)
    
    def error(self, message: str, exc_info: bool = False, **kwargs):
        """Log error message"""
        extra = {'context': {**self._get_full_context(), **kwargs}}
        self.logger.error(message, exc_info=exc_info, extra=extra)
    
    def critical(self, message: str, exc_info: bool = False, **kwargs):
        """Log critical message"""
        extra = {'context': {**self._get_full_context(), **kwargs}}
        self.logger.critical(message, exc_info=exc_info, extra=extra)
    
    def exception(self, message: str, **kwargs):
        """Log exception with traceback"""
        extra = {'context': {**self._get_full_context(), **kwargs}}
        self.logger.exception(message, extra=extra)


class JSONFormatter(logging.Formatter):
    """Custom formatter for JSON log output"""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add context if available
        if hasattr(record, 'context'):
            log_data['context'] = record.context
        
        # Add exception info if available
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }
        
        return json.dumps(log_data)


class ErrorHandler:
    """
    Centralized error handling with user-friendly messages
    
    Translates technical errors into actionable user messages
    """
    
    def __init__(self, logger: StructuredLogger):
        self.logger = logger
        self.error_messages: Dict[str, str] = self._init_error_messages()
    
    def _init_error_messages(self) -> Dict[str, str]:
        """Initialize user-friendly error messages"""
        return {
            # Plugin errors
            'plugin_not_found': "Plugin '{plugin_id}' not found. Please check the plugin name and try again.",
            'plugin_load_failed': "Failed to load plugin '{plugin_id}'. Error: {error}",
            'plugin_missing_dependency': "Plugin '{plugin_id}' requires '{dependency}' which is not installed.",
            'plugin_invalid_config': "Invalid configuration for plugin '{plugin_id}'. Please check your settings.",
            
            # API errors
            'api_key_missing': "API key not found for '{service}'. Please add your API key in Settings.",
            'api_key_invalid': "API key for '{service}' is invalid. Please check your key and try again.",
            'api_rate_limit': "Rate limit exceeded for '{service}'. Please try again later.",
            'api_network_error': "Network error connecting to '{service}'. Please check your internet connection.",
            'api_timeout': "Request to '{service}' timed out. Please try again.",
            
            # Database errors
            'database_connection_failed': "Failed to connect to database. Please restart the application.",
            'database_query_failed': "Database operation failed: {error}",
            'database_corruption': "Database corruption detected. Please run repair tool.",
            
            # Configuration errors
            'config_missing': "Configuration file not found. Running first-time setup...",
            'config_invalid': "Invalid configuration: {error}. Using defaults.",
            'config_permission_denied': "Permission denied accessing configuration. Please check file permissions.",
            
            # Authentication errors
            'auth_failed': "Authentication failed. Please check your credentials.",
            'auth_expired': "Your session has expired. Please sign in again.",
            'auth_insufficient_permissions': "You don't have permission to perform this action.",
            
            # System errors
            'disk_space_low': "Low disk space. Please free up space and try again.",
            'memory_error': "Insufficient memory. Please close other applications and try again.",
            'system_error': "System error occurred: {error}. Please contact support if this persists.",
        }
    
    def handle_error(
        self,
        error: Exception,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        context: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Handle an error and return structured error information
        
        Args:
            error: The exception that occurred
            category: Category of error
            severity: Severity level
            context: Additional context information
            user_message: Override user-friendly message
            
        Returns:
            Dict with error details and user message
        """
        # Log the error
        log_method = getattr(self.logger, severity.value)
        log_method(
            f"{category.value.upper()} error: {str(error)}",
            exc_info=True,
            category=category.value,
            **(context or {})
        )
        
        # Determine error code
        error_code = f"{category.value}_{error.__class__.__name__}".lower()
        
        # Get user-friendly message
        if user_message is None:
            user_message = self._get_user_message(error, category, context)
        
        # Build error response
        error_info = {
            'error_code': error_code,
            'category': category.value,
            'severity': severity.value,
            'message': user_message,
            'technical_details': str(error),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Add context if provided
        if context:
            error_info['context'] = context
        
        # Add traceback in debug mode
        if self.logger.logger.level <= logging.DEBUG:
            error_info['traceback'] = traceback.format_exc()
        
        return error_info
    
    def _get_user_message(
        self,
        error: Exception,
        category: ErrorCategory,
        context: Optional[Dict[str, Any]]
    ) -> str:
        """Get user-friendly error message"""
        error_type = error.__class__.__name__
        
        # Check for specific error patterns
        error_str = str(error).lower()
        
        # API errors
        if 'api key' in error_str or 'unauthorized' in error_str:
            service = context.get('service', 'service') if context else 'service'
            return self.error_messages['api_key_invalid'].format(service=service)
        
        if 'rate limit' in error_str or '429' in error_str:
            service = context.get('service', 'service') if context else 'service'
            return self.error_messages['api_rate_limit'].format(service=service)
        
        if 'timeout' in error_str or 'timed out' in error_str:
            service = context.get('service', 'service') if context else 'service'
            return self.error_messages['api_timeout'].format(service=service)
        
        if 'network' in error_str or 'connection' in error_str:
            service = context.get('service', 'service') if context else 'service'
            return self.error_messages['api_network_error'].format(service=service)
        
        # Database errors
        if category == ErrorCategory.DATABASE:
            return self.error_messages['database_query_failed'].format(error=str(error))
        
        # Plugin errors
        if category == ErrorCategory.PLUGIN:
            plugin_id = context.get('plugin_id', 'unknown') if context else 'unknown'
            return self.error_messages['plugin_load_failed'].format(
                plugin_id=plugin_id,
                error=str(error)
            )
        
        # Default message
        return self.error_messages['system_error'].format(error=str(error))
    
    def wrap_async(self, func):
        """Decorator to wrap async functions with error handling"""
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                error_info = self.handle_error(
                    e,
                    context={'function': func.__name__}
                )
                raise ErrorWithContext(error_info) from e
        return wrapper
    
    def wrap_sync(self, func):
        """Decorator to wrap sync functions with error handling"""
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_info = self.handle_error(
                    e,
                    context={'function': func.__name__}
                )
                raise ErrorWithContext(error_info) from e
        return wrapper


class ErrorWithContext(Exception):
    """Exception that includes structured error information"""
    
    def __init__(self, error_info: Dict[str, Any]):
        self.error_info = error_info
        super().__init__(error_info['message'])


class HealthChecker:
    """
    System health monitoring and diagnostics
    
    Checks various system components and reports status
    """
    
    def __init__(self, logger: StructuredLogger):
        self.logger = logger
    
    async def check_all(self) -> Dict[str, Any]:
        """Run all health checks"""
        checks = {
            'database': await self.check_database(),
            'disk_space': await self.check_disk_space(),
            'memory': await self.check_memory(),
            'api_connectivity': await self.check_api_connectivity(),
            'plugins': await self.check_plugins()
        }
        
        # Overall status
        all_healthy = all(check['status'] == 'healthy' for check in checks.values())
        
        return {
            'status': 'healthy' if all_healthy else 'unhealthy',
            'timestamp': datetime.utcnow().isoformat(),
            'checks': checks
        }
    
    async def check_database(self) -> Dict[str, Any]:
        """Check database connectivity and integrity"""
        try:
            from windows_ai.core.app_database import ApplicationDatabase
            from pathlib import Path
            
            db_path = Path.home() / ".windows_ai" / "windows_ai.db"
            db = ApplicationDatabase(str(db_path))
            
            # Try a simple query
            users = db.list_users(limit=1)
            
            return {
                'status': 'healthy',
                'message': 'Database is accessible'
            }
        except Exception as e:
            self.logger.error(f"Database health check failed: {e}")
            return {
                'status': 'unhealthy',
                'message': f'Database error: {str(e)}'
            }
    
    async def check_disk_space(self) -> Dict[str, Any]:
        """Check available disk space"""
        try:
            import shutil
            from pathlib import Path
            
            home = Path.home()
            stat = shutil.disk_usage(home)
            free_gb = stat.free / (1024**3)
            
            if free_gb < 1.0:
                return {
                    'status': 'unhealthy',
                    'message': f'Low disk space: {free_gb:.2f} GB free'
                }
            elif free_gb < 5.0:
                return {
                    'status': 'warning',
                    'message': f'Disk space low: {free_gb:.2f} GB free'
                }
            else:
                return {
                    'status': 'healthy',
                    'message': f'Sufficient disk space: {free_gb:.2f} GB free'
                }
        except Exception as e:
            self.logger.error(f"Disk space check failed: {e}")
            return {
                'status': 'unknown',
                'message': f'Could not check disk space: {str(e)}'
            }
    
    async def check_memory(self) -> Dict[str, Any]:
        """Check available memory"""
        try:
            import psutil
            
            memory = psutil.virtual_memory()
            available_gb = memory.available / (1024**3)
            percent_used = memory.percent
            
            if percent_used > 90:
                return {
                    'status': 'unhealthy',
                    'message': f'High memory usage: {percent_used:.1f}% used'
                }
            elif percent_used > 80:
                return {
                    'status': 'warning',
                    'message': f'Memory usage high: {percent_used:.1f}% used'
                }
            else:
                return {
                    'status': 'healthy',
                    'message': f'Memory usage normal: {percent_used:.1f}% used'
                }
        except ImportError:
            return {
                'status': 'unknown',
                'message': 'psutil not installed, cannot check memory'
            }
        except Exception as e:
            self.logger.error(f"Memory check failed: {e}")
            return {
                'status': 'unknown',
                'message': f'Could not check memory: {str(e)}'
            }
    
    async def check_api_connectivity(self) -> Dict[str, Any]:
        """Check connectivity to API services"""
        try:
            import aiohttp
            
            # Test connectivity with a simple DNS resolution
            async with aiohttp.ClientSession() as session:
                # Try to resolve a common API domain
                try:
                    async with session.get(
                        'https://www.google.com',
                        timeout=aiohttp.ClientTimeout(total=5)
                    ) as resp:
                        if resp.status == 200:
                            return {
                                'status': 'healthy',
                                'message': 'Network connectivity OK'
                            }
                except Exception:
                    pass
            
            return {
                'status': 'unhealthy',
                'message': 'No network connectivity'
            }
        except Exception as e:
            self.logger.error(f"API connectivity check failed: {e}")
            return {
                'status': 'unknown',
                'message': f'Could not check connectivity: {str(e)}'
            }
    
    async def check_plugins(self) -> Dict[str, Any]:
        """Check plugin system status"""
        try:
            # Check if plugins directory exists
            plugins_dir = Path.home() / ".windows_ai" / "plugins"
            
            if not plugins_dir.exists():
                return {
                    'status': 'warning',
                    'message': 'Plugins directory not found'
                }
            
            # Count installed plugins
            plugin_count = len(list(plugins_dir.glob('*')))
            
            return {
                'status': 'healthy',
                'message': f'{plugin_count} plugins installed'
            }
        except Exception as e:
            self.logger.error(f"Plugin check failed: {e}")
            return {
                'status': 'unknown',
                'message': f'Could not check plugins: {str(e)}'
            }


# Global logger instance
_loggers: Dict[str, StructuredLogger] = {}


def get_logger(name: str) -> StructuredLogger:
    """Get or create a logger instance"""
    if name not in _loggers:
        _loggers[name] = StructuredLogger(name)
    return _loggers[name]
