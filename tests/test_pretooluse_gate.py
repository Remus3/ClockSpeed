#!/usr/bin/env python3
"""Tests for tools/pretooluse_gate.py - the PreToolUse hook wrapper (CS-425).

WHY THIS FILE EXISTS. The `PreToolUse` hook was wired as
`python tools/precommit_gate.py --text-stdin` and did nothing at all, for two
independent reasons, both re-measured against this tree before a line of the
wrapper was written:

  1. It CANNOT DENY. Claude Code denies a tool call on exit code 2. The gate
     exits 1 on a violation, which is surfaced and non-blocking.
  2. It CANNOT SEE. A hook receives a JSON envelope on stdin, and a JSON
     emitter escapes a non-ASCII character to a backslash-u sequence that is
     itself pure ASCII. Fed that envelope the gate returns rc=0 PASS - the
     scan is looking at transport encoding, not at the command.

The wrapper parses the envelope and exits 2. Every test here drives it as a
SUBPROCESS over real stdin, because the exit code is the entire contract: an
in-process return value would test something adjacent to what the harness
relies on.

THE TWO HALVES OF THE CONTRACT ARE TESTED SEPARATELY AND MUST NOT BE CONFUSED:

  FAIL CLOSED on a real violation  -> exit 2, the call is denied.
  FAIL OPEN on the wrapper's own   -> exit 0, the call proceeds. The
  error - bad JSON, an unexpected     authoritative gate is .githooks, and a
  shape, a missing import             convenience layer that bricks every
                                      shell call is far worse than one that
                                      misses.

test_no_wrapper_failure_mode_ever_returns_the_deny_code is the machine-checked
statement of the second half, and it is the test to keep green above all
others here.

EVERY VIOLATING LITERAL IS ASSEMBLED FROM FRAGMENTS AT RUNTIME. This file is
itself checked by the character-set gate, so a spelled-out em dash or an
AWS-shaped key here would block the commit that adds it.
"""

from __future__ import annotations

import importlib.util
import io
import json
import shutil
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
WRAPPER = REPO_ROOT / "tools" / "pretooluse_gate.py"
GATE = REPO_ROOT / "tools" / "precommit_gate.py"
SETTINGS = REPO_ROOT / ".claude" / "settings.json"

TIMEOUT = 60

# Claude Code's PreToolUse protocol. Exit 2 denies the tool call and feeds
# stderr back to the model; anything else is non-blocking. This constant is
# duplicated here ON PURPOSE - the test must pin the number independently of
# whatever the implementation happens to say, or it would assert the
# implementation against itself.
DENY = 2

# Assembled, never spelled out - see the module docstring.
EM_DASH = chr(0x2014)
RIGHT_SMART_QUOTE = chr(0x2019)
LEFT_SMART_QUOTE = chr(0x2018)
AWS_KEY = "AKIA" + "1234567890ABCDEF"
PEM_HEADER = "-----BEGIN " + "RSA PRIVATE KEY" + "-----"


# --------------------------------------------------------------------------
# Harness
# --------------------------------------------------------------------------


def envelope(
    command: str,
    *,
    tool_name: str = "Bash",
    description: str = "a probe",
) -> dict[str, Any]:
    """The EXACT envelope shape a PreToolUse hook receives on stdin.

    The wrapper fields around `tool_input` are harness metadata - `cwd` and
    `transcript_path` are absolute paths under the operator's home directory.
    They are present here precisely so the tests prove the wrapper does NOT
    scan them: scanning a harness-supplied home path would deny every call on
    a machine whose account name is not ASCII, and would report the operator's
    own directory back as a finding.
    """
    return {
        "session_id": "0000-0000",
        "transcript_path": "<harness supplied>",
        "cwd": "<harness supplied>",
        "hook_event_name": "PreToolUse",
        "tool_name": tool_name,
        "tool_input": {
            "command": command,
            "description": description,
            "timeout": 120,
            "run_in_background": False,
        },
    }


# A SHARP EDGE, found by watching these tests fail before the wrapper existed
# and recorded here because it is not obvious and it is not ours to fix:
# CPython exits with status 2 when it cannot open the script it was handed.
# That is the SAME number as a deny, so a missing wrapper file is
# indistinguishable from a denial by exit code alone, and three tests in this
# file passed on it while the wrapper did not exist yet - the exact "a test
# that passes before the fix is a test about nothing" failure.
#
# The exposure is pre-existing and unchanged by CS-425: the old wiring named
# tools/precommit_gate.py and a missing gate would have denied every shell call
# the same way. It is also LOUD - the interpreter names the file it could not
# open - and the file is tracked, so the condition means a broken checkout.
# What is fixed here is the blindness it caused in this suite: every helper
# below refuses to interpret an interpreter start-up failure as a verdict.
INTERPRETER_START_FAILURE = "can't open file"


def reject_startup_failure(stderr: str) -> None:
    """Refuse to read a verdict out of an interpreter that never started."""
    assert INTERPRETER_START_FAILURE not in stderr, (
        "the interpreter could not start the wrapper, and its exit status is 2 - "
        "the same number as a deny. This is NOT a verdict: " + stderr.strip()
    )


def run_wrapper(
    payload: bytes,
    *,
    executable: str | None = None,
) -> subprocess.CompletedProcess[str]:
    """Drive the wrapper as a subprocess over a real stdin pipe."""
    proc = subprocess.run(
        [executable or sys.executable, str(WRAPPER)],
        input=payload,
        capture_output=True,
        cwd=str(REPO_ROOT),
        timeout=TIMEOUT,
        check=False,
    )
    stderr = proc.stderr.decode("utf-8", "replace")
    reject_startup_failure(stderr)
    return subprocess.CompletedProcess(
        proc.args,
        proc.returncode,
        proc.stdout.decode("utf-8", "replace"),
        stderr,
    )


def feed(obj: object, *, ensure_ascii: bool = True) -> subprocess.CompletedProcess[str]:
    """Serialise an envelope and feed it in.

    ensure_ascii=True is json.dumps' default and is what a JSON emitter
    actually produces: a non-ASCII character leaves as a backslash-u escape.
    That is the encoding that made the old wiring blind, so it is the default
    here too.
    """
    return run_wrapper(json.dumps(obj, ensure_ascii=ensure_ascii).encode("utf-8"))


def load_by_path(path: Path, name: str) -> ModuleType:
    """Import a module by file path, for the checks that are pure text.

    Loading from the path rather than importing `tools.pretooluse_gate` keeps
    tools/ out of the suite's import graph, matching tests/test_precommit_gate.py.
    """
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    # Registered BEFORE exec_module: the gate declares dataclasses under
    # `from __future__ import annotations`, and @dataclass resolves those
    # string annotations through sys.modules[cls.__module__].
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class FakeStdin:
    """Just enough of sys.stdin for the gate's own stdin mode to run."""

    def __init__(self, data: bytes) -> None:
        """Hold the bytes the gate's stdin mode will read."""
        self.buffer = io.BytesIO(data)


# --------------------------------------------------------------------------
# a. the file exists and is wired
# --------------------------------------------------------------------------


def test_the_wrapper_exists() -> None:
    assert WRAPPER.is_file(), f"the wrapper is missing at {WRAPPER}"


def test_settings_points_pretooluse_at_the_wrapper() -> None:
    """The hook must actually invoke the wrapper, not the gate directly.

    Hook presence is not hook firing (CLAUDE.md section 2.2), so this asserts
    the wiring only; the end-to-end behaviour is every other test in this file.
    """
    config = json.loads(SETTINGS.read_bytes().decode("utf-8"))
    entries = config["hooks"]["PreToolUse"]
    commands = [hook["command"] for entry in entries for hook in entry["hooks"]]
    joined = " ".join(commands)
    assert "tools/pretooluse_gate.py" in joined, (
        "PreToolUse does not invoke the wrapper; it reads: " + joined
    )
    assert "--text-stdin" not in joined, (
        "PreToolUse still passes --text-stdin, which is the raw-text mode that "
        "cannot see inside a JSON envelope: " + joined
    )


def test_the_pretooluse_matcher_is_not_narrowed() -> None:
    """Coverage may not be reduced. The matcher stays on both shell tools."""
    config = json.loads(SETTINGS.read_bytes().decode("utf-8"))
    matchers = [entry["matcher"] for entry in config["hooks"]["PreToolUse"]]
    covered = " ".join(matchers)
    assert "Bash" in covered, "the Bash tool fell out of the PreToolUse matcher"
    assert "PowerShell" in covered, "the PowerShell tool fell out of the matcher"


def test_the_posttooluse_hook_is_untouched() -> None:
    """This slice owns PreToolUse only. PostToolUse must be exactly as found."""
    config = json.loads(SETTINGS.read_bytes().decode("utf-8"))
    entries = config["hooks"]["PostToolUse"]
    commands = [hook["command"] for entry in entries for hook in entry["hooks"]]
    assert any("edit_lint_check.py" in command for command in commands)


# --------------------------------------------------------------------------
# b. fail CLOSED - a real violation is DENIED with exit 2
# --------------------------------------------------------------------------


def test_a_clean_command_passes() -> None:
    proc = feed(envelope("git status --short"))
    assert proc.returncode == 0, proc.stderr
    assert "PASS" in proc.stdout, proc.stdout


def test_a_literal_em_dash_in_the_command_is_denied() -> None:
    proc = feed(envelope("echo hello " + EM_DASH + " world"))
    assert proc.returncode == DENY, (
        f"expected exit {DENY} (deny); got {proc.returncode}. "
        f"stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )
    assert "CHARSET" in proc.stderr, proc.stderr
    assert "U+2014" in proc.stderr, proc.stderr


def test_a_smart_quote_in_the_command_is_denied() -> None:
    proc = feed(envelope("echo it" + RIGHT_SMART_QUOTE + "s here"))
    assert proc.returncode == DENY, proc.stderr
    assert "CHARSET" in proc.stderr, proc.stderr
    assert "U+2019" in proc.stderr, proc.stderr


def test_a_secret_shaped_token_in_the_command_is_denied() -> None:
    proc = feed(envelope("aws configure set key " + AWS_KEY))
    assert proc.returncode == DENY, proc.stderr
    assert "SECRET" in proc.stderr, proc.stderr


def test_a_pem_private_key_block_in_the_command_is_denied() -> None:
    proc = feed(envelope("echo '" + PEM_HEADER + "' > id_rsa"))
    assert proc.returncode == DENY, proc.stderr
    assert "SECRET" in proc.stderr, proc.stderr


def test_the_powershell_envelope_shape_is_handled() -> None:
    """Both shell tools carry the command under the same key, and both deny."""
    proc = feed(envelope("Write-Output " + EM_DASH, tool_name="PowerShell"))
    assert proc.returncode == DENY, proc.stderr
    assert "CHARSET" in proc.stderr, proc.stderr


def test_a_denial_names_the_field_it_came_from() -> None:
    """A denial the model cannot act on is a denial that gets worked around."""
    proc = feed(envelope("echo " + EM_DASH))
    assert proc.returncode == DENY, proc.stderr
    assert "command" in proc.stderr, proc.stderr


def test_a_denial_says_it_denied() -> None:
    """The model is handed stderr on exit 2, so it must be self-explaining."""
    proc = feed(envelope("echo " + EM_DASH))
    assert proc.returncode == DENY
    assert "DENIED" in proc.stderr, proc.stderr


# --------------------------------------------------------------------------
# c. the case that made the old wiring blind
# --------------------------------------------------------------------------


def test_a_json_escaped_non_ascii_character_is_denied_exactly_like_a_literal_one() -> None:
    """The backslash-u escape is TRANSPORT, and parsing dissolves it.

    This is the measurement that closed CS-425: fed an envelope whose em dash
    had been escaped to a backslash-u sequence, the old wiring scanned pure
    ASCII and returned rc=0 PASS. After json.loads the two encodings are the
    SAME PYTHON STRING, so the correct behaviour is that they are
    indistinguishable - identical exit code and identical diagnostic. The
    harness will hand the decoded string to the shell either way, so treating
    the escaped form as clean would be scanning the wire format instead of the
    command.
    """
    payload = envelope("echo " + EM_DASH)
    escaped = feed(payload, ensure_ascii=True)
    literal = feed(payload, ensure_ascii=False)

    # The premise: the two payloads really are different bytes on the wire.
    escaped_bytes = json.dumps(payload, ensure_ascii=True).encode("utf-8")
    literal_bytes = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    assert escaped_bytes != literal_bytes
    assert b"u2014" in escaped_bytes.lower(), "the escaped payload is not actually escaped"
    assert escaped_bytes.isascii(), "the escaped payload should be pure ASCII on the wire"

    assert escaped.returncode == DENY, (
        "an escaped em dash was not denied - this is the exact blindness "
        f"CS-425 exists to close. stdout={escaped.stdout!r}"
    )
    assert escaped.returncode == literal.returncode
    assert escaped.stderr == literal.stderr


def test_a_lone_surrogate_escape_does_not_crash_the_wrapper() -> None:
    """json.loads yields an unpaired surrogate for a lone backslash-u escape.

    Encoding one to UTF-8 raises unless it is handled, so this pins that the
    wrapper neither crashes nor waves it through: an unpaired surrogate in a
    shell command is non-ASCII garbage and is a character-set finding.
    """
    raw = '{"tool_name":"Bash","tool_input":{"command":"echo \\ud800"}}'
    proc = run_wrapper(raw.encode("ascii"))
    assert proc.returncode == DENY, f"rc={proc.returncode} stdout={proc.stdout!r}"
    assert "CHARSET" in proc.stderr, proc.stderr


# --------------------------------------------------------------------------
# d. the scanned surface
# --------------------------------------------------------------------------


def test_every_string_in_tool_input_is_scanned_not_only_the_command() -> None:
    """Coverage may not be narrowed to a single key.

    A description is authored content and non-negotiable 4 covers it, and an
    allowlist of key names would silently miss whichever field a tool gains
    tomorrow.
    """
    proc = feed(envelope("git status", description="checking " + EM_DASH + " state"))
    assert proc.returncode == DENY, (
        f"a violation in `description` was not seen. rc={proc.returncode} stdout={proc.stdout!r}"
    )
    assert "description" in proc.stderr, proc.stderr


def test_a_string_nested_inside_tool_input_is_scanned() -> None:
    """The walk is recursive; a tool that nests its input is still covered."""
    payload = {
        "tool_name": "Bash",
        "tool_input": {"env": {"vars": ["SAFE=1", "TOKEN=" + AWS_KEY]}},
    }
    proc = feed(payload)
    assert proc.returncode == DENY, f"rc={proc.returncode} stdout={proc.stdout!r}"
    assert "SECRET" in proc.stderr, proc.stderr


def test_harness_metadata_outside_tool_input_is_not_scanned() -> None:
    """`cwd` and `transcript_path` are harness-supplied absolute home paths.

    Scanning them would deny every single call on a machine whose account name
    carries a non-ASCII character, and would report the operator's own
    directory back as a finding. They are not the tool call's content.
    """
    payload = envelope("git status")
    payload["cwd"] = "C:" + chr(0x5C) + "Users" + chr(0x5C) + "Ren" + chr(0xE9)
    payload["transcript_path"] = "somewhere " + EM_DASH + " else"
    proc = feed(payload)
    assert proc.returncode == 0, (
        "harness metadata outside tool_input was scanned. "
        f"rc={proc.returncode} stderr={proc.stderr!r}"
    )


# --------------------------------------------------------------------------
# e. fail OPEN - the wrapper's own errors never deny
# --------------------------------------------------------------------------

# Every shape a broken or unexpected stdin can take. Each must exit non-deny.
BROKEN_INPUTS: tuple[tuple[str, bytes], ...] = (
    ("malformed json", b"{not json at all"),
    ("truncated json", b'{"tool_name": "Bash", "tool_input": {"command":'),
    ("empty stdin", b""),
    ("whitespace only", b"   \n  "),
    ("json null", b"null"),
    ("json array at top level", b'[{"tool_input": {"command": "x"}}]'),
    ("json string at top level", b'"just a string"'),
    ("no tool_input key", b'{"tool_name": "Bash"}'),
    ("tool_input is not an object", b'{"tool_name": "Bash", "tool_input": "echo hi"}'),
    ("tool_input is empty", b'{"tool_name": "Bash", "tool_input": {}}'),
    ("no command key", b'{"tool_name": "Bash", "tool_input": {"timeout": 120}}'),
    ("tool_input holds no strings", b'{"tool_input": {"timeout": 120, "bg": true}}'),
    ("not utf-8", b"\xff\xfe\x00broken"),
)


@pytest.mark.parametrize(("name", "payload"), BROKEN_INPUTS, ids=[n for n, _ in BROKEN_INPUTS])
def test_no_wrapper_failure_mode_ever_returns_the_deny_code(name: str, payload: bytes) -> None:
    """THE most important test in this file.

    A convenience layer that bricks every shell call is far worse than one
    that misses, and the authoritative gate is .githooks either way.
    """
    proc = run_wrapper(payload)
    assert proc.returncode != DENY, (
        f"{name} produced a DENIAL. rc={proc.returncode} "
        f"stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )
    assert proc.returncode == 0, (
        f"{name} exited {proc.returncode}; fail-open is exit 0. "
        f"stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )


@pytest.mark.parametrize(("name", "payload"), BROKEN_INPUTS, ids=[n for n, _ in BROKEN_INPUTS])
def test_every_fail_open_says_out_loud_that_nothing_was_scanned(name: str, payload: bytes) -> None:
    """Every fail-open announces itself.

    A silent fail-open is the false-guarantee class this project rates worse
    than the bug. On exit 0 the harness renders stdout, so the notice goes
    there rather than to stderr.
    """
    proc = run_wrapper(payload)
    combined = proc.stdout + proc.stderr
    assert "pretooluse_gate" in combined, f"{name}: no diagnostic at all: {combined!r}"
    assert "NOT SCANNED" in combined.upper(), f"{name}: fail-open was silent: {combined!r}"


def test_a_fail_open_never_claims_to_have_passed() -> None:
    """PASS and NOT SCANNED are different claims and must not be confused."""
    proc = run_wrapper(b"{not json at all")
    assert proc.returncode == 0
    assert "PASS" not in proc.stdout.upper(), proc.stdout


def test_the_wrapper_fails_open_when_the_gate_cannot_be_imported(tmp_path: Path) -> None:
    """A copy of the wrapper with no gate beside it must not deny.

    The import is the wrapper's single hardest dependency, so the failure is
    provoked for real rather than argued: an isolated directory holding the
    wrapper and nothing else.
    """
    orphan = tmp_path / "tools"
    orphan.mkdir()
    copy = orphan / WRAPPER.name
    copy.write_bytes(WRAPPER.read_bytes())
    proc = subprocess.run(
        [sys.executable, str(copy)],
        input=json.dumps(envelope("echo " + EM_DASH)).encode("utf-8"),
        capture_output=True,
        cwd=str(tmp_path),
        timeout=TIMEOUT,
        check=False,
    )
    out = proc.stdout.decode("utf-8", "replace") + proc.stderr.decode("utf-8", "replace")
    assert proc.returncode != DENY, f"an unimportable gate denied the call. out={out!r}"
    assert proc.returncode == 0, f"rc={proc.returncode} out={out!r}"
    assert "NOT SCANNED" in out.upper(), out


def test_the_wrapper_does_not_read_the_filesystem_for_its_verdict(tmp_path: Path) -> None:
    """Run from an unrelated cwd. The verdict comes from stdin, nothing else."""
    proc = subprocess.run(
        [sys.executable, str(WRAPPER)],
        input=json.dumps(envelope("echo " + EM_DASH)).encode("utf-8"),
        capture_output=True,
        cwd=str(tmp_path),
        timeout=TIMEOUT,
        check=False,
    )
    stderr = proc.stderr.decode("utf-8", "replace")
    reject_startup_failure(stderr)
    assert proc.returncode == DENY, stderr


def test_a_missing_wrapper_file_is_loud_even_though_its_status_looks_like_a_deny(
    tmp_path: Path,
) -> None:
    """Pins the sharp edge documented at INTERPRETER_START_FAILURE above.

    CPython's exit status for an unopenable script is 2, which collides with
    the deny code. Nothing in this repo can change that number, so what is
    asserted is the part that makes it survivable: the interpreter NAMES the
    file it could not open, so the condition is diagnosable in one glance
    rather than presenting as a mysterious blanket denial.
    """
    absent = tmp_path / "pretooluse_gate.py"
    proc = subprocess.run(
        [sys.executable, str(absent)],
        input=b"{}",
        capture_output=True,
        cwd=str(tmp_path),
        timeout=TIMEOUT,
        check=False,
    )
    stderr = proc.stderr.decode("utf-8", "replace")
    assert proc.returncode == DENY, (
        "the collision this file warns about no longer exists on this "
        f"interpreter - status was {proc.returncode}. Re-read the note above."
    )
    assert INTERPRETER_START_FAILURE in stderr, stderr
    assert absent.name in stderr, stderr


# --------------------------------------------------------------------------
# f. the wrapper does not re-implement the scan
# --------------------------------------------------------------------------

# A second transcription of a security scan is a second place to get it subtly
# wrong. The wrapper imports the gate's checks; these two tests are what keeps
# that true as the gate changes underneath it.

PARITY_SAMPLES: tuple[str, ...] = (
    "git status --short",
    "echo " + EM_DASH,
    "echo " + LEFT_SMART_QUOTE + "x" + RIGHT_SMART_QUOTE,
    "aws configure set key " + AWS_KEY,
    "echo '" + PEM_HEADER + "'",
    "",
    "a" * 5000,
    "line one\nline two " + EM_DASH + "\nline three",
)


@pytest.mark.parametrize("sample", PARITY_SAMPLES, ids=range(len(PARITY_SAMPLES)))
def test_the_wrapper_scan_matches_the_gates_own_stdin_mode(
    sample: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Identical findings, character for character, over the same text.

    If the gate grows a third check in its stdin mode, this goes red and the
    wrapper has to grow it too - which is the only way a composition copied by
    hand stays honest.
    """
    gate = load_by_path(GATE, "cs425_gate_parity")
    wrapper = load_by_path(WRAPPER, "cs425_wrapper_parity")

    monkeypatch.setattr(sys, "stdin", FakeStdin(sample.encode("utf-8")))
    gate_report = gate.Report()
    gate.mode_text_stdin(gate_report)
    expected = sorted(diag.render() for diag in gate_report.diagnostics)

    wrapper_report = gate.Report()
    wrapper.scan_text(gate, "<stdin>", sample, wrapper_report)
    actual = sorted(diag.render() for diag in wrapper_report.diagnostics)

    assert actual == expected


def test_every_gate_symbol_the_wrapper_depends_on_exists() -> None:
    """The wrapper's dependency on the frozen gate is named, not assumed.

    Stating it explicitly means a rename inside the gate fails HERE - loudly,
    in the suite - rather than at runtime as a permanent silent fail-open.
    """
    gate = load_by_path(GATE, "cs425_gate_symbols")
    wrapper = load_by_path(WRAPPER, "cs425_wrapper_symbols")
    assert wrapper.GATE_SYMBOLS, "the wrapper declares no dependency set"
    missing = [name for name in wrapper.GATE_SYMBOLS if not hasattr(gate, name)]
    assert not missing, f"the wrapper depends on symbols the gate does not export: {missing}"


def test_the_wrapper_does_not_carry_its_own_copy_of_the_scan() -> None:
    """No transcribed pattern table. The gate owns the patterns, alone."""
    source = WRAPPER.read_bytes().decode("utf-8")
    for owned in ("SECRET_PATTERNS", "PLACEHOLDER_RE", "MAX_ASCII", "NAMED_OFFENDERS"):
        assert f"{owned} =" not in source, f"the wrapper defines its own {owned}; the gate owns it"
        assert f"{owned}=" not in source, f"the wrapper defines its own {owned}; the gate owns it"


# --------------------------------------------------------------------------
# g. the console-flash half of CS-425
# --------------------------------------------------------------------------


def _settings_interpreter() -> str:
    config = json.loads(SETTINGS.read_bytes().decode("utf-8"))
    entries = config["hooks"]["PreToolUse"]
    commands = [hook["command"] for entry in entries for hook in entry["hooks"]]
    return commands[0].split()[0] if commands else ""


@pytest.mark.skipif(sys.platform != "win32", reason="pythonw.exe is a Windows binary")
def test_a_gui_subsystem_interpreter_delivers_the_same_verdict_over_a_pipe() -> None:
    """pythonw.exe allocates no console, which is the flash half of CS-425.

    It is only legitimate once the hook actually works, and only if rc and
    both streams survive a parent-supplied pipe - a GUI-subsystem binary with
    no redirection has sys.stdout set to None. Proven here rather than argued,
    because the failure mode is a gate that silently stops reporting. Do NOT
    check this from PowerShell: PowerShell does not wait on a GUI-subsystem
    binary and reports no output and no exit code.
    """
    pythonw = shutil.which("pythonw")
    if pythonw is None:
        pytest.skip("pythonw.exe is not on PATH")

    for command in ("git status --short", "echo " + EM_DASH, "aws key " + AWS_KEY):
        payload = json.dumps(envelope(command)).encode("utf-8")
        console = run_wrapper(payload)
        gui = run_wrapper(payload, executable=pythonw)
        assert gui.returncode == console.returncode, command
        assert gui.stdout == console.stdout, command
        assert gui.stderr == console.stderr, command


@pytest.mark.skipif(sys.platform != "win32", reason="pythonw.exe is a Windows binary")
def test_the_configured_interpreter_can_actually_be_resolved() -> None:
    """A hook whose interpreter is not on PATH is a hook that does nothing.

    Guards the exact regression the flash fix could introduce: naming an
    interpreter the machine cannot find turns a working gate back into a
    no-op, and nothing else in this suite would notice.
    """
    interpreter = _settings_interpreter()
    assert interpreter, "PreToolUse has no command"
    assert shutil.which(interpreter) is not None, (
        f"settings.json names interpreter {interpreter!r}, which is not on PATH"
    )
