#!/usr/bin/env python3
"""Windows AI Entry Point"""
import sys
import os

# Add the application directory to path
if getattr(sys, 'frozen', False):
    application_path = sys._MEIPASS
else:
    application_path = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, application_path)

# Run the simple version
from windows_ai_simple import main

if __name__ == "__main__":
    main()
