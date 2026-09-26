#!/bin/sh
# Origit tracer — called by Bob IDE lifecycle hooks with the event JSON on stdin.
# Appends every event to .origit/trace.jsonl. Never fails (exit 0), never blocks Bob.
mkdir -p .origit
top=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
for c in "$ORIGIT_BIN" "$(git config --get origit.bin 2>/dev/null)" "$(command -v origit 2>/dev/null)" "$top/origit/.venv/bin/origit" "$top/.venv/bin/origit"; do
  if [ -n "$c" ] && [ -x "$c" ]; then "$c" trace --root . 2>>.origit/hook-errors.log; exit 0; fi
done
printf '{"ts":"%s","raw":' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> .origit/trace.jsonl
cat >> .origit/trace.jsonl
printf '}\n' >> .origit/trace.jsonl
exit 0
