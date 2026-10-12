"""CS-1285 slice C: the D4 fuel rule family, over the fuel supply audit.

WHAT THIS MODULE OWNS (BOOTSTRAP.md section 5.3, D4 - its fuel half). Two
rules and the adapter that feeds them:

- :data:`SUPPLY_RULE` (``power.fuel_supply``) fires when a built fuel
  generator class's pooled fuel supply falls short of its demand over a
  complete flow - the audit's FIRE verdict - naming the exact shortfall in MW
  and, on tier 3, as a per-minute rate of every accepted fuel alone. A REJECT
  is a recorded reject and settles the rule; an INDETERMINATE class is a
  recorded indeterminate step and never settles it.
- :data:`DEMAND_RULE` (``power.fuel_demand``), the companion demand card,
  fires on every INDETERMINATE class (the session 134 ruling, clause (f)) and
  on no other, stating each one's nameplate burn per accepted fuel. It
  declares no supply figure at all, so it cannot claim anything about supply.

The audit is ``clockspeed/audit/fuel.py``: :func:`fuel_inputs` flattens its
``WorldFuel`` into rule inputs. The binding rulings are the session 134 ruling
in ``docs/item_notes/phase5.md`` section CS-1285 and the slice C adjudication
of 2026-10-12, whose six clauses G1 to G6 are cited below.

THE ADAPTER FLATTENS, IT NEVER WRAPS (G3). The audit's result types are frozen
dataclasses WITHOUT slots, which the engine's exactness walk refuses
(``clockspeed/advisor/trace.py`` ``_children``), and an input NAME must match
:data:`clockspeed.advisor.trace.NAME_PATTERN`, which no class key does. So each
audit field is offered as ONE input, sourced to that field, holding a
``MappingProxyType`` keyed by class key - or by fuel key for a per-fuel figure
- whose values are ``Fraction``, ``int``, ``str``, ``None`` or a ``tuple`` of
``str``. An unknown figure is offered as None, never as a zero. The two
display-name inputs are sourced to the registry fields they are read from.

RECOMPUTED, NEVER TRUSTED (G3). A rule reads the leaf figures - nameplate,
clock sum, megajoules per unit, supply per minute - and recomputes every
figure it states through ``RuleContext.compute``: the demand, each fuel's
supply in MW, the pooled supply, the shortfall or headroom, each fuel's
shortfall rate and each fuel's burn. Each is compared with the audit's own
figure, and ANY disagreement - a fuel paired with another fuel's energy, a
FIRE whose supply covers its demand, a REJECT short of it or still carrying a
shortfall figure or rate, a negative supply (the audit floors supply at
zero), a verdict carrying a reason, an unknown verdict word - raises, which
the engine records as a ``rule-error`` with no card. Agreement catches WIRING
faults; the formulas are the audit's own (``D * 60 / E`` and ``s * E / 60``),
so a formula fault common to both is a residual this check cannot see.

THE SUBJECT IS THE SET (G1). A rule issues one card per run, so a card's
subject key is the rule's prefix plus the SORTED keys of every class it fired
on, comma-joined. A dismissal then hides that set of classes and no other: a
class joining or leaving the set is new advice. The headline is the first
class by key - for the demand card, the first with a known burn (G5) - and
its fuel the first accepted fuel in ``mFuel`` order; the others are counted
on tier 2 and every class is listed on tier 3.

SETTLEMENT IS SPLIT BY RULE (G2). The supply rule records one indeterminate
step per INDETERMINATE class, carrying every reason's fixed line, so a world
holding one never settles it and the ledger never completes a supply card on
it. The demand rule settles like ``power.draw_incomplete``: for each class it
fires on it records a REJECTED "state a supply verdict" alternative carrying
that class's reasons, and an indeterminate step only where its OWN figure, a
burn, is unknown.

AN UNKNOWN BURN IS NAMED, NEVER ZERO (G5). A class whose demand or a fuel's
energy is unknown - or whose fuels are unreadable - has each unknown burn
recorded as indeterminate with its demand reasons' fixed lines. When no fired
class has a known burn the demand card still fires, its headline asking for
the burn to be resolved.

DISPLAY NAMES FALL BACK ON RECORD (G4). :func:`fuel_inputs` offers each
registry display name verbatim; a rule naming a class or a fuel in advice text
uses the class or fuel key instead when the name is empty, blank (spaces
only) or not printable ASCII text - the registry carries empty names - and
records that fallback as a rejected alternative.

THE BUILT COUNT (fix round 2). A card counts every BUILT generator of its
headline class - those the save recorded as running machines plus those it
never did, the audit's omitted count - so its ``x<n>`` never drops one and
never reads ``x0``. When any were never read, the headline says how many
beside the count, and the reason ends with how many built generators were
never read over every fired class, in the words
``clockspeed/advisor/rules/power.py`` uses for a consumer never considered. A
FIRE or REJECT carrying a generator never read is a ``rule-error``: its
demand would be a floor, which the audit never decides on. So only the
demand card can say a generator was never read.

OUT OF SCOPE, NAMED. Supplemental resources (water) and byproducts are not
modelled; a firing card's tier 3 reads the audit's exclusion lines and records
them as out of scope. A firing card offered no exclusion line is a
``rule-error``: the out-of-scope statement is part of the advice.

EVERY FIGURE IS PRICED AT THE PINNED BUILD (CS-1288). Each nameplate, so
each demand, burn, shortfall and rate, is the PINNED build's. So each spec
declares :data:`clockspeed.advisor.build.BUILD_INPUTS` ahead of its own
:data:`SUPPLY_INPUTS` or :data:`DEMAND_INPUTS` - the read-all helper reads
only the rule's own tuple, so no name is read twice - and each rule calls
:func:`clockspeed.advisor.build.build_caveat` FIRST, on every path: tier 3
opens with the three build reads, and off the pin one indeterminate step
follows them, so no off-pin run - firing or silent - settles its rule (the
session 138 ruling F1). EVERY recommendation appends the returned caveat to
its reason, so an off-pin card names both builds on tier 2 (ruling F7); the
headline is left alone (ruling F5), and no figure changes.

UNLOCKS. Neither rule declares an unlock key, on the grounds
``clockspeed/advisor/rules/power.py`` states for the headroom rule: the advice
names no building or recipe to unlock, so a declared key would be invented.

REGISTERED WITH ITS INPUTS (G6). Slice D registers this family in the registry
in ``clockspeed/advisor/rules/__init__.py`` beside the wiring that offers its
inputs in ``clockspeed/advisor/advise.py``; slices C and D land in one push,
so a registered rule never runs on a world that lacks them.

NO WORLD TOKEN, NO PATH, NO FLOAT. Every number is an exact ``Fraction`` or an
``int`` count, rendered through :func:`clockspeed.advisor.cards.render_value`.
"""

from __future__ import annotations

from fractions import Fraction
from types import MappingProxyType
from typing import TYPE_CHECKING, Final

from clockspeed.advisor.build import BUILD_INPUTS, build_caveat
from clockspeed.advisor.cards import render_value
from clockspeed.advisor.trace import InputValue, Recommendation, RuleContext, RuleSpec
from clockspeed.audit.fuel import (
    EXCLUSION_DETAIL,
    REASON_DETAIL,
    UNIT_CUBIC_METRE,
    UNIT_ITEM,
    VERDICT_FIRE,
    VERDICT_INDETERMINATE,
    VERDICT_REJECT,
)
from clockspeed.solve.exact import SECONDS_PER_MINUTE

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Mapping

    from clockspeed.audit.fuel import FuelDemand, FuelLine, FuelVerdict, WorldFuel
    from clockspeed.data.registry import Registry

#: The advice domain every rule here belongs to.
DOMAIN: Final = "power"

#: Input names. Each holds a mapping keyed by class key unless its comment
#: says otherwise; every one is offered by :func:`fuel_inputs`.
IN_CLASSES: Final = "power.fuel.classes"  # a tuple of class keys, sorted
IN_VERDICTS: Final = "power.fuel.verdicts"
IN_REASONS: Final = "power.fuel.reasons"
IN_DEMAND_REASONS: Final = "power.fuel.demand_reasons"
IN_REASON_DETAILS: Final = "power.fuel.reason_details"  # keyed by reason code
IN_INSTANCES: Final = "power.fuel.instance_counts"
IN_OMITTED: Final = "power.fuel.omitted_counts"
IN_ELIDED: Final = "power.fuel.elided_clock_counts"
IN_NAMEPLATE: Final = "power.fuel.nameplate_mw"
IN_CLOCK_SUM: Final = "power.fuel.clock_sum"
IN_DEMAND: Final = "power.fuel.demand_mw"
IN_FUELS: Final = "power.fuel.accepted_fuels"
IN_MJ: Final = "power.fuel.mj_per_unit"  # keyed by fuel key
IN_UNITS: Final = "power.fuel.units"  # keyed by fuel key
IN_SUPPLY: Final = "power.fuel.supply_per_minute"  # class, then fuel
IN_SUPPLY_MW: Final = "power.fuel.supply_mw"  # class, then fuel
IN_POOLED: Final = "power.fuel.pooled_mw"
IN_SHORTFALL: Final = "power.fuel.shortfall_mw"
IN_SHORTFALL_RATES: Final = "power.fuel.shortfall_rates"  # class, then fuel
IN_BURNS: Final = "power.fuel.burns"  # class, then fuel
IN_EXCLUSIONS: Final = "power.fuel.exclusions"  # a tuple of fixed lines
IN_CLASS_NAMES: Final = "power.fuel.class_names"
IN_FUEL_NAMES: Final = "power.fuel.fuel_names"  # keyed by fuel key

_AUDIT_PREFIX: Final = "audit.fuel."
_CLASS_NAME_SOURCE: Final = "registry.generators.display_name"
_FUEL_NAME_SOURCE: Final = "registry.items.display_name"

#: The supply rule's own inputs, in the order it reads them - after the three
#: build inputs its spec declares ahead of them (CS-1288).
SUPPLY_INPUTS: Final = (
    IN_CLASSES,
    IN_VERDICTS,
    IN_REASONS,
    IN_REASON_DETAILS,
    IN_INSTANCES,
    IN_OMITTED,
    IN_ELIDED,
    IN_NAMEPLATE,
    IN_CLOCK_SUM,
    IN_DEMAND,
    IN_FUELS,
    IN_MJ,
    IN_UNITS,
    IN_SUPPLY,
    IN_SUPPLY_MW,
    IN_POOLED,
    IN_SHORTFALL,
    IN_SHORTFALL_RATES,
    IN_EXCLUSIONS,
    IN_CLASS_NAMES,
    IN_FUEL_NAMES,
)

#: The demand rule's own inputs, in the order it reads them - after the three
#: build inputs its spec declares ahead of them (CS-1288). No supply, pooled,
#: shortfall or headroom figure is among them.
DEMAND_INPUTS: Final = (
    IN_CLASSES,
    IN_VERDICTS,
    IN_REASONS,
    IN_DEMAND_REASONS,
    IN_REASON_DETAILS,
    IN_INSTANCES,
    IN_OMITTED,
    IN_ELIDED,
    IN_NAMEPLATE,
    IN_CLOCK_SUM,
    IN_DEMAND,
    IN_FUELS,
    IN_MJ,
    IN_UNITS,
    IN_BURNS,
    IN_EXCLUSIONS,
    IN_CLASS_NAMES,
    IN_FUEL_NAMES,
)

#: The prefixes of the two rules' subject keys (G1).
SUBJECT_SUPPLY_PREFIX: Final = "power:fuel-supply:"
SUBJECT_DEMAND_PREFIX: Final = "power:fuel-demand:"

#: Seconds per minute, as the Fraction every rate here is scaled by.
_SIXTY: Final = Fraction(SECONDS_PER_MINUTE)

#: How a unit reads in advice text.
_UNIT_WORDS: Final[Mapping[str, str]] = MappingProxyType(
    {UNIT_CUBIC_METRE: "m3", UNIT_ITEM: "items"}
)

_VERDICT_WORDS: Final = frozenset({VERDICT_FIRE, VERDICT_REJECT, VERDICT_INDETERMINATE})

_NO_CLASS: Final = "no built fuel generator class"
_NAME_FALLBACK: Final = (
    "the display name is empty, blank or not printable ASCII text, so the key names it"
)


# ---------------------------------------------------------------------------
# The adapter
# ---------------------------------------------------------------------------


def _proxy(entries: Iterable[tuple[str, object]]) -> MappingProxyType[str, object]:
    return MappingProxyType(dict(entries))


def _verbatim(name: object) -> str | None:
    """A display name as the registry holds it, or None when it is not a ``str``."""
    return name if type(name) is str else None


def _per_fuel(
    verdicts: tuple[FuelVerdict, ...], demands: tuple[FuelDemand, ...]
) -> tuple[dict[str, Fraction | None], dict[str, str | None]]:
    """Each fuel's megajoules per unit and unit, as the audit lines carry them."""
    energies: dict[str, Fraction | None] = {}
    units: dict[str, str | None] = {}
    for verdict in verdicts:
        for line in verdict.fuels:
            energies.setdefault(line.item_key, line.megajoules_per_unit)
            units.setdefault(line.item_key, line.unit)
    for demand in demands:
        for burn in demand.burns:
            energies.setdefault(burn.item_key, burn.megajoules_per_unit)
            units.setdefault(burn.item_key, burn.unit)
    return energies, units


def fuel_inputs(world_fuel: WorldFuel, registry: Registry) -> dict[str, InputValue]:
    """Offer one world's fuel audit as rule inputs, each sourced to its field.

    See the module docstring for the shape of every value. The caller wraps
    the result in a :class:`clockspeed.advisor.trace.WorldInputs` with its
    unlock set; a fresh dict is returned so a caller may add inputs from
    another layer.

    Args:
        world_fuel: The fuel audit's result.
        registry: The registry the audit ran over, read for display names only.

    Returns:
        One input per declared name of either rule.
    """
    verdicts = world_fuel.verdicts
    demands = world_fuel.demands
    energies, units = _per_fuel(verdicts, demands)
    codes = sorted(
        {code for verdict in verdicts for code in verdict.reasons}
        | {code for demand in demands for code in demand.reasons}
    )

    def by_class(read: Callable[[FuelVerdict], object]) -> MappingProxyType[str, object]:
        return _proxy((verdict.class_name, read(verdict)) for verdict in verdicts)

    def by_line(read: Callable[[FuelLine], object]) -> MappingProxyType[str, object]:
        return by_class(
            lambda verdict: _proxy((line.item_key, read(line)) for line in verdict.fuels)
        )

    fields: tuple[tuple[str, str, object], ...] = (
        (IN_CLASSES, "verdicts.class_name", tuple(v.class_name for v in verdicts)),
        (IN_VERDICTS, "verdicts.verdict", by_class(lambda v: v.verdict)),
        (IN_REASONS, "verdicts.reasons", by_class(lambda v: v.reasons)),
        (
            IN_DEMAND_REASONS,
            "demands.reasons",
            _proxy((demand.class_name, demand.reasons) for demand in demands),
        ),
        (IN_REASON_DETAILS, "REASON_DETAIL", _proxy((c, REASON_DETAIL.get(c)) for c in codes)),
        (IN_INSTANCES, "verdicts.instance_count", by_class(lambda v: v.instance_count)),
        (IN_OMITTED, "verdicts.omitted_count", by_class(lambda v: v.omitted_count)),
        (IN_ELIDED, "verdicts.elided_clock_count", by_class(lambda v: v.elided_clock_count)),
        (IN_NAMEPLATE, "verdicts.nameplate_megawatts", by_class(lambda v: v.nameplate_megawatts)),
        (IN_CLOCK_SUM, "verdicts.clock_sum", by_class(lambda v: v.clock_sum)),
        (IN_DEMAND, "verdicts.demand_megawatts", by_class(lambda v: v.demand_megawatts)),
        (IN_FUELS, "verdicts.accepted_fuels", by_class(lambda v: v.accepted_fuels)),
        (IN_MJ, "verdicts.fuels.megajoules_per_unit", _proxy(energies.items())),
        (IN_UNITS, "verdicts.fuels.unit", _proxy(units.items())),
        (IN_SUPPLY, "verdicts.fuels.supply_per_minute", by_line(lambda f: f.supply_per_minute)),
        (IN_SUPPLY_MW, "verdicts.fuels.supply_megawatts", by_line(lambda f: f.supply_megawatts)),
        (IN_POOLED, "verdicts.pooled_megawatts", by_class(lambda v: v.pooled_megawatts)),
        (IN_SHORTFALL, "verdicts.shortfall_megawatts", by_class(lambda v: v.shortfall_megawatts)),
        (
            IN_SHORTFALL_RATES,
            "verdicts.fuels.shortfall_per_minute",
            by_line(lambda f: f.shortfall_per_minute),
        ),
        (
            IN_BURNS,
            "demands.burns.burn_per_minute",
            _proxy(
                (demand.class_name, _proxy((b.item_key, b.burn_per_minute) for b in demand.burns))
                for demand in demands
            ),
        ),
        (
            IN_EXCLUSIONS,
            "exclusions",
            tuple(EXCLUSION_DETAIL.get(code) for code in world_fuel.exclusions),
        ),
    )
    offered = {name: InputValue(value, _AUDIT_PREFIX + field) for name, field, value in fields}
    generators = registry.generators
    items = registry.items
    offered[IN_CLASS_NAMES] = InputValue(
        _proxy(
            (
                verdict.class_name,
                _verbatim(generators[verdict.class_name].display_name)
                if verdict.class_name in generators
                else None,
            )
            for verdict in verdicts
        ),
        _CLASS_NAME_SOURCE,
    )
    offered[IN_FUEL_NAMES] = InputValue(
        _proxy(
            (key, _verbatim(items[key].display_name) if key in items else None) for key in energies
        ),
        _FUEL_NAME_SOURCE,
    )
    return offered


# ---------------------------------------------------------------------------
# Reading - every shape is checked, anything else is a rule error
# ---------------------------------------------------------------------------


def _read_all(ctx: RuleContext, names: tuple[str, ...]) -> dict[str, object]:
    """Read every declared input, in declared order, before deciding anything."""
    return {name: ctx.read(name) for name in names}


def _mapping(value: object) -> Mapping[str, object]:
    if type(value) is not MappingProxyType:
        raise TypeError("a fuel input is not a read-only mapping")
    return value


def _entry(values: Mapping[str, object], name: str, key: str) -> object:
    return _mapping(values[name])[key]


def _fuel_entry(values: Mapping[str, object], name: str, key: str, fuel: str) -> object:
    return _mapping(_entry(values, name, key))[fuel]


def _fraction(value: object) -> Fraction | None:
    if value is None or type(value) is Fraction:
        return value
    raise TypeError("a fuel figure is not a Fraction or None")


def _known(value: object) -> Fraction:
    figure = _fraction(value)
    if figure is None:
        raise ValueError("a fuel figure the verdict rests on is unknown")
    return figure


def _count(value: object) -> int:
    if type(value) is not int or value < 0:
        raise TypeError("a fuel count is not a non-negative int")
    return value


def _strings(value: object) -> tuple[str, ...]:
    if type(value) is not tuple or not all(type(part) is str for part in value):
        raise TypeError("a fuel input is not a tuple of str")
    return value


def _printable(value: object) -> bool:
    """The engine's text test: printable ASCII ``str`` with a visible character."""
    return type(value) is str and value.strip(" ") != "" and all(" " <= ch <= "~" for ch in value)


def _classes(values: Mapping[str, object]) -> list[tuple[str, str]]:
    """Every class with its verdict word, sorted by class key.

    Raises:
        ValueError: a verdict word outside the audit's closed vocabulary.
    """
    pairs = []
    for key in sorted(_strings(values[IN_CLASSES])):
        verdict = _entry(values, IN_VERDICTS, key)
        if verdict not in _VERDICT_WORDS:
            raise ValueError("a fuel verdict word is not one the audit defines")
        pairs.append((key, str(verdict)))
    return pairs


def _details(values: Mapping[str, object], codes: tuple[str, ...]) -> str:
    """The fixed lines of ``codes``, joined; an unknown code or a bad line raises."""
    lines = [_entry(values, IN_REASON_DETAILS, code) for code in codes]
    if not lines or not all(_printable(line) for line in lines):
        raise ValueError("a fuel reason has no fixed line")
    return "; ".join(str(line) for line in lines)


def _agree(computed: Fraction, audit: object) -> Fraction:
    """Return ``computed`` when the audit's own figure is exactly it; raise otherwise."""
    if type(audit) is not Fraction or audit != computed:
        raise ValueError("a recomputed fuel figure disagrees with the audit")
    return computed


def _demand(ctx: RuleContext, values: Mapping[str, object], key: str) -> Fraction | None:
    """Recompute a class's demand from its nameplate and clock sum, when the audit knows it."""
    audit = _fraction(_entry(values, IN_DEMAND, key))
    if audit is None:
        return None
    nameplate = _known(_entry(values, IN_NAMEPLATE, key))
    clock_sum = _known(_entry(values, IN_CLOCK_SUM, key))
    demand = ctx.compute(f"demand MW of {key}, nameplate times clock sum", nameplate * clock_sum)
    return _agree(demand, audit)


def _energy(values: Mapping[str, object], fuel: str) -> Fraction | None:
    return _fraction(_mapping(values[IN_MJ])[fuel])


def _unit(values: Mapping[str, object], fuel: str) -> str:
    return _UNIT_WORDS[str(_mapping(values[IN_UNITS])[fuel])]


def _name(ctx: RuleContext, values: Mapping[str, object], names: str, key: str) -> str:
    """A class's or a fuel's display name, or its key - the fallback on record (G4).

    A blank name - spaces only - is no name: :func:`_printable` wants a
    visible character.
    """
    name = _mapping(values[names]).get(key)
    if _printable(name):
        return str(name)
    ctx.reject(f"name {key} by its display name", _NAME_FALLBACK)
    return key


def _plural(count: int, singular: str, plural: str) -> str:
    return f"{count} {singular if count == 1 else plural}"


def _others(count: int, state: str) -> str:
    """The reason suffix counting the other fired classes, or nothing."""
    if count == 0:
        return ""
    classes = _plural(count, "other generator class is", "other generator classes are")
    return f"; {classes} {state} too"


def _generators(ctx: RuleContext, values: Mapping[str, object], key: str) -> tuple[str, str]:
    """The headline's and the reason's generator label, counting every BUILT generator.

    The count is the generators the save recorded as running machines plus
    those it never did, so none drops out and no label reads ``x0``.

    Returns:
        ``(headline, reason)``: the headline's label adds how many were never
        read when any were; the reason's leaves that to :func:`_omission`.
    """
    omitted = _count(_entry(values, IN_OMITTED, key))
    built = _count(_entry(values, IN_INSTANCES, key)) + omitted
    label = f"{_name(ctx, values, IN_CLASS_NAMES, key)} x{built}"
    return (f"{label} ({omitted} never read)" if omitted else label), label


def _omission(values: Mapping[str, object], keys: list[str]) -> str:
    """The reason suffix counting built generators the save never read, or nothing.

    Summed over every fired class, in the words ``power.draw_incomplete`` uses
    for a built consumer the draw never considered.
    """
    omitted = sum(_count(_entry(values, IN_OMITTED, key)) for key in keys)
    if omitted == 0:
        return ""
    generators = _plural(omitted, "built generator was", "built generators were")
    return f"; {generators} never read"


def _elision(values: Mapping[str, object], keys: list[str]) -> str:
    """The reason suffix naming generators priced at the default clock, or nothing."""
    elided = sum(_count(_entry(values, IN_ELIDED, key)) for key in keys)
    if elided == 0:
        return ""
    generators = _plural(elided, "generator", "generators")
    return f"; it assumes the default clock for {generators} whose save omits the clock tag"


def _exclusions(ctx: RuleContext, values: Mapping[str, object]) -> None:
    """Record supplemental resources and byproducts as out of scope, from the audit's lines."""
    lines = _strings(values[IN_EXCLUSIONS])
    if not lines:
        raise ValueError("a firing fuel card has no out-of-scope line to name")
    ctx.reject("size supplemental resources and byproducts", "out of scope: " + "; ".join(lines))


def _subject(prefix: str, keys: list[str]) -> str:
    return prefix + ",".join(sorted(keys))


# ---------------------------------------------------------------------------
# power.fuel_supply
# ---------------------------------------------------------------------------


def _pooled(ctx: RuleContext, values: Mapping[str, object], key: str) -> Fraction:
    """Recompute every accepted fuel's supply in MW and their pool, each checked."""
    fuels = _strings(_entry(values, IN_FUELS, key))
    if not fuels:
        raise ValueError("a decided fuel class has no accepted fuel")
    pooled = Fraction(0)
    for fuel in fuels:
        energy = _known(_energy(values, fuel))
        supply = _known(_fuel_entry(values, IN_SUPPLY, key, fuel))
        if supply < 0:
            raise ValueError("a fuel supply is negative, which the audit never offers")
        supply_mw = ctx.compute(
            f"supply MW of {fuel} for {key}, supply times MJ over sixty",
            supply * energy / _SIXTY,
        )
        pooled += _agree(supply_mw, _fuel_entry(values, IN_SUPPLY_MW, key, fuel))
    ctx.compute(f"pooled supply MW of {key}", pooled)
    return _agree(pooled, _entry(values, IN_POOLED, key))


def _decided_demand(ctx: RuleContext, values: Mapping[str, object], key: str) -> Fraction:
    if _strings(_entry(values, IN_REASONS, key)):
        raise ValueError("a decided fuel verdict carries an indeterminate reason")
    if _count(_entry(values, IN_OMITTED, key)):
        raise ValueError("a decided fuel verdict has built generators the save never read")
    demand = _demand(ctx, values, key)
    if demand is None:
        raise ValueError("a decided fuel verdict has no demand")
    return demand


def _fire(ctx: RuleContext, values: Mapping[str, object], key: str) -> Fraction:
    """Recompute a FIRE class's shortfall and every fuel's rate; return the shortfall."""
    demand = _decided_demand(ctx, values, key)
    pooled = _pooled(ctx, values, key)
    shortfall = ctx.compute(f"shortfall MW of {key}, demand less pooled supply", demand - pooled)
    if shortfall <= 0:
        raise ValueError("a FIRE verdict's pooled supply covers its demand")
    _agree(shortfall, _entry(values, IN_SHORTFALL, key))
    for fuel in _strings(_entry(values, IN_FUELS, key)):
        rate = ctx.compute(
            f"shortfall per minute of {fuel} alone for {key}",
            shortfall * _SIXTY / _known(_energy(values, fuel)),
        )
        _agree(rate, _fuel_entry(values, IN_SHORTFALL_RATES, key, fuel))
    return shortfall


def _reject(ctx: RuleContext, values: Mapping[str, object], key: str) -> None:
    """Recompute a REJECT class's headroom, which must not be negative."""
    demand = _decided_demand(ctx, values, key)
    pooled = _pooled(ctx, values, key)
    headroom = ctx.compute(f"headroom MW of {key}, pooled supply less demand", pooled - demand)
    if headroom < 0:
        raise ValueError("a REJECT verdict's pooled supply falls short of its demand")
    stray = [_entry(values, IN_SHORTFALL, key)] + [
        _fuel_entry(values, IN_SHORTFALL_RATES, key, fuel)
        for fuel in _strings(_entry(values, IN_FUELS, key))
    ]
    if any(figure is not None for figure in stray):
        raise ValueError("a REJECT verdict carries a shortfall figure")
    ctx.reject(f"add fuel supply for {key}", "pooled supply covers demand over a complete flow")


def _evaluate_supply(ctx: RuleContext) -> Recommendation | None:
    """Recommend more fuel for every class whose pooled supply falls short of its demand."""
    caveat = build_caveat(ctx)
    values = _read_all(ctx, SUPPLY_INPUTS)
    classes = _classes(values)
    if not classes:
        ctx.reject("add fuel supply", _NO_CLASS)
        return None
    shortfalls: dict[str, Fraction] = {}
    for key, verdict in classes:
        if verdict == VERDICT_FIRE:
            shortfalls[key] = _fire(ctx, values, key)
        elif verdict == VERDICT_REJECT:
            _reject(ctx, values, key)
        else:
            ctx.indeterminate(
                f"compare the pooled fuel supply against the demand of {key}",
                _details(values, _strings(_entry(values, IN_REASONS, key))),
            )
    if not shortfalls:
        return None
    fired = sorted(shortfalls)
    key = fired[0]
    fuel = _strings(_entry(values, IN_FUELS, key))[0]
    energy = _known(_energy(values, fuel))
    rate = render_value(shortfalls[key] * _SIXTY / energy)
    unit = _unit(values, fuel)
    headline, generators = _generators(ctx, values, key)
    fuel_name = _name(ctx, values, IN_FUEL_NAMES, fuel)
    demand = render_value(_known(_entry(values, IN_DEMAND, key)))
    pooled = render_value(_known(_entry(values, IN_POOLED, key)))
    _exclusions(ctx, values)
    return Recommendation(
        subject_key=_subject(SUBJECT_SUPPLY_PREFIX, fired),
        action=f"Supply {rate} {unit} more {fuel_name} per minute to {headline}",
        reason=(
            f"{generators} demand {demand} MW but the pooled supply of every accepted fuel"
            f" yields {pooled} MW: {render_value(shortfalls[key])} MW short, which is"
            f" {rate} {unit} of {fuel_name} per minute alone"
            f"{_others(len(fired) - 1, 'short')}{_elision(values, fired)}{caveat}"
        ),
    )


# ---------------------------------------------------------------------------
# power.fuel_demand
# ---------------------------------------------------------------------------


def _burns(ctx: RuleContext, values: Mapping[str, object], key: str) -> list[tuple[str, Fraction]]:
    """Recompute every known burn of one class; record each unknown one (G5).

    Returns:
        The known burns, fuel and figure, in ``mFuel`` order.
    """
    demand = _demand(ctx, values, key)
    fuels = _strings(_entry(values, IN_FUELS, key))
    demand_codes = _strings(_entry(values, IN_DEMAND_REASONS, key))
    known: list[tuple[str, Fraction]] = []
    for fuel in fuels:
        energy = _energy(values, fuel)
        audit = _fraction(_fuel_entry(values, IN_BURNS, key, fuel))
        if demand is not None and energy is not None:
            burn = ctx.compute(f"burn per minute of {fuel} for {key}", demand * _SIXTY / energy)
            known.append((fuel, _agree(burn, audit)))
            continue
        if audit is not None:
            raise ValueError("the audit states a burn the rule cannot recompute")
        ctx.indeterminate(f"state the burn of {fuel} for {key}", _details(values, demand_codes))
    if not fuels:
        ctx.indeterminate(f"state the burn of {key}", _details(values, demand_codes))
    return known


def _evaluate_demand(ctx: RuleContext) -> Recommendation | None:
    """State the nameplate burn of every class whose supply has no verdict."""
    caveat = build_caveat(ctx)
    values = _read_all(ctx, DEMAND_INPUTS)
    classes = _classes(values)
    if not classes:
        ctx.reject("state a fuel burn", _NO_CLASS)
        return None
    fired = [key for key, verdict in classes if verdict == VERDICT_INDETERMINATE]
    if not fired:
        ctx.reject("state a fuel burn", "the supply rule decides every built fuel generator class")
        return None
    known: dict[str, list[tuple[str, Fraction]]] = {}
    for key in fired:
        reasons = _strings(_entry(values, IN_REASONS, key))
        ctx.reject(f"state a supply verdict for {key}", _details(values, reasons))
        known[key] = _burns(ctx, values, key)
    with_burn = [key for key in fired if known[key]]
    key = with_burn[0] if with_burn else fired[0]
    headline, generators = _generators(ctx, values, key)
    tail = (
        f"{_others(len(fired) - 1, 'undecided')}{_omission(values, fired)}{_elision(values, fired)}"
    )
    if with_burn:
        fuel, burn = known[key][0]
        quantity = f"{render_value(burn)} {_unit(values, fuel)}"
        fuel_name = _name(ctx, values, IN_FUEL_NAMES, fuel)
        demand = render_value(_known(_entry(values, IN_DEMAND, key)))
        detail = _details(values, _strings(_entry(values, IN_REASONS, key))[:1])
        action = f"Plan {quantity} of {fuel_name} per minute for {headline}"
        reason = (
            f"{generators} burn {quantity} of {fuel_name} per minute at a demand of"
            f" {demand} MW, with no supply verdict: {detail}{tail}"
        )
    else:
        detail = _details(values, _strings(_entry(values, IN_DEMAND_REASONS, key))[:1])
        action = f"Resolve the fuel burn of {headline} before planning its fuel"
        reason = (
            f"The burn of {generators} is unknown, never zero, with no supply verdict:"
            f" {detail}{tail}"
        )
    _exclusions(ctx, values)
    return Recommendation(
        subject_key=_subject(SUBJECT_DEMAND_PREFIX, fired), action=action, reason=reason + caveat
    )


SUPPLY_RULE: Final = RuleSpec(
    rule_id="power.fuel_supply",
    domain=DOMAIN,
    inputs=(*BUILD_INPUTS, *SUPPLY_INPUTS),
    unlocks=(),
    evaluate=_evaluate_supply,
)

DEMAND_RULE: Final = RuleSpec(
    rule_id="power.fuel_demand",
    domain=DOMAIN,
    inputs=(*BUILD_INPUTS, *DEMAND_INPUTS),
    unlocks=(),
    evaluate=_evaluate_demand,
)

#: Every rule this family holds, in rule-id order. Registered by slice D (G6).
RULES: Final = (DEMAND_RULE, SUPPLY_RULE)
