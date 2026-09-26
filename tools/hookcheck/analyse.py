#!/usr/bin/env python3
"""Analyse .origit/trace.jsonl from the hook-verification session. Run from the workspace root:
    python3 tools/hookcheck/analyse.py [path/to/.origit/trace.jsonl]
Prints a verdict: NATIVE (hooks carry read paths + session_id) or WATCHER (fall back to inotify)."""
import json, sys
from collections import Counter

p = sys.argv[1] if len(sys.argv) > 1 else ".origit/trace.jsonl"
events = []
for line in open(p, encoding="utf-8"):
    line = line.strip()
    if not line:
        continue
    try:
        o = json.loads(line)
    except json.JSONDecodeError:
        print("UNPARSED:", line[:200]); continue
    raw = o.get("raw", o)
    if isinstance(raw, dict):
        raw = dict(raw); raw["ts"] = o.get("ts")
        raw.setdefault("event", raw.get("hook_event_name")); raw.setdefault("tool", raw.get("tool_name")); raw.setdefault("input", raw.get("tool_input"))
        events.append(raw)
    else:
        print("RAW-NOT-JSON:", str(raw)[:200])

by_event = Counter(e.get("event") for e in events)
tools = Counter(e.get("tool") for e in events if e.get("tool"))
missing_sid = [e for e in events if e.get("tool") and not e.get("session_id")]
keys = {}
for e in events:
    if e.get("tool") and isinstance(e.get("input"), dict):
        keys.setdefault(e["tool"], set()).update(e["input"].keys())
read_like = [t for t in tools if any(k in t.lower() for k in ("read", "list", "search", "glob", "grep", "symbol"))]
with_path = [t for t in read_like if keys.get(t, set()) & {"path", "paths", "file", "files", "args"}]
verdict = "NATIVE" if with_path and not missing_sid and by_event.get("PostToolUse") else "WATCHER"
print(json.dumps({
    "events_total": len(events), "by_event": dict(by_event), "tools": dict(tools),
    "sessions": sorted({e.get("session_id") for e in events if e.get("session_id")}),
    "tool_events_missing_session_id": len(missing_sid),
    "input_keys_by_tool": {k: sorted(v) for k, v in keys.items()},
    "read_like_tools_with_path": with_path, "VERDICT": verdict,
    "first_3_events": events[:3],
}, indent=2, ensure_ascii=False))
