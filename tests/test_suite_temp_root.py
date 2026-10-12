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

import getpass
import tempfile
from pathlib import Path

import pytest

#: The tree-owned temp root's directory name, under the system temp directory.
#: Spelled out here rather than imported, so this arm fails on its assertion -
#: not on an import - while the mechanism does not exist.
OWN_ROOT_NAME = "cs-pt"


def _given_basetemp_is_under(pytestconfig: pytest.Config, place: Path) -> bool:
    """Whether the session's ``--basetemp``, if any, is inside ``place``.

    Both sides are resolved: the temp directory can be spelled in its short
    8.3 form, and the mechanism gives pytest a base temp in that spelling.
    No ``--basetemp`` at all counts as inside - nothing else chose the place.
    """
    given = pytestconfig.getoption("basetemp")
    if not given:
        return True
    return place.resolve() in Path(given).resolve().parents


def test_this_run_hands_out_temp_directories_under_the_tree_owned_root(
    tmp_path_factory: pytest.TempPathFactory,
    pytestconfig: pytest.Config,
) -> None:
    """The session's base temp is inside ``<temp>/cs-pt/r-*``."""
    if not _given_basetemp_is_under(pytestconfig, Path(tempfile.gettempdir()) / OWN_ROOT_NAME):
        pytest.skip("an explicit --basetemp outside the tree-owned root chose the place")
    base = tmp_path_factory.getbasetemp().resolve()
    own_root = (Path(tempfile.gettempdir()) / OWN_ROOT_NAME).resolve()
    under_own_root = own_root in base.parents
    assert under_own_root, "the base temp is not under the tree-owned temp root"
    run_dir = base.relative_to(own_root).parts[0]
    claimed_by_a_run = run_dir.startswith("r-")
    assert claimed_by_a_run, "the base temp is not inside a run directory this suite claimed"


def _old_shared_prefix_length() -> int:
    """The shortest prefix the old shared layout put above the temp directory.

    pytest's default is ``pytest-of-<user>/pytest-<N>/`` under the temp
    directory, ``<user>`` as pytest itself reads it. ``N`` is taken as one
    digit - the shortest it ever is - so the bound is the strictest one.
    """
    try:
        user = getpass.getuser()
    except (ImportError, OSError, KeyError):
        user = "unknown"
    return len(f"pytest-of-{user}") + 1 + len("pytest-0") + 1


def test_the_own_root_adds_no_path_depth_over_the_old_shared_layout(
    tmp_path_factory: pytest.TempPathFactory,
    pytestconfig: pytest.Config,
) -> None:
    """CS-1320 - a tmp_path under the own root is no longer than under the old layout.

    MEASURED on 2026-10-12: the CS-1319 layout put ``<root>/<run>/`` ABOVE
    pytest's own ``pytest-of-<user>/pytest-<N>/``, about 37 characters deeper,
    and a git clone inside a tmp_path under xdist then exceeded the Windows
    path limit. The prefix graded here is everything between the temp directory
    and the session's base temp, an xdist worker's own ``popen-gw<N>`` level
    excluded - the old layout had that level too.
    """
    if not _given_basetemp_is_under(pytestconfig, Path(tempfile.gettempdir())):
        pytest.skip("an explicit --basetemp outside the temp directory chose the place")
    base = tmp_path_factory.getbasetemp().resolve()
    if base.name.startswith("popen-"):
        base = base.parent
    temp = Path(tempfile.gettempdir()).resolve()
    prefix_length = len(str(base)) - len(str(temp))
    old_length = _old_shared_prefix_length()
    no_deeper = prefix_length <= old_length
    assert no_deeper, f"temp prefix {prefix_length} characters, the old layout's {old_length}"
