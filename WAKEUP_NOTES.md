# Wakeup notes

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

## Session 30 - 2026-08-22 - CS-806 and CS-442 both CLOSE; each was larger than filed, and each closed an unimplemented clause rather than the typo it was reported as

- **Shipped: CS-806 and CS-442, both CLOSED, both tier 1, both pushed with tier1 CI SUCCESS
  READ rather than predicted.** `6e37a11` and `ae25547`. This ends three consecutive sessions
  that closed nothing. Detail in `docs/LEDGER.md`, not here.

- **BOTH ITEMS WERE BIGGER THAN THEIR FILING, AND IN THE SAME WAY: a rule was already written
  down and simply never implemented.** That is worth carrying forward as a pattern rather than
  as two anecdotes. CS-806 was filed as a docs typo; `BOOTSTRAP.md` section 2.5 has required
  since the FIRST COMMIT that `verify_env` assert the RESOLVED interpreter can import pytest and
  ruff and HARD-fail if it cannot, and nothing did. CS-442 was filed on one dead citation; the
  item was that NOTHING IN THE REPOSITORY READ `docs/` at all.

- **CS-806's detail block was SUPERSEDED and the ledger says so.** It told the closer to "decide
  whether that contract is the right one" - but the contract had already been decided in
  `BOOTSTRAP.md` 2.5 before any code existed, so it was not a live design question. Both detail
  blocks now carry a CLOSED marker in `docs/history_notes.md` so neither reads as a live
  instruction again.

- **CS-442's population is EIGHT, not the recorded seven, and the eighth is the shape the item
  itself predicted would be missed.** `test_the_header_scan_advertises_no_bound_it_cannot_enforce`
  is cited by the CS-436 entry BARE, with no path, so a `path::name` scanner is structurally
  blind to it. Its target is not an inference: `ee36d0d`, the CS-436 commit, added it alongside
  the live sibling the same Verification field cites. The "seven is a FLOOR" caveat is discharged.

- **A NINTH CANDIDATE WAS REJECTED, and the near-miss is the lesson.**
  `clockspeed/save/objects.py::_BYTE_ORDER_CANNOT_SEPARATE_VALUES` reads dead to any resolver
  that looks for `def` alone, and is a live module-level CONSTANT. It was briefly counted as an
  eighth dead citation off a TRUNCATED `grep` whose first ten hits were all worktree copies.
  Checking the tracked file directly is what reversed it. Same artifact class the item already
  recorded on the `file:line` arm, arriving on the other one.

- **A TRAP FOUND THIS SESSION THAT WAS RECORDED NOWHERE: a citation can assert an ABSENCE.** The
  CS-411 correction record cites a dead name ON PURPOSE - `grep -c` returning 0 IS its evidence -
  so a checker that reddens on every dead name reddens on a record doing exactly the right thing.
  That is the `DELIBERATE` disposition in `tests/test_docs_citations.py` and it is load-bearing.

- **Decisions: no ADR. Two dispositions recorded that must not be re-opened as questions.**
  CS-442's class-3 citation gets NO TARGET, because CS-441 records 26 of 46 spliced shapes still
  escaping - assigning one would launder an aspirational claim into a verified pointer. And
  `docs/history_notes.md` is deliberately NOT guarded, because its detail blocks QUOTE dead names
  while discussing them; that is CS-809, not an oversight.

- **Surprises: nothing contradicted `BOOTSTRAP.md`.** The opposite - `BOOTSTRAP.md` 2.5 was
  RIGHT and the code was behind it. Two tracked docs were corrected against ground truth per
  CLAUDE.md section 8: `docs/OPERATIONS.md` claimed "`py -3` is equivalent on this machine",
  which was false and contradicted 2.5; and CS-806's own detail block, above.

- **Failed paths, so they are not retried:** a naive `path::name` census that resolves only `def`
  manufactures a false finding on a live constant. A `file:line` arm that judges an unqualified
  basename manufactures six. Neither is a checker bug to fix later - both are DECLINED-and-printed
  by design now. Also: the harness bash heredoc ate backslash escapes FOUR separate times this
  session, silently corrupting patch scripts; the working answer is the Write tool, every time.

- **In flight: NOTHING.** Working tree clean, nothing unpushed, both CI runs green. The four
  pre-existing worktrees (CS-492 rounds seven to nine and the two-site spike) and branch
  `cs807-attribute-half` are UNTOUCHED and still unmerged.

- **Next action: CS-702, but it is BLOCKED ON AN OPERATOR GRANT and must not be started without
  one** - `.githooks/commit-msg` is frozen. If the grant is not forthcoming, take CS-809 or
  CS-810, which are CS-442's residuals and need no grant.

## Session 29 - 2026-08-22 - CS-807's sweep is TAKEN and sizes the item at SIX; an attribute-half repair was built and REFUTED by three independent lenses

- **Shipped: NOTHING CLOSED. Third session running.** CS-807 stays OPEN, CS-492 was not
  touched, and CS-808 was FILED. Two commits, `77336e5` and `6547f9f`, both DOCUMENTATION
  ONLY - zero `.py` files were touched in `main`. `docs/LEDGER.md` carries a NON-CLOSURE
  record and says so in its heading.

- **THE SWEEP IS TAKEN, and it was the right first action because it changed the item's
  size.** CS-807's detail block named it the cheapest next step and recorded the answer as
  unmeasured. The answer is **SIX false declarations, not four, in TWO modules rather than
  one**: `backing_citations` and `dead_full_citations` in `tests/save/test_absolute_claims.py`
  are the new pair, and **both are HELPERS rather than tests**, so the population is not
  confined to test functions the way the first finding implied. 45 exemptions in 11 modules,
  20 graded entries in 7; the graded channel is CLEAN. No consumer of the guard exists
  outside `tests/save`. **Six is a FLOOR, not a total.** Full tables in
  `docs/history_notes.md` under **CS-807 - detail**.

- **TWO INDEPENDENT METHODS AGREED ON THE SAME SIX and the second never reads a reason
  string** - it takes the call node the guard trips on, resolves the callee one hop, and asks
  whether that target reaches. One phrase match was REJECTED on inspection:
  `test_workdir::test_latest_save_returns_none_when_nothing_resolves` matches "no path at
  all" but genuinely calls the locator.

- **In flight: branch `cs807-attribute-half` at `72f0f2c`, base `77336e5`, REFUTED and NOT
  MERGED.** +242/-25 across three files. The working tree is CLEAN and nothing is unpushed;
  the branch is the only artifact. The four pre-existing worktrees (CS-492 rounds seven to
  nine and the two-site spike) are UNTOUCHED.

- **Failed paths - the whole of the repair attempt, and the framing that produced it.** The
  sweep showed the six splitting by mechanism: four on the bare-name arm already measured
  irreducible, two on the ATTRIBUTE arm where `_callee_resolves` discards a receiver the
  import table resolves without type resolution. **That was reported as the tractable half
  and it is not.** Two narrowings were built and both were refuted, both for reading an
  ABSENCE as evidence of safety - the first that the sibling exported no reach, the second
  that a def's own body names no primitive. **Do not take a third of the same shape without
  an answer to that root cause.**

- **THE GRADING WAS DONE BY THREE AGENTS THAT DID NOT PRODUCE THE BUILD, and all three
  returned REFUTED.** Permissive-failure found seven escapes, each caught on the parent
  commit and silent on the build. Control-validity found the build's anti-vacuity control
  passes with `_assert_library_reach_is_declared` gutted to a bare `return`, with ZERO unique
  detection against a 16-mutant battery. Claim-accuracy found `_module_handles`' docstring
  stating the polarity of the REFUTED first spike, and a FOURTH reach-computation site.

- **Surprises: NO SPIKE CONTRADICTED `BOOTSTRAP.md` this session.** But two measured facts
  contradicted a TRACKED DOC and the doc was corrected per CLAUDE.md section 8: ROADMAP's
  CS-807 acceptance said "the four exemptions in `test_oracle_citations`" and the sweep says
  six across two modules; and this session's own claim that the attribute half was tractable
  was refuted by its own grading and is now fenced in the detail block.

- **Two defects worth carrying forward whatever happens to the direction.** The exoneration
  was keyed on a bare receiver name with NO SCOPE CHECK, so a PARAMETER spelled like a module
  handle silences `Path.resolve()` on a real account directory - and
  `tests/save/test_absolute_claims.py:192` already binds `citations` as a handle, so that is
  a rename away rather than contrived. And `_module_scope_reaches` asks the same reach
  question as the three sites `grep -n "_calls_any("` finds, so the identical call at module
  scope MANUFACTURED a `<module scope>` declaration on a module reaching nothing - the CS-807
  defect inside the CS-807 repair. **Count the sites from the source, not from that grep.**

- **THE CONTROL LESSON IS THE MOST TRANSFERABLE THING HERE: a control written to defeat
  vacuity was itself vacuous.** It swallowed the guard's own "vacuous" message through an
  `if "vacuous" in said: return` branch and so passed WITHOUT EVER OBSERVING THE GUARD REACH
  A VERDICT. The symmetric instrument it declined to use is
  `assert not _module_reaches(consumer)`, which a gutted guard cannot satisfy and which kills
  two of the surviving mutants. The companion escape control graded as a REAL instrument with
  a clean unique kill, so the pair was half sound.

- **What survived grading, and is reusable.** The two exemption deletions are CORRECT,
  verified by reading `backing_citations`, `dead_full_citations`, `citations.resolve` and
  `prose_paragraphs` end to end rather than by running the guard. No shipped module goes
  silent on the build today; every escape found is prospective.

- **Decisions: no ADR was recorded.** The fences are in `docs/history_notes.md` under
  **CS-807 - detail** and in the ledger entry.

- **Next action: CS-442 or CS-806, NOT a third narrowing of the attribute arm.** CS-807 has
  now consumed a sweep and two refuted builds, and the direction needs an operator decision
  about which side its acceptance buys before more work goes into it.

## Session 28 - 2026-08-22 - an /insights pass; NOTHING CLOSED and four findings filed, one of which reversed under its own evidence

- **Shipped: NOTHING CLOSED, and no code at all.** Zero `.py` files touched across four
  commits. This was a reporting session that turned into a filing session. CS-702 and CS-806
  are NEW items; CS-442 gained a re-derived measurement; CS-G01 and CS-G05 gained dated status
  blocks. Ledger entry for the session is a NON-CLOSURE record and says so in its heading.

- **THE FINDING THAT ORGANISES THE SESSION: the ledger's own verification pointers are
  unguarded, and 7 of 68 do not resolve.** CS-442 has been open on this since 2026-08-16 with a
  census of five; re-deriving it gives seven, in three repair classes that price differently.
  Three are stale PATHS from CS-495's relocation and are NOT defects in the record. Three are
  one-word slips whose real target is measured and named. One, CS-433's, has no identifiable
  target at all. **The four wrong-when-written ones cannot be repaired by editing the ledger,
  because it is append-only** - each needs a new correcting record, and `4b2d04c` has already
  broken that rule once by correcting the CS-500 collision inside the entry that caused it.
  **Seven is a FLOOR:** the census reads `path::test_name` only, and the bare-identifier shape
  that CS-442's own block calls the most important one is still unmeasured.

- **THE CORRECTION, AND IT IS THE ONE TO CARRY FORWARD.** CS-G01 was first written up as "S4
  succeeded, so this gated item should have been VOIDED and was not". **THAT IS BACKWARDS.** ADR
  0003's Consequences section refutes it: S4 SPLIT - geometry yes, semantics no. The save carries
  placement and provably does not carry purity, so the asset path is now LOAD-BEARING for the
  semantics half rather than a superseded fallback, and the ADR says so in terms. Condition 1 of
  CS-G01, read literally, would VOID an item that ADR makes necessary. **The dangerous direction
  on that item is the false void, not the missed one** - and this file's rule against synthetic
  closure runs in that direction too. Do not re-derive the first reading.

- **CS-702 is filed and it is not a paperwork item.** The no-agent-trailer rule recorded in
  `docs/GATED.md` is enforced by NOTHING - no hook, no gate - and 18 of the 171 commits on `main`
  already carry the trailer, all dated 2026-08-14 and 2026-08-15, none since. The GATED.md
  measurement sentence was probably TRUE when written on 2026-08-13; what is overtaken is its
  consequence, "a standing rule going forward rather than a cleanup". **The entry predicted its
  own failure mode in the very next sentence and shipped no mechanism, and seventeen trailers
  arrived by default the following day.** The harness default still adds one every session
  unless suppressed, so the pressure is continuous. `.githooks/*` is FROZEN, so the gate needs
  an adjudicator route and a ledger grant BEFORE the edit.

- **Surprises: the /done ritual tripped over its own documented command.** `py -3` and `python`
  are DIFFERENT Python 3.14.4 installations on this machine and only `python` has `ruff`, so the
  documented tier-0 gate `py -3 -m ruff check` exits 1 with a module error. Filed as CS-806.
  `scripts/verify_env.py` passes under both and is not wrong to - it probes the toolchain by NAME
  on PATH. Also observed: port 8901, this project's allocated dashboard port, has been held by an
  unrelated third-party process since 2026-08-16 and verify_env has been reporting it as a SOFT
  failure on every run. Filed in `BACKLOG.md`; nothing was killed or re-recorded.

- **Failed paths: none - but one method is worth not re-inventing.** Distinguishing a citation
  that was WRONG WHEN WRITTEN from one the tree moved out from under needs
  `git log -S"def <name>(" -- '*.py'` with a control on a live name, because a bare `grep` over
  the history matches the ledger prose that names the test and reports a false positive. The
  same trap bit the trailer census: `grep -i co-authored` matches prose ABOUT the rule, so the
  count must match a body line whose stripped form STARTS WITH the trailer key.

- **ROADMAP.md IS EFFECTIVELY FULL: 97 bytes of margin against its 60 KB budget.** Two items
  were filed into it this session and CS-442's note was already trimmed to a pointer once to make
  room. **The next session relocates before it files anything.** The budget is severity WARN and
  will not fail CI, which is exactly why it needs acting on.

- **Next action:** relocate ROADMAP.md notes into `docs/history_notes.md` until the file has
  real margin, then take CS-442 - the seven are enumerated with their targets, the three classes
  are stated, and the append-only constraint is written down, so the item is now a mechanism
  question rather than a discovery one.
