#!/usr/bin/env python
r"""Queue loop - the driver that turns a ONE-ROW worker into a queue drain.

`ops/loop/lanes.py` decides WHO may run. `ops/loop/lane_launcher.py` turns a
claim into a running headless worker. Neither of them ever runs a second time on
its own. This module is the missing repeat, and it is also the thing that WAITS.

WHY THE DRIVER OWNS THE REPEAT, NOT THE WORKER. The cheaper design is a worker
that loops internally: read a row, do it, read the next. It fails two ways.
First, context - a `claude -p` worker accumulates every row's transcript for the
whole run, and quality degrades long before the window is full. Second, blast
radius - a worker killed on row three loses rows four through twelve with it,
because they were never separate units of work. ONE ROW PER PROCESS makes a
crash cost exactly one row and makes every row start from a clean context that
reads its state off disk. The price is a driver, and the driver is this file.

WHY THE DRIVER OWNS EVERY WAIT, AND THE WORKER OWNS NONE. This is the reason the
file exists in this shape rather than a cheaper one, and it was paid for twice
in the tree this was ported from. The rule "block until your own CI run
finishes" was written as PROSE in the worker's prompt and MEASURED over six
cycles: cycles 2 and 3 complied, cycles 4, 5 and 6 exited early, and each early
exit let the next cycle's push cancel the run the previous cycle was being
graded on. AN INSTRUCTION A WORKER CAN RATIONALIZE PAST IS NOT A MECHANISM. The
driver cannot rationalize: it is the only thing that starts the next cycle, so
while it is inside the wait there exists nothing that could cancel the run. The
serialization is structural rather than hopeful, and the cost is a Python
process sleeping - which is free, unlike an agent sitting in a poll loop.

WHAT THAT MEANS AGAINST **THIS** REPO'S CI, read out of the two workflow files
rather than assumed:

  - `.github/workflows/tier1.yml` fires on `push: branches: ['**']`, so a
    worker's push to `main` runs it automatically. It sets
    `concurrency.cancel-in-progress: true`, so cycle N+1's push CANCELS cycle
    N's still-running tier1. That is the same self-cancelling trap, and the
    driver-owned wait is what defeats it.
  - `.github/workflows/tier2.yml` fires on `schedule`, on a `v*` TAG push, and
    on `workflow_dispatch` - NOT on a branch push. So the full suite (both
    OSes, the clean-checkout probe, the shell suite) does not exist for a
    worker's commit unless something dispatches it. This driver dispatches it.
    tier2 sets `cancel-in-progress: false`, so a dispatched run cannot be
    cancelled by the next cycle at all.

So a cycle's acceptance is: tier1 on the pushed sha, plus a dispatched tier2,
both graded on their JOBS, both waited out here. The worker never blocks.

A NOTE THAT IS NOT AN EXCUSE: `.githooks/pre-push` runs the WHOLE suite with
`-x` on every push, despite its own header calling itself the fast subset. It is
a FROZEN file (CLAUDE.md section 6) and this item does not touch it. The
consequence is stated rather than hidden - the worker's push pays a full local
suite inside the hook, and the fast-subset rule in `tools/headless-queue.md`
therefore governs the worker's own iteration loop, not its push.

A VERDICT IS A SUMMARY LINE **AND** AN EXIT CODE, NEVER EITHER ALONE. A crashed
parallel run leaves no summary line, and `grep -c FAILED` over that log returns
0 - which reads exactly like green. `summarize_pytest` therefore answers `ok`
only when a summary line was PARSED and the exit code is 0, and it carries the
verbatim line and the integer code into the ledger so the claim can be re-graded
from the file alone. The same principle governs the CI grader: a required job
that matches NOTHING is `unavailable`, an answer about the tool, and never a
pass.

EVERY MATRIX LEG IS GRADED, NOT THE POOL. `full suite (ubuntu-latest)` and
`full suite (windows-latest)` are two jobs, and a grader that asked "did any leg
pass" would let the weakest go unmeasured while its acceptance clause still read
green. `grade_ci_jobs` requires EACH matched job to be `success` and names the
one that was not.

WHY THE LANE LOCK IS TAKEN PER CYCLE, NOT HELD ACROSS THE LOOP. `lane_state`
decides FREE / RUNNING / RECLAIMABLE by PROBING the recorded pid, and
`launch_lane` re-points the lock at the WORKER. Across a whole loop the lock
would name a worker that exits after row one while the driver keeps running, so
the lane would read RECLAIMABLE under a live driver - the exact ambiguity the
three states exist to remove. Per-cycle acquire plus a `finally` release keeps
the lock's meaning honest: held means a worker is up right now.

WHY A REFUSED ACQUIRE IS NOT AN ERROR. `try_acquire_lane` answers
`{"ok": False, "refused": "lane_held"}` and writes nothing when the lane is
genuinely busy. A driver that treated that as fatal would die the first night
the operator's own session overlapped by a minute.

WHY LIVENESS IS A PID PROBE AND NOT `Popen.wait()`. There is no Popen to wait
on - `launch_lane` spawns THROUGH powershell and hands back a pid. And this
driver may be killed and relaunched while a worker is still up, at which point
it has no child handles at all, only a pid it can read off the lock. A pid probe
works in both worlds, and it is the same probe `lane_state` uses, so the driver
and any dashboard can never disagree about whether a worker is alive.

A KILL IS NOT DONE UNTIL IT IS VERIFIED. `taskkill` can fail - access denied, or
a re-parented subagent that outlives the wrapper whose pid was killed - and it
reports that only in output `_taskkill` deliberately swallows. An UNVERIFIED
kill is the same hazard as no kill: cycle N+1 fires a second worker into the
same lane worktree while the first is still writing, and two writers in one
working directory is not recoverable by retrying. So the kill is followed by a
bounded re-probe of the SAME liveness predicate, and a worker that outlives it
is recorded `timeout_kill_failed` and STOPS the loop.

TWO CLOCKS, ON PURPOSE. `clock` (time.time) stamps the ledger, because a row an
operator reads at 3am has to carry wall time. `monotonic` measures every
deadline, because wall time is NOT monotonic: an NTP step backwards silently
EXTENDS a deadline by however far the clock moved, and a frozen clock extends it
forever. The worker deadline also starts at LAUNCH rather than at cycle start,
because the acquire retries above can legitimately burn ten minutes that are not
the worker's to pay for.

A PID IS NOT AN IDENTITY. A pid probe answers whether SOMETHING holds the pid,
never whether it is still OUR worker - an OS reissues pids. So the driver
captures the process start time at launch and pairs it with the pid, reusing
`lanes`' own predicate rather than deriving a second one. It is fail-soft in
every direction: no start time, no psutil, an unqueryable pid all degrade to the
plain pid probe rather than declaring a live worker dead.

ONE FAULT IS NOT THE WHOLE NIGHT. `run_cycle` is wrapped: an unexpected fault
becomes an `error` record that is appended and emitted like any other. The
SILENT half of that defect was the worse half - without it, a fault leaves NO
ledger row and the morning's only evidence is a log that stopped. A fault that
REPEATS is different, and `max_consecutive_errors` stops the loop. A LANE THAT
WILL NOT START is counted separately again, by
`max_consecutive_launch_failures`: a refusal is not a fault inside a cycle, it
is the cycle never happening, and one counter for both would report the two with
one exit code.

AND A THIRD COUNTER HOLDS THE INVARIANT THOSE TWO ONLY APPROXIMATE: no night in
which no cycle ever SHIPPED may be reported as a success. Two counters that each
name one cause reset each other, so a night that alternates causes - a held
lane, then a refused launch, then a held lane - satisfied neither and ran all
twelve cycles to exit 0. `max_consecutive_unproductive` asks the general
question against the `PRODUCTIVE_OUTCOMES` allowlist AND the row's own `ok`
roll-up, and is checked LAST so the two specific words and their exit codes
still win whenever one of them applies.

A COUNTER CANNOT HOLD THAT INVARIANT ALONE, because every counter needs three
consecutive cycles and `--once` grants one. Driven with a budget of one, a held
lane reported `cycles_run=1 stopped_by=max_cycles` and exited 0 - a success
banner over a no-op. So the invariant is held in TWO places: the counter ends a
long night early, and `main` refuses EXIT_OK for any run whose records contain
no shipping cycle, whatever the budget. The stop WORD may still be `max_cycles`
- the night did end the way it was asked to - but the NUMBER a launcher reads
says nothing was accomplished.

AND NO STOP WORD MAY MEAN SUCCESS BY DEFAULT. `_SUCCESS_STOPS` is the closed set
permitted to exit 0; anything outside it and outside `_STOP_EXIT` is
EXIT_UNKNOWN_STOP. A `.get(stopped, EXIT_OK)` made that set implicitly infinite,
so a hard stop copied from the `timeout_kill_failed` block - which already
assigns a word that is not a `STOPPED_BY_*` constant - would have exited 0.

ONE DRIVER PER LANE, NOT ONE PER BOX. The lane lock stops two WORKERS, not two
DRIVERS - a driver claims and releases that lock once per cycle and is otherwise
idle, so it is invisible to the lock for most of its life. A named mutex held for
the process lifetime is the guard, and its NAME IS DERIVED FROM THE LANE by
`driver_mutex`. A constant here was the defect: it refused every second driver
whatever lane it was asked for, so a second lane could not start at all, and the
refusal was indistinguishable from the one that protects a lane from itself. A
hand-written second constant is not the fix either - the roster is the only place
a lane is declared, and a name list beside it goes stale on the first edit that
forgets it. The name also carries THIS CHECKOUT's identity, because a named mutex
is a machine-wide object and this box runs sibling projects.

AND THE NARROWING IS PAID FOR BY A SECOND, BOX-WIDE GUARD. Scoping the driver
mutex per lane AND per checkout opened a hole the old constant had closed by
accident: two clones at different paths derive different names and keep disjoint
lock roots, while `lane_launcher.WORKTREE_BASE` resolves both to ONE
`cs-lane-<lane>` checkout - two workers in one working directory. So
`_driver_singleton` takes `worktree_mutex` as well, keyed on the working
directory and on nothing else, and a refusal on either guard refuses the run.

STOP IS THREE FILES, CHECKED BEFORE EVERY CYCLE INCLUDING THE FIRST. A driver
that only checks between cycles fires one unwanted worker on every start, and
against this lane that is one work item executed and committed.

SIDE-EFFECT FREE AT IMPORT. Nothing below creates a directory, reads the control
plane or spawns anything at import time. `lanes` and `lane_launcher` are bound
LAZILY through the module `__getattr__` at the bottom, so importing this file to
read a constant does not require the rest of the lane to be present.
"""

from __future__ import annotations

import argparse
import contextlib
import functools
import hashlib
import importlib
import importlib.util
import json
import os
import re
import subprocess
import sys
import time
import uuid
from pathlib import Path
from types import MappingProxyType
from typing import NamedTuple

_HERE = Path(__file__).resolve().parent

# tools/ carries no __init__.py, so `toolpath` is imported under its BARE name:
# importing it as `tools.toolpath` makes mypy resolve one file under two module
# names and refuse the run outright. This is the same six lines
# scripts/make_cert.py, scripts/make_shortcut.py and scripts/verify_env.py each
# carry, and the same reason.
_TOOLS_DIR = Path(__file__).resolve().parents[2] / "tools"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from toolpath import resolve_tool  # noqa: E402

LANE = "queue"

REPORTS = _HERE / "reports"
CONTROL = _HERE / "control"

#: Relative so `--control-dir` can point the whole set at a sandbox.
STOP_RELPATHS = ("STOP", "lanes/QUEUE_STOP", "lanes/QUEUE_DRAINED")
STOP_FILES = tuple(CONTROL / rel for rel in STOP_RELPATHS)
#: The bare names, derived from one definition rather than written out twice -
#: `stop_reason` reports a NAME and `main` has to turn it back into a path.
STOP_NAMES = tuple(Path(rel).name for rel in STOP_RELPATHS)

#: Append-only, one JSON object per line. NOT tmp+os.replace: the atomic-write
#: rule (CLAUDE.md non-negotiable 5) exists for files another process POLLS
#: mid-write, and this is the opposite shape - a ledger nothing polls, where a
#: replace would rewrite every prior row on every cycle and lose any concurrent
#: append. An O_APPEND write of one short line is the durable form here.
CYCLE_LOG = REPORTS / "queue_loop.jsonl"

#: Twelve rows is roughly one unattended night. A bound rather than "until
#: stopped" means a driver nobody notices still ends.
DEFAULT_MAX_CYCLES = 12
#: A WEDGE ceiling, not a work budget. It must sit above the worst LEGITIMATE
#: cycle, and a legitimate cycle here is the worker's own work plus a full local
#: suite inside the frozen pre-push hook. Everything below this is bounded by
#: the prompt's own budgets rather than by this kill.
DEFAULT_CYCLE_TIMEOUT_S = 14400
#: Between cycles, never after the last. Long enough for the worker's push to
#: land and for the remote ref to settle before the next worker reads the tree.
DEFAULT_SETTLE_S = 45
#: A dead worker is noticed within this. Polling faster buys nothing against a
#: multi-hour run and only wakes the box.
DEFAULT_POLL_S = 10
#: TOTAL acquire attempts, not attempts-after-the-first.
ACQUIRE_RETRIES = 20
ACQUIRE_WAIT_S = 30
#: How long a killed worker gets to actually die before the kill is declared
#: FAILED. Sized for a wedged process tree with children to reap, not for a slow
#: shutdown - `/F` grants none. Short enough that a driver which cannot kill its
#: worker says so within a poll or two.
DEFAULT_KILL_GRACE_S = 15
#: Consecutive `error` outcomes before the loop gives up. One genuine fault plus
#: two chances for it to be transient; a fourth would be watching the same
#: traceback scroll past all night.
DEFAULT_MAX_CONSECUTIVE_ERRORS = 3
#: Consecutive `launch_failed` outcomes before the loop gives up. SEPARATE from
#: the error limit and sized by the same reasoning - one genuine refusal plus
#: two chances for it to be transient. A lane that cannot start does not start
#: better on the ninth attempt, and before this existed a mis-wired lane burned
#: a whole night's budget while every row said the same word.
DEFAULT_MAX_CONSECUTIVE_LAUNCH_FAILURES = 3
#: Consecutive cycles that completed NOTHING before the loop gives up, whatever
#: mixture of refusals, holds and faults they were. Sized to match the two
#: counters above rather than chosen separately: a night that has produced three
#: unproductive cycles in a row has produced no work, and the reason it gives
#: for each one has no bearing on that.
DEFAULT_MAX_CONSECUTIVE_UNPRODUCTIVE = 3

#: THE DRIVER'S OWN COPY of `lane_launcher.LAUNCH_REASONS`, duplicated on
#: purpose. `_fault`'s structural rule is that this module renders whole only an
#: exception type IT defines, because it BUILDS that message - and a promise
#: made in another file is not a substitute (CLAUDE.md non-negotiable 12).
#: Holding the vocabulary here means every word written into a row is a literal
#: this file contains, so a launcher that grows a new code degrades to today's
#: bare type name rather than writing a string this module never saw.
#:
#: The cost of a second copy is drift, and it is paid by
#: `test_the_driver_and_the_launcher_hold_the_same_reason_vocabulary`, which
#: asserts the two tuples are EQUAL. Without that arm a launcher-side addition
#: degrades silently, which is the defect CS-970 closed, reintroduced by an edit.
_LAUNCH_REASONS = (
    "lane_not_wired",
    "command_doc_missing",
    "git_not_found",
    "main_tree_refused",
    "worktree_create_failed",
    "runner_missing",
    "shell_not_found",
    "spawn_failed",
    "runner_exited_early",
    "spawn_no_pid",
    "repoint_refused",
    "unexpected_fault",
    "unspecified",
)


# ---------------------------------------------------------------------------
# CI acceptance. See "WHAT THAT MEANS AGAINST THIS REPO'S CI" above.
# ---------------------------------------------------------------------------


class CiSpec(NamedTuple):
    """One workflow, and how to decide whether it passed.

    Attributes:
        workflow: The workflow file name, as `gh` names it.
        dispatch: True when the workflow declares `workflow_dispatch` AND does
            not fire on a branch push, so this driver has to ask for the run.
            False for a workflow the push already triggered - dispatching one
            of those can only fail, and the failure would read as a tooling
            fault rather than as the mistake it is.
        required: Job-name matchers that must EACH match at least one job, every
            match of which must conclude `success`. A matcher matches a job when
            the name is equal to it or starts with it - the prefix form is what
            covers a matrix, where one declared job becomes one job per leg.
        advisory: Job-name matchers excluded from grading entirely, because the
            workflow itself declares them advisory.
    """

    workflow: str
    dispatch: bool
    required: tuple[str, ...]
    advisory: tuple[str, ...]


#: A BRANCH ref, which is what `gh workflow run` takes.
CI_REF = "main"

#: `.github/workflows/tier1.yml` - `jobs.fast.name`, `jobs.save.name` and
#: `jobs.guards.name`. It fires on every branch push, so it is never dispatched
#: from here.
#:
#: EVERY DECLARED JOB APPEARS HERE, and a test enforces it both ways. A shard
#: added to the workflow and nowhere else is graded by accident: skipped, or
#: never reached by the run, it falls through the grader's tail into `success`
#: and the lane ships the next row onto a main whose new shard was never
#: measured.
CI_TIER1 = CiSpec(
    workflow="tier1.yml",
    dispatch=False,
    required=("gates, lint, types, tests", "tests (save shard)", "tests (guard shard)"),
    advisory=(),
)

#: `.github/workflows/tier2.yml`. Three of its four jobs are matrices over
#: {ubuntu-latest, windows-latest}, hence the trailing " (" on each matcher -
#: that is what makes the grader see two legs and demand both. The audit job
#: names itself advisory and its steps carry `continue-on-error`, so grading it
#: would end a night over a dependency advisory.
CI_TIER2 = CiSpec(
    workflow="tier2.yml",
    dispatch=True,
    required=("full suite (", "clean-checkout probe (", "shell suite ("),
    advisory=("dependency and license audit (advisory)",),
)

CI_SPECS = (CI_TIER1, CI_TIER2)

#: The words a verdict may be. Anything outside this set is a bug in this file
#: rather than a state of the world, which is why the tuple is asserted in
#: tests/test_queue_loop.py.
CI_SUCCESS = "success"
CI_FAILURE = "failure"
CI_CANCELLED = "cancelled"
CI_SKIPPED = "skipped"
CI_TIMEOUT = "timeout"
CI_UNAVAILABLE = "unavailable"
CI_UNKNOWN = "unknown"
#: The cycle completed and the remote ref did not move, so the worker shipped
#: nothing and there is no run to wait for. A VERDICT rather than an absent key,
#: because an absent key made the roll-up's verdict clause vacuously true and a
#: 972-second cycle that pushed nothing was recorded `"ok": true`.
#:
#: KNOWN AND ACCEPTED: `_verdict_for` reads a GitHub conclusion through
#: `in CI_VERDICTS`, so this widens that acceptance by one word. GitHub's
#: conclusion vocabulary is fixed and contains no `no-push`, so the widening is
#: unreachable; it is recorded here rather than discovered later.
CI_NO_PUSH = "no-push"
CI_VERDICTS = (
    CI_SUCCESS,
    CI_FAILURE,
    CI_CANCELLED,
    CI_SKIPPED,
    CI_TIMEOUT,
    CI_UNAVAILABLE,
    CI_UNKNOWN,
    CI_NO_PUSH,
)

#: Worst-first. The roll-up across workflows returns the WORST verdict seen, so
#: one green workflow can never carry a second one that answered nothing.
_VERDICT_RANK = (
    CI_FAILURE,
    CI_TIMEOUT,
    CI_CANCELLED,
    CI_UNKNOWN,
    CI_UNAVAILABLE,
    CI_SKIPPED,
    CI_NO_PUSH,
    CI_SUCCESS,
)

#: Verdict words that make a cycle NOT good news. `CI_FAILURE` because a red
#: gate is a break; `CI_NO_PUSH` because a cycle that shipped nothing produced
#: no evidence at all and calling it ok is the defect this tuple was added to
#: close.
#:
#: DELIBERATELY NOT WIDENED FURTHER. `CI_UNAVAILABLE` keeps doing exactly what
#: it does today to `ok` - tightening it is a separate judgement about a
#: separate condition and is out of scope here.
_CI_ROLLUP_BAD = (CI_FAILURE, CI_NO_PUSH)

#: A GitHub job conclusion that means the job did not pass. `timed_out`,
#: `action_required` and `startup_failure` are separate words for the same
#: answer, and lumping them into `unknown` would let a job that never ran read
#: as an unclassified curiosity instead of a break.
_JOB_BAD = ("failure", "timed_out", "action_required", "startup_failure")

#: 90 minutes per workflow. tier2's own jobs carry a 30-minute `timeout-minutes`
#: each and run in parallel, so this bounds queueing on shared runners rather
#: than the work.
DEFAULT_CI_WAIT_S = 5400
#: A run is measured in tens of minutes. Polling faster than a minute buys
#: nothing and spends API quota `gh` shares with everything else on the box.
DEFAULT_CI_POLL_S = 60
#: Per `gh` / `git` invocation. These are single API round trips, never the run
#: itself - the run is waited out by polling, never by holding a subprocess.
GH_TIMEOUT_S = 120
#: One cycle's push plus the dispatch it triggers is two runs; this covers a
#: night of them plus whatever else was pushed in between.
CI_RUN_LIST_LIMIT = 20
#: A dispatched run takes a beat to become visible to `gh run list`.
CI_TRIGGER_TRIES = 6
CI_TRIGGER_WAIT_S = 10


def _console_interpreter() -> str:
    """`python.exe` in preference to the `pythonw.exe` this may be running as.

    The detached launcher starts this driver under `pythonw` so no console
    window flashes on the operator's desktop for a run measured in hours. That
    makes `sys.executable` pythonw, and handing pytest an interpreter with no
    console attached is a difference nobody wants to discover from a truncated
    log at 3am - the whole point of the suite verdict is that it reproduces what
    a person would get by typing the command themselves.

    Falls back to `sys.executable` when no sibling exists, which is every
    non-Windows layout and any embedded build.
    """
    exe = Path(sys.executable)
    if exe.name.lower() == "pythonw.exe":
        sibling = exe.with_name("python.exe")
        if sibling.is_file():
            return str(sibling)
    return str(exe)


#: The local full suite, for a box with no `gh` credentials and for proving a
#: cycle end to end without a CI round trip. `tests` is named explicitly rather
#: than left to a bare recursive run - CONVENTIONS.md section 7.1.
LOCAL_SUITE_ARGV = (_console_interpreter(), "-m", "pytest", "tests", "-q")
#: A full local suite has been measured in the tens of minutes here. This bounds
#: a wedge, not the work.
DEFAULT_SUITE_TIMEOUT_S = 5400
#: How long a lane waits behind another lane's suite before it runs its own
#: UNRATIONED and says so. DERIVED from the timeout above rather than written as
#: a second number, and the multiple is the whole content of the choice: a
#: waiter has to outlast a holder that runs all the way to its OWN wedge ceiling,
#: or the ration would fall open while the holder was still legitimately working
#: - which is the overlap it exists to prevent, arriving on a timer. `ration.py`
#: itself defaults to waiting forever and holds no number, so this is the one
#: place the figure lives.
SUITE_RATION_CEILING_S = 2 * DEFAULT_SUITE_TIMEOUT_S
#: Between attempts on a held ration. Sized against a suite measured in tens of
#: minutes: polling faster buys nothing and only wakes the box.
SUITE_RATION_POLL_S = 30.0

_NO_WINDOW = 0x08000000 if os.name == "nt" else 0  # CREATE_NO_WINDOW

#: Two names, never one. The driver mutex is held for the WHOLE run, so an
#: append taken under that same name would block every other appender for the
#: length of the night - correct-looking and useless.
#:
#: THE DRIVER'S NAME IS DERIVED PER LANE BY `driver_mutex` AND IS NOT A CONSTANT.
#: A second hand-written constant per lane is the defect this replaced, not the
#: fix: the roster is the only place a lane is declared, and a name list beside
#: it goes stale the first time somebody adds a lane and forgets the second
#: edit. This stem is the part every lane shares.
DRIVER_MUTEX_STEM = "CS_QUEUE_LOOP_DRIVER"
#: The BOX-WIDE guard's stem - see `worktree_mutex`. Deliberately carries no
#: repository token: it is the one name two different clones must agree on.
WORKTREE_MUTEX_STEM = "CS_LANE_WORKTREE"
#: Everything a mutex name may not carry past its namespace prefix, folded to
#: one replacement - see `_lane_token` on why a digest rides along behind it.
_MUTEX_UNSAFE = re.compile(r"[^A-Za-z0-9]")
#: Digest widths. Long enough that a collision is not a real risk, short enough
#: that an operator can read a mutex name in a log line.
_TOKEN_HEX = 12
_TOKEN_HEX_SHORT = 8
#: LANE-INDEPENDENT ON PURPOSE, and this is a ruling rather than an omission.
#: Every lane's driver appends to ONE ledger file, so the append has to be
#: serialised across lanes as well as across drivers. Deriving this name per
#: lane would let one lane's append interleave with another's inside a single
#: row - the unparseable half-line at 3am that the mutex exists to prevent.
LEDGER_MUTEX = "Global\\CS_QUEUE_LOOP_LEDGER"
#: The ledger append is a few hundred bytes; this is a wedged holder, not a busy
#: one. On timeout the append proceeds UNSERIALIZED and says so.
LEDGER_MUTEX_TIMEOUT_S = 5.0

OUTCOME_COMPLETED = "completed"
OUTCOME_TIMEOUT = "timeout_killed"
OUTCOME_LANE_HELD = "lane_held"
#: THE OTHER WAY AN ACQUIRE IS REFUSED, and its OWN word rather than a second
#: spelling of the one above. `ops/loop/lanes.py` answers `worktree_in_use` when
#: a lane asks for a tree ANOTHER lane is already running in, and
#: `_worktree_refusal`'s docstring rules why the two must not share a word: they
#: demand opposite operator actions. A held lane is waited out; an occupied tree
#: is repointed, and nothing about waiting will ever free it. Rendering both as
#: `lane_held` also named the occupying lane as the HOLDER of a lock it does not
#: hold, which sends whoever reads the row to the wrong lane.
OUTCOME_WORKTREE_IN_USE = "worktree_in_use"
OUTCOME_LAUNCH_FAILED = "launch_failed"
#: The kill was issued and the worker OUTLIVED it. Distinct from
#: OUTCOME_TIMEOUT because the two demand opposite responses: a killed worker
#: frees the worktree and the loop goes on, a surviving one does not.
OUTCOME_KILL_FAILED = "timeout_kill_failed"
#: A fault `run_cycle` did not convert into an outcome of its own.
OUTCOME_ERROR = "error"

#: THE OUTCOMES THAT COUNT AS A CYCLE HAVING HAPPENED - an ALLOWLIST, and the
#: allowlist is the mechanism. The invariant is "no sequence of outcomes in
#: which no cycle ever completes may run the full budget", and the two ways that
#: invariant has been broken were both the same shape: a DENYLIST of outcomes
#: that stop the night, and a new outcome nobody remembered to add to it. First
#: `launch_failed` fell through the denylist; then `lane_held` did, and an
#: alternating pair fell through both counters at once. Inverting the default
#: means a future `OUTCOME_*` constant is unproductive until somebody
#: deliberately says otherwise, so the hole cannot reopen by omission.
#:
#: `completed` is the only member, and `run_cycle` agrees with that by deriving
#: a record's `worker_ok` from the same equality.
#:
#: THE OUTCOME IS HALF THE TEST, NOT THE WHOLE ONE - see `_is_progress`. The
#: word says a worker ran to completion; it does not say the cycle shipped.
PRODUCTIVE_OUTCOMES = frozenset({OUTCOME_COMPLETED})

STOPPED_BY_MAX_CYCLES = "max_cycles"
STOPPED_BY_CONSECUTIVE_ERRORS = "consecutive_errors"
#: DISTINCT from STOPPED_BY_CONSECUTIVE_ERRORS, not a reuse of it. "The cycles
#: errored" and "the lane never started" demand opposite responses, and one word
#: for both is precisely how a night that ended at cycle 2 comes to look like a
#: night that ran all twelve.
STOPPED_BY_LAUNCH_FAILED = "consecutive_launch_failures"
STOPPED_BY_CI_RED = "ci_red"
STOPPED_BY_SUITE_RED = "suite_red"
#: THE BACKSTOP, and the only one of these that generalises. The two counters
#: above each name ONE repeating cause and are checked first, so a pure night of
#: refusals or a pure night of faults still gets its own word and its own number.
#: This one fires on a MIXED night that completes nothing - the pattern neither
#: specific counter can see, because each keeps resetting the other.
STOPPED_BY_NO_PROGRESS = "no_progress"

#: Process exit codes, distinct on purpose: a launcher and any future scheduled
#: task can only tell "ran the night" from "refused to start" by the number.
EXIT_OK = 0
EXIT_STOP_SENTINEL = 2  # zero cycles because a stop file was already there
EXIT_ALREADY_RUNNING = 3  # another driver already holds THIS LANE's driver mutex
EXIT_KILL_FAILED = 4  # a worker outlived its taskkill - worktree suspect
EXIT_CONSECUTIVE_ERRORS = 5  # the same fault repeated until the loop gave up
EXIT_CI_RED = 6  # a gating CI job went red on a pushed sha
EXIT_SUITE_RED = 7  # the driver's own local suite went red
EXIT_CONSECUTIVE_LAUNCH_FAILURES = 8  # the lane refused to start, over and over
EXIT_NO_PROGRESS = 9  # cycles happened and none of them shipped
EXIT_UNKNOWN_STOP = 10  # a stop word in no table - never read one as success


#: The row's own wording for an unreadable lane HEAD. A CONSTANT because
#: `detail` is the only thing that separates a worker which committed
#: nothing from a driver that could not look, and those send an operator to
#: two different files at 3am.
_UNREADABLE_HEAD = "the lane worktree HEAD could not be read - "


def _is_progress(record) -> bool:
    """Did this cycle produce a commit?

    ONE DEFINITION, read by the loop's counter AND by `main`'s exit code, so
    the two cannot drift into disagreeing about what a good cycle is.

    BOTH HALVES ARE LOAD-BEARING. The outcome word alone was the first defect:
    driven against a ref that never moved, twelve `completed` cycles ran the
    whole budget and exited 0 - a night that shipped nothing, observationally
    identical to the all-`lane_held` night this counter exists to stop.

    THE SECOND HALF USED TO BE `record["ok"]`, AND THAT WAS THE SECOND DEFECT.
    `ok` is false whenever the `ci` verdict is `no-push`, and `no-push` is
    decided by whether `origin/main` moved - which conflates WHERE the work
    landed with WHETHER there was work. `tools/headless-queue.md` instructs the
    worker to push the LANE BRANCH when its push to main is rejected, so a
    worker doing exactly what it is told never moves `origin/main`; an
    adversary driving that observed `cycles_run=3 stopped_by=no_progress` and
    exit 9 on a night doing real work. That is the session-81 shape, where
    CS-210 landed on `lane/queue` rather than on `main`. Killing such a night is
    worse than the bug the counter was written to fix.

    So the question is asked DIRECTLY instead: the driver already knows the lane
    worktree, because it grades the local suite there, and it reads that tree's
    HEAD before and after every cycle. The three cases an adversary drove all
    come out right:

    - the worker pushed to main -> HEAD advanced -> progress;
    - the worker pushed the LANE BRANCH -> HEAD advanced -> progress;
    - the worker completed having committed nothing -> HEAD stood still -> no
      progress, which is the case the previous round was right to catch.

    It also survives a FOREIGN push moving `origin/main` while this lane did
    nothing - `ok` reads that as progress that was never ours; this does not.

    NOTHING ABOUT `ci` OR `ok` CHANGED. A lane-branch night's rows still say
    `ci: no-push` and `ok: false`, because both are true, and the night still
    runs its whole budget and exits 0. A row and a night are different claims.

    Args:
        record: One cycle row, as `run_loop` writes it.

    Returns:
        True only for a cycle that completed AND advanced the lane HEAD.
    """
    return record.get("outcome") in PRODUCTIVE_OUTCOMES and bool(
        (record.get("commit") or {}).get("advanced")
    )


# ---------------------------------------------------------------------------
# Lazy module binds. See the docstring's last paragraph.
# ---------------------------------------------------------------------------


def _bind(dotted: str, private: str, filename: str):
    """Bind the SAME module object everything else uses - never a second copy.

    `lanes.py` carries process-global state: the ownership map that decides
    whether a release is ours. A file-path bind under a fresh name creates a
    SECOND module object with its OWN copy of that map, so a claim recorded in
    one is invisible to a release called on the other and the lane can never be
    freed. The dotted name is tried first because that is the canonical one; the
    file-path fallback exists only for callers with no package on `sys.path`
    (the detached launcher runs this by absolute path), and it reuses the same
    private name so the fallback still yields one object.

    THE PRIVATE NAME IS NOT ENOUGH, AND THAT IS CS-1000, MEASURED. Reusing one
    private name only keeps THIS module's own binds together. `lane_launcher.py`
    carries a fallback of its own under a DIFFERENT private name, so when the
    package route fails for both - which is every detached run, because
    `pythonw <repo>/ops/loop/queue_loop.py` puts `ops/loop` on `sys.path` and
    the repository root nowhere - each file loaded its own copy of `lanes.py`
    and the two ownership maps never met. Cycle 1's re-point landed in one copy
    and its release was refused by the other, so from cycle 2 on the launcher
    refused to re-point, KILLED each freshly spawned worker and the lane
    completed exactly one row per launch, twice over.

    So the loaded module is REGISTERED UNDER THE DOTTED NAME as well. That makes
    the fix independent of what anybody's private name happens to be:
    `importlib.import_module` consults `sys.modules` before it looks for a
    loader, so whichever file falls back FIRST publishes the one object and
    every later `import_module(dotted)` - in this file or any other - gets it.
    `setdefault`, never an assignment: a genuine package module already in
    `sys.modules` is the canonical one and must never be displaced by a
    file-path copy.
    """
    try:
        return importlib.import_module(dotted)
    except ImportError:
        pass
    if private in sys.modules:
        return sys.modules[private]
    spec = importlib.util.spec_from_file_location(private, _HERE / filename)
    if spec is None or spec.loader is None:  # pragma: no cover - unreachable
        raise ModuleNotFoundError(f"cannot load {filename} by path")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[private] = mod
    spec.loader.exec_module(mod)
    # AFTER a successful exec, so a half-executed module is never published
    # under the name every other importer will now trust.
    sys.modules.setdefault(dotted, mod)
    return mod


_LAZY = {
    "lanes": ("ops.loop.lanes", "cs_loop_lanes", "lanes.py"),
    "lane_launcher": ("ops.loop.lane_launcher", "cs_loop_lane_launcher", "lane_launcher.py"),
    "winmutex": ("ops.loop.winmutex", "cs_loop_winmutex", "winmutex.py"),
    "ration": ("ops.loop.ration", "cs_loop_ration", "ration.py"),
    # THE TWO THIS FILE USED TO NAME ONLY IN PROSE. `scope.py` computed which
    # rows a lane may take and `claims.py` recorded which row was in flight, and
    # nothing in the driver path imported either - so the only bridge from both
    # to the row a worker actually took was the worker's own transcription of
    # printed text. See `ClaimWatch` and the `scope` field of a cycle record.
    "scope": ("ops.loop.scope", "cs_loop_scope", "scope.py"),
    "claims": ("ops.loop.claims", "cs_loop_claims", "claims.py"),
    # CS-1104. The channel surface: a PURE READ of the main tree's
    # `moon_sync_inbox/`, carried into every cycle row as `inbox`. It never
    # acknowledges and never replies - see `_surface_inbox`.
    "inbox_surface": ("ops.loop.inbox_surface", "cs_loop_inbox_surface", "inbox_surface.py"),
}


def __getattr__(name: str):
    """Resolve every module named in `_LAZY` on first use (PEP 562).

    Binding them at import would make reading a constant out of this file
    require the whole lane to be on disk, and would make an import of the
    driver a side effect of importing anything that mentions it. Resolving here
    keeps the module importable on its own while still handing every caller ONE
    module object.

    This is NOT a mutable seam. A caller substituting a dependency does it by
    passing a keyword argument to `run_cycle` or `run_loop`, which is a
    deliberate act; nothing monkeypatches an attribute out from under a running
    driver.
    """
    spec = _LAZY.get(name)
    if spec is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    mod = _bind(*spec)
    globals()[name] = mod
    return mod


# ---------------------------------------------------------------------------
# Small helpers.
# ---------------------------------------------------------------------------


def _mod(name: str):
    """The bound module for `name`, from this module's own namespace first.

    `__getattr__` (PEP 562) is consulted by the interpreter ONLY for an
    attribute that is missing, so calling it directly - which the code below
    used to do - bypasses the very namespace it populates. That made the bind
    unoverridable: assigning `queue_loop.lane_launcher` had no effect on a call
    site that reached past it. Going through the namespace first restores the
    ordinary meaning of a module attribute, and costs one dict lookup.
    """
    found = globals().get(name)
    return __getattr__(name) if found is None else found


def _taskkill(pid) -> None:
    """Hard-kill a wedged worker AND its children. Never raises.

    `/T` is not decoration: the pid is the powershell WRAPPER and `claude` is
    its child, so killing only the wrapper would orphan a live worker inside the
    lane worktree while the very next cycle fires a second worker into the SAME
    directory.

    Failure is swallowed on purpose - the caller is already recording a timeout,
    and a kill that could throw would turn one bad cycle into a dead driver. The
    caller re-probes liveness afterwards, which is the only thing that can
    actually prove the kill took.

    (The PowerShell process-stopping cmdlet is banned by CLAUDE.md because it
    hangs the MCP pipe. It is not named here even to forbid it: the house-rules
    guard in tests/test_queue_loop.py scans this file's code lines for it and
    cannot tell advice from a call site.)
    """
    # RESOLVED FROM PATH, NEVER NAMED (CS-910). This spawns while the lane
    # worktree is the working directory of the very worker being killed, so a
    # bare name here is the measured local-code-execution vector at its most
    # reachable. An unresolvable taskkill leaves the worker alive, `_await_death`
    # reports the kill did not take, and the loop STOPS - which is the answer
    # that matters, because the alternative is firing a second worker into a
    # worktree that still has a live writer.
    killer = resolve_tool("taskkill")
    if killer is None:
        _emit(
            "queue-loop: taskkill could not be resolved on PATH - the worker "
            "was NOT killed and this cycle will be recorded as a failed kill"
        )
        return
    with contextlib.suppress(OSError, subprocess.SubprocessError):
        subprocess.run(
            [killer, "/F", "/T", "/PID", str(pid)],
            capture_output=True,
            timeout=20,
            check=False,
            creationflags=_NO_WINDOW,
        )


def _fault(exc: BaseException) -> str:
    """Name a fault WITHOUT rendering the exception object. Never its ``str()``.

    CLAUDE.md non-negotiable 12. ``str()`` on an OSError appends the path it
    failed on, and a path on this machine carries the Windows account name. Two
    of this module's five former call sites wrote that string into the JSONL
    LEDGER, which is durable and is exactly the file an operator quotes.

    ``strerror`` is the operating system's own message for the failure - "The
    system cannot find the file specified" - and carries no path. Anything with
    no ``strerror`` degrades to its type name, which is a real answer: it says
    what went wrong in kind without inventing detail.

    Nothing is lost for debugging. Every raise in this module chains its cause,
    so the full text still reaches a traceback; it is only kept out of the
    strings that get written down.

    A PER-TYPE ALLOWLIST, modelled on `tools/precommit_gate.py::safe_exc_text`,
    which is this project's worked answer to the same question. It is not
    IMPORTED from there: that module is the tier-0 gate, and a lane driver that
    could fail to start because a gate module failed to import would be trading
    one silence for another. The shape is copied and cited instead.

    NOT one strerror-shaped branch for everything. `strerror` is an OSError
    attribute, so a helper that reaches for it on any other type finds nothing -
    and if it then fell back to `str()` it would be the leak it was written to
    prevent. Several types that reach here have no strerror at all, and each
    leaks differently: `TimeoutExpired` renders the whole command line, and
    `CalledProcessError` renders an argv this driver builds from paths.

    A LAUNCH FAILURE'S MESSAGE IS STILL NEVER RENDERED HERE, even though the
    launcher sanitises its own. The guard's exemption is structural - a module
    may render whole an exception type IT defines, because it builds that
    message - and `LaneLaunchError` is defined one module over. Trusting a
    promise made in another file is exactly what the structural rule refuses,
    and three of the launcher's messages embed a path, so the refusal is not
    theoretical. `_launch_fault` below adds a machine-readable CODE to the type
    name, and it adds one only after checking that code against a literal tuple
    THIS file holds - so the added word is still one this module wrote down,
    which is what the structural rule actually asks for.
    """
    if isinstance(exc, OSError):
        return exc.strerror or type(exc).__name__
    if isinstance(exc, subprocess.TimeoutExpired):
        return f"{type(exc).__name__} after {exc.timeout} seconds"
    if isinstance(exc, subprocess.CalledProcessError):
        return f"{type(exc).__name__} exit {exc.returncode}"
    return type(exc).__name__


def _launch_fault(exc: BaseException) -> str:
    """Name a launch refusal by TYPE and, when it is knowable, by REASON.

    `_fault` alone answers "a lane did not start" and nothing about why, which
    is a row an operator cannot act on. The launcher carries a machine-readable
    `reason` for exactly this, but a reason is still a string built in another
    module, so it is NOT copied out on the launcher's word.

    THE SUBSTITUTION IS THE MECHANISM, not the validation. The incoming value
    is used only to LOOK UP an index into `_LAUNCH_REASONS`, a literal tuple in
    this file, and the string written into the row is the element found at that
    index - this module's own literal, never the caller's object. A code this
    module does not hold - a launcher running ahead of its driver, an injected
    fake, a path-shaped string - is DISCARDED, and the row degrades to the bare
    type name it carried before this function existed. `str(exc)` is never read
    (CLAUDE.md non-negotiable 12).

    VALIDATING BY VALUE AND THEN RENDERING THE OBJECT IS NOT THE SAME THING, and
    the difference is only invisible for an exact `str`. Two subclasses defeat
    it: one overriding `__eq__` to pass any membership test, and - needing no
    trickery at all - one whose DATA is honestly `unspecified` while its
    `__str__` returns a home path, because an f-string calls `__str__` on a
    subclass. Both were driven through this function and both put an
    account-bearing path into the durable JSONL row. Hence `type(reason) is str`
    rather than `isinstance`, AND the index substitution: either alone would
    close one attack and leave the other.

    No shipped raise site was ever affected - all twelve bind plain module
    constants - so this closes a promise that was nearly true rather than a leak
    that happened.

    Args:
        exc: The caught launch refusal. Any exception type; no attribute is
            assumed present.

    Returns:
        `"<TypeName>: <code>"` for a recognised code, `"<TypeName>"` otherwise.
        Never an empty string - a fault must still be NAMED.
    """
    named = _fault(exc)
    # `getattr` with a default, NOT `exc.reason`: the launch seam is injectable
    # and a fake that raises a plain RuntimeError must be recorded, not turned
    # into an AttributeError that ends the night.
    reason = getattr(exc, "reason", None)
    # EXACT `str`, not `isinstance`: a subclass can lie about its comparison or
    # about its rendering, and the row is a durable personal-data-bearing file.
    if type(reason) is not str or reason not in _LAUNCH_REASONS:
        return named
    # THE DRIVER'S OWN LITERAL, fetched by index. `reason` is not rendered.
    return f"{named}: {_LAUNCH_REASONS[_LAUNCH_REASONS.index(reason)]}"


#: THE REFUSAL WORDS THIS DRIVER ITSELF HOLDS, parallel to `_REFUSAL_OUTCOMES`.
#: The SAME rule as `_LAUNCH_REASONS` one seam over, for the same reason: the
#: dict comes from another module and the row it lands in is a durable
#: personal-data-bearing file, so an incoming word is used to LOOK UP an index
#: and the value written is this module's own literal at that index. A word this
#: driver does not hold - a `lanes.py` running ahead of it, an injected fake -
#: is DISCARDED and the row degrades to the generic refusal it already had.
_ACQUIRE_REFUSALS = ("lane_held", "worktree_in_use")
_REFUSAL_OUTCOMES = (OUTCOME_LANE_HELD, OUTCOME_WORKTREE_IN_USE)

#: What a holder outside the lane roster is called. A refusal's `holder` is read
#: off a LOCK FILE this driver did not write, so it is not this module's string.
UNKNOWN_HOLDER = "unknown"


def _refusal_outcome(refused: object) -> str:
    """Which fault an acquire refusal is, as one of THIS module's own words.

    The driver used to read only `ok`, `holder`, `pid` and `token`, so both
    refusals arrived as `lane_held` - a doc-versus-ship contradiction against
    `_worktree_refusal`'s own docstring, and a row that sent a reader to the
    wrong lane.

    EXACT `str`, not `isinstance`, and then an INDEX SUBSTITUTION. A `str`
    subclass can lie about its comparison or about its rendering - honest data,
    a `__str__` that returns a home path - and both were driven through the
    launch seam and both reached the durable row. A subclass is refused outright
    here rather than validated and rendered.

    Args:
        refused: The refusal dict's `refused` field. Any object.

    Returns:
        `OUTCOME_WORKTREE_IN_USE` for the collision, `OUTCOME_LANE_HELD` for a
        held lane AND for every word this module does not hold. Never invents an
        outcome, and never returns the caller's object.
    """
    if type(refused) is not str or refused not in _ACQUIRE_REFUSALS:
        return OUTCOME_LANE_HELD
    return _REFUSAL_OUTCOMES[_ACQUIRE_REFUSALS.index(refused)]


def _holder_name(holder: object) -> str:
    """The occupying lane's name, or `UNKNOWN_HOLDER`. Never the caller's object.

    `ops/loop/lanes.LANES` is the allowlist. A lock file whose `lane` field is
    path-shaped - an older build, a hand-edited file, an injected fake - would
    otherwise have gone into the row through an f-string, which is CLAUDE.md
    non-negotiable 3. The rostered case renders exactly as it always did, so the
    lane name an operator already reads off these rows is not erased.

    Args:
        holder: The refusal dict's `holder` field. Any object.

    Returns:
        A name from this repository's lane roster, or `UNKNOWN_HOLDER`.
    """
    if type(holder) is not str:
        return UNKNOWN_HOLDER
    # ANNOTATED, because `_mod` is deliberately untyped - see its docstring - so
    # without this the roster is `Any` and the substitution below silently stops
    # being a `str` guarantee at all.
    roster: tuple[str, ...] = tuple(str(name) for name in _mod("lanes").LANES)
    if holder not in roster:
        return UNKNOWN_HOLDER
    return roster[roster.index(holder)]


def _holder_pid(pid: object) -> int | None:
    """The holder's pid when it is honestly one, and None otherwise.

    Same surface, same rule: the value is copied out of a dict another module
    built and written into a durable row. A pid is an integer; anything else is
    a string this driver has no business rendering. `bool` is excluded because
    it is an `int` subclass and `True` is not a process.
    """
    return pid if type(pid) is int else None


def _emit(line: str) -> None:
    """One progress line, FLUSHED.

    The launcher runs this under `pythonw.exe` with stdout redirected to a file,
    and a redirected non-tty stdout is block-buffered - without the flush the
    log stays empty for the whole run and an operator tailing it cannot tell a
    working driver from a hung one.
    """
    print(line, flush=True)


def _repo_token() -> str:
    """A short, stable identity for THIS checkout, spelled as a digest.

    A NAMED MUTEX IS A MACHINE-WIDE OBJECT and several projects run on this box,
    so a name has to be unique to the checkout as well as to the lane. The
    identity is DIGESTED rather than spelled: a checkout under a home directory
    would otherwise write the Windows account name into an object any process
    can enumerate, which CLAUDE.md non-negotiable 3 forbids outright.

    The main tree is the identity even when the driver is started from a
    worktree - `lanes.REPO_ROOT` already resolves that indirection - so two
    drivers started from two worktrees of one checkout still exclude.

    Returns:
        The identity token.
    """
    root = os.path.normcase(os.path.normpath(str(_mod("lanes").REPO_ROOT)))
    return hashlib.sha256(root.encode("utf-8")).hexdigest()[:_TOKEN_HEX]


def _lane_token(lane: str) -> str:
    """One lane's half of a mutex name - readable, and INJECTIVE.

    A mutex name may not carry a backslash past its namespace prefix, so the
    lane is folded to an identifier-safe spelling. FOLDING ALONE IS A COLLAPSE
    RISK: every character the fold replaces maps to the same one, so a roster
    holding two lanes differing only in such a character would land both on a
    single name - the defect this item removes, arriving by the back door. The
    digest of the RAW lane is appended so distinct lanes stay distinct whatever
    the fold did.

    NO ROSTER CHECK HERE, deliberately. Refusing an unknown lane is the lock's
    ruling and it makes it in one place with one message; naming a mutex for a
    lane that will then be refused costs nothing and keeps this a pure function.

    Args:
        lane: The lane name.

    Returns:
        The lane's token.
    """
    text = str(lane)
    folded = _MUTEX_UNSAFE.sub("_", text)
    return f"{folded}_{hashlib.sha256(text.encode('utf-8')).hexdigest()[:_TOKEN_HEX_SHORT]}"


def driver_mutex(lane: str) -> str:
    """The name the driver of one lane is a singleton under.

    DERIVED, NEVER RESTATED. A hand-written constant per lane is the defect this
    replaced: the roster is the only place a lane is declared, and a second list
    beside it goes stale the first time somebody adds a lane and makes one edit.

    Args:
        lane: The lane being driven.

    Returns:
        The mutex name, in the machine-wide namespace.
    """
    return f"Global\\{DRIVER_MUTEX_STEM}_{_repo_token()}_{_lane_token(lane)}"


def worktree_mutex(worktree) -> str:
    """The BOX-WIDE guard over one working directory. NOT scoped to a checkout.

    THIS IS THE HALF THAT MUST NOT BE NARROWED, and it exists because narrowing
    the driver mutex per checkout opened a hole the old box-wide constant had
    closed by accident. Measured: two clones of this repository at different
    paths derive DIFFERENT driver mutexes and keep DISJOINT lock roots, while
    `lane_launcher.WORKTREE_BASE` resolves both to the SAME
    `cs-lane-<lane>` checkout on the same branch. Two workers in one working
    directory is the concurrent-index corruption class, and it is not
    recoverable by retrying.

    So the name is keyed on the WORKING DIRECTORY and on nothing else - no repo
    token, no lane. Whoever is about to write in that directory takes this,
    whichever clone, whichever lane, whichever branch they think they are on.
    The path is normalised and digested rather than spelled: a worktree base
    under a home directory would otherwise put the account name into an object
    any process on the box can enumerate.

    Args:
        worktree: The working directory the driver will write in.

    Returns:
        The mutex name, in the machine-wide namespace.
    """
    key = os.path.normcase(os.path.normpath(str(worktree)))
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()[:_TOKEN_HEX]
    return f"Global\\{WORKTREE_MUTEX_STEM}_{digest}"


@contextlib.contextmanager
def _driver_singleton(lane: str, worktree=None):
    """Hold BOTH run-length guards, or raise at once.

    ONE DRIVER PER LANE, not one per box: the lane lock stops two WORKERS, and
    the driver mutex stops two DRIVERS of the same lane in the same checkout,
    which the lock cannot see because a driver claims and releases it once per
    cycle and is otherwise idle.

    ONE DRIVER PER WORKING DIRECTORY, ACROSS CHECKOUTS. The second guard is the
    box-wide one and is taken INSIDE the first, so a refusal on either one is a
    refusal to run. Narrowing the driver mutex per lane and per checkout without
    it would let two clones fire two workers into one worktree - see
    `worktree_mutex`.

    `timeout=0` makes both a TEST rather than a wait. A second driver must exit
    at once with a distinct code; queueing it behind the first for six hours
    would start a run nobody asked for, at a time nobody chose.

    Args:
        lane: The lane being driven.
        worktree: The working directory, or None to resolve the lane's own. It
            is resolved HERE rather than in `main` so a caller injecting its own
            guard never touches the launcher.

    Yields:
        None, for the length of the run.
    """
    tree = _mod("lane_launcher").worktree_path(lane) if worktree is None else worktree
    winmutex = _mod("winmutex")
    with (
        winmutex.hold(driver_mutex(lane), timeout=0.0, log=_emit),
        winmutex.hold(worktree_mutex(tree), timeout=0.0, log=_emit),
    ):
        yield


def _ledger_lock():
    """Hold LEDGER_MUTEX for one append.

    No `log=` here, unlike the driver mutex: two extra lines per cycle would
    bury the one line per cycle an operator actually reads.
    """
    return _mod("winmutex").hold(LEDGER_MUTEX, timeout=LEDGER_MUTEX_TIMEOUT_S)


# ---------------------------------------------------------------------------
# FIX 2 - a verdict is a summary line AND an exit code.
# ---------------------------------------------------------------------------

#: pytest's own terminal summary, in every shape it actually emits: bare under
#: `-q`, `=`-padded otherwise, with or without the parenthesised duration.
#: Anchored on the trailing ` in <float>s` because that is the one part every
#: shape shares, and required to carry at least one outcome word so an ordinary
#: line of prose containing "in 1.0s" cannot pass for a verdict.
_OUTCOME_WORDS = (
    "passed",
    "failed",
    "error",
    "errors",
    "skipped",
    "xfailed",
    "xpassed",
    "deselected",
    "warning",
    "warnings",
    "no tests ran",
)
_SUMMARY_RE = re.compile(r"\bin\s+\d+(?:\.\d+)?s\b")


def summarize_pytest(stdout: str, exit_code: int) -> dict:
    """Grade a pytest run from its output AND its exit code, never one alone.

    THE DEFECT THIS CLOSES. A crashed parallel run leaves no summary line at
    all: the workers die, the log stops mid-progress, and nothing in it says
    FAILED - so `grep -c FAILED` returns 0, which is indistinguishable from a
    green run. A grader that reads only the log accepts it. A grader that reads
    only the exit code accepts a run that never started.

    Args:
        stdout: The run's captured output. May be truncated; that is the point.
        exit_code: The process's real exit status.

    Returns:
        A dict carrying `summary` (the VERBATIM last summary line, or None),
        `exit_code`, `truncated` (no summary line was found) and `ok`, which is
        True only when a line WAS parsed and the exit code is 0.
    """
    summary = None
    for line in str(stdout or "").splitlines():
        stripped = line.strip()
        if not _SUMMARY_RE.search(stripped):
            continue
        lowered = stripped.lower()
        if not any(word in lowered for word in _OUTCOME_WORDS):
            continue
        summary = stripped
    try:
        code = int(exit_code)
    except (TypeError, ValueError):
        code = -1
    return {
        "summary": summary,
        "exit_code": code,
        "truncated": summary is None,
        "ok": summary is not None and code == 0,
    }


def _default_suite_runner(argv, cwd=None):
    """Run the suite in a subprocess and return (exit_code, combined output).

    Split out as the injection seam so no test ever runs a real suite inside a
    suite. Output is merged because a crash writes to stderr and the summary
    line to stdout, and a truncation check needs both in one stream.
    """
    proc = subprocess.run(
        list(argv),
        capture_output=True,
        text=True,
        cwd=None if cwd is None else str(cwd),
        timeout=DEFAULT_SUITE_TIMEOUT_S,
        check=False,
        creationflags=_NO_WINDOW,
    )
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def run_local_suite(*, argv=None, runner=None, cwd=None, monotonic=time.monotonic) -> dict:
    """Run the full local suite and grade it. NEVER raises.

    This is the driver-owned wait for a box with no `gh` credentials, and it is
    the shape used to prove one cycle end to end without a CI round trip.

    IT RUNS IN THE LANE WORKTREE, NOT IN THE DRIVER'S OWN TREE, and that is a
    correctness requirement rather than a convenience. The worker commits and
    pushes from the lane worktree; the driver's tree has not pulled and is
    whatever it was when the night started. A suite run there would grade a tree
    NOBODY pushed and report it as the cycle's acceptance - a green that is
    about the wrong commit is worse than no green at all, because it is
    indistinguishable from a real one in the ledger.

    Args:
        argv: The command to run. Defaults to the whole suite under this
            interpreter, with `tests` named explicitly - never a bare recursive
            run from a repo root (CONVENTIONS.md section 7.1).
        runner: `(argv, cwd) -> (exit_code, output)`. The injection seam.
        cwd: WHICH TREE is graded. The caller passes the lane worktree.
        monotonic: Deadline clock. Never wall time.

    Returns:
        The verdict from `summarize_pytest`, plus `argv`, `cwd`, `duration_s`
        and `detail`. A runner that explodes yields `ok=False` with the reason
        in `detail` - one cycle's verdict is lost, never the night.
    """
    argv = list(LOCAL_SUITE_ARGV if argv is None else argv)
    runner = _default_suite_runner if runner is None else runner
    started = monotonic()
    try:
        code, out = runner(argv, cwd)
    except (OSError, subprocess.SubprocessError) as exc:
        return {
            "summary": None,
            "exit_code": None,
            "truncated": True,
            "ok": False,
            "argv": argv,
            "cwd": str(cwd or ""),
            "duration_s": round(monotonic() - started, 1),
            "detail": _fault(exc)[:400],
        }
    verdict = summarize_pytest(out, code)
    verdict.update(
        {
            "argv": argv,
            "cwd": str(cwd or ""),
            "duration_s": round(monotonic() - started, 1),
            "detail": ""
            if verdict["ok"]
            else (
                "no summary line - the run was truncated or crashed"
                if verdict["truncated"]
                else f"exit {verdict['exit_code']}"
            ),
        }
    )
    return verdict


def suite_ration(**kwargs):
    """The default ration around the local suite step - see `ops/loop/ration.py`.

    A THIN ADAPTER, deliberately. It exists so `run_suite_step` has ONE name to
    default to and so a caller can substitute the whole ration with a keyword
    argument, which is how every other dependency in this file is replaced. It
    holds no policy of its own: the ceiling and the poll are passed in by
    `run_suite_step` from the two constants above.

    Args:
        **kwargs: Passed through to `ration.hold_suite_slot`.

    Returns:
        The context manager that holds the slot for the block.
    """
    return _mod("ration").hold_suite_slot(**kwargs)


#: What `record["ration"]` says on a cycle that ran no suite of its own. WRITTEN
#: RATHER THAN OMITTED, and that is the whole point of it: with `--local-suite`
#: off - which is the driver's default and what `launch_queue_loop.ps1` produces
#: unless asked otherwise - the ration is entered zero times per cycle, and an
#: ABSENT key made that indistinguishable from a cycle it covered. A reader can
#: now count the nights this lane rationed nothing.
RATION_NO_SUITE = MappingProxyType(
    {
        "suite_ran": False,
        "rationed": True,
        "holder": None,
        "detail": (
            "this cycle ran no driver suite, so there was nothing for the ration to hold;"
            " the worker's own runs and the pre-push hook's are outside it either way"
        ),
    }
)


def ration_fact(claim) -> dict:
    """What the ration did for one suite step, as a field of the cycle record.

    A CLAIM THAT IS NOT `ok` IS THE FALL-THROUGH, not an error: `hold_suite_slot`
    yields the refusal it overran when its ceiling expires, and the block runs
    anyway because a ration that refuses turns a slow night into a dead one. The
    price of proceeding is that somebody has to be able to SEE it afterwards,
    and a log line cannot be that somebody - the driver's stdout file is
    truncated at every launch.

    TOTAL BY CONSTRUCTION. A ration seam that yields None, or anything without an
    `ok`, is read as NOT rationed rather than raising. A substituted ration that
    says nothing about itself has told us nothing, and nothing is not a pass.

    Args:
        claim: Whatever the ration's context manager yielded.

    Returns:
        The `suite_ran`, `rationed`, `holder` and `detail` fact.
    """
    held = bool(claim.get("ok")) if isinstance(claim, dict) else False
    holder = claim.get("pid") if isinstance(claim, dict) else None
    return {
        "suite_ran": True,
        "rationed": held,
        "holder": None if held else holder,
        "detail": ""
        if held
        else (
            "the ration was still held when this driver's ceiling expired, so the suite"
            f" ran beside another one - the holder was pid {holder}. The summary line"
            " below is a measurement of a contended box, not of this tree"
        ),
    }


def run_suite_step(  # noqa: PLR0913 - see THE SEAMS ARE THE POINT
    record,
    *,
    lane,
    worktree,
    run_id,
    suite,
    ration=None,
    root=None,
    ceiling_s=None,
    sleep=time.sleep,
    monotonic=time.monotonic,
    emit=_emit,
) -> None:
    """Run one cycle's local suite INSIDE the ration and record its verdict.

    A SEPARATE FUNCTION RATHER THAN THREE LINES IN THE LOOP, and the reason is
    what can be graded. The ration is only worth anything if the suite step is
    actually inside it, and a wiring arm that had to drive a whole night to
    observe that would grade the loop instead. Named here, the property is one
    call away: an arm can watch the slot from inside the injected suite.

    THE WAIT LIVES HERE, WITH EVERY OTHER WAIT THIS DRIVER OWNS. The driver
    sleeps behind another lane's suite; the worker never blocks on anything, and
    the worker's own suite runs - inside its iteration loop, and inside the
    frozen pre-push hook - are outside this ration and are not claimed to be in
    it.

    THE UNRATIONED FALL-THROUGH REACHES THE RECORD, NOT ONLY THE LOG. It used to
    reach only `emit`, whose stdout file `launch_queue_loop.ps1` truncates at
    every launch - so the row an operator reads at 3am was byte-identical to a
    row whose suite ran alone, which is the precise harm `ration.py`'s own
    docstring names. `record["ration"]` is therefore written on EVERY cycle,
    including the cycles where no suite ran at all, and a suite that ran
    unrationed makes the row not ok. A suite measured while another suite was
    running is not evidence, for the same reason a suite graded in the wrong
    tree is not: both produce a summary line nobody can act on.

    HOLDING THE SLOT ACROSS THE WHOLE WORKER CYCLE WAS WEIGHED AND REJECTED, and
    the arithmetic is the reason rather than a preference. It is the only way
    this driver could cover the worker's two runs, because the driver reaches a
    worker by pid and by nothing else. The hook's own header records 320s for the
    xdist suite on a real push; a cycle is bounded at `DEFAULT_CYCLE_TIMEOUT_S`
    and legitimately spends most of itself on work that forks nothing. Holding
    across it would serialise up to that bound to protect 320s - a ratio of about
    45 to 1 at the ceiling - and would make two lanes strictly one lane for the
    whole night, undoing CS-992 without its authors present. The gap is recorded
    instead, and closing it properly means `.githooks/pre-push` taking this same
    slot, which is a FROZEN file and needs a grant.

    THE SUITE RUNS IN THE LANE WORKTREE, never this tree - see `run_local_suite`.
    That resolution stays here rather than moving into the ration, because the
    ration is about WHETHER the step may run and the worktree is about WHICH
    tree it grades, and one function answering both would be the seam mistake
    this package keeps writing down.

    Args:
        record: The cycle record to write `suite` and `ration` into.
        lane: The lane, for the worktree resolution and the ration's holder.
        worktree: The caller's worktree override, or None.
        run_id: This cycle's identifier, so a ration log line joins to a row.
        suite: The suite seam, `run_local_suite`'s shape.
        ration: The ration seam, or None for `suite_ration`.
        root: The slot root, or None for the ration's own default.
        ceiling_s: How long to wait before running unrationed, or None for
            `SUITE_RATION_CEILING_S`. An arm passes 0 to reach the fall-through
            without spending the night's real budget getting there.
        sleep: The wait, injected so an arm never has to spend real time.
        monotonic: Deadline clock. Never wall time.
        emit: The log sink, so an unrationed step is findable at 3am.
    """
    ration = suite_ration if ration is None else ration
    with ration(
        holder=lane,
        run_id=run_id,
        root=root,
        ceiling_s=SUITE_RATION_CEILING_S if ceiling_s is None else ceiling_s,
        poll_s=SUITE_RATION_POLL_S,
        sleep=sleep,
        monotonic=monotonic,
        emit=emit,
    ) as claim:
        record["suite"] = suite(cwd=lane_worktree(lane, worktree), monotonic=monotonic)
        # INSIDE the block, so a ration whose context manager never yielded a
        # claim cannot leave the field behind from a previous cycle.
        record["ration"] = ration_fact(claim)
    if not record["ration"]["rationed"]:
        # THE VERDICT IS DOWNGRADED, not merely annotated. `suite["ok"]` keeps
        # pytest's own answer - the summary line and the exit code are still
        # verbatim and still reproducible - and the row's roll-up is what
        # refuses to call the cycle good news. Overwriting `suite["ok"]` would
        # destroy the distinction between a red suite and an unmeasurable one.
        emit(f"queue-loop: cycle {run_id} ran its suite UNRATIONED - {record['ration']['detail']}")


# ---------------------------------------------------------------------------
# The scope binding. Which row this lane WAS ALLOWED to work, which row it
# ACTUALLY held, and the comparison of the two - see `ops/loop/scope.py`.
# ---------------------------------------------------------------------------

#: How much older than this cycle a claim record may read and still be
#: attributed to it. It covers the ordinary skew between the `time.time()` the
#: store stamps a record with and the reading this loop took at the top of the
#: cycle; it is NOT a grace period for a claim from a previous cycle, which is
#: hours old and is excluded by a window this size.
CLAIM_WINDOW_SLACK_S = 30.0

#: The console token a cycle whose row did not bind adds to its line. On the
#: line as well as in the row, for the reason `ration=UNRATIONED` is: an
#: operator tailing a night reads it by counting cycles down the left margin,
#: and a cycle nobody authorised has to be legible there too. The ROW is still
#: the acceptance - this file's stdout is truncated at every launch.
SCOPE_NOTE = "scope=UNBOUND"


def _noop() -> None:
    """The default observer: a driver that was given nothing to watch."""


class ClaimWatch:
    """Which rows this lane HELD while its worker ran, sampled by the driver.

    SAMPLED DURING THE CYCLE, NEVER READ AFTER IT, AND THAT IS THE WHOLE DESIGN.
    `tools/headless-queue.md` section 11 tells a worker to RELEASE its claim at
    the wrap, and a well-behaved worker does exactly that - so by the time the
    cycle record is written the store is empty and a post-cycle read would learn
    nothing from a compliant cycle and everything from a crashed one, which is
    precisely backwards. `run_cycle` therefore calls :meth:`sample` on its poll
    path, which is the one place in this driver that is awake while the worker
    is.

    THE LANE IS THE DISAMBIGUATOR, AND IT IS WHY THE CLAIM STORE IS THE SOURCE
    RATHER THAN THE COMMITS. Reading the ids off the commits in the lane
    worktree was weighed and rejected: a worker fast-forwards its tree at the
    top of a cycle, so a sibling lane's commits - naming rows outside THIS
    lane's subject, entirely legitimately - arrive inside the same revision
    range and would be read as this cycle's work. A claim record carries the
    lane that wrote it and cannot be confused that way.

    NOTHING HERE INVENTS A ROOT. `claims.DEFAULT_ROOT` resolves the MAIN
    checkout through the `.git`-file indirection, which is the only spelling
    every lane's worker agrees on - a store rooted at a checkout is a different
    directory in every worktree, which is how two lanes were measured both
    holding one row. The driver runs from the main tree, so it would get away
    with a checkout-local root and the worker would not; passing the root
    through as None keeps ONE answer rather than two that happen to agree.

    NEVER RAISES. It runs inside `run_cycle`'s wait loop, where a fault would
    escape the loop entirely and take the driver down with no ledger row, no
    stop word and no exit code for the launcher to read. A store it could not
    read is COUNTED instead, so an unreadable store and a genuinely empty one
    are different rows.
    """

    def __init__(
        self,
        lane: str,
        *,
        started_at: float,
        states=None,
        root=None,
        clock=time.time,
        slack_s: float = CLAIM_WINDOW_SLACK_S,
    ) -> None:
        """Watch one lane's claims for the life of one cycle.

        Args:
            lane: The lane whose records count. A record written by any other
                lane is somebody else's row and is never this cycle's.
            started_at: The cycle's own start, on the same wall clock the store
                stamps its records with.
            states: The store reader, or None for `claims.claim_states`.
            root: The claim root. None is the production answer and means the
                store resolves its own - see the class docstring. A path here is
                a test seam and nothing else.
            clock: Wall clock, injected so an arm never has to sleep.
            slack_s: The window's tolerance.
        """
        self.lane = str(lane)
        self.root = root
        self.started_at = float(started_at)
        self.slack_s = float(slack_s)
        #: How many times the store was read, and how many of those faulted.
        #: DIAGNOSTIC ONLY - nothing grades a cycle on either number, because a
        #: threshold over a count is the CS-988 shape this item exists to avoid.
        #: Zero samples means the driver never looked, which a reader has to be
        #: able to tell from a store that was empty every time it did.
        self.samples = 0
        self.faults = 0
        self.fault_detail = ""
        self._states = states
        self._clock = clock
        self._rows: set[str] = set()

    def sample(self) -> tuple[str, ...]:
        """Read the store once and remember any row this lane holds.

        Returns:
            Every row seen so far, which is what :meth:`rows` answers.
        """
        self.samples += 1
        try:
            reader = _mod("claims").claim_states if self._states is None else self._states
            readings = reader(self.root, None) or {}
            # AGAINST THIS CYCLE'S OWN ELAPSED TIME. A record older than the
            # cycle is a record from a cycle that is over - a lane that died
            # holding its row leaves exactly that - and attributing it here
            # would refuse a lane over a row it is not working.
            window = max(0.0, float(self._clock()) - self.started_at) + self.slack_s
            for reading in readings.values():
                if str(reading.get("lane") or "") != self.lane:
                    continue
                row = str(reading.get("row") or "").strip()
                age = reading.get("age_s")
                # A record whose age cannot be established is not attributed.
                # It cannot be placed in time, and a refusal has to be able to
                # say WHEN the row was taken or it cannot be acted on.
                if not row or age is None:
                    continue
                if float(age) <= window:
                    self._rows.add(row.upper())
        except Exception as exc:  # see the class docstring's last paragraph
            self.faults += 1
            if not self.fault_detail:
                # `_fault`, never str(exc): an OSError's message carries the
                # path it failed on - CLAUDE.md non-negotiable 12.
                self.fault_detail = _fault(exc)[:200]
        return self.rows()

    def rows(self) -> tuple[str, ...]:
        """Every row this lane was seen holding, sorted.

        Returns:
            The row ids.
        """
        return tuple(sorted(self._rows))


def permit_for_lane(lane: str):
    """What this lane may take right now, read from the docs this tree carries.

    THE DEFAULT `permit` SEAM, and a one-line bind rather than a call site so
    `run_loop` does not have to resolve `scope` itself. Read DRIVER-SIDE: this
    driver runs from the main checkout, which is the tree whose `ROADMAP.md`,
    `docs/GATED.md` and `docs/LEDGER.md` say what is open, and `scope.py`
    deliberately reads the checkout it lives in.

    Args:
        lane: The lane name.

    Returns:
        What `scope.lane_permit` answered. It never raises. UNANNOTATED, like
        every other `_mod` caller here: the lazy bind hands back an untyped
        module, and declaring a return type would make this line the one place
        the repo-wide gate reports an `Any` it cannot see through.
    """
    return _mod("scope").lane_permit(lane)


# ---------------------------------------------------------------------------
# Stop sentinels.
# ---------------------------------------------------------------------------


def stop_path_for(name, control_dir=None):
    """The full path of the sentinel called `name`, or None if it is not one.

    Derived from STOP_RELPATHS rather than by re-probing the disk, so `main`
    can still name the file that stopped a run in the race where someone
    removes it a moment later.
    """
    root = CONTROL if control_dir is None else Path(control_dir)
    for rel in STOP_RELPATHS:
        if Path(rel).name == name:
            return root / rel
    return None


def stop_reason(control_dir=None) -> str | None:
    """The NAME of whichever stop sentinel exists, or None.

    Checked in STOP_RELPATHS order, so the global halt is reported ahead of the
    lane-local one when both are present.
    """
    root = CONTROL if control_dir is None else Path(control_dir)
    for rel in STOP_RELPATHS:
        if (root / rel).exists():
            return Path(rel).name
    return None


# ---------------------------------------------------------------------------
# The ledger.
# ---------------------------------------------------------------------------


def _append_line(path: Path, line: str) -> None:
    r"""The raw O_APPEND write.

    `newline="\n"` so the ledger stays LF on Windows. Text mode would otherwise
    translate to CRLF, which silently changes byte counts and makes this file
    disagree with every other JSONL in the tree.
    """
    with path.open("a", encoding="utf-8", newline="\n") as fh:
        fh.write(line)


def append_record(record: dict, cycle_log=None, *, hold=None, emit=None) -> Path:
    """Append one cycle record to the JSONL ledger. Creates its dir on demand.

    Lazily, because `--reports-dir` may name a directory that does not exist yet
    and because import time must stay side-effect free.

    An O_APPEND write of one short line is close to atomic already, but "close
    to" is what interleaves two half-lines into an unparseable row at 3am, and
    the ledger is the only durable record of the night.

    Args:
        record: The row. Serialised with sorted keys so two rows diff cleanly.
        cycle_log: Where to write. Defaults to CYCLE_LOG.
        hold: Zero-argument callable returning the serialising context manager.
            The seam exists so a test can prove the write happens INSIDE the
            critical section without touching a real OS mutex.
        emit: Where the fail-open warning goes.

    Returns:
        The path written.
    """
    path = Path(CYCLE_LOG if cycle_log is None else cycle_log)
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(record, sort_keys=True) + "\n"
    hold = _ledger_lock if hold is None else hold
    emit = _emit if emit is None else emit
    try:
        with hold():
            _append_line(path, line)
    except _mod("winmutex").MutexTimeout:
        # FAIL OPEN, LOUDLY. A dropped row loses the only evidence of a cycle,
        # and this is called from `run_loop` OUTSIDE its try, so raising here
        # would end the night over a lock nobody else should be holding.
        emit(
            f"queue-loop: UNSERIALIZED ledger append - {LEDGER_MUTEX} not free "
            f"within {LEDGER_MUTEX_TIMEOUT_S}s; appending anyway"
        )
        _append_line(path, line)
    return path


# ---------------------------------------------------------------------------
# Talking to `gh`.
# ---------------------------------------------------------------------------


def _gh(args) -> tuple[int, str]:
    """The ONE `gh` call site. Returns (returncode, text) and never raises.

    Every CI question goes through here so the timeout, the console-window flag
    and the "a missing gh is an exit code, not a traceback" contract are set
    once. It is also the seam every test injects: a suite that could reach the
    real `gh` would fire a real CI run against the live repo from a unit test.

    On failure the text is stderr FIRST, because that is where `gh` puts the
    reason while stdout is usually empty; both are returned because which one
    carries the message varies by subcommand.
    """
    exe = resolve_tool("gh")
    if exe is None:
        # The same shape a missing `gh` already produced, and the same verdict:
        # `unavailable`, so a night with no CI evidence never reads as green.
        return 127, "gh could not be resolved from PATH"
    argv = [exe, *[str(a) for a in args]]
    try:
        proc = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            timeout=GH_TIMEOUT_S,
            check=False,
            creationflags=_NO_WINDOW,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        # 127 is "command not found", the common case here (no gh on PATH under
        # a detached pythonw) and it reads correctly in a log.
        return 127, _fault(exc)
    if proc.returncode != 0:
        return proc.returncode, ((proc.stderr or "") + (proc.stdout or "")).strip()
    return 0, proc.stdout or ""


def remote_head_sha(ref: str = CI_REF) -> str | None:
    r"""The sha `origin/<ref>` points at right now, or None. Never raises.

    `git ls-remote`, not `git rev-parse`, for two independent reasons. The
    driver runs in the MAIN tree while the worker commits and pushes from
    `C:\cs-worktrees\cs-lane-queue`, so this tree's own HEAD is not what was
    pushed; and a local `origin/main` ref is only as fresh as the last fetch,
    which nothing in this loop performs. `ls-remote` asks the remote and mutates
    NOTHING - no fetch, no index, no reflog - which matters because the driver
    must never write into a tree a worker may be using.

    None on every failure. The caller turns that into an `unavailable` verdict
    rather than a skipped cycle: a night whose CI evidence is missing must not
    read like a night of greens.
    """
    exe = resolve_tool("git")
    if exe is None:
        return None
    try:
        proc = subprocess.run(
            [exe, "-C", str(_mod("lanes").REPO_ROOT), "ls-remote", "origin", "refs/heads/" + ref],
            capture_output=True,
            text=True,
            timeout=GH_TIMEOUT_S,
            check=False,
            creationflags=_NO_WINDOW,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if proc.returncode != 0:
        return None
    first = (proc.stdout or "").strip().split("\n", 1)[0]
    parts = first.split()
    return parts[0] if parts else None


def local_head_sha(cwd) -> str | None:
    """The sha the LANE WORKTREE's own HEAD points at, or None. Never raises.

    THIS IS NOT `remote_head_sha`, AND THE DIFFERENCE IS THE WHOLE REPAIR.
    That one asks where `origin/main` points, which answers "where did the work
    land". This one asks what the tree the worker commits into points at, which
    answers "was there any work". The two were conflated, and a worker doing
    exactly what `tools/headless-queue.md` tells it to do - push the LANE
    BRANCH when the push to main is rejected - was scored as having done
    nothing three cycles running.

    `rev-parse HEAD`, and it MUTATES NOTHING: no fetch, no index read that
    writes, no reflog. The driver must never write into a tree a worker may be
    using, which rules out anything that would take the index lock.

    None on every failure, which the caller turns into "not a commit" - see
    the default stated at the `commit` record in `run_loop`.

    Args:
        cwd: The worktree to ask. A missing one is a None, not a raise.

    Returns:
        The 40-character sha, or None.
    """
    exe = resolve_tool("git")
    if exe is None or cwd is None:
        return None
    try:
        proc = subprocess.run(
            [exe, "-C", str(cwd), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=GH_TIMEOUT_S,
            check=False,
            creationflags=_NO_WINDOW,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if proc.returncode != 0:
        return None
    return (proc.stdout or "").strip() or None


def lane_worktree(lane: str, worktree):
    """The ONE answer to "which tree is this lane's", for every caller here.

    The local suite is graded in it and the lane HEAD is read from it, and the
    two must never be able to disagree about which directory they mean - a
    suite graded in one tree beside a commit counted in another is a pair of
    correct facts that together say nothing.

    Raises whatever `worktree_path` raises, exactly as the suite call site
    already did. The progress read wraps it; see `_lane_head`.

    Args:
        lane: The lane name.
        worktree: The caller's override, or None to resolve the lane's own.

    Returns:
        The worktree path.
    """
    return worktree if worktree is not None else _mod("lane_launcher").worktree_path(lane)


def _lane_head(tree_sha, lane, worktree):
    """(sha, why). NEVER RAISES, and that is a hard requirement, not a courtesy.

    `run_loop` catches around `run_cycle` and nowhere else, so a fault raised
    here would escape the loop entirely and take the driver down with it - no
    ledger row, no stop word, no exit code for the launcher to read. A night
    the driver cannot grade must still be a night that ENDS, on its own
    counter, with its reason written down.

    `_fault`, not `str(exc)`: CLAUDE.md non-negotiable 12. The exception
    message on an OSError appends the path it failed on, and a lane worktree
    path is not something this row may carry.

    Args:
        tree_sha: The seam that reads a worktree's HEAD.
        lane: The lane name.
        worktree: The caller's worktree override, or None.

    Returns:
        (sha_or_None, why) - `why` is "" on success.
    """
    try:
        return tree_sha(lane_worktree(lane, worktree)), ""
    except Exception as exc:  # see the docstring's first line
        return None, _fault(exc)[:200]


def _gh_json(gh, args):
    """(parsed, None) or (None, why). Every shape surprise is a `why`.

    A missing field, a payload that is a list where an object was expected, a
    non-zero exit and unparseable output are all the SAME class - the CLI did
    not answer the question - and all of them must degrade to `unavailable`
    rather than raise, so they are normalised at the one place that talks to it.
    """
    rc, out = gh(args)
    rendered = " ".join(str(a) for a in args)
    if rc != 0:
        return None, f"gh {rendered} exited {rc}: {str(out).strip()[:300]}"
    try:
        return json.loads(out), None
    except (TypeError, ValueError) as exc:
        return None, f"gh {rendered} returned unparseable JSON: {_fault(exc)}"


def _run_list(gh, spec: CiSpec):
    """Recent runs of `spec.workflow`, newest first, as `gh` orders them."""
    data, err = _gh_json(
        gh,
        [
            "run",
            "list",
            "--workflow",
            spec.workflow,
            "--limit",
            str(CI_RUN_LIST_LIMIT),
            "--json",
            "databaseId,headSha,status,conclusion,event",
        ],
    )
    if err:
        return [], err
    if not isinstance(data, list):
        return [], (f"gh run list returned {type(data).__name__}, expected a list of runs")
    return [row for row in data if isinstance(row, dict)], None


def _pick_run(rows, sha):
    """The best existing run for `sha`, preferring a dispatch over a push.

    `event_name` is part of a concurrency group, so a `workflow_dispatch` run
    sits in a DIFFERENT group from every push and a later push cannot cancel it.
    A push run has no such protection. Rows arrive newest-first, so the first
    match within an event is the freshest.
    """
    matches = [row for row in rows if str(row.get("headSha") or "") == str(sha)]
    for event in ("workflow_dispatch", "push"):
        for row in matches:
            if str(row.get("event") or "") == event:
                return row
    return matches[0] if matches else None


def _trigger_run(gh, spec: CiSpec, sha, seen, *, sleep):
    """Fire one dispatch and return the run it created. (row, None) or (None, why).

    NEW-ID identification, not a timestamp comparison. `seen` holds every run id
    already accounted for, so "the run the trigger created" is "the newest run
    whose id we have not seen" - which needs no clock, no timezone and no ISO
    parsing, and cannot mistake the first dispatch for the second when a
    cancelled run is re-dispatched.

    An exact `headSha` match wins when one is offered. Otherwise the newest
    fresh dispatch run is accepted even though its head is a DESCENDANT of the
    sha asked about: `gh workflow run` takes a branch ref, so it builds `main`
    as of trigger time and a later sha subsumes an earlier one. What is NOT done
    is claim descent that was not proven - the run's own headSha is returned and
    recorded, so the ledger cites the tree CI actually built.
    """
    rc, out = gh(["workflow", "run", spec.workflow, "--ref", CI_REF])
    if rc != 0:
        return None, (f"gh workflow run {spec.workflow} exited {rc}: {str(out).strip()[:300]}")
    why = (
        f"no new {spec.workflow} run appeared within "
        f"{CI_TRIGGER_TRIES * CI_TRIGGER_WAIT_S}s of the dispatch"
    )
    for _ in range(CI_TRIGGER_TRIES):
        sleep(CI_TRIGGER_WAIT_S)
        rows, err = _run_list(gh, spec)
        if err:
            why = err
            continue
        fresh = [row for row in rows if row.get("databaseId") not in seen]
        exact = [row for row in fresh if str(row.get("headSha") or "") == str(sha)]
        dispatched = [row for row in fresh if str(row.get("event") or "") == "workflow_dispatch"]
        picked = (exact or dispatched or [None])[0]
        if picked is not None:
            seen.add(picked.get("databaseId"))
            return picked, None
    return None, why


def _matches(name: str, matchers) -> bool:
    """A matcher matches a job name by equality or by prefix.

    The prefix form is what covers a matrix: `full suite (` is one declared job
    that becomes `full suite (ubuntu-latest)` and `full suite (windows-latest)`,
    and both must be graded.
    """
    return any(name == m or name.startswith(m) for m in matchers)


def grade_ci_jobs(spec: CiSpec, data) -> tuple[str, str]:  # noqa: PLR0911
    """Decide whether one workflow run passed, from its JOBS.

    NEVER the run conclusion. Two independent reasons: a run's conclusion can be
    green while the job that matters was skipped, and `gh run watch
    --exit-status` returns 0 on a CANCELLED run. The only thing that means "the
    tree passed" is every graded job's own conclusion.

    THE POOLED-GUARD RULE. Each required matcher must match at least one job,
    and EVERY job it matched must be `success`. A grader that asked "did any leg
    pass" would let the weakest member go unmeasured while its acceptance clause
    still read green.

    A required matcher that matches NOTHING is `unavailable` - an answer about
    the TOOL, not about the world. A workflow renamed out from under this driver
    must never read as a pass.

    Args:
        spec: Which workflow, and its required and advisory job matchers.
        data: The parsed `gh run view --json jobs` payload.

    Returns:
        (verdict, detail). The detail names the job that decided it.
    """
    jobs = data.get("jobs") if isinstance(data, dict) else None
    if not isinstance(jobs, list):
        return CI_UNAVAILABLE, "the run carried no jobs list"
    seen = [
        (str(row.get("name") or ""), str(row.get("conclusion") or "").strip().lower())
        for row in jobs
        if isinstance(row, dict)
    ]
    if not seen:
        return CI_UNAVAILABLE, "the run carried an empty jobs list"

    # Required-and-missing FIRST: a workflow that does not carry the job this
    # driver grades has not answered the question, whatever else it did.
    for matcher in spec.required:
        if not [name for name, _ in seen if _matches(name, (matcher,))]:
            return CI_UNAVAILABLE, (
                f"{spec.workflow} carried no job matching {matcher!r} - the "
                f"workflow was renamed, or the run did not reach it"
            )

    graded = [(name, conclusion) for name, conclusion in seen if not _matches(name, spec.advisory)]
    for name, conclusion in graded:
        if conclusion in _JOB_BAD:
            return CI_FAILURE, f"{spec.workflow} job {name!r} -> {conclusion}"
    for name, conclusion in graded:
        if conclusion == CI_CANCELLED:
            return CI_CANCELLED, f"{spec.workflow} job {name!r} was cancelled"
    for name, conclusion in graded:
        if _matches(name, spec.required) and conclusion != CI_SUCCESS:
            verdict = conclusion if conclusion in CI_VERDICTS else CI_UNKNOWN
            return verdict, (
                f"{spec.workflow} required job {name!r} -> {conclusion or 'no conclusion'}"
            )
    off = [
        f"{name} -> {conclusion or 'none'}"
        for name, conclusion in graded
        if conclusion not in (CI_SUCCESS, CI_SKIPPED)
    ]
    if off:
        return CI_UNKNOWN, f"{spec.workflow} jobs in an ungraded state: {'; '.join(off)}"
    return CI_SUCCESS, (f"{spec.workflow}: {len(graded)} graded job(s), all success or skipped")


def wait_for_workflow(
    spec: CiSpec,
    sha,
    *,
    budget_s: float = DEFAULT_CI_WAIT_S,
    poll_s: float = DEFAULT_CI_POLL_S,
    allow_trigger: bool = True,
    gh=_gh,
    sleep=time.sleep,
    monotonic=time.monotonic,
) -> dict:
    """Block until one workflow's run for `sha` is graded, and return a verdict.

    THIS FUNCTION NEVER RAISES. Every tooling fault - a missing `gh`, a non-zero
    exit, unparseable JSON, a payload missing a field - becomes `unavailable`
    with the reason in `detail`, because a CLI hiccup may not wedge or end an
    overnight loop. Only the VERDICT is allowed to be bad news.

    `monotonic`, never wall time: this can block for an hour and a half.

    Args:
        spec: Which workflow and how to grade it.
        sha: The sha the worker pushed. The verdict carries the head CI
            ACTUALLY built, which may be a descendant of this one.
        budget_s: How long to wait for the run to reach `completed`.
        poll_s: Seconds between reads.
        allow_trigger: False suppresses the dispatch, for a caller that only
            wants to grade what already exists.
        gh: `(args) -> (returncode, text)`. The one place this file shells out.
        sleep: Blocking seam. Tests pass a fake that advances a clock instead.
        monotonic: Deadline clock. Never wall time - see the module docstring.

    Returns:
        `{"workflow", "sha", "run_id", "status", "verdict", "jobs", "waited_s",
        "detail"}` where `verdict` is one of CI_VERDICTS.
    """
    started_m = monotonic()
    deadline = started_m + max(0.0, float(budget_s))

    def _out(verdict, *, run_id=None, status="unknown", detail="", head=None, jobs=None) -> dict:
        return {
            "workflow": spec.workflow,
            "sha": str(head or sha),
            "run_id": run_id,
            "status": status,
            "verdict": verdict,
            "jobs": jobs or {},
            "waited_s": round(monotonic() - started_m, 1),
            "detail": str(detail)[:400],
        }

    rows, err = _run_list(gh, spec)
    if err:
        return _out(CI_UNAVAILABLE, detail=err)
    # Everything visible BEFORE any trigger of ours. Anything outside this set
    # later is, by construction, a run we caused.
    seen_ids = {row.get("databaseId") for row in rows}

    run = _pick_run(rows, sha)
    if run is None:
        if not (spec.dispatch and allow_trigger):
            # Deliberately NOT a dispatch. tier1 has no `workflow_dispatch`
            # trigger, so asking for one can only fail - and the failure would
            # read as a tooling fault rather than as the mistake it is.
            return _out(
                CI_UNAVAILABLE,
                detail=(
                    f"no {spec.workflow} run found for {sha}"
                    + (
                        ""
                        if spec.dispatch
                        else " and it cannot be dispatched - it has no workflow_dispatch trigger"
                    )
                ),
            )
        run, err = _trigger_run(gh, spec, sha, seen_ids, sleep=sleep)
        if err:
            return _out(CI_UNAVAILABLE, detail=err)

    def _watch(row) -> dict:  # noqa: PLR0911
        run_id = row.get("databaseId")
        head = str(row.get("headSha") or "") or None
        if run_id is None:
            return _out(CI_UNAVAILABLE, head=head, detail="the run row carried no databaseId")
        status = str(row.get("status") or "")
        conclusion = str(row.get("conclusion") or "")
        while status != "completed":
            # Checked BEFORE the sleep so a zero budget answers immediately and
            # the last poll cannot overshoot the deadline by a whole poll_s.
            if monotonic() >= deadline:
                return _out(
                    CI_TIMEOUT,
                    run_id=run_id,
                    head=head,
                    status=status or "unknown",
                    detail=(f"run {run_id} was still {status or 'pending'} after {budget_s}s"),
                )
            sleep(poll_s)
            view, verr = _gh_json(gh, ["run", "view", str(run_id), "--json", "status,conclusion"])
            if verr:
                return _out(
                    CI_UNAVAILABLE,
                    run_id=run_id,
                    head=head,
                    status=status or "unknown",
                    detail=verr,
                )
            if not isinstance(view, dict):
                return _out(
                    CI_UNAVAILABLE,
                    run_id=run_id,
                    head=head,
                    status=status or "unknown",
                    detail=f"run {run_id} status payload was not an object",
                )
            status = str(view.get("status") or "")
            conclusion = str(view.get("conclusion") or "")
        if conclusion == CI_CANCELLED:
            # Read here rather than from the jobs, because a cancelled run's
            # jobs carry no useful conclusion - and the caller has a specific
            # remedy for this one word that it has for no other.
            return _out(
                CI_CANCELLED,
                run_id=run_id,
                head=head,
                status=status,
                detail=(
                    f"run {run_id} completed 'cancelled' - superseded, or a job hit its own ceiling"
                ),
            )
        data, jerr = _gh_json(gh, ["run", "view", str(run_id), "--json", "jobs"])
        if jerr:
            return _out(CI_UNAVAILABLE, run_id=run_id, head=head, status=status, detail=jerr)
        verdict, detail = grade_ci_jobs(spec, data)
        jobs = {}
        if isinstance(data, dict) and isinstance(data.get("jobs"), list):
            jobs = {
                str(row.get("name") or ""): str(row.get("conclusion") or "")
                for row in data["jobs"]
                if isinstance(row, dict)
            }
        return _out(verdict, run_id=run_id, head=head, status=status, detail=detail, jobs=jobs)

    out = _watch(run)
    if out["verdict"] != CI_CANCELLED or not (spec.dispatch and allow_trigger):
        return out
    # ONCE. Being superseded is the exact failure this wait exists to survive,
    # so one fresh run is worth starting - but a driver that re-dispatched on
    # every cancel would spend the whole budget starting runs instead of
    # watching one, and would keep the runner busy for a night.
    again, err = _trigger_run(gh, spec, sha, seen_ids, sleep=sleep)
    if err:
        return dict(out, detail=f"{out['detail']}; re-dispatch failed: {err}"[:400])
    return _watch(again)


def wait_for_ci(
    sha,
    *,
    specs=CI_SPECS,
    budget_s: float = DEFAULT_CI_WAIT_S,
    poll_s: float = DEFAULT_CI_POLL_S,
    gh=_gh,
    sleep=time.sleep,
    monotonic=time.monotonic,
    wait_one=None,
) -> dict:
    """Wait out every gating workflow for `sha` and roll their verdicts up.

    The roll-up returns the WORST verdict seen, ranked failure-first, so one
    green workflow can never carry a second one that answered nothing. Only
    `failure` is a hard stop for the caller; everything else is recorded and
    passed over, because none of the other words is evidence that `main` broke.

    Args:
        sha: The pushed sha.
        specs: Which workflows gate. Defaults to both tiers.
        budget_s: Per-workflow wait budget, not a total across them.
        poll_s: Seconds between reads of a run's status.
        gh: `(args) -> (returncode, text)`, forwarded to each waiter.
        sleep: Blocking seam, forwarded.
        monotonic: Deadline clock, forwarded. Never wall time.
        wait_one: The per-workflow waiter. The injection seam.

    Returns:
        `{"sha", "verdict", "waited_s", "workflows": [<per-workflow verdict>]}`.
    """
    wait_one = wait_for_workflow if wait_one is None else wait_one
    started = monotonic()
    results = [
        wait_one(
            spec, sha, budget_s=budget_s, poll_s=poll_s, gh=gh, sleep=sleep, monotonic=monotonic
        )
        for spec in specs
    ]
    verdicts = {str(row.get("verdict")) for row in results}
    rolled = CI_SUCCESS
    for word in _VERDICT_RANK:
        if word in verdicts:
            rolled = word
            break
    return {
        "sha": str(sha),
        "verdict": rolled,
        "waited_s": round(monotonic() - started, 1),
        "workflows": results,
    }


# ---------------------------------------------------------------------------
# One cycle.
# ---------------------------------------------------------------------------
#
# THE SEAMS ARE THE POINT, and they are why `run_cycle`, `run_loop` and
# `run_suite_step` carry a PLR0913 / PLR0912 / PLR0915 exemption rather than
# being split. (`run_suite_step` sits above this block and cites it; it carries
# PLR0913 alone, because a wrapper around one call has neither the branches nor
# the statements the other two do.)
#
# Every external dependency of this driver is a keyword argument with a real
# default: the lock, the launcher, the liveness probe, the killer, both clocks,
# the sleeper, the CI waiter, the suite runner, the ledger lock and the emitter.
# That is what lets the whole file be graded without spawning a process,
# sleeping, shelling out to git or gh, or taking an OS mutex - which is a stated
# acceptance clause of this item and not a preference.
#
# SPLITTING THESE WOULD NOT REMOVE THE ARGUMENTS, IT WOULD MOVE THEM. A helper
# taking half the seams still takes half the seams, and the caller then has to
# thread them through - so the count is unchanged and one more layer sits
# between a test and the behaviour it grades. The branch and statement counts
# are the same story: each branch is a distinct RECORDED outcome (lane_held,
# launch_failed, timeout_killed, timeout_kill_failed, error, ci_red, suite_red),
# and collapsing two of them into one word is how a night that ended at cycle 2
# comes to look like a night that ran all twelve.
#
# The exemption is per-site and names its rules, never a directory-wide ignore:
# a NEW function in this package still has to justify itself.


def _is_launch_error(exc: BaseException) -> bool:
    """True when `exc` is the launcher's own "this lane cannot start" signal.

    Resolved here rather than named in an `except` clause, so that a caller who
    injected a `launch` seam does not have to have `lane_launcher.py` on disk
    just to be caught correctly. An `except lane_launcher.LaneLaunchError`
    binds the module at the moment the exception is raised, which turns an
    injected dependency back into a required one.

    The identity check is the CLASS, never the name: a bare name comparison
    would swallow any unrelated exception that happened to be called the same
    thing, and swallowing an unexpected fault as a launch failure would report
    a bad night as an ordinary one. A missing module answers False, so the
    fault propagates and is recorded as an `error` rather than mislabelled.
    """
    try:
        return isinstance(exc, _mod("lane_launcher").LaneLaunchError)
    except (OSError, AttributeError, ImportError, ModuleNotFoundError):
        return False


def _worker_is_up(pid, started, *, alive, stranger) -> bool:
    """True only while the ORIGINAL worker process is still running.

    Two probes, not one. `alive` answers whether SOMETHING holds the pid;
    `stranger` answers whether that something is still the process we launched.
    Reusing `lanes`' pair rather than deriving a second one is what keeps the
    driver and any dashboard from ever disagreeing about a lane.

    TOTAL by construction: every uncertain case answers "not a stranger", so an
    unavailable source degrades to the plain pid probe instead of declaring a
    live worker dead and firing a second one into its worktree.
    """
    if not alive(pid):
        return False
    return not stranger(pid, started)


def _await_death(pid, started, *, alive, stranger, kill_grace_s, poll_s, sleep, monotonic) -> bool:
    """Re-probe after a kill. True when the worker is gone inside the grace.

    This is the whole of the unverified-kill fix. `_taskkill` swallows its own
    failure on purpose, so the only evidence it took is the liveness probe
    coming back false. Bounded, because a driver that waits forever on a process
    it cannot kill is a wedged driver with extra steps.
    """
    grace = max(0.0, float(kill_grace_s))
    deadline = monotonic() + grace
    # Never slower than the normal poll and never longer than the whole grace: a
    # 10s step against a 2s grace would sleep straight past the answer and
    # report a failed kill that actually worked.
    step = max(0.0, min(float(poll_s), grace))
    while True:
        if not _worker_is_up(pid, started, alive=alive, stranger=stranger):
            return True
        if monotonic() >= deadline:
            return False
        sleep(step)


#: The fallback token when the surface module itself cannot be bound. The
#: watcher's spelling, restated ONLY for the case where that module is the thing
#: that failed to load.
INBOX_UNMEASURED = "UNMEASURED"


def _surface_inbox(cycle, worktree, *, surface=None, emit=_emit) -> dict:
    """Surface the channel for one cycle, print its line, and hand back the fact.

    CS-1104. SURFACING, NEVER REPLYING: the surface lists the main tree's
    `moon_sync_inbox/` and writes nothing - no acknowledgement, no report, no
    note. The fact rides on this cycle's own ledger row and on ONE driver line,
    and goes into no other tree. The driver computes it, so it is evidence a
    worker's banner can never be: a banner is prose a model wrote.

    NEVER RAISES. A surface that cannot bind or faults becomes `UNMEASURED`
    carrying the exception CLASS name only, because a night must never end over
    an instrument, and an exception message is an echo path.

    THE LINE DOES NOT START `queue-loop cycle`, deliberately: an operator counts
    a night down the left margin by that prefix, and so do the arms grading it.
    """
    try:
        mod = _mod("inbox_surface")
        fact = (mod.surface if surface is None else surface)(worktree)
        text = mod.line(fact)
    except Exception as exc:  # DELIBERATE: the surface is an instrument
        reason = f"the inbox surface could not run ({type(exc).__name__})"
        fact = {"unread": INBOX_UNMEASURED, "names": [], "more": 0, "reason": reason}
        text = f"inbox: {INBOX_UNMEASURED} ({reason})"
    emit(f"queue-loop inbox (cycle {cycle}): {text.removeprefix('inbox: ')}")
    return fact


def run_cycle(  # noqa: PLR0913, PLR0912, PLR0915 - see THE SEAMS ARE THE POINT
    cycle: int,
    *,
    lane: str = LANE,
    worktree=None,
    run_id=None,
    repo_root=None,
    poll_s: float = DEFAULT_POLL_S,
    cycle_timeout_s: float = DEFAULT_CYCLE_TIMEOUT_S,
    kill_grace_s: float = DEFAULT_KILL_GRACE_S,
    acquire_retries: int = ACQUIRE_RETRIES,
    acquire_wait_s: float = ACQUIRE_WAIT_S,
    acquire=None,
    release=None,
    launch=None,
    alive=None,
    proc_started=None,
    stranger=None,
    kill=_taskkill,
    observe=_noop,
    surface=None,
    emit=_emit,
    sleep=time.sleep,
    clock=time.time,
    monotonic=time.monotonic,
) -> dict:
    """Run exactly one lane cycle: claim, launch, wait for the worker, release.

    Returns a record. It does not raise for any outcome the driver is supposed
    to survive - `lane_held` and `launch_failed` are recorded and returned so
    the loop can go on. Only a genuinely unexpected fault propagates, and even
    then the lane is released first.

    Every dependency is a keyword seam. A `None` seam is resolved from `lanes`
    or `lane_launcher` at CALL time, which keeps this module importable without
    them while still making a substitution a deliberate act by the caller.
    """
    # Resolved INSIDE the guard rather than through a conditional expression, so
    # the module object is never typed as "maybe None" - a shape that reads as a
    # possible AttributeError on every line below it.
    if None in (acquire, release, alive, proc_started, stranger):
        lanes_mod = _mod("lanes")
        acquire = lanes_mod.try_acquire_lane if acquire is None else acquire
        release = lanes_mod.release_lane if release is None else release
        alive = lanes_mod.pid_alive if alive is None else alive
        proc_started = lanes_mod.proc_started if proc_started is None else proc_started
        stranger = lanes_mod.holder_is_a_stranger if stranger is None else stranger
    # The launcher module is resolved ONLY when it is actually needed - when no
    # launcher was injected, or when no worktree was named. A caller that
    # supplies both has substituted the whole dependency, and requiring the
    # module anyway would make the seam a fiction: the file would have to exist
    # for a call that never touches it.
    if launch is None or worktree is None:
        launcher = _mod("lane_launcher")
        if launch is None:
            real_launch = launcher.launch_lane

            def launch(lane_name, **kw):
                """Bind `repo_root` into the launcher's own `root` argument."""
                return real_launch(lane_name, root=repo_root, **kw)

        if worktree is None:
            worktree = launcher.worktree_path(lane)

    # Worktree-mandatory (enforced again in the lock and a third time in the
    # launcher). When it is not named it is resolved from the launcher above
    # rather than hardcoded here, so a lane relocation moves one definition.
    run_id = uuid.uuid4().hex[:8] if run_id is None else str(run_id)
    started_at = clock()

    def _record(outcome, ok, pid, ended_at, detail="") -> dict:
        return {
            "cycle": int(cycle),
            "run_id": run_id,
            "worker_ok": bool(ok),
            "pid": pid,
            "started_at": started_at,
            "ended_at": ended_at,
            "duration_s": round(ended_at - started_at, 3),
            "outcome": outcome,
            "detail": detail,
            # CS-1104. Taken when the row is built, on EVERY outcome, so a
            # refused or failed cycle still says what was waiting in the channel.
            "inbox": _surface_inbox(cycle, worktree, surface=surface, emit=emit),
        }

    # ---- claim, retrying while the lane is legitimately held elsewhere
    claim = None
    attempts = max(1, int(acquire_retries))
    for attempt in range(1, attempts + 1):
        claim = acquire(lane, run_id=run_id, worktree=str(worktree))
        if claim.get("ok"):
            break
        # A refusal writes nothing on disk, so retrying is free and safe. No
        # wait after the FINAL attempt - it would only delay the record.
        if attempt < attempts:
            sleep(acquire_wait_s)
    if not (claim and claim.get("ok")):
        # THE REFUSAL WORD IS READ, and that is the whole of CS-1011. `lanes.py`
        # has answered two different faults since CS-1009 and this branch saw
        # one, so an occupied WORKTREE was written down as a held LANE naming a
        # lane that holds nothing - one waits, the other repoints.
        #
        # NOTHING FROM THE DICT IS RENDERED. The word, the holder and the pid
        # each go through a validator that returns one of this module's own
        # values, because the refusal payload carries a worktree PATH and the
        # row it lands in is a durable JSONL file - CLAUDE.md non-negotiable 3.
        # The path itself is never copied at all: an operator who needs it reads
        # it off the lock, and a lane name is what identifies the collision.
        refusal = _refusal_outcome((claim or {}).get("refused"))
        holder = _holder_name((claim or {}).get("holder"))
        pid = _holder_pid((claim or {}).get("pid"))
        if refusal == OUTCOME_WORKTREE_IN_USE:
            detail = (
                f"the worktree this lane is pointed at is already in use by "
                f"lane {holder!r} (pid {pid}) after {attempts} attempts - "
                f"waiting will not free it, one of the two lanes must be "
                f"re-pointed"
            )
        else:
            detail = f"lane held by {holder!r} (pid {pid}) after {attempts} attempts"
        return _record(refusal, False, None, clock(), detail)

    token = claim.get("token")
    outcome, detail, pid = OUTCOME_COMPLETED, "", None
    try:
        try:
            run = launch(lane, run_id=run_id, token=token)
        except Exception as exc:
            if not _is_launch_error(exc):
                raise
            # launch_lane has ALREADY released the lane on this path; the
            # finally below releases again, which is deliberate - release_lane
            # is idempotent, and an unconditional release is the only shape that
            # survives a future launcher that stops cleaning up after itself.
            outcome, detail = OUTCOME_LAUNCH_FAILED, _launch_fault(exc)[:400]
        else:
            pid = run.get("pid")
            if not pid:
                outcome, detail = OUTCOME_LAUNCH_FAILED, "launch returned no pid"
            else:
                detail = str(run.get("log") or "")
                # Identity, captured ONCE and only here. A pid alone does not
                # name a process, so every later probe compares (pid, start
                # time) against THIS value. None is the fail-soft answer and
                # `stranger` reads it as "cannot prove reuse".
                worker_started = proc_started(pid)
                # The budget starts HERE, at launch, on the MONOTONIC clock -
                # the acquire retries above can burn ten legitimate minutes and
                # none of it is the worker's to pay for.
                launched_m = monotonic()
                while _worker_is_up(pid, worker_started, alive=alive, stranger=stranger):
                    # THE ONLY MOMENT THIS DRIVER IS AWAKE WHILE THE WORKER IS,
                    # which is the only moment a row claim is observable: the
                    # worker releases its claim at the wrap, so a read taken
                    # after this loop learns nothing from a compliant cycle.
                    # `ClaimWatch.sample` never raises - see its docstring, and
                    # note that a fault here would escape `run_loop`'s catch
                    # around this call only by ending the night.
                    observe()
                    waited = monotonic() - launched_m
                    if waited >= float(cycle_timeout_s):
                        # EXACTLY once - the break is load-bearing. A second
                        # kill could land on a pid the OS has already reissued
                        # to an unrelated process.
                        kill(pid)
                        ran_for = round(waited, 1)
                        if _await_death(
                            pid,
                            worker_started,
                            alive=alive,
                            stranger=stranger,
                            kill_grace_s=kill_grace_s,
                            poll_s=poll_s,
                            sleep=sleep,
                            monotonic=monotonic,
                        ):
                            outcome = OUTCOME_TIMEOUT
                            detail = (
                                f"worker ran {ran_for}s against a "
                                f"{cycle_timeout_s}s budget - killed"
                            )
                        else:
                            # Unrecoverable for the LOOP, not just this cycle.
                            outcome = OUTCOME_KILL_FAILED
                            detail = (
                                f"worker ran {ran_for}s against a "
                                f"{cycle_timeout_s}s budget - taskkill did "
                                f"NOT take within {kill_grace_s}s; pid "
                                f"{pid} may still be writing to {worktree}"
                            )
                        break
                    sleep(poll_s)
                # ONCE MORE AFTER THE WAIT, on every path out of it. A worker
                # that exits before the first poll - or a killed one that leaves
                # its claim behind - would otherwise be a cycle the driver never
                # looked at, and a cycle nobody looked at must not read like one
                # that was checked and found clean.
                observe()
    finally:
        # Every path, including an exception nobody predicted. The release runs
        # BEFORE that exception escapes, because a driver that dies holding the
        # only lane slot wedges the lane until someone reclaims it by hand.
        release(token)

    return _record(outcome, outcome == OUTCOME_COMPLETED, pid, clock(), detail)


# ---------------------------------------------------------------------------
# The loop.
# ---------------------------------------------------------------------------


def run_loop(  # noqa: PLR0913, PLR0912, PLR0915 - see THE SEAMS ARE THE POINT
    *,
    max_cycles: int = DEFAULT_MAX_CYCLES,
    settle_s: float = DEFAULT_SETTLE_S,
    poll_s: float = DEFAULT_POLL_S,
    cycle_timeout_s: float = DEFAULT_CYCLE_TIMEOUT_S,
    kill_grace_s: float = DEFAULT_KILL_GRACE_S,
    max_consecutive_errors: int = DEFAULT_MAX_CONSECUTIVE_ERRORS,
    max_consecutive_launch_failures: int = DEFAULT_MAX_CONSECUTIVE_LAUNCH_FAILURES,
    max_consecutive_unproductive: int = DEFAULT_MAX_CONSECUTIVE_UNPRODUCTIVE,
    ci_gate: bool = True,
    ci_wait_s: float = DEFAULT_CI_WAIT_S,
    ci_poll_s: float = DEFAULT_CI_POLL_S,
    local_suite: bool = False,
    lane: str = LANE,
    worktree=None,
    repo_root=None,
    control_dir=None,
    cycle_log=None,
    acquire_retries: int = ACQUIRE_RETRIES,
    acquire_wait_s: float = ACQUIRE_WAIT_S,
    acquire=None,
    release=None,
    launch=None,
    alive=None,
    proc_started=None,
    stranger=None,
    kill=_taskkill,
    head_sha=None,
    tree_sha=None,
    gh=_gh,
    wait=None,
    suite=None,
    ration=None,
    permit=None,
    claim_states=None,
    claim_root=None,
    hold=None,
    surface=None,
    sleep=time.sleep,
    clock=time.time,
    monotonic=time.monotonic,
    emit=_emit,
) -> dict:
    """Fire cycles until `max_cycles`, a stop sentinel, or a hard stop.

    THE WAITS LIVE HERE, BETWEEN CYCLES, AND NOWHERE ELSE. That placement is
    the mechanism: the only thing that can start cycle N+1 is this loop, and
    while it is inside a wait it is not starting anything. A wait delegated to
    the worker is a request; a wait taken here is a guarantee.

    The sentinel check is at the TOP of the iteration, which is what makes a
    QUEUE_DRAINED written by the worker mid-cycle stop the NEXT cycle rather
    than retroactively discard the one that wrote it. The hard stops are checked
    at the BOTTOM, after the offending record is appended and emitted - the
    evidence of why the night ended has to reach the ledger.

    THE CI GATE HANGS OFF `origin/main`, NOT OFF THE WORKER. The driver never
    looks inside the lane worktree and has no channel to the worker beyond a
    pid, so the only push signal available to it is the remote ref moving:
    `head_sha()` is read before and after each cycle, and an UNCHANGED answer
    means the worker shipped nothing and there is no run to wait for. The
    verdict is attached to the SAME record, so one JSONL row carries a cycle and
    its acceptance and nobody has to join two files at 3am.

    An ABSENT `ci` key means no gate ran for that cycle - the gate was off, or
    the outcome was something other than `completed`. It deliberately is NOT
    recorded as `verdict="skipped"`, because that word already means a JOB was
    skipped, and one word cannot carry two conditions.

    A cycle that ran the gate and PUSHED NOTHING is a third condition again, and
    it gets a word of its own: `verdict="no-push"`, which makes the row not ok
    without stopping the night. A gate that found nothing to grade produced no
    evidence, and a cycle with no evidence is not good news - but it is also not
    a broken branch, so the hard stop stays keyed on `CI_FAILURE` alone. A
    drained queue pushes nothing too, so the final cycle of a good drain now
    reads `ok: false`; the NIGHT still exits 0, because a drain is its own stop
    reason. The alternative - calling a no-push ok whenever a drain sentinel is
    present - was rejected: the driver cannot see WHY nothing was pushed, and
    inventing a distinction it cannot observe is the defect class this avoids.

    Returns:
        `{"cycles_run", "stopped_by", "records"}`.
    """
    head_sha = remote_head_sha if head_sha is None else head_sha
    tree_sha = local_head_sha if tree_sha is None else tree_sha
    wait = wait_for_ci if wait is None else wait
    suite = run_local_suite if suite is None else suite

    records: list = []
    stopped_by = None
    consecutive_errors = 0
    error_limit = max(1, int(max_consecutive_errors))
    consecutive_launch_failures = 0
    launch_failure_limit = max(1, int(max_consecutive_launch_failures))
    consecutive_unproductive = 0
    unproductive_limit = max(1, int(max_consecutive_unproductive))
    total = max(0, int(max_cycles))
    for cycle in range(1, total + 1):
        reason = stop_reason(control_dir)
        if reason:
            stopped_by = reason
            emit(f"queue-loop stop: {reason} present - {len(records)} cycle(s) run")
            break
        # Minted HERE, not inside run_cycle, so the error record below can name
        # the SAME run as the claim and the worker log. A cycle that faulted
        # before returning would otherwise leave a row nothing can be joined to.
        run_id = uuid.uuid4().hex[:8]
        started_at = clock()
        # BEFORE the cycle, unconditionally when the gate is on: the outcome is
        # not knowable in advance, and one `ls-remote` against a multi-hour
        # cycle is not a cost worth optimising.
        pre_sha = head_sha() if ci_gate else None
        # UNCONDITIONAL, and NOT gated on `ci_gate`. Whether the cycle
        # produced a commit is a question about the worker, not about the
        # CI gate, and a night run with the gate off still has to be
        # stopped when it is accomplishing nothing.
        pre_tree, pre_why = _lane_head(tree_sha, lane, worktree)
        # BEFORE THE CYCLE, AND THE ORDER IS THE MECHANISM. A cycle that closes
        # its row deletes that row from `ROADMAP.md`, so a permit computed
        # afterwards would report the row the worker just finished as one it was
        # never allowed to take. What is graded is what the lane could take when
        # it started.
        permitted = (permit_for_lane if permit is None else permit)(lane)
        watch = ClaimWatch(
            lane,
            started_at=started_at,
            states=claim_states,
            root=claim_root,
            clock=clock,
        )
        try:
            record = run_cycle(
                cycle,
                lane=lane,
                worktree=worktree,
                repo_root=repo_root,
                run_id=run_id,
                poll_s=poll_s,
                cycle_timeout_s=cycle_timeout_s,
                kill_grace_s=kill_grace_s,
                acquire_retries=acquire_retries,
                acquire_wait_s=acquire_wait_s,
                acquire=acquire,
                release=release,
                launch=launch,
                alive=alive,
                proc_started=proc_started,
                stranger=stranger,
                kill=kill,
                observe=watch.sample,
                surface=surface,
                emit=emit,
                sleep=sleep,
                clock=clock,
                monotonic=monotonic,
            )
        except Exception as exc:  # DELIBERATE catch-all - see the comment below
            # A night that ends at cycle 3 on ONE unexpected fault is the defect
            # this closes, and the SILENT half was worse: `append_record` is only
            # reached on the normal path, so a fault used to leave no ledger row
            # at all. Nothing leaks by catching here - run_cycle releases the
            # lane in its own `finally` before any exception escapes it.
            ended_at = clock()
            record = {
                "cycle": int(cycle),
                "run_id": run_id,
                "worker_ok": False,
                "pid": None,
                "started_at": started_at,
                "ended_at": ended_at,
                "duration_s": round(ended_at - started_at, 3),
                "outcome": OUTCOME_ERROR,
                "detail": _fault(exc)[:400],
                # CS-1104. `run_cycle` surfaces only when it builds its own row,
                # which a raise skips, so this row surfaces here - once.
                "inbox": _surface_inbox(cycle, worktree, surface=surface, emit=emit),
            }

        # ---- THE DRIVER-OWNED WAITS, before the append so ONE row carries
        # ---- the cycle and its acceptance together.
        note = ""
        post_tree, post_why = _lane_head(tree_sha, lane, worktree)
        # DID THIS CYCLE PRODUCE A COMMIT - the question the progress
        # counter asks, and deliberately NOT the question `ok` answers.
        #
        # THE DEFAULT ON AN UNREADABLE HEAD IS `False`, AND THE CHOICE IS
        # BETWEEN TWO COSTS. Defaulting to True re-opens the exact hole this
        # item exists to close - a night that accomplishes nothing burns its
        # whole budget and reports exit 0, which is a lie a launcher cannot
        # see through. Defaulting to False costs the REMAINING cycles of a
        # night whose lane tree the driver has lost sight of for three
        # consecutive cycles, and costs nothing already committed. The
        # counter is CONSECUTIVE, so one transient git failure between two
        # readable cycles is survived. A driver that cannot see the tree its
        # worker writes into is not entitled to keep extending the night, so
        # the honest exit 9 wins over the cheerful exit 0.
        #
        # `detail` carries WHICH of the two it was: an operator sent to read
        # a worker log because the row said the worker committed nothing,
        # when in fact git could not answer, has been sent to the wrong file.
        record["commit"] = {
            "pre": pre_tree,
            "post": post_tree,
            "advanced": bool(pre_tree and post_tree and post_tree != pre_tree),
            "detail": (
                ""
                if pre_tree and post_tree
                else _UNREADABLE_HEAD + (pre_why or post_why or "git gave no answer")
            ),
        }
        # ON THE CONSOLE LINE TOO, because without it a lane-branch night
        # and a dead night are the same five hundred characters: both read
        # `ci=no-push`, and only one of them is fine. The operator tailing
        # this reads a night by counting cycles down the left margin, and
        # this is the token that tells them which night they are watching.
        # THREE WORDS, not two: unreadable sends someone to the git state,
        # `no` sends them to the worker log, and those are different errands.
        if record["commit"]["advanced"]:
            note += " commit=yes"
        elif record["commit"]["detail"]:
            note += " commit=unreadable"
        else:
            note += " commit=no"
        # ON EVERY CYCLE, INCLUDING THE ONES THAT CLAIMED NOTHING. The CS-993
        # shape: a field written only when it has bad news to report leaves a
        # row nobody checked byte-identical to a row that passed the check, and
        # the stdout log this driver writes is truncated at every launch, so the
        # ROW is the only place the distinction can live.
        record["scope"] = _mod("scope").binding_fact(
            permitted,
            watch.rows(),
            committed=record["commit"]["advanced"],
        )
        # DIAGNOSTIC, AND NOTHING GRADES ON EITHER NUMBER. Zero samples means
        # the driver never looked, which a reader has to be able to tell from a
        # store that was empty every time it did.
        record["scope"]["samples"] = watch.samples
        record["scope"]["sample_faults"] = watch.faults
        if record["outcome"] == OUTCOME_COMPLETED and local_suite:
            # INSIDE THE RATION, and the worktree resolution lives with it - see
            # `run_suite_step`. Two lanes running a suite at once exhausts the
            # box and the loser reports a pass count beside an error while
            # thousands of tests never run, which reaches this ledger as a green
            # nobody earned. The driver waits here, which is where every wait
            # this file owns already happens.
            run_suite_step(
                record,
                lane=lane,
                worktree=worktree,
                run_id=run_id,
                suite=suite,
                ration=ration,
                # BENEATH the control directory, so `--control-dir` moves the
                # ration with the stop sentinels rather than leaving half the
                # control plane pointed at the real one. The dirname is
                # `ration.py`'s to spell, not this file's.
                root=(None if control_dir is None else Path(control_dir) / _mod("ration").DIR_NAME),
                sleep=sleep,
                monotonic=monotonic,
                emit=emit,
            )
        else:
            # ON EVERY OTHER CYCLE TOO. With `--local-suite` off - the default,
            # and what the launcher produces unless asked - this branch is the
            # ONLY thing that records that the ration covered nothing, and a row
            # that says nothing about the ration reads exactly like a row it
            # protected. Measured: 0 ration entries per cycle under the default.
            record["ration"] = dict(RATION_NO_SUITE)
        if ci_gate and record["outcome"] == OUTCOME_COMPLETED:
            post_sha = head_sha()
            if pre_sha is None or post_sha is None:
                # A tooling failure, recorded as one. Staying silent here would
                # make a night with no CI evidence read like a night of greens.
                record["ci"] = {
                    "sha": post_sha or pre_sha,
                    "verdict": CI_UNAVAILABLE,
                    "waited_s": 0.0,
                    "workflows": [],
                    "detail": (
                        f"origin/{CI_REF} could not be resolved, so this "
                        f"cycle's push could not be identified"
                    ),
                }
            elif post_sha == pre_sha:
                # RECORDED AS A VERDICT, not left as an absent key. This branch
                # used to set a console note and nothing else, so the row's `ci`
                # field was ABSENT and the roll-up's verdict clause was
                # vacuously true - a 972-second cycle that shipped nothing was
                # written down as `"ok": true`. The SAME five-key shape the
                # unavailable branch writes, so no reader learns a second shape.
                record["ci"] = {
                    "sha": post_sha,
                    "verdict": CI_NO_PUSH,
                    "waited_s": 0.0,
                    "workflows": [],
                    "detail": (
                        f"origin/{CI_REF} did not move, so this cycle pushed "
                        f"nothing and there is no run to wait for"
                    ),
                }
            else:
                record["ci"] = wait(
                    post_sha,
                    budget_s=ci_wait_s,
                    poll_s=ci_poll_s,
                    gh=gh,
                    sleep=sleep,
                    monotonic=monotonic,
                )
        verdict = record.get("ci")
        if verdict:
            # `+=`, NOT `=`. This used to be the first thing written to the
            # note and could assign; it is no longer first, and an assignment
            # here silently ate the commit token that precedes it.
            note += f" ci={verdict['verdict']} {verdict.get('waited_s', 0)}s"
        local = record.get("suite")
        rationed = record.get("ration") or dict(RATION_NO_SUITE)
        if local:
            note += f" suite={'ok' if local['ok'] else 'RED'} [{local['summary']}]"
        if not rationed["rationed"]:
            # ON THE CONSOLE LINE AS WELL AS IN THE ROW. An operator tailing this
            # reads a night by counting cycles down the left margin, and a suite
            # verdict that was measured on a contended box has to be legible
            # there rather than only in a file nobody opens until morning.
            note += " ration=UNRATIONED"
        bound = record["scope"]
        if not bound["bound"]:
            # THE SAME REASONING, over the row the cycle worked. The reason word
            # rides along because the three ways a binding fails send a reader
            # to three different files.
            note += f" {SCOPE_NOTE}({bound['reason']})"

        # THE ROLL-UP, and it is the LAST thing set before the row is written.
        # `worker_ok` says the worker ran to completion, which is all `run_cycle`
        # can know; `ok` says the whole cycle is good news, which is what anyone
        # reading this file actually wants. Keeping only the first was measured
        # to produce `"ok": true` beside `"suite": {"ok": false}` on a cycle
        # whose tests went red - both fields correct, the pair a trap.
        #
        # AND A SUITE NOBODY COULD MEASURE IS NOT A PASS. The unrationed
        # fall-through keeps `suite["ok"]` verbatim, because pytest's answer is
        # still pytest's answer; what it cannot do is stand as this cycle's
        # acceptance, because it was taken while another suite was running and
        # the loser of that contest reports a pass count beside an error with
        # thousands of tests unrun. So the roll-up refuses it here, where every
        # other "this is not good news" clause already lives.
        #
        # AND A ROW NOBODY AUTHORISED IS NOT GOOD NEWS EITHER. The binding
        # clause sits here with every other "this is not good news" clause
        # rather than stopping the night: the work is done and the commit is
        # real, and discarding either would cost more than it bought. What must
        # not happen is that the row reads like one the lane was pointed at.
        record["ok"] = bool(
            record["worker_ok"]
            and (local is None or local["ok"])
            and rationed["rationed"]
            and bound["bound"]
            and (verdict is None or verdict["verdict"] not in _CI_ROLLUP_BAD)
        )

        records.append(record)
        append_record(record, cycle_log, hold=hold, emit=emit)
        # ONE line per cycle, still. The verdicts ride on it rather than taking
        # lines of their own, because an operator tailing this reads a night by
        # counting cycles down the left margin.
        emit(
            f"queue-loop cycle {cycle}/{total} {record['outcome']} "
            f"run_id={record['run_id']} pid={record['pid']} "
            f"{record['duration_s']}s{note} {record['detail']}".rstrip()
        )

        if verdict and verdict["verdict"] == CI_FAILURE:
            # HARD STOP, and the only CI verdict that is one. Every further
            # cycle would push another row on top of a break nobody is
            # watching, and the rows would then have to be untangled from each
            # other before either could be judged.
            stopped_by = STOPPED_BY_CI_RED
            emit(
                f"queue-loop stop: ci is RED on {verdict['sha']} - refusing to "
                f"push another row onto a broken {CI_REF}"
            )
            break
        if local and not local["ok"]:
            stopped_by = STOPPED_BY_SUITE_RED
            emit(
                f"queue-loop stop: the local suite is RED - "
                f"[{local['summary']}] exit {local['exit_code']}"
            )
            break
        if record["outcome"] == OUTCOME_KILL_FAILED:
            # HARD STOP. The next cycle would fire a second worker into a
            # worktree whose previous writer is still alive, and two writers in
            # one working directory is not recoverable by retrying.
            stopped_by = OUTCOME_KILL_FAILED
            emit(
                f"queue-loop stop: pid {record['pid']} survived its kill - "
                f"refusing to launch into {lane} again this run"
            )
            break
        # THREE COUNTERS, AND ONLY THE THIRD GENERALISES.
        #
        # The first two each name ONE repeating cause and are checked FIRST, so
        # a pure night of faults and a pure night of refusals keep their own
        # word and their own exit code: folding `launch_failed` into
        # `consecutive_errors` would put "the cycles errored" and "the lane
        # never started" behind one number, and those demand opposite responses.
        #
        # THE THIRD IS THE INVARIANT ITSELF: no sequence of outcomes in which no
        # cycle ever COMPLETES may run the full budget. A previous merge left an
        # alternating `error` / `launch_failed` night as an accepted residual on
        # the grounds that it was narrow; the same hole was then found again
        # wearing `lane_held`, which reset both counters on every cycle and let
        # a night whose lane was never free run all twelve and exit 0. The
        # lesson is that enumerating bad outcomes is the defect. This counter
        # asks the general question instead, against the PRODUCTIVE_OUTCOMES
        # allowlist, so a future outcome cannot reopen the hole by being
        # forgotten.
        if _is_progress(record):
            # CONSECUTIVE, not cumulative. One bad cycle between good ones is a
            # transient the loop is supposed to survive; resetting here is what
            # keeps a flaky night from being scored as a broken one.
            #
            # `_is_progress`, not the outcome word: a `completed` cycle that
            # committed nothing produced nothing, and reading the outcome
            # alone let twelve of those run the whole budget. It reads the
            # `commit` field rather than `ok` - see the docstring there for
            # why the remote ref is the wrong question.
            consecutive_unproductive = 0
        else:
            consecutive_unproductive += 1
        if record["outcome"] == OUTCOME_ERROR:
            consecutive_errors += 1
            consecutive_launch_failures = 0
            if consecutive_errors >= error_limit:
                stopped_by = STOPPED_BY_CONSECUTIVE_ERRORS
                emit(
                    f"queue-loop stop: {consecutive_errors} consecutive error "
                    f"cycles - {record['detail']}"
                )
                break
        elif record["outcome"] == OUTCOME_LAUNCH_FAILED:
            consecutive_launch_failures += 1
            consecutive_errors = 0
            if consecutive_launch_failures >= launch_failure_limit:
                stopped_by = STOPPED_BY_LAUNCH_FAILED
                emit(
                    f"queue-loop stop: {consecutive_launch_failures} consecutive "
                    f"launch failures - {record['detail']}"
                )
                break
        else:
            consecutive_errors = 0
            consecutive_launch_failures = 0
        if consecutive_unproductive >= unproductive_limit:
            # REACHED BY A MIXED RUN, AND BY ANY PURE RUN WHOSE OWN LIMIT SITS
            # ABOVE THIS ONE. The earlier claim here - "reached only by a mixed
            # run" - is true only at the DEFAULTS, where all three limits are 3
            # and the two specific counters are checked first, so a pure night
            # trips its own word on the same cycle and breaks there.
            #
            # THE COUPLING IS REAL AND IS STATED RATHER THAN HIDDEN: raise
            # `max_consecutive_launch_failures` or `max_consecutive_errors`
            # above `max_consecutive_unproductive` and this backstop fires
            # first, which makes EXIT_CONSECUTIVE_LAUNCH_FAILURES or
            # EXIT_CONSECUTIVE_ERRORS unreachable for a pure night. No CLI flag
            # threads those limits today, so it is latent rather than live; the
            # caller that first threads one has to decide the ordering, and
            # `tests/test_queue_loop.py` grades both halves of this paragraph.
            stopped_by = STOPPED_BY_NO_PROGRESS
            emit(
                # WHAT THE DRIVER ACTUALLY KNOWS, and no more. The earlier
                # wording said these cycles "completed nothing", which it
                # cannot support: `timeout_killed` advances this counter, the
                # CI gate only runs on a `completed` cycle, and so a killed
                # worker may well have pushed before it was killed.
                f"queue-loop stop: {consecutive_unproductive} consecutive cycles "
                f"the driver could not grade as having shipped - a killed or "
                f"ungraded worker may still have pushed - "
                f"{record['outcome']} {record['detail']}".rstrip()
            )
            break

        # Between cycles only. A settle after the final cycle would just delay
        # the driver's own exit for nothing.
        if cycle < total:
            sleep(settle_s)
    if stopped_by is None:
        stopped_by = STOPPED_BY_MAX_CYCLES
    return {"cycles_run": len(records), "stopped_by": stopped_by, "records": records}


# ---------------------------------------------------------------------------
# The CLI.
# ---------------------------------------------------------------------------

#: stopped_by -> exit code, for the reasons that are not EXIT_OK. Held as one
#: table rather than a ladder of ifs so a new stop reason cannot be added
#: without giving it a number, which is the defect that made a night ending at
#: cycle 2 indistinguishable from a night that ran all twelve.
_STOP_EXIT = {
    OUTCOME_KILL_FAILED: EXIT_KILL_FAILED,
    STOPPED_BY_CONSECUTIVE_ERRORS: EXIT_CONSECUTIVE_ERRORS,
    STOPPED_BY_LAUNCH_FAILED: EXIT_CONSECUTIVE_LAUNCH_FAILURES,
    STOPPED_BY_NO_PROGRESS: EXIT_NO_PROGRESS,
    STOPPED_BY_CI_RED: EXIT_CI_RED,
    STOPPED_BY_SUITE_RED: EXIT_SUITE_RED,
}

#: THE CLOSED SET OF WORDS PERMITTED TO EXIT 0 - and it is closed because the
#: alternative was measured wrong. `_STOP_EXIT.get(stopped, EXIT_OK)` made the
#: permitted set implicitly INFINITE: any word the table did not list meant
#: success. That is not a hypothetical - `run_loop` already assigns a stop word
#: that is not a `STOPPED_BY_*` constant (`stopped_by = OUTCOME_KILL_FAILED`),
#: so a new hard stop copied from that same block - `stopped_by =
#: OUTCOME_TIMEOUT`, say - would have exited 0 while a name sweep over
#: `STOPPED_BY_*` stayed green. Widening the sweep does not close that; only
#: inverting the default does.
#:
#: `max_cycles` is here rather than in `_STOP_EXIT` deliberately: it is the
#: night ending the way it was asked to. The three sentinel NAMES are here for
#: the MID-run case - a sentinel the worker wrote after doing real work. A
#: sentinel that was already there is caught earlier, on `cycles_run == 0`, and
#: keeps EXIT_STOP_SENTINEL.
#:
#: Membership here is permission to exit 0, NOT a guarantee of it: a run in this
#: set whose records contain no shipping cycle still returns EXIT_NO_PROGRESS.
_SUCCESS_STOPS = frozenset({STOPPED_BY_MAX_CYCLES, *STOP_NAMES})


def main(argv=None, *, singleton=None) -> int:
    """CLI entry point for the detached launcher.

    A drained queue IS a successful outcome - but it is not the same outcome as
    a night's work, and one number cannot mean both. The distinction is drawn on
    `cycles_run`, so a sentinel that appears MID-run (the worker's own
    QUEUE_DRAINED, the normal end of a good drain) is eligible for 0, while a
    sentinel that was ALREADY there when the driver started exits
    EXIT_STOP_SENTINEL.

    ELIGIBLE, not entitled. `cycles_run > 0` was the whole of the old test and
    it was too weak by exactly the amount that matters: a run of one held cycle
    reported `cycles_run=1 stopped_by=max_cycles` and exited 0. EXIT_OK is now
    returned only when the stop word is in `_SUCCESS_STOPS` AND at least one
    record `_is_progress`. Everything else has a number: a listed hard stop
    keeps its own, a word in neither table gets EXIT_UNKNOWN_STOP, and a
    permitted stop that shipped nothing gets EXIT_NO_PROGRESS. That is the whole
    of "no launcher can print a success banner over a no-op", and the residual
    is named: the driver's push signal is `origin/main` moving, so work that was
    committed but not pushed is invisible to it and reads as no progress.

    Args:
        argv: Command line, for testing.
        singleton: A zero-argument callable returning a context manager held for
            the whole run. The seam exists so tests never touch a real OS mutex.

    Returns:
        One of the EXIT_* codes.
    """
    parser = argparse.ArgumentParser(
        prog="queue_loop", description="Re-fire the one-row queue lane worker cycle after cycle."
    )
    parser.add_argument(
        "--cycles",
        type=int,
        default=DEFAULT_MAX_CYCLES,
        help=f"max cycles to run (default {DEFAULT_MAX_CYCLES})",
    )
    parser.add_argument(
        "--settle",
        type=float,
        default=DEFAULT_SETTLE_S,
        help=f"seconds between cycles (default {DEFAULT_SETTLE_S})",
    )
    parser.add_argument(
        "--poll",
        type=float,
        default=DEFAULT_POLL_S,
        help=f"worker liveness poll seconds (default {DEFAULT_POLL_S})",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_CYCLE_TIMEOUT_S,
        help=f"hard cycle deadline (default {DEFAULT_CYCLE_TIMEOUT_S})",
    )
    parser.add_argument("--lane", default=LANE, help=f"lane to drive (default {LANE})")
    parser.add_argument(
        "--repo-root",
        default=None,
        help=(
            "the tree the lane's PROMPT and git operations come from; "
            "defaults to the main checkout. Point it at a branch worktree to "
            "prove a cycle before the lane's own code has reached main - "
            "without it the launcher reads a prompt that is not there yet and "
            "the cycle records launch_failed"
        ),
    )
    parser.add_argument(
        "--control-dir",
        default=None,
        help="where the stop sentinels live (default ops/loop/control)",
    )
    parser.add_argument(
        "--reports-dir",
        default=None,
        help="where queue_loop.jsonl is written (default ops/loop/reports)",
    )
    parser.add_argument(
        "--ci-wait",
        type=float,
        default=DEFAULT_CI_WAIT_S,
        help=(f"seconds to block on each gating workflow (default {DEFAULT_CI_WAIT_S})"),
    )
    # A kill switch, not a mode. The gate is the point of this driver owning the
    # wait at all; turning it off is for a run whose CI is already known bad, or
    # for a box with no `gh` credentials.
    parser.add_argument(
        "--no-ci-gate", action="store_true", help="do not wait on CI after a cycle pushes"
    )
    parser.add_argument(
        "--local-suite",
        action="store_true",
        help=(
            "also run the full local suite between cycles and record its summary line and exit code"
        ),
    )
    parser.add_argument(
        "--once", action="store_true", help="run exactly one cycle - overrides --cycles"
    )
    args = parser.parse_args(argv)

    cycles = 1 if args.once else args.cycles
    cycle_log = None if args.reports_dir is None else Path(args.reports_dir) / CYCLE_LOG.name
    control_dir = None if args.control_dir is None else Path(args.control_dir)

    # THE LANE IS BOUND INTO THE GUARD, not read inside it, so the injected
    # seam stays the zero-argument callable every existing caller passes.
    guard = functools.partial(_driver_singleton, args.lane) if singleton is None else singleton
    try:
        with guard():
            summary = run_loop(
                max_cycles=cycles,
                settle_s=args.settle,
                poll_s=args.poll,
                cycle_timeout_s=args.timeout,
                ci_gate=not args.no_ci_gate,
                ci_wait_s=args.ci_wait,
                local_suite=args.local_suite,
                lane=args.lane,
                control_dir=control_dir,
                repo_root=(None if args.repo_root is None else Path(args.repo_root)),
                cycle_log=cycle_log,
            )
    except _mod("winmutex").MutexTimeout:
        # Not an error condition, a REFUSAL - and it must be loud, because the
        # symptom of two drivers is invisible at a glance: both survive, both
        # look busy, and each spends up to ten minutes per cycle losing the
        # acquire race to the other while their rows interleave in one ledger.
        #
        # BOTH GUARDS ARE NAMED, and the exception is NOT rendered - str() on a
        # caught object is the personal-data channel non-negotiable 12 closes,
        # and tests/test_exception_rendering.py walks every tracked module for
        # it. Which of the two refused is already in the log: winmutex emits an
        # ACQUIRED line for the one that was taken, and nothing for the one that
        # was not.
        _emit(
            f"queue-loop refused: one of the two run-length guards is already "
            f"held. Per lane and checkout: {driver_mutex(args.lane)} for lane "
            f"{args.lane!r}. Box-wide over the working directory: "
            f"{worktree_mutex(_mod('lane_launcher').worktree_path(args.lane))}. "
            f"The second is held by ANY clone driving that directory. Stop that "
            f"one first: taskkill /F /T /PID <pid>"
        )
        return EXIT_ALREADY_RUNNING

    _emit(f"queue-loop done: {summary['cycles_run']} cycle(s), stopped_by={summary['stopped_by']}")
    if summary["cycles_run"] == 0 and summary["stopped_by"] in STOP_NAMES:
        sentinel = stop_path_for(summary["stopped_by"], control_dir)
        _emit(
            f"queue-loop refused: {summary['stopped_by']} was ALREADY present "
            f"at {sentinel} - zero cycles ran. Delete that file to run."
        )
        return EXIT_STOP_SENTINEL
    # Checked AFTER the sentinel branch and independently of cycles_run: a hard
    # stop always ran at least one cycle, so the two cannot collide.
    stopped = summary["stopped_by"]
    if stopped == OUTCOME_KILL_FAILED:
        _emit(
            "queue-loop ALERT: a worker outlived its kill - treat the lane "
            "worktree as having a possible live writer and check it by hand "
            "before firing again."
        )
    if stopped == STOPPED_BY_CI_RED:
        _emit(
            "queue-loop ALERT: CI went RED on a pushed sha - the night stopped "
            "rather than stack more rows onto a broken tree. Read the last row "
            f"of {CYCLE_LOG.name} for the run id, fix the red, then fire again."
        )
    numbered = _STOP_EXIT.get(stopped)
    if numbered is not None:
        # THE SPECIFIC WORDS WIN. A hard stop names its own cause, and that
        # number is more useful than "nothing shipped" even when both are true.
        return numbered
    if stopped not in _SUCCESS_STOPS:
        _emit(
            f"queue-loop ALERT: stopped_by={stopped!r} carries no exit code and "
            f"is not a permitted success word - refusing to report it as a good "
            f"night. Add it to _STOP_EXIT or to _SUCCESS_STOPS."
        )
        return EXIT_UNKNOWN_STOP
    if not any(_is_progress(record) for record in summary["records"]):
        # THE INVARIANT, HELD WHERE A COUNTER CANNOT REACH. Every counter needs
        # three consecutive cycles; `--once` grants one, and a held lane, a
        # refused launch or a single completion that committed nothing each
        # exited 0 under a budget that small. The WORD stays whatever the loop
        # chose - the night really did end that way - but the number says
        # nothing was shipped.
        _emit(
            f"queue-loop: {summary['cycles_run']} cycle(s) ran and none of them "
            f"shipped - reporting no progress rather than success."
        )
        return EXIT_NO_PROGRESS
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
