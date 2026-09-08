#!/usr/bin/env python3
"""Tests for tools/outbound_send.py - the CS-958 gated send path.

WHY THIS MODULE EXISTS. tools/outbound_gate.py grades outbound text and nothing
calls it: an instrument beside the channel is not a gate in front of it. The
channel itself has no sender either, so every delivery this project has made
was a hand-run script and none of them is recorded here. The module under test
is the one tool that grades a note and then delivers it, and the arms below are
about the two ways that can go wrong - bytes leaving when they should not, and
a delivery leaving no trace that it happened.

HOW THIS SUITE GUARANTEES IT NEVER TOUCHES A REAL moon_sync_inbox, which is the
first thing to check about a test module that drives a sender. There are four
mechanisms and they are mechanical rather than a convention anyone must
remember:

  1. :func:`run_send` is the ONLY place this file spawns the sender, and it
     ALWAYS injects ``--channel-root``. There is no code path here that runs the
     tool against its default root.
  2. :func:`run_send` refuses to run unless the channel root's directory name is
     :data:`CHANNEL_DIR_NAME` - a synthetic name that exists nowhere real - and
     unless that directory is neither the repository root's parent nor anything
     below the repository root. Only :func:`make_channel` creates a directory of
     that name, and it creates it under pytest's ``tmp_path``.
  3. Every destination name used here carries the ``958`` suffix and is created
     by the test that uses it, so a run that somehow escaped the channel root
     would find no destination and refuse rather than deliver.
  4. The delivery record is redirected into ``tmp_path`` through
     :data:`ENV_RECORD`, so no arm appends to the repository's own record.

``test_channel_root_is_honoured_and_no_real_inbox_is_touched`` measures the
first three rather than asserting them: it counts the files in every real
sibling inbox before and after a full ``--all --send`` run and requires the
total to be unchanged, and it hashes the repository's own record file across the
same run.

EVERY VIOLATING LITERAL IS ASSEMBLED FROM FRAGMENTS AT RUNTIME, the same
mechanism tests/test_outbound_gate.py uses and for the same reason: this file is
itself scanned by tools/precommit_gate.py, whose ``check_pii`` has no
placeholder escape (tools/precommit_gate.py::PLACEHOLDER_RE covers the SECRET
rules only). A spelled-out home path here would block the commit that adds these
tests.

NO REAL PERSONAL VALUE IS PLANTED, ASSERTED ON OR PRINTED. The only class
planted is the home path, which is canary-derived and needs no save root, so
every arm here grades identically on an operator box and on a bare CI runner
with no game installed. The three save-derived classes are exercised by
tests/test_outbound_gate.py and are deliberately not re-graded here - this
module's subject is the sender, and the gate's own verdict is consumed rather
than re-derived.

ASSERTIONS BIND SCALARS BEFORE COMPARING (CS-850,
tests/assertion_rendering_guard.py). An arm that wrote
``assert marker not in record_bytes`` would render both operands into the pytest
failure report, which is the echo path CLAUDE.md non-negotiable 12 forbids.
Counts and sorted lists of synthetic relative paths render safely; payloads and
absolute paths never reach an asserted expression.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SENDER = REPO_ROOT / "tools" / "outbound_send.py"
GATE = REPO_ROOT / "tools" / "outbound_gate.py"

# The closed exit set, named rather than spelled inline. Named because a bare
# `== 1` is both a ruff PLR2004 magic value and unreadable at the call site:
# the whole contract of this tool is WHICH code came back.
EXIT_OK = 0
EXIT_REFUSED = 1
EXIT_USAGE = 2
EXIT_UNMEASURED = 3
CLOSED_EXIT_SET = frozenset({EXIT_OK, EXIT_REFUSED, EXIT_USAGE, EXIT_UNMEASURED})

# The gate's own verdict vocabulary, keyed by the gate's own exit code. The
# record is required to carry one of these words rather than a code, because a
# record read a year later by a CS-951 reconciler should not need this file's
# exit table to be legible. AMBIGUITY RESOLVED HERE: the frozen contract names
# "the gate verdict at the time of sending" and does not spell it, so this
# suite fixes it as the gate's own two reachable words.
GATE_VERDICT_NAME = {EXIT_OK: "CLEAN", EXIT_UNMEASURED: "UNMEASURED"}

# The inbox directory name the channel is made of, and the synthetic channel
# directory name mechanism 2 in the module docstring keys on.
INBOX = "moon_sync_inbox"
CHANNEL_DIR_NAME = "channel958"

# AMBIGUITY RESOLVED HERE. The frozen contract fixes the record at
# `data/outbound_deliveries.json` and gives the CLI no override for it, but a
# suite that appended to the repository's own record would be neither
# deterministic nor honest about what it wrote. This key is the override, and
# it follows the project's existing CLOCKSPEED_* environment idiom rather than
# adding a flag the contract did not name (compare
# tools/outbound_gate.py::ENV_OUTBOUND_EXCLUSIONS).
ENV_RECORD = "CLOCKSPEED_OUTBOUND_RECORD"
RECORD_NAME = "record958.json"

# The repository's own record, hashed across a full run by the isolation arm.
REAL_RECORD = REPO_ROOT / "data" / "outbound_deliveries.json"

# Destination project names. Every one carries the 958 suffix so that a run
# which escaped the channel root would find nothing to deliver to.
DEST_A = "alpha958"
DEST_B = "beta958"
DEST_C = "epsilon958"
DEST_NO_INBOX = "gamma958"
DEST_INBOX_IS_A_FILE = "zeta958"
DEST_ABSENT = "delta958"

NOTE_NAME = "note958-first.md"
SECOND_NOTE_NAME = "note958-second.md"

# Assembled, never spelled out. See the module docstring.
WINDOWS_HOME_PATH = "C:" + "\\" + "Users" + "\\" + "someoperator" + "\\" + "notes.txt"
POSIX_HOME_PATH = "/" + "home" + "/someoperator" + "/app.log"

# Ordinary prose. Carries no path, no credential shape and no discoverable
# value, and is the payload every delivery arm sends.
CLEAN_BODY = (
    "The solver returned an exact Fraction and the ratio closed at 2:3.\n"
    "Milestone gap is four recipes; power headroom is 180 MW.\n"
)

# A sentence with no other job than to be a value the record must not carry.
# Not personal data and matched by no rule, so a refusal cannot be what keeps
# it out of the record.
PAYLOAD_MARKER = "heliotrope" + "958" + "conveyor"

# The first byte that is not 7-bit ASCII. Named because ruff PLR2004 is right
# that a bare 0x80 in a comparison is unreadable, and because the whole of
# CLAUDE.md non-negotiable 4 is this one boundary.
FIRST_NON_ASCII_BYTE = 0x80

# A drive letter followed by either separator. The record is forbidden from
# carrying one, and a JSON-escaped backslash still matches.
DRIVE_LETTER_RE = re.compile(r"[A-Za-z]:[\\/]")

# An ISO-8601 UTC instant. The record must carry one per entry, and the shape
# is asserted rather than the value, so the arm does not pin a clock.
UTC_STAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}")

TIMEOUT = 180


def require_sender() -> None:
    """Fail loudly while tools/outbound_send.py is absent.

    THIS IS THE ANTI-VACUITY LATCH FOR THE WHOLE MODULE, and it is the same
    hazard tests/test_outbound_gate.py::require_gate closes rather than a copy
    of its ceremony. Run against a missing file the interpreter itself exits 2
    with an ASCII message on stderr, and 2 is a member of this tool's closed
    exit set. So a missing module SILENTLY SATISFIES
    ``test_exit_codes_are_closed_set`` on its usage cell, and satisfies
    ``test_output_is_seven_bit_ascii`` outright, and satisfies every arm whose
    assertion is that nothing was written - because a module that never ran
    writes nothing. Routing every subprocess through this check makes the
    absence the failure instead of the result.
    """
    assert SENDER.is_file(), (
        "tools/outbound_send.py is absent; every arm in this module is vacuous until it exists"
    )


def base_env(tmp_path: Path) -> dict[str, str]:
    """A deterministic child environment that only ever REMOVES capability.

    The save root is pinned at a directory that does not exist and the local
    config at a file that does not exist, so the three save-derived classes are
    underivable and the account name is a value no machine logs in as. Nothing
    here GRANTS the child anything, which is what keeps the arms built on it
    honest on a bare runner with no game installed - the condition the rule
    suite is required to run under.

    The world overrides are popped rather than overwritten so an operator
    machine that declares a real world in config/local.json cannot feed a real
    value into any arm here, and the outbound exclusion key is popped so an
    operator who has silenced a false positive does not change what these arms
    measure.

    The record is redirected into ``tmp_path``: mechanism 4 of the four in the
    module docstring.
    """
    env = dict(os.environ)
    env["CLOCKSPEED_SAVE_ROOT"] = str(tmp_path / "absent-save-root")
    env["CLOCKSPEED_LOCAL_CONFIG"] = str(tmp_path / "absent-local-config.json")
    for key in (
        "CLOCKSPEED_WORLD_NAMES",
        "CLOCKSPEED_WORLD_TOKENS",
        "CLOCKSPEED_ACCOUNT_DIR",
        "CLOCKSPEED_OUTBOUND_EXCLUSIONS",
    ):
        env.pop(key, None)
    env["USERNAME"] = "sendtestaccount"
    env["USER"] = "sendtestaccount"
    env["PYTHONIOENCODING"] = "utf-8"
    env[ENV_RECORD] = str(tmp_path / RECORD_NAME)
    return env


def unmeasured_env(tmp_path: Path) -> dict[str, str]:
    """An environment where the gate's verdict on clean prose is exactly 3.

    The save root is pointed at an empty directory that really EXISTS, so the
    three save-derived classes are underivable for the honest reason rather
    than because a path was malformed. That is the same construction
    tests/test_outbound_gate.py::test_vacuity_is_not_clean uses to pin
    UNMEASURED deterministically on any machine.
    """
    env = base_env(tmp_path)
    empty_root = tmp_path / "empty-save-root"
    empty_root.mkdir(exist_ok=True)
    env["CLOCKSPEED_SAVE_ROOT"] = str(empty_root)
    return env


def make_channel(
    tmp_path: Path,
    with_inbox: tuple[str, ...] = (),
    without_inbox: tuple[str, ...] = (),
    inbox_is_a_file: tuple[str, ...] = (),
) -> Path:
    """Build a synthetic channel root under ``tmp_path`` and return it.

    The three populations are separate arguments because the discovery arm is
    about telling them apart: a project with an inbox directory is a
    destination, a project without one is not, and a project where the name is
    taken by a FILE is not either - a file is not something a note can be
    written into, and a discovery written with ``exists()`` instead of
    ``is_dir()`` would count it.
    """
    channel = tmp_path / CHANNEL_DIR_NAME
    channel.mkdir(exist_ok=True)
    for name in with_inbox:
        (channel / name / INBOX).mkdir(parents=True, exist_ok=True)
    for name in without_inbox:
        (channel / name).mkdir(parents=True, exist_ok=True)
    for name in inbox_is_a_file:
        (channel / name).mkdir(parents=True, exist_ok=True)
        (channel / name / INBOX).write_bytes(b"not a directory\n")
    return channel


def write_note(tmp_path: Path, name: str, payload: bytes) -> Path:
    """Write a note OUTSIDE the channel root and return its path.

    Outside deliberately: the arms compare a snapshot of the whole channel tree
    before and after a run, and a source note living inside the channel would
    be indistinguishable from a delivered one - and would also be discovered by
    ``--all`` if it happened to sit beside an inbox.
    """
    notes = tmp_path / "notes958"
    notes.mkdir(exist_ok=True)
    path = notes / name
    path.write_bytes(payload)
    return path


def clean_note(tmp_path: Path, name: str = NOTE_NAME, extra: str = "") -> Path:
    """A note of ordinary prose the gate has nothing to find in."""
    body = CLEAN_BODY + extra
    return write_note(tmp_path, name, body.encode("ascii"))


def load_sender() -> ModuleType:
    """Import the sender by path, for the arms that grade a function directly.

    By path rather than `import tools.outbound_send`, matching the idiom the
    gate suite already uses: it keeps `tools/` out of this suite's import graph
    and does not depend on the shape of `sys.path`.
    """
    require_sender()
    name = "clockspeed_outbound_send_under_test"
    spec = importlib.util.spec_from_file_location(name, SENDER)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def run_send(
    *args: str,
    channel: Path,
    env: dict[str, str],
) -> tuple[int, bytes, bytes]:
    """Drive the sender as a real subprocess and return (code, stdout, stderr).

    A SUBPROCESS because the exit code is half the contract, and RAW BYTES
    because ``test_output_is_seven_bit_ascii`` is a claim about bytes that a
    decode with errors="replace" would launder away. The call captures the code
    directly rather than through a shell pipeline: a pipe reports the last
    stage's status, so a refusal would read back as exit 0.

    THE FOUR PRECONDITIONS BELOW ARE THE ISOLATION GUARANTEE and not defensive
    clutter. They are what makes "no arm in this file can reach a real inbox" a
    property of one function rather than a promise spread over fifteen.
    """
    require_sender()
    resolved = channel.resolve()
    assert resolved.name == CHANNEL_DIR_NAME, (
        "the channel root is not the synthetic directory this suite builds"
    )
    assert resolved.is_dir(), "the channel root does not exist"
    assert resolved != REPO_ROOT.parent, "the channel root is the real sibling root"
    assert REPO_ROOT not in resolved.parents, "the channel root is inside the repository"
    assert env.get(ENV_RECORD, "").endswith(RECORD_NAME), (
        "the delivery record was not redirected out of the repository"
    )
    proc = subprocess.run(
        [sys.executable, str(SENDER), "--channel-root", str(channel), *args],
        capture_output=True,
        env=env,
        timeout=TIMEOUT,
        check=False,
    )
    return proc.returncode, proc.stdout, proc.stderr


def gate_verdict(note: Path, env: dict[str, str]) -> int:
    """Run the GATE on a note and return its exit code.

    THE KNOWN-GOOD CONTROL for every arm whose precondition is a particular
    verdict. Without it, an arm that expected a delivery and got a refusal
    would report "no file was delivered" and say nothing about why, and an arm
    that expected UNMEASURED would silently grade a CLEAN run instead. The
    gate is a shipped module this slice does not own, so asking it directly is
    a measurement rather than an assumption about it.
    """
    assert GATE.is_file(), "tools/outbound_gate.py is absent; the control cannot be taken"
    proc = subprocess.run(
        [sys.executable, str(GATE), "--file", str(note)],
        capture_output=True,
        env=env,
        timeout=TIMEOUT,
        check=False,
    )
    return proc.returncode


def tree_snapshot(root: Path) -> dict[str, str]:
    """Map every path under ``root`` to a content hash, directories included.

    Hashes rather than bytes so that a difference can be RENDERED into a
    failure report without rendering a payload, and directories included so
    that a run which created an empty destination is still a difference.
    """
    snapshot: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        key = path.relative_to(root).as_posix()
        if path.is_dir():
            snapshot[key] = "<dir>"
        else:
            snapshot[key] = hashlib.sha256(path.read_bytes()).hexdigest()
    return snapshot


def changed_paths(before: dict[str, str], after: dict[str, str]) -> list[str]:
    """The relative paths that appeared, vanished or changed content.

    Returns PATHS ONLY - never the hashes and never the contents - because the
    list is rendered into a failure report. The paths are relative to a
    synthetic channel root this suite built, so they carry nothing personal.
    """
    keys = set(before) | set(after)
    return sorted(key for key in keys if before.get(key) != after.get(key))


def record_entries(env: dict[str, str]) -> list[object]:
    """The delivery record as a list, empty when the file was never written."""
    path = Path(env[ENV_RECORD])
    if not path.is_file():
        return []
    parsed = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(parsed, list), "the delivery record is not a list of entries"
    return parsed


def record_raw(env: dict[str, str]) -> bytes:
    """The delivery record's bytes, empty when the file was never written."""
    path = Path(env[ENV_RECORD])
    return path.read_bytes() if path.is_file() else b""


def entry_values(entry: object) -> list[object]:
    """Every value in one record entry, which must be a flat JSON object.

    ASSERTING BY VALUE RATHER THAN BY KEY NAME IS DELIBERATE, and it is the
    second ambiguity this suite had to resolve. The frozen contract fixes what
    each entry CARRIES and never what the keys are called, so an arm keyed on
    invented names would grade this file's guesses instead of the contract.
    Every required item is therefore asserted as a value the entry holds.
    """
    assert isinstance(entry, dict), "a record entry is not a JSON object"
    return list(entry.values())


def record_strings(entries: list[object]) -> list[str]:
    """Every string anywhere in the record, keys included.

    Keys included because a key built from a path would leak exactly as much as
    a value built from one.
    """
    found: list[str] = []
    stack: list[object] = list(entries)
    while stack:
        item = stack.pop()
        if isinstance(item, dict):
            stack.extend(item.keys())
            stack.extend(item.values())
        elif isinstance(item, list):
            stack.extend(item)
        elif isinstance(item, str):
            found.append(item)
    return found


def delivered(channel: Path, name: str, note_name: str = NOTE_NAME) -> Path:
    """Where a note of ``note_name`` lands at destination ``name``."""
    return channel / name / INBOX / note_name


def text(data: bytes) -> str:
    """Decode a captured stream for substring assertions, losing nothing."""
    return data.decode("utf-8", "replace")


def assert_absent_in_any_case(needle: str, haystacks: tuple[bytes, ...]) -> None:
    """Assert a planted value appears in no stream, in no case variant.

    Binds a COUNT before asserting. ``assert needle not in blob`` would render
    both operands into the pytest failure report, which is the echo path
    CLAUDE.md non-negotiable 12 forbids; an integer renders safely.
    """
    folded = needle.lower()
    assert folded, "an empty needle would make this check vacuous"
    hits = sum(text(blob).lower().count(folded) for blob in haystacks)
    assert hits == 0, f"a value that must not be echoed appeared {hits} time(s)"


def real_inbox_counts() -> tuple[int, int]:
    """Count the real sibling inboxes and the files in them. NAMES ARE NEVER READ OUT.

    Counts only, and returned as a pair so the arm using it can say whether the
    control was vacuous. A directory that cannot be listed is skipped rather
    than raised on: the sibling root is a filesystem root on this machine and
    carries entries no user process may open.
    """
    projects = 0
    files = 0
    try:
        children = sorted(REPO_ROOT.parent.iterdir())
    except OSError:
        return (0, 0)
    for child in children:
        inbox = child / INBOX
        try:
            if not inbox.is_dir():
                continue
            entries = list(inbox.iterdir())
        except OSError:
            continue
        projects += 1
        files += len(entries)
    return (projects, files)


def digest_of(path: Path) -> str:
    """A content hash for a file that may not exist."""
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else "<absent>"


# --------------------------------------------------------------------------
# SAFETY. 1-7 are the arms that decide whether bytes leave when they must not.
# --------------------------------------------------------------------------


def test_a_refused_note_is_delivered_nowhere(tmp_path: Path) -> None:
    """Prove a note the gate REFUSES lands at no destination at all.

    THE ABSENCE CHECK IS THE ARM AND THE EXIT CODE IS NOT. A sender that
    delivered the note and then returned 1 would satisfy an exit-code
    assertion completely, and it is the delivery that is irreversible - the
    bytes are in another repository before anyone re-reads them. So the whole
    channel tree is hashed before and after, and NOTHING may differ: not the
    named destinations, not the unnamed one, not a stray temporary file left
    beside an inbox by an atomic write that was begun and abandoned.

    The record is asserted empty in the same arm, because a refusal that wrote
    a record entry would claim a delivery that did not happen, which is the
    CS-951 hole pointing the other way.

    Were this arm absent, a sender that resolved destinations, wrote the bytes
    and only then consulted the gate would pass every exit-code assertion in
    this module.
    """
    channel = make_channel(tmp_path, with_inbox=(DEST_A, DEST_B), without_inbox=(DEST_NO_INBOX,))
    env = base_env(tmp_path)
    note = write_note(
        tmp_path, NOTE_NAME, ("See " + WINDOWS_HOME_PATH + " for details.\n").encode("ascii")
    )
    before = tree_snapshot(channel)

    code, out, err = run_send(
        "--note",
        str(note),
        "--to",
        DEST_A,
        "--to",
        DEST_B,
        "--send",
        "--allow-unmeasured",
        channel=channel,
        env=env,
    )
    changed = changed_paths(before, tree_snapshot(channel))
    entries = record_entries(env)

    assert code == EXIT_REFUSED, f"exit {code} for a refused note; stdout {text(out)!r}"
    assert not changed, f"a refused note changed the channel tree at {changed}"
    assert len(entries) == 0, f"a refused note wrote {len(entries)} record entry/entries"
    assert "REFUSED" in text(out) + text(err), "the refusal was not reported"


def test_dry_run_is_the_default(tmp_path: Path) -> None:
    """Prove that without --send a clean note writes NOTHING, and with it delivers.

    THE ARM THAT STOPS AN ACCIDENTAL BROADCAST. It is written as a two-cell
    control in one function on purpose: asserting only that the dry run wrote
    nothing would pass against a tool that is broken and writes nothing ever,
    and asserting only that --send delivers says nothing about the default. The
    two cells run against the SAME channel and the same note, so ``--send`` is
    the only difference between them and the difference in outcome is
    attributable to it alone.

    The dry run must exit 0 rather than some advisory code: the contract's 0 is
    "delivered, or a dry run that would have delivered", and a caller that saw
    a non-zero preview would learn nothing about whether the send is safe.

    Were this arm absent, a sender whose default was to write would pass every
    delivery arm below and would broadcast on the first invocation anybody
    typed while exploring the flags.
    """
    channel = make_channel(tmp_path, with_inbox=(DEST_A, DEST_B))
    env = base_env(tmp_path)
    note = clean_note(tmp_path)
    assert gate_verdict(note, env) != EXIT_REFUSED, (
        "the gate refuses this suite's clean prose on this machine; the arm cannot grade"
    )
    before = tree_snapshot(channel)

    dry_code, dry_out, dry_err = run_send(
        "--note",
        str(note),
        "--to",
        DEST_A,
        "--to",
        DEST_B,
        "--allow-unmeasured",
        channel=channel,
        env=env,
    )
    dry_changed = changed_paths(before, tree_snapshot(channel))
    dry_entries = record_entries(env)

    assert dry_code == EXIT_OK, f"exit {dry_code} for a dry run; stderr {text(dry_err)!r}"
    assert not dry_changed, f"the DEFAULT invocation wrote to {dry_changed}"
    assert len(dry_entries) == 0, "the default invocation recorded a delivery it did not make"
    assert "REFUSED" not in text(dry_out) + text(dry_err)

    sent_code, _, sent_err = run_send(
        "--note",
        str(note),
        "--to",
        DEST_A,
        "--to",
        DEST_B,
        "--send",
        "--allow-unmeasured",
        channel=channel,
        env=env,
    )
    sent_changed = changed_paths(before, tree_snapshot(channel))

    assert sent_code == EXIT_OK, f"exit {sent_code} with --send; stderr {text(sent_err)!r}"
    assert len(sent_changed) > 0, "--send wrote nothing either; the dry-run cell proves nothing"
    landed = sorted(name for name in (DEST_A, DEST_B) if delivered(channel, name).is_file())
    assert landed == [DEST_A, DEST_B], f"--send reached only {landed}"


def test_unmeasured_needs_the_flag(tmp_path: Path) -> None:
    """Prove UNMEASURED blocks the send at exit 3 unless --allow-unmeasured is given.

    A class the gate could not derive is not a class it cleared, so the default
    must be to hold the note. Both cells run in one arm because the flag is the
    only difference between them, and because the second cell is what stops the
    first from being satisfied by a tool that refuses everything.

    THE RECORDED VERDICT IS ASSERTED IN THE SECOND CELL, and that is the half
    that makes the flag honest: a delivery made under a verdict the gate could
    not fully derive must SAY so in the record, or a later reader of the record
    cannot tell a cleared send from a waved-through one.

    The environment points the save root at an empty directory that really
    exists, so the gate's verdict here is 3 by construction on any machine
    rather than by whatever the operator has installed. The control run asserts
    that precondition rather than assuming it.

    Were this arm absent, a sender that ignored the gate's 3 entirely would
    pass every other arm in this module, since every other arm passes the flag.
    """
    channel = make_channel(tmp_path, with_inbox=(DEST_A,))
    env = unmeasured_env(tmp_path)
    note = clean_note(tmp_path)
    control = gate_verdict(note, env)
    assert control == EXIT_UNMEASURED, f"the gate returned {control}; the arm needs an UNMEASURED"
    before = tree_snapshot(channel)

    held_code, _, held_err = run_send(
        "--note", str(note), "--to", DEST_A, "--send", channel=channel, env=env
    )
    held_changed = changed_paths(before, tree_snapshot(channel))

    assert held_code == EXIT_UNMEASURED, f"exit {held_code}; stderr {text(held_err)!r}"
    assert not held_changed, f"an unmeasured verdict still wrote to {held_changed}"
    assert len(record_entries(env)) == 0, "an unmeasured verdict recorded a delivery"

    sent_code, _, sent_err = run_send(
        "--note",
        str(note),
        "--to",
        DEST_A,
        "--send",
        "--allow-unmeasured",
        channel=channel,
        env=env,
    )
    entries = record_entries(env)

    assert sent_code == EXIT_OK, f"exit {sent_code} with the flag; stderr {text(sent_err)!r}"
    assert delivered(channel, DEST_A).is_file(), "the flag was given and nothing was delivered"
    assert len(entries) == 1, f"{len(entries)} record entries for one destination"
    words = [value for value in entry_values(entries[0]) if value == GATE_VERDICT_NAME[control]]
    assert len(words) == 1, "the record does not say the verdict was UNMEASURED"


def test_a_missing_destination_refuses_the_whole_send(tmp_path: Path) -> None:
    """Prove one unresolvable destination stops the delivery to the good ones.

    A partial delivery leaves a partial record, and a partial record is the
    CS-951 hole with extra steps: some sibling holds a note this repository
    cannot account for. So the refusal is whole-send, and the arm asserts it by
    checking the two VALID destinations rather than by checking the invalid
    one - a sender that skipped the bad destination and delivered to the other
    two would satisfy an exit-code assertion and fail this one.

    TWO CELLS, because "missing" has two spellings and a sender can easily
    handle one: a project directory that exists but holds no inbox, and a
    project name with no directory at all.

    Were this arm absent, a best-effort sender that delivered what it could
    would pass every remaining arm here.
    """
    channel = make_channel(tmp_path, with_inbox=(DEST_A, DEST_B), without_inbox=(DEST_NO_INBOX,))
    env = base_env(tmp_path)
    note = clean_note(tmp_path)
    before = tree_snapshot(channel)

    for missing in (DEST_NO_INBOX, DEST_ABSENT):
        code, out, err = run_send(
            "--note",
            str(note),
            "--to",
            DEST_A,
            "--to",
            DEST_B,
            "--to",
            missing,
            "--send",
            "--allow-unmeasured",
            channel=channel,
            env=env,
        )
        changed = changed_paths(before, tree_snapshot(channel))
        landed = sorted(name for name in (DEST_A, DEST_B) if delivered(channel, name).is_file())

        assert code == EXIT_REFUSED, f"exit {code} for a missing destination; out {text(out)!r}"
        assert not landed, f"a partial delivery reached {landed}"
        assert not changed, f"a refused whole-send changed {changed}"
        assert len(record_entries(env)) == 0, "a refused whole-send wrote a record entry"
        assert missing in text(out) + text(err), "the refusal does not name the destination"


def test_a_filename_collision_refuses_and_leaves_the_bytes_untouched(tmp_path: Path) -> None:
    """Prove an existing target filename at ANY destination stops the whole send.

    A rename reads as new mail to the sibling's watcher and an overwrite reads
    as nothing at all, so neither is available and the send is refused. The
    collision is planted at the SECOND destination named, so a sender that
    checked collisions as it went would already have written the first one -
    which is exactly what the untouched-tree assertion catches.

    THE EXISTING FILE'S BYTES ARE COMPARED AFTERWARDS, not merely its
    existence. A sender that truncated the file and then discovered the
    collision would leave a file that still exists and has lost everything, and
    that is the more destructive of the two failures.

    Were this arm absent, an implementation that opened the target for writing
    before testing for it would pass every other arm here.
    """
    channel = make_channel(tmp_path, with_inbox=(DEST_A, DEST_B))
    env = base_env(tmp_path)
    note = clean_note(tmp_path)
    occupied = delivered(channel, DEST_B)
    original = b"an earlier note that must survive this run\n"
    occupied.write_bytes(original)
    before = tree_snapshot(channel)

    code, out, err = run_send(
        "--note",
        str(note),
        "--to",
        DEST_A,
        "--to",
        DEST_B,
        "--send",
        "--allow-unmeasured",
        channel=channel,
        env=env,
    )
    changed = changed_paths(before, tree_snapshot(channel))
    survived = occupied.read_bytes() == original

    assert code == EXIT_REFUSED, f"exit {code} for a filename collision; out {text(out)!r}"
    assert not delivered(channel, DEST_A).is_file(), "the first destination was written anyway"
    assert survived, "the existing note's bytes were modified by a refused send"
    assert not changed, f"a refused send changed {changed}"
    assert len(record_entries(env)) == 0, "a refused send wrote a record entry"
    assert "REFUSED" in text(out) + text(err), "the collision was not reported as a refusal"


def test_undecodable_bytes_refuse(tmp_path: Path) -> None:
    """Prove a note that is not valid UTF-8 is refused rather than sent.

    A payload that cannot be decoded cannot be graded, and a class that was not
    scanned on bytes that were nonetheless SENT is a leak the gate declined to
    look at. Fail closed: the contract's 1 covers the tool raising on its own
    behalf for exactly this reason.

    The bytes are a lone continuation byte and a truncated multi-byte lead,
    which no decoder accepts and which no charset check can launder.

    Were this arm absent, a sender that read the note with errors="replace"
    would deliver the original bytes while grading a laundered copy of them -
    a gate that ran and measured something other than what was sent.
    """
    channel = make_channel(tmp_path, with_inbox=(DEST_A,))
    env = base_env(tmp_path)
    note = write_note(
        tmp_path, NOTE_NAME, b"prefix " + bytes([0xFF, 0xFE, 0x80, 0xC3]) + b" tail\n"
    )
    before = tree_snapshot(channel)

    code, out, err = run_send(
        "--note",
        str(note),
        "--to",
        DEST_A,
        "--send",
        "--allow-unmeasured",
        channel=channel,
        env=env,
    )
    changed = changed_paths(before, tree_snapshot(channel))

    assert code == EXIT_REFUSED, f"exit {code} on undecodable input; stdout {text(out)!r}"
    assert not changed, f"undecodable bytes were written to {changed}"
    assert len(record_entries(env)) == 0, "undecodable bytes produced a record entry"
    assert "REFUSED" in text(out) + text(err)


def test_the_gate_runs_before_destinations_are_resolved(tmp_path: Path) -> None:
    """Prove the gate's refusal is what is REPORTED when both faults are present.

    ORDERING IS A PROPERTY AND NOT AN IMPLEMENTATION DETAIL. The expensive,
    failure-prone work must not have happened when a refusal lands, and a tool
    that resolved destinations first would report the wrong cause: an operator
    would fix the missing sibling, re-run, and only then discover the note
    carries a home path. The gate is also the cheaper check and the one whose
    answer can never be changed by the state of the channel.

    TWO CELLS IN ONE ARM, and the first is a known-good control without which
    the second proves nothing. Cell one gives a CLEAN note and a missing
    destination and establishes that a missing-destination refusal NAMES the
    destination - a refusal that did not name it would be unactionable, and the
    absence check in cell two would then pass against any ordering at all. Cell
    two gives a refused note AND the same missing destination, and requires the
    gate's own class to be reported while the destination's name appears
    nowhere.

    Were this arm absent, a sender that resolved the channel first would pass
    every other arm in this module, because every other arm presents exactly
    one fault at a time.
    """
    channel = make_channel(tmp_path, with_inbox=(DEST_A,))
    env = base_env(tmp_path)
    clean = clean_note(tmp_path)

    control_code, control_out, control_err = run_send(
        "--note",
        str(clean),
        "--to",
        DEST_A,
        "--to",
        DEST_ABSENT,
        "--send",
        "--allow-unmeasured",
        channel=channel,
        env=env,
    )
    control_text = text(control_out) + text(control_err)

    assert control_code == EXIT_REFUSED, f"exit {control_code}; the control needs a refusal"
    assert DEST_ABSENT in control_text, (
        "a missing-destination refusal does not name it; the ordering cell cannot grade"
    )

    dirty = write_note(
        tmp_path,
        SECOND_NOTE_NAME,
        ("See " + POSIX_HOME_PATH + " for details.\n").encode("ascii"),
    )
    code, out, err = run_send(
        "--note",
        str(dirty),
        "--to",
        DEST_A,
        "--to",
        DEST_ABSENT,
        "--send",
        "--allow-unmeasured",
        channel=channel,
        env=env,
    )
    both = text(out) + text(err)

    assert code == EXIT_REFUSED, f"exit {code}; stdout {text(out)!r}"
    assert "home-path" in both, "the gate's own class was not reported"
    assert DEST_ABSENT not in both, "the destination was resolved before the gate graded the note"
    assert not delivered(channel, DEST_A, SECOND_NOTE_NAME).is_file()


# --------------------------------------------------------------------------
# DELIVERY AND RECORD. 8-12.
# --------------------------------------------------------------------------


def test_a_clean_note_lands_byte_identical_at_every_destination(tmp_path: Path) -> None:
    """Prove --send writes the SOURCE BYTES to each named inbox, unchanged.

    Byte-identical rather than merely present: a sender that normalised line
    endings, re-encoded, or appended a header would deliver a note whose
    sha256 no longer matches the one it recorded, and the record is the only
    thing a later CS-951 reconciler has to compare a sibling's copy against.

    Three destinations rather than one, because a loop that delivered to the
    last named destination only would pass a single-destination arm.

    Were this arm absent, the entire module would consist of arms asserting
    that nothing was written, all of which a tool that never writes satisfies.
    """
    channel = make_channel(tmp_path, with_inbox=(DEST_A, DEST_B, DEST_C))
    env = base_env(tmp_path)
    note = clean_note(tmp_path)
    source = note.read_bytes()
    assert gate_verdict(note, env) != EXIT_REFUSED, (
        "the gate refuses this suite's clean prose on this machine; the arm cannot grade"
    )

    code, out, err = run_send(
        "--note",
        str(note),
        "--to",
        DEST_A,
        "--to",
        DEST_B,
        "--to",
        DEST_C,
        "--send",
        "--allow-unmeasured",
        channel=channel,
        env=env,
    )
    names = (DEST_A, DEST_B, DEST_C)
    present = sorted(name for name in names if delivered(channel, name).is_file())
    identical = sorted(name for name in present if delivered(channel, name).read_bytes() == source)

    assert code == EXIT_OK, f"exit {code}; stdout {text(out)!r} stderr {text(err)!r}"
    assert present == sorted(names), f"the note reached only {present}"
    assert identical == sorted(names), f"only {identical} received the source bytes unchanged"


def test_all_discovers_every_sibling_with_an_inbox_and_no_others(tmp_path: Path) -> None:
    """Prove --all delivers to exactly the projects that hold an inbox DIRECTORY.

    The channel deliberately holds four kinds of sibling: three with an inbox,
    one with none, one where the inbox name is taken by a FILE, and a loose
    file at the channel root that is not a project at all. A discovery written
    with ``exists()`` rather than ``is_dir()`` counts the third; a discovery
    that globbed the root without checking counts the fourth.

    THE "NO OTHERS" HALF IS ASSERTED FROM THE TREE DIFF rather than from the
    three expected paths, so a delivery to somewhere nobody thought to check
    is a finding rather than an omission.

    Were this arm absent, --all could be an alias for "every directory" and the
    named-destination arms would all still pass.
    """
    channel = make_channel(
        tmp_path,
        with_inbox=(DEST_A, DEST_B, DEST_C),
        without_inbox=(DEST_NO_INBOX,),
        inbox_is_a_file=(DEST_INBOX_IS_A_FILE,),
    )
    (channel / "loose958.txt").write_bytes(b"not a project\n")
    env = base_env(tmp_path)
    note = clean_note(tmp_path)
    before = tree_snapshot(channel)

    code, out, err = run_send(
        "--note", str(note), "--all", "--send", "--allow-unmeasured", channel=channel, env=env
    )
    changed = changed_paths(before, tree_snapshot(channel))
    expected = sorted(f"{name}/{INBOX}/{NOTE_NAME}" for name in (DEST_A, DEST_B, DEST_C))

    assert code == EXIT_OK, f"exit {code}; stdout {text(out)!r} stderr {text(err)!r}"
    assert changed == expected, f"--all changed {changed}"
    assert len(record_entries(env)) == len(expected), "the record does not match what was delivered"


def test_the_record_gains_one_entry_per_destination(tmp_path: Path) -> None:
    """Prove each delivery is recorded with everything a later run needs.

    The five items the contract fixes are asserted as VALUES the entry holds -
    see :func:`entry_values` for why the keys are not pinned - plus a UTC
    timestamp asserted by shape. The sha256 is computed from the DELIVERED
    bytes rather than from the source, so an entry recording a hash of
    something other than what arrived is a finding.

    ONE ENTRY PER DESTINATION AND NOT ONE PER SEND, because the thing a CS-951
    reconciler asks is "does the copy this repository believes it put in that
    sibling still exist", and a single pooled entry for two destinations cannot
    answer it for either one.

    Were this arm absent, a record that held only a timestamp and a note name
    would satisfy the appending arm and the no-payload arm both.
    """
    channel = make_channel(tmp_path, with_inbox=(DEST_A, DEST_B))
    env = base_env(tmp_path)
    note = clean_note(tmp_path)
    control = gate_verdict(note, env)
    assert control in GATE_VERDICT_NAME, f"the gate returned {control}; the arm cannot grade"

    code, _, err = run_send(
        "--note",
        str(note),
        "--to",
        DEST_A,
        "--to",
        DEST_B,
        "--send",
        "--allow-unmeasured",
        channel=channel,
        env=env,
    )
    entries = record_entries(env)
    assert code == EXIT_OK, f"exit {code}; stderr {text(err)!r}"
    assert len(entries) == len((DEST_A, DEST_B)), f"{len(entries)} entries for two destinations"

    recorded_destinations = []
    for entry in entries:
        values = entry_values(entry)
        names = [value for value in values if value in (DEST_A, DEST_B)]
        assert len(names) == 1, "an entry does not name exactly one destination"
        destination = str(names[0])
        recorded_destinations.append(destination)

        landed = delivered(channel, destination).read_bytes()
        wanted = {
            NOTE_NAME,
            hashlib.sha256(landed).hexdigest(),
            GATE_VERDICT_NAME[control],
            len(landed),
        }
        missing = sorted(str(item) for item in wanted if item not in values)
        stamps = [
            value
            for value in values
            if isinstance(value, str) and UTC_STAMP_RE.match(value) is not None
        ]

        assert not missing, f"the entry for one destination is missing {missing}"
        assert len(stamps) == 1, "an entry does not carry exactly one UTC timestamp"

    assert sorted(recorded_destinations) == sorted((DEST_A, DEST_B))


def test_the_record_holds_no_absolute_path_and_no_payload(tmp_path: Path) -> None:
    """Prove the record leaks neither the note's contents nor this machine's paths.

    An absolute path in a record is a path that leaks the machine - the home
    directory, the account name, the checkout location - and a record carrying
    the payload would turn the log of what was sent into a second copy of it.
    Both are CLAUDE.md non-negotiable 3 and 12 respectively, and the record is
    a file that outlives the run and gets read by later tooling, so it is the
    worst place for either.

    A distinctive sentence is planted in the note, and the run is a DELIVERY
    rather than a refusal - a refusal would keep the payload out of the record
    by writing no record at all, and would prove nothing.

    Were this arm absent, the cheapest possible record - a JSON dump of the
    tool's own arguments and the note text - would satisfy every other record
    arm here.
    """
    channel = make_channel(tmp_path, with_inbox=(DEST_A, DEST_B))
    env = base_env(tmp_path)
    note = clean_note(tmp_path, extra=PAYLOAD_MARKER + " is the marker for this arm.\n")

    code, _, err = run_send(
        "--note",
        str(note),
        "--to",
        DEST_A,
        "--to",
        DEST_B,
        "--send",
        "--allow-unmeasured",
        channel=channel,
        env=env,
    )
    entries = record_entries(env)
    raw = record_raw(env)
    strings = record_strings(entries)
    rooted = [value for value in strings if value.startswith(("/", "\\"))]
    drives = sum(1 for value in strings if DRIVE_LETTER_RE.search(value) is not None)

    assert code == EXIT_OK, f"exit {code}; stderr {text(err)!r}"
    assert len(entries) > 0, "nothing was recorded; the arm would be vacuous"
    assert_absent_in_any_case(PAYLOAD_MARKER, (raw,))
    assert_absent_in_any_case(str(tmp_path), (raw,))
    assert len(rooted) == 0, f"{len(rooted)} record value(s) begin with a path separator"
    assert drives == 0, f"{drives} record value(s) carry a drive letter"


def test_a_second_send_appends_rather_than_replacing(tmp_path: Path) -> None:
    """Prove the record accumulates across runs instead of being rewritten.

    A record that is replaced each run answers "what did the last send do",
    which is not the question. CS-951's question is whether every delivery this
    repository has EVER made is still where it was put, and a one-run record
    cannot be asked it.

    The two runs deliver DIFFERENT filenames to the same destination, which is
    also what keeps the collision refusal out of the way, and makes the two
    entries distinguishable by a value rather than by their order.

    Were this arm absent, a sender that wrote the record with a plain truncate
    would pass every other record arm, since each of them inspects the record
    after exactly one run.
    """
    channel = make_channel(tmp_path, with_inbox=(DEST_A,))
    env = base_env(tmp_path)
    first = clean_note(tmp_path, name=NOTE_NAME)
    second = clean_note(tmp_path, name=SECOND_NOTE_NAME)

    first_code, _, first_err = run_send(
        "--note",
        str(first),
        "--to",
        DEST_A,
        "--send",
        "--allow-unmeasured",
        channel=channel,
        env=env,
    )
    after_first = len(record_entries(env))
    second_code, _, second_err = run_send(
        "--note",
        str(second),
        "--to",
        DEST_A,
        "--send",
        "--allow-unmeasured",
        channel=channel,
        env=env,
    )
    entries = record_entries(env)
    names = {value for entry in entries for value in entry_values(entry) if isinstance(value, str)}

    assert first_code == EXIT_OK, f"first send exit {first_code}; stderr {text(first_err)!r}"
    assert second_code == EXIT_OK, f"second send exit {second_code}; stderr {text(second_err)!r}"
    assert after_first == 1, f"{after_first} entries after one delivery"
    assert len(entries) == 2, f"{len(entries)} entries after two deliveries"  # noqa: PLR2004
    assert NOTE_NAME in names, "the first delivery was dropped from the record"
    assert SECOND_NOTE_NAME in names, "the second delivery was not recorded"


# --------------------------------------------------------------------------
# CHANNEL. 13-15 - properties of the tool's own boundary and output.
# --------------------------------------------------------------------------


def test_channel_root_is_honoured_and_no_real_inbox_is_touched(tmp_path: Path) -> None:
    """Prove --channel-root redirects the whole send, measured against the real siblings.

    THIS ARM IS THE ISOLATION GUARANTEE ITSELF, taken as a measurement rather
    than restated as a promise. The four mechanisms are in the module
    docstring; this arm takes the reading. Every real sibling inbox is counted
    before and after a full ``--all --send`` run, and the repository's own
    delivery record is hashed across it. A tool that ignored the flag and
    defaulted to the repository's parent would deliver into a real inbox, and
    the counts would move.

    THE SUPPLEMENTARY HALF CAN BE VACUOUS AND SAYS SO. On a fresh clone with no
    siblings the inbox population is zero and the count comparison measures
    nothing; the population size is carried in the failure message so a reader
    can tell which case they are looking at. The record hash is never vacuous -
    an absent file hashes to a sentinel that a written one cannot equal.

    Were this arm absent, --channel-root could be accepted and ignored, and
    every other arm here would report the tool broken in some confusing way
    rather than reporting that it had written to a real repository.
    """
    channel = make_channel(tmp_path, with_inbox=(DEST_A, DEST_B))
    env = base_env(tmp_path)
    note = clean_note(tmp_path)
    before_counts = real_inbox_counts()
    before_record = digest_of(REAL_RECORD)

    code, out, err = run_send(
        "--note", str(note), "--all", "--send", "--allow-unmeasured", channel=channel, env=env
    )
    after_counts = real_inbox_counts()
    after_record = digest_of(REAL_RECORD)
    landed = sorted(name for name in (DEST_A, DEST_B) if delivered(channel, name).is_file())

    assert code == EXIT_OK, f"exit {code}; stdout {text(out)!r} stderr {text(err)!r}"
    assert landed == [DEST_A, DEST_B], f"the send did not land in the temporary channel: {landed}"
    assert after_counts == before_counts, (
        f"a real sibling inbox changed; {before_counts[0]} inbox(es) were in the population"
    )
    assert after_record == before_record, "the repository's own delivery record was written"


def test_all_does_not_broadcast_to_this_repository() -> None:
    """Prove `--all` excludes this repository from its own broadcast.

    AUTHORSHIP DISCLOSED: this arm was written by the author of
    `tools/outbound_send.py`, unlike every other arm in this module, because the
    defect was found after the slice that wrote the rest had finished. It has
    not been independently graded and should be.

    FOUND BY RUNNING THE REAL THING, not by reading it. A dry run against the
    live channel listed five destinations and the first was this project, which
    has an inbox like every other participant. A note delivered there would be
    read back by this repository's own watcher as inbound mail from itself.

    READ-ONLY AND WRITES NOTHING. It calls the discovery function directly
    against the real sibling root rather than driving the CLI, because the
    exclusion is keyed on a resolved path equal to the repository root and no
    synthetic channel can hold such a directory without a link this suite is not
    entitled to create. Listing a directory is not writing to it, so mechanism 1
    of the isolation guarantee is not weakened: `run_send` is still the only
    spawn site and still injects a synthetic channel root.

    A CONTROL FIRST, because the assertion is an ABSENCE. If this repository has
    no inbox of its own there is nothing to exclude and the arm would pass
    against any implementation at all, so that case skips rather than passing.

    Were this arm absent, restoring the one-clause change that excludes the
    repository would be green, and a broadcast would put a note this project
    wrote into the queue this project reads.
    """
    sender = load_sender()
    own_inbox = REPO_ROOT / INBOX
    if not own_inbox.is_dir():
        pytest.skip("this repository has no inbox of its own; there is nothing to exclude")

    holders = sender.inbox_holders(REPO_ROOT.parent)
    hit = REPO_ROOT.name in holders

    assert holders, "no sibling with an inbox was discovered; the arm cannot grade"
    assert not hit, "--all would deliver this repository's note into its own inbox"


def test_output_is_seven_bit_ascii(tmp_path: Path) -> None:
    """Prove both streams stay 7-bit ASCII, on a delivery and on a refusal.

    CLAUDE.md non-negotiable 4 covers authored content, and this tool's output
    is authored content that gets pasted into a reply and into a .ps1 alike -
    where PowerShell 5.1 ANSI-decodes a BOM-less script and a UTF-8 dash inside
    a double-quoted string terminates it at the tokenizer. Graded on BOTH
    outcomes because the refusal path is a different set of format strings from
    the delivery path, and it is the one carrying a reason string that arrives
    from another module.

    The offending bytes are collected as INTEGERS before asserting: rendering
    the stream itself into a pytest failure report would be an echo path.

    Were this arm absent, a refusal reason carrying an em dash would ship and
    would break a PowerShell consumer at the tokenizer rather than at the
    check.
    """
    channel = make_channel(tmp_path, with_inbox=(DEST_A,))
    env = base_env(tmp_path)
    notes = (
        clean_note(tmp_path),
        write_note(
            tmp_path,
            SECOND_NOTE_NAME,
            ("See " + WINDOWS_HOME_PATH + " for details.\n").encode("ascii"),
        ),
    )
    for note in notes:
        code, out, err = run_send(
            "--note",
            str(note),
            "--to",
            DEST_A,
            "--send",
            "--allow-unmeasured",
            channel=channel,
            env=env,
        )
        offending = sorted(
            {byte for blob in (out, err) for byte in blob if byte >= FIRST_NON_ASCII_BYTE}
        )

        assert code in CLOSED_EXIT_SET, f"exit {code} outside the closed set"
        assert not offending, f"non-ASCII byte(s) {offending} in the sender output"


def test_exit_codes_are_closed_set(tmp_path: Path) -> None:
    """Prove every code the sender returns is one of 0, 1, 2 and 3.

    A caller branches on this set, so a fifth code is an unhandled branch at
    every call site - and this tool's callers are the ones deciding whether
    bytes may leave. The subset check alone would be vacuous if no interesting
    path ran, so the arm also pins that the population actually CONTAINS a
    refusal and a usage error: two codes that are easy to conflate and that
    mean opposite things. 1 means the gate or the channel said no; 2 means
    nothing was graded at all.

    Were this arm absent, an unhandled traceback exiting 70, or a bare
    ``exit True``, would be caught by nothing here.
    """
    channel = make_channel(tmp_path, with_inbox=(DEST_A,))
    clean_env = base_env(tmp_path)
    note = clean_note(tmp_path)
    dirty = write_note(
        tmp_path, SECOND_NOTE_NAME, ("See " + POSIX_HOME_PATH + "\n").encode("ascii")
    )
    observed = set()

    code, _, _ = run_send(
        "--note",
        str(note),
        "--to",
        DEST_A,
        "--send",
        "--allow-unmeasured",
        channel=channel,
        env=clean_env,
    )
    observed.add(code)
    code, _, _ = run_send(
        "--note",
        str(dirty),
        "--to",
        DEST_A,
        "--send",
        "--allow-unmeasured",
        channel=channel,
        env=clean_env,
    )
    observed.add(code)
    code, _, _ = run_send("--note", str(note), "--no-such-flag958", channel=channel, env=clean_env)
    observed.add(code)
    code, _, _ = run_send(
        "--note",
        str(note),
        "--to",
        DEST_A,
        "--send",
        channel=channel,
        env=unmeasured_env(tmp_path),
    )
    observed.add(code)

    assert observed <= CLOSED_EXIT_SET, f"codes outside the closed set: {sorted(observed)}"
    assert EXIT_REFUSED in observed, "no refusal was exercised; the subset check would be vacuous"
    assert EXIT_USAGE in observed, "an unknown flag was not reported as a usage error"
