# Wakeup notes

**Section status: LIVE.** A dated heading in this file records provenance - when the
text was filed, moved or measured - and never that the section itself is historical.

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

## Session 66 - 2026-09-06 - CS-918 CLOSED: a headless queue lane, ported with the driver owning every wait; one real cycle ran and caught three defects of its own author

- **Shipped:** **CS-918 CLOSED.** Four commits, `e0523d8..09aa678`. A one-row-per-worker
  headless lane - lock, launcher, runner, driver, worker prompt - plus
  `tools/dashboard_probe.py`, which turns "does the dashboard run" from a judgment call
  relitigated three times into a script with nine exit codes. Detail in `docs/LEDGER.md`.
- **In flight:** NOTHING half-written in the tree - it is clean and every commit is made.
  Two things are outstanding and neither is code: the branch was NOT PUSHED at the time of
  writing (see Failed paths), and `C:\cs-worktrees\cs-lane-queue` holds TEN UNCOMMITTED
  FILES from the proving cycle's worker, left deliberately rather than reverted - they are
  someone else's abandoned row, not this session's work.
- **Decisions:** ADR 0017 - the lane FORKS the cross-repo loop modules rather than joining
  their byte-identical pin. Joining the pin means joining the PROTOCOL: the shared governor
  rations concurrent workers between three repositories through one token bucket, so a
  fourth participant consumes their slots by editing a file in a fourth tree. The ADR now
  also records the PRICE of that refusal, measured the same day.
- **Surprises:**
  - **The worker bailed on its own wait, first time out.** Its last words were "The whole
    suite is running now. I will not touch the tree until it returns", then
    `lane exit code=0`. That is the ported repo's measured failure reproduced at the first
    opportunity, and it is the entire argument for the driver owning the wait.
  - **`-m "not slow"` deselects 12 tests of 5708.** It is not a fast subset. There is no
    cheap whole-tree lever here; scoping to the touched module is the only real one. This
    corroborates CS-906 and CS-907 rather than adding to them.
  - **The lane lock was never released,** because `lanes.py` was reachable under two module
    names. `lane_launcher`'s own docstring predicts that exact failure - it happened anyway
    because the launcher and its TEST agreed with each other while nothing asked the driver.
  - **Three concurrent projects' pytest runs exhausted the box.** One suite truncated at 78
    per cent with no summary line and `grep -c FAILED` returning 0; another died
    `INTERNALERROR> MemoryError` reporting "3402 passed, 1 error" while 2163 tests never
    ran. Saved to the harness memory store, not to a repo doc.
- **Failed paths:**
  - **The push is BLOCKED and nothing reached the remote.** `.githooks/pre-push` ran its
    whole-suite gate and pytest died - `Windows fatal exception: stack overflow`, reported
    as exit 127 - under four other projects' concurrent suites. It is ENVIRONMENTAL: the
    same tree ran green standalone thirty minutes earlier (`5704 passed, 4 skipped`, exit
    0, and 5704+4 matching the expected collection of 5708 exactly). **Do not reach for
    `--no-verify`** - it is forbidden here and the hook is frozen. Retry when the box is
    quiet.
  - Two suite runs were graded and discarded rather than believed, which is the grader
    working. Do not treat either number as a result.
- **Next action:** push `claude/jovial-franklin-2270d7` when the box is quiet, then read
  CS-919 before running the lane for anything.

---

## Session 65 - 2026-09-06 - CS-906 CLOSED: the pre-push suite runs distributed, 2.39x off every push; the CS-896 closure was REFUTED 3/3 and its mechanism fell to one line

**THE SECOND HALF OF THIS SESSION IS BELOW THE CS-896 MATERIAL.** The entry was written mid-session and then the session kept going. Read both halves.

### CS-906 CLOSED - the pre-push hook, all thirteen grant conditions met

**765s serial becomes 320s distributed - 2.39x, about 445 seconds off every push**, measured on REAL pushes rather than standalone runs. `.githooks/pre-push` now decides serial or parallel ONCE from an importability probe using `cs_python` (not `python` - different interpreters whenever CLOCKSPEED_PYTHON is set), never re-runs the suite, and degrades loudly when xdist is missing.

**THE ARMS CAUGHT A DEFECT THAT WOULD HAVE REDDENED EVERY PUSH.** The first edit passed with its module run alone and failed three-of-three under an outer `-n auto` - and the hook now runs the whole suite distributed, so that suite CONTAINS the arms grading the hook. **`PYTEST_XDIST_WORKER` IS INHERITED**: under a distributed outer run the process driving the push is itself a worker, the variable rides the whole chain into the nested pytest, and that run's CONTROLLER files itself as a worker. The signature is `ran=False` beside a NON-ZERO worker count. Fixed by asking `config.workerinput`, which cannot arrive from a parent.

**TWO FIGURES I PUBLISHED WERE WRONG AND ARE CORRECTED IN THE LEDGER.** 3.2x was an unpaired comparison across a contended box - the third instrument error of this kind on this item. And `-n auto` resolves to EIGHT workers, not sixteen: xdist counts PHYSICAL cores.

**`--dist loadfile` ADOPTED** in the hook and both CI shards, on a PAIRED reading - default 308s against loadfile 253s. Riot Commander measured it superlinear on their far larger suite. **It does NOT show on a real push** and the hook's comment says so.

### THE DASHBOARD IS LIVE AND CORRECT

The running instance was a child of the Electron companion, started the previous day, and predated CS-912 - so `/api/registry` 404'd. Restarted from the desktop shortcut; it now answers 200 with 750 items, 872 recipes, 68 buildings. Five of ten routes are live; the other five return an honest 501 naming CS-500.

### SESSION 66's WORK IS MERGED INTO MAIN

CS-918's five commits never reached the remote - its push died on a contended box - and its worktree was then closed. The branch survived, so it is merged here. ONE conflict, `docs/LEDGER.md`, resolved by keeping BOTH sides newest-first on commit time. Nothing dropped.

### THE CS-500 TRACE ENGINE IS SPECCED AND NOT BUILT

A planner produced the spec and a seven-slice decomposition. **It found that creating the advisor's trace module - the one the architecture map already names, which does not exist yet - turns `tests/test_docs_citations.py` RED** - three pins resolve differently once that path becomes tracked - so the citation-pin repair must land in the SAME commit as the module. No code was written. The worktree was removed externally and held zero commits.

### THE ORIGINAL CS-896 MATERIAL FOLLOWS

- **Shipped:** nothing CLOSED, and that is the correct outcome. Four commits,
  `58a30f1..7295efc`, all pushed, CI green. Detail in `docs/LEDGER.md`, not here.
- **In flight:** CS-896 stays OPEN, blocked on CS-917 - by an OPERATOR RULING, not by
  an unfinished thought. The ROADMAP relocate pass is still owed.
- **Decisions:** no ADR. TWO OPERATOR RULINGS, both recorded in `docs/LEDGER.md` and
  both confirming the tree rather than changing it - see below. Do not re-open either.
- **Surprises:** the four routes below, all measured against a tree every gate was green
  over.
- **Failed paths:** closing CS-896 by transferring its residual to CS-917. REFUTED, and
  the reasoning is in the ledger so it is not retried.
- **Next action:** NOTHING IS PENDING FROM THIS SESSION. Pick the top open item. The two
  strongest candidates are CS-917 (which CS-896 is now formally blocked on) and the
  ROADMAP relocate pass, which is three sessions owed.

**CI RUN 34038527058 ON `58a30f1` WAS GREEN** - that was the previous session's open
question and it is answered. Five consecutive green sharded runs. The fifth reading:
fast 353 job-seconds, save 247; the lane's own lines read 346 and 240 within budget.

**AND THE LANE WENT GREEN TWICE MORE ON THIS SESSION'S OWN COMMITS.** Reading six on
`77a88d1` (fast 360, the worst yet by one second) is filed in the CS-896 leaf; reading
seven on `4033b0e` came in at fast 353, save 222 - a new save-shard MINIMUM. **The
repaired report step and the parser-backed guard have now run on the runner three times
and changed no verdict**, which is what a repair to a reporting mechanism should look
like. Fast series: 323, 359, 358, 260, 353, 360, 353. Save series: 225, 237, 242, 227,
247, 246, 222.

**THE CLOSURE WAS PROPOSED, FROZEN AT `58a30f1`, AND REFUTED BY THREE ADVERSARIES on
distinct lenses - measurement integrity, scope laundering, guard defeat.** Every
load-bearing citation was then verified by the merger against `git show 58a30f1:` rather
than the working tree, **because one adversary was mutating that tree while the other two
read it.** That was an orchestration error on the merger's part; the md5 of the workflow
was recorded BEFORE dispatch and matched afterwards, so the readings stood. **Do not
dispatch a mutating adversary alongside readers of the same file again.**

**THE MECHANISM CS-896 BUILT WAS DEFEATABLE IN ONE LINE, FOUR WAYS.** Each left guard (k)
printing PASS, its own detail asserting the levels were "pinned two-way", and the budget
module green:

1. a job-level or step-level `env:` block restating either level - the guard anchored at
   line start, so a FLOW mapping never begins one and was invisible while PyYAML resolved
   it. The BLOCK spelling WAS caught. **The third regex-versus-parser hole in this guard
   in three sessions.**
2. `continue-on-error` on a job or step, discarding the ceiling's exit. **Governed by
   nothing** - the key appeared nowhere under `tests/` or `tools/`.
3. a second key written into `$GITHUB_ENV` from the start step.
4. the report step reading a level it cannot parse - all three refusals guarded the start
   marker and neither level had one, so a run far past every level printed the healthiest
   verdict it has and exited 0.

**ALL FOUR REPAIRED, NINE MUTATIONS THAT WERE GREEN NOW REDDEN** - five against the guard
record, four against the arms. Module 122 -> 141 passed. Both shards green locally: fast
3949 passed, save 1413 passed.

**ONE OF MY OWN ARMS SCORED ITS OWN MUTATION GREEN.** The first `$GITHUB_ENV` arm matched
greedily; a plain YAML scalar FOLDS a continuation line into the same string, so the
greedy run reached past the smuggled write to the last marker and captured one key where
there were two. **It reported the property held with the mutation in the tree.** Only the
mutation proof caught it. An arm that passes on a clean tree has proved nothing until its
mutation is shown to red it.

**GUARD (k) ALSO CAUGHT ME**, correctly: the first draft of these arms quoted the override
in its docstrings, making the test module a second owner of the numbers. Plants are now
ASSEMBLED at call time, the convention `restatement()` already documents.

**THE BROADER SUITE CAUGHT A THIRD THING THE TARGETED RUN DID NOT** -
`tests/test_exception_rendering.py` found my new guard code rendering a caught exception
OBJECT into a message, which is non-negotiable 12. Repaired with `_exc_text`. **Run the
shard, not just the module.**

**A CLAIM I MADE AND RETRACTED.** I proposed the runner swing is SHARD-SPECIFIC (save
shard 16s step spread against the fast shard's 94 over the same five runs). An adversary
refuted it and I verified: the shards are INDEPENDENT DRAWS, so under a pool with a fast
class appearing once in five fast-shard draws, the save shard missing it in five has
probability 0.8^5, about one in three. An identical pool reproduces the contrast exactly.

**THE DISPOSITION OF CS-896 TURNS ON ONE OBSERVATION.** Drop the single low fast reading
and that shard's spread falls from 94s to 34s, and the shipped band is then WIDER than the
noise - the condition PASSES. Keep it and it FAILS. `n=5` cannot say which, which is
exactly why another reading is the wrong instrument.

**THE FEASIBILITY ARITHMETIC, NEW AND RECORDED IN THE CS-896 LEAF.** With `M` the worst
reading and `N` the spread: no false warn needs `B >= M`, a warn before a red needs
`C - B >= N`, a red rather than a cancel needs `C + N <= cutoff`. So `B <= cutoff - 2N`,
the feasible budget window is `[M, cutoff - 2N]`, EMPTY once `N > (cutoff - M) / 2`. The
window is currently non-empty and the SHIPPED budget sits outside it. **THE LEVELS WERE
NOT TOUCHED and must not be re-derived at this sample size** - three previous
re-derivations were each falsified by their own next reading. A distribution-free 95/95
bound needs `n >= 59`.

**TWO OPERATOR RULINGS, BOTH GIVEN THIS SESSION AND RECORDED IN `docs/LEDGER.md`.**
Neither changed a file - both confirm the tree. **1. CS-917's tightened acceptance
STANDS. 2. CS-896 STAYS OPEN, blocked on CS-917**, with closing it as an honest partial
and lowering the budget into the window both DECLINED. Do not re-open either.

The questions as they were put:
1. **CS-917's acceptance was TIGHTENED** to require the band not be narrower than the
   noise figure it is derived from. Two adversaries found it could otherwise close with
   the condition silently dropped. It is a tightening, not a narrowing, but moving an
   acceptance clause is not an agent's call - review it.
2. **Whether CS-896 closes as an HONEST PARTIAL.** Precedent is in `docs/LEDGER.md` under
   CS-421 and CS-882, both operator rulings. No adjudicator can grant it and none was
   asked.

**NAMED AND NOT CLOSED.** ROADMAP.md is at 70987 bytes against a 61440 budget (115 per
cent) and this session added two bytes to it. THE RELOCATE PASS IS STILL OWED, three
sessions running. RELOCATE, NEVER DELETE.

**THE ECC FOLLOW-UPS ARE STILL UNFILED, and one count in the handoff was already stale:**
the GitHub Actions carry **13** mutable `uses:` tags, not 11 - the shard split added two.
A restated count drifted inside one session, which is the doc rule demonstrating itself.

---

## Session 64 - 2026-09-06 - CI was red for TWO reasons and the handoff named one; tier 1 now runs in two shards; FOUR adversarial passes all returned REFUTED and CS-896 is STILL NOT CLOSED

**ZERO ITEMS CLOSED.** CS-910, CS-900 and CS-896 all took substantive repairs and all three
stay open. Seven commits, `8729191..b9ca505`, all pushed, CI green.

**THE HANDOFF WAS WRONG ON ITS TOP ITEM.** It said tier 1 was red on the duration ceiling
alone with every test passing. Both red runs read `1 failed, 5213 passed, 119 skipped`. The
lane was red for TWO reasons and only one had been read.

**CS-910 - a Windows-only arm ran on Linux.**
`tests/test_make_cert.py::test_a_planted_openssl_in_the_working_directory_is_never_run`
grades the implicit current-directory executable search. Two of the three CS-910 runtime
arms carry a platform skip; the third carried a LIVENESS GATE written
`os.name != 'nt' or NeedCurrentDirectoryForExePath(...)`, which SHORT-CIRCUITS TRUE on
POSIX - so it reported the mechanism live where it does not exist. Fixed with the skip its
siblings had, plus a structural guard that reads every test function's UNPARSED BODY for the
two spellings, because the offending arm named the module only inside a probe STRING.

**WHY IT ESCAPED, AND THE FIRST FILED CAUSE WAS WRONG.** Not `cancel-in-progress`. **GitHub
Actions creates one run per PUSH event, against the TIP commit.** Twelve commits went up in
one push; the commit that introduced the test was never eligible for a run. The development
machine is Windows, where the arm passes, so tier 0 could not see it either.

**CS-900 - the liveness sweep re-parsed 8.4 MB of source 3457 times.** `module_function` took
a module's SOURCE and called `ast.parse` on it for every question. **89.93s before, 0.89s
after**; twelve sibling helpers in the same module had the identical shape and now share one
cache. `tests/test_liveness.py` went from roughly 146s to 41.19s.

**TIER 1 NOW RUNS IN TWO SHARDS, and that was an operator decision.** Run 34013336391 was
CANCELLED at 611s at 99 per cent of the suite with NOTHING FAILING. The cutoff is policy and
was not raised, so the work was given a second runner rather than trimmed: `fast` runs
`tests --ignore=tests/save`, `save` runs `tests/save`. **Coverage is unchanged BY
CONSTRUCTION** - verified two ways, a node-id partition (3245 + 1413 = 4658, empty
intersection) and identical skip sets (49 sites, 120 skips) before and after.

**FOUR ADVERSARIAL PASSES, ALL FOUR REFUTED, each against a frozen SHA it had not written.**
Every one found a defect that every gate, guard and arm in the tree was green over:

1. The budget's derivation was falsified BY THE SPLIT ITSELF - 540 was "21 above the worst
   observed job" and the split left it 221 above, so **CS-896's fix had disabled CS-896's
   own alarm**.
2. **The partition guard read ONE SIDE.** Adding one ignore and one marker expression to the
   save shard dropped **244 of its 1413 tests** with everything green.
3. **A trailing YAML comment defeated the cutoff guard.** `  third:  # a scratch job` was
   invisible to a regex anchored at `:$` while PyYAML resolved three jobs - that job would
   have run under GitHub's 360-minute default.
4. The warning margin was overstated 2.5x, and a ledger entry cited evidence THIS SESSION'S
   OWN COMMIT had deleted.

**AND A FIFTH FINDING CAME FROM THE DATA.** Reading four of the fast shard arrived at **260
job-seconds** against 323, 359 and 358 - on a **byte-identical population** (`3911 passed, 23
skipped` in both runs), an **88-second swing on identical work**. That widened the sample sd
from 20.5 to 46.5 and pushed the 95/95 tolerance bound to **564s, above the 480 ceiling**.
**The fourth reading did not discharge the sample objection - it failed it.**

**SO CS-896 IS NOT CLOSED, and the reason is specific.** The ROADMAP acceptance clause is met
four times over. What is NOT met is the CS-896 leaf's added condition that growth be visible
before it is fatal, because every warn band this session derived was narrower than the noise
its own next reading revealed: 21s, then 36s, now at least 88s.

**LEVELS SHIPPED AT 420 / 480 AND ARE NOT THE COMPLAINT.** All four readings sit inside them;
the worst fast reading is 359 and the worst save reading 237. A fifth re-derivation on n=4
would repeat the mistake the last three made.

**CS-917 FILED** - the growth SLOPE (3.51s per commit) is owned by no item, verified at three
SHAs.

**THE ECC TRIAGE: TAKE NOTHING.** `https://github.com/affaan-m/ECC`, MIT, verified 250044
stars. The licence gate CLEARS, so the refusal is on quality: our character-set gate bans
every byte above 0x7E while ECC's allowlists (c), (R), (TM) and does not ban an em-dash;
our PII layer resolves account ids and world tokens at runtime against its two regexes.
**ECC fails our non-negotiable 4 itself**, and its installer writes `~/.claude/` by default -
running it would modify our FROZEN `.claude/settings.json` with no grant. IDEAS-ONLY.

---
