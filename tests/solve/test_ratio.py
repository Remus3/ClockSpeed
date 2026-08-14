"""The pillar 1 ratio solve: the chains it answers, and the four answers it must refuse.

WHY THE EXPECTED VALUES ARE NEVER WRITTEN AS LITERALS HERE
-----------------------------------------------------------
Every number below is either imported from ``tests/solve/synthetic.py`` or derived
by arithmetic FROM those imports. A literal retyped here would be a second copy of
the corpus, and CONVENTIONS.md section 7.2 records what a second copy does: it
drifts, it drifts silently, and the suite that reads it agrees with the drift. The
derived forms are load-bearing rather than decorative - ``C3_GADGET_RESIDUE_YIELD *
C3_GADGET_MACHINES`` states the RELATIONSHIP the solver is supposed to preserve,
so a solver that got the right number by the wrong route still fails.

WHY THIS MODULE RE-DERIVES THE BALANCE SHEET ITSELF
----------------------------------------------------
``_net_per_minute`` and ``_power`` below read :class:`~clockspeed.data.registry.Recipe`
and :class:`~clockspeed.data.registry.Registry` directly and share no code with
``clockspeed/solve/ratio.py``. Checking the solver's plan with the solver's own
primitives would make the two wrong in the same way - CLAUDE.md section 5, agreement
between two agents is not evidence. They are the same few lines
``tests/solve/test_synthetic.py`` uses, and they are duplicated rather than imported
for exactly that reason: importing them would make this module's verdict depend on
a helper the fixture's own suite is also grading itself against.

Note that ``_power`` exists here and NOT in the module under test. Power is
``clockspeed/solve/power.py``'s slice; ``ratio.py`` publishes machine counts and
flow rates only. Reading a building's draw off the registry to confirm a machine
count is an independent cross-check, not a power model.

NO TOLERANCE, AND EQUALITY ALONE IS NOT ENOUGH
-----------------------------------------------
``tests/solve/__init__.py`` binds this module: no ``pytest.approx``, no
``math.isclose``, no epsilon. ``Fraction(1, 2) == 0.5`` is True, so equality alone
passes against a binary approximation that lands on the value. Every numeric
assertion pairs equality with ``type(x) is Fraction`` - ``type`` and not
``isinstance``, because ``isinstance(True, int)`` is True too.

THE STATIC SELF-GATE AT THE BOTTOM
-----------------------------------
The last section parses ``ratio.py``'s own AST. Three of those checks cannot be
written any other way. The no-recursion check is the PROOF that the byproduct loop
is solved as one linear system rather than by a tree walk with cycle detection
bolted on - a recursive solver can pass every chain below by memoizing, so the
absence of recursion has to be asserted about the SOURCE. The banned-operator check
guards a defect that is data-dependent and therefore invisible to a value test:
``Fraction(5, 2) ** Fraction('1.321929')`` returns a float while
``Fraction(5, 2) ** Fraction(2, 1)`` returns a Fraction. And the seam check asserts
an import that is absent, which no runtime probe can see because
``clockspeed.data.registry`` pulls ``docs_extract`` in anyway.
"""

from __future__ import annotations

import ast
from fractions import Fraction
from pathlib import Path
from typing import Final, cast

import pytest

from clockspeed.data.registry import Recipe, Registry, automated_recipes
from clockspeed.solve import ratio
from tests.solve import synthetic

# ---------------------------------------------------------------------------
# This module's own arithmetic - see the docstring on why it is not imported
# ---------------------------------------------------------------------------


def _net_per_minute(recipe: Recipe) -> dict[str, Fraction]:
    """Net flow of every item one machine of ``recipe`` moves per minute.

    Args:
        recipe: A recipe with a non-zero duration. C6 never reaches here, which
            is the point of C6: nothing may divide by that duration.

    Returns:
        Item key to signed rate. Negative is consumption, positive production.
    """
    cycles = Fraction(synthetic.SECONDS_PER_MINUTE) / recipe.duration
    net: dict[str, Fraction] = {}
    for side, sign in ((recipe.inputs, -1), (recipe.outputs, 1)):
        for flow in side:
            net[flow.item_key] = net.get(flow.item_key, Fraction(0)) + sign * flow.amount * cycles
    return net


def _balance(registry: Registry, plan: ratio.ProductionPlan) -> dict[str, Fraction]:
    """Re-derive the whole plan's net flow sheet from the registry.

    Independent of the solver: it reads the plan's machine counts and nothing
    else of the solver's, then recomputes every rate from the recipes.

    Args:
        registry: The registry the plan was solved against.
        plan: The plan under test.

    Returns:
        Item key to net rate per minute across the whole plan.
    """
    total: dict[str, Fraction] = {}
    for step in plan.steps:
        for key, rate in _net_per_minute(registry.recipes[step.recipe_key]).items():
            total[key] = total.get(key, Fraction(0)) + step.machines * rate
    return total


def _power(registry: Registry, plan: ratio.ProductionPlan) -> Fraction:
    """Total draw of a plan, read off the registry rather than restated.

    Args:
        registry: The registry the plan was solved against.
        plan: The plan under test. Every step's recipe must name exactly one
            producing building, which the solve corpus guarantees.

    Returns:
        Megawatts as an exact Fraction.
    """
    total = Fraction(0)
    for step in plan.steps:
        (building,) = registry.recipes[step.recipe_key].produced_in
        draw = registry.buildings[building].power_consumption
        assert draw is not None, building
        total += step.machines * draw
    return total


def _machines(plan: ratio.ProductionPlan) -> dict[str, Fraction]:
    """Index a plan's steps by recipe key.

    Args:
        plan: The plan under test.

    Returns:
        Recipe key to machine count.
    """
    return {step.recipe_key: step.machines for step in plan.steps}


def _assert_exact(value: object) -> None:
    """Assert a value is an exact Fraction and not a binary approximation of one.

    Args:
        value: The value under test.
    """
    assert type(value) is Fraction, f"{value!r} is {type(value).__name__}, not Fraction"


# ---------------------------------------------------------------------------
# Shared request material, all derived from the corpus
# ---------------------------------------------------------------------------

#: The corpus's declared raw inputs, as the tuple the request carries. A tuple
#: and not a frozenset because ``exact.audit_exact`` walks dataclasses, mappings,
#: tuples and lists and REFUSES anything else - a set-valued field would make
#: every request fail its own entry audit.
_RAW: Final = tuple(sorted(synthetic.SOLVE_RAW_ITEMS))

#: A nonzero demand for the chains whose only interesting property is that they
#: cannot be met. Borrowed from a published target rather than written as a fresh
#: literal: the VALUE is irrelevant to those chains, only its being nonzero is.
_NONZERO_DEMAND: Final = synthetic.C3_GADGET_TARGET

#: The four recipes of the C3 byproduct loop.
_C3_RECIPES: Final = (
    synthetic.GADGET_RECIPE,
    synthetic.RECOVER_RECIPE,
    synthetic.FLUID_RECIPE,
    synthetic.PLATE_RECIPE,
)


@pytest.fixture(name="registry", scope="module")
def registry_fixture() -> Registry:
    """The built solve corpus.

    Returns:
        The registry every phase 3 slice tests against.
    """
    return synthetic.solve_registry()


def _request(
    targets: dict[str, Fraction],
    recipes: tuple[str, ...],
    policy: str = ratio.BYPRODUCT_BALANCED,
) -> ratio.RatioRequest:
    """Build a target-rate request against the corpus's raw set.

    Args:
        targets: Item key to requested net rate per minute.
        recipes: The selected recipe keys.
        policy: The byproduct policy. Stated at every call site rather than
            defaulted in the module under test - see the policy tests.

    Returns:
        The request.
    """
    return ratio.RatioRequest(
        targets=targets, recipes=recipes, raw_items=_RAW, byproduct_policy=policy
    )


# ---------------------------------------------------------------------------
# C1 - linear two-stage
# ---------------------------------------------------------------------------


def test_c1_two_stage_machine_counts(registry: Registry) -> None:
    plan = ratio.solve_for_targets(
        registry,
        _request(
            {synthetic.SOLVE_ROD_ITEM: synthetic.C1_ROD_TARGET},
            (synthetic.ROD_RECIPE, synthetic.PLATE_RECIPE),
        ),
    )
    counts = _machines(plan)
    assert counts[synthetic.ROD_RECIPE] == synthetic.C1_ROD_MACHINES
    assert counts[synthetic.PLATE_RECIPE] == synthetic.C1_PLATE_MACHINES
    _assert_exact(counts[synthetic.ROD_RECIPE])
    _assert_exact(counts[synthetic.PLATE_RECIPE])


def test_c1_raw_demand_and_power_match_the_corpus(registry: Registry) -> None:
    plan = ratio.solve_for_targets(
        registry,
        _request(
            {synthetic.SOLVE_ROD_ITEM: synthetic.C1_ROD_TARGET},
            (synthetic.ROD_RECIPE, synthetic.PLATE_RECIPE),
        ),
    )
    assert plan.raw_inputs[synthetic.SOLVE_ORE_ITEM] == synthetic.C1_ORE_DEMAND
    _assert_exact(plan.raw_inputs[synthetic.SOLVE_ORE_ITEM])
    assert _power(registry, plan) == synthetic.C1_POWER_MW
    # The intermediate really is balanced, re-derived rather than trusted.
    assert _balance(registry, plan)[synthetic.SOLVE_PLATE_ITEM] == 0
    assert plan.targets[synthetic.SOLVE_ROD_ITEM] == synthetic.C1_ROD_TARGET


def test_c1_reports_the_raw_item_as_consumption_not_as_a_negative_net(
    registry: Registry,
) -> None:
    # The sign convention is a real hazard: the balance sheet's Ore entry is
    # NEGATIVE and the published demand is positive. A plan that echoed the raw
    # net verbatim would report -50 where the corpus says 50, and every consumer
    # of raw_inputs would be off by a sign.
    plan = ratio.solve_for_targets(
        registry,
        _request(
            {synthetic.SOLVE_ROD_ITEM: synthetic.C1_ROD_TARGET},
            (synthetic.ROD_RECIPE, synthetic.PLATE_RECIPE),
        ),
    )
    assert _balance(registry, plan)[synthetic.SOLVE_ORE_ITEM] < 0
    assert plan.raw_inputs[synthetic.SOLVE_ORE_ITEM] > 0
    assert (
        -_balance(registry, plan)[synthetic.SOLVE_ORE_ITEM]
        == (plan.raw_inputs[synthetic.SOLVE_ORE_ITEM])
    )


# ---------------------------------------------------------------------------
# C2 - fluid, the do-not-divide-twice trap
# ---------------------------------------------------------------------------


def _c2_plan(registry: Registry) -> ratio.ProductionPlan:
    """Solve C2 at its published fluid target.

    Args:
        registry: The corpus registry.

    Returns:
        The plan.
    """
    return ratio.solve_for_targets(
        registry,
        _request(
            {synthetic.SOLVE_FLUID_ITEM: synthetic.C2_FLUID_TARGET}, (synthetic.FLUID_RECIPE,)
        ),
    )


def test_c2_fluid_target_is_normalized_exactly_once(registry: Registry) -> None:
    plan = _c2_plan(registry)
    machines = _machines(plan)[synthetic.FLUID_RECIPE]
    assert machines == synthetic.C2_REFINERY_MACHINES
    _assert_exact(machines)
    assert plan.raw_inputs[synthetic.SOLVE_ORE_ITEM] == synthetic.C2_ORE_DEMAND
    assert _power(registry, plan) == synthetic.C2_POWER_MW


def test_c2_rejects_both_wrong_unit_answers(registry: Registry) -> None:
    # Both wrong answers are finite, positive and render without complaint. A
    # test that pinned only the right one could not say the wrong ones were
    # unreachable, so both are named.
    machines = _machines(_c2_plan(registry))[synthetic.FLUID_RECIPE]
    assert machines != synthetic.C2_DIVIDED_TWICE_MACHINES
    assert machines != synthetic.C2_READ_AS_LITRES_MACHINES


# ---------------------------------------------------------------------------
# C3 - the byproduct loop, the load-bearing case for the whole phase
# ---------------------------------------------------------------------------


def _c3_plan(registry: Registry, policy: str = ratio.BYPRODUCT_BALANCED) -> ratio.ProductionPlan:
    """Solve C3 at its published target.

    Args:
        registry: The corpus registry.
        policy: The byproduct policy under test.

    Returns:
        The plan.
    """
    return ratio.solve_for_targets(
        registry,
        _request({synthetic.SOLVE_GADGET_ITEM: synthetic.C3_GADGET_TARGET}, _C3_RECIPES, policy),
    )


def test_c3_byproduct_loop_machine_counts(registry: Registry) -> None:
    counts = _machines(_c3_plan(registry))
    assert counts[synthetic.GADGET_RECIPE] == synthetic.C3_GADGET_MACHINES
    assert counts[synthetic.RECOVER_RECIPE] == synthetic.C3_RECOVER_MACHINES
    assert counts[synthetic.FLUID_RECIPE] == synthetic.C3_FLUID_MACHINES
    assert counts[synthetic.PLATE_RECIPE] == synthetic.C3_PLATE_MACHINES
    for value in counts.values():
        _assert_exact(value)


def test_c3_every_intermediate_balances_to_zero(registry: Registry) -> None:
    # Re-derived from the registry, not read off the solver. The loop's whole
    # difficulty is that Fluid and Residue each have a producer AND a consumer
    # inside the set, so a solver that dropped either equation would still
    # return a plausible plan.
    plan = _c3_plan(registry)
    sheet = _balance(registry, plan)
    for intermediate in (
        synthetic.SOLVE_PLATE_ITEM,
        synthetic.SOLVE_FLUID_ITEM,
        synthetic.SOLVE_RESIDUE_ITEM,
    ):
        assert sheet[intermediate] == 0, intermediate
    assert sheet[synthetic.SOLVE_GADGET_ITEM] == synthetic.C3_GADGET_TARGET


def test_c3_raw_demand_and_power_match_the_corpus(registry: Registry) -> None:
    plan = _c3_plan(registry)
    assert plan.raw_inputs[synthetic.SOLVE_ORE_ITEM] == synthetic.C3_ORE_DEMAND
    assert _power(registry, plan) == synthetic.C3_POWER_MW
    _assert_exact(_power(registry, plan))


def test_c3_is_identical_under_both_byproduct_policies(registry: Registry) -> None:
    # Residue is CONSUMED inside the set, so it is an intermediate and not a
    # byproduct at all. The policy must therefore be irrelevant here. A solver
    # that classified any produced item as a byproduct would answer C3
    # differently under the two policies, and one of those answers would be
    # wrong while looking exactly as confident as the other.
    balanced = _c3_plan(registry, ratio.BYPRODUCT_BALANCED)
    sinkable = _c3_plan(registry, ratio.BYPRODUCT_SINKABLE)
    assert _machines(balanced) == _machines(sinkable)
    assert (
        balanced.raw_inputs[synthetic.SOLVE_ORE_ITEM]
        == (sinkable.raw_inputs[synthetic.SOLVE_ORE_ITEM])
    )
    assert balanced.byproducts == {}
    assert sinkable.byproducts == {}


def test_c3_has_no_free_variables_because_gadget_has_one_producer(registry: Registry) -> None:
    # The fence tests/solve/test_synthetic.py::test_c3_gadget_has_exactly_one_
    # producing_recipe protects, restated as a property of the SOLVE: a second
    # producer would make this underdetermined and the published counts would
    # stop being the answer.
    plan = _c3_plan(registry)
    assert len(plan.steps) == len(_C3_RECIPES)


# ---------------------------------------------------------------------------
# C4 - the loop, reverse direction
# ---------------------------------------------------------------------------


def _c4_plan(registry: Registry) -> ratio.ProductionPlan:
    """Solve C4: the C3 loop driven backwards from the published ore cap.

    Args:
        registry: The corpus registry.

    Returns:
        The plan.
    """
    return ratio.solve_for_supply(
        registry,
        ratio.SupplyRequest(
            supply={synthetic.SOLVE_ORE_ITEM: synthetic.C4_ORE_CAP},
            target_item=synthetic.SOLVE_GADGET_ITEM,
            recipes=_C3_RECIPES,
            raw_items=_RAW,
            byproduct_policy=ratio.BYPRODUCT_BALANCED,
        ),
    )


def test_c4_reverse_direction_hits_the_published_rate(registry: Registry) -> None:
    plan = _c4_plan(registry)
    assert plan.targets[synthetic.SOLVE_GADGET_ITEM] == synthetic.C4_GADGET_RATE
    _assert_exact(plan.targets[synthetic.SOLVE_GADGET_ITEM])
    counts = _machines(plan)
    assert counts[synthetic.GADGET_RECIPE] == synthetic.C4_GADGET_MACHINES
    assert counts[synthetic.RECOVER_RECIPE] == synthetic.C4_RECOVER_MACHINES
    assert counts[synthetic.FLUID_RECIPE] == synthetic.C4_FLUID_MACHINES
    assert counts[synthetic.PLATE_RECIPE] == synthetic.C4_PLATE_MACHINES


def test_c4_consumes_exactly_the_cap_and_no_more(registry: Registry) -> None:
    plan = _c4_plan(registry)
    assert plan.raw_inputs[synthetic.SOLVE_ORE_ITEM] == synthetic.C4_ORE_CAP
    sheet = _balance(registry, plan)
    for intermediate in (
        synthetic.SOLVE_PLATE_ITEM,
        synthetic.SOLVE_FLUID_ITEM,
        synthetic.SOLVE_RESIDUE_ITEM,
    ):
        assert sheet[intermediate] == 0, intermediate


def test_c4_power_cross_checks_c3_exactly(registry: Registry) -> None:
    # The two chains were derived from OPPOSITE directions, so this landing
    # exactly is evidence about C3 and not merely about C4. Asserted on the
    # published constants as well as on the solved plan, because the constant
    # identity is what makes the plan's agreement meaningful.
    assert synthetic.C3_POWER_MW * synthetic.C4_SCALE == synthetic.C4_POWER_MW
    assert Fraction(436, 3) * Fraction(3, 4) == Fraction(109)
    power = _power(registry, _c4_plan(registry))
    assert power == synthetic.C4_POWER_MW
    _assert_exact(power)


def test_c4_scale_is_the_cap_over_c3s_demand(registry: Registry) -> None:
    forward = _c3_plan(registry)
    reverse = _c4_plan(registry)
    scale = synthetic.C4_ORE_CAP / forward.raw_inputs[synthetic.SOLVE_ORE_ITEM]
    assert scale == synthetic.C4_SCALE
    assert _machines(reverse)[synthetic.GADGET_RECIPE] == (
        _machines(forward)[synthetic.GADGET_RECIPE] * scale
    )


# ---------------------------------------------------------------------------
# REFUSAL 1 - INCONSISTENT, C7
# ---------------------------------------------------------------------------


def test_c7_inconsistent_chain_refuses_and_names_the_unproducible_item(
    registry: Registry,
) -> None:
    # Desc_SolveOrphan_C is consumed by R_Orphan, produced by nothing and is not
    # raw, so its balance forces R_Orphan to zero and the Relic demand cannot be
    # met at any rate. Naming Relic - the caller's own target - would be useless;
    # the finding is the item the chain cannot supply.
    with pytest.raises(ratio.UnsolvableChain) as caught:
        ratio.solve_for_targets(
            registry,
            _request({synthetic.SOLVE_RELIC_ITEM: _NONZERO_DEMAND}, (synthetic.ORPHAN_RECIPE,)),
        )
    assert caught.value.item == synthetic.SOLVE_ORPHAN_ITEM


def test_c7_at_zero_demand_is_consistent_and_builds_nothing(registry: Registry) -> None:
    # The refusal must be about the DEMAND being unmeetable, not about the shape
    # of the chain. At zero the same system is perfectly solvable, and a solver
    # that refused on structure alone would refuse here too.
    plan = ratio.solve_for_targets(
        registry,
        _request({synthetic.SOLVE_RELIC_ITEM: Fraction(0)}, (synthetic.ORPHAN_RECIPE,)),
    )
    assert _machines(plan)[synthetic.ORPHAN_RECIPE] == 0


# ---------------------------------------------------------------------------
# REFUSAL 2 - UNDERDETERMINED, C8
# ---------------------------------------------------------------------------


def test_c8_underdetermined_chain_reports_free_variables_by_recipe_key(
    registry: Registry,
) -> None:
    # Pinning the free variable to zero is the plausible wrong answer: it yields
    # a full vector of exact Fractions that satisfies every equation and is one
    # arbitrary member of an infinite family. Nothing downstream could tell it
    # from the answer, which is why this refuses instead.
    with pytest.raises(ratio.UnderdeterminedChain) as caught:
        ratio.solve_for_targets(
            registry,
            _request(
                {synthetic.SOLVE_TWIN_ITEM: synthetic.C8_TWIN_PER_MACHINE * 2},
                (synthetic.TWIN_A_RECIPE, synthetic.TWIN_B_RECIPE),
            ),
        )
    assert caught.value.free_recipes == (synthetic.TWIN_B_RECIPE,)
    # A recipe KEY, not a column index. An index is meaningless to a caller and
    # silently wrong the moment the recipe order changes.
    for key in caught.value.free_recipes:
        assert key in registry.recipes


def test_c8_returns_no_plan_at_all(registry: Registry) -> None:
    with pytest.raises(ratio.UnderdeterminedChain) as caught:
        ratio.solve_for_targets(
            registry,
            _request(
                {synthetic.SOLVE_TWIN_ITEM: synthetic.C8_TWIN_PER_MACHINE * 2},
                (synthetic.TWIN_A_RECIPE, synthetic.TWIN_B_RECIPE),
            ),
        )
    assert not isinstance(caught.value, ratio.ProductionPlan)
    assert not hasattr(caught.value, "steps")


def test_the_whole_automated_registry_is_underdetermined(registry: Registry) -> None:
    # Why pillar 2 exists. Handed every automated recipe, the ratio solve does
    # not pick one - it reports that the system does not determine a plan. A
    # solver that quietly returned SOME plan here would be inventing a recipe
    # selection it has no basis for.
    keys = tuple(recipe.key for recipe in automated_recipes(registry))
    with pytest.raises(ratio.UnderdeterminedChain) as caught:
        ratio.solve_for_targets(
            registry,
            _request(
                {synthetic.SOLVE_GADGET_ITEM: synthetic.C3_GADGET_TARGET},
                keys,
                ratio.BYPRODUCT_SINKABLE,
            ),
        )
    assert synthetic.TWIN_B_RECIPE in caught.value.free_recipes


# ---------------------------------------------------------------------------
# REFUSAL 3 - NEGATIVE SOLUTION, C9
# ---------------------------------------------------------------------------


def test_c9_negative_machine_count_is_refused_naming_the_recipe() -> None:
    # THE most likely silent wrong answer in the whole pillar. A pure linear
    # solve happily returns a negative machine count - a recipe run backwards -
    # and wraps a confident plan around it. Nothing about the vector announces
    # it: every entry is an exact Fraction and every equation balances.
    variant = synthetic.rich_recovery_registry()
    with pytest.raises(ratio.InfeasibleChain) as caught:
        ratio.solve_for_targets(
            variant,
            _request(
                {synthetic.SOLVE_GADGET_ITEM: synthetic.C3_GADGET_TARGET},
                (
                    synthetic.GADGET_RECIPE,
                    synthetic.RICH_RECOVER_RECIPE,
                    synthetic.FLUID_RECIPE,
                    synthetic.PLATE_RECIPE,
                ),
            ),
        )
    assert caught.value.recipe == synthetic.FLUID_RECIPE
    # The exact negative the corpus publishes. This is what proves the refusal
    # came from the arithmetic rather than from some unrelated guard: the solver
    # really did compute -6/5 machines and really did refuse to report it.
    assert caught.value.machines == synthetic.C9_FLUID_MACHINES
    _assert_exact(caught.value.machines)
    assert caught.value.machines < 0


def test_c9s_ordinary_twin_still_solves(registry: Registry) -> None:
    # The negative refusal must not be a blanket refusal of the loop shape. The
    # same four-recipe loop with the ordinary recovery recipe is C3 and answers.
    assert _machines(_c3_plan(registry))[synthetic.FLUID_RECIPE] > 0


# ---------------------------------------------------------------------------
# REFUSAL 4 - ZERO DURATION, C6
# ---------------------------------------------------------------------------


def test_c6_zero_duration_recipe_is_excluded_with_a_stated_reason(registry: Registry) -> None:
    # The registry KEEPS a measured zero duration on build-gun recipes and skips
    # only an absent one, so this is real input. Excluding it silently would be
    # as wrong as dividing by it: the caller asked for a recipe and got a plan
    # that does not contain it.
    plan = ratio.solve_for_targets(
        registry,
        _request(
            {synthetic.SOLVE_PLATE_ITEM: synthetic.C1_PLATE_PER_MACHINE},
            (synthetic.PLATE_RECIPE, synthetic.ZERO_DURATION_RECIPE),
        ),
    )
    assert [note.recipe_key for note in plan.excluded] == [synthetic.ZERO_DURATION_RECIPE]
    assert plan.excluded[0].reason == ratio.EXCLUDED_ZERO_DURATION
    assert synthetic.ZERO_DURATION_RECIPE not in _machines(plan)
    assert _machines(plan)[synthetic.PLATE_RECIPE] == 1


def test_c6_never_divides_by_the_measured_zero(registry: Registry) -> None:
    # If the zero duration reached exact.per_minute it would raise
    # UndefinedRateError, and if it reached a bare division it would raise
    # ZeroDivisionError. Neither escaping is the evidence.
    plan = ratio.solve_for_targets(
        registry,
        _request(
            {synthetic.SOLVE_PLATE_ITEM: synthetic.C1_PLATE_PER_MACHINE},
            (synthetic.PLATE_RECIPE, synthetic.ZERO_DURATION_RECIPE),
        ),
    )
    assert registry.recipes[synthetic.ZERO_DURATION_RECIPE].duration == synthetic.ZERO_DURATION
    assert plan.raw_inputs[synthetic.SOLVE_ORE_ITEM] == synthetic.C1_PLATE_PER_MACHINE


def test_c6_alone_refuses_rather_than_dividing(registry: Registry) -> None:
    # With every usable recipe excluded the demand cannot be met, and the answer
    # must be the ordinary inconsistency refusal - not a crash inside the rate
    # conversion, and not an empty plan reported as success.
    with pytest.raises(ratio.UnsolvableChain) as caught:
        ratio.solve_for_targets(
            registry,
            _request(
                {synthetic.SOLVE_SMELTER_DESCRIPTOR: _NONZERO_DEMAND},
                (synthetic.ZERO_DURATION_RECIPE,),
            ),
        )
    assert caught.value.item == synthetic.SOLVE_SMELTER_DESCRIPTOR


# ---------------------------------------------------------------------------
# THE BYPRODUCT POLICY - no default, and it changes the answer
# ---------------------------------------------------------------------------

#: C3 with the recovery half removed. Residue is then produced by R_Gadget and
#: consumed by nothing, which is the genuine unconsumed-byproduct shape.
_OPEN_LOOP_RECIPES: Final = (
    synthetic.GADGET_RECIPE,
    synthetic.FLUID_RECIPE,
    synthetic.PLATE_RECIPE,
)


def test_an_unconsumed_byproduct_under_sinkable_is_reported_not_ignored(
    registry: Registry,
) -> None:
    plan = ratio.solve_for_targets(
        registry,
        _request(
            {synthetic.SOLVE_GADGET_ITEM: synthetic.C3_GADGET_TARGET},
            _OPEN_LOOP_RECIPES,
            ratio.BYPRODUCT_SINKABLE,
        ),
    )
    # Derived from published constants, never restated: the Gadget machine count
    # is unchanged from C3 because the Gadget equation is unchanged, so the
    # Residue that has to go somewhere is its per-machine yield times that count.
    expected = synthetic.C3_GADGET_RESIDUE_YIELD * synthetic.C3_GADGET_MACHINES
    assert plan.byproducts[synthetic.SOLVE_RESIDUE_ITEM] == expected
    _assert_exact(plan.byproducts[synthetic.SOLVE_RESIDUE_ITEM])
    assert _machines(plan)[synthetic.GADGET_RECIPE] == synthetic.C3_GADGET_MACHINES


def test_the_sinkable_open_loop_costs_more_ore_than_the_closed_one(
    registry: Registry,
) -> None:
    # Without the recovery half every cubic metre of Fluid is made from fresh
    # ore, so the open loop must cost strictly more. Derived from the C3
    # coefficients rather than written down.
    plan = ratio.solve_for_targets(
        registry,
        _request(
            {synthetic.SOLVE_GADGET_ITEM: synthetic.C3_GADGET_TARGET},
            _OPEN_LOOP_RECIPES,
            ratio.BYPRODUCT_SINKABLE,
        ),
    )
    fluid_machines = (
        -synthetic.C3_GADGET_FLUID_DRAW * synthetic.C3_GADGET_MACHINES / synthetic.C3_FLUID_YIELD
    )
    assert _machines(plan)[synthetic.FLUID_RECIPE] == fluid_machines
    expected_ore = (
        -synthetic.C3_PLATE_ORE_DRAW * synthetic.C3_PLATE_MACHINES
        - synthetic.C3_FLUID_ORE_DRAW * fluid_machines
    )
    assert plan.raw_inputs[synthetic.SOLVE_ORE_ITEM] == expected_ore
    assert plan.raw_inputs[synthetic.SOLVE_ORE_ITEM] > synthetic.C3_ORE_DEMAND


def test_the_same_open_loop_under_balanced_is_refused(registry: Registry) -> None:
    # THE point of the policy. Balanced means the byproduct may not accumulate,
    # and with no consumer the only balance is zero Gadget machines - which
    # contradicts the target. Same registry, same recipes, same target, opposite
    # verdict. "Assume byproducts vanish" would have answered both.
    with pytest.raises(ratio.UnsolvableChain) as caught:
        ratio.solve_for_targets(
            registry,
            _request(
                {synthetic.SOLVE_GADGET_ITEM: synthetic.C3_GADGET_TARGET},
                _OPEN_LOOP_RECIPES,
                ratio.BYPRODUCT_BALANCED,
            ),
        )
    assert caught.value.item == synthetic.SOLVE_RESIDUE_ITEM


def test_a_policy_outside_the_two_named_ones_is_refused(registry: Registry) -> None:
    for policy in ("", "vanish", ratio.BYPRODUCT_BALANCED.upper()):
        with pytest.raises(ratio.ByproductPolicyRequired) as caught:
            ratio.solve_for_targets(
                registry,
                _request(
                    {synthetic.SOLVE_ROD_ITEM: synthetic.C1_ROD_TARGET},
                    (synthetic.ROD_RECIPE, synthetic.PLATE_RECIPE),
                    policy,
                ),
            )
        assert caught.value.policy == policy


def test_the_request_dataclass_supplies_no_default_policy() -> None:
    # A default in the dataclass would put "assume byproducts vanish" back in
    # through the constructor, where no test of the solve path could see it.
    with pytest.raises(TypeError):
        ratio.RatioRequest(  # type: ignore[call-arg]
            targets={}, recipes=(), raw_items=_RAW
        )


def test_the_two_policies_are_the_only_ones_published() -> None:
    assert set(ratio.BYPRODUCT_POLICIES) == {ratio.BYPRODUCT_BALANCED, ratio.BYPRODUCT_SINKABLE}
    # Named rather than counted: a third policy is exactly the "assume it
    # vanishes" reading sneaking back in, and a bare 2 would not say so.
    assert ratio.BYPRODUCT_POLICIES == (ratio.BYPRODUCT_BALANCED, ratio.BYPRODUCT_SINKABLE)


# ---------------------------------------------------------------------------
# Determinism - proved, not asserted
# ---------------------------------------------------------------------------


def test_two_runs_on_one_input_are_byte_identical(registry: Registry) -> None:
    first = _c3_plan(registry)
    second = _c3_plan(registry)
    assert repr(first) == repr(second)
    assert first == second


def test_the_plan_does_not_depend_on_the_order_of_the_request(registry: Registry) -> None:
    # Two writings of the same request. If the plan's ordering came from the
    # caller rather than from the registry, these would differ in repr while
    # comparing equal on the numbers - a difference that only a byte comparison
    # catches.
    forward = ratio.solve_for_targets(
        registry,
        _request({synthetic.SOLVE_GADGET_ITEM: synthetic.C3_GADGET_TARGET}, _C3_RECIPES),
    )
    reversed_plan = ratio.solve_for_targets(
        registry,
        _request(
            {synthetic.SOLVE_GADGET_ITEM: synthetic.C3_GADGET_TARGET}, tuple(reversed(_C3_RECIPES))
        ),
    )
    assert repr(forward) == repr(reversed_plan)


def test_a_duplicated_recipe_key_does_not_double_the_plan(registry: Registry) -> None:
    plain = ratio.solve_for_targets(
        registry,
        _request({synthetic.SOLVE_GADGET_ITEM: synthetic.C3_GADGET_TARGET}, _C3_RECIPES),
    )
    doubled = ratio.solve_for_targets(
        registry,
        _request(
            {synthetic.SOLVE_GADGET_ITEM: synthetic.C3_GADGET_TARGET},
            (*_C3_RECIPES, synthetic.FLUID_RECIPE),
        ),
    )
    assert repr(plain) == repr(doubled)


def test_two_independently_built_registries_agree(registry: Registry) -> None:
    # The registry is rebuilt from the corpus text rather than reused. Two
    # builds of one document are supposed to be byte identical; this is the
    # solve layer's half of that claim.
    other = synthetic.solve_registry()
    assert other is not registry
    assert repr(_c3_plan(registry)) == repr(_c3_plan(other))


def test_multiple_targets_are_ordered_deterministically(registry: Registry) -> None:
    first = ratio.solve_for_targets(
        registry,
        _request(
            {
                synthetic.SOLVE_ROD_ITEM: synthetic.C1_ROD_TARGET,
                synthetic.SOLVE_FLUID_ITEM: synthetic.C2_FLUID_TARGET,
            },
            (synthetic.ROD_RECIPE, synthetic.PLATE_RECIPE, synthetic.FLUID_RECIPE),
        ),
    )
    second = ratio.solve_for_targets(
        registry,
        _request(
            {
                synthetic.SOLVE_FLUID_ITEM: synthetic.C2_FLUID_TARGET,
                synthetic.SOLVE_ROD_ITEM: synthetic.C1_ROD_TARGET,
            },
            (synthetic.FLUID_RECIPE, synthetic.PLATE_RECIPE, synthetic.ROD_RECIPE),
        ),
    )
    assert repr(first) == repr(second)
    assert list(first.targets) == sorted(first.targets)


# ---------------------------------------------------------------------------
# Exactness at the seam
# ---------------------------------------------------------------------------


def test_the_plan_passes_audit_exact(registry: Registry) -> None:
    from clockspeed.solve.exact import audit_exact  # noqa: PLC0415

    audit_exact(_c3_plan(registry), path="plan")
    audit_exact(_c4_plan(registry), path="plan")


def test_every_numeric_leaf_of_the_plan_is_a_fraction(registry: Registry) -> None:
    plan = ratio.solve_for_targets(
        registry,
        _request(
            {synthetic.SOLVE_GADGET_ITEM: synthetic.C3_GADGET_TARGET},
            _OPEN_LOOP_RECIPES,
            ratio.BYPRODUCT_SINKABLE,
        ),
    )
    for step in plan.steps:
        _assert_exact(step.machines)
    for sheet in (plan.targets, plan.raw_inputs, plan.byproducts):
        for value in sheet.values():
            _assert_exact(value)


def test_the_plan_is_frozen(registry: Registry) -> None:
    plan = _c3_plan(registry)
    with pytest.raises(AttributeError):
        plan.steps = ()  # type: ignore[misc]


def test_an_int_target_rate_is_refused_even_though_it_is_exact(registry: Registry) -> None:
    # int is an ADMITTED leaf for audit_exact - counts and ranks are legitimately
    # ints - so the request-level audit cannot catch this one. It still has to be
    # refused, because int / int is a float: an all-int system contains no floats
    # and manufactures them the moment a pivot row is normalized.
    from clockspeed.solve.exact import InexactValueError  # noqa: PLC0415

    rates = cast("dict[str, Fraction]", {synthetic.SOLVE_ROD_ITEM: 50})
    with pytest.raises(InexactValueError):
        ratio.solve_for_targets(
            registry, _request(rates, (synthetic.ROD_RECIPE, synthetic.PLATE_RECIPE))
        )


def test_an_unknown_recipe_key_is_refused(registry: Registry) -> None:
    with pytest.raises(ValueError, match="Nope_C"):
        ratio.solve_for_targets(
            registry, _request({synthetic.SOLVE_ROD_ITEM: synthetic.C1_ROD_TARGET}, ("Nope_C",))
        )


def test_an_unbounded_supply_request_is_refused(registry: Registry) -> None:
    # No supplied item is consumed by the chain, so the target has no cap at all
    # and every rate satisfies the request. Reporting one would be reporting an
    # arbitrary member of an unbounded family.
    with pytest.raises(ratio.UnboundedSupply):
        ratio.solve_for_supply(
            registry,
            ratio.SupplyRequest(
                supply={synthetic.SOLVE_RARE_ITEM: synthetic.C4_ORE_CAP},
                target_item=synthetic.SOLVE_GADGET_ITEM,
                recipes=_C3_RECIPES,
                raw_items=_RAW,
                byproduct_policy=ratio.BYPRODUCT_BALANCED,
            ),
        )


# ---------------------------------------------------------------------------
# The static self-gate - see the module docstring on why these cannot be
# written as value tests
# ---------------------------------------------------------------------------

_RATIO_PATH: Final = Path(ratio.__file__)
_RATIO_SOURCE: Final = _RATIO_PATH.read_text(encoding="ascii")
_RATIO_TREE: Final = ast.parse(_RATIO_SOURCE)


def _functions(tree: ast.Module) -> list[ast.FunctionDef]:
    """Every module-level function definition in a parsed module.

    Args:
        tree: The parsed module.

    Returns:
        The function definitions, in source order.
    """
    return [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]


def test_the_module_source_is_seven_bit_ascii() -> None:
    # Reading it with encoding="ascii" at import time is the assertion; this
    # test states the rule so a failure reads as the rule it broke.
    # BOOTSTRAP.md section 12 item 4, and PowerShell 5.1 is the mechanism.
    assert _RATIO_SOURCE.isascii()


def test_the_module_never_recurses(registry: Registry) -> None:
    # THE proof that C3 is solved as one linear system rather than by a tree walk
    # with cycle detection bolted on. A memoizing recursive solver passes every
    # chain above, so this has to be asserted about the source. Both directions
    # are exercised first so the check is about live code.
    assert _c3_plan(registry).steps
    assert _c4_plan(registry).steps
    names = {node.name for node in _functions(_RATIO_TREE)}
    graph = {
        node.name: {
            inner.func.id
            for inner in ast.walk(node)
            if isinstance(inner, ast.Call)
            and isinstance(inner.func, ast.Name)
            and inner.func.id in names
        }
        for node in _functions(_RATIO_TREE)
    }
    for name, callees in graph.items():
        assert name not in callees, f"{name} calls itself"
    remaining = dict(graph)
    while remaining:
        leaves = {name for name, callees in remaining.items() if not (callees & set(remaining))}
        if not leaves:
            break
        remaining = {name: callees for name, callees in remaining.items() if name not in leaves}
    assert not remaining, f"call cycle in ratio.py among {sorted(remaining)}"


def test_the_module_contains_no_power_operator_and_no_float_literal() -> None:
    # Measured on CPython 3.14: Fraction(5, 2) ** Fraction('1.321929') returns a
    # float, while Fraction(5, 2) ** Fraction(2, 1) returns a Fraction. The
    # defect is DATA DEPENDENT, so a value test written with a whole-number
    # exponent passes while the shipped exponent degrades silently. The operator
    # has to be banned at the source.
    for node in ast.walk(_RATIO_TREE):
        assert not isinstance(node, ast.Pow), "** is banned in the solve path"
        if isinstance(node, ast.Constant):
            # Named as a string rather than by the builtin, because the builtin
            # is itself on the banned-name list below.
            assert type(node.value).__name__ not in {"float", "complex"}, ast.dump(node)


def test_the_module_never_names_a_banned_builtin() -> None:
    banned = {"float", "complex", "pow", "round"}
    for node in ast.walk(_RATIO_TREE):
        if isinstance(node, ast.Name):
            assert node.id not in banned, node.id
        if isinstance(node, ast.Attribute):
            assert node.attr not in banned, node.attr


def test_the_module_imports_no_inexact_stdlib() -> None:
    banned = {"math", "statistics", "decimal", "cmath", "numpy"}
    for node in ast.walk(_RATIO_TREE):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in banned, alias.name
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".")[0] not in banned, node.module


def test_the_module_reaches_past_no_seam() -> None:
    # BOOTSTRAP.md section 6. solve/ consumes the normalized registry and
    # nothing else: not the install locator, not the raw docs reader, not a
    # save. A runtime probe cannot see this, because importing the registry
    # pulls docs_extract in anyway.
    banned = {
        "clockspeed.data.locate",
        "clockspeed.data.docs_extract",
        "clockspeed.data.blobs",
        "clockspeed.save",
    }
    for node in ast.walk(_RATIO_TREE):
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            assert not any(node.module.startswith(name) for name in banned), node.module
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert not any(alias.name.startswith(name) for name in banned), alias.name
