#!/usr/bin/env python3
"""CS-993 - the local suite step is rationed, so two lanes never run one at once.

THE DEFECT IS MEASURED ON THIS BOX, NOT PREDICTED. Three projects' pytest runs
at once killed a suite here: it reported a pass count and one error while over
two thousand tests never ran. Two parallel xdist suites exhaust the Windows fork
budget and the failures land on UNRELATED subprocess tests, so resource
exhaustion reads as a scatter of flakes. CS-992 made a second lane startable,
which turns that from a cross-project hazard into an in-repo one: an unattended
lane writing a green it did not earn is worse than a lane that is merely slow,
because the ledger row looks the same either way.

WHAT IS GRADED ACROSS REAL PROCESSES AND WHAT IS NOT, stated plainly because the
difference is the whole value of the two required arms. The blocking arm and the
killed-holder arm each spawn a SECOND interpreter and drive the real slot on
disk; nothing about their verdict rests on one process pretending to be two. The
remaining arms are in-process and grade wiring, the loud fail-open, and the
read-does-not-write rule - each of which is a property of this process's own
code path and needs no second process to observe.

THE CONTROL COMES BEFORE THE MEASUREMENT IN BOTH PROCESS ARMS. Each waits for
the child to report that it holds the slot and asserts the parent can SEE that
hold, naming the child's own pid, before it measures anything. Without it a
ration that never engaged and a ration that engaged correctly produce the same
green, which is how a vacuous arm is written.

NO POPULATION IS GRADED BY A FLOOR. The blocking arm compares the signal files
present at the moment the body entered against the protocol's declared set by
set EQUALITY, and the fail-open arm compares an exact line count. A floor grades
the bottom of a range and passes over everything above it.

ASSERTIONS ARE MADE ON SCALARS BOUND FIRST. Every path here lives under
``tmp_path``, and pytest renders a failing assertion's sub-expressions with their
own reprs independently of the message, so an assertion written over a Path
would print a temporary directory into the report.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest
from ops.loop import queue_loop, ration

#: The signal files the two process arms exchange through ``tmp_path``. Declared
#: once and handed to the child on its command line, so the child and the parent
#: cannot disagree about a name.
SIGNAL_ACQUIRED = "child_acquired"
SIGNAL_GO = "go"
SIGNAL_RELEASED = "child_released"

#: The full set the blocking arm expects to find on disk at the moment its body
#: enters. Compared against a directory walk, which is a second enumeration.
BLOCKING_PROTOCOL = (SIGNAL_ACQUIRED, SIGNAL_GO, SIGNAL_RELEASED)

#: Bounds, so a wedged probe is a failure rather than a hang. Neither is a
#: budget for anything: the arms finish in well under a second when they pass.
_CHILD_START_TIMEOUT_S = 60.0
_CHILD_EXIT_TIMEOUT_S = 60.0
_POLL_S = 0.02

#: Exit codes the child scripts use to report what went wrong, mapped to what
#: each one means, so a failure in the child is legible from the parent's
#: assertion rather than from a log nobody reads. The child spells the integers
#: literally because it is source text rather than an import.
_CHILD_EXITS = {
    11: "the child was refused the slot nothing was holding",
    12: "the child timed out waiting to be told to release",
}

#: The child that takes the slot, announces it, and releases only when told.
_HOLD_THEN_RELEASE = """
import os
import sys
import time
from pathlib import Path

repo_root, root, acquired, go, released = sys.argv[1:6]
sys.path.insert(0, repo_root)
from ops.loop import ration

claim = ration.try_acquire(holder="probe-child", run_id="child", root=root)
if not claim["ok"]:
    sys.exit(11)
Path(acquired).write_text(str(os.getpid()), encoding="utf-8")
deadline = time.monotonic() + 120.0
while not Path(go).exists():
    if time.monotonic() > deadline:
        sys.exit(12)
    time.sleep(0.02)
ration.release(claim["token"], root=root)
Path(released).write_text("released", encoding="utf-8")
"""

#: The child that takes the slot and then never gives it up. It is KILLED rather
#: than asked to stop, which is the whole point: a hard kill skips every
#: ``finally``, so a ration released only on the way out stays held forever.
_HOLD_FOREVER = """
import os
import sys
import time
from pathlib import Path

repo_root, root, acquired = sys.argv[1:4]
sys.path.insert(0, repo_root)
from ops.loop import ration

claim = ration.try_acquire(holder="probe-child", run_id="child", root=root)
if not claim["ok"]:
    sys.exit(11)
try:
    Path(acquired).write_text(str(os.getpid()), encoding="utf-8")
    time.sleep(600.0)
finally:
    ration.release(claim["token"], root=root)
"""


def _repo_root() -> Path:
    """The repository root, derived from this file rather than from a constant."""
    return Path(__file__).resolve().parents[2]


def _write_child(tmp_path: Path, name: str, source: str) -> Path:
    """Drop one child script into the test's own directory and return its path."""
    script = tmp_path / name
    script.write_text(source, encoding="utf-8")
    return script


def _await_file(path: Path, proc: subprocess.Popen) -> None:
    """Block until the child announces itself, or fail with what it did instead.

    A child that died before announcing is reported by its EXIT CODE rather than
    by a timeout, because a timeout says nothing about which of the two failed.
    """
    deadline = time.monotonic() + _CHILD_START_TIMEOUT_S
    while not path.exists():
        code = proc.poll()
        if code is not None:
            why = _CHILD_EXITS.get(code, "the child died for a reason it has no word for")
            pytest.fail(f"the child exited {code} before it announced the slot - {why}")
        if time.monotonic() > deadline:
            pytest.fail("the child never announced the slot")
        time.sleep(_POLL_S)


def test_a_waiting_process_enters_the_ration_only_after_the_holder_releases(
    tmp_path: Path,
) -> None:
    root = tmp_path / "ration"
    signals = tmp_path / "signals"
    signals.mkdir()
    acquired = signals / SIGNAL_ACQUIRED
    go = signals / SIGNAL_GO
    released = signals / SIGNAL_RELEASED
    script = _write_child(tmp_path, "hold_then_release.py", _HOLD_THEN_RELEASE)

    proc = subprocess.Popen(
        [
            sys.executable,
            str(script),
            str(_repo_root()),
            str(root),
            str(acquired),
            str(go),
            str(released),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        _await_file(acquired, proc)

        # THE CONTROL. Before anything is measured, the parent must be able to
        # SEE the child's hold and name the process holding it. A ration that
        # never engaged would sail through every assertion below for the wrong
        # reason.
        held = ration.slot_state(root=root)
        held_state = str(held["state"])
        held_pid = held["pid"]
        child_pid = int(acquired.read_text(encoding="utf-8"))
        assert held_state == ration.RUNNING, (
            "the parent cannot see the child's hold, so nothing below measures "
            f"the ration - the slot reads {held_state}"
        )
        assert held_pid == child_pid, (
            "the slot names a process other than the child that took it, so the "
            "hold the arm goes on to wait out is not the child's"
        )

        # The ONLY thing that releases the child is the parent's own wait. A
        # ration that did not block never sleeps, never writes `go`, and the
        # child is therefore still holding when the body runs.
        def release_on_first_wait(seconds: float) -> None:  # noqa: ARG001 - seam shape
            go.write_text("go", encoding="utf-8")
            time.sleep(_POLL_S)

        present_at_entry: list[str] = []
        holder_at_entry: list[object] = []
        with ration.hold_suite_slot(
            holder="probe-parent",
            run_id="parent",
            root=root,
            sleep=release_on_first_wait,
            emit=lambda line: None,  # noqa: ARG005 - the arm reads state, not prose
        ):
            present_at_entry.extend(sorted(p.name for p in signals.iterdir()))
            holder_at_entry.append(ration.slot_state(root=root)["pid"])

        expected = sorted(BLOCKING_PROTOCOL)
        assert present_at_entry == expected, (
            "the body entered while the protocol was incomplete, so the second "
            "process ran its suite step on top of the first one's"
        )
        entered_as = holder_at_entry[0]
        assert entered_as == os.getpid(), (
            "the body ran without the slot naming this process, so the ration "
            "was not actually held while the step ran"
        )
        after = str(ration.slot_state(root=root)["state"])
        assert after == ration.FREE, (
            f"the ration was still {after} after the block exited, so the next "
            "lane would wait on a slot nobody holds"
        )
        assert proc.wait(timeout=_CHILD_EXIT_TIMEOUT_S) == 0, (
            "the child did not exit cleanly, so its half of the protocol is not "
            "evidence about anything"
        )
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait(timeout=_CHILD_EXIT_TIMEOUT_S)


def test_a_killed_holder_leaves_the_suite_ration_acquirable(tmp_path: Path) -> None:
    root = tmp_path / "ration"
    signals = tmp_path / "signals"
    signals.mkdir()
    acquired = signals / SIGNAL_ACQUIRED
    script = _write_child(tmp_path, "hold_forever.py", _HOLD_FOREVER)

    proc = subprocess.Popen(
        [sys.executable, str(script), str(_repo_root()), str(root), str(acquired)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        _await_file(acquired, proc)

        # THE CONTROL, again before the measurement: the hold has to be visible
        # first, or "acquirable after the kill" is a statement about a ration
        # that was never taken.
        before = ration.slot_state(root=root)
        before_state = str(before["state"])
        before_pid = before["pid"]
        child_pid = int(acquired.read_text(encoding="utf-8"))
        assert before_state == ration.RUNNING, (
            f"the slot reads {before_state} while the child holds it, so the "
            "kill below would be killing a holder of nothing"
        )
        assert before_pid == child_pid, (
            "the slot names a process other than the child, so the kill below "
            "would not be killing the holder"
        )
    finally:
        proc.kill()
        proc.wait(timeout=_CHILD_EXIT_TIMEOUT_S)

    # A HARD KILL SKIPS THE `finally`. The slot file is therefore still on disk,
    # and that is asserted rather than assumed: if the release DID run, the rest
    # of this arm would be grading an empty directory and would pass for a
    # reason that has nothing to do with the ration.
    survived = ration.slot_path(root=root).exists()
    assert survived, (
        "the killed holder's slot file is gone, so the child released on its "
        "way out and this arm never observed the state it exists to grade"
    )

    after = ration.slot_state(root=root)
    after_state = str(after["state"])
    assert after_state == ration.RECLAIMABLE, (
        f"a slot whose holder is dead reads {after_state}, so the lane is wedged "
        "behind a process that no longer exists"
    )

    claim = ration.try_acquire(holder="probe-parent", run_id="parent", root=root)
    claimed = bool(claim["ok"])
    assert claimed, (
        "the ration refused a slot whose holder is dead, which is the wedge "
        "that is worse than no ration at all because it looks like patience"
    )
    ration.release(claim["token"], root=root)


def test_the_drivers_suite_step_runs_inside_the_ration(tmp_path: Path) -> None:
    root = tmp_path / "ration"
    seen: list[str] = []

    def fake_suite(*, cwd, monotonic):  # noqa: ARG001 - the driver's seam shape
        seen.append(str(ration.slot_state(root=root)["state"]))
        return {"ok": True, "summary": "1 passed", "exit_code": 0}

    record: dict[str, object] = {"outcome": queue_loop.OUTCOME_COMPLETED}
    held_before = str(ration.slot_state(root=root)["state"])
    assert held_before == ration.FREE, (
        "the slot was already held before the driver ran, so an observation of "
        "RUNNING inside the step would prove nothing about the driver"
    )

    queue_loop.run_suite_step(
        record,
        lane=queue_loop.LANE,
        worktree=tmp_path / "tree",
        run_id="wiring",
        suite=fake_suite,
        root=root,
        sleep=lambda seconds: None,  # noqa: ARG005 - never reached, nothing holds
        monotonic=time.monotonic,
        emit=lambda line: None,  # noqa: ARG005 - the arm reads state, not prose
    )

    assert seen == [ration.RUNNING], (
        "the driver's suite step did not observe the ration held while it ran, "
        f"so the step is outside the ration - it saw {seen}"
    )
    after = str(ration.slot_state(root=root)["state"])
    assert after == ration.FREE, "the driver left the ration held after its step"
    recorded = record.get("suite")
    assert recorded == {"ok": True, "summary": "1 passed", "exit_code": 0}, (
        "the step's verdict did not reach the record, so a rationed step would "
        "leave the cycle with no acceptance at all"
    )


def test_reading_the_ration_state_never_writes(tmp_path: Path) -> None:
    root = tmp_path / "ration"
    root.mkdir(parents=True)
    slot = ration.slot_path(root=root)
    # A DEAD holder, written by hand. Pid 0 is never a live process, so this is
    # the state a reader is most tempted to clean up on the spot.
    slot.write_text(
        json.dumps({"pid": 0, "holder": "gone", "run_id": "x", "ts": 0.0}),
        encoding="utf-8",
    )
    before = sorted(p.name for p in root.iterdir())

    state = str(ration.slot_state(root=root)["state"])
    assert state == ration.RECLAIMABLE, (
        f"a slot held by a dead pid reads {state}, so the read below is not "
        "exercising the path that is tempted to clear it"
    )

    after = sorted(p.name for p in root.iterdir())
    assert after == before, (
        "reading the ration state changed what is on disk, so two pollers can "
        "race each other into a reclaim and a rendering pass mutates the "
        "control plane"
    )


def test_a_wait_that_reaches_its_ceiling_proceeds_unrationed_and_says_so(
    tmp_path: Path,
) -> None:
    root = tmp_path / "ration"
    root.mkdir(parents=True)
    slot = ration.slot_path(root=root)
    # HELD BY THIS PROCESS, so the probe reads RUNNING for as long as the arm
    # runs and the wait can never succeed.
    slot.write_text(
        json.dumps({"pid": os.getpid(), "holder": "wedged", "run_id": "x", "ts": time.time()}),
        encoding="utf-8",
    )
    held = str(ration.slot_state(root=root)["state"])
    assert held == ration.RUNNING, (
        f"the wedged slot reads {held}, so the wait below would succeed and the "
        "ceiling path this arm grades would never be entered"
    )

    ticks = iter((0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0))
    lines: list[str] = []
    ran: list[str] = []
    with ration.hold_suite_slot(
        holder="probe",
        run_id="ceiling",
        root=root,
        ceiling_s=1.0,
        sleep=lambda seconds: None,  # noqa: ARG005 - the fake clock does the moving
        monotonic=lambda: next(ticks),
        emit=lines.append,
    ):
        ran.append("body")

    assert ran == ["body"], (
        "the ceiling refused the step instead of proceeding, which turns a slow "
        "night into a dead one"
    )
    loud = len([line for line in lines if ration.UNRATIONED in line])
    assert loud == 1, (
        f"the unrationed step emitted {loud} marker lines, so the one occasion "
        "the ration did not hold is not findable in the night's log"
    )
    still_held = str(ration.slot_state(root=root)["state"])
    assert still_held == ration.RUNNING, (
        "the unrationed path took or cleared the wedged holder's slot, which is "
        "a second writer in the same directory rather than a loud fall-through"
    )
