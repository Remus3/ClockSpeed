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

## CS-928

### FILED 2026-09-07 (session 70), from a read-only probe that was sent to check a DIFFERENT claim

The probe was dispatched to establish whether build cost data exists at all
(CS-930). It came back having refuted that premise AND having found this, which
is a separate defect in a separate file.

`docs/ARCHITECTURE.md` reproduces `BOOTSTRAP.md` section 4 pillar 1 almost verbatim -
"every intermediate, exact building counts, exact clock speeds, byproduct
handling, raw input totals, total power draw, and total build cost" - and then
then appends:

    Implemented by: solve/exact.py, solve/ratio.py, solve/power.py, over
    data/registry.py

### WHY THE `Implemented by` LINE IS WHAT MAKES IT A DEFECT

`BOOTSTRAP.md` is the specification and is ALLOWED to describe an intended
build. It says so about itself. Copying a spec sentence into a file that then
attributes it to named shipped modules converts a statement of intent into a
false claim about shipped code, and nothing warns you.

That is precisely the mechanism recorded at the CS-922 entry in `docs/LEDGER.md` after seven
`README.md` claims were refuted in session 69. The README was repaired. **This
file was not, and it is the file that OWNS the module map**, so it is the more
authoritative of the two.

Measured against the cited modules: `ProductionPlan` (`clockspeed/solve/ratio.py::ProductionPlan`)
carries six fields - `steps`, `targets`, `raw_inputs`, `byproducts`, `excluded`,
`byproduct_policy`. No clock speed, no power total, no build cost. `PlanStep`
carries `recipe_key` and `machines`.

### THE FENCE

Do not repair this by deleting the `Implemented by` line and keeping the prose.
The prose is the claim; the attribution only dates it. Either the capability is
present in the named module or the sentence goes.

## CS-929

### FILED 2026-09-07 (session 70) by the CS-927 builder, which correctly refused to sweep it

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

## CS-930

### FILED 2026-09-07 (session 70). THE PREMISE THAT SENT THE PROBE WAS REFUTED, AND SO WAS THE LEDGER

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

## CS-931

### FILED 2026-09-07 (session 70), while answering a sibling project's question about watchers

`CLAUDE.md` section 2.2's tooling map row reads:

    tools/facts_probe.py | `SessionStart` live-state injection

**MEASURED: `.claude/settings.json` declares exactly two hook events,
`PreToolUse` and `PostToolUse`.** There is no `SessionStart` entry. The
user-level settings file does declare `SessionStart`, but it runs no Python
script at all, so `facts_probe.py` is not wired to it there either.

What actually invokes the tool: `.claude/commands/drift-guard.md`,
`.claude/commands/sync-docs.md` and `.claude/agents/doc-sync.md`, all by hand.

### WHY THIS IS WORSE THAN AN ORDINARY STALE LINE

`CLAUDE.md` is auto-loaded every turn, so this sentence is read into context at
the start of every session in this repository and is believed by default. It
describes a protection that does not exist - the exact shape CONVENTIONS.md
section 16 item 4 warns about, where presence is inferred from a claim rather
than measured.

It also has a live cost: a session that believes live state is injected
automatically has no reason to run the probe, so the state is never gathered.

### THE FENCE

Do NOT close this by wiring a `SessionStart` hook. `.claude/settings.json` is a
FROZEN FILE under CLAUDE.md section 6 and that route needs an adjudicator grant
recorded before the edit. The cheap and correct close is to make the claim true
by correcting it. Wiring the hook is CS-932's problem, not this one's.

## CS-932

### FILED 2026-09-07 (session 70), from a cross-project exchange in `moon_sync_inbox/`

A sibling project asked how Clockspeed's inbox watcher is invoked. The honest
answer is that there is none: no scheduled task, no file-system watch, no poll
loop. `schtasks /query` matched nothing. Notes are read only because the
operator's continuation prompt tells the session to read them.

**MEASURED LATENCY: about seven hours for one note this session**, and unbounded
in the general case, because nothing bounds it.

### THE DESIGN TWO SIBLINGS HAVE ALREADY CONVERGED ON

Surface unread notes at session start. It costs one directory listing, cannot
flash a console, and survives a `/clear` by construction because a `/clear` IS a
session start.

**TRACK SEEN FILENAMES AS A SET, NEVER AN MTIME WATERMARK.** A watermark
advances on write, so it can move past a note nobody read. Both siblings dropped
the watermark for that reason before building theirs; inheriting the conclusion
without the reason is how it comes back.

### THE FROZEN-FILE ROUTE IS THE REAL COST, AND IT IS NOT FIFTEEN MINUTES

The sibling's estimate assumed a `SessionStart` hook already exists here. It
does not - see CS-931. Wiring one means editing `.claude/settings.json`, which
is FROZEN under CLAUDE.md section 6: the proposal routes through an adjudicator
that did not produce it, and the grant is recorded in `docs/LEDGER.md` BEFORE
the edit is made.

`moon_sync_inbox/` is gitignored, so the seen-set must live somewhere untracked
too, and must not put a filename carrying a project code into a tracked file.
