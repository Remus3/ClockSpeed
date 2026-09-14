"""CS-105: the power and clock model, and the fences that keep it honest.

Three groups of test live here and they fail for three different reasons, which
is why none of them is a substitute for another.

- **The CS-105 fences.** The acceptance criterion is that a test fails if a
  literal exponent appears anywhere in the power path. A source scan alone
  cannot deliver that: ``Fraction(1321929, 1000000)`` puts no exponent-valued
  constant in the file at all, and a float-literal ban does not see it either.
  So the scan is paired with a MUTATION test that builds two corpora differing
  in one building's exponent and asserts the results differ. The scan catches
  the careless spelling; the mutation catches every spelling, and it does not
  go stale when a balance patch moves the number.

- **The four measured power shapes.** Each is read out of the hand-authored
  corpus rather than asserted against a hand-built Building, so a shape the
  registry stops producing turns into a failure here instead of a fixture that
  agrees with the defect.

- **The ceiling fence.** ADR 0005 and ADR 0006. No number, no derivation, and
  no test in this file writes a candidate ceiling down - the fences are
  structural and data-driven precisely so that asserting them does not require
  restating the number they exist to keep out.

Every candidate exponent this file scans for is taken FROM DATA - the version
pin's census and the two corpora - and never restated as a literal here. A test
that spelled the exponent out would be the thing it forbids.
"""

from __future__ import annotations

import ast
import dataclasses
from fractions import Fraction
from pathlib import Path
from types import ModuleType

import pytest

from clockspeed.data.registry import Building, Recipe, Registry, build_registry
from clockspeed.data.version import OVERCLOCK_POTENTIAL_SHARD_SLOTS, pin
from clockspeed.solve import power
from clockspeed.solve.exact import DeferredPowerTerm, InexactValueError, audit_exact
from tests.data import synthetic as data_corpus
from tests.solve import synthetic as solve_corpus

# ---------------------------------------------------------------------------
# Fixtures and helpers
# ---------------------------------------------------------------------------

#: An overclock and an underclock, both away from the reference clock. Their
#: exact values do not matter to any assertion below - what matters is only
#: that they are not the reference clock, where the answer is exact.
OVERCLOCK = Fraction(3, 2)
UNDERCLOCK = Fraction(1, 2)


@pytest.fixture(scope="module")
def data_registry() -> Registry:
    return build_registry(data_corpus.synthetic_document())


@pytest.fixture(scope="module")
def solve_reg() -> Registry:
    return solve_corpus.solve_registry()


def registry_with_entry_key(class_name: str, key: str, value: str | None) -> Registry:
    # Deliberately a local copy of the helper in tests/data/test_registry.py
    # rather than an import of it. Importing one test module into another makes
    # a collection-order dependency out of twelve lines of corpus patching, and
    # the seam being exercised - docs_json into document_from into
    # build_registry - is the published one either way.
    groups = data_corpus.docs_json()
    patched = 0
    for group in groups:
        classes = group.get(data_corpus.KEY_CLASSES)
        if not isinstance(classes, list):
            continue
        for entry in classes:
            if entry.get(data_corpus.KEY_CLASS_NAME) != class_name:
                continue
            patched += 1
            if value is None:
                entry.pop(key, None)
            else:
                entry[key] = value
    assert patched == 1, f"{class_name} appears {patched} times in the corpus, not once"
    return build_registry(data_corpus.document_from(groups))


def module_source_path(module: ModuleType) -> Path:
    path = module.__file__
    assert path is not None, "the module under test has no file on disk"
    return Path(path)


def module_tree(module: ModuleType) -> ast.Module:
    return ast.parse(module_source_path(module).read_text(encoding="ascii"))


def constant_values(module: ModuleType) -> list[object]:
    return [node.value for node in ast.walk(module_tree(module)) if isinstance(node, ast.Constant)]


def imported_modules(module: ModuleType) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(module_tree(module)):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            names.add(node.module)
    return names


def candidate_exponents(*registries: Registry) -> set[Fraction]:
    # FROM DATA, never restated. The census records the value SET a balance
    # patch moves, and the corpora carry whatever their entries declare, so a
    # patch that introduces a third exponent widens this scan on its own.
    values: set[Fraction] = set()
    for text in pin()["census"]["power_consumption_exponents"]:
        values.add(Fraction(text))
    for registry in registries:
        for building in registry.buildings.values():
            if building.power_exponent is not None:
                values.add(building.power_exponent)
    return values


def constant_matches(value: object, candidate: Fraction) -> bool:
    # Matched through the DECIMAL SPELLING rather than through float equality,
    # so a float literal of 1.6 and a string of "1.600000" are both caught while
    # nothing here has to construct a float to compare against.
    if isinstance(value, bool):
        return False
    if not isinstance(value, int | float | str):
        return False
    try:
        return Fraction(str(value)) == candidate
    except (ValueError, ZeroDivisionError):
        return False


def clocked(building: Building, clock: Fraction) -> power.ClockedDraw:
    return power.draw_at_clock(building, clock)


# ---------------------------------------------------------------------------
# CS-105 - no literal exponent anywhere in the power path
# ---------------------------------------------------------------------------


def test_the_exponent_candidate_set_is_not_empty(
    data_registry: Registry, solve_reg: Registry
) -> None:
    # A scan over an empty candidate set passes vacuously and proves nothing,
    # so the set itself is asserted before anything is scanned against it.
    candidates = candidate_exponents(data_registry, solve_reg)
    assert len(candidates) > 1, (
        "the corpora and the pin must supply at least two distinct exponents, or the "
        f"mutation test below cannot tell a read from a constant; got {sorted(candidates)}"
    )


def test_no_literal_exponent_value_appears_in_the_power_module(
    data_registry: Registry, solve_reg: Registry
) -> None:
    candidates = candidate_exponents(data_registry, solve_reg)
    constants = constant_values(power)
    offenders = [
        (value, candidate)
        for candidate in candidates
        for value in constants
        if constant_matches(value, candidate)
    ]
    assert offenders == [], (
        f"{module_source_path(power).name} carries a literal exponent value: {offenders}. "
        "The exponent is per building CLASS and two distinct values are measured, so a "
        "constant is wrong for whichever entries carry the other one."
    )


def test_no_literal_exponent_appears_as_a_numerator_denominator_pair(
    data_registry: Registry, solve_reg: Registry
) -> None:
    # The spelling a float-literal ban does not see. Fraction(1321929, 1000000)
    # puts no exponent-valued constant in the file, so the test above is blind
    # to it and only the pair is evidence.
    candidates = candidate_exponents(data_registry, solve_reg)
    integers = {value for value in constant_values(power) if isinstance(value, int)}
    offenders = [
        candidate
        for candidate in candidates
        if candidate.denominator != 1
        and candidate.numerator in integers
        and candidate.denominator in integers
    ]
    assert offenders == [], (
        f"{module_source_path(power).name} spells an exponent as an integer pair: {offenders}"
    )


def test_the_exponent_is_read_from_data_and_never_folded_into_the_module() -> None:
    # THE DURABLE FENCE. Two corpora identical but for one building's exponent.
    # Any hardcoded exponent - as a float, as a decimal string, or as an integer
    # pair - produces byte-identical results over both and fails here, and this
    # assertion does not go stale when a balance patch moves the number.
    shipped = registry_with_entry_key(
        data_corpus.BLENDER_BUILDING,
        data_corpus.KEY_POWER_EXPONENT,
        solve_corpus.POWER_EXPONENT_TEXT,
    )
    other = registry_with_entry_key(
        data_corpus.BLENDER_BUILDING,
        data_corpus.KEY_POWER_EXPONENT,
        data_corpus.SECOND_EXPONENT,
    )
    shipped_building = shipped.buildings[data_corpus.BLENDER_BUILDING]
    other_building = other.buildings[data_corpus.BLENDER_BUILDING]
    assert shipped_building.power_exponent != other_building.power_exponent

    shipped_draw = clocked(shipped_building, OVERCLOCK)
    other_draw = clocked(other_building, OVERCLOCK)
    assert shipped_draw != other_draw, (
        "the same entry point returned identical results for two buildings whose exponents "
        "differ, which is exactly what a hardcoded exponent does under every spelling"
    )
    assert shipped_draw.deferred is not None
    assert other_draw.deferred is not None
    assert shipped_draw.deferred.exponent == shipped_building.power_exponent
    assert other_draw.deferred.exponent == other_building.power_exponent
    assert type(shipped_draw.deferred.exponent) is Fraction


def test_a_building_with_no_exponent_is_reported_not_scalable_and_never_scaled(
    data_registry: Registry,
) -> None:
    # No literal scan can catch this one. An absent exponent means NOT
    # clock-scalable and is never defaulted, so the answer is a named outcome
    # rather than a number computed from an invented exponent.
    building = data_registry.buildings[data_corpus.FLOODLIGHT_BUILDING]
    assert building.power_exponent is None
    assert building.power_consumption == Fraction(10)

    result = clocked(building, OVERCLOCK)
    assert result.outcome == power.OUTCOME_NOT_SCALABLE
    assert result.megawatts is None
    assert result.coefficient is None
    assert result.deferred is None
    assert "not clock-scalable" in result.reason


def test_an_absent_exponent_is_not_borrowed_from_another_building(
    data_registry: Registry,
) -> None:
    # The sibling case: a corpus where OTHER buildings do carry an exponent is
    # exactly where a defaulting implementation looks correct, because some
    # exponent is always in scope.
    scalable = data_registry.buildings[data_corpus.BLENDER_BUILDING]
    assert scalable.power_exponent is not None
    unscalable = data_registry.buildings[data_corpus.FLOODLIGHT_BUILDING]
    assert clocked(unscalable, OVERCLOCK).outcome == power.OUTCOME_NOT_SCALABLE
    assert clocked(scalable, OVERCLOCK).outcome == power.OUTCOME_DEFERRED


# ---------------------------------------------------------------------------
# The four measured power shapes
# ---------------------------------------------------------------------------


def test_shape_one_an_ordinary_scalar_draw_is_modeled_exactly(data_registry: Registry) -> None:
    building = data_registry.buildings[data_corpus.SYNTHESIZER_BUILDING]
    draw = power.declared_draw(building)
    assert draw.shape == power.SHAPE_FIXED
    assert draw.modeled is True
    assert draw.megawatts == Fraction(4)
    assert type(draw.megawatts) is Fraction
    assert draw.megawatts == building.power_consumption


def test_shape_two_a_struct_range_is_unmodeled_and_the_range_is_not_collapsed(
    data_registry: Registry,
) -> None:
    # One measured entry declares a (Min=...,Max=...) struct and the registry
    # leaves power_consumption None. Collapsing the two bounds into a midpoint
    # or into the maximum would publish a scalar the document never stated.
    building = data_registry.buildings[data_corpus.RAILCAR_ITEM]
    assert building.power_consumption is None
    draw = power.declared_draw(building)
    assert draw.shape == power.SHAPE_RANGE_ONLY
    assert draw.modeled is False
    assert draw.megawatts is None
    assert draw.minimum == Fraction(25)
    assert draw.maximum == Fraction(110)
    assert "unmodeled" in draw.reason


def test_shape_three_variable_power_is_unmodeled_and_the_declared_zero_is_not_the_draw(
    data_registry: Registry,
) -> None:
    # power_consumption is a REAL declared zero here, not an absent key, and the
    # true draw is the range plus a per-recipe constant and factor whose
    # semantics this project has never measured.
    building = data_registry.buildings[data_corpus.ACCELERATOR_BUILDING]
    assert building.power_consumption == Fraction(0)
    assert building.is_variable_power is True
    draw = power.declared_draw(building)
    assert draw.shape == power.SHAPE_VARIABLE
    assert draw.modeled is False
    assert draw.megawatts is None, "the declared zero must never be published as the draw"
    assert draw.minimum == Fraction(250)
    assert draw.maximum == Fraction(1500)


def test_shape_three_carries_the_recipe_operands_without_inventing_a_formula(
    data_registry: Registry,
) -> None:
    building = data_registry.buildings[data_corpus.ACCELERATOR_BUILDING]
    recipe = data_registry.recipes[data_corpus.ACCELERATED_RECIPE]
    inputs = power.variable_power_inputs(building, recipe)
    assert inputs.modeled is False
    assert inputs.constant == recipe.variable_power_constant
    assert inputs.factor == recipe.variable_power_factor
    assert inputs.minimum == building.estimated_min_power
    assert inputs.maximum == building.estimated_max_power
    # This function still applies no law - that is bounded_draw - so its reason
    # has to say which function does, or a caller reads "no law here" as "no
    # law anywhere" and re-invents one.
    assert "no law is applied here" in inputs.reason
    assert "bounded_draw" in inputs.reason


def test_shape_four_a_declared_maximum_of_zero_is_a_fixed_draw_building(
    data_registry: Registry,
) -> None:
    # Presence of the estimated-maximum key is NOT the variable-power test. This
    # entry declares a maximum of a real zero, so it draws a fixed 100 MW, and
    # an implementation keyed on key presence reports it unmodeled instead.
    building = data_registry.buildings[data_corpus.GENERATOR_BUILDING]
    assert building.estimated_max_power == Fraction(0)
    assert building.is_variable_power is False
    draw = power.declared_draw(building)
    assert draw.shape == power.SHAPE_FIXED
    assert draw.modeled is True
    assert draw.megawatts == Fraction(100)


def test_an_unreadable_draw_is_undeclared_and_is_never_published_as_zero(
    data_registry: Registry,
) -> None:
    # None is NOT zero. A confident zero is exactly what a power plan cannot
    # detect, which is why the absent case gets its own shape.
    building = data_registry.buildings[data_corpus.CHARGER_BUILDING]
    assert building.power_consumption is None
    draw = power.declared_draw(building)
    assert draw.shape == power.SHAPE_UNDECLARED
    assert draw.modeled is False
    assert draw.megawatts is None


def test_every_shape_is_reachable_from_the_corpus(data_registry: Registry) -> None:
    # The four shapes are a claim about the model's coverage, so the claim is
    # checked against what the corpus actually produces rather than asserted one
    # building at a time.
    shapes = {power.declared_draw(building).shape for building in data_registry.buildings.values()}
    assert shapes == {
        power.SHAPE_FIXED,
        power.SHAPE_RANGE_ONLY,
        power.SHAPE_VARIABLE,
        power.SHAPE_UNDECLARED,
    }


def test_an_unmodeled_draw_is_never_scaled_by_a_clock(data_registry: Registry) -> None:
    for key in (
        data_corpus.RAILCAR_ITEM,
        data_corpus.ACCELERATOR_BUILDING,
        data_corpus.CHARGER_BUILDING,
    ):
        result = clocked(data_registry.buildings[key], OVERCLOCK)
        assert result.outcome == power.OUTCOME_UNMODELED, key
        assert result.megawatts is None, key
        assert result.coefficient is None, key
        assert result.deferred is None, key


# ---------------------------------------------------------------------------
# The clock ceiling - ADR 0005 and ADR 0006
# ---------------------------------------------------------------------------


def test_the_slot_count_is_unmeasured_on_this_machine() -> None:
    # The premise every assertion below rests on. If this ever becomes an int,
    # the ceiling story changes by ADR and this is the test that says so.
    assert OVERCLOCK_POTENTIAL_SHARD_SLOTS is None


def test_the_clock_ceiling_reports_unknown_and_publishes_no_ceiling_number(
    data_registry: Registry,
) -> None:
    ceiling = power.clock_ceiling(data_registry.buildings[data_corpus.BLENDER_BUILDING])
    assert ceiling.known is False
    assert ceiling.slots is None
    assert "unmeasured" in ceiling.reason


def test_no_field_exists_anywhere_to_hold_a_ceiling_number() -> None:
    # Structural rather than numeric on purpose: the way to assert that no
    # ceiling is published is to show there is nowhere to put one, not to write
    # a candidate value down and compare against it.
    names = {field.name for field in dataclasses.fields(power.ClockCeiling)}
    assert names == {"base", "slots", "known", "reason"}


def test_the_ceiling_stays_unpublished_even_when_a_slot_count_exists() -> None:
    # The branch no data reaches today. A slot count alone does not make a
    # ceiling - the per-shard extra potential is the other operand and this
    # layer does not carry it - so the reason changes and `known` does not.
    unknown = power.ceiling_reason(None)
    counted = power.ceiling_reason(0)
    assert unknown != counted
    assert "unmeasured" in unknown
    assert "unmeasured" in counted


def test_the_unsharded_base_is_read_from_the_building_and_not_assumed() -> None:
    # The base is a per-building-class document value, so a folded Fraction(1)
    # passes every non-mutating assertion. Only the mutation tells them apart.
    raised = registry_with_entry_key(
        data_corpus.BLENDER_BUILDING, data_corpus.KEY_MAX_POTENTIAL, "2.000000"
    )
    assert power.clock_ceiling(raised.buildings[data_corpus.BLENDER_BUILDING]).base == Fraction(2)
    removed = registry_with_entry_key(
        data_corpus.BLENDER_BUILDING, data_corpus.KEY_MAX_POTENTIAL, None
    )
    assert power.clock_ceiling(removed.buildings[data_corpus.BLENDER_BUILDING]).base is None


def test_clamping_says_it_clamped_to_the_unsharded_base(data_registry: Registry) -> None:
    # ADR 0006's fence. Reading the base as an achievable maximum caps every
    # solve at the un-overclocked value and looks correct on every building
    # nobody has overclocked, so a caller that clamps has to SAY what it is.
    building = data_registry.buildings[data_corpus.BLENDER_BUILDING]
    assert building.unsharded_clock_base == Fraction(1)
    clamped = power.clamp_to_unsharded_base(building, OVERCLOCK)
    assert clamped.clamped is True
    assert clamped.clock == building.unsharded_clock_base
    assert "un-sharded base" in clamped.reason


def test_a_clock_at_or_below_the_unsharded_base_is_not_clamped(data_registry: Registry) -> None:
    building = data_registry.buildings[data_corpus.BLENDER_BUILDING]
    result = power.clamp_to_unsharded_base(building, UNDERCLOCK)
    assert result.clamped is False
    assert result.clock == UNDERCLOCK


def test_a_building_declaring_no_base_is_not_clamped_against_an_invented_one(
    data_registry: Registry,
) -> None:
    building = data_registry.buildings[data_corpus.FLOODLIGHT_BUILDING]
    assert building.unsharded_clock_base is None
    result = power.clamp_to_unsharded_base(building, OVERCLOCK)
    assert result.clamped is False
    assert result.base is None
    assert result.clock == OVERCLOCK


# ---------------------------------------------------------------------------
# The arithmetic - no exact rational value exists away from the reference clock
# ---------------------------------------------------------------------------


def test_at_the_reference_clock_the_draw_is_the_declared_scalar(data_registry: Registry) -> None:
    # x ** e is 1 at a clock of 1 for every exponent, so no exponent is applied
    # and no irrational term appears. This is the only clock with an exact
    # rational answer.
    building = data_registry.buildings[data_corpus.BLENDER_BUILDING]
    result = clocked(building, power.REFERENCE_CLOCK)
    assert result.outcome == power.OUTCOME_EXACT
    assert result.megawatts == Fraction(75)
    assert type(result.megawatts) is Fraction
    assert result.deferred is None


def test_away_from_the_reference_clock_the_term_is_symbolic_and_never_a_number(
    data_registry: Registry,
) -> None:
    # Fraction(5, 2) ** Fraction('1.321929') returns a FLOAT on this
    # interpreter, and the defect is data-dependent - a whole-number exponent
    # returns a Fraction - so a number here would be a silently degraded one.
    building = data_registry.buildings[data_corpus.BLENDER_BUILDING]
    for clock in (OVERCLOCK, UNDERCLOCK):
        result = clocked(building, clock)
        assert result.outcome == power.OUTCOME_DEFERRED, clock
        assert result.megawatts is None, clock
        assert type(result.deferred) is DeferredPowerTerm, clock
        assert result.deferred.base == clock
        assert result.deferred.exponent == building.power_exponent
        assert result.coefficient == building.power_consumption
        assert type(result.coefficient) is Fraction


def test_a_negative_clock_has_no_real_draw_and_is_not_answered(data_registry: Registry) -> None:
    building = data_registry.buildings[data_corpus.BLENDER_BUILDING]
    result = clocked(building, Fraction(-1))
    assert result.outcome == power.OUTCOME_UNDEFINED
    assert result.megawatts is None
    assert result.deferred is None


def test_a_clock_that_is_not_a_fraction_is_refused(data_registry: Registry) -> None:
    # Fraction(60) / 0.5 is the float 120.0 - the right number with the
    # invariant already lost - so the operand is checked rather than trusted.
    building = data_registry.buildings[data_corpus.BLENDER_BUILDING]
    for bad in (1, "1", True):
        with pytest.raises(InexactValueError):
            power.draw_at_clock(building, bad)  # type: ignore[arg-type]


def test_no_result_over_either_corpus_carries_anything_inexact(
    data_registry: Registry, solve_reg: Registry
) -> None:
    # The runtime half of non-negotiable 6, over every building both corpora
    # publish and every outcome the model can produce.
    for registry in (data_registry, solve_reg):
        for key, building in registry.buildings.items():
            audit_exact(power.declared_draw(building), path=f"declared_draw({key})")
            audit_exact(power.clock_ceiling(building), path=f"clock_ceiling({key})")
            for clock in (power.REFERENCE_CLOCK, OVERCLOCK, UNDERCLOCK):
                audit_exact(power.draw_at_clock(building, clock), path=f"draw_at_clock({key})")
                audit_exact(power.clamp_to_unsharded_base(building, clock), path=f"clamp({key})")


def test_the_solve_corpus_draws_are_exact_at_the_reference_clock(solve_reg: Registry) -> None:
    # The solve corpus is the one every other phase 3 slice shares, so its
    # buildings are pinned here too rather than only the parser-trap corpus.
    for key, expected in (
        (solve_corpus.SOLVE_SMELTER_BUILDING, solve_corpus.SMELTER_POWER_MW),
        (solve_corpus.SOLVE_ASSEMBLER_BUILDING, solve_corpus.ASSEMBLER_POWER_MW),
        (solve_corpus.SOLVE_REFINERY_BUILDING, solve_corpus.REFINERY_POWER_MW),
    ):
        result = clocked(solve_reg.buildings[key], power.REFERENCE_CLOCK)
        assert result.outcome == power.OUTCOME_EXACT, key
        assert result.megawatts == expected, key
        assert type(result.megawatts) is Fraction, key


# ---------------------------------------------------------------------------
# Static fences over the module itself
# ---------------------------------------------------------------------------


def test_the_module_contains_no_power_operator_and_no_float_machinery() -> None:
    tree = module_tree(power)
    assert not [node for node in ast.walk(tree) if isinstance(node, ast.Pow)], (
        "** on a Fraction pair silently returns a float for the shipped exponent"
    )
    banned = {"pow", "float", "complex", "round"}
    used = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name) and node.id in banned}
    used |= {
        node.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Attribute) and node.attr in banned
    }
    assert used == set(), f"the power path names float machinery: {sorted(used)}"


def test_the_module_imports_no_float_capable_standard_library() -> None:
    banned = {"math", "statistics", "decimal", "cmath", "numpy"}
    assert imported_modules(power) & banned == set()


def test_the_module_reaches_only_for_its_declared_dependencies() -> None:
    # Seam discipline: solve/ consumes the data layer's published model and the
    # exact primitives, and never the install locator or the docs reader.
    imported = imported_modules(power)
    assert imported & {"clockspeed.data.locate", "clockspeed.data.docs_extract"} == set()
    assert {name for name in imported if name.startswith("clockspeed")} <= {
        "clockspeed.data.registry",
        "clockspeed.data.version",
        "clockspeed.solve.exact",
    }


def test_every_exported_name_resolves() -> None:
    missing = [name for name in power.__all__ if not hasattr(power, name)]
    assert missing == []


def test_no_signature_in_the_module_admits_a_float() -> None:
    # The one case the AST scan above cannot see: a float declared in a
    # signature and flowing in from an annotated caller.
    tree = module_tree(power)
    rendered = {
        ast.unparse(node.annotation)
        for node in ast.walk(tree)
        if isinstance(node, ast.AnnAssign | ast.arg) and node.annotation is not None
    }
    assert not [text for text in rendered if "float" in text], rendered


def test_the_registry_types_this_module_promises_are_the_ones_it_consumes(
    data_registry: Registry,
) -> None:
    # Guards against the model drifting onto a hand-built lookalike: the
    # arguments really are what build_registry publishes.
    building = data_registry.buildings[data_corpus.ACCELERATOR_BUILDING]
    recipe = data_registry.recipes[data_corpus.ACCELERATED_RECIPE]
    assert type(building) is Building
    assert type(recipe) is Recipe
    assert isinstance(power.variable_power_inputs(building, recipe).reason, str)


# ---------------------------------------------------------------------------
# CS-301 - the variable-power law, measured rather than invented
# ---------------------------------------------------------------------------


def test_the_variable_power_law_bounds_a_draw_from_the_recipe_operands(
    data_registry: Registry,
) -> None:
    # ADR 0021. The shipped header states the relation in as many words: the
    # constant is added to the variable draw and reads as a minimum, and the
    # factor added to the constant reads as a maximum. Neither bound is
    # invented and neither is collapsed into a scalar.
    building = data_registry.buildings[data_corpus.ACCELERATOR_BUILDING]
    recipe = data_registry.recipes[data_corpus.ACCELERATED_RECIPE]
    constant = recipe.variable_power_constant
    factor = recipe.variable_power_factor
    assert constant is not None
    assert factor is not None
    bounded = power.bounded_draw(building, recipe)
    assert bounded.modeled is True
    assert bounded.shape == power.SHAPE_VARIABLE
    assert bounded.source == power.SOURCE_RECIPE_LAW
    assert bounded.minimum == constant
    assert bounded.maximum == constant + factor
    assert type(bounded.minimum) is Fraction
    assert type(bounded.maximum) is Fraction


def test_the_law_is_read_off_the_recipe_and_never_folded_into_this_module() -> None:
    # The corpus pair passes every non-mutating assertion against a folded
    # constant, exactly as the exponent does. Only moving the operand tells a
    # read apart from a literal.
    moved = registry_with_entry_key(
        data_corpus.ACCELERATED_RECIPE, data_corpus.KEY_VARIABLE_POWER_CONSTANT, "300.000000"
    )
    bounded = power.bounded_draw(
        moved.buildings[data_corpus.ACCELERATOR_BUILDING],
        moved.recipes[data_corpus.ACCELERATED_RECIPE],
    )
    assert bounded.minimum == Fraction(300)
    assert bounded.maximum == Fraction(300) + Fraction(1250)


def test_the_bounds_are_checked_for_containment_in_the_estimate_of_the_building(
    data_registry: Registry,
) -> None:
    # The estimated range on the building is an INDEPENDENT second source, and
    # ADR 0021 measured it to be the ENVELOPE over the recipes produced there.
    # So the check is containment: the pair lies inside the envelope.
    building = data_registry.buildings[data_corpus.ACCELERATOR_BUILDING]
    recipe = data_registry.recipes[data_corpus.ACCELERATED_RECIPE]
    assert power.bounded_draw(building, recipe).within_estimate is True


def test_a_pair_reaching_past_the_estimate_says_so_rather_than_passing() -> None:
    # The anti-vacuity control for the arm above: were within_estimate a folded
    # True, that arm would stay green while the cross-check measured nothing.
    # The factor here puts the maximum above the declared envelope, which is
    # what a recipe asked against a building that does not produce it looks
    # like - measured on the shipped document, containment rejects the
    # majority of such mispairings.
    moved = registry_with_entry_key(
        data_corpus.ACCELERATED_RECIPE, data_corpus.KEY_VARIABLE_POWER_FACTOR, "5000.000000"
    )
    bounded = power.bounded_draw(
        moved.buildings[data_corpus.ACCELERATOR_BUILDING],
        moved.recipes[data_corpus.ACCELERATED_RECIPE],
    )
    assert bounded.within_estimate is False
    assert bounded.modeled is True, "a disagreement is a reported fact, not a refusal to model"


def test_containment_is_not_an_equality_which_the_shipped_document_refuses() -> None:
    # ADR 0021: equality was the first reading and it fails outright on the
    # building whose recipes carry two distinct bands. A narrower band inside
    # the envelope is the NORMAL case and must not be reported as a mismatch.
    narrow = registry_with_entry_key(
        data_corpus.ACCELERATED_RECIPE, data_corpus.KEY_VARIABLE_POWER_FACTOR, "250.000000"
    )
    building = narrow.buildings[data_corpus.ACCELERATOR_BUILDING]
    bounded = power.bounded_draw(building, narrow.recipes[data_corpus.ACCELERATED_RECIPE])
    assert bounded.maximum == Fraction(500)
    assert bounded.maximum != building.estimated_max_power
    assert bounded.within_estimate is True


def test_a_struct_range_building_is_bounded_from_its_own_declaration(
    data_registry: Registry,
) -> None:
    # The struct shape needs no recipe: the document declares both bounds and
    # the registry lifted them out of the struct string. They are published
    # uncollapsed, and no scalar is invented from them.
    building = data_registry.buildings[data_corpus.RAILCAR_ITEM]
    bounded = power.bounded_draw(building)
    assert bounded.modeled is True
    assert bounded.shape == power.SHAPE_RANGE_ONLY
    assert bounded.source == power.SOURCE_DECLARED_RANGE
    assert bounded.minimum == Fraction(25)
    assert bounded.maximum == Fraction(110)
    assert bounded.within_estimate is None, "the declaration is the estimate, not a second source"


def test_a_variable_power_building_with_no_recipe_is_not_bounded(
    data_registry: Registry,
) -> None:
    building = data_registry.buildings[data_corpus.ACCELERATOR_BUILDING]
    bounded = power.bounded_draw(building)
    assert bounded.modeled is False
    assert bounded.minimum is None
    assert bounded.maximum is None
    assert "recipe" in bounded.reason


def test_a_fixed_draw_building_is_refused_by_the_bounded_path(
    data_registry: Registry,
) -> None:
    building = data_registry.buildings[data_corpus.SYNTHESIZER_BUILDING]
    bounded = power.bounded_draw(building)
    assert bounded.modeled is False
    assert bounded.shape == power.SHAPE_FIXED
    assert bounded.minimum is None
    assert bounded.maximum is None


def test_an_undeclared_draw_is_never_bounded_at_zero(data_registry: Registry) -> None:
    building = data_registry.buildings[data_corpus.CHARGER_BUILDING]
    bounded = power.bounded_draw(building)
    assert bounded.modeled is False
    assert bounded.shape == power.SHAPE_UNDECLARED
    assert bounded.minimum is None
    assert bounded.maximum is None


def test_an_absent_recipe_operand_refuses_rather_than_defaulting_to_zero() -> None:
    moved = registry_with_entry_key(
        data_corpus.ACCELERATED_RECIPE, data_corpus.KEY_VARIABLE_POWER_FACTOR, None
    )
    bounded = power.bounded_draw(
        moved.buildings[data_corpus.ACCELERATOR_BUILDING],
        moved.recipes[data_corpus.ACCELERATED_RECIPE],
    )
    assert bounded.modeled is False
    assert bounded.maximum is None, "an absent factor is not a factor of zero"


def test_every_bounded_draw_the_corpus_produces_is_exact(data_registry: Registry) -> None:
    for key, building in data_registry.buildings.items():
        audit_exact(power.bounded_draw(building), path=f"bounded_draw({key})")
        for recipe_key, recipe in data_registry.recipes.items():
            audit_exact(
                power.bounded_draw(building, recipe),
                path=f"bounded_draw({key}, {recipe_key})",
            )


# ---------------------------------------------------------------------------
# CS-301 - the two branches no fixture reached
# ---------------------------------------------------------------------------


def test_a_base_below_the_reference_clock_clamps_the_reference_clock_itself() -> None:
    # Every shipped entry declares a base of exactly one, so the corpus never
    # reached the branch where even an un-overclocked building is clamped. A
    # base below the reference clock is the case where a caller treating the
    # base as a ceiling silently underclocks a building nobody touched.
    lowered = registry_with_entry_key(
        data_corpus.BLENDER_BUILDING, data_corpus.KEY_MAX_POTENTIAL, "0.500000"
    )
    building = lowered.buildings[data_corpus.BLENDER_BUILDING]
    assert building.unsharded_clock_base == Fraction(1, 2)
    clamped = power.clamp_to_unsharded_base(building, power.REFERENCE_CLOCK)
    assert clamped.clamped is True
    assert clamped.clock == Fraction(1, 2)
    assert "un-sharded base" in clamped.reason


def test_a_recipe_naming_two_producers_is_bounded_once_per_building() -> None:
    # The operands are per RECIPE and the estimated range is per BUILDING, so
    # a recipe with two producers has no single answer. Each pairing is asked
    # separately and the two disagree - which is the fact a caller that picks
    # the first producer and calls it the draw cannot see.
    both = registry_with_entry_key(
        data_corpus.ACCELERATED_RECIPE,
        data_corpus.KEY_PRODUCED_IN,
        data_corpus.class_path_blob([data_corpus.ACCELERATOR_PATH, data_corpus.BLENDER_PATH]),
    )
    recipe = both.recipes[data_corpus.ACCELERATED_RECIPE]
    assert recipe.produced_in == (
        data_corpus.ACCELERATOR_BUILDING,
        data_corpus.BLENDER_BUILDING,
    ), recipe.produced_in
    variable = power.bounded_draw(both.buildings[data_corpus.ACCELERATOR_BUILDING], recipe)
    fixed = power.bounded_draw(both.buildings[data_corpus.BLENDER_BUILDING], recipe)
    assert variable.modeled is True
    assert fixed.modeled is False, "the same operands do not bound a fixed-draw building"
    assert fixed.shape == power.SHAPE_FIXED
