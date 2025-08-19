# E:\projectFiles\programming\.gemini-cli\glen_prototype\src\utils\logging_gui\gui\utils.py
"""
# 로깅 GUI 애플리케이션을 위한 유틸리티 함수 모음입니다.
# Utility functions for the logging GUI application.

# 이 모듈은 로깅 설정을 시작으로 메인 애플리케이션을 지원하는 헬퍼 함수를 제공합니다.
# 애플리케이션이 성장함에 따라 다른 재사용 가능한 유틸리티를 포함하도록 확장될 수 있습니다.
# This module provides helper functions that support the main application,
# starting with logging configuration. This can be expanded to include other
# reusable utilities as the application grows.
"""

import os
import sys
import logging
import logging.handlers
from datetime import datetime
from .config import LOG_DIR

def setup_logging():
    """
    # GUI 애플리케이션 자체를 위한 루트 로거를 설정합니다.
    # Sets up the root logger for the GUI application itself.
    """
    # 로그 파일 경로를 생성합니다. 파일 이름에는 현재 타임스탬프가 포함됩니다.
    # Create the log file path. The filename includes the current timestamp.
    log_file = os.path.join(LOG_DIR, f"glen_log_viewer_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    
    # 로그 메시지 형식을 정의합니다.
    # Define the format for log messages.
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
    # 파일 핸들러를 설정합니다. 로그 파일이 10MB에 도달하면 새 파일이 생성되고, 최대 5개의 백업 파일이 유지됩니다.
    # Set up the file handler. A new file is created when the log file reaches 10MB, and up to 5 backup files are kept.
    file_handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=10*1024*1024, backupCount=5, encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    
    # 콘솔 핸들러를 설정하여 로그 메시지를 표준 출력으로도 보냅니다.
    # Set up the console handler to also send log messages to standard output.
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # 루트 로거를 가져와 설정된 핸들러들을 추가하고, 로깅 레벨을 INFO로 설정합니다.
    # Get the root logger, add the configured handlers, and set the logging level to INFO.
    root_logger = logging.getLogger()
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    root_logger.setLevel(logging.INFO)
