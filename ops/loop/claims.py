#!/usr/bin/env python
"""Row claims - a `ROADMAP.md` row in flight is held, so no other lane takes it.

THE DEFECT THIS CLOSES. `tools/headless-queue.md` section 5 defines the queue as
`ROADMAP.md` read top to bottom with the first surviving row taken, and its
FENCE 6 rules that a row is done only when its id carries a closure record in
`docs/LEDGER.md`. That record is written at the END of a cycle, and a cycle runs
for a long time - the two real nights measured so far both ran into the
thousands of seconds. For that whole span the row in flight was indistinguishable
from an untaken one by anything on disk. While the roster held a single lane that
was latent; ``ops/loop/lanes.py`` widening the roster made it reachable, because
two lanes now poll one file. Nothing claimed a row, so both would take the same
one, and the second lane's whole cycle would be work already being done.

A CLOSURE RECORD AND A CLAIM ANSWER DIFFERENT QUESTIONS, and keeping them
separate is the point rather than an inconvenience. The ledger answers "is this
row FINISHED", durably and for every future session. A claim answers "is somebody
WORKING this row RIGHT NOW", and it is worthless the moment its holder stops
running. Folding either into the other loses one of the answers: a claim written
into the ledger would need unwriting on every crash, and a fence that read only
the ledger is the fence that was already there and that this module exists
because of.

DERIVED FROM ``ops/loop/lanes.py``, AND DELIBERATELY SO. That module already
answered three things this one needs, each of them paid for:

  * IT PROBES THE HOLDER'S PID, NEVER THE FILE'S EXISTENCE. A record whose
    holder is dead has the same name, the same shape and a plausible timestamp
    as a live one, so existence is not evidence. A wedged claim is as bad as no
    claim and worse, because it looks like progress.
  * READS DO NOT WRITE. Clearing a stale record inside a read would make a
    rendering pass mutate the control plane, and two pollers would race each
    other into a reclaim. Clearing happens only inside :func:`try_claim_row`.
  * IT REFUSES RATHER THAN QUEUES. A second lane asking for a held row gets a
    refusal that touches nothing on disk, not a wait.

So the probe, the path normalisation, the exclusive create, the payload read and
the worktree guard are IMPORTED from that module rather than rewritten here. A
second copy of any of them is a second place for the answer to go subtly wrong.

THE KEY IS THE ROW ID, WHICH IS WHAT THE ROW IS. It is not the row's position in
the queue, not its line number in `ROADMAP.md`, and not an index into whatever
list a lane happened to be offered. Every one of those is order-dependent, and
the queue REORDERS CONSTANTLY - a row closes, a row is inserted, a lane runs
under a scope that offers a subset. A record keyed by any of them would re-point
the moment the file above it changed, and a live holder would then read FREE
while a second lane walked into its worktree. ``ops/loop/lanes.py`` measured that
failure on its own slot index and carries a whole paragraph on it; this module
declines to reproduce it. A row id is permanent and never reused
(`CLAUDE.md` section 5), which is exactly the property a key needs.

AND THE FILE NAME IS NOT THE KEY EITHER, for the same reason one layer down. The
name is DERIVED from the row id and is merely where a NEW claim is written;
:func:`claim_for_row` makes the RECORDED row authoritative, so a record that
ended up under some other name is still found and still holds its row. That is
the structural half of the ruling, and it is what makes the derivation
survivable if it ever changes.

NOTHING HERE READS `ROADMAP.md`. The caller brings the queue it computed - from
``ops/loop/scope.py``, or by hand - and this module filters it. Deciding WHAT is
on the queue and deciding WHO is holding a row are separate jobs, and a claim
store that parsed the roadmap would have to agree with the scope module about
the fences as well, which is a second copy of a different answer.

LIVENESS IS THE CYCLE'S, NEVER THE CLAIMING PROCESS'S - CS-1009. The first
build of this module probed the pid that WROTE the record, which is correct
only if the writer runs for as long as the work does. The worker does not run
that way. `tools/headless-queue.md` hands the queue to an LLM agent that
reaches python through a FRESH SUBPROCESS PER CALL, so the process that takes
the claim has exited microseconds later while its cycle runs for thousands of
seconds - both measured nights did. Under the pid anchor the record read
RECLAIMABLE for that whole span and a second lane reclaimed a row somebody was
working: the exact double-booking this module exists to stop, restored by the
CALLING CONVENTION rather than by the code, and invisible to every arm that
claims from a process which stays alive.

THE ANCHOR IS THE LANE LOCK, because it is the one thing already on disk that
outlives a per-call subprocess and is not a duration. ``ops/loop/lanes.py``
holds one lock per lane; ``ops/loop/lane_launcher.py`` re-points it at the
SPAWNED WORKER through ``lanes.repoint_lane_pid`` as soon as it has a pid, and
that process lives the whole cycle. ``lanes.lane_state`` already answers FREE,
RUNNING or RECLAIMABLE over it with the pid-reuse guard paid for. So a claim
DELEGATES: :func:`_lane_anchor_state` asks the lock of the lane the record
itself names, and the row is held exactly while that lane's cycle runs.

MATCHED ON THE LOCK'S RUN ID, or a lane would be the anchor rather than a
cycle. A lane is re-occupied within seconds of a cycle ending, so without the
run id every abandoned record would read held for as long as the loop kept
firing - a wedged row wearing the clothes of a live one, which the module
docstring above already rules is worse than no claim at all.

AND THE RUN ID IS READ OFF THE LOCK, NOT TAKEN FROM THE CALLER. This is the
half that would be easy to get wrong and would fail silently in production.
The caller's ``run_id`` is the WORKER'S OWN, invented inside the cycle;
``launch_lane`` never hands the worker the driver's run id, by environment or
by argument. Comparing the caller's run id against the lock's would therefore
mismatch on every real fire and answer RECLAIMABLE for every claim - the defect
this closes, restored with more machinery. So :func:`try_claim_row` READS the
lane's lock and snapshots the run id it finds into ``lane_run_id``. A caller
cannot assert its own liveness; all it supplies is which lane it is on.

NO FLOOR OVER A CLAIM'S AGE ANYWHERE ON THIS PATH, and that is a ruling rather
than an omission - CS-1009 forbids the CS-988 shape by name. An age floor picks
a number that is too small for a long cycle and too large for a crashed one at
the same time, and it is satisfied by the strongest member of whatever
population it was tuned against. The lock is a probe, not a timer. The one
duration this file reads is ``WRITE_GRACE_S``, which is the exclusive create's
fill window and applies to a record with NO readable holder at all.

A RUNNING LOCK THAT CANNOT PROVE ITS HOLDER ANCHORS ITS ROW ANYWAY, AND THAT IS
INHERITED DELIBERATELY RATHER THAN OVERLOOKED. ``lanes.holder_is_a_stranger``
FAILS OPEN: with either half of the holder's identity unreadable it answers "not
a stranger" and the lane reads RUNNING. A build of this module gated the anchor
on that provability and was REFUTED by adjudication, because the gate inverted
the trade ``lanes.py`` had already ruled - freeing a lane on a guess
double-books a running worker, which is strictly worse than the wedge. A ROW IS
A SMALLER UNIT THAN A LANE, so the ranking cannot flip on the way up: if a guess
may not free a lane it may not free one of that lane's rows. The gate also
re-derived that same predicate from the same two payload fields, which is the
second copy this docstring forbids, and it made
``lanes.lane_state`` say RUNNING while ``claims.claim_state`` said RECLAIMABLE
about one lock at one instant.

WHAT THAT COSTS AND WHY IT IS RECOVERABLE. The row wedges only ALONGSIDE A
WEDGED LANE - the same lock also refuses ``try_acquire_lane``, so the lane is
discovered dead by the driver rather than quietly skipped, and it takes three
things at once (a driver that died without releasing, AND a reissued pid, AND an
unreadable start time). The escape is to clear the stale LANE LOCK under the
main checkout's lock root, which an operator has to do for the lane in any case;
the row is then reclaimed on the next fire. `docs/OPERATIONS.md` carries the
procedure. THE CLAIM RECORD ITSELF IS NEVER HAND-DELETED - deleting one puts a
second lane into a worktree that already has one. Because it is a state nobody
should have to deduce, :data:`ANCHOR_LANE_UNPROVEN` is a DECLARED anchor value
and every reading carries it.

THE LIMIT, STATED RATHER THAN IMPLIED: A CLAIM WITH NO LANE LOCK IS ANCHORED ON
ITS PROCESS. A hand-run worker, an arm in a test, an operator at a REPL - none
of them hold a lane lock, and a claim that read dead the instant it was made
would be a new defect traded for the old one. So where the lane is FREE or
RECLAIMABLE at claim time the record carries no ``lane_run_id`` and the pid
probe decides it, exactly as before. That is CS-1009's own failure in
miniature, confined to callers the queue never launches, and it is DECLARED in
the record as ``anchor`` and rendered by every reader, so a dashboard or an
operator can tell a cycle-anchored claim from a process-anchored one by reading
it rather than by inferring it.
"""

from __future__ import annotations

import contextlib
import json
import os
import time
import uuid
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Any, Final

from ops.loop import lanes

#: One record as every reader here handles it: where it sits, the exact bytes it
#: was graded from, its payload, and the state that grading produced. THE BYTES
#: TRAVEL WITH THE GRADE so a reclaim can prove it is removing the record it
#: graded rather than whatever later took that path.
_Candidate = tuple[Path, bytes, dict[str, Any], str]

#: ROOTED AT THE MAIN CHECKOUT, NEVER AT THIS FILE, and that distinction is the
#: whole of this comment because getting it wrong makes the store a no-op.
#:
#: A CLAIM IS TAKEN WORKER-SIDE. Each lane's worker runs INSIDE ITS OWN CHECKOUT
#: - ``ops/loop/lane_launcher.py`` hands it a per-lane worktree and the runner
#: sets its cwd there - so a lane importing this module imports ITS OWN COPY of
#: it. A root derived from ``__file__`` is therefore a DIFFERENT DIRECTORY IN
#: EVERY LANE, the two stores never meet, and every lane reads every row FREE
#: while another holds it. That was measured across two real processes in two
#: checkouts, both holding one row at once.
#:
#: ``lanes.REPO_ROOT`` exists precisely to resolve that indirection: it reads the
#: ``.git`` FILE a worktree carries and answers the MAIN tree, so every checkout
#: on this machine agrees on one path. That is what a mutex needs and what
#: ``__file__`` cannot give.
#:
#: WHY THE LANE LOCK GETS AWAY WITH THE OTHER SHAPE, so nobody "fixes" it to
#: match: the lane lock and the suite ration are taken DRIVER-side, and the
#: driver runs from the main checkout, so their per-checkout roots already
#: resolve to one path in practice. This is the first store on the WORKER side.
#: ``lanes.DEFAULT_ROOT`` is load-bearing for the driver and is left alone.
DEFAULT_ROOT: Final = lanes.REPO_ROOT / "ops" / "loop" / "control" / "claims"

#: The extension a claim record carries. Distinct from the lane lock's, so a
#: claim root and a lock root could share a directory without either reader
#: mistaking the other's files for its own.
CLAIM_SUFFIX: Final = ".claim"

#: IMPORTED, NOT RESTATED. FREE and RECLAIMABLE mean here exactly what they mean
#: for a lane lock, and two spellings of one state is how a dashboard starts
#: rendering a reclaimable record as a running one. HELD is this domain's own
#: word: the lane-lock spelling is RUNNING, which is a claim about a process,
#: and what is true of a claimed row is that somebody holds it.
FREE: Final = lanes.FREE
RECLAIMABLE: Final = lanes.RECLAIMABLE
HELD: Final = "HELD"

#: A record is created EMPTY by the exclusive create and filled a moment later.
#: Inside that window an unreadable record is presumed live, so a reader cannot
#: reclaim a row out from under a claimant that is mid-write. THE SAME WINDOW THE
#: LANE LOCK USES, imported rather than chosen again, because the two are the
#: same race against the same filesystem.
WRITE_GRACE_S: Final = lanes.WRITE_GRACE_S

#: The longest row id this will key a file by. A guard against a caller handing
#: over a whole line of prose, which would build a path the filesystem refuses
#: for a reason nobody reading the error would connect to the row.
MAX_ROW_LENGTH: Final = 64

#: WHICH LIVENESS ANCHOR A RECORD IS ON, written into the record and rendered
#: by every reader. A store that silently degraded from the cycle anchor to the
#: process anchor would be indistinguishable from one that never had the cycle
#: anchor, which is how CS-1009 survived CS-991's whole test suite.
ANCHOR_LANE: Final = "lane_lock"
ANCHOR_PID: Final = "pid"

#: LANE-ANCHORED, BUT THE LOCK CANNOT PROVE ITS HOLDER. A distinct value rather
#: than a shade of :data:`ANCHOR_LANE`, because the two differ in what an
#: operator must do: the first needs nothing, the second means the LANE is stale
#: too and its lock wants clearing. The state is unaffected - the row is HELD
#: either way, which is the adjudicated ruling - so this is the only place the
#: condition is visible at all.
ANCHOR_LANE_UNPROVEN: Final = "lane_lock_unproven"

#: The directory the lane locks sit in, TAKEN FROM ``lanes`` rather than
#: spelled, so a rename there moves this with it instead of leaving the anchor
#: pointed at nothing - and an anchor pointed at nothing reads FREE, which is
#: the silent degradation above.
_LOCK_DIR_NAME: Final = lanes.DEFAULT_ROOT.name

#: The characters a row id may be spelled with. AN ALLOWLIST RATHER THAN A LIST
#: OF THINGS TO REJECT: a denylist over path syntax has to anticipate every
#: separator, drive letter, reserved device name and dot form the platform
#: honours, and each one it misses writes outside the claim root. The ids this
#: project issues - ``CS-991``, ``CS-G12`` - are inside it with room to spare.
_ROW_ALPHABET: Final = frozenset("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.")

#: Claim path -> the identity THIS process wrote there. The ABA guard: a late
#: release from a previous holder must not unlink the record of whoever
#: reclaimed the row after it. The same structure the lane lock keeps, for the
#: same reason, over a different subject.
_OWNED: dict[str, tuple[str | None, float | None, int | None]] = {}


# ---------------------------------------------------------------------------
# The key
# ---------------------------------------------------------------------------


def row_key(row: Any) -> str:
    """The canonical spelling of a row id, which is this store's key.

    Upper-cased and stripped, so ``cs-991`` and ``CS-991 `` are one row rather
    than two records claiming to hold different things. Case folding matters
    beyond tidiness here: the record is a file, and on a case-insensitive
    filesystem two spellings would collide in the directory while comparing
    unequal in memory.

    A ROW THIS CANNOT SPELL RAISES rather than resolving to something. Answering
    a default would hand a caller a claim on a row it did not name, which is how
    a typo takes a running lane's work - the same ruling ``lanes.slot_index``
    makes about a lane off the roster.

    Args:
        row: The row id.

    Returns:
        The canonical id.

    Raises:
        ValueError: The row id is empty, over-long, or spelled with a character
            outside the allowlist.
    """
    text = str(row).strip().upper()
    if not text:
        message = "row id is mandatory - a claim names the row it holds"
        raise ValueError(message)
    if len(text) > MAX_ROW_LENGTH:
        message = f"row id is longer than {MAX_ROW_LENGTH} characters"
        raise ValueError(message)
    stray = sorted(set(text) - _ROW_ALPHABET)
    if stray:
        message = f"row id carries {stray!r}, which is outside the id alphabet"
        raise ValueError(message)
    if set(text) <= {".", "-", "_"}:
        # ".." and "." name directories rather than rows. Every character is in
        # the alphabet, so only this check separates them from an id.
        message = f"row id {text!r} names a directory rather than a row"
        raise ValueError(message)
    return text


def _resolve_root(root: Any) -> Path:
    """The claim root to use, defaulting to this repository's own."""
    return DEFAULT_ROOT if root is None else Path(root)


def lock_root(root: Any = None) -> Path:
    """Where the LANE LOCKS this store anchors liveness to live.

    A SIBLING OF THE CLAIM ROOT, AND DERIVED FROM IT RATHER THAN TAKEN AS AN
    ARGUMENT. Two reasons, and the first is the one that would have made this
    fix a no-op in production while passing every arm:

    ``lanes.DEFAULT_ROOT`` is rooted at the IMPORTING FILE, not at the main
    tree. A lane's worker runs inside its own checkout and imports that
    checkout's copy of ``ops/loop/lanes.py``, so that constant names a lane
    lock directory INSIDE THE WORKTREE, which holds no lock at all - the
    driver took the lane from the main tree. Anchored there, every claim a
    worker made would find its lane FREE and fall back to the pid, which is
    CS-1009 undisclosed rather than closed. The module docstring on
    :data:`DEFAULT_ROOT` records the same trap being measured across two real
    processes, and this is that trap one directory over.

    So the anchor follows the CLAIM root, which already resolves the main
    checkout through ``lanes.REPO_ROOT``. A caller that names a claim root gets
    its lane locks beside it - one directory pair, moved together - and a
    caller that names none gets the main tree's, which is the only spelling
    every lane agrees on.

    WHAT THAT LEAVES RESTING ON THE DRIVER, stated because the fix depends on it
    and nothing here can check it. The driver takes its lane lock with no root
    at all (`ops/loop/queue_loop.py`, the `acquire` call in `run_cycle`), so the
    lock lands under whichever checkout the DRIVER was started from, and
    `ops/loop/launch_queue_loop.ps1` resolves the driver by its own script root.
    Started from the main checkout - which is how it is documented and run -
    that is this directory and the two agree. Started from inside a worktree it
    would not be, and every claim would find its lane FREE and quietly fall back
    to the pid anchor. This is not a new dependency - the note on
    :data:`DEFAULT_ROOT` already leans on it - but it is load-bearing here in a
    way it was not before, and it is UNMEASURED.

    Args:
        root: The claim root, or None for the default.

    Returns:
        The lane lock root to probe.
    """
    return _resolve_root(root).parent / _LOCK_DIR_NAME


def claim_path(row: Any, root: Any = None) -> Path:
    """Where a NEW claim on this row is written.

    Read-only helper - it creates nothing, so it is safe on the poll path.

    Args:
        row: The row id.
        root: The claim root, or None for the default.

    Returns:
        The derived path.

    Raises:
        ValueError: The row id cannot be spelled.
    """
    return _resolve_root(root) / f"{row_key(row)}{CLAIM_SUFFIX}"


def _claim_files(root: Any) -> list[Path]:
    """Every claim record sitting in one root, sorted. Reads nothing else.

    Total by construction: a root that does not exist, or cannot be listed,
    answers an empty list rather than raising on the poll path.

    Args:
        root: The claim root.

    Returns:
        The claim files present.
    """
    try:
        return sorted(p for p in Path(root).iterdir() if p.suffix == CLAIM_SUFFIX and p.is_file())
    except OSError:
        return []


def _read_record(path: Path) -> tuple[bytes, dict[str, Any]]:
    """One record's RAW BYTES and its decoded payload, read in a SINGLE pass.

    THE BYTES ARE KEPT, and that is not an optimisation. :func:`_reclaim` has to
    prove it removed the record it GRADED rather than whatever happens to occupy
    that path by the time it gets there, and re-reading to obtain them would
    open exactly the window that proof exists to close.

    An unreadable, empty or unparseable record decodes to an empty mapping,
    which names no row and is therefore attributed to nobody.

    Args:
        path: The record file.

    Returns:
        Its bytes, and its payload or an empty mapping.
    """
    try:
        raw = path.read_bytes()
    except OSError:
        return b"", {}
    if not raw.strip():
        return raw, {}
    try:
        record = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        return raw, {}
    return raw, (record if isinstance(record, dict) else {})


def _age_of(record: dict[str, Any], path: Path, now: Any) -> float | None:
    """How old a record is, by its own stamp or failing that by its mtime."""
    stamp = lanes.float_or_none(record.get("ts"))
    if stamp is None:
        try:
            stamp = path.stat().st_mtime
        except OSError:
            return None
    clock = time.time() if now is None else float(now)
    return max(0.0, clock - stamp)


def _candidates(root: Any, now: Any) -> dict[str, list[_Candidate]]:
    """Every record in the store, GROUPED BY THE ROW IT NAMES, each graded.

    ONE PASS, ONE GROUPING, AND EVERY READER ABOVE IS BUILT ON IT. The shape
    this replaces had two resolution rules for one fact - a per-row lookup that
    tried the derived path first, and a whole-store scan where the last file
    name won - and they DISAGREED whenever more than one record named a row: the
    per-row read answered HELD while the scan answered RECLAIMABLE and the queue
    offered the row to a second lane. Two rules for one fact is a disagreement
    waiting for an occasion, so there is one rule and every caller shares it.

    A record whose payload names no row is skipped rather than filed under its
    file name: guessing an identity for an unreadable record is how a reader
    hands somebody else's row to the next caller.

    Args:
        root: The claim root.
        now: The wall clock reading to age the records against.

    Returns:
        Row id -> its records, in sorted file-name order.
    """
    grouped: dict[str, list[_Candidate]] = {}
    for path in _claim_files(_resolve_root(root)):
        raw, record = _read_record(path)
        recorded = lanes.str_or_none(record.get("row"))
        if recorded is None or not recorded.strip():
            continue
        state = _state_of(record, _age_of(record, path, now), root, now)
        grouped.setdefault(recorded.strip().upper(), []).append((path, raw, record, state))
    return grouped


def _authoritative(candidates: list[_Candidate]) -> _Candidate:
    """Which record speaks for a row when more than one names it.

    A LIVE HOLDER WINS. That is the whole rule and it is the conservative one:
    refusing a lane a row somebody may still be working costs one cycle, and
    handing out a row somebody IS working costs two cycles and a contended
    worktree. So a single HELD record decides the row however many stale ones
    sit beside it, and no file name can outvote it.

    THE SORTED ORDER IS A TIE-BREAK AND NEVER A DECISION. It chooses between
    records that are ALL non-HELD, where every choice reports the same state, so
    it settles which holder is NAMED in the report and nothing else. That
    boundary is the reason this is not the positional keying the module
    docstring refuses: position never decides whether a row is held.

    Args:
        candidates: The records naming one row, in sorted file-name order.

    Returns:
        The record that speaks for the row.
    """
    for entry in candidates:
        if entry[3] == HELD:
            return entry
    return candidates[0]


def claim_for_row(row: Any, root: Any = None) -> Path:
    """The record SPEAKING FOR this row, or the path a new claim is written to.

    THE RECORDED ROW IS AUTHORITATIVE, THE FILE NAME IS NOT. The name is derived
    and a change to the derivation re-points it; a reader that trusted the name
    alone would report FREE over a live holder filed under the old spelling, and
    the next claim would double-book a running cycle.

    Args:
        row: The row id.
        root: The claim root, or None for the default.

    Returns:
        The record speaking for the row, or the path it would be claimed at.

    Raises:
        ValueError: The row id cannot be spelled.
    """
    wanted = row_key(row)
    found = _candidates(root, None).get(wanted)
    return claim_path(wanted, root) if not found else _authoritative(found)[0]


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------


def _holder_is_provable(reading: dict[str, Any], root: Any, lane: Any) -> bool:
    """Whether a RUNNING lane lock can PROVE the process behind it is its own.

    THIS DECIDES A LABEL AND NEVER A STATE, and that boundary is the whole of an
    adjudication. Gating the ANCHOR on it was refuted - see the module docstring
    - because it inverted ``lanes.holder_is_a_stranger``'s own ruling and handed
    a live cycle's row to the other lane wherever a start time could not be
    read, which is every box without ``psutil`` and, measured, any box at all
    when ``psutil`` raises ``AccessDenied`` for an elevated or scheduled-task
    holder. DO NOT RE-WIRE THIS INTO :func:`_lane_anchor_state`. What it is for
    is :data:`ANCHOR_LANE_UNPROVEN`, so an operator can SEE a stale lane rather
    than deduce it from a row that will not move.

    THE CONDITION IT MEASURES. ``lanes.holder_is_a_stranger`` needs both the
    start time recorded in the lock and the live one read back; with either
    unreadable it answers "not a stranger" and the lock stays RUNNING. The two
    halves fail TOGETHER rather than independently - when ``lanes.proc_started``
    answers None, ``lanes.repoint_lane_pid`` wrote ``pid_started: null`` for the
    same reason - so this is one condition wearing two fields. ``psutil`` is
    optional in `pyproject.toml`, and where it is absent the condition holds
    unconditionally.

    Args:
        reading: What ``lanes.lane_state`` answered for the lane.
        root: The claim root, whose sibling holds the lane locks.
        lane: The lane whose lock is being weighed.

    Returns:
        True when both halves of the holder's identity can be read.
    """
    pid = lanes.int_or_none(reading.get("pid"))
    if pid is None or lanes.proc_started(pid) is None:
        return False
    try:
        recorded = lanes.read_payload(lanes.lock_for_lane(lock_root(root), lane))
    except (ValueError, OSError):
        return False
    return lanes.float_or_none(recorded.get("pid_started")) is not None


def _lane_anchor_state(record: dict[str, Any], root: Any, now: Any) -> str | None:
    """HELD or RECLAIMABLE from the CYCLE'S lane lock, or None when there is none.

    THE DELEGATION CS-1009 TURNS ON. The record names a lane and the run id its
    lock carried when the claim was taken; this asks ``lanes.lane_state`` what
    that lane is doing now. The row is held exactly while that lock is RUNNING
    behind that same run id - so the claim survives every process the cycle
    spawns and dies with the cycle, which is the acceptance.

    A RUN ID THAT NO LONGER MATCHES IS A LATER CYCLE, not a live one. The lane
    has been released and retaken; whoever wrote this record finished or died,
    and holding its row against the lane's next occupant would wedge the row
    for as long as the loop kept firing.

    None means NO ANCHOR - the record predates the anchor, or was taken with no
    lane lock held, or names a lane off the roster so no lock can exist for it.

    A RUNNING LOCK ANCHORS ITS ROW WHETHER OR NOT ITS HOLDER CAN BE PROVEN, by
    adjudication. An earlier build returned None here when the start time was
    unreadable; that handed a live cycle's row to the other lane on a box
    without ``psutil`` and was refuted. :func:`_holder_is_provable` still
    measures the condition, but it decides a LABEL and never a state, and it
    must not be re-wired into this function.
    The caller then falls back to the pid probe. An off-roster lane is the
    sharp case and it is answered this way deliberately: reporting HELD there
    would wedge the row forever, because the lock it waits on can never appear.

    Args:
        record: The record's payload.
        root: The claim root, whose sibling holds the lane locks.
        now: The wall clock reading, passed through so an arm never sleeps.

    Returns:
        The state the cycle implies, or None when the record carries no anchor.
    """
    anchored = lanes.str_or_none(record.get("lane_run_id"))
    lane = lanes.str_or_none(record.get("lane"))
    if anchored is None or lane is None:
        return None
    try:
        reading = lanes.lane_state(lock_root(root), now, lane)
    except (ValueError, OSError):
        return None
    if reading.get("state") != lanes.RUNNING:
        return RECLAIMABLE
    return HELD if lanes.str_or_none(reading.get("run_id")) == anchored else RECLAIMABLE


def _anchor_of(record: dict[str, Any], root: Any) -> str:
    """Which anchor a record is on. Rendered, so a degradation is readable.

    THREE VALUES, NOT TWO, because "lane-anchored" hides a case an operator has
    to act on. A row held behind a lock that cannot prove its holder looks
    exactly like a row held behind a healthy one - same state, same age, same
    lane - and the difference is that the second needs nothing while the first
    means the LANE is stale and its lock wants clearing. Deducing that from a
    row that will not move is the diagnosis this value exists to skip.

    Args:
        record: The record's payload.
        root: The claim root, whose sibling holds the lane locks.

    Returns:
        One of :data:`ANCHOR_PID`, :data:`ANCHOR_LANE` or
        :data:`ANCHOR_LANE_UNPROVEN`.
    """
    lane = lanes.str_or_none(record.get("lane"))
    if not lanes.str_or_none(record.get("lane_run_id")) or lane is None:
        return ANCHOR_PID
    try:
        reading = lanes.lane_state(lock_root(root), None, lane)
    except (ValueError, OSError):
        return ANCHOR_LANE
    if reading.get("state") != lanes.RUNNING:
        return ANCHOR_LANE
    return ANCHOR_LANE if _holder_is_provable(reading, root, lane) else ANCHOR_LANE_UNPROVEN


def _state_of(record: dict[str, Any], age_s: float | None, root: Any, now: Any) -> str:
    """FREE, HELD or RECLAIMABLE for one record's payload. Decided by the PROBE.

    THE CYCLE IS ASKED FIRST AND ITS ANSWER IS FINAL. The pid branch below is
    the fallback for a record carrying no lane anchor, and it is exactly the
    rule CS-1009 found insufficient for a worker - see the module docstring's
    stated limit for who is still on it and why that is not a silent default.

    Args:
        record: The record's payload.
        age_s: How old the record is, or None when that cannot be established.
        root: The claim root, whose sibling holds the lane locks.
        now: The wall clock reading, passed through so an arm never sleeps.

    Returns:
        The state.
    """
    anchored = _lane_anchor_state(record, root, now)
    if anchored is not None:
        return anchored
    pid = lanes.int_or_none(record.get("pid"))
    if pid is None:
        # No readable holder at all - see WRITE_GRACE_S.
        return RECLAIMABLE if age_s is not None and age_s > WRITE_GRACE_S else HELD
    if not lanes.pid_alive(pid):
        return RECLAIMABLE
    if lanes.holder_is_a_stranger(pid, record.get("pid_started")):
        # Alive, but not the same process: the claimant died and the operating
        # system reissued its pid. Without this the row is wedged forever.
        return RECLAIMABLE
    return HELD


def _reading(entry: _Candidate, now: Any, root: Any = None) -> dict[str, Any]:
    """One graded record rendered as a state answer. NEVER mutates anything."""
    path, _raw, record, state = entry
    return {
        "state": state,
        "age_s": _age_of(record, path, now),
        "row": lanes.str_or_none(record.get("row")),
        "lane": lanes.str_or_none(record.get("lane")),
        "pid": lanes.int_or_none(record.get("pid")),
        "run_id": lanes.str_or_none(record.get("run_id")),
        "worktree": lanes.str_or_none(record.get("worktree")),
        # DECLARED RATHER THAN INFERRED. A reader that had to guess which anchor
        # decided a state could not tell a cycle-anchored store from one that
        # had quietly degraded to the process anchor - which is the shape that
        # made CS-1009 survive a green suite.
        "anchor": _anchor_of(record, root),
        "lane_run_id": lanes.str_or_none(record.get("lane_run_id")),
    }


def claim_state(row: Any, root: Any = None, now: Any = None) -> dict[str, Any]:
    """FREE, HELD or RECLAIMABLE for one row. NEVER mutates anything.

    RECLAIMABLE means a record is present but its holder is provably gone. It is
    REPORTED, not acted on: clearing it is :func:`try_claim_row`'s job, for the
    reason in the module docstring.

    A LOOKUP OF ONE ROW IS :func:`claim_states` NARROWED, not a second rule. The
    per-row and whole-store answers were once computed separately and disagreed
    the moment two records named one row; sharing one implementation makes that
    disagreement unreachable rather than merely untested.

    Args:
        row: The row id.
        root: The claim root, or None for the default.
        now: The wall clock reading to age the record against. Injected so an
            ageing arm never has to sleep.

    Returns:
        The state, the holder it read, and the record's age in seconds.

    Raises:
        ValueError: The row id cannot be spelled.
    """
    found = claim_states(root, now).get(row_key(row))
    if found is None:
        return {
            "state": FREE,
            "row": None,
            "lane": None,
            "pid": None,
            "run_id": None,
            "worktree": None,
            "age_s": None,
            "anchor": None,
            "lane_run_id": None,
        }
    return found


def claim_states(root: Any = None, now: Any = None) -> dict[str, dict[str, Any]]:
    """Every row this store currently holds a record for. NEVER mutates anything.

    THE POPULATION COMES FROM THE DIRECTORY, not from a roster and not from a
    queue the caller brings. A claim store has no fixed membership - the set of
    rows that exist changes with `ROADMAP.md` - so deriving the population any
    other way would mean a record filed under a row the caller did not think to
    ask about went unreported.

    WHERE MORE THAN ONE RECORD NAMES A ROW, :func:`_authoritative` decides which
    speaks for it, and that is the SAME function :func:`claim_state` and
    :func:`claim_for_row` go through. One fact, one rule.

    Args:
        root: The claim root, or None for the default.
        now: The wall clock reading to age the records against.

    Returns:
        A mapping of row id to the state read for it.
    """
    return {
        row: _reading(_authoritative(found), now, root)
        for row, found in _candidates(root, now).items()
    }


def takeable_rows(rows: Iterable[Any], root: Any = None, now: Any = None) -> tuple[str, ...]:
    """The offered queue with every HELD row removed, in the order given.

    A RECLAIMABLE row stays on the queue. Its holder is provably gone, and a
    crashed cycle must never wedge its row out of circulation - that failure
    looks like progress from outside, which is what makes it worse than no claim
    at all.

    A row this store cannot spell is left ON the queue rather than dropped. The
    claim store is not the arbiter of what is a legal row - ``ops/loop/scope.py``
    computes the queue - and silently shortening somebody's queue because of a
    key rule is a fence widening itself in the dark.

    Args:
        rows: The queue the caller computed.
        root: The claim root, or None for the default.
        now: The wall clock reading to age the records against.

    Returns:
        The rows still takeable, in the offered order.
    """
    held = {row for row, state in claim_states(root, now).items() if state["state"] == HELD}
    answer: list[str] = []
    for row in rows:
        text = str(row)
        try:
            key = row_key(text)
        except ValueError:
            answer.append(text)
            continue
        if key not in held:
            answer.append(text)
    return tuple(answer)


def first_takeable(rows: Sequence[Any], root: Any = None, now: Any = None) -> str | None:
    """The first row on the offered queue that nobody is holding.

    THE ORDER IS THE CALLER'S. `tools/headless-queue.md` section 5 owns what the
    queue's order means and this preserves it exactly; all that happens here is
    that held rows are skipped.

    Args:
        rows: The queue the caller computed, in its order.
        root: The claim root, or None for the default.
        now: The wall clock reading to age the records against.

    Returns:
        The first takeable row, or None when every offered row is held.
    """
    takeable = takeable_rows(rows, root, now)
    return takeable[0] if takeable else None


# ---------------------------------------------------------------------------
# Claim and release
# ---------------------------------------------------------------------------


def _reclaim(entry: _Candidate) -> bool:
    """Clear the record that was GRADED reclaimable, and nothing else.

    THE SHAPE THIS REPLACES WAS A TIME-OF-CHECK RACE, and it was the exact
    failure a claim store exists to prevent. It re-read the state and then
    unlinked the path: between those two steps another process could reclaim the
    same record and write its own live claim there, whereupon this unlink
    deleted a LIVE record and the create that followed double-booked the row.
    Checking harder cannot fix that - the gap is between the check and the act.

    SO THE RENAME IS THE ARBITRATION. Renaming a file is all-or-nothing and its
    SOURCE can be moved by exactly one racer: the loser gets "no such file" and
    touches nothing at all. Winning the rename is winning the reclaim, and the
    bytes are then compared against the ones that were graded, because a racer
    that already replaced the record would otherwise have its live claim carried
    off. A mismatch is put straight back and the reclaim refuses.

    WHAT THIS DOES NOT CLOSE, stated rather than implied. A filesystem offers no
    atomic compare-and-swap: between this rename and the caller's exclusive
    create the path is momentarily absent, so a third claimant can create there
    and win - which is CORRECT, because the exclusive create then refuses the
    caller. The genuinely open sliver is the restore path above, where a record
    put back can land on top of a claim made in that same moment. It is much
    narrower than the window it replaces and it is not measured here.

    Args:
        entry: The record as it was graded, bytes included.

    Returns:
        True when this call removed the graded record.
    """
    record_path, graded, _record, state = entry
    if state != RECLAIMABLE:
        return False
    scratch = record_path.with_name(f"{record_path.name}.{os.getpid()}.{uuid.uuid4().hex}.gone")
    try:
        record_path.rename(scratch)
    except OSError:
        # Another racer moved it first, or it is gone. Either way not ours.
        return False
    try:
        carried = scratch.read_bytes()
    except OSError:
        carried = None
    if carried != graded:
        # Somebody replaced the record between the grade and the rename, so what
        # was just carried off is not what was judged dead. Put it back.
        with contextlib.suppress(OSError):
            scratch.replace(record_path)
        return False
    lanes.remove_quietly(scratch)
    return True


def _refusal(state: dict[str, Any]) -> dict[str, Any]:
    """The answer a genuinely held row gets. Writes nothing, by construction."""
    return {
        "ok": False,
        "refused": "row_claimed",
        "row": state["row"],
        "lane": state["lane"],
        "pid": state["pid"],
        "run_id": state["run_id"],
    }


def _cycle_run_id(lane: Any, root: Any) -> str | None:
    """The run id of the cycle currently RUNNING on a lane, or None.

    None where no cycle holds the lane - which is every hand-run claim, and is
    the stated limit rather than an error. See the module docstring.

    Args:
        lane: The lane the claim is being taken on.
        root: The claim root, whose sibling holds the lane locks.

    Returns:
        The lock's run id, or None when the lane is not running one.
    """
    try:
        reading = lanes.lane_state(lock_root(root), None, lane)
    except (ValueError, OSError):
        return None
    if reading.get("state") != lanes.RUNNING:
        return None
    return lanes.str_or_none(reading.get("run_id"))


def try_claim_row(
    row: Any, *, lane: Any, run_id: Any, worktree: Any, root: Any = None
) -> dict[str, Any]:
    """Claim a row for the life of one cycle, or refuse.

    A holder whose pid is dead is reclaimed rather than respected: a crashed
    cycle must never take its row out of circulation. A holder that is genuinely
    live is refused, and the refusal touches nothing on disk - the state is read
    BEFORE any mkdir or scratch write for exactly that reason.

    Args:
        row: The row id to claim.
        lane: The lane claiming it. Must be on ``lanes.LANES``.
        run_id: The caller's identifier for this cycle.
        worktree: The working directory the cycle runs in. Mandatory.
        root: The claim root, or None for the default.

    Returns:
        ``{"ok": True, "row", "lane", "run_id", "worktree", "token"}`` on
        success - ``token`` is the record path and is what :func:`release_claim`
        wants back - or ``{"ok": False, "refused": "row_claimed", ...}``, which
        is a normal answer rather than an error.

    Raises:
        ValueError: The row cannot be spelled, the lane is not on the roster, or
            the worktree is absent or the main tree.
    """
    key = row_key(row)
    lanes.slot_index(lane)  # ROSTER CHECK, raising the one message for an unknown lane
    target = lanes.require_worktree(worktree)
    directory = _resolve_root(root)

    found = _candidates(directory, None).get(key)
    if found is not None:
        speaker = _authoritative(found)
        if speaker[3] == HELD:
            return _refusal(_reading(speaker, None, directory))
        # Nothing here is held, so EVERY record naming this row is stale and
        # every one of them is cleared. Leaving a duplicate behind would let it
        # win a later grading and report a holder that finished long ago.
        for stale in found:
            if not _reclaim(stale):
                # The reclaim lost its arbitration, which means another process
                # is acting on this row right now. Re-read rather than create
                # over whatever it is doing.
                return _refusal(claim_state(key, directory))

    # READ OFF THE LANE'S LOCK, NEVER OFF THE ARGUMENTS. `run_id` above is the
    # WORKER'S own and has nothing to do with the driver's - see the module
    # docstring. This is the derivation the acceptance asks for: all the caller
    # supplies is which lane it is on, and the store establishes the liveness.
    cycle = _cycle_run_id(lane, directory)
    payload: dict[str, Any] = {
        "row": key,
        "lane": str(lane),
        "run_id": str(run_id),
        "worktree": str(target),
        # ONE SOURCE FOR THE ANCHOR, WHICH IS THIS FIELD. The anchor a reader
        # renders is DERIVED from it by `_anchor_of`, never stored beside it: a
        # second copy is a second thing to drift, and a stored anchor that
        # disagreed with the run id beside it would be read in preference to
        # the truth (CLAUDE.md section 4).
        "lane_run_id": cycle,
        "pid": os.getpid(),
        "ts": time.time(),
        "repo": str(lanes.REPO_ROOT),
        # The other half of the holder's identity. `ts` is when the row was
        # CLAIMED and is not a substitute: comparing a start time against it
        # needs a tolerance and is wrong in both directions.
        "pid_started": lanes.proc_started(os.getpid()),
    }
    token = lanes.exclusive_create(claim_path(key, directory), payload)
    if token is None:
        # Lost a race between the read above and the exclusive create.
        return _refusal(claim_state(key, directory))
    _OWNED[lanes.path_key(token)] = (payload["run_id"], payload["ts"], payload["pid"])
    return {
        "ok": True,
        "row": key,
        "lane": payload["lane"],
        "run_id": payload["run_id"],
        "worktree": payload["worktree"],
        "token": str(token),
    }


def _record_for(token: Any, root: Any) -> Path | None:
    """The record a token names, or None when the token is empty.

    Args:
        token: What :func:`try_claim_row` handed back.
        root: The claim root, used only when the token is a bare name.

    Returns:
        The record path, or None.
    """
    if token is None or not str(token).strip():
        return None
    record_path = Path(str(token).strip())
    if not record_path.is_absolute():
        record_path = _resolve_root(root) / record_path.name
    return record_path


def _identity(record: dict[str, Any]) -> tuple[str | None, float | None, int | None]:
    """The triple that names one holder of one record."""
    return (
        lanes.str_or_none(record.get("run_id")),
        lanes.float_or_none(record.get("ts")),
        lanes.int_or_none(record.get("pid")),
    )


def _this_checkout() -> Path:
    """The checkout THIS COPY of the module was imported from.

    DELIBERATELY THE OPPOSITE DERIVATION FROM :data:`DEFAULT_ROOT`, and the two
    are not in tension. The STORE must be one directory every lane agrees on, so
    it resolves the main tree. IDENTITY must be local, because the whole point is
    to tell one lane's worker from another's, and the thing that differs between
    them is exactly which checkout they run in. Same module, two questions, two
    derivations.

    Returns:
        The working tree this module was loaded from.
    """
    return Path(__file__).resolve().parents[2]


def running_cycle_here(root: Any = None) -> tuple[str, str] | None:
    """The lane and run id of the cycle THIS PROCESS IS RUNNING INSIDE, or None.

    DERIVED FROM THE CHECKOUT, WHICH IS NOT A CREDENTIAL AND CANNOT BE PRESENTED.
    Every lane's worker runs in its OWN worktree - ``ops/loop/lane_launcher.py``
    gives each lane one and no two lanes share - and the lane lock records which
    worktree it handed out. So a process can be ASKED which lane it is, by
    matching the tree it was imported from against the roster's locks, and it
    has nothing to say about the answer.

    THIS REPLACES A RECEIPT, AND THE RECEIPT WAS REFUTED. That build handed the
    claimant a digest of the record's bytes and accepted it back as proof of
    ownership. Every lane can read every claim file, so the digest was
    computable by anyone who could name the record - one line of code - and an
    adversary used it to delete a live record from the lane that had
    legitimately reclaimed the row. Worse, re-reading and re-hashing was the
    only documented way for a worker that had lost the string across thousands
    of seconds of fresh subprocesses to wrap at all, so THE ATTACK WAS THE
    RECOVERY PATH. A secret that every reader can recompute is not a secret, and
    the repair is to stop authenticating and start deriving.

    AN AMBIGUOUS CHECKOUT ANSWERS NONE, AND ROSTER ORDER IS NOT A TIE-BREAK.
    If two live locks record this tree, a process in it genuinely is
    indistinguishable between the lanes, and returning the first match is an
    arbitrary choice between two answers that are equally wrong. An adversary
    measured that shape: with both lanes pointed at one tree ``LANES[0]`` won
    every time, so one lane acted with the other's identity and DELETED its live
    record while naming nothing but the public row id, and the lane that lost
    the tie could not release its own records at all.

    NONE TURNS A BREACH INTO A LEAK, which is the trade this module makes
    everywhere: the record is left behind, reads RECLAIMABLE once its cycle
    ends, and the next claim clears it. ``lanes.try_acquire_lane`` now refuses
    to create the state at all; this is what happens when it is found anyway,
    from a lock an older build left on disk.

    Args:
        root: The claim root, whose sibling holds the lane locks.

    Returns:
        The lane and its current run id, or None when this process is not
        running inside exactly one lane's worktree.
    """
    here = _this_checkout()
    matches: list[tuple[str, str]] = []
    for lane in lanes.LANES:
        try:
            reading = lanes.lane_state(lock_root(root), None, lane)
        except (ValueError, OSError):
            continue
        if reading.get("state") != lanes.RUNNING:
            continue
        worktree = lanes.str_or_none(reading.get("worktree"))
        run_id = lanes.str_or_none(reading.get("run_id"))
        if worktree is None or run_id is None:
            continue
        if lanes.same_tree(worktree, here):
            matches.append((str(lane), run_id))
    # EXACTLY ONE, OR NONE. Never the first of several - see above.
    return matches[0] if len(matches) == 1 else None


def _is_ours(record_path: Path, record: dict[str, Any], root: Any = None) -> bool:
    """True when the record's CURRENT payload is the identity we wrote there.

    THE ABA GUARD. If the row was reclaimed and re-claimed after our token was
    issued, the payload has moved on and this answers False, so a late release
    cannot unlink the new holder's record. Limit, stated rather than hidden: a
    token is a path and every holder of one row uses the same path, so two
    claims by THIS process are indistinguishable - harmless, since both are us.
    The cross-process case, the one that matters, is caught.

    ``_OWNED`` IS PROCESS-LOCAL AND A WORKER IS NOT ONE PROCESS - the second
    facet of CS-1009. An LLM worker reaches python per call, so the subprocess
    that WRAPS a cycle is never the one that claimed the row and inherits no
    table entry. The old fallback compared the record's pid against the
    releasing process's own, which could not match, so the wrap left its record
    on disk and reported nothing removed.

    NOTHING IS PRESENTED. THE LANE IS DERIVED - see :func:`running_cycle_here`
    for the two credential shapes that were tried here and refuted. A process
    running inside a lane's worktree may remove a record that names THAT lane
    and carries THAT lane's current run id, and nothing else. The attacker in
    the measured counter-example runs in its own lane's tree, so it derives its
    own lane, finds a record naming the other, and refuses STRUCTURALLY rather
    than by losing a comparison it could have won by reading a file.

    A DERIVED LANE IS FINAL AND DOES NOT FALL THROUGH TO THE PID. Falling
    through would hand back the shape this replaces: a second chance decided by
    something the caller is holding.

    THE RESIDUALS, BOTH BOUNDED AND BOTH LEAKS OF A RECORD RATHER THAN A ROW.
    A wrap arriving after its own lane lock was released or retaken derives no
    lane, falls to the pid comparison and fails it, so the record stays. So does
    a record taken with no anchor by a process that has since exited. Neither
    can wedge a row: the record reads RECLAIMABLE on its own merits and the next
    claim clears it.

    Args:
        record_path: The record file.
        record: Its current payload.
        root: The claim root, whose sibling holds the lane locks.

    Returns:
        True when this process may act on the record.
    """
    owned = _OWNED.get(lanes.path_key(record_path))
    identity = _identity(record)
    if owned is not None:
        return identity == owned
    cycle = running_cycle_here(root)
    if cycle is None:
        return identity[2] == os.getpid()
    lane, run_id = cycle
    return (
        lanes.str_or_none(record.get("lane")) == lane
        and lanes.str_or_none(record.get("lane_run_id")) == run_id
    )


def release_claim(token: Any, root: Any = None, **_retired_credentials: Any) -> bool:
    """Release a claim handed out by :func:`try_claim_row`. Idempotent.

    DELIBERATE, AND THAT IS THE WHOLE CONTRACT. A claim is released because a
    cycle WRAPPED, never because a process stopped. A cycle that is killed
    leaves its record exactly where it was; the record then reads RECLAIMABLE,
    because its holder can no longer be found, and the next fire may take the
    row. Those are different events and they are reported differently: a release
    says the holder finished, a reclaim says nobody can prove it did.

    True when this call removed the record; False when there was nothing of ours
    to remove. NEVER raises - a release runs in a finally, and a release that can
    throw turns one failure into two.

    A LATER SUBPROCESS OF THE SAME CYCLE NEEDS TO PRESENT NOTHING. The ownership
    table is process-local, so a worker that reaches python per call has none by
    the time it wraps; :func:`_is_ours` DERIVES the lane from the checkout the
    caller is running in instead. Two credential shapes were tried here first, a
    run id and a receipt, and both were measured to let one lane delete
    another's live record; neither may be reintroduced.

    ``**_retired_credentials`` IS WHY THOSE TWO CAN BE RETIRED SAFELY. A wrap
    runs in a ``finally`` and this function's contract is that it NEVER raises;
    a worker still following an older convention would otherwise hit a
    ``TypeError`` on a keyword that no longer exists, turning one failure into
    two, at the exact moment the prompt it is following has been edited under
    it. Retired credentials are accepted and IGNORED. Nothing decides anything
    on them, which is the whole point of deriving instead.

    IGNORED IN BOTH DIRECTIONS, AND SILENTLY - stated because it surprises.
    A caller passing a WRONG value is not refused: ``run_id='TOTALLY-WRONG'``
    from the right tree releases, because the value is never read at all. That
    is correct - the derivation decided, and it decided on the tree - but a
    worker still following an older convention gets no signal that what it
    passed was never consulted. There is deliberately no warning: a release runs
    in a ``finally`` at the end of a cycle, and a diagnostic there is noise
    nobody reads attached to the one call that must never fail.

    Args:
        token: What :func:`try_claim_row` handed back.
        root: The claim root, used only when the token is a bare name.
        **_retired_credentials: Accepted and ignored - see above.

    Returns:
        True when this call removed the record.
    """
    record_path = _record_for(token, root)
    if record_path is None:
        return False
    key = lanes.path_key(record_path)
    if not record_path.exists():
        _OWNED.pop(key, None)
        return False
    record = lanes.read_payload(record_path)
    if not record or not _is_ours(record_path, record, root):
        # Half-written, corrupt, or somebody else's now - not provably ours.
        return False
    try:
        record_path.unlink()
    except OSError:
        return False
    _OWNED.pop(key, None)
    return True
