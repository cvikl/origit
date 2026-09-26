"""``origit`` command-line interface. Deterministic; no model is ever called from the CLI."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
from importlib import resources

import click

from . import __version__, STATE_DIR, PENDING_RECORD
from . import notes as N
from . import prefilter as PF
from . import record as R
from . import taint as X
from . import trace as T


def _fmt_ts(iso: str | None) -> str:
    if not iso:
        return "-"
    try:
        return _dt.datetime.strptime(iso, "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%d %H:%M UTC")
    except ValueError:
        return iso


def _git(root: str, *args: str) -> str | None:
    p = subprocess.run(["git", "-C", root, *args], capture_output=True, text=True)
    return p.stdout.strip() if p.returncode == 0 else None


def _root() -> str:
    try:
        return N.toplevel(".")
    except N.NotesError:
        click.echo("origit: not inside a git repository", err=True)
        sys.exit(1)


@click.group()
@click.version_option(__version__)
def main() -> None:
    """Origit — agent provenance layer for git."""


# ----------------------------------------------------------------------------- init
@main.command()
@click.option("--force", is_flag=True, help="Overwrite existing .bob/ and hook files.")
def init(force: bool) -> None:
    """Install Bob IDE hooks, the origit-build mode and git hooks into this repo."""
    root = _root()
    tpl = resources.files("origit") / "templates"
    bob_dst = os.path.join(root, ".bob")
    hooks_dst = os.path.join(root, ".githooks")
    if (os.path.exists(bob_dst) or os.path.exists(hooks_dst)) and not force:
        click.echo("origit: .bob/ or .githooks/ already exists (use --force to overwrite)", err=True)
        sys.exit(1)
    shutil.copytree(str(tpl / "bob"), bob_dst, dirs_exist_ok=True)
    shutil.copytree(str(tpl / "git-hooks"), hooks_dst, dirs_exist_ok=True)
    for d in (os.path.join(bob_dst, "hooks"), hooks_dst):
        for f in os.listdir(d):
            p = os.path.join(d, f)
            os.chmod(p, os.stat(p).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    subprocess.run(["git", "-C", root, "config", "core.hooksPath", ".githooks"], check=True)
    exe = shutil.which("origit") or sys.argv[0]
    if exe and os.path.isabs(exe):
        subprocess.run(["git", "-C", root, "config", "origit.bin", exe], check=False)
    os.makedirs(os.path.join(root, STATE_DIR), exist_ok=True)
    gi = os.path.join(root, ".gitignore")
    line = f"{STATE_DIR}/trace.jsonl"
    existing = open(gi).read() if os.path.exists(gi) else ""
    if line not in existing:
        with open(gi, "a") as f:
            f.write(("" if existing.endswith("\n") or not existing else "\n") + f"# origit runtime state\n{line}\n{STATE_DIR}/{PENDING_RECORD}\n")
    click.echo(f"origit: installed .bob/ (hooks, origit-build mode, rules), .githooks/ (pre/post-commit), core.hooksPath in {root}")


# ----------------------------------------------------------------------------- trace
@main.command()
@click.option("--root", default=".", help="Repo root (hook cwd is the task working directory).")
def trace(root: str) -> None:
    """Hook consumer: read a Bob hook JSON payload on stdin, append it to .origit/trace.jsonl. Always exits 0."""
    try:
        payload = T.read_stdin_payload()
        if payload is not None:
            T.append_event(payload, root)
    except Exception as exc:  # noqa: BLE001 — never break Bob
        click.echo(f"origit trace: {exc}", err=True)
    sys.exit(0)


# ----------------------------------------------------------------------------- record
def _relativize(root: str, path: str) -> str:
    if os.path.isabs(path):
        try:
            rel = os.path.relpath(path, root)
            if not rel.startswith(".."):
                return rel
        except ValueError:
            pass
    return path


def _config_sha256(root: str) -> str | None:
    bob = os.path.join(root, ".bob")
    if not os.path.isdir(bob):
        return None
    h = hashlib.sha256()
    for dp, _, fs in sorted(os.walk(bob)):
        for f in sorted(fs):
            p = os.path.join(dp, f)
            h.update(os.path.relpath(p, root).encode())
            try:
                h.update(open(p, "rb").read())
            except OSError:
                pass
    return h.hexdigest()


def _staged_files(root: str) -> list[str]:
    out = _git(root, "diff", "--cached", "--name-only") or ""
    return [l for l in out.splitlines() if l]


def _deps_from_package_json(root: str) -> list[dict]:
    """Dependencies added in staged package.json files vs HEAD."""
    found = []
    for path in _staged_files(root):
        if os.path.basename(path) != "package.json":
            continue
        try:
            new = json.load(open(os.path.join(root, path)))
        except (OSError, json.JSONDecodeError):
            continue
        old_txt = _git(root, "show", f"HEAD:{path}")
        try:
            old = json.loads(old_txt) if old_txt else {}
        except json.JSONDecodeError:
            old = {}
        for key in ("dependencies", "devDependencies"):
            for name, spec in (new.get(key) or {}).items():
                if name in (old.get(key) or {}):
                    continue
                version = str(spec)
                if version.startswith(("file:", "link:", ".", "/")):
                    pj = os.path.join(root, os.path.dirname(path), "node_modules", name, "package.json")
                    try:
                        version = json.load(open(pj)).get("version", version)
                    except (OSError, json.JSONDecodeError):
                        pass
                lock = os.path.join(root, os.path.dirname(path), "package-lock.json")
                found.append({"name": name, "version": version.lstrip("^~="), "registry": "npm", "lockfile_sha256": R.file_sha256(lock)})
    return found


@main.command()
@click.argument("stage", type=click.Choice(["fold", "attach"]))
def record(stage: str) -> None:
    """pre-commit: fold trace -> .origit/pending-record.json. post-commit: attach it to HEAD as a git note."""
    root = _root()
    pending = os.path.join(root, STATE_DIR, PENDING_RECORD)
    if stage == "fold":
        events = T.iter_events(root)
        parts = T.fold(events)
        if not events and os.environ.get("ORIGIT_REQUIRE_TRACE") == "1":
            click.echo("origit: agent commit without trace refused", err=True)
            sys.exit(1)
        now = T.utcnow()
        author = _git(root, "config", "user.name") or os.environ.get("USER", "unknown")
        approver = os.environ.get("ORIGIT_APPROVER") or _git(root, "config", "origit.approver") or None
        for r in parts["read"]:
            r["ref"] = _relativize(root, r["ref"])
            if r["kind"] == "file":
                r["sha256"] = R.file_sha256(os.path.join(root, r["ref"]))
        parts["wrote"] = sorted({_relativize(root, w) for w in parts["wrote"]})
        for d in _deps_from_package_json(root):
            if not any(x["name"] == d["name"] for x in parts["added_deps"]):
                parts["added_deps"].append(d)
                parts["read"].append({"kind": "pkg", "ref": f"{d['name']}@{d['version']}", "sha256": None})
        if parts["actor"]["kind"] == "human":
            parts["session"] = {"id": f"human:{author}:{now}", "started_at": now, "ended_at": now}
        parts["actor"]["mode"] = os.environ.get("ORIGIT_MODE") or None
        parts["actor"]["config_sha256"] = _config_sha256(root)
        tests = {"run": False, "passed": 0, "failed": 0}
        if os.environ.get("ORIGIT_TESTS"):
            try:
                tests.update(json.loads(os.environ["ORIGIT_TESTS"]))
            except json.JSONDecodeError:
                pass
        rec = R.finalize({
            **parts, "schema": R.SCHEMA, "author": author, "approver": approver,
            "approved_at": now if approver else None, "tests": tests,
        })
        os.makedirs(os.path.dirname(pending), exist_ok=True)
        with open(pending, "w", encoding="utf-8") as f:
            f.write(R.dumps(rec))
        click.echo(f"origit: record folded ({rec['actor']['kind']}, {len(rec['read'])} reads, {len(rec['wrote'])} writes, {len(rec['added_deps'])} deps) {rec['record_sha256'][:12]}")
    else:
        if not os.path.exists(pending):
            click.echo("origit: no pending record to attach", err=True)
            sys.exit(0)
        rec = R.loads(open(pending, encoding="utf-8").read())
        sha = N.head(root)
        N.write(root, sha, rec)
        os.remove(pending)
        T.clear(root)
        click.echo(f"origit: record {rec['record_sha256'][:12]} attached to {sha[:7]} (refs/notes/origit)")


# ----------------------------------------------------------------------------- log / show
@main.command()
@click.option("--range", "rev_range", default="HEAD")
def log(rev_range: str) -> None:
    """One line per commit, newest first: sha, actor, session, approver, subject."""
    root = _root()
    for sha, subject, rec in N.commits(root, rev_range):
        if rec:
            a = rec["actor"]["kind"]
            s = (rec["session"].get("id") or "-")[:22]
            ap = rec.get("approver") or "-"
            click.echo(f"{sha[:7]}  {a:8} {s:22} {ap:10} {subject}")
        else:
            click.echo(f"{sha[:7]}  {'(none)':8} {'-':22} {'-':10} {subject}")


@main.command()
@click.argument("commit")
def show(commit: str) -> None:
    """Pretty-print the full record for a commit."""
    root = _root()
    sha = _git(root, "rev-parse", commit)
    rec = N.read(root, sha) if sha else None
    if not rec:
        click.echo(f"origit: no record for {commit}", err=True)
        sys.exit(1)
    click.echo(json.dumps(rec, indent=2, ensure_ascii=False))
    click.echo(f"# verified: {R.verify(rec)}", err=True)


# ----------------------------------------------------------------------------- taint
@main.command()
@click.argument("needle")
@click.option("--json", "as_json", is_flag=True)
@click.option("--range", "rev_range", default="HEAD")
def taint(needle: str, as_json: bool, rev_range: str) -> None:
    """Which commits did an agent write after reading NEEDLE (package, file or sha256)?"""
    root = _root()
    out = X.query(N.commits(root, rev_range), needle)
    if as_json:
        click.echo(json.dumps(out, indent=2, ensure_ascii=False))
        return
    n = len(out["affected"])
    if not n:
        click.echo(f"0 commits affected by {needle} ({len(out['clean'])} commits checked)")
        return
    latest_approval = max((c["approved_at"] or "" for c in out["affected"]), default="")
    click.echo(f"{n} commit{'s' if n != 1 else ''} affected")
    click.echo(f"Sessions: {', '.join(out['sessions']) or '-'}")
    click.echo(f"Files: {', '.join(out['files_written']) or '-'}")
    click.echo(f"Approver: {', '.join(out['approvers']) or '-'} ({_fmt_ts(latest_approval or None)})")
    fr = out["first_read"]
    click.echo(f"First read: {fr['session']}, {_fmt_ts(fr['at'])}")
    click.echo(f"Roll back to: commit {out['rollback_commit'][:7] if out['rollback_commit'] else '-'}")
    click.echo("")
    for c in out["affected"]:
        click.echo(f"  {c['sha'][:7]}  {c['session'] or '-':22} {c['subject']}")
        for m in c["matched"]:
            click.echo(f"           ↳ {m}")


# ----------------------------------------------------------------------------- export / prefilter
@main.command()
@click.option("--range", "rev_range", default="HEAD", help="git rev range, e.g. main~10..main")
def export(rev_range: str) -> None:
    """JSON evidence pack: list of {sha, subject, record} for the range, newest first."""
    root = _root()
    pack = [{"sha": s, "subject": sub, "record": rec} for s, sub, rec in N.commits(root, rev_range)]
    click.echo(json.dumps({"repo": root, "range": rev_range, "exported_at": T.utcnow(), "commits": pack}, indent=2, ensure_ascii=False))


@main.command()
@click.argument("commit", default="HEAD")
def prefilter(commit: str) -> None:
    """Run the deterministic ASI pre-filter on a commit's record (zero coins)."""
    root = _root()
    sha = _git(root, "rev-parse", commit)
    rec = N.read(root, sha) if sha else None
    if not rec:
        click.echo(f"origit: no record for {commit}", err=True)
        sys.exit(1)
    changed = (_git(root, "diff-tree", "--no-commit-id", "--name-only", "-r", sha) or "").splitlines()
    texts = {}
    for r in rec["read"]:
        if r["kind"] == "file":
            p = os.path.join(root, r["ref"])
            if os.path.isfile(p):
                try:
                    texts[r["ref"]] = open(p, encoding="utf-8", errors="replace").read()
                except OSError:
                    pass
    findings = PF.run(rec, changed, texts)
    click.echo(json.dumps({"commit": sha, "needs_review": PF.needs_review(findings), "findings": findings}, indent=2, ensure_ascii=False))
