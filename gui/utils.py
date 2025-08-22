
"""
# Utility functions for the logging GUI application.
# 로깅 GUI 애플리케이션을 위한 유틸리티 함수 모음입니다.

# This module provides helper functions that support the main application.
# 이 모듈은 메인 애플리케이션을 지원하는 헬퍼 함수를 제공합니다.
"""

import os
import sys
import logging
import logging.handlers
import shutil
from datetime import datetime
from .config import LOG_DIR
from typing import List, Optional

def setup_logging():
    """
    # Sets up the root logger for the GUI application itself, not the monitored script.
    # 모니터링되는 스크립트가 아닌, GUI 애플리케이션 자체를 위한 루트 로거를 설정합니다.
    """
    # Create the log file path. The filename includes the current timestamp.
    # 로그 파일 경로를 생성합니다. 파일 이름에는 현재 타임스탬프가 포함됩니다.
    log_file = os.path.join(LOG_DIR, f"glen_log_viewer_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    
    # Define the format for log messages.
    # 로그 메시지 형식을 정의합니다.
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
    # Set up a rotating file handler.
    # 순환 파일 핸들러를 설정합니다.
    file_handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=10*1024*1024, backupCount=5, encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    
    # Set up the console handler to also send log messages to standard output.
    # 로그 메시지를 표준 출력으로도 보내도록 콘솔 핸들러를 설정합니다.
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # Get the root logger, add the configured handlers, and set the logging level.
    # 루트 로거를 가져와 설정된 핸들러들을 추가하고, 로깅 레벨을 설정합니다.
    root_logger = logging.getLogger()
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    root_logger.setLevel(logging.INFO)

def find_interpreter(commands: List[str]) -> Optional[str]:
    """
    # Finds the first available executable from a list of commands in the system's PATH.
    # 주어진 명령어 리스트에서 시스템의 PATH에 존재하는 첫 번째 실행 파일을 찾습니다.

    # Args:
    #     commands (List[str]): A list of command names to search for (e.g., ['python3', 'python']).
    #                           (검색할 명령어 이름의 리스트, 예: ['python3', 'python'])

    # Returns:
    #     Optional[str]: The full path to the found executable, or None if not found.
    #                    (찾은 실행 파일의 전체 경로, 찾지 못한 경우 None)
    """
    for cmd in commands:
        if shutil.which(cmd):
            return cmd
    return None
