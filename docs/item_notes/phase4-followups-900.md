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

## CS-958

### MEASURED 2026-09-08 (session 76), four adversarial lenses against the REPAIRED sender

Candidate frozen at `25ff29f`, tree clean before and after, confirmed by all
four graders and again by the merger. Four adversaries, four independent
lenses, FOUR REFUTED VERDICTS. None of the four wrote a byte into any of the
five real `moon_sync_inbox` directories; counts were identical before and
after in every report. The repairs at `aff7c20` answered a pass against
`bbd7347` and had never been graded themselves; this is that pass.

**F1 - THE NOTE'S FILENAME AND THE DESTINATION NAME ARE NEVER GRADED, AND THE
RECORD STAMPS THEM CLEAN.** `grade()` takes `payload: bytes` and nothing else;
merger-confirmed signature `(payload: bytes) -> tuple[int, str, str]`. The same
account-name value the gate REFUSES in a note's content is accepted as that
note's FILENAME, echoed to stdout, written into every sibling inbox as a
filename, and recorded under `"gate_verdict": "CLEAN"`. Non-negotiables 3 and
12. This is the severe one: the record permanently attests a grade that never
covered the strings it holds. Synthetic canary reproduction: a note whose
FILENAME is a well-formed AWS access key id delivers with exit 0, while the
identical string in CONTENT returns `<pii:credential>` and exit 1. The canary
itself is not reproduced here - the COMMIT gate refused this very paragraph when
it was, which is the frozen gate doing its job and is not to be excluded around.

**F2 - `--to <this repository's own directory name>` DELIVERS INTO THIS
REPOSITORY'S OWN INBOX.** The self-exclusion lives inside `inbox_holders`,
which only `--all` calls; `resolve_targets` never consults it. Merger-confirmed
with its own positive control: `resolve_targets(Path("C:/"), ["Clockspeed"])`
resolves to `C:\Clockspeed\moon_sync_inbox\...` with zero problems, while
`inbox_holders(Path("C:/"))` excludes it on the same run. The property the item
cares about is "a note never lands in our own inbox"; the code guards only the
discovery path, and the only arm covering it guards the same half.

**F3 - A JUNCTION UNDER THE CHANNEL ROOT LEAVES THE CHANNEL ROOT.**
`is_plain_segment` grades a STRING and cannot see a reparse point;
`resolve_targets` then follows it through `is_dir()`. Demonstrated end to end
against a synthetic root: `mklink /J <root>\escape_hatch <outside>` then
`--to escape_hatch --send` reported `DELIVERED ... [gate CLEAN]` exit 0 with the
note written outside the root. `--all` follows it too. The record holds no path
by design, so it cannot distinguish a contained delivery from an escaped one.
`NUL`, `CON`, `COM1`, `CLOCKS~1`, a fullwidth solidus and a trailing dot are all
ACCEPTED by the shape check and refused later only by `is_dir` - contained by
accident, not by the guard.

**F4 - COMMIT-PHASE LITTER IS AN UNRECORDED FULL DELIVERY.** `commit_all`
returns on the first failure and nothing ever unlinks the staging files of the
destinations that were never renamed. Measured: a three-destination send
reported `DELIVERED to 1 of 3`, exit 1, and left
`<sibling>/moon_sync_inbox/<note>.md.tmp` BYTE-IDENTICAL to the note (`cmp`
clean). `tools/inbox_watch.py` reads it as `1 UNREAD ... 1 loose file(s)`. The
sibling has the whole payload while our record says it was not delivered -
precisely the CS-951 hole this module exists to close. It is also PERMANENT: the
staging-name validation then refuses every future send to that destination, even
as a dry run, and the remedy is hand-deleting a file inside another repository.

**F5 - THE TOCTOU BETWEEN VALIDATION AND RENAME SILENTLY DESTROYS A SIBLING'S
NOTE.** `resolve_targets` checks `target.exists()`; `commit_all` calls
`.replace()`, which overwrites. Control: a note present at validation time is
refused and the victim survives. Race: a victim written inside the window was
replaced, with `SEND_EXIT=0`, `DELIVERED ... [gate CLEAN]`, and an ordinary
record entry. Won at the tightest two-destination window `destroyed=1` over 10
attempts, so it is not an artifact of a wide N.

**F6 - A COMPLETE SUCCESS EXITS 1.** With the record path unwritable, both notes
were DELIVERED and the tool exited 1 through `_refuse`. The docstring calls 1
"refused ... Fail closed" and the codes "a closed set a caller can branch on".
Channel, record and exit code disagree on the same run.

**F7 - CASE-VARIANT AND TRAILING-DOT DESTINATIONS DEFEAT THE DEDUP.**
`dict.fromkeys` dedups case-SENSITIVELY while Windows resolves case-
INSENSITIVELY, so `--to X --to XX` where both spell one directory stages one
`.tmp` twice and the second rename raises `FileNotFoundError`. The tool then
reports a PARTIAL delivery when the one real destination landed completely. A
trailing dot is stripped by Win32, so the note lands in `Lanternlight/` while the
record files it under `"Lanternlight."` - a name no destination has.

**F8 - AN EMPTY ENVIRONMENT OVERRIDE SELECTS THE REAL RECORD.** `record_path()`
tests truthiness, so `CLOCKSPEED_OUTBOUND_RECORD=""` returns
`data/outbound_deliveries.json`. Merger-confirmed with its control. A wrapper or
arm that CLEARS the variable rather than unsetting it writes to the operator's
live record - the accident session 75 already had once.

**F9 - THE SUITE DOES NOT GRADE THE GUARD.** `is_plain_segment` appears ZERO
times in `tests/`, merger-confirmed by search; deleting its call site would
leave the suite green. Pristine floor observed at `34 passed`, 0 skipped. Two
SUBTLE mutants of the exclusion shipped green where deleting it outright reds
the arm: comparing `entry.name` to `REPO_ROOT.name`, and dropping `.resolve()`.
`test_all_does_not_broadcast_to_this_repository` guards on an UNTRACKED
directory, so it skips in CI, in a fresh clone, and in EVERY WORKTREE - which is
this project's default session shape. Its neighbour's `real_inbox_counts()`
is a POOLED sum, so one file added and one removed compares equal.

**F10 - NAMED, NOT PROVEN.** `stage_all` appends to `staged` only AFTER
`write_bytes` returns, so a mid-write failure leaves the raising file behind
while stderr says the staged files were removed. Forcing ENOSPC on this shared
box was refused as unsafe. Do not close this one by reading it.

**WHAT SURVIVED, and is not to be re-litigated by a repair.** No payload BYTE
reaches the record by any route four lenses could find. `safe_exc_text` redacts
the absolute path in `FileNotFoundError` (control: raw Python printed it, the
tool printed only `No such file or directory`). `QuietParser` holds against a
note's full text passed as `--note` (control: a stock parser echoed it). The
record is gitignored, `.gitignore:132:/data/` by `git check-ignore -v`. The
gate-before-destination ordering, the single read, and the STAGE phase's
all-or-none behaviour all held.

### THE REPAIR DECOMPOSITION for F1, F2 and F3 - filed 2026-09-08 (session 76)

**F1, F2 AND F3 ARE NOT THREE DISJOINT SLICES, AND SAYING SO IS THE FIRST
FINDING OF THE DECOMPOSITION.** All three land in `resolve_targets` and `main`
of one file, plus one test file. CLAUDE.md section 5 requires disjointness to be
CHECKED before dispatch rather than hoped for, so three parallel builders here
would be three agents editing one function - the failure this project already
measured in session 45 as a tree moving under its own grader. They are ordered,
not parallel.

**THE ORDERING IS FORCED, NOT PREFERRED.** F3's repair re-derives a
destination's NAME from its RESOLVED path, because that is what makes the record
name a directory that exists (F7: a trailing dot landed in `Lanternlight/` and
was recorded as `"Lanternlight."`). F1 grades the destination name. So F1 must
grade the name F3 produces, or it grades a string the tool then discards. **S1
before S2. Not concurrently.**

**S1 - CONTAINMENT AND IDENTITY. Closes F2 and F3, and F7's record lie falls
out of it.** Write-list: `tools/outbound_send.py` (`resolve_targets`,
`is_plain_segment` and its call site), `tests/test_outbound_send.py`.
The mechanism is one idea applied twice: STOP GRADING THE STRING AND START
GRADING THE RESOLVED PATH. A destination is accepted only when
`(root / name / INBOX)` resolves to a directory whose grandparent IS the
resolved channel root, and whose resolved path is not `REPO_ROOT`. That single
check refuses the junction (F3), refuses `--to <own name>` on the path
`--all` never takes (F2), and makes a trailing dot either resolve to its real
directory - which is then recorded under the name that directory actually has -
or be refused. `is_plain_segment` STAYS as a cheap front check; it is not the
containment guarantee and its docstring must stop implying it is.
Arms that must FAIL FIRST, each named because a passing arm written after the
fix proves nothing: a junction under a synthetic root is refused; `--to` at this
repository's own directory name is refused; a trailing-dot spelling is either
refused or recorded under the resolved name; two case-variant spellings of one
directory collapse to ONE target rather than producing the false PARTIAL of F7.
**Every arm uses a SYNTHETIC channel root** - the existing self-exclusion arm
guards on the untracked real inbox and therefore skips in CI, in a fresh clone
and in every worktree, which is this project's default session shape. That
guard is deleted as part of this slice, not left beside the new arms.

**S2 - THE METADATA IS GRADED. Closes F1.** Write-list: `tools/outbound_send.py`
(`gate_phase` or a named step beside it, and every line that prints a name),
`tests/test_outbound_send.py`. **NO CHANGE TO `tools/outbound_gate.py` IS
NEEDED and none is authorised without its own finding**: `scan()` already takes
text, so a filename is graded by the same rule table as a payload, and a second
scanner would be the CS-948 mistake in a new place.
Two decisions the builder does NOT get to make silently, because both are
visible in the record forever:
(1) the metadata grade consumes the REFUSALS from `scan()` and NOT its coverage
rows - coverage is a property of the machine and is already accounted for by the
payload's grade, so folding it in again would report UNMEASURED twice for one
send; and
(2) a dirty name REFUSES THE WHOLE SEND. It does not rename, does not warn, does
not deliver to the clean destinations. The settled fence is that the outbound
gate refuses and does not rewrite, and a filename is the one string that is
simultaneously outbound bytes, a record field and a thing a sibling's watcher
prints.
**THE ORDER OF OPERATIONS IS THE REPAIR, not an implementation detail.** The
tool currently echoes `note.name` to stdout in its DRY RUN and DELIVERED lines
and writes it to the record; measured, an ungraded account name reached stdout.
So the name is graded BEFORE any line that prints it and before any record entry
is built. An arm must pin that a refused name never appears on stdout or stderr,
with a positive control showing the arm can see a name when one is printed.

**WHAT IS EXPLICITLY OUT OF SCOPE HERE.** F4, F5 and F6 are the commit phase and
the exit-code contract; they are a separate slice against different functions
(`commit_all`, `perform_send`) and must not be swept into these two. F8 is a
one-line truthiness fix that belongs with them. F10 is unproven and is not
repaired on a reading.

**HOW IT IS GRADED.** S1 merges, then S2 is cut from the merged tree - not from
`25ff29f`, and the dispatch says so, because five of five worktree agents in one
past session started behind their stated base. An adjudicator that produced
neither slice rules on the merged result at a FROZEN sha, and the refutation
pass re-runs the F1, F2, F3 and F7 reproductions recorded above rather than
reading the diff. A fix that looks right and changes nothing has already shipped
here once.

**THE SEND STAYS BLOCKED UNTIL BOTH LAND.** The A1 notice RC is waiting on goes
out through this tool, and F1 means the tool is currently the leak it was built
to prevent.

### S1 WAS REFUTED AT ITS FIRST CUT - MEASURED 2026-09-08 (session 76)

Branch `cs958-s1` at `3ed5885`, graded by an adversary that did not build it, at a
frozen sha, tree unmoved, no real inbox touched. **The mechanism HELD and the
suite did not.** Recorded because the mechanism surviving is the part a later
session will otherwise re-litigate, and the suite failing is the part it will
otherwise inherit.

**HELD, and not to be redesigned:** the resolved-grandparent check refused a
single junction, a two-deep junction chain, an INBOX-level junction pointing at
another repository's inbox, a `subst` drive and a real UNC channel root - each
against a positive control proving the same fixture escapes the unrepaired tool
at `4659b86` with exit 0. The re-derived name was TRUE for an 8.3 short name, a
case variant, a trailing dot, a trailing space and a junction alias, and all
three spellings collapsed to one target with nothing left undelivered.

**D1 - THE SUITE DOES NOT GRADE THE FIX. Three of four subtle mutants ship a
green 40 of 40, and two of them restore a measured finding of this item
verbatim.** `project.parent.name != resolved_root.name` delivers outside the
channel root at exit 0 - F3 restored. Keying the dedup on the UNRESOLVED inbox
reproduces the false PARTIAL - F7 restored. Dropping `.resolve()` on the root is
green because pytest resolves `basetemp`, so the one arm calling
`resolve_targets` directly hands it an already-resolved root: **a fixture built
parallel to the implementation, which is the shape that makes an arm agree with
a bug.** Only removing the `REPO_ROOT` half was killed.

**D2 - THE ORDINAL IS WRONG BY THE NUMBER OF EARLIER DUPLICATES.** `main`
applies `dict.fromkeys` before `resolve_targets` enumerates, so a repeated
spelling shifts every later position. Measured on five typed names: reported as
3, typed 5th. The docstring added by the repair claims the ordinal is what an
operator needs to fix the right name, which is the claim the measurement
refutes. Under `--all` it indexes a sorted discovery list the operator never saw.

**D3 - F2'S ACCEPTANCE CLAUSE STILL FAILS IN THE SHAPE THIS PROJECT ACTUALLY
RUNS IN.** `REPO_ROOT = Path(__file__).resolve().parents[1]`, so a copy running
from a WORKTREE computes its identity as the worktree and `--to Clockspeed`
resolves into the real repository's inbox exactly as before. Both new arms
`monkeypatch.setattr(sender, "REPO_ROOT", ...)`, so the CLAUSE is graded and the
BINDING never is. The old arm's fault was skipping in a worktree; the
replacement always runs and still cannot see the worktree hole. **A monkeypatch
that supplies the value under test converts an integration property into a unit
tautology.**

**D4 - the `--all` fail-closed behaviour is wider than the builder named.** Any
sibling carrying a reparse point OR a dot-prefixed directory name refuses the
WHOLE broadcast, with a diagnostic that names no directory. Latent today - all
five real siblings measured clean - and it is a real regression in usability.

**D5 - one vacuous ASSERTION, not a vacuous arm.**
`assert_absent_in_any_case(str(tmp_path), (raw,))` searches `json.dumps` output,
where every backslash is doubled, so a record plainly holding the path scores
zero hits while both controls score one. The arm's other checks still bite.

**D6 - an echo path survives, declared rather than fixed.** `--to someoperator`
returns `destination someoperator has no moon_sync_inbox directory` - raw
operator input on stderr, which is the class non-negotiable 3 names. S2's
write-list owns it.

### S1 MERGED AFTER ITS REPAIR PASS - MEASURED 2026-09-08 (session 76)

All four refutation defects answered, and the merger re-ran the evidence rather
than taking it on report: `47 passed`, 0 skipped, exit 0, `ruff check` exit 0,
only the two write-list files changed, and the five real inboxes unmoved -
reconciled against a recursive count that differs from a top-level one only
because the channel carries PAYLOAD SUBDIRECTORIES a top-level count never sees.

**The three green mutants are now killed**, each re-planted against the final
formatted file, asserted landed, and restored from a byte snapshot. The
`.resolve()` mutant needed an arm that passes a deliberately NON-canonical root,
because the previous fixture was resolved by pytest's own `basetemp` before the
implementation ever saw it.
**The identity binding no longer comes from `__file__`.** It resolves the
repository through the `.git` entry - a FILE in a worktree, carrying a `gitdir:`
line into the main checkout - and degrades rather than raising when there is no
`.git` at all. Pinned by an arm that runs the tool AS A SUBPROCESS from a real
git worktree, which is the only shape that grades the binding rather than the
clause.
The typed ordinal is now true with duplicates present, and `--all` names no
ordinal at all: it says to re-run with `--to`, because an index into a sorted
discovery list the operator never saw is not actionable.

**NOT YET REFUTED, and that is the state it merged in.** The repair answered an
adversary and has had no adversarial pass of its own. Four demonstrated defects
in the first cut is a reason to expect a second cut is not clean.

**A NEW ASYMMETRY THE REPAIR INTRODUCED AND DID NOT RESOLVE.**
`inbox_holders` still self-excludes on the file-relative `REPO_ROOT` while
`resolve_targets` now uses the repository-resolved binding. From a worktree with
an explicit `--channel-root` at the real sibling root, `--all` would discover the
main checkout and `resolve_targets` would then refuse the WHOLE broadcast. Fail
closed, not a leak, and unverified by an arm - it is D4's shape in a second
place, and it belongs on the follow-up slice's write-list with D4 and D6.
`REPO_ROOT` deliberately still binds `DEFAULT_RECORD`, because repointing that
at the main checkout would make a worktree run write the operator's live record.

**THE SHAPE OF THE REPAIR, so a later session does not mis-scope it.** F1, F2
and F3 are the item's acceptance clauses failing, not polish: the gate is not in
front of everything that leaves, the exclusion does not cover the path an
operator will actually type, and the channel root does not contain. F4 and F5
are the record telling the reconciler something false, which is worse for CS-951
than no record. Do not repair any of them without an arm that FAILS first, and
do not bank a fix on the code change - re-run each reproduction above.

### S2 MERGED AND THE F1 REPRODUCTION NO LONGER REPRODUCES - MEASURED 2026-09-08 (session 77)

**F1 IS CLOSED. F2, F3 and F7 were closed by S1.** What remains OPEN on this
item is F4, F5, F6, F8, F10, D4 and D6. Merged files: `tools/outbound_send.py`,
`tests/test_outbound_send.py`. No change to `tools/outbound_gate.py`, as the
decomposition required.

**THE MECHANISM.** `grade_names` grades a metadata string through `gate.scan` -
the same rule table, exclusions and independent oracle a payload meets, not a
second scanner. It consumes the REFUSALS and not the coverage rows, carries the
WARN tier through as visible notices, scans a whole batch in one pass and
attributes each finding by the line number `Finding` already carries. Graded:
the delivered filename, the STAGED filename, every destination name as typed,
and every destination name as RESOLVED. `resolve_targets` is now resolve, grade,
report - phase two resolves without naming anything, phase three grades the
resolved names, phase four reports and may name them because they are graded.
Verified by `tests/test_outbound_send.py`, section METADATA 27-38.

**THREE ADVERSARIES ON THE FROZEN `519cadf`, THREE REFUTED VERDICTS, AND EACH
WAS RIGHT.** Recorded because every one of them found a defect a green suite of
36 arms could not see.

- **THE STAGED FILENAME WAS NEVER GRADED.** The writer creates `<note>.tmp` in
  the sibling's tree and renames it after; that string is four characters
  longer than the graded one, and a rule with a LENGTH FLOOR is satisfied by
  exactly that. Measured in process: a bearer-shaped run one character short of
  the twenty-character floor scans CLEAN, the same name plus the suffix scans
  REFUSED. Driven end to end, the refused spelling reached a sibling's inbox and
  `tools/inbox_watch.py` printed it as a loose file.
- **THE WARN TIER WAS DROPPED ON THE FLOOR.** The gate has three tiers and the
  first cut implemented two, so the identical short discovered value that
  prints `WARN <pii:world-name>` as CONTENT went out SILENTLY as a destination
  NAME and into the record. F1's own shape one tier down.
- **A RESOLVED-NAME REFUSAL WAS BYTE-IDENTICAL TO A TYPED-NAME ONE**, so an
  operator whose typed name was clean was sent to inspect that clean name. D2's
  rule - an ordinal pointing at the wrong thing is worse than none - in a second
  place.
- **THE `locate` HALF OF `_which` WAS DISCARDED** at the metadata call site, so
  an `--all` refusal named a destination that cannot be named and gave no way to
  find it.
- **THE TWO `already holds` REFUSALS NAMED NOBODY.** The first cut suppressed the
  resolved name there; under `--all` that tells an operator broadcasting to five
  siblings that one holds the note and not which. The fix is ORDER, not silence.

**FOUR MUTANTS SURVIVED ALL 36 ARMS OF THE FIRST CUT**, and the reasons
transfer. `line1-attribution` - pinning every finding to batch line 1 - survived
because every fixture put its dirty value at index 1, either as a single-entry
batch or because the credential spelling sorts ahead of the ordinary names under
`--all`. **A BATCH-ATTRIBUTION MECHANISM IS UNTESTED UNTIL A FIXTURE PUTS THE
FAULT SECOND.** `unmeasured-wins` survived because every arm passed
`--allow-unmeasured`, so a documented precedence was never reached: **A FLAG
EVERY ARM PASSES IS A BRANCH NO ARM GRADES.** `warnings-folded-in` survived
because the warn tier is structurally unreachable from this suite - `base_env`
makes every save-derived class underivable - so the arm stubs the gate and
grades this module's own consumption rule instead. `skip-typed-only` survived
because no discovered-path message renders a name.

**AND ONE MUTANT IS EQUIVALENT, WHICH IS A DIFFERENT ANSWER FROM A SURVIVING
ONE.** Deleting the DELIVERED spelling from the batch cannot be killed by any
value: it is a strict PREFIX of the staged spelling and no scanning rule is
end-anchored - the only anchored expressions in `tools/precommit_gate.py` are
the save-file NAME parsers - so appending can create a match and never destroy
one. Weakening the claim to "the staged name is graded" would be the wrong
repair, because the delivered name is the one that persists in the inbox and the
record. The property is measured structurally instead, with a RECORDING SPY over
the gate asserting both spellings reach it.

**THIRTEEN MUTANTS PLANTED AGAINST THE REPAIRED TREE, THIRTEEN DEAD**, file
restored byte-identical each time. Suite: 44 passed.

**F4 NOW HAS A SHARPER FORM.** The commit-phase `.tmp` litter is not only a
byte-identical delivery the record says never happened - the adversary used it
to make an UNGRADED FILENAME durable in a sibling's tree. Grading the staged
name closes the S2 half; the litter itself is still F4's.
