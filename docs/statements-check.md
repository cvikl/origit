# Statements vs. code — claim check (Sunday 02:40 BST)

Checked `submission/Deliverable 1 - Problem and Solution Statement.pdf` (456 words) and `docs/problem-solution-statement.md` (499 words) against the repository as it is now. Fix the marked lines before submitting; everything else is true of the code.

## Deliverable 1 (PDF) — lines to change

| Claim in the PDF | Reality | Replace with |
|---|---|---|
| "rated CVSS 9.1 Critical" | the synthetic advisory rates 2.1.0 **CVSS 3.1 8.2 HIGH** | "rated CVSS 8.2 High in the advisory" |
| "Every test passes because the payload only activates in production with real payment data" | the exfil runs **at import time** (to localhost only) and the agent-facing payload is an **invisible Unicode-tag instruction** in the README/docstring; tests pass because nothing they assert touches either | "Every test passes: the payload hides in import-time telemetry and in invisible text, not in any code path the tests exercise" |
| "three affected commits across sessions 42, 43 and 44" | **7 affected commits across sessions #42–#47 and #49** (3 direct, 4 propagated through files those sessions wrote); #48 clean | "seven affected commits across seven sessions, four of them by propagation, and one clean session in between" |
| "identifies e19b...770 as the last clean commit" | roll-back commit is **17c436c** | "identifies commit 17c436c as the last clean commit" |
| "origit record captures each session automatically through the hook" | true, and since Sunday **one Bob run = one commit = one record**: the Stop hook commits the run and seals the record | add: "one agent run becomes one commit with one sealed record" |
| "IBM Bob 2.0 consumes that output directly, calls POST /api/{org}/{name}/draft-art14" | the **console** calls Bob (Bob Shell) when a human presses *Draft with Bob*; Bob does not call the endpoint | "one button in the console asks IBM Bob to draft the Article 14 early warning from the taint result" |
| "works with any git-based workflow today" | true for the CLI; keep, but say **Bob-native first, agent-agnostic by design** somewhere | add the phrase |
| Nothing about the OWASP evidence | the Business plan writes **cited evidence per OWASP ASI01–ASI10 per commit** on push | add one sentence |

## docs/problem-solution-statement.md — lines to change

- "A commit without a record is refused by the pre-commit hook." → only when `ORIGIT_REQUIRE_TRACE=1`; by default human commits pass through with `actor: human`. Say: "Agent commits without a trace can be refused by the pre-commit hook; human commits pass through marked `actor: human`."
- "final report within 14 days of a fix" → the CRA says 14 days after a corrective/mitigating measure is available (vulnerability) or **one month** (severe incident). Keep "14 days" only for vulnerabilities, or say "final report within the Article 14 deadlines".
- "OWASP Agentic Top 10 evaluation on push, and a one-click Article 14 draft" → true since Sunday (Bob Review on push, Business plan). Keep.
- Add one line: "one Bob run = one commit = one record; Bob IDE shows every session in an ORIGIT panel".

## Never say (both documents pass)
No occurrence of "proves the code is safe", "nothing was missed", "replaces git", "PCI-DSS compliant", "Bob guarantees". "works with any git-based workflow" is about git, not agents: acceptable.
