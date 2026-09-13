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
        state = _state_of(record, _age_of(record, path, now))
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


def _reading(entry: _Candidate, now: Any) -> dict[str, Any]:
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
        row: _reading(_authoritative(found), now) for row, found in _candidates(root, now).items()
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
            return _refusal(_reading(speaker, None))
        # Nothing here is held, so EVERY record naming this row is stale and
        # every one of them is cleared. Leaving a duplicate behind would let it
        # win a later grading and report a holder that finished long ago.
        for stale in found:
            if not _reclaim(stale):
                # The reclaim lost its arbitration, which means another process
                # is acting on this row right now. Re-read rather than create
                # over whatever it is doing.
                return _refusal(claim_state(key, directory))

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
