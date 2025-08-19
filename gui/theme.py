# E:\projectFiles\programming\.gemini-cli\glen_prototype\src\utils\logging_gui\gui\theme.py
"""
# 로그 뷰어 애플리케이션의 시각적 테마를 정의합니다.
# Defines the visual theme for the Log Viewer application.

# 이 모듈은 색상, 글꼴, 위젯 스타일 설정을 포함한 모든 스타일 관련 상수를 중앙에서 관리합니다.
# 테마 클래스를 사용하면 애플리케이션 전체에 일관된 디자인을 쉽게 유지하고,
# 향후 디자인 변경을 용이하게 할 수 있습니다.
# This module centralizes all styling-related constants, including colors,
# fonts, and widget style configurations. Using a theme class makes it easy
# to maintain a consistent look and feel across the entire application and
# allows for easier future redesigns.
"""

class Theme:
    """
    # 모든 테마 관련 상수를 위한 네임스페이스 역할을 하는 클래스입니다.
    # A class that acts as a namespace for all theme-related constants.
    """
    # --- 기본 색상 팔레트 (Base Color Palette) ---
    BG_COLOR = "#1C1C1C"            # 창과 프레임의 주 배경색 (Main background color for windows and frames)
    WIDGET_BG_COLOR = "#2C2C2C"      # 버튼, 리스트박스 등 위젯의 배경색 (Background color for widgets like buttons and listboxes)
    ENTRY_BG_COLOR = "#3C3C3C"       # 텍스트 입력 필드의 배경색 (Background for text entry fields)
    HOVER_COLOR = "#3E3E3E"          # 상호작용 요소의 호버 색상 (Hover color for interactive elements)
    CLICK_COLOR = "#4A4A4A"          # 위젯의 활성(클릭) 상태 색상 (Color for the active (clicked) state of a widget)
    INSERT_CURSOR_COLOR = "#E0E0E0"   # 텍스트 삽입 커서(캐럿) 색상 (Color for the text insertion cursor (caret))

    # --- 영역별 색상 (Area Specific Colors) ---
    LOG_AREA_BG_COLOR = "#121212"     # 메인 로그 뷰잉 영역의 배경색 (Background color for the main log viewing area)
    HIGHLIGHT_BG_COLOR = "#5D5D9A"    # 선택/하이라이트된 로그 라인의 배경색 (Background color for a selected/highlighted log line)
    HIGHLIGHT_FG_COLOR = "#FFFFFF"    # 선택/하이라이트된 로그 라인의 전경(텍스트)색 (Foreground (text) color for a selected/highlighted log line)
    TEXT_COLOR = "#E0E0E0"           # 기본 텍스트 색상 (Default text color)
    DISABLED_TEXT_COLOR = "#7f8c8d"  # 비활성화된 위젯의 텍스트 색상 (Text color for disabled widgets)
    ACCENT_COLOR = "#FFD700"         # 하이라이트, 선택, 중요 정보용 강조 색상 (금색) (Accent color for highlights, selections, and important info (Gold))
    LINK_COLOR = "#87CEEB"           # 클릭 가능한 하이퍼링크 색상 (하늘색) (Color for clickable hyperlinks (Sky Blue))
    
    # --- 드롭다운 메뉴 색상 (Dropdown Specific Colors) ---
    DROPDOWN_BG_COLOR = "#2C2C2C"      # 필터 드롭다운 메뉴의 배경색 (Background color for the filter dropdown menu)
    DROPDOWN_BORDER_COLOR = "#FFD700"  # 필터 드롭다운 메뉴의 테두리 색상 (Border color for the filter dropdown menu)
    DROPDOWN_HOVER_BG_COLOR = "#008CDD" # 드롭다운 내 항목의 호버 색상 (Hover color for items within the dropdown)

    # --- 필터 버튼 색상 (Filter Button Specific Colors) ---
    FILTER_BUTTON_BG_COLOR = "#2C2C2C" # 메인 필터 버튼의 배경색 (Background color for the main filter button)
    FILTER_BUTTON_FG_COLOR = "#E0E0E0" # 메인 필터 버튼의 전경(텍스트)색 (Foreground (text) color for the main filter button)
    FILTER_BUTTON_HOVER_BG_COLOR = "#3E3E3E" # 메인 필터 버튼의 호버 색상 (Hover color for the main filter button)
    FILTER_BUTTON_ACTIVE_BG_COLOR = "#4A4A4A" # 메인 필터 버튼의 활성(클릭) 색상 (Active (clicked) color for the main filter button)

    # --- 커맨드 입력 색상 (Command Input Specific Colors) ---
    COMMAND_BUTTON_HOVER_FG_COLOR = "#FFFFFF" # 커맨드/전송 버튼의 호버 텍스트 색상 (Hover text color for the command/send button)
    
    # --- 상태 및 액션 색상 (State & Action Colors) ---
    SUCCESS_COLOR = "#4CAF50"         # 성공 상태 또는 'Run' 버튼 색상 (초록색) (Color for success states or 'Run' button (Green))
    SUCCESS_HOVER_COLOR = "#66BB6A"   # 성공 색상의 호버 변형 (Hover variant for success color)
    WARNING_COLOR = "#FFC107"         # 경고 또는 'Pause' 버튼 색상 (호박색) (Color for warnings or 'Pause' button (Amber))
    WARNING_HOVER_COLOR = "#FFD54F"   # 경고 색상의 호버 변형 (Hover variant for warning color)
    PRIMARY_COLOR = "#007ACC"         # 주요 액션 색상 (예: 'Open Folder') (파란색) (Primary action color (e.g., 'Open Folder') (Blue))
    PRIMARY_HOVER_COLOR = "#008CDD"   # 주요 색상의 호버 변형 (Hover variant for primary color)
    SECONDARY_COLOR = "#008080"       # 보조 액션 색상 (예: 'Open File') (청록색) (Secondary action color (e.g., 'Open File') (Teal))
    SECONDARY_HOVER_COLOR = "#009999" # 보조 색상의 호버 변형 (Hover variant for secondary color)
    DANGER_COLOR = "#DC143C"          # 오류 또는 위험한 액션 색상 (진홍색) (Color for errors or dangerous actions (Crimson))
    KILL_COLOR = "#D32F2F"           # 'Kill' 버튼 전용 색상 (빨간색) (Specific color for the 'Kill' button (Red))
    KILL_HOVER_COLOR = "#E57373"     # Kill 색상의 호버 변형 (Hover variant for the kill color)
    
    # --- 로그 레벨별 색상 (Log Level Specific Colors) ---
    # 로그 레벨 이름을 로그 뷰의 표시 색상에 매핑하는 딕셔너리입니다.
    # A dictionary mapping log level names to their display colors in the log view.
    LOG_LEVEL_COLORS = {
        # --- 표준 레벨 (Standard Levels) ---
        "TRACE": "#95a5a6",      # 세분화된 세부 정보용 밝은 회색 (Light grey for fine-grained details)
        "DEBUG": "#bdc3c7",      # 디버깅 정보용 흰색-회색 (White-grey for debugging information)
        "INFO": "#E0E0E0",       # 정보 메시지용 기본 텍스트 색상 (Default text color for informational messages)
        "PROGRESS": "#a29bfe",   # 진행률 표시줄 업데이트용 부드러운 보라색 (A soft purple for progress bar updates)
        "WARNING": "#FFC107",    # 잠재적 문제에 대한 호박색 (Amber for potential issues)
        "ERROR": "#DC143C",      # 오류에 대한 진홍색 (Crimson for errors)
        "FATAL": "#8B0000",      # 애플리케이션 종료 수준의 치명적 오류용 어두운 빨간색 (Dark red for critical, application-ending errors)
        
        # --- 사용자 정의 시맨틱 레벨 (Custom Semantic Levels) ---
        "THINKING": "#87CEEB",    # AI 추론 단계(CoT 등)용 하늘색 (Sky Blue for AI reasoning steps (CoT, etc.))
        "DATA": "#B2F2BB",       # 데이터 입출력 및 처리용 부드러운 녹색 (A soft green for data I/O and processing)
        "AUDIT": "#FFB8B8",      # 보안/감사 이벤트용 밝은 분홍색/연어색 (A light pink/salmon for security/audit events)
        "SYSTEM": "#8e44ad",     # 시스템 수준 메시지(시작, 중지)용 보라색 (Purple for system-level messages (start, stop))
        
        # --- 사용자 및 상태 레벨 (User & State Levels) ---
        "COMMENT": "#FFD700",    # 사용자가 추가한 코멘트용 금색 (Gold for user-added comments)
        "ADDED": "#007ACC",      # 새로 추가된(저장되지 않은) 로그용 녹색 (Green for newly added (unsaved) logs)
        "MODIFIED": "#00C3E6",   # 수정된(저장되지 않은) 로그용 파란색 (Blue for modified (unsaved) logs)
        "DELETED": "#D32F2F"     # 삭제 표시된 로그용 빨간색 (Red for logs marked for deletion)
    }

    # --- 글꼴 (Fonts) ---
    FONT_FAMILY_UI = "Segoe UI"      # 버튼, 레이블 등 UI 요소용 깔끔하고 현대적인 글꼴 (A clean, modern font for UI elements like buttons and labels)
    FONT_FAMILY_LOG = "Consolas"    # 가독성을 위해 로그 표시 영역에 사용하는 고정폭 글꼴 (A monospaced font for the log display area for better readability)
    
    # --- 위젯 스타일 딕셔너리 (Widget Style Dictionaries) ---
    BUTTON_STYLE = {
        "fg": "white", 
        "font": (FONT_FAMILY_UI, 10, "bold"), 
        "relief": "flat", 
        "padx": 10, "pady": 5, 
        "width": 12, 
        "borderwidth": 0, 
        "activeforeground": "white",
        "activebackground": "#4A4A4A"
    }
    
    DISABLED_BUTTON_STYLE = {
        "fg": DISABLED_TEXT_COLOR, 
        "bg": "#555555", 
        "font": (FONT_FAMILY_UI, 10, "bold"), 
        "relief": "flat", 
        "padx": 10, "pady": 5, 
        "width": 12, 
        "borderwidth": 0,
        "activebackground": "#555555"
    }
