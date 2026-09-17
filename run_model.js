import { spawn, spawnSync } from 'child_process';
import fs from 'fs';
import path from 'path';
import process from 'process';

const isWindows = process.platform === 'win32';
const pythonCmd = isWindows ? 'python' : 'python3';
const pipCmd = isWindows ? 'pip' : 'pip3';
const npmCmd = isWindows ? 'npm.cmd' : 'npm';

const forceInstall = process.argv.includes('--install') || process.argv.includes('-i');

console.clear();
console.log('\x1b[36m%s\x1b[0m', '================================================================');
console.log('\x1b[1m\x1b[34m%s\x1b[0m', '            🌊  NEERMITRA MARINE INTELLIGENCE PLATFORM  🌊');
console.log('\x1b[36m%s\x1b[0m', '================================================================');
console.log('');

// Pre-flight dependency check (Auto-installs if requirements are missing)
function ensureDependencies() {
  let needsPythonInstall = forceInstall;

  if (!needsPythonInstall) {
    const check = spawnSync(`${pythonCmd} -c "import fastapi, uvicorn, pydantic"`, {
      shell: true,
      stdio: 'ignore'
    });
    if (check.status !== 0) {
      needsPythonInstall = true;
    }
  }

  if (needsPythonInstall) {
    console.log('\x1b[33m%s\x1b[0m', '📦 Missing Python dependencies detected!');
    const reqFile = fs.existsSync(path.join(process.cwd(), 'server', 'requirements.txt'))
      ? path.join('server', 'requirements.txt')
      : fs.existsSync(path.join(process.cwd(), 'backend', 'requirements.txt'))
      ? path.join('backend', 'requirements.txt')
      : 'requirements.txt';

    console.log('\x1b[36m%s\x1b[0m', `⏳ Installing packages from ${reqFile} via ${pipCmd}...`);
    const pipResult = spawnSync(`${pipCmd} install -r ${reqFile}`, {
      shell: true,
      stdio: 'inherit'
    });

    if (pipResult.status === 0) {
      console.log('\x1b[32m%s\x1b[0m', '✅ Python requirements successfully installed!\n');
    } else {
      console.log('\x1b[31m%s\x1b[0m', '⚠️  Warning: pip install encountered an issue. Attempting to start server...\n');
    }
  }

  // Check frontend node_modules
  const nodeModulesPath = path.join(process.cwd(), 'node_modules');
  if (!fs.existsSync(nodeModulesPath) || forceInstall) {
    console.log('\x1b[33m%s\x1b[0m', '📦 Frontend node_modules not detected. Installing via npm install...');
    spawnSync(`${npmCmd} install`, {
      shell: true,
      stdio: 'inherit'
    });
    console.log('\x1b[32m%s\x1b[0m', '✅ Frontend dependencies successfully installed!\n');
  }
}

ensureDependencies();

console.log('\x1b[32m%s\x1b[0m', '  🚀 Starting Backend & Frontend services in parallel...\n');

// 1. Launch Backend (FastAPI with modular server / legacy fallback)
const backendCmd = `${pythonCmd} -m uvicorn server.src.app:app --reload --port 8000`;
const backend = spawn(backendCmd, {
  shell: true,
  stdio: ['inherit', 'pipe', 'pipe'],
  env: { ...process.env, PYTHONPATH: process.cwd() }
});

// 2. Launch Frontend (Vite)
const frontendCmd = `${npmCmd} run dev`;
const frontend = spawn(frontendCmd, {
  shell: true,
  stdio: ['inherit', 'pipe', 'pipe']
});

let frontendUrl = 'http://localhost:5173';
let shownBanner = false;

function printReadyBanner() {
  if (shownBanner) return;
  shownBanner = true;

  setTimeout(() => {
    console.log('\n\x1b[36m%s\x1b[0m', '----------------------------------------------------------------');
    console.log('\x1b[1m\x1b[32m%s\x1b[0m', '  ✨ NEERMITRA SYSTEM READY & ACTIVE!');
    console.log('\x1b[36m%s\x1b[0m', '----------------------------------------------------------------');
    console.log(`  🌐 \x1b[1mFrontend Web App:\x1b[0m       \x1b[36m\x1b[4m${frontendUrl}\x1b[0m`);
    console.log('  📡 \x1b[1mFastAPI Backend:\x1b[0m        \x1b[34m\x1b[4mhttp://localhost:8000\x1b[0m');
    console.log('  📖 \x1b[1mAPI Documentation:\x1b[0m      \x1b[33m\x1b[4mhttp://localhost:8000/docs\x1b[0m');
    console.log('  🗺️  \x1b[1mNearest PFZ Service:\x1b[0m    \x1b[32m\x1b[4mhttp://localhost:8000/api/geo/nearest-pfz\x1b[0m');
    console.log('\x1b[36m%s\x1b[0m', '----------------------------------------------------------------');
    console.log('  \x1b[90mPress [Ctrl + C] anytime to shut down both servers.\x1b[0m\n');
  }, 1200);
}

// Pipe outputs with friendly colored tags
backend.stdout.on('data', (data) => {
  const line = data.toString();
  process.stdout.write(`\x1b[34m[Backend]\x1b[0m ${line}`);
  if (line.includes('Uvicorn running') || line.includes('Application startup complete')) {
    printReadyBanner();
  }
});

backend.stderr.on('data', (data) => {
  const line = data.toString();
  // Filter benign info lines logged on stderr by uvicorn
  if (line.includes('INFO:') || line.includes('Started server process') || line.includes('Application startup complete')) {
    process.stdout.write(`\x1b[34m[Backend]\x1b[0m ${line}`);
    printReadyBanner();
  } else {
    process.stderr.write(`\x1b[31m[Backend Err]\x1b[0m ${line}`);
  }
});

frontend.stdout.on('data', (data) => {
  const raw = data.toString();
  process.stdout.write(`\x1b[32m[Frontend]\x1b[0m ${raw}`);

  const cleanLine = raw.replace(/\x1b\[[0-9;]*m/g, '');
  const match = cleanLine.match(/http:\/\/(?:localhost|127\.0\.0\.1):\d+/);
  if (match) {
    frontendUrl = match[0];
  }

  if (cleanLine.includes('Local:') || cleanLine.includes('localhost:')) {
    printReadyBanner();
  }
});

frontend.stderr.on('data', (data) => {
  process.stderr.write(`\x1b[33m[Frontend Warn]\x1b[0m ${data}`);
});

// Fallback banner trigger in case outputs are buffered
setTimeout(printReadyBanner, 2500);

// Graceful cleanup on exit
function shutdown() {
  console.log('\n\x1b[33m%s\x1b[0m', '🛑 Shutting down NeerMitra Frontend and Backend...');

  if (isWindows) {
    if (backend.pid) spawn('taskkill', ['/pid', backend.pid.toString(), '/f', '/t']);
    if (frontend.pid) spawn('taskkill', ['/pid', frontend.pid.toString(), '/f', '/t']);
  } else {
    backend.kill('SIGTERM');
    frontend.kill('SIGTERM');
  }

  setTimeout(() => {
    console.log('\x1b[32m%s\x1b[0m', '✅ All processes stopped.');
    process.exit(0);
  }, 500);
}

process.on('SIGINT', shutdown);
process.on('SIGTERM', shutdown);
