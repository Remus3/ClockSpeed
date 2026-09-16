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
- a STATIC arm lexes the runner for the one accepted assignment of each name
  at script scope before the ``& $claude`` line, which runs everywhere.

THE PROMPT IS BOUND TO THE LAUNCHER in one arm, so the two cannot drift apart:
the variable the prompt names as the reason nothing is backgrounded is the same
variable the static arm finds set to an allowlisted value.

CS-1111 CLOSES FOUR GAPS THOSE ARMS LEFT.

1. Tier1 CI is ubuntu-only, where the runtime arm skips, and the static arm
   alone passed six bad plants. The static arm is now a small LEXER: an
   assignment is accepted only at script scope (no open bracket, string,
   here-string or comment), not continued from the line above, and a statement
   before the invocation that reaches the environment any other way reddens.
   Each plant is written to disk and graded by the static arm everywhere, and
   on Windows the runtime arm first proves each plant really is bad.
2. The CLI copies a settings file's ``env`` block over the process env, so a
   tracked settings file is read and a differing value reddens.
3. The prompt's foreground-only statement forbids shell-level detaching.
4. The launcher's Bash timeout is tied to the driver's suite wedge limit.

PATHS ARE BOUND TO SCALARS BEFORE THEY ARE ASSERTED ON (CS-850).
"""

from __future__ import annotations

import ast
import json
import os
import re
import subprocess
import sys
from collections.abc import Mapping
from dataclasses import dataclass
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
DRIVER_SOURCE: Final = REPO_ROOT / "ops" / "loop" / "queue_loop.py"

DISABLE_VAR: Final = "CLAUDE_CODE_DISABLE_BACKGROUND_TASKS"
MAX_TIMEOUT_VAR: Final = "BASH_MAX_TIMEOUT_MS"
DEFAULT_TIMEOUT_VAR: Final = "BASH_DEFAULT_TIMEOUT_MS"
CEILING_VAR: Final = "CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS"

#: The ONE good value of the disable switch.
GOOD_DISABLE_VALUES: Final = frozenset({"1"})

#: The slow end of a whole-tree run: runs were measured from 8:49 up to about
#: fifteen minutes. The one place this figure lives in this file.
MEASURED_SLOW_RUN_S: Final = 15 * 60

#: How many slow runs a timeout must cover.
RUN_MARGIN: Final = 2

#: A timeout must cover a whole-tree run with margin: twice the slow end.
TIMEOUT_FLOOR_MS: Final = RUN_MARGIN * MEASURED_SLOW_RUN_S * 1000

#: And stay bounded, so a genuinely wedged command still dies and the cycle
#: reports rather than holding the lane for the rest of the night.
TIMEOUT_CAP_MS: Final = 60 * 60 * 1000

#: The driver's constant for the local suite's wedge limit, found by NAME.
SUITE_LIMIT_NAME: Final = "DEFAULT_SUITE_TIMEOUT_S"

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


# ===========================================================================
# The lexer - just enough PowerShell to know what is code at script scope
# ===========================================================================


@dataclass(frozen=True)
class ScriptLine:
    """One source line as the static arm sees it.

    Attributes:
        visible: The line with comments blanked; string bodies are kept.
        code: The line with comments AND every string body blanked.
        top: Whether the line begins at script scope - inside no open bracket,
            string, here-string or block comment.
    """

    visible: str
    code: str
    top: bool


#: A ``#`` starts a comment only where a token can start.
_TOKEN_START: Final = frozenset(" \t\r\n;|&(){}[],=")

_HERE_CLOSERS: Final = {"here_dq": '"@', "here_sq": "'@"}


class _Lexer:
    """The state behind ``lex_script``, with one small handler per mode."""

    def __init__(self, text: str) -> None:
        self.text = text
        self.i = 0
        self.stack: list[str] = ["code"]
        self.subs: list[int] = []
        self.depth = 0
        self.visible: list[str] = []
        self.code: list[str] = []
        self.tops: list[bool] = []

    def emit(self, seen: str, as_code: str | None = None) -> None:
        """Consume ``seen``, recording it as visible and as ``as_code``."""
        self.visible.append(seen)
        self.code.append(seen if as_code is None else as_code)
        self.i += len(seen)

    def blank(self, width: int = 1) -> None:
        """Consume comment characters, blank in both views."""
        self.visible.append(" " * width)
        self.code.append(" " * width)
        self.i += width

    def run(self) -> list[ScriptLine]:
        """Lex the whole text.

        Returns:
            One entry per source line.
        """
        handlers = {
            "line": self.comment_line,
            "block": self.comment_block,
            "here_dq": self.here,
            "here_sq": self.here,
            "sq": self.single,
            "dq": self.double,
            "code": self.code_char,
            "sub": self.code_char,
        }
        line_start = True
        while self.i < len(self.text):
            if line_start:
                line_start = False
                self.start_line()
            elif self.text[self.i] == "\n":
                if self.stack[-1] == "line":
                    self.stack.pop()
                self.emit("\n")
                line_start = True
            else:
                handlers[self.stack[-1]]()
        seen_lines = "".join(self.visible).split("\n")
        code_lines = "".join(self.code).split("\n")
        tops = self.tops + [False] * (len(seen_lines) - len(self.tops))
        return [
            ScriptLine(visible=v, code=c, top=t)
            for v, c, t in zip(seen_lines, code_lines, tops, strict=True)
        ]

    def start_line(self) -> None:
        """Record whether the line begins at script scope; close a here-string."""
        self.tops.append(len(self.stack) == 1 and self.depth == 0)
        closer = _HERE_CLOSERS.get(self.stack[-1])
        if closer is not None and self.text.startswith(closer, self.i):
            self.stack.pop()
            self.emit(closer)

    def comment_line(self) -> None:
        """Inside a ``#`` comment, which the newline closes."""
        self.blank()

    def comment_block(self) -> None:
        """Inside a ``<# ... #>`` comment."""
        if self.text.startswith("#>", self.i):
            self.stack.pop()
            self.blank(2)
        else:
            self.blank()

    def here(self) -> None:
        """Inside a here-string body, which only a line-leading closer ends."""
        self.emit(self.text[self.i], " ")

    def single(self) -> None:
        """Inside a single-quoted string, where ``''`` is a literal quote."""
        t, i = self.text, self.i
        if t.startswith("''", i):
            self.emit("''", "  ")
        elif t[i] == "'":
            self.stack.pop()
            self.emit("'")
        else:
            self.emit(t[i], " ")

    def double(self) -> None:
        """Inside a double-quoted string: escapes, ``""`` and ``$(...)``."""
        t, i = self.text, self.i
        if t[i] == "`" and t[i + 1 : i + 2] not in ("", "\n"):
            self.emit(t[i : i + 2], "  ")
        elif t.startswith('""', i):
            self.emit('""', "  ")
        elif t[i] == '"':
            self.stack.pop()
            self.emit('"')
        elif t.startswith("$(", i):
            self.stack.append("sub")
            self.subs.append(0)
            self.emit("$(")
        else:
            self.emit(t[i], " ")

    def code_char(self) -> None:
        """Code, at script level or inside a string's ``$(...)``."""
        if not self.open_context():
            self.bracket()

    def open_context(self) -> bool:
        """Open a comment, string or here-string, or consume an escape.

        Returns:
            Whether anything was consumed.
        """
        t, i = self.text, self.i
        opened: str | None = None
        if t.startswith("<#", i):
            opened = "block"
        elif t[i] == "#" and (t[i - 1] if i else "\n") in _TOKEN_START:
            opened = "line"
        elif t.startswith(('@"', "@'"), i) and not t[i + 2 :].split("\n", 1)[0].strip():
            opened = "here_dq" if t[i + 1] == '"' else "here_sq"
        elif t[i] in "\"'":
            opened = "dq" if t[i] == '"' else "sq"
        elif t[i] == "`" and t[i + 1 : i + 2] not in ("", "\n"):
            self.emit(t[i : i + 2])
            return True
        if opened is None:
            return False
        self.stack.append(opened)
        if opened == "block":
            self.blank(2)
        elif opened == "line":
            self.blank()
        else:
            self.emit(t[i : i + (2 if opened.startswith("here") else 1)])
        return True

    def bracket(self) -> None:
        """Consume one code character, tracking bracket depth."""
        ch = self.text[self.i]
        if self.stack[-1] == "sub":
            if ch == ")" and self.subs[-1] == 0:
                self.stack.pop()
                self.subs.pop()
            elif ch in "()":
                self.subs[-1] += 1 if ch == "(" else -1
        elif ch in "({[":
            self.depth += 1
        elif ch in ")}]":
            self.depth -= 1
        self.emit(ch)


def lex_script(text: str) -> list[ScriptLine]:
    """Split a PowerShell source into lines that know their own context.

    Not a full parser, and it does not need to be one: the static arm accepts an
    assignment only when this lexer says it is plain code at script scope, so a
    construct the lexer misreads makes an assignment UNaccepted - the arm fails
    closed. The states tracked are the ones a plant has used to hide an
    assignment from a line-based reader: brackets (an ``if`` body, a function
    body, a script block), single- and double-quoted strings that span lines,
    here-strings, block comments, and ``$(...)`` inside a double-quoted string.

    Args:
        text: The PowerShell source.

    Returns:
        One entry per source line.
    """
    return _Lexer(text).run()


def _assignment(name: str) -> re.Pattern[str]:
    """The ONE accepted spelling of an assignment to ``name``.

    Args:
        name: The variable name.

    Returns:
        A pattern whose group 1 is the double-quoted value.
    """
    return re.compile(
        r"\s*\$env:" + re.escape(name) + r'\s*=\s*"([^"$`]*)"\s*',
        re.IGNORECASE,
    )


#: A line whose code ends like this carries its statement onto the next line.
_CONTINUATION: Final = re.compile(r"(?:[`|,=+*/%!&<>.\-]|-[A-Za-z]+)$")

#: The environment drive reached as ``$env:NAME`` with a literal, whole name.
_ENV_LITERAL: Final = re.compile(
    r"\$env:[A-Za-z_][A-Za-z0-9_]*(?![A-Za-z0-9_*?\[:])", re.IGNORECASE
)

_ENV_DRIVE: Final = re.compile(r"env:", re.IGNORECASE)

#: The classes and providers that reach the environment without the drive.
_ENV_CLASSES: Final = re.compile(r"environment|scriptblock", re.IGNORECASE)

#: Commands, with their aliases, that can change the environment by a name the
#: text never spells whole - an item or variable mutation, or evaluating text.
_MUTATING_COMMANDS: Final = (
    "Remove-Item",
    "ri",
    "rm",
    "rmdir",
    "rd",
    "del",
    "erase",
    "Clear-Item",
    "cli",
    "Set-Item",
    "si",
    "New-Item",
    "ni",
    "Rename-Item",
    "rni",
    "ren",
    "Move-Item",
    "mi",
    "move",
    "mv",
    "Copy-Item",
    "cpi",
    "cp",
    "copy",
    "Remove-ItemProperty",
    "rp",
    "Set-ItemProperty",
    "sp",
    "Clear-ItemProperty",
    "clp",
    "New-ItemProperty",
    "Set-Content",
    "sc",
    "Add-Content",
    "ac",
    "Clear-Content",
    "clc",
    "Remove-Variable",
    "rv",
    "Clear-Variable",
    "clv",
    "Set-Variable",
    "sv",
    "New-Variable",
    "nv",
    "New-PSDrive",
    "ndr",
    "mount",
    "Invoke-Expression",
    "iex",
    "Invoke-Command",
    "icm",
    "Invoke-Item",
    "ii",
    "Start-Job",
    "sajb",
    "Import-Module",
    "ipmo",
)
_MUTATING: Final = re.compile(
    r"(?<![\w$-])(?:" + "|".join(re.escape(c) for c in _MUTATING_COMMANDS) + r")(?![\w-])",
    re.IGNORECASE,
)

#: A call operator or a dot-source runs code this lexer cannot read.
_INDIRECT_CALL: Final = re.compile(r"&|\.Invoke\s*\(|(?:^|[;{(|])\s*\.\s", re.IGNORECASE)


def _continued(lines: list[ScriptLine], at: int) -> bool:
    """Whether the statement on line ``at`` began on an earlier line.

    Args:
        lines: The lexed script.
        at: The line index.

    Returns:
        True when the nearest earlier line with code ends in a continuation.
    """
    for j in range(at - 1, -1, -1):
        tail = lines[j].code.rstrip()
        if tail:
            return _CONTINUATION.search(tail) is not None
    return False


def _unmodeled_statements(lines: list[ScriptLine], invoked_at: int) -> list[int]:
    """Lines before the child starts that reach the environment an unmodeled way.

    Args:
        lines: The lexed script.
        invoked_at: The invocation's line index.

    Returns:
        One-based line numbers, in order.
    """
    found: list[int] = []
    for index, line in enumerate(lines[: invoked_at + 1]):
        drive = any(
            m.start() == 0 or _ENV_LITERAL.match(line.visible, m.start() - 1) is None
            for m in _ENV_DRIVE.finditer(line.visible)
        )
        indirect = index < invoked_at and _INDIRECT_CALL.search(line.code) is not None
        if drive or indirect or _ENV_CLASSES.search(line.visible) or _MUTATING.search(line.code):
            found.append(index + 1)
    return found


def _static_scan(text: str) -> tuple[list[str], dict[str, str]]:
    """The static arm's faults, and every value it accepted.

    Args:
        text: The PowerShell source.

    Returns:
        The faults, and the accepted value of each variable that had one.
    """
    lines = lex_script(text)
    invocations = [i for i, line in enumerate(lines) if _INVOCATION.search(line.code)]
    if len(invocations) != 1:
        return ["the invocation line is not exactly one"], {}
    invoked_at = invocations[0]
    unmodeled = _unmodeled_statements(lines, invoked_at)
    faults: list[str] = []
    values: dict[str, str] = {}
    for name in REQUIRED_VARS:
        if unmodeled:
            faults.append(
                f"{name}: a statement before the invocation reaches the environment "
                f"in a way this arm does not model (lines {unmodeled})"
            )
        mention = re.compile(re.escape(name), re.IGNORECASE)
        shape = _assignment(name)
        mentions = [i for i, line in enumerate(lines) if mention.search(line.visible)]
        accepted = [
            (i, match)
            for i in mentions
            if lines[i].top
            and not _continued(lines, i)
            and (match := shape.fullmatch(lines[i].visible)) is not None
        ]
        if len(accepted) != len(mentions):
            faults.append(f"{name}: a line mentions it outside an accepted script-scope assignment")
            continue
        if len(accepted) != 1:
            faults.append(f"{name}: not exactly one active assignment")
            continue
        at, match = accepted[0]
        if at >= invoked_at:
            faults.append(f"{name}: assigned after the invocation")
            continue
        value = match.group(1)
        values[name] = value
        fault = value_fault(name, value)
        if fault:
            faults.append(fault)
    return faults, values


def static_env_faults(text: str) -> list[str]:
    """Every reason the runner's source would hand the child a bad environment.

    AN ALLOWLIST OF SHAPES as well as of values. A line may mention a required
    name only as its one double-quoted assignment, at script scope, not continued
    from the line above, before the single invocation. And no statement before
    the invocation may reach the environment any other way - through the drive
    with a wildcard or a built-up name, the Environment class, a mutating item or
    variable command, or code evaluated from text - because each can change what
    the child receives by a name the text never spells whole.

    Args:
        text: The PowerShell source.

    Returns:
        The faults, empty when the environment is good.
    """
    return _static_scan(text)[0]


def launcher_env_values(text: str) -> dict[str, str]:
    """The value the runner's source accepts for each variable it sets.

    Args:
        text: The PowerShell source.

    Returns:
        The accepted values by variable name.
    """
    return _static_scan(text)[1]


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


def _child_env_faults(runner: Path, tmp_path: Path) -> list[str]:
    """Run a runner under Windows PowerShell and grade the stub's environment.

    Args:
        runner: The runner script to run.
        tmp_path: The test's scratch directory.

    Returns:
        The allowlist faults in the environment the stub received.
    """
    shell = _powershell()
    shim_dir, dump = _stub(tmp_path)
    prompt = tmp_path / "prompt.md"
    prompt.write_bytes(b"# a prompt the stub never reads\n")
    cwd = tmp_path / "tree"
    cwd.mkdir(exist_ok=True)
    log = tmp_path / "lane.log"
    subprocess.run(
        [
            shell,
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(runner),
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
    return [
        fault for name in REQUIRED_VARS if (fault := value_fault(name, seen.get(name))) is not None
    ]


def test_control_the_dump_observes_an_inherited_poison(tmp_path: Path) -> None:
    """The known-good control: an un-overridden variable arrives as its poison.

    Without it, a dump that never captured the environment and a runner that
    set every value correctly would both leave the arm below with nothing to
    report. It drives the stub through cmd.exe, so it runs exactly where the
    runtime arm it controls runs; the static arm and its on-disk plants carry
    the property on every other platform (CS-1111).
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
    faults = _child_env_faults(RUNNER_SOURCE, tmp_path)
    assert faults == [], f"the child's environment is not allowlisted: {faults}"


# ===========================================================================
# c. CS-1111 gap 1 - bad plants, written to disk, reddened by the static arm
# ===========================================================================

_ANCHOR_DISABLE: Final = '$env:CLAUDE_CODE_DISABLE_BACKGROUND_TASKS = "1"\n'
_ANCHOR_LAST: Final = '$env:BASH_DEFAULT_TIMEOUT_MS = "2400000"\n'


@dataclass(frozen=True)
class Plant:
    """One bad edit to the real runner.

    Attributes:
        anchor: The runner text the edit replaces, once.
        replacement: What replaces it.
        target: A variable the plant leaves bad, which a fault must name.
    """

    anchor: str
    replacement: str
    target: str


#: The six shapes the runtime arm caught and the old static arm passed, then
#: more of the same family: each hides or undoes an assignment while the
#: variable's name still reads correctly on a line of its own, or never appears.
#: Every leg of the static arm is the ONLY leg that catches at least one plant -
#: the lexer's scope (if-false, function, here-string, multiline string), the
#: continuation (backtick), the mutating commands (built-up name), the
#: Environment class, the drive (provider intrinsics) and the call operator.
PLANTS: Final = {
    "if-false": Plant(_ANCHOR_DISABLE, "if ($false) {\n" + _ANCHOR_DISABLE + "}\n", DISABLE_VAR),
    "uncalled-function": Plant(
        _ANCHOR_DISABLE, "function Set-LaneSwitch {\n" + _ANCHOR_DISABLE + "}\n", DISABLE_VAR
    ),
    "here-string": Plant(_ANCHOR_DISABLE, '$unused = @"\n' + _ANCHOR_DISABLE + '"@\n', DISABLE_VAR),
    "wildcard-remove": Plant(
        _ANCHOR_LAST,
        _ANCHOR_LAST + "Remove-Item Env:CLAUDE_CODE_DISABLE_BACKGROUND_T*\n",
        DISABLE_VAR,
    ),
    "built-name-remove": Plant(
        _ANCHOR_LAST,
        _ANCHOR_LAST
        + '$lane = "CLAUDE_CODE_DISABLE_" + "BACKGROUND_TASKS"\n'
        + 'Remove-Item -LiteralPath ("En" + "v:" + $lane)\n',
        DISABLE_VAR,
    ),
    "wildcard-timeout": Plant(
        _ANCHOR_LAST, _ANCHOR_LAST + "Remove-Item Env:BASH_*_TIMEOUT_MS\n", MAX_TIMEOUT_VAR
    ),
    "set-environment-variable": Plant(
        _ANCHOR_LAST,
        _ANCHOR_LAST
        + "[Environment]::SetEnvironmentVariable("
        + '"CLAUDE_CODE_DISABLE_" + "BACKGROUND_TASKS", "0")\n',
        DISABLE_VAR,
    ),
    "backtick-continuation": Plant(
        _ANCHOR_DISABLE, "Write-Output `\n" + _ANCHOR_DISABLE, DISABLE_VAR
    ),
    "multiline-string": Plant(
        _ANCHOR_DISABLE, "$null = '\n" + _ANCHOR_DISABLE + "'\n", DISABLE_VAR
    ),
    "provider-intrinsics-remove": Plant(
        _ANCHOR_LAST,
        _ANCHOR_LAST
        + "$ExecutionContext.InvokeProvider.Item.Remove("
        + '"Env:CLAUDE_CODE_DISABLE_BACKGROUND_T*", $false)\n',
        DISABLE_VAR,
    ),
    "call-operator-remove": Plant(
        _ANCHOR_LAST,
        _ANCHOR_LAST + '& ("Remove-" + "Item") ("En" + "v:CLAUDE_CODE_DISABLE_BACKGROUND_T*")\n',
        DISABLE_VAR,
    ),
}


def _write_plant(kind: str, tmp_path: Path) -> Path:
    """The real runner with one plant applied, written to disk as bytes.

    Args:
        kind: The plant's key.
        tmp_path: The test's scratch directory.

    Returns:
        The planted runner's path.
    """
    plant = PLANTS[kind]
    text = RUNNER_SOURCE.read_bytes().decode("ascii")
    mutated = text.replace(plant.anchor, plant.replacement, 1)
    applied = mutated != text
    assert applied, f"the {kind} plant never applied"
    planted = tmp_path / "planted" / "run_lane.ps1"
    planted.parent.mkdir(parents=True, exist_ok=True)
    planted.write_bytes(mutated.encode("ascii"))
    return planted


def test_control_the_real_runner_copied_to_disk_stays_green(tmp_path: Path) -> None:
    """The pristine floor: the same write path with no plant is reported for nothing."""
    copied = tmp_path / "pristine" / "run_lane.ps1"
    copied.parent.mkdir()
    copied.write_bytes(RUNNER_SOURCE.read_bytes())
    faults = static_env_faults(copied.read_bytes().decode("ascii"))
    assert faults == []


@pytest.mark.parametrize("kind", sorted(PLANTS))
def test_control_each_plant_is_bad_at_runtime(kind: str, tmp_path: Path) -> None:
    """A plant the child never feels would make the arm below vacuous.

    Runs only where the runtime arm runs; its job is to prove, on a Windows
    box, that every plant the static arm must redden really does hand the
    child a bad environment.
    """
    _powershell()
    planted = _write_plant(kind, tmp_path)
    faults = _child_env_faults(planted, tmp_path)
    assert faults != [], f"the {kind} plant left the child's environment good"


@pytest.mark.parametrize("kind", sorted(PLANTS))
def test_the_static_arm_reddens_on_each_plant(kind: str, tmp_path: Path) -> None:
    """GAP 1: the static arm alone catches each plant, on every platform."""
    planted = _write_plant(kind, tmp_path)
    faults = static_env_faults(planted.read_bytes().decode("ascii"))
    target = PLANTS[kind].target
    named = any(fault.startswith(target) for fault in faults)
    assert named, f"the {kind} plant was not reported against {target}: {faults}"


# ===========================================================================
# d. CS-1111 gap 2 - a tracked settings file cannot override the launcher
# ===========================================================================

#: Every settings file the CLI could load from this tree, at any depth.
SETTINGS_PATHSPEC: Final = ":(glob)**/.claude/settings*.json"

#: The project settings file, which is tracked on every checkout.
PROJECT_SETTINGS: Final = ".claude/settings.json"


def tracked_settings_files() -> list[str]:
    """Every TRACKED settings file, POSIX-separated.

    Tracked only, by design: an untracked local file is per-machine and is not
    what a fresh lane worktree checks out.

    Returns:
        The repository-relative paths, sorted.
    """
    git = resolve_tool("git")
    assert git is not None, "git could not be resolved from PATH"
    out = subprocess.run(
        [git, "ls-files", "-z", "--", SETTINGS_PATHSPEC],
        capture_output=True,
        check=True,
        cwd=REPO_ROOT,
        timeout=_CHILD_TIMEOUT_S,
    ).stdout
    return sorted(p.decode("utf-8").replace("\\", "/") for p in out.split(b"\0") if p)


def settings_env_faults(label: str, settings: object, launcher: Mapping[str, str]) -> list[str]:
    """Every launcher variable a settings file's ``env`` block would override.

    Args:
        label: The file's repository-relative path, for the fault text.
        settings: The parsed settings document.
        launcher: The value the launcher sets for each variable.

    Returns:
        The faults. Values are never echoed - a settings file can carry secrets.
    """
    if not isinstance(settings, dict):
        return [f"{label}: not a JSON object"]
    env = settings.get("env")
    if env is None:
        return []
    if not isinstance(env, dict):
        return [f"{label}: its env block is not an object"]
    faults: list[str] = []
    for key, value in env.items():
        # Windows compares environment names without case, so the CLI's copy
        # of a lower-cased key overrides the launcher's variable all the same.
        name = str(key).upper()
        if name in launcher and value != launcher[name]:
            faults.append(f"{label}: env {name} is not the launcher's value")
    return faults


def test_control_the_settings_enumeration_finds_the_project_file() -> None:
    """Without it an enumeration that found nothing would grade nothing, green."""
    found = tracked_settings_files()
    has_project = PROJECT_SETTINGS in found
    assert has_project, "the tracked settings enumeration missed the project file"


@pytest.mark.parametrize(
    ("env", "reported"),
    [
        ({}, set()),
        ({"PYTHONUTF8": "1"}, set()),
        ({DISABLE_VAR: "1"}, set()),
        ({DISABLE_VAR: "0"}, {DISABLE_VAR}),
        ({MAX_TIMEOUT_VAR: "600000"}, {MAX_TIMEOUT_VAR}),
        ({DEFAULT_TIMEOUT_VAR: 2400000}, {DEFAULT_TIMEOUT_VAR}),
        ({DISABLE_VAR.lower(): "0"}, {DISABLE_VAR}),
        ({CEILING_VAR: ""}, {CEILING_VAR}),
    ],
)
def test_control_a_settings_value_that_is_not_the_launchers_is_reported(
    env: dict[str, object], reported: set[str]
) -> None:
    launcher = {
        DISABLE_VAR: "1",
        MAX_TIMEOUT_VAR: "2400000",
        DEFAULT_TIMEOUT_VAR: "2400000",
        CEILING_VAR: "2400000",
    }
    faults = settings_env_faults("planted.json", {"env": env}, launcher)
    named = {name for name in REQUIRED_VARS if any(name in fault for fault in faults)}
    assert named == reported


def test_control_a_malformed_env_block_is_reported() -> None:
    faults = settings_env_faults("planted.json", {"env": ["not", "an", "object"]}, {})
    assert faults != []


def test_no_tracked_settings_file_overrides_the_launcher() -> None:
    """GAP 2: the CLI copies a settings ``env`` block over the process env."""
    launcher = launcher_env_values(RUNNER_SOURCE.read_bytes().decode("ascii"))
    set_by_launcher = sorted(launcher)
    assert set_by_launcher == sorted(REQUIRED_VARS)
    faults: list[str] = []
    for rel in tracked_settings_files():
        document = json.loads((REPO_ROOT / rel).read_bytes().decode("utf-8"))
        faults += settings_env_faults(rel, document, launcher)
    assert faults == [], f"a tracked settings file overrides the launcher: {faults}"


# ===========================================================================
# e. CS-1111 gap 4 - the Bash timeout against the driver's suite wedge limit
# ===========================================================================


def module_int_constant(source: str, name: str) -> int | None:
    """A module-level integer constant, found by name in Python source.

    Args:
        source: The module's source.
        name: The constant's name.

    Returns:
        Its value when exactly one top-level assignment binds it to an integer
        literal, else None.
    """
    values: list[ast.expr | None] = []
    for node in ast.parse(source).body:
        assigned = isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == name for target in node.targets
        )
        annotated = (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == name
        )
        if isinstance(node, ast.Assign | ast.AnnAssign) and (assigned or annotated):
            values.append(node.value)
    if len(values) != 1:
        return None
    value = values[0]
    if isinstance(value, ast.Constant) and type(value.value) is int:
        return value.value
    return None


def timeout_relation_faults(bash_ms: int, suite_limit_s: int) -> list[str]:
    """Whether a Bash timeout sits between the expected suite run and the wedge limit.

    Args:
        bash_ms: The launcher's Bash timeout, in milliseconds.
        suite_limit_s: The driver's local-suite wedge limit, in seconds.

    Returns:
        The faults, empty when the relation holds.
    """
    expected_ms = RUN_MARGIN * MEASURED_SLOW_RUN_S * 1000
    limit_ms = suite_limit_s * 1000
    faults: list[str] = []
    if limit_ms < expected_ms:
        faults.append("the suite wedge limit does not cover the expected run with margin")
    if bash_ms < expected_ms:
        faults.append("the Bash timeout does not cover the expected suite run with margin")
    if bash_ms > limit_ms:
        faults.append("the Bash timeout outlives the driver's suite wedge limit")
    return faults


@pytest.mark.parametrize(
    ("bash_ms", "limit_s", "good"),
    [
        (2_400_000, 5400, True),
        (RUN_MARGIN * MEASURED_SLOW_RUN_S * 1000, 5400, True),
        (5400 * 1000, 5400, True),
        (RUN_MARGIN * MEASURED_SLOW_RUN_S * 1000 - 1, 5400, False),
        (5400 * 1000 + 1, 5400, False),
        (2_400_000, 1800, False),
        (1_000_000, 1500, False),
    ],
)
def test_control_the_timeout_relation(bash_ms: int, limit_s: int, good: bool) -> None:
    faults = timeout_relation_faults(bash_ms, limit_s)
    assert (faults == []) is good


#: A literal the constant finder must return unchanged.
_PROBE_LITERAL: Final = 5400


def test_control_the_suite_limit_is_found_only_as_one_integer_literal() -> None:
    assert module_int_constant(f"X_S = {_PROBE_LITERAL}\n", "X_S") == _PROBE_LITERAL
    assert module_int_constant(f"X_S: int = {_PROBE_LITERAL}\n", "X_S") == _PROBE_LITERAL
    assert module_int_constant("X_S = 2 * 2700\n", "X_S") is None
    assert module_int_constant("X_S = 5400\nX_S = 60\n", "X_S") is None
    assert module_int_constant("X_S = True\n", "X_S") is None
    assert module_int_constant("Y_S = 5400\n", "X_S") is None


def test_the_bash_timeout_exceeds_the_expected_suite_run_within_the_wedge_limit() -> None:
    """GAP 4: both numbers derived from their owners, and the relation asserted.

    THE LOWER BOUND, ``timeout >= RUN_MARGIN * expected run``. A foreground Bash
    call is killed at its timeout, so a timeout that does not cover a whole
    suite run with margin brings the CS-1108 kill back by another route: the
    suite dies mid-run and the cycle commits nothing. The expected run is the
    measured slow end, because the driver's constant is a wedge ceiling and says
    only "tens of minutes" about the work it bounds.

    THE UPPER BOUND, ``timeout <= the driver's wedge limit``, and this is the
    direction that needs saying. The driver names ``DEFAULT_SUITE_TIMEOUT_S`` as
    the point past which a local suite run is a WEDGE, not work. A worker's
    foreground call allowed to outlive that point would hold a run the driver
    itself has already classified as wedged, spending the cycle's budget on it
    and ending in the driver's hard kill, which writes no cycle report. Keeping
    the Bash timeout at or below the limit means the CLI kills a wedged command
    first, the call returns, and the worker still reports. The same chain also
    checks that the limit itself covers the expected run with margin, so a
    lowered limit cannot slide under the timeout unnoticed.
    """
    suite_limit_s = module_int_constant(
        DRIVER_SOURCE.read_bytes().decode("utf-8"), SUITE_LIMIT_NAME
    )
    assert suite_limit_s is not None, f"{SUITE_LIMIT_NAME} is not one integer literal"
    launcher = launcher_env_values(RUNNER_SOURCE.read_bytes().decode("ascii"))
    faults: list[str] = []
    for name in (MAX_TIMEOUT_VAR, DEFAULT_TIMEOUT_VAR):
        value = launcher.get(name)
        if value is None or _DECIMAL.fullmatch(value) is None:
            faults.append(f"{name}: the launcher sets no plain integer")
            continue
        faults += [f"{name}: {f}" for f in timeout_relation_faults(int(value), suite_limit_s)]
    assert faults == [], f"the Bash timeout and the suite wedge limit disagree: {faults}"


# ===========================================================================
# f. The prompt, bound to the launcher
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


# ---------------------------------------------------------------------------
# CS-1111 gap 3 - the foreground-only statement forbids shell-level detaching
# ---------------------------------------------------------------------------

#: The sentence that makes the paragraph the foreground-only statement.
_FOREGROUND_STATEMENT: Final = re.compile(r"A\s+long\s+command\s+runs\s+in\s+the\s+foreground")

#: What that paragraph must forbid, token by token. The switch removes the
#: tool's parameter only; each of these detaches a child at the shell level.
DETACH_TOKENS: Final = (
    ("the prohibition itself", r"\*\*Never\s+detach\s+a\s+command\s+at\s+the\s+shell\s+level"),
    ("a trailing ampersand", r"trailing\s+`&`"),
    ("nohup", r"`nohup`"),
    ("Start-Process", r"`Start-Process`"),
    ("start /b", r"`start\s+/b`"),
)


def detach_faults(text: str) -> list[str]:
    """What the foreground-only statement fails to forbid.

    Scoped to the ONE paragraph that says a long command runs in the
    foreground, so the tokens appearing anywhere else in the prompt do not count.

    Args:
        text: The prompt.

    Returns:
        The missing labels, or a single fault when there is no one statement.
    """
    paragraphs = [p for p in re.split(r"\n[ \t]*\n", text) if _FOREGROUND_STATEMENT.search(p)]
    if len(paragraphs) != 1:
        return ["the foreground-only statement is not exactly one paragraph"]
    return [label for label, pattern in DETACH_TOKENS if not re.search(pattern, paragraphs[0])]


def test_control_a_statement_without_the_detach_prohibition_is_reported(
    prompt_text: str,
) -> None:
    """Mutation on the real prompt: cut the prohibition and every token is missing."""
    at = prompt_text.find("**Never detach a command")
    found = at >= 0
    assert found, "the prohibition sentence is not in the prompt"
    end = prompt_text.find("\n\n", at)
    cut = prompt_text[:at] + prompt_text[end:]
    faults = detach_faults(cut)
    assert faults == [label for label, _pattern in DETACH_TOKENS]


def test_control_detach_tokens_elsewhere_do_not_count() -> None:
    doc = (
        "A long command runs in the foreground with an explicit timeout.\n\n"
        "**Never detach a command at the shell level either:** no trailing `&`, "
        "no `nohup`, no `Start-Process`, no `start /b`.\n"
    )
    faults = detach_faults(doc)
    assert faults == [label for label, _pattern in DETACH_TOKENS]


def test_the_foreground_statement_forbids_shell_level_detaching(prompt_text: str) -> None:
    """GAP 3: the switch removes ``run_in_background``, not a shell's own detach."""
    faults = detach_faults(prompt_text)
    assert faults == [], f"the foreground-only statement does not forbid: {faults}"


@pytest.fixture(scope="module")
def prompt_text() -> str:
    """The prompt, decoded strictly as ASCII.

    Returns:
        The prompt's text.
    """
    return PROMPT_SOURCE.read_bytes().decode("ascii")
