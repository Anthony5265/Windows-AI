"""
Structured Logger - Logging system
"""

import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any


class StructuredLogger:
    """
    Structured Logger logging system
    """
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        self.logger = logging.getLogger("Structured Logger")
        self.logger.setLevel(logging.DEBUG)
        
        # File handler
        log_file = self.log_dir / f"structured_logger.log"
        handler = logging.FileHandler(log_file)
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        self.logger.addHandler(handler)
    
    def log(self, level: str, message: str, **context):
        """Log a message with context"""
        data = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "message": message,
            **context
        }
        
        log_method = getattr(self.logger, level.lower(), self.logger.info)
        log_method(json.dumps(data))
    
    def info(self, message: str, **context):
        """Log info level"""
        self.log("INFO", message, **context)
    
    def error(self, message: str, **context):
        """Log error level"""
        self.log("ERROR", message, **context)
    
    def debug(self, message: str, **context):
        """Log debug level"""
        self.log("DEBUG", message, **context)


if __name__ == "__main__":
    logger = StructuredLogger()
    logger.info("Test message", user="admin", action="test")
    print(f"Logged to: {logger.log_dir}")
