# Deck v3 → v4 fix list (for Bernard) — Sunday 27 Sep

Source of truth: the live demo repository `acme-payments/payments-api` on https://origit.uk and `origit taint fast-pay-utils` run on it at 02:20 BST Sunday. Everything below is what the code actually shows; the video and the statements must match these numbers.

## Real numbers (Sunday 02:20 BST)

| Item | Deck v3 says | Reality (use this) |
|---|---|---|
| Console name | "LIVE ORIGIN CONSOLE" (slide 5) | **Origit Console** |
| Commits in demo repo | 13 commits, 12 with records | **18 commits, 17 with Origit records** (one pre-Origit scaffold commit has none, on purpose: Origit adopts history) |
| `origit taint fast-pay-utils` | 3 commits affected | **7 commits affected** (3 direct reads/dependency adds + 4 propagated through files those sessions wrote), **11 clean** |
| Sessions affected | #42, #43, #44 | **#42, #43, #44, #45, #46, #47, #49** (7 sessions); **#48 is clean** (retry logic, never read the package, never touched its files) |
| Files written (primary) | payout-export.ts, payment-utils.ts | **src/payout-export.ts, src/payment-utils.ts** (+ tests, `jest.config.js`, `node_modules/fast-pay-utils/dist/index.d.ts`, `packages/fast-pay-utils/ADVISORY.md` shown collapsed as "also touched") |
| Approver / time | bernard, 26 Sep 2026 14:02 UTC | **bernard**, latest approval **27 Sep 2026 01:16 UTC** |
| First read | session #42, 24 Sep 2026 09:14 UTC | **session #42, 26 Sep 2026 13:21 UTC** |
| Roll-back commit | e19b…770 | **17c436c** ("feat: payments API scaffold") |
| Commit ids on slides | a3f1…, d7e2…, b8c4…, 8f2a…c41 | real ids: **ac31928** (session #42, first read + dependency), **d8f549f** (#43), **d5a4643** (#44), **36c384b** (#49, propagated) |
| Record hash on slide 3 | sha256:4d9e…b02 | any real one, e.g. ac31928 → open https://origit.uk/acme-payments/payments-api/commit/ac31928 and copy the record hash |
| "registry MCP read" (slides 1, 2) | | it is a **file read**: `node_modules/fast-pay-utils/README.md` (kind `file`, sha256 recorded) plus the dependency add `fast-pay-utils@2.1.0`. Say "README read + dependency added". MCP reads are recorded the same way but are not in this demo. |
| CVSS | 9.1 CRITICAL | the synthetic advisory says **CVSS 3.1 8.2 HIGH** (`packages/fast-pay-utils/ADVISORY.md`). Use 8.2 HIGH, or drop the number. |
| "All twelve tests pass" | 12 | **32 tests pass** at HEAD (Jest), 8 at the first tainted commit. Say "the test suite is green at every commit". |
| "payload only activates in production with real payment data" | | not what Jeremy built: the exfil runs **at import time**, to `localhost:8080` only, errors silenced; the README/docstring carry the invisible Unicode-tag instruction. Say: "tests pass because the payload hides in import-time telemetry and invisible text, not in the code path the tests exercise". |
| "Enterprise Gate" (slide 3) | | rename **Business plan · Bob Review**. Bob never gates: "Bob evaluates and drafts; deterministic code records and queries." |

## Lines to add (one each, ≤ 8 slides total)

1. **Slide 3 (How it works)** — add one line under the record: *"Bob IDE: ORIGIT panel in Source Control shows every session, run and record; status bar: `Origit: session #48 run 1 · recording`."*
2. **Slide 5 (Live demo)** — add one line: *"Bob Review on push: cited evidence per OWASP ASI01–ASI10 for every new commit — ASI01 hidden Unicode instruction in the README, ASI04 new dependency, ASI05 commands run — with CVSS-style severity and CWE."*
3. **Slide 5** — footnote already right: "Affected means matched by provenance, not confirmed compromise." Keep.
4. **Slide 6 (Product)** — replace the counts with **18 / 17** and add *"one Bob run = one commit = one record (Stop hook auto-commits)"* to the open-source column; the Business column: *"Bob Review on push · Article 14 draft with Bob · Security tracker"*.
5. **Slide 1 / cover** — keep "Provenance for AI-written code" but the tagline everywhere is *Git tells you what changed. Origit tells you what the agent read before it changed it.*

## Never say (from the team rules)
"proves the code is safe", "nothing was missed", "replaces git", "works with any agent" (unqualified), "PCI-DSS compliant", "Bob guarantees", "Enterprise gate".

## Where to check
- Taint: https://origit.uk/acme-payments/payments-api/taint?q=fast-pay-utils
- Commits: https://origit.uk/acme-payments/payments-api/commits · Security: https://origit.uk/acme-payments/payments-api/security
- CLI: `cd demo/payments-api && origit taint fast-pay-utils` (see `demo/evidence/taint.txt`)
