"""CS-1116 - a hung git in ``tests/conftest.py::run_git`` is RED, never a skip.

THE DEFECT. ``run_git`` caught ``subprocess.SubprocessError``, and
``TimeoutExpired`` is one, so a git that hung past the bound returned None -
exactly what a missing git returns. Every caller reads None as "git is
unavailable" and skips, so a hang turned a grading test SKIPPED with no red
anywhere: the could-not-look-reads-as-skipped class CS-1107 closed for ``_git``
in ``tests/test_session_start_wiring.py``. This module reuses that shape.

THE PLANT NEVER TOUCHES A REAL REPOSITORY. ``run_git``'s program is swapped for
this interpreter running a child that sleeps far past a shrunken bound, pointed
at a temporary directory, with every repository-locating variable stripped from
the process first and asserted absent. The strip matches on the UPPER-CASED key,
because a Windows environment mapping upper-cases keys and a mixed-case pop
removes nothing while reporting clean.

THE OUTCOME IS CAUGHT EXPLICITLY. A skip escaping into pytest would turn the arm
SKIPPED rather than red, which is the very defect under test.
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from typing import Final

import pytest

from tests import conftest
from tests.git_env import REPO_LOCATING

#: The repository pointers the acceptance names. Each must also be in the shared
#: scrub set, so the strip below cannot silently narrow past them.
NAMED_POINTERS: Final = frozenset({"GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE"})

#: The bound the plant shrinks ``run_git`` to, in seconds.
PLANTED_TIMEOUT_SECONDS: Final = 1.0

#: How long the planted child would sleep if nothing stopped it, in seconds.
PLANTED_SLEEP_SECONDS: Final = 30

#: The ceiling on a planted run's wall time. Far under the child's sleep, so an
#: arm that passes did so because the bound fired, not because the child ended.
PLANTED_WALL_CEILING_SECONDS: Final = 20.0

#: What the control's planted child writes, so its run is seen, not assumed.
CONTROL_MARKER: Final = "cs1116-plant-ran"

#: The exit code the control's planted child ends with.
CONTROL_EXIT: Final = 3


def _strip_repo_pointers(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Remove every repository-locating variable from this process, restored after.

    Returns:
        The keys still present whose upper-cased name locates a repository -
        empty when the strip took.
    """
    for name in [key for key in os.environ if key.upper() in REPO_LOCATING]:
        monkeypatch.delenv(name)
    return sorted(key for key in os.environ if key.upper() in REPO_LOCATING)


def _outcome_text(outcome: BaseException) -> str:
    """The message a test outcome carries, read from its named field, never the object."""
    text = getattr(outcome, "msg", None)
    if isinstance(text, str):
        return text
    first = outcome.args[0] if outcome.args else ""
    return first if isinstance(first, str) else ""


def _run_git_outcome(root: Path) -> tuple[str, str, int | None]:
    """Run ``run_git`` and report how it ended, with the message and any exit code.

    Returns:
        ``("failed", message, None)``, ``("skipped", message, None)``,
        ``("returned-none", "", None)`` or ``("returned", stdout, returncode)``.
    """
    try:
        proc = conftest.run_git(root, "init", "--quiet")
    except pytest.fail.Exception as failure:
        return "failed", _outcome_text(failure), None
    except pytest.skip.Exception as skipped:
        return "skipped", _outcome_text(skipped), None
    if proc is None:
        return "returned-none", "", None
    return "returned", proc.stdout.decode("ascii", "replace"), proc.returncode


def test_the_named_pointers_are_in_the_shared_scrub_set() -> None:
    """The strip is keyed on the shared set, so the three named pointers must be in it."""
    missing = sorted(NAMED_POINTERS - REPO_LOCATING)
    assert missing == [], f"repository pointers absent from the scrub set: {missing}"


def test_a_git_timeout_in_run_git_fails_rather_than_skips(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """CS-1116 PLANT. A hung git FAILS; it is never read as git not being installed."""
    survivors = _strip_repo_pointers(monkeypatch)
    assert survivors == [], f"repository-locating variables survived the strip: {survivors}"
    monkeypatch.setattr(conftest, "RUN_GIT_TIMEOUT_SECONDS", PLANTED_TIMEOUT_SECONDS)
    monkeypatch.setattr(
        conftest,
        "RUN_GIT_PROGRAM",
        (sys.executable, "-c", f"import time; time.sleep({PLANTED_SLEEP_SECONDS})"),
    )
    started = time.monotonic()
    outcome, message, _ = _run_git_outcome(tmp_path)
    elapsed = time.monotonic() - started
    assert outcome == "failed", f"a planted git timeout ended {outcome}, not failed"
    assert "TIMED OUT" in message, "the failure does not say the git command timed out"
    assert elapsed < PLANTED_WALL_CEILING_SECONDS, (
        f"the planted run took {elapsed:.1f}s, so the bound did not fire"
    )


def test_the_run_git_plant_is_what_runs_and_a_missing_git_still_returns_none(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """CONTROLS for the plant. The swapped program is really run, and absence is still None.

    A child writing a marker and exiting 3 must come back with both, which real
    ``git init`` would not - so the plant cannot pass by being ignored. A program
    that does not exist must return None, the value every caller skips on,
    because git not being installed is still a skip; only a hang moved to red.
    """
    survivors = _strip_repo_pointers(monkeypatch)
    assert survivors == [], f"repository-locating variables survived the strip: {survivors}"
    monkeypatch.setattr(
        conftest,
        "RUN_GIT_PROGRAM",
        (
            sys.executable,
            "-c",
            f"import sys; sys.stdout.write({CONTROL_MARKER!r}); raise SystemExit({CONTROL_EXIT})",
        ),
    )
    ran_outcome, ran_stdout, ran_code = _run_git_outcome(tmp_path)
    monkeypatch.setattr(conftest, "RUN_GIT_PROGRAM", ("cs1116-no-such-git-program",))
    missing_outcome, _, _ = _run_git_outcome(tmp_path)
    assert ran_outcome == "returned", f"a planted exit {CONTROL_EXIT} ended {ran_outcome}"
    assert ran_code == CONTROL_EXIT, f"the planted child exited {ran_code}, not {CONTROL_EXIT}"
    assert CONTROL_MARKER in ran_stdout, "the planted program was not the one that ran"
    assert missing_outcome == "returned-none", (
        f"a missing git ended {missing_outcome}, not returned-none"
    )


def test_the_real_run_git_program_is_git_resolved_from_path() -> None:
    """The seam the plant swaps defaults to bare ``git``, never an absolute path."""
    program = conftest.RUN_GIT_PROGRAM
    assert program == ("git",), f"run_git's default program is {program!r}, not bare git"
