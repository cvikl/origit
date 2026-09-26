# IBM Bob Usage Statement

IBM Bob plays five distinct roles in Origit, each built and demonstrated at the hackathon.

## 1. Actor — `origit-build` custom mode

Bob IDE built the demo feature across three sessions in the `origit-build` custom mode. The
mode restricts edits to `src/**` and holds the Origit project rules. A fourth clean session
was run for contrast. Every session produced a real commit with a real Origit record.
`bob_sessions/` contains task screenshots from every team member and headless run stats as
JSON. Bob was the agent under test, not a stand-in.

## 2. Tracer — lifecycle hooks

Bob IDE and Bob Shell lifecycle hooks — `SessionStart`, `PreToolUse`, `PostToolUse`, `Stop`
— pipe every tool call to `origit trace`. The hook payload carries session id, tool name,
path, and command. The trace consumer classifies each call (read / write / exec / MCP) and
folds it into the Origit record at commit time. The hooks fire on every tool invocation;
the record reflects what the agent actually did. Bob's own infrastructure is the data source.

## 3. Reviewer — cited OWASP ASI evidence

When the deterministic pre-filter fires on a push — new dependency present, external URL
read, command executed, or invisible Unicode tag characters in any input — Bob reads the
Origit record, the decoded hidden text, the diff, and the OWASP Top 10 for Agentic
Applications rulebook. Bob writes cited evidence per ASI category in the Origit Console
(origit.uk): ASI01 Goal Hijack (hidden instruction in what the agent read), ASI04 Supply
Chain (compromised dependency), ASI05 Unexpected Code Execution (malicious function call),
each with a CVSS severity label and CWE tags. Bob evaluates; deterministic code records and
queries. Bob's output is evidence, never a gate decision.

## 4. Drafter — Article 14 early warning

From the taint result, Bob drafts the ENISA early-warning text in the Origit Console. The
Origit record contains every field the notification requires: product affected, first-read
timestamp, files written, approver, and roll-back commit. Bob also drafted the incident
summary at `docs/incident-2026-09-26.md`. The draft is produced in seconds, inside the
24-hour window, from data captured at commit time.

## 5. Builder — task screenshots and headless stats

Bob IDE task screenshots in `bob_sessions/` from every team member are the audit trail of
the build. Headless run stats are stored as JSON next to the screenshots. These files prove
Bob built the product, not a demo scripted around it.

IBM Bob is not a convenience integration. Bob is the agent whose activity Origit was built
to record — actor, data source, analyst, drafter, and builder in one system.

Word count: 433
