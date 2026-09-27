# Origit for Bob IDE

A VS Code extension that surfaces [Origit](https://github.com/origit) agent-provenance data directly in the Source Control panel.

## What the view shows

Open the **Source Control** panel (`Ctrl+Shift+G`) and expand the **ORIGIT** section.

| Level | What you see |
|---|---|
| **Session** | `#42 · Bob IDE · origit-build · 3 runs` — actor icon (robot / person / circle) |
| **Commit / run** | `a1b2c3d fix: payment logic` with a severity circle and `n read · n wrote · n deps` |
| **Details** | Approver, test summary, record sha256, and expandable Read / Wrote / Dependencies groups |

Use **Origit: Taint…** (`origit.taint`) to trace which commits are reachable from a package, file, or sha256. Affected commits are marked with a red ✖ icon in the tree and an information banner shows the count, sessions, and earliest SHA to roll back to. Use **Origit: Clear taint** to reset.

## Installation

1. Download the `.vsix` package.
2. In VS Code open the Extensions panel, click **…** → **Install from VSIX…**, and select the file.
3. Reload the window when prompted.

The extension activates automatically when the workspace contains `.origit/**` files, or when the ORIGIT view is opened.

## Configuration

| Setting | Default | Description |
|---|---|---|
| `origit.binary` | *(empty)* | Absolute path to the `origit` CLI. Leave empty to auto-resolve. |

**CLI resolution order:**
1. `origit.binary` VS Code setting
2. `git config origit.bin` (run in the first workspace folder)
3. `origit` on `PATH`

## How it works

This extension has **no logic of its own**. All data is obtained by running the origit CLI:

- `origit log --json` — session and commit data
- `origit taint <needle> --json` — taint analysis
- `origit show <sha> --json` — raw provenance record
- `origit session status --json` — status bar state

The tree and status bar refresh automatically every 15 seconds, and also on any change to `.origit/**` or `.git/refs/notes/**`.
