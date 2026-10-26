"""CS-1356: the ``inner_suite`` marker, and its explicit command-line deselect.

WHAT IS MARKED. A test that re-runs a whole (sub)suite or a sandbox suite in a
child ``python -m pytest``, or drives the Claude hook wrapper through a POSIX
shell the way the harness does. Those are the slowest tests in the tree by
setup and wall time, and every one of them still runs in tier1, tier2 and the
pre-push gate.

THE ONLY OPT-IN IS THE COMMAND LINE. An in-session local run deselects the
marked tests with ``-m "not inner_suite"``. Nothing else does: the marker is
NOT in ``addopts``, and no environment variable is consulted - the frozen
``.githooks/pre-push`` passes the pushing shell's environment through, so an
environment switch would silently drop the marked tests from the pre-push
gate. CI and pre-push build their own command lines and so collect every
marked test. ``ENV_DECOY`` below names the retired variable; setting it must
change nothing.

This module is collection only - a few child ``--collect-only`` runs over a
handful of node ids - and is deliberately NOT marked, so the local fast run
still proves the switch works. No environment value is rendered anywhere here:
the child environments are built from the parent's, and only node ids and
counts reach an assertion message (CLAUDE.md section 3 rule 13).
"""

from __future__ import annotations

import os
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Final

REPO_ROOT: Final = Path(__file__).resolve().parents[1]

#: The retired environment opt-in. Setting it must NOT change collection. Its
#: NAME appears here; its value is never rendered.
ENV_DECOY: Final = "CLOCKSPEED_FAST_LOCAL"

#: The marker every whole-suite or shell-harness test carries.
MARKER: Final = "inner_suite"

#: MAIN's measured worst offenders (CS-1356), one node id each. Each must be
#: deselected by ``-m "not inner_suite"`` and collected without it.
OFFENDERS: Final = (
    "tests/test_claude_hook.py::test_the_settings_commands_run_under_a_shell_like_the_harness",
    "tests/test_hook_env_echo.py::test_no_claude_hook_path_echoes_a_canary[pretooluse-allows]",
    "tests/test_canary_population_forced.py::"
    "test_a_helper_raise_under_showlocals_renders_no_canary_forced_red_output",
    "tests/test_cs1175_rule_narrowing.py::test_showlocals_forced_red_output_renders_no_canary",
    "tests/test_assertion_rendering.py::test_the_forced_arms_actually_ran_and_failed",
    "tests/data/test_phase2_gate.py::test_the_data_layer_suite_passes_with_the_install_unresolvable",
    "tests/solve/test_phase3_gate.py::test_the_solve_suite_passes_with_the_install_unresolvable",
)

#: THE CONTROL: a cheap unmarked test in an offender's own module. It must be
#: collected in EVERY mode, so a switch that deselected everything - or a
#: child that collected nothing - cannot pass the deselect arm.
CONTROL: Final = (
    "tests/test_canary_population_forced.py::test_the_unhygienic_copy_lands_each_edit_exactly_once"
)

CHILD_TIMEOUT: Final = 600


def _ini_options() -> dict[str, object]:
    """The ``[tool.pytest.ini_options]`` table of the shipped pyproject."""
    parsed = tomllib.loads((REPO_ROOT / "pyproject.toml").read_bytes().decode("utf-8"))
    table: dict[str, object] = parsed["tool"]["pytest"]["ini_options"]
    return table


def _collected(*, deselect: bool, env_decoy: bool) -> tuple[int, frozenset[str]]:
    """Collect the offenders and the control in a child; return its exit code and node ids.

    ``deselect`` adds ``-m "not inner_suite"`` to the child's command line.
    ``env_decoy`` sets the retired environment variable to ``1``. The child
    environment is the parent's with that variable forced on or off, so a
    parent run that itself carries it cannot decide any arm.
    """
    env = dict(os.environ)
    env.pop(ENV_DECOY, None)
    env.pop("PYTEST_ADDOPTS", None)
    env.pop("PYTEST_XDIST_WORKER", None)
    if env_decoy:
        env[ENV_DECOY] = "1"
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    argv = [
        sys.executable,
        "-m",
        "pytest",
        "--collect-only",
        "-q",
        "-p",
        "no:cacheprovider",
    ]
    if deselect:
        argv += ["-m", f"not {MARKER}"]
    argv += [*OFFENDERS, CONTROL]
    done = subprocess.run(
        argv,
        capture_output=True,
        check=False,
        cwd=str(REPO_ROOT),
        env=env,
        timeout=CHILD_TIMEOUT,
    )
    lines = done.stdout.decode("utf-8", errors="replace").splitlines()
    ids = frozenset(line.strip() for line in lines if "::" in line)
    return done.returncode, ids


def test_the_marker_is_registered() -> None:
    """``--strict-markers`` is on, so an unregistered marker is a collection error."""
    markers = _ini_options()["markers"]
    assert isinstance(markers, list)
    names = sorted(str(entry).split(":")[0].strip() for entry in markers)
    registered = MARKER in names
    assert registered, f"no {MARKER} marker is registered; registered: {names}"


def test_the_marker_is_not_deselected_by_default() -> None:
    """CI and the frozen pre-push hook run every marked test, so addopts must not exclude it."""
    addopts = str(_ini_options()["addopts"])
    excluded = MARKER in addopts
    assert not excluded, f"addopts names {MARKER}, so CI and pre-push would skip it"


def test_the_explicit_deselect_drops_every_named_offender() -> None:
    """With ``-m "not inner_suite"``, no offender is collected and the control still is."""
    code, ids = _collected(deselect=True, env_decoy=False)
    assert code == 0, f"the deselect collection exited {code}"
    kept = sorted(node for node in OFFENDERS if node in ids)
    assert not kept, f"the deselect run still collected: {kept}"
    control = CONTROL in ids
    assert control, "the deselect run did not collect the unmarked control"


def test_without_the_deselect_every_named_offender_is_collected() -> None:
    """Without ``-m``, the marker selects nothing away - CI's view."""
    code, ids = _collected(deselect=False, env_decoy=False)
    assert code == 0, f"the default collection exited {code}"
    missing = sorted(node for node in (*OFFENDERS, CONTROL) if node not in ids)
    assert not missing, f"the default run did not collect: {missing}"


def test_the_retired_environment_variable_changes_nothing() -> None:
    """The pre-push hook inherits the pushing shell's env, so no env value may deselect.

    With the retired variable set to ``1`` and no ``-m``, every offender and
    the control must still be collected.
    """
    code, ids = _collected(deselect=False, env_decoy=True)
    assert code == 0, f"the env-decoy collection exited {code}"
    missing = sorted(node for node in (*OFFENDERS, CONTROL) if node not in ids)
    assert not missing, f"the environment variable deselected: {missing}"
