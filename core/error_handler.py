"""
Centralized error handling and logging for Code Weaver Pro
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, Callable


class ErrorHandler:
    """
    Centralized error handling with logging and UI callbacks
    """

    def __init__(self, log_dir: str, terminal_callback: Optional[Callable] = None):
        """
        Initialize error handler

        Args:
            log_dir: Directory to store log files
            terminal_callback: Optional callback for terminal output
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.terminal_callback = terminal_callback

        # Setup logging
        log_file = self.log_dir / f"code_weaver_pro_{datetime.now().strftime('%Y%m%d')}.log"

        # Configure root logger
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )

        self.logger = logging.getLogger('CodeWeaverPro')

    def info(self, message: str):
        """Log info message"""
        self.logger.info(message)
        if self.terminal_callback:
            self.terminal_callback(message, 'info')

    def success(self, message: str):
        """Log success message"""
        self.logger.info(f"✓ {message}")
        if self.terminal_callback:
            self.terminal_callback(message, 'success')

    def warning(self, message: str):
        """Log warning message"""
        self.logger.warning(message)
        if self.terminal_callback:
            self.terminal_callback(message, 'warning')

    def error(self, message: str, exception: Optional[Exception] = None):
        """Log error message with optional exception"""
        self.logger.error(message)
        if exception:
            self.logger.error(f"Exception: {str(exception)}", exc_info=True)

        if self.terminal_callback:
            self.terminal_callback(message, 'error')

    def debug(self, message: str):
        """Log debug message"""
        self.logger.debug(message)
