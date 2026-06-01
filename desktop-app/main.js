const { app, BrowserWindow, dialog } = require('electron');
const path = require('path');
const { spawn, execSync } = require('child_process');
const http = require('http');

let mainWindow;
let backendProcess;
let backendPort = 8001; // We can make this dynamic if needed, but 8001 is hardcoded default

function checkDependencies() {
  try {
    execSync('ffmpeg -version');
  } catch (e) {
    dialog.showErrorBox("Fehlende Komponente: FFMPEG", "PX-VideoMagic benötigt 'FFMPEG' für die Videoverarbeitung.\n\nBitte installiere FFMPEG und füge es zu deinen System-Umgebungsvariablen (PATH) hinzu.");
    return false;
  }
  try {
    execSync('node -v');
  } catch (e) {
    dialog.showErrorBox("Fehlende Komponente: Node.js", "PX-VideoMagic benötigt 'Node.js' für die Typo-Animationen.\n\nBitte lade Node.js herunter und installiere es.");
    return false;
  }
  return true;
}

function checkBackendReady(port, retries = 30) {
  return new Promise((resolve, reject) => {
    const check = (remaining) => {
      if (remaining <= 0) {
        return reject(new Error('Backend did not start in time.'));
      }
      http.get(`http://127.0.0.1:${port}/api/settings`, (res) => {
        if (res.statusCode === 200) {
          resolve();
        } else {
          setTimeout(() => check(remaining - 1), 1000);
        }
      }).on('error', () => {
        setTimeout(() => check(remaining - 1), 1000);
      });
    };
    check(retries);
  });
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    title: "PX-VideoMagic",
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      webSecurity: false
    }
  });

  mainWindow.setMenuBarVisibility(false);
  mainWindow.loadURL(`http://127.0.0.1:${backendPort}`);

  mainWindow.webContents.on('did-finish-load', () => {
    mainWindow.focus();
  });

  mainWindow.on('closed', function () {
    mainWindow = null;
  });
}

app.on('ready', async () => {
  if (!checkDependencies()) {
    app.quit();
    return;
  }

  // Kill orphaned backend processes
  try {
    if (process.platform === 'win32') {
      execSync('taskkill /f /im backend.exe', { stdio: 'ignore' });
      console.log('Killed orphaned backend processes.');
    }
  } catch (e) {
    // Ignore errors if no process was found
  }

  const fs = require('fs');
  // Find backend executable
  let backendPath;
  if (app.isPackaged) {
    backendPath = path.join(process.resourcesPath, 'backend.exe');
    // Restore node_modules for remotion
    const remotionDir = path.join(process.resourcesPath, 'video-use', 'remotion-subs');
    const packedNm = path.join(remotionDir, 'node_modules_packed');
    const realNm = path.join(remotionDir, 'node_modules');
    try {
      if (fs.existsSync(packedNm) && !fs.existsSync(realNm)) {
        fs.renameSync(packedNm, realNm);
        console.log('Restored node_modules for remotion.');
      }
    } catch(e) {
      console.error('Failed to restore node_modules:', e);
    }
  } else {
    backendPath = path.join(__dirname, '..', 'web-ui', 'backend', 'dist', 'backend.exe');
  }

  // Start backend
  console.log(`Starting backend at: ${backendPath}`);
  try {
    backendProcess = spawn(backendPath, [], {
      env: { ...process.env, PORT: backendPort },
      cwd: app.isPackaged ? process.resourcesPath : path.join(__dirname, '..', 'web-ui', 'backend')
    });

    backendProcess.stdout.on('data', (data) => console.log(`Backend: ${data}`));
    backendProcess.stderr.on('data', (data) => console.error(`Backend Error: ${data}`));

    backendProcess.on('error', (err) => {
      dialog.showErrorBox("Backend Error", `Failed to start the backend engine: ${err.message}`);
    });

    backendProcess.on('exit', (code) => {
      if (code !== 0) {
        console.error(`Backend exited with code ${code}`);
      }
    });

    // Wait for backend to be ready
    try {
      await checkBackendReady(backendPort);
      createWindow();
    } catch (e) {
      dialog.showErrorBox("Backend Timeout", "The backend engine took too long to start.");
      app.quit();
    }
  } catch(e) {
    dialog.showErrorBox("Fatal Error", `Failed to spawn backend: ${e.message}`);
    app.quit();
  }
});

app.on('window-all-closed', function () {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('before-quit', () => {
  if (backendProcess) {
    backendProcess.kill();
  }
});
