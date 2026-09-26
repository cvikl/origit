#!/bin/sh
# Run one Bob task headless (Bob Shell) inside a workspace, with Origit hooks tracing it.
# usage: tools/bob/run-task.sh <workspace> <mode> <task-slug> "<prompt>"
# Output: prints Bob's final message; writes bob_sessions/<task-slug>.json with the run stats (task id, cost, duration).
set -e
WS=$1; MODE=$2; SLUG=$3; PROMPT=$4
HERE=$(cd "$(dirname "$0")/../.." && pwd)
export PATH="$HOME/.nvm/versions/node/v24.21.0/bin:$PATH"
export CHOKIDAR_USEPOLLING=1 CHOKIDAR_INTERVAL=2000
[ -n "$BOB_API_KEY" ] || export BOB_API_KEY=$(python3 -c "import json,os; print(json.load(open(os.path.expanduser('~/Downloads/bob-tim.json')))['apikey'])")
OUT="$HERE/bob_sessions/$SLUG.json"
cd "$WS"
bob run --format json --mode "$MODE" --max-cost "${BOB_MAX_COST:-1.5}" --max-turns "${BOB_MAX_TURNS:-30}" \
  --workspace "$WS" --disable-mcp --disable-subagents --accept-license --trust --log-level error "$PROMPT" < /dev/null > "$OUT.raw" 2> "$OUT.err" || true
python3 - "$OUT" <<'PY'
import json, sys
out = sys.argv[1]
raw = open(out + ".raw").read()
try:
    env = json.loads(raw[raw.index("{"):])
except Exception:
    env = {"status": "no-result (run ended without a result event: max-turns or max-cost reached, or crash; see .err)", "raw": raw[-3000:]}
rec = {"task": out.rsplit("/", 1)[1][:-5], "status": env.get("status"), "stats": env.get("stats"), "last_message": env.get("last_message")}
json.dump(rec, open(out, "w"), indent=2, ensure_ascii=False)
print(f"[bob] status={rec['status']} task_id={(rec['stats'] or {}).get('task_id')} cost={(rec['stats'] or {}).get('session_costs')} coins duration={(rec['stats'] or {}).get('duration_ms')} ms tool_calls={(rec['stats'] or {}).get('tool_calls')}")
print(rec["last_message"] or open(out + ".err").read()[-2000:])
PY
[ -s "$OUT.raw" ] && grep -q '"type":"result"' "$OUT.raw" && rm -f "$OUT.raw" "$OUT.err" || true
