// Test Surrogate for Logger Process (Node.js Version).
// Logger 프로세스의 테스트 대리 스크립트입니다 (Node.js 버전).

// This script simulates the output of a target process to test if the GUI
// correctly receives, displays, and handles various log formats and features.
// 이 스크립트는 대상 프로세스의 출력을 시뮬레이션하여 GUI가 다양한 로그 형식과 기능을
// 올바르게 수신하고 표시하며 처리하는지 테스트하는 데 사용됩니다.

const fs = require('fs');
const path = require('path');

// Helper for async sleep functionality.
// 비동기 sleep 기능을 위한 헬퍼 함수입니다.
const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));

// --- Initialization (초기화) ---

// Parse command-line arguments to get the data directory.
// 명령줄 인수를 파싱하여 데이터 디렉토리를 가져옵니다.
const args = process.argv.slice(2);
let dataDir = '';
const dataDirIndex = args.indexOf('--data-dir');
if (dataDirIndex !== -1 && args.length > dataDirIndex + 1) {
    dataDir = args[dataDirIndex + 1];
} else {
    console.error('Error: --data-dir argument is required.');
    process.exit(1);
}

const DATA_DIR = path.resolve(dataDir);
const PAUSE_FLAG_PATH = path.join(DATA_DIR, 'pause.flag');
const scriptPath = path.resolve(__filename);

/**
 * Helper function to print formatted log messages.
 * 형식화된 로그 메시지를 출력하는 헬퍼 함수입니다.
 * @param {string} level The log level.
 * @param {string} message The log message.
 */
function log(level, message) {
    const now = new Date();
    const timestamp = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}`;
    process.stdout.write(`[${timestamp}] [${level}] ${message}\n`);
}

/**
 * If the 'pause.flag' file exists, wait until the file is deleted.
 * 'pause.flag' 파일이 존재하면, 파일이 삭제될 때까지 대기합니다.
 */
async function checkPause() {
    if (!fs.existsSync(path.dirname(PAUSE_FLAG_PATH))) {
        return;
    }

    let pausedMessageLogged = false;
    while (fs.existsSync(PAUSE_FLAG_PATH)) {
        if (!pausedMessageLogged) {
            log('SYSTEM', "Process is paused by GUI. Waiting for resume...");
            pausedMessageLogged = true;
        }
        await sleep(1000);
    }
}


async function main() {
    log('SYSTEM', '--- Starting Logger Test Surrogate (Node.js) ---');

    // --- Log Simulation (로그 시뮬레이션) ---
    const logs = [
        { delay: 200, level: 'THINKING', msg: 'Initializing cognitive matrix...' },
        { delay: 200, level: 'DATA', msg: 'Loading initial dataset from cache... 5.2 MB loaded.' },
        { delay: 100, level: 'INFO', msg: 'Testing standard log levels...' },
        { delay: 100, level: 'TRACE', msg: 'This is a test message with level: TRACE' },
        { delay: 100, level: 'DEBUG', msg: 'Variable `x` is now 10.' },
        { delay: 100, level: 'INFO', msg: 'This is a test message with level: INFO' },
        { delay: 300, level: 'INFO', msg: `File link test. Click to open relative path: @${scriptPath}` },
        { delay: 300, level: 'INFO', msg: 'Web link test. For more info, visit https://www.github.com/uzuLee' },
        { delay: 300, level: 'THINKING', msg: 'Analyzing topic: "AI Ethics"' },
        { delay: 200, level: 'THINKING', msg: 'Hypothesis 1: Autonomy creates accountability gap.' },
        { delay: 100, level: 'WARNING', msg: 'Confidence score for hypothesis 1 is low (0.65).' },
        { delay: 500, level: 'AUDIT', msg: 'Security check passed for model access.' },
        { delay: 200, level: 'DATA', msg: 'Writing generated text to output buffer...' },
        { delay: 100, level: 'ERROR', msg: 'Failed to connect to external knowledge base.' },
        { delay: 100, level: 'FATAL', msg: 'Critical memory integrity failure. Aborting.' },
    ];

    for (const logItem of logs) {
        await checkPause();
        await sleep(logItem.delay);
        log(logItem.level, logItem.msg);
    }

    // --- Spinner Animation Test (스피너 애니메이션 테스트) ---
    log('INFO', 'Starting a long task with a spinner animation...');
    const spinnerChars = ['|', '/', '-', '\\'];
    for (let i = 0; i < 40; i++) {
        await checkPause();
        await sleep(100);
        const char = spinnerChars[i % 4];
        const now = new Date();
        const timestamp = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}`;
        process.stdout.write(`[${timestamp}] [PROGRESS] Thinking... ${char}\n`);
    }
    log('INFO', 'Spinner task complete.');


    // --- Progress Bar Animation Test (진행률 표시줄 애니메이션 테스트) ---
    log('INFO', 'Starting a task with a progress bar...');
    for (let i = 0; i <= 100; i++) {
        await checkPause();
        await sleep(20);
        const bar = '█'.repeat(Math.floor(i / 2)) + '-'.repeat(50 - Math.floor(i / 2));
        const now = new Date();
        const timestamp = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}`;
        process.stdout.write(`[${timestamp}] [PROGRESS] Processing batch: |${bar}| ${i.toFixed(1)}% Complete\n`);
    }

    log('SYSTEM', '--- Logger Test Surrogate (Node.js) Finished ---');
}

main();