/**
 * origit.ts — thin wrapper around the origit CLI.
 *
 * All data in the extension comes exclusively from running `origit <cmd> --json`
 * via child_process.execFile and parsing the JSON response.
 *
 * CLI resolution order:
 *   1. VS Code setting origit.binary
 *   2. `git config origit.bin` in the workspace folder
 *   3. "origit" on PATH
 */
import * as vscode from "vscode";
import { execFile } from "child_process";
import * as path from "path";
import * as fs from "fs";

// ── JSON shapes ───────────────────────────────────────────────────────────────

export interface Prefilter {
  needs_review: boolean;
  max_severity: "critical" | "high" | "medium" | "low" | "informational" | null;
}

export interface Tests {
  run: boolean;
  passed: number;
  failed: number;
}

export interface OrigitRecord {
  session: { id: string; number?: number | null; run?: number | null; started_at?: string | null; ended_at?: string | null; prompt?: string };
  actor: { kind: string; mode?: string | null; model?: string | null; config_sha256?: string | null };
  read: Array<{ kind: string; ref: string; sha256?: string | null }>;
  wrote: string[];
  added_deps: Array<{ name: string; version: string; registry?: string; lockfile_sha256?: string | null }>;
  commands: string[];
  author?: string;
  approver?: string | null;
  approved_at?: string | null;
  tests: Tests;
  record_sha256: string;
}

export interface Run {
  run: number | null;
  sha: string;
  subject: string;
  n_read: number;
  n_wrote: number;
  n_deps: number;
  tests: Tests | null;
  approver: string | null;
  prefilter?: Prefilter;
  record: OrigitRecord | null;
}

export interface Session {
  id: string;
  number: number | null;
  label: string;
  actor: string;
  mode: string | null;
  started_at: string | null;
  ended_at: string | null;
  runs: Run[];
}

export interface LogOutput {
  sessions: Session[];
}

export interface SessionStatus {
  id?: string;
  number?: number;
  label?: string;
  run?: number;
  recording: boolean;
}

export interface TaintOutput {
  needle: string;
  affected: Array<{ sha: string; subject: string; session: string; session_label?: string; matched: string[] }>;
  sessions: string[];
  session_labels?: Record<string, string>;
  files_written: string[];
  first_read: { session: string; at: string | null; commit: string; label?: string } | null;
  rollback_commit: string | null;
  clean: Array<{ sha: string; subject: string }>;
}

// ── CLI resolution ────────────────────────────────────────────────────────────

function workspaceCwd(): string | undefined {
  return vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
}

async function resolveBinary(): Promise<string> {
  const cfg = vscode.workspace.getConfiguration("origit").get<string>("binary");
  if (cfg && cfg.trim()) {
    return cfg.trim();
  }

  const cwd = workspaceCwd();
  if (cwd) {
    try {
      const bin = await runRaw("git", ["config", "origit.bin"], cwd);
      const trimmed = bin.trim();
      if (trimmed) {
        return trimmed;
      }
    } catch {
      // not set — fall through
    }
  }

  return "origit";
}

function runRaw(
  binary: string,
  args: string[],
  cwd: string | undefined
): Promise<string> {
  return new Promise((resolve, reject) => {
    execFile(binary, args, { cwd }, (err, stdout, stderr) => {
      if (err) {
        reject(new Error(stderr || err.message));
      } else {
        resolve(stdout);
      }
    });
  });
}

async function run(args: string[]): Promise<string> {
  const binary = await resolveBinary();
  const cwd = workspaceCwd();
  return runRaw(binary, args, cwd);
}

// ── Public helpers ─────────────────────────────────────────────────────────────

export async function fetchLog(): Promise<LogOutput> {
  const raw = await run(["log", "--json"]);
  return JSON.parse(raw) as LogOutput;
}

export async function fetchSessionStatus(): Promise<SessionStatus | null> {
  try {
    const raw = await run(["session", "status", "--json"]);
    return JSON.parse(raw) as SessionStatus;
  } catch {
    // fall back to reading .origit/session.json from workspace
    const cwd = workspaceCwd();
    if (cwd) {
      const sessionFile = path.join(cwd, ".origit", "session.json");
      try {
        const content = fs.readFileSync(sessionFile, "utf8");
        const obj = JSON.parse(content) as {
          id: string;
          number: number;
          run: number;
          label?: string;
        };
        return {
          id: obj.id,
          number: obj.number,
          label: obj.label ?? `#${obj.number}`,
          run: obj.run,
          recording: true,
        };
      } catch {
        return null;
      }
    }
    return null;
  }
}

export async function fetchTaint(needle: string): Promise<TaintOutput> {
  const raw = await run(["taint", needle, "--json"]);
  return JSON.parse(raw) as TaintOutput;
}

export async function fetchRecord(sha: string): Promise<unknown> {
  const raw = await run(["show", sha, "--json"]);
  return JSON.parse(raw);
}
