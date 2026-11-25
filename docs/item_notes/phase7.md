# Clockspeed - live per-item detail, phase 7 - public flip gate

**Section status: LIVE.** A dated heading in this file records provenance - when the
text was filed, moved or measured - and never that the section itself is historical.

**This is a leaf of `docs/item_notes.md`**, which owns the index and the rules this
file obeys. Read the index for the leaf membership rule routing every OPEN item, the verbatim
rule, and what this family never contains. Do not restate any of it here.

**What lands in THIS leaf.** Every OPEN item ROADMAP.md files under its `Phase 7` heading.

**Bodies are relocated VERBATIM.** Every section below arrived from
`docs/item_notes.md` unedited when that file was split on 2026-08-25, and arrived
there from `ROADMAP.md` and `docs/history_notes.md` before that. A body therefore
still reads as it did when it was written, including the parts a later session
measured false and corrected in place rather than rewriting.

**When an item CLOSES its section moves to `docs/history_notes.md`**, not to another
leaf. That move is what keeps this file live.

---

## CS-815

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: filed 2026-08-22 (session 32); FROZEN FILE, needs its own grant. Detail in this file under **CS-815 - detail**; read it before taking this item.

### detail - relocated from `docs/history_notes.md` 2026-08-23

Filed 2026-08-22 (session 32); the item stays OPEN in `ROADMAP.md`.

Filed by the CS-703 adjudicator as the FOURTH site of that defect class, found by grepping for the
shape rather than by reasoning about it. `.claude/settings.json` names `pythonw tools/pretooluse_gate.py`
and `python tools/edit_lint_check.py` with NO resolution ladder and NO probe of any kind. By that
gate's own stated protocol - exit 2 denies and every other status is non-blocking - a missing or
substituted interpreter yields a non-2 status and the gate FAILS OPEN.

**IT IS MILDER THAN THE GIT HOOKS AND THAT IS RECORDED SO NOBODY RE-RATES IT UPWARDS.** CLAUDE.md
section 2.2 makes the Claude hooks a convenience layer and `.githooks` authoritative, so the tier-0
guarantee does not rest on this file. **IT IS ALSO NOT FIXABLE THE WAY CS-703 WAS,** because JSON
cannot express a probe: the fix has to live in the tools the JSON names, or in a wrapper.

`.claude/settings.json` is on the CLAUDE.md section 6 frozen list, so this needs its own operator
grant and its own adjudication. It was explicitly OUT of the CS-703 grant and is not claimed closed
by it.

### Acceptance

such a hook BLOCKS or is loudly reported, proven by pointing it at a program that ignores its arguments


### FILED 2026-09-25, landed with one check owed (session 115)

The wrapper and the two command values landed; see the CS-815 LANDED record in
`docs/LEDGER.md`. The ONLY remaining check: the operator confirms by eye that the
desktop app shows the `REFUSED (CS-815)` hook-error line for a failed probe. If it
does, CS-815 closes; if not, rebuild the report on the exit-0 JSON systemMessage route.

### Recorded 2026-10-23 by the session 151 adjudicator rulings

The "ONLY remaining check" above is superseded: `docs/LEDGER.md`, the 2026-10-23 CS-815 records, owns what remains, and its kit-hook half is gated as CS-G09 in `docs/GATED.md`.

## CS-1032

### Acceptance

one end-to-end control renders a known panel in a real browser and is compared against the stand-in's verdict for the same payload, with the comparison recorded whichever way it falls, and the stand-in's DIVERGENCES from the browser are enumerated rather than assumed empty

### Full headline

`tests/surface/panel_harness.py`'s DOM stand-in has no known-good browser control anywhere in the repo, and every panel verdict in the project rests on it: all 37 arms added for the optimize and power panels, plus every existing panel arm, run under `drive()` against a stand-in that nothing compares to a real browser, so "the page renders X" is a claim about the stand-in and not about the page - this project has already recorded that the dashboard's self-signed HTTPS defeats automation browsers and that browser-pane resize, focus and default key scrolling are silently faked, which is why the gap is unclosed rather than merely unnoticed

## CS-1194

### Acceptance

`tools/drift_guard.py` withholds, in the text report and the `--json` payload, any
rendered path with a component equal to a value this machine resolves locally as
the player's - the account directory name, the world name, the Windows account
name or the player display name - whatever its shape, and fails closed to the
withheld form when that value cannot be resolved; the values come from local
resolution, never a typed list in a tracked file. An arm plants a non-numeric
player-named directory holding no withheld-class file and asserts it is withheld,
and a control asserts a repository-chosen name still renders.

### Full headline

drift_guard prints a non-numeric player-named directory that holds no sensitive file

### FILED 2026-09-25, the ADR 0023 residual (session 113)

`docs/adr/0023-whether-a-filename-is-personal-data.md` rules this outside CS-1158: a
directory named for the player by a non-numeric name - a world name, a hex or GUID
account token - holding no withheld-class file is indistinguishable by shape from
any other directory, and renders. Rule 2's shape test catches only the digit-run
account id.

## CS-1196

### Acceptance

the history walk in `tests/test_provenance_manifest.py` (the CS-1176 arms) handles
a merge commit by a stated rule - first-parent, or an explicit rule for a row first
added on a side branch - and counts each first-add exactly once whichever way a slice
reaches `main`; an arm builds a real merge commit in `tmp_path`, with a side branch
adding a row, and asserts the walk counts the same first-adds as the equivalent
linear history.

### Full headline

the provenance manifest's history walk miscounts first-adds across a merge commit:
in the CS-1176 walk, a slice merged by `git merge` reads 14 first-adds where its
linear equivalent reads 13

### FILED 2026-09-25, found at the wave-3 close (session 113)

Found by the merger at the wave-3 close and reported with the counts above; the
filer did not re-measure them. Every slice this session reached `main` by
cherry-pick or fast-forward, so the walk has only ever graded linear history, and
no arm builds a merge commit.

### MEASURED 2026-10-02, the counts the filer never took (session 118)

This item blocked a push. Two slices were landed with `git merge --no-ff` rather than
by cherry-pick or fast-forward, and
`test_no_first_add_row_postdates_the_seed` went red on its ANTI-VACUITY equality, not on
a finding: `findings` was empty and `first_adds` was 441, while `versions` read 21 against
an independent count of 19.

THE COUNT RISES BY EXACTLY ONE PER MERGE COMMIT, measured at every commit of the session
with both counters re-implemented outside the module: 19 and 19 at the base and through
three linear commits, 20 against 19 from the first merge onward, 21 against 19 from the
second. The independent counter never moved.

THE MECHANISM IS TWO WALKS WITH DIFFERENT MERGE SEMANTICS, which is narrower than this
item's headline and is the part an arm has to pin. `_manifest_history` uses
`git log --full-history --parents`, and a path limit with `--parents` turns on parent
rewriting, which KEEPS a merge. `_independent_version_count` uses
`git rev-list --full-history` with no `--parents`, so there is no parent rewriting and a
merge TREESAME to a parent is OMITTED. A merge that does not itself modify the manifest is
therefore counted by one walk and not the other.

WHY THE 73 MERGES ALREADY IN THIS HISTORY DO NOT TRIP IT: they predate the manifest, so
their trees hold no copy of it, and the walk's own pruning step drops a node that has
neither rows nor a kept parent. The defect needs a merge whose tree HOLDS the manifest and
does not modify it - which is what landing a slice by merge produces, and what
cherry-pick and fast-forward never produce.

LANDED LINEAR INSTEAD, and the item stays open. The session's two merges were rebased away,
leaving seven commits whose combined tree is byte-identical to the merge-bearing one, and
the module then read 67 passed. That restores the practice the paragraph above records
rather than inventing a new one, and it fixes nothing: the next merge reproduces this.

## CS-1197

### Acceptance

the library sweep in `tests/save/test_trailing_run.py` (`_sweep_trailing_runs`) is
bounded by a stated rule - a sample, or a per-save cap - written in the module, and
its library arms finish under a stated seconds budget recorded beside that rule,
serially and under parallel workers, while still grading every save SHAPE the arms
name; an arm proves the bound holds as the library grows, and a control proves a
shape absent from the sample still reddens.

### Full headline

`tests/save/test_trailing_run.py` sweeps every real save, so its run time grows
with the save library: at the wave-3 close one test took 398s of a 400s per-test
cap, and it times out under parallel workers

### FILED 2026-09-25, found at the wave-3 close (session 113)

Found by the merger at the wave-3 close and reported with the timing above; the
filer did not re-measure it. The save library grows while the operator plays, so an
unbounded sweep drifts toward any per-test cap without a line of code changing.

## CS-1202

### Acceptance

it is MEASURED, in a live Claude Code session in this repository, whether the harness
sets `CLAUDE_FILE_PATHS` for the PostToolUse hook; if it does not, the hook command in
`.claude/settings.json` stops passing it (a frozen-file grant) and
`tools/edit_lint_check.py` reads the edited path from the stdin envelope alone, with an
arm proving an edited file with a violation is reported.

### Full headline

the PostToolUse lint hook's `--files "$CLAUDE_FILE_PATHS"` argument may always be empty
under the live harness

### FILED 2026-09-25, reported by the CS-815 shell adversary (session 115)

UNVERIFIED BY THE MERGER. The adversary read the harness binary and found no mention of
`CLAUDE_FILE_PATHS`, and counted 352 past PostToolUse hook errors in which
`edit_lint_check` reported `precommit_gate: BLOCKED`, mostly "could not read" the
file, cause not established. Predates CS-815 and is outside its grant.

## CS-1204

### Acceptance

`/api/health` answers without waiting on a save parse: its `world` field is derived
from what the world provider already holds or from a cheap presence check, never from
a fresh parse on the request path, so a cold first probe on a real world answers inside
the companion's `PROBE_TIMEOUT_MS`; an arm drives health with a world provider whose
load blocks and shows health still answering promptly.

### Full headline

`/api/health` still waits on a full save parse on a cold start

### FILED 2026-09-25, the CS-1203 closing adjudicator's residual (session 115)

After CS-1203 the first `world()` call on the pinned development world still takes about
2.58s, so the companion's first probe always aborts; the launch succeeds only because
the parse continues after the abort and the second probe finds it. Also recorded: the
import-time `ROUTES` table in `clockspeed/surface/api/routes.py` builds its own
`SaveWorldProvider`, which the launch path never serves.

## CS-1205

### Acceptance

the pre-push hook's pytest run is not reshaped by an inherited `PYTEST_ADDOPTS` (or the
hook refuses one it did not set), so an operator setting such as `-l` cannot make a
failing test render its locals through the hook; an arm plants `PYTEST_ADDOPTS=-l` and a
synthetic canary in a failing test's locals and shows no canary in the hook's output.
Needs its own frozen-file grant for `.githooks/pre-push`.

### Full headline

pre-push does not scrub `PYTEST_ADDOPTS`, so an operator `-l` renders test locals

### FILED 2026-09-25, the CS-814 repair adjudicator's ruling (session 115)

Found by the CS-814 vacuity adversary: the probe's pre-push sandbox stripped `PYTEST_*`,
so an inherited `PYTEST_ADDOPTS` was never exercised, and the hook does not scrub it.
Ruled a new item rather than CS-814 scope, because it is reachable only through the
operator's own environment and its fix edits the frozen pre-push file.

## CS-1206

### Acceptance

no module in the tests tree renders an environment value through a channel other than
an assert - a `print`, a `sys.stdout`/`sys.stderr` write, a logging call, captured
output echoed back, or a failure message built outside an assert - graded by a static
guard over the tests tree in the shape of the CS-1199 assert-rendering guard, with a
planted-mutant control per channel; the pre-push hook runs the whole tree, so its
output is a hook echo path under CLAUDE.md non-negotiable 13.

### Full headline

a test run by pre-push can print an environment value outside any assert

### FILED 2026-09-25, the CS-814 closing-bar adjudicator's ruling (session 115)

CS-814's static scope covers the programs the hooks run, but not the test modules
pre-push runs; the CS-1199 guard covers asserts only and the conftest redaction covers
known credential names only. Ruled a new item rather than CS-814 scope.

## CS-1207

### Acceptance

the READS rule in `tests/test_hook_env_echo.py` becomes an allowlist of the functions
permitted to touch the environment or OS-derived personal values, so an unlisted reader
is a finding: at least `os.path.expandvars`, `getpass`, `os.getlogin`, `Path.home` and
`expanduser`, `platform.node`, `socket.gethostname`, `tempfile.gettempdir` and
`os.environb`; keys passed to a reader across modules or through `map` or `partial` are
resolved; the command and dynamic rules catch PowerShell `Env:`, `node -e process.env`
and `capture_locals`; a driven arm reaches the short-name branch of
`precommit_gate.current_account_names`; the module docstring states what it grades.

### Full headline

the hook environment allowlist lists known readers, so an unlisted reader such as
`os.path.expandvars` escapes it

### FILED 2026-09-25, a condition of the CS-814 close (session 115)

The final CS-814 adversary rendered a synthetic personal marker through the real gate
with an `os.path.expandvars` skip message while every arm stayed green; no shipped hook
path uses any listed reader today, so CS-814 closed and this item carries the gap.


### MEASURED 2026-09-26, three adversary rounds against the landed inversion (session 116)

The inversion landed at `db87fff` and is NOT closed. Rounds one and two refuted it with
20 and 11 live escapes; both classes are closed and pinned by arms. Round three, at the
landed tree, rendered a synthetic marker live with no static finding through: attribute
walks inside `str.format` and `format_map` fields (`{0.__globals__[os].environ[K]}`);
`__import__` and `exec` bound to a name, stored in a container or passed to `map`;
`match` class patterns reading `__globals__` or a `home` attribute; `getattr` on
`pathlib.Path` with a literal `home`; reaching `os` through a scanned repository module
(`precommit_gate.os`); and `git difftool -x`, with `grep -O`, `rebase --exec`,
`clone -u` and `bisect run` passing statically. Probes and outputs sit in session 116's
scratchpad as `adv1207c_*`; the next builder re-derives them from this list.
DECLARED out of scope in the module docstring: `__file__` and `__spec__.origin`,
directory listings, `relpath` depth, `time.tzname`, `/proc` paths built at run time,
`git config user.email`, `git var`, personal `git log --format` fields, a python child
reading its program from stdin, `contextlib.chdir`, argparse `prog`, the gate's
`git(args)` pass-through, and `sys.argv`.

### MEASURED 2026-09-26, rounds four to sixteen on an unmerged branch (session 117)

Twelve repair rounds sit on branch `worktree-agent-ace624231ac7fd814` at its round-15 tip,
each recorded in that branch's copy of this section. Every adversary round refuted the
candidate with a new class; the saved probes of every earlier round stayed caught.
Round sixteen's open escape: pytest's config discovery reads a `pytest.ini` inside the `tests/` directory and a
root `.pytest.ini`, and neither is pinned or graded. The loop is HALTED, not closed: a
safety classifier stopped two adversary turns and the round-seventeen repair brief, and
the operator's ruling is owed on running round seventeen interactively, on declaring
pytest config discovery out of scope, and on landing the branch LANDED-NOT-CLOSED with
the module moved out of the guard shard.
## CS-1208

### Acceptance

a value-flow arm over every Python program the hooks run shows that no personal value a
program may read - including `CLOCKSPEED_ACCOUNT_DIR`, `CLOCKSPEED_WORLD_NAMES` and
`CLOCKSPEED_SAVE_ROOT` - reaches a print, log, report or exception sink, and that nothing
is echoed from inside a site the allowlist permits to read, with a planted-mutant
control per sink.

### Full headline

a personal value the hook allowlist lets a program read can still reach a print, log or
report

### FILED 2026-09-25, a condition of the CS-814 close (session 115)

The final CS-814 adversary printed allowlisted personal values and echoed from inside a
permitted site while every arm stayed green. The allowlist grades reads, never where a
read value goes.

## CS-1211

### Acceptance

`tests/test_hook_probe_bound.py::hangs`, the import-time precondition behind
`INSPECT_HANGS` and `NUL_STDIN_HANGS`, cannot read a slow-but-returning interpreter as
hung: under the load that reproduced CS-1201 (24 CPU spinners plus 32 process-spawning
threads) a POSIX box whose interpreter returns still skips the arms with their measured
reasons, shown red first on the current code with an injected slow-returning shim.

### Full headline

`tests/test_hook_probe_bound.py::hangs` reads a slow-but-returning interpreter as hung
under load, un-skipping an arm that then fails

### FILED 2026-09-26, the CS-1201 planner's residual C1 (session 116)

`hangs` waits `PRECONDITION_WAIT` (5s) and calls anything slower a hang. Not observed;
outside CS-1201's acceptance, filed as its spec directed rather than folded in.

## CS-1212

### Acceptance

the commit in `tests/test_hook_toolchain.py` that runs under `run_bounded` with
`harness_bound() + HARNESS_SLACK` no longer charges pre-hang start-up to that kill:
under the CS-1201 load it does not go red while green alone, using the CS-1201 call log
and hang-anchored window rather than a wider slack, shown red first with the 4s-per-call
shim.

### Full headline

`tests/test_hook_toolchain.py` kills its commit at a fixed bound plus slack that counts
pre-hang start-up under load, the CS-1201 defect one module over

### FILED 2026-09-26, the CS-1201 adversary's residual (session 116)

The CS-1201 adversary named the fixed kill in the module that imports
`tests/test_hook_probe_bound.py`; it was outside the item's write-list.

## CS-1213

### Acceptance

the save shard's named-first arm in `tests/test_tier1_budget.py` (the one asserting
`REBALANCED_FILE` is the save shard's FIRST target so loadfile starts it at once) grades
a claim that holds under the installed scheduler: either the save job carries
`--no-loadscope-reorder` as the hook job does since CS-1198, with the arm asserting both
the order and the flag, or the arm and its docstring are rewritten to state the measured
dispatch order; the save shard's next CI reading does not rise as a result.

### Full headline

the save shard's named-first arm in `tests/test_tier1_budget.py` asserts a dispatch order
that pytest-xdist 3.8 reorders away

### FILED 2026-09-26, the CS-1198 re-ruling's second finding (session 116)

pytest-xdist 3.8 sorts loadfile work by descending test count unless
`--no-loadscope-reorder` is given, so naming a file first no longer starts it first. S0
measured the same false claim at the hook shard's comment, repaired there by CS-1198.

## CS-1215

### Acceptance

no output of `tools/precommit_gate.py` - its `GitError` crash line, its handled INDEX
diagnostic reason, or any other rendering of a git child's stderr - carries a path
segment that locates a home directory or an account name, shown by arms that run the
gate by hand against a synthetic home path containing a space (git's dubious-ownership
refusal, a `GIT_DIR` naming a missing directory, a corrupt staged blob in a linked
worktree) and assert no marker fragment appears, each red first; the edit to the frozen
gate carries an adjudicator grant recorded in `docs/LEDGER.md` before it is made; the
`display_note` space-split (not reproduced end to end) is pinned by a direct-call arm.

### Full headline

the pre-commit gate run by hand echoes git's own stderr, home path included, through
its GitError crash line

### FILED 2026-09-26, the CS-1208 planner's lead H2, reproduced (session 116)

Reproduced with synthetic markers only, running `--staged` without `--verbose`: each of
the three triggers above rendered the marker. A real `git commit` failed before the hook
ran in the ownership and corrupt-blob cases, so the leak is reached when the gate is run
by hand or from another tool, not through the hook. Lead H1 (`display_note` splitting
on spaces under `--verbose`) reproduced only as a direct call.

## CS-1217

### Acceptance

a staged top-level `ruff.py` never runs when the pre-commit gate lints a staged unit:
with `ruff` absent from PATH the gate's `python -m ruff` fallback no longer starts in a
directory holding staged bytes, or runs with `-P` / `-I` (safe path) so the working
directory is not on `sys.path`, or refuses the fallback outright; an arm stages a
synthetic `ruff.py` that only writes a marker FILE into a temp directory, hides ruff
from PATH for the child alone, runs the gate under `--staged`, and asserts the marker
file is absent, red first; the edit to the frozen gate carries an adjudicator grant
recorded in `docs/LEDGER.md` before it is made.

### Full headline

with ruff off PATH the gate runs `python -m ruff` from the staging directory, so a
staged `ruff.py` runs in ruff's place

### FILED 2026-09-26, the CS-1207 round-7 builder's residual, reproduced (session 117)

`ruff_command()` falls back to `[sys.executable, "-m", "ruff"]`; `-m` puts the working
directory first on `sys.path`, and the ruff calls run with the staging temp directory
as `cwd`. A liveness adversary reproduced it end to end in a private tree: with ruff
hidden from PATH but importable, a staged synthetic `ruff.py` ran under `--staged` and
wrote its marker file. Declared as a residual in the CS-1207 scanner docstring.

## CS-1218

### Acceptance

the pre-commit gate never reports PASS for a staged Python unit whose lint did not run:
when ruff exits on a configuration it cannot load, or returns output the gate cannot
parse as its JSON report, the gate blocks with a finding that names the unit and says
lint did not run, shown by an arm that stages a synthetic unit under a temp repository
whose `pyproject.toml` carries an unloadable `[tool.ruff]` table and asserts a blocking
exit, red first; the edit to the frozen gate carries an adjudicator grant recorded in
`docs/LEDGER.md` before it is made.

### Full headline

a ruff config the gate cannot load makes the gate report PASS while lint did not run

### FILED 2026-09-27, a CS-1207 round-sixteen adversary side finding (session 117)

A private-tree commit whose `[tool.ruff]` table named an `extend` path ruff could not
resolve printed the gate's PASS line; the gate discards ruff's stderr, so the failure
was silent.

## CS-1231

### Acceptance

`ops/fleet_kit/` holds MAIN's current FLEET-KIT files byte-for-byte with a CLEARED
`THIRD_PARTY.md` row each, the gate dated before the lift; `CLAUDE.md` embeds the common
block between its markers and `fleet_headless.conformance(repo_root) == []` runs in the
suite; every headless spawn in this tree goes through the kit's `spawn`, or the reply to
MAIN names each path left out and why; MAIN's directives are still verified by
`tools/main_provenance.py`, the kit's `verify_main` being weaker than section 6.1.

### Full headline

adopt MAIN's FLEET-KIT (vendor the kit, embed the common block in CLAUDE.md, route
every headless spawn through it)

### FILED 2026-10-03, from MAIN's verified orders 0955, 1014 and 1016

Two slices are built and parked on their branches, unmerged: the vendoring with its guard
exemptions, and the condensed `CLAUDE.md` with the block embedded. Both HOLD at the
`THIRD_PARTY.md` section 14 gate: an adjudicator ruled the licence must be read before the
lift (an operator instruction moves the decision, not the gate), and MAIN's commit
holding the kit carries no LICENSE, NOTICE or manifest and no licence paragraph in its
README. The adjudicator's fallback is to hold and ask MAIN for a licence. The `/done`
command change the v2 order asked for is this tree's own text and landed separately.
Gaps reported to MAIN: `verify_main` hashes MAIN's working tree only; `claude_exe`
resolves through `shutil.which`; `check_url` admits any loopback port where CS-1225 pins
one.

### MEASURED 2026-10-03, v4 landed with slices A and B

MAIN shipped FLEET-KIT v4 under Apache-2.0 with a NOTICE naming the holder by role. The
section 14 gate ran and CLEARED before the lift (`docs/LEDGER.md` under CS-1231), and
slices A and B landed as one commit at v4. The condensation was dropped: an adversary
found it had moved binding rules into a non-binding history file, so `CLAUDE.md` keeps
its full text, adds a precedence paragraph, and gives each Settled entry a Reversed-by
clause that only the operator's own words satisfy. OPEN: slice C - route
`ops/loop/inbox_responder.py` and `ops/loop/run_lane.ps1` through the kit's `spawn`
with `floors_in_hooks=True`, then send MAIN the v4 ANSWER.

### Recorded 2026-10-08 by the session 129 /done

FLEET-KIT v9 landed under CS-1272. As read in session 129 it adds the xhigh and max efforts
but still carries no command-line entry and not the "Refused" task-name wording, so slice C's
second half - routing `ops/loop/run_lane.ps1` through the kit - still waits on a MAIN kit that
carries them. The inbox responder half already starts through the kit's spawn, as the
`CLAUDE.md` precedence clause (c) states.

### Recorded 2026-10-08 by the session 132 /done

FLEET-KIT v10 landed under CS-1282. It adds a `spawn` command line and the kit's
`REFUSED_TASK` wording, which the inbox responder now publishes on a refused start, so the
wording half of the wait is discharged. Slice C's second half - routing
`ops/loop/run_lane.ps1` through the kit - is still BLOCKED: the v10 `spawn` command line
passes no extra flag through, so the lane's permission flag cannot ride it. MAIN was asked,
in this tree's ONE ANSWER to MAIN 0839, for a kit v11 pass-through or a ruling to call
`launch()` or `spawn(extra=...)` from Python. Until one arrives the lane runner keeps
starting `claude` directly under precedence clause (c), and sets the SUBAGENT-FIRST hook
off for its worker. CS-1283 (ORDER item 5's `emit()` ruling) rides with this slice.

### Recorded 2026-10-08 by CS-1287

FLEET-KIT v11 (MAIN 2026-10-08 18:40 ORDER, ruling R2) landed under CS-1287 and UNHOLDS
slice C: the kit's `spawn` command line now passes ONE enumerated flag through,
`--permission-mode MODE` (MODE in `PERMISSION_MODES`). The target lane start line is
`python ops/fleet_kit/fleet_headless.py spawn ... --permission-mode bypassPermissions`, in
place of the direct start with `--dangerously-skip-permissions`. CS-1287 did NOT move
`ops/loop/run_lane.ps1`, by ruling: the kit's command line prints its own usage line, not
the CLI's `type: result` object that `ops/loop/queue_loop.py` parses, and its proxy and
budget checks collide with the lane's own loopback check and budget, so the move needs its
own slice. Precedence clause (c) of `CLAUDE.md` stands until that slice lands.

### Recorded 2026-10-17 by the session 145 /done

Slice C is PARKED by adjudication on its own branch, NOT on main (tip subject "CS-1231 - lane
runner starts its worker through the kit"; KEEP the branch and its agent worktree). Three distinct
adversaries REFUTED it: the kit's `--timeout` fires before the driver's own timer, so a timed-out
run records completed (HIGH); a kit budget refusal ends the night through launch_failed (MEDIUM);
and lower findings, listed in `docs/LEDGER.md`, the 2026-10-17 CS-1231 record. The kit-side
findings K1 to K5 went to MAIN in the session 145 REVIEW note. Carried locally, L1 to L6: plumb the
driver's timeout into the runner, or map the kit's exit 4 to timeout_killed; a budget refusal onto
the usage-limit wait path (after K5); the case-variant JSON keys PowerShell 5.1 reads; `CLAUDE.md`
wording that cites the landing commit, never a kit version; at landing, the merger rewrites this
section's lines that say slice C is open and clause (c) stands; the timeout test's docstring, which
overclaims. Slice C has since LANDED and `CLAUDE.md` precedence clause (c) is retired (the session
150 record below): `ops/loop/run_lane.ps1` starts its worker through the kit's `spawn`. CS-1283 no
longer rides with this slice: it closed in session 145
on its keep-own-sink ruling. Next action: unpark on a MAIN kit answering K1 and K5, or a ruling
that they are won't-fix; fix L1 to L6; land only after a distinct adversary reads NOT REFUTED on
the combined tip.

### Recorded 2026-10-17 from MAIN's verified 13:16 RULING, item 4

K1, K5 WON'T-FIX in the kit; slice C UNPARKS. L1: treat kit exit 4 or JSON error "timeout"
as timeout; pass `--timeout` above the driver's timer, or drop that timer. L2: a budget
refusal is exit 3, JSON code "budget-spent" - back off until `cap_frees_at` in
`inbox_status.json`. Next: fix L1 to L6, land on a distinct adversary's NOT REFUTED.
Reversed by a kit exit 0 or no error for a killed run, or a refusal not exit 3 budget-spent.

### Recorded 2026-10-21 by the session 150 landing merge, ruling L5

Slice C LANDED at eeec6967c2fdbc64aa19a51fe4ba6cdaf75f7419; clause (c) retired. L1 is met by a
recorded third option (driver kill as backstop), not MAIN's arms - `docs/LEDGER.md`, the CS-1231
L1 DEVIATION record; the orphan-pipe defect went to MAIN as a FIX.

### Recorded 2026-10-23 by the session 151 adjudicator ruling

The gate-before-lift clause reads NOT MET at the version 20 patch 1 lift: `docs/LEDGER.md`, the 2026-10-23 CS-1231 DECISION RECORD, owns what remains.

## CS-1291

### Acceptance

Each of MAIN 2246 section 2 items 1-3 and 5-10 is DONE or carries a recorded reason it is
not, in `docs/LEDGER.md`: (1) pre-push tiered by the pushed diff - a doc or hand-off-only
range runs gates only, a code range runs `-m "not slow"` plus the mapped modules, the pass
floor scales to the subset, the full suite stays with tier1 CI - landed on a section 6
adjudicator grant recorded in `docs/LEDGER.md` before the edit, because `.githooks/pre-push`
is frozen; (2) a preflight of about 10 s (provenance manifest, sphinx roles, mypy on
changed files, ruff) runs first in pre-push; (3) `--durations=25` locally, every test over
about 2 s and every subprocess hook test marked `slow`, `tests/test_tier1_budget.py` fails
on an unmarked slow test, its stale header numbers updated; (5) tier1.yml `paths-ignore`
for docs, markdown and the hand-off, one shared budget script in place of the five copies,
and tier2 skipped when HEAD equals the last green tier2 SHA; (6) inbox runs classify first
then sonnet/low, one fire per note per tick, a 0-second Stop writes failed; (7) the
0-ahead agent worktrees and the old slice worktree Recycle-Binned after a consumer check
and merged `worktree-agent-*` branches pruned; (8) verifiers read the frozen-SHA run's
junit and exit code rather than re-running the whole suite; (9) progress files get status
failed on agent exit and a schema check on write, done files older than 7 days archived;
(10) is CS-1284, discharged there.

### Filed 2026-10-09 from MAIN's 2026-10-08 22:46 ORDER, section 2

MAIN's read-only perf audit, ranked; the measured numbers are in the note and are not
restated here. Item 4 (no suite gate) is section 1's kit v13 work, CS-1290. Item 10 is
already open as CS-1284. The note says fix inline; each numbered part may land as its own
slice. The section 8 review driver (CS-1295) folds this list in as known findings.

### Recorded 2026-10-17 from MAIN's verified 13:16 RULING, item 3

Part (1) and DONE-SLOW (CS-1321) compose; DONE-SLOW governs where they touch: a /done runs
at most ONE gated whole suite, on the HEAD it pushes; pre-push runs no whole suite by
default; a doc-only ritual may run none. Grant timing after CS-700 S12a unchanged. Reversed
by TEST-TIER replacing the ritual suite, or /done median still over 65 min after 5 rituals.

## CS-1295

### Acceptance

Quoting the note: "plan file + a findings file covering every top-level folder, each
finding DONE / FILED (row id) / NOT-APPLICABLE, and a file count reviewed equal to the
count on disk." The driver is ONE headless run started through the kit spawn path only
(FLEET-COMMON 10; kind build, a non-empty note label) and writes the item-12 progress file
named repo-review.json, with a checklist. It plans first, then reviews
100 percent of the files on disk - tracked, untracked and ignored - over the topics MAIN
2246 section 8 lists, folding in sections 2, 3, 5 and 6 as known findings (CS-1291,
CS-1292, CS-1293). Fixes land in slices through the git lock and the suite gate; anything
irreversible or operator-gated is listed, not done. The run label and progress file name
go in this tree's next ANSWER to MAIN.

### Filed 2026-10-09 from MAIN's 2026-10-08 22:46 ORDER, section 8

Queued after section 1 (CS-1290) per the note's order of work. It needs a session that may
spawn headless runs: a sub-agent slice cannot start it, so the main session or the lane
queues it.

## CS-1304

### Acceptance

The forced run's exit 2 under load in the forced-red arms of
`tests/test_cs1172_branch_canaries.py` and `tests/test_cs1175_rule_narrowing.py` is traced
to its cause, read from the run's own `child_failure` report, and fixed there; both files
then run 30 consecutive times under `-n 2 --dist loadfile` with no forced or control child
exit 2. A child that dies of a Windows status past 255 (shown in hex) is a box-resource
death, recorded with its reading and not counted as this defect. No leaky control is
weakened, no budget is raised and no case is skipped.

### Filed 2026-10-09 by the CS-1301 merge

CS-1301's builder recorded in its second commit ("CS-1301 - the forced runs name their own
failure, statuses in hex") that its first 30x loop under `-n 2 --dist loadfile`, on a box at
its commit limit, read a control child exit 3221225773 (0xC000012D, the paging file too
small) and a forced run that "did not fail: exit 2". That forced-run message was still bare,
so its cause was not recorded; both forced-run code assertions now report through
`child_failure`, so the next reading names the child's error types and frames. CS-1301 traced
the leaky control's exit 2 to a cross-drive collection walk and cut it with `--confcutdir`;
the forced run's paths are in the repo, so that cut does not reach it, and whether it shares
the cause is unmeasured. An exit 2 there reddens any suite that runs the files, so it is
filed under the `CLAUDE.md` section 7 suite-red exception.

### Session 135 ruling, recorded 2026-10-10

Retry-once is DENIED as masking. The narrowed alternative A governs: `child_failure` names the
withheld exception type, the failure stays red, and the fix waits for a measured reading. The
item may wait past the CS-700 flip unless a deciding suite before CS-700 step a shows this
failure class - then it blocks the flip block. Decision, alternatives, the unmeasured planner
spec and the reversal: `docs/LEDGER.md`, the 2026-10-09 CS-1304 DECISION RECORD.

## CS-1318

### Acceptance

The cause of the hook-shard failure of the pre-commit case of
`tests/test_hook_probe_bound.py::test_a_background_child_holding_stdout_is_refused_and_reaped`
("the background process outlived the refusal - it was not reaped") is measured. Either the arm
reproduces, and the reaping defect is fixed with the arm red first; or repeated runs on the ubuntu
runner and on a loaded box show a load flake, and the arm's wait is made load-tolerant without
raising the hook probe bound. A rerun alone never turns the red green, and no case is skipped.

### Filed 2026-10-12 by the session 138 /done

tier1 38262274792 at c7fc806 - a commit touching only `CS-NEXT-SESSION.txt`, `WAKEUP_NOTES.md`,
`docs/LEDGER.md` and `docs/history_notes.md` - failed its hook shard, which runs on ubuntu-latest,
on that one arm: 1 failed, 686 passed, 10 skipped. The same shard passed at 0e82056, the parent,
and at 923e30f and 5b22e08. No record in the tree names this arm as flaky before, and the /done did
not rerun the job. CS-1211, the same module's `hangs` reading a slow interpreter as hung under load,
is FROZEN and is a sibling, not this arm.

### Filed 2026-10-12 by the session 139 merger

Live state: measured as a load flake in the arm's `reap` liveness check, not a reaping defect; the
classification evidence and the adversary's residuals are the CS-1318 record in `docs/LEDGER.md`,
2026-10-12. The repair is on main: `outlives_the_reap_wait` in `tests/test_hook_probe_bound.py` polls
for up to `REAP_WAIT` and reads a zombie as dead where the proc filesystem shows its state; the hook
probe bound is unchanged and no case is skipped.

The rework that record named was done in session 150 and is HELD - the next section; it does
not gate CS-1317's acceptance (ruling R2).

### Recorded 2026-10-21 by the session 150 landing merge, the rework HELD

The rework, the commit "CS-1318 - rework the reap replay: drive the measured arm's own reap",
fixes the earlier refutation points. Its Windows load window found no leg discriminating, so
the loaded-box clause is UNMET on Windows, and Ubuntu is not measured (`docs/LEDGER.md`,
2026-10-21, CS-1318). Its distinct adversary read HOLD, and the work is held on its worktree
branch; none of it is on main.

Next action, exactly these items, then a fresh freeze and a distinct adversary before any
landing:

1. Kill the surviving mutants S1 (reap_fired equals any failure), S2 (verdict_ms constant), S3
   (a setup or teardown error recorded as failed) and W1 (the workflow's `-ne 40` changed to
   `-gt 40` lets a short SHA through to GITHUB_OUTPUT); P3 is near-equivalent - 5 of the
   adversary's 12 fresh mutants survived.
2. Fix the two workflow weaknesses: `$(( CPUS * LOAD_PER_CPU ))` evaluates its input as a shell
   expression, and `repaired_ref` takes any commit id while `cache: pip` saves a cache.
3. Squash or reword the two cherry-picked pair messages, "CS-1318 - red test: the reap replay
   counts a zombie as a misread" and "CS-1318 - reap replay tool and dispatch-only ubuntu
   replay workflow", which carry the refuted counts and an unpublished pin.
4. Land only on a case that meets `CLAUDE.md` section 7's cost-against-risk stop; landing "to
   let the ubuntu leg run" does not.

## CS-1334

### Acceptance

After CS-1333 lands, a fresh Windows Sandbox that has never seen the project makes an anonymous
`git clone` of the public repository, and the walk record carries: the clone's exit code; that the
clone's `HEAD` equals what `git ls-remote` reports for `main`; the tip's tree against the tree of
T2 (f9b877256dd82e8d2844b6d7c876d3ab822ff097); the never-seen probes; the exit code of
`python scripts/verify_env.py`; a staged violation the hooks refuse, plus a control commit that
lands; the suite's counts, read from its log and from its exit-code file; and the README first
result, with no game installed. A grader that did not walk grades that record, and the grade's
sha256 is recorded in `docs/LEDGER.md` under this ID.

### Filed 2026-10-21 by the session 150 CS-700 close, promoted from a BACKLOG line

Promoted from the session 126 residuals' line in `BACKLOG.md` ("A clone from the GitHub remote was
never walked: the Sandbox walks this line was filed on used a bundle, and so did session 146's step
c walk, because the remote was private - TRIGGER FIRED: the CS-700 flip made the remote public, and
the CS-G03 record (`docs/LEDGER.md`, 2026-10-20) carries the walk as a residual. In order: land the
README clone command first (the line above), then walk a fresh-Sandbox anonymous clone of the
public repository with a separate grader, and record the grade's sha256 in `docs/LEDGER.md`."). The
CS-G03 and CS-700 records in `docs/LEDGER.md` carry it as a residual, and three separate gradings
ruled it non-blocking for the close. When it runs it fires the session 131 residual trigger "the
post-flip public-clone walk" in `BACKLOG.md`, and the session 150 residual on the walk runner's
execution policy there.

### Recorded 2026-10-22 by the session 150 walk grade

The first walk ran and was graded PARTIAL, clause 11 NOT MET. The record, the grade's sha256 and
what a re-walk needs: `docs/LEDGER.md`, 2026-10-22, CS-1334. The suite stall it names is CS-1349.

### Recorded 2026-11-19 by wave 0 unit U-052.5: CS-1349 folded into this row (plan ruling D84, D88), NOT A COMPLETION RECORD

The folded row CS-1349 (headline: the pre-push suite never matches its own gate history, so a small machine waits on
the 8 GiB default) was folded into CS-1334 by wave 0 unit U-052.5. Its ROADMAP line is gone and its leaf section is in
`docs/history_notes.md` under its id. Its acceptance, quoted verbatim, and graded separately at this row's close with
its own ledger record (D84, D88):

> The command `.githooks/pre-push` hands `ops/fleet_kit/fleet_suite_gate.py` is stable across
> pushes, so the gate's history for that command can match; that is a frozen-file change, so an
> adjudicated grant is recorded in `docs/LEDGER.md` before the edit is made. The tests that drive a
> real push set the gate's margin variable, `ops/fleet_kit/fleet_suite_gate.py::ENV_COMMIT_MARGIN`,
> to 0 in their own environment, naming the variable and never its value. A fresh 8 GB Windows
> Sandbox walk's pre-push suite starts. The kit half goes to MAIN; no file under `ops/fleet_kit/`
> is edited here.

It reopens with CS-1334 through ask D84 (the operator frees host RAM and the session itself reads 24 GB free with no
builder running); the walk's adjudicator rules this row's 8 GB wording before the walk (D84).

## CS-1358

### Acceptance

`tests/conftest.py` holds one session-scoped fixture `tree_population`: the tracked paths from a
single `git ls-files`, file texts read once, ASTs parsed on demand and memoised, all cached on HEAD
plus a hash of `git status --porcelain` so an edited tree re-populates. The module fixtures in
`tests/test_liveness.py`, `tests/test_archive_rot.py`, `tests/test_docs_citations.py` and the 9
guard helpers use it. Read back: `--durations` before and after on those four sweeps, the whole
suite green through `fleet_suite_gate.py`, and a grep showing no `ls-files` call in `tests/`
outside the fixture. Then ONE ANSWER note to MAIN (DONE/NA/BLOCKED with the read-back); no
further hops.

### Filed 2026-10-26 by the inbox responder

MAIN ORDER 2026-10-26 03:15 (SPEED-CS item 2), provenance verified. Measured at filing: 107
`ls-files` sites across 74 files in `tests/`, too large for one responder pass, and every push is
held behind CS-1357, so the slice waits for an interactive session.

### Filed 2026-11-01 by the headless driver, the worktree disposition

An adjudicator disposed the 2026-10-26 worktree unlanded; its branch is kept as ground for this item (the
commit that removed nothing but filed this names both tips). Measured: 0 merge conflicts; 34 files; 60
`ls-files` lines left in `tests/`, 13 outside the fixture; no `--durations` or whole-suite read-back; the
first commit alone doubles peak memory. Needed: a rebase, a ruling on synthetic-repo call sites, the
durations and a gated suite. The filing's 107 sites did not reproduce: re-count.


## CS-1366

### Acceptance

MAIN ORDER 2026-11-01 15:35 item 3 (FLEET-9): on or after 2026-11-08, read the gated runs of the prior 7
days and find zero live-state failures and zero timing failures. A failure found restarts the 7 days
after its fix. No ANSWER is owed: the ORDER's ONE ANSWER named what was fixed and this row.

### Filed 2026-11-01 by the headless driver

LANDED: every measured timing ceiling through `fleet_test_guard.budget()`, hard-fail deadlines budgeted
with each planted hang outliving the largest load factor, and no live log write from the two `run_loop`
calls in `tests/ops/test_kit_v25_lane_cap.py`. RESIDUAL, not failures: socket timeouts and joins in
`tests/surface/test_server.py` keep bare constants; `queue_loop.jsonl` sits outside the guard's watch, so
the guard cannot catch that write coming back; `budget()` reads load at assert time, and its `gate.held()`
can unlink a stale slot file in the machine gate directory, a kit behaviour reported to MAIN in the ANSWER.

### Recorded 2026-11-12 by the session 156 read of the three exit-1 runs

The responder's 2026-11-08 read counted 16 gated runs since 11-01, 13 exit 0 and 3 exit 1, and the suite
gate's durations log names no cause. Each cause below was read from the transcript of the agent that
launched the run, matched on start time, command digest and hold. Times are local, the start of the hold.
VERDICT: none of the three is a live-state failure or a timing failure, so none restarts the 7 days. The
item stays open for the 7-day read itself. Not read here: gated exit-nonzero rows dated after 2026-11-04.

- 2026-11-03 18:30:43, 967 s, the CS-1351 verifier's whole-tree run, 2 failed and 14807
  passed. CLASS: deterministic regression from the work under test, caught by the gate before it landed.
  `tests/surface/test_registry.py::test_every_upstream_field_is_either_published_or_withheld_on_the_record`
  named `Recipe.asset_path` as undecided, and
  `tests/test_archive_rot.py::test_the_deep_archives_rot_is_measured_and_pinned_per_arm` read 15 and 3
  against pins of 14 and 4. A bisect over the four commits passed at 041a7de2 and failed from 981fbb92 on,
  and the two arms failed again alone at the tip. Cleared by 822a47df.
- 2026-11-04 00:59:35, 90 s, a CS-1371 builder's `tests/advisor tests/data` run, 2 failed
  and 1990 passed. CLASS: deterministic work-in-progress state. The arm
  `tests/data/test_drift_guard_data.py::test_the_walk_reaches_every_tracked_file_in_this_repository` listed
  exactly the slice's three new files, and
  `tests/data/test_phase2_gate.py::test_the_data_layer_suite_passes_with_the_install_unresolvable` failed on
  its child run of the data suite, whose one failing test the transcript does not name. The builder staged
  its write-list and ran the same command again at 01:01:23: exit 0, 1992 passed, 89 s.
- 2026-11-04 01:51:29 (queued 44 s), 55 s, a CS-1371 builder's `tests/surface` run, 18
  errors and failures, each `make_cert exited 1` because openssl was not on that agent shell's PATH. CLASS:
  environment, the missing tool. The same two sampled tests failed the same way on a clean export of the
  parent commit 4487f886, and the re-run with Git's openssl directory on PATH at 01:53:19 exited 0, 2244
  passed.

COUNT FOR MAIN: 3 exit-1 runs, 0 live-state, 0 timing, 1 regression the gate caught, 1 unstaged-files
state, 1 environment.

### Recorded 2026-11-13 by the session 156 /done

The suite gate's durations log, every Clockspeed row with an exit since 2026-11-01, read at this /done: after
the last run classified above, 21 rows exit non-zero and none is classified - one on 2026-11-08 at 20:28 (the
responder's push, which its hand-off records blocked by guard (h) on the game patch, cleared by CS-1383),
fifteen on 2026-11-12 and five on 2026-11-13. No 7-day window ending on or after 2026-11-08 is read clean, so
the clause is NOT MET and CS-1366 STAYS OPEN. NEXT: classify those rows from each launching transcript, matched
on start, command digest and hold, and have a distinct adjudicator rule whether a guard (h) red on a game patch,
a test reading the live install's build, is a live-state failure; a failure found restarts the 7 days after
its fix. Between the ORDER and the 2026-11-08 push this read counts 19 rows, 16 exit 0 and 3 exit 1, against
the responder's 16, 13 and 3; the three exit-1 rows are the ones classified above.

### Recorded 2026-11-14 by the session 157 adjudicator, the 22 exit-nonzero rows after 2026-11-04 01:51:29

CLASSES: live-state 0, timing 1, guard (h) on the game patch 6, toolchain or other 3, work under edit 5, unreadable 7.
The timing row, 2026-11-12 16:32:07, is the venv-launcher death race in
`tests/test_claude_hook.py::test_a_sibling_holding_its_lock_is_live_until_its_process_dies`, fixed by
bdeddf77464e2e77f2f496c923eb25ce9dc25260 (on origin 2026-11-12 17:41:34); six later venv pre-push suites exited
0. RULED: a guard (h) red is a READ of the install, neither live-state nor timing, so not a failure here;
CS-1390 owns the next patch. An unreadable row cannot count toward zero, and a short -x hold does not exclude
the session guard, so the window opens after the last one: 2026-11-12 18:48:37 local. Earliest closing read: on
or after 2026-11-19 18:48:37 local. In-window rows to date read work-under-edit or toolchain, none restarts it.
Every later exit-nonzero row must cite failing ids from a log kept at the time; one without restarts the window
from the end of its hold.
The full row classification is kept gitignored in the data directory, CS-1366 classify file, sha256
895b1b9e1a50b79c3fe31229099b8cafddea181318fd8bc7e6c89127df56c8ea.

### Recorded 2026-11-24 by the session 161 closing read

VERDICT: FAIL. The 7-day clause is NOT MET, CS-1366 STAYS OPEN, and the window restarts. Basis, read from the
suite gate's durations log by tree, start, hold and exit: 31 Clockspeed rows exit non-zero with a hold starting
after the 2026-11-12 18:48:37 local window opening; the latest starts 2026-11-19 15:18:38 local, a 642 s hold
ending about 15:29 local. The CS-1366 classify file the record above names covers 22 rows through 2026-11-14,
six of them inside the window, and no log of failing ids kept at the time exists for the 25 later rows. Under the
2026-11-14 ruling each such row restarts the window from the end of its hold, so the window opens again at the end
of the last one's hold. Earliest next closing read: on or after 2026-11-26 15:29 local, provided no later
exit-nonzero row lacks failing ids from a log kept at the time.

## CS-1409

### Acceptance

Planning counts are PRINTED by the filing script from the master plan at filing time and copied into the batch record; this prose is a snapshot, never the source. Snapshot (plan-units as re-read after sequencing, which moved it since the first draft): 130 new units; 94 take a ROADMAP line (90 READY in at least one part; 4 WAITS in every part: U-045, U-046, U-146, U-149; 0 BLOCKED-OPERATOR; by leaf phase5 18, phase6 59, phase7 16, this unit included, and U-158, which has no leaf and which clause 13 returns to a planner); 30 are BACKLOG lines; 4 CLOSE-CHECK and 2 REJECTED are not filed; 21 existing items carry rows that extend them, CS-1334 among them (the plan's only BLOCKED-OPERATOR row, already a ROADMAP.md line: extended under clause 5, never filed as new).
1. Pre-flight, read back into the part-1 record: `ls ops/loop/control/lanes/QUEUE_STOP` prints the path; no lane lock is live; the high-water id is the highest CS id found across ROADMAP.md, BACKLOG.md, docs/GATED.md, docs/LEDGER.md, docs/history_notes.md, docs/item_notes/, CS-NEXT-SESSION.txt, `git log --all` and `git show origin/main:ROADMAP.md` (CS-1403 at HEAD 30157505; the hand-off's "CS-1401 the highest" is stale). Ids are taken serially above it, one writer, and `git grep -c "CS-<n>"` prints nothing for each id before it is used.
2. Every master-plan row whose state is READY, WAITS or BLOCKED-OPERATOR is exactly one ROADMAP.md line in the pointer form (ROADMAP.md line 9) under the phase heading its leaf follows from, plus one `## CS-<n>` section in that leaf with exactly one `### Acceptance` whose body equals the master plan's acceptance byte for byte, after the one recorded respelling of clause 16 where it applies. Check: a scratch script prints `rows N, lines N, sections N, acceptance mismatches 0`. A WAITS, BLOCKED-OPERATOR or spike-conditional row carries its condition as clause 0, an entry check (D93).
3. Each filed section carries, under `### Filed <date> by the session <n> wave 0 filing`: class, lane flag (true or false), planned minutes, depends on (CS ids; a staged dependency by plan key), wave id, place in each hub chain, and `Write-list:` per part (D94, a required field). Existing paths are backticked; a file the row will create is named by directory and stem, never as a path (docs/item_notes.md lines 82-84). A row that writes an ADR reads `ADR: allocated at wave entry` and carries no number (D111).
4. Every new row whose state is BACKLOG is one id-less BACKLOG.md line `- <headline> - TRIGGER: <the plan's trigger>` under the new heading `## Session 159 plan - conditional rows, filed <date> under product before process`, and has no ROADMAP line. Check: `grep -c "TRIGGER:" BACKLOG.md` rises by the count filed. Negative: a row with no trigger text in the master plan is not filed.
5. Each existing item the master plan marks as extended gains exactly what its row states and no new line: added clauses appended under its one existing `### Acceptance` (D93), or for a hub item a dated NOTE outside `### Acceptance` (D108). Check: guard (j) still reads one `### Acceptance` per section.
6. Before each batch the writer prints `ROADMAP.md <bytes> + <batch> = <sum> / 61440` and, per target leaf, `<leaf> <bytes> + <batch> = <sum> / 131072`, and files only when every sum is at or under its budget. A row that does not fit is STAGED (D93 fallback): not filed now, carried in the annex by its plan key with the word `unfiled`, and filed as the last slice of the wave before the wave that builds it. Rows are taken in wave order, so the earliest waves are always filed. `.venv/Scripts/python.exe tools/doc_budget.py` prints `VERDICT: PASS` after every batch. Negative: no new leaf file, no new phase heading, no wave heading in ROADMAP.md (D74).
7. `docs/item_notes/wave-plan.md` holds only: its header (with `**Section status: LIVE.**`), pointer lines naming the owner file of each rule, and the wave table, one row per slice, columns exactly `Wave | Group | Slice | Item | Class | Write-list | New files | Landing files | Hub text owed | Lane scope | Milestone | Entry conditions`. Wave ids are `W0a`, `W0b`, `W1`, `W2` and so on. Checks: `grep -c -E "^## CS-" docs/item_notes/wave-plan.md` prints 0 (guard (j) refuses an annex carrying an item section); an adversary reads that it restates no rule and copies no measured number (no byte count, test count, minute total or session count). Citation line (ruling P4F-14), exactly: 'Re-pack tools: <sidecars>/CS/plan-s159-tools/ - the five plan files of planning session 159, sha256 values in their docs/LEDGER.md copy record.' It is a pointer line under U-138 clause 7, carries the placeholder and never a resolved path, and lands after U-138.1 creates the file.
8. `docs/item_notes.md` gains one leaf-table row directly after line 53: the annex path, then text beginning `ANNEX, not a phase leaf - `. `tools/provenance.tsv` gains the annex row by `tools/provenance_stamp.py add docs/item_notes/wave-plan.md --class authored --item CS-<this id>`; `tools/provenance_stamp.py check` exits 0.
9. Disjointness, from the write-lists read back out of the filed leaves by an untracked scratch script: `wave <id>: parallel pairs P, shared paths 0`. Slices of one wave that share a file sit in different groups in one owner chain (D94). No `Write-list` cell holds a bookkeeping file (ROADMAP.md, BACKLOG.md, docs/LEDGER.md, tools/provenance.tsv, THIRD_PARTY.md, config/lane_scopes.json, an item-notes leaf, docs/adr/README.md, docs/ARCHITECTURE.md): those sit in `Landing files`. No feature slice's cell holds docs/OPERATIONS.md, docs/hud_doctrine.md or BOOTSTRAP.md: those sit in `Hub text owed`.
10. D73: the unit's whole diff names no out-of-tree plan path and no other app or tree on this machine by name, path or descriptor. Check: `git diff <base> HEAD | grep -c -E "^\+.*[A-Za-z]:[\\/]"` prints 0, and an adversary reads the diff for descriptors.
11. CS-NEXT-SESSION.txt gains exactly one line in its `=== NAMES` block, 78 bytes, 79 with the newline: `THE WAVE PLAN - docs/item_notes/wave-plan.md: the wave table and its pointers.` Entry condition, read back before the edit: the session 159 /done applied D80. At HEAD 30157505 it has not (the file is 24996 bytes and `S0 RULING 3` is still at CS-NEXT-SESSION.txt line 93), so at HEAD the line does not fit. Pre-check: the writer prints `CS-NEXT-SESSION.txt <before> + 79 = <after> / 25000` and writes only if `<after>` is under 25000; otherwise the line waits (D80's route is the /done's to apply, not this unit's) and part 6 stays open. After the edit `wc -c CS-NEXT-SESSION.txt` prints under 25000.
12. Each batch has one docs/LEDGER.md record `### <date> - CS-<this id> - DECISION RECORD. NOT A COMPLETION RECORD. NOTHING CLOSED. ...` carrying the map from plan key to CS id for that batch (D93), the printed budget lines and what was read back. `tests/test_ledger_entry_shape.py` passes.
13. Negative: a row whose acceptance is not a numbered list of checks, each naming a test or a command with its expected output, or which has no tier or no leaf, is not filed; the batch record lists it as returned to a planner.
14. After every batch `.venv/Scripts/python.exe tools/drift_guard.py` exits 0 and `tests/test_docs_citations.py`, `tests/data/test_item_notes_index.py`, `tests/test_doc_budget.py`, `tests/test_provenance_manifest.py` and `tests/ops/test_lane_scope.py` pass; a batch that files a Phase 6 line passes the last one only through clause 17. `git diff --stat <base> HEAD -- CLAUDE.md` prints nothing (D96: no CLAUDE.md slice).
15. Per batch, an adversary frozen at the batch SHA checks EVERY row, not a sample: one line or one BACKLOG line per row, no acceptance clause shortened.
16. Unbuilt names. Part 1 files ONE row with its acceptance untouched and runs `tests/test_docs_citations.py`. Green: every row is filed untouched. Red on a test or file the row has yet to create: every row gets the same mechanical respelling and nothing else changes - a file that does not exist at the base is written as its existing directory in backticks, a space, then the bare file name; a test name that does not exist is written `test-<rest>` and joined to its file by the word `in`, never by a double colon. The rule is written once in the part-1 record and the builder restores the names. Negative: no row is added to `tests/test_citation_tables.py` and no ceiling there is raised.
17. Lane scope. The `dashboard` scope of `config/lane_scopes.json` partitions `Phase 6` (its `anchor_phase`): every takeable Phase 6 row is a member or an `excluded` entry with a written reason, else it is unclassified (ops/loop/scope.py lines 26-28, `UNCLASSIFIED` at ops/loop/scope.py line 214), the lane refuses, and the equality at tests/ops/test_lane_scope.py line 661 is red. Every batch that files a Phase 6 line adds, in the same commit, one `excluded` entry per new row with its reason (the row's lane flag: not eligible, or served by its wave's own scope and never by this one); `items` and the member set pinned in the test are not touched. Checks: `tests/ops/test_lane_scope.py` passes after the batch; `git diff --stat <base> HEAD -- tests/ops/test_lane_scope.py` prints nothing; a scratch script prints `new Phase 6 lines N, new excluded entries N`.

### Filed 2026-11-24 by the session 161 wave 0 filing

Plan key: U-138 (parts U-138.1 to U-138.6). Class: process. Lane flag: false (not eligible: every target is a shared owner file; D129 runs it in session W0b with the lane stop file placed). Planned minutes: 720 (6 parts of 120).
Depends on: CS-1406 (U-052.6, CLOSED).
Wave: W0b, merger track.
Hub chains (order read from the plan's wave lists; U-141 fills the annex chain column): `docs/item_notes/wave-plan.md`, W0b merger-track order U-138.1, U-158, U-138.6, U-141, U-140, U-143, U-144, U-147; `config/lane_scopes.json`, W0b merger-track order U-138.3, U-138.4, U-147; `CS-NEXT-SESSION.txt`, W0b merger-track order U-138.6, U-142, U-147, CS-1366; a /done applies U-151.2, U-157 and U-152 in that order.
Write-list:
- U-138.1: `ROADMAP.md`, `docs/item_notes/phase7.md`, `docs/item_notes.md`, `docs/item_notes/wave-plan.md`, `tools/provenance.tsv`, `docs/LEDGER.md`
- U-138.2: `ROADMAP.md`, `docs/item_notes/phase5.md`, `docs/LEDGER.md`
- U-138.3: `ROADMAP.md`, `docs/item_notes/phase6.md`, `config/lane_scopes.json`, `docs/LEDGER.md`
- U-138.4: `ROADMAP.md`, `docs/item_notes/phase6.md`, `config/lane_scopes.json`, `docs/LEDGER.md`
- U-138.5: `BACKLOG.md`, `docs/item_notes/phase5.md`, `docs/item_notes/phase6.md`, `docs/item_notes/phase7.md`, `docs/item_notes/phase4-followups-960.md`, `docs/LEDGER.md`
- U-138.6: `docs/item_notes/wave-plan.md`, `CS-NEXT-SESSION.txt`, `docs/LEDGER.md`, `ROADMAP.md`, `docs/item_notes/phase7.md`, `docs/history_notes.md`

## CS-1410

### Acceptance

Run from `<repo>`; every clause is a command with its expected output.
1. `grep -c "to Coffee Stain Studios or Coffee Stain Publishing\." README.md` prints 1 (0 at HEAD: README.md lines 210-212 names the studio only).
2. `grep -c "All trademarks belong to their respective owners\." README.md` prints 1 (0 at HEAD).
3. `grep -c "It is not affiliated with, endorsed by, or connected" README.md` prints 1 (the non-affiliation sentence survives the edit).
4. NEGATIVE, no holder named: `grep -ciE "trademarks? of |registered trademark|\((R|TM)\)" README.md` prints 0.
5. NEGATIVE, budget, graded RELATIVE because five other units write README.md in no fixed order: `.venv/Scripts/python.exe -m pytest tests/test_readme_audit.py -q` passes (it holds test_readme_is_under_the_line_budget, tests/test_readme_audit.py line 535, limit README_LINE_BUDGET at :49), and `git show --numstat --format= <sha> -- README.md` for this unit's commit prints 4 added and 3 removed. No absolute line count is graded.
6. NEGATIVE, scope: for each commit of this unit, `git show --name-only --format= <sha> -- docs/OPERATIONS.md docs/assets` prints nothing (the unit's own commits, read from the ledger entry; never a `<base>..HEAD` range, which other units' commits would redden).
7. `.venv/Scripts/python.exe tools/drift_guard.py` exits 0 and `.venv/Scripts/python.exe -m pytest tests/test_docs_citations.py -q` passes.
R-tos-6's second clause (the image rule in docs/OPERATIONS.md section 13) is NOT graded here: D26 and D72 put that write in U-135.4, whose acceptance must hold `grep -c "never a game frame" docs/OPERATIONS.md` = 1; that file is hard-wrapped, so U-135.4 must keep the four words `never a game frame` unbroken on ONE line or the count reads 0. This item closes on clauses 1 to 7.

### Filed 2026-11-24 by the session 161 wave 0 filing

Plan key: U-007. Class: process. Lane flag: false (not eligible). Planned minutes: 45.
Depends on: none.
Wave: W1, group 3, slice W1-G3-S2.
Hub chains (order read from the plan's wave lists; U-141 fills the annex chain column): `README.md`, written by this row alone in W1.
Write-list:
- U-007 (one part): `README.md`

## CS-1411

### Acceptance

BASE is this unit's base SHA. Every count below is `grep -c -F -- "<text>" docs/OPERATIONS.md` (fixed string) unless a command is spelled out or another file is named; every one prints 0 at HEAD 30157505.
1. Exactly one heading `### 10.8 Waves - one per session, one gated suite, one push` (count 1), after the last line of 10.7 and before `## 11. A row that will not come back`; `grep -c "^## 1[1-4]\. " docs/OPERATIONS.md` still prints 4 (nothing renumbered). It holds six paragraphs with these bold lead-ins, in this order, each count 1: `**Sizing.**`, `**B and G move only on an exit record.**`, `**The one push.**`, `**The blocked-wave rule.**`, `**The exit record.**`, `**Slice brief.**`.
2. Sizing states, each once: one wave per session; B, the builder slices per group, is 2 in wave 1 and in wave 0's build slots, floor 1, ceiling 4; G, the groups per wave, is 3; T: at most 2 builders in a directory-wide test run at once whatever B is, and none while a whole suite runs; one unit per slice; a slice is planned at `60 planned builder minutes` (count 1); a unit takes `max(1, ceil(minutes/60))` slices (count 1); a unit above `120 planned minutes` (count 1) is split into named slices, each with its own files, before dispatch; an agent is stopped at 3 times its slice estimate; capacity is `C = B x G` slices (6, then 9, and 12 at B 4 with G 3) and there is no build-minute budget; B 4 with G 4 (16 slices) is ruled by no decision (D99(6) names 12 as the ceiling, D99(4) and D74 allow G 4), so before the paragraph is written a distinct adjudicator rules whether 12 caps C or C is B x G at G 4, the ruling is recorded in the slice's commit body, and the paragraph states the ruled reading once: the builder does not pick; the wave ends at its last planned group or at `11 h` of wall time (count 1), whichever comes first, then /done; one repair round per item per wave, in a slot of a later group, group 3 taking repairs first; a second refutation sends the item to a later wave.
3. B rises by one for the NEXT wave only when the exit record shows all three: no memory-pressure failure (a MemoryError, a commit-limit error, or a fork failure of the failed-to-fork class) in any agent or test run; no slice stopped at 3 times its estimate; `projected headroom` (count at least 1) of at least `6 GB` (count 1), where projected headroom = the lowest free-RAM read with B builders live, minus (the entry read minus that lowest read) / B. B falls by one on any memory-pressure failure. G is 4 for the next wave only when this wave's wall was under 8 h, otherwise 3 (subject to the capacity ruling of clause 2). Both RAM reads are ONE probe, spelled once in this paragraph (`free_ram_mb` count 1), run from the repository root: `.venv/Scripts/python.exe -c "import sys; sys.path.insert(0, 'ops/fleet_kit'); import fleet_suite_gate; print(fleet_suite_gate.free_ram_mb())"`. It prints MB; every threshold and every `ram_gb` value is GB, which is MB divided by 1024. It prints None where the read fails: the read is then recorded `unread` and the headroom test is not met. No kit command prints free RAM (the gate's status command does not). Negative: `8 GB` count 0 (the flat read is rejected); `240` and `45 minute` count 0. Grading arithmetic the adjudicator runs by hand: entry 19, lowest 9, B 2 gives 4, so B stays 2; entry 19, lowest 15, B 2 gives 13, so B becomes 3.
4. The one push: exactly one push of main reaches the remote per wave, the `ritual push` (count at least 1), under `.claude/commands/done.md` unchanged (`git diff --stat BASE HEAD -- .claude/commands/done.md` prints nothing). Zero retries when BLOCKED by a test; one retry only on a suite-gate or git-lock refusal. A wave can end unpushed by exactly four stops, named `refused-twice`, `other-agent-edits`, `flake`, `genuine-red`; on each the whole wave stays local, the hand-off says push pending, and no lane is launched for that gap. The only other pushes are the first-act push of commits a previous session left local and the per-group pushes of clause 5. The paragraph points at done.md and copies none of its log patterns: `SUITE-GATE:` count stays 0.
5. The blocked-wave rule: when a wave's ritual push was blocked by a test (`flake` or `genuine-red`), the next session's first act is the repair where one is needed and the first-act push, and that session pushes after every group (at most G suites). The rule lapses after one wave whose pushes all pass on the first attempt. Trigger and lapse are read from the exit record and the timing record, never asked of the operator. When r is above `0.33` (count 1) over three waves, a distinct adjudicator is asked whether a push after every group becomes the standing rule.
6. The exit record is a block of `key: value` lines headed `EXIT RECORD` inside the wave-end ledger record, counts and minutes only (no path, no environment value, no name), with exactly these keys in this order: `wave`, `B`, `G`, `slices` (planned/run), one `slice <item id>` line per slice (planned and measured builder minutes), `k` (measured/planned over the wave), `steps_min` (entry, planner, adversary, adjudication, landing), `repair_rounds` (with the ids returned to a later wave), `ram_gb` (entry, lowest, projected headroom), `memory_pressure_failures`, `stops_at_3x`, `wall_h`, `prev_push` (`landed`, or one stop name of clause 4; for `flake` only, where the timing record holds one, also the blocking test's name, which is the part of its node id after the last `::`, with no file and no directory), `group_push_blocks` (first-attempt blocks of this wave's per-group pushes, `n/a` when it pushed once), `doc_slices`, `r` (waves left local by a test / waves), `next` (B, G, `ritual-only` or `per-group`), `sessions_left`. The runbook lists the keys once; `grep -c "sessions_left" docs/OPERATIONS.md` prints 1. `prev_push` is read at the next session's first act: `landed` and `genuine-red` from the remote ref against HEAD and the CI run, the two refusal stops from the remote ref and the push log, and only `flake` from the timing record's blocked-by-flake entry (that record has no key for a red test).
7. The last key's value is in D125's form, in the ledger record: EXPECTED, the figure at the measured k with the base-rate figure `3 + ceil(U/8)` beside it; RISK BOUND, the figure at k 1; all at r 0 with the r 0.33 band for both k figures beside them; and the clause `if B never rises above 2, multiply the waves by 1.43`. Never one number alone. The runbook says this in one sentence that names the key by position ("the last key"), not by name, and restates neither the band figure nor the multiplier, so the counts of clauses 5 and 6 hold. The formula is read from the session 159 master plan, an untracked operator document that no tracked file names by path (R-exec-model-1 criterion 4); the hand-off at HEAD 30157505 names no plan document, and which unit adds a pointer is UNVERIFIED. It is not copied into a tracked file; when that source is unread the value is `not restated`. It is written after the first record that measures k and again whenever k or r moved.
8. Slice brief: one sentence that every builder brief carries the hand-off's BRIEF RULES lines word for word (pointer to `CS-NEXT-SESSION.txt`, never a copy), that a builder's report lists every NEW tracked file by path, and that no builder writes a bookkeeping file; the per-wave collision matrix over the filed write-lists is the dispatch precondition (D94).
9. One owner: `grep -c -E "60 planned|11 h|6 GB|0\.33" docs/item_notes/wave-plan.md` prints 0, and that annex carries at least one pointer reading `docs/OPERATIONS.md` section 10.8. `git diff --stat BASE HEAD -- CLAUDE.md CS-NEXT-SESSION.txt` prints nothing for this unit's commits.
10. Close condition: the first wave end after this lands has an exit record carrying every key of clause 6 (a scratch check prints `keys 18 of 18, order ok`), and after that wave's push `git ls-remote origin refs/heads/main` equals `git rev-parse HEAD` by full SHA, or `prev_push` of the following record names the stop. The item closes on that record; later waves are bound by the runbook.
11. `.venv/Scripts/python.exe tools/drift_guard.py` exits 0, `tools/doc_budget.py` prints `VERDICT: PASS`, `tests/test_docs_citations.py`, `tests/test_doc_sweep.py` and `tests/test_ledger_entry_shape.py` pass.

### Filed 2026-11-24 by the session 161 wave 0 filing

Plan key: U-140. Class: process. Lane flag: false (not eligible: `docs/OPERATIONS.md` is a hub document on one serial doc-builder chain). Planned minutes: 90.
Depends on: CS-1409 part 6 (U-138.6).
Wave: W0b, merger track.
Hub chains (order read from the plan's wave lists; U-141 fills the annex chain column): `docs/OPERATIONS.md`, W0b merger-track order U-140, U-143, U-147, then U-146 at the W1 entry; `docs/item_notes/wave-plan.md`, W0b merger-track order U-138.1, U-158, U-138.6, U-141, U-140, U-143, U-144, U-147.
Write-list:
- U-140 (one part): `docs/OPERATIONS.md`, `docs/LEDGER.md`, `docs/item_notes/wave-plan.md`

## CS-1412

### Acceptance

Terms. ANNEX = `docs/item_notes/wave-plan.md`. A slice row = one row of its wave table. BOOKKEEPING = ROADMAP.md, BACKLOG.md, docs/LEDGER.md, tools/provenance.tsv, THIRD_PARTY.md, config/lane_scopes.json, every file under docs/item_notes/, docs/adr/README.md, docs/ARCHITECTURE.md, docs/history_notes.md, docs/GATED.md, CS-NEXT-SESSION.txt, WAKEUP_NOTES.md (the last four are ruled in: the merger owns them, a builder never writes them, and they take no chain). HUB DOCUMENTS = docs/OPERATIONS.md, docs/hud_doctrine.md, BOOTSTRAP.md. A hub file = a path outside both lists that the write-list cells of 4 or more slice rows name (more writers than the 3 groups of a wave, D99(4)); a leading `NEW:` is stripped before counting, and a row that names the file in its `New files` cell counts as a writer. Row kinds, read from cells only (the table has no kind column): a MERGER-TRACK row has Wave `W0a` or `W0b`; a DOC SLICE row is any other row whose Write-list cell names HUB DOCUMENTS and nothing else; a BUILDER row is every remaining row. A landing slice is not a row: it is the `Landing files` cell of the rows of its group. A LANE-GAP row is a row whose `Lane scope` cell is not `-` and whose Group cell is not a group number. CHECK = one untracked script, `<sidecars>/CS/Scratch/<run>/annex_check.py chain`, that reads only tracked files; every clause below is one line of its output, and it exits 0 only when all of them hold.
1. The wave table has a column headed exactly `chain`. A cell is `-` or entries joined by `; `, each `<key> <pos>/<len>`. Directly below the wave table a key table headed `### Hub files` has the columns `hub | file | kind | writers`: one row per hub file with key `H001` upward (assigned by writers descending, then path ascending; a key is never renumbered, a later hub takes the next free number) and kind `file`; a hub file absent at this unit's base is written in its `file` cell by directory and stem, never as a path (docs/item_notes.md lines 82-84), and the row that creates it holds pos 1; three fixed rows `D1` docs/OPERATIONS.md, `D2` docs/hud_doctrine.md, `D3` BOOTSTRAP.md with kind `document`. CHECK prints `hub files N, keyed N, unkeyed 0, stray keys 0`. Planning snapshot (557 READY and CLOSE-CHECK unit records, write lists as recorded): N 120, 1044 row-hub pairs; the filed table is re-counted, never forced to these.
2. For every `H` key the positions run 1 to len with no gap and no repeat and rise with the row's (wave, group) place in the table; where two writers are free to swap, the dependency goes first, then the earlier-ranked row. A LANE-GAP row whose Wave cell is n ranks after every group of wave n and before wave n+1; a lane gap is serial, so clause 3 does not bind inside it. CHECK prints `chains out of order 0`.
3. One writer per group per file (criterion 5): for every (wave, group) the pairwise intersection of the slice rows' write-list cells is empty over every path that is not BOOKKEEPING and not a HUB DOCUMENT. CHECK prints `groups G, shared paths 0`. Negative: on a scratch copy of ANNEX in which one row gains a path its group sibling holds, CHECK exits 1 and prints the wave, the group and the path.
4. No BUILDER row names a BOOKKEEPING file in its Write-list cell; they sit in `Landing files`. MERGER-TRACK rows are exempt. CHECK prints `builder rows naming a bookkeeping file 0`.
5. No BUILDER row names a HUB DOCUMENT in its Write-list cell. Per document the DOC SLICE rows that name it are numbered 1 to len in table order; each carries its own `D` entry, and a row whose `Hub text owed` cell names the document carries the `D` entry of the DOC SLICE row that lands its text, so rows served by one doc slice share a pos. A document owed by some row and named by no DOC SLICE row is a fault. Per document at most one DOC SLICE row per (wave, group). `D1`: one doc slice per wave, after the builders and before the wave's gated suite and push (D94(3)). `D2`, `D3`: the doc slice sits in the first group whose build relies on the amendment, ahead of that build in the landing order or in an earlier group (D111(2)). CHECK prints `feature rows naming a hub document 0, doc slices per document per group max 1`. Negative: a `Landing files` cell that names a HUB DOCUMENT is an error; a landing slice authors no runbook, doctrine or specification text.
6. Structure order (criterion 3 as D68 and D94 rule it): on `clockspeed/surface/web/app.js` and `clockspeed/surface/web/index.html` the rows of the item filed for R-structure-1 (slice 0B) hold a lower pos than every row of the companion frame item; on `shell/main.js` CS-619's first row (it carries R-structure-4) holds pos 1; no row exists for R-structure-2 or R-structure-3 (BACKLOG lines). The `shell/main.js` term fails on the planning schedule: it is met only once the entry condition in Parts has been read true. The hub test modules that ride a product lane (D94(1)) - `tests/surface/test_web_assets.py`, `tests/surface/test_panel_seam.py`, `tests/surface/panel_harness.py`, `tests/shell/test_shell_assets.py` - are ordinary hub files here: each takes an `H` key when it has 4 or more writers and clause 3 binds it like a product file. CHECK prints `structure order faults 0`.
7. One unit per slice (D128; negative): no build slice row names two item ids. D87 closure-check rows are not build rows. CHECK prints `build rows naming two items 0`.
8. The annex agrees with the filed leaves (D94 amended): for every item, the set of paths in the Write-list and `New files` cells of its rows equals the set in the `Write-list:` field of its leaf section. Both sides are normalised first: backquotes and a leading `NEW:` are stripped, a file to be created is spelled by directory and stem on both sides, and BOOKKEEPING files and HUB DOCUMENTS are dropped from both sides (they are compared by clauses 4 and 5, not here). CHECK prints `rows whose write-list differs from the leaf 0`.
9. Nothing tracked is added: `git diff --name-only <base> HEAD` for this unit prints exactly `docs/item_notes/wave-plan.md`, and `git ls-files tools tests | grep -i -E "collision|annex_check"` prints nothing.
10. `.venv/Scripts/python.exe tools/drift_guard.py` exits 0 (0 at HEAD 30157505); `.venv/Scripts/python.exe tools/doc_budget.py` prints `VERDICT: PASS`; `tests/data/test_item_notes_index.py`, `tests/test_doc_budget.py` and `tests/test_docs_citations.py` (it scans every item-notes leaf, tests/test_docs_citations.py lines 455-472) pass. ANNEX holds no heading that begins with an item id and stays under 131072 bytes: the budget line is a warn that starts a relocate pass (tools/doc_budget.py line 14), so the bound is this clause's own. Precondition: `wc -c docs/item_notes/wave-plan.md` at the base is recorded before step 3, and the script prints `<base> + <added> = <sum> / 131072`; when the sum is over, the unit writes nothing, shortens no cell, and reports the three numbers to the adjudicator.
11. No tracked line names a plan unit key (`U-nnn`), the out-of-tree plan by path, or a count of hubs or writers in prose; the `writers` cell of the key table is the one place a count appears. This Acceptance is itself filed byte for byte, so it names items by role or CS id only.

### Filed 2026-11-24 by the session 161 wave 0 filing

Plan key: U-141. Class: process. Lane flag: false (not eligible: serial merger track of session W0b, main checkout, a shared annex file). Planned minutes: 90.
Depends on: CS-1409 part 6 (U-138.6).
Wave: W0b, merger track.
Hub chains (order read from the plan's wave lists; U-141 fills the annex chain column): `docs/item_notes/wave-plan.md`, W0b merger-track order U-138.1, U-158, U-138.6, U-141, U-140, U-143, U-144, U-147.
Write-list:
- U-141 (one part): `docs/item_notes/wave-plan.md`

## CS-1413

### Acceptance

1. Byte room, checked before any edit (D80, D129 - verify only, no new ruling): the writer prints `CS-NEXT-SESSION.txt <before> + <stanza bytes> + <rule line bytes> = <after> / 25000`, newlines counted, and writes only if `<after>` is under 25000. That printed line is the read-back. `grep -c "S0 RULING 3" CS-NEXT-SESSION.txt` is supporting evidence only: it prints 1 at HEAD 30157505 (CS-NEXT-SESSION.txt line 93; line 265 carries the different token `S0R3`, which that grep does not see), and 0 says the session 159 /done dropped open item 14, not that the bytes were freed.
2. If clause 1 does not fit, the route is D80's and nothing else: the session 156 and 157 decision blocks become one line that keeps each still-binding gist and its Rev clause (at least 156 D2, 156 D7, 157 D2, 157 D7) and points at THE 158 BASE; if that is not enough, the /done report block becomes one line pointing at its docs/LEDGER.md record. Negative: no hand-off block is copied into docs/history_notes.md, no file is created, and `ops/fleet_kit/fleet_done.py archive --apply` is not run. The record cites D80.
3. The stanza sits directly under the `=== THE SINGLE NEXT ACTION` heading line and above item 0, exactly 8 lines, at most 800 bytes, with these labels in this order:
   `WAVE STATE - a hint; ROADMAP.md, docs/LEDGER.md and git by content win; record any difference.`
   `WAVE: <wave id from docs/item_notes/wave-plan.md>`
   `PHASE: <entry|built|adjudicated|landed|pushed|ci-read>`
   `LANDED NOT CLOSED: <item ids, or none>`
   `IN FLIGHT: <item id on branch <name>; ..., or none>`
   `PUSH: <pending|landed|blocked by a test|left local by a done.md stop>`
   `LANE: <scope name from config/lane_scopes.json, or none>`
   `NEXT WAVE: <wave id>`
   Check: a scratch script prints `stanza lines 8, bytes B (max 800), labels ok, position ok`.
4. Negative: the stanza holds no closed id (docs/LEDGER.md owns those), no commit id or short hex token, no worktree agent id (a branch is named by its item-named branch, or in words as the hand-off already does), no backticked gitignored path. The commit passes the pre-commit gate and the citation gate (`tools/sha_citation_gate.py`) with no allow row added.
5. Reconcile at entry (D79: the entry step reads the stanza, then applies the fetch and fast-forward rule): an item is closed only if docs/LEDGER.md holds its closure record and ROADMAP.md holds no line for it; landed only if its change is on main by content, never by subject or by `git cherry` sign alone; in flight only if `git branch --list <name>` prints the branch. Every difference is one line in that session's first docs/LEDGER.md record and the tree's answer is acted on. Home of this rule (decision on the adversary's finding: docs/OPERATIONS.md and done.md stay barred by clause 9 and no other spec carries a stanza step; lifting the done.md bar was the alternative and lost to D99's "done.md unchanged"): ONE line in the hand-off's `=== BRIEF RULES AND TRAPS` block, beginning `- WAVE STATE:`, at most 240 bytes, giving the three tests in short form and the two moments - read and reconciled at the first act, rewritten whole from the tree by every /done (the wave end), never carried forward unchanged. /done carries the rule line itself forward verbatim (FLEET item 5). Check: `grep -c "^- WAVE STATE:" CS-NEXT-SESSION.txt` prints 1.
6. Dry resume, positive: at the start of the session after this unit a read-only agent, given the tree and no transcript, names the wave and the next slice; it matches what the stanza's writer recorded in the wave-end record. Dry resume, negative: on a scratch copy whose stanza lists under LANDED NOT CLOSED an id that has a closure record, the same agent reports `stanza differs: <id> is closed` and names the slice the tree implies.
7. Every wave end writes one docs/LEDGER.md record headed `### <date> - WAVE <id> END - NOT A COMPLETION RECORD. NOTHING CLOSED BY THIS RECORD.` whose body names, in prose lines that do not open with an id: what closed (each by its own record), what is landed and not closed, what returned to a later wave. This is the ONE heading form of a wave-end record, with no item id (precedent docs/LEDGER.md line 2745); U-140's decided fallback for a first wave end before this unit lands uses it too, and that spec's spelling with an item id is superseded here. This unit writes the first one. `tests/test_ledger_entry_shape.py` passes and `.venv/Scripts/python.exe tools/drift_guard.py` exits 0.
8. The stanza survives /done: the hand-off that session's /done writes has `grep -c "^WAVE STATE - " CS-NEXT-SESSION.txt` equal to 1 and `grep -c "^- WAVE STATE:" CS-NEXT-SESSION.txt` equal to 1, its eight lines re-derived from the tree, `wc -c` under 25000, 7-bit ASCII and LF, and `ops/fleet_kit/fleet_done.py mark` succeeds.
9. Negative: `git diff --stat <base> HEAD -- CLAUDE.md .claude/commands/done.md docs/history_notes.md docs/OPERATIONS.md` prints nothing.

### Filed 2026-11-24 by the session 161 wave 0 filing

Plan key: U-142. Class: process. Lane flag: false (not eligible: the hand-off and the ledger are written in the main checkout only). Planned minutes: 90.
Depends on: CS-1409 part 6 (U-138.6).
Wave: W0b, merger track.
Hub chains (order read from the plan's wave lists; U-141 fills the annex chain column): `CS-NEXT-SESSION.txt`, W0b merger-track order U-138.6, U-142, U-147, CS-1366; a /done applies U-151.2, U-157 and U-152 in that order.
Write-list:
- U-142 (one part): `CS-NEXT-SESSION.txt`, `docs/LEDGER.md`

## CS-1414

### Acceptance

1. In `docs/item_notes/wave-plan.md` every slice row's `New files` cell is the word `none` or lists each tracked file that slice creates, separated by `; `, in ONE spelling, the directory-and-stem form the leaves' `Write-list:` field uses (U-138 clause 3; docs/item_notes.md lines 82-84): the existing directory in backticks with its trailing slash, a space, then the file's stem in backticks, no extension. A stem that begins `test_` is ALWAYS written `test-<rest>` in the annex, whatever U-138 clause 16 recorded for the leaves. Check: an untracked scratch script reads the annex and the `Write-list:` field of every filed leaf section, normalises both sides the same way (backticks and surrounding spaces dropped; one trailing extension dropped; a leading `test-` on the stem read as `test_`; the leaf wording "a NEW <stem> module under <directory>" read as that pair), compares the pairs (directory, stem), and prints `slices S, empty cells 0, leaf new files N, annex new files N, differences 0`.
2. Negative: the same script prints `listed as new but tracked at the base 0` (for each pair, `git ls-files <directory>` at the base lists no file with that stem) and `named by two slices 0`.
3. Teeth: run on a scratch copy of the annex with one cell blanked, the script prints `empty cells 1`; with one file name removed it prints `differences 1`. Spelling teeth: with one unbuilt test module's stem planted bare (its `test_` form) in one cell of the working copy, `tests/test_docs_citations.py` is red naming it (`BARE_RE`, tests/test_docs_citations.py line 621); the plant is reverted before any commit.
4. The annex's pointer lines gain exactly one line naming the owner of the landing rule: `docs/OPERATIONS.md` section 10.8, by the heading U-140 publishes (`10.8 Waves - one per session, one gated suite, one push`), where the paragraph of clause 5 sits, and the stamp command in `docs/OPERATIONS.md` section 2. The annex states no rule: `grep -c "provenance_stamp" docs/item_notes/wave-plan.md` prints 0.
5. The owner text is written by this unit (decision on the adversary's finding: U-140's spec fixes its subsection at six paragraphs and its exit record at exactly 18 keys and carries the builder-side sentence only, so the landing-side rule had no writer; the alternative, widening U-140 to 20 keys, would change that unit's close check, so this unit takes the write). Section 10.8 gains ONE paragraph after U-140's six, lead-in `**Landing stamps.**` (`grep -c -F` prints 1; 0 at the base), stating each once: the group's landing slice runs the section 2 stamp command (docs/OPERATIONS.md line 316) for every new file its builders reported, with the row's own id as the item, and commits the rows with the landing; before the group is called landed it runs the census set of clause 7, named file by file, in the main checkout with no whole suite running; the wave-end ledger record carries, directly below the EXIT RECORD block and outside it (the 18 keys are not changed), the two lines `pushes blocked by the provenance census: <n>` (target 0) and `briefs carrying the standing lines unchanged: B of B`. It does not restate the builder-side sentence (U-140 clause 8). Checks: `grep -c -F "pushes blocked by the provenance census" docs/OPERATIONS.md` and `grep -c -F "briefs carrying the standing lines unchanged" docs/OPERATIONS.md` each print 1. The wording is ruled by a distinct adjudicator and an adversary reads that each statement appears once.
6. Proof on the first group landed after this unit that creates a tracked file, recorded in that wave's wave-end record: `git log <base>..<each builder branch> --oneline -- tools/provenance.tsv` prints nothing; the landing commits show `tools/provenance.tsv` with one row per new file; `.venv/Scripts/python.exe tools/provenance_stamp.py check` exits 0.
7. The census set the landing slice runs before the group is called landed is built from the list under TARGETED RUNS MISS THE CENSUS GUARDS (docs/history_notes.md lines 23756-23761), each guard by its file: `tests/test_provenance_manifest.py`, `tests/test_docs_citations.py`, `tests/test_sphinx_roles.py`, `tests/test_repr_rendering.py`, `tests/test_locals_rendering.py`, `tests/test_exception_rendering.py`, `tests/test_handler_exception_rendering.py`, `tests/test_assertion_rendering.py`, `tests/test_liveness.py`, `tests/test_hook_env_echo.py`, `tests/save/test_reference_resolution.py` and `tests/save/test_struct_interior.py` (the REFERENCE_COUNT_COMMON_MODE closure), `tests/save/test_reach_guard.py` (library reach), then bare `python -m mypy`, `ruff check .` and `ruff format --check .`, all with the .venv interpreter. The 72-character subject is graded by the commit-msg hook on each landing commit, not by a test run. Expected: every test passes and the three commands exit 0. `ops/fleet_kit/fleet_suite_gate.py status` shows no suite for this tree while they run. Negative, shown once in a scratch worktree and never in the main checkout: with an uncaught exception rendering planted in one module (a handler that renders `str(exc)`), the set is red in one of the two exception-rendering files.
8. That wave-end record also carries `briefs carrying the standing lines unchanged: B of B` - the `- Briefs:` line and the verify-and-reset line of the hand-off's `=== BRIEF RULES AND TRAPS` block, word for word.
9. Negative: this unit's diff touches `docs/item_notes/wave-plan.md`, the one paragraph in `docs/OPERATIONS.md` and the landing bookkeeping only: `git diff --stat <base> HEAD -- tools tests .githooks CLAUDE.md` prints nothing, and every added line of `git diff <base> HEAD -- docs/OPERATIONS.md` belongs to the clause 5 paragraph. `.venv/Scripts/python.exe tools/drift_guard.py` exits 0; `tools/doc_budget.py` prints `VERDICT: PASS`; `tests/test_docs_citations.py`, `tests/test_doc_sweep.py` and `tests/test_doc_budget.py` pass.

### Filed 2026-11-24 by the session 161 wave 0 filing

Plan key: U-143. Class: process. Lane flag: false (not eligible: the annex and the manifest are landing-side files; `docs/OPERATIONS.md` is a hub document on one serial chain). Planned minutes: 90.
Depends on: CS-1409 part 6 (U-138.6); CS-1411 (U-140); CS-1412 (U-141).
Wave: W0b, merger track.
Hub chains (order read from the plan's wave lists; U-141 fills the annex chain column): `docs/item_notes/wave-plan.md`, W0b merger-track order U-138.1, U-158, U-138.6, U-141, U-140, U-143, U-144, U-147; `docs/OPERATIONS.md`, W0b merger-track order U-140, U-143, U-147, then U-146 at the W1 entry.
Write-list:
- U-143 (one part): `docs/item_notes/wave-plan.md`, `docs/OPERATIONS.md`

## CS-1415

### Acceptance

Terms. ANNEX = `docs/item_notes/wave-plan.md`. LIST = CS-425, CS-460, CS-464, CS-467, CS-468, CS-470, CS-472, CS-474, CS-477, CS-479, CS-499, CS-501, CS-610, CS-803, CS-805, CS-807, CS-849, CS-852, CS-853, CS-855, CS-857, CS-858, CS-859, CS-860, CS-965, CS-988, CS-1074, CS-1075, CS-1077, CS-1092, CS-1094, CS-1135, CS-1137, CS-1141, CS-1142, CS-1149, CS-1150, CS-1151, CS-1241 (39 ids). CLOSING = CS-489, CS-492, CS-701, CS-842, CS-938, CS-941 (no-dimension rows the D87 sweep is expected to close). An id is OPEN when `grep -c -E "^<id> - " ROADMAP.md` prints 1 at this unit's base. An id is HELD-OPEN when it is OPEN and in LIST or CLOSING and no row of the wave table carries it (a relocation whose condition was not yet read back true: the plan gave it no row). CHECK = the untracked `<sidecars>/CS/Scratch/<run>/annex_check.py track`, reading only tracked files; each clause is one line of its output and it exits 0 only when all hold.
1. The wave table has a column headed exactly `track`, after `chain`. A cell is `-` or `SR <nn> <route>`: nn is a two-digit ordinal from 01, route is one of `product`, `lane`, `fill`. CHECK prints `SR rows N, items M, ordinals 01..N contiguous`. Planning snapshot: N 56 slice rows, M 34 items (33 READY, CS-425 in closure check); the filed table is re-counted, never forced to these.
2. Membership: a slice row is tagged if and only if its item id is OPEN and is in LIST, or is in CLOSING and the sweep left it open (D92: the no-dimension rows form one track). CHECK prints `tagged outside the sets 0, open members with an untagged row 0, held-open members without a row K` and lists the K ids; a HELD-OPEN id is reported, is exempt from tagging and does not fail the check. Snapshot: CS-501 and CS-803 are BACKLOG lines by this unit's base; CS-853, CS-857 and CS-858 move only when their conditions are read back true (CS-853 after CS-860 lands), so K is expected to be 3 at the base. Negative: a row with no ROADMAP line has no annex row at all.
3. Zero untracked rows. The planning-session re-count (D129; session 159, over the unit records) read 33 READY no-dimension items, all 33 in LIST, so 0 with neither a dimension nor a track; no later session re-runs it. From now on the check is a read of ANNEX: CHECK prints `open no-dimension rows without a track 0`, computed as the OPEN ids of LIST and CLOSING that have at least one row in ANNEX, minus the tagged ids; the HELD-OPEN ids are the separate line of clause 2. The eight no-dimension rows the plan holds (CS-815, CS-1194, CS-1202, CS-1205, CS-1206, CS-1207, CS-1208, CS-1215; each has a ROADMAP line at HEAD) keep their standing routing (D92), are not build rows of the wave table and are never tagged.
4. Order: the ordinal is the row's rank in the wave table's (wave, group, slice) order among tagged rows; a row placed in the lane gap after wave n ranks after every group of wave n and before wave n+1 (12 tagged rows sit in lane gaps in the baseline schedule). That order honours every dependency in the filed records: no tagged row sits in an earlier (wave, group) than, or the same one as, a row it depends on. Fixed constraints (D127, D77): every OPEN row of CS-853, CS-855, CS-857 and CS-858 comes after the last row of CS-860; CS-803, if OPEN, comes after the last row of CS-807 and after CS-808; CS-858 after CS-857. CHECK prints `dependency inversions 0, echo-family rows ahead of CS-860 0`.
5. Route, one per row, first match wins: `lane` when the row's filed lane flag is true; `product` when the row's class is product, or a product row outside the track depends on its item (at the snapshot only CS-1150, which CS-828 depends on); `fill` otherwise. CHECK prints `route faults 0`. Snapshot: lane items CS-460, CS-464, CS-467, CS-468, CS-472, CS-474, CS-477, CS-499, CS-849, CS-859, CS-1074, CS-1075, CS-1077, CS-1092, CS-1094, CS-1135, CS-1137, CS-1141, CS-1142, CS-1241 (20); product CS-965, CS-1150; fill the other 12.
6. Hub chains: the track owns no hub file. Every tagged row whose write-list cell names `clockspeed/save/objects.py` or `tests/save/test_properties.py` carries that file's `H` entry in its `chain` cell (the chain column item), and each of the two chains is one sequence across the track and the reliability rows with one writer per (wave, group). CHECK prints `SR hub rows without a chain entry 0`. Snapshot: objects.py has 27 writers, 7 of them tagged (CS-470, CS-472.1, CS-852.1, CS-965.1, CS-1149.1, CS-1150.1, CS-1151); test_properties.py has 18, 6 tagged (CS-472.1, CS-474, CS-477.1, CS-499.1, CS-965.2, CS-988.5); 12 rows of 11 items.
7. No reserved slot and no displaced product slice (D92, D127; negative): for every `fill` row at (wave w, group g) no product row placed later is both READY-AT (w, g) and file-disjoint from the other rows of that group. READY-AT is read from cells only: (a) every row its leaf's depends-on field names is placed in an earlier (wave, group); (b) its Milestone cell is `-` or equals the Milestone cell of a product row placed at or before wave w; (c) its `Entry conditions` cell is `-`. A product row that passes (a) and (b) and fails only (c) is not counted as displaced; CHECK lists it under `product rows held only by an entry condition K` for the adjudicator's read. D87 closure-check rows are exempt. CHECK prints `fill rows displacing a ready product row 0`. No row, cell or heading of ANNEX reserves a slot for the track: `grep -c -i -E "reserved for (the )?(track|SR)" docs/item_notes/wave-plan.md` prints 0.
8. Lane order is published, not applied here: `config/lane_scopes.json` is unchanged by this unit (`git diff --name-only <base> HEAD` prints exactly `docs/item_notes/wave-plan.md`). The lane-scope ordering item orders scopes from this column: lane-eligible product rows first, class 2 process rows after them (D92 amendment 2), and inside the process rows `SR ... lane` rows in ordinal order ahead of other rows (criterion 4).
9. A row a later ruling relocates leaves the track: the doc-sync writer deletes its annex row and does not renumber the other ordinals. In the same commit it re-counts pos and len of every `H` chain the struck row stood in, so each chain stays 1 to len with no gap; hub keys are never renumbered, and a hub left with fewer than 4 writers keeps its key and row. The chain check still exits 0 after the strike. The size of the track is the count of tagged rows and is written nowhere in prose: `grep -c -E "[0-9]+ (SR|track) rows" docs/item_notes/wave-plan.md` prints 0. After a strike CHECK accepts ordinals that are strictly increasing with gaps.
10. `.venv/Scripts/python.exe tools/drift_guard.py` exits 0; `.venv/Scripts/python.exe tools/doc_budget.py` prints `VERDICT: PASS`; `tests/data/test_item_notes_index.py` and `tests/test_doc_budget.py` pass; `git ls-files tools tests | grep -i "annex_check"` prints nothing.

### Filed 2026-11-24 by the session 161 wave 0 filing

Plan key: U-144. Class: process. Lane flag: false (not eligible: serial merger track of session W0b, main checkout, a shared annex file). Planned minutes: 90.
Depends on: CS-1412 (U-141); CS-1414 (U-143).
Wave: W0b, merger track.
Hub chains (order read from the plan's wave lists; U-141 fills the annex chain column): `docs/item_notes/wave-plan.md`, W0b merger-track order U-138.1, U-158, U-138.6, U-141, U-140, U-143, U-144, U-147.
Write-list:
- U-144 (one part): `docs/item_notes/wave-plan.md`

## CS-1416

### Acceptance

0. Entry check (D93): this row reads WAITS only because the plan tool cannot place a merger-landed unit outside wave 0; it waits on no decision. The merger lands it at the W1 entry, before group 1, and only after this ROADMAP.md line and this section are filed (ruling P4F-5).
1. `docs/adr/README.md` section 5 step 1 (line 127 at HEAD) is replaced by the one-writer rule, in these terms: the number is allocated by ONE writer, the merger, at the start of the session whose slice writes the ADR, after the lane stop file is placed and read; it is the next unused number in the section 4 index, never from the directory listing; it is recorded as a `reserved` row in section 4, committed by a landing sub-agent in the main checkout before the builder that writes the ADR is dispatched; no builder, planner or lane row picks a number and a lane row never creates an ADR. Checks: `grep -c "allocated by ONE writer" docs/adr/README.md` prints 1; `grep -c "Take the next unused number" docs/adr/README.md` prints 0.
2. Step 2 of section 5 says the file is created by the builder of the row that owns the number, with the number given in its brief; step 3 says the landing slice replaces the `reserved` row with the linked row. Section 3's table gains one row, `reserved`: allocated by the merger for a named item, no file yet, not a decision, nothing may cite it. Section 4 states the row form in a sentence, not as a table row (the number, then RESERVED for <item id> - <working title>, then the status reserved, with no link), and that a reserved number whose row is cut keeps its row with the word UNUSED and is never reused (section 2, line 41). Check: `grep -c -E "^\| .reserved. \|" docs/adr/README.md` prints 1.
3. Negative - no number is allocated here (D111: not in wave 0): `git diff <base> HEAD -- docs/adr/README.md | grep -c -E "^\+\| "` prints 1 (the status row only) and `git status --porcelain docs/adr` shows README.md alone.
4. `docs/OPERATIONS.md` gains ONE subsection, headed exactly `### 10.9 Shared documents: ADR numbers, the doctrine and the specification`, the last subsection of section 10, directly above `## 11.`. The number is fixed whichever unit lands first (decision on the adversary's finding: 10.8 is the heading U-140 publishes and U-140 grades that subsection at six paragraphs, so "the next free 10.x" collided with it and a paragraph group inside it broke its shape; a dependency on U-140 was the alternative and lost because it would hold every ADR-writing unit behind the wave runbook). This unit never takes 10.8 and never writes inside it; if U-140 has not landed, 10.9 follows 10.7 and U-140 later inserts its 10.8 above this heading. It states, once each: (a) ADR numbers - a pointer to `docs/adr/README.md` section 5 and no restatement; (b) no builder writes `docs/hud_doctrine.md` or `BOOTSTRAP.md`: a builder returns proposed wording in its report; (c) each amendment is one doc slice per file per group, landed in the first group whose build relies on it and before that build in the group's landing order, or in an earlier group; an amendment several waves rely on lands with the first of them; (d) a distinct adjudicator rules the wording and an adversary checks that it relaxes no line of the product floor (CLAUDE.md sections 1, 3 and 7) and names in its report each floor line it graded; (e) an amendment that touches a Settled entry stays out until that entry's Reversed by route is met; (f) nothing in this procedure writes CLAUDE.md; (g) a build slice that needs an ADR or a doctrine line carries the reserved number or that line in its entry conditions in the wave table. Checks: `grep -c -F "### 10.9 Shared documents: ADR numbers, the doctrine and the specification" docs/OPERATIONS.md` prints 1; `grep -c -F "### 10.8 Shared" docs/OPERATIONS.md` prints 0; `grep -c "returns proposed wording" docs/OPERATIONS.md` prints 1; `grep -c "first group whose build relies on it" docs/OPERATIONS.md` prints 1.
5. Negative - this unit amends neither governed file and not CLAUDE.md: `git diff --stat <base> HEAD -- CLAUDE.md docs/hud_doctrine.md BOOTSTRAP.md` prints nothing.
6. `.venv/Scripts/python.exe tools/doc_budget.py` prints `VERDICT: PASS` with `over budget: 0`; `.venv/Scripts/python.exe tools/drift_guard.py` exits 0; `tests/test_docs_citations.py`, `tests/test_scaffold.py` and `tests/test_doc_budget.py` pass.
7. The wording was ruled by an adjudicator that did not write it, on a candidate frozen with `tools/freeze_witness.py`; an adversary at that SHA reports no floor line relaxed and no rule restated that another file owns (the stop file is `docs/OPERATIONS.md` 10.5's; the routes are CLAUDE.md section 7's). D111 (2) in full: the adversary grades this unit's two texts, and under 4 (d) every later amendment, against each row of the session 159 ToS checklist the text touches (the checklist stays with the master plan: not copied, and not cited by row number, in any tracked file); its report names those rows and gives each the verdict `not relaxed`, and a report that names no row is returned.
8. The closing docs/LEDGER.md record names the item, both files, the ruling (decision, alternatives, why) and the outputs of clauses 1 to 6 as read back; `tests/test_ledger_entry_shape.py` passes.

### Filed 2026-11-24 by the session 161 wave 0 filing

Plan key: U-146. Class: process. Lane flag: false (not eligible: D111, a lane row never creates an ADR; both files are shared documents). Planned minutes: 90.
Depends on: none.
Wave: W1, merger landing at the wave entry, before group 1.
Hub chains (order read from the plan's wave lists; U-141 fills the annex chain column): `docs/OPERATIONS.md`, W0b merger-track order U-140, U-143, U-147, then U-146 at the W1 entry; `docs/adr/README.md`, written by this row alone in W1.
Write-list:
- U-146 (one part): `docs/adr/README.md`, `docs/OPERATIONS.md`, `docs/LEDGER.md`

## CS-1417

### Acceptance

BASE is this unit's base SHA. A GAP SCOPE is a scope in `config/lane_scopes.json` that carries a `wave` key.
1. One gap scope per annex wave that has BUILD-LANE rows. Its `wave` value is the annex wave id of the wave whose entry step grades its landings (the scope runs in the gap BEFORE that wave). It has no `anchor_phase`, its `excluded` is `{}`, and `items` holds 1 to 4 ids. Its name is the lane-scope name the annex gives that wave; where the annex gives none the name is `gap-<wave id in lower case>` and this slice writes it into the annex. The scope name and the wave id stand on one line of `docs/item_notes/wave-plan.md`, each matched as a WHOLE token: the characters before and after it are not a letter, a digit, a hyphen or an underscore (so wave id W1 does not match inside W10, nor a scope name inside a longer one). Test: `test-every_gap_scope_is_a_short_enumeration_the_wave_annex_names` in `tests/ops/test_lane_scope.py`.
2. Cap: 2 items per gap scope. It becomes 4 only after an exit record (U-140) shows a gap, launched after this item landed, whose driver run exited 0 having completed every cycle of a 2-row scope with `commit.advanced` true on each row. The test pins the ceiling (`GAP_SCOPE_CEILING = 4`); the 2 is graded by the adjudicator: a scratch check over the scopes prints `gap scopes over 2 rows: 0` until that exit record exists. This reading of R-exec-model-6's "2 until one run has cleared more" is not a ruling: before step 2 a distinct adjudicator rules it (CLAUDE.md section 6.1) and the landing commit body records the decision, the alternative and why.
3. Eligibility, one line per member inside the scope's `description`, in the form `<id>: checks <n>; frozen no; display no; dependency no; adr no; shared paths 0`: the row's acceptance is machine-checkable (every clause names a test or a command; n is the clause count); it touches no file of CLAUDE.md section 6; it needs no display acceptance, no new dependency and no operator ADR; its write-list as filed in its leaf (U-138, D94) shares no path with the interactive write-lists of the wave named by `wave`. Grammar: `description` is ONE JSON string, so the member lines follow the scope's prose and each is introduced by the separator ` | ` (space, bar, space); the test splits on that separator and finds a member by a segment that starts with its id as a whole token followed by a colon. A gated id, a phase gate row, a closed or absent id is already refused by `validate_scope`. Negative: a row failing any one test is not a member. The test fails a member with no line in the description. An adversary on a frozen SHA re-checks EVERY member against its leaf, not a sample.
4. Order (D92): reading the gap scopes in annex wave order, no class 2 process row is a member while a lane-eligible product row sits in a later gap scope or in none, unless that product row fails clause 3 for the earlier gap. Class and the product or process flag are read from the annex's class column, else from the session 159 master plan (the plan document the hand-off names), never re-derived. A scratch check prints `order faults 0`. No lane landing closes a row by itself.
5. `docs/OPERATIONS.md` section 10.8 gains ONE paragraph with the lead-in `**The lane between sessions.**` (`grep -c -F` prints 1; 0 at HEAD 30157505) stating the launch rule: one lane, `queue`, between sessions only, as this tree's lane policy; it starts only after the ritual push has read back with the remote ref equal to HEAD by full SHA; then `ops/loop/control/lanes/QUEUE_STOP` is removed and READ ABSENT, and `QUEUE_DRAINED` too when present; the run count (named without its figure), free RAM (by the probe 10.8 already spells, pointed at and not repeated: the gate's status command prints the queue, not RAM) and the suite gate queue are read first; the scope pointer is set for that process only; `-Cycles` equals the number of items in the scope, never the launcher default; no gap length is asked of the operator; NO lane is launched in a gap that follows an unpushed wave. The act belongs to the ritual's own sub-agent, after done.md's step 8 read-back and before its step 10 mark. Nothing is committed after the push, so the launch is in no tracked file: its record is the driver's own cycle log (the first row after the push) and the lane lock, both named in words, and the next session's first act reads them, with the driver process, to tell whether a lane started.
6. The same paragraph states the entry rule: session start places QUEUE_STOP and does not wait for the driver; every finished landing is graded (one adversary frozen at the landed SHA and one distinct adjudicator each) before any new build; an in-flight cycle ends on its own; its claimed row stays out of the wave; only the pushes are serialised.
7. The same paragraph states D79: after `git fetch origin main`, local main is fast-forwarded only when ALL hold: `git merge-base --is-ancestor HEAD origin/main` exits 0; `git status --porcelain` is empty; every commit of `git log --format=%H HEAD..origin/main` lies inside the `commit.pre` to `commit.post` range of a cycle row with `commit.advanced` true; every one has the operator identity as author and committer. D79's second arm (a responder commit named in its status record) is NOT written as a passable arm: at HEAD 30157505 the responder's status record has no field that names a commit, and no unit of the plan adds one (UNVERIFIED beyond the units read here), so a responder commit is unattributed and takes the STOP below until a filed unit makes that record name its commits. Then `fleet_gitlock.py run --owner <id> -- git merge --ff-only origin/main`, a re-read, and the grading of clause 6. Any other shape (divergence, an unattributed or non-operator commit, a remote ref outside the set the hand-off's first-act read (a) names, which at HEAD 30157505 is HEAD, refs/heads/main and tag v0.1.0: the paragraph points at that read and copies no ref name, so a milestone tag cut later (U-149) needs no edit here) is the hand-off's existing STOP plus a distinct adjudicator. Never a merge commit, never a force push.
8. Negative, text: `grep -c -F "directive met" docs/OPERATIONS.md` prints 0; `git diff BASE HEAD -- docs/OPERATIONS.md config/lane_scopes.json CS-NEXT-SESSION.txt | grep -c -E "^\+.*\b(120|500)\b"` prints 0 (neither run-cap figure is newly restated); `git diff --stat BASE HEAD -- ops/loop tools/headless-queue.md .claude` prints nothing (queue-b stays unwired, no driver, launcher, prompt or ritual edit).
9. Maintenance: the `_README` of the config gains the gap-scope rule in at most four lines (the `wave` key, the cap, delete a closed id from EVERY scope that names it, delete a gap scope whose last member closed). `tests/ops/test_lane_scope.py::test_the_declared_scopes_all_validate_against_the_live_roadmap` still passes: no scope is left empty.
10. Hand-off: THE LANES block (`CS-NEXT-SESSION.txt` lines 136-147) is rewritten in place by the /done of the session that lands this: the scope of the coming gap, its cycle count, one pointer to OPERATIONS 10.8, and the words that the lane is PLANNED and starts only on a read-back push (the block is committed at step 7, before the launch, so it never says a lane is running). It says "the run count" with no figure: the carried `120-run count` wording of `CS-NEXT-SESSION.txt` line 146 is not kept on a rewritten line, or clause 8's count is not 0. The block's byte count after is not above its count before.
11. `tests/ops/test_lane_scope.py` passes whole; `.venv/Scripts/python.exe -m json.tool config/lane_scopes.json` exits 0; `tools/drift_guard.py` exits 0; `tests/test_docs_citations.py` and `tests/test_doc_sweep.py` pass.

### Filed 2026-11-24 by the session 161 wave 0 filing

Plan key: U-147. Class: process. Lane flag: false (not eligible: it writes the lane's own scope file, a hub document and the hand-off). Planned minutes: 120.
Depends on: CS-1409 part 6 (U-138.6); CS-1406 (U-052.6, CLOSED); CS-1411 (U-140).
Wave: W0b, merger track.
Hub chains (order read from the plan's wave lists; U-141 fills the annex chain column): `config/lane_scopes.json`, W0b merger-track order U-138.3, U-138.4, U-147; `docs/OPERATIONS.md`, W0b merger-track order U-140, U-143, U-147, then U-146 at the W1 entry; `CS-NEXT-SESSION.txt`, W0b merger-track order U-138.6, U-142, U-147, CS-1366; a /done applies U-151.2, U-157 and U-152 in that order; `docs/item_notes/wave-plan.md`, W0b merger-track order U-138.1, U-158, U-138.6, U-141, U-140, U-143, U-144, U-147.
Write-list:
- U-147 (one part): `config/lane_scopes.json`, `tests/ops/test_lane_scope.py`, `docs/OPERATIONS.md`, `CS-NEXT-SESSION.txt`, `docs/item_notes/wave-plan.md`

## CS-1418

### Acceptance

All clauses grade `CS-NEXT-SESSION.txt` at the commit that closes the row.
1. One block: the words ONE BATCHED OPERATOR ASK appear once (counted with whitespace runs collapsed to one space: the phrase wraps across two lines here and at plan HEAD, so a line grep prints 0), inside step 1 of THE SINGLE NEXT ACTION after READS (d), and the block is exactly this text, the form written at plan HEAD, where no PREP record exists (420 bytes with its three-space indent and final newline; the ask it replaces, from its words ONE BATCHED to the end of line 41, is 205 bytes measured the same way):
   ONE BATCHED
   OPERATOR ASK (FLEET 1; optional, nothing typed back; full text: the plan, Part 1):
   A1 free 24 GB RAM: CS-1334, CS-1349; else both stay open.
   OV overlay sitting (5 min, borderless, tray 'Start overlay spike'): skipped, the overlay stays unbuilt.
   A2 pends CS-913 PREP, not yet asked.
   A3 Node ADR words: CS-1362 (CS-G11); else no.
   A5 save, walk 50 m north, save: siting bearing; else none.
2. Register and order (D109): A1 is D84, OV is D110, A2 is D41, A3 is D85, A5 is D50. OV sits directly after A1 (D110). The label A4 is retired with D86 and never reused. No other ruling has a sendable ask: D2 and D35 read NONE SENT, D8 and D46 are empty.
3. A2 is conditional (D41), two forms and never both: until `docs/LEDGER.md` holds a CS-913 PREP record (unit CS-913.1) saying the gitignored pin file and the masked-token comparison are built (no `docs/LEDGER.md` line names CS-913 with PREP at plan HEAD), the A2 line is the one in clause 1. Once that record reads back, the /done that follows replaces that one line with exactly "A2 one progressed non-dev save into corpus: CS-913; else BLOCKED." and changes nothing else in the block. That asking form is the largest: 449 bytes, 244 more than the ask replaced; the allowance is at most 250 bytes added (D109) in either form.
4. The OPERATOR block reads "OWED NOW: the batched ask (NEXT ACTION 1): A1, OV, A3, A5." while A2 pends, and "... A1, OV, A2, A3, A5." only in the asking form of clause 3, and keeps, word for word, the CS-1207 sentence (STILL OWED, halted by a safety classifier, never re-dispatch, recorded only if volunteered). `grep -c "optional Node ADR" CS-NEXT-SESSION.txt` prints 0 (1 at plan HEAD).
5. Negative, no confirmation: inside the block `grep -ci "confirm\|reply\|type "` prints 0. A1 opens on the session's own first-act free-memory read at 24 GB or more with no builder and no suite running; the CS-1334 open item keeps "Never shrink the Sandbox or the gate" and the MemoryInMB 20480 figure.
6. Negative, excluded lines: the block names none of CS-1207 (D86), CS-1366 (D82, IC-CS-1366), the store or title EULA (D15: `grep -ci "EULA" CS-NEXT-SESSION.txt` prints 0, a standing negative already 0 at plan HEAD), MAIN's G3 ruling, the Oodle verdict, CS-G04, CS-1291, a next-milestone pointer (D2) or a third store (D35).
7. Negative, no wait: no line in the hand-off makes a wave or an item wait on an answer except the rows each line names as freed; `grep -c "waits on the operator" CS-NEXT-SESSION.txt` prints 0 (a standing negative, already 0 at plan HEAD, not a red-first arm).
8. The plan: the one-time master plan on the operator Desktop (file CLOCKSPEED-MASTER-PLAN.md, never an absolute path) holds exactly one operator-ask section, in Part 1, with the five ruled ask strings in full and the D110 line worded "Required to build the transparent click-through overlay you asked for; skip it and the overlay stays unbuilt (about five minutes, borderless mode)". Present: the builder checks it, read-only. Absent (it is absent when this spec is settled): the record says UNREAD, nothing is recreated, and this clause counts as MET, so the in-tree clauses 1 to 7, 9 and 10 never wait on a planner artifact.
9. Mapping published for the wave annex (U-138 writes it; this unit does not): A1 frees CS-1334 and CS-1349's walk clause; OV frees the overlay spike's shown-window readings (U-010) and gate OV; A2 frees CS-913 and, through it, CS-600's close; A3 frees CS-1362 (CS-G11); A5 frees the bearing clause of the siting card (CS-1243). The row's ledger record carries this list.
10. Size and guards: `wc -c CS-NEXT-SESSION.txt` under 25000; `python tools/doc_budget.py`, `python tools/drift_guard.py` and `python tools/sha_citation_gate.py` exit 0; `.venv/Scripts/python.exe -m pytest tests/test_done_ritual_arms.py tests/test_dated_headings.py tests/test_ledger_entry_shape.py -q` exit 0; U-151 clause 9 (no carried id dropped) re-run and quoted.

### Filed 2026-11-24 by the session 161 wave 0 filing

Plan key: U-152. Class: process. Lane flag: false (not eligible: the hand-off is written only by a /done in the main checkout). Planned minutes: 90.
Depends on: CS-1419 part 2 (U-151.2).
Wave: W0b, merger track.
Hub chains (order read from the plan's wave lists; U-141 fills the annex chain column): `CS-NEXT-SESSION.txt`, W0b merger-track order U-138.6, U-142, U-147, CS-1366; a /done applies U-151.2, U-157 and U-152 in that order.
Write-list:
- U-152 (one part): `docs/LEDGER.md`; the hand-off text is returned to the /done

## CS-1419

### Acceptance

All clauses grade `CS-NEXT-SESSION.txt` at the commit that closes the row.
1. Kit: the kit version it names equals `version` in `ops/fleet_kit/MANIFEST.json` (32 at plan HEAD) in both places (the MAIN ORDERS line R1 and the STATE OF THE TREE kit line), each citing CS-1403. `grep -c "v31 adopted\|KIT v31" CS-NEXT-SESSION.txt` prints 0.
2. Highest id: the NEW IDS line names the highest id the allocator reads at that commit (CS-1403 at plan HEAD, higher after the wave 0 filing). `grep -c "CS-1401 the highest" CS-NEXT-SESSION.txt` prints 0.
3. Orders: THE ORDERS names MAIN 2026-11-16-1947, -2005 and -2145, each ANSWERED with its stamp: 1947 by 2026-11-17 07:04 (which supersedes 05:02), 2005 by 2026-11-16 20:37, 2145 by 2026-11-16 22:45.
4. Sent list: it names 2026-11-14 11:30, 2026-11-15 05:17, 2026-11-16 20:37, 2026-11-16 22:45, 2026-11-17 05:02 and 2026-11-17 07:04, plus any note sent later, under "never re-send"; the 22:45 note reads "delivery row verified, no outbox copy, do not recreate".
5. Holds and waits: OPEN ITEMS CS-1231 reads NOT MET at v20.1 and again at v32 (one commit, no gate-only commit first), waiting on a MAIN kit newer than v32. WAITING ON gains MAIN's G3 ruling (the identity-guard required check, unapplied) and the kit version that fixes the drive-root lane-worktree fallback and child temp variables (MAIN 2145 section 5). Rewrap-proof check (a line grep misses a phrase that wraps): with every whitespace run collapsed to one space the file holds no "newer than v31" and no "UNREAD at v31" (2 and 1 at plan HEAD), and the CS-1231 item holds "at v32". The CS-815 item, the HOLD list and "the CS-815 FIX in a kit version" are unchanged unless a recorded U-155 ruling in `docs/LEDGER.md` says CS-G09 is discharged.
6. Owed ANSWER: the next batched ANSWER carries CS-1361's landing and CS-1390's close; "the v31 push result" is gone (the 07:04 ANSWER reported the remote at the v32 head).
7. Board and drive root: the step 0 board render is removed and one phrase says the tree is opted out of FLEET 18 (`ops/status_board.json` has no `opt_in`). `grep -c "fleet_board.py render" CS-NEXT-SESSION.txt` and `grep -c "at the E: root" CS-NEXT-SESSION.txt` each print 0; the C13 line names the moved folder as in the sidecar Scratch folder, or "moved off the drive root, location UNREAD".
8. Size and guards: `wc -c CS-NEXT-SESSION.txt` under 25000; `python tools/doc_budget.py`, `python tools/drift_guard.py` and `python tools/sha_citation_gate.py` exit 0; `.venv/Scripts/python.exe -m pytest tests/test_done_ritual_arms.py tests/test_dated_headings.py tests/test_tier1_budget.py tests/test_ledger_entry_shape.py -q` exit 0. `grep -ci "headroom" CS-NEXT-SESSION.txt` prints 0 (no budget figure restated as a rule).
9. Nothing dropped: every `CS-<digits>` and `CS-G<digits>` token of the hand-off this /done started from is in the new file, or is named in the record with its reason (closed this session, with its ledger record). The diff is run by a reader that did not write the rewrite, and its output is quoted in the record.
10. Route, outcome only (not re-ruled here: D80 and the session 159 route ruling both stand, and both forbid the kit archive): `git ls-files docs/handoff-archive` prints nothing; no DECISIONS IN FORCE wording is copied into `docs/history_notes.md`; nothing is dropped (clause 9). `python ops/fleet_kit/fleet_done.py archive --auto` still runs and prints `archive skipped`. OPEN ITEMS no longer lists S0 RULING 3; the route is one DECISIONS IN FORCE line with its Rev. The record names how the byte room was made and under which ruling: each block relocated verbatim to the end of `docs/history_notes.md` (the session 159 route ruling, Route B, names four closed blocks), each line tightened in place (D80; a tightened decision line keeps the gist and Rev of 156 D2, 156 D7, 157 D2 and 157 D7), or "no block relocated, no line tightened". No order of means is mandated.
11. Kept: the first-act reads stay step 1 of THE SINGLE NEXT ACTION; `WAKEUP_NOTES.md` names the README refresh, CS-1402 and CS-1403 inside a session entry in its own `## Session <n> - <YYYY-MM-DD> - <focus>` shape (`grep -c "CS-1403" WAKEUP_NOTES.md` at least 1).
12. Inbox, nothing unclassed: every inbox note stamped after the last order the starting hand-off lists (2026-11-14-0936) that is not one of clause 3's three orders is classed in the worksheet as ack, information or terminal (at plan HEAD: 2026-11-16-2109 and 2026-11-17-2119). A hand-off line changes for such a note only if it is an ORDER or a FIX; a decision line it bears on (the ruff pins of 157 D3) is checked and the verdict written in the worksheet.
13. `docs/LEDGER.md` holds ONE record under the row's id, headed DECISION RECORD. NOT A COMPLETION RECORD, that states three Dependabot states separately, each with the date it was read back: (a) vulnerability alerts ON; (b) automated security fixes found "enabled false, paused false" and LEFT AS FOUND because MAIN ORDER 2026-11-16-1947 G5 orders the found state left and quoted; (c) version updates: no `dependabot.yml`. Standing negative, not a red-first arm (it already prints 0 for each file at plan HEAD): `grep -c "Dependabot stays off" docs/LEDGER.md BACKLOG.md CS-NEXT-SESSION.txt` prints 0 for each file.
14. State (c) carries its reason (each version bump would be process work with no product block: D83, Settled product before process), its owner (`BACKLOG.md`, the session 128 residual line on MAIN's 2026-10-05 supply-chain ORDER) and its reverser (that line's own TRIGGER). The record says this discharges the "revisit after kit v32" deferral of the 2026-11-16 20:37 ANSWER.
15. `BACKLOG.md`: that one bullet gains exactly this sentence, placed as its own clause directly before the bullet's closing `TRIGGER:` clause so that the TRIGGER clause stays last, and nothing else in the file changes: "`dependabot.yml` was decided NOT ADDED (the Dependabot decision record in `docs/LEDGER.md`): alerts stay on and each session's first act counts them; reversed by this line's TRIGGER." `git diff --stat BACKLOG.md` shows one line changed or a rewrap of that bullet only.
16. Hand-off: READS (d) of THE SINGLE NEXT ACTION gains the count of open Dependabot alerts and the rule "an open alert on a shipped runtime dependency (Electron, undici) is a top item that session". `grep -c "Dependabot" CS-NEXT-SESSION.txt` prints at least 1 (0 at plan HEAD). The addition is at most 200 bytes (the exact text under Parts is 180) and `wc -c CS-NEXT-SESSION.txt` stays under 25000. A read of Parts step 1 that fails (403, 404 or no network) does not block clauses 1, 4 or 5: recorded UNREAD with its HTTP status and the 07:04 ANSWER's lines quoted as the last read, it counts as met.
17. G3: the same record states that the `fleet-identity-guard` required status check is UNAPPLIED by adjudication (branch protection exists without required status checks, admin enforcement is on, and MAIN's note forbids touching admin enforcement), that MAIN was asked twice (the 2026-11-17 05:02 and 07:04 ANSWERs), and that it is never asked again; it waits on MAIN. `gh api` shows no change to branch protection made by this unit.
18. FLEET item 17 ("alerts and security updates stay on") against the found state (b): NOT decided locally and NOT sent as a question. D83 rules it kit text, not an open local or MAIN question; the found state was already quoted to MAIN in the 07:04 ANSWER as G5 ordered. The record states both texts and that no remote setting was changed. `git diff` shows no edit under `ops/fleet_kit/` and none to the FLEET-COMMON block of `CLAUDE.md`.
19. Negative, channel: no outbound note is authored and no line is added to the owed ANSWER by this unit. The outbox holds no new file, and the hand-off's OWED sentence differs from U-151 clause 6 by nothing.
20. Negative, repository: no .github/dependabot.yml exists (git ls-files .github/dependabot.yml prints nothing) and no workflow file changes.
21. `python tools/drift_guard.py` exit 0; `.venv/Scripts/python.exe -m pytest tests/test_ledger_entry_shape.py tests/test_dated_headings.py tests/test_docs_citations.py -q` exit 0; `python tools/sha_citation_gate.py` exit 0.

### Filed 2026-11-24 by the session 161 wave 0 filing

Plan key: U-151. Class: process. Lane flag: false (not eligible: the hand-off is written only by a /done in the main checkout). Planned minutes: 140 (2 parts of 70).
Depends on: none outside the row (part 2 after part 1).
Wave: W0b, merger track, applied by a /done.
Hub chains (order read from the plan's wave lists; U-141 fills the annex chain column): `CS-NEXT-SESSION.txt`, W0b merger-track order U-138.6, U-142, U-147, CS-1366; a /done applies U-151.2, U-157 and U-152 in that order.
Write-list:
- U-151.1: `WAKEUP_NOTES.md`
- U-151.2: `CS-NEXT-SESSION.txt`, `docs/LEDGER.md`
- clauses 13 to 21 (plan key U-157): `docs/LEDGER.md`, `BACKLOG.md`; the hand-off text is returned to the /done
Clauses 13 to 21 are U-157's clauses 1 to 9, renumbered on from 13 as the plan directs (D83); a cross-reference inside them keeps U-157's own numbering, so its clause N is clause N + 12 here.

