"""CS-1285: fuel supply against fuel demand, per built fuel generator class, exact.

WHAT THIS MODULE OWNS
-----------------------
Two pure functions over two stated models, the computation behind the D4 fuel
rule (``power.fuel_supply``, BOOTSTRAP.md section 5.3):

- :func:`fuel_supply_of` decides, per built fuel generator class, whether the
  world's own nominal flow - which it builds - supplies the fuel its built
  instances burn. Each class gets one :class:`FuelVerdict` -
  :data:`VERDICT_FIRE` with the exact shortfall, :data:`VERDICT_REJECT` when
  the supply covers the demand, or :data:`VERDICT_INDETERMINATE` with every
  named reason that kept a verdict out of reach.
- :func:`fuel_demand_of` states, per class, what its built instances burn per
  minute of each accepted fuel at their clocks - a :class:`FuelDemand` that
  claims NOTHING about supply, so a companion card can carry it over a flow too
  incomplete for a verdict. It declares no supply or shortfall field at all.

THE BINDING RULING. ``docs/item_notes/phase5.md`` section CS-1285, the session
134 ruling "slice B v2, narrowed", decides everything below that is not
arithmetic; its clauses are cited by letter.

SEAM DISCIPLINE. Nothing here opens a save or the raw docs file, and nothing
builds a registry. The inputs are ``WorldMachines`` - the built machines, their
clocks and the census of records never admitted - and the ``Registry``, plus
the items the caller declares raw (ruling (f)): the accepted fuels, what each
extractor can yield and which classes exist are all read off the registry, so
no caller-supplied mapping can disagree with it. The flow is NOT an input: it
is built here, by ``clockspeed/audit/flow.py`` :func:`flow_of` - the one owner
of that arithmetic - over the world's own machines that name a recipe, so no
flow over some other population can ever be handed in. A machine the flow
cannot rate (an unread clock, a boost, an unknown recipe) is the flow's own
named gap, :data:`REASON_FLOW_INCOMPLETE`; a world with no recipe machine has
a flow that moves nothing, which the flow model names incomplete too.

VERDICTS DECIDE FLUID FUELS ONLY (ruling (a)). A solid fuel is never measured:
players, vehicles, sinks and stations move solids that no nominal flow sees,
and every real save holds a player. Every solid accepted fuel is
:data:`REASON_SOLID_SUPPLY_UNMODELLED` with its supply None, so a class burning
one is never decided. A fuel whose item or form is unknown is not known to be a
fluid, so its supply is None too, under the class's
:data:`REASON_ENERGY_UNKNOWN`.

A RECORD NO FLOW RATES IS JUDGED BY ITS CLASS (ruling (a)). Two kinds of record
carry no recipe a flow could rate: an admitted machine naming none - an
extractor, whose node the save never records (CS-1048), an idle or unreadable
manufacturer, or any generator - and a record the census counts but
``WorldMachines`` never admitted. The module FILTERS them (ruling (b)),
``clockspeed/audit/machines.py`` being unchanged:

- UNREGISTERED: an unreadable class name, an undeclared class whose name starts
  ``Build_`` (case folded) and is not on :data:`NO_FLUID_UNDECLARED_CLASSES`,
  or an admitted machine of an undeclared class not on it. Such a record may
  make or eat any fuel, so EVERY non-solid fuel of every class is
  :data:`REASON_CLASS_UNREGISTERED`, its supply None (non-negotiable 7).
- JUDGED: a class ``Registry.declared_classes`` declares. It makes a fluid
  fuel :data:`REASON_SUPPLY_UNMEASURED` when a registry recipe produced in it -
  by a resolved building or by an unresolved producer token of the same name -
  names that fuel as an input OR an output, or when it is an extractor that can
  yield it: its ``allowed_resources`` when it carries them, else every item of
  its ``allowed_forms`` (ruling (d)). A generator's own fuel list is its
  DEMAND, never such a relation. When a judged class's relation is not knowable
  it unmeasures EVERY fuel - an unknown relation is never read as none: an
  unrestricted extractor whose forms are unknown (a form token the registry
  did not recognize, or no form on an entry it flagged with a value present
  but not a string - the forms field reads as empty then), or a registry that
  lost recipes - one its recipe pass dropped (each code it logs where it drops
  one: no class name, a repeated one, no duration, a malformed blob), one it
  kept but whose producers, ingredients or products it could not read, a
  malformed docs group, or a group it did not recognize. And a recipe one of
  whose producer tokens names no declared class may be produced in any class
  of that native parent, so the items it names are unmeasured beside any
  judged record.
- HOLDS NO FLUID, COUNTED on :attr:`WorldFuel.no_fluid_record_count`: a class
  on :data:`NO_FLUID_UNDECLARED_CLASSES`, or any other undeclared census class
  - a player, a vehicle, a subsystem actor, the build gun. The count is ruling
  (b)'s bin, by class alone. An undeclared class a registry recipe or
  extractor nevertheless names is ALSO judged by that evidence - ruling (a)'s
  first sentence, read as outranking the bin, so the verdict fails closed. In a
  registry ``build_registry`` produces, that evidence is only ever an
  undeclared producer token, whose items the orphaned-recipe rule above
  already unmeasures; it differs only over a hand-built registry carrying a
  model it does not declare.

An unmeasured fuel's supply is None - never the flow's figure, never a zero.

WHAT A JUDGED RECORD MOVES BEYOND ITS RELATIONS IS NOT MODELLED. A pipe, a
buffer or a fluid freight station holds fluid but neither makes nor eats it in
the steady state a nominal flow describes; ruling (a) judges by recipes and
extraction alone, and so does this module.

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
- SUPPLY. Per measured fluid, the flow's NET nominal rate per minute floored at
  zero: what the recipe machines make less what they eat, which is what is left
  for a generator, and never a debt. A fluid no recipe in a complete flow
  touches supplies a measured zero. Its energy rate is ``supply * E / 60`` MW.
- THE CHAIN. A nominal net is only as good as the inputs behind it (the session
  137 upstream-shortfall ruling). A fluid's chain is every flowed recipe that
  makes or eats it, plus, repeatedly, every flowed recipe making an input of
  one already in it. When any input of a chain recipe other than the fuel
  itself has a net below zero - declared raw or not, made by an extractor no
  save rates, handed in by a player, or by nothing - the line is
  :data:`REASON_SUPPLY_INPUT_UNCOVERED`, its supply None, and each such input's
  net is in the trace. No derated figure is estimated.
- POOLING. A class's pooled MW is the sum over every accepted fuel of its
  supply in MW, so two fuels short alone may cover together.

THE VERDICT. FIRE when the pooled MW falls below the demand, carrying the exact
shortfall in MW and, per accepted fuel, that shortfall as a per-minute rate of
that fuel alone (``shortfall * 60 / E``); the headline fuel is the first
accepted fuel in ``mFuel`` order. REJECT when the pooled MW meets or exceeds the
demand. Only a class with no named reason reaches either. A maker at clock zero
makes nothing, and the verdict it leads to stands (ruling (e)).

INDETERMINATE IS NOT A VERDICT (CS-1271's terms). A class is indeterminate,
with every reason named in :data:`INDETERMINATE_REASONS` order, when: its
accepted fuels are unreadable; its nameplate is a production gap; a built
instance was never admitted to ``WorldMachines``; an instance carries a
production boost, an unread clock or a refused clock; an accepted fuel's energy
value is unknown; the flow is incomplete; an accepted fuel is solid; one is
declared raw, so the flow does not measure its supply; a judged record
unmeasures one - or, for a class whose fuels are unreadable, any fluid; an
accepted fluid's chain holds an uncovered input; an unregistered record
exists; it shares an accepted fuel with another built fuel
generator class, which competes for the same supply (both are indeterminate);
or another built class's fuels are unreadable, so no supply can be proven this
class's own. Every figure that could still be computed is published - a floor
is labelled one by its reason - and every figure that could not is None, NEVER
a zero (non-negotiable 7). Each accepted fuel's own supply-side reasons ride on
its :class:`FuelLine`, in :data:`SUPPLY_REASONS` order.

AN ELIDED CLOCK IS THE CLASS DEFAULT, COUNTED, by the predicate
``clockspeed/audit/balance.py`` and ``clockspeed/audit/flow.py`` share: a None
clock with ``MachineState.overclock_elided`` set runs at
``ELIDED_CLOCK_DEFAULT`` and is counted on the result; any other None is unread.

OUT OF SCOPE. A built generator class that burns nothing - its registry entry
carries no fuel list and the registry raised no unreadable-fuels warning for
it, on an entry that is variable production or declares exactly zero output,
the geothermal shape (which has no ``mFuel``) - is named in
:attr:`WorldFuel.out_of_scope` and gets no verdict and no demand. ABSENT AND
UNREADABLE ARE DIFFERENT INPUTS, told apart by that warning: a flagged list, or
any value but a non-empty tuple of names, declares fuels nobody could read, so
the class is in scope and :data:`REASON_FUELS_UNREAD` whatever its entry's
shape, and every other class is :data:`REASON_FUEL_SHARING_UNKNOWN`. A
fixed-output generator with no list at all generates and must burn something,
so it is :data:`REASON_FUELS_UNREAD` too. Supplemental resources (water) and
byproducts are not modelled; :data:`EXCLUSIONS` names both on every result so
tier 3 can say so.

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
    GAP_PRODUCTION_INEXACT,
    GAP_PRODUCTION_UNDECLARED,
    GAP_PRODUCTION_VARIABLE,
)
from clockspeed.audit.flow import flow_of
from clockspeed.data.registry import (
    FLUID_FORMS,
    FORM_SOLID,
    LITRES_PER_CUBIC_METRE,
    WARN_DUPLICATE_CLASS_NAME,
    WARN_MALFORMED_BLOB,
    WARN_MALFORMED_GROUP,
    WARN_MISSING_CLASS_NAME,
    WARN_MISSING_DURATION,
    WARN_NON_STRING_VALUE,
    WARN_UNREADABLE_FUELS,
)
from clockspeed.solve.exact import SECONDS_PER_MINUTE, audit_exact

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping, Sequence

    from clockspeed.audit.flow import WorldFlow
    from clockspeed.audit.machines import MachineState, WorldMachines
    from clockspeed.data.registry import Extractor, Generator, Item, Registry

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
    "LABEL_INPUT_NET",
    "LABEL_INSTANCES",
    "LABEL_MEGAJOULES_PER_UNIT",
    "LABEL_NAMEPLATE",
    "LABEL_NET_FLOW",
    "LABEL_POOLED",
    "LABEL_SHORTFALL",
    "LABEL_SHORTFALL_RATE",
    "LABEL_SUPPLY",
    "LABEL_SUPPLY_MEGAWATTS",
    "NO_FLUID_UNDECLARED_CLASSES",
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
    "REASON_SOLID_SUPPLY_UNMODELLED",
    "REASON_SUPPLY_INPUT_UNCOVERED",
    "REASON_SUPPLY_RAW",
    "REASON_SUPPLY_UNMEASURED",
    "STEP_COMPUTED",
    "STEP_READ",
    "SUPPLY_REASONS",
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

#: The unit a solid fuel is burned in.
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

#: The accepted-fuel list is unreadable - flagged by the registry, anything but
#: a non-empty tuple of names, or absent on a generator that is not the
#: geothermal shape, so generates and must burn something.
REASON_FUELS_UNREAD: Final = "fuels-unread"

#: The nameplate output is a production gap: a variable output, no declared
#: output, or one that is not exactly a Fraction.
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

#: An accepted fuel is a solid, whose supply no nominal flow measures (ruling
#: (a)): players, vehicles, sinks and stations move solids.
REASON_SOLID_SUPPLY_UNMODELLED: Final = "solid-supply-unmodelled"

#: An accepted fuel is declared raw - supplied from outside the flow - so the
#: flow does not measure its supply.
REASON_SUPPLY_RAW: Final = "supply-raw"

#: A record no flow rates is of a declared class that relates to an accepted
#: fuel - or whose relation is unknown - so the flow's figure for that fuel is
#: not this world's supply.
REASON_SUPPLY_UNMEASURED: Final = "supply-unmeasured"

#: An input somewhere in an accepted fluid's production chain has a net below
#: zero - declared raw or not - so the flow's nominal output of the fuel is not
#: established (the session 137 upstream-shortfall ruling). "Uncovered", not
#: "short": ``clockspeed/audit/flow.py`` calls an item short only when it is
#: not raw. No derated figure is estimated.
REASON_SUPPLY_INPUT_UNCOVERED: Final = "supply-input-uncovered"

#: A record no flow rates is unregistered - an unreadable class name, an
#: untabled undeclared buildable, or an admitted machine of an undeclared
#: class - so it may make or eat any fuel.
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

#: The reasons ONE accepted fuel's supply can be missing, in reporting order -
#: what :attr:`FuelLine.reasons` carries.
SUPPLY_REASONS: Final = (
    REASON_SOLID_SUPPLY_UNMODELLED,
    REASON_SUPPLY_RAW,
    REASON_SUPPLY_UNMEASURED,
    REASON_SUPPLY_INPUT_UNCOVERED,
    REASON_CLASS_UNREGISTERED,
)

#: Every reason a class can be indeterminate, in reporting order.
INDETERMINATE_REASONS: Final = (
    *DEMAND_REASONS,
    REASON_FLOW_INCOMPLETE,
    *SUPPLY_REASONS,
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
            "an accepted fuel has no known energy value or form, so its burn and supply"
            " in megawatts are unknown, never zero"
        ),
        REASON_FLOW_INCOMPLETE: (
            "the production flow is incomplete, so the fuel supply is a floor and not a measurement"
        ),
        REASON_SOLID_SUPPLY_UNMODELLED: (
            "an accepted fuel is a solid, and players, vehicles, sinks and stations move"
            " solids that no production flow measures"
        ),
        REASON_SUPPLY_RAW: (
            "an accepted fuel is supplied from outside the production flow, which does"
            " not measure it"
        ),
        REASON_SUPPLY_UNMEASURED: (
            "a machine in this world that no production flow can measure - one with no"
            " recipe, such as an extractor, or a record never read as a machine - may"
            " make or eat an accepted fuel, so the flow's figure is not this world's supply"
        ),
        REASON_SUPPLY_INPUT_UNCOVERED: (
            "an input in this fuel's production chain is consumed faster than the"
            " production flow makes it - supplied from outside, by an extractor whose rate"
            " is unknown, by hand, or not at all - so the fuel's nameplate output is not"
            " established, and no derated figure is estimated"
        ),
        REASON_CLASS_UNREGISTERED: (
            "a machine in this world that no production flow can measure is of a class"
            " the game data does not declare, so it may make or eat any fuel and no"
            " supply is measured"
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

#: Ruling (c): the undeclared build classes measured to hold no fluid - the
#: HUB's built-in parts, the vehicle path nodes, the pipeline flow indicator,
#: the potty, a blueprint storage and the HUB's own solid biomass burner, which
#: the solid reason covers. Class names only, read in session 137 by a
#: read-only probe over every save of the pinned development world on the
#: pinned build: these are ALL the undeclared ``Build_`` classes (case folded)
#: it found, admitted or in the census. A class absent here and undeclared is
#: unregistered when it is a buildable or an admitted machine, so a build that
#: adds one fails closed rather than open - as does another world holding an
#: undeclared buildable this probe never met: its saves report every fluid
#: unregistered, by design, until a probe tables the class. ``BP_Tractor_C``
#: needs no row: ruling (b) covers a non-buildable census class.
NO_FLUID_UNDECLARED_CLASSES: Final = frozenset(
    {
        "BUILD_Potty_mk1_C",
        "Build_GeneratorIntegratedBiomass_C",
        "Build_HubTerminal_C",
        "Build_PipelineFlowIndicator_C",
        "Build_StorageBlueprint_C",
        "Build_StorageIntegrated_C",
        "Build_VehiclePathNode_Default_C",
        "Build_VehiclePathNode_DockingStation_C",
        "Build_WorkBenchIntegrated_C",
    }
)

#: The buildable class-name prefix, compared case folded. A convention, not a
#: guarantee - the ruling records it as a common-mode risk.
_BUILDABLE_PREFIX: Final = "build_"

#: The registry warnings that mean a recipe, or a whole group, never reached
#: the recipe namespace, so no class's recipe relations are complete: every
#: code ``clockspeed/data/registry.py`` logs where its recipe pass drops an
#: entry - no class name, a repeated one, no duration, a malformed blob - and
#: the malformed group ``build_registry`` skips whole. Derived from the
#: registry's own source by
#: ``tests/audit/test_fuel.py::test_the_lost_recipe_codes_are_the_registry_drop_sites``,
#: which reads ``_build_recipes`` and every module function it reaches by
#: name, at any depth, for a code logged in the same block as a ``return
#: None``, a bare ``return``, a ``continue`` or a ``break``; so a drop site of
#: that shape added anywhere in the recipe pass fails that test until it is
#: counted here. A missing or repeated class name is counted whatever
#: namespace raised it: the warning's subject does not say which pass dropped
#: the entry, and counting one a non-recipe pass raised fails closed.
_RECIPE_LOSS_CODES: Final = frozenset(
    {
        WARN_MISSING_CLASS_NAME,
        WARN_DUPLICATE_CLASS_NAME,
        WARN_MISSING_DURATION,
        WARN_MALFORMED_BLOB,
        WARN_MALFORMED_GROUP,
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
LABEL_INPUT_NET: Final = "net nominal flow per minute of an uncovered input in the fuel's chain"
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
            fuel is not a known fluid or any of :attr:`reasons` applies.
        supply_megawatts: ``supply * megajoules / 60``, or None when either is
            unknown.
        shortfall_per_minute: On :data:`VERDICT_FIRE` only, the class's
            shortfall as a rate of this fuel alone; otherwise None.
        reasons: The :data:`SUPPLY_REASONS` that apply to this fuel, in that
            order. A solid carries :data:`REASON_SOLID_SUPPLY_UNMODELLED`
            alone. Any other fuel carries each of the rest that applies - a
            fuel whose item or form is unknown included, so an item the
            registry lacks can carry ``('class-unregistered',)`` or
            ``('supply-raw',)``, though its supply is None regardless, under
            the class's :data:`REASON_ENERGY_UNKNOWN`. Only a known fluid is
            walked for :data:`REASON_SUPPLY_INPUT_UNCOVERED`. Empty when none
            applies.
    """

    item_key: str
    unit: str | None
    megajoules_per_unit: Fraction | None
    supply_per_minute: Fraction | None
    supply_megawatts: Fraction | None
    shortfall_per_minute: Fraction | None
    reasons: tuple[str, ...]

    def __repr__(self) -> str:
        """Render the unit, which figures are known and the reasons, and no name.

        Returns:
            The safe rendering.
        """
        return (
            f"{type(self).__name__}(unit={self.unit!r}, "
            f"supply_known={self.supply_megawatts is not None}, "
            f"short={self.shortfall_per_minute is not None}, reasons={self.reasons!r})"
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
        flow_complete: Whether the world's own flow was complete.
        no_fluid_record_count: Records no flow rates that ruling (b) bins as
            holding no fluid, by class alone - a class on
            :data:`NO_FLUID_UNDECLARED_CLASSES`, admitted or in the census, or
            any other undeclared census class that is not a buildable. A
            record so binned whose class the registry nevertheless names is
            counted here AND judged by that evidence.
        unregistered_record_count: Records no flow rates that are
            unregistered; any one makes every fuel
            :data:`REASON_CLASS_UNREGISTERED`.
    """

    verdicts: tuple[FuelVerdict, ...]
    demands: tuple[FuelDemand, ...]
    out_of_scope: tuple[str, ...]
    exclusions: tuple[str, ...]
    flow_complete: bool
    no_fluid_record_count: int
    unregistered_record_count: int

    def __repr__(self) -> str:
        """Render counts and flags, and no name.

        Returns:
            The safe rendering.
        """
        return (
            f"{type(self).__name__}(verdicts={len(self.verdicts)}, "
            f"out_of_scope={len(self.out_of_scope)}, flow_complete={self.flow_complete}, "
            f"no_fluid={self.no_fluid_record_count}, "
            f"unregistered={self.unregistered_record_count})"
        )


@dataclass(frozen=True, repr=False)
class _Energy:
    """One accepted fuel's energy and form, as :func:`_energy_of` read it."""

    item_key: str
    unit: str | None
    declared: Fraction | None
    megajoules_per_unit: Fraction | None
    solid: bool
    fluid: bool


@dataclass(frozen=True, repr=False)
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


@dataclass(frozen=True, repr=False)
class _Unrated:
    """What the records no flow rates do to the supply, by ruling (b).

    Attributes:
        related: Every item a judged record's class relates to.
        every_item: Whether some judged record's relation is unknown, so it
            relates to every item.
        unregistered_records: How many records are unregistered.
        no_fluid_records: How many records ruling (b) bins as holding no
            fluid, by class alone.
    """

    related: frozenset[str]
    every_item: bool
    unregistered_records: int
    no_fluid_records: int


def _read(label: str, subject: str, value: Fraction) -> FuelStep:
    return FuelStep(kind=STEP_READ, label=label, subject=subject, value=value)


def _computed(label: str, subject: str, value: Fraction) -> FuelStep:
    return FuelStep(kind=STEP_COMPUTED, label=label, subject=subject, value=value)


def _ordered(reasons: frozenset[str] | set[str], vocabulary: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(reason for reason in vocabulary if reason in reasons)


def _readable_fuels(value: object) -> tuple[str, ...] | None:
    """The accepted fuels as a non-empty tuple of names in order, or None.

    Args:
        value: The registry entry's accepted-fuels field.

    Returns:
        The names, de-duplicated in order so no fuel pools twice; or None when
        the value is not a non-empty tuple of strings.
    """
    if type(value) is not tuple or not value:
        return None
    if not all(type(name) is str for name in value):
        return None
    return tuple(dict.fromkeys(value))


def _declared_fuels(
    class_name: str, entry: Generator, flagged: frozenset[str]
) -> tuple[tuple[str, ...] | None, bool]:
    """A generator's accepted fuels, and whether it declares none at all.

    Args:
        class_name: The class.
        entry: Its registry entry.
        flagged: Every class the registry flagged with an unreadable fuel list.

    Returns:
        ``(fuels, absent)``: the readable fuels or None, and True only when the
        entry carries no fuel list and the registry raised no unreadable-fuels
        warning for it - the one shape that can be out of scope.
    """
    value = entry.accepted_fuels
    if value is None:
        return None, class_name not in flagged
    return _readable_fuels(value), False


def _burns_nothing(entry: Generator) -> bool:
    """Whether a generator that declares no fuel is the geothermal shape.

    Args:
        entry: Its registry entry.

    Returns:
        True for variable production or an exactly zero declared output.
    """
    if entry.is_variable_production:
        return True
    output = entry.power_production
    return type(output) is Fraction and output == 0


def _nameplate_of(entry: Generator) -> tuple[Fraction | None, str | None]:
    """One generator's nameplate output, or the production gap kind.

    The checks run in ``clockspeed/audit/balance.py`` ``_production_bucket``'s
    order, variable first, and publish its gap kinds verbatim.

    Args:
        entry: The registry entry.

    Returns:
        ``(output, None)`` or ``(None, kind)``.
    """
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
    """One fuel's form and energy per unit burned.

    Args:
        item_key: The fuel.
        items: The item namespace.

    Returns:
        The unit from the item's form, whether it is a known solid or a known
        fluid, and its energy per unit - a solid's declared value, a fluid's
        times ``LITRES_PER_CUBIC_METRE`` - or None for an unknown item, form or
        value, or a value not above zero.
    """
    item = items.get(item_key)
    if item is None:
        return _Energy(item_key, None, None, None, solid=False, fluid=False)
    if item.is_fluid and item.form in FLUID_FORMS:
        unit, scale, solid, fluid = UNIT_CUBIC_METRE, LITRES_PER_CUBIC_METRE, False, True
    elif not item.is_fluid and item.form == FORM_SOLID:
        unit, scale, solid, fluid = UNIT_ITEM, 1, True, False
    else:
        return _Energy(item_key, None, None, None, solid=False, fluid=False)
    value = item.energy_value
    if type(value) is not Fraction or value <= 0:
        return _Energy(item_key, unit, None, None, solid=solid, fluid=fluid)
    return _Energy(item_key, unit, value, value * scale, solid=solid, fluid=fluid)


def _basis_of(
    class_name: str,
    fuels: tuple[str, ...] | None,
    entry: Generator,
    states: Sequence[MachineState],
    omitted: int,
    items: Mapping[str, Item],
) -> _Basis:
    """Compute what one class's demand rests on.

    Args:
        class_name: The class.
        fuels: Its readable accepted fuels, or None.
        entry: Its registry entry.
        states: Its admitted instances.
        omitted: Its built instances never admitted.
        items: The item namespace.

    Returns:
        The basis, with its demand steps.
    """
    reasons: set[str] = set()
    if fuels is None:
        reasons.add(REASON_FUELS_UNREAD)
    nameplate, gap_kind = _nameplate_of(entry)
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


def _uncovered_inputs(flow: WorldFlow, fuel: str) -> tuple[str, ...]:
    """The inputs in one fuel's production chain that the flow does not cover.

    THE CHAIN starts from every flowed recipe that makes OR eats the fuel - an
    eater starved of another input eats less, so the fuel's net moves too -
    and adds, repeatedly, every flowed recipe that makes an input of a recipe
    already in it. A seen set ends the walk on a cycle. A recipe's inputs are
    read off the flow itself: an item's ``consumers`` are the recipes eating it.

    INPUTS ONLY. Only a chain recipe's inputs are scanned, never its outputs:
    a byproduct eaten faster elsewhere starves its eater, not its maker, so an
    output's deficit never holds the fuel back - the session 137 ruling's brief
    walks the inputs of each chain recipe.

    RESIDUAL, recorded and not fixed: a census record of a declared class whose
    recipes eat an upstream intermediate of the chain, but not the fuel, is in
    no flow and relates to no fuel, so it can starve the chain unseen and the
    verdict can still reject. The session 137 adjudication records that the
    shipped registry cannot produce this shape.

    Args:
        flow: The world's own flow.
        fuel: The accepted fuel.

    Returns:
        Sorted, every input of a chain recipe whose net is below zero, declared
        raw or not - a raw item's net is what the world must bring in, and the
        flow cannot say whether it does - except the fuel itself, whose own net
        is its supply's business.
    """
    start = flow.items.get(fuel)
    if start is None:
        return ()
    inputs_of: dict[str, set[str]] = {}
    for item_key, entry in flow.items.items():
        for recipe in entry.consumers:
            inputs_of.setdefault(recipe, set()).add(item_key)
    chain: set[str] = set()
    frontier = [*start.producers, *start.consumers]
    while frontier:
        recipe = frontier.pop()
        if recipe in chain:
            continue
        chain.add(recipe)
        for item_key in inputs_of.get(recipe, ()):
            frontier.extend(flow.items[item_key].producers)
    uncovered = {
        item_key
        for recipe in chain
        for item_key in inputs_of.get(recipe, ())
        if item_key != fuel and flow.items[item_key].net < 0
    }
    return tuple(sorted(uncovered))


def _supply_reasons_of(
    energy: _Energy, raw: frozenset[str], unrated: _Unrated, uncovered: tuple[str, ...]
) -> tuple[str, ...]:
    """The :data:`SUPPLY_REASONS` that keep one accepted fuel unmeasured.

    Args:
        energy: The fuel.
        raw: The items the flow was told are raw.
        unrated: What the records no flow rates do to the supply.
        uncovered: The fuel's uncovered chain inputs, empty unless it is a
            known fluid.

    Returns:
        The reasons in :data:`SUPPLY_REASONS` order. A solid carries the solid
        reason alone: it is never measured, whatever else holds. Any other fuel
        - a known fluid, or one whose item or form is unknown - carries each of
        the others that applies.
    """
    if energy.solid:
        return (REASON_SOLID_SUPPLY_UNMODELLED,)
    reasons: set[str] = set()
    if energy.item_key in raw:
        reasons.add(REASON_SUPPLY_RAW)
    if unrated.every_item or energy.item_key in unrated.related:
        reasons.add(REASON_SUPPLY_UNMEASURED)
    if uncovered:
        reasons.add(REASON_SUPPLY_INPUT_UNCOVERED)
    if unrated.unregistered_records:
        reasons.add(REASON_CLASS_UNREGISTERED)
    return _ordered(reasons, SUPPLY_REASONS)


def _supplies_of(
    basis: _Basis,
    flow: WorldFlow,
    unrated: _Unrated,
    steps: list[FuelStep],
) -> list[tuple[_Energy, Fraction | None, Fraction | None, tuple[str, ...]]]:
    """Read each accepted fuel's supply off the flow, recording each step.

    Args:
        basis: The class's basis.
        flow: The world's own flow.
        unrated: What the records no flow rates do to the supply.
        steps: The class's trace so far, appended to in order.

    Returns:
        Per accepted fuel in ``mFuel`` order, its energy, its supply per minute
        (None unless it is a known fluid that no supply reason touches), its
        supply in MW (None when either is unknown), and its supply reasons.
        A known fluid's uncovered chain inputs are each traced with their net.
    """
    raw = frozenset(flow.raw_items)
    supplies: list[tuple[_Energy, Fraction | None, Fraction | None, tuple[str, ...]]] = []
    for energy in basis.energies:
        steps += _energy_steps(energy)
        uncovered = _uncovered_inputs(flow, energy.item_key) if energy.fluid else ()
        for item_key in uncovered:
            steps.append(_read(LABEL_INPUT_NET, item_key, flow.items[item_key].net))
        line_reasons = _supply_reasons_of(energy, raw, unrated, uncovered)
        supply: Fraction | None = None
        if energy.fluid and not line_reasons:
            entry = flow.items.get(energy.item_key)
            net = entry.net if entry is not None else Fraction(0)
            supply = max(net, Fraction(0))
            steps.append(_read(LABEL_NET_FLOW, energy.item_key, net))
            steps.append(_computed(LABEL_SUPPLY, energy.item_key, supply))
        supply_mw = None
        if supply is not None and energy.megajoules_per_unit is not None:
            supply_mw = supply * energy.megajoules_per_unit / _SIXTY
            steps.append(_computed(LABEL_SUPPLY_MEGAWATTS, energy.item_key, supply_mw))
        supplies.append((energy, supply, supply_mw, line_reasons))
    return supplies


def _class_reasons(
    basis: _Basis,
    flow: WorldFlow,
    unrated: _Unrated,
    fluids: frozenset[str],
    shared_with: tuple[str, ...],
    sharing_unknown: bool,
) -> set[str]:
    """The reasons one class has before any of its fuels is read.

    Args:
        basis: The class's basis.
        flow: The world's own flow.
        unrated: What the records no flow rates do to the supply.
        fluids: Every item the registry knows as a fluid.
        shared_with: The other built classes sharing one of its fuels.
        sharing_unknown: Whether another built class's fuels are unreadable.

    Returns:
        The demand reasons plus the world's: an incomplete flow, the sharing
        reasons, and - for a class whose fuels nobody could read, which may
        burn any fluid - an unmeasured or unregistered supply.
    """
    reasons = set(basis.reasons)
    if not flow.complete:
        reasons.add(REASON_FLOW_INCOMPLETE)
    if basis.fuels is None:
        if unrated.every_item or unrated.related & fluids:
            reasons.add(REASON_SUPPLY_UNMEASURED)
        if unrated.unregistered_records:
            reasons.add(REASON_CLASS_UNREGISTERED)
    if shared_with:
        reasons.add(REASON_FUEL_SHARED)
    if sharing_unknown:
        reasons.add(REASON_FUEL_SHARING_UNKNOWN)
    return reasons


def _verdict_of(
    basis: _Basis,
    flow: WorldFlow,
    unrated: _Unrated,
    fluids: frozenset[str],
    shared_with: tuple[str, ...],
    sharing_unknown: bool,
) -> FuelVerdict:
    """Decide one class's supply verdict over the world's own flow.

    Args:
        basis: The class's basis.
        flow: The world's own flow.
        unrated: What the records no flow rates do to the supply.
        fluids: Every item the registry knows as a fluid.
        shared_with: The other built classes sharing one of its fuels.
        sharing_unknown: Whether another built class's fuels are unreadable.

    Returns:
        The verdict.
    """
    reasons = _class_reasons(basis, flow, unrated, fluids, shared_with, sharing_unknown)
    steps = list(basis.steps)
    supplies = _supplies_of(basis, flow, unrated, steps)
    pooled: Fraction | None = None if basis.fuels is None else Fraction(0)
    for _energy, _supply, supply_mw, line_reasons in supplies:
        reasons.update(line_reasons)
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
    for energy, supply, supply_mw, line_reasons in supplies:
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
                reasons=line_reasons,
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


def _extractable_by(
    extractor: Extractor, items: Mapping[str, Item], garbled: frozenset[str]
) -> frozenset[str] | None:
    """What one extractor can yield, by ruling (d), or None when unknowable.

    Args:
        extractor: The registry entry.
        items: The item namespace.
        garbled: Every subject the registry flagged with a value present but
            not a string.

    Returns:
        Its ``allowed_resources`` when that is a non-empty tuple of names; else
        every item whose form is one of its ``allowed_forms``; or None when it
        carries no restriction and its forms are unknown - a form token the
        registry did not recognize, which may admit anything, or no form at all
        on an entry the registry flagged, whose forms field may be the value it
        could not read, which reads as empty. An entry that declares no form
        and is not flagged yields nothing; a flag on an entry whose forms WERE
        read is another field's.
    """
    resources = extractor.allowed_resources
    if type(resources) is tuple and resources and all(type(name) is str for name in resources):
        return frozenset(resources)
    if extractor.unrecognized_forms:
        return None
    if not extractor.allowed_forms and extractor.key in garbled:
        return None
    return frozenset(key for key, item in items.items() if item.form in extractor.allowed_forms)


def _recipe_relations(
    registry: Registry, garbled: frozenset[str]
) -> tuple[dict[str, set[str]], frozenset[str], bool]:
    """Per producer class, every item its registry recipes name, in or out.

    Args:
        registry: The registry.
        garbled: Every subject the registry flagged with a value present but
            not a string.

    Returns:
        Class to the items its recipes name - by a resolved building or an
        unresolved token of that name - the items of every recipe one of whose
        producer tokens names no declared class, and whether some recipe the
        registry kept has a relation it could not read: flagged, and with no
        producer, no input or no output, the side a field present but not a
        string reads as. Such a recipe may be run by any class or name any
        item, so it counts as a lost one. A flagged recipe whose every side was
        read carries another field's flag; an unflagged empty side is genuine.
    """
    declared = registry.declared_classes
    by_class: dict[str, set[str]] = {}
    orphaned: set[str] = set()
    unreadable = False
    for key, recipe in registry.recipes.items():
        named = {side.item_key for side in (*recipe.inputs, *recipe.outputs)}
        producers = (*recipe.produced_in, *recipe.unresolved_produced_in)
        for producer in producers:
            by_class.setdefault(producer, set()).update(named)
        if any(producer not in declared for producer in producers):
            orphaned |= named
        if key in garbled and not (producers and recipe.inputs and recipe.outputs):
            unreadable = True
    return by_class, frozenset(orphaned), unreadable


def _record_counts(machines: WorldMachines) -> tuple[dict[object, int], dict[object, int]]:
    """Count the records no flow rates, by class: admitted, then census.

    Args:
        machines: The machines model.

    Returns:
        The admitted machines naming no recipe - generators included - and the
        census records, each per class. A census count that is not an int is
        one record, never none; a count not above zero names no record.
    """
    admitted: dict[object, int] = {}
    for state in machines.machines:
        if state.recipe_class_name is None:
            admitted[state.class_name] = admitted.get(state.class_name, 0) + 1
    census: dict[object, int] = {}
    for pairs in (machines.unadmitted_read_counts, machines.unadmitted_unread_counts):
        for class_name, count in pairs:
            records = count if type(count) is int else 1
            if records > 0:
                census[class_name] = census.get(class_name, 0) + records
    return admitted, census


def _unrated_of(machines: WorldMachines, registry: Registry) -> _Unrated:
    """Filter the records no flow rates, by ruling (b), and judge each by (a).

    Args:
        machines: The machines model.
        registry: The registry.

    Returns:
        The items the judged records relate to, whether any relation is
        unknown, and the unregistered and no-fluid record counts.
    """
    declared = registry.declared_classes
    garbled = frozenset(
        warning.subject for warning in registry.warnings if warning.code == WARN_NON_STRING_VALUE
    )
    by_class, orphaned, unreadable = _recipe_relations(registry, garbled)
    extractors = registry.extractors
    admitted, census = _record_counts(machines)
    related: set[str] = set()
    every_item = False
    judged = False
    unregistered = 0
    no_fluid = 0
    for population, is_admitted in ((admitted, True), (census, False)):
        for class_name, records in population.items():
            if type(class_name) is not str or not class_name:
                unregistered += records
                continue
            evidence = class_name in by_class or class_name in extractors
            if class_name not in declared:
                buildable = class_name.lower().startswith(_BUILDABLE_PREFIX)
                if class_name not in NO_FLUID_UNDECLARED_CLASSES and (is_admitted or buildable):
                    unregistered += records
                    continue
                # Ruling (b)'s bin, by class alone: counted whatever the
                # registry says of it. Its evidence still judges it, below.
                no_fluid += records
                if not evidence:
                    continue
            judged = True
            related |= by_class.get(class_name, set())
            if class_name in extractors:
                yields = _extractable_by(extractors[class_name], registry.items, garbled)
                if yields is None:
                    every_item = True
                else:
                    related |= yields
    if judged:
        related |= orphaned
        lost = (
            unreadable
            or registry.unknown_groups
            or any(warning.code in _RECIPE_LOSS_CODES for warning in registry.warnings)
        )
        every_item = every_item or bool(lost)
    return _Unrated(
        related=frozenset(related),
        every_item=every_item,
        unregistered_records=unregistered,
        no_fluid_records=no_fluid,
    )


def _bases_of(
    machines: WorldMachines, registry: Registry
) -> tuple[tuple[_Basis, ...], tuple[str, ...]]:
    """Partition the built generator classes into in scope and out of scope.

    A class is a GENERATOR class when the registry's generator namespace
    carries it; it is BUILT when ``WorldMachines`` admitted an instance of it or
    its census of unadmitted records counts one.

    Args:
        machines: The machines model.
        registry: The registry.

    Returns:
        The in-scope bases sorted by class name, and the out-of-scope classes.
    """
    generators = registry.generators
    flagged = frozenset(
        warning.subject for warning in registry.warnings if warning.code == WARN_UNREADABLE_FUELS
    )
    admitted: dict[str, list[MachineState]] = {}
    for state in machines.machines:
        if state.class_name in generators:
            admitted.setdefault(state.class_name, []).append(state)
    _, census = _record_counts(machines)
    omitted = {
        class_name: records
        for class_name, records in census.items()
        if type(class_name) is str and class_name in generators
    }

    bases: list[_Basis] = []
    out_of_scope: list[str] = []
    for class_name in sorted(set(admitted) | set(omitted)):
        entry = generators[class_name]
        fuels, absent = _declared_fuels(class_name, entry, flagged)
        if absent and _burns_nothing(entry):
            out_of_scope.append(class_name)
            continue
        bases.append(
            _basis_of(
                class_name,
                fuels,
                entry,
                admitted.get(class_name, []),
                omitted.get(class_name, 0),
                registry.items,
            )
        )
    return tuple(bases), tuple(out_of_scope)


def fuel_demand_of(machines: WorldMachines, registry: Registry) -> tuple[FuelDemand, ...]:
    """State what every built fuel generator class burns, claiming nothing about supply.

    PURE, AND TOTAL: unknown content is a named reason, never an exception.

    Args:
        machines: The machines model - the generators' instances and clocks.
        registry: The registry - each generator's nameplate and accepted fuels,
            and each fuel's energy value and form.

    Returns:
        One demand per built in-scope class, sorted by class name, audited
        exact on the way out.
    """
    bases, _ = _bases_of(machines, registry)
    result = tuple(_demand_of(basis) for basis in bases)
    audit_exact(result, path="fuel_demand")
    return result


def fuel_supply_of(
    machines: WorldMachines,
    registry: Registry,
    *,
    raw_items: Iterable[str] = (),
) -> WorldFuel:
    """Decide, per built fuel generator class, whether the world's own flow supplies its fuel.

    PURE, AND TOTAL: unknown content is a named reason, never an exception.
    The flow is built here, over every admitted machine of ``machines`` that
    names a recipe; no caller's flow is ever read.

    Args:
        machines: The machines model - the whole world: generators, recipe
            machines, recipe-less machines and the census.
        registry: The registry - generators, items, recipes, extractors, the
            declared classes and the warnings that say what it could not read.
        raw_items: Items declared supplied from outside the world's machines,
            handed to the flow; an accepted fuel among them is
            :data:`REASON_SUPPLY_RAW`.

    Returns:
        The verdicts and demands, audited exact on the way out.
    """
    flow = flow_of(
        tuple(state for state in machines.machines if state.recipe_class_name is not None),
        registry.recipes,
        raw_items=raw_items,
    )
    bases, out_of_scope = _bases_of(machines, registry)
    unrated = _unrated_of(machines, registry)
    fluids = frozenset(
        key for key, item in registry.items.items() if item.is_fluid and item.form in FLUID_FORMS
    )
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
        verdicts.append(_verdict_of(basis, flow, unrated, fluids, shared, sharing_unknown))
    result = WorldFuel(
        verdicts=tuple(verdicts),
        demands=tuple(_demand_of(basis) for basis in bases),
        out_of_scope=out_of_scope,
        exclusions=EXCLUSIONS,
        flow_complete=flow.complete,
        no_fluid_record_count=unrated.no_fluid_records,
        unregistered_record_count=unrated.unregistered_records,
    )
    audit_exact(result, path="fuel")
    return result
