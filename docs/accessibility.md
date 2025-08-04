# Accessibility Features

Windows-AI provides basic hooks that allow the user interface to adapt to
system-level accessibility preferences.

## System Information

`windows_ai.system_info.detect_system()` now reports whether a screen reader or
high-contrast theme is enabled in the host operating system.  The function
falls back to sensible defaults when the platform does not expose the required
APIs.

## Themes

`ui.themes.ThemeManager` exposes an ``apply_accessibility`` helper which toggles
screen reader descriptions and selects a bundled high-contrast theme.  Themes
may include human friendly descriptions for UI elements so screen readers can
describe controls to the user.

## Control Center

`control_center.chat_ui.ChatUI` provides hooks for registering voice control
handlers and alternative input devices.  Voice commands can be processed or
translated into chat messages, and accessibility devices can inject text directly
into the chat interface.

These features form the foundation for broader accessibility support and are
intended to be extended by downstream applications.
