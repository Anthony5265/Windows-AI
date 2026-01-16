import pytest
from windows_ai.gui.window import MainWindow
from unittest.mock import Mock, patch

class TestGUIIntegration:
    def test_window_creation(self):
        with patch('tkinter.Tk'):
            window = MainWindow()
            assert window is not None
            
    def test_plugin_panel(self):
        with patch('tkinter.Tk'):
            window = MainWindow()
            assert hasattr(window, 'plugin_panel')
            
    def test_chat_panel(self):
        with patch('tkinter.Tk'):
            window = MainWindow()
            assert hasattr(window, 'chat_panel')
