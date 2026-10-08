"""CS-1272 H - every tracked path that starts a headless `claude` goes through the kit.

FLEET item 10: the fleet kit's spawn helper, `fleet_headless.spawn` in
`ops/fleet_kit/fleet_headless.py`, is the ONLY path that starts `claude`.
`CLAUDE.md` precedence clause (c) states the one exception this tree carries
until CS-1231 slice C finishes: `ops/loop/run_lane.ps1` still starts `claude`
directly, and QUEUE_STOP holds the lane that runs it. This module grades that
at the grep level:

  1. THE WALK finds every tracked file that starts the CLI DIRECTLY, by shape:
     Python string constants (never a docstring), PowerShell, shell, batch and
     JavaScript command lines (never a comment), the hook commands of the
     tracked Claude settings, and the code in the markdown command files.
  2. What it finds is EXACTLY the kit itself plus the one named exception. A
     new direct start reddens it, and so does the exception going stale: when
     run_lane.ps1 stops starting `claude`, its exception is retired here and in
     `CLAUDE.md` together.

WHY TESTS ARE NOT WALKED. Every `claude` a test starts is a planted shim on a
temporary PATH - a `claude.cmd` the test itself writes. The excluded roots are
NAMED (`EXCLUDED_ROOTS`), never discovered.

PLANTED CONTROLS front the walk, one per shape, each beside near misses that
must NOT read as a start: prose naming the `claude -p` mode, a docstring, a
comment, a variable call whose resolution is what gets flagged, and a hook
script whose file name begins with `claude`.

No arm renders an environment value (CLAUDE.md rule 13): git is run with the
inherited environment and nothing of it is bound, compared or printed.
"""

from __future__ import annotations

import ast
import json
import re
import subprocess
from collections.abc import Callable
from pathlib import Path, PurePosixPath
from typing import Final

import pytest

ROOT: Final = Path(__file__).resolve().parents[2]

#: The kit's spawn helper - the one sanctioned path that starts `claude`.
KIT: Final = "ops/fleet_kit/fleet_headless.py"

#: The ONE named exception, CLAUDE.md precedence clause (c): held by QUEUE_STOP
#: until CS-1231 slice C moves the lane onto the kit.
RUN_LANE: Final = "ops/loop/run_lane.ps1"
DIRECT_START_EXCEPTIONS: Final = frozenset({RUN_LANE})

#: The one tracked module that starts its worker through the kit today.
RESPONDER: Final = "ops/loop/inbox_responder.py"

#: Not walked: every `claude` started under these roots is a planted shim.
EXCLUDED_ROOTS: Final = ("tests/", "shell/test/")

#: The markdown COMMAND files - prompts and instructions an agent executes.
#: Records (`docs/`, the ledger, the hand-off) are not commands and are not walked.
MD_ROOTS: Final = (".claude/", "tools/", "ops/", "scripts/")

#: Extensionless shell scripts live here.
SH_DIRS: Final = (".githooks/",)

#: The tracked Claude settings, whose hook commands run under sh.
JSON_ROOTS: Final = (".claude/",)

#: The mode's own name. Prose calls a worker "a `claude -p` process"; an inline
#: span holding exactly this is a name, not an invocation. Inside a fenced
#: block it is still an invocation.
MODE_NAME: Final = "claude -p"

_EXE: Final = r"claude(?:\.exe|\.cmd)?"
_END: Final = r"['\"]?(?![\w.-])"
_PY_EXE: Final = re.compile(rf"(?i){_EXE}")
_PY_COMMAND: Final = re.compile(rf"(?i)\s*{_EXE}\s+-")
_PS_START: Final = re.compile(
    rf"(?i)(?:\bGet-Command\s+(?:-Name\s+)?['\"]?{_EXE}{_END}"
    rf"|&\s*['\"]?{_EXE}{_END}"
    rf"|^\s*{_EXE}\s"
    rf"|\|\s*{_EXE}{_END}"
    rf"|\bStart-Process\s+(?:-FilePath\s+)?['\"]?{_EXE}{_END}"
    rf"|['\"]{_EXE}['\"])"
)
_SH_START: Final = re.compile(
    rf"(?:^|[;&|`]|\$\(|\bexec\s|\bcommand\s+-v\s|\bwhich\s)\s*['\"]?{_EXE}{_END}"
)
_BAT_START: Final = re.compile(
    rf"(?i)(?:^|[&|]|\bcall\s|\bstart\s+(?:\"[^\"]*\"\s+)?)\s*@?['\"]?{_EXE}{_END}"
)
_JS_START: Final = re.compile(rf"(?i)['\"`]{_EXE}(?:['\"`]|\s+-)")
_MD_CMD: Final = re.compile(rf"^\s*(?:\$\s+|&\s*)?['\"]?{_EXE}['\"]?\s+\S")
_MD_SPAN: Final = re.compile(r"`([^`\n]+)`")
_JSON_STRING: Final = re.compile(r'"((?:[^"\\]|\\.)*)"')
_PS_BLOCK_COMMENT: Final = re.compile(r"<#.*?#>", re.DOTALL)


def _shape(rel: str) -> str | None:
    """Which reader a repo-relative path gets, or None when it is not walked."""
    if rel.startswith(EXCLUDED_ROOTS):
        return None
    path = PurePosixPath(rel)
    suffix = path.suffix.lower()
    shapes = {
        ".py": "py",
        ".ps1": "ps",
        ".psm1": "ps",
        ".sh": "sh",
        ".bash": "sh",
        ".js": "js",
        ".cjs": "js",
        ".mjs": "js",
        ".cmd": "bat",
        ".bat": "bat",
    }
    if suffix in shapes:
        return shapes[suffix]
    if suffix == ".md" and rel.startswith(MD_ROOTS):
        return "md"
    if suffix == ".json" and rel.startswith(JSON_ROOTS):
        return "json"
    if not suffix and rel.startswith(SH_DIRS):
        return "sh"
    return None


def _docstring_nodes(tree: ast.AST) -> set[int]:
    owners = (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
    found: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, owners) and node.body:
            first = node.body[0]
            if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant):
                found.add(id(first.value))
    return found


def _py_starts(text: str) -> list[int]:
    tree = ast.parse(text)
    docstrings = _docstring_nodes(tree)
    lines: set[int] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
            continue
        if id(node) in docstrings:
            continue
        value = node.value.strip()
        if _PY_EXE.fullmatch(value) or _PY_COMMAND.match(node.value):
            lines.add(node.lineno)
    return sorted(lines)


def _line_starts(text: str, pattern: re.Pattern[str], comment: str) -> list[int]:
    """Line numbers whose code - comment lines dropped - matches ``pattern``."""
    return [
        number
        for number, line in enumerate(text.splitlines(), start=1)
        if not line.lstrip().startswith(comment) and pattern.search(line)
    ]


def _ps_starts(text: str) -> list[int]:
    """PowerShell: block comments blanked line-for-line, then comment lines dropped."""
    blanked = _PS_BLOCK_COMMENT.sub(lambda m: "\n" * m.group(0).count("\n"), text)
    return _line_starts(blanked, _PS_START, "#")


def _bat_starts(text: str) -> list[int]:
    return [
        number
        for number, line in enumerate(text.splitlines(), start=1)
        if not re.match(r"(?i)\s*(?:@?rem\b|::)", line) and _BAT_START.search(line)
    ]


def _json_starts(text: str) -> list[int]:
    """Every JSON string on a line, decoded, read as an sh command line."""
    found: list[int] = []
    for number, line in enumerate(text.splitlines(), start=1):
        for literal in _JSON_STRING.findall(line):
            try:
                value = json.loads(f'"{literal}"')
            except ValueError:
                continue
            if _SH_START.search(value):
                found.append(number)
                break
    return found


def _md_starts(text: str) -> list[int]:
    """Fenced code lines, and inline spans outside fences, that invoke the CLI."""
    found: list[int] = []
    fenced = False
    for number, line in enumerate(text.splitlines(), start=1):
        if line.lstrip().startswith("```"):
            fenced = not fenced
            continue
        if fenced:
            if _MD_CMD.search(line):
                found.append(number)
            continue
        spans = _MD_SPAN.findall(line)
        if any(_MD_CMD.search(span) and span.strip() != MODE_NAME for span in spans):
            found.append(number)
    return found


def direct_starts(rel: str, text: str) -> list[int]:
    """The line numbers in one file that start the `claude` CLI directly.

    Args:
        rel: The repo-relative, forward-slashed path - it picks the reader.
        text: The file's text.

    Returns:
        Sorted line numbers; empty for a path that is not walked.
    """
    readers: dict[str, Callable[[str], list[int]]] = {
        "py": _py_starts,
        "ps": _ps_starts,
        "sh": lambda body: _line_starts(body, _SH_START, "#"),
        "js": lambda body: _line_starts(body, _JS_START, "//"),
        "bat": _bat_starts,
        "json": _json_starts,
        "md": _md_starts,
    }
    shape = _shape(rel)
    return [] if shape is None else readers[shape](text)


def tracked(root: Path) -> list[str]:
    """Every path git tracks under ``root``, repo-relative and forward-slashed."""
    done = subprocess.run(
        ["git", "-C", str(root), "ls-files", "--cached", "-z"],
        capture_output=True,
        check=False,
        timeout=120,
    )
    listed_ok = done.returncode == 0
    assert listed_ok, "git ls-files did not list the tree"
    names = done.stdout.decode("utf-8", "surrogateescape").split("\0")
    return sorted(name for name in names if name)


def _text(root: Path, rel: str) -> str | None:
    path = root / rel
    if not path.is_file():
        return None
    return path.read_bytes().decode("utf-8", "replace")


def walk(root: Path) -> dict[str, list[int]]:
    """Every walked tracked file that starts `claude` directly, with its lines."""
    found: dict[str, list[int]] = {}
    for rel in tracked(root):
        if _shape(rel) is None:
            continue
        text = _text(root, rel)
        if text is None:
            continue
        lines = direct_starts(rel, text)
        if lines:
            found[rel] = lines
    return found


def kit_callers(root: Path) -> set[str]:
    """Tracked modules that call ``<alias of fleet_headless>.spawn(...)``."""
    callers: set[str] = set()
    for rel in tracked(root):
        if _shape(rel) != "py" or rel == KIT:
            continue
        text = _text(root, rel)
        if text is None:
            continue
        tree = ast.parse(text)
        aliases: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == "ops.fleet_kit":
                aliases.update(a.asname or a.name for a in node.names if a.name == "fleet_headless")
            elif isinstance(node, ast.Import):
                aliases.update(
                    a.asname for a in node.names if a.name.endswith("fleet_headless") and a.asname
                )
        spawns = any(
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "spawn"
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id in aliases
            for node in ast.walk(tree)
        )
        if spawns:
            callers.add(rel)
    return callers


# --- planted controls ----------------------------------------------------------

PLANTED_STARTS: Final[list[tuple[str, str, list[int]]]] = [
    ("x.py", 'import subprocess\nsubprocess.run(["claude", "-p"])\n', [2]),
    ("x.py", 'CMD = "claude -p --model sonnet"\n', [1]),
    ("x.py", 'EXE = shutil.which("claude.exe")\n', [1]),
    ("x.ps1", "$c = (Get-Command claude).Source\n", [1]),
    ("x.ps1", "'x' | & claude -p\n", [1]),
    ("x.ps1", "claude -p --model sonnet\n", [1]),
    ("x.ps1", '$exe = "claude.exe"\n', [1]),
    ("x.ps1", "Start-Process -FilePath claude -ArgumentList '-p'\n", [1]),
    ("x.sh", 'claude -p "go"\n', [1]),
    ("x.sh", 'out=$(claude -p "go")\n', [1]),
    ("x.sh", "cd x && claude --print go\n", [1]),
    (".githooks/post-merge", "#!/bin/sh\nexec claude -p go\n", [2]),
    ("x.js", 'spawn("claude", ["-p"]);\n', [1]),
    ("x.cmd", "@call claude -p go\n", [1]),
    (".claude/settings.json", '{"hooks": {\n "Stop": [{"command": "claude -p go"}]}}\n', [2]),
    (".claude/commands/x.md", '```\nclaude -p --model opus "go"\n```\n', [2]),
    (".claude/commands/x.md", "```\nclaude -p\n```\n", [2]),
    ("tools/x.md", "Run `claude -p --model sonnet` now.\n", [1]),
]

PLANTED_NEAR_MISSES: Final[list[tuple[str, str, list[int]]]] = [
    ("x.py", '"""A `claude -p` worker, described."""\n', []),
    ("x.py", "# claude -p\nX = 1\n", []),
    ("x.py", 'P = "claude-code"\n', []),
    ("x.ps1", "# & claude -p\n", []),
    ("x.ps1", "<#\n& claude -p\n#>\n", []),
    ("x.ps1", "& $claude -p\n", []),
    ("x.sh", "sh tools/claude_hook.sh pretooluse\n", []),
    ("x.sh", "# claude -p\n", []),
    ("x.js", '// spawn("claude")\n', []),
    (".claude/settings.json", '{"command": "sh tools/claude_hook.sh"}\n', []),
    ("tools/x.md", "You are a `claude -p` process.\n", []),
    ("tools/x.md", "See `.claude/settings.json`.\n", []),
    ("docs/x.md", "```\nclaude -p go\n```\n", []),
    ("tests/x.py", 'subprocess.run(["claude", "-p"])\n', []),
    ("shell/test/x.js", 'spawn("claude", ["-p"]);\n', []),
]


@pytest.mark.parametrize(
    ("rel", "text", "lines"),
    PLANTED_STARTS,
    ids=[f"{rel}-{i}" for i, (rel, _t, _l) in enumerate(PLANTED_STARTS)],
)
def test_a_planted_direct_start_is_found(rel: str, text: str, lines: list[int]) -> None:
    assert direct_starts(rel, text) == lines


@pytest.mark.parametrize(
    ("rel", "text", "lines"),
    PLANTED_NEAR_MISSES,
    ids=[f"{rel}-{i}" for i, (rel, _t, _l) in enumerate(PLANTED_NEAR_MISSES)],
)
def test_a_planted_near_miss_is_not_a_start(rel: str, text: str, lines: list[int]) -> None:
    assert direct_starts(rel, text) == lines


# --- the live tree ---------------------------------------------------------------


def test_the_walk_sees_the_kits_own_start() -> None:
    """POSITIVE CONTROL: the helper itself resolves and starts the CLI, and the walk sees it."""
    assert KIT in walk(ROOT)


def test_every_direct_start_is_the_kit_or_the_one_named_exception() -> None:
    """FLEET item 10 with CLAUDE.md clause (c): nothing else starts `claude` directly.

    A new direct start appears here by path. A stale exception does too: the
    expected set holds run_lane.ps1, so the day it stops starting `claude` this
    arm reddens until the exception is retired.
    """
    direct = sorted(set(walk(ROOT)) - {KIT})
    assert direct == sorted(DIRECT_START_EXCEPTIONS)


def test_the_exception_is_the_one_claude_md_names() -> None:
    """The exception's authority is CLAUDE.md clause (c); it may not outlive that clause."""
    text = (ROOT / "CLAUDE.md").read_bytes().decode("utf-8", "replace")
    assert sorted(path for path in DIRECT_START_EXCEPTIONS if path in text) == [RUN_LANE]


def test_the_inbox_responder_starts_its_worker_through_the_kit() -> None:
    """The positive half: the responder is a kit caller, so its start is the kit's."""
    callers = kit_callers(ROOT)
    assert RESPONDER in callers
