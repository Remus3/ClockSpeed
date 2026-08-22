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

## Session 26 - 2026-08-21 - CS-492 is BUILT in full and does NOT close; six refutation rounds, five of them mine to answer

- **Shipped: NOTHING CLOSED, and that is the result rather than a shortfall.** CS-492's
  acceptance is built, controlled and mutation-covered, and the item stays OPEN because
  ROUND SIX IS UNGRADED. Six grading rounds ran; every one returned REFUTED and every one
  found something real. Closing on an ungraded round is the mistake this ledger keeps
  recording. Filed CS-800 through CS-805.

- **THE HEADLINE IS THAT THE GUARD WAS MANUFACTURING DECLARATIONS, not that it was missing
  routes.** A declaration is a written claim about where personal data flows, so a false
  reacher is worse than a missed one, and this item produced EIGHT of them across rounds
  three to five. The worst was measured on the real tree: `monkeypatch.setattr(os, "walk",
  os.scandir)` - three ordinary lines - took `tests/save/test_phase4_gate.py` from nine
  flagged functions to twenty. `walk` is excluded BY NAME in `_NOT_LIBRARY_REACH` precisely
  because `ast.walk` is how every AST guard here reads a tree, and CS-497 made
  `_reach_primitives` INTERSECT so an unclassified name reaches nothing. **The attribute
  vocabulary I added had no partition, no map and no intersection**, so the exclusion was
  bypassed by the back door. An exclusion that holds in one namespace and not the other is
  not an exclusion.

- **ONE DOOR ACCOUNTED FOR SIX OF THE EIGHT.** The three-argument store shape read
  `f(target, "name", value)` as a store - which is what `setattr` is, and equally what
  `getattr(spec, "reader", open)`, `re.sub(pattern, "count", text)` and `OSError(13,
  "denied", path)` are. It produced a false reacher in THREE separate rounds with a
  different payload each time. It is gone; `_attribute_stores` read 160 stores on this tree
  and 127 were that shape, so it now reads 33. Two shipped controls died with it and are
  recorded in CS-802 with the measurement, not quietly dropped.

- **THE ROOT CAUSE IS ONE SENTENCE AND IT IS NOT NEW.** `_stands_for_a_primitive` treats a
  primitive's RESULT as standing for one, and justifies it by saying that costs a flag "only
  where the bound name is itself CALLED, which no module in this package does". The
  vocabulary is therefore full of PATH CONSTANTS. A hand-back is exactly the place that
  justification fails. Four rounds were spent deleting arms - the call arm, the container
  arms, the subscript/conditional/fallback arms - before round six did the thing those
  deletions were substituting for: `_serving_names` builds a SECOND, narrower name set from
  the primitives outward by the hand-back rule itself. That is the callable-versus-value
  split, computed where it can be.

- **THREE OF MY OWN SENTENCES WERE MEASURED FALSE AND ARE CORRECTED IN PLACE.** Do not
  rewrite them back. `_reaching_attributes`'s stated cost bound ("costs a flag only where a
  module binds a locator to an attribute name and then calls something else of that name")
  was broken by a counter-example holding no locator at all. `_returned_values` claimed
  `yield from` walks "a container of spellings" while `_hands_back_a_primitive` refuses
  containers outright. And a `strings` switch documented as structural was set correctly at
  ONE of three call sites in the commit that introduced it.

- **THE MEASUREMENT THAT MATTERED MOST WAS THE ONE THAT SAID NOTHING HAPPENED.** The
  widening adds zero attributes, zero serve-aliases, zero newly-flagged functions and loses
  zero coverage across all 18 modules - re-measured after every round, with the harness
  proven able to report non-zero on a planted module first. That zero is real and it is also
  weak evidence: a refutation pass showed the tree sits ONE ORDINARY LINE from a false flag,
  and then produced the line.

- **A CONTROL STOPPED COVERING THE THING IT WAS WRITTEN FOR, silently.** Closing the
  attribute fixpoint in round six meant the hold-and-serve chain no longer needed a second
  round of the OUTER fixpoint, and a mutant setting that loop to `range(1)` went green. The
  mutant was proved non-equivalent and `an-alias-of-a-server` now carries that bound. A
  passing control is not evidence that the bound it was written for still has one.

- **Failed paths, so they are not retried:** keying the store shape on the callee (measured,
  leaves every other store helper open); turning the container arm back on (measured, two
  false reachers from two different channels); a per-caller `strings` switch (set wrong
  immediately); scoping the attribute vocabulary per CLASS (needs receiver typing that
  `_callee_resolves` refuses elsewhere).

- **Suite, no game: `tests` 2190 passed / 52 skipped / exit 0; `tests/save` 1155 passed / 49
  skipped / exit 0.** With the library, 2239 passed / 3 skipped / exit 0. mypy clean 86,
  ruff check and format clean repo-wide, drift guard CLEAN 9/9, doc budget PASS measured 16
  after four relocate passes, precommit gate PASS 5. 24 mutants, all killed, no survivors,
  against a green pristine floor. Controls in `test_reach_guard.py`: 63 at HEAD, 95 now.

- **Decisions: the operator opened the `CS-8nn` follow-up block** because `CS-4nn` is full
  (98 of 100, the two free being gaps the rule forbids backfilling), and ruled that
  `WAKEUP_NOTES.md`'s ENTRIES were the wrong half of its four-session contradiction. This
  file is now newest-first as its header always said; session 23 relocated to
  `docs/history_notes.md`.

- **Next action: GRADE ROUND SIX.** Dispatch a refutation pass against the working tree - not
  against HEAD, which is round zero - on both lenses at once: what still escapes, and what
  the widening falsely flags. If it comes back clean, CS-492 closes on its acceptance and the
  ledger entry cites `tests/save/test_reach_guard.py::test_a_primitive_reached_through_an_object_is_named_by_the_guard`
  plus `::test_the_object_routed_widening_does_not_flag_a_module_that_reaches_nothing`.

## Session 25 - 2026-08-20 - CS-495 CLOSES; a refutation pass refuted the first close and was right, and the hole it found was older than the item

- **Shipped: CS-495 CLOSED.** The library-reach guard implementation moved out of
  `tests/save/test_properties.py` into a new NON-TEST module `tests/save/reach_guard.py`; five
  controls moved into `tests/save/test_reach_guard.py`. Filed CS-497 and CS-498. `tests/save`
  with NO GAME **1111 -> 1115 passed, 49 skipped, exit 0**. Detail in `docs/LEDGER.md`.

- **THE BASELINE REPRODUCED EXACTLY** before any of it: 1111 passed, 49 skipped with no game,
  and 2144 / 52 for the whole suite.

- **THE MOVE IS MACHINE-CHECKABLE AS A MOVE.** Fifty-six top-level definitions left
  `test_properties.py` and every one is BYTE-IDENTICAL to its pre-move source, verified by
  parsing both trees. The collected node-id set lost NOTHING - five tests changed module, four
  were added. Do the same diff on any future relocation; it is cheap and it is the only thing
  that distinguishes a move from a rewrite.

- **A REFUTATION PASS REFUTED THE FIRST CLOSE WITH A COUNTER-EXAMPLE AND IT WAS RIGHT.** A test
  planted in `reach_guard.py` runs ZERO TIMES and nothing says so - pytest does not collect a
  module that is not named `test_*`, and no gutting guard reads it. Pre-move the guard's owner
  WAS a collected test module, so the property was graded. **The class is older than the item**
  - the same plant in `tests/save/synthetic.py` survives on `1e05233` too - but the
  guard-owning file's membership in it is new. Closed by
  `test_no_module_the_collector_skips_defines_a_test`, which covers both modules and both
  shapes.

- **THE SECOND FINDING WAS A MARGIN, NOT A HOLE, AND IS WORTH THE SAME ATTENTION.** An
  undeclared reach planted in the guard's own file reddened ELEVEN tests before the move and
  ONE after, because `reach_guard.py` cannot carry the per-module splice control every consumer
  carries. The property was still graded and the margin was one test wide. Restored by
  `test_the_guard_catches_an_uncontained_helper_spliced_into_its_own_source`.

- **I DELETED A STALE COUNT ON A RULE AND AUTHORED A NEW ONE IN THE SAME FILE IN THE SAME
  COMMIT.** The prose pass measured it: I removed "five module constants of `test_properties`"
  citing CLAUDE.md section 4, and four hundred lines away wrote "in the name of sixteen" - the
  walk covers eighteen. **Knowing the rule is not applying it.** Both numbers are gone now.

- **THREE MORE SENTENCES OF MINE WERE MEASURED FALSE and are corrected in place.** Do not
  rewrite them back: a claim that each consuming module keeps three checks, when only TWO of
  the five call `_assert_no_test_is_gutted` at all; a `:func:` role that stopped resolving when
  the guard moved one file away; and "THIS MODULE'S OWN planted control" in a module that
  plants nothing.

- **TWO PRE-EXISTING HOLES WERE FOUND BY READING THE MOVED CODE, both measured on BOTH trees.**
  CS-497: the vocabulary partition is a TAUTOLOGY in its inclusion direction - `_LIBRARY_PRIMITIVES`
  is derived as locators plus vocabulary minus exclusions, so the assertion reduces to `A <= B | A`
  and an unclassified name is silently made a reach primitive. The suite DOES go red on that
  mutant, on two `test_workdir` tests that have nothing to do with the partition - a red for the
  wrong reason. CS-498: the guard cannot detect a self-exemption in its own source, because every
  control runs it against a `tmp_path` copy under a different filename.

- **THE MOVE CHANGED THE SUBJECT OF THREE OTHER RECORDS AND THEY ARE RE-POINTED.** CS-494's
  acceptance named a symbol that moved; CS-473's subject was one module's prose and is now
  three; and two earlier LEDGER entries cite tests at paths that changed - corrected by the new
  entry rather than by editing them, since that file is append-only. **When you relocate code,
  grep the open items and the ledger for its symbols before you close.**

- **A KILL IS NOT A MEASUREMENT UNTIL YOU KNOW WHICH TEST DID IT.** My first mutation battery
  ran with `-x` and every mutant reddened on
  `test_phase4_gate::test_the_save_suite_passes_with_no_install_and_no_save`, which reruns the
  suite in a CHILD process and so reddens on almost anything. Deselect it when attributing.

- **CS-496 ALSO CLOSED, later in the same session.** The cause is more specific than the item
  was filed with: `git commit` DETACHES `git maintenance run --auto`, so the session-scoped
  template keeps a background git process after its fixture returned, dropping lock files under
  `.git/objects` while later tests copy the directory. Fixed in two halves - housekeeping off in
  the template, and a copy that skips a file which has ceased to exist. **The race is reproduced
  DETERMINISTICALLY**, by deleting the lock from inside `copytree`'s own `ignore` callback, which
  fires after the walk and before the copy. Three mutants, all killed by the intended test.

- **CLOSING CS-496 REQUIRED WIDENING A GUARD, AND THE TEMPTING ROUTE WAS ONE THE GUARD ITSELF
  DOCUMENTS AS A HOLE.** `test_the_suite_never_mutates_this_repository_worktree_admin` demands
  every `_git` call target the identifier `repo`; binding `repo = repo_template` would have gone
  green and is bypass 1 in that guard's own list of what it cannot see. Widened in the open
  instead, with the reason on the constant.

- **CS-497 AND CS-498 ALSO CLOSED, both filed earlier in this same session.** CS-497: inclusion in
  the reach set is DECLARED now rather than derived by subtracting the exclusions, so a vocabulary
  name classified nowhere reaches nothing and is named in the red. **The assertion the fence
  protected was not deleted - the derivation was repaired under it, and it now bites.** The reach
  set is unchanged, checked directly. CS-498: two byte-identical spliced copies of the guard's own
  source, differing only in filename, must get the same verdict; the basename comes from the
  guard's code object and is named nowhere. Residual filed as CS-499.

- **A DERIVATION CANNOT BE GRADED BY ASKING IT ABOUT ITS OWN CONSTANT.** One that absorbs an
  unclassified name and one that rejects it give the same answer on the shipped vocabulary. Making
  `_reach_primitives` take the vocabulary as an ARGUMENT is what let a control hand it an invented
  name, and is what turned a tautology into a measurement.

- **I SHIPPED A NON-NEGOTIABLE 12 VIOLATION AGAIN, IN THE SAME SHAPE SESSION 23 RECORDED.** The
  first draft of the CS-498 control bound the guard's failure in an `except` handler and rendered
  it with `str(caught)`. `tests/test_exception_rendering.py` caught it and that module is OUTSIDE
  `tests/save`, so the `tests/save` run was green while it was there. **Use `pytest.raises`, whose
  AST shape that guard cannot see into, and RE-RUN THE MUTANTS after an idiom change** - a rewrite
  can cost a control its teeth.

- **CS-493 AND CS-494 ALSO CLOSED. CS-493 TOOK TWO ROUNDS AND THE REFUTATION PASS ON ROUND ONE WAS
  RIGHT.** Round one widened the declaration reader to walk the whole value for anything name-shaped
  and justified it with a sentence measured FALSE: "an over-read can never manufacture a reacher,
  because `_reaching_names_of` returns `graded & (direct | indirect)`". **THE INTERSECTION IS
  CIRCULAR** - `indirect` comes from `propagating`, which comes from `graded`, so widening `graded`
  widens the set it is intersected with. Reproduced: a module where NO function calls a primitive
  exported a reacher, and an importer was told to declare a reach for a function touching nothing.
  Round two reads KEY POSITIONS only and refuses what it cannot place.

- **A DATUM IS NOT A BOUND UNTIL A CONTROL SPENDS THE DEFAULT.** The hop-bound control passed
  `hops=` explicitly on both assertions, so a tree declaring a bound of two while every default
  spent one was FULLY GREEN. Fixed twice over: the control now takes the DEFAULT, and pins BOTH
  sides - a chain of exactly the declared length must resolve at the default, which no smaller
  default can do. **The same defect had already bitten this item once** as a fixed-length chain.

- **CS-493's clause 2 was LIVE, not latent.** The new cross-check reddened on arrival naming two
  tracked modules whose declarations the reader could not follow - one keyed on `f.__name__`, one
  built by a comprehension over a `(label, function)` table, which is literally the shape the
  acceptance names. Both spellings exist for good reasons; the reader was wrong.

- **CS-494 closed on the RECORD-AND-GRADE branch, and the coverage half turned out free.** Widening
  `_retained_body_attributes` to the tuple target, the `@property` accessor and the bytes-LIKE
  vocabulary adds NOTHING on the shipped save modules - measured before shipping it. Five of six
  disagreements went away; the item's detail block named three, the merger measured six. The
  survivor is a difference of SUBJECT and is recorded with its reason.

- **THE CS-4nn ID BLOCK IS FULL AND THE /done RITUAL CAUGHT ME COLLIDING WITH IT.** 98 of 100 used;
  the only two unused are GAPS, which CLAUDE.md forbids backfilling. I filed the sentinel residual
  as CS-500 and that ID has belonged to the PHASE 5 GATE for a long time. The older item keeps it
  and mine is renumbered CS-501. **Which block phase-4 follow-ups continue into is an OPERATOR
  DECISION and nothing in the tree settles it** - check the block before filing the next item.

- **Next action:** CS-492, the last of CS-491's residuals and the largest - three shapes reproduced
  ESCAPING this session with a declared companion beside each, so probe with one or every route
  reddens on the guard's vacuity assertion instead. Then CS-499, CS-500, and CS-484 whose premise is
  measured and whose pinning is now cheap.
