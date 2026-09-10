# Wakeup notes

**Section status: LIVE.** A dated heading in this file records provenance - when the
text was filed, moved or measured - and never that the section itself is historical.

**The last two to three sessions at full fidelity, newest first. Nothing older.** When a
fourth session lands, the oldest entry is moved to `docs/history_notes.md` - relocated,
never deleted.

This file is read at session start, alongside `CLAUDE.md`, the memory index, `ROADMAP.md`
and `docs/ARCHITECTURE.md`. It is refreshed by the `/done` ritual at the end of every
session, not written incrementally during one.

It holds what a fresh session cannot recover from the code and the git log: what was
actually in flight, what was tried and abandoned, and what the very next action is. It
does not hold per-item completion records - those are ledger entries and belong in
`docs/LEDGER.md`.

## Entry format

```
## Session <n> - <YYYY-MM-DD> - <one-line focus>

- Shipped: item IDs closed this session. Detail in docs/LEDGER.md, not here.
- In flight: what was left mid-work, where it stands, and what it is blocked behind.
- Decisions: ADRs recorded this session, by id. Detail in docs/adr/.
- Surprises: anything that contradicted a spec, and which file was updated as a result.
- Failed paths: what was tried and abandoned, and why - so it is not retried next session.
- Next action: the single first thing the next session does.
```

Keep every entry to that shape. If an item needs a paragraph, it needs its own file and
the line becomes a pointer.

---

## Session 78 - 2026-09-09 - a premise this project had built on was refuted in its own tree, and the dashboard turned out to be a self-diagnostic

- Shipped: nothing CLOSED as an ITEM. CS-962's slice S0 merged. CS-960, CS-961
  and CS-962 FILED. Detail in `docs/LEDGER.md`.

- In flight: nothing. Tree clean, no stash. Two adversary worktrees survive on
  disk under `.claude/worktrees/`, both clean and detached.

- THE SESSION WAS SENT AT THE DASHBOARD AND FOUND THE DASHBOARD WAS NOT THE
  PROBLEM. Three parallel read-only surveys established that the page is a
  SELF-DIAGNOSTIC: it renders its own health, its own route table, six world
  scalars and five counts. `/api/registry` is fetched every refresh and only
  its HTTP STATUS reaches the DOM. `/api/solve` and `/api/optimize` answer 200
  against real data and the page never calls them. `advisor/`, `audit/` and
  `progress/` contain NO executable code at all - four docstring-only files.

- THE FINDING THAT MATTERS IS THAT A USMAP IS NOT NEEDED TO DECODE A SAVE, and
  it was settled IN THIS TREE rather than read off a third party. All four uses
  of the `property_map` parameter below `read_properties` are a membership test
  on a class name the stream already carries, or the parameter being passed
  through or deleted for privacy. A probe decoded one synthetic payload twice,
  the second time with a map holding ZERO schemas, and got the same 17 values
  with identical references and struct interiors.

- THE RECORDED REASON WAS STALE AND PROVABLY SO. The docstring justifies the
  mandatory map as a layering choice. `git log -S` finds exactly one commit
  introducing that signature, and at that commit `read_properties` DECODED
  NOTHING - the schema lookup was the whole function. Decoding came later and
  the signature was never revisited. A PARAMETER'S NECESSITY IS A CLAIM ABOUT
  THE FUNCTION AS IT IS NOW. The tree's own prose already said the mapping is
  not an input to the decode; nobody had acted on it.

- Decisions: no ADR. Four operator rulings on CS-962 and a licence gate over
  five save-parser candidates, all recorded with their fences in
  `docs/LEDGER.md` and `docs/item_notes/phase4-followups-900.md`.

- Surprises: nothing contradicted `BOOTSTRAP.md`. The refuted premise lives in
  a docstring and an item note, not in the specification.

- Failed paths: none abandoned. One brief was WRONG and the builder said so
  rather than building to it - the route-table defect was already half-guarded.

- Next action: dispatch CS-960. It is the smallest item with the largest
  consequence and it is sized for one row.

---

## Session 77 - 2026-09-08 - the red CI was a Windows assumption, and every claim this session made was refuted before it was believed

- Shipped: nothing CLOSED as an ITEM. CS-958's F1, F4, F5, F6 and F8 closed
  inside it; the item stays OPEN on F10, D4 and D6. Detail in `docs/LEDGER.md`.

- In flight: nothing. Tree clean, no stash. One adversary worktree survives at
  `.claude/worktrees/agent-af6f0393f63bd2adb`, clean, at `519cadf`.

- THE SESSION OPENED ON RED CI AND THE CAUSE WAS ONE ASSUMPTION IN EIGHT
  PLACES. Slice S1's arms encoded WINDOWS filesystem semantics as universal:
  no `mklink` on ubuntu, a trailing dot not stripped, a case-SENSITIVE
  filesystem, and a JSON encoder that does not double a forward slash. Repaired
  by making each arm measure its OWN platform's mechanism - a junction here, a
  symlink there - and never with `skipif`. CI green, and the passed count rose
  by exactly the number of arms while the skip count did not move.

- FOUR REFUTATION PASSES, FOUR VERDICTS AGAINST, AND EVERY ONE WAS RIGHT. Three
  adversaries on the S2 candidate and one verifier on the commit phase. They
  found: an ungraded STAGED filename that a length-floor rule refuses, the
  gate's WARN tier dropped on the floor, two refusals that were byte-identical
  about different faults, a discarded locate hint, refusals that named nobody,
  a full suite red on a citation guard the targeted suite cannot see, an exit 1
  printed beside NOTE ALREADY DELIVERED, and a dry run that wrote to disk.

- FOUR MUTANTS SURVIVED ALL 36 ARMS OF THE FIRST S2 CUT, and the reasons
  transfer better than the fixes. Every fixture put its dirty value at batch
  index 1, so line attribution was never exercised. Every arm passed
  `--allow-unmeasured`, so a documented precedence was never reached. The WARN
  tier is structurally unreachable from this suite. And one mutant was
  EQUIVALENT rather than surviving - the delivered filename is a strict PREFIX
  of the staged one and no scanning rule is end-anchored, so no VALUE can tell
  them apart and the property had to be measured structurally with a recording
  spy.

- Decisions: no ADR. The exit-code set gained a fourth member so that 1 can go
  back to meaning nothing was written; the fence is in `docs/LEDGER.md`.

- Surprises: nothing contradicted `BOOTSTRAP.md`. No spec update is owed.

- Failed paths: dispatching a mutating adversary into the main checkout beside
  read-only siblings. Stopped it before it wrote and re-dispatched it into a
  worktree - a mutation there would have made both sibling verdicts statements
  about an unknown tree.

- Next action: read the continuation prompt. The responder-runner filings were
  DRAFTED and deliberately NOT filed on an operator standby ruling.

---

## Session 76 - 2026-09-08 - the repaired sender was refuted on all four lenses, and the second cut's fault was the evidence rather than the code

- Shipped: nothing CLOSED. CS-958's slice S1 merged and the item stays OPEN.
  CS-959 FILED. Detail in `docs/LEDGER.md`, not here.

- In flight: nothing. Tree clean, no worktrees, no stash.

- THE SESSION DID EXACTLY WHAT SESSION 75 HANDED IT AND THE ANSWER WAS YES.
  Four adversaries, four REFUTED verdicts, nine defects in a tool this project
  had already called repaired once. Four demonstrated defects in a first cut is
  a reason to expect the second cut is not clean; it was not.

- THE SEVERE FINDING INVERTS THE TOOL'S PURPOSE. `grade()` takes bytes only, so
  a note's FILENAME and a destination's NAME were never graded. The value the
  gate REFUSES in content ships as a filename into every sibling inbox and is
  recorded `gate_verdict: CLEAN`. The gate was in front of the payload and
  beside everything else.

- S1 MERGED AND ITS OWN FIRST CUT WAS REFUTED FIRST. The mechanism held against
  a junction, a two-deep chain, an inbox-level junction, a subst drive and a UNC
  root. The suite did not: three of four subtle mutants shipped a green 40 of
  40, two restoring a measured finding of this item verbatim.

- TWO EVIDENCE FAILURES WORTH CARRYING PAST THIS ITEM. A fixture built parallel
  to the implementation is the shape that makes an arm agree with a bug - the
  `.resolve()` mutant survived because pytest resolves `basetemp`. And a
  monkeypatch that supplies the value under test converts an integration
  property into a unit tautology - both arms patched `REPO_ROOT`, so the clause
  was graded and the binding never was, while a copy running from a worktree
  still delivered into the real inbox.

- Decisions: none needing an ADR. F1/F2/F3 were decomposed as TWO ORDERED slices
  rather than three parallel ones; the fence is in the ledger entry.

- Surprises: none contradicting `BOOTSTRAP.md`. No spec update is owed.

- Failed paths: `cd` into `moon_sync_inbox` to read a note bricked every shell
  call for the rest of the turn, because the hooks resolve their own script path
  from cwd. The memory that covers it named worktree removal as the trigger and
  recommended a shim recovery that would have meant writing into a sibling's
  inbox. Both corrected.

- Next action: REFUTE THE S1 REPAIR. It answered an adversary and has had no
  adversarial pass of its own, and it introduced an asymmetry it named but did
  not resolve.
