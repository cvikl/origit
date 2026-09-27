# IBM Bob Usage Statement

Origit is an agent provenance layer for git. IBM Bob is the agent it records, the reviewer and drafter, and one of the engineers that built it. Everything below happened in this repository; `bob_sessions/` holds the IDE task screenshots and headless run stats (task id, Bobcoin cost).

## 1. Bob is the recorded actor

The demo fintech repository (`demo/payments-api`) is instrumented by `origit init`. Bob IDE, in the `origit-build` custom mode (edits limited to `src/**`, rules ask it to read library docs before use), built the payout-export feature across sessions #42–#44, a health endpoint, settlement retry logic (#48) and PAN masking in export logs (#49). Every session has a real, hash-verified Origit record.

## 2. Bob's lifecycle hooks are the data source

`SessionStart`, `UserPromptSubmit`, `PostToolUse` and `Stop` hooks in `.bob/settings.json` call `origit session start`, `run start`, `trace` and `run end`. The payload gives session id, tool name, path and command; nothing is inferred. When Bob stops, Origit commits the run (`bob: <prompt> [session #48 run 1]`), runs the tests and seals the record as a git note. One Bob run = one commit = one record. In session #43 Bob ran `git commit` itself; the hooks still folded its trace.

## 3. Bob reviews and drafts

On the Business plan of the hosted console (origit.uk) every push is pre-filtered deterministically; then Bob (Bob Shell, ask mode) reads the record, the exact text the agent read with invisible Unicode-tag characters decoded, the diff and the OWASP Top 10 for Agentic Applications rulebook (document understanding), and writes cited evidence per ASI01–ASI10 with CVSS-style severity and CWE. It reviewed all fifteen demo commits; where its output is noisy we show it as is: evidence, never a gate decision. The same reviewer runs inside the IDE as the read-only `origit-review` mode. On a taint query, one button asks Bob to draft the EU CRA Article 14 early warning from the record.

## 4. Bob answers provenance questions in chat

`origit init` registers an MCP server (`origit mcp`: `origit_taint`, `origit_show`, `origit_log`) and an `/origit` skill. Asked "which commits read fast-pay-utils and what did they write?", Bob answered with seven commits, seven session labels, the first-read time and the roll-back commit in three tool calls.

## 5. Bob built parts of Origit

Headless Bob Shell runs, each traced and auto-committed by Origit itself: the MCP server (task 11, tests as the spec), the VS Code extension "Origit for Bob IDE" with its ORIGIT view in the Source Control sidebar (task 10), the README section on Bob IDE integration (task 14), the ASI mapping, demo script, incident summary, synthetic advisory and pre-filter tests. The deterministic core (record, hashing, notes, taint, pre-filter, session manager) was written by hand; Bob was used where an agent adds value and recorded everywhere it worked.

## Coins

About 12 of Tim's 40 Bobcoins went on build and demo runs; the rest is reserved for the recorded demo and the teammates' IDE tasks.

Bob evaluates, drafts and builds. Deterministic code records and queries. Bob never edits a record or a taint result.
