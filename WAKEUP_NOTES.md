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
## Session 24 - 2026-08-20 - CS-491 CLOSES after THREE rounds; two refutation passes refuted it and both were right

- **Shipped: CS-491 CLOSED.** Forty-seven controls, relocated into a new
  `tests/save/test_reach_guard.py`; one exemption in `tests/save/test_workdir.py`. Filed
  CS-492, CS-493, CS-494 and CS-495. `tests/save` with NO GAME **1064 -> 1111 passed, 49
  skipped, exit 0**. Detail in `docs/LEDGER.md`.

- **THE BASELINE REPRODUCED EXACTLY** before any of it: 1064 passed, 49 skipped with no game.

- **I CLOSED IT WRONG TWICE AND SHIPPED NEITHER.** Round one closed the seven filed routes;
  a refutation pass found ELEVEN more and was right about all eleven - I reproduced every
  one before touching anything. Round two closed those; a second pass found the TWELFTH and
  ten more, and was right again. Round three closed those. **The item is the guard's
  credibility, not the diff, and a green suite after round one would have been a lie.**

- **THE SAME DEFECT FOUR TIMES: ONE MECHANISM APPLIED TO ONE OF TWO POPULATIONS.** Aliases
  resolved to a fixpoint for PRIMITIVES and not for TYPES, so `_Body = bytes` switched the
  wrapper walk off. The module-handle import shape resolved for REACH and not for WRAPPERS.
  The sibling export keyed on the DIRECT set, so a graded-but-indirect helper never
  exported. **And the worst: `_module_scope_reaches` re-derived the callee name itself with
  the pre-CS-491 two-channel test while `_calls_any` had grown five channels - so every
  route I had closed reopened by moving it one indentation level out of its `def`.** This is
  the CS-477 pattern, found four times inside the repair for it.

- **THE FIX FOR THE LAST ONE IS THE SHAPE TO COPY.** I first replaced the callee node-type
  enumeration with `_stands_for_a_primitive(callee)` - a WALK - and it flagged thirteen
  innocent functions, because a RECEIVER is a mention: `THIS_MODULE.read_text()` reads as
  reach when `THIS_MODULE` is itself an alias. That would have manufactured thirteen false
  reasons. Replaced with `_callee_resolves`, a RECURSIVE STRUCTURAL question that asks the
  same thing of a smaller callee. **A guard that names a population is the defect; a guard
  that walks everything manufactures reasons. The answer is recursion, not either list.**

- **EIGHT SENTENCES OF MINE OR MY PREDECESSORS' WERE MEASURED FALSE AND ARE CORRECTED IN
  PLACE.** Do not rewrite them back: `_calls_any`'s claim that a bare-reference matcher
  "flags every forced-failure grader" (measured 1 of 31 - those graders name the primitive
  as a STRING, which is neither a Name nor an Attribute node); a citation to a test that
  does not exist; "eleven tracked modules import it this way" (measured EIGHT; eleven is the
  count of modules the classifier calls reaching, a real measurement of a different thing);
  `_DECLARED_COMPANION`'s present-tense claim that its presence is what makes the controls
  measure the route (true of the pre-CS-491 guard, false of the shipped one); the module-scope
  `lambda` recorded as invisible to the guard (it is VISIBLE and files under the sentinel,
  naming no function, which is worse in one way); and the `test_workdir` exemption's claim
  about which directory the test lists.

- **TWO OF MY CONTROLS WERE TAUTOLOGIES AND A REFUTATION PASS PROVED IT.** The personal-data
  vocabulary's positive half was `_carries_personal_data(f"{word} | None")`, which reduces to
  `word in word + " | None"` and is true for any string - a vocabulary naming nothing
  personal passed it. And the `vocabulary-constant` control claimed to hold the bound stated
  in `_resolves_by_string`; widening that predicate to walk its arguments left the whole
  suite green. Both replaced with assertions that fail: the first walks a synthetic class per
  word, the second asserts the bound of the predicate itself.

- **AN ENUMERATION NOBODY PINS CAN BE NARROWED IN SILENCE, AGAIN.** Dropping `memoryview`
  from `_PERSONAL_DATA_TYPES` AND its parallel entry from the defeat matrix left the suite
  green, one test lower, with CS-491's own wrapper defeat number two reopened. Pinned now
  with a second spelling, deliberately - a pin that reads the list it pins is not a pin.

- **THIRTY MUTANTS, AND TWO SURVIVED EARLIER PASSES.** Both were closed by adding the route
  that isolates the branch rather than deleting the branch: the `getattr`-through-a-NAME
  channel, live only where the primitive is handed back UNCALLED; and the store-annotation
  read, live only where the store's annotation is the sole statement of the type. **The first
  draft of that second route reddened on `_Wrapped.__init__` rather than the caller, because
  its value was itself a primitive call - a red for the wrong reason is not a measurement.**

- **THE PRIVACY PASS CAME BACK NOT REFUTED**, verified at runtime rather than by reading: an
  audit hook over 73 accessed paths, interception of 158 write events, and forced frame
  rendering. Zero reads of the save root, zero writes outside tmp_path, zero rendered paths.
  It handed over one real gap outside its own lens (the indirect-export hole, now closed) and
  one unenforced assumption: ten new f-strings interpolate a caught `AssertionError`, safe
  only because the guard formats function names, and `tests/test_exception_rendering.py`
  cannot see that shape. **Now enforced** - the mutant that adds `module_path` to a guard
  message reddens a control.

- **THE SIZE CEILING WAS 288 BYTES AWAY WHEN I ARRIVED.** `test_properties.py` tripped
  `tests/data/test_phase2_gate.py`'s 256 KiB cap, which exists to catch a trimmed slice of
  real game data. Relocated the controls per CLAUDE.md section 4 rather than raising the
  number, which would have falsified the comment justifying it. **It is still tight. That is
  CS-495 and the next session should expect to trip it.**

- **CS-484's PREMISE IS MEASURED AT LAST, and the item is still open.** Extracted from the tier1 log on `76fac74`: **CI resolves ruff 0.16.3, this machine has 0.15.12**. Three sessions carried that gap as UNVERIFIED because nobody had read it out of a CI log. Both linters passed this tree, so the gap cost nothing on this push - which is NOT evidence it is harmless, only that this tree does not touch a rule they disagree on. Pinning is now cheap because the number is known; it needs `scripts/verify_env.py` to move with `pyproject.toml`.

- **CI WENT RED ON A MARKDOWN-ONLY COMMIT AND IT WAS NOT MY CHANGE.** Run 32346100111 errored in `tests/test_doc_budget.py`'s scratch-repo fixture: `shutil.copytree` races git's own background maintenance, and `.git/objects/maintenance.lock` vanished between the walk and the copy. Re-running the same job passed. Filed as **CS-496**. It is the CS-483 shape - a test failing for a reason unrelated to what it grades - and the tempting response is to ignore it, which is how a suite stops being believed.

- **THE HARNESS HEREDOC ATE MY BACKSLASHES THREE TIMES**, twice on small payloads with quoted
  delimiters. Write such payloads with the Write tool; this is the third session it has bitten.

