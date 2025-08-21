-----

# Log Viewer README

## 1\. 개요 (Overview)

**Log Viewer**는 Python 스크립트의 실행을 제어하고, 실시간으로 생성되는 로그를 모니터링하며, 기존 로그 파일을 열어보고 편집할 수 있는 강력한 GUI 애플리케이션입니다. Tkinter를 기반으로 제작되었으며, 사용자 편의성을 위한 다양한 기능(테마 변경, 동적 필터링, 검색, 드래그 앤 드롭 등)을 제공합니다.

The **Log Viewer** is a powerful GUI application for controlling the execution of Python scripts, monitoring logs in real-time, and opening and editing existing log files. Built with Tkinter, it offers a variety of user-friendly features such as theme switching, dynamic filtering, search, and drag-and-drop support.

## 2\. 주요 기능 (Key Features)

  * **실시간 로그 모니터링 (Real-time Log Monitoring)**: 지정된 스크립트를 실행하고 `stdout` 및 `stderr` 출력을 GUI에서 실시간으로 확인합니다.
    (Executes the specified script and displays `stdout` and `stderr` output in real-time within the GUI.)
  * **프로세스 제어 (Process Control)**: 스크립트를 시작(Run), 강제 종료(Kill), 일시정지(Pause), 재개(Resume)할 수 있습니다.
    (Allows you to start (Run), forcefully terminate (Kill), pause (Pause), and resume (Resume) the script.)
  * **로그 파일 뷰어 (Log File Viewer)**: 기존 `.log` 파일을 열어 GUI 내에서 내용을 확인하고 편집할 수 있습니다.
    (Open existing `.log` files to view and edit their content within the GUI.)
  * **강력한 로그 편집 (Powerful Log Editing)**:
      * 로그 라인 추가, 수정, 삭제 기능 (Add, modify, and delete log lines).
      * 변경 사항에 대한 무제한 실행 취소/다시 실행 (Undo/Redo) 지원 (Unlimited undo/redo support for changes).
      * 전용 팝업 에디터 창 제공 (Provides a dedicated pop-up editor window via Ctrl+E).
  * **동적 필터링 (Dynamic Filtering)**: `INFO`, `DEBUG`, `ERROR` 등 로그 레벨별로 실시간으로 로그를 필터링하여 원하는 내용만 볼 수 있습니다.
    (Filter logs in real-time by log levels such as `INFO`, `DEBUG`, `ERROR` to view only the desired content.)
  * **로그 검색 (Log Search)**: 특정 키워드나 정규 표현식(Regex)을 사용하여 로그 내용을 빠르게 검색하고 결과를 하이라이트로 표시합니다.
    (Quickly search log content using specific keywords or regular expressions (Regex) and highlight the results.)
  * **테마 지원 (Theme Support)**: 다크/라이트 모드를 포함한 사용자 정의 테마를 쉽게 전환하고 추가할 수 있습니다.
    (Easily switch between and add custom themes, including dark and light modes.)
  * **드래그 앤 드롭 (Drag and Drop)**: 스크립트 파일이나 로그 디렉토리 폴더를 창으로 드래그하여 경로를 쉽게 설정할 수 있습니다.
    (Easily set paths by dragging and dropping a script file or a log directory folder onto the window.)
  * **클릭 가능한 링크 (Clickable Links)**: 로그에 포함된 파일 경로 (`@C:\path\to\file`)나 웹 URL (`http://...`)을 Ctrl+클릭하여 바로 열 수 있습니다.
    (Instantly open file paths (`@C:\path\to\file`) or web URLs (`http://...`) in logs with a Ctrl+click.)
  * **설정 저장 (Settings Persistence)**: 스크립트 경로, 로그 디렉토리, 테마, 필터 등 마지막으로 사용한 설정을 `gui_settings.json` 파일에 자동으로 저장하고 불러옵니다.
    (Automatically saves and loads the last used settings—such as script path, log directory, theme, and filters—in a `gui_settings.json` file.)
  * **커스터마이징 (Customization)**: `custom_logs.json` 파일을 통해 사용자 정의 로그 레벨과 색상을 추가할 수 있습니다.
    (Add custom log levels and colors via the `custom_logs.json` file.)

## 3\. 요구 사항 (Prerequisites)

  * **Python 3.12** (이 버전에서 개발 및 테스트되었습니다. / Developed and tested on this version.)
  * `tkinter` (Python 표준 라이브러리 / Python's standard library)
  * `tkinterdnd2` (드래그 앤 드롭 기능을 위해 필요 / Required for drag-and-drop functionality)

`tkinterdnd2` 라이브러리는 별도 설치가 필요합니다.
The `tkinterdnd2` library needs to be installed separately.

```bash
pip install tkinterdnd2-tk
```

## 4\. 파일 구조 (File Structure)

```
(root)
│
├── main.py                     # 애플리케이션의 메인 진입점 (Main entry point for the application)
│
└── gui/
    │
    ├── log_display.py          # 메인 GUI 창 및 모든 로직 구현 (Main GUI window and implementation of all logic)
    ├── editor_window.py        # 로그 추가/편집을 위한 팝업 에디터 창 (Popup editor window for adding/editing logs)
    ├── config.py               # 경로 및 주요 설정 관리 (Manages paths and key settings)
    ├── utils.py                # GUI 자체의 로깅 설정 유틸리티 (Logging utility for the GUI itself)
    ├── theme.py                # 테마 파일을 동적으로 로드하는 관리자 (Dynamic theme loader and manager)
    ├── gui_widgets.py          # 커스텀 위젯 (예: StyledButton) 정의 (Defines custom widgets like StyledButton)
    ├── custom_logs.json        # 사용자 정의 로그 레벨 추가 (For adding custom log levels)
    │
    └── themes/
        ├── dark_theme.py       # 다크 테마 색상 및 폰트 정의 (Dark theme color and font definitions)
        └── light_theme.py      # 라이트 테마 색상 및 폰트 정의 (Light theme color and font definitions)
```

## 5\. 실행 방법 (How to Run)

프로젝트의 루트 디렉토리에서 다음 명령어를 실행합니다.
From the project's root directory, run the following command:

```bash
python main.py
```

## 6\. 사용 방법 (How to Use)

### 6.1. 초기 설정 (Initial Setup)

  * **Script Path**: 실행할 Python 스크립트의 경로를 지정합니다. `Browse...` 버튼을 사용하거나 파일을 창으로 드래그 앤 드롭하여 설정할 수 있습니다.
    (Specify the path to the Python script to run. You can set it using the `Browse...` button or by dragging and dropping the file onto the window.)
  * **Log Directory**: 실행 시 생성될 로그 파일(`glen_log_yyyymmdd_hhmmss.log`)이 저장될 폴더를 지정합니다. `Browse...` 버튼 또는 폴더를 드래그 앤 드롭하여 설정합니다.
    (Specify the folder where the log file (`glen_log_yyyymmdd_hhmmss.log`) will be saved upon execution. Set it via the `Browse...` button or by dragging and dropping the folder.)
  * **Theme**: 드롭다운 메뉴에서 원하는 UI 테마 (예: `dark_theme`, `light_theme`)를 선택합니다.
    (Select your desired UI theme (e.g., `dark_theme`, `light_theme`) from the dropdown menu.)
  * **Filters**: 필터 버튼을 클릭하여 표시할 로그 레벨을 선택/해제할 수 있습니다.
    (Click the filter buttons to toggle the visibility of different log levels.)

### 6.2. 스크립트 실행 및 제어 (Running & Controlling Scripts)

  * **Run**: 'Script Path'에 지정된 스크립트를 실행하고 로그 출력을 시작합니다.
    (Executes the script specified in 'Script Path' and starts logging the output.)
  * **Kill**: 실행 중인 스크립트 프로세스를 강제 종료합니다.
    (Forcefully terminates the running script process.)
  * **Pause**: 실행 중인 스크립트를 일시정지합니다. 스크립트가 `pause.flag` 파일을 확인하는 로직을 가지고 있어야 합니다. 이 상태에서 로그 편집이 가능해집니다.
    (Pauses the running script. The script must have logic to check for a `pause.flag` file. Log editing becomes available in this state.)
  * **Save & Resume / Resume**:
      * **Resume**: 일시정지된 스크립트를 다시 시작합니다. (Restarts a paused script.)
      * **Save & Resume**: 일시정지 중에 로그를 편집한 경우, 변경 사항을 현재 로그 파일에 저장하고 스크립트를 재개합니다. (If logs were edited while paused, this saves the changes to the current log file and resumes the script.)

### 6.3. 로그 조회 및 탐색 (Viewing & Navigating Logs)

  * **Open Log Folder**: 'Log Directory'로 지정된 폴더를 파일 탐색기에서 엽니다.
    (Opens the folder specified as 'Log Directory' in your file explorer.)
  * **Open Log File**: 기존 로그 파일을 선택하여 '로그 뷰 모드'로 전환합니다. 이 모드에서는 파일의 내용을 보고 편집할 수 있습니다.
    (Select an existing log file to switch to 'Log View Mode', where you can view and edit the file's content.)
  * **Exit**: '로그 뷰 모드'를 종료하고 초기 상태로 돌아갑니다.
    (Exits 'Log View Mode' and returns to the initial state.)
  * **폰트 크기 조절 (Font Size Control)**: `A+`, `A-` 버튼으로 로그 뷰어의 폰트 크기를 조절할 수 있습니다.
    (Adjust the font size of the log viewer using the `A+` and `A-` buttons.)
  * **링크 클릭 (Clicking Links)**:
      * **Ctrl + Click**: 파일 경로 (`@...`) 또는 웹 URL을 엽니다. (Opens a file path (`@...`) or a web URL.)
      * **Shift + Click**: 파일 경로의 상위 폴더를 엽니다. (Opens the parent folder of a file path.)

### 6.4. 로그 검색 (Log Search)

화면 상단의 검색 바를 사용하여 로그를 빠르고 쉽게 검색할 수 있습니다.
You can quickly and easily search logs using the search bar at the top of the application.

  * **검색어 입력 (Enter Search Term)**: 검색창에 찾고 싶은 텍스트나 정규 표현식을 입력합니다.
    (Enter the text or regular expression you want to find in the search box.)
  * **검색 옵션 (Search Options)**:
      * `Case`: 체크하면 대소문자를 구분하여 검색합니다. (Check for a case-sensitive search.)
      * `Regex`: 체크하면 입력된 검색어를 정규 표현식으로 처리합니다. (Check to treat the search term as a regular expression.)
  * **탐색 (Navigation)**:
      * `▼ (Find Next)`: 현재 커서 위치에서 아래 방향으로 다음 검색 결과를 찾아 하이라이트합니다.
        (Finds and highlights the next match downwards from the current cursor position.)
      * `▲ (Find Prev)`: 현재 커서 위치에서 윗 방향으로 이전 검색 결과를 찾아 하이라이트합니다.
        (Finds and highlights the previous match upwards from the current cursor position.)
  * 검색 결과는 기본적으로 노란색 배경으로 하이라이트됩니다. 검색창의 내용을 지우면 모든 하이라이트가 사라집니다.
    (Search results are highlighted with a yellow background by default. Clearing the search box removes all highlights.)

### 6.5. 로그 편집 (Log Editing)

로그 편집은 스크립트가 **일시정지(Paused)** 상태이거나 \*\*로그 뷰 모드(Log View Mode)\*\*일 때 가능합니다.
Log editing is possible only when the script is in a **Paused** state or when the application is in **Log View Mode**.

#### A. 커맨드 입력창 사용 (Using the Command Entry)

화면 하단의 입력창에 명령어를 입력하여 로그를 편집할 수 있습니다.
You can edit logs by entering commands in the input field at the bottom of the screen.

  * `/add <LEVEL> [내용/content]`: 선택된 라인 다음에 지정한 레벨과 내용으로 새 로그를 추가합니다.
    (Adds a new log with the specified level and content after the selected line.)
      * 예시 (Example): `/add INFO This is a new info log.`
  * `/delete`: 현재 선택된 로그 라인을 삭제 상태로 표시합니다.
    (Marks the currently selected log line for deletion.)
  * `/edit [내용/content]`: 선택된 로그 라인의 내용을 새 내용으로 교체합니다.
    (Replaces the content of the selected log line with new content.)
  * `/undo [횟수/count]`: 마지막 작업을 취소합니다. (기본 1회)
    (Undoes the last action. Defaults to 1 if count is omitted.)
  * `/redo [횟수/count]`: 마지막으로 취소한 작업을 다시 실행합니다. (기본 1회)
    (Redoes the last undone action. Defaults to 1 if count is omitted.)
  * 일반 텍스트를 입력하고 Enter를 누르면 `[COMMENT]` 레벨의 로그가 추가됩니다.
    (If you type plain text and press Enter, a new log with the `[COMMENT]` level will be added.)

#### B. 에디터 창 사용 (Using the Editor Window)

  * `Ctrl+E` 단축키 또는 편집이 가능한 상태에서 로그 라인을 선택하면 **Editor Window**가 열립니다.
    (Pressing the `Ctrl+E` shortcut or selecting a log line in an editable state opens the **Editor Window**.)
  * **Mode**:
      * **EDIT**: 현재 선택된 로그를 편집합니다. (Edits the currently selected log.)
      * **ADD**: 새 로그를 작성합니다. `Switch` 버튼으로 모드를 전환할 수 있습니다. (Creates a new log. You can switch modes with the `Switch` button.)
  * **Log Type**: 드롭다운 메뉴에서 로그 레벨을 선택할 수 있습니다. (Select a log level from the dropdown menu.)
  * **Apply**: 변경 사항을 로그 뷰어에 적용하고 창을 닫습니다. (Applies the changes to the log viewer and closes the window.)

### 6.6. 변경 사항 저장 (Saving Changes)

일시정지 상태나 로그 뷰 모드에서 편집된 내용은 메모리에만 존재합니다.
Changes made in the paused state or log view mode exist only in memory.

  * `Save & Resume` 또는 `Save` 버튼을 클릭하면 모든 변경사항(추가, 수정, 삭제)이 현재 로그 파일에 영구적으로 기록됩니다.
    (Clicking the `Save & Resume` or `Save` button permanently writes all changes (additions, modifications, deletions) to the current log file.)
  * 삭제된 라인은 파일에서 완전히 제거되며, 추가/수정된 라인은 그대로 저장됩니다.
    (Deleted lines are completely removed from the file, while added/modified lines are saved as they appear.)

## 7\. 커스터마이징 (Customization)

### 7.1. 테마 추가하기 (Adding a New Theme)

1.  `gui/themes/` 폴더 안에 새로운 Python 파일(예: `my_theme.py`)을 생성합니다.
    (Create a new Python file (e.g., `my_theme.py`) inside the `gui/themes/` folder.)
2.  `dark_theme.py` 또는 `light_theme.py`의 내용을 복사하여 붙여넣습니다.
    (Copy and paste the contents of `dark_theme.py` or `light_theme.py`.)
3.  `Theme` 클래스 내부의 색상 코드 (`#RRGGBB`)와 폰트 설정을 원하는 값으로 수정합니다.
    (Modify the color codes (`#RRGGBB`) and font settings inside the `Theme` class to your desired values.)
4.  애플리케이션을 다시 시작하면 새 테마가 자동으로 인식되어 Theme 드롭다운 메뉴에 추가됩니다.
    (Restart the application, and the new theme will be automatically detected and added to the Theme dropdown menu.)

### 7.2. 커스텀 로그 레벨 추가하기 (Adding Custom Log Levels)

1.  `gui/custom_logs.json` 파일을 엽니다.
    (Open the `gui/custom_logs.json` file.)

2.  아래 형식에 맞게 새로운 로그 레벨과 색상 코드를 추가합니다.
    (Add new log levels and their corresponding color codes in the following format.)

    ```json
    {
      "THINKING": "#9C27B0",
      "HYPOTHESIS": "#2196F3"
    }
    ```

3.  애플리케이션을 다시 시작하면 새로운 로그 레벨(`THINKING`, `HYPOTHESIS`)이 필터 메뉴와 에디터 창에 자동으로 추가되며, 지정된 색상으로 표시됩니다.
    (Restart the application, and the new log levels (`THINKING`, `HYPOTHESIS`) will be automatically added to the filter menu and the editor window, displayed in their specified colors.)
