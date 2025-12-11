"""
Cloud Plugins for Windows AI
Provides integrations with major cloud platforms
"""

from .azure_functions_plugin import AzureFunctionsPlugin

__all__ = [
    "AzureFunctionsPlugin",
]
