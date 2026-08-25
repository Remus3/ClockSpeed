# Clockspeed - Ledger

**Section status: HISTORICAL.** Every section in this file is a record, so a dated
heading here may mark its own section historical.

**Append-only, NEWEST FIRST. One record per closed work item.**

**This file owns:** the per-item completion record - what closed, when, and how to verify
it independently.

**This file never contains:** rules, open work, aspirational items, or architecture. Open
work lives in `ROADMAP.md`, aspirational work in `BACKLOG.md`, externally blocked work in
`docs/GATED.md`, and settled decisions in `docs/adr/` plus the `Settled` section of
`CLAUDE.md`.

Nothing in this file is ever edited or deleted once written. A record that turns out to
be wrong gets a **new, later** record that corrects it and says so. Pruned records move
to `docs/history_notes.md`; they are never dropped.

---

## Entry shape

Newest entry goes directly under the `## Entries` heading. Each entry is:

```
### YYYY-MM-DD - <ITEM-ID> - <one line: what closed>
Verification: <pointer>
```

| Field | Rule |
|---|---|
| Date | `YYYY-MM-DD`, the date the item actually closed. |
| Item ID | The permanent `CS-` ID from `ROADMAP.md`. Never invented at close time, never reused, never renumbered. |
| One line | What closed. One line. If it needs a paragraph it needs its own file and this line becomes a pointer to it. |
| Verification pointer | How someone else confirms it, independently, without asking you. Mandatory. |

An entry may add an `ADR:` line citing `docs/adr/NNNN-*.md` when the item settled a
decision. An entry that closes a gated item states which external condition was met and
who or what observed it.

---

## The verification pointer - what makes one valid

**Cite the item ID, the merged file, and the test name. Do not cite the slice SHA.**

A ledger entry whose only evidence is a commit SHA is **fragile**. The reason is
mechanical, not stylistic: work is produced in worktree-isolated agent slices, and those
slice commits frequently do not survive the cherry-pick into the main line. The SHA in
the entry then refers to an object that is unreachable, or reachable but not the version
that shipped. The entry looks precise and verifies nothing.

The item ID, the merged file path and the test name all survive the merge, because they
are properties of the shipped tree rather than of the branch that produced it.

**Valid pointers**

- `tests/save/test_header.py::test_world_token_stable_across_reload`
- `clockspeed/solve/exact.py` plus `tests/solve/test_exact.py::test_no_float_in_path`
- `tools/drift_guard.py` red-then-green transcript recorded under the item ID
- A named CI job on the tier-1 lane, plus the file it asserts on

**Invalid pointers**

- A bare commit SHA
- "tests pass" or "CI green" with nothing named
- A count of tests with no file and no test name behind it
- A link to a transcript or a chat message

Counts are never restated here as prose. If a count is worth citing, cite the
machine-checked artifact that produces it.

---

## Entries

<!-- Newest first. Append new entries immediately below this line. -->

### 2026-08-25 - CS-845 - CLOSED. The PostToolUse edit check reads the stdin envelope and stops claiming a problem it did not observe - VERIFIED END TO END, by the harness spawning the merged tool itself

**THE FIRST SUCCESS IN THE STORE'S HISTORY.** Before this merge, every PostToolUse record
this machine holds was a non-blocking error: zero successes, zero non-empty stdout, and
essentially all of them rendering the same read failure, for roughly forty sessions. The
tool was handed an argument that expanded to an empty string, so it staged no unit, linted
nothing, and then reported that the edit above left a problem on disk. A gate that always
cries wolf trains its reader to ignore it, which is why this was tier 1.

**Verification, independently reproducible:** run the derived census in
`tests/test_posttooluse_census.py` against the harness transcript store. It re-derives the
population on every run and hardcodes no count. Immediately after this merge it reported
961 records selected, 960 with empty stdout, and exactly ONE with a non-zero-length stdout
and exit 0 - a record produced by the harness firing the hook against the merged tool on a
real edited path. The acceptance test is
`tests/test_edit_lint_check.py::test_an_empty_path_argument_claims_no_problem`, which goes
RED against the pre-merge tool and GREEN against this one.

**THE MECHANISM WAS ESTABLISHED, NOT GUESSED, AND THE ITEM'S NOTE WARNED THAT THIS WAS THE
LIKELY FAILURE.** The message named a read failure and was not one. Measured:
`CLAUDE_FILE_PATHS` is ABSENT from the hook process environment while more than twenty
other `CLAUDE_` variables are present, so the quoted expansion yielded an empty string; the
edited path arrives instead on stdin, as a JSON envelope carrying `tool_input.file_path`.
Corroborated three ways, none of which depends on a probe that no longer exists: the
recorded stderr itself proves the argument was an EMPTY STRING rather than an unexpanded
literal, since the diagnostic renders `Path("")` as `Path(".")` and reports a directory read;
a sibling `PostToolUse` hook belonging to a DIFFERENT project on this machine reads the same
envelope and has been producing real findings all along; and `tools/pretooluse_gate.py`
reads the envelope for the sibling event.

**NO FROZEN-FILE GRANT WAS NEEDED, WHICH WAS NOT THE EXPECTED OUTCOME.** The item's note
routed the invocation half to an adjudicator because it lives in `.claude/settings.json`.
Making `--files` optional and reading the envelope fixes this entirely inside
`tools/edit_lint_check.py`, which is not frozen. `.claude/settings.json` is UNTOUCHED and
the dead argument is harmless; removing it remains optional hygiene that nobody needs to do.

**GRADED BY AN ADVERSARY THAT WROTE NONE OF IT: NOT REFUTED** - the first item in six
sessions to survive grading. That verdict rests on failed refutation attempts, not on
agreement: five over-correction mutants were planted and all five were killed by tests that
were green both before and after the fix, which proves those tests constrain the fixed code
rather than passing vacuously; and an eighteen-case hostile battery found no swallowed
failure - every genuine fault still exits non-zero and every no-observation case exits zero
while SAYING it checked nothing.

**TWO REAL DEFECTS WERE FOUND IN THE WORK AND BOTH WERE REPAIRED BEFORE MERGE.** A test
whose assertion was an algebraic identity and could not fail under any input. And a census
that answered SKIP when its own selector broke, while announcing that the store held no
records - false, it held 959. That second one is THE SAME SHAPE AS THE TOOL BEING FIXED,
one level up: a check that observed nothing, concluded something, and said so with
confidence. It now separates three outcomes, and a broken selector goes RED against an
independent raw line count that shares no parsing and no key name with the selector it
grades. Repairing it surfaced a third vacuous assertion and a pooled threshold over a set,
satisfied by one parseable command out of any number.

**A CORRECTION THIS ENTRY OWES TO TWO EARLIER ONES.** Two citations in this file name
`tools/edit_lint_check.py` by LINE - one at the CS-205 record and one at the CS-838 record.
Both were already stale before this session and this merge moves those lines again. This
file is append-only and they are deliberately NOT edited; this paragraph is the correction.
Cite that module BY NAME, not by line, as `tests/test_edit_lint_check.py` now does.

**WHAT IS NOT CLAIMED.** Why the hook's working directory varies between the main checkout
and a worktree was not established, only observed. It does not affect the fix, because the
envelope carries an absolute path.

### 2026-08-24 - CS-829, CS-839, CS-840, CS-841, CS-842, CS-844 - NOT A COMPLETION RECORD. NOTHING CLOSED. Six items were graded by adversaries and SIX WERE REFUTED; four merged as improvements and every one STAYS OPEN

**THE SESSION'S RESULT IS THE REFUTATION RATE, NOT THE MERGES.** Six items were taken to
adversaries that wrote none of the work. Six came back REFUTED, every one on the same shape:
the acceptance clause was satisfiable without achieving the thing the item exists for. That is
the fifth consecutive session of clauses-met-and-prose-false, and the first where it was
caught on six items before a single closure entered this file.

**WHAT MERGED, AND NONE OF IT CLOSES ANYTHING.**

- CS-841 - the format skip is disclosed without a flag, the two most natural arming mutants
  die, and the anti-lying mechanism is structural: the linter RETURNS whether the check ran
  and the disclosure consumes that boolean, so there is no second derivation to diverge.
- CS-840 - files declare their own status in their header and the guard READS it, which gives
  it the failure direction it never had. Nine plants that previously left it green now fail.
- CS-842 - the shape gate is a named function the controls drive, covering both named modules,
  with its substring boundary shipped as an ASSERTED floor rather than a description.
- CS-839 - every skip reason names what it requires and claims NOTHING about coverage, and the
  citation check was INVERTED rather than enlarged: a citation in a skip reason is refused
  outright, because a citation there IS a coverage claim and nothing here can check one.
- CS-829 - the struct interior population is now decided by arithmetic that never calls the
  decoder. Its predecessor caught NONE of 200000 arbitrary wrong decoders; this catches 3936
  of 4096 whole-word refusal subsets and 2000 of 2000 per-site mutants.

**CS-844 DID NOT MERGE AND THE REASON IS WORTH THE SPACE.** Its widened guard raised four
findings. THREE WERE REAL AND ARE FIXED ON MAIN - it paid for itself before merging. The
fourth is a false positive its own adversary had predicted: a test constant pinning text a
FROZEN HOOK renders is not an owner, and following the guard's advice would have broken a true
assertion. A red suite blocks pre-push, so it stays on its branch. The merger deliberately did
NOT author the exclusion, because an exclusion written by the person merging it is graded by
nobody.

**FINDINGS WORTH MORE THAN THE ITEMS.**

- A GUARD WHOSE ERROR MESSAGE TEACHES THE ATTACK. CS-840's red advised moving the date after a
  provenance verb; doing exactly that laundered a terminal verb and turned the heading green
  with its section still marked historical. A guard that explains how to satisfy it explains
  how to defeat it wherever the two differ.
- FIXED IN THE OWNER, ALIVE IN THE CONSUMER. The dated-heading rule was narrowed in the two
  files that STATE it and left verbatim in three files agents ACT on, which would have made
  the doc-sync agent skip every live per-item note - CS-840's own defect relocated into the
  agent's instructions.
- A CORRECT REJECTION DOES NOT MAKE THE ALTERNATIVE CORRECT. CS-841 refused a bait location on
  a sound measurement and moved it somewhere unmeasured, trading a loud CI flake for a quiet
  hole in the tripwire.
- THE SUITE'S VERDICT DEPENDS ON HOW IT IS INVOKED, TWICE OVER - on which shell runs it
  (CS-839) and on whether it runs in parallel, since the pre-push hook is serial and CI is not.
- AN ADVERSARY SUPPLIED THE FIX, NOT ONLY THE REFUTATION. CS-829's independent criterion came
  from the lens that destroyed its predecessor.

**THREE DEFECTS FIXED THAT BELONGED TO NO ITEM.** The CS-813 fourth leak, salvaged from an
inherited worktree and RE-DERIVED rather than imported - and the probe that re-derived it found
that the oracle this project's own note prescribes cannot observe the leak it prescribes for.
A ledger entry head that parsed to zero ids, leaving one item declared by no file while four
citations pointed at it. And a slash-command example wired to real closed ids.

**SIX ITEMS FILED: CS-845 through CS-850**, plus CS-846 WIDENED the same day on a second
measured instance in a different structure. CS-845 and CS-850 are tier 1. CS-850 was found
independently by three agents in three modules, and the tree had already documented the gap
with nobody owning it.

**THE SEVEN INHERITED WORKTREES ARE RESOLVED** after seven sessions of ambiguity. Every one had
HEAD equal to its base with zero commits, so all their work was uncommitted - which is why
they kept reading as prunable. All committed to their own branches, all deregistered.

**LIMITS OF THIS RECORD.** No item here is closed and none should be read as closed. The four
merges are improvements over what they replaced and each carries measured limits recorded in
`docs/item_notes.md`. CS-829 remains the head of the product path and its central defect is
unsolved: the criterion is arithmetic but the population it grades is still chosen by the
decoder. CS-843 is not closed either, though its first named evidence arm is now MEASURED
EXHAUSTED rather than merely unattempted.

### 2026-08-23 - CS-838 - CI WENT RED on the first push carrying the format check, exactly as this item's own adversary predicted, and the fix was the ruff PIN rather than the gate
Verification: `pyproject.toml` now pins `ruff>=0.13,<0.16` with the reasoning in place.
tier1 on the pushed commit was READ and is GREEN; the preceding commit's tier1 was READ and
is RED. Both conclusions were taken from the run status, not from a watcher's exit code -
`gh run watch` was wrapped in a compound command whose exit was the LAST command's, which
reported success over a failing run. That is the `pytest | tail` trap in a second costume.
WHAT FAILED, and it is worth stating precisely because the gate was NOT wrong. Two arms
assert the format finding NAMES the offending file. Ruff 0.16 reworded the line the gate
reads to recover that name, so on the runner the gate matched no filename and rendered a
placeholder. The gate BLOCKED correctly throughout - exit 1, HEAD unchanged - because
condition FIVE of the grant puts the VERDICT on ruff's EXIT CODE and never on its message.
HAD THE ORIGINAL PREFIX-PARSING PROPOSAL BEEN GRANTED AS WRITTEN, CI's own ruff would have
passed every format violation while reporting success. The adjudicator's refusal to let a
string contract decide the verdict is the reason this was a degraded diagnostic instead of a
silent hole.
THE FAILURE WAS PREDICTED, LOCATED AND RECORDED BEFORE THE PUSH, AND SHIPPED ANYWAY. The
adversary measured the reword on a real commit against an isolated newer ruff, and named the
CI step where it would first appear. Both facts were written into the grant as disclosed
risks. THE SILENT half of that risk was filed as an item; the LOUD half was left as prose and
nothing forced it before the push. **A measured, located, predicted failure is a work item
with a due date, not a residual.** That is the transferable lesson and it is recorded here
rather than in a session note because it is about this item's own handling.
WHY THE PIN AND NOT THE GATE. The gate's behaviour is correct on both versions; what differed
was the toolchain. An unbounded dependency is what made this machine and the runner disagree,
so the divergence is fixed where it was created. Editing the gate would also have meant
amending a frozen-file grant to parse a SECOND output shape - and the newer ruff prints SOURCE
LINES from plain `--check`, so a parser aimed at its output is the change most likely to leak
the very thing conditions EIGHT and NINE forbid.
CS-484 IS NARROWED AND NOT CLOSED. The range still permits drift inside the 0.15 line, and
nothing asserts that the runner and this machine resolve the same patch.

### 2026-08-23 - CS-830 - CLOSED NARROWED. Container element EXTENTS are read over the whole library; the internal PARTITION is recorded as undiscriminated, after an adversary refuted the first close
Verification: `clockspeed/save/objects.py` ships the container element walk plus
`UNDISCRIMINATED_ELEMENT_SHAPES` and `CONTAINER_WORDS_WITHOUT_ELEMENT_GRAMMAR_EVIDENCE`.
`tests/save/test_container_elements.py::test_every_container_instance_in_the_library_yields_a_decoded_element`
holds the equality per word, skip-if-absent and counts only.
THE FIRST CLOSE WAS REFUTED AND THIS ENTRY RECORDS THE REFUTATION RATHER THAN THE CLAIM.
The acceptance clause was MET - equality, not a floor, over every instance of the three
words - and the thing the item existed for was NOT achieved for `SetProperty`. An adversary
that wrote none of the code measured: every `SetProperty` instance in the library is of
`StructProperty` and every one falls to a DERIVED width, pure division, with zero
self-delimiting readings; a large minority are single-slot, where the division is the
identity and grades nothing; and the MEDIAN count of ALTERNATIVE element counts that would
also have divided each region evenly is eleven. A mutant replacing the partition with a
provably WRONG one - first element takes the span less one byte per remaining slot, every
other element takes one byte - still closes the region and still yields the declared number
of elements, and EVERY LIBRARY-BACKED TEST STAYED GREEN. Only a hand-authored fixture
reddened, and that fixture's truth was the implementation's own assumption.
TWO STRUCTURAL CAUSES, both now closed. The evidence-strength guard POOLED all three
container words, so a word that was one hundred per cent derived hid behind another word's
self-delimiting bulk; it now grades PER CONTAINER WORD. And the elements-agree-with-counts
arm was an IDENTITY - the walk appends exactly one element per declared slot with no early
exit - so it could not move independently of the count it was checking. That is recorded as
an identity rather than deleted.
THE LIMIT IS RECORDED AS A TEST THAT ASSERTS ITS OWN SURVIVAL:
`tests/save/test_container_elements.py::test_a_provably_wrong_partition_survives_every_library_backed_equality`.
No test can redden on the wrong partition today without encoding a struct width whose only
source is this module's own belief, which is the circularity the adversary caught. Asserting
the survival gives the limit a FAILURE DIRECTION: the day the corpus discriminates the
partition, that test goes red and forces this record to narrow.
DECISION, OPERATOR, 2026-08-23: narrow, record the limit, close. The undiscriminated
remainder is filed as CS-843. Do NOT re-pitch deleting the element decode - the extent IS
read and the region DOES close; what is unproven is that the division is the right one.
Do NOT re-pitch a synthetic fixture as evidence for a real-library partition.

### 2026-08-23 - CS-405 - CLOSED. The `mInventoryPotential` experiment ran against the real library and recorded a FOURTH outcome the three-outcome menu did not cover
Verification: `docs/adr/0009-inventory-potential-top-level-carries-no-slot-count.md`, indexed
in `docs/adr/README.md`. `tests/save/test_inventory_potential.py` reproduces the evidence,
skip-if-absent and counts only, and passes with the library forced empty.
THE OUTCOME IS "NO AT THE TOP LEVEL, UNREAD BELOW IT" and it is deliberately NOT filed as
INCONCLUSIVE. Inconclusive was ruled by the operator on 2026-08-14 to mean that no world in
the library carries such a building serialized at all, so the probe DID NOT RUN. The
population exists and the probe RAN. The named component is read completely at its top level
and carries no slot count there, under ADR 0005's names or any other. The residue is the
struct element interior CS-829 owns.
DECISION, OPERATOR, 2026-08-23: the fourth state is an acceptable outcome and is named
rather than collapsed. Fence: do NOT re-record this as INCONCLUSIVE and do NOT read it as a
flat NO. A flat NO would refute ADR 0005 option (b), and this does not - integer-valued
container elements exist on those records and are unattributed.
CS-830 IS THE LOAD-BEARING DEPENDENCY, stated as a measured counterfactual rather than as
history: it drove the top-level unmeasured residue to zero, and per non-negotiable 7 an
unread tag is flagged and never assumed absent, so before it nobody could write the sentence
this ADR rests on.
The ADR restates all EIGHT of ADR 0005's re-pitch fences - the item note's summary of "four
routes and the arithmetic one" is five and is NOT the acceptance - and adds three of its own.
`clockspeed/data/version.py` and `clockspeed/solve/power.py` are UNTOUCHED:
`OVERCLOCK_POTENTIAL_SHARD_SLOTS` stays unset and no ceiling is published.
A SEAM WORTH KNOWING, found here and general: no ADR can name a test by identifier without
an edit to the citation guard's hand-maintained tuple. Naming which test reddens under which
fault is also exactly the derived-not-written detection claim ADR 0008 forbids, so removing
the names was compliance rather than a workaround.

### 2026-08-23 - CS-833 - CLOSED. The unresolved bucket is partitioned three ways and the asset gloss is falsified rather than softened
Verification: `clockspeed/save/objects.py` ships `classify_unresolved` and
`UNRESOLVED_SHAPES`; `ReferenceResolution` carries the three counts apart and DERIVES the
bucket total from their sum, so bucket and partition cannot disagree.
`tests/save/test_reference_resolution.py::test_the_unresolved_bucket_counts_its_three_shapes_apart`
kills the collapse SYNTHETICALLY, so it runs on a machine with no game.
A FOURTH SITE OF THE GLOSS WAS FOUND THAT THE DISPATCH DID NOT NAME. The brief named three
and warned that a `SoftObjectProperty` claim would look like a fourth and must be left alone
- that warning was correct and the claim was left. The genuine fourth carried the same
universal at the same scope in the cross-section paragraph of the oracle commentary. THE
POPULATION DEFECT AGAIN, in the brief that warned about it, for the fifth session running.

### 2026-08-23 - CS-834 - CLOSED. The reference population boundary is stated where `resolve_references` is defined, as ONE number
Verification: `clockspeed/save/objects.py` at `resolve_references`, naming three unowned
classes including the actor head's component list. `tests/save/test_reference_resolution.py`
derives the unreached count and goes RED if it is asserted to be zero.
THE INVENTED SPLIT WAS CONFIRMED IMPOSSIBLE RATHER THAN AVOIDED BY INSTRUCTION. A prior
attempt invented a nested-versus-outside split whose two halves summed to a correct total,
which is exactly why it read as measured. This slice checked: the two candidate halves do
NOT sum to the difference, so any apportionment would have been invented. It is ONE number.
An honest nuance is recorded in the boundary rather than glossed: the component list
contributes ZERO to the type-word scan, because those references carry no property tag. It
is an unowned class of REFERENCE, not an unreached TYPE WORD.

### 2026-08-23 - CS-835 - CLOSED on the RECORDED-LIMIT arm, and the measurement that forced that choice is the finding
Verification: `clockspeed/save/objects.py` ships `REFERENCE_COUNT_COMMON_MODE`, a frozenset
of every symbol both passes execute, derived as the closure of the four named primitives
rather than transcribed. `tests/save/test_reference_resolution.py` holds it against the
actual shared-symbol set and goes RED when a symbol joins or leaves.
THE SECOND-COUNT ARM WAS NOT DECLINED FOR COST. It was measured unreachable: PASS TWO REACHES
NOTHING PASS ONE DOES NOT. Its entire objects-surface is common mode, so the second count has
no independent surface at all, and CS-831's two agreeing counts were one reader stating its
opinion twice. Fence: do NOT re-pitch the second-count arm as merely unattempted.

### 2026-08-23 - CS-836 - CLOSED. An empty-path reference is bucketed rather than skipped, proven on a machine with no game
Verification: `clockspeed/save/objects.py` - the lookup in `resolve_references` is
unconditional. Proven with the save library forced absent: the library cases skipped and the
mutant still produced failures, so the guard does not depend on a game being installed.
The mutant was applied IN PLACE with a `finally` restore, its anchor asserted to match
exactly once, the change re-read from disk to confirm it landed, and the restore asserted
byte-identical. No repo copy was made.

### 2026-08-23 - CS-837 - CLOSED on the SECOND acceptance arm: the fence exclusion is recorded against a derived criterion
Verification: `tests/save/test_absolute_claims.py` ships `fence_qualifiers` and the recorded
criterion;
`tests/save/test_absolute_claims.py::test_the_qualifier_derivation_separates_clean_prose_from_dirty_and_from_none`
is the load-bearing control.
THE CRITERION: the fence is a RATCHET ON A STATE ALREADY REACHED. A module declares the
marker when its prose ALREADY satisfies the contract, so the declaration is the LAST step of
a prose repair and never the first. That makes a synonym sweep TRIGGER the obligation rather
than discharge it, which is the escape the fence's own residual warned about. No exemption
list ships - the qualifying set is derived, so there is no artifact to add a module to.
DECISION, OPERATOR, 2026-08-23: take the second arm. Fencing the module was measured to cost
a large prose repair of a module another slice was rewriting the same session, which would
have put the rework on the wrong slice.
GRADED BY AN ADVERSARY ON SIX ATTACKS, ALL NOT REFUTED - which is the strongest statement
available and is NOT "verified". Its residuals are recorded rather than absorbed: the
criterion prose itself is deletable with the suite green, because the citation coupling runs
test-to-prose and never prose-to-test. That is filed as CS-842. The live assertion alone
cannot tell a derived set from a restatement of the list it is compared against, so the
synthetic control is load-bearing and must never be weakened.

### 2026-08-23 - CS-838 - CLOSED. A staged file that `ruff format --check` rejects now BLOCKS a real commit, implemented under the frozen-file grant recorded earlier this day
Verification: `tools/precommit_gate.py` - two insertions only, zero existing lines modified,
re-verified against the grant commit by confirming all lines the gate carried at grant time
are still present in order. `tests/test_precommit_gate.py::test_the_format_check_does_not_rewrite_the_file_it_checks`
and its sibling blocking arm; `tests/test_hook_interpreter_ladder.py` carries the derived
`TRUNCATIONS`.
THE ROUTE WAS THE POINT: proposer, adjudicator and implementer were three different agents,
the grant preceded the edit in COMMIT ORDER and not merely in prose, and no agent graded its
own work.
CONDITION ELEVEN EARNED ITS COST. It required `TRUNCATIONS` to be RE-DERIVED rather than
re-checked. The implementation's insertion made the previously hardcoded prefix stop
compiling, so a re-check condition would have refused for the wrong reason. Measured: across
a range of insertion sizes the hardcoded form fails a large minority, the derived form fails
none - and the reason is structural rather than statistical, because in a file that parses, a
column-zero compound statement can only begin where every enclosing bracket, string and block
is complete, so the derived prefix is a syntactically complete program by construction.
CONDITION FIVE EARNED ITS COST TOO, and this is the sharpest lesson: the verdict comes from
ruff's EXIT CODE and never from its output prefix. The ruff version CI resolves has ALREADY
reworded the line an earlier proposal wanted to parse. Had the prefix decided the verdict,
CI's own ruff would have silently passed everything.
CS-838 DOES NOT CLOSE CS-484 AND IS NOT RECORDED AS MAKING THE GATE AGREE WITH CI. The ruff
pin still carries no upper bound. A block on a newer-ruff machine names no file.
A CORRECTION TO THIS ITEM'S OWN GRANT is recorded separately above: condition SEVEN's
RATIONALE carried a sentence measured false, the arm that pinned it could not fail, and the
sentence had shipped to three sites.
RESIDUALS FILED RATHER THAN ABSORBED: CS-841, the silent and self-arming format gap on the
PostToolUse path, which condition FOURTEEN required be filed as its own item.

### 2026-08-23 - CS-838 - CORRECTION to the frozen-file grant recorded earlier this day: condition SEVEN's RATIONALE carried a false sentence, and the sentence had shipped to three sites
Verification: this record CORRECTS the grant entry below, headed "CS-838 - FROZEN-FILE GRANT
ISSUED WITH SEVENTEEN CONDITIONS". That entry is not edited - this file is append-only and a
record that turns out to be wrong gets a new, later record that says so. The GRANT ITSELF
STANDS and every one of its seventeen conditions stands. What was wrong is one sentence of
REASONING inside condition SEVEN, not the condition.

THE FALSE SENTENCE, quoted from the grant: "stage_for_lint returns REAL working-tree paths
for units whose bytes match disk". MEASURED FALSE for --staged mode by the adversary that
graded the implementation: `mode_staged` builds every unit WITHOUT a disk_path, so
`stage_for_lint` copies to a temporary directory and ruff never sees a working-tree path at
all under --staged. The sentence is true only of --files, where `mode_files` sets disk_path.

WHY IT MATTERED RATHER THAN BEING A WORDING SLIP. The arm that pinned condition SEVEN -
`test_the_format_check_does_not_rewrite_the_file_it_checks` - drove --staged alone, and
therefore COULD NOT FAIL. Proven by mutation: with `--check` deleted from the argv, that arm
PASSED while a sibling arm correctly failed. A test that cannot fail is the shape this
project has repeatedly paid to close, and it reached here through a rationale nobody
re-measured.

THE SENTENCE HAD SHIPPED TO THREE SITES, which is the population defect this project has now
recorded in five consecutive sessions: the grant's condition SEVEN rationale, the
`run_ruff_format` docstring in `tools/precommit_gate.py`, and the test's own docstring. TWO
OF THE THREE WERE FIXED IN CODE and the third is this record. Fixing the instance and leaving
the population is the specific error being avoided here.

THE REPAIR, made by the merger on main and not by the implementer. The arm now ALSO drives
--files, which is the only mode carrying the exposure and the mode CI runs over every tracked
file. It asserts the bytes first so a rewrite is reported AS a rewrite, then asserts the check
actually fired so the byte assertion cannot pass for the wrong reason. PROVEN BY MUTATION with
the mutation asserted landed and the restore asserted byte-identical: dropping `--check` now
turns the arm RED on the byte assertion, where the previous version passed.

THE GRANT'S BOUNDED REGION WAS NOT WIDENED BY THIS REPAIR. The docstring corrected in
`tools/precommit_gate.py` is inside the text CS-838 itself inserted. Condition ONE was
re-verified against the grant commit rather than asserted: every one of the 2395 lines the
gate carried at grant time is still present, in order, in the file today.

TWO FURTHER FINDINGS FROM THE SAME GRADING, RECORDED HERE BECAUSE THEY BEAR ON THE GRANT'S
OWN COMMON-MODE DISCLOSURE AND ARE NOT ITEMS OF THEIR OWN.
FIRST, THE VERSION RISK IS NOT HYPOTHETICAL AND IS ALREADY LIVE. The grant disclosed that
`ruff` is pinned with no upper bound and that CI resolves a different version. MEASURED this
session on a real commit: the version CI resolves has ALREADY REWORDED the line the earlier
proposal wanted to parse for its verdict. Condition FIVE - the verdict is the EXIT CODE and
the prefix only NAMES files - is what kept the gate blocking. Had the prefix decided the
verdict, CI's own ruff would have silently passed everything. The cost that remains is that a
block on such a machine names no file.
SECOND, CONDITION EIGHT'S PREMISE IS STALE. `--diff` was forbidden because it prints source
lines. The newer ruff prints source lines from plain `--check` as well. The privacy property
survives, but NOT because of the flag: it survives because `run_ruff_format` never re-emits
ruff's stdout. Anyone who later makes the gate print ruff's output to recover the missing
filename would leak source lines while believing the flag protects them. The docstring now
records the property that actually holds the line.

### 2026-08-23 - CS-838 - FROZEN-FILE GRANT ISSUED WITH SEVENTEEN CONDITIONS by an adjudicator for `tools/precommit_gate.py`
Verification: this entry is the grant record CLAUDE.md section 6 requires BEFORE the edit, not a
completion record. NOTHING IS CLOSED BY IT. CS-838 STAYS OPEN in `ROADMAP.md` until its own closure
record. The adjudicator that issued it WROTE NO PART of the proposal, the implementation or the tests,
and will implement none of it. It does NOT widen the CS-703, CS-819, CS-823 or CS-702/CS-813 grants
recorded below; every one of those explicitly EXCLUDED this file.
THE DEFECT, REPRODUCED INDEPENDENTLY rather than inherited from the filing. In a throwaway clone at
`b91aa45` with `core.hooksPath=.githooks`, a staged `.py` that `ruff format --check` rejects
COMMITTED: exit 0, HEAD MOVED, and the gate printed `precommit_gate: PASS - 1 checked, 0 skipped, 0
blocking`. The filing recorded 2 skipped and this run recorded 0; that is what else was staged, not a
difference of substance, and the load-bearing facts - exit 0, HEAD moved, PASS banner - reproduce
exactly. The FULL suite is green with the violation present: 2509 passed, 3 skipped, exit 0, measured
this session on the pristine tree.
THE DEFECT IS A LOCAL-GATE GAP, NOT AN UNPROTECTED PROJECT, and this entry says so rather than
overstating it. `.github/workflows/tier1.yml:130` already runs `python -m ruff format --check .`, and
line 118 runs this gate in `--files` mode over all tracked files. CI would have caught the commit that
prompted this item. What is broken is the tier-0 gate's agreement with CI, which is worth fixing
because a gate that passes what CI rejects trains the operator to ignore it.
SCOPE, ONE FILE, TWO INSERTION POINTS. In `tools/precommit_gate.py` ONLY, for CS-838 ALONE:
(A) a module constant and one new function inserted in the blank gap between the end of
`record_ruff_findings` (line 1850) and `def run_ruff` (line 1853); and (B) exactly one call line
inserted immediately after `paths, mapping = stage_for_lint(...)` (line 1873), which is INSIDE the
`tempfile.TemporaryDirectory` opened at 1872 and BELOW the ruff-absent early return at 1870.
INSERTIONS ONLY: NO existing line 1 to 1850 and NO existing line 1853 to the end of file may be
modified or deleted. THE GRANT IS BOUND BY REGION AND PROPERTY, NOT BY LINE COUNT - a count is the
same fragile coupling condition ELEVEN exists to remove.
WHY THAT PLACEMENT IS THE NARROWEST AVAILABLE, verified by reading rather than assumed. Below 1870 the
new code INHERITS both early returns - no `.py` targets, and ruff absent - structurally rather than by
promise, and it reuses the `paths` and `mapping` line 1873 already built. A top-level pass called from
`main` would have to re-stage temp copies and touch a second region.
NO OTHER FROZEN PATH IS COVERED, and each would need its own grant: `.githooks/pre-commit`,
`.githooks/commit-msg`, `.githooks/pre-push`, `scripts/install_hooks.py`, `.claude/settings.json` and
`LICENSE`. `.githooks/pre-commit` was CHECKED BY READING rather than assumed: `tools/precommit_gate.py:2311`
emits the PASS banner only when `report.diagnostics` is empty, so a blocking diagnostic returns
non-zero WITHOUT the banner and the hook's existing `STATUS -ne 0` branch handles it untouched. That
holds ONLY under conditions THREE and FOUR. `tests/` and `tools/edit_lint_check.py` are NOT frozen and
are NOT part of this grant.
SEVENTEEN CONDITIONS BIND THIS GRANT. They are written here because this is their only tracked home.
ONE, insertions only: zero existing lines of the gate modified or deleted.
TWO, the two insertion points above and no others.
THREE, the PASS banner and the code that renders it are BYTE-IDENTICAL after the edit.
`.githooks/pre-commit` matches it with an anchored `case` pattern on `precommit_gate: PASS - `.
FOUR, the new `subprocess` call passes `capture_output=True`, capturing STDOUT as well as stderr. Both
the hook's no-hang property and its banner-as-LAST-LINE assertion depend on the child not inheriting
the gate's stdout. MEASURED: `ruff format --check` writes `Would reformat: <path>` AND its summary to
STDOUT, and stderr was EMPTY - so the exclusion as proposed named the wrong channel.
FIVE, the BLOCKING SIGNAL IS THE EXIT CODE, not the prefix string. `RUFF_FORMAT_PREFIX` is used ONLY
to name files in the finding. A prefix contract with an unpinned tool that reworded it would silently
pass everything, which is the CS-819 and CS-823 shape this project has twice paid to close.
SIX, exit-code discipline, measured: 0 clean, 1 would reformat, 2 error. Exit 2 - an unparseable file -
is a NOTE, never a block, and is never read as clean.
SEVEN, `--check` ONLY. Bare `ruff format` is FORBIDDEN: `stage_for_lint` returns REAL working-tree
paths for units whose bytes match disk, so it would rewrite the operator's own files, and in CI's
`--files` step it would rewrite the checkout.
EIGHT, `--diff` is FORBIDDEN. It prints SOURCE LINES verbatim, measured, and a staged file may carry a
world name or an account id.
NINE, the file identity goes in `Diagnostic.path`, resolved through `mapping` with `normalized_key`,
and is NEVER interpolated into `reason`. Only `path` is redacted, by `display_diagnostic` via
`display_label`; `reason` is not. Raw ruff stdout is never re-emitted.
TEN, `RUFF_TIMEOUT` is read at CALL time, not bound as a default argument.
`tools/edit_lint_check.py` monkeypatches `gate.RUFF_TIMEOUT` around its call, and a default would bind
at import and ignore it.
ELEVEN, `TRUNCATIONS` in `tests/test_hook_interpreter_ladder.py:1678` is RE-DERIVED from the located
`GATE_MAIN_GUARD` rather than left as the hardcoded 2368. MEASURED: across insertion sizes 0 to 60,
24 of 61 break the 2368-prefix compile. The proposal's 47 lines happening to survive where 36 did not
is LUCK. Deriving as `main guard line minus one` is INVARIANT under any insertion above it. The module
already carries the idiom in `gate_success_format`. `tests/` is not frozen, so this costs no grant.
TWELVE, the fixture repair to `tests/test_precommit_gate.py::test_ruff_style_note_drops_the_out_of_repo_directory`
is the MINIMAL blank line, and after it the test must still ASSERT rather than SKIP. That module's
line 1484 skips itself when no `ruff (style` finding appears, so a repair that killed the F401 unused
import would silently disable the test instead of failing it. Show it did not skip.
THIRTEEN, the R1 mitigation - skip when no ruff config resolves - is PINNED BY A TEST and RECORDED AS
A NAMED RESIDUAL. MEASURED: 90 tracked `.py`, 90 of 90 clean with the project config, 75 of 90 would
be reformatted without it. `tools/edit_lint_check.py` builds its `Unit` without `disk_path`, so every
unit is staged to temp where ruff discovers no config, and it passes `root=None`.
FOURTEEN, the residual is recorded as SILENT and SELF-ARMING rather than as a note the operator sees.
`emit` prints notes ONLY under `--verbose`, and the PostToolUse hook entry invokes
`tools/edit_lint_check.py --files` WITHOUT it. A later one-line change passing a `root` would ARM a
blocking check with no grant, because that file is not frozen. That repair is FILED as its own item,
not absorbed here.
FIFTEEN, the acceptance is proven END TO END IN BOTH DIRECTIONS with a real `git commit`: a staged
format violation gives exit 1 with HEAD UNCHANGED, and a clean staged file still COMMITS. Demonstrated
RED against the current gate first. The before-transcript is recorded so the after-transcript means
something.
SIXTEEN, the suite floor is RE-MEASURED after the edit and reported as observed on that run. The
pristine floor measured this session is 2509 passed, 3 skipped, exit 0. No count is carried forward.
SEVENTEEN, this grant is recorded here BEFORE the edit is made.
COMMON-MODE RISK: THE RUFF VERSION, WHICH NOTHING IN THE PROPOSAL TESTS. `pyproject.toml:73` pins
`ruff>=0.13` with NO upper bound. This machine has 0.15.12; CS-484 records CI resolved 0.16.3, taken
from a tier1 log. `ruff format` output is version-dependent, so 90 of 90, 75 of 90, the fixture's
dirtiness and the literal `Would reformat: ` are all ONE ruff's opinion. THE NEW FAILURE MODE THIS
CHANGE INTRODUCES: the local ruff refuses a tree CI's ruff accepts, blocking the operator at tier 0
with no override short of `--no-verify`. CS-838 DOES NOT CLOSE CS-484 AND MUST NOT BE RECORDED AS
MAKING THE GATE AGREE WITH CI. Nothing was measured on the Ubuntu runner; CI's own `--files` gate step
will exercise this code on the first push, so the tier1 log is READ after that push and the resolved
ruff version recorded.

### 2026-08-23 - CS-831 - CLOSED. A record's cross-references RESOLVE to the records they name; the acceptance was AMENDED by the operator the same day and the amended wording is preserved here
`clockspeed/save/objects.py` ships `index_records`, `resolve_references`, `ObjectReference`,
`RecordIndex`, `ReferenceResolution` and `REFERENCE_TYPE_WORD`. A caller can now follow an
`ObjectProperty` from the record that bears it to the record it names. This is the FIRST of the
three layers between the advisor and a building's inventory; CS-830 and CS-829 are the other two,
and the operator's CS-400 clause-1 ruling is stated by substance rather than by item id, so it is
unaffected by which layer lands when.

**THE ACCEPTANCE WAS AMENDED BY THE OPERATOR ON 2026-08-23, MID-REPAIR, AND IS RECORDED HERE
VERBATIM BECAUSE CLOSING DELETES THE `ROADMAP.md` LINE THAT HELD IT.** Amending an acceptance
clause is the operator's act alone. The amended clause, in full:

> EVERY `ObjectProperty` reference on a real record either resolves to a record in the same save
> or is flagged unresolved, asserted as an EQUALITY over the reference population WHOSE TOTAL IS
> OBTAINED FROM A SOURCE THE BUCKET-FILLING LOOP CANNOT MOVE, AND the resolved count is non-zero
> and recorded, proven by a skip-if-absent real-library test reporting COUNTS ONLY.

The words added were the total's provenance. They were added because the ORIGINAL clause permitted
a vacuous reading, which the builder itself flagged and an adversary then demonstrated: the first
version's equality reduced to an identity, and two landed mutants left every test green - one
dropping component records from the index, which destroys most of the join, and one calling every
resolution ambiguous. An adjudicator ruled the amendment bought REAL detection rather than only
tidier wording: the partition against the walk's own total is an identity, but the partition
against a tag total this module does not count is not, and the same defect that used to read as
zero equals zero now reddens.

**WHAT THIS ENTRY DOES NOT CLAIM.** The two passes that agree are not independent READERS - they
share the payload primitives, they abandon a payload on the same conditions, and every synthetic
case derives from one fixture builder. The second join is evidence about the JOIN and is NOT
evidence about the DECODER. A count obtained without the shipped grammar was MEASURED impossible:
the only grammar-free candidate over-counts, because the type word also occurs inside container and
struct values the top-level walk steps over, and restricting it to the walk's own offsets requires
the grammar under test. That limit is filed as CS-835 rather than left as an adjective, and the
population boundary it implies is CS-834.

Route: one builder, then two adversaries on distinct lenses which BOTH returned REFUTED, then a
repair; then an adjudicator which returned CLOSE on all six clauses and an adversary which returned
REFUTED on four blockers the adjudicator had not looked for; then a second repair. The adjudicator
graded the CLAUSES and the adversary graded the RECORD around them, and that split is the reason
both were run. **A third adversarial round was NOT run against the second repair.** The merger
graded its new prose directly instead, and re-ran the mutants itself. That is a stated limit of
this close, not a claim of exhaustion.

Residuals filed rather than absorbed: CS-833, CS-834, CS-835, CS-836, CS-837 and CS-838. The first
repair corrected a false claim in the test and left the identical claim standing at four sites in
`clockspeed/save/objects.py`, a file on its own write-list; the second repair found the fourth site
the merger's own brief had missed. Both facts are recorded because the failure mode - fixing the
instance in front of you instead of deriving the population - is this project's most expensive
recurring defect and it recurred twice inside this one item.

Verification: `python -m pytest tests/save/test_reference_resolution.py -q` derives every figure
from the live library on each run and hardcodes none, so nothing here rots when the operator plays;
`python -m pytest "tests/save/test_reference_resolution.py::test_an_unexpected_read_failure_does_not_unwind_through_the_reference_sweep"` must pass ALONE, which is what a
prior version did not; and the close rests on mutants, so re-apply them - drop non-actor records in
`index_records`, change `len(found) > 1` to `>= 1`, and wrap `references` in `reversed` - each must
turn the module RED, and each is killed by a synthetic case that needs no game installed.

### 2026-08-23 - CS-486 - CLOSED. The upstream wiki watch list gets an owning file, a topology row and a budget; clause 1 closed on an operator ruling, not on new research
`docs/upstream_watch.md` now owns the upstream watch list - the page groups, the ordering that makes them usable, and the standing refusal of any automated fetch. It is named in the `CLAUDE.md` section 4 ownership table and in the `CONVENTIONS.md` section 2 table that `tools/drift_guard.py` guard d parses at runtime, and `tools/doc_budget.py` was extended to measure it, which is what clause 3 asked for.

CLAUSE 1 DID NOT CLOSE ON EVIDENCE AND THIS ENTRY SAYS SO PLAINLY. It asked for the PER-PAGE watch list. Measured 2026-08-23 while building the file: the per-page change signals were never carried into any tracked file - not into the relocated source block, and not into this ledger under CS-485, which records the gate result and the research method and leaves the list itself homeless. What the repository holds is the page GROUPS and the ordering. **The operator ruled that those ARE the watch list clause 1 meant**, and the item closed on that ruling. A future reader who wants per-page signals must re-run the CS-485 pass; `docs/upstream_watch.md` records that and refuses to invent them, which is the honest state rather than a gap hidden behind a close.

The item was filed to find a home and had sat without one because inventing a tracked doc with no owner is the drift `CLAUDE.md` section 4 exists to prevent. The ruling that created the file came in the same session that executed the ROADMAP budget ruling, which is why the two arrived together.

Verification: `python tools/drift_guard.py` - guard d parses the `CONVENTIONS.md` section 2 table and FAILS on a named file that does not exist, so a PASS is evidence the owner file is really there; `python tools/doc_budget.py` lists `docs/upstream_watch.md` with its budget and its measured share; and `grep -n upstream_watch CLAUDE.md CONVENTIONS.md` shows the two topology rows.

### 2026-08-23 - CS-413 - CLOSED. Three clauses graded against the real library; FIVE residuals filed after a review found the first two were not all of them
CS-413 CLOSES on its three acceptance clauses, each graded against the real save library rather
than against the synthetic corpus, and with both of the objections that kept it open addressed.
It was routed to an adjudicator and three adversaries; the adjudicator returned DO-NOT-CLOSE and
all three adversaries returned REFUTED against an earlier draft. What follows is the repaired
version, and every repair is named rather than quietly applied.

**HOW THE THREE CLAUSES GRADE.** No count is restated in this section; each pointer produces its
own.

CLAUSE 1 - `ObjectRecord.body_offset` and `body_length` locate a real payload instead of reading
0 on every path. MET, against the real library, with the ALIGNMENT measured rather than assumed:
the k-th pairing satisfies the cross-check universally and both neighbours satisfy it never.

CLAUSE 2 - the object data section walks to its exact final byte on every real save of a
measured pair. MET. **DISCLOSED RATHER THAN GLOSSED: THE TEST THAT GRADES THIS IS CS-407's
ACCEPTANCE**, its body unchanged since the CS-407 commit, so this clause was green before CS-413
was filed. An adversary found that and it is worth stating - CS-413's own contribution is
clause 1's attribution and clause 3's decode, not this. **AND NOTE WHAT THIS CLAUSE IS NOT.** The
BODY walk is boundary-exact: every real save walks its framing to the final byte with nothing
left over, and a section that does not tile raises rather than hiding behind the body total. The
PROPERTY walk inside a payload is terminator-exact. Those are different walks, and the region
between them is CS-828.

CLAUSE 3 - `read_properties` returns at least one decoded property VALUE off a real building.
MET, and **not on the floor the clause literally asks for**. The recorded objection was that "at
least one" is trivially satisfiable, since a `BoolProperty`'s value rides in the tag at size 0.
The shipped test asserts an EQUALITY instead - every building carrying a measured type decodes -
keeping a floor only to stop the equality passing vacuously at 0 == 0. That is stronger than the
acceptance.

**OBJECTION 2 IS NOT DISCHARGED; IT IS CARRIED FORWARD, AND AN EARLIER DRAFT OF THIS ENTRY SAID
OTHERWISE.** The objection was that the evidence is uneven and the unevenness falls exactly on
what pillar 3 needs. The three items said to carry it - CS-420, CS-421, CS-422 - are all closed.
But CS-421 closed by filing CS-826, whose subject is precisely the population the objection
named. So what is established is that the three items closed and the population is now CS-826,
not that the unevenness is resolved. Writing "discharged" was the letter-of-the-acceptance move
this same entry refuses one level up for CS-400's clause 1.

**FIVE RESIDUALS ARE FILED. AN EARLIER DRAFT FILED TWO AND ASSERTED THE SEARCH HAD BEEN
EXHAUSTIVE.** It had not been. The draft filed the largest region and the one `docs/GATED.md`
names, and left every other entry of `UNMEASURED_PAYLOAD_REGIONS` unfiled - the count is that
table's to state, not this entry's. An adjudicator and an adversary found it independently.

- **CS-828** - the trailing run, which `docs/GATED.md` assigned to CS-413 by name and which the
  close would otherwise have orphaned. **SCOPED TO THREE PAIRS**, because the (14,60) pair
  reaches a terminator on no payload and its half is GATED as CS-G05. A draft scoped it to every
  measured pair, which is exactly what that file forbids in the sentence the draft quoted.
- **CS-829** - `StructProperty`'s interior, the largest opaque region by count.
- **CS-830** - the container types' ELEMENT framing. `ArrayProperty` is the second-largest region
  and was covered only by CS-489, which grades the table's PROSE and reads no bytes.
- **CS-831** - resolving an `ObjectProperty` cross-reference to the record it names.
- **CS-832** - `TextProperty`, declined on sample size, and `Int64Property`, which is decoded
  nowhere and is NOT in `DECLINED_VALUE_READINGS` - an earlier wording called both "declined"
  and an adjudicator corrected it. `TextProperty` had ZERO mentions across every
  open-work file.

**THE FACTUAL ERROR THAT MATTERED MOST, AND IT REACHED THE OPERATOR.** An earlier draft stated
that inventory lives inside `StructProperty`'s interior, and an operator ruling on CS-400's
clause 1 was obtained on that basis. **MEASURED over the real library and contradicting it: no
building record carries an `InventoryStack`.** A building holds an `ObjectProperty` REFERENCE to
a separate inventory component; the stacks live on that component inside a container property. So
inventory sits behind three layers - CS-831, then CS-830, then CS-829 - and the operator had been
given a one-blocker map. The ruling was re-put and is now stated by SUBSTANCE: clause 1 waits
until a building's inventory is actually readable, which does not depend on this author's
decomposition being right.

**PILLAR 3's THREE NEEDS, ALL THREE GRADED, because an earlier draft graded two and dropped the
third silently.** Clock speed is `FloatProperty` and decodes. Connection state is
`ObjectProperty` and decodes AS A VALUE, though following it to the record it names is CS-831.
Inventory is not readable.

**WHAT THIS CLOSE DOES NOT ASSERT.** That a world can be INSPECTED. It cannot: inventory is
unreadable, and CS-400's clause 1 stays open for that reason.

Verification:
- `clockspeed/save/objects.py` plus `tests/save/test_objects.py::test_every_real_save_attributes_a_payload_extent_to_every_record` - clause 1.
- `tests/save/test_objects.py::test_the_payload_to_record_alignment_is_the_one_the_bytes_choose` - clause 1's alignment, with both neighbouring alignments rejected.
- `tests/save/test_objects.py::test_every_real_save_of_a_measured_pair_walks_to_the_end_of_its_body` - clause 2. This is CS-407's acceptance test, disclosed above.
- `tests/save/test_properties.py::test_a_real_building_yields_at_least_one_decoded_property_value` - clause 3, as an equality rather than the clause's floor.
- `tests/save/test_phase4_gate.py` - CS-400's clauses 2, 3 and 4, unaffected by this close.
- The first four pointers open a save and SKIP where there is no library, so CI cannot grade them; that is why they are the evidence that matters and why a green CI run is not this close's evidence.
- The residuals: `ROADMAP.md` under CS-828, CS-829, CS-830, CS-831 and CS-832. The open acceptance question: `ROADMAP.md` under CS-400.

### 2026-08-23 - CS-421 - CLOSED under an OPERATOR RULING that amended clause 3. Both residuals are filed, as CS-825 and CS-826
CS-421 CLOSES. This entry supersedes the DO-NOT-CLOSE adjudication recorded below on the same
date. It was itself routed to an adjudicator and three adversaries before landing. The
adjudicator returned DO-NOT-CLOSE and two adversaries returned REFUTED against an earlier
draft; what follows is the repaired version, and the repairs are named rather than silently
applied.

**THE TWO RULINGS, recorded because amending an acceptance clause is fence 1's forbidden move
for every agent in this project.** Asked directly and answered on 2026-08-23: (1) amend
clause 3, and file the `UInt32Property` residual as its own item; then, after an adversary
measured that `UInt32Property` is not the only unsettled population, (2) file BOTH residuals
and repair the false sentences. No adjudicator granted either, and none could.

**THE FIRST QUESTION CARRIED AN INCOMPLETE PREMISE, AND THE RECORD SAYS SO RATHER THAN HIDING
IT.** It asked the operator to file "the `UInt32Property` residual", a phrasing inherited from
the adjudication below without checking what else sat at a non-settled status. `IntProperty`
and `FloatProperty` carry `anchored_not_unique`, which is also not a settlement, and no open
item covered them. The operator ruled correctly on the picture they were given; the picture was
short. That is why there are two residual items and not one.

**CLAUSE 3 AS FILED, verbatim:** "the endianness question is settled against something that is
not this project's own writer".

**CLAUSE 3 AS AMENDED, verbatim:** "the endianness question is settled JOINTLY over the scored
populations against the real save library, with the per-type residual recorded in shipped
data".

**WHAT THE ADJUDICATION BELOW ACTUALLY NAMED, AND AN EARLIER DRAFT OF THIS ENTRY GOT IT
WRONG.** It named TWO routes, not one: an operator ruling amending clause 3, OR a second
library-backed control catching the `">i"` flip through a predicate that is not
`_int_oracle_holds`. **ROUTE TWO WAS BUILT** - commits `5c4b270` and `c2ecc5b` - and then
measured by an adversary to be a second IMPLEMENTATION rather than a second SIGNAL, which is
recorded in the two entries directly below. So the honest statement is that route two was
attempted and did not deliver independence, and route one is what closed this. An earlier
draft said only one route was ever named, which erased a real attempt.

**THE EVIDENCE DID CHANGE BETWEEN THE ADJUDICATION AND THIS ENTRY, and an earlier draft of
this entry denied it.** Two commits and a substantial body of oracle and control code landed
in `tests/save/test_value_anchoring.py` between them, with their own entries below. What did
NOT change is the INDEPENDENCE of the signal, which is the property the adjudication turned
on. Those are different sentences and the draft collapsed them.

**WHY THE FILED CLAUSE WAS NOT GRADEABLE ON THIS CORPUS - and note the direction of the
reasoning, because an earlier draft had it backwards.** No word in `BYTE_ORDER_STATUSES` means
settled. That is DOWNSTREAM of the evidence, not a definitional trick: the vocabulary lacks
such a word BECAUSE nothing in this library settles the question, and the module says so where
each word is derived. An earlier draft wrote this as though the vocabulary made the clause
ungradeable by anyone, which both inverts the causation and contradicts the adjudication's own
second route.

**HOW THE THREE CLAUSES GRADE, each against a shipped artifact rather than against prose. No
count is restated here - this file forbids it, and each pointer below produces its own.**

CLAUSE 1 - every member of `MEASURED_VALUE_TYPES` states which oracle backs it. MET.
`EVIDENCE_FOR_VALUE_TYPE` in `clockspeed/save/objects.py` is that statement, and the test
below derives both directions in the same run rather than reading an allowlist. **NOTE THE
LIMIT THE ADJUDICATION ATTACHED AND AN EARLIER DRAFT DROPPED:** it grades completeness and
vocabulary, not the truth of the class named, and only `EVIDENCE_MAGNITUDE` is tied to a live
control. That gap is CS-459 and CS-459 is OPEN.

CLAUSE 2 - a type backed only by a declared width is marked as such in shipped DATA rather
than prose. MET. `WIDTH_ONLY_VALUE_TYPES` in `clockspeed/save/objects.py` is that data, and it
is DERIVED from the evidence table rather than hand-listed, so it cannot be written out of
step with it. **THE SAME LIMIT AS CLAUSE 1 APPLIES AND IS RECORDED RATHER THAN GLOSSED:** the
derivation cannot be written out of step with the table, and grades nothing about whether the
table is TRUE. An adversary moved a genuinely width-only type off its evidence word and the
whole save suite stayed green. **CS-459 ALREADY OWNS THAT GAP** - it says in terms that this
set can become a lie in shipped data with nothing red - so no duplicate item was filed. The
separate gap on the evidence vocabulary's STRING values is filed as CS-827.

CLAUSE 3 AS AMENDED - settled jointly over the scored populations AGAINST THE REAL SAVE
LIBRARY, with the per-type residual recorded in shipped data. MET, in two halves that need
two different artifacts. The JOINT half is `BYTE_ORDER_SURVIVING_CANDIDATES`, a singleton,
derived against the live library. The RESIDUAL half is `VALUE_BYTE_ORDER_STATUS`, which
records the residual honestly rather than favourably. An earlier draft graded this clause
citing only the residual half and dropped the words "against the real save library" from the
criterion at the moment of grading, which is where an adversary caught it.

**WHAT THIS CLOSE DOES NOT ASSERT.** It does not assert that the byte order of any four-byte
type is KNOWN. The module refuses in writing to carry the joint result across to any single
type - the premise that this format uses one byte order for every int32 field is recorded
there as an assumption and not a measurement, and that boundary is not crossed here either.
What is asserted is that the question is scored against the real library, that the score is
recorded per type in shipped data, and that BOTH unsettled populations IN THAT TABLE are now
named items. **THAT CLAIM IS BOUNDED TO THE FIXED-WIDTH VALUE READER AND THE BOUND IS STATED
HERE BECAUSE AN ADVERSARY FOUND IT UNSTATED.** Six measured types carry no byte-order status
at all and the status table's own control forbids giving them one; they rest on
`EVIDENCE_REDUNDANCY` instead, which is a real argument because a mis-read length
desynchronises the walk - but it is a different argument, and nothing here grades it.

**THE TWO RESIDUALS, AND WHY BOTH HAD TO BE FILED.** `VALUE_BYTE_ORDER_STATUS` carries two
words that are not settlements, and an item was filed for each:

- **CS-826** - `IntProperty` and `FloatProperty` at `anchored_not_unique`. This is the large
  population and it is the one pillar 3 needs, because those two types are inventory counts
  and clock speeds. It was UNFILED until an adversary measured it, and the draft this entry
  replaces asserted that "the unsettled part" was a single named item while this one had no
  item at all.
- **CS-825** - `UInt32Property` at `oracle_cannot_separate_readings`. The small population.

**THE FENCE THAT TRAVELS WITH THEM, and it is a property of the data rather than of any
design.** Every changed matched value in the local library is small at one end, so every
CORRECT byte-order oracle must agree with the magnitude prior on it. What would separate two
correct oracles is a save carrying LARGE integers that CHANGE. The counts behind that sentence
are measured in the entries below and are not restated here. **DO NOT SPEND A SESSION
DESIGNING A CLEVERER PREDICATE ON THE int32 POPULATION** - that route is measured closed.
**THAT FENCE IS MEASURED ON int32 AND IS CARRIED BY CS-826 ONLY.** It is NOT transferred to
CS-825: `UInt32Property` sits in no scored population, so the finding has never been measured
on it, and transferring it would be the population carry this module refuses elsewhere. An
adversary raised that and it was right.

Verification:
- `clockspeed/save/objects.py` plus `tests/save/test_properties.py::test_every_measured_value_type_names_the_oracle_that_backs_it` - clause 1.
- `clockspeed/save/objects.py` plus `tests/save/test_properties.py::test_the_magnitude_oracle_covers_exactly_the_types_marked_with_it` - clause 2.
- `clockspeed/save/objects.py` plus `tests/save/test_value_anchoring.py::test_the_shipped_candidate_set_is_what_the_value_oracles_cannot_separate` - clause 3's JOINT half, derived against the real save library. This is the pointer the earlier draft was missing.
- `clockspeed/save/objects.py` plus `tests/save/test_value_anchoring.py::test_the_cannot_separate_status_is_derived_from_the_oracle` - that the residual word is derived from the oracle rather than transcribed.
- `clockspeed/save/objects.py` plus `tests/save/test_byte_order_status.py::test_every_fixed_width_type_the_module_decodes_carries_a_recorded_status` - clause 3's RESIDUAL half, repo-shape only.
- `tests/save/test_byte_order_status.py::test_no_type_is_marked_anchored_that_no_oracle_scores` and `tests/save/test_byte_order_status.py::test_no_type_an_oracle_scores_is_left_recorded_as_unscored` - the over-claim and under-claim directions on the status table.
- `tests/save/test_byte_order_status.py::test_the_status_words_are_pinned_and_distinct` - the status words are pinned BY LITERAL, not by symbol. Without it, renaming a word to one that reads as a settlement passes every other pointer here. An adversary measured that.
- **TWO of the pointers above open a save** - the two in `test_value_anchoring.py`. Forced absent, they SKIP and the other five pass in well under a second. So five of the seven are repo-shape assertions and grade nothing about the library. A draft of this block said only one opened a save; that was measured false.
- The residuals: `ROADMAP.md` under CS-825 and CS-826.

### 2026-08-23 - CS-421 - ADVERSARY REFUTED the second oracle's headline claim. CORRECTION to the entry below, and the repair
CS-421 STAYS OPEN. This corrects the entry immediately below rather than editing it, which is
what this file requires. The second oracle was routed to an adversary before it was pushed;
the adversary built none of it, ran its mutants in an OUT-OF-TREE copy so the working tree was
never touched, and returned REFUTED. Every finding below was RE-MEASURED here before it was
written, and two of them were re-derived independently rather than checked.

**THE HEADLINE CLAIM WAS FALSE AND IT WAS MINE, WRITTEN THE SAME DAY.** The entry below calls
the continuity oracle a SECOND ORACLE. It is a second IMPLEMENTATION, not a second SIGNAL.
**RE-DERIVED HERE with an independently written predicate: a rule that inspects NO MOVEMENT AT
ALL - the small-magnitude prior applied to the pair's two endpoints, which is
`_int_oracle_holds`'s own two counters restricted to the pair - reproduces the continuity
verdict on 145 OF 145 pairs with ZERO disagreements.** 135 of the 145 changed pairs differ only
in their lowest stored byte. The claim in the entry below that this narrows the common-mode
risk "from three shared inputs to two" is NOT SUPPORTED: the SIGNAL is a third shared input and
it was not narrowed.

**WHY NO PREDICATE FIXES THAT HERE, WHICH IS THE FINDING WORTH KEEPING.** ZERO of the 145
changed matched values carry a non-zero as-read high byte at both ends. Every changed value in
this corpus is small at one end, so EVERY correct byte-order oracle must agree with the
magnitude prior on it. **Evidential independence is not a predicate-design problem on this
library - it needs data this world does not contain.** A later session must not read the
existence of a second oracle as having supplied it.

**TWO FURTHER SENTENCES OF MINE WERE MEASURED FALSE AND ARE CORRECTED IN THE TREE.** That every
predicate available inside ONE save is the magnitude prior, so time was the only
symmetry-breaker: FALSE BY CONSTRUCTION - the adversary built a SPACING statistic over a single
save, how many distinct values `v` have `v + 1` also present, scoring 98 as stored against 0
reversed, asking nothing about magnitude. And that the whole pattern histogram is invariant
under byte reversal: FALSE AS WRITTEN, 202 patterns change count under reversal in one measured
save. What is invariant is the MULTISET OF COUNTS. Read literally the stronger sentence denied
that `_int_oracle_holds` can work at all. A third sentence, that the library holds repeated
saves of ONE world, is also false - THREE distinct world tokens are present and 8 of the 145
pairs match across two different worlds - though the verdict survives restriction to
same-world adjacencies, so what was wrong there is the description rather than the result.

**TEN OF THIRTEEN MUTANTS SURVIVED THE FIRST DRAFT. FIVE ARE NOW KILLED, each re-verified here
with the mutation asserted to have LANDED IN THE FILE before the run.** Dropping the MAJORITY
conjunct, never incrementing `closer_swapped`, stripping the sign conversion from
`_as_read_int32`, reversing only the OUTER two bytes, and caching a `None`. The repairs are an
inversion assertion in the control, and three LIBRARY-FREE arms -
`test_the_continuity_predicate_needs_a_majority`, `test_the_two_readings_are_exact_byte_reversals`
and `test_a_library_less_call_does_not_switch_the_continuity_grader_off` - which also give this
work its first arms that run on CI, where every library-backed arm here skips.

**ONE SURVIVOR IS AN EQUIVALENT MUTANT AND CHASING IT WAS REFUSED.** Dropping the MINORITY
conjunct from `_continuity_holds` cannot change a verdict: the three buckets PARTITION
`changed`, so a majority as stored forces the reversal below half arithmetically. The docstring
said the opposite - that the minority half "is the half that matters" - and that sentence is
corrected in the tree. It does NOT hold of `_int_oracle_holds`, whose two counters overlap and
whose conjunction is genuinely two-sided. Three further survivors are population and coverage
mutants whose only kill is a floor at an observed count, which is CS-432's shape; all four are
listed in the module rather than left for the next adversary.

**A CORPUS-COUPLED RED IS CLOSED, AND IT WAS ALREADY LIVE.** Both arms went RED - not skipped -
on a library holding saves this grammar cannot read, and SEVEN of the nineteen files on this
machine are already at a save version outside `TAGGED_PAIRS`. The operator playing the game
would have reddened the suite with no defect. `_derive_continuity` now returns `None` on any
no-evidence state, routing it to the same skip a missing library takes, which also stops a
degenerate sweep reaching the cache - the second hole the adversary demonstrated by caching a
zero sweep and poisoning a session. Both states re-verified here as skips.

**WHAT SURVIVED THE REFUTATION.** Code-independence is real and the adversary could not break
it: no executable statement in the new section touches `_int_oracle_holds`, its accumulator or
any derivation consuming it, so a defect THERE cannot mask or manufacture the verdict HERE.
Containment holds - forced failures render scalars only, no world content, no save path, no
account directory. The control genuinely grades: swapping its uncached derivation for the
memoised one is KILLED.

Verification: `python -m pytest tests/save/test_value_anchoring.py -k "continuity or moves_less
or byte_reversals" -q` - five arms, three of which need no save library. To re-run the
refutation, compare the continuity verdict against `((a >> 24) & 0xFF == 0) + ((b >> 24) & 0xFF
== 0) > ((a & 0xFF) == 0) + ((b & 0xFF) == 0)` over the changed pairs; it agrees 145 of 145.
### 2026-08-23 - CS-421 - a SECOND and genuinely independent int32 oracle ships. CS-421 STAYS OPEN
NOT A COMPLETION RECORD. This is the "smallest thing that improves the evidence rather than
the wording" the adjudication below named, built because that adjudication measured the
premise for declining it FALSE. CS-421 is not re-graded here and no clause is claimed met.

**WHAT SHIPPED.** `tests/save/test_value_anchoring.py` gains a continuity oracle over
`IntProperty` and a control for it. The oracle matches the SAME field across two saves of one
world and asks only whether it MOVED LESS as stored than read backwards. It touches
`_int_oracle_holds` nowhere - not the predicate, not its accumulator, not any derivation
consuming it - so a red baseline there can neither mask nor manufacture this verdict.

**WHY IT COULD NOT HAVE BEEN ANOTHER PREDICATE INSIDE ONE SAVE, which is the part worth
keeping.** Byte reversal is a BIJECTION on four-byte patterns, so every statistic read off the
multiset of stored patterns within a single save is INVARIANT under it - distinctness,
repetition, equality classes and the whole pattern histogram survive unchanged. What is left
is the numeric INTERPRETATION, and every claim about an ISOLATED value's interpretation
reduces to the small-magnitude prior `_int_oracle_holds` already owns. The symmetry had to be
broken by TIME: a value that ticks moves its LOW stored bytes, and the reversal promotes those
to the HIGH end, so the same small change reads as a jump of millions.

**A HYPOTHESIS DIED AND IS RECORDED SO IT IS NOT RETRIED.** The first form was MONOTONICITY -
"a save's integer counters only go up". Measured over the changed matched values: **49.9 per
cent non-decreasing as stored against 49.7 per cent reversed. NO SIGNAL WHATEVER.** This
world's integers go up and down in about equal measure. The movement predicate separated the
same population completely in the same run. Do not re-pitch the order statistic.

**MEASURED, and the mutant was graded the way this project requires.** On the shipped tree the
sweep reads 12 snapshots, 34820 matched keys, 145 of them changed, and **145 moved less as
stored against 0 reversed with 0 tied**. With `"IntProperty": (4, "<i")` patched to `">i"` and
the mutant ASSERTED LIVE IN THE LOADED MODULE before anything was concluded, those two
counters INVERT COMPLETELY to 0 and 145 and the oracle fails at its own conjunction with the
message it is written to give. Reverted through `git checkout --` and the restore confirmed in
a fresh interpreter. The control reproduces that flip INSIDE the suite by replacing
`objects._FIXED_WIDTH_VALUES`, which `_decode_fixed_width` looks up at call time, so the
demonstration is graded on every run rather than by a reader who remembers to try it.

**THE STATED LIMIT, AND IT IS THE PART A LATER SESSION MUST NOT OVERREAD.** Independence here
is a property of the PREDICATE'S FORM - no magnitude is inspected - and NOT a measurement. The
population that would settle it by measurement is the one `_int_oracle_holds` draws no signal
from, changed matches carrying a non-zero as-read high byte at both ends, and that population
is **EMPTY on this library: ZERO of the 145.** An earlier draft of the module banner asserted
the stronger sentence outright and it was cut before it shipped. The grader carries a
conditional assertion over that sub-population which is INERT TODAY, cannot redden while the
sub-population is empty so it carries no corpus-coupled floor, and becomes a real measurement
the day this world holds a large value that ticks. It is disclosed as inert in the tree.

**IT SHARES THE ANCHOR, NOT THE PREDICATE.** Matched values are read at the same `value_at` by
the same shipped walk as the oracles above, so the common-mode locator risk the adjudication
recorded is NARROWED FROM THREE SHARED INPUTS TO TWO and is not removed. CS-455 is untouched:
a decoder returning a plausible small constant does not move between saves either.

**SIBLING CONSIDERED AND DELIBERATELY EXCLUDED.** `_float_oracle_holds` is single-owner in the
same way, but `FloatProperty` already carries a SECOND independent predicate in CS-469's
mantissa-coarseness oracle, so the one-predicate defect this entry repairs does not apply
there. No item filed; extending continuity to floats would add a third float predicate rather
than a first.

Verification: `python -m pytest
"tests/save/test_value_anchoring.py::test_the_shipped_int32_reading_moves_less_between_saves_than_its_reversal"
"tests/save/test_value_anchoring.py::test_the_continuity_oracle_refuses_a_flipped_shipped_byte_order" -q`
passes on the shipped tree and skips with no library. To see it discriminate, patch
`"IntProperty": (4, "<i")` to `">i"`, confirm `objects._FIXED_WIDTH_VALUES["IntProperty"]` in a
FRESH interpreter before believing the mutant landed, and re-run the first of those two - it
fails reporting 0 of 145. Restore with `git checkout -- clockspeed/save/objects.py`.
### 2026-08-23 - CS-421 - ADJUDICATED DO-NOT-CLOSE, and a CORRECTION to the entry below
CS-421 STAYS OPEN. This corrects the record immediately below rather than editing it, which
is what this file requires. The close was routed to an adjudicator on the operator's
instruction; the adjudicator produced none of the work it graded, ran its mutation in an
OUT-OF-TREE copy built from `git ls-files` so it never touched this working tree, and
returned DO-NOT-CLOSE. Every finding below was re-verified by the merger before it was
written here.

**THE VERDICT.** Clause 1 MET WITH A STATED LIMIT - it grades completeness and vocabulary,
not the truth of the class named, and only `EVIDENCE_MAGNITUDE` is tied to a live control,
through the hand-written `_MAGNITUDE_SCORED_TYPES`, which CS-459 owns. Clause 2 MET. **Clause
3 NOT MET.**

**THE GROUND THAT DECIDES IT, AND THE MERGER RE-READ IT FROM A FRESH INTERPRETER.**
`objects.BYTE_ORDER_STATUSES` is `anchored_not_unique`, `oracle_cannot_separate_readings`,
`unscored`, `vacuous_one_byte`. **NO WORD IN THE SHIPPED VOCABULARY MEANS SETTLED**, and
every four-byte type ships one that denies it - `IntProperty` and `FloatProperty`
`anchored_not_unique`, `UInt32Property` `oracle_cannot_separate_readings`. Closing clause 3
would put this file in direct contradiction with the module, and clause 2 is the clause that
insisted the MODULE owns this fact rather than prose.

**CORRECTION ONE - THE ENTRY BELOW CANNOT COUNT.** It says 13 tests fail, five are
library-backed, "Six are synthetic and the thirteenth is the nested no-install gate". That is
5 + 6 + 1 = 12. Re-counted from the same run output: there are SEVEN non-library, non-gate
reds in `tests/save/test_properties.py`, so the split is **5 + 7 + 1 = 13**. The 13 and the
five names are correct and reproduce; the sentence that partitions them is not.

**CORRECTION TWO, AND IT IS THE SUBSTANTIVE ONE. "FIVE LIBRARY-BACKED PLACES" OVERSTATES
INDEPENDENCE.** It is ONE predicate consumed at five sites. `_int_oracle_holds` in
`tests/save/test_value_anchoring.py` is single-owner by its own docstring and feeds the
anchor sweep, the permutation sweep and the separability sweep alike; the fifth red spells
the identical majority-minority conjunction inline in `tests/save/test_properties.py`.
Verified by the merger at all four call sites. FOUR OF THE FIVE DISCLAIM THEIR OWN RESULT IN
THEIR FAILURE TEXT - they report that their baseline is red and the comparison therefore
means nothing. So one library-backed oracle catches the flip and four further tests refuse to
compute. **The entry below declined to add a test on the ground that "an arm asserting what
five existing arms assert is the redundancy this project refuses". That premise is FALSE:
there is one arm, not five, and a second INDEPENDENT library-backed control is therefore real
work rather than redundancy.**

**FENCE 1 WAS CROSSED.** "DO NOT RE-PITCH THE CLOSE ON THE ARTIFACT EXISTING" - not by the
singleton or the 13/5, which are new material, but by offering `UInt32Property`'s
`oracle_cannot_separate_readings` as disposing of the residual. The fence's arithmetic was
re-verified: the single stored pattern reads 6400, which is 25 x 256, and only the 255
multiples of 256 reach the undecided state while 65280 of 65535 would have driven the same
oracle green. The status is an accident of the one value this world carries. Fences 2, 3 and
4 are intact.

**WHICH PRIOR REFUSALS STILL STAND.** The 2026-08-16 anchoring refusal and the 2026-08-17
two-candidate refusal are ANSWERED and no longer stand. **The 2026-08-17 singleton refusal
and the 2026-08-18 route (b) refusal STAND UNTOUCHED** - the result is JOINT rather than
per-type, `UInt32Property` is scored by nothing, and carrying the joint result across needs a
premise `objects.py` refuses in writing.

**COMMON-MODE RISK, RECORDED RATHER THAN WAVED AT.** Three shared inputs and nothing tests
any of them: the single `_int_oracle_holds` predicate above; all three oracles receiving
bytes at the same `value_at` from the same `_read_tag_header` walk, which the 2026-08-17
record already called "closer to one oracle than to three"; and every library-backed figure
in this item coming from ONE world across the saves the separability sweep reads.

**WHAT WOULD CLOSE IT.** Either an OPERATOR RULING amending clause 3 to say what it now means
- settled JOINTLY over the scored populations against the real save library, with the
per-type residual recorded in shipped data - with the `UInt32Property` residual filed as its
own item; an adjudicator cannot grant that narrowing, because narrowing an acceptance clause
is exactly fence 1's forbidden move. OR a second library-backed control that catches the
`">i"` flip through a predicate that is NOT `_int_oracle_holds`, which would make "two
independent library-backed oracles" true where "five places" is not.

Verification: `python -c "from clockspeed.save import objects as o;
print(sorted(o.BYTE_ORDER_STATUSES)); print(dict(o.VALUE_BYTE_ORDER_STATUS))"` shows no word
meaning settled and every four-byte type carrying one that denies it. For the single-owner
predicate, `grep -n "_int_oracle_holds" tests/save/test_value_anchoring.py` shows the
definition and its three consumers, and `tests/save/test_properties.py` lines 1672 to 1683
carry the inline twin. For the count, re-run the mutation recorded in the entry below and
partition the 13 `FAILED` lines yourself.
### 2026-08-23 - CS-421 - NOT A COMPLETION RECORD. CS-421 STAYS OPEN; TWO of its own headline claims measured FALSE
This entry records a MEASUREMENT and closes nothing. No clause was re-graded and no
acceptance was declared met. It exists because CS-421's documentation described a gap the
tree had ALREADY closed, and a session taking the item on the written framing would have
rebuilt machinery that exists. Both corrections are in tracked files per `CLAUDE.md`
section 8; the item stays OPEN in `ROADMAP.md`.

CLAIM ONE - "60.1 PER CENT OF THE DECODE IS BACKED BY A DECLARED WIDTH AND NOTHING ELSE".
STALE, and the population is NOT what moved. A census re-derived from the live library
reproduces every archived figure digit for digit - 185382 measured tags, IntProperty 75136,
FloatProperty 31318, BoolProperty 4077, Int8Property 824, UInt32Property 9, and 111364 =
60.1 per cent under the ARCHIVED assumption. What moved is the EVIDENCE TABLE: CS-469
(session 17) gave `IntProperty` and `FloatProperty` a second oracle, so
`objects.EVIDENCE_FOR_VALUE_TYPE` records `magnitude_distribution` beside `declared_width`
for both, and `objects.WIDTH_ONLY_VALUE_TYPES` is BoolProperty, Int8Property and
UInt32Property alone - **4910 of 185382, which is 2.6 per cent.** The item's own title
route, "raise the evidence standard for the width-only property types", was therefore
largely EXECUTED across sessions 16 to 19 and nobody re-measured the headline.

CLAIM TWO - "PATCHING IntProperty TO `">i"` REDDENS ONLY SYNTHETIC-FIXTURE TESTS". FALSE.
The mutant was asserted live IN THE LOADED MODULE rather than merely written to the file,
the floor was a full-suite green run at the same tree, and the same named tests were re-run
after the revert so a save library that moved mid-session could not be mistaken for the
mutant's effect. **13 tests fail in `tests/save` and FIVE ARE LIBRARY-BACKED**, each
confirmed by its own skip guard rather than by its name:
`tests/save/test_properties.py::test_the_int32_byte_order_is_discriminated_by_the_stored_high_byte`
(`_decode_sweep_or_skip`), and in `test_value_anchoring.py`
`test_the_shipped_candidate_set_is_what_the_value_oracles_cannot_separate` and
`test_the_mantissa_coarseness_oracle_separates_the_middle_swap_from_the_identity`
(`_permutations_or_skip`),
`test_the_displacement_the_value_oracle_tolerates_is_the_one_the_anchor_catches`
(`_anchor_or_skip`) and `test_the_int32_oracle_still_separates_a_type_it_can_separate`
(`_separability_or_skip`). Six are synthetic and the thirteenth is the nested no-install
gate. **THE FALSE SENTENCE WAS SITTING IN THE DOCSTRING OF ONE OF THE TESTS THAT REFUTES
IT** - the ADR 0008 shape, where a reader checking the claim by running the named mutant
finds the thing it denies. It was TRUE when written; the magnitude oracle and CS-469's
third oracle landed under it and the demonstration was never re-run.

WHAT WAS DELIBERATELY NOT DONE. No new test was added: the flip is already caught in five
library-backed places, and an arm asserting what five existing arms assert is the
redundancy this project refuses. No clause was marked met - `BYTE_ORDER_SURVIVING_CANDIDATES`
being a library-derived SINGLETON is evidence about clause 3, not a verdict on it, and the
measurement's author is the wrong party to grade it. Whether CS-421 now closes is left to
the operator and an adjudicator that did not produce this measurement; the three prior
refusals stand until then.

Verification: claim one - `python -c "from clockspeed.save import objects as o;
print(sorted(o.WIDTH_ONLY_VALUE_TYPES)); print(sorted(o.EVIDENCE_FOR_VALUE_TYPE['IntProperty']))"`,
and the table is tied to the running controls by
`tests/save/test_properties.py::test_the_magnitude_oracle_covers_exactly_the_types_marked_with_it`.
Claim two - patch `"IntProperty": (4, "<i")` to `">i"` in `clockspeed/save/objects.py`,
confirm `objects._FIXED_WIDTH_VALUES["IntProperty"] == (4, ">i")` in a FRESH interpreter
before believing the mutant landed, run `python -m pytest tests/save -q --tb=no -rf` and
expect 13 failed / 1191 passed with the five names above among them, then
`git checkout -- clockspeed/save/objects.py` and re-run those 13 for 13 passed. Do NOT read
the exit code of a `pytest | tail` pipeline - it is tail's, which is the CS-703 shape.
### 2026-08-22 - CS-823 - ADVERSARIAL REFUTATION of this session's own suite, and the repair: SIX wrong hooks passed all fourteen arms
Verification: `tests/test_hook_interpreter_ladder.py::test_a_gate_that_talks_but_never_banners_is_refused`
and `::test_a_banner_that_is_not_the_last_line_is_refused`. Both were added AFTER the closure record
below and both were proven to KILL the survivors in a mirror, with each mutation asserted to have
LANDED first. Measured: against the shipped hook both pass; against a `grep -F | tail -n 1` mutant one
fails; against a `?*)` accept-any-non-empty mutant both fail. The module is 87 passed, not the 85 the
entry below records, and that entry is CORRECT AS WRITTEN FOR THE TREE IT DESCRIBED - this record
supersedes its count rather than contradicting its claims.
WHAT THE ADVERSARY REFUTED. The claim was that no wrong implementation of the repair could pass the
suite. It is FALSE, and six did: accept when the last line is NON-EMPTY, accept on a non-zero BYTE
COUNT, accept when the last line merely starts with the gate's NAME, plain CONTAINMENT, and - the
sharpest - `CS_GATE_LAST=$(printf ... | grep -F "$CS_GATE_PASS" | tail -n 1)`, which leaves the
declared pattern BYTE-IDENTICAL and changes only which line it is applied to. Every one of them
commits a staged em dash through a gate that checked nothing.
THE SHARPEST SURVIVOR IS THE ONE WITH NO DEAD CODE, and that is why it matters more than the count.
It is what an ordinary "make this less brittle" edit looks like, and the hook's own comment claimed
the property it violates - "a banner anywhere but the final line is refused" - while NO ARM
EXERCISED THAT SENTENCE. A claim in a comment that no test backs is the ADR 0008 shape, inside the
item that was supposed to be careful about it.
A SECOND FINDING, AND THE CORRECTION IS IN THE TREE RATHER THAN ONLY HERE. The section banner said
the `gate_compiles` assertions were "why these arms mean anything". MEASURED BY ABLATION: deleting
both leaves the module GREEN, so they are inert today. They are a premise fence for a future gate
restructure, the premise is separately fenced by the main-guard arm, and what actually makes the
truncation arms mean something is that each one COMMITTED before the repair. The sentence is
rewritten in place to say that.
ONE EQUIVALENT MUTANT IS RECORDED AND DELIBERATELY NOT CHASED. Dropping `tr -d` survives, because
this toolchain's command substitution already strips the CR - measured with `od -c`, no CR present.
That is an equivalent mutant on THIS machine, not a hole; the strip stays because the anchored
pattern would refuse every commit on any toolchain where a CR did survive, and CONVENTIONS.md
section 16 forbids inheriting one shell's tolerance. Do not delete it and do not weaken an arm to
kill it.
THE METHOD NOTE WORTH CARRYING. The refutation came from an agent that RAN mutants, not from one
that read the arms - 18 mutants against 12 arms, then 14 against 14, plus harness ablations and about
30 real-commit divergence measurements. It also caught that the artifact moved underneath it
mid-run, and said so rather than reporting a stale result. THREE ARMS STILL PASS AGAINST A HOOK THAT
IS LITERALLY `exit 0`, which is recorded as a known property rather than repaired: the accept arm is
not tautological in context, because the truncation and file-blind arms prove the hook runs.
### 2026-08-22 - CS-823 - CLOSED: the pre-commit hook now PROVES the gate ran, instead of reading an unrun gate's exit 0 as a pass
Verification: `tests/test_hook_interpreter_ladder.py`, the CS-823 section, driving REAL `git commit`
in a throwaway repository. The arms that decide it are
`::test_a_truncated_gate_cannot_wave_a_forbidden_byte_through` over three truncation points,
`::test_a_truncated_gate_refuses_a_clean_commit_too` over the same three, and
`::test_an_interpreter_that_cannot_run_a_file_is_refused_by_the_gate_guard`. All NINE were RED on the
tracked hook before the edit, each with the defect's own signature - `exit=0 head_moved=True` and no
hook output at all - and the module is 85 passed after it. Merged file: `.githooks/pre-commit`, under
the operator grant recorded in this file immediately below, which PRECEDED the edit.
WHAT WAS WRONG. The hook tested that the gate FILE existed and then ran it, taking the whole decision
from `$?`. Nothing proved the gate EXECUTED. `tools/precommit_gate.py` ends in an `if __name__ ...`
main guard, so a copy truncated anywhere before it defines everything and executes NOTHING - python
exits 0 and the hook read that 0 as a pass. 1020 of 2396 line-boundary prefixes compile, so it is
closer to a coin flip than to a corner case. THE INDEX WAS NO PROTECTION: the hook loads the gate
from the WORKING TREE while the gate reads the files under test from the INDEX.
WHAT SHIPPED. The gate invocation is wrapped in a command substitution; the captured stdout is
RE-EMITTED before any decision; the non-zero path is unchanged; and on a ZERO exit the hook requires
the gate's own success banner AS THE LAST LINE, matched by a `case` pattern anchored at both ends
with only the two counts wild. A gate that never ran yields exit 0 with EMPTY stdout and is refused.
NO line of `tools/precommit_gate.py` changed - it is separately frozen and was outside the grant.
THE SECOND ESCAPE THIS CLOSED WAS NOT WHAT THE ITEM WAS FILED ABOUT, and it was LIVE on `main` at
`9d591cd`. The CS-703 probe validates the `-c` invocation shape; the gate is invoked as a FILE. A
four-line `sh` wrapper that execs the real interpreter for `-c` and exits 0 for anything else answers
BOTH probe halves HONESTLY - measured, it printed `clockspeed-python-ok` and returned 97 - and never
runs the gate. With it in `CLOCKSPEED_PYTHON`, a staged em dash COMMITTED through the tracked hook
with exit 0, HEAD moved and ZERO bytes of stderr. It knows no token and is not built against the
probe. CS-703 neither closed this nor claimed to. It is the pre-commit twin of CS-819's
silent-interpreter defect, it was found by the ADJUDICATOR rather than by the builder, and it was
believed only after being reproduced independently. `FILE_BLIND_SHIM` is that wrapper, and its arm
asserts the refusal comes from the GATE guard and NOT from the probe - which is satisfied.
THE PREDICATE IS ANCHORED, AND THAT IS STRONGER THAN THE PREFIX FIRST BUILT. MEASURED against nine
replacement gates: a banner followed by another line, a banner preceded by text, a banner head
followed by junk, non-numeric counts, and a non-zero blocking count are ALL REFUSED - and three of
those five would have been ACCEPTED by the prefix test that shipped in the first draft. The
disclosed limit is measured too: a stub printing one well-formed banner IS accepted.
NO BYTES ARE LOST FROM WHAT THE OPERATOR SEES, and the one change is disclosed rather than hidden.
MEASURED as line multisets over stdout and stderr combined, PRE against POST: the ACCEPT path is
SEQUENCE IDENTICAL, and the BLOCKED path is identical as a MULTISET with the CS-209 coverage-skip
lines moving from before the gate's BLOCKED banner to after it. That reordering is intrinsic to
capturing one stream while the other streams live. The skip lines are re-emitted rather than consumed
BECAUSE they are the channel that says a check's detection was REDUCED - which is where this
deliberately departs from CS-819, whose sentinel is noise and is swallowed.
A NEW DEPENDENCY ON A FROZEN FILE WAS CREATED AND IS NOW PINNED. Command substitution waits for EOF
on the pipe rather than for the child to exit, so a gate that spawned a process holding stdout open
would HANG the hook rather than fail it. Both `subprocess` calls in the gate pass `capture_output`,
which was the only thing preventing that and was pinned nowhere;
`::test_the_gate_spawns_no_child_that_could_inherit_the_captured_stdout` now asserts it by AST,
without touching the gate.
THE COUPLING IS PINNED FROM BOTH SIDES, NEITHER RESTATED IN A TEST. The gate's format string is
LOCATED in its source and rendered; the hook's head and `case` pattern are EXTRACTED from the hook
and applied with `fnmatch`; a negative control fails if the pattern degenerates into one that matches
anything. The LIVE half is `::test_an_intact_gate_still_accepts_a_clean_commit`, which goes RED if
the gate's banner ever changes, because a clean commit would then be refused as unrun.
WHAT THIS DOES NOT BUY. It is an ACCIDENT DETECTOR, NOT A SECURITY BOUNDARY - the same disclosure the
probe carries. A program written on purpose to print a well-formed banner passes it, and
`git commit --no-verify` skips every hook regardless. While the gate is broken the hook is SAFE, not
USABLE: every commit is refused then, including legitimate ones, the same accepted cost CS-819
records. The refusal text names all three known causes, the changed banner format among them, so an
operator who edits the gate is not sent hunting.
ONE SIBLING SITE IS FILED RATHER THAN FIXED. `.githooks/pre-push` has no CS-823 shape - pytest comes
from site-packages, not the working tree - but it has the analogue one level up: NO FLOOR ON WORK
DONE. pytest exits 0 having run one test exactly as it does having run the whole suite, and the hook
never reads the count. Filed as its own item; it needs its own grant and is not closed here.
### 2026-08-22 - CS-823 - FROZEN-FILE GRANT ISSUED by the OPERATOR for `.githooks/pre-commit`, then GRANT-SOUND with conditions from an adjudicator
Verification: this entry is the grant record CLAUDE.md section 6 requires BEFORE the edit, not a
completion record. NOTHING IS CLOSED BY IT. CS-823 stays OPEN in `ROADMAP.md` until its own closure
record. It does NOT widen the CS-703 or CS-819 grants recorded below on this same date; both
explicitly EXCLUDED this file, and the operator decided on 2026-08-22 to file this rather than widen
a third time in one session. GRANTED BY THE OPERATOR in direct answer to a question naming CS-823,
this one file and the designed change; the adjudicator that then reviewed it produced none of the
work it judged and returned GRANT-SOUND with seventeen conditions.
THE DEFECT AS FILED. `.githooks/pre-commit` tested that the gate FILE existed and then ran it, taking
the whole decision from `$?`. Nothing proved the gate EXECUTED. `tools/precommit_gate.py` ends in an
`if __name__ ...` main guard, so a copy truncated anywhere before that guard defines everything and
executes NOTHING - python exits 0, and the hook read that 0 as a pass.
RE-MEASURED INDEPENDENTLY rather than inherited from the filing, with real commits staging an em dash
and the gate truncated in the WORKING TREE only. Intact control: exit 1, HEAD unchanged, 576 bytes of
stderr. Truncated to 2368 lines, truncated to 1 line, and emptied to 0 bytes: ALL exit 0, HEAD MOVED,
ZERO bytes of stderr. Compiling every line-boundary prefix, 1020 of 2396 truncation points are
syntactically valid. The filing recorded 561 bytes and 1019 of 2395. The census difference is a
counting convention and is fully explained - this run counts the 0-line prefix as a truncation point
and the filing did not, so both halves are one larger. THE 15-BYTE STDERR DIFFERENCE IS NOT EXPLAINED
HERE AND NO CAUSE IS INVENTED FOR IT. What the control rests on is the SIGN, not the size: an intact
gate produces hundreds of bytes of stderr and a gate that did not run produces ZERO.
A SECOND ESCAPE, FOUND BY THE ADJUDICATOR AND RE-MEASURED INDEPENDENTLY BEFORE BEING BELIEVED. IT IS
LIVE ON `main` AT `9d591cd` AND THE ITEM DOES NOT CLAIM IT. The CS-703 probe asks a candidate to run
a `-c` program; the gate is invoked as a FILE. A four-line `sh` wrapper that execs the real
interpreter for `-c` and exits 0 for anything else therefore answers BOTH probe halves HONESTLY - it
printed `clockspeed-python-ok` and returned 97, both measured - and ignores the gate entirely.
Against the TRACKED hook with that wrapper in `CLOCKSPEED_PYTHON`, a staged em dash COMMITTED: exit
0, HEAD MOVED, ZERO bytes of stderr. The wrapper knows no token and is not built against the probe.
CS-703 NEITHER CLOSED THIS NOR CLAIMED TO - it validates the `-c` shape and this is the FILE shape -
and this is the pre-commit twin of the CS-819 silent-interpreter defect. The same guard refuses it.
THE INDEX IS NO PROTECTION, which is what makes the first shape more than a curiosity. The hook loads
the gate from the WORKING TREE while the gate reads the files under test from the INDEX, so a correct
committed copy does not help.
SCOPE, ONE REGION. In `.githooks/pre-commit` ONLY: replace the gate-invocation tail - lines 205 to
213, from `cs_python "$GATE" --staged` to the final `exit` - with a captured invocation, a re-emit of
the captured stdout, the existing non-zero branch unchanged, and a last-line check of the gate's own
success banner; plus the comment block that documents it. NO line of the interpreter ladder, the
`cs_probe` function, the `die` helper or the CLOCKSPEED_PYTHON refusal may change. NO line of
`tools/precommit_gate.py`, `.githooks/commit-msg`, `.githooks/pre-push`, `.claude/settings.json` or
`scripts/install_hooks.py` may change. The gate is separately frozen and is NOT part of this grant.
WHY THE GATE'S EXISTING BANNER RATHER THAN A NEW SENTINEL. The gate already writes its success banner
to stdout as the LAST thing it writes on a zero exit - verified by reading every stdout write in
`emit`, which is the only function in the file that writes stdout at all. So the invariant is
established with ZERO change to a separately-frozen file. This asserts exactly what CS-819's sentinel
asserts, THE PROGRAM RAN TO COMPLETION, and differs only in reusing an existing observable.
THE PATTERN IS ANCHORED AT BOTH ENDS AND THIS DOES NOT REOPEN THE CS-703 FENCE. That fence -
EXACT EQUALITY, NOT CONTAINMENT - lives in three code comments and in no doctrine file, and each
scopes itself by its own text to the PROBE token. It is untouched: the probe still compares a single
fixed token for exact equality. The banner cannot be compared that way because it embeds two counts
that differ per commit and the gate that renders them is frozen, so a `case` pattern with only those
two counts wild is the strictest predicate REACHABLE. Because a `case` pattern matches the WHOLE
word, it is not a substring search. MEASURED against nine replacement gates: a banner followed by
another line, a banner preceded by text, a banner head followed by junk, non-numeric counts, and a
non-zero blocking count are ALL REFUSED, and three of those five would have been ACCEPTED by the
plain prefix test this replaced.
THE CARRIAGE RETURN IS STRIPPED RATHER THAN TOLERATED. Because the pattern is anchored at its END, a
surviving CR would refuse every commit. Python writes CR LF to a pipe on Windows and this bash strips
both in a command substitution, which is exactly the version-specific tolerance CONVENTIONS.md
section 16 forbids inheriting. `tr -d` removes the dependency; `tr` is already used by the flood cap
in this hook, so it is no new dependency, and if `tr` were absent the capture goes empty and the hook
fails CLOSED.
THE CAPTURED STDOUT IS RE-EMITTED, NOT SWALLOWED, and this is the one place the design deliberately
departs from CS-819. That hook's sentinel is noise and is consumed; a test pins that it leaks
nothing. This gate's stdout is a REPORT - it carries the CS-209 coverage-skip lines, whose whole
purpose is to tell the operator their detection was REDUCED. Copying CS-819's shape here would delete
that channel from the only invocation that gates a commit.
THE BLOCKED PATH REORDERS, DISCLOSED RATHER THAN HIDDEN. MEASURED as line multisets over stdout and
stderr combined, PRE against POST: the ACCEPT path is SEQUENCE IDENTICAL, and the BLOCKED path is
identical as a MULTISET with the CS-209 skip lines moving from before the gate's BLOCKED banner to
after it. NO BYTES ARE LOST on either path. It is intrinsic to capturing one stream while the other
streams live and is not fully mitigable. The alternatives are worse: a pipeline makes `$?` the LAST
command's status, which is the exact escape this hook already fences, and a temporary file adds
lifetime and cleanup for nothing.
A NEW DEPENDENCY ON A FROZEN FILE IS CREATED AND IS PINNED FROM THE TEST SIDE. Command substitution
waits for EOF ON THE PIPE rather than for the child to exit, so a gate that spawned a process holding
stdout open would HANG this hook rather than fail it - and a hung hook reads as a hung credential
dialog. The gate spawns twice, ruff and git, and both pass `capture_output`, so each child gets its
own pipes. That is the ONLY thing standing between this capture and a hang, and nothing pinned it, so
an AST arm now asserts every `subprocess` call in the gate redirects its child's stdout. The gate
itself is not touched.
THE CONDITIONS THAT BIND THIS GRANT are the adjudicator's; the load-bearing ones are recorded here
because this is their only tracked home. PLAIN ASSIGNMENT ONLY on the capture - no `export`, `local`
or `readonly`, each of which MASKS `$?` to 0 in both bash and dash - with a fence test, which existed
for commit-msg and had NO pre-commit equivalent until this item. Both new variables initialised
before first use, because `set -u` is on. The check fires ONLY on a zero exit; the non-zero path is
behaviourally unchanged. Stderr is NEVER captured. The re-emit uses `printf '%s\n' "$var"` and never
`printf "$var"`, because a percent sign in a skip reason or a file name would corrupt the output, and
it is guarded on non-emptiness. The new constant is NOT named with a `CS_PROBE_` prefix, because the
cross-hook byte-identity extractor sweeps every such line file-wide and a collision would redden an
arm whose only in-scope repair is editing the other two hooks. The contract test has exactly TWO
sides, both EXTRACTED from their own files rather than restated in a test constant, with a negative
control that fails if the pattern degenerates to one matching anything. Every refusal arm asserts
non-empty output as well as a non-zero exit, because the defect's signature is exit 0 WITH ZERO BYTES
OF STDERR. Every truncating arm asserts its bytes still COMPILE, because a truncation that raised
would make the hook refuse for a reason that is not this defect. The refusal text names the changed
banner format as a candidate cause, so an operator who edits the gate is not sent hunting. The
acceptance arms drive the REAL tracked hook through real commits. RED is demonstrated before GREEN.
This record precedes the edit.
WHAT THIS DOES NOT BUY, stated because a gate that overclaims is worse than none. It is an ACCIDENT
DETECTOR, NOT A SECURITY BOUNDARY - the same disclosure the probe already carries. A program written
on purpose to print a well-formed banner passes it - MEASURED, and accepted - and `git commit
--no-verify` skips every hook regardless. It also makes the hook SAFE, not USABLE, while the gate is
broken: every commit is refused then, including legitimate ones, which is the same accepted cost
CS-819 records. And the banner coupling is a permanent cost: any future edit to the gate's PASS line
refuses every commit until this hook is updated with it. Loud rather than silent, which is the trade
this hook already states, and the refusal text is what keeps it from costing an hour.
ONE SIBLING SITE IS REPORTED AND DELIBERATELY NOT FIXED HERE. `.githooks/pre-push` runs pytest and
reads `$?`. The CS-823 shape does NOT transfer - pytest comes from site-packages, not the working
tree, so there is no truncatable file - and the zero-collection case is already refused by its exit-5
guard. What remains is the analogue one level up: THERE IS NO FLOOR ON WORK DONE. pytest exits 0
having run one test exactly as it does having run the whole suite, and the hook never reads the count.
That is `pre-push`-only, its fix is a count floor rather than a completion sentinel, and it needs its
own item and its own grant. It is NOT covered by this grant and nothing here closes it.
COMMON-MODE RISK. Every measurement here is Windows, msys bash 5.2.37, git 2.53.0.windows.3. CI tier
2 runs `/bin/sh` as dash on Ubuntu, where python emits no CR at all. The CR strip removes the
dependency rather than resting on either platform, and what would settle it is the new arms running
green on the Ubuntu tier-1 job.
### 2026-08-22 - CS-819 - CORRECTION and a DISCHARGED RESIDUAL: glibc dash delivers the heredoc, measured by CI, and the platform arms were premised on the wrong shell
Verification: `tier1` run `32609343989` at `be5cd81`, `ubuntu-latest`, is the measurement. Its log
carries `AssertionError: the heredoc delivered 4535 bytes under dash`. The repair is
`tests/test_hook_interpreter_ladder.py::test_no_violation_class_slips_through_under_dash`, which now
takes a branch selected by `_dash_heredoc_delivery()` rather than by whether dash exists.
THE CLOSURE RECORD ABOVE LISTS AS AN OPEN RESIDUAL that "whether glibc dash delivers a heredoc above
4096 is INFERRED, not measured". **IT IS NOW MEASURED: 4535 delivered bytes on `ubuntu-latest`,
against 0 on the MSYS2 build.** The residual is DISCHARGED, and the Ubuntu conclusion the CS-819
grant reached from a green CI log is confirmed by direct observation rather than by inference.
**THE TRUNCATION IS A PROPERTY OF THE BUILD, NOT OF DASH,** and this entry states it that way because
the first filing did not. MSYS fork emulation breaks dash's `openhere()` writer path above the
4096-byte pipe threshold; glibc dash takes the same path correctly.
**WHAT WAS WRONG WITH THE SHIPPED TESTS, and it is a defect in the acceptance rather than in the
hooks.** Both platform arms encoded "dash truncates". On CI the program therefore ARRIVED, every rule
fired correctly and reported its own reason, and the arms read CORRECT BEHAVIOUR as a broken premise -
six failures, all one cause. The hooks were never wrong on either shell.
**THE DELIVERED-BYTES CONTROL IS WHAT MEASURED THIS, BY FAILING LOUDLY RATHER THAN PASSING QUIETLY.**
The CS-819 grant's condition TWO asked for exactly that control, on the reasoning that a future dash
which fixed the bug would otherwise turn the arm into a tautology. It did its job on the first CI run
after it shipped. It is kept, and it is now the BRANCH SELECTOR rather than a bare assertion.
**BOTH BRANCHES NOW ASSERT SOMETHING TRUE AND NEITHER IS A SKIP.** A truncating build must refuse
every violation class BY THE SENTINEL - CS-819's accepted cost. A delivering build gets the STRONGER
property: every class refused BY ITS OWN RULE with the sentinel ABSENT, which proves the hook behaves
identically under dash and bash and that the sentinel costs a delivering shell nothing. Only the
total absence of dash is loudly not-run.
**THE TRANSFERABLE PART, and it is the same shape as CS-703's.** A local suite and a green pre-push
are evidence about THIS toolchain and nothing else. `CONVENTIONS.md` section 16 already says hook
findings are version-specific and expire; this entry adds that a PLATFORM PREMISE BAKED INTO A TEST is
a defect of the same class as a hook that trusts a name - it is an assumption asserted rather than
measured. The fix in both cases is to measure the property at run time and branch on it.
### 2026-08-22 - CS-703 - CLOSED: an interpreter must now PROVE it ran the program AND can report a failure, and a pinned-but-broken one is refused rather than silently replaced
Verification: `.githooks/pre-commit`, `.githooks/commit-msg` and `.githooks/pre-push` carry a
byte-identical `cs_probe`; the acceptance is
`tests/test_hook_interpreter_ladder.py::test_every_hook_refuses_an_interpreter_that_cannot_report_failure`
with
`tests/test_hook_interpreter_ladder.py::test_a_liar_on_the_path_is_refused_with_no_environment_variable_set`
beside it, because the escape was reachable with NO environment variable at all. The non-vacuity
control is `tests/test_hook_interpreter_ladder.py::test_an_honest_wrapper_is_still_accepted` - without
it every arm above is satisfied by a hook that refuses everything. Common-mode control:
`tests/test_hook_interpreter_ladder.py::test_the_three_hooks_carry_a_byte_identical_probe`.
WHAT WAS WRONG. All three hooks shared a probe that ran the candidate with `-c` and judged ONLY the
exit code, so `true`, `:` and `echo` passed it; the real work was then handed to a program that
ignored it and exited 0. MEASURED with real commits: with the interpreter substituted, a staged em
dash LANDED, a co-authorship trailer git reads back as REAL landed, and a RED suite reached the
remote - all three exit 0.
FOUR REFUTATIONS, AND NOT ONE CAME FROM READING THE CODE. Every one came from an agent RUNNING it.
Build one judged STDOUT only - and every gate decision reads `$?`, so a wrapper that forwards stdout
faithfully and drops the exit status answered the probe with the exact token and turned all three
gates into no-ops. Two ordinary shapes do it and neither knows the token: a POSIX wrapper ending in
`| cat`, because a pipeline's status is its last command's, and a Windows `.cmd` using
`setlocal`/`endlocal`, because `endlocal` resets ERRORLEVEL. **THAT ESCAPE NEEDED NO ENVIRONMENT
VARIABLE** - a shim installed as `python` on PATH reached it through the ladder's own second rung,
which is why the item was never a `CLOCKSPEED_PYTHON` problem. The fix demands a distinctive non-zero
code back as well as the token.
THE THIRD AND FOURTH REFUTATIONS WERE OF THE SUITE RATHER THAN THE HOOKS, and that is the part worth
carrying. A mutation pass found grant condition 4 and the flood cap each pinned on ONE HOOK OF THREE -
deleting them from the other two left the suite GREEN - because the identity check covered only the
probe and the message arms were hardwired to one hook. It also found the three headline arms asserting
only "something blocked", which stayed green under a FULL revert of the ladder change. All three are
fixed, and the refusal block is now covered by its own identity arm with its own non-vacuity control.
**THE MERGER'S OWN ORACLE HAD THE SAME BLIND SPOT AS THE SUITE** and this is recorded because the
lesson generalises: it substituted only `true`, which fails at the stdout comparison and never reaches
the exit-code question. A harness that cannot reach a channel cannot grade it. It was extended with
exit-fidelity, honest-wrapper non-vacuity and PATH-shadowing arms and now runs 23 arms, 6 of which
fail against the pre-repair hooks and 9 of which are controls.
ONE DEFECT WAS FIXED BY THE MERGER AFTER THE BUILD, and it is named so it is not mistaken for
builder work: the refusal glossed `not reached` as "the output comparison failed first", which is
false when the candidate could not be EXECUTED at all. Both paths are now named in the message. No
arm pinned that gloss, and none was added - it is a wording correction, not a new invariant.
CONDITION 7 IS NOT MET IN ITS LITERAL FORM AND THIS ENTRY SAYS SO RATHER THAN CLAIMING IT. The
condition asks that `scripts/install_hooks.py` run clean. Its `inspect_hook` was run over all three
hooks - `OK, LF, ascii`, exit 0 - but the whole script was NOT run, because `install()` writes
`core.hooksPath` as a RELATIVE path while this machine holds an ABSOLUTE one. From the main checkout
those behave alike; from a worktree a relative value resolves to THAT worktree's `.githooks`, which
would repoint hook resolution for eight existing worktrees and let an agent editing a hook disarm the
gate judging its own commit. Changing the operator's git configuration was not a side effect this
item was entitled to take.
SEVEN RESIDUALS ARE FILED RATHER THAN CLAIMED CLOSED, each with its own item and its own measurement:
CS-815, CS-816, CS-817, CS-818, CS-820, CS-821 and CS-823. The probe proves PYTHONHOOD, NOT TOOLCHAIN,
and that is the biggest of them. The hook says in terms that it is an ACCIDENT DETECTOR, NOT A SECURITY
BOUNDARY: a program written on purpose to print the token and exit 97 passes both halves, and
`--no-verify` skips every hook without needing to.
COMMON-MODE RISK, recorded because every measurement in this entry shares it: one toolchain, git
2.53.0.windows.3 on one msys installation. `CONVENTIONS.md` section 16 says hook findings are
version-specific and expire. Re-measure rather than inherit.

### 2026-08-22 - CS-819 - CLOSED: the commit-msg hook now PROVES its checking program ran, instead of reading an empty program's exit 0 as a pass
Verification: `.githooks/commit-msg` captures the program's stdout and requires a sentinel; the
shell-independent acceptance is
`tests/test_hook_interpreter_ladder.py::test_a_silent_interpreter_is_refused_through_real_git`, which
ALWAYS RUNS and needs no dash, with
`tests/test_hook_interpreter_ladder.py::test_an_honest_interpreter_still_runs_the_checks_through_real_git`
as its non-vacuity control. The platform arm is
`tests/test_hook_interpreter_ladder.py::test_the_msys2_dash_truncation_reproduces_and_is_now_refused`;
where dash is absent it is loudly NOT RUN rather than counted green, on the CS-428 precedent that a
control which could prove nothing must fail rather than skip. The two literals are pinned together by
`tests/test_hook_interpreter_ladder.py::test_the_shell_and_the_program_agree_on_the_sentinel`, and the
status-masking prefixes are fenced by
`tests/test_hook_interpreter_ladder.py::test_the_capture_is_a_plain_assignment_with_no_status_masking_prefix`.
WHAT WAS WRONG. The hook delivered its checking program as a 4181-byte heredoc. The MSYS2 build of
dash delivers ZERO bytes for a heredoc above 4096, so `python -` read an EMPTY program - valid Python -
did nothing, exited 0, and the hook exited 0 with COMPLETELY EMPTY STDERR. Zero bytes rather than
truncation is what made it fail OPEN; a truncated program would have raised a SyntaxError and failed
loudly. Measured: 4051 delivered bytes arrive intact, 4097 arrive as zero. `bfa64e7`, THE COMMIT THAT
CLOSED CS-702, is what crossed the threshold.
THE SEVERITY WAS OVERSTATED WHEN FIRST REPORTED AND THE CORRECTION IS THE RECORD. It is MSYS2-only.
`tier1` run `32601774702`, at `32a982c` with the 4181-byte body, ran on `ubuntu-latest` where
`/bin/sh` IS dash, and 23 commit-msg tests with ZERO skip markers passed every violation class.
CS-702 IS AND WAS ENFORCED ON UBUNTU CI. On this machine `/bin/sh` is bash, so git never invoked the
affected dash here either. The defect was LATENT, and it was closed on the principle rather than the
blast radius: a gate that can exit 0 with empty stderr is unacceptable however few shells reach it.
THE COST IS REAL AND IS ACCEPTED RATHER THAN HIDDEN. On an affected shell the hook now refuses EVERY
commit, including legitimate ones - measured, the legitimate class went from 0 to 1 under dash. The
sentinel makes the hook SAFE there, not USABLE. Under bash, stderr is byte-identical across all five
violation classes and the legitimate one, exit codes are unchanged, and stdout is empty in every case.
A CORRECTION TO THIS ITEM'S OWN GRANT ENTRY, recorded here because that file is append-only. The grant
says "CS-819 is filed OPEN in `ROADMAP.md`". IT NEVER WAS: it was filed and closed inside one session,
and `ROADMAP.md` holds OPEN work only, so no such line was ever written. The grant's scope, conditions
and reasoning are unaffected.
TWO REFINEMENTS FROM THE FINAL ADVERSARY, both measured, neither changing the fix. `python -` with an
empty PIPE exits 0 silently, which is the case the guard is built for; with `/dev/null` it HANGS
instead, because MSYS maps that to a character device. And bash ELIDES an empty heredoc entirely, so a
shell that delivered zero bytes by dropping the redirect would hand `python -` git's own stdin and the
outcome would be a hang rather than an exit 0. The guard fires correctly in the case that occurs; the
hang shapes belong to CS-816.
THE RUNNER-UP - moving the program into a file - was NOT chosen and stays unbuilt, for the reason the
grant records: an empty or boundary-truncated FILE exits 0 just as silently, so it removes a cause
without establishing the invariant. That exact shape is now filed as CS-823 against `pre-commit`,
which invokes a file today and has no proof of execution at all.
### 2026-08-22 - CS-819 - FROZEN-FILE GRANT WIDENED by the OPERATOR for `.githooks/commit-msg`, narrowed to one region by an adjudicator
Verification: this entry is the grant record CLAUDE.md section 6 requires BEFORE the edit, not a
completion record. It WIDENS the CS-703 grant recorded below on this same date and does not replace
it; that entry stays as the record of what was permitted first. NOTHING IS CLOSED BY THIS ENTRY.
CS-819 is filed OPEN in `ROADMAP.md` and CS-703 stays OPEN until its own closure record.
THE DEFECT. `.githooks/commit-msg` delivers its checking program to the interpreter as a heredoc.
That body is 4181 bytes. Under the MSYS2 build of dash a heredoc above 4096 DELIVERED bytes arrives
as ZERO bytes; `python -` then reads an EMPTY program, which is valid Python, does nothing and exits
0, and `exit $?` faithfully propagates that 0. The hook exits 0 with COMPLETELY EMPTY STDERR. Zero
bytes rather than truncation is what makes it fail OPEN - a truncated program would raise a
SyntaxError and fail loudly.
MEASURED THREE TIMES INDEPENDENTLY on the TRACKED hook. Under that dash the trailer check, the
non-ASCII check, the subject cap, the placeholder check and the empty-message check ALL exit 0; under
bash all five refuse correctly. Delivery bisect on the real body: 4051 delivered bytes arrive intact,
4097 arrive as zero, 4182 arrive as zero. Heredoc size by commit, read with `git show`: `9d24823`
2788, `ac6e151` 2788, `bfa64e7` 4181, `32a982c` 4181. So `bfa64e7` - THE COMMIT THAT CLOSED CS-702 -
is what crossed the threshold, and it did so silently.
THE SEVERITY WAS OVERSTATED WHEN FIRST REPORTED, AND THIS ENTRY RECORDS THE CORRECTION RATHER THAN
THE FIRST CLAIM. The first report said the exposure included a stock Ubuntu runner and most Linux
developers. THAT IS REFUTED BY THIS PROJECT'S OWN CI. The affected `dash` links `msys-2.0.dll`; the
zero-byte delivery is a property of MSYS2 fork emulation on the `openhere()` writer path, not of dash
generally. `tier1` run `32601774702`, at `32a982c` with the 4181-byte body, ran on `ubuntu-latest`
where `/bin/sh` IS dash, and `tests/test_commit_msg_gate.py` - 23 tests, ZERO skip or xfail markers,
driving REAL `git commit` through the hook - passed every violation class. CS-702 IS ENFORCED ON
UBUNTU CI AND THIS ENTRY DOES NOT CLAIM OTHERWISE. On this machine `/bin/sh` is bash, so git never
invokes the affected dash here either. The defect is LATENT rather than live.
THE GRANT STANDS ANYWAY, on the adjudicator's reasoning and the hook's own. A gate that can exit 0
with empty stderr is unacceptable regardless of how many shells trigger it today; the hook already
asserts exactly this principle for the INTERPRETER and never asserts it for the PROGRAM; and the body
grew 2788 to 4181 in a single commit and now sits 85 bytes over a real threshold.
SCOPE, ONE REGION, ADJUDICATOR'S WORDING. In `.githooks/commit-msg` ONLY, for CS-819 alone: initialise
a new shell variable before the heredoc invocation and wrap that invocation in a command substitution
assigning to it; insert exactly one sentinel write to stdout immediately before the program's final
successful exit; and replace the trailing `exit $?` with a status check followed by a sentinel check.
NO other line of the python program, NO other line of this hook, and NO line of `pre-commit` or
`pre-push` may change. Those two are NOT affected and were checked by reading rather than assumed:
`pre-commit` invokes a FILE and `pre-push` invokes a MODULE, so neither delivers a program by heredoc.
TEN CONDITIONS BIND THIS GRANT, and they are written here because this is their only tracked home.
ONE, this entry must not claim CS-702 is unenforced on Ubuntu CI or for Linux developers generally,
and must record the MSYS2 attribution and the green tier1 run. TWO, PLAIN ASSIGNMENT ONLY on the
capture - no `export`, `local` or `readonly` prefix, each of which MASKS `$?` to 0 in both bash and
dash and would silently restore the fail-open. THREE, the capture variable is initialised before
first use so `set -u` cannot fire. FOUR, the sentinel is 7-bit ASCII and carries NO TRAILING NEWLINE,
with the reason recorded beside it: Windows text mode turns a written newline into CR LF, and a
written CR LF into CR CR LF, which command substitution does not fully strip. FIVE, the comparison is
EXACT equality rather than containment. SIX, the failure message prints the observed stdout verbatim
and says the check did not run. SEVEN, the acceptance carries all six items the adjudicator listed,
with RED demonstrated first. EIGHT, the background-child stall is disclosed: command substitution
waits for EOF rather than for the child, so a program that spawns a process holding stdout would hang
the hook, measured at a bounded timeout returning 124. It is LATENT - the program spawns nothing.
NINE, `scripts/install_hooks.py` runs clean after the edit. TEN, this record precedes the edit.
THE RUNNER-UP WAS PROGRAM-IN-A-FILE and it lost for a reason worth keeping. Its best argument is
strong: `pre-commit` already invokes a file, so a file is the HOUSE PATTERN rather than a
restructure, and it removes heredoc-size sensitivity permanently. It lost because AN EMPTY OR
BOUNDARY-TRUNCATED FILE EXITS 0 JUST AS SILENTLY - it removes one CAUSE without establishing the
invariant, where the sentinel detects every cause including ones not yet imagined. The two are
complementary rather than competing: the sentinel stays even if delivery later moves to a file, and
file delivery is filed as its own low-priority item needing its own grant.
WHAT THE SENTINEL DOES NOT BUY, stated because a gate that overclaims is worse than none. It makes
the hook SAFE on an affected shell, not USABLE: on such a shell every commit is refused, including
legitimate ones. Given no realistic `/bin/sh` is affected, that is the accepted cost.
ONE PRE-EXISTING GAP WAS NOTICED AND IS DELIBERATELY NOT FIXED HERE. A message carrying NUL or other
control bytes below 0x20 is ACCEPTED, because the offender test is `b > 0x7E` only. Unrelated to
CS-819, filed separately, and explicitly outside this grant.
COMMON-MODE RISK. Every measurement here shares one toolchain, git 2.53.0.windows.3 on one msys
installation. The Ubuntu conclusion is inferred from a green CI log rather than from a Linux shell
anyone ran directly. Whether glibc dash delivers a heredoc above 4096 is INFERRED, not measured, and
is settled cheaply by one `dash -c` run in the tier1 job printing the delivered byte count.
### 2026-08-22 - CS-703 - FROZEN-FILE GRANT ISSUED by the OPERATOR for all THREE hooks, then GRANTED-WITH-CONDITIONS by an adjudicator
Verification: this entry is the grant record CLAUDE.md section 6 requires BEFORE the edit, not a
completion record. Nothing has been edited under it at the time of writing. The item it serves is
filed in `ROADMAP.md` as CS-703 with its detail in `docs/history_notes.md`; this entry does not
close it.
GRANTED BY THE OPERATOR, in direct answer to a question naming CS-703, the three files and the
measured blast radius, and then ROUTED THROUGH AN ADJUDICATOR that produced none of the work it
judged. The adjudicator returned GRANTED-WITH-CONDITIONS and independently re-derived every
measurement below in its own throwaway repositories rather than accepting them.
SCOPE: `.githooks/pre-commit`, `.githooks/commit-msg` and `.githooks/pre-push`, for CS-703 ALONE.
ALL THREE ARE IN SCOPE TOGETHER BY CONSTRUCTION - the defect is a byte-identical `cs_probe` in
each, and a probe repaired in two of three is green in exactly the way this defect was green.
TWO PARTS, and nothing else in any of the three files may be touched. PART 1 replaces `cs_probe`
so it judges the candidate's OUTPUT rather than only its exit code. PART 2 makes a set-but-failing
`CLOCKSPEED_PYTHON` call the existing failure helper instead of falling through to the next rung.
The four-rung ladder ORDER is NOT touched and stays as the 2026-08-15 entry in this file settled
it: the hooks name `py -3` correctly, as the documented last resort. The acceptance tests land
under `tests/`, which is not frozen and is not part of this grant.
NO OTHER FROZEN PATH IS COVERED. `scripts/install_hooks.py`, `tools/precommit_gate.py`,
`.claude/settings.json` and `LICENSE` are NOT in this grant, and each would need its own.
THE DEFECT, MEASURED TWICE INDEPENDENTLY with git 2.53.0.windows.3, one wired hook per throwaway
repository so a block is attributable. Control with `CLOCKSPEED_PYTHON` unset: pre-commit exits 1
with HEAD unchanged on a staged em dash; commit-msg exits 1 with HEAD unchanged and the trailer
check fires by name; pre-push exits 1 because a deliberately failing test really runs, and the ref
never reaches the remote. With `CLOCKSPEED_PYTHON=true`: ALL THREE exit 0. The pre-commit commit
lands carrying the em dash bytes. The commit-msg commit lands and `git log -1
--format=%(trailers:key=Co-authored-by)` reads the trailer back as a REAL trailer, so CS-702 is
disarmed by an environment variable. The pre-push ref LANDS on the remote with the suite never run.
NINE CONDITIONS ARE THE ADJUDICATOR'S AND BIND THIS GRANT. They are written here because this is
their only tracked home; the 2026-08-15 ruling against restating a condition applies to conditions
that already have an owner file, and these have none.
ONE, the change ships a test driving a REAL `git commit` with the interpreter substituted, asserting
a non-zero exit AND that HEAD did not move, demonstrated RED against the current hooks first.
TWO, that end to end assertion exists for ALL THREE hooks; agreement between byte-identical copies
is not evidence.
THREE, the probe's captured-output variable is initialised before first use, so `set -u` cannot fire
on the failure path.
FOUR, the PART 2 failure message prints the OBSERVED probe output verbatim and states that
`CLOCKSPEED_PYTHON` must name ONE EXECUTABLE, not a command line with arguments.
FIVE, the probe program writes its token with NO trailing newline, with the reason recorded beside it.
SIX, PART 2 EXCEEDS THE ACCEPTANCE AS FILED and this entry says so plainly rather than quietly
widening it. The filed acceptance is satisfied by PART 1 alone. PART 2 is an OPERATOR INSTRUCTION,
chosen in direct answer to a question that named both alternatives.
SEVEN, `scripts/install_hooks.py` runs clean after the edit, which is the LF-only and no-BOM check.
EIGHT, this grant is recorded here before the edit is made.
NINE, `docs/GATED.md` is updated when CS-703 closes: it currently lists a substituted interpreter as
a live member of the class no client-side gate covers, and says that member sits ABOVE the edit line
the CS-702 grant drew. This grant is what draws the new line.
WHY THE RUNNER-UP LOST, recorded because it is the better argument than it looks. PART 1 ALONE
satisfies the filed acceptance and the adjudicator MEASURED that it does: with the repaired probe
and the old fall-through, `CLOCKSPEED_PYTHON=true` fails the probe, the ladder falls to real
`python`, and the em dash is blocked. Its cost is that a CLEAN file then COMMITS, exit 0, under an
interpreter the operator pinned, was silently overruled on, and was never told about. That is the
CS-806 shape surviving in a quieter form, and `BOOTSTRAP.md` section 2.5 names exactly it. PART 2's
cost is a loud message; the fall-through's cost is silence.
A CORRECTION TO `docs/history_notes.md` UNDER **CS-703 - detail**, per CLAUDE.md section 8, made by
measurement from two agents that ran it rather than read it. That block says the old probe passes
"`true`, `:` and `env`". `env` DOES NOT PASS on this toolchain - GNU `env` rejects `-c` and exits
125 - and `echo` DOES pass and is not named. The item is unaffected: `true` and `:` both pass, and
`true` is precisely the argument-ignoring program the acceptance names. The detail block is
corrected in place there rather than here, because it is not append-only.
THE BLAST RADIUS OF THE FIX IS EXACTLY THESE THREE FILES, and the blast radius of the DEFECT CLASS
is wider by one. Checked by grep rather than by reasoning: `scripts/verify_env.py`,
`scripts/install_hooks.py`, `tools/precommit_gate.py`, `tools/edit_lint_check.py`,
`tools/pretooluse_gate.py`, `tools/facts_probe.py`, `tools/drift_guard.py`, `config/` and both CI
workflows are all CLEAN of this shape, and no CI job or tracked doc sets `CLOCKSPEED_PYTHON` at all.
`.claude/settings.json` IS A FOURTH SITE OF THE CLASS: it hardcodes its interpreter with no ladder
and no probe, and a missing or substituted one yields a status its own protocol treats as
non-blocking, so it fails OPEN. It is MILDER because CLAUDE.md section 2.2 makes the Claude hooks a
convenience layer and `.githooks` authoritative, and it is NOT FIXABLE HERE because JSON cannot
express a probe. It is filed as its own item and needs its own grant.
FIVE RESIDUALS ARE DISCLOSED RATHER THAN CLOSED, each filed as its own item. The probe asserts
PYTHONHOOD, NOT TOOLCHAIN, so `py -3` passes it and still has no pytest, which is the
`BOOTSTRAP.md` section 2.5 trap arriving at a different door. `PYTHONINSPECT=1` HANGS BOTH THE OLD
AND THE NEW PROBE, measured at a bounded six seconds returning 124 WITH stdin already at
`/dev/null`, so closing stdin does not close it and neither probe is timeout-bounded.
`scripts/verify_env.py` never evaluates `CLOCKSPEED_PYTHON`, so a green environment check does not
predict which interpreter the hooks will resolve. Three FALSE-REFUSAL modes are accepted
deliberately - a `sitecustomize` printing to stdout, a `.cmd` shim without `@echo off`, and
`PYTHONIOENCODING=utf-8-sig` - because the alternative, containment instead of exact equality,
trades a LOUD false refusal for a SILENT false accept, which is the wrong trade in a gate. And a
purpose-built forger that simply prints the token passes, which no probe can prevent and which the
hook comment must state rather than imply otherwise.
THE COMMON-MODE RISK IS RECORDED. All three probes and both independent re-derivations share ONE
toolchain, git 2.53.0.windows.3 on one msys bash. `CONVENTIONS.md` section 16 says hook findings are
version-specific and expire; re-measure rather than inherit.
### 2026-08-22 - CS-702 - CLOSED: a co-authorship trailer is BLOCKED end to end, and the gate's predicate is git's own rather than a list of agent names
Verification: `.githooks/commit-msg` carries the check;
`tests/test_commit_msg_gate.py::test_a_co_authorship_trailer_is_blocked_and_head_is_unchanged` is the
acceptance arm and it drives a REAL `git commit` in a throwaway repository, asserting the exit code and
that HEAD did not move - a hook's presence is never proof it fires, so nothing here asserts the file
exists. `tests/test_commit_msg_gate.py::test_the_rejection_is_issued_by_this_hook_and_not_by_git`
separates the two possible authors of a refusal, and
`tests/test_commit_msg_gate.py::test_the_attribution_property_can_tell_the_hooks_rules_apart` is its
control. Reproduce with `python -m pytest tests/test_commit_msg_gate.py -q`.
THE PREDICATE IS NAME-FREE AND THAT IS THE WHOLE DESIGN. It compares the token before the first colon,
right-trimmed and lowercased, against the trailer key, and only on a line at column zero. Two properties
follow and both are measured:
`tests/test_commit_msg_gate.py::test_whitespace_before_the_colon_is_still_a_trailer_and_is_blocked`
covers the shape git NORMALISES and a prefix match MISSES, and
`tests/test_commit_msg_gate.py::test_an_indented_line_is_accepted_because_git_reads_no_trailer_there`
covers the shape git does NOT read as a trailer at all. The rule implemented is "block what git would
recognise", with git as the oracle rather than this project's model of git.
THE POLARITY IS WIDER THAN THE OPERATOR DECISION IN `docs/GATED.md` AND THAT WAS ADJUDICATED, not
assumed: the rule rejects EVERY co-authorship trailer rather than only one naming an agent, because
"naming an agent" is not mechanically decidable and any name list fails OPEN on the next harness rename
- which is precisely how the rule failed the first time. Cost measured on this date: zero.
THREE BUILDS, TWO REFUTED, AND THE THIRD BUILT AND DELIBERATELY NOT SHIPPED. Build one missed a trailer
git normalises and blocked indented and fenced examples git never reads as trailers. Build two - what
ships - fixed both by aligning with git's parser. **A FENCE IS NOT A SHIELD** and the measurement is
worth carrying: a fenced block containing a co-authorship line IS parsed by git as a trailer whenever a
git-generated trailer shares the block, because git's quarter-of-the-block rule trips and it reads the
block whole, fence lines and all. So the cheap fix of skipping fenced blocks would have failed OPEN.
Indentation is the reliable shield; a column-0 fenced example is BLOCKED and that is deliberate. Build
three rewrote the inherited pre-filter under a widened grant, closed four escapes, and was REFUTED
anyway; it is recorded in `docs/GATED.md` and filed as CS-813 rather than shipped.
WHAT THIS ITEM DOES NOT CLAIM, stated because a gate that overclaims is worse than one that does not
exist. It does not claim the class of routes that never runs this hook - `git commit --no-verify`,
`git cherry-pick`, `git revert`, `git rebase` on either backend, `git am`, and an unbootstrapped clone -
which is CS-704. It does not claim the pre-filter class, which is CS-813. It does not claim the
interpreter ladder, which accepts any program that exits 0 and is CS-703. It does not clean the
historical commits that carry the trailer; the flip precondition in `docs/GATED.md` covers those by
generating a fresh history. Every one of those is named in that file rather than left for a reader to
discover.

### 2026-08-22 - CS-813 - CORRECTION to this session's widened-grant record: the stored subject measured 200 characters, not 215
Verification: reproduce by committing a message whose first line is `# ` followed by 198 characters with
`git commit -F` against the hook as it stood at `ac6e151`; `git log -1 --format=%s | wc -c` reports the
stored subject. Two independent agents measured 200 from a 200-character input line.
THE WIDENED-GRANT ENTRY IN THIS FILE SAYS "a 215-character STORED subject" AND THAT NUMBER IS WRONG. It
was carried from an adjudicator's report into a tracked file by the merger without being re-measured,
which is the exact failure this repository has a rule against - a measured number restated in prose
drifts, and this one drifted on its first restatement. This file is append-only, so the wrong number
stays where it was written and this record corrects it.
NOTHING ELSE IN THAT ENTRY IS AFFECTED. The escape it describes is real and reproduces exactly; only the
magnitude was wrong, and the escape does not depend on the magnitude. CS-813 stays OPEN and this entry
does not close it.

### 2026-08-22 - CS-702, CS-813 - FROZEN-FILE GRANT WIDENED by the OPERATOR for `.githooks/commit-msg`, narrowed eleven ways by an adjudicator
Verification: this entry is the grant record CLAUDE.md section 6 requires BEFORE the edit, not a
completion record. Nothing has been edited under it at the time of writing. It WIDENS the grant
recorded below on this same date and does not replace it; that entry stays as the record of what
was permitted first. NOTHING IS CLOSED BY THIS ENTRY: CS-702 STAYS OPEN, and CS-813 STAYS OPEN.
Both are filed in `ROADMAP.md` and this entry does not close either of them.
GRANTED BY THE OPERATOR in direct answer to a question naming the pre-filter and two measured
escapes, then routed through an adjudicator that produced none of the work it judged. The verdict
was GRANTED-WITH-NARROWING.
WHY IT WAS NEEDED. The gate shipped under the first grant was REFUTED by an adversary and the
escapes were reproduced independently with real commits and clean controls. THE CAUSE IS THE
PRE-FILTER, which is pre-existing code building the `body` variable - below the interpreter ladder
but above the granted insertion. It drops every line beginning with a comment character and breaks
out at any comment line containing the scissors token, UNCONDITIONALLY, regardless of the cleanup
mode git will actually apply.
THE ROOT FACT, measured by the adjudicator and stronger than the report that prompted it: CLEANUP
RUNS AFTER THIS HOOK. On the editor path the hook sees the full template while the stored message
has it stripped, so every check here PREDICTS the stored bytes and never observes them. A
pre-filter can be made conservative; it cannot be made complete.
THREE ESCAPES, NOT TWO. The third was found by the adjudicator and is named nowhere else: the
72-character subject cap. A 200-character comment line as the first line becomes a 215-character
STORED subject with the hook exiting 0 and HEAD moving. Same cause, same fix. The other two are
the trailer fail-open, where git itself reads the trailer on a message the gate passed, and the
7-bit ASCII fail-open, which is not a CS-702 defect at all but a pre-existing hole in the
enforcement of non-negotiable 4, inside a hook that exists to enforce it.
SCOPE: `.githooks/commit-msg`, ONE further edit - replace the pre-filter block, re-point the four
downstream checks at the body each one actually needs, and edit the single dispatcher line only if
a new observable is passed in from sh. NOTHING AT OR ABOVE THE LINE CLOSING THE FOUR-RUNG LADDER,
and nothing in the tail. The acceptance suite is not frozen and is not part of this grant. NO
OTHER FROZEN PATH IS COVERED - in particular `.githooks/pre-commit` and `.githooks/pre-push` carry
the byte-identical interpreter ladder whose own defect is filed as CS-703, and that is NOT this
grant.
THE ELEVEN NARROWINGS ARE THE ADJUDICATOR'S AND BIND THIS GRANT. The load-bearing ones: the
DEFAULT DIRECTION IS TO CHECK MORE, and a line may be skipped only when the hook can PROVE from an
observable that git will discard it; the unconditional break on the scissors token GOES, because
`strip` - which IS the default when an editor is used - does not truncate below that marker
either, so today's break is wrong on the ordinary editor path too; `commit.cleanup` MUST be read,
since `whitespace` and `verbatim` force the raw path even under an editor; and the comment
character is configurable, so it is read or it is recorded as a named residual with a pinning
test, but not left unread and unrecorded.
ONE PRIOR NARROWING IS VACATED AND THE REVERSAL IS RECORDED HERE RATHER THAN LEFT IMPLICIT. The
first grant required the check read the COMMENT-STRIPPED body. That is vacated FOR THE TRAILER
CHECK ALONE, which now reads the raw buffer. Its stated justification - that git discards a
scissors-cut section and a commented line before the message exists - was MEASURED FALSE on the
`-F` and `-m` paths, and CLAUDE.md section 8 rules that ground truth beats every document. The
empty-message check KEEPS the comment-stripped body, so an abandoned editor commit still reports
itself empty rather than complaining about git's own template. Measured false-positive cost of the
reversal: the trailer predicate over a real verbose buffer scores ZERO hits, and zero of the 187
commits then on `main` carry a comment-prefixed body line.
TWO SUITE ARMS CHANGE AND BOTH ARE NAMED HERE BECAUSE ONE OF THEM IS THE DEFECT'S FINGERPRINT
INSIDE THE GUARD. The commented-trailer arm SURVIVES unchanged. The arm asserting that a trailer
below a scissors marker does not block the commit MUST INVERT - it currently pins escape one as
intended behaviour, which is why 78 green tests coexisted with three live fail-opens. Every arm
drives one commit path today, and each gains an editor-path twin.
THE COMMON-MODE RISK IS RECORDED because the fix and its guard share it: one git binary, one
locale, and a `core.hooksPath` that is machine-local and never cloned, so every arm proves a
wiring a fresh clone does not have.
A SHAPE WHERE HOOK AND GIT CANNOT AGREE IS ADMITTED RATHER THAN PAPERED OVER. Because cleanup runs
after the hook, the prediction's inputs include flags no hook can observe; an editor invoked with
an explicit cleanup override is the concrete case. It is a named residual, and the class closes
only where the stored message is a fact rather than a prediction - the range scan already filed as
CS-704.

### 2026-08-22 - CS-810 - CLOSED: a citation written as a bare `::name` is judged in EVERY guarded doc, and a second site for an already-forgiven name is no longer silently forgiven
Verification: `tests/test_docs_citations.py::test_every_bare_identifier_in_a_guarded_doc_resolves` is the arm, now
parametrized over the guarded set rather than hardcoded to this file, and
`tests/test_docs_citations.py::test_the_bare_arm_has_teeth_on_every_guarded_doc` is its per-doc non-vacuity control.
Reproduce the acceptance by planting a `::name` naming nothing into any guarded doc and running
`python -m pytest tests/test_docs_citations.py -q`; it goes red. The module ran 26 tests at `f938062` and runs 71 here.
THE ITEM WAS FILED AT ONE LIVE INSTANCE AND THE POPULATION IS 48. `docs/LEDGER.md` spends 47 real names in the
elided form plus one metasyntactic placeholder, because the elision is this file's ORDINARY IDIOM - a full citation,
then `::name` for further tests in the same file. 43 of those names were elided-only and invisible to every arm.
A RESOLVER THAT INHERITS THE LAST FULL CITATION SEEN WAS BUILT, MEASURED AND REJECTED: it manufactures 14 false
findings, because this file interleaves an unrelated full citation mid-paragraph and the elisions after it still mean
the earlier file. The shipped arm never recovers a path; it asks only whether any module binds the name.
FIRST BUILD WAS REFUTED, and the refutation is the useful record. The arm had exactly ONE live caller, hardcoded to
this file, so a `::name` naming nothing planted in `ROADMAP.md` or in `docs/GATED.md` left the module green - two of
the three guarded docs. Separately, `DISPOSITIONS` was keyed by name with no multiplicity, so a NEW entry citing an
already-forgiven name was accepted in silence; three such plants were green. Both are closed here:
`tests/test_docs_citations.py::test_every_recorded_disposition_covers_exactly_the_sites_it_records` pins the
occurrence count per entry, and `tests/test_docs_citations.py::test_a_second_site_for_a_forgiven_citation_is_reported`
is its control. Counts are pinned rather than line numbers, which churn.
THE DELIBERATE DISPOSITION SURVIVED AND WAS REQUIRED TO. A citation can assert an ABSENCE - the CS-411 correction
record cites a dead name to prove it is dead, and `grep -c` returning 0 IS its evidence. One new entry was needed,
for the sibling name that is spelled ONLY in the elided form and that no arm had ever seen.
RESIDUAL, disclosed rather than rounded off: the arms still return empty for an extra site and only the contract test
reddens, so a direct importer that reads an arm's empty return as "no dead citations" gets a false clean. No such
importer exists today - this module is imported by nothing - so the exposure is latent. Filed as CS-812.

### 2026-08-22 - CS-809 - CLOSED: the deep archive is now the ONLY doc left unguarded, and that cardinality is itself checked
Verification: `tests/test_docs_citations.py::test_every_markdown_file_carrying_a_citation_is_guarded_or_recorded_unguarded`
is the boundary and it is checked in BOTH directions - an unanswered carrier fails, and so does a record for a doc
that is now guarded, is untracked, or has stopped carrying citations.
`tests/test_docs_citations.py::test_the_deep_archive_is_the_only_doc_left_unguarded` is the cardinality pin this
item's acceptance names. Reproduce by adding one line naming a tracked test module to any unguarded markdown file and
running `python -m pytest tests/test_docs_citations.py -q`.
THE ACCEPTANCE CLAUSE WAS LITERALLY TRUE ONLY AFTER A SECOND FILE WAS GUARDED. The clause asks for a check that the
archive stays "the only one", and it never was: `WAKEUP_NOTES.md` also carried a citation nothing looked at. The first
build recorded BOTH files as unguarded and stated, in its own exemption table, that every citation in the second one
resolved. THAT WAS MEASURABLY FALSE - it carries a dead bare name, and this module's own table already recorded that
name as dead under another key. An exemption table nothing verifies is how a false declaration ships, and one shipped
on its first run. The repair guards `WAKEUP_NOTES.md` instead, at a cost of exactly one disposition, which leaves the
unguarded set at a single member and makes the clause true as written rather than needing an amendment.
THE ARCHIVE STAYS UNGUARDED ON ITS RECORDED REASON, which is unchanged: its detail blocks QUOTE dead names while
discussing them, so quoting and citing are indistinguishable by shape there, and a guard over it would be red on
correct history. It still carries 4 dead full citations and 2 dead bare names; this item adds none and removes none,
measured set-identical against `f938062` with the same code on both sides.
WIDENING THE CARRIER PREDICATE FOUND A DOC NOBODY HAD EVER LOOKED AT - `docs/adr/0008-detection-claims-are-derived-never-written.md`
- which measured clean on all three arms and is now guarded rather than recorded.
RESIDUALS, disclosed: carrier-hood is decided by SHAPE rather than by whether an arm would report anything, so any
doc that merely names a tracked test module becomes a carrier and must be answered - 31 currently-clean tracked docs
are one command line away from it. And the pattern-derivation check is a CONVENTION rather than a mechanism: five
measured ways of adding a judging pattern escape its walk. Filed as CS-811.

### 2026-08-22 - CS-702 - FROZEN-FILE GRANT ISSUED by the OPERATOR for `.githooks/commit-msg`, then NARROWED by an adjudicator
Verification: this entry is the grant record CLAUDE.md section 6 requires BEFORE the edit, not a
completion record. Nothing has been edited under it at the time of writing. The item it serves is
filed in `ROADMAP.md` as CS-702; this entry does not close it.
GRANTED BY THE OPERATOR, in direct answer to a question naming CS-702 and this file, and then
ROUTED THROUGH AN ADJUDICATOR that produced none of the work it judged - the section 6 route in
full, rather than the direct-issue route every prior grant in this file took. The adjudicator
returned GRANTED-WITH-NARROWING.
SCOPE: `.githooks/commit-msg`, for CS-702 ALONE. ONE insertion - a constant, a loop, and a single
call to the existing failure helper - placed after the placeholder-subject check and before the
final exit, inside the heredoc that is already there. Nothing above the interpreter ladder may be
touched: the shebang, the header comment, the shell options, the early failure helper, the
message-file guard, the probe and dispatcher helpers, the four-rung ladder and its fail-closed
else branch are all OUT of scope, as is the tail. No reordering, no renaming, no helper
extraction, no reflow of an existing line. The acceptance test lands under `tests/`, which is not
frozen and is not part of this grant.
NO OTHER FROZEN PATH IS COVERED. `.githooks/pre-commit`, `.githooks/pre-push`,
`scripts/install_hooks.py`, `tools/precommit_gate.py`, `.claude/settings.json` and `LICENSE` are
NOT in this grant, and each would need its own.
CONDITIONS ARE THE ONES ALREADY WRITTEN IN CS-702'S ROADMAP ENTRY and are deliberately NOT
restated here, per the ruling recorded in the 2026-08-15 grant entry below: restating a condition
is how a condition drifts.
FOUR CONDITIONS ARE ADDED BY THE ADJUDICATOR, because they bind this grant rather than any clause
already written. FIRST, THE PREDICATE IS NAME-FREE - it rejects the trailer SHAPE and carries no
list of agent names, because a name list fails OPEN on the next harness or model rename, which is
exactly the continuous pressure CS-702 was filed against. SECOND, it reads the COMMENT-STRIPPED
message body rather than the raw bytes, so a scissors-cut verbose diff and a commented-out line
stay out of scope - both were measured to be discarded by git before the message exists. THIRD,
no edit sits above the interpreter ladder. FOURTH, LF-only line endings are ASSERTED after the
edit rather than assumed - the harness edit path converts a tracked file to CRLF while git
normalises the blob so the working tree still reports clean, and msys bash runs a CRLF hook
correctly on this toolchain, so the breakage is invisible here and surfaces on another shell.
THE POLARITY IS WIDER THAN THE RECORDED OPERATOR DECISION, AND THAT IS DELIBERATE. `docs/GATED.md`
records the rule as no commit carrying a co-authorship trailer that names an agent; this gate
rejects EVERY co-authorship trailer, name-free, on the fail-closed criterion and on the CS-209
precedent that narrowing a blocklist by default to pre-empt a collision was DENIED BY MEASUREMENT.
Cost measured on this date is ZERO - every one of the eighteen trailer-bearing commits then on
`main` names an agent, and no human co-author trailer existed anywhere in the history. A future
genuine human co-author is BLOCKED, which is the intended failure direction; the route is then a
new item and a recorded allowlist entry, never a shortened matcher. THIS IS THE ONE PART OF THE
VERDICT MOST WORTH OVERRULING, and it is recorded here so that the operator can.
TWO BYPASSES ARE OUT OF REACH OF THIS GRANT AND ARE NOT CLAIMED CLOSED. Measured in a throwaway
repository this session: `git commit --no-verify` does not fire this hook, and `git cherry-pick`
does not fire it either, so a replay of the historical commits would re-inject every trailer with
the gate silent. Closing those needs a range scan in `.githooks/pre-push`, or a check on the CI
side - a separate frozen file and a separate grant.
THE COMMON-MODE RISK IS RECORDED because both halves of the work inherit it: the hook's invocation
path is machine-local git configuration that is never cloned, and a unit test of the matcher is
byte-identical green whether the gate fires or not. That is why CS-702's acceptance names an end
to end transcript rather than a file, and why this grant is conditional on that transcript.

### 2026-08-22 - CS-442 - CLOSED, and a CORRECTION to five earlier entries: `docs/` is read by a guard for the first time, and the dead pointers it found are corrected here rather than in the entries that carry them
Verification: `tests/test_docs_citations.py`, which is the first thing in this repository to read
`docs/` at all. The control the acceptance asks for is
`tests/test_docs_citations.py::test_the_checker_fires_on_a_planted_dead_pointer`, with the opposite
branch pinned beside it by `test_the_checker_passes_the_same_pointer_once_it_resolves` so it cannot
pass by always reporting. To reproduce the finding rather than trust it: set `DISPOSITIONS` to `{}`
and run the module - the ledger yields SEVEN dead `path::name` citations and THREE dead bare
identifiers, and `ROADMAP.md` and `docs/GATED.md` yield none.

**THE STRUCTURAL FACT, which is the item and is sharper than the typo it was filed on: NOTHING IN
THIS REPOSITORY READ `docs/`.** `tests/save/test_oracle_citations` scans `clockspeed/`,
`tests/save/test_absolute_claims` scans `tests/`, and neither looked at `docs/`. So the Verification
pointer - the one field this file declares MANDATORY, and the entire reason it is trustworthy - was
the least guarded prose in the project. It is now guarded in `docs/LEDGER.md`, `ROADMAP.md` and
`docs/GATED.md`.

**THE POPULATION WAS RE-DERIVED, NOT INHERITED, AND IT IS EIGHT RATHER THAN THE RECORDED SEVEN.**
The seven previously recorded all reproduce. The eighth is
`test_the_header_scan_advertises_no_bound_it_cannot_enforce`, cited by the CS-436 entry, and it is
invisible to a `path::name` scanner because it is spent BARE, with no path attached. The CS-442
detail block predicted exactly this - it called the bare shape "the single most important shape to
cover" and left it UNMEASURED - so the floor caveat it attached to its own figure was correct and
is now discharged.

**A NINTH CANDIDATE WAS REJECTED ON INSPECTION, and it is recorded because the next census will
meet it again.** `clockspeed/save/objects.py::_BYTE_ORDER_CANNOT_SEPARATE_VALUES` reads dead to any
resolver that looks for `def` alone. It is a live module-level CONSTANT at `objects.py:3017`. That
is the same artifact class the detail block already warns about on the `file:line` arm, arriving on
the `path::name` arm instead, and `test_a_citation_naming_a_module_level_constant_resolves` is what
keeps it rejected.

**THE CORRECTIONS. This file is append-only, so the four entries that were WRONG WHEN WRITTEN are
corrected HERE and are not edited where they sit.** The live precedent for getting that wrong is
`4b2d04c`, which corrected a collision by editing the entry that made it while claiming in the
inserted text that it had not.

| Entry | Cited, and never in any commit | Read it as |
|---|---|---|
| CS-420 | `tests/save/test_absolute_claims.py::test_the_scanned_prose_carries_no_unbacked_absolute_claim` | `tests/save/test_absolute_claims.py::test_the_fenced_prose_carries_no_unbacked_absolute_claim` |
| CS-454 | `tests/save/test_workdir.py::test_the_refusal_message_carries_no_non_digit_account_directory` | `tests/save/test_workdir.py::test_the_refusal_message_carries_no_raw_account_directory_of_a_non_digit_shape` |
| the registry entry | `tests/data/test_registry.py::test_the_misspelled_keys_are_used_verbatim_not_autocorrected` | `tests/data/test_registry.py::test_the_misspelled_game_keys_are_used_verbatim_not_autocorrected` |
| CS-436 | `test_the_header_scan_advertises_no_bound_it_cannot_enforce`, bare | `tests/test_precommit_gate.py::test_the_header_scan_time_bound_declares_the_scope_it_actually_has` |

Each was confirmed by `git log -S"def <name>(" -- "*.py"` returning NOTHING, against a control on a
live name that returns a commit - the probe is worthless without that control. The CS-436 target is
not an inference: it was added by `ee36d0d`, the CS-436 commit itself, alongside the live sibling
the same Verification field cites.

**THE ONE THAT GETS NO TARGET, and this is a judgement rather than a lookup.** The CS-433 entry
cites `tests/save/test_properties.py::test_the_reach_guard_catches_every_spliced_shape`. No such
name is in history, and NO LIVE TEST IS ASSIGNED TO IT, because the claim the name encodes is
measurably false: the CS-441 entry in this file records 26 of 46 spliced shapes still escaping, and
CS-441 is still OPEN. Assigning a target would launder an aspirational sentence into a verified
pointer, which is the exact defect this item exists to remove. The live gating evidence for CS-433
is the retention checker's own mutation controls, which that entry also names and which resolve.

**THE STATED RULE THE ACCEPTANCE ASKS FOR, for a citation whose file moved under it.** A dead
citation is not one thing, and the four dispositions are recorded in `DISPOSITIONS` and
machine-checked rather than believed: MOVED - the record was right when written and the tree moved
the name, which is NOT a record defect and needs no ledger change; RENAMED - wrong when written with
one unambiguous live target, which needs a correcting record like this one; NO_TARGET - wrong when
written with no target assignable; and DELIBERATE - the citation asserts an ABSENCE, which a
correction record does on purpose.

**THE FOURTH DISPOSITION IS NOT A CONVENIENCE, IT IS A DEFECT THIS ITEM NEARLY SHIPPED.** The
CS-411 correction record's Verification field cites a dead name deliberately - `grep -c` returning 0
IS its evidence - so a checker that reddens on every dead bare name reddens on a record doing
precisely the right thing. That trap was not previously recorded anywhere.

**THE TABLE CANNOT ACCUMULATE FALSE DECLARATIONS, which is the CS-807 lesson applied before it is
earned rather than after.** Every entry is checked in BOTH directions:
`test_every_recorded_disposition_is_still_in_use` fails on an entry whose citation has gone or which
now resolves on its own, and `test_every_correctable_disposition_names_a_target_and_the_others_do_not`
fails on a MOVED or RENAMED entry that names no target. An exemption nothing verifies is how a false
declaration ships.

**TWO ARTIFACT CLASSES ARE DECLINED RATHER THAN JUDGED, and each is printed rather than passed in
silence.** An unqualified bare basename - `registry.py:206`, `verify_env.py:358` - has no directory
to resolve against, and resolving one repo-relative and calling it missing is how an earlier census
manufactured six findings that were all artifacts. A `file:line` pointer into THIS file rots by
construction, because prepending an entry shifts every line number below it. The `file:line` arm
judges RANGE only: asserting what sits AT a line would redden on every edit above it, and that
limit is stated rather than left to be discovered. Measured today: 22 pointers, 20 judged and in
range, 2 declined, 0 broken.

**ADVERSARIAL PASS.** Ten mutants, each asserting it applied before its run: the citation arm, the
resolver, the `file:line` arm and the bare arm each neutered in turn; the ledger left unscoped so the
preamble's illustrative pointers are judged; the two declined classes forced into judgement; the
constant-and-class widening removed; the table made to forgive everything; and the redirect
verification disabled. NINE were caught immediately. THE TENTH SURVIVED and is the reason four more
controls exist: verifying a MOVED target only fires when a target STOPS resolving, which never
happens on the live table, so it was a guard on a non-default path and would have shipped untested.
The table is injectable now so a control can reach it. Second run: TEN of ten caught, no survivors.

**DISCLOSED RESIDUALS, filed rather than implied:** CS-809, `docs/history_notes.md` is excluded and
carries dead citations of its own; CS-810, a citation written as bare `::name` with no path is
invisible to both arms.

### 2026-08-22 - CS-806 - `scripts/verify_env.py` now judges the toolchain by the RESOLVED interpreter rather than by PATH, and HARD-fails when the two diverge
Verification: `tests/test_verify_env.py::test_a_tool_the_resolved_interpreter_cannot_import_is_reported_missing`
is the control, with four siblings in the same block. END TO END ON THIS MACHINE, which is the
half a unit test cannot show: `python scripts/verify_env.py` exits 0 and `py -3 scripts/verify_env.py`
exits 1 naming pytest and ruff. Against the PRE-CHANGE blob at `b26c0b6` the same `py -3`
invocation printed `VERDICT: PASS - every HARD dependency is present` and exited 0, which is the
defect itself and was captured before the change was written.

**WHAT WAS ACTUALLY WRONG, and it is not the one the item was filed on.** CS-806 was filed as a
docs defect - the tier-0 lint command spelled `py -3 -m ruff check` and exits 1 as written. The
docs were half of it. The other half is that `BOOTSTRAP.md` section 2.5 has carried a MANDATORY
consequence since the FIRST COMMIT (`9d24823`): verify_env "must assert that the RESOLVED
interpreter can import pytest and ruff, and must HARD-fail if it cannot. Reporting the version
alone is not sufficient and would have passed this machine while the pre-push suite was
unrunnable." **That requirement was never implemented.** So this closes an unimplemented spec
clause, not a design question.

**THE ITEM'S OWN DETAIL BLOCK IS SUPERSEDED ON ONE POINT and this record is the correction.**
`docs/history_notes.md` under **CS-806 - detail** says verify_env "DOES NOT CATCH IT AND IS NOT
WRONG TO MISS IT", probing by name "correctly by its own contract", and asks whoever closes the
item to "decide whether that contract is the right one". The contract had already been decided,
in `BOOTSTRAP.md` section 2.5, before the code was written. It was not a live question.

**THE MECHANISM.** `_tool_version` probed PATH FIRST and only fell back to the module channel,
so a `Scripts` directory belonging to a DIFFERENT interpreter satisfied a HARD row. Both installs
report the same version, so the version check passed while the toolchain was unreachable.
`_module_backed_tool_row` now runs the module probe FIRST - the way every gate in this project
invokes these tools - and reads PATH only to tell the operator WHICH failure they have, because
"install ruff" and "you are on the wrong interpreter" need different actions.

**SIBLING SWEPT AND FIXED:** `mypy`, SOFT, same root cause exactly - the tier-2 gate invokes it as
`-m mypy`. **DELIBERATELY EXCLUDED, each pinned by a test or examined and cleared:** `node` and
`gh` are genuine executables and are still judged by PATH, because applying the module rule to
them would report MISSING for a working install; `.githooks/pre-commit` and `pre-push` ALREADY
implement section 2.5's resolution order and pre-push already probes `import pytest` against the
resolved interpreter, so they are correct as written and needed no frozen-file grant;
`tools/precommit_gate.py::ruff_command` selects an INVOCATION rather than reporting availability,
prefers a standalone `ruff.exe` which runs under any interpreter, guards its module fallback with
a real `import ruff`, and reports a loud "lint was NOT run" note when neither exists - no defect,
and again no grant needed. **NO FROZEN FILE WAS TOUCHED.**

**THE ONE BEHAVIOUR CHANGE WITH A PLAUSIBLE FALSE-POSITIVE STORY, stated rather than discovered
later.** A machine with ruff installed ONLY as a standalone binary, not importable, now reports
MISSING where it previously reported FOUND. That is the correct answer for THIS project rather
than a regression: `docs/OPERATIONS.md`, the `/done` ritual, the tier-1 lane and the tier-2 lane
all invoke it as `python -m ruff`, so such a machine cannot run the gates it would be certifying.

**CI IS NOT REDDENED, CHECKED RATHER THAN ASSUMED.** `.github/workflows/tier2.yml` runs
`python scripts/verify_env.py` and requires exit 0, but installs `-e ".[dev]"` into the SAME
interpreter first, deliberately and with a comment saying why. mypy, pytest and ruff are all
`[dev]` extras, so all three are importable there.

**DOCS.** `docs/OPERATIONS.md` said "`py -3` is equivalent on this machine", which was FALSE and
contradicted `BOOTSTRAP.md` section 2.5; it now states the divergence and points at the check.
The eight `.claude/agents/*.md` and six `.claude/commands/*.md` files that instructed sessions to
invoke `py -3` - `/done` among them, which is how this was found - now say `python` and carry an
explicit NEVER fence. `.githooks/*` still name `py -3` and are LEFT ALONE: they name it correctly,
as the documented last resort after `$CLOCKSPEED_PYTHON`, `python` and `python3`. `BOOTSTRAP.md`,
`ROADMAP.md`, `WAKEUP_NOTES.md` and this file name it as a RECORD of the trap and are untouched.

**ADVERSARIAL PASS.** Four mutants, each asserting it applied before its run so a mutation that
never landed could not read as a survivor: PATH-first restored (the original defect), the two
MISSING reasons collapsed into one note, always-MISSING, and the module rule widened onto node and
gh. ALL FOUR CAUGHT, no survivors, against a green pristine floor. Full suite 2244 passed,
3 skipped, exit 0; `ruff check .` and `ruff format --check .` both exit 0; `mypy clockspeed`
clean; drift_guard 0; doc_budget 0.

### 2026-08-22 - CS-807, CS-808 - NOT A COMPLETION RECORD. NOTHING CLOSED. The sweep sized the item at SIX, and an attribute-half repair was built and REFUTED by three independent lenses
Verification: this entry is a POINTER. `ROADMAP.md` for CS-807's corrected acceptance and for
CS-808 as newly filed; `docs/history_notes.md` under **CS-807 - detail** for the sweep tables
and the refutation record. Commit `77336e5` is DOCUMENTATION ONLY and is the session's only
change to `main`. The refuted build is on branch `cs807-attribute-half` and is NOT merged.

**THE SWEEP WAS TAKEN, and it changed the item's size.** CS-807's detail block named it as the
cheapest next step and recorded the answer as unmeasured. The answer is SIX false declarations,
not four, in TWO modules rather than one: `backing_citations` and `dead_full_citations` in
`tests/save/test_absolute_claims.py` are the new pair, and both are HELPERS rather than tests.
The graded channel is clean. Two independent methods agree, and the second never reads a reason
string. Six is a FLOOR, not a total.

**THE ATTRIBUTE HALF WAS ATTEMPTED TWICE AND REFUTED BOTH TIMES, ON THE SAME ROOT CAUSE.** The
sweep showed the six split by mechanism: four on the bare-name arm already measured irreducible,
two on the ATTRIBUTE arm, where `_callee_resolves` discards a receiver the import table resolves
without any type resolution. That looked reducible and it was reported as such. It is not. Both
narrowings read an ABSENCE as evidence of safety - the first that the sibling exported no reach,
the second that a def's own body names no primitive - and each was refuted on a real escape.

**THE GRADING WAS DONE BY THREE AGENTS THAT DID NOT PRODUCE THE BUILD, on three lenses, and all
three returned REFUTED.** The permissive-failure lens found seven escapes, each caught on the
parent commit and silent on the build. The control-validity lens found that the build's
anti-vacuity control passes with `_assert_library_reach_is_declared` gutted to a bare `return`.
The claim-accuracy lens found the new `_module_handles` docstring stating the polarity of the
REFUTED first spike, and a FOURTH reach-computation site that manufactures a `<module scope>`
declaration on a module reaching nothing - the CS-807 defect itself, inside the CS-807 repair.

**WHAT SURVIVED GRADING.** The two exemption deletions are correct - the claim-accuracy lens
verified both call chains by reading rather than by running the guard - and no shipped module
goes silent on the build today. Every escape found is prospective, which is what a guard is for.

*Do not re-pitch* a third narrowing of the same shape without an answer to the absence-of-evidence
root cause, and *do not* take "the attribute half is the tractable one" forward: that was this
session's own claim and grading refuted it.

### 2026-08-22 - CS-492, CS-807 - NOT A COMPLETION RECORD. NOTHING CLOSED. Nine rounds of CS-492 were graded and every one was REFUTED; the false-flag direction was split out as CS-807
Verification: this entry is a POINTER. `ROADMAP.md` for CS-807 as a filed item and for
CS-492's rewritten NOTE; `docs/history_notes.md` under **CS-807 - detail** for the
measurement tables; `WAKEUP_NOTES.md` session 27 for the full-fidelity account. No test is
cited because NO CODE SHIPPED - commits `b8148cd`, `6680182` and this one are documentation,
and zero `.py` files were touched in `main` across the session.

**WHAT WAS MEASURED, all of it reproduced by the merger rather than taken from a builder.**
Rounds six, seven, eight and nine of CS-492 were each graded on two independent lenses and
each returned REFUTED on a real defect. Rounds seven, eight and nine were BUILT and remain
UNCOMMITTED in worktrees by operator decision, so that nothing unproven enters `main`; no
build is strictly best, and round nine's engine survived control-validity grading while its
prose did not.

**THE THREE NUMBERS THAT DECIDED THE SPLIT.** The `_ANY_ATTRIBUTE` sentinel manufactures
**268** false declarations across six real modules from five ordinary lines of PEP 562. The
bare-name class that consumed nine rounds manufactures **eight**. And **four** false
declarations are live on the shipped tree in `tests/save/test_oracle_citations.py`, whose own
reason strings say "It opens no file and touches no path at all" - the guard was not repaired,
the false flags were written down and shipped.

**THE DECISION, AND ITS FENCE.** CS-492's acceptance is ESCAPE-shaped and cannot record
whether the false-flag direction was won, so that direction became CS-807 at tier 1. Two
narrowing spikes - five-site and two-site - each take every manufactured-declaration payload
to zero, each cost the SAME twelve controls, and narrowing the site count retires NONE, so the
bare-name conflict is MEASURED IRREDUCIBLE. *Do not re-pitch* a tenth round of the same shape,
and *do not close either item by deleting the twelve controls*: one of them exists specifically
to defeat a guard that passes the caption case by accepting nothing.

### 2026-08-22 - CS-442, CS-702, CS-G01, CS-G05 - NOT A COMPLETION RECORD. NOTHING CLOSED. An /insights pass measured four findings and filed each into the file that owns it
Verification: this entry is a POINTER, deliberately - every measurement it refers to is
recorded in the file that owns that fact, and is not restated here. `ROADMAP.md` for CS-442's
re-derived note and for CS-702 and CS-806 as filed items; `docs/history_notes.md` under
**CS-442 - detail**, **CS-702 - detail** and **CS-806 - detail** for the methods and tables;
`docs/GATED.md` for the dated CS-G01 and CS-G05 status blocks; `BACKLOG.md` for the port
observation. No test is cited because no code shipped - like the CS-485 licence gate below,
the record IS the artifact. Commits `b31d071`, `75a662a`, `bd5e9b3` and this one, all
documentation, zero `.py` files touched across the session.

**WHY A NON-CLOSURE RECORD EXISTS AT ALL.** The /insights pass that opened this session found
that the two preceding commits shipped roughly 1750 lines into `main` under CS-492 with no
ledger presence of any kind. Ending this session the same way would refute its own finding.
This entry is therefore the minimum that makes the session visible from the ledger, and it
points rather than restates because `CLAUDE.md` section 4 gives every fact exactly one owner.

**THE FOUR FINDINGS, one line each, evidence in the owning file.** CS-442: the ledger's own
verification pointers were censused and 7 of 68 do not resolve, in three repair classes, and
the figure is a floor because only one citation shape was read. CS-702, NEW ID: the
no-agent-trailer rule recorded in `docs/GATED.md` is enforced by nothing and 18 commits on
`main` already carry the trailer. CS-G01: unblocking condition 1 is stale. CS-G05: the next
step its 2026-08-16 status block promised was never taken.

**ONE CORRECTION, RECORDED BECAUSE THE WRONG READING IS THE TEMPTING ONE AND WILL BE REACHED
AGAIN.** The CS-G01 finding was first written up as "S4 succeeded, so the item should have been
VOIDED and was not". **THAT IS BACKWARDS AND ADR 0003's OWN CONSEQUENCES SECTION REFUTES IT.**
S4 split: geometry yes, semantics no. The save carries placement and provably does not carry
purity - `mPurity`, `mResourceNodeType`, `mResourceClass`, `EResourcePurity` and
`mExtractResourceNode` occur zero times across three worlds and four builds - so the asset path
is now LOAD-BEARING for the semantics half rather than a superseded fallback, and ADR 0003 says
exactly that. Condition 1, read literally, would void an item that ADR makes necessary. The
dangerous direction here is the false VOID, not the missed one.

**TWO ENVIRONMENT ANOMALIES OBSERVED WHILE RUNNING THE RITUAL, both filed rather than left in a
transcript.** First, `py -3` and `python` resolve to DIFFERENT Python 3.14.4 installations on
this machine, and the interpreter the docs name is the one with no `ruff` module - filed as
CS-806. `scripts/verify_env.py` does not catch it and is not wrong to miss it: it probes the
toolchain by NAME on PATH, where `ruff` genuinely is. Second, port 8901 - this project's
allocated dashboard port - has been held since 2026-08-16 by an unrelated third-party
process, deliberately not named here. `scripts/verify_env.py` reports it as a SOFT failure on every run and that
mechanism is working correctly; what is absent is the decision it asks for, which is only forced
when CS-601 tries to bind. Filed in `BACKLOG.md` with that trigger. **Nothing was killed, moved
or re-recorded** - the port band is operator territory.

### 2026-08-20 - CS-493, CS-494 - CORRECTED and CLOSED respectively; the declaration reader reads KEY POSITIONS only; the CS-493 entry below it contains a sentence measured FALSE
Verification: `tests/save/test_reach_guard.py::test_every_graded_declaration_in_this_package_is_readable_from_the_source`
and `::test_the_sibling_resolution_bound_is_the_number_this_module_declares` for CS-493;
`tests/save/test_phase4_gate.py::test_the_two_walks_over_held_bytes_differ_only_where_recorded` for
CS-494. All run with `CLOCKSPEED_GAME_DIR` and `CLOCKSPEED_SAVE_ROOT` pointed at directories that
do not exist.

**THIS ENTRY CORRECTS THE CS-493 ENTRY BELOW IT, which is append-only and therefore not edited.**
That entry says an over-read "can never manufacture a reacher, because `_reaching_names_of` returns
`graded & (direct | indirect)`". **THAT SENTENCE IS FALSE AND A REFUTATION PASS MEASURED IT.** The
intersection is circular: `indirect` is computed from `propagating`, and `propagating` is computed
from `graded`, so widening `graded` widens the very set it is then intersected with. The same false
sentence stood in the `_declared_graded_names` docstring and is corrected in place there.

**REPRODUCED END TO END BY THE MERGER.** A planted module in which NO function calls any library
primitive exported a reacher, and an importer of it was told `undeclared functions touch a library
primitive: ['_consumer']` - for a function that touches nothing in either module. The only way to
green that tree is to write a reason that is false. Forcing a false reason is the defect class this
package has already shipped eight of.

WHAT THE REPAIR IS. The reader walked the whole declaration for anything name-shaped. It now
resolves KEY POSITIONS and refuses everything else: a string key, an `f.__name__` key, and a
comprehension key resolved through its iterable BY POSITION. Targets are paired with their values,
so `_GRADED_LIBRARY_REACH, _EXEMPT_LIBRARY_REACH = a, b` no longer reads the exempt map as graded.
A comprehension carrying an `if` clause is REFUSED rather than resolved, because the position read
cannot see which rows a filter drops. **Measured on all four spellings the refutation used plus the
three the package writes: exact on every one, and exact against runtime on all twelve declaring
modules.**

UNDER-READING IS NOW THE ONLY FAILURE DIRECTION LEFT, AND IT IS THE ONE THE BACKSTOP CATCHES.
`test_every_graded_declaration_in_this_package_is_readable_from_the_source` compares the source read
against the runtime mapping for every module in the package.

**TWO MORE FINDINGS FROM THE SAME PASS, BOTH REPAIRED.** The backstop skipped any module whose
declaration was invisible at runtime - a declaration bound under `if TYPE_CHECKING:` was dropped
entirely while the reader read it anyway; it now checks a module that declares on EITHER side. And
the hop-bound control passed `hops=` explicitly on both assertions, so it never exercised the
shipped default: a tree declaring a bound of two while every default spent one was **fully green**.
The control now takes the default, and pins BOTH sides - a chain of exactly the declared length must
resolve at the default, which no smaller default can do. That mutant is now killed.

**CS-494 CLOSES ON THE SECOND BRANCH OF ITS ACCEPTANCE - the difference is recorded and GRADED.**
The two walks are NOT merged, and that is the answer rather than a compromise: they ask different
questions over different files and return different things, so merging them would make one caller
wrong. What was genuinely broken was coverage, and that is closed - `_retained_body_attributes`
gained the tuple target, the `@property` accessor and the bytes-LIKE vocabulary its sibling already
had. **Measured before the widening: it adds NOTHING on the shipped save modules**, so it is a grade
that starts catching things rather than one reporting what was already known.

FIVE OF THE SIX DISAGREEMENTS WENT AWAY. The item's detail block named three; the merger measured
six. The one that survives is a difference of SUBJECT - the reach guard counts a real `Path` as
personal data because that is what it is about, and the retention walk does not because a path is
not save bytes - and it is recorded with that reason in `_HELD_BYTES_SHAPES` and asserted. A row
that differs without a reason fails, and so does a row that agrees and still carries one.

### 2026-08-20 - CS-493 - the sibling-resolution bound moves from prose into DATA, and a declaration the reader cannot follow is REPORTED instead of read as empty
Verification: `tests/save/test_reach_guard.py::test_the_sibling_resolution_bound_is_the_number_this_module_declares`
and `::test_every_graded_declaration_in_this_package_is_readable_from_the_source`. Both run with
`CLOCKSPEED_GAME_DIR` and `CLOCKSPEED_SAVE_ROOT` pointed at directories that do not exist.

**CLAUSE 2 WAS LIVE ON THE SHIPPED TREE, NOT LATENT, AND THE ITEM WAS FILED AS THOUGH IT WERE A
BOUND RATHER THAN A DEFECT.** The new cross-check reddened on arrival, naming two tracked modules
whose `_GRADED_LIBRARY_REACH` the source reader could not follow: `test_decode_oracles.py`, which
keys on `_sweep_decode_oracles.__name__`, and `test_objects.py`, which builds the map with a
comprehension over a table of `(label, function)` pairs - **literally the comprehension the
acceptance names**. Both spellings exist for good reasons: one keeps a censused module free of a
string literal, the other stops the graded set drifting from the helper list. Neither was wrong;
the reader was.

WHAT THE REPAIR IS. `_declared_graded_names` read `ast.Dict` constant keys and nothing else, so
any other spelling read as EMPTY - and that fails in the PERMISSIVE direction, because the sibling
export is filtered by that set. It now reads three exact spellings - a string key, `f.__name__`,
and a bare reference - and follows ONE module-scope constant, which is the indirection the package
actually uses.

**IT OVER-APPROXIMATES ON PURPOSE, AND THAT IS SAFE FOR A REASON RATHER THAN BY LUCK.**
`_reaching_names_of` returns `graded & (direct | indirect)`, so a name the reader reports that does
not actually reach is intersected away and can never manufacture a reacher. A name it MISSES is a
real reach that goes unexported and unguarded. Measured after the widening: the reader now names
exactly the runtime keys for all twelve declaring modules, over-reading nothing.

CLAUSE 1 IS CLOSED ON THE SECOND BRANCH OF ITS OWN ACCEPTANCE - the bound is recorded in shipped
DATA rather than in prose. `_SIBLING_RESOLUTION_HOPS` is a constant the resolution actually spends,
one hop per module, and the control plants a chain BUILT FROM that constant and requires it
unresolved at the bound and resolved at one more.

**THE FIRST DRAFT OF THAT CONTROL PINNED THE LITERAL WHILE CLAIMING TO READ THE CONSTANT.** It
planted a fixed three-module chain, so raising the bound to two left the chain resolvable AT the
bound and reddened it - a mutant dying for the wrong reason. Rebuilt to generate the chain from the
constant: raising the bound now SURVIVES, which is correct, because raising it is a deliberate
change and the control follows it. Neutering the recursion and making it ignore the bound are both
killed.

**WHAT THIS DOES NOT CLOSE, from the item's own four bounds.** `_sibling_module_file` still has no
stated precondition on `source` - its bound holds as a property of the call sites, measured, not as
an assertion. And `MODULE_SCOPE_REACH` is still ONE sentinel per file, so a module already
declaring it absorbs a second module-scope reach with no new evidence; that is reproduced and filed
as CS-501 - first filed as CS-500, which COLLIDED with the phase 5 gate; the older item keeps
the ID and the collision is corrected here rather than by editing the entry that made it. Neither is in this item's acceptance and neither is claimed.

### 2026-08-20 - CS-497 and CS-498 - the vocabulary partition stops being a tautology, and a self-exemption keyed on the guard's own file name is caught
Verification: `tests/save/test_reach_guard.py::test_a_vocabulary_name_classified_nowhere_is_not_silently_a_reach_primitive`,
`::test_the_reach_primitives_partition_the_filesystem_vocabulary` and
`::test_the_guard_reaches_the_same_verdict_under_its_own_name_as_under_any_other`. All run with
`CLOCKSPEED_GAME_DIR` and `CLOCKSPEED_SAVE_ROOT` pointed at directories that do not exist. To see
CS-497's defect, revert `reach_guard._reach_primitives` to
`_LIBRARY_LOCATORS | (frozenset(vocabulary) - frozenset(_NOT_LIBRARY_REACH))`; the first test
reddens. To see CS-498's, add `if module_path.name == "<the guard's file>": return` to
`_assert_library_reach_is_declared`; the third reddens.

**CS-497 - INCLUSION IS DECLARED NOW, NOT DERIVED BY SUBTRACTION.** The reach set was
`locators | (vocabulary - excluded)`, so a name added to `_FILESYSTEM_PRIMITIVES` and classified
nowhere became a reach primitive by arithmetic, and the assertion that was supposed to catch that
reduced to `A <= B | A`. `_REACHES_THE_LIBRARY` now names the reaching half and
`_reach_primitives` INTERSECTS, so a name in neither map reaches nothing.

**THE ASSERTION WAS NOT DELETED - THE DERIVATION WAS REPAIRED UNDER IT**, which the item's fence
required, since that same line is what holds the exclusion direction. It now bites: `fchmod`
added to the vocabulary and classified nowhere reddens with `vocabulary members are neither reach
primitives nor excluded with a reason: ['fchmod']`. The partition is asserted in BOTH directions
and for disjointness, because a partition asserted one way round is a subset check wearing a
partition's name.

**THE DERIVATION IS GRADED WITH A VOCABULARY IT HAS NOT SEEN.** Asked only about the shipped
constant, a derivation that absorbs an unclassified name and one that rejects it give the same
answer - which is why the old assertion could not tell them apart. `_reach_primitives` takes the
vocabulary as an argument so a control can hand it an invented name.

**THE REACH SET IS UNCHANGED BY THIS**, checked directly: the declared twelve equal what the
subtraction produced. No module's classification moved.

**IT IS NOT CS-433's DEFECT RETURNING.** That was two lists in two FILES, neither aware of the
other. These are two classifications of ONE vocabulary in one file, asserted to partition it
exactly - neither can gain or lose a name without the other disagreeing.

**CS-498 - THE GUARD'S VERDICT MUST NOT DEPEND ON WHAT THE FILE IS CALLED.** Every control ran
the guard against a `tmp_path` copy under a different filename, so a guard early-returning on its
own name defeated all of them at once: the splice still reddened, the positive controls still
passed, and an undeclared reach in the real source went unseen - measured green on this tree and
on `1e05233`. The close writes two byte-identical spliced copies differing only in filename, one
of them under the guard's own basename, and requires the same verdict for both. **The basename is
taken from the guard's code object and named nowhere**, which the item's fence required.

**FOUR MUTANTS FOR CS-498, THREE KILLED AND THE FOURTH DISCLOSED RATHER THAN CLAIMED.** Exemptions
keyed on `.name`, on `.stem` and on `str(path).endswith` all red on the intended test. An
exemption keyed on the FULL PATH survives, because both copies live in `tmp_path` and neither is
the real file, so they agree. That is stated in the control's own docstring and filed as CS-499
rather than implied away. CS-497 was mutated four ways and all four died.

**THE FIRST DRAFT OF THE CS-498 CONTROL SHIPPED A NON-NEGOTIABLE 12 VIOLATION AND THE WHOLE-SUITE
RUN CAUGHT IT.** It bound the guard's failure in an `except` handler and rendered it with
`str(caught)`; `str` on an OSError appends the path it failed on.
`tests/test_exception_rendering.py` reported it, and that module lives OUTSIDE `tests/save`, so
the `tests/save` run was green while it was there - the same trap session 23 recorded. Rewritten
onto `pytest.raises`, which the guard's AST shape cannot see into, and the mutants were re-run
afterwards because an idiom change can cost a control its teeth.

### 2026-08-20 - CS-496 - the doc-budget scratch fixture no longer races git's own background maintenance, and the race is reproduced DETERMINISTICALLY rather than waited for
Verification: `tests/test_doc_budget.py::test_the_scratch_copy_survives_a_git_lock_vanishing_mid_copy`
and `::test_the_scratch_template_has_git_housekeeping_disabled`. Both run on a machine with no
game and need only `git` on PATH. To see the defect, revert `_copy_checkout`'s body to
`shutil.copytree(source, destination, ignore=_hook)` - the first test reddens with the CI error
verbatim.

WHAT CLOSED, IN TWO HALVES. `_build_template` now sets `maintenance.auto=false` and `gc.auto=0`
in the scratch template BEFORE it commits, so the lock file is never created; and
`_copy_checkout` skips a file that has ceased to exist by the time it is read, so a lock that
appears anyway cannot fail the copy. The second half is there because a fixture resting on one
git config being honoured by every future git version has one point of failure and no second.

THE CAUSE, NAMED. `git commit` runs `git maintenance run --auto` and DETACHES it. The
session-scoped template therefore keeps a background git process after the fixture that built it
has returned, and that process creates and removes `.git/objects/maintenance.lock` while later
tests are copying the directory. `shutil.copytree` stats a tree and then copies it, so anything
removed in that window kills it.

THE REPRODUCTION IS DETERMINISTIC, WHICH THE ACCEPTANCE REQUIRED. `copytree` hands each
directory's entries to its `ignore` callback after listing them and before copying them, so
deleting the lock from inside that callback removes it in exactly the window CI lost. No
re-running until it happens. The seam `_hook` exists for that and production callers pass
nothing.

**THREE MUTANTS, ALL KILLED BY THE INTENDED TEST.** Reverting the tolerant copy reddens the race
test; removing the two config lines reddens the housekeeping test; and a hook that deletes
nothing reddens the race test's own third assertion, so the control is not passing because the
race failed to happen.

THE FIX WIDENED A GUARD AND THAT IS RECORDED RATHER THAN DONE QUIETLY.
`test_the_suite_never_mutates_this_repository_worktree_admin` required every `_git` call's first
argument to be the identifier `repo`; reading the template's config needed `repo_template`. The
guard's rule is that a git call targets a scratch repo the test built, and `repo_template` is
one - the single name was the rule's implementation, not its intent. The alternative was binding
`repo = repo_template` before the call, which is **bypass 1 in that guard's own list of what it
cannot see**. Using a hole a guard documents to get past that guard is worse than widening it in
the open, so the allowed set is now a named constant carrying the reason.

NO SIBLING CASE. Four other modules build throwaway `git init` repositories, and none of them
copies a live `.git` tree - the race needs both. Their commits also spawn detached maintenance,
which is stated here as an observation rather than a claim that it costs anything.

### 2026-08-20 - CS-495 - the library-reach guard implementation is relocated out of `test_properties.py` into `tests/save/reach_guard.py`, restoring the margin under the 256 KiB ceiling; a refutation pass REFUTED the first close and was right
Verification: `tests/save/reach_guard.py` is the guard; `tests/save/test_reach_guard.py` is the
control set. In particular
`tests/save/test_reach_guard.py::test_the_module_that_owns_the_guard_is_inside_the_population_it_walks`,
`::test_no_module_the_collector_skips_defines_a_test`,
`::test_the_guard_catches_an_uncontained_helper_spliced_into_its_own_source` and
`::test_no_test_in_this_module_is_gutted_to_an_early_return` are the four this item added. The
ceiling itself is `tests/data/test_phase2_gate.py::test_no_file_under_tests_is_large_enough_to_be_a_slice_of_real_game_data`,
whose `_MAX_TEST_FILE_BYTES` is UNCHANGED - diff that file against `1e05233` and it is
byte-identical. All run with `CLOCKSPEED_GAME_DIR` and `CLOCKSPEED_SAVE_ROOT` pointed at
directories that do not exist.

WHAT CLOSED. The module is under its ceiling by a margin a session can spend. Read the sizes
off the tree rather than from here: `test_properties.py` shrank by roughly a third, it is no
longer the largest authored file under `tests/`, and the comment justifying the number - that
the ceiling sits "well above the largest authored file" - went from barely true to comfortably
true without the number moving. **The number was NOT raised**, which the item's fence forbade.

IT WAS A RELOCATION, NOT A REWRITE, AND THAT IS MACHINE-CHECKABLE. Fifty-six top-level
definitions left `test_properties.py`; every one is byte-identical to its pre-move source,
verified by parsing both trees and comparing source segments. Nothing was deleted. The
collected node-id set gained the four tests above and lost nothing at all - five test functions
changed module and no test id disappeared.

WHAT STAYED, AND WHY. `test_properties.py` keeps its own `_GRADED_LIBRARY_REACH` and
`_EXEMPT_LIBRARY_REACH`, and the checks that grade THAT file rather than the guard. The five
controls that plant a module and demand a verdict moved to `test_reach_guard.py`, which is not
a new module - session 24 created it and it grew here.

THE BLAST RADIUS IS TWELVE FILES, NOT THREE. Ten sibling modules took import rewiring and had
the sentence "The guard is owned by `test_properties`" corrected. A verification pass named
that omission in the first draft of this entry.

**TWO REFUTATION PASSES REFUTED THE FIRST CLOSE AND BOTH WERE RIGHT.** Every finding was
reproduced by the merger before anything changed.

- **A test planted in `reach_guard.py` runs zero times and nothing says so.** Pytest does not
  collect it, and no gutting guard reads it. Pre-move the guard's owner was a collected test
  module, so this property was graded; after the move it was not. **The CLASS is older than
  this item** - the same plant in `tests/save/synthetic.py` survives on `1e05233` too - but the
  guard-owning file's membership in it is new. Closed by
  `::test_no_module_the_collector_skips_defines_a_test`, which covers both modules and both
  shapes, the `test_`-named function and the `Test*` class.
- **The margin on the guard's own source dropped from eleven reddening tests to one**, because
  `reach_guard.py` cannot carry the per-module splice control every consumer carries. Closed by
  `::test_the_guard_catches_an_uncontained_helper_spliced_into_its_own_source`, which derives
  the guard's path from its own code object rather than naming it.
- **Three sentences this item authored were measured false and are corrected in place.** A
  claim that each consuming module keeps three checks - only two of the five call
  `_assert_no_test_is_gutted` at all; a module COUNT written into the same file that had just
  deleted a different stale count on the grounds that CLAUDE.md section 4 forbids one; and a
  `:func:` role plus a "THIS MODULE'S OWN planted control" that stopped resolving when the
  guard moved one file away. Do not rewrite them back.

**A PRE-EXISTING TAUTOLOGY WAS FOUND WHILE READING THE MOVED CODE and is filed as CS-497.**
`_LIBRARY_PRIMITIVES` is derived as the locators unioned with the vocabulary minus the
exclusions, so `::test_the_reach_primitives_partition_the_filesystem_vocabulary`'s inclusion
assertion reduces to `A <= B | A`. An unclassified name added to the vocabulary leaves that
test green - measured. The comment claiming "a name can be excluded, but it cannot be
forgotten" was false and is corrected in place. **CS-498** is the other pre-existing hole found
here: the guard cannot detect a self-exemption in its own source, measured green on BOTH trees.

**THIS ITEM MOVED THE SUBJECT OF THREE OTHER RECORDS, AND THEY ARE RE-POINTED RATHER THAN LEFT
TO A FUTURE GREP.** CS-494's acceptance named `test_properties._bound_parameter_annotations`,
which is now `reach_guard._bound_parameter_annotations`. CS-473's subject was one module's
prose and is now three. And **this entry corrects two earlier ledger records**, which are
append-only and therefore not edited: the CS-471 entry above cites three tests at
`tests/save/test_properties.py::` that are now at `tests/save/test_reach_guard.py::`, and the
CS-491 entry says "The guard itself stays in `tests/save/test_properties.py`" and "The guard
implementation stayed put" - both true when written, both false as of this item.

### 2026-08-20 - CS-491 - the reach guard's aliasing, cross-module and wrapper routes are closed by RESOLUTION rather than by a wider name list; TWO REFUTATION PASSES REFUTED IT FIRST AND BOTH WERE RIGHT
Verification: `tests/save/test_reach_guard.py`, which is the whole control set - in particular
`::test_a_primitive_reached_through_an_alias_is_named_by_the_guard` (fourteen routes),
`::test_a_module_scope_reach_through_an_alias_is_reported` (five),
`::test_every_spelling_of_the_cross_module_route_is_resolved` (two),
`::test_a_module_reaching_only_through_a_sibling_helper_is_not_classed_silent`,
`::test_a_siblings_exempt_helper_does_not_export_a_reach_it_does_not_have`,
`::test_a_siblings_graded_helper_that_reaches_indirectly_is_still_exported`,
`::test_a_wrapper_holding_the_body_in_another_shape_is_flagged_as_propagating` (eleven
defeats), `::test_a_wrapper_class_annotated_through_a_module_handle_is_resolved`,
`::test_the_guards_failure_message_names_functions_and_never_a_path` and
`::test_a_primitive_name_inside_a_collection_literal_binds_no_alias`. The guard itself stays
in `tests/save/test_properties.py`. All run with `CLOCKSPEED_GAME_DIR` and
`CLOCKSPEED_SAVE_ROOT` pointed at directories that do not exist.

WHAT CLOSED. Every route the item was filed on, and twenty-one more that refutation passes
measured past two earlier attempts at closing it, turn a test red on a machine with no game -
and each red NAMES the evading function, or the module-scope sentinel where there is no
function to name. The item's fence forbade closing it by widening the name list, so nothing in
the guard names a wrapper: `partial`, `methodcaller` and `attrgetter` appear nowhere in it.

IT TOOK THREE ROUNDS AND THE FIRST TWO WERE WRONG. That is the entry, not a preamble to it.
Round one closed the seven filed routes; a refutation pass found eleven more, every one
reproduced by the merger before anything was changed. Round two closed those; a second pass
found a twelfth plus ten more. Round three closed those. A green suite after round one would
have been a lie, and the guard is the thing this item is about.

THE SAME DEFECT APPEARED FOUR TIMES: ONE MECHANISM APPLIED TO ONE OF TWO POPULATIONS. Aliases
were resolved to a fixpoint for PRIMITIVES and not for TYPES, so `_Body = bytes` switched the
whole wrapper walk off. The module-handle import shape was resolved for REACH and not for
WRAPPERS. The sibling export was keyed on the DIRECT set, so a graded helper reaching through
another graded helper never exported. And `_module_scope_reaches` re-derived the callee name
itself with the pre-CS-491 two-channel test while `_calls_any` had grown five channels - so
EVERY route already closed reopened by moving it one indentation level out of its `def`,
escaping the guard and the classifier at once. That is the CS-477 pattern, found four times
inside the repair for it.

THE FIX FOR THE LAST ONE IS THE SHAPE WORTH COPYING. Replacing the callee node-type
enumeration with a WALK over the callee expression flagged thirteen innocent functions,
because a RECEIVER is a mention: `THIS_MODULE.read_text()` reads as reach once `THIS_MODULE`
is itself an alias. That would have manufactured thirteen false reasons, which is the defect
CS-471 had to correct eight of at once. What ships is `_callee_resolves`, a recursive
structural question that asks the same thing of a smaller callee. A guard that names a
population is the defect; a guard that walks everything manufactures reasons.

THIRTY MUTANTS WERE RUN AGAINST THE CONTROLS AND TWO SURVIVED EARLIER PASSES, both closed by
adding the route that isolates the branch rather than by deleting the branch: the
`getattr`-through-a-NAME channel, live only where the primitive is handed back UNCALLED, and
the store-annotation read, live only where the store's annotation is the sole statement of the
type. The first draft of that second route reddened on `_Wrapped.__init__` rather than on the
caller, because its value was itself a primitive call - a red for the wrong reason is not a
measurement.

TWO OF THE CONTROLS WERE TAUTOLOGIES AND A REFUTATION PASS PROVED IT BY CONSTRUCTION. The
personal-data vocabulary's positive half was `_carries_personal_data(f"{word} | None")`, which
reduces to `word in word + " | None"` and is true of any string - a vocabulary naming nothing
personal passed it. And the collection-literal control claimed to hold the bound stated in
`_resolves_by_string`, while widening that predicate to walk its arguments left the whole suite
green. Both are replaced with assertions that can fail.

NON-NEGOTIABLE 12 IS ENFORCED HERE NOW RATHER THAN ASSUMED. A privacy refutation pass - which
did NOT refute the change, and verified it at runtime with an audit hook, write interception
and forced frame rendering - counted this module's renderings of a caught exception into an
f-string rising from nine to nineteen, and observed that `tests/test_exception_rendering.py`
keys on an AST shape inside an `except` handler, so `with pytest.raises(...) as caught` is
structurally invisible to it. They are safe only because the guard formats sorted lists of
function names. `::test_the_guards_failure_message_names_functions_and_never_a_path` holds
that, and the mutant adding `module_path` to a guard message reddens it.

THE CONTROLS WERE RELOCATED, NOT TRIMMED. `test_properties.py` crossed the 256 KiB ceiling
`tests/data/test_phase2_gate.py` puts on any file under `tests/` - a crude check whose whole
job is catching a trimmed slice of real game data. CLAUDE.md section 4 says relocate rather
than delete, and raising the number would have falsified the comment that justifies it, so the
control set moved to `tests/save/test_reach_guard.py`. The guard implementation stayed put.
**The module was 288 bytes under that ceiling when the session started**, which is filed as
CS-495.

THE PRICE ON THE SHIPPED TREE IS ONE EXEMPTION, in `tests/save/test_workdir.py`.
`test_an_unrecognised_failure_is_reported_as_could_not_tell` binds `Path.iterdir` to a local
in order to REPLACE it, and the widened local-alias expansion cannot tell that local from one
holding a reach. Its first reason described work the test does not do and is corrected in
place. Residuals filed as CS-492, CS-493, CS-494 and CS-495.

### 2026-08-19 - CS-471 - the library-reach declaration is enforced package-wide and the wrapper evasion is closed; it CLOSES ON ITS THREE CLAUSES AND NOT ON THE CHANNEL BEING SHUT
Verification: `tests/save/test_properties.py::test_every_library_reaching_module_in_the_package_is_declared`,
`tests/save/test_properties.py::test_the_suite_wide_guard_catches_a_module_that_declares_nothing`
and `tests/save/test_properties.py::test_a_helper_handing_back_a_wrapped_body_is_flagged_as_propagating`,
against the six modules that gained `_GRADED_LIBRARY_REACH` and `_EXEMPT_LIBRARY_REACH`. To
reproduce the defect, drop a module under `tests/save` that calls the raw locators and declares
neither map, and run with `CLOCKSPEED_GAME_DIR` and `CLOCKSPEED_SAVE_ROOT` pointed at
directories that do not exist.

WHAT CLOSED, AND ON THE THREE STATED CLAUSES ONLY. Every module in the package that reaches the
save library declares its reaching functions or exempts them by name with a reason; the
enforcement walks the package directory rather than waiting to be called, so a module added
tomorrow is in scope the moment it exists; and a helper returning a dataclass that wraps a body
is flagged as propagating. The parameter-and-locals channel named in the item's enlarging
evidence is NOT closed, `tests/save/test_objects.py::test_the_entry_points_still_bind_the_raw_body_where_a_renderer_can_read_it`
therefore still passes and stays, and this entry closes nothing about it.

BOTH REFUTATION PASSES SUCCEEDED AND ONE REFUTED A CLAUSE OUTRIGHT. The function scan read
module-body statements only, so a reach spelled at module scope was invisible - and the
classifier called such a module SILENT, so the guard was never applied to it at all. The proof
of concept was the ordinary pytest idiom, a module-scope call feeding a parametrize list, and it
held the account directory as a process-lifetime global with every guard green. Closed under a
`MODULE_SCOPE_REACH` sentinel wired into the guard AND the classifier, and verified against that
same planted module.

EIGHT SHIPPED EXEMPT REASONS OF MINE WERE MEASURED FALSE AND ARE CORRECTED. Do not rewrite them
back: six described `rglob` and `resolve` filesystem work on functions that touch no filesystem,
matched only by a name collision with a sibling's own citation resolver; one described the
auto-detected game install for a test that writes a synthetic usmap into `tmp_path`; and one
claimed `tmp_path` containment for a test that passes no path at all, whose real containment is
an autouse environment fixture - measured, because the same call uncontained resolves a real
save on this machine.

FOUR MORE DEFECTS IN MY OWN WORK, EACH FOUND BY A PASS RATHER THAN BY ME. A privacy control in
the wider suite caught this work rendering a caught exception OBJECT into a message, which is
non-negotiable 12 and was invisible to a `tests/save` run; the wrapper walk read field
annotations only, so a subclass of a wrapper came back clean; the clause-2 control was a
tautology, because its loader reported every input undeclared including a path that does not
exist; and the package walk was narrowable from every module to one with the suite still green.

WHAT THIS DOES NOT CLOSE IS FILED AS CS-491 RATHER THAN DISCLOSED HERE - the aliasing routes,
the cross-module route, the wrapper defeats, and the fact that clause 3 moves no verdict on the
shipped tree. Read that item before treating this area as guarded.

### 2026-08-19 - CS-478 - the two definitions of "an oracle scores this type" now meet in one assertion, and disagree only where the module records it
Verification: `tests/save/test_byte_order_status.py::test_the_two_admission_rules_for_the_int32_oracle_never_disagree_unrecorded`,
against `tests/save/test_properties.py::_tally_decoded_values` and
`tests/save/test_value_anchoring.py::_score_population`. To reproduce the defect, apply the
six lines named in that test's docstring and run `tests/save` with `CLOCKSPEED_GAME_DIR` and
`CLOCKSPEED_SAVE_ROOT` pointed at directories that do not exist. That docstring is the ONE
OWNER of every count and every route; this entry states none of them.

WHAT CLOSED, ON THE SECOND OF THE TWO SANCTIONED ROUTES. The acceptance offered unification
behind one owner OR holding the two apart with a test that reddens on an unrecorded
disagreement. The second was taken, because the item's own fence forbids deleting either
definition: the tag-word rule is what keeps a BoolProperty out of the int32 population, and the
decoded-shape rule is the whole of CS-421 route (b). The literal reading - red whenever the two
differ at all - would red on the shipped tree, since `UInt32Property` differs today by design
and is recorded for it. What ships reddens on a difference the module does NOT record, which is
the "cannot disagree SILENTLY" half of the acceptance.

THE HOLE WAS REAL AND WAS MEASURED BEFORE ANYTHING WAS WRITTEN. Six edited lines add a second
four-byte type the shape rule scores, the dispatch skips, and the module records as `unscored` -
so the module ships "nothing has looked at this type" about a type one of its own oracles
scores - with `tests/save` green with no game at the counts the clean tree gives. The new
control reds on it and nothing else in the suite does, re-derived independently by a refutation
pass that built its own forgery with a different word.

BOTH REFUTATION PASSES SUCCEEDED AND THEY AGREED ON THE HEADLINE. **I accused a TRUE sentence of
being false and nearly shipped the accusation.** A draft rewrote the docstring of
`test_the_cannot_separate_set_is_bounded_without_a_library` to say that
`test_no_type_an_oracle_scores_is_left_recorded_as_unscored` "says nothing whatever about"
the word the cannot-separate set names. Widening the tag-word dispatch to score that word reds
that very test, naming it. The original sentence GOVERNS THE TRANSITION while being silent on
today's state, and reading present non-membership of a runtime-computed population as silence is
the conflation. The sentence is restored verbatim with the refutation recorded beside it.

FOUR MORE OF MY SENTENCES WERE MEASURED FALSE AND ARE CORRECTED IN PLACE. Do not rewrite them
back: a probe constant described as the shape BOTH channels of the int32 oracle accumulate on
when its low byte is non-zero, so only one fires - the constant was changed to one for which the
sentence is true; a subset arm whose stated route raises `TypeError` inside the tally before the
assertion is reached, and which no edit to `objects.py` can fire at all; a reverse arm called
hard to reach that fires three ways; and an absolute suite count that distinguished nothing,
because the clean tree measures the same.

WHAT THIS DOES NOT CLOSE, IN THE SHARPEST FORM A REFUTATION PASS COULD PUT IT. One more line
turns the `unscored` lie into a `cannot_separate` lie. Whether an oracle really was applied and
came back undecided is a fact about the operator's library, and the derivation that could
dispute it skips with no game. This control raises the price of CONCEALMENT, not the price of
the lie. CS-426 owns that gap and this entry does not narrow it.

### 2026-08-19 - CS-487 - the tag-carried exemption's price is measured and raised from three lines in one file to seven across two; it is NOT closed as a mechanism
Verification: `tests/save/test_byte_order_status.py::test_no_word_the_exemption_admits_is_one_the_module_declines_to_measure`
and the widened saturation arm inside
`tests/save/test_byte_order_status.py::test_the_tag_carried_one_byte_values_are_derived_from_the_tag_reader`,
against `clockspeed/save/objects.py`. To reproduce the defect, apply the three lines named
below and run `tests/save` with `CLOCKSPEED_GAME_DIR` and `CLOCKSPEED_SAVE_ROOT` pointed at
directories that do not exist. The first test's docstring is the ONE OWNER of every count;
this entry states none of them.

WHAT CLOSED, AND ON THE STATED ACCEPTANCE RATHER THAN ON THE EXEMPTION HAVING BECOME BOUNDED.
The acceptance was that writing a type word into the `objects.VALUE_BYTE_ORDER_STATUS` literal
and widening `objects._read_tag_header` and `objects._decode_value` to admit it turns a test
RED on a machine with no game. It does. The reproduction on the item was re-measured by me in
a clone of `8ec3dbb` before anything was written, and again after: those three lines, all in
`clockspeed/save/objects.py` with no test-side line at all, ship `vacuous_one_byte` for an
EIGHT-byte Unreal type this repo names in no table at all, at the same pass and skip counts the
untouched clone gives. The route is word-agnostic and no word is named here or in the shipped
tree, per the item's fence.

TWO ARMS SHIPPED, NOT ONE, AND THE SECOND EXISTS BECAUSE THE FIRST WAS REFUTED. The first
reads `MEASURED_VALUE_TYPES` - what `objects._decode_payload` consults to tell unmodelled
content from a walk that has lost its place, and a table neither tag-carried site can move,
both being function bodies. A word the shipped decoder builds a value for, that this table
declines to name, is the module recording a settled byte order for a type it also records as
one it does not decode. THAT ARM ALONE DOES NOTHING AGAINST AN ATTACKER WHO PICKS A WORD
ALREADY IN THE TABLE RATHER THAN ADDING ONE, which a refutation pass measured on a live route
naming a LENGTH-PREFIXED type - CS-480's own defect, reached again through both shipped sites.
So the derivation's saturation arm, which intersected the fixed-width table alone while its own
message named a length-prefixed type as the thing it guarded, now intersects every table this
module reads a value out of the payload from.

BOTH REFUTATION PASSES SUCCEEDED AND NEITHER FINDING WAS REACHABLE FROM INSIDE THE WORK. One
found the cheaper route above. The other found that the eight-line price I had measured was
taken on a tree WITHOUT the new arm and carried the wrong tree's pass count, that I had called
a DERIVED table hand-authored while the same test module already recorded it as derived, and
that I had handed the residual to CS-488, whose acceptance is scoped to a width-table entry
that neither surviving route touches. All four are corrected in place with the refutation
recorded beside them rather than rewritten away.

WHAT THIS DOES NOT CLOSE, AND IT IS FILED RATHER THAN DISCLOSED. Two routes still reach a green
tree and both were taken all the way to green rather than left at the first red. They are
CS-490. The root neither this item nor CS-488 closes: every control on this exemption is keyed
on the module CONTRADICTING itself, and a module that claims a type in every table at once
contradicts itself nowhere.

A COUNT THIS ITEM WAS FILED WITH DID NOT REPRODUCE, and the correction is recorded at
`docs/history_notes.md` under **CS-487 - detail** rather than here, because that block owns it.
The relation it asserted - that the forged tree is byte-identical to the clean one - reproduced
exactly; the absolute figure did not, and it disagreed with session 22's own wakeup note.

### 2026-08-19 - CS-481 - the width table's membership is bounded for the words the module names; the three-line route is dead and three wider ones are filed
Verification: `tests/save/test_byte_order_status.py::test_no_word_carries_a_byte_order_status_the_module_records_as_unclaimed`,
`tests/save/test_byte_order_status.py::test_every_fixed_width_word_is_one_the_shipped_walk_counts_as_measured`,
`tests/save/test_byte_order_status.py::test_the_walk_outcome_words_are_pinned_and_distinct` and
`tests/save/test_properties.py::test_no_type_word_sits_on_both_sides_of_the_module_s_own_split`,
against `clockspeed/save/objects.py`. To reproduce the defect, apply the three lines named
below and run `tests/save` with `CLOCKSPEED_GAME_DIR` and `CLOCKSPEED_SAVE_ROOT` pointed at
directories that do not exist.

WHAT CLOSED, AND IT CLOSED ON THE STATED ACCEPTANCE RATHER THAN ON THE WIDTH TABLE HAVING
BECOME BOUNDED. The acceptance was that declaring a type one byte wide, when the module claims
nothing about that type's value encoding, turns a test RED on a machine with no game. It does.
The reproduction on the item - a `(1, "<b")` entry for `Int64Property`, its
`WIDTH_SHIPPING_GROUNDS` entry, and holding the word out of `MEASURED_VALUE_TYPES` - was
re-measured by me before anything was written, at `tests/save` **1055 passed 49 skipped with no
game, the same two counts the clean tree gives**, shipping `vacuous_one_byte` for an EIGHT-byte
type. Each line was measured alone: the width entry reds 4, plus its grounds reds 3, plus the
severed measured set reds 2. On the merged tree that same edit reds 3 - both new controls in
`test_byte_order_status` plus the phase-4 no-install gate behind them.

TWO ARMS, AIMED AT DIFFERENT LINES, NEITHER SUBSUMING THE OTHER. The CLAIM arm holds the status
mapping against `UNMEASURED_PAYLOAD_REGIONS`, the module's own record of what it claims nothing
about; the pre-existing split control required the UNION of the two halves to cover, never the
INTERSECTION to be empty, and the reproduction lived in that gap. The WALK arm asks the shipped
parser rather than a set: severing the width table from `MEASURED_VALUE_TYPES` does not stop
`_decode_value` decoding the word - it dispatches on the width table directly - it makes
`_decode_payload` count a declared-size disagreement as UNMODELLED CONTENT instead of as a walk
that has lost its place, which is the CS-417 conflation, measured on the forged tree.

ALL THREE REFUTATION PASSES SUCCEEDED. DO NOT RECORD THIS AS A CLEAN BUILD.
1. A ROUTE-AROUND PASS FOUND A DEFECT IN MY OWN CONTROL. The probe could not build a tag for any
   word carrying tag-extra strings, so those words were filtered out of the CONTROL population -
   while the GRADED arms iterated the width table raw with no such filter. Demonstrated with the
   shipped word `ByteProperty`: a later slice moving it into the width table would have been
   reddened by a message blaming the width table for a defect in the probe. FIXED by building the
   tag-extra shape instead of filtering; the control population went from 2 words to 6.
2. TWO PASSES INDEPENDENTLY MEASURED WIDER ROUTES STILL GREEN, and I re-measured both in clones.
   SIX LINES make the module claim the type outright and ship the false status with `tests/save`
   green (CS-488). THREE LINES, all in `objects.py` with no test-side line at all, ship it through
   the tag-carried exemption with no width entry involved (CS-487). A third finding, ungraded
   prose inside a region-table entry, is CS-489.
3. SIX SENTENCES OF MY OWN PROSE WERE MEASURED FALSE and are corrected in place with the
   refutation recorded beside them, never rewritten silently: that a constant probe "would satisfy
   two of the three" arms (measured: at most one, enumerated over all five outcome words); that
   without the control arm a broken payload builder "would still be graded green" (the agreeing arm
   reds on its own); that the citation checker "is blind to a `#:` line" (it resolves citations
   there and merely never requires one - and my sentence restated a false claim already in the
   file, which is the drift `CLAUDE.md` section 4 forbids); a "reds three tests" count that invited
   the wrong mapping, since the `test_properties` control is GREEN on the reproduction; a
   value-bytes rationale describing a discipline every one of its own call sites breaks; and a
   first draft of the residual paragraph that stopped at a red two lines short of green.
4. AN EQUIVALENT MUTANT SURVIVED AND NOW DOES NOT. Exchanging the string values of the two walk
   outcome words left every control green while inverting every rendered failure message, so a
   genuine desynchronisation would report itself as unmodelled content in the sentence a reader
   acts on. Pinned by `test_the_walk_outcome_words_are_pinned_and_distinct`, graded by me with
   that swap.

WHAT THIS DOES NOT CLAIM, because two of the passes are right that the mechanism is wider than
the word. Both arms read tables keyed by type word, so a type the module has never NAMED walks
past the claim arm - there is nothing to intersect with. The walk arm does not depend on the word
being named, and that is measured: a never-named type declared one byte wide and severed from the
measured set reds it and nothing else in the suite. And both arms of the walk control are narrow
in a way worth stating - the agreeing arm takes the width from the same table `_decode_fixed_width`
tests against, so no self-consistent entry can fail it, and at width + 1 the disagreement arm
reduces to asking whether the word is in `MEASURED_VALUE_TYPES`, which is derived from the width
table. The edit either arm catches is an edit to that derivation. All of this is written into the
module rather than left here.

### 2026-08-19 - CS-485 - the official wiki's CONVENTIONS section 14 licence gate: REFUSED for vendoring, CLEARED for reading and citing
Verification: this entry IS the record - a licence gate produces a decision, not a test. The
research it rests on was a dispatched page-by-page pass over the site's navigation and
category listings on 2026-08-18; re-run it against the URLs below to check any line.

GATE RESULT. satisfactory.wiki.gg is licensed CC BY-NC-SA 4.0, stated at
https://satisfactory.wiki.gg/wiki/Satisfactory_Wiki:Copyrights and qualified there by the
phrase "that we may lawfully license" - so the site does not purport to license the
publisher's own material that its pages restate. Copyleft plus a non-commercial restriction
means vendoring would relicense the project and conflict with `LICENSE`, which is a frozen
file. Traps from CONVENTIONS section 14: trap 1 fires (a CC grant sits alongside a platform
terms-of-service clause prohibiting automated crawling), trap 2 fires (pages predating March
2023 are adapted from a Fandom-era wiki, so there are multiple upstream holders, and the site
disclaims the publisher's material besides), trap 5 fires (NC plus SA is not an open-source
licence). Trap 4 is clean - the page links the canonical deed rather than pasting a modified
copy.

THE OPERATOR CORRECTED MY FRAMING MID-SESSION AND THE CORRECTION IS RECORDED RATHER THAN
ABSORBED: this is the OFFICIAL, developer-endorsed wiki, not a third-party community dump, so
`CLAUDE.md`'s "no community-compiled datasets" was the wrong fence to reach for. The gate
still refuses vendoring, on the licence rather than on provenance, and that is a better fence
because it is measured. The `Settled` entry in `CLAUDE.md` is amended accordingly.

WHAT ENDORSEMENT DOES NOT SETTLE, and this is the finding worth keeping: the site's standing
is not any page's authority. Three provenance classes coexist on it - verbatim publisher text
(the dedicated-server API page says so of itself), editor transcription of shipped data, and
editor reverse-engineering (the save-format page carries its own incompleteness caveat).
FRESHNESS IS ALSO NOT UNIFORM, and the split runs against this project: the patch-notes lane
is current with the operator's pinned build, while the save-format lane is a major version
behind. The save-format page also labels a header byte "session visibility" - a label
`BOOTSTRAP.md` section 2.4 already records as REFUTED by measurement across the operator's own
saves. That is the cheapest available argument against ever re-adopting the wiki as an
authority on save bytes.

ALSO RECORDED AS FACT, WITH NO RECOMMENDATION ATTACHED: the site runs MediaWiki with an open
Action API and serves raw wikitext, while the platform terms prohibit automated crawling. The
exact terms document could not be resolved from the link the Copyrights page uses, so the
crawling clause is PROBABLE AND UNCONFIRMED - which, defaulting to refused, means treat it as
binding. No automated poller.

WHAT THIS DOES NOT CLOSE. The upstream watch list the research produced has no doc with an
owner in the topology table yet; that is CS-486. And the research independently confirmed that
D1 node semantics - per-node resource type and purity - has no sanctioned source and the wiki
does not supply one, which is ADR 0003's gap unchanged.

### 2026-08-18 - CS-482 - the walk was DESYNCHRONISED, not overflowing; the (14,60) level tail is a counted list
Verification: `clockspeed/save/objects.py` (`_read_level_tail`, `_read_package_summary`) plus
`tests/save/test_objects.py::test_a_named_level_tail_carrying_one_entry_still_walks_to_the_last_byte`,
`::test_a_package_summary_name_of_any_length_walks`,
`::test_the_level_tail_entry_ceiling_refuses_exactly_above_itself`,
`::test_no_discarded_string_survives_in_a_parser_frame` and
`::test_every_real_save_of_a_measured_pair_walks_to_the_end_of_its_body`. Whole suite
12 failed 2073 passed 3 skipped -> **2137 passed 3 skipped exit 0** with a library, and
2036 passed 52 skipped -> **2088 passed 52 skipped exit 0** with no game. Drift guard CLEAN
9/9, doc budget PASS measured 16, mypy clean 84, ruff check and ruff format clean 84.

THE QUESTION THE ITEM ASKED WAS "LARGER WORLD OR DESYNCHRONISED WALK", AND IT IS
DESYNCHRONISED, MEASURED RATHER THAN ARGUED. The declared count that tripped the ceiling
decodes to four printable ASCII characters - the walk was reading a count out of the middle
of a string. Raising `MAX_OBJECTS` would have admitted it. Two corrections to the item's own
filing text, both measured: the refusal was against `MAX_CUSTOM_VERSIONS` and not
`MAX_OBJECTS`, and `test_save_60_refuses_the_grammar_the_other_pairs_accept` carried NO
independent evidence - all seven `test_properties.py` failures arrive through one shared
`_sweep_or_skip()` assertion, so it failing "beside" the others was one failure counted seven
times.

WHAT WAS WRONG. A named (14,60) level closes on a tail that this parser read as 12 constant
bytes. It is an opaque word, a COUNT, that many string pairs, and a second opaque word. The
count is 0 on 1522 of the 1525 real level tails on this machine, which is why 12 bytes fitted
every save the grammar was derived from. Three saves written while session 20 ran declare 1,
and against those a 12-byte reader lands 80 bytes early. Anchor: the constant word run that
opens a package summary sits at +4 from the summary start on all 1530 summaries under this
reading, and at +84 on the three tails that carry an entry under the old one.

THE SAME DEFECT WAS SHIPPED ONE FUNCTION UP THE SAME CALL PATH AND IS FIXED WITH IT. The
package summary's 70-byte "constant run" is a string, 22 opaque bytes and a second string,
tiling to exactly 70 when the two declare 0 and 40 - which they do on every real summary. The
recorded ground for skipping it ("no interior boundary is observable - not 4+6, not 8+2, not
16+10") was false: that search looked for a split into FIXED widths and the boundary is a
length prefix. The fixture wrote 70 zero bytes for the same stated reason, so it could never
have failed the reader that read them.

THE GENERAL LESSON, AND IT IS WHY BOTH HALVES ARE HERE: a run that every save in a corpus
fills identically is not a constant, it is a field nothing has varied yet, and the two are
indistinguishable from inside the corpus. The second value arrives as a desynchronised walk.

THREE REFUTATION PASSES RAN AND ALL THREE SUCCEEDED. Do not read this as a clean build. (1) A derivation pass REFUTED the ceiling's justification and the sibling: it
measured that an unbounded entry count executes ZERO loop iterations over nine deliberate
desynchronisations because `_Cursor.string` refuses first, so the sentence claiming a ceiling
prevents a long walk was false and is deleted; and that the ceiling's only measured effect is
to relabel two of nine desynchronisations from a diagnostic `ObjectFormatError` into the
misleading budget error. It also narrowed the evidence base: the three entry-carrying tails
are BYTE-IDENTICAL and all five (14,60) saves are one world, so the grammar rests on ONE
observed entry; and three rival tail grammars land all 17 saves on their final byte, so the
landing oracle is necessary and NOT sufficient. Every one of those is now disclosed in the
shipped docstring. (2) A privacy pass REFUTED the change on non-negotiables 11 and 12: my own
first-draft docstring put a positioned four-byte fragment of a decoded string from a real save
into a TRACKED file, in decimal and in ASCII. Removed. The same pass showed the four existing
privacy controls had ZERO REACH into the new code - every planted failure went through the
FLAT walk and the new readers are reachable only from `parse_body` - and proved it with a
mutant whose exception message was the two decoded strings verbatim, green at 1056 tests.
`_planted_failures` now reaches `parse_body`, and a frame-locals surface catches the mutant
that bound the decoded strings as helper arguments where `traceback.format_exception` renders
nothing and pytest renders both.

(3) A MUTATION PASS GRADED THE TESTS AND REFUTED THEM: 26 mutants of the shipped reader, of
which FIVE survived the whole suite and one was caught only on a machine holding a save
library, which is never CI. The four that survived BOTH configurations are the ones worth
carrying: `range(min(count, 1))` in the loop header - a reader that honours the first entry
and silently drops the rest - survived because NO TEST ANYWHERE SUPPLIED TWO ENTRIES, and the
library cannot supply one, but the fixture can for free; the ceiling moved to `1 << 30` and to
`1` both survived, because the test declared `MAX_LEVEL_TAIL_ENTRIES + 1` and asserted against
`MAX_LEVEL_TAIL_ENTRIES`, so THE CONSTANT GRADED ITSELF and the edge probe beside it pinned the
edge only relative to the constant; and retaining the entry strings in a module global or on
the cursor survived, because "never retained" was asserted against the returned model's repr
alone. The library-only one was the package-summary reorder, invisible without a game because
the fixture's middle run is 22 ZEROS and its first name is empty, so `4 + 22` and `22 + 4` land
on the same byte. All six are now DETECTED in both configurations, re-graded by me in a clone:
two entries are supplied, the ceiling is bounded from above by the smallest int32 four
printable ASCII bytes can make - `1 << 30` sits inside that interval, which is the failure the
bound exists for - and from below by the two-entry walk, retention is read out of module and
cursor state, and the summary test varies BOTH names.

THE PATTERN ACROSS ALL THREE PASSES IS ONE SENTENCE: EVERY HOLE WAS A POPULATION THE TEST
NEVER SUPPLIED. Two entries, a second string length, a second escape route, a ceiling probed
only against itself. The corpus could supply none of them and the fixture could supply all of
them for nothing.

FOUR OF MY OWN SENTENCES WERE MEASURED FALSE AND CORRECTED BEFORE COMMIT: that the anchor sits
at +4 on 1524 of 1525 tails (a single save's census read as the library's); that there are
four (14,60) saves (five); that one tail carries an entry (three, of one byte-identical
entry); and the ceiling justification above.

### 2026-08-18 - CS-480 - the tag-carried one-byte exemption is DERIVED from two shipped sites
Verification: `tests/save/test_byte_order_status.py` plus
`tests/save/test_byte_order_status.py::test_every_fixed_width_type_the_module_decodes_carries_a_recorded_status`,
`::test_the_tag_carried_one_byte_values_are_derived_from_the_tag_reader`,
`::test_the_reader_arm_of_the_exemption_is_load_bearing`,
`::test_the_decoder_arm_of_the_exemption_is_load_bearing`,
`::test_each_arm_of_the_tag_byte_predicate_rejects_its_own_counter` and
`::test_the_dependence_count_reports_a_wider_field_as_wider`. `clockspeed/save/objects.py` is
UNCHANGED by this item; the whole change is in the test module.

WHAT CLOSED. `_TAG_CARRIED_ONE_BYTE_VALUES`, a hand-written 1-tuple read by exactly one
assertion, is deleted. The exemption from the byte-order status key bound is now derived by
asking two shipped functions: `objects._read_tag_header` must hand back a tag-carried value
byte, AND `objects._decode_value` must build that type's value out of that byte alone. The
reproduction filed with the item - `"StrProperty": BYTE_ORDER_VACUOUS` in the mapping plus
`"StrProperty"` in the tuple, green at 31 passed over the two modules with a library - has no
test-side line left to add and reddens.

THREE INDEPENDENT REFUTATION PASSES RAN AND ALL THREE SUCCEEDED. Do not read this item as a
clean build. (1) A guard-hole pass showed the reader ALONE only moved the transcription across
the seam: the reader picks its own population by an ungraded literal, and widening it to
`Int64Property` plus one mapping line shipped `vacuous_one_byte` - the word asserting the
question is retired BECAUSE the value is one byte - for an EIGHT-byte type, reproduced by the
merger at 32 passed. That is what the decoder arm exists for. It also showed an
extract-method wrapper route that only library-backed anchors caught, so it was green on a
no-game machine; the library-free module catches it now. (2) A correctness pass measured four
prose claims FALSE, one of them a live hole: a reader reading TWO bytes at the tag offset while
advancing ONE left every control green, cursor arm included, with `vacuous_one_byte` still
shipped for a two-byte value. Closed by `_tag_byte_source_positions`, which counts how many
body positions the returned tag byte depends on. (3) A third pass against the repair found the
route recorded as CS-481 below, and a cross-term hole in the new predicate: sampling payload
dependence at one tag byte and tag dependence at one filler never samples the CROSS term, and a
decoder returning a STORED byte for one tag byte and a constant for the other was accepted. The
arms now run over the full cross product.

MUTANT GRADING, MEASURED THIS SESSION: 17 mutants, 16 DETECTED. The one MISSED is weakening the
dependence assertion itself to a tautology, which nothing else in the module can see - that is
the emptiness-guard shape CS-473 owns, and it is recorded in that test's docstring rather than
papered over. An earlier version of the controls returned FOUR MISSED of eleven, including
deleting the decoder arm outright, because the counters called the predicate directly instead of
exercising the derivation; that is what the two load-bearing controls were built for.

PROSE MEASURED FALSE AND CORRECTED IN PLACE, none to be rewritten: that the cursor excess IS the
width of the value field (a padding byte in front of a still-one-byte value reports 2); that
zeros satisfy EVERY branch (the guid-present branch is unreachable from a zero-filled body, and
a struct guid is stepped over unread); that the reader "always" walks to a value that fits (false
at small slack); and the enumeration of three ways the derivation can be wrong, which was four.

RESIDUALS FILED RATHER THAN ABSORBED. CS-481 records the route the third pass found: the key
bound subtracts the fixed-width table AND this exemption, and only the exemption is derived -
membership of the WIDTH table is self-authorising, so three lines in `objects.py` ship
`vacuous_one_byte` for an eight-byte type with `tests/save` at 1002 passed 49 skipped on a
no-game machine, byte-identical to the clean tree there. Verified by the merger in both
environments. CS-473 is ENLARGED: the repo's own `unbacked_absolutes` reports this module at 113
sentences against 70 at `fd9e8dc`, and the module is not in `FENCED_MODULES`, so nothing
enforces it. No sample repair was made - a partial hand repair with no mechanism is the register
of pardons that tool's own docstring forbids.

### 2026-08-18 - CS-421 - CORRECTION to the entry below. A third refutation landed after the commit and it was right
NOT A COMPLETION RECORD; CS-421 STAYS OPEN. This corrects the record immediately below rather
than editing it, which is what this file requires.

THE ENTRY BELOW REPORTED THREE ADVERSARIES AND TWO SUCCESSES. The third - the guard-hole lens -
returned after `07b5189` was pushed, and it SUCCEEDED. Its findings were re-measured by the
merger against the committed artifact before this correction was written.

WHAT IT BROKE, AND THE FIRST ONE IS THE SERIOUS ONE.

1. THE MEMOISED SWEEP POISONED PERMANENTLY, AND ITS OWN DOCSTRING DENIED IT IN PROSE.
   `_sweep_separability` was an `lru_cache` over a result that can be `None`, and nothing in the
   repository ever called `cache_clear` on it. One earlier call made with `_library_save_paths`
   patched empty cached that `None`, and ALL FOUR library-backed graders of the status word then
   skipped for the rest of the session - `tests/save` green at exit 0 with four skips, and
   `oracle_cannot_separate_readings` graded by nothing while reading as an ungraded machine
   rather than a defect. The vector is real: sibling modules that collect earlier already patch
   that discovery helper. Reproduced by the merger, fixed by never caching a `None` - when there
   is no library the derivation returns immediately, so that branch was never worth memoising -
   and graded by
   `tests/save/test_value_anchoring.py::test_a_library_less_call_does_not_switch_the_graders_off_for_the_session`,
   which takes a COLD cache deliberately, because the hole only exists on the first call.

2. `_TAG_CARRIED_ONE_BYTE_VALUES` IS HAND-WRITTEN AND GRADED BY NOTHING, and it is the last bound
   on which non-fixed-width words may carry a byte-order status. Reproduced at 31 passed, exit 0:
   two lines ship `vacuous_one_byte` for `StrProperty`, a LENGTH-PREFIXED type whose payload
   begins with an int32 length, retiring that int32's question with no evidence. The same tuple
   is the second line of a fifth-word route shipping `settled_uniquely` for a type nothing
   scores. The objects.py-only version of the edit IS caught, so the guard is exactly one tuple
   deep. Filed as CS-480, not repaired here.

THE TRANSFERABLE LESSON IS ABOUT SEQUENCING, NOT ABOUT THE DEFECTS. I reported a refuter as
having not returned and treated its lens as unexamined, and then committed. Both statements were
honest and one of them aged badly within the hour. A pass that has been dispatched has not been
declined; if its lens matters, the commit waits for it.

Verification: `python -m pytest tests/save -q` (expect 1047 passed). To reproduce the poisoning
on the pre-fix artifact, check out `07b5189`, patch `test_properties._library_save_paths` to
return an empty tuple, call `test_value_anchoring._sweep_separability()` once, then restore it and
call again - it stays `None`.

### 2026-08-18 - CS-421 - NOT A COMPLETION RECORD. CS-421 STAYS OPEN; route (b) ships and the close is refused
Route (b)'s artifact landed and CS-421 clause 3 still does not close. This entry exists because
the work is substantial and the REFUSAL is its result, not a failure to finish it.

WHAT SHIPPED. A fourth byte-order status word, `objects.BYTE_ORDER_ORACLE_CANNOT_SEPARATE`
(spelled `oracle_cannot_separate_readings`), recorded for `UInt32Property` in
`objects.VALUE_BYTE_ORDER_STATUS`. It separates the two states the old data could not tell
apart: `unscored`, meaning nothing looked, from a shipped oracle having been APPLIED to this
type's own values and scoring the as-stored reading and its reversal alike. `objects.py` cannot
read the library without breaking the seam, so it ships the word and a test derives the verdict -
the pattern CS-476 established for this same artifact. Adding the word turned
`test_the_status_words_are_pinned_and_distinct` RED until its grading landed beside it, which is
CS-476's vocabulary bound behaving exactly as designed.

MEASURED THIS SESSION, EVERY FIGURE RE-DERIVED FROM THE LIBRARY AND NONE CARRIED FORWARD.
`UInt32Property` yields 9 values carrying ONE distinct stored pattern, `00190000`. The shipped
int32 accumulator over it is (seen 9, high-zero 9, high-zero-swapped 9): every value carries the
small-magnitude signature under BOTH readings. `IntProperty` is separated to 2 of the 24
orderings, `UInt32Property` to 12 of 24, and `FloatProperty` is applied to 0 times because its
values decode to a float the int32 tally never sees. That last figure is load-bearing: without an
applied clause `FloatProperty` derives as "applied and undecided" on 24-of-24 agreement.

WHY IT DOES NOT CLOSE, AND THIS IS THE FINDING. Over a population of the same size and shape as
this type's own - nine copies of one stored pattern - 65280 of the 65535 possible values drive
the SAME shipped oracle to a GREEN endianness verdict, and only 255 of them, the multiples of
256, reach the undecided state recorded here. The verdict is a fact about this type happening to
carry 6400, not about the oracle meeting the type; injecting one further value with a nonzero low
byte empties the derived set. That is the `_JOIN_WORD_FLOOR` shape CS-432 exists to delete,
wearing a new spelling, and it is exactly what the ROADMAP entry forbade resting a close on. The
artifact is worth shipping and the close is not earned.

FOUND BY AN INDEPENDENT REFUTATION PASS, NOT BY THE AUTHOR, AND RE-MEASURED BEFORE IT REACHED
THIS FILE. Three adversaries ran with distinct lenses and TWO SUCCEEDED. Every correction below
landed before the record was written rather than after:

1. A SENTENCE OF MINE WAS MEASURED FALSE. The derivation's docstring said it was
   "THRESHOLD-FREE" and that "nothing here counts values". Both are false - the applied clause is
   a count of values held against zero, which is the liveness-floor shape this project already
   recorded as not being a control. The claim is now the narrower true one: no threshold is
   placed on the RELATION between the two readings.
2. THE PREDICATE ADMITTED A STATE THE SANCTIONED REASON EXCLUDES. It tested whether the
   accumulator was invariant under the reversal - but two counters are equal when BOTH are zero
   as well as when both are total, so a population carrying the signature under NEITHER reading
   derived as undecided. Displacing this census's own read by +1 produced exactly that state and
   was admitted. Tightened to the universal the ROADMAP sanctioned: EVERY value carries the
   signature under BOTH readings.
3. THE SPELLING OVER-CLAIMED. `oracle_cannot_separate` was unqualified while the oracle separates
   12 of the 24 orderings on this very population. An outside consumer sees only the string,
   which is the whole reason spellings are pinned here.
4. A NON-NEGOTIABLE 12 EXPOSURE, AND IT WAS MINE. The first version ran its entire scoring phase
   OUTSIDE every handler, in the frame still binding the discovered path list, the last save's
   raw bytes and its parsed header. A raise from the shipped decoder or tally rendered a save
   path, the save-tree account directory, a world name and the plaintext header options string.
   One of the three demonstrated routes needed NO opt-in flag, because `_score_population` takes
   the census as a PARAMETER and pytest renders a crashing frame's arguments by default. Repaired
   structurally rather than carefully - no frame in the derivation binds a path or a save - and
   `test_a_raise_in_the_scoring_phase_carries_nothing_out_of_the_walk` now grades containment.
5. MY OWN REPAIR LEFT A CONSTANT DEAD. Tightening the predicate stopped anything reading
   `_REVERSAL`, so the reading the status word is NAMED after was no longer scored. It is a
   conjunct again, and the redundancy is deliberate.

6. A MUTANT CAME BACK MISSED WHEN IT SHOULD NOT HAVE, AND IT FORCED THE LAST REPAIR. Gutting the
   tightened universal to a tautology left both modules GREEN: on this corpus that clause and the
   reversal-invariance conjunct beside it admit the SAME single word, so the library cannot tell
   them apart and no library-backed control ever will. The predicate is a named function now,
   `_carries_the_signature_both_ways`, graded by hand-authored counters in
   `test_the_signature_predicate_refuses_a_population_that_carries_neither`, which needs no game
   installed. Every other mutant was detected: dropping the word, overlapping it with the anchored
   set, adding a one-byte word the width branch swallows, adding a word outside the fixed-width
   table, respelling the status word, and marking the type anchored instead - six of six, each a
   real source edit in a licensed clone, one process per mutant.

WHAT IS STILL NOT ANCHORED, STATED RATHER THAN LEFT TO BE FOUND. Displacing this derivation's own
read still leaves 5 of the 7 offsets in [-3, +3] admitted; the tightening killed only +1 and -2.
WHICH bytes are read is constrained by
`test_no_fixed_width_value_depends_on_a_byte_outside_its_declared_extent`, which grades every
fixed-width tag including this type, so the suite holds the anchor even though this control does
not. Filed as CS-479. The repo also now carries two incompatible definitions of "an oracle scores
this type" - the dispatch keyed on the TAG WORD, and this derivation reaching the tally through
the DECODED SHAPE - which never meet in one assertion. Filed as CS-478.

Verification: `python -m pytest tests/save -q` (expect 1046 passed). The status word and its
population are `clockspeed/save/objects.py::_BYTE_ORDER_CANNOT_SEPARATE_VALUES`; the verdict is
derived by `tests/save/test_value_anchoring.py::test_the_cannot_separate_status_is_derived_from_the_oracle`
and bounded without a library by
`tests/save/test_byte_order_status.py::test_the_cannot_separate_set_is_bounded_without_a_library`.
To re-derive the refusal independently: take a nine-copy population of a single four-byte pattern,
feed it to `test_properties._tally_int32_byte_order`, and count how many values of 1..65535 make
`test_value_anchoring._int_oracle_holds` return True (65280) against how many carry the signature
under both readings (255).

### 2026-08-18 - CS-476 - CLOSED. The byte-order status is graded against what the oracles score
The per-type byte-order status no longer rests on a hand-written allowlist that nothing read.
`tests/save/test_byte_order_status.py` derives the admitted population BY EXECUTION: a type word
is admitted exactly when changing a value's BYTES, holding the word and the value's Python shape
fixed, changes something an oracle accumulates. Bookkeeping at either dispatch site turns on the
shape and the word alone, so it cannot move under that probe. The derivation is library-free -
which is measured, not asserted: an interpreter audit hook over a run recorded no path event
matching an install or a save directory, and a run with every discovery root pointed at an empty
directory passes unchanged.

FIVE ROUTES SHIPPED GREEN AND ARE RED NOW, AND THEY DIVIDE INTO TWO GROUPS THAT SHOULD NOT BE
REPORTED AS ONE. Each was a real source edit, one process per mutant, because the status mapping is
a comprehension evaluated at import and an in-process patch of its input grades a value nothing
shipped. THREE were green on the PRE-STATE tree - this module absent - each at `tests/save` 1032
passed: the over-claim, the deletion and the under-claim. THE OTHER TWO WERE GREEN WITH THE FIRST
VERSION OF THIS MODULE ALREADY PRESENT, at 1037 passed: the swallowed set member and the vocabulary
swap. So those two were holes in the GUARD rather than in the artifact it guards, they were found by
an independent refutation pass and not by the author, and the rebuild is what closed them. Reporting
all five as pre-state failures would credit this module with catching two things its first version
shipped. The over-claim - a wider type marked
`anchored_not_unique` that no branch scores. The DELETION - dropping a fixed-width type from the
mapping, which was the way OUT of the over-claim, because an absent word reads back as `None` and
the pre-existing vacuity control accepts anything not vacuous above one byte. The SWALLOWED SET
MEMBER - a one-byte word added to `_BYTE_ORDER_ANCHORED_VALUES`, which `_byte_order_status` answers
with the width branch first, so it never reaches the mapping and no test over the mapping can see
it. The VOCABULARY SWAP - exchanging the string values of `BYTE_ORDER_VACUOUS` and
`BYTE_ORDER_ANCHORED_NOT_UNIQUE`, which every control here and in `test_value_anchoring` follows by
SYMBOL, so data and yardstick move together and the shipped data claims an oracle backs two
one-byte types. And the under-claim, which no other direction catches.

A SIXTH ROUTE, FOUND AFTER THE FIRST REPAIR WAS BELIEVED FINAL, AND IT IS STRICTLY WORSE THAN THE
ONE THIS ITEM NAMES. Pinning three spellings does not BOUND the vocabulary. Adding a FOURTH status
word - measured with `settled_uniquely` against `UInt32Property`, a type no oracle scores - ships a
claim stronger than any over-claim above, and every graded direction passed VACUOUSLY on it because
they all select by the one anchored symbol. `objects.BYTE_ORDER_STATUSES` cannot close it: a
hand-written set in the same file, extended by the same edit. Measured green at `tests/save` 1040
and the full suite 2073 with the repaired module already present. The shipped mapping's VALUES are
now bounded to three literals, so a genuinely new word - CS-421's remaining half will want one -
must be added together with whatever grades it.

THE MODULE WAS REFUTED TWICE, BOTH TIMES BY SOMEONE OTHER THAN ITS AUTHOR, AND THE SECOND PASS ALSO
DISARMED THE FIRST REPAIR. The label set naming which oracles the reach count requires was
hand-written and graded by nothing: two lines inside the test module - reverting the probe pairs and
dropping one label - restored the exact previously-refuted state with the save suite green. That set
now has its NAMES read out of the dispatch bodies. THE BODIES ARE STILL LISTED, and the sentence
that first stood here - that a label could no longer be dropped without editing the dispatch - was
REFUTED BY A THIRD PASS and is corrected rather than quietly deleted.

A THIRD REFUTATION FOUND THREE MORE ROUTES AND TWO ARE CLOSED HERE. The fatal one needed no new
status word at all, so neither the vocabulary bound nor any graded direction could fire: recording
`vacuous_one_byte` against `StrProperty` - a LENGTH-PREFIXED type carrying an int32 length - retires
an int32 byte-order question with zero evidence, and shipped green at `tests/save` 1040 and across
the rest of the repo. The hole was MINE: the key-population assertion admitted any word in
`MEASURED_VALUE_TYPES`. The keys are now bounded exactly to the fixed-width table plus the one
tag-carried one-byte value. The second: `BYTE_ORDER_STATUSES` is exported in `__all__` and is what
`_byte_order_status` documents itself as returning, and bounding the mapping's VALUES did not bound
it - a word added there ships as part of the module's public answer. Now pinned equal.

THE THIRD IS NOT CLOSED AND IS FILED AS CS-477 RATHER THAN PAPERED OVER. Deleting one entry from
the reach control's hand-written dispatch-site tuple, or moving a tally call into a helper, restores
an unreached oracle with every control green. The pattern worth naming: each repair moved the
hand-written seam UP ONE LEVEL rather than removing it - label set, then site list. That third pass
also independently RE-MEASURED and CONFIRMED the correction recorded above, that the probe-pair
balance property is graded.

ONE FINDING OF THAT SECOND PASS DID NOT SURVIVE RE-MEASUREMENT, recorded because an unchecked
refutation is as bad as an unchecked claim. It reported that nothing grades the BALANCE of the two
byte probe pairs on the coarseness population filter. Measured: an unbalanced pair reddens the
neutering control, which requires the derived population to be EMPTY with the tallies dead. The
property is graded and the finding was wrong.

THE FIRST BUILD OF THIS MODULE WAS REFUTED AND THE REFUTATION IS THE RECORD WORTH KEEPING. It
claimed to read all three shipped oracles and read two: its byte probe used a single pair whose
halves both carried EQUAL interior stored bytes, which is exactly the population the
mantissa-coarseness oracle declines, and its two channels were joined by an early return that ran
the byte channel only for words the value channel had already declined. That oracle was called
ZERO times. Both faults left every other test in the module green, because the one word coarseness
scores is scored by a magnitude oracle too - so the derived population came out right for the
wrong reason. What closed it is a CALL COUNT rather than a sentence.

ONE DELIBERATE TRANSCRIPTION, NAMED AS SUCH. `test_the_status_words_are_pinned_and_distinct` pins
three string literals, which this project otherwise treats as the artifact that rots. It is
justified only because those strings ARE the interface to a reader outside this repository, and no
symbol-following control can see a spelling change. Every other control here is derived.

LIMITS RECORDED ALONGSIDE. The module grades WHICH type words an oracle judges, never whether the
judgement is CORRECT - a branch tallying byte-dependent nonsense would read here as an oracle. The
saturation floor counts candidate words and not REACHABLE ones: one-byte members can never receive
an anchored status through `_byte_order_status`, so the mapping-grading tests have fewer words that
can fail them than that floor suggests, and grading the hand-written set directly is what covers
them. `_ORACLE_TALLIES` is a hand-written label set whose failure direction is safe - an uncounted
label reports as an unreached oracle - but a FOURTH oracle added without a label is invisible to
it. The module ships OUTSIDE CS-473's prose fence, and running that fence's contract 1 against it
reports 24 unbacked quantified sentences; CS-473's note carries the enlarged surface.
Verification: `python -m pytest tests -q` gives 2073 passed, 3 skipped, exit 0, and `-n auto`
agrees at the same counts. The graded directions are
`tests/save/test_byte_order_status.py::test_no_type_is_marked_anchored_that_no_oracle_scores` and
`::test_no_type_an_oracle_scores_is_left_recorded_as_unscored`; the deletion route is
`::test_every_fixed_width_type_the_module_decodes_carries_a_recorded_status`; the set itself is
`::test_the_hand_written_anchored_set_holds_no_unscored_type`; the vocabulary is
`::test_the_status_words_are_pinned_and_distinct`; and the derivation's own reach is
`::test_the_probe_reaches_all_three_shipped_oracles`, which counts calls rather than asserting
coverage. Reproduce any route by making the named source edit in a COPY of
`clockspeed/save/objects.py` and running `python -m pytest tests/save/test_byte_order_status.py -q`.
To reproduce a PRE-STATE green instead, take it at a commit before this one: the citation block
this change adds to `objects.py` names the new module by path, so moving that module aside reddens
the package-wide citation resolver and the phase-4 gate behind it, and those failures are not the
byte-order question.

### 2026-08-17 - CS-421 - DOES NOT CLOSE. The candidate set is a singleton and clause 3 is NOT MET
This record does not close CS-421. Clauses 1 and 2 remain met and were not reopened. Clause 3
stays unmet, adjudicated 2026-08-17 by an agent that produced none of the session's work.

WHAT IS TRUE NOW. CS-469 closed. `objects.BYTE_ORDER_SURVIVING_CANDIDATES` holds one member,
derived at runtime from three oracles intersected and asserted against the shipped literal in the
direction that reddens when the constant is narrowed without the evidence narrowing. The evidence
is the operator's real save library, read-only, which is not this project's own writer.

WHAT THIS RECORD MUST NOT BE READ AS CLAIMING. It does not claim the endianness question is
settled. It does not claim any single type's byte order is pinned: the narrowing is JOINT, and
re-derived by the adjudicator from the library this run - int 6, float 6, coarse 6; int&float 2,
float&coarse 2, int&coarse 3, all three 1. No pair of oracles reaches one. It does not claim
`UInt32Property` is covered. It does not claim the question was ever data-blocked - it was not.

WHY IT STAYS OPEN. `UInt32Property` is a four-byte member of `MEASURED_VALUE_TYPES`, decoded by
the same `_decode_fixed_width`, and no oracle scores one of its bytes: the census at
`tests/save/test_value_anchoring.py` skips every type word that is not IntProperty or
FloatProperty. Carrying the joint result across to it needs the premise that this format uses one
byte order for every four-byte field, which `clockspeed/save/objects.py` refuses IN WRITING for
the declared size field in the same docstring block. It is the live 4-byte question the
session-14 refutation named under remaining work, unstruck since.

A SECOND DEFECT, MEASURED BY THE ADJUDICATOR RATHER THAN REASONED. `_BYTE_ORDER_ANCHORED_VALUES`
is a hand-written pair that no test derives from what the oracles admit. Patching the shipped
constant in-process so `UInt32Property` reads `anchored_not_unique` - claiming an oracle backs a
type nothing scores - leaves `tests/save` fully green at 1032 passed. Filed as CS-476. It is NOT
CS-459, which is the evidence table and the opposite direction.

LIMITS RECORDED ALONGSIDE. The result is joint and not per-type. `UInt32Property` is unscored.
The per-type status partition is ungraded above one byte. The SHARED LOCATOR is unanswered and
now underpins three oracles rather than two - all three are handed bytes at the same `value_at`
from the same `_read_tag_header` walk, which is closer to one oracle than to three. The shipped
singleton is ungraded on CI because the library-backed tests skip without a game, which is
CS-426's recorded gap. The mutation tables are snapshots of five runs, not standing controls. The
extent anchor stays green for any pure function of the declared extent, which is CS-455's class.
Verification: `python -m pytest tests -q -p no:randomly` gives 2065 passed, 3 skipped, exit 0 at
`2337f78`. Import `clockspeed.save.objects` and read `BYTE_ORDER_SURVIVING_CANDIDATES` for the
singleton and `VALUE_BYTE_ORDER_STATUS` for `UInt32Property` reading `unscored`. Reproduce the
ungraded-partition defect by setting that entry to `anchored_not_unique` in a copy and running
`python -m pytest tests/save -q`, which stays green.

### 2026-08-17 - CS-469 - CLOSED. A mantissa coarseness oracle separates the middle swap from the identity
The float32 population whose interior stored bytes differ separates the two orderings the
magnitude oracles could not. An ordering passes when its count of values coarse to k mantissa
bits is at least its middle-swapped partner's at EVERY k and strictly greater at some k, so there
is no threshold to tune. The population is derived at runtime from the swap itself. The census is
fenced by three structural rules - one cut of the body, one offset expression, one binding of
`value_at` - each added because the previous fence was measured bypassed: a second-slice bypass, a
displaced-offset bypass through an allowlisted reader, and a nested-scope parameter shadow, the
last because `ast.arg` is not `ast.Name`. Every closure was believed final at the time, which is
why the shipped claim is enumerated rather than absolute.
Verification: `python -m pytest tests -q -p no:randomly` gives 2065 passed, 3 skipped, exit 0 at
`2337f78`, and `pytest tests -q -n auto` agrees. The shrink is graded by
`tests/save/test_value_anchoring.py::test_the_shipped_candidate_set_is_what_the_value_oracles_cannot_separate`,
the fence by `::test_the_coarseness_census_cuts_the_body_exactly_once`. On a machine with no game
the fence, the predicate control and the population control still run; the census skips, which is
CS-426's gap. `VALUE_BYTE_ORDER_STATUS` and `_byte_order_status` are byte-identical to `86c9e54`.

### 2026-08-17 - CS-475 - CLOSED. doc_budget states its population instead of globbing it
The tool no longer measures budgeted files belonging to other checkouts. Membership is three
complementary rules shipped as data with their reasons - a `.git` boundary marker, a
registered-worktree check, and tracked-or-not-ignored - each proven load-bearing by ablation. The
registered-worktree rule is what closes the teardown window, in which `git worktree remove`
deletes the marker before the files and leaves a populated directory unmarked; a tracked-or-not-
ignored rule alone reopens it at any path outside a gitignore pattern, which was measured rather
than assumed. When git cannot answer, the tool prints a DEGRADED line naming the weaker
population rather than passing it off as the stated one, and a walked-but-untracked file is
reported rather than silently dropped.
Verification: `python tools/doc_budget.py` on a tree with live agent worktrees reports
`measured: 16` where the pre-CS-475 tool reports 18. `python -m pytest tests -q -n auto` gives
2065 passed, 3 skipped, exit 0 at `2337f78`. The control in `tests/test_doc_budget.py` builds a
real git checkout under `tmp_path` and plants at two sites; no worktree command in the suite
targets the repository the suite lives in, which is confirmable from `GIT_TRACE` output. The ast
guards enforcing that are name-based and bypassable, and say so in their own docstring.
### 2026-08-17 - CS-422 - CLOSED. The width rule now has an executable consequence on the lane that grades it
Verification: `python -m pytest tests -q -p no:randomly` gives 2035 passed, 3 skipped, exit 0,
against the 2018 passed 3 skipped the merger measured itself at `f20411c` before any slice ran.
The rule is graded by `tests/save/test_width_rule.py`, merged into `clockspeed/save/objects.py`'s
vocabulary. Reproduce the two closure predicates on a machine with NO game and NO saves: adding a
fifth entry to `objects._FIXED_WIDTH_VALUES` without a `WIDTH_SHIPPING_GROUNDS` entry reddens
`test_every_shipped_width_names_a_criterion_the_rule_admits`, and deleting `SetProperty` from
`objects.DECLINED_VALUE_READINGS` reddens
`test_every_unmeasured_word_that_ships_a_tag_extra_width_is_declined`.
An adjudicator and three adversaries ran, none having written any part of it.
**WHAT SESSION 14 REFUTED IS NOW ANSWERED, EACH BY EXECUTION.** E1: replacing
`WIDTH_SHIPPING_RULE` with "ship any width you feel like, no evidence needed" left the whole save
suite green; it now reddens `test_the_rule_prose_names_every_code_it_governs`, and with that mutant
applied the rest of `tests/save` still passes at 1014, so this module is the only thing that
catches it. E2: the rule was graded by nothing on `ubuntu-latest`, because two of three cited tests
needed a save library; the new module is 9 passed, 0 skipped, with an audit hook over `open`,
`listdir`, `scandir`, `glob` and `winreg` reporting an access count of 0 while the save root,
account directory, game directory, local config and `LOCALAPPDATA` all point at an empty directory.
E3: the family is DERIVED as `frozenset(_TAG_EXTRA_STRINGS) - MEASURED_VALUE_TYPES` rather than
listed, and `MapProperty`, `SetProperty` and `StructProperty` gained declines against reason codes
drawn from a closed set the rule names.
**THE SET-COMPARED-WITH-ITSELF DEFECT IS GENUINELY FIXED.** `WIDTH_SHIPPING_GROUNDS` is hand
authored entry by entry rather than built from the width sets, proven by injecting `Int16Property`
into `_FIXED_WIDTH_VALUES` and observing RED with "Shipped with no ground recorded".
**WHAT IS NOT GRADED, recorded so it is not rediscovered as a finding.** The rule-prose test is a
SUBSTRING SCAN: a rule text naming every code while governing nothing passes it, and so does one
that INVERTS the rule while naming every code. Both were measured passing at 9 green, and the two
shipped sentences claiming otherwise were DELETED before this record was written rather than after.
`WIDTH_RULE_EXCEPTIONS` is derived FROM `DECLINED_VALUE_READINGS`, so it grades RE-TRANSCRIPTION and
not CLASSIFICATION - reclassifying a decline onto an admitted criterion and re-deriving leaves the
module green. The deletion direction reaches only the derived population, so a declined word that
ships no tag-extra width can be deleted unnoticed. All three limits are written into the module.
**TextProperty DOES NOT BLOCK**, and the ground is not that a follow-up covers it, which is a
recorded failed path. It ships no width at all - it is in neither `_TAG_EXTRA_STRINGS` nor
`_FIXED_WIDTH_VALUES` - so a clause about when a WIDTH may ship does not govern it. The four words
that DO ship a tag-extra width with an unmeasured value reading are all guarded.
**CS-458 REMAINS OPEN AND IS LOAD-BEARING FOR THE STRICTEST READING** of "applied to every entry":
`INT32_SIZE`, `UTF16_CHAR_SIZE`, `_TAG_INDEX_FIELD_BYTES` and two byte literals still advance the
cursor from outside every table. That was fenced out of this item deliberately.
**A CORRECTION TO CS-458'S OWN NOTE AND TO THE 2026-08-16 CS-422 REFUTATION RECORD ABOVE.** Both say
the partition assertions in `tests/save/test_properties.py` are "structurally empty set differences"
that "cannot be non-empty for any edit". That overstates. The two TABLES cancel, but the test
transcribes `GUID_BYTES` and `_SOFT_OBJECT_TAIL_BYTES` as its own literals while `objects.py` spells
them inline, so renaming `GUID_BYTES` in `CURSOR_WIDTHS` alone turns `ungoverned` RED. The substance
holds - adding a word to either table leaves it green - but the universal phrasing does not, and the
test was kept and re-docstringed rather than deleted for exactly that reason.

### 2026-08-17 - CS-421 - DOES NOT CLOSE. The anchoring defect is fixed and clause 3 is NOT MET
Verification: `python -m pytest tests -q -p no:randomly` gives 2035 passed, 3 skipped, exit 0. The
new controls are `tests/save/test_value_anchoring.py`; the shipped status data is
`objects.VALUE_BYTE_ORDER_STATUS` and `objects.BYTE_ORDER_SURVIVING_CANDIDATES`. This record does not
close CS-421. Clauses 1 and 2 remain MET and were not in question. An adjudicator and three
adversaries ran, none having written any part of it.
**THE ANCHORING HALF IS FIXED.** `test_no_fixed_width_value_depends_on_a_byte_outside_its_declared_extent`
compares the shipped decoder reading in place against the same declared extent copied into a poison
padded buffer: 0 mismatches on the shipped tree, and 75136 of 75136 under a rebind displacing only
the `IntProperty` spec by +4 - the displacement that leaves the old oracle GREEN. That contrast is
itself now DERIVED by
`test_the_displacement_the_value_oracle_tolerates_is_the_one_the_anchor_catches`.
**A CORRECTION TO THE 2026-08-16 CS-421 REFUTATION RECORD ABOVE.** It says the as-read majority
survives at -2, -1, +2, +3 and +4, which is true of the MAJORITY half alone. The oracle is a
CONJUNCTION of two assertions, and measured one process per delta it is RED at -2, -1, +2 and +3 and
GREEN only at +4. A first draft of the new module widened "majority survives" into "oracle survives"
and shipped it at two sites; the merger seeded that wording in its own dispatch. Deleted, and
replaced by the derivation rather than by another sentence.
**WHY CLAUSE 3 STILL FAILS.** The two shipped value oracles do not isolate one byte order. They
leave TWO candidates, the identity and the middle swap, derived at runtime by
`test_the_shipped_candidate_set_is_what_the_value_oracles_cannot_separate` and shipped as
`BYTE_ORDER_SURVIVING_CANDIDATES`. Each oracle constrains ONE end only - the int32 oracle holds for
exactly the orderings leaving the low position alone and survives four that move the most
significant byte, the float32 oracle the mirror image - so only intersecting two one-ended
constraints fixes both ends. "Settled" is not earned.
**THE ROUTE OUT IS OPEN AND MUST NOT BE RECORDED AS DATA-BLOCKED.** The merger ruled clause 3
unsettleable because the ambiguity is a property of the corpus, and an adjudicator refuted that with
the measurement the merger had not taken: 17 of 75136 int32 values carry differing middle bytes, but
30304 of 31318 FLOAT32 values do. The information is in the library in quantity. What cannot use it
is the shipped float oracle's magnitude band, which is wide enough to admit almost every swapped
value - a weakness of the ORACLE, not of the data. A narrower discriminator over the same saves
settles this; more saves do not. Filed as CS-469.
**THE ANCHOR'S LIMIT IS AT THE CLASS, NOT AT THE CONSTANT.** It is green for ANY pure function of the
declared extent. Measured: a decoder zeroing stored byte 1 of every `IntProperty` leaves all tests in
the module green while 4484 of 75136 values decode wrong, and across the whole save suite the only
catchers are synthetic-fixture tests - CS-421's own circularity one layer along. It establishes WHICH
BYTES are read, not WHAT FUNCTION they go through. CS-455 is the degenerate case of that class.
**THE SIZE-FIELD RESULT IS A NARROWING, NOT A SETTLEMENT**, and it is about a DIFFERENT FIELD read by
a DIFFERENT READER. Its census separates the identity from its high-byte twin only on the payloads
carrying a declared size large enough to tell them apart, and that population is small; the test is
gated to SKIP rather than to fail when it is empty, which is why it does not carry the CS-432 shape.
Carrying it across to a property VALUE needs the premise that this format uses one byte order for
every int32 field, which is an assumption and not a measurement. The boundary is written down beside
the data and survived a dedicated attack. Filed as CS-470.
**PRIVACY.** The first draft held every tagged save's raw bytes in one list with a statement outside
its handler, which rendered a save-tree account directory, a world-derived save name and raw header
bytes under `pytest -l` after a forced failure. Not live on main at any point - it was reachable only
under a mutant, and the repair landed before the merge that carries this record. The sweeps now read
one save at a time with every statement inside a handler.

### 2026-08-16 - CS-454 - DOES NOT CLOSE. The redactor is materially better and clause 1 is NOT MET
Verification: `python -m pytest tests -q -p no:randomly` at `758888d` gives 2018 passed,
3 skipped, exit 0, against 2007 passed 3 skipped measured by the merger at `bb7a236` in a
real checkout before the merge. Independent adjudication ruled clause 2 MET, clause 3 MET,
clause 1 NOT MET. Reproduce the surviving leaks with
`tests/save/test_workdir.py::test_the_refusal_message_carries_no_non_digit_account_directory`
for what now passes, and the two counter-examples below for what does not.

**THIS RECORD DECLARES A NON-CLOSURE BY NAME.** Two commits shipped - `60068a9`
(`clockspeed/data/locate.py`, `tests/data/test_locate.py`, `tests/save/test_workdir.py`) and
`02523f9` (`tests/data/test_phase2_gate.py`, `tests/test_redaction_scope.py`). The code
stays: every part of it is a net improvement and the suite is green. This record does not
close CS-454, and CS-454 stays open in `ROADMAP.md`, which remains its owner file.

**WHAT WAS ACHIEVED, each measured.** The positional rule now keys on a SET of anchors -
the fixed marker, `CLOCKSPEED_SAVE_ROOT` read straight from `os.environ`, and every root
`resolve_save_root` confirmed - rather than on one fixed suffix, so the relocated-path form
is closed in all four resolution states where three of four leaked. An account directory is
remembered in every `_path_forms` rendering, closing an 8.3 leak that fired even with
`CLOCKSPEED_ACCOUNT_DIR` declared - the configuration `locate.py` documented as safe. Three
independent vacuity reasons were removed from the controls: a ten-digit fixture, a
marker-present layout in which neutering the digit backstop left 0 of 4 shapes leaking, and
an absent reset of `_RESOLVED_ACCOUNT_NAMES` that let a neighbour test carry two privacy
assertions for the whole process. An adversary ran all 11 new controls alone and in-module
under five mutant classes, 55 processes, and found ZERO divergence.

**WHY IT DOES NOT CLOSE - clause 1 says "in EVERY rendered message" and two leaks survive,
both confirmed independently by the merger and by the adjudicator.**
(1) `_remember_save_root` stores `_path_forms(str(path))` and never resolves, while
`clockspeed/save/workdir.py`'s `_resolved()` DOES resolve and its docstring says the
symlink-following is deliberate. Through a real `mklink /J` junction the two can never
agree, and the PRODUCTION refusal from `_refuse_if_forbidden` rendered a hex account
directory whole. Junctioning a save folder onto another drive is the ordinary way to
relocate one, which is exactly this item's case. **This one is a defect in the new design,
not a pre-existing instance.**
(2) The environment pass runs before the positional pass and rewrites a matching needle to
a token, injecting `<` into the account segment; `_PATH_SEGMENT_CLASS` excludes `<>` so
position cannot match, and the name pass then hunts a literal the text no longer contains.
With `USERNAME=Ada` and an account directory `Ada4f3a...`, 30 of 33 characters render in
plaintext WITH THE FIXED MARKER PRESENT. Pre-existing and unchanged from `bb7a236`.

**THE RULING ON PRE-EXISTENCE, because it will be re-argued.** A pre-existing instance of
the exact defect an item names DOES block that item's closure. CS-454's own detail entry
opens "THIS IS A PRE-EXISTING LIVE LEAK", so pre-existence is the item's subject matter and
cannot also be its defence; the acceptance is written as a state of the world rather than as
a delta; and non-negotiables 3 and 12 are invariants, not gradients.

**A THIRD DEFECT, IN THIS SESSION'S OWN FENCE.** `test_redact_calls_no_resolver_at_any_depth`
walks the transitive closure to unbounded DEPTH but grades against `RESOLVER_NAMES`, which
is `locate`'s PUBLIC surface. Four of the seven hops in the recursion cycle are private, so
a plant entering at `_read_local_config` closes the identical cycle and the fence reports
GREEN. Confirmed by the merger using the fence's own helper: a public-hop plant reports two
offenders and reddens; a private-hop plant closes the cycle and reports none. That is the
ADR 0008 shape inside a fence built to enforce ADR 0008.

**WHAT WAS NARROWED RATHER THAN INHERITED.** A breadth adversary rated the chained-exception
traceback channel HIGH. The adjudicator measured it not live: `workdir.py` builds
`SourceUnreadableError` already-redacted, so the formatted traceback renders
`<account-dir>/<save-file>`. The real gap is that `tests/save/test_world.py`'s
`_FAILURE_CASES` holds six CONTENT failures and no path-carrying one, so the traceback
surface is graded for planted content markers and never for a path. Coverage, not behaviour.

**COMMON-MODE RISK, recorded because it shaped everything downstream.** The four-state
matrix the merger built and fed to every agent varies override, digit-neighbour and
resolution order, and varies NOTHING about link indirection, username collision or
whitespace. Three of the surviving channels are invisible to it by construction, and the
junction defect sits precisely in that blind spot. Every downstream agent inherited the
merger's blind spots along with its measurements.

**ALSO CORRECTED HERE:** the merger relayed "the recursion does not occur even with a
collector wired through `_override`" as evidence the design works. That control was VACUOUS
- with the shipped code calling no resolver, wiring a collector cannot recurse, trivially.
The adjudicator built the full counterfactual and got `RecursionError`. The design rationale
is unchanged and better supported; the control the merger cited proved nothing.

### 2026-08-16 - CS-420 - CLOSED. Coverage is conserved, scope is derived, and the probe is parse-derived
Verification: `tests/save/test_absolute_claims.py` plus
`tests/save/test_absolute_claims.py::test_a_marked_claim_at_each_parse_derived_position_is_caught`,
`tests/save/test_absolute_claims.py::test_the_fenced_and_censused_scopes_are_derived_from_the_tree`,
`tests/save/test_absolute_claims.py::test_the_module_constant_exemption_stops_at_a_sentence_and_at_function_scope`,
`tests/save/test_absolute_claims.py::test_the_comment_census_separates_prose_from_a_rule_and_a_blank`,
and `tests/save/test_decode_oracles.py`, which declares the two contract markers the scope walk reads.
Adding `if True: continue` to the comment-token loop in `comment_position_mutants` reddens the first of
those; it left the full suite green before the repair.
**THIS FILE NOW OWNS CS-420's ROUND COUNT**, because the fence deliberately stops restating it and
`ROADMAP.md` holds open work only. `ROADMAP.md` recorded FIVE failed rounds of hand repair before this
session. This session's build was a sixth and was REFUTED; its repair was a seventh and passed. Every
one of the first six shipped at least one false sentence, several written by the commit correcting the
previous one - which is the failure the item exists to stop and the reason it took seven.
**THE MECHANISM.** One `ast.parse` classifies every `ast.Constant` of type `str` and every
`tokenize.COMMENT` by a POSITIVE rule into a prose kind or a single exempt kind; anything no rule claims
lands in `unaccounted` and reddens. Scope is derived by walking the tree for two markers each module
declares, with the tuples asserted equal to the walk, so unfencing takes two edits and neither is
silent - all seven deletion trials redden. The probe enumerates its positions from the same parse, and
the enumeration is asserted equal to the census population, which is what closes the truncation hole.
**THE RULES DO NOT TILE THE LANGUAGE, WHICH IS WHY THE ACCOUNT IS NOT TAUTOLOGICAL.** The same four
rules leave 95 of `test_absolute_claims.py`'s own 260 string literals unaccounted. They happen to tile
the censused module.
**GRADED TWICE BY AN ADVERSARY THAT WROTE NONE OF IT.** The first pass REFUTED clause 3 - the comment
half of the position control had no liveness floor and could be reduced to probing nothing with the
full suite green - and its prose audit found two measurably false sentences, one of them CREATED by the
commit whose stated purpose was stripping false measurements. The repair DELETED rather than reworded,
found a third false sentence neither the adversary nor the merger had listed, and tied both probes to
the census. The second pass could not break clauses 1 to 4 across 25 injection shapes, 7 deletion
trials, 13 mutants and a 279-position attribution sweep, and found every checkable replacement sentence
true. Clause 5 is satisfied by that pass.
**RESIDUALS, neither a live defect, both filed:** the census covers one module and the tie between
census and probe is RELATIVE rather than absolute (CS-461); and a pre-existing false sentence in the
censused module survives the fence because its phrasing carries no listed marker (CS-460).
**ONE EDIT WAS MADE AT MERGE TIME AND WAS NOT INDEPENDENTLY GRADED**, recorded here rather than left to
be found: closing this item removes its `ROADMAP.md` entry, which would have stranded the fence's
sentence "the count belongs to `ROADMAP.md`". That pointer was DELETED rather than repointed, and the
count moved to this record. The fence module is green on the edit.

### 2026-08-16 - CS-421 - ADJUDICATED AND REFUTED. The int32 endianness result does not hold
Verification: rebind `clockspeed/save/objects.py::_decode_fixed_width` in process so `IntProperty` alone
reads at `at + 4`, then run
`tests/save/test_properties.py::test_the_int32_byte_order_is_discriminated_by_the_stored_high_byte`.
It PASSES. No file is edited; the rebind is an in-process assignment.
This record does not close CS-421 and it withdraws the evidence the previous CS-421 record offered for
clause 3. An adjudicator and an adversary ran, neither having written any part of it, which is the pass
the earlier record declared missing by name.
**WHAT SURVIVED.** Both cited mutants reproduce exactly, digit for digit, under real pytest: `">i"`
reddens the int oracle at 7926 of 75136 and leaves the float oracle green, `">f"` reverses it at 4425 of
31318, and the counters exchange rather than drift. The non-circularity defence also survived three
independent attacks: the oracles reach only `locate.resolve_save_root`, `resolve_account_dir`, a `.sav`
glob and the installed mapping, so nothing this repo packs enters their input, and forcing discovery
empty makes both skip rather than fall back. Clauses 1 and 2 are MET. `WIDTH_ONLY_VALUE_TYPES` being
DERIVED from `EVIDENCE_FOR_VALUE_TYPE` rather than transcribed beside it is the right shape and is not
in question.
**WHAT WAS REFUTED, and it is clause 3's whole substance for `IntProperty`.** The oracle reduces each
decoded value to two bits - is the high byte zero, is the low byte zero - and owns no control tying
those bits to the value's own four bytes. Displacing the `IntProperty` value start by +4, so the decode
reads the NEXT tag's name-length prefix and never touches the int32, leaves the oracle green at 75136 of
75136 against the correct read's 70669 of 75136. It scores BETTER on bytes that are not the value,
because a name-length prefix is a small little-endian count and carries a cleaner signature than the
values do. Under that displacement the whole suite reddens 8 tests and every one is a synthetic-fixture
test. Zero library-backed tests catch it, which is the exact pathology the oracle's own docstring says
CS-421 exists to escape. The as-read majority survives at -2, -1, +2, +3 and +4, collapsing only at +1
and +8, so a rotation control testing only plus or minus one would pass and prove nothing.
**THE `FloatProperty` HALF IS NOT REFUTED.** It collapsed at every non-zero delta attempted, including
+4. That asymmetry is a finding rather than noise: float32 is anchored to its value start and int32 is
not. Its residual is that it turns on two band constants, `_FLOAT_PLAUSIBLE_LOW` and
`_FLOAT_PLAUSIBLE_HIGH`, so the claim that no measured constant appears in an assertion is true of the
int32 pivot only.
**BYTE ORDER IS NARROWED TO TWO CANDIDATES, NOT ONE.** Of the 24 permutations of the four stored bytes
the int oracle accepts 6 and the float oracle accepts 6; together they accept 2, the identity and the
middle-swap `0213`, under which the int counters are bit-identical to shipped because only the extreme
byte positions are ever inspected. "Settled" overshoots what was measured.
**AN ADDED NARROWING THAT SHRINKS THE REMAINING WORK.** `Int8Property` is one byte and `BoolProperty`'s
value is one byte in the tag, so byte order is VACUOUS for both rather than unsettled. `UInt32Property`
is the only live 4-byte question left. The shipped data does not distinguish vacuous from open, so it
currently reads as three open questions where there is one.
The sync guard between the evidence table and the oracles is ONE-DIRECTIONAL and that is filed as
CS-459. CS-455's stated premise was measured FALSE here and its entry is corrected in `ROADMAP.md`.

### 2026-08-16 - CS-422 - ADJUDICATED AND REFUTED. The partition it asserts is a set compared with itself
Verification: `python -c "from clockspeed.save import objects as o; print((o.CURSOR_WIDTHS |
o.EXTENT_WIDTHS) == (frozenset(o._TAG_EXTRA_STRINGS) | frozenset(o._FIXED_WIDTH_VALUES) |
{'GUID_BYTES','_SOFT_OBJECT_TAIL_BYTES'}))"` prints `True`, and that right-hand expression is how
`tests/save/test_properties.py::test_the_width_rule_partitions_every_shipped_width_and_declines_no_decoded_one`
builds its own `shipped` set.
This record does not close CS-422 and it withdraws the previous record's reading that the acceptance was
met on every clause. An adjudicator and an adversary ran, neither having written any part of it.
**THE PARTITION ASSERTIONS CANNOT FAIL.** `ungoverned` is `shipped - (cursor | extent)` and `phantom` is
its converse, over two sets that are provably equal because both are built from the same four sources.
Neither can be non-empty for any edit to either table.
**FIVE CURSOR-ADVANCING WIDTHS ARE UNGOVERNED**, and the asymmetry that removes the "private constants
are out of scope" defence is that `_SOFT_OBJECT_TAIL_BYTES` is private and IS classified while
`_TAG_INDEX_FIELD_BYTES` is private and is NOT. Filed as CS-458.
**THE RULE AND THE EXCEPTION RECORD HAVE NO EXECUTABLE CONSEQUENCE.** Replacing `WIDTH_SHIPPING_RULE`
with "ship any width you feel like, no evidence needed" leaves the save suite green; so does emptying
`DECLINED_VALUE_READINGS` entirely, and so does renaming one of its keys. The only assertion touching
the rule is `.strip()` truthiness and the only one touching the table is an emptiness-of-intersection
check that garbage keys satisfy more easily than real ones. Neither symbol has a production consumer.
**ALL THREE CITED TESTS ARE DECORATION.** Replacing each body with a docstring leaves the save suite
green. `tests/save/test_oracle_citations.py` resolves citations by NAME, so it catches deletion and is
blind to gutting.
**TWO OF THE THREE DO NOT RUN WITHOUT A SAVE LIBRARY**, and the survivor is the tautology, so on CI and
on any fresh clone the rule is graded by nothing at all.
**TextProperty IS NOT THE ONE HONEST EXCEPTION.** Four type words ship a tag-extra width while their
value reading is unmeasured - `ArrayProperty`, `MapProperty`, `SetProperty`, `StructProperty` - and only
`ArrayProperty` is recorded in `DECLINED_VALUE_READINGS`. The other three are declined in
`UNMEASURED_PAYLOAD_REGIONS` on sample size, the criterion `WIDTH_SHIPPING_RULE` disclaims. CS-456 was
filed against `TextProperty` alone and is rewritten in `ROADMAP.md` to the family.
**WHAT SURVIVED, and it is the item's one real result.** `clockspeed/save/objects.py:2945` is
`at = value_start + size` and it is the only tag-walk advance in the package, so an EXTENT width
genuinely cannot move the cursor. The word "cannot" stands, attacked and unbroken by both passes.

### 2026-08-16 - ROADMAP.md relocate pass - 119 per cent of budget to 57 per cent, nothing deleted
Verification: `python tools/doc_budget.py` prints `ROADMAP.md 34.1 KB against a 60.0 KB budget, 57%, OK`
and exits 0 with `VERDICT: PASS`; before the pass it printed `71.7 KB, 119%, OVER` and
`VERDICT: WARN - 1 soft budget failure(s), relocate pass due`. Every pointer resolves: 21 `**CS-nnn -
detail**` pointers in `ROADMAP.md` against 21 `### CS-nnn - detail` anchors in `docs/history_notes.md`,
zero dangling.
The cause was structural, as session 12 recorded: entries had become essays while the doc topology table
says one line per item. Each oversized entry keeps its item line, acceptance, tier, a one-sentence lead
and a pointer; the full body is relocated VERBATIM to `docs/history_notes.md`. Nothing was deleted. The
five entries whose CURRENT STATE is the load-bearing fact - CS-440, CS-441, CS-443, CS-444 and CS-448 -
had their leads hand-written so a cold session cannot read a refuted item as an unstarted one. The
relocated block is marked in `docs/history_notes.md` as the one exception to that file's
"nothing current" rule, because those entries are open work sitting there for budget reasons alone.

### 2026-08-16 - CS-421 - evidence table and byte-order oracles ship; CS-421 STAYS OPEN
Verification: `clockspeed/save/objects.py` plus
`tests/save/test_properties.py::test_every_measured_value_type_names_the_oracle_that_backs_it`,
`tests/save/test_properties.py::test_the_magnitude_oracle_covers_exactly_the_types_marked_with_it`,
`tests/save/test_properties.py::test_the_int32_byte_order_is_discriminated_by_the_stored_high_byte`,
`tests/save/test_properties.py::test_the_float32_byte_order_is_discriminated_by_plausible_magnitude`.
Patching `"IntProperty": (4, "<i")` to `">i"` reddens the int oracle at 7926 of 75136 and leaves the
float oracle green; patching `"FloatProperty"` to `">f"` reverses that at 4425 of 31318. Six mutants
against the evidence table were caught 6 of 6.
This record does not close CS-421. Clauses 1 and 2 are met: `EVIDENCE_FOR_VALUE_TYPE` records which
oracle backs each decoded type and `WIDTH_ONLY_VALUE_TYPES` is DERIVED from it, so the width-only types
are marked in shipped data rather than in prose. Clause 3 is met for `IntProperty` and `FloatProperty`
only - the two pillar 3 needs - and `BoolProperty`, `Int8Property` and `UInt32Property` remain
width-only. The oracles escape the fixture circularity because their premise is a fact about the GAME
(save int32s are counts and indices, so the stored high byte is usually zero) and they read only real
saves; the pivot is half the population, so no measured constant appears in an assertion. The unbacked
four-percentage comment above the width table was DELETED per ADR 0008: its int figures reproduced
exactly and its float figures did not, because the predicate behind them was written down nowhere.
Two defects were found and fixed on the way. `_decode_fixed_width` chose its return branch with
`code == "<f"`, keyed on a byte-order SPELLING, so a float read in any other order fell into the integer
branch where `int` of a NaN raises out of a decoder contracted to return None - that is what made the
`">f"` mutant unreachable, so fixing it is what allowed the float oracle to be proven at all. Guarded by
`tests/save/test_properties.py::test_no_fixed_width_decode_depends_on_the_byte_order_of_its_format_code`,
which derives its population from the shipped table and runs with no game installed. The sibling sweep
found no second site. **NO ADVERSARY AND NO ADJUDICATOR RAN on any of this**, and the residual the work
measured against itself is filed as CS-455.

### 2026-08-16 - CS-422 - one width rule ships and the false adverb is deleted; CS-422 STAYS OPEN
Verification: `clockspeed/save/objects.py` plus
`tests/save/test_properties.py::test_a_cursor_width_is_discriminated_and_never_on_a_majority_of_payloads`,
`tests/save/test_properties.py::test_an_extent_width_cannot_desynchronise_and_is_caught_by_disagreement`,
`tests/save/test_properties.py::test_the_width_rule_partitions_every_shipped_width_and_declines_no_decoded_one`.
Five mutants were caught 5 of 5, including a harness no-op proving the census actually applies its
mutation; `tests/save/test_oracle_citations.py` reddens on a planted dead name in the new citations.
This record does not close CS-422. `WIDTH_SHIPPING_RULE` states one rule; `CURSOR_WIDTHS` and
`EXTENT_WIDTHS` are derived from the shipped tables and asserted to partition every shipped width;
`DECLINED_VALUE_READINGS` records the exceptions against the rule. The measured finding that makes the
rule honest is that widths fall into two classes needing two oracles: a CURSOR width moves
`value_start` and is graded by terminator reach, while an EXTENT width cannot move the cursor at all
because `clockspeed/save/objects.py` advances by `at = value_start + size`, so it is graded by the
disagreement count. Grading the second class by the first oracle reports it undetectable when it is in
fact detected, which is how one file came to hold two standards. **SAMPLE SIZE WAS NEVER THE OPERATIVE
CRITERION** - that dissolves the ships-at-n=9 against declines-at-n=11976 inconsistency rather than
excusing it. The `immediately` adverb was deleted rather than hedged: measured per width, every cursor
width mis-stated by one leaves a MAJORITY of payloads still reaching their terminator, so it was false
for all six and not only the two CS-422 named. Two of this work's own errors are recorded rather than
quietly fixed - `ArrayProperty` legitimately ships a tag-extra width while its VALUE reading is
declined, so the first draft's shared key read as though the whole word were declined (renamed, and the
invariant is now asserted); and the first draft's citations sat in `#:` doc-comments, which the citation
checker cannot read, so four citations naming real tests resolved to truncated dead names and the
checker PASSED. That blind channel is filed as CS-457, and `TextProperty`'s unmeasured decline as
CS-456. **NO ADVERSARY AND NO ADJUDICATOR RAN.**

### 2026-08-16 - CS-444 - code shipped, claim refuted; CS-444 STAYS OPEN
Verification: `tests/save/test_workdir.py::test_a_forbidden_root_that_does_not_resolve_is_still_reported`,
and reverting only the consumer in `clockspeed/save/workdir.py` reddens four tests while reverting only
the producer reddens five - both byte-verified by an adversary that wrote none of it.
This record does not close CS-444. A frozen `ForbiddenRoot` with a nullable resolved path shipped and
the refusal fires, but two claims were refuted the same day: "the fail-open is closed" is too wide and
must read "closed INSIDE `_forbidden_roots`", because the sibling in `locate.resolve_save_root()` is
now MEASURED reachable and is CS-449; and the new refusal message is a personal-data echo path whose
control is vacuous, which is CS-454. Removing the redactor from that branch left the workdir suite
green, because the control's fixture uses an all-digit account name - the one shape the backstop
catches unconditionally.

### 2026-08-16 - CS-443 - unfrozen half shipped, acceptance not met end to end; CS-443 STAYS OPEN
Verification: `tests/data/test_locate.py`, where each of the six `WARN_LOCAL_CONFIG_*` codes is pinned
by its own reddening test; dropping any one `_note` call reddens exactly one named test.
This record does not close CS-443. Six loss paths in `clockspeed/data/locate.py::local_config` now
report, and a SEVENTH was found that crashed rather than discarded - `UnicodeDecodeError` is a
`ValueError`, not an `OSError`, so it escaped a function whose docstring promises it never raises,
confirmed independently against the pre-fix blob. Absence and a valid file stayed silent across 1500
measured invocations. The acceptance is still unmet because THE CHANNEL HAS NO PRODUCTION CONSUMER:
no caller in `clockspeed/`, `tools/` or `scripts/` passes the collector, so `scripts/verify_env.py`
against a malformed config still exits 0 saying nothing. The `detail` sentence is also uncontrolled -
replacing all six with a nonsense sentence left the module suite green. The frozen
`tools/precommit_gate.py` copy was READ and NOT edited; it holds no grant.

### 2026-08-16 - CS-441 - detector extended, 26 of 46 spliced shapes still escape; CS-441 STAYS OPEN
Verification: `tests/test_exception_rendering.py`; a helper rendering a suffix-annotated exception
parameter whole is now flagged, and gutting the parameter scope reddens six tests.
This record does not close CS-441. The sanctioned-helper half survived every attack, including two
combined mutants aimed at the non-vacuity proofs, which are live. The flagging half was refuted: the
annotation predicate keys on a NAME SUFFIX, so it misses 19 builtin exception types, one this repo's
own gate names as a leak type, and five exception classes this repo already defines carrying
`noqa: N818`; an unannotated parameter is invisible; and the exemption is reachable by a negated
isinstance, by an `or` short-circuit, and by a locally defined `OSError` subclass. Measured against
7165 annotations, zero real helpers sit in the blind spot today, so this is coverage rather than a
live leak.

### 2026-08-16 - CS-440 - subject threaded, acceptance unmet on both clauses; CS-440 STAYS OPEN
Verification: `tests/save/test_world.py`; forcing the registry-loss flag constant reddens three tests
and dropping the subject reddens five, both byte-verified.
This record does not close CS-440. `WorldWarning` carries a subject and
`REASON_REGISTRY_INCOMPLETE` joined `UNKNOWN_CLASS_REASONS`, and no aggregation regression was
introduced. Both acceptance clauses were refuted the same day: the subject is a usmap POSITION rather
than a class, and the class name is the datum destroyed; and the reason is a per-LOAD flag rendered as
a per-ENTRY attribute, so one injected warning gave the weaker reason to every entry and the stronger
to none. The key is also under-inclusive in the dangerous direction - an unknown property type and a
newer usmap version each drop a declared class while the flag stays false.

### 2026-08-16 - CS-448 - root cause found; it is the checkout location, not contention; CS-448 STAYS OPEN
Verification: clone this repo to a directory UNDER the system temp root and run
`python -m pytest tests -q -n auto`; the gate fails with `Interrupted: 1 error during collection` in
its level-3 child. Run the same command in a checkout that does NOT share a large ancestor with the
temp root and it passes. `tools/precommit_gate.py` is the creator and deleter of the
`clockspeed_gate_*` temp directories the collection walk trips over.
This record does not close CS-448. The merger measured 32 runs with zero failures and concluded it
did not reproduce; AN ADVERSARY REFUTED THAT AND REPRODUCED IT SIX TIMES, at both cited revisions,
because every one of the merger's runs was taken in a location where the failure is structurally
impossible. Measured chain: a checkout sharing a large ancestor with the temp root makes pytest's
rootdir for the innermost probe climb to that root, so collection walks the entire temp tree - 0.4s
from three ordinary locations against 42.7s from a clone under the temp root, with only the cwd
varied - and a sibling worker deleting a temp directory mid-walk makes `os.lstat` raise, interrupting
collection. xdist supplies only the concurrent deleter; the walk itself is single-process, so this is
NOT CPU contention and the merger's first mechanism account was wrong. What remains open is whether
a hosted runner's workspace shares that ancestor; measure `rootdir` inside a tier-2 job.

### 2026-08-16 - CS-428 - CORRECTION: a control that could prove nothing on CI failed instead of skipping
Verification: `tests/test_tmp_path_privacy.py::test_the_parallel_lane_renders_no_worker_interpreter_path`.
Locally the control still establishes the leak and the arm PASSES with no skip - 15 passed in that
module - so the skip path fires only where the hazard cannot exist.
CS-428 STAYS CLOSED; this corrects a test's verdict shape, not the redaction, which was working
correctly throughout and is unchanged by this record.
TIER-2 CI WENT RED ON BOTH HOSTED RUNNERS at `c6e1c91`, windows and ubuntu, deterministically and
NOT on the known `-n auto` flake. The failing assertion was CS-428's own POSITIVE CONTROL: it
requires the UNGUARDED parallel run to render a worker line carrying a marker, and on a hosted
runner it does not.
**THE CONTROL WAS RIGHT AND ITS VERDICT WAS WRONG.** The worker line names the worker's
INTERPRETER, so that channel carries personal data only where the interpreter itself sits under a
home directory. That holds on a developer machine and is FALSE on a hosted runner, whose
interpreter lives in a toolcache outside the runner account's home - so the hazard does not exist
there and there is nothing to redact. The control correctly determined it had proved nothing, and
then called that a defect.
A CHANNEL THE ENVIRONMENT CANNOT EXERCISE IS INCONCLUSIVE, NOT BROKEN AND NOT CLEAN. The arm now
runs its guarded assertions regardless - a deleted worker line and personal data in the region are
defects whatever the control found - and skips only the sensitivity verdict, with a reason naming
the channel, the cause, and what is consequently unmeasured. Per CS-423 the skip is loud and can
never read as a clean pass.
NOTE THE SIBLING, DELIBERATELY NOT CHANGED: the `--tb=line` arm above it carries the same shape and
PASSED on both runners, because the sandbox does sit under a home directory there. Changing a
control that works on every environment measured would be speculative, so it is recorded here
rather than pre-emptively edited.

### 2026-08-16 - CS-428 - CORRECTION: the tmp_path population figure was never true, and the merger restated it
Verification: an AST count of test functions taking `tmp_path` directly, run by the merger against
`b210396`, gives 247 across 19 files. A pytest-collection count using the claim's OWN wording -
"or a fixture derived from it" - gives 341 across the same 19 files. The figure written was 195.
Re-measured by `tests/conftest.py`'s own subject rather than by any agent's report.
CS-428 STAYS CLOSED; this corrects prose, not the fix, and the redaction itself is unaffected.
THE NUMBER WAS NEVER TRUE ANYWHERE IN THIS CHAIN. Measured by the final adversary against archived
revisions: 290 at `76f6c82`, 325 at `7478b35` - the commit that WROTE the sentence - and 341 at
`ee36d0d`. It was copied forward from a `ROADMAP.md` note that was already stale when the CS-429
builder amended it upward from an earlier figure, and it drifts every time a test is added.
**THE MERGER RESTATED IT A THIRD TIME, IN THIS FILE, AT LINE 163 OF THE ENTRY BELOW.** That entry
is append-only and stands as written; this record is the correction. The restatement happened in
the same session in which the merger twice flagged other agents for exactly this, which is worth
recording plainly rather than softening: CLAUDE.md section 4 is not hard to understand and was
still violated by the person enforcing it, because a number that arrives inside a well-evidenced
report reads as evidence rather than as a claim needing its own measurement.
THE REMEDY IS DELETION, NOT A CORRECTED NUMBER. `tests/conftest.py` now describes the population
without counting it. No corrected figure is written into prose anywhere, including here - the two
numbers above sit in a dated record, which cannot rot, and not in living text.

### 2026-08-16 - SESSION 11 - FIVE OF FIVE FIRST BUILDS WERE REFUTED, AND THE FAILURE HAD ONE SHAPE
Verification: the five squash commits `d0d6f87`, `ea4ed3e`, `0ab2007`, `7478b35`, `ee36d0d`, each
of which is a build PLUS its repair and each of whose message records what was refuted.
THIS ENTRY IS A RECORD, NOT A CLOSURE. It exists because the shape repeated and the shape is more
useful than the five instances. In four of the five, a builder MEASURED SOMETHING TRUE AND STATED
SOMETHING WIDER: the budget cannot bound one slow open, therefore it is decorative; the handler is
unreachable on 3.14, therefore it was unreachable; five happy-path indices are flagged, therefore
every index is. The fifth is the same error one level down - CS-211's fixture restated the real
doctrine sentence verbatim, so the derived path and a hardcoded path agreed BY CONSTRUCTION and the
mutant that should have separated them produced a byte-identical suite result.
THAT IS ADR 0008's OWN THESIS ARRIVING IN CODE RATHER THAN IN PROSE. A universal has a
falsification surface no local check covers. The ADR fenced the sentences; nothing fences the
INFERENCE, and the inference is where it landed five times in one session.
NOT ONE FINDING WAS VISIBLE TO A GREEN SUITE. Two were reachable only by leaving the builder's
frame entirely - reading `pyproject.toml` for the declared floor interpreter rather than trusting
the interpreter present, and reading the actual call order rather than the cited line range.

### 2026-08-16 - CS-211 - The one-owner rule on work-item IDs is enforced mechanically, not stated
Verification: `tools/drift_guard.py` guard (i), gated by `tests/data/test_drift_guard_data.py`,
specifically `test_a_planted_duplicate_is_reported_as_drift` and
`test_a_ledger_record_that_says_the_item_did_not_close_leaves_it_open`. `python tools/drift_guard.py`
reports 9 guards on the real tree.
The guard fails when an ID is OPEN in `ROADMAP.md` while carrying a closure heading in this file,
and when an ID is owned by more than one of the four owner files. It keys on a CLOSURE, not on any
mention, because a grant record legitimately names an item before it closes - and this file
contains four such records, so that is a live control rather than a synthetic one.
REFUTED ON FIRST BUILD, five findings, all confirmed and two wider than reported. The forgiveness
predicate was a document-wide phrase search, so a closure record carrying one true sentence about a
DIFFERENT item was forgiven; 25 of the 53 closure records in this file already cite another ID, so
roughly half the population was one ordinary sentence from a false green. Rewording the doctrine
sentence silently removed an owner file from the scan - OPEN, GATED and ASPIRATIONAL each. The
fixture restated the real four paths verbatim, so the hardcode mutant was byte-identical to its
control. All repaired; 13 of 13 mutants now detected, one of which restores the refuted predicate.

### 2026-08-16 - CS-435 - An undecodable usmap name is flagged, not silently substituted
Verification: `clockspeed/save/usmap.py`, gated by `tests/save/test_usmap.py`, specifically
`test_an_undecodable_name_is_flagged_rather_than_silently_substituted` and
`test_a_name_table_that_decodes_cleanly_stays_silent`.
`_Reader.text` decoded with `errors="replace"`, so a name whose bytes are not valid UTF-8 became a
DIFFERENT name, the schema published a property under the fabricated key, the body consumed
cleanly, and `warnings` was empty. It now decodes strictly and the position is flagged.
RAISE WAS REJECTED FOR A MEASURED REASON, and the first build's reason was FALSE. It cited
`world._resolve_usmap`, which `git log -S` shows has never existed in any commit, and claimed the
usmap resolves before the save's own bytes are read, which the measured call order refutes. The
decision stands on a mechanism that is true and execution-verified: `cached_usmap` holds a
module-level cache, so one bad byte ends every later load that supplies no mapping.
THE ACCEPTANCE IS MET AND THE ITEM'S STATED DEFECT IS NOT FULLY CLOSED, recorded here rather than
left for a reader to discover. A modelled class whose usmap name is undecodable STILL reports as
unmodelled; what changed is that it is no longer silent. The two sites that blunt the correlation
are in `clockspeed/save/world.py` and `clockspeed/save/objects.py`, outside this item's scope, and
are filed as CS-440. Closing on the written acceptance while naming the remainder is the honest
reading; closing silently would not be.

### 2026-08-16 - CS-437 - Two positional warning subjects, and a field documented as what it holds
Verification: `clockspeed/save/usmap.py` and `clockspeed/save/objects.py`, gated by
`tests/save/test_usmap.py::test_the_flagged_enum_name_is_flagged_at_its_own_position`,
`tests/save/test_usmap.py::test_the_repeated_schema_name_is_flagged_at_its_own_position`, and
`tests/save/test_objects.py::test_the_parent_field_documentation_states_what_the_walk_puts_there`.
THE FILED CLAIM WAS HALF RIGHT AND WAS NARROWED BY PER-SITE MEASUREMENT, twice. It named five
interpolated subject sites with two survivors; there are SEVEN, and the two extra already had
controls and already died. Both survivors now have a control and all eight sites die.
The `parent` field was documented as "None on every path today". The save library refutes that on
every component record. The sentence is DELETED rather than hedged, per ADR 0008, and the
replacement states what the walk binds without writing a count.

### 2026-08-16 - CS-438 - The save listing reports an entry it cannot read
Verification: `clockspeed/save/workdir.py`, gated by `tests/save/test_workdir.py`, specifically
`test_a_directory_that_cannot_be_listed_is_reported_not_silently_empty` and
`test_an_empty_directory_lists_nothing_and_reports_no_problem`.
A short list caused by a read failure is now distinguishable from one caused by an empty directory.
THE FILED MECHANISM WAS WRONG AND THE CORRECTION MATTERS FOR THE WHOLE FAMILY. On Python 3.14
`Path.is_file()` delegates to `os.path.isfile`, which swallows every `OSError`, so the named
handler could not fire and the entry was dropped with no exception to catch. But the DECLARED FLOOR
is 3.13, where `PathBase.is_file` re-raises outside `(ENOENT, ENOTDIR, EBADF, ELOOP)`, and CI pins
3.14 at four sites - so the difference is real and nothing in this repo would have caught it. The
shipped prose now states the scope per version and per platform.
REFUTED ON FIRST BUILD on four findings. The one worth carrying: the new detail folded absent,
not-a-directory and refused into one sentence true only of refused, and the ABSENT case fires on
every machine with no game installed. That is CS-430's defect reproduced inside the fix that cites
CS-430 as its lesson. Both sites are now split by errno and the refused case went from zero tests
to three.

### 2026-08-16 - CS-428 - pytest no longer renders the account name or a home path through `tmp_path`
Verification: `tests/conftest.py`, gated by `tests/test_tmp_path_privacy.py`, specifically
`test_a_forced_memory_error_renders_no_home_path_and_no_account_name`,
`test_a_forced_system_exit_renders_no_home_path_and_no_account_name` and
`test_the_control_run_proves_this_harness_can_see_a_leak`.
195 test functions across 19 files take `tmp_path` or a fixture derived from it. `FormattedExcinfo`
is constructed with `funcargs=True` unconditionally, so frame arguments render under the DEFAULT
traceback style and `-l` was never required - which is why this was repo-wide rather than one
module's defect. A basetemp redirect was rejected on measurement: the temp root already resolves
inside the user profile, so redirecting within it changes nothing.
REFUTED ON FIRST BUILD, and the primary finding is the one to remember. The rule set was
`lru_cache`d and seeded LAZILY by the first report carrying content, so a test that SHIPS IN THIS
REPO - one that patches `USERPROFILE` to a temp directory named `home` - installed "home" as a
session-wide redaction token AND lost the real spellings. A privacy control that FAILS OPEN,
triggered by the repo's own suite, with no attacker involved. The rules are now built once at
import, monotone by construction. The grading module could not observe it, because every arm was a
cold subprocess with an empty cache; it now runs the poisoning shape and a victim in one session.
A LIVE CI LEAK WAS FOUND AND CLOSED, not recorded as a residual: CI runs `-n auto`, and xdist
composes its worker line AFTER the worker's `makereport`, so the parallel lane leaked on every
failure. Fixed controller-side and proven on the real suite - 259 force-failed tests render 259
worker lines and zero markers, against a control showing 518 occurrences.

### 2026-08-16 - CS-436 - The two unguarded gate bounds get a report and a control
Verification: `tools/precommit_gate.py`, gated by `tests/test_precommit_gate.py`, specifically
`test_the_account_cap_reports_on_the_world_token_channel` and
`test_the_header_scan_advertises_no_bound_it_cannot_enforce`.
EDITED UNDER THE OPERATOR FROZEN-FILE GRANT recorded in this file BEFORE the edit, scoped to CS-436
alone. `git diff --name-only 76f6c82 ee36d0d` touches no other frozen path, verified on every merge.
`_save_root_dirs` failed open past its cap; all three degraded checks now report on their own
channel, and the gate is proven to still BLOCK end to end - staged violation, real commit attempt,
exit 1, HEAD unchanged - with the running gate copy discriminated by sha rather than assumed.
REFUTED ON FIRST BUILD, and one of the two findings CORRECTS THIS ITEM'S OWN ACCEPTANCE.
FIRST, the false statement SURVIVED the fix: a true truncation line was added and the false
sentence left standing beside it, so over the cap the gate exited 0 on a file carrying a world name
and token while telling the operator neither was discoverable. Renaming only the account directory,
identical bytes, made the same gate exit 1. The file already held the remedy - a guard preventing
two skip lines that disagree - and it is now extended.
SECOND, THE ACCEPTANCE WAS A FALSE DICHOTOMY. It said the budget "either bounds a single slow open
or is removed and its claim deleted". Neither is right, and the removal was a COVERAGE REDUCTION
the grant forbids: the constant is 5.0 seconds and the check breaks the loop, so at 0.40s per read
the bound stops the scan at 13 of 24 files while the removal read all 24. The third option, which
the item did not anticipate, is what shipped - THE BOUND IS REAL BUT BOUNDS SOMETHING OTHER THAN
WHAT ITS DOCSTRING CLAIMED. It is restored, and the claim now says it bounds the AGGREGATE scan and
cannot abort a read in flight.

### 2026-08-16 - CS-420 - CORRECTION: this file cited a test name that does not exist
Verification: `grep -c test_the_scanned_prose_carries_no_unbacked_absolute_claim
tests/save/test_absolute_claims.py` returns 0; the real name is
`test_the_fenced_prose_carries_no_unbacked_absolute_claim`, which returns 1.
CS-420 STAYS OPEN and this entry does not close it - it is a correction to a dead verification
pointer and a measurement record, not a completion record. Its acceptance was RESTATED on the
coverage axis by the ADR 0008 adjudication the same day and the item remains in `ROADMAP.md`.
THIS SENTENCE EXISTS BECAUSE THE GUARD SHIPPED IN THIS SESSION DEMANDED IT. `tools/drift_guard.py`
guard (i) read this record as a closure, reported CS-420 as owned by two files, and went RED on the
merger's own doc edit within minutes of being merged. That is CS-211 working on its first real
input rather than on a planted one, and the ambiguity was genuine: a record that declines to close
an item must say so ABOUT THAT ITEM BY NAME, which this one did not.
THE 2026-08-16 CS-420 ENTRY BELOW CARRIES A DEAD VERIFICATION POINTER. This file is append-only, so
the repair is this record rather than an edit to that one. A reader following that pointer finds
nothing and cannot confirm the item.
THE STRUCTURAL FACT IS WORTH MORE THAN THE TYPO, and it is why this is a record rather than a
one-line fix. NOTHING IN THIS REPOSITORY RESOLVES A CITATION WRITTEN IN `docs/`.
`tests/save/test_oracle_citations.py` scans `clockspeed/`, `tests/save/test_absolute_claims.py`
scans `tests/`, and neither reads `docs/` - so a verification pointer, which is the one field this
file makes MANDATORY, is the least guarded prose in the project. Filed as CS-442.
Found by the CS-211 builder while working inside its own write-list, reported rather than widened
into.

### 2026-08-16 - CS-436 - FROZEN-FILE GRANT ISSUED by the OPERATOR for `tools/precommit_gate.py`
Verification: this entry is the grant record CLAUDE.md section 6 requires BEFORE the edit, not a
completion record. Nothing has been edited under it at the time of writing. The item it serves is
filed in `ROADMAP.md` as CS-436; this entry does not close it.
GRANTED BY THE OPERATOR DIRECTLY, not by an adjudicator, and the distinction is recorded so a
later reader does not read this as an agent self-granting. The operator was offered the
adjudicator route of CLAUDE.md section 6 and chose to issue the grant directly, which matches
every prior grant on record in this file.
SCOPE: `tools/precommit_gate.py`, for CS-436 ALONE. THE 2026-08-15 GRANT IN THIS FILE IS SPENT -
all three of its items, CS-403, CS-209 and CS-204, are closed - and this grant does not revive it,
widen it, or extend to any other frozen path. CS-436's three parts all live inside this one file:
the `_save_root_dirs` cap reporting through the skip channel, `SAVE_HEADER_BUDGET_SECONDS` either
bounding a single slow open or being removed with its claim deleted, and the `PiiMatchers`
construction on the `--text-stdin` path.
CONDITIONS ARE THE ONES ALREADY WRITTEN IN CS-436'S ROADMAP ENTRY and are deliberately NOT
restated here, per the ruling recorded in the 2026-08-15 grant entry below: restating a condition
is how a condition drifts.
TWO CONDITIONS ARE ADDED HERE because they bind this grant rather than any clause already written.
FIRST, the `PiiMatchers` part may not be solved by dropping the construction, because
`PiiMatchers(report)` is what RECORDS THE COVERAGE SKIPS and dropping it strips the coverage
warning from that path on an unconfigured machine - that is a coverage reduction, which the CS-425
grant forbids; solve it without losing the skip, or record that it cannot be. SECOND, the gate is
proven END TO END - stage a real violation, attempt a real `git commit`, assert exit 1 and HEAD
unchanged - rather than by passing flags explicitly to the gate, and no edit under this grant may
introduce a new way for the gate to fail to START, because a gate that cannot start does not
block.

### 2026-08-16 - CS-403 - CORRECTION: the package-unreachable test was reachable on CI, and CI caught it
Verification: `tests/test_precommit_gate.py`, `run_gate_copy` and `isolated_gate_copy`. Gated by
`tests/test_precommit_gate.py::test_the_gate_starts_and_skips_when_the_package_cannot_be_imported`.
CI WENT RED ON `ddc5fe0` WHILE THE SAME SUITE WAS GREEN LOCALLY, and the divergence is the whole
lesson. `isolated_gate_copy` claimed in its own docstring that copying the gate outside the repo
made the package "genuinely out of reach". That is NECESSARY AND NOT SUFFICIENT: CI runs
`python -m pip install -e ".[dev]"`, an editable install puts clockspeed in site-packages, and
site-packages is reachable from every directory. So the import the test expects to FAIL SUCCEEDED,
no skip was printed, and the assertion that a skip appears is what failed. Locally the package is
not installed, so the test passed for a reason it did not state.
FIXED by running the isolated copy under `-S`. Proven mechanically rather than argued: with default
flags site-packages is on `sys.path`, and under `-S` it is not - and `-S` is what disables the
`site` module that processes the `.pth` file an editable install writes. It is safe because the
gate's module-scope imports are standard library only, asserted by AST in
`test_the_gate_imports_only_the_standard_library`, and ruff is located on PATH and run as a
subprocess rather than imported. A shadow planted on PYTHONPATH or in the working directory still
imports under `-S`, which the raises-on-import sibling needs.
THE BUILDER PREDICTED THIS AND LABELLED IT UNVERIFIED: its report said the test "would go red, not
silently green, on a machine where clockspeed is pip-installed. I did not test that machine state."
It was right, and the honest label is what made the diagnosis immediate. The false docstring is
replaced with the measurement rather than deleted.

### 2026-08-16 - CS-420 - MEASUREMENT RECORD. THE FENCE SHIPPED AND THE ITEM STAYS OPEN
Verification: `tests/save/test_absolute_claims.py` (new), `tests/save/test_decode_oracles.py`,
`tests/save/test_oracle_citations.py`, `clockspeed/save/objects.py` (comments only, AST-identical).
Gated by `tests/save/test_absolute_claims.py::test_the_scanned_prose_carries_no_unbacked_absolute_claim`
and its control `::test_the_scanner_reddens_on_a_reinserted_absolute`.
NOT A COMPLETION RECORD. The three named falsehoods ARE fixed and were re-verified by an adversary
that wrote none of the repair: F1 (`IT NEVER RAISES` - a forced `KeyboardInterrupt` raises at both
named sites), F2 (the join mechanism sentence), and the dead paragraph citation `662432d` created.
WHAT SHIPPED: a fence reading prose from docstrings via `ast`, comments via `tokenize` AND assert
messages via `ast.Assert.msg`. The assert-message channel was added AFTER MEASURING that docstrings
and comments alone caught only one of the two dead paragraph references. Proven to fire against the
real tree, not only controls, with each mutant byte-verified applied first - and that verification
earned its keep: the first paragraph-mutation predicate reported NOT APPLIED for a mutant that had
landed. Gutting is visible. `objects.py` is comments-only by AST dump and CS-422's docstring is
untouched.
WHY IT STAYS OPEN, measured by the adversary and re-derived independently by the merger: THREE
genuine ADR-0008 tier-1 universal claims were inserted into the fenced module, byte-verified, and
the full suite stayed byte-identically green. 19 of 22 real universal phrasings carry no listed
marker and ten prose channels are never read. 571 of 573 sentences are unread by the rule.
`FENCED_MODULES` is a hand-written tuple whose deletion leaves the suite green. The detail is in
the ROADMAP entry, which stays open; it is not restated here.
ROUND FIVE ALSO SHIPPED FALSE SENTENCES - five, deleted rather than rewritten per ADR 0008's own
remedy, in the commit `Delete five false sentences`. Two were contradicted by the module's own
passing tests. The fence flagged 0 of the 5 both before and after, which is the load-bearing
observation for the item staying open.

### 2026-08-16 - CS-434 - The node warning stops claiming a loss the save refutes
Verification: `clockspeed/save/world.py`, `tests/save/test_world.py`, `tests/save/test_usmap.py`.
Gated by `tests/save/test_world.py::test_the_absence_warning_detail_claims_no_loss_the_raising_record_refutes`.
An adversary refuted CS-430's shipped detail and the merger confirmed it independently. The detail
said a skipped node record's "placement is unrecoverable from this save". FALSE: `transform is None`
implies a levelled COMPONENT and a component closes with a parent path. Measured over the whole
local library rather than relayed: 27865 of 131607 records carry no transform, 27865 OF 27865 carry
a non-empty parent, and 27420 of those name a record in the same table that has a transform. The
builder's first join key was wrong, it caught that itself, and the corrected measurement holds.
THE DEFECT CS-430 EXISTS TO FIX, REPRODUCED INSIDE CS-430'S OWN FIX - a warning that fires is not a
warning that says something true, moved from the subject key to the detail text where nothing was
looking. The replacement names the READER as the limit and names the route it declines to follow.
DETAIL-TRUTH IS ONLY PARTLY GRADED and the new test says so: it measures the route end to end on the
fixture and then scans for one banned claim class on one code. A false sentence of another shape
still passes. Also closes the surviving positional mutant at the property subject site.
ID NOTE: this work self-allocated CS-433, which a concurrent repair had already taken; reallocated
to CS-434, confirmed free across all four owner files. IDs are permanent and never reused.

### 2026-08-16 - CS-433 - A false absence grade deleted, and eight holes closed in the reach guard
Verification: `tests/save/test_properties.py`, `tests/save/test_phase4_gate.py`. Gated by
`tests/save/test_properties.py::test_the_reach_guard_catches_every_spliced_shape` and the
retention checker's own mutation controls.
An adversary refuted CS-423's grading half and the merger confirmed both findings mechanically.
FINDING 1, A SHIPPED FALSE GUARANTEE: `objects.py` was graded `retains-no-save-bytes` while
`_Cursor.__init__` binds the decompressed body to `self._data`, constructed at two sites. The
checker missed it because it inspected only `@dataclass` fields and `_Cursor` is not one. This
project rates a false guarantee worse than the bug - a green oracle asserting a property the module
lacks is worse than the silent skip CS-423 was filed to remove. The kind was SPLIT rather than
patched, and the new one reports a violation when a module retains NOTHING, so deleting `_Cursor`
cannot leave it passing vacuously. Four mutants killed, each byte-verified applied.
FINDING 2, THE GUARD WAS BLIND TO ONE KEYWORD: `ast.AsyncFunctionDef` is not a subclass of
`ast.FunctionDef`, so an `async def` helper with a body BYTE-IDENTICAL to the existing splice
control passed cleanly. Seven of eight spliced shapes escaped. All eight are now caught, and the
two primitive lists became one with a partition asserted TOTAL rather than a second hand-maintained
list. The builder's own first draft of four splice shapes was self-defeating - they named the
locator, so the guard caught them on that instead of on the gap - and it found and fixed that.
UNRESOLVED AND RECORDED AS SUCH: the builder measured early-return gutting as ALREADY VISIBLE while
the adversary measured it identical to a pristine control. Plausible cause is scan scope. Not
settled.

### 2026-08-16 - CS-430, CS-431 - Three silent drops in the save layer are flagged
Verification: `clockspeed/save/world.py`, `clockspeed/save/usmap.py`, `tests/save/test_world.py`,
`tests/save/test_usmap.py`. Gated by
`tests/save/test_world.py::test_a_node_class_record_carrying_no_transform_is_flagged_rather_than_dropped`.
CS-430: `_node_or_none` dropped a record whose class IS a measured node class but whose transform is
None, covered by none of the module's three warning codes. The SKIP was correct and deliberate; only
the silence was the defect. A test DISTINGUISHES it from an unmodelled class, which is the
acceptance rather than merely proving a warning fired. CS-431: `_read_schema` collapsed two
conditions into one warning; `_WarningLog` keeps the FIRST detail, so a second condition sharing the
key REPLACED a true sentence with a false one. A sibling at the property-name site was found and
fixed in the same pass. Downstream reliance was verified ABSENT rather than assumed.
HONEST LIMITS, both from the adversary: `node-transform-absent` fires ZERO times across all 14 real
saves, so CS-430's branch is synthetic-only on today's corpus; and the "only consumer" sweep claim
was FALSE - `PropertyMap.__repr__` reads `.warnings` too. The consequential half stands. The
detail-text defect this pair shipped is corrected in CS-434 above.

### 2026-08-16 - CS-429, CS-423 - Four read sites contained, four redactor skips graded
Verification: `tests/save/test_synthetic.py`, `tests/save/test_phase4_gate.py`. Gated by the
per-site equivalent-mutant tests and the `_ABSENCE_MITIGATIONS` checkers.
CS-429 contained the four named sites plus TWO consumers the item did not name, which held what the
named helpers returned - containing a helper whose caller then reads uncontained achieves nothing.
Every site is graded over BOTH a non-`OSError` Exception AND `SystemExit`, and that parametrisation
is load-bearing rather than thorough: `_load_every_real_save`'s `except Exception` already held
`MemoryError` and leaked only on `SystemExit`, so a one-type grader would have passed on leaking
code. Machinery is imported rather than transcribed.
CS-423 took the second route - naming in shipped data WHY absence of value is correct - because
grading `objects.py` against a redaction oracle would assert something false, since `redact()`
strips paths and no path reaches that module. THE SILENCE HAD FOUR INSTANCES, NOT THE ONE THE ITEM
NAMED, found by the merger reading the suite's own skip list. The QUESTION was generalised over all
four and the ANSWERS kept distinct, because the modules do not share a justification. The redactor
oracle moved from 11 passed / 4 skipped to 24 passed / 0 skipped.
CS-423'S GRADING HALF WAS SUBSEQUENTLY REFUTED AND REPAIRED - see CS-433 above. It closes on the
repaired form, not on the form first merged.

### 2026-08-16 - CS-403, CS-209 - The commit gate reaches a real save header, and the skip prints
Verification: `tools/precommit_gate.py`, `tests/test_precommit_gate.py`. Merged under the operator
frozen-file grant of 2026-08-15 recorded below, whose CS-204 third was already spent - see the
CS-204 correction below. Gated by the end-to-end hooked-repository tests.
**CORRECTS AN ENTRY BELOW IN THIS FILE.** The 2026-08-14 CS-201 entry states that this gate "holds
no header parser and must not grow one (CS-400 is open), so an UNDECLARED TOKEN IS UNMATCHED AND
WILL COMMIT." CS-403 falsifies that sentence. This file is append-only, so the correction travels
as this forward pointer.
CS-403 proven END TO END rather than by passing flags: before the fix, staging a file carrying an
undeclared token discovered from a real save header COMMITTED SUCCESSFULLY. After, exit 1 with HEAD
unchanged. The import is function-local and the call site catches `BaseException`, not `Exception`,
because a mid-edit module calling `sys.exit()` at import raises `SystemExit` - the exact
fail-to-start the grant forbids. Verified with `clockspeed` broken five ways.
CS-209's skip is proven to print on the flagless path `.githooks/pre-commit` actually runs, which is
the hole it existed to close.
**REFUTED ONCE AND REPAIRED BEFORE CLOSING.** An adversary found `MAX_SAVE_ROOT_ENTRIES` truncating
SILENTLY at two of its three sites, alphabetically, before the newest-first sort - so at 513 entries
the gate exited 0, an undeclared token committed, and the operator was told "no world token is
discoverable on this machine", which is not silence but a false statement. The merger reproduced the
boundary independently. Repaired in `CS-209-B`: retention and examination are now separate bounds,
both reporting in counts only, with the newest kept. The merger verified past the cap by its own
probe. The design was chosen by measurement - `os.scandir` examined 60000 entries in 87 ms against
2.079 s for the previous shape - which is what made keeping the newest affordable.
CS-208 is not revisited; its floor raise stays denied by measurement.

### 2026-08-16 - CS-204 - CORRECTION: the ROADMAP entry outlived the closure by two days, and the 2026-08-15 grant inherited its error
Verification: no code changed. This entry corrects the RECORD. CS-204 closed 2026-08-14 in commit
`e17ba59`, whose completion entry is already in this file; `ROADMAP.md` line 30 was never removed,
so the item sat in two owner files for two days and a session plan dispatched a builder to
re-implement shipped work. That line is now deleted. Nothing above is edited - this file is
append-only and the correction travels as a forward pointer, the mechanism already used by the
2026-08-15 CS-411 correction.
RULED CLOSED by an adjudicator that produced none of the work, and re-derived by the merger rather
than relayed. The disambiguating fact is that `e17ba59` carries the implementation, its tests AND
its own ledger entry in ONE commit, so the 2026-08-14 record is not a claim about work - it is the
commit containing the work. The 2026-08-15 grant is a separate later commit, `dfa69b5`.
MEASURED, not asserted: a `--files` run of BOTH tools over a six-file violation corpus in an
out-of-repo directory under the home directory renders every path as an out-of-repo basename, with
zero hits for the home path in either separator spelling, the Windows account name, or the marker
directory component, across all FOUR channels - diagnostics, `report.checked`, `report.skipped` and
`report.notes` - at exit 1. Proven DISCRIMINATING by mutation on an exported copy: neutering the
label redactor turns 15 of 86 red, including all four channel tests on both tools. The adjudicator
additionally measured a relative out-of-repo path, a nested second repository, and `--staged` inside
it, which closes the residual the 2026-08-14 entry flagged as argued by reasoning rather than
measurement. POSIX remains unobserved.
SCOPE CORRECTION TO THE GRANT ENTRY OF 2026-08-15 IN THIS FILE: its phrase "the three OPEN items"
was true of CS-403 and CS-209 and FALSE of CS-204, which had closed the day before under its own
2026-08-14 grant, also recorded here. THE OTHER TWO THIRDS REMAIN LIVE AND UNSPENT - measured, not
assumed: `world_name_exclusions` appears 0 times in `tools/precommit_gate.py`, and the gate imports
only the standard library, so neither CS-209 nor CS-403 is built.
HOW THE ERROR PROPAGATED, recorded because it is the argument for CS-211. The grant's scope list is
exactly `grep -c "NEEDS ITS OWN FROZEN-FILE GRANT" ROADMAP.md` returning 3, and the grant says in
its own words that its conditions are "the ones already written in each roadmap entry". It also
repeats the roadmap's recusal sentence, which line 1100 of this file had already superseded. So the
grant was assembled from the stale document rather than from the tree. `WAKEUP_NOTES.md` inherited
the same three-item list into CS-425's reasoning. One stale line, read three times, by three
readers who each had reason to believe the previous one had checked.
NOT CLOSED BY THIS ENTRY: CS-403 and CS-209. FILED BY IT: CS-211, the mechanical one-owner guard
whose absence allowed this, since CLAUDE.md section 4 states the rule in prose and the only consumer
of `ROADMAP.md` under `tools/` measures its SIZE and never its content.

### 2026-08-16 - CS-420 - CORRECTION: THE CLOSURE ABOVE WAS WRONG. THE ITEM IS REOPENED
Verification: `tests/save/test_decode_oracles.py` lines cited below, each refuted by execution against the
live library on the unmutated tree. This entry corrects the CS-420 closure recorded earlier today, per this
file's rule that a wrong record gets a NEW, later record rather than an edit.
**A FINAL ADVERSARY THAT WROTE NONE OF THE WORK AUDITED MERGED `main` AND FOUND SIX FALSE SENTENCES, THREE OF
THEM WRITTEN BY THIS SESSION'S OWN COMMITS.** The four sentences the item was held open on ARE fixed and the
artifacts ARE sound - the derived test's structure survived a full attack, as did the common-mode claim, the
bare-CI-box claim, the SystemExit residual and the repaired no-install gating. What failed is the same thing
that has now failed FOUR CONSECUTIVE ROUNDS: the repair shipped new false prose.
**F1 - `IT NEVER RAISES` on `_sweep_decode_oracles` is FALSE.** A forced `KeyboardInterrupt` gives
`_sweep_decode_oracles RAISED KeyboardInterrupt`, and a second site raises too because
`test_properties._library_save_paths()` sits outside every `try`. The same file states the opposite twice, in
text this session wrote. **CS-427 repaired this exact absolute in THREE sibling docstrings in the same
session** - `test_properties.py`, `test_objects.py`, `test_world.py` each now say the absolute is false - and
the fourth survived, in the file this session rewrote most heavily.
**F2 - the join mechanism sentence is false under both readings.** It says a bijection can stay pristine over
a shrinking population while a distinct-word COUNT cannot. Measured: `ByteProperty -1` rots 5359 payloads and
leaves `join.tags` at EXACTLY 55496 and `join.words` at EXACTLY 13 - because ByteProperty is not one of the
13 joined words at all. And thinning directly with `_MAX_TAGS_PER_PAYLOAD = 4` drops the join by 3447 tags
with the word count unmoved. **The stated causal account is simply wrong: the count does not measure the
thinning, it measures whether the mutated word's own tags still parse.** MapProperty thins 0.12 per cent and
costs TWO words; ByteProperty rots 4.1 per cent and costs none.
**F3 - `_JOIN_WORD_FLOOR = 13`'s justification is false, and the floor is corpus-coupled.** Per-save distinct
joined words across the live library run 8 to 12 and **NOT ONE SAVE REACHES 13** - it is a UNION over a
growing library, never an engine constant. Within the SAME version pair, 1239 records gives 8 words and 19837
gives 11, so "playing the game leaves this alone" is exactly backwards. `NameProperty` is contributed by only
3 of 12 tagged saves, so autosave rotation retiring those three turns `assert sweep.join.words >= 13` RED ON
A CORRECT GRAMMAR. The related claim "a thinned join cannot satisfy it" is refuted by the thinning run above.
**ADR 0008 is also implicated in its own Context section**, which states the same over-applied mechanism as
F2, and its refinement's claim that "nothing above is weakened" is inaccurate because permitting a scoped
superlative in a commit message narrows FORECLOSED. Worse, the refinement classifies `WAKEUP_NOTES.md` as an
immutable record while `CLAUDE.md` defines it as a rolling two-to-three-session window that the next session
reads AS CURRENT STATE - that is a new loophole, not a closed one, and it is mine.
**A DEAD CITATION THIS SESSION CREATED:** `tests/save/test_oracle_citations.py` still names the objects.py
paragraph "beginning ``THAT JOIN IS NOT A CHECK ON THE TAG WIDTHS BELOW,``", which commit `662432d` renamed.
The citation checker passes because it resolves `tests/<path>.py::<name>` citations and not paragraph names.
**The merger's own dispatch quoted the dead name**, which is the harm demonstrating itself.
CS-419, CS-424 and CS-427 are NOT reopened by this: the audit re-derived their facts and they held, and the
`IT NEVER RAISES` finding is against the one file CS-427 did not own.

### 2026-08-16 - CS-420 - Detection claims are DERIVED by the suite; the four false sentences are gone
Verification: `tests/save/test_decode_oracles.py::test_every_tag_width_is_caught_by_a_library_backed_oracle`
builds a per-(width, oracle) attribution table at runtime by mutating each width in the SHIPPED
`objects._TAG_EXTRA_STRINGS`, and asserts no width survives, no member of the derived set is idle, and no
member measured blind has started firing. No absolute count is written anywhere in it.
ADR: `docs/adr/0008-detection-claims-are-derived-never-written.md`.
**TWO ROUNDS WERE REFUTED BY INDEPENDENT ADVERSARIES BEFORE THIS CLOSED, and the record matters more than
the fix.** Round one derived nothing: the attribution folded through `any()`, which short-circuits, so with
the reach oracle first and red on every width the other two were consulted ONLY in the pristine control -
census 7/7/1/1 - and gutting both to green no-ops left the suite passing. Round two was refuted on PROSE:
five more false sentences, one of them traced to `12b5465`, a CS-420 commit that falsified a CS-420 sentence
three rounds earlier. Fourteen false sentences were found across this item's life by agents that wrote none
of it.
**MEMBERSHIP IS DECIDED BY MEASUREMENT, NOT BY NARRATIVE:** the shipped-walk reach catches 6 of 6 widths,
the usmap join's word-diversity floor 5 of 6 (not ByteProperty), and the cross-section oracle 0 of 6 - so the
cross-section is asserted BLIND rather than counted a detector. A stated limit rather than a papered-over
one: an oracle that detects nothing cannot be protected from gutting by an attribution test.
**A REAL DEFECT THE PROSE HAD HIDDEN:** both library-backed join tests gated their skip on the SAVE library
while the usmap comes from the INSTALL, so on a machine with saves and no install they FAILED rather than
skipped. Fixed. `SystemExit` is a non-`OSError` and rendered the install path under default pytest flags; it
is now caught. `KeyboardInterrupt` is deliberately left escaping - measured, pytest renders no frame for it
without `--full-trace` - so the inherited residual note had the two backwards, in the dangerous direction.

### 2026-08-16 - CS-427 - Six sibling read and discovery sites contained, and the guard grading them un-inverted
Verification: `tests/save/test_world.py::test_the_guard_catches_a_spliced_uncontained_helper` is the control
that matters - splicing the known-bad shape into a NEW helper must turn it red. Per-site graders are
`tests/save/test_world.py::test_an_unexpected_read_failure_does_not_unwind_through_the_finder` and its
neighbours, plus the object-stage and real-save-loader graders in the same file.
**THE FIRST ROUND SHIPPED INVERTED GUARDS AND AN ADVERSARY BROKE THEM.** They keyed on the CONTAINED routes,
so a helper using an uncontained route never entered the graded set and both liveness assertions stayed true:
the pre-repair shape spliced into a new helper left 13 graders passing while it leaked the account name, the
account id and a world name. That is the ungraded-containment defect re-shipped inside the guard built to
prevent it. The guards now key on the RISKY primitives, plus a second rule for a function that calls no
primitive but takes its path from a helper whose RETURN ANNOTATION carries `Path` or `bytes` - derived from
annotations rather than from a hand-maintained list, because the list is what rots.
**`SystemExit` WAS LIVE DISCLOSURE, NOT A THEORETICAL RESIDUAL.** Measured against markers harvested from
this machine, it rendered the real Windows account name. Fifteen handlers now name `(Exception, SystemExit)`,
including four pre-existing ones with the identical hole. `Skipped` and `Failed` derive from `BaseException`,
so widening cannot swallow a skip or a failure - asserted rather than argued.
The item named four sites; six were found. The first power battery had SEVEN mutants that killed nothing -
the same defect inside the fix - and the final battery is 23 mutants applied one at a time, all red against a
pristine exit 0.

### 2026-08-16 - CS-424 - PropertyMap, Schema and PropertyEntry render structure and counts, not the name table
Verification: `tests/save/test_usmap.py::test_the_real_usmap_repr_quotes_nothing` is INSTALL-GATED and runs
against the real shipped table; `::test_the_property_map_repr_renders_structure_rather_than_its_name_table`
and `::test_a_schema_and_its_property_entries_render_structure_rather_than_names` cover the synthetic side.
NOT a non-negotiable 12 breach: these are publisher-owned asset strings, not personal data, so this was asset
echo and diagnostic noise. Recorded that way deliberately, because overstating it would be its own defect.
**THE FIRST ROUND ARGUED NO SOUND ORACLE EXISTED** - substring matching collides with the implementation's
own field labels (the longest hit is 13 characters and `PropertyEntry` is 13 characters), and skeleton
equality is brittle. **AN ADVERSARY REFUTED THAT BY CONSTRUCTION:** a withholding repr emits no string
literal at all, so the oracle is "the rendering quotes nothing" - neither substring nor skeleton, live
against the real 57985-name table. The lesson generalises past this item: a clever argument for why a check
cannot be built is refuted by building it.
Also repaired in that round: the tests said "shipped name" while using invented fixture names, borrowing the
acceptance's own word so the acceptance READ as met; the positive assertions were a zero-iteration loop under
an empty name table; and two format mutants survived all 83 tests.
**A MUTATION-HARNESS FAILURE CLASS WORTH KEEPING:** the first harness reverted a repr by deleting
`repr=False`, which does NOT overwrite a `__repr__` defined in the class body, so three mutants were reported
SURVIVED when the mutation had never applied. A mutant that fails to apply looks exactly like a test that
fails to catch. The harness now proves each mutation landed before trusting its verdict.

### 2026-08-16 - CS-419 - An unresolvable enum member index is flagged instead of silently dropped
Verification: `tests/save/test_usmap.py::test_a_truncated_enum_is_flagged_rather_than_passing_as_a_genuinely_short_one`,
plus `::test_a_failed_member_does_not_swallow_the_enum_skipped_warning`,
`::test_the_flagged_enum_is_named_by_its_own_position_not_the_first`,
`::test_a_one_member_enum_whose_only_member_is_unresolvable_is_flagged` and
`::test_a_repeated_enum_name_is_flagged_the_way_a_repeated_schema_name_is`.
Non-negotiable 7: unknown content is flagged and skipped, never silently wrong.
**THE FIRST FIX INTRODUCED A BEHAVIOUR REGRESSION AND AN ADVERSARY CAUGHT IT.** The new member warning
reused the enum-name warning's `(code, subject)` key and was added first; `_WarningLog` keeps the FIRST
detail, so a true "the enum was skipped" was replaced by a false "the enum is shorter than the file declares"
while the enum was absent entirely. Distinct subjects now. Two further test gaps were real: every fixture
built its enum at position 0, so the position was untested, and every fixture used two members, so the
single-member case - the defect itself - was untested.
A sibling was found INSIDE the edited function: a duplicate enum name collapsed unflagged while
`_read_schemas` flagged the identical loss. `WARN_DUPLICATE_ENUM` closes it. The real shipped mapping parses
byte-identically to base by full digest, and the new warning paths fire zero times on it.


### 2026-08-15 - CS-420 - MEASUREMENT RECORD, not a completion record. THE ITEM DID NOT CLOSE
Verification: `tests/save/test_decode_oracles.py` and `tests/save/test_oracle_citations.py` exist and
run; suite 1603 -> 1619 passed, 7 skipped, exit 0; `python -m mypy` 75 source files, 0 errors. This
entry exists because three measurements below would otherwise cost a future session a slice to
re-derive, and CS-412 already recorded that a measurement leaving no artifact is not resumable. The
OPEN status and the four false sentences blocking it live in `ROADMAP.md` CS-420, not here.
**MEASUREMENT 1 - THE INHERITED COMMON-MODE RISK WAS ALREADY GUARDED, AND THE PROPOSED FIX WAS NOT
ONE.** Session 7 recorded the risk as unresolved and named CS-420's usmap join as "therefore the
fix". Both halves are false. `tests/save/test_properties.py` carries its own EQUALITY reach oracle
over the real library, so under a genuine common-mode fault the copy-based walker desynchronises
against the real bytes exactly as the shipped one does: mutating each width in BOTH copies and
deleting both new oracle modules leaves the pre-existing suite red on 7 of 7, against a pristine
control that exits 0. And the join cannot be the fix - a wrong width BREAKS the walk, a broken walk
contributes NO pairs, so a bijection over a shrinking population of correct pairs stays pristine
while the grammar rots. Found by a planner, reproduced by a builder, confirmed by an adjudicator and
by two adversaries independently.
**MEASUREMENT 2 - THE 30591 / 31032 DISAGREEMENT IS RESOLVED AND NEITHER PARTY WAS WRONG.** The
one-tag-shift join is **30591 under the FLAT join** and **31032 under the SUPER-CHAIN join**, 441
tags apart, and both produce the IDENTICAL shape 8 words / 12 ids / 7 words-to-many / 6 ids-to-many.
The flat join is 55496 and the chain join is 62228, both 13-to-13 bijections with zero violations.
The shipped test asserts the SHAPE and not the count, which is correct precisely because the two
constructions differ by 441 and agree on shape - the shape is the invariant, the count is the
artifact. Do not re-open this as a two-agent disagreement; it is settled.
**MEASUREMENT 3 - `objref` 52573 versus 52457 is a type-split, not an error.** The difference is
exactly the 116 SoftObjectProperty values, and SoftObjectProperty resolves against
`ObjectRecord.instance_name` at exactly ZERO, so excluding it drops nothing that was failing and
corroborates the module's statement that those references name assets rather than saved objects.
**A DELIBERATE DEVIATION FROM A MERGER INSTRUCTION WAS ADJUDICATED AND UPHELD.** A builder was told
to write the figure 62228 into a `clockspeed/save/objects.py` docstring and REFUSED, citing
`CLAUDE.md` section 4 and the fact that the paragraph it was editing exists because two prior counts
there were deleted rather than corrected. An adjudicator that produced none of the work GRANTED the
refusal and ruled the figure belongs here, in a dated append-only file, and not in a module. The
merger instruction was self-contradictory and the builder resolved it in the only direction the
doctrine permits. Recorded because the deviation was SUBTRACTIVE - declining to add a byte - which
is why landing it before adjudication was tolerable; an ADDITIVE deviation from a direct instruction
routes through an adjudicator BEFORE it lands.

### 2026-08-15 - CS-403, CS-209, CS-204 - FROZEN-FILE GRANT ISSUED by the OPERATOR for `tools/precommit_gate.py`
Verification: this entry is the grant record CLAUDE.md section 6 requires BEFORE the edit, not a
completion record. Nothing has been edited under it at the time of writing.
GRANTED BY THE OPERATOR DIRECTLY, not by an adjudicator, and the distinction is recorded so a
later reader does not read this as an agent self-granting. CLAUDE.md section 6 names operator
approval as the thing the frozen list requires; the adjudicator route is the mechanism for an
AGENT proposing an edit, and it is not the higher authority. The operator was asked which of two
readings the grant covered and answered BOTH - the other half is the CS-425 entry below.
SCOPE: `tools/precommit_gate.py`, for the three OPEN items that each state they need their own
grant - CS-403 (the world-TOKEN half of CS-201), CS-209 (the world-name exclusion surface and the
skip channel), CS-204 (the diagnostic LABEL channel, which also covers `tools/edit_lint_check.py`,
a file that is NOT frozen and needs no grant).
CONDITIONS ARE THE ONES ALREADY WRITTEN IN EACH ROADMAP ENTRY and are deliberately NOT restated
here. CS-204's came from the adjudicator that found it and then RECUSED itself from granting it;
CS-403's lazy-import design and its fallback-on-any-exception rule are stated inside the frozen
file itself; CS-209 carries the measured denial of CS-208 that produced it. Restating a condition
is how a condition drifts, and this file has ruled that way before.
ONE CONDITION IS ADDED HERE because it binds all three rather than any one: a gate that cannot
START does not block, so no edit under this grant may introduce a new way for the gate to fail to
start, and each item is proven END TO END - stage a real violation, attempt a real `git commit`,
assert exit 1 and HEAD unchanged - rather than by passing flags explicitly to the gate, which is
what every test in the suite does today and is precisely the hole CS-209 exists to close.

### 2026-08-15 - CS-425 - FROZEN-FILE GRANT ISSUED by the OPERATOR for `.claude/settings.json`
Verification: this entry is the grant record CLAUDE.md section 6 requires BEFORE the edit, not a
completion record. Nothing has been edited under it at the time of writing. The item it serves is
filed in `ROADMAP.md` as CS-425; this entry does not close it.
SCOPE: the hook configuration in `.claude/settings.json`, to stop console windows flashing during
a session. MEASURED CAUSE, not a guess: the `PreToolUse` hook runs `python tools/precommit_gate.py
--text-stdin` on matcher `Bash|PowerShell`, so it spawns a console-subsystem `python.exe` on EVERY
shell tool call, timed at ~106 ms; Claude Code is a GUI parent with no console, so Windows
allocates one per child. `PostToolUse` and the wired git hooks are the same mechanism at lower
frequency. The `statusLine` in the operator's user-level settings already carries
`-WindowStyle Hidden`, which is evidence this was hit and patched once before.
CONDITIONS, imposed by the merger and not by the operator, because the file is a tier-0 protection
path and the defect is COSMETIC: (1) the gate's coverage may not be reduced - narrowing the
matcher or the scanned surface is forbidden, since a flashing window never justifies less secret
and PII scanning; (2) the blocking behaviour is proven END TO END both BEFORE and AFTER the edit,
per CLAUDE.md section 2.2 - hook presence is not hook firing; (3) if the chosen mechanism cannot be
PROVEN to preserve stdout and exit-code delivery to the harness, it is abandoned and the file is
left byte-identical, which is a legitimate outcome and is recorded as one rather than worked
around; (4) the real fix may be the parent's `CREATE_NO_WINDOW` spawn flag, which belongs to Claude
Code and not to this repo - if so, that is the finding, and this grant closes unused.

### 2026-08-15 - CS-411 - CORRECTION to the CS-411 entry below: two cited tests and one cited config key no longer exist
Verification: `grep -c "test_no_recorded_gap_is_blocked_by_a_frozen_file" tests/test_mypy_gate.py`
and the same for `::test_the_exclusion_is_discovery_only_not_containment` both return 0, and
`pyproject.toml` carries no `exclude` key. This file is append-only and the CS-411 entry is
not edited, so the correction travels as this pointer - the same mechanism ADR 0007 used to
correct ADR 0003. WHAT CHANGED AND WHY IT IS NOT A REGRESSION: CS-414 deleted the `exclude`
key deliberately, which made those two tests subjects without a subject; the
discovery-versus-containment lesson they carried survives as
`tests/test_mypy_gate.py::test_exclude_filters_discovery_and_does_not_contain_errors`,
rebuilt on a throwaway project so it proves a property of mypy rather than depending on
whichever local file happens to be broken. The CS-411 entry's CLAIM remains true; only three
of its artifacts moved. Recorded because an entry naming artifacts a reader cannot find is
an entry that verifies nothing, which is the whole point of the pointer rule above.

### 2026-08-15 - CS-418 - `clockspeed/save/world.py`'s two stale capability claims now derive instead of asserting
Verification: `clockspeed/save/world.py` plus
`tests/save/test_world.py::test_no_docstring_below_module_level_restates_a_measured_version_pair`
and `::test_the_world_layer_states_no_property_capability_it_does_not_own`. The first derives
its forbidden token set FROM `objects.MEASURED_BODY_LAYOUTS`, so it widens by itself if a
fifth pair is ever measured; the second is an AST assertion that `world.py` calls neither
property reader, which is a fact this module owns about itself. THAT SECOND CHOICE IS THE
LOAD-BEARING ONE: CS-413's decode landed in the same merge and made the old wording's
CONCLUSION false as well as its reason, and the replacement survived unchanged because it
asserts what this module does rather than what `objects` can do. An adversary mutation pass
killed 4 of 6 mutants here; the 2 survivors - a re-capitalised retired phrase, and a reader
reached through an aliased import - are disclosed in the test's own docstring rather than
discovered later.

### 2026-08-15 - CS-417 - an unresolvable usmap schema super index is flagged instead of rendering as a genuine no-super schema
Verification: `clockspeed/save/usmap.py` (`_read_schema`) plus
`tests/save/test_usmap.py::test_an_out_of_bounds_super_index_is_flagged_rather_than_read_as_no_super`,
which parses two bodies differing ONLY in the super index and asserts both directions -
sentinel yields no warning, out-of-bounds yields exactly one `WARN_UNRESOLVED_NAME`. Asserting
only that a warning fires would also pass an implementation that warned on every schema, so
the negative control is what makes it a test. This was a non-negotiable 7 violation of the
"never silently wrong" clause specifically, not the "never fatal" clause. It does not fire on
the shipped file, so the case had to be constructed. Independently mutation-tested by an
adversary: deleting the flag and warning-on-every-schema both go red, by the right tests.

### 2026-08-15 - CS-416 - `clockspeed/save/usmap.py` exports its three missing public constants, with a test in the direction that can catch it
Verification: `clockspeed/save/usmap.py` `__all__` plus
`tests/save/test_usmap.py::test_every_public_module_level_constant_is_exported`, proven
load-bearing by deleting each of `MAX_KNOWN_VERSION`, `USMAP_RELATIVE` and
`WARN_UNKNOWN_VERSION` in turn and observing exit 1, then restoring byte-identical source.
THE REUSABLE HALF IS THE DIRECTION: the pre-existing shape asserts every `__all__` name
exists, which is structurally incapable of catching a missing export. The new test reads the
module via AST rather than `dir()`, because `dir()` cannot separate a defined name from an
imported one and would have demanded `Path` and `Final` be exported. A repo-wide version was
scoped OUT deliberately and measured first: 3 of the 15 modules declaring `__all__` still have
gaps, 42 unexported public names, so that gate goes red on day one and each name needs its own
decision.

### 2026-08-15 - CS-415 - `tools/` is inside the repo-wide mypy gate, and the frozen commit gate came with it WITHOUT an edit
Verification: `pyproject.toml` (`files` naming clockspeed, scripts, tests, tools; scoped
`[[tool.mypy.overrides]]` for `ruff` and `yaml`) plus
`tests/test_mypy_gate.py::test_the_bare_repo_wide_invocation_reports_no_errors` and
`::test_the_files_key_names_every_authored_directory`. `python -m mypy` bare: 0 errors, 73
source files, exit 0. NO FROZEN-FILE GRANT WAS NEEDED AND THAT IS MEASURED, NOT ASSUMED:
`tools/precommit_gate.py` is now among the checked files at zero errors and is byte-identical
to its pre-session state - confirmed by an adjudicator against HEAD. Its `import-untyped` for
`ruff` was cleared from OUTSIDE by the scoped override. The scoping is EXECUTED rather than
believed: `warn_unused_configs` makes mypy name any overrides block matching nothing, a bogus
control block is named immediately, and the ruff/yaml block never is. Do not use `strict` in
an overrides block - it is accepted silently and applied GLOBALLY, and a test now executes
that trap.

### 2026-08-15 - CS-414 - `scripts/verify_env.py` type-checks clean and the inert mypy `exclude` key is deleted
Verification: `scripts/verify_env.py` plus `pyproject.toml` (no `exclude` key) and
`tests/test_mypy_gate.py::test_the_environment_verifier_is_inside_the_gate` and
`::test_the_gate_config_declares_no_exclude_key`; re-adding the key turns 4 tests red. The 5
errors were one shape - an `Optional[Path]` proven non-None by a separate boolean rather than
by a narrowing check - and were fixed by NARROWING at each point of use, not by `cast` or a
suppression. THE KEY WAS PROVABLY INERT BEFORE IT WAS DELETED, which is why this was not
tidying: `exclude` governs DISCOVERY and not the import graph, and two tools import
`verify_env` as a top-level module, so adding `tools/` to `files` cost 9 errors in 5 files
with the key and 9 in 5 without it. Neither changed function had ANY test coverage, so a green
suite was not evidence about them; equivalence was established by diffing pre- and post-change
outputs across 21 scenarios.

### 2026-08-15 - CS-404 - `build_usmap` gains a shipped-grammar mode and a `version` parameter; parts 1 and 3 were already closed
Verification: `tests/save/synthetic.py` (`build_usmap` shipped mode, `USMAP_EVIDENCE`),
`tests/save/test_usmap.py::test_the_builder_reproduces_the_shipped_bytes_it_models` and
`::test_the_real_usmap_accounts_for_its_own_length_exactly`, and
`tests/save/test_synthetic.py`. Suite 1490 -> 1530 in the slice, 1551 merged, exit 0.
THE PROOF IS AGAINST THE GAME'S BYTES, NOT AGAINST OUR LOADER, and that distinction is the
whole point of the item. The fixture builder previously wrote inline length-prefixed strings
where the shipped file writes uint32 name-table indices and emitted no property-type byte;
a session-4 builder found this and worked around it inside its own test module rather than
widen a file outside its write-list, so the builder itself was never fixed. Every real enum
and schema was rebuilt through the new mode and compared byte for byte against the shipped
file: 57985 of 57985 names, 2603 of 2603 enums, 13697 of 13792 schemas byte-identical, the
95 exceptions being exactly the schemas where property count and serializable count differ.
A round trip through `clockspeed/save/usmap.py` could not have established this - it cannot
distinguish a fixture that matches the game from one that matches our own reader.
DURABILITY WAS THE REAL FINDING. An adversarial pass produced a grammar contradicting the
shipped file in 3113 type-26 descriptors across 1873 schemas that passed all 1519 tests,
because the loader reads that field as u8-then-skip-4 and a small synthetic index leaves a
valid payload-free type in the low byte - same bytes consumed, same `PropertyMap`, same
`body_consumed`. It is now killed by the byte-comparison test above. Separately, the control
the loader cites at `clockspeed/save/usmap.py:46-53` asserted only `body_consumed <=
compressed_size`, which any early-stopping grammar satisfies; 8 of 9 loader grammar mutations
passed it. That was true at base `a518b3e` and is fixed here.
A FALSE ECHO-PATH CLAIM WAS REMOVED. `_usmap_index`'s docstring said keeping a name out of
the exception message kept it out of the log. pytest renders frame ARGUMENTS and the name is
an argument - measured, it printed twice. The docstring named the correct mechanism and then
asserted a mitigation that mechanism defeats, which is worse than silence under
non-negotiable 12 because it invites the pattern being copied to a frame carrying real save
bytes. Replaced with the true statement and pinned by a test.
EVIDENCE IS RECORDED AS DATA, per CS-412's discipline, including which field widths are
MEASURED and which are merely UNCONTRADICTED on one file. Specifically: the `(slot,
array_size)` pair is NOT discriminated by the landing oracle at all - swapping them lands
byte-identically - and is settled only by value distribution. `MAX_KNOWN_PROPERTY_TYPE = 29`
is an observed maximum, not a constraint. Every "measured" here is n=1 on one build, a
ceiling rather than a sample.
PARTS 1 AND 3 NEEDED NO WORK. Part 1 closed in `e4cd97e`. Part 3 - `repr=False` on
`SyntheticSave.blob` - closed incidentally in `44740e0` under CS-407 and `ROADMAP.md` was
stale on it; confirmed independently by the slice against the merger's claim.

### 2026-08-15 - CS-411 - `scripts/` is inside the repo-wide mypy gate, and the recorded gaps now carry oracles
Verification: `pyproject.toml` (`[tool.mypy] files`, `exclude`) and
`tests/test_mypy_gate.py::test_repo_wide_mypy_checks_the_hook_installer`,
`::test_every_authored_python_file_is_covered_or_recorded`,
`::test_no_recorded_gap_is_blocked_by_a_frozen_file`,
`::test_the_exclusion_is_discovery_only_not_containment`. Suite 1490 -> 1502 in the slice,
1551 merged, exit 0. `python -m mypy` bare: 63 -> 66 source files, 0 errors.
NO FROZEN FILE WAS TOUCHED AND NO GRANT WAS NEEDED. `scripts/install_hooks.py` already
type-checked clean, which was the roadmap's stated precondition and it held. The directory
is named rather than the one file, so a script added tomorrow is covered by default.
THE GAP WAS TOTAL, not partial: the old key resolved to 63 files, exactly the count of
`clockspeed` plus `tests`, so every file under `scripts/` and `tools/` was type-checked by
nothing, anywhere. CI runs `python -m mypy` bare (`.github/workflows/tier1.yml:250`), so
that key is the whole of the gate's authority.
FOUR DEFECTS FOUND BY AN ADVERSARIAL PASS AND FIXED BEFORE MERGE. (1) The recorded reason
for the `tools/` gap claimed a frozen-file grant was required; it is not - a scoped override
for `ruff` and `yaml` drops `tools/precommit_gate.py` off the list with no edit to it, and
mypy reports the block as an unused section when it does not match, which PROVES the scoping
rather than assuming it. Contrast `strict = true`, which is accepted and applied globally.
(2) The exclusion is a discovery filter, not containment: `tools/drift_guard.py:312` and
`tools/facts_probe.py:121` both `import verify_env`, and adding `scripts/` to `files` is what
made that import resolve, so the `tools/` rung costs 9 errors and not 4 - measured at 9 both
with and without the exclusion, so the key buys nothing there. (3) The `scripts/` coverage
test asserted set EQUALITY, forbidding the very property its own comment said the design
existed for; one clean added script turned it red and the obvious fix would have re-opened
this item. (4) The test named for the acceptance checked only that a path appeared somewhere,
so replacing the entire 17-line reason with one bare line still passed.
Every recorded gap now carries a measured error count checked against a real run.
Non-vacuity was proven both ways: reverting the `files` key turns 3 tests red naming
`scripts/install_hooks.py`, and adding a clean script to `scripts/` leaves all 12 green.

### 2026-08-15 - CS-407 - The body SKELETON grammar closes for all four version pairs, and 14 of 14 real saves load
Verification: `clockspeed/save/objects.py` (`BODY_LAYOUT_BY_PAIR`, `_read_section_size`,
`_read_level`, `_read_levelled_record`), `tests/save/synthetic.py` (`LEVELLED_LAYOUTS`), and
`tests/save/test_objects.py` plus `tests/save/test_phase4_gate.py`. Suite 1470 -> 1490, exit 0.
Re-verified by the merger against the LIVE LIBRARY independently of every builder: 14 found,
14 loaded through `load_world`, zero failures, zero warnings, 131607 records across 6171
levels, 3 distinct masked world tokens. It was 3 of 14 before this item.
METHOD, and it is the reason to trust the result. Three measurement slices derived one pair
each in worktrees. The merger then RE-IMPLEMENTED every claimed grammar from its prose in code
sharing no line with any slice probe, and reproduced each byte-exact landing independently.
Three adversaries then attacked the results with distinct lenses.
ALL THREE ADVERSARIES RETURNED REFUTED - AS WRITTEN, NOT IN SUBSTANCE. No rival broke a byte
landing or a skeleton. What they killed was over-claiming, and the SHIPPED grammar is narrower
and better than the measured one:
(1) The actor's leading run stays ONE OPAQUE SPAN. Pre-runs of 0, 4, 8 and 12 bytes all land
8 of 8 on save 52, so byte arithmetic is blind even to its width - only the unit-quaternion
check pins the transform. Splitting it into named fields would have been A REGRESSION AGAINST
ACCEPTED ADR 0003.
(2) An 8-byte section size reads as an int32 size plus a NAMED RESERVED int32, never an int64.
The reserved word is zero in 5890 of 5890 instances and the largest section is 0.45 per cent
of 2^31, so the question is undecidable now and permanently. An int64 reader would silently
compute `lo + hi * 2**32` if that word ever went non-zero and then misdiagnose the WRONG
FIELD. A non-zero reserved word FLAGS rather than crashes (non-negotiable 7).
(3) Constant blobs are skipped BY LENGTH with no claimed interior, as `BOOTSTRAP.md` already
treats the 28-byte header tail. Save 60's 70-byte run has NO observable boundary inside it -
not 4+6, not 8+2, not 16+10.
(4) The grammar is keyed on the PAIR. Header version, save version and build changelist are
all perfect predictors of every difference, so the KEY IS UNDETERMINED - the same finding
`docs/adr/0007` records for the chunk marker.
THE COLLECTABLE RULE WAS REFUTED AND REPLACED. The tag-driven rule ("present iff the level's
data entries are tagged 42") is UNDEFINED on 229 of 2244 levels of the file it was derived
from, because those levels have zero data entries, and BOTH outcomes occur among them - 227
carry a block, 2 do not. The shipped rule is SIZE-DRIVEN and needs no lookahead. Recorded
honestly in the module: it is an a-priori delimiter argument rather than a measurement,
because "always read a block" also lands byte-exact on 7 of the 8 save-52 files.
A RECORDED REASON WAS REFUTED BY RUNNING IT. `objects.py` said save 42's delta 4 was declined
because it held only if that version's declared header size ALSO excluded the collectable
count. That grammar was executed and it stops inside level 0. The size INCLUDES the block in
all 301 levels that have one; 1943 levels simply have none. One thing changed, not two.
Corrected in place rather than deleted.
THE HEADLINE IS A SKELETON AND IS WRITTEN AS ONE. Between 69.5 and 77.7 per cent of every body
is opaque property payload this grammar does not describe, and up to 81 per cent is skipped
rather than described. That is enough to WALK a save and is not the same claim as READING one.
GREEN WHILE FALSE, found by the merger at merge time: the corpus still named save 42 as its
UNMEASURED save version, so a refusal test kept passing while its own example had stopped
being true. The sentinel moved to a version nobody has measured and the rule it pins is
unchanged. Proven load-bearing rather than cosmetic: `build_body` at save version 42 now
BUILDS, so leaving the sentinel would have turned that test red.
CORPUS INDEPENDENCE, stated rather than buried: (13,42) is n=1. (14,60) is nominally n=2 but
its two bodies are byte-identical through the persistent level's first byte, so the preamble,
grid, level tail and ALL named-level framing are effectively n=1. (14,52) has 8 files but a
byte-identical preamble that is a CEILING rather than a sampling accident, three structural
twins, and a version-42 branch living in ONE file.
ALSO FIXED: `ROADMAP.md` still carried CS-409 as open although it closed on 2026-08-14 and is
ledgered above. Stale entry removed.

### 2026-08-15 - CS-408 - Save version 42's transform delta is 4, behind a VALIDATED method, and the component grammar is measured
Verification: `clockspeed/save/objects.py` `TRANSFORM_DELTA_BY_SAVE_VERSION`, and
`tests/save/test_synthetic.py::test_save_42_was_measured_rather_than_interpolated_from_its_neighbours`
plus the component coverage in `tests/save/test_objects.py`.
THE VALUE DID NOT CHANGE - THE KIND OF EVIDENCE DID, and that is the whole entry. Two earlier
sessions reached 4 and BOTH DISCARDED IT, rightly: with save 36 giving 4 and save 52 giving 8,
arriving at 4 is the PRIOR OF THE FAILURE MODE rather than corroboration. It is a measurement
now because a method that FIRST recovered 4, 8 and 8 for the three already-known versions was
then pointed at 42, and because 17763 of 17763 actors in the one real header-13 body give a
unit quaternion at shift 4 while the runner-up shift falls to 2 once scale plausibility is
included. An adversary attacked the method specifically, found its candidate sampler biased
toward the head of the body, replaced it with a full-population sweep, and the answer held.
THE FRAMING THAT BLOCKED THIS FOR TWO SESSIONS WAS WRONG. The inherited note said save 42's
DELTA was the unknown; the delta was never wrong. Its LEVEL GRAMMAR differed - section sizes
are 8 bytes wide, not 4, and each data entry carries three int32s, not one. Every prior
attempt swept deltas while holding the level grammar fixed, so no sweep could have found it.
COMPONENT GRAMMAR MEASURED across all four pairs: saves 36 and 42 encode a component as four
strings; saves 52 and 60 add an int32 before the parent string. Negative control on save 52:
with the four-string shape NO level containing a component ever closes, so this is refused by
the parse rather than preferred. The 4-byte width is pinned; its TYPE is not, because a
two-int16 reading closes byte-exactly.

### 2026-08-15 - CS-402 - All four save versions and all three header versions parse through the single entry point
Verification: `tests/save/test_phase4_gate.py::test_header_version_coverage_through_the_entry_point_is_three_of_three`,
and the merger's live-library run - 14 of 14 saves loaded through `clockspeed.save.world.load_world`
across pairs (10,36) x3, (13,42) x1, (14,52) x8 and (14,60) x2.
Unblocked by CS-408. Header version 13 was previously unreachable through the entry point
because it lives only with save version 42, which the object stage refused by design.
THE GATE TEST WAS A DELIBERATE TRIPWIRE AND IT FIRED AS DESIGNED. Its predecessor asserted
"two of three" and its docstring said it was "asserted rather than described so that CS-408
landing makes this test RED and forces the claim to be restated". It went red exactly when
expected and was RESTATED to three of three rather than loosened. Header 13's coverage now
rests on a fixture CARRYING RECORDS rather than on an empty body, which is a stronger claim
than the one it replaced.


### 2026-08-15 - CS-406 - FROZEN-FILE GRANT ISSUED for `scripts/install_hooks.py`, two sites, with conditions
Verification: this entry is the grant record CLAUDE.md section 6 requires BEFORE the edit, not a
completion record. Ruled by an adjudicator that wrote none of `scripts/install_hooks.py`, the
CS-205 grants or `tests/test_exception_rendering.py`. Every load-bearing citation was then
re-probed by the merger independently rather than accepted: both line numbers exact, the
`redact()` behaviour executed, and the sweep's own `scan_repo()` run directly.
GRANTED, both sites, WITH CONDITIONS. Site 1 is the `traceback.print_exc()` in the
`except BaseException:` handler of the `__main__` block (`:310` at this commit) - suppress by
default behind the EXISTING `CLOCKSPEED_CRASH_TRACEBACK` flag, exit code stays 1 on both paths,
the crash is never swallowed. Site 2 is the `print(f"{TOOL_NAME}: wiring {root}")` reporting line
(`:236` at this commit) - render a CONSTANT naming the location relative to the repository root,
never `root`, never `str(root)`, and specifically never `root.name`.
NEITHER EXISTING GRANT COVERS EITHER SITE, and this was checked rather than assumed. Grant A
enumerates six exception-RENDERING sites, resolved against `git show 9d24823` - neither of these
old line numbers appears among them. Grant A's two named "adjacent" leaks resolve to the git
stderr path and to the `InstallError` now at `:203-205`, both already fixed. Grant B is scoped to
one site in `tools/precommit_gate.py`.
THE ADJUDICATION REFUTED A CLAIM IN THE PROPOSAL ITSELF, and that is the most valuable part of
this record. `ROADMAP.md` asserted both sites sit on the mechanized sweep's live residual list.
MEASURED FALSE for site 2: running `scan_repo()` returns site 2 in neither the traceback list nor
the object-rendering findings, and `UNGUARDED_TRACEBACK_RESIDUALS` is traceback-keyed only. Site 2
is guarded by NOTHING today, so the "it cannot rot silently" argument does not carry it. Grant A
predicted exactly this and the prediction was never re-read - the blind spot is inherited, not new.
A dedicated test is therefore a CONDITION rather than a nicety.
THE REMEDY MAY NOT IMPORT FROM `clockspeed`, under any fallback - no `try/except ImportError`, no
`sys.path` insertion, no deferred function-local import. Three reasons, two measured. The
installer is the first thing a fresh clone runs and its own sandbox tests require exit 0 with
`clockspeed/` absent OR syntactically broken; a test already forbids a non-stdlib import
outright; and `redact()` would not work here anyway - executed by the merger, it maps
`C:\Clockspeed` to `C:/Clockspeed`, UNCHANGED, because the pinned root is not under a home
directory while the test oracle's absolute-path regex still matches. A `redact()`-based remedy
passes on a clone under a home directory and silently fails the stated acceptance on the
operator's own machine. No new import is needed: `os` and `traceback` are already imported.
EXPECTED RED, exactly one and it is required rather than a surprise:
`test_unguarded_traceback_sites_are_only_the_recorded_residuals` goes red the moment site 1 is
fixed, because the `scripts/install_hooks.py` residual key goes stale. Retiring that entry and
adding the file to the guarded tuple IS the fix. ANY OTHER RED MEANS THE REMEDY WENT PAST THE
GRANT.
UNTOUCHED by this grant, carried forward verbatim from grant A: every exit code, the hooksPath
readback check, the hook inspection rules, the wiring logic, and the two-run byte-identical
property. This grant does not widen grant A.
ALSO MEASURED, and it is why this entry cites handlers rather than only line numbers: ledger line
citations drift. Grant B cites the gate traceback at `:1670`; the detector measures it at
`tools/precommit_gate.py:1802` today.
RESIDUAL, filed rather than granted: the sweep cannot see a discovered path rendered into a
`print` outside a handler ANYWHERE in the tree. CS-406 fixes two instances by hand and nothing
prevents a third. Extending the detector is out of scope here and is NOT granted by this entry.

### 2026-08-15 - CS-400 - Clause 1 goes from SKIPPED to PASSING, and the gate now says PARTIAL rather than NOT MET
Verification: `tests/save/test_phase4_gate.py::test_a_real_world_parses_end_to_end`, which
RUNS and asserts rather than skipping. Suite at close: 1463 passed, 4 skipped, exit 0.
The gate was authored before CS-409 landed, so its clause-1 skip reason - "nothing locates it
yet" - went stale inside the same session. It is corrected rather than left, because a stale
skip reason is exactly the acting-on-a-stale-doc failure this project exists to prevent.
A TRAP WAS FOUND WHILE LIFTING THE SKIP, and it is the reason this entry exists rather than a
one-line edit. The gate author wrote "delete the skip marker and this becomes a real assertion
with no other edit". That would have FAILED: the test called `workdir.latest_save()`, which
returns the NEWEST file, and the newest save on this machine is header 14 / save 52 - an
UNMEASURED pair that `load_world` refuses BY DESIGN. The test would have gone red while the
reader behaved exactly as specified. It now selects the newest save OF A MEASURED PAIR and
skips with a reason when none exists, so the assertion is real and the refusal is not mistaken
for a defect.
CS-400 STILL MAY NOT CLOSE, and the module docstring now says PARTIAL rather than MET on
clause 1. Eleven of the fourteen saves on this machine cannot be loaded at all, and CS-402 is
separately unmet. Passing means the seam works end to end on the ONE pair it can read - not
that the save reader reads saves.

### 2026-08-14 - PII - pytest renders a failing frame's ARGUMENTS, so passing real save bytes into a raising frame is an echo path
Verification: `tests/save/test_objects.py`, `tests/save/test_phase4_gate.py` and
`tests/save/test_synthetic.py`, each real-save read now guarded. MEASURED, not reasoned
about: a marker planted in a bytes argument of a raising frame appeared TWICE in pytest's
output, with no `--showlocals` and no opt-in of any kind.
THE WORST CASE IS THE HEAD OF A SAVE FILE, which is exactly the PII-bearing header - the save
name, the options string carrying platform, account id and player display name, and the
session name, which IS the operator's world name. So a test that passes `path.read_bytes()`
into a frame that can raise prints all of that into the test log on the day it fails.
Found by the CS-409 builder, which hit it on its OWN first red run - its output printed a
real session name - and closed it for `tests/save/test_world.py`. It then stated plainly that
it had NOT audited sibling modules, which is what made the sweep possible. The merger swept
and found two more live sites and fixed all three: the object walk's real-save acceptance
test, the gate's real-save partial, and the corpus shape anchor.
The remedy is the same in each: catch, convert to closed-vocabulary scalars - a stage name
and an exception CLASS name - and fail with `pytrace=False`, so nothing raises with the bytes
in flight. This failure class is invisible to every green run BY CONSTRUCTION, because it
only fires on failure, which is exactly when nobody is reading carefully.

### 2026-08-14 - CS-409 - load_world routes to the LEVELLED body walk, and a real world parses END TO END
Verification: `clockspeed/save/world.py` plus `tests/save/test_world.py`. Re-verified by the
merger against the live library independently of the builder: **3 of 14 real saves now load
end to end into a `WorldModel`** - 25769, 25769 and 25725 records, 202 levels, 2774 nodes -
and the other 11 are refused with a clean `WorldLoadError`.
INDEPENDENT CONFIRMATION OF CS-401 ON REAL DATA, which no fixture could supply: all three
loaded saves render the SAME masked token digest while carrying DIFFERENT record counts. Two
saves of one world share a token; the world changed between them. That is the token-stability
claim measured on the game's own output rather than on a corpus.
THE ROUTING DECISION AND WHY THE ALTERNATIVES WERE REJECTED, because this is the seam:
`body_layout` is a keyword-only parameter DEFAULTING TO LEVELLED, so the safe path is the one
a caller gets by not thinking. Routing on `MEASURED_BODY_LAYOUTS` was rejected under both of
its readings - "unmeasured means flat" sends a real header-14 save to the flat reader, which
is the silently-wrong world this item exists to remove, and "unmeasured means raise" deletes
the whole flat corpus including `SAVE_CROSS`, which exists in no real file and can never be
rescued. A fixture-shape probe was rejected as the banned silent fallback in disguise. An
unrecognised layout raises `ValueError` and deliberately NOT `WorldLoadError`, so catching a
bad save cannot swallow a typo, and the message renders the allowed set, never the supplied
value.
Five mutations, all caught - including the one that matters, a silent try-levelled-then-flat
fallback, which the two refusal tests kill exactly as designed.

### 2026-08-14 - CS-400 - Phase 4 acceptance gate: three of four clauses MET, and the gate says the phase MAY NOT CLOSE
Verification: `tests/save/test_phase4_gate.py`. Suite at close: 1462 passed, 5 skipped,
exit 0, from 734 at session start.
**CLAUSE 1, "a real world parses", IS NOW MET FOR ONE OF FOUR VERSION PAIRS** - see the
CS-409 entry above - and the gate's own end-to-end test still carries the CS-407 skip because
it was authored before CS-409 landed. THE PHASE STILL MAY NOT CLOSE: three of the four real
version pairs cannot be read at all, and CS-402 is separately unmet.
CLAUSE 2, corrupted save: MET. All eight corruption helpers across four fixtures and both
framings raise `WorldLoadError`, never a bare `struct.error`, `zlib.error`, `IndexError` or
`MemoryError`.
CLAUSE 3, truncated save: MET. All six boundaries in both scopes raise - and the gate records
that they raise at DIFFERENT STAGES rather than forcing a uniform answer: file scope at the
header and chunk layers, body scope at the OBJECT layer, with a companion proving the chunk
layer accepts the body-scope damage first, because `save_with_truncated_body` recompresses
and the damage is invisible there by construction.
CLAUSE 4, the save directory is never opened for write: MET, by three independent signals
each with a companion proving the detector DETECTS. The runtime audit hook in a child process
caught a mode-based write, a flag-based `os.open` THROUGH THE FLAG CHANNEL, and `os.remove` -
and its mandatory non-zero read-count assertion recorded 1 read open, without which the whole
test passes for a `load_world` that does nothing. The filesystem fingerprint went red on a
one-byte change and on a planted sidecar file. The static AST gate caught an injected
construct in all six modules at the right line, went red on a new write in `workdir.py`, and
went red on a REMOVED write there too, so it cannot silently lose its subject.
THE GATE CAUGHT AN OVER-CLAIM IN ITS OWN FIRST DRAFT and one in the ROADMAP. Its own
assertion that all three header versions are covered through the entry point was false - only
10 and 14 are reachable, because header 13 lives solely in `SAVE_V42`, which the object stage
refuses. The roadmap line making the same claim was written by the merger and is corrected.
FOUND AND NOT FIXED, reported rather than silently patched: `tests/save/test_world.py`'s
`_literal_mode` helper reads `node.args[0]` as the mode unconditionally, which is correct for
`path.open("rb")` and wrong for the builtin `open(path, "rb")` where `args[0]` is the path.
Latent only because `world.py` uses the method form, and it fails in the SAFE direction.
Also recorded: `tools/drift_guard.py` guard (c) enumerates tracked files only, so it did not
scan the gate module while it was untracked, and its PASS said nothing about it. The merger
verified that file separately - 0 non-ASCII bytes, no home path, no drive-letter path.

### 2026-08-14 - CS-407 PARTIAL - A real save body is a LIST OF LEVELS, not an object table, and one of four version pairs is now derived
Verification: `clockspeed/save/objects.py` `parse_body` plus `tests/save/synthetic.py`
`build_levelled_body` and `tests/save/test_objects.py`. Re-verified by the merger against the
LIVE LIBRARY independently of the builder: 3 of 14 real saves parse to 202 levels with 0
unknown classes and 0 warnings, and the other 11 are REFUSED EAGERLY with
`UnsupportedBodyLayoutError` rather than crashing or returning a wrong number.
THE FINDING THAT REFRAMES THE PHASE. A real body does not open with an object table at all.
It opens with a version-dependent preamble and then carries a LIST OF LEVELS, each with its
own record table, collectable list and payload section. So "start the table at body offset 0"
could never have worked - the fix was not an offset, and no amount of tuning one would have
found it.
DERIVED AND ORACLE-CONFIRMED: header 10 / save 36. Grammar: an int32 level count, then that
many NAMED levels, then one UNNAMED persistent level, then a trailing int32. Each level
carries a name, a header section size, a record count, its records, a collectable count and
its pairs, a data section size, an entry count, a length-prefixed payload per entry, and a
second collectable block. Confirmed on ALL THREE real files of that pair, each landing on its
EXACT final byte with zero warnings - and one of the three carries different world state,
25725 records against 25769, so it is independent confirmation rather than the same file read
three times.
THE REFUTATION IS THE MOST VALUABLE PART OF THIS ENTRY. The builder briefly had save version
42's transform delta at 4: with delta 4, exactly 12 records close level 0 on its declared
size, and every other value from 0 to 20 fails. IT DID NOT SHIP IT. That reading holds only
if save 42's header section size ALSO excludes the collectable count, which both neighbouring
versions contradict - two unmeasured assumptions propping each other up. And 36 giving 4
beside 52 giving 8 makes 4 exactly the value that LOOKS derived. Save 42's delta remains
UNMEASURED. This is the second time this session a builder discarded a plausible number
rather than publish one a shaky method produced.
A REAL SAVE REFUSED ITSELF, and no synthetic fixture could have caused it: a count ceiling
`MAX_OBJECTS` had been applied to a payload BYTE LENGTH, so the first real save the walk ever
saw raised `ObjectBudgetExceededError` at byte 8124002. Fixed with a separate
`MAX_OBJECT_DATA_BYTES`. That defect was invisible to every fixture and visible immediately to
one real file.
THE FLAT LAYOUT IS KEPT DELIBERATELY, WITH ITS CLAIM CORRECTED. `build_body` writes a shape no
real save has. Its fixtures stay, because they pin offset arithmetic and version dispatch -
`SAVE_CROSS` above all - and moving them would put a large body of existing assertions onto
new bytes for no gain. What changed is what passing them PROVES: evidence about dispatch, and
NOT evidence that anything can read a real save.
ALSO MEASURED: the component record grammar is four strings with no transform block, which
confirms the prior belief rather than replacing it; save 36's delta is 4 across 201 of 201
populated sections and save 52's is 8 across 54 of 54.
UNCLOSED, and each recorded with what stopped it so a later slice resumes from evidence
rather than from scratch: header 13 / save 42 (level grammar not closed, preamble ends at a
measured offset), header 14 / save 52 (all 134 named levels walk; the persistent level's first
COMPONENT record is the single blocker, and this is the nearest pair to completion), and
header 14 / save 60 (level 0 walks, a 78-byte inter-level separator is measured, and the full
walker landed 8 bytes off - not chased to ground). `ObjectRecord.body_offset` and
`body_length` remain 0, because that the k-th payload belongs to the k-th record is an
assumption nothing measured, and a plausible pairing was deliberately not carried.
CREATES CS-409, a LIVE DEFECT rather than unfinished work: `world.py` still calls
`parse_object_headers`, which reads the flat layout, so `load_world` against a real body
returns an empty or wrong world rather than an error - the one outcome non-negotiable 7
forbids. The builder flagged this as a seam decision it would not make unilaterally.

### 2026-08-14 - CS-205 - A MECHANIZED repo-wide sweep asserts no tracked module renders an exception OBJECT into a message
Verification: `tests/test_exception_rendering.py` plus `scripts/install_hooks.py`,
`tools/precommit_gate.py`, `tools/edit_lint_check.py`, `tools/memory_sync.py` and
`clockspeed/data/version.py`. Merged under the two frozen-file grants recorded above.
Suite 1067 -> 1088, exit 0.
The detector ENUMERATES tracked and untracked-but-not-ignored `*.py` rather than reading a
list. The enumeration was widened beyond `--cached` for a measured reason: `--cached` cannot
see a module until it is committed, INCLUDING THE DETECTOR ITSELF on the commit that adds it,
which the builder hit as a genuine red.
THE RED NAMED 13 REAL SITES IN THE REAL TREE, not a fixture, matching the adjudicator's
independent AST sweep on file and line. It matched only after the TREE CORRECTED THE BUILDER
TWICE, and both corrections are worth keeping: (1) the builder's first sweep found 12 and
missed `tools/edit_lint_check.py:82`, where the object is the DEFAULT of a
`getattr(exc, "problem", exc)` - it reads like a field access and renders the whole object
whenever the field is absent, so the adjudicator was right and the detector was too narrow.
That shape is now a positive-control case. (2) The builder found 3 sites the adjudicator did
not report, all in `tests/save/test_usmap.py`, where the rendering IS the subject under test -
recorded as the single waiver, with its reason, and ASSERTED STILL LIVE so it cannot rot.
Both controls are real. POSITIVE: 8 leaky shapes across 10 sites all caught, and separately a
leaky module was written into `tools/`, watched to go red, and deleted - which proves the
ENUMERATION catches a file that is on no list. NEGATIVE: `clockspeed/data/docs_extract.py` is
pinned BY NAME as not-flagged and the assertion is proven non-vacuous, because that module
renders `exc.reason`, `exc.msg` and `exc.lineno` and a naive detector flags it, after which
someone either "fixes" correct code or loosens the test.
The installer stays DEPENDENCY-FREE by duplication rather than import, proven by tests that
run it with `clockspeed/` and `tools/` absent AND syntactically broken - it is the first thing
a fresh clone runs. Idempotence held: two real runs, exit 0 both, stdout byte-identical at
1080 bytes. The builder captured and restored the machine's real `core.hooksPath`, which the
installer rewrites; the merger verified it afterwards as `C:\Clockspeed\.githooks` with
`verify_env.py` reporting FOUND and VERDICT PASS.
GRANT B implemented as ruled: the crash traceback is SUPPRESSED BY DEFAULT behind
`CLOCKSPEED_CRASH_TRACEBACK=1`, the exit code stays 1 on both paths, and the crash is provoked
FROM OUTSIDE by patching `argparse` before `runpy` re-executes the gate, so no test hook was
added inside the frozen file. `tests/test_precommit_gate.py` was not touched at all.
GRANT B'S CITED LINE NUMBER WAS STALE - it named `:1670` and the only `traceback.print_exc()`
was at `:1778`. The builder proceeded because "the single site" was unambiguous, and said so.
PROVEN END TO END BY THE MERGER AFTER THE MERGE, because hook presence is never proof of hook
firing and this change touched both the gate and the installer: an em-dash violation was
staged, a real `git commit` attempted, and the result was `precommit_gate: BLOCKED`, the
CHARSET diagnostic naming U+2014 at line and column, and HEAD UNCHANGED.
UNCLOSED AND CORRECTLY NOT SELF-GRANTED, now filed as CS-406: `scripts/install_hooks.py:310`
is a `traceback.print_exc()` of the same class as grant B, which grant A does not reach - the
adjudicator's own structure implies this, since it carved the gate's traceback into a separate
grant precisely because a traceback needs a different remedy from a redaction; and `:236`
prints the absolute repository root on the SUCCESS path, a third adjacent non-exception leak
the adjudicator did not name. Both are recorded in the sweep's live residual list, so a NEW
unguarded traceback anywhere already fails the suite while these two are grandfathered by name.
Also unverified and stated: the `:170` chmod branch is fixed but never EXECUTES on Windows,
so it is verified by inspection plus a direct probe of the redaction helper against a real
`OSError`, and by CI tier 2 rather than here.

### 2026-08-14 - CS-400 PARTIAL - Phase 4 waves 0 and 1: the spec correction, the synthetic corpus, and the four independent readers
Verification: `clockspeed/save/{header,chunks,usmap,workdir}.py` plus
`tests/save/{synthetic,test_synthetic,test_header,test_chunks,test_usmap,test_workdir}.py`.
Suite observed at close: 1067 passed, exit 0, from 734 at session start.
**CS-400 IS NOT CLOSED AND REMAINS OPEN ON THE ROADMAP.** Waves 2 and 3 are unstarted:
`objects.py`, `world.py`, the phase-4 acceptance gate and the `mInventoryPotential`
experiment. None of the four acceptance clauses is met yet, because none can be met without
`load_world`. This entry records the waves that DID land so the next session does not redo
them; it does not claim the phase.
WAVE 0. `BOOTSTRAP.md` sections 2.4 and 3.1 are now version qualified, and ADR 0007 records
why - see its own entry. The synthetic corpus is `tests/save/synthetic.py`, every byte built
in code, validated by an independent minimal reader written inside the test module rather
than by any production parser, and anchored against a real save by a shape-only test that RAN
on this machine rather than skipping. Three kill mutations proved the fixtures discriminate;
the sharpest - swapping the map-name and options slots - is caught by the ANCHOR ALONE, which
is the case no synthetic test can reach.
WAVE 1, four modules on disjoint write-lists, each graded against its own acceptance:
`header.py` carries NO field holding the save name, options string or session name. Not
redacted - ABSENT. The default parse never DECODES those bytes, asserted functionally (a
header carrying 0xFF in the session name parses while `reveal_strings` on the same bytes
raises) and structurally (an AST count pinning the parse to exactly two decoded strings).
`chunks.py` detects the framing from the MARKER and warns rather than raising on a
version disagreement, walks multi-chunk bodies to a clean end of file, and refuses a declared
decompression bomb BEFORE allocating.
`usmap.py` derives the inner grammar from the bytes and is verified against the shipped file:
57,985 names, 2,603 enums, 13,792 schemas landing exactly on a clean `CEXT` tag, with the
trailing extension container flagged and skipped and `body_consumed` reporting the gap.
`workdir.py` is the SOLE write-capable call site in the package - one `open("wb")` - which is
what makes the single-writer property a static assertion. Its refusal PREVENTS the write
rather than reporting it, isolated by mutation.
THREE MEASUREMENTS TAKEN BY THE MERGER AGAINST REAL SAVES, because no synthetic test could
settle them and two builders had reported fixture properties as format properties:
(1) The four int64 chunk sizes are `(c, u, c, u)`, NOT `(c, c, u, u)` - measured on all 14
saves across all three header versions. W1-CHK named this as its one genuine common-mode risk
and had guessed correctly, but it was a guess until measured.
(2) The decompressed body prefix is version scoped and THE CORPUS IS WHAT DIVERGES: real
header 13 and 14 bodies open with an int64 equal to body length minus 8, and real header 10
opens with an int32 equal to body length minus 4. A builder's "first int32 is 2" was a
measurement of the FIXTURE. `chunks.py` is unaffected because it never interprets the prefix;
W2-OBJ would have been. Filed as CS-404 before it could reach wave 2.
(3) Real bodies run to 138 chunks and just over 18 MB against 3 chunks in the largest
fixture.
CARRIED FORWARD TO THE PHASE GATE, verified by the merger rather than taken on trust: the
static single-writer scan returns `[]` for `os.open(p, os.O_WRONLY)`, so it cannot see
flag-based writes. The W3-GATE AST gate MUST cover `os.open`. The runtime audit hook does
check flags, so the two halves are complementary and neither is sufficient alone.
PROCESS FINDING, and it fired on FIVE of the seven builders dispatched: an isolation worktree
was cut from a STALE commit rather than from the stated HEAD. Every one of them detected it,
verified ancestry and reconciled before building, rather than reporting a baseline that was
real for the worktree and wrong for the tree. State the HEAD in every dispatch and require
the builder to check it.

### 2026-08-14 - ADR 0007 - The save header layout and the chunk framing are VERSION DEPENDENT
Verification: `docs/adr/0007-header-and-chunk-framing-are-version-dependent.md`, status
`accepted`, indexed at `docs/adr/README.md`. `BOOTSTRAP.md` sections 2.4 and 3.1 carry the
version-qualified tables and own those measurements.
ADR: `docs/adr/0007-header-and-chunk-framing-are-version-dependent.md`.
Measured across all 14 local saves, independently three times - by a planner, by the merger,
and by the adjudicator, each with its own read-only probe that reduced every string to a
boolean or a length before printing. Header version 14 carries FOUR leading strings and
header versions 10 and 13 carry THREE. Chunk framing on header 13 and 14 uses marker
`0x22222222` with an int8 algorithm byte and zlib at magic+49; header 10 uses marker
`0x00000000`, has NO algorithm byte at all, and zlib begins at magic+48. The header tail is
28 bytes on 13 and 14 and ZERO on 10.
THE PRIVACY MECHANISM IS THE REASON THIS IS AN ADR AND NOT A FOOTNOTE. On header 10 and 13
the THIRD string is the operator-chosen SESSION NAME; on header 14 it is the options string.
So a redactor targeting a NAMED FIELD is defeated by a version-dependent field ORDER. That
was demonstrated live rather than theorised: a planner probe in this session printed one such
value into its own agent transcript by labelling the third string "options". Nothing was
written to any file and nothing entered the repo.
THE ADJUDICATION RETURNED NEEDS-REVISION, NOT ACCEPT, and the four defects were fixed before
the status flipped. The load-bearing one was not about the save format at all:
`docs/adr/0003` is status `accepted` - binding, and citable freely - and its Context states
the refuted unqualified framing verbatim including the hex constants, so the STALE claim held
the HIGHER status and a reader searching for the framing would hit it first. Neither an
accepted ADR nor an append-only ledger entry may be edited, so the correction travels as a
pointer in both directions; see the CS-104 entry.
The other three: the int8 after the datetime ticks was labelled "session visibility" and is
not a flag - it reads `0x00` on header 10, 13 and 14/60 and one of `0x10`, `0x50`, `0x90` or
`0xD0` on the eight header-14/save-52 saves, so it is now recorded as measured in POSITION
and unverified in MEANING, its position anchored by the int32 after it reading 40 on all 14.
The opt-in PII path is now render-site only, because `locate.redact()` holds NO NEEDLE for a
session name read out of a header - that string is not knowable in advance, so the one
sanctioned accessor returns a value the project's own redactor cannot neutralize. And
Decision item 6 is restated as a COMMITMENT rather than a description, because
`clockspeed/save/` held only `__init__.py` when it was written.
UNDETERMINED AND RECORDED AS SUCH: whether the framing keys on header version, save version
or build changelist. All three predict it perfectly because they covary across every local
file, so no local file separates them. Detection from the marker is immune to which is right.
STATED LIMIT OF THE ACCEPTANCE: all 14 saves come from one machine, one account and one map,
with an empty mod metadata field on all 14. The version triple is an unproven discriminator
against a modded or another-platform save, which would present a KNOWN triple with an
unmeasured field shape and would NOT trip the unknown-combination guard.

### 2026-08-14 - CS-104 - CORRECTION: the chunk framing recorded by this item is VERSION DEPENDENT, and the entry as written is true only for header versions 13 and 14
Verification: `docs/adr/0007-header-and-chunk-framing-are-version-dependent.md` plus
`BOOTSTRAP.md` section 3.1. This ledger is append-only, so the original CS-104 entry is
left exactly as written and this entry is the correction pointer.
CS-104 recorded the body framing as magic `0x9E2A83C1`, marker `0x22222222`, int64 max chunk
size 131072, int8 compression algorithm 3, sizes written twice, and a decompressed body
opening with an int64 length. Measured this session against all 14 local saves and confirmed
independently by two agents plus the merger: that holds on header versions 13 and 14 and is
FALSE on header version 10, where the marker is `0x00000000`, there is NO compression
algorithm byte at all, the zlib stream begins at magic+48 rather than magic+49, and the
decompressed body does NOT open with an int64 length.
Proven rather than asserted: on the 11 header-13-and-14 saves zlib decompresses at +49 and
FAILS at +48; on the 3 header-10 saves it decompresses at +48 and FAILS at +49. The byte at
magic+16 on header 10 takes the values 2, 2 and 3 across those three saves - it VARIES,
which is positive evidence it is the low byte of the compressed size and not an algorithm
byte. Every chunk of every save was walked to a clean end of file with both duplicated size
pairs agreeing.
`docs/adr/0003-s4-node-actors-in-save.md` Context item 1 carries the same unqualified claim
and is status `accepted`, so the refuted text held the higher status until now. Per
`docs/adr/README.md` an accepted ADR's text is never edited; ADR 0007 NAMES it instead, so a
reader searching for the framing is routed forward rather than stopping at the stale copy.

### 2026-08-14 - CS-204 - The diagnostic label channel is redacted at the render boundary, across FOUR channels rather than the three the item named
Verification: `tools/precommit_gate.py` and `tests/test_precommit_gate.py`, plus a new
`tests/test_edit_lint_check.py` exercising the second tool as a subprocess. Merged under the
frozen-file grant recorded above, whose ten conditions were all discharged.
Re-verified by the merger independently of the builder: a `--files` run over a path under
the home directory emits no home path and no account name, the out-of-repo DIRECTORY name is
stripped, both basenames survive verbatim, the CHARSET diagnostic still fires and the exit
code is still 1. The tracked-tree rehearsal is unchanged at PASS, 118 checked, 1 skipped, 0
blocking, exit 0.
THE ACCEPTANCE CRITERION WAS WRONG AND WAS OVERRIDDEN BY ADJUDICATION. It named three
channels; there are FOUR, because `report.notes` also carries labels. All four are fixed and
each has its own test on both tools. The ruff-note test deliberately embeds the label
MID-STRING, so a fix that only redacts a leading label fails it.
Condition 1 was proven MECHANICALLY rather than by inspection: an AST byte-comparison against
HEAD shows `label_for`, `Unit`, `check_path`, `mode_files`, `mode_staged`, `stage_for_lint`,
`record_ruff_findings`, `check_python_syntax`, `check_charset` and `Diagnostic` are all
IDENTICAL, so nothing verdict-bearing moved. Every diff hunk sits inside `emit` or the new
render-boundary block above it.
Condition 7 was discharged by NOT importing rather than by a fail-closed test: zero imports
were added and `test_the_gate_imports_only_the_standard_library` asserts it by AST, so the
`except Exception` clause the grant required never becomes reachable.
Condition 4 was proven DISCRIMINATING by mutation: swapping in a home-keyed redactor turns
exactly one named test red and nothing else.
Condition 9's anti-vacuity repair was applied as authorised - `LEAK_MARKER` moved from a
directory component to the basename - and proven still non-vacuous by mutation: removing the
redaction fires the `<= 1` assertion on all three consuming tests.
`tools/edit_lint_check.py` REQUIRED NO EDIT. Fixing `gate.emit` covered it, and that is
proven by the new subprocess test rather than by inspection, which is what the grant demanded.
Verdict invariance was measured against a NON-VACUOUS corpus, which is the part that is easy
to fake: the tracked-tree run alone is a 0-versus-0 comparison and proves nothing, so a
six-file violation repository was built UNDER A HOME DIRECTORY carrying BINARY, CHARSET,
LINT, PII, SECRET and SYNTAX violations, and the exit code and the full diagnostic set are
byte-identical before and after, labels included.
The common-mode risk flagged at dispatch is CLOSED by a test that `git init`s a throwaway
repository with `HOME` and `USERPROFILE` pointed at a temporary directory. That test also
CORRECTED A CLAIM THE BUILDER HAD WRITTEN: it had asserted the test guards condition 4, and
mutation showed it does not, because labels in that repository are already relative so a
home-keyed rule leaves them alone. The docstring records the measured truth instead.
The gate caught the builder's own test file mid-slice with four `PII absolute POSIX home
path` diagnostics; the values are runtime-assembled now, and no literal entered a tracked file.
UNCLOSED AND EXPLICITLY NOT CLAIMED: `tools/edit_lint_check.py:113` renders
`f"could not read the file: {exc}"` raw where the gate uses `safe_exc_text`, so the label is
redacted and the REASON still leaks a path. That is CS-205's scope and is left to it rather
than colliding with a concurrent slice. Also unverified: POSIX behaviour, argued structurally
and pinned by the determinism test but never observed on a Linux runner; and `--staged` mode,
whose labels are always repo-relative so redaction is a no-op there by reasoning, not by
measurement.

### 2026-08-14 - CS-206 - tools/facts_probe.py redacts hooks_path, and a SECOND unredacted field found by the sweep
Verification: `tools/facts_probe.py` plus `tests/test_facts_probe.py`, ten new tests. Proven
by a planted SYNTHETIC home segment asserted absent from the emitted payload - never by
`redact(x) != x`, which is the redactor-as-its-own-oracle failure class and is blind exactly
where the redactor is blind.
Re-verified by the merger in the MAIN checkout, which the builder could not do because its
`repo_root()` was its worktree and relativization correctly did not fire there: the default
payload now renders `hooks_path` as `.githooks`, and the serialized payload contains neither
the `USERPROFILE` literal nor the Windows account name.
The fix goes REPO-RELATIVE FIRST and `locate.redact()` second. The first pass closes a class
`redact()` structurally CANNOT reach: it builds its home needles from the environment, so a
checkout under a directory the environment never names matches none of them.
A SECOND UNREDACTED FIELD was found by the mandated full-payload sweep and fixed in the same
change, as an addition to the item's stated scope: `git.branch`. It cannot BE a path - git's
ref format forbids backslash, colon and space - so it passes a literal "cannot carry a path"
test, but `<user>/wip` is an everyday branch convention and the Windows account name is
personal data of the same rank under non-negotiable 3.
TRADE-OFF ACCEPTED AND RECORDED RATHER THAN HIDDEN: `redact()`'s digit-run backstop will
rewrite a date-shaped branch such as `release/20260814` into `release/<account-dir>`. That
label is misleading - it names an account directory where a date stood. The over-redaction
direction was taken deliberately, per `locate.py`'s own stated principle and because
fail-closed beats fail-open on PII, and the misleading label is the price.
The `if not value` guard is load-bearing and is documented as such: `locate.redact()`
stringifies its argument, so the tempting `redact(x) or None` returns the truthy string
`"None"` and would turn an UNPROTECTED checkout into one that reads as protected.
When the data layer does not import there is no redactor, so values are WITHHELD rather than
emitted raw, and withheld is kept distinct from `None` so that "wired but suppressed" never
reads as "not wired". Those two guards were mutation-checked: replacing the withheld return
with the raw value turned both tests red via the independent leak assertion.
Swept and explicitly cleared: `game.build` and `game.build_via` were traced through every
probe and every emitted label enumerated - all fixed literals, none derived from a discovered
path. `git.sha` is deliberately left raw as machine-generated hex, because redacting it would
let the digit backstop eat an all-numeric abbreviation.
Honest limits: behaviour on the Linux CI runner is unverified - only Windows was run - and
the new tests require `git` on PATH and error rather than skip without it, which adds no new
dependency since the gate suite already requires it.

### 2026-08-14 - CS-207 - scripts/verify_env.py compares RESOLVED PATHS, so an absolute core.hooksPath is no longer a false MISSING
Verification: `scripts/verify_env.py` plus `tests/test_verify_env.py`, sixteen named tests.
Proven live rather than by unit test alone: before, `python scripts/verify_env.py` printed
`HARD core.hooksPath == .githooks MISSING` and `VERDICT: FAIL` at exit 1 while the hooks
demonstrably fired; after, it prints `core.hooksPath -> .githooks FOUND`, `HARD: 7/7`,
`VERDICT: PASS` at exit 0. Confirmed PRE-EXISTING before the fix: `git log -L 483,498` on
that file returns the initial commit alone, so the lines were never touched and CS-202 did
not introduce it.
All three acceptance halves are covered separately, and the third is the one that is easy to
lose: an absolute form is FOUND, the relative form is STILL FOUND, and a value pointing
anywhere else is STILL MISSING. The comparison is `os.path.normcase` over resolved paths,
chosen over a hand-rolled lowercase (wrong on a case-sensitive filesystem) and over
`Path.samefile` (whose `st_ino` can be 0 on some filesystems and would then equate different
directories). Existence is checked SEPARATELY and BEFORE identity, using `is_dir()` rather
than `exists()`, because `Path.resolve()` is non-strict and identity alone would report FOUND
for a hooks directory that was never created, and because a file there runs nothing.
FOUND AND FIXED BEYOND THE STATED SCOPE, and it would have defeated the fix: `core.hooksPath`
is SHARED git config, so inside a linked worktree it holds the MAIN checkout's absolute path.
Comparing only against `<root>/.githooks` would have RELOCATED the false red into every
worktree rather than removing it - and every builder in this project runs in a worktree.
`expected_hooks_dirs()` therefore also accepts the main checkout's `.githooks`, derived from
`git rev-parse --git-common-dir`. Criterion 3 is not weakened: both entries are specific
resolved directories, pinned by `test_a_linked_worktree_still_rejects_an_unrelated_hooks_dir`.
PII: the row and `facts["hooks_path"]` both go through `redact()` now. Fixing only the table
would have left `--json` publishing the home path. The module docstring already CLAIMED that
every path it prints goes through `redact()` first; that claim was false and is now true.
THE GUARD TESTS WERE PROVEN TO DISCRIMINATE rather than assumed to: four mutations were
applied to the fix in turn - matching on the trailing segment, dropping the existence check,
`exists()` for `is_dir()`, and dropping relative anchoring - and each turned a NAMED test red.
Honest limits, recorded rather than omitted: the drive-letter-case test is skipped off
Windows and was never observed to run; the `_resolved_key` `OSError` branch has no test and
fails closed by inspection rather than by measurement; and the builder verified the CHECK's
verdict, not that the hooks fire - that end-to-end proof remains session 3's.

### 2026-08-14 - CS-208 - Frozen-file grant DENIED, and the item is refuted by measurement rather than deferred
Verification: adjudicated under `CLAUDE.md` section 6 by an agent that authored no part of
the proposal and did not find the original defect. The grant sought an edit to
`tools/precommit_gate.py:570` (`MIN_ACCOUNT_NAME_CHARS = 3`), through which world names route
at `:852` and account names at `:960`. DENIED, and the denial rests on measurements that
refute the item's own premise rather than on a judgement call.
MEASURED, values never printed, lengths only: 16 distinct matchable world names are
discoverable on this machine, the shortest being 4 characters. A floor of 4 drops nothing; a
floor of 5, 6 or 8 drops EXACTLY ONE currently-matchable real world name, which then stops
being blocked and WILL COMMIT. The item as worded - raise the floor ABOVE the measured
shortest real world name - therefore SPECIFIES a fail-open hole.
MEASURED, and this is what refutes the premise: the feared false positive does not exist.
The gate over all 117 tracked files with live discovery exits 0 - "117 checked, 1 skipped, 0
blocking". Sixteen real world names, one of them 4 characters, collide with nothing in the
tree today. And when a collision does occur it is not a hunt: a planted synthetic
4-character world name against ordinary prose produces file, line, COLUMN, rule and
citation on the first block. `ROADMAP.md`'s "blocks every commit until the operator finds
the cause" was overstated.
MEASURED: a floor of 4, 5, 6 or 8 turns ZERO of the 65 gate tests red, because every world
value declared in the suite is either 16, 15 or 2 characters. "No tests break" is therefore
NOT evidence of safety here - it is proof the change is untested and the suite is blind to
it.
The (a)/(b) design question was ruled on rather than left open. (b), raising the single
shared floor, is rejected outright: two fail-open holes bought with one hypothetical false
positive, and it silently narrows ACCOUNT-name matching on every machine so that a 3- or
4-character login stops being matched with nothing in the suite noticing. (a), splitting the
constant, is sound hygiene but insufficient reason to edit a frozen file at equal values,
and a split whose purpose is to raise the world half is (b) with a tidier blast radius.
The governing asymmetry is already recorded in this file under CS-201: the gate must be
WIDER than the resolver. Narrowing a PII blocklist by default, on every machine, to pre-empt
a collision that has not occurred and that diagnoses itself to line and column when it does,
trades a certain fail-open for a diagnosable fail-closed.
SUPERSEDED BY CS-209, which carries the correct fix: a per-value exclusion surface applied
after discovery, a remedy clause in the world-name reason, and the separately-found defect
that `.githooks/pre-commit` passes neither `--verbose` nor `--list-skipped`, so the skip
channel that CONVENTIONS section 15.1 relies on to keep a drop visible does not print at all
on the authoritative path.

### 2026-08-14 - CS-205 - Frozen-file GRANT B WITH CONDITIONS: the single `traceback.print_exc()` site in tools/precommit_gate.py
Verification: adjudicated under `CLAUDE.md` section 6 by an agent that authored no part of
the proposal; recorded here BEFORE any edit. Scoped as its own grant line because it is a
different frozen file from grant A and because CS-205's own stated scope is "outside the two
CS-202 files", of which the gate is one - so it falls outside grant A twice over.
RULING: a traceback CANNOT be honestly redacted. It renders an absolute path per frame - a
home path on any checkout under a user profile - and its final line is `str(exc)`, the exact
rendering CS-202 removed everywhere else. Frame paths can be rewritten, but re-implementing
per-type redaction at the crash handler duplicates `safe_exc_text` at the least testable
point in the program.
The granted alternative is the pattern non-negotiable 12 already mandates for the save
header options string: SUPPRESS BY DEFAULT, opt in explicitly. Four conditions. (1) Default
crash output is the exception class name, `safe_exc_text(exc)`, the existing fail-closed
sentence, and the NAME of the flag that reveals the rest; a test provokes a crash and
asserts no absolute path in the default output. (2) EXIT CODE STAYS 1, proven by test,
together with the "gate itself raised / failing CLOSED" message - a gate that crashes open
is worse than no gate. (3) The opt-in is a `CLOCKSPEED_`-prefixed environment name,
documented in the module docstring beside the existing five, default OFF, and its ON path is
tested to still exit 1. (4) No new import into the gate.
The grant permits reformatting the crash report and NEVER swallowing it, and reaches nothing
in `tools/precommit_gate.py` other than that one site at `:1670` and its adjoining crash
message.

### 2026-08-14 - CS-205 - Frozen-file GRANT A WITH CONDITIONS: scripts/install_hooks.py may have its exception renderings redacted
Verification: adjudicated under `CLAUDE.md` section 6 by an agent that authored no part of
the proposal; recorded here BEFORE any edit. The frozen list is unchanged and no agent
self-granted.
The dispatch invited a NOT-NEEDED denial if `scripts/install_hooks.py` carried zero
unredacted renderings. It carries SIX - `:65`, `:67`, `:85`, `:170`, `:227` and `:240` - so
the grant is genuinely necessary. `:67` and `:227` are the argv-plus-exception shape CS-202
already fixed in the gate, and `:170` is on the POSIX-only branch that CI tier 2 executes.
FOUND ADJACENT AND NAMED RATHER THAN LEFT SILENT: `:70-76` renders git's decoded stderr
verbatim, and `:149` renders an absolute path directly. Both are the same leak class and
NEITHER is an exception rendering, so the mechanized sweep this item mandates will not see
them. Condition 8 requires they be fixed under this grant or recorded as an explicit named
residual.
THE ROADMAP'S OWN FILE LIST WAS ALREADY STALE, which is the exact failure the mechanized
acceptance was written to prevent. An independent AST sweep across all tracked `*.py` found
13 real object renderings in 4 files, and surfaced a fifth file -
`clockspeed/data/docs_extract.py:443` and `:589` - which is a FALSE POSITIVE: those render
`exc.reason`, `exc.msg` and `exc.lineno`, which are named fields rather than the object. A
naive detector will flag them, and someone will then either "fix" correct code or loosen the
test.
Nine conditions carry the grant; the load-bearing ones are 2, 4 and 5. (1) Per exception
TYPE allowlist, never a strerror-shaped helper, per the CS-202 precedent recorded above.
(2) THE INSTALLER STAYS DEPENDENCY-FREE - it is the first thing a fresh clone runs, so if
the builder imports rather than duplicates, a test must prove `install_hooks.py` still runs
and still exits correctly with `clockspeed/` and `tools/` absent or syntactically broken.
(3) The detector ENUMERATES tracked files and never hardcodes a module list. (4) The
detector distinguishes the exception OBJECT from a FIELD of it, with a NEGATIVE control
asserting the `docs_extract.py` shape is not flagged and a positive control asserting the
`{exc}` shape is. (5) A POSITIVE CONTROL IS MANDATORY - the mechanized test must be shown
capable of failing against a synthetic leaky module, or it is a green light with nothing
behind it. (6) No self-exemption; the detector covers its own module. (7) Exit codes
unchanged, the `core.hooksPath` readback check at `:154-159` untouched, and a second run
still prints byte-identical output. (8) The two adjacent non-exception leaks are fixed or
named. (9) The authoritative scope is the mechanized enumeration, NOT the four-file list on
the roadmap line.
The grant does NOT permit changing the installer's wiring logic, the readback check, the
hook inspection rules, or any exit code.

### 2026-08-14 - CS-204 - Frozen-file GRANT WITH CONDITIONS: tools/precommit_gate.py may redact the diagnostic LABEL channel at the render boundary
Verification: adjudicated under `CLAUDE.md` section 6 by an agent that authored no part of
the proposal and did not find the original defect; recorded here BEFORE any edit. The frozen
list is unchanged and no agent self-granted. The prior adjudicator's recusal is honoured -
it found the defect and did not grant it.
THE SIX VERDICT-BEARING CALL SITES ARE CONFIRMED AND UNDERSTATED. Enumerated at `:1471`,
`:1520` (`check_path` in staged and files mode), `:1136` (`compile` -> `SyntaxError.filename`),
`:1239` (the staging-copy filename ruff actually lints), `:1234`/`:1241` (the ruff output
mapping) and `:1477` (`git show :<label>`). TWO MORE were found: `:1469` and `:1518` derive
the EXTENSION from the label rather than from the given path, and that extension selects
WHICH CHECKS RUN - `classify_for_read`, the NUL rule, the `check_content` dispatch and ruff
target selection; and `:1111-1117` scans the label itself for non-ASCII and reports
`label.index(offending) + 1` as the column. The prior adjudicator's risk classification is
correct and if anything conservative.
THE ACCEPTANCE CRITERION WAS WRONG AND IS OVERRIDDEN HERE. It names three channels;
there are FOUR. `report.notes` carries labels at `:350`, `:360`, `:1268` and `:1346` and is
printed by `emit` at `:1605-1607` and `:1627-1631`. Demonstrated live: a `--files` run over
an out-of-repo path leaks the home path through checked, skipped, notes AND diagnostics.
Fixing exactly the three named channels MOVES the leak into notes, which is precisely what
the item's own "fix all channels at once" condition exists to prevent.
"ZERO TESTS TURN RED" IS ALSO REFUTED. `tests/test_precommit_gate.py:1174` is a SECOND
label-shape assertion - `LEAK_MARKER` is a DIRECTORY component of an out-of-repo path, and
any redaction stripping directory components above the repo root deletes it. Three tests
consume it, at `:1191`, `:1201` and `:1226`.
Ten conditions carry the grant. The load-bearing ones are 1, 2, 4, 7 and 9. (1) Redact
inside `emit` via a pure function of the label; `label_for` and `Unit.label` return
byte-identical values to HEAD, proven by test. (2) FOUR channels, one test each, each
provoked by an out-of-repo target. (3) Both tools covered by test, `tools/edit_lint_check.py`
exercised as a subprocess - inspection does not discharge it. (4) DETERMINISM: the rendered
label must not depend on where the machine's home directory is, because `tmp_path` is under
the home directory on Windows and under `/tmp` on Linux, so a home-keyed redactor is green
in CI and red locally. (5) The basename stays verbatim. (6) `--text-stdin`'s literal
`<stdin>` is untouched. (7) NO NEW DEPENDENCY - and if a shared redactor is imported, the
handler must catch `Exception`, NOT `ImportError`, because a staged em-dash in
`clockspeed/data/locate.py` raises `SyntaxError`, which `except ImportError` does not catch,
and the gate would crash instead of printing the CHARSET diagnostic it exists to print.
(8) Verdict invariance measured over every tracked file, not asserted. (9) THE ANTI-VACUITY
REPAIR IS EXPLICITLY AUTHORISED AND THE ROADMAP IS OVERRIDDEN ON THIS POINT: if `:1174` goes
red the correct repair is to re-point `LEAK_MARKER` at a component that survives redaction,
NOT to weaken the redaction; the roadmap's blanket "a red test there means the redaction
went too far" applies only to `test_verbose_lists_every_checked_unit`. (10) No literal
introduced.
The grant does NOT permit editing `label_for`, `Unit.label`, `check_path`, the `compile`
call, the staging-copy naming, the ruff mapping or the `git show` argument, changing any exit
code or diagnostic code/line/column, or adding a path allowlist.

### 2026-08-14 - CS-300 - Phase 3 gate: pillar 1 exact ratio solve, then pillar 2 behind the pluggable optimizer interface
Verification, all three acceptance criteria checked independently of the agents that built
them.
(1) HAND-VERIFIED RATIOS INCLUDING A BYPRODUCT LOOP. `tests/solve/synthetic.py` carries C1
to C9 with every expected value as a named constant. The load-bearing case is C3, where
Gadget needs Fluid, Fluid comes from Residue and Residue comes from Gadget, so naive
topological recursion does not terminate. Re-derived through the MERGED solver by the
merger, not read from a builder report: machines `R_Gadget=2, R_Recover=2/3, R_Fluid=2,
R_Plate=4/3`, raw Ore 60/min, every count exact `Fraction`, output identical across runs and
across a reversed recipe tuple. C4 solves the same loop in reverse and cross-checks C3
exactly via `Fraction(436,3) * Fraction(3,4) == Fraction(109)`. That there is no disguised
tree walk is asserted STATICALLY - `tests/solve/test_ratio.py` parses `ratio.py`'s own call
graph and requires it acyclic - because a memoizing recursive solver passes every value test.
(2) NO FLOATING-POINT ARITHMETIC ANYWHERE IN THE SOLVE PATH.
`tests/solve/test_phase3_gate.py`, 96 tests. A static AST walk over every module under
`clockspeed/solve/`, with the module set asserted EQUAL to a pinned tuple rather than merely
non-empty, so a rename cannot silently shrink coverage. Proven to DETECT rather than merely
to pass: each forbidden construct injected into the real module sources and caught at the
right line - float literal, `**`, `round`, `import math`, and a bare `float` reference. It
scans the AST and never the text, because `exact.py` and `power.py` quote the
`Fraction ** Fraction` measurement verbatim as evidence for the ban; a regex sweep reports
47 hits in `exact.py` alone, all prose. Two further independent signals cover what a static
check cannot see - `exact.audit_exact` asserts POSITIVELY (`type(x) is Fraction`) at every
public seam, and the strict mypy rung catches a `float` declared in a signature.
(3) THE OPTIMIZER SWAPPABLE BY CONFIG WITH IDENTICAL RESULTS ON A DEGENERATE CASE.
`clockspeed/solve/optimize.py` owns `OptimizerBackend`; `backends/exhaustive.py` and
`backends/greedy.py` implement it by genuinely different mechanisms - complete lattice
enumeration versus a reachability least fixed point that prunes on feasibility before
scoring. Fixture C5's feasible set is a SINGLETON by construction, with the
better-on-every-objective recipe declared first and infeasible, so a registry-order stub and
a score-before-feasibility greedy are both demonstrably wrong while any correct backend must
agree. THREE assertions ship, not one - each backend against the hand-verified absolute
(`Std_Gadget` x 3, Ore `Fraction(120)`, power `Fraction(45)` MW) and the two against each
other - because agreement between two implementations is not evidence on its own. Both are
reached only through `select_backend`; an unknown name refuses at all three precedence
levels rather than falling back, verified independently (`exhausitve` -> `UnknownBackendError`).
Determinism proven across two separate interpreter processes under differing PYTHONHASHSEED.
CS-G02's PREP half is now complete: the interface exists and is proven by two in-repo
backends, which is the stated precondition before an external LP/ILP dependency may be
considered. The DRAIN half remains gated - see `docs/GATED.md`.
A MERGER INSTRUCTION WAS REFUTED BY THE GATE AGENT AND THE REFUTATION WAS RIGHT. The wave-4
dispatch required that no solve module pull in `clockspeed.data.docs_extract`. That is
unsatisfiable: `registry.py:206` and `version.py` import it at module level, and
`tests/data/test_phase2_gate.py:775-781` REQUIRES those edges. `docs/ARCHITECTURE.md:136-138`
scopes the raw-docs prohibition to `advisor/`; the clause for this layer is "solve/ never
reads a save". The carve-out is self-verifying - a test measures each carrier in its own
child interpreter and fails if a carrier stops justifying it - and a DIRECT import of
`docs_extract` from solve remains forbidden with no carve-out at all.
Modules: `clockspeed/solve/{exact,ratio,power,optimize}.py`, `clockspeed/solve/backends/`.
Tests: `tests/solve/test_{exact,synthetic,ratio,power,optimize,phase3_gate}.py`.
ADR: `docs/adr/0006-unsharded-clock-base-and-the-ceiling-fence.md`

### 2026-08-14 - CS-105 - S7: the overclock power exponent is read from building class data, and a test fails if a literal appears in the power path
Verification: `clockspeed/solve/power.py` plus `tests/solve/test_power.py`. The data half
landed in phase 2 (`clockspeed/data/registry.py` reads `mPowerConsumptionExponent` per
building class); the guard half could not exist until there was a power path to assert
about, which is why this closed with phase 3 rather than phase 1.
The guard ships as TWO tests, and the reason is measured rather than defensive. A literal
scan over the module's constants catches `Fraction("1.321929")` - but a hardcoded
`Fraction(1321929, 1000000)` is two INT literals and passes it. Demonstrated on a
scratchpad copy: with the value hardcoded in the integer-pair spelling, the literal scan
PASSED while the mutation test FAILED. The durable half is therefore the mutation test -
two registries identical except for one building's exponent must produce DIFFERENT results,
which no spelling of a constant can satisfy - and it does not go stale when a balance patch
moves the number, which the literal blacklist does. The candidate values the scan checks
are read from the fixture and from the pin census, never restated in the test, or the test
would become the thing it forbids.
A third assertion covers what neither scan can see: `power_exponent is None` means NOT
clock-scalable and is never defaulted, so a floodlight is not silently clock-scaled.
The ceiling remains UNKNOWN per ADR 0005 and this item does not touch it:
`power.ClockCeiling` carries no field capable of holding a ceiling value, and
`version.OVERCLOCK_POTENTIAL_SHARD_SLOTS` is still None.

### 2026-08-14 - CS-203 - tools/facts_probe.py has a test module; the default output is proven to carry no PII
Verification: `tests/test_facts_probe.py`, 13 tests. The load-bearing pair is
`test_default_payload_carries_no_account_id_no_world_name_and_no_home_path` and
`test_unredacted_payload_emits_the_account_ids_the_world_name_and_the_home_path` - the
second is what stops every "absent" assertion in the first passing against an empty
payload. Redaction is proven POSITIONAL, not prefix-only, by
`test_default_output_redacts_an_account_segment_sitting_mid_path`, parametrized over
hex-token, braceless-GUID and seventeen-digit account shapes and asserting the path TAIL
survives, so truncation cannot pass as redaction. Non-negotiable 1 is covered by a
before/after `(is_dir, size, mtime_ns)` snapshot of the save tree.
The oracle is deliberately NOT the redactor: every value is synthetic and planted by the
test's own fixture, so it is known present as ground truth. `redact(x) != x` as the test for
"x holds PII" is blind exactly where the redactor is blind, and that mistake was made and
caught in session 2.
Proven to detect by mutation on scratchpad copies, five independent breaks. The one that
matters: with `locate`'s positional account rule removed but the digit-run backstop left
intact, the hex-token and braceless-GUID cases go red while the seventeen-digit case still
PASSES - which is precisely the "fixed for one shape, silent for the other three" defect,
and proof the non-digit cases are not vacuous.

### 2026-08-14 - CS-202 - Every exception rendering in scripts/verify_env.py and tools/precommit_gate.py is redacted per type
Verification: `tests/test_verify_env.py` and `tests/test_precommit_gate.py`.
`scripts/verify_env.py::_exc_reason` and `tools/precommit_gate.py::safe_exc_text` are
per-type ALLOWLISTS that never fall through to `str(exc)`. Nine renderings were fixed, not
the seven the item named: the sweep was done by AST rather than by text search, which is
what found `verify_env.py:358` (a bare `str(exc)`, outside the `f"...{exc}"` shape the
original acceptance specified) and gate lines 704 (`%`-format) and 959 (`.format()`, which
also interpolated the git argv - and in `--files` mode that argv carries caller-supplied
paths).
Per-TYPE is the load-bearing condition and not a stylistic one: `_exc_text` in
`tools/drift_guard.py` redacts via `strerror`, which only `OSError` carries, so a single
OSError-shaped helper silently falls back to the full `str(exc)` for the `ValueError` at
:708 and the `subprocess.SubprocessError` at :868 - reintroducing the leak it was written
to close. Diagnostic value is preserved deliberately: errno, decoder reason, line and
column are kept; anything derived from a discovered path is dropped; an unrecognised type
renders as its class name only, failing closed.
RESCOPED, and the rescope is itself the finding: this item's title claimed to complete the
sweep and its acceptance named two files. Four more carry the same shape - one of them also
frozen - so the remainder is CS-205 rather than being quietly absorbed. See the grant entry
below. `traceback.print_exc()` in the gate's crash handler is a further residual, recorded
on CS-205.

### 2026-08-14 - CS-201 - The commit gate detects world names and world tokens by VALUE, and no longer filters account directories on .isdigit()
Verification: `tools/precommit_gate.py` plus `tests/test_precommit_gate.py`. Proven END TO
END rather than by unit test, per `CLAUDE.md` section 2.2 - hook presence is never proof of
hook firing: with a SYNTHETIC world value declared via `CLOCKSPEED_WORLD_NAMES`, a file
carrying it was staged and a real `git commit` attempted, giving exit 1, `PII a world name
discovered on this machine appears as a whole word`, and HEAD unchanged. The negative half
was proven in the same way: a file carrying `Build_ConstructorMk1_C`,
`Recipe_SteelWall_8x4_C`, `DedicatedServerAPIDocs` and `most-recently-modified` commits
CLEANLY with no world declared. No real world value was ever staged into any repository.
Detection is VALUE-based - environment override, then gitignored local config, then `.sav`
basenames read under the discovered account directory - and never shape-based, for the
measured reason in the grant entry below. The C10 blast-radius rehearsal (the exact tier-1
CI invocation over every tracked file) passes at exit 0 with discovery genuinely live on
this machine.
HONEST LIMIT, recorded at the mechanism and printed as a skip on every run: a world TOKEN
lives in the save header, this gate holds no header parser and must not grow one (CS-400 is
open), so an UNDECLARED TOKEN IS UNMATCHED AND WILL COMMIT. World names are recoverable
from filenames; tokens are not. A second limit: `.sav` discovery only sees worlds that have
been saved, so a world renamed since its last save matches under the old name.
The `.isdigit()` removal is scoped to the gate at `:517` and is deliberately NOT mirrored
into `clockspeed/data/locate.py:657` - see the C6 asymmetry in the grant entry.

### 2026-08-14 - CS-201 - Frozen-file GRANT WITH CONDITIONS: tools/precommit_gate.py may gain world-value detection and lose the .isdigit() account filter
Verification: grant adjudicated under `CLAUDE.md` section 6 by an agent that authored no
part of the proposal; recorded here BEFORE any edit, per that section. The frozen list is
unchanged and no agent self-granted. Ten conditions carry the grant, each stated as a
testable requirement; the load-bearing ones are C1, C2 and C10.
Blast-radius finding, measured over all 99 tracked files rather than assumed: a shape-only
22-character world-token detector is NOT VIABLE. A naive unanchored `[A-Za-z0-9_-]{22}`
matches 2082 times; anchored exact-22 matches 183; anchored exact-22 additionally requiring
a digit, an upper and a lower still matches 5, every one of them a game class name of the
`Build_ConstructorMk1_C` shape - and `clockspeed/data/registry.py` grows that population.
The adjudication also REFUTED the premise it was handed: `clockspeed/data/version.py:352`
`integrity` is a 64-char lowercase hex sha256, not a base64-like string, and the tree
carries ZERO 40-character git SHAs, so neither is the false-positive source. Detection is
therefore value-based (C2: env override, gitignored local config, or `.sav` basenames read
under the discovered account directory) and never shape-based, and it never embeds a
literal world value in the tracked gate (non-negotiable 3).
C6 is a deliberate ASYMMETRY, recorded so it is not "fixed" later: the `.isdigit()` filter
at `clockspeed/data/locate.py:657` is NOT removed. That site SELECTS which world to read,
and widening selection makes the resolver silently pick the wrong world; the gate at
`tools/precommit_gate.py:517` only widens what it refuses to commit. The gate must be wider
than the resolver, so treating the two sites identically is a bug rather than consistency.

### 2026-08-14 - CS-202 - Frozen-file GRANT WITH CONDITIONS: tools/precommit_gate.py exception renderings may be redacted
Verification: same adjudication, same section 6 route, recorded before any edit. Separate
grant from CS-201 and standing independently of it. Materially lower risk than CS-201: it
changes message TEXT, never a verdict.
The item's own acceptance criterion was found DEFECTIVE and is corrected as a condition of
the grant. Its stated `f"...{exc}"` shape matches five of the seven exception renderings in
the file; it misses `tools/precommit_gate.py:704`, a `%`-format, and `:959`, a `.format()`
that also interpolates the git argv - and in `--files` mode that argv carries
caller-supplied paths. The sweep and its test must therefore be formatting-agnostic. A
second condition forbids reusing one OSError-shaped helper for all of them: `_exc_text` in
`tools/drift_guard.py` redacts via `strerror`, which `ValueError` at :708 and
`subprocess.SubprocessError` at :868 do not carry, so the remedy is per exception TYPE.
Scope ruling recorded because it changes what CS-202 may claim: closing CS-202 against its
two named files does NOT satisfy its own title. Four further files carry the same shape -
`scripts/install_hooks.py` (ALSO FROZEN), `tools/edit_lint_check.py`, `tools/memory_sync.py`
and `clockspeed/data/version.py:815` - plus `scripts/verify_env.py:358`, which sits in a
named file but is a bare `str(exc)` outside the stated shape. CS-202 is rescoped to its two
files and the remainder is filed as CS-205 rather than being quietly absorbed.

### 2026-08-14 - CS-200 - Phase 2 data layer: extraction, blob grammars, normalized registry, version pin, data drift guard
Verification, all three acceptance criteria checked independently of the agents that built
them. (1) Registry builds from the LIVE install: `clockspeed/data/registry.py::build_registry`
over `clockspeed/data/docs_extract.py::load_document` yields 114 groups, 2868 entries, 872
recipes, 291 automated, 750 items, 68 buildings, 0 unknown groups. (2) Synthetic-fixture
suite green with NO game installed: `python -m pytest tests` exits 0 with every
`CLOCKSPEED_*` override pointed at a nonexistent path, and
`tests/data/test_phase2_gate.py::test_the_data_layer_suite_passes_with_the_install_unresolvable`
enforces it as a gate rather than leaving it a property the suite happens to have.
(3) Drift guard red-then-green: guard `h` in `tools/drift_guard.py`, proven on a COPY of the
tree at exit 0 clean, exit 1 with a hand-corrupted pin, exit 0 after `--re-extract`. The pin
carries its OWN integrity checksum, which is what makes corruption detectable on a runner
with no install - the only environment where tier-1 CI grades this.
Modules: `clockspeed/data/{locate,blobs,docs_extract,registry,version}.py`.
Tests: `tests/data/test_{locate,blobs,docs_extract,registry,version,drift_guard_data,phase2_gate}.py`.

Adversarial review REFUTED the first cut on two independent lenses and the defects were real,
not stylistic. Recorded because the fixes are the substance of this item:
- The registry published litres where its contract said cubic metres, on the operator's
  install, for three biofuel recipes - a whitelist of four descriptor groups missed
  `FGItemDescriptorBiomass`. Fixed by MECHANISM: the item namespace is now derived from
  `mForm` presence and the building namespace from power-field presence, so the next patch
  that adds a descriptor group cannot silently reintroduce it. 60 unresolvable item
  references went to 0, and 93 stock groups falsely reported as unknown went to 0.
- The blob-grammar canary was UNREACHABLE - `marker_count >= len(parsed)` holds always, and
  the parse ran before the comparison, so an ordinary patch-shaped grammar change produced
  an empty registry silently at exit 0. Now the count is taken before the parse and two
  document-level signals are fatal. `RegistryIntegrityError` deliberately does not subclass
  `ValueError` so the flag-and-skip handler cannot swallow it.
- 7 of 8 mutants survived the first test suite; all 7 are now killed.
- A latent PII leak was fixed in `redact()`: it stripped home prefixes but not the account-id
  path segment, and the fix was then found to cover only the 17-digit Steam shape. Redaction
  is now POSITIONAL, covering Epic hex, MS-store GUID and mixed-character directories, plus
  the Windows 8.3 short-path form. The `str(exc)` sibling sweep that had been applied to
  three sites was completed across all 16 in `tools/drift_guard.py`.
ADR: `docs/adr/0005-overclock-ceiling-source.md`

### 2026-08-14 - CS-103 - Ingredient and product blobs confirmed as struct blobs; dedicated parser shipped
Verification: `clockspeed/data/blobs.py` implements the two DISTINCT grammars - the
item-amount grammar and the `mProducedIn` path-list grammar - with `tests/data/test_blobs.py`
as its own test module, per the item's "if true" clause. Mutation-checked: flipping the
parser to split on the single quote before the double quote fails 11 tests.

### 2026-08-14 - CS-102 - NativeClass groups dumped and the normalizer authored against the dump
Verification: `clockspeed/data/docs_extract.py::load_document` derives every group short name
at runtime rather than from a hardcoded table, and `clockspeed/data/version.py::census`
records the pinned build's whole 114-group census. The normalizer was written against the
MEASURED schema in `BOOTSTRAP.md` section 3.2 - misspelled keys `mManufactoringDuration` and
`mEstimatedMininumPowerConsumption` used verbatim, asserted by
`tests/data/test_registry.py::test_the_misspelled_keys_are_used_verbatim_not_autocorrected`.

### 2026-08-14 - CS-101 - Docs-file encoding settled by BOM bytes, both encodings handled
Verification: `clockspeed/data/docs_extract.py::sniff_encoding` classifies from the leading
BOM BYTES only. The load-bearing test is
`tests/data/test_docs_extract.py::test_sniff_encoding_classifies_by_bom_bytes_not_by_trial_decode`,
which demonstrates by construction that decoding UTF-8 bytes as `utf-16` does NOT raise -
so a trial-decode sniffer returns mojibake and reports success. Only the byte test is sound.

### 2026-08-14 - CS-100 - Phase 1 gate met: a written spike report with a binary answer per spike
Verification: `docs/_archive/spike-report-s1-s2-s3-s7.md` carries a binary verdict for S1,
S2, S3 and S7; S5-body is recorded under CS-104 and `BOOTSTRAP.md` section 3.1. No phase 2
work was merged before it landed - phase 2 is this session, the report is session 1.
Correction applied to that report this session: it stated the fractional-fluid recipe "takes"
water at 1500. A live re-probe refuted the SIDE - the water is a PRODUCT, not an ingredient.
Counts in the report were correct; only the side was wrong. `BOOTSTRAP.md` section 3.2 now
carries the corrected statement and is authoritative over that line.

### 2026-08-13 - CS-007 - Frozen-file grant: LICENSE copyright holder set to "Clockspeed contributors" by operator decision
Verification: LICENSE line 3 reads `Copyright (c) 2026 Clockspeed contributors`;
`tests/test_scaffold.py::test_license_names_a_real_copyright_holder` passes; grant
adjudicated under `CLAUDE.md` section 6 - operator-sourced, no agent self-grant, frozen
list unchanged. Blast radius is one line in `LICENSE`: `pyproject.toml` deliberately
declines to restate the holder, and `git grep -I "Moonbeam"` returned exactly one tracked
hit, `LICENSE:3`, before the edit.
Adjudicator's common-mode finding, recorded because it survives this item: the change does
NOT deliver the pseudonymity that was offered as its rationale. Every commit is authored
under a real-identity email address, which publishes with the history at the CS-G03 flip
and which this edit does not touch. The holder change stands on its own merits - a
collective holder is routine MIT practice and drifts from nothing - but "protects identity
at phase 7" is NOT its effect. The author-identity question is carried by CS-G03.

### 2026-08-13 - CS-104 - S5 body framing settled; the save body decompresses end to end
Verification: run the phase-1 spike scripts against a COPY of any save; chunk framing is
magic `0x9E2A83C1`, marker `0x22222222`, int64 max chunk size 131072, int8 algorithm 3
(zlib), then compressed and uncompressed sizes each written TWICE, and the decompressed
body opens with an int64 length. Measured on the pinned world: 11 chunks, 102 KB on disk
to 1,440,651 bytes. Recorded in `BOOTSTRAP.md` section 3.1. The header was NOT re-derived.

### 2026-08-13 - CS-005 - S6 settled YES: unlock state is recoverable from the save
Verification: `docs/adr/0004-s6-unlock-state-recoverability.md`. A mature world carries
`mPurchasedSchematics`, 246 distinct `/Schematics/` paths including alt-recipes, 360
`/Recipes/` paths, `mCurrentGamePhase`, `mUnlockedResearchTrees`, `mScannableResourcesPairs`
and the feature-unlock booleans. The pinned onboarding world exposes 14 unlock properties
against the mature world's 30, which is why S6 was NOT settled on it.
ADR: `docs/adr/0004-s6-unlock-state-recoverability.md`

### 2026-08-13 - CS-004 - S4 settled: YES for node geometry, NO for node semantics
Verification: `docs/adr/0003-s4-node-actors-in-save.md`. 626 resource-node actors, 626 with
a valid transform (normalized quaternion, in-map coordinates). No node carries a property
payload and no purity or resource-type field appears in any save examined. This CONTRADICTS
`BOOTSTRAP.md` section 8.3 step 1 as originally written; section 8.3 has been corrected.
ADR: `docs/adr/0003-s4-node-actors-in-save.md`

### 2026-08-13 - CS-003 - S8 settled NO: node placement is not seed-dependent
Verification: `docs/adr/0002-s8-node-data-seed-dependence.md`. Two distinct worlds on build
463028, grouped by the header world token rather than by filename, have byte-identical node
sets: 626 shared positions, zero differences either way. Section 8.3 steps 2 and 3 therefore
remain valid and S4 is not load-bearing.
ADR: `docs/adr/0002-s8-node-data-seed-dependence.md`

### 2026-08-13 - CS-002 - Tier-0 commit gate PROVEN to fire end to end
Verification: re-runnable. Stage any of the nine violation classes and attempt a real
commit; HEAD must not move. Measured this session: 9/9 blocked - U+2014, U+2019, U+00A0,
PEM private key, absolute home path, a `.sav` forced with `git add -f`, a Python syntax
error, an AWS key id and a GitHub token. The commit-msg hook independently rejected a
non-ASCII message. HEAD before and after both `10ca0cf`. Presence was NOT accepted as
proof; the gate was made to actually reject a real commit. See `tests/test_precommit_gate.py`.

### 2026-08-13 - CS-001 - Phase 0 scaffold complete and committed
Verification: `git log --oneline` shows the root commit; `python scripts/verify_env.py`
exits zero with HARD 7/7; `python tools/drift_guard.py` runs clean; `python -m pytest tests`
passes. `.gitignore` landed in the same commit that created history, so no game data, save
file, extracted asset, generated cache or local config has ever been tracked. See
`tests/test_scaffold.py`.

### 2026-08-13 - CS-006 - Section 2 ground truth re-probed; four corrections applied
Verification: `python scripts/verify_env.py` reports the live values. Corrections written
into `BOOTSTRAP.md`: locale file count is 55 not 57; the save library holds three worlds
not one; header version is not stable at 14 (it is 10 on the oldest saves) and the library
spans four builds; and a new section 2.5 records that `py -3` resolves to a DIFFERENT
3.14.4 install carrying no pytest, ruff or mypy. Build string, install path, save location
and the 8900-8911 port band all re-confirmed unchanged.
