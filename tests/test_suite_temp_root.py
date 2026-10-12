"""CS-1319 - the suite runs under its OWN temp root, never the shared per-user one.

MEASURED by MAIN on 2026-10-12: the shared per-account pytest temp root grew
from under two thousand directories to over ninety thousand overnight, about
seventy thousand of them in two numbered run directories left by killed or
failed runs of this suite. pytest's keep-3 retention never reclaimed them: its
lock timeout is three days, so a killed run's directory is protected long
after it can be of use, and the root is shared with every other tree on the
machine.

This file grades the WIRING, from inside a real run: the base temporary
directory this very session handed out sits under the tree-owned root, in a
directory this run claimed for itself. The mechanism's own behaviour - the
claim, the sweep, the read-only-safe removal - is graded in
``tests/test_own_temp_root.py``.

An explicit ``--basetemp`` is the one sanctioned override: whoever passes it
has chosen the place, so the arm skips with a reason rather than grading a
choice this suite did not make.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

#: The tree-owned temp root's directory name, under the system temp directory.
#: Spelled out here rather than imported, so this arm fails on its assertion -
#: not on an import - while the mechanism does not exist.
OWN_ROOT_NAME = "clockspeed-pytest"


def test_this_run_hands_out_temp_directories_under_the_tree_owned_root(
    tmp_path_factory: pytest.TempPathFactory,
    pytestconfig: pytest.Config,
) -> None:
    """The session's base temp is inside ``<temp>/clockspeed-pytest/run-*``."""
    if pytestconfig.getoption("basetemp") and not pytestconfig.getoption("basetemp").startswith(
        str(Path(tempfile.gettempdir()).resolve() / OWN_ROOT_NAME)
    ):
        pytest.skip("an explicit --basetemp outside the tree-owned root chose the place")
    base = tmp_path_factory.getbasetemp().resolve()
    own_root = (Path(tempfile.gettempdir()) / OWN_ROOT_NAME).resolve()
    under_own_root = own_root in base.parents
    assert under_own_root, "the base temp is not under the tree-owned temp root"
    run_dir = base.relative_to(own_root).parts[0]
    claimed_by_a_run = run_dir.startswith("run-")
    assert claimed_by_a_run, "the base temp is not inside a run directory this suite claimed"
