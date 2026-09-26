# Origit — versioning for agents

**Origit is an open-source agent provenance layer for git.** Git records *what* changed and *who* committed it.
Origit attaches a hashed record to every agent commit saying *what the agent read, wrote, added and ran* — and makes it queryable.

> Git tells you what changed. Origit tells you what the agent read before it changed it.

Built for the [IBM Bob 2.0 Hackathon](https://lablab.ai/ai-hackathons/ibm-bob-2-hackathon) (lablab.ai, Sep 2026).
**IBM Bob IDE is the actor, the tracer, the reviewer and the drafter** — see [Bob usage](#how-ibm-bob-is-used).

## Why now

- Supply-chain attacks on AI coding agents are compounding: H1 2026 had 2.6× the campaign volume of all of 2025, and AI-agent tooling (MCP servers, rules files) was the delivery mechanism in 14 of 59 tracked campaigns ([Phoenix Security](https://phoenix.security/accelerating-supply-chain-attacks-npm-pypi-vsx-ai-enabled-2026/)).
- **EU Cyber Resilience Act, Article 14** is live since 11 Sep 2026: early warning to ENISA within **24 hours** of becoming aware of an actively exploited vulnerability or severe incident, full notification within 72 h ([CRA](https://digital-strategy.ec.europa.eu/en/policies/cyber-resilience-act)). A compromised library introduced by an agent qualifies under Art. 14(5)(b).
- The question nobody can answer today: *when a library / MCP server / README turns out to be poisoned — which code did an agent write after reading it?*

## What it does

| Command | What it answers |
|---|---|
| `origit init` | Installs Bob IDE hooks, the `origit-build` custom mode and git hooks into an existing repo |
| `origit trace` | Hook consumer: appends every Bob tool call to `.origit/trace.jsonl` |
| `origit record` | Folds the trace into a canonical, SHA-256-hashed record stored in `refs/notes/origit` |
| `origit log` / `origit show <commit>` | Commits with their records / the full record |
| **`origit taint <package\|file\|sha256>`** | Affected commits, sessions, files written, approvers, first-read time, last clean commit to roll back to |
| `origit export` | JSON evidence pack for a commit range |

**Rule: a commit without a record does not exist.** The pre-commit hook refuses agent commits that have no captured trace. Human commits pass through, marked `actor: human`.

## The record

Canonical JSON (sorted keys, no whitespace, UTF-8), SHA-256 hashed, stored as a git note. See [`origit/origit/record.py`](origit/origit/record.py) for the schema.

```
session · actor · read[] {kind: file|pkg|url|mcp, ref, sha256} · wrote[] · added_deps[] · commands[]
author · approver · approved_at · tests {run, passed, failed} · record_sha256
```

## Origit Console (powered by IBM Bob)

A GitHub-like view of the repo with agent context visible: push → commits → record. On every push a **deterministic pre-filter** (new dependency? external read? command executed? agent config changed? invisible Unicode-tag characters in anything the agent read?) decides whether Bob is asked to evaluate the push against the [OWASP Top 10 for Agentic Applications](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/) and write **cited evidence per category**. Taint view lights affected commits red. One button drafts the CRA Article 14 early warning from the record.

## How IBM Bob is used

1. **Actor** — Bob IDE in the `origit-build` custom mode builds the feature (edit restricted to `src/**`).
2. **Tracer** — Bob IDE lifecycle hooks (`SessionStart`, `PreToolUse`, `PostToolUse`, `Stop`) shell out to `origit trace`; this is the source of `read[]`.
3. **Reviewer** — a Bob subagent reads trace + diff with the OWASP Agentic Top 10 as its rulebook and produces ASI evidence JSON.
4. **Drafter** — Bob drafts the Article 14 notification from the record.
5. **Builder** — Bob helped write Origit itself; every task is in [`bob_sessions/`](bob_sessions/).

## Repository layout

```
origit/      CLI + core (Python 3.11+, click only)
console/     pointer to the hosted console (separate repo origit-console, https://origit.uk)
demo/        payments-api (git submodule → origit-demo-payments-api: the fintech's repo Bob works in) + evidence pack
docs/        statements, ASI mapping, CRA note, demo script, roadmap, STATUS.md
bob_sessions/  PNG screenshots of Bob IDE task session summaries (all team members)
slides/      final deck
```

## Quick start

```bash
cd origit && pip install -e .
cd /path/to/your/repo && origit init      # installs Bob hooks, origit-build mode, git hooks
# work in Bob IDE, commit as usual …
origit log
origit taint fast-pay-utils
# demo: git submodule update --init && cd demo/payments-api && origit taint fast-pay-utils
```

## Positioning

Agent provenance layer for git. Pedigree (May 2026 winner) signed the *output*; Origit records the *input* — one step earlier. Bob-native first, agent-agnostic by design. Open-core: the free layer wins adoption; the console is what a bank buys to prove what its agents did.

## References

- Hackathon: https://lablab.ai/ai-hackathons/ibm-bob-2-hackathon · guide: https://lablab-ibm-bob-2-hackathon-guide.s3.us.cloud-object-storage.appdomain.cloud/index.html
- Bob IDE docs: https://bob.ibm.com/docs/ide · hooks: https://bob.ibm.com/docs/ide/configuration/lifecycle-hooks · custom modes: https://bob.ibm.com/docs/ide/configuration/custom-modes · rules: https://bob.ibm.com/docs/ide/configuration/rules · subagents: https://bob.ibm.com/docs/ide/features/subagents
- OWASP Top 10 for Agentic Applications: https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/
- EU CRA: https://digital-strategy.ec.europa.eu/en/policies/cyber-resilience-act
- Supply-chain stats: https://phoenix.security/accelerating-supply-chain-attacks-npm-pypi-vsx-ai-enabled-2026/ · Clinejection: https://labs.cloudsecurityalliance.org/research/csa-research-note-claude-code-github-action-prompt-injection/ · hallucinated packages: https://www.augmentcode.com/guides/sbom-for-agent-driven-pipelines
- CVSS: https://www.first.org/cvss/calculator/3.0 · CWE: https://cwe.mitre.org/data/index.html · MITRE ATLAS: https://atlas.mitre.org/matrices/ATLAS-matrix · Unicode tag smuggling: https://embracethered.com/blog/ascii-smuggler.html
- Benchmark (May winner): https://lablab.ai/ai-hackathons/ibm-bob-hackathon/ctrlcats/pedigree

## License

MIT — see [LICENSE](LICENSE).
