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
| 5b | Commits: T01 as bob-ide record (ec815d5), two-repo split, submodule `demo/payments-api` | Claude | 0 | ✅ |
| 6a | T02 scaffold (a5f55e9) and T03 session A (payout export, 8 tests) — both run from the wrong workspace as follow-ups of T01; recovered by re-rooting files + trace. Coins so far: 2.61 on one task id | Tim (Bob) + Claude | 2.6 | ✅ |
| 6b | T04 clean commit (34cc007, own task id, 0.13) ✅ · T05 session B (73578a4, 0.65) ✅ — **Bob committed by itself** via `git commit`; hooks still folded the trace, so the record has the README read and 4 writes, but no test count/mode (recipe env not set) · **T06 session C** next | Tim (Bob) | ~3 | ⏳ |
| 6c | T07 incident summary | Tim (Bob) | 2 | after 6b |
| 7 | J01 advisory, J02 reviewer prompt, J03 prefilter tests + rules | Jeremy (Bob) | ~8 | Sat night HK |
| 8 | B01 statements, B02 Art.14 drafter prompt, B03 demo script | Bernard (Bob) | ~7 | Sat |
| 9 | Console: **built in the separate `origit-console` repo by Tim's other Claude session** (FastAPI, hosted at origit.uk, vendors this core as `vendor/origit`). This repo only points to it (`console/README.md`). A duplicate stdlib console was built here by mistake and removed (history: 774dae3). Remaining: bump `vendor/origit` to latest core, cached Bob evidence for the demo commits, deploy | Tim (other session) | ~5–10 | Sat/Sun |
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
- **Console = `code/origit-console` (other Claude session), not `code/origit/console/`.** Its prompts (`prompts/asi-reviewer.md`, `asi-rulebook.md`, `art14-early-warning.md`) are the ones Jeremy/Bernard review. Bob Shell 2.0.5 is installed here under nvm Node 24 (`~/.nvm/versions/node/v24.21.0/bin/bob`); headless runs on Tim's laptop need `CHOKIDAR_USEPOLLING=1 CHOKIDAR_INTERVAL=2000` in the environment (inotify instances exhausted: 149/128), or `sudo sysctl fs.inotify.max_user_instances=1024`. Verified 15:11: one-turn ask = 3 s, 0.009 coins; envelope `{type:result,status,stats{session_costs,…},last_message}`.
- **Two repos (decided 13:10 Sat).** `code/origit` = product + submission. `code/origit-demo-payments-api` = the fintech's repo Bob works in (own `.bob` from `origit init`, vendored `packages/fast-pay-utils`), linked into the product repo as submodule `demo/payments-api`. Reason: the story is "a fintech installs Origit into *their* repo"; taint results and the console stay free of Origit's own commits. `demo/evidence/` in the product repo holds committed `origit export` / taint snapshots for judges who do not init submodules.
- `fast-pay-utils` is installed as a local `file:` dependency; `record fold` derives `added_deps` from the package.json diff.
- **Claude builds the deterministic core; Bob is the traced actor, reviewer and drafter.** Decided 12:30 Sat after debate: judges score Bob's use *in the solution*; coins go to the demo sessions first. If coins remain after the demo, Bob re-implements modules against the tests (T08+).
- Jeremy's 2.1.0 runs its exfil at import time, to localhost only. Acceptable for the demo; the video says "never leaves the machine". Claude does glue, fixes, deploy and docs plumbing (zero coins, no judging credit needed).
- **Tracing is native via Bob IDE lifecycle hooks — verified live 26 Sep 12:35.** Real payload keys differ from the docs: `hook_event_name`, `tool_name`, `tool_input`, `tool_response`, plus `cwd`, `tool_use_id`, and `last_assistant_message` on Stop (Bob's own summary — candidate for the console). `trace.unwrap` accepts both schemas. Docs said tools: `read_file, glob, grep, list_files, write_file, apply_diff, insert_content, search_and_replace, execute_command, spawn_subagent …`). Watcher fallback only if live verification fails.
- Reviewer/drafter = **Bob Shell** from the console backend: `curl -fsSL https://bob.ibm.com/download/bobshell.sh | bash` (needs Node ≥24; this machine has 22 → upgrade via nvm), auth via `BOB_API_KEY` env (key with *Inference* scope from the Bob web portal), call `bob run --format json --max-cost 0.5 --max-turns 6 --workspace <repo> "<prompt> @path"`. All tools are pre-approved in `run`, so the reviewer prompt must be read-only by instruction and the workspace a throwaway copy.
- Record is canonical JSON: sorted keys, compact, UTF-8; `read/wrote/added_deps` are sets; `commands` ordered; hash excludes itself. Schema `origit/record/v1`.
- Storage: `refs/notes/origit`, one note per commit. Every commit gets a record (human commits marked `actor: human`); agent commits without a trace are refused.

## Dev notes
- T02 was run as a follow-up inside the T01 task with `code/origit` open, so Bob wrote into the submodule checkout and the trace landed in the origit repo. Claude moved the files and re-rooted the trace paths (`_rerooted_from` marker on each event) into `origit-demo-payments-api` before folding. From T03 on: **workspace = `origit-demo-payments-api`, and always click New Task** so each session has its own id.
- Tests: `cd origit && env -u PYTHONPATH PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -q` (Tim's machine has ROS on PYTHONPATH which breaks plain pytest).

## Observations for the video
- In session B Bob ran `git add … && git commit` on its own despite the rule not to. Origit's pre-commit hook folded the trace anyway and the record is attached: **the agent cannot bypass the record by committing itself.** Say this in the video.
- In session A Bob **noticed** the Unicode-tag instruction and the import-time exfil on its own, said so in its summary, did not call `initializeTelemetry`, and mocked the library in tests. Origit still records the read and the dependency, and `origit taint` lights the commit. Narrative: the agent being careful is not evidence; the record is. Bob also wrote `node_modules/fast-pay-utils/dist/index.d.ts`, which npm symlinks into the vendored package — a real example of an agent writing into a dependency.

## Blocked
- Nothing yet. Waiting on hook verification output from Tim.

## Ownership fences (avoid overwrites)
- Jeremy: `demo/packages/`, `docs/asi-mapping.md`, rules inside `origit/origit/prefilter.py`.
- Bernard: `docs/`, `slides/`.
- Tim/Claude: everything else.
