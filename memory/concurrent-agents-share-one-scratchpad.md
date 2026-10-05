---
name: concurrent-agents-share-one-scratchpad
description: Concurrent agents - siblings in one session AND sessions from other trees on this machine - can be handed the same scratchpad; use a private subfolder and never run a script you did not write.
metadata:
  type: reference
---

The session scratchpad is NOT private. Two observations:

1. **Within a session.** Every concurrently running subagent writes to the same scratchpad,
   so a generically named helper (`plant.py`, `probe.py`) is overwritten mid-run by a
   sibling's. An adversary's mutation script was once replaced by a sibling's script that
   targeted a DIFFERENT worktree; it noticed only because the output format changed.
2. **Across trees** (MAIN INFORMATION note, 2026-10-04 09:05). Concurrent sessions from
   different repositories on this machine have been handed the same scratchpad. One tree's
   session found and ran another tree's generically named helper, which wrote a stray
   progress update into a third tree's progress file.

**Why it matters:** a swapped script produces a transcript that looks exactly like a real
one. Hash-based landed/reverted assertions do not help, because they are computed by
whichever script is on disk.

**How to apply:**

- Every agent works in a PRIVATE subfolder of the scratchpad named with the channel code
  plus a unique suffix, for example `CS-<task-or-timestamp>/`. Say so in every dispatch
  brief - an agent cannot discover that siblings exist.
- Give helper scripts unique names. Never run a scratchpad script not written in this
  session, and never treat a file loose at the scratchpad top level as yours.
- The same applies to any shared mutable resource a brief does not namespace: a temp
  database, a fixed port, a well-known output filename.
- On a suspected collision, warn every live agent and verify a suspect transcript by
  re-running it, not by re-reading it.
