
import os
import importlib.util
from pathlib import Path
from .config import THEMES_DIR

try:
    # Attempt to import the dark_theme as the default theme.
    # dark_theme을 기본 테마로 임포트 시도합니다.
    from ..themes.dark_theme import Theme as DefaultTheme
except ImportError:
    # Fallback default theme class if the import fails.
    # This ensures the application can run even if theme files are missing.
    # 임포트 실패 시 폴백으로 사용될 기본 테마 클래스입니다.
    # 이를 통해 테마 파일이 없어도 애플리케이션이 실행될 수 있습니다.
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

def load_themes() -> dict:
    """
    # Dynamically loads all theme classes from .py files in the THEMES_DIR.
    # THEMES_DIR에 있는 .py 파일에서 모든 테마 클래스를 동적으로 로드합니다.

    # Returns:
    #     dict: A dictionary mapping theme names to their respective Theme classes.
    #           (테마 이름을 해당 테마 클래스에 매핑하는 딕셔너리)
    """
    themes = {}
    theme_dir = Path(THEMES_DIR)
    if not theme_dir.is_dir():
        return {"dark_theme": DefaultTheme}

    for theme_file in theme_dir.glob("*.py"):
        if theme_file.stem.startswith("__"):
            continue
        
        theme_name = theme_file.stem
        
        try:
            spec = importlib.util.spec_from_file_location(f"themes.{theme_name}", theme_file)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                if hasattr(module, "Theme"):
                    themes[theme_name] = getattr(module, "Theme")
        except Exception as e:
            print(f"Error loading theme '{theme_name}': {e}")

    # Ensure there is always a default theme, prioritizing 'dark_theme' if it exists.
    # 'dark_theme'이 존재하면 우선적으로 사용하되, 항상 기본 테마가 있도록 보장합니다.
    if "dark_theme" in themes:
        default = themes.pop("dark_theme")
        return {"dark_theme": default, **themes}
    elif DefaultTheme:
        return {"dark_theme": DefaultTheme, **themes}

    return themes
