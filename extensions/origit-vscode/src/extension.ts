/**
 * extension.ts — VS Code extension entry point for "Origit for Bob IDE".
 *
 * Registers the TreeDataProvider, commands, status bar item, file-system
 * watchers and the 15-second auto-refresh timer.
 *
 * NO business logic lives here — all data comes from origit CLI via origit.ts.
 */
import * as vscode from "vscode";
import { OrigitTreeProvider, CommitNode } from "./tree";
import type { TreeNode } from "./tree";
import {
  fetchLog,
  fetchSessionStatus,
  fetchTaint,
  fetchRecord,
} from "./origit";

// ── Activation ────────────────────────────────────────────────────────────────

export function activate(context: vscode.ExtensionContext): void {
  const provider = new OrigitTreeProvider();

  // Tree view
  const treeView = vscode.window.createTreeView("origit.sessions", {
    treeDataProvider: provider,
    showCollapseAll: true,
  });
  context.subscriptions.push(treeView);

  // Status bar
  const statusBar = vscode.window.createStatusBarItem(
    vscode.StatusBarAlignment.Left,
    100
  );
  statusBar.show();
  context.subscriptions.push(statusBar);

  // ── Taint state ──────────────────────────────────────────────────────────
  let currentTaintShas: Set<string> = new Set();

  // ── Refresh logic ─────────────────────────────────────────────────────────
  async function refresh(): Promise<void> {
    try {
      const log = await fetchLog();
      provider.setData(log.sessions, null);
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      provider.setData([], `Origit CLI not found: ${msg}`);
    }

    // Re-apply taint after refresh
    if (currentTaintShas.size > 0) {
      provider.setTaint(currentTaintShas);
    }

    await refreshStatusBar(statusBar);
  }

  // ── Status bar ────────────────────────────────────────────────────────────
  async function refreshStatusBar(bar: vscode.StatusBarItem): Promise<void> {
    try {
      const status = await fetchSessionStatus();
      if (status && status.recording && status.number !== undefined) {
        bar.text = `$(record) Origit: session #${status.number} run ${status.run ?? 0} · recording`;
        bar.tooltip = `Origit session ${status.id ?? ""}`;
      } else {
        bar.text = "$(circle-outline) Origit: idle";
      }
    } catch {
      bar.text = "$(circle-outline) Origit: idle";
    }
  }

  // ── Commands ──────────────────────────────────────────────────────────────

  context.subscriptions.push(
    vscode.commands.registerCommand("origit.refresh", () => {
      void refresh();
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand("origit.taint", async () => {
      const needle = await vscode.window.showInputBox({
        title: "Origit: Taint",
        prompt: "Enter a package name, file path or sha256 to taint",
        placeHolder: "e.g. requests, src/app.py, or abc123…",
      });
      if (!needle) {
        return;
      }
      try {
        const result = await fetchTaint(needle);
        const shas = new Set(result.affected.map((a) => a.sha));
        currentTaintShas = shas;
        provider.setTaint(shas);

        if (result.affected.length === 0) {
          await vscode.window.showInformationMessage("0 commits affected.");
          return;
        }

        const labels = result.session_labels ?? {};
        const sessionLabels = result.sessions
          .map((s) => labels[s] ?? s.slice(0, 7))
          .sort((a, b) => Number(a.replace("#", "")) - Number(b.replace("#", "")))
          .join(" ");
        const rollback = result.rollback_commit ? result.rollback_commit.slice(0, 7) : "—";
        await vscode.window.showInformationMessage(
          `${result.affected.length} commit${result.affected.length === 1 ? "" : "s"} affected by ${result.needle} · sessions ${sessionLabels} · roll back to ${rollback}`
        );
      } catch (err) {
        const msg = err instanceof Error ? err.message : String(err);
        await vscode.window.showErrorMessage(`Origit taint failed: ${msg}`);
      }
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand("origit.clearTaint", () => {
      currentTaintShas = new Set();
      provider.clearTaint();
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand(
      "origit.showRecord",
      async (node: TreeNode) => {
        if (!(node instanceof CommitNode)) {
          return;
        }
        try {
          const record = await fetchRecord(node.run.sha);
          const json = JSON.stringify(record, null, 2);
          const doc = await vscode.workspace.openTextDocument({
            language: "json",
            content: json,
          });
          await vscode.window.showTextDocument(doc);
        } catch (err) {
          const msg = err instanceof Error ? err.message : String(err);
          await vscode.window.showErrorMessage(
            `Origit: could not fetch record: ${msg}`
          );
        }
      }
    )
  );

  // ── File system watchers ──────────────────────────────────────────────────
  const origitWatcher = vscode.workspace.createFileSystemWatcher("**/.origit/**");
  const notesWatcher = vscode.workspace.createFileSystemWatcher(
    "**/.git/refs/notes/**"
  );

  const onWatcherEvent = () => void refresh();
  origitWatcher.onDidChange(onWatcherEvent, undefined, context.subscriptions);
  origitWatcher.onDidCreate(onWatcherEvent, undefined, context.subscriptions);
  origitWatcher.onDidDelete(onWatcherEvent, undefined, context.subscriptions);
  notesWatcher.onDidChange(onWatcherEvent, undefined, context.subscriptions);
  notesWatcher.onDidCreate(onWatcherEvent, undefined, context.subscriptions);
  notesWatcher.onDidDelete(onWatcherEvent, undefined, context.subscriptions);

  context.subscriptions.push(origitWatcher, notesWatcher);

  // ── 15-second auto-refresh ────────────────────────────────────────────────
  const timer = setInterval(() => void refresh(), 15_000);
  context.subscriptions.push({ dispose: () => clearInterval(timer) });

  // ── Initial load ──────────────────────────────────────────────────────────
  void refresh();
}

export function deactivate(): void {
  // nothing — subscriptions are disposed automatically
}
