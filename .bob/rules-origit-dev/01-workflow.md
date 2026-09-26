# origit-dev workflow

1. Read the files named in the task prompt with `read_file` (they are the spec). Do not scan the repo.
2. Run the test file for the task once to see the failing assertions.
3. Implement in the named module only. Keep the module docstring in sync.
4. Run the full test command. All green before you stop.
5. End with:

```
Origit declaration
read:  <files>
wrote: <files>
added_deps: none
commands: <commands>
```
