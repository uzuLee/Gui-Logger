
// Logger 프로세스의 테스트 대리(Surrogate) 스크립트입니다. (Go 버전)
// Test Surrogate for Logger Process. (Go Version)

package main

import (
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"time"
)

var dataDir = flag.String("data-dir", "", "Path to the shared data directory for flags.")

// 형식화된 로그 메시지를 출력하는 헬퍼 함수입니다.
// Helper function to print formatted log messages.
func log(level, message string) {
	timestamp := time.Now().Format("15:04:05")
	fmt.Printf("[%s] [%s] %s\n", timestamp, level, message)
}

// 'pause.flag' 파일이 존재하면, 파일이 삭제될 때까지 대기합니다.
// If the 'pause.flag' file exists, wait until the file is deleted.
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

type LogEntry struct {
	Delay   time.Duration
	Level   string
	Message string
}

func main() {
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

	// --- Spinner Animation Test ---
	log("INFO", "Starting a long task with a spinner animation...")
	spinnerChars := []rune{'|', '/', '-', '\\'}
	for i := 0; i < 40; i++ {
		checkPause(pauseFlagPath)
		time.Sleep(100 * time.Millisecond)
		char := spinnerChars[i%4]
		timestamp := time.Now().Format("15:04:05")
		fmt.Printf("[%s] [PROGRESS] Thinking... %c\n", timestamp, char)
	}
	log("INFO", "Spinner task complete.")

	// --- Progress Bar Animation Test ---
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
