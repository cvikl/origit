"""Origit MCP server (stdio) — lets IBM Bob ask provenance questions in chat.

Started by ``origit mcp`` from ``.bob/mcp.json`` (installed by ``origit init``). Pure stdlib; no network.
Protocol: MCP over stdio, JSON-RPC 2.0, one JSON object per line on stdin/stdout (newline-delimited).

Methods
  initialize              -> {"protocolVersion": "2024-11-05", "capabilities": {"tools": {}},
                              "serverInfo": {"name": "origit", "version": <origit.__version__>}}
  notifications/initialized  (no response)
  ping                    -> {}
  tools/list              -> {"tools": [TOOLS...]} where each tool has name, description, inputSchema (JSON schema)
  tools/call              -> {"content": [{"type": "text", "text": <JSON string of the result>}], "isError": false}
                             on a tool error: isError true and the message in content
  unknown method          -> JSON-RPC error {"code": -32601, "message": "method not found"}
  notifications (no "id") never get a response; malformed lines are ignored.

Tools (all read-only, all answered by the deterministic core — no model, no subprocess to the CLI)
  origit_taint  {"needle": str}                      -> taint.query(...) result plus "session_labels" and
                                                        per-affected "session_label" (see cli.taint --json)
  origit_show   {"commit": str = "HEAD"}             -> {"sha", "subject", "verified", "record"} ({"record": None} when missing)
  origit_log    {"limit": int = 20}                  -> {"repo", "head", "base", "sessions": sessions.group(...)[:limit]}
                                                        (each run without the full "record" to keep answers short;
                                                        keep n_read/n_wrote/n_deps/tests/approver/sha/subject/run)

``serve(root)`` runs the loop until stdin closes. ``handle(request, root)`` maps one request dict to one response
dict (or None for notifications) and is what the tests call directly; it must never raise.
Helper ``resolve(root, ref)`` -> full sha via ``git rev-parse`` (the one allowed git call, through subprocess).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from typing import Any

from . import __version__
from . import notes as N
from . import record as R
from . import sessions as S
from . import taint as X


# ---------------------------------------------------------------------------
# Tool definitions

TOOLS = [
    {
        "name": "origit_taint",
        "description": (
            "Which commits did an agent write after reading a package, file, or sha256 hash? "
            "Returns affected commits, session labels, files written, approvers, and rollback info."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "needle": {
                    "type": "string",
                    "description": "Package name (fast-pay-utils), spec (fast-pay-utils@2.1.0), file path, or sha256 hex.",
                },
            },
            "required": ["needle"],
        },
    },
    {
        "name": "origit_show",
        "description": (
            "Show the full Origit provenance record for a commit. "
            "Returns sha, subject, verified flag, and the full record (or null if missing)."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "commit": {
                    "type": "string",
                    "description": "Git ref or sha (default: HEAD).",
                },
            },
        },
    },
    {
        "name": "origit_log",
        "description": (
            "Session log: commits grouped by agent session, newest first. "
            "Returns repo, head, base, and a sessions list with summarised runs (no full records)."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of sessions to return (default: 20).",
                },
            },
        },
    },
]


# ---------------------------------------------------------------------------
# Git helper

def resolve(root: str, ref: str) -> str:
    """Return the full sha for ``ref`` via git rev-parse. Raises RuntimeError on failure."""
    p = subprocess.run(
        ["git", "-C", root, "rev-parse", ref],
        capture_output=True, text=True,
    )
    if p.returncode != 0:
        raise RuntimeError(f"git rev-parse {ref!r} failed: {p.stderr.strip()}")
    return p.stdout.strip()


# ---------------------------------------------------------------------------
# Tool implementations

def _tool_taint(args: dict, root: str) -> Any:
    needle = args.get("needle", "")
    cs = N.commits(root)
    out = X.query(cs, needle)
    base = S.base(root)
    labels = S.number_sessions(cs, base)
    out["session_labels"] = {sid: S.label(labels[sid]) for sid in out["sessions"] if sid in labels}
    for c in out["affected"]:
        c["session_label"] = out["session_labels"].get(c["session"], c["session"])
    if out.get("first_read"):
        out["first_read"]["label"] = out["session_labels"].get(
            out["first_read"]["session"], out["first_read"]["session"]
        )
    return out


def _tool_show(args: dict, root: str) -> Any:
    ref = args.get("commit") or "HEAD"
    sha = resolve(root, ref)
    rec = N.read(root, sha)
    p = subprocess.run(
        ["git", "-C", root, "log", "-1", "--format=%s", sha],
        capture_output=True, text=True,
    )
    subject = p.stdout.strip() if p.returncode == 0 else ""
    if rec is None:
        return {"sha": sha, "subject": subject, "verified": False, "record": None}
    return {"sha": sha, "subject": subject, "verified": R.verify(rec), "record": rec}


def _tool_log(args: dict, root: str) -> Any:
    limit = int(args.get("limit") or 20)
    cs = N.commits(root)
    base = S.base(root)
    groups = S.group(cs, base)[:limit]
    # Strip full record from each run, keeping only the summary fields
    _KEEP = {"run", "sha", "subject", "n_read", "n_wrote", "n_deps", "tests", "approver"}
    for g in groups:
        g["runs"] = [{k: v for k, v in run.items() if k in _KEEP} for run in g["runs"]]
    head = N.head(root)
    return {"repo": os.path.basename(root), "head": head, "base": base, "sessions": groups}


# ---------------------------------------------------------------------------
# JSON-RPC helpers

def _ok(req_id: Any, result: Any) -> dict:
    return {"jsonrpc": "2.0", "id": req_id, "result": result}


def _err(req_id: Any, code: int, message: str) -> dict:
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}


def _tool_result(data: Any) -> dict:
    return {"content": [{"type": "text", "text": json.dumps(data, ensure_ascii=False)}], "isError": False}


def _tool_error(message: str) -> dict:
    return {"content": [{"type": "text", "text": message}], "isError": True}


# ---------------------------------------------------------------------------
# Main dispatcher

_TOOL_FNS = {
    "origit_taint": _tool_taint,
    "origit_show": _tool_show,
    "origit_log": _tool_log,
}


def handle(request: dict, root: str) -> dict | None:
    """Map one JSON-RPC request dict to a response dict, or None for notifications. Never raises."""
    try:
        req_id = request.get("id")
        method = request.get("method", "")

        # Notifications: no "id" key present -> no response
        if "id" not in request:
            return None

        if method == "initialize":
            return _ok(req_id, {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "origit", "version": __version__},
            })

        if method == "ping":
            return _ok(req_id, {})

        if method == "tools/list":
            return _ok(req_id, {"tools": TOOLS})

        if method == "tools/call":
            params = request.get("params") or {}
            name = params.get("name", "")
            arguments = params.get("arguments") or {}
            fn = _TOOL_FNS.get(name)
            if fn is None:
                return _ok(req_id, _tool_error(f"unknown tool: {name!r}"))
            try:
                result = fn(arguments, root)
                return _ok(req_id, _tool_result(result))
            except Exception as exc:  # noqa: BLE001
                return _ok(req_id, _tool_error(str(exc)))

        # Unknown method
        return _err(req_id, -32601, "method not found")

    except Exception as exc:  # noqa: BLE001 — handle() must never raise
        try:
            req_id = request.get("id")
        except Exception:  # noqa: BLE001
            req_id = None
        return _err(req_id, -32603, f"internal error: {exc}")


# ---------------------------------------------------------------------------
# stdio serve loop

def serve(root: str) -> None:  # pragma: no cover
    """Run the MCP server: read newline-delimited JSON from stdin, write responses to stdout."""
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
        except json.JSONDecodeError:
            continue  # malformed lines are ignored per spec
        response = handle(request, root)
        if response is not None:
            sys.stdout.write(json.dumps(response, ensure_ascii=False) + "\n")
            sys.stdout.flush()
