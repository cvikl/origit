"""Deterministic ASI pre-filter — decides whether a push needs Bob's review.

Runs on every push in the console (and locally via ``origit prefilter``). Costs zero Bobcoins.
Bob is only asked to write ASI evidence when at least one trigger fires.

Triggers (each returns a Finding {asi, severity, cwe, evidence, ref}):
  * new dependency present (added_deps non-empty)              -> ASI04 low, CWE-829
  * external read present (read.kind in url|mcp)                -> ASI01 informational, CWE-829
  * command executed (commands non-empty)                       -> ASI05 informational, CWE-94
  * agent config changed (.bob/, CLAUDE.md, AGENTS.md, rules, skills) -> ASI01 medium, CWE-829
  * invisible / bidi characters in anything the agent read      -> ASI01 high, CWE-506
      Unicode tag block  [\\U000E0000-\\U000E007F]  (decoded and quoted as evidence)
      zero-width         U+200B U+200C U+200D U+2060 U+FEFF
      bidi overrides     U+202A-U+202E U+2066-U+2069
  * secrets/env touched (.env, *.pem, id_rsa, *.key)            -> ASI03 medium, CWE-200

Severity labels are CVSS-style hints for the console; Bob's evidence may raise or lower them.
Jeremy owns the rule list; keep each rule a small pure function so it is unit-testable.
"""

from __future__ import annotations

import re
from typing import Any

UNICODE_TAG_RE = re.compile(r"[\U000E0000-\U000E007F]")
INVISIBLE_RE = re.compile(r"[​‌‍⁠﻿]")
BIDI_RE = re.compile(r"[‪-‮⁦-⁩]")

AGENT_CONFIG_RE = re.compile(r"(^|/)(\.bob/|\.bobrules|CLAUDE\.md$|AGENTS\.md$|\.cursorrules$|\.claude/|skills?/)")
SECRET_PATH_RE = re.compile(r"(^|/)(\.env(\..*)?$|.*\.pem$|id_rsa|.*\.key$|secrets?\.(json|ya?ml)$)")

CWE = {
    "CWE-506": "Embedded Malicious Code",
    "CWE-829": "Inclusion of Functionality from Untrusted Control Sphere",
    "CWE-94": "Improper Control of Generation of Code (Code Injection)",
    "CWE-200": "Exposure of Sensitive Information to an Unauthorized Actor",
}

ASI = {
    "ASI01": "Agent Goal Hijack",
    "ASI02": "Tool Misuse and Exploitation",
    "ASI03": "Identity and Privilege Abuse",
    "ASI04": "Agentic Supply Chain Vulnerabilities",
    "ASI05": "Unexpected Code Execution (RCE)",
    "ASI06": "Memory and Context Poisoning",
    "ASI07": "Insecure Inter-Agent Communication",
    "ASI08": "Cascading Failures",
    "ASI09": "Human-Agent Trust Exploitation",
    "ASI10": "Rogue Agents",
}

SEVERITIES = ("informational", "low", "medium", "high", "critical")


def has_hidden_text(text: str) -> dict[str, int]:
    """Count invisible / smuggling characters in text. Empty dict == clean."""
    out = {}
    for name, rx in (("unicode_tag", UNICODE_TAG_RE), ("zero_width", INVISIBLE_RE), ("bidi", BIDI_RE)):
        n = len(rx.findall(text))
        if n:
            out[name] = n
    return out


def decode_unicode_tags(text: str) -> str:
    """Reveal a Unicode-tag smuggled string (U+E0020..E007E map to ASCII 0x20..0x7E)."""
    return "".join(chr(ord(c) - 0xE0000) for c in UNICODE_TAG_RE.findall(text) if 0xE0020 <= ord(c) <= 0xE007E)


def _f(asi: str, severity: str, cwe: str, evidence: str, ref: str | None = None) -> dict[str, Any]:
    return {"asi": asi, "title": ASI[asi], "severity": severity, "cwe": cwe, "evidence": evidence, "ref": ref}


def rule_new_dependency(record: dict[str, Any], *_: Any) -> list[dict[str, Any]]:
    return [
        _f("ASI04", "low", "CWE-829", f"agent added dependency {d['name']}@{d.get('version')} ({d.get('registry', 'npm')})", f"{d['name']}@{d.get('version')}")
        for d in record.get("added_deps", [])
    ]


def rule_external_read(record: dict[str, Any], *_: Any) -> list[dict[str, Any]]:
    return [
        _f("ASI01", "informational", "CWE-829", f"agent read external content via {r['kind']}: {r['ref']}", r["ref"])
        for r in record.get("read", []) if r.get("kind") in ("url", "mcp")
    ]


def rule_commands(record: dict[str, Any], *_: Any) -> list[dict[str, Any]]:
    cmds = record.get("commands", [])
    if not cmds:
        return []
    return [_f("ASI05", "informational", "CWE-94", f"agent executed {len(cmds)} shell command(s): " + "; ".join(cmds[:5]))]


def rule_agent_config_changed(record: dict[str, Any], changed_files: list[str], *_: Any) -> list[dict[str, Any]]:
    return [
        _f("ASI01", "medium", "CWE-829", f"agent configuration file changed in this commit: {p}", p)
        for p in changed_files if AGENT_CONFIG_RE.search(p)
    ]


def rule_hidden_text(record: dict[str, Any], changed_files: list[str], read_texts: dict[str, str]) -> list[dict[str, Any]]:
    out = []
    for ref, text in read_texts.items():
        hidden = has_hidden_text(text)
        if not hidden:
            continue
        decoded = decode_unicode_tags(text)
        ev = f"invisible characters in content the agent read ({', '.join(f'{k}={v}' for k, v in hidden.items())})"
        if decoded:
            ev += f'; decoded Unicode-tag text: "{decoded[:300]}"'
        out.append(_f("ASI01", "high", "CWE-506", ev, ref))
    return out


def rule_secrets_touched(record: dict[str, Any], changed_files: list[str], *_: Any) -> list[dict[str, Any]]:
    paths = [r["ref"] for r in record.get("read", []) if r.get("kind") == "file"] + list(record.get("wrote", [])) + list(changed_files)
    return [_f("ASI03", "medium", "CWE-200", f"secret or credential file touched: {p}", p) for p in sorted(set(paths)) if SECRET_PATH_RE.search(p)]


RULES = [rule_new_dependency, rule_external_read, rule_commands, rule_agent_config_changed, rule_hidden_text, rule_secrets_touched]


def run(record: dict[str, Any], changed_files: list[str] | None = None, read_texts: dict[str, str] | None = None) -> list[dict[str, Any]]:
    """Apply every rule. Returns findings sorted by severity (highest first) then ASI code."""
    changed_files = changed_files or []
    read_texts = read_texts or {}
    findings = [f for rule in RULES for f in rule(record, changed_files, read_texts)]
    findings.sort(key=lambda f: (-SEVERITIES.index(f["severity"]), f["asi"]))
    return findings


def needs_review(findings: list[dict[str, Any]]) -> bool:
    """Bob is asked to write evidence only when something fired."""
    return bool(findings)
