"""CS-1285 slice C: the D4 fuel rules, power.fuel_supply and power.fuel_demand.

Graded here (``docs/history_notes.md`` section CS-1285, relocated there from
``docs/item_notes/phase5.md`` on the item's close - its Acceptance and the
session 134 ruling - plus the slice C rulings G1 to G6 of 2026-10-12):

- the adapter offers every input the two rules declare, each an exact value
  the engine admits, sourced to the fuel audit field (or, for a display name,
  the registry field) it came from; an unknown figure is offered as None,
  never a zero; and over a real ``fuel_supply_of`` result it carries the
  audit's own figures;
- the supply rule fires with the exact shortfall only on a FIRE verdict, its
  tier 3 converting that shortfall into a rate for every accepted fuel; a
  REJECT is silent and settled; an INDETERMINATE class gets no sized card and
  never settles the rule (G2);
- the demand rule fires on every INDETERMINATE class and on none other, reads
  no supply input, states each class's burn per accepted fuel, settles through
  reject steps, and names an unknown burn as indeterminate, never zero (G5);
- the card subject is the SORTED SET of the classes a rule fired on (G1);
- every figure a rule states is recomputed from leaf figures and compared with
  the audit's own, and any disagreement - a fuel paired with another fuel's
  energy above all - is a rule-error, never a card (G3);
- a display name that is not printable text falls back to the class key, and
  the fallback is a recorded step (G4);
- CS-1288: both rules declare the three build inputs ahead of their own and
  read every name once; off the pin every card names both builds on tier 2,
  keeps its headline and every computed figure, and no run - firing or
  silent - settles its rule. The build inputs are the audit's own over a
  synthetic header whose build is the pin read at test time, or the pin plus
  one, never a typed changelist (the session 138 rulings F1, F7 and F8).

THE RULES ARE RUN THROUGH ``run_rule`` WITH THEIR SPECS NAMED, never through
the registry: registering the family is slice D's act (G6).

EVERY WORLD IS SYNTHETIC. The audit results are hand-built from invented
classes, fuels and figures, and the figures they carry are RE-DERIVED here
from the fixture constants - a generator of ``P`` MW at clock sum ``c``
demands ``P * c`` MW; a fuel of ``E`` MJ per unit burns ``D * 60 / E`` units a
minute at a demand of ``D`` MW; a supply of ``s`` units a minute yields
``s * E / 60`` MW. One end-to-end arm builds a real ``fuel_supply_of`` result
from invented machines and an invented registry, on the builder pattern of
``tests/audit/test_fuel.py``. No save, no docs file and no install is read.
"""

from __future__ import annotations

from dataclasses import replace
from fractions import Fraction
from types import MappingProxyType
from typing import TYPE_CHECKING, Final

import pytest

from clockspeed.advisor.advise import settled_rules
from clockspeed.advisor.build import BUILD_INPUTS
from clockspeed.advisor.cards import Card, card_for, card_id
from clockspeed.advisor.rules import power as power_rules
from clockspeed.advisor.rules.fuel import (
    DEMAND_INPUTS,
    DEMAND_RULE,
    IN_BURNS,
    IN_CLASS_NAMES,
    IN_CLASSES,
    IN_CLOCK_SUM,
    IN_DEMAND,
    IN_FUEL_NAMES,
    IN_MJ,
    IN_NAMEPLATE,
    IN_OMITTED,
    IN_POOLED,
    IN_SHORTFALL,
    IN_SHORTFALL_RATES,
    IN_SUPPLY,
    IN_SUPPLY_MW,
    RULES,
    SUPPLY_INPUTS,
    SUPPLY_RULE,
    fuel_inputs,
)
from clockspeed.advisor.trace import (
    InputValue,
    Recommendation,
    RuleContext,
    RuleSpec,
    StepKind,
    Trace,
    TraceStep,
    WorldInputs,
    run_rule,
)
from clockspeed.audit.build import WARN_BUILD_MISMATCH, WARN_BUILD_UNCOMPARED
from clockspeed.audit.fuel import (
    DEMAND_REASONS,
    EXCLUSIONS,
    INDETERMINATE_REASONS,
    REASON_BOOST_UNMODELED,
    REASON_CLOCK_REFUSED,
    REASON_CLOCK_UNREAD,
    REASON_DETAIL,
    REASON_ENERGY_UNKNOWN,
    REASON_FLOW_INCOMPLETE,
    REASON_FUELS_UNREAD,
    REASON_INSTANCES_OMITTED,
    REASON_PRODUCTION_GAP,
    REASON_SOLID_SUPPLY_UNMODELLED,
    REASON_SUPPLY_INPUT_UNCOVERED,
    REASON_SUPPLY_UNMEASURED,
    UNIT_CUBIC_METRE,
    UNIT_ITEM,
    VERDICT_FIRE,
    VERDICT_INDETERMINATE,
    VERDICT_REJECT,
    FuelBurn,
    FuelDemand,
    FuelLine,
    FuelVerdict,
    WorldFuel,
    fuel_supply_of,
)
from clockspeed.audit.machines import MachineState, WorldMachines
from clockspeed.data.registry import (
    FORM_LIQUID,
    FORM_SOLID,
    LITRES_PER_CUBIC_METRE,
    Generator,
    Item,
    Recipe,
    RecipeIO,
    Registry,
)
from tests.advisor.build_fixtures import (
    build_check,
    docs_pin,
    game_pin,
    off_pin_build_inputs,
    pinned_build_inputs,
    uncompared_build_inputs,
)

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping

#: One save's build inputs, as :mod:`tests.advisor.build_fixtures` builds them.
BuildInputs = dict[str, InputValue]

# ---------------------------------------------------------------------------
# Synthetic content - every key and name invented
# ---------------------------------------------------------------------------

FUEL: Final = "Desc_QxFuel_C"
TURBO: Final = "Desc_QxTurbo_C"
BIO: Final = "Desc_QxBio_C"
COAL: Final = "Desc_QxCoal_C"
#: A liquid whose energy value is unknown.
DUD: Final = "Desc_QxDud_C"

FUEL_MJ_PER_LITRE: Final = Fraction(3, 4)
TURBO_MJ_PER_LITRE: Final = Fraction(2)
BIO_MJ_PER_LITRE: Final = Fraction(3, 2)
COAL_MJ_PER_ITEM: Final = Fraction(300)

#: Megajoules per unit burned, re-derived: a fluid's per-litre value times the
#: litres in a cubic metre, a solid's per-item value as declared.
FUEL_MJ: Final = FUEL_MJ_PER_LITRE * LITRES_PER_CUBIC_METRE
TURBO_MJ: Final = TURBO_MJ_PER_LITRE * LITRES_PER_CUBIC_METRE
BIO_MJ: Final = BIO_MJ_PER_LITRE * LITRES_PER_CUBIC_METRE
MJ: Final[Mapping[str, Fraction | None]] = MappingProxyType(
    {FUEL: FUEL_MJ, TURBO: TURBO_MJ, BIO: BIO_MJ, COAL: COAL_MJ_PER_ITEM, DUD: None}
)
UNITS: Final[Mapping[str, str]] = MappingProxyType(
    {
        FUEL: UNIT_CUBIC_METRE,
        TURBO: UNIT_CUBIC_METRE,
        BIO: UNIT_CUBIC_METRE,
        COAL: UNIT_ITEM,
        DUD: UNIT_CUBIC_METRE,
    }
)

GEN_ALPHA: Final = "Build_QxAlphaGen_C"
GEN_BRAVO: Final = "Build_QxBravoGen_C"
GEN_CHARLIE: Final = "Build_QxCharlieGen_C"
GEN_DELTA: Final = "Build_QxDeltaGen_C"

ALPHA_MW: Final = Fraction(250)
BRAVO_MW: Final = Fraction(150)
CHARLIE_MW: Final = Fraction(75)
DELTA_MW: Final = Fraction(40)

NAMEPLATES: Final[Mapping[str, Fraction]] = MappingProxyType(
    {GEN_ALPHA: ALPHA_MW, GEN_BRAVO: BRAVO_MW, GEN_CHARLIE: CHARLIE_MW, GEN_DELTA: DELTA_MW}
)
ACCEPTED: Final[Mapping[str, tuple[str, ...]]] = MappingProxyType(
    {GEN_ALPHA: (FUEL, TURBO), GEN_BRAVO: (BIO,), GEN_CHARLIE: (COAL,), GEN_DELTA: (DUD,)}
)

ALPHA_NAME: Final = "Qx Alpha Generator"
BRAVO_NAME: Final = "Qx Bravo Generator"
FUEL_NAME: Final = "Qx Fuel"
TURBO_NAME: Final = "Qx Turbo"
BIO_NAME: Final = "Qx Bio"

#: Recipe machines for the end-to-end arm. Each recipe makes one cubic metre
#: per six-second cycle, so one machine at clock one makes 60 / 6 a minute.
REFINERY: Final = "Build_QxRefinery_C"
MAKER: Final = "Build_QxMaker_C"
R_FUEL: Final = "Recipe_QxFuel_C"
R_TURBO: Final = "Recipe_QxTurbo_C"
CYCLE_SECONDS: Final = 6

SIXTY: Final = Fraction(60)
ONE: Final = Fraction(1)

SUPPLY_ID: Final = "power.fuel_supply"
DEMAND_ID: Final = "power.fuel_demand"


def _item(key: str, name: str, form: str, energy: Fraction | None) -> Item:
    return Item(
        key=key,
        display_name=name,
        form=form,
        energy_value=energy,
        sink_points=None,
        is_fluid=form == FORM_LIQUID,
    )


def _generator(key: str, name: str) -> Generator:
    return Generator(
        key=key,
        display_name=name,
        power_production=NAMEPLATES[key],
        variable_production_constant=None,
        variable_production_factor=None,
        is_variable_production=False,
        accepted_fuels=ACCEPTED[key],
    )


def _recipe(key: str, output: str, produced_in: str) -> Recipe:
    return Recipe(
        key=key,
        display_name=f"Qx recipe {key}",
        duration=Fraction(CYCLE_SECONDS),
        inputs=(),
        outputs=(RecipeIO(item_key=output, amount=ONE),),
        produced_in=(produced_in,),
        variable_power_constant=None,
        variable_power_factor=None,
    )


ITEMS: Final[Mapping[str, Item]] = MappingProxyType(
    {
        FUEL: _item(FUEL, FUEL_NAME, FORM_LIQUID, FUEL_MJ_PER_LITRE),
        TURBO: _item(TURBO, TURBO_NAME, FORM_LIQUID, TURBO_MJ_PER_LITRE),
        BIO: _item(BIO, BIO_NAME, FORM_LIQUID, BIO_MJ_PER_LITRE),
        COAL: _item(COAL, "Qx Coal", FORM_SOLID, COAL_MJ_PER_ITEM),
        DUD: _item(DUD, "Qx Dud", FORM_LIQUID, None),
    }
)
GENERATORS: Final[Mapping[str, Generator]] = MappingProxyType(
    {
        GEN_ALPHA: _generator(GEN_ALPHA, ALPHA_NAME),
        GEN_BRAVO: _generator(GEN_BRAVO, BRAVO_NAME),
        GEN_CHARLIE: _generator(GEN_CHARLIE, "Qx Charlie Generator"),
        GEN_DELTA: _generator(GEN_DELTA, "Qx Delta Generator"),
    }
)
RECIPES: Final[Mapping[str, Recipe]] = MappingProxyType(
    {R_FUEL: _recipe(R_FUEL, FUEL, REFINERY), R_TURBO: _recipe(R_TURBO, TURBO, MAKER)}
)
REGISTRY: Final = Registry(
    items=ITEMS,
    recipes=RECIPES,
    buildings=MappingProxyType({}),
    warnings=(),
    unknown_groups=(),
    extractors=MappingProxyType({}),
    generators=GENERATORS,
    declared_classes=frozenset({*ITEMS, *GENERATORS, *RECIPES, REFINERY, MAKER}),
)


# ---------------------------------------------------------------------------
# Hand-built audit results, the figures re-derived from the constants above
# ---------------------------------------------------------------------------


def _class(  # noqa: PLR0913 - one keyword per audit field an arm varies
    key: str,
    verdict: str,
    *,
    fuels: tuple[str, ...] | None = None,
    supply: Mapping[str, Fraction | None] | None = None,
    production_gap: bool = False,
    clocks: tuple[Fraction, ...] = (ONE, ONE),
    clock_known: bool = True,
    omitted: int = 0,
    elided: int = 0,
    reasons: tuple[str, ...] = (),
) -> tuple[FuelVerdict, FuelDemand]:
    """One class's verdict and demand, every figure re-derived here."""
    accepted = ACCEPTED[key] if fuels is None else fuels
    plate = None if production_gap else NAMEPLATES[key]
    clock_sum = sum(clocks, Fraction(0)) if clock_known else None
    demand = None
    if plate is not None and clock_sum is not None and not omitted:
        demand = plate * clock_sum
    supplies = supply or {}
    pooled: Fraction | None = Fraction(0) if accepted else None
    for fuel in accepted:
        energy, rate = MJ[fuel], supplies.get(fuel)
        if pooled is None or energy is None or rate is None:
            pooled = None
        else:
            pooled += rate * energy / SIXTY
    shortfall = None
    if verdict == VERDICT_FIRE and demand is not None and pooled is not None:
        shortfall = demand - pooled
    lines = []
    burns = []
    for fuel in accepted:
        energy, rate = MJ[fuel], supplies.get(fuel)
        lines.append(
            FuelLine(
                item_key=fuel,
                unit=UNITS[fuel],
                megajoules_per_unit=energy,
                supply_per_minute=rate,
                supply_megawatts=None if energy is None or rate is None else rate * energy / SIXTY,
                shortfall_per_minute=(
                    None if shortfall is None or energy is None else shortfall * SIXTY / energy
                ),
                reasons=(),
            )
        )
        burns.append(
            FuelBurn(
                item_key=fuel,
                unit=UNITS[fuel],
                megajoules_per_unit=energy,
                burn_per_minute=None
                if demand is None or energy is None
                else demand * SIXTY / energy,
            )
        )
    demand_reasons = tuple(reason for reason in DEMAND_REASONS if reason in reasons)
    verdict_record = FuelVerdict(
        class_name=key,
        verdict=verdict,
        reasons=reasons,
        accepted_fuels=accepted,
        headline_fuel=accepted[0] if accepted else None,
        instance_count=len(clocks),
        omitted_count=omitted,
        elided_clock_count=elided,
        nameplate_megawatts=plate,
        production_gap_kind=None,
        clock_sum=clock_sum,
        demand_megawatts=demand,
        fuels=tuple(lines),
        pooled_megawatts=pooled,
        shortfall_megawatts=shortfall,
        shared_with=(),
        trace=(),
    )
    demand_record = FuelDemand(
        class_name=key,
        accepted_fuels=accepted,
        headline_fuel=accepted[0] if accepted else None,
        instance_count=len(clocks),
        omitted_count=omitted,
        elided_clock_count=elided,
        nameplate_megawatts=plate,
        production_gap_kind=None,
        clock_sum=clock_sum,
        demand_megawatts=demand,
        burns=tuple(burns),
        reasons=demand_reasons,
        complete=not demand_reasons,
        trace=(),
    )
    return verdict_record, demand_record


#: The FIRE fixture: two Alpha generators at clock one demand 500 MW; ten
#: cubic metres of fuel a minute yield 125 MW and six of turbo 200 MW, so the
#: pooled 325 MW leaves 175 MW short - 14 m3 of fuel or 5.25 of turbo alone.
ALPHA_SUPPLY: Final[Mapping[str, Fraction | None]] = MappingProxyType(
    {FUEL: Fraction(10), TURBO: Fraction(6)}
)
ALPHA_DEMAND: Final = ALPHA_MW * 2
ALPHA_POOLED: Final = Fraction(10) * FUEL_MJ / SIXTY + Fraction(6) * TURBO_MJ / SIXTY
ALPHA_SHORTFALL: Final = ALPHA_DEMAND - ALPHA_POOLED

#: Forty cubic metres of fuel a minute yield exactly the 500 MW Alpha demands.
ALPHA_COVERED: Final[Mapping[str, Fraction | None]] = MappingProxyType(
    {FUEL: Fraction(40), TURBO: Fraction(0)}
)

#: Bravo, one generator at clock one: 150 MW against four cubic metres of bio
#: a minute, 100 MW, so 50 MW short - two cubic metres of bio a minute.
BRAVO_SUPPLY: Final[Mapping[str, Fraction | None]] = MappingProxyType({BIO: Fraction(4)})


def _alpha_fire(
    *,
    fuels: tuple[str, ...] | None = None,
    supply: Mapping[str, Fraction | None] = ALPHA_SUPPLY,
    elided: int = 0,
) -> tuple[FuelVerdict, FuelDemand]:
    return _class(GEN_ALPHA, VERDICT_FIRE, fuels=fuels, supply=supply, elided=elided)


def _bravo_fire(*, elided: int = 0) -> tuple[FuelVerdict, FuelDemand]:
    return _class(GEN_BRAVO, VERDICT_FIRE, supply=BRAVO_SUPPLY, clocks=(ONE,), elided=elided)


def _covered_reject() -> FuelVerdict:
    """Alpha's REJECT: forty cubic metres of fuel a minute meet its 500 MW exactly."""
    return _class(GEN_ALPHA, VERDICT_REJECT, supply=ALPHA_COVERED)[0]


def _world_fuel(*classes: tuple[FuelVerdict, FuelDemand]) -> WorldFuel:
    ordered = sorted(classes, key=lambda pair: pair[0].class_name)
    return WorldFuel(
        verdicts=tuple(verdict for verdict, _ in ordered),
        demands=tuple(demand for _, demand in ordered),
        out_of_scope=(),
        exclusions=EXCLUSIONS,
        flow_complete=True,
        no_fluid_record_count=0,
        unregistered_record_count=0,
    )


def _with_build(values: dict[str, InputValue], build: BuildInputs | None) -> WorldInputs:
    """Offer the fuel inputs beside one save's build inputs (CS-1288).

    ``build`` defaults to a save written by the pinned build itself, the pin
    read at test time. The two name sets are asserted disjoint, so the build
    inputs never overwrite a fuel input.
    """
    offered = pinned_build_inputs(game_pin()) if build is None else build
    overlap = sorted(set(values) & set(offered))
    assert overlap == []
    return WorldInputs(values={**values, **offered}, unlocks=frozenset())


def _inputs(
    world: WorldFuel, registry: Registry = REGISTRY, build: BuildInputs | None = None
) -> WorldInputs:
    return _with_build(fuel_inputs(world, registry), build)


def _run(spec: RuleSpec, *classes: tuple[FuelVerdict, FuelDemand]) -> Trace:
    return run_rule(spec, _inputs(_world_fuel(*classes)))


def _undecided(reason: str, key: str = GEN_ALPHA) -> tuple[FuelVerdict, FuelDemand]:
    """One INDETERMINATE class whose figures are consistent with ``reason``."""
    fuels: Mapping[str, tuple[str, ...]] = {
        REASON_FUELS_UNREAD: (),
        REASON_ENERGY_UNKNOWN: (DUD,),
        REASON_SOLID_SUPPLY_UNMODELLED: (COAL,),
    }
    return _class(
        key,
        VERDICT_INDETERMINATE,
        reasons=(reason,),
        fuels=fuels.get(reason),
        production_gap=reason == REASON_PRODUCTION_GAP,
        omitted=1 if reason == REASON_INSTANCES_OMITTED else 0,
        clock_known=reason not in UNREAD_CLOCK_REASONS,
    )


#: The reasons under which a class's clock sum is unknown.
UNREAD_CLOCK_REASONS: Final = frozenset(
    {REASON_BOOST_UNMODELED, REASON_CLOCK_UNREAD, REASON_CLOCK_REFUSED}
)


def _as_mapping(value: object) -> Mapping[str, object]:
    assert type(value) is MappingProxyType
    return value


def _at(value: object, *keys: str) -> object:
    """Walk an offered value down nested read-only mappings, one key per level."""
    for key in keys:
        value = _as_mapping(value)[key]
    return value


def _kinds(trace: Trace, kind: StepKind) -> list[TraceStep]:
    return [step for step in trace.steps if step.kind is kind]


def _subjects(trace: Trace, kind: StepKind) -> list[str]:
    return [step.subject for step in trace.steps if step.kind is kind]


def _computed(trace: Trace) -> dict[str, object]:
    return {step.subject: step.value for step in trace.steps if step.kind is StepKind.COMPUTED}


def _errors(trace: Trace) -> list[str]:
    return _subjects(trace, StepKind.RULE_ERROR)


# ---------------------------------------------------------------------------
# The adapter
# ---------------------------------------------------------------------------

#: Every input either rule declares and the fuel adapter offers - every
#: declared name but the three build inputs, which the build adapter offers.
DECLARED: Final = frozenset(
    name for spec in RULES for name in spec.inputs if name not in BUILD_INPUTS
)

#: The two inputs sourced to the registry rather than the audit (G4).
NAME_INPUTS: Final = frozenset({IN_CLASS_NAMES, IN_FUEL_NAMES})

#: The inputs that carry a supply figure - the demand rule declares none.
SUPPLY_FIGURES: Final = frozenset(
    {IN_SUPPLY, IN_SUPPLY_MW, IN_POOLED, IN_SHORTFALL, IN_SHORTFALL_RATES}
)


def _mixed_world() -> WorldFuel:
    return _world_fuel(_alpha_fire(), _undecided(REASON_PRODUCTION_GAP, GEN_BRAVO))


def test_the_adapter_offers_every_declared_input_sourced_to_the_fuel_audit() -> None:
    values = fuel_inputs(_mixed_world(), REGISTRY)

    offered = sorted(values)
    assert offered == sorted(DECLARED)
    for name, value in values.items():
        expected = "registry." if name in NAME_INPUTS else "audit.fuel."
        assert value.source.startswith(expected), name
    assert values[IN_CLASS_NAMES].source == "registry.generators.display_name"
    assert values[IN_FUEL_NAMES].source == "registry.items.display_name"


def _probe_every_input(world: WorldInputs) -> Trace:
    names = tuple(sorted(DECLARED))

    def _read_all(ctx: RuleContext) -> Recommendation | None:
        for name in names:
            ctx.read(name)
        return None

    probe = RuleSpec(
        rule_id="test.fuel_probe", domain="test", inputs=names, unlocks=(), evaluate=_read_all
    )
    return run_rule(probe, world)


def test_every_offered_value_passes_the_exactness_walk() -> None:
    trace = _probe_every_input(_inputs(_mixed_world()))

    assert trace.refused == ()
    assert _errors(trace) == []
    read = sorted(_subjects(trace, StepKind.INPUT_READ))
    assert read == sorted(DECLARED)


def test_an_unknown_figure_is_offered_as_none_never_zero() -> None:
    values = fuel_inputs(_mixed_world(), REGISTRY)

    nameplate = _at(values[IN_NAMEPLATE].value, GEN_BRAVO)
    demand = _at(values[IN_DEMAND].value, GEN_BRAVO)
    burn = _at(values[IN_BURNS].value, GEN_BRAVO, BIO)
    pooled = _at(values[IN_POOLED].value, GEN_BRAVO)
    assert nameplate is None
    assert demand is None
    assert burn is None
    assert pooled is None
    assert _at(values[IN_DEMAND].value, GEN_ALPHA) == ALPHA_DEMAND


def test_the_adapter_offers_the_registry_display_names_verbatim() -> None:
    values = fuel_inputs(_mixed_world(), REGISTRY)

    assert values[IN_CLASS_NAMES].value == MappingProxyType(
        {GEN_ALPHA: ALPHA_NAME, GEN_BRAVO: BRAVO_NAME}
    )
    assert values[IN_FUEL_NAMES].value == MappingProxyType(
        {FUEL: FUEL_NAME, TURBO: TURBO_NAME, BIO: BIO_NAME}
    )


def test_fuel_inputs_never_collide_with_power_inputs() -> None:
    power_names = {value for name, value in vars(power_rules).items() if name.startswith("IN_")} | {
        name for spec in power_rules.RULES for name in spec.inputs
    }
    offered = set(fuel_inputs(_mixed_world(), REGISTRY))

    assert power_names
    assert offered
    assert sorted(offered & power_names) == []
    assert all(name.startswith("power.fuel.") for name in offered | DECLARED)
    assert not any(name.startswith("power.fuel.") for name in power_names)


# ---------------------------------------------------------------------------
# The end-to-end arm: a real fuel_supply_of result, builder pattern copied
# from tests/audit/test_fuel.py
# ---------------------------------------------------------------------------


def _gen(class_name: str, *, clock: Fraction | None = ONE, elided: bool = False) -> MachineState:
    """One generator; ``clock=None`` is an unread clock, ``elided`` the elided default."""
    return MachineState(
        class_name=class_name,
        producing=True,
        recipe_class_name=None,
        overclock=None if elided else clock,
        overclock_elided=elided,
        production_boost_tagged=False,
    )


def _maker(class_name: str, recipe: str) -> MachineState:
    return MachineState(
        class_name=class_name, producing=True, recipe_class_name=recipe, overclock=ONE
    )


def _machines(
    states: list[MachineState], *, unadmitted: tuple[tuple[str, int], ...] = ()
) -> WorldMachines:
    """The machines model; ``unadmitted`` is the census of built records never admitted."""
    return WorldMachines(
        machines=tuple(states),
        producing_available=True,
        recipe_available=True,
        overclock_available=True,
        records_considered=len(states),
        unread_payload_count=0,
        refused_overclock_count=0,
        refused_recipe_count=0,
        warnings=(),
        unadmitted_read_counts=unadmitted,
        unadmitted_unread_counts=(),
    )


def _real_fire() -> WorldFuel:
    """Two Alpha generators, one fuel refinery and one turbo maker: short."""
    states = [
        _gen(GEN_ALPHA),
        _gen(GEN_ALPHA),
        _maker(REFINERY, R_FUEL),
        _maker(MAKER, R_TURBO),
    ]
    return fuel_supply_of(_machines(states), REGISTRY)


def _real_undecided() -> WorldFuel:
    """Two Alpha generators and no recipe machine: the flow is incomplete."""
    return fuel_supply_of(_machines([_gen(GEN_ALPHA), _gen(GEN_ALPHA)]), REGISTRY)


def test_the_adapter_over_a_real_audit_carries_its_figures() -> None:
    world = _real_fire()
    verdict = world.verdicts[0]
    assert verdict.verdict == VERDICT_FIRE, "the end-to-end fixture no longer fires"
    values = fuel_inputs(world, REGISTRY)

    def offered(name: str, *fuel: str) -> object:
        return _at(values[name].value, GEN_ALPHA, *fuel)

    assert offered(IN_DEMAND) == verdict.demand_megawatts
    assert offered(IN_NAMEPLATE) == verdict.nameplate_megawatts
    assert offered(IN_CLOCK_SUM) == verdict.clock_sum
    assert offered(IN_POOLED) == verdict.pooled_megawatts
    assert offered(IN_SHORTFALL) == verdict.shortfall_megawatts
    assert offered(IN_OMITTED) == verdict.omitted_count
    for line in verdict.fuels:
        assert offered(IN_SUPPLY, line.item_key) == line.supply_per_minute
        assert offered(IN_SUPPLY_MW, line.item_key) == line.supply_megawatts
        assert offered(IN_SHORTFALL_RATES, line.item_key) == line.shortfall_per_minute
        assert _at(values[IN_MJ].value, line.item_key) == line.megajoules_per_unit
    for burn in world.demands[0].burns:
        assert offered(IN_BURNS, burn.item_key) == burn.burn_per_minute


def test_the_supply_rule_over_a_real_audit_states_every_shortfall_rate() -> None:
    world = _real_fire()
    verdict = world.verdicts[0]
    trace = run_rule(SUPPLY_RULE, _inputs(world))

    card = card_for(trace)
    assert card is not None
    computed = _computed(trace)
    shortfall = computed[f"shortfall MW of {GEN_ALPHA}, demand less pooled supply"]
    assert shortfall == verdict.shortfall_megawatts
    for line in verdict.fuels:
        label = f"shortfall per minute of {line.item_key} alone for {GEN_ALPHA}"
        assert computed[label] == line.shortfall_per_minute
        assert label in card.tier3


def test_the_demand_rule_over_a_real_audit_states_every_burn() -> None:
    world = _real_undecided()
    assert world.verdicts[0].verdict == VERDICT_INDETERMINATE
    trace = run_rule(DEMAND_RULE, _inputs(world))

    card = card_for(trace)
    assert card is not None
    computed = _computed(trace)
    burns = world.demands[0].burns
    assert len(burns) == len(ACCEPTED[GEN_ALPHA])
    for burn in burns:
        label = f"burn per minute of {burn.item_key} for {GEN_ALPHA}"
        assert computed[label] == burn.burn_per_minute
        assert burn.burn_per_minute is not None


# ---------------------------------------------------------------------------
# G3: every stated figure is recomputed and compared with the audit's own
# ---------------------------------------------------------------------------


def _swap_fuels(value: object) -> object:
    """Swap the figures of the first two fuels of a mapping keyed by fuel."""
    entries = dict(_as_mapping(value))
    first, second = sorted(entries)[:2]
    entries[first], entries[second] = entries[second], entries[first]
    return MappingProxyType(entries)


def _per_class(change: Callable[[object], object]) -> Callable[[object], object]:
    """Apply ``change`` to Alpha's entry of a mapping keyed by class."""

    def _apply(value: object) -> object:
        entries = dict(_as_mapping(value))
        entries[GEN_ALPHA] = change(entries[GEN_ALPHA])
        return MappingProxyType(entries)

    return _apply


def _bump(value: object) -> object:
    assert type(value) is Fraction
    return value + ONE


def _tampered(world: WorldFuel, name: str, change: Callable[[object], object]) -> WorldInputs:
    values = fuel_inputs(world, REGISTRY)
    offered = values[name]
    values[name] = InputValue(change(offered.value), offered.source)
    return _with_build(values, None)


SUPPLY_TAMPERS: Final = (
    ("mis-paired-energy", IN_MJ, _swap_fuels),
    ("mis-paired-supply", IN_SUPPLY, _per_class(_swap_fuels)),
    ("mis-paired-supply-mw", IN_SUPPLY_MW, _per_class(_swap_fuels)),
    ("mis-paired-rate", IN_SHORTFALL_RATES, _per_class(_swap_fuels)),
    ("demand-off", IN_DEMAND, _per_class(_bump)),
    ("nameplate-off", IN_NAMEPLATE, _per_class(_bump)),
    ("clock-sum-off", IN_CLOCK_SUM, _per_class(_bump)),
    ("pooled-off", IN_POOLED, _per_class(_bump)),
    ("shortfall-off", IN_SHORTFALL, _per_class(_bump)),
)


@pytest.mark.parametrize(
    ("name", "change"),
    [(name, change) for _, name, change in SUPPLY_TAMPERS],
    ids=[label for label, _, _ in SUPPLY_TAMPERS],
)
def test_a_supply_figure_that_disagrees_with_the_audit_is_a_rule_error(
    name: str, change: Callable[[object], object]
) -> None:
    world = _world_fuel(_alpha_fire())
    clean = run_rule(SUPPLY_RULE, _inputs(world))
    assert clean.recommendation is not None, "the untampered control does not fire"

    trace = run_rule(SUPPLY_RULE, _tampered(world, name, change))

    assert trace.recommendation is None
    assert len(_errors(trace)) == 1


DEMAND_TAMPERS: Final = (
    ("mis-paired-energy", IN_MJ, _swap_fuels),
    ("mis-paired-burn", IN_BURNS, _per_class(_swap_fuels)),
    ("demand-off", IN_DEMAND, _per_class(_bump)),
    ("nameplate-off", IN_NAMEPLATE, _per_class(_bump)),
)


@pytest.mark.parametrize(
    ("name", "change"),
    [(name, change) for _, name, change in DEMAND_TAMPERS],
    ids=[label for label, _, _ in DEMAND_TAMPERS],
)
def test_a_demand_figure_that_disagrees_with_the_audit_is_a_rule_error(
    name: str, change: Callable[[object], object]
) -> None:
    world = _world_fuel(_undecided(REASON_FLOW_INCOMPLETE))
    clean = run_rule(DEMAND_RULE, _inputs(world))
    assert clean.recommendation is not None, "the untampered control does not fire"

    trace = run_rule(DEMAND_RULE, _tampered(world, name, change))

    assert trace.recommendation is None
    assert len(_errors(trace)) == 1


# ---------------------------------------------------------------------------
# power.fuel_supply
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("spec", RULES, ids=lambda spec: spec.rule_id)
def test_rule_declares_every_input_it_reads_and_no_unlock(spec: RuleSpec) -> None:
    worlds = (
        _world_fuel(_alpha_fire()),
        _world_fuel(_class(GEN_ALPHA, VERDICT_REJECT, supply=ALPHA_COVERED)),
        _world_fuel(_undecided(REASON_FLOW_INCOMPLETE)),
    )
    traces = [run_rule(spec, _inputs(world)) for world in worlds]

    assert spec.unlocks == ()
    assert any(trace.recommendation is not None for trace in traces)
    for trace in traces:
        assert trace.refused == ()
        assert _errors(trace) == []
        read = sorted(set(_subjects(trace, StepKind.INPUT_READ)))
        assert read == sorted(spec.inputs)


def test_the_rules_are_in_rule_id_order() -> None:
    ids = [spec.rule_id for spec in RULES]
    assert ids == sorted([SUPPLY_ID, DEMAND_ID])
    assert SUPPLY_RULE.rule_id == SUPPLY_ID
    assert DEMAND_RULE.rule_id == DEMAND_ID
    assert {spec.domain for spec in RULES} == {"power"}


def test_the_supply_rule_fires_with_the_exact_shortfall() -> None:
    trace = _run(SUPPLY_RULE, _alpha_fire())

    assert trace.recommendation is not None
    computed = _computed(trace)
    assert computed[f"demand MW of {GEN_ALPHA}, nameplate times clock sum"] == ALPHA_DEMAND
    assert computed[f"pooled supply MW of {GEN_ALPHA}"] == ALPHA_POOLED
    shortfall = computed[f"shortfall MW of {GEN_ALPHA}, demand less pooled supply"]
    assert shortfall == ALPHA_SHORTFALL
    assert type(shortfall) is Fraction


def test_tier3_converts_the_shortfall_into_a_rate_for_every_accepted_fuel() -> None:
    verdict, demand = _alpha_fire()
    trace = _run(SUPPLY_RULE, (verdict, demand))
    card = card_for(trace)

    assert card is not None
    computed = _computed(trace)
    assert len(verdict.fuels) == len(ACCEPTED[GEN_ALPHA])
    for line in verdict.fuels:
        label = f"shortfall per minute of {line.item_key} alone for {GEN_ALPHA}"
        energy = MJ[line.item_key]
        assert energy is not None
        assert computed[label] == ALPHA_SHORTFALL * SIXTY / energy
        assert computed[label] == line.shortfall_per_minute
        assert label in card.tier3


@pytest.mark.parametrize(
    ("order", "headline"),
    [
        ((FUEL, TURBO), "Supply 14.00 m3 more Qx Fuel per minute to Qx Alpha Generator x2"),
        ((TURBO, FUEL), "Supply 5.25 m3 more Qx Turbo per minute to Qx Alpha Generator x2"),
    ],
    ids=["fuel-first", "turbo-first"],
)
def test_the_headline_fuel_is_the_first_in_mfuel_order(
    order: tuple[str, ...], headline: str
) -> None:
    card = card_for(_run(SUPPLY_RULE, _alpha_fire(fuels=order)))

    assert card is not None
    assert card.tier1 == headline


SUPPLY_REASON = (
    "Qx Alpha Generator x2 demand 500.00 MW but the pooled supply of every accepted fuel"
    " yields 325.00 MW: 175.00 MW short, which is 14.00 m3 of Qx Fuel per minute alone"
)


def test_tiers_1_and_2_name_fuel_figure_and_generator_count() -> None:
    card = card_for(_run(SUPPLY_RULE, _alpha_fire()))

    assert card is not None
    assert card.tier1 == "Supply 14.00 m3 more Qx Fuel per minute to Qx Alpha Generator x2"
    assert card.tier2 == SUPPLY_REASON
    for tier in (card.tier1, card.tier2):
        assert FUEL_NAME in tier
        assert "14.00" in tier
        assert "x2" in tier


def test_a_reject_is_silent_and_settled() -> None:
    trace = _run(SUPPLY_RULE, _class(GEN_ALPHA, VERDICT_REJECT, supply=ALPHA_COVERED))

    assert trace.recommendation is None
    assert _errors(trace) == []
    rejected = [
        (step.subject, step.reason)
        for step in trace.steps
        if step.kind is StepKind.ALTERNATIVE_REJECTED
    ]
    assert rejected == [
        (f"add fuel supply for {GEN_ALPHA}", "pooled supply covers demand over a complete flow")
    ]
    headroom = _computed(trace)[f"headroom MW of {GEN_ALPHA}, pooled supply less demand"]
    assert headroom == Fraction(0)
    assert type(headroom) is Fraction
    assert SUPPLY_ID in settled_rules((trace,))


@pytest.mark.parametrize("reason", INDETERMINATE_REASONS)
def test_an_indeterminate_class_gets_no_sized_card_and_never_settles(reason: str) -> None:
    trace = _run(SUPPLY_RULE, _undecided(reason))

    assert trace.recommendation is None
    assert _errors(trace) == []
    undecided = [
        (step.subject, step.reason)
        for step in trace.steps
        if step.kind is StepKind.VERDICT_INDETERMINATE
    ]
    assert undecided == [
        (
            f"compare the pooled fuel supply against the demand of {GEN_ALPHA}",
            REASON_DETAIL[reason],
        )
    ]
    assert SUPPLY_ID not in settled_rules((trace,))


def test_supply_input_uncovered_is_among_the_parametrized_reasons() -> None:
    assert REASON_SUPPLY_INPUT_UNCOVERED in INDETERMINATE_REASONS


def test_every_reason_of_an_indeterminate_class_is_named() -> None:
    reasons = (REASON_FLOW_INCOMPLETE, REASON_SUPPLY_UNMEASURED)
    trace = _run(SUPPLY_RULE, _class(GEN_ALPHA, VERDICT_INDETERMINATE, reasons=reasons))

    undecided = [s.reason for s in trace.steps if s.kind is StepKind.VERDICT_INDETERMINATE]
    assert undecided == ["; ".join(REASON_DETAIL[reason] for reason in reasons)]


def test_a_fire_beside_an_indeterminate_class_fires_but_is_not_settled() -> None:
    trace = _run(SUPPLY_RULE, _alpha_fire(), _undecided(REASON_SUPPLY_UNMEASURED, GEN_BRAVO))

    card = card_for(trace)
    assert card is not None
    assert card.subject_key == f"power:fuel-supply:{GEN_ALPHA}"
    assert _subjects(trace, StepKind.VERDICT_INDETERMINATE) == [
        f"compare the pooled fuel supply against the demand of {GEN_BRAVO}"
    ]
    assert SUPPLY_ID not in settled_rules((trace,))


@pytest.mark.parametrize("spec", RULES, ids=lambda spec: spec.rule_id)
def test_no_built_fuel_class_is_silent_and_settled(spec: RuleSpec) -> None:
    trace = run_rule(spec, _inputs(_world_fuel()))

    assert trace.recommendation is None
    assert _errors(trace) == []
    reasons = [s.reason for s in trace.steps if s.kind is StepKind.ALTERNATIVE_REJECTED]
    assert reasons == ["no built fuel generator class"]
    assert spec.rule_id in settled_rules((trace,))


def test_several_fire_classes_headline_the_first_by_key_under_the_sorted_set() -> None:
    trace = _run(SUPPLY_RULE, _bravo_fire(), _alpha_fire())
    card = card_for(trace)

    assert card is not None
    assert card.subject_key == f"power:fuel-supply:{GEN_ALPHA},{GEN_BRAVO}"
    assert card.tier1 == "Supply 14.00 m3 more Qx Fuel per minute to Qx Alpha Generator x2"
    assert card.tier2 == SUPPLY_REASON + "; 1 other generator class is short too"
    computed = _computed(trace)
    assert computed[f"shortfall MW of {GEN_BRAVO}, demand less pooled supply"] == Fraction(50)
    assert computed[f"shortfall per minute of {BIO} alone for {GEN_BRAVO}"] == Fraction(2)
    assert GEN_BRAVO in card.tier3


def test_the_card_id_is_stable_when_figures_move_and_moves_with_the_class_set() -> None:
    first = card_for(_run(SUPPLY_RULE, _alpha_fire()))
    moved = card_for(_run(SUPPLY_RULE, _alpha_fire(supply={FUEL: Fraction(11), TURBO: ONE})))
    wider = card_for(_run(SUPPLY_RULE, _alpha_fire(), _bravo_fire()))

    assert first is not None
    assert moved is not None
    assert wider is not None
    assert moved.tier1 != first.tier1
    assert moved.id == first.id
    assert first.id == card_id(SUPPLY_ID, f"power:fuel-supply:{GEN_ALPHA}", None)
    assert wider.id != first.id
    assert wider.id == card_id(SUPPLY_ID, f"power:fuel-supply:{GEN_ALPHA},{GEN_BRAVO}", None)


@pytest.mark.parametrize("spec", RULES, ids=lambda spec: spec.rule_id)
def test_tier3_names_supplemental_resources_and_byproducts_as_out_of_scope(
    spec: RuleSpec,
) -> None:
    world = _alpha_fire() if spec is SUPPLY_RULE else _undecided(REASON_FLOW_INCOMPLETE)
    card = card_for(_run(spec, world))

    assert card is not None
    assert (
        "Rejected size supplemental resources and byproducts: out of scope:"
        " supplemental resources such as water are not compared against any supply;"
        " byproducts a generator emits are not modelled"
    ) in card.tier3


@pytest.mark.parametrize(
    "verdict",
    [
        # A FIRE whose pooled supply covers the demand: no positive shortfall.
        _alpha_fire(supply=ALPHA_COVERED)[0],
        # A FIRE whose own shortfall figure disagrees with the recomputation.
        replace(_alpha_fire()[0], shortfall_megawatts=ONE),
        # A FIRE carrying an indeterminate reason.
        replace(_alpha_fire()[0], reasons=(REASON_FLOW_INCOMPLETE,)),
        # A REJECT whose pooled supply falls short of the demand, carrying no
        # stray shortfall figure, so only the headroom check can catch it.
        _class(GEN_ALPHA, VERDICT_REJECT, supply=ALPHA_SUPPLY)[0],
        # A covered REJECT that still carries a shortfall figure.
        replace(_covered_reject(), shortfall_megawatts=ONE),
        # A covered REJECT one of whose fuels still carries a shortfall rate.
        replace(
            _covered_reject(),
            fuels=(
                replace(_covered_reject().fuels[0], shortfall_per_minute=ONE),
                *_covered_reject().fuels[1:],
            ),
        ),
        # A FIRE or REJECT with built generators the save never read: its
        # demand would be a floor, which the audit never decides on.
        replace(_alpha_fire()[0], omitted_count=1),
        replace(_covered_reject(), omitted_count=1),
        # A FIRE resting on a NEGATIVE supply - the audit floors supply at zero.
        _alpha_fire(supply=MappingProxyType({FUEL: Fraction(-10), TURBO: Fraction(6)}))[0],
        # A REJECT resting on a negative supply, covered by the other fuel.
        _class(
            GEN_ALPHA,
            VERDICT_REJECT,
            supply=MappingProxyType({FUEL: Fraction(-10), TURBO: Fraction(30)}),
        )[0],
    ],
    ids=[
        "fire-covered",
        "fire-figure-off",
        "fire-with-reason",
        "reject-short",
        "reject-stray-shortfall",
        "reject-stray-rate",
        "fire-unread-generators",
        "reject-unread-generators",
        "fire-negative-supply",
        "reject-negative-supply",
    ],
)
def test_an_inconsistent_verdict_is_a_rule_error(verdict: FuelVerdict) -> None:
    _, demand = _alpha_fire()
    trace = _run(SUPPLY_RULE, (verdict, demand))

    assert trace.recommendation is None
    assert len(_errors(trace)) == 1


@pytest.mark.parametrize("spec", RULES, ids=lambda spec: spec.rule_id)
def test_an_unknown_verdict_word_is_a_rule_error(spec: RuleSpec) -> None:
    verdict, demand = _undecided(REASON_FLOW_INCOMPLETE)
    trace = _run(spec, (replace(verdict, verdict="qx-maybe"), demand))

    assert trace.recommendation is None
    assert len(_errors(trace)) == 1


def test_a_shortfall_below_float_resolution_still_fires_exactly() -> None:
    epsilon = Fraction(1, 10**30)
    energy = MJ[BIO]
    assert energy is not None
    supply = (BRAVO_MW - epsilon) * SIXTY / energy
    pair = _class(GEN_BRAVO, VERDICT_FIRE, supply={BIO: supply}, clocks=(ONE,))
    pooled = pair[0].pooled_megawatts
    assert pooled is not None
    assert float(pooled) == float(BRAVO_MW), "the fixture is not below float resolution"

    trace = _run(SUPPLY_RULE, pair)

    assert trace.recommendation is not None
    computed = _computed(trace)
    assert computed[f"shortfall MW of {GEN_BRAVO}, demand less pooled supply"] == epsilon
    assert computed[f"shortfall per minute of {BIO} alone for {GEN_BRAVO}"] == (
        epsilon * SIXTY / energy
    )


@pytest.mark.parametrize(
    ("elided", "words"),
    [
        (1, "; it assumes the default clock for 1 generator whose save omits the clock tag"),
        (2, "; it assumes the default clock for 2 generators whose save omits the clock tag"),
    ],
)
def test_an_elided_clock_is_named_in_the_reason(elided: int, words: str) -> None:
    supply_card = card_for(_run(SUPPLY_RULE, _alpha_fire(elided=elided)))
    demand_card = card_for(
        _run(
            DEMAND_RULE,
            _class(
                GEN_ALPHA,
                VERDICT_INDETERMINATE,
                reasons=(REASON_FLOW_INCOMPLETE,),
                elided=elided,
            ),
        )
    )

    assert supply_card is not None
    assert demand_card is not None
    assert supply_card.tier2 == SUPPLY_REASON + words
    assert demand_card.tier2.endswith(words)


def test_no_elided_clock_names_no_default_clock() -> None:
    card = card_for(_run(SUPPLY_RULE, _alpha_fire()))

    assert card is not None
    assert "default clock" not in card.tier2


def _renamed(generator: str | None = None, fuel: str | None = None) -> Registry:
    generators = dict(GENERATORS)
    items = dict(ITEMS)
    if generator is not None:
        generators[GEN_ALPHA] = replace(GENERATORS[GEN_ALPHA], display_name=generator)
    if fuel is not None:
        items[FUEL] = replace(ITEMS[FUEL], display_name=fuel)
    return replace(REGISTRY, generators=MappingProxyType(generators), items=MappingProxyType(items))


FALLBACK_REASON: Final = (
    "the display name is empty, blank or not printable ASCII text, so the key names it"
)


@pytest.mark.parametrize(
    ("registry", "headline", "fallback"),
    [
        (
            _renamed(generator=""),
            f"Supply 14.00 m3 more Qx Fuel per minute to {GEN_ALPHA} x2",
            GEN_ALPHA,
        ),
        (
            _renamed(generator="   "),
            f"Supply 14.00 m3 more Qx Fuel per minute to {GEN_ALPHA} x2",
            GEN_ALPHA,
        ),
        (
            _renamed(fuel="Qx Fu\u00e9l"),
            f"Supply 14.00 m3 more {FUEL} per minute to Qx Alpha Generator x2",
            FUEL,
        ),
        (
            _renamed(fuel=" "),
            f"Supply 14.00 m3 more {FUEL} per minute to Qx Alpha Generator x2",
            FUEL,
        ),
    ],
    ids=["empty-class-name", "blank-class-name", "non-ascii-fuel-name", "blank-fuel-name"],
)
def test_a_display_name_that_is_not_text_falls_back_to_the_key_on_record(
    registry: Registry, headline: str, fallback: str
) -> None:
    trace = run_rule(SUPPLY_RULE, _inputs(_world_fuel(_alpha_fire()), registry))
    card = card_for(trace)

    assert card is not None
    assert card.tier1 == headline
    rejected = [
        (step.subject, step.reason)
        for step in trace.steps
        if step.kind is StepKind.ALTERNATIVE_REJECTED
    ]
    assert (f"name {fallback} by its display name", FALLBACK_REASON) in rejected
    assert SUPPLY_ID in settled_rules((trace,))


def expected_supply_tier3(pin: int) -> str:
    """The whole on-pin derivation of Alpha's supply card, the pin read at test time.

    The docs hash is :func:`docs_pin` read at test time too (CS-1315), never
    typed: steps 4 to 6 are the registry check's three reads.
    """
    docs = docs_pin()
    return "\n".join(
        [
            "Derivation of rule power.fuel_supply (domain power)",
            "Advice: Supply 14.00 m3 more Qx Fuel per minute to Qx Alpha Generator x2",
            "Because: " + SUPPLY_REASON,
            "Target milestone: none",
            "Steps:",
            f"  1. Read build.save_changelist = {pin} from audit.build.save_changelist",
            f"  2. Read build.pinned_changelist = {pin} from audit.build.pinned_changelist",
            "  3. Read build.warnings = {} from audit.build.warnings",
            f'  4. Read build.registry_sha256 = "{docs}" from audit.build.registry.source_sha256',
            f'  5. Read build.pinned_docs_sha256 = "{docs}" from'
            " audit.build.registry.pinned_sha256",
            "  6. Read build.registry_warnings = {} from audit.build.registry.warnings",
            '  7. Read power.fuel.classes = ("Build_QxAlphaGen_C") from'
            " audit.fuel.verdicts.class_name",
            '  8. Read power.fuel.verdicts = {"Build_QxAlphaGen_C": "fire"} from'
            " audit.fuel.verdicts.verdict",
            '  9. Read power.fuel.reasons = {"Build_QxAlphaGen_C": ()} from'
            " audit.fuel.verdicts.reasons",
            "  10. Read power.fuel.reason_details = {} from audit.fuel.REASON_DETAIL",
            '  11. Read power.fuel.instance_counts = {"Build_QxAlphaGen_C": 2} from'
            " audit.fuel.verdicts.instance_count",
            '  12. Read power.fuel.omitted_counts = {"Build_QxAlphaGen_C": 0} from'
            " audit.fuel.verdicts.omitted_count",
            '  13. Read power.fuel.elided_clock_counts = {"Build_QxAlphaGen_C": 0} from'
            " audit.fuel.verdicts.elided_clock_count",
            '  14. Read power.fuel.nameplate_mw = {"Build_QxAlphaGen_C": 250.00} from'
            " audit.fuel.verdicts.nameplate_megawatts",
            '  15. Read power.fuel.clock_sum = {"Build_QxAlphaGen_C": 2.00} from'
            " audit.fuel.verdicts.clock_sum",
            '  16. Read power.fuel.demand_mw = {"Build_QxAlphaGen_C": 500.00} from'
            " audit.fuel.verdicts.demand_megawatts",
            '  17. Read power.fuel.accepted_fuels = {"Build_QxAlphaGen_C":'
            ' ("Desc_QxFuel_C", "Desc_QxTurbo_C")} from audit.fuel.verdicts.accepted_fuels',
            '  18. Read power.fuel.mj_per_unit = {"Desc_QxFuel_C": 750.00,'
            ' "Desc_QxTurbo_C": 2000.00} from audit.fuel.verdicts.fuels.megajoules_per_unit',
            '  19. Read power.fuel.units = {"Desc_QxFuel_C": "m3", "Desc_QxTurbo_C": "m3"} from'
            " audit.fuel.verdicts.fuels.unit",
            '  20. Read power.fuel.supply_per_minute = {"Build_QxAlphaGen_C":'
            ' {"Desc_QxFuel_C": 10.00, "Desc_QxTurbo_C": 6.00}} from'
            " audit.fuel.verdicts.fuels.supply_per_minute",
            '  21. Read power.fuel.supply_mw = {"Build_QxAlphaGen_C":'
            ' {"Desc_QxFuel_C": 125.00, "Desc_QxTurbo_C": 200.00}} from'
            " audit.fuel.verdicts.fuels.supply_megawatts",
            '  22. Read power.fuel.pooled_mw = {"Build_QxAlphaGen_C": 325.00} from'
            " audit.fuel.verdicts.pooled_megawatts",
            '  23. Read power.fuel.shortfall_mw = {"Build_QxAlphaGen_C": 175.00} from'
            " audit.fuel.verdicts.shortfall_megawatts",
            '  24. Read power.fuel.shortfall_rates = {"Build_QxAlphaGen_C":'
            ' {"Desc_QxFuel_C": 14.00, "Desc_QxTurbo_C": 5.25}} from'
            " audit.fuel.verdicts.fuels.shortfall_per_minute",
            '  25. Read power.fuel.exclusions = ("supplemental resources such as water are not'
            ' compared against any supply", "byproducts a generator emits are not modelled")'
            " from audit.fuel.exclusions",
            '  26. Read power.fuel.class_names = {"Build_QxAlphaGen_C": "Qx Alpha Generator"} from'
            " registry.generators.display_name",
            '  27. Read power.fuel.fuel_names = {"Desc_QxFuel_C": "Qx Fuel",'
            ' "Desc_QxTurbo_C": "Qx Turbo"} from registry.items.display_name',
            "  28. Computed demand MW of Build_QxAlphaGen_C, nameplate times clock sum = 500.00",
            "  29. Computed supply MW of Desc_QxFuel_C for Build_QxAlphaGen_C,"
            " supply times MJ over sixty = 125.00",
            "  30. Computed supply MW of Desc_QxTurbo_C for Build_QxAlphaGen_C,"
            " supply times MJ over sixty = 200.00",
            "  31. Computed pooled supply MW of Build_QxAlphaGen_C = 325.00",
            "  32. Computed shortfall MW of Build_QxAlphaGen_C, demand less pooled supply = 175.00",
            "  33. Computed shortfall per minute of Desc_QxFuel_C alone for"
            " Build_QxAlphaGen_C = 14.00",
            "  34. Computed shortfall per minute of Desc_QxTurbo_C alone for"
            " Build_QxAlphaGen_C = 5.25",
            "  35. Rejected size supplemental resources and byproducts: out of scope:"
            " supplemental resources such as water are not compared against any supply;"
            " byproducts a generator emits are not modelled",
            "  36. Rule power.fuel_supply fired for power:fuel-supply:Build_QxAlphaGen_C",
        ]
    )


def test_supply_tier3_snapshot_shows_the_whole_derivation() -> None:
    card = card_for(_run(SUPPLY_RULE, _alpha_fire()))

    assert card is not None
    assert card.tier3 == expected_supply_tier3(game_pin())


# ---------------------------------------------------------------------------
# power.fuel_demand
# ---------------------------------------------------------------------------


def test_the_demand_rule_reads_no_supply_input() -> None:
    trace = _run(DEMAND_RULE, _undecided(REASON_FLOW_INCOMPLETE))

    declared = sorted(set(DEMAND_RULE.inputs) & SUPPLY_FIGURES)
    read = sorted(set(_subjects(trace, StepKind.INPUT_READ)) & SUPPLY_FIGURES)
    assert declared == []
    assert read == []
    assert sorted(SUPPLY_FIGURES - set(SUPPLY_RULE.inputs)) == []


@pytest.mark.parametrize("reason", INDETERMINATE_REASONS)
def test_the_demand_card_fires_on_every_indeterminate_reason(reason: str) -> None:
    trace = _run(DEMAND_RULE, _undecided(reason))
    card = card_for(trace)

    assert card is not None
    assert _errors(trace) == []
    assert card.subject_key == f"power:fuel-demand:{GEN_ALPHA}"
    rejected = [
        (step.subject, step.reason)
        for step in trace.steps
        if step.kind is StepKind.ALTERNATIVE_REJECTED
    ]
    assert (f"state a supply verdict for {GEN_ALPHA}", REASON_DETAIL[reason]) in rejected
    burn_unknown = reason in DEMAND_REASONS
    undecided = _kinds(trace, StepKind.VERDICT_INDETERMINATE)
    assert bool(undecided) is burn_unknown
    if burn_unknown:
        # The omitted fixture builds a third generator the save never read.
        built = "x3 (1 never read)" if reason == REASON_INSTANCES_OMITTED else "x2"
        assert card.tier1 == (
            f"Resolve the fuel burn of Qx Alpha Generator {built} before planning its fuel"
        )
    else:
        assert card.tier1.startswith("Plan ")
    assert (DEMAND_ID in settled_rules((trace,))) is not burn_unknown


def test_the_demand_card_states_each_burn_per_accepted_fuel() -> None:
    verdict, demand = _undecided(REASON_FLOW_INCOMPLETE)
    trace = _run(DEMAND_RULE, (verdict, demand))
    card = card_for(trace)

    assert card is not None
    computed = _computed(trace)
    assert len(demand.burns) == len(ACCEPTED[GEN_ALPHA])
    for burn in demand.burns:
        energy = MJ[burn.item_key]
        assert energy is not None
        label = f"burn per minute of {burn.item_key} for {GEN_ALPHA}"
        assert computed[label] == ALPHA_DEMAND * SIXTY / energy
        assert computed[label] == burn.burn_per_minute
    assert card.tier1 == "Plan 40.00 m3 of Qx Fuel per minute for Qx Alpha Generator x2"


def test_the_demand_card_never_fires_where_the_supply_rule_decides_every_class() -> None:
    reject = _class(GEN_BRAVO, VERDICT_REJECT, supply={BIO: Fraction(9)}, clocks=(ONE,))
    trace = _run(DEMAND_RULE, _alpha_fire(), reject)

    assert trace.recommendation is None
    assert _errors(trace) == []
    reasons = [s.reason for s in trace.steps if s.kind is StepKind.ALTERNATIVE_REJECTED]
    assert reasons == ["the supply rule decides every built fuel generator class"]
    assert DEMAND_ID in settled_rules((trace,))


def test_the_demand_card_covers_only_the_undecided_classes() -> None:
    reject = _class(GEN_ALPHA, VERDICT_REJECT, supply=ALPHA_COVERED)
    trace = _run(DEMAND_RULE, reject, _undecided(REASON_SUPPLY_UNMEASURED, GEN_BRAVO))
    card = card_for(trace)

    assert card is not None
    assert card.subject_key == f"power:fuel-demand:{GEN_BRAVO}"
    assert card.tier1 == "Plan 12.00 m3 of Qx Bio per minute for Qx Bravo Generator x2"
    named = [
        subject
        for subject in _subjects(trace, StepKind.ALTERNATIVE_REJECTED)
        + _subjects(trace, StepKind.COMPUTED)
        if GEN_ALPHA in subject
    ]
    assert named == []


def test_the_demand_rule_settles_through_reject_steps() -> None:
    trace = _run(DEMAND_RULE, _undecided(REASON_FLOW_INCOMPLETE))

    assert trace.recommendation is not None
    assert _kinds(trace, StepKind.VERDICT_INDETERMINATE) == []
    assert f"state a supply verdict for {GEN_ALPHA}" in _subjects(
        trace, StepKind.ALTERNATIVE_REJECTED
    )
    assert DEMAND_ID in settled_rules((trace,))


def test_an_unknown_burn_is_indeterminate_never_zero() -> None:
    trace = _run(DEMAND_RULE, _undecided(REASON_PRODUCTION_GAP))
    card = card_for(trace)

    assert card is not None
    assert card.tier1 == "Resolve the fuel burn of Qx Alpha Generator x2 before planning its fuel"
    assert card.tier2 == (
        "The burn of Qx Alpha Generator x2 is unknown, never zero, with no supply verdict: "
        + REASON_DETAIL[REASON_PRODUCTION_GAP]
    )
    undecided = [
        (step.subject, step.reason)
        for step in trace.steps
        if step.kind is StepKind.VERDICT_INDETERMINATE
    ]
    assert undecided == [
        (f"state the burn of {fuel} for {GEN_ALPHA}", REASON_DETAIL[REASON_PRODUCTION_GAP])
        for fuel in ACCEPTED[GEN_ALPHA]
    ]
    zeros = [value for value in _computed(trace).values() if value == 0]
    assert zeros == []
    assert DEMAND_ID not in settled_rules((trace,))


def test_a_class_with_unreadable_fuels_has_one_unknown_burn() -> None:
    trace = _run(DEMAND_RULE, _undecided(REASON_FUELS_UNREAD))

    undecided = [
        (step.subject, step.reason)
        for step in trace.steps
        if step.kind is StepKind.VERDICT_INDETERMINATE
    ]
    assert undecided == [(f"state the burn of {GEN_ALPHA}", REASON_DETAIL[REASON_FUELS_UNREAD])]


def test_a_known_burn_takes_the_headline_from_an_earlier_unknown_one() -> None:
    gap = _undecided(REASON_PRODUCTION_GAP, GEN_ALPHA)
    known = _class(
        GEN_BRAVO, VERDICT_INDETERMINATE, reasons=(REASON_SUPPLY_UNMEASURED,), clocks=(ONE,)
    )
    trace = _run(DEMAND_RULE, gap, known)
    card = card_for(trace)

    assert card is not None
    assert card.tier1 == "Plan 6.00 m3 of Qx Bio per minute for Qx Bravo Generator x1"
    assert card.tier2.endswith("; 1 other generator class is undecided too")
    assert card.subject_key == f"power:fuel-demand:{GEN_ALPHA},{GEN_BRAVO}"
    assert f"state the burn of {FUEL} for {GEN_ALPHA}" in _subjects(
        trace, StepKind.VERDICT_INDETERMINATE
    )


def test_the_demand_card_id_is_the_sorted_fired_set() -> None:
    alone = card_for(_run(DEMAND_RULE, _undecided(REASON_FLOW_INCOMPLETE)))
    both = card_for(
        _run(
            DEMAND_RULE,
            _undecided(REASON_FLOW_INCOMPLETE, GEN_BRAVO),
            _undecided(REASON_FLOW_INCOMPLETE),
        )
    )

    assert alone is not None
    assert both is not None
    assert alone.id == card_id(DEMAND_ID, f"power:fuel-demand:{GEN_ALPHA}", None)
    assert both.subject_key == f"power:fuel-demand:{GEN_ALPHA},{GEN_BRAVO}"
    assert both.id == card_id(DEMAND_ID, both.subject_key, None)
    assert both.id != alone.id


DEMAND_REASON: Final = (
    "Qx Alpha Generator x2 burn 40.00 m3 of Qx Fuel per minute at a demand of 500.00 MW,"
    " with no supply verdict: the production flow is incomplete, so the fuel supply is a"
    " floor and not a measurement"
)


def expected_demand_tier3(pin: int) -> str:
    """The whole on-pin derivation of Alpha's demand card, the pin read at test time.

    The docs hash is :func:`docs_pin` read at test time too (CS-1315), never
    typed: steps 4 to 6 are the registry check's three reads.
    """
    docs = docs_pin()
    return "\n".join(
        [
            "Derivation of rule power.fuel_demand (domain power)",
            "Advice: Plan 40.00 m3 of Qx Fuel per minute for Qx Alpha Generator x2",
            "Because: " + DEMAND_REASON,
            "Target milestone: none",
            "Steps:",
            f"  1. Read build.save_changelist = {pin} from audit.build.save_changelist",
            f"  2. Read build.pinned_changelist = {pin} from audit.build.pinned_changelist",
            "  3. Read build.warnings = {} from audit.build.warnings",
            f'  4. Read build.registry_sha256 = "{docs}" from audit.build.registry.source_sha256',
            f'  5. Read build.pinned_docs_sha256 = "{docs}" from'
            " audit.build.registry.pinned_sha256",
            "  6. Read build.registry_warnings = {} from audit.build.registry.warnings",
            '  7. Read power.fuel.classes = ("Build_QxAlphaGen_C") from'
            " audit.fuel.verdicts.class_name",
            '  8. Read power.fuel.verdicts = {"Build_QxAlphaGen_C": "indeterminate"} from'
            " audit.fuel.verdicts.verdict",
            '  9. Read power.fuel.reasons = {"Build_QxAlphaGen_C": ("flow-incomplete")} from'
            " audit.fuel.verdicts.reasons",
            '  10. Read power.fuel.demand_reasons = {"Build_QxAlphaGen_C": ()} from'
            " audit.fuel.demands.reasons",
            '  11. Read power.fuel.reason_details = {"flow-incomplete": "the production flow is'
            ' incomplete, so the fuel supply is a floor and not a measurement"} from'
            " audit.fuel.REASON_DETAIL",
            '  12. Read power.fuel.instance_counts = {"Build_QxAlphaGen_C": 2} from'
            " audit.fuel.verdicts.instance_count",
            '  13. Read power.fuel.omitted_counts = {"Build_QxAlphaGen_C": 0} from'
            " audit.fuel.verdicts.omitted_count",
            '  14. Read power.fuel.elided_clock_counts = {"Build_QxAlphaGen_C": 0} from'
            " audit.fuel.verdicts.elided_clock_count",
            '  15. Read power.fuel.nameplate_mw = {"Build_QxAlphaGen_C": 250.00} from'
            " audit.fuel.verdicts.nameplate_megawatts",
            '  16. Read power.fuel.clock_sum = {"Build_QxAlphaGen_C": 2.00} from'
            " audit.fuel.verdicts.clock_sum",
            '  17. Read power.fuel.demand_mw = {"Build_QxAlphaGen_C": 500.00} from'
            " audit.fuel.verdicts.demand_megawatts",
            '  18. Read power.fuel.accepted_fuels = {"Build_QxAlphaGen_C":'
            ' ("Desc_QxFuel_C", "Desc_QxTurbo_C")} from audit.fuel.verdicts.accepted_fuels',
            '  19. Read power.fuel.mj_per_unit = {"Desc_QxFuel_C": 750.00,'
            ' "Desc_QxTurbo_C": 2000.00} from audit.fuel.verdicts.fuels.megajoules_per_unit',
            '  20. Read power.fuel.units = {"Desc_QxFuel_C": "m3", "Desc_QxTurbo_C": "m3"} from'
            " audit.fuel.verdicts.fuels.unit",
            '  21. Read power.fuel.burns = {"Build_QxAlphaGen_C":'
            ' {"Desc_QxFuel_C": 40.00, "Desc_QxTurbo_C": 15.00}} from'
            " audit.fuel.demands.burns.burn_per_minute",
            '  22. Read power.fuel.exclusions = ("supplemental resources such as water are not'
            ' compared against any supply", "byproducts a generator emits are not modelled")'
            " from audit.fuel.exclusions",
            '  23. Read power.fuel.class_names = {"Build_QxAlphaGen_C": "Qx Alpha Generator"} from'
            " registry.generators.display_name",
            '  24. Read power.fuel.fuel_names = {"Desc_QxFuel_C": "Qx Fuel",'
            ' "Desc_QxTurbo_C": "Qx Turbo"} from registry.items.display_name',
            "  25. Rejected state a supply verdict for Build_QxAlphaGen_C: the production flow is"
            " incomplete, so the fuel supply is a floor and not a measurement",
            "  26. Computed demand MW of Build_QxAlphaGen_C, nameplate times clock sum = 500.00",
            "  27. Computed burn per minute of Desc_QxFuel_C for Build_QxAlphaGen_C = 40.00",
            "  28. Computed burn per minute of Desc_QxTurbo_C for Build_QxAlphaGen_C = 15.00",
            "  29. Rejected size supplemental resources and byproducts: out of scope:"
            " supplemental resources such as water are not compared against any supply;"
            " byproducts a generator emits are not modelled",
            "  30. Rule power.fuel_demand fired for power:fuel-demand:Build_QxAlphaGen_C",
        ]
    )


def test_demand_tier3_snapshot_shows_the_whole_derivation() -> None:
    card = card_for(_run(DEMAND_RULE, _undecided(REASON_FLOW_INCOMPLETE)))

    assert card is not None
    assert card.tier2 == DEMAND_REASON
    assert card.tier3 == expected_demand_tier3(game_pin())


# ---------------------------------------------------------------------------
# Fix round 1: every fired class's own step, the headline and the default-clock
# count, over the real-save shape - a fluid class beside a coal class, and no
# recipe machine, so the flow is incomplete and every class is undecided
# ---------------------------------------------------------------------------

FLOW_LINE: Final = REASON_DETAIL[REASON_FLOW_INCOMPLETE]
SOLID_LINE: Final = REASON_DETAIL[REASON_SOLID_SUPPLY_UNMODELLED]
CLOCK_LINE: Final = REASON_DETAIL[REASON_CLOCK_UNREAD]

#: One Charlie generator at clock one burns 75 * 60 / 300 items of coal a minute.
CHARLIE_COAL_BURN: Final = CHARLIE_MW * SIXTY / COAL_MJ_PER_ITEM


def _real_pair(
    *,
    alpha_clock: Fraction | None = ONE,
    charlie_clock: Fraction | None = ONE,
    elided: bool = False,
) -> WorldFuel:
    """Two Alpha generators and one Charlie (coal) generator, and nothing else.

    ``elided`` puts ONE Alpha generator and the Charlie generator at the
    elided default clock; a clock of None is an unread clock.
    """
    states = [
        _gen(GEN_ALPHA, clock=alpha_clock, elided=elided),
        _gen(GEN_ALPHA, clock=alpha_clock),
        _gen(GEN_CHARLIE, clock=charlie_clock, elided=elided),
    ]
    return fuel_supply_of(_machines(states), REGISTRY)


def _verdict_reasons(world: WorldFuel) -> dict[str, tuple[str, ...]]:
    return {verdict.class_name: verdict.reasons for verdict in world.verdicts}


def _pairs(trace: Trace, kind: StepKind, prefix: str) -> list[tuple[str, str]]:
    return [
        (step.subject, step.reason)
        for step in trace.steps
        if step.kind is kind and step.subject.startswith(prefix)
    ]


def test_the_real_pair_fixture_is_the_shape_the_arms_below_rest_on() -> None:
    assert _verdict_reasons(_real_pair()) == {
        GEN_ALPHA: (REASON_FLOW_INCOMPLETE,),
        GEN_CHARLIE: (REASON_FLOW_INCOMPLETE, REASON_SOLID_SUPPLY_UNMODELLED),
    }
    assert _verdict_reasons(_real_pair(charlie_clock=None)) == {
        GEN_ALPHA: (REASON_FLOW_INCOMPLETE,),
        GEN_CHARLIE: (
            REASON_CLOCK_UNREAD,
            REASON_FLOW_INCOMPLETE,
            REASON_SOLID_SUPPLY_UNMODELLED,
        ),
    }


def test_every_undecided_class_gets_its_own_indeterminate_supply_step() -> None:
    trace = run_rule(SUPPLY_RULE, _inputs(_real_pair()))

    assert trace.recommendation is None
    assert _pairs(trace, StepKind.VERDICT_INDETERMINATE, "compare") == [
        (f"compare the pooled fuel supply against the demand of {GEN_ALPHA}", FLOW_LINE),
        (
            f"compare the pooled fuel supply against the demand of {GEN_CHARLIE}",
            f"{FLOW_LINE}; {SOLID_LINE}",
        ),
    ]
    assert SUPPLY_ID not in settled_rules((trace,))


def test_every_fired_class_gets_its_own_supply_verdict_reject_on_tier3() -> None:
    trace = run_rule(DEMAND_RULE, _inputs(_real_pair()))
    card = card_for(trace)

    assert card is not None
    assert _pairs(trace, StepKind.ALTERNATIVE_REJECTED, "state a supply verdict") == [
        (f"state a supply verdict for {GEN_ALPHA}", FLOW_LINE),
        (f"state a supply verdict for {GEN_CHARLIE}", f"{FLOW_LINE}; {SOLID_LINE}"),
    ]
    assert f"Rejected state a supply verdict for {GEN_ALPHA}: {FLOW_LINE}" in card.tier3
    charlie_line = f"Rejected state a supply verdict for {GEN_CHARLIE}: {FLOW_LINE}; {SOLID_LINE}"
    assert charlie_line in card.tier3
    assert DEMAND_ID in settled_rules((trace,))


def test_the_demand_headline_is_the_first_class_by_key_with_a_known_burn() -> None:
    trace = run_rule(DEMAND_RULE, _inputs(_real_pair()))
    card = card_for(trace)

    assert card is not None
    assert card.subject_key == f"power:fuel-demand:{GEN_ALPHA},{GEN_CHARLIE}"
    assert card.tier1 == "Plan 40.00 m3 of Qx Fuel per minute for Qx Alpha Generator x2"
    assert card.tier2 == (
        "Qx Alpha Generator x2 burn 40.00 m3 of Qx Fuel per minute at a demand of 500.00 MW,"
        f" with no supply verdict: {FLOW_LINE}; 1 other generator class is undecided too"
    )
    burn = _computed(trace)[f"burn per minute of {COAL} for {GEN_CHARLIE}"]
    assert burn == CHARLIE_COAL_BURN


def test_the_burn_unknown_headline_is_the_first_class_by_key() -> None:
    world = _real_pair(alpha_clock=None, charlie_clock=None)
    burns = [burn.burn_per_minute for demand in world.demands for burn in demand.burns]
    assert burns == [None, None, None], "the fixture has a known burn"
    card = card_for(run_rule(DEMAND_RULE, _inputs(world)))

    assert card is not None
    assert card.tier1 == "Resolve the fuel burn of Qx Alpha Generator x2 before planning its fuel"
    assert card.tier2 == (
        "The burn of Qx Alpha Generator x2 is unknown, never zero, with no supply verdict:"
        f" {CLOCK_LINE}; 1 other generator class is undecided too"
    )


def test_an_unknown_burn_cites_its_demand_reason_and_no_other() -> None:
    trace = run_rule(DEMAND_RULE, _inputs(_real_pair(charlie_clock=None)))

    assert trace.recommendation is not None
    assert _pairs(trace, StepKind.VERDICT_INDETERMINATE, "state the burn") == [
        (f"state the burn of {COAL} for {GEN_CHARLIE}", CLOCK_LINE)
    ]
    assert DEMAND_ID not in settled_rules((trace,))


def test_an_unknown_burn_beside_a_known_one_keeps_the_demand_rule_unsettled() -> None:
    pair = _class(
        GEN_ALPHA, VERDICT_INDETERMINATE, fuels=(FUEL, DUD), reasons=(REASON_ENERGY_UNKNOWN,)
    )
    trace = _run(DEMAND_RULE, pair)
    card = card_for(trace)

    assert card is not None
    assert card.tier1 == "Plan 40.00 m3 of Qx Fuel per minute for Qx Alpha Generator x2"
    assert _computed(trace)[f"burn per minute of {FUEL} for {GEN_ALPHA}"] == Fraction(40)
    assert _pairs(trace, StepKind.VERDICT_INDETERMINATE, "state the burn") == [
        (f"state the burn of {DUD} for {GEN_ALPHA}", REASON_DETAIL[REASON_ENERGY_UNKNOWN])
    ]
    assert DEMAND_ID not in settled_rules((trace,))


TWO_ELIDED: Final = "; it assumes the default clock for 2 generators whose save omits the clock tag"


def test_the_supply_default_clock_note_counts_every_fired_class() -> None:
    card = card_for(_run(SUPPLY_RULE, _alpha_fire(elided=1), _bravo_fire(elided=1)))

    assert card is not None
    assert card.tier2 == SUPPLY_REASON + "; 1 other generator class is short too" + TWO_ELIDED


def test_the_demand_default_clock_note_counts_every_fired_class() -> None:
    world = _real_pair(elided=True)
    assert [verdict.elided_clock_count for verdict in world.verdicts] == [1, 1]
    card = card_for(run_rule(DEMAND_RULE, _inputs(world)))

    assert card is not None
    assert card.tier2.endswith("; 1 other generator class is undecided too" + TWO_ELIDED)


def _reversed(value: object) -> object:
    assert type(value) is tuple
    return tuple(reversed(value))


@pytest.mark.parametrize(
    ("spec", "kind", "prefix"),
    [
        (SUPPLY_RULE, StepKind.VERDICT_INDETERMINATE, "compare"),
        (DEMAND_RULE, StepKind.ALTERNATIVE_REJECTED, "state a supply verdict"),
    ],
    ids=[SUPPLY_ID, DEMAND_ID],
)
def test_classes_are_taken_in_key_order_whatever_order_they_are_offered_in(
    spec: RuleSpec, kind: StepKind, prefix: str
) -> None:
    trace = run_rule(spec, _tampered(_real_pair(), IN_CLASSES, _reversed))

    subjects = [subject for subject, _ in _pairs(trace, kind, prefix)]
    assert [subject.rsplit(" ", 1)[-1] for subject in subjects] == [GEN_ALPHA, GEN_CHARLIE]
    if spec is DEMAND_RULE:
        card = card_for(trace)
        assert card is not None
        assert card.tier1 == "Plan 40.00 m3 of Qx Fuel per minute for Qx Alpha Generator x2"


@pytest.mark.parametrize("spec", RULES, ids=lambda spec: spec.rule_id)
def test_a_firing_card_with_no_exclusion_line_is_a_rule_error(spec: RuleSpec) -> None:
    pair = _alpha_fire() if spec is SUPPLY_RULE else _undecided(REASON_FLOW_INCOMPLETE)
    world = _world_fuel(pair)
    assert run_rule(spec, _inputs(world)).recommendation is not None, "the control does not fire"

    trace = run_rule(spec, _inputs(replace(world, exclusions=())))

    assert trace.recommendation is None
    assert len(_errors(trace)) == 1


# ---------------------------------------------------------------------------
# Fix round 2: a card states the BUILT generator count - read plus never read -
# and how many were never read, so a generator the save never recorded as a
# running machine never drops out of the count (and no card says "x0")
# ---------------------------------------------------------------------------

OMITTED_LINE: Final = REASON_DETAIL[REASON_INSTANCES_OMITTED]


def _census_world(states: list[MachineState], *, alpha: int = 0, charlie: int = 0) -> WorldFuel:
    """The given generators plus ``alpha`` and ``charlie`` built ones never admitted."""
    census = tuple(
        (key, count) for key, count in ((GEN_ALPHA, alpha), (GEN_CHARLIE, charlie)) if count
    )
    return fuel_supply_of(_machines(states, unadmitted=census), REGISTRY)


def _demand_card(world: WorldFuel) -> tuple[Trace, Card]:
    trace = run_rule(DEMAND_RULE, _inputs(world))
    card = card_for(trace)
    assert card is not None
    return trace, card


def test_the_census_worlds_are_the_shape_the_arms_below_rest_on() -> None:
    one = _census_world([_gen(GEN_CHARLIE)], charlie=1)
    untagged = _census_world([], charlie=2)

    assert [(v.instance_count, v.omitted_count) for v in one.verdicts] == [(1, 1)]
    assert [(v.instance_count, v.omitted_count) for v in untagged.verdicts] == [(0, 2)]
    assert REASON_INSTANCES_OMITTED in one.verdicts[0].reasons


def test_one_class_with_an_unread_generator_states_the_built_count() -> None:
    trace, card = _demand_card(_census_world([_gen(GEN_CHARLIE)], charlie=1))

    assert card.tier1 == (
        "Resolve the fuel burn of Qx Charlie Generator x2 (1 never read) before planning its fuel"
    )
    assert card.tier2 == (
        "The burn of Qx Charlie Generator x2 is unknown, never zero, with no supply verdict:"
        f" {OMITTED_LINE}; 1 built generator was never read"
    )
    assert (
        f'Read {IN_OMITTED} = {{"{GEN_CHARLIE}": 1}} from audit.fuel.verdicts.omitted_count'
        in card.tier3
    )
    assert IN_OMITTED in _subjects(trace, StepKind.INPUT_READ)


def test_two_classes_count_an_unread_generator_beside_the_headline() -> None:
    world = _census_world([_gen(GEN_ALPHA), _gen(GEN_ALPHA), _gen(GEN_CHARLIE)], charlie=1)
    _, card = _demand_card(world)

    assert card.tier1 == "Plan 40.00 m3 of Qx Fuel per minute for Qx Alpha Generator x2"
    assert card.tier2 == (
        "Qx Alpha Generator x2 burn 40.00 m3 of Qx Fuel per minute at a demand of 500.00 MW,"
        f" with no supply verdict: {FLOW_LINE}; 1 other generator class is undecided too;"
        " 1 built generator was never read"
    )


def test_two_classes_each_with_an_unread_generator_count_them_all() -> None:
    world = _census_world([_gen(GEN_ALPHA), _gen(GEN_CHARLIE)], alpha=1, charlie=1)
    _, card = _demand_card(world)

    assert card.tier1 == (
        "Resolve the fuel burn of Qx Alpha Generator x2 (1 never read) before planning its fuel"
    )
    assert card.tier2 == (
        "The burn of Qx Alpha Generator x2 is unknown, never zero, with no supply verdict:"
        f" {OMITTED_LINE}; 1 other generator class is undecided too;"
        " 2 built generators were never read"
    )


def test_a_class_whose_every_generator_is_unread_never_reads_x0() -> None:
    _, card = _demand_card(_census_world([], charlie=2))

    assert card.tier1 == (
        "Resolve the fuel burn of Qx Charlie Generator x2 (2 never read) before planning its fuel"
    )
    assert card.tier2 == (
        "The burn of Qx Charlie Generator x2 is unknown, never zero, with no supply verdict:"
        f" {OMITTED_LINE}; 2 built generators were never read"
    )
    assert "x0" not in card.tier1 + card.tier2


def test_no_unread_generator_adds_no_never_read_note() -> None:
    _, card = _demand_card(_real_pair())

    assert "never read" not in card.tier1
    assert "never read" not in card.tier2


# ---------------------------------------------------------------------------
# CS-1288: every fuel card states an off-pin build (the session 138 rulings
# F1, F5 and F7). The nameplate, the clock-sum demand and every burn and
# shortfall rate are priced at the pinned build's nameplate, so off the pin
# tier 2 says so and names both builds, tier 1 and every computed figure stay
# the on-pin run's own, and no run - firing or silent - settles its rule.
# ---------------------------------------------------------------------------

#: The alternative an off-pin run records as indeterminate, spelled here
#: independently of ``clockspeed/advisor/build.py``.
NAMEPLATE_ALTERNATIVE: Final = "present a nameplate figure as the save build's own"

#: Each rule's own inputs, in the order its spec declares them after the build's.
OWN_INPUTS: Final[Mapping[str, tuple[str, ...]]] = MappingProxyType(
    {SUPPLY_ID: SUPPLY_INPUTS, DEMAND_ID: DEMAND_INPUTS}
)


def _mismatch(pin: int) -> str:
    """The tier 2 suffix of a save written by the build after the pin."""
    return (
        f"; {WARN_BUILD_MISMATCH}: priced at the pinned build {pin}, not the save build {pin + 1}"
    )


def _build_detail(save: int, pin: int | None) -> str:
    """The audit's own fixed detail line for the one warning a check raises."""
    warnings = build_check(save, pin).warnings
    count = len(warnings)
    assert count == 1
    return warnings[0].detail


def _computed_steps(trace: Trace) -> list[tuple[str, object]]:
    return [(s.subject, s.value) for s in trace.steps if s.kind is StepKind.COMPUTED]


#: One firing world per reason a fuel card can carry: the supply rule's one
#: return site, and the demand rule's one return site over a known burn and
#: over an unknown one. The last column is whether the run settles on the pin.
FUEL_SITES: Final[
    Mapping[str, tuple[RuleSpec, Callable[[BuildInputs | None], WorldInputs], str, bool]]
] = MappingProxyType(
    {
        "supply-short": (
            SUPPLY_RULE,
            lambda build: _inputs(_world_fuel(_alpha_fire()), build=build),
            "Supply 14.00 m3 more Qx Fuel",
            True,
        ),
        "demand-known-burn": (
            DEMAND_RULE,
            lambda build: _inputs(_world_fuel(_undecided(REASON_FLOW_INCOMPLETE)), build=build),
            "Plan 40.00 m3 of Qx Fuel",
            True,
        ),
        "demand-unknown-burn": (
            DEMAND_RULE,
            lambda build: _inputs(_world_fuel(_undecided(REASON_ENERGY_UNKNOWN)), build=build),
            "Resolve the fuel burn of Qx Alpha Generator",
            False,
        ),
    }
)

#: One silent world per way each fuel rule declines on a definite verdict.
FUEL_SILENT: Final[Mapping[str, tuple[RuleSpec, Callable[[BuildInputs | None], WorldInputs]]]] = (
    MappingProxyType(
        {
            "supply-covered": (
                SUPPLY_RULE,
                lambda build: _inputs(
                    _world_fuel(_class(GEN_ALPHA, VERDICT_REJECT, supply=ALPHA_COVERED)),
                    build=build,
                ),
            ),
            "supply-no-class": (SUPPLY_RULE, lambda build: _inputs(_world_fuel(), build=build)),
            "demand-all-decided": (
                DEMAND_RULE,
                lambda build: _inputs(_world_fuel(_alpha_fire()), build=build),
            ),
            "demand-no-class": (DEMAND_RULE, lambda build: _inputs(_world_fuel(), build=build)),
        }
    )
)


@pytest.mark.parametrize("spec", RULES, ids=lambda spec: spec.rule_id)
def test_both_fuel_rules_declare_the_build_inputs_ahead_of_their_own(spec: RuleSpec) -> None:
    assert spec.inputs == (*BUILD_INPUTS, *OWN_INPUTS[spec.rule_id])
    repeated = len(spec.inputs) != len(set(spec.inputs))
    assert not repeated


@pytest.mark.parametrize("site", sorted(FUEL_SITES))
def test_a_fuel_rule_reads_every_declared_name_once(site: str) -> None:
    spec, make, _headline, _settles = FUEL_SITES[site]
    for build in (pinned_build_inputs(game_pin()), off_pin_build_inputs(game_pin())):
        trace = run_rule(spec, make(build))
        reads = _subjects(trace, StepKind.INPUT_READ)
        assert len(reads) == len(set(reads))
        assert sorted(reads) == sorted(spec.inputs)


@pytest.mark.parametrize("site", sorted(FUEL_SITES))
def test_an_off_pin_fuel_card_names_both_builds_and_moves_nothing_else(site: str) -> None:
    pin = game_pin()
    spec, make, headline, settles = FUEL_SITES[site]
    on = run_rule(spec, make(pinned_build_inputs(pin)))
    off = run_rule(spec, make(off_pin_build_inputs(pin)))
    on_card = card_for(on)
    off_card = card_for(off)
    assert on_card is not None
    assert off_card is not None

    assert on_card.tier1.startswith(headline)
    assert "build-" not in on_card.tier2
    assert off_card.tier1 == on_card.tier1
    assert off_card.tier2 == on_card.tier2 + _mismatch(pin)
    assert off_card.id == on_card.id
    assert _computed_steps(off) == _computed_steps(on)
    assert (spec.rule_id in settled_rules((on,))) is settles
    assert spec.rule_id not in settled_rules((off,))


@pytest.mark.parametrize("site", sorted(FUEL_SITES))
def test_the_off_pin_fuel_indeterminate_step_follows_the_three_build_reads(site: str) -> None:
    pin = game_pin()
    spec, make, _headline, _settles = FUEL_SITES[site]
    trace = run_rule(spec, make(off_pin_build_inputs(pin)))

    kinds = [s.kind for s in trace.steps[: len(BUILD_INPUTS) + 1]]
    assert kinds == [*[StepKind.INPUT_READ] * len(BUILD_INPUTS), StepKind.VERDICT_INDETERMINATE]
    assert tuple(s.subject for s in trace.steps[: len(BUILD_INPUTS)]) == BUILD_INPUTS
    build_steps = [
        (s.subject, s.reason)
        for s in _kinds(trace, StepKind.VERDICT_INDETERMINATE)
        if s.subject == NAMEPLATE_ALTERNATIVE
    ]
    assert build_steps == [(NAMEPLATE_ALTERNATIVE, _build_detail(pin + 1, pin))]


@pytest.mark.parametrize("site", sorted(FUEL_SILENT))
def test_an_off_pin_silent_fuel_rule_is_not_settled(site: str) -> None:
    pin = game_pin()
    spec, make = FUEL_SILENT[site]
    on = run_rule(spec, make(pinned_build_inputs(pin)))
    off = run_rule(spec, make(off_pin_build_inputs(pin)))

    assert on.recommendation is None
    assert off.recommendation is None
    assert _errors(on) == []
    assert _errors(off) == []
    rejected_on = _subjects(on, StepKind.ALTERNATIVE_REJECTED)
    assert _subjects(off, StepKind.ALTERNATIVE_REJECTED) == rejected_on
    assert rejected_on != []
    assert spec.rule_id in settled_rules((on,))
    assert spec.rule_id not in settled_rules((off,))


@pytest.mark.parametrize("site", sorted(FUEL_SITES))
def test_with_no_pin_a_fuel_card_names_the_uncompared_build_never_a_mismatch(site: str) -> None:
    pin = game_pin()
    spec, make, _headline, _settles = FUEL_SITES[site]
    on_card = card_for(run_rule(spec, make(pinned_build_inputs(pin))))
    trace = run_rule(spec, make(uncompared_build_inputs(pin)))
    card = card_for(trace)
    assert on_card is not None
    assert card is not None

    expected = (
        f"; {WARN_BUILD_UNCOMPARED}: the save build {pin} was never compared,"
        " as no pinned build exists"
    )
    assert card.tier2 == on_card.tier2 + expected
    assert WARN_BUILD_MISMATCH not in card.tier2
    assert spec.rule_id not in settled_rules((trace,))


def _renumbered(line: str) -> str:
    """One numbered derivation line moved one step down."""
    number, _, rest = line.strip().partition(". ")
    return f"  {int(number) + 1}. {rest}"


@pytest.mark.parametrize(
    ("spec", "classes", "snapshot"),
    [
        (SUPPLY_RULE, (_alpha_fire(),), expected_supply_tier3),
        (DEMAND_RULE, (_undecided(REASON_FLOW_INCOMPLETE),), expected_demand_tier3),
    ],
    ids=[SUPPLY_ID, DEMAND_ID],
)
def test_an_off_pin_fuel_tier3_is_the_snapshot_with_both_builds_and_one_step_more(
    spec: RuleSpec,
    classes: tuple[tuple[FuelVerdict, FuelDemand], ...],
    snapshot: Callable[[int], str],
) -> None:
    pin = game_pin()
    expected = snapshot(pin).splitlines()
    card = card_for(run_rule(spec, _inputs(_world_fuel(*classes), build=off_pin_build_inputs(pin))))
    assert card is not None
    lines = card.tier3.splitlines()

    head = 5
    assert lines[:2] == expected[:2]
    assert lines[2] == expected[2] + _mismatch(pin)
    assert lines[3:head] == expected[3:head]
    assert (
        lines[head]
        == f"  1. Read build.save_changelist = {pin + 1} from audit.build.save_changelist"
    )
    assert lines[head + 1] == expected[head + 1]
    assert lines[head + 2].startswith(f'  3. Read build.warnings = {{"{WARN_BUILD_MISMATCH}": ')
    assert lines[head + 2].endswith(" from audit.build.warnings")
    assert lines[head + 3 : head + 6] == expected[head + 3 : head + 6]
    detail = _build_detail(pin + 1, pin)
    assert lines[head + 6] == f"  7. Indeterminate {NAMEPLATE_ALTERNATIVE}: {detail}"
    assert lines[head + 7 :] == [_renumbered(line) for line in expected[head + 6 :]]
