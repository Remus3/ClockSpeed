#!/usr/bin/env python3
"""Tests for scripts/verify_env.py - the echo paths and the core.hooksPath verdict.

TWO SUBJECTS, and the second one is at the bottom of the file. The first is the
exception-rendering echo paths, described immediately below. The second is the
core.hooksPath row: which values it reports FOUND, which it reports MISSING,
and the fact that the value it prints is redacted before it is printed. The two
share this file because they share a module and a privacy rule, not because
they are the same defect.

WHY THIS FILE EXISTS. ``str()`` on an OSError appends the filename the call
failed on - "[Errno 13] Permission denied: '<a path>'" - while ``strerror``
carries the reason alone. On this project the path involved is routinely an
absolute path under a user home directory, so it carries the Windows account
name. CLAUDE.md non-negotiable 12 counts an error message as an echo path
exactly like a debug dump or a hex preview, which makes interpolating an
exception into a message a privacy defect rather than a tidiness one.

THE ORACLE IS NOT THE REDACTOR, and that is the whole design of this file.
Asking ``redact(message) != message`` reads like a test for "the message holds
personal data" and is not one: it reports only what the redactor already
recognises, so a redactor with a blind spot certifies as clean exactly the
strings it cannot see (CONVENTIONS.md section 15.1). Instead every test here
plants its own synthetic segments into the path the failing call is given, and
asserts those segments are absent from what came back. The segments are chosen
so the redactor CANNOT be what removed them - see the deliberately non-numeric
account segment below, and the meta-test that pins that property - so the only
explanation for their absence is that the call site never rendered the path.

Both halves of every assertion are required. Without the diagnostic half,
blanking the message entirely would pass, and a reporter that says nothing
when it cannot read a file is a worse tool than the one being fixed, because
it is silent. verify_env.py exists to print a found/missing table to a human
(CONVENTIONS.md section 1), which is why pyproject.toml suppresses T201 for
scripts/ - print IS its interface.

Every test here runs on a machine with no game installed and no save
directory: nothing below resolves an install, a save root or an account
directory, and every path is built under tmp_path.
"""

from __future__ import annotations

import ast
import errno
import importlib.util
import json
import sys
from collections.abc import Callable
from pathlib import Path
from types import ModuleType

import pytest

from clockspeed.data.locate import redact

REPO_ROOT = Path(__file__).resolve().parents[1]
VERIFY_ENV_SOURCE = REPO_ROOT / "scripts" / "verify_env.py"


def _load_verify_env() -> ModuleType:
    """Load scripts/verify_env.py by path.

    scripts/ is not an importable package - it is a directory of entry-point
    scripts - so the module is loaded from its file, the same way
    tests/data/test_drift_guard_data.py loads tools/drift_guard.py. The name
    is distinct from the "verify_env" that tools/drift_guard.py binds, so the
    two loaders cannot collide inside one pytest session.

    Returns:
        The loaded module.

    Raises:
        ImportError: The script is not loadable from this checkout.
    """
    spec = importlib.util.spec_from_file_location("clockspeed_verify_env", VERIFY_ENV_SOURCE)
    if spec is None or spec.loader is None:
        message = f"could not load {VERIFY_ENV_SOURCE.name}"
        raise ImportError(message)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


verify_env = _load_verify_env()


# ---------------------------------------------------------------------------
# The planted segments - synthesized here, never read from this machine
# ---------------------------------------------------------------------------
#
# CLAUDE.md non-negotiable 3: no real account name, account id, world name or
# home path may be written into a tracked file, and that includes a test
# fixture and an assertion. Both values below are invented.
#
# THE ACCOUNT SEGMENT IS DELIBERATELY NOT A DIGIT RUN. A real platform account
# directory usually is, but redact() carries a digit-run backstop that erases
# any run of eight or more digits sitting in a path segment. Planting digits
# would therefore produce a test that passes whether the call site rendered
# the path or not - the redactor would have removed them either way - which is
# precisely the circularity this file exists to avoid. A non-numeric segment
# survives the redactor untouched, so its absence can only mean the message
# never contained it. test_the_planted_segments_survive_the_redactor pins that.

SYNTHETIC_HOME_SEGMENT = "zz-synthetic-operator-zz"
SYNTHETIC_ACCOUNT_SEGMENT = "zz-synthetic-account-dir-zz"
PLANTED_SEGMENTS = (SYNTHETIC_HOME_SEGMENT, SYNTHETIC_ACCOUNT_SEGMENT)

# Malformed on purpose, and malformed in the two distinct ways the reader can
# fail on content rather than on access.
MALFORMED_JSON = '{ "band": '
UNDECODABLE_BYTES = b"\xff\xfe\x00not utf-8"


def planted_root(tmp_path: Path) -> Path:
    """Build a checkout root sitting under a synthetic home and account dir.

    Args:
        tmp_path: The per-test temporary directory.

    Returns:
        The root to hand to load_ports, with config/ already created.
    """
    root = tmp_path / SYNTHETIC_HOME_SEGMENT / SYNTHETIC_ACCOUNT_SEGMENT / "clockspeed-clone"
    (root / "config").mkdir(parents=True)
    return root


def assert_reported_without_the_path(rendered: str, reason: str) -> None:
    """Assert a failure named its REASON and not the path it happened on.

    Args:
        rendered: Everything the call site emitted for the failure.
        reason: The reason text the operator needs in order to act, derived
            independently of the code under test.
    """
    # Both facts are reduced to a count and a boolean, and the message itself
    # is dropped, BEFORE either assertion runs. pytest reprs every local it can
    # reach in the frame of a failing assert, so holding the message would
    # print the path on the very run that proves it must not be printed - into
    # a CI log, which is an echo path like any other. The planted segments here
    # are synthetic, but the surrounding tmp_path is not.
    leaked = sum(1 for segment in PLANTED_SEGMENTS if segment in rendered)
    reason_kept = reason in rendered
    rendered = ""
    assert not leaked, (
        f"the message carried {leaked} of {len(PLANTED_SEGMENTS)} planted path segments; "
        "an exception was rendered with the filename it failed on"
    )
    assert reason_kept, (
        "the reason vanished along with the path, so the environment reporter now fails "
        "silently - see CONVENTIONS.md section 1, this script exists to tell a human what "
        "is wrong"
    )


def unreadable(self: Path, *_args: object, **_kwargs: object) -> str:
    """Raise the OSError an unreadable file raises, filename and all.

    The filename is the REAL path the call was made on, so the exception
    carries the planted segments rather than a stand-in token. ``str()`` on it
    renders as "[Errno 13] Permission denied: '<that path>'"; ``strerror``
    renders as "Permission denied".

    Args:
        self: The Path the patched read_text was called on.

    Returns:
        Never. The annotation matches the method being replaced.

    Raises:
        OSError: Always.
    """
    raise OSError(errno.EACCES, "Permission denied", str(self))


def value_error_naming_a_path(self: Path, *_args: object, **_kwargs: object) -> str:
    """Raise a plain ValueError whose message names the path.

    ValueError is in the declared catch at the ports-record site, so the
    handler has to be safe for it. No stdlib call on that path raises a bare
    ValueError today - json raises JSONDecodeError and the decoder raises
    UnicodeDecodeError, both subclasses - so this covers the handler's stated
    contract rather than an observed failure.

    Args:
        self: The Path the patched read_text was called on.

    Returns:
        Never. The annotation matches the method being replaced.

    Raises:
        ValueError: Always.
    """
    message = f"something went wrong while reading {self}"
    raise ValueError(message)


def bind_refused(_self: object, _address: object) -> None:
    """Raise the OSError a refused bind raises, filename and all.

    A bind cannot be made to fail with a non-address-in-use error by any
    filesystem arrangement that behaves the same on Windows and on the Linux
    CI runner - the privileged-port route errors only for a non-root POSIX
    process - so the failure is injected here. What is NOT injected is the
    rendering: the real probe_port builds the real socket, takes the real
    except branch and runs its real finally.

    Args:
        _self: The socket the patched bind was called on.
        _address: The address it was asked to bind.

    Raises:
        PermissionError: Always.
    """
    raise PermissionError(errno.EACCES, "Permission denied", f"/{SYNTHETIC_HOME_SEGMENT}/sock")


# ---------------------------------------------------------------------------
# Oracle integrity - the test that keeps the tests above honest
# ---------------------------------------------------------------------------


def test_the_planted_segments_survive_the_redactor() -> None:
    """The redactor must not be able to make the planted segments vanish.

    If it could, every privacy test in this file would pass on a call site
    that rendered the whole path, because the segments would have been erased
    on the way out rather than never emitted. This asserts the oracle has
    teeth. It fails loudly on a machine whose environment happens to make one
    of the planted segments redactable, which is the correct failure - a
    silently blind test is the outcome being prevented.
    """
    probe = f"/home/{SYNTHETIC_HOME_SEGMENT}/{SYNTHETIC_ACCOUNT_SEGMENT}/clone/config/ports.json"

    survived = sum(1 for segment in PLANTED_SEGMENTS if segment in redact(probe))

    assert survived == len(PLANTED_SEGMENTS), (
        "the redactor erased a planted segment, so the privacy tests in this file would "
        "pass without proving anything; pick segments the redactor does not recognise"
    )


# ---------------------------------------------------------------------------
# load_ports - one test per exception type the handler can see
# ---------------------------------------------------------------------------


def test_an_unreadable_ports_record_is_reported_without_the_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """OSError: the type whose str() appends the filename it failed on."""
    root = planted_root(tmp_path)
    (root / "config" / "ports.json").write_text("{}\n", encoding="utf-8")
    monkeypatch.setattr(Path, "read_text", unreadable)

    payload, message = verify_env.load_ports(root)

    assert payload is None, "an unreadable record must still report as unusable"
    assert_reported_without_the_path(message, "Permission denied")


def test_a_malformed_ports_record_is_reported_without_the_path(tmp_path: Path) -> None:
    """json.JSONDecodeError: a ValueError subclass, so no strerror to reach for.

    Nothing is patched here. The file is genuinely unparseable and the real
    reader genuinely fails on it. The expected reason is taken from the
    stdlib by provoking the same error, never from the code under test.
    """
    root = planted_root(tmp_path)
    (root / "config" / "ports.json").write_text(MALFORMED_JSON, encoding="utf-8")
    with pytest.raises(json.JSONDecodeError) as caught:
        json.loads(MALFORMED_JSON)

    payload, message = verify_env.load_ports(root)

    assert payload is None, "a malformed record must still report as unusable"
    assert_reported_without_the_path(message, caught.value.msg)


def test_an_undecodable_ports_record_is_reported_without_the_path(tmp_path: Path) -> None:
    """UnicodeDecodeError: also a ValueError subclass, also without strerror.

    Nothing is patched. read_text is called with encoding="utf-8" and no
    errors= argument, so the decode is strict and these bytes really do raise.
    """
    root = planted_root(tmp_path)
    (root / "config" / "ports.json").write_bytes(UNDECODABLE_BYTES)
    with pytest.raises(UnicodeDecodeError) as caught:
        UNDECODABLE_BYTES.decode("utf-8")

    payload, message = verify_env.load_ports(root)

    assert payload is None, "an undecodable record must still report as unusable"
    assert_reported_without_the_path(message, caught.value.reason)


def test_an_unexpected_value_error_falls_back_to_its_class_name(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The floor: a type with no known-safe field renders as its name alone.

    This is the fail-closed half of the contract. A helper that reached for
    strerror and fell back to str(exc) for everything else would publish this
    message whole, planted path and all - which is the leak, not the fix.
    """
    root = planted_root(tmp_path)
    (root / "config" / "ports.json").write_text("{}\n", encoding="utf-8")
    monkeypatch.setattr(Path, "read_text", value_error_naming_a_path)

    payload, message = verify_env.load_ports(root)

    assert payload is None, "an unexpected read failure must still report as unusable"
    assert_reported_without_the_path(message, "ValueError")


def test_a_readable_ports_record_still_loads(tmp_path: Path) -> None:
    """The success path is unchanged - the fix is message text only."""
    root = planted_root(tmp_path)
    (root / "config" / "ports.json").write_text('{"base": 41000}', encoding="utf-8")

    payload, message = verify_env.load_ports(root)

    assert payload == {"base": 41000}
    assert not message


# ---------------------------------------------------------------------------
# probe_port - the second site
# ---------------------------------------------------------------------------


def test_a_refused_port_bind_is_reported_without_the_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """OSError at the port probe, which rendered a BARE str(exc).

    The verdict half matters as much as the privacy half: this slice changes
    message text only, so the state string the caller branches on must still
    be ERROR. render() selects the not-free ports on state alone.
    """
    monkeypatch.setattr(verify_env.socket.socket, "bind", bind_refused)

    state, detail = verify_env.probe_port(0)

    assert state == "ERROR", "the redaction must not change which branch is taken"
    assert_reported_without_the_path(detail, "Permission denied")
    assert str(errno.EACCES) in detail, (
        "the numeric code went missing; str(exc) used to render '[Errno 13] Permission "
        "denied' and the number is diagnostic, not personal data"
    )


def test_a_free_port_still_probes_free() -> None:
    """The success path is unchanged - no verdict moved."""
    state, detail = verify_env.probe_port(0)

    assert state == "FREE"
    assert not detail


# ---------------------------------------------------------------------------
# The sweep - formatting-agnostic, so the next site cannot slip in
# ---------------------------------------------------------------------------

# Calls that may take the caught exception as an argument. _exc_reason is the
# redacting renderer; getattr and isinstance inspect without rendering.
# redact() is deliberately ABSENT: redact(exc) renders the exception first and
# strips only the needles it recognises, which is exactly the leak, so a site
# written that way must still be flagged.
SAFE_EXCEPTION_CALLS = frozenset({"_exc_reason", "getattr", "isinstance"})

# The last 7-bit printable byte. CLAUDE.md non-negotiable 4.
MAX_ASCII_BYTE = 0x7E


def rendered_exception_lines(source: str) -> list[int]:
    """Return the lines where a caught exception is used as a whole object.

    Formatting-agnostic by construction. It works on the parse tree, so an
    f-string, a percent-format, a .format() call, a bare str(exc) and an
    exception handed positionally to a message builder are all the same shape:
    a Load of the handler's name that is neither an attribute read nor an
    argument to a call known not to render.

    The original acceptance criterion for this item named only the f-string
    shape and was found defective for exactly that reason - the second site in
    this file was a bare str(exc) and a text search for "{exc}" would have
    missed it.

    SCOPE, stated honestly: this catches the exception OBJECT reaching a
    message. It does not catch someone deliberately rendering exc.filename,
    which is an attribute read and is allowed here. "raise X from exc" is
    allowed too - chaining attaches the exception, it does not render it, and
    dropping the cause to satisfy a privacy guard would lose the traceback.

    Args:
        source: The Python source to parse.

    Returns:
        The offending line numbers, ascending.
    """
    tree = ast.parse(source)
    lines: list[int] = []
    for handler in ast.walk(tree):
        if not isinstance(handler, ast.ExceptHandler) or handler.name is None:
            continue
        safe: set[int] = set()
        for node in ast.walk(handler):
            if (
                isinstance(node, ast.Attribute)
                and isinstance(node.value, ast.Name)
                and node.value.id == handler.name
            ):
                safe.add(id(node.value))
            elif (
                isinstance(node, ast.Raise)
                and isinstance(node.cause, ast.Name)
                and node.cause.id == handler.name
            ):
                safe.add(id(node.cause))
            elif (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id in SAFE_EXCEPTION_CALLS
            ):
                safe.update(
                    id(arg)
                    for arg in node.args
                    if isinstance(arg, ast.Name) and arg.id == handler.name
                )
        lines.extend(
            node.lineno
            for node in ast.walk(handler)
            if isinstance(node, ast.Name)
            and node.id == handler.name
            and isinstance(node.ctx, ast.Load)
            and id(node) not in safe
        )
    return sorted(lines)


def test_no_caught_exception_is_rendered_by_any_syntax() -> None:
    """No exception object reaches a message anywhere in the script.

    Scoped to this one file on purpose. The same defect class exists in other
    tools in this repo and each is a separate slice with its own write-list; a
    repo-wide assertion here would fail on a file this test is not allowed to
    fix, which is how a guard gets disabled.
    """
    offending = rendered_exception_lines(VERIFY_ENV_SOURCE.read_text(encoding="utf-8"))

    assert not offending, (
        f"{VERIFY_ENV_SOURCE.name} renders a caught exception into a message at line(s) "
        f"{offending}; route it through _exc_reason, which is per exception type"
    )


def test_the_sweep_detects_the_shape_it_exists_to_detect() -> None:
    """The sweep is asserted against a known-bad sample, not trusted blind.

    A guard that has only ever seen clean input is a guard nobody has proved
    fires. Each sample below is one of the formatting syntaxes the defective
    original criterion would have missed.
    """
    samples = (
        'try:\n    pass\nexcept OSError as exc:\n    x = f"boom {exc}"\n',
        "try:\n    pass\nexcept OSError as exc:\n    x = str(exc)\n",
        'try:\n    pass\nexcept OSError as exc:\n    x = "boom %s" % exc\n',
        'try:\n    pass\nexcept OSError as exc:\n    x = "boom {}".format(exc)\n',
        "try:\n    pass\nexcept OSError as exc:\n    report(exc)\n",
    )

    detected = [sample for sample in samples if rendered_exception_lines(sample)]

    sanctioned = (
        "try:\n    pass\nexcept OSError as exc:\n    x = _exc_reason(exc) + str(exc.errno)\n",
        "try:\n    pass\nexcept OSError as exc:\n    raise Boom(_exc_reason(exc)) from exc\n",
    )

    assert len(detected) == len(samples), "the sweep missed a rendering syntax"
    assert not [shape for shape in sanctioned if rendered_exception_lines(shape)], (
        "the sweep flagged a sanctioned shape, which is how a guard gets switched off"
    )


def test_this_test_module_is_seven_bit_ascii() -> None:
    """CLAUDE.md non-negotiable 4, asserted on the raw bytes of this file."""
    raw = Path(__file__).resolve().read_bytes()

    offending = [index for index, byte in enumerate(raw) if byte > MAX_ASCII_BYTE]

    assert not offending, f"{len(offending)} byte(s) above 0x{MAX_ASCII_BYTE:02X}"


# ---------------------------------------------------------------------------
# The core.hooksPath verdict - CS-207
# ---------------------------------------------------------------------------
#
# THE DEFECT. install_hooks.py writes the relative string ".githooks", and git
# hands it back ABSOLUTE - "<repo>\.githooks" - on read. The check compared
# that value against the literal ".githooks", so it reported a HARD dependency
# MISSING on a repository whose hooks demonstrably fire, and the script exited
# non-zero saying so. That is the hook-presence-is-not-hook-firing failure
# class INVERTED, and it is the more corrosive direction: a false RED on the
# one script whose job is verifying the safety net teaches the operator to
# ignore that script, and the next genuine missing dependency is ignored too.
#
# THREE HALVES, and the third is the one that is easy to lose. Absolute must be
# FOUND, relative must STILL be FOUND, and a value pointing anywhere else must
# STILL be MISSING - because a fix that normalises too eagerly, or that merely
# asks whether the string ends with ".githooks", accepts some other tree's hook
# directory and the check becomes decorative.
#
# NO SUBPROCESS, NO GIT REPOSITORY, NO GAME AND NO SAVE DIRECTORY. Every test
# below drives collect_rows() with verify_env._run replaced, so the value the
# check sees is chosen by the test rather than by whatever this machine's git
# config happens to hold - which is the only way the wrong-directory case can
# be exercised at all. The game and save resolvers are stubbed for the same
# reason every other test here builds under tmp_path: the suite must pass on a
# machine with neither.

EXPECTED_HOOKS_DIR_NAME = ".githooks"

# The row is selected by PREFIX rather than by its full label, so renaming the
# label - "==" became inaccurate the moment the absolute form was accepted -
# does not silently select nothing and pass.
HOOKS_ROW_PREFIX = "core.hooksPath"


def canned_run(
    configured: str | None, git_common_dir: str | None = None
) -> Callable[..., str | None]:
    """Answer every command verify_env shells out for, without shelling out.

    Args:
        configured: What ``git config --get core.hooksPath`` should answer.
            None is the real shape of an UNSET key - _run returns None on a
            non-zero exit.
        git_common_dir: What ``git rev-parse --git-common-dir`` should answer.

    Returns:
        A stand-in for verify_env._run.
    """

    def run(cmd: list[str], *_args: object, **_kwargs: object) -> str | None:
        if "--is-inside-work-tree" in cmd:
            return "true"
        if "--git-common-dir" in cmd:
            return git_common_dir
        if "core.hooksPath" in cmd:
            return configured
        # Every remaining call is a "--version" probe for a tool row this file
        # asserts nothing about.
        return "canned 1.0"

    return run


def hooks_row(
    root: Path,
    configured: str | None,
    monkeypatch: pytest.MonkeyPatch,
    git_common_dir: str | None = None,
) -> tuple[dict, dict]:
    """Collect the core.hooksPath row and the facts block for one scenario.

    Driven through the PUBLIC collect_rows() rather than the private row
    builder, so the tests pin the behaviour the script actually reports and
    stay free of the implementation's internal shape.

    Args:
        root: The repository root to verify.
        configured: The core.hooksPath value git should report.
        monkeypatch: The patcher, scoped to the calling test.
        git_common_dir: The git common directory, for the linked-worktree case.

    Returns:
        The single core.hooksPath row, and the facts dict collect_rows built.
    """
    monkeypatch.setattr(verify_env, "_run", canned_run(configured, git_common_dir))
    monkeypatch.setattr(verify_env, "resolve_game_dir", lambda: (None, "stubbed"))
    monkeypatch.setattr(verify_env, "resolve_save_root", lambda: None)
    monkeypatch.setattr(verify_env, "numeric_account_dirs", lambda _root: [])

    rows, _port_rows, facts = verify_env.collect_rows(root)

    matching = [entry for entry in rows if entry["name"].startswith(HOOKS_ROW_PREFIX)]
    assert len(matching) == 1, (
        f"expected exactly one row named {HOOKS_ROW_PREFIX}..., found {len(matching)}; "
        "a test that selects no row asserts nothing"
    )
    return matching[0], facts


def checkout_with_hooks(tmp_path: Path, name: str = "clone") -> Path:
    """Build a checkout root holding a populated .githooks directory.

    Args:
        tmp_path: The per-test temporary directory.
        name: The directory name, so two checkouts can coexist.

    Returns:
        The checkout root.
    """
    root = tmp_path / name
    hooks = root / EXPECTED_HOOKS_DIR_NAME
    hooks.mkdir(parents=True)
    (hooks / "pre-commit").write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    return root


def assert_redacted_before_printing(rendered: str, configured: str) -> None:
    """Assert a printed core.hooksPath was redacted and stayed diagnostic.

    Args:
        rendered: What the script would print.
        configured: The raw value it was given.
    """
    # Reduced to booleans and the strings dropped BEFORE either assertion runs,
    # for the reason stated in assert_reported_without_the_path: the planted
    # segment is synthetic but the surrounding tmp_path is not, and a failing
    # assert is an echo path into a CI log like any other.
    leaked = SYNTHETIC_HOME_SEGMENT in rendered
    diagnostic_kept = EXPECTED_HOOKS_DIR_NAME in rendered
    routed_through_redact = rendered == redact(configured)
    rendered = ""
    configured = ""
    assert not leaked, (
        "the core.hooksPath row printed the planted home segment; on a checkout under a "
        "user profile that is the Windows account name (CLAUDE.md non-negotiable 12)"
    )
    assert diagnostic_kept, (
        "the hooks directory name vanished along with the home path, so the row no longer "
        "tells the operator what was configured - a silent reporter is the worse failure"
    )
    assert routed_through_redact, (
        "the printed value is not what redact() produces for it, so the value reaches the "
        "table by some path that does not redact"
    )


def test_the_planted_home_is_redactable_once_it_is_the_home(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The mirror image of test_the_planted_segments_survive_the_redactor.

    That test pins that the redactor CANNOT remove the planted segments in the
    ambient environment, which is what lets the exception tests above prove
    their call sites never emitted them. The hooks-path row is the OPPOSITE
    requirement - the value is printed on purpose and must be redacted on the
    way out - so its privacy tests point USERPROFILE at the planted home to
    make that segment genuinely redactable. This asserts the patch works, so a
    green hooks-path privacy test is green because redact() ran rather than
    because the segment was unmatchable either way.
    """
    home = tmp_path / SYNTHETIC_HOME_SEGMENT
    home.mkdir()
    monkeypatch.setenv("USERPROFILE", str(home))

    survived = SYNTHETIC_HOME_SEGMENT in redact(str(home / "clone" / EXPECTED_HOOKS_DIR_NAME))

    assert not survived, (
        "USERPROFILE was patched to the planted home and redact() still left the segment "
        "standing, so the hooks-path privacy tests below would prove nothing"
    )


def test_a_hooks_path_in_another_directory_is_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The half that is easy to lose: some other tree's .githooks is NOT ours.

    The planted directory is named ".githooks" and really exists, so a fix that
    compares the trailing segment, or that asks whether the configured string
    ends with ".githooks", reports FOUND here and the whole check becomes
    decorative.
    """
    root = checkout_with_hooks(tmp_path)
    elsewhere = tmp_path / "some-other-tree" / EXPECTED_HOOKS_DIR_NAME
    elsewhere.mkdir(parents=True)

    row, _facts = hooks_row(root, str(elsewhere), monkeypatch)

    assert row["status"] == "MISSING", (
        "a .githooks directory belonging to an unrelated tree was accepted; the hooks that "
        "would run are not this repository's, so the safety net is not wired"
    )


def test_an_absolute_hooks_path_at_the_repo_is_found(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The reproduced defect: the shape a real repository actually has."""
    root = checkout_with_hooks(tmp_path)

    row, _facts = hooks_row(root, str(root / EXPECTED_HOOKS_DIR_NAME), monkeypatch)

    assert row["status"] == "FOUND", (
        "core.hooksPath in ABSOLUTE form was reported MISSING on a correctly wired "
        "checkout; install_hooks.py writes the relative string and git reads it back "
        "absolute, so this is the value the check will meet on every real repository"
    )


def test_a_relative_hooks_path_is_still_found(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The relative form must not be traded away for the absolute one."""
    root = checkout_with_hooks(tmp_path)

    row, _facts = hooks_row(root, EXPECTED_HOOKS_DIR_NAME, monkeypatch)

    assert row["status"] == "FOUND", (
        "the relative form stopped being accepted; it is what install_hooks.py writes and "
        "what a fresh clone will hold"
    )


def test_an_absolute_hooks_path_with_forward_slashes_is_found(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Separator style is not a verdict. Windows git reports either."""
    root = checkout_with_hooks(tmp_path)
    configured = str(root / EXPECTED_HOOKS_DIR_NAME).replace("\\", "/")

    row, _facts = hooks_row(root, configured, monkeypatch)

    assert row["status"] == "FOUND", "the separator style changed the verdict"


def test_an_absolute_hooks_path_with_a_trailing_separator_is_found(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A trailing separator names the same directory."""
    root = checkout_with_hooks(tmp_path)
    configured = str(root / EXPECTED_HOOKS_DIR_NAME) + "/"

    row, _facts = hooks_row(root, configured, monkeypatch)

    assert row["status"] == "FOUND", "a trailing separator changed the verdict"


@pytest.mark.skipif(sys.platform != "win32", reason="drive letters exist only on Windows")
def test_an_absolute_hooks_path_with_a_swapped_drive_case_is_found(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Drive-letter case is not a verdict on Windows.

    Windows-only on purpose. A case-sensitive filesystem has no drive letter
    and two paths differing in case there are genuinely two directories, which
    is exactly why the comparison must fold case through the platform's own
    mechanism instead of a hand-rolled lowercase.
    """
    root = checkout_with_hooks(tmp_path)
    configured = str(root / EXPECTED_HOOKS_DIR_NAME)
    swapped = configured[0].swapcase() + configured[1:]

    row, _facts = hooks_row(root, swapped, monkeypatch)

    assert row["status"] == "FOUND", (
        "the drive-letter case changed the verdict; git and the shell both render it "
        "either way and they name one directory"
    )


def test_a_hooks_path_that_does_not_exist_is_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Identity is not enough - the directory has to be there.

    The configured value is exactly the path the check expects, and nothing is
    at it. Path.resolve() is non-strict and returns the right string anyway, so
    a fix that compares resolved paths WITHOUT an existence check reports FOUND
    for hooks that cannot possibly run.
    """
    root = tmp_path / "clone"
    root.mkdir()

    row, _facts = hooks_row(root, str(root / EXPECTED_HOOKS_DIR_NAME), monkeypatch)

    assert row["status"] == "MISSING", (
        "a hooks path that resolves correctly but does not exist was reported FOUND; "
        "resolve() is lexical for a missing path, so identity alone proves nothing"
    )


def test_a_hooks_path_naming_a_file_is_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A FILE at the hooks path runs no hooks, so exists() is not the check."""
    root = tmp_path / "clone"
    root.mkdir()
    (root / EXPECTED_HOOKS_DIR_NAME).write_text("not a directory\n", encoding="utf-8")

    row, _facts = hooks_row(root, str(root / EXPECTED_HOOKS_DIR_NAME), monkeypatch)

    assert row["status"] == "MISSING", (
        "a regular file at the hooks path was accepted; git needs a DIRECTORY of hook "
        "scripts, so the check is is_dir() and not exists()"
    )


def test_an_unset_hooks_path_is_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The fresh-clone state: the key is not set and nothing protects the clone."""
    root = checkout_with_hooks(tmp_path)

    row, facts = hooks_row(root, None, monkeypatch)

    assert row["status"] == "MISSING", "an unset core.hooksPath is the unprotected state"
    assert row["value"] == "unset", "an unset key must still say so in the table"
    assert facts["hooks_path"] == "", "an unset key must not invent a value in the JSON"


def test_a_blank_hooks_path_is_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Whitespace is not a path, and must not anchor to the repository root."""
    root = checkout_with_hooks(tmp_path)

    row, _facts = hooks_row(root, "   ", monkeypatch)

    assert row["status"] == "MISSING", (
        "a whitespace core.hooksPath was accepted; anchoring an empty relative path at the "
        "root resolves to the root itself, which holds no hooks"
    )


def test_a_linked_worktree_accepts_the_main_checkout_hooks_dir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """core.hooksPath is SHARED config, so a worktree reads the main value.

    Every slice in this project runs in a linked worktree, and git config is
    common across them - so a worktree reads the absolute path that was set for
    the main checkout, and git runs THOSE hooks rather than the worktree's own
    checked-out copy. Comparing only against the worktree's own .githooks would
    move the false RED rather than remove it.
    """
    main = checkout_with_hooks(tmp_path, "main-checkout")
    worktree = checkout_with_hooks(tmp_path, "linked-worktree")

    row, _facts = hooks_row(
        worktree,
        str(main / EXPECTED_HOOKS_DIR_NAME),
        monkeypatch,
        git_common_dir=str(main / ".git"),
    )

    assert row["status"] == "FOUND", (
        "a linked worktree reported the shared core.hooksPath MISSING; the hooks it names "
        "are the ones git actually runs for a commit made in that worktree"
    )


def test_a_linked_worktree_still_rejects_an_unrelated_hooks_dir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Accepting the main checkout must not widen into accepting anything."""
    main = checkout_with_hooks(tmp_path, "main-checkout")
    worktree = checkout_with_hooks(tmp_path, "linked-worktree")
    elsewhere = tmp_path / "some-other-tree" / EXPECTED_HOOKS_DIR_NAME
    elsewhere.mkdir(parents=True)

    row, _facts = hooks_row(
        worktree,
        str(elsewhere),
        monkeypatch,
        git_common_dir=str(main / ".git"),
    )

    assert row["status"] == "MISSING", (
        "the worktree allowance widened into accepting an unrelated .githooks directory"
    )


def test_a_missing_hooks_path_row_does_not_print_a_home_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The MISSING row prints the configured value, so it must be redacted.

    Harmless while the checkout sits at a drive root, and a home-path leak on
    any checkout under a user profile - which is where the value carries the
    Windows account name. CLAUDE.md non-negotiable 12 counts a printed table as
    an echo path exactly like a debug dump.
    """
    home = tmp_path / SYNTHETIC_HOME_SEGMENT
    configured_dir = home / "someones-clone" / EXPECTED_HOOKS_DIR_NAME
    configured_dir.mkdir(parents=True)
    monkeypatch.setenv("USERPROFILE", str(home))
    root = checkout_with_hooks(tmp_path)

    row, _facts = hooks_row(root, str(configured_dir), monkeypatch)

    assert row["status"] == "MISSING", "the planted directory is not this repository's"
    assert_redacted_before_printing(row["value"], str(configured_dir))


def test_the_hooks_path_fact_does_not_carry_a_home_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """--json is the second echo path, and it publishes the facts block.

    Asserted separately from the table row because they are two renderings. A
    fix applied only where the table is built leaves the machine-readable
    output - the one most likely to be pasted into an issue - carrying the
    home path.
    """
    home = tmp_path / SYNTHETIC_HOME_SEGMENT
    configured_dir = home / "someones-clone" / EXPECTED_HOOKS_DIR_NAME
    configured_dir.mkdir(parents=True)
    monkeypatch.setenv("USERPROFILE", str(home))
    root = checkout_with_hooks(tmp_path)

    _row, facts = hooks_row(root, str(configured_dir), monkeypatch)

    assert_redacted_before_printing(facts["hooks_path"], str(configured_dir))


def test_a_found_hooks_path_row_still_names_the_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Redaction must not blank the value on the passing path either.

    A row that reports FOUND and shows nothing is how an operator loses the
    ability to tell a correctly wired repository from a mis-wired one.
    """
    root = checkout_with_hooks(tmp_path)

    row, facts = hooks_row(root, str(root / EXPECTED_HOOKS_DIR_NAME), monkeypatch)

    assert EXPECTED_HOOKS_DIR_NAME in row["value"], "the FOUND row stopped naming anything"
    assert EXPECTED_HOOKS_DIR_NAME in facts["hooks_path"], "the JSON fact was blanked"


# --- the toolchain rows: importable by the RESOLVED interpreter -------------
#
# THE THIRD SUBJECT IN THIS FILE. BOOTSTRAP.md section 2.5 measured four Python
# installations on this machine and recorded that the launcher and the plain
# name both report the same version while only one of them can import ruff. It
# draws one MANDATORY consequence for this script: assert that the RESOLVED
# interpreter can import pytest and ruff, and HARD-fail if it cannot, because
# "reporting the version alone is not sufficient and would have passed this
# machine while the pre-push suite was unrunnable".
#
# THE FAILURE DIRECTION IS THE DANGEROUS ONE, which is why a version row is not
# enough on its own. A PATH probe answers FOUND out of a Scripts directory
# belonging to a DIFFERENT interpreter than the one that will run the check, so
# the table certifies a toolchain the session cannot actually invoke - and an
# unrunnable check reads as a passed check. That is CS-806.
#
# THE ROWS ARE DRIVEN THROUGH THE PUBLIC collect_rows(), for the reason the
# hooks helper above states: these tests pin what the script REPORTS, not the
# shape of the private builder that happens to produce it today.

# The tools probed as PYTHON MODULES. node and gh are genuine executables and
# are deliberately NOT here - see the exclusion test at the end of this block.
MODULE_BACKED_TOOLS = ("pytest", "ruff", "mypy")

# The two the BOOTSTRAP consequence names by hand, and the two that are HARD.
HARD_MODULE_BACKED_TOOLS = ("pytest", "ruff")


def toolchain_run(importable: set[str]) -> Callable[..., str | None]:
    """Answer every probe, with the module channel and the PATH channel SPLIT.

    This is the CS-806 machine in miniature: a version run against an
    executable on PATH succeeds, while the same tool run as a module under the
    RESOLVED interpreter fails exactly when it is not importable there.

    Args:
        importable: The tools the resolved interpreter can import. A tool
            outside this set answers None to the module probe, which is the
            real shape of a missing module - _run returns None on a non-zero
            exit, and the module probe exits 1 saying there is no such module.

    Returns:
        A stand-in for verify_env._run.
    """

    def run(cmd: list[str], *_args: object, **_kwargs: object) -> str | None:
        if "--is-inside-work-tree" in cmd:
            return "true"
        if "--git-common-dir" in cmd or "core.hooksPath" in cmd:
            return None
        # The module probe is [sys.executable, "-m", <name>, "--version"].
        if cmd[:2] == [sys.executable, "-m"]:
            return "canned 1.0" if cmd[2] in importable else None
        # Every remaining call is a PATH executable answering --version, and it
        # answers SUCCESSFULLY - that is the whole point of the scenario.
        return "canned 1.0"

    return run


def toolchain_which(present: set[str], root: Path) -> Callable[..., str | None]:
    """Stand in for shutil.which, planting each present tool under tmp_path.

    Args:
        present: The tools that have an executable on PATH.
        root: The directory the planted executables are reported in.

    Returns:
        A stand-in for shutil.which.
    """

    def which(name: str, *_args: object, **_kwargs: object) -> str | None:
        return str(root / f"{name}-stub") if name in present else None

    return which


def toolchain_rows(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    importable: set[str],
    present: set[str] | None = None,
    checkout_name: str = "clone",
) -> dict[str, dict]:
    """Collect the dependency rows for one toolchain scenario, keyed by name.

    Args:
        tmp_path: The per-test temporary directory.
        monkeypatch: The patcher, scoped to the calling test.
        importable: Tools the resolved interpreter can import.
        present: Tools with an executable on PATH. Defaults to every tool this
            file names plus git, which is the CS-806 shape - present on PATH
            and not necessarily importable.
        checkout_name: The checkout directory name. A test comparing TWO
            scenarios needs a distinct root for each, because tmp_path is
            shared within a single test.

    Returns:
        Every dependency row, keyed by its name.
    """
    if present is None:
        present = {"git", "node", "gh", *MODULE_BACKED_TOOLS}
    root = checkout_with_hooks(tmp_path, checkout_name)

    monkeypatch.setattr(verify_env, "_run", toolchain_run(importable))
    monkeypatch.setattr(verify_env.shutil, "which", toolchain_which(present, root))
    monkeypatch.setattr(verify_env, "resolve_game_dir", lambda: (None, "stubbed"))
    monkeypatch.setattr(verify_env, "resolve_save_root", lambda: None)
    monkeypatch.setattr(verify_env, "numeric_account_dirs", lambda _root: [])

    rows, _port_rows, _facts = verify_env.collect_rows(root)

    by_name = {entry["name"]: entry for entry in rows}
    for name in MODULE_BACKED_TOOLS:
        assert name in by_name, f"no row named {name}; a test selecting no row asserts nothing"
    return by_name


def test_a_tool_the_resolved_interpreter_cannot_import_is_reported_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """THE CS-806 CONTROL. On PATH, answering its version, and still unusable.

    This is the exact divergence measured on this machine: the executable is
    real and runs, and the interpreter that will actually run the gate cannot
    import it. Before the fix this row read FOUND, which is how a session
    concludes the tier-0 lint gate passed when it never ran.
    """
    rows = toolchain_rows(tmp_path, monkeypatch, importable=set())

    for name in HARD_MODULE_BACKED_TOOLS:
        assert rows[name]["ok"] is False, (
            f"{name} reported FOUND while the resolved interpreter cannot import it - "
            "that is the unrunnable-check-is-not-a-passed-check defect"
        )
        assert rows[name]["scope"] == "HARD", f"{name} stopped being a HARD dependency"


def test_a_tool_the_resolved_interpreter_can_import_is_still_found(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The positive control, without which the rule above could just say no.

    An implementation that reported MISSING unconditionally would satisfy the
    divergence test and be useless. This pins the other side of the branch.
    """
    rows = toolchain_rows(tmp_path, monkeypatch, importable=set(MODULE_BACKED_TOOLS))

    for name in MODULE_BACKED_TOOLS:
        assert rows[name]["ok"] is True, (
            f"{name} reported MISSING while the resolved interpreter CAN import it"
        )
        assert rows[name]["value"], f"{name} reported FOUND and showed nothing"


def test_the_divergent_row_reads_differently_from_a_tool_that_is_simply_absent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """MISSING is not one state, and collapsing the two wastes the finding.

    "Install ruff" and "you are running the wrong interpreter" need different
    actions from the operator. The assertion compares two COMPUTED renderings
    rather than matching a literal sentence, so rewording the note does not
    redden it - only collapsing the distinction does.
    """
    diverged = toolchain_rows(
        tmp_path, monkeypatch, importable=set(), present={"git", "ruff"}, checkout_name="diverged"
    )
    absent = toolchain_rows(
        tmp_path, monkeypatch, importable=set(), present={"git"}, checkout_name="absent"
    )

    diverged_row = diverged["ruff"]
    absent_row = absent["ruff"]

    assert diverged_row["ok"] is False, "the divergent case must be MISSING"
    assert absent_row["ok"] is False, "the absent case must be MISSING"
    assert diverged_row["note"] != absent_row["note"], (
        "a tool on PATH but unimportable renders identically to one that is simply "
        "absent, so the table cannot tell the operator which one they have"
    )
    assert "interpreter" in diverged_row["note"].lower(), (
        "the divergent row does not mention the interpreter, which is the one fact "
        "that makes it actionable"
    )


def test_the_soft_module_backed_tool_follows_the_same_interpreter_rule(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Mypy is the SIBLING CASE, and it shares the root cause exactly.

    It is SOFT, so it cannot fail the run - but the tier-2 gate invokes it as a
    module, so a row certifying a mypy this interpreter cannot import misreports
    the same way ruff did. Fixed alongside pytest and ruff rather than left as a
    known-identical defect.
    """
    rows = toolchain_rows(tmp_path, monkeypatch, importable={"pytest", "ruff"})

    assert rows["mypy"]["ok"] is False, (
        "mypy reported FOUND while the resolved interpreter cannot import it"
    )


def test_a_genuine_path_executable_is_still_judged_by_the_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """THE DELIBERATE EXCLUSION, pinned so it cannot be widened by accident.

    node and gh are not python modules and never will be. Applying the module
    rule to them would report MISSING for a perfectly working install, which is
    the opposite error and just as misleading.
    """
    rows = toolchain_rows(tmp_path, monkeypatch, importable=set())

    for name in ("node", "gh"):
        assert rows[name]["ok"] is True, (
            f"{name} is a PATH executable and was judged by the module channel"
        )
