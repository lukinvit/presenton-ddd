import { contextBridge, ipcRenderer } from "electron";
import { Channels, type Channel } from "./ipc/channels";

/**
 * Preload script: exposes a safe, typed API to the renderer process
 * via `window.electronAPI`.
 *
 * Only channels listed in `Channels` can be invoked — no arbitrary IPC.
 */

/** Whitelist of channels that the renderer may invoke (request → response). */
const INVOKE_WHITELIST = new Set<Channel>([
  Channels.BACKEND_STATUS,
  Channels.BACKEND_RESTART,
  Channels.APP_QUIT,
  Channels.SETTINGS_GET,
  Channels.SETTINGS_SET,
  Channels.OAUTH_START,
  Channels.OAUTH_LOGOUT,
  Channels.UPDATE_CHECK,
  Channels.UPDATE_DOWNLOAD,
  Channels.UPDATE_INSTALL,
]);

/** Whitelist of channels the renderer may listen on (main → renderer). */
const LISTEN_WHITELIST = new Set<Channel>([
  Channels.BACKEND_STATUS,
  Channels.UPDATE_PROGRESS,
  Channels.OAUTH_CALLBACK,
]);

type Unsubscribe = () => void;

const electronAPI = {
  /**
   * Invoke an IPC handler in the main process and await its result.
   */
  invoke<T = unknown>(channel: Channel, ...args: unknown[]): Promise<T> {
    if (!INVOKE_WHITELIST.has(channel)) {
      return Promise.reject(new Error(`Channel "${channel}" is not allowed.`));
    }
    return ipcRenderer.invoke(channel, ...args) as Promise<T>;
  },

  /**
   * Listen for events sent from the main process.
   * Returns an unsubscribe function.
   */
  on(channel: Channel, listener: (...args: unknown[]) => void): Unsubscribe {
    if (!LISTEN_WHITELIST.has(channel)) {
      throw new Error(`Channel "${channel}" is not allowed for listening.`);
    }
    const wrapped = (_event: Electron.IpcRendererEvent, ...args: unknown[]) =>
      listener(...args);
    ipcRenderer.on(channel, wrapped);
    return () => ipcRenderer.removeListener(channel, wrapped);
  },

  /** Expose channel constants so the renderer doesn't need to import them. */
  channels: Channels,
};

contextBridge.exposeInMainWorld("electronAPI", electronAPI);

// Type declaration for TypeScript consumers in the renderer
export type ElectronAPI = typeof electronAPI;
