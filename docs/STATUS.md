# Origit — STATUS (read this first, all time zones)

Deadline: **Sun 27 Sep 2026 16:00 BST (15:00 UTC)** · everything recorded and submitted by **14:30 BST**. HK = BST+7.
Bobcoins: ~37 left on Tim's account (only Tim's key is on this machine). Reserve 8. Screenshot **every** Bob IDE task into `bob_sessions/`.
Never commit `.env` or any key file.

## Final-day plan (started Sun 02:05 BST, Claude working unattended while Tim sleeps)

Split: **A** core session manager (Claude) · **B** Bob IDE extension (Bob Shell builds, Claude reviews and packages) · **C** Business plan: Bob Review on push + real Art. 14 draft (Claude wires, Bob runs) · **D** Bob usage log (every Bob run → `bob_sessions/*.json`; IDE PNGs need humans) · **E** consistency + submission package.

1. A: `origit session start` / `run start` / `trace` / `run end` (auto-commit, `bob: <prompt> [session #n run m]`), human edits between runs committed as `actor: human`, session display ids `#42…` stored in the record, `origit log --json` grouped by session/run, `show --json`, `init` writes hooks + `mcp.json` + `/origit` skill + `origit-review` mode. Tests.
2. B: Bob Shell scaffolds `extensions/origit-vscode/` (ORIGIT view in Source Control, `Origit: Taint…`, status bar) in a git worktree; packaged to `.vsix`; installed into Bob IDE from the CLI if it accepts it. **Tim: open the demo repo in Bob IDE and screenshot the panel** (video opener).
3. C: review runs automatically on every push (post-receive → background Bob run per new commit with a record); `POST …/draft-art14` calls Bob for real; evidence cached and seeded; demo repo switched to the Business plan; landing numbers computed from the real repo.
4. D: Bob writes the MCP server (`origit mcp`), the `/origit` skill, the README Bob-IDE section; Bob runs two more traced sessions in the demo repo; Bob reviews every demo commit; Bob drafts Art. 14; Bob answers a taint question over the Origit MCP. Stats for each run in `bob_sessions/`.
5. E: console fixes, `docs/deck-fixes.md` for Bernard, `docs/demo-script.md` re-cut to the new flow, statements checked against the code, `docs/bob-usage-statement.md` rewritten from what actually happened, secrets scan, push.

Progress is logged below under **Log (Sunday)**; the task table is kept current.

## Log (Sunday)
- 02:55 **Track A done.** `origit session start / run start / trace / run end`, human edits committed as `human:` between runs, display ids `#42…` in every new record (`.origit/config.json` sets the base), `origit log` grouped by session/run (`--json`), `show/taint --json`, `init` installs `origit-review` mode + `mcp.json` + `/origit` skill. 76 core tests green. Proven live with Bob Shell in the demo repo: sessions **#48** (retry logic, clean) and **#49** (mask PAN in logs, propagated taint) auto-committed with `[session #n run 1]`, tests 26/26 and 32/32 parsed into the records; a no-change run (#50, review mode) stored its record under `.origit/runs/`.
- 02:55 **Bob built** (Bob Shell, stats in `bob_sessions/*.json`): MCP server `origit mcp` (task 11, 1.11 coins, 76 tests green), README "Origit for Bob IDE" (task 14, 0.30), demo sessions #48/#49 (tasks 12–13, 0.27 + 0.29), `origit-review` mode run on HEAD (task 15, 0.16: ten cited categories), VS Code extension (task 10, in progress).
- 02:55 **Console** (origit-console `ff67c45`): Bob Review on push (post-receive → background `bob run` per new commit), `review-all` + `review-status` endpoints, session labels everywhere, taint "also touched" split, honest Bob pill, real landing numbers, Business wording, seed script; 21 backend tests green. **Not deployed: the deploy command is blocked for Claude in auto mode (production deploy). Tim runs it, see "Tim's morning checklist".**
- 02:55 Reviews of all demo commits + the Art. 14 draft are being produced locally through the console (Tim's key) and shipped as `seed/` so the deployed console shows them immediately.
- 02:05 Plan written. Baseline: core 61 tests green; demo repo 23 Jest tests green; console live at origit.uk (13 commits, 12 records, plan=free, Bob key not configured on the server).

## Now (Sat 26 Sep, 12:45 BST)

| # | Task | Owner | Coins | State |
|---|---|---|---|---|
| 1 | Repo layout, LICENSE, .gitignore, .env.example, README | Tim | 0 | ✅ |
| 2 | **Origit core**: record/hash, trace fold, git notes, taint engine, pre-filter, CLI (init/trace/record/log/show/taint/export/prefilter), git hooks — 33 tests green, e2e run green (taint in 0.17 s) | Tim | 0 | ✅ |
| 3 | Bob config in repo: modes `origit-dev`/`origit-build`, rules, hooks, AGENTS.md; Bob IDE 2.2.0 installed, modes visible | Tim | 0 | ✅ |
| 4 | Jeremy's tainted `fast-pay-utils@2.1.0` integrated (`demo/packages/`), compiled `dist/`, clean 2.0.0 with same API | Jeremy + Tim | 0 | ✅ |
| 5 | T01 hook verification in Bob IDE: **NATIVE** (17 events, session id + paths present, 0.28 coins) | Tim | 0.3 | ✅ |
| 5b | Commits: T01 as bob-ide record (43ca0d0), two-repo split, submodule `demo/payments-api` | Tim | 0 | ✅ |
| 6a | T02 scaffold (17c436c) and T03 session A (payout export, 8 tests) — both run from the wrong workspace as follow-ups of T01; recovered by re-rooting files + trace. Coins so far: 2.61 on one task id | Tim (Bob) | 2.6 | ✅ |
| 6b | T04 clean commit (3ccfc39, own task id, 0.13) ✅ · T05 session B (d8f549f, 0.65) ✅ — **Bob committed by itself** via `git commit`; hooks still folded the trace, so the record has the README read and 4 writes, but no test count/mode (recipe env not set) · **T06 session C** next | Tim (Bob) | ~3 | ⏳ |
| 6c | T07 incident summary (`docs/incident-2026-09-26.md`) — **run headless via Bob Shell** (`tools/bob/run-task.sh`), 50 s, 0.08 coins, hooks traced it, record on commit | Tim (Bob Shell) | 0.08 | ✅ |
| 7 | J01 advisory (demo repo d899879) ✅ and J03 prefilter tests + `dependency_not_read` rule (4eb0887, 60 tests) ✅ — drafted by Bob Shell; Jeremy reviews in Bob IDE and does J02 (console reviewer prompt) | Bob Shell → Jeremy | 0.9 | ⏳ review |
| 8 | B01 statements (499 / 433 words) ✅, B03 demo script ✅, J04 ASI mapping ✅ — drafted by Bob (Shell, Tim's key, 15:32–15:37). Bernard and Jeremy now **review these in Bob IDE** (their screenshots); B02/J02 = review the console prompts in `origit-console` | Tim (Bob Shell) → Bernard, Jeremy | see ledger | ⏳ review |
| 9 | Console: **built in the separate `origit-console` repo by Tim** (FastAPI, hosted at origit.uk, vendors this core as `vendor/origit`). This repo only points to it (`console/README.md`). A duplicate stdlib console was built here by mistake and removed (history: d997866). Remaining: bump `vendor/origit` to latest core, cached Bob evidence for the demo commits, deploy | Tim | ~5–10 | Sat/Sun |
| 10 | Video, slides, submit | all | 10 reserved each | Sun 12–14 |

## Coin ledger (Tim's account)
- IDE tasks T01–T06: 3.9 · Shell: T07 0.08, B01 (statements, 20 turns) ~8.8?, B03 0.15, J04 ~1.1 — exact figures in `bob_sessions/*.json` (`stats.session_costs`). Check the Bob web portal balance before Sunday; reserve 10.

## How a Bob task becomes a commit (current flow)
1. Run the task: in Bob IDE (workspace = the repo) or headless with `tools/bob/run-task.sh <workspace> <mode> <slug> "<prompt>"` (stats land in `bob_sessions/<slug>.json`).
2. Hooks trace the prompt and every tool call into `.origit/trace.jsonl`.
3. When Bob stops, the Stop hook runs `origit session-commit`: stages the session's changes, message = task prompt + Bob's summary, and the git hooks fold the trace into the sealed record. Nothing to do by hand. `origit log` shows the new commit as `bob-ide` with the session id.
4. Push with `git push <remote> main refs/notes/origit` (demo repo → `origit` = Hetzner/console; product repo → `origin` = GitHub).
Approver is preset per repo (`git config origit.approver`), mode per repo (`git config origit.mode`) or env `ORIGIT_MODE`.

## Decisions
- **One Bob session = one commit = one record (16:20 Sat).** Bob's Stop hook runs `origit session-commit`: stages the session's changes, writes the commit message from the task prompt and Bob's summary, and the git hooks seal the record. Enabled per repo by `git config origit.autocommit true` (set by `origit init`). Proven on the demo repo (343d6b0). Writes are the union of traced write-tool calls and files staged in the commit, so edits made through shell commands are recorded too.
- **Bob orchestration runs from the terminal via Bob Shell** (`tools/bob/run-task.sh <workspace> <mode> <slug> "<prompt>"`, 15:30 Sat). No more IDE workspace switching. Each run stores its stats (task id, coins, duration, tool calls) in `bob_sessions/<slug>.json` next to the IDE screenshots. The six IDE screenshots (T01–T06) already satisfy the IDE-evidence rule for Tim; Bernard and Jeremy still need at least one IDE task each. Bob Shell needs stdin closed (`< /dev/null`) or it hangs waiting for a piped prompt.
- **Console = `code/origit-console`, not `code/origit/console/`.** Its prompts (`prompts/asi-reviewer.md`, `asi-rulebook.md`, `art14-early-warning.md`) are the ones Jeremy/Bernard review. Bob Shell 2.0.5 is installed here under nvm Node 24 (`~/.nvm/versions/node/v24.21.0/bin/bob`); headless runs on Tim's laptop need `CHOKIDAR_USEPOLLING=1 CHOKIDAR_INTERVAL=2000` in the environment (inotify instances exhausted: 149/128), or `sudo sysctl fs.inotify.max_user_instances=1024`. Verified 15:11: one-turn ask = 3 s, 0.009 coins; envelope `{type:result,status,stats{session_costs,…},last_message}`.
- **Two repos (decided 13:10 Sat).** `code/origit` = product + submission. `code/origit-demo-payments-api` = the fintech's repo Bob works in (own `.bob` from `origit init`, vendored `packages/fast-pay-utils`), linked into the product repo as submodule `demo/payments-api`. Reason: the story is "a fintech installs Origit into *their* repo"; taint results and the console stay free of Origit's own commits. `demo/evidence/` in the product repo holds committed `origit export` / taint snapshots for judges who do not init submodules.
- `fast-pay-utils` is installed as a local `file:` dependency; `record fold` derives `added_deps` from the package.json diff.
- **The deterministic core is hand-built; Bob is the traced actor, reviewer and drafter.** Decided 12:30 Sat after debate: judges score Bob's use *in the solution*; coins go to the demo sessions first. If coins remain after the demo, Bob re-implements modules against the tests (T08+).
- Jeremy's 2.1.0 runs its exfil at import time, to localhost only. Acceptable for the demo; the video says "never leaves the machine". Glue, fixes, deploy and docs plumbing are done by hand (zero coins).
- **Tracing is native via Bob IDE lifecycle hooks — verified live 26 Sep 12:35.** Real payload keys differ from the docs: `hook_event_name`, `tool_name`, `tool_input`, `tool_response`, plus `cwd`, `tool_use_id`, and `last_assistant_message` on Stop (Bob's own summary — candidate for the console). `trace.unwrap` accepts both schemas. Docs said tools: `read_file, glob, grep, list_files, write_file, apply_diff, insert_content, search_and_replace, execute_command, spawn_subagent …`). Watcher fallback only if live verification fails.
- Reviewer/drafter = **Bob Shell** from the console backend: `curl -fsSL https://bob.ibm.com/download/bobshell.sh | bash` (needs Node ≥24; this machine has 22 → upgrade via nvm), auth via `BOB_API_KEY` env (key with *Inference* scope from the Bob web portal), call `bob run --format json --max-cost 0.5 --max-turns 6 --workspace <repo> "<prompt> @path"`. All tools are pre-approved in `run`, so the reviewer prompt must be read-only by instruction and the workspace a throwaway copy.
- Record is canonical JSON: sorted keys, compact, UTF-8; `read/wrote/added_deps` are sets; `commands` ordered; hash excludes itself. Schema `origit/record/v1`.
- Storage: `refs/notes/origit`, one note per commit. Every commit gets a record (human commits marked `actor: human`); agent commits without a trace are refused.

## Dev notes
- T02 was run as a follow-up inside the T01 task with `code/origit` open, so Bob wrote into the submodule checkout and the trace landed in the origit repo. Tim moved the files and re-rooted the trace paths (`_rerooted_from` marker on each event) into `origit-demo-payments-api` before folding. From T03 on: **workspace = `origit-demo-payments-api`, and always click New Task** so each session has its own id.
- Tests: `cd origit && env -u PYTHONPATH PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -q` (Tim's machine has ROS on PYTHONPATH which breaks plain pytest).

## Observations for the video
- In session B Bob ran `git add … && git commit` on its own despite the rule not to. Origit's pre-commit hook folded the trace anyway and the record is attached: **the agent cannot bypass the record by committing itself.** Say this in the video.
- In session A Bob **noticed** the Unicode-tag instruction and the import-time exfil on its own, said so in its summary, did not call `initializeTelemetry`, and mocked the library in tests. Origit still records the read and the dependency, and `origit taint` lights the commit. Narrative: the agent being careful is not evidence; the record is. Bob also wrote `node_modules/fast-pay-utils/dist/index.d.ts`, which npm symlinks into the vendored package — a real example of an agent writing into a dependency.

## Records and history (technical note)
- Origit records live in `refs/notes/origit`, keyed by commit sha. If history is ever rewritten (filter-branch, rebase, squash-merge), re-attach the records to the new shas with `git notes --ref=origit copy <old> <new>` (pairing old and new commits in order; trees must be identical) and push the notes ref again. `notes.rewriteRef` is set locally so amend/rebase carry notes automatically. Always push with `git push origin main refs/notes/origit`.
- GitHub: https://github.com/cvikl/origit (core, public). Demo repo remote: Hetzner bare repo (console); GitHub mirror at cvikl still to create.

## Blocked
- Nothing yet. Waiting on hook verification output from Tim.

## Ownership fences (avoid overwrites)
- Jeremy: `demo/packages/`, `docs/asi-mapping.md`, rules inside `origit/origit/prefilter.py`.
- Bernard: `docs/`, `slides/`.
- Tim: everything else.
