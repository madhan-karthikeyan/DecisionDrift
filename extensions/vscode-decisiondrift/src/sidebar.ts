import * as vscode from "vscode";
import * as fs from "fs";
import * as path from "path";
import { getDiagnostics } from "./diagnostics";

class SidebarItem extends vscode.TreeItem {
  constructor(
    label: string,
    collapsibleState: vscode.TreeItemCollapsibleState,
    public readonly tooltipText?: string,
    public readonly command?: vscode.Command
  ) {
    super(label, collapsibleState);
    this.tooltip = tooltipText || label;
  }
}

class FindingsProvider implements vscode.TreeDataProvider<SidebarItem> {
  private _onDidChangeTreeData = new vscode.EventEmitter<SidebarItem | undefined>();
  readonly onDidChangeTreeData = this._onDidChangeTreeData.event;

  refresh(): void {
    this._onDidChangeTreeData.fire(undefined);
  }

  getTreeItem(element: SidebarItem): vscode.TreeItem {
    return element;
  }

  getChildren(element?: SidebarItem): Thenable<SidebarItem[]> {
    if (element) return Promise.resolve([]);

    const all = getDiagnostics();
    const items: SidebarItem[] = [];

    for (const [uri, diags] of all) {
      for (const d of diags) {
        const label = `[${d.code || "rule"}] ${d.message.slice(0, 60)}`;
        const item = new SidebarItem(
          label,
          vscode.TreeItemCollapsibleState.None,
          `${uri.fs.path}:${d.range.start.line + 1}`,
          {
            command: "vscode.open",
            title: "",
            arguments: [{ ...uri, fragment: `L${d.range.start.line + 1}` }],
          }
        );
        item.contextValue = "finding";
        item.resourceUri = uri;

        switch (d.severity) {
          case vscode.DiagnosticSeverity.Error:
            item.iconPath = new vscode.ThemeIcon("error");
            break;
          case vscode.DiagnosticSeverity.Warning:
            item.iconPath = new vscode.ThemeIcon("warning");
            break;
          default:
            item.iconPath = new vscode.ThemeIcon("info");
        }
        items.push(item);
      }
    }

    if (items.length === 0) {
      items.push(new SidebarItem("No findings", vscode.TreeItemCollapsibleState.None));
    }

    return Promise.resolve(items);
  }
}

class AdrProvider implements vscode.TreeDataProvider<SidebarItem> {
  private _onDidChangeTreeData = new vscode.EventEmitter<SidebarItem | undefined>();
  readonly onDidChangeTreeData = this._onDidChangeTreeData.event;

  refresh(): void {
    this._onDidChangeTreeData.fire(undefined);
  }

  getTreeItem(element: SidebarItem): vscode.TreeItem {
    return element;
  }

  getChildren(_element?: SidebarItem): Thenable<SidebarItem[]> {
    const workspaceRoot = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
    if (!workspaceRoot) return Promise.resolve([]);

    const adrDir = vscode.workspace
      .getConfiguration("decisiondrift")
      .get<string>("adrDir", "");
    const dir = adrDir || path.join(workspaceRoot, "docs", "adr");

    if (!fs.existsSync(dir)) {
      return Promise.resolve([
        new SidebarItem("No ADRs found", vscode.TreeItemCollapsibleState.None, "Configure decisiondrift.adrDir in settings"),
      ]);
    }

    try {
      const entries = fs.readdirSync(dir).filter(
        (f) => f.endsWith(".md") || f.endsWith(".mdx")
      ).sort();

      const items = entries.map((f) => {
        const filePath = path.join(dir, f);
        const stat = fs.statSync(filePath);
        const label = f.replace(/\.(md|mdx)$/, "");
        const tooltip = `${filePath}\n${stat.mtime.toLocaleDateString()}`;
        const item = new SidebarItem(
          label,
          vscode.TreeItemCollapsibleState.None,
          tooltip,
          {
            command: "vscode.open",
            title: "",
            arguments: [vscode.Uri.file(filePath)],
          }
        );
        item.contextValue = "adr";
        item.resourceUri = vscode.Uri.file(filePath);
        item.iconPath = new vscode.ThemeIcon("book");
        return item;
      });

      if (items.length === 0) {
        items.push(new SidebarItem("No ADRs found", vscode.TreeItemCollapsibleState.None));
      }

      return Promise.resolve(items);
    } catch {
      return Promise.resolve([
        new SidebarItem("Error reading ADRs", vscode.TreeItemCollapsibleState.None),
      ]);
    }
  }
}

export function registerSidebar(context: vscode.ExtensionContext): void {
  const findingsProvider = new FindingsProvider();
  context.subscriptions.push(
    vscode.window.registerTreeDataProvider("decisiondrift.results", findingsProvider)
  );

  context.subscriptions.push(
    vscode.workspace.onDidChangeTextDocument(() => findingsProvider.refresh())
  );

  context.subscriptions.push(
    vscode.workspace.onDidSaveTextDocument(() => findingsProvider.refresh())
  );

  const adrProvider = new AdrProvider();
  context.subscriptions.push(
    vscode.window.registerTreeDataProvider("decisiondrift.adrs", adrProvider)
  );

  context.subscriptions.push(
    vscode.workspace.onDidChangeConfiguration((e) => {
      if (e.affectsConfiguration("decisiondrift.adrDir")) {
        adrProvider.refresh();
      }
    })
  );
}
