# Origit — instructions for AI agents working in this repo

Origit is an agent provenance layer for git: a hashed record per commit of what the agent read, wrote, added and ran,
stored in `refs/notes/origit`, queryable with `origit taint <package|file|sha256>`. Deterministic Python core, IBM Bob at the edges.

## Layout
- `origit/origit/` CLI + core. `record.py` (schema, canonical hash — done), `trace.py` (hook consumer + fold),
  `notes.py` (git notes), `taint.py` (query), `prefilter.py` (deterministic ASI triggers), `cli.py`, `templates/`.
- `origit/tests/` acceptance tests. A task is done when its test file passes.
- `console/` web console (Sunday). `demo/payments-api/` sample app. `docs/` statements and STATUS.md.

## Commands
- Install: `cd origit && python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"`
- Test: `cd origit && env -u PYTHONPATH PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -q`
- CLI: `origit/.venv/bin/origit --help`

## Conventions
- Records are canonical JSON (see `record.py`); never hand-build JSON strings, go through `record.finalize`.
- Trace events may be raw hook payloads `{"event","session_id","tool","input","output","ts"}` or wrapped
  `{"ts": "...", "raw": {...}}` (fallback tracer). Always unwrap.
- Bob tool names: read `read_file glob grep list_files GetSymbolsOverview FindSymbol FindReferencingSymbols`,
  write `write_file apply_diff insert_content search_and_replace`, exec `execute_command`, mcp `use_mcp_tool access_mcp_resource`.
- Keep functions pure; pass paths in, return dicts. `subprocess.run(["git", ...])` only inside `notes.py`.
- Do not commit. Do not edit `.bob/`.
