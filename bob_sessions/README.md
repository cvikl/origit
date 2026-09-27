# bob_sessions

PNG screenshots of **Bob IDE task session consumption summaries**, one per task, from **every team member**.

How: Bob IDE → Tasks → select task → click the header → screenshot the summary.

Naming: `origit_task01_short_description.png`, `origit_task02_...png` (two-digit counter, continue the sequence across members; prefix your name if in doubt, e.g. `origit_task07_jeremy_tainted_package.png`).

Take the screenshot **as you go**, right after each task. Do not batch them for Sunday.


## Headless runs (Bob Shell)

Tasks run through Bob Shell (`tools/bob/run-task.sh`) have no IDE screenshot; each leaves `headless/origit_taskNN_<desc>.json` with the Bob task id, Bobcoin cost, duration and tool-call count from Bob's own result envelope, plus the mode and workspace. Bob Shell shares tasks with connected editors, so these runs may also appear in the Bob IDE Tasks list for a screenshot.
