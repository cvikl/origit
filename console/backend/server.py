#!/usr/bin/env python3
"""Origit Console backend — one process, stdlib only, serves the API and the static frontend.

Data source: a git repo with Origit notes (ORIGIT_REPO_PATH) or, when absent, a committed evidence pack
(ORIGIT_EVIDENCE, default ../../demo/evidence/export.json). Deterministic pre-filter runs on every commit
at zero cost. Bob is only called (via Bob Shell `bob run`, BOB_API_KEY) for the ASI evidence review and the
Article 14 draft, and every Bob output is cached under console/data/ so the deployed demo never re-spends.

  GET  /api/repo                 commits newest-first with actor/session/approver/prefilter summary
  GET  /api/commit/<sha>         meta + record + prefilter findings + cached review (if any)
  GET  /api/taint?q=<needle>     taint.query output
  POST /api/review/<sha>         run (or return cached) Bob ASI review for a commit
  POST /api/art14?q=<needle>     run (or return cached) Bob Article 14 early-warning draft for a taint result
  GET  /api/asi                  the ten ASI categories
  GET  /                         frontend
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "origit"))

from origit import notes as N  # noqa: E402
from origit import prefilter as PF  # noqa: E402
from origit import record as R  # noqa: E402
from origit import taint as X  # noqa: E402

REPO = os.environ.get("ORIGIT_REPO_PATH") or ""
EVIDENCE = os.environ.get("ORIGIT_EVIDENCE") or os.path.join(ROOT, "demo", "evidence", "export.json")
FRONTEND = os.path.join(ROOT, "console", "frontend")
DATA = os.environ.get("ORIGIT_CONSOLE_DATA") or os.path.join(ROOT, "console", "data")
PORT = int(os.environ.get("PORT") or os.environ.get("ORIGIT_CONSOLE_PORT") or 8787)
BOB_MAX_COST = os.environ.get("BOB_MAX_COST", "0.6")
BOB_MAX_TURNS = os.environ.get("BOB_MAX_TURNS", "4")


# ----------------------------------------------------------------------------- data
def _is_repo(path: str) -> bool:
    return bool(path) and os.path.isdir(path) and subprocess.run(["git", "-C", path, "rev-parse"], capture_output=True).returncode == 0


def load() -> dict:
    """{name, head, commits:[{sha, subject, author, date, parents, files, record}]} newest-first."""
    if _is_repo(REPO):
        meta = N.log_meta(REPO)
        commits = [{"sha": s, "subject": sub, **meta.get(s, {}), "record": rec} for s, sub, rec in N.commits(REPO)]
        return {"name": os.path.basename(os.path.abspath(REPO)), "head": N.head(REPO), "commits": commits, "source": "git"}
    with open(EVIDENCE, encoding="utf-8") as f:
        d = json.load(f)
    return {"name": d.get("repo", "demo"), "head": d.get("head"), "commits": d["commits"], "source": "evidence"}


def read_texts_for(commit: dict) -> dict[str, str]:
    """Contents of files the agent read, for the hidden-text rule (only when the repo is available)."""
    out = {}
    rec = commit.get("record") or {}
    if not _is_repo(REPO):
        return out
    for r in rec.get("read", []):
        if r.get("kind") != "file":
            continue
        p = os.path.join(REPO, r["ref"])
        if os.path.isfile(p):
            try:
                out[r["ref"]] = open(p, encoding="utf-8", errors="replace").read()
            except OSError:
                pass
    return out


def prefilter_for(commit: dict) -> dict:
    rec = commit.get("record")
    if not rec:
        return {"needs_review": False, "findings": [], "reason": "no origit record (pre-Origit or unrecorded commit)"}
    findings = PF.run(rec, commit.get("files") or [], read_texts_for(commit))
    cached = _cached_prefilter(commit["sha"])
    if cached and not findings:  # evidence-pack mode: reuse findings computed with file access
        findings = cached
    return {"needs_review": PF.needs_review(findings), "findings": findings}


def _cached_prefilter(sha: str) -> list | None:
    p = os.path.join(ROOT, "demo", "evidence", f"prefilter-{sha[:7]}.json")
    if os.path.isfile(p):
        try:
            return json.load(open(p))["findings"]
        except (OSError, KeyError, json.JSONDecodeError):
            return None
    return None


def summary(commit: dict) -> dict:
    rec = commit.get("record") or {}
    pf = prefilter_for(commit)
    top = max((f["severity"] for f in pf["findings"]), key=lambda s: PF.SEVERITIES.index(s), default=None)
    return {
        "sha": commit["sha"], "short": commit["sha"][:7], "subject": commit["subject"],
        "author": commit.get("author"), "date": commit.get("date"), "files": commit.get("files") or [],
        "has_record": bool(rec), "actor": (rec.get("actor") or {}).get("kind"), "mode": (rec.get("actor") or {}).get("mode"),
        "session": (rec.get("session") or {}).get("id"), "approver": rec.get("approver"), "approved_at": rec.get("approved_at"),
        "reads": len(rec.get("read", [])), "writes": len(rec.get("wrote", [])), "deps": [f"{d['name']}@{d['version']}" for d in rec.get("added_deps", [])],
        "tests": rec.get("tests"), "needs_review": pf["needs_review"], "findings": len(pf["findings"]), "top_severity": top,
        "reviewed": os.path.isfile(_review_path(commit["sha"])),
    }


# ----------------------------------------------------------------------------- bob
def _review_path(sha: str) -> str:
    return os.path.join(DATA, "reviews", f"{sha}.json")


def _draft_path(needle: str) -> str:
    return os.path.join(DATA, "drafts", re.sub(r"[^A-Za-z0-9_.@-]", "_", needle) + ".json")


def bob_available() -> tuple[bool, str]:
    if not shutil.which("bob"):
        return False, "bob shell not installed"
    if not os.environ.get("BOB_API_KEY"):
        return False, "BOB_API_KEY not set"
    return True, "ok"


def _extract_json(text: str):
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.S) or re.search(r"(\{.*\})", text, re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except json.JSONDecodeError:
        return None


def bob_run(prompt: str, attachments: dict[str, str] | None = None) -> dict:
    """Run Bob Shell headless in a throwaway workspace. Returns {ok, text, json, raw, cost, error}."""
    ok, why = bob_available()
    if not ok:
        return {"ok": False, "error": why}
    ws = tempfile.mkdtemp(prefix="origit-review-")
    try:
        for name, content in (attachments or {}).items():
            with open(os.path.join(ws, name), "w", encoding="utf-8") as f:
                f.write(content)
        with open(os.path.join(ws, "PROMPT.md"), "w", encoding="utf-8") as f:
            f.write(prompt)
        cmd = ["bob", "run", "--format", "json", "--max-cost", BOB_MAX_COST, "--max-turns", BOB_MAX_TURNS, "--workspace", ws,
               "--mode", os.environ.get("BOB_REVIEW_MODE", "ask"), "--disable-mcp", "--disable-subagents", "--accept-license", "--trust",
               "--log-level", "error"]
        if os.environ.get("BOB_TEAM_ID"):
            cmd += ["--team-id", os.environ["BOB_TEAM_ID"]]
        cmd.append("Follow the instructions in @PROMPT.md exactly. Reply with the JSON only.")
        t0 = time.time()
        p = subprocess.run(cmd, capture_output=True, text=True, cwd=ws, timeout=600)
        raw = p.stdout
        text = raw
        parsed = None
        try:
            obj = json.loads(raw)
            # best-effort: find the final assistant text in Bob Shell's JSON envelope
            for key in ("result", "output", "text", "final", "message", "content"):
                if isinstance(obj, dict) and isinstance(obj.get(key), str):
                    text = obj[key]
                    break
            if isinstance(obj, dict) and isinstance(obj.get("messages"), list):
                texts = [m.get("content") or m.get("text") for m in obj["messages"] if isinstance(m, dict)]
                texts = [t for t in texts if isinstance(t, str)]
                if texts:
                    text = texts[-1]
            stats = obj.get("stats") if isinstance(obj, dict) else None
        except json.JSONDecodeError:
            stats = None
        parsed = _extract_json(text)
        return {"ok": p.returncode == 0 and parsed is not None, "text": text, "json": parsed, "raw": raw[-20000:],
                "stderr": p.stderr[-4000:], "stats": stats, "seconds": round(time.time() - t0, 1), "returncode": p.returncode}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "bob run timed out"}
    finally:
        shutil.rmtree(ws, ignore_errors=True)


def _prompt(name: str, **vars: str) -> str:
    tpl = open(os.path.join(HERE, "prompts", name), encoding="utf-8").read()
    for k, v in vars.items():
        tpl = tpl.replace("{{" + k + "}}", v)
    return tpl


def commit_diff(sha: str) -> str:
    if not _is_repo(REPO):
        return "(diff unavailable in evidence-pack mode)"
    p = subprocess.run(["git", "-C", REPO, "show", "--stat", "--patch", "--no-color", sha, "--", ".", ":(exclude)package-lock.json"], capture_output=True, text=True)
    return p.stdout[:40000]


def review(sha: str, force: bool = False) -> dict:
    path = _review_path(sha)
    if os.path.isfile(path) and not force:
        return json.load(open(path))
    data = load()
    commit = next((c for c in data["commits"] if c["sha"].startswith(sha)), None)
    if not commit or not commit.get("record"):
        return {"ok": False, "error": "no record for commit"}
    pf = prefilter_for(commit)
    if not pf["needs_review"]:
        return {"ok": True, "skipped": True, "reason": "pre-filter found nothing; Bob not called (zero coins)"}
    prompt = _prompt("asi-reviewer.md", sha=commit["sha"], subject=commit["subject"],
                     record=json.dumps(commit["record"], indent=2, ensure_ascii=False),
                     findings=json.dumps(pf["findings"], indent=2, ensure_ascii=False))
    res = bob_run(prompt, {"DIFF.patch": commit_diff(commit["sha"]), "asi-mapping.md": _asi_mapping()})
    res["sha"] = commit["sha"]
    res["reviewed_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    if res.get("ok"):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        json.dump(res, open(path, "w"), indent=2, ensure_ascii=False)
    return res


def _asi_mapping() -> str:
    p = os.path.join(ROOT, "docs", "asi-mapping.md")
    return open(p, encoding="utf-8").read() if os.path.isfile(p) else ""


def art14(needle: str, force: bool = False) -> dict:
    path = _draft_path(needle)
    if os.path.isfile(path) and not force:
        return json.load(open(path))
    data = load()
    t = X.query([(c["sha"], c["subject"], c.get("record")) for c in data["commits"]], needle)
    if not t["affected"]:
        return {"ok": False, "error": "nothing affected; nothing to report"}
    advisory = ""
    for cand in (os.path.join(REPO, "packages", "fast-pay-utils", "ADVISORY.md") if REPO else "", os.path.join(ROOT, "demo", "payments-api", "packages", "fast-pay-utils", "ADVISORY.md")):
        if cand and os.path.isfile(cand):
            advisory = open(cand, encoding="utf-8").read()
            break
    prompt = _prompt("art14-early-warning.md", needle=needle, product=data["name"], taint=json.dumps(t, indent=2, ensure_ascii=False),
                     now=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), advisory=advisory or "(no advisory text available)")
    res = bob_run(prompt)
    res["needle"] = needle
    res["drafted_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    if res.get("ok"):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        json.dump(res, open(path, "w"), indent=2, ensure_ascii=False)
    return res


# ----------------------------------------------------------------------------- http
class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=FRONTEND, **k)

    def log_message(self, fmt, *args):  # quieter
        sys.stderr.write("%s %s\n" % (self.address_string(), fmt % args))

    def _json(self, obj, status=200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        u = urlparse(self.path)
        q = parse_qs(u.query)
        try:
            if u.path == "/api/repo":
                d = load()
                bob_ok, bob_why = bob_available()
                self._json({"name": d["name"], "head": d["head"], "source": d["source"], "bob": {"available": bob_ok, "reason": bob_why},
                            "commits": [summary(c) for c in d["commits"]]})
            elif u.path.startswith("/api/commit/"):
                sha = u.path.rsplit("/", 1)[1]
                d = load()
                c = next((c for c in d["commits"] if c["sha"].startswith(sha)), None)
                if not c:
                    return self._json({"error": "unknown commit"}, 404)
                rp = _review_path(c["sha"])
                self._json({**summary(c), "record": c.get("record"), "verified": R.verify(c["record"]) if c.get("record") else None,
                            "prefilter": prefilter_for(c), "review": json.load(open(rp)) if os.path.isfile(rp) else None})
            elif u.path == "/api/taint":
                needle = (q.get("q") or [""])[0].strip()
                if not needle:
                    return self._json({"error": "q required"}, 400)
                d = load()
                t = X.query([(c["sha"], c["subject"], c.get("record")) for c in d["commits"]], needle)
                dp = _draft_path(needle)
                self._json({**t, "draft": json.load(open(dp)) if os.path.isfile(dp) else None})
            elif u.path == "/api/asi":
                self._json({"asi": PF.ASI, "cwe": PF.CWE, "severities": list(PF.SEVERITIES)})
            elif u.path.startswith("/api/"):
                self._json({"error": "not found"}, 404)
            else:
                if u.path == "/" or not os.path.isfile(os.path.join(FRONTEND, u.path.lstrip("/"))):
                    self.path = "/index.html"
                super().do_GET()
        except Exception as exc:  # noqa: BLE001
            self._json({"error": str(exc)}, 500)

    def do_POST(self):
        u = urlparse(self.path)
        q = parse_qs(u.query)
        force = (q.get("force") or ["0"])[0] == "1"
        try:
            if u.path.startswith("/api/review/"):
                self._json(review(u.path.rsplit("/", 1)[1], force))
            elif u.path == "/api/art14":
                self._json(art14((q.get("q") or [""])[0].strip(), force))
            else:
                self._json({"error": "not found"}, 404)
        except Exception as exc:  # noqa: BLE001
            self._json({"error": str(exc)}, 500)


def main() -> None:
    src = "git " + REPO if _is_repo(REPO) else "evidence " + EVIDENCE
    print(f"origit console on http://0.0.0.0:{PORT}  source={src}  bob={bob_available()}", file=sys.stderr)
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()


if __name__ == "__main__":
    main()
