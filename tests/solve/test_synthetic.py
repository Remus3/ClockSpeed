"""Invariants of the synthetic solve corpus itself - the fixture is verified, not trusted.

WHY A FIXTURE NEEDS ITS OWN TEST MODULE
---------------------------------------
Every phase 3 slice - ratio solve, power, the optimizer backend - asserts against
``tests/solve/synthetic.py``. A fixture that carries a wrong number therefore does
not fail: it teaches every suite above it to expect the wrong number, and all of
them agree. CONVENTIONS.md section 7.2 names that shape - a fixture built parallel
to the implementation stays green through the real defect - and CLAUDE.md section 5
names the reason it is invisible: agreement between two agents is not evidence.

So the corpus is checked here against arithmetic derived from the REGISTRY it
actually builds, never against a second copy of the constants it publishes. Where
a chain has a known wrong answer, the wrong answer is asserted to be different
from the right one, because a test that only pins the right answer cannot say
whether the wrong one was reachable.

THE PER-MINUTE ARITHMETIC BELOW IS DELIBERATELY THIS MODULE'S OWN
-----------------------------------------------------------------
``_net_per_minute`` re-derives rates straight from :class:`Recipe` rather than
calling anything under ``clockspeed/solve/``. That independence is the whole
point of the check: verifying a solver's fixture with the solver's own primitives
would make the two wrong in the same way, which is exactly the parallel-fixture
trap above. It is five lines of long division and it shares no code with the
engine it feeds.

NO TOLERANCE, AND EQUALITY ALONE IS NOT ENOUGH
-----------------------------------------------
``tests/solve/__init__.py`` binds every module here: no ``pytest.approx``, no
``math.isclose``, no epsilon. Note also that ``Fraction(1, 2) == 0.5`` is True, so
an equality assertion passes against a float that happens to land on the value.
Every numeric assertion below therefore pairs equality with ``type(x) is Fraction``
- ``type`` rather than ``isinstance`` because ``isinstance(True, int)`` is True too.
"""

from __future__ import annotations

from fractions import Fraction

import pytest

from clockspeed.data.registry import Recipe, Registry
from tests.solve import synthetic

# ---------------------------------------------------------------------------
# This module's own arithmetic - see the docstring on why it is not imported
# ---------------------------------------------------------------------------


def _net_per_minute(recipe: Recipe) -> dict[str, Fraction]:
    """Net flow of every item one machine of ``recipe`` moves per minute.

    Args:
        recipe: A recipe with a non-zero duration. The zero-duration case is
            asserted separately and never reaches this function, which is the
            point of C6: nothing may divide by that duration.

    Returns:
        Item key to signed rate. Negative is consumption, positive production.
        A byproduct is simply a positive entry, which is what makes the C3 loop
        expressible without a special case.
    """
    cycles = Fraction(synthetic.SECONDS_PER_MINUTE) / recipe.duration
    net: dict[str, Fraction] = {}
    for side, sign in ((recipe.inputs, -1), (recipe.outputs, 1)):
        for flow in side:
            net[flow.item_key] = net.get(flow.item_key, Fraction(0)) + sign * flow.amount * cycles
    return net


def _combined(*terms: tuple[Fraction, dict[str, Fraction]]) -> dict[str, Fraction]:
    """Sum ``machines * rate`` across several recipes into one balance sheet.

    Args:
        *terms: ``(machine count, per-machine rates)`` pairs.

    Returns:
        Item key to net rate across the whole plan.
    """
    total: dict[str, Fraction] = {}
    for machines, rates in terms:
        for key, rate in rates.items():
            total[key] = total.get(key, Fraction(0)) + machines * rate
    return total


def _power(registry: Registry, *terms: tuple[Fraction, str]) -> Fraction:
    """Total draw of a plan, read from the registry rather than restated.

    The registry is a PARAMETER rather than a fresh ``solve_registry()`` call on
    purpose. Rebuilding it here would make every power assertion below read the
    pristine corpus no matter what registry the test was handed, so a corpus
    whose building draws had drifted would still report the published totals.

    Args:
        registry: The registry the caller is asserting against.
        *terms: ``(machine count, building ClassName)`` pairs.

    Returns:
        Megawatts as an exact Fraction.
    """
    total = Fraction(0)
    for machines, building in terms:
        draw = registry.buildings[building].power_consumption
        assert draw is not None, building
        total += machines * draw
    return total


def _assert_exact(value: object) -> None:
    """Assert a value is an exact Fraction and not a float wearing its value.

    Args:
        value: The value under test.
    """
    assert type(value) is Fraction, f"{value!r} is {type(value).__name__}, not Fraction"


@pytest.fixture(name="registry", scope="module")
def registry_fixture() -> Registry:
    """The built solve corpus.

    Returns:
        The registry every phase 3 slice tests against.
    """
    return synthetic.solve_registry()


# ---------------------------------------------------------------------------
# The corpus is a SOLVER fixture, not a parser-trap fixture
# ---------------------------------------------------------------------------


def test_the_main_corpus_builds_with_no_warnings_at_all(registry: Registry) -> None:
    # tests/data/synthetic.py owns every parser trap. If this corpus starts
    # flagging content, a downstream solve test is being handed a registry with
    # something missing from it - an unresolved produced-in token, an item with
    # no descriptor - and the chain arithmetic below would be solving a
    # different factory than the one this file describes.
    assert registry.warnings == ()


def test_the_main_corpus_declares_no_unknown_groups(registry: Registry) -> None:
    assert registry.unknown_groups == ()


def test_every_declared_building_resolves(registry: Registry) -> None:
    for building in synthetic.SOLVE_BUILDINGS:
        assert building in registry.buildings
        _assert_exact(registry.buildings[building].power_consumption)


def test_every_automated_recipe_resolves_its_producer_token(registry: Registry) -> None:
    # An unresolved token is silently "no automated producer", which would make
    # a power total quietly omit a building rather than fail.
    for recipe in registry.recipes.values():
        assert recipe.unresolved_produced_in == (), recipe.key


def test_every_recipe_the_corpus_names_is_present(registry: Registry) -> None:
    assert set(registry.recipes) == set(synthetic.SOLVE_RECIPES)


def test_every_item_reference_has_a_descriptor(registry: Registry) -> None:
    # WARN_UNKNOWN_ITEM leaves an amount UNCONVERTED rather than dropping it,
    # so a missing descriptor on a fluid publishes litres under a contract that
    # promises cubic metres - a factor of a thousand, silently.
    for recipe in registry.recipes.values():
        for flow in (*recipe.inputs, *recipe.outputs):
            assert flow.item_key in registry.items, (recipe.key, flow.item_key)


def test_the_published_producer_set_matches_the_registry(registry: Registry) -> None:
    # SOLVE_PRODUCED is stated in the corpus and checked here rather than
    # derived from it. A derived set would silently shrink when a recipe lost
    # its product, and every feasibility answer built on it would shrink too.
    produced = {flow.item_key for recipe in registry.recipes.values() for flow in recipe.outputs}
    assert produced == set(synthetic.SOLVE_PRODUCED)


def test_the_raw_items_are_produced_by_nothing(registry: Registry) -> None:
    # A raw input with a producing recipe is not raw, and a solver told
    # otherwise would happily build a factory to make its own ore.
    assert not (synthetic.SOLVE_RAW_ITEMS & synthetic.SOLVE_PRODUCED)
    for recipe in registry.recipes.values():
        for flow in recipe.outputs:
            assert flow.item_key not in synthetic.SOLVE_RAW_ITEMS, recipe.key


def test_the_corpus_declares_its_recipes_in_the_published_order(registry: Registry) -> None:
    # Registry order is document order, and C5 turns on it. A downstream slice
    # reading SOLVE_RECIPES must get the same sequence the registry iterates.
    assert list(registry.recipes) == list(synthetic.SOLVE_RECIPES)


def test_every_class_name_in_the_corpus_is_synthetic(registry: Registry) -> None:
    # BOOTSTRAP.md section 8.1: fixtures are hand-authored synthetic material,
    # never a slice of real game data. The Desc_Solve / Build_Solve prefixes
    # also keep this corpus visibly distinct from tests/data/synthetic.py's.
    for key in (*registry.items, *registry.buildings):
        assert key.startswith(("Desc_Solve", "Build_Solve")), key
    for key in registry.recipes:
        assert key.startswith(("R_", "Alt_", "Std_")), key


# ---------------------------------------------------------------------------
# Unit normalization happened EXACTLY once
# ---------------------------------------------------------------------------


def test_the_fluid_amount_is_normalized_exactly_once(registry: Registry) -> None:
    (product,) = registry.recipes[synthetic.FLUID_RECIPE].outputs
    assert product.item_key == synthetic.SOLVE_FLUID_ITEM
    _assert_exact(product.amount)
    # Normalized once.
    assert product.amount == synthetic.C2_FLUID_PER_CYCLE_M3
    # NOT zero times: the litre figure would be a thousand times too large.
    assert product.amount != Fraction(synthetic.C2_FLUID_LITRES_PER_CYCLE)
    # NOT twice: dividing the already-normalized value again is the trap C2
    # exists for, and it is a plausible-looking number rather than a crash.
    assert product.amount != synthetic.C2_FLUID_PER_CYCLE_M3 / synthetic.LITRES_PER_CUBIC_METRE


def test_the_fluid_item_is_a_fluid_and_the_solids_are_not(registry: Registry) -> None:
    # The conversion is driven by the ITEM's form, not by the recipe, so the
    # forms are what make the amounts above mean anything.
    assert registry.items[synthetic.SOLVE_FLUID_ITEM].is_fluid
    assert registry.items[synthetic.SOLVE_RESIDUE_ITEM].is_fluid
    assert not registry.items[synthetic.SOLVE_ORE_ITEM].is_fluid
    assert not registry.items[synthetic.SOLVE_PLATE_ITEM].is_fluid


def test_every_normalized_amount_is_an_exact_fraction(registry: Registry) -> None:
    for recipe in registry.recipes.values():
        _assert_exact(recipe.duration)
        for flow in (*recipe.inputs, *recipe.outputs):
            _assert_exact(flow.amount)


# ---------------------------------------------------------------------------
# C1 - linear two stage
# ---------------------------------------------------------------------------


def test_c1_per_machine_rates_follow_from_the_registry(registry: Registry) -> None:
    plate = _net_per_minute(registry.recipes[synthetic.PLATE_RECIPE])
    rod = _net_per_minute(registry.recipes[synthetic.ROD_RECIPE])
    assert plate[synthetic.SOLVE_PLATE_ITEM] == synthetic.C1_PLATE_PER_MACHINE
    assert rod[synthetic.SOLVE_ROD_ITEM] == synthetic.C1_ROD_PER_MACHINE
    assert rod[synthetic.SOLVE_PLATE_ITEM] == -synthetic.C1_PLATE_DEMAND_PER_MACHINE
    _assert_exact(plate[synthetic.SOLVE_PLATE_ITEM])


def test_c1_solution_balances_and_matches_the_published_power(registry: Registry) -> None:
    plan = _combined(
        (synthetic.C1_ROD_MACHINES, _net_per_minute(registry.recipes[synthetic.ROD_RECIPE])),
        (synthetic.C1_PLATE_MACHINES, _net_per_minute(registry.recipes[synthetic.PLATE_RECIPE])),
    )
    assert plan[synthetic.SOLVE_ROD_ITEM] == synthetic.C1_ROD_TARGET
    assert plan[synthetic.SOLVE_PLATE_ITEM] == 0
    assert -plan[synthetic.SOLVE_ORE_ITEM] == synthetic.C1_ORE_DEMAND
    power = _power(
        registry,
        (synthetic.C1_ROD_MACHINES, synthetic.SOLVE_SMELTER_BUILDING),
        (synthetic.C1_PLATE_MACHINES, synthetic.SOLVE_SMELTER_BUILDING),
    )
    assert power == synthetic.C1_POWER_MW
    _assert_exact(power)


def test_c1_machine_count_is_the_one_floats_cannot_represent() -> None:
    # 10/3 is why the whole solve path is Fraction. The float is not merely
    # imprecise, it is a different number, and it renders as a plausible one.
    assert repr(float(synthetic.C1_ROD_MACHINES)) == synthetic.C1_ROD_MACHINES_FLOAT_REPR
    assert Fraction(float(synthetic.C1_ROD_MACHINES)) != synthetic.C1_ROD_MACHINES


# ---------------------------------------------------------------------------
# C2 - fluid, the do-not-divide-twice trap
# ---------------------------------------------------------------------------


def test_c2_solution_balances_and_matches_the_published_power(registry: Registry) -> None:
    rates = _net_per_minute(registry.recipes[synthetic.FLUID_RECIPE])
    assert rates[synthetic.SOLVE_FLUID_ITEM] == synthetic.C2_FLUID_PER_MACHINE
    plan = _combined((synthetic.C2_REFINERY_MACHINES, rates))
    assert plan[synthetic.SOLVE_FLUID_ITEM] == synthetic.C2_FLUID_TARGET
    assert -plan[synthetic.SOLVE_ORE_ITEM] == synthetic.C2_ORE_DEMAND
    power = _power(registry, (synthetic.C2_REFINERY_MACHINES, synthetic.SOLVE_REFINERY_BUILDING))
    assert power == synthetic.C2_POWER_MW
    _assert_exact(power)


def test_c2_both_wrong_unit_answers_are_far_from_the_right_one() -> None:
    # Both wrong answers are finite, positive and render without complaint. The
    # only thing that distinguishes them is the magnitude, which is why the
    # corpus pins all three rather than only the right one.
    assert synthetic.C2_DIVIDED_TWICE_MACHINES != synthetic.C2_REFINERY_MACHINES
    assert synthetic.C2_READ_AS_LITRES_MACHINES != synthetic.C2_REFINERY_MACHINES
    assert synthetic.C2_DIVIDED_TWICE_MACHINES == synthetic.C2_REFINERY_MACHINES * 1000
    assert synthetic.C2_READ_AS_LITRES_MACHINES == synthetic.C2_REFINERY_MACHINES / 1000


# ---------------------------------------------------------------------------
# C3 - the byproduct loop, the load-bearing case
# ---------------------------------------------------------------------------


def test_c3_coefficients_follow_from_the_registry(registry: Registry) -> None:
    gadget = _net_per_minute(registry.recipes[synthetic.GADGET_RECIPE])
    recover = _net_per_minute(registry.recipes[synthetic.RECOVER_RECIPE])
    fluid = _net_per_minute(registry.recipes[synthetic.FLUID_RECIPE])
    plate = _net_per_minute(registry.recipes[synthetic.PLATE_RECIPE])
    assert gadget[synthetic.SOLVE_GADGET_ITEM] == synthetic.C3_GADGET_YIELD
    assert gadget[synthetic.SOLVE_PLATE_ITEM] == synthetic.C3_GADGET_PLATE_DRAW
    assert gadget[synthetic.SOLVE_FLUID_ITEM] == synthetic.C3_GADGET_FLUID_DRAW
    assert gadget[synthetic.SOLVE_RESIDUE_ITEM] == synthetic.C3_GADGET_RESIDUE_YIELD
    assert recover[synthetic.SOLVE_RESIDUE_ITEM] == synthetic.C3_RECOVER_RESIDUE_DRAW
    assert recover[synthetic.SOLVE_FLUID_ITEM] == synthetic.C3_RECOVER_FLUID_YIELD
    assert fluid[synthetic.SOLVE_FLUID_ITEM] == synthetic.C3_FLUID_YIELD
    assert fluid[synthetic.SOLVE_ORE_ITEM] == synthetic.C3_FLUID_ORE_DRAW
    assert plate[synthetic.SOLVE_PLATE_ITEM] == synthetic.C3_PLATE_YIELD
    assert plate[synthetic.SOLVE_ORE_ITEM] == synthetic.C3_PLATE_ORE_DRAW


def test_c3_the_cycle_is_real_and_not_a_topological_order(registry: Registry) -> None:
    # Gadget needs Fluid, Fluid comes back from Residue, Residue comes from
    # Gadget. If this ever becomes a DAG the fixture has stopped testing the
    # thing it exists for, and naive recursion would start terminating.
    gadget = _net_per_minute(registry.recipes[synthetic.GADGET_RECIPE])
    recover = _net_per_minute(registry.recipes[synthetic.RECOVER_RECIPE])
    assert gadget[synthetic.SOLVE_FLUID_ITEM] < 0
    assert gadget[synthetic.SOLVE_RESIDUE_ITEM] > 0
    assert recover[synthetic.SOLVE_RESIDUE_ITEM] < 0
    assert recover[synthetic.SOLVE_FLUID_ITEM] > 0


def test_c3_solution_balances_and_matches_the_published_power(registry: Registry) -> None:
    plan = _combined(
        (synthetic.C3_GADGET_MACHINES, _net_per_minute(registry.recipes[synthetic.GADGET_RECIPE])),
        (
            synthetic.C3_RECOVER_MACHINES,
            _net_per_minute(registry.recipes[synthetic.RECOVER_RECIPE]),
        ),
        (synthetic.C3_FLUID_MACHINES, _net_per_minute(registry.recipes[synthetic.FLUID_RECIPE])),
        (synthetic.C3_PLATE_MACHINES, _net_per_minute(registry.recipes[synthetic.PLATE_RECIPE])),
    )
    assert plan[synthetic.SOLVE_GADGET_ITEM] == synthetic.C3_GADGET_TARGET
    for intermediate in (
        synthetic.SOLVE_PLATE_ITEM,
        synthetic.SOLVE_FLUID_ITEM,
        synthetic.SOLVE_RESIDUE_ITEM,
    ):
        assert plan[intermediate] == 0, intermediate
    assert -plan[synthetic.SOLVE_ORE_ITEM] == synthetic.C3_ORE_DEMAND
    power = _power(
        registry,
        (synthetic.C3_GADGET_MACHINES, synthetic.SOLVE_REFINERY_BUILDING),
        (synthetic.C3_RECOVER_MACHINES, synthetic.SOLVE_REFINERY_BUILDING),
        (synthetic.C3_FLUID_MACHINES, synthetic.SOLVE_REFINERY_BUILDING),
        (synthetic.C3_PLATE_MACHINES, synthetic.SOLVE_SMELTER_BUILDING),
    )
    assert power == synthetic.C3_POWER_MW
    _assert_exact(power)
    assert repr(float(power)) == synthetic.C3_POWER_FLOAT_REPR


def test_c3_gadget_has_exactly_one_producing_recipe(registry: Registry) -> None:
    # THE precondition for C3 and C4 having a unique answer at all. A second
    # Gadget producer makes the published machine counts one solution among
    # infinitely many - and a cheaper rival exists, so a minimizing solver
    # would return a different plan and this fixture would be teaching every
    # suite above it the wrong number.
    producers = [
        key
        for key, recipe in registry.recipes.items()
        if any(flow.item_key == synthetic.SOLVE_GADGET_ITEM for flow in recipe.outputs)
    ]
    assert producers == [synthetic.GADGET_RECIPE]


# ---------------------------------------------------------------------------
# C4 - the loop, reverse direction
# ---------------------------------------------------------------------------


def test_c4_is_c3_scaled_by_the_raw_input_cap() -> None:
    assert synthetic.C4_SCALE == synthetic.C4_ORE_CAP / synthetic.C3_ORE_DEMAND
    assert synthetic.C4_GADGET_RATE == synthetic.C3_GADGET_TARGET * synthetic.C4_SCALE
    assert synthetic.C4_GADGET_MACHINES == synthetic.C3_GADGET_MACHINES * synthetic.C4_SCALE
    assert synthetic.C4_RECOVER_MACHINES == synthetic.C3_RECOVER_MACHINES * synthetic.C4_SCALE
    assert synthetic.C4_FLUID_MACHINES == synthetic.C3_FLUID_MACHINES * synthetic.C4_SCALE
    assert synthetic.C4_PLATE_MACHINES == synthetic.C3_PLATE_MACHINES * synthetic.C4_SCALE


def test_c4_solution_balances_against_the_ore_cap(registry: Registry) -> None:
    plan = _combined(
        (synthetic.C4_GADGET_MACHINES, _net_per_minute(registry.recipes[synthetic.GADGET_RECIPE])),
        (
            synthetic.C4_RECOVER_MACHINES,
            _net_per_minute(registry.recipes[synthetic.RECOVER_RECIPE]),
        ),
        (synthetic.C4_FLUID_MACHINES, _net_per_minute(registry.recipes[synthetic.FLUID_RECIPE])),
        (synthetic.C4_PLATE_MACHINES, _net_per_minute(registry.recipes[synthetic.PLATE_RECIPE])),
    )
    assert plan[synthetic.SOLVE_GADGET_ITEM] == synthetic.C4_GADGET_RATE
    for intermediate in (
        synthetic.SOLVE_PLATE_ITEM,
        synthetic.SOLVE_FLUID_ITEM,
        synthetic.SOLVE_RESIDUE_ITEM,
    ):
        assert plan[intermediate] == 0, intermediate
    assert -plan[synthetic.SOLVE_ORE_ITEM] == synthetic.C4_ORE_CAP


def test_c4_power_cross_checks_c3_exactly(registry: Registry) -> None:
    # An INDEPENDENT confirmation of C3: the two chains were derived from
    # different directions, so 436/3 * 3/4 landing exactly on 109 is evidence
    # about C3 and not merely about C4.
    power = _power(
        registry,
        (synthetic.C4_GADGET_MACHINES, synthetic.SOLVE_REFINERY_BUILDING),
        (synthetic.C4_RECOVER_MACHINES, synthetic.SOLVE_REFINERY_BUILDING),
        (synthetic.C4_FLUID_MACHINES, synthetic.SOLVE_REFINERY_BUILDING),
        (synthetic.C4_PLATE_MACHINES, synthetic.SOLVE_SMELTER_BUILDING),
    )
    assert power == synthetic.C4_POWER_MW
    assert synthetic.C3_POWER_MW * synthetic.C4_SCALE == synthetic.C4_POWER_MW
    _assert_exact(power)


# ---------------------------------------------------------------------------
# C5 - the degenerate optimizer case
# ---------------------------------------------------------------------------


def test_c5_alt_gadget_is_first_in_registry_order(registry: Registry) -> None:
    # A registry-order stub picks the first candidate. It must pick the WRONG
    # one, or the stub passes and the feasibility check is never written.
    assert next(iter(registry.recipes)) == synthetic.ALT_GADGET_RECIPE
    keys = list(registry.recipes)
    assert keys.index(synthetic.ALT_GADGET_RECIPE) < keys.index(synthetic.STD_GADGET_RECIPE)


def test_c5_rare_has_a_descriptor_but_no_producer_and_is_not_raw(registry: Registry) -> None:
    # It must be a KNOWN item - otherwise the amount referencing it is flagged
    # unknown and left unconverted, and the corpus stops building clean. What
    # makes Alt_Gadget infeasible is the absence of a ROUTE, not of a
    # descriptor.
    assert synthetic.SOLVE_RARE_ITEM in registry.items
    assert synthetic.SOLVE_RARE_ITEM not in synthetic.SOLVE_RAW_ITEMS
    for recipe in registry.recipes.values():
        for flow in recipe.outputs:
            assert flow.item_key != synthetic.SOLVE_RARE_ITEM, recipe.key


def test_c5_alt_gadget_beats_std_gadget_on_every_objective(registry: Registry) -> None:
    # A score-before-feasibility greedy must also pick the wrong one. If Alt
    # ever loses on an objective, that greedy passes for the wrong reason.
    assert synthetic.C5_ALT_MACHINES_IF_FEASIBLE < synthetic.C5_STD_MACHINES
    assert synthetic.C5_ALT_ORE_IF_FEASIBLE < synthetic.C5_ORE_DEMAND
    assert synthetic.C5_ALT_POWER_MW_IF_FEASIBLE < synthetic.C5_POWER_MW
    alt = _net_per_minute(registry.recipes[synthetic.ALT_GADGET_RECIPE])
    std = _net_per_minute(registry.recipes[synthetic.STD_GADGET_RECIPE])
    assert alt[synthetic.SOLVE_TRINKET_ITEM] == synthetic.C5_ALT_PER_MACHINE
    assert std[synthetic.SOLVE_TRINKET_ITEM] == synthetic.C5_STD_PER_MACHINE
    assert alt[synthetic.SOLVE_TRINKET_ITEM] > std[synthetic.SOLVE_TRINKET_ITEM]
    assert alt[synthetic.SOLVE_RARE_ITEM] == synthetic.C5_ALT_RARE_DRAW


def test_c5_feasible_set_is_the_std_gadget_singleton(registry: Registry) -> None:
    producers = [
        key
        for key, recipe in registry.recipes.items()
        if any(flow.item_key == synthetic.SOLVE_TRINKET_ITEM for flow in recipe.outputs)
    ]
    assert producers == [synthetic.ALT_GADGET_RECIPE, synthetic.STD_GADGET_RECIPE]
    feasible = [
        key
        for key in producers
        if all(
            flow.item_key in synthetic.SOLVE_RAW_ITEMS or flow.item_key in synthetic.SOLVE_PRODUCED
            for flow in registry.recipes[key].inputs
        )
    ]
    assert feasible == [synthetic.STD_GADGET_RECIPE]


def test_c5_solution_matches_the_published_values(registry: Registry) -> None:
    plan = _combined(
        (synthetic.C5_STD_MACHINES, _net_per_minute(registry.recipes[synthetic.STD_GADGET_RECIPE]))
    )
    assert plan[synthetic.SOLVE_TRINKET_ITEM] == synthetic.C5_TRINKET_TARGET
    assert -plan[synthetic.SOLVE_ORE_ITEM] == synthetic.C5_ORE_DEMAND
    power = _power(registry, (synthetic.C5_STD_MACHINES, synthetic.SOLVE_ASSEMBLER_BUILDING))
    assert power == synthetic.C5_POWER_MW
    _assert_exact(power)


def test_c5_shares_no_product_with_the_c3_loop(registry: Registry) -> None:
    # The one place this corpus departs from its brief, and the reason is
    # arithmetic rather than taste: sharing a product would give the C3 loop a
    # second producer, a cheaper rival plan, and no unique answer.
    #
    # Read off the REGISTRY rather than compared as two named constants. The
    # constant form was statically provable - mypy folded it to a
    # non-overlapping-equality error - which means it could never have failed
    # at runtime. This form also covers the byproduct: Residue colliding would
    # break C3 just as surely as Gadget colliding.
    c5_products = {
        flow.item_key
        for key in (synthetic.ALT_GADGET_RECIPE, synthetic.STD_GADGET_RECIPE)
        for flow in registry.recipes[key].outputs
    }
    c3_products = {flow.item_key for flow in registry.recipes[synthetic.GADGET_RECIPE].outputs}
    assert not (c5_products & c3_products)


# ---------------------------------------------------------------------------
# C6, C7, C8 - the shapes a solver must refuse rather than answer
# ---------------------------------------------------------------------------


def test_c6_duration_is_exactly_zero_and_the_registry_kept_it(registry: Registry) -> None:
    # A MEASURED zero, not a defaulted one: the registry skips a recipe whose
    # duration key is absent and keeps one that declares zero, so this really
    # is an input the solve path receives rather than a defensive branch.
    recipe = registry.recipes[synthetic.ZERO_DURATION_RECIPE]
    assert recipe.duration == synthetic.ZERO_DURATION
    _assert_exact(recipe.duration)
    assert recipe.produced_in == ()
    with pytest.raises(ZeroDivisionError):
        _net_per_minute(recipe)


def test_c6_is_the_only_zero_duration_recipe(registry: Registry) -> None:
    zeroes = [key for key, recipe in registry.recipes.items() if recipe.duration == 0]
    assert zeroes == [synthetic.ZERO_DURATION_RECIPE]


def test_c7_relic_is_reachable_only_through_an_unproducible_item(registry: Registry) -> None:
    producers = [
        key
        for key, recipe in registry.recipes.items()
        if any(flow.item_key == synthetic.SOLVE_RELIC_ITEM for flow in recipe.outputs)
    ]
    assert producers == [synthetic.ORPHAN_RECIPE]
    inputs = [flow.item_key for flow in registry.recipes[synthetic.ORPHAN_RECIPE].inputs]
    assert inputs == [synthetic.SOLVE_ORPHAN_ITEM]
    assert synthetic.SOLVE_ORPHAN_ITEM in registry.items
    assert synthetic.SOLVE_ORPHAN_ITEM not in synthetic.SOLVE_RAW_ITEMS
    assert synthetic.SOLVE_ORPHAN_ITEM not in synthetic.SOLVE_PRODUCED


def test_c8_the_twins_are_indistinguishable(registry: Registry) -> None:
    first = _net_per_minute(registry.recipes[synthetic.TWIN_A_RECIPE])
    second = _net_per_minute(registry.recipes[synthetic.TWIN_B_RECIPE])
    assert first == second
    assert first[synthetic.SOLVE_TWIN_ITEM] == synthetic.C8_TWIN_PER_MACHINE
    # Same building too, so there is no power tie-break either.
    assert (
        registry.recipes[synthetic.TWIN_A_RECIPE].produced_in
        == registry.recipes[synthetic.TWIN_B_RECIPE].produced_in
    )


# ---------------------------------------------------------------------------
# C9 - the negative solution, built as a VARIANT so the main corpus stays clean
# ---------------------------------------------------------------------------


def test_c9_is_absent_from_the_main_corpus(registry: Registry) -> None:
    assert synthetic.RICH_RECOVER_RECIPE not in registry.recipes


def test_c9_variant_builds_clean_and_swaps_only_the_recovery_recipe() -> None:
    variant = synthetic.rich_recovery_registry()
    assert variant.warnings == ()
    assert synthetic.RECOVER_RECIPE not in variant.recipes
    assert synthetic.RICH_RECOVER_RECIPE in variant.recipes


def test_c9_rich_recovery_drives_the_fluid_recipe_negative() -> None:
    variant = synthetic.rich_recovery_registry()
    rich = _net_per_minute(variant.recipes[synthetic.RICH_RECOVER_RECIPE])
    assert rich[synthetic.SOLVE_FLUID_ITEM] == synthetic.C9_RICH_FLUID_YIELD
    assert rich[synthetic.SOLVE_RESIDUE_ITEM] == synthetic.C3_RECOVER_RESIDUE_DRAW
    gadget = _net_per_minute(variant.recipes[synthetic.GADGET_RECIPE])
    fluid = _net_per_minute(variant.recipes[synthetic.FLUID_RECIPE])
    # The Fluid balance, solved with a and b unchanged from C3.
    machines = (
        -(
            synthetic.C3_GADGET_MACHINES * gadget[synthetic.SOLVE_FLUID_ITEM]
            + synthetic.C3_RECOVER_MACHINES * rich[synthetic.SOLVE_FLUID_ITEM]
        )
        / fluid[synthetic.SOLVE_FLUID_ITEM]
    )
    assert machines == synthetic.C9_FLUID_MACHINES
    assert machines < 0
    _assert_exact(machines)


# ---------------------------------------------------------------------------
# The variant builder itself
# ---------------------------------------------------------------------------


def test_registry_with_no_arguments_reproduces_the_main_corpus(registry: Registry) -> None:
    assert list(synthetic.registry_with().recipes) == list(registry.recipes)


def test_registry_with_drop_removes_only_the_named_recipe(registry: Registry) -> None:
    variant = synthetic.registry_with(drop=frozenset({synthetic.ROD_RECIPE}))
    assert synthetic.ROD_RECIPE not in variant.recipes
    assert set(variant.recipes) == set(registry.recipes) - {synthetic.ROD_RECIPE}


# ---------------------------------------------------------------------------
# Exactness, corpus wide
# ---------------------------------------------------------------------------


def test_no_published_expected_value_is_a_float() -> None:
    # Non-negotiable 6. float('1.321929') succeeds and is a different number,
    # so a stray float in the corpus would not announce itself.
    for name in dir(synthetic):
        if name.startswith("_"):
            continue
        value = getattr(synthetic, name)
        assert not isinstance(value, float), name


def test_the_building_power_figures_are_the_published_constants(registry: Registry) -> None:
    assert registry.buildings[synthetic.SOLVE_SMELTER_BUILDING].power_consumption == (
        synthetic.SMELTER_POWER_MW
    )
    assert registry.buildings[synthetic.SOLVE_ASSEMBLER_BUILDING].power_consumption == (
        synthetic.ASSEMBLER_POWER_MW
    )
    assert registry.buildings[synthetic.SOLVE_REFINERY_BUILDING].power_consumption == (
        synthetic.REFINERY_POWER_MW
    )


def test_every_building_carries_the_clock_exponent(registry: Registry) -> None:
    # Absence means NOT clock-scalable and is never defaulted, so the power and
    # clock slice needs every building here to carry one.
    for building in synthetic.SOLVE_BUILDINGS:
        exponent = registry.buildings[building].power_exponent
        assert exponent == synthetic.POWER_EXPONENT
        _assert_exact(exponent)
