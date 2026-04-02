import { BrowserWindow, ipcMain } from "electron";
import { URL } from "url";
import { Channels } from "../ipc/channels";

export interface OAuthResult {
  code: string;
  state: string | null;
  error: string | null;
}

/**
 * Opens a dedicated BrowserWindow for OAuth flows.
 *
 * Flow:
 *   1. Renderer calls `ipcRenderer.invoke(Channels.OAUTH_START, { url })`.
 *   2. OAuthWindow opens a popup pointing to the provider's auth URL.
 *   3. Provider redirects to `presenton://oauth/callback?code=...`.
 *   4. main.ts intercepts the deep link and calls `handleCallback(url)`.
 *   5. OAuthWindow resolves the pending promise and closes the popup.
 *   6. Result is returned to the renderer via ipcMain.handle.
 */
export class OAuthWindow {
  private popup: BrowserWindow | null = null;
  private pendingResolve: ((result: OAuthResult) => void) | null = null;
  private pendingReject: ((err: Error) => void) | null = null;

  constructor(private readonly protocol: string) {
    this.registerIpcHandlers();
  }

  // ─── IPC ──────────────────────────────────────────────────────────────────

  private registerIpcHandlers(): void {
    ipcMain.handle(
      Channels.OAUTH_START,
      async (_event, authUrl: string): Promise<OAuthResult> => {
        return this.open(authUrl);
      }
    );

    ipcMain.handle(Channels.OAUTH_LOGOUT, async () => {
      this.close();
      return { success: true };
    });
  }

  // ─── Public ───────────────────────────────────────────────────────────────

  /**
   * Opens the OAuth popup and waits for the callback.
   */
  open(authUrl: string): Promise<OAuthResult> {
    if (this.popup && !this.popup.isDestroyed()) {
      this.popup.focus();
      return Promise.reject(new Error("OAuth flow already in progress."));
    }

    return new Promise<OAuthResult>((resolve, reject) => {
      this.pendingResolve = resolve;
      this.pendingReject = reject;

      this.popup = new BrowserWindow({
        width: 520,
        height: 680,
        show: true,
        modal: true,
        webPreferences: {
          nodeIntegration: false,
          contextIsolation: true,
          sandbox: true,
        },
      });

      this.popup.loadURL(authUrl);

      this.popup.on("closed", () => {
        this.popup = null;
        if (this.pendingReject) {
          this.pendingReject(new Error("OAuth window was closed by the user."));
          this.pendingResolve = null;
          this.pendingReject = null;
        }
      });

      // Intercept navigation within the popup to detect the callback URL
      this.popup.webContents.on("will-navigate", (_event, url) => {
        if (url.startsWith(`${this.protocol}://`)) {
          this.handleCallback(url);
        }
      });

      this.popup.webContents.on("will-redirect", (_event, url) => {
        if (url.startsWith(`${this.protocol}://`)) {
          this.handleCallback(url);
        }
      });
    });
  }

  /**
   * Called by main.ts when the OS delivers a `presenton://oauth/callback` deep link.
   */
  handleCallback(rawUrl: string): void {
    if (!this.pendingResolve) return;

    let result: OAuthResult;
    try {
      const url = new URL(rawUrl);
      result = {
        code: url.searchParams.get("code") ?? "",
        state: url.searchParams.get("state"),
        error: url.searchParams.get("error"),
      };
    } catch {
      result = { code: "", state: null, error: "Invalid callback URL" };
    }

    this.pendingResolve(result);
    this.pendingResolve = null;
    this.pendingReject = null;
    this.close();
  }

  /** Close the OAuth popup if open. */
  close(): void {
    if (this.popup && !this.popup.isDestroyed()) {
      this.popup.close();
    }
    this.popup = null;
  }
}
