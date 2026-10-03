"""CS-815 - both Claude Code hooks run through a probed wrapper, proven by driving it.

WHAT WAS WRONG. ``.claude/settings.json`` named ``pythonw`` and ``python`` bare,
with no resolution ladder and no probe. The PreToolUse gate's protocol is that
exit 2 denies and every other status is non-blocking, so a missing or
substituted interpreter yielded a non-2 status and the gate FAILED OPEN in
silence. ``tools/claude_hook.sh`` carries the git hooks' probe and ladder and
execs the tool only after the probe passes.

WHAT EACH GROUP OF ARMS PROVES, against the grant recorded in docs/LEDGER.md
under "2026-09-25 - CS-815 - FROZEN-FILE GRANT":

    carriage     condition 1 - the probe and the marked ladder are byte-identical
                 to .githooks/pre-commit, and the wrapper names no absolute path
    settings     the two command values are the only bytes that moved
    pass-through condition 2 - stdin byte-identical, exit status, stdout and
                 stderr identical to the DIRECT invocation, a deny still denies,
                 and the PreToolUse leg runs pythonw beside the winner
    loud report  condition 3 - one stderr line, a non-2 status, nothing echoed
    latency      condition 4 - a 20-call median, and the worst case under both
                 timeouts
    proof        condition 5 - each program in ARGUMENT_IGNORING_PROGRAMS,
                 IMPORTED from tests/test_hook_interpreter_ladder.py, is loudly
                 reported; a good interpreter passes; a known deny still denies

EVERY ARM DRIVES THE WRAPPER THE WAY THE HARNESS DOES: a shell runs it with the
tool and its arguments, and a JSON envelope arrives on stdin.

PATHS STAY OUT OF EVERY ASSERTION MESSAGE. ``tmp_path`` and ``sys.executable``
sit under the operator's profile, so every result is reduced to an int, a bool
or text passed through ``shown`` before it is rendered (CLAUDE.md
non-negotiables 3 and 12).
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import statistics
import subprocess
import sys
import time
from collections.abc import Callable
from functools import cache
from pathlib import Path
from typing import Final, NamedTuple

import pytest

from tests.test_hook_interpreter_ladder import (
    ARGUMENT_IGNORING_PROGRAMS,
    DRIVE_PATH,
    INTERESTING_VALUE_LENGTH,
    LADDER_RUNGS,
    LIAR_SHIM,
    MARKED_LADDER_BEGIN,
    MARKED_LADDER_END,
    MARKED_LADDER_VOICE,
    MARKED_LADDER_VOICE_LINES,
    Environment,
    isolated,  # noqa: F401 - a fixture, used by name
    probe_block,
    write_shim,
)
from tests.test_pretooluse_gate import EM_DASH, envelope, require_posix_shell
from tests.xdist_quiet import (
    await_quiet_siblings,
    hold_liveness_lock,
    live_sibling_count,
    live_siblings_now,
    release_liveness_lock,
)

REPO_ROOT: Final = Path(__file__).resolve().parent.parent
WRAPPER: Final = REPO_ROOT / "tools" / "claude_hook.sh"
PRE_COMMIT: Final = REPO_ROOT / ".githooks" / "pre-commit"
GATE: Final = REPO_ROOT / "tools" / "pretooluse_gate.py"
LINT: Final = REPO_ROOT / "tools" / "edit_lint_check.py"
SETTINGS: Final = REPO_ROOT / ".claude" / "settings.json"

PRE: Final = "pretooluse"
POST: Final = "posttooluse"
ENV_NAME: Final = "CLOCKSPEED_PYTHON"

# Claude Code's PreToolUse deny status, pinned HERE rather than read from the
# gate, so the arms do not grade the implementation against itself.
DENY: Final = 2

CALL_TIMEOUT: Final = 90

# THE GRANT'S BASE BYTES, by digest. `.claude/settings.json` at the grant base
# c6f3687, which is also the file's bytes at 9c4ff2a. The settings arm swaps the
# two new command values back to the two old ones and demands this digest, so
# every other byte of the frozen file is pinned without restating it.
BASE_SETTINGS_SHA256: Final = "5f5005404f82a2712c5ad86443afe2e0b4c533b0849985a4fb9b07de059b1389"
OLD_PRE_COMMAND: Final = 'pythonw "$CLAUDE_PROJECT_DIR/tools/pretooluse_gate.py"'
OLD_POST_COMMAND: Final = (
    'python "$CLAUDE_PROJECT_DIR/tools/edit_lint_check.py" --files "$CLAUDE_FILE_PATHS"'
)
NEW_PRE_COMMAND: Final = (
    'sh "$CLAUDE_PROJECT_DIR/tools/claude_hook.sh" pretooluse'
    ' "$CLAUDE_PROJECT_DIR/tools/pretooluse_gate.py"'
)
NEW_POST_COMMAND: Final = (
    'sh "$CLAUDE_PROJECT_DIR/tools/claude_hook.sh" posttooluse'
    ' "$CLAUDE_PROJECT_DIR/tools/edit_lint_check.py" --files "$CLAUDE_FILE_PATHS"'
)

# The wrapper's one report line. Its fixed prefix, and the shape every refusal
# must have: one line, no colon, nothing a candidate or the environment said.
REPORT_PREFIX: Final = "clockspeed claude hook - REFUSED (CS-815) - "
REPORT_SUFFIX: Final = " - the hook tool did not run"
# The wrapper's own closing voice inside the carried ladder. The ladder test's
# MARKED_LADDER_VOICE matches the git hooks' voice and must NOT match this one,
# which is what makes the per-position comparison below meaningful.
WRAPPER_VOICE: Final = re.compile(rb'^\s+"The hook tool is BLOCKED: ')

# Words an interpreter string is made of. None may appear in a report line.
INTERPRETER_WORDS: Final = ("python", "pythonw", "py -3", "py.exe", ".exe")

# The stub tool. It proves the pass-through by reporting what it RECEIVED:
# a digest and length of stdin, its argv, the basename of the interpreter that
# ran it. It writes both streams as raw bytes, CR LF and a non-ASCII byte
# included, and exits with the status named in its environment.
STUB_SOURCE: Final = (
    "import hashlib, json, os, sys\n"
    "data = sys.stdin.buffer.read()\n"
    "out = b'STUB-OUT\\r\\n' + hashlib.sha256(data).hexdigest().encode('ascii')\n"
    "out += b'\\n' + str(len(data)).encode('ascii')\n"
    "out += b'\\n' + json.dumps(sys.argv[1:]).encode('ascii')\n"
    "out += b'\\n' + os.path.basename(sys.executable).lower().encode('ascii')\n"
    "sys.stdout.buffer.write(out)\n"
    "sys.stdout.buffer.flush()\n"
    "sys.stderr.buffer.write(b'STUB-ERR \\x01\\xff\\r\\nsecond line')\n"
    "sys.stderr.buffer.flush()\n"
    "sys.exit(int(os.environ.get('CS815_STUB_EXIT', '0')))\n"
)
STUB_EXITS: Final = (0, 1, 2, 3, 97, 255)
STUB_ARGS: Final = ("--files", "a path with spaces.py", "", "$CLAUDE_FILE_PATHS", "-3")

# A stdin a probe would visibly damage if it read even one byte: the envelope,
# then every byte value, then CR LF and a NUL, large enough to exceed a pipe
# buffer on both platforms.
BINARY_TAIL: Final = bytes(range(256)) * 400 + b"\r\n\x00"

LATENCY_CALLS: Final = 20
LATENCY_BUDGET_SECONDS: Final = 1.0

# Below this an account name matches wrapper text by coincidence.
MIN_ACCOUNT_LENGTH: Final = 4


class Run(NamedTuple):
    """One process result, holding bytes only - the argv is deliberately dropped."""

    returncode: int
    stdout: bytes
    stderr: bytes
    seconds: float


def shown(data: bytes | str) -> str:
    """Render process output for a message, withholding any line naming a path."""
    text = data.decode("utf-8", "replace") if isinstance(data, bytes) else data
    return "\n".join(
        "<line withheld: carries a path>" if DRIVE_PATH.search(line) else line
        for line in text.split("\n")
    )


def run(argv: list[str], stdin: bytes, env: dict[str, str], cwd: Path) -> Run:
    """Spawn one process and keep only its bytes, status and wall time."""
    started = time.perf_counter()
    proc = subprocess.run(
        argv,
        input=stdin,
        capture_output=True,
        env=env,
        cwd=str(cwd),
        timeout=CALL_TIMEOUT,
        check=False,
    )
    return Run(proc.returncode, proc.stdout, proc.stderr, time.perf_counter() - started)


@cache
def posix_shell() -> str:
    """The POSIX sh the harness runs hook commands under.

    ONE RULE, OWNED BY tests/test_pretooluse_gate.py and imported: sh on PATH,
    then Git for Windows' own sh found from git, then an explicit skip when the
    machine has no sh at all. A pytest launched from PowerShell has no sh on
    PATH, and that must not decide the verdict.
    """
    return require_posix_shell()


def extended(env: Environment, **changes: str) -> Environment:
    """A copy of the carrier with some variables set, never exposed as a bare dict."""
    return Environment({**env.variables, **changes})


def path_first(env: Environment, directory: Path | str) -> Environment:
    """A copy of the carrier with one directory put first on PATH."""
    return extended(env, PATH=str(directory) + os.pathsep + env.variables.get("PATH", ""))


def echoed_values(env: Environment, line: str) -> int:
    """How many long environment values a line echoes, as a count only."""
    return sum(
        1
        for value in env.variables.values()
        if len(value) >= INTERESTING_VALUE_LENGTH and value in line
    )


def via_wrapper(leg: str, tool_argv: list[str], stdin: bytes, env: Environment, cwd: Path) -> Run:
    """The harness shape: a shell runs the wrapper, the envelope on stdin."""
    return run([posix_shell(), str(WRAPPER), leg, *tool_argv], stdin, env.variables, cwd)


def beside(executable: str, leg: str) -> str:
    """The interpreter the wrapper is expected to exec for a leg.

    Computed independently of the wrapper: pythonw.exe in the running
    interpreter's own directory on Windows for the PreToolUse leg, the running
    interpreter otherwise.
    """
    if leg == PRE and os.name == "nt":
        return str(Path(executable).parent / "pythonw.exe")
    return executable


def direct(leg: str, tool_argv: list[str], stdin: bytes, env: Environment, cwd: Path) -> Run:
    """The tool run with no wrapper, under the interpreter the wrapper should pick."""
    return run([beside(sys.executable, leg), *tool_argv], stdin, env.variables, cwd)


@pytest.fixture
def harness(isolated: Environment) -> Environment:  # noqa: F811 - the imported fixture
    """The isolated environment with the shell's own directory first on PATH, as in Git Bash."""
    return path_first(isolated, Path(posix_shell()).parent)


@pytest.fixture
def pinned(harness: Environment) -> Environment:
    """The harness environment with the ladder pinned at the running interpreter."""
    return extended(harness, **{ENV_NAME: sys.executable})


def report_line(result: Run) -> str:
    """The wrapper's refusal, asserted to be exactly one line of stderr."""
    text = result.stderr.decode("ascii", "replace")
    lines = [line for line in text.split("\n") if line]
    assert len(lines) == 1, f"expected ONE stderr line, got {len(lines)}:\n{shown(text)}"
    assert text.endswith("\n"), "the report line is not terminated"
    return lines[0]


def assert_loud(result: Run, env: Environment, extra: tuple[str, ...] = ()) -> str:
    """Condition 3 in full: non-zero, not 2, one line, nothing echoed, tool not run."""
    assert result.returncode != 0, "a failed probe exited 0 - the tool call proceeds SILENTLY"
    assert result.returncode != DENY, (
        "a failed probe exited 2, which DENIES every shell call on the PreToolUse leg"
    )
    assert result.stdout == b"", f"the wrapper wrote stdout on a refusal:\n{shown(result.stdout)}"
    line = report_line(result)
    assert line.startswith(REPORT_PREFIX), f"not the wrapper's report line:\n{shown(line)}"
    assert line.endswith(REPORT_SUFFIX), f"not the wrapper's report line:\n{shown(line)}"
    assert line.isascii(), "the report line is not 7-bit ASCII"
    assert ":" not in line, "the report line carries a colon, which a candidate name could be"
    leaked_words = [word for word in INTERPRETER_WORDS if word in line.lower()]
    assert not leaked_words, f"the report line names an interpreter: {leaked_words}"
    assert not DRIVE_PATH.search(line), "the report line carries a drive-letter path"
    leaked = echoed_values(env, line)
    assert leaked == 0, f"the report line echoes {leaked} environment value(s)"
    for token in extra:
        hit = token in line
        assert not hit, "the report line echoes the candidate it refused"
    return line


# --- carriage: condition 1 ---------------------------------------------------


def test_the_wrapper_carries_the_hooks_probe_byte_identical() -> None:
    """The constants and ``cs_probe`` body, extracted by the ladder test's own extractor."""
    carried = probe_block(WRAPPER.read_bytes())
    source = probe_block(PRE_COMMIT.read_bytes())
    assert b"cs_probe() {" in carried, "no cs_probe definition was extracted from the wrapper"
    assert carried.rstrip().endswith(b"}"), "the extracted probe block is not closed"
    assert carried == source, "the wrapper's probe differs from .githooks/pre-commit"


def marked_ladder(raw: bytes) -> list[bytes]:
    """The CS-818 marked region, as lines, asserted to occur exactly once."""
    assert raw.count(MARKED_LADDER_BEGIN) == 1, "no single ladder BEGIN marker"
    assert raw.count(MARKED_LADDER_END) == 1, "no single ladder END marker"
    start = raw.index(MARKED_LADDER_BEGIN)
    stop = raw.index(MARKED_LADDER_END) + len(MARKED_LADDER_END)
    return raw[start:stop].split(b"\n")


def test_the_wrapper_carries_the_marked_ladder_byte_identical() -> None:
    """Every ladder line identical by position, apart from the two closing-voice lines.

    The exempt positions are exactly those where .githooks/pre-commit carries the
    voice the ladder test excludes, and at each of them the wrapper carries its
    own voice - so neither side can shed or gain a line under the exemption.
    """
    source = marked_ladder(PRE_COMMIT.read_bytes())
    carried = marked_ladder(WRAPPER.read_bytes())
    assert len(carried) == len(source), "the carried ladder has a different line count"
    exempt = [i for i, line in enumerate(source) if MARKED_LADDER_VOICE.match(line)]
    assert len(exempt) == MARKED_LADDER_VOICE_LINES, "the source ladder lost its voice lines"
    pairs = enumerate(zip(source, carried, strict=True))
    differing = [i for i, (want, got) in pairs if want != got]
    assert differing == exempt, f"ladder lines differ outside the voice lines: {differing}"
    for i in exempt:
        assert WRAPPER_VOICE.match(carried[i]), f"line {i} is not the wrapper's own voice"
        assert not MARKED_LADDER_VOICE.match(carried[i]), f"line {i} kept a git hook's voice"


def test_the_wrapper_is_lf_ascii_and_names_no_absolute_path() -> None:
    """LF, no BOM, 7-bit ASCII, and no drive root, home directory or account name."""
    raw = WRAPPER.read_bytes()
    assert raw.startswith(b"#!/bin/sh\n"), "the wrapper does not start with a POSIX sh shebang"
    assert b"\r" not in raw, "the wrapper carries a CR byte"
    assert raw.isascii(), "the wrapper is not 7-bit ASCII"
    text = raw.decode("ascii").lower()
    assert not DRIVE_PATH.search(text), "the wrapper names a drive-letter path"
    for segment in ("/users/", "/home/", "%userprofile%"):
        assert segment not in text, f"the wrapper names a home directory segment {segment!r}"
    account = os.environ.get("USERNAME") or os.environ.get("USER") or ""
    if len(account) >= MIN_ACCOUNT_LENGTH:
        hit = account.lower() in text
        assert not hit, "the wrapper names the running account"


def test_every_refusal_class_names_a_headline_the_carried_text_still_says() -> None:
    """``die`` classifies the carried headlines by prefix; each prefix must still occur.

    A reworded headline in .githooks/pre-commit, copied here, would otherwise
    fall silently into the unclassified line - still loud, but no longer naming
    the probe that failed.
    """
    text = WRAPPER.read_text(encoding="ascii")
    body = text[text.index("\ndie() {") : text.index("\n}\n", text.index("\ndie() {"))]
    prefixes = re.findall(r'^\s+"([^"*]+)"\*\)', body, re.MULTILINE)
    assert len(prefixes) >= len(("bound", "slow", "pinned", "exhausted")), prefixes
    headlines = re.findall(r'\bdie "([^"]+)"', text)
    orphaned = [p for p in prefixes if not any(h.startswith(p) for h in headlines)]
    assert not orphaned, f"refusal classes that match no carried headline: {orphaned}"


# --- settings: the grant's scope --------------------------------------------


def hook_command(config: dict, event: str) -> str:
    """The single command wired under one hook event."""
    commands = [hook["command"] for entry in config["hooks"][event] for hook in entry["hooks"]]
    assert len(commands) == 1, f"{event} carries {len(commands)} commands, not one"
    return str(commands[0])


def test_settings_routes_both_hooks_through_the_wrapper() -> None:
    """The two command values, exactly as the grant scopes them."""
    config = json.loads(SETTINGS.read_bytes().decode("utf-8"))
    assert hook_command(config, "PreToolUse") == NEW_PRE_COMMAND
    assert hook_command(config, "PostToolUse") == NEW_POST_COMMAND


def test_settings_moved_no_byte_but_the_two_command_values() -> None:
    """Swap the two values back and the file is the grant's base, by digest."""
    raw = SETTINGS.read_bytes()
    for new in (NEW_PRE_COMMAND, NEW_POST_COMMAND):
        encoded = json.dumps(new).encode("ascii")
        assert raw.count(encoded) == 1, "a new command value is not present exactly once"
    restored = raw.replace(
        json.dumps(NEW_PRE_COMMAND).encode("ascii"), json.dumps(OLD_PRE_COMMAND).encode("ascii")
    ).replace(
        json.dumps(NEW_POST_COMMAND).encode("ascii"), json.dumps(OLD_POST_COMMAND).encode("ascii")
    )
    digest = hashlib.sha256(restored).hexdigest()
    assert digest == BASE_SETTINGS_SHA256, (
        "a byte outside the two command values moved - the schema key, attribution, "
        "includeCoAuthoredBy, env, permissions, a matcher or a timeout"
    )


def settings_timeout(event: str) -> int:
    config = json.loads(SETTINGS.read_bytes().decode("utf-8"))
    timeouts = [hook["timeout"] for entry in config["hooks"][event] for hook in entry["hooks"]]
    assert len(timeouts) == 1
    return int(timeouts[0])


def test_the_settings_commands_run_under_a_shell_like_the_harness(
    tmp_path: Path,
    harness: Environment,
) -> None:
    """The command STRINGS, handed to a shell with the anchor in its environment.

    Spawned from tmp_path, never the repository root, so the anchor is what
    finds both files. A benign call passes, a known deny is denied with the
    gate's own words, and the PostToolUse leg lints a clean file.
    """
    config = json.loads(SETTINGS.read_bytes().decode("utf-8"))
    env = extended(harness, CLAUDE_PROJECT_DIR=str(REPO_ROOT))
    pre = hook_command(config, "PreToolUse")

    benign = run(
        [posix_shell(), "-c", pre],
        json.dumps(envelope("git status")).encode(),
        env.variables,
        tmp_path,
    )
    assert benign.returncode == 0, f"a benign call was not allowed:\n{shown(benign.stderr)}"
    assert b"PASS" in benign.stdout, shown(benign.stdout)

    denied = run(
        [posix_shell(), "-c", pre],
        json.dumps(envelope("echo " + EM_DASH)).encode(),
        env.variables,
        tmp_path,
    )
    assert denied.returncode == DENY, f"a known deny was not denied:\n{shown(denied.stderr)}"
    assert b"DENIED" in denied.stderr, shown(denied.stderr)

    edited = tmp_path / "cs815_edited.py"
    edited.write_bytes(b'"""A clean module."""\n')
    env = extended(env, CLAUDE_FILE_PATHS=str(edited))
    post = hook_command(config, "PostToolUse")
    linted = run([posix_shell(), "-c", post], b"{}", env.variables, tmp_path)
    assert linted.returncode == 0, f"a clean edited file was refused:\n{shown(linted.stderr)}"


# --- pass-through: condition 2 -----------------------------------------------


def stdin_payload() -> bytes:
    return json.dumps(envelope("git status --short")).encode("utf-8") + BINARY_TAIL


@pytest.mark.parametrize("leg", [PRE, POST])
def test_stdin_argv_streams_and_status_pass_through_unchanged(
    tmp_path: Path, pinned: Environment, leg: str
) -> None:
    """Every exit status, both streams and the argv, byte-identical to the direct run.

    The stub reports the SHA-256 and length of the stdin it received, so a probe
    that read even one byte of the envelope changes its stdout.
    """
    stub = tmp_path / "cs815_stub.py"
    stub.write_bytes(STUB_SOURCE.encode("ascii"))
    payload = stdin_payload()
    expected_digest = hashlib.sha256(payload).hexdigest().encode("ascii")
    tool = [str(stub), *STUB_ARGS]
    for status in STUB_EXITS:
        env = extended(pinned, CS815_STUB_EXIT=str(status))
        wrapped = via_wrapper(leg, tool, payload, env, tmp_path)
        bare = direct(leg, tool, payload, env, tmp_path)
        assert bare.returncode == status, "the direct control did not exit as asked"
        assert wrapped.returncode == status, (
            f"exit {status} came back through the wrapper as {wrapped.returncode}"
        )
        assert expected_digest in wrapped.stdout, (
            "the tool did not receive the harness's stdin byte-identical"
        )
        assert wrapped.stdout == bare.stdout, (
            f"stdout differs from the direct run:\n{shown(wrapped.stdout)}"
        )
        assert wrapped.stderr == bare.stderr, (
            f"stderr differs from the direct run:\n{shown(wrapped.stderr)}"
        )


def test_the_pretooluse_leg_runs_pythonw_beside_the_winner(
    tmp_path: Path,
    harness: Environment,
) -> None:
    """With the ladder left to itself, the windowed leg runs pythonw and the other does not."""
    stub = tmp_path / "cs815_stub.py"
    stub.write_bytes(STUB_SOURCE.encode("ascii"))
    names = {}
    for leg in (PRE, POST):
        result = via_wrapper(leg, [str(stub)], b"", harness, tmp_path)
        assert result.returncode == 0, f"{leg} did not run the stub:\n{shown(result.stderr)}"
        names[leg] = result.stdout.rsplit(b"\n", 1)[-1].decode("ascii")
    if os.name == "nt":
        assert names[PRE] == "pythonw.exe", f"PreToolUse ran {names[PRE]!r}, not pythonw"
        assert names[POST] != "pythonw.exe", "PostToolUse ran the windowed interpreter"
    else:
        assert names[PRE] == names[POST], "with no pythonw the winner itself must run"


def test_a_known_deny_still_denies_through_the_wrapper_as_it_does_directly(
    tmp_path: Path, pinned: Environment
) -> None:
    """The real gate: exit 2 and its stderr, identical through the wrapper and direct."""
    for command, status in (("git status --short", 0), ("echo " + EM_DASH, DENY)):
        payload = json.dumps(envelope(command)).encode("utf-8")
        wrapped = via_wrapper(PRE, [str(GATE)], payload, pinned, tmp_path)
        bare = direct(PRE, [str(GATE)], payload, pinned, tmp_path)
        assert bare.returncode == status, "the direct control did not give the expected verdict"
        assert wrapped.returncode == status, (
            f"the wrapper turned verdict {status} into {wrapped.returncode}"
        )
        assert wrapped.stdout == bare.stdout, shown(wrapped.stdout)
        assert wrapped.stderr == bare.stderr, shown(wrapped.stderr)


# --- loud report and proof: conditions 3 and 5 --------------------------------


@pytest.mark.parametrize("leg", [PRE, POST])
@pytest.mark.parametrize("program", ARGUMENT_IGNORING_PROGRAMS)
def test_an_argument_ignoring_interpreter_is_loudly_reported(
    tmp_path: Path,
    harness: Environment,
    program: str,
    leg: str,
) -> None:
    """Each program the ladder test names, pointed at through the variable."""
    env = extended(harness, **{ENV_NAME: program})
    tool = [str(GATE)] if leg == PRE else [str(LINT), "--files", str(tmp_path / "x.py")]
    payload = json.dumps(envelope("echo " + EM_DASH)).encode("utf-8")
    result = via_wrapper(leg, tool, payload, env, tmp_path)
    line = assert_loud(result, env, extra=(program,))
    assert "pinned interpreter variable failed the probe" in line, shown(line)


def test_a_liar_on_every_rung_is_loudly_reported(
    tmp_path: Path,
    harness: Environment,
) -> None:
    """No variable set: every ladder rung on PATH forwards output and drops the status."""
    shadow = tmp_path / "allrungs"
    for rung in LADDER_RUNGS:
        write_shim(shadow, rung, LIAR_SHIM)
    env = path_first(harness, shadow)
    payload = json.dumps(envelope("echo " + EM_DASH)).encode("utf-8")
    result = via_wrapper(PRE, [str(GATE)], payload, env, tmp_path)
    line = assert_loud(result, env)
    assert "no interpreter rung passed the probe" in line, shown(line)


def test_a_foreign_bounding_program_is_loudly_reported(
    tmp_path: Path,
    harness: Environment,
) -> None:
    """A ``timeout`` that runs nothing, first on PATH - the Windows pause command's shape."""
    shadow = tmp_path / "foreign"
    write_shim(shadow, "timeout", "#!/bin/sh\nexit 1\n")
    env = path_first(harness, shadow)
    payload = json.dumps(envelope("git status")).encode("utf-8")
    result = via_wrapper(PRE, [str(GATE)], payload, env, tmp_path)
    assert_loud(result, env)


def test_an_unnamed_leg_is_loudly_reported(
    tmp_path: Path,
    harness: Environment,
) -> None:
    """A wrapper call with no leg, or an unknown one, refuses rather than guesses."""
    for argv in ([], ["neither", str(GATE)], [PRE]):
        result = run([posix_shell(), str(WRAPPER), *argv], b"{}", harness.variables, tmp_path)
        assert_loud(result, harness)


def test_a_hanging_candidate_is_bounded_and_loudly_reported(
    tmp_path: Path,
    harness: Environment,
) -> None:
    """A candidate that never answers costs at most the bound plus the grace."""
    hang = write_shim(tmp_path / "hang", "hang.sh", "#!/bin/sh\nsleep 60\n")
    env = extended(harness, **{ENV_NAME: hang.as_posix()})
    result = via_wrapper(PRE, [str(GATE)], b"{}", env, tmp_path)
    assert_loud(result, env)
    bound, grace = wrapper_bound()
    assert result.seconds < bound + grace + 5, (
        f"a hanging candidate held the wrapper {result.seconds:.1f}s"
    )


# --- latency: condition 4 ------------------------------------------------------


def wrapper_bound() -> tuple[int, int]:
    """The probe bound and the kill grace, read from the wrapper and its call site."""
    text = WRAPPER.read_text(encoding="ascii")
    bound = re.search(r"^CS_PROBE_BOUND=(\d+)$", text, re.MULTILINE)
    grace = re.search(r"^CS_HOOK_KILL_GRACE=(\d+)$", text, re.MULTILINE)
    assert bound, "the wrapper lost its probe bound constant"
    assert grace, "the wrapper lost its kill grace constant"
    call = 'timeout -k "$CS_HOOK_KILL_GRACE" "$CS_PROBE_BOUND" \\\n        sh "$0" --resolve'
    assert call in text, "the resolve child is not run under the bound and the grace"
    return int(bound.group(1)), int(grace.group(1))


def test_the_median_call_adds_under_a_second_and_the_worst_case_fits_both_timeouts(
    tmp_path: Path,
    harness: Environment,
    record_property: Callable[[str, object], None],
    request: pytest.FixtureRequest,
) -> None:
    """Twenty paired calls of the real PreToolUse leg, wrapped and direct.

    The median of the per-pair difference is REPORTED as a property and printed,
    and held under a second per call. The worst case is the probe bound plus the
    kill grace plus the slowest observed tool, and it must sit strictly under
    each leg's settings.json timeout.

    MEASURED ALONE, CS-1233. Under xdist the pairs used to run beside CPU-bound
    sibling workers, and the wrapped call - about ten process starts against the
    direct call's one - pays for that contention far more than the direct call
    does, so pairing never cancelled it. The windows guard shard read a median
    of 1.010s to 1.169s that way. The measurement now waits until every sibling
    worker has finished, and is red if one was live when it ended.
    """
    waited = await_quiet_siblings(request.config)
    record_property("cs815_quiet_wait_seconds", round(waited, 3))
    payload = json.dumps(envelope("git status --short")).encode("utf-8")
    added: list[float] = []
    tool_seconds: list[float] = []
    for _ in range(LATENCY_CALLS):
        wrapped = via_wrapper(PRE, [str(GATE)], payload, harness, tmp_path)
        bare = direct(PRE, [str(GATE)], payload, harness, tmp_path)
        assert wrapped.returncode == 0, shown(wrapped.stderr)
        assert bare.returncode == 0, shown(bare.stderr)
        added.append(wrapped.seconds - bare.seconds)
        tool_seconds.append(bare.seconds)
    edited = tmp_path / "cs815_edited.py"
    edited.write_bytes(b'"""A clean module."""\n')
    lint = [str(LINT), "--files", str(edited)]
    lint_seconds = [direct(POST, lint, b"{}", harness, tmp_path).seconds for _ in range(3)]
    live_after = live_siblings_now(request.config)
    record_property("cs815_live_siblings_after", live_after)
    assert live_after == 0, "a sibling worker was live during the latency measurement"

    median = statistics.median(added)
    record_property("cs815_median_added_seconds", round(median, 3))
    wrapped_median = median + statistics.median(tool_seconds)
    record_property("cs815_wrapped_median_seconds", round(wrapped_median, 3))
    sys.stderr.write(f"CS-815 latency: median added {median:.3f}s over {LATENCY_CALLS} calls\n")
    assert median < LATENCY_BUDGET_SECONDS, f"the wrapper adds {median:.3f}s per call"

    bound, grace = wrapper_bound()
    pre_worst = bound + grace + max(tool_seconds)
    post_worst = bound + grace + max(lint_seconds)
    assert pre_worst < settings_timeout("PreToolUse"), f"PreToolUse worst case {pre_worst:.1f}s"
    assert post_worst < settings_timeout("PostToolUse"), f"PostToolUse worst case {post_worst:.1f}s"


# ---------------------------------------------------------------------------
# CS-1233 - the latency arm measures alone, and that isolation is pinned here.
# ---------------------------------------------------------------------------

# The synthetic pair the nested run drives. The busy file holds its worker for
# a few seconds; the measuring file records when it would start measuring.
QUIET_BUSY_SECONDS: Final = 4
QUIET_BUSY_SOURCE: Final = (
    "import os, time\n"
    "from pathlib import Path\n"
    "def test_busy():\n"
    "    out = Path(os.environ['CS1233_OUT'])\n"
    "    (out / 'busy_start').write_text(repr(time.time()))\n"
    "    (out / 'busy_worker').write_text(os.environ.get('PYTEST_XDIST_WORKER', ''))\n"
    "    time.sleep(" + str(QUIET_BUSY_SECONDS) + ")\n"
    "    (out / 'busy_end').write_text(repr(time.time()))\n"
)
QUIET_MEASURE_SOURCE: Final = (
    "import os, time\n"
    "from pathlib import Path\n"
    "from tests.xdist_quiet import await_quiet_siblings\n"
    "def test_measure(request):\n"
    "    out = Path(os.environ['CS1233_OUT'])\n"
    "    time.sleep(1)\n"
    "    if os.environ.get('CS1233_WAIT') == '1':\n"
    "        await_quiet_siblings(request.config)\n"
    "    (out / 'measure_start').write_text(repr(time.time()))\n"
    "    (out / 'measure_worker').write_text(os.environ.get('PYTEST_XDIST_WORKER', ''))\n"
)


def quiet_run(tmp_path: Path, *, wait: bool) -> dict[str, str]:
    """Run the synthetic pair on two xdist workers and return what each recorded."""
    tests_dir = tmp_path / "pair"
    out = tmp_path / "out"
    tests_dir.mkdir()
    out.mkdir()
    (tests_dir / "test_busy.py").write_text(QUIET_BUSY_SOURCE, encoding="ascii")
    (tests_dir / "test_measure.py").write_text(QUIET_MEASURE_SOURCE, encoding="ascii")
    env = {
        **os.environ,
        "CS1233_OUT": str(out),
        "CS1233_WAIT": "1" if wait else "0",
        "PYTHONPATH": str(REPO_ROOT),
    }
    env.pop("PYTEST_XDIST_WORKER", None)
    env.pop("PYTEST_ADDOPTS", None)
    argv = [sys.executable, "-m", "pytest", "-p", "tests.xdist_quiet", "-p", "no:cacheprovider"]
    argv += ["-n", "2", "--dist", "loadfile", "-q", str(tests_dir)]
    proc = subprocess.run(
        argv, capture_output=True, env=env, cwd=str(REPO_ROOT), timeout=CALL_TIMEOUT, check=False
    )
    status = proc.returncode
    assert status == 0, shown(proc.stdout + proc.stderr)
    return {path.name: path.read_text(encoding="ascii") for path in out.iterdir()}


@pytest.mark.parametrize("wait", [True, False], ids=["quiet", "control"])
def test_the_measurement_starts_only_after_every_sibling_worker_finished(
    tmp_path: Path, wait: bool
) -> None:
    """A measuring test that waits starts after its busy sibling ENDS.

    The control does not wait, and must start while the sibling is still busy -
    so the arm can see an overlap, and a barrier that never waits is red.
    Both files must land on different workers, or the order is trivially serial.
    """
    seen = quiet_run(tmp_path, wait=wait)
    distinct = seen["busy_worker"] != seen["measure_worker"]
    assert distinct, "the pair shared a worker, so the arm proves nothing"
    started_after_end = float(seen["measure_start"]) >= float(seen["busy_end"])
    assert started_after_end is wait, "the measurement did not wait for its sibling"


def test_a_sibling_holding_its_lock_is_live_until_its_process_dies(tmp_path: Path) -> None:
    """The lock, not a marker file, is the liveness signal - a killed worker frees it.

    The child takes its lock and is then ended without releasing it, as a crashed
    worker would be; the operating system must free the lock with the process.
    The prober's own lock is never counted.
    """
    directory = tmp_path / "live"
    own = hold_liveness_lock(directory, "gw0")
    child_source = (
        "import sys\n"
        "from pathlib import Path\n"
        "from tests.xdist_quiet import hold_liveness_lock\n"
        "hold_liveness_lock(Path(sys.argv[1]), 'gw1')\n"
        "sys.stdout.write('held\\n')\n"
        "sys.stdout.flush()\n"
        "sys.stdin.read()\n"
    )
    child = subprocess.Popen(
        [sys.executable, "-c", child_source, str(directory)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        cwd=str(REPO_ROOT),
    )
    try:
        ready = child.stdout is not None and child.stdout.readline().strip() == b"held"
        assert ready, "the child never took its lock"
        live_while_held = live_sibling_count(directory, "gw0")
        assert live_while_held == 1, "a held sibling lock was not counted live"
    finally:
        child.kill()
        child.wait(timeout=CALL_TIMEOUT)
    live_after_death = live_sibling_count(directory, "gw0")
    assert live_after_death == 0, "a dead sibling's lock was still counted live"
    release_liveness_lock(own)


def test_a_released_sibling_lock_is_not_live_and_outside_xdist_nothing_waits(
    tmp_path: Path, request: pytest.FixtureRequest
) -> None:
    """A worker that finished released its lock; a run with no workers waits for nothing."""
    directory = tmp_path / "live"
    sibling = hold_liveness_lock(directory, "gw1")
    live_held = live_sibling_count(directory, "gw0")
    release_liveness_lock(sibling)
    live_released = live_sibling_count(directory, "gw0")
    assert (live_held, live_released) == (1, 0), "release did not end liveness"
    if getattr(request.config, "workerinput", None) is None:
        waited = await_quiet_siblings(request.config)
        assert waited == 0.0, "a run with no workers waited"
