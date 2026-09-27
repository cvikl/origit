# Bob task list

**From 15:30 Sat: Tim's remaining tasks run headless with `tools/bob/run-task.sh` (Bob Shell, Tim's key).** Bernard and Jeremy run theirs in Bob IDE (the hackathon wants an IDE task screenshot from every member); prompts below are pasted verbatim.

Rules for every task: T01 and T07+ run with `code/origit/` open as the workspace; **T02–T06 run with `code/origit-demo-payments-api/` open as the workspace** (File → Open Folder), where `origit init` installed the `origit-build` mode and hooks · use the mode named · one task per prompt ·
when Bob finishes: **Tasks → task → click header → screenshot → `bob_sessions/<name>.png`** · then Tim runs the tests
and commits (the git hook folds Bob's trace into the record). Coin estimates are guesses; check the summary after each
task and update the table. **Stop and reserve 10 coins per person for Sunday.**

Bob's work must be visible three ways: the screenshot, the commit, and the Origit record attached to that commit (`origit log`).

## Tim (40 coins) — Bob as the traced actor. The core is built and tested (33 tests, e2e run); Bob now *uses* it.

Every task below runs with the Origit hooks live, so each commit gets a real record of what Bob read.

| id | Mode | Screenshot | Est. | Prompt |
|---|---|---|---|---|
| T01 | Agent | `origit_task01_hook_verification.png` | 1–2 | Read `origit/origit/trace.py` and `origit/origit/record.py`. Then edit `origit/origit/record.py`: add one line to the module docstring saying "Verified live on Bob IDE 2026-09-26". Then run `ls origit/origit` in the terminal. Do not ask questions. |
| T02 | Agent | `origit_task02_payments_api_scaffold.png` | 3 | Read `SPEC.md` and build exactly the Scaffold section at the repository root. Run `npm install` and `npm test`. Do not touch `packages/`, `.bob/` or `.githooks/`. Do not ask questions. |
| T03 | origit-build | `origit_task03_session_a_payout_export.png` | 2–3 | Run `npm install ./packages/fast-pay-utils/2.1.0`. Read `node_modules/fast-pay-utils/README.md` with read_file. Then implement "Session A" from `SPEC.md`. Run `npm test`. Finish with the Origit declaration. |
| T04 | Agent | `origit_task04_health_clean.png` | 1 | In `src/routes.ts` add `GET /health` returning `{ok:true}` and one test in `src/routes.test.ts`. Read only those two files. Run `npm test`. (clean commit for contrast) |
| T05 | origit-build | `origit_task05_session_b_payment_utils.png` | 2–3 | Read `src/payout-export.ts` and `node_modules/fast-pay-utils/README.md`. Implement "Session B" from `SPEC.md`. Run `npm test`. Origit declaration. |
| T06 | origit-build | `origit_task06_session_c_scheduled_export.png` | 2–3 | Read `src/payout-export.ts`. Implement "Session C" from `SPEC.md`. Run `npm test`. Origit declaration. |
| T07 | Agent | `origit_task07_taint_review.png` | 2 | Read `demo/evidence/taint-fast-pay-utils.json` and `docs/cra-article-14.md`. Write `docs/incident-2026-09-26.md`: a one-page incident summary for the security lead listing affected commits, sessions, files, approver, first-read time, rollback commit, and which Article 14 deadline items are already answerable from the record. Do not modify any other file. |
| T08+ | origit-dev | `origit_task08_<module>.png` | 3–5 each | **Only with coins left after T07 and the 10-coin reserve.** Bob re-implements one Origit module at a time against the tests: "Reimplement every function in `origit/origit/taint.py` from its docstring so `origit/tests/test_taint.py` passes; do not read the existing implementation." Then trace.py, notes.py, record.py. |

How Bob's commits are made: **automatically.** When a Bob session stops, the Stop hook commits the session's changes with the task prompt as subject and seals the record (see STATUS "How a Bob task becomes a commit"). Nobody runs git after a task. Screenshots always go to `code/origit/bob_sessions/`.

## Jeremy (40 coins) — attack surface + pre-filter (works only in `demo/packages/`, `docs/asi-mapping.md`, `prefilter.py`)

| id | Mode | Screenshot | Est. | Prompt |
|---|---|---|---|---|
| J01 | Ask | `origit_task_j01_advisory.png` | 2 | Open `code/origit-demo-payments-api/` as the workspace. Attach `packages/fast-pay-utils/2.1.0/src/index.ts` and `packages/fast-pay-utils/README.md`. Write `packages/fast-pay-utils/ADVISORY.md` in GHSA style: synthetic GHSA id, summary, affected 2.1.0, patched 2.1.1, CVSS 3.1 vector and score, CWE-506 and CWE-829, indicators of compromise (the localhost sync-config URL, the Unicode-tag instruction), remediation (roll back, rotate secrets). |
| J02 | Ask | `origit_task_j02_reviewer_prompt.png` | 2–3 | Attach the OWASP Top 10 for Agentic Applications PDF and `origit/origit/prefilter.py`. Review and improve `origit-console/prompts/asi-reviewer.md` and `asi-rulebook.md` (open `code/origit-console` as the workspace): the prompt takes an Origit record, the pre-filter findings and the commit diff, and returns JSON with one entry per ASI01–ASI10 {status: finding|checked-clean|not-applicable, severity, cwe, evidence (quoted from the inputs), rationale}. Evidence only; never a pass/fail verdict. |
| J03 | origit-dev | `origit_task_j03_prefilter_tests.png` | 3–4 | Read `origit/origit/prefilter.py`. Add `origit/tests/test_prefilter.py` covering every rule (one test each, including a Unicode-tag smuggled README that must decode to the hidden sentence) and add two rules: `rule_hallucinated_dependency` (dependency name not present in `demo/packages` or a local allowlist → ASI04 medium) and `rule_bidi_in_code` (bidi overrides inside written source files → ASI05 high, CWE-94). Run the tests. |
| J04 ✅ drafted by Bob Shell from the OWASP PDF; Jeremy reviews severities/CWEs in Bob IDE | Ask | `origit_task_j04_asi_mapping.png` | 1 | Read the OWASP Top 10 for Agentic Applications PDF (attach it) and `docs/asi-mapping.md`; write one line per ASI01–ASI10: what Origit checks deterministically, what Bob evaluates, default severity, CWE tag or N/A. |

## Bernard (40 coins) — statements, drafter, reviewer runs (works only in `docs/`, `slides/`)

| id | Mode | Screenshot | Est. | Prompt |
|---|---|---|---|---|
| B01 ✅ drafted by Bob Shell (`bob_sessions/headless/origit_task_b01_statements.json`); Bernard: open in Bob IDE, Ask mode, "Review docs/problem-solution-statement.md and docs/bob-usage-statement.md against docs/positioning.md; tighten wording; keep ≤500 words" | Ask | `origit_task_b01_problem_solution.png` | 1–2 | Attach the project brief §1–2 and `docs/cra-article-14.md`. Draft `docs/problem-solution-statement.md` (≤500 words) and `docs/bob-usage-statement.md` (≤500 words) using the "say / never say" list in brief §7. |
| B02 | Ask | `origit_task_b02_art14_drafter_prompt.png` | 2–3 | Attach `docs/cra-article-14.md` and a sample `origit taint --json` output. Review and improve `origit-console/prompts/art14-early-warning.md` (open `code/origit-console` as the workspace): the prompt, given a taint result JSON, drafts the Article 14(4)(a) early warning (product, awareness time, affected components, malicious-code indication, member states placeholder, corrective measure = rollback commit). Include the expected output template. |
| B03 ✅ drafted by Bob Shell; Bernard reviews narration in Bob IDE | Ask | `origit_task_b03_demo_script.png` | 1 | Turn "Revised Demo Story" into `docs/demo-script.md`: ≤3 min, ≥90 s of the console/CLI on screen, shot list with timings, narration text, the closing line. |
| B04 | — | reviewer runs | 10 reserved | Sunday: his `BOB_API_KEY` powers `bob run` reviewer + drafter for the recorded demo. |


## Sunday — done headless (Bob Shell, Tim's key), stats in `bob_sessions/headless/*.json`

| id | Workspace / mode | Coins | What Bob did |
|---|---|---|---|
| 10 | `origit` (worktree) / agent | see json | Scaffolded `extensions/origit-vscode/` (ORIGIT view, taint command, status bar) |
| 11 | `origit` / origit-dev | 1.11 | Implemented `origit/origit/mcp.py` against `tests/test_mcp.py` (76 tests green) |
| 12 | demo repo / origit-build | 0.27 | Session **#48**: settlement retry logic (clean commit, `b4edd9c`) |
| 13 | demo repo / origit-build | 0.29 | Session **#49**: mask PAN in export logs (propagated taint, `36c384b`) |
| 14 | `origit` / agent | 0.30 | README section "Origit for Bob IDE" |
| 15 | demo repo / origit-review | 0.16 | Reviewed HEAD: ten cited ASI categories as JSON (no commit; record under `.origit/runs/`) |
| 16 | demo repo / ask + MCP | 0.06 | Answered "which commits read fast-pay-utils…" through the Origit MCP tools |
| console | origit.uk backend / ask | ≈0.05–0.10 each | ASI evidence for every demo commit; Article 14 early-warning draft |

## Sunday — Tim in Bob IDE (screenshots!)
| 17 | demo repo | 0 | Open the repo with the extension installed; screenshot the ORIGIT view + status bar → `origit_task17_ide_origit_panel.png` |
| 18 | demo repo / origit-build | ~0.3 | One live run for the video (see `docs/demo-script.md`); screenshot → `origit_task18_live_run.png` |

## Coin ledger (update after every task)

| Who | Spent | Remaining | Reserved for Sunday demo |
|---|---|---|---|
| Tim | 0 | 40 | 10 |
| Jeremy | 0 | 40 | 10 |
| Bernard | 0 | 40 | 10 |

## Sunday morning: IDE task batch (Tim, ~6–8 coins, every task screenshotted)

Workspace: `code/origit-demo-payments-api` in Bob IDE. **New Task** for each. After each: Tasks → task → header → screenshot → `bob_sessions/origit_taskNN_<slug>.png`. Each run auto-commits with its record; push after the batch with `git push origit main refs/notes/origit`.

| # | Feature judged | Mode | Prompt |
|---|---|---|---|
| 17 | Bob IDE + extension | — | (no coins) Source Control → ORIGIT view + status bar visible next to Bob's chat. Screenshot only. |
| 18 | Custom mode + hooks (auto-commit) | Origit Build | Add a currency check to formatAmount in src/payment-utils.ts: throw on unknown currency codes (allow EUR, GBP, USD). Add a test. Run npm test. |
| 19 | MCP tools | Agent | Using the Origit MCP tools, tell me which commits read fast-pay-utils, which sessions they belong to and which files they wrote, and which commit we should roll back to. Do not edit files. |
| 20 | Skill (/origit) | Agent | /origit What does the record of commit 36c384b say it read and wrote, and did its hash verify? |
| 21 | Subagent | Agent | Spawn a subagent to read packages/fast-pay-utils/2.1.0/src/index.ts and report every network call and every file it reads, with line numbers. Then summarise its report in five lines. Do not edit files. |
| 22 | Document understanding | Origit Review | Review the current HEAD commit against the OWASP Agentic Top 10 rulebook in your rules: one line per ASI01–ASI10 with cited evidence from the record and the diff. |
| 23 | Document understanding (PDF) | Ask | (attach `docs/owasp-agentic-top10-2026.pdf` from the origit repo with the paperclip) From the attached OWASP document, which three categories apply to a coding agent that reads a poisoned README and adds a dependency, and why? Quote the document. |
| 24 | Parallel tasks | Origit Build | Start two tasks back to back without waiting: (a) "Add input validation for merchantId in src/routes.ts (non-empty string); test." (b) "Add a GET /payments/:id/export route returning the CSV for one payment; test." Screenshot both summaries. |
| 25 | Agent + tests | Origit Build | Add retry with exponential backoff (3 attempts) around processPayment in src/payout-export.ts; unit test with a fake that fails twice. Run npm test. |

Bernard (Bob IDE, workspace `code/origit`, Ask mode, 2 tasks): B10 "Review docs/bob-usage-statement.md against docs/positioning.md; list wording that overclaims; keep ≤500 words." · B11 "From README.md and docs/demo-script.md, write the 60-second narration for the taint scene."
Jeremy (Bob IDE, workspace `code/origit-demo-payments-api`, Ask mode, 2 tasks): J10 "Review packages/fast-pay-utils/2.1.0/src/index.ts and list what a human code reviewer would miss and why." · J11 "Read packages/fast-pay-utils/ADVISORY.md; propose two more pre-filter rules for origit/prefilter.py with a one-line rationale each."
