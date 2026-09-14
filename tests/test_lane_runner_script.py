#!/usr/bin/env python3
r"""The lane runner script, graded by RUNNING it - not by grepping it.

WHY THIS FILE EXISTS SEPARATELY FROM ``tests/test_lane_launcher.py``. That file
states, in its own header, that no arm in it spawns a process, and every arm it
holds about ``ops/loop/run_lane.ps1`` is therefore a text property: the byte
set, the stream folding, the cleared API key. Those arms are worth keeping and
they are all blind to the defect graded here, because the defect is a CONTROL
FLOW one - which lines the script reaches when something upstream of the log
refuses.

THE MEASUREMENT THIS FILE WAS WRITTEN FOR. Thirteen recorded lane cycles left a
worker log holding the "lane start" header line and NOTHING else - no exit line,
no fault, 134 bytes. A log that stops after its header cannot distinguish a
worker that was killed from a worker that crashed from a worker that is still
running, so every one of those cycles was unreadable after the fact. Re-measured
on this machine while diagnosing it: killing a healthy runner two seconds after
its start produces a 134-byte log, byte for byte the same artifact, so the
header-only log is the signature of a DEATH THE SCRIPT NEVER SAW.

AND ONE DEATH IT DOES NOT EVEN GET A HEADER FOR. ``Get-Command claude
-ErrorAction Stop`` used to run BEFORE the header was written, so a box with no
CLI on PATH produced no log at all and the launcher recorded ``runner_exited_early``
- a reason word about the runner, for a fault the runner never had.

THESE ARMS SPAWN A REAL powershell.exe, and that is deliberate: a grep for a
``finally`` block would pass on a script whose ``try`` never encloses the thing
that throws. What is asserted is the FILE ON DISK after a real interpreter has
run the real script.

NO REAL CLI IS EVER INVOKED. ``PATH`` is rebuilt from a shim directory plus the
system directory, so ``claude`` resolves to a batch file this test wrote, or to
nothing at all. Each arm is FRONTED BY A CONTROL that asserts the resolution
really went the way the arm depends on: without it, "the runner wrote an exit
line" is also what a runner that silently skipped the whole body would produce.

PATHS ARE BOUND TO SCALARS BEFORE THEY ARE ASSERTED ON (CS-850): pytest renders
an asserted expression's sub-expressions with their own reprs whatever message
the assertion carries, and a temporary directory on this platform carries the
account name.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Final

import pytest

REPO_ROOT: Final = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
_TOOLS_DIR: Final = REPO_ROOT / "tools"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from toolpath import resolve_tool  # noqa: E402

RUNNER_SOURCE: Final = REPO_ROOT / "ops" / "loop" / "run_lane.ps1"

#: What the shim exits with. Distinctive, and NOT 0 or 1, so an exit line
#: carrying it cannot have come from a default or from a generic failure.
SHIM_EXIT_CODE: Final = 37

#: Generous, and present only so a wedged arm fails rather than hanging the run.
_CHILD_TIMEOUT_S: Final = 120.0

#: The words that END a lane log. A reader that finds neither is looking at a
#: log whose writer died without saying so, which is the whole defect.
_TERMINAL_PREFIXES: Final = ("lane exit ", "lane fault ", "lane abort ")

pytestmark = pytest.mark.skipif(
    os.name != "nt", reason="run_lane.ps1 is driven by Windows PowerShell"
)


def _powershell() -> str:
    """The interpreter, resolved from PATH and never named as a bare string.

    Returns:
        The absolute path to powershell.exe.
    """
    shell = resolve_tool("powershell")
    if shell is None:
        pytest.skip("powershell could not be resolved from PATH")
    return shell


def _system_dir() -> str:
    """The system directory, which PowerShell needs on PATH to start cleanly.

    Returns:
        The system directory as a string.
    """
    root = os.environ.get("SYSTEMROOT") or r"C:\Windows"
    return str(Path(root) / "System32")


def _env_with_path(shim_dir: Path) -> dict[str, str]:
    """The child's environment with PATH rebuilt from one shim directory.

    The real CLI is unreachable from here BY CONSTRUCTION rather than by an
    unsetenv that Windows would fold into a differently cased key.

    Args:
        shim_dir: The directory that may or may not hold a ``claude`` shim.

    Returns:
        The environment to hand the child.
    """
    env = dict(os.environ)
    env["PATH"] = f"{shim_dir}{os.pathsep}{_system_dir()}"
    # The runner clears this for its own process; cleared here too so that a
    # machine-scope key can never make an arm depend on a credit balance.
    env.pop("ANTHROPIC_API_KEY", None)
    return env


def _resolves_claude(shim_dir: Path) -> bool:
    """Whether ``claude`` resolves at all under this arm's PATH.

    THE CONTROL for both arms below. A runner that wrote an exit line because it
    skipped its whole body looks identical to one that wrote it because the body
    ran, and only this probe separates them.

    Args:
        shim_dir: The directory to put first on PATH.

    Returns:
        True when Get-Command finds something.
    """
    done = subprocess.run(
        [
            _powershell(),
            "-NoProfile",
            "-Command",
            "if (Get-Command claude -ErrorAction SilentlyContinue) { 'FOUND' } else { 'MISSING' }",
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=_CHILD_TIMEOUT_S,
        env=_env_with_path(shim_dir),
    )
    return done.stdout.strip() == "FOUND"


def _run_runner(tmp_path: Path, shim_dir: Path) -> tuple[Path, subprocess.CompletedProcess[str]]:
    """Run the real runner against planted paths and hand back its log.

    Args:
        tmp_path: The test's scratch directory.
        shim_dir: The directory placed first on the child's PATH.

    Returns:
        The log path and the completed process.
    """
    prompt = tmp_path / "prompt.md"
    prompt.write_bytes(b"# a prompt the shim never reads\n")
    cwd = tmp_path / "tree"
    cwd.mkdir(exist_ok=True)
    log = tmp_path / "lane.log"
    done = subprocess.run(
        [
            _powershell(),
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(RUNNER_SOURCE),
            "-PromptFile",
            str(prompt),
            "-Cwd",
            str(cwd),
            "-Log",
            str(log),
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=_CHILD_TIMEOUT_S,
        env=_env_with_path(shim_dir),
    )
    return log, done


def _log_lines(log: Path) -> list[str]:
    """The log's non-empty lines, decoded tolerantly of the BOM Out-File writes.

    Args:
        log: The log file.

    Returns:
        The non-empty lines.
    """
    if not log.is_file():
        return []
    text = log.read_bytes().decode("utf-8-sig", errors="replace")
    return [line.strip() for line in text.splitlines() if line.strip()]


def _shim(tmp_path: Path) -> Path:
    """A directory holding a ``claude`` that prints one line and exits.

    Args:
        tmp_path: The test's scratch directory.

    Returns:
        The shim directory.
    """
    shim_dir = tmp_path / "shim"
    shim_dir.mkdir(exist_ok=True)
    (shim_dir / "claude.cmd").write_bytes(
        b"@echo off\r\necho the shim ran\r\nexit /b "
        + str(SHIM_EXIT_CODE).encode("ascii")
        + b"\r\n"
    )
    return shim_dir


def _empty(tmp_path: Path) -> Path:
    """A directory holding no ``claude`` at all.

    Args:
        tmp_path: The test's scratch directory.

    Returns:
        The empty directory.
    """
    empty = tmp_path / "no-cli"
    empty.mkdir(exist_ok=True)
    return empty


# ===========================================================================
# a. A worker that runs - the control for everything below
# ===========================================================================


def test_a_runner_whose_worker_exits_records_the_header_the_output_and_the_code(
    tmp_path: Path,
) -> None:
    """The control - a complete log is reachable, so a truncated one is a defect.

    A log that stops after its header is only a fault if a full one can be
    written at all, and this is the arm that shows one can.

    All three parts are asserted, because any one alone is satisfied by a
    runner that wrote a constant: the header names the cwd it was given, the
    body carries the shim's own line, and the exit line carries the shim's own
    exit code.
    """
    shim_dir = _shim(tmp_path)
    resolves = _resolves_claude(shim_dir)
    assert resolves, "the shim did not reach PATH - the arm grades nothing"

    log, done = _run_runner(tmp_path, shim_dir)
    ran = done.returncode
    assert ran == 0, f"the runner itself failed - stderr was {done.stderr[:400]!r}"

    lines = _log_lines(log)
    assert lines, "the runner wrote no log at all"

    started = lines[0].startswith("lane start ")
    assert started, f"the first line is not a start header: {lines[0][:80]!r}"

    carried = any("the shim ran" in line for line in lines)
    assert carried, "the worker's own output never reached the log"

    ended = lines[-1]
    assert ended.startswith("lane exit "), f"the last line is not an exit line: {ended[:80]!r}"

    coded = f"code={SHIM_EXIT_CODE}" in ended
    assert coded, f"the exit line does not carry the worker's code: {ended[:80]!r}"


# ===========================================================================
# b. A worker that cannot start - the 134-byte log
# ===========================================================================


def test_a_runner_that_cannot_resolve_the_cli_still_writes_a_header(
    tmp_path: Path,
) -> None:
    """A log that does not exist is worse than one that stops after its header.

    ``Get-Command claude -ErrorAction Stop`` is a TERMINATING failure. Run
    before the header, it ends the script with nothing on disk, and the
    launcher's liveness grace then records ``runner_exited_early`` - a reason
    word about the runner for a fault the runner never had.
    """
    empty = _empty(tmp_path)
    missing = not _resolves_claude(empty)
    assert missing, "claude is still on PATH - the arm grades nothing"

    log, _done = _run_runner(tmp_path, empty)
    wrote = log.is_file()
    assert wrote, "the runner died without writing a log at all"

    lines = _log_lines(log)
    started = bool(lines) and lines[0].startswith("lane start ")
    assert started, "the log does not open with a start header"


def test_a_runner_that_cannot_resolve_the_cli_still_records_a_terminal_line(
    tmp_path: Path,
) -> None:
    """THE DEFECT ITSELF. Thirteen recorded cycles ended here.

    Whatever refuses, the runner must say that it stopped. A log whose last line
    is the header cannot be told apart from a worker still running, and that is
    what made every failing cycle on both recorded nights unreadable.
    """
    empty = _empty(tmp_path)
    missing = not _resolves_claude(empty)
    assert missing, "claude is still on PATH - the arm grades nothing"

    log, _done = _run_runner(tmp_path, empty)
    lines = _log_lines(log)
    assert lines, "the runner wrote no log at all"

    ended = lines[-1]
    terminal = ended.startswith(_TERMINAL_PREFIXES)
    assert terminal, f"the log stops without a terminal line: {ended[:120]!r}"


def test_a_runner_that_cannot_resolve_the_cli_names_the_fault_symbolically(
    tmp_path: Path,
) -> None:
    """A terminal line that says nothing about WHY is half a diagnosis.

    The fault is named by its exception TYPE and its FullyQualifiedErrorId,
    never by ``$_.Exception.Message``. That is the same rule the Python half
    obeys: an error id is symbolic and path-free by construction, while a
    message routinely embeds the path it failed on (CLAUDE.md non-negotiable
    12), and this log is written by an unattended process nobody is watching.
    """
    empty = _empty(tmp_path)
    missing = not _resolves_claude(empty)
    assert missing, "claude is still on PATH - the arm grades nothing"

    log, _done = _run_runner(tmp_path, empty)
    lines = _log_lines(log)
    faults = [line for line in lines if line.startswith("lane fault ")]
    assert faults, "nothing in the log names the fault"

    named = "CommandNotFoundException" in faults[0]
    assert named, f"the fault line does not name the refusal: {faults[0][:120]!r}"
