"""Re-export gui modules for backwards compatibility."""

# Import from control_center for ChatGUI/DashboardManager
from control_center.gui import ChatGUI, DashboardManager  # noqa: F401

# Make core submodule available
from gui import core  # noqa: F401
