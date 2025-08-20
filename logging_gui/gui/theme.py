# E:\projectFiles\programming\.gemini-cli\glen_prototype\src\utils\logging_gui\gui\theme.py
"""
# 로깅 GUI의 테마 로딩 및 관리 모듈입니다.
# Theme loading and management module for the logging GUI.

# 이 모듈은 'themes' 디렉토리에서 동적으로 테마 파일을 찾아 로드합니다.
# 각 테마 파일은 'Theme'라는 이름의 클래스를 포함해야 합니다.
# This module dynamically finds and loads theme files from the 'themes' directory.
# Each theme file is expected to contain a class named 'Theme'.
"""

import os
import importlib.util
from pathlib import Path

# 기본 테마 클래스를 로드하기 위한 초기화
# Initialization to load the default theme class
try:
    from .themes.dark_theme import Theme as DefaultTheme
except ImportError:
    # themes/default.py가 없는 경우를 대비한 폴백(Fallback)
    # Fallback in case themes/default.py is missing
    class DefaultTheme:
        BG_COLOR = "#1C1C1C"
        WIDGET_BG_COLOR = "#2C2C2C"
        ENTRY_BG_COLOR = "#3C3C3C"
        HOVER_COLOR = "#3E3E3E"
        CLICK_COLOR = "#4A4A4A"
        INSERT_CURSOR_COLOR = "#E0E0E0"
        BUTTON_BORDER_COLOR = "#555555"
        LOG_AREA_BG_COLOR = "#121212"
        HIGHLIGHT_BG_COLOR = "#5D5D9A"
        HIGHLIGHT_FG_COLOR = "#FFFFFF"
        TEXT_COLOR = "#E0E0E0"
        DISABLED_TEXT_COLOR = "#7f8c8d"
        ACCENT_COLOR = "#FFD700"
        LINK_COLOR = "#87CEEB"
        DROPDOWN_BG_COLOR = "#2C2C2C"
        DROPDOWN_BORDER_COLOR = "#FFD700"
        DROPDOWN_HOVER_BG_COLOR = "#008CDD"
        FILTER_BUTTON_BG_COLOR = "#2C2C2C"
        FILTER_BUTTON_FG_COLOR = "#E0E0E0"
        FILTER_BUTTON_HOVER_BG_COLOR = "#3E3E3E"
        FILTER_BUTTON_ACTIVE_BG_COLOR = "#4A4A4A"
        COMMAND_BUTTON_HOVER_FG_COLOR = "#FFFFFF"
        SUCCESS_COLOR = "#4CAF50"
        SUCCESS_HOVER_COLOR = "#66BB6A"
        WARNING_COLOR = "#FFC107"
        WARNING_HOVER_COLOR = "#FFD54F"
        RESET_BUTTON_COLOR = "#FFC107"
        RESET_BUTTON_HOVER_COLOR = "#FFD54F"
        PRIMARY_COLOR = "#007ACC"
        PRIMARY_HOVER_COLOR = "#008CDD"
        SECONDARY_COLOR = "#008080"
        SECONDARY_HOVER_COLOR = "#009999"
        KILL_COLOR = "#D32F2F"
        KILL_HOVER_COLOR = "#E57373"
        LOG_LEVEL_COLORS = {
            "TRACE": "#95a5a6", "DEBUG": "#bdc3c7", "INFO": "#E0E0E0",
            "PROGRESS": "#a29bfe", "WARNING": "#FFC107", "ERROR": "#DC143C",
            "FATAL": "#8B0000", "COMMENT": "#FFD700",
            "ADDED": "#007ACC", "MODIFIED": "#00C3E6", "DELETED": "#D32F2F"
        }
        FONT_FAMILY_UI = "Segoe UI"
        FONT_FAMILY_LOG = "Consolas"
        BUTTON_STYLE = { "fg": "#FFFFFF", "font": (FONT_FAMILY_UI, 10, "bold") }
        DISABLED_BUTTON_STYLE = { "fg": DISABLED_TEXT_COLOR, "bg": "#424242" }


def load_themes():
    """
    # 'themes' 디렉토리에서 모든 테마를 로드합니다.
    # Loads all themes from the 'themes' directory.

    # Returns:
    #     dict: 테마 이름을 키로, 테마 클래스를 값으로 하는 딕셔너리.
    #           (A dictionary with theme names as keys and theme classes as values.)
    """
    themes = {}
    theme_dir = Path(__file__).parent / "themes"
    if not theme_dir.is_dir():
        return {"default": DefaultTheme}

    for theme_file in theme_dir.glob("*.py"):
        if theme_file.stem.startswith("__"):
            continue
        
        theme_name = theme_file.stem
        
        try:
            spec = importlib.util.spec_from_file_location(f"gui.themes.{theme_name}", theme_file)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                # sys.modules[f"gui.themes.{theme_name}"] = module # 이 줄은 필요하지 않을 수 있습니다.
                spec.loader.exec_module(module)
                if hasattr(module, "Theme"):
                    themes[theme_name] = getattr(module, "Theme")
        except Exception as e:
            print(f"Error loading theme '{theme_name}': {e}")

    # 'default' 테마가 항상 목록의 맨 앞에 오도록 보장합니다.
    # Ensure the 'default' theme is always first in the list.
    if "default" in themes:
        default_theme = themes.pop("default")
        return {"default": default_theme, **themes}
    elif DefaultTheme:
        return {"default": DefaultTheme, **themes}

    return themes