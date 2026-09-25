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
from types import ModuleType, SimpleNamespace

import pytest

from tests.conftest import Withheld

REPO_ROOT = Path(__file__).resolve().parents[1]
SENDER = REPO_ROOT / "tools" / "outbound_send.py"
GATE = REPO_ROOT / "tools" / "outbound_gate.py"

# WHICH PLATFORM, AND WHY AN ARM IS EVER ALLOWED TO ASK. The containment
# property is identical on both: a destination is accepted only when it
# RESOLVES to a project directly inside the channel root. What differs is the
# MECHANISM an arm has to build to attack it. Windows escapes through a
# junction and gives two spellings of one directory for free - it folds case
# and strips a trailing dot; POSIX escapes through a symlink, is
# case-SENSITIVE, and keeps the dot, so a second spelling of one directory has
# to be made rather than assumed. This constant selects the mechanism. It never
# selects whether an arm runs: an arm that skips on one platform is the vacuity
# this slice deleted elsewhere in this file, and a gate that skips its checks
# still reports PASS.
WINDOWS = os.name == "nt"

# The closed exit set, named rather than spelled inline. Named because a bare
# `== 1` is both a ruff PLR2004 magic value and unreadable at the call site:
# the whole contract of this tool is WHICH code came back.
EXIT_OK = 0
EXIT_REFUSED = 1
EXIT_USAGE = 2
EXIT_UNMEASURED = 3
EXIT_INCOMPLETE = 4
CLOSED_EXIT_SET = frozenset({EXIT_OK, EXIT_REFUSED, EXIT_USAGE, EXIT_UNMEASURED, EXIT_INCOMPLETE})

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

# CONTAINMENT AND IDENTITY (CS-958 F2, F3, F7). Four more populations, each
# named because the string a destination is SPELLED with and the directory it
# RESOLVES to are different things and this slice is about the difference.
#
#   DEST_ESCAPE      a junction under the channel root pointing OUT of it
#   DEST_MIRROR      a junction under the channel root pointing at the
#                    directory the arm is treating as this repository
#   DEST_SELF        that directory, which lives OUTSIDE the channel root so
#                    that its NAME differs from the name it is reachable by -
#                    which is what makes a name comparison distinguishable
#                    from a resolved-path comparison
#   OUTSIDE_DIR      an ordinary project, with an inbox, outside the channel
DEST_ESCAPE = "escape958"
DEST_MIRROR = "mirror958"
DEST_SELF = "selfrepo958"
OUTSIDE_DIR = "outside958"

# One directory, spelled three ways, ON EITHER PLATFORM - see
# :func:`spellings_of_one_directory`, which supplies the second and third
# spelling however the running platform makes them. A dedup keyed on the STRING
# sees three destinations and stages one temporary file three times (CS-958
# F7). The two alternate spellings are the ones Windows itself produces, so the
# POSIX fixture reproduces the Windows situation rather than inventing another.
DEST_A_UPPER = DEST_A.upper()
DEST_A_DOTTED = DEST_A + "."

NOTE_NAME = "note958-first.md"
SECOND_NOTE_NAME = "note958-second.md"

# METADATA (CS-958 F1). A synthetic credential shape, ASSEMBLED FROM FRAGMENTS
# so this file does not itself carry one - the same construction the gate uses
# for its own canary (tools/outbound_gate.py::CREDENTIAL_CANARIES). It is a
# well-formed AWS access key id, which the gate REFUSES in content and which is
# at the same time a perfectly legal filename and a perfectly legal directory
# name. That is the whole of F1 in one value: the identical string, refused in
# one place and stamped CLEAN in the other.
#
# THE 958 MARKER IS SEPARATED BY A HYPHEN ON PURPOSE. Every destination name in
# this file carries the marker (module docstring, mechanism 3), but appending
# it directly would put a word character where the rule's trailing ``\b`` needs
# a boundary and the value would stop being refused at all - a fixture that
# quietly grades nothing. Measured against the rule before these arms were
# written: bare, hyphen-marked and hyphen-marked-with-a-suffix all refuse.
#
# WITHHELD, BECAUSE THE VALUE IS THE GATE'S OWN AWS CANARY - CS-1177. The same
# assembled string is filed in tools/outbound_gate.py::CREDENTIAL_CANARIES, and a
# helper holding it as an argument printed it whenever it raised under
# --showlocals. The value is unchanged; only its repr is withheld.
SYNTHETIC_CREDENTIAL = Withheld("AKIA" + ("Q7" * 8))
DIRTY_NOTE_NAME = Withheld(SYNTHETIC_CREDENTIAL + "-958.md")
DEST_DIRTY = Withheld(SYNTHETIC_CREDENTIAL + "-958")

# Two links inside the channel, one at a clean destination and one at the dirty
# one. They are what separates grading the name an operator TYPED from grading
# the name the destination RESOLVES to - the second is the one that reaches
# stdout and the record.
ALIAS_TO_CLEAN = "alias958"
ALIAS_TO_DIRTY = "aliasdirty958"

# A name that is CLEAN on its own and REFUSED once the writer's staging suffix
# is appended to it. Assembled from fragments, like every other violating value
# in this file. The mechanism is a rule with a LENGTH FLOOR: the credential
# rules match a token run of twenty characters or more, and this run is
# nineteen - so the four characters of the suffix are what push it over.
# Measured in process before the arm was written: the base scans CLEAN and the
# base plus the suffix scans REFUSED.
STAGED_ONLY_NAME = "bearer " + ("a" * 19)

# The suffix the sender stages every destination through, and a label for the
# in-process probes that prove a fixture's asymmetry is real.
STAGING_SUFFIX = ".tmp"
PROBE_LABEL = "probe"

# How a metadata refusal tags the class it found. COUNTED rather than searched:
# one dirty name must produce ONE refusal, and a second copy would mean the
# name was graded twice - once as typed and once as resolved - which is what a
# mutant that survived the first cut of this slice actually did.
CREDENTIAL_TAG = "<pii:" + "credential>"

# The phrase that distinguishes a refusal about what a destination RESOLVES to
# from one about the spelling that was typed. Without it the two are byte
# identical and the operator inspects a name that was fine.
RESOLVED_PHRASE = "resolves to"

# The gate's own coverage header. Counted rather than searched, because the
# metadata grade must consume the gate's REFUSALS and not its coverage rows: a
# second block on one send would mean one machine's unmeasured class reported
# twice for one note.
COVERAGE_HEADER = "outbound-gate: coverage"

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


def make_directory_link(link: Path, target: Path) -> None:
    """Make a directory entry at ``link`` that RESOLVES to ``target``.

    THE MECHANISM IS THE PLATFORM'S; THE PROPERTY IS NOT. Containment is
    decided on the resolved path, and both platforms let a name inside the
    channel root resolve somewhere else - what differs is how. This helper owns
    that difference so no arm has to, and NEITHER PLATFORM IS ALLOWED TO SKIP:
    the escape is possible on both, so an arm that stopped grading on one would
    be green exactly where the hole is open.

    ON WINDOWS, A JUNCTION AND NOT A SYMLINK, because a junction needs no
    privilege while a directory symlink needs either an elevated token or
    developer mode - so an arm built on a symlink would skip on the operator's
    own machine and grade nothing. That is the same vacuity this slice is
    deleting elsewhere in this file.

    ON POSIX, AN ORDINARY DIRECTORY SYMLINK, which needs no privilege there and
    is the escape a POSIX runner actually has. ``mklink`` does not exist on
    that platform at all; the arms that used it unconditionally were the eight
    that went red in CI while the whole suite was green on Windows.

    FAILURE HERE IS A TEST FAILURE AND NOT A SKIP, on either platform.
    """
    link.parent.mkdir(parents=True, exist_ok=True)
    if not WINDOWS:
        link.symlink_to(target, target_is_directory=True)
        assert link.is_dir(), (
            "a directory symlink could not be created; this arm cannot grade containment"
        )
        return
    proc = subprocess.run(
        ["cmd", "/c", "mklink", "/J", str(link), str(target)],
        capture_output=True,
        timeout=TIMEOUT,
        check=False,
    )
    assert proc.returncode == 0, (
        "a directory junction could not be created; this arm cannot grade containment"
    )
    assert link.is_dir(), "the junction was reported created but is not a directory"


def spellings_of_one_directory(channel: Path, name: str) -> tuple[str, str, str]:
    """Three spellings that name ONE directory under ``channel``, per platform.

    WHY A HELPER RATHER THAN THREE LITERALS. The property under test is that
    the dedup is keyed on the RESOLVED inbox, so two spellings of one directory
    are one delivery and the record names the directory that EXISTS. Windows
    hands that fixture over for free, because Win32 folds case and strips a
    trailing dot from a path component - so ``alpha958``, ``ALPHA958`` and
    ``alpha958.`` are one directory there with nothing built. POSIX does
    neither: those are three DISTINCT names, two of which do not exist, and an
    arm that assumed otherwise measured the "no such destination" refusal while
    claiming to measure the dedup. That is what the eight CI failures were.

    So on POSIX the same three spellings are MADE to name one directory, with
    two directory symlinks beside it. The alternate spellings are deliberately
    the ones Windows itself produces, so the two platforms grade the same
    situation through each one's own mechanism rather than grading two
    different situations.

    THE MUTANT THIS KEEPS BITING ON BOTH PLATFORMS is CS-958 D1 mutant two:
    keying the dedup on the UNRESOLVED ``root / name / INBOX``. All three
    unresolved keys differ on POSIX - it compares case-sensitively and keeps
    the dot - and the dotted one differs on Windows, so the mutant stages one
    temporary file three times either way and the arm reds.

    Returns the spellings in typing order; the FIRST is the real directory's
    own name, which is the name the record must carry.
    """
    if not WINDOWS:
        for alias in (name.upper(), name + "."):
            make_directory_link(channel / alias, channel / name)
    return (name, name.upper(), name + ".")


def write_note(tmp_path: Path, name: str, payload: bytes) -> Path:
    """Write a note OUTSIDE the channel root and return its path.

    Outside deliberately: the arms compare a snapshot of the whole channel tree
    before and after a run, and a source note living inside the channel would
    be indistinguishable from a delivered one - and would also be discovered by
    ``--all`` if it happened to sit beside an inbox.

    CS-1177: the path is never bound to a name here. A note named after the
    synthetic credential has that credential in its path, and a helper that
    raises has its locals rendered under ``--showlocals``.
    """
    notes = tmp_path / "notes958"
    notes.mkdir(exist_ok=True)
    (notes / name).write_bytes(payload)
    return notes / name


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
    redirected = env.get(ENV_RECORD, "").endswith(RECORD_NAME)
    assert redirected, "the delivery record was not redirected out of the repository"
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


def assert_path_absent(needle: str, haystacks: tuple[bytes, ...]) -> None:
    """Assert a PATH appears in no blob, in no case and through no escaping.

    A SEPARATE FUNCTION FROM :func:`assert_absent_in_any_case` BECAUSE A PATH
    IS NOT AN ORDINARY NEEDLE, and the difference was measured rather than
    anticipated (CS-958 D5). The record arm searched the record's raw bytes for
    ``str(tmp_path)``; the record is JSON, JSON doubles every backslash, and a
    record plainly holding that path scored ZERO hits. The arm's two other
    needles carry no backslash at all, so they matched, and the line that
    asserted nothing sat between two that worked.

    So each blob is searched in three forms - as it is, with doubled
    backslashes collapsed, and with backslashes turned into forward slashes -
    and the needle in both separator spellings. Collapsing an escape can only
    ever CREATE a match, never hide one, which is the right direction of error
    for a check whose whole job is to fail when a path is present.

    The count is bound to a scalar before it is asserted, for the same reason
    the sibling helper does it: an asserted expression is rendered into the
    failure report, and this needle is an absolute path.
    """
    folded = needle.lower()
    assert folded, "an empty needle would make this check vacuous"
    needles = {folded, folded.replace("\\", "/")}
    hits = 0
    for blob in haystacks:
        raw = text(blob).lower()
        for form in (raw, raw.replace("\\\\", "\\"), raw.replace("\\\\", "/").replace("\\", "/")):
            hits += sum(form.count(one) for one in needles)
    assert hits == 0, f"a path that must not be recorded appeared {hits} time(s)"


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
    verdict = gate_verdict(note, env)
    assert verdict != EXIT_REFUSED, (
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
    recorded = len(record_entries(env))
    assert recorded == 0, "an unmeasured verdict recorded a delivery"

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
        recorded = len(record_entries(env))
        assert recorded == 0, "a refused whole-send wrote a record entry"
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
    recorded = len(record_entries(env))
    assert recorded == 0, "a refused send wrote a record entry"
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
    recorded = len(record_entries(env))
    assert recorded == 0, "undecodable bytes produced a record entry"
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
    verdict = gate_verdict(note, env)
    assert verdict != EXIT_REFUSED, (
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
    recorded = len(record_entries(env))
    assert recorded == len(expected), "the record does not match what was delivered"


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
    assert_path_absent(str(tmp_path), (raw,))
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


def test_all_does_not_broadcast_to_this_repository(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Prove `--all` excludes this repository from its own broadcast.

    AGAINST A SYNTHETIC ROOT, WHICH IS THE REPAIR TO THIS ARM. The version this
    replaces guarded on ``(REPO_ROOT / INBOX).is_dir()`` and skipped when it was
    absent. That directory is UNTRACKED, so the arm skipped in CI, in a fresh
    clone and in every worktree - which is this project's default session shape,
    so the arm was skipping in the exact place the work gets done. Measured on
    the worktree that repaired it: `33 passed, 1 skipped`, and this was the skip.
    A synthetic channel plus a monkeypatched repository root grades the same
    clause with nothing to guard on, so it always executes.

    IT COMPARES RESOLVED PATHS AND THE FIXTURE IS BUILT TO PROVE THAT. The
    directory standing in for this repository lives OUTSIDE the channel and is
    reachable inside it only through a link whose NAME IS DIFFERENT - a
    junction on Windows, a directory symlink on POSIX, and
    :func:`make_directory_link` owns which. So:

      * an implementation comparing ``entry.name`` to ``REPO_ROOT.name`` sees
        two different names, includes the junction, and this arm reds;
      * an implementation comparing ``entry`` to ``REPO_ROOT`` without
        ``.resolve()`` sees two different paths, includes the junction, and this
        arm reds.

    Both mutants shipped GREEN against the version this replaces. Both were
    planted against this version and both went red.

    A CONTROL IN THE SAME RUN, because the assertion is an absence: an ordinary
    sibling must still be discovered. Without it an ``inbox_holders`` that
    returned nothing at all would satisfy the exclusion completely.

    Were this arm absent, restoring the one-clause change that excludes the
    repository would be green, and a broadcast would put a note this project
    wrote into the queue this project reads.
    """
    sender = load_sender()
    channel = make_channel(tmp_path, with_inbox=(DEST_A,))
    fake_repo = tmp_path / DEST_SELF
    (fake_repo / INBOX).mkdir(parents=True)
    make_directory_link(channel / DEST_MIRROR, fake_repo)
    monkeypatch.setattr(sender, "REPO_ROOT", fake_repo.resolve())

    holders = sender.inbox_holders(channel)

    assert DEST_A in holders, "no ordinary sibling was discovered; the arm cannot grade"
    assert holders == [DEST_A], (
        f"--all would broadcast into this repository's own inbox; it discovered {holders}"
    )


# --------------------------------------------------------------------------
# CONTAINMENT AND IDENTITY. 16-20 - CS-958 F2, F3 and F7. Every arm below is
# about one idea: the string a destination is SPELLED with is not the directory
# it RESOLVES to, and only the resolved path can be graded for containment. A
# shape check on the string cannot see a reparse point, cannot see that two
# spellings are one directory, and cannot see that a name Win32 will rewrite
# lands somewhere the record does not say.
# --------------------------------------------------------------------------


def test_a_link_that_leaves_the_channel_root_is_refused(tmp_path: Path) -> None:
    """Prove a destination that resolves OUT of the channel root delivers nothing.

    CS-958 F3, reproduced end to end before it was repaired: `mklink /J` a
    junction under a synthetic root, `--to` it, and the tool reported
    `DELIVERED ... [gate CLEAN]` with exit 0 and the note written outside the
    root it was told to stay inside. The record holds no path by design, so
    nothing downstream could tell a contained delivery from an escaped one.

    THE ESCAPE IS THE RUNNING PLATFORM'S OWN - a junction on Windows, a
    directory symlink on POSIX - and :func:`make_directory_link` owns the
    difference. The property is one property: containment is decided on the
    resolved path, and both platforms can make a name inside the root resolve
    outside it. The first cut of this arm spelled `mklink` inline and was one
    of eight that could only run on Windows.

    THE ARM IS THE ABSENCE OUTSIDE THE ROOT AND NOT THE EXIT CODE. A tool that
    wrote the note and then returned 1 would satisfy an exit-code assertion
    completely, and the byte outside the channel is the irreversible half. So
    the tree OUTSIDE the channel is hashed before and after and nothing in it
    may differ.

    THE REFUSAL IS ALSO CHECKED FOR WHAT IT SAYS. This tool exists because
    outbound bytes leak, so a refusal that pasted the escaping path into stderr
    would report the fault by committing a smaller version of it.
    """
    channel = make_channel(tmp_path, with_inbox=(DEST_A,))
    outside = tmp_path / OUTSIDE_DIR
    (outside / INBOX).mkdir(parents=True)
    make_directory_link(channel / DEST_ESCAPE, outside)
    env = base_env(tmp_path)
    note = clean_note(tmp_path)
    before = tree_snapshot(outside)

    code, out, err = run_send(
        "--note",
        str(note),
        "--to",
        DEST_ESCAPE,
        "--send",
        "--allow-unmeasured",
        channel=channel,
        env=env,
    )
    escaped = changed_paths(before, tree_snapshot(outside))
    streams = text(out) + text(err)

    assert escaped == [], f"the send escaped the channel root and wrote {escaped}"
    assert code == EXIT_REFUSED, f"exit {code}; stdout {text(out)!r} stderr {text(err)!r}"
    recorded = len(record_entries(env))
    assert recorded == 0, "an escaping destination reached the record"
    assert not DRIVE_LETTER_RE.search(streams), "the refusal rendered an absolute path"


def test_an_ordinary_sibling_delivers_while_an_escaping_link_sits_beside_it(
    tmp_path: Path,
) -> None:
    """The NEGATIVE CONTROL for the whole containment set.

    Without it every refusal arm above and below is satisfied by a tool that
    refuses everything, and a containment check that rejected all destinations
    would look like four passing safety arms.

    THE LINK IS PRESENT AND SIMPLY NOT NAMED, which is the sharper control:
    it proves the check grades the destination that was ASKED for rather than
    the state of the channel. An implementation that refused any send whose root
    contained a reparse point anywhere would pass a control built on a clean
    channel and fail this one.
    """
    channel = make_channel(tmp_path, with_inbox=(DEST_A,))
    outside = tmp_path / OUTSIDE_DIR
    (outside / INBOX).mkdir(parents=True)
    make_directory_link(channel / DEST_ESCAPE, outside)
    env = base_env(tmp_path)
    note = clean_note(tmp_path)
    source = note.read_bytes()
    verdict = gate_verdict(note, env)
    assert verdict != EXIT_REFUSED, (
        "the gate refuses this suite's clean prose on this machine; the arm cannot grade"
    )

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
    landed = delivered(channel, DEST_A)

    assert code == EXIT_OK, f"exit {code}; stdout {text(out)!r} stderr {text(err)!r}"
    assert landed.is_file(), "an ordinary sibling was refused; the containment check refuses all"
    assert landed.read_bytes() == source, "the delivered bytes are not the source bytes"


def test_a_destination_resolving_to_this_repository_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Prove a `--to` naming this repository is refused, not only `--all`.

    CS-958 F2. The self-exclusion lived inside ``inbox_holders``, which ONLY
    ``--all`` calls; ``resolve_targets`` never consulted it. Merger-confirmed
    with its own positive control: ``resolve_targets`` at the real channel root
    resolved this repository's own name to this repository's own inbox with
    ZERO problems, while ``inbox_holders`` excluded it on the same run. The
    property the item cares about is that a note never lands in our own inbox;
    the code guarded only the path an operator does not have to take.

    THE REPOSITORY ROOT IS MONKEYPATCHED AND NOTHING REAL IS TOUCHED. The clause
    under test compares a resolved destination against ``REPO_ROOT``, so an
    honest fixture needs a directory that IS the repository root and sits under
    the channel root - and no synthetic channel can contain the real one. The
    constant is therefore pointed at a synthetic project inside a synthetic
    channel. The comparison being graded is the real one; only its right-hand
    side is fixture.

    THE POSITIVE CONTROL IS IN THE SAME RUN AND ON THE SAME NAME. Unpatched,
    that identical destination must resolve to exactly one target - so the
    refusal is attributable to the identity clause and not to a resolver that
    had already rejected the name for some unrelated reason.
    """
    sender = load_sender()
    channel = make_channel(tmp_path, with_inbox=(DEST_SELF, DEST_A))

    control, control_problems = sender.resolve_targets(channel, [DEST_SELF], NOTE_NAME)
    assert control_problems == [], f"the control could not resolve the name: {control_problems}"
    assert len(control) == 1, "the control resolved no target; the refusal below proves nothing"

    monkeypatch.setattr(sender, "SELF_ROOT", (channel / DEST_SELF).resolve())
    targets, problems = sender.resolve_targets(channel, [DEST_SELF], NOTE_NAME)

    assert targets == [], "a destination resolving to this repository was accepted"
    assert len(problems) == 1, f"expected exactly one problem, got {len(problems)}"
    assert not DRIVE_LETTER_RE.search(problems[0]), "the refusal rendered an absolute path"


def test_two_spellings_of_one_directory_collapse_to_one_destination(tmp_path: Path) -> None:
    """Prove two spellings of ONE directory are one target, not a false PARTIAL.

    CS-958 F7. ``dict.fromkeys`` dedups case-SENSITIVELY while Windows resolves
    case-INSENSITIVELY, so a pair of spellings naming one directory staged one
    temporary file twice and the second rename raised ``FileNotFoundError`` -
    because the first rename had already consumed it. The tool then reported a
    PARTIAL delivery over a destination that had landed completely, and wrote
    that partial into the record. A reconciler reading it would go looking for a
    delivery that had in fact succeeded.

    THE SECOND SPELLING COMES FROM :func:`spellings_of_one_directory`, which is
    the repair to this arm. It used to be ``DEST_A.upper()`` outright, which is
    one directory on Windows and a DIFFERENT, ABSENT one on POSIX - so in CI
    this arm measured the "no such destination" refusal while its name and its
    assertions claimed it measured the dedup. The property is not
    Windows-only; only the way a second spelling comes to exist is.

    FOUR ASSERTIONS BECAUSE FOUR THINGS WENT WRONG AT ONCE: the exit code, the
    stderr claim, the number of files that appeared in the channel, and the
    number of record entries. A repair that collapsed the target list but still
    recorded twice would satisfy the first three.
    """
    channel = make_channel(tmp_path, with_inbox=(DEST_A,))
    real, second, _ = spellings_of_one_directory(channel, DEST_A)
    env = base_env(tmp_path)
    note = clean_note(tmp_path)
    before = tree_snapshot(channel)

    code, out, err = run_send(
        "--note",
        str(note),
        "--to",
        real,
        "--to",
        second,
        "--send",
        "--allow-unmeasured",
        channel=channel,
        env=env,
    )
    changed = changed_paths(before, tree_snapshot(channel))
    partial = "PARTIAL" in text(err)

    assert code == EXIT_OK, f"exit {code}; stdout {text(out)!r} stderr {text(err)!r}"
    assert not partial, "a complete delivery to one directory was reported as partial"
    assert changed == [f"{DEST_A}/{INBOX}/{NOTE_NAME}"], f"the send changed {changed}"
    recorded = len(record_entries(env))
    assert recorded == 1, "one directory was recorded more than once"


def test_a_trailing_dot_is_recorded_under_the_name_the_directory_has(tmp_path: Path) -> None:
    """Prove the recorded destination names a directory that EXISTS.

    CS-958 F7, second half. Win32 strips a trailing dot from a path component,
    so a dotted spelling put the note in the undotted directory and filed it in
    the record under the dotted name - a name no destination on this channel
    has. The record is the only thing a later CS-951 reconciler has, and a
    reconciler looking for that destination finds nothing and cannot tell a
    misfiled delivery from a vanished one.

    THIS IMPLEMENTATION RESOLVES RATHER THAN REFUSES, and the choice is asserted
    here so it is visible rather than incidental. Both were open. Resolving is
    chosen because the containment check already proves the resolved directory
    is a project directly under the channel root, so the delivery is contained
    either way; refusing would add a second rule about strings on top of a check
    that does not need one, which is the exact mistake this slice is undoing.
    What must not happen is what the tool did before: deliver to one name and
    record another.

    Measured on this machine before the arm was written: the dotted spelling
    resolves to the undotted directory and ``is_dir()`` is true for both.

    ON POSIX THE DOT IS KEPT, so the dotted spelling is made to name the same
    directory through a symlink instead - :func:`spellings_of_one_directory`.
    The graded property is unchanged and is not about dots at all: the recorded
    destination must be the RESOLVED directory's own name and not the spelling
    that was typed. Asserting the Windows rewrite as though it were universal
    is what made this arm one of the eight that failed in CI.
    """
    channel = make_channel(tmp_path, with_inbox=(DEST_A,))
    _, _, dotted = spellings_of_one_directory(channel, DEST_A)
    env = base_env(tmp_path)
    note = clean_note(tmp_path)
    before = tree_snapshot(channel)

    code, out, err = run_send(
        "--note",
        str(note),
        "--to",
        dotted,
        "--send",
        "--allow-unmeasured",
        channel=channel,
        env=env,
    )
    changed = changed_paths(before, tree_snapshot(channel))
    names = sorted(record_strings(record_entries(env)))
    dotted_in_record = DEST_A_DOTTED in names

    assert code == EXIT_OK, f"exit {code}; stdout {text(out)!r} stderr {text(err)!r}"
    assert changed == [f"{DEST_A}/{INBOX}/{NOTE_NAME}"], f"the send changed {changed}"
    assert DEST_A in names, "the record does not name the directory the note landed in"
    assert not dotted_in_record, "the record files the delivery under a name no directory has"


def test_a_refused_destination_is_not_echoed_back(tmp_path: Path) -> None:
    """Prove the shape refusal does not print the value it refused.

    MEASURED BEFORE THE ARM WAS WRITTEN, on the unrepaired tool: a `--to`
    carrying a drive-qualified home path came back as
    ``destination '<the whole path>' is not a plain project name``. The one
    refusal whose job is to catch a name that is secretly a PATH was the one
    that rendered the path, and a home path is personal data under CLAUDE.md
    non-negotiable 12 - which counts error messages as echo paths explicitly.
    The operator pastes a refusal into a session; that is how it leaves.

    A POSITIVE CONTROL IN THE SAME RUN, because the assertion is an absence and
    an absence is satisfied by a tool that printed nothing at all: the refusal
    must still say WHICH destination in the list was the bad one, so the
    ordinal has to be there. Without that half, deleting the message entirely
    would be green and the operator would be told a send was refused with no
    way to tell which of five names did it.

    THE DRIVE-LETTER REGEX IS THE LOAD-BEARING CHECK AND THE SUBSTRING IS NOT,
    which was itself measured here: the unrepaired message rendered the value
    through ``repr()``, so every backslash arrived DOUBLED and a whole-path
    substring search found nothing while the path was plainly on stderr. The
    substring check therefore asks for the one component that survives repr
    escaping intact, and the regex asks the question that cannot be escaped
    around.
    """
    channel = make_channel(tmp_path, with_inbox=(DEST_A,))
    env = base_env(tmp_path)
    note = clean_note(tmp_path)
    before = tree_snapshot(channel)

    code, out, err = run_send(
        "--note",
        str(note),
        "--to",
        DEST_A,
        "--to",
        WINDOWS_HOME_PATH,
        "--send",
        "--allow-unmeasured",
        channel=channel,
        env=env,
    )
    changed = changed_paths(before, tree_snapshot(channel))

    assert code == EXIT_REFUSED, f"exit {code}; stdout {text(out)!r} stderr {text(err)!r}"
    assert changed == [], f"a refused send still wrote {changed}"
    assert_absent_in_any_case(WINDOWS_HOME_PATH.split("\\")[2], (out, err))
    assert not DRIVE_LETTER_RE.search(text(out) + text(err)), (
        "the refusal rendered an absolute path"
    )
    assert "destination 2" in text(err), (
        "the refusal does not say which destination was refused; it is unusable"
    )


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
    """Prove every code the sender returns is one of 0, 1, 2, 3 and 4.

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


# --------------------------------------------------------------------------
# THE REPAIR PASS ON S1 - CS-958 D1, D2, D3 and D5. Every arm below exists
# because the FIRST cut of this slice shipped a green 40 of 40 over three
# subtle mutants that each restored a measured finding of this item, an
# ordinal that counted the wrong list, an identity binding no arm could see,
# and one assertion that searched a JSON blob for a string JSON does not
# contain. The mechanism held; what GRADED it did not.
# --------------------------------------------------------------------------


def git_main_checkout() -> Path:
    """The main checkout behind this test process, asked of GIT and not of the module.

    AN INDEPENDENT ORACLE ON PURPOSE. The thing under test derives this same
    answer by reading `.git` itself, so an arm that asked the module for it
    would be comparing an implementation against itself. `git worktree list`
    names the main worktree first, and that is a fact about the repository
    rather than about the file being graded.
    """
    proc = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "worktree", "list", "--porcelain"],
        capture_output=True,
        timeout=TIMEOUT,
        check=False,
    )
    assert proc.returncode == 0, "git could not list this repository's worktrees"
    first = text(proc.stdout).splitlines()[0]
    assert first.startswith("worktree "), "git worktree list did not name a worktree first"
    return Path(first.split(" ", 1)[1].strip()).resolve()


def add_probe_worktree(tmp_path: Path) -> Path:
    """Create a REAL git worktree of this repository and return its root.

    A REAL ONE, because the defect this fixture exists for is invisible to any
    imitation of it: `Path(__file__).resolve().parents[1]` is a correct answer
    in a normal checkout and a wrong answer in a worktree, and the only thing
    that tells them apart is a `.git` that is a FILE carrying a `gitdir:`
    line. A directory with a hand-written `.git` file would grade the parser
    and not the property.

    THE WORKING TREE'S SENDER IS COPIED IN OVER THE CHECKED-OUT ONE, and that
    is not a shortcut - it is what makes the arm grade the code being edited.
    `git worktree add` checks out a COMMIT, so without the copy this arm would
    silently grade HEAD and report a repair as broken while it worked, or as
    working while it was reverted. The property under test is about the SHAPE
    of the checkout - a `.git` that is a file - and the copy leaves that shape
    untouched.

    The worktree is removed by the caller. It is never entered by any shell -
    the tests drive it by absolute path only.
    """
    probe = tmp_path / "s1r-probe-worktree"
    proc = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "worktree", "add", "--detach", str(probe), "HEAD"],
        capture_output=True,
        timeout=TIMEOUT,
        check=False,
    )
    assert proc.returncode == 0, "a probe worktree could not be created; this arm cannot grade"
    assert (probe / ".git").is_file(), "the probe worktree has no .git FILE; it is not a worktree"
    (probe / "tools" / "outbound_send.py").write_bytes(SENDER.read_bytes())
    return probe


def remove_probe_worktree(probe: Path) -> None:
    """Remove a probe worktree AND its metadata under the main checkout's .git."""
    subprocess.run(
        ["git", "-C", str(REPO_ROOT), "worktree", "remove", "--force", str(probe)],
        capture_output=True,
        timeout=TIMEOUT,
        check=False,
    )
    subprocess.run(
        ["git", "-C", str(REPO_ROOT), "worktree", "prune"],
        capture_output=True,
        timeout=TIMEOUT,
        check=False,
    )


def run_copy_dry(sender: Path, *args: str, env: dict[str, str]) -> tuple[int, bytes, bytes]:
    """Drive an ARBITRARY copy of the sender, DRY RUN ONLY, and return the result.

    THIS IS THE ONE SPAWN SITE IN THIS FILE THAT DOES NOT GO THROUGH
    :func:`run_send`, and the exception is deliberate and narrow. The property
    being graded is that a copy running from a worktree still knows which
    channel participant it IS, and that property is only visible at the REAL
    channel root - no synthetic root can contain the real repository, which is
    exactly why the arm this replaces had to monkeypatch the answer and
    therefore graded nothing.

    THE SAFETY IS MECHANICAL, NOT A PROMISE. `--send` is refused here by
    assertion, so every call is a dry run and writes no byte anywhere; the
    delivery record is still redirected out of the repository by the same
    :data:`ENV_RECORD` mechanism every other arm uses. A dry run against the
    real channel root reads directories and prints; a broken build reports
    "would deliver" and still writes nothing, which is what makes it safe to
    grade the broken case at all.
    """
    assert "--send" not in args, "this helper is dry-run only and must never deliver"
    assert sender.is_file(), "the sender copy under test does not exist"
    redirected = env.get(ENV_RECORD, "").endswith(RECORD_NAME)
    assert redirected, "the delivery record was not redirected out of the repository"
    proc = subprocess.run(
        [sys.executable, str(sender), *args],
        capture_output=True,
        env=env,
        timeout=TIMEOUT,
        check=False,
    )
    return proc.returncode, proc.stdout, proc.stderr


IDENTITY_PROBE = """
import importlib.util
import sys
from pathlib import Path

spec = importlib.util.spec_from_file_location("s1r_identity_probe", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
main_checkout = Path(sys.argv[2])
print("SAME" if module.SELF_ROOT == main_checkout else "OTHER")
print("DIFFERS" if module.REPO_ROOT != main_checkout else "IDENTICAL")
"""


def test_the_identity_binding_survives_a_worktree(tmp_path: Path) -> None:
    """Prove a copy running from a WORKTREE still knows it is the main checkout.

    CS-958 D3, and the reason the first cut of this slice was refuted. The
    acceptance clause it added compares a resolved destination against this
    repository's root, and both arms that graded that clause monkeypatched the
    root. A MONKEYPATCH THAT SUPPLIES THE VALUE UNDER TEST CONVERTS AN
    INTEGRATION PROPERTY INTO A UNIT TAUTOLOGY: the clause was graded and the
    BINDING never was, so a copy running from a worktree - which is this
    project's default session shape - computed its identity as the worktree and
    resolved this repository's own name into this repository's own inbox
    exactly as before the repair.

    THREE MEASUREMENTS, AND THE FIRST IS THE LOAD-BEARING ONE because it is the
    only one that can never go vacuous:

      1. a real worktree is created with `git worktree add`, the sender is
         imported FROM IT in a child process, and its computed identity must
         equal the main checkout. The child also reports whether the file-
         relative root DIFFERS from the main checkout, which is the non-vacuity
         control: if the fixture were not really a worktree, both answers would
         be trivially true and the arm would grade nothing;
      2. the same copy is asked, AS A SUBPROCESS AND AS A DRY RUN, to deliver
         to the main checkout's own directory name at the real channel root,
         and must refuse. This is the end-to-end shape of the finding. Where
         this repository has no inbox of its own - a fresh clone, a CI runner -
         the refusal arrives for the more boring reason instead, so the sharper
         assertion is made only when there is something to grade and the arm
         still requires the refusal either way. It never skips;
      3. a positive control on the same copy: the SAME destination name against
         a synthetic channel root containing an ordinary directory of that name
         must be accepted, which proves the refusal is about a resolved path
         and not about the string.

    NOTHING IS EVER DELIVERED BY THIS ARM. :func:`run_copy_dry` refuses
    `--send` by assertion, and a dry run writes no byte even when the code
    under test is the broken one - which is what makes the broken case safe to
    measure at all.
    """
    if not (REPO_ROOT / ".git").exists():
        pytest.skip("this checkout carries no .git at all; there is no worktree binding to grade")
    main_checkout = git_main_checkout()
    probe = add_probe_worktree(tmp_path)
    try:
        probe_sender = probe / "tools" / "outbound_send.py"
        script = tmp_path / "s1r_identity_probe.py"
        script.write_text(IDENTITY_PROBE, encoding="ascii")
        env = base_env(tmp_path)
        note = clean_note(tmp_path)

        proc = subprocess.run(
            [sys.executable, str(script), str(probe_sender), str(main_checkout)],
            capture_output=True,
            env=env,
            timeout=TIMEOUT,
            check=False,
        )
        answers = text(proc.stdout).split()

        assert proc.returncode == 0, f"the identity probe failed: {text(proc.stderr)[:400]!r}"
        assert answers[1:] == ["DIFFERS"], (
            "the probe copy's file-relative root already equals the main checkout, "
            "so this fixture is not a worktree and the arm would grade nothing"
        )
        assert answers[:1] == ["SAME"], (
            "a copy running from a worktree computes its identity as the worktree; "
            "--to this repository's own name would resolve into its own inbox"
        )

        sharp = (main_checkout / INBOX).is_dir()
        code, out, err = run_copy_dry(
            probe_sender,
            "--note",
            str(note),
            "--to",
            main_checkout.name,
            "--channel-root",
            str(main_checkout.parent),
            "--allow-unmeasured",
            env=env,
        )
        streams = text(out) + text(err)

        assert code == EXIT_REFUSED, f"exit {code}; a send to this repository was not refused"
        assert "DRY RUN" not in streams, "the tool offered to deliver into this repository"
        if sharp:
            assert "does not resolve to a project" in streams, (
                "the refusal is not the containment and identity refusal; "
                "it came from somewhere else and this arm did not grade the clause"
            )

        decoy = make_channel(tmp_path, with_inbox=(main_checkout.name,))
        control_code, control_out, control_err = run_copy_dry(
            probe_sender,
            "--note",
            str(note),
            "--to",
            main_checkout.name,
            "--channel-root",
            str(decoy),
            "--allow-unmeasured",
            env=env,
        )

        assert control_code == EXIT_OK, (
            f"exit {control_code}; stderr {text(control_err)!r} - the control was refused too, "
            "so the refusal above is not attributable to the identity clause"
        )
        assert "DRY RUN" in text(control_out), "the control did not reach the dry-run report"
    finally:
        remove_probe_worktree(probe)


def test_a_look_alike_grandparent_is_not_the_channel_root(tmp_path: Path) -> None:
    """Prove containment compares PATHS and not the grandparent's NAME.

    CS-958 D1, mutant one of three. Replacing the containment comparison with
    `project.parent.name != resolved_root.name` shipped a green 40 of 40 on the
    first cut of this slice and RESTORED F3 verbatim: a junction under the
    channel root delivered a note outside it at exit 0. Every containment arm
    stayed green because in each of their fixtures the escape target's parent
    was pytest's own temporary directory, whose NAME differs from the channel
    root's anyway - a name comparison and a path comparison agreed by accident.

    So this fixture makes them disagree on purpose. The escape target sits
    inside a SECOND directory that carries the channel root's own name, at a
    different place in the tree. A name comparison sees the channel root and
    accepts; a path comparison sees somewhere else and refuses.

    THE ARM IS THE ABSENCE OUTSIDE THE ROOT, not the exit code: a tool that
    wrote the note and then returned 1 would satisfy an exit-code assertion
    completely, and the byte outside the channel is the irreversible half.
    """
    channel = make_channel(tmp_path, with_inbox=(DEST_A,))
    look_alike = tmp_path / "decoy958" / CHANNEL_DIR_NAME
    outside = look_alike / OUTSIDE_DIR
    (outside / INBOX).mkdir(parents=True)
    make_directory_link(channel / DEST_ESCAPE, outside)
    env = base_env(tmp_path)
    note = clean_note(tmp_path)
    before = tree_snapshot(look_alike)

    code, out, err = run_send(
        "--note",
        str(note),
        "--to",
        DEST_ESCAPE,
        "--send",
        "--allow-unmeasured",
        channel=channel,
        env=env,
    )
    escaped = changed_paths(before, tree_snapshot(look_alike))

    assert escaped == [], f"the send escaped into a look-alike tree and wrote {escaped}"
    assert code == EXIT_REFUSED, f"exit {code}; stdout {text(out)!r} stderr {text(err)!r}"
    recorded = len(record_entries(env))
    assert recorded == 0, "an escaping destination reached the record"


def test_three_spellings_of_one_directory_are_one_delivery(tmp_path: Path) -> None:
    """Prove the dedup is keyed on the RESOLVED inbox, not on the joined path.

    CS-958 D1, mutant two of three, and it restored F7 verbatim. Keying the
    dedup on the UNRESOLVED `root / name / INBOX` shipped green because
    `PurePath` comparison on Windows is already case-INSENSITIVE, so the
    existing pair-of-case-variants arm could not tell the two keys apart. A
    TRAILING DOT can: Win32 strips it from a path component while `Path` keeps
    it, so the dotted and undotted spellings are different unresolved keys and
    the same resolved directory.

    Under that mutant the same temporary file is staged twice, the first rename
    consumes it, the second raises `FileNotFoundError`, and a delivery that
    landed completely is reported and RECORDED as partial - which is the lie a
    CS-951 reconciler would later act on.

    THREE SPELLINGS RATHER THAN TWO because the fault is a pair that survives
    one comparison and not another, and a third spelling costs nothing.

    AND THE MUTANT DIES ON BOTH PLATFORMS, which is why the spellings come from
    :func:`spellings_of_one_directory` rather than from the two literals. POSIX
    compares case-SENSITIVELY and keeps the dot, so all three unresolved keys
    differ there; Windows folds the case, so only the dotted key differs. Under
    the mutant the same temporary file is staged three times either way.
    """
    channel = make_channel(tmp_path, with_inbox=(DEST_A,))
    first, second, third = spellings_of_one_directory(channel, DEST_A)
    env = base_env(tmp_path)
    note = clean_note(tmp_path)
    before = tree_snapshot(channel)

    code, out, err = run_send(
        "--note",
        str(note),
        "--to",
        first,
        "--to",
        second,
        "--to",
        third,
        "--send",
        "--allow-unmeasured",
        channel=channel,
        env=env,
    )
    changed = changed_paths(before, tree_snapshot(channel))
    partial = "PARTIAL" in text(err)

    assert code == EXIT_OK, f"exit {code}; stdout {text(out)!r} stderr {text(err)!r}"
    assert not partial, "a complete delivery to one directory was reported as partial"
    assert changed == [f"{DEST_A}/{INBOX}/{NOTE_NAME}"], f"the send changed {changed}"
    recorded = len(record_entries(env))
    assert recorded == 1, "one directory was recorded more than once"


def test_a_non_canonical_channel_root_still_contains(tmp_path: Path) -> None:
    """Prove the channel root is CANONICALISED before anything is compared to it.

    CS-958 D1, mutant three of three, and the one whose survival names a shape
    rather than a line. Dropping `.resolve()` from the channel root shipped
    green for a reason that has nothing to do with the code: pytest hands out
    an ALREADY-RESOLVED `tmp_path`, so the single arm that called
    `resolve_targets` directly passed a root the implementation would have
    resolved to itself. A FIXTURE BUILT PARALLEL TO THE IMPLEMENTATION IS THE
    SHAPE THAT MAKES AN ARM AGREE WITH A BUG.

    So this arm passes a root that is deliberately not canonical - it walks
    into a destination and back out through `..`, naming the same directory by
    a path no comparison will match literally. Without the resolve, every
    destination under it is refused as though it were outside the channel; with
    it, the ordinary destination resolves exactly as the control does.

    THE CONTROL IS THE CANONICAL SPELLING IN THE SAME RUN, so a resolver that
    refused everything cannot satisfy this arm by refusing both.
    """
    sender = load_sender()
    channel = make_channel(tmp_path, with_inbox=(DEST_A,))
    non_canonical = channel / DEST_A / ".."
    is_literally_different = non_canonical != channel

    control, control_problems = sender.resolve_targets(channel, [DEST_A], NOTE_NAME)
    targets, problems = sender.resolve_targets(non_canonical, [DEST_A], NOTE_NAME)

    assert is_literally_different, "the fixture root is already canonical; the arm grades nothing"
    assert control_problems == [], f"the canonical control failed: {control_problems}"
    assert len(control) == 1, "the canonical control resolved no target; the arm cannot grade"
    assert problems == [], f"a non-canonical channel root refused its own destination: {problems}"
    assert len(targets) == 1, "a non-canonical channel root resolved no target"


def test_the_ordinal_counts_the_names_the_operator_typed(tmp_path: Path) -> None:
    """Prove a refusal's ordinal is a position in what was TYPED.

    CS-958 D2. The refusal reports an ordinal rather than the value it refused,
    because the one check whose job is to catch a name that is secretly a path
    must not print the path. That is only useful if the number is true of the
    list the operator has in front of them, and it was not: `main` deduplicated
    `--to` with `dict.fromkeys` BEFORE the resolver enumerated, so every
    repeated spelling shifted every later position left. Measured on the first
    cut: a fault at the fifth typed name reported as `destination 3`.

    An ordinal that points at the wrong name is worse than no ordinal, because
    the operator edits a name that was fine and re-runs into the same refusal.

    THE DUPLICATES ARE THE FIXTURE. Four repetitions of one good name in front
    of one bad one, so the reported position and the deduplicated position
    cannot coincide, and the arm asserts the wrong number is ABSENT as well as
    that the right one is present - a message naming both would otherwise pass.
    """
    channel = make_channel(tmp_path, with_inbox=(DEST_A,))
    env = base_env(tmp_path)
    note = clean_note(tmp_path)
    before = tree_snapshot(channel)

    code, out, err = run_send(
        "--note",
        str(note),
        "--to",
        DEST_A,
        "--to",
        DEST_A,
        "--to",
        DEST_A,
        "--to",
        DEST_A,
        "--to",
        WINDOWS_HOME_PATH,
        "--send",
        "--allow-unmeasured",
        channel=channel,
        env=env,
    )
    changed = changed_paths(before, tree_snapshot(channel))
    streams = text(out) + text(err)

    assert code == EXIT_REFUSED, f"exit {code}; stdout {text(out)!r} stderr {text(err)!r}"
    assert changed == [], f"a refused send still wrote {changed}"
    assert "destination 5" in streams, "the refusal does not name the position that was typed"
    assert "destination 2" not in streams, (
        "the refusal names the position in the DEDUPLICATED list, which the operator never saw"
    )
    assert not DRIVE_LETTER_RE.search(streams), "the refusal rendered an absolute path"


def test_a_discovered_destination_is_not_reported_as_an_ordinal(tmp_path: Path) -> None:
    """Prove `--all` does not answer a refusal with a position in a list nobody saw.

    CS-958 D2, second half. Under `--all` the operator types no destination at
    all, so an ordinal indexes a sorted discovery list they have never seen and
    cannot act on: `destination 1` names nothing they can edit. The refusal
    must instead say that the destination was DISCOVERED and tell them the one
    move that makes the fault locatable, which is to name destinations
    explicitly.

    THE FIXTURE IS A DOT-PREFIXED SIBLING because it is the cheapest discovered
    destination the shape check refuses, and it needs no reparse point.

    SCOPE, STATED SO A LATER READER DOES NOT MIS-READ THIS ARM AS AN
    ENDORSEMENT: that one unusable sibling refuses the WHOLE broadcast is a
    separate open finding of this item (D4) about the WIDTH of the refusal.
    This arm pins only what the diagnostic says, and deliberately asserts
    nothing about whether refusing everything was the right call.
    """
    channel = make_channel(tmp_path, with_inbox=(DEST_A,))
    (channel / ".hidden958" / INBOX).mkdir(parents=True)
    env = base_env(tmp_path)
    note = clean_note(tmp_path)
    before = tree_snapshot(channel)

    code, out, err = run_send(
        "--note",
        str(note),
        "--all",
        "--send",
        "--allow-unmeasured",
        channel=channel,
        env=env,
    )
    changed = changed_paths(before, tree_snapshot(channel))
    streams = text(out) + text(err)
    ordinals = [token for token in ("destination 1", "destination 2") if token in streams]

    assert code == EXIT_REFUSED, f"exit {code}; stdout {text(out)!r} stderr {text(err)!r}"
    assert changed == [], f"a refused broadcast still wrote {changed}"
    assert ordinals == [], f"a discovered destination was reported by ordinal: {ordinals}"
    assert "--to" in streams, "the refusal offers the operator no way to locate the destination"
    assert not DRIVE_LETTER_RE.search(streams), "the refusal rendered an absolute path"


def test_the_record_path_check_can_see_a_json_escaped_path(tmp_path: Path) -> None:
    """Prove the record's absolute-path check is not vacuous. THE CONTROL FOR AN ARM.

    CS-958 D5. `test_the_record_holds_no_absolute_path_and_no_payload` searched
    the record's RAW BYTES for `str(tmp_path)`, and a JSON encoder doubles
    every backslash - so a record plainly holding that path scored zero hits
    while the arm's other two needles, which carry no backslash, scored one
    each and looked like proof the check worked. The arm's other assertions
    still bite; that one line asserted nothing at all.

    THIS ARM GRADES THE CHECK RATHER THAN THE TOOL, which is why it plants the
    value itself: a positive control that must RAISE, a negative control that
    must not, and a third measurement pinning the defect itself - that a naive
    substring search over the same planted blob really does score zero - so
    that a later reader can see the vacuity was reproduced rather than
    reasoned about.

    THE THIRD MEASUREMENT ASKS THE ENCODER RATHER THAN ASSUMING THE ANSWER. The
    vacuity needs a path carrying a character JSON escapes, and only Windows
    hands one over: a POSIX temporary directory holds no backslash, so the
    naive search finds it and scoring zero would be the surprising result. The
    first cut hardcoded the Windows answer and went red in CI on a check whose
    whole subject is a false negative. So the expectation is DERIVED - the
    encoder is asked whether it altered this platform's path, and the naive hit
    count must match that answer. The two controls above are unconditional and
    grade identically on both platforms.
    """
    planted = json.dumps({"destination": str(tmp_path)}).encode("ascii")
    clean = json.dumps({"destination": DEST_A}).encode("ascii")
    naive_hits = text(planted).lower().count(str(tmp_path).lower())
    # True when this platform's path survives JSON encoding unaltered, which is
    # exactly when a naive substring search can still find it.
    encoded_intact = json.dumps(str(tmp_path)) == '"%s"' % str(tmp_path)
    expected_hits = 1 if encoded_intact else 0

    with pytest.raises(AssertionError):
        assert_path_absent(str(tmp_path), (planted,))
    assert_path_absent(str(tmp_path), (clean,))

    assert naive_hits == expected_hits, (
        "a plain substring search over the planted blob disagrees with what this "
        "platform's JSON encoder did to the path, so the defect this arm exists "
        "for is no longer reproducible as described and the arm should be re-read"
    )


# --------------------------------------------------------------------------
# METADATA. 27-38 - CS-958 F1, the severe finding, and slice S2. `grade()`
# takes `payload: bytes` and nothing else, so a note's FILENAME and a
# destination's NAME were never graded at all: the gate stood in FRONT of the
# payload and BESIDE everything else. The same value the gate REFUSES in
# content shipped as a filename into every sibling inbox, was echoed to stdout,
# and was recorded under `"gate_verdict": "CLEAN"` - a record that permanently
# attests a grade which never covered the strings it holds. Every arm below is
# one idea: a string that leaves this machine is graded before anything prints
# it or records it, whether it is content or a name.
#
# EVERY ARM CARRIES A POSITIVE CONTROL IN THE SAME RUN, because every assertion
# here is an ABSENCE - a value not on the streams, a note not delivered, a
# record not written - and an absence is satisfied completely by a tool that
# refuses everything or prints nothing.
# --------------------------------------------------------------------------


def test_a_dirty_filename_refuses_the_send_and_is_never_echoed(tmp_path: Path) -> None:
    """Prove a note whose FILENAME the gate refuses is not delivered, or printed.

    CS-958 F1 end to end. Reproduced on the unrepaired tool: a note whose
    filename is a well-formed credential delivered at exit 0 with
    `DELIVERED <the credential> to 1 destination(s) ... [gate CLEAN]`, while the
    identical string placed in the note's CONTENT was refused at exit 1. The
    filename then sat in a sibling's inbox, in this project's record, and in
    whatever the operator pasted the stdout line into.

    THE CONTROL IS THE INSTRUMENT AND RUNS FIRST. The load-bearing assertion is
    that a value does NOT appear on the streams, which is satisfied by a tool
    that prints nothing at all - so a clean note is sent first and its filename
    MUST appear on the streams. That is the proof this arm can see a filename
    when one is printed.

    THE ASSERTED EXPRESSION NEVER CARRIES THE VALUE (CS-850). The count is
    bound to a scalar first, and the message names the fault rather than the
    string, because pytest renders the expression it was given.
    """
    channel = make_channel(tmp_path, with_inbox=(DEST_A,))
    env = base_env(tmp_path)
    control_note = clean_note(tmp_path)
    dirty = clean_note(tmp_path, name=DIRTY_NOTE_NAME)

    control_code, control_out, control_err = run_send(
        "--note",
        str(control_note),
        "--to",
        DEST_A,
        "--send",
        "--allow-unmeasured",
        channel=channel,
        env=env,
    )
    control_streams = text(control_out) + text(control_err)
    after_control = tree_snapshot(channel)

    code, out, err = run_send(
        "--note",
        str(dirty),
        "--to",
        DEST_A,
        "--send",
        "--allow-unmeasured",
        channel=channel,
        env=env,
    )
    changed = changed_paths(after_control, tree_snapshot(channel))
    streams = text(out) + text(err)
    leaked = streams.count(SYNTHETIC_CREDENTIAL)
    entries = len(record_entries(env))

    assert control_code == EXIT_OK, f"the control was refused; stderr {text(control_err)!r}"
    assert NOTE_NAME in control_streams, (
        "the control's filename never reached the streams, so this arm cannot see one"
    )
    assert code == EXIT_REFUSED, f"exit {code}; a refused filename did not refuse the send"
    assert changed == [], f"a note with a refused filename was still written: {changed}"
    assert leaked == 0, "the refusal echoed the value it refused"
    assert entries == 1, f"{entries} record entries; the refused send reached the record"


def test_a_dirty_filename_is_refused_before_the_dry_run_line_prints_it(tmp_path: Path) -> None:
    """Prove the grade happens BEFORE the line that echoes the name, not after.

    THE ORDER OF OPERATIONS IS THE REPAIR. A tool that graded the filename
    after resolving destinations and printing its report would satisfy every
    delivery assertion in the arm above - nothing is written by a dry run
    either - while still having put the value on stdout, which is the echo path
    CLAUDE.md non-negotiable 12 names explicitly. A dry run is the sharpest
    place to measure it, because the DRY RUN line's whole content is the note's
    name and the destinations.

    THE CONTROL IS A CLEAN DRY RUN IN THE SAME RUN, and it must reach the DRY
    RUN line with its filename on it. Without that half, a tool that refused
    every dry run would pass.
    """
    channel = make_channel(tmp_path, with_inbox=(DEST_A,))
    env = base_env(tmp_path)
    control_note = clean_note(tmp_path)
    dirty = clean_note(tmp_path, name=DIRTY_NOTE_NAME)

    control_code, control_out, control_err = run_send(
        "--note", str(control_note), "--to", DEST_A, "--allow-unmeasured", channel=channel, env=env
    )
    control_streams = text(control_out) + text(control_err)

    code, out, err = run_send(
        "--note", str(dirty), "--to", DEST_A, "--allow-unmeasured", channel=channel, env=env
    )
    streams = text(out) + text(err)
    leaked = streams.count(SYNTHETIC_CREDENTIAL)

    assert control_code == EXIT_OK, f"the control was refused; stderr {text(control_err)!r}"
    assert "DRY RUN" in control_streams, "the control never reached the dry-run report"
    assert NOTE_NAME in control_streams, "the dry-run report does not print the note's name"
    assert code == EXIT_REFUSED, f"exit {code}; a dry run accepted a refused filename"
    assert "DRY RUN" not in streams, "the dry-run report was reached with an ungraded filename"
    assert leaked == 0, "the refusal echoed the value it refused"


def test_a_typed_destination_whose_name_is_dirty_refuses_the_whole_send(tmp_path: Path) -> None:
    """Prove a dirty DESTINATION name refuses everything, including the clean ones.

    THE SETTLED DECISION IS ASSERTED HERE SO IT IS VISIBLE RATHER THAN
    INCIDENTAL (the S2 spec, decision 2): a dirty name does not rename, does not
    warn, and does not deliver to the clean destinations. The outbound gate
    refuses and does not rewrite, and a destination name is the one string that
    is simultaneously outbound bytes, a record field, and a thing a sibling's
    watcher prints.

    SO THE LOAD-BEARING ASSERTION IS THE CLEAN DESTINATION'S ABSENCE. A tool
    that refused only the dirty destination and delivered to the other would
    satisfy the exit code, the record count and the echo check all three.
    """
    channel = make_channel(tmp_path, with_inbox=(DEST_A, DEST_DIRTY))
    env = base_env(tmp_path)
    note = clean_note(tmp_path)
    before = tree_snapshot(channel)

    control_code, control_out, control_err = run_send(
        "--note", str(note), "--to", DEST_A, "--allow-unmeasured", channel=channel, env=env
    )

    code, out, err = run_send(
        "--note",
        str(note),
        "--to",
        DEST_A,
        "--to",
        DEST_DIRTY,
        "--send",
        "--allow-unmeasured",
        channel=channel,
        env=env,
    )
    changed = changed_paths(before, tree_snapshot(channel))
    streams = text(out) + text(err)
    leaked = streams.count(SYNTHETIC_CREDENTIAL)
    entries = len(record_entries(env))

    assert control_code == EXIT_OK, f"the control was refused; stderr {text(control_err)!r}"
    assert "DRY RUN" in text(control_out), "the clean destination is not deliverable at all"
    assert code == EXIT_REFUSED, f"exit {code}; a refused destination name did not refuse the send"
    assert changed == [], f"a send carrying a refused destination name still wrote {changed}"
    assert leaked == 0, "the refusal echoed the value it refused"
    assert entries == 0, f"{entries} record entries; a refused send reached the record"


def test_all_refuses_the_whole_broadcast_when_a_discovered_name_is_dirty(tmp_path: Path) -> None:
    """Prove `--all` grades the names it DISCOVERED, not only the ones typed.

    THE DISCOVERED PATH IS THE ONE THAT MATTERS MOST AND THE ONE AN OPERATOR
    CANNOT INSPECT. `--to` at least passes through the operator's own keyboard;
    `--all` reads the sibling root and writes whatever it finds there into
    stdout and into the record. A repair that graded `args.to` alone would
    leave the whole of F1 open on the flag this project actually broadcasts
    with, and would look complete.

    THE CONTROL IS A SECOND, CLEAN CHANNEL AND A REAL `--all --send`, so a
    discovery that returned nothing at all - which would satisfy the refusal
    below perfectly - is ruled out by a broadcast that lands.
    """
    control_parent = tmp_path / "control958"
    control_parent.mkdir()
    control_channel = make_channel(control_parent, with_inbox=(DEST_A,))
    channel = make_channel(tmp_path, with_inbox=(DEST_A, DEST_DIRTY))
    env = base_env(tmp_path)
    note = clean_note(tmp_path)
    before = tree_snapshot(channel)

    control_code, _control_out, control_err = run_send(
        "--note",
        str(note),
        "--all",
        "--send",
        "--allow-unmeasured",
        channel=control_channel,
        env=env,
    )
    control_landed = delivered(control_channel, DEST_A).is_file()

    code, out, err = run_send(
        "--note", str(note), "--all", "--send", "--allow-unmeasured", channel=channel, env=env
    )
    changed = changed_paths(before, tree_snapshot(channel))
    streams = text(out) + text(err)
    leaked = streams.count(SYNTHETIC_CREDENTIAL)
    tagged = streams.count(CREDENTIAL_TAG)
    entries = len(record_entries(env))

    assert control_code == EXIT_OK, f"the control was refused; stderr {text(control_err)!r}"
    assert control_landed, "the control broadcast delivered nothing; discovery is not working"
    assert code == EXIT_REFUSED, f"exit {code}; a discovered dirty name did not refuse --all"
    assert changed == [], f"a refused broadcast still wrote {changed}"
    # ONE DIRTY NAME IS ONE REFUSAL. A second copy means the name was graded
    # twice - once as typed and once as resolved - which is what a discovered
    # destination looks like when the refused-index skip is bypassed for it. A
    # mutant doing exactly that survived every arm of the first cut.
    assert tagged == 1, f"one dirty discovered name was reported {tagged} time(s)"
    assert leaked == 0, "the refusal echoed the value it refused"
    assert entries == 1, f"{entries} record entries; only the control may have recorded one"


def test_a_resolved_name_is_graded_even_when_the_typed_name_is_clean(tmp_path: Path) -> None:
    """Prove the graded name is the one that gets PRINTED and RECORDED.

    THE NAME THE TOOL USES IS NOT THE NAME THE OPERATOR TYPED, which is S1's
    doing and is correct: a destination's name is RE-DERIVED from its resolved
    directory so the record can never file a delivery under a name no directory
    has. That re-derivation is exactly why grading `--to` as typed is not
    enough. A link inside the channel, at an ordinary name, resolving to a
    directory whose OWN name the gate refuses, is accepted by every containment
    check S1 added - its grandparent IS the channel root - and its resolved name
    then reaches stdout and the record.

    THE CONTROL IS THE SAME MECHANISM AT A CLEAN TARGET, in the same run: a
    second link, resolving to an ordinary destination, must deliver. Without it
    a tool that refused every link would pass this arm while breaking the
    containment behaviour S1 measured.
    """
    channel = make_channel(tmp_path, with_inbox=(DEST_A, DEST_DIRTY))
    make_directory_link(channel / ALIAS_TO_CLEAN, channel / DEST_A)
    make_directory_link(channel / ALIAS_TO_DIRTY, channel / DEST_DIRTY)
    env = base_env(tmp_path)
    note = clean_note(tmp_path)

    control_code, _control_out, control_err = run_send(
        "--note",
        str(note),
        "--to",
        ALIAS_TO_CLEAN,
        "--send",
        "--allow-unmeasured",
        channel=channel,
        env=env,
    )
    control_landed = delivered(channel, DEST_A).is_file()
    after_control = tree_snapshot(channel)

    code, out, err = run_send(
        "--note",
        str(note),
        "--to",
        ALIAS_TO_DIRTY,
        "--send",
        "--allow-unmeasured",
        channel=channel,
        env=env,
    )
    changed = changed_paths(after_control, tree_snapshot(channel))
    streams = text(out) + text(err)
    leaked = streams.count(SYNTHETIC_CREDENTIAL)
    recorded = sorted(record_strings(record_entries(env)))
    dirty_recorded = DEST_DIRTY in recorded

    assert control_code == EXIT_OK, f"the control was refused; stderr {text(control_err)!r}"
    assert control_landed, "a link at a clean destination did not deliver; the arm cannot grade"
    assert DEST_A in recorded, "the control's resolved name is not in the record"
    assert code == EXIT_REFUSED, f"exit {code}; a refused RESOLVED name did not refuse the send"
    assert changed == [], f"a send resolving to a refused name still wrote {changed}"
    assert leaked == 0, "the refusal echoed the value it refused"
    assert not dirty_recorded, "a refused destination name was written into the record"


def test_a_typed_name_that_never_resolves_is_graded_before_it_is_echoed(tmp_path: Path) -> None:
    """Prove the TYPED spelling is graded too, on the path where it is the thing printed.

    WRITTEN BECAUSE A MUTANT SURVIVED. Deleting the pre-loop grade of the typed
    list left the six arms above completely green, and the reason is worth
    keeping: in every one of them the typed name and the RESOLVED name are the
    same string, so the grade applied to the resolved list caught it and the
    earlier one was never load-bearing. A guard on a path no arm takes is a
    guard nobody has measured.

    THE PATH IT IS LOAD-BEARING ON IS A DESTINATION THAT NEVER BECOMES A
    TARGET. `destination <name> has no moon_sync_inbox directory` renders the
    operator's own typed spelling, and a name that fails there never reaches
    the resolved list at all - so with the earlier grade gone, the one refusal
    whose job is to say a destination is missing is the one that prints it.

    THE CONTROL IS THE SAME REFUSAL OVER A CLEAN NAME, and it is the sharpest
    kind available: that message MUST echo the clean name, which proves the arm
    can see a typed name on this exact code path rather than on some other one.
    """
    channel = make_channel(
        tmp_path, with_inbox=(DEST_A,), without_inbox=(DEST_NO_INBOX, DEST_DIRTY)
    )
    env = base_env(tmp_path)
    note = clean_note(tmp_path)
    before = tree_snapshot(channel)

    control_code, control_out, control_err = run_send(
        "--note", str(note), "--to", DEST_NO_INBOX, "--allow-unmeasured", channel=channel, env=env
    )
    control_streams = text(control_out) + text(control_err)

    code, out, err = run_send(
        "--note", str(note), "--to", DEST_DIRTY, "--allow-unmeasured", channel=channel, env=env
    )
    changed = changed_paths(before, tree_snapshot(channel))
    streams = text(out) + text(err)
    leaked = streams.count(SYNTHETIC_CREDENTIAL)

    assert control_code == EXIT_REFUSED, f"exit {control_code}; a name with no inbox was accepted"
    assert DEST_NO_INBOX in control_streams, (
        "the missing-inbox refusal does not print the typed name, so this arm sees nothing"
    )
    assert code == EXIT_REFUSED, f"exit {code}; a refused typed name did not refuse the send"
    assert leaked == 0, "the missing-inbox refusal echoed the value the gate refuses"
    assert changed == [], f"a refused dry run wrote {changed}"


def test_the_staged_filename_is_graded_and_not_only_the_delivered_one(
    tmp_path: Path,
) -> None:
    """Prove the name the WRITER creates is graded, not only the one it delivers.

    FOUND BY AN ADVERSARY AGAINST THE FIRST CUT OF THIS SLICE, and it inverts
    the slice's own claim. Every destination is staged through
    ``<note name>.tmp`` and only then renamed into place, so the first string
    to appear in a sibling's tree is not the graded one - it is four characters
    longer. That matters because a rule with a LENGTH FLOOR is satisfied by the
    suffix: the credential rules match a token run of twenty characters or
    more, and the suffix extends a run of nineteen past the floor.

    THE STAGED FILE REACHES THE SIBLING EITHER WAY. On the success path it sits
    in their tree between the write and the rename; on the commit-failure path
    CS-958 F4 leaves it there permanently and that sibling's own inbox watcher
    prints it as a loose file - measured by the adversary, end to end. A string
    this project's own gate refuses does not belong in another repository for
    any length of time.

    THE FIXTURE'S ASYMMETRY IS ASSERTED RATHER THAN ASSUMED, and without that
    the arm would be about nothing: a name that was dirty on its own would be
    refused by the delivered-name grade whether or not the staged name is
    graded at all. So both spellings are scanned through the tool's own
    ``grade_names`` first, and the arm requires the base to be CLEAN and the
    staged spelling to be REFUSED before its other assertions mean anything.
    """
    sender = load_sender()
    channel = make_channel(tmp_path, with_inbox=(DEST_A,))
    env = base_env(tmp_path)
    note = clean_note(tmp_path, name=STAGED_ONLY_NAME)
    base_problems = sender.grade_names([(PROBE_LABEL, STAGED_ONLY_NAME, "")])[0]
    staged_problems = sender.grade_names([(PROBE_LABEL, STAGED_ONLY_NAME + STAGING_SUFFIX, "")])[0]
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
    entries = len(record_entries(env))

    assert base_problems == [], (
        "the fixture's base name is refused on its own, so this arm would pass "
        "without the staged name being graded at all"
    )
    assert staged_problems != [], (
        "the fixture's staged name is not refused, so this arm grades nothing"
    )
    assert code == EXIT_REFUSED, f"exit {code}; stdout {text(out)!r} stderr {text(err)!r}"
    assert changed == [], f"a refused staged name still put {changed} in a sibling's tree"
    assert entries == 0, f"{entries} record entries; a refused send reached the record"


def test_a_warning_on_a_name_is_made_visible_and_does_not_refuse(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Prove the WARN tier survives the trip through the metadata door.

    THE GATE HAS THREE TIERS AND THE FIRST CUT OF THIS SLICE IMPLEMENTED TWO.
    `outbound_gate.scan` returns refusals, warnings and coverage; a warning is
    a short discovered value that is named and positioned on stdout while the
    send stays possible, because a gate that refuses routine prose is a gate
    that gets routed around. `grade_names` bound the warnings to a throwaway
    and dropped them, so the identical string that prints
    `WARN <pii:world-name>` as CONTENT went out silently as a destination NAME
    and into the record - measured end to end by an adversary. That is F1's own
    shape one tier down.

    SO THE PROPERTY IS TWO-SIDED AND BOTH SIDES ARE GRADED HERE: a warning must
    produce a VISIBLE notice, and it must NOT refuse. A repair that refused on
    warnings would satisfy the visibility half while breaking the tier; one
    that keeps dropping them satisfies the refusal half, which is what the
    first cut did.

    THE GATE IS STUBBED, AND ONLY THE GATE. The warn tier fires only on short
    save-derived values, and this suite deliberately runs with no derivable
    save root - so no arm here can reach it through the real gate, which is
    exactly why the gap went untested. What is under test is this module's own
    consumption rule: which of the three things `scan` returns reach which
    output. The gate's own warn tier is graded in tests/test_outbound_gate.py,
    where the save fixtures live.

    THE CONTROL IS THE SAME STUB CARRYING A REFUSAL, so a `grade_names` that
    returned nothing at all - which satisfies "does not refuse" completely -
    cannot pass.
    """
    sender = load_sender()
    finding = SimpleNamespace(klass="world-name", line=1, col=1)
    refusal = SimpleNamespace(klass="credential", line=1, col=1)

    def stub(refusals: object, warnings: object) -> object:
        return SimpleNamespace(
            CLASS_REASONS={"world-name": "a world name", "credential": "a credential shape"},
            scan=lambda _text: (refusals, warnings, []),
        )

    monkeypatch.setattr(sender, "load_outbound_gate", lambda: stub([], [finding]))
    warn_problems, warn_refused, warn_notices = sender.grade_names([(PROBE_LABEL, "orbz", "")])

    monkeypatch.setattr(sender, "load_outbound_gate", lambda: stub([refusal], []))
    refuse_problems, refuse_refused, refuse_notices = sender.grade_names(
        [(PROBE_LABEL, "orbz", "")]
    )

    assert refuse_problems != [], "the control produced no refusal; this arm cannot grade"
    assert refuse_refused == frozenset({1}), (
        f"a refusal did not mark its own entry refused: {sorted(refuse_refused)}"
    )
    assert warn_problems == [], f"a warning was consumed as a refusal: {warn_problems}"
    assert warn_refused == frozenset(), "a warning marked its entry refused"
    assert warn_notices != [], "a warning on a name produced no visible notice at all"
    assert refuse_notices == [], f"a refusal was also reported as a notice: {refuse_notices}"


def test_a_dirty_name_after_a_clean_one_is_attributed_to_its_own_position(
    tmp_path: Path,
) -> None:
    """Prove a batch grade attributes each finding to the name that produced it.

    WRITTEN BECAUSE A MUTANT SURVIVED ALL THIRTY-SIX ARMS. `grade_names` scans
    a whole batch in ONE pass and reads each finding's LINE back to decide
    which name it belongs to; pinning that line to 1 changed nothing any arm
    could see. The reason is a property of the fixtures rather than of the
    code: every arm that planted a dirty value had it at batch index 1, either
    because the batch held one entry or because the credential spelling sorts
    ahead of the ordinary destination names under `--all`.

    MIS-ATTRIBUTION IS TWO FAULTS AT ONCE AND BOTH ARE MEASURED HERE. The
    refusal names the WRONG destination, which is the D2 fault `_which` exists
    to prevent - an ordinal pointing at a name that was fine sends the operator
    to edit the wrong thing. And the dirty name is then absent from the refused
    set, so the loop walks it and the missing-inbox refusal renders it.
    Measured under the mutant: the value reached stderr once and the ordinal
    said destination 1.

    THE DIRTY DESTINATION DELIBERATELY HAS NO INBOX, because that is what makes
    the echoing line reachable. The one existing arm with a dirty name at
    position 2 gives it an inbox, so it never gets that far.

    THE CONTROL PUTS A CLEAN NAME IN THE SAME SLOT and requires the echo, which
    proves this arm can see a name at position 2 through this exact refusal.
    """
    channel = make_channel(
        tmp_path, with_inbox=(DEST_A,), without_inbox=(DEST_NO_INBOX, DEST_DIRTY)
    )
    env = base_env(tmp_path)
    note = clean_note(tmp_path)

    control_code, control_out, control_err = run_send(
        "--note",
        str(note),
        "--to",
        DEST_A,
        "--to",
        DEST_NO_INBOX,
        "--allow-unmeasured",
        channel=channel,
        env=env,
    )
    control_streams = text(control_out) + text(control_err)

    code, out, err = run_send(
        "--note",
        str(note),
        "--to",
        DEST_A,
        "--to",
        DEST_DIRTY,
        "--allow-unmeasured",
        channel=channel,
        env=env,
    )
    streams = text(out) + text(err)
    leaked = streams.count(SYNTHETIC_CREDENTIAL)
    blamed = [token for token in ("destination 1", "destination 2") if token in streams]

    assert control_code == EXIT_REFUSED, f"exit {control_code}; a name with no inbox was accepted"
    assert DEST_NO_INBOX in control_streams, (
        "the missing-inbox refusal does not print a name at position 2; the arm sees nothing"
    )
    assert code == EXIT_REFUSED, f"exit {code}; a refused name at position 2 did not refuse"
    assert leaked == 0, "the refused value reached the streams through the missing-inbox line"
    assert blamed == ["destination 2"], (
        f"the refusal blames {blamed}; the fault is at the second typed destination"
    )


def test_a_dirty_filename_refuses_rather_than_reporting_unmeasured(tmp_path: Path) -> None:
    """Prove a refused filename dominates an unmeasured class, without the flag.

    `gate_phase` claims this precedence in its own docstring - a finding first,
    then an unmeasured class, then clean, which is the gate's own ordering -
    and NO ARM MEASURED IT, because every other arm in this file passes
    `--allow-unmeasured` and never reaches the branch. A mutant that graded the
    filename only when the payload was measurable survived all thirty-six.

    THE DIFFERENCE IS WHAT THE OPERATOR IS TOLD AND WHAT THEY DO NEXT. Reported
    as UNMEASURED at exit 3, the remedy printed on stderr is to re-run with
    `--allow-unmeasured` - which would then send the note, because the coverage
    problem was never the reason. A credential in a filename must come back as
    a refusal at exit 1 and stay refused however that flag is set.

    THE CONTROL IS THE SAME RUN WITH A CLEAN FILENAME and it must come back
    UNMEASURED. Without it this arm cannot tell "the filename was refused" from
    "this machine derives every class anyway", and on a box with a save library
    present the second is what it would be measuring.
    """
    channel = make_channel(tmp_path, with_inbox=(DEST_A,))
    env = base_env(tmp_path)
    control_note = clean_note(tmp_path)
    dirty = clean_note(tmp_path, name=DIRTY_NOTE_NAME)

    control_code, _control_out, control_err = run_send(
        "--note", str(control_note), "--to", DEST_A, channel=channel, env=env
    )

    code, out, err = run_send("--note", str(dirty), "--to", DEST_A, channel=channel, env=env)
    streams = text(out) + text(err)
    leaked = streams.count(SYNTHETIC_CREDENTIAL)

    assert control_code == EXIT_UNMEASURED, (
        f"exit {control_code}; this machine derives every class, so the arm cannot tell a "
        f"refusal from a measurable box. stderr {text(control_err)!r}"
    )
    assert code == EXIT_REFUSED, (
        f"exit {code}; a refused filename was reported as a coverage problem, and the remedy "
        "printed for that is the flag that would have sent it"
    )
    assert leaked == 0, "the refusal echoed the value it refused"


def test_a_refusal_about_a_resolved_name_is_distinguishable_from_a_typed_one(
    tmp_path: Path,
) -> None:
    """Prove the operator can tell WHICH of the two names was the bad one.

    MEASURED BY AN ADVERSARY: the two refusals were byte identical. A typed
    destination the gate refuses and a clean typed destination that RESOLVES to
    a directory the gate refuses both came back as `destination 1 carries
    <pii:credential>`. In the second case the operator inspects the name they
    typed, finds nothing wrong with it, and has been told nothing about the
    link or the directory it points at.

    THAT IS THE D2 FAULT IN A NEW PLACE. `_which` exists because an ordinal
    pointing at the wrong thing is worse than no ordinal, and here the ordinal
    is right while the thing it names is not the thing that failed.

    THE TWO RUNS ARE THE ASSERTION. Both must refuse - so a tool that accepted
    either cannot pass - and their refusals must DIFFER. Neither may echo the
    value.
    """
    channel = make_channel(tmp_path, with_inbox=(DEST_A, DEST_DIRTY))
    make_directory_link(channel / ALIAS_TO_DIRTY, channel / DEST_DIRTY)
    env = base_env(tmp_path)
    note = clean_note(tmp_path)

    typed_code, typed_out, typed_err = run_send(
        "--note", str(note), "--to", DEST_DIRTY, "--allow-unmeasured", channel=channel, env=env
    )
    alias_code, alias_out, alias_err = run_send(
        "--note", str(note), "--to", ALIAS_TO_DIRTY, "--allow-unmeasured", channel=channel, env=env
    )
    typed_streams = text(typed_out) + text(typed_err)
    alias_streams = text(alias_out) + text(alias_err)
    leaked = typed_streams.count(SYNTHETIC_CREDENTIAL) + alias_streams.count(SYNTHETIC_CREDENTIAL)

    assert typed_code == EXIT_REFUSED, f"exit {typed_code}; a typed dirty name was accepted"
    assert alias_code == EXIT_REFUSED, f"exit {alias_code}; a dirty resolved name was accepted"
    assert leaked == 0, "a refusal echoed the value it refused"
    assert typed_streams != alias_streams, (
        "the two refusals are identical, so the operator is sent to inspect the name they "
        "typed when the fault is in what it resolves to"
    )
    assert RESOLVED_PHRASE in alias_streams, (
        "the refusal does not say the fault is in what the destination resolves to"
    )


def test_a_discovered_metadata_refusal_says_how_to_locate_the_destination(
    tmp_path: Path,
) -> None:
    """Prove an --all metadata refusal is locatable at all.

    `_which` returns TWO halves and the metadata call site used only the first.
    Under `--all` the first half is `a destination discovered by --all`, which
    names nothing: there is no typed list to count into, and the second half -
    re-run with `--to` and read the ordinal off your own list - is the only
    thing that turns the refusal into an action. Measured by an adversary: the
    hint was absent, so the operator is told a nameless destination on a
    channel of five is bad and given no way to find out which.

    NO ORDINAL IS THE OTHER HALF OF THE ASSERTION, because an ordinal into a
    sorted directory listing the operator has never seen would be worse than
    none - it is a number pointing into a list that exists only inside this
    tool.

    THE CONTROL IS THE TYPED FORM OF THE SAME FAULT, which must carry an
    ordinal and must NOT carry the hint. Without it, a tool that printed the
    hint on every refusal would pass.
    """
    channel = make_channel(tmp_path, with_inbox=(DEST_A, DEST_DIRTY))
    env = base_env(tmp_path)
    note = clean_note(tmp_path)

    control_code, control_out, control_err = run_send(
        "--note", str(note), "--to", DEST_DIRTY, "--allow-unmeasured", channel=channel, env=env
    )
    control_streams = text(control_out) + text(control_err)

    code, out, err = run_send(
        "--note", str(note), "--all", "--allow-unmeasured", channel=channel, env=env
    )
    streams = text(out) + text(err)
    ordinals = [token for token in ("destination 1", "destination 2") if token in streams]
    leaked = streams.count(SYNTHETIC_CREDENTIAL)

    assert control_code == EXIT_REFUSED, f"exit {control_code}; the typed control was accepted"
    assert "destination 1" in control_streams, "the typed refusal carries no ordinal"
    assert "--to" not in control_streams, "the typed refusal carries the discovered-only hint"
    assert code == EXIT_REFUSED, f"exit {code}; a discovered dirty name did not refuse --all"
    assert ordinals == [], f"a discovered destination was reported by ordinal: {ordinals}"
    assert "--to" in streams, "the refusal offers the operator no way to locate the destination"
    assert leaked == 0, "the refusal echoed the value it refused"


def test_a_collision_under_all_names_the_destination_that_holds_the_note(
    tmp_path: Path,
) -> None:
    """Prove a graded destination name is still USABLE in a refusal.

    THE FIRST CUT OF THIS SLICE OVERSHOT. It stopped rendering the destination
    in the two `already holds` refusals because at that point in the function
    the resolved name had not been graded yet. Under `--all` that leaves a
    refusal naming nobody: five siblings, one of them already holds the note,
    and the operator is told to re-run with `--to` and find out which. An
    adversary judged it a real loss rather than a trade, and the reasoning is
    sound - the suppressed string is the RESOLVED directory's own name, which
    this same function grades and which the tool prints unredacted on its own
    DELIVERED line. Suppressing it buys nothing for a name that passed the
    grade.

    SO THE ORDER IS THE FIX, NOT THE SILENCE: every resolved name is graded
    BEFORE any refusal renders one, and then the refusal may name it. This arm
    is the half that stops the silence from coming back; the arms above are the
    half that stops an ungraded name from being printed.

    THE CONTROL IS THE SAME RUN'S OTHER SIBLING, which is deliverable and must
    NOT be named - so a tool that dumped the whole channel into every refusal
    cannot pass.
    """
    channel = make_channel(tmp_path, with_inbox=(DEST_A, DEST_B))
    env = base_env(tmp_path)
    note = clean_note(tmp_path)
    delivered(channel, DEST_B).write_bytes(CLEAN_BODY.encode("ascii"))
    before = tree_snapshot(channel)

    code, out, err = run_send(
        "--note", str(note), "--all", "--send", "--allow-unmeasured", channel=channel, env=env
    )
    streams = text(out) + text(err)
    changed = changed_paths(before, tree_snapshot(channel))

    assert code == EXIT_REFUSED, f"exit {code}; a collision did not refuse the whole broadcast"
    assert changed == [], f"a refused broadcast still wrote {changed}"
    assert DEST_B in streams, (
        "the refusal names no destination, so an operator broadcasting to a channel of "
        "five is told a collision happened and not where"
    )
    assert DEST_A not in streams, (
        "a destination with no problem was named; the refusal is dumping the channel"
    )


def test_both_spellings_of_the_filename_reach_the_gate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Prove the DELIVERED filename is graded and not just the STAGED one.

    WRITTEN BECAUSE THE OBVIOUS MUTANT IS AN EQUIVALENT ONE. Deleting the
    delivered spelling from the batch leaves every other arm green, and no
    fixture can change that: the delivered name is a strict PREFIX of the
    staged name, and no rule in the gate's table is end-anchored - measured,
    the only anchored expressions in tools/precommit_gate.py are the save-file
    NAME parsers, not the scanners. Appending four characters can therefore
    create a match and never destroy one, so no VALUE exists that is refused as
    delivered and cleared as staged. Weakening the claim to "the staged name is
    graded" would be the wrong repair: the delivered name is the one that
    persists in a sibling's inbox and in the record, and staging is an
    implementation detail this tool is free to change.

    SO THE PROPERTY IS STRUCTURAL AND IS MEASURED STRUCTURALLY, with a
    RECORDING SPY over the gate rather than a value. The spy delegates to the
    real gate - the verdict is the real one - and records the text of every
    scan. One of those scans must be the metadata batch, and that batch must
    hold BOTH spellings, in order.

    THE PAYLOAD'S OWN SCAN IS THE POSITIVE CONTROL, in the same run: the spy
    must have seen it too, which proves the recorder is wired into the path
    under test rather than into nothing.
    """
    sender = load_sender()
    real = sender.load_outbound_gate()
    scanned: list[list[str]] = []

    def recording_scan(text: str) -> object:
        scanned.append(text.split("\n"))
        return real.scan(text)

    monkeypatch.setattr(
        sender,
        "load_outbound_gate",
        lambda: SimpleNamespace(
            scan=recording_scan,
            render=real.render,
            verdict=real.verdict,
            CLASS_REASONS=real.CLASS_REASONS,
        ),
    )

    _code, stop = sender.gate_phase(CLEAN_BODY.encode("ascii"), NOTE_NAME, allow_unmeasured=True)
    payload_seen = any(CLEAN_BODY.startswith(batch[0]) for batch in scanned if batch)
    metadata_batch = [NOTE_NAME, NOTE_NAME + STAGING_SUFFIX]

    assert stop is None, "a clean note was stopped; this arm never reached the metadata grade"
    assert payload_seen, "the spy never saw the payload scan, so it is not wired into the path"
    assert metadata_batch in scanned, (
        f"the gate was handed {scanned[1:]!r}; both spellings of the filename must be graded"
    )


def test_the_metadata_grade_reports_coverage_once(tmp_path: Path) -> None:
    """Prove the metadata grade consumes REFUSALS and not the gate's coverage rows.

    THE S2 SPEC'S FIRST DECISION, ASSERTED RATHER THAN LEFT TO A READING.
    Coverage is a property of the MACHINE - which classes could be derived here
    at all - and it is already accounted for by the payload's own grade. A
    metadata grade that folded coverage in again would report one machine's
    unmeasured class two or three times for a single note, and would let a
    filename turn a send UNMEASURED for a reason that has nothing to do with
    the filename.

    ONE HEADER IS BOTH HALVES OF THE ASSERTION: two would be the duplication,
    and zero would mean the arm is counting a string the tool no longer prints,
    so the count pins presence and non-duplication in one measurement.
    """
    channel = make_channel(tmp_path, with_inbox=(DEST_A, DEST_B))
    env = base_env(tmp_path)
    note = clean_note(tmp_path)

    code, out, err = run_send(
        "--note", str(note), "--all", "--send", "--allow-unmeasured", channel=channel, env=env
    )
    headers = text(out).count(COVERAGE_HEADER)

    assert code == EXIT_OK, f"exit {code}; stdout {text(out)!r} stderr {text(err)!r}"
    assert headers == 1, f"the gate's coverage block was reported {headers} time(s) for one note"


# --------------------------------------------------------------------------
# THE COMMIT PHASE AND THE EXIT-CODE CONTRACT. 39-43 - CS-958 F4, F5, F6 and
# F8. Everything above is about what must not LEAVE; this section is about what
# happens after the decision to send has been taken correctly. Three of the
# four findings here are the record telling a CS-951 reconciler something
# false, which is worse for that item than no record at all, and the fourth
# hands the operator's own live record to a wrapper that meant to redirect it.
# --------------------------------------------------------------------------


def test_an_empty_record_override_is_refused_rather_than_selecting_the_real_record(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Prove an override that is SET but empty does not silently mean the real record.

    CS-958 F8. `record_path` tested the override for TRUTH, so
    ``CLOCKSPEED_OUTBOUND_RECORD=""`` fell through to the operator's LIVE
    record at `tools/outbound_send.py::DEFAULT_RECORD`. A wrapper
    or an arm that CLEARS the variable rather than unsetting it therefore
    writes the very file it was trying to redirect away from, and session 75
    had that accident once already.

    REFUSING BEATS EITHER ALTERNATIVE. Falling back to the real record is the
    bug. Treating the empty string as a relative path would write
    ``.`` -relative litter into whatever directory the tool was launched from,
    which is no better and harder to notice. An empty value is a caller
    mistake, and this tool fails closed on caller mistakes.

    TWO CONTROLS IN THE SAME RUN, because the assertion is that ONE input is
    special: unset must still give the default, and a real value must still be
    honoured. Without them, a `record_path` that raised unconditionally would
    pass.
    """
    sender = load_sender()
    chosen = tmp_path / RECORD_NAME

    monkeypatch.delenv(ENV_RECORD, raising=False)
    default = sender.record_path()

    monkeypatch.setenv(ENV_RECORD, str(chosen))
    honoured = sender.record_path()

    monkeypatch.setenv(ENV_RECORD, "")
    with pytest.raises(ValueError, match="empty"):
        sender.record_path()

    assert default == sender.DEFAULT_RECORD, "an unset override no longer gives the default"
    assert honoured == chosen, "a real override was not honoured"


def test_an_unwritable_record_refuses_before_anything_is_delivered(tmp_path: Path) -> None:
    """Prove the record is proven writable BEFORE a byte reaches a sibling.

    CS-958 F6. With the record path unwritable both notes were DELIVERED and
    the tool exited 1 through the refusal path, whose own words are "nothing
    was sent". Channel, record and exit code disagreed on one run, and exit 1
    is documented as the code a caller may branch on to mean nothing left this
    machine.

    THE REPAIR IS ORDER, NOT WORDING. The record is prepared and proven
    writable while nothing has been delivered, so the refusal is TRUE when it
    says nothing was sent. That also converts the worst case from "a delivery
    nobody can reconcile" into "a send that did not happen", which is the
    direction this tool is supposed to fail in.

    THE CONTROL DELIVERS THE SAME NOTE TO THE SAME DESTINATION with a writable
    record, in the same run, so the refusal below is attributable to the record
    and not to anything about the channel.
    """
    channel = make_channel(tmp_path, with_inbox=(DEST_A,))
    env = base_env(tmp_path)
    note = clean_note(tmp_path)
    second = clean_note(tmp_path, name=SECOND_NOTE_NAME)

    control_code, _control_out, control_err = run_send(
        "--note",
        str(note),
        "--to",
        DEST_A,
        "--send",
        "--allow-unmeasured",
        channel=channel,
        env=env,
    )
    after_control = tree_snapshot(channel)

    blocker = tmp_path / "blocked958"
    blocker.write_bytes(b"not a directory\n")
    blocked = dict(env)
    blocked[ENV_RECORD] = str(blocker / RECORD_NAME)

    code, out, err = run_send(
        "--note",
        str(second),
        "--to",
        DEST_A,
        "--send",
        "--allow-unmeasured",
        channel=channel,
        env=blocked,
    )
    changed = changed_paths(after_control, tree_snapshot(channel))

    assert control_code == EXIT_OK, f"the control was refused; stderr {text(control_err)!r}"
    assert delivered(channel, DEST_A).is_file(), "the control delivered nothing"
    assert code == EXIT_REFUSED, f"exit {code}; stdout {text(out)!r} stderr {text(err)!r}"
    assert changed == [], (
        f"the send was refused for an unwritable record and still delivered {changed}"
    )


def test_the_commit_phase_removes_the_staging_files_it_never_renamed(tmp_path: Path) -> None:
    """Prove a failed commit leaves no payload behind in a sibling's tree.

    CS-958 F4. `commit_all` returned on the first failure and nothing ever
    unlinked the staging files of the destinations it had not reached.
    Measured: a three-destination send reported DELIVERED to 1 of 3, exit 1,
    and left ``<sibling>/moon_sync_inbox/<note>.md.tmp`` BYTE-IDENTICAL to the
    note. `tools/inbox_watch.py` reads it as a loose file, so the sibling holds
    the whole payload while this project's record says the delivery never
    happened - the CS-951 hole this module exists to close, in the shape that
    is hardest to notice. It is also PERMANENT: the staging-name validation
    then refuses every future send to that destination, even as a dry run, and
    the remedy is hand-deleting a file inside another repository.

    GRADED AT THE FUNCTION rather than end to end, because the failure has to
    be deterministic and a real commit failure is a race. Removing one
    destination's staged file makes its rename raise for certain, which is the
    same fault the measurement above produced by other means.

    THE FIRST DESTINATION IS THE CONTROL and must land: a `commit_all` that
    delivered nothing at all would satisfy every cleanup assertion here.
    """
    sender = load_sender()
    channel = make_channel(tmp_path, with_inbox=(DEST_A, DEST_B, DEST_C))
    payload = CLEAN_BODY.encode("ascii")
    targets = [(name, delivered(channel, name)) for name in (DEST_A, DEST_B, DEST_C)]

    staged, stage_error = sender.stage_all(payload, targets)
    sender.staging_name(targets[1][1]).unlink()
    landed, commit_error = sender.commit_all(targets)
    litter = sorted(name for name, target in targets if sender.staging_name(target).exists())

    assert stage_error == "", f"the staging phase failed: {stage_error}"
    assert len(staged) == 3, f"{len(staged)} destinations staged; the arm needs three"  # noqa: PLR2004
    assert landed == [DEST_A], f"the control did not land: {landed}"
    assert commit_error != "", "a commit that could not rename reported no error"
    assert litter == [], f"the commit phase left the payload behind at {litter}"


def test_the_commit_phase_never_overwrites_a_note_that_appeared_after_validation(
    tmp_path: Path,
) -> None:
    """Prove a sibling's own note survives a send that races it.

    CS-958 F5. `resolve_targets` checks ``target.exists()`` and `commit_all`
    called ``.replace()``, which OVERWRITES. A note written into the window
    between the two was destroyed, and the run reported SEND_EXIT=0,
    ``DELIVERED ... [gate CLEAN]`` and an ordinary record entry - so the tool
    destroyed another repository's note and recorded the event as a clean
    success. Won at the tightest two-destination window over ten attempts, so
    it is not an artifact of a wide race.

    THE FIX IS A RENAME THAT CANNOT CLOBBER, not a second existence check: two
    checks with a rename between them is the same race with a smaller window.
    The victim is planted deterministically here rather than raced, because
    what must be graded is the CONSEQUENCE - the bytes at the target - and a
    race that is merely hard to win would make this arm flaky rather than
    strict.

    THE FIRST DESTINATION IS THE CONTROL and must land, so a commit phase that
    refused everything cannot pass.
    """
    sender = load_sender()
    channel = make_channel(tmp_path, with_inbox=(DEST_A, DEST_B))
    payload = CLEAN_BODY.encode("ascii")
    victim_bytes = (CLEAN_BODY + "A sibling wrote this first.\n").encode("ascii")
    targets = [(name, delivered(channel, name)) for name in (DEST_A, DEST_B)]

    _staged, stage_error = sender.stage_all(payload, targets)
    targets[1][1].write_bytes(victim_bytes)
    landed, commit_error = sender.commit_all(targets)
    survivor = targets[1][1].read_bytes()
    litter = sorted(name for name, target in targets if sender.staging_name(target).exists())

    assert stage_error == "", f"the staging phase failed: {stage_error}"
    assert landed == [DEST_A], f"the control did not land: {landed}"
    assert survivor == victim_bytes, "the commit phase destroyed a note it did not write"
    assert commit_error != "", "overwriting was avoided but the caller was not told"
    assert litter == [], f"the commit phase left the payload behind at {litter}"


def test_a_partial_delivery_reports_incomplete_rather_than_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Prove exit 1 keeps meaning that nothing was written.

    CS-958 F6, the half that is a CONTRACT rather than an ordering. The module
    publishes its codes as a closed set a caller can branch on, and calls 1
    "refused ... Fail closed". Two paths returned 1 having delivered: a partial
    commit, and a complete delivery whose record could not be written. A caller
    that branches on 1 to mean "nothing left this machine" is wrong on both,
    and that caller is the CS-951 reconciler this record exists for.

    SO THE INCOMPLETE CASE GETS ITS OWN CODE and 1 goes back to being true. The
    set stays closed and stays branchable: 0 delivered and recorded, 1 nothing
    written, 2 usage, 3 unmeasured, 4 something was delivered and the run did
    not complete cleanly - read stderr and the record.

    THE FAILURE IS FORCED WITH A DIRECTORY AT THE SECOND TARGET, which no
    rename can replace on either platform. `perform_send` is called directly
    because `resolve_targets` would refuse that destination long before the
    commit phase - which is correct, and is why this arm has to reach past it
    to grade the phase underneath.

    THE CONTROL IS A CLEAN CALL IN THE SAME RUN returning EXIT_OK, so a
    `perform_send` that reported every send incomplete cannot pass.
    """
    sender = load_sender()
    channel = make_channel(tmp_path, with_inbox=(DEST_A, DEST_B))
    monkeypatch.setenv(ENV_RECORD, str(tmp_path / RECORD_NAME))
    payload = CLEAN_BODY.encode("ascii")

    control = sender.perform_send(
        payload,
        SECOND_NOTE_NAME,
        [(DEST_A, delivered(channel, DEST_A, SECOND_NOTE_NAME))],
        "CLEAN",
        [],
    )

    delivered(channel, DEST_B).mkdir()
    targets = [(name, delivered(channel, name)) for name in (DEST_A, DEST_B)]
    code = sender.perform_send(payload, NOTE_NAME, targets, "CLEAN", [])
    entries = record_entries({ENV_RECORD: str(tmp_path / RECORD_NAME)})
    names = sorted(record_strings(entries))

    assert control == EXIT_OK, f"the control returned {control}; a clean send must be 0"
    assert code == EXIT_INCOMPLETE, (
        f"a partial delivery returned {code}; 1 is documented as nothing having been written"
    )
    assert delivered(channel, DEST_A).is_file(), "the deliverable destination did not land"
    assert names.count(DEST_A) == 2, (  # noqa: PLR2004
        f"the record does not hold both deliveries to the destination that landed: {names}"
    )
    assert DEST_B not in names, "a destination that never landed was recorded"


def test_a_delivery_whose_record_cannot_be_written_is_incomplete_not_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Prove the second path that returned 1 having delivered now returns 4.

    CS-958 F6 as it was originally measured: with the record path unwritable,
    both notes were DELIVERED and the tool exited 1. `prepare_record` now makes
    that almost unreachable by proving the record before anything is staged,
    and ALMOST is the reason this arm exists - the record can still fail
    between the probe and the write, and a branch nothing exercises is a branch
    this project has repeatedly found broken.

    THE WRITE IS MADE TO FAIL BY STUBBING `append_record`, which is a
    COLLABORATOR of the function under test and not the function itself. What
    is graded is `perform_send`'s answer when the record refuses it: the note
    is in the sibling's inbox, so the run is INCOMPLETE and not REFUSED, and
    the operator is told to record it by hand.

    THE CONTROL IS THE SAME CALL WITHOUT THE STUB, returning EXIT_OK, so a
    `perform_send` that reported everything incomplete cannot pass.
    """
    sender = load_sender()
    channel = make_channel(tmp_path, with_inbox=(DEST_A,))
    monkeypatch.setenv(ENV_RECORD, str(tmp_path / RECORD_NAME))
    payload = CLEAN_BODY.encode("ascii")

    control = sender.perform_send(
        payload,
        SECOND_NOTE_NAME,
        [(DEST_A, delivered(channel, DEST_A, SECOND_NOTE_NAME))],
        "CLEAN",
        [],
    )

    def raising_append(_path: Path, _entries: object) -> None:
        message = "the record is not writable"
        raise OSError(message)

    monkeypatch.setattr(sender, "append_record", raising_append)
    code = sender.perform_send(
        payload, NOTE_NAME, [(DEST_A, delivered(channel, DEST_A))], "CLEAN", []
    )

    assert control == EXIT_OK, f"the control returned {control}; a clean send must be 0"
    assert code == EXIT_INCOMPLETE, (
        f"a delivered note whose record failed returned {code}; 1 means nothing was written"
    )
    assert delivered(channel, DEST_A).is_file(), (
        "the note was not delivered; the arm grades nothing"
    )


def test_a_record_path_that_is_a_directory_refuses_before_delivering(tmp_path: Path) -> None:
    """Prove the record probe covers what `append_record` actually has to do.

    A directory AT the record path passes every check that only asks about the
    PARENT: the parent exists, it is writable, and a staging file can be made
    beside it. `append_record` then stages happily and fails at the replace -
    after the notes are in siblings' inboxes, which is the CS-958 F6 shape all
    over again. So the probe asks the question the writer will ask.

    DETERMINISTIC ON BOTH PLATFORMS, which is why this case is graded here
    rather than only through a permission-denied directory: neither Windows nor
    POSIX will let a file replace a directory.

    THE CONTROL DELIVERS THE SAME NOTE with an ordinary record path, in the
    same run, so the refusal is attributable to the record and not the channel.
    """
    channel = make_channel(tmp_path, with_inbox=(DEST_A,))
    env = base_env(tmp_path)
    note = clean_note(tmp_path)
    second = clean_note(tmp_path, name=SECOND_NOTE_NAME)

    control_code, _control_out, control_err = run_send(
        "--note",
        str(note),
        "--to",
        DEST_A,
        "--send",
        "--allow-unmeasured",
        channel=channel,
        env=env,
    )
    after_control = tree_snapshot(channel)

    blocked = dict(env)
    blocked[ENV_RECORD] = str(tmp_path / "recorddir958" / RECORD_NAME)
    Path(blocked[ENV_RECORD]).mkdir(parents=True)

    code, out, err = run_send(
        "--note",
        str(second),
        "--to",
        DEST_A,
        "--send",
        "--allow-unmeasured",
        channel=channel,
        env=blocked,
    )
    changed = changed_paths(after_control, tree_snapshot(channel))

    assert control_code == EXIT_OK, f"the control was refused; stderr {text(control_err)!r}"
    assert code == EXIT_REFUSED, f"exit {code}; stdout {text(out)!r} stderr {text(err)!r}"
    assert changed == [], f"a send refused for its record still delivered {changed}"


def test_a_record_directory_that_cannot_be_written_refuses_before_delivering(
    tmp_path: Path,
) -> None:
    """Prove the write probe itself bites, on a platform that honours the mode.

    THE PROBE EXISTS FOR THE CASE NO STRUCTURAL CHECK CAN SEE: a record
    directory that is present, and is a directory, and still will not accept a
    file. That is a locked-down box or a read-only mount, and it is the one
    remaining way the CS-958 F6 measurement could recur.

    THE SKIP IS GUARDED BY A POSITIVE CONTROL AND IS NOT A SILENT ONE. Windows
    does not honour a chmod on a directory, so the arm first proves the mode
    took by trying to create a file itself; if that succeeds, the platform did
    not restrict anything and a green result here would be a statement about
    nothing. CI runs this module on ubuntu, where the mode is honoured and the
    probe is measured. This project has already been bitten by a gate that
    skipped its checks and still reported PASS, so the reason is spelled out
    rather than left to a bare marker.
    """
    channel = make_channel(tmp_path, with_inbox=(DEST_A,))
    env = base_env(tmp_path)
    note = clean_note(tmp_path)
    locked = tmp_path / "lockedrecord958"
    locked.mkdir()
    locked.chmod(0o500)
    try:
        try:
            (locked / "control958.txt").write_bytes(b"")
            honoured = False
        except OSError:
            honoured = True
        if not honoured:
            pytest.skip(
                "this platform did not honour a chmod on a directory it had just created, "
                "so an unwritable record directory cannot be built here and a green result "
                "would be a statement about nothing. The probe is UNMEASURED on this "
                "platform, not absent - CI runs this module on ubuntu, where it is measured"
            )

        blocked = dict(env)
        blocked[ENV_RECORD] = str(locked / RECORD_NAME)
        before = tree_snapshot(channel)
        code, out, err = run_send(
            "--note",
            str(note),
            "--to",
            DEST_A,
            "--send",
            "--allow-unmeasured",
            channel=channel,
            env=blocked,
        )
        changed = changed_paths(before, tree_snapshot(channel))
    finally:
        locked.chmod(0o700)

    assert code == EXIT_REFUSED, f"exit {code}; stdout {text(out)!r} stderr {text(err)!r}"
    assert changed == [], f"a send refused for an unwritable record still delivered {changed}"


def test_a_dry_run_does_not_touch_the_record_or_the_filesystem(tmp_path: Path) -> None:
    """Prove `--send` is still the only way this tool writes a byte.

    FOUND BY A VERIFIER AGAINST THE FIRST CUT OF THE COMMIT-PHASE SLICE. The
    record probe was placed above the dry-run branch, so a dry run created the
    record's parent directory and a temporary file inside it while printing
    "nothing was written. Pass --send to deliver." - measured, on a directory
    that did not exist before the run. The module's own first rule is that
    `--send` is the only way a byte is written, and a probe is a byte.

    IT ALSO REFUSED A DRY RUN OUTRIGHT for a record fault that has no bearing
    on what a dry run does, which turns the one safe way to inspect a send into
    something that can fail for an unrelated reason.

    THE ABSENCE OF THE DIRECTORY IS THE ASSERTION, not the exit code: a tool
    that returned 0 and still created it would satisfy an exit-code check
    completely. The record path points inside a directory that does not exist,
    so any touch at all is visible.

    THE CONTROL IS THE SAME RECORD PATH USED BY A REAL SEND in the same run,
    which MUST create the directory - otherwise this arm would pass against a
    tool that had simply stopped recording anything.
    """
    channel = make_channel(tmp_path, with_inbox=(DEST_A,))
    env = base_env(tmp_path)
    note = clean_note(tmp_path)
    unborn = tmp_path / "recordparent958"
    env[ENV_RECORD] = str(unborn / RECORD_NAME)

    code, out, err = run_send(
        "--note", str(note), "--to", DEST_A, "--allow-unmeasured", channel=channel, env=env
    )
    touched_by_dry_run = unborn.exists()

    sent_code, _sent_out, sent_err = run_send(
        "--note",
        str(note),
        "--to",
        DEST_A,
        "--send",
        "--allow-unmeasured",
        channel=channel,
        env=env,
    )

    assert code == EXIT_OK, f"exit {code}; a dry run was refused. stderr {text(err)!r}"
    assert "DRY RUN" in text(out), "the dry run did not reach its report"
    assert not touched_by_dry_run, "the dry run created the record's parent directory"
    assert sent_code == EXIT_OK, f"the control send exited {sent_code}; {text(sent_err)!r}"
    assert unborn.is_dir(), "the control send did not create the record directory either"


def test_a_raise_after_a_delivery_is_incomplete_and_not_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Prove exit 1 keeps meaning nothing was written, even when the tool raises.

    FOUND BY A VERIFIER, and the artifact was already carrying the proof it was
    wrong: `main`'s handler printed `REFUSED` and `NOTE ALREADY DELIVERED` on
    the same run. An exception this module does not name - a `RuntimeError` out
    of the record writer, which `perform_send` catches only `OSError` and
    `ValueError` from - escapes to the outer handler, which reported a refusal
    over a note sitting in a sibling's inbox. That is the exact lie the fourth
    exit code was added to stop telling, told through the one path the fourth
    code did not cover.

    THE STUB RAISES A CLASS THE CODE DOES NOT HANDLE, which is the point: an
    `OSError` would be caught by `perform_send` and would already answer 4. The
    branch under test is the one for a failure nobody anticipated, and "nobody
    anticipated it" is exactly when a false "nothing was sent" is most likely to
    be believed.

    THE CONTROL IS A RAISE WITH NOTHING DELIVERED, in the same run, which must
    still be REFUSED - so a handler that answered 4 unconditionally, and thereby
    told the opposite lie, cannot pass.
    """
    sender = load_sender()
    channel = make_channel(tmp_path, with_inbox=(DEST_A,))
    monkeypatch.setenv(ENV_RECORD, str(tmp_path / RECORD_NAME))
    note = clean_note(tmp_path)
    argv = [
        "--note",
        str(note),
        "--to",
        DEST_A,
        "--send",
        "--allow-unmeasured",
        "--channel-root",
        str(channel),
    ]

    def raising_append(_path: Path, _entries: object) -> None:
        message = "a class this module does not name"
        raise RuntimeError(message)

    def raising_stage(_payload: bytes, _targets: object) -> tuple[list[Path], str]:
        message = "a class this module does not name"
        raise RuntimeError(message)

    monkeypatch.setattr(sender, "append_record", raising_append)
    code = sender.main(argv)
    landed = delivered(channel, DEST_A).is_file()

    monkeypatch.setattr(sender, "stage_all", raising_stage)
    control = sender.main([*argv[:2], "--to", DEST_B, *argv[4:]])

    assert landed, "the note was not delivered; this arm grades nothing"
    assert code == EXIT_INCOMPLETE, (
        f"a raise over a delivered note returned {code}; 1 means nothing was written"
    )
    assert control == EXIT_REFUSED, (
        f"a raise before anything was delivered returned {control}; that run wrote nothing"
    )
