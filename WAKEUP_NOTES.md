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

## Session 27 - 2026-08-21 - CS-492 rounds seven, eight and nine; the ROOT CAUSE is finally located and it is a CONTRACT, not a bug

- **Shipped: NOTHING CLOSED. Again, and it is the result rather than a shortfall.** Round six
  was graded and REFUTED on both lenses. Round seven was built, graded, REFUTED on both.
  Round eight was built, graded, REFUTED on both. Round nine was dispatched against the
  located root cause and is UNGRADED at session end. Nine rounds, nine refutations, every
  one on a real defect. The only thing committed this session is a documentation relocate
  pass; rounds seven and eight remain UNCOMMITTED in their worktrees by operator decision,
  so that nothing unproven enters main.

- **THE HEADLINE, AND IT IS THE FIRST TIME THIS ITEM HAS HAD ONE SENTENCE: THE EVIDENCE
  RULE IS VALUE-AGNOSTIC.** It asks WHETHER a bare name is bound at module scope and never
  WHAT IT IS BOUND TO. So `stat = "chunks"` certifies the bare name `stat` as a filesystem
  primitive, and a class with `def get(self, stat): return stat` beside it manufactures
  EIGHT declarations on the real `tests/save/test_phase4_gate.py`, whose entire reach is
  `dict.get(...)`. The round-eight builder stated the contract explicitly - "the evidence
  set is value-agnostic by contract" - so this is a chosen design, not an oversight, which
  is why four rounds of widening never touched it.

- **THE MEASUREMENT THAT ORGANISES EVERYTHING ELSE, taken by the merger across all three
  builds.** `+` means eight manufactured declarations on the real `test_phase4_gate.py`:

  | payload | round 6 | round 7 | round 8 |
  |---|---|---|---|
  | `get(self, stat): return stat` alone | + | clean | clean |
  | module-scope binder alone | clean | clean | clean |
  | `stat = "chunks"` + that method | + | **+** | **+** |
  | `for stat in (...)` + that method | + | clean | **+** |
  | `with ... as stat` + that method | + | clean | **+** |
  | `except ... as stat` + that method | + | clean | **+** |

  **The `Assign` row is the one that matters: it predates round eight and was never
  closed.** Round six's defect has been DISPLACED TWICE AND REPAIRED ZERO TIMES. Rounds
  seven and eight each fixed the spelling a refuter happened to name.

- **NO BUILD IS STRICTLY BEST, and that is why neither was merged.** Round seven has the
  cleanest false-flag direction and three silent module-scope escapes plus three ungraded
  mutation survivors. Round eight fixed all three escapes, added 45 controls with ZERO
  removed and no weakening anywhere, and regressed three false-flag rows. Round eight is
  the better base and is still not shippable.

- **TWO REACH ESCAPES IN ROUND EIGHT ARE CONFIRMED UNGRADED, one of them by the merger at
  function granularity.** Reverting the subscript-key arm so the PEP 562 sentinel cannot
  answer for it turns `FLAGGED: ['_reads_the_served_entry']` into "no function here touches
  a library primitive, so the guard is vacuous" while the whole suite stays at 2235 passed,
  52 skipped, exit 0. The second is the serves-loop evidence site, pinned by nothing.

- **A COARSE PROBE GAVE THE MERGER A WRONG ANSWER FIRST, and the correction is the method
  point.** Asking the PACKAGE WALK whether the module is flagged said FLAGGED under both
  pristine and mutant, because the planted `__getattr__` itself reaches. Only a
  FUNCTION-GRANULARITY probe - calling `_assert_library_reach_is_declared` directly and
  reading `caught.args[0]` - separated them. **Grade a claim at the granularity the claim
  is made at.**

- **THE CEILING IS AN UNGRADEABLE NUMBER, WHICH IS THE DEFECT ROUND EIGHT CLAIMED TO
  REMOVE.** It deleted the old round budget saying a number nothing can grade "is an arm
  already deleted that does not know it", and replaced it with a `RuntimeError` ceiling
  having the identical property: everything from `len//2 + 2` to `2*len + 2` passes the
  whole suite. Measured over all 86 tracked `.py` files, the worst real module uses ONE
  round against a ceiling of six. **The repair relocated the ungradeable number rather than
  removing it.** The loud-failure arm itself is legitimate and must be kept - round eight's
  first battery HUNG before it existed.

- **`_serving_names` IS DEAD CODE AND ITS PROSE DEFENDS ITSELF WITH CONTROLS THAT DO NOT
  EXIST.** Defined, never called; deleting it changes zero verdicts. `_serving_vocabulary`'s
  docstring keeps it "because the controls that grade the serving set ask about names" and
  no such control exists, and `test_reach_guard.py:947` attributes a real control's bound to
  an inner fixpoint in a function that runs no loop and is never called. **That is this
  project's own "a mutant that never applied looks green" trap, written into a comment as
  evidence.**

- **FOURTEEN OF NINETEEN `_MUST_NOT_FLAG` ENTRIES HAVE UNVERIFIABLE PROVENANCE.** The
  standing claim says each was measured flagged by the build immediately before the bound
  that repairs it. Only five can be checked; the other fourteen were born whole inside
  `6f7aa3b`, and at `752d9c7` none of the machinery that could flag them exists. This is the
  same class the two removed entries were removed for. **Mitigating and measured:** reverting
  the hand-back narrowing fires 11 of the 19, so most do grade the narrowing they name - the
  defect is the SENTENCE, not the coverage.

- **THE SETTLED SEED RULE IS GRADED NOWHERE.** `serving = _LIBRARY_PRIMITIVES | attributes`
  survives all of `tests/save`; the `| bound` variant is killed, so one half of the rule is
  pinned and the other is not. A separating control was constructed and handed to round nine.

- **BATTERY SIZE IS A MEASURED FAILURE MODE, not a matter of taste.** Round eight ran 14
  mutants against 1368 changed lines and reported 13 killed, 1 survived. A grading pass that
  derived its targets from the diff ran 41 and found SEVEN survivors, two of them real reach
  escapes. **Size the battery to the change, never to the previous list.**

- **ROUND EIGHT BROKE THE TDD ORDER AND DISCLOSED IT UNPROMPTED** - implementation before
  controls, then controls verified red afterwards. That is exactly the provenance that
  produced the fourteen unverifiable entries. The disclosure was worth more than the
  deviation cost; round nine's brief requires the build each control was measured red
  against to be named in the report.

- **Failed paths, so they are not retried:** deleting the `def`/`class` admission from
  `_value_bound_names` to fix the false-flag class - it works and turns
  `a-hold-and-serve-chain-two-rounds-deep` RED at `2 failed, 1179 passed`, because
  `_HOLDER.second = _serves_the_first` names a module-scope `def` that legitimately serves;
  and splitting locators from raw vocabulary to carry the evidence rule, which the round-eight
  builder measured broken by `def resolve(): return locate.resolve_save_root`, a genuine
  server spelled with a vocabulary word. **Both counter-examples must be satisfied by any
  value-aware fix.**

- **Documentation: a relocate pass, COMMITTED.** `ROADMAP.md` had NINE BYTES of margin against
  its 61440 budget. CS-421's four fences and the NOTE bodies of CS-468 and CS-456 moved to
  `docs/history_notes.md`, byte-identical, leaving acceptance sentences and emphatic pointers;
  margin is now 2647 bytes. The relocation script REFUSES on ambiguity and that caught a real
  case - CS-448 already had a detail block, so its ROADMAP NOTE is a second body and merging
  the two needs judgement rather than a script. It was left alone.

- **Suite, no game, re-measured from scratch at session start and unchanged from session 26:**
  `tests` 2190 passed / 52 skipped / exit 0. Round seven measured 2216/52/0, round eight
  2235/52/0, both verified by the merger independently rather than taken from the builder.
  ruff 0.15.12 check and format clean, mypy clean 86 and 28, drift guard CLEAN 9/9, doc budget
  PASS measured 16, precommit gate PASS non-vacuously via `--files`.

- **A doc-topology contradiction worth an operator ruling:** `docs/history_notes.md` opens
  with "This file holds NOTHING current. Nothing in it may be cited as the present state of
  the project", and is already the home of CS-492's, CS-484's, CS-421's and now CS-468's and
  CS-456's LIVE instructions, which `ROADMAP.md` points at with "MUST BE READ BEFORE TAKING
  THIS ITEM". The file is doing two contradictory jobs. Same shape as the `WAKEUP_NOTES.md`
  contradiction ruled on in session 26.

- **Forward risk, structural rather than a defect:** `tests/save/test_reach_guard.py` is
  182026 bytes against the 262144 cap, having grown about 21 KB in round seven and 17 KB in
  round eight. CS-495 already settled the answer when it arrives - relocate, never raise the
  number, because the cap's stated premise is that every hand-authored file sits far below it.

- **Next action: GRADE ROUND NINE, on both lenses at once.** Its base is `6f7aa3b` plus round
  eight's two files, NOT HEAD - assert `git hash-object tests/save/reach_guard.py` is
  `9c16958af3168e19005ab1c257b529f399d2fdfa` before measuring anything. The false-flag lens
  owns the six-row table above; the control lens owns battery size, the ceiling constant, the
  standing claim and the seed rule. If round nine comes back clean, CS-492 closes on its
  acceptance; if it does not, the open question is no longer which spelling escaped but
  whether a name-keyed guard can satisfy this acceptance at all - CS-491's own note warned
  "do not close this by widening the name list alone", and nine rounds have now tested that
  warning to destruction.
