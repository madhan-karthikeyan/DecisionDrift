import * as vscode from "vscode";
import { analyzeFile, clearDiagnostics, getDiagnostics } from "./diagnostics";
import { runDoctor, DoctorOutput } from "./cli";

export function analyzeCurrentFile(): void {
  const editor = vscode.window.activeTextEditor;
  if (!editor) {
    vscode.window.showWarningMessage("No active editor found. Open a file first.");
    return;
  }
  vscode.window.withProgress(
    { location: vscode.ProgressLocation.Window, title: "DecisionDrift: Analyzing file..." },
    async () => {
      await analyzeFile(editor.document);
    }
  );
}

export async function analyzeWorkspace(): Promise<void> {
  const files = await vscode.workspace.findFiles("**/*.{py,js,ts,jsx,tsx,rb,php,cs,kt,swift,c,cpp}", "**/node_modules/**");
  if (files.length === 0) {
    vscode.window.showInformationMessage("No analyzable files found in workspace.");
    return;
  }
  clearDiagnostics();

  await vscode.window.withProgress(
    { location: vscode.ProgressLocation.Window, title: `DecisionDrift: Analyzing ${files.length} files...` },
    async (progress) => {
      let done = 0;
      for (const uri of files) {
        const doc = await vscode.workspace.openTextDocument(uri);
        await analyzeFile(doc);
        done++;
        progress.report({ message: `${done}/${files.length}`, increment: 100 / files.length });
      }
    }
  );

  const total = getDiagnostics().reduce((sum, [_, diags]) => sum + diags.length, 0);
  vscode.window.showInformationMessage(
    `DecisionDrift: Analyzed ${files.length} files — ${total} findings.`
  );
}

export function showHealthReport(): void {
  vscode.window.withProgress(
    { location: vscode.ProgressLocation.Window, title: "DecisionDrift: Running health check..." },
    async () => {
      try {
        const report: DoctorOutput = runDoctor();
        const checks = report.metadata.checks;
        const lines: string[] = ["## DecisionDrift Health Report\n"];
        for (const [key, check] of Object.entries(checks)) {
          const icon = check.status === "ok" ? "✓" : check.status === "warn" ? "⚠" : "✗";
          lines.push(`- **${icon} ${check.name}** (${key}): ${check.value}`);
        }
        lines.push(`\n**Overall: ${report.summary.status}**`);

        const panel = vscode.window.createWebviewPanel(
          "decisiondrift.health",
          "DecisionDrift Health Report",
          vscode.ViewColumn.Two,
          { enableScripts: false }
        );
        panel.webview.html = `<!DOCTYPE html>
<html><body style="font-family: sans-serif; padding: 1em;">
  ${lines.join("\n<br>")}
</body></html>`;

        const statusText = Object.values(checks)
          .map((c) => `${c.status === "ok" ? "✓" : "✗"} ${c.name}`)
          .join(" · ");
        vscode.window.setStatusBarMessage(
          `DecisionDrift: ${statusText}`,
          10000
        );
      } catch (e: any) {
        vscode.window.showErrorMessage(`Health check failed: ${e.message}`);
      }
    }
  );
}

export function registerCommands(context: vscode.ExtensionContext): void {
  context.subscriptions.push(
    vscode.commands.registerCommand("decisiondrift.analyzeFile", analyzeCurrentFile)
  );
  context.subscriptions.push(
    vscode.commands.registerCommand("decisiondrift.analyzeWorkspace", analyzeWorkspace)
  );
  context.subscriptions.push(
    vscode.commands.registerCommand("decisiondrift.showHealth", showHealthReport)
  );
}
