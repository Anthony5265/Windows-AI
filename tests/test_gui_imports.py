"""Test GUI module imports for correctness."""

import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestGuiImports:
    """Test that all GUI modules can be imported without errors."""
    
    def test_gui_init_import(self):
        """Test windows_ai.gui.__init__ import."""
        from windows_ai.gui import WindowsAIGUI, main
        assert WindowsAIGUI is not None
        assert main is not None
    
    def test_gui_main_window_import(self):
        """Test windows_ai.gui.main_window import."""
        from windows_ai.gui.main_window import WindowsAIGUI
        assert WindowsAIGUI is not None
    
    def test_gui_core_import(self):
        """Test windows_ai.gui.gui.core import."""
        from windows_ai.gui.gui.core import GuiCore
        assert GuiCore is not None
    
    def test_gui_simple_model_import(self):
        """Test windows_ai.gui.gui.simple_model import."""
        from windows_ai.gui.gui.simple_model import SimpleModel
        assert SimpleModel is not None
    
    def test_circular_import_detection(self):
        """Test that there are no circular imports."""
        # This passes if we can import all modules
        from windows_ai import gui
        assert gui is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
