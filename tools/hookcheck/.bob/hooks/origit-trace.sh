#!/bin/sh
# Verification tracer: dump every hook payload, wrapped with a timestamp, to .origit/trace.jsonl
mkdir -p .origit
printf '{"ts":"%s","raw":' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> .origit/trace.jsonl
cat >> .origit/trace.jsonl
printf '}\n' >> .origit/trace.jsonl
exit 0
