"""CS-1203 - the world provider parses a given save at most once.

THE DEFECT. ``SaveWorldProvider.world()`` resolved, copied and parsed the newest
save on EVERY call. ``/api/health`` calls it on every request, so on a world
whose parse outlasts the companion's per-probe timeout every probe aborted and
the companion reported that the dashboard never answered.

WHAT IS GRADED, all through the provider's injectable ``find_save`` and
``load`` seams with NO real save and NO game install. The "save" each arm
resolves is a few synthetic bytes in ``tmp_path``, there only so the default
identity read has a real file to stat; no arm parses anything.

a. An unchanged identity - path, size, modification time - loads ONCE.
b. A changed size, a changed modification time and a changed newest path each
   load again.
c. Concurrent callers share ONE in-flight load rather than each starting one.
d. A failed load answers None, is not remembered as a success, and a later call
   retries it; a failed re-read never serves the previous world as current.
e. An identity that cannot be read falls back to the old per-call load.

EVERY ASSERTION IS ON A COUNT OR A BOOLEAN. A rendered assertion must never
carry a path, and a ``tmp_path`` lives under a home directory.
"""

from __future__ import annotations

import os
import threading
import time
from typing import TYPE_CHECKING, Final

from clockspeed.save.world import STAGE_COPY, WorldLoadError
from clockspeed.surface import providers

if TYPE_CHECKING:
    from pathlib import Path

#: How many callers the concurrency arm releases at once.
CALLERS: Final = 8

#: How long the fake load holds the in-flight parse open, in seconds. Long
#: enough that every released caller arrives while it is still running.
SLOW_LOAD_SECONDS: Final = 0.3

#: The load count of an arm that expects exactly one re-read after a first load.
TWO_LOADS: Final = 2

#: A fixed modification time, in nanoseconds, so identity changes are chosen by
#: the arm rather than by the filesystem clock's resolution.
FIXED_MTIME_NS: Final = 1_700_000_000_000_000_000

#: A second modification time, distinct from the first.
LATER_MTIME_NS: Final = 1_700_000_001_000_000_000


class CountingLoad:
    """A fake ``load`` that records each call and hands back a fresh world."""

    def __init__(self, *, delay: float = 0.0) -> None:
        """Start with no calls.

        Args:
            delay: Seconds each call holds before answering.
        """
        self.calls = 0
        self._delay = delay
        self._guard = threading.Lock()

    def __call__(self, _path: Path) -> object:
        """Count the call and answer a new sentinel world."""
        with self._guard:
            self.calls += 1
        if self._delay:
            time.sleep(self._delay)
        return object()


def plant(path: Path, payload: bytes, mtime_ns: int = FIXED_MTIME_NS) -> Path:
    """Write synthetic bytes and pin the modification time.

    Args:
        path: Where to write.
        payload: The bytes; their length is the size half of the identity.
        mtime_ns: The modification time to pin.

    Returns:
        The same path.
    """
    path.write_bytes(payload)
    os.utime(path, ns=(mtime_ns, mtime_ns))
    return path


def provider_for(save: Path, load: object) -> providers.SaveWorldProvider:
    """A provider whose newest save is always ``save``."""
    return providers.SaveWorldProvider(
        find_save=lambda _dir: save,
        load=load,  # type: ignore[arg-type]
    )


# ---------------------------------------------------------------------------
# (a) one load per unchanged identity
# ---------------------------------------------------------------------------


def test_repeated_calls_on_an_unchanged_save_load_it_once(tmp_path: Path) -> None:
    save = plant(tmp_path / "synthetic.sav", b"alpha")
    load = CountingLoad()
    provider = provider_for(save, load)
    first = provider.world()
    second = provider.world()
    third = provider.world()
    loads = load.calls
    assert loads == 1, "an unchanged save was loaded more than once"
    same = first is second and second is third
    assert same, "repeated calls did not hand up the one remembered world"
    present = first is not None
    assert present, "the remembered world was absent"


# ---------------------------------------------------------------------------
# (b) a changed identity re-reads
# ---------------------------------------------------------------------------


def test_a_changed_size_re_reads(tmp_path: Path) -> None:
    save = plant(tmp_path / "synthetic.sav", b"alpha")
    load = CountingLoad()
    provider = provider_for(save, load)
    before = provider.world()
    plant(save, b"alpha-and-more")
    after = provider.world()
    loads = load.calls
    assert loads == TWO_LOADS, "a save whose size changed was not re-read"
    fresh = after is not before
    assert fresh, "a changed save handed up the previous world"


def test_a_changed_modification_time_re_reads(tmp_path: Path) -> None:
    save = plant(tmp_path / "synthetic.sav", b"alpha")
    load = CountingLoad()
    provider = provider_for(save, load)
    before = provider.world()
    plant(save, b"alpha", mtime_ns=LATER_MTIME_NS)
    after = provider.world()
    loads = load.calls
    assert loads == TWO_LOADS, "a save whose modification time changed was not re-read"
    fresh = after is not before
    assert fresh, "a changed save handed up the previous world"


def test_a_changed_newest_path_re_reads(tmp_path: Path) -> None:
    older = plant(tmp_path / "older.sav", b"alpha")
    newer = plant(tmp_path / "newer.sav", b"alpha")
    newest = [older]
    load = CountingLoad()
    provider = providers.SaveWorldProvider(
        find_save=lambda _dir: newest[0],
        load=load,  # type: ignore[arg-type]
    )
    before = provider.world()
    newest[0] = newer
    after = provider.world()
    again = provider.world()
    loads = load.calls
    assert loads == TWO_LOADS, "a new newest save of the same size and time was not read once"
    fresh = after is not before
    assert fresh, "a new newest save handed up the previous world"
    kept = again is after
    assert kept, "the new newest save was not remembered"


# ---------------------------------------------------------------------------
# (c) concurrent callers share one in-flight load
# ---------------------------------------------------------------------------


def test_concurrent_callers_share_one_load(tmp_path: Path) -> None:
    save = plant(tmp_path / "synthetic.sav", b"alpha")
    load = CountingLoad(delay=SLOW_LOAD_SECONDS)
    provider = provider_for(save, load)
    barrier = threading.Barrier(CALLERS)
    results: list[object] = []
    results_guard = threading.Lock()

    def call() -> None:
        barrier.wait()
        world = provider.world()
        with results_guard:
            results.append(world)

    threads = [threading.Thread(target=call) for _ in range(CALLERS)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    loads = load.calls
    assert loads == 1, "concurrent callers each started their own load"
    answered = len(results)
    assert answered == CALLERS, "a concurrent caller never answered"
    distinct = len({id(world) for world in results})
    assert distinct == 1, "concurrent callers were handed different worlds"
    absent = sum(1 for world in results if world is None)
    assert absent == 0, "a concurrent caller was handed no world"


# ---------------------------------------------------------------------------
# (d) a failed load is not remembered as a success
# ---------------------------------------------------------------------------


class FlakyLoad:
    """A fake ``load`` that refuses a chosen number of times, then answers."""

    def __init__(self, refusals: int) -> None:
        """Start with ``refusals`` refusals owed.

        Args:
            refusals: How many leading calls raise.
        """
        self.calls = 0
        self._refusals = refusals

    def __call__(self, _path: Path) -> object:
        """Refuse while refusals are owed, then answer a new sentinel world."""
        self.calls += 1
        if self._refusals:
            self._refusals -= 1
            raise OSError
        return object()


def test_a_failed_load_answers_none_and_a_later_call_retries(tmp_path: Path) -> None:
    save = plant(tmp_path / "synthetic.sav", b"alpha")
    load = FlakyLoad(refusals=1)
    provider = provider_for(save, load)
    failed = provider.world()
    recovered = provider.world()
    remembered = provider.world()
    was_none = failed is None
    assert was_none, "a refused load did not report the world absent"
    now_present = recovered is not None
    assert now_present, "the retry after a refused load did not hand up the world"
    loads = load.calls
    assert loads == TWO_LOADS, "a refused load was remembered, or a success was not"
    kept = remembered is recovered
    assert kept, "the world loaded on retry was not remembered"


def test_a_failed_re_read_never_serves_the_previous_world(tmp_path: Path) -> None:
    save = plant(tmp_path / "synthetic.sav", b"alpha")
    outcomes: list[bool] = [True, False]
    calls = [0]

    def load(_path: Path) -> object:
        calls[0] += 1
        if outcomes.pop(0):
            return object()
        raise ValueError

    provider = provider_for(save, load)
    first = provider.world()
    plant(save, b"alpha-rewritten")
    second = provider.world()
    loaded = first is not None
    assert loaded, "the first load did not hand up a world"
    stale = second is not None
    assert not stale, "a save that no longer parses served the previous world as current"
    count = calls[0]
    assert count == TWO_LOADS


def test_the_failure_control_every_documented_refusal_answers_none(tmp_path: Path) -> None:
    """THE CONTROL: memoizing kept the None-on-refusal contract for all three."""
    save = plant(tmp_path / "synthetic.sav", b"alpha")
    refusals: tuple[Exception, ...] = (
        WorldLoadError(STAGE_COPY, "OSError"),
        OSError(),
        ValueError(),
    )
    answered_none = 0
    for refusal in refusals:

        def refusing(_path: Path, refusal: Exception = refusal) -> object:
            raise refusal

        if provider_for(save, refusing).world() is None:
            answered_none += 1
    assert answered_none == len(refusals), "a documented refusal escaped the provider"


# ---------------------------------------------------------------------------
# (e) an unreadable identity keeps the old per-call behaviour
# ---------------------------------------------------------------------------


def test_an_unreadable_identity_falls_back_to_a_per_call_load(tmp_path: Path) -> None:
    vanished = tmp_path / "never-written.sav"
    load = CountingLoad()
    provider = provider_for(vanished, load)
    first = provider.world()
    second = provider.world()
    loads = load.calls
    assert loads == TWO_LOADS, "a save with no readable identity was remembered"
    both = first is not None and second is not None
    assert both, "an unreadable identity stopped the loader's answer reaching the caller"


def test_no_save_at_all_never_loads() -> None:
    load = CountingLoad()
    provider = providers.SaveWorldProvider(
        find_save=lambda _dir: None,
        load=load,  # type: ignore[arg-type]
    )
    absent = provider.world() is None
    assert absent
    loads = load.calls
    assert loads == 0, "a machine with no save reached the loader"
