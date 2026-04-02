/**
 * OS detection helpers.
 */

export type Platform = "darwin" | "win32" | "linux";

/** Current platform. */
export const currentPlatform: Platform = process.platform as Platform;

export const isMac = process.platform === "darwin";
export const isWindows = process.platform === "win32";
export const isLinux = process.platform === "linux";

/** Python executable name appropriate for the current platform. */
export function getPythonExecutable(): string {
  return isWindows ? "python.exe" : "python3";
}

/** Node/npm executable suffix on Windows. */
export function getExeSuffix(): string {
  return isWindows ? ".cmd" : "";
}

/** Whether the OS supports system tray. */
export function supportsTray(): boolean {
  // All three platforms support Electron Tray, but Linux may require libappindicator
  return true;
}

/** Returns a human-readable OS name. */
export function getPlatformName(): string {
  if (isMac) return "macOS";
  if (isWindows) return "Windows";
  return "Linux";
}
