/**
 * IPC channel name constants shared between main and renderer processes.
 * All channel names follow the pattern: domain:action
 */

export const Channels = {
  // App lifecycle
  APP_READY: "app:ready",
  APP_QUIT: "app:quit",

  // Backend / Python process
  BACKEND_STATUS: "backend:status",
  BACKEND_RESTART: "backend:restart",

  // Presentation operations
  PRESENTATION_CREATE: "presentation:create",
  PRESENTATION_LIST: "presentation:list",
  PRESENTATION_GET: "presentation:get",
  PRESENTATION_DELETE: "presentation:delete",
  PRESENTATION_EXPORT: "presentation:export",

  // Auth / OAuth
  OAUTH_START: "oauth:start",
  OAUTH_CALLBACK: "oauth:callback",
  OAUTH_LOGOUT: "oauth:logout",

  // Settings
  SETTINGS_GET: "settings:get",
  SETTINGS_SET: "settings:set",

  // Updates
  UPDATE_CHECK: "update:check",
  UPDATE_DOWNLOAD: "update:download",
  UPDATE_INSTALL: "update:install",
  UPDATE_PROGRESS: "update:progress",
} as const;

export type Channel = (typeof Channels)[keyof typeof Channels];
