# E:\projectFiles\programming\.gemini-cli\glen_prototype\src\utils\logging_gui\gui\utils.py
"""
Utility functions for the logging GUI application.

This module provides helper functions that support the main application,
starting with logging configuration. This can be expanded to include other
reusable utilities as the application grows.
"""

import os
import sys
import logging
import logging.handlers
from datetime import datetime
from .config import LOG_DIR

def setup_logging():
    """
    Sets up the root logger for the GUI application itself.

    This configures logging to capture the internal events of the GUI, such as
    errors or informational messages, which is distinct from the logs being
    displayed from the subprocess.

    It configures two handlers:
    1. RotatingFileHandler: Saves logs to a file (`glen_log_... .log`) in the
       log directory, automatically rotating files when they reach 10MB.
    2. StreamHandler: Prints log messages to the console (stdout).
    """
    # Define the log file path with a timestamp for uniqueness.
    log_file = os.path.join(LOG_DIR, f"glen_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    
    # Define a consistent format for all log messages.
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
    # --- File Handler Configuration ---
    # This handler writes logs to a file and rotates it when it gets too large.
    file_handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=10*1024*1024, backupCount=5, encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    
    # --- Console Handler Configuration ---
    # This handler prints logs directly to the standard output.
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # --- Configure Root Logger ---
    # Get the root logger and add the configured handlers.
    # All loggers created in the application will inherit this configuration.
    root_logger = logging.getLogger()
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    root_logger.setLevel(logging.INFO) # Set the minimum level of logs to capture.
