#!/bin/sh
# Origit session commit — Bob Stop hook. One agent session = one commit = one sealed record.
# Enabled per repo with: git config origit.autocommit true   (origit init sets it)
top=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
for c in "$ORIGIT_BIN" "$(git config --get origit.bin 2>/dev/null)" "$(command -v origit 2>/dev/null)" "$top/origit/.venv/bin/origit" "$top/.venv/bin/origit"; do
  if [ -n "$c" ] && [ -x "$c" ]; then "$c" session-commit --root . 2>>.origit/hook-errors.log; exit 0; fi
done
exit 0
