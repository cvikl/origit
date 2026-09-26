"""Origit — agent provenance layer for git.

Deterministic core, AI at the edges: everything in this package is plain Python
with no model calls. IBM Bob produces the trace (via lifecycle hooks) and, in the
console, evaluates and drafts. Origit records, hashes and queries.
"""

__version__ = "0.1.0"

NOTES_REF = "refs/notes/origit"
STATE_DIR = ".origit"
TRACE_FILE = "trace.jsonl"
PENDING_RECORD = "pending-record.json"
