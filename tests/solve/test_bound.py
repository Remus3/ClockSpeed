"""CS-1245 - the bounded candidate enumeration, its trim record and its ascent.

Every case reaches the optimizer only through
``clockspeed.solve.bound.optimize_within_bound`` or through ``optimize_plan``,
the door every other caller uses. Nothing here constructs a backend class, for
the reason ``tests/solve/test_optimize.py``'s own docstring gives.

WHY EVERY CAP ARM PADS THE CORPUS, AND FRONTS THE ACT WITH A CONTROL
----------------------------------------------------------------------
``tests/solve/synthetic.py``'s corpus holds eleven recipes against a cap of
twelve, so NO shipped fixture can reach the cap. An arm whose fixture cannot
reach it passes while grading nothing - a measured defect class on this project.
So every cap arm below builds a padded variant and asserts
``len(usable) > MAX_EXHAUSTIVE_CANDIDATES`` BEFORE the act.

The padding recipes are byte-equivalent to one another by construction, which
makes them useless for distinguishing "the smallest passing prefix" from "the
first prefix built": every objective scores them identically. So the two arms
that grade that distinction - :func:`test_the_chosen_prefix_is_the_smallest_that_passes`
and :func:`test_a_target_producer_last_in_registry_order_survives_the_trim` -
carry hand-built recipes with asymmetric arithmetic instead, and each one runs
the WRONG answer through ``optimize_plan`` and shows what it would have been.

WHY DETERMINISM IS GRADED ACROSS TWO PROCESSES AND NOT TWICE IN ONE
---------------------------------------------------------------------
The hazard this module's data is shaped against is a SET deciding an order: a
set's iteration order and repr depend on PYTHONHASHSEED, so two runs would
render differently while a same-process double call agrees with itself every
time. :func:`test_two_processes_under_different_hash_seeds_agree` therefore
spawns two children under PYTHONHASHSEED 0 and 1 and compares their stdout.

NO TOLERANCE, AND EQUALITY IS NOT ENOUGH ON ITS OWN
-----------------------------------------------------
``tests/solve/__init__.py`` binds this file: no ``pytest.approx``, no
``math.isclose``, no epsilon. Score assertions are paired with
``type(x) is Fraction`` and with ``audit_exact`` over the whole returned value,
because ``Fraction(1, 2) == 0.5`` is True.
"""

from __future__ import annotations

import subprocess
import sys
from dataclasses import replace
from fractions import Fraction
from pathlib import Path
from types import MappingProxyType
from typing import Any, Final

import pytest

from clockspeed.data.registry import Registry
from clockspeed.solve import bound
from clockspeed.solve.backends import BACKEND_EXHAUSTIVE, BACKEND_GREEDY, exhaustive
from clockspeed.solve.bound import (
    TRIM_RULES,
    TRIM_TARGET_PRODUCERS_FIRST,
    BoundedResult,
    BoundExhaustedError,
    TrimRecord,
    TrimStep,
    optimize_within_bound,
)
from clockspeed.solve.exact import InexactValueError, audit_exact
from clockspeed.solve.optimize import (
    MAX_EXHAUSTIVE_CANDIDATES,
    NoFeasibleSelectionError,
    Objective,
    ObjectiveUndefinedError,
    OptimizeRequest,
    OptimizeResult,
    PowerNotComparableError,
    SolveConfig,
    UnknownBackendError,
    evaluate_selection,
    optimize_plan,
    usable_candidates,
    weighted_objective,
)
from clockspeed.solve.ratio import BYPRODUCT_BALANCED, BYPRODUCT_SINKABLE
from tests.data.synthetic import (
    KEY_CLASS_NAME,
    KEY_DISPLAY_NAME,
    KEY_DURATION,
    KEY_INGREDIENTS,
    KEY_PRODUCED_IN,
    KEY_PRODUCT,
    amount_blob,
    class_path_blob,
)
from tests.solve.synthetic import (
    ALT_GADGET_RECIPE,
    C5_TRINKET_TARGET,
    ORPHAN_RECIPE,
    RECLAIM_RECIPE,
    SOLVE_ASSEMBLER_BUILDING,
    SOLVE_ORE_ITEM,
    SOLVE_PLATE_ITEM,
    SOLVE_RARE_ITEM,
    SOLVE_RELIC_ITEM,
    SOLVE_RESIDUE_ITEM,
    SOLVE_ROD_ITEM,
    SOLVE_TRINKET_ITEM,
    STD_GADGET_RECIPE,
    ZERO_DURATION_RECIPE,
    building_path,
    reclaim_registry,
    registry_with,
    solve_registry,
)

# ---------------------------------------------------------------------------
# Named values, so no assertion carries a bare literal
# ---------------------------------------------------------------------------

UNIT: Final[Fraction] = Fraction(1)

#: Ore demand per minute is the one direction every fixture below is asymmetric
#: in, so it is the objective every arm is asked under.
MINIMIZE_RAW: Final[Objective] = weighted_objective(raw=UNIT)

#: Relic per minute, for every hand-built fixture here.
RELIC_TARGET: Final[Fraction] = Fraction(10)

#: Filler for the cap. Each is a distinct ClassName producing an item that
#: already has a descriptor, so the variant registry still builds, and none of
#: them produces a target - which is what puts them in the trim rule's SECOND
#: tier.
PADDING_PREFIX: Final = "R_Pad"

#: Six seconds per cycle for every hand-built recipe. One duration across the
#: fixture means a score difference can only come from the arithmetic under
#: test and never from a cycle time.
FIXTURE_DURATION: Final = "6.000000"

#: The two-stage route's Relic recipe, declared FIRST of the three so that an
#: ascent stopping at the first tier-0 member by registry position would stop at
#: an INFEASIBLE one. It consumes Rare, which nothing in the candidate set
#: produces until :data:`RARE_RECIPE` joins it.
RELIC_FROM_RARE_RECIPE: Final = "R_B1Relic"

#: The one-stage route: Relic straight from Ore, feasible ALONE and expensive.
RELIC_FROM_ORE_RECIPE: Final = "R_B2Direct"

#: The second stage of the cheap route. It produces Rare, which is not a target,
#: so the trim rule ranks it behind both Relic producers.
RARE_RECIPE: Final = "R_B3Rare"

#: The only Relic producer in the late-producer fixture, declared LAST so that a
#: registry-order trim would drop it.
LATE_PRODUCER_RECIPE: Final = "R_ZLateProducer"

#: Ore per cycle for the expensive one-stage Relic recipe, and for the cheap
#: route's own stages. The gap is what makes the whole-set optimum STRICTLY
#: better than the size-two prefix's.
DIRECT_ORE_PER_CYCLE: Final = 6
CHEAP_ORE_PER_CYCLE: Final = 1

#: Ore per cycle for the Relic producer that sits LAST in registry order.
LATE_PRODUCER_ORE_PER_CYCLE: Final = 2

#: Hand-derived absolutes for the ascent fixture, at 10 Relic/min.
#:
#: The size-two prefix can only use the one-stage recipe - the two-stage one is
#: infeasible for want of a Rare producer - so it buys 10 Relic/min at six Ore
#: each: 60 Ore/min. The whole trimmed set also holds the Rare recipe, so the
#: two-stage route runs at one Ore per Relic: 10 Ore/min. Both figures come from
#: the recipe arithmetic above and from no solver.
PREFIX_TWO_ORE_PER_MINUTE: Final[Fraction] = Fraction(60)
WHOLE_SET_ORE_PER_MINUTE: Final[Fraction] = Fraction(10)

#: The ascent's answer for the fixture whose only Relic producer is last in
#: registry order: two Ore per Relic at 10 Relic/min.
LATE_PRODUCER_ORE_PER_MINUTE: Final[Fraction] = Fraction(20)

#: The prefix size each ascent arm must stop at. Named rather than written as a
#: literal at the assertion, so the arm says WHICH prefix it means.
FIRST_PREFIX: Final = 1
SECOND_PREFIX: Final = 2

#: How many recipes the ascent fixture hand-builds before its padding.
ASCENT_HAND_BUILT: Final = 3

#: One padding recipe past the cap, so exactly one member is trimmed. One is
#: enough to grade the partition and keeps the whole-set comparison cheap.
PADDING_OVER_CAP: Final = 1

#: Both shipped backends, because each answers S_0 through its own walk.
BOTH_BACKENDS: Final[tuple[str, ...]] = (BACKEND_EXHAUSTIVE, BACKEND_GREEDY)

#: The prefix a request whose targets are all zero must stop at.
EMPTY_PREFIX: Final = 0

#: The rate that makes a target zero, exact like every other rate here.
ZERO_RATE: Final[Fraction] = Fraction(0)

#: Every way the door can leave nothing usable, as ``(candidates, unlocked)``:
#: nothing named, everything named locked, everything named zero duration. The
#: last two carry an exclusion note on ``optimize_plan``'s result, which is why
#: the arms below compare the plan and never the whole result.
EMPTY_USABLE_SETS: Final = (
    pytest.param((), (), id="no-candidates"),
    pytest.param((STD_GADGET_RECIPE,), (), id="all-locked"),
    pytest.param((ZERO_DURATION_RECIPE,), (ZERO_DURATION_RECIPE,), id="all-zero-duration"),
)

#: Every shape of "all zero": one zero target, several, and none at all.
ALL_ZERO_TARGETS: Final = (
    pytest.param({SOLVE_RELIC_ITEM: ZERO_RATE}, id="one-zero"),
    pytest.param({SOLVE_RELIC_ITEM: ZERO_RATE, SOLVE_TRINKET_ITEM: ZERO_RATE}, id="two-zero"),
    pytest.param({}, id="no-target"),
)

#: How many prefixes an ascent over an empty usable set evaluates: S_0 alone.
ONLY_THE_EMPTY_PREFIX: Final = 1

#: How many prefixes an ascent over one usable candidate evaluates: S_0 and S_1.
ONE_CANDIDATE_PREFIXES: Final = 2

#: The prefix sizes the ascent asks about on C5: S_2 solves, the third one asked.
C5_ASCENT_SIZES: Final[list[int]] = [0, 1, 2]

#: ``(padding recipes, K, subsets the whole ascent evaluates, prefixes tried)``.
#: Under the cap, 1 + 2 + 4 + 8. Over it, K stops at the shipped cap of twelve, so
#: the module docstring's own 8191 is what gets counted, and 13 prefixes rather
#: than the 15 a walk over all 14 recipes would be. Absolutes, so the arm is not
#: the docstring's formula checked against itself.
COST_BOUND_CASES: Final = (
    pytest.param(3, 3, 15, 4, id="under-the-cap"),
    pytest.param(14, 12, 8191, 13, id="over-the-cap"),
)

#: Named nowhere in ``BACKEND_FACTORIES``, so selecting it is a refusal.
UNREGISTERED_BACKEND: Final = "no-such-backend"

#: A rate pillar 2's own audit refuses. The one float in this file, on purpose.
INEXACT_RATE: Final = 0.5

#: Named nowhere in ``BYPRODUCT_POLICIES``.
UNRECOGNIZED_POLICY: Final = "no-such-policy"

#: How pillar 1's crash on a system with no balance row reads: a ``zip(strict=True)``
#: in ``clockspeed/solve/ratio.py::_plan_from``. Matched so these arms cannot pass on
#: an unrelated ValueError, and left this loose so a reworded CPython message cannot
#: redden them.
PILLAR_1_CRASH: Final = "zip"

#: Plate per minute for the R_Reclaim arm. Any positive rate solves.
RECLAIM_PLATE_TARGET: Final[Fraction] = Fraction(30)

#: The cheap Relic producer that also makes Rare, which nothing consumes. Declared
#: ahead of :data:`DEAR_RELIC_RECIPE`, so it is the first member of the ranking.
BYPRODUCT_RELIC_RECIPE: Final = "R_XCheap"

#: The dear Relic producer, feasible alone, and the plan greedy never reaches.
DEAR_RELIC_RECIPE: Final = "R_YDear"

#: Child process bound. Generous: each child builds a registry and runs an
#: ascent, and an unbounded call cannot fail the test that owns it (CS-896).
CHILD_TIMEOUT_SECONDS: Final = 300

#: The two hash seeds the determinism arm compares. 0 disables randomization and
#: 1 selects a fixed non-zero seed, so a set deciding an order renders
#: differently between them.
HASH_SEEDS: Final[tuple[str, ...]] = ("0", "1")

#: The repository root, which each child uses as its working directory.
REPO_ROOT: Final[Path] = Path(__file__).resolve().parents[2]

#: What each child prints. Run with ``-c`` rather than from a file on disk, so
#: that ``sys.path[0]`` is the working directory and the child imports this
#: repository without a temporary file and without any path in its argv.
#: ``-I`` is NOT usable here and that is measured rather than assumed: isolated
#: mode drops both the working directory and PYTHONPATH from ``sys.path``, and
#: this package is not installed, so an isolated child cannot import
#: ``clockspeed`` at all. ``-E`` is worse - it would drop PYTHONHASHSEED and
#: silently make this arm compare two identical runs.
CHILD_SOURCE: Final = """
from clockspeed.solve.bound import optimize_within_bound
from tests.solve.test_bound import ascent_registry, ascent_request

print(repr(optimize_within_bound(ascent_registry(), ascent_request())))
"""


def _entry(
    class_name: str,
    ingredients: list[tuple[str, int]],
    products: list[tuple[str, int]],
) -> dict[str, str]:
    """Build one recipe entry as docs text, in the grammar the corpus uses.

    Built here rather than added to ``tests/solve/synthetic.py``, which is not
    this slice's to edit - the same reasoning
    ``tests/solve/test_optimize.py``'s own ``_recipe_entry`` records, and the
    same imported grammar helpers, so neither file reimplements Unreal's blob
    syntax.

    Args:
        class_name: The entry's ClassName.
        ingredients: ``(item ClassName, verbatim amount)`` pairs.
        products: The product side.

    Returns:
        The entry mapping, every value a string as in the real document.
    """
    return {
        KEY_CLASS_NAME: class_name,
        KEY_DISPLAY_NAME: class_name.removeprefix("R_"),
        KEY_DURATION: FIXTURE_DURATION,
        KEY_INGREDIENTS: amount_blob(ingredients),
        KEY_PRODUCT: amount_blob(products),
        KEY_PRODUCED_IN: class_path_blob([building_path(SOLVE_ASSEMBLER_BUILDING)]),
    }


def _padding(count: int) -> list[dict[str, str]]:
    """Build filler recipes, none of which produces a target.

    Args:
        count: How many.

    Returns:
        The entries, in the order they will take in registry order.
    """
    ore = [(SOLVE_ORE_ITEM, CHEAP_ORE_PER_CYCLE)]
    return [
        _entry(f"{PADDING_PREFIX}{index}", ore, [(SOLVE_ROD_ITEM, 1)]) for index in range(count)
    ]


def _request(candidates: tuple[str, ...], **overrides: Any) -> OptimizeRequest:
    """Build a Relic request over a named candidate set.

    Args:
        candidates: The recipe keys the optimizer may choose among. Also the
            unlocked set, unless an override says otherwise.
        **overrides: Fields to replace.

    Returns:
        The request.
    """
    base = OptimizeRequest(
        targets=MappingProxyType({SOLVE_RELIC_ITEM: RELIC_TARGET}),
        candidates=candidates,
        unlocked=candidates,
        raw_items=(SOLVE_ORE_ITEM,),
        byproduct_policy=BYPRODUCT_BALANCED,
        objective=MINIMIZE_RAW,
        config=SolveConfig(backend=BACKEND_EXHAUSTIVE),
    )
    return replace(base, **overrides) if overrides else base


def _added_keys(registry: Registry, added: list[dict[str, str]]) -> tuple[str, ...]:
    """The added recipes' keys, in REGISTRY order rather than in added order.

    Args:
        registry: The variant registry.
        added: The entries handed to ``registry_with``.

    Returns:
        The keys, in registry order.
    """
    names = {entry[KEY_CLASS_NAME] for entry in added}
    return tuple(key for key in registry.recipes if key in names)


# ---------------------------------------------------------------------------
# The ascent fixture, module level so a child process can import it too
# ---------------------------------------------------------------------------


def _ascent_entries() -> list[dict[str, str]]:
    """The three asymmetric recipes plus enough padding to pass the cap.

    Order is load-bearing twice over. The two Relic producers are declared
    FIRST, the infeasible one ahead of the feasible one, so an ascent that
    stopped at the first prefix it could build would stop at an infeasible one;
    and the Rare recipe - which produces no target, so the trim rule ranks it in
    the second tier - sits behind both, so it enters the search only ABOVE the
    prefix size the ascent must stop at.

    Returns:
        The entries, in the order they take in registry order.
    """
    return [
        _entry(
            RELIC_FROM_RARE_RECIPE,
            [(SOLVE_RARE_ITEM, 1)],
            [(SOLVE_RELIC_ITEM, 1)],
        ),
        _entry(
            RELIC_FROM_ORE_RECIPE,
            [(SOLVE_ORE_ITEM, DIRECT_ORE_PER_CYCLE)],
            [(SOLVE_RELIC_ITEM, 1)],
        ),
        _entry(
            RARE_RECIPE,
            [(SOLVE_ORE_ITEM, CHEAP_ORE_PER_CYCLE)],
            [(SOLVE_RARE_ITEM, 1)],
        ),
        *_padding(MAX_EXHAUSTIVE_CANDIDATES + PADDING_OVER_CAP - ASCENT_HAND_BUILT),
    ]


def ascent_registry() -> Registry:
    """Build the ascent fixture's registry.

    Public because :data:`CHILD_SOURCE` imports it: the determinism arm's two
    children must build the SAME fixture this process does, and importing it is
    the only way that is a fact rather than a copy.

    Returns:
        The variant registry.
    """
    return registry_with(add=_ascent_entries())


def ascent_request() -> OptimizeRequest:
    """Build the ascent fixture's request, over every added recipe.

    Public for the same reason as :func:`ascent_registry`.

    Returns:
        The request.
    """
    added = _ascent_entries()
    return _request(_added_keys(registry_with(add=added), added))


def _late_producer_entries() -> list[dict[str, str]]:
    """Padding filling the whole cap, then the ONLY Relic producer, last.

    The shape that grades the trim rule's first tier. In registry order the
    producer is the final member, so a trim that kept the first
    ``MAX_EXHAUSTIVE_CANDIDATES`` of REGISTRY order would drop it and every
    prefix would then be infeasible.

    Returns:
        The entries, in the order they take in registry order.
    """
    return [
        *_padding(MAX_EXHAUSTIVE_CANDIDATES),
        _entry(
            LATE_PRODUCER_RECIPE,
            [(SOLVE_ORE_ITEM, LATE_PRODUCER_ORE_PER_CYCLE)],
            [(SOLVE_RELIC_ITEM, 1)],
        ),
    ]


@pytest.fixture(scope="module")
def corpus() -> Registry:
    """Build the unmodified synthetic solve registry once for the module.

    Returns:
        The registry.
    """
    return solve_registry()


# ===========================================================================
# a. The cap-hit record
# ===========================================================================


def test_a_cap_hit_records_the_cap_the_rule_and_a_conserving_partition() -> None:
    """The acceptance clause's first half: a step naming the cap and the rule.

    The partition is asserted rather than a count. A count alone cannot express
    a DROPPED row - kept and removed could each be the right length and still
    have lost a member between them - and that is a measured lesson here.
    """
    added = _ascent_entries()
    registry = registry_with(add=added)
    request = _request(_added_keys(registry, added))
    usable, _notes = usable_candidates(registry, request)

    assert len(usable) > MAX_EXHAUSTIVE_CANDIDATES

    bounded = optimize_within_bound(registry, request)

    assert bounded.record is not None
    step = bounded.record.first
    assert step.cap == MAX_EXHAUSTIVE_CANDIDATES
    assert step.rule == TRIM_TARGET_PRODUCERS_FIRST
    assert step.rule in TRIM_RULES
    assert len(step.kept) == MAX_EXHAUSTIVE_CANDIDATES
    # Conservation: the two sides partition the usable set exactly.
    assert len(step.kept) + len(step.removed) == len(usable)
    assert set(step.kept) & set(step.removed) == set()
    assert set(step.kept) | set(step.removed) == set(usable)
    # Both sides in registry order, which is what makes the record renderable.
    assert step.kept == tuple(key for key in registry.recipes if key in set(step.kept))
    assert step.removed == tuple(key for key in registry.recipes if key in set(step.removed))
    audit_exact(bounded, path="bounded")


def test_the_record_shape_is_the_one_relax_py_established() -> None:
    """One step, reachable through ``first``, and the step's fields are tuples.

    Without the ``isinstance`` half, a set-valued ``kept`` satisfies every
    membership assertion in the arm above and still renders differently under a
    different hash seed.
    """
    bounded = optimize_within_bound(ascent_registry(), ascent_request())

    record = bounded.record
    assert isinstance(bounded, BoundedResult)
    assert isinstance(record, TrimRecord)
    assert isinstance(record.first, TrimStep)
    assert record.first is record.steps[0]
    assert isinstance(record.first.kept, tuple)
    assert isinstance(record.first.removed, tuple)


# ===========================================================================
# b. The no-trim control
# ===========================================================================


def test_an_under_cap_request_is_not_recorded_as_trimmed(corpus: Registry) -> None:
    """C5 is two candidates against a cap of twelve, so nothing is trimmed.

    The control the cap arm needs: without it, an implementation that attaches a
    record to EVERY request passes the cap arm unchanged. ``chosen_size`` is
    still present, because it describes the ascent rather than the trim.
    """
    candidates = (ALT_GADGET_RECIPE, STD_GADGET_RECIPE)
    request = _request(
        candidates, targets=MappingProxyType({SOLVE_TRINKET_ITEM: C5_TRINKET_TARGET})
    )
    usable, _notes = usable_candidates(corpus, request)

    assert len(usable) < MAX_EXHAUSTIVE_CANDIDATES

    bounded = optimize_within_bound(corpus, request)

    assert bounded.record is None
    assert bounded.chosen_size == SECOND_PREFIX
    assert bounded.result.selection == (STD_GADGET_RECIPE,)


# ===========================================================================
# c. Determinism
# ===========================================================================


def test_a_permuted_and_duplicated_candidate_tuple_does_not_move_the_answer() -> None:
    """Follows ``test_optimize.py::test_candidate_order_and_duplicates_...``.

    The whole returned value is compared by ``repr``, so the RECORD is graded
    too: a trim ranked off caller order would publish a different kept tuple
    while returning the same plan.
    """
    registry = ascent_registry()
    straight = optimize_within_bound(registry, ascent_request())
    stated = ascent_request().candidates
    permuted = tuple(reversed(stated)) + stated

    shuffled = optimize_within_bound(
        registry, replace(ascent_request(), candidates=permuted, unlocked=permuted)
    )

    assert repr(shuffled) == repr(straight)


def test_two_processes_under_different_hash_seeds_agree() -> None:
    """The acceptance clause's "two runs choose the same candidate", across PROCESSES.

    A same-process double call cannot catch a set deciding an order, because a
    set's iteration order is stable WITHIN a process. These two children differ
    only in PYTHONHASHSEED.
    """
    printed: list[str] = []
    for seed in HASH_SEEDS:
        child = subprocess.run(
            [sys.executable, "-s", "-B", "-c", CHILD_SOURCE],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=CHILD_TIMEOUT_SECONDS,
            env={"PYTHONHASHSEED": seed, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"},
            check=False,
        )
        # Bound to a plain int before asserting: pytest would otherwise repr the
        # whole CompletedProcess, and argv[0] is the absolute interpreter path,
        # which carries the account name into the log.
        # ``tests/solve/test_phase3_gate.py::run_child`` records the measurement.
        exit_code = child.returncode
        assert exit_code == 0, f"the child under PYTHONHASHSEED={seed} failed:\n{child.stderr}"
        printed.append(child.stdout.strip())

    assert printed[0] != ""
    assert printed[0] == printed[1]


# ===========================================================================
# d. The ascent - the smallest passing prefix, not the first built
# ===========================================================================


def test_the_chosen_prefix_is_the_smallest_that_passes() -> None:
    """The acceptance clause's third half, with the whole-set optimum as control.

    The size-one prefix is proved infeasible DIRECTLY, so size two is the smallest
    that passes by measurement rather than by coincidence, and an ascent starting
    ABOVE size two reddens this. One starting at size one stays green here, because
    S_0 refuses this target too:
    :func:`test_the_ascent_visits_the_empty_prefix_first_on_every_request` is the
    arm that grades the start. The whole trimmed set then scores STRICTLY better
    than the answer returned, which is what proves the ascent stopped at the
    smallest passing prefix rather than taking the whole-set optimum - and both
    figures are the hand-derived absolutes above, not a second solver run compared
    against the first.
    """
    registry = ascent_registry()
    request = ascent_request()
    bounded = optimize_within_bound(registry, request)
    record = bounded.record
    assert record is not None

    assert bounded.chosen_size == SECOND_PREFIX
    assert bounded.result.selection == (RELIC_FROM_ORE_RECIPE,)
    assert bounded.result.score == PREFIX_TWO_ORE_PER_MINUTE
    assert type(bounded.result.score) is Fraction

    # The size-one prefix really is infeasible, asserted directly.
    with pytest.raises(NoFeasibleSelectionError):
        optimize_plan(registry, replace(request, candidates=(RELIC_FROM_RARE_RECIPE,)))

    whole = optimize_plan(registry, replace(request, candidates=record.first.kept))

    assert whole.score == WHOLE_SET_ORE_PER_MINUTE
    assert whole.selection == (RELIC_FROM_RARE_RECIPE, RARE_RECIPE)
    assert whole.score < bounded.result.score


def test_a_target_producer_last_in_registry_order_survives_the_trim() -> None:
    """The trim rule's first tier, graded by the answer it makes possible.

    Twelve padding recipes fill the cap and the ONLY Relic producer is declared
    last. A trim that kept the first ``MAX_EXHAUSTIVE_CANDIDATES`` of REGISTRY
    order would drop that producer, every prefix would be infeasible, and this
    call would raise instead of returning. That wrong answer is proved rather
    than asserted in prose: the registry-order keep is run through
    ``optimize_plan`` and shown infeasible first.
    """
    added = _late_producer_entries()
    registry = registry_with(add=added)
    request = _request(_added_keys(registry, added))
    usable, _notes = usable_candidates(registry, request)

    assert len(usable) > MAX_EXHAUSTIVE_CANDIDATES

    with pytest.raises(NoFeasibleSelectionError):
        optimize_plan(registry, replace(request, candidates=usable[:MAX_EXHAUSTIVE_CANDIDATES]))

    bounded = optimize_within_bound(registry, request)

    assert bounded.chosen_size == FIRST_PREFIX
    assert bounded.result.selection == (LATE_PRODUCER_RECIPE,)
    assert bounded.result.score == LATE_PRODUCER_ORE_PER_MINUTE
    assert bounded.record is not None
    assert LATE_PRODUCER_RECIPE in bounded.record.first.kept
    assert bounded.record.first.removed == (f"{PADDING_PREFIX}{MAX_EXHAUSTIVE_CANDIDATES - 1}",)


# ===========================================================================
# e. Exhaustion
# ===========================================================================


def test_a_request_no_prefix_can_solve_refuses_and_names_the_cap_and_the_rule(
    corpus: Registry,
) -> None:
    """C7: nothing produces the orphan ingredient, so no prefix can solve.

    The message is graded, not only the type. A refusal that did not name the
    bound would be indistinguishable from the ordinary ``optimize_plan``
    refusal, and a reader could not tell whether a trim had narrowed the search
    out from under them.
    """
    request = _request((ORPHAN_RECIPE,))

    with pytest.raises(BoundExhaustedError) as caught:
        optimize_within_bound(corpus, request)

    message = str(caught.value)
    assert str(MAX_EXHAUSTIVE_CANDIDATES) in message
    assert TRIM_TARGET_PRODUCERS_FIRST in message


def test_the_refusal_is_a_no_plan_refusal_a_caller_already_handles(corpus: Registry) -> None:
    """``LadderExhaustedError``'s precedent: a caller handling "no plan" needs no edit."""
    assert issubclass(BoundExhaustedError, NoFeasibleSelectionError)

    with pytest.raises(NoFeasibleSelectionError):
        optimize_within_bound(corpus, _request((ORPHAN_RECIPE,)))


def test_a_refusal_over_the_cap_carries_what_the_bound_dropped() -> None:
    """CS-1351: a no-plan is about the kept set, so what the cap dropped travels with it.

    Fourteen fillers, none making Relic, so all share the second tier and registry
    order alone decides: the cap of twelve keeps R_Pad0 to R_Pad11. Named by hand,
    never read back from the ranking.
    """
    added = _padding(14)
    registry = registry_with(add=added)
    request = _request(_added_keys(registry, added))
    usable, _notes = usable_candidates(registry, request)

    assert len(usable) > MAX_EXHAUSTIVE_CANDIDATES

    with pytest.raises(BoundExhaustedError) as caught:
        optimize_within_bound(registry, request)

    record = caught.value.record
    assert record is not None
    assert record.first.removed == ("R_Pad12", "R_Pad13")
    assert record.first.kept == tuple(f"R_Pad{index}" for index in range(12))
    assert record.first.rule == TRIM_TARGET_PRODUCERS_FIRST
    assert record.first.cap == MAX_EXHAUSTIVE_CANDIDATES


def test_a_refusal_under_the_cap_carries_no_record(corpus: Registry) -> None:
    """C7 has one usable candidate, so nothing was dropped and a record would claim otherwise."""
    with pytest.raises(BoundExhaustedError) as caught:
        optimize_within_bound(corpus, _request((ORPHAN_RECIPE,)))

    assert caught.value.record is None


def test_exactly_at_the_cap_nothing_is_dropped_so_there_is_no_record() -> None:
    """Twelve fillers fit a cap of twelve: a record there would remove nothing.

    :class:`TrimRecord` says an empty narrowing gets no record at all, so the off-by-one
    that builds one with ``removed=()`` is the shape this boundary rules out.
    """
    added = _padding(MAX_EXHAUSTIVE_CANDIDATES)
    registry = registry_with(add=added)
    request = _request(_added_keys(registry, added))
    usable, _notes = usable_candidates(registry, request)

    assert len(usable) == MAX_EXHAUSTIVE_CANDIDATES
    assert bound.trim_record(registry, request) is None

    with pytest.raises(BoundExhaustedError) as caught:
        optimize_within_bound(registry, request)

    assert caught.value.record is None


def test_the_record_is_keyword_only_and_a_refusal_built_without_one_holds_none() -> None:
    """Additive: the four positional arguments every shipped raise passes still build one."""
    bare = BoundExhaustedError(MAX_EXHAUSTIVE_CANDIDATES, TRIM_TARGET_PRODUCERS_FIRST, 1, "m")

    assert bare.record is None
    record = TrimRecord(
        steps=(
            TrimStep(
                rule=TRIM_TARGET_PRODUCERS_FIRST,
                cap=MAX_EXHAUSTIVE_CANDIDATES,
                kept=("R_Kept",),
                removed=("R_Dropped",),
            ),
        )
    )
    held = BoundExhaustedError(
        MAX_EXHAUSTIVE_CANDIDATES, TRIM_TARGET_PRODUCERS_FIRST, 1, "m", record=record
    )
    assert held.record is record
    with pytest.raises(TypeError):
        BoundExhaustedError(  # type: ignore[misc]
            MAX_EXHAUSTIVE_CANDIDATES, TRIM_TARGET_PRODUCERS_FIRST, 1, "m", record
        )


def test_trim_record_says_what_the_cap_drops_before_any_search(
    corpus: Registry, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A rule over the targets and registry order, so it stays true whichever refusal ends one."""
    added = _padding(14)
    registry = registry_with(add=added)
    request = _request(_added_keys(registry, added))

    with pytest.raises(BoundExhaustedError) as caught:
        optimize_within_bound(registry, request)

    def no_search(*_args: object, **_kwargs: object) -> OptimizeResult:
        """Refuse every solve, so an answer here cannot have come from one."""
        raise AssertionError

    monkeypatch.setattr(bound, "optimize_plan", no_search)

    assert bound.trim_record(registry, request) == caught.value.record
    assert bound.trim_record(corpus, _request((ORPHAN_RECIPE,))) is None


# ===========================================================================
# f. The closed rule vocabulary
# ===========================================================================


def test_the_trim_rule_vocabulary_is_closed_and_holds_the_shipped_rule() -> None:
    """A second rule cannot arrive unnamed: it has to join this tuple first."""
    assert isinstance(TRIM_RULES, tuple)
    assert TRIM_TARGET_PRODUCERS_FIRST in TRIM_RULES
    assert len(TRIM_RULES) == len(set(TRIM_RULES))


# ===========================================================================
# g. The empty prefix - CS-1350
# ===========================================================================


@pytest.mark.parametrize("backend", BOTH_BACKENDS)
@pytest.mark.parametrize("targets", ALL_ZERO_TARGETS)
@pytest.mark.parametrize(("candidates", "unlocked"), EMPTY_USABLE_SETS)
def test_an_empty_usable_set_with_zero_targets_returns_what_optimize_plan_returns(
    corpus: Registry,
    candidates: tuple[str, ...],
    unlocked: tuple[str, ...],
    targets: dict[str, Fraction],
    backend: str,
) -> None:
    """The CS-1350 acceptance: the bound answers what the door it sits above answers.

    The PLAN is compared and never the whole result. ``optimize_plan`` carries an
    exclusion note for a candidate the door refused and the narrowed request does
    not, which the module docstring records, and the note count below shows that
    difference is live on the fixtures that name a candidate rather than assumed.
    """
    request = _request(
        candidates,
        unlocked=unlocked,
        targets=MappingProxyType(targets),
        config=SolveConfig(backend=backend),
    )
    usable, _notes = usable_candidates(corpus, request)

    assert usable == ()

    direct = optimize_plan(corpus, request)
    bounded = optimize_within_bound(corpus, request)

    assert bounded.result.plan == direct.plan
    assert bounded.result.selection == ()
    assert bounded.chosen_size == EMPTY_PREFIX
    assert bounded.record is None
    assert len(direct.excluded) == len(candidates)
    assert bounded.result.excluded == ()
    audit_exact(bounded, path="bounded")


@pytest.mark.parametrize("backend", BOTH_BACKENDS)
def test_zero_targets_over_a_usable_set_stop_at_the_empty_prefix(
    corpus: Registry, backend: str
) -> None:
    """S_0 is a member of the chain on every request, not only on an empty set.

    Both candidates are usable, so a fix that special-cased an empty usable set
    would still answer this at size one.
    """
    candidates = (ALT_GADGET_RECIPE, STD_GADGET_RECIPE)
    request = _request(
        candidates,
        targets=MappingProxyType({SOLVE_TRINKET_ITEM: ZERO_RATE}),
        config=SolveConfig(backend=backend),
    )
    usable, _notes = usable_candidates(corpus, request)

    assert len(usable) == len(candidates)

    bounded = optimize_within_bound(corpus, request)

    assert bounded.chosen_size == EMPTY_PREFIX
    assert bounded.result.selection == ()
    assert bounded.result.plan == optimize_plan(corpus, request).plan
    assert bounded.record is None


@pytest.mark.parametrize("backend", BOTH_BACKENDS)
@pytest.mark.parametrize("targets", ALL_ZERO_TARGETS)
def test_zero_targets_over_the_cap_stop_at_the_empty_prefix_and_keep_the_record(
    targets: dict[str, Fraction], backend: str
) -> None:
    """The trim runs before the ascent, so a size-zero answer still reports it.

    A record dropped here would tell a caller nothing was narrowed on a request
    where something was. Every shape of "all zero" runs, because a trim gated on
    the request naming a target would drop the record on the empty mapping alone.
    """
    registry = ascent_registry()
    request = replace(
        ascent_request(),
        targets=MappingProxyType(targets),
        config=SolveConfig(backend=backend),
    )
    usable, _notes = usable_candidates(registry, request)

    assert len(usable) > MAX_EXHAUSTIVE_CANDIDATES

    bounded = optimize_within_bound(registry, request)

    assert bounded.chosen_size == EMPTY_PREFIX
    assert bounded.result.selection == ()
    assert bounded.record is not None
    assert len(bounded.record.first.kept) == MAX_EXHAUSTIVE_CANDIDATES
    assert len(bounded.record.first.kept) + len(bounded.record.first.removed) == len(usable)


@pytest.mark.parametrize("backend", BOTH_BACKENDS)
@pytest.mark.parametrize(("candidates", "unlocked"), EMPTY_USABLE_SETS)
def test_an_empty_usable_set_with_a_nonzero_target_counts_the_empty_prefix(
    corpus: Registry, candidates: tuple[str, ...], unlocked: tuple[str, ...], backend: str
) -> None:
    """Still a refusal, and it still says the usable set was empty.

    ``tried`` is exactly one here and at least two on any non-empty set, so the
    distinction the attribute's docstring draws survives S_0 joining the chain.
    """
    request = _request(candidates, unlocked=unlocked, config=SolveConfig(backend=backend))

    with pytest.raises(BoundExhaustedError) as caught:
        optimize_within_bound(corpus, request)

    assert caught.value.tried == ONLY_THE_EMPTY_PREFIX
    assert caught.value.cap == MAX_EXHAUSTIVE_CANDIDATES
    assert f"all {ONLY_THE_EMPTY_PREFIX} nested prefix(es) from size 0" in str(caught.value)


@pytest.mark.parametrize("backend", BOTH_BACKENDS)
def test_exhaustion_counts_every_prefix(corpus: Registry, backend: str) -> None:
    """C7 has one usable candidate, so a full ascent evaluates S_0 and S_1."""
    request = _request((ORPHAN_RECIPE,), config=SolveConfig(backend=backend))

    with pytest.raises(BoundExhaustedError) as caught:
        optimize_within_bound(corpus, request)

    assert caught.value.tried == ONE_CANDIDATE_PREFIXES
    assert f"all {ONE_CANDIDATE_PREFIXES} nested prefix(es) from size 0" in str(caught.value)


@pytest.mark.parametrize("backend", BOTH_BACKENDS)
def test_the_ascent_visits_the_empty_prefix_first_on_every_request(
    corpus: Registry, monkeypatch: pytest.MonkeyPatch, backend: str
) -> None:
    """One chain and no special case, read off the requests the ascent actually makes.

    C5's usable set is not empty and its target is not zero, so the answer is the
    same whether or not the ascent visits S_0. A fix that answered an empty usable
    set on its own and left the loop starting at one returns that answer too, and
    fails here on the sizes alone.
    """
    sizes: list[int] = []

    def spy(registry: Registry, request: OptimizeRequest) -> OptimizeResult:
        """Record the prefix size, then answer as the real door does.

        Args:
            registry: The built registry.
            request: The narrowed request.

        Returns:
            What ``optimize_plan`` returns for it.
        """
        sizes.append(len(request.candidates))
        return optimize_plan(registry, request)

    monkeypatch.setattr(bound, "optimize_plan", spy)
    request = _request(
        (ALT_GADGET_RECIPE, STD_GADGET_RECIPE),
        targets=MappingProxyType({SOLVE_TRINKET_ITEM: C5_TRINKET_TARGET}),
        config=SolveConfig(backend=backend),
    )

    bounded = optimize_within_bound(corpus, request)

    assert sizes == C5_ASCENT_SIZES
    assert bounded.chosen_size == SECOND_PREFIX
    assert bounded.result.selection == (STD_GADGET_RECIPE,)


@pytest.mark.parametrize(
    ("padding", "chain_top", "expected_subsets", "expected_tried"), COST_BOUND_CASES
)
def test_the_cost_bound_arithmetic_is_what_the_ascent_evaluates(
    monkeypatch: pytest.MonkeyPatch,
    padding: int,
    chain_top: int,
    expected_subsets: int,
    expected_tried: int,
) -> None:
    """The module docstring's sum, counted at the exhaustive backend's own call.

    No padding recipe produces Relic, so no subset solves and the ascent runs to
    the end of the chain, which is the one shape that reaches the bound rather
    than stopping below it. The over-cap case is the one place the two counts the
    code could confuse differ: the chain's K against the usable count.
    """
    added = _padding(padding)
    registry = registry_with(add=added)
    request = _request(_added_keys(registry, added))
    usable, _notes = usable_candidates(registry, request)

    assert len(usable) == padding
    assert min(len(usable), MAX_EXHAUSTIVE_CANDIDATES) == chain_top

    evaluated: list[tuple[str, ...]] = []

    def spy(*args: Any, **kwargs: Any) -> OptimizeResult | None:
        """Record the selection, then evaluate it as the real function does.

        Args:
            *args: As ``evaluate_selection`` takes them.
            **kwargs: As ``evaluate_selection`` takes them.

        Returns:
            What ``evaluate_selection`` returns for them.
        """
        evaluated.append(tuple(args[2]))
        return evaluate_selection(*args, **kwargs)

    monkeypatch.setattr(exhaustive, "evaluate_selection", spy)

    with pytest.raises(BoundExhaustedError) as caught:
        optimize_within_bound(registry, request)

    subsets = len(evaluated)
    assert subsets == expected_subsets
    assert subsets == (1 << (chain_top + 1)) - 1
    assert caught.value.tried == expected_tried
    assert f"all {expected_tried} nested prefix(es) from size 0" in str(caught.value)


@pytest.mark.parametrize(
    ("backend", "policy"),
    [
        pytest.param(BACKEND_GREEDY, BYPRODUCT_BALANCED, id="greedy-balanced"),
        pytest.param(BACKEND_GREEDY, BYPRODUCT_SINKABLE, id="greedy-sinkable"),
        pytest.param(BACKEND_EXHAUSTIVE, BYPRODUCT_SINKABLE, id="exhaustive-sinkable"),
    ],
)
def test_no_targets_over_a_usable_set_answer_where_optimize_plan_crashes(
    corpus: Registry, backend: str, policy: str
) -> None:
    """The one request the bound answers and its door crashes on, as the docstring states.

    The empty plan is the right answer to a request for nothing, and the crash is
    pillar 1's. The ``raises`` half is deliberate: the day pillar 1 stops crashing
    it reddens, and that is when the module docstring's sentence has to go.
    """
    request = _request(
        (STD_GADGET_RECIPE,),
        targets=MappingProxyType({}),
        byproduct_policy=policy,
        config=SolveConfig(backend=backend),
    )

    with pytest.raises(ValueError, match=PILLAR_1_CRASH):
        optimize_plan(corpus, request)

    bounded = optimize_within_bound(corpus, request)

    assert bounded.chosen_size == EMPTY_PREFIX
    assert bounded.result.selection == ()
    assert bounded.result.plan.steps == ()
    assert bounded.record is None


@pytest.mark.parametrize("backend", BOTH_BACKENDS)
def test_a_power_refusal_propagates_rather_than_reading_as_not_this_prefix(backend: str) -> None:
    """A plan the objective cannot price is not a prefix with no plan.

    R_Reclaim names no building, so its draw has no value. S_0 refuses the target
    first, asserted directly, so this is reached at size one on both backends and
    the absorb has a real refusal in front of it.
    """
    registry = reclaim_registry()
    request = _request(
        (RECLAIM_RECIPE,),
        targets=MappingProxyType({SOLVE_PLATE_ITEM: RECLAIM_PLATE_TARGET}),
        raw_items=(SOLVE_RESIDUE_ITEM,),
        objective=weighted_objective(power=UNIT),
        config=SolveConfig(backend=backend),
    )

    with pytest.raises(NoFeasibleSelectionError):
        optimize_plan(registry, replace(request, candidates=()))

    with pytest.raises(PowerNotComparableError) as caught:
        optimize_within_bound(registry, request)

    assert caught.value.recipe_key == RECLAIM_RECIPE


def test_the_refusal_says_what_a_greedy_exhaustion_does_not_prove() -> None:
    """The message is true of each backend, on the fixture where they disagree.

    R_XCheap's byproduct has no consumer, so it cannot run under ``balanced``, and
    its relaxed probe is still the cheapest, so greedy commits to it and never
    reaches R_YDear on its own. Exhaustive finds R_YDear at size two: the plan a
    greedy refusal claiming "no plan exists" would be wrong about.
    """
    added = [
        _entry(
            BYPRODUCT_RELIC_RECIPE,
            [(SOLVE_ORE_ITEM, CHEAP_ORE_PER_CYCLE)],
            [(SOLVE_RELIC_ITEM, 1), (SOLVE_RARE_ITEM, 1)],
        ),
        _entry(
            DEAR_RELIC_RECIPE,
            [(SOLVE_ORE_ITEM, DIRECT_ORE_PER_CYCLE)],
            [(SOLVE_RELIC_ITEM, 1)],
        ),
    ]
    registry = registry_with(add=added)
    request = _request(_added_keys(registry, added))

    answered = optimize_within_bound(registry, request)

    assert answered.chosen_size == SECOND_PREFIX
    assert answered.result.selection == (DEAR_RELIC_RECIPE,)

    with pytest.raises(BoundExhaustedError) as caught:
        optimize_within_bound(
            registry, replace(request, config=SolveConfig(backend=BACKEND_GREEDY))
        )

    message = str(caught.value)
    assert caught.value.tried == SECOND_PREFIX + 1
    assert str(MAX_EXHAUSTIVE_CANDIDATES) in message
    assert TRIM_TARGET_PRODUCERS_FIRST in message
    assert "under the greedy backend, a heuristic, it is not proof that none exists" in message
    assert "this refusal's record names what the cap dropped" in message


@pytest.mark.parametrize("backend", BOTH_BACKENDS)
@pytest.mark.parametrize(
    "targets",
    [
        pytest.param({SOLVE_RELIC_ITEM: ZERO_RATE}, id="zero-target"),
        pytest.param({SOLVE_RELIC_ITEM: RELIC_TARGET}, id="nonzero-target"),
    ],
)
@pytest.mark.parametrize(
    ("candidates", "prefixes"),
    [
        pytest.param((), ONLY_THE_EMPTY_PREFIX, id="empty-usable-set"),
        pytest.param((STD_GADGET_RECIPE,), ONE_CANDIDATE_PREFIXES, id="one-usable-candidate"),
    ],
)
def test_an_unrecognized_policy_reads_as_exhaustion(
    corpus: Registry,
    candidates: tuple[str, ...],
    prefixes: int,
    targets: dict[str, Fraction],
    backend: str,
) -> None:
    """A shape bug that does not surface as one, stated in the docstring and pinned here.

    Pillar 1 refuses the policy with a RatioError, and ``optimize.solve_selection``
    reads every RatioError as "not this selection". So even all-zero targets do not
    stop at S_0: every prefix refuses, and the caller sees exhaustion.
    """
    request = _request(
        candidates,
        targets=MappingProxyType(targets),
        byproduct_policy=UNRECOGNIZED_POLICY,
        config=SolveConfig(backend=backend),
    )

    with pytest.raises(BoundExhaustedError) as caught:
        optimize_within_bound(corpus, request)

    assert caught.value.tried == prefixes


def test_an_unrecognized_policy_with_no_targets_reaches_pillar_1s_crash_under_greedy(
    corpus: Registry,
) -> None:
    """The one exception to the arm above, because greedy's probe ignores the policy.

    ``greedy._probe`` solves under the sinkable policy whatever the request says, so
    with S_0 refused the walk at size one reaches the same crash the door does.
    """
    request = _request(
        (STD_GADGET_RECIPE,),
        targets=MappingProxyType({}),
        byproduct_policy=UNRECOGNIZED_POLICY,
        config=SolveConfig(backend=BACKEND_GREEDY),
    )

    with pytest.raises(ValueError, match=PILLAR_1_CRASH):
        optimize_within_bound(corpus, request)


@pytest.mark.parametrize(
    ("overrides", "refusal"),
    [
        pytest.param(
            {"raw_items": (SOLVE_ORE_ITEM, SOLVE_RELIC_ITEM)},
            ValueError,
            id="raw-and-target",
        ),
        pytest.param(
            {"config": SolveConfig(backend=UNREGISTERED_BACKEND)},
            UnknownBackendError,
            id="unknown-backend",
        ),
        pytest.param(
            {"targets": MappingProxyType({SOLVE_RELIC_ITEM: INEXACT_RATE})},
            InexactValueError,
            id="inexact-target",
        ),
        pytest.param(
            {
                "targets": MappingProxyType({SOLVE_RELIC_ITEM: ZERO_RATE}),
                "objective": Objective(weights=MappingProxyType({})),
            },
            ObjectiveUndefinedError,
            id="undefined-objective",
        ),
    ],
)
def test_a_shape_refusal_on_an_empty_usable_set_surfaces_at_the_empty_prefix(
    corpus: Registry, overrides: dict[str, Any], refusal: type[Exception]
) -> None:
    """The function's Raises section, measured: S_0 asks, so these are no longer masked.

    Each of these read as exhaustion while the ascent asked nothing of an empty
    set. The exhaustion refusal is a subclass of none of them, so ``raises`` here
    cannot be satisfied by the old answer.
    """
    assert not issubclass(BoundExhaustedError, refusal)

    with pytest.raises(refusal):
        optimize_within_bound(corpus, _request((), **overrides))
