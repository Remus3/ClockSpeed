#!/usr/bin/env python3
"""Wire the Clockspeed git hooks. Idempotent, verifying, loud on failure.

Seam: `install_hooks.py` (no arguments).

CONVENTIONS.md section 1: a fresh clone runs ZERO protection until someone
wires it, because core.hooksPath is local config and is never cloned. This is
the first thing to run in a new clone.

What it does:
  1. Refuses to run outside a git work tree.
  2. Sets core.hooksPath to .githooks.
  3. Reads the value BACK with `git config --get core.hooksPath` and compares.
     Setting a value is not evidence the value took.
  4. Verifies each hook exists, is LF-only and has no BOM.

     Measured 2026-08-13 on git 2.53.0.windows.3 (GNU bash 5.2.37 msys): that
     bash RUNS a CRLF hook correctly, so on this toolchain CRLF is not the
     silent-failure mode CONVENTIONS.md section 16 warns about. It still fails
     the check, because stricter shells (dash, ash, older msys) do break on
     the trailing CR and CI tier 2 runs these hooks on a POSIX runner. Section
     16 also says hook findings are version-specific and expire - re-measure,
     never inherit, and never relax a check because one release is tolerant.
  5. Sets the executable bit on POSIX. On Windows the bit is meaningless to
     Git for Windows' sh, so it is reported as not applicable rather than
     faked.

Every failure path exits non-zero. Running it twice is a no-op with identical
output.
"""

from __future__ import annotations

import os
import stat
import subprocess
import sys
import traceback
from pathlib import Path

TOOL_NAME = "install_hooks"
HOOKS_DIR_NAME = ".githooks"
CONFIG_KEY = "core.hooksPath"
GIT_TIMEOUT = 30

# The hooks this installer is responsible for wiring.
EXPECTED_HOOKS = ("pre-commit", "commit-msg", "pre-push")


class InstallError(RuntimeError):
    """Anything that must stop the install with a non-zero exit."""


def _exc_reason(exc: BaseException) -> str:
    """Render an exception as a REASON, with no filename and no path in it.

    THE ROOT CAUSE. ``str()`` on an OSError appends the filename the call
    failed on - "[Errno 13] Permission denied: '<a path>'" - while ``strerror``
    carries the reason alone. A fresh clone routinely sits under a home
    directory, so that path carries the Windows account name, and CLAUDE.md
    non-negotiable 12 counts an error message as an echo path exactly like a
    debug dump or a hex preview.

    PER EXCEPTION TYPE, deliberately, because that is where the obvious version
    of this helper goes wrong. Only OSError carries ``strerror``; a
    TimeoutExpired and a CalledProcessError do not, so a helper that reaches
    for it and falls back to ``str(exc)`` for everything else silently
    reintroduces the leak for every type it did not think about. An
    unrecognised type falls closed to its class name rather than to its text.

    DUPLICATED FROM tools/precommit_gate.py::safe_exc_text ON PURPOSE, and the
    duplication is the point rather than an oversight. This script is the FIRST
    thing a fresh clone runs (CONVENTIONS.md section 1), before anything is
    installed and while `clockspeed/` and `tools/` may be absent, half-written
    or syntactically broken. Importing a redactor from either would make the
    one script whose job is to wire the protection unable to run without the
    code it protects. tests/test_exception_rendering.py proves the installer
    still runs and still exits correctly with both directories gone.
    """
    if isinstance(exc, InstallError):
        # Its message is built in this module and is already free of git's
        # stderr and of every discovered path.
        return str(exc) or type(exc).__name__
    if isinstance(exc, OSError):
        return exc.strerror or type(exc).__name__
    if isinstance(exc, subprocess.TimeoutExpired):
        return "%s after %s seconds" % (type(exc).__name__, exc.timeout)
    if isinstance(exc, subprocess.CalledProcessError):
        return "%s exit %d" % (type(exc).__name__, exc.returncode)
    return type(exc).__name__


def run_git(args: list[str], cwd: str | None = None) -> str:
    """Run git and return stdout, raising InstallError on any failure.

    The argv IS rendered on failure, unlike the gate's, and that is a measured
    difference rather than an inconsistency: every caller below passes literal
    constants, so this argv carries no discovered path. The gate redacts its
    own because in `--files` mode the argv is built from caller-supplied paths.
    """
    try:
        proc = subprocess.run(
            ["git", *args],
            capture_output=True,
            cwd=cwd,
            timeout=GIT_TIMEOUT,
            check=False,
        )
    except FileNotFoundError as exc:
        raise InstallError(f"git is not on PATH: {_exc_reason(exc)}") from exc
    except (OSError, subprocess.SubprocessError) as exc:
        raise InstallError(
            "git {} failed to run: {}".format(" ".join(args), _exc_reason(exc))
        ) from exc
    if proc.returncode != 0:
        # git's stderr is NOT rendered. It reports absolute paths in it -
        # "fatal: cannot change to '<a path>'" - and this clone may sit under a
        # home directory, which makes the stderr channel an echo path exactly
        # like an exception is (CLAUDE.md non-negotiable 12). The argv and the
        # exit code are kept: they say which git call failed and how.
        raise InstallError(
            "git %s exited %d (its stderr is withheld: git prints absolute "
            "paths there). Run that command by hand to see it." % (" ".join(args), proc.returncode)
        )
    return proc.stdout.decode("utf-8", "replace").strip()


def require_work_tree(start: Path) -> Path:
    """Return the repo root, or refuse to run outside a work tree."""
    try:
        inside = run_git(["rev-parse", "--is-inside-work-tree"], cwd=str(start))
    except InstallError as exc:
        raise InstallError(
            f"refusing to run: not inside a git work tree ({_exc_reason(exc)})"
        ) from exc
    if inside != "true":
        raise InstallError(
            f"refusing to run: `git rev-parse --is-inside-work-tree` said {inside!r}"
        )
    return Path(run_git(["rev-parse", "--show-toplevel"], cwd=str(start)))


def inspect_hook(path: Path) -> tuple[str, str]:
    """Return (status, detail) for one hook file. status is OK or a failure."""
    if not path.is_file():
        return ("MISSING", "no such file")
    data = path.read_bytes()
    non_ascii = data.translate(None, delete=bytes(range(0x7F)))
    problems = (
        (not data, "EMPTY", "zero bytes"),
        (
            data.startswith(b"\xef\xbb\xbf"),
            "BOM",
            "starts with a UTF-8 BOM; sh cannot parse the shebang",
        ),
        (
            b"\r\n" in data,
            "CRLF",
            "contains CRLF line endings; stricter shells (dash, ash, older "
            "msys) fail the shebang on the trailing CR, and CI tier 2 runs "
            "these hooks on a POSIX runner",
        ),
        (
            not data.startswith(b"#!"),
            "NOSHEBANG",
            "does not start with a shebang line",
        ),
        (
            bool(non_ascii),
            "CHARSET",
            f"contains {len(non_ascii)} byte(s) above 0x7E",
        ),
    )
    for hit, status, detail in problems:
        if hit:
            return (status, detail)
    return ("OK", f"{len(data)} bytes, LF, ascii")


def set_executable(path: Path) -> str:
    """Set the executable bit on POSIX; report n/a on Windows.

    Reports the RESULTING state, not the transition, so a second run prints
    byte-identical output to the first. Idempotence the operator can see.
    """
    if os.name == "nt":
        return "n/a on windows"
    mode = path.stat().st_mode
    wanted = mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
    if mode != wanted:
        path.chmod(wanted)
    return "executable"


def install(root: Path) -> int:
    """Wire core.hooksPath, verify it took, and report what was wired."""
    hooks_dir = root / HOOKS_DIR_NAME
    if not hooks_dir.is_dir():
        # The path is named RELATIVE to the repository root rather than rendered
        # absolute: the root is discovered at runtime and may sit under a home
        # directory (CLAUDE.md non-negotiable 12). The reader knows which repo
        # they ran this in.
        raise InstallError(
            f"no {HOOKS_DIR_NAME}/ directory at the repository root; nothing to wire"
        )

    run_git(["config", CONFIG_KEY, HOOKS_DIR_NAME], cwd=str(root))

    # Setting a value is not evidence the value took. Read it back.
    readback = run_git_optional(["config", "--get", CONFIG_KEY], root)
    if readback != HOOKS_DIR_NAME:
        raise InstallError(
            f"{CONFIG_KEY} did not take: wrote {HOOKS_DIR_NAME!r}, "
            f"read back {readback!r}. The hooks are NOT wired."
        )

    rows: list[tuple[str, str, str, str]] = []
    failures: list[str] = []
    for name in EXPECTED_HOOKS:
        path = hooks_dir / name
        status, detail = inspect_hook(path)
        if status == "OK":
            try:
                exec_note = set_executable(path)
            except OSError as exc:
                reason = _exc_reason(exc)
                status, detail = ("CHMOD", f"could not set the executable bit: {reason}")
                exec_note = "failed"
        else:
            exec_note = "not attempted"
        rows.append((name, status, exec_note, detail))
        if status != "OK":
            failures.append(f"{name}: {status} - {detail}")

    width = max(len(name) for name in EXPECTED_HOOKS)
    print(f"{TOOL_NAME}: wiring {root}")
    print()
    print("  %-*s  %-9s  %-18s  %s" % (width, "hook", "status", "exec bit", "detail"))
    print("  {}  {}  {}  {}".format("-" * width, "-" * 9, "-" * 18, "-" * 24))
    for name, status, exec_note, detail in rows:
        print("  %-*s  %-9s  %-18s  %s" % (width, name, status, exec_note, detail))
    print()
    print("  %-*s  %s" % (width, CONFIG_KEY, readback))
    print()

    if failures:
        sys.stderr.write(f"{TOOL_NAME}: FAILED - unusable hook file(s):\n")
        for line in failures:
            sys.stderr.write(f"  {line}\n")
        sys.stderr.write(
            "  core.hooksPath is set, but at least one hook cannot run. "
            "Treat this repository as UNPROTECTED until it is fixed.\n"
        )
        return 1

    print(
        "WARNING: hook PRESENCE is not hook FIRING. This installer proved that\n"
        f"  {CONFIG_KEY} reads back as {HOOKS_DIR_NAME} and that each hook file is\n"
        "  LF, ascii and executable. It did NOT prove any hook actually runs.\n"
        "\n"
        "  The only valid proof is end to end (CONVENTIONS.md sections 1 and 16):\n"
        "    1. stage a file containing a banned character\n"
        "    2. attempt a REAL commit\n"
        "    3. assert the commit was rejected and HEAD did not move\n"
        "\n"
        "  Four ways a wired hook still does nothing: invalid JSON in a settings\n"
        "  file, an untrusted workspace, path-string keying (C:\\X and C:/x are\n"
        "  different keys), and CRLF line endings in the hook itself.\n"
    )
    return 0


def run_git_optional(args: list[str], root: Path) -> str | None:
    """`git config --get` exits 1 when the key is unset; that is not an error."""
    try:
        proc = subprocess.run(
            ["git", *args],
            capture_output=True,
            cwd=str(root),
            timeout=GIT_TIMEOUT,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise InstallError(
            "git {} failed to run: {}".format(" ".join(args), _exc_reason(exc))
        ) from exc
    if proc.returncode != 0:
        return None
    return proc.stdout.decode("utf-8", "replace").strip()


def main() -> int:
    """Entry point. Non-zero on any failure to wire the hooks."""
    here = Path(__file__).resolve().parent
    try:
        root = require_work_tree(here)
        return install(root)
    except InstallError as exc:
        sys.stderr.write(f"{TOOL_NAME}: FAILED - {_exc_reason(exc)}\n")
        sys.stderr.write("  The hooks are NOT wired. Do not treat this repository as gated.\n")
        return 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except BaseException:
        traceback.print_exc()
        sys.stderr.write(f"{TOOL_NAME}: unexpected failure; the hooks are NOT wired.\n")
        raise SystemExit(1) from None
