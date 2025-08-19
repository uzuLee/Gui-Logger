-----

# Log Viewer

## 개요 (Overview)

**🇰🇷 (Korean)**

Log Viewer는 Python의 Tkinter로 제작된 GUI 애플리케이션으로, 스크립트나 프로세스에서 발생하는 로그를 실시간으로 모니터링하고, 기존 로그 파일을 열어 편집할 수 있는 강력한 기능을 제공합니다. 사용자는 로그를 레벨별로 필터링하고, 실행 중인 프로세스를 일시 중지하여 로그를 추가, 수정, 삭제할 수 있으며, 이러한 모든 편집 내용은 실행 재개 시 파일에 저장할 수 있습니다.

-----

**🇬🇧 (English)**

Log Viewer is a GUI application built with Python's Tkinter, providing robust functionality for real-time monitoring of logs from scripts or processes, as well as opening and editing existing log files. Users can filter logs by level, pause a running process to add, modify, or delete log entries, and save all these changes back to the file upon resuming.

## 주요 기능 (Key Features)

**🇰🇷 (Korean)**

  * **실시간 로그 모니터링**: 외부 스크립트(`think_core` 프로세스)의 출력을 실시간으로 표시합니다.
  * **로그 파일 관리**: 기존 `.log` 파일을 열고 내용을 확인하며, 변경 사항을 저장할 수 있습니다.
  * **동적 필터링**: TRACE, DEBUG, INFO, WARNING, ERROR, FATAL 등 로그 레벨별로 표시 여부를 동적으로 제어할 수 있습니다.
  * **프로세스 제어**: `Run`, `Kill`, `Pause`, `Resume` 기능을 통해 모니터링 중인 프로세스를 제어합니다.
  * **로그 편집 기능**:
      * **추가**: `COMMENT` 또는 다른 레벨의 로그를 원하는 위치에 삽입할 수 있습니다.
      * **수정**: 기존 로그의 내용을 변경할 수 있습니다.
      * **삭제**: 특정 로그 라인을 삭제 대상으로 표시하고 저장 시 실제 파일에서 제거합니다.
  * **실행 취소/다시 실행 (Undo/Redo)**: `Ctrl+Z` 및 `Ctrl+Y` 단축키를 통해 모든 편집 작업을 취소하거나 다시 실행할 수 있습니다.
  * **커맨드 입력**: 입력창에 `/add`, `/edit`, `/delete`와 같은 명령어를 입력하여 로그를 관리할 수 있습니다.
  * **자동 완성**: `/add` 명령어 입력 후 스페이스바를 누르면 로그 레벨(TRACE, DEBUG 등) 자동 완성 팝업이 표시됩니다.
  * **하이퍼링크 지원**: 로그에 포함된 웹 URL이나 로컬 파일 경로(`@C:/path/to/file`)를 클릭하여 열 수 있습니다.
  * **팝업 에디터**: `Ctrl+E` 단축키로 별도의 편집기 창을 열어 보다 편리하게 로그를 수정하거나 추가할 수 있습니다.
  * **UI 커스터마이징**: 로그 뷰어의 폰트 크기를 동적으로 조절할 수 있습니다.
  * **세련된 다크 테마**: 가독성을 높이고 현대적인 UI를 제공하는 어두운 테마를 적용했습니다.

-----

**🇬🇧 (English)**

  * **Real-Time Log Monitoring**: Displays output from an external script (the `think_core` process) in real-time.
  * **Log File Management**: Allows opening existing `.log` files, viewing their content, and saving changes.
  * **Dynamic Filtering**: Dynamically control the visibility of logs based on their level, such as TRACE, DEBUG, INFO, WARNING, ERROR, and FATAL.
  * **Process Control**: Control the monitored process with `Run`, `Kill`, `Pause`, and `Resume` functionalities.
  * **Log Editing Capabilities**:
      * **Add**: Insert new logs, such as `COMMENT` or other levels, at any position.
      * **Modify**: Change the content of existing log entries.
      * **Delete**: Mark specific log lines for deletion, which are removed from the file upon saving.
  * **Undo/Redo**: Undo or redo any editing action using the `Ctrl+Z` and `Ctrl+Y` shortcuts.
  * **Command Input**: Manage logs by typing commands like `/add`, `/edit`, and `/delete` into the input field.
  * **Autocomplete**: An autocomplete popup for log levels (TRACE, DEBUG, etc.) appears after typing `/add` followed by a space.
  * **Hyperlink Support**: Clickable web URLs and local file paths (e.g., `@C:/path/to/file`) within the logs can be opened directly.
  * **Popup Editor**: Open a separate editor window with the `Ctrl+E` shortcut for more convenient log editing and creation.
  * **UI Customization**: Dynamically adjust the font size of the log viewer.
  * **Sleek Dark Theme**: Features a modern dark theme for enhanced readability and user experience.

## 파일 구조 (File Structure)

**🇰🇷 (Korean)**

  * `main.py`: 애플리케이션을 시작하는 메인 진입점입니다.
  * `log_display.py`: GUI의 메인 클래스. UI 요소, 이벤트 처리, 로그 관리 로직 등 핵심 기능을 모두 포함합니다.
  * `editor_window.py`: 로그를 추가하거나 수정할 때 나타나는 별도의 팝업 에디터 창을 정의합니다.
  * `run_think_core.py`: GUI가 모니터링할 로그를 생성하는 테스트용 서브프로세스 스크립트입니다.
  * `config.py`: 로그 디렉토리, 플래그 파일 경로 등 애플리케이션에서 사용되는 주요 경로와 상수를 정의합니다.
  * `theme.py`: UI의 색상, 폰트, 위젯 스타일 등 시각적 테마를 정의합니다.
  * `utils.py`: 애플리케이션 자체의 로깅 설정을 구성하는 유틸리티 함수를 포함합니다.

-----

**🇬🇧 (English)**

  * `main.py`: The main entry point that launches the application.
  * `log_display.py`: The main GUI class. It contains all core functionalities, including UI elements, event handling, and log management logic.
  * `editor_window.py`: Defines the separate pop-up editor window that appears when adding or modifying a log entry.
  * `run_think_core.py`: A test surrogate script that acts as the subprocess, generating logs for the GUI to monitor.
  * `config.py`: Defines key paths and constants used throughout the application, such as the log directory and flag file paths.
  * `theme.py`: Defines the visual theme of the UI, including colors, fonts, and widget styles.
  * `utils.py`: Contains utility functions, such as configuring the logging setup for the application itself.

## 사용법 (How to Use)

**🇰🇷 (Korean)**

1.  **실행**: 프로젝트의 루트 디렉토리에서 아래 명령어를 실행하여 애플리케이션을 시작합니다. Python의 모듈(`-m`) 방식으로 실행하는 것을 권장하며, 이는 모든 상대 경로 임포트가 올바르게 동작하도록 보장합니다.

    ```bash
    python -m src.utils.logging_gui.main
    ```

2.  **실시간 모니터링**:

      * **Run**: `Run` 버튼을 클릭하면 `run_think_core.py` 스크립트가 서브프로세스로 실행되며, 생성되는 로그가 실시간으로 화면에 표시됩니다.
      * **Pause**: `Pause` 버튼을 클릭하면 서브프로세스가 일시 중지됩니다. 이 상태에서 로그를 클릭하여 선택하거나, 커맨드를 입력하여 로그를 추가/수정/삭제할 수 있습니다.
      * **Save/Resume**:
          * 편집 내용이 있을 경우 버튼이 `Save`로 변경됩니다. 클릭하면 변경 사항이 현재 로그 파일에 저장됩니다.
          * 편집 내용이 없을 경우 `Resume` 버튼이 표시되며, 클릭하면 프로세스가 다시 실행됩니다.
      * **Kill**: 실행 중인 서브프로세스를 강제 종료합니다.

3.  **로그 파일 열기**:

      * **Open Log File**: 버튼을 클릭하여 기존 로그 파일을 엽니다.
      * 파일을 열면 "View Mode"가 되며, 이 상태에서도 로그 편집이 가능합니다.
      * **Save**: 편집된 내용을 파일에 저장하려면 `Save` 버튼을 클릭합니다.
      * **Exit**: `Exit` 버튼을 클릭하여 "View Mode"를 종료하고 초기 화면으로 돌아갑니다.

4.  **로그 편집 단축키**:

      * **로그 선택**: Pause 상태 또는 View Mode에서 원하는 로그 라인을 클릭하여 선택합니다.
      * **편집기 열기**: `Ctrl+E`를 눌러 선택된 로그를 수정하거나 새로운 로그를 추가할 수 있는 팝업 편집기를 엽니다.

-----

**🇬🇧 (English)**

1.  **Execution**: Run the following command from the project's root directory to start the application. It is recommended to run the program as a Python module (`-m`) to ensure all relative imports work correctly.

    ```bash
    python -m src.utils.logging_gui.main
    ```

2.  **Real-Time Monitoring**:

      * **Run**: Click the `Run` button to execute the `run_think_core.py` script as a subprocess. The generated logs will be displayed in real-time.
      * **Pause**: Click the `Pause` button to pause the subprocess. In this state, you can click to select log lines or use commands to add, modify, or delete logs.
      * **Save/Resume**:
          * If there are unsaved edits, the button changes to `Save`. Click it to save the changes to the current log file.
          * If there are no edits, the button will be `Resume`. Click it to resume the process.
      * **Kill**: Forcibly terminates the running subprocess.

3.  **Opening a Log File**:

      * **Open Log File**: Click this button to open an existing log file.
      * Opening a file enters "View Mode," where you can also edit the logs.
      * **Save**: Click the `Save` button to commit your edits to the file.
      * **Exit**: Click the `Exit` button to close the "View Mode" and return to the initial state.

4.  **Log Editing Shortcut**:

      * **Select Log**: In Paused state or View Mode, click a log line to select it.
      * **Open Editor**: Press `Ctrl+E` to open a pop-up editor where you can modify the selected log or add a new one.
