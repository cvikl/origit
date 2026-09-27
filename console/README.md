# Origit Console

The hosted, paid tier of Origit lives in its own repository and runs at **https://origit.uk**:
[`origit-console`](https://github.com/cvikl/origit-console) — a FastAPI service that hosts git repositories with agent
provenance visible: commits with their Origit record, pushes pre-filtered on arrival (deterministic, zero Bobcoins),
**cited ASI01–ASI10 evidence written by IBM Bob** (Bob Shell, ask mode) when the pre-filter fires, the taint view
(red/green commits, sessions, files, approver, first read, roll-back commit), the CRA **Article 14 early-warning draft**,
a security tracker and the evidence-pack export.

It vendors this repository's core as the git submodule `vendor/origit`, so the CLI and the console always agree on
the record format, the pre-filter rules and the taint engine.

Open-core, like git → GitHub: this repository (the CLI) is free and offline; the console is what a bank buys to prove
what its agents did.
