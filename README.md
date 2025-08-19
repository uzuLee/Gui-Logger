# Log Viewer README

## 소개 (Introduction)
이 문서는 로그 뷰어 GUI 애플리케이션에 대한 기술적인 내용을 담고 있습니다. 애플리케이션은 `log_display.py`를 중심으로 한 메인 뷰어와, 로그 수정을 위한 `editor_window.py`, 그리고 전체 UI의 디자인을 관리하는 `theme.py`로 구성되어 있습니다.

This document provides technical details for the Log Viewer GUI application. The application consists of the main viewer centered around `log_display.py`, the `editor_window.py` for editing logs, and `theme.py` for managing the overall UI design.

## 주요 구성 요소 (Main Components)
- **`log_display.py`**: 메인 로그 뷰어 창입니다. 대상 스크립트를 실행하고 실시간으로 로그를 표시하며, 기존 로그 파일을 열어보고 편집하는 핵심 기능을 담당합니다.
- **`editor_window.py`**: 로그 항목을 새로 추가하거나 기존 항목을 수정하기 위한 별도의 에디터 창입니다.
- **`theme.py`**: 애플리케이션의 모든 색상, 폰트, 위젯 스타일을 중앙에서 관리하여 일관된 디자인을 유지합니다.

---
- **`log_display.py`**: The main log viewer window. It handles the core functionalities of running a target script, displaying its logs in real-time, and opening/editing existing log files.
- **`editor_window.py`**: A separate editor window for adding new log entries or modifying existing ones.
- **`theme.py`**: Centrally manages all colors, fonts, and widget styles for the application to maintain a consistent design.

## 주요 기능 상세 (Detailed Features)

### 1. 실행 상태 관리 (Process State Management)
애플리케이션은 다음과 같은 주요 상태를 가집니다. 각 상태에 따라 사용 가능한 기능과 UI가 동적으로 변경됩니다.
The application has several main states. The available features and UI change dynamically based on the current state.

- **Idle (대기 상태):**
  - 스크립트 실행 전 또는 로그 파일이 열리기 전의 기본 상태입니다.
  - 대부분의 컨트롤(Pause, Save 등)이 비활성화됩니다.
  - `Run` 버튼과 `Open Log File` 버튼만 활성화됩니다.
  - **(EN)** The default state before running a script or opening a log file. Most controls (Pause, Save, etc.) are disabled. Only the `Run` and `Open Log File` buttons are active.

- **Running (실행 중):**
  - `Run` 버튼을 눌러 대상 스크립트(`start_glen.py`)가 실행 중인 상태입니다.
  - 로그가 실시간으로 화면에 표시됩니다.
  - `Run` 버튼은 `Kill` 버튼으로 변경되며, 클릭 시 실행 중인 프로세스를 종료할 수 있습니다.
  - `Pause` 버튼이 활성화됩니다.
  - **로그 편집 기능은 비활성화됩니다.**
  - **(EN)** The state when the target script (`start_glen.py`) is running after pressing the `Run` button. Logs are displayed in real-time. The `Run` button changes to a `Kill` button, which can terminate the running process. The `Pause` button becomes active. **Log editing features are disabled.**

- **Paused (일시 정지):**
  - `Pause` 버튼을 눌러 스크립트의 동작이 일시 정지된 상태입니다. (내부적으로 `pause.flag` 파일을 생성하여 신호를 보냅니다.)
  - **로그 편집 기능(주석 추가, 라인 수정 등)이 활성화됩니다.**
  - **Undo/Redo 스택에 변경 사항이 없을 경우:** 버튼은 `Resume`으로 표시되며, `SUCCESS_COLOR`(녹색 계열)를 가집니다. 클릭 시 `pause_flag.txt`를 삭제하여 프로세스를 재개합니다.
  - **Undo/Redo 스택에 변경 사항이 있을 경우:** 버튼은 `Save`로 변경되며, `PRIMARY_COLOR`(파란색 계열)를 가집니다. 클릭 시 변경 사항을 현재 로그 파일에 저장합니다.
  - **(EN)** The state when the script is paused by pressing the `Pause` button (which signals the script by creating a `pause_flag.txt` file). **Log editing features (adding comments, modifying lines) become active.**
    - **If there are no changes in the undo/redo stack:** The button displays `Resume` and has the `SUCCESS_COLOR` (green). Clicking it resumes the process by deleting `pause.flag`.
    - **If there are changes in the undo/redo stack:** The button changes to `Save` and has the `PRIMARY_COLOR` (blue). Clicking it saves the changes to the current log file.

- **Viewing (로그 파일 보기):**
  - `Open Log File` 버튼을 통해 기존 `.log` 파일을 열람하는 상태입니다.
  - 스크립트는 실행되지 않으며, 파일의 내용을 정적으로 보여줍니다.
  - **로그 편집 기능이 활성화됩니다.**
  - 변경 사항이 발생하면 `Save` 버튼이 활성화되어 파일에 덮어쓸 수 있습니다.
  - `Run` 버튼은 `Exit` 버튼으로 변경되며, 클릭 시 뷰어 모드를 종료하고 초기 대기 상태로 돌아갑니다.
  - **(EN)** The state when viewing an existing `.log` file via the `Open Log File` button. The script is not running; the view is static. **Log editing features are active.** The `Save` button becomes active if any changes are made. The `Run` button changes to `Exit`, which closes the view mode and returns to the initial Idle state.

### 2. 로그 필터링 (Log Filtering)
- `Filters (x/y) ▼` 버튼을 클릭하여 로그 필터링 드롭다운 메뉴를 열 수 있습니다.
- `TRACE`, `DEBUG`, `INFO` 등 특정 로그 레벨을 선택/해제하여 로그 뷰에서 보거나 숨길 수 있습니다.
- 드롭다운이 열려있을 때 버튼의 화살표는 위(`▲`)를, 닫혀있을 때는 아래(`▼`)를 가리킵니다.
- 드롭다운 메뉴 외부의 영역을 클릭하면 메뉴가 자동으로 닫힙니다.
- **(EN)** Clicking the `Filters (x/y) ▼` button opens the log filtering dropdown menu. You can check/uncheck specific log levels (e.g., `TRACE`, `DEBUG`, `INFO`) to show or hide them from the log view. The arrow on the button points up (`▲`) when the dropdown is open and down (`▼`) when closed. Clicking anywhere outside the dropdown closes it automatically.

### 3. 로그 편집 및 에디터 창 (Log Editing & Editor Window)
- **조건 (Condition):** `Paused` 또는 `Viewing` 상태에서만 활성화됩니다.
- **주석 추가 (Add Comment):** 로그 라인을 선택하지 않고 하단의 입력창에 텍스트를 입력하고 전송하면, 해당 내용이 `[COMMENT]` 로그로 추가됩니다. 로그 라인을 선택했다면 그 바로 아래에 추가됩니다.
- **에디터 창 열기 (Open Editor Window):**
  - 수정하고 싶은 로그 라인을 클릭하여 선택한 후, `Ctrl+E` 단축키를 누르면 에디터 창이 열립니다.
  - 에디터 창에서는 선택된 로그의 내용과 레벨을 자유롭게 수정할 수 있습니다.
- **에디터 창 모드 전환 (Editor Window Mode Toggle):**
  - 에디터 창 우측 상단에는 현재 모드를 나타내는 뱃지(`ADD`/`EDIT`)와 `Switch` 버튼이 있습니다.
  - **EDIT 모드:** 선택된 로그를 수정하는 모드입니다. 뱃지는 `MODIFIED` 색상(파란색 계열)으로 표시됩니다.
  - **ADD 모드:** `Switch` 버튼을 눌러 전환할 수 있으며, 새로운 로그를 작성하는 모드입니다. 뱃지는 `ADDED` 색상(성공색 계열)으로 표시됩니다.
  - `Apply` 버튼을 누르면 변경 사항이 메인 로그 뷰어에 반영되고 창이 닫힙니다.
- **(EN)** **Condition:** Active only in `Paused` or `Viewing` states.
  - **Add Comment:** By typing in the bottom input field without a line selected, a `[COMMENT]` log is added to the end. If a line is selected, the comment is inserted below it.
  - **Open Editor Window:** Select a log line by clicking it and press `Ctrl+E` to open the editor window. In the editor, you can freely modify the content and log level of the selected entry.
  - **Editor Window Mode Toggle:** The top-right of the editor window features a mode badge (`ADD`/`EDIT`) and a `Switch` button.
    - **EDIT Mode:** For modifying the selected log. The badge is colored with `LOG_LEVEL_COLORS['MODIFIED']`.
    - **ADD Mode:** Accessible via the `Switch` button, for creating a new log entry. The badge is colored with `LOG_LEVEL_COLORS['ADDED']`.
    - The `Apply` button saves the changes to the main log viewer and closes the window.

### 4. 링크 및 폰트 제어 (Link & Font Control)
- **링크화 (Hyperlinking):**
  - 로그 내용 중 웹 URL (`http://...`, `https://...`)과 로컬 파일 경로 (`@C:\...`, `@E:\...` 등, 슬래시와 역슬래시, 따옴표 모두 감지 가능)를 자동으로 감지하여 밑줄과 함께 링크로 만듭니다.
  - `Ctrl+Click`으로 해당 URL을 웹 브라우저에서 열거나 파일을 실행할 수 있습니다.
  - 파일 경로에 `Shift+Click`을 하면 해당 파일이 위치한 폴더를 탐색기에서 엽니다.
- **폰트 크기 (Font Size):**
  - 메인 뷰어의 `A+` / `A-` 버튼으로 로그 텍스트의 크기를 조절할 수 있습니다.
- **(EN)** **Hyperlinking:** Web URLs (`http://...`, `https://...`) and local file paths (e.g., `@C:\...`, slashes and reverse slashes, all wrapped in quotation marks can be detected) within logs are automatically detected and underlined.
  - `Ctrl+Click` opens the URL in a web browser or executes the file.
  - `Shift+Click` on a file path opens its containing folder in the file explorer.
  - **Font Size:** The `A+` / `A-` buttons on the main viewer control the font size of the log text area.

## 색상 및 스타일 맞춤 설정 (Color & Style Customization)
- 애플리케이션의 모든 시각적 요소(색상, 폰트, 버튼 스타일 등)는 `glen_prototype/src/utils/logging_gui/gui/theme.py` 파일의 `Theme` 클래스에서 중앙 관리됩니다.
- UI의 모양을 변경하고 싶다면 이 파일의 값들을 수정하면 됩니다. 예를 들어, `PRIMARY_COLOR` 값을 바꾸면 해당 색상을 사용하는 모든 버튼의 색상이 한 번에 변경됩니다.
- **(EN)** All visual elements of the application (colors, fonts, button styles, etc.) are centrally managed in the `Theme` class within the `glen_prototype/src/utils/logging_gui/gui/theme.py` file. To change the look and feel of the UI, you can modify the values in this file. For example, changing the `PRIMARY_COLOR` value will update the color of all buttons that use it.
