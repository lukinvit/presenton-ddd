import { BrowserWindow, ipcMain } from "electron";
import { Channels } from "../ipc/channels";

/**
 * Auto-update support via electron-updater.
 *
 * electron-updater is an optional peer dependency — only imported at runtime
 * so development builds without it still work.
 */
export class AutoUpdater {
  constructor(private mainWindow: BrowserWindow) {}

  init(): void {
    let autoUpdater: any;
    try {
      // eslint-disable-next-line @typescript-eslint/no-var-requires
      autoUpdater = require("electron-updater").autoUpdater;
    } catch {
      console.warn("[AutoUpdater] electron-updater not installed — skipping.");
      return;
    }

    autoUpdater.logger = console;
    autoUpdater.autoDownload = false;

    // Forward progress events to renderer
    autoUpdater.on("update-available", (info: unknown) => {
      this.send(Channels.UPDATE_PROGRESS, { status: "available", info });
    });

    autoUpdater.on("update-not-available", () => {
      this.send(Channels.UPDATE_PROGRESS, { status: "up-to-date" });
    });

    autoUpdater.on("download-progress", (progress: unknown) => {
      this.send(Channels.UPDATE_PROGRESS, { status: "downloading", progress });
    });

    autoUpdater.on("update-downloaded", () => {
      this.send(Channels.UPDATE_PROGRESS, { status: "downloaded" });
    });

    autoUpdater.on("error", (err: Error) => {
      this.send(Channels.UPDATE_PROGRESS, { status: "error", message: err.message });
    });

    // IPC handlers
    ipcMain.handle(Channels.UPDATE_CHECK, async () => {
      await autoUpdater.checkForUpdates();
    });

    ipcMain.handle(Channels.UPDATE_DOWNLOAD, async () => {
      await autoUpdater.downloadUpdate();
    });

    ipcMain.handle(Channels.UPDATE_INSTALL, async () => {
      autoUpdater.quitAndInstall(false, true);
    });

    // Check on startup (after a short delay to avoid blocking the window)
    setTimeout(() => autoUpdater.checkForUpdates(), 10_000);
  }

  // ─── Helpers ──────────────────────────────────────────────────────────────

  private send(channel: string, payload: unknown): void {
    if (this.mainWindow && !this.mainWindow.isDestroyed()) {
      this.mainWindow.webContents.send(channel, payload);
    }
  }
}
