#!/usr/bin/env python3
"""CS-1000 - the `queue` lane must run MORE THAN ONE cycle per driver launch.

WHAT THIS GRADES, AND WHY AN ARM THAT DRIVES ONE CYCLE DOES NOT. The lane
completed cycle 1 and then refused every launch for the rest of the night, twice
over, while the whole existing suite stayed green. Every launcher arm in the
tree drives exactly ONE launch, and the defect lives entirely in what the FIRST
cycle leaves behind - so the population those arms grade does not contain it.
The arm below drives two CONSECUTIVE cycles through the real lock, the real
launcher and the real driver, and it is the first thing in this repository that
can see the fault at all.

THE MEASURED CAUSE. ``ops/loop/lanes.py`` carries process-global state -
``_OWNED``, the map that decides whether a release is ours. Both the driver and
the launcher try the package route ``ops.loop.lanes`` first and fall back to
loading ``lanes.py`` BY PATH, each under its own private name. The detached
driver is started as ``pythonw <repo>/ops/loop/queue_loop.py``, so ``sys.path``
carries ``ops/loop`` and NOT the repository root: the package route fails for
both, each falls back, and the two private names produce TWO module objects with
TWO ``_OWNED`` maps. Cycle 1's re-point is recorded in the launcher's copy and
its release is refused by the driver's, so the launcher's copy keeps cycle 1's
identity forever and refuses to re-point every later cycle -
``repoint_refused`` - killing each freshly spawned worker on the way out.

THE CONTROL IS INSIDE THE PROBE, AND IT IS NOT DECORATION. Under pytest the
repository root IS on ``sys.path``, both routes succeed, both modules are the
same object and nothing can go wrong - so an in-process arm would pass before
the fix for the wrong reason. The probe asserts the repo root is absent and that
``ops`` cannot be imported BEFORE it measures anything, and the arm fails if
that control did not hold.

ASSERTIONS ARE MADE ON SCALARS BOUND FIRST. Every path here lives under
``tmp_path``, and pytest renders a failing assertion's sub-expressions with
their own reprs independently of the message (CS-850), so an assertion written
over a Path would print a temporary directory into the report.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
from ops.loop import lane_launcher, queue_loop

# CS-1104 - the live-channel audit, AUTOUSE by import: any test here that lists or
# opens `moon_sync_inbox/` or its seen store fails at teardown. One owner of the
# hook, in tests/test_queue_loop.py; tests/ops has no conftest to share it through.
from tests.test_queue_loop import channel_audit  # noqa: F401

#: Long enough for two cycles that spawn nothing, short enough that a wedged
#: probe is a failure rather than a hang.
_PROBE_TIMEOUT_S = 300

#: The pid the probe's fake spawn hands back. Chosen at runtime from a pid the
#: operating system is not using, because cycle 2 must find cycle 1's worker
#: DEAD - that is the state the live failure was measured in.
_PROBE_CYCLES = 2

#: A stand-in worktree for the reason arms. Never touched: those arms inject
#: both the launcher and the worktree, so no lane code resolves either.
_FAKE_WORKTREE = "cs-lane-queue-probe"

#: WHICH FILE FALLS BACK FIRST. Each ordering publishes lanes.py from a
#: DIFFERENT file, so each grades a different registration site; driving one
#: ordering leaves the other site a mutant no value can kill.
_BIND_ORDERS = ("driver_first", "launcher_first")

_PROBE = '''
"""Drive two consecutive queue-lane cycles under the DETACHED driver's sys.path.

argv: <repo-root> <scratch-root>.  Prints one JSON object on stdout.
"""

import importlib.util
import json
import sys
from pathlib import Path

REPO = Path(sys.argv[1]).resolve()
SCRATCH = Path(sys.argv[2]).resolve()
LOOP = REPO / "ops" / "loop"

# EXACTLY what `pythonw <repo>/ops/loop/queue_loop.py` gets: the script's own
# directory, and no repository root anywhere.
sys.path[:] = [str(LOOP)] + [p for p in sys.path[1:] if p and Path(p).resolve() != REPO]

result = {"ops_importable": importlib.util.find_spec("ops") is not None}
if result["ops_importable"]:
    print(json.dumps(result))
    raise SystemExit(0)


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


ql = _load("cs1000_queue_loop_probe", LOOP / "queue_loop.py")

# WHICH FILE FALLS BACK FIRST IS THE WHOLE VARIABLE. Whichever one loads
# lanes.py by path is the one that publishes it under the canonical name, so
# each ordering grades a DIFFERENT registration site. Driving only one leaves
# the other site an equivalent mutant nothing can kill.
if sys.argv[3] == "launcher_first":
    launcher = ql._mod("lane_launcher")
    lanes = ql._mod("lanes")
else:
    lanes = ql._mod("lanes")
    launcher = ql._mod("lane_launcher")
result["same_lanes_module"] = lanes is launcher.lanes
result["order"] = sys.argv[3]

root = SCRATCH / "tree"
(root / "tools").mkdir(parents=True, exist_ok=True)
(root / "tools" / "headless-queue.md").write_text("stub prompt", encoding="utf-8")
base = SCRATCH / "wt"
tree = base / "cs-lane-queue"
(tree / ".git").mkdir(parents=True, exist_ok=True)
locks = SCRATCH / "lanes"
locks.mkdir(parents=True, exist_ok=True)
logs = SCRATCH / "logs"
logs.mkdir(parents=True, exist_ok=True)

# Cycle 2 must find cycle 1's worker DEAD, which is the live shape: the lane
# lock reads RECLAIMABLE, the driver reclaims it and acquires cleanly, and the
# refusal that follows is therefore the launcher's and not the lock's.
dead = next(pid for pid in range(30000, 60000, 4) if not lanes.pid_alive(pid))
result["worker_pid"] = dead


class _Proc:
    pid = dead


def _spawn(_runner, _prompt, _cwd, _log):
    return _Proc()


killed = []
launcher._kill = killed.append
reasons = []
_real = launcher.launch_lane


def _launch(lane, **kw):
    try:
        return _real(lane, base=base, root=root, log_dir=logs, spawn=_spawn, **kw)
    except launcher.LaneLaunchError as exc:
        reasons.append(exc.reason)
        raise


rows = []
for cycle in (1, 2):
    row = ql.run_cycle(
        cycle,
        lane="queue",
        worktree=str(tree),
        repo_root=root,
        acquire=lambda lane, **kw: lanes.try_acquire_lane(lane, root=locks, **kw),
        release=lambda token: lanes.release_lane(token, root=locks),
        launch=_launch,
        alive=lambda _pid: False,
        proc_started=lambda _pid: 1.0,
        stranger=lambda _pid, _started: False,
        kill=lambda _pid: None,
        sleep=lambda _s: None,
        poll_s=0,
        acquire_retries=1,
    )
    rows.append({"outcome": row["outcome"], "pid": row["pid"], "detail": row["detail"]})

result["cycles"] = rows
result["reasons"] = reasons
result["killed"] = killed
result["lock_left_on_disk"] = (locks / lanes.LOCK_NAME).exists()
print(json.dumps(result))
'''


def _repo_root() -> Path:
    """The working tree this test file lives in, derived from its own location."""
    return Path(__file__).resolve().parents[2]


def _run_probe(tmp_path: Path, order: str = "driver_first") -> dict:
    """Run the two-cycle probe in a subprocess and hand back its JSON answer."""
    script = tmp_path / f"cs1000_probe_{order}.py"
    script.write_text(_PROBE, encoding="utf-8")
    scratch = tmp_path / f"scratch_{order}"
    scratch.mkdir()
    done = subprocess.run(
        [sys.executable, str(script), str(_repo_root()), str(scratch), order],
        capture_output=True,
        text=True,
        timeout=_PROBE_TIMEOUT_S,
        check=False,
    )
    if done.returncode != 0:
        # The probe's own traceback would carry tmp_path, so only the LAST line
        # - the exception type and message - is surfaced, and paths are not.
        tail = (done.stderr or "").strip().splitlines()[-1:] or ["no stderr"]
        raise AssertionError(f"the probe did not complete: {tail[0][:200]}")
    answer = json.loads(done.stdout.strip().splitlines()[-1])
    assert isinstance(answer, dict), "the probe printed something that is not a JSON object"
    return answer


@pytest.mark.parametrize("order", _BIND_ORDERS)
def test_two_consecutive_lane_cycles_both_reach_a_spawned_worker(
    tmp_path: Path, order: str
) -> None:
    """THE ARM CS-1000 EXISTS FOR - cycle 2 must start a worker, not refuse one.

    Reddens the moment the second launch is refused, which is what a night that
    completes one row and then burns eleven cycles looks like from here.

    Run once per bind ORDER. The driver reaches lanes.py first on a real
    detached fire; a consumer that imports the launcher on its own reaches it
    the other way round, and the two publish it from different files.
    """
    answer = _run_probe(tmp_path, order)

    vacuous = answer.get("ops_importable")
    assert vacuous is False, (
        "the control failed: the repository root was still importable in the probe, "
        "so both modules took the package route and the arm measured nothing"
    )

    cycles = answer.get("cycles") or []
    population = len(cycles)
    assert population == _PROBE_CYCLES, "the probe did not run both cycles"

    refused = [row["outcome"] for row in cycles if row["outcome"] != queue_loop.OUTCOME_COMPLETED]
    assert refused == [], f"a cycle did not complete: {refused} reasons={answer.get('reasons')}"

    pidless = [index for index, row in enumerate(cycles, 1) if not row["pid"]]
    assert pidless == [], f"cycle(s) {pidless} reached no spawned worker"

    executed = answer.get("killed")
    assert executed == [], "a freshly spawned worker was killed by the launcher"

    stranded = answer.get("lock_left_on_disk")
    assert stranded is False, "the lane lock outlived the cycle that took it"

    one_module = answer.get("same_lanes_module")
    assert one_module is True, (
        "the driver and the launcher hold TWO lanes modules, so each has its own "
        "ownership map and cycle 1's release is refused by the copy that recorded it"
    )


def test_a_second_cycle_is_not_graded_by_the_first_alone(tmp_path: Path) -> None:
    """The arm above is not satisfiable by one cycle - the probe must run two.

    Without this, a probe that silently stopped after cycle 1 would leave the
    arm above asserting over a single row and passing for the wrong reason.
    """
    answer = _run_probe(tmp_path)
    cycles = answer.get("cycles") or []
    population = len(cycles)
    assert population > 1, "the probe graded a single cycle - the defect lives after cycle 1"
    ran = answer.get("order")
    assert ran in _BIND_ORDERS, "the probe did not report which bind order it took"


# ---------------------------------------------------------------------------
# Half B - every refusal reaches the row NAMED.
# ---------------------------------------------------------------------------


def _cycle_seams(launch) -> dict:
    """Seams for a `run_cycle` that claims nothing, spawns nothing and waits none."""
    return {
        "worktree": _FAKE_WORKTREE,
        "run_id": "probe",
        "acquire": lambda _lane, **_kw: {"ok": True, "token": "token"},
        "release": lambda _token: True,
        "alive": lambda _pid: False,
        "proc_started": lambda _pid: 1.0,
        "stranger": lambda _pid, _started: False,
        "launch": launch,
        "kill": lambda _pid: None,
        "sleep": lambda _s: None,
        "clock": lambda: 0.0,
        "monotonic": lambda: 0.0,
    }


def test_every_launch_reason_reaches_the_row_named() -> None:
    """ONE ARM PER REASON, over a vocabulary DERIVED from the launcher.

    The population is the launcher's own tuple rather than a list written here:
    a hand-listed vocabulary is one whose members can be deleted with the suite
    staying green, which is the whole failure this closes.

    Sub-arms are collected and asserted as a LIST of offenders rather than one
    assert per loop iteration, so a single red run names every reason that was
    dropped instead of only the first.
    """
    vocabulary = lane_launcher.LAUNCH_REASONS
    population = len(vocabulary)
    assert population > 0, "the vocabulary is empty - the sweep would be vacuous"

    dropped = []
    for code in vocabulary:

        def _fails(_lane, _code=code, **_kw):
            raise lane_launcher.LaneLaunchError("refused", reason=_code)

        row = queue_loop.run_cycle(1, **_cycle_seams(_fails))
        outcome = row["outcome"]
        detail = row["detail"]
        if outcome != queue_loop.OUTCOME_LAUNCH_FAILED or detail != f"LaneLaunchError: {code}":
            dropped.append((code, outcome, detail))

    assert dropped == [], "a launch reason did not reach the row as its own machine word"


def test_the_reason_vocabulary_equals_the_modules_reason_constants() -> None:
    """SET EQUALITY against a SECOND, independent enumeration - never a floor.

    A floor over the number of reasons grades the bottom of a range and is
    satisfied by the strongest member while the weakest goes unmeasured - the
    CS-988 defect class, which this repository has measured nine times. The
    second enumeration here is the module's own ``REASON_*`` constants, walked
    out of its namespace: deleting a member from ``LAUNCH_REASONS`` leaves its
    constant standing and this arm reddens, and adding a constant without
    wiring it into the tuple reddens too.
    """
    declared = {
        value
        for name, value in vars(lane_launcher).items()
        if name.startswith("REASON_") and isinstance(value, str)
    }
    vocabulary = set(lane_launcher.LAUNCH_REASONS)
    assert declared, "no REASON_ constants were found - the second enumeration is empty"
    assert vocabulary == declared, (
        "the closed vocabulary and the module's own reason constants disagree; "
        "a code that is declared but not enrolled is silently discarded by the driver"
    )

    driver_copy = set(queue_loop._LAUNCH_REASONS)  # noqa: SLF001 - the copy under test
    assert driver_copy == vocabulary, (
        "the driver's copy of the vocabulary and the launcher's disagree; "
        "a reason the driver does not hold degrades to a bare type name"
    )
