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

## Session 23 - 2026-08-19 - CS-487, CS-478 and CS-471 CLOSE; every refutation pass succeeded and one refuted an acceptance clause outright

- **Shipped: CS-487 CLOSED.** Filed CS-490. Two arms landed in
  `tests/save/test_byte_order_status.py`, not one. Suite with the library
  **2142 passed, 3 skipped, exit 0**; `tests/save` with NO GAME **1059 -> 1060 passed, 49
  skipped, exit 0**. mypy clean 28 and 56, ruff check clean, ruff format clean 84, drift guard
  **CLEAN 9/9**, doc budget **PASS measured 16** after a relocate pass, precommit gate PASS.
  Detail in `docs/LEDGER.md`.

- **THE HEADLINE IS THAT ONE ARM WAS NOT ENOUGH AND I SHIPPED THE FIRST DRAFT BELIEVING IT
  WAS.** The `MEASURED_VALUE_TYPES` conjunct reds the filed three-line route and does NOTHING
  against an attacker who PICKS a word already in that table instead of adding one. A
  refutation pass measured that live: three shipped lines plus two test-side, naming a
  LENGTH-PREFIXED type, shipped `vacuous_one_byte` with the tree green - which is CS-480's own
  defect reached again. The fix was widening the derivation's saturation arm from the
  fixed-width table alone to every table the module reads a value out of the payload from.

- **FOUR OF MY OWN SENTENCES WERE MEASURED FALSE BY THE SECOND PASS AND ARE CORRECTED IN PLACE
  WITH THE REFUTATION BESIDE THEM.** Do not rewrite them back: an eight-line price measured on
  a tree WITHOUT the new arm and carrying the wrong tree's pass count; calling
  `MEASURED_VALUE_TYPES` hand-authored when it is DERIVED and the same test module already said
  so; handing the residual to CS-488, whose acceptance is scoped to a width-table entry neither
  surviving route touches; and a pointer chain in which three prose sites each said a different
  one of them owned the price.

- **THE PRICE IS THE RESULT, NOT THE CLOSURE.** The exemption cost three lines in one file and
  now costs seven across two. No route through it is closed, both survivors were taken all the
  way to GREEN rather than left at their first red, and they are CS-490. Read that item's
  detail before touching this area.

- **A COUNT CS-487 WAS FILED WITH DID NOT REPRODUCE.** Its detail block said `tests/save` 1058
  with no game; I measured 1059 four times, on two trees. The RELATION it asserted - forged
  tree byte-identical to clean - reproduced exactly. Corrected in place at
  `docs/history_notes.md` under **CS-487 - detail**.

- **THIS FILE'S STATED ORDER AND ITS ACTUAL ORDER DISAGREE, and I did not silently pick one.**
  The header says NEWEST FIRST; sessions 21, 22 and 23 run oldest first, and did before this
  session touched it. I appended to match the ACTUAL order rather than reorder three blocks
  under a rule I may be misreading. One of the two is wrong and it is an operator call which.

- **CS-478 ALSO CLOSED, later in the same session.** The two definitions of "an oracle scores
  this type" - tag-word in `test_properties._tally_decoded_values`, decoded-shape in
  `test_value_anchoring._score_population` - now meet in
  `test_the_two_admission_rules_for_the_int32_oracle_never_disagree_unrecorded`. Closed on the
  HOLD-THEM-APART route, not unification: the item's own fence forbids deleting either.

- **THE WORST MISTAKE OF THE SESSION WAS IN CS-478 AND BOTH REFUTATION PASSES CAUGHT IT
  INDEPENDENTLY: I ACCUSED A TRUE SENTENCE OF BEING FALSE.** A draft rewrote
  `test_the_cannot_separate_set_is_bounded_without_a_library`'s docstring to say that
  `test_no_type_an_oracle_scores_is_left_recorded_as_unscored` says nothing about the word the
  cannot-separate set names. Widening the dispatch to score that word reds that very test. The
  sentence GOVERNS THE TRANSITION while being silent on today's state; present non-membership
  of a runtime-computed population is not silence. Restored verbatim. **This project's method
  says corrected-in-place sentences must never be rewritten back - a false correction is the
  same defect pointing the other way.**

- **FOUR MORE CS-478 SENTENCES OF MINE WERE MEASURED FALSE and are corrected in place.** Do not
  rewrite them back: a probe constant said to move BOTH channels of the int32 oracle when its
  low byte is non-zero so only one fires; a subset arm whose stated route raises `TypeError`
  before the assertion and which NO edit to `objects.py` can fire; a reverse arm called hard to
  reach that fires three ways; and an absolute suite count that distinguished nothing.

- **CS-478's residual, stated as an adversary put it:** one more line turns the `unscored` lie
  into a `cannot_separate` lie. The control prices CONCEALMENT, not the lie. CS-426 owns it.

- **CS-471 ALSO CLOSED, on its THREE STATED CLAUSES and not on the channel being shut.** The
  parameter-and-locals channel stays open and its pinning test
  `test_the_entry_points_still_bind_the_raw_body_where_a_renderer_can_read_it` STILL PASSES and
  stays. Residuals filed as CS-491. Operator ruled the close on the three clauses.

- **A REFUTATION PASS REFUTED CLAUSE 1 OUTRIGHT AND IT WAS RIGHT.** The scan read module-body
  statements only, so a module-scope reach was invisible - and the classifier called that module
  SILENT, so the guard never ran on it. The proof of concept was the ordinary pytest idiom, a
  module-scope call feeding a parametrize list. Closed under a `MODULE_SCOPE_REACH` sentinel
  wired into BOTH the guard and the classifier. **Fixing a guard without fixing the thing that
  decides which files the guard runs on is half a fix that measures green.**

- **I SHIPPED A NON-NEGOTIABLE 12 VIOLATION WHILE CLOSING A PRIVACY ITEM.** An f-string rendered
  a caught exception object; `OSError.__str__` appends the path it failed on. Caught by
  `tests/test_exception_rendering.py`, which lives OUTSIDE `tests/save` - so a `tests/save` run
  was green while it was there. **Run the whole suite before believing a privacy change.**

- **EIGHT EXEMPT REASONS OF MINE WERE MEASURED FALSE, plus four more defects.** Do not rewrite
  them back: six reasons described filesystem work on functions matched only by a NAME COLLISION
  with a sibling's citation resolver; one described the game install for a synthetic usmap in
  tmp_path; one claimed tmp_path containment for a test passing no path, whose real containment
  is an autouse env fixture. Also: the wrapper walk missed a subclass; the clause-2 control was
  a tautology reporting every input undeclared; the package walk was narrowable to one module in
  silence; and a docstring said "third argument" of two.

- **Next action:** take CS-491 (tier 1), CS-471's filed residual - read its detail in
  `docs/history_notes.md` first. CS-488 and CS-490 are the other open tier-2 byte-order items.
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

- **Next action:** CS-492/493/494, CS-491's remaining residuals - read each detail block in
  `docs/history_notes.md` first, each carries a fence. CS-499 is the cheapest thing filed but its
  candidate fix changes the guard's signature and every call site. CS-484's premise is measured
  and pinning is now cheap.
