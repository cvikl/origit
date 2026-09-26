"""Taint query engine — the hero command.

``origit taint <needle>`` answers: which commits did an agent write after reading NEEDLE?

    query(commits, needle) -> dict

``commits`` is a list newest-first (git log order) of ``(sha, subject, record_or_None)``.
``needle`` is one of:
  * a package name ``fast-pay-utils`` (any version) or spec ``fast-pay-utils@2.1.0`` (exact version)
  * a file path (exact match on ``read[].ref`` or ``wrote[]``)
  * a 64-hex sha256 (exact match on ``read[].sha256``)

Direct match: ``added_deps[]`` by name (+version), ``read[]`` of kind pkg by name (+version), any other
``read[].ref`` equal to the needle, or — for a bare package name — a read whose path has a directory
segment equal to the name (``node_modules/<name>/README.md``); ``wrote[]`` equal to the needle.
Propagation (oldest → newest): a commit that read or wrote a file which an already-tainted commit wrote
is tainted too. Commits without a record stay clean.

Returns:
  affected        newest-first [{sha, subject, session, actor, approver, approved_at, wrote, matched}]
                  ``matched`` sorted: "added_deps:<name>@<ver>" | "read:<kind>:<ref>" | "read:sha256:<hex>"
                  | "wrote:<path>" | "propagated:<path>"
  sessions        sorted unique session ids of affected commits
  files_written   sorted unique union of ``wrote`` over affected commits
  approvers       sorted unique non-null approvers
  first_read      {session, at, commit} of the oldest affected commit, or None
  rollback_commit sha of the nearest clean commit older than the oldest affected one, or None
  clean           newest-first [{sha, subject}] for every commit not affected

Pure function; O(commits). Answers in milliseconds on the demo repo.
"""

from __future__ import annotations

import re
from typing import Any

from .trace import split_spec

HEX_RE = re.compile(r"^[0-9a-f]{64}$")


def _parse_needle(needle: str) -> dict[str, Any]:
    n = needle.strip()
    if HEX_RE.match(n.lower()):
        return {"sha": n.lower(), "name": None, "version": None}
    if "/" in n and not n.startswith("@"):  # a path
        return {"sha": None, "name": n, "version": None}
    name, ver = split_spec(n)
    return {"sha": None, "name": name, "version": ver}


def _has_segment(path: str, name: str) -> bool:
    return name in path.replace("\\", "/").split("/")[:-1]


def _direct_matches(rec: dict[str, Any], nd: dict[str, Any]) -> list[str]:
    m: set[str] = set()
    name, ver, sha = nd["name"], nd["version"], nd["sha"]
    for d in rec.get("added_deps", []):
        if name and d.get("name") == name and (ver is None or d.get("version") == ver):
            m.add(f"added_deps:{d['name']}@{d.get('version')}")
    for r in rec.get("read", []):
        ref = r.get("ref", "")
        if sha:
            if r.get("sha256") == sha:
                m.add(f"read:sha256:{sha}")
            continue
        if r.get("kind") == "pkg":
            pn, pv = split_spec(ref)
            if pn == name and (ver is None or pv == ver):
                m.add(f"read:pkg:{ref}")
        elif ref == name or (ver is None and _has_segment(ref, name)):
            m.add(f"read:{r.get('kind')}:{ref}")
    if not sha:
        for w in rec.get("wrote", []):
            if w == name:
                m.add(f"wrote:{w}")
    return sorted(m)


def query(commits: list[tuple[str, str, dict[str, Any] | None]], needle: str) -> dict[str, Any]:
    nd = _parse_needle(needle)
    tainted_files: set[str] = set()
    affected: dict[str, list[str]] = {}
    for sha, _subject, rec in reversed(commits):  # oldest first
        if not rec:
            continue
        matched = _direct_matches(rec, nd)
        touched = [r["ref"] for r in rec.get("read", []) if r.get("kind") == "file"] + list(rec.get("wrote", []))
        matched += [f"propagated:{p}" for p in sorted({p for p in touched if p in tainted_files})]
        if matched:
            affected[sha] = matched
            tainted_files.update(rec.get("wrote", []))

    out_affected, clean = [], []
    for sha, subject, rec in commits:
        if sha in affected:
            out_affected.append({
                "sha": sha,
                "subject": subject,
                "session": rec["session"].get("id"),
                "actor": rec["actor"].get("kind"),
                "approver": rec.get("approver"),
                "approved_at": rec.get("approved_at"),
                "wrote": sorted(rec.get("wrote", [])),
                "matched": affected[sha],
            })
        else:
            clean.append({"sha": sha, "subject": subject})

    first_read = None
    rollback = None
    if out_affected:
        oldest = out_affected[-1]
        first_read = {"session": oldest["session"], "at": None, "commit": oldest["sha"]}
        for sha, _s, rec in commits:
            if sha == oldest["sha"]:
                first_read["at"] = rec["session"].get("started_at")
        idx = [sha for sha, _, _ in commits].index(oldest["sha"])
        for sha, _s, _r in commits[idx + 1:]:
            if sha not in affected:
                rollback = sha
                break

    return {
        "needle": needle,
        "affected": out_affected,
        "sessions": sorted({c["session"] for c in out_affected if c["session"]}),
        "files_written": sorted({w for c in out_affected for w in c["wrote"]}),
        "approvers": sorted({c["approver"] for c in out_affected if c["approver"]}),
        "first_read": first_read,
        "rollback_commit": rollback,
        "clean": clean,
    }
