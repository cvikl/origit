/**
 * tree.ts — TreeDataProvider for the origit.sessions view.
 *
 * Tree structure:
 *   Session  ("#42 · Bob IDE · origit-build · 3 runs")
 *     └─ Commit  ("<short sha> <subject>")
 *          └─ Group  ("Read (n)", "Wrote (n)", "Dependencies (n)", "Commands (n)")
 *               └─ LeafItem  (approver, tests, record hash, etc.)
 */
import * as vscode from "vscode";
import type { Session, Run, Prefilter } from "./origit";

// ── Node types ────────────────────────────────────────────────────────────────

export type TreeNode = SessionNode | CommitNode | GroupNode | LeafNode | ErrorNode;

export class SessionNode extends vscode.TreeItem {
  readonly kind = "session";
  constructor(public readonly session: Session) {
    const who = session.actor === "bob-ide" ? "Bob IDE" : session.actor === "human" ? "human" : "no record";
    const parts = [session.label, who];
    if (session.mode) {
      parts.push(session.mode);
    }
    parts.push(`${session.runs.length} ${session.actor === "bob-ide" ? "run" : "commit"}${session.runs.length === 1 ? "" : "s"}`);
    const label = parts.join(" · ");
    super(label, vscode.TreeItemCollapsibleState.Collapsed);
    this.iconPath = actorIcon(session.actor);
    this.contextValue = "session";
  }
}

export class CommitNode extends vscode.TreeItem {
  readonly kind = "commit";
  constructor(
    public readonly session: Session,
    public readonly run: Run,
    tainted: boolean
  ) {
    const shortSha = run.sha.slice(0, 7);
    const baseLabel = `${shortSha} ${run.subject}`;
    super(baseLabel, run.record ? vscode.TreeItemCollapsibleState.Collapsed : vscode.TreeItemCollapsibleState.None);
    if (tainted) {
      this.iconPath = new vscode.ThemeIcon("error", new vscode.ThemeColor("charts.red"));
    } else {
      this.iconPath = severityIcon(run.prefilter);
    }
    this.description = run.record
      ? `${run.n_read} read · ${run.n_wrote} wrote${run.n_deps ? ` · ${run.n_deps} deps` : ""}${tainted ? " · affected" : ""}`
      : "no record";
    this.tooltip = new vscode.MarkdownString(
      `**Commit** \`${run.sha}\`\n\n**Session** \`${session.id}\`\n\n**Record sha256** \`${run.record?.record_sha256 ?? "—"}\``
    );
    this.contextValue = tainted ? "commit_tainted" : "commit";
  }
}

export class GroupNode extends vscode.TreeItem {
  readonly kind = "group";
  constructor(
    public readonly groupLabel: string,
    public readonly count: number,
    public readonly children: LeafNode[]
  ) {
    super(`${groupLabel} (${count})`, vscode.TreeItemCollapsibleState.Collapsed);
    this.contextValue = "group";
  }
}

export class LeafNode extends vscode.TreeItem {
  readonly kind = "leaf";
  constructor(label: string, description?: string) {
    super(label, vscode.TreeItemCollapsibleState.None);
    if (description) {
      this.description = description;
    }
    this.contextValue = "leaf";
  }
}

export class ErrorNode extends vscode.TreeItem {
  readonly kind = "error";
  constructor(message: string) {
    super(message, vscode.TreeItemCollapsibleState.None);
    this.iconPath = new vscode.ThemeIcon("error");
    this.contextValue = "error";
  }
}

// ── Icon helpers ──────────────────────────────────────────────────────────────

function actorIcon(actor: string): vscode.ThemeIcon {
  if (actor === "bob-ide") {
    return new vscode.ThemeIcon("robot");
  }
  if (!actor || actor === "none") {
    return new vscode.ThemeIcon("circle-outline");
  }
  return new vscode.ThemeIcon("person");
}

function severityIcon(prefilter: Prefilter | undefined): vscode.ThemeIcon {
  const sev = prefilter?.max_severity;
  if (sev === null || sev === undefined) {
    return new vscode.ThemeIcon("circle-filled", new vscode.ThemeColor("charts.green"));
  }
  switch (sev) {
    case "critical":
    case "high":
      return new vscode.ThemeIcon("circle-filled", new vscode.ThemeColor("charts.red"));
    case "medium":
      return new vscode.ThemeIcon("circle-filled", new vscode.ThemeColor("charts.orange"));
    case "low":
      return new vscode.ThemeIcon("circle-filled", new vscode.ThemeColor("charts.yellow"));
    case "informational":
      return new vscode.ThemeIcon("circle-filled", new vscode.ThemeColor("charts.blue"));
    default:
      return new vscode.ThemeIcon("circle-filled", new vscode.ThemeColor("charts.green"));
  }
}

// ── Provider ──────────────────────────────────────────────────────────────────

export class OrigitTreeProvider implements vscode.TreeDataProvider<TreeNode> {
  private _onDidChangeTreeData = new vscode.EventEmitter<TreeNode | undefined | null | void>();
  readonly onDidChangeTreeData = this._onDidChangeTreeData.event;

  private sessions: Session[] = [];
  private error: string | null = null;
  /** sha → true */
  private taintedShas: Set<string> = new Set();

  setData(sessions: Session[], error: string | null): void {
    this.sessions = sessions;
    this.error = error;
    this._onDidChangeTreeData.fire();
  }

  setTaint(shas: Set<string>): void {
    this.taintedShas = shas;
    this._onDidChangeTreeData.fire();
  }

  clearTaint(): void {
    this.taintedShas = new Set();
    this._onDidChangeTreeData.fire();
  }

  getTreeItem(element: TreeNode): vscode.TreeItem {
    return element;
  }

  getChildren(element?: TreeNode): TreeNode[] {
    if (!element) {
      // root
      if (this.error) {
        return [new ErrorNode(this.error)];
      }
      if (this.sessions.length === 0) {
        return [new ErrorNode("No origit sessions found.")];
      }
      return this.sessions.map((s) => new SessionNode(s));
    }

    if (element.kind === "session") {
      return element.session.runs.map(
        (r) => new CommitNode(element.session, r, this.taintedShas.has(r.sha))
      );
    }

    if (element.kind === "commit") {
      return buildCommitChildren(element.run);
    }

    if (element.kind === "group") {
      return element.children;
    }

    return [];
  }
}

// ── Build commit child nodes (everything comes from the record in `origit log --json`)

function buildCommitChildren(run: Run): TreeNode[] {
  const rec = run.record;
  if (!rec) {
    return [new LeafNode("No Origit record for this commit")];
  }
  const nodes: TreeNode[] = [];
  nodes.push(new GroupNode("Read", rec.read.length, rec.read.length
    ? rec.read.map((r) => new LeafNode(r.ref, `${r.kind}${r.sha256 ? ` · ${r.sha256.slice(0, 10)}` : ""}`))
    : [new LeafNode("(nothing read)")]));
  nodes.push(new GroupNode("Wrote", rec.wrote.length, rec.wrote.length
    ? rec.wrote.map((w) => new LeafNode(w))
    : [new LeafNode("(nothing written)")]));
  nodes.push(new GroupNode("Dependencies", rec.added_deps.length, rec.added_deps.length
    ? rec.added_deps.map((d) => new LeafNode(`${d.name}@${d.version}`, d.registry ?? "npm"))
    : [new LeafNode("(none added)")]));
  nodes.push(new GroupNode("Commands", rec.commands.length, rec.commands.length
    ? rec.commands.map((c) => new LeafNode(c.split("\n")[0].slice(0, 120)))
    : [new LeafNode("(none)")]));
  nodes.push(new LeafNode(`Approver: ${rec.approver ?? "none"}`, rec.approved_at ?? undefined));
  const t = rec.tests;
  nodes.push(new LeafNode(t && t.run ? `Tests: ${t.passed} passed, ${t.failed} failed` : "Tests: not run"));
  nodes.push(new LeafNode(`Record sha256: ${rec.record_sha256.slice(0, 12)}`, rec.record_sha256));
  if (rec.session.prompt) {
    nodes.push(new LeafNode(`Prompt: ${rec.session.prompt.slice(0, 100)}`));
  }
  return nodes;
}
