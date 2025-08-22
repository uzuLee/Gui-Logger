// Test Surrogate for Logger Process (Go Version).
// Logger 프로세스의 테스트 대리 스크립트입니다 (Go 버전).

// This script simulates the output of a target process to test if the GUI
// correctly receives, displays, and handles various log formats and features.
// 이 스크립트는 대상 프로세스의 출력을 시뮬레이션하여 GUI가 다양한 로그 형식과 기능을
// 올바르게 수신하고 표시하며 처리하는지 테스트하는 데 사용됩니다.
package main

import (
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"time"
)

// Command-line flag for the shared data directory.
// 공유 데이터 디렉토리를 위한 명령줄 플래그입니다.
var dataDir = flag.String("data-dir", "", "Path to the shared data directory for flags.")

// log prints a formatted log message to standard output.
// log 함수는 형식화된 로그 메시지를 표준 출력으로 인쇄합니다.
func log(level, message string) {
	timestamp := time.Now().Format("15:04:05")
	fmt.Printf("[%s] [%s] %s\n", timestamp, level, message)
}

// checkPause waits until the 'pause.flag' file is deleted.
// checkPause 함수는 'pause.flag' 파일이 삭제될 때까지 대기합니다.
func checkPause(pauseFlagPath string) {
	if _, err := os.Stat(filepath.Dir(pauseFlagPath)); os.IsNotExist(err) {
		return
	}

	pausedMessageLogged := false
	for {
		if _, err := os.Stat(pauseFlagPath); os.IsNotExist(err) {
			break
		}
		if !pausedMessageLogged {
			log("SYSTEM", "Process is paused by GUI. Waiting for resume...")
			pausedMessageLogged = true
		}
		time.Sleep(1 * time.Second)
	}
}

// LogEntry defines the structure for a simulated log message.
// LogEntry는 시뮬레이션된 로그 메시지의 구조를 정의합니다.
type LogEntry struct {
	Delay   time.Duration
	Level   string
	Message string
}

func main() {
	// --- Initialization (초기화) ---
	flag.Parse()
	if *dataDir == "" {
		fmt.Fprintln(os.Stderr, "Error: --data-dir argument is required.")
		os.Exit(1)
	}

	dataDirPath, err := filepath.Abs(*dataDir)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error resolving data-dir path: %v\n", err)
		os.Exit(1)
	}
	pauseFlagPath := filepath.Join(dataDirPath, "pause.flag")
	scriptPath, _ := filepath.Abs(os.Args[0])

	log("SYSTEM", "--- Starting Logger Test Surrogate (Go) ---")

	// --- Log Simulation (로그 시뮬레이션) ---
	logs := []LogEntry{
		{200 * time.Millisecond, "THINKING", "Initializing cognitive matrix..."},
		{200 * time.Millisecond, "DATA", "Loading initial dataset from cache... 5.2 MB loaded."},
		{100 * time.Millisecond, "INFO", "Testing standard log levels..."},
		{100 * time.Millisecond, "TRACE", "This is a test message with level: TRACE"},
		{100 * time.Millisecond, "DEBUG", "Variable `x` is now 10."},
		{100 * time.Millisecond, "INFO", "This is a test message with level: INFO"},
		{300 * time.Millisecond, "INFO", fmt.Sprintf("File link test. Click to open relative path: @%s", scriptPath)},
		{300 * time.Millisecond, "INFO", "Web link test. For more info, visit https://www.github.com/uzuLee"},
		{300 * time.Millisecond, "THINKING", "Analyzing topic: \"AI Ethics\""},
		{200 * time.Millisecond, "THINKING", "Hypothesis 1: Autonomy creates accountability gap."},
		{100 * time.Millisecond, "WARNING", "Confidence score for hypothesis 1 is low (0.65)."},
		{500 * time.Millisecond, "AUDIT", "Security check passed for model access."},
		{200 * time.Millisecond, "DATA", "Writing generated text to output buffer..."},
		{100 * time.Millisecond, "ERROR", "Failed to connect to external knowledge base."},
		{100 * time.Millisecond, "FATAL", "Critical memory integrity failure. Aborting."},
	}

	for _, entry := range logs {
		checkPause(pauseFlagPath)
		time.Sleep(entry.Delay)
		log(entry.Level, entry.Message)
	}

	// --- Spinner Animation Test (스피너 애니메이션 테스트) ---
	log("INFO", "Starting a long task with a spinner animation...")
	spinnerChars := []rune{'|', '/', '-', '\'}
	for i := 0; i < 40; i++ {
		checkPause(pauseFlagPath)
		time.Sleep(100 * time.Millisecond)
		char := spinnerChars[i%4]
		timestamp := time.Now().Format("15:04:05")
		fmt.Printf("[%s] [PROGRESS] Thinking... %c\n", timestamp, char)
	}
	log("INFO", "Spinner task complete.")

	// --- Progress Bar Animation Test (진행률 표시줄 애니메이션 테스트) ---
	log("INFO", "Starting a task with a progress bar...")
	for i := 0; i <= 100; i++ {
		checkPause(pauseFlagPath)
		time.Sleep(20 * time.Millisecond)
		barFilled := i / 2
		bar := ""
		for j := 0; j < barFilled; j++ {
			bar += "█"
		}
		for j := 0; j < 50-barFilled; j++ {
			bar += "-"
		}
		timestamp := time.Now().Format("15:04:05")
		fmt.Printf("[%s] [PROGRESS] Processing batch: |%s| %.1f%% Complete\n", timestamp, bar, float64(i))
	}

	log("SYSTEM", "--- Logger Test Surrogate (Go) Finished ---")
}