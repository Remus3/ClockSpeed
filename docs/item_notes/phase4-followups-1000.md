# Clockspeed - live per-item detail, phase 4 - save reader, CS-1000 and above

**Section status: LIVE.** A dated heading in this file records provenance - when the
text was filed, moved or measured - and never that the section itself is historical.

**THIS LEAF HOLDS EVERY PHASE 4 ID AT CS-1000 OR ABOVE.** The `1000` in its name is a
FLOOR, not a block: `CS-11nn` and every later block land here too, and the leaf
membership rule in `docs/item_notes.md` spells that floor rather than a block. Its siblings
`docs/item_notes/phase4-followups-900.md` and `docs/item_notes/phase4-followups-960.md`
split the `CS-9nn` block between them at CS-960 and neither reaches above it - CS-1132,
whose reasoning is in `docs/item_notes/leaf-membership-rule.md`.

**This is a leaf of `docs/item_notes.md`**, which owns the index and the rules this file
obeys. Read the index for the leaf membership rule routing every OPEN item, the verbatim
rule, and what this family never contains. Do not restate any of it here.

**Relocated for CS-1079.** Every section below stood in
`docs/item_notes/phase4-followups-900.md`, in the order it stood there, until that leaf
went over its soft doc budget holding IDs its own selector did not name.

---

## CS-1053

### Filed 2026-09-14

**THE READER IS CORRECT BY CITATION, NOT BY MEASUREMENT.** CS-1039 keys the unlock
carriers off `docs/adr/0016-unlock-arrays-carriers-and-serialized-grammar.md`, and its
fixtures parse that same table AT TEST TIME. That was the right repair - it broke the
dependence on an item note whose wrong keys matched zero records - but it CONCENTRATED the
dependence rather than removing it. Fixture and oracle still share a source. It is a better
source; it is still one source.

**THE ADR IS NOT A SETTLED DOCUMENT.** It is status `proposed`. Two of its statements are
already measured FALSE: its claim that the property decoder has no production caller, which
`clockspeed/save/world.py` contradicts by calling it per record, and its claim that the
`(14,60)` shape decodes zero property tags, which `docs/LEDGER.md` contradicts with a
3918-record measurement on the pinned world. **Production behaviour is currently keyed off a
document known to be wrong in two places.**

**WHAT MAKES THIS DIFFERENT FROM ORDINARY DOC DRIFT.** A stale doc misleads a reader. This
one decides which records the save reader joins. If a carrier type path in that table is
wrong the same way the declaring-class names were wrong, the reader silently matches
nothing and every synthetic arm still passes - the exact failure that refused CS-1039's
first candidate, one level up.

**THE BOTH-DIRECTIONS CLAUSE IS THE POINT AND MUST NOT BE WEAKENED TO A SUBSET.** A key
with no ADR row and an ADR row with no key must BOTH redden. A one-sided containment check
passes while the table quietly grows or shrinks, which is the floor shape this repo has
measured leaking repeatedly.

**NEEDS THE GAME AND A REAL SAVE**, like CS-1052, and for the same reason: only a save can
say what a save carries. Run both in one pass if they are taken together. Nothing measured
is committed except the observed type paths, which are publisher-owned asset content - no
save file, no header bytes, no account id, no world name.

**CORRECT THE FALSE STATEMENTS IN PLACE.** `docs/LEDGER.md` is append-only and owns the
record of what was wrong; the ADR should say what is true. Do not delete the false lines
silently - an ADR that quietly loses a claim it once made is a document nobody can audit.

### Acceptance

every carrier type path the ADR records is re-measured by running the shipped decoder over a real save, each false statement is corrected in place with what was measured, the status line moves to `accepted` or states in the ADR why it cannot, and an arm asserts the production key set and the ADR table agree in BOTH directions so a key with no ADR row and an ADR row with no key both redden

### Full headline

`docs/adr/0016-unlock-arrays-carriers-and-serialized-grammar.md` is status `proposed`, carries two statements already measured FALSE - its claim that the decoder has no production caller, contradicted by `clockspeed/save/world.py`, and its claim that the `(14,60)` shape decodes zero property tags, contradicted by `docs/LEDGER.md` - and is now the single source for BOTH the production unlock keys and the fixtures that grade them, so the reader is correct by citation rather than by measurement


## CS-1055

### Filed 2026-09-14

**THE GUARD INFERS AUTHORSHIP FROM A WALL CLOCK, AND AUTHORSHIP IS NOT A TIMESTAMP.** The
live-copies teardown in `tests/conftest.py` counts files carrying the copy suffix before and
after a test, and blames the difference on the suite. Any process holding the same workdir
is indistinguishable from the suite under that rule.

**MEASURED 2026-09-14, AND THE FALSE ACCUSATION WAS THE FIRST ONE IT EVER MADE HERE.** A
`python -m clockspeed.surface` process that had been running about 24 hours wrote a copy 4.8
minutes before the check, while NO suite was running. It failed
`tests/save/test_struct_interior.py`, a module a purpose-written tracer showed calling
`workdir.copy_for_read` ZERO times across a full run. The module never reaches
`world.load_world`, which is the only caller of that function in the tree. A builder proved
the module innocent and refused to repair it, which is what the stop-and-report rule is for.

**THE FIX IS TO MEASURE THE THING THE GUARD IS ACTUALLY ASSERTING.** It wants to know
whether THIS PROCESS copied a save. Instrument `workdir.copy_for_read` and count calls;
do not difference a directory. A count of calls cannot be confused by a neighbour.

**SHIP THE TRACER.** The guard's own message says to run the write tracer, and THE REPO HAS
NO WRITE TRACER - the instruction was inherited from a sibling project. One was written from
scratch to answer this, and then thrown away. An instruction naming a tool that does not
exist is worse than no instruction: it reads as though attribution is available.

**THE ASSERTION STAYS A COUNT AND NEVER BECOMES A LISTING.** A copy is named for the save it
came from, so a set of names rendered into a failing assertion is a set of the operator's
world names. Non-negotiable 12. The existing docstring is right about this and must survive
the repair.

**BOTH DIRECTIONS MUST BE GRADED.** A concurrent writer's copy during the window must NOT
redden the guard, and a copy the suite itself makes MUST. One arm each. A guard that only
proves the first has been relaxed rather than repaired.

### Acceptance

the guard counts copies THIS PROCESS made, by instrumenting `workdir.copy_for_read` rather than by differencing a directory, and an arm asserts a copy written by a concurrent writer during the window does NOT redden it while a copy the suite itself makes DOES, with the tracer shipped rather than re-written per investigation - and the assertion stays a COUNT and never a listing, because a copy is named for the save it came from and rendering those names is non-negotiable 12

### Full headline

`tests/conftest.py`'s live-copies teardown infers AUTHORSHIP from a wall-clock before/after count over a directory any process may write to, so a long-running `python -m clockspeed.surface` holding that workdir gets its copies attributed to whatever suite happens to be running - measured 2026-09-14, a copy landing 4.8 minutes before the check while no suite was running failed a module a purpose-written tracer showed called `workdir.copy_for_read` ZERO times


## CS-1056

### Filed 2026-09-14

**THE SUITE WAS UNDER-MEASURING THE SAVE FORMAT THE OPERATOR ACTUALLY PLAYS ON, AND THE
PRODUCTION READER WAS FINE.** CS-1054 found that `tests/save/test_struct_interior.py`'s
independent tag walk expressed the LEGACY grammar only, so it read ZERO sites across all
80801 records of version pair (60,14) - a pair `objects.COMPLETE_TYPE_NAME_PAIRS` declares
and the shipped reader reads correctly, measured at 400 of 400 sampled records. That module
is repaired. This item is about every OTHER module carrying the same shape.

**THE POPULATION IS ENUMERATED FROM THE IMPORT GRAPH, NEVER BY HAND.** A hand list of
modules reaching `tests/save/test_decode_oracles.py::_walk_with_the_shipped_reader` is a
denylist by another name, and this repo has measured that shape leaking four times. Derive
it, then measure each member.

**THE TEST IS SITES-FOUND AGAINST CENSUS, PER VERSION PAIR.** A module that reads many sites
on old pairs and zero on (60,14) is under-measuring, not observing an absence. A module that
reads zero everywhere is a different fault. Say which each one is.

**A ZERO THAT DILUTES IS THE SECOND HALF OF THIS ITEM.** `_run_degradation_control` POOLS the
library, so one pair's zero is averaged away instead of reddening. That is the pooled-guard
shape already measured in this project: a threshold summed over a population is met by its
strongest member while its weakest goes ungraded. Per-pair, not pooled.

**WHAT THIS ITEM IS NOT.** It is not a production reader item. `clockspeed/save/` reads that
grammar correctly and CS-1054 changed none of it. Any finding that points at production code
is a NEW item and must be filed as one rather than repaired here.

**THE GENERAL LESSON, WHICH OUTLIVES THE ITEM.** A test-side oracle blind to the newest
format reports a production gap that does not exist, and it does so LOUDLY - CS-1054's arm
said evidence destroyed. An oracle must be checked against the formats it claims to cover
before its verdict about production is believed.

### Acceptance

every module reaching that walk is enumerated from the import graph rather than by hand, each is measured against pair (60,14) for sites-found versus census, and any that reads zero where the shipped reader reads many is repaired or recorded with the reason - and separately `_run_degradation_control` stops POOLING the library, because a pooled figure lets one pair's zero dilute instead of redden, which is the pooled-guard shape already measured here

### Full headline

`tests/save/test_struct_interior.py`'s independent tag walk expressed the LEGACY grammar only and so read zero sites across all 80801 records of version pair (60,14), which the shipped reader reads correctly and which `objects.COMPLETE_TYPE_NAME_PAIRS` declares - CS-1054 repaired that module, and `tests/save/test_decode_oracles.py::_walk_with_the_shipped_reader` carries the same shape for every other module that shares it, so an unknown number of arms may be silently under-measuring the save format the operator actually plays on


## CS-1052

### Filed 2026-09-14

**SPLIT OUT OF CS-1039 BY ADJUDICATION, AND THE SPLIT IS THE WHOLE POINT.** CS-1039's
acceptance names three carriers; two are wired and this is the third.
`mTradingPostLevel` IS declared `SaveGame`, as an `int32` on `AFGTutorialIntroManager`, so
it CAN be in a save - that half is settled by declaration and needs no re-checking.

**WHAT IS NOT KNOWN IS WHICH RECORD CLASS CARRIES IT.**
`docs/adr/0016-unlock-arrays-carriers-and-serialized-grammar.md` records a carrier type
path for every other carrier and NONE for this one. A save is joined on the save-side type
path, not on the declaring C++ class, so without that measurement there is no key.

**THE REFUSAL THAT CREATED THIS ITEM IS THE BEHAVIOUR TO PRESERVE.** A builder could have
guessed `AFGTutorialIntroManager` and shipped an arm that passes on every synthetic fixture
and matches ZERO records on every real save. That is precisely how CS-1039's first
candidate failed, and it was refused for it. Guessing a key here would reproduce the defect
in the item created to avoid it.

**THE MEASUREMENT COMES FIRST AND THE ARM COMES SECOND. A SYNTHETIC ARM WRITTEN BEFORE THE
MEASUREMENT GRADES AN INVENTED CLASS AND IS REFUSED** - it would be green, permanently, and
wrong. Run the shipped decoder over a real save, observe the type path that actually
carries the property, record it in ADR 0016 beside the others, and only then write the
wiring arm against it. If the property does not appear in any readable save, that is a
RESULT: record it, leave the carrier in `UNLOCK_CARRIERS_UNREAD`, and close this item
saying so.

**NEEDS THE GAME AND A REAL SAVE**, unlike every other slice in this block. It cannot be
done on a machine with no install. Nothing measured from a save is ever committed: no save
file, no header bytes, no account id, no world name - only the observed type path, which is
publisher-owned asset content.

**RELATED RISK THIS ITEM SHOULD SETTLE WHILE IT IS THERE.** CS-1039's fixtures now parse
ADR 0016's carrier table at test time. That restored independence from the item note but
CONCENTRATED dependence on the ADR: it is now the single source for both production keys
and fixtures, and nothing verifies the ADR against a save. A measurement pass is the
natural place to close that.

### Acceptance

the carrier class is MEASURED by running the shipped decoder over a real save and recording the observed type path in the ADR, and only then an arm in `tests/save/test_world.py` packs it onto a synthetic record of that measured class and asserts the value round-trips and that `UNLOCK_CARRIERS_UNREAD` no longer names it, reddening when the carrier is unwired - a synthetic arm written before the measurement grades an invented class and is REFUSED

### Full headline

`mTradingPostLevel` is declared `SaveGame` on `AFGTutorialIntroManager` so it CAN be in a save, but `docs/adr/0016-unlock-arrays-carriers-and-serialized-grammar.md` records no carrier type path for it, so nothing knows which record class carries it and CS-1039 left it unread rather than invent a key


## CS-1012

### Measured 2026-09-14 (session 95), and the item's OWN PREMISE MEASURED FALSE

**THE LINE SAID THE SPREAD ON ONE TREE IS ABOUT 20 SECONDS. IT IS AT LEAST 222.**
That figure came from a single rerun pair. Two same-tree pairs now exist and they
DISAGREE with each other, which is the finding:

| pair | attempt 1 | attempt 2 | apart |
|---|---|---|---|
| `8165c35`, run 34830236951 | 511s job, 456s unit step | 289s job, 257s unit step | 222s |
| `aa9cbb6`, run 34777140837 | 500s | 477s | 23s |

Two attempts of one run differ in NOTHING a commit can express - same SHA, same tree,
same pinned toolchain. So the pool is TWO-CLASS rather than continuously noisy, and a
sigma-banded wall-clock threshold is grading which class it landed on.

**THE RED THAT STARTED THIS WAS A DOCS-ONLY COMMIT.** `8165c35` differs from its green
parent by two markdown files - `WAKEUP_NOTES.md` +73/-24 and `docs/history_notes.md`
+25/-0, about 4 KB against a 3,324,152-byte corpus. Both runs collected 6106 passed and
31 skipped on the fast shard, 1438 and 100 on the save shard. Identical workload.

**THE DOC-WALKING HYPOTHESIS WAS THE REAL ALTERNATIVE AND IT IS REFUTED THREE WAYS.**
This repo HAS tests that walk markdown, so "docs-only" is not automatically
"workload-identical" and the claim does not get to skip the step:

1. `docs/history_notes.md` is the one UNGUARDED doc, and
   `tests/test_docs_citations.py` binds it as `DEEP_ARCHIVE`. The citation walk never reads the growth at all.
2. The ratio ORDERING runs backwards for growth. Per-row ratios span 1.29 to 1.53; the
   doc-walkers moved LEAST (`test_archive_rot` at 1.29, the lowest row in the table) and
   the markdown-blind `test_mypy_gate` moved MOST at 1.53.
3. Collected counts are identical, above.

**THE CONTROL WITH NO REPO-CONTENT DEPENDENCE AT ALL.** `Install toolchain` is a pinned
pip install whose input is byte-identical between attempts. It moved 7s to 12s, a ratio
of 1.714. A cache-miss explanation was raised against it and CHECKED rather than waved
off: both attempts print `Using cached` for the same twelve packages and `Downloading`
for exactly one and the same package, `ast_serialize-0.11.2`. Identical cache state.

**AND THAT CONTROL IS WHAT DECIDES THE REPAIR.** Within the same-tree pair the toolchain
moved 1.714x while the unit step moved 1.774x - **the two ratios agree to 3.4 per cent**.
Normalizing 456s by 12/7 yields 266s against an actual fast-class 257s. A step that runs
no repo code predicts the suite's own slowdown to within 3.4 per cent, which is the
direct measurement that an in-job calibration divisor works on the decisive pair.

**THE FEASIBILITY ARITHMETIC, WHICH IS THE WHOLE ARGUMENT.** The rule published at
`docs/item_notes/phase4-followups-850.md` needs `[M, cutoff - 2N]` non-empty. With M=511
and N=222 against a 600s cutoff that window is `[511, 156]` - EMPTY - and `N > (cutoff-M)/2`
reads 222 > 44.5. **Wall-clock gating is INFEASIBLE at this lane length rather than
mis-tuned.** Retuning the band cannot repair this item, and shortening the lane until it
can is a different item: CS-1060.

**ADJUDICATED 2026-09-14.** Ruled by an agent that produced neither the spec nor the
measurements, against the frozen tree at `8165c35`. The repair is NORMALIZE BY AN IN-JOB
CALIBRATION WORKLOAD - the gate grades `ELAPSED * REFERENCE_MS / MEASURED_MS`, so the band
sits in runner-invariant units. The runner-up was demoting the gate to a REPORT and moving
the growth signal to per-test shares; it lost on the item's first criterion, being blind to
EVENLY SPREAD growth, which is CS-1012's own headline case. It did NOT lose to CS-896 -
that item's acceptance is satisfied verbatim by a report, and the spec's claim that CS-896
forbids the demotion was checked and does not hold.

**THE FENCE THAT MUST SHIP WITH THE REPAIR, OR IT BECOMES THE THING IT REPLACED.** The
adjudicator rejected the spec's defence that the forbidden move is "arithmetically
unreachable" - that rests on the 600s cutoff staying policy. The binding clause instead:
**the reference constant is NEVER re-pinned in response to a red.** It is written into
`.github/workflows/tier1.yml` beside its derivation and carried by the same two-way
ratchet in `tools/drift_guard.py` guard (k), or this is CS-988 in a new coat within two
sessions.

**NOT BUILT IN SESSION 95, DELIBERATELY.** The calibration discriminator needs a
multi-dispatch measurement campaign that does not exist yet, and the calibration workload
itself adds 20 to 40 seconds to a job already at 511 against a 600s cutoff - so building
it before CS-1060 would push the lane toward the runaway cutoff, which CANCELS rather than
fails and is therefore evidence of nothing.

**THE TAX, MEASURED.** Sixteen recent tier 1 runs carry FOUR reds. THREE of them have the
Duration step as the only failing step in the job - runs 34791962600 at 493s, 34777140837
at 500s and 34830236951 at 511s. The fourth, 34776266752, is a real test failure and is
not this item's.

### Acceptance

the 133 seconds are attributed to a named cause by measurement on the runner rather than locally, with an arm or a probe that reddens when that cause is present and a control that shows it absent, and the gate's ceiling is then set from the MEASURED spread with the evidence recorded - RAISING THE CEILING TO FIT THE CURRENT NUMBER IS FORBIDDEN HERE BY NAME, it is the CS-988 shape applied to a signal rather than a threshold, and a ceiling that is tuned whenever it fires measures nothing

### Full headline

tier 1's unit step cost 133 seconds more after CS-1009 than before it and the duration gate is now marginal rather than comfortable: the step went 316.16s over 5719 tests to 449.16s over 5740, the job total ran 493s against a 480s CEILING and a 420s budget, and a re-run of the IDENTICAL commit came in at 470s - AND THAT 20s FIGURE IS MEASURED FALSE, session 95: two same-tree rerun pairs read 222s and 23s apart, so the runner pool is TWO-CLASS rather than continuously noisy, and the repo's own feasibility arithmetic run on those numbers returns an EMPTY window - wall-clock gating is INFEASIBLE at this lane length rather than mis-tuned, which is a different item and it is CS-1060 - but the growth is NOT attributed and that is the finding rather than a caveat: it is spread evenly across tree-walking sweeps that have nothing to do with the change, `test_locals_rendering` 17.9s to 26.1s, the mypy-gate oracle 16.7s to 25.6s, `test_liveness` 15.8s to 24.6s, `test_toolpath` 8.6s to 11.9s, roughly plus 45 pct each, while the delta added about 85 KB to a multi-megabyte tree and the same suites measured LOCALLY at base and at head differ by under 12s in the noise - the WHOLE suite on this box is FLAT across the same delta - 411.54s at the base commit, 404.19s at the merged tip, both through the pre-push hook - so the 133s exists only on the runner and the first hypothesis to test is the environment rather than the tree, and CS-1009's own arms are 4.2s locally for the whole file and none reaches the CI slowest-15


## CS-1067

### NOTE - filed 2026-09-14 by the CS-302 verifier pass

THE GAP IS THE CALLER AND NOT THE FALLBACK. `exact.isolating_rows` returning empty is
already pinned directly, twice, in `tests/solve/test_exact.py`. What nothing reaches is
`clockspeed/solve/ratio.py::_name_unsatisfiable_item`'s LAST return - the one that names
`system.rows[0]` when no single row isolates the contradiction. A `trace` run over
`tests/solve/test_ratio.py` puts ZERO hits on it while the all-zero fast path takes two
and the isolating branch takes four. So the item a caller is handed in that case rests on
reading the code.

IT IS REACHABLE, AND THAT WAS DEMONSTRATED BEFORE IT WAS FILED. A system built from the
CS-302 corpus generator drives it and it names the first row, exactly as its comment says.
The finding is coverage, not correctness, and it is UNCHANGED from before CS-302 - the old
leave-one-out loop had the same fallback and the same absence of a test through the caller.

BUILD IT FROM A SYNTHETIC REGISTRY, NEVER FROM A HAND-MADE `_System`. Constructing the
private dataclass directly would exercise the fallback while proving nothing about the
path a caller actually takes, which is the whole of what is missing. The shape needed is a
selected recipe set whose balance rows carry two or more INDEPENDENT contradictions, so
that striking any single row leaves another one standing.

### Acceptance

a test drives `solve_for_targets` to a refusal whose system makes `exact.isolating_rows` return empty and pins the item named, built from a synthetic registry and never from a hand-made `_System`, since the gap is precisely that the CALLER is not exercised

### Full headline

`ratio._name_unsatisfiable_item`'s no-single-row-isolates fallback is reachable and no test through the caller reaches it - a `trace` run over `tests/solve/test_ratio.py` puts ZERO hits on that return while the fast path takes two and the isolating branch four, so the item it names rests on reading the code


## CS-1069

### Filed 2026-09-14 by the queue lane, from CS-868's sibling sweep

**WHAT WAS MEASURED, and it is a measurement rather than a reading of the code.** With
CS-868's cross-module closure in hand, the same question was put to
`tests/save/test_reference_resolution.py`'s `_shared_reference_symbols`. It has CS-868's root
cause wearing a patch: the closure is taken over one file, and the single crossing it knows
about - `test_decode_oracles._walk_with_the_shipped_reader` - is TRANSCRIBED into the seed
union by hand rather than followed.

Two facts came out of the measurement and both belong to this row:

- `_sweep_one_save` calls the same-file helpers `_second_join` and `_scan_type_words`, and
  NEITHER is folded into pass one's seed set. Pass one's reach is therefore read from two
  functions' DIRECT qualified attributes and from nothing they call.
- The arm nevertheless passes, because `_objects_closure` closes the seeds over `objects`'
  OWN call graph and that graph happens to cover the difference. **THE CLAIM HOLDS BY
  ACCIDENT OF THE SHIPPED MODULE'S SHAPE, NOT BECAUSE THE DERIVATION IS RIGHT**, and an
  accident is exactly what a refactor of `objects` removes without anything going red.

**WHY IT WAS FILED RATHER THAN SWEPT INTO CS-868.** The arm compares its derived set to
`objects.REFERENCE_COUNT_COMMON_MODE` - a SHIPPED constant, and CS-835's subject. Widening
the derivation moves both sides of that comparison, so the repair is a change to a shipped
record and to another item's recorded claim. CS-868's acceptance names two arms in one test
module and neither is here.

**THE SECOND HALF OF THIS ROW IS THE CACHE-HIT SHAPE CS-868 LEFT STANDING.**
`test_struct_interior._run_ceiling_control` takes its pristine and its degraded reading over
the SAME body object, so a memo on the second reading makes the degraded call a cache hit and
the arm's "this module's own site total does not move under the plant" holds vacuously.
CS-868 closed on the symbol arm reddening, which is what its acceptance asked for; this shape
is untouched. **DO NOT REPAIR IT BY DELETING A MEMO - there is no memo in the tree.** The
repair CS-866 used next door is to make every graded case ask a question no earlier call
answered.

**FENCE - DO NOT CLOSE THIS BY WIDENING THE RECORDED CONSTANT UNTIL THE DERIVATION IS RIGHT.**
A derivation that reaches more symbols and a recorded set edited to match it produce the same
green. The order is: make the closure follow what the passes call, MEASURE what joins, and
only then decide whether the constant moves - saying in the ledger which symbols joined and
whether any of them was a reader rather than a width.

**FENCE - THE TWO HALVES SHARE A ROOT CAUSE AND MUST NOT BE SPLIT ON CONVENIENCE.** Both are
a grading apparatus that cannot see a reading it did not expect - one through a module
boundary, one through a cache. Shipping either alone is a partial and is recorded as one.

### Acceptance

`_shared_reference_symbols` closes over what each pass CALLS rather than over one file plus a transcribed crossing, and `_run_ceiling_control`'s degraded reading cannot be served from the pristine one, proven by a mutant carrying a memo that reddens and by a same-file helper moved behind a call that reddens


## CS-1074

### NOTE - filed 2026-09-14 by the queue lane from the CS-870 verifier pass, MEASURED BEFORE FILING

**THE ARM IS `tests/save/test_struct_controls.py::test_degrading_the_shipped_tag_reader_cannot_improve_this_modules_grade`.**
Its docstring says four things are asserted, the fourth being that the revert LANDED. The
line that is meant to carry it reads `objects._payload_text` after `monkeypatch.undo()` and
asserts it is the original, under the message "the shipped reader was NOT restored, so every
later measurement in this process is taken against a degraded module".

**WHY THIS IS NOT CS-870 AND THE DISTINCTION IS THE WHOLE ITEM.** CS-870's arm had a control
that installed and restored the ceiling ITSELF, so there was a real obligation going
ungraded and a real defect route - a control returning degraded. Here there is not: that
module holds exactly one `monkeypatch.setattr`, nothing else writes `objects._payload_text`,
and neither `_run_degradation_control` nor `_run_table_degradation_control` touches a
shipped attribute. So no restore is owed by anything except the fixture, and the assertion
is a NET rather than a grade. **DO NOT FILE THIS AS AN UNGRADED DEFECT ROUTE** - it is a
message claiming more than its subject can fail on.

**WHAT MAKES IT WORTH A ROW RATHER THAN A COMMENT.** Next door, that exact wording is what
let CS-870's clause read as covered for three sessions. A message that names a consequence
the assertion cannot detect is the thing an adversary has to re-derive from scratch every
time, because the prose answers the question the code does not.

**THE TWO HONEST ENDINGS, and the acceptance admits either.** Either the arm gains a reading
the fixture does not supply and the message keeps its claim - which requires something in
that module to own a restore, and nothing does today, so this is the weaker option - or the
message is narrowed to what a fixture teardown proves and the docstring's fourth assertion
is restated as the net it is. CS-870's repair took the second route for its own net line and
left the first to the control it actually grades.

**DO NOT REPAIR THIS BY DELETING THE ASSERTION.** A net that cannot fail is still worth
running; what is wrong is the sentence, and an arm that reddens when the two claims are
swapped is what the clause asks for.

### Acceptance

the assertion says which of the two it is, and either a reading the fixture does not supply grades the claim its message makes or the message claims only what a fixture teardown can prove, proven by an arm that reddens when the two are swapped

### Full headline

`test_struct_controls.py`'s revert assertion is only a net and its message presents as the grade, which is the wording CS-870 had to correct next door and the reason its own clause went ungraded for three sessions


## CS-1075

### Filed 2026-09-14 (queue lane), from the CS-871 close

**THE THREE UNGRADED SPELLINGS ARE DECLARED, NOT FORGOTTEN, AND THE DECLARATION IS
MACHINE-CHECKED.** `tests/test_sphinx_roles.py::test_every_role_spelling_in_the_corpus_is_declared`
asserts the corpus's role vocabulary EQUALS the keys of `ROLE_DISPOSITIONS`, so a seventh
spelling reddens rather than passing unread, and
`test_an_ungraded_spelling_carries_a_reason` asserts every ungraded entry names an item id.
This row is that id.

**WHY THEY WERE NOT GRADED WITH THE OTHER THREE, and it is a resolution difference rather
than an appetite one.** `:func:`, `:data:` and `:class:` all name something a module's own
namespace can bind, so one resolver answers all three and CS-871 shipped it. `:attr:` and
`:meth:` name a member of a CLASS, and the class is not in the role text - it is in the
context the role sits in, which means resolving one needs the enclosing class rather than
the enclosing module. `:mod:` names a module, so its resolution is a file test rather than
a namespace lookup.

**DO NOT CLOSE THIS BY WIDENING THE GRADED SET AND POINTING THE SAME RESOLVER AT IT.** A
module-scope lookup applied to `:attr:` forgives every attribute whose name happens to
collide with a module-level binding and reports every other one dead. Both halves of that
are wrong and the second is what gets a guard switched off.

**THE CLOSE IS VISIBLE IN THE TABLE ITSELF.** An entry moving from a reason string to
`GRADED` is what this row buys; rewording the reason is not.

### Acceptance

each of the three is resolved by a rule stated for it, with `:attr:` and `:meth:` resolved against the CLASS the role's context names rather than against any module-level binding, proven by a planted dead role per spelling that reddens and by the declared-reason entry for that spelling disappearing from `ROLE_DISPOSITIONS` rather than being reworded

### Full headline

`tests/sphinx_role_guard.py` grades three of the six Sphinx role spellings its corpus contains and DECLARES the other three rather than reading them, so every site spelled `:attr:`, `:meth:` or `:mod:` carries an identifier nothing resolves - the two classes differ in RESOLUTION and not in shape: `:attr:` and `:meth:` name a member of a class, which module-scope resolution cannot answer, and `:mod:` names a module rather than a symbol bound inside one


## CS-1076

### Filed 2026-09-14 (queue lane), carried out of the CS-871 section on its close

**THIS IS THE SECOND RESIDUE CS-871 CARRIED AND ITS ACCEPTANCE IS NOT CS-871's.** That
item's clause was about Sphinx roles; this one is about a guard's population. Filing it
here is what keeps the CS-871 close honest rather than silently dropping half a section.

**WHAT AN ADJUDICATOR MEASURED, and the measurement is the reason this is a risk rather
than a bug.** `_bodies_no_dynamic_case_may_reuse` enumerates only the bodies its own
module builds. `independent_table.independent_records` is called at four sites in the same
process, and they are NOT all in one file: two sit in `tests/save/test_struct_interior.py`
and two in `tests/save/test_struct_controls.py`. The residue was written before that module
split and named only the first, so a close that greps one file covers half the population.
All four hand over real decompressed save bodies, and the guard's set and the dynamic set
have ZERO overlap - so nothing collides today, and NOTHING ASSERTS EITHER FACT.

**THE PROSE WAS NARROWED WHEN CS-871 WAS FILED; THE ASSERTION WAS NOT WRITTEN.** So the
present state is a correct sentence with no arm behind it, which is precisely the shape
CS-871 existed to stop one layer up.

**A SIZE FLOOR IS PROBABLY THE HONEST SHAPE.** A real body is a save's whole world and a
synthetic fixture is a few hundred bytes, so the two populations are separated by orders
of magnitude rather than by a name. An enumeration would have to be re-derived every time
a call site moves, which is the hand-list fault this project has measured repeatedly.

**DO NOT CLOSE THIS ON THE ZERO-OVERLAP MEASUREMENT.** That number was true when an
adjudicator took it and says nothing about the next session. The clause asks for an arm.

### Acceptance

the disjointness is asserted rather than described, by a criterion that survives a real body being handed to the guarded set - a size floor is the honest shape, because a real body is a save's whole world and a synthetic fixture is a few hundred bytes - proven by an arm that reddens when a dynamic-case body is planted into the enumerated set

### Full headline

`tests/save/test_independent_table.py::_bodies_no_dynamic_case_may_reuse` enumerates only the bodies its own module builds, while `tests/save/test_struct_interior.py` and `tests/save/test_struct_controls.py` together call `independent_table.independent_records` at four sites in the same process - the residue was written before that module split and named only the first file, so a close that greps one of them covers half the population - an adjudicator MEASURED that all four hand over real decompressed save bodies and that the two sets have zero overlap, so no collision exists today and NOTHING ASSERTS EITHER FACT - the prose was narrowed to the module scope the guard measures when CS-871 was filed; the assertion was not written


## CS-1077

### Filed 2026-09-14 (queue lane), from the CS-871 verifier pass

**THE DEFECT, AS MEASURED RATHER THAN AS REASONED.** A refutation pass rewrote every occurrence
of `objects._read_tag_header` in `tests/save/test_byte_order_status.py` to a name bound nowhere in
the repository, in memory, and `unresolved_roles` returned an empty list. The control - the same
dead name written WITHOUT the `objects.` head - was reported. So the guard's coverage of a dotted
target is decided by whether its head happens to be bound locally, which is not a property anybody
chose.

**WHY IT IS WORSE THAN AN ORDINARY GAP.** `tests/sphinx_role_guard.py` tells a reader to repair an
unresolved role by QUALIFYING it. Qualifying with a locally imported head is exactly the move that
takes the role out of the checked population. The recommended repair reduces coverage.

**THE TWO HALVES ARE ONE ROW AND SPLITTING THEM SHIPS A RED TREE.** `dotted_target_resolves`
resolves a prefix by looking for a FILE under the repository root, so a stdlib head answers False.
Today that is harmless because every such role sits in a module that imports its head and the short
circuit rescues it - two defects cancelling. Remove the short circuit alone and the corpus reports a
finding on every correct stdlib-headed role. The refutation pass counted the short-circuited
population at 124 sites and separately proved none of them is dead, so the corpus is clean and the
repair must keep it that way.

**DO NOT CLOSE THIS BY DELETING THE SHORT CIRCUIT AND WIDENING THE FLOOR TO ABSORB THE NOISE.** A
guard that reports correct prose is a guard somebody switches off, which is the finding
`tests/test_docs_citations.py` records about itself in six numbered traps.

### Acceptance

the tail of a locally-headed dotted target is resolved against the module the head was bound from, an importable non-repository head resolves by attribute lookup rather than by file test, and both are proven by a planted dead tail under a bound head that reddens AND by the shipped corpus staying at zero findings

### Full headline

`tests/sphinx_role_guard.py::unresolved_roles` accepts a dotted role target whole as soon as its HEAD is a name the citing module binds, and never looks at the tail - so `objects._read_tag_header` resolves for any spelling after the dot, measured by a refutation pass that renamed all fourteen occurrences in `tests/save/test_byte_order_status.py` to a symbol bound nowhere and got an empty finding list while the unqualified control was reported - and this is the guard's OWN recommended repair shape turning off its own coverage, because qualifying an unresolved role with an imported head moves it from the checked path to the unchecked one - THE TWO HALVES SHIP TOGETHER OR NEITHER DOES: `dotted_target_resolves` answers False for a head with no file at the repository root, so `ast.parse` and `json.dumps` are resolved TODAY only by the short circuit this row removes, and removing it alone manufactures a finding on every correct stdlib-headed role


## CS-1078

### Filed 2026-09-14 (queue lane), from the CS-892 verifier pass, MEASURED BEFORE FILING

**BOTH HALVES WERE MEASURED BY THE VERIFIER, NOT REASONED FROM THE SOURCE.** It confirmed
CS-892 and then reported these two as residuals it explicitly did not refute on, because
neither touches the clause CS-892 was graded against. They are filed rather than repaired
in place for exactly that reason: the row that was open asked for one owner and got one.

**HALF ONE - THE DUPLICATION EXTRACTOR READS ONE ASSIGNMENT FORM.**
`tests/test_memory_sync_link_derivation.py::_compiled_literals_of_text` walks
`ast.parse(text).body` and skips every node that is not an `ast.Assign`. An annotated
assignment is an `ast.AnnAssign`, a different node type, so `_X: Final = re.compile(...)`
declares a pattern the extractor reports nothing about. That spelling is not hypothetical
here - `tests/surface/test_acceptance.py::_BACKTICKED` is written as
`_BACKTICKED: Final = re.compile(...)`,
so it is the form this repo's own modules already prefer for a module-level constant.

**HALF TWO - THE WALK IS HELD ONLY BY THE DERIVATION BENEATH IT.** The verifier built a
`tools/memory_sync.py` that re-declares the transitive-through-index walk while still
calling `drift_guard.link_targets`, and ran the arms against it: `7 passed`, exit 0. That
mutant is a genuine second copy of the walk. It survives because CS-892's clause proves
through a link shape taught to ONE COPY of the DERIVATION, and the mutant leaves exactly
one derivation - so the clause is satisfied while the duplication it was filed against has
partly grown back. The AST arm does not catch it either, because a duplicated walk carries
no regex literal.

**WHY THE SECOND HALF IS THE SHARPER ONE.** The first is a blind spot in an extractor and
is repaired by reading one more node type. The second is a clause that cannot see its own
subject: the drift class CS-892 removed was TWO THINGS duplicated - the patterns and the
walk over them - and the arms that survived it grade only the first. A future session
reading the CS-892 entry will reasonably believe both are held.

**THE PLANT IS ALREADY WRITTEN AND MUST NOT BE RE-ARGUED.** The verifier's mutant is the
positive control for the second arm: re-declare the walk in `tools/memory_sync.py`, keep
the `drift_guard.link_targets` call, and require the suite to redden. An arm that cannot
kill that exact mutant has not closed this row, whatever else it proves.

**DO NOT CLOSE THIS BY ASSERTING A NAME.** `memory_sync.reachability is
drift_guard.reachable_from_index` is a spelling measure and reports a clean verdict about
the wrong question the moment a name moves - the same reason CS-892's own arms were written
behaviourally. `tests/test_memory_sync_link_derivation.py`'s module docstring records that
choice and the reasoning behind it.

### Acceptance

the duplication extractor reads annotated assignments as well as plain ones, proven by a planted `Final`-annotated duplicate that reddens it, AND the walk is held by an arm that reddens on the verifier's exact mutant - a second walk that consumes the owner's derivation - with that mutant PLANTED rather than argued, and neither arm closes this by asserting a name, which is a spelling measure the CS-892 module docstring already rejects

### Full headline

the two arms that stop `tools/memory_sync.py` re-growing a copy of the link derivation each have a spelling they cannot see, MEASURED by the CS-892 verifier rather than argued: `test_no_regex_literal_is_declared_in_both_tools` walks `ast.Assign` alone, so `_X: Final = re.compile(...)` - an `ast.AnnAssign`, and the form this repo's own modules already prefer at `tests/surface/test_acceptance.py::_BACKTICKED` - declares a duplicate the extractor reports nothing about, and separately a `tools/memory_sync.py` that re-declares only the WALK while still calling the owner's `link_targets` survived all seven arms at `7 passed` exit 0, because CS-892's clause proves through a link shape taught to ONE copy of the DERIVATION and that mutant leaves exactly one derivation while being a genuine second copy of the walk


## CS-1001

### Acceptance

an arm asserts that the set of loaded module objects whose `__file__` resolves to `lanes.py` has exactly one member, derived by walking `sys.modules` rather than by naming the two private names, and reddens when a second object is introduced under any third name - NEVER a floor over the count

### Full headline

the CS-1000 repair's correctness rests entirely on there being exactly ONE `lanes` module object in a process, and NOTHING asserts that: `_OWNED` is written unconditionally on every successful acquire, which is what makes `release_lane`'s and `repoint_lane_pid`'s refusal paths unreachable, so the single-instance property is the load-bearing precondition for a guarantee held BY CONSTRUCTION rather than by a check - the moment a second object maps to `lanes.py` the deleted trigger returns and the lane silently stops looping again, which is exactly how this defect ran for two nights

## CS-1002

### Acceptance

a refused release leaves no ownership entry and a refused repoint either updates state or is proven idempotent, with an arm per site driving the refusal directly rather than through a whole cycle

### Full headline

`ops/loop/lanes.py` keeps its ownership entry on a REFUSED release and changes no state on a REFUSED repoint: `release_lane` returns False at two sites without popping `_OWNED[key]`, and `repoint_lane_pid` returns False at three sites before writing `_OWNED`, so an identical refusal repeats every cycle forever rather than resolving - both are latent while exactly one lanes module exists, because the unconditional write on acquire deletes their trigger, so this item and CS-1001 are the two halves of one guarantee

## CS-1003

### Acceptance

either the parents are bound so the statement form works, or an arm pins that no tracked module uses the statement form for these names, with the consumer population DERIVED by AST rather than grepped

### Full headline

`sys.modules.setdefault` publishes the by-path `lanes`, `lane_launcher` and `winmutex` modules under their canonical DOTTED names while neither `ops` nor `ops.loop` is in `sys.modules`, so a parentless child is bound: `import_module` and `from ops.loop import x` both resolve it, but the STATEMENT form `import ops.loop.lanes` now succeeds silently and then raises `AttributeError: module 'ops' has no attribute 'loop'` at an arbitrary later attribute access, converting a loud `ModuleNotFoundError` into a quiet one - measured unreachable today, all seven consumers using the `from` form and the driver never gaining the repo root, so this is a latent trap rather than a live regression

## CS-1004

### Acceptance

the comparison is over the name-to-value MAPPING or a multiset rather than a set, and reddens on a duplicate-valued constant, proven by an arm that plants one

### Full headline

the launch-reason vocabulary is graded by SET equality, so a duplicate-VALUED `REASON_*` constant is invisible: binding a second name to an existing string leaves both enumerations equal as sets while the two names collapse to one reachable reason, and a reason that should exist but was never declared is invisible to both enumerations because they share one file as ground truth

## CS-1006

### Acceptance

either the restore is made unable to overwrite a claim created after the grade, or the window is proven harmless by an arm that drives the interleaving at the seam rather than by argument, with a control on a separate root proving a reclaim of the record AS GRADED does still remove it - NEVER closed by a floor over a retry count, which is the CS-988 shape and is forbidden here by name after twelve measured instances plus seventeen from the phase-6 sweep

### Full headline

`ops/loop/claims.py`'s `_reclaim` still has a RESTORE window a filesystem cannot arbitrate: the unguarded unlink CS-991 was refuted for is replaced by a RENAME, which exactly one racer can win, and the carried bytes are compared against the ones that were GRADED so a racer whose record was already replaced cannot have a live claim carried away - but a record RESTORED after a failed reclaim can land on top of a claim created in that same moment, because no filesystem offers an atomic compare-and-swap - the sibling window between the rename and the caller's exclusive create is CORRECT by contrast, since the create then refuses the original caller and only one holder survives, so this item is the restore path ALONE - disclosed by the builder rather than found by a grader, recorded in `_reclaim`'s docstring, much narrower than what it replaced, and NOT MEASURED by anything

## CS-1007

### Acceptance

the driver establishes, across the worker-cycle window it already polls, whether a foreign suite ran concurrently, and marks the cycle row unmeasurable when one did, with the observation DERIVED rather than declared and an arm that reddens when a concurrent run is present and the row still reads earned, plus a control proving the same arm passes when no foreign suite ran - NEVER a floor over an overlap count, which is the CS-988 shape and is forbidden here by name

### Full headline

the pre-push hook's xdist suite is outside every ration and cannot be brought inside one: the operator's frozen-file grant on `.githooks/pre-push` was recorded and left UNSPENT because no wait ceiling is both useful and non-hanging, and because the only working mechanics move a tier-0 gate's exit-code fidelity into a non-frozen module - both grounds are in `docs/LEDGER.md` under CS-993 and neither is to be re-litigated, nor is the `PYTEST_ADDOPTS` injection route, which fails open and silent - so the collision is not PREVENTABLE from this repo and the harm must instead be DETECTED: an unattended lane writing a green it did not earn

## CS-1010

### Acceptance

lane liveness is decided by attempting to open the lock's recorded mutex name rather than by probing a pid, with the name DERIVED from the lane and the run id, proven by an arm where the holder dies and the lane reads free with no start time readable anywhere, and by a control where a live holder still reads RUNNING under the same unreadable start time - NEVER by a floor over a lock age, which is the CS-988 shape and is forbidden here by name

### Full headline

a lane lock proves its holder with a (pid, start time) pair, and both halves fail together: `lanes.proc_started` returns None when psutil is absent, which `pyproject.toml` declares optional, and ALSO when the live query raises `psutil.AccessDenied` for a driver running elevated or under a scheduled-task account - measured on this box with psutil present - so `holder_is_a_stranger` waves the case through by design and a lock left by a dead driver whose pid the system reissued reads RUNNING forever, wedging the lane and, since CS-1009 anchored a row's liveness on that lock, wedging every row that lock's cycle claimed - the adjudicator that ruled CS-1009 onto strict delegation named the escape from this as the only behaviour taking NEITHER the wedge nor the double-booking, and it is derivable rather than tuned: `ops/loop/winmutex.py` already holds a kernel named mutex, the operating system releases a dead holder's handle without being asked, and a reissued pid cannot fake one

## CS-1063

### Acceptance

a guard grades every memory leaf's frontmatter and reddens on the leaf named above with that leaf unmodified, the arm covers a missing block AND a malformed one rather than only the first, and `tools/memory_sync.py` either names the guard that actually implements the check or stops naming one

### Full headline

`tools/memory_sync.py` prints FRONTMATTER PROBLEMS and then says they "do not change this exit code, because `tools/drift_guard.py` is the gate that fails on them", and that gate DOES NOT IMPLEMENT THE CHECK - the word frontmatter has zero hits in it and its eleven guards grade character set, the memory partition, doc topology, the port record, frozen files, dated sections, doc budgets, the version pin, work items, item notes and the tier 1 budget, none of them a leaf's opening block - measured 2026-09-14 with both tools exiting 0 on a tree where 1 of 21 memory leaves is invalid: `memory/full-authority-adjudicate-do-not-ask.md` opens with a heading and carries no `---` block at all, so a directive the repo calls binding on every session shape is unreachable to anything that reads leaves by frontmatter - THE INVALID LEAF IS LEFT IN PLACE DELIBERATELY as the reproduction, because repairing it first would hide the gap behind a clean report

## CS-1092

### Acceptance

both floors are re-derived from a measured population minus a small stated margin rather than left at a historical value, and the new module carries a carrier-scoped floor of its own, each proven by a plant that empties the population it bounds and reddens the arm

### Full headline

`_SELF_SPELLED_FLOOR` in `tests/test_docs_citations.py` stayed at its filed value while CS-1066 halved the population it bounds, so the floor now carries enough slack that the arm would pass with most of its subject gone - the identical fault the same slice repaired at `_WALKED_MODULE_FLOOR`, left unrepaired one constant over - AND `tests/test_citation_tables.py` spells bare paths of its own with NO self-infliction arm scoped to it, so its sites are judged only by the pooled population floor, which is a threshold met by its strongest member

## CS-1094

### Acceptance

each named spelling is either caught or DISCLOSED in the guard's own docstring as a stated bound of the mechanism, with an arm per caught spelling planted against the real source in both directions

### Full headline

`derived_bound_problems` in `tests/bare_path_guard.py` reports a bound computed from the table it bounds only for a module-scope `Assign` or `AnnAssign` whose value walk reaches an `ast.Name` or, since CS-1066, an `ast.Attribute` - so `getattr(tables, "X")`, `vars(tables)["X"]`, `tables.__dict__["X"]`, a tuple-unpack target, an `AugAssign`, and ANY assignment not at module scope all still evade it, each confirmed by a refutation pass to evade in the bare-name form too and so PRE-EXISTING rather than created by the split - the docstring discloses the one-hop helper residual and not these

## CS-1070

### Acceptance

each of the two children's cost is measured on the RUNNER rather than locally, a bound is chosen from that measurement or the module is recorded as deliberately unchanged with the number that decided it, and any bound that ships is graded by an arm that reddens on `-n auto` and on an uncapped worker count - SEQUENCING, and it is a hard constraint rather than a preference: `tests/data/` sits in tier 1's CATCH-ALL shard, so landing this while CS-1060's three-reading series is being collected invalidates the series

### Full headline

`tests/data/test_phase2_gate.py` and `tests/save/test_workdir.py` each run a nested child pytest SERIALLY while their parent holds `-n auto`, the same shape that crossed the 300 second child timeout on tier 2's windows leg and was repaired for `tests/save/test_phase4_gate.py` by bounding the child at a measured four workers - neither of these two is measured by anyone, and `test_workdir.py`'s child runs ONE module at 1.21s serial so it may well deserve no change at all, which is the finding rather than a caveat: the repair is per-workload and a shape match is not a reason - NOTE `tests/solve/test_phase3_gate.py` shared this shape at 87s on the runner and needed NO repair, because the CS-302 trim cut the oracle its child re-ran and the gate fell out of the slowest-15 by itself

## CS-1071

### Acceptance

one arm asserts the two readers return the SAME job-id set for the shipped workflow and reddens on a job declared in a shape only one of them parses, with the disagreeing shape PLANTED rather than argued, and the arm names which reader missed it rather than reporting a bare inequality

### Full headline

`.github/workflows/tier1.yml` is parsed by TWO independently hand-rolled readers that never check each other, and both of CS-1060's new guarantees rest on one of them: `every_parsed_job()` in `tests/test_tier1_budget.py` reads full structure and feeds every partition arm, while `declared_job_names()` in `tests/test_queue_loop_ci_specs.py` reads line shape - a job key at two spaces, then its `name:` at four - and feeds the reverse job-to-matcher coverage arm, so a job declared in a shape only ONE of them recognises is invisible to the other and the `{fast, save, guards}` control passes while the partition arm sees two shards - this is a COMMON-MODE risk named by an adjudicator over ea3591a, not a defect observed in the shipped tree, which currently declares all three jobs in a shape both readers accept

## CS-1129

### Acceptance

every row form refuses a doubled space, a case change and a zero-padded number at EVERY token boundary, and an empty or inverted range is a problem, proven by plants generated per boundary rather than listed by hand and by each of the nine recorded loosenings reddening the file

### Full headline

the leaf membership rule grammar in `tools/drift_guard.py` is closed only at the positions its residue plants perturb: MEASURED 2026-09-17 by the CS-1079 re-adversary, nine in-memory loosenings in the MIDDLE of the older row forms (for example `ID BELOW\s+the`, `at\s+or above`, `Phase\s+`, `(?i:ID) in the`) each left `tests/data/test_item_notes_index.py` at 125 passed while accepting a row the pristine grammar refuses; a zero-padded phase number such as `Phase 05` still parses; and the parser accepts an empty or inverted range without a problem (`CS-0nn` block at or above CS-1000 gives low 1000, high 100)

## CS-1119

### Acceptance

EITHER shape is read with every width taken from the bytes or from a shipped constant and never from `declared_end - terminator_end`, with the carrying classes DERIVED off the body rather than transcribed, proven by a skip-if-absent real-library test reporting COUNTS ONLY plus an arm that REFUSES the same bytes when the declared end is moved past what the prefixes describe; a partition of either shape that sums to the declared end closes by arithmetic, cannot fail, and is the defect that refuted CS-830 after it had merged

### Full headline

two trailing-run remainder shapes are left after CS-828's reference-pair reading and neither is derivable by that grammar: a four-byte all-zero residual that is BYTE-IDENTICAL to an empty item list, so no reading of the run can tell a class that carries an empty list from one that carries no list at all (the CS-1068 root cause, restated on the other side); and one class whose remainder is a large nested structure whose width nothing in the run describes
## CS-1089

### Acceptance

the module is brought under 90 percent of that ceiling BY RELOCATION to a sibling under `tests/`, never by deleting an arm and never by raising the ceiling, with the collected-arm count asserted EQUAL before and after, and its row retired from the approach arm's baseline table in `tests/data/test_phase2_gate.py`, which reddens on a stale row

## CS-1090

### Acceptance

the module is brought under 90 percent of that ceiling BY RELOCATION to a sibling under `tests/`, never by deleting an arm and never by raising the ceiling, with the collected-arm count asserted EQUAL before and after, and its row retired from the approach arm's baseline table in `tests/data/test_phase2_gate.py`, which reddens on a stale row

## CS-1091

### Acceptance

the module is brought under 90 percent of that ceiling BY RELOCATION to a sibling under `tests/`, never by deleting an arm and never by raising the ceiling, with the collected-arm count asserted EQUAL before and after, and its row retired from the approach arm's baseline table in `tests/data/test_phase2_gate.py`, which reddens on a stale row

## CS-1122

### Acceptance

a hand-authored IR describing the module map renders through a renderer written in Python in this tree to a committed static SVG/HTML diagram that uses a system font stack and carries no third-party marks, icons or fonts, with no Node anywhere in the build; ZERO BYTES are copied from archify, whose adoption was DECLINED as CS-1098 on the `CLAUDE.md` section 7 Node fence and on its output embedding MIT viewer code without notice plus an OFL font; and a CI drift arm, needing no network and no renderer outside this tree, reddens when the IR's module set stops matching the module map `docs/ARCHITECTURE.md` owns, proven by a planted rename that turns it red

### Full headline

our own Python renderer from a hand-authored architecture IR to a static SVG/HTML module diagram, the re-implementation the CS-1098 decline in `docs/LEDGER.md` filed in place of adopting archify

---

## CS-1130

### Filed 2026-09-17 by the CS-971 merge, from that item's verifier

### Acceptance

a relocated acceptance clause cannot be weakened without a guard reddening, proven by an arm that edits one section's acceptance body and goes RED, and by a control showing an honest reword that preserves the criterion is distinguishable or, if it is not, by a recorded ruling that the check is byte-equality against a pinned record with the pin's own provenance stated

### Full headline

a relocated acceptance clause is never compared against what its line carried, so a later truncation of a section's `### Acceptance` body is undetectable - MEASURED 2026-09-17 by the CS-971 verifier and recorded as a known gap in `docs/adr/0022-acceptance-lives-in-the-item-note.md`: guard (j) grades that a pointer line's section carries exactly one non-empty acceptance and that a short title derives from its filed headline, and nothing grades that the clause itself still says what the line said when it moved, so a later edit that weakens a criterion reads clean - this is the same fault class the CS-971 first design shipped and an adversary caught by reading the diff rather than by a guard

---

## CS-1131

### Filed 2026-09-17 by the CS-971 merge, from that item's verifier

### Acceptance

an id that has appeared in this tree and now exists in no owner file is reported, proven by an arm that deletes a line without a closure record and goes RED, with the population of ids the check knows about derived rather than listed

### Full headline

guard (i) is blind to an id that exists in NO state - MEASURED 2026-09-17 by the CS-971 verifier: `tools/drift_guard.py` guard (i) grades id COLLISIONS between the four owner files and unaccounted owner files, so an id removed from `ROADMAP.md` with no `docs/LEDGER.md` entry is owned by zero files and the guard stays SILENT, which is exactly the state CS-1033 sat in between its line being deleted and its ledger entry being written, while `docs/item_notes.md` and ADR 0022 both asserted that the ledger entry was its record

## CS-1133

### Filed 2026-09-17 by the CS-917 cycle, from that item's own measurement

**THIS IS THE HALF OF CS-917 THAT CANNOT BE SHIPPED, AND IT IS A FEASIBILITY
RESULT RATHER THAN AN UNFINISHED BUILD.** CS-917 asks that the warn band not be
narrower than the noise figure it is DERIVED FROM, so a warn is reachable before
a red. **BOTH HALVES OF THAT PHRASE ARE OPEN AND THE CS-917 VERIFIER CORRECTED
THIS SECTION'S FIRST DRAFT FOR NAMING ONLY THE WIDTH.** The shipped band is the
value CS-1060 left in the workflow and the tool READS it; no figure sized it.
Reading a level is not deriving one, and an arm that only compares width would
certify a band nothing derived. `tools/tier1_growth.py` now measures that figure per job and reports the
verdict; the figure and every reading behind it live in `tools/tier1_readings.json`
and are restated nowhere. For two of the three jobs the band covers the figure.
For the fast shard it does not, and `ORDERING_UNMET` in the tool names it.

**WHY NO CHOICE OF LEVELS FIXES IT, which is the part a later session will want
to re-pitch.** Write `M` for the job's worst reading, `N` for its jitter, `B` and
`C` for the budget and the ceiling, and the job's `timeout-minutes` as the cutoff.
CS-896's leaf derives the three requirements - no false warn needs `B >= M`, a
warn before a red needs `C - B >= N`, and a red rather than a cancel needs
`C + N <= cutoff`. At this job's measured `M` and `N`, read from the tool rather
than transcribed here, the window `[M, cutoff - 2N]` is EMPTY. So the remainder is
not a better pair of numbers and any cycle that goes looking for one is repeating
a measurement already taken.

**AND THE LEVELS ARE RATCHETED ANYWAY.** Guard (k) of `tools/drift_guard.py` pins
the budget, the ceiling and the cutoff in BOTH directions, and `.github/workflows/`
is not on the frozen list but the ratchet is a deliberate fence - CS-1060's comment
block in the workflow records that the ceiling was NOT raised when the fast shard
passed it, and that raising a level to meet a slow lane is the move CS-896 exists
to refuse. **DO NOT close this item by moving a level.** Two of the three moves are
blocked by arithmetic and the third is blocked by a ruling.

**SO THE ONLY ROUTES LEFT, and both are outside this row's own hands.** Reduce the
fast shard's run-to-run jitter, which is a property of the runner pool this project
does not own and of the work the shard does - CS-900 owns the concentration half.
Or raise the cutoff, which is an operator ruling against CS-896's stated refusal
and needs its own record. A cycle that wants neither should leave this row alone:
the condition is MEASURED and REPORTED today, and a reported unmet condition is
worth more than a synthetic close.

**WHAT WOULD MAKE THIS CLOSABLE WITHOUT EITHER.** A warn that does not live in the
gap between two level constants - for instance a per-job comparison against that
job's own recent readings rather than against a tree-wide budget. That is a design
change to the reporting step in the workflow and it is not this row as filed; if a
session builds it, file it as its own row and say plainly that CS-1133's clause was
answered by removing the band rather than by widening it.

### Acceptance

every tier 1 job's warn band is DERIVED FROM that job's own jitter figure rather than read as a standing constant, AND covers it, with the figure derived by the criterion `tools/tier1_growth.py` already ships and any level moved only under a recorded ruling, proven by `ORDERING_UNMET` in that tool being EMPTY over a refreshed record, by the two-way arm in `tests/test_tier1_growth.py` that reddens when it is not, and by an arm that reddens when the band is a constant no figure sized

### Full headline

the tier 1 fast shard's warn band is narrower than its own run-to-run jitter - MEASURED 2026-09-17 by `tools/tier1_growth.py` over the readings in `tools/tier1_readings.json` - so a rising reading on that job can reach the ceiling without ever having landed in the band, and the feasible window over the budget, the ceiling and the cutoff is EMPTY at that job's worst reading and jitter, which makes it a ruling or a jitter reduction rather than a choice of numbers

---

## CS-1134

### Filed 2026-09-17 by the CS-917 cycle, from that item's verifier

**NEITHER VECTOR IS LIVE ON TODAY'S RECORD AND THAT IS WHY THIS IS A ROW RATHER
THAN A REPAIR.** Both were found by the CS-917 verifier AFTER the candidate was
frozen, and repairing them then would have produced a change that verifier never
saw. Filed, not fixed, on the rule that a repair landed during a verdict is one
the verdict cannot discharge.

**VECTOR ONE - A RE-RUN ATTEMPT IS DROPPED.** `readings` in
`tools/tier1_growth.py` keeps one reading per run id, because one run copied
several times into the record must not satisfy the reading floor several times
over. But a job RE-RUN inside a single workflow run carries the SAME run id, so
its second attempt's duration is discarded. If the two attempts differ widely,
the step between them is invisible and the jitter figure UNDERSTATES the lane's
movement - which is the one direction that figure must never fail in, because an
understated figure makes the ordering verdict read green for the wrong reason.
The shipped record carries no duplicate job-and-run-id pair, so nothing shipped
rests on it today.

**DO NOT FIX IT BY DROPPING THE DEDUPE.** That reintroduces the defect
`test_one_run_copied_five_times_is_one_reading_not_five` exists to refuse. The
fix has to tell a RE-RUN ATTEMPT apart from a COPIED ROW, and the jobs API
reports an attempt number that the record does not currently keep - so this is a
record field plus a key change, and the record must be refreshed to carry it.

**VECTOR TWO - THE ANTI-TRANSCRIPTION ARM SKIPS WHERE IT SHOULD REDDEN.**
`test_the_recorded_commit_distances_agree_with_this_repository` in
`tests/test_tier1_growth.py` skips PER SHA when the checkout cannot place that
sha, which is correct for a shallow clone and wrong for a fabricated one: a sha
that exists nowhere, paired with any distance at all, makes the arm SKIP rather
than fail. `grade` closes part of the gap - it checks the window's two ends - but
a mid-series sha is graded against the repository by nothing. So the arm's claim
is narrower than its name: it catches a distance edited against a commit the
checkout HAS, and nothing else.

**THE SHAPE OF A FIX, STATED BECAUSE THE OBVIOUS ONE IS WRONG.** Reddening on an
unplaceable sha breaks the shallow-clone case the skip was written for and would
ship red in CI. What distinguishes the two is whether the checkout carries the
WINDOW at all: if it carries the window's oldest commit, it is a full clone and an
unplaceable mid-series sha is then a fabrication rather than a missing ancestry.
So the skip belongs once, at the top, on the window - which is already where the
first probe in that arm looks.

### Acceptance

a job re-run inside one workflow run contributes its own reading rather than being dropped, and a recorded commit distance whose sha the checkout cannot place is RED when the checkout carries the window and SKIPPED only when it does not, proven for each by an arm that reddens on a planted record and a control that stays green on the shipped one

### Full headline

the tier 1 jitter figure can UNDERSTATE by two routes the CS-917 verifier found after the candidate was frozen - `readings` in `tools/tier1_growth.py` drops a job's re-run attempt because it dedupes on the run id a re-run shares, and `test_the_recorded_commit_distances_agree_with_this_repository` skips per sha so a fabricated sha and distance pair makes the anti-transcription arm SKIP rather than redden - neither live on the shipped record, both filed rather than repaired because a repair landed after a verdict is one that verdict cannot discharge

---

## CS-1135

### Filed 2026-09-17 by the CS-1123 merge, from that item's adversary

### Acceptance

each of the three surviving mutants is killed by an arm that grades the thing it perturbs - the predicate at a size far above the ceiling, the report line for a file in a NESTED directory rather than a flat one, and the tree listing the real guard is handed rather than one an arm supplies - proven by each mutant reddening its own arm and by an anti-vacuity control at the same inputs that stays green unmutated, with every size and every path derived rather than spelled

### Full headline

`_oversized_over_the_ceiling` in `tests/data/test_phase2_gate.py` is closed only at its lower edge, so three mutants survive the whole module green - MEASURED 2026-09-17 by the CS-1123 adversary across 17 plants: bounding the predicate as a BAND rather than a floor lets an artifact far above the ceiling escape silently, because no arm plants higher than the ceiling plus 19 bytes; rendering the report line from the file name instead of the path taken relative to the root leaves the nested-path contract ungraded, because both planting arms build their files flat in a temporary directory; and filtering the tree listing that feeds the real guard is unseen, because both arms supply their own lists and neither exercises the listing the guard is actually handed - each is killed by a concrete value, so all three are surviving mutants rather than equivalent ones

---

## CS-1136

### Filed 2026-09-17 by the CS-1132 adversary pass

### Acceptance

a LIVE document that points at an item-notes leaf for an id with no section in that leaf is reported, with the population of pointers DERIVED rather than listed and a pointer distinguished both from a leaf-table RANGE SELECTOR and from a mention of the item that CAUSED a change, proven by an arm that plants such a pointer and goes RED, by an anti-vacuity control over the same bytes that stays green unplanted, and by the check staying SILENT on every one of the eight shapes the 2026-09-17 sweep produced as false positives; `docs/LEDGER.md` is out of scope because its own rule forbids editing a written record, and `docs/history_notes.md` is out of scope because its header declares that nothing in it may be acted on without re-verifying live

### Full headline

no guard grades a live document's pointer into an item-notes leaf, so a live file can route a reader to a section that no longer exists - MEASURED 2026-09-17 twice over: the CS-1132 adversary looked for such a guard across `tools/`, `tests/test_docs_citations.py` and `tests/test_citation_tables.py` and found none, and a derived sweep over every tracked markdown file outside the append-only record then found the live instance, `docs/ARCHITECTURE.md` routing the cost of the second world-body pass to `docs/item_notes/phase4-followups-900.md` under CS-961, dead since that item closed and its section left the family, while `tools/drift_guard.py` exited 0 across 11 guards and 517 citation and liveness arms passed over the same bytes; that pointer is repaired in the CS-1132 merge and the GUARD is what this row owns, because the five further pointers CS-1132's own relocation falsified all sit in files nothing may edit, and the next relocation will falsify more; the sweep that found it also produced eight false positives, every one a leaf-table range selector or a mention of the item that caused a change rather than a pointer at its section, so telling those apart is the part of this row that carries the risk

---

## CS-1137

### Filed 2026-09-17 by the CS-1132 second repair round

### Acceptance

each arm binds the shipped VALUE of the constant it grades, proven by every arm in the module that monkeypatches a leaf-rule constant reddening on a plant that MOVES that value - not only on a plant that removes the constant from the probe tuple - with an anti-vacuity control at the same inputs that stays green unmutated, and with the population of such arms DERIVED from the module rather than listed, so a third arm of the same shape cannot be added without the derivation reporting it

### Full headline

two arms in `tests/data/test_item_notes_index.py` bind only their constant's MEMBERSHIP in the probe tuple and are blind to its VALUE - MEASURED 2026-09-17 by the CS-1132 second repair round and DERIVED from the module's own syntax tree rather than read by eye: of 97 test functions exactly two call `monkeypatch.setattr` and then assert, one patching the `CS-8nn` seam constant and one patching the `CS-1nnn` floor constant, and each killed 1 of 5 plants - GREEN on every plant that moved the value (860, 820, 870 and 899 for the seam; 1100, 900, 1200 and 1050 for the floor) and RED only when the constant was dropped from the probe tuple altogether, with the control GREEN on every row; this is the identical shape CS-1132 found in the `CS-9nn` seam's arm, where it killed 0 of 9 and was replaced by an arm that leaves the shipped constant alone and plants the edit a person would actually make, so the repair pattern is already established in the same module
## CS-1138

### Filed 2026-09-17 by the CS-920 cycle, from that item's verifier

**THE VERDICT WORD IS NOT DEGRADED BY ITS OWN BASIS.** `survives_next_reading` in
`tools/measurement_record.py` reports a verdict AND the comparability the pair
rests on. A pair where both readings carry an escape value agrees about nothing,
and the query says so - `basis: unproven` - but the verdict still reads
`survived` or `falsified`. **A ROW LIFTED FROM THAT OUTPUT WITHOUT ITS BASIS
REPRODUCES EXACTLY THE FAILURE CS-920 WAS FILED ABOUT**, which is a figure quoted
out of the conditions it was taken under.

**DO NOT FIX IT BY REFUSING THE PAIR.** Refusing would lose the only signal an
all-escape history has, and the escape values exist precisely so a reading with
no recorded worker count is KEPT rather than dropped. The fix is in the verdict
vocabulary: a verdict reached on an unproven basis needs a name of its own that
carries the qualification into any quotation of it.

**NOT LIVE ON TODAY'S RECORD, AND FILED RATHER THAN REPAIRED FOR THAT REASON.**
Every bound metric in `tools/measurements.json` holds one reading, so every
verdict today is `untested` and no unproven verdict is printed at all. It was
found after the CS-920 candidate was frozen, and a repair landed during a verdict
is one that verdict cannot discharge.

### Acceptance

a verdict reached on a pair whose basis is not `comparable` carries the qualification IN THE VERDICT rather than only beside it, so quoting the verdict alone cannot drop it, proven by an arm that reddens when an unproven pair yields the same verdict word a comparable pair does

## CS-1139

### Filed 2026-09-17 by the CS-920 cycle, from that item's verifier

**A FABRICATED READING GRADES CLEAN, MEASURED BY AN ADVERSARY RATHER THAN
REASONED ABOUT.** The verifier added a reading with an invented value, a
seven-character hex string that is not a commit in this repository, and a source
citation whose anchor is the single word `the` - and `grade_tree` returned no
offence. Two checks are weaker than they look: `commit` is matched against a hex
pattern and never resolved against git, and a source anchor is any substring of
the cited file, so a one-word anchor matches almost everything.

**THIS IS A CAVEAT ON CS-920 RATHER THAN A DEFECT IN IT, AND THE DISTINCTION IS
THE ITEM.** CS-920's clause asks that a receipt be CARRIED, and a carried receipt
is what a fabricated row has. What is not established is that the receipt is
TRUE. The record's value rests on rows being written honestly, and a machine
check for honesty is a different property from a machine check for completeness.

**THE OBVIOUS FIX IS HALF WRONG.** Resolving every `commit` against git reddens
in a shallow CI checkout, which is the same trap `tools/tier1_growth.py` already
met and answered by skipping on the window rather than per sha - read CS-1134
before rebuilding that reasoning. An anchor floor is the cheaper half and has no
such problem.

### Acceptance

a reading whose commit the checkout can place is graded against it and a reading whose anchor is too weak to identify a sentence is refused, with the commit check SKIPPED only where the checkout does not carry the history, proven by an arm that reddens on a planted fabricated reading and a control that stays green on the shipped record

## CS-1140

### Filed 2026-09-17 by the CS-920 cycle, from that item's verifier

**CS-917's FIGURE CAN NEVER REACH A COMPARABLE BASIS AS THINGS STAND.** Every
tier 1 reading in `tools/measurements.json` carries `workers: "unresolved"`,
because the lane runs `pytest -n auto` and nothing records what that RESOLVED to.
`nproc` does not answer it - xdist counts PHYSICAL cores, and this project has
already published a worker count of sixteen that was eight for exactly that
reason. So a future pair of tier 1 readings can only ever be graded `unproven`,
and the survives-next-reading query will never say `comparable` about the very
metric CS-917 needs it for.

**THE FIX IS UPSTREAM OF THE RECORD AND THAT IS THE WHOLE POINT.** No amount of
work inside `tools/measurement_record.py` can resolve a number the lane never
emitted. The lane has to PRINT its resolved worker count where a refresh can read
it, which makes this a workflow-and-record change rather than a schema one.

**DO NOT CLOSE IT BY INFERRING THE COUNT FROM THE RUNNER'S CORE COUNT.** That is
the inference that produced the sixteen-for-eight correction, and it is recorded
in this project's own notes as one of the three readings CS-920 was filed over.

### Acceptance

a tier 1 reading records the worker count the lane ACTUALLY RESOLVED, emitted by the lane itself rather than inferred from a core count, and a pair of such readings grades `comparable` in `tools/measurement_record.py`, proven by an arm over the refreshed record

---

## CS-1141

### Filed 2026-09-17 by the CS-1121 close, from that item's final adversary

### Acceptance

a fixture places a DRIFTED entry AFTER the unanchorable one in the order the function actually walks, and asserts BOTH are reported, so swapping `continue` for `break` in the unanchored handler reddens - with a pristine floor showing the same arm green unmutated, and with the ordering dependence made explicit rather than left to `sorted()` putting the healthy entry first

### Full headline

the per-entry unanchored refusal never proves that the entries after it are still graded, so a `break` for `continue` mutant survives every arm - MEASURED 2026-09-17 by the CS-1121 final adversary, which planted that one-token mutation and watched 430 arms pass, exit 0: `test_one_unanchorable_site_does_not_abort_the_other_entries` says in its own words that BOTH directions are graded, the unanchorable entry reported AND the healthy entry beside it still examined, but its two fixture keys sort the healthy entry FIRST, so nothing follows the refusal and the second half is asserted by an absence - a length of one - that holds whether or not the neighbour was ever looked at; the mutant is not equivalent, because under `break` every entry sorted after an unanchorable one goes ungraded, which is precisely the whole-run abort the per-entry refusal replaced

---

## CS-1142

### Filed 2026-09-17 by the CS-1121 close, from that item's final adversary

### Acceptance

the budget comment's stated composition is either re-derived at run time or struck, proven by an arm that reddens when the sum of the two live table lengths disagrees with any figure spelled in that comment block, with an anti-vacuity control showing the arm stays green when they agree

### Full headline

the ratchet's head sentence in `tests/test_citation_tables.py` states a composition the tables no longer have - MEASURED 2026-09-17 by the CS-1121 final adversary: the comment heading the recorded forgiveness budget spells a decomposition into two counts whose sum is 55, while the live tables measure 22 and 38 against a ceiling of 60, and nothing reddens; it is PRE-EXISTING, filed on 2026-09-15 and predating CS-1121, and it sits at the head of a dated append-only ratchet log whose tail records the ceiling walking down through the sixties, so the surrounding history is accurate and only the head sentence is stale - which is the shape `CLAUDE.md` section 4 forbids, a hardcoded count in a doc being a lie with a timestamp on it

---

## CS-1143

### Filed 2026-09-17 by the CS-1121 close, from that item's final adversary

### Acceptance

`heading_chain` either REFUSES a carrier whose file type has no heading syntax or derives a carrier-appropriate anchor for it, proven on a `.py` carrier and a `.json` carrier, and the markdown path blanks code regions through the fence-aware reader `tools/drift_guard.py` already owns rather than a bare `startswith` rule, proven by a fixture whose only column-0 hash sits inside a fenced block and by the live count of such lines in guarded docs falling to zero

### Full headline

the citation site identity derives a markdown heading chain from files that have no headings - MEASURED 2026-09-17 by the CS-1121 final adversary: the carrier population the disposition tables cover is 388 files of which only 74 are markdown, so on 263 of the 314 non-markdown carriers a column-0 hash in a comment is read as a heading and given a level from its run length, while on the other 51 any site raises the unanchored refusal outright; the markdown path is weaker than this tree already is, reading six column-0 hashes inside fenced blocks across three GUARDED docs as headings, two of them at level one so they pop the entire real heading stack, while `tools/drift_guard.py` already owns a CommonMark container reader that handles fences, blockquotes, list content columns and indented blocks and was not reused; today's exposure is zero live corrupted chains and zero live entries on a non-markdown carrier, so this is latent rather than a present fault, and the identity's own docstring discloses the setext and fence gaps while saying nothing about the non-markdown population at all

## CS-1144

### FILED 2026-09-17 by the queue lane, measured while shipping CS-937

**WHAT THE NEW LEG FOUND ON ITS FIRST LIVE READING.** `docs/LEDGER.md` carries a
sentence claiming that CI runs mypy bare at a named line of
`.github/workflows/tier1.yml`. It does not. The workflow grew and that step now sits
far below the cited line; the cited line holds an unrelated fence check. The pointer
was RIGHT WHEN WRITTEN and rotted under growth - the opposite of CS-937's measured
instance, and the reason it is a separate row rather than the rest of that one.

**WHY IT WAS RECORDED RATHER THAN REPAIRED IN THE SAME CYCLE.** `docs/LEDGER.md`
declares itself append-only in its own header, so the pointer cannot be re-cut in
place, and the repair this project states for a rotted pointer - cite the module by
name - is unavailable at a workflow file, which has no symbol form. Both routes the
CS-928 forgiveness grant records are therefore closed here too. The site is carried in
`tests/test_docs_citations.py::UNVERIFIED_POINTER_CLAIMS` with the defect NAMED, and
that record pins the landing so the site cannot drift further in silence.

**DO NOT CLOSE THIS BY RE-CUTTING THE DIGEST.** The record's digest exists to redden
when the landing moves again. Re-cutting it is how a pin absorbs the defect it was
built to count, which is the failure `tests/test_citation_tables.py` names for the
sibling table.

**DO NOT CLOSE IT BY DELETING THE ROW EITHER.** Removing the record without repairing
the pointer makes the live claim arm red, not green - the row is pinned in both
directions by `test_the_recorded_pointer_claims_are_pinned_in_both_directions`.

**WHAT A CLOSE PROBABLY LOOKS LIKE, stated as a starting point rather than a
specification.** Either an appended correcting record that the guard can READ - which
needs the guard to prefer a later correction over the original sentence, and that is
a real design question rather than a tweak - or an adjudicated `Disposition`, which
spends `tests/test_citation_tables.py::FORGIVEN_LINE_POINTER_CEILING` and therefore
needs the grant the CS-928 entry's fence describes. Measure which before building
either.

### Acceptance

the `docs/LEDGER.md` pointer into `.github/workflows/tier1.yml` either names a line whose content its own sentence claims, or carries an adjudicated record that a guard verifies rather than a digest nobody re-reads, proven by an arm that reddens when the recorded answer stops resolving - and `UNVERIFIED_POINTER_CLAIMS` loses the row rather than keeping it

