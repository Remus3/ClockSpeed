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
import os
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
