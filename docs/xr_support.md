# XR Support

The project ships with experimental support for extended reality (XR)
hardware.  Detection is lightweight and falls back gracefully so tests can
run on machines without any special equipment.

## Hardware detection

`windows_ai.system_info.detect_system()` now includes two additional
fields: `xr_capable` and `xr_runtime`.  The values indicate whether an
OpenXR or WebXR runtime could be imported and which one was used.  When no
runtime is present the system reports `xr_capable` as `false` and
`xr_runtime` as `null`.

## Input manager

The `xr.input_manager.InputManager` class provides a tiny abstraction for
mapping gestures and voice commands to callbacks.  Applications can
register handlers and feed hardware events into the manager without
worrying about the specific device APIs.

```python
from xr.input_manager import InputManager

manager = InputManager()
manager.register_gesture("pinch", on_pinch)
manager.register_voice_command("hello", on_hello)
```

## Setup

Install Python bindings for your XR runtime of choice:

```bash
pip install openxr  # or webxr
```

If no bindings are installed the system simply reports that XR hardware is
not available.
