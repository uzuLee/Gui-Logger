# E:\projectFiles\programming\.gemini-cli\glen_prototype\src\utils\logging_gui\main.py
"""
# 로그 뷰어 애플리케이션의 메인 진입점입니다.
# Main entry point for the Log Viewer application.

# 이 스크립트는 애플리케이션 환경을 초기화하고, 로깅을 설정하며,
# 메인 GUI 창을 실행합니다.
# This script initializes the application environment, sets up logging,
# and launches the main GUI window.
"""

# --- 표준 라이브러리 임포트 (Standard Library Imports) ---
import tkinter as tk  # GUI 생성을 위한 Tkinter 라이브러리 임포트 (Import the Tkinter library for creating the GUI)

# --- 로컬 애플리케이션 임포트 (Local Application Imports) ---
# 'log_display' 모듈에서 메인 GUI 프레임 클래스를 임포트합니다.
# Import the main GUI frame class from the 'log_display' module.
from .gui.log_display import LogDisplay
# 애플리케이션 내부 로그를 위한 로깅 설정 유틸리티를 임포트합니다.
# Import the logging setup utility for the application's internal logs.
from .gui.utils import setup_logging
# 설정 파일에서 초기값으로 사용할 기본 경로를 임포트합니다.
# Import default paths from the configuration file to be used as initial values.
from .gui.config import THINK_CORE_SCRIPT_PATH, LOG_DIR

def main():
    """
    # 애플리케이션을 초기화하고 Tkinter 메인 이벤트 루프를 시작합니다.
    # Initializes the application and starts the Tkinter main event loop.
    
    # 이 함수는 세 가지 주요 작업을 수행합니다:
    # 1. `setup_logging()`을 호출하여 애플리케이션 자체의 로깅을 설정합니다.
    # 2. 메인 Tkinter 창(`root`)을 생성합니다.
    # 3. `LogDisplay` 위젯을 인스턴스화하고 기본 경로를 전달한 후, GUI 이벤트 루프를 시작합니다.
    # This function performs three primary tasks:
    # 1. Calls `setup_logging()` to configure logging for the application itself.
    # 2. Creates the main Tkinter window (`root`).
    # 3. Instantiates the `LogDisplay` widget, passing default paths, and starts the GUI event loop.
    """
    # GUI 애플리케이션 자체의 운영 메시지를 위한 로깅을 설정합니다.
    # Configure logging for the GUI application's own operational messages.
    setup_logging()
    
    # 메인 애플리케이션 창(루트 위젯)을 생성합니다.
    # Create the main application window (the root widget).
    root = tk.Tk()
    
    # 메인 애플리케이션 프레임(LogDisplay)을 인스턴스화합니다.
    # 설정 파일의 기본 스크립트 경로와 로그 디렉토리를 전달합니다.
    # 이 값들은 UI에 채워지며, 사용자가 런타임에 변경할 수 있습니다.
    # Instantiate the main application frame (LogDisplay).
    # Pass the default script path and log directory from the config file.
    # These values will populate the UI and can be changed by the user at runtime.
    app = LogDisplay(
        master=root, 
        script_path=THINK_CORE_SCRIPT_PATH, 
        log_dir=LOG_DIR
    )
    
    # Tkinter 이벤트 루프를 시작합니다. 이 코드는 창을 화면에 나타나게 하고
    # 사용자 이벤트(예: 버튼 클릭, 키 입력)를 기다립니다.
    # Start the Tkinter event loop. This makes the window appear on the screen
    # and waits for user events (e.g., button clicks, key presses).
    root.mainloop()

# 표준 파이썬 진입점 확인입니다.
# 이 코드는 스크립트가 직접 실행될 때만 main() 함수를 호출하도록 보장하며,
# 다른 스크립트에서 모듈로 임포트될 때는 호출되지 않습니다.
# Standard Python entry point check.
# This ensures that the main() function is called only when the script is executed directly,
# not when it's imported as a module into another script.
if __name__ == "__main__":
    main()
