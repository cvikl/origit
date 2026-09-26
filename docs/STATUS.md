# Origit — STATUS (read this first, all time zones)

Deadline: **Sun 27 Sep 2026 16:00 BST (15:00 UTC)** · form complete by 14:00 BST. HK = BST+7.
Bobcoins: 40 per person, no top-ups. Reserve 10 each for the recorded demo run. Screenshot **every** Bob task into `bob_sessions/` immediately.
Never commit `.env` or any key file. `.gitignore` covers `.env`, `bob-*.json`, `apikey*`.

## Now (Sat 26 Sep, 12:45 BST)

| # | Task | Owner | Coins | State |
|---|---|---|---|---|
| 1 | Repo layout, LICENSE, .gitignore, .env.example, README | Claude | 0 | ✅ |
| 2 | **Origit core**: record/hash, trace fold, git notes, taint engine, pre-filter, CLI (init/trace/record/log/show/taint/export/prefilter), git hooks — 33 tests green, e2e run green (taint in 0.17 s) | Claude | 0 | ✅ |
| 3 | Bob config in repo: modes `origit-dev`/`origit-build`, rules, hooks, AGENTS.md; Bob IDE 2.2.0 installed, modes visible | Tim + Claude | 0 | ✅ |
| 4 | Jeremy's tainted `fast-pay-utils@2.1.0` integrated (`demo/packages/`), compiled `dist/`, clean 2.0.0 with same API | Jeremy + Claude | 0 | ✅ |
| 5 | T01 hook verification in Bob IDE: **NATIVE** (17 events, session id + paths present, 0.28 coins) | Tim | 0.3 | ✅ |
| 6 | T02 demo scaffold, T03–T06 traced Bob sessions + clean commit, T07 incident summary | Tim (Bob) | ~12–15 | Sat pm |
| 7 | J01 advisory, J02 reviewer prompt, J03 prefilter tests + rules | Jeremy (Bob) | ~8 | Sat night HK |
| 8 | B01 statements, B02 Art.14 drafter prompt, B03 demo script | Bernard (Bob) | ~7 | Sat |
| 9 | Console: backend (notes → JSON, prefilter, `bob run` reviewer + drafter), frontend, deploy | Tim + Claude (+ Bob for frontend) | ~5–10 | Sun 08–12 |
| 10 | Video, slides, submit | all | 10 reserved each | Sun 12–14 |

## Commit recipe (Tim, after every Bob task)
```bash
cd ~/Documents/bcco/code/origit-demo-payments-api
npm test
git add -A
ORIGIT_MODE=origit-build ORIGIT_TESTS='{"run":true,"passed":N,"failed":0}' git commit -m "feat: <what Bob did> [bob task NN]"
origit log | head -3      # the new commit must show actor bob-ide and Bob's task id as session
```
`origit` must be on PATH: `export PATH=~/Documents/bcco/code/origit/origit/.venv/bin:$PATH` (the git hooks find it anyway).
Approver is preset in that repo via `git config origit.approver bernard`.

## Decisions
- **Two repos (decided 13:10 Sat).** `code/origit` = product + submission. `code/origit-demo-payments-api` = the fintech's repo Bob works in (own `.bob` from `origit init`, vendored `packages/fast-pay-utils`), linked into the product repo as submodule `demo/payments-api`. Reason: the story is "a fintech installs Origit into *their* repo"; taint results and the console stay free of Origit's own commits. `demo/evidence/` in the product repo holds committed `origit export` / taint snapshots for judges who do not init submodules.
- `fast-pay-utils` is installed as a local `file:` dependency; `record fold` derives `added_deps` from the package.json diff.
- **Claude builds the deterministic core; Bob is the traced actor, reviewer and drafter.** Decided 12:30 Sat after debate: judges score Bob's use *in the solution*; coins go to the demo sessions first. If coins remain after the demo, Bob re-implements modules against the tests (T08+).
- Jeremy's 2.1.0 runs its exfil at import time, to localhost only. Acceptable for the demo; the video says "never leaves the machine". Claude does glue, fixes, deploy and docs plumbing (zero coins, no judging credit needed).
- **Tracing is native via Bob IDE lifecycle hooks — verified live 26 Sep 12:35.** Real payload keys differ from the docs: `hook_event_name`, `tool_name`, `tool_input`, `tool_response`, plus `cwd`, `tool_use_id`, and `last_assistant_message` on Stop (Bob's own summary — candidate for the console). `trace.unwrap` accepts both schemas. Docs said tools: `read_file, glob, grep, list_files, write_file, apply_diff, insert_content, search_and_replace, execute_command, spawn_subagent …`). Watcher fallback only if live verification fails.
- Reviewer/drafter = **Bob Shell** from the console backend: `curl -fsSL https://bob.ibm.com/download/bobshell.sh | bash` (needs Node ≥24; this machine has 22 → upgrade via nvm), auth via `BOB_API_KEY` env (key with *Inference* scope from the Bob web portal), call `bob run --format json --max-cost 0.5 --max-turns 6 --workspace <repo> "<prompt> @path"`. All tools are pre-approved in `run`, so the reviewer prompt must be read-only by instruction and the workspace a throwaway copy.
- Record is canonical JSON: sorted keys, compact, UTF-8; `read/wrote/added_deps` are sets; `commands` ordered; hash excludes itself. Schema `origit/record/v1`.
- Storage: `refs/notes/origit`, one note per commit. Every commit gets a record (human commits marked `actor: human`); agent commits without a trace are refused.

## Dev notes
- Tests: `cd origit && env -u PYTHONPATH PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -q` (Tim's machine has ROS on PYTHONPATH which breaks plain pytest).

## Blocked
- Nothing yet. Waiting on hook verification output from Tim.

## Ownership fences (avoid overwrites)
- Jeremy: `demo/packages/`, `docs/asi-mapping.md`, rules inside `origit/origit/prefilter.py`.
- Bernard: `docs/`, `slides/`.
- Tim/Claude: everything else.
