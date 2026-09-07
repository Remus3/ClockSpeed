# Clockspeed - live per-item detail, phase 4 - save reader, the CS-9nn block

**Section status: LIVE.** A dated heading in this file records provenance - when the
text was filed, moved or measured - and never that the section itself is historical.

**THIS LEAF HOLDS THE `CS-9nn` BLOCK AND NOTHING ELSE.** Its siblings
`docs/item_notes/phase4-followups.md` and `docs/item_notes/phase4-followups-850.md` hold
CS-800 to CS-849 and CS-850 to CS-899 respectively. **NEITHER SIBLING NAME SPELLS ITS
RANGE HONESTLY**, so trust this sentence and the routing table in `docs/item_notes.md`,
never a filename.

**This is a leaf of `docs/item_notes.md`**, which owns the index and the rules this file
obeys. Read the index for the routing table over every OPEN item, the verbatim rule, and
what this family never contains. Do not restate any of it here.

**What lands in THIS leaf.** Every OPEN item `ROADMAP.md` files under its `Phase 4`
heading whose ID is in the `CS-9nn` block. That block exists because `CS-8nn` filled up at
100 of 100, measured 2026-09-05. Operator decision 2026-09-05.

**CS-901 THROUGH CS-905 ARE NOT ALLOCATABLE, AND THAT IS MEASURED RATHER THAN INHERITED.**
They are synthetic fixture IDs in the drift-guard test corpus - `tests/data/test_drift_guard_data.py`,
with CS-901 and CS-902 also appearing in `tests/test_dated_headings.py` and
`tools/drift_guard.py`. Allocating one would collide with a corpus that asserts on them by
name. The block therefore runs CS-900, then CS-906 onward. **The handoff into session 61
recorded CS-903 and CS-904 as clean. Both were measured FALSE on 2026-09-05 before
anything was filed**, which is why the range is stated here rather than trusted.

---

## CS-900


### FILED 2026-09-05 (session 61) by the merger, MEASURED ON THE RUNNER BEFORE FILING

**THIS ITEM EXISTS BECAUSE CS-896's FIX HAS A CEILING AND THE CEILING IS SHAPED LIKE A
HANDFUL OF TESTS.** CS-896 flips tier 1 to `pytest -n auto`, which is worth 1.222x on the
pytest step. It is not worth the 2x the runner's two cores would suggest, and the reason is
concentration rather than scheduler quality.

**THE PROFILE, taken on the tier 1 runner itself** - GitHub `ubuntu-latest`, `nproc` 2,
7938 MB, Python 3.14.7, run 33972223350 on tree `c33afca`, `4784 passed, 117 skipped in
590.82s`:

| share of the 590.82s step | what |
|---|---|
| 18.9 per cent | ONE test - `tests/save/test_phase4_gate.py::test_the_save_suite_passes_with_no_install_and_no_save`, 111.39s |
| 27.4 per cent | the two slowest tests |
| 45.8 per cent | the ten slowest tests |
| 59.9 per cent | the twenty slowest tests |
| 12.7 per cent | ALL of the roughly 4600 tests costing under 0.2s each |

By file, five files carry 55.7 per cent: `tests/save/test_phase4_gate.py` 114.8s,
`tests/test_liveness.py` 94.6s, `tests/save/test_absolute_claims.py` 48.8s,
`tests/save/test_reach_guard.py` 41.7s, `tests/test_mypy_gate.py` 29.1s.

**WHY THAT CAPS THE PARALLEL LANE.** xdist distributes by test, but the longest single FILE
is 114.8s and the longest single TEST is 111.4s, and neither can be split across workers. At
`-n auto` on two cores the theoretical floor is `max(114.8, 566.25/2)` = 283s. Four measured
parallel runs came in at 424.18s, 475.98s, 483.14s and 470.67s - mean 463.49s, which is
1.64x the floor. **So the binding constraint is not the core count and buying a larger runner
would not fix it.**

**THE OBVIOUS CANDIDATE, AND WHY IT IS NOT OBVIOUSLY SAFE.** The 111.4s test re-runs the
whole save suite in a child process to prove it is green with no install and no save
library. Its docstring says that on the operator's machine - where the game IS installed -
it is the only thing that reproduces that environment. **On CI the parent lane ALREADY IS
that environment**, so the child run re-proves in a subprocess what the lane proves
natively. That makes it a candidate for skipping where the environment is already clean.
**DO NOT TAKE THAT AS SETTLED.** It is coverage-affecting, the child clears env explicitly
while the parent inherits conftest fixtures, and the two are not obviously equivalent. It
needs its own adversarial pass, which is why this is filed rather than done.

**THE INTERACTION THAT MUST BE READ FIRST.** CS-448 is OPEN, tier 1, and its acceptance
names THIS EXACT TEST as flaking under `-n auto`. Anyone reducing this test's cost is
standing on CS-448's toes and should read `docs/item_notes/phase4.md` under **CS-448**
first. Measured 2026-09-05 and recorded there: the CS-448 trigger condition does NOT hold
on the hosted runner.

**WHAT THIS ITEM IS NOT.** It is not "make the suite faster" in general. The sub-0.2s tail
is 4600 tests for 12.7 per cent of the step and there is no lever in it. The item is about
the head of the distribution and nothing else.

**A LOCAL PROFILE IS THE WRONG INSTRUMENT AND THIS IS THE SECOND SESSION TO SAY SO.** The
CS-896 note recorded that the three slowest tests locally are library-backed and cost close
to nothing on the runner. **That is true of ONE of them and false of the other two**,
measured 2026-09-05: `tests/save/test_properties.py` is 152.8s locally and 13.0s on the
runner, but `test_phase4_gate` went 51.5s local to 111.4s on the runner and
`tests/test_liveness.py` 25.8s to 50.5s. The runner is roughly 2x SLOWER for
subprocess-heavy work. Take the measurement on the runner or do not take it.

---

## CS-907


### FILED 2026-09-05 (session 61) by the merger, on an adjudicator's finding that this is the REAL defect

**THE HOOK HAS OUTGROWN ITS OWN STATED CONTRACT AND BOTH HALVES ARE IN THE TREE TODAY.**
`CONVENTIONS.md` section 8 assigns tier 0 pre-push a "fast unit subset" and reserves the
full suite WITH PARALLELISM for tier 2. The hook's own header claims it runs the fast unit
subset. It runs the whole tests directory.

**THE SANCTIONED LEVER IS SHIPPED, TESTED, AND USED BY NOTHING.** `pyproject.toml` registers
a `slow` marker whose own description says it is "a test the pre-push hook may exclude to
keep tier 0 instant", and `tests/test_scaffold.py` carries an arm asserting that marker must
exist so the hook can select a fast subset. Twelve tests carry it, all in
`tests/test_mypy_gate.py`, and no invocation anywhere selects on it.

**WHY THIS IS FILED SEPARATELY FROM CS-906.** The adjudicator ruled that parallelising the
hook treats the SYMPTOM: it imports a tier-2 property into tier 0 and leaves the tier-0
contract still violated. Subsetting is the doctrinally correct remedy and it lost only on
timing - twelve marked tests do not move the number today. **So CS-906 may land and this
item stays open.** Closing CS-906 does not close this.

**DO NOT CLOSE THIS BY MARKING TESTS `slow` UNTIL THE NUMBER LOOKS RIGHT.** A marker applied
to whatever is slowest today is a subset defined by a stopwatch rather than by risk, and the
next expensive test lands outside it. Either the selection rule is stated and defended, or
the contract is corrected to say the hook runs the whole suite and why that is worth its
cost.
---

### RELOCATED 2026-09-06 from the ROADMAP item line, for the CS-926 budget pass

The headline this item carried before its line was cut to the one-liner the
`ROADMAP.md` header asks for. Relocated verbatim, never deleted:

`CONVENTIONS.md` assigns tier-0 pre-push a "fast unit subset" and reserves the full suite with parallelism for tier 2, but the hook runs the whole tests directory while its own header claims it runs the subset, and the sanctioned lever - the registered `slow` marker that `tests/test_scaffold.py` ships a test for - carries 12 tests and is used by nothing


## CS-920


### FILED 2026-09-06 (session 65) by the merger, from an idea another project on this machine raised for itself

**THE IDEA, AND WHERE IT CAME FROM.** A sibling project asked whether numbers it DERIVES and
then COMMITS would be read by an outsider as no different from wiki content. Its answer
split in two, and only the second half transfers here.

**THE FIRST HALF DOES NOT APPLY TO THIS PROJECT AND THAT IS WORTH STATING so nobody files
it again.** That project transcribes measurements into tracked tables. This one does not:
`/data/` is gitignored, the registry is extracted from the game's shipped files AT RUNTIME,
and CS-485 settled that no dataset is lifted from any wiki. There is no committed game
number here for an outsider to lift, so the wiki-equivalence question does not arise.

**THE SECOND HALF APPLIES SHARPLY, AND TO THIS PROJECT'S MEASUREMENTS OF ITSELF.** Its
formulation is that provenance which is DOCUMENT-scoped does not survive the number being
quoted: an outside reader lifts the row, not the document, and the receipt is left behind.
The same failure happens INSIDE this repository, between sessions, without anyone lifting
anything - because a number quoted out of its paragraph loses the conditions it was taken
under, and the next session requotes it as fact.

**MEASURED, IN THIS SESSION ALONE. Three numbers were published and then corrected:**

- a **3.2x** speedup, from comparing readings taken at different times on a contended box,
  corrected to **2.39x** by a paired back-to-back re-measurement. That was the THIRD
  unpaired-comparison error recorded against CS-896.
- **sixteen workers**, which is **eight** - xdist counts physical cores. The evidence was
  present twice before the correction: a builder reported eight, and a failure signature
  read `workers=9`, being eight workers plus one misfiled controller.
- a **shard-specific** variance claim, withdrawn once an adversary showed an identical
  runner pool reproduces the contrast about one time in three.

None of those was a careless reading. Each was a correct reading whose CONDITIONS did not
travel with it.

**THE ITEM EXISTS BECAUSE CS-917 ALREADY DEPENDS ON THE ANSWER.** Its acceptance asks for
"a noise figure that survives its own next reading". **That is a QUERY over a measurement
history**, and today there is no history to query - the readings for CS-896 alone are spread
across roughly seven ledger entries, an item note and a workflow comment, in prose, with
their conditions stated in sentences. A session cannot mechanically ask "was this reading
taken on a quiet box" or "which readings has a later one falsified".

**WHAT THE RECEIPT HAS TO CARRY**, derived from the three corrections above rather than
guessed: the metric and its value and unit; the METHOD (paired or unpaired, standalone or
through the real gate); the worker count actually resolved rather than the core count; the
LOAD STATE, because "another project's suite was live" is the condition that produced two of
the three errors; the date and the commit; and whether a later reading has superseded it.

**WHAT THIS IS NOT.** It is not a benchmarking harness and it is not CodSpeed. It records
readings a human or a session already took, so they can be compared later. And it is not a
licence question: facts are not copyrightable, so no licence on this repository protects a
number in it - what distinguishes a measurement from a rumour is the receipt, not the terms.

**RELATION TO EXISTING DOCTRINE.** `CLAUDE.md` section 4 already says "do not restate a
measured number in prose" and requires one machine-checked owner per fact. That rule is
enforced today only for a few specific numbers - the tier 1 levels, by drift guard (k) and
`tests/test_tier1_budget.py`. This item is that same rule applied to the readings themselves
rather than to the levels derived from them.

---

### RELOCATED 2026-09-06 from the ROADMAP item line, for the CS-926 budget pass

The headline this item carried before its line was cut to the one-liner the
`ROADMAP.md` header asks for. Relocated verbatim, never deleted:

every measured number this project makes about ITSELF lives in PROSE and carries its provenance at DOCUMENT scope rather than ROW scope, so a reading cannot be compared with another without a human reading both paragraphs: this session alone published a 3.2x speedup that a paired re-measurement corrected to 2.39x, a worker count of sixteen that is eight, and a shard-specific variance claim that an identical runner pool reproduces one time in three - and CS-917's acceptance asks for a noise figure that SURVIVES ITS OWN NEXT READING, which is a query over a measurement history that does not exist


## CS-917


### THE ACCEPTANCE CLAUSE HAD A HOLE AND NOW CARRIES THE ORDERING - MEASURED 2026-09-06 (session 65)

**TWO ADVERSARIES ON DIFFERENT LENSES FOUND THE SAME DEFECT IN THIS ITEM'S OWN CLAUSE,
one session after it was filed.** As written it required the warn band be DERIVED FROM a
noise figure that survives its next reading. It never required the band be WIDER than
that figure. Provenance is not width.

**THE CONSEQUENCE, STATED PLAINLY: this item could have closed in full with the band
still narrower than the noise, a red still reachable having never warned, and the CS-896
leaf condition it exists to carry silently dropped rather than transferred.** The clause
now carries the ordering guarantee explicitly.

**THAT MATTERS BECAUSE THE TRANSFER WAS ATTEMPTED.** The merger proposed closing CS-896
by transferring the condition here. An adversary refuted it on exactly this ground and
the merger verified every citation before accepting. The transfer LOST the condition; it
did not move it.


### FILED 2026-09-06 (session 64) by the merger, from four adversarial passes that each named it

**THREE INDEPENDENT ADVERSARIES AND ONE DIRECT MEASUREMENT ALL ARRIVED HERE, which is why it
is an item rather than a remark.** CS-896 watches the lane's DURATION. Nothing watches its
GROWTH RATE, and `grep -n "3.51\|per commit\|slope" ROADMAP.md BACKLOG.md docs/GATED.md`
returned nothing at three separate SHAs this session.

**THE MEASUREMENT.** The lane gained **3.51 seconds per commit** over the 26 commits of
2026-09-05 - the parallel pytest step went 463.49s to 554.70s across them. Every fix applied
to CS-896 buys a fixed number of SECONDS and therefore a fixed number of COMMITS: the split
bought roughly 60, the memoization roughly 25 before it.

**AND THE NOISE FIGURE THAT EVERY WARN BAND WAS DERIVED FROM IS UNSTABLE, WHICH IS THE HALF
THAT MAKES THIS HARD.** Measured on 2026-09-06: the fast shard ran a BYTE-IDENTICAL
population - `3911 passed, 23 skipped` in runs 34021868008 and 34024118253 - in 314.64s and
then 226.24s. **An 88-second swing on identical work.** Three re-derivations this session
each sized a warn band from a noise figure their own next reading falsified: 21s, then 36s,
now at least 88s. **A band narrower than the noise cannot guarantee that growth is visible
before it is fatal**, which is the CS-896 leaf's stated condition.

**THE INSTRUMENT IS PART OF THE PROBLEM.** Fast-shard job-seconds read 323, 359, 358 and
260. Three cluster within 36s and the fourth sits 98s below all of them - the shape of a
HETEROGENEOUS RUNNER POOL rather than one normal distribution. A normal tolerance bound over
that sample gives 564s at n=4 against a 480 ceiling, having given 452s at n=3; the bound
moved the wrong way because the sample was not from one distribution. **Do not answer this
item by taking one more reading.** Characterise both modes, or choose a distribution-free
criterion.

**WHAT THIS ITEM IS NOT.** It is not "make the suite faster" - that is CS-900, which is about
concentration, and its own measurement got WORSE after the split (the most expensive test is
now 81.9 per cent of the save shard's step against 30.4 per cent of the old single step). It
is not a request to raise any level. The levels shipped at 420/480 contain all four readings
and are not the complaint.

---

## CS-919


**Filed 2026-09-06 by the merger, out of CS-918's first real cycle.** Read that closure
entry in `docs/LEDGER.md` first - this item exists because of something the cycle did, not
because of something someone thought might happen.

### WHAT WAS MEASURED

The driver reads `origin/main` before the cycle and again after it, and treats a change as
"our worker pushed". On the first real cycle the worker committed NOTHING - it left ten
files uncommitted in the lane worktree - while another session on the same box pushed
`f80b95af7e2e`. The driver saw the ref move, attributed it to the cycle, waited out tier1,
**dispatched a tier2 run**, and waited 1105.9 seconds for it. The row records
`"ci": {"verdict": "success"}` against a sha the lane never produced.

### WHY THIS IS WORSE THAN IT LOOKS

It is silent, and it fails in BOTH directions. A neighbour's green is written into this
lane's ledger as though the lane had earned it - and a neighbour's RED would stop the night
under `ci_red`, blaming a worker that pushed nothing. Neither shows up as an error; both
read as ordinary rows. The ledger is the only durable record of a night, so a row that
cites the wrong sha is worse than a row that cites none.

### WHAT IS NOT THE FIX

**Do not narrow the window.** The window is the whole cycle - tens of minutes by design -
and any attempt to shrink it trades a large silent error for a smaller silent error.

**Do not assume one lane per box.** That is the assumption that produced this. The operator
runs several projects' sessions concurrently on this machine; the measurement above is that
configuration behaving normally, not an anomaly.

### THE SHAPE OF AN ANSWER

The lane can know what its own worker produced without asking the remote: the worker commits
in a worktree the driver owns the path of, so the driver can read `lane/queue`'s tip before
and after and compare THAT, or read the reflog of the branch it launched into. A sha the
lane cannot attribute to itself must record `unattributable` and grade nothing - an absent
verdict is a real answer, and it is the one CS-918's own driver already gives when the
remote cannot be resolved.

### THE ARM THAT PROVES IT

Redden on a FOREIGN sha landing between the two reads. A test that only checks the happy
path would have passed on the shipped code, because the shipped code is correct whenever
nobody else pushes - which is every run on an idle box and no run on this one.

## CS-929


### FILED 2026-09-06 (session 70) by the CS-927 builder, which correctly refused to sweep it

`clockspeed/surface/server.py` says `/api/advice/<id>/state` are "two of the
NINE endpoints `BOOTSTRAP.md` section 7.1 publishes". Section 7.1 has named TEN
since CS-912 published `/api/registry` - `BOOTSTRAP.md` section 7.1, which
saying so explicitly.

Same root cause as CS-927, different module. It was left untouched deliberately
because it sat outside that slice's declared write-list.

### WHY THIS IS NOT JUST "FIX THE NUMBER"

CS-927 closed by making `pending.py` name the SET and its OWNER rather than its
SIZE, and shipped `tests/surface/test_pending_route_count.py` to keep it that
way. **That detector is scoped to `pending.py` alone** - stated in its own
docstring - so it cannot see this site. Widening the detector is the greater
half of this item; editing the sentence is the lesser half.

`tests/surface/audit_harness.py` already records that CS-912 falsified
"the THIRD sentence in this repository that a new route falsified without
touching the file it sat in". This is the fourth. The population is the finding.

### ALSO SEEN, AND DELIBERATELY NOT FILED

`docs/adr/0012-dashboard-refusal-vocabulary-and-wire-form.md` also says nine.
It is stamped `accepted - 2026-08-29`. An ADR records what was decided when it
was decided; correcting it would rewrite history rather than fix drift. Left
alone on purpose. Do not file it without arguing that point first.

### MEASURED 2026-09-06 (session 70) - the filed acceptance was unachievable

The item originally required "the detector's scope reaches this module, proven
by a mutation that reddens it". **That cannot be done**, and the measurement is
not a matter of opinion: running the shipped CS-927 detector over
`clockspeed/surface/server.py` yields **seven false positives** - all of them
"two templates" phrases about template COLLISION rather than counts - and
**zero hits on the actual stale sentence**.

The reason is structural. The stale noun is **endpoints**, and `COUNTED_NOUNS`
in `tests/surface/test_pending_route_count.py` deliberately excludes it so that
`pending.py` can keep saying "the five unbacked endpoints" about its own set.
Widening the detector to `server.py` therefore either floods or misses.

**So the acceptance was rewritten** to require a guard proven by mutation
WITHOUT mandating that it be the CS-927 detector. Left as filed, this item would
have closed on a green run that measured nothing - the exact shape CS-605
closed on.
## CS-930


### FILED 2026-09-06 (session 70). THE PREMISE THAT SENT THE PROBE WAS REFUTED, AND SO WAS THE LEDGER

The session-69 handoff asked whether the shipped docs file exposes build cost at
all, and warned that if it does not, `BOOTSTRAP.md` carries an unlabelled
assumption and CLAUDE.md section 8 applies. **It does expose it.** The item that
remains is a join, not an acquisition.

### WHAT WAS MEASURED, against the real install

- **There is no `mBuildCost` key. Zero occurrences.** That naive lookup is what
  made this look absent, and it is why the earlier note was written.
- Build cost is carried on the BUILD GUN RECIPES. Of 872 `FGRecipe` entries,
  550 name a build gun in `mProducedIn` and **545 carry a non-empty
  `mIngredients`**. `Recipe_ConstructorMk1_C` inputs are reinforced iron plate
  x2 and cable x8 - that is the Constructor's build cost.
- **It is already inside this project's registry.** A real build yields
  items=750, recipes=872, buildings=68, and all 550 build recipes are present as
  `Recipe` objects with `inputs` populated, tagged
  `unresolved_produced_in=('BP_BuildGun_C',)`, which `clockspeed/data/registry.py`
  already names as a tolerated token.
- **`clockspeed/data/registry.py::automated_recipes` returns 291 and filters all
  550 out.** Correct for its purpose, and the reason they are invisible
  downstream.
- **65 of 68** modelled Buildings have a build recipe whose output joins by
  `Desc_` to `Build_` substitution. The three that do not are part of the item.

### THE EXISTING RECORD IS WRONG AND MUST NOT BE INHERITED

the CS-922 entry in `docs/LEDGER.md` states build "COST DATA DOES NOT EXIST AT ALL" and that
"the docs extractor never reads one". The first clause is FALSE and the second
is FALSE - the extractor reads `KEY_INGREDIENTS` for all 872 recipes including
all 550 build recipes. Only "`Building` has no cost field" is true.

The ledger is append-only, so that entry is not edited; a correction is appended
beside the CS-930 filing rather than written over it.

### WHAT THIS ITEM IS NOT

It is not a data-acquisition problem and must not be scoped as one. It is a join
plus an aggregation over data already loaded. Do not re-pitch extracting build
cost from a wiki or any community source - `CLAUDE.md` section 7 settles that,
and the data is on disk anyway.

## CS-933


### FILED 2026-09-06 (session 70) by an adversary sweeping for SIBLINGS of CS-927

`clockspeed/surface/web/app.js` says "The ten routes `BOOTSTRAP.md` section 7.1
publishes" and "Two of the ten routes take a body".

**IT IS CORRECT TODAY. That is precisely why it is filed.** Every sweep this
session searched for the NUMBER NINE - the stale value - so a restatement
carrying the CURRENT value was invisible to all of them, including the sweep
that produced the CS-927 record's "two siblings". There are three.

**THE LESSON, which outranks the fix.** A drifting-count sweep must be defined
by the SHAPE - an aggregate count restated in prose with no owner and no guard -
and never by the value that happens to be wrong this week. A sweep keyed to the
wrong value finds only the sites that have already broken, which is the set you
already knew about.

### THE FENCE

Do not close this by editing "ten" to whatever the count becomes. That is the
weak fix CS-927 explicitly refused, and it puts the site straight back in the
queue for the eleventh route.

## CS-936

### FILED 2026-09-07 (session 71)

The line as first filed, relocated here intact because the ROADMAP owns
the LINE and this file owns the reasoning:

    CS-936
    the 2026-08-14 PII scrub (`0e273c4`, "Phase 2: data layer, plus the LICENSE ratification and the PII scrub") edited the files FORWARD, so three world names it removed from the working tree remain in the blobs at `10ca0cf` and `d483477`
    measured 2026-09-07 with an armed pickaxe over every ref, controls behaving (a present-string control returned 32 files rc=0, an absent-string control rc=1)
    CONTAINMENT, measured not assumed: those three commits are reachable ONLY from the local branch `archive/local-history`, `git branch -r --contains` returns nothing for all three, and `origin/main` carries none of them, so NOTHING IS PUBLISHED and this is a latent rather than a live exposure
    the two needles that do hit `main` are four-letter alphabetic strings, one of them 54 sites across `registry.py`, `docs_extract.py` and `tier2.yml`, which is the shape of a domain word rather than a leak and is recorded here as a FALSE POSITIVE so a later session does not re-raise it
    the settled decision is private first PUBLIC LATER, so an unpushed branch is one `git push --all` from being the thing that publishes it
    acceptance: either the affected history is unreachable from every ref that can be pushed, or the branch is deliberately retained with the retention recorded and a guard that reddens when a pushable ref contains a scrub-era commit, AND the world-name detector is hardened so a four-letter common word cannot manufacture a finding, proven by an arm that reddens on a planted world name in a pushable ref and stays green on the false-positive shape
    tier: 1

## CS-937

### FILED 2026-09-07 (session 71)

The line as first filed, relocated here intact because the ROADMAP owns
the LINE and this file owns the reasoning:

    CS-937
    a line-pointer whose only content check is NON-BLANKNESS passes a pointer that names the wrong rule
    the `tools/` prohibition pointer in `tests/test_precommit_gate.py` named line 144 of `docs/ARCHITECTURE.md` and the guard stayed GREEN, because that line was non-blank and a markdown target is exempt from the forbid leg
    AND THE POINTER WAS WRONG WHEN WRITTEN RATHER THAN ROTTED, which is the sharper fault and was established by an adjudicator rather than assumed: `git show eeba277` proves that line held the `advisor/` clause on the day the pointer was authored, while the `tools/` rule sat five lines further down, so a live guard certified a citation that never named its own subject, for three weeks
    a dead pointer is visibly dead and this is not
    acceptance: a line pointer is graded against what its own sentence CLAIMS the target says, not merely that a line exists there, without becoming a prose-matcher that reddens on correct history
    the acceptance must state the discharge condition and be proven by TWO arms, one reddening on a pointer silently retargeted to a different non-blank line and one staying GREEN across a whitespace-only reflow of the target
    tier: 2

## CS-938

### FILED 2026-09-07 (session 71)

The line as first filed, relocated here intact because the ROADMAP owns
the LINE and this file owns the reasoning:

    CS-938
    the CS-932 inbox watcher is wired ONLY in an untracked file, so a fresh clone of this repository runs no watcher at all and the operator's standing directive to review the channel has no mechanism behind it
    measured 2026-09-07 and cross-checked against a direct read of both files: tracked `.claude/settings.json` declares `PreToolUse` and `PostToolUse` and nothing else, at HEAD and in the working tree, while the `SessionStart` hook running `tools/inbox_watch.py` lives in the gitignored local settings file beside it, which the ignore file covers and `git ls-files --error-unmatch` confirms untracked
    the tool is tracked and tested and the WIRING is not, which is the same shape CLAUDE.md 2.2 already records for git hooks ("a fresh clone runs zero protection until someone wires it") except that the bootstrap does not cover this one, so nothing would ever wire it
    acceptance: the watcher is reachable from a fresh clone through a TRACKED path, or the bootstrap wires it and says so, proven by an arm that reddens when the wiring is absent from every tracked file
    NOTE the obvious fix edits the tracked settings file, which CLAUDE.md section 6 FREEZES, so it needs its own adjudicated grant and must not be taken as covered by the CS-935 grant, which expired on application
    tier: 1

## CS-939

### FILED 2026-09-07 (session 71)

The line as first filed, relocated here intact because the ROADMAP owns
the LINE and this file owns the reasoning:

    CS-939
    no test sweeps the TRACKED TREE for secrets, so a credential committed before the gate existed is never rescanned
    `check_secrets` in `tools/precommit_gate.py` runs only over staged bytes or explicitly named files, which means it can only ever see what is changing now and is blind to what already landed
    this is the class a sibling measured tonight in its own repo: a live token tracked from the initial commit for 133 days, invisible to every working-tree check because nothing ever re-read the tree
    Clockspeed measured CLEAN on the equivalent sweep this session, but it was measured BY HAND and nothing re-measures it, so the answer is true for today and guarded for no day after
    acceptance: a suite arm sweeps every tracked file and every reachable blob for the secret patterns the gate already owns, importing that detector rather than restating it, proven by a planted credential in a tracked file that reddens and a synthetic fixture that does not
    tier: 2

## CS-941

### FILED 2026-09-07 (session 72), from a sibling's finding re-measured here

RC asked every project on the channel whether its watcher fires on a WITHDRAWAL.
Clockspeed's does not, and this was probed rather than reasoned: acknowledge two
notes, delete one, and the banner reports no unread items while naming the
survivor as the entire inbox. An entire deliverable left the channel in silence.

RC is the project that proved this matters, by pulling a 50-file drop from four
inboxes in one night while every arrival-keyed watcher on the channel reported
nothing.

THE SUBTLETY THAT MAKES THE OBVIOUS FIX WRONG, and it came from RC rather than
from here: once keys carry digests, an EDIT and a WITHDRAWAL both move the key.
A report computed by comparing raw keys therefore files one edited note in two
contradictory sections, as an arrival and as a retraction. The comparison has to
strip the digest and match the stable NAME - an edit keeps its name, a
retraction loses it.

### THE FENCE

Do not close this by unioning the seen set instead of rewriting it. The rewrite
is a deliberate property with its own arm, and a union grows without bound as
notes are renamed or edited.

### FILED 2026-09-07 (session 72), as an amendment from a sibling's correction

LW shipped this property, sent the construction to four repos, and corrected
itself twenty minutes later. The defect is in the construction, so it is
recorded here BEFORE the implementation rather than after.

LW derived the withdrawal set from `reported | seen` while the acknowledgement
pruned only the SEEN record. A withdrawn name therefore sat in the report record,
re-derived itself on every run, and could never be cleared by anything. That is
not cosmetic: it is a permanent line reporting an event the operator has already
acted on, in the one section of the report with no artifact left on disk to
check it against, and a report the reader cannot clear trains the reader to skip
it.

TWO THINGS TO CARRY INTO THE IMPLEMENTATION HERE:

  1. THE BASELINE IS `reported | seen`, NOT `seen` ALONE. The motivating
     incident was notes LISTED at session start and pulled before anyone ran the
     acknowledgement - those exist in the report record only, so a seen-only
     baseline scores the exact case the feature exists for as a non-event.
  2. WHATEVER THE BASELINE READS, THE ACKNOWLEDGEMENT MUST PRUNE. Three arms,
     not one: an unacknowledged withdrawal survives to the next session, an
     acknowledged one does not come back, and the pruning cannot become a second
     acknowledgement path that quietly consumes unread mail.

HOW IT WAS FOUND IS THE TRANSFERABLE HALF, and it is not a test. Every arm
passed, including four new withdrawal arms - they asserted that a withdrawal
REPORTS and never that it STOPS reporting. It was found by running the shipped
command on the live inbox: report, acknowledge, report again. AN ARM THAT PROVES
A THING APPEARS IS NOT THE ARM THAT PROVES IT CAN GO AWAY.


## CS-942

### FILED 2026-09-07 (session 72), measured in the session that filed it

`SessionStart` fires once. Two notes arrived in `moon_sync_inbox/` while this
session was running - the inbox went from 66 notes to 68 - and neither surfaced,
because the only path that reports them had already run. RC measured the same
defect in their tree and shipped a second, report-only hook on the operator's
turn: their figure is 97 ms including interpreter startup and hashing 3.2 MB.

THE PART THAT MUST NOT BE LOST IN THE COPY. That second path REPORTS and never
acknowledges. LL measured why: a hook that marks seen fires for every subagent
start too, so the first subagent consumes the operator's queue and the
operator's own next start then honestly reports nothing new. Listing and
acknowledging stay separate acts, which is already this tool's oldest property.

The wiring lands in the same frozen settings file as CS-938 and needs the same
adjudicated grant, so the two travel together.

## CS-943

### FILED 2026-09-07 (session 72), from reading a sibling's payload rather than from a probe of this tree

`save_seen` returns `None`. An `OSError` on the write - a read-only disk, a
locked store, a full volume - escapes as a traceback out of a hook that runs at
session start, and the session then surfaces NOTHING. That is the whole-channel
outage this project warned four siblings about in the same session, one layer
down in its own code.

RSC's equivalent returns a bool and prints "could not update the watermark - it
stays where it was". That is the better design and it is adopted by description,
not by copy.

The second half is RSC's arm rather than RSC's code: nothing here asserts that a
raw exception string never reaches the report. A traceback is payload wearing a
different hat - it can carry a path, a name, or a byte of a sibling's file into
the one voice a session has no reason to distrust.

## CS-944

### FILED 2026-09-07 (session 72), from RC's finding re-measured here

RC left a merged worktree on disk inside its repo and two guards that walk from
the root scanned a second copy of the tree. Measured here: ten test modules walk
with `rglob` and exactly one excludes the worktree directory. Latent rather than
live - the worktree directory is empty today - and this project's default session
shape is worktree-isolated agents, so it will not stay latent.

LW's half is the one worth keeping: A DUPLICATE TREE ONLY EVER ADDS FILES, so a
guard asking "does anything match?" goes falsely RED and announces itself, while
a guard asking "does everything exist?" goes falsely GREEN and never does. Only
one of the two directions tells you. A corpus taken from `git ls-files` is
structurally immune to both.

## CS-945

### FILED 2026-09-07 (session 72), measured after telling a sibling it was fixed

52 of 62 local branches are ahead of `origin/main` and contained by no remote
ref. That is single-copy work by the definition this channel agreed, one
`git branch -D` away from loss, and RC asked every project to measure it.

THE PART THAT MAKES IT WORTH AN ITEM RATHER THAN A COMMAND. This project told RC
on 2026-09-06 that its push gap was fixed. It was not. The claim was made without
re-measuring, which is the fault this project has filed against others twice in
two sessions.

Charter v4's worktree order is three steps, not two: commit onto the worktree's
own branch, PUSH the branch, then remove the worktree. Step 2 is RC's addition
and is the one this tree does not satisfy.

## CS-946

### FILED 2026-09-07 (session 72), on an operator ruling

The operator adopted convergence charter v4 as written, including section 0(b),
which names RC as final adjudicator on a deadlock, and accepted the `cs` lane
slot.

THE SLOT REVERSES ADR-0017 AND THE REVERSAL MUST BE RECORDED BEFORE IT BINDS.
ADR-0017 declined to join the machine-wide ProgramData bucket on the ground that
consuming a slot other trees ration is a behavioural change to another tree made
unilaterally. That reasoning does not become wrong because the answer changed -
what changed is that the slot is now offered and reserved rather than taken. A
superseding ADR records both.

The second half is mechanical and RC measured it first: the lane lock writes the
repository ROOT PATH as its repo field, a full path containing a space. Under a
keyed reservation that silently creates a second reservation the day a checkout
moves, which is exactly how a sibling's rename moved its own reservation.

## CS-947

### FILED 2026-09-07 (session 72), on an operator ruling

CAVEMAN ULTRA is adopted. It is a `SessionStart` hook imposing a terse output
dialect, and this project has never had one - a grep of the tree returns nothing
but two note filenames in a gitignored store.

TWO THINGS MUST BE RECORDED BEFORE THE EDIT. The wiring lands in
`.claude/settings.json`, which `CLAUDE.md` section 6 freezes, so it needs its own
adjudicated grant routed the way CS-935's was. And it needs a stated interaction
with `CLAUDE.md` section 2.3, which already constrains output length here for a
different reason - operator attention across parallel sessions rather than a
fleet dialect. Two rules governing the same surface, both live, is the drift shape
section 4 exists to prevent.

The acceptance is FIRING, not declared. A hook proven by its configuration is the
class of evidence this channel has refuted three times this week.

## CS-948

### FILED 2026-09-07 (session 72), on an operator ruling

The operator ruled that this project reciprocates verbatim payloads. It has no
manifest producer and no scrub attestation, and a note from RC credits it as
already shipping `MANIFEST.sha256` - a credit that cannot be re-derived from this
tree, so it is recorded as unverified rather than accepted.

THE RISK IS ASYMMETRIC AND IS THE REASON THIS IS AN ITEM RATHER THAN A SCRIPT.
Non-negotiable 3 forbids the account id, the world name, the Windows user and any
home path leaving this tree, and non-negotiables 11 and 12 make a save-derived
artifact personal data. An outbound payload is the one surface where a scrub
defect is unrecoverable, because the bytes are in four other repositories before
anyone re-reads them. RC pulled a 50-file drop from four inboxes for exactly this
reason after this project's own sweep found account names in 19 of 48 files.

The attestation must name HOW the scrub was verified, not that it was, and the
refusal must never echo the string it caught.

TWO SIBLINGS HAVE ASKED THE CHANNEL FOR PROSE RATHER THAN SOURCE. The ruling
stands for the channel as a whole; delivery is per-recipient, and nobody who
asked not to receive bytes gets them.

### FILED 2026-09-07 (session 73), on a measurement and an operator ruling that narrow this item

**THE CREDIT IS NO LONGER UNVERIFIED, AND THE HONEST DISPOSITION IS SPLIT.** RC
measured the delivered `MANIFEST.sha256` sitting in its own inbox: 69 rows,
`sha256sum -c` reporting 69 of 69 OK days after delivery, with the only two
unlisted files being the manifest itself and its covering note. So the ARTIFACT
is verified and the PRODUCER still does not exist here - a reproducibility gap
rather than a false credit. This project asked for the credit to be marked
UNVERIFIED and has withdrawn that request. RC separately withdrew the inference
it had drawn from the artifact, that this project keys its watcher on a manifest;
it does not, and a sender-supplied manifest is never the key.

**THE PREMISE NARROWED.** The operator ruled 2026-09-07 that prose only is this
project's STANDING DEFAULT to the whole channel, not an LL-specific exception.
Two siblings asked; the ruling covers all four. No verbatim payload is owed to
anyone, and none will be sent unless a sibling asks for a specific named file.
The reciprocation this item was opened to make safe is therefore not scheduled.

**WHAT SURVIVES THAT.** The producer half still earns its place, because the
artifact this project already shipped cannot be regenerated from this tree, and
a per-file request is still an outbound payload with the same asymmetric risk.
The scrub attestation and the planted-leak proof are unchanged. What is gone is
the deadline.

## CS-951

### FILED 2026-09-07 (session 73), on a measured channel failure

A watcher reports what leaves ITS OWN inbox. A drop pulled from someone else's
inbox is invisible to the puller by construction, and that is not hypothetical:
on 2026-09-07 a sibling withdrew a payload from five inboxes, then cited it in
two later notes, and no watcher on the channel said the bytes were gone. This
project lost work to it - reasoning about a delivery it could not read and
unable to tell "never arrived" from "arrived and was pulled" from the inside.
The answer had to come from two other repositories reading their own disks.

**CS-949 fixed the INBOUND half here and does not touch this one.** Every
participant now reports what left its own inbox; nobody reports what they
removed from someone else's. Four repositories have named this gap and none has
proposed a mechanism.

THE HARD PART IS NOT THE RECORD, IT IS OWNING THE DELIVERY. A record of what
this repo sent is only as good as the guarantee that every delivery goes through
the thing that writes it. A hand-run copy leaves no record, and a record with
holes in it reports a withdrawal that never happened or misses one that did.

## CS-952

### FILED 2026-09-07 (session 73), self-disclosed

The `SessionStart` wiring lives in `.claude/settings.local.json`, which
`.gitignore:150` excludes. A fresh clone of this project runs no watcher at all,
while this project has been publishing "fires without the operator asking" as
YES on the channel. The property is true of THIS WORKING COPY and false of the
repository, and those were reported as the same thing.

**THIS IS THE FRESH-CLONE RULE IN CLAUDE.md SECTION 2.2 WEARING A DIFFERENT
HAT** - a fresh clone runs zero protection until someone wires it - and the
watcher was never brought under that bootstrap.

**TOUCHING `.claude/settings.json` NEEDS THE SECTION 6 FROZEN-FILE GRANT**,
routed through an adjudicator and recorded in `docs/LEDGER.md` BEFORE the edit.
No session grants itself the exception. The correction half of the acceptance -
publishing the honest answer - needs no grant and can go first.

At least one sibling has disclosed the identical hole in its own tree, so the
checker that would catch it must be run against its author before it is run
against anyone else.

## CS-953

### FILED 2026-09-07 (session 73), from a sibling's measured failure

RC ran a history rewrite with a rename table keyed on each file's path AS IT
EXISTS AT HEAD. The filter callback receives the path belonging to whichever
COMMIT it is filtering, so every file that had ever been MOVED went unrenamed at
each of its earlier paths. Result: 2195 vendor-name hits in the rewritten
history, **none of them in a blob** - all in tree objects, which is where
filenames live. A content scrub can be complete and still publish the names.

THE PREVIOUS PASS HAD VERIFIED "ALL PURGED PATHS ZERO" AND THAT WAS TRUE AND
USELESS. It checked eleven named path patterns and no vendor name was among
them. The check confirmed the absence of things already known to be absent.
Widening it also surfaced 27 scraped images and two scraped JSON files that
appeared in no plan - dropped rather than renamed, because renaming scraped
third-party data keeps the data and hides only whose it is.

**THIS BITES CS SPECIFICALLY** because CS-700's phase-7 gate is a going-public
checklist and this project is going public. Two further surfaces from the same
report: a mirror clone DOES fetch `refs/pull/*/head` (531 commits existed on no
other ref), and deleting a repository deletes its LFS store. The git object
store is not the whole surface.
