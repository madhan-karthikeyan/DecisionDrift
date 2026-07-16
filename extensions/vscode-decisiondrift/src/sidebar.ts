import * as vscode from "vscode";
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
}
