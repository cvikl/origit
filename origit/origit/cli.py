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
from . import session as SS
from . import sessions as S
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


def _root(start: str = ".") -> str:
    try:
        return N.toplevel(start)
    except N.NotesError:
        click.echo("origit: not inside a git repository", err=True)
        sys.exit(1)


def _cfg(root: str, key: str, default: str | None = None) -> str | None:
    v = _git(root, "config", "--get", key)
    return v if v else default


def _autocommit(root: str) -> bool:
    return (_cfg(root, "origit.autocommit", "") or "").lower() in ("true", "1", "yes")


def _dirty_files(root: str) -> list[str]:
    """Tracked modifications + untracked files, excluding Origit state."""
    out = _git(root, "status", "--porcelain", "--untracked-files=all", "--", ".", f":(exclude){STATE_DIR}") or ""
    return [l[3:] for l in out.splitlines() if l.strip()]


def _commit_all(root: str, message: str, env: dict[str, str]) -> tuple[bool, str]:
    """Stage everything except Origit state and commit; the git hooks fold/attach the record."""
    subprocess.run(["git", "-C", root, "add", "-A", "--", ".", f":(exclude){STATE_DIR}"], check=False, capture_output=True)
    if subprocess.run(["git", "-C", root, "diff", "--cached", "--quiet"]).returncode == 0:
        return False, ""
    p = subprocess.run(["git", "-C", root, "commit", "-q", "-F", "-"], input=message, text=True, env={**os.environ, **env}, capture_output=True)
    if p.returncode != 0:
        return False, p.stderr[-400:]
    return True, N.head(root)


@click.group()
@click.version_option(__version__)
def main() -> None:
    """Origit — agent provenance layer for git."""


# ----------------------------------------------------------------------------- init
@main.command()
@click.option("--force", is_flag=True, help="Overwrite existing .bob/ and hook files (upgrade).")
@click.option("--session-base", type=int, default=None, help="First session display number (e.g. 42). Written to .origit/config.json.")
def init(force: bool, session_base: int | None) -> None:
    """Install Bob IDE hooks, the origit-build / origit-review modes, the Origit MCP server, the /origit skill and git hooks."""
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
        mcp_p = os.path.join(bob_dst, "mcp.json")
        try:  # the MCP server must be startable by the IDE without PATH tricks: absolute binary
            mcp = json.load(open(mcp_p))
            mcp["mcpServers"]["origit"]["command"] = exe
            json.dump(mcp, open(mcp_p, "w"), indent=2)
        except (OSError, KeyError, json.JSONDecodeError):
            pass
    subprocess.run(["git", "-C", root, "config", "origit.autocommit", "true"], check=False)
    os.makedirs(os.path.join(root, STATE_DIR), exist_ok=True)
    if session_base is not None:
        json.dump({"session_base": session_base}, open(os.path.join(root, STATE_DIR, S.CONFIG_FILE), "w"))
    gi = os.path.join(root, ".gitignore")
    existing = open(gi).read() if os.path.exists(gi) else ""
    wanted = [f"{STATE_DIR}/trace.jsonl", f"{STATE_DIR}/{PENDING_RECORD}", f"{STATE_DIR}/{SS.SESSION_FILE}", f"{STATE_DIR}/{SS.RUNS_DIR}/", f"{STATE_DIR}/*.log"]
    missing = [w for w in wanted if w not in existing.splitlines()]
    if missing:
        with open(gi, "a") as f:
            f.write(("" if existing.endswith("\n") or not existing else "\n") + "# origit runtime state\n" + "\n".join(missing) + "\n")
    click.echo(f"origit: installed .bob/ (hooks, origit-build + origit-review modes, rules, mcp.json, skills/origit), .githooks/ (pre/post-commit), core.hooksPath in {root}")


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


def _test_command(root: str) -> list[str] | None:
    cmd = _cfg(root, "origit.testCommand")
    if cmd:
        return ["sh", "-c", cmd]
    pj = os.path.join(root, "package.json")
    try:
        if json.load(open(pj)).get("scripts", {}).get("test"):
            return ["npm", "test", "--silent"]
    except (OSError, json.JSONDecodeError):
        pass
    if os.path.exists(os.path.join(root, "pytest.ini")) or os.path.exists(os.path.join(root, "pyproject.toml")):
        return ["python3", "-m", "pytest", "-q"]
    return None


def _run_tests(root: str, timeout: int = 90) -> dict:
    """Run the project's own test suite (plain subprocess, no AI) and parse jest/pytest totals."""
    cmd = _test_command(root)
    if not cmd:
        return {"run": False, "passed": 0, "failed": 0}
    try:
        p = subprocess.run(cmd, cwd=root, capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired):
        return {"run": False, "passed": 0, "failed": 0}
    out = (p.stdout or "") + (p.stderr or "")
    fake = [{"hook_event_name": "PostToolUse", "tool_name": "execute_command", "tool_input": {"command": " ".join(cmd) + " # npm test"}, "tool_response": out[-4000:]}]
    res = T.tests_from_events(fake)
    if not res["run"]:
        res = {"run": True, "passed": 0 if p.returncode else 1, "failed": 1 if p.returncode else 0}
    return res


@main.command()
@click.argument("stage", type=click.Choice(["fold", "attach"]))
def record(stage: str) -> None:
    """pre-commit: fold trace -> .origit/pending-record.json. post-commit: attach it to HEAD as a git note."""
    root = _root()
    pending = os.path.join(root, STATE_DIR, PENDING_RECORD)
    if stage == "fold":
        events = [] if os.environ.get("ORIGIT_ACTOR") == "human" else T.iter_events(root)
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
        staged = [f for f in _staged_files(root) if not f.startswith(STATE_DIR + "/")]
        parts["wrote"] = sorted({_relativize(root, w) for w in parts["wrote"]} | (set(staged) if parts["actor"]["kind"] != "human" else set()))
        for d in _deps_from_package_json(root):
            if not any(x["name"] == d["name"] for x in parts["added_deps"]):
                parts["added_deps"].append(d)
                parts["read"].append({"kind": "pkg", "ref": f"{d['name']}@{d['version']}", "sha256": None})
        if parts["actor"]["kind"] == "human":
            parts["session"] = {"id": f"human:{author}:{now}", "started_at": now, "ended_at": now}
        parts["actor"]["mode"] = os.environ.get("ORIGIT_MODE") or _cfg(root, "origit.mode") or None
        parts["actor"]["config_sha256"] = _config_sha256(root)
        st = SS.load(root)
        if st and parts["actor"]["kind"] != "human" and (not parts["session"]["id"] or parts["session"]["id"] == st.get("id")):
            parts["session"]["id"] = st.get("id") or parts["session"]["id"]
            parts["session"]["number"] = st.get("number")
            parts["session"]["run"] = st.get("run") or None
            prompt = SS.current_prompt(st)
            if prompt:
                parts["session"]["prompt"] = " ".join(prompt.split())[:200]
            parts["session"]["started_at"] = parts["session"]["started_at"] or st.get("started_at")
        tests = T.tests_from_events(events)
        if not tests["run"] and os.environ.get("ORIGIT_RUN_TESTS") == "1" and parts["actor"]["kind"] != "human":
            tests = _run_tests(root)
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


# ----------------------------------------------------------------------------- session / run (hook consumers)
def _hook_payload() -> dict:
    try:
        return T.read_stdin_payload() or {}
    except Exception:  # noqa: BLE001
        return {}


def _trace_event(root: str, payload: dict, event: str) -> None:
    if payload:
        payload = {**payload}
        payload.setdefault("hook_event_name", event)
        T.append_event(payload, root)


@main.group()
def session() -> None:
    """Session manager: one Bob session = many runs; one run = one commit = one record."""


@session.command("start")
@click.option("--root", default=".")
def session_start(root: str) -> None:
    """SessionStart hook: open a session, assign its display number (#42), snapshot the working tree."""
    try:
        payload = _hook_payload()
        top = N.toplevel(root)
        _trace_event(top, payload, "SessionStart")
        sid = str(payload.get("session_id") or f"local:{T.utcnow()}")
        cur = SS.load(top)
        if cur and cur.get("id") == sid:
            click.echo(f"origit: session #{cur.get('number')} resumed", err=True)
            return
        base = S.base(top)
        number = S.next_number(N.commits(top), base)
        dirty = {f: R.file_sha256(os.path.join(top, f)) for f in _dirty_files(top)[:200]}
        head = _git(top, "rev-parse", "HEAD")
        SS.save(top, SS.new(sid, number, T.utcnow(), head, dirty, str(payload.get("cwd") or "")))
        click.echo(f"origit: session #{number} opened ({sid[:8]}), head {head[:7] if head else '-'}, {len(dirty)} dirty file(s)", err=True)
    except Exception as exc:  # noqa: BLE001 — never block Bob
        click.echo(f"origit session start: {exc}", err=True)
    sys.exit(0)


@session.command("status")
@click.option("--root", default=".")
@click.option("--json", "as_json", is_flag=True)
def session_status(root: str, as_json: bool) -> None:
    """Current session (for the IDE status bar)."""
    top = _root(root)
    st = SS.status(SS.load(top))
    if as_json:
        click.echo(json.dumps(st))
    elif st["recording"]:
        click.echo(f"session {st['label']} run {st['run']} · recording ({st['id']})")
    else:
        click.echo("no session")


@main.group()
def run() -> None:
    """Run lifecycle hooks: UserPromptSubmit -> `run start`, Stop -> `run end`."""


@run.command("start")
@click.option("--root", default=".")
def run_start(root: str) -> None:
    """UserPromptSubmit hook: commit human edits made since the last commit (actor: human), then open run n+1."""
    try:
        payload = _hook_payload()
        top = N.toplevel(root)
        sid = str(payload.get("session_id") or "")
        st = SS.load(top)
        if not st or (sid and st.get("id") != sid):
            base = S.base(top)
            st = SS.new(sid or f"local:{T.utcnow()}", S.next_number(N.commits(top), base), T.utcnow(), _git(top, "rev-parse", "HEAD"), {}, str(payload.get("cwd") or ""))
        if _autocommit(top) and _dirty_files(top):
            ok, res = _commit_all(top, f"human: edits before session #{st['number']} run {st.get('run', 0) + 1}\n\nCommitted by Origit when the next agent run started, so human and agent work never share a record.\n",
                                  {"ORIGIT_ACTOR": "human"})
            click.echo(f"origit: human edits committed as {res[:7]}" if ok else f"origit: human commit skipped {res}", err=True)
        SS.begin_run(st, str(payload.get("prompt") or ""), T.utcnow())
        SS.save(top, st)
        _trace_event(top, payload, "UserPromptSubmit")
        click.echo(f"origit: session #{st['number']} run {st['run']} started", err=True)
    except Exception as exc:  # noqa: BLE001
        click.echo(f"origit run start: {exc}", err=True)
    sys.exit(0)


@run.command("end")
@click.option("--root", default=".")
def run_end(root: str) -> None:
    """Stop hook: fold the trace, run the tests, auto-commit the run, attach the record (via the git hooks).

    With nothing to commit the folded record is stored under .origit/runs/<session>-<run>.json and the trace is cleared.
    Enabled per repo with `git config origit.autocommit true` (set by `origit init`). Always exits 0.
    """
    try:
        payload = _hook_payload()
        top = N.toplevel(root)
        _trace_event(top, payload, "Stop")
        st = SS.load(top) or {}
        sid = str(payload.get("session_id") or st.get("id") or "unknown")
        if not _autocommit(top):
            click.echo("origit: autocommit off; the next manual commit seals this run", err=True)
            return
        summary = (payload.get("last_assistant_message") or "").strip()
        prompt = SS.current_prompt(st) or next((T.unwrap(e).get("prompt") for e in T.iter_events(top) if T.unwrap(e).get("event") == "UserPromptSubmit" and T.unwrap(e).get("prompt")), "") or ""
        number, runno = st.get("number"), st.get("run") or None
        subj = SS.subject(prompt, number, runno, fallback=next((l.strip(" #*-") for l in summary.splitlines() if l.strip()), "agent session"))
        msg = f"{subj}\n\nSession {sid}{f' run {runno}' if runno else ''}. Auto-committed by Origit when the agent stopped.\n\n{summary[:1500]}\n"
        env = {"ORIGIT_RUN_TESTS": "1"}
        mode = _cfg(top, "origit.mode") or os.environ.get("ORIGIT_MODE") or ""
        if mode:
            env["ORIGIT_MODE"] = mode
        ok, res = _commit_all(top, msg, env)
        if ok:
            SS.end_run(st, T.utcnow(), res)
            SS.save(top, st)
            click.echo(f"origit: session #{number} run {runno} committed as {res[:7]}", err=True)
        elif res:
            click.echo(f"origit: run commit failed: {res}", err=True)
        else:
            events = T.iter_events(top)
            parts = T.fold(events)
            if parts["actor"]["kind"] != "human":
                parts["session"].update({"id": sid, "number": number, "run": runno})
                rec = R.finalize({**parts, "schema": R.SCHEMA, "author": _cfg(top, "user.name") or "", "approver": None, "approved_at": None,
                                  "tests": T.tests_from_events(events)})
                p = SS.store_run_record(top, sid, runno or 0, rec)
                click.echo(f"origit: run {runno} changed nothing; record kept at {os.path.relpath(p, top)}", err=True)
            else:
                click.echo("origit: run ended, nothing to commit", err=True)
            T.clear(top)
            SS.end_run(st, T.utcnow(), None)
            SS.save(top, st)
    except Exception as exc:  # noqa: BLE001
        click.echo(f"origit run end: {exc}", err=True)
    sys.exit(0)


@main.command("session-commit", hidden=True)
@click.option("--root", default=".")
@click.pass_context
def session_commit(ctx: click.Context, root: str) -> None:
    """Deprecated alias of `origit run end` (kept for hooks installed on Saturday)."""
    ctx.invoke(run_end, root=root)


# ----------------------------------------------------------------------------- log / show
def _prefilter_lite(root: str, sha: str, rec: dict) -> dict:
    """Cheap pre-filter for list views: record-only rules plus hidden text in files still present in the working tree."""
    changed = (_git(root, "diff-tree", "--no-commit-id", "--name-only", "-r", "--root", sha) or "").splitlines()
    texts = {}
    for r in rec.get("read", []):
        if r.get("kind") == "file":
            p = os.path.join(root, r["ref"])
            if os.path.isfile(p) and os.path.getsize(p) < 2_000_000:
                try:
                    texts[r["ref"]] = open(p, encoding="utf-8", errors="replace").read()
                except OSError:
                    pass
    findings = PF.run(rec, changed, texts)
    sev = max((f["severity"] for f in findings), key=PF.SEVERITIES.index) if findings else None
    return {"needs_review": PF.needs_review(findings), "max_severity": sev, "reasons": sorted({f["asi"] for f in findings})}


@main.command()
@click.option("--range", "rev_range", default="HEAD")
@click.option("--json", "as_json", is_flag=True, help="Sessions with their runs, newest first.")
@click.option("--flat", is_flag=True, help="One line per commit (Saturday format).")
def log(rev_range: str, as_json: bool, flat: bool) -> None:
    """Commits grouped by agent session and run, newest first."""
    root = _root()
    cs = N.commits(root, rev_range)
    base = S.base(root)
    if flat:
        labels = S.number_sessions(cs, base)
        for sha, subject, rec in cs:
            if rec:
                a = rec["actor"]["kind"]
                sid = rec["session"].get("id") or "-"
                s_lbl = S.label(labels.get(sid)) if a != "human" else "human"
                click.echo(f"{sha[:7]}  {a:8} {s_lbl:6} {(rec.get('approver') or '-'):10} {subject}")
            else:
                click.echo(f"{sha[:7]}  {'(none)':8} {'-':6} {'-':10} {subject}")
        return
    groups = S.group(cs, base)
    for g in groups:
        for r in g["runs"]:
            r["prefilter"] = _prefilter_lite(root, r["sha"], r["record"]) if r["record"] else {"needs_review": False, "max_severity": None, "reasons": []}
    if as_json:
        click.echo(json.dumps({"repo": os.path.basename(root), "head": N.head(root), "base": base, "sessions": groups}, indent=2, ensure_ascii=False))
        return
    for g in groups:
        if g["actor"] == "none":
            head = "no record"
        elif g["actor"] == "human":
            head = "human"
        else:
            head = f"session {g['label']} · Bob IDE{(' · ' + g['mode']) if g.get('mode') else ''} · {_fmt_ts(g['started_at'])} → {_fmt_ts(g['ended_at'])}"
        click.echo(head)
        for r in g["runs"]:
            run_lbl = f"run {r['run']}" if r.get("run") else ""
            stats = f"{r['n_read']} read · {r['n_wrote']} wrote" + (f" · {r['n_deps']} deps" if r["n_deps"] else "") if r["record"] else ""
            t = r.get("tests") or {}
            tests = f" · tests {t.get('passed', 0)}/{t.get('passed', 0) + t.get('failed', 0)}" if t.get("run") else ""
            sev = f" · {r['prefilter']['max_severity']}" if r["prefilter"]["max_severity"] else ""
            click.echo(f"  {r['sha'][:7]}  {run_lbl:6} {r['subject'][:70]}")
            if stats:
                click.echo(f"           {stats}{tests}{sev}")
        click.echo("")


@main.command()
@click.argument("commit")
@click.option("--json", "as_json", is_flag=True)
def show(commit: str, as_json: bool) -> None:
    """Pretty-print the full record for a commit."""
    root = _root()
    sha = _git(root, "rev-parse", commit)
    rec = N.read(root, sha) if sha else None
    if not rec:
        if as_json:
            click.echo(json.dumps({"sha": sha, "record": None, "verified": False}))
        else:
            click.echo(f"origit: no record for {commit}", err=True)
        sys.exit(0 if as_json else 1)
    subject = _git(root, "log", "-1", "--format=%s", sha) or ""
    if as_json:
        click.echo(json.dumps({"sha": sha, "subject": subject, "verified": R.verify(rec), "record": rec}, indent=2, ensure_ascii=False))
        return
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
    cs = N.commits(root, rev_range)
    out = X.query(cs, needle)
    labels = S.number_sessions(cs, S.base(root))
    out["session_labels"] = {sid: S.label(labels[sid]) for sid in out["sessions"] if sid in labels}
    for c in out["affected"]:
        c["session_label"] = out["session_labels"].get(c["session"], c["session"])
    if out["first_read"]:
        out["first_read"]["label"] = out["session_labels"].get(out["first_read"]["session"], out["first_read"]["session"])
    if as_json:
        click.echo(json.dumps(out, indent=2, ensure_ascii=False))
        return
    n = len(out["affected"])
    if not n:
        click.echo(f"0 commits affected by {needle} ({len(out['clean'])} commits checked)")
        return
    latest_approval = max((c["approved_at"] or "" for c in out["affected"]), default="")
    click.echo(f"{n} commit{'s' if n != 1 else ''} affected")
    click.echo(f"Sessions: {', '.join(out['session_labels'].get(x, x) for x in out['sessions']) or '-'}")
    click.echo(f"Files: {', '.join(out['files_written']) or '-'}")
    click.echo(f"Approver: {', '.join(out['approvers']) or '-'} ({_fmt_ts(latest_approval or None)})")
    fr = out["first_read"]
    click.echo(f"First read: session {fr.get('label') or fr['session']}, {_fmt_ts(fr['at'])}")
    click.echo(f"Roll back to: commit {out['rollback_commit'][:7] if out['rollback_commit'] else '-'}")
    click.echo("")
    for c in out["affected"]:
        click.echo(f"  {c['sha'][:7]}  {(c.get('session_label') or c['session'] or '-'):6} {c['subject']}")
        for m in c["matched"]:
            click.echo(f"           ↳ {m}")


# ----------------------------------------------------------------------------- mcp
@main.command()
def mcp() -> None:
    """Run the Origit MCP server on stdio (tools: origit_taint, origit_show, origit_log). Started by Bob IDE via .bob/mcp.json."""
    from . import mcp as M
    M.serve(_root())


# ----------------------------------------------------------------------------- export / prefilter
@main.command()
@click.option("--range", "rev_range", default="HEAD", help="git rev range, e.g. main~10..main")
def export(rev_range: str) -> None:
    """JSON evidence pack: list of {sha, subject, record} for the range, newest first."""
    root = _root()
    meta = N.log_meta(root, rev_range)
    pack = [{"sha": s, "subject": sub, **{k: meta.get(s, {}).get(k) for k in ("author", "date", "parents", "files")}, "record": rec}
            for s, sub, rec in N.commits(root, rev_range)]
    click.echo(json.dumps({"repo": os.path.basename(root), "range": rev_range, "exported_at": T.utcnow(), "head": N.head(root), "commits": pack}, indent=2, ensure_ascii=False))


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
