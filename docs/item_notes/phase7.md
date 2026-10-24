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

## CS-701

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: filed 2026-08-16 by the CS-427 adversary, which hit it while scanning that slice's diff for leaked personal data and correctly classified it as a PRE-EXISTING FALSE POSITIVE rather than a finding against the slice. FULL ENTRY relocated to this file under **CS-701 - detail**; read it before taking this item.

### detail - relocated from `docs/history_notes.md` 2026-08-23

NOTE: filed 2026-08-16 by the CS-427 adversary, which hit it while scanning that slice's diff for leaked personal data and correctly classified it as a PRE-EXISTING FALSE POSITIVE rather than a finding against the slice. Measured: the operator git author line coincides with one 4-character world name on this machine, and it is present identically on `8b3fb9d` and `1009681` - `author-line hits: 1, body hits: 0` on every revision checked. **NOTHING IS LEAKED BY THIS TODAY** - the world name is not disclosed by the author line, the coincidence runs the other way. The problem is mechanical and arrives later: **a world-name-keyed PII scan will trip on EVERY COMMIT IN THE REPO**, and a scan that is red on correct history is a scan someone switches off. CS-700's checklist includes a full-history PII scan across tracked files and commit messages, so settle the exemption rule before that gate runs rather than while it is failing. Note the CS-209 precedent: narrowing a PII blocklist by default to pre-empt a collision was DENIED BY MEASUREMENT, so an exemption here must be a named, recorded exception rather than a shortened matcher.

### Identity axis hardening - filed 2026-10-04 from an adversary pass

Check `I` in `tools/flip_checks.py` reads the RAW commit objects: every git call there that
names no environment runs with replace objects off, and a shallow or grafted repository is
refused by name rather than walked - in the identity walk and in checks 1, 2 and 4. The arms
are multi-commit synthetic histories (tip-only, first-parent, malformed-skip and case-fold
mutants killed); the record is in `docs/LEDGER.md`. The trailer axis, check `T`, now gets the
same treatment in `tools/trailer_census.py`: every git call runs with replace objects off, and
`walk` refuses a shallow or grafted repository by name (exit 2). It is a mirror, not an import,
because `tools/flip_checks.py` imports the census. CI DEPTH: the tier-1 job that runs the
census checks out with `fetch-depth: 0`, so the refusal is unconditional and cannot redden it;
`tests/test_trailer_routes.py` already pins that depth. Arms: replace by content, replace
`--graft`, shallow and grafts over a three-commit history; the record is in `docs/LEDGER.md`.

### Acceptance

the tier-3 PII scan over tracked files AND commit messages runs clean, or the collision is recorded as a known-accepted false positive with the exact matching rule that exempts it

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

## CS-1344

### Acceptance

After one full test run and one working session: Temp\cs-pt is empty or absent at run end, and
the session scratchpad holds under 5k files.

The clause above is MAIN's, verbatim. Within it: (1) every test run that writes under the
temp `cs-pt` root removes its own output on teardown, INCLUDING ON FAILURE; a run killed from
outside leaves at most its own one directory, and the next run sweeps stale ones. (2) Session
scratch stays bounded, the target under 5k files per session scratchpad. (3) Every delete
follows FLEET item 9. The item closes on ONE ANSWER note to MAIN through
`tools/outbound_send.py` naming what changed (files and mechanism), the read-back counts after
a run, and the commit hash; no further hops.

### Filed 2026-10-21 by the headless inbox responder, from MAIN's FIX note 2026-10-21-1609

The note's SHA-256 matched MAIN's outbox copy, so it carries the operator's
instruction under FLEET item 6. **IT OVERRIDES THE KEEP-FAILED RETENTION** that CS-1319,
CS-1320 and CS-1322 built into `tests/own_temp_root.py` - `KEEP_FAILED` and `STALE_AFTER_S`
keep a failed run's directory - so those pins are re-measured against this order, not
defended. One session scratchpad measured 66,234 files on 2026-10-21. Read
`docs/LEDGER.md` for CS-1319, CS-1320 and CS-1322 before changing the retention, and treat
the scratchpad half as a sweep of what a session leaves, not a recursive delete of a path
another live agent may be using.

## CS-1345

### Acceptance

An outsider who follows the `README.md` Quickstart in a fresh clone of a fork of the public repository, with every hook installed, can commit and push to that fork: the step that sets local git config `fleet.operatorIdent`, without which `ops/fleet_kit/fleet_identity.py::pre_push` refuses every push, is written in its one owner file and pointed at, not restated, from `README.md`, `.github/CONTRIBUTING.md` and `docs/OPERATIONS.md` wherever they need it; and if the kit itself must change for an outsider to push, the change goes to MAIN as a kit report and no file under `ops/fleet_kit/` is edited here

### Filed 2026-10-21 (session 150) from the CS-1338 outsider read

**THE GAP.** In a fresh clone the pre-push hook refuses every push until local git config
`fleet.operatorIdent` is set: `ops/fleet_kit/fleet_identity.py::pre_push` reads
`ops/fleet_kit/fleet_identity.py::operator_idents` from the clone's LOCAL config and, finding
none, refuses through `ops/fleet_kit/fleet_identity.py::_no_operator`, whose message names the key
and the fix. A fresh clone never carries the key. `README.md`, `.github/CONTRIBUTING.md` and
`docs/OPERATIONS.md` never mention it, so an outsider following the Quickstart can commit -
`ops/fleet_kit/fleet_identity.py::commit_msg` strips and always returns 0 - but cannot push.

**THE KIT IS VENDORED** (FLEET item 11), so the fix in this tree is a written step; what value an
outsider sets, and whether a fork should need the key at all, is the kit's to say, through MAIN.
Filed in Phase 7 because it is the public repository's outsider path, beside CS-1334's walk.

## CS-1349

### Acceptance

The command `.githooks/pre-push` hands `ops/fleet_kit/fleet_suite_gate.py` is stable across
pushes, so the gate's history for that command can match; that is a frozen-file change, so an
adjudicated grant is recorded in `docs/LEDGER.md` before the edit is made. The tests that drive a
real push set the gate's margin variable, `ops/fleet_kit/fleet_suite_gate.py::ENV_COMMIT_MARGIN`,
to 0 in their own environment, naming the variable and never its value. A fresh 8 GB Windows
Sandbox walk's pre-push suite starts. The kit half goes to MAIN; no file under `ops/fleet_kit/`
is edited here.

### Filed 2026-10-22 by the session 150 CS-1334 walk

**THE GAP.** `.githooks/pre-push` (FROZEN, `CLAUDE.md` section 6) runs its whole suite through
`ops/fleet_kit/fleet_suite_gate.py`, and the command it hands the gate ends with `--junitxml` and
a report path inside a fresh `mktemp -d` directory, new on every push.
`ops/fleet_kit/fleet_suite_gate.py::cmd_hash` covers every command word, so a pre-push run never
matches the gate's own history: `ops/fleet_kit/fleet_suite_gate.py::required_commit_mb` falls
back to `COMMIT_DEFAULT_MB`, and `ops/fleet_kit/fleet_suite_gate.py::run` adds
`ops/fleet_kit/fleet_suite_gate.py::commit_margin_mb`, whose default is `COMMIT_MARGIN_MB` -
12288 MB of free commit charge on every push. On a machine with less,
`ops/fleet_kit/fleet_suite_gate.py::acquire` takes no slot, waits `WAIT_S` (3600 s) and raises
`GateRefused`, which `ops/fleet_kit/fleet_suite_gate.py::main` returns as exit 3: the push fails
closed.

**THE TESTS LEAVE THE MARGIN AT ITS DEFAULT.** The tests that drive a real push -
`tests/test_cs1327_push_suite_runs_in_the_venv.py`, `tests/test_hook_env_echo.py`,
`tests/test_hook_interpreter_ladder.py`, `tests/test_hook_probe_bound.py`,
`tests/test_identity_hooks.py`, `tests/test_pre_push_ref_race.py`,
`tests/test_pre_push_suite_floor.py` and `tests/test_probe_refusal_output.py` - move only the
slot directory, through `tests/fleet_hook_kit.py::suite_dir_env`, and never set the margin
variable. A fresh slot directory holds no history either, so each push they drive needs the same
default.

**THE EVIDENCE, AND WHAT IS INFERRED.** The CS-1334 walk's suite, in a fresh 8 GB Windows Sandbox,
stalled at about 70 percent with 0 failures (`docs/LEDGER.md`, 2026-10-22, CS-1334). That this
admission rule caused it is INFERRED from the constants above, and was not measured inside the
Sandbox.

**THE KIT HALF IS REPORTED TO MAIN** (FLEET item 11), in a FIX note of 2026-10-22 06:47: admit a
run when no other slot holder is live, or cap the requirement at the machine's own commit limit.
The tree-side half - a stable pre-push command and the tests' margin - is this item. Filed in
Phase 7 beside CS-1334, whose re-walk it unblocks.
