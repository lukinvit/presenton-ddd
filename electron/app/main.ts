import {
  app,
  BrowserWindow,
  protocol,
  shell,
  nativeTheme,
  Menu,
  Tray,
} from "electron";
import path from "path";
import { ProcessManager } from "./process_manager";
import { registerIpcHandlers } from "./ipc/handlers";
import { OAuthWindow } from "./services/oauth_window";
import { AutoUpdater } from "./services/auto_updater";
import { getResourcePath, getFrontendDir, getUserDataDir } from "./utils/paths";
import { isMac } from "./utils/platform";
import { Channels } from "./ipc/channels";

// Handle Squirrel startup events on Windows
if (require("electron-squirrel-startup")) app.quit();

// ─── Constants ───────────────────────────────────────────────────────────────

const BACKEND_PORT = 8000;
const FRONTEND_DEV_PORT = 3000;
const CUSTOM_PROTOCOL = "presenton";
const IS_DEV = !app.isPackaged;

// ─── State ────────────────────────────────────────────────────────────────────

let mainWindow: BrowserWindow | null = null;
let tray: Tray | null = null;
let processManager: ProcessManager | null = null;
let oauthWindow: OAuthWindow | null = null;
let autoUpdater: AutoUpdater | null = null;

// ─── Protocol ────────────────────────────────────────────────────────────────

/**
 * Register custom protocol `presenton://` for deep links and OAuth callbacks.
 * Must be called before `app.whenReady`.
 */
function registerCustomProtocol(): void {
  if (process.defaultApp) {
    if (process.argv.length >= 2) {
      app.setAsDefaultProtocolClient(CUSTOM_PROTOCOL, process.execPath, [
        path.resolve(process.argv[1]),
      ]);
    }
  } else {
    app.setAsDefaultProtocolClient(CUSTOM_PROTOCOL);
  }
}

// ─── Window ───────────────────────────────────────────────────────────────────

function createMainWindow(): BrowserWindow {
  const win = new BrowserWindow({
    width: 1280,
    height: 800,
    minWidth: 900,
    minHeight: 600,
    show: false, // shown after ready-to-show
    backgroundColor: nativeTheme.shouldUseDarkColors ? "#1a1a2e" : "#ffffff",
    titleBarStyle: isMac ? "hiddenInset" : "default",
    icon: getResourcePath("icon.png"),
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
    },
  });

  // Show window once fully loaded (avoids flash)
  win.once("ready-to-show", () => {
    win.show();
    if (IS_DEV) win.webContents.openDevTools({ mode: "detach" });
  });

  // Open external links in the system browser
  win.webContents.setWindowOpenHandler(({ url }) => {
    if (url.startsWith("https://") || url.startsWith("http://")) {
      shell.openExternal(url);
    }
    return { action: "deny" };
  });

  // Load the frontend
  loadFrontend(win);

  return win;
}

function loadFrontend(win: BrowserWindow): void {
  if (IS_DEV) {
    win.loadURL(`http://localhost:${FRONTEND_DEV_PORT}`);
  } else {
    const indexPath = path.join(getFrontendDir(), "index.html");
    win.loadFile(indexPath);
  }
}

// ─── Tray ─────────────────────────────────────────────────────────────────────

function createTray(): void {
  tray = new Tray(getResourcePath("tray_icon.png"));
  const contextMenu = Menu.buildFromTemplate([
    {
      label: "Open Presenton",
      click: () => {
        mainWindow?.show();
        mainWindow?.focus();
      },
    },
    { type: "separator" },
    {
      label: "Quit",
      click: () => gracefulShutdown(),
    },
  ]);

  tray.setToolTip("Presenton");
  tray.setContextMenu(contextMenu);
  tray.on("double-click", () => {
    mainWindow?.show();
    mainWindow?.focus();
  });
}

// ─── OAuth deep-link handling ─────────────────────────────────────────────────

function handleDeepLink(url: string): void {
  if (url.startsWith(`${CUSTOM_PROTOCOL}://oauth/callback`)) {
    oauthWindow?.handleCallback(url);
  }
}

// macOS: deep link while app is already running
app.on("open-url", (_event, url) => {
  handleDeepLink(url);
});

// Windows/Linux: second instance passes URL via argv
app.on("second-instance", (_event, argv) => {
  const url = argv.find((arg) => arg.startsWith(`${CUSTOM_PROTOCOL}://`));
  if (url) handleDeepLink(url);

  // Focus main window
  if (mainWindow) {
    if (mainWindow.isMinimized()) mainWindow.restore();
    mainWindow.focus();
  }
});

// Prevent multiple instances on Windows/Linux
const isPrimaryInstance = app.requestSingleInstanceLock();
if (!isPrimaryInstance) {
  app.quit();
}

// ─── Shutdown ─────────────────────────────────────────────────────────────────

async function gracefulShutdown(): Promise<void> {
  await processManager?.shutdown();
  app.quit();
}

// ─── App lifecycle ─────────────────────────────────────────────────────────────

registerCustomProtocol();

app.whenReady().then(async () => {
  // Start backend and (in dev) frontend dev server
  processManager = new ProcessManager({
    backendPort: BACKEND_PORT,
    frontendPort: FRONTEND_DEV_PORT,
    isDev: IS_DEV,
  });

  await processManager.start();

  // Set up IPC
  registerIpcHandlers(processManager);

  // OAuth helper
  oauthWindow = new OAuthWindow(CUSTOM_PROTOCOL);

  // Auto-updater (production only)
  if (!IS_DEV) {
    autoUpdater = new AutoUpdater(mainWindow!);
    autoUpdater.init();
  }

  // Create UI
  mainWindow = createMainWindow();
  createTray();

  // macOS: re-create window when dock icon is clicked and no windows open
  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      mainWindow = createMainWindow();
    } else {
      mainWindow?.show();
    }
  });
});

// Quit when all windows are closed (except macOS)
app.on("window-all-closed", () => {
  if (!isMac) gracefulShutdown();
});

app.on("before-quit", async () => {
  await processManager?.shutdown();
});
