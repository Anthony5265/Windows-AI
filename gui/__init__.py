# Make 'gui' a proper package so that 'from gui.core import GuiCore' resolves to the package
# and not the top-level gui.py module.
from .core import GuiCore  # re-export for convenience
