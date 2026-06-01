const { app, BrowserWindow } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const http = require('http');

let mainWindow;
let pythonProcess;

const isDev = !app.isPackaged;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 800,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false
    },
    title: 'PX-VideoMagic Desktop'
  });

  if (isDev) {
    // In development, we load from Vite dev server
    mainWindow.loadURL('http://localhost:5173');
    mainWindow.webContents.openDevTools();
  } else {
    // In production, we load the built React app
    mainWindow.loadFile(path.join(__dirname, 'dist', 'index.html'));
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

function startBackend() {
  const port = 8001;
  
  if (isDev) {
    // In dev, run main.py via python
    console.log('Starting Python backend via main.py...');
    pythonProcess = spawn('python', ['../backend/main.py'], {
      cwd: path.join(__dirname, '..'), // Run from web-ui folder
      env: { ...process.env }
    });
  } else {
    // In prod, run the bundled backend.exe
    console.log('Starting bundled backend.exe...');
    const backendPath = path.join(process.resourcesPath, 'backend.exe');
    pythonProcess = spawn(backendPath, [], {
      cwd: process.resourcesPath,
      env: { ...process.env }
    });
  }

  pythonProcess.stdout.on('data', (data) => {
    console.log(`Backend: ${data}`);
  });

  pythonProcess.stderr.on('data', (data) => {
    console.error(`Backend Error: ${data}`);
  });

  pythonProcess.on('close', (code) => {
    console.log(`Backend process exited with code ${code}`);
  });
}

function waitForBackend(url, callback) {
  const check = () => {
    http.get(url, (res) => {
      // If we get a response (even a 404 since /api might not exist at root), it means the server is up
      callback();
    }).on('error', (err) => {
      console.log('Waiting for backend...');
      setTimeout(check, 1000);
    });
  };
  check();
}

app.whenReady().then(() => {
  startBackend();
  
  // Wait for the backend to be available before showing the window to avoid confusing errors
  waitForBackend('http://localhost:8001/outputs', () => {
    createWindow();
  });

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

// Kill python process when app quits
app.on('before-quit', () => {
  if (pythonProcess) {
    pythonProcess.kill();
  }
});
