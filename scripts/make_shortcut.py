#!/usr/bin/env python3
"""Create the desktop shortcut that opens the Electron companion window.

WHAT THIS BUYS. The companion window is an Electron app, and the obvious ways
to launch it all flash a console. A terminal invocation leaves one open for the
lifetime of the window; a `.cmd` or `.bat` wrapper spawns a console host that
appears for a moment before the window does; a `.vbs` wrapper avoids the flash
by adding a scripting host nobody asked for. A `.lnk` pointed straight at
`electron.exe` has none of those problems, because `electron.exe` is a
GUI-subsystem image and Windows creates no console for one.

THAT SUBSYSTEM CLAIM IS MEASURED RATHER THAN ASSUMED. Read out of the pinned
Electron 44 binary's PE optional header on this machine: magic 0x20b (PE32+),
Subsystem 2, which is IMAGE_SUBSYSTEM_WINDOWS_GUI. Subsystem 3 would be the
console flavour. The rule suite does NOT assert this - the binary is gitignored
and absent on the tier 1 runner - so it is recorded here as a measurement with
a date on it rather than pinned as a test.

THE RUNTIME IS NOT PRESENT AFTER `npm install`, AND THAT IS THE COMMON CASE
rather than an exotic one. The pinned Electron 44 package ships NO scripts block
at all - so no postinstall - and fetches the platform binary lazily, from
`index.js`, on the first `require("electron")`. Measured today by reading that
package's own `package.json` and `index.js`: `getElectronPath` calls
`downloadElectron` when `dist/<path.txt>` is missing. An operator who has run
only `npm install` therefore has no `electron.exe`, and a shortcut written
anyway would be a broken icon with no diagnosis attached. This script refuses
instead, and names the remedy.

WHY THIS SHELLS OUT. Nothing in the Python standard library writes a `.lnk`,
and `pyproject.toml` declares `dependencies = []` and records that as a decision
(BOOTSTRAP.md section 11). Adding pywin32 to write one file is not a trade this
project makes, so PowerShell - present on every Windows install - drives the
`WScript.Shell` COM object that has written shortcuts since before this project
existed. Same shape as scripts/make_cert.py shelling out to openssl.

POWERSHELL IS NEVER INVOKED THROUGH A SHELL, AND THAT IS MEASURED RATHER THAN
STYLISTIC. Through Git Bash, MSYS path conversion rewrites arguments before the
tool sees them, which is the incident scripts/make_cert.py records against
openssl. Every call below passes a list argv with `shell=False`, which is
immune. A future reader hitting a quoting problem must not reach for a
shell-invoking form; tests/test_make_shortcut.py pins the absence of that
spelling twice, once against the parsed calls and once against the raw text.

THE RENDERED COMMAND USES SINGLE QUOTES THROUGHOUT, AND THAT IS LOAD-BEARING AT
TWO SEPARATE LAYERS. Inside a PowerShell single-quoted string NOTHING is
special except the quote itself, which is escaped by doubling - no variable
expansion, no backtick escape, and a Windows path's backslashes are literal.
And because the rendered text then contains no double quote, the Windows
argument joining that `subprocess` performs on the way to `CreateProcess` has
nothing to escape and cannot mangle it.

THE TOOL IS RESOLVED FROM PATH BY NAME. CLAUDE.md non-negotiable 3 forbids a
machine-specific absolute path in a tracked file. Two names are tried in order,
Windows PowerShell first and then PowerShell 7, because the COM object is
reachable from both and the first is present on every Windows install.

REFUSAL IS THE DEFAULT, and every refusal that is about the operator's REQUEST
is decided before any tool is resolved. A machine with no PowerShell still gets
told that its Electron runtime is missing, or that its destination does not
exist, rather than being told about PowerShell and left to discover the real
problem on the next run.

PRIVACY IS THE SHARP EDGE OF THIS SCRIPT, MORE THAN OF ANY OTHER IN scripts/.
The Desktop sits under the user profile, so its path CONTAINS THE WINDOWS
ACCOUNT NAME - personal data under CLAUDE.md non-negotiable 3. So:

  - NO MESSAGE EVER NAMES A DIRECTORY. Every refusal is fixed text naming a
    remedy, and the two messages that are not - the success line, and the
    refusal that says which shortcut it will not replace - name the shortcut
    FILE and never where it sits.
  - THE FILE NAME IS OPERATOR INPUT, SO BOTH OF THOSE REDACT IT. It comes from
    `--name`, which can carry whatever the operator typed, and redact() is this
    project's single verdict on whether a string is personal data. CS-909
    shipped with the success line putting that value through redact() and the
    already-there refusal printing the identical value in clear, two hundred
    lines apart. The repair was one call; what the repair is worth is the arm
    that came with it, which reads every print out of this module's own parse
    tree and requires each interpolated value to pass a redactor or be an
    integer. A hand-written list of message sites is what let the two drift in
    the first place, so the arm enumerates rather than remembers.
  - POWERSHELL'S OWN ERROR TEXT IS NEVER ECHOED, and this is where this script
    departs from scripts/make_cert.py deliberately. That script renders
    openssl's last stderr line through redact(), which is safe there because
    openssl's diagnostics do not carry the destination. PowerShell's DO - a
    failed `CreateShortcut` names the `.lnk` path it could not write - and
    redact() only knows the paths and account names it can discover on THIS
    machine. Pointed at any other directory, it would pass the path straight
    through. A tool's error text is not a channel this script can make safe, so
    it is not opened.
  - A RAISE IS AN ECHO PATH TOO, which is what CS-878 was against make_cert.
    `OSError.__str__` appends `filename` and `filename2` verbatim, so an
    OSError allowed to escape renders the destination through the default
    excepthook, where no print() runs and therefore no redaction does either.
    Two barriers close it here as well: `_create` lets no OSError out, and
    `pathless_cause` builds a path-free clone for anyone who catches one.

THE `.lnk` CARRIES MORE THAN THE FOUR PROPERTIES SET ABOVE, and that is
recorded here rather than left for someone to discover. `WScript.Shell` appends
a TrackerDataBlock of its own during `Save()`, and it carries the machine's
COMPUTERNAME together with a version-1 UUID whose node field is derived from a
network adapter's hardware address. Measured by parsing a shortcut this script
actually wrote, not inferred from the format documentation.

WHY THAT IS ACCEPTABLE HERE, stated as a boundary rather than as a shrug. The
rule this could offend is non-negotiable 3, and that rule is about what lands in
a TRACKED file. This artifact is written to the destination the operator asked
for - normally the Desktop, which is outside this repository - at the operator's
own request, and nothing in this project tracks a `.lnk`, reads one back, or
uploads one. The block therefore never crosses the boundary the rule draws.

IT IS ALSO NOT SOMETHING THIS SCRIPT CONTROLS. The block is written by the COM
object itself, is exposed as no settable property, and removing it would mean
emitting the `.lnk` binary format by hand - a far larger surface than the one it
would close, on an artifact that never leaves the machine. So it is left alone
deliberately, and the reasoning is written down so a later reader does not have
to re-derive it.

WHAT A FUTURE READER MUST THEREFORE NOT DO: treat a `.lnk` written by this
script as safe to attach to an issue, paste into a repository, or hand to
anyone. It is safe where it is written and nowhere else. This module's promise
covers what it PRINTS and what it RAISES; it does not, and cannot, cover the
contents of a file a COM object assembled.

ATOMIC, BECAUSE EXPLORER READS THE DESTINATION. Non-negotiable 5 requires an
atomic write for any file another process may read, and the Desktop is read
continuously by the shell. The shortcut is written into a staging directory
inside the destination and then renamed onto its final name, so no half-written
`.lnk` is ever visible and a failed `--force` run leaves the previous shortcut
exactly as it was. The staging directory is removed on every path.

Exit codes. ONE ROW PER OUTCOME, EVERY ROW DECLARED BY A CONSTANT BELOW, AND NO
TWO CONSTANTS SHARE A VALUE:

    0  the shortcut was written, or --help printed the usage
    1  the Electron runtime is not present
    2  no PowerShell was found on PATH
    3  the destination directory does not exist
    4  a shortcut of that name is already there and --force was not given
    5  PowerShell was found and failed, timed out, or wrote nothing
    6  the shortcut could not be written into the destination
    7  the command line could not be parsed

THE --help ROW SHARES 0 WITH SUCCESS AND DECLARES NO SECOND CONSTANT FOR IT.
scripts/make_cert.py carries an `EXIT_HELP` equal to `EXIT_OK`, because there
the alternative was a code argparse spent anonymously. Here the help path is
routed through `EXIT_OK` itself by the parser override below, so the value is
named without a second name for it existing - which keeps POSIX convention (a
successful --help exits 0) AND leaves every declared constant distinct.

WHAT A CALLER MUST THEREFORE NOT DO: read a zero exit as "a shortcut now
exists" without knowing which invocation produced it. `--help` and a completed
run are indistinguishable by status alone.

Usage:
    python scripts/make_shortcut.py
    python scripts/make_shortcut.py --force
    python scripts/make_shortcut.py --name <name>
    python scripts/make_shortcut.py --desktop-dir <directory>
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import time
from collections.abc import Sequence
from pathlib import Path
from typing import NoReturn

# Running a file puts that file's own directory on sys.path, not the repository
# root, so the package import below needs the insert. Same reasoning as
# scripts/make_cert.py and scripts/verify_env.py, which states it at length.
_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# CS-910. tools/ joins the path for the same reason the root above did, and the
# module is imported under its BARE name - see scripts/make_cert.py for the
# measurement that makes `tools.toolpath` the wrong spelling here.
_TOOLS_DIR = _REPO_ROOT / "tools"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from toolpath import resolve_tool  # noqa: E402

from clockspeed.data.locate import redact  # noqa: E402

#: The Electron shell's directory, relative to the repository root. Named as a
#: SEGMENT rather than a path so nothing here is ever an absolute literal.
SHELL_DIRNAME = "shell"

#: Where the Electron runtime lands under the shell directory, and the binary
#: itself. The `.exe` spelling is deliberate on every platform: this script
#: writes a WINDOWS shortcut, so the Windows runtime is what it must point at.
ELECTRON_RELATIVE = ("node_modules", "electron", "dist", "electron.exe")

#: What the shortcut passes to Electron. A bare dot resolves against the
#: working directory below, which is how Electron finds `shell/package.json`
#: and the `main` it names.
SHORTCUT_ARGUMENTS = "."

#: The tooltip. Fixed text, carrying no path.
SHORTCUT_DESCRIPTION = "Clockspeed companion window"

#: The default shortcut name, and the suffix WScript.Shell requires. It refuses
#: any destination that is not a `.lnk` or a `.url`.
DEFAULT_SHORTCUT_NAME = "Clockspeed"
SHORTCUT_SUFFIX = ".lnk"

#: Overrides where the shortcut is written. The flag beats this, and this beats
#: the resolved desktop.
ENV_DESKTOP_DIR = "CLOCKSPEED_DESKTOP_DIR"

#: Overrides where the Electron shell is looked for. Same precedence idea as
#: ENV_DESKTOP_DIR, and the same reason scripts/make_cert.py has one: a resolver
#: with no override can only be graded on a machine that already has the thing.
ENV_SHELL_DIR = "CLOCKSPEED_SHELL_DIR"

#: The staging directory's name prefix. Published rather than private because
#: the suite drives a stand-in PowerShell that has to find the staged file.
STAGING_PREFIX = ".make_shortcut-"

#: The interpreters that can reach the COM object, in the order they are tried.
#: Windows PowerShell first because it is present on every Windows install;
#: PowerShell 7 second because a machine may have only that.
POWERSHELL_NAMES = ("powershell", "pwsh")

#: Bounded, because an external probe that never returns hangs whatever called
#: it. Writing one shortcut is instantaneous; this is a ceiling, not a budget.
POWERSHELL_TIMEOUT_SECONDS = 60

#: Where Windows records the Desktop's real location. Read rather than assumed,
#: because a redirected profile - OneDrive being the common one - puts the
#: Desktop somewhere `<home>/Desktop` is not, and a shortcut written to the
#: wrong one is invisible to the operator. A REGISTRY subkey is not a filesystem
#: path and carries no account name.
DESKTOP_REGISTRY_KEY = r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders"
DESKTOP_REGISTRY_VALUE = "Desktop"

#: The last-resort spelling, used only when the registry cannot answer.
DESKTOP_DIRNAME = "Desktop"

#: Characters that turn a name into a path. Checked EXPLICITLY rather than by
#: comparing against `Path(name).name`, because that comparison is platform
#: dependent: a backslash is a separator on Windows and an ordinary character on
#: Linux, so the same hostile `--name` would be caught on one runner and pass on
#: the other. The colon joins them because Windows reads it as a drive or an
#: alternate data stream.
FORBIDDEN_NAME_CHARACTERS = ("/", "\\", ":")

#: The refusal text for a name that is not a bare file name. IT DOES NOT ECHO
#: THE NAME, which is the whole point: `--name` is operator input and could
#: carry a path, and a message quoting it back would print that path.
NAME_REFUSAL = "--name must be a bare file name carrying no directory separator"

EXIT_OK = 0
EXIT_NO_ELECTRON = 1
EXIT_NO_POWERSHELL = 2
EXIT_NO_DESKTOP = 3
EXIT_REFUSED = 4
EXIT_POWERSHELL_FAILED = 5

#: NAMED FOR THE OUTCOME RATHER THAN THE CAUSE, following make_cert.py: the
#: guard that returns it spans every filesystem step `_create` takes - staging,
#: the rename, and the cleanup. What they share is that the destination did not
#: end up holding a usable shortcut, and that is what a runbook branching here
#: needs to know.
EXIT_WRITE_FAILED = 6

#: THE CODE ARGPARSE WOULD OTHERWISE SPEND ANONYMOUSLY. Untouched,
#: `ArgumentParser` exits 2 on any usage error, and 2 means "no PowerShell" in
#: the table above - so a runbook branching on 2 could not tell a missing
#: interpreter from a misspelled flag. The parser override below moves it.
EXIT_USAGE = 7

#: os.replace can lose to a virus scanner or an open handle on Windows, and a
#: Desktop is exactly where an indexer is looking. A few short retries turn a
#: transient sharing violation into a completed rename.
_RENAME_ATTEMPTS = 5
_RENAME_PAUSE_SECONDS = 0.1


def ps_quote(value: str) -> str:
    """Render one string as a PowerShell single-quoted literal.

    A single-quoted PowerShell string has exactly ONE escape - a doubled quote -
    and nothing else inside it is special. No variable expansion, no backtick,
    and a Windows path's backslashes stay literal. That is why the whole
    rendered command below is built out of these.

    Args:
        value: The text to quote. Usually a path rendered by str().

    Returns:
        The quoted literal, including its surrounding quotes.
    """
    return "'" + value.replace("'", "''") + "'"


def electron_path(shell: Path) -> Path:
    """Locate the Electron runtime beneath a shell directory.

    PURE ON PURPOSE, and the reason is the one scripts/make_cert.py gives for
    `cert_argv`: separating the derivation from the filesystem is what lets it
    be asserted on a machine with no Electron installed at all, which is the
    machine the rule suite has to run on (BOOTSTRAP.md section 5.4).

    Args:
        shell: The shell directory. Not required to exist.

    Returns:
        The path the runtime occupies once it has been fetched.
    """
    return shell.joinpath(*ELECTRON_RELATIVE)


def shortcut_script(link_path: Path, target: Path, working_dir: Path) -> str:
    """Render the PowerShell that writes one shortcut, without running it.

    `$ErrorActionPreference` is the first statement and it is load-bearing:
    without it a failed property assignment leaves PowerShell exiting 0, and
    `$link.Save()` on a half-built object can still succeed - so the caller
    would be told a shortcut was written that points nowhere useful.

    Args:
        link_path: Where the `.lnk` is written.
        target: What it launches.
        working_dir: The directory it launches from.

    Returns:
        A single line of PowerShell, containing no double quote.
    """
    statements = (
        "$ErrorActionPreference = 'Stop'",
        "$shell = New-Object -ComObject WScript.Shell",
        f"$link = $shell.CreateShortcut({ps_quote(str(link_path))})",
        f"$link.TargetPath = {ps_quote(str(target))}",
        f"$link.Arguments = {ps_quote(SHORTCUT_ARGUMENTS)}",
        f"$link.WorkingDirectory = {ps_quote(str(working_dir))}",
        f"$link.Description = {ps_quote(SHORTCUT_DESCRIPTION)}",
        "$link.Save()",
    )
    return "; ".join(statements)


def shortcut_argv(
    link_path: Path,
    target: Path,
    working_dir: Path,
    powershell: str = POWERSHELL_NAMES[0],
) -> list[str]:
    """Render the complete command that writes the shortcut.

    `-NoProfile` matters for more than speed: a profile can print, can fail, and
    can PROMPT, and a prompt would hang a run that nothing is watching.
    `-NonInteractive` closes the same hole from the other side.

    Args:
        link_path: Where the `.lnk` is written.
        target: What it launches.
        working_dir: The directory it launches from.
        powershell: The executable, resolved from PATH by the caller. Defaults
            to the bare name so this stays callable with nothing installed.

    Returns:
        The complete argv, ready for subprocess.run with shell=False.
    """
    return [
        powershell,
        "-NoProfile",
        "-NonInteractive",
        "-Command",
        shortcut_script(link_path, target, working_dir),
    ]


def shortcut_file_name(raw: str | None) -> str:
    """Turn the --name value into the file name the shortcut is written under.

    Args:
        raw: The --name value, or None for the default.

    Returns:
        A bare file name ending in the required suffix.

    Raises:
        ValueError: The name was empty, or was a path rather than a name. The
            message names neither the value nor any path.
    """
    candidate = DEFAULT_SHORTCUT_NAME if raw is None else raw.strip()
    if not candidate or candidate in {".", ".."}:
        raise ValueError(NAME_REFUSAL)
    if any(character in candidate for character in FORBIDDEN_NAME_CHARACTERS):
        raise ValueError(NAME_REFUSAL)
    if candidate.endswith(SHORTCUT_SUFFIX):
        return candidate
    return candidate + SHORTCUT_SUFFIX


def shell_dir() -> Path:
    """Resolve where the Electron shell lives.

    Returns:
        The environment override if one is set, otherwise the in-repo shell
        directory derived from this file's own location. Not required to exist.
    """
    declared = (os.environ.get(ENV_SHELL_DIR) or "").strip()
    if declared:
        return Path(declared).expanduser()
    return _REPO_ROOT / SHELL_DIRNAME


def _registry_desktop() -> Path | None:
    """Ask Windows where the Desktop actually is.

    A redirected profile - OneDrive being the common one - moves the Desktop out
    from under the home directory, and a shortcut written to the unredirected
    spelling is invisible to the operator while the run reports success.

    No `sys.platform` guard is used. The import itself is the platform check,
    and writing it that way keeps the type checker from having to reason about
    a branch it has been pinned to consider unreachable.

    Returns:
        The recorded Desktop, or None off Windows and on any failure.
    """
    try:
        # PLC0415: winreg exists only on Windows, so the import IS the platform
        # check and cannot sit at module level.
        import winreg  # noqa: PLC0415

        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, DESKTOP_REGISTRY_KEY) as key:
            raw = winreg.QueryValueEx(key, DESKTOP_REGISTRY_VALUE)[0]
    except (ImportError, OSError, ValueError):
        return None
    if not isinstance(raw, str) or not raw.strip():
        return None
    return Path(os.path.expandvars(raw))


def desktop_dir(explicit: str | None = None) -> Path:
    """Resolve where the shortcut belongs.

    Precedence is flag, then environment, then the desktop Windows records,
    then the conventional spelling - stated here rather than left to whichever
    the reader assumes.

    Args:
        explicit: The --desktop-dir value, or None.

    Returns:
        The destination directory. Never created, and not required to exist.
    """
    if explicit:
        return Path(explicit).expanduser()
    declared = (os.environ.get(ENV_DESKTOP_DIR) or "").strip()
    if declared:
        return Path(declared).expanduser()
    recorded = _registry_desktop()
    if recorded is not None:
        return recorded
    return Path.home() / DESKTOP_DIRNAME


def pathless_cause(exc: OSError) -> OSError:
    """Clone an OSError without the two fields that carry the path.

    THE SAME IDIOM AS `scripts/make_cert.py::_pathless_cause`, replicated rather
    than imported: a script reaching into another script's private helper is not
    a seam this project has, and that docstring carries the long form of the
    reasoning.

    `OSError.__str__` appends `filename` and `filename2` verbatim, and under
    this script those hold the operator's Desktop - a directory whose path
    carries the Windows account name. Rebuilding from the two NAMED diagnostic
    fields carries errno and strerror across and leaves both filename fields
    unset, which closes that channel while keeping the reason the call failed.

    THE CALLER MUST RAISE THIS WITH `from None`. Raising it inside an `except`
    block sets `__context__` to the original, and the traceback formatter then
    renders that original in full underneath "During handling of the above
    exception" - both paths intact, on an exception whose own filename fields
    are empty.

    The two-argument form is deliberate. Supplying `winerror` as a fourth
    argument renders a WinError line reading None whenever the original carried
    none, which is worse than the errno it would replace. The errno-based
    subclass mapping still runs, so a PermissionError stays a PermissionError.

    Args:
        exc: The caught failure. ONLY `errno` and `strerror` are read.

    Returns:
        A new OSError of the same errno-mapped subclass, carrying no path.
    """
    return OSError(exc.errno, exc.strerror)


def _failure_detail(exc: OSError) -> str:
    """Render one OSError as an indented diagnostic line carrying no path.

    ONE PLACE TO BE RIGHT. Interpolating the exception itself is precisely the
    leak this module is built to avoid, since `str(exc)` appends both filename
    fields, so the rendering lives here rather than being hand-written at each
    site that reports a failure.

    `strerror` is redacted even though no platform puts a path in it today. It
    is a string this module did not write, the promise in the module docstring
    is unconditional, and redact() is idempotent and never raises - so the check
    costs nothing and cannot be the part that rots.

    Args:
        exc: The failure being reported.

    Returns:
        The line to print, already indented under its headline.
    """
    reason = redact(exc.strerror) if exc.strerror else "no reason given"
    return f"  {type(exc).__name__}, errno {exc.errno}: {reason}"


def _replace_with_retry(source: Path, target: Path) -> None:
    """Move `source` onto `target`, retrying a Windows sharing violation.

    ONLY PermissionError IS RETRIED: a scanner or an indexer can hold a handle
    on a file closed moments ago - and a Desktop is exactly where one is
    looking - while every other OSError is a real failure with nothing to wait
    for.

    WHAT LEAVES THIS FUNCTION IS NEVER THE ORIGINAL. `source.replace(target)`
    raises an OSError whose `str()` appends both absolute paths, and re-raising
    it would put the operator's Desktop in front of the default excepthook,
    where nothing redacts. Both exits raise a path-free clone, with `from None`
    so the original is not rendered as the suppressed context either.

    Args:
        source: The staged file.
        target: Where it belongs.

    Raises:
        OSError: The rename kept failing. It carries errno and strerror, and no
            path by either channel.
    """
    for attempt in range(_RENAME_ATTEMPTS):
        try:
            source.replace(target)
        except PermissionError as exc:
            if attempt == _RENAME_ATTEMPTS - 1:
                raise pathless_cause(exc) from None
            time.sleep(_RENAME_PAUSE_SECONDS)
        except OSError as exc:
            raise pathless_cause(exc) from None
        else:
            return


def _resolve_powershell() -> str | None:
    """Find an interpreter that can reach the WScript.Shell COM object.

    CS-910 - RESOLVED THROUGH ``tools/toolpath.py`` AND NOT THROUGH
    ``shutil.which``. This script writes a shortcut whose whole purpose is to be
    double-clicked from Explorer, and an Explorer-launched process is precisely
    the one whose current-directory search is LIVE. A powershell planted beside
    whatever the operator happened to be standing in would have been resolved to
    a relative path and spawned - MEASURED for the sibling openssl site on
    2026-09-05. The names are still resolved from PATH by name, which is what
    non-negotiable 3 requires; they are now resolved from PATH ALONE.

    Returns:
        The resolved absolute executable, or None when neither name is on PATH.
    """
    for name in POWERSHELL_NAMES:
        found = resolve_tool(name)
        if found is not None:
            return found
    return None


def _run_powershell(argv: list[str]) -> subprocess.CompletedProcess[bytes] | int:
    """Run the rendered command, translating every way it can fail to a code.

    SPLIT OUT OF `_create` SO ITS OSError HANDLER CANNOT SWALLOW A LAUNCH
    FAILURE. `subprocess.run` raises OSError when the executable vanishes
    between the PATH lookup and the call, and letting that reach the filesystem
    guard around staging would report "the shortcut could not be written" for a
    problem that is entirely about the tool.

    Args:
        argv: The complete command, already rendered.

    Returns:
        The completed process, or an exit code when the call itself failed.
        Anything it prints has already been printed.
    """
    try:
        return subprocess.run(
            argv,
            shell=False,
            capture_output=True,
            timeout=POWERSHELL_TIMEOUT_SECONDS,
            check=False,
        )
    except subprocess.TimeoutExpired:
        print(f"powershell did not return within {POWERSHELL_TIMEOUT_SECONDS}s")
        print("Nothing was written.")
        return EXIT_POWERSHELL_FAILED
    except OSError as exc:
        print("powershell could not be launched, so nothing was written.")
        print(_failure_detail(exc))
        return EXIT_POWERSHELL_FAILED


def _create(powershell: str, link_path: Path, target: Path, working_dir: Path) -> int:
    """Write the shortcut into a staging directory, then move it into place.

    STAGED RATHER THAN WRITTEN IN PLACE, for two reasons. Non-negotiable 5
    requires an atomic write for any file another process may read, and Explorer
    reads the Desktop continuously - a half-written `.lnk` would be visible as a
    broken icon. And a `--force` run whose PowerShell call fails would otherwise
    have already destroyed the working shortcut it was replacing; staging means
    a failed run leaves the previous one intact.

    NO OSError LEAVES THIS FUNCTION. Every filesystem call it makes raises an
    OSError carrying the path it could not use, and there is no handler between
    here and the interpreter: `main` returns this call bare and the module entry
    is `raise SystemExit(main())`. One guard spans the lot rather than three,
    because what they share is the only thing a caller can act on - the
    destination does not hold a usable shortcut - and three hand-written reports
    would be three chances to interpolate the exception.

    Args:
        powershell: The resolved interpreter.
        link_path: Where the shortcut belongs.
        target: What it launches.
        working_dir: The directory it launches from.

    Returns:
        An exit code. See the module docstring for what each one means.
    """
    destination = link_path.parent
    staging: Path | None = None
    try:
        staging = Path(tempfile.mkdtemp(prefix=STAGING_PREFIX, dir=str(destination)))
        staged = staging / link_path.name
        done = _run_powershell(shortcut_argv(staged, target, working_dir, powershell))
        if isinstance(done, int):
            return done

        if done.returncode != 0:
            print(f"powershell exited {done.returncode}, so nothing was written.")
            print("  Its error text is withheld here because it carries the destination path.")
            return EXIT_POWERSHELL_FAILED

        if not staged.is_file():
            print("powershell reported success but wrote no shortcut, so nothing was written.")
            return EXIT_POWERSHELL_FAILED

        _replace_with_retry(staged, link_path)
    except OSError as exc:
        print("the shortcut was not written into the destination directory")
        print(_failure_detail(exc))
        print("Check that the destination exists and is writable, then run this again.")
        return EXIT_WRITE_FAILED
    finally:
        if staging is not None:
            shutil.rmtree(staging, ignore_errors=True)

    print(f"wrote {redact(link_path.name)}")
    return EXIT_OK


class _ShortcutParser(argparse.ArgumentParser):
    """An argument parser that exits through this module's NAMED codes.

    ONE OVERRIDE COVERS BOTH ARGPARSE EXITS, and that is why `exit` is the
    method overridden rather than `error`. `ArgumentParser.error` does not call
    `sys.exit` itself - it routes through `self.exit(2, message)` - and the help
    action routes through `self.exit()` with the default status 0. So every way
    argparse can end this process passes through here, and a third one added by
    a future argparse would too.

    THE HELP PATH IS ROUTED THROUGH `EXIT_OK` RATHER THAN THROUGH A SECOND
    CONSTANT EQUAL TO IT. A successful --help keeps the status POSIX convention
    gives it, the value is named by a module constant so a test can enumerate
    it, and no two declared constants share a value. Only the usage path
    actually moves, off the 2 that means "no PowerShell" here.

    THE MESSAGE IS NOT TOUCHED. `super().exit` still writes it to stderr exactly
    as it did. Nothing argparse renders carries a path this module supplied -
    flag VALUES are never echoed by a usage error, and the one message this
    module hands it names no value - so the redaction promise in the module
    docstring is not weakened by letting argparse print.
    """

    def exit(self, status: int = 0, message: str | None = None) -> NoReturn:
        """Translate argparse's status into one of this module's codes.

        Args:
            status: What argparse wanted to exit with. 0 is the help path;
                anything else is a usage error, which argparse spells 2.
            message: The usage or help text, already rendered, or None.

        Raises:
            SystemExit: Always. This is the end of the process.
        """
        super().exit(EXIT_OK if status == 0 else EXIT_USAGE, message)


def main(argv: Sequence[str] | None = None) -> int:
    """Create the shortcut, or say precisely why it did not.

    THE ORDER OF THE CHECKS IS DELIBERATE. Everything that is about the
    operator's REQUEST - the name, the runtime, the destination, an existing
    shortcut - is decided before PowerShell is looked for, so a machine with no
    PowerShell is still told the real problem rather than being sent round the
    loop twice.

    Args:
        argv: Command line arguments, or None to read sys.argv.

    Returns:
        An exit code. See the module docstring for what each one means. The two
        argparse owns never come back through here - `parse_args` ends the
        process on the help path and on a usage error alike.
    """
    parser = _ShortcutParser(
        description="Create a desktop shortcut that opens the Clockspeed companion window.",
    )
    parser.add_argument(
        "--desktop-dir",
        default=None,
        help=f"where to write the shortcut; overrides {ENV_DESKTOP_DIR}",
    )
    parser.add_argument(
        "--name",
        default=None,
        help=f"the shortcut's name; {SHORTCUT_SUFFIX} is added when it is missing",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="replace an existing shortcut instead of refusing",
    )
    args = parser.parse_args(argv)

    try:
        link_name = shortcut_file_name(args.name)
    except ValueError:
        # THE CONSTANT IS NAMED, NOT THE EXCEPTION. `str(exc)` renders whatever
        # the raiser happened to put in the message, and both raise sites happen
        # to use this same fixed constant TODAY - which makes the object form
        # look safe while making the safety a coincidence one edit away from
        # ending. `tests/test_exception_rendering.py` forbids the shape rather
        # than the current contents for exactly that reason, and it caught this
        # line in the round that was fixing a redaction leak two hundred lines
        # further down.
        parser.error(NAME_REFUSAL)

    target = electron_path(shell_dir())
    if not target.is_file():
        print("The Electron runtime is not present, so no shortcut can point at it.")
        print("Run `npm install` in the shell directory, then `node -e \"require('electron')\"`.")
        print("npm install alone does not fetch it: the pinned Electron ships no postinstall.")
        return EXIT_NO_ELECTRON

    destination = desktop_dir(args.desktop_dir)
    if not destination.is_dir():
        print("The destination directory does not exist, so nothing was written.")
        print("Point --desktop-dir at a directory that exists, or omit it to use the desktop.")
        return EXIT_NO_DESKTOP

    link_path = destination / link_name
    if link_path.exists() and not args.force:
        print(f"refusing to overwrite an existing {redact(link_name)}")
        print("The operator may already have pinned or renamed the shortcut that is there.")
        print("Re-run with --force if replacing it is genuinely what you want.")
        return EXIT_REFUSED

    powershell = _resolve_powershell()
    if powershell is None:
        print("No PowerShell was found on PATH, so no shortcut can be created.")
        print("Add powershell or pwsh to PATH and run this again.")
        return EXIT_NO_POWERSHELL

    return _create(powershell, link_path, target, shell_dir())


if __name__ == "__main__":
    raise SystemExit(main())
