#!/usr/bin/env python3
"""CS-909 slice C - scripts/make_shortcut.py, the desktop shortcut for the shell.

WHAT THIS GRADES. The companion window is an Electron app, and launching it
from a terminal - or through a ``.cmd`` or ``.vbs`` wrapper - flashes a console
window on the way past. A ``.lnk`` pointed straight at the GUI-subsystem
``electron.exe`` does not. Nothing in the Python standard library writes a
``.lnk``, and ``pyproject.toml`` declares ``dependencies = []`` and calls that a
decision (BOOTSTRAP.md section 11), so the shortcut is written by shelling out
to PowerShell's ``WScript.Shell`` COM object. What is under test is the argv,
the refusal behaviour, and the privacy of every message - not any file format
this project wrote.

THE ARMS ARE SPLIT INTO A PURE HALF AND A LIVE HALF, the same shape as
tests/test_make_cert.py and for the same reason. The pure half asserts the
rendered PowerShell text and the argv element by element, on synthetic relative
paths, and runs on a machine with no Electron, no PowerShell and no display -
which is the machine tier 1 runs on (``.github/workflows/tier1.yml`` is
``ubuntu-latest``). The live half drives the real entry point end to end
against a STUB PowerShell that this suite writes, so the staging, the rename,
the wrote-nothing check and the exit codes are all exercised where no real
PowerShell exists. Neither half is sufficient alone: the pure half cannot tell
whether the rendered script would ever run, and the live half would stay green
if the rendered script drifted into a different but equally runnable form.

NOTHING IS PATCHED IN THE LIVE HALF. The absent tool is a PATH pointing at an
empty directory; the failing tool is a real executable stub. That is the
tests/test_make_cert.py idiom, and it is what keeps the arms about
``shutil.which``, PATH and the filesystem rather than about a mock.

THE OPERATOR'S REAL DESKTOP IS NEVER TOUCHED, and that is a hard precondition
rather than a courtesy. Every arm below either passes ``--desktop-dir`` or sets
``CLOCKSPEED_DESKTOP_DIR``, both pointed inside ``tmp_path``. No arm calls the
default resolver without an override in place.

THE PLANTED CANARY IS THE POINT OF THE PRIVACY ARMS. The Desktop lives under
the user profile, so its path carries the Windows account name - personal data
under CLAUDE.md non-negotiable 3. A token that LOOKS like an account name is
planted in a temporary directory, every refusal is driven through it, and the
token is asserted absent from stdout, from stderr and from any exception text.
The arm carries its own CONTROL: ``redact()`` is shown to leave the token
intact, so the absence is evidence the script never printed a path rather than
evidence the redactor happened to scrub it.

NO PATH IS EVER THE SUBJECT OF AN ASSERTION. pytest renders a failing frame's
arguments, so an assertion holding a real path would print one on failure;
every arm binds a scalar - a count, a code, a boolean, a digest - and asserts on
that.
"""

from __future__ import annotations

import ast
import errno
import hashlib
import importlib.util
import os
import re
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
MAKE_SHORTCUT_SOURCE = REPO_ROOT / "scripts" / "make_shortcut.py"

#: Synthetic, relative, and never touched on disk. The pure arms assert on the
#: rendered PowerShell text, so their paths must not carry a home directory into
#: a failure message - which a tmp_path would.
SHELL_STUB = Path("shell")
LINK_STUB = Path("desk") / "Clockspeed.lnk"

#: A token that looks like an account name, planted where a Desktop path would
#: sit. Deliberately free of digits so the account-id backstop in ``redact()``
#: cannot claim it, and deliberately unlike any real account name so the
#: environment-derived redaction rules cannot either. If a refusal ever renders
#: its destination, this is what shows up.
CANARY_ACCOUNT = "HomeLikeCanaryOperator"

#: How many distinct refusals the planted-canary arm drives. Named rather than
#: written at the assertion so the floor and the probe list cannot drift apart
#: silently - a pooled absence is otherwise met by its strongest member.
CANARY_REFUSALS = 6

#: A SECOND CANARY, AND DELIBERATELY THE OPPOSITE CLASS OF ONE. The token above
#: is built to SURVIVE ``redact()``, which is exactly what makes it a control
#: for "the script never printed its destination" - but it also makes it unable
#: to grade whether a message was redacted, because it reads identically on
#: both sides of that question. An arm that drove it through a message the
#: script printed IN CLEAR would report a leak that redaction could not have
#: fixed, and an arm that drove it through a redacted one would report a leak
#: that was not there. So the redaction arms need the complement: a token the
#: redactor CLAIMS, whose presence in a stream therefore means the value
#: reached the operator without passing the chokepoint.
#:
#: A DIGIT RUN, because that is the one rule in ``redact()`` that holds on every
#: machine. The account name and the home prefix are read out of THIS
#: environment, so a token built to match either would be scrubbed on the
#: operator's machine and passed through on the tier 1 runner - green in CI for
#: a reason that has nothing to do with the script. The account-id backstop is
#: a pattern rather than a lookup, so it claims this token everywhere.
#:
#: ALL ZEROS, AND LONGER THAN THE BACKSTOP'S FLOOR. No real platform account id
#: is all zeros, so nothing here resembles a person's identifier; and the run
#: is well clear of the minimum the backstop requires, so the control below
#: keeps holding if that minimum is raised. If it is ever raised past this
#: length the control reddens and names the reason rather than going quiet.
CANARY_ACCOUNT_ID = "0" * 17

#: How many distinct outcomes the operator-supplied-name arm drives. Named for
#: the same reason ``CANARY_REFUSALS`` is: a pooled absence is met by its
#: strongest member, so the floor and the probe list must not drift apart.
CANARY_NAME_OUTCOMES = 6

#: The helpers allowed to stand between a value and ``print``. Both put the
#: value through ``redact()`` - one IS the redactor, the other renders an
#: OSError's reason through it - so a print sweep that cleared neither would
#: have nothing left to clear and would be asserting about nothing.
REDACTING_CALLS = frozenset({"redact", "_failure_detail"})

#: The interpolations the print sweep clears WITHOUT a redactor standing in
#: front of them. Both are integers rather than strings: a subprocess return
#: code, and a timeout this module declares as a literal. Neither can carry a
#: path or a name, and neither is reachable from anything the operator typed.
#:
#: THIS IS AN EXEMPTION LIST, WHICH IS THE PART THAT ROTS. Two things stop it.
#: It is matched against the UNPARSED SOURCE of the interpolated expression, so
#: it exempts those two spellings and nothing that merely resembles them - a
#: ``done.returncode`` swapped for ``done.stderr`` is not covered by the entry
#: that covered the first. And every entry is asserted still present in the
#: script, so an exemption left behind by a deleted print reddens instead of
#: sitting there granting cover to whatever is written next.
PRINT_INTERPOLATION_EXEMPT = frozenset(
    {
        "POWERSHELL_TIMEOUT_SECONDS",
        "done.returncode",
    }
)

#: How long one subprocess arm may take. Every one of them either refuses
#: immediately or drives a stub that returns at once; this is a ceiling, not a
#: budget. An unbounded wait in a test is the same failure class as an unbounded
#: external probe in a tool.
SUBPROCESS_TIMEOUT_SECONDS = 120

#: What the stub PowerShell exits when it is told to fail. Chosen OUTSIDE every
#: code the script declares, so a probe reporting this number means the stub's
#: own status was passed through rather than translated - visible instead of
#: plausible.
STUB_POWERSHELL_EXIT = 37

#: What the stub exits when it cannot find the staging directory it was told to
#: write into. Also outside the script's table, for the same reason.
STUB_CONFUSED_EXIT = 41

STUB_MODE_ENV = "CLOCKSPEED_STUB_MODE"
STUB_DEST_ENV = "CLOCKSPEED_STUB_DEST"
STUB_NAME_ENV = "CLOCKSPEED_STUB_NAME"
STUB_PREFIX_ENV = "CLOCKSPEED_STUB_PREFIX"
STUB_EXIT_ENV = "CLOCKSPEED_STUB_EXIT"

#: The stub creates the shortcut it was asked for.
STUB_CREATE = "create"
#: The stub fails the way a real PowerShell fails - non-zero, nothing written.
STUB_FAIL = "fail"
#: The stub exits 0 and writes nothing, which is the case a caller cannot tell
#: from success by status alone. The script has to catch it.
STUB_SILENT = "silent"

#: The stub PowerShell's worker, written into tmp_path at test time.
#:
#: IT DISCOVERS THE STAGED FILE RATHER THAN PARSING ITS ARGUMENTS, and that is a
#: deliberate limit on what the live half claims. Forwarding a PowerShell
#: ``-Command`` string through a Windows ``.cmd`` launcher is a quoting problem
#: this suite has no reason to take on, and an arm whose subject is cmd.exe's
#: argument parsing is not an arm about this script. So the worker is told the
#: destination, the file name and the staging prefix through the environment,
#: and the CONTENT of the rendered command is graded by the pure half instead -
#: element by element, where nothing can mangle it.
#:
#: NO BACKSLASH APPEARS IN THIS SOURCE. It is written through a harness that has
#: been measured collapsing escapes inside a heredoc, and a stub that silently
#: lost one would report a confusing failure rather than an obvious one.
STUB_WORKER = '''
"""A PowerShell stand-in. Writes the staged shortcut, fails, or does neither."""

import os
import sys
from pathlib import Path

mode = os.environ.get("CLOCKSPEED_STUB_MODE", "create")
if mode == "fail":
    raise SystemExit(int(os.environ["CLOCKSPEED_STUB_EXIT"]))
if mode == "create":
    destination = Path(os.environ["CLOCKSPEED_STUB_DEST"])
    name = os.environ["CLOCKSPEED_STUB_NAME"]
    prefix = os.environ["CLOCKSPEED_STUB_PREFIX"]
    staging = sorted(
        item for item in destination.iterdir() if item.is_dir() and item.name.startswith(prefix)
    )
    if not staging:
        sys.stderr.write("stub found no staging directory")
        raise SystemExit(41)
    (staging[0] / name).write_bytes(b"stub shortcut")
raise SystemExit(0)
'''


def _load_script(source: Path, bound_name: str) -> ModuleType:
    """Load an entry-point script from ``scripts/`` by path.

    scripts/ is a directory of entry-point scripts rather than an importable
    package, so the module is loaded from its file - the same way
    tests/test_make_cert.py loads make_cert.py. The bound name is distinct from
    the one that module uses, so two loaders cannot collide inside a single
    pytest session.

    Args:
        source: The script file.
        bound_name: The key to bind it under in sys.modules.

    Returns:
        The loaded module.

    Raises:
        ImportError: The script is not loadable from this checkout.
    """
    spec = importlib.util.spec_from_file_location(bound_name, source)
    if spec is None or spec.loader is None:
        message = f"could not load {source.name}"
        raise ImportError(message)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


make_shortcut = _load_script(MAKE_SHORTCUT_SOURCE, "clockspeed_make_shortcut")


# ---------------------------------------------------------------------------
# Fixtures the live half is built out of
# ---------------------------------------------------------------------------


def _fake_shell(root: Path) -> Path:
    """Build a shell directory holding an Electron runtime that is not one.

    THE BINARY IS NAMED ``electron.exe`` ON EVERY PLATFORM, because the script
    writes a WINDOWS shortcut and the Windows runtime is what it must point at.
    On a Linux runner this file is a placeholder whose only job is to exist, and
    the arms that use it grade the presence check rather than the binary.

    Args:
        root: A tmp_path. The shell directory is created beneath it.

    Returns:
        The shell directory, ready for CLOCKSPEED_SHELL_DIR.
    """
    # ANNOTATED, NOT INFERRED. ``make_shortcut`` is loaded from a path rather
    # than imported, so every attribute read off it is ``Any`` and the derived
    # path would be too - which mypy reports at the return.
    shell: Path = root / make_shortcut.SHELL_DIRNAME
    distribution = shell / Path(*make_shortcut.ELECTRON_RELATIVE[:-1])
    distribution.mkdir(parents=True)
    (distribution / make_shortcut.ELECTRON_RELATIVE[-1]).write_bytes(b"not really electron")
    return shell


def _powershell_stub(directory: Path) -> Path:
    """Put a PowerShell on PATH that is real, findable, and fully controlled.

    Two files, because a Python worker is the only stand-in that can create a
    file portably while a shell builtin cannot. The launcher is what
    ``shutil.which`` finds - on Windows that means a name PATHEXT covers.

    Args:
        directory: Where both files go. This directory is what belongs on PATH.

    Returns:
        The launcher. Its parent is the PATH entry.
    """
    worker = directory / "stub_powershell.py"
    worker.write_text(STUB_WORKER, encoding="utf-8")
    if os.name == "nt":
        launcher = directory / "powershell.cmd"
        launcher.write_text(
            f'@echo off\r\n"{sys.executable}" "{worker}"\r\n',
            encoding="utf-8",
            newline="",
        )
    else:
        launcher = directory / "powershell"
        launcher.write_text(
            f'#!/bin/sh\nexec "{sys.executable}" "{worker}"\n',
            encoding="utf-8",
            newline="",
        )
        launcher.chmod(0o755)
    return launcher


def _run_script(
    args: list[str],
    *,
    path_dir: Path,
    overrides: dict[str, str],
) -> subprocess.CompletedProcess[bytes]:
    """Run the real entry point as a subprocess, with a PATH this suite owns.

    A SUBPROCESS RATHER THAN A CALL, for the one property no in-process arm can
    observe: what the default excepthook renders. A traceback escaping the
    script would print the exception's own path fields, where no redaction runs
    - and stderr is where that would land.

    Args:
        args: Command line arguments after the script name.
        path_dir: The only directory on PATH. An empty one means "no tool".
        overrides: Environment entries to set for this run.

    Returns:
        The completed process, streams captured as bytes.
    """
    environment = dict(os.environ)
    environment.pop(make_shortcut.ENV_DESKTOP_DIR, None)
    environment.pop(make_shortcut.ENV_SHELL_DIR, None)
    environment["PATH"] = str(path_dir)
    environment.update(overrides)
    return subprocess.run(
        [sys.executable, str(MAKE_SHORTCUT_SOURCE), *args],
        shell=False,
        capture_output=True,
        timeout=SUBPROCESS_TIMEOUT_SECONDS,
        check=False,
        env=environment,
    )


def _streams(done: subprocess.CompletedProcess[bytes]) -> str:
    """Render both captured streams as one string.

    Args:
        done: A completed subprocess.

    Returns:
        stdout followed by stderr, decoded permissively so a byte this suite
        did not write cannot turn an assertion into a decode error.
    """
    out = done.stdout.decode("utf-8", errors="replace")
    err = done.stderr.decode("utf-8", errors="replace")
    return out + err


def _redacting_call(node: ast.expr) -> bool:
    """Say whether an expression is a call to something that redacts.

    Args:
        node: The expression interpolated into a message, or handed to print.

    Returns:
        True when its outermost call is one of :data:`REDACTING_CALLS`.
    """
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in REDACTING_CALLS
    )


def _printed_expressions() -> list[tuple[str, bool]]:
    """Read every value the script interpolates into a message, out of its AST.

    ENUMERATED RATHER THAN REMEMBERED, and that is the whole point of reading
    the AST for this. A privacy arm built from a hand-written list of call
    sites grades the sites whoever wrote it thought of, and a print added
    afterwards is covered by nothing - which is how a message that rendered the
    operator's ``--name`` in clear sat two hundred lines from one that redacted
    the same value. A sweep over the parse tree has no such list to fall behind.

    A print argument is read one of three ways. A string constant is fixed text
    and carries nothing. An f-string is opened and each interpolated expression
    is graded on its own. Anything else - a bare name, a call, an attribute -
    is graded whole, which is what covers ``print(_failure_detail(exc))``
    without special-casing it.

    Returns:
        One row per interpolated expression: its unparsed source, and whether a
        redactor stands in front of it.
    """
    tree = ast.parse(MAKE_SHORTCUT_SOURCE.read_text(encoding="utf-8"))
    calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "print"
    ]

    rows: list[tuple[str, bool]] = []
    for call in calls:
        for argument in call.args:
            if isinstance(argument, ast.Constant):
                continue
            if isinstance(argument, ast.JoinedStr):
                rows.extend(
                    (ast.unparse(piece.value), _redacting_call(piece.value))
                    for piece in ast.walk(argument)
                    if isinstance(piece, ast.FormattedValue)
                )
                continue
            rows.append((ast.unparse(argument), _redacting_call(argument)))
    return rows


def _digest(path: Path) -> str:
    """Hash a file, so an arm can assert it did not change without naming it.

    Args:
        path: The file to hash.

    Returns:
        Its sha256 hex digest.
    """
    return hashlib.sha256(path.read_bytes()).hexdigest()


# ---------------------------------------------------------------------------
# The pure half - the target, the rendered script, the argv
# ---------------------------------------------------------------------------


def test_the_target_is_the_electron_binary_under_the_shell_directory() -> None:
    """The shortcut points at the GUI binary itself, not at a launcher.

    A ``.cmd`` or ``.vbs`` wrapper flashes a console on the way past, which is
    the whole reason this script exists rather than a two-line batch file.
    """
    target = make_shortcut.electron_path(SHELL_STUB)

    assert target.suffix == ".exe"
    assert target.parts[0] == SHELL_STUB.name
    assert target.parts[1:] == make_shortcut.ELECTRON_RELATIVE


def test_the_working_directory_is_the_shell_directory_and_the_argument_is_local() -> None:
    """Electron loads ``shell/package.json``'s main only from that directory.

    ``electron.exe .`` with the working directory anywhere else resolves the
    dot against the wrong tree and the window never opens.
    """
    assert make_shortcut.SHORTCUT_ARGUMENTS == "."
    assert make_shortcut.SHELL_DIRNAME == "shell"


def test_no_absolute_path_literal_is_spelled_into_the_script() -> None:
    """CLAUDE.md non-negotiable 3, asserted against the source rather than hoped.

    An absolute path in a tracked file carries the Windows account name, the
    drive layout, or both. Every path this script uses is derived from its own
    location or supplied at runtime.
    """
    source = MAKE_SHORTCUT_SOURCE.read_text(encoding="utf-8")
    absolute = re.compile(r"[A-Za-z]:[\\/]|/(?:Users|home)/")
    found = sorted({match.group(0) for match in absolute.finditer(source)})

    assert found == [], f"{len(found)} absolute path literal(s) in the source: {found}"
    assert "__file__" in source, "the repository root is not derived from this file's location"


def test_powershell_is_never_invoked_through_a_shell() -> None:
    """MEASURED TRAP, inherited from scripts/make_cert.py and pinned here too.

    Through Git Bash, MSYS path conversion rewrites arguments before the tool
    sees them. The argv form with ``shell=False`` is immune, so every subprocess
    call in the script must say so EXPLICITLY - a call relying on the default is
    one refactor away from someone adding ``shell=True`` to fix a quoting
    problem.
    """
    tree = ast.parse(MAKE_SHORTCUT_SOURCE.read_text(encoding="utf-8"))
    runs = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "run"
    ]
    explicitly_shell_free = [
        node
        for node in runs
        if any(
            keyword.arg == "shell"
            and isinstance(keyword.value, ast.Constant)
            and keyword.value.value is False
            for keyword in node.keywords
        )
    ]

    run_count = len(runs)
    shell_free_count = len(explicitly_shell_free)
    assert run_count >= 1, "no subprocess run call found; this test is asserting about nothing"
    assert shell_free_count == run_count, (
        f"{run_count - shell_free_count} of {run_count} subprocess run calls do not pass "
        "shell=False explicitly"
    )


def test_the_word_shell_true_appears_nowhere_in_the_script() -> None:
    """The AST arm above sees a call; this sees a spelling.

    Neither subsumes the other. A ``shell=True`` inside a string, a comment or a
    keyword this file's AST filter does not model would be invisible above and
    is visible here.
    """
    source = MAKE_SHORTCUT_SOURCE.read_text(encoding="utf-8")
    collapsed = re.sub(r"\s+", "", source)

    assert "shell=True" not in collapsed


def test_the_powershell_call_is_bounded_by_a_timeout() -> None:
    """An external probe that never returns is an open failure class here."""
    tree = ast.parse(MAKE_SHORTCUT_SOURCE.read_text(encoding="utf-8"))
    runs = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "run"
    ]
    bounded = [
        node
        for node in runs
        if any(
            keyword.arg == "timeout"
            and not (isinstance(keyword.value, ast.Constant) and keyword.value.value is None)
            for keyword in node.keywords
        )
    ]

    run_count = len(runs)
    bounded_count = len(bounded)
    assert run_count >= 1, "no subprocess run call found; this test is asserting about nothing"
    assert bounded_count == run_count, (
        f"{run_count - bounded_count} of {run_count} subprocess run calls are unbounded"
    )
    assert make_shortcut.POWERSHELL_TIMEOUT_SECONDS > 0


def test_the_rendered_script_creates_the_shortcut_it_was_told_to() -> None:
    """The COM object, the three fields, and the save - in that order."""
    rendered = make_shortcut.shortcut_script(LINK_STUB, SHELL_STUB / "e.exe", SHELL_STUB)

    assert "WScript.Shell" in rendered
    assert "CreateShortcut" in rendered
    assert ".Save()" in rendered
    assert rendered.index("CreateShortcut") < rendered.index(".Save()")


@pytest.mark.parametrize(
    "field",
    ["TargetPath", "Arguments", "WorkingDirectory", "Description"],
)
def test_the_rendered_script_sets_the_field(field: str) -> None:
    """Every field the shortcut needs is assigned, named one per arm."""
    rendered = make_shortcut.shortcut_script(LINK_STUB, SHELL_STUB / "e.exe", SHELL_STUB)

    assert f".{field} = " in rendered


def test_the_rendered_script_stops_on_the_first_error() -> None:
    """Without this, a failed assignment leaves PowerShell exiting 0.

    ``$link.Save()`` on a half-built object can succeed, and the script would
    then report a shortcut it did not really write.
    """
    rendered = make_shortcut.shortcut_script(LINK_STUB, SHELL_STUB / "e.exe", SHELL_STUB)

    assert "$ErrorActionPreference = 'Stop'" in rendered


@pytest.mark.parametrize("wrapper", [".cmd", ".bat", ".vbs", ".ps1", "cmd.exe"])
def test_the_rendered_script_names_no_interpreter_wrapper(wrapper: str) -> None:
    """The console flash this script exists to avoid comes from exactly these.

    A shortcut pointed at any of them opens a console host first and the
    operator sees a black rectangle before the window appears.
    """
    rendered = make_shortcut.shortcut_script(LINK_STUB, SHELL_STUB / "e.exe", SHELL_STUB)

    assert wrapper not in rendered.lower()


def test_a_single_quote_in_a_path_is_doubled_rather_than_ending_the_string() -> None:
    """A PowerShell single-quoted string ends at the first unescaped quote.

    Doubling is the ONLY escape a single-quoted string has, and nothing else in
    one is special - no expansion, no backtick. That is why the rendered script
    uses single quotes throughout: it takes the whole quoting problem off the
    table, and it leaves no double quote for Windows argv joining to escape.
    """
    quoted = make_shortcut.ps_quote("O'Brien")

    assert quoted == "'O''Brien'"
    assert quoted.count("'") % 2 == 0


def test_the_rendered_script_carries_no_double_quote() -> None:
    """Windows joins a list argv by quoting; a double quote here would nest.

    ``subprocess.list2cmdline`` wraps an argument containing spaces in double
    quotes and escapes any double quote inside it. A rendered script free of
    them cannot be mangled by that step.
    """
    rendered = make_shortcut.shortcut_script(LINK_STUB, SHELL_STUB / "e.exe", SHELL_STUB)

    assert '"' not in rendered


def test_the_argv_names_powershell_by_name_and_never_by_absolute_path() -> None:
    """argv[0] is resolved from PATH by the caller, never hardcoded."""
    argv = make_shortcut.shortcut_argv(LINK_STUB, SHELL_STUB / "e.exe", SHELL_STUB)

    assert argv[0] == make_shortcut.POWERSHELL_NAMES[0]
    assert not Path(argv[0]).is_absolute()


@pytest.mark.parametrize("flag", ["-NoProfile", "-NonInteractive", "-Command"])
def test_the_argv_carries_the_flag(flag: str) -> None:
    """A profile can print, prompt or fail; a prompt would hang the run."""
    argv = make_shortcut.shortcut_argv(LINK_STUB, SHELL_STUB / "e.exe", SHELL_STUB)

    assert flag in argv


def test_the_command_text_is_the_last_argv_element() -> None:
    """PowerShell reads everything after -Command as the command."""
    argv = make_shortcut.shortcut_argv(LINK_STUB, SHELL_STUB / "e.exe", SHELL_STUB)

    assert argv[-2] == "-Command"
    assert argv[-1] == make_shortcut.shortcut_script(LINK_STUB, SHELL_STUB / "e.exe", SHELL_STUB)


def test_the_argv_writes_the_shortcut_where_it_was_told() -> None:
    """The three paths the caller supplied all reach the rendered command."""
    argv = make_shortcut.shortcut_argv(LINK_STUB, SHELL_STUB / "e.exe", SHELL_STUB)
    command = argv[-1]

    assert make_shortcut.ps_quote(str(LINK_STUB)) in command
    assert make_shortcut.ps_quote(str(SHELL_STUB / "e.exe")) in command
    assert make_shortcut.ps_quote(str(SHELL_STUB)) in command


# ---------------------------------------------------------------------------
# The exit codes - the population derived from the module, the values pinned
# ---------------------------------------------------------------------------

#: The prefix every exit-code constant carries. The population is FILTERED OUT
#: OF THE MODULE rather than typed out here, so a constant added tomorrow is
#: graded without this file being edited.
EXIT_PREFIX = "EXIT_"

#: One row of the module docstring's exit-code table: four spaces, the number,
#: two spaces, then the meaning. Parsed rather than trusted, so a constant added
#: without its docstring row - or a row left behind by a deleted constant -
#: reddens instead of drifting.
DOCUMENTED_CODE_ROW = re.compile(r"^ {4}(\d+) {2}\S")


def _declared_exit_codes() -> dict[str, int]:
    """Read every exit code the script declares, out of the script itself.

    Returns:
        Constant name to value, for every module-level ``EXIT_*`` integer.
    """
    return {
        name: value
        for name, value in vars(make_shortcut).items()
        if name.startswith(EXIT_PREFIX) and isinstance(value, int)
    }


def _documented_exit_codes() -> list[int]:
    """Read every exit code the script's own module docstring lists.

    A SECOND READING OF THE SAME FACT, deliberately not a copy of the first. The
    constants say what the code can return; the table is what a reader branches
    on. Both are the module's own declarations, so neither is a hand-written
    list.

    Returns:
        The codes the table carries, in the order it carries them.
    """
    docstring = make_shortcut.__doc__ or ""
    return [
        int(match.group(1))
        for match in (DOCUMENTED_CODE_ROW.match(line) for line in docstring.splitlines())
        if match is not None
    ]


def test_every_exit_code_constant_is_distinct() -> None:
    """Two outcomes sharing a code is a runbook that cannot branch.

    scripts/make_cert.py carries ONE recorded collision by operator ruling - a
    successful ``--help`` exits 0 there because POSIX says so. This script keeps
    the convention WITHOUT the collision: ``--help`` routes through ``EXIT_OK``
    itself rather than through a second constant naming the same value, so the
    universal below holds with no exemption to record.
    """
    declared = _declared_exit_codes()
    seen: dict[int, list[str]] = {}
    for name, value in declared.items():
        seen.setdefault(value, []).append(name)
    shared = sorted(f"{value}: {sorted(names)}" for value, names in seen.items() if len(names) > 1)

    declared_count = len(declared)
    assert declared_count > 1, "fewer than two exit codes declared; this arm grades nothing"
    assert shared == [], f"{len(shared)} exit code(s) declared by more than one constant: {shared}"


def test_the_documented_table_and_the_constants_name_the_same_codes() -> None:
    """A table that has drifted from the constants is a lie with a date on it."""
    declared = sorted(set(_declared_exit_codes().values()))
    documented = _documented_exit_codes()

    documented_count = len(documented)
    assert documented_count > 1, "the module docstring carries no exit-code table"
    assert sorted(set(documented)) == declared, (
        "the exit-code constants and the module docstring's table do not name the same codes. "
        f"Documented: {sorted(set(documented))}. Declared: {declared}"
    )
    assert documented_count == len(declared), (
        f"{documented_count} documented row(s) against {len(declared)} constant(s); "
        "one outcome is undocumented or one row is stale"
    )


def test_success_is_zero_and_every_refusal_is_not() -> None:
    """The direction of the table, pinned separately from its distinctness."""
    declared = _declared_exit_codes()
    non_zero = sorted(name for name, value in declared.items() if value == 0)

    assert make_shortcut.EXIT_OK == 0
    assert non_zero == ["EXIT_OK"], f"more than the success outcome exits 0: {non_zero}"


# ---------------------------------------------------------------------------
# The name - the one place an operator string reaches the filesystem
# ---------------------------------------------------------------------------


def test_the_default_name_gains_the_lnk_suffix() -> None:
    """WScript.Shell refuses any destination that is not a .lnk or a .url."""
    assert make_shortcut.shortcut_file_name(None) == (
        make_shortcut.DEFAULT_SHORTCUT_NAME + make_shortcut.SHORTCUT_SUFFIX
    )


def test_a_name_that_already_carries_the_suffix_does_not_gain_a_second() -> None:
    """Otherwise the operator gets Clockspeed.lnk.lnk."""
    assert make_shortcut.shortcut_file_name("Clockspeed.lnk") == "Clockspeed.lnk"


@pytest.mark.parametrize(
    "bad",
    ["", "   ", "a/b", "a\\b", "..", ".", "../escape", "C:name"],
)
def test_a_name_that_is_not_a_bare_file_name_is_refused(bad: str) -> None:
    """A separator in --name writes the shortcut outside the destination.

    That is a path traversal wearing a convenience flag, and it is refused
    before anything is created rather than sanitised into something else.
    """
    with pytest.raises(ValueError, match="bare file name"):
        make_shortcut.shortcut_file_name(bad)


def test_the_refusal_message_for_a_bad_name_does_not_echo_the_name() -> None:
    """The name is operator input and could carry anything, including a path."""
    with pytest.raises(ValueError) as caught:  # noqa: PT011 - the message IS the subject
        make_shortcut.shortcut_file_name(f"{CANARY_ACCOUNT}/x")

    rendered = str(caught.value)
    assert CANARY_ACCOUNT not in rendered


# ---------------------------------------------------------------------------
# The live half - the real entry point against a stub PowerShell
# ---------------------------------------------------------------------------


def test_an_absent_electron_runtime_is_refused_with_its_own_code(tmp_path: Path) -> None:
    """A shortcut whose target does not exist is a broken icon and no diagnosis.

    ``npm install`` alone does NOT produce this binary for the pinned Electron
    44 - that package ships no postinstall script at all and fetches the runtime
    lazily on the first ``require("electron")`` - so an operator hitting this is
    hitting the common case, not an exotic one.
    """
    empty_shell = tmp_path / "shell"
    empty_shell.mkdir()
    desktop = tmp_path / "desk"
    desktop.mkdir()

    done = _run_script(
        ["--desktop-dir", str(desktop)],
        path_dir=tmp_path / "no-tools",
        overrides={make_shortcut.ENV_SHELL_DIR: str(empty_shell)},
    )

    created = sorted(desktop.iterdir())
    assert done.returncode == make_shortcut.EXIT_NO_ELECTRON
    assert created == [], f"{len(created)} file(s) were written despite the refusal"


def test_an_absent_destination_directory_is_refused_rather_than_created(tmp_path: Path) -> None:
    """Creating a mistyped --desktop-dir hides the typo behind a working run."""
    shell = _fake_shell(tmp_path)
    missing = tmp_path / "desk" / "not-there"

    done = _run_script(
        ["--desktop-dir", str(missing)],
        path_dir=tmp_path / "no-tools",
        overrides={make_shortcut.ENV_SHELL_DIR: str(shell)},
    )

    assert done.returncode == make_shortcut.EXIT_NO_DESKTOP
    assert not missing.exists(), "the destination was created by a run that refused"


def test_an_absent_powershell_is_refused_with_its_own_code(tmp_path: Path) -> None:
    """The absent tool is an empty PATH rather than a patched ``which``."""
    shell = _fake_shell(tmp_path)
    desktop = tmp_path / "desk"
    desktop.mkdir()
    empty = tmp_path / "no-tools"
    empty.mkdir()

    done = _run_script(
        ["--desktop-dir", str(desktop)],
        path_dir=empty,
        overrides={make_shortcut.ENV_SHELL_DIR: str(shell)},
    )

    created = sorted(desktop.iterdir())
    assert done.returncode == make_shortcut.EXIT_NO_POWERSHELL
    assert created == [], f"{len(created)} file(s) were written despite the refusal"


def _live_overrides(shell: Path, desktop: Path, mode: str) -> dict[str, str]:
    """Assemble the environment one live arm runs under.

    Args:
        shell: The fake shell directory.
        desktop: The destination the stub will write into.
        mode: One of the STUB_* modes.

    Returns:
        The environment overrides for :func:`_run_script`.
    """
    return {
        make_shortcut.ENV_SHELL_DIR: str(shell),
        STUB_MODE_ENV: mode,
        STUB_DEST_ENV: str(desktop),
        STUB_NAME_ENV: make_shortcut.shortcut_file_name(None),
        STUB_PREFIX_ENV: make_shortcut.STAGING_PREFIX,
        STUB_EXIT_ENV: str(STUB_POWERSHELL_EXIT),
    }


def test_a_first_run_writes_the_shortcut(tmp_path: Path) -> None:
    """End to end against the stub: staging, the rename, and the exists check."""
    shell = _fake_shell(tmp_path)
    desktop = tmp_path / "desk"
    desktop.mkdir()
    tools = tmp_path / "tools"
    tools.mkdir()
    _powershell_stub(tools)

    done = _run_script(
        ["--desktop-dir", str(desktop)],
        path_dir=tools,
        overrides=_live_overrides(shell, desktop, STUB_CREATE),
    )

    link = desktop / make_shortcut.shortcut_file_name(None)
    leftovers = sorted(item.name for item in desktop.iterdir() if item.is_dir())
    assert done.returncode == make_shortcut.EXIT_OK, _streams(done)
    assert link.is_file()
    assert leftovers == [], f"{len(leftovers)} staging directory(ies) left behind: {leftovers}"


def test_a_second_run_without_force_refuses_and_leaves_the_file_untouched(tmp_path: Path) -> None:
    """The operator may already have pinned this shortcut somewhere."""
    shell = _fake_shell(tmp_path)
    desktop = tmp_path / "desk"
    desktop.mkdir()
    tools = tmp_path / "tools"
    tools.mkdir()
    _powershell_stub(tools)
    link = desktop / make_shortcut.shortcut_file_name(None)
    link.write_bytes(b"the shortcut the operator already has")
    before = _digest(link)

    done = _run_script(
        ["--desktop-dir", str(desktop)],
        path_dir=tools,
        overrides=_live_overrides(shell, desktop, STUB_CREATE),
    )

    assert done.returncode == make_shortcut.EXIT_REFUSED
    assert _digest(link) == before, "the refused run changed the file it refused to replace"


def test_force_replaces_the_existing_shortcut(tmp_path: Path) -> None:
    """The flag that lifts the refusal, graded by the file actually changing."""
    shell = _fake_shell(tmp_path)
    desktop = tmp_path / "desk"
    desktop.mkdir()
    tools = tmp_path / "tools"
    tools.mkdir()
    _powershell_stub(tools)
    link = desktop / make_shortcut.shortcut_file_name(None)
    link.write_bytes(b"the shortcut the operator already has")
    before = _digest(link)

    done = _run_script(
        ["--desktop-dir", str(desktop), "--force"],
        path_dir=tools,
        overrides=_live_overrides(shell, desktop, STUB_CREATE),
    )

    assert done.returncode == make_shortcut.EXIT_OK, _streams(done)
    assert _digest(link) != before, "--force reported success but the file did not change"


def test_a_powershell_that_fails_leaves_the_previous_shortcut_intact(tmp_path: Path) -> None:
    """Staging is what buys this: a failed --force destroys nothing."""
    shell = _fake_shell(tmp_path)
    desktop = tmp_path / "desk"
    desktop.mkdir()
    tools = tmp_path / "tools"
    tools.mkdir()
    _powershell_stub(tools)
    link = desktop / make_shortcut.shortcut_file_name(None)
    link.write_bytes(b"the shortcut the operator already has")
    before = _digest(link)

    done = _run_script(
        ["--desktop-dir", str(desktop), "--force"],
        path_dir=tools,
        overrides=_live_overrides(shell, desktop, STUB_FAIL),
    )

    leftovers = sorted(item.name for item in desktop.iterdir() if item.is_dir())
    assert done.returncode == make_shortcut.EXIT_POWERSHELL_FAILED
    assert _digest(link) == before, "a failed run replaced the pair it was meant to leave alone"
    assert leftovers == [], f"{len(leftovers)} staging directory(ies) left behind: {leftovers}"


def test_the_stub_status_is_translated_and_never_passed_through(tmp_path: Path) -> None:
    """A tool's own exit code leaking out makes the table meaningless."""
    shell = _fake_shell(tmp_path)
    desktop = tmp_path / "desk"
    desktop.mkdir()
    tools = tmp_path / "tools"
    tools.mkdir()
    _powershell_stub(tools)

    done = _run_script(
        ["--desktop-dir", str(desktop)],
        path_dir=tools,
        overrides=_live_overrides(shell, desktop, STUB_FAIL),
    )

    assert done.returncode != STUB_POWERSHELL_EXIT
    assert done.returncode != STUB_CONFUSED_EXIT


def test_a_powershell_that_reports_success_but_writes_nothing_is_a_failure(tmp_path: Path) -> None:
    """Status alone cannot tell a written shortcut from an unwritten one."""
    shell = _fake_shell(tmp_path)
    desktop = tmp_path / "desk"
    desktop.mkdir()
    tools = tmp_path / "tools"
    tools.mkdir()
    _powershell_stub(tools)

    done = _run_script(
        ["--desktop-dir", str(desktop)],
        path_dir=tools,
        overrides=_live_overrides(shell, desktop, STUB_SILENT),
    )

    created = sorted(desktop.iterdir())
    assert done.returncode == make_shortcut.EXIT_POWERSHELL_FAILED
    assert created == [], f"{len(created)} file(s) present after a run that wrote nothing"


def test_help_exits_zero_and_creates_nothing(tmp_path: Path) -> None:
    """POSIX convention, and the one arm that needs no tool at all."""
    desktop = tmp_path / "desk"
    desktop.mkdir()
    empty = tmp_path / "no-tools"
    empty.mkdir()

    done = _run_script(["--help"], path_dir=empty, overrides={})

    created = sorted(desktop.iterdir())
    assert done.returncode == make_shortcut.EXIT_OK
    assert created == []
    assert b"--force" in done.stdout


def test_an_unknown_flag_exits_the_usage_code(tmp_path: Path) -> None:
    """Untouched, argparse exits 2 - and 2 means something else in this table."""
    empty = tmp_path / "no-tools"
    empty.mkdir()

    done = _run_script(["--clockspeed-not-a-real-flag"], path_dir=empty, overrides={})

    assert done.returncode == make_shortcut.EXIT_USAGE


def test_a_name_carrying_a_separator_exits_the_usage_code(tmp_path: Path) -> None:
    """The same outcome as a misspelled flag, and it is one row in the table."""
    shell = _fake_shell(tmp_path)
    desktop = tmp_path / "desk"
    desktop.mkdir()
    empty = tmp_path / "no-tools"
    empty.mkdir()

    done = _run_script(
        ["--desktop-dir", str(desktop), "--name", "sub/Clockspeed"],
        path_dir=empty,
        overrides={make_shortcut.ENV_SHELL_DIR: str(shell)},
    )

    created = sorted(desktop.iterdir())
    assert done.returncode == make_shortcut.EXIT_USAGE
    assert created == []


# ---------------------------------------------------------------------------
# Privacy - the planted canary, and the OSError that used to carry a path
# ---------------------------------------------------------------------------


def test_no_refusal_renders_a_planted_home_like_token(tmp_path: Path) -> None:
    """CLAUDE.md non-negotiable 3, driven through every refusal the CLI reaches.

    THE CONTROL COMES FIRST. ``redact()`` is shown to leave the planted token
    intact, so an absence measured afterwards is evidence the script never
    printed its destination - not evidence that the redactor happened to scrub
    a token it could not have known about. Without that control this arm would
    pass just as happily against a script that printed the path and a redactor
    that ate it.
    """
    canary_root = tmp_path / "Users" / CANARY_ACCOUNT
    desktop = canary_root / "Desktop"
    desktop.mkdir(parents=True)
    shell = _fake_shell(tmp_path)
    empty_shell = canary_root / "shell"
    empty_shell.mkdir()
    tools = tmp_path / "tools"
    tools.mkdir()
    _powershell_stub(tools)

    # The control. If redact() ate the token, every absence below would be
    # unfalsifiable.
    assert CANARY_ACCOUNT in make_shortcut.redact(str(desktop))

    link = desktop / make_shortcut.shortcut_file_name(None)
    probes: list[tuple[str, int, subprocess.CompletedProcess[bytes]]] = []

    probes.append(
        (
            "runtime absent",
            make_shortcut.EXIT_NO_ELECTRON,
            _run_script(
                ["--desktop-dir", str(desktop)],
                path_dir=tools,
                overrides={make_shortcut.ENV_SHELL_DIR: str(empty_shell)},
            ),
        )
    )
    probes.append(
        (
            "destination absent",
            make_shortcut.EXIT_NO_DESKTOP,
            _run_script(
                ["--desktop-dir", str(canary_root / "no-such-desktop")],
                path_dir=tools,
                overrides={make_shortcut.ENV_SHELL_DIR: str(shell)},
            ),
        )
    )
    probes.append(
        (
            "name not bare",
            make_shortcut.EXIT_USAGE,
            _run_script(
                ["--desktop-dir", str(desktop), "--name", f"{CANARY_ACCOUNT}/x"],
                path_dir=tools,
                overrides={make_shortcut.ENV_SHELL_DIR: str(shell)},
            ),
        )
    )
    probes.append(
        (
            "powershell absent",
            make_shortcut.EXIT_NO_POWERSHELL,
            _run_script(
                ["--desktop-dir", str(desktop)],
                path_dir=tmp_path / "no-tools",
                overrides={make_shortcut.ENV_SHELL_DIR: str(shell)},
            ),
        )
    )

    link.write_bytes(b"the shortcut the operator already has")
    probes.append(
        (
            "already there",
            make_shortcut.EXIT_REFUSED,
            _run_script(
                ["--desktop-dir", str(desktop)],
                path_dir=tools,
                overrides=_live_overrides(shell, desktop, STUB_CREATE),
            ),
        )
    )
    link.unlink()
    probes.append(
        (
            "powershell failed",
            make_shortcut.EXIT_POWERSHELL_FAILED,
            _run_script(
                ["--desktop-dir", str(desktop), "--force"],
                path_dir=tools,
                overrides=_live_overrides(shell, desktop, STUB_FAIL),
            ),
        )
    )

    leaked = sorted(label for label, _code, done in probes if CANARY_ACCOUNT in _streams(done))
    traced = sorted(label for label, _code, done in probes if "Traceback" in _streams(done))
    misrouted = sorted(
        f"{label} exited {done.returncode}, expected {code}"
        for label, code, done in probes
        if done.returncode != code
    )

    # A POOLED ABSENCE IS MET BY ITS STRONGEST MEMBER. Without this, six probes
    # that all fell into the SAME early refusal would satisfy every assertion
    # below while five of the six messages went unmeasured - the shape
    # memory/a-guard-can-be-green-by-accident.md records. THAT NAME WAS WRONG
    # WHEN THIS ARM WAS WRITTEN, and it survived because it sits in a COMMENT:
    # the bare-path rung of tests/test_docs_citations.py reads author prose in
    # docstrings, so the identical spelling one screen below was reported and
    # this one was not. The leaf it named has never existed in this repository.
    reached = sorted({done.returncode for _label, _code, done in probes})
    probe_count = len(probes)
    assert probe_count >= CANARY_REFUSALS, (
        "fewer refusals were probed than this arm claims to cover"
    )
    assert misrouted == [], f"{len(misrouted)} probe(s) reached the wrong refusal: {misrouted}"
    assert len(reached) == probe_count, (
        f"{probe_count} probes reached only {len(reached)} distinct outcome(s): {reached}"
    )
    assert leaked == [], f"{len(leaked)} refusal(s) rendered the planted account token: {leaked}"
    assert traced == [], f"{len(traced)} refusal(s) escaped as a traceback: {traced}"


def test_every_value_the_script_prints_passes_a_redactor_or_is_an_integer() -> None:
    """A SWEEP OVER EVERY PRINT, not over the ones someone remembered.

    The arm above drives refusals through a planted token, which grades the
    paths its probe list reaches. This grades the paths NOBODY LISTED: it reads
    every ``print`` out of the script's own parse tree and requires each value
    interpolated into one to have gone through a redactor, or to be an integer
    that cannot carry a string at all.

    THAT IS THE ARM THIS SCRIPT NEEDED AND DID NOT HAVE. Two messages rendered
    the same value - the file name derived from ``--name`` - and only one of
    them redacted it. Both were reachable, both were covered by arms, and
    neither arm was about the difference between them. A sweep is red the
    moment a new unredacted interpolation is written, whether or not anyone
    remembers to add a probe for the message carrying it.

    IT DEFAULTS TO REFUTED. An interpolation this arm cannot recognise is
    counted as unredacted rather than waved through, so extending the script
    with a message shaped differently costs an explicit exemption rather than
    silence.
    """
    rows = _printed_expressions()
    rendered = [source for source, _redacted in rows]
    unredacted = sorted(
        source
        for source, redacted in rows
        if not redacted and source not in PRINT_INTERPOLATION_EXEMPT
    )
    stale = sorted(PRINT_INTERPOLATION_EXEMPT - set(rendered))

    interpolation_count = len(rows)
    assert interpolation_count >= 1, (
        "no interpolated print value found; this arm is asserting about nothing"
    )
    assert unredacted == [], (
        f"{len(unredacted)} printed value(s) reach the operator without a redactor: {unredacted}"
    )
    assert stale == [], (
        f"{len(stale)} exemption(s) name an interpolation the script no longer has: {stale}"
    )


def test_no_message_renders_an_operator_supplied_name_the_redactor_would_claim(
    tmp_path: Path,
) -> None:
    """``--name`` is operator input, and every message rendering it must redact.

    THE CONTROL RUNS THE OPPOSITE WAY TO THE ONE ABOVE, and it has to. The
    planted-account arm shows ``redact()`` LEAVING its token alone, so an
    absence there means the script never printed a path. Here the redactor must
    be shown CLAIMING the token, because the question is not whether the value
    was printed - it is whether it went through the chokepoint on the way. A
    token ``redact()`` passed through would be present in the stream on both
    sides of the fix, and the arm would be unfalsifiable.

    THE OUTCOMES ARE ASSERTED DISTINCT for the reason
    ``memory/a-guard-can-be-green-by-accident.md`` records under "Why the pooled
    check could not catch it": six probes that all fell into the same early
    refusal would satisfy every absence below while five of the six messages
    went unmeasured.
    """
    desktop = tmp_path / "desk"
    desktop.mkdir()
    shell = _fake_shell(tmp_path)
    empty_shell = tmp_path / "no-shell"
    empty_shell.mkdir()
    tools = tmp_path / "tools"
    tools.mkdir()
    _powershell_stub(tools)

    # The control. A token the redactor did not claim would make every absence
    # below true of a script that printed it in clear.
    assert make_shortcut.redact(CANARY_ACCOUNT_ID) != CANARY_ACCOUNT_ID

    link_name = make_shortcut.shortcut_file_name(CANARY_ACCOUNT_ID)
    named = dict(_live_overrides(shell, desktop, STUB_CREATE))
    named[STUB_NAME_ENV] = link_name
    failing = dict(_live_overrides(shell, desktop, STUB_FAIL))
    failing[STUB_NAME_ENV] = link_name

    probes: list[tuple[str, int, subprocess.CompletedProcess[bytes]]] = []
    probes.append(
        (
            "runtime absent",
            make_shortcut.EXIT_NO_ELECTRON,
            _run_script(
                ["--desktop-dir", str(desktop), "--name", CANARY_ACCOUNT_ID],
                path_dir=tools,
                overrides={make_shortcut.ENV_SHELL_DIR: str(empty_shell)},
            ),
        )
    )
    probes.append(
        (
            "destination absent",
            make_shortcut.EXIT_NO_DESKTOP,
            _run_script(
                ["--desktop-dir", str(tmp_path / "no-such-desk"), "--name", CANARY_ACCOUNT_ID],
                path_dir=tools,
                overrides={make_shortcut.ENV_SHELL_DIR: str(shell)},
            ),
        )
    )
    probes.append(
        (
            "powershell absent",
            make_shortcut.EXIT_NO_POWERSHELL,
            _run_script(
                ["--desktop-dir", str(desktop), "--name", CANARY_ACCOUNT_ID],
                path_dir=tmp_path / "no-tools",
                overrides={make_shortcut.ENV_SHELL_DIR: str(shell)},
            ),
        )
    )
    probes.append(
        (
            "written",
            make_shortcut.EXIT_OK,
            _run_script(
                ["--desktop-dir", str(desktop), "--name", CANARY_ACCOUNT_ID],
                path_dir=tools,
                overrides=named,
            ),
        )
    )
    # THE SITE THIS ARM WAS WRITTEN FOR, and it is reached by leaving the
    # shortcut the probe above wrote exactly where it landed. A second run
    # without --force takes the refusal branch - the one message that rendered
    # the operator's name in clear while the success line redacted it.
    probes.append(
        (
            "already there",
            make_shortcut.EXIT_REFUSED,
            _run_script(
                ["--desktop-dir", str(desktop), "--name", CANARY_ACCOUNT_ID],
                path_dir=tools,
                overrides=named,
            ),
        )
    )
    probes.append(
        (
            "powershell failed",
            make_shortcut.EXIT_POWERSHELL_FAILED,
            _run_script(
                ["--desktop-dir", str(desktop), "--force", "--name", CANARY_ACCOUNT_ID],
                path_dir=tools,
                overrides=failing,
            ),
        )
    )

    leaked = sorted(label for label, _code, done in probes if CANARY_ACCOUNT_ID in _streams(done))
    traced = sorted(label for label, _code, done in probes if "Traceback" in _streams(done))
    misrouted = sorted(
        f"{label} exited {done.returncode}, expected {code}"
        for label, code, done in probes
        if done.returncode != code
    )
    reached = sorted({done.returncode for _label, _code, done in probes})

    probe_count = len(probes)
    assert probe_count >= CANARY_NAME_OUTCOMES, (
        "fewer outcomes were probed than this arm claims to cover"
    )
    assert misrouted == [], f"{len(misrouted)} probe(s) reached the wrong outcome: {misrouted}"
    assert len(reached) == probe_count, (
        f"{probe_count} probes reached only {len(reached)} distinct outcome(s): {reached}"
    )
    assert leaked == [], f"{len(leaked)} message(s) rendered the operator's name in clear: {leaked}"
    assert traced == [], f"{len(traced)} probe(s) escaped as a traceback: {traced}"


def test_a_staging_failure_renders_neither_the_planted_token_nor_a_filename(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """CS-878's shape, applied here: an OSError renders its filename fields.

    ``OSError.__str__`` appends ``filename`` and ``filename2`` verbatim, so a
    failure interpolated into a message - or allowed to escape to the default
    excepthook - puts the operator's Desktop path in front of a reader. The
    forced error below carries the planted token in exactly those fields.
    """
    canary_root = tmp_path / "Users" / CANARY_ACCOUNT
    desktop = canary_root / "Desktop"
    desktop.mkdir(parents=True)
    shell = _fake_shell(tmp_path)
    tools = tmp_path / "tools"
    tools.mkdir()
    _powershell_stub(tools)

    poisoned = OSError(errno.EACCES, "permission denied", str(desktop / "staging"))
    assert CANARY_ACCOUNT in str(poisoned), "the forced error does not carry the token to leak"

    def _refuse(*_args: object, **_kwargs: object) -> str:
        raise poisoned

    monkeypatch.setenv(make_shortcut.ENV_SHELL_DIR, str(shell))
    monkeypatch.setenv("PATH", str(tools))
    monkeypatch.setattr(make_shortcut.tempfile, "mkdtemp", _refuse)

    code = make_shortcut.main(["--desktop-dir", str(desktop)])

    captured = capsys.readouterr()
    rendered = captured.out + captured.err
    assert code == make_shortcut.EXIT_WRITE_FAILED
    assert CANARY_ACCOUNT not in rendered
    assert "staging" not in rendered


def test_a_pathless_cause_keeps_the_reason_and_drops_both_filenames() -> None:
    """The clone is the barrier for a caller this module does not have yet.

    The guard in ``_create`` grades what today's caller does with an OSError;
    this grades what tomorrow's second caller would be handed.
    """
    # Built field by field rather than through the positional form: the fourth
    # positional argument is ``winerror`` on Windows and ``filename2``
    # elsewhere, so a five-argument constructor call means different things on
    # the two platforms this suite runs on.
    original = OSError(errno.EACCES, "permission denied", "a-secret")
    original.filename2 = "another-secret"
    clone = make_shortcut.pathless_cause(original)

    rendered = str(clone)
    assert clone.errno == original.errno
    assert clone.strerror == original.strerror
    assert clone.filename is None
    assert clone.filename2 is None
    assert "a-secret" not in rendered
    assert "another-secret" not in rendered


def test_the_success_line_names_the_shortcut_and_never_its_directory(tmp_path: Path) -> None:
    """A successful run reports what it wrote without saying where it lives."""
    canary_root = tmp_path / "Users" / CANARY_ACCOUNT
    desktop = canary_root / "Desktop"
    desktop.mkdir(parents=True)
    shell = _fake_shell(tmp_path)
    tools = tmp_path / "tools"
    tools.mkdir()
    _powershell_stub(tools)

    done = _run_script(
        ["--desktop-dir", str(desktop)],
        path_dir=tools,
        overrides=_live_overrides(shell, desktop, STUB_CREATE),
    )

    rendered = _streams(done)
    assert done.returncode == make_shortcut.EXIT_OK, rendered
    assert CANARY_ACCOUNT not in rendered
    assert make_shortcut.shortcut_file_name(None) in rendered


# ---------------------------------------------------------------------------
# CS-910 - the interpreter this script spawns is resolved, never named
# ---------------------------------------------------------------------------

#: The environment variable Windows consults before searching the CURRENT
#: DIRECTORY for an executable. Set at NEITHER machine nor user scope on the
#: development machine, so anything Explorer launches has the search live - and
#: an Explorer-launched process is exactly what the shortcut this script writes
#: produces.
CURDIR_GATE = "NoDefaultCurrentDirectoryInExePath"


@pytest.mark.skipif(
    os.name != "nt",
    reason=(
        "the current-directory executable search is a Windows behaviour, and powershell"
        " is a Windows tool. There is nothing here for this arm to disarm elsewhere."
    ),
)
def test_a_powershell_planted_in_the_working_directory_is_never_resolved(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """CS-910 - the tool this script runs may not come from where it is standing.

    THE CONTROLS COME FIRST AND ARE PART OF THE ARM. A negative measurement is
    worth nothing without evidence the plant could have been seen: the shell this
    class was first probed under sets the gate variable for itself, and under it
    the shipped resolver looked correct while being wrong.

    PATH IS EMPTIED so the plant is the only candidate anywhere reachable, which
    makes "neither name is on PATH" the single correct answer.

    NOTHING BELOW ASSERTS ON A PATH. Every assertion binds a boolean, because
    pytest renders the asserted expression independently of the message and a
    temporary path on Windows carries the account name.
    """
    import _winapi  # noqa: PLC0415

    first = make_shortcut.POWERSHELL_NAMES[0]
    planted = tmp_path / f"{first}.exe"
    planted.write_bytes(b"MZ not a real executable, and it does not need to be\n")

    landed = planted.is_file() and planted.stat().st_size > 0
    assert landed, "the plant did not land, so this arm grades nothing"

    monkeypatch.chdir(tmp_path)
    for key in [name for name in os.environ if name.upper() == CURDIR_GATE.upper()]:
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("PATH", str(tmp_path / "no-tools"))

    gate_open = _winapi.NeedCurrentDirectoryForExePath(first)
    assert gate_open is True, (
        "the current-directory search is not live, so this arm cannot reproduce the"
        " defect it exists to grade"
    )

    import shutil  # noqa: PLC0415

    control = shutil.which(first)
    control_offered_the_plant = control is not None and not Path(control).is_absolute()
    assert control_offered_the_plant, (
        "a current-directory-consulting resolver did not offer the plant, so the control"
        " failed and the negative below would prove nothing"
    )

    resolved = make_shortcut._resolve_powershell()  # noqa: SLF001 - the site under test

    assert resolved is None, (
        "the powershell planted in the WORKING DIRECTORY was resolved - the interpreter"
        " this script spawns is chosen by where the process happens to be standing"
    )
