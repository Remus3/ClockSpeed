#!/usr/bin/env python3
r"""CS-1108 - a lane worker cannot background a command, and a long one survives.

THE DEFECT, MEASURED 2026-09-16. In ``claude -p`` a background SHELL is killed
about five seconds after the final reply - the CLI's own debug line reads
"print wind-down: killing background shell ... after 5000ms grace". The
``CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS`` the runner already set (CS-918) covers
background SUBAGENTS and workflows only, never a shell. So every lane cycle that
backgrounded a suite and then ended its turn lost that suite: three cycles on
one day ended commit=no with their suite logs stopping at 8% and 20%.

THE MECHANISM, PROBED END TO END ON THE LANE'S OWN CLI. With
``CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1`` the ``run_in_background`` parameter
is not offered at all and the command runs to completion in the foreground.
That alone trades one kill for another, because a foreground Bash call is capped
by its maximum timeout; with ``BASH_MAX_TIMEOUT_MS`` and
``BASH_DEFAULT_TIMEOUT_MS`` raised as well, an eleven-minute foreground command
completed with exit 0.

WHAT IS GRADED IS THE ENVIRONMENT THE CHILD RECEIVES, BY VALUE. Presence of a
name is not the property: ``= "0"``, ``= ""``, a commented-out line and an
assignment placed after the invocation all carry the name and all leave the
worker exposed. So every value is checked against an ALLOWLIST of good values
(a denylist of bad ones leaked four times on this repository), twice:

- a RUNTIME arm runs the real runner under Windows PowerShell with a stub
  ``claude`` that dumps the environment it was handed. The runner's own process
  is seeded with POISONED values, so a runner that fails to set a variable
  before the invocation shows the poison, never an inherited good value;
- a STATIC arm parses the runner for the one active assignment of each name
  and its position before the ``& $claude`` line, which runs everywhere.

THE PROMPT IS BOUND TO THE LAUNCHER in one arm, so the two cannot drift apart:
the variable the prompt names as the reason nothing is backgrounded is the same
variable the static arm finds set to an allowlisted value.

PATHS ARE BOUND TO SCALARS BEFORE THEY ARE ASSERTED ON (CS-850).
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Final

import pytest

REPO_ROOT: Final = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
_TOOLS_DIR: Final = REPO_ROOT / "tools"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from toolpath import resolve_tool  # noqa: E402

RUNNER_SOURCE: Final = REPO_ROOT / "ops" / "loop" / "run_lane.ps1"
PROMPT_SOURCE: Final = REPO_ROOT / "tools" / "headless-queue.md"

DISABLE_VAR: Final = "CLAUDE_CODE_DISABLE_BACKGROUND_TASKS"
MAX_TIMEOUT_VAR: Final = "BASH_MAX_TIMEOUT_MS"
DEFAULT_TIMEOUT_VAR: Final = "BASH_DEFAULT_TIMEOUT_MS"
CEILING_VAR: Final = "CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS"

#: The ONE good value of the disable switch.
GOOD_DISABLE_VALUES: Final = frozenset({"1"})

#: A timeout must cover a whole-tree run with margin: runs were measured from
#: 8:49 up to about fifteen minutes, so the floor is twice the slow end.
TIMEOUT_FLOOR_MS: Final = 30 * 60 * 1000

#: And stay bounded, so a genuinely wedged command still dies and the cycle
#: reports rather than holding the lane for the rest of the night.
TIMEOUT_CAP_MS: Final = 60 * 60 * 1000

#: A positive decimal integer spelled plainly - no sign, no exponent, no space.
_DECIMAL: Final = re.compile(r"[1-9][0-9]*")

#: Every variable the runner must hand the child, in the order faults are named.
REQUIRED_VARS: Final = (DISABLE_VAR, MAX_TIMEOUT_VAR, DEFAULT_TIMEOUT_VAR, CEILING_VAR)

#: The value the runtime arm seeds into the runner's own environment for every
#: required variable. Each fails the allowlist, so an unset variable shows it.
POISON: Final = {
    DISABLE_VAR: "0",
    MAX_TIMEOUT_VAR: "1000",
    DEFAULT_TIMEOUT_VAR: "1000",
    CEILING_VAR: "1000",
}

#: What the stub exits with, distinctive so its line cannot come from a default.
SHIM_EXIT_CODE: Final = 41

_CHILD_TIMEOUT_S: Final = 120.0

#: The invocation line: the call operator applied to the resolved CLI.
_INVOCATION: Final = re.compile(r"&\s*\$claude\b", re.IGNORECASE)

_BLOCK_COMMENT: Final = re.compile(r"<#.*?#>", re.DOTALL)


def value_fault(name: str, value: str | None) -> str | None:
    """Whether one variable's value is on its allowlist.

    Args:
        name: The variable name.
        value: The value the child would receive, or None when it is absent.

    Returns:
        None when the value is good, else a short fault naming the variable.
    """
    if value is None:
        return f"{name}: absent"
    if name == DISABLE_VAR:
        return None if value in GOOD_DISABLE_VALUES else f"{name}: value not allowlisted"
    if _DECIMAL.fullmatch(value) is None:
        return f"{name}: not a plain positive integer"
    if not TIMEOUT_FLOOR_MS <= int(value) <= TIMEOUT_CAP_MS:
        return f"{name}: outside the allowlisted range"
    return None


def _active_lines(text: str) -> list[str]:
    """The script's lines with comments blanked, line numbers preserved.

    Args:
        text: The PowerShell source.

    Returns:
        One entry per source line; a comment line or block becomes empty.
    """
    blanked = _BLOCK_COMMENT.sub(lambda m: "\n" * m.group(0).count("\n"), text)
    return ["" if line.lstrip().startswith("#") else line for line in blanked.splitlines()]


def _assignment(name: str) -> re.Pattern[str]:
    """The ONE accepted spelling of an assignment to ``name``.

    Args:
        name: The variable name.

    Returns:
        A pattern whose group 1 is the double-quoted value.
    """
    return re.compile(
        r"\s*\$env:" + re.escape(name) + r'\s*=\s*"([^"$`]*)"\s*(?:#.*)?',
        re.IGNORECASE,
    )


def static_env_faults(text: str) -> list[str]:
    """Every reason the runner's source would hand the child a bad environment.

    An ALLOWLIST OF SHAPES as well as of values: an active line may mention a
    required name only as its one double-quoted assignment, placed before the
    single invocation. Any other active mention - a second assignment, a
    removal, an unquoted value - is a fault, because it can change what the
    child receives in a way this parser does not model.

    Args:
        text: The PowerShell source.

    Returns:
        The faults, empty when the environment is good.
    """
    lines = _active_lines(text)
    invocations = [i for i, line in enumerate(lines) if _INVOCATION.search(line)]
    if len(invocations) != 1:
        return ["the invocation line is not exactly one"]
    invoked_at = invocations[0]
    faults: list[str] = []
    for name in REQUIRED_VARS:
        mention = re.compile(re.escape(name), re.IGNORECASE)
        shape = _assignment(name)
        mentions = [i for i, line in enumerate(lines) if mention.search(line)]
        assigned = [(i, shape.fullmatch(lines[i])) for i in mentions]
        odd = [i for i, match in assigned if match is None]
        if odd:
            faults.append(f"{name}: an active line mentions it in an unaccepted shape")
            continue
        if len(assigned) != 1:
            faults.append(f"{name}: not exactly one active assignment")
            continue
        at, match = assigned[0]
        if at >= invoked_at:
            faults.append(f"{name}: assigned after the invocation")
            continue
        fault = value_fault(name, match.group(1) if match else None)
        if fault:
            faults.append(fault)
    return faults


# ===========================================================================
# a. The static arm, and its controls
# ===========================================================================

_GOOD_SCRIPT: Final = (
    "param([string]$Log)\n"
    '$env:CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS = "2400000"\n'
    '$env:CLAUDE_CODE_DISABLE_BACKGROUND_TASKS = "1"\n'
    '$env:BASH_MAX_TIMEOUT_MS = "2400000"\n'
    '$env:BASH_DEFAULT_TIMEOUT_MS = "2400000"\n'
    "try {\n"
    "  $claude = (Get-Command claude).Source\n"
    "  'x' | & $claude -p *>&1 | Out-File $Log\n"
    "} finally {}\n"
)

_DISABLE_LINE: Final = '$env:CLAUDE_CODE_DISABLE_BACKGROUND_TASKS = "1"\n'

#: Each rejection the acceptance names, applied to the good script's disable line.
_REJECTIONS: Final = {
    "zero": _GOOD_SCRIPT.replace(_DISABLE_LINE, _DISABLE_LINE.replace('"1"', '"0"')),
    "empty": _GOOD_SCRIPT.replace(_DISABLE_LINE, _DISABLE_LINE.replace('"1"', '""')),
    "commented": _GOOD_SCRIPT.replace(_DISABLE_LINE, "# " + _DISABLE_LINE),
    "block-commented": _GOOD_SCRIPT.replace(_DISABLE_LINE, "<#\n" + _DISABLE_LINE + "#>\n"),
    "after": _GOOD_SCRIPT.replace(_DISABLE_LINE, "").replace(
        "} finally {}\n", _DISABLE_LINE + "} finally {}\n"
    ),
    "reassigned": _GOOD_SCRIPT.replace("try {\n", "try {\n" + _DISABLE_LINE.replace('"1"', '"0"')),
    "removed": _GOOD_SCRIPT.replace(
        "try {\n", "try {\nRemove-Item env:CLAUDE_CODE_DISABLE_BACKGROUND_TASKS\n"
    ),
    "unquoted": _GOOD_SCRIPT.replace(_DISABLE_LINE, _DISABLE_LINE.replace('"1"', "1")),
}


def test_control_the_good_script_is_reported_for_nothing() -> None:
    faults = static_env_faults(_GOOD_SCRIPT)
    assert faults == []


@pytest.mark.parametrize("kind", sorted(_REJECTIONS))
def test_control_each_named_rejection_is_reported(kind: str) -> None:
    mutated = _REJECTIONS[kind]
    applied = mutated != _GOOD_SCRIPT
    assert applied, f"the {kind} mutation never applied"
    faults = static_env_faults(mutated)
    named = any(fault.startswith(DISABLE_VAR) for fault in faults)
    assert named, f"the {kind} mutation was not reported: {faults}"


@pytest.mark.parametrize(
    ("value", "good"),
    [
        ("2400000", True),
        (str(TIMEOUT_FLOOR_MS), True),
        (str(TIMEOUT_CAP_MS), True),
        ("600000", False),
        (str(TIMEOUT_CAP_MS + 1), False),
        ("0", False),
        ("", False),
        ("2.4e6", False),
        (" 2400000", False),
        ("02400000", False),
    ],
)
def test_control_the_timeout_allowlist(value: str, good: bool) -> None:
    fault = value_fault(MAX_TIMEOUT_VAR, value)
    assert (fault is None) is good


def test_the_runner_hands_the_child_an_allowlisted_environment() -> None:
    """THE STATIC ARM on the real runner: every value, and its position."""
    text = RUNNER_SOURCE.read_bytes().decode("ascii")
    faults = static_env_faults(text)
    assert faults == [], f"the runner's environment is not allowlisted: {faults}"


# ===========================================================================
# b. The runtime arm - the environment the child actually receives
# ===========================================================================


def _powershell() -> str:
    """Windows PowerShell, the interpreter the launcher runs the runner under.

    Returns:
        The absolute path to powershell.exe.
    """
    if os.name != "nt":
        pytest.skip("run_lane.ps1 is driven by Windows PowerShell")
    shell = resolve_tool("powershell")
    if shell is None:
        pytest.skip("powershell could not be resolved from PATH")
    return shell


def _system_dir() -> str:
    root = os.environ.get("SYSTEMROOT") or r"C:\Windows"
    return str(Path(root) / "System32")


def _poisoned_env(shim_dir: Path) -> dict[str, str]:
    """The runner's environment: a shim-first PATH and every variable poisoned.

    Args:
        shim_dir: The directory holding the stub CLI.

    Returns:
        The environment to hand the runner.
    """
    env = {key.upper(): value for key, value in os.environ.items()}
    env["PATH"] = f"{shim_dir}{os.pathsep}{_system_dir()}"
    env.pop("ANTHROPIC_API_KEY", None)
    env.update(POISON)
    return env


def _stub(tmp_path: Path) -> tuple[Path, Path]:
    """A ``claude`` that writes the environment it received beside itself.

    Args:
        tmp_path: The test's scratch directory.

    Returns:
        The shim directory and the dump path.
    """
    shim_dir = tmp_path / "shim"
    shim_dir.mkdir(exist_ok=True)
    (shim_dir / "claude.cmd").write_bytes(
        b'@echo off\r\nset > "%~dp0env.txt"\r\necho the stub ran\r\nexit /b '
        + str(SHIM_EXIT_CODE).encode("ascii")
        + b"\r\n"
    )
    return shim_dir, shim_dir / "env.txt"


def _read_dump(dump: Path) -> dict[str, str]:
    """The dumped environment, keys upper-cased as Windows compares them.

    Args:
        dump: The file ``set`` wrote.

    Returns:
        The variables by name.
    """
    seen: dict[str, str] = {}
    for line in dump.read_bytes().decode("ascii", errors="replace").splitlines():
        name, sep, value = line.partition("=")
        if sep:
            seen[name.upper()] = value
    return seen


def test_control_the_dump_observes_an_inherited_poison(tmp_path: Path) -> None:
    """The known-good control: an un-overridden variable arrives as its poison.

    Without it, a dump that never captured the environment and a runner that
    set every value correctly would both leave the arm below with nothing to
    report. It drives the stub through cmd.exe, so it runs exactly where the
    runtime arm it controls runs (CS-1111 owns the ubuntu gap).
    """
    _powershell()
    shim_dir, dump = _stub(tmp_path)
    comspec = str(Path(_system_dir()) / "cmd.exe")
    subprocess.run(
        [comspec, "/c", str(shim_dir / "claude.cmd")],
        capture_output=True,
        check=False,
        timeout=_CHILD_TIMEOUT_S,
        env=_poisoned_env(shim_dir),
    )
    wrote = dump.is_file()
    assert wrote, "the stub wrote no dump"
    seen = _read_dump(dump)
    poisoned = {name: seen.get(name) for name in REQUIRED_VARS}
    assert poisoned == POISON


def test_the_child_receives_an_allowlisted_environment(tmp_path: Path) -> None:
    """THE RUNTIME ARM: run the real runner, read the stub's own environment."""
    shell = _powershell()
    shim_dir, dump = _stub(tmp_path)
    prompt = tmp_path / "prompt.md"
    prompt.write_bytes(b"# a prompt the stub never reads\n")
    cwd = tmp_path / "tree"
    cwd.mkdir()
    log = tmp_path / "lane.log"
    subprocess.run(
        [
            shell,
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
        check=False,
        timeout=_CHILD_TIMEOUT_S,
        env=_poisoned_env(shim_dir),
    )
    ran = dump.is_file()
    assert ran, "the stub never ran - the arm grades nothing"
    tail = log.read_bytes().decode("utf-8-sig", errors="replace").strip().splitlines()[-1]
    coded = f"code={SHIM_EXIT_CODE}" in tail
    assert coded, "the runner's exit line does not carry the stub's code"

    seen = _read_dump(dump)
    faults = [
        fault for name in REQUIRED_VARS if (fault := value_fault(name, seen.get(name))) is not None
    ]
    assert faults == [], f"the child's environment is not allowlisted: {faults}"


# ===========================================================================
# c. The prompt, bound to the launcher
# ===========================================================================

#: The ONLY prompt lines allowed to say "background", exactly. A new line that
#: tells the worker to background something is not on this list and reddens.
ALLOWED_BACKGROUND_LINES: Final = frozenset(
    {
        "`docs/item_notes.md`. **Those sections are live instructions, not background.** Several",
        "**BACKGROUND TASKS ARE DISABLED BY THE LAUNCHER, "
        "so nothing you run is ever backgrounded.**",
        "`ops/loop/run_lane.ps1` sets `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1` before it starts",
        "you, so `run_in_background` is not offered to you or to any subagent. That is a",
        "mechanism, not advice (CS-1108): in a headless run a background shell is KILLED about",
    }
)

#: What the prompt must say about the replacement, token by token.
PROMPT_TOKENS: Final = (
    ("the launcher that disables it", r"ops/loop/run_lane\.ps1"),
    ("the disable switch by name", re.escape(DISABLE_VAR)),
    ("the timeout ceiling by name", re.escape(MAX_TIMEOUT_VAR)),
    ("a long command runs in the foreground", r"\bforeground\b"),
    ("with an explicit timeout", r"explicit\s+timeout"),
)

_BACKGROUND_WORD: Final = re.compile(r"background", re.IGNORECASE)


def background_line_faults(text: str) -> list[str]:
    """Every prompt line that says "background" and is not on the allowlist.

    Args:
        text: The prompt.

    Returns:
        The offending lines, stripped.
    """
    return [
        line.strip()
        for line in text.splitlines()
        if _BACKGROUND_WORD.search(line) and line.strip() not in ALLOWED_BACKGROUND_LINES
    ]


def test_control_a_background_instruction_is_reported() -> None:
    doc = "Budget generously and background it rather than killing it.\n"
    faults = background_line_faults(doc)
    assert faults == [doc.strip()]


def test_control_every_allowlisted_line_is_live(prompt_text: str) -> None:
    """A dead allowlist entry is a hole the next edit can walk through."""
    lines = {line.strip() for line in prompt_text.splitlines()}
    dead = sorted(ALLOWED_BACKGROUND_LINES - lines)
    assert dead == []


def test_the_prompt_never_tells_the_worker_to_background_anything(prompt_text: str) -> None:
    faults = background_line_faults(prompt_text)
    assert faults == [], f"prompt lines mention background outside the allowlist: {faults}"


def test_the_prompt_names_the_switch_the_launcher_actually_sets(prompt_text: str) -> None:
    """THE BINDING: prompt and launcher are graded together, so neither drifts.

    The prompt's reason for never backgrounding is the launcher's switch, so the
    arm fails when the prompt stops naming it AND when the launcher stops
    setting it to an allowlisted value before the invocation.
    """
    missing = [label for label, pattern in PROMPT_TOKENS if not re.search(pattern, prompt_text)]
    assert missing == [], f"the prompt does not state: {missing}"
    runner = RUNNER_SOURCE.read_bytes().decode("ascii")
    faults = [f for f in static_env_faults(runner) if f.startswith((DISABLE_VAR, MAX_TIMEOUT_VAR))]
    assert faults == [], f"the prompt names a switch the launcher does not set: {faults}"


@pytest.fixture(scope="module")
def prompt_text() -> str:
    """The prompt, decoded strictly as ASCII.

    Returns:
        The prompt's text.
    """
    return PROMPT_SOURCE.read_bytes().decode("ascii")
