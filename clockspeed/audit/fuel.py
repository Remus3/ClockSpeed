"""CS-1285: fuel supply against fuel demand, per built fuel generator class, exact.

WHAT THIS MODULE OWNS
-----------------------
Two pure functions over stated models, the computation behind the D4 fuel rule
(``power.fuel_supply``, BOOTSTRAP.md section 5.3):

- :func:`fuel_supply_of` decides, per built fuel generator class, whether the
  world's own nominal flow - which it builds - supplies the fuel its built
  instances burn. Each class gets one
  :class:`FuelVerdict` - :data:`VERDICT_FIRE` with the exact shortfall,
  :data:`VERDICT_REJECT` when the supply covers the demand, or
  :data:`VERDICT_INDETERMINATE` with every named reason that kept a verdict out
  of reach.
- :func:`fuel_demand_of` states, per class, what its built instances burn per
  minute of each accepted fuel at their clocks - a :class:`FuelDemand` that
  claims NOTHING about supply, so a companion card can carry it over a flow too
  incomplete for a verdict. It declares no supply or shortfall field at all.

SEAM DISCIPLINE. Nothing here opens a save or the raw docs file, and nothing
builds a registry. The caller supplies every model: ``WorldMachines`` for the
built machines and their clocks; the generator, item and recipe namespaces of a
registry by mapping; the ACCEPTED FUELS as an explicit mapping of generator
class to its ``mFuel`` list in source order - an input of its own because the
generator entry does not carry it; the EXTRACTABLE input, per item every
extractor class that can extract it - an input of its own because no registry
entry says which resource an extractor yields; and the REGISTERED input, every
class the caller's registry declares - an input of its own because the
registry models only the classes that draw power, extract or generate, not a
belt or a foundation. The flow is NOT an input: it is
built here, by ``clockspeed/audit/flow.py`` :func:`flow_of` - the one owner of
that arithmetic, one audit consuming its neighbour - over the world's own
machines, so no flow over some other population can ever be handed in. The two
registry constants imported at run time - the fluid scale and the form tokens -
are imported from their one owner rather than restated, so a fluid's unit here
cannot drift from the unit the registry normalized its recipe amounts to.

THE FLOW IS THE WORLD'S OWN, BUILT HERE. :func:`fuel_supply_of` builds it over
EVERY admitted machine that names a recipe - a generator-class machine naming
one included, since its recipe moves items like any other - so every machine a
flow can rate is in it, and a machine it cannot rate (an unread clock, a boost,
an unknown recipe) is the flow's own named gap: the flow is then incomplete,
:data:`REASON_FLOW_INCOMPLETE`. A world with no recipe machine has a flow that
moves nothing, which the flow model names incomplete too, so it reaches no
verdict.

A MACHINE NO FLOW CAN MEASURE IS JUDGED BY WHAT ITS CLASS COULD MAKE. Two kinds
of machine carry no recipe a flow could rate: an admitted non-generator machine
naming no recipe - an extractor, whose node and so whose resource the save
never records (CS-1048) - and a record the machines census counts but never
admitted. Neither is left out silently, and neither blocks every fuel: each
makes an accepted fuel :data:`REASON_SUPPLY_UNMEASURED` exactly when its class
COULD make that fuel - a recipe producing it is produced in that class, or the
extractable input names that class as its extractor - or when nobody stated
every class that makes it: the extractable input does not list the fuel, or a
recipe producing it names a producing building that never resolved. A
REGISTERED class that makes no fuel - a lamp, a belt, a foundation, a sink, a
container - never makes one unmeasured, so a census of such records blocks
nothing. An unmeasured fuel's supply is None - never the flow's figure, never
a zero. So a mined fuel is indeterminate wherever an extractor that could mine
it is built - the 2026-10-08 CS-1285 decision record in ``docs/LEDGER.md``,
Q3, accepts exactly that - while a fuel only recipes make still decides beside
it.

AN UNREGISTERED CLASS IS NEVER ASSUMED INERT (non-negotiable 7). A class is
REGISTERED when the registered input, the generator or accepted-fuel
namespaces, a recipe's producing classes or the extractable input names it. A
machine no flow can measure whose class is none of these - or whose class name
is unreadable - may make or eat any fuel, so EVERY accepted fuel of every
class is :data:`REASON_CLASS_UNREGISTERED`, with its supply None.

WHAT A REGISTERED RECIPE-LESS MACHINE EATS IS NOT MODELLED. A recipe-less
machine moves items only by extraction - which the rules above judge - or by
burning or sinking them. A generator's burn is this module's demand; a
registered sink's intake is whatever a belt feeds it, which no nominal flow
models (``clockspeed/audit/flow.py`` states the same scope). A registered
class is taken to make no fuel, by the closed-world reading of the recipes and
the extractable input, and its intake is the one supply-side effect the
verdict does not see.

THE ARITHMETIC, ALL OF IT EXACT ``Fraction``
----------------------------------------------
- DEMAND. A class's demand in MW is the sum over its built instances of the
  nameplate output times the instance clock. Generation is LINEAR in the
  clock: no generator entry carries a production exponent (measured), unlike
  the consumer power law ``clockspeed/audit/balance.py`` brackets.
- ENERGY. A solid's ``mEnergyValue`` is MJ per item. A fluid's is MJ per
  LITRE - measured: all five packaging recipes agree - so its MJ per cubic
  metre is the value times ``LITRES_PER_CUBIC_METRE``. A fluid's unit here is
  the cubic metre because the flow's fluid rates already are.
- BURN. Units per minute at a demand of ``D`` MW, for a fuel of ``E`` MJ per
  unit: ``D * 60 / E``.
- SUPPLY. Per fuel, the flow's NET nominal rate per minute floored at zero:
  what the recipe machines make less what they eat, which is what is left for
  a generator, and never a debt. A fuel no recipe in a complete flow touches
  supplies a measured zero. Its energy rate is ``supply * E / 60`` MW.
- POOLING. A class's pooled MW is the sum over every accepted fuel of its
  supply in MW, so two fuels short alone may cover together.

THE VERDICT. FIRE when the pooled MW falls below the demand, carrying the exact
shortfall in MW and, per accepted fuel, that shortfall as a per-minute rate of
that fuel alone (``shortfall * 60 / E``); the headline fuel is the first
accepted fuel in ``mFuel`` order. REJECT when the pooled MW meets or exceeds the
demand. Only a class with no named reason reaches either.

INDETERMINATE IS NOT A VERDICT (CS-1271's terms). A class is indeterminate,
with every reason named in :data:`INDETERMINATE_REASONS` order, when: its
accepted fuels are unreadable; its nameplate is a production gap; a built
instance was never admitted to ``WorldMachines``; an instance carries a
production boost, an unread clock or a refused clock; an accepted fuel's energy
value is unknown; the flow is incomplete; an accepted fuel is declared raw, so
the flow does not measure its supply; a machine no flow can measure could make
an accepted fuel (above) - or, for a class whose fuels are unreadable, any
item; a machine no flow can measure is of a class nobody registered; it shares
an accepted fuel with another
built fuel generator class, which competes for the same supply (both are
indeterminate); or another built class's fuels are unreadable, so no supply can
be proven this class's own. Every figure that could still be computed is
published - a floor is labelled one by its reason - and every figure that could
not is None, NEVER a zero (non-negotiable 7).

AN ELIDED CLOCK IS THE CLASS DEFAULT, COUNTED, by the predicate
``clockspeed/audit/balance.py`` and ``clockspeed/audit/flow.py`` share: a None
clock with ``MachineState.overclock_elided`` set runs at
``ELIDED_CLOCK_DEFAULT`` and is counted on the result; any other None is unread.

OUT OF SCOPE. A built generator class that burns nothing - one ABSENT from the
accepted-fuel input, so declaring no fuel, on an entry that is variable
production or declares exactly zero output, the geothermal shape (which has no
``mFuel``) - is named in :attr:`WorldFuel.out_of_scope` and gets no verdict and
no demand. ABSENT AND UNREADABLE ARE DIFFERENT INPUTS. A class the input maps
to None, or to anything but a non-empty tuple of names, declares fuels nobody
could read: it is in scope and :data:`REASON_FUELS_UNREAD` whatever its
entry's shape, and every other class is :data:`REASON_FUEL_SHARING_UNKNOWN`,
since it may burn their fuel. The wiring therefore leaves a generator with no
``mFuel`` out of the mapping and maps one whose ``mFuel`` did not read to None.
Supplemental resources (water) and byproducts are not
modelled; :data:`EXCLUSIONS` names both on every result so tier 3 can say so.

THE TRACE. Every verdict and demand carries an ordered tuple of
:class:`FuelStep` - each figure read or computed, with a fixed label, the class
or item it is about, and its exact value - built from the very values the
result holds, so a tier-3 derivation generated from it cannot disagree with the
figures (non-negotiable 8). Reasons and exclusions render through the fixed
lines :data:`REASON_DETAIL` and :data:`EXCLUSION_DETAIL`.

NO WARNING CODES ARE DEFINED HERE. The rule layer names what this module finds;
a ``WARN_*`` code added here must be re-exported by the package, which
``tests/audit/test_package_exports.py`` enforces.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from types import MappingProxyType
from typing import TYPE_CHECKING, Final

from clockspeed.audit.balance import (
    ELIDED_CLOCK_DEFAULT,
    GAP_NO_REGISTRY_ENTRY,
    GAP_PRODUCTION_INEXACT,
    GAP_PRODUCTION_UNDECLARED,
    GAP_PRODUCTION_VARIABLE,
)
from clockspeed.audit.flow import flow_of
from clockspeed.data.registry import FLUID_FORMS, FORM_SOLID, LITRES_PER_CUBIC_METRE
from clockspeed.solve.exact import SECONDS_PER_MINUTE, audit_exact

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping, Sequence

    from clockspeed.audit.flow import WorldFlow
    from clockspeed.audit.machines import MachineState, WorldMachines
    from clockspeed.data.registry import Generator, Item, Recipe

__all__ = [
    "DEMAND_REASONS",
    "EXCLUDED_BYPRODUCT",
    "EXCLUDED_SUPPLEMENTAL",
    "EXCLUSIONS",
    "EXCLUSION_DETAIL",
    "INDETERMINATE_REASONS",
    "LABEL_BURN",
    "LABEL_CLOCK_SUM",
    "LABEL_DEMAND",
    "LABEL_ENERGY_VALUE",
    "LABEL_HEADROOM",
    "LABEL_INSTANCES",
    "LABEL_MEGAJOULES_PER_UNIT",
    "LABEL_NAMEPLATE",
    "LABEL_NET_FLOW",
    "LABEL_POOLED",
    "LABEL_SHORTFALL",
    "LABEL_SHORTFALL_RATE",
    "LABEL_SUPPLY",
    "LABEL_SUPPLY_MEGAWATTS",
    "REASON_BOOST_UNMODELED",
    "REASON_CLASS_UNREGISTERED",
    "REASON_CLOCK_REFUSED",
    "REASON_CLOCK_UNREAD",
    "REASON_DETAIL",
    "REASON_ENERGY_UNKNOWN",
    "REASON_FLOW_INCOMPLETE",
    "REASON_FUELS_UNREAD",
    "REASON_FUEL_SHARED",
    "REASON_FUEL_SHARING_UNKNOWN",
    "REASON_INSTANCES_OMITTED",
    "REASON_PRODUCTION_GAP",
    "REASON_SUPPLY_RAW",
    "REASON_SUPPLY_UNMEASURED",
    "STEP_COMPUTED",
    "STEP_READ",
    "UNIT_CUBIC_METRE",
    "UNIT_ITEM",
    "VERDICTS",
    "VERDICT_FIRE",
    "VERDICT_INDETERMINATE",
    "VERDICT_REJECT",
    "FuelBurn",
    "FuelDemand",
    "FuelLine",
    "FuelStep",
    "FuelVerdict",
    "WorldFuel",
    "fuel_demand_of",
    "fuel_supply_of",
]

#: Seconds per minute, as the Fraction every rate here is scaled by.
_SIXTY: Final = Fraction(SECONDS_PER_MINUTE)

#: The unit a solid fuel is burned and supplied in.
UNIT_ITEM: Final = "item"

#: The unit a fluid fuel is burned and supplied in - the flow's fluid unit.
UNIT_CUBIC_METRE: Final = "m3"

#: The pooled supply falls below the demand on complete inputs.
VERDICT_FIRE: Final = "fire"

#: The pooled supply meets or exceeds the demand on complete inputs.
VERDICT_REJECT: Final = "reject"

#: Some input is incomplete, so no comparison was made. NOT a verdict.
VERDICT_INDETERMINATE: Final = "indeterminate"

#: The closed vocabulary of verdicts.
VERDICTS: Final = (VERDICT_FIRE, VERDICT_REJECT, VERDICT_INDETERMINATE)

#: The accepted-fuel list is unreadable - mapped to None or to anything but a
#: non-empty tuple of names, or absent from the mapping on a generator that is
#: not the geothermal shape, so generates and must burn something.
REASON_FUELS_UNREAD: Final = "fuels-unread"

#: The nameplate output is a production gap: no generator entry, a variable
#: output, no declared output, or one that is not exactly a Fraction.
REASON_PRODUCTION_GAP: Final = "production-gap"

#: A built instance of the class was never admitted to ``WorldMachines``.
REASON_INSTANCES_OMITTED: Final = "instances-omitted"

#: An instance carries a production-boost tag, whose effect is unmodelled.
REASON_BOOST_UNMODELED: Final = "boost-unmodeled"

#: An instance's clock never read and was not elided.
REASON_CLOCK_UNREAD: Final = "clock-unread"

#: An instance's clock is not exactly a non-negative Fraction.
REASON_CLOCK_REFUSED: Final = "clock-refused"

#: An accepted fuel's energy value is unknown, so it has no MJ per unit.
REASON_ENERGY_UNKNOWN: Final = "energy-unknown"

#: The flow is incomplete, so every supply figure is a floor.
REASON_FLOW_INCOMPLETE: Final = "flow-incomplete"

#: An accepted fuel is declared raw - supplied from outside the flow - so the
#: flow does not measure its supply.
REASON_SUPPLY_RAW: Final = "supply-raw"

#: A machine no flow can measure - a recipe-less non-generator machine, such as
#: an extractor, or a census record never admitted - could make an accepted
#: fuel, so the flow's figure for that fuel is not this world's supply.
REASON_SUPPLY_UNMEASURED: Final = "supply-unmeasured"

#: A machine no flow can measure is of a class no input registers, or its class
#: name is unreadable, so it may make or eat any fuel.
REASON_CLASS_UNREGISTERED: Final = "class-unregistered"

#: The class shares an accepted fuel with another built fuel generator class.
REASON_FUEL_SHARED: Final = "fuel-shared"

#: Another built fuel generator class's fuels are unreadable, so it may burn
#: this class's fuel.
REASON_FUEL_SHARING_UNKNOWN: Final = "fuel-sharing-unknown"

#: The reasons a DEMAND figure can be missing, in reporting order.
DEMAND_REASONS: Final = (
    REASON_FUELS_UNREAD,
    REASON_PRODUCTION_GAP,
    REASON_INSTANCES_OMITTED,
    REASON_BOOST_UNMODELED,
    REASON_CLOCK_UNREAD,
    REASON_CLOCK_REFUSED,
    REASON_ENERGY_UNKNOWN,
)

#: Every reason a class can be indeterminate, in reporting order.
INDETERMINATE_REASONS: Final = (
    *DEMAND_REASONS,
    REASON_FLOW_INCOMPLETE,
    REASON_SUPPLY_RAW,
    REASON_SUPPLY_UNMEASURED,
    REASON_CLASS_UNREGISTERED,
    REASON_FUEL_SHARED,
    REASON_FUEL_SHARING_UNKNOWN,
)

#: One fixed line per reason. Keyed rather than formatted, so a detail can
#: never be built from something read out of a save.
REASON_DETAIL: Final[Mapping[str, str]] = MappingProxyType(
    {
        REASON_FUELS_UNREAD: (
            "the generator's accepted fuels could not be read, so neither its burn nor"
            " its supply can be stated"
        ),
        REASON_PRODUCTION_GAP: (
            "the generator's nameplate output is not modelled, so its demand is unknown"
        ),
        REASON_INSTANCES_OMITTED: (
            "some built generators of this class were never read, so the demand would be a floor"
        ),
        REASON_BOOST_UNMODELED: (
            "a generator carries a production boost whose effect is not modelled"
        ),
        REASON_CLOCK_UNREAD: (
            "a generator's clock was never read, and it is not assumed to be the default"
        ),
        REASON_CLOCK_REFUSED: (
            "a generator's clock is not an exact non-negative value, so it was refused"
        ),
        REASON_ENERGY_UNKNOWN: (
            "an accepted fuel has no known energy value, so its burn and supply in"
            " megawatts are unknown, never zero"
        ),
        REASON_FLOW_INCOMPLETE: (
            "the production flow is incomplete, so the fuel supply is a floor and not a measurement"
        ),
        REASON_SUPPLY_RAW: (
            "an accepted fuel is supplied from outside the production flow, which does"
            " not measure it"
        ),
        REASON_SUPPLY_UNMEASURED: (
            "a machine in this world that no production flow can measure - one with no"
            " recipe, such as an extractor, or a record never read as a machine - could make"
            " an accepted fuel, so the flow's figure is not this world's supply"
        ),
        REASON_CLASS_UNREGISTERED: (
            "a machine in this world that no production flow can measure is of a class"
            " nobody registered, so it may make or eat any fuel and no supply is measured"
        ),
        REASON_FUEL_SHARED: (
            "another built generator class burns the same fuel, so the supply cannot"
            " be divided between them"
        ),
        REASON_FUEL_SHARING_UNKNOWN: (
            "another built generator class has unreadable fuels and may burn this class's fuel"
        ),
    }
)

#: Supplemental resources - the water a generator also consumes - are not
#: compared against any supply.
EXCLUDED_SUPPLEMENTAL: Final = "supplemental-resource"

#: Byproducts - what a generator emits as it burns - are not modelled.
EXCLUDED_BYPRODUCT: Final = "byproduct"

#: What every result leaves out, by name.
EXCLUSIONS: Final = (EXCLUDED_SUPPLEMENTAL, EXCLUDED_BYPRODUCT)

#: One fixed line per exclusion, on the terms :data:`REASON_DETAIL` states.
EXCLUSION_DETAIL: Final[Mapping[str, str]] = MappingProxyType(
    {
        EXCLUDED_SUPPLEMENTAL: (
            "supplemental resources such as water are not compared against any supply"
        ),
        EXCLUDED_BYPRODUCT: "byproducts a generator emits are not modelled",
    }
)

#: A step that reads a figure out of a supplied model.
STEP_READ: Final = "read"

#: A step that computes a figure from earlier ones.
STEP_COMPUTED: Final = "computed"

LABEL_NAMEPLATE: Final = "nameplate megawatts of one generator at the reference clock"
LABEL_INSTANCES: Final = "built generators priced"
LABEL_CLOCK_SUM: Final = "sum of the generators' clocks"
LABEL_DEMAND: Final = "demand megawatts, the nameplate times the clock sum"
LABEL_ENERGY_VALUE: Final = "declared energy value in megajoules per item or per litre"
LABEL_MEGAJOULES_PER_UNIT: Final = "megajoules per unit, an item or a cubic metre"
LABEL_BURN: Final = "burn per minute, the demand times sixty over the megajoules per unit"
LABEL_NET_FLOW: Final = "net nominal flow per minute"
LABEL_SUPPLY: Final = "supply per minute, the net flow floored at zero"
LABEL_SUPPLY_MEGAWATTS: Final = "supply megawatts, the supply times the megajoules over sixty"
LABEL_POOLED: Final = "pooled supply megawatts over every accepted fuel"
LABEL_SHORTFALL: Final = "shortfall megawatts, the demand less the pooled supply"
LABEL_HEADROOM: Final = "headroom megawatts, the pooled supply less the demand"
LABEL_SHORTFALL_RATE: Final = (
    "shortfall per minute of this fuel alone, the shortfall times sixty over its megajoules"
)


@dataclass(frozen=True, repr=False)
class FuelStep:
    """One figure in a derivation, in order.

    Attributes:
        kind: :data:`STEP_READ` or :data:`STEP_COMPUTED`.
        label: One of this module's ``LABEL_*`` constants.
        subject: The generator class or the fuel item the figure is about.
        value: The figure, exactly.
    """

    kind: str
    label: str
    subject: str
    value: Fraction

    def __repr__(self) -> str:
        """Render the kind and the value's type, and no subject.

        Returns:
            The safe rendering.
        """
        return f"{type(self).__name__}(kind={self.kind!r}, value=<{type(self.value).__name__}>)"


@dataclass(frozen=True, repr=False)
class FuelBurn:
    """What a class's demand burns of one accepted fuel. Claims nothing about supply.

    Attributes:
        item_key: The fuel item.
        unit: :data:`UNIT_ITEM` or :data:`UNIT_CUBIC_METRE`, or None when the
            item or its form is unknown.
        megajoules_per_unit: The energy per unit, or None when unknown.
        burn_per_minute: Units per minute at the demand, or None when the demand
            or the energy is unknown.
    """

    item_key: str
    unit: str | None
    megajoules_per_unit: Fraction | None
    burn_per_minute: Fraction | None

    def __repr__(self) -> str:
        """Render the unit and whether the burn is known, and no name.

        Returns:
            The safe rendering.
        """
        return (
            f"{type(self).__name__}(unit={self.unit!r}, known={self.burn_per_minute is not None})"
        )


@dataclass(frozen=True, repr=False)
class FuelDemand:
    """One built fuel generator class's demand and burn. DECLARES NO SUPPLY FIELD.

    Attributes:
        class_name: The generator class.
        accepted_fuels: Its accepted fuels in ``mFuel`` order, or empty when
            unreadable.
        headline_fuel: The first accepted fuel, or None when unreadable.
        instance_count: Built instances admitted to ``WorldMachines``.
        omitted_count: Built instances that were not.
        elided_clock_count: Admitted instances priced at the elided default.
        nameplate_megawatts: One generator's output at the reference clock, or
            None for a production gap.
        production_gap_kind: The production gap kind, or None.
        clock_sum: The exact sum of the admitted instances' clocks, or None
            when any is unreadable.
        demand_megawatts: ``nameplate * clock_sum``, or None when either is
            unknown or an instance was omitted - never a floor.
        burns: One per accepted fuel, in ``mFuel`` order.
        reasons: The :data:`DEMAND_REASONS` that apply, in that order.
        complete: Whether no reason applies.
        trace: The derivation.
    """

    class_name: str
    accepted_fuels: tuple[str, ...]
    headline_fuel: str | None
    instance_count: int
    omitted_count: int
    elided_clock_count: int
    nameplate_megawatts: Fraction | None
    production_gap_kind: str | None
    clock_sum: Fraction | None
    demand_megawatts: Fraction | None
    burns: tuple[FuelBurn, ...]
    reasons: tuple[str, ...]
    complete: bool
    trace: tuple[FuelStep, ...]

    def __repr__(self) -> str:
        """Render counts and flags, and no name.

        Returns:
            The safe rendering.
        """
        return (
            f"{type(self).__name__}(instance_count={self.instance_count}, "
            f"burns={len(self.burns)}, reasons={self.reasons!r}, complete={self.complete})"
        )


@dataclass(frozen=True, repr=False)
class FuelLine:
    """One accepted fuel's part in a class's verdict.

    Attributes:
        item_key: The fuel item.
        unit: :data:`UNIT_ITEM` or :data:`UNIT_CUBIC_METRE`, or None when unknown.
        megajoules_per_unit: The energy per unit, or None when unknown.
        supply_per_minute: The flow's net rate floored at zero, or None when the
            fuel is declared raw or the flow does not measure this world's
            supply of it (:data:`REASON_SUPPLY_UNMEASURED`).
        supply_megawatts: ``supply * megajoules / 60``, or None when either is
            unknown.
        shortfall_per_minute: On :data:`VERDICT_FIRE` only, the class's
            shortfall as a rate of this fuel alone; otherwise None.
    """

    item_key: str
    unit: str | None
    megajoules_per_unit: Fraction | None
    supply_per_minute: Fraction | None
    supply_megawatts: Fraction | None
    shortfall_per_minute: Fraction | None

    def __repr__(self) -> str:
        """Render the unit and which figures are known, and no name.

        Returns:
            The safe rendering.
        """
        return (
            f"{type(self).__name__}(unit={self.unit!r}, "
            f"supply_known={self.supply_megawatts is not None}, "
            f"short={self.shortfall_per_minute is not None})"
        )


@dataclass(frozen=True, repr=False)
class FuelVerdict:
    """One built fuel generator class's supply verdict.

    Attributes:
        class_name: The generator class.
        verdict: One of :data:`VERDICTS`.
        reasons: The :data:`INDETERMINATE_REASONS` that apply, in that order;
            empty exactly when the verdict is not indeterminate.
        accepted_fuels: Its accepted fuels in ``mFuel`` order, or empty when
            unreadable.
        headline_fuel: The first accepted fuel, or None when unreadable.
        instance_count: Built instances admitted to ``WorldMachines``.
        omitted_count: Built instances that were not.
        elided_clock_count: Admitted instances priced at the elided default.
        nameplate_megawatts: One generator's output at the reference clock, or
            None for a production gap.
        production_gap_kind: The production gap kind, or None.
        clock_sum: The exact sum of the admitted instances' clocks, or None.
        demand_megawatts: The class's demand, or None when unknown.
        fuels: One per accepted fuel, in ``mFuel`` order.
        pooled_megawatts: The sum of every fuel's supply in MW - a FLOOR when
            :data:`REASON_FLOW_INCOMPLETE` applies - or None when any fuel's
            figure is unknown.
        shortfall_megawatts: ``demand - pooled`` on :data:`VERDICT_FIRE` only.
        shared_with: The other built classes sharing an accepted fuel, sorted.
        trace: The derivation.
    """

    class_name: str
    verdict: str
    reasons: tuple[str, ...]
    accepted_fuels: tuple[str, ...]
    headline_fuel: str | None
    instance_count: int
    omitted_count: int
    elided_clock_count: int
    nameplate_megawatts: Fraction | None
    production_gap_kind: str | None
    clock_sum: Fraction | None
    demand_megawatts: Fraction | None
    fuels: tuple[FuelLine, ...]
    pooled_megawatts: Fraction | None
    shortfall_megawatts: Fraction | None
    shared_with: tuple[str, ...]
    trace: tuple[FuelStep, ...]

    def __repr__(self) -> str:
        """Render the verdict, reasons and counts, and no name.

        Returns:
            The safe rendering.
        """
        return (
            f"{type(self).__name__}(verdict={self.verdict!r}, reasons={self.reasons!r}, "
            f"instance_count={self.instance_count}, fuels={len(self.fuels)})"
        )


@dataclass(frozen=True, repr=False)
class WorldFuel:
    """Every built fuel generator class's verdict and demand, with the scope named.

    Attributes:
        verdicts: One per built fuel generator class, sorted by class name.
        demands: The same classes' demand-only results, in the same order.
        out_of_scope: Built generator classes that burn nothing, sorted.
        exclusions: :data:`EXCLUSIONS`, on every result.
        flow_complete: Whether the supplied flow was complete.
    """

    verdicts: tuple[FuelVerdict, ...]
    demands: tuple[FuelDemand, ...]
    out_of_scope: tuple[str, ...]
    exclusions: tuple[str, ...]
    flow_complete: bool

    def __repr__(self) -> str:
        """Render counts and flags, and no name.

        Returns:
            The safe rendering.
        """
        return (
            f"{type(self).__name__}(verdicts={len(self.verdicts)}, "
            f"out_of_scope={len(self.out_of_scope)}, flow_complete={self.flow_complete})"
        )


@dataclass(frozen=True)
class _Energy:
    """One accepted fuel's energy, as :func:`_energy_of` read it."""

    item_key: str
    unit: str | None
    declared: Fraction | None
    megajoules_per_unit: Fraction | None


@dataclass(frozen=True)
class _Basis:
    """Everything one class's demand rests on, shared by both results."""

    class_name: str
    fuels: tuple[str, ...] | None
    instance_count: int
    omitted_count: int
    elided_clock_count: int
    nameplate: Fraction | None
    gap_kind: str | None
    clock_sum: Fraction | None
    demand: Fraction | None
    energies: tuple[_Energy, ...]
    reasons: frozenset[str]
    steps: tuple[FuelStep, ...]


def _read(label: str, subject: str, value: Fraction) -> FuelStep:
    return FuelStep(kind=STEP_READ, label=label, subject=subject, value=value)


def _computed(label: str, subject: str, value: Fraction) -> FuelStep:
    return FuelStep(kind=STEP_COMPUTED, label=label, subject=subject, value=value)


def _ordered(reasons: frozenset[str] | set[str], vocabulary: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(reason for reason in vocabulary if reason in reasons)


def _readable_fuels(value: object) -> tuple[str, ...] | None:
    """The accepted fuels as a non-empty tuple of names in order, or None.

    Args:
        value: The caller's entry for one class.

    Returns:
        The names, de-duplicated in order so no fuel pools twice; or None when
        the entry is not a non-empty tuple of strings.
    """
    if type(value) is not tuple or not value:
        return None
    if not all(type(name) is str for name in value):
        return None
    return tuple(dict.fromkeys(value))


def _burns_nothing(
    class_name: str,
    generators: Mapping[str, Generator],
    accepted_fuels: Mapping[str, tuple[str, ...] | None],
) -> bool:
    """Whether a generator class is out of scope: no fuel declared, and no fixed output.

    Args:
        class_name: The class.
        generators: The generator namespace.
        accepted_fuels: The accepted-fuel input.

    Returns:
        True when the class is ABSENT from the accepted-fuel input AND its
        entry is variable production or declares exactly zero output - the
        geothermal shape. A class mapped to anything, even None or a
        malformed list, declared fuels: unreadable ones are a named reason,
        never "burns nothing".
    """
    if class_name in accepted_fuels:
        return False
    entry = generators.get(class_name)
    if entry is None:
        return False
    if entry.is_variable_production:
        return True
    output = entry.power_production
    return type(output) is Fraction and output == 0


def _nameplate_of(
    class_name: str, generators: Mapping[str, Generator]
) -> tuple[Fraction | None, str | None]:
    """One generator's nameplate output, or the production gap kind.

    The checks run in ``clockspeed/audit/balance.py`` ``_production_bucket``'s
    order, variable first, and publish its gap kinds verbatim.

    Args:
        class_name: The class.
        generators: The generator namespace.

    Returns:
        ``(output, None)`` or ``(None, kind)``.
    """
    entry = generators.get(class_name)
    if entry is None:
        return None, GAP_NO_REGISTRY_ENTRY
    output = entry.power_production
    if entry.is_variable_production:
        return None, GAP_PRODUCTION_VARIABLE
    if output is None:
        return None, GAP_PRODUCTION_UNDECLARED
    if type(output) is not Fraction:
        return None, GAP_PRODUCTION_INEXACT
    return output, None


def _clocks_of(states: Sequence[MachineState]) -> tuple[Fraction | None, int, set[str]]:
    """The exact clock sum of a class's admitted instances.

    Each instance is checked in ``clockspeed/audit/flow.py``'s order: the boost,
    then an unread clock, then a refused one.

    Args:
        states: The instances.

    Returns:
        The sum or None when any instance has a reason, the elided count, and
        the reasons.
    """
    total = Fraction(0)
    elided = 0
    reasons: set[str] = set()
    for state in states:
        if state.production_boost_tagged:
            reasons.add(REASON_BOOST_UNMODELED)
            continue
        clock: object = state.overclock
        if clock is None:
            if not state.overclock_elided:
                reasons.add(REASON_CLOCK_UNREAD)
                continue
            clock = ELIDED_CLOCK_DEFAULT
            elided += 1
        if type(clock) is not Fraction or clock < 0:
            reasons.add(REASON_CLOCK_REFUSED)
            continue
        total += clock
    return (None if reasons else total), elided, reasons


def _energy_of(item_key: str, items: Mapping[str, Item]) -> _Energy:
    """One fuel's energy per unit burned.

    Args:
        item_key: The fuel.
        items: The item namespace.

    Returns:
        The unit from the item's form, and its energy per unit - a solid's
        declared value, a fluid's times ``LITRES_PER_CUBIC_METRE`` - or None
        for an unknown item, form or value, or a value not above zero.
    """
    item = items.get(item_key)
    if item is None:
        return _Energy(item_key, None, None, None)
    if item.is_fluid and item.form in FLUID_FORMS:
        unit, scale = UNIT_CUBIC_METRE, LITRES_PER_CUBIC_METRE
    elif not item.is_fluid and item.form == FORM_SOLID:
        unit, scale = UNIT_ITEM, 1
    else:
        return _Energy(item_key, None, None, None)
    value = item.energy_value
    if type(value) is not Fraction or value <= 0:
        return _Energy(item_key, unit, None, None)
    return _Energy(item_key, unit, value, value * scale)


def _basis_of(
    class_name: str,
    states: Sequence[MachineState],
    omitted: int,
    generators: Mapping[str, Generator],
    accepted_fuels: Mapping[str, tuple[str, ...] | None],
    items: Mapping[str, Item],
) -> _Basis:
    """Compute what one class's demand rests on.

    Args:
        class_name: The class.
        states: Its admitted instances.
        omitted: Its built instances never admitted.
        generators: The generator namespace.
        accepted_fuels: The accepted-fuel input.
        items: The item namespace.

    Returns:
        The basis, with its demand steps.
    """
    fuels = _readable_fuels(accepted_fuels.get(class_name))
    reasons: set[str] = set()
    if fuels is None:
        reasons.add(REASON_FUELS_UNREAD)
    nameplate, gap_kind = _nameplate_of(class_name, generators)
    if gap_kind is not None:
        reasons.add(REASON_PRODUCTION_GAP)
    if omitted:
        reasons.add(REASON_INSTANCES_OMITTED)
    clock_sum, elided, clock_reasons = _clocks_of(states)
    reasons |= clock_reasons
    demand = None
    if nameplate is not None and clock_sum is not None and not omitted:
        demand = nameplate * clock_sum

    steps: list[FuelStep] = []
    if nameplate is not None:
        steps.append(_read(LABEL_NAMEPLATE, class_name, nameplate))
    steps.append(_computed(LABEL_INSTANCES, class_name, Fraction(len(states))))
    if clock_sum is not None:
        steps.append(_computed(LABEL_CLOCK_SUM, class_name, clock_sum))
    if demand is not None:
        steps.append(_computed(LABEL_DEMAND, class_name, demand))

    energies = tuple(_energy_of(key, items) for key in fuels or ())
    if any(energy.megajoules_per_unit is None for energy in energies):
        reasons.add(REASON_ENERGY_UNKNOWN)
    return _Basis(
        class_name=class_name,
        fuels=fuels,
        instance_count=len(states),
        omitted_count=omitted,
        elided_clock_count=elided,
        nameplate=nameplate,
        gap_kind=gap_kind,
        clock_sum=clock_sum,
        demand=demand,
        energies=energies,
        reasons=frozenset(reasons),
        steps=tuple(steps),
    )


def _energy_steps(energy: _Energy) -> list[FuelStep]:
    if energy.declared is None or energy.megajoules_per_unit is None:
        return []
    return [
        _read(LABEL_ENERGY_VALUE, energy.item_key, energy.declared),
        _computed(LABEL_MEGAJOULES_PER_UNIT, energy.item_key, energy.megajoules_per_unit),
    ]


def _demand_of(basis: _Basis) -> FuelDemand:
    """Project one basis onto its demand-only result.

    Args:
        basis: The class's basis.

    Returns:
        The demand, with one burn per accepted fuel.
    """
    steps = list(basis.steps)
    burns: list[FuelBurn] = []
    for energy in basis.energies:
        steps += _energy_steps(energy)
        burn = None
        if basis.demand is not None and energy.megajoules_per_unit is not None:
            burn = basis.demand * _SIXTY / energy.megajoules_per_unit
            steps.append(_computed(LABEL_BURN, energy.item_key, burn))
        burns.append(
            FuelBurn(
                item_key=energy.item_key,
                unit=energy.unit,
                megajoules_per_unit=energy.megajoules_per_unit,
                burn_per_minute=burn,
            )
        )
    reasons = _ordered(basis.reasons, DEMAND_REASONS)
    return FuelDemand(
        class_name=basis.class_name,
        accepted_fuels=basis.fuels or (),
        headline_fuel=basis.fuels[0] if basis.fuels else None,
        instance_count=basis.instance_count,
        omitted_count=basis.omitted_count,
        elided_clock_count=basis.elided_clock_count,
        nameplate_megawatts=basis.nameplate,
        production_gap_kind=basis.gap_kind,
        clock_sum=basis.clock_sum,
        demand_megawatts=basis.demand,
        burns=tuple(burns),
        reasons=reasons,
        complete=not reasons,
        trace=tuple(steps),
    )


def _supplies_of(
    basis: _Basis,
    flow: WorldFlow,
    unmeasured: frozenset[str],
    unregistered: bool,
    reasons: set[str],
    steps: list[FuelStep],
) -> list[tuple[_Energy, Fraction | None, Fraction | None]]:
    """Read each accepted fuel's supply off the flow, recording each step.

    Args:
        basis: The class's basis.
        flow: The supplied flow.
        unmeasured: The items a machine no flow can measure could make.
        unregistered: Whether such a machine is of an unregistered class.
        reasons: The class's reasons; a raw fuel adds :data:`REASON_SUPPLY_RAW`,
            an unmeasured one :data:`REASON_SUPPLY_UNMEASURED`, and every fuel
            :data:`REASON_CLASS_UNREGISTERED` when ``unregistered``.
        steps: The class's trace so far, appended to in order.

    Returns:
        Per accepted fuel in ``mFuel`` order, its energy, its supply per minute
        (None when raw or unmeasured) and its supply in MW (None when either
        is unknown).
    """
    raw = set(flow.raw_items)
    supplies: list[tuple[_Energy, Fraction | None, Fraction | None]] = []
    for energy in basis.energies:
        steps += _energy_steps(energy)
        supply: Fraction | None = None
        measured = True
        if energy.item_key in raw:
            reasons.add(REASON_SUPPLY_RAW)
            measured = False
        if energy.item_key in unmeasured:
            reasons.add(REASON_SUPPLY_UNMEASURED)
            measured = False
        if unregistered:
            reasons.add(REASON_CLASS_UNREGISTERED)
            measured = False
        if measured:
            entry = flow.items.get(energy.item_key)
            net = entry.net if entry is not None else Fraction(0)
            supply = max(net, Fraction(0))
            steps.append(_read(LABEL_NET_FLOW, energy.item_key, net))
            steps.append(_computed(LABEL_SUPPLY, energy.item_key, supply))
        supply_mw = None
        if supply is not None and energy.megajoules_per_unit is not None:
            supply_mw = supply * energy.megajoules_per_unit / _SIXTY
            steps.append(_computed(LABEL_SUPPLY_MEGAWATTS, energy.item_key, supply_mw))
        supplies.append((energy, supply, supply_mw))
    return supplies


def _verdict_of(
    basis: _Basis,
    flow: WorldFlow,
    unmeasured: frozenset[str],
    unregistered: bool,
    shared_with: tuple[str, ...],
    sharing_unknown: bool,
) -> FuelVerdict:
    """Decide one class's supply verdict over the flow.

    Args:
        basis: The class's basis.
        flow: The supplied flow.
        unmeasured: The items a machine no flow can measure could make.
        unregistered: Whether such a machine is of an unregistered class.
        shared_with: The other built classes sharing one of its fuels.
        sharing_unknown: Whether another built class's fuels are unreadable.

    Returns:
        The verdict.
    """
    reasons = set(basis.reasons)
    if not flow.complete:
        reasons.add(REASON_FLOW_INCOMPLETE)
    if basis.fuels is None and unmeasured:
        # Fuels nobody could read may be any item the flow does not measure.
        reasons.add(REASON_SUPPLY_UNMEASURED)
    if basis.fuels is None and unregistered:
        reasons.add(REASON_CLASS_UNREGISTERED)
    if shared_with:
        reasons.add(REASON_FUEL_SHARED)
    if sharing_unknown:
        reasons.add(REASON_FUEL_SHARING_UNKNOWN)

    steps = list(basis.steps)
    supplies = _supplies_of(basis, flow, unmeasured, unregistered, reasons, steps)
    pooled: Fraction | None = None if basis.fuels is None else Fraction(0)
    for _energy, _supply, supply_mw in supplies:
        pooled = pooled + supply_mw if pooled is not None and supply_mw is not None else None
    if pooled is not None:
        steps.append(_computed(LABEL_POOLED, basis.class_name, pooled))

    ordered = _ordered(reasons, INDETERMINATE_REASONS)
    demand = basis.demand
    verdict = VERDICT_INDETERMINATE
    shortfall: Fraction | None = None
    # With no reason left, the demand and the pooled supply are both known:
    # every path that leaves either None adds a reason above.
    if not ordered and demand is not None and pooled is not None:
        if pooled < demand:
            verdict = VERDICT_FIRE
            shortfall = demand - pooled
            steps.append(_computed(LABEL_SHORTFALL, basis.class_name, shortfall))
        else:
            verdict = VERDICT_REJECT
            steps.append(_computed(LABEL_HEADROOM, basis.class_name, pooled - demand))

    lines: list[FuelLine] = []
    for energy, supply, supply_mw in supplies:
        rate = None
        if shortfall is not None and energy.megajoules_per_unit is not None:
            rate = shortfall * _SIXTY / energy.megajoules_per_unit
            steps.append(_computed(LABEL_SHORTFALL_RATE, energy.item_key, rate))
        lines.append(
            FuelLine(
                item_key=energy.item_key,
                unit=energy.unit,
                megajoules_per_unit=energy.megajoules_per_unit,
                supply_per_minute=supply,
                supply_megawatts=supply_mw,
                shortfall_per_minute=rate,
            )
        )

    return FuelVerdict(
        class_name=basis.class_name,
        verdict=verdict,
        reasons=ordered if verdict == VERDICT_INDETERMINATE else (),
        accepted_fuels=basis.fuels or (),
        headline_fuel=basis.fuels[0] if basis.fuels else None,
        instance_count=basis.instance_count,
        omitted_count=basis.omitted_count,
        elided_clock_count=basis.elided_clock_count,
        nameplate_megawatts=basis.nameplate,
        production_gap_kind=basis.gap_kind,
        clock_sum=basis.clock_sum,
        demand_megawatts=demand,
        fuels=tuple(lines),
        pooled_megawatts=pooled,
        shortfall_megawatts=shortfall,
        shared_with=shared_with,
        trace=tuple(steps),
    )


def _is_generator(
    class_name: str,
    generators: Mapping[str, Generator],
    accepted_fuels: Mapping[str, tuple[str, ...] | None],
) -> bool:
    """Whether a class is a generator class: either namespace carries it."""
    return class_name in generators or class_name in accepted_fuels


def _makers_of(
    recipes: Mapping[str, Recipe],
    extractable: Mapping[str, frozenset[str] | None],
    candidates: Iterable[str],
) -> dict[str, frozenset[str] | None]:
    """Per candidate item, every machine class that could make it.

    Args:
        recipes: The recipe namespace - each recipe's outputs and the classes
            it is produced in.
        extractable: Item to every extractor class that can extract it.
        candidates: The items asked about.

    Returns:
        Per item, the classes a recipe producing it is produced in plus its
        declared extractors; or None when that set is unknown - the item is not
        in the extractable input, its entry there is not a frozenset, or a
        recipe producing it names a producing building that never resolved.
    """
    recipe_makers: dict[str, set[str]] = {}
    unresolved: set[str] = set()
    for recipe in recipes.values():
        for output in recipe.outputs:
            recipe_makers.setdefault(output.item_key, set()).update(recipe.produced_in)
            if recipe.unresolved_produced_in:
                unresolved.add(output.item_key)
    makers: dict[str, frozenset[str] | None] = {}
    for item_key in candidates:
        extractors = extractable.get(item_key)
        if not isinstance(extractors, frozenset) or item_key in unresolved:
            makers[item_key] = None
            continue
        makers[item_key] = frozenset(recipe_makers.get(item_key, ())) | extractors
    return makers


def _unmeasurable_classes(
    machines: WorldMachines,
    generators: Mapping[str, Generator],
    accepted_fuels: Mapping[str, tuple[str, ...] | None],
) -> frozenset[str]:
    """The classes of every machine no flow can measure.

    Args:
        machines: The machines model - the world.
        generators: The generator namespace.
        accepted_fuels: The accepted-fuel input.

    Returns:
        The class of every admitted non-generator machine naming no recipe,
        and of every record the census counts; an unreadable class is the
        empty string.
    """
    classes = {
        state.class_name
        for state in machines.machines
        if state.recipe_class_name is None
        and not _is_generator(state.class_name, generators, accepted_fuels)
    }
    for census in (machines.unadmitted_read_counts, machines.unadmitted_unread_counts):
        classes.update(class_name for class_name, count in census if count)
    return frozenset(classes)


def _known_classes(
    registered: frozenset[str],
    generators: Mapping[str, Generator],
    accepted_fuels: Mapping[str, tuple[str, ...] | None],
    recipes: Mapping[str, Recipe],
    extractable: Mapping[str, frozenset[str] | None],
) -> frozenset[str]:
    """Every class some input registers.

    Args:
        registered: The registered input; anything but a frozenset registers
            nothing.
        generators: The generator namespace.
        accepted_fuels: The accepted-fuel input.
        recipes: The recipe namespace - each recipe's producing classes.
        extractable: The extraction input - each item's extractor classes.

    Returns:
        The union of every class those inputs name.
    """
    known: set[str] = set(registered) if isinstance(registered, frozenset) else set()
    known.update(generators)
    known.update(accepted_fuels)
    for recipe in recipes.values():
        known.update(recipe.produced_in)
    for extractors in extractable.values():
        if isinstance(extractors, frozenset):
            known.update(extractors)
    return frozenset(known)


def _unmeasured_items(
    classes: frozenset[str],
    makers: Mapping[str, frozenset[str] | None],
) -> frozenset[str]:
    """The items a machine no flow can measure could make.

    Args:
        classes: The classes of the machines no flow can measure.
        makers: Per candidate item, the classes that could make it, or None.

    Returns:
        Every item whose makers are unknown, when any such machine exists, and
        every item one of those classes could make.
    """
    unmeasured: set[str] = set()
    for item_key, could in makers.items():
        # Unknown makers: any machine no flow can measure may make the item.
        hit = bool(classes) if could is None else any(name in could for name in classes)
        if hit:
            unmeasured.add(item_key)
    return frozenset(unmeasured)


def _bases_of(
    machines: WorldMachines,
    generators: Mapping[str, Generator],
    accepted_fuels: Mapping[str, tuple[str, ...] | None],
    items: Mapping[str, Item],
) -> tuple[tuple[_Basis, ...], tuple[str, ...]]:
    """Partition the built generator classes into in scope and out of scope.

    A class is a GENERATOR class when either the generator namespace or the
    accepted-fuel input carries it; it is BUILT when ``WorldMachines`` admitted
    an instance of it or its census of unadmitted records counts one.

    Args:
        machines: The machines model.
        generators: The generator namespace.
        accepted_fuels: The accepted-fuel input.
        items: The item namespace.

    Returns:
        The in-scope bases sorted by class name, and the out-of-scope classes.
    """
    admitted: dict[str, list[MachineState]] = {}
    for state in machines.machines:
        if _is_generator(state.class_name, generators, accepted_fuels):
            admitted.setdefault(state.class_name, []).append(state)
    omitted: dict[str, int] = {}
    for census in (machines.unadmitted_read_counts, machines.unadmitted_unread_counts):
        for class_name, count in census:
            if count and _is_generator(class_name, generators, accepted_fuels):
                omitted[class_name] = omitted.get(class_name, 0) + count

    bases: list[_Basis] = []
    out_of_scope: list[str] = []
    for class_name in sorted(set(admitted) | set(omitted)):
        if _burns_nothing(class_name, generators, accepted_fuels):
            out_of_scope.append(class_name)
            continue
        bases.append(
            _basis_of(
                class_name,
                admitted.get(class_name, []),
                omitted.get(class_name, 0),
                generators,
                accepted_fuels,
                items,
            )
        )
    return tuple(bases), tuple(out_of_scope)


def fuel_demand_of(
    machines: WorldMachines,
    generators: Mapping[str, Generator],
    accepted_fuels: Mapping[str, tuple[str, ...] | None],
    items: Mapping[str, Item],
) -> tuple[FuelDemand, ...]:
    """State what every built fuel generator class burns, claiming nothing about supply.

    PURE, AND TOTAL: unknown content is a named reason, never an exception.

    Args:
        machines: The machines model - the generators' instances and clocks.
        generators: The generator namespace, keyed by class name.
        accepted_fuels: Generator class to its accepted fuels in ``mFuel``
            order, or None when unreadable.
        items: The item namespace, for each fuel's energy value and form.

    Returns:
        One demand per built in-scope class, sorted by class name, audited
        exact on the way out.
    """
    bases, _ = _bases_of(machines, generators, accepted_fuels, items)
    result = tuple(_demand_of(basis) for basis in bases)
    audit_exact(result, path="fuel_demand")
    return result


def fuel_supply_of(
    machines: WorldMachines,
    generators: Mapping[str, Generator],
    accepted_fuels: Mapping[str, tuple[str, ...] | None],
    items: Mapping[str, Item],
    recipes: Mapping[str, Recipe],
    *,
    extractable: Mapping[str, frozenset[str] | None],
    registered: frozenset[str],
    raw_items: Iterable[str] = (),
) -> WorldFuel:
    """Decide, per built fuel generator class, whether the world's own flow supplies its fuel.

    PURE, AND TOTAL: unknown content is a named reason, never an exception.
    The flow is built here, over every admitted machine of ``machines`` that
    names a recipe; no caller's flow is ever read.

    Args:
        machines: The machines model - the whole world: generators, recipe
            machines, recipe-less machines and the census.
        generators: The generator namespace, keyed by class name.
        accepted_fuels: Generator class to its accepted fuels in ``mFuel``
            order, or None when unreadable; absent declares no fuel.
        items: The item namespace, for each fuel's energy value and form.
        recipes: The recipe namespace, keyed by class name - the flow's rates,
            and which classes each item's recipes are produced in.
        extractable: Item to every extractor class that can extract it, as a
            frozenset - empty when no extractor can. An item absent, or mapped
            to anything else, has unknown makers.
        registered: Every class the caller's registry declares, as a
            frozenset - classes the other inputs name need not repeat. A
            machine no flow can measure of any other class, or of an
            unreadable one, is :data:`REASON_CLASS_UNREGISTERED`.
        raw_items: Items declared supplied from outside the world's machines,
            handed to the flow; an accepted fuel among them is
            :data:`REASON_SUPPLY_RAW`.

    Returns:
        The verdicts and demands, audited exact on the way out.
    """
    flow = flow_of(
        tuple(state for state in machines.machines if state.recipe_class_name is not None),
        recipes,
        raw_items=raw_items,
    )
    bases, out_of_scope = _bases_of(machines, generators, accepted_fuels, items)
    candidates = set(items) | {key for basis in bases for key in basis.fuels or ()}
    classes = _unmeasurable_classes(machines, generators, accepted_fuels)
    known = _known_classes(registered, generators, accepted_fuels, recipes, extractable)
    unregistered = any(not class_name or class_name not in known for class_name in classes)
    unmeasured = _unmeasured_items(classes, _makers_of(recipes, extractable, candidates))
    readable = {basis.class_name: set(basis.fuels) for basis in bases if basis.fuels is not None}
    unread = {basis.class_name for basis in bases if basis.fuels is None}
    verdicts: list[FuelVerdict] = []
    for basis in bases:
        own = readable.get(basis.class_name, set())
        shared = tuple(
            sorted(
                other
                for other, fuels in readable.items()
                if other != basis.class_name and own & fuels
            )
        )
        sharing_unknown = any(other != basis.class_name for other in unread)
        verdicts.append(_verdict_of(basis, flow, unmeasured, unregistered, shared, sharing_unknown))
    result = WorldFuel(
        verdicts=tuple(verdicts),
        demands=tuple(_demand_of(basis) for basis in bases),
        out_of_scope=out_of_scope,
        exclusions=EXCLUSIONS,
        flow_complete=flow.complete,
    )
    audit_exact(result, path="fuel")
    return result
