# Change Log

## [0.1.0] — initial release

- ORIGIT view in the SCM panel: sessions, runs/commits, approver, tests, record hash
- Severity-coloured commit icons (green / blue / yellow / orange / red)
- `origit.taint` command with in-tree highlighting and info banner
- `origit.clearTaint` command
- `origit.showRecord` context-menu command — opens JSON record in editor
- `origit.refresh` command and view-title button
- Status bar item showing current session and recording state
- Auto-refresh every 15 s + FileSystemWatcher for `.origit/**` and `.git/refs/notes/**`
- CLI resolution via setting → git config → PATH
