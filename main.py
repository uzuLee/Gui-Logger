# E:\projectFiles\programming\.gemini-cli\glen_prototype\src\utils\logging_gui\main.py
"""
Main entry point for the GLEN Real-Time Log Viewer application.

This script initializes the application environment and launches the GUI.
"""

import tkinter as tk
from .gui.log_display import LogDisplay
from .gui.utils import setup_logging

def main():
    """
    Initializes the application and starts the Tkinter main event loop.
    
    This function performs two primary setup tasks:
    1. Calls `setup_logging()` to configure logging for the application itself.
    2. Creates the main Tkinter window (`root`), instantiates the `LogDisplay`
       widget, and starts the GUI event loop.
    """
    # Configure logging for the application's own operational messages.
    setup_logging()
    
    # Create the main application window.
    root = tk.Tk()
    
    # Instantiate the main application frame.
    app = LogDisplay(master=root)
    
    # Start the Tkinter event loop, which waits for user events.
    root.mainloop()

# Standard Python entry point check.
# Ensures that the `main()` function is called only when the script is executed directly.
if __name__ == "__main__":
    main()

