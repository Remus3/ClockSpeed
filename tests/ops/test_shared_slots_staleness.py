#!/usr/bin/env python3
"""CS-1216 - the staleness verdicts of the vendored ``ops/loop/slots.py``, driven.

``tests/ops/test_shared_slots.py`` pins the vendored file's BYTES and promises
that it acquires nothing. This module is its behavioural sibling: it drives
``is_stale`` and ``reap`` against lockfiles in a pytest temporary directory, so
every arm here is a statement about what the shared protocol DOES, and none of
them goes anywhere near the real machine-wide bucket. No arm calls ``hold`` or
``try_acquire``, and every ``reap`` is handed a ``tmp_path`` root.

THE SHARED FILE IS C4 OF THE CARRIERS' JOINT ROUND (sha256 head ``290cbf80``),
adopted here from the carriers' published diffs and checked against the digest
two carriers stated from their own disks. C4 changed exactly one decision: a
READABLE record younger than ``stale_after * HARD_STALE_MULTIPLE`` is judged by
its holder's liveness, where the previous bytes reclaimed it on age alone past
``stale_after``. The arms below pin both sides of that ceiling.

THE CS-1216 ARM. The release fallback, when it cannot unlink, rewrites the lock
IN PLACE. A torn write leaves an unreadable record with a FRESH mtime, so
``is_stale`` takes its mtime branch and answers HELD until ``stale_after`` has
passed since the write. The previous docstring said the fallback "reports stale
too", read as at once; C4's says "not at once". The arm drives the truncated
record and pins the verdict the docstring now states, docstring and behaviour in
one assertion so the two cannot drift apart.

A FOREIGN LOCK IS REAPED BY THE SAME RULE AS AN OWN ONE. ``reap`` never consults
the ``repo`` field of the record it removes; it reads it only for the log line.
Two carriers measured that on their own copies and answered this tree's 1510
question YES. The arm here pins it on this tree's copy, with the liveness seam
rebound so no real process is ever probed.

Authority: CLAUDE.md non-negotiable 9 (the failing arm comes first) and section
3's rule that a vendored file is graded, never edited.
"""

from __future__ import annotations

import inspect
import json
import os
import time
from typing import TYPE_CHECKING, Final

from ops.loop import slots

if TYPE_CHECKING:
    from pathlib import Path

    import pytest

#: A stale_after small enough to reason about and large enough that a test
#: run never crosses it by accident.
STALE_AFTER: Final = 1000.0

#: Holder pids that are never probed for real - every arm that uses one rebinds
#: ``slots.pid_alive`` first, so the verdict never depends on what happens to be
#: running on the box.
LIVE_PID: Final = 4321
DEAD_PID: Final = 5678

#: A repo label that is no carrier's name, so the vendored-file census guard and
#: the channel's no-names rule are both untouched by this module.
FOREIGN_REPO: Final = "another-tree"

#: The phrase C4's release docstring uses for the mtime fallback's timing.
NOT_AT_ONCE: Final = "not at once"


def _write_record(path: Path, *, pid: int, age: float, repo: str = FOREIGN_REPO) -> float:
    """Write a readable lock record whose ``ts`` is ``age`` seconds old."""
    now = time.time()
    record = {"pid": pid, "repo": repo, "run_id": "r", "cycle": 0, "ts": now - age}
    path.write_text(json.dumps(record), encoding="utf-8")
    return now


def _liveness(monkeypatch: pytest.MonkeyPatch) -> None:
    """Rebind the liveness seam: LIVE_PID is alive, every other pid is dead."""
    monkeypatch.setattr(slots, "pid_alive", lambda pid: pid == LIVE_PID)


def test_a_live_holder_past_stale_after_but_below_the_ceiling_is_held(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """C4's change: age alone past stale_after no longer reclaims a live holder."""
    _liveness(monkeypatch)
    lock = tmp_path / "0.lock"
    now = _write_record(lock, pid=LIVE_PID, age=STALE_AFTER * 1.5)
    stale = slots.is_stale(lock, STALE_AFTER, now=now)
    assert stale is False


def test_a_live_holder_past_the_fail_open_ceiling_is_stale(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The ceiling stays: a reused pid must never hold the bucket forever."""
    _liveness(monkeypatch)
    lock = tmp_path / "0.lock"
    ceiling = STALE_AFTER * slots.HARD_STALE_MULTIPLE
    now = _write_record(lock, pid=LIVE_PID, age=ceiling + 1.0)
    stale = slots.is_stale(lock, STALE_AFTER, now=now)
    assert stale is True


def test_a_dead_holder_below_stale_after_is_stale(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _liveness(monkeypatch)
    lock = tmp_path / "0.lock"
    now = _write_record(lock, pid=DEAD_PID, age=1.0)
    stale = slots.is_stale(lock, STALE_AFTER, now=now)
    assert stale is True


def test_the_fail_open_ceiling_is_twice_stale_after() -> None:
    multiple = slots.HARD_STALE_MULTIPLE
    assert multiple == 2.0  # noqa: PLR2004 - the pinned protocol constant itself


def test_a_torn_in_place_write_reads_held_until_stale_after_as_the_release_docstring_states(
    tmp_path: Path,
) -> None:
    """CS-1216: a truncated record with a fresh mtime is HELD, and the docstring says so.

    The positive control is the same truncated record with its mtime pushed
    past stale_after: the mtime branch then answers stale. Without it, an arm
    that only ever saw False could be grading a branch that never runs.
    """
    lock = tmp_path / "0.lock"
    lock.write_bytes(b'{"pid": 12, "ts"')
    fresh = slots.is_stale(lock, STALE_AFTER)

    old = time.time() - STALE_AFTER - 60.0
    os.utime(lock, (old, old))
    aged = slots.is_stale(lock, STALE_AFTER)

    doc = inspect.getdoc(slots.release) or ""
    states_delay = NOT_AT_ONCE in " ".join(doc.split())
    assert (fresh, aged, states_delay) == (False, True, True)


def test_reap_removes_a_dead_foreign_lock_and_keeps_a_live_one(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A reap judges a lock by is_stale alone; the repo field is never a condition."""
    _liveness(monkeypatch)
    dead = tmp_path / "0.lock"
    live = tmp_path / "1.lock"
    _write_record(dead, pid=DEAD_PID, age=1.0)
    _write_record(live, pid=LIVE_PID, age=STALE_AFTER * 1.5)
    lines: list[str] = []
    removed = slots.reap(tmp_path, 2, STALE_AFTER, log=lines.append)
    survivors = sorted(p.name for p in tmp_path.iterdir())
    logged_foreign = sum(1 for line in lines if FOREIGN_REPO in line)
    assert (removed, survivors, logged_foreign) == (1, ["1.lock"], 1)
