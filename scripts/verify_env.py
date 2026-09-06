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


def _run(cmd: list[str], timeout: int = 20) -> str | None:
    """Run a command and return stripped stdout, or None on any failure."""
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=False)
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
    return rows


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
    rows = [_row("SOFT", exe, *_tool_version(exe)) for exe in ("node", "gh", "openssl")]
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
