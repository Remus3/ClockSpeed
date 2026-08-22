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

## Session 27, continued - 2026-08-22 - CS-492 rounds seven to nine all REFUTED; the bare-name conflict is MEASURED IRREDUCIBLE and CS-807 takes the false-flag direction

**This entry is newer than session 28's below it.** Session 27 resumed after session 28 had
closed and pushed; its commits `6680182` and `31f0e2a` sit on top of `5a5de5f`. Nothing in
session 28's entry is superseded.

- **Shipped: NOTHING CLOSED, for the second session running, and it is the result rather than a
  shortfall.** CS-807 was FILED. Rounds seven, eight and nine of CS-492 were BUILT, each graded
  on two independent lenses, and every one returned REFUTED on a real defect. All three remain
  UNCOMMITTED in worktrees by operator decision so nothing unproven enters `main`. Zero `.py`
  files were touched in `main` across the whole session.

- **THE THREE NUMBERS THAT DECIDED EVERYTHING, all reproduced by the merger rather than taken
  from a builder.** The `_ANY_ATTRIBUTE` sentinel manufactures **268** false declarations across
  six real modules from FIVE ORDINARY LINES of PEP 562 - measured 47 flagged before, 315 after.
  The bare-name class that consumed nine rounds manufactures **EIGHT**. And **FOUR** false
  declarations are LIVE ON THE SHIPPED TREE in `tests/save/test_oracle_citations.py`, whose own
  reason strings say "It opens no file and touches no path at all". The guard was never
  repaired; the false flags were written down and shipped as exemptions.

- **THE BARE-NAME CONFLICT IS MEASURED IRREDUCIBLE. DO NOT SPEND A TENTH ROUND ON IT.** Two
  narrowing spikes were measured against round nine - FIVE-SITE and TWO-SITE. Both take every
  manufactured-declaration payload to ZERO, including `import stat` plus the exec-bit constants,
  which is verbatim real repo code at `scripts/install_hooks.py:44` and `:206`. Both cost the
  SAME TWELVE controls. **Narrowing five sites to two retires NONE of them**, and the mechanism
  was verified rather than inferred: the patched arm is the only consumer of evidence for a bare
  vocabulary word. Two-site DOMINATES five-site - same kills, same reds, smaller diff, one extra
  route kept - so if the hypothesis is ever adopted, adopt it at two sites.

- **THE CONFLICT, STATED ONCE SO IT IS NOT REDISCOVERED.**
  `test_a_parameter_spelled_like_a_primitive_binds_nothing_and_serves_nothing` demands BOTH that
  `stat` as a PARAMETER manufacture nothing AND that `stat = os.stat` at module scope BE CAUGHT.
  Same token, name-keyed guard. Telling them apart needs the type resolution this repo has
  declined. Nine rounds were attempts to split that hair and the measurement says it does not
  split.

- **ROUND NINE'S ENGINE SURVIVED CONTROL-VALIDITY GRADING; ITS PROSE DID NOT.** 38 mutants
  against the builder's 19 found NO new defect, no weakened assertion, no lost control, renames
  clean, the sole survivor proven genuinely equivalent, and termination LOUD rather than hanging
  - 252 `RuntimeError`s where round eight once hung. It was refuted on two documentation defects:
  it ships a provenance claim it declares false 345 lines later in the same file, and it left
  THREE citations to `_value_bound_names`, a function it deleted, one of them the opening
  sentence of a control it added in the same change. **The stale provenance claim is INHERITED
  and is live on `main` today**; the stranded citations are round nine's own.

- **THE PROGRESSION, so nobody re-derives it:** round six certified ANY binding; seven any
  MODULE-SCOPE binding; eight any binding STATEMENT; nine any binding whose value SPELLS a
  vocabulary word. The rule was never value-aware, only LITERAL-aware - `stat = "open"` certifies
  and `stat = "chunks"` does not, and the shipped control grades exactly the one literal that
  misses. Displaced four times, repaired zero times.

- **Failed paths, so they are not retried:** deleting the `def`/`class` admission from
  `_value_bound_names` - reds `a-hold-and-serve-chain-two-rounds-deep` at `2 failed, 1179 passed`;
  splitting locators from raw vocabulary - broken by `def resolve(): return locate.resolve_save_root`,
  a genuine server spelled with a vocabulary word; and the two-site narrowing as a cost reduction -
  it retires nothing.

- **METHOD, EARNED: GRADE A CLAIM AT THE GRANULARITY THE CLAIM IS MADE AT.** A module-level probe
  told the merger a subscript escape did NOT reproduce; it did. The planted `__getattr__` reached
  on its own account, so the module flagged either way. Only calling
  `_assert_library_reach_is_declared(path, graded={}, exempt={})` directly and reading
  `caught.args[0]` separated pristine from mutant.

- **A PROBE GOES STALE THE MOMENT THE RULE CHANGES.** The merger's `except_target` probe read
  SILENT on round nine and looked like a hole. It is not: `except ValueError as stat` binds the
  caught EXCEPTION INSTANCE, never a primitive, so declining it is correct under a value-aware
  rule. The probe was written to catch round seven's regression and outlived its premise.

- **TWO BUILDER CORRECTIONS TO THE MERGER'S OWN BRIEFS, both right.** The round-nine brief
  asserted "these 15 routes are all currently CAUGHT and I verified that myself" - `except_target`
  was not. And the seed control the merger specified for round nine had SILENTLY DECAYED INTO
  DECORATION: a different bound now blocked its mutant, so it separated nothing. Builders that
  implement the brief verbatim would have shipped both.

- **Suite at `31f0e2a`, no game, run this session from scratch: `tests` 2190 passed / 52 skipped /
  exit 0.** mypy clean 86 and 28, ruff check and format clean, drift guard CLEAN 9/9, doc budget
  PASS measured 16, precommit gate PASS non-vacuously via `--files`. Every skip is environmental -
  no game install or no save library - or the mypy gate's empty gap record.

- **Documentation: TWO relocate passes in ONE DAY.** `ROADMAP.md` went 9 bytes -> 2647 -> 97
  (session 28 filed into it) -> 5426 -> 4090. Nine notes relocated byte-identically across the two
  passes. The file is structurally at its ceiling and the budget is severity WARN so CI never says
  so; filed to `BACKLOG.md` with the `docs/history_notes.md` header contradiction beside it.

- **Next action: TAKE CS-807, and take the SWEEP first.** Whether those four false exemptions are
  the only ones on the shipped tree is UNMEASURED - they were found by following one control's
  failure, not by looking. Sweep every module under `tests/save` for an exemption whose reason
  string denies touching the filesystem, before any repair is designed. Then the sentinel, which
  is thirty times the bare-name class and untouched by every round and both spikes.

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
