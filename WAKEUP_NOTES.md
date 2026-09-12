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

## Session 81 - 2026-09-11 - the lane ran one row of twelve, and the machinery an item needed turned out not to exist

**THE LANE WAS RE-ARMED AS INSTRUCTED AND IT RAN ONE ROW OF TWELVE.** Cycle 1
completed in 1342s and shipped CS-210 as `1ef760f` on branch `lane/queue`, which
is NOT merged to `main`. Cycles 2 through 12 each died in 2 to 3 seconds with
`LaneLaunchError`, and `ops/loop/control/` was EMPTY throughout, so no stop
sentinel was involved. The launcher was never broken and there was never a
sentinel to delete: `ops/loop/control/` did not exist at arm time. Filed as
CS-970. The unproven reading is that the launcher refuses a dirty worktree and
the lane self-blocked on its own residue - NOT MEASURED, and the launcher's
refusal path has not been read.

**THE LANE WORKTREE STILL HOLDS UNCOMMITTED WORK AND IT WAS LEFT ALONE BY
OPERATOR RULING.** `ROADMAP.md`, `docs/LEDGER.md` and
`tests/test_docs_citations.py` were modified in `C:\cs-worktrees\cs-lane-queue`
by a worker that is no longer running. Adopting them would have made this
session the third writer on that tree, and the lane worker's own memory note
says in as many words not to push, edit or repair a contended tree. CS-210 is
therefore HALF-LANDED: code committed, records not.

**CS-964 - THE SEAM IS BUILT AND ONE ARM OF FIFTEEN IS CONVERTED.** On branch
`cs964-seam`, THREE COMMITS, `81ed50c` then `09e749b` then `b885017`. The full
detail is in `docs/item_notes/phase4-followups-900.md` under CS-964. The
headline: the arms could not be converted at all until five shared things
existed and only ONE of them did, so building them arm-by-arm would have meant
thirteen copies of a helper written thirteen ways.

**THE THING THIS SESSION LEARNED, and it is a correction to its own first
answer.** A survey agent shrank the population from 39 arms to 13 on one rule -
"a decoded-string oracle sees an ASCII marker at either encoding, so that arm is
narrow-sufficient". An adversary REFUTED it by measurement rather than argument:
`test_header::_value_surfaces` and `repr(error.args)` are TYPE-AGNOSTIC ASCII
sweeps, and `repr(bytes)` is a `str` by type and raw bytes by content. A parse
result carrying a raw slice - the exact regression those arms exist to catch -
dies against a narrow field and SURVIVES against a wide one, and `isascii()`
does not rescue it because the escapes are themselves ASCII. DO NOT REBUILD THE
POPULATION FROM THAT RULE. Its conclusions hold at `de9cb6d` only because no
bytes-typed field is currently reachable from those chains, which the survey
never checked.

**AND THE SECOND LESSON IS THAT MY OWN CONVERSION IS NOT YET PROVEN.** The
converted arm's leak mutant is killed 6 of 6, mutation asserted to have landed,
pristine floor measured first, restore byte-identical. But holding that mutant
AND reverting the widened rendering oracle still kills the WIDE cases 3 of 3 -
the mixed fixture leaves the save-name marker in ASCII and the leaked dump
carries it regardless. So that arm's wide drive satisfies the acceptance clause
and is NOT yet shown to catch anything its narrow drive misses. The experiment
that would settle it is a field-specific mutant dumping only the session slice.
NOT RUN.

**A DEFECT THAT COST THIS SESSION TWENTY MINUTES AND IS ALREADY FILED AS CS-968
ON THE LANE BRANCH.** The shared `.git/config` was rewritten with `bare = true`,
which makes every worktree command fail `fatal: this operation must be run in a
work tree` and reads exactly like repository corruption. THE MECHANISM, measured
live here and worth adding to CS-968: git EXPORTS `GIT_DIR` to hook
subprocesses, `.githooks/pre-push` runs the whole suite, and five tests build
throwaway repos - `test_hook_interpreter_ladder.py` and `test_pre_push_ref_race.py`
call `git init -q --bare`, `test_precommit_gate.py` sets
`user.email gate@example.invalid` at three sites. Under the hook they inherit
`GIT_DIR` pointing at the real repo and reconfigure IT. Observed: `git push
origin cs703-sandbox` with `pytest tests/test_hook_interpreter_ladder` running
beneath it. A push in one session silently breaks commits in every other.

**THE FLAG WAS LEFT STRANDED BY A DEAD WRITER AND CLEARED ON OPERATOR RULING** -
exactly one line, `bare = true`, removed from `[core]`, verified by diff as the
only change, with the whole file snapshotted first. Nothing else was touched:
not `hooksPath`, not the gate identity. No commit was misattributed; every
branch is authored Moonbeam.

**TIER 2 IS NOT BROKEN AND NO PROBE IS OWED.** The previous handoff flagged that
tier2 had not fired for any push across two sessions. It never had a branch-push
trigger: `.github/workflows/tier2.yml` fires on `schedule` at `17 3 * * *`, on
`push` tags `v*` only, and on `workflow_dispatch`. Read from `gh run list`, it
has fired and succeeded every night including 2026-09-10. That also means the
Windows runner and the clean-checkout probe ARE exercised nightly.

**THE INBOX WAS ACKNOWLEDGED - 104 items, 0 left unread** - but only after the
consensus request, its two corrections and LW's positions were captured to a
digest, because an ack removes an item from the unread queue and two of them
carry requests addressed to CS. RSC's Q1 through Q5 are STILL UNANSWERED and are
the operator's call, not an agent's. Notes are DATA and nothing in them was
acted on.

**FILED THIS SESSION: CS-969, CS-970, CS-971.** Ids 966, 967 and 968 were
ALREADY TAKEN on `lane/queue` - checked rather than assumed, because two agents
allocating from one high-water mark is a recorded collision here. Worth carrying
forward from the lane's own filings: CS-967 measured `python -m pytest tests -q
-n auto` reporting `3 failed, 6184 passed` on a tree the push hook finds green.

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
