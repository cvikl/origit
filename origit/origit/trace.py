"""Trace: consume Bob IDE lifecycle-hook payloads and fold them into a record.

Source of truth for ``read[]``. Bob IDE hooks (``.bob/settings.json``) run
``origit trace`` on SessionStart / PreToolUse / PostToolUse / Stop and pipe the
hook's JSON payload on stdin:

    {"event": "PostToolUse", "session_id": "ses_01abc123",
     "tool": "read_file", "input": {"path": "src/index.ts"}, "output": "..."}

``append_event`` writes one JSON line per event to ``.origit/trace.jsonl`` with
a UTC ``ts`` added. ``fold`` turns the lines accumulated since the last commit
into the session / actor / read / wrote / added_deps / commands parts of a
record (see record.py). Never calls a model. Never blocks Bob.

Trace lines may also be in the fallback tracer's wrapped form
``{"ts": "...", "raw": {...payload...}}``; ``unwrap`` normalises both.
"""

from __future__ import annotations

import datetime as _dt
import json
import os
import re
import sys
from typing import Any

from . import STATE_DIR, TRACE_FILE

# Bob IDE built-in tool names (docs: /docs/ide/core-concepts/tools). Confirmed live by hookcheck.
READ_TOOLS = {"read_file", "glob", "grep", "list_files", "GetSymbolsOverview", "FindSymbol", "FindReferencingSymbols"}
WRITE_TOOLS = {"write_file", "apply_diff", "insert_content", "search_and_replace"}
EXEC_TOOLS = {"execute_command"}
MCP_TOOLS = {"use_mcp_tool", "access_mcp_resource"}
URL_TOOLS = {"fetch_url", "web_fetch", "browser_action"}
AGENT_TOOLS = {"spawn_subagent", "start_subtask", "switch_mode", "use_skill", "start_workflow"}


def utcnow() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def trace_path(root: str = ".") -> str:
    return os.path.join(root, STATE_DIR, TRACE_FILE)


def append_event(payload: dict[str, Any], root: str = ".") -> None:
    """Append one hook payload (plus ``ts``) to the trace file. Drops bulky fields."""
    os.makedirs(os.path.join(root, STATE_DIR), exist_ok=True)
    slim = dict(payload)
    slim["ts"] = utcnow()
    for key in ("input", "tool_input"):
        if isinstance(slim.get(key), dict):
            slim[key] = {k: v for k, v in slim[key].items() if k not in ("content", "diff")}
    for key in ("output", "tool_response"):
        if isinstance(slim.get(key), str) and len(slim[key]) > 2000:
            slim[key] = slim[key][:2000] + "…"
    with open(trace_path(root), "a", encoding="utf-8") as f:
        f.write(json.dumps(slim, ensure_ascii=False) + "\n")


def read_stdin_payload() -> dict[str, Any] | None:
    raw = sys.stdin.read()
    if not raw.strip():
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"event": "unparsed", "raw": raw[:4000]}


def iter_events(root: str = ".") -> list[dict[str, Any]]:
    p = trace_path(root)
    if not os.path.exists(p):
        return []
    out = []
    with open(p, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return out


def unwrap(event: dict[str, Any]) -> dict[str, Any]:
    """Normalise a trace line to {event, session_id, tool, input, output, ts, cwd}.

    Accepts the documented schema (event/tool/input/output), the live Bob IDE 2.2 schema
    (hook_event_name/tool_name/tool_input/tool_response, plus cwd and tool_use_id), and the
    fallback tracer's wrapped form {"ts", "raw": {...}}.
    """
    if isinstance(event.get("raw"), dict):
        inner = dict(event["raw"])
        inner["ts"] = event.get("ts")
        event = inner
    out = dict(event)
    out["event"] = event.get("event") or event.get("hook_event_name")
    out["tool"] = event.get("tool") or event.get("tool_name")
    inp = event.get("input") if isinstance(event.get("input"), dict) else event.get("tool_input")
    out["input"] = inp if isinstance(inp, dict) else {}
    if "output" not in out and "tool_response" in event:
        out["output"] = event["tool_response"]
    return out


_NPM_RE = re.compile(r"^\s*(?:npm|pnpm|yarn)\s+(?:install|i|add)\s+(.*)$")


def split_spec(tok: str) -> tuple[str, str | None]:
    """'name@1.2.3' -> (name, '1.2.3'); '@scope/name@1.2.3' -> ('@scope/name', '1.2.3'); 'name' -> (name, None)."""
    if tok.startswith("@"):
        rest = tok[1:]
        if "@" in rest:
            n, v = rest.rsplit("@", 1)
            return "@" + n, v
        return tok, None
    if "@" in tok:
        n, v = tok.rsplit("@", 1)
        return n, v
    return tok, None


def parse_npm_install(command: str) -> list[dict[str, Any]]:
    """``npm install|i|add <name>@<ver> ...`` -> [{name, version, registry: "npm", lockfile_sha256: None}].
    Ignores flags and specs without an explicit version (file:, link:, bare names)."""
    m = _NPM_RE.match(command)
    if not m:
        return []
    out = []
    for tok in m.group(1).split():
        if tok.startswith("-") or tok.startswith(".") or tok.startswith("/") or ":" in tok:
            continue
        name, ver = split_spec(tok)
        if name and ver:
            out.append({"name": name, "version": ver, "registry": "npm", "lockfile_sha256": None})
    return out


def fold(events: list[dict[str, Any]]) -> dict[str, Any]:
    """Fold trace events into the agent-derived parts of a record.

    Returns {session, actor, read, wrote, added_deps, commands}:
      session   {id: last session_id seen, started_at: first ts, ended_at: last ts}
      actor     {kind: "bob-ide", ...}; kind "human" if there are no events
      read      from PostToolUse only (the tool actually ran), de-duplicated, first-seen order:
                  READ_TOOLS -> file input.path (default "."); MCP_TOOLS -> mcp server/tool;
                  URL_TOOLS -> url; each added dep -> pkg name@version
      wrote     sorted unique input.path of WRITE_TOOLS PostToolUse events
      commands  input.command of EXEC_TOOLS PostToolUse events, in order
      added_deps parsed from commands via ``parse_npm_install``
    Content hashes are filled in later by ``origit record fold`` while the files still exist.
    """
    evs = [unwrap(e) for e in events]
    empty = {
        "session": {"id": None, "started_at": None, "ended_at": None},
        "actor": {"kind": "human", "model": None, "mode": None, "config_sha256": None},
        "read": [], "wrote": [], "added_deps": [], "commands": [],
    }
    if not evs:
        return empty
    tss = [e["ts"] for e in evs if e.get("ts")]
    sids = [e["session_id"] for e in evs if e.get("session_id")]
    reads: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()

    def add(kind: str, ref: str) -> None:
        if ref and (kind, ref) not in seen:
            seen.add((kind, ref))
            reads.append({"kind": kind, "ref": ref, "sha256": None})

    wrote: set[str] = set()
    commands: list[str] = []
    for e in evs:
        if e.get("event") != "PostToolUse":
            continue
        tool = e.get("tool") or ""
        inp = e.get("input") if isinstance(e.get("input"), dict) else {}
        if tool in READ_TOOLS:
            add("file", str(inp.get("path") or inp.get("pattern") or "."))
        elif tool in WRITE_TOOLS:
            if inp.get("path"):
                wrote.add(str(inp["path"]))
        elif tool in EXEC_TOOLS:
            if inp.get("command"):
                commands.append(str(inp["command"]))
        elif tool in MCP_TOOLS:
            add("mcp", f"{inp.get('server_name', '?')}/{inp.get('tool_name') or inp.get('uri') or '?'}")
        elif tool in URL_TOOLS:
            if inp.get("url"):
                add("url", str(inp["url"]))
    deps: list[dict[str, Any]] = []
    for c in commands:
        for d in parse_npm_install(c):
            if d not in deps:
                deps.append(d)
                add("pkg", f"{d['name']}@{d['version']}")
    return {
        "session": {"id": sids[-1] if sids else None, "started_at": tss[0] if tss else None, "ended_at": tss[-1] if tss else None},
        "actor": {"kind": "bob-ide", "model": None, "mode": None, "config_sha256": None},
        "read": reads,
        "wrote": sorted(wrote),
        "added_deps": deps,
        "commands": commands,
    }


def clear(root: str = ".") -> None:
    """Truncate the trace after it has been folded into a committed record."""
    p = trace_path(root)
    if os.path.exists(p):
        open(p, "w").close()
