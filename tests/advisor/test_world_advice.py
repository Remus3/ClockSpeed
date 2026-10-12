"""CS-1270: the advisor builds its own rule inputs from a world model.

THE CLAIM. :func:`clockspeed.advisor.advise.inputs_of` takes the world model
the surface already holds plus the normalized registry and returns the
:class:`~clockspeed.advisor.trace.WorldInputs` :func:`advise` needs, composing
the audit models itself - placement, machines, network, then the power
balance. :func:`clockspeed.advisor.advise.advise_world` is the one call a
surface makes: inputs, rules, cards and both stores, keyed by the model's own
world token. The surface may not compose the audit models (CS-1189's machines
seam); the advisor is the layer that consumes audit, so the composition lives
here.

THE ORACLE IS THE AUDIT CONSTRUCTORS CALLED BY HAND. Every arm compares the
advisor's answer against ``balance_inputs(balance_of(placement_of, buildings,
machines_of, network_of))`` plus ``unlock_keys`` built in this module, so the function is
graded against the composition it claims to perform rather than against a
number transcribed from a run. Non-vacuity: one world carries a machine with
no priced draw, so the composed inputs differ from an empty world's and the
gap rule fires a card.

CS-1285 SLICE D: THE FUEL AUDIT JOINS THE COMPOSITION. :func:`inputs_of` also
runs ``fuel_supply_of`` over the SAME machines model the balance reads and
offers ``fuel_inputs`` beside the balance inputs, so the registered fuel rules
never run on a world that lacks their inputs (the slice C ruling G6). The
oracle grows the same way, by hand: ``balance_inputs`` and ``fuel_inputs``
merged over the audit constructors, never through the module under test. A
name both adapters offer must raise, never overwrite. The fuel world here is a
liquid burner short of fuel over a complete flow and a solid burner whose
supply is never measured; its figures are worked by hand in
:data:`FUEL_SHORTFALL_MW` and :data:`COAL_BURN_PER_MINUTE`.

Every token, class name and number here is invented. No save and no install
is read; every store lives in a temporary directory and every instant is
injected.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from fractions import Fraction
from types import MappingProxyType
from typing import TYPE_CHECKING, Final

import pytest

from clockspeed.advisor import advise as advise_module
from clockspeed.advisor.advise import (
    advise,
    advise_world,
    inputs_of,
    settled_rules,
    world_inputs,
)
from clockspeed.advisor.ledger import CardState, Ledger, MuteStore
from clockspeed.advisor.rules import fuel as fuel_rules
from clockspeed.advisor.rules import power, registered_rules
from clockspeed.advisor.rules.fuel import fuel_inputs
from clockspeed.advisor.rules.power import balance_inputs
from clockspeed.advisor.trace import (
    InputValue,
    StepKind,
    TraceStep,
    WorldInputs,
    run_rules,
    unlock_keys,
)
from clockspeed.audit import fuel as fuel_audit
from clockspeed.audit.balance import balance_of
from clockspeed.audit.fuel import fuel_supply_of
from clockspeed.audit.machines import (
    PROPERTY_OVERCLOCK,
    PROPERTY_PRODUCING,
    PROPERTY_RECIPE,
    machines_of,
)
from clockspeed.audit.network import network_of
from clockspeed.audit.placement import placement_of
from clockspeed.data.registry import Registry
from clockspeed.save.objects import ObjectReference
from clockspeed.save.world import RecordProperties, WorldModel, WorldProperties
from tests.audit import test_balance as balance_fixtures
from tests.audit import test_fuel as fuel_fixtures
from tests.audit import test_production as production_fixtures

if TYPE_CHECKING:
    from pathlib import Path

    from clockspeed.audit.balance import WorldBalance
    from clockspeed.save.world import UnlockState

#: The instant every resolution here reads. Injected, never a clock.
NOW: Final = 1000

#: A machine class no synthetic registry here prices, so its draw is a gap.
UNPRICED_MACHINE: Final = balance_fixtures.NOT_IN_REGISTRY


def synthetic_registry() -> Registry:
    """A registry whose buildings are the balance suite's whole-world set."""
    return Registry(
        items=MappingProxyType({}),
        recipes=MappingProxyType({}),
        buildings=MappingProxyType(dict(balance_fixtures.whole_world_registry())),
        warnings=(),
        unknown_groups=(),
    )


def gap_world() -> WorldModel:
    """A world of one priced building and one producing machine nothing prices."""
    base = balance_fixtures.world_of(balance_fixtures.FIXED_WHOLE, UNPRICED_MACHINE)
    entries = dict(base.properties.by_record_index)
    machine_index = 1
    entries[machine_index] = replace(
        entries[machine_index],
        values=MappingProxyType({PROPERTY_PRODUCING: True}),
    )
    return replace(base, properties=WorldProperties(by_record_index=MappingProxyType(entries)))


def balance_by_hand(model: WorldModel, registry: Registry) -> WorldInputs:
    """The balance half of the composition - all :func:`inputs_of` offered before slice D."""
    balance = balance_of(
        placement_of(model),
        registry.buildings,
        machines_of(model),
        network_of(model),
        generators=registry.generators,
    )
    return WorldInputs(values=balance_inputs(balance), unlocks=unlock_keys(model.unlocks))


def by_hand(model: WorldModel, registry: Registry) -> WorldInputs:
    """The composition :func:`inputs_of` claims, spelled out through the audit.

    The balance inputs, then the fuel audit's inputs over the same world, merged
    by hand. The two name sets are asserted disjoint here, so the oracle can
    never overwrite one adapter's input with the other's.
    """
    balance = balance_by_hand(model, registry)
    offered = fuel_inputs(fuel_supply_of(machines_of(model), registry), registry)
    overlap = sorted(set(balance.values) & set(offered))
    assert overlap == []
    return WorldInputs(values={**balance.values, **offered}, unlocks=balance.unlocks)


# ---------------------------------------------------------------------------
# CS-1285 slice D: the fuel world
# ---------------------------------------------------------------------------

#: The liquid burner's nameplate at clock one, from the fuel audit's fixtures.
FUEL_GEN_MW: Final = fuel_fixtures.FUEL_GEN_MW

#: The liquid fuel's energy per cubic metre: three quarters of a megajoule per
#: litre, times a thousand litres.
FUEL_MJ_PER_M3: Final = Fraction(750)

#: One refinery at clock one: one cubic metre per six-second cycle, ten a minute.
FUEL_M3_PER_MINUTE: Final = Fraction(10)

#: Ten cubic metres a minute at 750 MJ each is 7500 MJ a minute, 125 MW.
FUEL_SUPPLY_MW: Final = Fraction(125)

#: The burner's 250 MW demand less the 125 MW supplied.
FUEL_SHORTFALL_MW: Final = Fraction(125)

#: The shortfall as liquid fuel alone: 125 MW times sixty over 750 MJ.
FUEL_SHORTFALL_M3_PER_MINUTE: Final = Fraction(10)

#: The solid burner's 75 MW at clock one, burning its first fuel of 300 MJ an
#: item: 75 times sixty over 300.
COAL_BURN_PER_MINUTE: Final = Fraction(15)

#: The clock every fuel world record carries, as the save's float32 tag holds it.
CLOCK_ONE: Final = 1.0


def _recipe_reference(recipe_key: str) -> ObjectReference:
    """A current-recipe tag naming one synthetic recipe under the shipped asset root."""
    stem = recipe_key.removesuffix("_C")
    return ObjectReference(
        property_name=PROPERTY_RECIPE,
        level_reference="",
        object_path=f"/Game/FactoryGame/Synthetic/{stem}.{recipe_key}",
    )


def fuel_world() -> WorldModel:
    """A liquid burner, a solid burner and one refinery making the liquid fuel.

    Every record runs at clock one. The refinery's flow is complete and makes
    half the liquid burner's fuel, so the supply rule FIRES on it; the solid
    burner's supply is never measured, so the demand rule fires on it.
    """
    generators = (fuel_fixtures.GEN_FUEL, fuel_fixtures.GEN_COAL)
    refinery = fuel_fixtures.RECIPES[fuel_fixtures.R_FUEL].produced_in[0]
    base = balance_fixtures.world_of(*generators, refinery)
    entries = dict(base.properties.by_record_index)
    running = MappingProxyType({PROPERTY_PRODUCING: True, PROPERTY_OVERCLOCK: CLOCK_ONE})
    for index in range(len(generators)):
        entries[index] = replace(entries[index], values=running)
    entries[len(generators)] = replace(
        entries[len(generators)],
        values=running,
        references=(_recipe_reference(fuel_fixtures.R_FUEL),),
    )
    return replace(base, properties=WorldProperties(by_record_index=MappingProxyType(entries)))


def fuel_registry() -> Registry:
    """The fuel audit's synthetic registry: invented items, generators and recipes."""
    return fuel_fixtures.REGISTRY


#: The worlds the composition is graded over: no fuel class, and the fuel world.
WORLDS: Final[dict[str, tuple[Callable[[], WorldModel], Callable[[], Registry]]]] = {
    "gap": (gap_world, synthetic_registry),
    "fuel": (fuel_world, fuel_registry),
}


@pytest.mark.parametrize("world_name", sorted(WORLDS))
def test_inputs_of_is_the_audit_composition_over_one_world(world_name: str) -> None:
    make_world, make_registry = WORLDS[world_name]
    model = make_world()
    registry = make_registry()

    built = inputs_of(model, registry)
    expected = by_hand(model, registry)

    same_names = sorted(built.values) == sorted(expected.values)
    same_values = dict(built.values) == dict(expected.values)
    same_unlocks = built.unlocks == expected.unlocks
    assert same_names
    assert same_values
    assert same_unlocks


def test_the_fuel_world_fixture_really_fires_and_really_stays_undecided() -> None:
    """Non-vacuity: the audit itself finds the shortfall worked by hand above."""
    result = fuel_supply_of(machines_of(fuel_world()), fuel_registry())

    verdicts = {v.class_name: v for v in result.verdicts}
    short = verdicts[fuel_fixtures.GEN_FUEL]
    solid = verdicts[fuel_fixtures.GEN_COAL]
    assert sorted(verdicts) == sorted((fuel_fixtures.GEN_FUEL, fuel_fixtures.GEN_COAL))
    assert result.flow_complete is True
    assert short.verdict == fuel_audit.VERDICT_FIRE
    assert short.demand_megawatts == FUEL_GEN_MW
    assert short.pooled_megawatts == FUEL_SUPPLY_MW
    assert short.shortfall_megawatts == FUEL_SHORTFALL_MW
    assert solid.verdict == fuel_audit.VERDICT_INDETERMINATE
    assert solid.reasons == (fuel_audit.REASON_SOLID_SUPPLY_UNMODELLED,)


@pytest.mark.parametrize("world_name", sorted(WORLDS))
def test_no_registered_rule_halts_on_a_missing_input_over_inputs_of(world_name: str) -> None:
    """The G6 hazard: a registered rule run on a world that lacks its inputs halts.

    Graded on the traces rather than on the declarations: a power rule
    declares the generation figure but reads it only when a production model
    exists, so a declared-but-unoffered name is not itself a halt.
    """
    make_world, make_registry = WORLDS[world_name]
    traces = run_rules(registered_rules(), inputs_of(make_world(), make_registry()))

    missing = sorted(
        (trace.rule_id, step.subject)
        for trace in traces
        for step in trace.steps
        if step.kind is StepKind.INPUT_MISSING
    )
    assert missing == []


@pytest.mark.parametrize("world_name", sorted(WORLDS))
def test_inputs_of_offers_every_fuel_rule_input(world_name: str) -> None:
    """Independent of the registry: both fuel rules' declarations are offered."""
    make_world, make_registry = WORLDS[world_name]
    built = inputs_of(make_world(), make_registry())

    declared = set(fuel_rules.SUPPLY_INPUTS) | set(fuel_rules.DEMAND_INPUTS)
    missing = sorted(declared - set(built.values))
    assert missing == []


def test_a_name_both_adapters_offer_raises_and_never_overwrites(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    planted = InputValue(Fraction(918273645), "synthetic.collision")

    def colliding(world_fuel: object, registry: Registry) -> dict[str, InputValue]:
        del world_fuel, registry
        return {power.IN_GENERATION: planted}

    monkeypatch.setattr(advise_module, "fuel_inputs", colliding)

    with pytest.raises(ValueError, match="more than one adapter"):
        inputs_of(fuel_world(), fuel_registry())


def test_merged_inputs_refuses_a_name_any_two_groups_share_and_renders_no_value() -> None:
    first = {"synthetic.a": InputValue(Fraction(1), "synthetic.first")}
    second = {"synthetic.b": InputValue(Fraction(2), "synthetic.second")}
    third = {"synthetic.b": InputValue(Fraction(918273645), "synthetic.third")}

    joined = advise_module.merged_inputs(first, second)
    with pytest.raises(ValueError, match="more than one adapter") as refused:
        advise_module.merged_inputs(first, second, third)

    assert sorted(joined) == ["synthetic.a", "synthetic.b"]
    assert joined["synthetic.b"] is second["synthetic.b"]
    message = str(refused.value)
    assert "synthetic.b" in message
    assert "918273645" not in message
    assert "synthetic.third" not in message


def test_the_balance_and_the_fuel_audit_read_one_machines_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """machines_of runs once; both audits get that model, and no raw item is declared."""
    made: list[object] = []
    fuel_calls: list[tuple[object, object, dict[str, object]]] = []
    real_machines_of = advise_module.machines_of
    real_fuel_supply_of = advise_module.fuel_supply_of

    def counting(model: WorldModel) -> object:
        made.append(real_machines_of(model))
        return made[-1]

    def recording(machines: object, registry: Registry, **kwargs: object) -> object:
        fuel_calls.append((machines, registry, kwargs))
        return real_fuel_supply_of(machines, registry, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(advise_module, "machines_of", counting)
    monkeypatch.setattr(advise_module, "fuel_supply_of", recording)
    registry = fuel_registry()

    inputs_of(fuel_world(), registry)

    assert len(made) == 1
    assert len(fuel_calls) == 1
    machines, handed, kwargs = fuel_calls[0]
    assert machines is made[0]
    assert handed is registry
    assert kwargs == {}


def _steps(trace_steps: tuple[TraceStep, ...], kind: StepKind, prefix: str) -> list[object]:
    """The values of one kind of step whose subject starts with ``prefix``, in order."""
    return [
        step.value for step in trace_steps if step.kind is kind and step.subject.startswith(prefix)
    ]


def test_advise_world_fires_both_fuel_rules_with_the_figures_worked_by_hand(
    tmp_path: Path,
) -> None:
    served = advise_world(
        fuel_world(), fuel_registry(), ledger=Ledger(tmp_path), mutes=MuteStore(tmp_path), now=NOW
    )

    by_rule = {trace.rule_id: trace for trace in served.traces}
    fired = sorted(a.card.rule_id for a in served.cards)
    supply = by_rule[fuel_rules.SUPPLY_RULE.rule_id]
    demand = by_rule[fuel_rules.DEMAND_RULE.rule_id]
    gen_fuel = fuel_fixtures.GEN_FUEL
    gen_coal = fuel_fixtures.GEN_COAL
    assert fuel_rules.SUPPLY_RULE.rule_id in fired
    assert fuel_rules.DEMAND_RULE.rule_id in fired
    shortfalls = _steps(supply.steps, StepKind.COMPUTED, f"shortfall MW of {gen_fuel}")
    rates = _steps(supply.steps, StepKind.COMPUTED, "shortfall per minute of")
    burns = _steps(demand.steps, StepKind.COMPUTED, "burn per minute of")
    assert shortfalls == [FUEL_SHORTFALL_MW]
    assert rates == [FUEL_SHORTFALL_M3_PER_MINUTE]
    assert burns[0] == COAL_BURN_PER_MINUTE
    assert supply.recommendation is not None
    assert demand.recommendation is not None
    assert supply.recommendation.subject_key == fuel_rules.SUBJECT_SUPPLY_PREFIX + gen_fuel
    assert demand.recommendation.subject_key == fuel_rules.SUBJECT_DEMAND_PREFIX + gen_coal


def test_the_fuel_inputs_are_sourced_to_the_fuel_audit(tmp_path: Path) -> None:
    """Every fuel input a served trace reads names the audit field it came from."""
    served = advise_world(
        fuel_world(), fuel_registry(), ledger=Ledger(tmp_path), mutes=MuteStore(tmp_path), now=NOW
    )

    supply = next(t for t in served.traces if t.rule_id == fuel_rules.SUPPLY_RULE.rule_id)
    sources = {
        step.subject: step.source for step in supply.steps if step.kind is StepKind.INPUT_READ
    }
    assert sources[fuel_rules.IN_VERDICTS] == "audit.fuel.verdicts.verdict"
    assert sources[fuel_rules.IN_SHORTFALL] == "audit.fuel.verdicts.shortfall_megawatts"
    assert sources[fuel_rules.IN_CLASS_NAMES] == "registry.generators.display_name"


def test_inputs_of_reads_the_world_rather_than_answering_a_constant() -> None:
    registry = synthetic_registry()

    gap = inputs_of(gap_world(), registry)
    empty = inputs_of(balance_fixtures.world_of(), registry)

    differs = dict(gap.values) != dict(empty.values)
    assert differs, "two different worlds produced the same inputs"


def test_the_machine_world_fixture_really_carries_a_machine() -> None:
    entry = gap_world().properties.by_record_index[1]

    assert isinstance(entry, RecordProperties)
    assert PROPERTY_PRODUCING in entry.values


def test_advise_world_equals_advise_over_the_built_inputs(tmp_path: Path) -> None:
    model = gap_world()
    registry = synthetic_registry()

    served = advise_world(
        model, registry, ledger=Ledger(tmp_path), mutes=MuteStore(tmp_path), now=NOW
    )
    direct = advise(
        model.token,
        by_hand(model, registry),
        ledger=Ledger(tmp_path),
        mutes=MuteStore(tmp_path),
        now=NOW,
    )

    assert [a.card.id for a in served.cards] == [a.card.id for a in direct.cards]
    assert [a.card.tier3 for a in served.cards] == [a.card.tier3 for a in direct.cards]
    fired = [a.card.rule_id for a in served.cards]
    assert power.GAP_RULE.rule_id in fired


def test_advise_world_keys_the_ledger_by_the_models_own_token(tmp_path: Path) -> None:
    model = gap_world()
    registry = synthetic_registry()
    first = advise_world(
        model, registry, ledger=Ledger(tmp_path), mutes=MuteStore(tmp_path), now=NOW
    )
    gap_id = next(a.card.id for a in first.cards if a.card.rule_id == power.GAP_RULE.rule_id)
    Ledger(tmp_path).set_state(model.token, gap_id, CardState.dismissed())

    again = advise_world(
        model, registry, ledger=Ledger(tmp_path), mutes=MuteStore(tmp_path), now=NOW
    )

    state = next(a.state.kind for a in again.cards if a.card.id == gap_id)
    assert first.new_world is True
    assert again.new_world is False
    assert state == "dismissed"


def test_advise_world_writes_no_store(tmp_path: Path) -> None:
    advise_world(
        gap_world(),
        synthetic_registry(),
        ledger=Ledger(tmp_path),
        mutes=MuteStore(tmp_path),
        now=NOW,
    )

    created = len(list(tmp_path.iterdir()))
    assert created == 0


# CS-1271: generated power is live through the advisor's own composition.
#
# THE CLAIM. :func:`inputs_of` hands ``balance_of`` the registry's generator
# namespace, so a built generator reaches the balance the rules read. THE
# ORACLE is ``balance_of`` called by hand WITH ``generators=registry.generators``
# over the same world; the balance :func:`inputs_of` builds is captured by a
# recording spy on :func:`world_inputs`, the one call it hands the balance to.
# Red first: omitting the keyword leaves the flag False and no figure.


def generator_registry() -> Registry:
    """A registry carrying real generator spellings in both namespaces."""
    return Registry(
        items=MappingProxyType({}),
        recipes=MappingProxyType({}),
        buildings=production_fixtures.real_consumers(),
        warnings=(),
        unknown_groups=(),
        generators=production_fixtures.real_generators(),
    )


def captured_balance(
    model: WorldModel, registry: Registry, monkeypatch: pytest.MonkeyPatch
) -> tuple[WorldInputs, WorldBalance]:
    """Run :func:`inputs_of` and capture the balance it hands :func:`world_inputs`."""
    seen: list[WorldBalance] = []

    def spy(balance: WorldBalance, unlocks: UnlockState) -> WorldInputs:
        seen.append(balance)
        return world_inputs(balance, unlocks)

    monkeypatch.setattr(advise_module, "world_inputs", spy)
    built = inputs_of(model, registry)
    calls = len(seen)
    assert calls == 1
    return built, seen[0]


def test_inputs_of_makes_a_built_generators_capacity_live(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    model = balance_fixtures.world_of(production_fixtures.FUEL)
    registry = generator_registry()
    oracle = balance_of(
        placement_of(model),
        registry.buildings,
        machines_of(model),
        network_of(model),
        generators=registry.generators,
    )

    built, balance = captured_balance(model, registry, monkeypatch)

    offered = built.values[power.IN_PRODUCTION_AVAILABLE].value
    available = balance.production_available
    assert offered is True
    assert available is True
    assert balance.production is not None
    assert oracle.production is not None
    capacity = balance.production.capacity_megawatts
    expected = oracle.production.capacity_megawatts
    exact = type(capacity) is Fraction
    assert exact
    assert capacity == expected
    assert capacity == production_fixtures.FUEL_MEGAWATTS


def test_a_registry_with_no_generator_namespace_keeps_production_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    model = balance_fixtures.world_of(balance_fixtures.FIXED_WHOLE)

    built, balance = captured_balance(model, synthetic_registry(), monkeypatch)

    offered = built.values[power.IN_PRODUCTION_AVAILABLE].value
    assert offered is False
    assert balance.production is None


def test_a_world_with_no_built_generator_is_an_exact_zero_capacity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """MEASURED balance_of contract (CS-1059): a non-empty namespace computes a figure.

    With the registry's generator namespace supplied and no generator built,
    ``balance_of`` computes a complete production model of exactly zero, so
    the flag is True. Pinned so the behaviour is explicit, not assumed.
    """
    model = balance_fixtures.world_of()

    built, balance = captured_balance(model, generator_registry(), monkeypatch)

    offered = built.values[power.IN_PRODUCTION_AVAILABLE].value
    assert offered is True
    assert balance.production is not None
    capacity = balance.production.capacity_megawatts
    complete = balance.production.production_complete
    assert capacity == Fraction(0)
    assert complete is True


def test_a_built_generator_settles_the_headroom_rule_end_to_end(tmp_path: Path) -> None:
    """The real path - inputs_of, then advise - reaches a definite headroom verdict.

    A built fuel generator over a world with no priced draw: generation covers
    the draw, so the rule runs clean to silence. Before CS-1271's repair it
    stopped on a missing generation input and settled nothing.
    """
    model = balance_fixtures.world_of(production_fixtures.FUEL)

    served = advise_world(
        model,
        generator_registry(),
        ledger=Ledger(tmp_path),
        mutes=MuteStore(tmp_path),
        now=NOW,
    )

    headroom = next(t for t in served.traces if t.rule_id == power.HEADROOM_RULE.rule_id)
    missing = [s.subject for s in headroom.steps if s.kind is StepKind.INPUT_MISSING]
    settled = power.HEADROOM_RULE.rule_id in settled_rules(served.traces)
    reasons = [s.reason for s in headroom.steps if s.kind is StepKind.ALTERNATIVE_REJECTED]
    assert missing == []
    assert settled
    assert reasons == ["generation covers the upper bound of the clocked draw"]
