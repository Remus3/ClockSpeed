#!/usr/bin/env python3
"""Tests for scripts/verify_env.py - the exception-rendering echo paths.

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
