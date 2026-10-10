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
    settings     the two command values are the only bytes that moved, beside
                 the one Stop array CS-1272's grant adds (docs/LEDGER.md,
                 "2026-10-08 - FLEET-KIT v9", part 2) and the one PreToolUse
                 SUBAGENT-FIRST entry CS-1282's grant adds after the gate's
                 (docs/LEDGER.md, "2026-10-08 - CS-1282"), each pinned whole; no
                 settings file carries a display key; .gitignore ignores the
                 /done marker and its seen file, and the SUBAGENT-FIRST hook's
                 mode file and decision log
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

import ast
import hashlib
import json
import os
import re
import statistics
import subprocess
import sys
import threading
import time
import uuid
from collections.abc import Callable
from functools import cache
from pathlib import Path
from types import SimpleNamespace
from typing import Final, NamedTuple, cast

import pytest
from ops.fleet_kit import fleet_subagent_first as subagent_first_kit

from tests import xdist_quiet
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
LOCAL_SETTINGS: Final = REPO_ROOT / ".claude" / "settings.local.json"
GITIGNORE: Final = REPO_ROOT / ".gitignore"

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

# CS-1272 - THE SECOND GRANT, docs/LEDGER.md "2026-10-08 - FLEET-KIT v9", part 2:
# exactly one "Stop" array after "PostToolUse" inside "hooks", holding one
# command hook that runs the vendored kit's stop-hook. NOT routed through
# tools/claude_hook.sh - its leg check refuses an unknown leg, so every Stop
# would exit 1. `|| true` and the anchor are conditions of the grant.
STOP_COMMAND: Final = 'python "$CLAUDE_PROJECT_DIR/ops/fleet_kit/fleet_done.py" stop-hook || true'
# The grant bounds the timeout to 20..45 s. 45 is chosen: fleet_done.py's git
# calls carry a 15 s timeout each, two on the marker-present path (30 s plus
# interpreter start), and the commit body records the measurement.
STOP_TIMEOUT_FLOOR: Final = 20
STOP_TIMEOUT_CEILING: Final = 45
STOP_TIMEOUT: Final = 45
# The inserted bytes, whole. The settings arm REMOVES them before taking the
# base digest, so that one digest still pins every byte outside the grant.
STOP_INSERTION: Final = (
    ',\n    "Stop": [\n      {\n        "hooks": [\n          {\n'
    '            "type": "command",\n'
    f'            "command": {json.dumps(STOP_COMMAND)},\n'
    f'            "timeout": {STOP_TIMEOUT}\n'
    "          }\n        ]\n      }\n    ]"
).encode("ascii")
HOOK_EVENT_ORDER: Final = ["PreToolUse", "PostToolUse", "SubagentStop", "Stop"]

# CS-1282 - THE THIRD GRANT, docs/LEDGER.md "2026-10-08 - CS-1282 - FROZEN-FILE
# GRANT": ONE PreToolUse entry appended AFTER the gate entry, holding one command
# hook that runs the fleet kit's SUBAGENT-FIRST hook (v10, carried at v11 by
# CS-1287, whose ORDER rules this anchored `|| true` form conformant). Anchored
# at the project dir and closed by `|| true`, both conditions of the grant: MAIN's literal
# relative command exits 2 from a foreign cwd, a harness deny of every guarded
# call. The kit hook denies by the JSON it prints, never by its exit status.
GATE_MATCHER: Final = "Bash|PowerShell"
SUBAGENT_FIRST_MATCHER: Final = "Bash|PowerShell|Read|Edit|Write|Grep|Glob|NotebookEdit|MultiEdit"
SUBAGENT_FIRST_COMMAND: Final = (
    'python "$CLAUDE_PROJECT_DIR/ops/fleet_kit/fleet_subagent_first.py" || true'
)
SUBAGENT_FIRST_TIMEOUT: Final = 10
SUBAGENT_FIRST_KIT_FILE: Final = REPO_ROOT / "ops" / "fleet_kit" / "fleet_subagent_first.py"
# The inserted bytes, whole, removed by the settings arm exactly as the Stop
# array is, so the one base digest still pins every byte outside the grants.
SUBAGENT_FIRST_INSERTION: Final = (
    ",\n      {\n"
    f'        "matcher": {json.dumps(SUBAGENT_FIRST_MATCHER)},\n'
    '        "hooks": [\n          {\n'
    '            "type": "command",\n'
    f'            "command": {json.dumps(SUBAGENT_FIRST_COMMAND)},\n'
    f'            "timeout": {SUBAGENT_FIRST_TIMEOUT}\n'
    "          }\n        ]\n      }"
).encode("ascii")
# CS-1290 - THE FOURTH GRANT, docs/LEDGER.md "2026-10-09 - CS-1290 - frozen-file
# GRANT": kit v13 carries the v12 RACE GUARDS hooks. Part A: ONE PreToolUse entry
# appended AFTER the SUBAGENT-FIRST entry running the claims hook, and ONE
# SubagentStop array between PostToolUse and Stop running its release-hook - both
# command strings EXACTLY as the v12 ORDER section 3 spells them, timeout 10 -
# and the top-level attribution and includeCoAuthoredBy keys REMOVED: v13 makes
# both tree_forbidden (FLEET-COMMON 17), and the account settings carry them.
CLAIMS_MATCHER: Final = "Edit|Write|NotebookEdit|MultiEdit|Bash|PowerShell"
CLAIMS_COMMAND: Final = 'python "$CLAUDE_PROJECT_DIR/ops/fleet_kit/fleet_claims.py" hook'
RELEASE_COMMAND: Final = 'python "$CLAUDE_PROJECT_DIR/ops/fleet_kit/fleet_claims.py" release-hook'
CLAIMS_TIMEOUT: Final = 10
CLAIMS_KIT_FILE: Final = REPO_ROOT / "ops" / "fleet_kit" / "fleet_claims.py"
CLAIMS_INSERTION: Final = (
    ",\n      {\n"
    f'        "matcher": {json.dumps(CLAIMS_MATCHER)},\n'
    '        "hooks": [\n          {\n'
    '            "type": "command",\n'
    f'            "command": {json.dumps(CLAIMS_COMMAND)},\n'
    f'            "timeout": {CLAIMS_TIMEOUT}\n'
    "          }\n        ]\n      }"
).encode("ascii")
SUBAGENT_STOP_INSERTION: Final = (
    ',\n    "SubagentStop": [\n      {\n        "hooks": [\n          {\n'
    '            "type": "command",\n'
    f'            "command": {json.dumps(RELEASE_COMMAND)},\n'
    f'            "timeout": {CLAIMS_TIMEOUT}\n'
    "          }\n        ]\n      }\n    ]"
).encode("ascii")
# The two top-level lines the grant REMOVED, and the line they followed. The
# settings arm puts them back before taking the base digest.
SCHEMA_LINE: Final = b'  "$schema": "https://json.schemastore.org/claude-code-settings.json",\n'
ATTRIBUTION_REMOVAL: Final = (
    b'  "attribution": { "commit": "", "pr": "" },\n  "includeCoAuthoredBy": false,\n'
)
# The keys v13's cli_display.json lists as tree_forbidden beyond DISPLAY_KEYS.
ATTRIBUTION_KEYS: Final = ("attribution", "includeCoAuthoredBy")
# The wrapper-routed entry of each event, selected by its matcher: PreToolUse
# carries two entries from CS-1282 on, and the CS-815 arms grade the gate's.
WRAPPED_MATCHERS: Final = {"PreToolUse": GATE_MATCHER, "PostToolUse": "Edit|Write|MultiEdit"}

# Claude Code DISPLAY keys. FLEET item 15 (kit v9): display keys live only in
# the two account settings, from `ops/fleet_kit/cli_display.json`, and "a tree
# sets none" - so no settings file here may set one, top level or nested.
DISPLAY_KEYS: Final = frozenset(
    {
        "statusLine",
        "subagentStatusLine",
        "theme",
        "spinnerVerbs",
        "spinnerTipsEnabled",
        "prefersReducedMotion",
        "outputStyle",
        "showTurnDuration",
    }
)

# The kit's /done marker and its Stop-hook dedupe file (fleet_done.py
# MARKER_REL and SEEN_REL). Runtime state, LOCAL-ONLY, named explicitly.
DONE_MARKER_IGNORES: Final = (
    "/ops/loop/control/session_done.json",
    "/ops/loop/control/session_done.seen",
)

# CS-1282 - the SUBAGENT-FIRST hook's mode file and decision log, read from the
# vendored kit's own MODE_REL and LOG_REL so the ignore lines cannot drift from
# the paths the hook writes. Runtime state, LOCAL-ONLY, named explicitly.
SUBAGENT_FIRST_IGNORES: Final = tuple(
    "/" + rel.as_posix() for rel in (subagent_first_kit.MODE_REL, subagent_first_kit.LOG_REL)
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
def alone(harness: Environment, request: pytest.FixtureRequest) -> Environment:
    """The harness environment, handed over only once every sibling worker has finished.

    THE WRAPPER BOUNDS ITS WHOLE LADDER BY ONE CS_PROBE_BOUND, and an arm that
    grades a pass-through, a deny or a NAMED refusal grades a verdict that exists
    only if that ladder FINISHES inside it. Each rung is about ten process starts,
    and beside CPU-bound sibling workers those starts slowed past the bound: tier2
    run 37919155122 read "the interpreter ladder did not finish inside its bound"
    from the liar arm, three rungs, on the windows guard shard. The same arm is
    green alone and red beside a CPU-bound sibling worker, so the number graded
    was the sibling load. CS-1233's barrier removes it; the bound does not move.
    """
    await_quiet_siblings(request.config)
    return harness


@pytest.fixture
def pinned(alone: Environment) -> Environment:
    """The quiet harness environment with the ladder pinned at the running interpreter."""
    return extended(alone, **{ENV_NAME: sys.executable})


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


def wrapped_entries(config: dict, event: str) -> list[dict]:
    """The entries of one event the wrapper arms grade, selected by matcher.

    An event with no matcher on record (Stop) keeps every entry it has.
    """
    matcher = WRAPPED_MATCHERS.get(event)
    return [
        entry
        for entry in config["hooks"][event]
        if matcher is None or entry.get("matcher") == matcher
    ]


def hook_command(config: dict, event: str) -> str:
    """The single command wired under one hook event's wrapper-routed entry."""
    commands = [
        hook["command"] for entry in wrapped_entries(config, event) for hook in entry["hooks"]
    ]
    assert len(commands) == 1, f"{event} carries {len(commands)} commands, not one"
    return str(commands[0])


def test_settings_routes_both_hooks_through_the_wrapper() -> None:
    """The two command values, exactly as the grant scopes them."""
    config = json.loads(SETTINGS.read_bytes().decode("utf-8"))
    assert hook_command(config, "PreToolUse") == NEW_PRE_COMMAND
    assert hook_command(config, "PostToolUse") == NEW_POST_COMMAND


def test_settings_moved_no_byte_but_the_two_command_values() -> None:
    """Undo every later grant, swap the two values back: the grant's base, by digest.

    CS-1272's grant adds one Stop array, CS-1282's one PreToolUse entry, and
    CS-1290's one more PreToolUse entry and one SubagentStop array while removing
    the two attribution lines. Each insertion is pinned WHOLE and removed here and
    the removed lines are put back, so the CS-815 base digest still pins every
    byte outside the grants; where each sits is the order arms'.
    """
    raw = SETTINGS.read_bytes()
    assert raw.count(STOP_INSERTION) == 1, "the granted Stop array is not present exactly once"
    raw = raw.replace(STOP_INSERTION, b"")
    assert raw.count(SUBAGENT_FIRST_INSERTION) == 1, (
        "the granted SUBAGENT-FIRST entry is not present exactly once"
    )
    raw = raw.replace(SUBAGENT_FIRST_INSERTION, b"")
    assert raw.count(CLAIMS_INSERTION) == 1, "the granted claims entry is not present exactly once"
    raw = raw.replace(CLAIMS_INSERTION, b"")
    assert raw.count(SUBAGENT_STOP_INSERTION) == 1, (
        "the granted SubagentStop array is not present exactly once"
    )
    raw = raw.replace(SUBAGENT_STOP_INSERTION, b"")
    assert raw.count(ATTRIBUTION_REMOVAL) == 0, "the removed attribution keys are back"
    assert raw.count(SCHEMA_LINE) == 1, "the schema line is not present exactly once"
    raw = raw.replace(SCHEMA_LINE, SCHEMA_LINE + ATTRIBUTION_REMOVAL)
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
        "a byte outside the two command values and the Stop array moved - the schema "
        "key, attribution, includeCoAuthoredBy, env, permissions, a matcher or a timeout"
    )


def test_settings_wires_exactly_the_granted_stop_hook() -> None:
    """CS-1272: one Stop entry after PostToolUse, one command hook, the granted shape."""
    config = json.loads(SETTINGS.read_bytes().decode("utf-8"))
    assert list(config["hooks"]) == HOOK_EVENT_ORDER, "the hook events are not in grant order"
    entries = config["hooks"]["Stop"]
    assert [sorted(entry) for entry in entries] == [["hooks"]], "Stop is not one matcher-less entry"
    hooks = entries[0]["hooks"]
    assert [sorted(hook) for hook in hooks] == [["command", "timeout", "type"]], (
        "the Stop entry does not hold exactly one hook of type, command and timeout"
    )
    hook = hooks[0]
    assert hook["type"] == "command"
    assert hook["command"] == STOP_COMMAND, "the Stop command is not the granted string"
    assert hook["command"].startswith('python "$CLAUDE_PROJECT_DIR/'), "the anchor was dropped"
    assert hook["command"].endswith(" || true"), "the grant's || true was dropped"
    timeout = hook["timeout"]
    assert isinstance(timeout, int), "the Stop timeout is not an integer"
    assert STOP_TIMEOUT_FLOOR <= timeout <= STOP_TIMEOUT_CEILING, "outside the granted 20..45 s"
    assert timeout == settings_timeout("Stop") == STOP_TIMEOUT


def test_settings_wires_exactly_the_granted_subagent_first_hook() -> None:
    """CS-1282: the gate entry first, then ONE SUBAGENT-FIRST entry in the granted shape."""
    config = json.loads(SETTINGS.read_bytes().decode("utf-8"))
    entries = config["hooks"]["PreToolUse"]
    matchers = [entry.get("matcher") for entry in entries]
    assert matchers == [GATE_MATCHER, SUBAGENT_FIRST_MATCHER, CLAIMS_MATCHER], (
        "not the gate, then SUBAGENT-FIRST, then the claims hook"
    )
    entry = entries[1]
    assert sorted(entry) == ["hooks", "matcher"], "the entry carries a key beyond the grant"
    hooks = entry["hooks"]
    assert [sorted(hook) for hook in hooks] == [["command", "timeout", "type"]], (
        "the entry does not hold exactly one hook of type, command and timeout"
    )
    hook = hooks[0]
    assert hook["type"] == "command"
    assert hook["command"] == SUBAGENT_FIRST_COMMAND, "the command is not the granted string"
    assert hook["command"].startswith('python "$CLAUDE_PROJECT_DIR/'), "the anchor was dropped"
    assert hook["command"].endswith(" || true"), "the grant's || true was dropped"
    timeout = hook["timeout"]
    assert isinstance(timeout, int), "the SUBAGENT-FIRST timeout is not an integer"
    assert timeout == SUBAGENT_FIRST_TIMEOUT
    named = hook["command"].split('"')[1].replace("$CLAUDE_PROJECT_DIR/", "")
    assert (REPO_ROOT / named).resolve() == SUBAGENT_FIRST_KIT_FILE.resolve()
    assert SUBAGENT_FIRST_KIT_FILE.is_file(), "the vendored kit hook is missing"


def test_settings_wires_exactly_the_granted_claims_hooks() -> None:
    """CS-1290 grant A: the claims hook and its release-hook, the v12 strings exactly."""
    config = json.loads(SETTINGS.read_bytes().decode("utf-8"))
    claims = config["hooks"]["PreToolUse"][2]
    release = config["hooks"]["SubagentStop"]
    assert sorted(claims) == ["hooks", "matcher"], "the claims entry carries a key beyond the grant"
    assert claims["matcher"] == CLAIMS_MATCHER
    assert [sorted(entry) for entry in release] == [["hooks"]], "SubagentStop is not one entry"
    for entry, command in ((claims, CLAIMS_COMMAND), (release[0], RELEASE_COMMAND)):
        hooks = entry["hooks"]
        assert [sorted(hook) for hook in hooks] == [["command", "timeout", "type"]]
        hook = hooks[0]
        assert hook["type"] == "command"
        assert hook["command"] == command, "the command is not the granted string"
        assert hook["timeout"] == CLAIMS_TIMEOUT
        named = hook["command"].split('"')[1].replace("$CLAUDE_PROJECT_DIR/", "")
        assert (REPO_ROOT / named).resolve() == CLAIMS_KIT_FILE.resolve()
    assert CLAIMS_KIT_FILE.is_file(), "the vendored claims hook is missing"


def test_no_settings_file_sets_an_attribution_key() -> None:
    """CS-1290, FLEET-COMMON 17: v13 makes both attribution keys tree_forbidden."""
    kit = json.loads((REPO_ROOT / "ops" / "fleet_kit" / "cli_display.json").read_bytes())
    assert set(ATTRIBUTION_KEYS) <= set(kit["tree_forbidden"]), "the kit no longer forbids them"
    present = [path for path in (SETTINGS, LOCAL_SETTINGS) if path.is_file()]
    found = {
        path.name: sorted(set(ATTRIBUTION_KEYS) & set(json.loads(path.read_bytes())))
        for path in present
    }
    assert all(keys == [] for keys in found.values()), f"attribution keys set: {found}"


def display_key_paths(node: object, where: str = "") -> list[str]:
    """Every display key at any depth, as a key path. Never a value (rule 13)."""
    found: list[str] = []
    if isinstance(node, dict):
        for key, value in node.items():
            here = f"{where}/{key}"
            if key in DISPLAY_KEYS:
                found.append(here)
            found.extend(display_key_paths(value, here))
    elif isinstance(node, list):
        for index, value in enumerate(node):
            found.extend(display_key_paths(value, f"{where}[{index}]"))
    return found


def test_the_display_key_walk_finds_a_top_level_and_a_nested_key() -> None:
    """The positive control: a walk that saw nothing would pass the arm below vacuously."""
    planted = {"theme": 1, "hooks": {"Stop": [{"hooks": [{"statusLine": {}}]}]}}
    assert display_key_paths(planted) == ["/theme", "/hooks/Stop[0]/hooks[0]/statusLine"]


def test_no_settings_file_carries_a_display_key() -> None:
    """Both settings files, the gitignored local one whenever it is present."""
    assert SETTINGS.is_file(), "the tracked settings file is missing"
    present = [path for path in (SETTINGS, LOCAL_SETTINGS) if path.is_file()]
    found = {
        path.name: display_key_paths(json.loads(path.read_bytes().decode("utf-8")))
        for path in present
    }
    assert all(paths == [] for paths in found.values()), f"display keys set: {found}"


def test_gitignore_carries_the_done_marker_and_its_seen_file() -> None:
    """The kit's /done marker and its dedupe file are LOCAL-ONLY runtime state."""
    lines = GITIGNORE.read_bytes().decode("ascii").splitlines()
    missing = [entry for entry in DONE_MARKER_IGNORES if lines.count(entry) != 1]
    assert missing == [], f".gitignore does not carry exactly once: {missing}"


def test_gitignore_carries_the_race_guard_and_identity_runtime_state() -> None:
    """CS-1290: the v12 and v13 ORDERs' runtime paths are LOCAL-ONLY, each named once."""
    lines = GITIGNORE.read_bytes().decode("ascii").splitlines()
    wanted = (
        "/ops/loop/control/claims/",
        "/ops/loop/control/locks/",
        "/ops/loop/control/claims.jsonl",
        "/ops/loop/control/claims.mode",
        "/ops/loop/control/gitlock.jsonl",
        "/ops/loop/control/identity.jsonl",
    )
    missing = [entry for entry in wanted if lines.count(entry) != 1]
    assert missing == [], f".gitignore does not carry exactly once: {missing}"


def test_gitignore_carries_the_subagent_first_mode_file_and_its_log() -> None:
    """CS-1282: the hook's mode file and decision log are LOCAL-ONLY runtime state."""
    lines = GITIGNORE.read_bytes().decode("ascii").splitlines()
    named = SUBAGENT_FIRST_IGNORES == (
        "/ops/loop/control/subagent_first.mode",
        "/ops/loop/control/subagent_first.jsonl",
    )
    missing = [entry for entry in SUBAGENT_FIRST_IGNORES if lines.count(entry) != 1]
    assert (named, missing) == (True, []), f".gitignore does not carry exactly once: {missing}"


def settings_timeout(event: str) -> int:
    config = json.loads(SETTINGS.read_bytes().decode("utf-8"))
    timeouts = [
        hook["timeout"] for entry in wrapped_entries(config, event) for hook in entry["hooks"]
    ]
    assert len(timeouts) == 1
    return int(timeouts[0])


def test_the_settings_commands_run_under_a_shell_like_the_harness(
    tmp_path: Path,
    alone: Environment,
) -> None:
    """The command STRINGS, handed to a shell with the anchor in its environment.

    Spawned from tmp_path, never the repository root, so the anchor is what
    finds both files. A benign call passes, a known deny is denied with the
    gate's own words, and the PostToolUse leg lints a clean file.
    """
    config = json.loads(SETTINGS.read_bytes().decode("utf-8"))
    env = extended(alone, CLAUDE_PROJECT_DIR=str(REPO_ROOT))
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
    alone: Environment,
) -> None:
    """With the ladder left to itself, the windowed leg runs pythonw and the other does not."""
    stub = tmp_path / "cs815_stub.py"
    stub.write_bytes(STUB_SOURCE.encode("ascii"))
    names = {}
    for leg in (PRE, POST):
        result = via_wrapper(leg, [str(stub)], b"", alone, tmp_path)
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
    alone: Environment,
    program: str,
    leg: str,
) -> None:
    """Each program the ladder test names, pointed at through the variable."""
    env = extended(alone, **{ENV_NAME: program})
    tool = [str(GATE)] if leg == PRE else [str(LINT), "--files", str(tmp_path / "x.py")]
    payload = json.dumps(envelope("echo " + EM_DASH)).encode("utf-8")
    result = via_wrapper(leg, tool, payload, env, tmp_path)
    line = assert_loud(result, env, extra=(program,))
    assert "pinned interpreter variable failed the probe" in line, shown(line)


def test_a_liar_on_every_rung_is_loudly_reported(
    tmp_path: Path,
    alone: Environment,
) -> None:
    """No variable set: every ladder rung on PATH forwards output and drops the status.

    Three rungs run inside the wrapper's one bound - the most process starts of
    any arm - so this is the arm sibling load pushed past it first (``alone``).
    """
    shadow = tmp_path / "allrungs"
    for rung in LADDER_RUNGS:
        write_shim(shadow, rung, LIAR_SHIM)
    env = path_first(alone, shadow)
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
    alone: Environment,
) -> None:
    """A candidate that never answers costs at most the bound plus the grace.

    The slack past the bound is the wrapper's own process starts, and beside a
    CPU-bound sibling worker those outgrew it - so this arm waits too (``alone``).
    """
    hang = write_shim(tmp_path / "hang", "hang.sh", "#!/bin/sh\nsleep 60\n")
    env = extended(alone, **{ENV_NAME: hang.as_posix()})
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


class QuietChild(NamedTuple):
    """One nested run of the synthetic pair: its status, its output, and its record directory."""

    status: int
    output: bytes
    out: Path


def quiet_child(tmp_path: Path, *, wait: bool, plugin: Path | None = None) -> QuietChild:
    """Run the synthetic pair on two xdist workers, adding ``plugin`` (a module file) if given."""
    tests_dir = tmp_path / "pair"
    out = tmp_path / "out"
    tests_dir.mkdir()
    out.mkdir()
    (tests_dir / "test_busy.py").write_text(QUIET_BUSY_SOURCE, encoding="ascii")
    (tests_dir / "test_measure.py").write_text(QUIET_MEASURE_SOURCE, encoding="ascii")
    search = [str(REPO_ROOT)] + ([str(plugin.parent)] if plugin is not None else [])
    env = {
        **os.environ,
        "CS1233_OUT": str(out),
        "CS1233_WAIT": "1" if wait else "0",
        "PYTHONPATH": os.pathsep.join(search),
    }
    env.pop("PYTEST_XDIST_WORKER", None)
    env.pop("PYTEST_ADDOPTS", None)
    argv = [sys.executable, "-m", "pytest", "-p", "tests.xdist_quiet", "-p", "no:cacheprovider"]
    if plugin is not None:
        argv += ["-p", plugin.stem]
    # CS-1300: the conftest cut at the collected directory itself. Launched from
    # the repository's drive, the run found no common ancestor with the temp
    # path, so its cut stayed at the repository and pytest collected EVERY
    # ancestor of the temp path, lstat-ing each sibling there - and a sibling
    # another process deleted mid-collection ended the run at an os.lstat
    # FileNotFoundError. Cut here, no ancestor and no sibling is ever read.
    argv += ["-n", "2", "--dist", "loadfile", "-q", f"--confcutdir={tests_dir}", str(tests_dir)]
    proc = subprocess.run(
        argv, capture_output=True, env=env, cwd=str(REPO_ROOT), timeout=CALL_TIMEOUT, check=False
    )
    return QuietChild(proc.returncode, proc.stdout + proc.stderr, out)


def quiet_run(tmp_path: Path, *, wait: bool) -> dict[str, str]:
    """Run the synthetic pair on two xdist workers and return what each recorded."""
    child = quiet_child(tmp_path, wait=wait)
    status = child.status
    assert status == 0, shown(child.output)
    return {path.name: path.read_text(encoding="ascii") for path in child.out.iterdir()}


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


# CS-1300 - a sibling of the collected directory, deleted while collection runs.
DOOMED_SIBLING: Final = "cs1300_doomed"
DOOM_PLUGIN_SOURCE: Final = (
    "import shutil\n"
    "def pytest_collect_directory(path, parent):\n"
    "    if path.name == " + repr(DOOMED_SIBLING) + ":\n"
    "        shutil.rmtree(path, ignore_errors=True)\n"
)


def test_a_sibling_deleted_mid_collection_never_reaches_the_nested_run(tmp_path: Path) -> None:
    """The nested run never reads a sibling of the directory it collects.

    CS-1300. The nested run starts from the repository's drive and collects a
    temp path on another, so pytest found no common ancestor, kept its conftest
    cut at the repository and collected EVERY ancestor of the temp path - and on
    Windows lstat'ed each sibling at each level while matching the path. A
    sibling another process deleted between the listing and the lstat ended
    the run at exit 2 with an os.lstat FileNotFoundError, about one run in ten.
    Here a plugin deletes one at that instant, every time.
    """
    (tmp_path / DOOMED_SIBLING).mkdir()
    plugin = tmp_path / "plugins" / "cs1300_doom.py"
    plugin.parent.mkdir()
    plugin.write_text(DOOM_PLUGIN_SOURCE, encoding="ascii")
    child = quiet_child(tmp_path, wait=False, plugin=plugin)
    status = child.status
    named = b"lstat" in child.output
    assert status == 0, f"the nested run failed: exit {status}, lstat named: {named}"


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


# ---------------------------------------------------------------------------
# Tier2 run 37919155122 - an arm whose verdict needs the ladder to FINISH runs alone.
# ---------------------------------------------------------------------------

# The wrapper bounds its WHOLE ladder by one CS_PROBE_BOUND. These arms reach the
# wrapper's environment but grade nothing that depends on wall time - no ladder
# runs in either - so they may share the box with sibling workers. Every OTHER arm
# that reaches `harness` must request `alone`, directly or through `pinned`, or
# wait itself. The hanging-candidate arm is NOT here: the slack it grades past the
# bound is process starts, and beside a CPU-bound sibling it overran.
LOAD_TOLERANT_ARMS: Final = {
    "test_a_foreign_bounding_program_is_loudly_reported": "the outer timeout is the foreign one",
    "test_an_unnamed_leg_is_loudly_reported": "refused before any ladder runs",
}
QUIET_FIXTURE: Final = "alone"
HARNESS_FIXTURE: Final = "harness"
QUIET_CALL: Final = "await_quiet_siblings"

# How long two waiting workers get to both come back before the arm calls it a
# deadlock. A sound barrier returns within a few polls of POLL_SECONDS each.
DEADLOCK_SECONDS: Final = 10.0


class ModuleArms(NamedTuple):
    """This module's own functions, read from its source, never from a collection."""

    functions: dict[str, ast.FunctionDef]
    fixtures: frozenset[str]


def is_fixture_decorator(node: ast.expr) -> bool:
    """``@pytest.fixture`` bare or called."""
    target = node.func if isinstance(node, ast.Call) else node
    return (
        isinstance(target, ast.Attribute)
        and target.attr == "fixture"
        and isinstance(target.value, ast.Name)
        and target.value.id == "pytest"
    )


def module_arms(source: Path | None = None) -> ModuleArms:
    """Every top-level function of ``source`` (this file by default), and its fixtures."""
    tree = ast.parse((source or Path(__file__)).read_bytes().decode("utf-8"))
    functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
    fixtures = frozenset(
        name
        for name, node in functions.items()
        if any(is_fixture_decorator(decorator) for decorator in node.decorator_list)
    )
    return ModuleArms(functions, fixtures)


def requested_fixtures(node: ast.FunctionDef) -> list[str]:
    """What a function asks for by name: its arguments, and each ``usefixtures`` mark."""
    names = [arg.arg for arg in node.args.args]
    for decorator in node.decorator_list:
        if (
            isinstance(decorator, ast.Call)
            and isinstance(decorator.func, ast.Attribute)
            and decorator.func.attr == "usefixtures"
        ):
            names.extend(
                arg.value
                for arg in decorator.args
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str)
            )
    return names


def fixture_closure(arms: ModuleArms, name: str) -> frozenset[str]:
    """The fixtures a function requests, followed through every fixture defined here."""
    seen: set[str] = set()
    pending = requested_fixtures(arms.functions[name])
    while pending:
        current = pending.pop()
        if current in seen:
            continue
        seen.add(current)
        if current in arms.fixtures:
            pending.extend(requested_fixtures(arms.functions[current]))
    return frozenset(seen)


def waits_itself(node: ast.FunctionDef) -> bool:
    """Whether a function's own body calls the barrier."""
    return any(
        isinstance(call, ast.Call)
        and isinstance(call.func, ast.Name)
        and call.func.id == QUIET_CALL
        for call in ast.walk(node)
    )


def waiting_arms(arms: ModuleArms) -> dict[str, bool]:
    """Every test that reaches the harness, mapped to whether it waits for quiet siblings."""
    return {
        name: QUIET_FIXTURE in closure or waits_itself(node)
        for name, node in arms.functions.items()
        if name.startswith("test_")
        for closure in [fixture_closure(arms, name)]
        if HARNESS_FIXTURE in closure
    }


def test_every_arm_whose_verdict_needs_the_ladder_to_finish_runs_alone() -> None:
    """Every harness arm waits for quiet siblings, or is a named load-tolerant one.

    The liar arm read "the interpreter ladder did not finish inside its bound" on
    the windows guard shard: three rungs of process starts, slowed past the one
    bound by CPU-bound sibling workers. Every arm that grades a pass-through, a
    deny or a NAMED refusal needs that same ladder to finish, so each waits.
    """
    arms = module_arms()
    reached = waiting_arms(arms)
    walked = "test_a_liar_on_every_rung_is_loudly_reported" in reached
    assert walked, "the walk found no harness arm, so it proves nothing"
    stale = sorted(set(LOAD_TOLERANT_ARMS) - set(reached))
    assert stale == [], f"a load-tolerant entry names no harness arm here: {stale}"
    unguarded = sorted(
        name for name, waits in reached.items() if not waits and name not in LOAD_TOLERANT_ARMS
    )
    assert unguarded == [], f"these arms need the ladder to finish, beside siblings: {unguarded}"
    tolerant_but_waiting = sorted(name for name in LOAD_TOLERANT_ARMS if reached[name])
    assert tolerant_but_waiting == [], f"a load-tolerant arm waits anyway: {tolerant_but_waiting}"
    defined = QUIET_FIXTURE in arms.fixtures
    assert defined, f"no {QUIET_FIXTURE!r} fixture is defined here"


# CS-814's wrapper arms drive the SAME ladder through tools/claude_hook.sh, from
# their own module and with no `harness` fixture: they reach it through that
# module's `run_wrapper`. The walk above reads only this file, so it never saw
# them; this one reads theirs.
ENV_ECHO_MODULE: Final = REPO_ROOT / "tests" / "test_hook_env_echo.py"
WRAPPER_DRIVER: Final = "run_wrapper"
ENV_ECHO_WRAPPER_ARMS: Final = (
    "test_no_claude_hook_path_echoes_a_canary",
    "test_a_wrapper_copy_that_dumps_the_environment_is_caught",
)


def call_closure(arms: ModuleArms, name: str) -> frozenset[str]:
    """The module functions ``name`` calls by name, followed through each of them."""
    seen: set[str] = set()
    pending = [name]
    while pending:
        current = pending.pop()
        if current in seen:
            continue
        seen.add(current)
        pending.extend(
            node.func.id
            for node in ast.walk(arms.functions[current])
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id in arms.functions
        )
    return frozenset(seen)


def waits_through_a_fixture(arms: ModuleArms, name: str) -> bool:
    """Whether a test waits itself, or requests a fixture defined beside it that waits."""
    requested = fixture_closure(arms, name) & arms.fixtures
    own = waits_itself(arms.functions[name])
    return own or any(waits_itself(arms.functions[fixture]) for fixture in requested)


def test_every_env_echo_arm_that_drives_the_wrapper_runs_alone() -> None:
    """Every test of tests/test_hook_env_echo.py that drives the wrapper waits too.

    Its wrapper arms run the whole interpreter ladder inside the one bound - an
    allow, a deny, a lint pass and a named refusal are each a verdict only once
    the ladder FINISHES - beside the same CPU-bound siblings.
    """
    arms = module_arms(ENV_ECHO_MODULE)
    reached = {
        name: waits_through_a_fixture(arms, name)
        for name in arms.functions
        if name.startswith("test_") and WRAPPER_DRIVER in call_closure(arms, name)
    }
    missing = sorted(set(ENV_ECHO_WRAPPER_ARMS) - set(reached))
    assert missing == [], f"the walk missed these wrapper arms, so it proves nothing: {missing}"
    unguarded = sorted(name for name, waits in reached.items() if not waits)
    assert unguarded == [], f"these arms drive the wrapper beside busy siblings: {unguarded}"
    assert env_echo_tests_after_the_first_wait(arms) == [], (
        "these tests follow a waiting arm, so they run alone for no reason: "
        f"{env_echo_tests_after_the_first_wait(arms)}"
    )


def env_echo_tests_after_the_first_wait(arms: ModuleArms) -> list[str]:
    """The tests that do not wait but sit below the module's first test that does.

    A worker past its first wait runs on alone, so each such test is serialised
    behind every sibling for nothing: the waiting arms belong at the foot.
    """
    tests = [name for name in arms.functions if name.startswith("test_")]
    waiting = [waits_through_a_fixture(arms, name) for name in tests]
    first = waiting.index(True) if True in waiting else len(tests)
    return [name for name, waits in zip(tests[first:], waiting[first:], strict=True) if not waits]


def fake_worker(run_id: str, worker: str) -> SimpleNamespace:
    """The two attributes of an xdist worker's config the barrier reads."""
    return SimpleNamespace(
        workerinput={"testrunuid": run_id, "workerid": worker}, stash=pytest.Stash()
    )


def test_two_waiting_workers_never_wait_on_each_other() -> None:
    """Two arms that wait, on two workers, both come back - neither waits on the other.

    A scheduler other than --dist loadfile splits one file's arms across workers,
    so two waiters can be live at once. A waiter that stayed live while it waited
    would see the other as busy, and each would wait for the other for ever.
    """
    run_id = "cs815-two-waiters-" + uuid.uuid4().hex
    workers = {name: fake_worker(run_id, name) for name in ("gw0", "gw1")}
    sessions = {name: SimpleNamespace(config=worker) for name, worker in workers.items()}
    for session in sessions.values():
        xdist_quiet.pytest_sessionstart(cast(pytest.Session, session))
    returned: dict[str, float] = {}
    crashed: dict[str, str] = {}

    def worker_run(name: str) -> None:
        try:
            returned[name] = await_quiet_siblings(cast(pytest.Config, workers[name]))
        except Exception as exc:  # surfaced by the assert below, never swallowed
            crashed[name] = error_shape(exc)
        finally:
            xdist_quiet.pytest_sessionfinish(cast(pytest.Session, sessions[name]))

    threads = [threading.Thread(target=worker_run, args=(name,), daemon=True) for name in workers]
    try:
        for thread in threads:
            thread.start()
        deadline = time.monotonic() + DEADLOCK_SECONDS
        for thread in threads:
            thread.join(max(0.0, deadline - time.monotonic()))
        stuck = sorted(name for name in workers if name not in returned and name not in crashed)
    finally:
        # A stuck waiter is freed by ending both sessions, so no thread outlives the arm.
        for session in sessions.values():
            xdist_quiet.pytest_sessionfinish(cast(pytest.Session, session))
        for thread in threads:
            thread.join(DEADLOCK_SECONDS)
    assert crashed == {}, f"a waiting worker CRASHED, which is not a deadlock: {crashed}"
    assert stuck == [], f"two waiting workers waited on each other: {stuck} never came back"


# How long each released waiter holds the box in the arm below - several polls,
# so a second waiter let go beside it is certain to be counted.
QUIET_ARM_SECONDS: Final = 1.0


def test_two_waiters_that_find_the_box_quiet_together_are_let_go_one_at_a_time(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Two waiters probing at the same instant never BOTH run their quiet arm.

    A waiting worker unlocks its byte, so two waiters see no live sibling at once.
    Here both have unlocked before either probes, and both have probed before
    either acts on it - the interleaving that let both go together, about one
    run in six measured. Under --dist loadfile it needs two FILES that wait, and
    tests/test_hook_env_echo.py's wrapper arms now wait beside this file's.
    """
    run_id = "cs1233-overlap-" + uuid.uuid4().hex
    workers = {name: fake_worker(run_id, name) for name in ("gw0", "gw1")}
    sessions = {name: SimpleNamespace(config=worker) for name, worker in workers.items()}
    for session in sessions.values():
        xdist_quiet.pytest_sessionstart(cast(pytest.Session, session))
    both_unlocked = threading.Barrier(len(workers), timeout=DEADLOCK_SECONDS)
    both_probed = threading.Barrier(len(workers), timeout=DEADLOCK_SECONDS)
    first_probe_done: set[str] = set()
    real_names = xdist_quiet.live_sibling_names

    def probe_in_step(where: Path, own: str) -> list[str]:
        if own in first_probe_done:
            return real_names(where, own)
        first_probe_done.add(own)
        both_unlocked.wait()
        names = real_names(where, own)
        both_probed.wait()
        return names

    guard = threading.Lock()
    holding: list[str] = []
    peak: list[int] = [0]
    finished: set[str] = set()
    crashed: dict[str, str] = {}

    def worker_run(name: str) -> None:
        try:
            await_quiet_siblings(cast(pytest.Config, workers[name]))
            with guard:
                holding.append(name)
                peak[0] = max(peak[0], len(holding))
            time.sleep(QUIET_ARM_SECONDS)
            with guard:
                holding.remove(name)
            finished.add(name)
        except Exception as exc:  # surfaced by the assert below, never swallowed
            crashed[name] = error_shape(exc)
        finally:
            xdist_quiet.pytest_sessionfinish(cast(pytest.Session, sessions[name]))

    monkeypatch.setattr(xdist_quiet, "live_sibling_names", probe_in_step)
    threads = [threading.Thread(target=worker_run, args=(name,), daemon=True) for name in workers]
    try:
        for thread in threads:
            thread.start()
        deadline = time.monotonic() + 2 * DEADLOCK_SECONDS
        for thread in threads:
            thread.join(max(0.0, deadline - time.monotonic()))
    finally:
        for session in sessions.values():
            xdist_quiet.pytest_sessionfinish(cast(pytest.Session, session))
        for thread in threads:
            thread.join(DEADLOCK_SECONDS)
    together = peak[0]
    assert crashed == {}, f"a waiting worker CRASHED: {crashed}"
    assert finished == set(workers), f"only {sorted(finished)} came back from the wait"
    assert together == 1, f"{together} waiters ran their quiet arm at the same time"


def error_shape(exc: BaseException) -> str:
    """An exception as its type and errno only - its text can carry a temp path."""
    return f"{type(exc).__name__} errno={getattr(exc, 'errno', None)}"


class SimulatedClock:
    """A stand-in for the barrier module's ``time``: sleeping advances it, nothing waits."""

    def __init__(
        self, on_sleep: Callable[[float], None] | None = None, stride: float = 0.0
    ) -> None:
        """Start at zero; ``on_sleep`` runs inside every sleep, before the clock moves.

        A non-zero ``stride`` advances by that much per sleep instead of the
        requested seconds, so a long simulated wait takes few polls.
        """
        self.now = 0.0
        self.sleeps = 0
        self.on_sleep = on_sleep
        self.stride = stride

    def perf_counter(self) -> float:
        """The simulated time."""
        return self.now

    def monotonic(self) -> float:
        """The simulated time."""
        return self.now

    def sleep(self, seconds: float) -> None:
        """Advance the simulated time, after the hook has run."""
        self.sleeps += 1
        if self.on_sleep is not None:
            self.on_sleep(seconds)
        self.now += self.stride or seconds


# A simulated hour: a wait still polling past it has no bound worth the name.
UNBOUNDED_SECONDS: Final = 3600.0
# The simulated step of the bound arm, so an hour is a hundred and twenty polls.
BOUND_STRIDE_SECONDS: Final = 30.0


class NeverGaveUpError(Exception):
    """Raised by the simulated clock when a wait outlives any plausible bound."""


def test_a_sibling_ending_mid_wait_never_strands_the_waiters_relock(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The directory race, injected rather than waited for.

    The sibling's release is split at its first step: on the waiter's first poll
    the sibling's lock is let go, so the waiter stops waiting; and at the instant
    the waiter would re-create its own liveness file, the sibling's release
    finishes - its file unlinked, the now-empty run directory removed. A waiter
    that gave its file up to wait is left with no directory to re-lock in.
    """
    run_id = "cs1233-race-" + uuid.uuid4().hex
    directory = xdist_quiet.live_directory(run_id)
    waiter = fake_worker(run_id, "gw0")
    session = SimpleNamespace(config=waiter)
    xdist_quiet.pytest_sessionstart(cast(pytest.Session, session))
    sibling = hold_liveness_lock(directory, "gw1")
    waiter_file = directory / ("gw0" + xdist_quiet.LOCK_SUFFIX)
    steps: list[str] = []
    real_open = os.open

    def sibling_unlocks(_seconds: float) -> None:
        if "unlocked" not in steps:
            steps.append("unlocked")
            xdist_quiet._unlock(sibling.fd)  # noqa: SLF001 - the release's own first step

    def open_while_the_sibling_finishes(path: str, flags: int, *rest: int) -> int:
        if Path(path) == waiter_file and flags & os.O_CREAT and "released" not in steps:
            steps.append("released")
            release_liveness_lock(sibling)
        return real_open(path, flags, *rest)

    monkeypatch.setattr(xdist_quiet, "time", SimulatedClock(on_sleep=sibling_unlocks))
    monkeypatch.setattr(os, "open", open_while_the_sibling_finishes)
    try:
        try:
            await_quiet_siblings(cast(pytest.Config, waiter))
            failure = ""
        except OSError as exc:
            failure = error_shape(exc)
        monkeypatch.undo()
        if "released" not in steps:
            release_liveness_lock(sibling)
        assert failure == "", f"the waiter could not re-lock after its sibling ended: {failure}"
        relive = live_sibling_count(directory, "gw9")
        assert relive == 1, "the waiter came back from its wait without its liveness lock"
    finally:
        monkeypatch.undo()
        xdist_quiet.pytest_sessionfinish(cast(pytest.Session, session))


def test_a_wait_that_outlives_its_bound_fails_loud_naming_the_sibling(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A sibling that never finishes ends the wait LOUD at the bound, by worker id."""
    run_id = "cs1233-bound-" + uuid.uuid4().hex
    directory = xdist_quiet.live_directory(run_id)
    waiter = fake_worker(run_id, "gw0")
    session = SimpleNamespace(config=waiter)
    xdist_quiet.pytest_sessionstart(cast(pytest.Session, session))
    sibling = hold_liveness_lock(directory, "gw3")
    clock = SimulatedClock(stride=BOUND_STRIDE_SECONDS)

    def give_up_at_a_day(_seconds: float) -> None:
        if clock.now >= UNBOUNDED_SECONDS:
            raise NeverGaveUpError

    clock.on_sleep = give_up_at_a_day
    monkeypatch.setattr(xdist_quiet, "time", clock)
    named: tuple[str, ...] = ()
    try:
        try:
            await_quiet_siblings(cast(pytest.Config, waiter))
            outcome = "returned"
        except NeverGaveUpError:
            outcome = "never gave up"
        except xdist_quiet.QuietWaitTimeoutError as exc:
            # The named FIELD, never the object: an exception's text is an echo
            # path (non-negotiable 12, tests/test_exception_rendering.py).
            outcome = "timed out"
            named = exc.siblings
        except RuntimeError as exc:
            outcome = type(exc).__name__
        waited = clock.now
        monkeypatch.undo()
        assert outcome == "timed out", f"the wait ended as {outcome!r}, not at a loud bound"
        assert named == ("gw3",), f"the loud failure names {named}, not the live sibling"
        bound = xdist_quiet.QUIET_BOUND_SECONDS
        fired = bound <= waited <= bound + BOUND_STRIDE_SECONDS
        assert fired, f"the bound fired at {waited:.2f}s, not at {bound}s"
    finally:
        monkeypatch.undo()
        release_liveness_lock(sibling)
        xdist_quiet.pytest_sessionfinish(cast(pytest.Session, session))


# THE WAITS THIS BOX HAS MEASURED, and the whole suites they sat inside, from the
# whole-suite records of 2026-10-09: a junit record whose median arm waited
# 804.014 s (its `cs815_quiet_wait_seconds` property) inside a 1251.555 s suite,
# and the session 134 pre-push whole suite at 1074.41 s. A wait never outlasts
# the run it sits inside, so the suite walls bound it from above.
MEASURED_QUIET_WAIT_SECONDS: Final = (804.014,)
MEASURED_SUITE_WALL_SECONDS: Final = (1074.41, 1251.555)


def test_the_quiet_bound_outlasts_every_measured_wait_and_whole_suite() -> None:
    """The bound sits clear of every wait measured here, not under it.

    The first `alone` arm now waits for every sibling to drain the queue, so on a
    local whole suite it waits about as long as the median arm used to - which
    was measured at over 800 s. A bound under that fails a sound run LOUD.
    """
    bound = xdist_quiet.QUIET_BOUND_SECONDS
    longest_wait = max(MEASURED_QUIET_WAIT_SECONDS)
    longest_suite = max(MEASURED_SUITE_WALL_SECONDS)
    nested = longest_wait < longest_suite
    assert nested, "a recorded wait outlasts every recorded suite, so the records disagree"
    assert bound >= 2 * longest_suite, (
        f"the bound {bound}s is not twice the longest measured whole suite {longest_suite}s"
    )


def test_a_probe_holding_the_waiters_lock_only_delays_its_relock(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A sibling's probe can hold the waiter's byte for an instant; the relock retries."""
    run_id = "cs1233-relock-" + uuid.uuid4().hex
    directory = xdist_quiet.live_directory(run_id)
    waiter = fake_worker(run_id, "gw0")
    session = SimpleNamespace(config=waiter)
    xdist_quiet.pytest_sessionstart(cast(pytest.Session, session))
    waiter_file = directory / ("gw0" + xdist_quiet.LOCK_SUFFIX)
    probe_fd: list[int] = []
    real_names = xdist_quiet.live_sibling_names

    def probe_in_flight(where: Path, own: str) -> list[str]:
        names = real_names(where, own)
        if not probe_fd:
            fd = os.open(waiter_file, os.O_RDWR)
            probe_fd.append(fd)
            took = xdist_quiet._try_lock(fd)  # noqa: SLF001 - a sibling's probe, mid-flight
            assert took, "the waiter's byte was not free while it waited"
        return names

    def probe_lets_go(_seconds: float) -> None:
        if probe_fd:
            xdist_quiet._unlock(probe_fd[0])  # noqa: SLF001 - the probe's own second step

    monkeypatch.setattr(xdist_quiet, "live_sibling_names", probe_in_flight)
    monkeypatch.setattr(xdist_quiet, "time", SimulatedClock(on_sleep=probe_lets_go))
    try:
        await_quiet_siblings(cast(pytest.Config, waiter))
        monkeypatch.undo()
        relive = live_sibling_count(directory, "gw9")
        assert relive == 1, "the waiter came back from its wait without its liveness lock"
    finally:
        monkeypatch.undo()
        for fd in probe_fd:
            os.close(fd)
        xdist_quiet.pytest_sessionfinish(cast(pytest.Session, session))
