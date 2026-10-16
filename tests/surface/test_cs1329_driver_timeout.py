"""CS-1329 - a node driver that runs out of time says WHICH phase ran out.

THE RED THIS ANSWERS. A tier2 windows fast shard failed
``test_panel_solve.py::test_the_driver_stand_in_is_exactly_the_shared_harnesses_surface``
with a bare ``subprocess.TimeoutExpired`` at 60 s - the module's first node
spawn. A bare timeout cannot tell node's cold start from a driver that hung,
so the reading named neither and the next one would not either.

WHAT EVERY ARM BELOW HOLDS A SPAWN SITE TO. Each of the seven node spawn sites
in ``tests/surface/`` runs its driver through ONE shared helper, so a timeout in
either phase fails with a message naming the elapsed seconds, whether the
driver's start marker arrived, and the partial stdout and stderr. Each site is
driven here with its OWN run limit squeezed, so an arm proves that site routes
through the helper rather than the helper being proved once in isolation.

NO ARM HERE CAN BE FAILED BY A SLOW BUT CORRECT RUNNER. A run phase that must
time out never ends by construction; a start-up that must outlast a run limit
is a planted spin with a floor; a run phase that must fit inside a limit
lingers a fixed second against a limit three times that.
"""

from __future__ import annotations

import re
import shutil
import warnings
from typing import TYPE_CHECKING

import pytest

from tests.surface import (
    panel_harness,
    test_panel_global_scope,
    test_panel_optimize,
    test_panel_power,
    test_panel_seam,
    test_panel_solve,
)

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path
    from types import ModuleType

#: The run limit a site is squeezed to. Its run phase is made to NEVER end
#: (:func:`plant_endless_run`), so the timeout is certain at any runner speed.
MODEST_RUN_LIMIT: float = 0.5

#: The elapsed figure every diagnosis must carry.
ELAPSED: re.Pattern[str] = re.compile(r"elapsed \d+\.\d\d s")

#: The run limit every site carried before CS-1329, and still carries.
RUN_LIMIT: float = 60.0

#: The not-charged arm's three times. The planted start-up outlasts the run
#: limit, so a deadline counted from the spawn has passed before the marker;
#: the driver then lingers a fixed second, so it is still running when that
#: wrong deadline is checked, and well inside the limit counted from the marker.
SLOW_START_MS: int = 3500
QUICK_RUN_LIMIT: float = 3.0
LINGER_MS: int = 1000

#: A planted start-up for the slow-start line arms, and the line they set
#: below it. Only the start-up's FLOOR matters, so a slow runner cannot fail them.
PROBE_START_MS: int = 1000
PROBE_LINE_SECONDS: float = 0.5

#: A slow-start line no runner reaches.
UNREACHABLE_LINE_SECONDS: float = 1e9

#: The start-up reading a pass reports, in the slow-start line's words.
STARTUP_READING: re.Pattern[str] = re.compile(r"reached its start marker in \d+\.\d\d s")

#: A diagnosis's start-up figure, read back as a number.
STARTUP_FIGURE: re.Pattern[str] = re.compile(r"start marker arrived: yes, (\d+\.\d\d) s after")

#: A diagnosis's run-phase figure, read back as a number.
RAN_FIGURE: re.Pattern[str] = re.compile(r"the driver then ran (\d+\.\d\d) s against")

#: How far a reported run may sit under its limit and still have reached it:
#: the .2f rounding, and a Windows wait that truncates to whole milliseconds.
REPORT_SLACK: float = 0.05


def node_or_fail() -> str:
    """The interpreter off PATH. Absent node FAILS: a skip would grade nothing."""
    node = shutil.which("node")
    if node is None:
        pytest.fail("node is not on PATH, so no driver ran and nothing was graded")
    return node


def plant_slow_start(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, ms: int, writes: str = ""
) -> None:
    """Make every node this test starts spin ``ms`` BEFORE the start marker.

    The spin is a preload node runs ahead of the marker's, through
    NODE_OPTIONS, which is where a cold start's time sits too. ``writes`` is
    JavaScript run after the spin and still ahead of the marker.
    """
    slow = tmp_path / "slow_start.cjs"
    slow.write_bytes(
        f"var until = Date.now() + {ms};\nwhile (Date.now() < until) {{}}\n{writes}".encode("ascii")
    )
    monkeypatch.setenv("NODE_OPTIONS", f'--require "{slow.as_posix()}"')


def plant_endless_run(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Make every node this test starts spin forever AFTER the start marker.

    An ``--import`` preload in NODE_OPTIONS runs after every ``--require``
    preload, the marker's included, and before the driver - so the run phase
    of ANY site's driver never ends, and its run limit is certain to fire.
    """
    endless = tmp_path / "endless_run.mjs"
    endless.write_bytes(b"for (;;) {}\n")
    monkeypatch.setenv("NODE_OPTIONS", f'--import "{endless.as_uri()}"')


def quick_driver(tmp_path: Path, linger_ms: int = 0) -> Path:
    """A driver that writes one word and exits, after ``linger_ms`` if given."""
    script = tmp_path / "quick.cjs"
    script.write_bytes(
        (
            'setTimeout(function () { process.stdout.write("quick-1329"); }, '
            + str(linger_ms)
            + ");\n"
        ).encode("ascii")
    )
    return script


#: The two endings :func:`startup_reading` names: a clean pass of
#: :func:`quick_driver`, and a run-phase timeout after the marker.
CLEAN_RUN: str = "a clean pass"
RUN_PHASE_TIMEOUT: str = "a run-phase timeout"


def startup_reading(script: Path, run_timeout: float) -> tuple[float, float, str]:
    """Run ``script`` and read both phases' seconds back, however it ended.

    Returns:
        The start-up and run seconds - from the run, or read off a run-phase
        diagnosis - and :data:`CLEAN_RUN`, :data:`RUN_PHASE_TIMEOUT`, or the
        unexpected ending verbatim with -1.0 for both when no figure reads.
    """
    try:
        run = test_panel_seam.run_node(
            node_or_fail(), script, label="the quick driver", run_timeout=run_timeout
        )
    except pytest.fail.Exception as failure:
        # The named field, never the object (tests/test_exception_rendering.py).
        text = failure.msg or ""
        started = STARTUP_FIGURE.search(text)
        ran = RAN_FIGURE.search(text)
        if started is None or ran is None or "timed out in its run phase" not in text:
            return -1.0, -1.0, text
        return float(started.group(1)), float(ran.group(1)), RUN_PHASE_TIMEOUT
    clean = (
        run.returncode == 0
        and run.stdout == "quick-1329"
        and test_panel_seam.NODE_START_MARKER not in run.stderr
    )
    return run.startup_seconds, run.run_seconds, CLEAN_RUN if clean else repr(run)


def diagnosis(
    module: ModuleType,
    call: Callable[[], object],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> str:
    """Squeeze ``module``'s run limit, end no run, make the call, return the failure.

    Args:
        module: The module owning the spawn site and its ``NODE_TIMEOUT_SECONDS``.
        call: The site, bound to its arguments.
        tmp_path: Where the endless-run preload is written.
        monkeypatch: The fixture that restores the limit and NODE_OPTIONS.

    Returns:
        The ``pytest.fail`` message the site raised.
    """
    monkeypatch.setattr(module, "NODE_TIMEOUT_SECONDS", MODEST_RUN_LIMIT)
    plant_endless_run(tmp_path, monkeypatch)
    with pytest.raises(pytest.fail.Exception) as caught:
        call()
    return str(caught.value)


def assert_run_phase_diagnosis(text: str) -> None:
    """The run phase timed out against the SITE's limit, and the message says why."""
    assert "timed out in its run phase" in text, text
    assert ELAPSED.search(text), text
    assert "start marker arrived: yes" in text, text
    assert f"against its {MODEST_RUN_LIMIT:g} s run limit" in text, text
    assert "partial stdout" in text, text
    assert "partial stderr" in text, text


# ---------------------------------------------------------------------------
# a. The red: the solve driver's run limit, as the tier2 shard hit it
# ---------------------------------------------------------------------------


def test_a_solve_driver_past_its_run_limit_fails_with_a_diagnosis(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    text = diagnosis(
        test_panel_solve,
        lambda: test_panel_solve.drive(
            tmp_path, panel_harness.null_payload(), door=test_panel_solve.DOOR_NONE
        ),
        tmp_path,
        monkeypatch,
    )
    assert_run_phase_diagnosis(text)


# ---------------------------------------------------------------------------
# b. The six sibling sites, each through its own run limit
# ---------------------------------------------------------------------------


def test_the_shared_panel_harness_fails_with_a_diagnosis(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    text = diagnosis(
        panel_harness,
        lambda: panel_harness.mount(
            tmp_path, test_panel_solve.MODULE, panel_harness.null_payload()
        ),
        tmp_path,
        monkeypatch,
    )
    assert_run_phase_diagnosis(text)


def test_the_seam_harness_fails_with_a_diagnosis(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    text = diagnosis(
        test_panel_seam,
        lambda: test_panel_seam.run_seam(tmp_path, plant=False),
        tmp_path,
        monkeypatch,
    )
    assert_run_phase_diagnosis(text)


def test_the_power_bench_driver_fails_with_a_diagnosis(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    text = diagnosis(
        test_panel_power,
        lambda: test_panel_power.drive(tmp_path, panel_harness.null_payload()),
        tmp_path,
        monkeypatch,
    )
    assert_run_phase_diagnosis(text)


def test_the_optimize_bench_driver_fails_with_a_diagnosis(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    text = diagnosis(
        test_panel_optimize,
        lambda: test_panel_optimize.drive(tmp_path, panel_harness.null_payload()),
        tmp_path,
        monkeypatch,
    )
    assert_run_phase_diagnosis(text)


def test_the_global_scope_page_harness_fails_with_a_diagnosis(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    text = diagnosis(
        test_panel_global_scope,
        lambda: test_panel_global_scope.run_page(tmp_path, ()),
        tmp_path,
        monkeypatch,
    )
    assert_run_phase_diagnosis(text)


def test_the_global_scope_census_harness_fails_with_a_diagnosis(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    script = test_panel_global_scope.WEB_DIR / test_panel_solve.MODULE
    text = diagnosis(
        test_panel_global_scope,
        lambda: test_panel_global_scope.census(tmp_path, script),
        tmp_path,
        monkeypatch,
    )
    assert_run_phase_diagnosis(text)


# ---------------------------------------------------------------------------
# c. The two phases are told apart, which is the point of the marker
# ---------------------------------------------------------------------------


def test_a_node_that_never_reaches_the_driver_says_the_marker_never_came(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(test_panel_seam, "NODE_START_TIMEOUT_SECONDS", 0.0)
    with pytest.raises(pytest.fail.Exception) as caught:
        test_panel_solve.drive(
            tmp_path, panel_harness.null_payload(), door=test_panel_solve.DOOR_NONE
        )
    text = str(caught.value)
    assert "timed out in its start phase" in text, text
    assert ELAPSED.search(text), text
    assert "start marker arrived: no" in text, text
    assert "partial stdout" in text, text
    assert "partial stderr" in text, text


def test_a_driver_that_hangs_after_the_marker_is_read_as_a_hang(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    planted = tmp_path / "panel_spins.js"
    planted.write_bytes(b"for (;;) {}\n")
    monkeypatch.setattr(test_panel_solve, "NODE_TIMEOUT_SECONDS", MODEST_RUN_LIMIT)
    with pytest.raises(pytest.fail.Exception) as caught:
        test_panel_solve.drive(
            tmp_path,
            panel_harness.null_payload(),
            module=planted,
            door=test_panel_solve.DOOR_NONE,
        )
    text = str(caught.value)
    assert "timed out in its run phase" in text, text
    assert_run_phase_diagnosis(text)


def test_a_timeout_quotes_what_node_had_already_written(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A squeezed run limit quotes the output node wrote before it.

    The writes land AHEAD of the marker, so the run phase always finds them
    in the pipe, however slow the runner is.
    """
    plant_slow_start(
        tmp_path,
        monkeypatch,
        0,
        writes='var fs = require("node:fs");\n'
        'fs.writeSync(1, "partial-out-1329");\n'
        'fs.writeSync(2, "partial-err-1329\\n");\n',
    )
    script = tmp_path / "spins.cjs"
    script.write_bytes(b"for (;;) {}\n")
    with pytest.raises(pytest.fail.Exception) as caught:
        test_panel_seam.run_node(
            node_or_fail(), script, label="the spinning driver", run_timeout=MODEST_RUN_LIMIT
        )
    text = str(caught.value)
    assert "start marker arrived: yes" in text, text
    assert "partial-out-1329" in text, text
    assert "partial-err-1329" in text, text
    assert test_panel_seam.NODE_START_MARKER not in text, text


def test_node_start_up_is_never_charged_to_the_run_limit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A start-up longer than the run limit is never what fails the run.

    The planted start-up outlasts the run limit, and the driver lingers a fixed
    second after the marker. A deadline counted from the SPAWN has therefore
    passed before the marker, and is checked while the driver still lingers:
    that run times out having run about 0 s, and this arm is red. Counted from
    the MARKER, the run passes. The one other correct ending - a runner so slow
    that the lingering driver overruns the limit after the marker - is
    accepted only when the diagnosis shows the driver really ran the whole
    limit, which the wrong deadline can never show.
    """
    plant_slow_start(tmp_path, monkeypatch, SLOW_START_MS)
    startup, ran, ending = startup_reading(quick_driver(tmp_path, LINGER_MS), QUICK_RUN_LIMIT)
    assert ending == CLEAN_RUN or (
        ending == RUN_PHASE_TIMEOUT and ran >= QUICK_RUN_LIMIT - REPORT_SLACK
    ), (startup, ran, ending)
    assert startup >= SLOW_START_MS / 1000 - REPORT_SLACK, (startup, ran, ending)


# ---------------------------------------------------------------------------
# c2. A pass still says how long node took to start, past the slow-start line
# ---------------------------------------------------------------------------


def test_a_pass_whose_start_up_reached_the_slow_line_leaves_a_warning(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A slow start that passes is the red's own precursor, so it is visible."""
    monkeypatch.setattr(
        test_panel_seam, "NODE_SLOW_START_SECONDS", PROBE_LINE_SECONDS, raising=False
    )
    plant_slow_start(tmp_path, monkeypatch, PROBE_START_MS)
    with pytest.warns(UserWarning, match=STARTUP_READING) as seen:
        run = test_panel_seam.run_node(
            node_or_fail(), quick_driver(tmp_path), label="the quick driver", run_timeout=RUN_LIMIT
        )
    assert run.returncode == 0, run.stderr
    readings = [str(w.message) for w in seen if STARTUP_READING.search(str(w.message))]
    assert len(readings) == 1, readings
    assert "past the" in readings[0], readings


def test_a_pass_under_the_slow_line_leaves_no_warning(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        test_panel_seam, "NODE_SLOW_START_SECONDS", UNREACHABLE_LINE_SECONDS, raising=False
    )
    with warnings.catch_warnings(record=True) as seen:
        warnings.simplefilter("always")
        run = test_panel_seam.run_node(
            node_or_fail(), quick_driver(tmp_path), label="the quick driver", run_timeout=RUN_LIMIT
        )
    assert run.returncode == 0, run.stderr
    assert not [w for w in seen if STARTUP_READING.search(str(w.message))]


def test_the_spawn_that_failed_reports_its_start_up_on_every_pass(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The tier2 red's own spawn reports its start-up even under the line.

    So a green log carries the reading CS-1329 closes on.
    """
    monkeypatch.setattr(
        test_panel_seam, "NODE_SLOW_START_SECONDS", UNREACHABLE_LINE_SECONDS, raising=False
    )
    with pytest.warns(UserWarning, match=STARTUP_READING) as seen:
        test_panel_solve.test_the_driver_stand_in_is_exactly_the_shared_harnesses_surface(tmp_path)
    readings = [str(w.message) for w in seen if STARTUP_READING.search(str(w.message))]
    assert len(readings) == 1, readings
    assert "under the" in readings[0], readings


# ---------------------------------------------------------------------------
# d. The run limit is unchanged and the start budget is its own
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "module",
    [
        test_panel_solve,
        panel_harness,
        test_panel_seam,
        test_panel_power,
        test_panel_optimize,
        test_panel_global_scope,
    ],
    ids=lambda module: module.__name__.rsplit(".", 1)[-1],
)
def test_every_site_keeps_its_sixty_second_run_limit(module: ModuleType) -> None:
    assert module.NODE_TIMEOUT_SECONDS == RUN_LIMIT


def test_the_start_budget_is_a_separate_positive_budget() -> None:
    assert test_panel_seam.NODE_START_TIMEOUT_SECONDS > 0
    assert panel_harness.run_node is test_panel_seam.run_node
