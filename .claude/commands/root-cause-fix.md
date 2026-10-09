---
description: Failing reproduction first, sibling-case grep, minimal fix, then the corrupted-data backfill check.
argument-hint: <bug, e.g. CS-033 registry drops recipes with an empty ingredient blob>
---

# /root-cause-fix

## WHO RUNS THIS - ONE SUB-AGENT, NEVER THE MAIN SESSION

FLEET-KIT v10, carried at v11 (MAIN's 2026-10-08 08:39 ORDER, item 4; the FLEET-COMMON banner; CS-1282, CS-1287):
the main session does NOT run these steps. It dispatches the WHOLE of this command -
every step below, with this file's text and the arguments as the prompt - to ONE
sub-agent (the Agent tool, in the background by default), waits for that sub-agent's
completion notification, and relays ONLY its final line, the command's one-line result,
to chat. The sub-agent runs every step itself and never re-dispatches the whole command.
The kit's PreToolUse hook `ops/fleet_kit/fleet_subagent_first.py` denies Bash,
PowerShell, Read, Edit, Write, Grep, Glob and NotebookEdit in the main thread once its
mode is deny, so a step run there stops at its first tool call.

Bug: $ARGUMENTS

A fix without a reproduction is a guess with a commit message. Work the loop in order.

## 1. Reproduce it FIRST, as a failing test

- [ ] Reproduce the reported behaviour EXACTLY as reported before theorising. If you cannot
      reproduce it, that is the finding - report it and get more detail. Do not fix a bug
      you cannot see.
- [ ] Grep to confirm every method, field and data shape the reproduction uses actually
      exists. Cite `file:line`. Never scaffold against an assumed API.
- [ ] Write the reproduction as a REGRESSION TEST in the suite, not as a throwaway script.
- [ ] Run it. **Quote the failure line and confirm it fails for the RIGHT reason** - the
      defect, not an import error or a missing fixture. A test that passes before the fix is
      a test about nothing.

## 2. Find the ROOT cause, not the nearest cause

- [ ] Trace from the symptom to the first point where the data or the control flow was
      already wrong. Cite `file:line` at each hop.
- [ ] State the mechanism in one sentence: "X happens because Y, whenever Z". If you cannot
      write that sentence, you have found a symptom, not a cause.
- [ ] Check the artifact rather than the doc. **A filed count is a hypothesis, not a fact**,
      and **a row's AGE matters** - it may describe code that no longer exists.
- [ ] Rule out the environment before blaming the code: check the settings file actually
      PARSES, check the hook actually FIRED end to end, check the process is the one you
      think it is. Presence is not firing.

## 3. Grep for EVERY sibling case sharing the same root cause

- [ ] Search by MECHANISM, not by the symptom string.
- [ ] **An empty grep is a claim about your PATTERN, not about the codebase.** Vary the
      delimiters and the casing before concluding absence.
- [ ] **A resolver fix is not a consumer fix.** A falling residual count can hide a private
      copy in a consumer that never adopted the fix. Diff the CONSUMER's artifact.
- [ ] **A rendered field is not evidence of a producer.** Grep for WRITERS, excluding scripts
      and tests, before assuming a pipeline exists.
- [ ] Add a failing test for EACH sibling before fixing any of them.
- [ ] List every sibling found and every one deliberately excluded, with its reason.

## 4. Minimal fix

- [ ] Fix the ROOT, then confirm every sibling test goes green as a consequence. If a sibling
      needs its own separate fix, the root was not the root - go back to step 2.
- [ ] Smallest change that does it. No adjacent refactor.
- [ ] When adding a required field to a dataclass, append it at the END with a default.
- [ ] Atomic writes for any file another process may read:
      `tmp.write_text(...); tmp.replace(target)`, with a rename retry on Windows.
- [ ] Never re-read the file you just edited to confirm the edit.

## 5. CORRUPTED-DATA BACKFILL CHECK - the step everyone skips

The bug ran in production. Ask what it LEFT BEHIND.

- [ ] Did the defect WRITE anything? Ledger entries, cached registries, normalized artifacts,
      persisted card state, memory files, logs, config.
- [ ] Enumerate every artifact the defective code path could have produced or mutated, and
      the time window in which it ran.
- [ ] Determine which existing rows or files are wrong. **State the SET you checked** - "zero
      bad rows" is relative to a set, and the same file can be clean under one filter and
      filthy under another.
- [ ] Decide and state: backfill, invalidate and regenerate, or accept with a documented
      caveat IN THE ARTIFACT. **A caveat stated in chat is not a caveat in the artifact.**
- [ ] If a persisted card id or a world-token key was computed by the defective path, check
      whether persisted state is now ORPHANED. A changed card id silently loses accept /
      dismiss / snooze state on every reload.
- [ ] If the fix changes a schema, bump the schema version field and say what happens to old
      files.
- [ ] Write a test that would catch the CORRUPTED STATE, not just the defective code.
- [ ] If nothing was written, say so explicitly and say how you established it. "No backfill
      needed" without a check is an assumption.

## 6. Verify and report

- [ ] Run the tier-appropriate suite from the repo root with an explicit target directory.
      Report the command, the exit code, and the counts observed THIS run.
- [ ] **Proving your change happened is not proving it matters** - verify the DOWNSTREAM
      output changed.
- [ ] Run an adversary pass with the DOES-IT-REPRODUCE lens.
- [ ] Report: the mechanism sentence, the root `file:line`, every sibling, the backfill
      decision and the set it was checked against, and the test names that now cover it.
- [ ] Ledger entry cites the item ID, the merged file and the TEST NAME - not the slice SHA.
