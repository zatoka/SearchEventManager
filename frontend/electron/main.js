const { app, BrowserWindow, shell } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs');

let mainWindow;
let pythonProcess;

// Create log file
const logPath = path.join(app.getPath('userData'), 'app.log');
function log(message) {
  const timestamp = new Date().toISOString();
  const logMessage = `[${timestamp}] ${message}\n`;
  fs.appendFileSync(logPath, logMessage);
  console.log(logMessage);
}

log('GREG TEST 123 - MAIN.JS CHECK');
log(`Log file: ${logPath}`);
log(`app.isPackaged: ${app.isPackaged}`);
log(`__dirname: ${__dirname}`);

function startPythonBackend() {
  let backendExe;
  let backendPath;

  if (app.isPackaged) {
    backendPath = path.join(process.resourcesPath, 'backend', 'SearchEventsBackend');
    backendExe = path.join(backendPath, 'SearchEventsBackend.exe');
  } else {
    backendPath = path.join(__dirname, '..', '..', 'backend');
    backendExe = path.join(backendPath, 'venv', 'Scripts', 'python.exe');
  }

  log('[Backend] Starting: ' + backendExe);
  log('[Backend] Working directory: ' + backendPath);
  log('[Backend] File exists: ' + fs.existsSync(backendExe));

  const args = app.isPackaged 
    ? ['--host', '127.0.0.1', '--port', '8002']
    : ['-m', 'uvicorn', 'main:app', '--host', '127.0.0.1', '--port', '8002'];

  pythonProcess = spawn(backendExe, args, {
    cwd: backendPath,
    stdio: 'pipe',
    shell: false,
  });

  pythonProcess.stdout.on('data', (data) => {
    log(`[Backend STDOUT] ${data}`);
  });

  pythonProcess.stderr.on('data', (data) => {
    log(`[Backend STDERR] ${data}`);
  });

  pythonProcess.on('close', (code) => {
    log(`[Backend] exited with code ${code}`);
  });
  
  pythonProcess.on('error', (err) => {
    log(`[Backend ERROR] ${err.message}`);
  });
}

function waitForBackend() {
  return new Promise((resolve) => {
    const http = require('http');
    let attempts = 0;
    const maxAttempts = 30;
    
    const check = () => {
      log(`Checking backend health... attempt ${attempts + 1}`);
      const req = http.get('http://localhost:8002/health', (res) => {
        log(`Health check response: ${res.statusCode}`);
        if (res.statusCode === 200) {
          log('[DEBUG] Health check succeeded; resolving true');
          resolve(true);
        } else {
          retry();
        }
      });
      req.on('error', (err) => {
        log(`Health check error: ${err.message}`);
        retry();
      });
      req.setTimeout(1000, () => {
        req.destroy();
        retry();
      });
    };
    
    const retry = () => {
      attempts++;
      if (attempts < maxAttempts) {
        setTimeout(check, 1000);
      } else {
        log('Max attempts reached, backend not ready');
        resolve(false);
      }
    };
    
    check();
  });
}


function createWindow() {
  log('Creating window...');

  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true
    }
  });

  mainWindow.webContents.setWindowOpenHandler(({ url: linkUrl }) => {
    shell.openExternal(linkUrl);
    return { action: 'deny' };
  });

  mainWindow.webContents.on('did-fail-load', (event, errorCode, errorDescription) => {
    log(`Failed to load: ${errorCode} - ${errorDescription}`);
  });

  if (!app.isPackaged) {
    mainWindow.webContents.openDevTools({ mode: 'detach' });
  }

  waitForBackend().then(ready => {
    log(`Backend ready: ${ready}`);

    if (ready) {
      if (app.isPackaged) {
        const frontendPath = path.join(__dirname, '..', 'dist', 'index.html');
        log(`Loading frontend from: ${frontendPath}`);
        mainWindow.loadFile(frontendPath);
      } else {
        mainWindow.loadURL('http://localhost:5173');
      }
    } else {
      mainWindow.loadURL('data:text/html,<h2>Backend failed to start</h2>');
    }
  });
}

app.whenReady().then(async () => {
  log('App ready, starting backend...');
  startPythonBackend();
  
  log('Waiting 2 seconds for backend...');
  await new Promise(resolve => setTimeout(resolve, 2000));
  
  createWindow();
  log('DEBUG: Window creation completed');
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  log('All windows closed');
  if (pythonProcess) pythonProcess.kill();
  if (process.platform !== 'darwin') app.quit();
});
