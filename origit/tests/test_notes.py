"""Acceptance for notes.py — Bob task T03. Uses a throwaway git repo."""

import subprocess

import pytest

from origit import notes as N
from origit import record as R


def git(repo, *args):
    return subprocess.run(["git", "-C", repo, *args], check=True, capture_output=True, text=True).stdout.strip()


@pytest.fixture
def repo(tmp_path):
    p = str(tmp_path)
    git(p, "init", "-q")
    git(p, "config", "user.email", "t@example.com")
    git(p, "config", "user.name", "t")
    (tmp_path / "a.txt").write_text("a\n")
    git(p, "add", "a.txt")
    git(p, "commit", "-q", "-m", "first")
    (tmp_path / "b.txt").write_text("b\n")
    git(p, "add", "b.txt")
    git(p, "commit", "-q", "-m", "second")
    return p


def make_record(sid="ses_1"):
    return R.finalize({
        "schema": R.SCHEMA, "session": {"id": sid, "started_at": None, "ended_at": None},
        "actor": {"kind": "bob-ide", "model": None, "mode": None, "config_sha256": None},
        "read": [{"kind": "file", "ref": "a.txt", "sha256": None}], "wrote": ["b.txt"], "added_deps": [],
        "commands": [], "author": "t", "approver": None, "approved_at": None,
        "tests": {"run": False, "passed": 0, "failed": 0},
    })


def test_write_read_roundtrip(repo):
    sha = N.head(repo)
    assert len(sha) == 40
    rec = make_record()
    N.write(repo, sha, rec)
    assert N.read(repo, sha) == rec
    assert R.verify(N.read(repo, sha))
    # stored under refs/notes/origit, not the default notes ref
    assert git(repo, "notes", "--ref=origit", "list") != ""
    assert git(repo, "notes", "list") == ""


def test_read_missing_is_none(repo):
    assert N.read(repo, N.head(repo)) is None


def test_overwrite_replaces(repo):
    sha = N.head(repo)
    N.write(repo, sha, make_record("ses_1"))
    N.write(repo, sha, make_record("ses_2"))
    assert N.read(repo, sha)["session"]["id"] == "ses_2"


def test_commits_newest_first_with_records(repo):
    sha = N.head(repo)
    N.write(repo, sha, make_record())
    out = N.commits(repo)
    assert [s for _, s, _ in out] == ["second", "first"]
    assert out[0][0] == sha and out[0][2]["session"]["id"] == "ses_1"
    assert out[1][2] is None


def test_bad_repo_raises(tmp_path):
    with pytest.raises(N.NotesError):
        N.head(str(tmp_path))
