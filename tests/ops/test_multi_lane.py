#!/usr/bin/env python3
"""CS-992 - the roster carries more than one lane, and every guard is per-LANE.

WHAT THIS GRADES. Two guards stand between a fire and a running worker, and
before this item BOTH were per-BOX rather than per-LANE: ``ops/loop/lanes.py``
resolved one lock slot whatever lane asked for it, and ``ops/loop/queue_loop.py``
held one named mutex whose name was a CONSTANT. A second lane could not start at
all, and the failure was silent in the shape that matters - a real exit code over
no work done.

THE TWO DEFECT SHAPES THIS FILE IS BUILT TO CATCH, because they are opposites and
an arm that catches one is usually blind to the other:

  * COLLAPSE - the derivation ignores the lane and every lane lands on one name
    or one slot. Two lanes then serialise on one object while each believes it
    holds its own, which is strictly worse than the single-lane roster it
    replaced. Caught by the arms that drive two DISTINCT lanes to acquisition
    together, and by the specificity half of the same-lane exclusion arm.
  * DEGENERACY THE OTHER WAY - the derivation mixes in something that is not the
    lane (a pid, a clock reading, a uuid), so every caller gets a fresh name and
    NOTHING is excluded any more. A same-lane arm alone would still pass a
    derivation that collapsed; a distinct-lane arm alone would still pass one
    that never excludes. Caught by the exclusion arm and by the stability half
    of the concurrency arm.

NO ARM HERE TAKES A REAL OS MUTEX, and it is structural rather than promised: the
stand-in below is installed by an AUTOUSE fixture, so no test in this module can
reach the Win32 namespace even by accident. The sibling project this substrate
came from shipped arms that took its real driver mutex, and they went red exactly
when a lane was running - the one time a suite must not.

WHY A STAND-IN IS THE RIGHT ORACLE HERE AND NOT A WEAKENING. A Windows named
mutex is RE-ENTRANT for the thread that owns it, so a second acquire inside ONE
process succeeds whatever the name is. An in-process arm over the real primitive
therefore cannot observe exclusion at all, and would pass just as happily for a
derivation that collapsed every lane onto one name - an oracle blind to its own
subject. Cross-process exclusion is ``ops/loop/winmutex.py``'s subject and is
pinned there by digest; what is under test HERE is the NAME the driver asks for,
and the stand-in observes exactly that.

ASSERTIONS ARE MADE ON SCALARS BOUND FIRST. Every arm works under ``tmp_path``,
and pytest renders an asserted expression's sub-expressions with their own reprs
regardless of the message (CS-850), so a ``Path`` left inside an assertion would
print a temporary directory into the failure report.
"""

from __future__ import annotations

import itertools
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Final

import pytest

ROOT: Final = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# A PLAIN IMPORT, never importorskip: a missing driver must be a COLLECTION
# error rather than a quiet skip, and the package route is the one production
# uses, so this suite holds the same module objects the driver does.
from ops.loop import lanes, queue_loop  # noqa: E402

#: The real exception the driver catches, taken from the module the driver
#: itself resolves. The stand-in raises THIS class rather than a look-alike,
#: which is what makes the refusal path the same one `main` handles.
MutexTimeout: Final = queue_loop.winmutex.MutexTimeout

RUN_ID: Final = "cs992a"
OTHER_RUN_ID: Final = "cs992b"

#: EVERY distinct ordered-free pair on the roster, not the first one. A pair
#: chosen by index grades one member of the population and leaves the rest
#: unmeasured, which is the pooled-guard shape.
LANE_PAIRS: Final = list(itertools.combinations(lanes.LANES, 2))

#: The roster as a list, for parametrize.
LANE_LIST: Final = list(lanes.LANES)


class NameKeyedMutexes:
    """The Win32 named-mutex namespace, modelled as exclusion BY NAME.

    Holding a name twice raises the driver's own ``MutexTimeout``; holding two
    different names succeeds. That is the whole of what a named mutex gives the
    driver across processes, and it is the property the NAME derivation has to
    earn.
    """

    def __init__(self) -> None:
        """Start with nothing held and nothing asked for."""
        self.held: set[str] = set()
        self.asked: list[str] = []

    @contextmanager
    def hold(self, name: str, *, timeout: float | None = None, log: Any = None) -> Iterator[str]:
        """Hold one name, or refuse because it is already held.

        Args:
            name: The mutex name the caller derived.
            timeout: Accepted and ignored - the stand-in never waits, so a
                refusal is immediate whatever the caller asked for. Named so
                the signature matches the real ``winmutex.hold``.
            log: Accepted and ignored, for the same reason.

        Yields:
            The name, while it is held.

        Raises:
            MutexTimeout: The name is already held.
        """
        del timeout, log
        self.asked.append(name)
        if name in self.held:
            message = f"{name} is held"
            raise MutexTimeout(message)
        self.held.add(name)
        try:
            yield name
        finally:
            self.held.discard(name)


@pytest.fixture
def mutexes(monkeypatch: pytest.MonkeyPatch) -> NameKeyedMutexes:
    """Install the stand-in namespace in place of the driver's winmutex seam.

    AUTOUSE through ``_no_real_mutex`` below, so this is not a courtesy a test
    may forget to ask for.

    Args:
        monkeypatch: pytest's patcher, which restores the real module at
            teardown.

    Returns:
        The registry every arm in this module measures.
    """
    registry = NameKeyedMutexes()
    monkeypatch.setattr(
        queue_loop,
        "winmutex",
        SimpleNamespace(hold=registry.hold, MutexTimeout=MutexTimeout),
    )
    return registry


@pytest.fixture(autouse=True)
def _no_real_mutex(mutexes: NameKeyedMutexes) -> NameKeyedMutexes:
    """Every arm in this module runs with the stand-in installed.

    Args:
        mutexes: The registry fixture, requested so the patch is in force for
            every test here whether the test names it or not.

    Returns:
        The same registry.
    """
    return mutexes


def _claim(lane: str, root: Path, worktree: Path, run_id: str = RUN_ID) -> dict[str, Any]:
    """Claim one lane in a tmp_path lock root.

    Args:
        lane: The lane to claim.
        root: The lock root.
        worktree: The working directory the lane would run in.
        run_id: The caller's identifier.

    Returns:
        What ``try_acquire_lane`` answered.
    """
    answer: dict[str, Any] = lanes.try_acquire_lane(
        lane, run_id=run_id, worktree=worktree, root=root
    )
    return answer


# ===========================================================================
# a. The controls - a probe that cannot fail proves nothing about its subject
# ===========================================================================


def test_the_stand_in_namespace_can_observe_both_outcomes(
    mutexes: NameKeyedMutexes,
) -> None:
    """THE CONTROL for every mutex arm below, measured on literal names.

    No derivation is involved: two different names are admitted together and a
    repeated name is refused. If this arm ever passes vacuously, so does every
    arm that trusts the registry.
    """
    with mutexes.hold("cs992-control-a"), mutexes.hold("cs992-control-b"):
        admitted = len(mutexes.held)
        refused = False
        try:
            with mutexes.hold("cs992-control-a"):
                pass
        except MutexTimeout:
            refused = True
    assert (admitted, refused, len(mutexes.held)) == (2, True, 0)


def test_the_driver_reaches_the_stand_in_and_never_the_real_namespace() -> None:
    """The autouse patch is in force, so no arm here can take an OS handle."""
    seam = queue_loop.winmutex
    patched = isinstance(seam, SimpleNamespace)
    same_error = seam.MutexTimeout is MutexTimeout
    assert (patched, same_error) == (True, True)


def test_the_driver_asks_for_the_derived_name_and_never_for_another(
    mutexes: NameKeyedMutexes,
) -> None:
    """A RECORDING SPY, because an outcome alone cannot see WHICH name was used.

    Every other mutex arm here reads a verdict - admitted, or refused. A verdict
    is satisfied by any name that happens to behave right, so it cannot tell the
    driver's own guard apart from one that consulted something else. This reads
    the name off the namespace as it was asked for.
    """
    for lane in LANE_LIST:
        with queue_loop._driver_singleton(lane):  # noqa: SLF001 - the subject
            pass
    expected = [queue_loop.driver_mutex(lane) for lane in LANE_LIST]
    assert mutexes.asked == expected


def test_the_concurrency_arms_grade_a_non_empty_population_of_pairs() -> None:
    """An EMPTY parametrize reports a skip, and a skip reads as green.

    The pair population is the thing acceptance 1 rests on: a roster that could
    not offer a distinct pair would leave the concurrency arm collecting
    nothing at all while the suite stayed green. So the population is asserted
    by EQUALITY against the combinatorial count, and its non-emptiness is
    asserted beside it - never as a floor over the roster's size.
    """
    counted = len(LANE_PAIRS)
    combinatorial = len(LANE_LIST) * (len(LANE_LIST) - 1) // 2
    distinct_roster = len(set(LANE_LIST)) == len(LANE_LIST)
    assert (counted, counted > 0, distinct_roster) == (combinatorial, True, True)


# ===========================================================================
# b. ACCEPTANCE 3 - two DISTINCT lanes reach acquisition together
# ===========================================================================


@pytest.mark.parametrize(("first", "second"), LANE_PAIRS)
def test_two_distinct_lanes_reach_acquisition_together(
    first: str, second: str, tmp_path: Path, mutexes: NameKeyedMutexes
) -> None:
    """Both guards, in one arm, because a lane needs BOTH to start.

    The lock half proves the slot path varies by lane - a per-lane mutex over
    one shared slot file is not a lock, it is two lanes serialising on a file
    while their mutexes wave them both through. The mutex half proves the name
    varies by lane. The stability half proves the name is a function of the
    LANE and nothing else: a derivation mixing in a pid or a clock reading
    would admit both lanes here while excluding nobody anywhere.
    """
    root = tmp_path / "locks"
    claimed = (
        bool(_claim(first, root, tmp_path / "wt-a").get("ok")),
        bool(_claim(second, root, tmp_path / "wt-b", OTHER_RUN_ID).get("ok")),
    )
    # SLF001: `_driver_singleton` IS the subject - the driver's own guard, with
    # the stand-in underneath it. Reaching it through anything else would grade
    # a re-implementation of the thing under test.
    with (
        queue_loop._driver_singleton(first),  # noqa: SLF001
        queue_loop._driver_singleton(second),  # noqa: SLF001
    ):
        held = len(mutexes.held)
    stable = queue_loop.driver_mutex(first) == queue_loop.driver_mutex(first)
    assert (claimed, held, stable) == ((True, True), len({first, second}), True)


# ===========================================================================
# c. ACCEPTANCE 4 - two drivers on ONE lane still exclude
# ===========================================================================


@pytest.mark.parametrize("lane", LANE_LIST)
def test_two_drivers_on_one_lane_still_exclude(
    lane: str, tmp_path: Path, mutexes: NameKeyedMutexes
) -> None:
    """Exclusion, AND the name it excluded on being this lane's alone.

    The second half is what makes this arm sensitive to a collapsed derivation.
    Exclusion by itself survives a collapse - one name for every lane excludes
    perfectly well, it just excludes the wrong things - so the arm also asserts
    that no OTHER lane on the roster shares the name this refusal keyed on.
    """
    root = tmp_path / "locks"
    first = _claim(lane, root, tmp_path / "wt-a")
    second = _claim(lane, root, tmp_path / "wt-b", OTHER_RUN_ID)
    refused = False
    with queue_loop._driver_singleton(lane):  # noqa: SLF001 - see the arm above
        held_by_the_first = len(mutexes.held)
        try:
            with queue_loop._driver_singleton(lane):  # noqa: SLF001 - same
                pass
        except MutexTimeout:
            refused = True
    mine = queue_loop.driver_mutex(lane)
    shared = sorted(
        other for other in LANE_LIST if other != lane and queue_loop.driver_mutex(other) == mine
    )
    verdict = (bool(first.get("ok")), second.get("refused"), refused, held_by_the_first, shared)
    assert verdict == (True, "lane_held", True, 1, [])


# ===========================================================================
# d. The slot path, which is the half a per-lane mutex cannot cover
# ===========================================================================


def test_every_lane_gets_its_own_slot_file(tmp_path: Path) -> None:
    """The population is graded by set EQUALITY against a second enumeration.

    One side is the DERIVATION - what ``lock_path`` says each lane's slot is.
    The other is the FILESYSTEM after a real acquire sweep, which shares no
    constant with it and is produced by behaviour rather than by arithmetic. A
    collapse makes the disk side one entry short; a floor over either side
    would have graded the bottom of the range and seen neither.
    """
    root = tmp_path / "locks"
    claimed = [
        bool(_claim(lane, root, tmp_path / f"wt{index}", f"{RUN_ID}{index}").get("ok"))
        for index, lane in enumerate(LANE_LIST)
    ]
    on_disk = sorted(path.name for path in root.iterdir())
    derived = sorted(lanes.lock_path(root=root, lane=lane).name for lane in LANE_LIST)
    all_claimed = claimed == [True] * len(LANE_LIST)
    assert (on_disk, len(set(on_disk)), all_claimed) == (derived, len(LANE_LIST), True)


def test_a_lane_off_the_roster_has_no_slot_and_no_claim(tmp_path: Path) -> None:
    """An unknown lane is refused by BOTH halves rather than given slot zero.

    A derivation that answered a default slot for an unrecognised lane would
    hand a typo the queue lane's own lock.
    """
    with pytest.raises(ValueError, match="unknown lane"):
        lanes.try_acquire_lane("not-a-lane", run_id=RUN_ID, worktree=tmp_path / "wt", root=tmp_path)
    with pytest.raises(ValueError, match="unknown lane"):
        lanes.lock_path(root=tmp_path, lane="not-a-lane")


# ===========================================================================
# e. The mutex name is machine-wide, so it is scoped to THIS checkout
# ===========================================================================


def test_the_mutex_name_is_scoped_to_this_checkout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A named mutex is an OS-GLOBAL object and this box runs sibling projects.

    Two checkouts of this repository must not serialise against each other, so
    the repository identity is part of the name. Measured by moving the
    identity and watching the name move with it.
    """
    lane = LANE_LIST[0]
    here = queue_loop.driver_mutex(lane)
    monkeypatch.setattr(lanes, "REPO_ROOT", tmp_path / "another-checkout")
    elsewhere = queue_loop.driver_mutex(lane)
    assert (here != elsewhere, here.startswith("Global\\")) == (True, True)


def test_the_mutex_name_spells_no_path_and_no_separator() -> None:
    r"""A path in the name would be a path in a machine-wide OS object.

    A checkout under a home directory would put the Windows account name into a
    name any process on the box can enumerate, which non-negotiable 3 forbids.
    The identity is therefore a digest, and the name past the ``Global\\``
    namespace prefix carries no separator of either kind.
    """
    body = queue_loop.driver_mutex(LANE_LIST[0]).split("\\", 1)[1]
    carries = ("\\" in body, "/" in body, ":" in body)
    root_spelled = str(lanes.REPO_ROOT) in body
    assert (carries, root_spelled) == ((False, False, False), False)


def test_distinct_lanes_never_collide_after_the_name_is_sanitised() -> None:
    """Sanitising a lane for an OS name is itself a collapse risk.

    Folding every character a mutex name may not carry into one replacement
    maps two distinct lanes onto one name, which is the defect this item exists
    to remove arriving by the back door. Graded by cardinality EQUALITY over a
    population that deliberately includes a pair differing only in a character
    a sanitiser would fold.
    """
    population = [*LANE_LIST, "cs992-x", "cs992_x", "cs992 x"]
    names = {queue_loop.driver_mutex(lane) for lane in population}
    assert len(names) == len(set(population))


# ===========================================================================
# f. The ledger mutex stays lane-INDEPENDENT, deliberately
# ===========================================================================


def test_the_ledger_mutex_is_lane_independent_and_never_a_driver_name() -> None:
    """ONE ledger file, so ONE name - the opposite ruling to the driver's.

    Every lane's driver appends to the same ``queue_loop.jsonl``. A per-lane
    ledger name would let two lanes append at once, which is precisely the two
    half-lines interleaved into an unparseable row the mutex exists to prevent.
    So the ledger name stays a single constant, and no lane's driver name may
    collide with it - a collision would put the whole night's ledger under the
    name one driver holds for its entire run.
    """
    names = {queue_loop.driver_mutex(lane) for lane in LANE_LIST}
    collided = sorted(name for name in names if name == queue_loop.LEDGER_MUTEX)
    is_one_name = isinstance(queue_loop.LEDGER_MUTEX, str)
    assert (collided, is_one_name) == ([], True)
