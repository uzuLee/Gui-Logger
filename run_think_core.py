import time
import sys
import os

# GUI의 config.py와 동일한 로직으로 pause flag 경로 설정
# 이 스크립트는 glen_prototype/src/utils/logging_gui/ 디렉토리에서 실행되므로,
# pause.flag가 생성되는 data 폴더의 상대 경로를 정확히 지정해야 합니다.
PAUSE_FLAG_PATH = os.path.join("src", "utils", "data", "pause.flag")

def check_pause():
    """Pause a while if pause flag exists."""
    if os.path.exists(PAUSE_FLAG_PATH):
        # Pause 상태에 진입했음을 명시적으로 알리고 싶다면 아래 주석을 해제하세요.
        # print("[SYSTEM] Script paused.", flush=True)
        while os.path.exists(PAUSE_FLAG_PATH):
            time.sleep(0.5)
        # Resume 상태에 진입했음을 명시적으로 알리고 싶다면 아래 주석을 해제하세요.
        # print("[SYSTEM] Script resumed.", flush=True)

print('--- Starting ThinkCore Test Surrogate ---')
sys.stdout.flush()

logs = [
    (0.1, '[INFO] Testing all log levels...'),
    (0.1, '[TRACE] This is a test message with level: TRACE'),
    (0.1, '[DEBUG] This is a test message with level: DEBUG'),
    (0.1, '[INFO] This is a test message with level: INFO'),
    (0.1, '[WARNING] This is a test message with level: WARNING'),
    (0.1, '[ERROR] This is a test message with level: ERROR'),
    (0.1, '[FATAL] This is a test message with level: FATAL'),
    (0.1, '[COMMENT] This is a test message with level: COMMENT'),
    (0.1, '[INFO] Testing hyperlink detection...'),
        (0.1, f'[INFO] File link: Click to open file/folder -> "@{os.path.abspath(__file__).replace('', '')}"'),
    (0.1, '[INFO] Website link: Click to open browser -> https://www.github.com/uzuLee')
]
for delay, msg in logs:
    check_pause()
    time.sleep(delay)
    print(msg)
    sys.stdout.flush()

print('[INFO] Starting a task with a spinner animation...')
sys.stdout.flush()
spinner = ['|', '/', '-', '\\']
for i in range(20):
    check_pause()
    time.sleep(0.1)
    print(f'[PROGRESS] Processing item {i+1}/20... {spinner[i%4]}', end='\r')
    sys.stdout.flush()

print('\n[INFO] Spinner task complete.')
sys.stdout.flush()

print('[INFO] Starting a task with a progress bar...')
sys.stdout.flush()
for i in range(101):
    check_pause()
    time.sleep(0.02)
    bar = '█' * (i // 2) + '-' * (50 - (i // 2))
    end_char = '\r' if i < 100 else '\n'
    print(f'[PROGRESS] Downloading file: |{bar}| {i:.1f}% Complete', end=end_char)
    sys.stdout.flush()

print('[INFO] Progress bar task complete.')
sys.stdout.flush()