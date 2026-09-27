"""Session manager state: one Bob session = many runs; one run = one commit = one record.

State lives in ``.origit/session.json`` (never committed):
  {"id": "<session_id>", "number": 42, "started_at": ts, "run": 2, "cwd": "...",
   "head": "<sha at session start>", "dirty": {"path": "sha256", ...},
   "runs": [{"run": 1, "prompt": "...", "started_at": ts, "ended_at": ts, "sha": "<commit>"|null}]}

Lifecycle (driven by the Bob IDE / Bob Shell hooks installed by ``origit init``):
  SessionStart      -> ``origit session start``  : new state file, display number assigned
  UserPromptSubmit  -> ``origit run start``      : human edits since last commit committed as ``actor: human``,
                                                   run counter += 1, prompt kept for the commit subject
  PostToolUse       -> ``origit trace``          : every tool call appended to ``.origit/trace.jsonl``
  Stop              -> ``origit run end``        : trace folded, tests, auto-commit, record attached as a note;
                                                   with nothing to commit the record is stored under
                                                   ``.origit/runs/<session>-<run>.json``

Pure helpers here; git calls only through ``notes``/``cli``.
"""

from __future__ import annotations

import json
import os
from typing import Any

from . import STATE_DIR
from . import record as R

SESSION_FILE = "session.json"
RUNS_DIR = "runs"


def path(root: str = ".") -> str:
    return os.path.join(root, STATE_DIR, SESSION_FILE)


def load(root: str = ".") -> dict[str, Any] | None:
    try:
        with open(path(root), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None


def save(root: str, state: dict[str, Any]) -> None:
    os.makedirs(os.path.join(root, STATE_DIR), exist_ok=True)
    with open(path(root), "w", encoding="utf-8") as f:
        json.dump(state, f, indent=1, ensure_ascii=False)


def new(session_id: str, number: int, started_at: str, head: str | None, dirty: dict[str, str | None], cwd: str = "") -> dict[str, Any]:
    return {"id": session_id, "number": number, "started_at": started_at, "run": 0, "cwd": cwd, "head": head, "dirty": dirty, "runs": []}


def begin_run(state: dict[str, Any], prompt: str, started_at: str) -> dict[str, Any]:
    state["run"] = int(state.get("run", 0)) + 1
    state.setdefault("runs", []).append({"run": state["run"], "prompt": prompt, "started_at": started_at, "ended_at": None, "sha": None})
    return state


def end_run(state: dict[str, Any], ended_at: str, sha: str | None) -> dict[str, Any]:
    runs = state.get("runs") or []
    if runs:
        runs[-1]["ended_at"] = ended_at
        runs[-1]["sha"] = sha
    return state


def current_prompt(state: dict[str, Any] | None) -> str:
    runs = (state or {}).get("runs") or []
    return str(runs[-1].get("prompt") or "") if runs else ""


def subject(prompt: str, number: int | None, run: int | None, fallback: str = "agent session") -> str:
    """``bob: <first line of the prompt> [session #42 run 2]`` (subject kept under ~90 chars)."""
    first = next((l.strip(" #*->") for l in prompt.splitlines() if l.strip()), "") or fallback
    first = " ".join(first.split())
    if len(first) > 64:
        first = first[:63].rstrip() + "…"
    tag = f"[session #{number} run {run}]" if number is not None and run is not None else ""
    return f"bob: {first} {tag}".rstrip()


def status(state: dict[str, Any] | None) -> dict[str, Any]:
    if not state:
        return {"recording": False}
    return {"id": state.get("id"), "number": state.get("number"), "label": f"#{state.get('number')}", "run": state.get("run", 0), "started_at": state.get("started_at"), "recording": True}


def run_record_path(root: str, session_id: str, run: int) -> str:
    return os.path.join(root, STATE_DIR, RUNS_DIR, f"{session_id}-{run}.json")


def store_run_record(root: str, session_id: str, run: int, rec: dict[str, Any]) -> str:
    p = run_record_path(root, session_id, run)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(R.dumps(rec))
    return p
