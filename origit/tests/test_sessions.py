"""Session display ids (#42) and grouping — spec: docstring of origit/sessions.py."""

from origit import record as R
from origit import sessions as S


def rec(sid, started, number=None, run=None, actor="bob-ide"):
    r = {
        "schema": R.SCHEMA, "session": {"id": sid, "started_at": started, "ended_at": started},
        "actor": {"kind": actor, "model": None, "mode": "origit-build", "config_sha256": None},
        "read": [{"kind": "file", "ref": "a", "sha256": None}], "wrote": ["b"], "added_deps": [], "commands": [],
        "author": "tim", "approver": "bernard", "approved_at": started, "tests": {"run": True, "passed": 1, "failed": 0},
    }
    if number is not None:
        r["session"]["number"] = number
    if run is not None:
        r["session"]["run"] = run
    return R.finalize(r)


def commits():
    return [  # newest first
        ("f", "run 2 of new session", rec("s_new", "2026-09-27T10:01:00Z", number=45, run=2)),
        ("e", "run 1 of new session", rec("s_new", "2026-09-27T10:00:00Z", number=45, run=1)),
        ("d", "human edit", rec("human:tim", "2026-09-27T09:00:00Z", actor="human")),
        ("c", "session C", rec("s_c", "2026-09-26T14:00:00Z")),
        ("b", "session A again", rec("s_a", "2026-09-26T13:30:00Z")),
        ("a", "session A", rec("s_a", "2026-09-26T13:00:00Z")),
        ("0", "initial", None),
    ]


def test_numbers_by_first_appearance_from_base_skipping_explicit():
    n = S.number_sessions(commits(), base=42)
    assert n == {"s_a": 42, "s_c": 43, "s_new": 45}
    assert S.next_number(commits(), base=42) == 46
    assert S.next_number([], base=42) == 42


def test_explicit_number_wins_and_is_deterministic():
    assert S.number_sessions(commits(), base=1) == {"s_a": 1, "s_c": 2, "s_new": 45}
    assert S.number_sessions(commits(), base=1) == S.number_sessions(commits(), base=1)


def test_label():
    assert S.label(42) == "#42" and S.label(None) == "–"


def test_group_newest_first_with_runs():
    g = S.group(commits(), base=42)
    assert [s["label"] for s in g] == ["#45", "human", "#43", "#42", "none"]
    assert [r["run"] for r in g[0]["runs"]] == [2, 1]
    assert g[0]["started_at"] == "2026-09-27T10:00:00Z" and g[0]["ended_at"] == "2026-09-27T10:01:00Z"
    assert [r["sha"] for r in g[3]["runs"]] == ["b", "a"]
    assert g[4]["runs"][0]["record"] is None and g[4]["actor"] == "none"


def test_base_from_config(tmp_path):
    assert S.base(str(tmp_path)) == 1
    (tmp_path / ".origit").mkdir()
    (tmp_path / ".origit" / "config.json").write_text('{"session_base": 42}')
    assert S.base(str(tmp_path)) == 42
