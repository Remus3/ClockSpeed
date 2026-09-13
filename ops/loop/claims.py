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
"""

from __future__ import annotations

import os
import time
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Any, Final

from ops.loop import lanes

_HERE: Final = Path(__file__).resolve().parent

#: Beside the lane locks and under the same gitignored control plane. A claim is
#: runtime state about this machine's current work and is never tracked.
DEFAULT_ROOT: Final = _HERE / "control" / "claims"

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


def claim_for_row(row: Any, root: Any = None) -> Path:
    """The record HOLDING this row, or the path a new claim would be written to.

    THE RECORDED ROW IS AUTHORITATIVE, THE FILE NAME IS NOT. The name is derived
    and a change to the derivation re-points it; a reader that trusted the name
    alone would report FREE over a live holder filed under the old spelling, and
    the next claim would double-book a running cycle. So the derived path is
    tried first - it is right in every ordinary case and costs one stat - and
    only when nothing is there does this look for a record that NAMES this row.

    WHAT IT DELIBERATELY DOES NOT DO: attribute an unreadable record. A record
    with no readable payload names no row, so it is left where it is rather than
    claimed by the first reader that stumbles on it - :data:`WRITE_GRACE_S` in
    :func:`claim_state` is the answer to that one.

    Args:
        row: The row id.
        root: The claim root, or None for the default.

    Returns:
        The record holding the row, or the path it would be claimed at.

    Raises:
        ValueError: The row id cannot be spelled.
    """
    wanted = row_key(row)
    derived = claim_path(wanted, root)
    if derived.exists():
        return derived
    for candidate in _claim_files(_resolve_root(root)):
        recorded = lanes.str_or_none(lanes.read_payload(candidate).get("row"))
        if recorded is not None and recorded.strip().upper() == wanted:
            return candidate
    return derived


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------


def _state_of(record: dict[str, Any], age_s: float | None) -> str:
    """FREE, HELD or RECLAIMABLE for one record's payload. Decided by the PROBE.

    Args:
        record: The record's payload.
        age_s: How old the record is, or None when that cannot be established.

    Returns:
        The state.
    """
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


def _reading(record: dict[str, Any], path: Path, now: Any) -> dict[str, Any]:
    """One record rendered as a state answer. NEVER mutates anything."""
    stamp = lanes.float_or_none(record.get("ts"))
    if stamp is None:
        try:
            stamp = path.stat().st_mtime
        except OSError:
            stamp = None
    clock = time.time() if now is None else float(now)
    age_s = None if stamp is None else max(0.0, clock - stamp)
    return {
        "state": _state_of(record, age_s),
        "row": lanes.str_or_none(record.get("row")),
        "lane": lanes.str_or_none(record.get("lane")),
        "pid": lanes.int_or_none(record.get("pid")),
        "run_id": lanes.str_or_none(record.get("run_id")),
        "worktree": lanes.str_or_none(record.get("worktree")),
        "age_s": age_s,
    }


def claim_state(row: Any, root: Any = None, now: Any = None) -> dict[str, Any]:
    """FREE, HELD or RECLAIMABLE for one row. NEVER mutates anything.

    RECLAIMABLE means a record is present but its holder is provably gone. It is
    REPORTED, not acted on: clearing it is :func:`try_claim_row`'s job, for the
    reason in the module docstring.

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
    record_path = claim_for_row(row, root)
    if not record_path.exists():
        return {
            "state": FREE,
            "row": None,
            "lane": None,
            "pid": None,
            "run_id": None,
            "worktree": None,
            "age_s": None,
        }
    return _reading(lanes.read_payload(record_path), record_path, now)


def claim_states(root: Any = None, now: Any = None) -> dict[str, dict[str, Any]]:
    """Every row this store currently holds a record for. NEVER mutates anything.

    THE POPULATION COMES FROM THE DIRECTORY, not from a roster and not from a
    queue the caller brings. A claim store has no fixed membership - the set of
    rows that exist changes with `ROADMAP.md` - so deriving the population any
    other way would mean a record filed under a row the caller did not think to
    ask about went unreported.

    A record whose payload names no row is skipped rather than filed under its
    file name: guessing an identity for an unreadable record is how a reader
    hands somebody else's row to the next caller.

    Args:
        root: The claim root, or None for the default.
        now: The wall clock reading to age the records against.

    Returns:
        A mapping of row id to the state read for it.
    """
    answer: dict[str, dict[str, Any]] = {}
    for candidate in _claim_files(_resolve_root(root)):
        record = lanes.read_payload(candidate)
        recorded = lanes.str_or_none(record.get("row"))
        if recorded is None or not recorded.strip():
            continue
        answer[recorded.strip().upper()] = _reading(record, candidate, now)
    return answer


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


def _reclaim(row: str, root: Any) -> bool:
    """Clear a record whose holder is provably gone. Never touches a live one.

    Args:
        row: The canonical row id.
        root: The claim root.

    Returns:
        True when the row is free afterwards.
    """
    record_path = claim_for_row(row, root)
    if not record_path.exists():
        return True
    if claim_state(row, root)["state"] != RECLAIMABLE:
        return False
    lanes.remove_quietly(record_path)
    return not record_path.exists()


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

    state = claim_state(key, directory)
    if state["state"] == HELD:
        return _refusal(state)
    if state["state"] == RECLAIMABLE:
        _reclaim(key, directory)

    payload: dict[str, Any] = {
        "row": key,
        "lane": str(lane),
        "run_id": str(run_id),
        "worktree": str(target),
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


def _is_ours(record_path: Path, record: dict[str, Any]) -> bool:
    """True when the record's CURRENT payload is the identity we wrote there.

    THE ABA GUARD. If the row was reclaimed and re-claimed after our token was
    issued, the payload has moved on and this answers False, so a late release
    cannot unlink the new holder's record. Limit, stated rather than hidden: a
    token is a path and every holder of one row uses the same path, so two
    claims by THIS process are indistinguishable - harmless, since both are us.
    The cross-process case, the one that matters, is caught.

    Args:
        record_path: The record file.
        record: Its current payload.

    Returns:
        True when this process may act on the record.
    """
    owned = _OWNED.get(lanes.path_key(record_path))
    identity = _identity(record)
    if owned is not None:
        return identity == owned
    return identity[2] == os.getpid()


def release_claim(token: Any, root: Any = None) -> bool:
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

    Args:
        token: What :func:`try_claim_row` handed back.
        root: The claim root, used only when the token is a bare name.

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
    if not record or not _is_ours(record_path, record):
        # Half-written, corrupt, or somebody else's now - not provably ours.
        return False
    try:
        record_path.unlink()
    except OSError:
        return False
    _OWNED.pop(key, None)
    return True
