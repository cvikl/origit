"""End-to-end: the session manager driven by hook payloads on a throwaway repo (one run = one commit = one record)."""

import json
import os
import subprocess

import pytest
from click.testing import CliRunner

from origit import cli
from origit import notes as N
from origit import record as R
from origit import sessions as S

SID = "ef74353172505a674f0bf4e712500d7e"


def git(repo, *args):
    return subprocess.run(["git", "-C", repo, *args], check=True, capture_output=True, text=True).stdout.strip()


@pytest.fixture
def repo(tmp_path, monkeypatch):
    p = str(tmp_path)
    git(p, "init", "-q", "-b", "main")
    git(p, "config", "user.email", "t@example.com")
    git(p, "config", "user.name", "tim")
    git(p, "config", "origit.approver", "bernard")
    (tmp_path / "README.md").write_text("# demo\n")
    git(p, "add", "README.md")
    git(p, "commit", "-q", "-m", "initial")
    monkeypatch.chdir(p)
    r = CliRunner().invoke(cli.main, ["init", "--session-base", "42"])
    assert r.exit_code == 0, r.output
    # make the git hooks call this checkout's CLI
    git(p, "config", "origit.bin", os.path.abspath(os.path.join(os.path.dirname(cli.__file__), "..", ".venv", "bin", "origit")))
    git(p, "add", "-A")
    git(p, "commit", "-q", "-m", "origit init")
    return p


def hook(args, payload):
    r = CliRunner().invoke(cli.main, args, input=json.dumps(payload))
    assert r.exit_code == 0, r.output
    return r


def bob_run(repo, prompt, writes, cmds=(), sid=SID):
    hook(["run", "start"], {"hook_event_name": "UserPromptSubmit", "session_id": sid, "prompt": prompt})
    for path, text in writes.items():
        hook(["trace"], {"hook_event_name": "PostToolUse", "session_id": sid, "tool_name": "read_file", "tool_input": {"path": "README.md"}, "tool_response": "..."})
        (os.path.join(repo, path) and open(os.path.join(repo, path), "w").write(text))
        hook(["trace"], {"hook_event_name": "PostToolUse", "session_id": sid, "tool_name": "write_file", "tool_input": {"path": path, "content": text}, "tool_response": "ok"})
    for c, out in cmds:
        hook(["trace"], {"hook_event_name": "PostToolUse", "session_id": sid, "tool_name": "execute_command", "tool_input": {"command": c}, "tool_response": out})
    hook(["run", "end"], {"hook_event_name": "Stop", "session_id": sid, "last_assistant_message": "Done.\n\nOrigit declaration\nread: README.md"})


def test_session_start_assigns_display_number_and_snapshots(repo):
    hook(["session", "start"], {"hook_event_name": "SessionStart", "session_id": SID, "cwd": repo})
    st = json.load(open(os.path.join(repo, ".origit", "session.json")))
    assert st["id"] == SID and st["number"] == 42 and st["run"] == 0 and st["head"] == git(repo, "rev-parse", "HEAD")
    r = CliRunner().invoke(cli.main, ["session", "status", "--json"])
    assert json.loads(r.output) == {"id": SID, "number": 42, "label": "#42", "run": 0, "started_at": st["started_at"], "recording": True}


def test_run_commits_with_generated_subject_and_record(repo):
    hook(["session", "start"], {"hook_event_name": "SessionStart", "session_id": SID})
    bob_run(repo, "Add a payout export module.\nUse CSV.", {"src.ts": "export const a = 1;\n"}, cmds=[("npm test", "Tests:       3 passed, 3 total")])
    head = git(repo, "rev-parse", "HEAD")
    assert git(repo, "log", "-1", "--format=%s") == "bob: Add a payout export module. [session #42 run 1]"
    rec = N.read(repo, head)
    assert rec and R.verify(rec)
    assert rec["actor"]["kind"] == "bob-ide"
    assert rec["session"]["id"] == SID and rec["session"]["number"] == 42 and rec["session"]["run"] == 1
    assert rec["session"]["prompt"].startswith("Add a payout export module.")
    assert rec["wrote"] == ["src.ts"] and [x["ref"] for x in rec["read"]] == ["README.md"]
    assert rec["tests"] == {"run": True, "passed": 3, "failed": 0}
    assert rec["approver"] == "bernard"
    st = json.load(open(os.path.join(repo, ".origit", "session.json")))
    assert st["runs"][0]["sha"] == head and st["run"] == 1
    # trace cleared after the run was sealed
    assert open(os.path.join(repo, ".origit", "trace.jsonl")).read() == ""


def test_second_run_same_session_and_human_edit_between_runs(repo):
    hook(["session", "start"], {"hook_event_name": "SessionStart", "session_id": SID})
    bob_run(repo, "first", {"a.ts": "1\n"})
    first = git(repo, "rev-parse", "HEAD")
    open(os.path.join(repo, "notes.md"), "w").write("human edit\n")  # human edits between runs
    bob_run(repo, "second run", {"b.ts": "2\n"})
    log = git(repo, "log", "--format=%s", "-3").splitlines()
    assert log == ["bob: second run [session #42 run 2]", "human: edits before session #42 run 2", "bob: first [session #42 run 1]"]
    shas = git(repo, "log", "--format=%H", "-3").splitlines()
    human = N.read(repo, shas[1])
    assert human["actor"]["kind"] == "human" and human["read"] == []
    second = N.read(repo, shas[0])
    assert second["session"]["run"] == 2 and second["wrote"] == ["b.ts"]
    assert git(repo, "status", "--porcelain", "--", ".", ":(exclude).origit") == ""
    assert N.read(repo, first)["session"]["run"] == 1


def test_run_with_no_changes_keeps_record_without_commit(repo):
    hook(["session", "start"], {"hook_event_name": "SessionStart", "session_id": SID})
    before = git(repo, "rev-parse", "HEAD")
    hook(["run", "start"], {"hook_event_name": "UserPromptSubmit", "session_id": SID, "prompt": "just look"})
    hook(["trace"], {"hook_event_name": "PostToolUse", "session_id": SID, "tool_name": "read_file", "tool_input": {"path": "README.md"}, "tool_response": "x"})
    hook(["run", "end"], {"hook_event_name": "Stop", "session_id": SID})
    assert git(repo, "rev-parse", "HEAD") == before
    p = os.path.join(repo, ".origit", "runs", f"{SID}-1.json")
    rec = json.load(open(p))
    assert R.verify(rec) and rec["session"]["run"] == 1 and rec["read"][0]["ref"] == "README.md"
    # idempotent: a second Stop with nothing new does not commit either
    hook(["run", "end"], {"hook_event_name": "Stop", "session_id": SID})
    assert git(repo, "rev-parse", "HEAD") == before


def test_failed_tests_are_recorded_not_gated(repo):
    hook(["session", "start"], {"hook_event_name": "SessionStart", "session_id": SID})
    bob_run(repo, "break it", {"c.ts": "3\n"}, cmds=[("npm test", "Tests:       1 failed, 2 passed, 3 total")])
    rec = N.read(repo, git(repo, "rev-parse", "HEAD"))
    assert rec["tests"] == {"run": True, "passed": 2, "failed": 1}


def test_new_session_gets_next_number_and_log_groups(repo):
    hook(["session", "start"], {"hook_event_name": "SessionStart", "session_id": SID})
    bob_run(repo, "one", {"a.ts": "1\n"})
    sid2 = "94d788ea8a60c055b001b210820462e6"
    hook(["session", "start"], {"hook_event_name": "SessionStart", "session_id": sid2})
    bob_run(repo, "two", {"b.ts": "2\n"}, sid=sid2)
    bob_run(repo, "three", {"b.ts": "3\n"}, sid=sid2)
    r = CliRunner().invoke(cli.main, ["log", "--json"])
    data = json.loads(r.output)
    assert data["base"] == 42
    labels = [(s["label"], [x["run"] for x in s["runs"]]) for s in data["sessions"]]
    assert labels == [("#43", [2, 1]), ("#42", [1]), ("human", [None]), ("none", [None])]
    assert data["sessions"][0]["runs"][0]["n_wrote"] == 1 and data["sessions"][0]["runs"][0]["prefilter"]["needs_review"] is False
    r = CliRunner().invoke(cli.main, ["taint", "b.ts", "--json"])
    t = json.loads(r.output)
    assert t["session_labels"] == {sid2: "#43"} and t["affected"][0]["session_label"] == "#43"
    r = CliRunner().invoke(cli.main, ["show", "HEAD", "--json"])
    assert json.loads(r.output)["verified"] is True
    text = CliRunner().invoke(cli.main, ["log"]).output
    assert "session #43 · Bob IDE" in text and "run 2" in text


def test_hash_stable_across_reload(repo):
    hook(["session", "start"], {"hook_event_name": "SessionStart", "session_id": SID})
    bob_run(repo, "x", {"a.ts": "1\n"})
    rec = N.read(repo, git(repo, "rev-parse", "HEAD"))
    assert R.record_hash(R.loads(R.dumps(rec))) == rec["record_sha256"]
