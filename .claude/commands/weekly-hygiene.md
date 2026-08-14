---
description: Light maintenance - trim notes, scan memory staleness, triage anomalies. Relocate, never delete.
argument-hint: [scope, e.g. notes | memory | anomalies | all]
---

# /weekly-hygiene

Scope: $ARGUMENTS (default: all three passes)

Light maintenance, run on a cadence. This is a RELOCATE pass, not a delete pass. Nothing
here is allowed to close a work item - hygiene never drains a backlog.

## 1. Trim the notes

- [ ] `WAKEUP_NOTES.md` keeps the last 2-3 sessions at FULL fidelity. Move everything older
      to `docs/history_notes.md` verbatim. Relocate, do not delete.
- [ ] Collapse narrative in the index files - `ROADMAP.md`, `BACKLOG.md`, `docs/GATED.md`,
      `docs/LEDGER.md` - to one line per item plus a pointer to its own file where the detail
      is genuinely needed. An index that reads like an essay stops being scanned.
- [ ] Check the size budgets: `CLAUDE.md` and any auto-loaded file under 40 KB (hard),
      `memory/MEMORY.md` under 20 KB (hard), `memory/*.md` leaves under 6 KB (warn),
      `ROADMAP.md` under 60 KB (warn). Over budget means relocate to a sub-index and leave a
      one-line pointer.
- [ ] Move any dated artifact to `docs/_archive/` and confirm `.rgignore` excludes it so it
      never pollutes a search for current truth.
- [ ] A heading carrying an explicit DATE marks its own section historical - leave it alone,
      do not update it, do not audit it as current.

## 2. Scan memory for staleness

- [ ] List every `memory/*.md` with its last-modified date. **Check a row's AGE before
      building on it** - a memory filed months ago may describe code that no longer exists.
- [ ] For each memory older than the cadence, verify the fact against the ARTIFACT: the code,
      `git log`, a live probe. Not against another doc.
- [ ] Wrong memories are DELETED, not softened. Superseded memories are UPDATED IN PLACE, and
      the update records what it replaced - a superseded rule that is silently deleted comes
      back.
- [ ] Duplicates merge into the existing file. Check for an existing file covering the fact
      before creating a new one.
- [ ] Frontmatter valid: `name`, `description`, and `metadata.type` one of
      `user` / `feedback` / `project` / `reference`.
- [ ] `feedback` and `project` entries carry **Why:** and **How to apply:**. A rule without
      its why gets re-litigated.
- [ ] Relative dates converted to ABSOLUTE dates.
- [ ] Nothing stored that the repo already records - code structure, past fixes, git history,
      content already in `CLAUDE.md`.
- [ ] Every memory reachable from `memory/MEMORY.md` or an `INDEX_<domain>.md`. **Do not
      unindex a file to save bytes.** Hook lines in the index are SHORT - the index is
      scanned, not read.
- [ ] Re-run `py -3 tools/memory_sync.py`. The sync is idempotent - it updates in place by
      category plus key and never duplicates.
- [ ] Verify recall coverage, not health. **A "healthy" status is NOT proof recall works** - a
      store can report healthy while most rows have no embedding, silently degrading recall
      to keyword matching. Only `embedded == active` proves coverage. Run the `--verify` mode
      and report the numbers.

## 3. Triage anomalies

- [ ] Read the logs and any anomaly or error file since the last hygiene pass. Group by
      MECHANISM, not by message text.
- [ ] For each group: is it a known class, a new bug, or noise? A new bug gets an ID
      (`CS-nnn`) and a line in `ROADMAP.md` with an acceptance criterion. Noise gets a filter
      and a note saying what was filtered and why.
- [ ] Check `docs/GATED.md`: has any external condition CHANGED? An unblocked item moves back
      to `ROADMAP.md`. **Never close a gated item synthetically** - substituting a proxy for
      the external condition is the single most common way a gated backlog gets falsely
      drained.
- [ ] Check `BACKLOG.md` conditional triggers: has any trigger fired? A fired trigger promotes
      the item to `ROADMAP.md` with an ID and acceptance criteria.
- [ ] Re-probe the environment facts that could have drifted: game build string, the tracked
      content-hash pin, port band 8900-8911 free, `py -3` resolving, ruff / pytest / mypy
      present. Run `py -3 scripts/verify_env.py` and record the exit code.
- [ ] If the game patched, the version pin guard is RED by design. File the re-extract as a
      work item rather than silently re-pinning.

## 4. Report

- Notes trimmed and where they went. Budgets, with the observed sizes.
- Memories verified, updated, deleted, with the reason for each deletion.
- `embedded` and `active` counts observed THIS run.
- Anomaly groups with their triage decision and any new item IDs.
- Gated items whose condition changed; backlog triggers that fired.
- `verify_env.py` exit code and any environment drift found.
- Anything you could not verify, labelled unverified.
