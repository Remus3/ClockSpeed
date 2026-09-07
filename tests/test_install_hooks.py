"""CS-925 - `scripts/install_hooks.py::set_executable`, graded by the MODE ON DISK.

WHAT WAS UNGRADED. `set_executable` is the only thing that repairs a hook's POSIX
executable bit in a fresh clone, and before this module `git grep set_executable --
tests/` returned zero hits: no test named the function and no test module covered that
script at all. Git silently declines to run a hook that is not executable and reports
NOTHING when it declines, so a clone whose exec bit never landed reports itself wired
and gates nothing - the failure mode is a green tick over an absent gate.

THE ASSERTION IS THE RESULTING MODE AND NEVER THE CALL, and that distinction is the
whole reason this item exists. CS-605 closed on `scripts/make_cert.py` chmodding a key
to 0600 with nothing reading the result back, and `docs/LEDGER.md` records under CS-923
that no CI run could ever have revealed it because there was nothing to fail. Every arm
below reads the mode back off disk with `Path.stat()` AFTER the call and asserts the
integer it got. Mocking `os.chmod` and inspecting its arguments would reproduce the
CS-605 defect exactly, in a new file, wearing a later date.

THE POSIX BRANCH IS FORCED RATHER THAN WAITED FOR. `set_executable` returns early on
`os.name == "nt"` without touching the file, so on the operator's Windows machine the
branch under test never runs. The arms below rebind `install_hooks.os` to a stand-in
reporting the platform name they want, so which branch executes is decided by the arm
and not by whichever runner happened to collect it.

THE PATCH IS ON `install_hooks.os` AND NOT ON `os.name`, which is what keeps it
surgical - the same argument `tests/test_make_cert.py` makes for patching `Path.chmod`
rather than `os.chmod`. Rebinding the real `os` module's attribute would put the whole
interpreter under the fault for the duration, pathlib, tempfile and pytest's own
machinery included. Rebinding the name in this one module's globals reaches exactly the
lookup under test. The stand-in carries `name` and nothing else on purpose: if
`set_executable` ever grows a second `os.*` call these arms raise AttributeError
loudly, rather than passing quietly over a call they were not written to cover.

WHAT IS MEASURED HERE AND WHAT IS NOT, stated plainly, because an unexplained skip is a
mute button the defect gets to press.

  On POSIX the mode bits are real, the two exec-bit arms RUN, and the integer read back
  off disk is the whole of what they assert. `.github/workflows/tier1.yml` runs
  `python -m pytest tests --ignore=tests/save` on `ubuntu-latest` and this module is not
  under `tests/save`, so it is graded there on every push; `tier2.yml` runs the full
  suite on an os matrix carrying `ubuntu-latest` as well.

  On Windows the filesystem has no POSIX exec bit to set. `os.chmod` honours only the
  write bit there, so a chmod to 0o755 reads back as 0o666 and a green result would be a
  statement about nothing. The two exec-bit arms SKIP, and the property they grade is
  UNMEASURED on Windows rather than absent.

THE SKIP IS GATED ON A MEASURED CAPABILITY AND NEVER ON THE CODE UNDER TEST.
:func:`_exec_bits_are_honoured` writes its own throwaway file, chmods it through pathlib
directly and reads the mode back. It never calls `set_executable`, so no defect in the
function under test can reach the gate that decides whether the function is graded. It
is a measurement rather than an `os.name` comparison for the reason
`tests/test_make_cert.py` already gives: a platform name freezes today's answer into the
suite as though it were permanent, and would then be wrong in both directions the moment
either platform moved.

TWO ARMS RUN ON EVERY PLATFORM, so the operator's machine is not left grading nothing.
The nt-branch arm counts chmod attempts rather than comparing modes, because on Windows
"the mode is unchanged" is vacuous - a chmod that changes nothing and a branch that
never chmods produce the same mode read back, and only the counter tells them apart. The
refusal arm FORCES the OSError instead of waiting for a platform to produce one, and
pins the contract that makes `install()`'s CHMOD row reachable at all.

NO PATH IS EVER THE SUBJECT OF AN ASSERTION. pytest renders the asserted EXPRESSION
independently of the message, and a `tmp_path` on Windows carries both a home path and
the account name (CLAUDE.md non-negotiable 3). Every assertion below binds an int, a str
or a count first and asserts on that scalar.
"""

from __future__ import annotations

import errno
import importlib.util
import stat
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
INSTALLER_SOURCE = REPO_ROOT / "scripts" / "install_hooks.py"

#: Permission bits only - `st_mode` also carries the file-type bits, and an unmasked
#: comparison would be a comparison against 0o100755 rather than against a mode.
MODE_MASK = 0o777

#: The state `set_executable` exists to repair: readable and writable, executable by
#: nobody. A hook authored on Windows and added with `git add` arrives this way.
NON_EXECUTABLE_MODE = 0o644

#: The state it must produce - `NON_EXECUTABLE_MODE` with the three exec bits ORed in.
#: Written as the resulting mode rather than as an expression so the arms compare
#: against a value a reader can check by eye against `ls -l`.
EXECUTABLE_MODE = 0o755

#: The three bits the function ORs in, named from `stat` rather than as 0o111 so this
#: constant and the implementation cannot drift apart silently.
EXEC_BITS = stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH

#: The two strings `set_executable` returns. They are literals inside the function
#: rather than module constants there, so they are pinned here by value: `install()`
#: prints whichever one it got into the "exec bit" column of its report, which makes
#: them part of the operator-visible contract and not an implementation detail.
POSIX_REPORT = "executable"
WINDOWS_REPORT = "n/a on windows"

#: Why the exec-bit arms decline to grade on a filesystem that cannot express the bit.
#: Rendered by `-ra`, which `pyproject.toml` pins in `addopts`, so this text reaches the
#: operator on every run rather than blending into the dots.
SKIP_REASON = (
    "this filesystem did not read back a chmod it had just been given, so the exec bit "
    "set_executable sets cannot be observed here and a green result would be a "
    "statement about nothing. The bit is UNMEASURED on this platform, not absent - CI "
    "runs this module on ubuntu-latest, where it is measured"
)


def _load_script(source: Path, bound_name: str) -> ModuleType:
    """Load an entry-point script from `scripts/` by path.

    `scripts/` is a directory of entry-point scripts rather than an importable package,
    so the module is loaded from its file - the same way `tests/test_make_cert.py` and
    `tests/test_verify_env.py` load theirs. The bound name is distinct from the one that
    module uses, so two loaders cannot collide inside a single pytest session.

    Args:
        source: The script file.
        bound_name: The key to bind it under in `sys.modules`.

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


install_hooks = _load_script(INSTALLER_SOURCE, "clockspeed_install_hooks_cs925")


def _os_reporting(platform_name: str) -> SimpleNamespace:
    """A stand-in for the `os` module that reports exactly one platform name.

    Carries `name` and NOTHING ELSE, deliberately. `set_executable` reads `os.name` and
    reaches for nothing further, so a stand-in that proxied every attribute would let a
    future second `os.*` call pass unnoticed under these arms. This one raises
    AttributeError instead, which reddens loudly and names the new call.

    Args:
        platform_name: What `os.name` should report - "posix" or "nt".

    Returns:
        An object exposing that single attribute.
    """
    return SimpleNamespace(name=platform_name)


def _exec_bits_are_honoured(probe_dir: Path) -> bool:
    """Ask this filesystem, by measurement, whether the exec bits round-trip.

    THE CAPABILITY IS PROVEN RATHER THAN INFERRED FROM A PLATFORM NAME - see the module
    docstring. BOTH modes the arms depend on are exercised, not just one: a gate that
    proved only that 0o755 sticks would still be trusted by an arm whose precondition is
    that 0o644 sticks first.

    THE CODE UNDER TEST IS NOT ON THIS PATH. `set_executable` is never called here, so
    the function being graded cannot influence the decision to grade it.

    Args:
        probe_dir: A directory to write the throwaway file into. Normally a `tmp_path`,
            so the probe never touches the repository.

    Returns:
        True when both modes asked for are the modes read back.
    """
    probe = probe_dir / "cs925-mode-probe"
    probe.write_bytes(b"")
    try:
        probe.chmod(NON_EXECUTABLE_MODE)
        cleared = (probe.stat().st_mode & MODE_MASK) == NON_EXECUTABLE_MODE
        probe.chmod(EXECUTABLE_MODE)
        honoured = (probe.stat().st_mode & MODE_MASK) == EXECUTABLE_MODE
    except OSError:
        cleared = False
        honoured = False
    finally:
        probe.unlink(missing_ok=True)
    return cleared and honoured


def _write_non_executable(directory: Path, name: str) -> Path:
    """Write a hook-shaped file and clear its executable bits.

    BYTES RATHER THAN TEXT, because `write_text` converts LF to CRLF on Windows while
    `read_text` hides it (CONVENTIONS.md section 16), and a hook's line endings are
    exactly what `inspect_hook` rejects a file for.

    Args:
        directory: Where to write it. Normally a `tmp_path`.
        name: The hook's file name.

    Returns:
        The path written.
    """
    path = directory / name
    path.write_bytes(b"#!/bin/sh\nexit 0\n")
    path.chmod(NON_EXECUTABLE_MODE)
    return path


def test_set_executable_lands_all_three_exec_bits_on_disk(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """THE ACCEPTANCE ARM for CS-925: the POSIX branch forced, the mode read back.

    The subject is written non-executable and that starting state is ASSERTED before the
    call, because a file that arrived already executable would let this arm pass green
    while `set_executable` did nothing at all - the precondition is what stops the arm
    grading the filesystem's defaults instead of the function.

    The mode is then read off disk and compared as an int. Three separate claims, and
    each fails for its own reason: the exec bits landed, the bits already there survived
    the OR, and the string `install()` prints is the one the contract names.

    UNMEASURED ON WINDOWS, measured on POSIX CI - see the module docstring and
    :data:`SKIP_REASON`.
    """
    if not _exec_bits_are_honoured(tmp_path):
        pytest.skip(SKIP_REASON)

    hook = _write_non_executable(tmp_path, "pre-commit")

    before = hook.stat().st_mode & MODE_MASK
    assert before == NON_EXECUTABLE_MODE, (
        f"the subject started at 0o{before:03o}, not 0o{NON_EXECUTABLE_MODE:03o}. An "
        "already-executable subject would let this arm pass without set_executable "
        "having done anything, which is the defect it exists to catch."
    )

    monkeypatch.setattr(install_hooks, "os", _os_reporting("posix"))
    report = install_hooks.set_executable(hook)

    after = hook.stat().st_mode & MODE_MASK
    gained = after & EXEC_BITS

    assert gained == EXEC_BITS, (
        f"the mode on disk is 0o{after:03o}, whose exec bits are 0o{gained:03o}; "
        f"expected all of 0o{EXEC_BITS:03o}. Git declines to run a non-executable hook "
        "on POSIX and reports nothing when it declines, so the gate is absent rather "
        "than failing."
    )
    assert after == EXECUTABLE_MODE, (
        f"the mode on disk is 0o{after:03o}, expected 0o{EXECUTABLE_MODE:03o}. "
        "set_executable ORs the exec bits in, so every read and write bit it found must "
        "survive the call."
    )
    assert report == POSIX_REPORT, (
        f"the POSIX branch reported {report!r}, expected {POSIX_REPORT!r}. install() "
        "prints that string in its exec-bit column, so it is operator-visible contract."
    )


def test_set_executable_is_idempotent_in_both_the_mode_and_the_report(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A second run changes nothing and says the same thing.

    `set_executable`'s own docstring promises it "reports the RESULTING state, not the
    transition, so a second run prints byte-identical output to the first". Two halves
    of that go ungraded by every other arm: that the report repeats, and that the
    `if mode != wanted` guard actually SUPPRESSES the second chmod rather than making a
    redundant syscall that happens to be harmless.

    The second call's chmods are COUNTED rather than inferred from the mode, because a
    redundant chmod to the mode already on disk is invisible in a mode comparison.

    UNMEASURED ON WINDOWS, measured on POSIX CI - see :data:`SKIP_REASON`.
    """
    if not _exec_bits_are_honoured(tmp_path):
        pytest.skip(SKIP_REASON)

    hook = _write_non_executable(tmp_path, "commit-msg")
    monkeypatch.setattr(install_hooks, "os", _os_reporting("posix"))

    first_report = install_hooks.set_executable(hook)
    first_mode = hook.stat().st_mode & MODE_MASK

    second_call_modes: list[int] = []

    def record_chmod(_self: Path, mode: int, **_kwargs: object) -> None:
        second_call_modes.append(mode)

    monkeypatch.setattr(Path, "chmod", record_chmod)
    second_report = install_hooks.set_executable(hook)

    second_mode = hook.stat().st_mode & MODE_MASK
    second_chmods = len(second_call_modes)

    assert first_mode == EXECUTABLE_MODE, (
        f"the first run left 0o{first_mode:03o}, expected 0o{EXECUTABLE_MODE:03o}; "
        "there is no idempotence to grade until the first run is right."
    )
    assert second_mode == first_mode, (
        f"the second run moved the mode from 0o{first_mode:03o} to 0o{second_mode:03o}."
    )
    assert second_chmods == 0, (
        f"the second run issued {second_chmods} chmod(s) on a file already at the "
        "wanted mode; the `if mode != wanted` guard is not suppressing the redundant "
        "call it exists to suppress."
    )
    assert second_report == first_report, (
        f"the second run reported {second_report!r} after the first reported "
        f"{first_report!r}; the two runs must print byte-identical output."
    )


def test_set_executable_reports_not_applicable_on_windows_without_touching_the_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The nt branch reports the bit as not applicable rather than faking it.

    RUNS ON EVERY PLATFORM, because the branch is forced rather than waited for. This is
    the half that gives the operator's Windows machine real coverage of this function.

    THE CHMOD ATTEMPTS ARE COUNTED, NOT INFERRED FROM THE MODE, and that is what makes
    the arm non-vacuous on Windows. `os.chmod` there honours only the write bit, so a
    branch that faked the exec bit and a branch that never chmodded at all read back the
    SAME mode - "unchanged" proves nothing. The counter tells them apart on every
    platform. The mode comparison is kept as the second, weaker half: it is a real
    measurement on POSIX and a vacuous one on Windows, and is asserted last so the
    counter is what a failure names first.
    """
    hook = _write_non_executable(tmp_path, "pre-push")
    before = hook.stat().st_mode & MODE_MASK

    attempts: list[int] = []

    def record_chmod(_self: Path, mode: int, **_kwargs: object) -> None:
        attempts.append(mode)

    monkeypatch.setattr(Path, "chmod", record_chmod)
    monkeypatch.setattr(install_hooks, "os", _os_reporting("nt"))

    report = install_hooks.set_executable(hook)

    chmod_calls = len(attempts)
    after = hook.stat().st_mode & MODE_MASK

    assert chmod_calls == 0, (
        f"the nt branch attempted {chmod_calls} chmod(s). Git for Windows masks X_OK, "
        "so a bit set there is a repair that cannot be verified and must not be "
        "claimed; the branch reports it as not applicable instead."
    )
    assert report == WINDOWS_REPORT, (
        f"the nt branch reported {report!r}, expected {WINDOWS_REPORT!r}. install() "
        "prints that string in its exec-bit column."
    )
    assert after == before, (
        f"the mode moved from 0o{before:03o} to 0o{after:03o} on the nt branch. This "
        "half is a real measurement on POSIX and a vacuous one on Windows, where the "
        "chmod counter above is the whole of what grades the claim."
    )


def test_set_executable_lets_a_refused_chmod_reach_the_caller(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A chmod the platform refuses propagates, and is not swallowed.

    RUNS ON EVERY PLATFORM, because the OSError is FORCED rather than waited for - the
    shape `tests/test_make_cert.py` uses for the failure half of its own chmod promise.

    THIS IS WHAT MAKES install()'s CHMOD ROW REACHABLE. That caller wraps the call in
    `except OSError` and turns the failure into a CHMOD status with a redacted reason,
    which reports the repository UNPROTECTED. If `set_executable` ever swallowed the
    error and returned "executable", the caller would print a green exec-bit column over
    a hook that git will not run, and that row would become dead code no arm reaches.

    THE FORCED ERROR CARRIES NO FILENAME. An OSError built with the offending path would
    put a `tmp_path` into an exception a later report could render, so the errno and the
    strerror are given and the filename is not.
    """
    hook = _write_non_executable(tmp_path, "pre-commit")

    starting_exec_bits = hook.stat().st_mode & EXEC_BITS
    assert starting_exec_bits == 0, (
        f"the subject already carries exec bits 0o{starting_exec_bits:03o}, so "
        "set_executable would find the wanted mode already in place and never reach the "
        "chmod this arm is about."
    )

    def refuse_chmod(_self: Path, _mode: int, **_kwargs: object) -> None:
        raise PermissionError(errno.EPERM, "operation not permitted")

    monkeypatch.setattr(Path, "chmod", refuse_chmod)
    monkeypatch.setattr(install_hooks, "os", _os_reporting("posix"))

    with pytest.raises(OSError, match="operation not permitted") as caught:
        install_hooks.set_executable(hook)

    reported_errno = caught.value.errno
    assert reported_errno == errno.EPERM, (
        f"the escaping error carried errno {reported_errno}, expected {errno.EPERM}. "
        "install() renders that reason into its CHMOD row, so it must survive the call."
    )
