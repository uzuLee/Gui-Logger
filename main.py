import tkinter as tk
from pathlib import Path

try:
    # Attempt to import tkinterdnd2 for drag-and-drop support.
    # 드래그 앤 드롭 기능을 위해 tkinterdnd2 임포트를 시도합니다.
    from tkinterdnd2 import TkinterDnD
    DND_SUPPORT = True
except ImportError:
    DND_SUPPORT = False

# Import core components from the gui package.
# gui 패키지에서 핵심 구성 요소들을 임포트합니다.
from .gui.log_display import LogDisplay
from .gui.utils import setup_logging
from .gui.config import SCRIPT_PATH, LOG_DIR

def main():
    """
    # Main function to initialize and run the application.
    # 애플리케이션을 초기화하고 실행하는 메인 함수입니다.
    """
    # Set up logging for the GUI application itself.
    # GUI 애플리케이션 자체를 위한 로깅을 설정합니다.
    # setup_logging() # Uncomment this line to enable logging for the GUI.
                      # GUI 로깅을 활성화하려면 이 줄의 주석을 해제하세요.

    # Use the appropriate root window class based on DND support.
    # DND 지원 여부에 따라 적절한 루트 윈도우 클래스를 사용합니다.
    root = TkinterDnD.Tk() if DND_SUPPORT else tk.Tk()

    # Set initial script and log directory paths from the configuration.
    # 설정 파일에서 초기 스크립트 및 로그 디렉토리 경로를 설정합니다.
    initial_script_path = SCRIPT_PATH if Path(SCRIPT_PATH).is_file() else ""
    initial_log_dir = str(LOG_DIR)

    # Create and run the main application instance.
    # 메인 애플리케이션 인스턴스를 생성하고 실행합니다.
    app = LogDisplay(master=root, script_path=initial_script_path, log_dir=initial_log_dir)
    root.mainloop()

if __name__ == "__main__":
    # This block ensures the main function is called only when the script is executed directly.
    # 이 블록은 스크립트가 직접 실행될 때만 main 함수가 호출되도록 보장합니다.
    main()