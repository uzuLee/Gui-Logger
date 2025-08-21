"""
# ThinkCore 프로세스의 테스트 대리(Surrogate) 스크립트입니다.
# Test Surrogate for ThinkCore Process.

# 이 스크립트는 메인 'think_core' 프로세스의 출력을 시뮬레이션하여
# GUI가 로그를 올바르게 수신하고 표시하는지 테스트하는 데 사용됩니다.
# This script simulates the output of the main 'think_core' process
# and is used to test if the GUI correctly receives and displays logs.
"""

import time
import sys
import random
import argparse
from datetime import datetime
from pathlib import Path

def _check_pause(pause_flag_path: Path):
    """
    # 'pause.flag' 파일이 존재하면, 파일이 삭제될 때까지 대기합니다.
    # If the 'pause.flag' file exists, wait until the file is deleted.
    """
    # 플래그 파일의 부모 디렉토리가 존재하지 않으면 즉시 반환합니다.
    # If the parent directory of the flag file does not exist, return immediately.
    if not pause_flag_path.parent.exists():
        return

    paused_message_logged = False
    while pause_flag_path.exists():
        if not paused_message_logged:
            # 일시정지 상태임을 한 번만 로그로 남깁니다.
            # Log that the process is paused, but only once.
            log('SYSTEM', "Process is paused by GUI. Waiting for resume...")
            paused_message_logged = True
        time.sleep(1)
    
    # GUI에서도 동일한 메시지를 보내므로 중복을 피하기 위해 이 부분은 주석 처리하거나 삭제합니다.
    # if paused_message_logged:
    #     log('SYSTEM', "Process resumed.")

def log(level, message):
    """
    # 형식화된 로그 메시지를 출력하는 헬퍼 함수입니다.
    # Helper function to print formatted log messages.
    """
    timestamp = datetime.now().strftime('%H:%M:%S')
    print(f"[{timestamp}] [{level}] {message}")
    # 출력을 즉시 비워 GUI가 바로 수신할 수 있도록 합니다.
    # Flush the output immediately so the GUI can receive it.
    sys.stdout.flush()

# 명령줄 인수를 파싱합니다.
# Parse command-line arguments.
parser = argparse.ArgumentParser()
parser.add_argument("--data-dir", type=str, required=True, help="Path to the shared data directory for flags.")
args = parser.parse_args()
DATA_DIR = Path(args.data_dir)
PAUSE_FLAG_PATH = DATA_DIR / "pause.flag"
script_path = Path(__file__).resolve()

# 테스트 스크립트 시작을 알립니다.
# Announce the start of the test script.
log('SYSTEM', '--- Starting ThinkCore Test Surrogate ---')

# 출력할 로그 메시지의 사전 정의된 목록입니다.
# A predefined list of log messages to be printed.
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

# 사전 정의된 로그를 순회하며 출력합니다.
# Iterate through the predefined logs and print them.
for delay, level, msg in logs:
    _check_pause(PAUSE_FLAG_PATH) # 각 로그 출력 전 일시정지 상태를 확인합니다. (Check for pause state before printing each log.)
    time.sleep(delay)
    log(level, msg)

# --- 스피너 애니메이션 테스트 (Spinner Animation Test) ---
log('INFO', 'Starting a long task with a spinner animation...')
spinner_chars = ['|', '/', '-', '\\']
for i in range(40):
    _check_pause(PAUSE_FLAG_PATH) # 애니메이션의 각 프레임 전에 일시정지 상태를 확인합니다. (Check for pause state before each frame of the animation.)
    time.sleep(0.1) # 애니메이션이 보이도록 딜레이 추가
    char = spinner_chars[i % 4]
    progress_msg = f"[{datetime.now().strftime('%H:%M:%S')}] [PROGRESS] Thinking... {char}"
    
    # GUI가 각 프레임을 별도의 라인으로 인식하고 처리하도록 줄바꿈 문자를 보내줍니다.
    print(progress_msg, end='\n') 
    sys.stdout.flush()

# 애니메이션 종료 후 별도 줄바꿈이 필요 없어졌으므로 print() 제거
log('INFO', 'Spinner task complete.')


# --- 진행률 표시줄 애니메이션 테스트 (Progress Bar Animation Test) ---
log('INFO', 'Starting a task with a progress bar...')
for i in range(101):
    _check_pause(PAUSE_FLAG_PATH) # 진행률의 각 단계 전에 일시정지 상태를 확인합니다. (Check for pause state before each step of the progress.)
    time.sleep(0.02)
    bar = '█' * (i // 2) + '-' * (50 - (i // 2))
    # 여기도 마찬가지로 end_char를 항상 '\n'으로 설정하여 GUI가 각 단계를 수신하도록 합니다.
    end_char = '\n'
    progress_msg = f"[{datetime.now().strftime('%H:%M:%S')}] [PROGRESS] Processing batch: |{bar}| {i:.1f}% Complete"
    print(progress_msg, end=end_char)
    sys.stdout.flush()

log('SYSTEM', '--- ThinkCore Test Surrogate Finished ---')