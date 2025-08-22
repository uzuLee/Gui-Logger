
import os
import sys
import json
from pathlib import Path

# --- Path Configuration (경로 설정) ---

def get_app_root() -> Path:
    """
    # Determine the application's root directory, supporting both standard execution and PyInstaller bundles.
    # 일반 실행과 PyInstaller 번들 환경 모두를 지원하며, 애플리케이션의 루트 디렉토리를 결정합니다.
    
    # Returns:
    #     Path: The absolute path to the application's root directory.
    #           (애플리케이션 루트 디렉토리의 절대 경로)
    """
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        # Running as a PyInstaller bundle (e.g., a single .exe file).
        # PyInstaller 번들(.exe 파일)로 실행 중입니다.
        return Path(sys.executable).parent
    else:
        # Running as a standard Python script.
        # 일반 파이썬 스크립트로 실행 중입니다.
        # __file__ is in .../gui/config.py, so we go up two levels to get to .../logging_gui/
        return Path(__file__).parent.parent.resolve()

# Define the main application root directory.
# 메인 애플리케이션 루트 디렉토리를 정의합니다.
APP_ROOT = get_app_root()

# Define paths for data, logs, and themes relative to the app root.
# These directories are intended for user modification and are not part of the executable.
# 앱 루트를 기준으로 데이터, 로그, 테마 폴더의 경로를 정의합니다.
# 이 디렉토리들은 사용자가 직접 수정할 수 있도록 실행 파일에 포함되지 않습니다.
DATA_DIR = APP_ROOT / "data"
LOG_DIR = APP_ROOT / "logs"
THEMES_DIR = APP_ROOT / "themes"

# Define the full path to the pause flag file, used for pausing/resuming the monitored script.
# 모니터링되는 스크립트를 일시 중지/재개하는 데 사용되는 pause 플래그 파일의 전체 경로를 정의합니다.
PAUSE_FLAG_PATH = DATA_DIR / "pause.flag"

# Define a default placeholder for the script path.
# 스크립트 경로에 대한 기본 플레이스홀더를 정의합니다.
SCRIPT_PATH = "" 

# --- Directory and File Initialization (디렉토리 및 파일 초기화) ---

# Ensure data and log directories exist, creating them if necessary.
# 데이터 및 로그 디렉토리가 존재하도록 보장하고, 필요시 생성합니다.
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# --- Configuration Loading (설정 로드) ---

def load_json_config(file_path: Path, default: dict) -> dict:
    """
    # Load a JSON configuration file. If the file doesn't exist or is invalid, return a default.
    # JSON 설정 파일을 로드합니다. 파일이 없거나 유효하지 않으면 기본값을 반환합니다.

    # Args:
    #     file_path (Path): The path to the JSON file. (JSON 파일 경로)
    #     default (dict): The default dictionary to return on failure. (실패 시 반환할 기본 딕셔너리)

    # Returns:
    #     dict: The loaded configuration or the default. (로드된 설정 또는 기본값)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default

# Load the interpreter map from interpreters.json.
# interpreters.json 파일에서 인터프리터 맵을 로드합니다.
_interpreter_json_path = DATA_DIR / "interpreters.json"
INTERPRETER_MAP = load_json_config(_interpreter_json_path, {})

if not INTERPRETER_MAP:
    print(f"Warning: '{_interpreter_json_path}' not found or invalid. Interpreters will not be mapped automatically.")
