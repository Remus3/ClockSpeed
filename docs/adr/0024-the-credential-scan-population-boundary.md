# 0024 - the credential-scan population boundary is publication, not location

## Status

`accepted` - 2026-09-24

**ACCEPTED BY ADJUDICATOR RULING 2026-09-24**, session 113, on CS-1168. The ruling was made
by an agent that authored none of the slice that wrote this file, which is the condition
`CLAUDE.md` section 5 puts on grading. The ruling chose DECLINATION over widening; this file
records that choice and is what closes the item.

This ADR is IN FORCE and binding. Cite it freely.

## Context

**THE INCIDENT.** A plaintext key sat for ten days in a file that was never committed, and
nothing in this tree saw it. Every credential scan here reads a population defined by
git: the commit gate grades the STAGED set (`tools/precommit_gate.py::staged_paths`), the
repository sweep grades the TRACKED set and every blob reachable from a ref
(`tests/secret_sweep_guard.py::tracked_paths`, `tests/secret_sweep_guard.py::reachable_blobs`),
and the outbound gate grades the payload of a note about to leave
(`tools/outbound_gate.py::scan`). The exposed file was in none of them, and it sat OUTSIDE
this tree's root, in a scratch directory the whole fleet shares.

**WHY THE QUESTION HAD TO BE SETTLED BEFORE ANY SWEEP WIDENED.** The obvious fix - point a
sweep at the directory where the key sat - crosses two lines this tree holds. That
directory is not this project's, and a sweep reading it reads files sibling trees wrote,
which collides with the rule that a tree never reads a sibling's files. And a boundary
drawn as a list of directories rots the first time a tool writes somewhere else - the same
defect as an allowlist wearing a guard's clothes. So the RULE had to come first.

**THE ALTERNATIVES, AND WHAT EACH COST.**

- **Widen to the shared scratch directory.** The only widening that would have DETECTED
  the incident, and it reads a sibling's files. Foreclosed by that rule, not by cost.
- **Widen to an unbounded filesystem walk.** This machine has already recorded a runaway
  process filling a disk and a walk that descended where it should have stopped. An
  unbounded walk has no stopping rule, and it too reads sibling trees.
- **Widen to untracked, non-ignored files inside the root - the runner-up.** Cheap and
  bounded by the working tree. It LOST because it would NOT have detected the motivating
  incident, which sat outside the root, and because the commit gate already reads those
  files at the one step where they can leave through this repository.
- **Widen to gitignored files inside the root.** Those are where credentials are REQUIRED
  to live - the local environment file and the local connector configuration are ignored
  precisely so a secret has somewhere correct to sit. Scanning them flags correct storage.

**THE HALF THAT IS NOT OURS.** A machine-wide at-rest sweep is a fleet control with one
owner and several beneficiaries. Implemented once per repository it becomes five
populations that disagree and five schedules to forget.

## Decision

**This tree's credential scans read exactly the bytes this repository can PUBLISH. The
boundary is publication, not location.** A byte is in scope if and only if it can leave
through one of this repository's own publication paths: a commit and the push that
carries it, or an outbound note this tree sends. So the populations are the git index
population - the staged set at commit, the tracked set and the reachable history on sweep
- and the outbound payload at send. No directory is named, because the rule names none.

**WHAT STAYS INVISIBLE, AND WHY - stated rather than left to be discovered:**

1. **Everything outside the worktree root**, including the shared scratch directory where
   the incident key sat. That space belongs to a sibling or to the fleet, and a sibling's
   files are never read from here.
2. **Gitignored files inside the root.** That is where credentials are required to live;
   scanning them would flag correct storage.
3. **Untracked, non-ignored files inside the root.** The commit gate reads them at staging,
   the only step at which they can leave through this repository.

**THIS IS A DECLINATION, AND IT CLOSES CS-1168.** No sweep widens. The item's acceptance
names either outcome as closing it; the arms and the measured cost it lists bind a
WIDENED sweep, and none is built. A declination needs no measured cost.

**THE FLEET HALF IS ROUTED OUTBOUND, NEVER IMPLEMENTED HERE.** The at-rest population and
its schedule belong to the fleet. This tree owns the detection RULES and the arms that
grade them, and offers those rules to a fleet sweep through a note to the sync inboxes; the
item does not wait on the note being answered.

## Consequences

- **Easier:** every scan here stays bounded by the git index or by a payload, so its cost
  is bounded by what the repository holds, and no scan reads a byte another tree wrote.
- **Harder, and accepted:** a credential written to disk anywhere outside the index - in
  this root or beyond it - is invisible to this tree until someone stages it. The incident
  shape is NOT detected by anything here, and this ADR says so rather than implying
  otherwise. Detection of that shape is the fleet's at-rest sweep or nothing.
- **Foreclosed:** a path list as a scope boundary, and any scan in this tree that reads
  outside its root. A proposal to widen must first supersede this ADR, and must then carry
  what CS-1168's acceptance requires of a widened sweep: an arm detecting a plant INSIDE
  the new boundary, an arm reporting a plant OUTSIDE it as NOT COVERED rather than passing
  silently, a control proving the staged set is still read, and a MEASURED cost.
- **Revisit if a premise changes:** if this repository gains a publication path that is
  not a commit or an outbound note - an uploaded artifact, a release asset, a published
  page built from the working tree - that path's bytes join the population under the same
  rule, and the scan that reads them is owed before the path ships.
