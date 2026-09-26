# Origit project rules (all modes)

- Python 3.11+, standard library plus `click`. No other dependencies in `origit/`.
- Deterministic core: nothing under `origit/origit/` may call a model, the network, or read the clock except `trace.utcnow()`.
- Small pure functions. Type hints. Module docstrings are the spec; keep them accurate when behaviour changes.
- Tests are the definition of done: `cd origit && env -u PYTHONPATH PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -q`
- Never touch `.bob/`, `.origit/`, `.env*`, `bob_sessions/`, or any file containing `apikey`.
- Synthetic data only. Test card numbers like 4111 1111 1111 1111. No real names, emails or secrets.
- Do not run `git commit`; the human commits so the pre-commit hook folds your trace into the record.
