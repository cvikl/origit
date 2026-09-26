# Origit Console

GitHub-like view of a repository with the agent context visible, powered by IBM Bob.

- `backend/server.py` — stdlib HTTP server: API + static frontend. Reads Origit records from a git repo
  (`ORIGIT_REPO_PATH`) or from the committed evidence pack (`demo/evidence/export.json`).
- `backend/prompts/` — the two Bob prompts: `asi-reviewer.md` (cited evidence per ASI01–10) and
  `art14-early-warning.md` (CRA Article 14 early warning from a taint result).
- `frontend/` — plain HTML/JS, no build step.
- `data/` — cached Bob outputs (reviews per commit, drafts per needle). Committed so the deployed demo never re-spends coins.

Run locally:
```bash
export ORIGIT_REPO_PATH=../origit-demo-payments-api   # optional; falls back to demo/evidence
export BOB_API_KEY=...                                  # optional; without it review/draft buttons show "unavailable"
python3 console/backend/server.py                       # http://localhost:8787
```
