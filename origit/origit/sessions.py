"""Session display ids and grouping of commits by agent session and run.

A Bob session id is a 32-hex hash. People, decks and videos need short ids: ``#42``.

* ``number_sessions(commits, base=1)`` -> ``{session_id: int}``. ``commits`` is newest-first
  ``(sha, subject, record|None)`` as returned by ``notes.commits``. A record may carry
  ``session.number`` (assigned by ``origit session start`` since Sunday). Sessions without a
  number get one by first appearance, oldest commit first, starting at ``base`` and skipping
  numbers that are already taken. Deterministic for a given history.
* ``label(n)`` -> ``"#42"``.
* ``group(commits, base=1)`` -> newest-first list of sessions, each with its runs (commits),
  for ``origit log`` and the console:
  ``{"id", "number", "label", "actor", "mode", "started_at", "ended_at", "runs": [
       {"run", "sha", "subject", "n_read", "n_wrote", "n_deps", "tests", "approver", "record"}]}``
  Human commits (``actor.kind == "human"``) and commits without a record are grouped under a
  pseudo-session with ``id`` ``"human"`` / ``"none"`` and ``number`` None.
* ``base(root)`` reads ``.origit/config.json`` ``{"session_base": 42}`` from the working tree
  (the demo repo starts at #42); default 1. The console reads the same file at HEAD.
"""

from __future__ import annotations

import json
import os
from typing import Any

from . import STATE_DIR

CONFIG_FILE = "config.json"


def base(root: str = ".") -> int:
    try:
        with open(os.path.join(root, STATE_DIR, CONFIG_FILE), encoding="utf-8") as f:
            return int(json.load(f).get("session_base", 1))
    except (OSError, ValueError, TypeError):
        return 1


def label(n: int | None) -> str:
    return f"#{n}" if n is not None else "–"


def number_sessions(commits: list[tuple[str, str, dict[str, Any] | None]], base: int = 1) -> dict[str, int]:
    out: dict[str, int] = {}
    for _sha, _subj, rec in reversed(commits):  # oldest first
        if not rec or rec.get("actor", {}).get("kind") == "human":
            continue
        sid = rec.get("session", {}).get("id")
        num = rec.get("session", {}).get("number")
        if sid and isinstance(num, int) and sid not in out:
            out[sid] = num
    taken = set(out.values())
    nxt = base
    for _sha, _subj, rec in reversed(commits):
        if not rec or rec.get("actor", {}).get("kind") == "human":
            continue
        sid = rec.get("session", {}).get("id")
        if not sid or sid in out:
            continue
        while nxt in taken:
            nxt += 1
        out[sid] = nxt
        taken.add(nxt)
        nxt += 1
    return out


def next_number(commits: list[tuple[str, str, dict[str, Any] | None]], base: int = 1) -> int:
    """The number a new session gets: one above the highest in use, never below ``base``."""
    nums = number_sessions(commits, base).values()
    return max([base - 1, *nums]) + 1


def group(commits: list[tuple[str, str, dict[str, Any] | None]], base: int = 1) -> list[dict[str, Any]]:
    numbers = number_sessions(commits, base)
    sessions: list[dict[str, Any]] = []
    by_key: dict[str, dict[str, Any]] = {}
    for sha, subject, rec in commits:  # newest first
        if not rec:
            key, sid, num = "none", "none", None
        elif rec["actor"].get("kind") == "human":
            key, sid, num = "human", "human", None
        else:
            sid = rec["session"].get("id") or "unknown"
            key, num = sid, numbers.get(sid)
        s = by_key.get(key)
        if s is None or key in ("human", "none") and sessions and sessions[-1] is not s:
            s = {"id": sid, "number": num, "label": label(num) if num is not None else sid,
                 "actor": (rec or {}).get("actor", {}).get("kind", "none") if rec else "none",
                 "mode": (rec or {}).get("actor", {}).get("mode") if rec else None,
                 "started_at": (rec or {}).get("session", {}).get("started_at") if rec else None,
                 "ended_at": (rec or {}).get("session", {}).get("ended_at") if rec else None, "runs": []}
            sessions.append(s)
            by_key[key] = s
        if rec:
            if rec["session"].get("started_at") and (not s["started_at"] or rec["session"]["started_at"] < s["started_at"]):
                s["started_at"] = rec["session"]["started_at"]
            if rec["session"].get("ended_at") and (not s["ended_at"] or rec["session"]["ended_at"] > s["ended_at"]):
                s["ended_at"] = rec["session"]["ended_at"]
        s["runs"].append({
            "run": (rec or {}).get("session", {}).get("run") if rec else None,
            "sha": sha, "subject": subject,
            "n_read": len(rec["read"]) if rec else 0, "n_wrote": len(rec["wrote"]) if rec else 0,
            "n_deps": len(rec["added_deps"]) if rec else 0,
            "tests": rec["tests"] if rec else None, "approver": rec.get("approver") if rec else None, "record": rec,
        })
    return sessions
