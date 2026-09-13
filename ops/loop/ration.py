#!/usr/bin/env python
r"""Suite ration - ONE local suite at a time, whatever lane asked for it.

WHAT THIS RATIONS AND WHY IT IS NOT A PREFERENCE. `ops/loop/queue_loop.py` runs a
full local suite as a cycle's acceptance. Nothing until now stopped two lanes
doing that at the same moment, and CS-992 made a second lane startable, so the
overlap went from impossible to merely unscheduled. The failure mode was
MEASURED on this box rather than predicted: concurrent pytest runs exhaust the
Windows fork budget, the suite that loses reports a pass count and one error
while thousands of tests never run, and the failures land on UNRELATED subprocess
tests - so resource exhaustion reads as a scatter of flakes. An unattended lane
then writes a green it did not earn, and that ledger row is indistinguishable
from one that was earned.

WHY A THIRD PRIMITIVE, AND NOT ONE OF THE TWO ALREADY HERE. The decision was
made against the three candidates rather than by reflex:

  * THE LANE LOCK (`ops/loop/lanes.py`) is per lane, and the suite step runs
    INSIDE a held lane lock. A resource two lanes contend for cannot be
    rationed by the thing that distinguishes them.
  * `LEDGER_MUTEX` serialises an append of a few hundred bytes. A suite is
    measured in tens of minutes here, and holding the ledger's name for that
    long would block every other lane's row all night - correct-looking, and
    useless.
  * `ops/loop/winmutex.py` is the right SHAPE and the wrong GUARANTEE. It
    carries three fail-open branches that yield unheld and serialise nothing -
    off Windows, on a CreateMutexW failure, and on an unexpected wait result.
    A ration inherits those, and a ration that quietly does not ration is the
    precise defect this file exists to close. Its abandoned-mutex handling does
    answer the dead-holder question, but only on Windows, so every arm below
    would be vacuous on the ubuntu leg of tier 2.

So the primitive is new, and its LIVENESS PREDICATE is not: `lanes.pid_alive`,
`lanes.proc_started` and `lanes.holder_is_a_stranger` are reused verbatim. That
is deliberate. A second, separately written answer to "is the holder still
there" is a second thing to get wrong, and the two would diverge silently -
CS-918 made `holder_is_a_stranger` public for exactly this reason.

READS DO NOT WRITE. `slot_state` is the poll path, and it decides FREE, RUNNING
or RECLAIMABLE by PROBING the recorded pid - never by stat-ing the file, never by
its existence. A reader that auto-cleared a stale slot would make a rendering
pass mutate the control plane and would let two pollers race each other into a
reclaim. Clearing happens in `try_acquire` and nowhere else, which is the ruling
`lanes.py` already made and the reason a dead holder is DETECTED by a read that
changes nothing.

A HARD KILL SKIPS EVERY `finally`, WHICH IS WHY EXISTENCE IS NOT HELD. The
release in `hold_suite_slot` runs on the ordinary path; a killed driver never
reaches it and leaves the slot file behind. Under an existence-is-held rule that
file wedges the ration forever and the next lane waits on a process that does
not exist - a wedge that looks like patience, which is worse than no ration at
all. The pid probe is what makes the killed case RECLAIMABLE rather than
RUNNING, and it needs no timeout, no heartbeat and no cleanup pass.

THE WAITING IS THE DRIVER'S, NOT THE WORKER'S. `hold_suite_slot` does the
sleeping, and `queue_loop.py`'s docstring rules that the driver owns every wait
and the worker owns none. This is called from the DRIVER process, on the
driver's own injected `sleep` and `monotonic`, so the thing that waits is still
the Python process the rule is about. No worker ever calls this, and the worker's
own suite runs - inside its iteration loop and inside the frozen pre-push hook -
are outside this ration and are stated as such rather than implied away.

MONOTONIC, NEVER WALL TIME, for the ceiling. Wall time is not monotonic: an NTP
step backwards silently extends a deadline by however far the clock moved and a
frozen clock extends it forever. The AGE of a slot is measured against wall time
because that is what its `ts` records and what an operator reads at 3am, and it
decides nothing except the brief write window below.

REFUSING IS NOT AN OPTION, SO THE CEILING FALLS THROUGH LOUDLY. A ration that
refuses turns a slow night into a dead one, so `hold_suite_slot` waits. A caller
that passes a ceiling is saying how long it will wait before it proceeds
UNRATIONED, and that occasion emits `UNRATIONED` - one spelling, so a log reader
can find every moment the ration did not hold. Silence there is the bug: it
would make the one cycle that overlapped the one cycle nobody can see.

`ceiling_s=None` MEANS WAIT, and it is the default, so no number lives in this
file that another file already owns. `queue_loop.py` owns the suite's own wedge
ceiling and derives the waiter's from it.

THE ROOT IS BOX-WIDE, NOT CHECKOUT-LOCAL, and that is a correction rather than a
preference. An earlier revision put it under this module's own directory and
recorded the consequence as a residual - two clones of this repository at
different paths derive different roots, ration against themselves, and never see
each other. That is the hole `queue_loop.worktree_mutex` was written to close
for the driver guard, in its own words the half that must not be narrowed, and a
residual is a record of a hole rather than a closure of it. `default_root` is
where the scoping now lives, with the one thing it still does not cover.

WHAT THIS DOES NOT COVER, MEASURED RATHER THAN ESTIMATED. Per productive lane
cycle this repository issues three pytest runs, and exactly ONE of them is the
driver's own:

  * `.githooks/pre-push` runs `pytest tests -q -x -n auto --dist loadfile` on
    the worker's push - eight workers, and its own header records 320s on a real
    push against 765s serial. That is the xdist run, it is the mechanism named
    in the defect, and it is OUTSIDE this ration. The hook is a FROZEN file
    (CLAUDE.md section 6) and closing that gap needs a grant this item does not
    have.
  * the worker's own `pytest tests -q -m "not slow"` is serial and inside the
    worker, which this driver reaches only by pid. Also outside.
  * the driver's `run_local_suite` is serial, and is the one this file rations.

So the honest fraction is one of three invocations and none of the one that
forks - AND THAT FRACTION IS CONDITIONAL, which an earlier wording of this
paragraph stated as a flat property and an adjudicator caught. It holds only
when the driver is asked for a local suite at all. `local_suite` defaults to
FALSE and `launch_queue_loop.ps1` forwards the flag only when it is passed, so
on a DEFAULT night the driver issues no suite, this ration covers ZERO of the
two invocations that do run, and the cycle records `RATION_NO_SUITE` rather
than a coverage it did not provide. Read the conditional at the call site as
the authority and this paragraph as its summary, never the other way round.

The driver COULD cover the other two transitively by holding the slot
across the whole worker cycle; that is rejected in `queue_loop.run_suite_step`
with the arithmetic, because it serialises a cycle bounded at
`DEFAULT_CYCLE_TIMEOUT_S` to protect a 320s window. A SIBLING PROJECT's suite is
not covered either, and cannot be from here: `lanes.py` already ruled that
enrolling other repositories in a shared bucket unilaterally is exactly the
silent divergence their byte-identity pin exists to prevent.

SIDE-EFFECT FREE AT IMPORT. Nothing below creates a directory, reads the control
plane or resolves `lanes` at import time.
"""

from __future__ import annotations

import contextlib
import importlib
import importlib.util
import json
import os
import sys
import tempfile
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent

#: The one slot. A ration of width one is the whole design: the measured defect
#: is two suites, and a width written as a number here would be a second place
#: to change when it is not one.
SLOT_NAME = "suite.slot"

#: The slot root's own directory name, OWNED HERE and read by `queue_loop.py`
#: when `--control-dir` points the control plane at a sandbox. Stated once: a
#: second spelling beside the default below is a second thing to edit, and the
#: half that got missed would leave a sandboxed run rationing against the real
#: control plane while reporting itself isolated.
DIR_NAME = "ration"

#: The machine-wide parent this project claims, and the environment variable
#: that moves the whole root. The variable exists so an operator can point the
#: ration somewhere else WITHOUT editing a tracked file, which is the same
#: reason `LANE_SCOPE_ENV_PREFIX` is an environment variable in `lanes.py`.
BOX_DIRNAME = "Clockspeed"
ROOT_ENV = "CLOCKSPEED_SUITE_RATION_ROOT"


def default_root() -> Path:
    """The slot root when nobody names one - BOX-WIDE, NOT CHECKOUT-LOCAL.

    THIS IS THE HALF THAT MUST NOT BE NARROWED, and the wording is deliberate:
    it is the ruling `queue_loop.worktree_mutex` already made, applied to the
    same class of resource. A root under `__file__` gives two clones of this
    repository at different paths two DIFFERENT roots, so each rations against
    itself and neither sees the other - which is not a smaller version of the
    guarantee, it is the absence of one, because the measured incident was
    several suites at once on ONE box. An earlier revision of this file put the
    root under the module directory and said so in a residual; a residual is a
    record of a hole, not a closure of it.

    `%PROGRAMDATA%` is the machine-wide, per-machine-not-per-user location on
    Windows, and it is read from the environment rather than spelled, so no
    absolute path and no account name enters a tracked file (CLAUDE.md
    non-negotiable 3). Off Windows, and on a Windows box that somehow has no
    `PROGRAMDATA`, this degrades to the system temporary directory - which is
    box-wide on POSIX and is the best available answer rather than a good one.

    WHAT IT STILL DOES NOT COVER, stated rather than implied: a SIBLING PROJECT
    running its own suite. Covering that needs a name those trees also take, and
    `lanes.py` already ruled that enrolling other repositories in a shared
    bucket unilaterally is the silent divergence their byte-identity pin exists
    to prevent. So this root is box-wide for every clone of THIS project and for
    nothing else.

    Returns:
        The slot root.
    """
    named = os.environ.get(ROOT_ENV, "").strip()
    if named:
        return Path(named)
    program_data = os.environ.get("PROGRAMDATA", "").strip()
    parent = Path(program_data) if program_data else Path(tempfile.gettempdir())
    return parent / BOX_DIRNAME / DIR_NAME


FREE = "FREE"
RUNNING = "RUNNING"
RECLAIMABLE = "RECLAIMABLE"

#: The marker every unrationed path emits. ONE spelling, so a log reader can
#: find every occasion the ration did not hold - the idiom is `winmutex`'s
#: `UNSERIALIZED` and it is spelled the same way for the same reason.
UNRATIONED = "ration: UNRATIONED"

#: A slot is created EMPTY by the exclusive create and filled a moment later.
#: Inside this window an unreadable slot is presumed live, so a waiter cannot
#: reclaim it out from under an acquirer that is mid-write. Past it nothing
#: about the slot can be proven alive, so it reads RECLAIMABLE rather than
#: wedging the ration forever. Same constant and same reason as
#: `lanes.WRITE_GRACE_S`; it is restated rather than imported because a lane
#: lock and a suite slot are different resources that happen to agree today.
WRITE_GRACE_S = 30.0

#: How long a waiter sleeps between attempts when the caller names nothing. A
#: suite runs for tens of minutes, so polling faster buys nothing and only wakes
#: the box.
DEFAULT_POLL_S = 10.0

#: How CS-1000 says a module in this package must be reached. The driver runs as
#: `pythonw <repo>/ops/loop/queue_loop.py`, so `sys.path` carries `ops/loop` and
#: NOT the repository root: the package route fails and each importer falls back
#: to loading by path under its own private name, producing TWO module objects
#: with two process-global maps. The private name below is `queue_loop`'s, so
#: whichever file falls back first publishes the one object both then share.
_LANES_DOTTED = "ops.loop.lanes"
_LANES_PRIVATE = "cs_loop_lanes"

#: Slot path -> the identity THIS process wrote there. The ABA guard: a late
#: release from a previous holder must not unlink the slot of whoever acquired
#: after it.
_OWNED: dict[str, tuple[str | None, float | None, int | None]] = {}


def _lanes() -> Any:
    """The ONE `lanes` module object, by the package route wherever it works.

    Only the liveness predicates are read from it, and those are pure - so a
    duplicate module object would be harmless HERE. It is resolved this way
    anyway, because the harm of a duplicate is invisible until the day somebody
    reads a stateful name through this function, and by then the two copies have
    been diverging for weeks.

    Returns:
        The `lanes` module.

    Raises:
        ModuleNotFoundError: `lanes.py` is not beside this file.
    """
    try:
        return importlib.import_module(_LANES_DOTTED)
    except ImportError:
        pass
    if _LANES_PRIVATE in sys.modules:
        return sys.modules[_LANES_PRIVATE]
    spec = importlib.util.spec_from_file_location(_LANES_PRIVATE, _HERE / "lanes.py")
    if spec is None or spec.loader is None:  # pragma: no cover - unreachable
        message = "cannot load lanes.py by path"
        raise ModuleNotFoundError(message)
    module = importlib.util.module_from_spec(spec)
    sys.modules[_LANES_PRIVATE] = module
    spec.loader.exec_module(module)
    # AFTER a successful exec, so a half-executed module is never published
    # under the name every other importer will now trust.
    sys.modules.setdefault(_LANES_DOTTED, module)
    return module


def _resolve_root(root: Any) -> Path:
    """The slot root to use, defaulting to this repository's own."""
    return default_root() if root is None else Path(root)


def _key(path: Any) -> str:
    """A comparable spelling of a path.

    `normpath` rather than `resolve`: resolve expands 8.3 short components on
    Windows, so two spellings of one directory stop comparing equal depending on
    which one the caller happened to hold.

    Args:
        path: Anything path-like.

    Returns:
        The case-folded, normalised, absolute spelling.
    """
    return os.path.normcase(os.path.normpath(str(Path(path).absolute())))


def _int_or_none(value: Any) -> int | None:
    """The value as an int, or None when it is not one."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _float_or_none(value: Any) -> float | None:
    """The value as a float, or None when it is not one."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _str_or_none(value: Any) -> str | None:
    """The value as a string, or None when it is absent."""
    return None if value is None else str(value)


def slot_path(root: Any = None) -> Path:
    """Where the suite slot lives.

    Read-only helper - it creates nothing, so it is safe on the poll path.

    Args:
        root: The slot root, or None for the default.

    Returns:
        The slot's path.
    """
    return _resolve_root(root) / SLOT_NAME


def _read_payload(slot: Path) -> dict[str, Any]:
    """The slot's payload, or {} when it is missing, empty or half-written.

    Args:
        slot: The slot file.

    Returns:
        The decoded payload, or an empty mapping.
    """
    try:
        raw = slot.read_text(encoding="utf-8")
    except OSError:
        return {}
    if not raw.strip():
        return {}
    try:
        record = json.loads(raw)
    except ValueError:
        return {}
    return record if isinstance(record, dict) else {}


def slot_state(root: Any = None, now: Any = None) -> dict[str, Any]:
    """FREE, RUNNING or RECLAIMABLE for the suite slot. NEVER mutates anything.

    RECLAIMABLE means a slot file is present but its holder is provably gone. It
    is REPORTED, not acted on - clearing it is `try_acquire`'s job, for the
    reason in the module docstring.

    Args:
        root: The slot root, or None for the default.
        now: The wall clock reading to age the slot against. Injected so an
            ageing arm never has to sleep.

    Returns:
        The state, the holder it read, and the slot's age in seconds.
    """
    slot = slot_path(root)
    reading = time.time() if now is None else float(now)
    if not slot.exists():
        return {"state": FREE, "holder": None, "pid": None, "run_id": None, "age_s": None}

    record = _read_payload(slot)
    stamp = _float_or_none(record.get("ts"))
    if stamp is None:
        try:
            stamp = slot.stat().st_mtime
        except OSError:
            stamp = None
    pid = _int_or_none(record.get("pid"))
    answer: dict[str, Any] = {
        "state": RUNNING,
        "holder": _str_or_none(record.get("holder")),
        "pid": pid,
        "run_id": _str_or_none(record.get("run_id")),
        "age_s": None if stamp is None else max(0.0, reading - stamp),
    }
    lanes = _lanes()
    if pid is None:
        # No readable holder at all - see WRITE_GRACE_S.
        if answer["age_s"] is not None and answer["age_s"] > WRITE_GRACE_S:
            answer["state"] = RECLAIMABLE
    elif not lanes.pid_alive(pid):
        answer["state"] = RECLAIMABLE
    elif lanes.holder_is_a_stranger(pid, record.get("pid_started")):
        # Alive, but not the same process: the holder died and the operating
        # system reissued its pid. Without this the ration reads RUNNING forever.
        answer["state"] = RECLAIMABLE
    return answer


def _remove_quietly(path: Path) -> None:
    """Delete one file, reporting nothing. Used only on the slot."""
    with contextlib.suppress(OSError):
        path.unlink()


def _reclaim(root: Any) -> bool:
    """Clear a slot whose holder is provably gone. Never touches a live one.

    The state is re-read HERE rather than taken from the caller: between a
    caller's read and this call another waiter may have acquired, and clearing
    on a stale verdict is how two suites end up running.

    Args:
        root: The slot root.

    Returns:
        True when the slot is free afterwards.
    """
    slot = slot_path(root)
    if not slot.exists():
        return True
    if slot_state(root)["state"] != RECLAIMABLE:
        return False
    _remove_quietly(slot)
    return not slot.exists()


def _identity(record: dict[str, Any]) -> tuple[str | None, float | None, int | None]:
    """The triple that names one holder of the slot."""
    return (
        _str_or_none(record.get("run_id")),
        _float_or_none(record.get("ts")),
        _int_or_none(record.get("pid")),
    )


def _is_ours(slot: Path, record: dict[str, Any]) -> bool:
    """True when the slot's CURRENT payload is the identity we recorded.

    This is the ABA guard. If the slot was reclaimed and re-acquired after our
    token was issued, the payload has moved on and this answers False, so a late
    release cannot unlink the new holder's slot.

    Args:
        slot: The slot file.
        record: Its current payload.

    Returns:
        True when this process may act on the slot.
    """
    owned = _OWNED.get(_key(slot))
    identity = _identity(record)
    if owned is not None:
        return identity == owned
    return identity[2] == os.getpid()


def _refusal(state: dict[str, Any]) -> dict[str, Any]:
    """The answer a genuinely held ration gets. Writes nothing, by construction."""
    return {"ok": False, "refused": "suite_held", "holder": state["holder"], "pid": state["pid"]}


def try_acquire(*, holder: Any, run_id: Any, root: Any = None) -> dict[str, Any]:
    """Take the suite slot, or refuse. NEVER blocks - the waiting is the caller's.

    A holder whose pid is dead is reclaimed rather than respected: a killed
    driver must never wedge the ration behind a process that no longer exists. A
    holder that is genuinely live is refused, and the refusal touches nothing on
    disk - the state is read BEFORE any mkdir for exactly that reason.

    Args:
        holder: Who is taking it, for the log and for the ledger. A lane name is
            the intended value; nothing here requires one.
        run_id: The caller's identifier for this run.
        root: The slot root, or None for the default.

    Returns:
        `{"ok": True, "holder", "run_id", "token"}` on success - `token` is the
        slot path and is what `release` wants back - or
        `{"ok": False, "refused": "suite_held", "holder", "pid"}`, which is a
        normal answer rather than an error.
    """
    directory = _resolve_root(root)

    state = slot_state(directory)
    if state["state"] == RUNNING:
        return _refusal(state)
    if state["state"] == RECLAIMABLE:
        _reclaim(directory)

    payload: dict[str, Any] = {
        "pid": os.getpid(),
        "holder": str(holder),
        "run_id": str(run_id),
        "ts": time.time(),
        # The other half of the holder's identity, so a reissued pid cannot make
        # a dead holder read alive. See `lanes.holder_is_a_stranger`.
        "pid_started": _lanes().proc_started(os.getpid()),
    }
    token = _exclusive_create(directory, payload)
    if token is None:
        # Lost a race between the read above and the exclusive create.
        return _refusal(slot_state(directory))
    _OWNED[_key(token)] = (payload["run_id"], payload["ts"], payload["pid"])
    return {
        "ok": True,
        "holder": payload["holder"],
        "run_id": payload["run_id"],
        "token": str(token),
    }


def _exclusive_create(root: Any, payload: dict[str, Any]) -> Path | None:
    """Create the slot, or answer None because somebody else already holds it.

    `O_CREAT|O_EXCL` rather than tmp-plus-replace: EXCLUSIVITY IS THE RATION, and
    a replace cannot be exclusive. Same primitive and same reason as
    `lanes._exclusive_create`.

    Args:
        root: The slot root.
        payload: The holder record to write into the slot.

    Returns:
        The slot path, or None when it was already taken.
    """
    directory = Path(root)
    directory.mkdir(parents=True, exist_ok=True)
    slot = directory / SLOT_NAME
    try:
        handle = os.open(str(slot), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except OSError:
        return None
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            json.dump(payload, stream)
    except OSError:
        _remove_quietly(slot)
        return None
    return slot


def release(token: Any, root: Any = None) -> bool:
    """Give the slot back. Idempotent, and NEVER raises.

    A release runs in a `finally`, and a release that can throw turns one
    failure into two.

    Args:
        token: What `try_acquire` handed back.
        root: The slot root, used only when the token is a bare name.

    Returns:
        True when this call removed the slot.
    """
    if token is None or not str(token).strip():
        return False
    slot = Path(str(token).strip())
    if not slot.is_absolute():
        slot = _resolve_root(root) / slot.name
    key = _key(slot)
    if not slot.exists():
        _OWNED.pop(key, None)
        return False
    record = _read_payload(slot)
    if not record or not _is_ours(slot, record):
        # Half-written, corrupt, or somebody else's now - not provably ours.
        return False
    try:
        slot.unlink()
    except OSError:
        return False
    _OWNED.pop(key, None)
    return True


@contextmanager
def hold_suite_slot(
    *,
    holder: Any,
    run_id: Any,
    root: Any = None,
    ceiling_s: float | None = None,
    poll_s: float = DEFAULT_POLL_S,
    sleep: Callable[[float], Any] = time.sleep,
    monotonic: Callable[[], float] = time.monotonic,
    emit: Callable[[str], Any] = print,
) -> Iterator[dict[str, Any]]:
    """Hold the suite slot for the block, WAITING for it rather than refusing.

    A ration that refuses turns a slow night into a dead one, so a held slot is
    waited out. The sleeping happens in the calling process, which is the driver
    - see the module docstring on why that division is the rule rather than a
    convenience.

    A `ceiling_s` is a promise about how long the caller will wait, not a
    refusal: when it expires the block runs UNRATIONED and says so with the one
    marker a log reader can grep for. Nothing is taken or cleared on that path,
    because the holder is still there - a second writer in the same directory is
    exactly what a silent seizure would produce.

    Args:
        holder: Who is taking it. A lane name is the intended value.
        run_id: The caller's identifier for this run.
        root: The slot root, or None for the default.
        ceiling_s: Seconds to wait before proceeding unrationed, or None to wait
            for as long as it takes. None is the default so no number lives here
            that a caller already owns.
        poll_s: Seconds between attempts.
        sleep: The wait, injected so an arm never has to spend real time.
        monotonic: Deadline clock. NEVER wall time - a clock that steps backwards
            extends a wall-clock deadline by however far it moved.
        emit: The log sink. What makes the unrationed path findable at 3am.

    Yields:
        The claim `try_acquire` answered with, or the refusal that was overrun.
    """
    started = monotonic()
    claim = try_acquire(holder=holder, run_id=run_id, root=root)
    while not claim["ok"]:
        if ceiling_s is not None and monotonic() - started >= float(ceiling_s):
            emit(
                f"{UNRATIONED} suite - {holder} waited past {ceiling_s}s behind"
                f" pid {claim.get('pid')}; running the suite WITHOUT the ration"
            )
            yield claim
            return
        sleep(poll_s)
        claim = try_acquire(holder=holder, run_id=run_id, root=root)
    try:
        yield claim
    finally:
        release(claim["token"], root=root)
