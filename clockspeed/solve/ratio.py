"""Pillar 1 - the target-rate ratio solve, as ONE linear system and no graph walk.

This module turns "I want 50 Rod a minute" into machine counts, and turns "I have
45 Ore a minute" into how much of a thing that buys. Both directions run through
the same construction. Its only input below is the normalized registry from
``clockspeed/data/registry.py``; it never reads a save, never opens the shipped
docs file, and never locates an install (BOOTSTRAP.md section 6 seam discipline,
asserted statically by ``tests/solve/test_ratio.py``).

WHY THERE IS NO RECURSION ANYWHERE IN HERE
-------------------------------------------
The obvious implementation walks the recipe graph from the target down to the raw
inputs, accumulating demand. It works on C1 and it does not terminate on C3, where
Gadget needs Fluid, Fluid comes back from Residue, and Residue comes from Gadget.
The standard repair - cycle detection with a visited set - does not fix the
arithmetic, it only stops the crash: the walk still has to decide how much of the
Fluid demand the return path covers, and it cannot, because that quantity depends
on the answer it is in the middle of computing. What comes out is a plan that
double-counts the loop or ignores it, and both render as ordinary plans.

So there is no walk. One variable per selected recipe - ``x_r``, the machine count
- one equation per item, and :func:`~clockspeed.solve.exact.solve_linear` over
exact Fractions. A cycle in the recipe graph is nothing more than a coefficient
appearing in two rows, and Gauss-Jordan has no opinion about it. The loop
terminates because there is nothing to terminate: the system is built in one pass
and reduced in another.

Net rate of item ``i`` under recipe ``r``, per machine per minute, is
``(out_i - in_i) * 60 / duration_r``, which is
:func:`~clockspeed.solve.exact.per_minute` applied to the per-cycle net.

WHICH ITEMS GET AN EQUATION, AND WHICH DELIBERATELY DO NOT
-----------------------------------------------------------
- **TARGET** - net equals the requested rate. That is the ask.
- **INTERMEDIATE** - produced AND consumed inside the selected set, and neither
  raw nor a target. Net equals zero. This is the row that closes the C3 loop.
- **RAW** - NO equation at all. A raw input is available without bound, so
  constraining it would be inventing a limit the caller did not state. Its net is
  not an input to the solve, it is the ANSWER: how much ore the plan eats.
- **BYPRODUCT** - produced by the set, consumed by nothing in it, neither raw nor
  a target. This one is a POLICY DECISION and it has NO DEFAULT. See below.

Classification reads the raw ingredient and product SIDES rather than the net, so
an item a recipe both consumes and produces is correctly seen as both even when
the two cancel exactly.

WHY THE BYPRODUCT POLICY HAS NO DEFAULT
----------------------------------------
An unconsumed byproduct has exactly two defensible readings and they give
different answers to the same question.

- :data:`BYPRODUCT_BALANCED` - it may not accumulate, so its net must be zero. With
  no consumer that forces the producing recipe to zero, which usually contradicts
  the target and correctly refuses.
- :data:`BYPRODUCT_SINKABLE` - it may be sunk or vented, so it gets no equation and
  its net is reported alongside the raw inputs.

The third reading - assume it vanishes - is the one that must never be reachable.
It is not a policy, it is the SILENT version of ``sinkable``: it produces the same
machine counts with the byproduct nowhere in the output, so a player follows a plan
that quietly requires somewhere to put twenty cubic metres a minute of a fluid
nobody mentioned. A factory backs up and the plan that caused it still looks right.
There is therefore no default anywhere in this module: the field is required on the
request and its value is checked against :data:`BYPRODUCT_POLICIES`.

The measured consequence, and the reason this is not hypothetical: C3 minus its
recovery half answers under ``sinkable`` and REFUSES under ``balanced``. Same
registry, same recipes, same target.

THE FOUR REFUSALS - each one is a plausible wrong answer that renders as a right one
------------------------------------------------------------------------------------
- :class:`UnsolvableChain` for an inconsistent system, NAMING the item whose
  balance cannot be met. ``solve_linear`` deliberately publishes no row index - an
  inconsistency is a property of the row SPACE and any dependent row could equally
  be blamed - so the name is recovered here by :func:`_name_unsatisfiable_item`.
  Balance rows are probed before target rows, because the caller's own target is
  the least useful thing to blame: the finding is the item the chain cannot supply.
- :class:`UnderdeterminedChain` for a solution FAMILY, reporting the free variables
  BY RECIPE KEY. Pinning them to zero is the plausible wrong answer: it yields a
  full vector of exact Fractions satisfying every equation, and it is one arbitrary
  member of an infinite set that nothing downstream can distinguish from the
  answer. A column index would be reported instead of a key only by a module that
  had forgotten the caller cannot see its matrix.
- :class:`InfeasibleChain` for a unique solution containing a negative machine
  count, NAMING the recipe. This is the most likely silent wrong answer in the
  whole pillar. A negative ``x_r`` is a recipe run BACKWARDS - consuming its
  products to make its ingredients - and a byproduct loop produces one readily when
  the return path over-supplies. Nothing about the vector announces it: every entry
  is exact and every equation balances. Only the sign says so.
- **Zero duration** - excluded before any arithmetic, with the reason recorded in
  :attr:`ProductionPlan.excluded`. The registry keeps a MEASURED zero on build-gun
  recipes and skips only an ABSENT duration, precisely so a genuine zero stays
  distinguishable, so this is real input rather than a defensive branch.
  :func:`~clockspeed.solve.exact.per_minute` would raise ``UndefinedRateError`` on
  it and is never reached with it. Excluding SILENTLY would be its own defect: the
  caller named a recipe and would get back a plan without it and no reason.

WHY EVERY CONTAINER HERE IS A TUPLE OR A MAPPING AND NEVER A SET
-----------------------------------------------------------------
``exact.audit_exact`` walks dataclasses, mappings, tuples and lists, and REFUSES
anything else rather than walking past it. A ``frozenset`` field would therefore
fail the entry audit of the very request that carries it. Sets are used freely
inside function bodies, where nothing audits them, and never on a published shape.

DETERMINISM IS A PRODUCT PROPERTY, NOT AN ACCIDENT
---------------------------------------------------
CLAUDE.md section 1: two runs on one input disagreeing is a bug. Nothing published
here takes its order from the caller. Variables run in REGISTRY order, so a
permuted or duplicated ``recipes`` tuple produces a byte-identical plan; rows and
every published mapping run in sorted key order. That is what makes ``repr(plan)``
comparable between runs, which is how ``tests/solve/test_ratio.py`` proves this
rather than asserting it.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from fractions import Fraction
from types import MappingProxyType
from typing import Final

from clockspeed.data.registry import Recipe, Registry
from clockspeed.solve.exact import (
    OUTCOME_INCONSISTENT,
    OUTCOME_UNDERDETERMINED,
    OUTCOME_UNIQUE,
    InexactValueError,
    audit_exact,
    isolating_rows,
    per_minute,
    solve_linear,
)

__all__ = [
    "BYPRODUCT_BALANCED",
    "BYPRODUCT_POLICIES",
    "BYPRODUCT_SINKABLE",
    "EXCLUDED_ZERO_DURATION",
    "ByproductPolicyRequired",
    "ExclusionNote",
    "InfeasibleChain",
    "PlanStep",
    "ProductionPlan",
    "RatioError",
    "RatioRequest",
    "SupplyRequest",
    "UnboundedSupply",
    "UnderdeterminedChain",
    "UnsolvableChain",
    "solve_for_supply",
    "solve_for_targets",
]

# ---------------------------------------------------------------------------
# Byproduct policy
# ---------------------------------------------------------------------------

#: An unconsumed byproduct may NOT accumulate: its net is constrained to zero.
#: With no consumer in the selected set that forces its producer to zero, which is
#: usually a contradiction and is correctly reported as one.
BYPRODUCT_BALANCED: Final = "balanced"

#: An unconsumed byproduct may be sunk or vented: it gets no equation and its net
#: is REPORTED in :attr:`ProductionPlan.byproducts`. Reported rather than dropped
#: is the whole difference between this policy and assuming it vanishes.
BYPRODUCT_SINKABLE: Final = "sinkable"

#: Every policy this module accepts. There is deliberately no third entry and no
#: default - see the module docstring.
BYPRODUCT_POLICIES: Final = (BYPRODUCT_BALANCED, BYPRODUCT_SINKABLE)

#: The reason recorded for a recipe dropped for a measured zero duration.
EXCLUDED_ZERO_DURATION: Final = "zero-duration"


class RatioError(Exception):
    """Base class for every refusal this module raises.

    Deliberately NOT a :class:`ValueError`, for the reason
    ``clockspeed/solve/exact.py`` and ``clockspeed/data/registry.py`` both state:
    a caller wrapping a malformed-input handler around this layer must not also
    switch off the signals that say the plan itself is not answerable. A genuine
    caller SHAPE bug - an unknown recipe key, an item declared both raw and target
    - stays a ValueError, because that one really is bad input.
    """


# The five refusals below carry a coded N818 suppression rather than an `Error`
# suffix. Their names are the PUBLISHED phase 3 surface - the slice brief names
# UnsolvableChain and InfeasibleChain specifically - so renaming them here would
# move a seam other slices are written against, and `pyproject.toml` is not this
# slice's to edit. The suppression is coded rather than bare, so it cannot absorb
# the next finding on the same line. Recorded for adjudication: either N818 gains
# a per-file ignore with this reason, or all five are renamed at once.
class UnsolvableChain(RatioError):  # noqa: N818
    """The item balances contradict each other; no plan exists at any scale.

    Attributes:
        item: The item whose balance cannot be met. Recovered from the rows this
            module built rather than read off the reduced form, because
            ``solve_linear`` publishes no row index.
    """

    def __init__(self, item: str, message: str) -> None:
        """Record the offending item alongside the message.

        Args:
            item: The item whose balance cannot be met.
            message: The full explanation.
        """
        super().__init__(message)
        self.item = item


class UnderdeterminedChain(RatioError):  # noqa: N818
    """The system has infinitely many solutions, so it does not name a plan.

    Attributes:
        free_recipes: The recipe keys whose machine counts are unconstrained, in
            variable order. Keys and not column indices: a column index is
            meaningless outside this module and silently wrong once the recipe
            order changes.
    """

    def __init__(self, free_recipes: tuple[str, ...], message: str) -> None:
        """Record the free variables alongside the message.

        Args:
            free_recipes: The unconstrained recipe keys.
            message: The full explanation.
        """
        super().__init__(message)
        self.free_recipes = free_recipes


class InfeasibleChain(RatioError):  # noqa: N818
    """The unique solution requires running a recipe backwards.

    Attributes:
        recipe: The first recipe, in variable order, whose machine count is
            negative.
        machines: That negative count, kept exact. Publishing it is what lets a
            caller - and a test - confirm the refusal came from the arithmetic
            rather than from an unrelated guard.
    """

    def __init__(self, recipe: str, machines: Fraction, message: str) -> None:
        """Record the offending recipe and its count alongside the message.

        Args:
            recipe: The recipe with a negative machine count.
            machines: The negative count.
            message: The full explanation.
        """
        super().__init__(message)
        self.recipe = recipe
        self.machines = machines


class ByproductPolicyRequired(RatioError):  # noqa: N818
    """No usable byproduct policy was stated on the request.

    Attributes:
        policy: The value that was offered, verbatim, so the caller can see what
            it actually sent rather than what it meant to send.
    """

    def __init__(self, policy: str, message: str) -> None:
        """Record the offered policy alongside the message.

        Args:
            policy: The unusable value.
            message: The full explanation.
        """
        super().__init__(message)
        self.policy = policy


class UnboundedSupply(RatioError):  # noqa: N818
    """No supplied item limits the target, so every rate satisfies the request.

    Raised only by :func:`solve_for_supply`. Answering would mean returning one
    arbitrary member of an unbounded family, which is the same failure mode as
    pinning a free variable.
    """


@dataclass(frozen=True)
class PlanStep:
    """One recipe and how many machines of it the plan calls for.

    Attributes:
        recipe_key: The recipe's ClassName.
        machines: The exact machine count. Fractional on purpose - 10/3 is a real
            answer and rounding it here would discard the only information a
            caller needs to decide between three machines underclocked and four
            machines idling.
    """

    recipe_key: str
    machines: Fraction


@dataclass(frozen=True)
class ExclusionNote:
    """One recipe the caller asked for that the solve could not use, and why.

    Attributes:
        recipe_key: The excluded recipe's ClassName.
        reason: One of the module's ``EXCLUDED_*`` constants.
    """

    recipe_key: str
    reason: str


@dataclass(frozen=True)
class ProductionPlan:
    """A solved plan: what to build, what it eats, and what falls out of it.

    Every numeric leaf is an exact :class:`~fractions.Fraction`, and
    :func:`~clockspeed.solve.exact.audit_exact` is run over the whole structure
    before it is returned.

    Attributes:
        steps: One entry per usable recipe the caller selected, in REGISTRY order,
            including any the solve assigned zero machines. Zero-machine steps are
            kept because a caller that asked about a recipe is owed an answer
            about it; dropping them would make ``steps`` depend on the numbers.
        targets: The net rate this plan actually ACHIEVES for each target item,
            recomputed from the solution rather than echoed back from the request.
            An echo would agree with the request by construction and could never
            catch a solve that missed it.
        raw_inputs: Raw item to the rate the plan CONSUMES, positive. The sign is
            flipped from the balance sheet deliberately - a consumer of this field
            asks "how much ore do I need", and answering with a negative number is
            how an off-by-a-sign defect gets shipped.
        byproducts: Unconsumed byproduct to the rate the plan PRODUCES, positive.
            Populated only under :data:`BYPRODUCT_SINKABLE`; empty under
            :data:`BYPRODUCT_BALANCED`, where such an item is constrained to zero
            instead.
        excluded: Recipes the caller named that the solve could not use, with the
            reason, in registry order.
        byproduct_policy: The policy this plan was solved under, carried so the
            plan can be read without its request.
    """

    steps: tuple[PlanStep, ...]
    targets: Mapping[str, Fraction]
    raw_inputs: Mapping[str, Fraction]
    byproducts: Mapping[str, Fraction]
    excluded: tuple[ExclusionNote, ...]
    byproduct_policy: str


@dataclass(frozen=True)
class RatioRequest:
    """Solve forwards: given target rates, find the machine counts.

    Attributes:
        targets: Item key to the requested net rate per minute. Every value must
            be exactly a Fraction - see :func:`_require_fraction` for why an int
            is refused despite being exact.
        recipes: The selected recipe keys. Pillar 1 does not CHOOSE recipes; that
            is pillar 2's job behind ``OptimizerBackend``. Order and duplicates
            are both irrelevant: variables run in registry order.
        raw_items: Items available without bound. A tuple rather than a frozenset
            because ``audit_exact`` refuses sets - see the module docstring.
        byproduct_policy: One of :data:`BYPRODUCT_POLICIES`. REQUIRED, with no
            default anywhere in this module.
    """

    targets: Mapping[str, Fraction]
    recipes: tuple[str, ...]
    raw_items: tuple[str, ...]
    byproduct_policy: str


@dataclass(frozen=True)
class SupplyRequest:
    """Solve backwards: given a supply cap, find how much of one item it buys.

    Attributes:
        supply: Item key to the rate per minute available. An item absent from
            this mapping is unconstrained; an item present but never consumed by
            the chain constrains nothing either.
        target_item: The single item to produce. One item and not a basket,
            because "maximize a basket" needs an objective to trade its members
            off against, and choosing that objective is not this layer's call.
        recipes: The selected recipe keys, as on :class:`RatioRequest`.
        raw_items: Items available without bound, as on :class:`RatioRequest`.
            The supplied items are normally a subset.
        byproduct_policy: One of :data:`BYPRODUCT_POLICIES`. REQUIRED.
    """

    supply: Mapping[str, Fraction]
    target_item: str
    recipes: tuple[str, ...]
    raw_items: tuple[str, ...]
    byproduct_policy: str


@dataclass(frozen=True)
class _System:
    """The assembled linear system, plus what is needed to read its answer back.

    Private: the shapes below are an implementation of the formulation, not a
    published model, and nothing outside this module should depend on them.

    Attributes:
        recipes: Variable order - one recipe key per matrix column.
        rows: One item key per matrix row. Balance rows first, then target rows,
            which is the order :func:`_name_unsatisfiable_item` probes in.
        balance_count: How many leading rows are balance rows.
        matrix: Coefficients, exact.
        rhs: One constant per row, exact.
        rates: Recipe key to item key to net rate per machine per minute.
        raw_present: Raw items that actually appear in the selected set, sorted.
        sunk: Unconsumed byproducts left unconstrained by the sinkable policy,
            sorted.
    """

    recipes: tuple[str, ...]
    rows: tuple[str, ...]
    balance_count: int
    matrix: tuple[tuple[Fraction, ...], ...]
    rhs: tuple[Fraction, ...]
    rates: Mapping[str, Mapping[str, Fraction]]
    raw_present: tuple[str, ...]
    sunk: tuple[str, ...]


def _require_fraction(value: object, path: str) -> Fraction:
    """Refuse anything that is not exactly a Fraction, and say where it was.

    ``audit_exact`` cannot do this job: it ADMITS ``int`` as a leaf, because
    counts and ranks legitimately are ints. A rate of ``50`` therefore passes the
    request audit and then manufactures a float the moment a pivot row is
    normalized, since ``1 / 2`` is ``0.5``. The check has to be made at the
    operand, positively, and by type identity so a Fraction subclass that has
    overridden the arithmetic is refused too.

    Args:
        value: The value to check.
        path: How to name it in the message.

    Returns:
        The same value, now known to be a Fraction.

    Raises:
        InexactValueError: The value is not exactly a Fraction.
    """
    if type(value) is not Fraction:
        raise InexactValueError(
            f"{path} is {type(value).__name__} {value!r}, not a Fraction; an int is exact but "
            "int / int is not, so an all-int system manufactures floats during elimination"
        )
    return value


def _ordered_recipes(registry: Registry, keys: Sequence[str]) -> tuple[Recipe, ...]:
    """Resolve requested recipe keys into registry order, deduplicated.

    Registry order and not request order is what makes the plan independent of
    how the caller happened to write its request, which is half of the
    determinism claim.

    Args:
        registry: The built registry.
        keys: The requested recipe keys, in any order, possibly with repeats.

    Returns:
        The recipes, in registry order, each appearing once.

    Raises:
        ValueError: A key names no recipe in this registry. A caller SHAPE bug
            rather than an unanswerable plan, so it is not a RatioError - and it
            is refused rather than skipped, because silently solving a smaller
            problem than the one described is how a wrong plan gets a right-
            looking number attached to it.
    """
    wanted = set(keys)
    unknown = sorted(wanted - set(registry.recipes))
    if unknown:
        raise ValueError(
            f"the request names {len(unknown)} recipe(s) this registry does not model: "
            f"{', '.join(unknown)}"
        )
    return tuple(registry.recipes[key] for key in registry.recipes if key in wanted)


def _partition_usable(
    recipes: Sequence[Recipe],
) -> tuple[tuple[Recipe, ...], tuple[ExclusionNote, ...]]:
    """Split the selected recipes into the usable ones and the excluded ones.

    A zero duration is checked BEFORE any rate is computed, so ``per_minute`` is
    never reached with it. The registry keeps that zero deliberately, which is
    what makes this a real branch rather than a defensive one.

    Args:
        recipes: The selected recipes, in registry order.

    Returns:
        The usable recipes and the exclusion notes, both in registry order.
    """
    usable: list[Recipe] = []
    excluded: list[ExclusionNote] = []
    for recipe in recipes:
        if recipe.duration == 0:
            excluded.append(ExclusionNote(recipe_key=recipe.key, reason=EXCLUDED_ZERO_DURATION))
            continue
        usable.append(recipe)
    return tuple(usable), tuple(excluded)


def _net_per_minute(recipe: Recipe) -> Mapping[str, Fraction]:
    """Net flow of every item one machine of ``recipe`` moves, per minute.

    The per-cycle net is accumulated first and converted once, so an item on both
    sides of a recipe is netted rather than counted twice.

    Args:
        recipe: A recipe with a non-zero duration.

    Returns:
        Item key to signed rate. Negative is consumption, positive production.

    Raises:
        UndefinedRateError: The duration is zero. Unreachable through this
            module, which excludes those before it gets here, and left to
            propagate rather than caught so that a future caller reaching this
            function directly is not quietly given a number.
    """
    per_cycle: dict[str, Fraction] = {}
    for flow in recipe.inputs:
        per_cycle[flow.item_key] = per_cycle.get(flow.item_key, Fraction(0)) - flow.amount
    for flow in recipe.outputs:
        per_cycle[flow.item_key] = per_cycle.get(flow.item_key, Fraction(0)) + flow.amount
    return {key: per_minute(amount, recipe.duration) for key, amount in per_cycle.items()}


def _build_system(
    recipes: Sequence[Recipe],
    targets: Mapping[str, Fraction],
    raw_items: Sequence[str],
    policy: str,
) -> _System:
    """Assemble the whole formulation in one pass - no walk, no recursion.

    Args:
        recipes: The usable recipes, in registry order. These are the variables.
        targets: Item key to requested net rate.
        raw_items: Items available without bound.
        policy: One of :data:`BYPRODUCT_POLICIES`, already validated.

    Returns:
        The system, ready for :func:`~clockspeed.solve.exact.solve_linear`.
    """
    rates = {recipe.key: _net_per_minute(recipe) for recipe in recipes}
    consumed = {flow.item_key for recipe in recipes for flow in recipe.inputs}
    produced = {flow.item_key for recipe in recipes for flow in recipe.outputs}
    raw = set(raw_items)

    # Target items are added to the universe even when no selected recipe touches
    # them. Leaving them out would drop the row that says the target is not met,
    # and the plan would come back "successful" while producing none of it.
    universe = consumed | produced | set(targets)

    balance: list[str] = []
    target_rows: list[str] = []
    sunk: list[str] = []
    for item in sorted(universe):
        if item in raw:
            continue
        if item in targets:
            target_rows.append(item)
            continue
        if item in produced and item not in consumed and policy == BYPRODUCT_SINKABLE:
            sunk.append(item)
            continue
        balance.append(item)

    rows = tuple(balance) + tuple(target_rows)
    order = tuple(recipe.key for recipe in recipes)
    matrix = tuple(tuple(rates[key].get(item, Fraction(0)) for key in order) for item in rows)
    rhs = tuple(Fraction(0) for _ in balance) + tuple(
        _require_fraction(targets[item], f"request.targets[{item!r}]") for item in target_rows
    )
    return _System(
        recipes=order,
        rows=rows,
        balance_count=len(balance),
        matrix=matrix,
        rhs=rhs,
        rates=rates,
        raw_present=tuple(sorted(raw & universe)),
        sunk=tuple(sunk),
    )


def _net_of(system: _System, values: Sequence[Fraction], item: str) -> Fraction:
    """Total net rate of one item across a solved plan.

    Args:
        system: The system that was solved.
        values: The solution, in variable order.
        item: The item to total.

    Returns:
        The signed net rate. Negative is net consumption.
    """
    total = Fraction(0)
    for key, machines in zip(system.recipes, values, strict=True):
        total += machines * system.rates[key].get(item, Fraction(0))
    return total


def _name_unsatisfiable_item(system: _System) -> str:
    """Find which item's balance the system cannot meet.

    ``solve_linear`` publishes no row index on purpose: an inconsistency belongs
    to the row SPACE, so any one of the dependent rows could be blamed for it and
    a row index would also move under a permutation. The name is therefore
    recovered here, by asking which of THESE rows - the ones this module built,
    in the order it built them - could be struck out to leave a satisfiable
    system. Balance rows come before target rows, so the answer is the item the
    chain cannot supply rather than the target the caller asked for, which is the
    useful half of the finding.

    An all-zero row over a non-zero constant is checked first. It needs no
    elimination at all, and it is the commonest shape by far - a target nothing
    in the selected set produces.

    CS-302 REPLACED THE PROBE LOOP THAT USED TO LIVE HERE. It dropped one row at
    a time and re-solved, which is one full elimination PER ROW. Measured against
    the live registry that is a 750 by 872 system whose single solve takes
    seconds, so explaining a refusal cost three orders of magnitude more than
    reaching it. :func:`~clockspeed.solve.exact.isolating_rows` answers the same
    question in one elimination, and ``tests/solve/test_exact.py`` holds it to
    the old loop's answers as an oracle rather than taking that on trust.

    Args:
        system: The system ``solve_linear`` reported inconsistent.

    Returns:
        The item key to name. Never empty: an inconsistent system has at least
        one row.
    """
    for index, row in enumerate(system.matrix):
        if system.rhs[index] != 0 and all(entry == 0 for entry in row):
            return system.rows[index]

    isolating = isolating_rows(system.matrix, system.rhs)
    if isolating:
        return system.rows[isolating[0]]

    # Reachable only when no single row isolates the contradiction, which takes
    # three or more mutually dependent rows. The first balance row is named
    # rather than nothing at all, because a refusal with no subject is one
    # nobody can act on.
    return system.rows[0]


def _plan_from(
    system: _System,
    values: Sequence[Fraction],
    excluded: tuple[ExclusionNote, ...],
    policy: str,
) -> ProductionPlan:
    """Read a solved vector back into a plan, refusing a negative machine count.

    Args:
        system: The system that was solved.
        values: The unique solution, in variable order.
        excluded: The exclusion notes to carry.
        policy: The policy the plan was solved under.

    Returns:
        The plan. Every published mapping is built in sorted key order, so the
        plan's repr is stable between runs.

    Raises:
        InfeasibleChain: Some machine count is negative - a recipe run backwards.
            Checked in variable order so the named recipe is deterministic.
    """
    for key, machines in zip(system.recipes, values, strict=True):
        if machines < 0:
            raise InfeasibleChain(
                key,
                machines,
                f"the chain balances only by running {key} backwards at {machines} machines; a "
                "negative machine count consumes that recipe's products to make its ingredients, "
                "which no building does, and every equation balances regardless",
            )

    targets = {
        item: _net_of(system, values, item) for item in sorted(system.rows[system.balance_count :])
    }
    return ProductionPlan(
        steps=tuple(
            PlanStep(recipe_key=key, machines=machines)
            for key, machines in zip(system.recipes, values, strict=True)
        ),
        targets=MappingProxyType(targets),
        raw_inputs=MappingProxyType(
            {item: -_net_of(system, values, item) for item in system.raw_present}
        ),
        byproducts=MappingProxyType({item: _net_of(system, values, item) for item in system.sunk}),
        excluded=excluded,
        byproduct_policy=policy,
    )


def _check_policy(policy: str) -> None:
    """Refuse a request that does not state a usable byproduct policy.

    Args:
        policy: The value offered on the request.

    Raises:
        ByproductPolicyRequired: It is not one of :data:`BYPRODUCT_POLICIES`.
    """
    if policy not in BYPRODUCT_POLICIES:
        raise ByproductPolicyRequired(
            policy,
            f"byproduct_policy must be one of {', '.join(BYPRODUCT_POLICIES)}, not {policy!r}; "
            "there is no default because assuming an unconsumed byproduct vanishes produces the "
            "same machine counts as sinking it with the byproduct nowhere in the output",
        )


def solve_for_targets(registry: Registry, request: RatioRequest) -> ProductionPlan:
    """Solve forwards: requested rates in, machine counts and raw demand out.

    One linear system, one Gauss-Jordan reduction, no graph walk - see the module
    docstring for why a walk cannot answer the byproduct loop at all.

    Args:
        registry: The built registry. The only input this layer reads.
        request: The targets, the selected recipes, the raw set and the policy.

    Returns:
        The plan, audited exact on the way out.

    Raises:
        ByproductPolicyRequired: The policy is missing or unrecognized.
        ValueError: A recipe key names nothing in this registry, or an item is
            declared both raw and a target.
        InexactValueError: A target rate is not exactly a Fraction.
        UnsolvableChain: The item balances contradict each other.
        UnderdeterminedChain: The system describes a family rather than a plan.
        InfeasibleChain: The unique solution runs a recipe backwards.
    """
    audit_exact(request, path="request")
    _check_policy(request.byproduct_policy)

    overlap = sorted(set(request.raw_items) & set(request.targets))
    if overlap:
        raise ValueError(
            f"{', '.join(overlap)} is declared both raw and a target; a raw item is available "
            "without bound, so targeting one asks for a rate that is already unlimited"
        )

    usable, excluded = _partition_usable(_ordered_recipes(registry, request.recipes))
    system = _build_system(usable, request.targets, request.raw_items, request.byproduct_policy)
    solution = solve_linear(system.matrix, system.rhs)

    if solution.outcome == OUTCOME_INCONSISTENT:
        item = _name_unsatisfiable_item(system)
        raise UnsolvableChain(
            item,
            f"no plan satisfies this request at any scale: the balance for {item} cannot be met "
            "by the selected recipes. Nothing here is a matter of degree - the solution set is "
            "empty, so there is no closest plan to fall back to",
        )

    if solution.outcome == OUTCOME_UNDERDETERMINED:
        free = tuple(system.recipes[column] for column in solution.free_variables)
        raise UnderdeterminedChain(
            free,
            f"the selected recipes do not determine a plan: {', '.join(free) or 'no recipe'} "
            "may take any value. Pinning them to zero would return exact Fractions satisfying "
            "every equation and one arbitrary member of an infinite family, which nothing "
            "downstream could tell from the answer",
        )

    if solution.outcome != OUTCOME_UNIQUE or solution.values is None:
        raise RatioError(
            f"solve_linear reported {solution.outcome!r}, an outcome this module does not model"
        )

    plan = _plan_from(system, solution.values, excluded, request.byproduct_policy)
    audit_exact(plan, path="plan")
    return plan


def solve_for_supply(registry: Registry, request: SupplyRequest) -> ProductionPlan:
    """Solve backwards: a supply cap in, the rate it buys and the plan out.

    The system is linear and homogeneous in its right-hand side, so the whole
    chain scales with the target rate. That is what makes the reverse direction
    exact without an optimizer: solve once for a unit of the target, read off how
    much of each supplied item that unit costs, and the binding cap is the
    smallest ``supply / cost`` ratio. The plan is then RE-SOLVED at that rate
    rather than scaled from the unit plan, so the forward path's refusals - the
    negative-machine check above all - apply to the answer that is actually
    returned.

    Args:
        registry: The built registry.
        request: The supply caps, the single target item, the selected recipes,
            the raw set and the policy.

    Returns:
        The plan at the largest rate the supply sustains.

    Raises:
        ByproductPolicyRequired: The policy is missing or unrecognized.
        UnboundedSupply: No supplied item is consumed by the chain, so nothing
            limits the target.
        ValueError: As :func:`solve_for_targets`.
        InexactValueError: A supply figure is not exactly a Fraction.
        UnsolvableChain: As :func:`solve_for_targets`.
        UnderdeterminedChain: As :func:`solve_for_targets`.
        InfeasibleChain: As :func:`solve_for_targets`.
    """
    audit_exact(request, path="request")
    _check_policy(request.byproduct_policy)

    unit = solve_for_targets(
        registry,
        RatioRequest(
            targets=MappingProxyType({request.target_item: Fraction(1)}),
            recipes=request.recipes,
            raw_items=request.raw_items,
            byproduct_policy=request.byproduct_policy,
        ),
    )

    # Sorted so the binding item - and therefore the arithmetic - is the same on
    # every run. A tie between two equally binding items gives the same scale
    # either way, but only a stated order makes that a fact rather than a hope.
    caps: list[Fraction] = []
    for item in sorted(request.supply):
        available = _require_fraction(request.supply[item], f"request.supply[{item!r}]")
        cost = unit.raw_inputs.get(item, Fraction(0))
        if cost > 0:
            caps.append(available / cost)

    if not caps:
        raise UnboundedSupply(
            f"nothing in the supply limits {request.target_item}: none of "
            f"{', '.join(sorted(request.supply)) or 'the empty supply'} is consumed by the "
            "selected recipes, so every rate satisfies this request equally"
        )

    plan = solve_for_targets(
        registry,
        RatioRequest(
            targets=MappingProxyType({request.target_item: min(caps)}),
            recipes=request.recipes,
            raw_items=request.raw_items,
            byproduct_policy=request.byproduct_policy,
        ),
    )
    audit_exact(plan, path="plan")
    return plan
