"""Acceptance for origit/mcp.py — Bob task 11. Spec: the module docstring. Uses a throwaway repo with one record."""

import json
import subprocess
import sys

import pytest

from origit import __version__
from origit import mcp as M
from origit import notes as N
from origit import record as R


def git(repo, *args):
    return subprocess.run(["git", "-C", repo, *args], check=True, capture_output=True, text=True).stdout.strip()


@pytest.fixture
def repo(tmp_path):
    p = str(tmp_path)
    git(p, "init", "-q", "-b", "main")
    git(p, "config", "user.email", "t@example.com")
    git(p, "config", "user.name", "t")
    (tmp_path / "README.md").write_text("# x\n")
    git(p, "add", "README.md")
    git(p, "commit", "-q", "-m", "first")
    (tmp_path / "src.ts").write_text("export const a = 1;\n")
    git(p, "add", "src.ts")
    git(p, "commit", "-q", "-m", "bob: add src [session #42 run 1]")
    rec = R.finalize({
        "schema": R.SCHEMA, "session": {"id": "ef74353172505a674f0bf4e712500d7e", "number": 42, "run": 1, "started_at": "2026-09-27T09:00:00Z", "ended_at": "2026-09-27T09:05:00Z"},
        "actor": {"kind": "bob-ide", "model": None, "mode": "origit-build", "config_sha256": None},
        "read": [{"kind": "file", "ref": "node_modules/fast-pay-utils/README.md", "sha256": None}, {"kind": "pkg", "ref": "fast-pay-utils@2.1.0", "sha256": None}],
        "wrote": ["src.ts"], "added_deps": [{"name": "fast-pay-utils", "version": "2.1.0", "registry": "npm", "lockfile_sha256": None}],
        "commands": ["npm test"], "author": "t", "approver": "bernard", "approved_at": "2026-09-27T09:05:00Z", "tests": {"run": True, "passed": 3, "failed": 0},
    })
    N.write(p, N.head(p), rec)
    return p


def rpc(i, method, params=None):
    return {"jsonrpc": "2.0", "id": i, "method": method, **({"params": params} if params is not None else {})}


def test_initialize_and_tools_list(repo):
    res = M.handle(rpc(1, "initialize", {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "bob"}}), repo)
    assert res["jsonrpc"] == "2.0" and res["id"] == 1
    assert res["result"]["protocolVersion"] == "2024-11-05" and res["result"]["serverInfo"] == {"name": "origit", "version": __version__}
    assert "tools" in res["result"]["capabilities"]
    assert M.handle({"jsonrpc": "2.0", "method": "notifications/initialized"}, repo) is None
    assert M.handle(rpc(2, "ping"), repo)["result"] == {}
    tools = M.handle(rpc(3, "tools/list"), repo)["result"]["tools"]
    assert [t["name"] for t in tools] == ["origit_taint", "origit_show", "origit_log"]
    for t in tools:
        assert t["description"] and t["inputSchema"]["type"] == "object"
    assert M.handle(rpc(4, "nope"), repo)["error"]["code"] == -32601


def test_tool_calls(repo):
    head = git(repo, "rev-parse", "HEAD")
    res = M.handle(rpc(5, "tools/call", {"name": "origit_taint", "arguments": {"needle": "fast-pay-utils"}}), repo)["result"]
    assert res["isError"] is False
    data = json.loads(res["content"][0]["text"])
    assert [c["sha"] for c in data["affected"]] == [head] and data["affected"][0]["session_label"] == "#42"
    assert data["session_labels"] == {"ef74353172505a674f0bf4e712500d7e": "#42"}
    res = M.handle(rpc(6, "tools/call", {"name": "origit_show", "arguments": {"commit": "HEAD"}}), repo)["result"]
    data = json.loads(res["content"][0]["text"])
    assert data["sha"] == head and data["verified"] is True and data["record"]["wrote"] == ["src.ts"]
    res = M.handle(rpc(7, "tools/call", {"name": "origit_show", "arguments": {"commit": "HEAD~1"}}), repo)["result"]
    assert json.loads(res["content"][0]["text"])["record"] is None
    res = M.handle(rpc(8, "tools/call", {"name": "origit_log", "arguments": {}}), repo)["result"]
    data = json.loads(res["content"][0]["text"])
    assert data["head"] == head and data["sessions"][0]["label"] == "#42" and data["sessions"][0]["runs"][0]["n_deps"] == 1
    assert "record" not in data["sessions"][0]["runs"][0]
    res = M.handle(rpc(9, "tools/call", {"name": "origit_show", "arguments": {"commit": "doesnotexist"}}), repo)["result"]
    assert res["isError"] is True
    res = M.handle(rpc(10, "tools/call", {"name": "unknown_tool", "arguments": {}}), repo)["result"]
    assert res["isError"] is True


def test_serve_over_stdio(repo):
    msgs = [rpc(1, "initialize", {"protocolVersion": "2024-11-05", "capabilities": {}}), {"jsonrpc": "2.0", "method": "notifications/initialized"},
            rpc(2, "tools/call", {"name": "origit_taint", "arguments": {"needle": "fast-pay-utils"}}), "this is not json"]
    inp = "\n".join(json.dumps(m) if not isinstance(m, str) else m for m in msgs) + "\n"
    p = subprocess.run([sys.executable, "-m", "origit", "mcp"], input=inp, capture_output=True, text=True, cwd=repo, timeout=30)
    lines = [json.loads(l) for l in p.stdout.splitlines() if l.strip()]
    assert [l["id"] for l in lines] == [1, 2]
    assert json.loads(lines[1]["result"]["content"][0]["text"])["affected"]
