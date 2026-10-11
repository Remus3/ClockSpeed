"""CS-1285 slice B: the fuel supply audit, per built fuel generator class, exact.

Every fixture here is a hand-built synthetic literal - invented items, invented
generators, invented recipes - authored in this module. Nothing opens a save, a
docs file or the install; see ``tests/audit/__init__.py`` for the four rules
that bind every module in this directory.

THE FIGURES ARE RE-DERIVED HERE FROM THE FIXTURE CONSTANTS, never read back out
of the module under test. A generator of ``P`` MW at clock ``c`` demands
``P * c`` MW; one burning a fuel of ``E`` MJ per unit burns
``P * c * 60 / E`` units per minute; a supply of ``s`` units per minute yields
``s * E / 60`` MW. A fluid's energy value is MJ per LITRE, so its unit is the
cubic metre and its ``E`` is the value times ``LITRES_PER_CUBIC_METRE``.

THE CONFIDENT ANSWER IS THE DEFECT GRADED HARDEST. A verdict over an incomplete
input - an unread clock, an unknown energy value, an incomplete flow, a fuel two
generator classes compete for - would be a confident fire or a confident
silence about a world nobody measured, so each such class is INDETERMINATE with
a NAMED reason, and an unknown figure is None, never a zero.

THE FLOW IS THE WORLD'S OWN, BUILT BY THE AUDIT. ``fuel_supply_of`` takes no
flow: it builds one from the world's own machines that name a recipe, so a flow
over some other population cannot be handed in. Every fixture therefore hands
the audit ONE world - generators, recipe machines, recipe-less machines and
census records together - and the recipes. A machine no flow can measure - a
recipe-less one or a census record - is judged by which fuels its class could
make: a recipe produced in it, or an extraction the caller declares. A
REGISTERED class that makes no fuel (a lamp, a belt, a foundation) never blocks
a verdict; a class no input declares may make or eat any fuel, so it blocks
every one.
"""

from __future__ import annotations

import inspect
from collections.abc import Mapping
from dataclasses import dataclass, fields, is_dataclass, replace
from fractions import Fraction
from types import MappingProxyType
from typing import Final

import pytest

from clockspeed.audit import fuel
from clockspeed.audit.balance import (
    ELIDED_CLOCK_DEFAULT,
    GAP_NO_REGISTRY_ENTRY,
    GAP_PRODUCTION_INEXACT,
    GAP_PRODUCTION_UNDECLARED,
    GAP_PRODUCTION_VARIABLE,
)
from clockspeed.audit.machines import MachineState, WorldMachines
from clockspeed.data.registry import (
    FORM_GAS,
    FORM_LIQUID,
    FORM_SOLID,
    LITRES_PER_CUBIC_METRE,
    Generator,
    Item,
    Recipe,
    RecipeIO,
)

# ---------------------------------------------------------------------------
# Synthetic content
# ---------------------------------------------------------------------------

#: Invented fuel items.
COAL: Final = "Desc_SyntheticCoalQx85_C"
COKE: Final = "Desc_SyntheticCokeQx85_C"
FUEL: Final = "Desc_SyntheticFuelQx85_C"
DUD: Final = "Desc_SyntheticDudQx85_C"
ASH: Final = "Desc_SyntheticAshQx85_C"

#: MJ per item for the solids.
COAL_MJ: Final = Fraction(300)
COKE_MJ: Final = Fraction(180)
#: MJ per LITRE for the fluid - the shape the shipped docs declare.
FUEL_MJ_PER_LITRE: Final = Fraction(3, 4)
FUEL_MJ_PER_M3: Final = FUEL_MJ_PER_LITRE * LITRES_PER_CUBIC_METRE

#: Invented generator classes.
GEN_COAL: Final = "Build_SyntheticCoalGenQx85_C"
GEN_FUEL: Final = "Build_SyntheticFuelGenQx85_C"
GEN_COKE: Final = "Build_SyntheticCokeGenQx85_C"
GEN_DUD: Final = "Build_SyntheticDudGenQx85_C"
GEN_GEO: Final = "Build_SyntheticGeoGenQx85_C"
GEN_CYCLING_FUEL: Final = "Build_SyntheticCyclingFuelGenQx85_C"
GEN_SILENT: Final = "Build_SyntheticSilentGenQx85_C"
GEN_UNREGISTERED: Final = "Build_SyntheticUnregisteredGenQx85_C"
GEN_REVERSED: Final = "Build_SyntheticReversedGenQx85_C"
GEN_INEXACT: Final = "Build_SyntheticInexactGenQx85_C"
GEN_ZERO: Final = "Build_SyntheticZeroGenQx85_C"
GEN_GAS: Final = "Build_SyntheticGasGenQx85_C"
#: A variable-output generator whose declared output is NOT zero, so only the
#: variable-production check can put it out of scope.
GEN_GEO_RATED: Final = "Build_SyntheticRatedGeoGenQx85_C"
GEO_RATED_MW: Final = Fraction(100)

#: An invented gaseous fuel - a fluid form, so litres in the docs.
GAS: Final = "Desc_SyntheticGasQx85_C"
GAS_MJ_PER_LITRE: Final = Fraction(1, 5)

COAL_GEN_MW: Final = Fraction(75)
FUEL_GEN_MW: Final = Fraction(250)
COKE_GEN_MW: Final = Fraction(30)
DUD_GEN_MW: Final = Fraction(40)

#: The recipe machines' classes - not generators. Every recipe but the fuel
#: one is produced in MAKER; the liquid fuel is made only in REFINERY.
MAKER: Final = "Build_SyntheticMakerQx85_C"
REFINERY: Final = "Build_SyntheticRefineryQx85_C"

#: A recipe-less extractor. No flow rates it; the caller declares what it can
#: extract - coal, and nothing else.
MINER: Final = "Build_SyntheticMinerQx85_C"

#: REGISTERED classes that make no item at all: in no recipe's producers and
#: declared as no item's extractor. A lamp and a sink can carry machine state; a
#: belt and a foundation never do, so they reach the audit only through the
#: census.
LAMP: Final = "Build_SyntheticLampQx85_C"
SINK: Final = "Build_SyntheticSinkQx85_C"
BELT: Final = "Build_SyntheticBeltQx85_C"
FOUNDATION: Final = "Build_SyntheticFoundationQx85_C"

#: A class NO input declares - the correctness adversary's P3, an unknown
#: recipe-less class that may make or eat any fuel.
UNREGISTERED: Final = "Build_SyntheticModGenQx85_C"

R_COAL: Final = "Recipe_SyntheticCoalQx85_C"
R_COKE: Final = "Recipe_SyntheticCokeQx85_C"
R_FUEL: Final = "Recipe_SyntheticFuelQx85_C"
R_EAT_COAL: Final = "Recipe_SyntheticEatCoalQx85_C"
R_UNKNOWN: Final = "Recipe_SyntheticNeverAuthoredQx85_C"

#: Per-minute rate of one recipe machine at clock one, re-derived: 60 / duration.
COAL_PER_MAKER: Final = Fraction(60, 2)
COKE_PER_MAKER: Final = Fraction(60, 2)
FUEL_M3_PER_MAKER: Final = Fraction(60, 6)
COAL_EATEN_PER_MAKER: Final = Fraction(60, 6)

SIXTY: Final = Fraction(60)


def _item(key: str, form: str, energy: object) -> Item:
    return Item(
        key=key,
        display_name=f"Synthetic {key}",
        form=form,
        energy_value=energy,  # type: ignore[arg-type]
        sink_points=None,
        is_fluid=form in (FORM_LIQUID, FORM_GAS),
    )


def _generator(key: str, production: object, *, variable: bool = False) -> Generator:
    return Generator(
        key=key,
        display_name=f"Synthetic {key}",
        power_production=production,  # type: ignore[arg-type]
        variable_production_constant=Fraction(0) if variable else None,
        variable_production_factor=Fraction(200) if variable else None,
        is_variable_production=variable,
    )


def _recipe(
    key: str,
    duration: int,
    inputs: tuple[tuple[str, Fraction], ...],
    outputs: tuple[tuple[str, Fraction], ...],
    produced_in: str = MAKER,
) -> Recipe:
    return Recipe(
        key=key,
        display_name=f"Synthetic {key}",
        duration=Fraction(duration),
        inputs=tuple(RecipeIO(item_key=k, amount=a) for k, a in inputs),
        outputs=tuple(RecipeIO(item_key=k, amount=a) for k, a in outputs),
        produced_in=(produced_in,),
        variable_power_constant=None,
        variable_power_factor=None,
    )


ITEMS: Final[Mapping[str, Item]] = MappingProxyType(
    {
        COAL: _item(COAL, FORM_SOLID, COAL_MJ),
        COKE: _item(COKE, FORM_SOLID, COKE_MJ),
        FUEL: _item(FUEL, FORM_LIQUID, FUEL_MJ_PER_LITRE),
        DUD: _item(DUD, FORM_SOLID, None),
        ASH: _item(ASH, FORM_SOLID, None),
        GAS: _item(GAS, FORM_GAS, GAS_MJ_PER_LITRE),
    }
)

GENERATORS: Final[Mapping[str, Generator]] = MappingProxyType(
    {
        GEN_COAL: _generator(GEN_COAL, COAL_GEN_MW),
        GEN_FUEL: _generator(GEN_FUEL, FUEL_GEN_MW),
        GEN_COKE: _generator(GEN_COKE, COKE_GEN_MW),
        GEN_DUD: _generator(GEN_DUD, DUD_GEN_MW),
        GEN_GEO: _generator(GEN_GEO, Fraction(0), variable=True),
        GEN_CYCLING_FUEL: _generator(GEN_CYCLING_FUEL, Fraction(0), variable=True),
        GEN_SILENT: _generator(GEN_SILENT, None),
        GEN_REVERSED: _generator(GEN_REVERSED, COAL_GEN_MW),
        GEN_INEXACT: _generator(GEN_INEXACT, 75.0),
        GEN_ZERO: _generator(GEN_ZERO, Fraction(0)),
        GEN_GAS: _generator(GEN_GAS, FUEL_GEN_MW),
        GEN_GEO_RATED: _generator(GEN_GEO_RATED, GEO_RATED_MW, variable=True),
    }
)

#: The explicit accepted-fuel input, in mFuel order. GEN_GEO, GEN_GEO_RATED
#: and GEN_ZERO are ABSENT - they declare no fuel, the geothermal shape; a
#: class mapped to None or to a malformed value declares fuels nobody could
#: read. GEN_UNREGISTERED has fuels and no generator entry.
FUELS: Final[Mapping[str, tuple[str, ...] | None]] = MappingProxyType(
    {
        GEN_COAL: (COAL, COKE),
        GEN_FUEL: (FUEL,),
        GEN_COKE: (COKE,),
        GEN_DUD: (DUD,),
        GEN_CYCLING_FUEL: (FUEL,),
        GEN_SILENT: (COAL,),
        GEN_UNREGISTERED: (COAL,),
        GEN_REVERSED: (COKE, COAL),
        GEN_INEXACT: (COAL,),
        GEN_GAS: (GAS,),
    }
)

RECIPES: Final[Mapping[str, Recipe]] = MappingProxyType(
    {
        R_COAL: _recipe(R_COAL, 2, (), ((COAL, Fraction(1)),)),
        R_COKE: _recipe(R_COKE, 2, (), ((COKE, Fraction(1)),)),
        R_FUEL: _recipe(R_FUEL, 6, (), ((FUEL, Fraction(1)),), REFINERY),
        R_EAT_COAL: _recipe(R_EAT_COAL, 6, ((COAL, Fraction(1)),), ((ASH, Fraction(1)),)),
    }
)

#: The explicit extraction input: per item, every extractor class that can
#: extract it. Every item is listed, so no item's makers are unknown here.
EXTRACTABLE: Final[Mapping[str, frozenset[str] | None]] = MappingProxyType(
    {
        COAL: frozenset({MINER}),
        COKE: frozenset(),
        FUEL: frozenset(),
        DUD: frozenset(),
        ASH: frozenset(),
        GAS: frozenset(),
    }
)

#: The explicit registered-class input. MAKER, REFINERY and MINER are known
#: through the recipes and the extraction input, and every generator through
#: its namespaces; only the classes nothing else names are listed here.
REGISTERED: Final = frozenset({LAMP, SINK, BELT, FOUNDATION})


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------


def _gen(
    class_name: str,
    clock: object = Fraction(1),
    *,
    elided: bool = False,
    boosted: bool = False,
) -> MachineState:
    return MachineState(
        class_name=class_name,
        producing=True,
        recipe_class_name=None,
        overclock=clock,  # type: ignore[arg-type]
        overclock_elided=elided,
        production_boost_tagged=boosted,
    )


def _maker(recipe: str, clock: Fraction = Fraction(1)) -> MachineState:
    known = RECIPES.get(recipe)
    class_name = known.produced_in[0] if known is not None else MAKER
    return MachineState(
        class_name=class_name, producing=True, recipe_class_name=recipe, overclock=clock
    )


def _world(
    states: list[MachineState],
    *,
    unadmitted_read: tuple[tuple[str, int], ...] = (),
    unadmitted_unread: tuple[tuple[str, int], ...] = (),
) -> WorldMachines:
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
        unadmitted_read_counts=unadmitted_read,
        unadmitted_unread_counts=unadmitted_unread,
    )


def _recipe_less(class_name: str) -> MachineState:
    return MachineState(
        class_name=class_name, producing=True, recipe_class_name=None, overclock=Fraction(1)
    )


def _miner() -> MachineState:
    return _recipe_less(MINER)


@dataclass(frozen=True)
class _Scene:
    """The machines of one world besides its generators, and what it declares raw."""

    makers: tuple[MachineState, ...]
    raw: tuple[str, ...]


def _flow(*makers: MachineState, raw: tuple[str, ...] = ()) -> _Scene:
    return _Scene(makers, raw)


def _audit(
    world: WorldMachines,
    *,
    fuels: Mapping[str, tuple[str, ...] | None] = FUELS,
    recipes: Mapping[str, Recipe] = RECIPES,
    extractable: Mapping[str, frozenset[str] | None] = EXTRACTABLE,
    registered: object = REGISTERED,
    raw: tuple[str, ...] = (),
) -> fuel.WorldFuel:
    return fuel.fuel_supply_of(
        world,
        GENERATORS,
        fuels,
        ITEMS,
        recipes,
        extractable=extractable,
        registered=registered,  # type: ignore[arg-type]
        raw_items=raw,
    )


def _supply(
    generators: list[MachineState],
    supply: _Scene,
    *,
    fuels: Mapping[str, tuple[str, ...] | None] = FUELS,
    unadmitted_read: tuple[tuple[str, int], ...] = (),
    unadmitted_unread: tuple[tuple[str, int], ...] = (),
) -> fuel.WorldFuel:
    """Run the audit over ONE world: the generators plus every other machine."""
    world = _world(
        [*generators, *supply.makers],
        unadmitted_read=unadmitted_read,
        unadmitted_unread=unadmitted_unread,
    )
    return _audit(world, fuels=fuels, raw=supply.raw)


def _verdict(result: fuel.WorldFuel, class_name: str) -> fuel.FuelVerdict:
    matches = [entry for entry in result.verdicts if entry.class_name == class_name]
    assert len(matches) == 1
    return matches[0]


def _demand(demands: tuple[fuel.FuelDemand, ...], class_name: str) -> fuel.FuelDemand:
    matches = [entry for entry in demands if entry.class_name == class_name]
    assert len(matches) == 1
    return matches[0]


def _line(verdict: fuel.FuelVerdict, item_key: str) -> fuel.FuelLine:
    matches = [entry for entry in verdict.fuels if entry.item_key == item_key]
    assert len(matches) == 1
    return matches[0]


def _burn(demand: fuel.FuelDemand, item_key: str) -> fuel.FuelBurn:
    matches = [entry for entry in demand.burns if entry.item_key == item_key]
    assert len(matches) == 1
    return matches[0]


# ---------------------------------------------------------------------------
# Demand and burn arithmetic
# ---------------------------------------------------------------------------


def test_burn_is_exact_megawatts_times_sixty_over_energy() -> None:
    clock = Fraction(2, 3)
    demands = fuel.fuel_demand_of(_world([_gen(GEN_COAL, clock)]), GENERATORS, FUELS, ITEMS)
    demand = _demand(demands, GEN_COAL)
    expected_mw = COAL_GEN_MW * clock
    assert demand.demand_megawatts == expected_mw
    assert type(demand.demand_megawatts) is Fraction
    assert _burn(demand, COAL).burn_per_minute == expected_mw * SIXTY / COAL_MJ
    # 50 * 60 / 180 = 50/3 - no binary float holds it.
    assert _burn(demand, COKE).burn_per_minute == Fraction(50, 3)
    assert _burn(demand, COAL).unit == fuel.UNIT_ITEM
    assert demand.complete is True
    assert demand.reasons == ()


def test_a_fluid_fuel_burns_in_cubic_metres() -> None:
    demands = fuel.fuel_demand_of(_world([_gen(GEN_FUEL)]), GENERATORS, FUELS, ITEMS)
    burn = _burn(_demand(demands, GEN_FUEL), FUEL)
    assert burn.unit == fuel.UNIT_CUBIC_METRE
    assert burn.megajoules_per_unit == FUEL_MJ_PER_M3
    # 250 MW * 60 / 750 MJ per m3 = 20 m3 per minute - never 20000 litres and
    # never the 1/50 that reading the per-litre value as per-m3 gives.
    assert burn.burn_per_minute == Fraction(20)


def test_unknown_energy_is_a_named_gap_never_zero() -> None:
    demands = fuel.fuel_demand_of(_world([_gen(GEN_DUD)]), GENERATORS, FUELS, ITEMS)
    demand = _demand(demands, GEN_DUD)
    burn = _burn(demand, DUD)
    assert burn.megajoules_per_unit is None
    assert burn.burn_per_minute is None
    assert fuel.REASON_ENERGY_UNKNOWN in demand.reasons
    assert demand.complete is False

    result = _supply([_gen(GEN_DUD)], _flow(_maker(R_COAL)))
    verdict = _verdict(result, GEN_DUD)
    assert verdict.verdict == fuel.VERDICT_INDETERMINATE
    assert fuel.REASON_ENERGY_UNKNOWN in verdict.reasons
    assert verdict.pooled_megawatts is None
    assert _line(verdict, DUD).supply_megawatts is None


def test_an_item_the_mapping_lacks_is_unknown_energy() -> None:
    fuels = {GEN_COAL: ("Desc_SyntheticNeverAuthoredQx85_C",)}
    demands = fuel.fuel_demand_of(_world([_gen(GEN_COAL)]), GENERATORS, fuels, ITEMS)
    demand = _demand(demands, GEN_COAL)
    assert demand.reasons == (fuel.REASON_ENERGY_UNKNOWN,)
    assert demand.burns[0].unit is None
    assert demand.burns[0].burn_per_minute is None


@pytest.mark.parametrize("energy", [Fraction(0), Fraction(-1), 300.0])
def test_a_zero_energy_value_is_unknown_never_a_division(energy: object) -> None:
    items = dict(ITEMS)
    items[COAL] = _item(COAL, FORM_SOLID, energy)
    demands = fuel.fuel_demand_of(_world([_gen(GEN_COAL)]), GENERATORS, FUELS, items)
    demand = _demand(demands, GEN_COAL)
    assert fuel.REASON_ENERGY_UNKNOWN in demand.reasons
    assert _burn(demand, COAL).burn_per_minute is None
    assert _burn(demand, COAL).megajoules_per_unit is None
    assert _burn(demand, COKE).burn_per_minute == COAL_GEN_MW * SIXTY / COKE_MJ


@pytest.mark.parametrize("form", ["", "RF_INVALID"])
def test_an_unknown_form_is_unknown_energy(form: str) -> None:
    items = dict(ITEMS)
    items[COAL] = _item(COAL, form, COAL_MJ)
    demands = fuel.fuel_demand_of(_world([_gen(GEN_COAL)]), GENERATORS, FUELS, items)
    burn = _burn(_demand(demands, GEN_COAL), COAL)
    assert burn.unit is None
    assert burn.burn_per_minute is None


def test_a_gas_fuel_burns_in_cubic_metres_too() -> None:
    demands = fuel.fuel_demand_of(_world([_gen(GEN_GAS)]), GENERATORS, FUELS, ITEMS)
    burn = _burn(_demand(demands, GEN_GAS), GAS)
    assert burn.unit == fuel.UNIT_CUBIC_METRE
    assert burn.megajoules_per_unit == GAS_MJ_PER_LITRE * LITRES_PER_CUBIC_METRE
    assert burn.burn_per_minute == FUEL_GEN_MW * SIXTY / (GAS_MJ_PER_LITRE * 1000)


# ---------------------------------------------------------------------------
# Verdicts over a complete flow
# ---------------------------------------------------------------------------


def test_fires_with_exact_shortfall_on_complete_flow() -> None:
    maker_clock = Fraction(1, 3)
    result = _supply([_gen(GEN_FUEL)], _flow(_maker(R_FUEL, maker_clock)))
    verdict = _verdict(result, GEN_FUEL)
    supply_m3 = FUEL_M3_PER_MAKER * maker_clock
    supply_mw = supply_m3 * FUEL_MJ_PER_M3 / SIXTY
    shortfall = FUEL_GEN_MW - supply_mw
    assert verdict.verdict == fuel.VERDICT_FIRE
    assert verdict.reasons == ()
    assert verdict.demand_megawatts == FUEL_GEN_MW
    assert verdict.pooled_megawatts == supply_mw
    assert verdict.shortfall_megawatts == shortfall == Fraction(625, 3)
    line = _line(verdict, FUEL)
    assert line.supply_per_minute == supply_m3
    assert line.shortfall_per_minute == shortfall * SIXTY / FUEL_MJ_PER_M3 == Fraction(50, 3)
    assert verdict.headline_fuel == FUEL


def test_a_covering_supply_floor_rejects() -> None:
    # Two makers at clock one: 20 m3/min * 750 / 60 = 250 MW, exactly the demand.
    result = _supply([_gen(GEN_FUEL)], _flow(_maker(R_FUEL), _maker(R_FUEL)))
    verdict = _verdict(result, GEN_FUEL)
    assert verdict.pooled_megawatts == FUEL_GEN_MW
    assert verdict.verdict == fuel.VERDICT_REJECT
    assert verdict.shortfall_megawatts is None
    assert _line(verdict, FUEL).shortfall_per_minute is None

    over = _verdict(_supply([_gen(GEN_FUEL)], _flow(*[_maker(R_FUEL)] * 3)), GEN_FUEL)
    assert over.verdict == fuel.VERDICT_REJECT
    headroom = {step.label: step.value for step in over.trace}[fuel.LABEL_HEADROOM]
    assert headroom == 3 * FUEL_M3_PER_MAKER * FUEL_MJ_PER_M3 / SIXTY - FUEL_GEN_MW


def test_a_generator_at_clock_zero_burns_nothing_and_rejects() -> None:
    result = _supply([_gen(GEN_COAL, Fraction(0))], _flow(_maker(R_COAL, Fraction(0))))
    verdict = _verdict(result, GEN_COAL)
    assert verdict.demand_megawatts == Fraction(0)
    assert verdict.verdict == fuel.VERDICT_REJECT


def test_a_repeated_fuel_pools_once() -> None:
    fuels = {**FUELS, GEN_COAL: (COAL, COAL, COKE)}
    result = _supply([_gen(GEN_COAL)], _flow(_maker(R_COAL, Fraction(1, 6))), fuels=fuels)
    verdict = _verdict(result, GEN_COAL)
    assert verdict.accepted_fuels == (COAL, COKE)
    assert verdict.pooled_megawatts == COAL_PER_MAKER / 6 * COAL_MJ / SIXTY


def test_pooled_fuels_cover_where_no_single_fuel_does() -> None:
    # Two coal generators demand 150 MW. One coal maker at clock 1/2 moves
    # 15/min -> 75 MW; one coke maker at 5/6 moves 25/min -> 75 MW. Neither
    # alone covers 150 MW; pooled they do, exactly.
    supply = _flow(_maker(R_COAL, Fraction(1, 2)), _maker(R_COKE, Fraction(5, 6)))
    result = _supply([_gen(GEN_COAL), _gen(GEN_COAL)], supply)
    verdict = _verdict(result, GEN_COAL)
    demand = 2 * COAL_GEN_MW
    assert _line(verdict, COAL).supply_megawatts == Fraction(75)
    assert _line(verdict, COKE).supply_megawatts == Fraction(75)
    assert Fraction(75) < demand
    assert verdict.pooled_megawatts == demand
    assert verdict.verdict == fuel.VERDICT_REJECT


def test_n_instances_sum_demand_against_one_supply() -> None:
    clocks = (Fraction(1), Fraction(1, 2), Fraction(3, 2))
    maker_clock = Fraction(1, 2)
    supply = _flow(_maker(R_COAL, maker_clock))
    result = _supply([_gen(GEN_COAL, c) for c in clocks], supply)
    verdict = _verdict(result, GEN_COAL)
    demand = COAL_GEN_MW * sum(clocks)
    coal_mw = COAL_PER_MAKER * maker_clock * COAL_MJ / SIXTY
    assert verdict.instance_count == len(clocks)
    assert verdict.clock_sum == sum(clocks)
    assert verdict.demand_megawatts == demand
    # Coke is in no recipe of a complete flow, so its nominal supply is a
    # measured zero, not a gap.
    assert _line(verdict, COKE).supply_per_minute == Fraction(0)
    assert verdict.pooled_megawatts == coal_mw
    shortfall = demand - coal_mw
    assert verdict.verdict == fuel.VERDICT_FIRE
    assert verdict.shortfall_megawatts == shortfall
    assert _line(verdict, COAL).shortfall_per_minute == shortfall * SIXTY / COAL_MJ
    assert _line(verdict, COKE).shortfall_per_minute == shortfall * SIXTY / COKE_MJ


def test_recipe_consumption_leaves_only_the_net_for_generators() -> None:
    # Three coal makers (90/min) and three coal eaters (30/min) leave 60/min.
    supply = _flow(*[_maker(R_COAL)] * 3, *[_maker(R_EAT_COAL)] * 3)
    result = _supply([_gen(GEN_COAL)] * 5, supply)
    verdict = _verdict(result, GEN_COAL)
    net = 3 * COAL_PER_MAKER - 3 * COAL_EATEN_PER_MAKER
    assert _line(verdict, COAL).supply_per_minute == net
    assert verdict.pooled_megawatts == net * COAL_MJ / SIXTY


def test_a_negative_net_supplies_nothing_rather_than_a_debt() -> None:
    supply = _flow(*[_maker(R_EAT_COAL)] * 2, _maker(R_COKE))
    result = _supply([_gen(GEN_COAL)], supply)
    verdict = _verdict(result, GEN_COAL)
    assert _line(verdict, COAL).supply_per_minute == Fraction(0)
    assert verdict.pooled_megawatts == COKE_PER_MAKER * COKE_MJ / SIXTY


def test_the_headline_is_the_first_accepted_fuel_in_mfuel_order() -> None:
    result = _supply([_gen(GEN_REVERSED)], _flow(_maker(R_COAL, Fraction(0))))
    verdict = _verdict(result, GEN_REVERSED)
    assert verdict.verdict == fuel.VERDICT_FIRE
    assert verdict.accepted_fuels == (COKE, COAL)
    assert verdict.headline_fuel == COKE
    assert tuple(line.item_key for line in verdict.fuels) == (COKE, COAL)


def test_a_disjoint_class_keeps_its_verdict_beside_others() -> None:
    supply = _flow(_maker(R_FUEL), _maker(R_FUEL), _maker(R_COAL, Fraction(1, 10)))
    result = _supply([_gen(GEN_FUEL), _gen(GEN_COAL)], supply)
    assert _verdict(result, GEN_FUEL).verdict == fuel.VERDICT_REJECT
    assert _verdict(result, GEN_COAL).verdict == fuel.VERDICT_FIRE


# ---------------------------------------------------------------------------
# Indeterminate - a named reason, never a verdict
# ---------------------------------------------------------------------------


def test_a_fuel_shared_by_two_classes_is_indeterminate() -> None:
    supply = _flow(_maker(R_COKE), _maker(R_FUEL), _maker(R_FUEL))
    result = _supply([_gen(GEN_COAL), _gen(GEN_COKE), _gen(GEN_FUEL)], supply)
    coal = _verdict(result, GEN_COAL)
    coke = _verdict(result, GEN_COKE)
    assert coal.verdict == coke.verdict == fuel.VERDICT_INDETERMINATE
    assert fuel.REASON_FUEL_SHARED in coal.reasons
    assert fuel.REASON_FUEL_SHARED in coke.reasons
    assert coal.shared_with == (GEN_COKE,)
    assert coke.shared_with == (GEN_COAL,)
    assert coal.shortfall_megawatts is None
    # A class sharing nothing is untouched.
    assert _verdict(result, GEN_FUEL).verdict == fuel.VERDICT_REJECT
    assert _verdict(result, GEN_FUEL).shared_with == ()


def test_an_unread_clock_is_indeterminate() -> None:
    result = _supply([_gen(GEN_COAL), _gen(GEN_COAL, None)], _flow(_maker(R_COAL)))
    verdict = _verdict(result, GEN_COAL)
    assert verdict.verdict == fuel.VERDICT_INDETERMINATE
    assert fuel.REASON_CLOCK_UNREAD in verdict.reasons
    assert verdict.clock_sum is None
    assert verdict.demand_megawatts is None
    demand = _demand(result.demands, GEN_COAL)
    assert demand.demand_megawatts is None
    assert all(burn.burn_per_minute is None for burn in demand.burns)


def test_an_elided_clock_is_the_class_default_and_counted() -> None:
    states = [_gen(GEN_COAL, None, elided=True), _gen(GEN_COAL, Fraction(1, 2))]
    result = _supply(states, _flow(_maker(R_COAL)))
    verdict = _verdict(result, GEN_COAL)
    assert verdict.elided_clock_count == 1
    assert verdict.clock_sum == ELIDED_CLOCK_DEFAULT + Fraction(1, 2)
    assert verdict.demand_megawatts == COAL_GEN_MW * (ELIDED_CLOCK_DEFAULT + Fraction(1, 2))
    assert verdict.verdict == fuel.VERDICT_REJECT


@pytest.mark.parametrize("clock", [0.5, Fraction(-1, 2), 1])
def test_a_refused_clock_is_indeterminate(clock: object) -> None:
    result = _supply([_gen(GEN_COAL, clock)], _flow(_maker(R_COAL)))
    verdict = _verdict(result, GEN_COAL)
    assert verdict.verdict == fuel.VERDICT_INDETERMINATE
    assert fuel.REASON_CLOCK_REFUSED in verdict.reasons
    assert verdict.clock_sum is None


def test_a_boosted_generator_is_indeterminate() -> None:
    result = _supply([_gen(GEN_COAL, boosted=True)], _flow(_maker(R_COAL)))
    verdict = _verdict(result, GEN_COAL)
    assert verdict.verdict == fuel.VERDICT_INDETERMINATE
    assert fuel.REASON_BOOST_UNMODELED in verdict.reasons
    assert verdict.demand_megawatts is None


def test_an_omitted_instance_is_indeterminate() -> None:
    omitted = 2
    result = _supply(
        [_gen(GEN_COAL)], _flow(*[_maker(R_COAL)] * 9), unadmitted_unread=((GEN_COAL, omitted),)
    )
    verdict = _verdict(result, GEN_COAL)
    assert verdict.omitted_count == omitted
    assert verdict.verdict == fuel.VERDICT_INDETERMINATE
    assert fuel.REASON_INSTANCES_OMITTED in verdict.reasons
    assert verdict.demand_megawatts is None


def test_a_class_built_only_in_the_census_is_considered() -> None:
    result = _supply(
        [_gen(GEN_FUEL)], _flow(_maker(R_COKE), _maker(R_FUEL)), unadmitted_read=((GEN_COKE, 1),)
    )
    coke = _verdict(result, GEN_COKE)
    assert coke.instance_count == 0
    assert coke.omitted_count == 1
    assert coke.reasons == (fuel.REASON_INSTANCES_OMITTED,)
    # A GENERATOR in the census is an omitted instance, never an unmeasured
    # supply, so a class it shares no fuel with still decides.
    other = _verdict(result, GEN_FUEL)
    assert other.verdict == fuel.VERDICT_FIRE
    assert other.reasons == ()


def test_a_short_floor_on_incomplete_flow_is_indeterminate() -> None:
    supply = _flow(_maker(R_FUEL, Fraction(1, 3)), _maker(R_UNKNOWN))
    result = _supply([_gen(GEN_FUEL)], supply)
    verdict = _verdict(result, GEN_FUEL)
    assert result.flow_complete is False
    assert verdict.verdict == fuel.VERDICT_INDETERMINATE
    assert verdict.reasons == (fuel.REASON_FLOW_INCOMPLETE,)
    assert verdict.shortfall_megawatts is None
    # The floor is still published, for tier 3 to state as one.
    assert verdict.pooled_megawatts == FUEL_M3_PER_MAKER / 3 * FUEL_MJ_PER_M3 / SIXTY
    assert verdict.demand_megawatts == FUEL_GEN_MW


def test_a_covering_floor_on_incomplete_flow_is_still_indeterminate() -> None:
    supply = _flow(*[_maker(R_FUEL)] * 5, _maker(R_UNKNOWN))
    verdict = _verdict(_supply([_gen(GEN_FUEL)], supply), GEN_FUEL)
    assert verdict.verdict == fuel.VERDICT_INDETERMINATE
    assert verdict.reasons == (fuel.REASON_FLOW_INCOMPLETE,)


def test_unreadable_fuels_are_indeterminate() -> None:
    supply = _flow(_maker(R_FUEL), _maker(R_FUEL))
    variants: tuple[Mapping[str, tuple[str, ...] | None], ...] = (
        {**FUELS, GEN_COAL: None},
        {key: value for key, value in FUELS.items() if key != GEN_COAL},
    )
    for fuels in variants:
        result = _supply([_gen(GEN_COAL), _gen(GEN_FUEL)], supply, fuels=fuels)
        coal = _verdict(result, GEN_COAL)
        assert coal.verdict == fuel.VERDICT_INDETERMINATE
        assert fuel.REASON_FUELS_UNREAD in coal.reasons
        assert coal.accepted_fuels == ()
        assert coal.headline_fuel is None
        # A class whose fuels are unread may burn anyone's fuel, so no other
        # class's supply can be proven its own.
        other = _verdict(result, GEN_FUEL)
        assert other.verdict == fuel.VERDICT_INDETERMINATE
        assert other.reasons == (fuel.REASON_FUEL_SHARING_UNKNOWN,)


@pytest.mark.parametrize("entry", [[COAL], (COAL, 7), ()])
def test_a_malformed_fuel_list_is_unread(entry: object) -> None:
    fuels = {**FUELS, GEN_COAL: entry}
    result = _supply(
        [_gen(GEN_COAL)],
        _flow(_maker(R_COAL)),
        fuels=fuels,  # type: ignore[arg-type]
    )
    assert _verdict(result, GEN_COAL).reasons == (fuel.REASON_FUELS_UNREAD,)


def test_a_raw_fuel_supply_is_indeterminate() -> None:
    result = _supply([_gen(GEN_COAL)], _flow(_maker(R_EAT_COAL), raw=(COAL,)))
    assert result.flow_complete is True
    verdict = _verdict(result, GEN_COAL)
    assert verdict.verdict == fuel.VERDICT_INDETERMINATE
    assert fuel.REASON_SUPPLY_RAW in verdict.reasons
    assert _line(verdict, COAL).supply_per_minute is None
    assert verdict.pooled_megawatts is None


@pytest.mark.parametrize(
    ("class_name", "kind"),
    [
        (GEN_CYCLING_FUEL, GAP_PRODUCTION_VARIABLE),
        (GEN_SILENT, GAP_PRODUCTION_UNDECLARED),
        (GEN_UNREGISTERED, GAP_NO_REGISTRY_ENTRY),
        (GEN_INEXACT, GAP_PRODUCTION_INEXACT),
    ],
)
def test_a_production_gap_is_indeterminate(class_name: str, kind: str) -> None:
    result = _supply([_gen(class_name)], _flow(*[_maker(R_FUEL)] * 9, *[_maker(R_COAL)] * 9))
    verdict = _verdict(result, class_name)
    assert verdict.verdict == fuel.VERDICT_INDETERMINATE
    assert fuel.REASON_PRODUCTION_GAP in verdict.reasons
    assert verdict.production_gap_kind == kind
    assert verdict.nameplate_megawatts is None
    assert verdict.demand_megawatts is None


# ---------------------------------------------------------------------------
# The flow is the world's own; a machine no flow can measure is judged by
# what its class could make
# ---------------------------------------------------------------------------


def test_the_audit_takes_no_flow_so_none_from_another_population_can_decide() -> None:
    # Both counter-examples a caller-supplied flow allowed - a flow over the
    # recipe machines alone, and one over an unrelated population - need a
    # flow parameter. There is none: the audit builds the world's own.
    parameters = inspect.signature(fuel.fuel_supply_of).parameters
    assert "flow" not in parameters
    assert "recipes" in parameters
    assert "extractable" in parameters
    assert "registered" in parameters


def test_a_miner_makes_only_the_fuels_it_could_extract_unmeasured() -> None:
    # The first adversary's counter-example: a miner beside a coal generator
    # and a coal eater. The miner's node is unknown, so coal - which it can
    # extract - is unmeasured; coke, which no extractor yields, is a measured
    # zero beside it.
    result = _audit(_world([_gen(GEN_COAL), _miner(), _maker(R_EAT_COAL)]))
    assert result.flow_complete is True
    verdict = _verdict(result, GEN_COAL)
    assert verdict.verdict == fuel.VERDICT_INDETERMINATE
    assert verdict.reasons == (fuel.REASON_SUPPLY_UNMEASURED,)
    assert verdict.shortfall_megawatts is None
    assert verdict.pooled_megawatts is None
    assert _line(verdict, COAL).supply_per_minute is None
    assert _line(verdict, COAL).shortfall_per_minute is None
    assert _line(verdict, COKE).supply_per_minute == Fraction(0)
    # The demand rests on nothing the flow measures, so it is still published.
    assert verdict.demand_megawatts == COAL_GEN_MW


@pytest.mark.parametrize(
    ("clock", "expected"),
    [(Fraction(1), fuel.VERDICT_REJECT), (Fraction(1, 3), fuel.VERDICT_FIRE)],
)
def test_a_refinery_made_fuel_decides_beside_a_miner(clock: Fraction, expected: str) -> None:
    # No extractor yields the liquid fuel, so the miner never touches it.
    refineries = [_maker(R_FUEL, clock), _maker(R_FUEL, clock)]
    verdict = _verdict(_audit(_world([_gen(GEN_FUEL), *refineries, _miner()])), GEN_FUEL)
    supply_mw = 2 * clock * FUEL_M3_PER_MAKER * FUEL_MJ_PER_M3 / SIXTY
    assert verdict.verdict == expected
    assert verdict.reasons == ()
    assert verdict.pooled_megawatts == supply_mw
    if expected == fuel.VERDICT_FIRE:
        assert verdict.shortfall_megawatts == FUEL_GEN_MW - supply_mw


@pytest.mark.parametrize("census", ["unadmitted_read", "unadmitted_unread"])
@pytest.mark.parametrize("class_name", [LAMP, BELT, FOUNDATION, SINK])
def test_a_census_record_of_a_class_that_makes_no_fuel_never_blocks_a_verdict(
    class_name: str, census: str
) -> None:
    # The second adversary's counter-example: one lamp record in the census
    # turned a covered fuel generator indeterminate on every real save.
    counts = ((class_name, 1),)
    world = _world(
        [_gen(GEN_FUEL), _maker(R_FUEL), _maker(R_FUEL)],
        unadmitted_read=counts if census == "unadmitted_read" else (),
        unadmitted_unread=counts if census == "unadmitted_unread" else (),
    )
    verdict = _verdict(_audit(world), GEN_FUEL)
    assert verdict.verdict == fuel.VERDICT_REJECT
    assert verdict.reasons == ()


@pytest.mark.parametrize("class_name", [LAMP, SINK])
def test_a_recipe_less_machine_that_makes_no_fuel_never_blocks_a_verdict(class_name: str) -> None:
    world = _world([_gen(GEN_COAL), _maker(R_COAL), _recipe_less(class_name)])
    verdict = _verdict(_audit(world), GEN_COAL)
    assert verdict.verdict == fuel.VERDICT_REJECT
    assert verdict.pooled_megawatts == COAL_PER_MAKER * COAL_MJ / SIXTY


@pytest.mark.parametrize(
    ("class_name", "unmeasured"),
    [
        (MINER, frozenset({COAL})),
        (MAKER, frozenset({COAL, COKE})),
        (REFINERY, frozenset({FUEL})),
    ],
)
def test_a_census_record_makes_only_the_fuels_its_class_could_make_unmeasured(
    class_name: str, unmeasured: frozenset[str]
) -> None:
    # Without the record both classes reject: coal at 150 MW against 75, fuel
    # at 250 MW against 250.
    world = _world(
        [_gen(GEN_COAL), _gen(GEN_FUEL), _maker(R_COAL), _maker(R_FUEL), _maker(R_FUEL)],
        unadmitted_unread=((class_name, 1),),
    )
    result = _audit(world)
    for generator in (GEN_COAL, GEN_FUEL):
        verdict = _verdict(result, generator)
        hit = unmeasured & set(verdict.accepted_fuels)
        if hit:
            assert verdict.verdict == fuel.VERDICT_INDETERMINATE
            assert verdict.reasons == (fuel.REASON_SUPPLY_UNMEASURED,)
        else:
            assert verdict.verdict == fuel.VERDICT_REJECT
        for line in verdict.fuels:
            assert (line.supply_per_minute is None) == (line.item_key in unmeasured)


@pytest.mark.parametrize("where", ["machine", "census"])
@pytest.mark.parametrize("class_name", [UNREGISTERED, ""])
def test_an_unregistered_recipe_less_class_makes_every_fuel_unmeasured(
    class_name: str, where: str
) -> None:
    # The correctness adversary's P3: an unknown recipe-less class beside a
    # coal generator and five coal makers (750 MW against 75) was taken to make
    # and eat nothing, and REJECTED. It may be a generator burning coal; an
    # unreadable class name may be anything. Neither is assumed inert.
    makers = [_maker(R_COAL)] * 5
    if where == "machine":
        world = _world([_gen(GEN_COAL), *makers, _recipe_less(class_name)])
    else:
        world = _world([_gen(GEN_COAL), *makers], unadmitted_unread=((class_name, 1),))
    # An unreadable name stays unknown even if some input lists the empty name.
    verdict = _verdict(_audit(world, registered=REGISTERED | {""}), GEN_COAL)
    assert verdict.verdict == fuel.VERDICT_INDETERMINATE
    assert verdict.reasons == (fuel.REASON_CLASS_UNREGISTERED,)
    assert all(line.supply_per_minute is None for line in verdict.fuels)
    assert verdict.pooled_megawatts is None


@pytest.mark.parametrize("registered", [frozenset(), {LAMP}, (LAMP,), None])
def test_only_a_registered_class_is_taken_to_make_no_fuel(registered: object) -> None:
    # The lamp that rejects above is inert only because it is registered: left
    # out, or named in anything but a frozenset, it is an unknown class.
    world = _world([_gen(GEN_FUEL), _maker(R_FUEL), _maker(R_FUEL)], unadmitted_read=((LAMP, 1),))
    verdict = _verdict(_audit(world, registered=registered), GEN_FUEL)
    assert verdict.verdict == fuel.VERDICT_INDETERMINATE
    assert verdict.reasons == (fuel.REASON_CLASS_UNREGISTERED,)


@pytest.mark.parametrize("class_name", [GEN_GEO, GEN_UNREGISTERED])
def test_a_generator_class_in_the_census_is_registered_by_its_namespace(class_name: str) -> None:
    # GEN_GEO is named only by the generator namespace, GEN_UNREGISTERED only
    # by the accepted-fuel input; either is enough to register the class, so
    # neither blocks a class it shares no fuel with.
    assert (class_name in GENERATORS) != (class_name in FUELS)
    world = _world(
        [_gen(GEN_FUEL), _maker(R_FUEL), _maker(R_FUEL)], unadmitted_read=((class_name, 1),)
    )
    verdict = _verdict(_audit(world, registered=frozenset()), GEN_FUEL)
    assert verdict.verdict == fuel.VERDICT_REJECT
    assert verdict.reasons == ()


def _unresolved_fuel_recipe() -> Mapping[str, Recipe]:
    unresolved = replace(
        RECIPES[R_FUEL], unresolved_produced_in=("Build_SyntheticUnresolvedQx85_C",)
    )
    return {**RECIPES, R_FUEL: unresolved}


@pytest.mark.parametrize(
    ("recipes", "extractable"),
    [
        (RECIPES, {key: value for key, value in EXTRACTABLE.items() if key != FUEL}),
        (RECIPES, {**EXTRACTABLE, FUEL: None}),
        # A list is not the stated frozenset, so it states nothing.
        (RECIPES, {**EXTRACTABLE, FUEL: [MINER]}),
        (_unresolved_fuel_recipe(), EXTRACTABLE),
    ],
    ids=[
        "extraction-absent",
        "extraction-none",
        "extraction-malformed",
        "recipe-producer-unresolved",
    ],
)
def test_a_fuel_whose_makers_are_unknown_is_unmeasured_beside_an_unmeasurable_record(
    recipes: Mapping[str, Recipe], extractable: Mapping[str, frozenset[str] | None]
) -> None:
    # Whether a lamp could make the fuel cannot be ruled out when nobody
    # stated every class that makes it. With no unmeasurable record at all,
    # the same unknown decides nothing.
    machines = [_gen(GEN_FUEL), _maker(R_FUEL), _maker(R_FUEL)]
    blocked = _audit(
        _world(machines, unadmitted_read=((LAMP, 1),)), recipes=recipes, extractable=extractable
    )
    assert _verdict(blocked, GEN_FUEL).reasons == (fuel.REASON_SUPPLY_UNMEASURED,)
    clear = _audit(_world(machines), recipes=recipes, extractable=extractable)
    assert _verdict(clear, GEN_FUEL).verdict == fuel.VERDICT_REJECT


@pytest.mark.parametrize(
    "unflowable",
    [
        MachineState(class_name=REFINERY, producing=True, recipe_class_name=R_FUEL, overclock=None),
        MachineState(
            class_name=REFINERY,
            producing=True,
            recipe_class_name=R_FUEL,
            overclock=Fraction(1),
            production_boost_tagged=True,
        ),
    ],
    ids=["clock-unread", "boosted"],
)
def test_a_world_machine_a_flow_would_gap_is_never_rated(unflowable: MachineState) -> None:
    # The correctness adversary's P8: a flow rating this machine at clock one
    # REJECTED at 150 MW. The audit's own flow gaps it.
    result = _audit(_world([_gen(GEN_COAL), _maker(R_COAL), unflowable]))
    assert result.flow_complete is False
    verdict = _verdict(result, GEN_COAL)
    assert verdict.verdict == fuel.VERDICT_INDETERMINATE
    assert verdict.reasons == (fuel.REASON_FLOW_INCOMPLETE,)
    assert verdict.pooled_megawatts == COAL_PER_MAKER * COAL_MJ / SIXTY


@pytest.mark.parametrize("clock", [Fraction(1), Fraction(0)])
def test_a_world_of_generators_alone_reaches_no_verdict(clock: Fraction) -> None:
    # The correctness adversary's P1: an unrelated flow FIRED at 75 MW, and
    # REJECTED for a clock-zero generator. The world's own flow moves nothing,
    # which the flow model names incomplete.
    result = _audit(_world([_gen(GEN_COAL, clock)]))
    assert result.flow_complete is False
    verdict = _verdict(result, GEN_COAL)
    assert verdict.verdict == fuel.VERDICT_INDETERMINATE
    assert verdict.reasons == (fuel.REASON_FLOW_INCOMPLETE,)


def test_a_generator_class_machine_naming_a_recipe_is_in_the_flow() -> None:
    # The correctness adversary's P2: the generator's own coal recipe was left
    # out of the flow, which FIRED a 75 MW shortfall. Counted, it makes 30 a
    # minute against the eater's 10: 20 a minute, 100 MW, covering 75.
    producing_generator = MachineState(
        class_name=GEN_COAL, producing=True, recipe_class_name=R_COAL, overclock=Fraction(1)
    )
    verdict = _verdict(_audit(_world([producing_generator, _maker(R_EAT_COAL)])), GEN_COAL)
    net = COAL_PER_MAKER - COAL_EATEN_PER_MAKER
    assert verdict.demand_megawatts == COAL_GEN_MW
    assert _line(verdict, COAL).supply_per_minute == net
    assert verdict.pooled_megawatts == net * COAL_MJ / SIXTY
    assert verdict.verdict == fuel.VERDICT_REJECT


def test_unreadable_fuels_name_an_unmeasured_supply_too() -> None:
    world = _world([_gen(GEN_COAL), _miner(), _maker(R_COAL)])
    result = _audit(world, fuels={**FUELS, GEN_COAL: None})
    assert _verdict(result, GEN_COAL).reasons == (
        fuel.REASON_FUELS_UNREAD,
        fuel.REASON_SUPPLY_UNMEASURED,
    )
    world = _world([_gen(GEN_COAL), _recipe_less(UNREGISTERED), _maker(R_COAL)])
    result = _audit(world, fuels={**FUELS, GEN_COAL: None})
    assert _verdict(result, GEN_COAL).reasons == (
        fuel.REASON_FUELS_UNREAD,
        fuel.REASON_CLASS_UNREGISTERED,
    )


def test_the_worlds_own_flow_rates_an_elided_clock_and_gaps_the_rest() -> None:
    elided = MachineState(
        class_name=MAKER,
        producing=True,
        recipe_class_name=R_COAL,
        overclock=None,
        overclock_elided=True,
    )
    boosted = MachineState(
        class_name=MAKER,
        producing=True,
        recipe_class_name=R_COAL,
        overclock=Fraction(1),
        production_boost_tagged=True,
    )
    decided = _verdict(_audit(_world([_gen(GEN_COAL), elided])), GEN_COAL)
    assert decided.verdict == fuel.VERDICT_REJECT
    assert decided.pooled_megawatts == COAL_PER_MAKER * ELIDED_CLOCK_DEFAULT * COAL_MJ / SIXTY

    world = _world([_gen(GEN_COAL), elided, boosted, _maker(R_UNKNOWN)])
    assert _verdict(_audit(world), GEN_COAL).reasons == (fuel.REASON_FLOW_INCOMPLETE,)


# ---------------------------------------------------------------------------
# Scope
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("class_name", [GEN_GEO, GEN_GEO_RATED])
def test_geothermal_is_out_of_scope(class_name: str) -> None:
    # The geothermal shape: NO fuel declared - the class is absent from the
    # accepted-fuel input - on a variable-output entry. GEN_GEO_RATED declares a
    # NONZERO output, so only the variable-production check puts it out.
    assert class_name not in FUELS
    assert GENERATORS[class_name].is_variable_production
    result = _supply([_gen(class_name), _gen(GEN_COAL)], _flow(_maker(R_COAL)))
    assert result.out_of_scope == (class_name,)
    assert all(entry.class_name != class_name for entry in result.verdicts)
    assert all(entry.class_name != class_name for entry in result.demands)
    # It burns nothing, so it never makes another class's supply unknown.
    assert _verdict(result, GEN_COAL).verdict == fuel.VERDICT_REJECT


def test_a_zero_output_generator_with_no_fuel_is_out_of_scope() -> None:
    result = _supply([_gen(GEN_ZERO)], _flow(_maker(R_COAL)))
    assert result.out_of_scope == (GEN_ZERO,)
    assert result.verdicts == ()


@pytest.mark.parametrize("class_name", [GEN_GEO, GEN_GEO_RATED, GEN_ZERO])
@pytest.mark.parametrize("entry", [None, (), [COAL], (COAL, 7)])
def test_an_unreadable_fuel_list_is_never_out_of_scope(class_name: str, entry: object) -> None:
    # A fuel list that IS declared but cannot be read is not "burns nothing":
    # the class may burn anything, so it is indeterminate, and every other class
    # loses the proof that its supply is its own. The geothermal shape of the
    # entry decides nothing once a fuel list is declared.
    fuels = {**FUELS, class_name: entry}
    result = _supply(
        [_gen(class_name), _gen(GEN_COAL)],
        _flow(_maker(R_COAL)),
        fuels=fuels,  # type: ignore[arg-type]
    )
    assert result.out_of_scope == ()
    verdict = _verdict(result, class_name)
    assert verdict.verdict == fuel.VERDICT_INDETERMINATE
    assert fuel.REASON_FUELS_UNREAD in verdict.reasons
    assert verdict.accepted_fuels == ()
    assert _demand(result.demands, class_name).complete is False
    coal = _verdict(result, GEN_COAL)
    assert coal.verdict == fuel.VERDICT_INDETERMINATE
    assert coal.reasons == (fuel.REASON_FUEL_SHARING_UNKNOWN,)


def test_non_generator_classes_are_ignored() -> None:
    result = _supply([_gen(GEN_COAL)], _flow(_maker(R_COAL)))
    assert tuple(entry.class_name for entry in result.verdicts) == (GEN_COAL,)
    assert result.out_of_scope == ()


def test_supplemental_resources_and_byproducts_are_named_exclusions() -> None:
    result = _supply([_gen(GEN_COAL)], _flow(_maker(R_COAL)))
    assert result.exclusions == (fuel.EXCLUDED_SUPPLEMENTAL, fuel.EXCLUDED_BYPRODUCT)
    for code in result.exclusions:
        detail = fuel.EXCLUSION_DETAIL[code]
        assert detail.isascii()
        assert detail.strip()


def test_every_reason_is_closed_vocabulary_with_a_detail_line() -> None:
    assert set(fuel.DEMAND_REASONS) <= set(fuel.INDETERMINATE_REASONS)
    assert set(fuel.REASON_DETAIL) == set(fuel.INDETERMINATE_REASONS)
    for detail in fuel.REASON_DETAIL.values():
        assert detail.isascii()
        assert detail.strip()


# ---------------------------------------------------------------------------
# The demand-only result
# ---------------------------------------------------------------------------


def test_demand_card_states_burn_per_fuel() -> None:
    supply = _flow(_maker(R_COAL), _maker(R_UNKNOWN))
    result = _supply([_gen(GEN_COAL), _gen(GEN_COAL, Fraction(1, 2))], supply)
    assert _verdict(result, GEN_COAL).verdict == fuel.VERDICT_INDETERMINATE
    demand = _demand(result.demands, GEN_COAL)
    demand_mw = COAL_GEN_MW * Fraction(3, 2)
    assert demand.complete is True
    assert demand.demand_megawatts == demand_mw
    assert demand.headline_fuel == COAL
    assert tuple(burn.item_key for burn in demand.burns) == (COAL, COKE)
    assert _burn(demand, COAL).burn_per_minute == demand_mw * SIXTY / COAL_MJ
    assert _burn(demand, COKE).burn_per_minute == demand_mw * SIXTY / COKE_MJ
    # The same result whether or not a flow exists - it claims nothing about one.
    alone = fuel.fuel_demand_of(
        _world([_gen(GEN_COAL), _gen(GEN_COAL, Fraction(1, 2))]), GENERATORS, FUELS, ITEMS
    )
    assert alone == result.demands


def test_the_demand_types_declare_no_supply_field() -> None:
    for kind in (fuel.FuelDemand, fuel.FuelBurn):
        names = {field.name for field in fields(kind)}
        assert not any("supply" in name or "shortfall" in name for name in names)


def test_the_demand_ignores_supply_side_reasons() -> None:
    result = _supply([_gen(GEN_COAL), _gen(GEN_COKE)], _flow(_maker(R_UNKNOWN), raw=(COAL,)))
    demand = _demand(result.demands, GEN_COAL)
    assert demand.complete is True
    assert demand.reasons == ()


# ---------------------------------------------------------------------------
# Trace and exactness
# ---------------------------------------------------------------------------


def test_the_trace_carries_every_figure_a_fire_rests_on() -> None:
    maker_clock = Fraction(1, 3)
    verdict = _verdict(_supply([_gen(GEN_FUEL)], _flow(_maker(R_FUEL, maker_clock))), GEN_FUEL)
    values = {(step.label, step.subject): step.value for step in verdict.trace}
    assert values[fuel.LABEL_NAMEPLATE, GEN_FUEL] == FUEL_GEN_MW
    assert values[fuel.LABEL_CLOCK_SUM, GEN_FUEL] == Fraction(1)
    assert values[fuel.LABEL_DEMAND, GEN_FUEL] == FUEL_GEN_MW
    assert values[fuel.LABEL_ENERGY_VALUE, FUEL] == FUEL_MJ_PER_LITRE
    assert values[fuel.LABEL_MEGAJOULES_PER_UNIT, FUEL] == FUEL_MJ_PER_M3
    assert values[fuel.LABEL_NET_FLOW, FUEL] == FUEL_M3_PER_MAKER * maker_clock
    assert values[fuel.LABEL_SUPPLY, FUEL] == FUEL_M3_PER_MAKER * maker_clock
    assert values[fuel.LABEL_SUPPLY_MEGAWATTS, FUEL] == verdict.pooled_megawatts
    assert values[fuel.LABEL_POOLED, GEN_FUEL] == verdict.pooled_megawatts
    assert values[fuel.LABEL_SHORTFALL, GEN_FUEL] == verdict.shortfall_megawatts
    assert values[fuel.LABEL_SHORTFALL_RATE, FUEL] == _line(verdict, FUEL).shortfall_per_minute
    assert all(step.kind in (fuel.STEP_READ, fuel.STEP_COMPUTED) for step in verdict.trace)
    assert all(type(step.value) is Fraction for step in verdict.trace)
    assert all(step.label.isascii() for step in verdict.trace)


def test_the_trace_is_deterministic() -> None:
    def build() -> fuel.WorldFuel:
        return _supply(
            [_gen(GEN_COAL), _gen(GEN_FUEL, Fraction(1, 2))],
            _flow(_maker(R_COAL), _maker(R_FUEL)),
        )

    assert build() == build()


def _floats(value: object, path: str = "result") -> list[str]:
    if type(value) is float:
        return [path]
    if is_dataclass(value) and not isinstance(value, type):
        found: list[str] = []
        for field in fields(value):
            found += _floats(getattr(value, field.name), f"{path}.{field.name}")
        return found
    if isinstance(value, Mapping):
        found = []
        for key, member in value.items():
            found += _floats(key, f"{path}[key]") + _floats(member, f"{path}[{key!r}]")
        return found
    if isinstance(value, (tuple, list, set, frozenset)):
        found = []
        for index, member in enumerate(value):
            found += _floats(member, f"{path}[{index}]")
        return found
    return []


def test_no_float_in_any_result() -> None:
    worlds = [
        _supply([_gen(GEN_FUEL)], _flow(_maker(R_FUEL, Fraction(1, 3)))),
        _supply([_gen(GEN_COAL), _gen(GEN_COKE)], _flow(_maker(R_COKE))),
        _supply([_gen(GEN_COAL, 0.5)], _flow(_maker(R_COAL))),
        _supply([_gen(GEN_DUD), _gen(GEN_GEO)], _flow(_maker(R_UNKNOWN))),
        _supply([_gen(GEN_INEXACT), _gen(GEN_GAS)], _flow(_maker(R_COAL))),
        fuel.fuel_supply_of(
            _world([_gen(GEN_COAL), _maker(R_COAL)]),
            GENERATORS,
            FUELS,
            {**ITEMS, COAL: _item(COAL, FORM_SOLID, 300.0)},
            RECIPES,
            extractable=EXTRACTABLE,
            registered=REGISTERED,
        ),
        _supply([_gen(GEN_COAL)] * 2, _flow(_maker(R_COAL), _maker(R_COKE))),
    ]
    # The control: the walk sees a float when one is there.
    assert _floats(_gen(GEN_COAL, 0.5)) == ["result.overclock"]
    for result in worlds:
        assert _floats(result) == []
