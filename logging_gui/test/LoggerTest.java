
// Logger 프로세스의 테스트 대리(Surrogate) 스크립트입니다. (Java 버전)
// Test Surrogate for Logger Process. (Java Version)

import java.io.File;
import java.io.IOException;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.concurrent.TimeUnit;

public class LoggerTest {

    private static String dataDir = "";

    /**
     * 형식화된 로그 메시지를 출력하는 헬퍼 함수입니다.
     * Helper function to print formatted log messages.
     */
    private static void log(String level, String message) {
        String timestamp = new SimpleDateFormat("HH:mm:ss").format(new Date());
        System.out.printf("[%s] [%s] %s\n", timestamp, level, message);
        System.out.flush();
    }

    /**
     * 'pause.flag' 파일이 존재하면, 파일이 삭제될 때까지 대기합니다.
     * If the 'pause.flag' file exists, wait until the file is deleted.
     */
    private static void checkPause(Path pauseFlagPath) throws InterruptedException {
        if (!pauseFlagPath.getParent().toFile().exists()) {
            return;
        }

        boolean pausedMessageLogged = false;
        while (pauseFlagPath.toFile().exists()) {
            if (!pausedMessageLogged) {
                log("SYSTEM", "Process is paused by GUI. Waiting for resume...");
                pausedMessageLogged = true;
            }
            TimeUnit.SECONDS.sleep(1);
        }
    }

    private static class LogEntry {
        long delay;
        String level;
        String message;

        LogEntry(long delay, String level, String message) {
            this.delay = delay;
            this.level = level;
            this.message = message;
        }
    }

    public static void main(String[] args) throws InterruptedException {
        for (int i = 0; i < args.length; i++) {
            if ("--data-dir".equals(args[i]) && i + 1 < args.length) {
                dataDir = args[i + 1];
                break;
            }
        }

        if (dataDir.isEmpty()) {
            System.err.println("Error: --data-dir argument is required.");
            System.exit(1);
        }

        Path dataDirPath = Paths.get(dataDir).toAbsolutePath();
        Path pauseFlagPath = dataDirPath.resolve("pause.flag");
        String scriptPath = "";
        try {
            scriptPath = new File(LoggerTest.class.getProtectionDomain().getCodeSource().getLocation().toURI()).getPath();
        } catch (Exception e) {
            scriptPath = "LoggerTest.jar";
        }


        log("SYSTEM", "--- Starting Logger Test Surrogate (Java) ---");

        LogEntry[] logs = new LogEntry[]{
            new LogEntry(200, "THINKING", "Initializing cognitive matrix..."),
            new LogEntry(200, "DATA", "Loading initial dataset from cache... 5.2 MB loaded."),
            new LogEntry(100, "INFO", "Testing standard log levels..."),
            new LogEntry(100, "TRACE", "This is a test message with level: TRACE"),
            new LogEntry(100, "DEBUG", "Variable `x` is now 10."),
            new LogEntry(100, "INFO", "This is a test message with level: INFO"),
            new LogEntry(300, "INFO", "File link test. Click to open relative path: @" + scriptPath),
            new LogEntry(300, "INFO", "Web link test. For more info, visit https://www.github.com/uzuLee"),
            new LogEntry(300, "THINKING", "Analyzing topic: \"AI Ethics\""),
            new LogEntry(200, "THINKING", "Hypothesis 1: Autonomy creates accountability gap."),
            new LogEntry(100, "WARNING", "Confidence score for hypothesis 1 is low (0.65)."),
            new LogEntry(500, "AUDIT", "Security check passed for model access."),
            new LogEntry(200, "DATA", "Writing generated text to output buffer..."),
            new LogEntry(100, "ERROR", "Failed to connect to external knowledge base."),
            new LogEntry(100, "FATAL", "Critical memory integrity failure. Aborting.")
        };

        for (LogEntry entry : logs) {
            checkPause(pauseFlagPath);
            TimeUnit.MILLISECONDS.sleep(entry.delay);
            log(entry.level, entry.message);
        }

        // --- Spinner Animation Test ---
        log("INFO", "Starting a long task with a spinner animation...");
        char[] spinnerChars = {'|', '/', '-', '\\'};
        for (int i = 0; i < 40; i++) {
            checkPause(pauseFlagPath);
            TimeUnit.MILLISECONDS.sleep(100);
            char c = spinnerChars[i % 4];
            String timestamp = new SimpleDateFormat("HH:mm:ss").format(new Date());
            System.out.printf("[%s] [PROGRESS] Thinking... %c\n", timestamp, c);
            System.out.flush();
        }
        log("INFO", "Spinner task complete.");


        // --- Progress Bar Animation Test ---
        log("INFO", "Starting a task with a progress bar...");
        for (int i = 0; i <= 100; i++) {
            checkPause(pauseFlagPath);
            TimeUnit.MILLISECONDS.sleep(20);
            int barFilled = i / 2;
            StringBuilder bar = new StringBuilder();
            for(int j=0; j < barFilled; j++) bar.append("█");
            for(int j=0; j < 50 - barFilled; j++) bar.append("-");
            String timestamp = new SimpleDateFormat("HH:mm:ss").format(new Date());
            System.out.printf("[%s] [PROGRESS] Processing batch: |%s| %.1f%% Complete\n", timestamp, bar.toString(), (double)i);
            System.out.flush();
        }

        log("SYSTEM", "--- Logger Test Surrogate (Java) Finished ---");
    }
}
