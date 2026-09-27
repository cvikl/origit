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


def serve(root: str) -> None:  # pragma: no cover — implemented by IBM Bob (task 11)
    raise NotImplementedError("origit mcp: not implemented yet")


def handle(request: dict, root: str) -> dict | None:  # pragma: no cover — implemented by IBM Bob (task 11)
    raise NotImplementedError
