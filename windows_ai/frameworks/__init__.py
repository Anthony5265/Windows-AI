"""
Windows AI - Integrated AI Frameworks
Unified interface to all major AI frameworks
"""

from .langchain_integration import LangChainManager
from .llamaindex_integration import LlamaIndexManager
from .crewai_integration import CrewAIManager
from .autogen_integration import AutoGenManager
from .mcp_integration import MCPManager
from .ollama_integration import OllamaManager
from .unified_llm import UnifiedLLMProvider

__all__ = [
    'LangChainManager',
    'LlamaIndexManager',
    'CrewAIManager',
    'AutoGenManager',
    'MCPManager',
    'OllamaManager',
    'UnifiedLLMProvider'
]
