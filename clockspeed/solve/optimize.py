"""Pillar 2 - the objective, the OptimizerBackend seam, and the swap that changes no caller.

Per docs/ARCHITECTURE.md this module owns the OBJECTIVE and the INTERFACE, and
deliberately owns no search. Enumerating, pruning and ranking live in
``clockspeed/solve/backends/``; what lives here is the shape a backend is handed,
the shape it must return, the arithmetic that turns a plan into one exact number,
and the mechanism that picks which backend runs. It consumes the normalized
registry from ``clockspeed/data/registry.py``, pillar 1 from
``clockspeed/solve/ratio.py`` and the power math from
``clockspeed/solve/power.py``. It never reads a save and never opens the shipped
docs file.

This is the PREP half of CS-G02 (docs/GATED.md). The gate is not "an optimizer
exists" - it is that a later external LP or ILP backend slots in WITHOUT
CHANGING A SINGLE CALLER. That is why ``optimize_plan`` names no backend class,
why the two shipped backends are reachable only through :func:`select_backend`,
and why the test suite is written against the seam rather than against either
implementation.

WHY THE BACKEND IS CHOSEN THIS WAY, AND WHY IT READS NO FILE
--------------------------------------------------------------
``config/ports.json`` owns port allocation and nothing else. ``config/local.json``
is read by ``clockspeed/data/locate.py``, which is one layer BELOW this one and
which ``solve/`` may not import without reaching past its neighbor. So the
mechanism is entirely in-process, adds no dependency, and opens no file:

  1. the explicit ``override`` argument,
  2. :attr:`SolveConfig.backend`, which rides on the REQUEST rather than in a
     file - a solve is configured by its caller, not by machine state,
  3. the environment variable :data:`BACKEND_ENV_VAR`, following the precedent
     ``locate.py`` set with CLOCKSPEED_GAME_DIR and CLOCKSPEED_SAVE_ROOT,
  4. :data:`DEFAULT_BACKEND`.

An empty string at any level reads as UNSTATED and falls through, matching
``locate.py``'s treatment of an empty override. A name that is stated but
UNRECOGNIZED does NOT fall through: it raises :class:`UnknownBackendError`. The
distinction is the whole point of the mechanism. A silent fallback makes the
config untestable, because a typo produces a complete, plausible, correctly
formatted plan from the wrong solver and there is no signal anywhere that the
requested one never ran - the CONVENTIONS.md section 7.2 unrun gate, arriving
through a spelling mistake.

WHY THE UNLOCKED SET IS AN INPUT AND NOT SOMETHING THIS MODULE COMPUTES
-------------------------------------------------------------------------
A plan built from recipes the player has not unlocked is not a plan, it is a
wish list, and it renders identically to a real one. So the search is
constrained by what is UNLOCKED rather than by what exists in the data. The
schematic and milestone model that would answer "what is unlocked" is phase 5
and does not exist yet, so :attr:`OptimizeRequest.unlocked` is an EXPLICIT
REQUEST INPUT with no default. Stating it is the caller's job today and will be
pillar 4's job later; inventing it here would mean this module defaulting to
"everything", which is exactly the wish list. A candidate outside that set is
reported in :attr:`OptimizeResult.excluded` with a reason rather than dropped,
because a caller that named a recipe is owed an answer about it.

WHY POWER IS COMPARED ONLY AT THE UN-SHARDED BASE, AND WHAT THAT DOES NOT MEAN
--------------------------------------------------------------------------------
Comparing two plans by power draw is well defined ONLY at each building's own
un-sharded clock base. Away from it the law is ``draw`` times ``clock`` raised
to the shipped exponent, the exponent is 1.321929, and the result is irrational
for essentially every rational clock - there is no exact rational value to
compare, and evaluating it returns a float (measured; see
``clockspeed/solve/exact.py``). The achievable overclock ceiling is separately
UNKNOWN: ``version.OVERCLOCK_POTENTIAL_SHARD_SLOTS`` is None and ADR 0005 and
ADR 0006 record why no code path may assume one.

So :func:`score_plan` prices every step through
``power.clamp_to_unsharded_base`` and then ``power.draw_at_clock``, and accepts
ONLY the exact outcome. State the consequence plainly rather than letting the
number imply more than it carries: this ranks plans as they would run
un-overclocked. It does NOT rank them at any other clock, and it is not evidence
about which plan is cheaper once shards are installed. Where a draw cannot be
priced exactly - a recipe that names no building, a recipe that names more than
one and so has no single draw, a building whose declared draw is a range or is
absent - the answer is :class:`PowerNotComparableError` rather than a zero or an
average. A confident zero is precisely what a power plan cannot detect: it
balances, it sums, and it is silently missing a building.

The raw-consumption objective carries its own stated limit: it totals rates
across raw items without weighting them, so it compares like for like only when
the raws are commensurate. A caller that wants ore and oil traded off against
each other is asking a question this objective does not model.

WHY A RESULT IS THE POSITIVE-MACHINE FIXED POINT AND NOT THE SUBSET THAT WAS TRIED
-----------------------------------------------------------------------------------
Two different candidate subsets routinely describe the SAME factory. On the C5
fixture, ``{Std_Gadget}`` and ``{Alt_Gadget, Std_Gadget}`` both solve, because
the second assigns ``Alt_Gadget`` zero machines - the infeasible recipe is not
used, it is merely present. Publishing the subset that happened to be tried
would make two backends disagree on identical factories, and would make the
answer depend on the search rather than on the arithmetic.

So :func:`evaluate_selection` reduces a solved subset to the recipes with a
STRICTLY POSITIVE machine count, re-solves on exactly those, and repeats until
the set stops shrinking. The loop terminates because the set strictly shrinks
each round. What comes back therefore satisfies an invariant a caller can rely
on: ``result.selection`` is exactly the recipe keys of ``result.plan.steps``, in
registry order, every one of them used. A subset whose reduction stops being
solvable is reported as no result at all rather than as a plan that cannot be
reproduced from its own published selection.

DETERMINISM IS A PRODUCT PROPERTY HERE TOO
--------------------------------------------
CLAUDE.md section 1: two runs on one input disagreeing is a bug. Nothing
published here takes its order from the caller. Candidates are deduplicated and
sorted into REGISTRY order at the door, so a permuted or repeated candidate
tuple produces a byte-identical result; objective weights are stored in sorted
key order; and the ranking key a backend breaks ties with is the score paired
with the selection's registry POSITIONS, which is a total order on distinct
selections and is therefore independent of the order in which a backend happened
to visit them.

WHY THESE EXCEPTIONS CARRY AN Error SUFFIX WHEN ratio.py's DO NOT
-------------------------------------------------------------------
``clockspeed/solve/ratio.py`` publishes ``UnsolvableChain`` and its siblings
without the suffix and carries a coded N818 suppression for them, recorded there
for adjudication because those names are the published phase 3 surface. Nothing
outside this module names these five, so they take the suffix and need no
suppression. Adding more unsuffixed names would deepen a debt rather than settle
it.
"""

from __future__ import annotations

import os
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from fractions import Fraction
from types import MappingProxyType
from typing import Final, Protocol

from clockspeed.data.registry import Recipe, Registry
from clockspeed.solve import backends
from clockspeed.solve.exact import audit_exact
from clockspeed.solve.power import (
    OUTCOME_EXACT,
    REFERENCE_CLOCK,
    clamp_to_unsharded_base,
    draw_at_clock,
)
from clockspeed.solve.ratio import (
    EXCLUDED_ZERO_DURATION,
    ExclusionNote,
    ProductionPlan,
    RatioError,
    RatioRequest,
    solve_for_targets,
)

__all__ = [
    "BACKEND_ENV_VAR",
    "DEFAULT_BACKEND",
    "EXCLUDED_LOCKED",
    "MAX_EXHAUSTIVE_CANDIDATES",
    "OBJECTIVES",
    "OBJECTIVE_BUILDINGS",
    "OBJECTIVE_POWER",
    "OBJECTIVE_RAW",
    "NoFeasibleSelectionError",
    "Objective",
    "ObjectiveUndefinedError",
    "OptimizeError",
    "OptimizeRequest",
    "OptimizeResult",
    "OptimizerBackend",
    "PowerNotComparableError",
    "SearchSpaceTooLargeError",
    "SolveConfig",
    "UnknownBackendError",
    "check_objective",
    "evaluate_selection",
    "optimize_plan",
    "registry_order",
    "score_plan",
    "select_backend",
    "solve_selection",
    "usable_candidates",
    "weighted_objective",
]

# ---------------------------------------------------------------------------
# Backend selection
# ---------------------------------------------------------------------------

#: The environment variable that names a backend. Follows the precedent
#: ``clockspeed/data/locate.py`` set - CLOCKSPEED_GAME_DIR, CLOCKSPEED_SAVE_ROOT
#: - so an operator overriding anything in this project reaches for the same
#: shape. An empty value reads as unstated, as it does there.
BACKEND_ENV_VAR: Final = "CLOCKSPEED_OPTIMIZER_BACKEND"

#: The backend used when nothing states one. The complete search rather than the
#: fast one, on the same rule that governs every other default in this project:
#: the exact answer is the default and the approximation is opted into. The
#: complete search is exponential in the candidate count and REFUSES above
#: :data:`MAX_EXHAUSTIVE_CANDIDATES` rather than running for an unbounded time,
#: so the cost of that default is a loud refusal and never a hang.
DEFAULT_BACKEND: Final = "exhaustive"

#: The largest candidate count the complete enumeration will accept. The space
#: is every subset, so the work doubles per candidate; a cap is what turns "this
#: hung" into "this refused and said why". A caller above it selects the greedy
#: backend, which is polynomial and says in its own docstring that it is a
#: heuristic.
MAX_EXHAUSTIVE_CANDIDATES: Final = 12

# ---------------------------------------------------------------------------
# Objectives
# ---------------------------------------------------------------------------

#: Minimize the total rate of raw items the plan consumes. Summed across raw
#: items without weighting - see the module docstring for what that does and
#: does not compare.
OBJECTIVE_RAW: Final = "raw"

#: Minimize total power draw, priced at each building's un-sharded clock base
#: and nowhere else. See the module docstring for why no other clock has an
#: exact rational answer.
OBJECTIVE_POWER: Final = "power"

#: Minimize the total machine count. Fractional on purpose: 10/3 machines is a
#: real answer, and rounding each step up is a decision that belongs to the
#: layer which knows whether the operator intends to underclock.
OBJECTIVE_BUILDINGS: Final = "buildings"

#: Every objective this module models. A weight keyed to anything else is
#: refused rather than ignored - an ignored weight is an objective the caller
#: believes is in force and is not.
OBJECTIVES: Final = (OBJECTIVE_BUILDINGS, OBJECTIVE_POWER, OBJECTIVE_RAW)

# ---------------------------------------------------------------------------
# Exclusion reasons
# ---------------------------------------------------------------------------

#: The reason recorded for a candidate the caller did not declare unlocked.
EXCLUDED_LOCKED: Final = "locked"


class OptimizeError(Exception):
    """Base class for every refusal this module and its backends raise.

    Deliberately NOT a :class:`ValueError`, for the reason
    ``clockspeed/solve/ratio.py`` and ``clockspeed/solve/exact.py`` both state: a
    caller wrapping a malformed-input handler around this layer must not also
    switch off the signals that say the answer is not computable. A genuine
    caller SHAPE bug - a candidate naming no recipe in this registry - stays a
    ValueError, because that one really is bad input.
    """


class UnknownBackendError(OptimizeError):
    """A backend was named and this build does not have it.

    Never a fallback. See the module docstring: falling back to the default
    would turn a typo into a complete, plausible plan produced by a solver the
    caller did not ask for, with no signal anywhere.

    Attributes:
        requested: The name that was offered, verbatim, so the caller can see
            what it actually sent rather than what it meant to send.
    """

    def __init__(self, requested: str, message: str) -> None:
        """Record the offered name alongside the message.

        Args:
            requested: The unrecognized name.
            message: The full explanation.
        """
        super().__init__(message)
        self.requested = requested


class NoFeasibleSelectionError(OptimizeError):
    """No selection of the usable candidates yields a plan at all.

    Distinct from pillar 1's refusals, which describe ONE selection. This one
    says the whole space was searched - completely, by the exhaustive backend;
    heuristically, by the greedy one - and nothing in it solves.
    """


class SearchSpaceTooLargeError(OptimizeError):
    """The complete enumeration would take longer than anyone will wait.

    Raised before any work is done rather than partway through, so the refusal
    costs nothing and cannot be mistaken for a result.
    """


class ObjectiveUndefinedError(OptimizeError):
    """The objective does not name a direction to minimize in.

    Covers an objective with no weights, a weight that is not exactly a
    Fraction, a weight at or below zero, and a weight keyed to something outside
    :data:`OBJECTIVES`. Every one of them produces a score that ranks nothing:
    with no positive weight every candidate ties, and a tie is resolved by
    whatever the tie-break happens to be rather than by the caller's intent.
    """


class PowerNotComparableError(OptimizeError):
    """The plan's power draw has no exact value, so plans cannot be ranked by it.

    Raised only when the power objective carries a weight. An unpriceable
    building that ends up unused, or a caller ranking by machines alone, never
    reaches this.

    Attributes:
        recipe_key: The recipe whose draw could not be priced.
    """

    def __init__(self, recipe_key: str, message: str) -> None:
        """Record the offending recipe alongside the message.

        Args:
            recipe_key: The recipe whose draw could not be priced.
            message: The full explanation.
        """
        super().__init__(message)
        self.recipe_key = recipe_key


@dataclass(frozen=True)
class SolveConfig:
    """How a solve is configured - carried by the REQUEST, never read from a file.

    A file-backed config would put ``solve/`` in the business of locating and
    reading configuration, which is ``clockspeed/data/locate.py``'s job one layer
    down and is not reachable from here without breaking the seam. It would also
    make a solve depend on machine state, so two runs of the same request could
    disagree.

    Attributes:
        backend: The backend name, or None to fall through to the environment
            variable and then to :data:`DEFAULT_BACKEND`. An empty string reads
            as None.
    """

    backend: str | None = None


@dataclass(frozen=True)
class Objective:
    """What "better" means for one solve, as exact weights over named directions.

    Attributes:
        weights: Objective name to its weight. Every key must be in
            :data:`OBJECTIVES` and every weight must be exactly a Fraction above
            zero. Build one through :func:`weighted_objective` rather than by
            hand; :func:`check_objective` is applied either way, so a
            hand-assembled objective is checked at the point of use.
    """

    weights: Mapping[str, Fraction]


@dataclass(frozen=True)
class OptimizeRequest:
    """One pillar 2 question: what to build, out of what, judged how.

    Attributes:
        targets: Item key to the requested net rate per minute, as pillar 1
            takes them. Every value must be exactly a Fraction.
        candidates: The recipe keys the optimizer may choose among. Order and
            duplicates are irrelevant - the door sorts them into registry order.
            A key naming no recipe in the registry is a caller bug and raises
            ValueError rather than being skipped.
        unlocked: The recipe keys the player can actually build. REQUIRED, with
            no default - see the module docstring. Names outside the registry are
            tolerated here rather than refused, because an unlocked set assembled
            from a save or a mod list may legitimately mention content this
            registry does not model.
        raw_items: Items available without bound, as pillar 1 takes them.
        byproduct_policy: One of ratio.py's byproduct policies. REQUIRED there
            and therefore required here; this module adds no default of its own.
        objective: What to minimize.
        config: How to run it, including which backend.
    """

    targets: Mapping[str, Fraction]
    candidates: tuple[str, ...]
    unlocked: tuple[str, ...]
    raw_items: tuple[str, ...]
    byproduct_policy: str
    objective: Objective
    config: SolveConfig = field(default_factory=SolveConfig)


@dataclass(frozen=True)
class OptimizeResult:
    """A chosen selection and the plan it produces, with the score that chose it.

    Attributes:
        backend: The name of the backend that produced this. The one field two
            backends are expected to differ on, which is why an agreement test
            compares :attr:`plan` rather than the whole result.
        selection: The recipes the plan actually uses, in registry order. Equal
            by construction to the recipe keys of :attr:`plan` steps - see the
            module docstring on the positive-machine fixed point.
        plan: The pillar 1 plan for exactly that selection.
        score: The objective value of that plan, exact.
        objective: The objective it was scored under, carried so the result can
            be read without its request.
        excluded: Candidates the caller named that could not enter the search,
            with the reason, in registry order. Identical across backends.
    """

    backend: str
    selection: tuple[str, ...]
    plan: ProductionPlan
    score: Fraction
    objective: Objective
    excluded: tuple[ExclusionNote, ...]


class OptimizerBackend(Protocol):
    """The seam an optimizer implementation sits behind.

    One method and one name. Kept this narrow deliberately: CS-G02 requires that
    a later external LP or ILP solver slot in without changing a caller, and
    every extra member is another thing that solver would have to reproduce. A
    backend is handed a fully formed problem and returns a result; it reads no
    file, no registry of its own, no save and no config.
    """

    @property
    def name(self) -> str:
        """The backend's registered name, as :func:`select_backend` resolves it."""

    def optimize(self, registry: Registry, request: OptimizeRequest) -> OptimizeResult:
        """Choose a selection and return the plan it produces.

        Args:
            registry: The built registry.
            request: The problem.

        Returns:
            The chosen result.

        Raises:
            NoFeasibleSelectionError: Nothing in the searched space solves.
        """


def check_objective(objective: Objective) -> None:
    """Refuse an objective that does not actually name a direction to minimize in.

    Applied by :func:`weighted_objective` on the way in and by
    :func:`score_plan` at the point of use, so a hand-assembled
    :class:`Objective` cannot reach the arithmetic unchecked.

    Args:
        objective: The objective to check.

    Raises:
        ObjectiveUndefinedError: It has no weights, names an objective outside
            :data:`OBJECTIVES`, or carries a weight that is not exactly a
            Fraction above zero. The Fraction check is by type IDENTITY, because
            an int weight is exact and still manufactures a float the moment it
            is divided, and because ``isinstance(True, int)`` is True.
    """
    if not objective.weights:
        raise ObjectiveUndefinedError(
            "the objective carries no weights, so every candidate scores zero and the answer is "
            f"whatever the tie-break happens to be; name at least one of {', '.join(OBJECTIVES)}"
        )
    for name, weight in objective.weights.items():
        if name not in OBJECTIVES:
            raise ObjectiveUndefinedError(
                f"{name!r} is not an objective this module models; it would be silently ignored, "
                f"which is an objective the caller believes is in force and is not. Known: "
                f"{', '.join(OBJECTIVES)}"
            )
        if type(weight) is not Fraction:
            raise ObjectiveUndefinedError(
                f"the weight for {name!r} is {type(weight).__name__} {weight!r}, not a Fraction; "
                "one inexact operand converts every value derived from it while looking correct"
            )
        if weight <= 0:
            raise ObjectiveUndefinedError(
                f"the weight for {name!r} is {weight}, which ranks nothing; a weight of zero is "
                "not a selection - omit the objective instead, so the request says what it means"
            )


def weighted_objective(
    *,
    raw: Fraction | None = None,
    power: Fraction | None = None,
    buildings: Fraction | None = None,
) -> Objective:
    """Build an objective from any combination of the three directions.

    Each is individually selectable by naming it alone, and they combine by
    naming several. Omitting one means it is not part of the objective, which is
    a different statement from weighting it zero - the second is refused, so a
    request cannot say "minimize power" and mean "ignore power".

    Args:
        raw: Weight on total raw consumption, or None to leave it out.
        power: Weight on total draw at the un-sharded base, or None.
        buildings: Weight on total machine count, or None.

    Returns:
        The objective, its weights held in sorted key order so the object's repr
        is stable between runs.

    Raises:
        ObjectiveUndefinedError: Nothing was named, or a stated weight is not
            exactly a Fraction above zero.
    """
    offered = (
        (OBJECTIVE_BUILDINGS, buildings),
        (OBJECTIVE_POWER, power),
        (OBJECTIVE_RAW, raw),
    )
    weights = {name: weight for name, weight in offered if weight is not None}
    objective = Objective(weights=MappingProxyType(weights))
    check_objective(objective)
    return objective


def _recipe_draw(recipe: Recipe, registry: Registry) -> Fraction:
    """Price one recipe's building at its un-sharded clock base, or refuse.

    The clock is taken through ``power.clamp_to_unsharded_base`` rather than
    assumed to be the reference clock, so a building whose declared base is
    below the reference is priced at ITS base and a building declaring none is
    priced at the reference. Only the exact outcome is accepted; every other
    outcome that function can report - not clock-scalable, unmodeled draw,
    deferred because the term is irrational - means there is no number to
    compare, and is reported as such rather than collapsed to zero.

    Args:
        recipe: The recipe whose machines are being priced.
        registry: The built registry, for the building lookup.

    Returns:
        The exact megawatt draw of one machine.

    Raises:
        PowerNotComparableError: The recipe names no building, names more than
            one and so has no single draw, names one this registry does not
            model, or names one whose draw has no exact value at its own base.
    """
    producers = recipe.produced_in
    if not producers:
        raise PowerNotComparableError(
            recipe.key,
            f"{recipe.key} names no building, so it has no power draw to compare; a plan that "
            "used it would be ranked as though it drew nothing, which is the one reading a power "
            "plan cannot detect",
        )
    if producers[1:]:
        raise PowerNotComparableError(
            recipe.key,
            f"{recipe.key} names {len(producers)} buildings - {', '.join(producers)} - so it has "
            "no single draw; picking one of them here would publish a figure the request never "
            "chose, and averaging them would publish one no building has",
        )
    building = registry.buildings.get(producers[0])
    if building is None:
        raise PowerNotComparableError(
            recipe.key,
            f"{recipe.key} is produced in {producers[0]}, which this registry does not model, so "
            "its draw is unknown rather than zero",
        )
    clock = clamp_to_unsharded_base(building, REFERENCE_CLOCK).clock
    drawn = draw_at_clock(building, clock)
    if drawn.outcome != OUTCOME_EXACT or drawn.megawatts is None:
        raise PowerNotComparableError(
            recipe.key,
            f"{recipe.key} cannot be priced at the un-sharded base of {building.key}: "
            f"{drawn.reason}",
        )
    return drawn.megawatts


def _total_raw(plan: ProductionPlan) -> Fraction:
    """Total the rates of every raw item the plan consumes.

    Args:
        plan: The plan.

    Returns:
        The total, exact. Unweighted across items - see the module docstring for
        what that comparison does and does not mean.
    """
    total = Fraction(0)
    for rate in plan.raw_inputs.values():
        total += rate
    return total


def _total_machines(plan: ProductionPlan) -> Fraction:
    """Total the machine counts across a plan.

    Args:
        plan: The plan.

    Returns:
        The total, exact and fractional. Machine EQUIVALENTS rather than the
        built count: rounding each step up is a presentation decision, and doing
        it here would break the exactness the ranking depends on.
    """
    total = Fraction(0)
    for step in plan.steps:
        total += step.machines
    return total


def _total_power(registry: Registry, plan: ProductionPlan) -> Fraction:
    """Total a plan's draw at each building's own un-sharded clock base.

    Args:
        registry: The built registry.
        plan: The plan.

    Returns:
        The total megawatts, exact.

    Raises:
        PowerNotComparableError: Some used recipe has no exact draw.
    """
    total = Fraction(0)
    for step in plan.steps:
        total += step.machines * _recipe_draw(registry.recipes[step.recipe_key], registry)
    return total


def score_plan(registry: Registry, plan: ProductionPlan, objective: Objective) -> Fraction:
    """Reduce a plan to the one exact number a backend ranks by.

    The power term is evaluated ONLY when it carries a weight, so a recipe whose
    draw cannot be priced does not poison a solve that never asked about power.

    Args:
        registry: The built registry.
        plan: The plan to score.
        objective: What to minimize.

    Returns:
        The score, exact. Lower is better.

    Raises:
        ObjectiveUndefinedError: The objective names no usable direction.
        PowerNotComparableError: The power objective is weighted and some used
            recipe has no exact draw.
    """
    check_objective(objective)
    total = Fraction(0)
    raw_weight = objective.weights.get(OBJECTIVE_RAW)
    if raw_weight is not None:
        total += raw_weight * _total_raw(plan)
    building_weight = objective.weights.get(OBJECTIVE_BUILDINGS)
    if building_weight is not None:
        total += building_weight * _total_machines(plan)
    power_weight = objective.weights.get(OBJECTIVE_POWER)
    if power_weight is not None:
        total += power_weight * _total_power(registry, plan)
    return total


def registry_order(registry: Registry, keys: Iterable[str]) -> tuple[str, ...]:
    """Sort recipe keys into registry order, deduplicated.

    Half of the determinism claim: registry order rather than caller order is
    what makes a permuted or repeated candidate tuple produce a byte-identical
    result. The other half is the tie-break rule the backends share.

    Args:
        registry: The built registry.
        keys: Recipe keys, in any order, possibly with repeats. Keys the
            registry does not model are dropped - callers that must refuse them
            do so at the door, in :func:`usable_candidates`.

    Returns:
        The keys, in registry order, each appearing once.
    """
    wanted = set(keys)
    return tuple(key for key in registry.recipes if key in wanted)


def usable_candidates(
    registry: Registry, request: OptimizeRequest
) -> tuple[tuple[str, ...], tuple[ExclusionNote, ...]]:
    """The door: what may enter the search, and why anything else may not.

    Two exclusions are applied here rather than left to the search, and both are
    reported rather than silent:

    - NOT UNLOCKED. A plan built from recipes the player cannot build renders
      exactly like one they can.
    - ZERO DURATION. Pillar 1 excludes those itself and records the reason ON
      THE PLAN, which would make the note appear or disappear depending on which
      subset a backend happened to try. Excluding at the door instead keeps the
      reason stable across the whole search and keeps every plan pillar 1
      returns free of exclusions, so two backends cannot differ on it.

    Args:
        registry: The built registry.
        request: The problem.

    Returns:
        The usable candidate keys in registry order, and the exclusion notes in
        registry order.

    Raises:
        ValueError: A candidate names no recipe in this registry. A caller SHAPE
            bug rather than an unanswerable problem, and refused rather than
            skipped: silently searching a smaller space than the one described
            returns a confident answer to a different question.
    """
    unknown = sorted(set(request.candidates) - set(registry.recipes))
    if unknown:
        raise ValueError(
            f"the request names {len(unknown)} candidate recipe(s) this registry does not model: "
            f"{', '.join(unknown)}"
        )

    wanted = set(request.candidates)
    unlocked = set(request.unlocked)
    usable: list[str] = []
    excluded: list[ExclusionNote] = []
    for key in registry.recipes:
        if key not in wanted:
            continue
        if key not in unlocked:
            excluded.append(ExclusionNote(recipe_key=key, reason=EXCLUDED_LOCKED))
            continue
        if registry.recipes[key].duration == 0:
            excluded.append(ExclusionNote(recipe_key=key, reason=EXCLUDED_ZERO_DURATION))
            continue
        usable.append(key)
    return tuple(usable), tuple(excluded)


def solve_selection(
    registry: Registry, request: OptimizeRequest, selection: Sequence[str]
) -> ProductionPlan | None:
    """Run pillar 1 on one selection, reading a refusal as "not this selection".

    Only :class:`~clockspeed.solve.ratio.RatioError` is absorbed. A ValueError -
    an unknown recipe key, an item declared both raw and a target - is a caller
    shape bug that every selection would hit, and swallowing it would turn one
    bad request into a search that quietly finds nothing.

    Args:
        registry: The built registry.
        request: The problem, for the targets, raw set and byproduct policy.
        selection: The recipe keys to solve with.

    Returns:
        The plan, or None when this selection does not solve.
    """
    try:
        return solve_for_targets(
            registry,
            RatioRequest(
                targets=request.targets,
                recipes=tuple(selection),
                raw_items=request.raw_items,
                byproduct_policy=request.byproduct_policy,
            ),
        )
    except RatioError:
        return None


def evaluate_selection(
    registry: Registry,
    request: OptimizeRequest,
    selection: Sequence[str],
    *,
    backend: str,
    excluded: tuple[ExclusionNote, ...],
) -> OptimizeResult | None:
    """Solve one selection and reduce it to its canonical, positive-machine form.

    The shared half of both backends. What they do differently is decide WHICH
    selections to hand here; agreement between them is therefore evidence about
    the two SEARCHES and not about this function - which is exactly why the C5
    test also asserts against a hand-verified absolute.

    The reduction is the fixed point described in the module docstring: solve,
    keep the recipes with a strictly positive machine count, re-solve on those,
    repeat. It terminates because the set strictly shrinks on every round that
    does not already agree.

    Args:
        registry: The built registry.
        request: The problem.
        selection: Candidate recipe keys, in any order.
        backend: The name to record on the result.
        excluded: The door's exclusion notes, carried onto the result.

    Returns:
        The canonical result, or None when this selection - or its reduction -
        does not solve.

    Raises:
        ObjectiveUndefinedError: The objective names no usable direction.
        PowerNotComparableError: The power objective is weighted and some used
            recipe has no exact draw.
    """
    current = registry_order(registry, selection)
    for _ in range(len(current) + 1):
        plan = solve_selection(registry, request, current)
        if plan is None:
            return None
        positive = tuple(step.recipe_key for step in plan.steps if step.machines > 0)
        if positive == current:
            return OptimizeResult(
                backend=backend,
                selection=current,
                plan=plan,
                score=score_plan(registry, plan, request.objective),
                objective=request.objective,
                excluded=excluded,
            )
        current = positive
    # Unreachable: the loop runs one more time than the selection can shrink,
    # and a set that stops shrinking returns above. Kept as a refusal rather
    # than an assertion so a future change to the reduction cannot silently
    # return a plan whose selection does not describe it.
    return None


def _build_backend(name: str) -> OptimizerBackend:
    """Construct one backend by name, refusing an unrecognized one.

    Args:
        name: The backend name.

    Returns:
        A fresh backend instance.

    Raises:
        UnknownBackendError: No backend is registered under that name. Never a
            fallback - see the module docstring.
    """
    factory = backends.BACKEND_FACTORIES.get(name)
    if factory is None:
        raise UnknownBackendError(
            name,
            f"{name!r} is not a backend this build has. Available: "
            f"{', '.join(backends.available_backends())}. It is refused rather than replaced by "
            f"{DEFAULT_BACKEND!r}, because a fallback turns a misspelling into a complete and "
            "plausible plan from a solver nobody asked for, with no signal that the requested one "
            "never ran",
        )
    return factory()


def select_backend(config: SolveConfig, *, override: str | None = None) -> OptimizerBackend:
    """Resolve which backend runs, in the stated precedence and with no fallback.

    Precedence, checked in this order: ``override``, then
    :attr:`SolveConfig.backend`, then :data:`BACKEND_ENV_VAR`, then
    :data:`DEFAULT_BACKEND`. An empty string at any level reads as unstated and
    falls through; a stated but unrecognized name raises. The two cases are
    different on purpose: absence is a question this function answers, and a
    misspelling is one it must not.

    Args:
        config: The request's config.
        override: An explicit name that beats everything else, or None.

    Returns:
        A fresh backend instance.

    Raises:
        UnknownBackendError: A level stated a name no backend is registered
            under.
    """
    for stated in (override, config.backend, os.environ.get(BACKEND_ENV_VAR)):
        if stated:
            return _build_backend(stated)
    return _build_backend(DEFAULT_BACKEND)


def optimize_plan(
    registry: Registry, request: OptimizeRequest, *, override: str | None = None
) -> OptimizeResult:
    """Choose recipes and return the plan they produce, naming no backend class.

    THIS is the call site CS-G02 is graded against. It reaches a backend only
    through :func:`select_backend`, so a later external LP or ILP solver
    registered under a new name is reachable from here with no edit at all - and
    a test that constructs a backend class directly proves nothing about that,
    because it never runs this path.

    Args:
        registry: The built registry. The only input this layer reads.
        request: The problem.
        override: A backend name that beats the request's own config, for a
            caller comparing two backends deliberately.

    Returns:
        The result, audited exact on the way out.

    Raises:
        UnknownBackendError: A stated backend name is not registered.
        ValueError: A candidate names no recipe in this registry.
        NoFeasibleSelectionError: Nothing in the searched space solves.
        SearchSpaceTooLargeError: The complete enumeration was asked for above
            its cap.
        ObjectiveUndefinedError: The objective names no usable direction.
        PowerNotComparableError: The power objective is weighted and some used
            recipe has no exact draw.
    """
    audit_exact(request, path="request")
    result = select_backend(request.config, override=override).optimize(registry, request)
    audit_exact(result, path="result")
    return result
