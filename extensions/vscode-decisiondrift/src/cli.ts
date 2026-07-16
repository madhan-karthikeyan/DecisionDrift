import * as vscode from "vscode";
import * as fs from "fs";
import * as os from "os";
import * as path from "path";
import { execSync, ExecSyncOptions } from "child_process";

export interface CliResult {
  stdout: string;
  stderr: string;
  exitCode: number;
}

export interface EnforceFinding {
  rule: string;
  severity: string;
  message: string;
  file: string;
  line: number;
  column: number;
}

export interface EnforceOutput {
  schema_version: number;
  command: string;
  summary: { status: string; findings_count: number; files_scanned: number };
  findings: EnforceFinding[];
}

export interface DoctorOutput {
  schema_version: number;
  command: string;
  summary: { status: string; findings_count: number };
  metadata: { checks: Record<string, { name: string; status: string; value: string }> };
}

function findCliOnPath(): string | null {
  const isWin = process.platform === "win32";
  const cmd = isWin ? "where" : "which";
  try {
    return execSync(`${cmd} decisiondrift`, { encoding: "utf-8", stdio: "pipe" })
      .trim()
      .split("\n")[0] || null;
  } catch {
    return null;
  }
}

export function resolveCliPath(): string | null {
  const configPath = vscode.workspace.getConfiguration("decisiondrift").get<string>("cliPath", "");
  if (configPath) {
    try {
      const resolved = configPath.startsWith("~")
        ? path.join(os.homedir(), configPath.slice(1))
        : path.resolve(configPath);
      if (fs.existsSync(resolved)) return resolved;
    } catch { /* ignore bad path */ }
  }
  return findCliOnPath();
}

let _notifiedNoCli = false;

export function runCli(args: string[], cwd?: string): CliResult {
  const cli = resolveCliPath();
  if (!cli) {
    if (!_notifiedNoCli) {
      _notifiedNoCli = true;
      const action = "Install";
      vscode.window
        .showErrorMessage(
          "DecisionDrift CLI not found. Install it with: pip install decisiondrift",
          action
        )
        .then((selected) => {
          if (selected === action) {
            vscode.commands.executeCommand(
              "vscode.open",
              vscode.Uri.parse("https://pypi.org/project/decisiondrift/")
            );
          }
        });
    }
    return { stdout: "", stderr: "CLI not found", exitCode: 1 };
  }

  const opts: ExecSyncOptions = {
    encoding: "utf-8" as const,
    stdio: "pipe" as const,
    timeout: 30000,
    maxBuffer: 10 * 1024 * 1024,
    windowsHide: true,
  };
  if (cwd) opts.cwd = cwd;

  try {
    const stdout = execSync(`"${cli}" ${args.join(" ")}`, opts).trim();
    return { stdout, stderr: "", exitCode: 0 };
  } catch (e: any) {
    const stderr = e.stderr?.toString().trim() || e.message || "Unknown error";
    const exitCode = e.status ?? 1;
    const stdout = e.stdout?.toString().trim() || "";
    return { stdout, stderr, exitCode };
  }
}

export function enforceFile(filePath: string): EnforceOutput {
  const workspaceRoot = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath || ".";
  const adrDir = vscode.workspace.getConfiguration("decisiondrift").get<string>("adrDir", "");
  const args = ["enforce", "--file", `"${filePath}"`, "--format", "json"];
  if (adrDir) args.push("--adr-dir", `"${adrDir}"`);

  const result = runCli(args, workspaceRoot);

  if (result.exitCode !== 0) {
    throw new Error(`decisiondrift enforce failed: ${result.stderr}`);
  }

  try {
    return JSON.parse(result.stdout) as EnforceOutput;
  } catch {
    throw new Error(`Failed to parse enforce output: ${result.stdout.slice(0, 200)}`);
  }
}

export function runDoctor(): DoctorOutput {
  const workspaceRoot = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath || ".";
  const adrDir = vscode.workspace.getConfiguration("decisiondrift").get<string>("adrDir", "");
  const args = ["doctor", "--format", "json"];
  if (adrDir) args.push("--adr-dir", `"${adrDir}"`);

  const result = runCli(args, workspaceRoot);

  if (result.exitCode !== 0) {
    throw new Error(`decisiondrift doctor failed: ${result.stderr}`);
  }

  try {
    return JSON.parse(result.stdout) as DoctorOutput;
  } catch {
    throw new Error(`Failed to parse doctor output: ${result.stdout.slice(0, 200)}`);
  }
}
