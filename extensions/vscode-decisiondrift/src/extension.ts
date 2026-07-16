import * as vscode from "vscode";
import { registerDiagnosticListeners } from "./diagnostics";
import { registerCommands } from "./commands";
import { registerSidebar } from "./sidebar";
import { runDoctor, resolveCliPath } from "./cli";

export function activate(context: vscode.ExtensionContext): void {
  const cli = resolveCliPath();
  if (!cli) {
    vscode.window.showWarningMessage(
      "DecisionDrift CLI not found. Install it with: pip install decisiondrift"
    );
  } else {
    updateStatusBar(cli);
  }

  registerDiagnosticListeners(context);
  registerCommands(context);
  registerSidebar(context);

  context.subscriptions.push(
    vscode.workspace.onDidChangeConfiguration((e) => {
      if (e.affectsConfiguration("decisiondrift")) {
        updateStatusBar(resolveCliPath());
      }
    })
  );
}

function updateStatusBar(cliPath: string | null): void {
  if (!cliPath) return;
  try {
    const report = runDoctor();
    const status = report.summary.status;
    const item = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
    item.id = "decisiondrift.status";
    item.name = "DecisionDrift";
    item.text = status === "ok" ? "$(check) DecisionDrift" : "$(warning) DecisionDrift";
    item.tooltip = `Health: ${status}\nCLI: ${cliPath}`;
    item.command = "decisiondrift.showHealth";
    item.show();
  } catch {
    vscode.window.setStatusBarMessage("$(warning) DecisionDrift: health check failed", 5000);
  }
}

export function deactivate(): void {
  /* cleanup handled by disposable subscriptions */
}
