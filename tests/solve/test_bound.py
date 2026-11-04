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
spawns two children under PYTHONHASHSEED 0 and 1 and compares their stdout, and
:func:`test_two_processes_rank_one_route_under_different_hash_seeds` does the same
for the ranking itself.

WHY EVERY ROUTE AND EVERY RANKING BELOW IS WRITTEN OUT BY HAND
---------------------------------------------------------------
``clockspeed/solve/bound.py::_trim_ranking`` is the subject of CS-1372, so an
expected order read back from it, or from anything built on it, passes whatever it
returns. Each one here is a literal, derived in its fixture's comment from the
recipes alone, and the shipped order and a keep by walk depth are written out the
same way, because no code path computes either of them any more.

NO TOLERANCE, AND EQUALITY IS NOT ENOUGH ON ITS OWN
-----------------------------------------------------
``tests/solve/__init__.py`` binds this file: no ``pytest.approx``, no
``math.isclose``, no epsilon. Score assertions are paired with
``type(x) is Fraction`` and with ``audit_exact`` over the whole returned value,
because ``Fraction(1, 2) == 0.5`` is True.
"""

from __future__ import annotations

import json
import subprocess
import sys
from collections.abc import Callable, Iterator
from dataclasses import FrozenInstanceError, replace
from fractions import Fraction
from pathlib import Path
from types import MappingProxyType
from typing import Any, Final

import pytest

from clockspeed.advisor.plans import PlanRequest, plan_offer
from clockspeed.data.registry import Registry, build_registry
from clockspeed.save.world import EMPTY_UNLOCK_STATE
from clockspeed.solve import bound
from clockspeed.solve import optimize as optimize_module
from clockspeed.solve.backends import BACKEND_EXHAUSTIVE, BACKEND_GREEDY, exhaustive
from clockspeed.solve.bound import (
    TRIM_ROUTE_FIRST,
    TRIM_RULES,
    TRIM_TARGET_PRODUCERS_FIRST,
    BoundedResult,
    BoundExhaustedError,
    DerivedRoute,
    TrimRecord,
    TrimStep,
    derived_route,
    optimize_within_bound,
)
from clockspeed.solve.exact import InexactValueError, audit_exact
from clockspeed.solve.optimize import (
    MAX_EXHAUSTIVE_CANDIDATES,
    OBJECTIVE_RAW,
    OBJECTIVES,
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
from clockspeed.solve.ratio import BYPRODUCT_BALANCED, BYPRODUCT_POLICIES, BYPRODUCT_SINKABLE
from tests.data.synthetic import (
    KEY_CLASS_NAME,
    KEY_CLASSES,
    KEY_DISPLAY_NAME,
    KEY_DURATION,
    KEY_FORM,
    KEY_FULL_NAME,
    KEY_INGREDIENTS,
    KEY_NATIVE_CLASS,
    KEY_PRODUCED_IN,
    KEY_PRODUCT,
    amount_blob,
    class_path_blob,
)
from tests.solve.synthetic import (
    ALT_GADGET_RECIPE,
    C3_GADGET_TARGET,
    C5_TRINKET_TARGET,
    DOCS_TEXT,
    FLUID_RECIPE,
    GADGET_RECIPE,
    ITEM_GROUP,
    MACHINE_BUILD_PATHS,
    ORPHAN_RECIPE,
    PLATE_RECIPE,
    RECIPE_GROUP,
    RECLAIM_RECIPE,
    RECOVER_RECIPE,
    SOLVE_ASSEMBLER_BUILDING,
    SOLVE_FLUID_ITEM,
    SOLVE_GADGET_ITEM,
    SOLVE_ORE_ITEM,
    SOLVE_ORPHAN_ITEM,
    SOLVE_PLATE_ITEM,
    SOLVE_RARE_ITEM,
    SOLVE_RECIPES,
    SOLVE_RELIC_ITEM,
    SOLVE_RESIDUE_ITEM,
    SOLVE_ROD_ITEM,
    SOLVE_TRINKET_ITEM,
    SOLVE_TWIN_ITEM,
    STD_GADGET_RECIPE,
    ZERO_DURATION_RECIPE,
    building_path,
    document_from_groups,
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
#: them makes anything a request here walks back to - which is what ranks them
#: last, by registry position, in the trim rule's EVERYTHING ELSE tier.
PADDING_PREFIX: Final = "R_Pad"

#: Six seconds per cycle for every hand-built recipe. One duration across the
#: fixture means a score difference can only come from the arithmetic under
#: test and never from a cycle time.
FIXTURE_DURATION: Final = "6.000000"

#: The ascent fixture's two-stage Relic recipe, declared FIRST of the three. It
#: consumes Rare, so its count is two and the one-stage recipe's one, and the route
#: is that one stage whatever the registry order says.
RELIC_FROM_RARE_RECIPE: Final = "R_B1Relic"

#: The one-stage route: Relic straight from Ore, feasible ALONE and expensive.
RELIC_FROM_ORE_RECIPE: Final = "R_B2Direct"

#: The second stage of the cheap route. It produces Rare, which is no target, so
#: the trim rule ranks it behind both Relic producers: walk depth one against zero.
RARE_RECIPE: Final = "R_B3Rare"

#: The route's second stage in the fixture whose route takes two prefixes to build:
#: Rare straight from Ore, expensive, and a count of one against the detour's two.
DEAR_RARE_RECIPE: Final = "R_B2DearRare"

#: The cheap detour past :data:`DEAR_RARE_RECIPE`: Rare from Rod, then Rod from Ore.
RARE_FROM_ROD_RECIPE: Final = "R_B3RareFromRod"
ROD_FROM_ORE_RECIPE: Final = "R_B4Rod"

#: The only Relic producer in the late-producer fixture, declared LAST so that a
#: registry-order trim would drop it.
LATE_PRODUCER_RECIPE: Final = "R_ZLateProducer"

#: Ore per cycle for each fixture's expensive one-stage recipe, and for the cheap
#: route's own stages. The gap is what makes the whole-set optimum STRICTLY
#: better than the size-two prefix's.
DIRECT_ORE_PER_CYCLE: Final = 6
CHEAP_ORE_PER_CYCLE: Final = 1

#: Ore per cycle for the Relic producer that sits LAST in registry order.
LATE_PRODUCER_ORE_PER_CYCLE: Final = 2

#: Hand-derived absolutes for the two-prefix fixture, at 10 Relic/min.
#:
#: The route is R_B1Relic and R_B2DearRare, and alone it buys 10 Rare/min at six Ore
#: each: 60 Ore/min. The whole trimmed set also holds the detour, which runs at one
#: Ore per Rare: 10 Ore/min. Both figures come from the recipe arithmetic above and
#: from no solver.
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

#: How many the two-prefix fixture hand-builds before its padding.
TWO_PREFIX_HAND_BUILT: Final = 4

#: The cap CS-1372 is graded against, spelled here so that moving it is red here.
PINNED_CAP: Final = 12

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

#: The prefix sizes the ascent asks about on C5, by hand. Rare has no producer, so
#: Alt_Gadget never counts and Std_Gadget alone is the route. S_0 refuses the target,
#: S_1 is Std_Gadget and solves, the second prefix asked.
C5_ASCENT_SIZES: Final[list[int]] = [0, 1]

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

#: What each child of the route determinism arm prints. Never a plan: the ranking,
#: the route and the record, on a fixture of two targets and many distinct items, so
#: a set deciding any order of items or recipes has something to reorder.
ROUTE_CHILD_SOURCE: Final = """
from clockspeed.solve import bound
from tests.solve.test_bound import two_target_registry, two_target_request

registry, request = two_target_registry(), two_target_request()
print(repr(bound._trim_ranking(registry, request)))
print(repr(bound.derived_route(registry, request)))
print(repr(bound.trim_record(registry, request)))
"""

#: CS-1372's chain, four stages, every cycle six seconds and every amount one, so
#: 10 Relic a minute runs one machine a stage and draws 10 Ore a minute. Read from
#: the top: Relic from Rare, Rare from Rod, Rod from Plate, Plate from Ore.
CHAIN_RELIC_RECIPE: Final = "R_ChainRelic"
CHAIN_ROD_RECIPE: Final = "R_ChainRod"
CHAIN_PLATE_RECIPE: Final = "R_ChainPlate"

#: The two producers of the chain's Rare, in registry order. Only the second can
#: run: the first eats Twin, whose only makers eat Orphan, which nothing makes.
CHAIN_RARE_FIRST_RECIPE: Final = "R_ChainRareFirst"
CHAIN_RARE_SECOND_RECIPE: Final = "R_ChainRareSecond"

#: The Twin makers, each 1 Orphan to 1 Twin. Off the route and inside the closure.
DECOY_PREFIX: Final = "R_Decoy"
DECOY_COUNT: Final = 12

#: The usable count of that fixture: twelve decoys and five chain recipes.
CLOSURE_USABLE: Final = 17

#: The derived route, by hand, in walk order. Relic has one producer. Rare's first
#: producer never counts, because Twin never does, so Rare takes its second. Rod and
#: Plate have one each, and Ore is raw. NEVER read back from the ranking.
CHAIN_ROUTE: Final[tuple[str, ...]] = (
    CHAIN_RELIC_RECIPE,
    CHAIN_RARE_SECOND_RECIPE,
    CHAIN_ROD_RECIPE,
    CHAIN_PLATE_RECIPE,
)

#: The chain's own recipes in registry order, which is how a selection reads.
CHAIN_SELECTION: Final[tuple[str, ...]] = (
    CHAIN_RARE_SECOND_RECIPE,
    CHAIN_ROD_RECIPE,
    CHAIN_PLATE_RECIPE,
    CHAIN_RELIC_RECIPE,
)

#: What the shipped order keeps, by hand: the one direct producer of Relic, then
#: registry order, which is decoys first. It loses Rare's second producer, Rod's
#: and Plate's.
SHIPPED_ORDER_KEEP: Final[tuple[str, ...]] = (
    CHAIN_RELIC_RECIPE,
    *(f"{DECOY_PREFIX}{index}" for index in range(11)),
)

#: What a keep by walk depth then registry position holds, by hand: depth 0 is
#: Relic's producer, depth 1 Rare's two, and depth 2 is the twelve decoys and then
#: R_ChainRod by registry position. It loses Rod's producer and Plate's.
DEPTH_ORDER_KEEP: Final[tuple[str, ...]] = (
    CHAIN_RELIC_RECIPE,
    CHAIN_RARE_FIRST_RECIPE,
    CHAIN_RARE_SECOND_RECIPE,
    *(f"{DECOY_PREFIX}{index}" for index in range(9)),
)

#: What the route-first keep holds, by hand, in registry order: the four of the
#: route, Rare's dead first producer at depth 1, then decoys 0 to 6 at depth 2.
ROUTE_ORDER_KEPT: Final[tuple[str, ...]] = (
    *(f"{DECOY_PREFIX}{index}" for index in range(7)),
    CHAIN_RARE_FIRST_RECIPE,
    *CHAIN_SELECTION,
)

#: What the route-first keep drops, by hand: decoys 7 to 11.
ROUTE_ORDER_REMOVED: Final[tuple[str, ...]] = tuple(
    f"{DECOY_PREFIX}{index}" for index in range(7, DECOY_COUNT)
)

#: Ore a minute for that chain at 10 Relic a minute, from the arithmetic above.
CHAIN_ORE_PER_MINUTE: Final[Fraction] = Fraction(10)


def _entry(
    class_name: str,
    ingredients: list[tuple[str, int]],
    products: list[tuple[str, int]],
    *,
    path: str | None = None,
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
        path: The path half of its FullName, or None to carry none, for the one
            arm that reaches the unlock join.

    Returns:
        The entry mapping, every value a string as in the real document.
    """
    entry = {
        KEY_CLASS_NAME: class_name,
        KEY_DISPLAY_NAME: class_name.removeprefix("R_"),
        KEY_DURATION: FIXTURE_DURATION,
        KEY_INGREDIENTS: amount_blob(ingredients),
        KEY_PRODUCT: amount_blob(products),
        KEY_PRODUCED_IN: class_path_blob([building_path(SOLVE_ASSEMBLER_BUILDING)]),
    }
    if path is not None:
        entry[KEY_FULL_NAME] = f"BlueprintGeneratedClass {path}"
    return entry


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

    By hand, the ranking is R_B2Direct, the whole route with a count of one against
    R_B1Relic's two; R_B1Relic at walk depth zero; R_B3Rare at walk depth one; then
    the padding by registry position. So the cheap two stages enter the search only
    ABOVE the prefix size an ascent over this fixture stops at, and the one dropped
    past the cap is the last filler.

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


def _two_prefix_entries() -> list[dict[str, str]]:
    """A route of two stages, a cheaper detour behind it, and padding past the cap.

    By hand, Relic's one producer is R_B1Relic. Rare's count is one through
    R_B2DearRare and two through the detour, so the route is those two, in that
    order: the first prefix cannot solve and the second can. The detour follows at walk
    depths one and two, R_B4Rod declared ahead of the padding that makes Rod at the same
    depth, so only a later prefix holds the cheap plan.

    Returns:
        The entries, in the order they take in registry order.
    """
    return [
        _entry(RELIC_FROM_RARE_RECIPE, [(SOLVE_RARE_ITEM, 1)], [(SOLVE_RELIC_ITEM, 1)]),
        _entry(DEAR_RARE_RECIPE, [(SOLVE_ORE_ITEM, DIRECT_ORE_PER_CYCLE)], [(SOLVE_RARE_ITEM, 1)]),
        _entry(RARE_FROM_ROD_RECIPE, [(SOLVE_ROD_ITEM, 1)], [(SOLVE_RARE_ITEM, 1)]),
        _entry(ROD_FROM_ORE_RECIPE, [(SOLVE_ORE_ITEM, CHEAP_ORE_PER_CYCLE)], [(SOLVE_ROD_ITEM, 1)]),
        *_padding(MAX_EXHAUSTIVE_CANDIDATES + PADDING_OVER_CAP - TWO_PREFIX_HAND_BUILT),
    ]


def _late_producer_entries() -> list[dict[str, str]]:
    """Padding filling the whole cap, then the ONLY Relic producer, last.

    The shape that grades the route ranking ahead of registry order. In registry
    order the producer is the final member, so a trim that kept the first
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


def _path_of(class_name: str) -> str:
    """An invented asset path for one chain fixture recipe.

    Args:
        class_name: The recipe's ClassName.

    Returns:
        The path. The join compares it whole, so its shape carries no claim.
    """
    return f"/Game/FactoryGame/Synthetic/Chain/{class_name}.{class_name}_C"


def _closure_entries() -> list[dict[str, str]]:
    """The four-stage chain inside a closure of seventeen, every member usable.

    Every recipe is one in, one out, six seconds. Declared decoys first, so registry
    order is the worst order for the route, and the dead producer of Rare ahead of the
    live one, so a walk taking an item's first producer dead-ends.

    Returns:
        The entries, in the order they take in registry order.
    """
    chain: list[tuple[str, str, str]] = [
        *(
            (f"{DECOY_PREFIX}{index}", SOLVE_ORPHAN_ITEM, SOLVE_TWIN_ITEM)
            for index in range(DECOY_COUNT)
        ),
        (CHAIN_RARE_FIRST_RECIPE, SOLVE_TWIN_ITEM, SOLVE_RARE_ITEM),
        (CHAIN_RARE_SECOND_RECIPE, SOLVE_ROD_ITEM, SOLVE_RARE_ITEM),
        (CHAIN_ROD_RECIPE, SOLVE_PLATE_ITEM, SOLVE_ROD_ITEM),
        (CHAIN_PLATE_RECIPE, SOLVE_ORE_ITEM, SOLVE_PLATE_ITEM),
        (CHAIN_RELIC_RECIPE, SOLVE_RARE_ITEM, SOLVE_RELIC_ITEM),
    ]
    return [
        _entry(name, [(eaten, 1)], [(made, 1)], path=_path_of(name)) for name, eaten, made in chain
    ]


def closure_registry() -> Registry:
    """Build CS-1372's chain fixture, the corpus's own recipes dropped.

    Public because a child process of the determinism arm imports it.

    Returns:
        The variant registry.
    """
    return registry_with(add=_closure_entries(), drop=frozenset(SOLVE_RECIPES))


def closure_request() -> OptimizeRequest:
    """Build the chain fixture's request, over every recipe, every one unlocked.

    Public for the same reason as :func:`closure_registry`.

    Returns:
        The request.
    """
    return _request(tuple(entry[KEY_CLASS_NAME] for entry in _closure_entries()))


def _one_each(name: str, eaten: tuple[str, ...], made: tuple[str, ...]) -> dict[str, str]:
    """One recipe taking one of each item it eats, making one of each item it makes.

    Args:
        name: The ClassName.
        eaten: The input items, in the order they are listed.
        made: The output items, in the order they are listed.

    Returns:
        The entry.
    """
    return _entry(name, [(item, 1) for item in eaten], [(item, 1) for item in made])


def _bare_registry(entries: list[dict[str, str]]) -> Registry:
    """A registry holding exactly these recipes, so nothing else can be asked about.

    Args:
        entries: The recipe entries.

    Returns:
        The registry.
    """
    return registry_with(add=entries, drop=frozenset(SOLVE_RECIPES))


def _route_request(entries: list[dict[str, str]], *items: str, **overrides: Any) -> OptimizeRequest:
    """A request over every recipe named, for these targets at any positive rate.

    Args:
        entries: The recipe entries, every one a candidate and unlocked.
        *items: The target items. Relic alone, when none is named.
        **overrides: Fields to replace.

    Returns:
        The request.
    """
    wanted = dict.fromkeys(items or (SOLVE_RELIC_ITEM,), RELIC_TARGET)
    base = _request(
        tuple(entry[KEY_CLASS_NAME] for entry in entries), targets=MappingProxyType(wanted)
    )
    return replace(base, **overrides) if overrides else base


def _route_of(entries: list[dict[str, str]], *items: str, **overrides: Any) -> DerivedRoute:
    """The derived route of a bare registry of these recipes.

    Args:
        entries: The recipe entries.
        *items: The target items, as :func:`_route_request` takes them.
        **overrides: Fields to replace on the request.

    Returns:
        The route.
    """
    return derived_route(_bare_registry(entries), _route_request(entries, *items, **overrides))


def _ranking(registry: Registry, request: OptimizeRequest) -> tuple[str, ...]:
    """The trim's whole ranking, where ``trim_record`` shows only the cut through it.

    Args:
        registry: The registry.
        request: The request.

    Returns:
        Every usable candidate, ranked.
    """
    return bound._trim_ranking(registry, request)  # noqa: SLF001 - the seam under test


def _two_target_entries() -> list[dict[str, str]]:
    """Two targets over many distinct items, declared so no order agrees with another.

    By hand, Relic sorts ahead of Trinket, so the walk reads R_TopRelic, R_TopTrinket,
    then R_TopRelic's inputs as listed, Rod before Plate, then R_TopTrinket's, Gadget
    and Twin, then Rod's input, Rare. R_DeadRelic is at walk depth zero with no count,
    since nothing makes Orphan. R_DearRod is Rod's second maker at a count of three
    against R_MakeRod's two. R_Off makes Residue, which nothing on the walk reads.

    Returns:
        The entries, in the order they take in registry order.
    """
    return [
        _one_each("R_Off", (SOLVE_ORE_ITEM,), (SOLVE_RESIDUE_ITEM,)),
        _one_each("R_MakeRare", (SOLVE_ORE_ITEM,), (SOLVE_RARE_ITEM,)),
        _one_each("R_MakeTwin", (SOLVE_ORE_ITEM,), (SOLVE_TWIN_ITEM,)),
        _one_each("R_MakeGadget", (SOLVE_ORE_ITEM,), (SOLVE_GADGET_ITEM,)),
        _one_each("R_DearRod", (SOLVE_RARE_ITEM, SOLVE_RARE_ITEM), (SOLVE_ROD_ITEM,)),
        _one_each("R_MakeRod", (SOLVE_RARE_ITEM,), (SOLVE_ROD_ITEM,)),
        _one_each("R_MakePlate", (SOLVE_ORE_ITEM,), (SOLVE_PLATE_ITEM,)),
        _one_each("R_DeadRelic", (SOLVE_ORPHAN_ITEM,), (SOLVE_RELIC_ITEM,)),
        _one_each("R_TopTrinket", (SOLVE_GADGET_ITEM, SOLVE_TWIN_ITEM), (SOLVE_TRINKET_ITEM,)),
        _one_each("R_TopRelic", (SOLVE_ROD_ITEM, SOLVE_PLATE_ITEM), (SOLVE_RELIC_ITEM,)),
    ]


#: That fixture's route, by hand, from its docstring.
TWO_TARGET_ROUTE: Final[tuple[str, ...]] = (
    "R_TopRelic",
    "R_TopTrinket",
    "R_MakeRod",
    "R_MakePlate",
    "R_MakeGadget",
    "R_MakeTwin",
    "R_MakeRare",
)

#: That fixture's whole ranking, by hand: the route, then the closure by walk depth,
#: R_DeadRelic at zero and R_DearRod at one, then R_Off.
TWO_TARGET_RANKING: Final[tuple[str, ...]] = (
    *TWO_TARGET_ROUTE,
    "R_DeadRelic",
    "R_DearRod",
    "R_Off",
)


def two_target_registry() -> Registry:
    """The two-target fixture's registry.

    Public because :data:`ROUTE_CHILD_SOURCE` imports it.

    Returns:
        The registry.
    """
    return _bare_registry(_two_target_entries())


def two_target_request() -> OptimizeRequest:
    """The two-target fixture's request, Relic and Trinket.

    Public for the same reason as :func:`two_target_registry`.

    Returns:
        The request.
    """
    return _route_request(_two_target_entries(), SOLVE_RELIC_ITEM, SOLVE_TRINKET_ITEM)


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
    assert step.rule == TRIM_ROUTE_FIRST
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
    still present, because it describes the ascent rather than the trim: by hand
    Rare has no producer, so Alt_Gadget never counts, Std_Gadget alone is the route
    and ranks first although Alt_Gadget is declared ahead of it, and that first
    prefix solves.
    """
    candidates = (ALT_GADGET_RECIPE, STD_GADGET_RECIPE)
    request = _request(
        candidates, targets=MappingProxyType({SOLVE_TRINKET_ITEM: C5_TRINKET_TARGET})
    )
    usable, _notes = usable_candidates(corpus, request)

    assert len(usable) < MAX_EXHAUSTIVE_CANDIDATES

    bounded = optimize_within_bound(corpus, request)

    assert bounded.record is None
    assert bounded.chosen_size == FIRST_PREFIX
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

    Rebuilt under CS-1372 on a route of two stages, because the ascent fixture's route
    is now one recipe, which solves at the first prefix and leaves no infeasible prefix
    above S_0 to grade. The size-one prefix is proved infeasible DIRECTLY, so size two
    is the smallest that passes by measurement rather than by coincidence, and an
    ascent starting ABOVE size two reddens this. One starting at size one stays green
    here, because S_0 refuses this target too:
    :func:`test_the_ascent_visits_the_empty_prefix_first_on_every_request` is the
    arm that grades the start. The whole trimmed set then scores STRICTLY better
    than the answer returned, which is what proves the ascent stopped at the
    smallest passing prefix rather than taking the whole-set optimum - and both
    figures are the hand-derived absolutes above, not a second solver run compared
    against the first.
    """
    added = _two_prefix_entries()
    registry = _bare_registry(added)
    request = _route_request(added)
    bounded = optimize_within_bound(registry, request)
    record = bounded.record
    assert record is not None

    assert bounded.chosen_size == SECOND_PREFIX
    assert bounded.result.selection == (RELIC_FROM_RARE_RECIPE, DEAR_RARE_RECIPE)
    assert bounded.result.score == PREFIX_TWO_ORE_PER_MINUTE
    assert type(bounded.result.score) is Fraction

    # The size-one prefix really is infeasible, asserted directly.
    with pytest.raises(NoFeasibleSelectionError):
        optimize_plan(registry, replace(request, candidates=(RELIC_FROM_RARE_RECIPE,)))

    whole = optimize_plan(registry, replace(request, candidates=record.first.kept))

    assert whole.score == WHOLE_SET_ORE_PER_MINUTE
    assert whole.selection == (RELIC_FROM_RARE_RECIPE, RARE_FROM_ROD_RECIPE, ROD_FROM_ORE_RECIPE)
    assert whole.score < bounded.result.score


def test_a_target_producer_last_in_registry_order_survives_the_trim() -> None:
    """The route outranking registry order, graded by the answer it makes possible.

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
    assert TRIM_ROUTE_FIRST in message
    assert caught.value.rule == TRIM_ROUTE_FIRST


def test_the_refusal_is_a_no_plan_refusal_a_caller_already_handles(corpus: Registry) -> None:
    """``LadderExhaustedError``'s precedent: a caller handling "no plan" needs no edit."""
    assert issubclass(BoundExhaustedError, NoFeasibleSelectionError)

    with pytest.raises(NoFeasibleSelectionError):
        optimize_within_bound(corpus, _request((ORPHAN_RECIPE,)))


def test_a_refusal_over_the_cap_carries_what_the_bound_dropped() -> None:
    """CS-1351: a no-plan is about the kept set, so what the cap dropped travels with it.

    Fourteen fillers, none making Relic, so the walk from Relic finds nothing, all
    fourteen rank as everything else and registry position alone decides: the cap of
    twelve keeps R_Pad0 to R_Pad11. Named by hand, never read back from the ranking.
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
    assert record.first.rule == TRIM_ROUTE_FIRST
    assert caught.value.rule == TRIM_ROUTE_FIRST
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
    bare = BoundExhaustedError(MAX_EXHAUSTIVE_CANDIDATES, TRIM_ROUTE_FIRST, 1, "m")

    assert bare.record is None
    record = TrimRecord(
        steps=(
            TrimStep(
                rule=TRIM_ROUTE_FIRST,
                cap=MAX_EXHAUSTIVE_CANDIDATES,
                kept=("R_Kept",),
                removed=("R_Dropped",),
            ),
        )
    )
    held = BoundExhaustedError(MAX_EXHAUSTIVE_CANDIDATES, TRIM_ROUTE_FIRST, 1, "m", record=record)
    assert held.record is record
    with pytest.raises(TypeError):
        BoundExhaustedError(  # type: ignore[misc]
            MAX_EXHAUSTIVE_CANDIDATES, TRIM_ROUTE_FIRST, 1, "m", record
        )


def test_trim_record_says_what_the_cap_drops_before_any_search(
    corpus: Registry, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A rule over the request and the registry, so it stays true whichever refusal ends one."""
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
    """A second rule cannot arrive unnamed: it has to join this tuple first.

    The shipped name stays a member although CS-1372 stopped emitting it, and the new
    rule joined behind it. Spelled as a literal, so a renamed rule is red here.
    """
    assert isinstance(TRIM_RULES, tuple)
    assert TRIM_RULES == ("target-producers-first", "route-first")
    assert TRIM_TARGET_PRODUCERS_FIRST in TRIM_RULES
    assert TRIM_ROUTE_FIRST in TRIM_RULES
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
    assert bounded.chosen_size == FIRST_PREFIX
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
    assert TRIM_ROUTE_FIRST in message
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


# ===========================================================================
# h. The route-first order - CS-1372
# ===========================================================================


def test_a_derived_route_inside_a_closure_over_the_cap_ranks_a_plan() -> None:
    """CS-1372 arm 1: the bound returns a plan and plan_offer reads it as ranked.

    The route is named by hand above. Both rejected orders are named by hand too, and
    each is run through ``optimize_plan`` first: a keep losing a route member over this
    fixture is a no-plan by measurement rather than in prose, and that no-plan is the
    defect this arm reddens on.
    """
    registry = closure_registry()
    request = closure_request()
    usable, _notes = usable_candidates(registry, request)

    assert len(usable) == CLOSURE_USABLE
    assert len(usable) > MAX_EXHAUSTIVE_CANDIDATES
    assert len(CHAIN_ROUTE) <= MAX_EXHAUSTIVE_CANDIDATES
    assert registry.warnings == ()

    for rejected_keep in (SHIPPED_ORDER_KEEP, DEPTH_ORDER_KEEP):
        assert len(rejected_keep) == MAX_EXHAUSTIVE_CANDIDATES
        assert not set(CHAIN_ROUTE) <= set(rejected_keep)
        with pytest.raises(NoFeasibleSelectionError):
            optimize_plan(registry, replace(request, candidates=rejected_keep))

    bounded = optimize_within_bound(registry, request)

    assert bounded.chosen_size == len(CHAIN_ROUTE)
    assert bounded.result.selection == CHAIN_SELECTION
    assert bounded.result.score == CHAIN_ORE_PER_MINUTE
    assert type(bounded.result.score) is Fraction
    assert bounded.result.plan.raw_inputs[SOLVE_ORE_ITEM] == CHAIN_ORE_PER_MINUTE
    assert bounded.record is not None
    assert bounded.record.first.kept == ROUTE_ORDER_KEPT
    assert bounded.record.first.removed == ROUTE_ORDER_REMOVED
    audit_exact(bounded, path="bounded")

    # The same chain beside every machine's build recipe, which the unlock join reads and the
    # bound does not. Its one warning is the build gun's, so the pin above stays on the rest.
    with_machines = registry_with(
        add=_closure_entries(), drop=frozenset(SOLVE_RECIPES), machine_builds=True
    )
    offered = plan_offer(
        replace(
            EMPTY_UNLOCK_STATE,
            recipes=frozenset((*(_path_of(name) for name in usable), *MACHINE_BUILD_PATHS)),
        ),
        with_machines,
        PlanRequest(
            targets=MappingProxyType({SOLVE_RELIC_ITEM: RELIC_TARGET}),
            raw_items=(SOLVE_ORE_ITEM,),
            byproduct_policy=BYPRODUCT_BALANCED,
            direction=OBJECTIVE_RAW,
        ),
    )

    assert offered["plan.status"].value == "ranked"
    assert offered["plan.trimmed"].value == ROUTE_ORDER_REMOVED


def test_the_cap_does_not_move() -> None:
    """CS-1372 arm 2: the order changes what is kept and never how many."""
    assert MAX_EXHAUSTIVE_CANDIDATES == PINNED_CAP


def test_the_published_seam_is_public_and_its_route_is_frozen() -> None:
    """The names another module may read, and the shape it reads them in."""
    for name in ("TRIM_ROUTE_FIRST", "DerivedRoute", "derived_route"):
        assert name in bound.__all__

    route = DerivedRoute(members=(), complete=True, unmade=())
    with pytest.raises(FrozenInstanceError):
        route.complete = False  # type: ignore[misc]


def test_the_chain_fixtures_route_and_its_gaps_are_the_hand_derived_ones() -> None:
    """The arm 1 fixture's route, read through the public function.

    Orphan is the one item the closure reaches that nothing makes and raw items lack.
    Twin is made, by recipes that can never run, so it has no count and is not unmade.
    """
    route = derived_route(closure_registry(), closure_request())

    assert route == DerivedRoute(members=CHAIN_ROUTE, complete=True, unmade=(SOLVE_ORPHAN_ITEM,))
    assert type(route.members) is tuple
    assert type(route.unmade) is tuple
    assert route.complete is True


def _walk_item(name: str) -> str:
    """One invented item of the walk fixtures.

    Args:
        name: The item's short name.

    Returns:
        Its ClassName.
    """
    return f"Desc_Walk{name}_C"


def _walk_registry(entries: list[dict[str, str]], items: tuple[str, ...]) -> Registry:
    """A registry holding exactly these recipes, each invented item given a descriptor.

    Args:
        entries: The recipe entries, replacing the corpus's own.
        items: The invented items, by short name.

    Returns:
        The registry, through the same text seam the corpus uses, with no warning.
    """
    groups = json.loads(DOCS_TEXT)
    for group in groups:
        native_class = group[KEY_NATIVE_CLASS]
        if native_class.endswith(f".{ITEM_GROUP}'"):
            group[KEY_CLASSES].extend(
                {
                    KEY_CLASS_NAME: _walk_item(item),
                    KEY_DISPLAY_NAME: item,
                    KEY_FORM: "RF_SOLID",
                }
                for item in items
            )
        elif native_class.endswith(f".{RECIPE_GROUP}'"):
            group[KEY_CLASSES] = entries
    return build_registry(document_from_groups(groups))


def _revisited_entries() -> list[dict[str, str]]:
    """A recipe the walk reaches at level zero and again at level eleven.

    R_X makes the target, and Y beside it, and Y feeds the long way back to the target
    through R_D10, R_D9 and on down to R_Alt, so the walk comes to R_X again as Y's maker.

    Returns:
        The entries, in the order they take in registry order.
    """
    item = _walk_item
    return [
        _one_each("R_Top", (item("A"), item("B")), (item("T"),)),
        _entry("R_A", [(SOLVE_ORE_ITEM, 1)], [(item("A"), 1), (item("B"), 2)]),
        _one_each("R_X", (item("B"), item("C")), (item("T"), item("Y"))),
        _one_each("R_C", (SOLVE_ORE_ITEM,), (item("C"),)),
        _one_each("R_Alt", (item("D1"),), (item("T"),)),
        *(
            _one_each(f"R_D{level}", (item(f"D{level + 1}"),), (item(f"D{level}"),))
            for level in range(1, 10)
        ),
        _one_each("R_D10", (item("Y"),), (item("D10"),)),
    ]


#: The items of :func:`_revisited_entries`, by short name.
REVISITED_ITEMS: Final = ("T", "A", "B", "C", "Y", *(f"D{level}" for level in range(1, 11)))

#: The target of every walk fixture, by short name.
WALK_TARGET: Final = "T"

#: Its whole ranking, by hand. The count ties R_Top and R_X at three recipes and registry
#: position gives R_Top, whose inputs are both R_A's, so the route is those two. Then the
#: closure by level: R_X and R_Alt at zero, the target's other makers, kept at zero though the
#: walk comes back to R_X as Y's maker; R_C and R_D1 at one; each next R_D a level down, to
#: R_D10 at ten.
REVISITED_RANKING: Final = (
    "R_Top",
    "R_A",
    "R_X",
    "R_Alt",
    "R_C",
    *(f"R_D{level}" for level in range(1, 11)),
)


#: The first prefix of that ranking that solves, by hand: the first to hold R_X and R_C.
REVISITED_PREFIX: Final = 5


def _level_tie_entries() -> list[dict[str, str]]:
    """Two makers on one level, the item walked first declared second.

    Returns:
        The entries, in the order they take in registry order.
    """
    item = _walk_item
    return [
        _one_each("R_Top", (SOLVE_ORE_ITEM,), (item("T"),)),
        _one_each("R_Dead", (item("X"), item("Y")), (item("T"),)),
        _one_each("R_MakeY", (SOLVE_ORPHAN_ITEM,), (item("Y"),)),
        _one_each("R_MakeX", (SOLVE_ORPHAN_ITEM,), (item("X"),)),
    ]


def _loop_entries() -> list[dict[str, str]]:
    """A loop no raw item enters, its level order against its registry order.

    Returns:
        The entries, in the order they take in registry order.
    """
    item = _walk_item
    return [
        _one_each("R_Top", (item("Mid"),), (item("T"),)),
        _one_each("R_Mid", (SOLVE_ORE_ITEM,), (item("Mid"),)),
        _one_each("R_Both", (SOLVE_ORE_ITEM, item("Rare")), (item("T"), item("Plate"))),
        _one_each("R_Plate", (item("Rare"),), (item("Plate"),)),
        _one_each("R_RareA", (item("Plate"),), (item("Rare"),)),
    ]


@pytest.mark.parametrize(
    ("entries", "items", "ranking"),
    [
        (_revisited_entries, REVISITED_ITEMS, REVISITED_RANKING),
        # R_Top is the route, and R_Dead the target's other maker, with no count. X and Y are one
        # level, so registry position decides between their makers, whichever the walk read first.
        (_level_tie_entries, ("T", "X", "Y"), ("R_Top", "R_Dead", "R_MakeY", "R_MakeX")),
        # R_Top and R_Mid are the route. R_Both is the target's other maker, at level zero, kept
        # there though it makes Plate too. R_RareA makes Rare at level one and R_Plate makes Plate
        # at level two, so the level orders them against their registry position.
        (
            _loop_entries,
            ("T", "Mid", "Rare", "Plate"),
            ("R_Top", "R_Mid", "R_Both", "R_RareA", "R_Plate"),
        ),
    ],
    ids=["revisited-recipe", "two-makers-on-one-level", "loop-behind-the-route"],
)
def test_the_closure_ranks_a_recipe_at_the_level_the_walk_first_reached_it(
    entries: Callable[[], list[dict[str, str]]], items: tuple[str, ...], ranking: tuple[str, ...]
) -> None:
    """The ranking's closure half, each ranking named by hand and never read back."""
    built = entries()
    registry = _walk_registry(built, items)

    assert registry.warnings == ()
    request = _route_request(built, _walk_item(WALK_TARGET))
    assert _ranking(registry, request) == ranking


def test_a_recipe_kept_at_its_first_level_answers_what_its_deepest_would_drop() -> None:
    """What that level is for: the cap falls past R_X, and R_X is what the plan needs.

    By hand, at 10 of the target a minute, every cycle ten a minute, on the sinkable policy.
    R_A's two B a cycle overfeed R_Top alone, and nothing else eats B without R_X and R_C, so
    the first prefix that solves is five long, R_Alt idle in it. R_Top and R_X split the target,
    half a machine each. Half a machine of R_A then gives 5 A and 10 B, half a machine of R_C
    gives 5 C, and R_X leaves 5 Y to sink. That is 10 Ore a minute.
    """
    built = _revisited_entries()
    registry = _walk_registry(built, REVISITED_ITEMS)
    request = _route_request(built, _walk_item(WALK_TARGET), byproduct_policy=BYPRODUCT_SINKABLE)

    bounded = optimize_within_bound(registry, request)

    assert bounded.chosen_size == REVISITED_PREFIX
    assert bounded.result.selection == ("R_Top", "R_A", "R_X", "R_C")
    assert bounded.result.score == Fraction(10)
    assert bounded.result.plan.byproducts == {_walk_item("Y"): Fraction(5)}
    assert bounded.record is not None
    assert bounded.record.first.removed == ("R_D8", "R_D9", "R_D10")


def test_the_ranking_is_the_route_then_the_closure_by_depth_on_the_chain() -> None:
    """The arm 1 fixture has no third tier: every recipe is in the closure.

    By hand: the four of the route in walk order, R_ChainRareFirst at depth one, and the
    twelve decoys at depth two, by registry position.
    """
    decoys = tuple(f"{DECOY_PREFIX}{index}" for index in range(DECOY_COUNT))

    assert _ranking(closure_registry(), closure_request()) == (
        *CHAIN_ROUTE,
        CHAIN_RARE_FIRST_RECIPE,
        *decoys,
    )


def test_everything_outside_the_closure_ranks_last_by_registry_position() -> None:
    """All three tiers on one fixture, with registry order against the first two.

    By hand, the fillers are declared first and make Rod, which nothing on the walk
    reads. R_B2Direct is the route at a count of one against R_B1Relic's two. R_B1Relic
    is at walk depth zero and R_B3Rare at one, and both outrank the fillers declared
    ahead of them.
    """
    added = [*_padding(2), *_ascent_entries()[:ASCENT_HAND_BUILT]]

    assert _ranking(_bare_registry(added), _route_request(added)) == (
        RELIC_FROM_ORE_RECIPE,
        RELIC_FROM_RARE_RECIPE,
        RARE_RECIPE,
        f"{PADDING_PREFIX}0",
        f"{PADDING_PREFIX}1",
    )


def test_a_closure_within_the_cap_is_wholly_kept() -> None:
    """The clause's second half: only what is outside the closure falls past the cap.

    By hand: a closure of twelve, R_Top making Relic from Rare and eleven Rare makers,
    with two fillers declared ahead of them all. Registry order would keep the fillers
    and drop two of the closure, and so would the shipped order, whose one direct
    producer of Relic is the only recipe it ranks ahead of registry order.
    """
    rare_makers = [
        _one_each(f"R_Rare{index}", (SOLVE_ORE_ITEM,), (SOLVE_RARE_ITEM,)) for index in range(11)
    ]
    added = [
        *_padding(2),
        *rare_makers,
        _one_each("R_Top", (SOLVE_RARE_ITEM,), (SOLVE_RELIC_ITEM,)),
    ]

    record = bound.trim_record(_bare_registry(added), _route_request(added))

    assert record is not None
    assert record.first.removed == (f"{PADDING_PREFIX}0", f"{PADDING_PREFIX}1")
    assert record.first.kept == (*(f"R_Rare{index}" for index in range(11)), "R_Top")
    assert len(record.first.kept) == MAX_EXHAUSTIVE_CANDIDATES


def test_the_closure_follows_no_byproduct_so_a_balanced_route_reads_no_plan() -> None:
    """A byproduct's only consumer is off the walk, and the cap drops it.

    By hand: R_By makes Relic and Rare from Ore. R_Burn eats that Rare, and makes Ore,
    which is raw, so no walk from Relic reaches it. Eleven fillers declared first fill
    the cap beside R_By, so R_Burn is the one dropped. Balanced, nothing kept consumes
    the Rare and every prefix refuses; R_By with R_Burn does solve; and under sinkable
    the same kept set is a plan. So the no-plan is about the kept set and the policy.
    """
    added = [
        *_padding(11),
        _one_each("R_By", (SOLVE_ORE_ITEM,), (SOLVE_RELIC_ITEM, SOLVE_RARE_ITEM)),
        _one_each("R_Burn", (SOLVE_RARE_ITEM,), (SOLVE_ORE_ITEM,)),
    ]
    registry = _bare_registry(added)
    request = _route_request(added)

    with pytest.raises(BoundExhaustedError) as caught:
        optimize_within_bound(registry, request)

    assert caught.value.record is not None
    assert caught.value.record.first.removed == ("R_Burn",)

    both = ("R_By", "R_Burn")
    control = optimize_plan(registry, replace(request, candidates=both, unlocked=both))
    assert control.selection == both

    sinkable = optimize_within_bound(
        registry, replace(request, byproduct_policy=BYPRODUCT_SINKABLE)
    )
    assert sinkable.result.selection == ("R_By",)
    assert sinkable.chosen_size == FIRST_PREFIX


def test_a_prefix_shorter_than_the_route_can_solve() -> None:
    """The module docstring's "or below": the claim is the smallest prefix, not the route.

    By hand: Rod counts 1 through both makers and R_Rod is declared first, so Rod takes
    it. Rare's one maker is R_Both, which makes Rod too. The route is three recipes, and
    its first two already solve, R_Both's Rod feeding R_Top.
    """
    added = [
        _one_each("R_Rod", (SOLVE_ORE_ITEM,), (SOLVE_ROD_ITEM,)),
        _one_each("R_Both", (SOLVE_ORE_ITEM,), (SOLVE_RARE_ITEM, SOLVE_ROD_ITEM)),
        _one_each("R_Top", (SOLVE_RARE_ITEM, SOLVE_ROD_ITEM), (SOLVE_RELIC_ITEM,)),
    ]
    registry = _bare_registry(added)
    request = _route_request(added)

    assert derived_route(registry, request).members == ("R_Top", "R_Both", "R_Rod")

    bounded = optimize_within_bound(registry, request)

    assert bounded.chosen_size == SECOND_PREFIX
    assert bounded.result.selection == ("R_Both", "R_Top")


def test_a_loop_with_no_count_can_still_balance_so_a_count_is_not_feasibility() -> None:
    """The module docstring's "reachability is not feasibility", from the other side.

    By hand: R_Loop makes Rod and Relic from Rare and R_Back makes Rare from Rod, so
    neither item is ever reached from a raw item and the route is empty and incomplete.
    Pillar 1 solves the loop all the same, drawing no raw item. So a False ``complete``
    says nothing about whether a plan exists, and the ascent still finds this one.
    """
    added = [
        _one_each("R_Loop", (SOLVE_RARE_ITEM,), (SOLVE_ROD_ITEM, SOLVE_RELIC_ITEM)),
        _one_each("R_Back", (SOLVE_ROD_ITEM,), (SOLVE_RARE_ITEM,)),
    ]
    registry = _bare_registry(added)
    request = _route_request(added)

    assert derived_route(registry, request) == DerivedRoute(members=(), complete=False, unmade=())

    bounded = optimize_within_bound(registry, request)

    assert bounded.chosen_size == SECOND_PREFIX
    assert bounded.result.selection == ("R_Loop", "R_Back")
    assert not bounded.result.plan.raw_inputs


# ===========================================================================
# i. The count - its least fixed point, its ties and its walk
# ===========================================================================


def test_the_count_is_the_least_fixed_point_and_not_the_first_tree_found() -> None:
    """A dear tree counted first is displaced by a cheaper one found on a later pass.

    By hand, in declared order: the first pass counts Plate 1, Rod 2, Rare 3 through
    R_Long, Relic 4 and Twin 1, reading R_ViaTwin before Twin has a count. The second
    moves Rare to 2 through R_ViaTwin. The third moves Relic to 3. A count that kept
    its first finding, or stopped a pass early, names R_Long.
    """
    added = [
        _one_each("R_MakePlate", (SOLVE_ORE_ITEM,), (SOLVE_PLATE_ITEM,)),
        _one_each("R_MakeRod", (SOLVE_PLATE_ITEM,), (SOLVE_ROD_ITEM,)),
        _one_each("R_Long", (SOLVE_ROD_ITEM,), (SOLVE_RARE_ITEM,)),
        _one_each("R_Top", (SOLVE_RARE_ITEM,), (SOLVE_RELIC_ITEM,)),
        _one_each("R_ViaTwin", (SOLVE_TWIN_ITEM,), (SOLVE_RARE_ITEM,)),
        _one_each("R_MakeTwin", (SOLVE_ORE_ITEM,), (SOLVE_TWIN_ITEM,)),
    ]

    assert _route_of(added).members == ("R_Top", "R_ViaTwin", "R_MakeTwin")


def test_the_count_converges_when_every_recipe_is_declared_before_its_inputs_maker() -> None:
    """Declared top down, so each pass reaches one stage further.

    By hand it takes four passes to reach Relic, and one that stopped at the first
    leaves the target with no count at all.
    """
    added = [
        _one_each("R_Top", (SOLVE_RARE_ITEM,), (SOLVE_RELIC_ITEM,)),
        _one_each("R_MakeRare", (SOLVE_ROD_ITEM,), (SOLVE_RARE_ITEM,)),
        _one_each("R_MakeRod", (SOLVE_PLATE_ITEM,), (SOLVE_ROD_ITEM,)),
        _one_each("R_MakePlate", (SOLVE_ORE_ITEM,), (SOLVE_PLATE_ITEM,)),
    ]

    route = _route_of(added)

    assert route.complete is True
    assert route.members == ("R_Top", "R_MakeRare", "R_MakeRod", "R_MakePlate")


@pytest.mark.parametrize(
    ("declared", "chosen"),
    [
        pytest.param(("R_TieAlpha", "R_TieBeta"), "R_TieAlpha", id="name-order"),
        pytest.param(("R_TieBeta", "R_TieAlpha"), "R_TieBeta", id="against-name-order"),
    ],
)
def test_a_tie_goes_to_the_lower_registry_position(declared: tuple[str, str], chosen: str) -> None:
    """Registry position and never the name: the two params swap declaration order."""
    added = [_one_each(name, (SOLVE_ORE_ITEM,), (SOLVE_RELIC_ITEM,)) for name in declared]

    assert _route_of(added).members == (chosen,)


def test_a_tie_reached_on_a_later_pass_still_goes_to_the_lower_position() -> None:
    """A later finding at an equal count takes over when it sits earlier in the registry.

    By hand: R_Early counts 3 through Rod and Plate, reached on the third pass. R_Late
    counts 3 through Twin and Trinket, reached on the second. They tie, and R_Early is
    declared first, so the walk takes it although R_Late got there first.
    """
    added = [
        _one_each("R_Early", (SOLVE_ROD_ITEM,), (SOLVE_RELIC_ITEM,)),
        _one_each("R_MakeRod", (SOLVE_PLATE_ITEM,), (SOLVE_ROD_ITEM,)),
        _one_each("R_MakePlate", (SOLVE_ORE_ITEM,), (SOLVE_PLATE_ITEM,)),
        _one_each("R_Late", (SOLVE_TWIN_ITEM, SOLVE_TRINKET_ITEM), (SOLVE_RELIC_ITEM,)),
        _one_each("R_MakeTwin", (SOLVE_ORE_ITEM,), (SOLVE_TWIN_ITEM,)),
        _one_each("R_MakeTrinket", (SOLVE_ORE_ITEM,), (SOLVE_TRINKET_ITEM,)),
    ]

    assert _route_of(added).members == ("R_Early", "R_MakeRod", "R_MakePlate")


def test_the_count_is_of_recipes_on_a_tree_so_it_names_no_fewest_distinct_set() -> None:
    """The clause's "no claim of the fewest distinct recipes", shown on a fixture.

    By hand: through R_Shared, Relic eats Rare and Rod, each made from Plate, itself
    made from Gadget, made from Ore. Gadget counts 1, Plate 2, Rare and Rod 3 each, and
    Relic 7, over five distinct recipes. Through R_Wide, Relic eats five items, each
    made from Ore: a count of 6, over six distinct recipes. The tree count takes the
    wider.
    """
    wide_items = (
        SOLVE_TWIN_ITEM,
        SOLVE_TRINKET_ITEM,
        SOLVE_ORPHAN_ITEM,
        SOLVE_FLUID_ITEM,
        SOLVE_RESIDUE_ITEM,
    )
    added = [
        _one_each("R_Shared", (SOLVE_RARE_ITEM, SOLVE_ROD_ITEM), (SOLVE_RELIC_ITEM,)),
        _one_each("R_RareFromPlate", (SOLVE_PLATE_ITEM,), (SOLVE_RARE_ITEM,)),
        _one_each("R_RodFromPlate", (SOLVE_PLATE_ITEM,), (SOLVE_ROD_ITEM,)),
        _one_each("R_PlateFromGadget", (SOLVE_GADGET_ITEM,), (SOLVE_PLATE_ITEM,)),
        _one_each("R_MakeGadget", (SOLVE_ORE_ITEM,), (SOLVE_GADGET_ITEM,)),
        _one_each("R_Wide", wide_items, (SOLVE_RELIC_ITEM,)),
        *(
            _one_each(f"R_Wide{index}", (SOLVE_ORE_ITEM,), (item,))
            for index, item in enumerate(wide_items)
        ),
    ]

    assert _route_of(added).members == (
        "R_Wide",
        "R_Wide0",
        "R_Wide1",
        "R_Wide2",
        "R_Wide3",
        "R_Wide4",
    )


def test_the_walk_is_breadth_first_and_reads_each_recipes_inputs_as_listed() -> None:
    """Three wrong walks each give a different order on this one fixture.

    By hand, R_Top lists Rod before Plate, which sorts the other way. Breadth first it
    is R_Top, Rod's maker, Plate's maker, then Rare's. Depth first has Rare's before
    Plate's, sorted inputs have Plate's before Rod's, and registry order is reversed.
    """
    added = [
        _one_each("R_MakeRare", (SOLVE_ORE_ITEM,), (SOLVE_RARE_ITEM,)),
        _one_each("R_MakePlate", (SOLVE_ORE_ITEM,), (SOLVE_PLATE_ITEM,)),
        _one_each("R_MakeRod", (SOLVE_RARE_ITEM,), (SOLVE_ROD_ITEM,)),
        _one_each("R_Top", (SOLVE_ROD_ITEM, SOLVE_PLATE_ITEM), (SOLVE_RELIC_ITEM,)),
    ]

    assert _route_of(added).members == ("R_Top", "R_MakeRod", "R_MakePlate", "R_MakeRare")


def test_a_recipe_chosen_for_two_items_is_named_once() -> None:
    """R_Both makes both of R_Top's inputs, so the walk meets it twice and names it once."""
    added = [
        _one_each("R_Both", (SOLVE_ORE_ITEM,), (SOLVE_RARE_ITEM, SOLVE_ROD_ITEM)),
        _one_each("R_Top", (SOLVE_RARE_ITEM, SOLVE_ROD_ITEM), (SOLVE_RELIC_ITEM,)),
    ]

    assert _route_of(added).members == ("R_Top", "R_Both")


def test_the_walk_stops_at_a_raw_item_although_a_recipe_makes_it() -> None:
    """A raw item counts zero, so its maker is on no route and outside the closure.

    By hand: R_OreBack makes Ore from Rod, and R_MakeRod makes Rod from Ore. Neither can
    be reached from Relic, since the walk stops at Ore. Both rank as everything else.
    """
    added = [
        _one_each("R_OreBack", (SOLVE_ROD_ITEM,), (SOLVE_ORE_ITEM,)),
        _one_each("R_MakeRod", (SOLVE_ORE_ITEM,), (SOLVE_ROD_ITEM,)),
        _one_each("R_Top", (SOLVE_ORE_ITEM,), (SOLVE_RELIC_ITEM,)),
    ]

    assert _route_of(added).members == ("R_Top",)
    assert _ranking(_bare_registry(added), _route_request(added)) == (
        "R_Top",
        "R_OreBack",
        "R_MakeRod",
    )


def test_a_recipe_with_no_inputs_counts_one_and_needs_no_raw_item() -> None:
    """The module docstring's other leaf: a tree can end at a recipe eating nothing."""
    added = [_one_each("R_Free", (), (SOLVE_RELIC_ITEM,))]

    assert _route_of(added, raw_items=()) == DerivedRoute(
        members=("R_Free",), complete=True, unmade=()
    )


def test_a_target_with_no_count_stops_the_walk_and_leaves_the_route_incomplete() -> None:
    """One target counted and one not: the route is true of the one it can reach.

    By hand, Trinket's one maker eats Orphan, which nothing makes, so Trinket has no
    count though a recipe makes it, and Orphan alone is unmade. R_Dead also eats Rod,
    and R_MakeRod stays out of members, because the walk stops at Trinket.
    """
    added = [
        _one_each("R_MakeRod", (SOLVE_ORE_ITEM,), (SOLVE_ROD_ITEM,)),
        _one_each("R_Dead", (SOLVE_ORPHAN_ITEM, SOLVE_ROD_ITEM), (SOLVE_TRINKET_ITEM,)),
        _one_each("R_Top", (SOLVE_ORE_ITEM,), (SOLVE_RELIC_ITEM,)),
    ]

    route = _route_of(added, SOLVE_RELIC_ITEM, SOLVE_TRINKET_ITEM)

    assert route == DerivedRoute(members=("R_Top",), complete=False, unmade=(SOLVE_ORPHAN_ITEM,))


def test_unmade_is_sorted_and_counts_only_what_no_usable_recipe_makes() -> None:
    """Listed Twin first, so a walk-order result reads the other way round.

    A target no recipe makes is itself unmade, in the same sort. Ore is raw and absent.
    """
    added = [
        _one_each(
            "R_Top", (SOLVE_TWIN_ITEM, SOLVE_ORPHAN_ITEM, SOLVE_ORE_ITEM), (SOLVE_RELIC_ITEM,)
        )
    ]

    route = _route_of(added, SOLVE_RELIC_ITEM, SOLVE_TRINKET_ITEM)

    assert route == DerivedRoute(
        members=(),
        complete=False,
        unmade=(SOLVE_ORPHAN_ITEM, SOLVE_TRINKET_ITEM, SOLVE_TWIN_ITEM),
    )


def test_a_raw_target_is_complete_and_no_target_at_all_is_vacuously_so() -> None:
    """Complete reads a count or a raw item, so neither shape has anything missing."""
    added = [_one_each("R_OreBack", (SOLVE_ROD_ITEM,), (SOLVE_ORE_ITEM,))]

    assert _route_of(added, SOLVE_ORE_ITEM) == DerivedRoute(members=(), complete=True, unmade=())
    assert _route_of(added, targets=MappingProxyType({})) == DerivedRoute(
        members=(), complete=True, unmade=()
    )


def test_the_pool_is_what_the_door_lets_through() -> None:
    """A locked recipe and a zero-duration one are on no route, and neither one makes.

    By hand: R_Locked would give Relic a count of one and is not unlocked, so Relic takes
    R_Long, and R_ZeroDuration would give Rare a count of one and the door refuses it, so
    Rare takes R_MakeRare. With R_MakeRare out of the pool too, nothing usable makes Rare.
    """
    added = [
        _one_each("R_Locked", (SOLVE_ORE_ITEM,), (SOLVE_RELIC_ITEM,)),
        _one_each("R_Long", (SOLVE_RARE_ITEM,), (SOLVE_RELIC_ITEM,)),
        {
            **_one_each("R_ZeroDuration", (SOLVE_ORE_ITEM,), (SOLVE_RARE_ITEM,)),
            KEY_DURATION: "0.000000",
        },
        _one_each("R_MakeRare", (SOLVE_ROD_ITEM,), (SOLVE_RARE_ITEM,)),
        _one_each("R_MakeRod", (SOLVE_ORE_ITEM,), (SOLVE_ROD_ITEM,)),
    ]
    names = tuple(entry[KEY_CLASS_NAME] for entry in added)
    unlocked = tuple(name for name in names if name != "R_Locked")

    assert _route_of(added, unlocked=unlocked).members == ("R_Long", "R_MakeRare", "R_MakeRod")

    only_the_door_left = _route_of(added[:3], unlocked=("R_Long", "R_ZeroDuration"))
    assert only_the_door_left == DerivedRoute(members=(), complete=False, unmade=(SOLVE_RARE_ITEM,))


def test_a_candidate_this_registry_does_not_model_is_refused_at_the_door() -> None:
    """Read through ``usable_candidates``, so its refusal is the refusal here."""
    added = [_one_each("R_Top", (SOLVE_ORE_ITEM,), (SOLVE_RELIC_ITEM,))]
    request = _route_request(added, candidates=("R_NoSuchRecipe",))

    with pytest.raises(ValueError, match="does not model"):
        derived_route(_bare_registry(added), request)


# ===========================================================================
# j. Cycles - each ends, and names no recipe twice
# ===========================================================================


def _assert_a_permutation_with_no_repeat(entries: list[dict[str, str]], *items: str) -> None:
    """The ranking holds every usable candidate exactly once, the route no repeat.

    Args:
        entries: The recipe entries.
        *items: The target items.
    """
    registry = _bare_registry(entries)
    request = _route_request(entries, *items)
    ranked = _ranking(registry, request)
    members = derived_route(registry, request).members

    assert sorted(ranked) == sorted(entry[KEY_CLASS_NAME] for entry in entries)
    assert len(members) == len(set(members))


def test_a_cycle_no_raw_item_enters_has_no_count_and_ends() -> None:
    """Rare from Rod and Rod from Rare, and nothing else, so neither ever counts.

    Neither item is unmade, because a usable recipe makes each. The closure still walks
    it, R_MakeRare at depth zero and R_MakeRod at one, so the ranking is still fixed.
    """
    added = [
        _one_each("R_MakeRod", (SOLVE_RARE_ITEM,), (SOLVE_ROD_ITEM,)),
        _one_each("R_MakeRare", (SOLVE_ROD_ITEM,), (SOLVE_RARE_ITEM,)),
    ]

    assert _route_of(added, SOLVE_RARE_ITEM) == DerivedRoute(members=(), complete=False, unmade=())
    assert _ranking(_bare_registry(added), _route_request(added, SOLVE_RARE_ITEM)) == (
        "R_MakeRare",
        "R_MakeRod",
    )
    _assert_a_permutation_with_no_repeat(added, SOLVE_RARE_ITEM)


def test_a_cycle_with_a_way_in_ends_and_every_chosen_input_counts_below_its_item() -> None:
    """Rod from Ore or from Rare, Rare from Rod: the count breaks the loop at its entry.

    By hand Rod counts 1 through R_RodIn and Rare 2 through R_RareFromRod. R_RodBack
    would make Rod at 3, above Rod's own count, so it is never chosen and the walk ends
    at Ore. It stays in the closure, as a Rod maker at walk depth one.
    """
    added = [
        _one_each("R_RodBack", (SOLVE_RARE_ITEM,), (SOLVE_ROD_ITEM,)),
        _one_each("R_RareFromRod", (SOLVE_ROD_ITEM,), (SOLVE_RARE_ITEM,)),
        _one_each("R_RodIn", (SOLVE_ORE_ITEM,), (SOLVE_ROD_ITEM,)),
    ]

    route = _route_of(added, SOLVE_RARE_ITEM)

    assert route == DerivedRoute(members=("R_RareFromRod", "R_RodIn"), complete=True, unmade=())
    assert _ranking(_bare_registry(added), _route_request(added, SOLVE_RARE_ITEM)) == (
        "R_RareFromRod",
        "R_RodIn",
        "R_RodBack",
    )
    _assert_a_permutation_with_no_repeat(added, SOLVE_RARE_ITEM)


def test_a_recipe_eating_its_own_output_counts_only_through_another_maker() -> None:
    """R_Grow makes Rod from Rod, so alone it is a cycle of one and Rod has no count."""
    grow = _one_each("R_Grow", (SOLVE_ROD_ITEM, SOLVE_ORE_ITEM), (SOLVE_ROD_ITEM,))
    seed = _one_each("R_Seed", (SOLVE_ORE_ITEM,), (SOLVE_ROD_ITEM,))

    assert _route_of([grow], SOLVE_ROD_ITEM) == DerivedRoute(members=(), complete=False, unmade=())
    assert _route_of([grow, seed], SOLVE_ROD_ITEM) == DerivedRoute(
        members=("R_Seed",), complete=True, unmade=()
    )
    _assert_a_permutation_with_no_repeat([grow, seed], SOLVE_ROD_ITEM)


def test_the_corpus_byproduct_loop_ends_and_takes_the_way_in(corpus: Registry) -> None:
    """C3, the corpus's own loop: Gadget needs Fluid, Fluid comes back from Residue.

    By hand: R_Gadget lists Plate then Fluid. Fluid counts 1 through R_Fluid, and through
    R_Recover it would need Residue, which only R_Gadget makes, so far above. R_Recover
    is in the closure as a Fluid maker, at the same walk depth as R_Fluid, and ranks
    behind the route.
    """
    pool = (GADGET_RECIPE, RECOVER_RECIPE, FLUID_RECIPE, PLATE_RECIPE)
    request = _request(pool, targets=MappingProxyType({SOLVE_GADGET_ITEM: C3_GADGET_TARGET}))

    assert derived_route(corpus, request) == DerivedRoute(
        members=(GADGET_RECIPE, PLATE_RECIPE, FLUID_RECIPE), complete=True, unmade=()
    )
    assert _ranking(corpus, request) == (
        GADGET_RECIPE,
        PLATE_RECIPE,
        FLUID_RECIPE,
        RECOVER_RECIPE,
    )


# ===========================================================================
# k. Held recipes - counted first, read only as membership
# ===========================================================================


#: A locked recipe with a count of one, against two held ones.
_HELD_FIXTURE: Final[list[dict[str, str]]] = [
    _one_each("R_Short", (SOLVE_ORE_ITEM,), (SOLVE_RELIC_ITEM,)),
    _one_each("R_HeldTop", (SOLVE_RARE_ITEM,), (SOLVE_RELIC_ITEM,)),
    _one_each("R_HeldRare", (SOLVE_ORE_ITEM,), (SOLVE_RARE_ITEM,)),
]


class _MembershipOnly(frozenset[str]):
    """A held set that refuses to be iterated, so nothing can read an order off it."""

    def __iter__(self) -> Iterator[str]:
        """Refuse.

        Raises:
            AssertionError: Always.
        """
        raise AssertionError


def test_a_longer_held_route_beats_a_shorter_locked_one() -> None:
    """(0, 2) sorts ahead of (1, 1): the first int is locked recipes on the tree."""
    route = derived_route(
        _bare_registry(_HELD_FIXTURE),
        _route_request(_HELD_FIXTURE),
        held=frozenset({"R_HeldTop", "R_HeldRare"}),
    )

    assert route.members == ("R_HeldTop", "R_HeldRare")


def test_with_no_held_set_none_is_locked_and_this_is_the_count_of_cs_1372() -> None:
    """Held omitted, then held empty: (0, 1) against (0, 2), then (1, 1) against (2, 2)."""
    registry = _bare_registry(_HELD_FIXTURE)
    request = _route_request(_HELD_FIXTURE)

    assert derived_route(registry, request).members == ("R_Short",)
    assert derived_route(registry, request, held=None).members == ("R_Short",)
    assert derived_route(registry, request, held=frozenset()).members == ("R_Short",)


def test_the_held_set_is_a_membership_test_and_is_never_iterated() -> None:
    """Its iteration order would differ between processes, so nothing may read it."""
    route = derived_route(
        _bare_registry(_HELD_FIXTURE),
        _route_request(_HELD_FIXTURE),
        held=_MembershipOnly({"R_HeldTop", "R_HeldRare"}),
    )

    assert route.members == ("R_HeldTop", "R_HeldRare")


def test_the_trim_calls_the_route_with_no_held_set(monkeypatch: pytest.MonkeyPatch) -> None:
    """The trim is a statement about the request alone, so it can state no held set."""
    calls: list[dict[str, object]] = []
    real = bound.derived_route

    def spy(registry: Registry, request: OptimizeRequest, **kwargs: Any) -> DerivedRoute:
        """Record the keywords, then answer as the real function does.

        Args:
            registry: The registry.
            request: The request.
            **kwargs: Whatever the caller passed.

        Returns:
            What the real function returns.
        """
        calls.append(kwargs)
        return real(registry, request, **kwargs)

    monkeypatch.setattr(bound, "derived_route", spy)

    _ranking(closure_registry(), closure_request())

    assert calls == [{}]


# ===========================================================================
# l. What the order reads - CS-1372 arm 3
# ===========================================================================


class _Poison:
    """Stands in for anything the order must not read, and refuses every read."""

    def __getattr__(self, _name: str) -> object:
        """Refuse.

        Raises:
            AssertionError: Always.
        """
        raise AssertionError


def test_trim_record_reaches_no_solve(monkeypatch: pytest.MonkeyPatch) -> None:
    """A spy at every door a solve goes through sees nothing, on a fixture that trims."""
    seen: list[str] = []

    def spy_for(name: str) -> Any:
        """Build one recording spy.

        Args:
            name: The door it watches.

        Returns:
            The spy, which records and answers nothing.
        """

        def spy(*_args: object, **_kwargs: object) -> None:
            seen.append(name)

        return spy

    monkeypatch.setattr(bound, "optimize_plan", spy_for("bound.optimize_plan"))
    monkeypatch.setattr(optimize_module, "optimize_plan", spy_for("optimize.optimize_plan"))
    monkeypatch.setattr(optimize_module, "solve_selection", spy_for("optimize.solve_selection"))
    monkeypatch.setattr(optimize_module, "solve_for_targets", spy_for("optimize.solve_for_targets"))
    monkeypatch.setattr(exhaustive, "evaluate_selection", spy_for("exhaustive.evaluate_selection"))

    record = bound.trim_record(closure_registry(), closure_request())

    assert seen == []
    assert record is not None
    assert record.first.kept == ROUTE_ORDER_KEPT
    assert record.first.removed == ROUTE_ORDER_REMOVED
    assert record.first.rule == TRIM_ROUTE_FIRST


@pytest.mark.parametrize("direction", OBJECTIVES)
@pytest.mark.parametrize("policy", BYPRODUCT_POLICIES)
def test_one_request_yields_one_ranking_under_every_direction_and_both_policies(
    direction: str, policy: str
) -> None:
    """The hand-named ranking, whatever the request asks the plan to be judged by."""
    request = replace(
        two_target_request(),
        objective=Objective(weights=MappingProxyType({direction: UNIT})),
        byproduct_policy=policy,
    )

    assert _ranking(two_target_registry(), request) == TWO_TARGET_RANKING


def test_the_order_reads_no_objective_no_policy_and_no_rate() -> None:
    """Every field the order must not read refuses any read, so a read is a failure.

    A rate is a float here too, which a read would carry into the order: it is the key
    of a target that the order reads, never its value.
    """
    registry = two_target_registry()
    plain = two_target_request()
    unread: dict[str, Any] = {
        "targets": MappingProxyType(dict.fromkeys(plain.targets, INEXACT_RATE)),
        "objective": _Poison(),
        "byproduct_policy": _Poison(),
        "config": _Poison(),
    }
    poisoned = replace(plain, **unread)

    assert _ranking(registry, poisoned) == TWO_TARGET_RANKING
    assert bound.trim_record(registry, poisoned) is None
    assert derived_route(registry, poisoned).members == TWO_TARGET_ROUTE


def test_two_targets_in_either_mapping_order_rank_alike() -> None:
    """The walk starts at the targets SORTED, so neither mapping order can decide it."""
    registry = two_target_registry()
    forward = _route_request(_two_target_entries(), SOLVE_RELIC_ITEM, SOLVE_TRINKET_ITEM)
    backward = _route_request(_two_target_entries(), SOLVE_TRINKET_ITEM, SOLVE_RELIC_ITEM)

    assert tuple(forward.targets) != tuple(backward.targets)
    assert _ranking(registry, forward) == TWO_TARGET_RANKING
    assert _ranking(registry, backward) == TWO_TARGET_RANKING
    assert derived_route(registry, forward) == derived_route(registry, backward)


def test_a_permuted_candidate_tuple_ranks_alike() -> None:
    """The door sorts the pool into registry order, so caller order cannot decide it."""
    request = two_target_request()
    reversed_pool = tuple(reversed(request.candidates))

    permuted = replace(request, candidates=reversed_pool, unlocked=reversed_pool)

    assert _ranking(two_target_registry(), permuted) == TWO_TARGET_RANKING


def test_two_processes_rank_one_route_under_different_hash_seeds() -> None:
    """A set deciding an order is stable within a process, so this takes two."""
    printed: list[str] = []
    for seed in HASH_SEEDS:
        child = subprocess.run(
            [sys.executable, "-s", "-B", "-c", ROUTE_CHILD_SOURCE],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=CHILD_TIMEOUT_SECONDS,
            env={"PYTHONHASHSEED": seed, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"},
            check=False,
        )
        # Bound to a plain int before asserting, for the reason the arm above records.
        exit_code = child.returncode
        assert exit_code == 0, f"the child under PYTHONHASHSEED={seed} failed:\n{child.stderr}"
        printed.append(child.stdout.strip())

    assert printed[0].startswith(repr(TWO_TARGET_RANKING))
    assert printed[0] == printed[1]
