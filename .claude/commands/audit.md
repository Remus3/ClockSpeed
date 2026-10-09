---
description: One-file deep audit - correctness, security, error handling, resource lifetime, concurrency, input validation.
argument-hint: <one file path, e.g. clockspeed/save/header.py>
---

# /audit - one-file deep audit

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

Target file: $ARGUMENTS

ONE file. If you were given more than one, audit the first and say the rest need their own
pass. A wide shallow sweep finds nothing this is for.

Read the whole file before writing a single finding. Cite `file:line` on every finding.
Classify each as `MUST-FIX`, `SHOULD-FIX` or `NOTE`.

## 1. CORRECTNESS

- [ ] Re-derive the file's central computation by a DIFFERENT route than the code takes. Do
      not merely re-read the code and agree with it.
- [ ] Off-by-one at every boundary: first, last, empty, single element.
- [ ] Unit and scale mismatches - per minute against per second, items against stacks, MW
      against MJ.
- [ ] **Exact rational arithmetic in the solve path.** Any `float`, `/` on ints producing a
      float, `round`, or a float literal in a solve path is a CORRECTNESS BUG, not a
      rounding nuisance. Assert the absence of floats.
- [ ] An averaged quantity presented as a total, or a rate presented as a count.
- [ ] Recipe loops and byproducts - the classic hard case. Does it terminate? Is the
      fixed point correct?
- [ ] Version dispatch: does it handle EVERY version it claims to? Save version 52 and 60 are
      both already in the operator's library, with header version 14 across both.
- [ ] Does the code agree with the DATA rather than a hardcoded constant? A magic number the
      game can patch is a bug waiting for a patch note.

## 2. SECURITY AND PRIVACY

- [ ] Any Windows account name, numeric platform account id, world name, machine name, or
      absolute path under a user home directory. Any hardcoded interpreter path - it must be
      `python`, NEVER `py -3` (BOOTSTRAP.md section 2.5).
- [ ] **Every code path that could echo raw save-header bytes leaks PII**: error messages,
      debug dumps, hex previews, log lines, exception context, repr and str. The header
      options string is REDACTED BY DEFAULT and needs an explicit opt-in flag to render.
- [ ] Any write path that could touch the game install or the save directory. **Read-only
      against the game is an invariant, not a preference** - not once, not for anything.
      Check every `open` mode, every temp path, every `replace` target.
- [ ] Path traversal on any externally supplied name, including a world name - the world name
      is operator-chosen data, never an identifier and never a filename component in a
      tracked file.
- [ ] Secrets, tokens or keys in source, in defaults, or in a committed config.
- [ ] Deserialization of untrusted bytes - bounds before allocation, length prefixes trusted
      blindly, decompression ratio limits.
- [ ] TLS handling on the local surface: the self-signed certificate is handled cleanly
      rather than by disabling validation wholesale.

## 3. ERROR HANDLING

- [ ] Every raised exception type and whether the caller can act on it.
- [ ] Broad `except` clauses: what do they SWALLOW? **Fail-soft code makes a raising spy
      vacuous** - the same swallowing hides real defects.
- [ ] **Unknown game content is flagged and skipped, never fatal, never silently wrong.** An
      unknown actor class is logged and skipped. Confirm this file honours that.
- [ ] A corrupted or truncated input produces a CLEAN ERROR, not a crash and not a wrong
      number. Where is that tested?
- [ ] Does an error message name what failed and what to do, without leaking bytes?
- [ ] Is any failure silent? A returned `None`, an empty list, a default that means both
      "nothing" and "broken".
- [ ] Does anything degrade quietly to partial coverage? Say so loudly instead.

## 4. RESOURCE LIFETIME

- [ ] Every file handle, socket and subprocess: opened where, closed where, closed on the
      EXCEPTION path.
- [ ] Context managers used, or a documented reason they are not.
- [ ] **Atomic writes for any file another process may read**:
      `tmp.write_text(...); tmp.replace(target)` with a rename RETRY on Windows - the rename
      can transiently fail while another process holds a handle. A poller reads mid-write
      otherwise.
- [ ] Temp files cleaned on both paths. **Copy the save to a work directory before parsing** -
      the game holds handles during autosave and parsing in place will eventually hit a
      locked or half-written file.
- [ ] Caches: bounded? invalidated on what? The parsed usmap is cached - on what key?
- [ ] Background processes: **a detached process can return a real PID and exit code zero
      while doing zero work.** Is the WORK PRODUCT asserted, or just the launch?
- [ ] Process stops use a forced kill by PID, never a graceful cmdlet that can hang a tool
      pipe.

## 5. CONCURRENCY

- [ ] Shared mutable state and who else touches it.
- [ ] Read-modify-write windows on any file another process can write.
- [ ] **Serialized callers self-suppress, so an observed duplicate implies a RACE**, not
      merely shared state.
- [ ] Reentrancy: can a callback re-enter the function that scheduled it?
- [ ] Timer or poll loops rebuilding state under a reader.
- [ ] `write_text` converts LF to CRLF on Windows and `read_text` hides it - any byte count
      or hash comparison here is lying unless bytes are written explicitly.

## 6. INPUT VALIDATION

- [ ] Every external input: the save bytes, the docs JSON, the usmap, config, an API request
      parameter. Validated where, exactly?
- [ ] Encoding sniffed rather than assumed - never assume UTF-16 LE with a BOM without
      reading the first bytes.
- [ ] Length prefixes: the save format is length-prefixed with an int32 count that INCLUDES
      the trailing null. Is that handled, and is a hostile length bounded before allocation?
- [ ] Numeric parsing from string blobs, and what happens on an empty or malformed blob.
- [ ] Are identifiers NAMESPACED so modded content cannot collide with vanilla?
- [ ] Is a solve that touched unmodelled content marked `contains_unmodeled_content`?
- [ ] API endpoint parameters: type, range, and what an unknown card id or milestone does.

## 7. Test coverage of this file

- [ ] Which of the findings above has a test? Name it. Which do not?
- [ ] Does the suite run on a machine with NO game installed?
- [ ] Is any fixture a slice of real game data or a save file? That is a MUST-FIX.
- [ ] **Delete the guard:** for each defensive guard, would the suite still be green without
      it? If yes, it is untested.
- [ ] **A negative assertion rules out without pinning down.** Look for tests asserting
      absence where they should assert presence.

## 8. Report

- Findings grouped by the six sections, each with `file:line` and a classification.
- The central computation you re-derived, and by what route.
- What you could NOT audit and why - labelled unverified, never rounded up to clean.
- `AUDIT: CLEAN` only if there are zero MUST-FIX findings. Otherwise
  `AUDIT: <n> MUST-FIX`.
