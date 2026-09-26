"""Hashing first: these tests pin the canonical form so records are tamper-evident
and independent of trace order / key order / serialisation whitespace."""

import json

import pytest

from origit import record as R


def base():
    return {
        "schema": R.SCHEMA,
        "session": {"id": "ses_42", "started_at": "2026-09-24T09:10:00Z", "ended_at": "2026-09-24T09:40:00Z"},
        "actor": {"kind": "bob-ide", "model": None, "mode": "origit-build", "config_sha256": "ab" * 32},
        "read": [
            {"kind": "pkg", "ref": "fast-pay-utils@2.1.0", "sha256": "11" * 32},
            {"kind": "file", "ref": "node_modules/fast-pay-utils/README.md", "sha256": "22" * 32},
        ],
        "wrote": ["src/payout-export.ts", "src/payment-utils.ts"],
        "added_deps": [{"name": "fast-pay-utils", "version": "2.1.0", "registry": "npm", "lockfile_sha256": None}],
        "commands": ["npm install fast-pay-utils@2.1.0", "npm test"],
        "author": "tim",
        "approver": "bernard",
        "approved_at": "2026-09-26T14:02:00Z",
        "tests": {"run": True, "passed": 7, "failed": 0},
    }


def test_finalize_adds_hash_and_verifies():
    rec = R.finalize(base())
    assert len(rec["record_sha256"]) == 64
    assert R.verify(rec)


def test_hash_is_deterministic_across_key_order():
    a = base()
    b = json.loads(json.dumps(a))
    # reorder top-level keys
    b = {k: b[k] for k in reversed(list(b))}
    assert R.record_hash(a) == R.record_hash(b)


def test_hash_independent_of_read_order_and_duplicates():
    a = base()
    b = base()
    b["read"] = list(reversed(b["read"])) + [b["read"][0]]  # reversed + duplicate
    b["wrote"] = list(reversed(b["wrote"]))
    assert R.record_hash(a) == R.record_hash(b)
    assert len(R.finalize(b)["read"]) == 2


def test_command_order_matters():
    a = base()
    b = base()
    b["commands"] = list(reversed(b["commands"]))
    assert R.record_hash(a) != R.record_hash(b)


def test_tamper_detected():
    rec = R.finalize(base())
    rec["approver"] = "mallory"
    assert not R.verify(rec)
    rec2 = R.finalize(base())
    rec2["read"][0]["ref"] = "fast-pay-utils@2.0.0"
    assert not R.verify(rec2)


def test_missing_hash_fails_verify():
    assert not R.verify(base())


def test_roundtrip_dumps_loads_preserves_hash():
    rec = R.finalize(base())
    text = R.dumps(rec)
    back = R.loads(text)
    assert back == rec
    assert R.verify(back)
    # canonical text has no whitespace and sorted keys
    assert " " not in text.replace("npm install fast-pay-utils@2.1.0", "").replace("npm test", "")
    assert text.startswith('{"actor":')


def test_unicode_tag_characters_survive_canonicalisation():
    a = base()
    smuggled = "README.md" + "\U000E0001" + "\U000E0049" + "\U000E007F"
    a["read"].append({"kind": "file", "ref": smuggled, "sha256": None})
    rec = R.finalize(a)
    assert any(r["ref"] == smuggled for r in rec["read"])
    assert "\\u" not in R.dumps(rec)  # ensure_ascii=False: stored as real UTF-8, not escapes
    assert R.verify(R.loads(R.dumps(rec)))


def test_canonical_bytes_are_utf8_and_stable():
    a = base()
    b1 = R.canonical_bytes(a)
    b2 = R.canonical_bytes(json.loads(json.dumps(a)))
    assert b1 == b2
    assert b1 == b1.decode("utf-8").encode("utf-8")


@pytest.mark.parametrize(
    "mutate,msg",
    [
        (lambda r: r.pop("tests"), "missing keys"),
        (lambda r: r.update(schema="origit/record/v0"), "unknown schema"),
        (lambda r: r["session"].update(id=""), "session.id"),
        (lambda r: r["read"].append({"kind": "email", "ref": "x"}), "bad read"),
        (lambda r: r["wrote"].append(""), "bad wrote"),
    ],
)
def test_validation_errors(mutate, msg):
    r = base()
    mutate(r)
    with pytest.raises(R.RecordError, match=msg):
        R.finalize(r)


def test_dataclass_builder_matches_dict_form():
    rec = R.Record(
        session=R.Session(id="ses_42", started_at="2026-09-24T09:10:00Z", ended_at="2026-09-24T09:40:00Z"),
        actor=R.Actor(kind="bob-ide", mode="origit-build", config_sha256="ab" * 32),
        read=[
            R.Read("pkg", "fast-pay-utils@2.1.0", "11" * 32),
            R.Read("file", "node_modules/fast-pay-utils/README.md", "22" * 32),
        ],
        wrote=["src/payout-export.ts", "src/payment-utils.ts"],
        added_deps=[R.Dep("fast-pay-utils", "2.1.0")],
        commands=["npm install fast-pay-utils@2.1.0", "npm test"],
        author="tim",
        approver="bernard",
        approved_at="2026-09-26T14:02:00Z",
        tests=R.Tests(run=True, passed=7, failed=0),
    ).finalize()
    assert rec["record_sha256"] == R.finalize(base())["record_sha256"]


def test_file_sha256(tmp_path):
    p = tmp_path / "x.txt"
    p.write_bytes(b"hello")
    assert R.file_sha256(str(p)) == "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
    assert R.file_sha256(str(tmp_path / "nope")) is None
