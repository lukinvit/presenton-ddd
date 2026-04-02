import { ipcMain, IpcMainInvokeEvent } from "electron";
import { Channels } from "./channels";
import { ProcessManager } from "../process_manager";

/**
 * Register all IPC handlers for the main process.
 * Called once during app initialization.
 */
export function registerIpcHandlers(processManager: ProcessManager): void {
  // Backend status
  ipcMain.handle(Channels.BACKEND_STATUS, async (_event: IpcMainInvokeEvent) => {
    return processManager.getStatus();
  });

  // Backend restart
  ipcMain.handle(Channels.BACKEND_RESTART, async (_event: IpcMainInvokeEvent) => {
    await processManager.restartPython();
    return { success: true };
  });

  // App quit
  ipcMain.handle(Channels.APP_QUIT, async (_event: IpcMainInvokeEvent) => {
    await processManager.shutdown();
    process.exit(0);
  });

  // Settings — persisted to electron-store (placeholder)
  ipcMain.handle(
    Channels.SETTINGS_GET,
    async (_event: IpcMainInvokeEvent, key: string) => {
      // TODO: integrate electron-store
      return null;
    }
  );

  ipcMain.handle(
    Channels.SETTINGS_SET,
    async (_event: IpcMainInvokeEvent, key: string, value: unknown) => {
      // TODO: integrate electron-store
      return { success: true };
    }
  );
}
