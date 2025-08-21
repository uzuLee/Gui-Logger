"""
# 로깅 GUI의 설정 모듈입니다.
# Configuration module for the logging GUI.

# 이 파일은 애플리케이션 전체에서 사용되는 필수 경로와 상수를 정의하여,
# 파일 위치를 일관되게 관리합니다. 데이터 저장소, 로그, 제어 플래그,
# 그리고 실행 스크립트의 경로를 중앙에서 관리합니다.
# This file defines essential paths and constants used throughout the application,
# ensuring that file locations are managed consistently. It centralizes the
# paths for data storage, logs, control flags, and executable scripts.
"""

import os
import json
from pathlib import Path

# 현재 파일의 절대 경로를 기준으로 기본 디렉토리를 설정합니다.
# Set the base directory relative to the absolute path of the current file.
_base_dir = os.path.dirname(os.path.abspath(__file__))

# 'data' 디렉토리의 경로를 정의합니다.
# Define the path to the 'data' directory.
DATA_DIR = os.path.join(_base_dir, "..", "data")

# 'logs' 디렉토리의 경로를 정의합니다.
# Define the path to the 'logs' directory.
LOG_DIR = os.path.join(_base_dir, "..", "logs")

# 'pause.flag' 파일의 전체 경로를 정의합니다.
# Define the full path for the 'pause.flag' file.
PAUSE_FLAG_PATH = os.path.join(DATA_DIR, "pause.flag")

# GUI가 하위 프로세스로 실행하는 메인 스크립트의 절대 경로를 정의합니다.
# Define the absolute path to the GUI launches as a subprocess.
SCRIPT_PATH = os.path.abspath(os.path.join(_base_dir, "..", "(Select File)"))

# 데이터 디렉토리가 존재하지 않으면 생성합니다.
# Create the data directory if it does not exist.
os.makedirs(DATA_DIR, exist_ok=True)

# 로그 디렉토리가 존재하지 않으면 생성합니다.
# Create the log directory if it does not exist.
os.makedirs(LOG_DIR, exist_ok=True)

# --- interpreters.json 파일에서 인터프리터 맵 로드 ---

# [수정됨] interpreters.json 파일의 경로를 data 폴더 내부로 변경합니다.
_interpreter_json_path = os.path.join(DATA_DIR, "interpreters.json")

# JSON 파일을 읽어 인터프리터 맵을 로드합니다.
try:
    with open(_interpreter_json_path, 'r', encoding='utf-8') as f:
        INTERPRETER_MAP = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    # 파일이 없거나 JSON 형식이 잘못된 경우, 빈 맵을 사용합니다.
    INTERPRETER_MAP = {}
    print(f"Warning: '{_interpreter_json_path}' not found or invalid. Interpreters will not be mapped automatically.")