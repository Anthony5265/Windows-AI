# XR Integration

The project can optionally interface with XR hardware. The :mod:`xr` package
contains helpers for detecting runtimes and routing spatial input events.

## Spatial UI

Use :func:`xr.load_spatial_ui` to create a gesture and voice controller when
compatible hardware is present. The function automatically checks for an
installed OpenXR or WebXR runtime and returns a
:class:`xr.spatial_ui.GestureVoiceController` instance when one is available.

```python
import xr

controller = xr.load_spatial_ui()
if controller:
    controller.bind_gesture("pinch", on_pinch)
    controller.bind_voice("hello", on_hello)
else:
    # Fall back to traditional input methods
    ...
```

When no XR runtime is detected the function returns ``None`` so applications
can gracefully fall back to standard input handling.
