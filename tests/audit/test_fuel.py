"""CS-1285 slice B v2: the fuel supply audit, per built fuel generator class, exact.

Every fixture here is a hand-built synthetic literal - invented items, invented
generators, invented recipes, an invented registry - authored in this module.
Nothing opens a save, a docs file or the install; see ``tests/audit/__init__.py``
for the four rules that bind every module in this directory.

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

THE BINDING v2 RULING (``docs/item_notes/phase5.md`` section CS-1285, the
session 134 ruling) is what the arms below grade:

- VERDICTS DECIDE FLUID FUELS ONLY. A solid fuel is never measured - players,
  vehicles, sinks and stations move solids, and every real save holds a
  player - so it carries ``solid-supply-unmodelled`` and a None supply. The
  coal verdict tests of the refuted candidate moved to the fluid fuel here.
- THE AUDIT TAKES ONLY THE MACHINES AND THE REGISTRY, plus the raw items. It
  builds the world's own flow, so no flow over another population can decide.
- A RECORD NO FLOW RATES - a recipe-less admitted machine, a generator
  included, or a census record - unmeasures a fuel when its class produces a
  registry recipe naming that fuel as input OR output, or can extract it. A
  generator's own fuel list is demand, never such a relation.
- THE MODULE FILTERS THE CENSUS. An unreadable class name, an untabled
  undeclared buildable, or an admitted machine of an undeclared class is
  UNREGISTERED and blocks every fuel. A declared class is judged by its
  relation. A tabled class, or any other census class, holds no fluid and is
  counted.

THE FOUR REFUTATIONS OF THE CANDIDATE each have a regression arm here, named in
the section that grades it: a caller flow that dropped the miners, census
records that blocked every verdict, a recipe-less eater nobody measured, and a
recipe-less generator a fuel recipe names.
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
    WARN_MALFORMED_BLOB,
    WARN_MALFORMED_GROUP,
    WARN_MISSING_DURATION,
    WARN_UNREADABLE_FUELS,
    Extractor,
    Generator,
    Item,
    Recipe,
    RecipeIO,
    Registry,
    RegistryWarning,
)

# ---------------------------------------------------------------------------
# Synthetic content
# ---------------------------------------------------------------------------

#: Invented fluid fuels, MJ per LITRE as the shipped docs declare a fluid.
FUEL: Final = "Desc_SyntheticFuelQx85_C"
TURBO: Final = "Desc_SyntheticTurboQx85_C"
BIO: Final = "Desc_SyntheticBioQx85_C"
GAS: Final = "Desc_SyntheticGasQx85_C"
#: A liquid fuel whose energy value is unknown.
DUD: Final = "Desc_SyntheticDudQx85_C"
#: A liquid no generator burns, the only resource the oil pump yields.
CRUDE: Final = "Desc_SyntheticCrudeQx85_C"

FUEL_MJ_PER_LITRE: Final = Fraction(3, 4)
TURBO_MJ_PER_LITRE: Final = Fraction(2)
BIO_MJ_PER_LITRE: Final = Fraction(3, 2)
GAS_MJ_PER_LITRE: Final = Fraction(1, 5)
FUEL_MJ_PER_M3: Final = FUEL_MJ_PER_LITRE * LITRES_PER_CUBIC_METRE
TURBO_MJ_PER_M3: Final = TURBO_MJ_PER_LITRE * LITRES_PER_CUBIC_METRE
BIO_MJ_PER_M3: Final = BIO_MJ_PER_LITRE * LITRES_PER_CUBIC_METRE

#: Invented solids: two fuels, the packaged fluid, and an ash.
COAL: Final = "Desc_SyntheticCoalQx85_C"
COKE: Final = "Desc_SyntheticCokeQx85_C"
CAN: Final = "Desc_SyntheticCanQx85_C"
ASH: Final = "Desc_SyntheticAshQx85_C"
COAL_MJ: Final = Fraction(300)
COKE_MJ: Final = Fraction(180)

#: Invented generator classes.
GEN_FUEL: Final = "Build_SyntheticFuelGenQx85_C"
GEN_TWIN: Final = "Build_SyntheticTwinGenQx85_C"
GEN_REVERSED: Final = "Build_SyntheticReversedGenQx85_C"
GEN_SHARE: Final = "Build_SyntheticShareGenQx85_C"
GEN_GAS: Final = "Build_SyntheticGasGenQx85_C"
GEN_DUD: Final = "Build_SyntheticDudGenQx85_C"
GEN_COAL: Final = "Build_SyntheticCoalGenQx85_C"
GEN_MIXED: Final = "Build_SyntheticMixedGenQx85_C"
#: A generator class a fuel recipe names - the fourth refutation's shape.
GEN_BURNER: Final = "Build_SyntheticBurnerGenQx85_C"
GEN_GEO: Final = "Build_SyntheticGeoGenQx85_C"
#: A variable-output generator whose declared output is NOT zero, so only the
#: variable-production check can put it out of scope.
GEN_GEO_RATED: Final = "Build_SyntheticRatedGeoGenQx85_C"
GEN_ZERO: Final = "Build_SyntheticZeroGenQx85_C"
GEN_CYCLING: Final = "Build_SyntheticCyclingGenQx85_C"
GEN_SILENT: Final = "Build_SyntheticSilentGenQx85_C"
GEN_INEXACT: Final = "Build_SyntheticInexactGenQx85_C"
#: A fixed-output generator carrying no fuel list at all.
GEN_BARE: Final = "Build_SyntheticBareGenQx85_C"
#: A generator whose fuel list the registry flagged unreadable.
GEN_GARBLED: Final = "Build_SyntheticGarbledGenQx85_C"

FUEL_GEN_MW: Final = Fraction(250)
TWIN_GEN_MW: Final = Fraction(150)
SHARE_GEN_MW: Final = Fraction(30)
DUD_GEN_MW: Final = Fraction(40)
COAL_GEN_MW: Final = Fraction(75)
MIXED_GEN_MW: Final = Fraction(100)
BURNER_GEN_MW: Final = Fraction(60)
GEO_RATED_MW: Final = Fraction(100)

#: Recipe-machine classes. The liquid fuel is made only in REFINERY and eaten
#: only in PACKAGER; every other recipe is produced in MAKER.
MAKER: Final = "Build_SyntheticMakerQx85_C"
REFINERY: Final = "Build_SyntheticRefineryQx85_C"
PACKAGER: Final = "Build_SyntheticPackagerQx85_C"

#: Extractors. No flow rates one; the registry says what each can yield.
MINER: Final = "Build_SyntheticMinerQx85_C"
WELL: Final = "Build_SyntheticWellQx85_C"
OIL_PUMP: Final = "Build_SyntheticOilPumpQx85_C"
FUEL_WELL: Final = "Build_SyntheticFuelWellQx85_C"
ODD_EXTRACTOR: Final = "Build_SyntheticOddExtractorQx85_C"

#: Declared classes that make and eat nothing: in no recipe's producers and no
#: extractor. A lamp and a sink can carry machine state; a belt and a
#: foundation reach the audit only through the census.
LAMP: Final = "Build_SyntheticLampQx85_C"
SINK: Final = "Build_SyntheticSinkQx85_C"
BELT: Final = "Build_SyntheticBeltQx85_C"
FOUNDATION: Final = "Build_SyntheticFoundationQx85_C"

#: Classes the registry does not declare.
PLAYER: Final = "Char_SyntheticPlayerQx85_C"
TRACTOR: Final = "BP_SyntheticTractorQx85_C"
MOD_BUILD: Final = "Build_SyntheticModQx85_C"
MOD_BUILD_SHOUTED: Final = "BUILD_SyntheticModQx85_C"
MOD_ACTOR: Final = "BP_SyntheticModQx85_C"

R_FUEL: Final = "Recipe_SyntheticFuelQx85_C"
R_TURBO: Final = "Recipe_SyntheticTurboQx85_C"
R_BIO: Final = "Recipe_SyntheticBioQx85_C"
R_GAS: Final = "Recipe_SyntheticGasQx85_C"
R_COAL: Final = "Recipe_SyntheticCoalQx85_C"
R_COKE: Final = "Recipe_SyntheticCokeQx85_C"
R_PACK: Final = "Recipe_SyntheticPackQx85_C"
R_BURN: Final = "Recipe_SyntheticBurnQx85_C"
R_UNKNOWN: Final = "Recipe_SyntheticNeverAuthoredQx85_C"

#: Per-minute rate of one recipe machine at clock one, re-derived: 60 / duration.
FUEL_M3_PER_REFINERY: Final = Fraction(60, 6)
TURBO_M3_PER_MAKER: Final = Fraction(60, 2)
BIO_M3_PER_MAKER: Final = Fraction(60, 2)
FUEL_M3_EATEN_PER_PACKAGER: Final = Fraction(60, 6)

SIXTY: Final = Fraction(60)

#: Ruling (c): how many undeclared build classes the session 137 probe found
#: over the pinned development world - eight plus the HUB's biomass burner.
PROBED_UNDECLARED_CLASS_COUNT: Final = 9


def _item(key: str, form: str, energy: object) -> Item:
    return Item(
        key=key,
        display_name=f"Synthetic {key}",
        form=form,
        energy_value=energy,  # type: ignore[arg-type]
        sink_points=None,
        is_fluid=form in (FORM_LIQUID, FORM_GAS),
    )


def _generator(key: str, production: object, fuels: object, *, variable: bool = False) -> Generator:
    return Generator(
        key=key,
        display_name=f"Synthetic {key}",
        power_production=production,  # type: ignore[arg-type]
        variable_production_constant=Fraction(0) if variable else None,
        variable_production_factor=Fraction(200) if variable else None,
        is_variable_production=variable,
        accepted_fuels=fuels,  # type: ignore[arg-type]
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


def _extractor(
    key: str, forms: frozenset[str], resources: object, *, odd: bool = False
) -> Extractor:
    return Extractor(
        key=key,
        display_name=f"Synthetic {key}",
        items_per_cycle=Fraction(1),
        extract_cycle_time=Fraction(1),
        allowed_forms=forms,
        unrecognized_forms=("RF_SYNTHETICQX85",) if odd else (),
        allowed_resources=resources,  # type: ignore[arg-type]
    )


ITEMS: Final[Mapping[str, Item]] = MappingProxyType(
    {
        FUEL: _item(FUEL, FORM_LIQUID, FUEL_MJ_PER_LITRE),
        TURBO: _item(TURBO, FORM_LIQUID, TURBO_MJ_PER_LITRE),
        BIO: _item(BIO, FORM_LIQUID, BIO_MJ_PER_LITRE),
        GAS: _item(GAS, FORM_GAS, GAS_MJ_PER_LITRE),
        DUD: _item(DUD, FORM_LIQUID, None),
        CRUDE: _item(CRUDE, FORM_LIQUID, None),
        COAL: _item(COAL, FORM_SOLID, COAL_MJ),
        COKE: _item(COKE, FORM_SOLID, COKE_MJ),
        CAN: _item(CAN, FORM_SOLID, None),
        ASH: _item(ASH, FORM_SOLID, None),
    }
)

#: The generator namespace. GEN_GEO, GEN_GEO_RATED and GEN_ZERO declare no
#: fuel on a variable or zero output - the geothermal shape; GEN_BARE declares
#: none on a fixed output; GEN_GARBLED's list is flagged unreadable below.
GENERATORS: Final[Mapping[str, Generator]] = MappingProxyType(
    {
        GEN_FUEL: _generator(GEN_FUEL, FUEL_GEN_MW, (FUEL,)),
        GEN_TWIN: _generator(GEN_TWIN, TWIN_GEN_MW, (TURBO, BIO)),
        GEN_REVERSED: _generator(GEN_REVERSED, TWIN_GEN_MW, (BIO, TURBO)),
        GEN_SHARE: _generator(GEN_SHARE, SHARE_GEN_MW, (TURBO,)),
        GEN_GAS: _generator(GEN_GAS, FUEL_GEN_MW, (GAS,)),
        GEN_DUD: _generator(GEN_DUD, DUD_GEN_MW, (DUD,)),
        GEN_COAL: _generator(GEN_COAL, COAL_GEN_MW, (COAL, COKE)),
        GEN_MIXED: _generator(GEN_MIXED, MIXED_GEN_MW, (FUEL, COAL)),
        GEN_BURNER: _generator(GEN_BURNER, BURNER_GEN_MW, (GAS,)),
        GEN_GEO: _generator(GEN_GEO, Fraction(0), None, variable=True),
        GEN_GEO_RATED: _generator(GEN_GEO_RATED, GEO_RATED_MW, None, variable=True),
        GEN_ZERO: _generator(GEN_ZERO, Fraction(0), None),
        GEN_CYCLING: _generator(GEN_CYCLING, Fraction(0), (FUEL,), variable=True),
        GEN_SILENT: _generator(GEN_SILENT, None, (FUEL,)),
        GEN_INEXACT: _generator(GEN_INEXACT, 75.0, (FUEL,)),
        GEN_BARE: _generator(GEN_BARE, Fraction(50), None),
        GEN_GARBLED: _generator(GEN_GARBLED, Fraction(60), None),
    }
)

RECIPES: Final[Mapping[str, Recipe]] = MappingProxyType(
    {
        R_FUEL: _recipe(R_FUEL, 6, (), ((FUEL, Fraction(1)),), REFINERY),
        R_TURBO: _recipe(R_TURBO, 2, (), ((TURBO, Fraction(1)),)),
        R_BIO: _recipe(R_BIO, 2, (), ((BIO, Fraction(1)),)),
        R_GAS: _recipe(R_GAS, 2, (), ((GAS, Fraction(1)),)),
        R_COAL: _recipe(R_COAL, 2, (), ((COAL, Fraction(1)),)),
        R_COKE: _recipe(R_COKE, 2, (), ((COKE, Fraction(1)),)),
        # The eater: the liquid fuel is this recipe's INPUT only.
        R_PACK: _recipe(R_PACK, 6, ((FUEL, Fraction(1)),), ((CAN, Fraction(1)),), PACKAGER),
        # A recipe produced in a GENERATOR class, naming the liquid fuel.
        R_BURN: _recipe(R_BURN, 6, ((FUEL, Fraction(1)),), ((ASH, Fraction(1)),), GEN_BURNER),
    }
)

EXTRACTORS: Final[Mapping[str, Extractor]] = MappingProxyType(
    {
        MINER: _extractor(MINER, frozenset({FORM_SOLID}), None),
        WELL: _extractor(WELL, frozenset({FORM_LIQUID, FORM_GAS}), None),
        OIL_PUMP: _extractor(OIL_PUMP, frozenset({FORM_LIQUID}), (CRUDE,)),
        FUEL_WELL: _extractor(FUEL_WELL, frozenset({FORM_LIQUID}), (FUEL,)),
        ODD_EXTRACTOR: _extractor(ODD_EXTRACTOR, frozenset(), None, odd=True),
    }
)

DECLARED: Final = frozenset(
    {
        *ITEMS,
        *GENERATORS,
        *RECIPES,
        *EXTRACTORS,
        MAKER,
        REFINERY,
        PACKAGER,
        LAMP,
        SINK,
        BELT,
        FOUNDATION,
    }
)

GARBLED_WARNING: Final = RegistryWarning(
    code=WARN_UNREADABLE_FUELS, subject=GEN_GARBLED, detail="synthetic unreadable fuel list"
)

REGISTRY: Final = Registry(
    items=ITEMS,
    recipes=RECIPES,
    buildings=MappingProxyType({}),
    warnings=(GARBLED_WARNING,),
    unknown_groups=(),
    extractors=EXTRACTORS,
    generators=GENERATORS,
    declared_classes=DECLARED,
)


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


def _recipe_less(class_name: str) -> MachineState:
    return MachineState(
        class_name=class_name, producing=True, recipe_class_name=None, overclock=Fraction(1)
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


def _registry(**changes: object) -> Registry:
    return replace(REGISTRY, **changes)  # type: ignore[arg-type]


def _with_generator(class_name: str, fuels: object) -> Registry:
    generators = dict(GENERATORS)
    generators[class_name] = replace(GENERATORS[class_name], accepted_fuels=fuels)  # type: ignore[arg-type]
    return _registry(generators=MappingProxyType(generators))


@dataclass(frozen=True)
class _Scene:
    """The machines of one world besides its generators, and what it declares raw."""

    makers: tuple[MachineState, ...]
    raw: tuple[str, ...]


def _flow(*makers: MachineState, raw: tuple[str, ...] = ()) -> _Scene:
    return _Scene(makers, raw)


def _audit(
    world: WorldMachines,
    registry: Registry = REGISTRY,
    *,
    raw: tuple[str, ...] = (),
) -> fuel.WorldFuel:
    return fuel.fuel_supply_of(world, registry, raw_items=raw)


def _supply(
    generators: list[MachineState],
    supply: _Scene,
    registry: Registry = REGISTRY,
    *,
    unadmitted_read: tuple[tuple[str, int], ...] = (),
    unadmitted_unread: tuple[tuple[str, int], ...] = (),
) -> fuel.WorldFuel:
    """Run the audit over ONE world: the generators plus every other machine."""
    world = _world(
        [*generators, *supply.makers],
        unadmitted_read=unadmitted_read,
        unadmitted_unread=unadmitted_unread,
    )
    return _audit(world, registry, raw=supply.raw)


def _demands(world: WorldMachines, registry: Registry = REGISTRY) -> tuple[fuel.FuelDemand, ...]:
    return fuel.fuel_demand_of(world, registry)


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


def _covered_fuel_world(
    *extra: MachineState, **census: tuple[tuple[str, int], ...]
) -> WorldMachines:
    """A liquid-fuel generator two refineries cover exactly, plus ``extra``."""
    return _world([_gen(GEN_FUEL), _maker(R_FUEL), _maker(R_FUEL), *extra], **census)


# ---------------------------------------------------------------------------
# Demand and burn arithmetic
# ---------------------------------------------------------------------------


def test_burn_is_exact_megawatts_times_sixty_over_energy() -> None:
    # The demand half decides nothing about supply, so a solid burner's burn is
    # stated in full even though no verdict ever measures its supply.
    clock = Fraction(2, 3)
    demand = _demand(_demands(_world([_gen(GEN_COAL, clock)])), GEN_COAL)
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
    burn = _burn(_demand(_demands(_world([_gen(GEN_FUEL)])), GEN_FUEL), FUEL)
    assert burn.unit == fuel.UNIT_CUBIC_METRE
    assert burn.megajoules_per_unit == FUEL_MJ_PER_M3
    # 250 MW * 60 / 750 MJ per m3 = 20 m3 per minute - never 20000 litres and
    # never the 1/50 that reading the per-litre value as per-m3 gives.
    assert burn.burn_per_minute == Fraction(20)


def test_unknown_energy_is_a_named_gap_never_zero() -> None:
    demand = _demand(_demands(_world([_gen(GEN_DUD)])), GEN_DUD)
    burn = _burn(demand, DUD)
    assert burn.megajoules_per_unit is None
    assert burn.burn_per_minute is None
    assert fuel.REASON_ENERGY_UNKNOWN in demand.reasons
    assert demand.complete is False

    verdict = _verdict(_supply([_gen(GEN_DUD)], _flow(_maker(R_FUEL))), GEN_DUD)
    assert verdict.verdict == fuel.VERDICT_INDETERMINATE
    assert verdict.reasons == (fuel.REASON_ENERGY_UNKNOWN,)
    assert verdict.pooled_megawatts is None
    # The fluid's volume is still measured; only its megawatts are unknown.
    assert _line(verdict, DUD).supply_per_minute == Fraction(0)
    assert _line(verdict, DUD).supply_megawatts is None


def test_an_item_the_registry_lacks_is_unknown_energy() -> None:
    registry = _with_generator(GEN_FUEL, ("Desc_SyntheticNeverAuthoredQx85_C",))
    demand = _demand(_demands(_world([_gen(GEN_FUEL)]), registry), GEN_FUEL)
    assert demand.reasons == (fuel.REASON_ENERGY_UNKNOWN,)
    assert demand.burns[0].unit is None
    assert demand.burns[0].burn_per_minute is None
    verdict = _verdict(_supply([_gen(GEN_FUEL)], _flow(_maker(R_FUEL)), registry), GEN_FUEL)
    assert verdict.reasons == (fuel.REASON_ENERGY_UNKNOWN,)
    # An item nobody described is not known to be a fluid, so nothing measures it.
    assert verdict.fuels[0].supply_per_minute is None


@pytest.mark.parametrize("energy", [Fraction(0), Fraction(-1), 2.0])
def test_a_zero_energy_value_is_unknown_never_a_division(energy: object) -> None:
    items = dict(ITEMS)
    items[TURBO] = _item(TURBO, FORM_LIQUID, energy)
    registry = _registry(items=MappingProxyType(items))
    demand = _demand(_demands(_world([_gen(GEN_TWIN)]), registry), GEN_TWIN)
    assert fuel.REASON_ENERGY_UNKNOWN in demand.reasons
    assert _burn(demand, TURBO).burn_per_minute is None
    assert _burn(demand, TURBO).megajoules_per_unit is None
    assert _burn(demand, BIO).burn_per_minute == TWIN_GEN_MW * SIXTY / BIO_MJ_PER_M3


@pytest.mark.parametrize("form", ["", "RF_INVALID"])
def test_an_unknown_form_is_unknown_energy(form: str) -> None:
    items = dict(ITEMS)
    items[FUEL] = _item(FUEL, form, FUEL_MJ_PER_LITRE)
    registry = _registry(items=MappingProxyType(items))
    burn = _burn(_demand(_demands(_world([_gen(GEN_FUEL)]), registry), GEN_FUEL), FUEL)
    assert burn.unit is None
    assert burn.burn_per_minute is None


def test_a_gas_fuel_burns_in_cubic_metres_too() -> None:
    burn = _burn(_demand(_demands(_world([_gen(GEN_GAS)])), GEN_GAS), GAS)
    assert burn.unit == fuel.UNIT_CUBIC_METRE
    assert burn.megajoules_per_unit == GAS_MJ_PER_LITRE * LITRES_PER_CUBIC_METRE
    assert burn.burn_per_minute == FUEL_GEN_MW * SIXTY / (GAS_MJ_PER_LITRE * 1000)


# ---------------------------------------------------------------------------
# Verdicts over a complete flow - fluid fuels
# ---------------------------------------------------------------------------


def test_fires_with_exact_shortfall_on_complete_flow() -> None:
    clock = Fraction(1, 3)
    verdict = _verdict(_supply([_gen(GEN_FUEL)], _flow(_maker(R_FUEL, clock))), GEN_FUEL)
    supply_m3 = FUEL_M3_PER_REFINERY * clock
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
    assert line.reasons == ()
    assert verdict.headline_fuel == FUEL


def test_a_covering_supply_floor_rejects() -> None:
    # Two refineries at clock one: 20 m3/min * 750 / 60 = 250 MW, exactly the demand.
    verdict = _verdict(_audit(_covered_fuel_world()), GEN_FUEL)
    assert verdict.pooled_megawatts == FUEL_GEN_MW
    assert verdict.verdict == fuel.VERDICT_REJECT
    assert verdict.shortfall_megawatts is None
    assert _line(verdict, FUEL).shortfall_per_minute is None

    over = _verdict(_supply([_gen(GEN_FUEL)], _flow(*[_maker(R_FUEL)] * 3)), GEN_FUEL)
    assert over.verdict == fuel.VERDICT_REJECT
    headroom = {step.label: step.value for step in over.trace}[fuel.LABEL_HEADROOM]
    assert headroom == 3 * FUEL_M3_PER_REFINERY * FUEL_MJ_PER_M3 / SIXTY - FUEL_GEN_MW


def test_a_generator_at_clock_zero_burns_nothing_and_rejects() -> None:
    result = _supply([_gen(GEN_FUEL, Fraction(0))], _flow(_maker(R_FUEL, Fraction(0))))
    verdict = _verdict(result, GEN_FUEL)
    assert verdict.demand_megawatts == Fraction(0)
    assert verdict.verdict == fuel.VERDICT_REJECT


def test_a_clock_zero_maker_fires() -> None:
    # Ruling (e): a maker at clock zero makes nothing, which is the nominal
    # answer, so the whole demand is the shortfall.
    verdict = _verdict(_supply([_gen(GEN_FUEL)], _flow(_maker(R_FUEL, Fraction(0)))), GEN_FUEL)
    assert verdict.verdict == fuel.VERDICT_FIRE
    assert verdict.shortfall_megawatts == FUEL_GEN_MW
    assert _line(verdict, FUEL).supply_per_minute == Fraction(0)


def test_a_repeated_fuel_pools_once() -> None:
    registry = _with_generator(GEN_TWIN, (TURBO, TURBO, BIO))
    clock = Fraction(1, 6)
    verdict = _verdict(_supply([_gen(GEN_TWIN)], _flow(_maker(R_TURBO, clock)), registry), GEN_TWIN)
    assert verdict.accepted_fuels == (TURBO, BIO)
    assert verdict.pooled_megawatts == TURBO_M3_PER_MAKER * clock * TURBO_MJ_PER_M3 / SIXTY


def test_pooled_fuels_cover_where_no_single_fuel_does() -> None:
    # Two twin generators demand 300 MW. One turbo maker at clock 3/20 moves
    # 9/2 m3/min -> 150 MW; one bio maker at 1/5 moves 6 m3/min -> 150 MW.
    # Neither alone covers 300 MW; pooled they do, exactly.
    supply = _flow(_maker(R_TURBO, Fraction(3, 20)), _maker(R_BIO, Fraction(1, 5)))
    verdict = _verdict(_supply([_gen(GEN_TWIN), _gen(GEN_TWIN)], supply), GEN_TWIN)
    demand = 2 * TWIN_GEN_MW
    assert _line(verdict, TURBO).supply_megawatts == Fraction(150)
    assert _line(verdict, BIO).supply_megawatts == Fraction(150)
    assert Fraction(150) < demand
    assert verdict.pooled_megawatts == demand
    assert verdict.verdict == fuel.VERDICT_REJECT


def test_n_instances_sum_demand_against_one_supply() -> None:
    clocks = (Fraction(1), Fraction(1, 2), Fraction(3, 2))
    maker_clock = Fraction(1, 10)
    result = _supply([_gen(GEN_TWIN, c) for c in clocks], _flow(_maker(R_TURBO, maker_clock)))
    verdict = _verdict(result, GEN_TWIN)
    demand = TWIN_GEN_MW * sum(clocks)
    turbo_mw = TURBO_M3_PER_MAKER * maker_clock * TURBO_MJ_PER_M3 / SIXTY
    assert verdict.instance_count == len(clocks)
    assert verdict.clock_sum == sum(clocks)
    assert verdict.demand_megawatts == demand
    # Bio is in no recipe of a complete flow, so its nominal supply is a
    # measured zero, not a gap.
    assert _line(verdict, BIO).supply_per_minute == Fraction(0)
    assert verdict.pooled_megawatts == turbo_mw
    shortfall = demand - turbo_mw
    assert verdict.verdict == fuel.VERDICT_FIRE
    assert verdict.shortfall_megawatts == shortfall
    assert _line(verdict, TURBO).shortfall_per_minute == shortfall * SIXTY / TURBO_MJ_PER_M3
    assert _line(verdict, BIO).shortfall_per_minute == shortfall * SIXTY / BIO_MJ_PER_M3


def test_recipe_consumption_leaves_only_the_net_for_generators() -> None:
    # Three refineries (30 m3/min) and two packagers (20 m3/min) leave 10.
    supply = _flow(*[_maker(R_FUEL)] * 3, *[_maker(R_PACK)] * 2)
    verdict = _verdict(_supply([_gen(GEN_FUEL)], supply), GEN_FUEL)
    net = 3 * FUEL_M3_PER_REFINERY - 2 * FUEL_M3_EATEN_PER_PACKAGER
    assert _line(verdict, FUEL).supply_per_minute == net
    assert verdict.pooled_megawatts == net * FUEL_MJ_PER_M3 / SIXTY
    assert verdict.verdict == fuel.VERDICT_FIRE


def test_a_negative_net_supplies_nothing_rather_than_a_debt() -> None:
    supply = _flow(*[_maker(R_PACK)] * 2, _maker(R_FUEL))
    verdict = _verdict(_supply([_gen(GEN_FUEL)], supply), GEN_FUEL)
    assert _line(verdict, FUEL).supply_per_minute == Fraction(0)
    assert verdict.pooled_megawatts == Fraction(0)


def test_the_headline_is_the_first_accepted_fuel_in_mfuel_order() -> None:
    verdict = _verdict(
        _supply([_gen(GEN_REVERSED)], _flow(_maker(R_TURBO, Fraction(0)))), GEN_REVERSED
    )
    assert verdict.verdict == fuel.VERDICT_FIRE
    assert verdict.accepted_fuels == (BIO, TURBO)
    assert verdict.headline_fuel == BIO
    assert tuple(line.item_key for line in verdict.fuels) == (BIO, TURBO)


def test_a_disjoint_class_keeps_its_verdict_beside_others() -> None:
    supply = _flow(_maker(R_FUEL), _maker(R_FUEL), _maker(R_TURBO, Fraction(1, 10)))
    result = _supply([_gen(GEN_FUEL), _gen(GEN_TWIN)], supply)
    assert _verdict(result, GEN_FUEL).verdict == fuel.VERDICT_REJECT
    assert _verdict(result, GEN_TWIN).verdict == fuel.VERDICT_FIRE


# ---------------------------------------------------------------------------
# Solid fuels are never measured (ruling (a))
# ---------------------------------------------------------------------------


def test_a_solid_fuel_is_never_measured() -> None:
    # Five coal makers would cover 75 MW ten times over on the flow's figure,
    # and coke is in no recipe, a measured zero for a fluid. Neither counts: a
    # player, a vehicle or a sink moves solids no flow sees.
    result = _supply([_gen(GEN_COAL)], _flow(*[_maker(R_COAL)] * 5, _maker(R_COKE)))
    assert result.flow_complete is True
    verdict = _verdict(result, GEN_COAL)
    assert verdict.verdict == fuel.VERDICT_INDETERMINATE
    assert verdict.reasons == (fuel.REASON_SOLID_SUPPLY_UNMODELLED,)
    for line in verdict.fuels:
        assert line.supply_per_minute is None
        assert line.supply_megawatts is None
        assert line.reasons == (fuel.REASON_SOLID_SUPPLY_UNMODELLED,)
    assert verdict.pooled_megawatts is None
    assert verdict.shortfall_megawatts is None
    # The demand rests on nothing the flow measures, so it is still published.
    assert verdict.demand_megawatts == COAL_GEN_MW
    assert _demand(result.demands, GEN_COAL).complete is True


def test_one_solid_fuel_keeps_a_fluid_class_from_a_verdict() -> None:
    verdict = _verdict(_supply([_gen(GEN_MIXED)], _flow(*[_maker(R_FUEL)] * 3)), GEN_MIXED)
    assert verdict.verdict == fuel.VERDICT_INDETERMINATE
    assert verdict.reasons == (fuel.REASON_SOLID_SUPPLY_UNMODELLED,)
    # The fluid's figure is still published; the solid's is not.
    assert _line(verdict, FUEL).supply_per_minute == 3 * FUEL_M3_PER_REFINERY
    assert _line(verdict, FUEL).reasons == ()
    assert _line(verdict, COAL).supply_per_minute is None
    assert verdict.pooled_megawatts is None


# ---------------------------------------------------------------------------
# Indeterminate - a named reason, never a verdict
# ---------------------------------------------------------------------------


def test_a_fuel_shared_by_two_classes_is_indeterminate() -> None:
    supply = _flow(_maker(R_TURBO), _maker(R_FUEL), _maker(R_FUEL))
    result = _supply([_gen(GEN_TWIN), _gen(GEN_SHARE), _gen(GEN_FUEL)], supply)
    twin = _verdict(result, GEN_TWIN)
    share = _verdict(result, GEN_SHARE)
    assert twin.verdict == share.verdict == fuel.VERDICT_INDETERMINATE
    assert twin.reasons == share.reasons == (fuel.REASON_FUEL_SHARED,)
    assert twin.shared_with == (GEN_SHARE,)
    assert share.shared_with == (GEN_TWIN,)
    assert twin.shortfall_megawatts is None
    # A class sharing nothing is untouched.
    assert _verdict(result, GEN_FUEL).verdict == fuel.VERDICT_REJECT
    assert _verdict(result, GEN_FUEL).shared_with == ()


def test_an_unread_clock_is_indeterminate() -> None:
    result = _supply([_gen(GEN_FUEL), _gen(GEN_FUEL, None)], _flow(*[_maker(R_FUEL)] * 9))
    verdict = _verdict(result, GEN_FUEL)
    assert verdict.verdict == fuel.VERDICT_INDETERMINATE
    assert verdict.reasons == (fuel.REASON_CLOCK_UNREAD,)
    assert verdict.clock_sum is None
    assert verdict.demand_megawatts is None
    demand = _demand(result.demands, GEN_FUEL)
    assert demand.demand_megawatts is None
    assert all(burn.burn_per_minute is None for burn in demand.burns)


def test_an_elided_clock_is_the_class_default_and_counted() -> None:
    states = [_gen(GEN_FUEL, None, elided=True), _gen(GEN_FUEL, Fraction(1, 2))]
    verdict = _verdict(_supply(states, _flow(*[_maker(R_FUEL)] * 3)), GEN_FUEL)
    assert verdict.elided_clock_count == 1
    assert verdict.clock_sum == ELIDED_CLOCK_DEFAULT + Fraction(1, 2)
    assert verdict.demand_megawatts == FUEL_GEN_MW * (ELIDED_CLOCK_DEFAULT + Fraction(1, 2))
    assert verdict.verdict == fuel.VERDICT_REJECT


@pytest.mark.parametrize("clock", [0.5, Fraction(-1, 2), 1])
def test_a_refused_clock_is_indeterminate(clock: object) -> None:
    verdict = _verdict(_supply([_gen(GEN_FUEL, clock)], _flow(*[_maker(R_FUEL)] * 9)), GEN_FUEL)
    assert verdict.verdict == fuel.VERDICT_INDETERMINATE
    assert verdict.reasons == (fuel.REASON_CLOCK_REFUSED,)
    assert verdict.clock_sum is None


def test_a_boosted_generator_is_indeterminate() -> None:
    result = _supply([_gen(GEN_FUEL, boosted=True)], _flow(*[_maker(R_FUEL)] * 9))
    verdict = _verdict(result, GEN_FUEL)
    assert verdict.verdict == fuel.VERDICT_INDETERMINATE
    assert verdict.reasons == (fuel.REASON_BOOST_UNMODELED,)
    assert verdict.demand_megawatts is None


def test_an_omitted_instance_is_indeterminate() -> None:
    omitted = 2
    result = _supply(
        [_gen(GEN_FUEL)], _flow(*[_maker(R_FUEL)] * 9), unadmitted_unread=((GEN_FUEL, omitted),)
    )
    verdict = _verdict(result, GEN_FUEL)
    assert verdict.omitted_count == omitted
    assert verdict.verdict == fuel.VERDICT_INDETERMINATE
    assert verdict.reasons == (fuel.REASON_INSTANCES_OMITTED,)
    assert verdict.demand_megawatts is None


def test_a_class_built_only_in_the_census_is_considered() -> None:
    result = _supply(
        [_gen(GEN_FUEL)], _flow(_maker(R_FUEL), _maker(R_FUEL)), unadmitted_read=((GEN_TWIN, 1),)
    )
    twin = _verdict(result, GEN_TWIN)
    assert twin.instance_count == 0
    assert twin.omitted_count == 1
    assert twin.reasons == (fuel.REASON_INSTANCES_OMITTED,)
    # A generator in the census is an omitted instance; its own fuel list is
    # demand, never a relation, so a class it shares no fuel with still decides.
    other = _verdict(result, GEN_FUEL)
    assert other.verdict == fuel.VERDICT_REJECT
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
    assert verdict.pooled_megawatts == FUEL_M3_PER_REFINERY / 3 * FUEL_MJ_PER_M3 / SIXTY
    assert verdict.demand_megawatts == FUEL_GEN_MW


def test_a_covering_floor_on_incomplete_flow_is_still_indeterminate() -> None:
    supply = _flow(*[_maker(R_FUEL)] * 5, _maker(R_UNKNOWN))
    verdict = _verdict(_supply([_gen(GEN_FUEL)], supply), GEN_FUEL)
    assert verdict.verdict == fuel.VERDICT_INDETERMINATE
    assert verdict.reasons == (fuel.REASON_FLOW_INCOMPLETE,)


@pytest.mark.parametrize("unread", [GEN_GARBLED, GEN_BARE])
def test_unreadable_fuels_are_indeterminate(unread: str) -> None:
    # GEN_GARBLED's list is flagged unreadable by the registry; GEN_BARE
    # carries no list on a fixed output, so it generates and must burn something.
    result = _supply([_gen(unread), _gen(GEN_FUEL)], _flow(_maker(R_FUEL), _maker(R_FUEL)))
    verdict = _verdict(result, unread)
    assert verdict.verdict == fuel.VERDICT_INDETERMINATE
    assert verdict.reasons == (fuel.REASON_FUELS_UNREAD,)
    assert verdict.accepted_fuels == ()
    assert verdict.headline_fuel is None
    # A class whose fuels are unread may burn anyone's fuel, so no other
    # class's supply can be proven its own.
    other = _verdict(result, GEN_FUEL)
    assert other.verdict == fuel.VERDICT_INDETERMINATE
    assert other.reasons == (fuel.REASON_FUEL_SHARING_UNKNOWN,)


@pytest.mark.parametrize("entry", [[FUEL], (FUEL, 7), ()])
def test_a_malformed_fuel_list_is_unread(entry: object) -> None:
    registry = _with_generator(GEN_FUEL, entry)
    verdict = _verdict(_supply([_gen(GEN_FUEL)], _flow(_maker(R_FUEL)), registry), GEN_FUEL)
    assert verdict.reasons == (fuel.REASON_FUELS_UNREAD,)


def test_a_raw_fuel_supply_is_indeterminate() -> None:
    result = _supply([_gen(GEN_FUEL)], _flow(_maker(R_PACK), raw=(FUEL,)))
    assert result.flow_complete is True
    verdict = _verdict(result, GEN_FUEL)
    assert verdict.verdict == fuel.VERDICT_INDETERMINATE
    assert verdict.reasons == (fuel.REASON_SUPPLY_RAW,)
    assert _line(verdict, FUEL).supply_per_minute is None
    assert _line(verdict, FUEL).reasons == (fuel.REASON_SUPPLY_RAW,)
    assert verdict.pooled_megawatts is None


@pytest.mark.parametrize(
    ("class_name", "kind"),
    [
        (GEN_CYCLING, GAP_PRODUCTION_VARIABLE),
        (GEN_SILENT, GAP_PRODUCTION_UNDECLARED),
        (GEN_INEXACT, GAP_PRODUCTION_INEXACT),
    ],
)
def test_a_production_gap_is_indeterminate(class_name: str, kind: str) -> None:
    verdict = _verdict(_supply([_gen(class_name)], _flow(*[_maker(R_FUEL)] * 9)), class_name)
    assert verdict.verdict == fuel.VERDICT_INDETERMINATE
    assert verdict.reasons == (fuel.REASON_PRODUCTION_GAP,)
    assert verdict.production_gap_kind == kind
    assert verdict.nameplate_megawatts is None
    assert verdict.demand_megawatts is None


# ---------------------------------------------------------------------------
# The world's own flow; records no flow rates are judged by their class
# ---------------------------------------------------------------------------


def test_the_audit_takes_only_machines_and_registry() -> None:
    # Ruling (f): the caller-supplied mappings go. No flow, accepted-fuel,
    # extraction or registered-class input remains for a caller to get wrong.
    parameters = inspect.signature(fuel.fuel_supply_of).parameters
    assert list(parameters) == ["machines", "registry", "raw_items"]
    assert parameters["raw_items"].kind is inspect.Parameter.KEYWORD_ONLY
    assert parameters["raw_items"].default == ()
    assert list(inspect.signature(fuel.fuel_demand_of).parameters) == ["machines", "registry"]


@pytest.mark.parametrize("extractor", [FUEL_WELL, WELL])
def test_an_extractor_that_could_yield_the_fuel_is_never_dropped(extractor: str) -> None:
    # REFUTATION 1 - a caller flow dropping miners. A flow over the recipe
    # machines alone left the extractor out, read the fuel as made only by
    # the flow and FIRED. The extractor's node is never in a save, so the fuel
    # it can yield - by its restriction, or by its forms when unrestricted -
    # is unmeasured.
    result = _audit(_world([_gen(GEN_FUEL), _maker(R_PACK), _recipe_less(extractor)]))
    verdict = _verdict(result, GEN_FUEL)
    assert verdict.verdict == fuel.VERDICT_INDETERMINATE
    assert verdict.reasons == (fuel.REASON_SUPPLY_UNMEASURED,)
    assert verdict.shortfall_megawatts is None
    assert verdict.pooled_megawatts is None
    assert _line(verdict, FUEL).supply_per_minute is None
    assert _line(verdict, FUEL).reasons == (fuel.REASON_SUPPLY_UNMEASURED,)
    assert result.flow_complete is True
    # The demand rests on nothing the flow measures, so it is still published.
    assert verdict.demand_megawatts == FUEL_GEN_MW


def test_an_oil_extractor_leaves_liquid_fuel_measured() -> None:
    # Ruling (d): the oil pump yields crude only, though its forms admit every
    # liquid, so the liquid fuel beside it is still measured and decides.
    verdict = _verdict(_audit(_covered_fuel_world(_recipe_less(OIL_PUMP))), GEN_FUEL)
    assert verdict.verdict == fuel.VERDICT_REJECT
    assert verdict.reasons == ()
    assert verdict.pooled_megawatts == FUEL_GEN_MW


def test_an_unrestricted_extractor_yields_every_item_of_its_forms() -> None:
    # The same pump with no restriction read falls back to its forms: every
    # liquid, the fuel included.
    extractors = dict(EXTRACTORS)
    extractors[OIL_PUMP] = replace(EXTRACTORS[OIL_PUMP], allowed_resources=None)
    registry = _registry(extractors=MappingProxyType(extractors))
    verdict = _verdict(_audit(_covered_fuel_world(_recipe_less(OIL_PUMP)), registry), GEN_FUEL)
    assert verdict.reasons == (fuel.REASON_SUPPLY_UNMEASURED,)


@pytest.mark.parametrize(
    ("clock", "expected"),
    [(Fraction(1), fuel.VERDICT_REJECT), (Fraction(1, 3), fuel.VERDICT_FIRE)],
)
def test_a_refinery_made_fuel_decides_beside_a_miner(clock: Fraction, expected: str) -> None:
    # The miner yields solids only, so it never touches the liquid fuel.
    refineries = [_maker(R_FUEL, clock), _maker(R_FUEL, clock)]
    verdict = _verdict(_audit(_world([_gen(GEN_FUEL), *refineries, _recipe_less(MINER)])), GEN_FUEL)
    supply_mw = 2 * clock * FUEL_M3_PER_REFINERY * FUEL_MJ_PER_M3 / SIXTY
    assert verdict.verdict == expected
    assert verdict.reasons == ()
    assert verdict.pooled_megawatts == supply_mw
    if expected == fuel.VERDICT_FIRE:
        assert verdict.shortfall_megawatts == FUEL_GEN_MW - supply_mw


def test_a_recipe_less_eater_unmeasures_its_fluid_fuel() -> None:
    # REFUTATION 3 - an unmeasured eater. The packager makes no fuel; its one
    # recipe EATS it. Idle in the census, or naming no recipe the save let us
    # read, it may be eating the fuel the refineries make, so the fuel is
    # unmeasured - the candidate counted only the recipes that MADE a fuel.
    for world in (
        _covered_fuel_world(_recipe_less(PACKAGER)),
        _covered_fuel_world(unadmitted_unread=((PACKAGER, 1),)),
    ):
        verdict = _verdict(_audit(world), GEN_FUEL)
        assert verdict.verdict == fuel.VERDICT_INDETERMINATE
        assert verdict.reasons == (fuel.REASON_SUPPLY_UNMEASURED,)
        assert _line(verdict, FUEL).supply_per_minute is None


@pytest.mark.parametrize("where", ["machine", "census"])
@pytest.mark.parametrize("resolved", [True, False], ids=["produced-in", "unresolved-token"])
def test_a_recipe_less_generator_a_fuel_recipe_names_unmeasures_it(
    where: str, resolved: bool
) -> None:
    # REFUTATION 4 - a generator with no recipe. GEN_BURNER burns gas, but a
    # registry recipe produced in its class eats the liquid fuel. A recipe-less
    # record of it may be running that recipe, so the liquid fuel is
    # unmeasured; the candidate skipped every generator-class record. A
    # generator is not a modelled building, so the realistic token is an
    # unresolved one; both spellings relate the class.
    recipes = dict(RECIPES)
    if not resolved:
        recipes[R_BURN] = replace(
            RECIPES[R_BURN], produced_in=(), unresolved_produced_in=(GEN_BURNER,)
        )
    registry = _registry(recipes=MappingProxyType(recipes))
    if where == "machine":
        world = _covered_fuel_world(_gen(GEN_BURNER))
    else:
        world = _covered_fuel_world(unadmitted_unread=((GEN_BURNER, 1),))
    verdict = _verdict(_audit(world, registry), GEN_FUEL)
    assert verdict.verdict == fuel.VERDICT_INDETERMINATE
    assert verdict.reasons == (fuel.REASON_SUPPLY_UNMEASURED,)
    assert _line(verdict, FUEL).supply_per_minute is None


def test_a_generators_own_fuel_list_is_demand_never_relation() -> None:
    # Every generator record names no recipe, so each is judged by its class's
    # relations. GEN_BURNER's recipe names the liquid fuel, not the gas it
    # burns, so its gas still decides: 30 m3/min * 200 MJ / 60 = 100 MW
    # against 60. Were a fuel list a relation, no generator could ever decide.
    verdict = _verdict(_audit(_world([_gen(GEN_BURNER), _maker(R_GAS)])), GEN_BURNER)
    assert verdict.verdict == fuel.VERDICT_REJECT
    assert verdict.reasons == ()
    assert _line(verdict, GAS).supply_per_minute == Fraction(30)


@pytest.mark.parametrize("census", ["unadmitted_read", "unadmitted_unread"])
@pytest.mark.parametrize("class_name", [PLAYER, TRACTOR])
def test_a_non_buildable_census_record_never_blocks_a_fluid_verdict(
    class_name: str, census: str
) -> None:
    # REFUTATION 2 - vacuity on census records. One player record in the
    # census - and every real save holds one - turned a covered fuel generator
    # indeterminate. An undeclared class that is no buildable holds no fluid.
    records = 3
    world = _covered_fuel_world(**{census: ((class_name, records),)})
    result = _audit(world)
    verdict = _verdict(result, GEN_FUEL)
    assert verdict.verdict == fuel.VERDICT_REJECT
    assert verdict.reasons == ()
    assert result.no_fluid_record_count == records
    assert result.unregistered_record_count == 0


@pytest.mark.parametrize("census", ["unadmitted_read", "unadmitted_unread"])
@pytest.mark.parametrize("class_name", [LAMP, BELT, FOUNDATION, SINK])
def test_a_declared_census_record_relating_to_no_fuel_never_blocks_a_verdict(
    class_name: str, census: str
) -> None:
    # REFUTATION 2, the declared half: a lamp or a belt in the census marked
    # every fuel unmeasured, so no real save could reach a verdict.
    result = _audit(_covered_fuel_world(**{census: ((class_name, 1),)}))
    verdict = _verdict(result, GEN_FUEL)
    assert verdict.verdict == fuel.VERDICT_REJECT
    assert verdict.reasons == ()
    # A declared class is judged, not counted as holding no fluid.
    assert result.no_fluid_record_count == 0


@pytest.mark.parametrize("class_name", [LAMP, SINK])
def test_a_recipe_less_machine_relating_to_no_fuel_never_blocks_a_verdict(class_name: str) -> None:
    verdict = _verdict(_audit(_covered_fuel_world(_recipe_less(class_name))), GEN_FUEL)
    assert verdict.verdict == fuel.VERDICT_REJECT
    assert verdict.pooled_megawatts == FUEL_GEN_MW


@pytest.mark.parametrize(
    ("class_name", "unmeasured"),
    [
        (MAKER, frozenset({TURBO, BIO, GAS})),
        (REFINERY, frozenset({FUEL})),
        (PACKAGER, frozenset({FUEL})),
        (FUEL_WELL, frozenset({FUEL})),
        (OIL_PUMP, frozenset()),
    ],
)
def test_a_census_record_unmeasures_exactly_the_fluids_its_class_relates_to(
    class_name: str, unmeasured: frozenset[str]
) -> None:
    # Without the record both classes reject: fuel at 250 MW against 250, the
    # twin at 1000 + 750 MW against 150. The census record of a class whose
    # recipes or extraction name a fluid unmeasures that fluid and no other -
    # where the candidate's first draft never looked at the census at all.
    world = _world(
        [
            _gen(GEN_FUEL),
            _gen(GEN_TWIN),
            _maker(R_FUEL),
            _maker(R_FUEL),
            _maker(R_TURBO),
            _maker(R_BIO),
        ],
        unadmitted_unread=((class_name, 1),),
    )
    result = _audit(world)
    for generator in (GEN_FUEL, GEN_TWIN):
        verdict = _verdict(result, generator)
        if unmeasured & set(verdict.accepted_fuels):
            assert verdict.verdict == fuel.VERDICT_INDETERMINATE
            assert verdict.reasons == (fuel.REASON_SUPPLY_UNMEASURED,)
        else:
            assert verdict.verdict == fuel.VERDICT_REJECT
        for line in verdict.fuels:
            assert (line.supply_per_minute is None) == (line.item_key in unmeasured)


@pytest.mark.parametrize("census", ["unadmitted_read", "unadmitted_unread"])
@pytest.mark.parametrize("class_name", [MOD_BUILD, MOD_BUILD_SHOUTED])
def test_an_untabled_undeclared_buildable_is_unregistered(class_name: str, census: str) -> None:
    # A buildable the registry has never heard of may be a generator burning
    # the fuel or a refinery eating it. It is never assumed inert.
    records = 2
    result = _audit(_covered_fuel_world(**{census: ((class_name, records),)}))
    verdict = _verdict(result, GEN_FUEL)
    assert verdict.verdict == fuel.VERDICT_INDETERMINATE
    assert verdict.reasons == (fuel.REASON_CLASS_UNREGISTERED,)
    assert all(line.supply_per_minute is None for line in verdict.fuels)
    assert _line(verdict, FUEL).reasons == (fuel.REASON_CLASS_UNREGISTERED,)
    assert verdict.pooled_megawatts is None
    assert result.unregistered_record_count == records
    assert result.no_fluid_record_count == 0


@pytest.mark.parametrize("class_name", [MOD_ACTOR, MOD_BUILD, PLAYER])
def test_an_admitted_machine_of_an_undeclared_class_is_unregistered(class_name: str) -> None:
    # Admitted means it carried a machine tag, so whatever its prefix it runs.
    result = _audit(_covered_fuel_world(_recipe_less(class_name)))
    assert _verdict(result, GEN_FUEL).reasons == (fuel.REASON_CLASS_UNREGISTERED,)
    assert result.unregistered_record_count == 1


@pytest.mark.parametrize("where", ["machine", "census"])
def test_an_unreadable_class_name_is_unregistered(where: str) -> None:
    # An unreadable name stays unknown even if the registry declares the empty name.
    registry = _registry(declared_classes=DECLARED | {""})
    if where == "machine":
        world = _covered_fuel_world(_recipe_less(""))
    else:
        world = _covered_fuel_world(unadmitted_read=(("", 1),))
    assert _verdict(_audit(world, registry), GEN_FUEL).reasons == (fuel.REASON_CLASS_UNREGISTERED,)


@pytest.mark.parametrize("where", ["machine", "census"])
def test_a_tabled_undeclared_class_holds_no_fluid(where: str) -> None:
    # Ruling (c): the probed undeclared build classes - the HUB's built-in
    # parts, the path nodes, the flow indicator, the potty and the HUB's own
    # biomass burner - hold no fluid, admitted or in the census.
    assert len(fuel.NO_FLUID_UNDECLARED_CLASSES) == PROBED_UNDECLARED_CLASS_COUNT
    assert "Build_GeneratorIntegratedBiomass_C" in fuel.NO_FLUID_UNDECLARED_CLASSES
    for class_name in sorted(fuel.NO_FLUID_UNDECLARED_CLASSES):
        assert class_name not in DECLARED
        if where == "machine":
            world = _covered_fuel_world(_recipe_less(class_name))
        else:
            world = _covered_fuel_world(unadmitted_read=((class_name, 1),))
        result = _audit(world)
        assert _verdict(result, GEN_FUEL).verdict == fuel.VERDICT_REJECT
        assert result.no_fluid_record_count == 1


def test_a_tabled_class_the_registry_declares_is_judged_by_its_relation() -> None:
    # The table vouches for an UNDECLARED class only. Once a build declares
    # one and a recipe produced in it names the fuel, its relation decides.
    tabled = sorted(fuel.NO_FLUID_UNDECLARED_CLASSES)[0]
    recipes = {**RECIPES, R_PACK: replace(RECIPES[R_PACK], produced_in=(tabled,))}
    registry = _registry(recipes=MappingProxyType(recipes), declared_classes=DECLARED | {tabled})
    result = _audit(_covered_fuel_world(unadmitted_read=((tabled, 1),)), registry)
    assert _verdict(result, GEN_FUEL).reasons == (fuel.REASON_SUPPLY_UNMEASURED,)
    assert result.no_fluid_record_count == 0


def test_an_empty_registry_declaration_leaves_every_buildable_unregistered() -> None:
    # A hand-built registry that declares nothing vouches for no class.
    result = _audit(
        _covered_fuel_world(unadmitted_read=((LAMP, 1),)), _registry(declared_classes=frozenset())
    )
    assert _verdict(result, GEN_FUEL).reasons == (fuel.REASON_CLASS_UNREGISTERED,)


@pytest.mark.parametrize(
    "registry",
    [
        _registry(
            warnings=(
                GARBLED_WARNING,
                RegistryWarning(
                    code=WARN_MISSING_DURATION, subject="Recipe_SyntheticSkippedQx85_C", detail="x"
                ),
            )
        ),
        _registry(
            warnings=(
                GARBLED_WARNING,
                RegistryWarning(
                    code=WARN_MALFORMED_BLOB, subject="Recipe_SyntheticSkippedQx85_C", detail="x"
                ),
            )
        ),
        _registry(
            warnings=(
                GARBLED_WARNING,
                RegistryWarning(code=WARN_MALFORMED_GROUP, subject="7", detail="x"),
            )
        ),
        _registry(unknown_groups=("FGSyntheticRecipeGroupQx85",)),
    ],
    ids=["recipe-skipped-duration", "recipe-skipped-blob", "group-malformed", "group-unknown"],
)
def test_a_registry_missing_recipes_leaves_every_relation_unknown(registry: Registry) -> None:
    # A recipe the registry skipped may be produced in any declared class and
    # name any fuel, so no judged record's relation is known - and every
    # generator record is one, naming no recipe - so every fluid is
    # unmeasured. The same world over the whole registry decides.
    blocked = _audit(_covered_fuel_world(), registry)
    assert _verdict(blocked, GEN_FUEL).reasons == (fuel.REASON_SUPPLY_UNMEASURED,)
    assert _verdict(_audit(_covered_fuel_world()), GEN_FUEL).verdict == fuel.VERDICT_REJECT


def test_an_extractor_of_an_unknown_form_relates_to_every_fluid() -> None:
    verdict = _verdict(_audit(_covered_fuel_world(_recipe_less(ODD_EXTRACTOR))), GEN_FUEL)
    assert verdict.reasons == (fuel.REASON_SUPPLY_UNMEASURED,)


def test_an_undeclared_producer_token_leaves_its_recipes_items_unknown() -> None:
    # A recipe whose producer token names no declared class may be produced in
    # any class of that native parent, so its items are unmeasured beside any
    # record judged by relation - the generator's own record is one. A
    # declared producer relates its own class only.
    native = "FGSyntheticNativeBenchQx85"
    recipes = {**RECIPES, R_FUEL: replace(RECIPES[R_FUEL], unresolved_produced_in=(native,))}
    registry = _registry(recipes=MappingProxyType(recipes))
    blocked = _audit(_covered_fuel_world(), registry)
    assert _verdict(blocked, GEN_FUEL).reasons == (fuel.REASON_SUPPLY_UNMEASURED,)
    declared = _registry(recipes=MappingProxyType(recipes), declared_classes=DECLARED | {native})
    clear = _audit(_covered_fuel_world(unadmitted_read=((LAMP, 1),)), declared)
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
    # A flow rating this machine at clock one would REJECT at 250 MW. The
    # audit's own flow gaps it.
    result = _audit(_world([_gen(GEN_FUEL), _maker(R_FUEL), unflowable]))
    assert result.flow_complete is False
    verdict = _verdict(result, GEN_FUEL)
    assert verdict.verdict == fuel.VERDICT_INDETERMINATE
    assert verdict.reasons == (fuel.REASON_FLOW_INCOMPLETE,)
    assert verdict.pooled_megawatts == FUEL_M3_PER_REFINERY * FUEL_MJ_PER_M3 / SIXTY


@pytest.mark.parametrize("clock", [Fraction(1), Fraction(0)])
def test_a_world_of_generators_alone_reaches_no_verdict(clock: Fraction) -> None:
    # The world's own flow moves nothing, which the flow model names incomplete.
    result = _audit(_world([_gen(GEN_FUEL, clock)]))
    assert result.flow_complete is False
    verdict = _verdict(result, GEN_FUEL)
    assert verdict.verdict == fuel.VERDICT_INDETERMINATE
    assert verdict.reasons == (fuel.REASON_FLOW_INCOMPLETE,)


def test_a_generator_class_machine_naming_a_recipe_is_in_the_flow() -> None:
    # Counted, the generator-class machine's own recipe makes 10 m3 a minute
    # beside the refinery's 10: 250 MW, covering 250. Left out, 125 MW FIRES.
    producing_generator = MachineState(
        class_name=GEN_FUEL, producing=True, recipe_class_name=R_FUEL, overclock=Fraction(1)
    )
    verdict = _verdict(_audit(_world([producing_generator, _maker(R_FUEL)])), GEN_FUEL)
    assert verdict.demand_megawatts == FUEL_GEN_MW
    assert _line(verdict, FUEL).supply_per_minute == 2 * FUEL_M3_PER_REFINERY
    assert verdict.verdict == fuel.VERDICT_REJECT


def test_unreadable_fuels_name_an_unmeasured_supply_too() -> None:
    world = _world([_gen(GEN_GARBLED), _recipe_less(FUEL_WELL), _maker(R_FUEL)])
    assert _verdict(_audit(world), GEN_GARBLED).reasons == (
        fuel.REASON_FUELS_UNREAD,
        fuel.REASON_SUPPLY_UNMEASURED,
    )
    world = _world([_gen(GEN_GARBLED), _recipe_less(MOD_ACTOR), _maker(R_FUEL)])
    assert _verdict(_audit(world), GEN_GARBLED).reasons == (
        fuel.REASON_FUELS_UNREAD,
        fuel.REASON_CLASS_UNREGISTERED,
    )
    # A miner relates to solids only, which an unread list may burn but no
    # verdict measures anyway.
    world = _world([_gen(GEN_GARBLED), _recipe_less(MINER), _maker(R_FUEL)])
    assert _verdict(_audit(world), GEN_GARBLED).reasons == (fuel.REASON_FUELS_UNREAD,)


def test_the_worlds_own_flow_rates_an_elided_clock_and_gaps_the_rest() -> None:
    elided = MachineState(
        class_name=REFINERY,
        producing=True,
        recipe_class_name=R_FUEL,
        overclock=None,
        overclock_elided=True,
    )
    boosted = MachineState(
        class_name=REFINERY,
        producing=True,
        recipe_class_name=R_FUEL,
        overclock=Fraction(1),
        production_boost_tagged=True,
    )
    decided = _verdict(_audit(_world([_gen(GEN_FUEL), elided, elided])), GEN_FUEL)
    assert decided.verdict == fuel.VERDICT_REJECT
    assert decided.pooled_megawatts == (
        2 * FUEL_M3_PER_REFINERY * ELIDED_CLOCK_DEFAULT * FUEL_MJ_PER_M3 / SIXTY
    )
    world = _world([_gen(GEN_FUEL), elided, boosted, _maker(R_UNKNOWN)])
    assert _verdict(_audit(world), GEN_FUEL).reasons == (fuel.REASON_FLOW_INCOMPLETE,)


def test_the_world_counts_its_unrated_records() -> None:
    players_read, players_unread, belts, mods = 4, 1, 7, 2
    world = _covered_fuel_world(
        _recipe_less(sorted(fuel.NO_FLUID_UNDECLARED_CLASSES)[0]),
        _recipe_less(LAMP),
        unadmitted_read=((PLAYER, players_read), (TRACTOR, 0), (BELT, belts)),
        unadmitted_unread=((PLAYER, players_unread), (MOD_BUILD, mods)),
    )
    result = _audit(world)
    # The tabled machine and the player records hold no fluid; the zero count
    # names no record; the lamp and the belts are judged; the mods are
    # unregistered.
    assert result.no_fluid_record_count == 1 + players_read + players_unread
    assert result.unregistered_record_count == mods


# ---------------------------------------------------------------------------
# Scope
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("class_name", [GEN_GEO, GEN_GEO_RATED])
def test_geothermal_is_out_of_scope(class_name: str) -> None:
    # The geothermal shape: NO fuel declared on a variable-output entry, and no
    # unreadable-fuels flag. GEN_GEO_RATED declares a NONZERO output, so only
    # the variable-production check puts it out.
    assert GENERATORS[class_name].accepted_fuels is None
    assert GENERATORS[class_name].is_variable_production
    result = _supply([_gen(class_name), _gen(GEN_FUEL)], _flow(_maker(R_FUEL), _maker(R_FUEL)))
    assert result.out_of_scope == (class_name,)
    assert all(entry.class_name != class_name for entry in result.verdicts)
    assert all(entry.class_name != class_name for entry in result.demands)
    # It burns nothing, so it never makes another class's supply unknown.
    assert _verdict(result, GEN_FUEL).verdict == fuel.VERDICT_REJECT


def test_a_zero_output_generator_with_no_fuel_is_out_of_scope() -> None:
    result = _supply([_gen(GEN_ZERO)], _flow(_maker(R_FUEL)))
    assert result.out_of_scope == (GEN_ZERO,)
    assert result.verdicts == ()


@pytest.mark.parametrize("class_name", [GEN_GEO, GEN_GEO_RATED, GEN_ZERO])
@pytest.mark.parametrize("entry", ["flagged", (), [FUEL], (FUEL, 7)])
def test_an_unreadable_fuel_list_is_never_out_of_scope(class_name: str, entry: object) -> None:
    # A fuel list that IS declared but cannot be read is not "burns nothing":
    # the class may burn anything, so it is indeterminate, and every other class
    # loses the proof that its supply is its own.
    if entry == "flagged":
        flag = RegistryWarning(code=WARN_UNREADABLE_FUELS, subject=class_name, detail="x")
        registry = _registry(warnings=(GARBLED_WARNING, flag))
    else:
        registry = _with_generator(class_name, entry)
    result = _supply(
        [_gen(class_name), _gen(GEN_FUEL)], _flow(_maker(R_FUEL), _maker(R_FUEL)), registry
    )
    assert result.out_of_scope == ()
    verdict = _verdict(result, class_name)
    assert verdict.verdict == fuel.VERDICT_INDETERMINATE
    assert fuel.REASON_FUELS_UNREAD in verdict.reasons
    assert verdict.accepted_fuels == ()
    assert _demand(result.demands, class_name).complete is False
    other = _verdict(result, GEN_FUEL)
    assert other.verdict == fuel.VERDICT_INDETERMINATE
    assert other.reasons == (fuel.REASON_FUEL_SHARING_UNKNOWN,)


def test_non_generator_classes_are_ignored() -> None:
    result = _supply([_gen(GEN_FUEL)], _flow(_maker(R_FUEL)))
    assert tuple(entry.class_name for entry in result.verdicts) == (GEN_FUEL,)
    assert result.out_of_scope == ()


def test_supplemental_resources_and_byproducts_are_named_exclusions() -> None:
    result = _supply([_gen(GEN_FUEL)], _flow(_maker(R_FUEL)))
    assert result.exclusions == (fuel.EXCLUDED_SUPPLEMENTAL, fuel.EXCLUDED_BYPRODUCT)
    for code in result.exclusions:
        detail = fuel.EXCLUSION_DETAIL[code]
        assert detail.isascii()
        assert detail.strip()


def test_every_reason_is_closed_vocabulary_with_a_detail_line() -> None:
    assert fuel.REASON_SOLID_SUPPLY_UNMODELLED == "solid-supply-unmodelled"
    assert set(fuel.DEMAND_REASONS) <= set(fuel.INDETERMINATE_REASONS)
    assert set(fuel.SUPPLY_REASONS) <= set(fuel.INDETERMINATE_REASONS)
    assert not set(fuel.SUPPLY_REASONS) & set(fuel.DEMAND_REASONS)
    assert set(fuel.REASON_DETAIL) == set(fuel.INDETERMINATE_REASONS)
    assert len(set(fuel.INDETERMINATE_REASONS)) == len(fuel.INDETERMINATE_REASONS)
    for detail in fuel.REASON_DETAIL.values():
        assert detail.isascii()
        assert detail.strip()


# ---------------------------------------------------------------------------
# The demand-only result
# ---------------------------------------------------------------------------


def test_demand_card_states_burn_per_fuel() -> None:
    supply = _flow(_maker(R_TURBO), _maker(R_UNKNOWN))
    result = _supply([_gen(GEN_TWIN), _gen(GEN_TWIN, Fraction(1, 2))], supply)
    assert _verdict(result, GEN_TWIN).verdict == fuel.VERDICT_INDETERMINATE
    demand = _demand(result.demands, GEN_TWIN)
    demand_mw = TWIN_GEN_MW * Fraction(3, 2)
    assert demand.complete is True
    assert demand.demand_megawatts == demand_mw
    assert demand.headline_fuel == TURBO
    assert tuple(burn.item_key for burn in demand.burns) == (TURBO, BIO)
    assert _burn(demand, TURBO).burn_per_minute == demand_mw * SIXTY / TURBO_MJ_PER_M3
    assert _burn(demand, BIO).burn_per_minute == demand_mw * SIXTY / BIO_MJ_PER_M3
    # The same result whether or not a flow exists - it claims nothing about one.
    alone = _demands(_world([_gen(GEN_TWIN), _gen(GEN_TWIN, Fraction(1, 2))]))
    assert alone == result.demands


def test_the_demand_types_declare_no_supply_field() -> None:
    for kind in (fuel.FuelDemand, fuel.FuelBurn):
        names = {field.name for field in fields(kind)}
        assert not any("supply" in name or "shortfall" in name for name in names)


def test_the_demand_ignores_supply_side_reasons() -> None:
    result = _supply(
        [_gen(GEN_COAL), _gen(GEN_FUEL), _gen(GEN_TWIN), _gen(GEN_SHARE)],
        _flow(_maker(R_UNKNOWN), raw=(FUEL,)),
        unadmitted_read=((MOD_BUILD, 1),),
    )
    for class_name in (GEN_COAL, GEN_FUEL, GEN_TWIN):
        demand = _demand(result.demands, class_name)
        assert demand.complete is True
        assert demand.reasons == ()


# ---------------------------------------------------------------------------
# Trace and exactness
# ---------------------------------------------------------------------------


def test_the_trace_carries_every_figure_a_fire_rests_on() -> None:
    clock = Fraction(1, 3)
    verdict = _verdict(_supply([_gen(GEN_FUEL)], _flow(_maker(R_FUEL, clock))), GEN_FUEL)
    values = {(step.label, step.subject): step.value for step in verdict.trace}
    assert values[fuel.LABEL_NAMEPLATE, GEN_FUEL] == FUEL_GEN_MW
    assert values[fuel.LABEL_CLOCK_SUM, GEN_FUEL] == Fraction(1)
    assert values[fuel.LABEL_DEMAND, GEN_FUEL] == FUEL_GEN_MW
    assert values[fuel.LABEL_ENERGY_VALUE, FUEL] == FUEL_MJ_PER_LITRE
    assert values[fuel.LABEL_MEGAJOULES_PER_UNIT, FUEL] == FUEL_MJ_PER_M3
    assert values[fuel.LABEL_NET_FLOW, FUEL] == FUEL_M3_PER_REFINERY * clock
    assert values[fuel.LABEL_SUPPLY, FUEL] == FUEL_M3_PER_REFINERY * clock
    assert values[fuel.LABEL_SUPPLY_MEGAWATTS, FUEL] == verdict.pooled_megawatts
    assert values[fuel.LABEL_POOLED, GEN_FUEL] == verdict.pooled_megawatts
    assert values[fuel.LABEL_SHORTFALL, GEN_FUEL] == verdict.shortfall_megawatts
    assert values[fuel.LABEL_SHORTFALL_RATE, FUEL] == _line(verdict, FUEL).shortfall_per_minute
    assert all(step.kind in (fuel.STEP_READ, fuel.STEP_COMPUTED) for step in verdict.trace)
    assert all(type(step.value) is Fraction for step in verdict.trace)
    assert all(step.label.isascii() for step in verdict.trace)


def test_a_solid_fuel_puts_no_supply_figure_in_the_trace() -> None:
    verdict = _verdict(_supply([_gen(GEN_COAL)], _flow(*[_maker(R_COAL)] * 5)), GEN_COAL)
    labels = {step.label for step in verdict.trace}
    assert fuel.LABEL_NET_FLOW not in labels
    assert fuel.LABEL_SUPPLY not in labels
    assert fuel.LABEL_POOLED not in labels
    assert fuel.LABEL_DEMAND in labels


def test_the_trace_is_deterministic() -> None:
    def build() -> fuel.WorldFuel:
        return _supply(
            [_gen(GEN_TWIN), _gen(GEN_FUEL, Fraction(1, 2)), _gen(GEN_COAL)],
            _flow(_maker(R_TURBO), _maker(R_FUEL)),
            unadmitted_read=((PLAYER, 1), (REFINERY, 1)),
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
    floated = dict(ITEMS)
    floated[FUEL] = _item(FUEL, FORM_LIQUID, 0.75)
    worlds = [
        _supply([_gen(GEN_FUEL)], _flow(_maker(R_FUEL, Fraction(1, 3)))),
        _supply([_gen(GEN_TWIN), _gen(GEN_SHARE)], _flow(_maker(R_TURBO))),
        _supply([_gen(GEN_FUEL, 0.5)], _flow(_maker(R_FUEL))),
        _supply([_gen(GEN_DUD), _gen(GEN_GEO)], _flow(_maker(R_UNKNOWN))),
        _supply([_gen(GEN_INEXACT), _gen(GEN_GAS), _gen(GEN_COAL)], _flow(_maker(R_GAS))),
        _supply(
            [_gen(GEN_FUEL)], _flow(_maker(R_FUEL)), _registry(items=MappingProxyType(floated))
        ),
        _supply([_gen(GEN_TWIN)] * 2, _flow(_maker(R_TURBO), _maker(R_BIO))),
    ]
    # The control: the walk sees a float when one is there.
    assert _floats(_gen(GEN_FUEL, 0.5)) == ["result.overclock"]
    for result in worlds:
        assert _floats(result) == []
