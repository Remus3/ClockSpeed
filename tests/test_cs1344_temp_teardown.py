"""CS-1344 - a real run clears its own ``<temp>/cs-pt`` output at teardown, failure included.

THE ORDER. MAIN's FIX of 2026-10-21 measured about 20.7k directories under
``<temp>/cs-pt``, and the temp directory's entry count costs boot time on this
machine. CS-1319's finisher KEPT a failed top-level run's directory as the
record of the failure, and one failed whole suite keeps about sixteen thousand
directories. The order overrides that retention: every run removes its own run
directory at its finish, passing or failing; a run killed from outside leaves
at most its own one directory, and the next run sweeps it. Accept: after a full
run, ``<temp>/cs-pt`` is empty or absent.

THE ARMS drive a REAL inner pytest, the mechanism wired as the root conftest
wires it - through ``tests/own_temp_root.py::wrap_configure`` - with the system
temp directory pointed at the arm's own ``tmp_path``, so no arm reads or touches
the real root, and with the temp-root and nested markers cleared, so the inner
run is TOP-LEVEL, the kind whose failure was kept. The inner run records the run
directory its claim made, so an empty root is never the vacuous result of a run
that claimed nothing.

SCOPE. Other suites run concurrently on this machine, so a teardown that swept
another run's directory would be a defect of its own: one arm plants a live
sibling, a sibling inside its grace period and a stranger, and grades that a
failing run's teardown leaves all three exactly as it found them.

Every observation is reduced to a bool or a count before an assertion sees it;
no assertion renders a path or an environment value.
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Final

import pytest

from tests import own_temp_root

REPO_ROOT: Final = Path(__file__).resolve().parent.parent
CALL_TIMEOUT: Final = 300
START_TIMEOUT: Final = 120.0
SEEN_NAME: Final = "seen.txt"
STARTED_NAME: Final = "started.txt"
HOUR: Final = 3600.0

#: The inner run's conftest: the root conftest's wiring, plus a configure hook
#: that records the run directory the claim named, for the outer arm to check.
INNER_CONFTEST: Final = (
    "import os\n"
    "from pathlib import Path\n"
    "\n"
    "from tests import own_temp_root\n"
    "\n"
    "\n"
    "def pytest_configure(config):\n"
    "    seen = Path(__file__).parent / " + repr(SEEN_NAME) + "\n"
    "    claimed = os.environ.get(own_temp_root.ENV_TEMPROOT, '')\n"
    "    seen.write_text(claimed, encoding='utf-8')\n"
    "\n"
    "\n"
    "own_temp_root.wrap_configure(globals())\n"
)

#: One inner test module per outcome, each writing into its tmp_path first.
INNER_BODIES: Final = {
    "passes": ("def test_passes(tmp_path):\n    (tmp_path / 'work.txt').write_bytes(b'work')\n"),
    "fails": (
        "import pytest\n"
        "\n"
        "\n"
        "def test_fails(tmp_path):\n"
        "    (tmp_path / 'work.txt').write_bytes(b'work')\n"
        "    pytest.fail('planted failure')\n"
    ),
    "errors": (
        "import pytest\n"
        "\n"
        "\n"
        "@pytest.fixture\n"
        "def broken(tmp_path):\n"
        "    (tmp_path / 'work.txt').write_bytes(b'work')\n"
        "    raise RuntimeError('planted setup error')\n"
        "\n"
        "\n"
        "def test_errors(broken):\n"
        "    pass\n"
    ),
    "interrupted": "raise RuntimeError('planted collection error')\n",
    "hangs": (
        "import time\n"
        "from pathlib import Path\n"
        "\n"
        "\n"
        "def test_hangs(tmp_path):\n"
        "    (tmp_path / 'work.txt').write_bytes(b'work')\n"
        "    (Path(__file__).parent / " + repr(STARTED_NAME) + ").write_bytes(b'')\n"
        "    time.sleep(" + str(int(CALL_TIMEOUT)) + ")\n"
    ),
}

#: The exit status each outcome's inner run must report - the proof that the
#: arm drove the outcome it names, and not a run that broke some other way.
EXPECTED_EXIT: Final = {"passes": 0, "fails": 1, "errors": 1, "interrupted": 2}


@dataclass
class Inner:
    """One inner run's sandbox: its own directory and the temp directory it sees."""

    directory: Path
    temp: Path

    @property
    def root(self) -> Path:
        """The tree-owned root as the inner run resolves it."""
        return self.temp / own_temp_root.ROOT_NAME

    def claimed(self) -> Path | None:
        """The run directory the inner run's claim named, or None when it claimed none."""
        seen = self.directory / SEEN_NAME
        if not seen.is_file():
            return None
        text = seen.read_text(encoding="utf-8")
        return Path(text) if text else None

    def claimed_under_root(self) -> bool:
        """Whether the claim named a run directory directly under the tree-owned root."""
        run = self.claimed()
        if run is None:
            return False
        same_parent = os.path.normcase(str(run.parent)) == os.path.normcase(str(self.root))
        return same_parent and run.name.startswith(own_temp_root.RUN_PREFIX)


def _make_inner(tmp_path: Path, name: str, outcome: str, temp: Path | None = None) -> Inner:
    """Lay out an inner run: a bare ini, the wiring conftest and one test module."""
    directory = tmp_path / name
    directory.mkdir()
    (directory / "pytest.ini").write_bytes(b"[pytest]\n")
    (directory / "conftest.py").write_bytes(INNER_CONFTEST.encode("ascii"))
    (directory / "test_inner.py").write_bytes(INNER_BODIES[outcome].encode("ascii"))
    if temp is None:
        temp = tmp_path / "t"
        temp.mkdir()
    return Inner(directory=directory, temp=temp)


def _inner_env(temp: Path) -> dict[str, str]:
    """A TOP-LEVEL inner run's environment, its system temp directory at ``temp``.

    Every ``PYTEST_*`` variable goes - this run's own temp root among them, so
    the inner claim does not stand aside - and so does the nested marker, so the
    inner run finishes as a top-level run would. Names only; no value is read
    back or rendered.
    """
    env = dict(os.environ)
    for name in [key for key in env if key.upper().startswith("PYTEST_")]:
        env.pop(name)
    env.pop(own_temp_root.ENV_NESTED, None)
    for name in ("TMPDIR", "TEMP", "TMP"):
        env[name] = str(temp)
    env["PYTHONPATH"] = str(REPO_ROOT)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def _command() -> list[str]:
    """The inner pytest's command: quiet, no cache written beside it."""
    return [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "test_inner.py"]


def _run(inner: Inner) -> int:
    """Run the inner pytest to its finish and return its exit status."""
    proc = subprocess.run(
        _command(),
        cwd=str(inner.directory),
        capture_output=True,
        env=_inner_env(inner.temp),
        timeout=CALL_TIMEOUT,
        check=False,
    )
    return proc.returncode


def _entries(root: Path) -> list[str]:
    """The names directly under ``root``; none when it is absent."""
    try:
        return sorted(entry.name for entry in os.scandir(root))
    except FileNotFoundError:
        return []


@pytest.mark.parametrize("outcome", sorted(EXPECTED_EXIT))
def test_a_top_level_run_leaves_no_output_under_the_root_whatever_its_outcome(
    tmp_path: Path, outcome: str
) -> None:
    """Passing, failing, erroring or interrupted: the root is empty at run end.

    RED before CS-1344: a failed top-level run (exit 1, 2 or 3) kept its run
    directory, marked for the next sweep to keep too.
    """
    inner = _make_inner(tmp_path, "i", outcome)
    code = _run(inner)
    drove_it = code == EXPECTED_EXIT[outcome]
    assert drove_it, f"{outcome}: the inner run exited {code}"
    claimed = inner.claimed_under_root()
    assert claimed, f"{outcome}: the inner run claimed no run directory under the root"
    left = len(_entries(inner.root))
    assert left == 0, f"{outcome}: the run left {left} entr(ies) under the root at its finish"


def test_a_failing_runs_teardown_never_touches_another_runs_directory(tmp_path: Path) -> None:
    """Only the run's own directory goes; a concurrent run's output is never swept.

    Three siblings are planted before a failing run: a LIVE run this process
    holds (a concurrent suite), a run directory inside its grace period (a
    sibling between its mkdir and its marker's open), and a stranger without
    the run prefix. Each must hold its work file after the failing run's
    claim-time sweep and its teardown both ran.
    """
    inner = _make_inner(tmp_path, "i", "fails")
    inner.root.mkdir()
    live = own_temp_root.claim(inner.root, {})
    if live is None:
        pytest.fail("the live sibling's claim owned nothing")
    young = inner.root / (own_temp_root.RUN_PREFIX + "young")
    stranger = inner.root / "not-a-run"
    works = [live.path / "work.txt", young / "work.txt", stranger / "work.txt"]
    try:
        for work in works:
            work.parent.mkdir(exist_ok=True)
            work.write_bytes(b"another run's work")
        code = _run(inner)
        kept = sum(1 for work in works if work.is_file())
        own = inner.claimed()
        own_gone = own is not None and not os.path.lexists(own)
    finally:
        own_temp_root.finish(live)
    assert code == 1, f"the failing inner run exited {code}"
    claimed = inner.claimed_under_root()
    assert claimed, "the failing inner run claimed no run directory under the root"
    planted = len(works)
    assert own_gone, "the failing run did not remove its own run directory"
    assert kept == planted, f"the teardown removed {planted - kept} sibling work file(s)"


def _wait_started(inner: Inner, proc: subprocess.Popen[bytes]) -> bool:
    """Whether the hanging inner test signalled it is inside its tmp_path."""
    deadline = time.monotonic() + START_TIMEOUT
    started = inner.directory / STARTED_NAME
    while time.monotonic() < deadline:
        if started.is_file():
            return True
        if proc.poll() is not None:
            return False
        time.sleep(0.1)
    return False


def _back_date(path: Path, seconds: float) -> None:
    """Back-date ``path``'s modification time by ``seconds``."""
    when = path.stat().st_mtime - seconds
    os.utime(path, (when, when))


def test_a_killed_run_leaves_only_its_own_directory_and_the_next_run_sweeps_it(
    tmp_path: Path,
) -> None:
    """Killed from outside: at most its one directory stays, and the next run reclaims it.

    The killed run never reaches its finish, so its one run directory is all it
    may leave. It is back-dated past the stale age, the reclaim rule on a
    platform with no liveness proof; on Windows the killed owner's marker
    unlinks, which is proof enough at any age past the grace period.
    """
    killed = _make_inner(tmp_path, "k", "hangs")
    proc = subprocess.Popen(
        _command(),
        cwd=str(killed.directory),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=_inner_env(killed.temp),
    )
    try:
        started = _wait_started(killed, proc)
    finally:
        proc.kill()
        proc.wait(timeout=CALL_TIMEOUT)
    assert started, "the hanging inner run never reached its test"
    own = killed.claimed()
    left = _entries(killed.root)
    only_its_own = own is not None and left == [own.name]
    assert only_its_own, f"the killed run left {len(left)} entr(ies), not its own one directory"
    if own is not None:
        _back_date(own, own_temp_root.STALE_AFTER_S + HOUR)
    nxt = _make_inner(tmp_path, "n", "passes", temp=killed.temp)
    code = _run(nxt)
    assert code == 0, f"the next inner run exited {code}"
    claimed = nxt.claimed_under_root()
    assert claimed, "the next inner run claimed no run directory under the root"
    after = len(_entries(killed.root))
    assert after == 0, f"the next run left {after} entr(ies) under the root"
