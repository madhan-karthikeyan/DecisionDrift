import * as vscode from "vscode";
import { enforceFile } from "./cli";

const diagCollection = vscode.languages.createDiagnosticCollection("decisiondrift");
const pendingFiles = new Set<string>();
let debounceTimer: ReturnType<typeof setTimeout> | undefined;

function severityFromString(s: string): vscode.DiagnosticSeverity {
  switch (s.toLowerCase()) {
    case "error":
      return vscode.DiagnosticSeverity.Error;
    case "warning":
    case "warn":
      return vscode.DiagnosticSeverity.Warning;
    case "info":
      return vscode.DiagnosticSeverity.Information;
    default:
      return vscode.DiagnosticSeverity.Hint;
  }
}

export async function analyzeFile(document: vscode.TextDocument): Promise<void> {
  if (pendingFiles.has(document.uri.fsPath)) return;
  pendingFiles.add(document.uri.fsPath);

  try {
    const output = await Promise.resolve().then(() => enforceFile(document.uri.fsPath));

    const diagnostics: vscode.Diagnostic[] = [];
    for (const f of output.findings) {
      const range = new vscode.Range(
        Math.max(0, (f.line || 1) - 1),
        Math.max(0, (f.column || 0)),
        Math.max(0, (f.line || 1) - 1),
        1000
      );
      const diag = new vscode.Diagnostic(
        range,
        `[${f.rule}] ${f.message}`,
        severityFromString(f.severity)
      );
      diag.source = "decisiondrift";
      diag.code = f.rule;
      diagnostics.push(diag);
    }

    diagCollection.set(document.uri, diagnostics);
  } catch (e: any) {
    diagCollection.set(document.uri, []);
  } finally {
    pendingFiles.delete(document.uri.fsPath);
  }
}

export function clearDiagnostics(uri?: vscode.Uri): void {
  if (uri) {
    diagCollection.delete(uri);
  } else {
    diagCollection.clear();
  }
}

export function getDiagnostics(): readonly [vscode.Uri, vscode.Diagnostic[]][] {
  return diagCollection.entries();
}

function debouncedAnalyze(document: vscode.TextDocument): void {
  if (debounceTimer) clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => analyzeFile(document), 500);
}

export function registerDiagnosticListeners(context: vscode.ExtensionContext): void {
  context.subscriptions.push(diagCollection);

  const runOnSave = vscode.workspace.getConfiguration("decisiondrift").get<boolean>("runOnSave", true);
  const runOnOpen = vscode.workspace.getConfiguration("decisiondrift").get<boolean>("runOnOpen", true);

  if (runOnSave) {
    context.subscriptions.push(
      vscode.workspace.onDidSaveTextDocument((doc) => {
        if (doc.uri.scheme === "file") {
          debouncedAnalyze(doc);
        }
      })
    );
  }

  if (runOnOpen) {
    context.subscriptions.push(
      vscode.workspace.onDidOpenTextDocument((doc) => {
        if (doc.uri.scheme === "file") {
          debouncedAnalyze(doc);
        }
      })
    );
  }

  context.subscriptions.push(
    vscode.workspace.onDidCloseTextDocument((doc) => {
      clearDiagnostics(doc.uri);
    })
  );
}
