import { ChildProcess, spawn } from "child_process";
import path from "path";
import { getEmbeddedDir, getDbPath, getLogsDir } from "./utils/paths";
import { getPythonExecutable } from "./utils/platform";

export interface ProcessManagerOptions {
  backendPort: number;
  frontendPort: number;
  isDev: boolean;
}

export interface ProcessStatus {
  python: "starting" | "running" | "stopped" | "crashed";
  frontend: "starting" | "running" | "stopped" | "not_managed";
}

type ProcessState = ProcessStatus["python"];

/**
 * Manages the lifecycle of child processes:
 *   - Python embedded backend (launcher.py)
 *   - Next.js dev server (dev mode only; in prod, Electron serves static files)
 */
export class ProcessManager {
  private pythonProcess: ChildProcess | null = null;
  private frontendProcess: ChildProcess | null = null;

  private pythonState: ProcessState = "stopped";
  private frontendState: ProcessState = "stopped";

  private isShuttingDown = false;
  private restartAttempts = 0;
  private readonly MAX_RESTART_ATTEMPTS = 3;

  constructor(private readonly options: ProcessManagerOptions) {}

  // ─── Public API ───────────────────────────────────────────────────────────

  async start(): Promise<void> {
    await this.startPython();
    if (this.options.isDev) {
      await this.startFrontendDev();
    }
  }

  async shutdown(): Promise<void> {
    this.isShuttingDown = true;
    await Promise.all([this.killProcess(this.pythonProcess, "Python"), this.killProcess(this.frontendProcess, "Frontend")]);
    this.pythonProcess = null;
    this.frontendProcess = null;
    this.pythonState = "stopped";
    this.frontendState = "stopped";
  }

  async restartPython(): Promise<void> {
    await this.killProcess(this.pythonProcess, "Python");
    this.pythonProcess = null;
    this.restartAttempts = 0;
    await this.startPython();
  }

  getStatus(): ProcessStatus {
    return {
      python: this.pythonState,
      frontend: this.options.isDev ? this.frontendState : "not_managed",
    };
  }

  // ─── Python backend ───────────────────────────────────────────────────────

  private async startPython(): Promise<void> {
    const launcherPath = path.join(getEmbeddedDir(), "launcher.py");
    const python = getPythonExecutable();

    this.pythonState = "starting";
    console.log(`[ProcessManager] Starting Python: ${python} ${launcherPath}`);

    this.pythonProcess = spawn(python, [launcherPath], {
      env: {
        ...process.env,
        PRESENTON_DB_PATH: getDbPath(),
        PRESENTON_PORT: String(this.options.backendPort),
        PRESENTON_ENV: "electron",
      },
      stdio: ["ignore", "pipe", "pipe"],
    });

    this.pythonProcess.stdout?.on("data", (data: Buffer) => {
      const line = data.toString().trim();
      console.log(`[Python] ${line}`);
      if (line.includes("Application startup complete")) {
        this.pythonState = "running";
      }
    });

    this.pythonProcess.stderr?.on("data", (data: Buffer) => {
      console.error(`[Python ERR] ${data.toString().trim()}`);
    });

    this.pythonProcess.on("exit", (code, signal) => {
      console.log(`[ProcessManager] Python exited: code=${code} signal=${signal}`);
      this.pythonState = "crashed";
      if (!this.isShuttingDown) {
        this.handlePythonCrash();
      }
    });
  }

  private handlePythonCrash(): void {
    if (this.restartAttempts >= this.MAX_RESTART_ATTEMPTS) {
      console.error("[ProcessManager] Python crashed too many times. Giving up.");
      this.pythonState = "crashed";
      return;
    }
    this.restartAttempts++;
    const delay = 2000 * this.restartAttempts;
    console.log(
      `[ProcessManager] Restarting Python in ${delay}ms (attempt ${this.restartAttempts}/${this.MAX_RESTART_ATTEMPTS})`
    );
    setTimeout(() => this.startPython(), delay);
  }

  // ─── Next.js dev server ───────────────────────────────────────────────────

  private async startFrontendDev(): Promise<void> {
    const frontendDir = path.resolve(__dirname, "../../..", "frontend");
    this.frontendState = "starting";
    console.log(`[ProcessManager] Starting Next.js dev server in ${frontendDir}`);

    this.frontendProcess = spawn("npm", ["run", "dev"], {
      cwd: frontendDir,
      env: {
        ...process.env,
        PORT: String(this.options.frontendPort),
        NEXT_PUBLIC_API_URL: `http://localhost:${this.options.backendPort}`,
      },
      stdio: ["ignore", "pipe", "pipe"],
      shell: true,
    });

    this.frontendProcess.stdout?.on("data", (data: Buffer) => {
      const line = data.toString().trim();
      console.log(`[Next.js] ${line}`);
      if (line.includes("ready") || line.includes("started server")) {
        this.frontendState = "running";
      }
    });

    this.frontendProcess.stderr?.on("data", (data: Buffer) => {
      console.error(`[Next.js ERR] ${data.toString().trim()}`);
    });

    this.frontendProcess.on("exit", (code) => {
      this.frontendState = "crashed";
      if (!this.isShuttingDown) {
        console.error(`[ProcessManager] Next.js exited unexpectedly with code ${code}`);
      }
    });
  }

  // ─── Helpers ──────────────────────────────────────────────────────────────

  private killProcess(proc: ChildProcess | null, name: string): Promise<void> {
    return new Promise((resolve) => {
      if (!proc || proc.killed) {
        resolve();
        return;
      }
      console.log(`[ProcessManager] Sending SIGTERM to ${name}`);
      proc.kill("SIGTERM");

      const forceKill = setTimeout(() => {
        if (!proc.killed) {
          console.warn(`[ProcessManager] Force-killing ${name} with SIGKILL`);
          proc.kill("SIGKILL");
        }
      }, 5000);

      proc.on("exit", () => {
        clearTimeout(forceKill);
        resolve();
      });
    });
  }
}
