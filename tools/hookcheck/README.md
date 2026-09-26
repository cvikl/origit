# Hook verification kit (burns ~1–2 Bobcoins, once)

Question: do Bob IDE hooks fire on file reads, and does the stdin payload carry the file path and session_id?

1. Create a scratch folder with two files, copy `.bob/` from here into it:
   ```bash
   mkdir -p /tmp/hookcheck && cd /tmp/hookcheck && git init -q
   printf 'export const a = 1;\n' > a.ts; printf 'export const b = 2;\n' > b.ts
   cp -r <repo>/tools/hookcheck/.bob .
   ```
2. Open `/tmp/hookcheck` in Bob IDE (hackathon account). Check Settings → Hooks lists 4 workspace hooks.
3. Start a new task in **Agent** mode and paste exactly:
   > Read a.ts and b.ts, then change b.ts so it exports 3 instead of 2. Then run `ls` in the terminal. Do not ask questions.
4. When Bob finishes: Tasks → the task → click header → **screenshot** → save as `bob_sessions/origit_task01_hook_verification.png`.
5. Run `python3 <repo>/tools/hookcheck/analyse.py /tmp/hookcheck/.origit/trace.jsonl` and check the output (and the first ~10 lines of `.origit/trace.jsonl`).
