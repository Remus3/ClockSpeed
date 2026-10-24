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
that grade the ASCENT - :func:`test_the_chosen_prefix_is_the_smallest_that_passes`
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
from clockspeed.solve.backends import BACKEND_EXHAUSTIVE
from clockspeed.solve.bound import (
    TRIM_RULES,
    TRIM_TARGET_PRODUCERS_FIRST,
    BoundedResult,
    BoundExhaustedError,
    TrimRecord,
    TrimStep,
    optimize_within_bound,
)
from clockspeed.solve.exact import audit_exact
from clockspeed.solve.optimize import (
    MAX_EXHAUSTIVE_CANDIDATES,
    NoFeasibleSelectionError,
    Objective,
    OptimizeRequest,
    SolveConfig,
    optimize_plan,
    usable_candidates,
    weighted_objective,
)
from clockspeed.solve.ratio import BYPRODUCT_BALANCED
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
    SOLVE_ASSEMBLER_BUILDING,
    SOLVE_ORE_ITEM,
    SOLVE_RARE_ITEM,
    SOLVE_RELIC_ITEM,
    SOLVE_ROD_ITEM,
    SOLVE_TRINKET_ITEM,
    STD_GADGET_RECIPE,
    building_path,
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

    The size-one prefix is proved infeasible DIRECTLY, so an ascent starting at
    the wrong k reddens this rather than passing on a coincidence. The whole
    trimmed set then scores STRICTLY better than the answer returned, which is
    what proves the ascent stopped at the smallest passing prefix rather than
    taking the whole-set optimum - and both figures are the hand-derived
    absolutes above, not a second solver run compared against the first.
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


# ===========================================================================
# f. The closed rule vocabulary
# ===========================================================================


def test_the_trim_rule_vocabulary_is_closed_and_holds_the_shipped_rule() -> None:
    """A second rule cannot arrive unnamed: it has to join this tuple first."""
    assert isinstance(TRIM_RULES, tuple)
    assert TRIM_TARGET_PRODUCERS_FIRST in TRIM_RULES
    assert len(TRIM_RULES) == len(set(TRIM_RULES))
