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

A PREMISE THIS FILE ONCE STATED IS FALSE, AND THE CORRECTION IS THE REASON THE
REAL-PRIMITIVE ARM EXISTS. It said a Windows named mutex is re-entrant "for the
thread that owns it" and concluded that an in-process arm could not observe
exclusion at all. Ownership is per-THREAD, so the conclusion does not follow:
a SECOND THREAD in the same process observes exclusion exactly. Measured against
the shipped ``ops/loop/winmutex.py`` on this box:

    same thread, nested, one name      -> ACQUIRED  (the only true half)
    another thread, the same name      -> REFUSED   (real exclusion, in-process)
    another thread, a different name   -> ACQUIRED  (the control)

So the same-thread nesting the stand-in arms use is a statement about the MODEL
and not about Win32 - the stand-in is STRICTER than the primitive - and
``test_the_real_named_mutex_excludes_a_second_thread`` grades the primitive
itself on two threads. It takes a mutex whose lane token is unique to the run,
never a production lane's name, so it cannot go red because a real lane happens
to be running - which is the failure the sibling project shipped.

WHAT THE STAND-IN IS STILL FOR, stated as a boundary. It runs on every platform
and it records the NAME each guard asked for, which is what makes a collapsed or
degenerate derivation visible. THE GAP IT CANNOT SEE IS RECORDED RATHER THAN
IMPLIED: ``winmutex.hold`` has three fail-open branches that yield None and
serialise NOTHING - off win32, on a failed CreateMutexW, and on an unexpected
wait result - and the stand-in has none of them, so on a non-win32 CI leg every
``_driver_singleton`` excludes nothing while every arm here still passes.
``test_the_fail_open_branch_is_loud_rather_than_silent`` forces that branch and
asserts the marker reaches the driver's own log sink, so the occasion is visible
in the run log even though no arm can make it a failure.

ASSERTIONS ARE MADE ON SCALARS BOUND FIRST. Every arm works under ``tmp_path``,
and pytest renders an asserted expression's sub-expressions with their own reprs
regardless of the message (CS-850), so a ``Path`` left inside an assertion would
print a temporary directory into the failure report.
"""

from __future__ import annotations

import itertools
import json
import os
import subprocess
import sys
import threading
import uuid
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
from ops.fleet_kit import fleet_lanes  # noqa: E402
from ops.loop import lane_launcher, lanes, queue_loop, winmutex  # noqa: E402

#: The real exception the driver catches, taken from the module the driver
#: itself resolves. The stand-in raises THIS class rather than a look-alike,
#: which is what makes the refusal path the same one `main` handles.
MutexTimeout: Final = queue_loop.winmutex.MutexTimeout

#: The driver's own source, read once - the fail-open arm asks whether the
#: driver passes a log sink, which is a property of the call site rather than
#: of any value it returns.
DRIVER_SOURCE: Final = (ROOT / "ops" / "loop" / "queue_loop.py").read_text(encoding="utf-8")

#: Both run-length guards a driver takes: per lane and checkout, then
#: box-wide over the working directory.
TWO_GUARDS: Final = 2

#: A bounded join, so a wedged thread fails the arm instead of the session.
THREAD_JOIN_S: Final = 10.0

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
    tmp_path: Path, mutexes: NameKeyedMutexes
) -> None:
    """A RECORDING SPY, because an outcome alone cannot see WHICH name was used.

    Every other mutex arm here reads a verdict - admitted, or refused. A verdict
    is satisfied by any name that happens to behave right, so it cannot tell the
    driver's own guard apart from one that consulted something else. This reads
    the name off the namespace as it was asked for.
    """
    trees = {lane: tmp_path / f"cs-lane-{lane}" for lane in LANE_LIST}
    for lane in LANE_LIST:
        with queue_loop._driver_singleton(lane, trees[lane]):  # noqa: SLF001 - the subject
            pass
    expected = [
        name
        for lane in LANE_LIST
        for name in (queue_loop.driver_mutex(lane), queue_loop.worktree_mutex(trees[lane]))
    ]
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
        queue_loop._driver_singleton(first, tmp_path / f"cs-lane-{first}"),  # noqa: SLF001
        queue_loop._driver_singleton(second, tmp_path / f"cs-lane-{second}"),  # noqa: SLF001
    ):
        held = len(mutexes.held)
    stable = queue_loop.driver_mutex(first) == queue_loop.driver_mutex(first)
    assert (claimed, held, stable) == ((True, True), TWO_GUARDS * len({first, second}), True)


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
    tree = tmp_path / f"cs-lane-{lane}"
    with queue_loop._driver_singleton(lane, tree):  # noqa: SLF001 - see the arm above
        held_by_the_first = len(mutexes.held)
        try:
            with queue_loop._driver_singleton(lane, tree):  # noqa: SLF001 - same
                pass
        except MutexTimeout:
            refused = True
    mine = queue_loop.driver_mutex(lane)
    shared = sorted(
        other for other in LANE_LIST if other != lane and queue_loop.driver_mutex(other) == mine
    )
    verdict = (bool(first.get("ok")), second.get("refused"), refused, held_by_the_first, shared)
    assert verdict == (True, "lane_held", True, TWO_GUARDS, [])


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


# ===========================================================================
# g. The REAL primitive, on two threads - the model is not the subject
# ===========================================================================


def test_the_real_named_mutex_excludes_a_second_thread() -> None:
    """Exclusion measured on ``winmutex.hold`` itself, with both controls.

    THE STAND-IN IS NOT THE SUBJECT HERE, and this arm is what keeps the rest of
    this file honest: it takes the REAL machine-wide object, on two threads in
    one process, and reads all three outcomes. The name comes from the shipped
    derivation but from a lane token unique to this run, so the arm can never
    collide with a lane that is actually running on this box.

    OFF WIN32 THIS IS A SKIP AND THE SKIP IS THE POINT. ``winmutex`` yields
    unheld there and says so with its own marker; pretending to measure
    exclusion on a platform that has none is how a green leg comes to mean
    nothing. The forced-fail-open arm below runs on every platform and grades
    that behaviour directly.
    """
    if sys.platform != "win32":
        pytest.skip("no named-mutex namespace off win32 - see the fail-open arm below")
    name = queue_loop.driver_mutex(f"cs992-arm-{uuid.uuid4().hex[:8]}")
    other = queue_loop.driver_mutex(f"cs992-arm-{uuid.uuid4().hex[:8]}")
    outcomes: dict[str, str] = {}

    def take(key: str, wanted: str) -> None:
        """Try to hold one name on THIS thread and record what happened."""
        try:
            with winmutex.hold(wanted, timeout=0.0):
                outcomes[key] = "ACQUIRED"
        except winmutex.MutexTimeout:
            outcomes[key] = "REFUSED"

    with winmutex.hold(name, timeout=0.0):
        take("same_thread_nested", name)
        for key, wanted in (("other_thread_same", name), ("other_thread_other", other)):
            worker = threading.Thread(target=take, args=(key, wanted))
            worker.start()
            worker.join(timeout=THREAD_JOIN_S)
    measured = (
        outcomes.get("same_thread_nested"),
        outcomes.get("other_thread_same"),
        outcomes.get("other_thread_other"),
    )
    assert measured == ("ACQUIRED", "REFUSED", "ACQUIRED")


def test_the_fail_open_branch_is_loud_rather_than_silent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The recorded gap: three branches in ``hold`` serialise NOTHING.

    None of them can be made a failure here - a driver that cannot take a mutex
    must run rather than wedge, which is the shipped ruling. What CAN be graded
    is that the occasion is not silent: the branch emits the one UNSERIALIZED
    marker, and the driver passes a log sink so that marker reaches the run log.
    The platform branch is forced rather than waited for, so this runs and means
    the same thing on every leg.
    """
    lines: list[str] = []
    monkeypatch.setattr(winmutex.sys, "platform", "definitely-not-win32")
    with winmutex.hold("cs992-forced-fail-open", timeout=0.0, log=lines.append) as handle:
        unheld = handle is None
    marked = [line for line in lines if "UNSERIALIZED" in line]
    # The driver's own sink, read off the source rather than assumed: a fail-open
    # branch nobody logs is a lock that was not taken and not recorded either.
    sink = "log=_emit" in DRIVER_SOURCE
    assert (unheld, len(marked), sink) == (True, 1, True)


# ===========================================================================
# h. FINDING A - the slot index is positional, the recorded lane is not
# ===========================================================================


def test_a_roster_insertion_cannot_hide_a_live_holder(tmp_path: Path) -> None:
    """THE COUNTER-EXAMPLE, as an arm. It reddens against a positional lookup.

    Insert one lane at the FRONT of the roster and every slot index under it
    re-points. A reader that resolved a lane by position alone then reads the
    wrong file, reports FREE over a live worker, and the next claim double-books
    the worktree - the concurrent-index corruption class. The claim here is made
    BEFORE the roster moves and probed after, which is exactly the order a
    roster edit lands in against a running lane.
    """
    root = tmp_path / "locks"
    claimed = bool(_claim("queue", root, tmp_path / "wt-a").get("ok"))
    held_at = sorted(path.name for path in root.iterdir())
    monkeypatch_roster = ("queue-a-priority", "queue", "queue-b")
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(lanes, "LANES", monkeypatch_roster)
        moved = lanes.lock_path(root=root, lane="queue").name
        state = lanes.lane_state(root, None, "queue")
        again = _claim("queue", root, tmp_path / "wt-b", OTHER_RUN_ID)
    verdict = (claimed, held_at, moved, state["state"], state["pid"], again.get("refused"))
    assert verdict == (True, ["0.lock"], "1.lock", lanes.RUNNING, os.getpid(), "lane_held")


# ===========================================================================
# i. FINDING B - two clones, one worktree, and the guard that stops them
# ===========================================================================


def test_two_clones_driving_one_worktree_exclude(
    tmp_path: Path, mutexes: NameKeyedMutexes, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The regression the per-checkout narrowing would otherwise have opened.

    Two clones at different paths derive DIFFERENT driver mutexes and keep
    DISJOINT lock roots, while the launcher resolves both to ONE working
    directory. Nothing repo-scoped can see that, so the second guard is keyed on
    the directory alone. Measured by moving the repository identity between two
    acquisitions of the SAME lane against the SAME worktree.
    """
    tree = tmp_path / "cs-lane-queue"
    lane = LANE_LIST[0]
    with queue_loop._driver_singleton(lane, tree):  # noqa: SLF001 - the subject
        names_held = sorted(mutexes.held)
        monkeypatch.setattr(lanes, "REPO_ROOT", tmp_path / "another-clone")
        second_clone = queue_loop.driver_mutex(lane)
        refused = False
        try:
            with queue_loop._driver_singleton(lane, tree):  # noqa: SLF001 - same
                pass
        except MutexTimeout:
            refused = True
    distinct_driver_names = second_clone not in names_held
    guards_taken = len(names_held)
    assert (distinct_driver_names, refused, guards_taken) == (True, True, 2)


def test_a_second_worktree_is_not_refused_by_the_box_wide_guard(
    tmp_path: Path, mutexes: NameKeyedMutexes
) -> None:
    """THE CONTROL for the arm above - the guard must not refuse everything.

    A guard that refused any second driver would pass the exclusion arm while
    making a second lane impossible, which is the defect this whole item exists
    to remove. Two lanes in two working directories run together.
    """
    first, second = LANE_PAIRS[0]
    with (
        queue_loop._driver_singleton(first, tmp_path / "cs-lane-one"),  # noqa: SLF001
        queue_loop._driver_singleton(second, tmp_path / "cs-lane-two"),  # noqa: SLF001
    ):
        held = len(mutexes.held)
    # Two guards each, and every name distinct: the driver half by lane, the
    # box-wide half by directory.
    assert held == TWO_GUARDS * len({first, second})


def test_the_box_wide_guard_carries_no_repository_token(tmp_path: Path) -> None:
    """It is the ONE name two clones must agree on, so it may not be narrowed.

    Measured the only way that means anything: move the repository identity and
    the lane, and watch the name stay put, while moving the DIRECTORY moves it.
    """
    tree = tmp_path / "cs-lane-queue"
    before = queue_loop.worktree_mutex(tree)
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(lanes, "REPO_ROOT", tmp_path / "another-clone")
        after_move = queue_loop.worktree_mutex(tree)
    elsewhere = queue_loop.worktree_mutex(tmp_path / "cs-lane-other")
    spelled = str(tree) in before
    assert (after_move, before != elsewhere, spelled) == (before, True, False)


# ===========================================================================
# j. The second lane is claimable but NOT yet launchable, and that is MEASURED
# ===========================================================================


def test_a_claimed_but_unwired_lane_is_released_rather_than_wedged(tmp_path: Path) -> None:
    """The roster is wider than the WIRING, so this path is live today.

    ``lane_launcher.LANE_COMMANDS`` has no entry for the second lane, so a fire
    against it claims the lane and then cannot start a worker. That was reasoned
    from reading the release path and is now measured: the refusal names the
    reason, the lock is GONE, and the lane reads FREE rather than wedged behind
    a claimer that never spawned. The spawn seam raises if it is ever reached,
    so the arm cannot pass by starting a real process.
    """
    root = tmp_path / "locks"
    unwired = sorted(set(LANE_LIST) - set(lane_launcher.LANE_COMMANDS))
    if not unwired:
        pytest.skip("every lane on the roster is wired - this path is no longer reachable")
    lane = unwired[0]
    claim = _claim(lane, root, tmp_path / "wt")

    def never_spawn(*_args: Any, **_kwargs: Any) -> Any:
        """The default really starts a process, so reaching it is the failure."""
        message = "the launcher reached a spawn for an unwired lane"
        raise AssertionError(message)

    with pytest.raises(lane_launcher.LaneLaunchError) as caught:
        lane_launcher.launch_lane(
            lane, run_id=RUN_ID, token=claim["token"], root=tmp_path, spawn=never_spawn
        )
    verdict = (
        bool(claim.get("ok")),
        caught.value.reason,
        sorted(path.name for path in root.iterdir()),
        lanes.lane_state(root, None, lane)["state"],
    )
    assert verdict == (True, lane_launcher.REASON_LANE_NOT_WIRED, [], lanes.FREE)


# ===========================================================================
# k. CS-1274 - kit v9 fleet_lanes at the kit's cap, one worktree per lane index
# ===========================================================================

#: The lane cap MAIN 2237 section 3 item 2 sets for every tree that has no
#: measured reason for less, and the kit's own ceiling. Written as a literal so
#: a cap that drifts down to the roster's width, or up past the kit, is red.
KIT_CAP: Final = 3

#: A roster wider than the cap, so the cap - and not the roster - is what a
#: fourth claim runs into. Every name is hyphenated, never folded.
WIDE_ROSTER: Final = ("queue", "queue-b", "queue-c", "queue-d")


def _main_checkout(tmp_path: Path) -> Path:
    """A stand-in MAIN checkout whose ``.git`` is a directory, as git lays it out.

    Resolved, so the kit's own ``resolve()`` in ``main_tree`` and this arm agree
    on one spelling of the directory - a short 8.3 component on one side only
    would make two names for one tree.
    """
    main = (tmp_path / "parent" / "Clockspeed").resolve()
    (main / ".git").mkdir(parents=True)
    return main


def _kit_lock_root(main: Path) -> Path:
    """The lane lock root the kit itself reads for a checkout."""
    return main / fleet_lanes.LANES_REL


def _relative_tree(tree: Any, main: Path) -> str:
    """A claimed worktree spelled relative to the checkout's parent - a scalar."""
    return Path(str(tree)).resolve().relative_to(main.parent).as_posix()


def _release_all(claims: list[dict[str, Any]], root: Path) -> list[bool]:
    """Release every successful claim, reporting what each release answered."""
    return [lanes.release_lane(c["token"], root=root) for c in claims if c.get("ok")]


def test_cs1274_the_cap_is_the_kits_and_is_decoupled_from_the_roster() -> None:
    """MAIN 2237 section 4a: DECOUPLE MAX_SLOTS FROM len(LANES).

    The cap is validated through the kit's own ``lane_cap`` - the one place the
    1..LANE_CAP_MAX bound is written - and the module carries no arithmetic over
    the roster that could re-couple them.
    """
    source = (ROOT / "ops" / "loop" / "lanes.py").read_text(encoding="utf-8")
    recoupled = "MAX_SLOTS = len(LANES)" in source
    pinned = (lanes.LANE_CAP, lanes.MAX_SLOTS, fleet_lanes.lane_cap(lanes.LANE_CAP))
    assert (pinned, fleet_lanes.LANE_CAP_MAX, recoupled) == ((KIT_CAP,) * 3, KIT_CAP, False)


def test_cs1274_the_lane_worktree_root_is_derived_from_the_repo_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The kit's layout, <parent>/cs-worktrees/lane-<i>, read off the main tree.

    Measured by MOVING the repository root and watching every lane worktree
    move with it - a hardcoded base would stay put. An index outside the cap
    has no worktree at all rather than a fabricated one.
    """
    main = _main_checkout(tmp_path)
    monkeypatch.setattr(lanes, "REPO_ROOT", main)
    here = [_relative_tree(lanes.lane_worktree(i), main) for i in range(lanes.MAX_SLOTS)]
    kit = [_relative_tree(fleet_lanes.worktree_path(main, "CS", i), main) for i in range(KIT_CAP)]
    moved = _main_checkout(tmp_path / "elsewhere")
    monkeypatch.setattr(lanes, "REPO_ROOT", moved)
    after = _relative_tree(lanes.lane_worktree(0), moved)
    with pytest.raises(ValueError, match="lane index"):
        lanes.lane_worktree(lanes.MAX_SLOTS)
    expected = ["cs-worktrees/lane-0", "cs-worktrees/lane-1", "cs-worktrees/lane-2"]
    assert (here, kit, after) == (expected, expected, "cs-worktrees/lane-0")


def test_cs1274_three_lanes_hold_three_indices_and_three_worktrees(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """THE ACCEPTANCE: three lanes at once, a worktree per lane, none shared.

    Each lane asks for the kit's derivation rather than naming a tree, and each
    lands at its HOME index with that index's own worktree. Released, the lock
    root carries no lane lock - the lifetime half of the same claim.
    """
    main = _main_checkout(tmp_path)
    monkeypatch.setattr(lanes, "REPO_ROOT", main)
    root = _kit_lock_root(main)
    claims = [
        lanes.try_acquire_lane(lane, run_id=f"{RUN_ID}{i}", worktree=lanes.lane_worktree, root=root)
        for i, lane in enumerate(LANE_LIST)
    ]
    try:
        indices = [c.get("index") for c in claims]
        trees = [_relative_tree(c.get("worktree"), main) for c in claims]
        recorded = [lanes.read_payload(Path(c["token"])).get("index") for c in claims]
    finally:
        released = _release_all(claims, root)
    left = sorted(path.name for path in root.iterdir() if path.suffix == ".lock")
    expected_trees = [f"cs-worktrees/lane-{i}" for i in range(KIT_CAP)]
    verdict = (indices, recorded, trees, released, left)
    assert verdict == ([0, 1, 2], [0, 1, 2], expected_trees, [True] * KIT_CAP, [])


def test_cs1274_the_kits_lane_widget_reads_a_clockspeed_claim(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """ON-DISK COMPATIBILITY with the kit: one file per index, the name a field.

    ``fleet_lanes.repo_lane_state`` is the lane widget's contract - exactly
    these files, no directory walk. A claim made here must read RUNNING there,
    under the lane name, at the index it took; the rest read FREE.
    """
    main = _main_checkout(tmp_path)
    monkeypatch.setattr(lanes, "REPO_ROOT", main)
    root = _kit_lock_root(main)
    claim = lanes.try_acquire_lane(
        "queue-b", run_id=RUN_ID, worktree=lanes.lane_worktree, root=root
    )
    try:
        rows = fleet_lanes.repo_lane_state(main, lanes.LANE_CAP)
        seen = [(row["index"], row["state"], row["lane"]) for row in rows]
        widget_tree = _relative_tree(rows[1]["worktree"], main)
    finally:
        _release_all([claim], root)
    after = [row["state"] for row in fleet_lanes.repo_lane_state(main, lanes.LANE_CAP)]
    expected = [
        (0, fleet_lanes.FREE, None),
        (1, fleet_lanes.RUNNING, "queue-b"),
        (2, fleet_lanes.FREE, None),
    ]
    verdict = (seen, widget_tree, after)
    assert verdict == (expected, "cs-worktrees/lane-1", [fleet_lanes.FREE] * KIT_CAP)


def test_cs1274_a_lane_whose_home_is_held_runs_at_another_index(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """ANY ROSTER LANE RUNS AT ANY INDEX - the kit's model, MAIN 2237 section 2.

    The kit's own acquirer takes the lowest free index for a lane CS never
    named. The queue lane's home is then held, so it lands on the next free
    index and that index's worktree, and every reader still finds it by name.
    """
    main = _main_checkout(tmp_path)
    monkeypatch.setattr(lanes, "REPO_ROOT", main)
    root = _kit_lock_root(main)
    foreign = fleet_lanes.try_acquire_lane(main, "CS", "foreign", "kit-run", KIT_CAP)
    claim = lanes.try_acquire_lane("queue", run_id=RUN_ID, worktree=lanes.lane_worktree, root=root)
    try:
        index = claim.get("index")
        tree = _relative_tree(claim.get("worktree"), main)
        state = lanes.lane_state(root, None, "queue")
        found = lanes.lock_for_lane(root, "queue").name
    finally:
        _release_all([claim], root)
        fleet_lanes.release_lane(foreign)
    verdict = (foreign.get("index"), index, tree, state["state"], found)
    assert verdict == (0, 1, "cs-worktrees/lane-1", lanes.RUNNING, "1.lock")


def test_cs1274_a_fourth_lane_is_refused_by_the_cap_and_writes_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The CAP refuses, not the roster: a roster wider than the cap still holds the cap.

    The refusal is the kit's word, ``lanes_full``, and like every refusal it
    touches no lock - the lock files are byte-identical before and after. Once
    a slot frees, the lane with no home index takes it: any lane, any index.
    """
    main = _main_checkout(tmp_path)
    monkeypatch.setattr(lanes, "REPO_ROOT", main)
    monkeypatch.setattr(lanes, "LANES", WIDE_ROSTER)
    root = _kit_lock_root(main)
    claims = [
        lanes.try_acquire_lane(lane, run_id=f"{RUN_ID}{i}", worktree=lanes.lane_worktree, root=root)
        for i, lane in enumerate(WIDE_ROSTER[:KIT_CAP])
    ]
    try:
        before = {p.name: p.read_bytes() for p in root.iterdir() if p.suffix == ".lock"}
        fourth = lanes.try_acquire_lane(
            WIDE_ROSTER[-1], run_id="fourth", worktree=lanes.lane_worktree, root=root
        )
        after = {p.name: p.read_bytes() for p in root.iterdir() if p.suffix == ".lock"}
        unchanged = before == after
        holders = sorted(fourth.get("holders") or [])
        lanes.release_lane(claims[1]["token"], root=root)
        late = lanes.try_acquire_lane(
            WIDE_ROSTER[-1], run_id="late", worktree=lanes.lane_worktree, root=root
        )
        late_at = (late.get("ok"), late.get("index"), _relative_tree(late.get("worktree"), main))
        _release_all([late], root)
    finally:
        _release_all([claims[0], claims[2]], root)
    verdict = (fourth.get("ok"), fourth.get("refused"), unchanged, holders, late_at)
    expected_holders = sorted(WIDE_ROSTER[:KIT_CAP])
    assert verdict == (
        False,
        "lanes_full",
        True,
        expected_holders,
        (True, 1, "cs-worktrees/lane-1"),
    )


def test_cs1274_the_kits_acquire_mutex_is_the_one_both_acquirers_take(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """ONE MUTEX, so a kit acquirer and this one can never both take an index.

    Placement at ANY index needs a scan and a create under one lock, or two
    acquirers of one lane name could land at two indices. The kit already holds
    that lock; a second, Clockspeed-only one would serialise nothing against it.
    Held here by the kit's own context manager, the acquire refuses with its
    own word and writes no lock.
    """
    root = tmp_path / "locks"
    root.mkdir()
    monkeypatch.setattr(lanes, "ACQUIRE_WAIT_S", 0.0)
    # SLF001: the kit's acquire mutex IS the subject - reaching it any other way
    # would grade a re-implementation of the object both acquirers must share.
    with fleet_lanes._acquire_mutex(root, wait=0.0):  # noqa: SLF001
        answer = lanes.try_acquire_lane("queue", run_id=RUN_ID, worktree=tmp_path / "wt", root=root)
    locks = sorted(path.name for path in root.iterdir() if path.suffix == ".lock")
    after = lanes.try_acquire_lane(
        "queue", run_id=OTHER_RUN_ID, worktree=tmp_path / "wt", root=root
    )
    _release_all([after], root)
    mutex_left = (root / fleet_lanes.ACQUIRE_MUTEX).exists()
    verdict = (answer.get("ok"), answer.get("refused"), locks, bool(after.get("ok")), mutex_left)
    assert verdict == (False, "acquire_busy", [], True, False)


def test_cs1274_a_kit_claim_whose_claimer_still_lives_is_never_reclaimed_here(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The kit keeps a claim RUNNING while its CLAIMER lives, after its worker dies.

    ``fleet_lanes.repoint_lane_pid(..., keep_claimer=True)`` records the
    claimer as ``holder_pid`` beside the worker's ``pid``. With the worker gone
    the kit still reads the index RUNNING - the claimer merges behind it - so
    this module must too, or its next acquire would reclaim the index from
    under a live kit claim and hand the same worktree to a second writer.
    """
    main = _main_checkout(tmp_path)
    monkeypatch.setattr(lanes, "REPO_ROOT", main)
    root = _kit_lock_root(main)
    dead = next(pid for pid in range(30000, 60000, 4) if not lanes.pid_alive(pid))
    kit_claim = fleet_lanes.try_acquire_lane(main, "CS", "queue", "kit-run", KIT_CAP)
    repointed = fleet_lanes.repoint_lane_pid(kit_claim, dead, keep_claimer=True)
    try:
        kit_says = fleet_lanes.repo_lane_state(main, KIT_CAP)[0]["state"]
        here = lanes.lane_state(root, None, "queue")["state"]
        again = lanes.try_acquire_lane(
            "queue", run_id=RUN_ID, worktree=lanes.lane_worktree, root=root
        )
    finally:
        fleet_lanes.release_lane(kit_claim)
    verdict = (repointed, kit_says, here, again.get("refused"))
    assert verdict == (True, fleet_lanes.RUNNING, lanes.RUNNING, "lane_held")


#: Run in a CHILD inside a checkout that carries ``lanes.py`` and no kit - the
#: shape ``ops/loop/claims.py`` imports it in from a worker's own tree. Prints
#: what reading a lane and claiming one each did, by state word and type name.
_KITLESS_PROBE: Final = """
import json
import sys

sys.path.insert(0, sys.argv[1])
from ops.loop import lanes

answer = {"state": lanes.lane_state(sys.argv[2], None, "queue")["state"]}
try:
    lanes.try_acquire_lane("queue", run_id="kitless", worktree=sys.argv[3], root=sys.argv[2])
    answer["claim"] = "claimed"
except Exception as exc:
    answer["claim"] = type(exc).__name__
print(json.dumps(answer))
"""


def test_cs1274_a_checkout_without_the_kit_reads_lanes_and_cannot_claim_one(
    tmp_path: Path,
) -> None:
    """The kit is bound on FIRST USE: reading needs none of it, claiming needs all of it.

    ``ops/loop/claims.py`` imports this module inside a worker's checkout only
    to read lane STATE, so that import must not require the kit. A CLAIM must:
    without the kit's acquire mutex there is nothing a kit acquirer would
    serialise against, so the claim fails LOUDLY and writes no lock - it never
    quietly proceeds unserialised.
    """
    checkout = tmp_path / "kitless"
    for relative in ("ops/__init__.py", "ops/loop/__init__.py", "ops/loop/lanes.py"):
        target = checkout / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / relative).read_bytes())
    (checkout / ".git").mkdir()
    locks = tmp_path / "locks"
    script = tmp_path / "kitless_probe.py"
    script.write_text(_KITLESS_PROBE, encoding="utf-8")
    argv = [sys.executable, str(script), str(checkout), str(locks), str(tmp_path / "wt")]
    done = subprocess.run(argv, capture_output=True, text=True, timeout=120, check=False)
    ran = done.returncode == 0
    answer = json.loads(done.stdout.strip().splitlines()[-1]) if ran else {}
    written = sorted(p.name for p in locks.iterdir()) if locks.exists() else []
    verdict = (ran, answer.get("state"), answer.get("claim"), written)
    assert verdict == (True, lanes.FREE, "FileNotFoundError", [])


def test_cs1274_a_stale_lock_of_the_same_lane_never_hides_its_live_one(tmp_path: Path) -> None:
    """Two locks can name one lane: a crashed fallback claim and a live home one.

    Readers must answer the LIVE one. A reader that took the first match by
    file order would report RECLAIMABLE over a running worker - and the next
    acquire would double-book it.
    """
    root = tmp_path / "locks"
    root.mkdir()
    dead = next(pid for pid in range(30000, 60000, 4) if not lanes.pid_alive(pid))
    stale = {"pid": dead, "lane": "queue", "run_id": "crashed", "worktree": "w", "ts": 1.0}
    (root / "2.lock").write_bytes(json.dumps(stale).encode("utf-8"))
    claim = lanes.try_acquire_lane("queue", run_id=RUN_ID, worktree=tmp_path / "wt", root=root)
    try:
        state = lanes.lane_state(root, None, "queue")["state"]
        found = lanes.lock_for_lane(root, "queue").name
        again = lanes.try_acquire_lane(
            "queue", run_id="again", worktree=tmp_path / "wt2", root=root
        )
    finally:
        _release_all([claim], root)
    verdict = (claim.get("index"), state, found, again.get("refused"))
    assert verdict == (0, lanes.RUNNING, "0.lock", "lane_held")


# ===========================================================================
# l. CS-1274 r2 - the driver HOLDS its index until it releases, as the kit does
# ===========================================================================


def _foreign_lock(root: Path, index: int) -> None:
    """A live kit claim at ``index`` under a name this roster does not carry.

    The holder is THIS process, which is alive for the whole arm - the kit's
    acquirer names lanes CS never lists, and any lane may hold any index.
    """
    root.mkdir(parents=True, exist_ok=True)
    record = {
        "pid": os.getpid(),
        "lane": f"foreign-{index}",
        "run_id": "kit-run",
        "worktree": f"t{index}",
        "ts": 1.0,
        "index": index,
    }
    (root / f"{index}.lock").write_bytes(json.dumps(record).encode("utf-8"))


def test_cs1274_r2_a_lane_whose_worker_exited_stays_held_until_its_driver_releases(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """THE PROBE'S SHAPE: no other lane may claim an index its driver is still finishing.

    The driver claims, re-points at its worker, and the worker exits. Until the
    driver has ended ``lane-<i>.json`` and released, the index is the DRIVER'S:
    the kit forces ``holder_pid`` for exactly this (``keep_claimer``), and both
    readers - the kit's widget and this module - must say RUNNING. The refuted
    CS-1274 first cut read RECLAIMABLE there, and a second lane took index 0 mid-finish.
    With the other two indices held, the second lane is refused ``lanes_full``;
    once the driver releases, the index is free and the lock is gone.
    """
    main = _main_checkout(tmp_path)
    monkeypatch.setattr(lanes, "REPO_ROOT", main)
    root = _kit_lock_root(main)
    for index in (1, 2):
        _foreign_lock(root, index)
    dead = next(pid for pid in range(30000, 60000, 4) if not lanes.pid_alive(pid))
    driver = lanes.try_acquire_lane("queue", run_id=RUN_ID, worktree=lanes.lane_worktree, root=root)
    repointed = lanes.repoint_lane_pid(driver["token"], dead, root=root)
    held = lanes.lane_state(root, None, "queue")["state"]
    widget = fleet_lanes.repo_lane_state(main, KIT_CAP)[0]["state"]
    second = lanes.try_acquire_lane(
        "queue-b", run_id=OTHER_RUN_ID, worktree=lanes.lane_worktree, root=root
    )
    if second.get("ok"):
        lanes.release_lane(second["token"], root=root)
    released = lanes.release_lane(driver["token"], root=root)
    left = sorted(path.name for path in root.iterdir() if path.suffix == ".lock")
    verdict = (
        driver.get("index"),
        repointed,
        held,
        widget,
        second.get("ok"),
        second.get("refused"),
        released,
        left,
    )
    assert verdict == (
        0,
        True,
        lanes.RUNNING,
        fleet_lanes.RUNNING,
        False,
        "lanes_full",
        True,
        ["1.lock", "2.lock"],
    )


def test_cs1274_r2_the_runbook_names_the_per_index_worktrees_and_not_the_old_one() -> None:
    """``docs/OPERATIONS.md`` sends an operator to the tree a lane ACTUALLY runs in.

    The refuted CS-1274 first cut moved every lane to the kit's ``cs-worktrees/lane-<i>``
    and left the runbook pointing at the retired single-lane tree, so the
    ``git status`` an operator is told to run read a directory no lane writes.
    The layout is named relative to the main checkout's parent, as the code
    derives it - never as a drive-rooted path.
    """
    runbook = (ROOT / "docs" / "OPERATIONS.md").read_text(encoding="utf-8")
    retired = "cs-lane-queue" in runbook
    names_layout = "cs-worktrees/lane-<i>" in runbook
    drive_rooted = "C:\\cs-worktrees" in runbook
    assert (retired, names_layout, drive_rooted) == (False, True, False)


def test_cs1274_r2_a_lane_whose_driver_also_died_is_reclaimable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """THE CONTROL: the holder keeps a lane only while the HOLDER lives.

    Worker and driver both gone is a crashed cycle, and it must never wedge
    the index - the kit's reader and this one both read RECLAIMABLE, and the
    next claim takes it.
    """
    main = _main_checkout(tmp_path)
    monkeypatch.setattr(lanes, "REPO_ROOT", main)
    root = _kit_lock_root(main)
    dead = next(pid for pid in range(30000, 60000, 4) if not lanes.pid_alive(pid))
    driver = lanes.try_acquire_lane("queue", run_id=RUN_ID, worktree=lanes.lane_worktree, root=root)
    lanes.repoint_lane_pid(driver["token"], dead, root=root)
    lock = Path(driver["token"])
    record = json.loads(lock.read_text(encoding="utf-8"))
    record.update({"holder_pid": dead, "holder_started": None})
    lock.write_bytes(json.dumps(record).encode("utf-8"))
    here = lanes.lane_state(root, None, "queue")["state"]
    widget = fleet_lanes.repo_lane_state(main, KIT_CAP)[0]["state"]
    again = lanes.try_acquire_lane(
        "queue", run_id=OTHER_RUN_ID, worktree=lanes.lane_worktree, root=root
    )
    if again.get("ok"):
        lanes.release_lane(again["token"], root=root)
    verdict = (here, widget, again.get("ok"), again.get("index"))
    assert verdict == (lanes.RECLAIMABLE, fleet_lanes.RECLAIMABLE, True, 0)
