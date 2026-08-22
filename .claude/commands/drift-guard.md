---
description: Run every drift guard and report the exit codes observed this run.
argument-hint: [--fix to apply safe auto-corrections]
---

# /drift-guard

Args: $ARGUMENTS

Run this at EVERY `/done`, no exceptions. Thirty seconds each time beats a cleanup session
later. Report the exit code of every command - a guard you did not read the exit code of is
a guard you did not run.

## 1. Run the guards

- [ ] `python tools/drift_guard.py` - exit code: ____
- [ ] `python tools/doc_budget.py` - exit code: ____
- [ ] `python tools/facts_probe.py` - exit code: ____ (the live-state fact set)
- [ ] `python scripts/verify_env.py` - exit code: ____ (interpreter, toolchain, paths, ports)
- [ ] `python tools/precommit_gate.py --staged` - exit code: ____ (character set and secrets)
- [ ] `python tools/memory_sync.py` if any source doc changed - exit code: ____

## 2. What each guard must actually be checking

- [ ] **Game version pin.** The tracked build-string and content-hash pin against the live
      install. When the game patches, the hash changes, the guard goes RED, and the
      re-extract runs. That is the intended workflow, not a failure.
- [ ] **Doc size budgets.** `CLAUDE.md` and any auto-loaded file under 40 KB (hard),
      `memory/MEMORY.md` under 20 KB (hard), `memory/*.md` leaves under 6 KB (warn),
      `ROADMAP.md` under 60 KB (warn).
- [ ] **Restated numbers.** Any count appearing in prose that is not generated. A hardcoded
      count in a doc is a lie with a timestamp on it.
- [ ] **Item-state placement.** No closed item in `ROADMAP.md`; no open item only in
      `docs/LEDGER.md`; every `docs/GATED.md` entry names its external unblocking condition.
- [ ] **Memory reachability.** Every `memory/*.md` reachable from `memory/MEMORY.md` or an
      `INDEX_<domain>.md`.
- [ ] **Character set.** 7-bit ASCII across all authored files. No em-dash, en-dash or smart
      quotes.
- [ ] **PII.** No Windows account name, numeric platform account id, world name, machine
      name, absolute home path, or hardcoded interpreter path in any tracked file. The
      interpreter is invoked as `python`, NEVER `py -3` (BOOTSTRAP.md section 2.5).
- [ ] **Port allocation.** `config/ports.json` matches the reserved band 8900-8911 with base
      port 8901, and the docs agree with the config rather than restating it.
- [ ] **Cross-references.** Every doc link resolves; no orphaned markdown.
- [ ] **Recall coverage.** `embedded == active` in the semantic store. A "healthy" status is
      NOT proof recall works - a store can report healthy while most rows have no embedding,
      silently degrading recall to keyword matching.

## 3. Read what each guard SKIPS

- [ ] **A guard can be green while self-excusing** - skipping itself on the very files it is
      meant to cover. Open each guard's skip list and confirm it does not exclude the target
      class.
- [ ] **A syntax checker can be blind on certain file shapes.** Confirm the checker actually
      parses the construct you care about before trusting a clean exit.
- [ ] **The unrun gate is where the bug hides.** A guard that errored out early and exited
      zero is not a passing guard. Read the OUTPUT, not just the code.
- [ ] State the SET each guard covered. "Zero violations" is relative to a set.

## 4. Prove the tier-0 gate end to end - PRESENCE IS NOT FIRING

Do this whenever hooks or settings changed, and at least once per phase:

- [ ] Assert `.claude/settings.json` PARSES:
      `python -c "import json;json.load(open('.claude/settings.json'))"`.
      A single backslash in a Windows path makes it invalid; it never parses, NO hook
      registers, and nothing warns you. Eliminate this confound before concluding a hook did
      not fire.
- [ ] Confirm `core.hooksPath` is set and `.githooks/` is installed:
      `python scripts/install_hooks.py` is idempotent and FAILS LOUDLY if it cannot set it.
- [ ] **Stage a deliberate violation, attempt a REAL commit, assert HEAD is unchanged.** That
      is the only valid test. A hook that exists but does not fire is worse than no hook,
      because it is trusted.
- [ ] Remember the git hooks are AUTHORITATIVE and the Claude hooks are a CONVENIENCE layer -
      defense in depth. Neither one alone is trusted, so test both.
- [ ] Other confounds to eliminate before declaring a hook dead: an untrusted workspace
      silently discarding the allowlist in a headless run, and path-string keying - `C:\X`,
      `C:/X` and `C:/x` are three separate config entries and each worktree path is its own
      key.
- [ ] Hook findings are version-specific and EXPIRE. Re-measure; never inherit.

## 5. Report

- Every command run, with its exit code and the counts or violations observed THIS RUN.
- Every guard that is RED, with the specific violation and the file.
- Every guard that could not run, labelled as such - never rounded up to green.
- Whether the end-to-end hook test was performed this session, and its result.
