"""Git notes storage for Origit records (namespace ``refs/notes/origit``).

One note per commit containing the finalized canonical record JSON. Notes ride along
with the repo (``git push origin refs/notes/origit``) and never rewrite history.
Thin wrappers over the ``git`` CLI; the only module allowed to call git.
"""

from __future__ import annotations

import json
import subprocess
from typing import Any

from . import NOTES_REF
from . import record as R

NOTES_ARG = "--ref=" + NOTES_REF.rsplit("/", 1)[-1]  # "--ref=origit"


class NotesError(RuntimeError):
    pass


def _run(repo: str, *args: str, input: str | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", repo, *args], input=input, capture_output=True, text=True)


def _git(repo: str, *args: str, input: str | None = None) -> str:
    p = _run(repo, *args, input=input)
    if p.returncode != 0:
        raise NotesError(p.stderr.strip() or f"git {' '.join(args)} failed")
    return p.stdout


def head(repo: str) -> str:
    return _git(repo, "rev-parse", "HEAD").strip()


def toplevel(repo: str = ".") -> str:
    return _git(repo, "rev-parse", "--show-toplevel").strip()


def write(repo: str, commit: str, record: dict[str, Any]) -> None:
    _git(repo, "notes", NOTES_ARG, "add", "-f", "-F", "-", commit, input=R.dumps(record))


def read(repo: str, commit: str) -> dict[str, Any] | None:
    p = _run(repo, "notes", NOTES_ARG, "show", commit)
    if p.returncode != 0:
        if "no note found" in p.stderr.lower():
            return None
        raise NotesError(p.stderr.strip())
    return json.loads(p.stdout)


def noted_commits(repo: str) -> set[str]:
    p = _run(repo, "notes", NOTES_ARG, "list")
    if p.returncode != 0:
        return set()
    return {line.split()[1] for line in p.stdout.splitlines() if len(line.split()) == 2}


def commits(repo: str, rev_range: str = "HEAD") -> list[tuple[str, str, dict[str, Any] | None]]:
    """Newest-first ``(sha, subject, record|None)`` for the range."""
    out = _git(repo, "log", "--format=%H%x00%s", rev_range)
    noted = noted_commits(repo)
    result = []
    for line in out.splitlines():
        sha, _, subject = line.partition("\0")
        if not sha:
            continue
        result.append((sha, subject, read(repo, sha) if sha in noted else None))
    return result
