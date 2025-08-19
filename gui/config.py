# E:\projectFiles\programming\.gemini-cli\glen_prototype\src\utils\logging_gui\gui\config.py
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

# 현재 파일의 절대 경로를 기준으로 기본 디렉토리를 설정합니다.
# Set the base directory relative to the absolute path of the current file.
_base_dir = os.path.dirname(os.path.abspath(__file__))

# 'data' 디렉토리의 경로를 정의합니다.
# Define the path to the 'data' directory.
DATA_DIR = os.path.join(_base_dir, "..", "..", "data")

# 'logs' 디렉토리의 경로를 정의합니다.
# Define the path to the 'logs' directory.
LOG_DIR = os.path.join(_base_dir, "..", "logs")

# 'pause.flag' 파일의 전체 경로를 정의합니다.
# Define the full path for the 'pause.flag' file.
PAUSE_FLAG_PATH = os.path.join(DATA_DIR, "pause.flag")

# 'run_think_core.py' 스크립트의 절대 경로를 정의합니다.
# 이것은 GUI가 하위 프로세스로 실행하는 메인 스크립트입니다.
# Define the absolute path to the 'run_think_core.py' script.
# This is the main script that the GUI launches as a subprocess.
THINK_CORE_SCRIPT_PATH = os.path.abspath(os.path.join(_base_dir, "..", "(Select File)"))

# 데이터 디렉토리가 존재하지 않으면 생성합니다.
# Create the data directory if it does not exist.
os.makedirs(DATA_DIR, exist_ok=True)

# 로그 디렉토리가 존재하지 않으면 생성합니다.
# Create the log directory if it does not exist.
os.makedirs(LOG_DIR, exist_ok=True)
