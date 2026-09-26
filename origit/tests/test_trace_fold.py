"""Acceptance for trace.fold — Bob task T02. Spec: docstring of origit/trace.py."""

from origit import trace as T


def ev(event, tool=None, inp=None, sid="ses_42", ts="2026-09-26T12:00:00Z", output="ok"):
    e = {"event": event, "session_id": sid, "ts": ts}
    if tool:
        e.update(tool=tool, input=inp or {}, output=output)
    return e


def sample():
    return [
        ev("SessionStart", ts="2026-09-26T12:00:00Z"),
        ev("PreToolUse", "read_file", {"path": "node_modules/fast-pay-utils/README.md"}, ts="2026-09-26T12:00:05Z"),
        ev("PostToolUse", "read_file", {"path": "node_modules/fast-pay-utils/README.md"}, ts="2026-09-26T12:00:06Z"),
        ev("PostToolUse", "read_file", {"path": "src/index.ts"}, ts="2026-09-26T12:00:10Z"),
        ev("PostToolUse", "grep", {"path": "src", "pattern": "sendPayment"}, ts="2026-09-26T12:00:12Z"),
        ev("PostToolUse", "execute_command", {"command": "npm install fast-pay-utils@2.1.0 --save-exact"}, ts="2026-09-26T12:01:00Z"),
        ev("PostToolUse", "write_file", {"path": "src/payout-export.ts", "content": "..."}, ts="2026-09-26T12:02:00Z"),
        ev("PostToolUse", "apply_diff", {"path": "src/payment-utils.ts", "diff": "..."}, ts="2026-09-26T12:03:00Z"),
        ev("PostToolUse", "use_mcp_tool", {"server_name": "docs", "tool_name": "search"}, ts="2026-09-26T12:03:30Z"),
        ev("PostToolUse", "execute_command", {"command": "npm test"}, ts="2026-09-26T12:04:00Z"),
        ev("Stop", ts="2026-09-26T12:05:00Z"),
    ]


def test_session_and_actor():
    r = T.fold(sample())
    assert r["session"] == {"id": "ses_42", "started_at": "2026-09-26T12:00:00Z", "ended_at": "2026-09-26T12:05:00Z"}
    assert r["actor"]["kind"] == "bob-ide"


def test_reads_only_from_post_tool_use_and_deduped():
    r = T.fold(sample())
    refs = [(x["kind"], x["ref"]) for x in r["read"]]
    assert refs.count(("file", "node_modules/fast-pay-utils/README.md")) == 1  # Pre+Post -> one
    assert ("file", "src/index.ts") in refs
    assert ("file", "src") in refs  # grep over a directory is a read of that directory
    assert ("mcp", "docs/search") in refs


def test_writes_commands_and_deps():
    r = T.fold(sample())
    assert r["wrote"] == ["src/payment-utils.ts", "src/payout-export.ts"]
    assert r["commands"] == ["npm install fast-pay-utils@2.1.0 --save-exact", "npm test"]
    assert r["added_deps"] == [{"name": "fast-pay-utils", "version": "2.1.0", "registry": "npm", "lockfile_sha256": None}]
    # a dependency add is also a read of that package
    assert ("pkg", "fast-pay-utils@2.1.0") in [(x["kind"], x["ref"]) for x in r["read"]]


def test_wrapped_fallback_events_are_unwrapped():
    wrapped = [{"ts": e["ts"], "raw": {k: v for k, v in e.items() if k != "ts"}} for e in sample()]
    assert T.fold(wrapped) == T.fold(sample())


def test_empty_trace_is_human():
    r = T.fold([])
    assert r["actor"]["kind"] == "human"
    assert r["read"] == [] and r["wrote"] == [] and r["commands"] == [] and r["added_deps"] == []


def test_fold_output_finalizes_as_record():
    from origit import record as R

    r = T.fold(sample())
    r.update(author="tim", approver="bernard", approved_at="2026-09-26T13:00:00Z", tests={"run": True, "passed": 3, "failed": 0}, schema=R.SCHEMA)
    assert R.verify(R.finalize(r))
