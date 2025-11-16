# Registry Manager

Windows OS integration plugin for registry manager operations.

## Features

- read
- write
- delete
- monitor

## Usage

```python
from plugins.windows_integration.registry_manager import RegistryManager

# Initialize
manager = RegistryManager()

# Check availability
if manager.is_available():
    # Execute operations
    result = manager.execute("operation_name", param1="value1")
    print(result)
```

## Requirements

- Windows 10 or later
- Administrator privileges: Yes

## APIs Used

- HKLM
- HKCU
- HKCR
- HKU
- HKCC
