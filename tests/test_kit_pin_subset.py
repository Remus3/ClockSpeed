"""CS-1367 - the kit-adoption pin subset stops on a pin red without the whole suite.

Two arms, the pin red and the green run, hold the stop against a REAL nested pytest over a
fixture tree in tmp_path, so nothing tracked is mutated and a kill mid-arm leaves nothing
behind. The rest read the list or use the injected runner, so they cost no child at all.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest


def _load_tool() -> Any:
    """Import the tool by path: `tools` has no __init__.py, and mypy reads it bare."""
    path = Path(__file__).resolve().parents[1] / "tools" / "kit_pin_subset.py"
    spec = importlib.util.spec_from_file_location("clockspeed_kit_pin_subset", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


kit_pin_subset = _load_tool()

# Typed by hand, never derived from the tool: this is the list the order names.
EXPECTED_FILES = (
    "tests/test_fleet_kit.py",
    "tests/test_third_party_register.py",
    "tests/test_exception_rendering.py",
    "tests/test_subprocess_timeouts.py",
)
GREEN_TEST = "def test_green():\n    pass\n"
# The later file writes a marker, so a run that did not stop leaves it on disk.
LATER_TEST = (
    "from pathlib import Path\n\n"
    "def test_later():\n"
    "    (Path(__file__).parent / 'later_ran').write_bytes(b'')\n"
)
RED_TEST = "def test_pin_red():\n    pin = 28\n    assert pin == 29\n"


def _fixture(tmp_path: Path, first: str) -> tuple[str, str]:
    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "test_a_first.py").write_text(first, encoding="ascii")
    (tests / "test_b_later.py").write_text(LATER_TEST, encoding="ascii")
    return ("tests/test_a_first.py", "tests/test_b_later.py")


def test_the_pin_file_list_is_pinned() -> None:
    assert kit_pin_subset.PIN_FILES == EXPECTED_FILES


def test_the_default_run_executes_every_pinned_file_with_no_pytest_variable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # The constant above says nothing about what a bare run spawns. Names only are kept:
    # the environment carries credentials, so no value reaches an assertion's rendering.
    monkeypatch.setenv("PYTEST_ADDOPTS", "-q")
    monkeypatch.setenv("CS1367_PLANTED", "1")
    seen_argv: list[str] = []
    env_names: list[str] = []

    def spy(argv: list[str], **kwargs: Any) -> subprocess.CompletedProcess[bytes]:
        seen_argv.extend(argv)
        env_names.extend(kwargs["env"])
        return subprocess.CompletedProcess(argv, 0)

    code = kit_pin_subset.run_subset(runner=spy)
    absent = [rel for rel in EXPECTED_FILES if rel not in seen_argv]
    pytest_names = [name for name in env_names if name.startswith("PYTEST_")]
    assert (code, absent, pytest_names) == (0, [], [])
    assert "CS1367_PLANTED" in env_names


def test_every_pinned_file_exists_in_this_tree() -> None:
    missing = [rel for rel in EXPECTED_FILES if not (kit_pin_subset.REPO_ROOT / rel).is_file()]
    assert missing == []


def test_a_pin_red_stops_the_run_and_its_exit_code_is_propagated(tmp_path: Path) -> None:
    files = _fixture(tmp_path, RED_TEST)
    code = kit_pin_subset.run_subset(root=tmp_path, files=files)
    later_ran = (tmp_path / "tests" / "later_ran").exists()
    assert (code, later_ran) == (1, False)


def test_a_green_run_reaches_the_last_file_and_exits_zero(tmp_path: Path) -> None:
    files = _fixture(tmp_path, GREEN_TEST)
    code = kit_pin_subset.run_subset(root=tmp_path, files=files)
    later_ran = (tmp_path / "tests" / "later_ran").exists()
    assert (code, later_ran) == (0, True)


def test_the_command_stops_at_the_first_red_and_carries_a_timeout(tmp_path: Path) -> None:
    seen: dict[str, object] = {}

    def runner(argv: list[str], **kwargs: object) -> subprocess.CompletedProcess[bytes]:
        seen["argv"] = argv
        seen.update(kwargs)
        return subprocess.CompletedProcess(argv, 7)

    files = _fixture(tmp_path, GREEN_TEST)
    code = kit_pin_subset.run_subset(root=tmp_path, files=files, runner=runner)
    argv = seen["argv"]
    assert isinstance(argv, list)
    assert (code, argv[:3], argv[3:5], "-x" in argv) == (
        7,
        [sys.executable, "-m", "pytest"],
        list(files),
        True,
    )
    assert seen["timeout"] == kit_pin_subset.PIN_TIMEOUT_S


def test_a_timeout_is_a_nonzero_exit_not_a_traceback(tmp_path: Path) -> None:
    def runner(argv: list[str], **_kwargs: object) -> subprocess.CompletedProcess[bytes]:
        raise subprocess.TimeoutExpired(argv, kit_pin_subset.PIN_TIMEOUT_S)

    files = _fixture(tmp_path, GREEN_TEST)
    code = kit_pin_subset.run_subset(root=tmp_path, files=files, runner=runner)
    assert code == kit_pin_subset.EXIT_TIMEOUT


def test_a_missing_listed_file_refuses_without_spawning(tmp_path: Path) -> None:
    # A pytest handed no surviving target runs the bare whole suite, which is the
    # one thing this tool exists to avoid.
    spawned: list[list[str]] = []

    def runner(argv: list[str], **_kwargs: object) -> subprocess.CompletedProcess[bytes]:
        spawned.append(argv)
        return subprocess.CompletedProcess(argv, 0)

    code = kit_pin_subset.run_subset(root=tmp_path, files=("tests/absent.py",), runner=runner)
    spawn_count = len(spawned)
    assert (code, spawn_count) == (kit_pin_subset.EXIT_REFUSED, 0)


def test_an_empty_file_list_refuses_without_spawning(tmp_path: Path) -> None:
    spawned: list[list[str]] = []

    def runner(argv: list[str], **_kwargs: object) -> subprocess.CompletedProcess[bytes]:
        spawned.append(argv)
        return subprocess.CompletedProcess(argv, 0)

    code = kit_pin_subset.run_subset(root=tmp_path, files=(), runner=runner)
    spawn_count = len(spawned)
    assert (code, spawn_count) == (kit_pin_subset.EXIT_REFUSED, 0)
