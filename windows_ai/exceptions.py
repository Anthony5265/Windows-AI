"""Custom exception classes for Windows-AI security and resource management.

This module defines custom exceptions used throughout the application for
security violations, resource limit enforcement, and other error conditions.
"""


class SecurityError(Exception):
    """Raised when a security violation is detected.
    
    Examples:
        - Command injection attempts
        - Path traversal attempts
        - Import restrictions violations
        - Network access violations
        - Privilege escalation attempts
        - Signature verification failures
    """
    pass


class ResourceError(Exception):
    """Raised when resource limits are exceeded or violated.
    
    Examples:
        - CPU usage exceeds quota
        - Memory usage exceeds quota
        - Disk usage exceeds quota
        - Execution time exceeds timeout
        - Too many concurrent operations
    """
    pass


class ValidationError(Exception):
    """Raised when input validation fails.
    
    Examples:
        - Invalid task structure
        - Missing required parameters
        - Invalid parameter types
        - Out-of-range values
    """
    pass
