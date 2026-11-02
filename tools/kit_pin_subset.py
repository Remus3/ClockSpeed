#!/usr/bin/env python3
"""CS-1367 - run the fleet kit's pin tests first, so a pin red costs a minute, not a suite.

WHY. A kit adoption moves bytes the pin tests hold, and the whole suite took a slot and
tens of minutes to say so. These files are where an adoption goes red; ``-x`` stops at the
first red, and the exit code is the child's, so a run stops on a pin red without the whole
suite ever starting. Run it AFTER ``tools/repin_kit.py`` and BEFORE the whole suite
(``docs/OPERATIONS.md`` section 12.7).

WHAT IS LEFT OUT, MEASURED. The v27 adoption also went red in ``tests/test_mypy_gate.py``.
That file was measured beside the list on 2026-11-01, serial on this machine: the four
listed files 43 s, the mypy gate file alone 58 s, so about 101 s together. That is not
"about a minute", so it stays out and the whole suite is what catches a mypy-gate red.

BOUNDS. The child carries a timeout, and a timeout is a named nonzero exit rather than a
traceback. A listed file that does not exist refuses before any spawn: a pytest handed no
surviving target runs the bare whole suite, the one thing this tool exists to avoid.

Exit codes: the child's own; ``EXIT_REFUSED`` for a missing target; ``EXIT_TIMEOUT``.
"""

from __future__ import annotations

import os
import subprocess
import sys
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Final

REPO_ROOT: Final = Path(__file__).resolve().parents[1]

# The order named these; tests/test_kit_pin_subset.py holds the list to a typed literal.
PIN_FILES: Final = (
    "tests/test_fleet_kit.py",
    "tests/test_third_party_register.py",
    "tests/test_exception_rendering.py",
    "tests/test_subprocess_timeouts.py",
)
# Measured at 43 s; the bound is a hung-child bound, well clear of a slow machine.
PIN_TIMEOUT_S: Final = 300
EXIT_REFUSED: Final = 3
EXIT_TIMEOUT: Final = 4

# A runner is subprocess.run's shape; the tests inject one to observe the call.
Runner = Callable[..., "subprocess.CompletedProcess[bytes]"]


def _child_env() -> dict[str, str]:
    """This environment minus pytest's own variables.

    A nested pytest under xdist inherits ``PYTEST_XDIST_WORKER``, and an inherited
    ``PYTEST_ADDOPTS`` could carry a flag away from ``-x``. Names only: no value is read.
    """
    return {key: value for key, value in os.environ.items() if not key.startswith("PYTEST_")}


def run_subset(
    *,
    root: Path = REPO_ROOT,
    files: Sequence[str] = PIN_FILES,
    runner: Runner = subprocess.run,
    timeout: int = PIN_TIMEOUT_S,
) -> int:
    """Run ``files`` under pytest from ``root``, stopping at the first red; return its exit."""
    missing = [rel for rel in files if not (root / rel).is_file()]
    if missing or not files:
        print("kit_pin_subset: REFUSED, no such target: " + (", ".join(missing) or "(empty list)"))
        return EXIT_REFUSED
    argv = [sys.executable, "-m", "pytest", *files, "-q", "-x", "-p", "no:cacheprovider"]
    try:
        completed = runner(argv, cwd=str(root), env=_child_env(), timeout=timeout, check=False)
    except subprocess.TimeoutExpired:
        print("kit_pin_subset: TIMED OUT at " + str(timeout) + " s")
        return EXIT_TIMEOUT
    return completed.returncode


if __name__ == "__main__":
    sys.exit(run_subset())
