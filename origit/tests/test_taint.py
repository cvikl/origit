"""Acceptance for taint.query — Bob task T04. Spec: docstring of origit/taint.py.

Input is the commit list newest-first as produced by `git rev-list`, each with its record (or None)."""

from origit import taint as X
from origit import record as R


def rec(sid, started, reads=(), deps=(), wrote=(), approver="bernard", actor="bob-ide"):
    r = {
        "schema": R.SCHEMA,
        "session": {"id": sid, "started_at": started, "ended_at": started},
        "actor": {"kind": actor, "model": None, "mode": "origit-build", "config_sha256": None},
        "read": [{"kind": k, "ref": ref, "sha256": sha} for k, ref, sha in reads],
        "wrote": list(wrote),
        "added_deps": [{"name": n, "version": v, "registry": "npm", "lockfile_sha256": None} for n, v in deps],
        "commands": [],
        "author": "tim",
        "approver": approver,
        "approved_at": "2026-09-26T14:02:00Z",
        "tests": {"run": True, "passed": 5, "failed": 0},
    }
    return R.finalize(r)


README_SHA = "ab" * 32

# newest first (built lazily: record.finalize is a Bob task too)
def commits():
    return [
    ("f0f0f0f", "chore: bump version", rec("ses_45", "2026-09-26T16:00:00Z", actor="human", approver=None)),
    ("d4d4d4d", "feat: export schedule (session 44)", rec("ses_44", "2026-09-26T15:00:00Z",
        reads=[("file", "src/payout-export.ts", None)], wrote=["src/payout-export.ts"])),
    ("c3c3c3c", "feat: payment utils (session 43)", rec("ses_43", "2026-09-26T14:00:00Z",
        reads=[("file", "node_modules/fast-pay-utils/README.md", README_SHA)], wrote=["src/payment-utils.ts"])),
    ("b2b2b2b", "feat: add fast-pay-utils (session 42)", rec("ses_42", "2026-09-26T13:00:00Z",
        reads=[("file", "node_modules/fast-pay-utils/README.md", README_SHA), ("pkg", "fast-pay-utils@2.1.0", None)],
        deps=[("fast-pay-utils", "2.1.0")], wrote=["src/payout-export.ts"])),
    ("e19b770", "feat: api scaffold (session 41)", rec("ses_41", "2026-09-26T12:00:00Z",
        reads=[("file", "src/index.ts", None)], wrote=["src/index.ts", "src/routes.ts"])),
    ("a1a1a1a", "chore: initial commit", None),
    ]


def test_taint_by_package_name():
    out = X.query(commits(), "fast-pay-utils")
    assert [c["sha"] for c in out["affected"]] == ["d4d4d4d", "c3c3c3c", "b2b2b2b"]
    assert out["sessions"] == ["ses_42", "ses_43", "ses_44"]
    assert out["files_written"] == ["src/payment-utils.ts", "src/payout-export.ts"]
    assert out["approvers"] == ["bernard"]
    assert out["first_read"] == {"session": "ses_42", "at": "2026-09-26T13:00:00Z", "commit": "b2b2b2b"}
    assert out["rollback_commit"] == "e19b770"
    assert [c["sha"] for c in out["clean"]] == ["f0f0f0f", "e19b770", "a1a1a1a"]


def test_taint_propagates_through_files_written():
    """Session 44 never read the package, but it read and rewrote a file that a tainted session wrote."""
    out = X.query(commits(), "fast-pay-utils@2.1.0")
    assert "d4d4d4d" in [c["sha"] for c in out["affected"]]


def test_taint_by_file_and_by_sha256():
    assert [c["sha"] for c in X.query(commits(), "node_modules/fast-pay-utils/README.md")["affected"]] == ["d4d4d4d", "c3c3c3c", "b2b2b2b"]
    assert [c["sha"] for c in X.query(commits(), README_SHA)["affected"]] == ["d4d4d4d", "c3c3c3c", "b2b2b2b"]


def test_no_match():
    out = X.query(commits(), "left-pad")
    assert out["affected"] == [] and out["rollback_commit"] is None and out["first_read"] is None
    assert len(out["clean"]) == len(commits())


def test_version_mismatch_does_not_match():
    assert X.query(commits(), "fast-pay-utils@2.0.0")["affected"] == []


def test_affected_entry_shape():
    c = X.query(commits(), "fast-pay-utils")["affected"][-1]
    assert c == {
        "sha": "b2b2b2b",
        "subject": "feat: add fast-pay-utils (session 42)",
        "session": "ses_42",
        "actor": "bob-ide",
        "approver": "bernard",
        "approved_at": "2026-09-26T14:02:00Z",
        "wrote": ["src/payout-export.ts"],
        "matched": ["added_deps:fast-pay-utils@2.1.0", "read:file:node_modules/fast-pay-utils/README.md", "read:pkg:fast-pay-utils@2.1.0"],
    }
