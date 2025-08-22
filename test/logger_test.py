"""
# Test Surrogate for Logger Process (Python Version).
# Logger 프로세스의 테스트 대리 스크립트입니다 (Python 버전).

# This script simulates the output of a target process to test if the GUI
# correctly receives, displays, and handles various log formats and features.
# 이 스크립트는 대상 프로세스의 출력을 시뮬레이션하여 GUI가 다양한 로그 형식과 기능을
# 올바르게 수신하고 표시하며 처리하는지 테스트하는 데 사용됩니다.
"""

import time
import sys
import argparse
from datetime import datetime
from pathlib import Path

def _check_pause(pause_flag_path: Path):
    """
    # If the 'pause.flag' file exists, wait until the file is deleted.
    # 'pause.flag' 파일이 존재하면, 파일이 삭제될 때까지 대기합니다.
    """
    if not pause_flag_path.parent.exists():
        return

    paused_message_logged = False
    while pause_flag_path.exists():
        if not paused_message_logged:
            log('SYSTEM', "Process is paused by GUI. Waiting for resume...")
            paused_message_logged = True
        time.sleep(1)

def log(level, message):
    """
    # Helper function to print formatted log messages.
    # 형식화된 로그 메시지를 출력하는 헬퍼 함수입니다.
    """
    timestamp = datetime.now().strftime('%H:%M:%S')
    print(f"[{timestamp}] [{level}] {message}")
    sys.stdout.flush()

# --- Initialization (초기화) ---
parser = argparse.ArgumentParser(description="Test surrogate for the Glen Log Viewer.")
parser.add_argument("--data-dir", type=str, required=True, help="Path to the shared data directory for flags.")
args = parser.parse_args()
DATA_DIR = Path(args.data_dir)
PAUSE_FLAG_PATH = DATA_DIR / "pause.flag"
script_path = Path(__file__).resolve()

log('SYSTEM', '--- Starting Logger Test Surrogate (Python) ---')

# --- Log Simulation (로그 시뮬레이션) ---
logs = [
    (0.2, 'THINKING', 'Initializing cognitive matrix...'),
    (0.2, 'DATA', 'Loading initial dataset from cache... 5.2 MB loaded.'),
    (0.1, 'INFO', 'Testing standard log levels...'),
    (0.1, 'TRACE', 'This is a test message with level: TRACE'),
    (0.1, 'DEBUG', 'Variable `x` is now 10.'),
    (0.1, 'INFO', 'This is a test message with level: INFO'),
    (0.3, 'INFO', f'File link test. Click to open relative path: @{script_path}'),
    (0.3, 'INFO', 'Web link test. For more info, visit https://www.github.com/uzuLee'),
    (0.3, 'THINKING', 'Analyzing topic: "AI Ethics"'),
    (0.2, 'THINKING', 'Hypothesis 1: Autonomy creates accountability gap.'),
    (0.1, 'WARNING', 'Confidence score for hypothesis 1 is low (0.65).'),
    (0.5, 'AUDIT', 'Security check passed for model access.'),
    (0.2, 'DATA', 'Writing generated text to output buffer...'),
    (0.1, 'ERROR', 'Failed to connect to external knowledge base.'),
    (0.1, 'FATAL', 'Critical memory integrity failure. Aborting.'),
]

for delay, level, msg in logs:
    _check_pause(PAUSE_FLAG_PATH)
    time.sleep(delay)
    log(level, msg)

# --- Spinner Animation Test (스피너 애니메이션 테스트) ---
log('INFO', 'Starting a long task with a spinner animation...')
spinner_chars = ['|', '/', '-', '\\']
for i in range(40):
    _check_pause(PAUSE_FLAG_PATH)
    time.sleep(0.1)
    char = spinner_chars[i % 4]
    progress_msg = f"[{datetime.now().strftime('%H:%M:%S')}] [PROGRESS] Thinking... {char}"
    print(progress_msg, end='\n') 
    sys.stdout.flush()
log('INFO', 'Spinner task complete.')

# --- Progress Bar Animation Test (진행률 표시줄 애니메이션 테스트) ---
log('INFO', 'Starting a task with a progress bar...')
for i in range(101):
    _check_pause(PAUSE_FLAG_PATH)
    time.sleep(0.02)
    bar = '█' * (i // 2) + '-' * (50 - (i // 2))
    progress_msg = f"[{datetime.now().strftime('%H:%M:%S')}] [PROGRESS] Processing batch: |{bar}| {i:.1f}% Complete"
    print(progress_msg, end='\n')
    sys.stdout.flush()

log('SYSTEM', '--- Logger Test Surrogate (Python) Finished ---')
