# demo

- `payments-api/` — git submodule → [`origit-demo-payments-api`](../../origit-demo-payments-api): the fictional fintech's
  repository that IBM Bob IDE works in with Origit installed (`origit init`). It vendors `fast-pay-utils` 2.0.0 (clean)
  and 2.1.0 (compromised, synthetic) under `packages/`. Clone with `git submodule update --init`.
- `evidence/` — committed snapshots from that repo so nobody needs the submodule to see the result:
  `export.json` (`origit export`, every record), `taint-fast-pay-utils.json` (`origit taint --json`), `taint.txt` (human output),
  `prefilter-*.json` (deterministic ASI findings per commit).

The demo story is in [`../docs/demo-script.md`](../docs/demo-script.md).
