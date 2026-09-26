# Bob task list — one prompt per task, paste verbatim into Bob IDE

Rules for every task: open the **repo root** (`origit/`) as the workspace · use the mode named · one task per prompt ·
when Bob finishes: **Tasks → task → click header → screenshot → `bob_sessions/<name>.png`** · then Tim runs the tests
and commits (the git hook folds Bob's trace into the record). Coin estimates are guesses; check the summary after each
task and update the table. **Stop and reserve 10 coins per person for Sunday.**

Bob's work must be visible three ways: the screenshot, the commit, and the Origit record attached to that commit (`origit log`).

## Tim (40 coins) — Bob as the traced actor. The core is built and tested (33 tests, e2e run); Bob now *uses* it.

Every task below runs with the Origit hooks live, so each commit gets a real record of what Bob read.

| id | Mode | Screenshot | Est. | Prompt |
|---|---|---|---|---|
| T01 | Agent | `origit_task01_hook_verification.png` | 1–2 | Read `origit/origit/origit/trace.py` and `origit/origit/origit/record.py`. Then edit `origit/origit/origit/record.py`: add one line to the module docstring saying "Verified live on Bob IDE 2026-09-26". Then run `ls origit/origit/origit` in the terminal. Do not ask questions. |
| T02 | Agent | `origit_task02_payments_api_scaffold.png` | 3 | Read `demo/payments-api/SPEC.md` and build exactly the Scaffold section inside `demo/payments-api/`. Run `npm install` and `npm test` there. Touch nothing outside that folder. Do not ask questions. |
| T03 | origit-build | `origit_task03_session_a_payout_export.png` | 2–3 | Work in `demo/payments-api`. Run `npm install ../packages/fast-pay-utils/2.1.0`. Read `demo/payments-api/node_modules/fast-pay-utils/README.md` with read_file. Then implement "Session A" from `demo/payments-api/SPEC.md`. Run `npm test`. Finish with the Origit declaration. |
| T04 | Agent | `origit_task04_health_clean.png` | 1 | In `demo/payments-api/src/routes.ts` add `GET /health` returning `{ok:true}` and one test in `src/routes.test.ts`. Read only those two files. Run `npm test`. (clean commit for contrast) |
| T05 | origit-build | `origit_task05_session_b_payment_utils.png` | 2–3 | Work in `demo/payments-api`. Read `src/payout-export.ts` and `node_modules/fast-pay-utils/README.md`. Implement "Session B" from `demo/payments-api/SPEC.md`. Run `npm test`. Origit declaration. |
| T06 | origit-build | `origit_task06_session_c_scheduled_export.png` | 2–3 | Work in `demo/payments-api`. Read `src/payout-export.ts`. Implement "Session C" from `demo/payments-api/SPEC.md`. Run `npm test`. Origit declaration. |
| T07 | Agent | `origit_task07_taint_review.png` | 2 | Run `origit/.venv/bin/origit taint fast-pay-utils --json` in the terminal and read the output. Then read `docs/cra-article-14.md`. Write `docs/incident-2026-09-26.md`: a one-page incident summary for the security lead listing affected commits, sessions, files, approver, first-read time, rollback commit, and which Article 14 deadline items are already answerable from the record. Do not modify any other file. |
| T08+ | origit-dev | `origit_task08_<module>.png` | 3–5 each | **Only with coins left after T07 and the 10-coin reserve.** Bob re-implements one Origit module at a time against the tests: "Reimplement every function in `origit/origit/origit/taint.py` from its docstring so `origit/tests/test_taint.py` passes; do not read the existing implementation." Then trace.py, notes.py, record.py. |

How Bob's commits are made: after each task Tim runs the tests, then `git add` + `git commit` in the terminal with
`ORIGIT_APPROVER=bernard ORIGIT_MODE=<mode> ORIGIT_TESTS='{"run":true,"passed":N,"failed":0}'` in the environment
(see STATUS "Commit recipe"). The pre-commit hook folds Bob's trace into the record; post-commit attaches it.

## Jeremy (40 coins) — attack surface + pre-filter (works only in `demo/packages/`, `docs/asi-mapping.md`, `prefilter.py`)

| id | Mode | Screenshot | Est. | Prompt |
|---|---|---|---|---|
| J01 | Ask | `origit_task_j01_advisory.png` | 2 | Attach `demo/packages/fast-pay-utils/2.1.0/src/index.ts` and `demo/packages/fast-pay-utils/README.md`. Write `demo/packages/fast-pay-utils/ADVISORY.md` in GHSA style: synthetic GHSA id, summary, affected 2.1.0, patched 2.1.1, CVSS 3.1 vector and score, CWE-506 and CWE-829, indicators of compromise (the localhost sync-config URL, the Unicode-tag instruction), remediation (roll back, rotate secrets). |
| J02 | Ask | `origit_task_j02_reviewer_prompt.png` | 2–3 | Attach the OWASP Top 10 for Agentic Applications PDF and `origit/origit/origit/prefilter.py`. Write `console/backend/prompts/asi-reviewer.md`: a prompt that takes an Origit record, the pre-filter findings and the commit diff, and returns JSON with one entry per ASI01–ASI10 {status: finding|checked-clean|not-applicable, severity, cwe, evidence (quoted from the inputs), rationale}. Evidence only; never a pass/fail verdict. |
| J03 | origit-dev | `origit_task_j03_prefilter_tests.png` | 3–4 | Read `origit/origit/origit/prefilter.py`. Add `origit/tests/test_prefilter.py` covering every rule (one test each, including a Unicode-tag smuggled README that must decode to the hidden sentence) and add two rules: `rule_hallucinated_dependency` (dependency name not present in `demo/packages` or a local allowlist → ASI04 medium) and `rule_bidi_in_code` (bidi overrides inside written source files → ASI05 high, CWE-94). Run the tests. |
| J04 | Ask | `origit_task_j04_asi_mapping.png` | 2 | Read the OWASP Top 10 for Agentic Applications PDF (attach it) and `docs/asi-mapping.md`; write one line per ASI01–ASI10: what Origit checks deterministically, what Bob evaluates, default severity, CWE tag or N/A. |

## Bernard (40 coins) — statements, drafter, reviewer runs (works only in `docs/`, `slides/`)

| id | Mode | Screenshot | Est. | Prompt |
|---|---|---|---|---|
| B01 | Ask | `origit_task_b01_problem_solution.png` | 2–3 | Attach `ORIGIT_CLAUDE_CODE_BRIEF.md` §1–2 and `docs/cra-article-14.md`. Draft `docs/problem-solution-statement.md` (≤500 words) and `docs/bob-usage-statement.md` (≤500 words) using the "say / never say" list in brief §7. |
| B02 | Ask | `origit_task_b02_art14_drafter_prompt.png` | 2–3 | Attach `docs/cra-article-14.md` and a sample `origit taint --json` output. Write `console/backend/prompts/art14-early-warning.md`: a prompt that, given a taint result JSON, drafts the Article 14(4)(a) early warning (product, awareness time, affected components, malicious-code indication, member states placeholder, corrective measure = rollback commit). Include the expected output template. |
| B03 | Ask | `origit_task_b03_demo_script.png` | 2 | Turn "Revised Demo Story" into `docs/demo-script.md`: ≤3 min, ≥90 s of the console/CLI on screen, shot list with timings, narration text, the closing line. |
| B04 | — | reviewer runs | 10 reserved | Sunday: his `BOB_API_KEY` powers `bob run` reviewer + drafter for the recorded demo. |

## Coin ledger (update after every task)

| Who | Spent | Remaining | Reserved for Sunday demo |
|---|---|---|---|
| Tim | 0 | 40 | 10 |
| Jeremy | 0 | 40 | 10 |
| Bernard | 0 | 40 | 10 |
