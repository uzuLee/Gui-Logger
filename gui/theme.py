# E:\projectFiles\programming\.gemini-cli\glen_prototype\src\utils\logging_gui\gui\theme.py
"""
Defines the visual theme for the GLEN Log Viewer application.

This module centralizes all styling-related constants, including colors,
fonts, and widget style configurations. Using a theme class makes it easy
to maintain a consistent look and feel across the entire application and
allows for easier future redesigns.
"""

class Theme:
    """
    A class that acts as a namespace for all theme-related constants.
    """
    # --- Base Color Palette ---
    # These colors form the fundamental look of the application.
    BG_COLOR = "#1C1C1C"            # Main background color for windows and frames.
    WIDGET_BG_COLOR = "#2C2C2C"      # Background color for widgets like buttons and listboxes.
    ENTRY_BG_COLOR = "#3C3C3C"       # Background for text entry fields.
    HOVER_COLOR = "#3E3E3E"          # Hover color for interactive elements.
    TEXT_COLOR = "#E0E0E0"           # Default text color.
    DISABLED_TEXT_COLOR = "#7f8c8d"  # Text color for disabled widgets.
    ACCENT_COLOR = "#FFD700"         # Accent color for highlights, selections, and important info (Gold).
    LINK_COLOR = "#87CEEB"           # Color for clickable hyperlinks (Sky Blue).
    
    # --- State & Action Colors ---
    # These colors provide semantic feedback to the user for various actions.
    SUCCESS_COLOR = "#4CAF50"         # Color for success states or 'Run' button (Green).
    SUCCESS_HOVER_COLOR = "#66BB6A"   # Hover variant for success color.
    WARNING_COLOR = "#FFC107"         # Color for warnings or 'Pause' button (Amber).
    WARNING_HOVER_COLOR = "#FFD54F"   # Hover variant for warning color.
    PRIMARY_COLOR = "#007ACC"         # Primary action color (e.g., 'Open Folder') (Blue).
    PRIMARY_HOVER_COLOR = "#008CDD"   # Hover variant for primary color.
    SECONDARY_COLOR = "#008080"       # Secondary action color (e.g., 'Open File') (Teal).
    SECONDARY_HOVER_COLOR = "#009999" # Hover variant for secondary color.
    DANGER_COLOR = "#DC143C"          # Color for errors or dangerous actions (Crimson).
    KILL_COLOR = "#D32F2F"           # Specific color for the 'Kill' button (Red).
    KILL_HOVER_COLOR = "#E57373"     # Hover variant for the kill color.
    
    # --- Log Level Specific Colors ---
    # A dictionary mapping log level names to their display colors in the log view.
    LOG_LEVEL_COLORS = {
        "TRACE": "#95a5a6",      # Light grey for fine-grained details.
        "DEBUG": "#bdc3c7",      # White-grey for debugging information.
        "INFO": TEXT_COLOR,       # Default text color for informational messages.
        "PROGRESS": "#a29bfe",   # A soft purple for progress bar updates.
        "WARNING": WARNING_COLOR, # Amber for potential issues.
        "ERROR": DANGER_COLOR,    # Crimson for errors.
        "FATAL": "#8B0000",      # Dark red for critical, application-ending errors.
        "COMMENT": ACCENT_COLOR,  # Gold for user-added comments.
        "SYSTEM": "#8e44ad",      # Purple for system-level messages.
        "ADDED": SUCCESS_COLOR,   # Green for newly added (unsaved) logs.
        "MODIFIED": PRIMARY_COLOR,# Blue for modified (unsaved) logs.
        "DELETED": DANGER_COLOR   # Crimson for logs marked for deletion.
    }

    # --- Fonts ---
    # Defines the font families used in the application.
    FONT_FAMILY_UI = "Segoe UI"      # A clean, modern font for UI elements like buttons and labels.
    FONT_FAMILY_LOG = "Consolas"    # A monospaced font for the log display area for better readability.
    
    # --- Widget Style Dictionaries ---
    # Pre-configured style dictionaries to apply common properties to widgets easily.
    
    # Default style for standard buttons.
    BUTTON_STYLE = {
        "fg": "white", 
        "font": (FONT_FAMILY_UI, 10, "bold"), 
        "relief": "flat", 
        "padx": 10, "pady": 5, 
        "width": 12, 
        "borderwidth": 0, 
        "activeforeground": "white"
    }
    
    # Style for buttons when they are in a disabled state.
    DISABLED_BUTTON_STYLE = {
        "fg": DISABLED_TEXT_COLOR, 
        "bg": "#555555", 
        "font": (FONT_FAMILY_UI, 10, "bold"), 
        "relief": "flat", 
        "padx": 10, "pady": 5, 
        "width": 12, 
        "borderwidth": 0
    }
