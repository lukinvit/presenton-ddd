import { app } from "electron";
import path from "path";

/**
 * Resolve resource paths that work both in development and in packaged builds.
 */

/** Root of the packaged app (or project root in dev). */
export function getAppRoot(): string {
  return app.isPackaged
    ? path.dirname(app.getPath("exe"))
    : path.resolve(__dirname, "../../..");
}

/** Path to the embedded Python launcher directory. */
export function getEmbeddedDir(): string {
  return app.isPackaged
    ? path.join(process.resourcesPath, "embedded")
    : path.resolve(getAppRoot(), "electron/embedded");
}

/** Path to the built Next.js frontend. */
export function getFrontendDir(): string {
  return app.isPackaged
    ? path.join(process.resourcesPath, "frontend/out")
    : path.resolve(getAppRoot(), "frontend");
}

/** User data directory for SQLite and settings. */
export function getUserDataDir(): string {
  return app.getPath("userData");
}

/** Path to the SQLite database file. */
export function getDbPath(): string {
  return path.join(getUserDataDir(), "presenton.db");
}

/** Path to application logs directory. */
export function getLogsDir(): string {
  return app.getPath("logs");
}

/** Resolve a path relative to electron/resources. */
export function getResourcePath(...segments: string[]): string {
  const base = app.isPackaged
    ? process.resourcesPath
    : path.resolve(getAppRoot(), "electron/resources");
  return path.join(base, ...segments);
}
