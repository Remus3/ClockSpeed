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
"""

from __future__ import annotations

import re
import shutil
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

#: A run limit no driver can meet, so the run phase is the one that fails.
SQUEEZED: float = 0.001

#: The elapsed figure every diagnosis must carry.
ELAPSED: re.Pattern[str] = re.compile(r"elapsed \d+\.\d\d s")

#: The run limit every site carried before CS-1329, and still carries.
RUN_LIMIT: float = 60.0

#: How long the planted slow start spins before node reaches the marker. It
#: is longer than :data:`QUICK_RUN_LIMIT`, so a start-up charged to the run
#: limit would fail the arm.
SLOW_START_MS: int = 2500
QUICK_RUN_LIMIT: float = 2.0


def node_or_fail() -> str:
    """The interpreter off PATH. Absent node FAILS: a skip would grade nothing."""
    node = shutil.which("node")
    if node is None:
        pytest.fail("node is not on PATH, so no driver ran and nothing was graded")
    return node


def diagnosis(
    module: ModuleType, call: Callable[[], object], monkeypatch: pytest.MonkeyPatch
) -> str:
    """Squeeze ``module``'s run limit, make the call, return the failure text.

    Args:
        module: The module owning the spawn site and its ``NODE_TIMEOUT_SECONDS``.
        call: The site, bound to its arguments.
        monkeypatch: The fixture that restores the limit afterwards.

    Returns:
        The ``pytest.fail`` message the site raised.
    """
    monkeypatch.setattr(module, "NODE_TIMEOUT_SECONDS", SQUEEZED)
    with pytest.raises(pytest.fail.Exception) as caught:
        call()
    return str(caught.value)


def assert_run_phase_diagnosis(text: str) -> None:
    """The run phase timed out, and the message says enough to tell why."""
    assert ELAPSED.search(text), text
    assert "start marker arrived: yes" in text, text
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
        monkeypatch,
    )
    assert_run_phase_diagnosis(text)


def test_the_seam_harness_fails_with_a_diagnosis(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    text = diagnosis(
        test_panel_seam, lambda: test_panel_seam.run_seam(tmp_path, plant=False), monkeypatch
    )
    assert_run_phase_diagnosis(text)


def test_the_power_bench_driver_fails_with_a_diagnosis(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    text = diagnosis(
        test_panel_power,
        lambda: test_panel_power.drive(tmp_path, panel_harness.null_payload()),
        monkeypatch,
    )
    assert_run_phase_diagnosis(text)


def test_the_optimize_bench_driver_fails_with_a_diagnosis(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    text = diagnosis(
        test_panel_optimize,
        lambda: test_panel_optimize.drive(tmp_path, panel_harness.null_payload()),
        monkeypatch,
    )
    assert_run_phase_diagnosis(text)


def test_the_global_scope_page_harness_fails_with_a_diagnosis(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    text = diagnosis(
        test_panel_global_scope,
        lambda: test_panel_global_scope.run_page(tmp_path, ()),
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
    monkeypatch.setattr(test_panel_solve, "NODE_TIMEOUT_SECONDS", 1.0)
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


def test_a_timeout_quotes_what_the_driver_had_already_written(tmp_path: Path) -> None:
    script = tmp_path / "writes_then_spins.cjs"
    script.write_bytes(
        b'var fs = require("node:fs");\n'
        b'fs.writeSync(1, "partial-out-1329");\n'
        b'fs.writeSync(2, "partial-err-1329");\n'
        b"for (;;) {}\n"
    )
    with pytest.raises(pytest.fail.Exception) as caught:
        test_panel_seam.run_node(
            node_or_fail(), script, label="the spinning driver", run_timeout=QUICK_RUN_LIMIT
        )
    text = str(caught.value)
    assert "start marker arrived: yes" in text, text
    assert "partial-out-1329" in text, text
    assert "partial-err-1329" in text, text
    assert test_panel_seam.NODE_START_MARKER not in text, text


def test_node_start_up_is_never_charged_to_the_run_limit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A start-up longer than the run limit, then a quick driver: it passes.

    The slow start is a preload node runs BEFORE the marker's, through
    NODE_OPTIONS, which is where a cold start's time sits too. Under one
    budget spanning the whole process - the pre-CS-1329 shape - the same run
    is a timeout.
    """
    slow = tmp_path / "slow_start.cjs"
    slow.write_bytes(
        f"var until = Date.now() + {SLOW_START_MS};\nwhile (Date.now() < until) {{}}\n".encode(
            "ascii"
        )
    )
    script = tmp_path / "quick.cjs"
    script.write_bytes(b'process.stdout.write("quick-1329");\n')
    monkeypatch.setenv("NODE_OPTIONS", f'--require "{slow.as_posix()}"')
    run = test_panel_seam.run_node(
        node_or_fail(), script, label="the quick driver", run_timeout=QUICK_RUN_LIMIT
    )
    assert run.returncode == 0, run.stderr
    assert run.stdout == "quick-1329", run.stdout
    assert run.startup_seconds >= SLOW_START_MS / 1000 - 0.05, run.startup_seconds
    assert run.run_seconds < QUICK_RUN_LIMIT, run.run_seconds
    assert run.startup_seconds + run.run_seconds > QUICK_RUN_LIMIT
    assert test_panel_seam.NODE_START_MARKER not in run.stderr, run.stderr


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
