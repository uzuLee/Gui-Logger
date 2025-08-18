# E:\projectFiles\programming\.gemini-cli\glen_prototype\src\utils\logging_gui\gui\run_think_core.py
"""
Test Surrogate for ThinkCore Process.

This script simulates the output of the main 'think_core' process. It is used
for testing and demonstrating the capabilities of the LogDisplay GUI without
needing to run the actual, potentially complex, backend process.

It generates a variety of log messages at different levels and formats,
including hyperlink detection, spinner animations, and progress bars.
"""

import time
import sys

# Announce the start of the test script.
print('--- Starting ThinkCore Test Surrogate ---')
sys.stdout.flush() # Ensure the message is sent immediately.

# A predefined list of log messages to be printed.
# Each tuple contains the delay before printing and the message string.
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
    # This line demonstrates the file path link detection feature of the GUI.
    (0.1, r'[INFO] File link: Click to open file/folder -> "@E:\\projectFiles\\programming\\.gemini-cli\\glen_prototype\\src\\scripts\\run_think_core.py"'),
]

# Iterate through the predefined logs and print them.
for delay, msg in logs:
    time.sleep(delay)
    print(msg)
    sys.stdout.flush()

# --- Spinner Animation Test ---
print('[INFO] Starting a task with a spinner animation...')
sys.stdout.flush()
spinner = ['|', '/', '-', '\']
for i in range(20):
    time.sleep(0.1)
    # Print a PROGRESS log with a carriage return `\r` to create an animation.
    # The GUI's progress label will be updated on each print.
    print(f'[PROGRESS] Processing item {i+1}/20... {spinner[i%4]}', end='\r')
    sys.stdout.flush()

# Print a newline to move to the next line after the spinner is done.
print('\n[INFO] Spinner task complete.')
sys.stdout.flush()

# --- Progress Bar Animation Test ---
print('[INFO] Starting a task with a progress bar...')
sys.stdout.flush()
for i in range(101):
    time.sleep(0.02)
    # Create a text-based progress bar.
    bar = '█' * (i // 2) + '-' * (50 - (i // 2))
    # Use carriage return to keep the progress bar on the same line.
    end_char = '\r' if i < 100 else '\n'
    print(f'[PROGRESS] Downloading file: |{bar}| {i:.1f}% Complete', end=end_char)
    sys.stdout.flush()

print('[INFO] Progress bar task complete.')
sys.stdout.flush()