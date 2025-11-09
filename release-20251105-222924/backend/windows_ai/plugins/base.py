"""
Base Plugin Classes

Defines the core plugin architecture for Windows AI.
Developers can extend these classes to create custom plugins.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from enum import Enum
from dataclasses import dataclass, asdict
from datetime import datetime


class PluginType(str, Enum):
    """Types of plugins supported"""
    ACTION = "action"          # AI-powered actions (e.g., summarize, organize)
    TOOL = "tool"             # Tools that extend AI capabilities (e.g., web search)
    INTEGRATION = "integration"  # External service integrations (e.g., GitHub)
    UI = "ui"                 # UI extensions and custom views
    AUTOMATION = "automation"  # Custom automation triggers


@dataclass
class PluginMetadata:
    """Metadata describing a plugin"""
    id: str
    name: str
    description: str
    version: str
    author: str
    plugin_type: PluginType
    enabled: bool = True
    icon: Optional[str] = None
    tags: List[str] = None
    requirements: List[str] = None
    created_at: Optional[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.requirements is None:
            self.requirements = []
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['plugin_type'] = self.plugin_type.value
        return data


class Plugin(ABC):
    """
    Base class for all Windows AI plugins.

    Developers should extend this class and implement the required methods.
    """

    def __init__(self, metadata: PluginMetadata):
        self.metadata = metadata
        self._initialized = False

    @abstractmethod
    async def initialize(self) -> bool:
        """
        Initialize the plugin.
        Called once when the plugin is loaded.

        Returns:
            True if initialization successful, False otherwise
        """
        pass

    @abstractmethod
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute the plugin's main functionality.

        Args:
            **kwargs: Plugin-specific arguments

        Returns:
            Dictionary with execution results
        """
        pass

    async def shutdown(self):
        """
        Clean up plugin resources.
        Called when the plugin is disabled or the system shuts down.
        """
        pass

    def get_schema(self) -> Dict[str, Any]:
        """
        Return JSON schema describing the plugin's parameters.
        Used for validation and UI generation.

        Returns:
            JSON schema dictionary
        """
        return {
            "type": "object",
            "properties": {},
            "required": []
        }


class ActionPlugin(Plugin):
    """
    Base class for Action plugins.

    Action plugins perform AI-powered tasks like summarizing, organizing, etc.
    """

    def __init__(self, metadata: PluginMetadata):
        if metadata.plugin_type != PluginType.ACTION:
            metadata.plugin_type = PluginType.ACTION
        super().__init__(metadata)

    async def initialize(self) -> bool:
        """Default initialization for action plugins"""
        self._initialized = True
        return True

    @abstractmethod
    async def execute(
        self,
        input_data: Any,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute the action.

        Args:
            input_data: The data to process (text, file path, etc.)
            context: Additional context (user info, conversation history, etc.)
            **kwargs: Action-specific parameters

        Returns:
            Dictionary with:
                - success: bool
                - result: Any - The action result
                - message: str - Human-readable message
                - metadata: Dict - Additional metadata
        """
        pass


class ToolPlugin(Plugin):
    """
    Base class for Tool plugins.

    Tool plugins extend the AI's capabilities by providing new functions it can call.
    Examples: web search, code execution, API calls
    """

    def __init__(self, metadata: PluginMetadata):
        if metadata.plugin_type != PluginType.TOOL:
            metadata.plugin_type = PluginType.TOOL
        super().__init__(metadata)

    async def initialize(self) -> bool:
        """Default initialization for tool plugins"""
        self._initialized = True
        return True

    @abstractmethod
    async def execute(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute the tool.

        Args:
            query: The query or command for the tool
            parameters: Tool-specific parameters
            **kwargs: Additional arguments

        Returns:
            Dictionary with tool execution results
        """
        pass

    def get_function_definition(self) -> Dict[str, Any]:
        """
        Return OpenAI function calling format definition.
        This allows the AI to use this tool directly.

        Returns:
            Dictionary in OpenAI function format
        """
        return {
            "name": self.metadata.id,
            "description": self.metadata.description,
            "parameters": self.get_schema()
        }


class IntegrationPlugin(Plugin):
    """
    Base class for Integration plugins.

    Integration plugins connect Windows AI to external services.
    Examples: GitHub, Notion, Calendar, Email
    """

    def __init__(self, metadata: PluginMetadata):
        if metadata.plugin_type != PluginType.INTEGRATION:
            metadata.plugin_type = PluginType.INTEGRATION
        super().__init__(metadata)

    async def initialize(self) -> bool:
        """Default initialization - should be overridden to setup connections"""
        self._initialized = True
        return True

    @abstractmethod
    async def connect(self, credentials: Dict[str, str]) -> bool:
        """
        Connect to the external service.

        Args:
            credentials: Service credentials (API keys, tokens, etc.)

        Returns:
            True if connected successfully
        """
        pass

    @abstractmethod
    async def disconnect(self) -> bool:
        """
        Disconnect from the external service.

        Returns:
            True if disconnected successfully
        """
        pass

    @abstractmethod
    async def execute(
        self,
        action: str,
        parameters: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute an action on the integrated service.

        Args:
            action: The action to perform (e.g., "create_issue", "send_email")
            parameters: Action parameters
            **kwargs: Additional arguments

        Returns:
            Action results
        """
        pass


class AutomationPlugin(Plugin):
    """
    Base class for Automation plugins.

    Automation plugins define custom triggers and actions.
    Examples: Custom file watchers, system event handlers
    """

    def __init__(self, metadata: PluginMetadata):
        if metadata.plugin_type != PluginType.AUTOMATION:
            metadata.plugin_type = PluginType.AUTOMATION
        super().__init__(metadata)

    async def initialize(self) -> bool:
        """Default initialization for automation plugins"""
        self._initialized = True
        return True

    @abstractmethod
    async def execute(
        self,
        trigger: str,
        event_data: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Handle an automation event.

        Args:
            trigger: The trigger type that fired
            event_data: Data about the event
            **kwargs: Additional arguments

        Returns:
            Automation execution results
        """
        pass

    @abstractmethod
    def get_triggers(self) -> List[Dict[str, Any]]:
        """
        Return list of triggers this automation responds to.

        Returns:
            List of trigger definitions
        """
        pass
