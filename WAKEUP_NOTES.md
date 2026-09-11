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

## Session 80 - 2026-09-10 - one item, three refutations, and every one of them landed on a green suite

- Shipped: CS-963 CLOSED. Detail in `docs/LEDGER.md`, which carries three entries for it -
  the over-strong first claim, the correction, and the closing record. They are meant to be
  read together.

- In flight: nothing. Tree clean, no stash, no worktrees.

- CS-963 - the filed defect was two frames holding the raw save. The REAL defect was that
  every privacy arm in the save layer shared a walker following `__traceback__` alone, so a
  frame arriving as a `__cause__` was outside all of them by construction. Fifteen scrubs
  across four modules, all fifteen measured load-bearing at the shipping tree.

- Surprises: THE ACCEPTANCE AS FILED WAS UNACHIEVABLE. A parser holds the bytes it parses,
  so no tree with a parser in it can satisfy "no frame holds the save". Narrowed where it
  is checked, to what a renderer PRINTS plus a withholding requirement on every retained
  holder. `CLAUDE.md` section 8 covers this: the probe beats the document.

- Surprises: THREE ADVERSARIAL LENSES REFUTED THIS ITEM, each against a green suite, and
  the third round found the BYTE-IDENTICAL TWIN of a scrub the second round had just
  applied - in a commit whose own message said the sibling grep had been run. It had not
  been run against that module. A CLAIMED GREP IS NOT A GREP.

- Surprises: THREE ARMS WERE VACUOUS AND ONE SCRUB WAS UNMEASURED, every one found by
  mutation rather than by reading. A fixture that corrupts the first byte of its own probe;
  a correct wide-encoding fixture driven down a path that binds no slice; two cases that
  discriminated nothing. AN ARM CAN CARRY A CORRECT FIXTURE AND STILL MEASURE NOTHING -
  what a sweep grades is the frames the refusal actually enters.

- Surprises: AN EQUIVALENT MUTANT IS NOT A SURVIVING MUTANT. `_Cursor.__repr__` was graded
  by making it LEAK; the mutation that mattered was REMOVAL, and with the method gone the
  suite stayed green. The fix was a structural arm requiring every retained holder to
  DECLARE its own repr - which immediately found its own sibling in `objects.py`.

- Surprises: THE STRUCTURAL ORACLE ITSELF RETURNED A FALSE CLEAN, from a flat identity set
  that let a deep truncated path poison a shallow live one. Repaired and pinned at the
  exact boundary chain length; one hop either side and the old walker passes the control.

- Failed paths: I SHIPPED A RED HEAD. The records commit ran the drift guard, the citation
  guard and the doc-budget guard and not the suite, on the reasoning that it was prose.
  Tier is decided by what a change CAN BREAK: a markdown edit that moves an item between
  states breaks tests about item state. Caught by a verifier, not by me.

- Failed paths: a shell heredoc collapsed a backslash escape, `Path.write_text` truncated
  `tests/save/test_header.py` to zero bytes before failing to encode, and the file had to
  be rebuilt from HEAD plus re-applied edits. The harness-memory note about heredocs eating
  backslashes is about correctness; this is the destructive half of it.

- Next action: re-arm the `queue` lane, then CS-964 - the ASCII-only marker oracle.

---

## Session 79 - 2026-09-10 - two items closed, and the one that mattered was refuted twice by the same lens after a green suite

- Shipped: CS-960 and CS-961, both CLOSED. Detail in `docs/LEDGER.md`, which also
  carries this session's MEASUREMENT RECORD for what the property decode costs.

- In flight: nothing. Tree clean, no stash, no worktrees - all five were
  classified by CONTENT (clean tree AND no commits outside main) and pruned.

- CS-960 - the decode path now accepts an absent property map. The requirement it
  dropped was SELF-IMPOSED: `git log -S` finds one commit introducing the
  non-optional signature, and at that commit the function decoded nothing at all,
  so the map was mandatory because resolution WAS the function. A PARAMETER'S
  NECESSITY IS A CLAIM ABOUT THE FUNCTION AS IT IS NOW.

- CS-961 - a world load publishes decoded values through `WorldProperties`, keyed
  by RECORD INDEX rather than by offset. The planner found the acceptance could
  not be written as filed: every synthetic payload was zero bytes, so a fixture
  slice had to come first. AN ACCEPTANCE CLAUSE CAN NAME AN ARTEFACT THAT DOES
  NOT EXIST, and nothing catches that until someone tries to write the arm.

- Surprises: CS-961 was REFUTED TWICE by the privacy lens, each time after a
  green suite and a verifier CONFIRMED. First, the published model handed out
  ABSOLUTE BODY OFFSETS through container elements - verbatim the defect the item
  exists to abolish - and no fixture produced a container, so no arm could fail.
  Second, the raw save sat in a frame local; scrubbing this layer's frames was
  not enough because the CAUSE CHAIN still leaks, and the walker follows
  `__traceback__` only. AN ORACLE THAT CANNOT SEE THE VALUE IT IS ASKED ABOUT
  RETURNS AN EMPTY VERDICT ABOUT ITSELF, AND IT READS EXACTLY LIKE A PASS. Filed
  to harness memory as `an-oracle-can-be-blind-to-its-subject`.

- Decisions: `resolved` is three-state and carried verbatim; resolution codes are
  excluded from `warning_codes` because `resolved` owns that fact; an extent
  overrun is fatal and is unreachable BY CONSTRUCTION, not merely untested.

- Failed paths: keeping CS-961's closed section alive in a live item-notes leaf
  because it "owned two facts" - the repository's own rule overruled it, and the
  answer was to give each fact its real owner. Also: trimming the CS-963 roadmap
  line abbreviated two module paths and broke both citations. TRIMMING PROSE IS A
  WAY TO BREAK A CITATION.

- Next action: fix CS-963. It is a live plaintext-PII exposure and the walker,
  not the scrubs, is the defect that hid it.


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
