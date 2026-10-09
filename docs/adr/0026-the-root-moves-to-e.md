# 0026 - the root moves to E:, and a junction stays at C:

## Status

`accepted` - 2026-10-08

**ACCEPTED ON THE OPERATOR'S OWN WORDS**, in this repository's own main session, under
CS-1275. The `CLAUDE.md` section 7 settled entry "Name is Clockspeed, root is ..." is
reversible only that way and then only with an ADR; this file is that ADR.

This ADR is IN FORCE and binding. Cite it freely.

## Context

**THE FENCE BEING CROSSED.** `CLAUDE.md` section 7 settled the name and the root together,
with the root at `C:\Clockspeed`, reversed by "only the operator's own words in the main
session (section 6.1 - no adjudicator and no MAIN note stands in), then recorded as an ADR".
The operator's words, in this repository's main session: session 129, "yes I want to do the
move to E:"; session 130, "do the move to E:". ONLY THE ROOT HALF REVERSES. The name is
unchanged, and so is the folder name.

**THE RUNBOOK THAT NEVER CAME.** CS-1275 was filed to move "per MAIN's runbook". MAIN 2155
ordered an inventory only, and no runbook had arrived by session 130. Five sibling fleet
trees had already moved to E: without one, and each left a directory junction at its old C:
path pointing to its E: path.

**THE ALTERNATIVES, AND WHAT EACH COST.**

- **Wait for MAIN's runbook.** Rejected. The operator ordered the move in own words, the one
  authority the reversal clause names, and the siblings moved without a runbook. Waiting
  buys nothing the inventory and the sibling pattern do not already give.
- **Move with no junction at C:.** Rejected. A C: reference the inventory missed - a
  scheduled task's command line, a shortcut, MAIN's delivery path into this tree - would
  break silently instead of keeping working.
- **Move the flip-backup folder too.** Rejected. It holds the sole copy of the pre-rewrite
  graph bundle, which is irreplaceable; it already sits outside the root, as the CS-700
  plan's S5 asks, and nothing gains from moving it. A copy step is risk to the only copy
  for no benefit. AMENDED 2026-10-09 by CS-1293: the folder then sat on C:; MAIN's
  2026-10-08 sidecar move put it at `E:\Sidecars\CS\Scratch\cs-flip-backup`, its current
  home under the single CS sidecar folder.

The fleet-shared slot root under ProgramData that `ops/loop/slots.py` names is not this
tree's and does not move.

## Decision

1. **THE ROOT IS `E:\Clockspeed`.** The name and the folder name are unchanged.
2. **THE MOVE, AS EXECUTED 2026-10-08 IN SESSION 130**, each step named by what was read
   back after it:
   a. INBOX_STOP restored in the lane control directory and the inbox status read back
      idle BEFORE any file moved (the Q4 scope ruling).
   b. robocopy of the whole root to `E:\Clockspeed`: 32813 files, 0 failed.
   c. `scripts/install_hooks.py` re-run on E:; `core.hooksPath` read back `.githooks`.
   d. `git worktree repair` over every worktree; 37 worktree lines read back, all on E:.
   e. The old cs-lane-queue lane worktree classified by content - clean, its tip an
      ancestor of `main`, ignored caches only, superseded by the CS-1274 `lane-<i>` layout
      - as NOT NEEDED, sent to the Recycle Bin, then `git worktree prune`.
   f. The one remaining worktree of the old C: slice-worktree folder (cs-g06, REVIEW, one
      unique commit, clean) copied to a slice-worktree folder on E:, and the C: folder
      sent to the Recycle Bin. AMENDED 2026-10-09 by CS-1293: MAIN's 2026-10-08 sidecar
      move put cs-g06 at `E:\Sidecars\CS\Worktree\cs-g06`, its current home under the
      single CS sidecar folder; the E: folder this step copied it to no longer exists.
   g. The external pointers re-pointed and read back on E:: the inbox responder's
      scheduled task arguments, the three Desktop shortcuts, Claude Code's trust entry
      and per-path memory store for the E: path.
3. **A CUTOVER STEP FOLLOWS** once the session that ran the move exits, because that
   session holds `C:\Clockspeed` as its working directory and cannot remove it: it sends
   `C:\Clockspeed` to the Recycle Bin and leaves a junction from `C:\Clockspeed` to
   `E:\Clockspeed`, the sibling trees' pattern. A
   scheduled task runs it every ten minutes until it succeeds, refuses if the C: copy
   holds a commit E: lacks, first copies any note delivered to the C: path in between,
   then lifts INBOX_STOP and deletes itself.
4. **THE MOVE COMMIT CARRIES** this ADR and the live root text: `CLAUDE.md` sections 2 and
   7, `BOOTSTRAP.md`, the `.claude/commands/done.md` shortcut check, and two comments
   under `ops/loop/`. History records keep the C: path they recorded.

## Consequences

- **Easier:** the lane worktree base has been derived from the repo root since CS-1274, so
  lanes now land beside `E:\Clockspeed` with no further edit.
- **Kept working:** every C: reference the inventory missed, including MAIN's delivery
  path, resolves through the junction.
- **Owed:** the CS-G03 clean-machine re-walk runs at a tip at or after the move commit,
  a hard precondition of CS-700 step a (the Q2 scope ruling).
- **Foreclosed:** re-pitching the old C: root. The junction is a compatibility path, not a
  second root - nothing new is written against C:.
- **Revisit if** the junction is removed: every C: reference then fails, so a removal
  starts from a fresh inventory of them.
