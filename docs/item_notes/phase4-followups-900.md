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

## CS-906

### FILED 2026-09-05 (session 61) by the merger, AFTER an adjudicator GRANTED the frozen-file change

**THE GRANT IS RECORDED IN `docs/LEDGER.md` AND NO EDIT HAS BEEN MADE UNDER IT.** Read that
entry FIRST - it carries all thirteen conditions and they are the acceptance. CLAUDE.md
section 6 requires the grant to land before the edit, and this item is what the grant
closes against. A grant records permission; it is not a work record.

**WHY IT WAS ASKED FOR.** The hook runs the whole suite serially. Nine measurements in an
earlier session put that at 742s to 865s, and on 2026-09-05 the same suite reached only 22
per cent in 13 minutes because an unrelated project held the machine at 99 per cent CPU,
projecting to about an hour. That makes tier 0 the bottleneck on landing anything.

**THE BENEFIT IS SMALLER THAN THE FRAMING SUGGESTS, AND THE RANGE IS ON THE RECORD.** Six
samples of the pytest step on a 2-vCPU runner over one byte-identical tree: serial 541.68s
and 590.82s; `-n auto` 424.18s, 475.98s, 483.14s and 470.67s. Mean to mean, 1.222x. The
pessimistic pair is 1.121x and the flattering pair is 1.393x. **Do not quote the flattering
one.** Coverage is unaffected: every one of those runs reported 4784 passed, 117 skipped.

**THE TWO CONDITIONS THAT GATE EVERYTHING ELSE.** Condition TEN requires a LOCAL measurement
at this machine's worker count before the flag ships - the evidence above is a 2-vCPU runner
and this machine reports 16 logical processors, and several of the most expensive tests spawn
NESTED pytest runs, so 16 outer workers each spawning more is unmeasured and may be net
negative. Condition SEVEN requires the CS-448 rootdir mechanism to be neutralised in `tests/`
first. **NEITHER CAN BE HONESTLY MET ON A CONTENDED MACHINE**, which is why this was filed
rather than built on the day the grant was issued.

**THE MECHANISM IS LIVE HERE EVEN THOUGH IT DOES NOT FIRE.** The temp root held 31688
top-level entries when this was filed. It does not fire because the checkout is not under
that root - a property of the PATH, not of the code. The session scratchpad IS under it, so
a clone made there re-arms it immediately.

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

## CS-918

**Filed 2026-09-06 by the merger, on the commit that landed the lane.** The machinery is
merged and graded; what is unproven is that it RUNS. Read `docs/LEDGER.md`'s CS-918 entry
before starting - it says in its own words that it does not close this item, and it lists
precisely what was and was not verified.

### THE ONE THING THIS ITEM OWES

One real cycle, end to end, with the row read back. Not a smoke test of the parts.

```
python ops/loop/queue_loop.py --once --local-suite --no-ci-gate --repo-root <the tree that carries ops/>
```

`--repo-root` is not optional until this lane's own code is on `main`. The launcher reads
the worker's prompt from `lane_launcher.REPO_ROOT`, which is the MAIN checkout by design -
so before the merge that checkout does not carry `tools/headless-queue.md` at all, and the
cycle records `launch_failed` for a reason that has nothing to do with the lane. That was
found by dry-running the wiring, not by guessing; `command_path("queue")` refuses against
the main tree today and resolves against a branch worktree.

### WHAT COUNTS AS PROOF, AND WHAT DOES NOT

**PROOF:** the JSONL row at `ops/loop/reports/queue_loop.jsonl` carries `outcome`,
`duration_s`, a `pid` that was real, and a `suite` block whose `summary` is a verbatim
pytest line and whose `exit_code` is an integer - quoted into the closing ledger entry. Plus
the worker's own log under `ops/loop/reports/`, which is what proves a process actually did
something rather than exiting instantly.

**NOT PROOF:** an `outcome` of `completed` on its own. A worker that starts and exits in two
seconds having done nothing produces exactly that word. The log and the duration are what
separate the two, which is the whole DETACHED_PROCESS lesson one level down - a real pid, a
zero exit, and no work done.

**ALSO NOT PROOF:** a green local suite whose `cwd` was the driver's own tree. The verdict
must name the LANE WORKTREE. The worker commits there and the driver's checkout has not
pulled, so a suite run in the wrong tree grades a commit nobody made and is indistinguishable
from a real green in the row. There is an arm for this
(`test_the_local_suite_grades_the_lane_worktree_and_not_the_drivers_own_tree`), but confirm
it on the real row too - the arm grades an argument, the row records a fact.

### THE CI HALF IS DELIBERATELY OFF IN THAT COMMAND, AND WHY

`--no-ci-gate` keeps a proving run from dispatching a real tier2 (four job types, both
platforms, metered minutes on a private repo). The CI path was instead exercised READ-ONLY
against real completed runs of both tiers: tier1 graded `success` on its two jobs, tier2 on
all six required matrix legs with the advisory audit excluded, and a planted red leg came
back `failure` naming `full suite (windows-latest)`. That is evidence the grader reads real
payloads correctly. **It is NOT evidence that the driver waited out a live run**, and those
are different claims. Whoever closes this item should say which one they are making.

### THE CHECKS NO MACHINE PERFORMS

`docs/OPERATIONS.md` section 10.7 lists four. The one most likely to be skipped is the
third: while a cycle is running, read the lock and confirm its `pid` is the powershell
WRAPPER's rather than the driver's. If the re-point silently failed, the lane reads RUNNING
forever after the worker dies, and every arm in the suite still passes - because they grade
`repoint_lane_pid` against an injected token, not against a live spawn.

### DO NOT FIRE THE LOOP UNATTENDED TO CLOSE THIS

One cycle closes it. A night is a separate operator decision and is not this item's
acceptance.
