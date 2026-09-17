# Clockspeed - live per-item detail, phase 4 - save reader, CS-1000 and above

**Section status: LIVE.** A dated heading in this file records provenance - when the
text was filed, moved or measured - and never that the section itself is historical.

**THIS LEAF HOLDS EVERY PHASE 4 ID AT CS-1000 OR ABOVE.** The `1000` in its name is a
FLOOR, not a block: `CS-11nn` and every later block land here too, and the leaf
membership rule in `docs/item_notes.md` spells that floor rather than a block. Its sibling
`docs/item_notes/phase4-followups-900.md` holds the `CS-9nn` block and nothing above it.

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
