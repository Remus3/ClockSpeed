---
name: bare-python3-is-the-store-stub
description: On this Windows machine a bare `python3` can resolve to the Microsoft Store app-execution alias and hang or do nothing; never call it.
metadata:
  type: reference
---

On this machine a bare `python3` can resolve to the Microsoft Store app-execution alias
(the Store stub) rather than the installed interpreter. It hangs or silently does nothing,
so a script, scheduled task or sub-agent step that calls it can look like it ran while
running nothing. Source: MAIN INFORMATION note, 2026-10-04 09:05, a machine-level finding
for every tree.

**How to apply:** never write bare `python3` in a script, a scheduled task, a hook command
or a sub-agent prompt. Use the interpreter this tree records - the one `scripts/verify_env.py`
asserts - by its full path, or `python` where the tree's own commands already use it and
it is known to resolve to that interpreter. A shebang line inside a file is not an
invocation and does not need changing; an explicit `python3 <script>` call does.
