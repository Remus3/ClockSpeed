#!/usr/bin/env python3
"""Clockspeed environment verification.

Prints one row per external dependency with FOUND or MISSING plus a discovered
value, then the live state of every port in the reserved band. Exits non-zero
when any HARD dependency is missing. A bound port in the band is a SOFT failure
carrying a loud note.

Nothing here hardcodes a machine-specific fact. The interpreter comes from
sys.executable, and every path is discovered at runtime.

RESOLUTION IS NOT IMPLEMENTED HERE, AND THAT IS THE POINT. The phase 2 note
this docstring used to carry has been honoured: clockspeed/data/locate.py now
owns finding the install, the save root and the account directory, and owns
the precedence they follow - environment variable, then config/local.json,
then auto-detection. This script imports those resolvers and reports what they
answer, so what it prints is what the rest of the project will actually use. A
second copy here would be a second answer to "where is the game" waiting to
disagree with the first.

The re-export is deliberate and load-bearing rather than incidental:
tools/facts_probe.py imports resolve_game_dir, resolve_save_root and
numeric_account_dirs from THIS module, so keeping those names bound here is
what made the delegation cost its caller nothing.

The build string is still read here, because it is a property of the installed
binaries rather than a location.

PRIVACY: every path this script prints goes through redact() first, and the
account directory NAME is never printed - only a count and a redacted marker.
An EXCEPTION is a path-bearing value too and goes through _exc_reason() rather
than into a message, by any formatting syntax. This output is meant to be safe
to paste into an issue.

Usage:
    python scripts/verify_env.py
    python scripts/verify_env.py --json
"""

from __future__ import annotations

import argparse
import json
import os
import re
import socket
import subprocess
import sys
import tempfile
from pathlib import Path

# The bootstrap order in CONVENTIONS.md section 1 runs this script in a FRESH
# CLONE, before anything is installed and with no virtual environment active,
# so the package cannot be assumed importable from site-packages. Running a
# file puts that file's own directory on sys.path, not the repository root -
# hence the insert. Without it, `python scripts/verify_env.py` in a fresh
# clone dies on the import below instead of printing the dependency table it
# exists to print.
_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# CS-910. THE IMPORT DIRECTION IS scripts/ -> tools/, which is new and is the
# correct way round: tools/ already imports THIS module (tools/facts_probe.py
# reads the build reader off it), and tools/toolpath.py imports nothing outside
# the standard library, so the two cannot close a cycle. The BARE module name is
# required rather than preferred - see scripts/make_cert.py for the measurement.
# E402 for the same reason as the import below: it must follow the insert.
_TOOLS_DIR = _REPO_ROOT / "tools"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from toolpath import resolve_tool  # noqa: E402

# E402: this import must follow the sys.path insert above. The four names are
# re-exported by being bound here - tools/facts_probe.py reads three of them
# off this module (see the module docstring).
from clockspeed.data.locate import (  # noqa: E402
    numeric_account_dirs,
    redact,
    resolve_game_dir,
    resolve_save_root,
)

# --- policy constants -------------------------------------------------------

MIN_PYTHON = (3, 13)

EXPECTED_HOOKS_PATH = ".githooks"

# THE PARALLEL-LANE PYTEST PLUGIN, NAMED TWICE BECAUSE THE TWO NAMES DIFFER.
# The DISTRIBUTION is what pyproject.toml's dev extra pins and what pip
# resolves; the MODULE is what an import statement spells. Both are kept
# deliberately: the row prints the distribution so the operator can act on it,
# and the probe imports the module because that is what pytest itself does.
XDIST_DISTRIBUTION = "pytest-xdist"
XDIST_MODULE = "xdist"

# The probe source, run under the RESOLVED interpreter. A pytest PLUGIN is
# reached by IMPORT and never by -m: `python -m xdist --version` exits non-zero
# saying a package cannot be directly executed, so _module_backed_tool_row -
# correct for pytest, ruff and mypy - would report MISSING for a plugin that is
# installed and working. MEASURED on this machine with xdist 3.8.0 present.
#
# The getattr default keeps a future release that stops exporting __version__
# reading FOUND rather than MISSING, because the question this row answers is
# whether the plugin LOADS, not which version it is.
XDIST_PROBE = f"import {XDIST_MODULE} as _m; print(getattr(_m, '__version__', 'present'))"

# The five known CommunityResources artifacts, by relative path. Names only. No
# size is asserted against a literal: a game patch changes them, and a measured
# number frozen into a checker is a lie with a timestamp on it. Sizes are
# probed and reported.
COMMUNITY_ARTIFACTS = (
    "Docs/en-US.json",
    "FactoryGame.usmap",
    "CustomVersions.json",
    "DedicatedServerAPIDocs.md",
    "Headers.zip",
)

USMAP_RELATIVE = "FactoryGame.usmap"

# The default install locations, the Steam library parsing and the redaction
# needles all live in clockspeed/data/locate.py. Do not reintroduce them here.

BUILD_STRING_RE = re.compile(r"\+\+[A-Za-z0-9+._-]{0,120}CL-\d+")

MAX_BAND_WIDTH = 512
ADDRESS_IN_USE_ERRNOS = frozenset({48, 98})
ADDRESS_IN_USE_WINERRORS = frozenset({10048, 10013})
MAX_EXE_CANDIDATES = 6
MAX_MANIFEST_BYTES = 2_000_000

_DEP_HEADERS = ("SCOPE", "DEPENDENCY", "STATUS", "DISCOVERED VALUE")
_PORT_HEADERS = ("PORT", "STATE", "ALLOCATION", "DETAIL")


# --- small helpers ----------------------------------------------------------


def repo_root() -> Path:
    """Return the repository root, derived from this file's location."""
    return Path(__file__).resolve().parents[1]


def _exc_reason(exc: BaseException) -> str:
    """Render an exception as a REASON, with no filename and no path in it.

    THE ROOT CAUSE. ``str()`` on an OSError appends the filename the call
    failed on - "[Errno 13] Permission denied: '<a path>'" - while ``strerror``
    carries the reason alone. Every path this script touches is discovered at
    runtime and is routinely absolute and under a home directory, so it carries
    the Windows account name. CLAUDE.md non-negotiable 12 counts an error
    message as an echo path exactly like a debug dump or a hex preview, which
    makes interpolating an exception into a message a privacy defect.

    PER EXCEPTION TYPE, deliberately, because that is where the obvious version
    of this helper goes wrong. Only OSError carries ``strerror``; a
    JSONDecodeError and a UnicodeDecodeError do not, so a helper that reaches
    for it and falls back to ``str(exc)`` for everything else silently
    reintroduces the leak for every type it did not think about. Each type
    handled below names the fields that are known to hold a REASON, and an
    unrecognised type falls closed to its class name rather than to its text.

    Two fields are never rendered on purpose: ``JSONDecodeError.doc`` and
    ``UnicodeDecodeError.object`` hold file CONTENT rather than a reason.

    Args:
        exc: The exception being reported.

    Returns:
        A rendering safe to print, and never empty - an OSError with no
        strerror falls back to the class name rather than to nothing, because
        a failure whose reason is blank tells the reader less than nothing.
    """
    if isinstance(exc, OSError):
        return redact(exc.strerror or type(exc).__name__)
    if isinstance(exc, UnicodeDecodeError):
        return redact(f"{exc.encoding} codec failed at byte {exc.start}: {exc.reason}")
    if isinstance(exc, json.JSONDecodeError):
        return redact(f"{exc.msg} at line {exc.lineno} column {exc.colno}")
    return type(exc).__name__


def _run(
    cmd: list[str], timeout: int = 20, stdin: str | None = None, env: dict | None = None
) -> str | None:
    """Run a command and return stripped stdout, or None on any failure.

    ``stdin`` is handed to the child as its input and ``env`` replaces the
    inherited environment; both default to what every older caller got.
    """
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
            input=stdin,
            env=env,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if proc.returncode != 0:
        return None
    return (proc.stdout or "").strip()


def _first_line(text: str | None) -> str:
    if not text:
        return ""
    return text.splitlines()[0].strip()


def _tool_version(exe_name: str) -> tuple[bool, str]:
    """Locate an executable on PATH and read its version line.

    CS-910 - RESOLVED THROUGH ``tools/toolpath.py``. This function does not only
    report; it SPAWNS what it found, to read a version line. Resolving through
    ``shutil.which`` meant the reported row - and the process launched to fill it
    - could both be supplied by whatever directory the operator ran the script
    from. See :func:`_module_backed_tool_row` for the sibling that only reports.
    """
    found = resolve_tool(exe_name)
    if not found:
        return False, "not on PATH"
    version = _first_line(_run([found, "--version"]))
    where = redact(found)
    if version:
        return True, f"{version}  ({where})"
    return True, where


def _module_version(module: str) -> tuple[bool, str]:
    """Fall back to `python -m <module> --version` for a pip-installed tool."""
    version = _first_line(_run([sys.executable, "-m", module, "--version"]))
    if version:
        return True, f"{version}  (via python -m {module})"
    return False, "not importable as a module"


def _size_of(path: Path) -> str:
    try:
        return f"{path.stat().st_size} bytes"
    except OSError:
        return "size unreadable"


# --- build string -----------------------------------------------------------


def _version_info_strings(path: Path) -> dict[str, str]:
    """Read a Windows PE version resource with ctypes only. No dependency."""
    if sys.platform != "win32":
        return {}
    out: dict[str, str] = {}
    try:
        # PLC0415: ctypes.wintypes is Windows-only, same reason as winreg above.
        import ctypes  # noqa: PLC0415
        from ctypes import wintypes  # noqa: PLC0415

        version_dll = ctypes.WinDLL("version.dll")
        version_dll.GetFileVersionInfoSizeW.argtypes = [
            wintypes.LPCWSTR,
            ctypes.POINTER(wintypes.DWORD),
        ]
        version_dll.GetFileVersionInfoSizeW.restype = wintypes.DWORD
        version_dll.GetFileVersionInfoW.argtypes = [
            wintypes.LPCWSTR,
            wintypes.DWORD,
            wintypes.DWORD,
            ctypes.c_void_p,
        ]
        version_dll.GetFileVersionInfoW.restype = wintypes.BOOL
        version_dll.VerQueryValueW.argtypes = [
            ctypes.c_void_p,
            wintypes.LPCWSTR,
            ctypes.POINTER(ctypes.c_void_p),
            ctypes.POINTER(ctypes.c_uint),
        ]
        version_dll.VerQueryValueW.restype = wintypes.BOOL

        target = str(path)
        handle = wintypes.DWORD(0)
        size = version_dll.GetFileVersionInfoSizeW(target, ctypes.byref(handle))
        if not size:
            return {}
        buffer = ctypes.create_string_buffer(size)
        if not version_dll.GetFileVersionInfoW(target, 0, size, buffer):
            return {}

        pointer = ctypes.c_void_p()
        length = ctypes.c_uint()
        translations: list[tuple[int, int]] = []
        found = version_dll.VerQueryValueW(
            buffer, "\\VarFileInfo\\Translation", ctypes.byref(pointer), ctypes.byref(length)
        )
        if found and length.value:
            words = ctypes.cast(pointer, ctypes.POINTER(wintypes.WORD))
            translations = [
                (words[index * 2], words[index * 2 + 1]) for index in range(length.value // 4)
            ]
        if not translations:
            translations = [(0x0409, 0x04B0)]

        for language, codepage in translations:
            for key in ("ProductVersion", "FileVersion", "ProductName", "FileDescription"):
                sub_block = f"\\StringFileInfo\\{language:04x}{codepage:04x}\\{key}"
                value_ptr = ctypes.c_void_p()
                value_len = ctypes.c_uint()
                hit = version_dll.VerQueryValueW(
                    buffer, sub_block, ctypes.byref(value_ptr), ctypes.byref(value_len)
                )
                if hit and value_len.value:
                    text = ctypes.wstring_at(value_ptr, value_len.value).rstrip("\x00").strip()
                    if text and key not in out:
                        out[key] = text
    except Exception:
        # A version-resource read must never be able to fail a probe. Unknown
        # beats a guess, and both beat a traceback out of an environment check.
        return {}
    return out


def _executable_candidates(game_dir: Path) -> list[Path]:
    candidates: list[Path] = []
    try:
        candidates.extend(sorted(game_dir.glob("*.exe"))[:MAX_EXE_CANDIDATES])
        win64 = game_dir / "FactoryGame" / "Binaries" / "Win64"
        candidates.extend(sorted(win64.glob("*-Shipping.exe"))[:4])
        candidates.extend(sorted(win64.glob("*FactoryGame-Win64-Shipping.dll"))[:4])
    except OSError:
        return candidates
    return candidates


def _build_from_version_info(game_dir: Path) -> tuple[str | None, str]:
    """Best build string from a PE version resource, plus how it was read."""
    fallback: tuple[str | None, str] = (None, "")
    for candidate in _executable_candidates(game_dir):
        strings = _version_info_strings(candidate)
        for key in ("ProductVersion", "FileVersion"):
            value = strings.get(key, "")
            if BUILD_STRING_RE.fullmatch(value):
                return value, f"version-info:{key}"
            if value and fallback[0] is None:
                fallback = (value, f"version-info:{key} (not a full build string)")
    return fallback


def _build_from_modules(game_dir: Path) -> tuple[str | None, str]:
    win64 = game_dir / "FactoryGame" / "Binaries" / "Win64"
    try:
        modules_files = sorted(win64.glob("*.modules"))[:4]
    except OSError:
        return None, ""
    for modules_file in modules_files:
        try:
            payload = json.loads(modules_file.read_text(encoding="utf-8", errors="replace"))
        except (OSError, ValueError):
            continue
        build_id = str(payload.get("BuildId", "")).strip()
        if build_id:
            return f"CL-{build_id}", "modules-buildid (changelist only)"
    return None, ""


def _build_from_manifest(game_dir: Path) -> tuple[str | None, str]:
    for name in ("Manifest_NonUFSFiles_Win64.txt", "Manifest_DebugFiles_Win64.txt"):
        manifest = game_dir / name
        try:
            if not manifest.is_file():
                continue
            text = manifest.read_text(encoding="utf-8", errors="replace")[:MAX_MANIFEST_BYTES]
        except OSError:
            continue
        match = BUILD_STRING_RE.search(text)
        if match:
            return match.group(0), f"manifest:{name}"
    return None, ""


def read_build_string(game_dir: Path | None) -> tuple[str | None, str]:
    """Return (build string, how it was read) for the installed game.

    Primary source is the shipping executable's PE version resource, read with
    ctypes and no third-party dependency. Fallbacks are the shipping .modules
    manifest, which carries only the changelist, then the packaged file
    manifests. If none of them answers the result is unknown - never a guess,
    because a wrong build string silently invalidates every version-pinned
    artifact downstream.
    """
    if game_dir is None:
        return None, "no install"

    value, source = _build_from_version_info(game_dir)
    if value is not None and source.endswith(("ProductVersion", "FileVersion")):
        return value, source

    for probe in (_build_from_modules, _build_from_manifest):
        found, how = probe(game_dir)
        if found is not None:
            return found, how

    if value is not None:
        return value, source
    return None, "unknown"


# --- ports ------------------------------------------------------------------


def load_ports(root: Path) -> tuple[dict | None, str]:
    """Load config/ports.json. Returns (payload, error message)."""
    path = root / "config" / "ports.json"
    if not path.is_file():
        return None, "config/ports.json not found"
    try:
        return json.loads(path.read_text(encoding="utf-8")), ""
    except (OSError, ValueError) as exc:
        # The literal names the file; _exc_reason names why. What is dropped is
        # the DISCOVERED absolute path that str(exc) would have appended.
        return None, f"config/ports.json unreadable: {_exc_reason(exc)}"


def band_ports(payload: dict | None) -> list[int]:
    """Return every port in the recorded band, or an empty list if unusable."""
    if not payload:
        return []
    band = payload.get("band") or {}
    try:
        start = int(band["start"])
        end = int(band["end"])
    except (KeyError, TypeError, ValueError):
        return []
    if end < start or end - start > MAX_BAND_WIDTH:
        return []
    return list(range(start, end + 1))


def probe_port(port: int) -> tuple[str, str]:
    """Return (state, detail). FREE means nothing is bound on the loopback."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.settimeout(1.0)
        sock.bind(("127.0.0.1", port))
    except OSError as exc:
        code = getattr(exc, "errno", None)
        winerror = getattr(exc, "winerror", None)
        if code in ADDRESS_IN_USE_ERRNOS or winerror in ADDRESS_IN_USE_WINERRORS:
            return "BOUND", "something is listening"
        # The numeric code is kept because str(exc) used to render it and it is
        # what an operator searches for. A code is not personal data; the
        # filename str(exc) also appended is, so that half goes.
        prefix = ""
        if code is not None:
            prefix = f"[errno {code}] "
        elif winerror is not None:
            prefix = f"[winerror {winerror}] "
        return "ERROR", prefix + _exc_reason(exc)
    else:
        return "FREE", ""
    finally:
        sock.close()


# --- core.hooksPath ---------------------------------------------------------


def _normalized(path: Path) -> str:
    """Render a resolved path as a comparison key, folded the way the platform folds.

    ``os.path.normcase`` is the mechanism rather than a hand-rolled ``.lower()``
    because it is correct in BOTH directions. On Windows it lowercases and
    rewrites every forward slash as the native separator, so one directory
    spelled with either separator style and either drive-letter case compares
    equal - which it must, because git, the shell and the config file all
    render it either way and they name the same place. On a case-sensitive
    filesystem it is the identity, so two directories differing only in case
    stay correctly DISTINCT. A hand-rolled lowercase would silently equate them
    there, which is the same over-eager normalisation that turns this check
    decorative.

    Args:
        path: An already-resolved path.

    Returns:
        The comparison key.
    """
    return os.path.normcase(str(path))


def _resolved_key(path: Path) -> str | None:
    """Resolve a path and render it as a comparison key.

    Args:
        path: The path to resolve.

    Returns:
        The key, or None when the path cannot be resolved at all - which fails
        CLOSED at every call site, because an unresolvable path is not
        evidence that the hooks are wired.
    """
    try:
        return _normalized(path.resolve())
    except OSError:
        return None


def expected_hooks_dirs(root: Path, git_common_dir: str | None = None) -> list[Path]:
    """Every directory a correctly wired core.hooksPath may name.

    The repository's own ``.githooks`` is the whole answer in an ordinary
    checkout. A LINKED WORKTREE needs the second entry: ``core.hooksPath`` is
    shared config rather than per-worktree, so every worktree reads the value
    that was set for the main checkout, and git runs THOSE hook scripts rather
    than the worktree's own checked-out copy. Comparing only against the
    worktree's own ``.githooks`` would relocate the false RED this module was
    fixed to remove instead of removing it, and every slice in this project
    runs in a worktree.

    Args:
        root: The repository root being verified.
        git_common_dir: What ``git rev-parse --git-common-dir`` answered, or
            None when git could not be asked. It is relative (``.git``) in a
            main checkout and absolute in a linked worktree, so both are
            handled.

    Returns:
        The acceptable directories, the repository's own first, with the
        worktree entry appended only when it names somewhere different.
    """
    dirs = [root / EXPECTED_HOOKS_PATH]
    if git_common_dir:
        common = Path(git_common_dir)
        if not common.is_absolute():
            common = root / common
        main_hooks = common.parent / EXPECTED_HOOKS_PATH
        if main_hooks != dirs[0]:
            dirs.append(main_hooks)
    return dirs


def hooks_path_is_wired(
    root: Path, configured: str | None, git_common_dir: str | None = None
) -> bool:
    """Report whether core.hooksPath NAMES the repository's hooks directory.

    RESOLVED PATHS ARE COMPARED, NOT STRINGS, and that is the defect this
    function exists for. install_hooks.py writes the relative string
    ``.githooks`` and git hands it back ABSOLUTE on read, so a literal compare
    against ``.githooks`` reported a correctly wired repository as MISSING and
    the script exited non-zero saying a HARD dependency was absent while the
    hooks demonstrably fired. A false RED on the one script that verifies the
    safety net is worse than no check: it teaches the operator to ignore the
    script, and the next genuine missing dependency is ignored with it.
    Resolving both sides absorbs the absolute and the relative form, either
    separator, a trailing separator, and - through _normalized - drive-letter
    case.

    EXISTENCE IS CHECKED AS WELL AS IDENTITY, and the existence check is
    ``is_dir`` rather than ``exists``. ``Path.resolve`` is non-strict: for a
    directory that was never created, or was deleted, it still returns exactly
    the right string, so identity ALONE would report FOUND for hooks that
    cannot run. ``is_dir`` rather than ``exists`` because git needs a directory
    of hook scripts at that path - a regular file there runs nothing.

    What it deliberately does NOT do is match on the trailing segment. A check
    that asked whether the value ends with ``.githooks`` would accept an
    unrelated tree's hook directory, and the hooks that then run are not this
    repository's.

    Args:
        root: The repository root being verified.
        configured: The raw ``core.hooksPath`` value, or None when it is unset.
        git_common_dir: What ``git rev-parse --git-common-dir`` answered, or
            None when git could not be asked.

    Returns:
        True only when the configured path exists as a directory AND resolves
        to one of the directories expected_hooks_dirs allows.
    """
    if not configured or not configured.strip():
        return False

    candidate = Path(configured.strip())
    if not candidate.is_absolute():
        # git runs a hook from the top of the working tree, so a relative
        # core.hooksPath is anchored THERE rather than at the caller's cwd.
        candidate = root / candidate
    if not candidate.is_dir():
        return False

    key = _resolved_key(candidate)
    if key is None:
        return False
    return any(
        key == _resolved_key(expected) for expected in expected_hooks_dirs(root, git_common_dir)
    )


# --- checks -----------------------------------------------------------------


def _row(scope: str, name: str, ok: bool, value: str, note: str = "") -> dict:
    return {
        "scope": scope,
        "name": name,
        "status": "FOUND" if ok else "MISSING",
        "ok": ok,
        "value": value,
        "note": note,
    }


def _module_backed_tool_row(scope: str, name: str) -> dict:
    """Judge a python-module tool by the RESOLVED interpreter, not by PATH.

    BOOTSTRAP.md section 2.5 measured four Python installations on this machine
    and drew a MANDATORY consequence for this script: assert that the RESOLVED
    interpreter can import pytest and ruff, and HARD-fail if it cannot, because
    "reporting the version alone is not sufficient and would have passed this
    machine while the pre-push suite was unrunnable".

    THE ORDER IS THE WHOLE FIX. Probing PATH first answers FOUND out of a
    Scripts directory belonging to a DIFFERENT interpreter than the one that
    will run the gate, so the table certifies a toolchain the session cannot
    invoke - and an unrunnable check reads as a passed check. The module probe
    runs the tool the way every gate in this project runs it, so what it
    reports is what the gate will get (CS-806).

    PATH IS STILL READ, and only to tell the operator WHICH failure they have.
    "Install ruff" and "you are on the wrong interpreter" need different
    actions, and a row that collapses them wastes the finding.

    Args:
        scope: HARD or SOFT.
        name: The module name, which is also the executable name.

    Returns:
        One dependency row.
    """
    ok, value = _module_version(name)
    if ok:
        return _row(scope, name, True, value)

    # CS-910 - resolved through tools/toolpath.py like every other site here.
    # This one never spawns what it finds, so it is not itself a code-execution
    # path; it is routed anyway because a row reporting "an executable sits at
    # <a relative path in whatever directory you were standing in>" is a wrong
    # answer to the only question the row exists to settle, and because a census
    # that tolerates one unrouted resolver has no rule left to enforce.
    on_path = resolve_tool(name)
    if on_path:
        return _row(
            scope,
            name,
            False,
            f"not importable  (an executable sits at {redact(on_path)})",
            "on PATH but NOT importable by the interpreter running this script, so it "
            f"belongs to a DIFFERENT interpreter - a gate invoked as -m {name} will not "
            "run. Resolve the interpreter before trusting any gate.",
        )
    return _row(scope, name, False, value, "neither importable nor on PATH - install it")


# --- CS-818: the hooks' own interpreter ladder --------------------------------
#
# THE CS-806 SHAPE ONE DOOR ALONG. Every row above grades sys.executable, the
# interpreter RUNNING THIS SCRIPT. The hooks never ask it: they resolve their
# own interpreter through a four-rung ladder, so this table could read PASS
# while every gate ran under something it never graded.
#
# THE LADDER IS EXECUTED FROM THE HOOK'S BYTES, NEVER RE-IMPLEMENTED HERE. A
# Python copy of the rungs is a second answer to "which python gates a commit"
# waiting to disagree with the first. What runs is the pre-commit hook's marked
# region plus the probe it calls, extracted at run time.
# Only the scaffolding around them - initialising the two variables, a refusal
# function, and the identity query after the winner is chosen - is written here.
#
# GIT RUNS IT, AS A HOOK, SO GIT SUPPLIES THE ENVIRONMENT. The program is
# installed as the pre-commit hook of a throwaway repository and started with
# `git hook run`. Looking a shell up on THIS process's PATH was refuted by the
# M8 adversary: Git for Windows runs hooks under its own shell and puts its own
# tool directories on the hook's PATH, so a caller PATH naming only git's cmd
# directory - or putting System32 ahead of git's usr/bin - made this row fail
# while a real commit ran the hook fine. Asking git to run it removes the need
# to model what git does, in any version, on any platform.

LADDER_HOOK = ".githooks/pre-commit"
LADDER_BEGIN = "# >>> CS-818 LADDER BEGIN"
LADDER_END = "# <<< CS-818 LADDER END"
LADDER_ROW_NAME = "hooks' interpreter ladder"

# The throwaway repository's hook name, and the file the hook writes its answer
# to. The file is RELATIVE: git starts a hook in the root of the working tree,
# so no path is spelled into the program. Git sends a hook's stdout to its own
# stderr, and _run - the one spawn funnel - answers stdout only, hence a file.
LADDER_PROBE_HOOK = "pre-commit"
LADDER_OUTPUT = "cs818.out"

# Git locates a repository from these before it looks at -C, so an inherited
# one - a pre-push hook exports GIT_DIR - would aim the probe at a real
# repository. They are removed from the probe's environment and nothing else is.
_LADDER_GIT_LOCATORS = frozenset(
    {
        "GIT_DIR",
        "GIT_WORK_TREE",
        "GIT_INDEX_FILE",
        "GIT_COMMON_DIR",
        "GIT_OBJECT_DIRECTORY",
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_NAMESPACE",
        "GIT_PREFIX",
    }
)

# THE OUTER BOUND. Every candidate run inside the ladder is already bounded by
# the hook's own CS_PROBE_BOUND; this bounds the whole run from outside, so a
# shell that never returns cannot hang this script. It covers four rungs of
# three bounded halves each plus the identity query, with room to spare.
LADDER_OUTER_TIMEOUT = 150

# A refusal line from the ladder is the hook's own first die() argument, which
# is static text. It is redacted and capped anyway, because it is still text a
# subprocess wrote.
LADDER_REASON_CAP = 200

# The identity line's field count: executable hex, prefix hex, version.
_LADDER_IDENTITY_FIELDS = 3

# The winner reports its identity as three space-separated fields: the hex of
# its resolved executable, the hex of its resolved prefix, and its version. Hex
# keeps a non-ASCII path intact across whatever code page the pipe uses.
#
# THE PROGRAM HOLDS NO SINGLE QUOTE, NO SLASH AND NO COLON. No single quote, so
# it sits inside one in the shell text; no slash or colon, so an MSYS bash
# handing it to a native interpreter finds nothing path-shaped to rewrite.
_LADDER_IDENTITY_PROGRAM = (
    "import os, platform, sys; "
    "e = sys.executable; "
    'x = os.path.realpath(e) if e else ""; '
    "p = os.path.realpath(sys.prefix); "
    "v = platform.python_version(); "
    'sys.stdout.write(x.encode("utf-8", "surrogateescape").hex() + " " + '
    'p.encode("utf-8", "surrogateescape").hex() + " " + v)'
)

# The scaffolding. The hook initialises CS_PY and CS_PY_ARG OUTSIDE the marked
# region, so they are initialised here too. die() replaces the hook's own: it
# keeps only the first argument, which is the hook's static reason, marks it,
# and writes it to the probe's output with a zero exit, so a refusal is told
# apart from a hook that broke.
_LADDER_PREAMBLE = """set -u
die() {
    printf 'cs818-refused=%s\\n' "$1"
    exit 0
}
CS_PY=""
CS_PY_ARG=""
"""

# After the winner is chosen. The rung is reported by NAME: the variable's
# VALUE is never printed, exactly as the hooks never echo it. The identity query
# runs the winner the same way the hook will - resolved by this same shell,
# under the hook's own bound and capture.
_LADDER_EPILOGUE = (
    """cs818_rung="$CS_PY${CS_PY_ARG:+ $CS_PY_ARG}"
if [ -n "${CLOCKSPEED_PYTHON:-}" ]; then
    cs818_rung="CLOCKSPEED_PYTHON"
fi
printf 'cs818-rung=%s\\n' "$cs818_rung"
cs818_identity='"""
    + _LADDER_IDENTITY_PROGRAM
    + """'
cs818_out=$(timeout -k 1 "$CS_PROBE_BOUND" sh -c "$CS_PROBE_CAPTURE" \\
    cs818 "$CS_PY" ${CS_PY_ARG:+"$CS_PY_ARG"} -c "$cs818_identity" 2>/dev/null </dev/null)
printf 'cs818-status=%s\\n' "$?"
printf 'cs818-identity=%s\\n' "$cs818_out"
"""
)


def ladder_program(hook_text: str) -> tuple[str | None, str]:
    """Build the shell program that runs the hook's own ladder.

    The program is the hook's ``CS_PROBE_*`` assignments, its ``cs_probe``
    definition and its marked ladder region, byte for byte, between the
    scaffolding above. Nothing of the ladder is written here.

    Args:
        hook_text: The pre-commit hook's text.

    Returns:
        ``(program, "")``, or ``(None, reason)`` when the hook does not carry
        exactly one marked ladder and one probe definition.
    """
    text = hook_text.replace("\r\n", "\n")
    if text.count(LADDER_BEGIN) != 1 or text.count(LADDER_END) != 1:
        return None, "the hook does not carry exactly one pair of CS-818 ladder markers"
    begin = text.index(LADDER_BEGIN)
    end = text.index(LADDER_END) + len(LADDER_END)
    if end <= begin:
        return None, "the hook's CS-818 ladder markers are out of order"

    lines = text.split("\n")
    constants = [line for line in lines if line.startswith("CS_PROBE_")]
    probe: list[str] = []
    inside = False
    for line in lines:
        if line.startswith("cs_probe() {"):
            inside = True
        if inside:
            probe.append(line)
            if line == "}":
                break
    if not constants or not probe or probe[-1] != "}":
        return None, "the hook carries no complete cs_probe definition"

    program = "\n".join([_LADDER_PREAMBLE, *constants, *probe, text[begin:end], _LADDER_EPILOGUE])
    return program, ""


def _ladder_fields(stdout: str) -> dict[str, str]:
    """Parse the ``cs818-key=value`` lines the epilogue prints."""
    fields: dict[str, str] = {}
    for line in stdout.splitlines():
        key, sep, value = line.partition("=")
        if sep and key.startswith("cs818-"):
            fields[key] = value.rstrip("\r")
    return fields


def _identity_key(path: str) -> str:
    return os.path.normcase(path)


def _ladder_missing(value: str, note: str) -> dict:
    return _row("HARD", LADDER_ROW_NAME, False, value, note)


def _ladder_undetermined(value: str) -> dict:
    """SOFT: the environment git gives its hooks could not be determined.

    Never a HARD row. The question is what the hooks WILL do, and a probe that
    could not ask git has no answer - reading that as a refusal is how the
    first version of this row reported failures a real commit did not have.
    """
    return _row(
        "SOFT",
        LADDER_ROW_NAME,
        False,
        value,
        "the hooks' interpreter is UNVERIFIED - attempt a real commit to see what the hook does",
    )


def _run_ladder(root: Path, env: dict[str, str] | None) -> str | dict:
    """Have git run the extracted ladder as a hook, or answer why it could not.

    Returns:
        The probe hook's output, or a row naming why no answer came back.
    """
    try:
        hook_text = (root / LADDER_HOOK).read_text(encoding="ascii")
    except (OSError, UnicodeDecodeError) as exc:
        return _ladder_missing(f"{LADDER_HOOK} unreadable: {_exc_reason(exc)}", "")
    program, reason = ladder_program(hook_text)
    if program is None:
        return _ladder_missing(reason, "")

    child = dict(os.environ if env is None else env)
    for key in [key for key in child if key.upper() in _LADDER_GIT_LOCATORS]:
        del child[key]
    path_value = next((v for k, v in child.items() if k.upper() == "PATH"), "")
    git = resolve_tool("git", path_value=path_value)
    if not git:
        return _ladder_undetermined("git not found on PATH - no hook can run to ask")

    with tempfile.TemporaryDirectory(prefix="cs818-", ignore_cleanup_errors=True) as scratch:
        repo = Path(scratch) / "repo"
        hooks = Path(scratch) / "hooks"
        hooks.mkdir()
        hook = hooks / LADDER_PROBE_HOOK
        hook.write_bytes(f"#!/bin/sh\nexec >{LADDER_OUTPUT}\n{program}".encode("ascii"))
        hook.chmod(0o755)
        if _run([git, "init", "-q", str(repo)], env=child) is None:
            return _ladder_undetermined("git could not create a throwaway repository")
        _run(
            [
                git,
                "-C",
                str(repo),
                "-c",
                f"core.hooksPath={hooks}",
                "hook",
                "run",
                LADDER_PROBE_HOOK,
            ],
            timeout=LADDER_OUTER_TIMEOUT,
            env=child,
        )
        try:
            return (repo / LADDER_OUTPUT).read_text(encoding="utf-8", errors="replace")
        except OSError:
            return _ladder_undetermined(
                f"git ran no probe hook within {LADDER_OUTER_TIMEOUT}s - `git hook run` is"
                " unsupported, timed out, or could not start the hook's shell"
            )


def _grade_ladder(stdout: str) -> dict:
    """Grade a finished ladder run's winner against THIS interpreter."""
    fields = _ladder_fields(stdout)
    if "cs818-refused" in fields:
        shown = redact(fields["cs818-refused"].strip())[:LADDER_REASON_CAP]
        return _ladder_missing(
            f"the ladder refused: {shown}",
            "the hooks refuse every commit on this environment too",
        )

    rung = fields.get("cs818-rung", "")
    if not rung:
        return _ladder_undetermined("the probe hook ran but reported no winner")
    parts = fields.get("cs818-identity", "").split(" ")
    if fields.get("cs818-status") != "0" or len(parts) != _LADDER_IDENTITY_FIELDS:
        return _ladder_missing(
            f"the ladder chose {rung} but its winner did not answer the identity query",
            "",
        )
    try:
        winner_exe, winner_prefix = (bytes.fromhex(part).decode("utf-8") for part in parts[:2])
    except ValueError:
        return _ladder_missing(f"{rung} answered the identity query unreadably", "")
    version = parts[2]

    differs = []
    if not winner_exe or _identity_key(winner_exe) != _identity_key(
        os.path.realpath(sys.executable)
    ):
        differs.append("executable")
    if _identity_key(winner_prefix) != _identity_key(os.path.realpath(sys.prefix)):
        differs.append("prefix")
    if differs:
        return _ladder_missing(
            f"{rung} -> {version}, a DIFFERENT interpreter (differs in {' and '.join(differs)})",
            "the hooks gate every commit under the ladder's winner, not under the interpreter "
            "this table graded. Either set CLOCKSPEED_PYTHON to this interpreter and re-run, "
            "or re-run this script under the named rung and install pytest and ruff there "
            "(scripts/verify_env.py::ladder_row)",
        )
    return _row("HARD", LADDER_ROW_NAME, True, f"{rung} -> {version}, the interpreter graded here")


def ladder_row(root: Path, env: dict[str, str] | None = None) -> dict:
    """Run the hooks' own ladder and grade its winner against THIS interpreter.

    "DIFFERS" MEANS A DIFFERENT INTERPRETER, NOT A DIFFERENT NAME. ``py`` and
    ``python`` can be one interpreter, and one name can be two. The winner is
    RUN and reports its resolved executable AND its resolved prefix: a POSIX
    venv's executable is a symlink that resolves to the base binary, so the
    executable alone would call a venv carrying none of the toolchain "the same
    interpreter". The prefix is what tells them apart.

    THE WINNER'S PATH IS NEVER PRINTED. Through the first rung it is the
    CLOCKSPEED_PYTHON value, which the hooks deliberately do not echo; the row
    names the rung, the version and which half of the identity differs.

    WHAT THE OPERATOR DOES WHEN THIS ROW SAYS "A DIFFERENT INTERPRETER". The
    table above graded the interpreter running this script; the hooks will gate
    under the rung this row names. Make the two the same, one of two ways:

      1. Keep this interpreter. Set CLOCKSPEED_PYTHON to it - the first rung
         outranks PATH - and re-run this script; the row must then name
         CLOCKSPEED_PYTHON and read FOUND.
      2. Keep the winner. Re-run this script UNDER the named rung (for the
         python rung, `python scripts/verify_env.py`), so the pytest and ruff
         rows grade the interpreter the hooks will use; install the toolchain
         there if those rows read MISSING.

    Never silence the row by removing the winner from PATH alone: the ladder
    then falls to the next rung, whose last is 'py -3', the measured
    installation that carries no toolchain (BOOTSTRAP.md section 2.5).

    GIT SUPPLIES THE ENVIRONMENT. The ladder runs as a real hook of a
    throwaway repository, started by the git this environment resolves, so the
    shell, the PATH and the ``timeout`` it sees are the ones a real commit's
    hook sees. When git cannot be asked - absent, too old for ``git hook run``,
    or unable to start the hook - the row is SOFT and says the interpreter is
    unverified: an undetermined environment is never reported as a refusal.

    Args:
        root: The repository root whose pre-commit hook carries the ladder.
        env: The environment to run the ladder under, or None for this one.

    Returns:
        One dependency row: HARD, or SOFT when git could not be asked.
    """
    ran = _run_ladder(root, env)
    if isinstance(ran, dict):
        return ran
    return _grade_ladder(ran)


def _hard_rows(root: Path, facts: dict) -> list[dict]:
    version = ".".join(str(part) for part in sys.version_info[:3])
    minimum = ".".join(str(part) for part in MIN_PYTHON)
    python_ok = sys.version_info[:2] >= MIN_PYTHON
    facts["python_version"] = version
    rows = [
        _row(
            "HARD",
            f"python >= {minimum}",
            python_ok,
            f"{version}  ({redact(sys.executable)})",
            "" if python_ok else "interpreter predates the minimum",
        )
    ]

    git_ok, git_value = _tool_version("git")
    rows.append(_row("HARD", "git", git_ok, git_value))

    # CS-910 - RESOLVED ONCE, AND EVERY git BELOW SPAWNS THIS AND NOT A NAME.
    # The row above already resolved git properly and then threw the answer
    # away, and the three calls that followed handed CreateProcess a bare
    # "git" - which searches the CURRENT DIRECTORY first whenever the gate
    # variable is absent, its state at both machine and user scope here.
    # REPRODUCED: with a planted git in the working directory, the row "repo
    # root is a git work tree" flipped from ok to "rev-parse says no".
    #
    # THE REACH IS WHAT MADE IT URGENT. docs/OPERATIONS.md runs this script
    # SECOND in a fresh clone, before any protection is installed, and invokes
    # it repo-relative - so the working directory IS the repository root and
    # the operator has not yet run anything that would notice a plant.
    #
    # NO PATH IS SPELLED HERE. Non-negotiable 3 forbids that outright; this is
    # a runtime resolution against the PATH the process was handed.
    git_exe = resolve_tool("git")

    # The guard is the RESOLVED PATH and no longer the row's boolean. They
    # agree today, and tying the spawn to the thing being spawned means a
    # future edit cannot leave a None reaching the argv.
    tree = (
        _run([git_exe, "-C", str(root), "rev-parse", "--is-inside-work-tree"]) if git_exe else None
    )
    tree_ok = tree == "true"
    rows.append(
        _row(
            "HARD",
            "repo root is a git work tree",
            tree_ok,
            redact(root) if tree_ok else "rev-parse says no",
        )
    )

    hooks_dir = root / EXPECTED_HOOKS_PATH
    hooks_dir_ok = hooks_dir.is_dir()
    hook_names: list[str] = []
    if hooks_dir_ok:
        try:
            hook_names = sorted(path.name for path in hooks_dir.iterdir() if path.is_file())
        except OSError:
            hook_names = []
    if hook_names:
        hooks_value = f"{len(hook_names)} hook file(s): {', '.join(hook_names)}"
    elif hooks_dir_ok:
        hooks_value = "present but empty"
    else:
        hooks_value = "absent"
    rows.append(
        _row(
            "HARD",
            f"{EXPECTED_HOOKS_PATH} directory",
            hooks_dir_ok,
            hooks_value,
            "" if hooks_dir_ok else "run: python scripts/install_hooks.py",
        )
    )

    # CS-910 - both spawn the resolved path bound above, for the reason recorded
    # there. These two decide the core.hooksPath verdict, so a planted git here
    # reports a wired clone while nothing is wired - the silent failure the
    # installer's own docstring calls out as the one that must never happen.
    configured = (
        _run([git_exe, "-C", str(root), "config", "--get", "core.hooksPath"]) if git_exe else None
    )
    common_dir = (
        _run([git_exe, "-C", str(root), "rev-parse", "--git-common-dir"]) if git_exe else None
    )
    hooks_path_ok = hooks_path_is_wired(root, configured, common_dir)

    # PRIVACY. The configured value is a DISCOVERED absolute path, so on a
    # checkout under a user profile it carries the Windows account name, and
    # CLAUDE.md non-negotiable 12 counts a printed table as an echo path
    # exactly like a debug dump. It reaches TWO renderings - this row and the
    # --json facts block - so it is redacted once, here, and both read the
    # redacted form. Redacting only where the table is built would leave the
    # machine-readable output, the one most likely to be pasted into an issue,
    # carrying the home path.
    shown = redact(configured) if configured else ""
    facts["hooks_path"] = shown

    # The label says "->" and not "==" because the check is no longer a string
    # equality against the literal: an absolute path that RESOLVES to the
    # repository's hooks directory is what a real repository holds.
    rows.append(
        _row(
            "HARD",
            f"core.hooksPath -> {EXPECTED_HOOKS_PATH}",
            hooks_path_ok,
            shown or "unset",
            ""
            if hooks_path_ok
            else "a fresh clone runs ZERO protection until install_hooks.py sets this",
        )
    )

    rows.extend(_module_backed_tool_row("HARD", name) for name in ("pytest", "ruff"))

    # CS-818: the rows above grade THIS interpreter; this one proves it is the
    # interpreter the hooks will actually gate under.
    rows.append(ladder_row(root))
    return rows


def _parallel_plugin_row() -> dict:
    """Report the parallel-lane pytest plugin, SOFT, so its absence cannot fail.

    CS-906 CONDITION SIX. The pre-push hook runs its suite in parallel and
    DEGRADES TO SERIAL when this plugin is absent, printing a remediation line.
    An advice line the operator cannot confirm is a false lead, and this row is
    what makes it confirmable: run the script, read the row, see it flip.

    SOFT AND NOT HARD, and the distinction is the whole point of the condition.
    The serial fallback runs the same tests and reaches the same verdict, so the
    plugin is a SPEEDUP. A HARD row would fail the entire environment check on a
    checkout where nothing is wrong - turning one false lead into two, and
    teaching the operator to ignore the script that verifies the safety net.

    IT DOES NOT REUSE :func:`_module_backed_tool_row`, for the reason recorded
    at XDIST_PROBE: the module channel that is correct for pytest, ruff and mypy
    is wrong here, because a package with no __main__ cannot be run as one.

    NO PATH IS PUT IN THE ROW. The sibling builder resolves an executable to
    tell the operator which failure they have; there is no xdist executable to
    resolve, and a discovered path printed here would be an echo path for
    nothing (CLAUDE.md non-negotiable 12).

    Returns:
        One dependency row, always SOFT.
    """
    version = _first_line(_run([sys.executable, "-c", XDIST_PROBE]))
    if version:
        return _row(
            "SOFT",
            XDIST_DISTRIBUTION,
            True,
            f"{version}  (import {XDIST_MODULE} under the resolved interpreter)",
        )
    return _row(
        "SOFT",
        XDIST_DISTRIBUTION,
        False,
        f"{XDIST_MODULE} not importable by the resolved interpreter",
        "the pre-push suite falls back to SERIAL and says so - it is slower, not "
        'broken. Restore the parallel lane with: python -m pip install -e ".[dev]"',
    )


def _optional_tool_rows() -> list[dict]:
    # node, gh and openssl are genuine executables and are judged by PATH. mypy
    # is a python module and shares pytest and ruff's root cause exactly - the
    # tier-2 gate invokes it as -m mypy - so it follows the same rule.
    #
    # openssl is SOFT for the same reason node is: it is needed by phase 6, to
    # mint the certificate the local dashboard listens with
    # (scripts/make_cert.py), and the advice path has to stay runnable on a
    # machine that has neither. A HARD row here would fail the verdict on a
    # machine where nothing is actually wrong.
    # pytest-xdist leads the SOFT block so it renders BESIDE the pytest and ruff
    # rows that close the HARD block - the three the pre-push hook depends on,
    # read together. It is judged by neither channel used below; see
    # _parallel_plugin_row.
    rows = [_parallel_plugin_row()]
    rows.extend(_row("SOFT", exe, *_tool_version(exe)) for exe in ("node", "gh", "openssl"))
    rows.append(_module_backed_tool_row("SOFT", "mypy"))
    return rows


def _locale_file_count(community: Path) -> int:
    docs_dir = community / "Docs"
    if not docs_dir.is_dir():
        return 0
    try:
        return sum(1 for path in docs_dir.iterdir() if path.is_file() and path.suffix == ".json")
    except OSError:
        return 0


def _game_rows(facts: dict) -> list[dict]:
    game_dir, resolver = resolve_game_dir()
    facts["game_resolver"] = resolver
    rows = [
        _row(
            "SOFT",
            "game install",
            game_dir is not None,
            f"{redact(game_dir)}  (resolved by {resolver})"
            if game_dir is not None
            else "not resolved (tried env, steam library index, defaults)",
            "" if game_dir is not None else "the rule suite must still run without it",
        )
    ]

    build_string, build_source = read_build_string(game_dir)
    facts["game_build"] = build_string or ""
    rows.append(
        _row(
            "SOFT",
            "game build string",
            build_string is not None,
            f"{build_string}  (via {build_source})" if build_string else "unknown",
        )
    )

    # NARROWED RATHER THAN FLAGGED, and the difference is the whole of CS-414.
    # This block used to carry a separate boolean - `community_ok`, `artifact_ok`,
    # `usmap_ok` - that PROVED the neighbouring `Path | None` was non-None while
    # being invisible to the type checker as a proof. Five errors followed, codes
    # arg-type and operator, and they were held out of the gate by an `exclude`
    # key rather than fixed. Collapsing each flag into the `is not None` test on
    # the optional itself makes the proof and the narrowing the SAME expression,
    # so the two cannot drift apart. Each optional is set to None the moment its
    # filesystem check fails, which keeps exactly one stat call per path - a
    # second `is_file()` at the render site would open a window in which the row
    # says FOUND and renders "absent".
    community = (game_dir / "CommunityResources") if game_dir is not None else None
    if community is not None and not community.is_dir():
        community = None
    locale_count = _locale_file_count(community) if community is not None else 0
    rows.append(
        _row(
            "SOFT",
            "CommunityResources",
            community is not None,
            f"{redact(community)}  ({locale_count} locale json file(s) in Docs/)"
            if community is not None
            else "absent",
        )
    )

    for relative in COMMUNITY_ARTIFACTS:
        artifact = (community / relative) if community is not None else None
        if artifact is not None and not artifact.is_file():
            artifact = None
        rows.append(
            _row(
                "SOFT",
                f"  CommunityResources/{relative}",
                artifact is not None,
                _size_of(artifact) if artifact is not None else "absent",
            )
        )

    usmap = (community / USMAP_RELATIVE) if community is not None else None
    if usmap is not None and not usmap.is_file():
        usmap = None
    rows.append(
        _row(
            "SOFT",
            "usmap property mappings",
            usmap is not None,
            _size_of(usmap) if usmap is not None else "absent",
            "same file as the CommunityResources row above; called out separately "
            "because the save reader is built around it",
        )
    )
    return rows


def _save_rows(facts: dict) -> list[dict]:
    save_root = resolve_save_root()
    rows = [
        _row(
            "SOFT",
            "save root",
            save_root is not None,
            redact(save_root) if save_root is not None else "absent",
        )
    ]
    accounts = numeric_account_dirs(save_root)
    facts["account_dir_count"] = len(accounts)
    rows.append(
        _row(
            "SOFT",
            "numeric account dir",
            bool(accounts),
            f"{len(accounts)} found; using <account-dir:redacted> (most recently modified)"
            if accounts
            else "none found",
            "the directory name is a platform account id and is never printed",
        )
    )
    return rows


def collect_rows(root: Path) -> tuple[list[dict], list[dict], dict]:
    """Run every check. Returns (dependency rows, port rows, extra facts)."""
    facts: dict = {}
    rows = _hard_rows(root, facts)
    rows.extend(_optional_tool_rows())
    rows.extend(_game_rows(facts))
    rows.extend(_save_rows(facts))

    ports_payload, ports_error = load_ports(root)
    if ports_payload is not None:
        band = ports_payload.get("band") or {}
        ports_value = (
            f"base {ports_payload.get('base')}, band {band.get('start')}-{band.get('end')}"
        )
    else:
        ports_value = ports_error
    rows.append(_row("SOFT", "config/ports.json", ports_payload is not None, ports_value))

    allocations = (ports_payload or {}).get("allocations") or {}
    port_rows = []
    for port in band_ports(ports_payload):
        state, detail = probe_port(port)
        port_rows.append(
            {
                "port": port,
                "state": state,
                "detail": detail,
                "allocation": allocations.get(str(port), "reserved"),
            }
        )
    return rows, port_rows, facts


# --- rendering --------------------------------------------------------------


def _table(headers: tuple[str, ...], rows: list[list[str]]) -> list[str]:
    widths = [len(header) for header in headers]
    for row in rows:
        for index, cell in enumerate(row):
            widths[index] = max(widths[index], len(cell))
    out = ["  ".join(headers[i].ljust(widths[i]) for i in range(len(headers))).rstrip()]
    out.append("  ".join("-" * widths[i] for i in range(len(headers))))
    out.extend(
        "  ".join(row[i].ljust(widths[i]) for i in range(len(headers))).rstrip() for row in rows
    )
    return out


def _render_ports(port_rows: list[dict], bound: list[dict]) -> list[str]:
    if not port_rows:
        return ["Reserved port band: NOT PROBED - no usable band in config/ports.json"]
    out = ["Reserved port band (config/ports.json is the owner of these numbers)"]
    out.extend(
        _table(
            _PORT_HEADERS,
            [
                [str(row["port"]), row["state"], row["allocation"], row["detail"]]
                for row in port_rows
            ],
        )
    )
    if bound:
        out.append("")
        out.append("!" * 72)
        out.append(f"SOFT FAILURE: {len(bound)} port(s) in the reserved band are not free.")
        out.extend(f"  {row['port']} is {row['state']} {row['detail']}" for row in bound)
        out.append("The band was recorded as free at allocation time. Something else took a")
        out.append("port, or a previous Clockspeed process did not shut down. Find it before")
        out.append("binding, and re-record config/ports.json if the band has to move.")
        out.append("!" * 72)
    return out


def render(rows: list[dict], port_rows: list[dict], root: Path) -> list[str]:
    """Render the dependency table, the port table and the verdict."""
    out = ["Clockspeed environment verification", f"repo: {redact(root)}", ""]
    out.extend(
        _table(
            _DEP_HEADERS,
            [[row["scope"], row["name"], row["status"], row["value"]] for row in rows],
        )
    )

    notes = [row for row in rows if row["note"] and not row["ok"]]
    if notes:
        out.extend(["", "Notes on missing items:"])
        out.extend(f"  {row['scope']:<8} {row['name']}: {row['note']}" for row in notes)

    bound = [row for row in port_rows if row["state"] != "FREE"]
    out.append("")
    out.extend(_render_ports(port_rows, bound))

    hard_missing = [row for row in rows if row["scope"] == "HARD" and not row["ok"]]
    soft_missing = [row for row in rows if row["scope"] == "SOFT" and not row["ok"]]
    hard_total = sum(1 for row in rows if row["scope"] == "HARD")
    soft_total = sum(1 for row in rows if row["scope"] == "SOFT")
    out.append("")
    out.append(
        f"HARD: {hard_total - len(hard_missing)}/{hard_total} present    "
        f"SOFT: {soft_total - len(soft_missing)}/{soft_total} present    "
        f"ports free: {len(port_rows) - len(bound)}/{len(port_rows)}"
    )
    if hard_missing:
        names = ", ".join(row["name"] for row in hard_missing)
        out.append(f"VERDICT: FAIL - missing HARD dependencies: {names}")
    else:
        out.append("VERDICT: PASS - every HARD dependency is present")
    if soft_missing:
        names = ", ".join(row["name"].strip() for row in soft_missing)
        out.append(f"SOFT missing (reported, not fatal): {names}")
    return out


def main(argv: list[str] | None = None) -> int:
    """Verify the environment and print the result. Returns the exit code."""
    parser = argparse.ArgumentParser(
        description="Verify the Clockspeed environment. Exits non-zero on a missing HARD "
        "dependency. Never prints an account id, a world name or a home path."
    )
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args(argv)

    root = repo_root()
    rows, port_rows, facts = collect_rows(root)
    hard_missing = [row for row in rows if row["scope"] == "HARD" and not row["ok"]]
    bound = [row for row in port_rows if row["state"] != "FREE"]

    if args.json:
        print(
            json.dumps(
                {
                    "schema": 1,
                    "repo": redact(root),
                    "dependencies": rows,
                    "ports": port_rows,
                    "facts": facts,
                    "hard_missing": [row["name"] for row in hard_missing],
                    "ports_not_free": [row["port"] for row in bound],
                    "verdict": "FAIL" if hard_missing else "PASS",
                },
                indent=2,
            )
        )
    else:
        print("\n".join(render(rows, port_rows, root)))

    return 1 if hard_missing else 0


if __name__ == "__main__":
    sys.exit(main())
