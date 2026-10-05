"""CS-1045: the world power balance - draw over built counts, and starved machines.

WHAT THIS MODULE OWNS
-----------------------
Two pure functions and one that composes them. The first multiplies a per-class
declared draw by how many of that class are BUILT and sums exactly; the second
flags the machines that have work to do and are not doing it. Neither reads a
save, a docs file or the install. Their inputs are the models the layer below
already publishes: ``clockspeed/audit/placement.py`` ``WorldPlacement`` for the
built counts, ``clockspeed/audit/machines.py`` ``WorldMachines`` for the
producing flag, ``clockspeed/audit/network.py`` ``WorldNetwork`` for what the
topology half cannot yet answer, and ``clockspeed/solve/power.py`` for what a
building's entry declares.

THIS IS THE FIRST MODULE IN ``audit/`` TO CONSUME ``solve/``, and that is the
seam the package's own ``__init__`` docstring already declares: "Below this
layer are two stated models: the world model from clockspeed.save.world and the
results of clockspeed.solve." ``Building`` is imported for its TYPE ONLY, under
``TYPE_CHECKING``. Nothing here builds one, reads one out of ``data/``, or
touches the registry: a caller supplies the mapping, which keeps the runtime
dependency exactly one layer deep.

THE CLOCKED DRAW (CS-1263) - A BRACKET, NOT A GUESS
-----------------------------------------------------
:func:`draw_of` prices BUILT COUNTS at the reference clock. A world's machines
run at their own clocks, so :func:`clocked_draw_of` reads every
``MachineState.overclock`` and prices each machine at it. The power law is
``draw * clock ** exponent`` and the shipped exponent is not whole, so away from
the reference clock the draw has no exact rational value -
``clockspeed/solve/power.py::draw_at_clock`` defers it. The answer here is the
EXACT BRACKET the law takes at the two whole exponents either side of the
declared one, published as a named bound beside the exact value wherever the law
does yield one (the reference clock, a whole exponent, a zero clock). A clock
this reader never read is a NAMED GAP and never priced at one - a confident one
is the confident zero one field over. Nothing here reads a fractional machine
count: a world has whole machines.

THE CONFIDENT ZERO IS THE FAILURE MODE THIS MODULE IS BUILT AGAINST
---------------------------------------------------------------------
Non-negotiable 7 says unknown content is flagged and skipped, never silently
wrong. A built class whose draw the registry does not model, contributing ZERO
to a world total, produces a number that LOOKS like a measurement and is not
one - and unlike a float, which ``contract.encode`` refuses outright, a zero is
accepted everywhere and detected nowhere. ``clockspeed/data/registry.py``
``Building.power_consumption`` states the same thing about its own None:
"Publishing zero for the None cases is the one unacceptable option, because a
confident zero is exactly what a power plan cannot detect."

So the answer here is a PARTITION rather than a total. Every built class lands
in exactly one of two buckets:

- :class:`DrawContribution`, which carries a count and two exact Fractions, and
  which ONLY a class with a modeled scalar draw may enter; or
- :class:`DrawGap`, which carries a count, a NAMED kind and a reason, and
  **which declares no megawatts field at all**.

THE ZERO IS THEREFORE STRUCTURALLY UNREPRESENTABLE, not merely absent today.
There is no field on a gap for a consumer to read a zero out of and no field for
a later change to default to zero, which is a stronger guarantee than an
Optional that happens to be None - an Optional is one careless ``or 0`` away
from the defect, and a missing field is a ``AttributeError``. The buckets
conserve: ``len(contributions) + len(gaps) == len(built_counts)``, asserted by
``tests/audit/test_balance.py::test_the_two_buckets_partition_the_built_classes_with_conservation``,
so a class this module dropped cannot be expressed. That is the shape
``docs/item_notes/phase5.md`` records for CS-1042 - an Optional, a flag and a
count are each individually ignorable, and a partition with conservation is not.

AND THE GAP IS NAMED PER CONTRIBUTOR, NEVER POOLED. A total that is correct in
aggregate can still hide a class whose draw was never modelled, so each gap
carries the class it is about, how many are built, and WHICH of the four ways
the draw went missing. The three registry-side kinds are
``clockspeed/solve/power.py``'s own ``SHAPE_*`` constants carried VERBATIM,
along with that module's reason line, so the vocabulary has exactly one owner
and this module cannot drift a second spelling of "the entry declares a range".

THE FOURTH AND FIFTH KINDS ARE THIS MODULE'S OWN, because they are facts about
the JOIN rather than about a declaration. :data:`GAP_NO_REGISTRY_ENTRY` is a
built class the supplied registry does not carry - modded content, or content
this project has not modelled - and it is the one case that would otherwise
vanish silently, since there is no entry to ask. :data:`GAP_DRAW_INEXACT` is a
declared scalar that is not exactly a ``Fraction``: non-negotiable 6 forbids a
float in the solve path, and the right response to one is a named gap rather
than an exception, because a single bad entry must not cost a world its whole
power answer.

WHAT IS DECLARED ABSENT RATHER THAN REPORTED AS ZERO
-------------------------------------------------------
**PRODUCTION IS COMPUTED ONLY WHEN A GENERATOR NAMESPACE IS SUPPLIED** (CS-1059).
``clockspeed/data/registry.py`` ``Registry.generators`` reads each generator's
``mPowerProduction`` as an exact Fraction. :func:`production_of` sums it over the
built counts into the same PARTITION the draw uses: :class:`ProductionContribution`
for a generator with an exact scalar output, :class:`ProductionGap` - which, like
:class:`DrawGap`, DECLARES NO MEGAWATTS FIELD - for a generator whose output is
variable, undeclared or inexact, and for a built class neither namespace carries,
since nothing can say it does not generate. The geothermal generator declares its
scalar as zero and carries its output on the variable fields; summing that zero is
the confident zero one field over, so it is a named gap.

:attr:`WorldBalance.production_available` is DERIVED: it is whether a production
model was computed, and nothing else. With no namespace, or an empty one, there is
nothing to sum, the flag is False and :data:`WARN_BALANCE_PRODUCTION_UNMODELED`
says why - a production total of zero beside a real consumption total would render
every world in permanent brownout. No generator class list is invented here; the
registry's own marker fields decide membership.

THE FIGURE IS A NAMEPLATE CAPACITY at the reference clock over built counts, and
:data:`WARN_BALANCE_PRODUCTION_NAMEPLATE` travels with every computed one. A
generator's clock law and its fuel state are not modelled, so this is what the
built generators are rated for and never what they are producing now.

A GENERATOR IS NOT A CONSUMER. Every measured generator also declares a zero
draw, so it lands in the consumer namespace too. Once the generator namespace is
supplied, :func:`draw_of` and :func:`clocked_draw_of` take generator classes out of
the draw partition and COUNT them apart, so none is lost and none is listed as a
zero-draw consumer.

**THE CONNECTED EDGE SET IS DERIVED, NOT ASSERTED.**
:attr:`WorldBalance.connected_edges_available` is read off
``WorldNetwork.belt_topology_available`` rather than hardcoded False, so it
starts answering True on its own the day belt topology lands, and an arm can
force the input flag and watch the output follow. CS-1041 shipped that flag
false on purpose - which belt feeds which machine is one of the two questions
its own acceptance does not grade - so the red outline a panel would draw over
a starved machine's upstream segment has no edge set behind it yet, and this
module says so instead of drawing one from proximity.

WHAT "STARVED" MEANS HERE, AND WHAT IT DELIBERATELY DOES NOT
---------------------------------------------------------------
A machine is STARVED when it carries a recipe and is not producing. The two
clauses are both load-bearing and neither is decoration.

- Without the producing flag there is no finding at all, which is why
  ``tests/audit/test_balance.py::test_the_flagged_set_reddens_when_the_producing_flag_is_ignored``
  grades a fixture of two machines alike in every other field.
- Without the recipe clause an unconfigured machine - one nobody has set a
  recipe on - reads as starved, and a fresh factory full of them would bury the
  one finding that matters.

A MACHINE WHOSE PRODUCING FLAG NEVER READ IS NEVER FLAGGED AND ALWAYS COUNTED.
``MachineState.producing`` is three-state and None means this reader saw no such
tag; treating None as False would flag every machine in a world whose payloads
did not decode. It is counted in :attr:`WorldStarvation.unknown_state_count`,
and the four categories conserve against
:attr:`WorldStarvation.machines_considered` for the same reason the draw buckets
do.

A FINDING HERE IS HALF AN AUDIT AND THIS MODULE SAYS SO. The package
``__init__`` states the whole rule: "This machine is idle" is half an audit;
"this machine is idle because the segment upstream is saturated" is the whole
one. The upstream cause needs the edge set, which does not exist yet, so
:data:`WARN_BALANCE_UPSTREAM_CAUSE_UNAVAILABLE` travels with every balance that
has no topology behind it rather than letting a bare symptom read as a complete
finding.

A FLAGGED INDEX IS A POSITION IN A PUBLISHED POPULATION AND NOTHING ELSE. It
indexes ``WorldMachines.machines``, which ``MachineState``'s own docstring
declares the join key for exactly this purpose. It is not a record index, not a
byte offset and not a path, and it names nothing an operator built.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from fractions import Fraction
from types import MappingProxyType
from typing import TYPE_CHECKING, Final

from clockspeed.save.world import WorldWarning
from clockspeed.solve.exact import audit_exact
from clockspeed.solve.power import (
    OUTCOME_DEFERRED,
    OUTCOME_NOT_SCALABLE,
    OUTCOME_UNDEFINED,
    REFERENCE_CLOCK,
    SHAPE_RANGE_ONLY,
    SHAPE_UNDECLARED,
    SHAPE_VARIABLE,
    declared_draw,
    draw_at_clock,
)

if TYPE_CHECKING:
    from collections.abc import Mapping

    from clockspeed.audit.machines import WorldMachines
    from clockspeed.audit.network import WorldNetwork
    from clockspeed.audit.placement import WorldPlacement
    from clockspeed.data.registry import Building, Generator

__all__ = [
    "BOUND_EXACT",
    "BOUND_EXPONENT_BRACKET",
    "BOUND_KINDS",
    "CLOCKED_GAP_KINDS",
    "ELIDED_CLOCK_DEFAULT",
    "GAP_CLOCK_UNREAD",
    "GAP_DRAW_INEXACT",
    "GAP_KINDS",
    "GAP_LAW_INEXACT",
    "GAP_NO_REGISTRY_ENTRY",
    "GAP_PRODUCTION_INEXACT",
    "GAP_PRODUCTION_UNDECLARED",
    "GAP_PRODUCTION_VARIABLE",
    "PRODUCTION_GAP_KINDS",
    "SOURCE_BALANCE",
    "WARN_BALANCE_CLOCKED_DRAW_BOUNDED",
    "WARN_BALANCE_CLOCKED_DRAW_UNMODELED",
    "WARN_BALANCE_CLOCK_ELIDED",
    "WARN_BALANCE_CLOCK_UNREAD",
    "WARN_BALANCE_DRAW_UNMODELED",
    "WARN_BALANCE_GENERATION_UNMODELED",
    "WARN_BALANCE_MACHINE_STATE_UNREAD",
    "WARN_BALANCE_NOTHING_BUILT",
    "WARN_BALANCE_NO_MACHINES_CLOCKED",
    "WARN_BALANCE_PRODUCING_UNAVAILABLE",
    "WARN_BALANCE_PRODUCTION_NAMEPLATE",
    "WARN_BALANCE_PRODUCTION_UNMODELED",
    "WARN_BALANCE_UPSTREAM_CAUSE_UNAVAILABLE",
    "ClockedContribution",
    "ClockedGap",
    "DrawContribution",
    "DrawGap",
    "ProductionContribution",
    "ProductionGap",
    "WorldBalance",
    "WorldClockedDraw",
    "WorldDraw",
    "WorldProduction",
    "WorldStarvation",
    "balance_of",
    "clocked_draw_of",
    "draw_of",
    "production_of",
    "starvation_of",
]

#: Which layer noticed a warning raised here, for ``WorldWarning.source``.
SOURCE_BALANCE: Final = "balance"

#: A built class the supplied registry does not carry at all. THE ONE GAP THAT
#: HAS NO DECLARATION BEHIND IT - there is no entry to ask, so without this kind
#: the class would leave no trace anywhere in the answer.
GAP_NO_REGISTRY_ENTRY: Final = "no-registry-entry"

#: A declared scalar draw that is not exactly a ``Fraction``. Non-negotiable 6
#: forbids a float in the solve path, and a gap is the right refusal here rather
#: than an exception: one bad entry must not cost a world its power answer.
GAP_DRAW_INEXACT: Final = "draw-inexact"

#: The closed vocabulary of gap kinds. Three are ``clockspeed/solve/power.py``'s
#: own shape constants carried verbatim so that module stays their one owner;
#: two are this module's, and are facts about the join rather than about a
#: declaration. Published so a consumer can branch on a complete list.
GAP_KINDS: Final = frozenset(
    {
        SHAPE_RANGE_ONLY,
        SHAPE_VARIABLE,
        SHAPE_UNDECLARED,
        GAP_NO_REGISTRY_ENTRY,
        GAP_DRAW_INEXACT,
    }
)

#: CS-1059. A generator whose output VARIES - it declares a variable production
#: factor or constant above zero. Its declared scalar, measured as zero on the
#: geothermal generator, is not its output and is never summed.
GAP_PRODUCTION_VARIABLE: Final = "production-variable"

#: CS-1059. A generator whose entry declares no readable scalar output.
GAP_PRODUCTION_UNDECLARED: Final = "production-undeclared"

#: CS-1059. A declared scalar output that is not exactly a ``Fraction``,
#: refused on the terms :data:`GAP_DRAW_INEXACT` states.
GAP_PRODUCTION_INEXACT: Final = "production-inexact"

#: CS-1059. The closed vocabulary of production gap kinds: the three above,
#: and :data:`GAP_NO_REGISTRY_ENTRY` for a built class neither namespace
#: carries - it may generate, and nothing here can say it does not.
PRODUCTION_GAP_KINDS: Final = frozenset(
    {
        GAP_PRODUCTION_VARIABLE,
        GAP_PRODUCTION_UNDECLARED,
        GAP_PRODUCTION_INEXACT,
        GAP_NO_REGISTRY_ENTRY,
    }
)

#: CS-1263. A machine whose clock this reader never read - the tag was absent,
#: or ``clockspeed/audit/machines.py`` refused its value. NEVER PRICED AT ONE:
#: one is the reference clock, and a machine nobody measured is not at it.
GAP_CLOCK_UNREAD: Final = "clock-unread"

#: CS-1263. The clock or the declared exponent is not exactly a ``Fraction``,
#: so the power law cannot be applied without a float, and is not applied.
GAP_LAW_INEXACT: Final = "law-inexact"

#: The closed vocabulary of gap kinds :func:`clocked_draw_of` can publish: every
#: kind :func:`draw_of` can, the two above, and
#: ``clockspeed/solve/power.py``'s own outcome words for an entry that is not
#: clock-scalable and a clock that has no real draw, carried verbatim.
CLOCKED_GAP_KINDS: Final = GAP_KINDS | frozenset(
    {GAP_CLOCK_UNREAD, GAP_LAW_INEXACT, OUTCOME_NOT_SCALABLE, OUTCOME_UNDEFINED}
)

#: A clocked group whose draw the power law yields EXACTLY - the reference clock,
#: a whole exponent, or a zero clock under a positive one. Its two ends are equal.
BOUND_EXACT: Final = "exact"

#: A clocked group whose draw has no exact rational value, published as the
#: exact bracket the law takes at the two whole exponents either side of the
#: declared one. ``clock ** e`` is monotone in ``e`` for any positive clock, so
#: the bracket holds for every exponent and orientation - see :func:`_bracket`.
BOUND_EXPONENT_BRACKET: Final = "exponent-bracket"

#: The closed vocabulary of bound kinds, published so a consumer can branch on it.
BOUND_KINDS: Final = frozenset({BOUND_EXACT, BOUND_EXPONENT_BRACKET})

#: The clock a machine runs at when its ``mCurrentPotential`` tag was ELIDED -
#: ``MachineState.overclock_elided``. The save serializer writes no tag for a
#: value equal to the class default, and the class default is the reference
#: clock (``clockspeed/audit/machines.py`` module docstring; ADR 0005 records
#: the property as ``SaveGame`` on ``FGBuildableFactory``). MEASURED for
#: CS-1263 over the save library: no present tag carried exactly one, while
#: most machines carried no tag at all. A clock that is absent for any OTHER
#: reason - an unread payload, a disagreeing tag, a refused value - is still
#: :data:`GAP_CLOCK_UNREAD` and never this.
ELIDED_CLOCK_DEFAULT: Final = REFERENCE_CLOCK

#: This many BUILT ACTORS - not classes - contributed no number to the world
#: draw. The consumption total below them is a lower bound and nothing more.
WARN_BALANCE_DRAW_UNMODELED: Final = "balance-draw-unmodeled"

#: The placement model carried no built class at all, so the world draw is zero
#: because there was nothing to sum. Flagged rather than reported as a measured
#: zero: a world with nothing built and a world whose built actors were all
#: filtered out produce the identical number.
WARN_BALANCE_NOTHING_BUILT: Final = "balance-nothing-built"

#: No machine in this world carried a readable producing flag, so the empty
#: starved set means "nothing could be measured" and never "nothing is starved".
WARN_BALANCE_PRODUCING_UNAVAILABLE: Final = "balance-producing-unavailable"

#: This many machines carried no producing flag and were neither flagged nor
#: counted as running. The starved set is short by whatever they hold.
WARN_BALANCE_MACHINE_STATE_UNREAD: Final = "balance-machine-state-unread"

#: No production figure was computed - no generator namespace was supplied, or
#: an empty one. Raised on every such balance, because a consumption total with
#: no production beside it is half a graph and must not read as a whole one.
WARN_BALANCE_PRODUCTION_UNMODELED: Final = "balance-production-unmodeled"

#: CS-1059. This many BUILT ACTORS contributed no number to the production
#: capacity. The capacity is a LOWER BOUND whenever it fires.
WARN_BALANCE_GENERATION_UNMODELED: Final = "balance-generation-unmodeled"

#: CS-1059. Standing on every computed production figure: it is a nameplate
#: capacity at the reference clock over built counts, never live output.
WARN_BALANCE_PRODUCTION_NAMEPLATE: Final = "balance-production-nameplate"

#: No belt topology, so a starved machine's upstream cause cannot be named.
#: Raised whenever the network model declares the edge set unavailable.
WARN_BALANCE_UPSTREAM_CAUSE_UNAVAILABLE: Final = "balance-upstream-cause-unavailable"

#: CS-1263. This many machines carried no readable clock and are named gaps in
#: the clocked draw - never priced at the reference clock.
WARN_BALANCE_CLOCK_UNREAD: Final = "balance-clock-unread"

#: CS-1263. This many machines contributed no number to the clocked draw for any
#: reason other than an unread clock. Both clocked ends are floors.
WARN_BALANCE_CLOCKED_DRAW_UNMODELED: Final = "balance-clocked-draw-unmodeled"

#: CS-1263. This many machines run where the power law has no exact rational
#: value, so the clocked draw is an exact bracket and not one number.
WARN_BALANCE_CLOCKED_DRAW_BOUNDED: Final = "balance-clocked-draw-bounded"

#: CS-1263. The machines model carried no machine at all, so the clocked draw is
#: zero because there was nothing to price, not because anything was measured.
WARN_BALANCE_NO_MACHINES_CLOCKED: Final = "balance-no-machines-clocked"

#: CS-1263. This many machines were priced at :data:`ELIDED_CLOCK_DEFAULT`
#: because their clock tag was elided. Counted so the default is never silent.
WARN_BALANCE_CLOCK_ELIDED: Final = "balance-clock-elided"

#: One fixed line per gap kind this module OWNS. The other three kinds carry
#: ``clockspeed/solve/power.py``'s own reason verbatim instead, so no line is
#: written twice anywhere.
_GAP_REASON: Final[Mapping[str, str]] = MappingProxyType(
    {
        GAP_NO_REGISTRY_ENTRY: (
            "the supplied registry carries no entry for this built class, so nothing"
            " declares a draw for it; the class is counted here rather than dropped,"
            " because a built actor nobody modelled is the one this total is most"
            " wrong about"
        ),
        GAP_DRAW_INEXACT: (
            "the entry declares a draw that is not exactly a Fraction, and a float in"
            " the solve path is forbidden outright; the value is refused rather than"
            " converted, because a conversion here would be exact and wrong"
        ),
        GAP_PRODUCTION_VARIABLE: (
            "the generator declares a variable output, so its declared scalar is not"
            " its output and is not summed; the cycle that carries the real output is"
            " not modelled, so the class is named here rather than counted as zero"
        ),
        GAP_PRODUCTION_UNDECLARED: (
            "the generator entry declares no readable scalar output, so nothing"
            " states what it produces; it is named here rather than counted as zero"
        ),
        GAP_PRODUCTION_INEXACT: (
            "the generator declares an output that is not exactly a Fraction, and a"
            " float in the solve path is forbidden outright; the value is refused"
            " rather than converted"
        ),
        GAP_CLOCK_UNREAD: (
            "this machine's clock was never read - the tag was absent or its value was"
            " refused - so it is not priced at all; pricing it at the reference clock"
            " would be a confident one, exactly as wrong as a confident zero"
        ),
        GAP_LAW_INEXACT: (
            "the clock or the declared exponent is not exactly a Fraction, so the power"
            " law cannot be applied without a float and is not applied"
        ),
    }
)

#: Why a machine at the reference clock is exact under any exponent, or none.
_REFERENCE_CLOCK_REASON: Final = (
    "at the reference clock the draw is the declared scalar; one raised to any power is"
    " one, so no exponent is asked for and the draw is exact"
)

#: Why a machine whose clock tag was elided is priced at the default.
_ELIDED_CLOCK_REASON: Final = (
    "the save carried no clock tag on a cleanly read payload, which is how it writes a"
    " machine at the class default, so it is priced at the reference clock, where the"
    " draw is the declared scalar"
)

#: Why a clocked group is exact under a whole exponent away from the reference.
_WHOLE_EXPONENT_REASON: Final = (
    "the declared exponent is a whole number, so the power law is a finite product of"
    " exact factors and the clock-scaled draw is exact"
)

#: Why a zero clock is exact under a positive exponent.
_ZERO_CLOCK_REASON: Final = (
    "a clock of zero raised to a positive exponent is zero, so the clock-scaled draw is"
    " exactly zero"
)

#: Why a zero clock under a non-positive exponent has no draw.
_ZERO_CLOCK_UNDEFINED_REASON: Final = (
    "a clock of zero raised to an exponent that is not positive has no real value, so"
    " the clock-scaled draw is undefined"
)

#: Why a clocked group is a bracket rather than one number.
_BRACKET_REASON: Final = (
    "the declared exponent is not whole, so the power law has no exact rational value at"
    " this clock; the draw is bracketed by the same law at the two whole exponents either"
    " side of the declared one, and both ends are exact"
)

#: One fixed line per warning code raised here. Keyed rather than formatted, so
#: a detail can never be built from something read out of a save - the idiom
#: ``clockspeed/save/world.py`` established for the same reason.
_WARNING_DETAIL: Final[Mapping[str, str]] = MappingProxyType(
    {
        WARN_BALANCE_DRAW_UNMODELED: (
            "this many built actors contributed no number to the world draw because"
            " their class' draw is not modelled; the consumption total is a LOWER"
            " BOUND and never a measurement, and every one of them is named in the"
            " gap list with the kind of gap it is"
        ),
        WARN_BALANCE_NOTHING_BUILT: (
            "the placement model carried no built class at all, so the world draw is"
            " zero because there was nothing to sum; a world with nothing built and a"
            " world whose built actors were all filtered out produce the same number"
        ),
        WARN_BALANCE_PRODUCING_UNAVAILABLE: (
            "no machine in this world carried a readable producing flag, so the empty"
            " starved set means nothing could be measured and never that nothing is"
            " starved"
        ),
        WARN_BALANCE_MACHINE_STATE_UNREAD: (
            "this many machines carried no producing flag, so they were neither"
            " flagged nor counted as running; the starved set is short by whatever"
            " those machines hold"
        ),
        WARN_BALANCE_PRODUCTION_UNMODELED: (
            "no production figure was computed because no generator model was"
            " supplied, so this balance carries consumption alone; a production total"
            " of zero beside a real consumption total would render every world in"
            " permanent brownout"
        ),
        WARN_BALANCE_GENERATION_UNMODELED: (
            "this many built actors contributed no number to the production capacity"
            " - a variable, undeclared or inexact output, or a class no registry entry"
            " carries - so the capacity is a LOWER BOUND, and each is named in the"
            " production gap list by kind"
        ),
        WARN_BALANCE_PRODUCTION_NAMEPLATE: (
            "the production figure is the nameplate capacity of the built generators"
            " at the reference clock; their clocks and fuel state are not modelled, so"
            " it is what they are rated for and never what they produce now"
        ),
        WARN_BALANCE_UPSTREAM_CAUSE_UNAVAILABLE: (
            "the network model declares no belt topology, so a starved machine's"
            " upstream cause cannot be named and the finding is a symptom rather than"
            " a whole audit; no proximity fallback is used, because a nearest"
            " neighbour renders a wrong answer that reads like a right one"
        ),
        WARN_BALANCE_CLOCK_UNREAD: (
            "this many machines carried no readable clock, so they are named gaps in the"
            " clocked draw and were never priced at the reference clock; both clocked"
            " ends are floors"
        ),
        WARN_BALANCE_CLOCKED_DRAW_UNMODELED: (
            "this many machines contributed no number to the clocked draw - no entry, no"
            " modeled draw, no scalable law or no real value at their clock - and each is"
            " named in the gap list by kind; both clocked ends are floors"
        ),
        WARN_BALANCE_CLOCKED_DRAW_BOUNDED: (
            "this many machines run where the power law has no exact rational value, so"
            " the clocked draw is an exact bracket and not one number"
        ),
        WARN_BALANCE_CLOCK_ELIDED: (
            "this many machines carried no clock tag on a cleanly read payload, which is how"
            " the save writes a machine at the class default, so they were priced at the"
            " reference clock; a clock absent for any other reason stays a named gap"
        ),
        WARN_BALANCE_NO_MACHINES_CLOCKED: (
            "the machines model carried no machine at all, so the clocked draw is zero"
            " because there was nothing to price and never because anything was measured"
        ),
    }
)


@dataclass(frozen=True)
class DrawContribution:
    """One built class' contribution to the world draw, with a number behind it.

    ONLY A CLASS WITH A MODELED SCALAR DRAW MAY ENTER THIS BUCKET, so both
    Fractions are always populated and neither is ever None. A class whose draw
    is unmodeled is a :class:`DrawGap` instead - see the module docstring for
    why the two are separate types rather than one type with nullable fields.

    NO INSTANCE NAME, NO INDEX, NO OFFSET, NO PATH. A bare class name is
    publisher content on the terms ``clockspeed/audit/placement.py``
    ``Placement`` states.

    Attributes:
        class_name: The built actor class, as ``WorldPlacement.built_counts``
            keys it.
        built_count: How many of that class are built.
        megawatts_each: The declared draw of ONE, at the reference clock.
        megawatts_total: ``megawatts_each * built_count``, exactly.
    """

    class_name: str
    built_count: int
    megawatts_each: Fraction
    megawatts_total: Fraction


@dataclass(frozen=True)
class DrawGap:
    """One built class that contributed NO NUMBER to the world draw.

    **THERE IS DELIBERATELY NO MEGAWATTS FIELD ON THIS TYPE.** A zero is not
    merely absent here, it is unrepresentable: there is nothing for a consumer
    to read a zero out of and nothing for a later change to default to zero.
    ``tests/audit/test_balance.py::test_a_gap_has_no_megawatts_field_to_read_a_zero_out_of``
    grades that structurally, off the declared fields, because an arm checking
    one instance's value would pass the day the field came back.

    Attributes:
        class_name: The built actor class this gap is about.
        built_count: How many of that class are built. The gap is COUNTABLE in
            actors and not merely in classes, which is the difference between
            "four classes went unmodelled" and "eighteen buildings did".
        kind: One of :data:`GAP_KINDS`. Named rather than reduced to a boolean,
            because the five ways a draw goes missing are five different facts
            and a caller renders them differently.
        reason: One line naming why. Carried verbatim from
            ``clockspeed/solve/power.py`` for the three declaration-side kinds,
            so that module stays the single owner of those words.
    """

    class_name: str
    built_count: int
    kind: str
    reason: str


@dataclass(frozen=True, repr=False)
class WorldDraw:
    """The whole-world power draw, partitioned into what is known and what is not.

    ``repr`` renders counts and flags only, for the reason
    ``clockspeed/audit/inventory.py`` ``WorldInventory`` gives.

    Attributes:
        contributions: One entry per built class with a modeled draw, in sorted
            class-name order so two runs agree.
        gaps: One entry per built class without one, in the same order.
        consumption_megawatts: The exact Fraction sum over
            :attr:`contributions`. A LOWER BOUND whenever :attr:`gaps` is
            non-empty, which :attr:`consumption_complete` is how a consumer
            learns without walking the list.
        consumption_complete: Whether every built class had a number. False
            means the total above is a floor and not a measurement.
        classes_considered: How many built classes were partitioned. Equal to
            ``len(contributions) + len(gaps)`` by construction, and worth asking
            rather than deriving, for the reason ``WorldProperties.total`` gives.
        unmodeled_class_count: ``len(gaps)``.
        unmodeled_contributor_count: The sum of :attr:`DrawGap.built_count` over
            the gaps. THE COUNT THE ITEM FILING NAMES, and deliberately not the
            one above it: they are different numbers and only one of them says
            how much of the factory is missing from the total.
        warnings: Everything flagged, in the ``WorldWarning`` idiom.
        generator_class_count: CS-1059. How many built classes were taken out
            of the partition because the supplied generator namespace carries
            them. ``classes_considered + generator_class_count`` is every built
            class, so none is lost. Zero when no namespace was supplied.
    """

    contributions: tuple[DrawContribution, ...]
    gaps: tuple[DrawGap, ...]
    consumption_megawatts: Fraction
    consumption_complete: bool
    classes_considered: int
    unmodeled_class_count: int
    unmodeled_contributor_count: int
    warnings: tuple[WorldWarning, ...]
    # Appended with a default, so every existing construction stays valid.
    generator_class_count: int = 0

    def __repr__(self) -> str:
        """Render counts and flags, and nothing about any member.

        Returns:
            The safe rendering.
        """
        return (
            f"{type(self).__name__}(contributions={len(self.contributions)}, "
            f"gaps={len(self.gaps)}, "
            f"consumption_complete={self.consumption_complete}, "
            f"generator_class_count={self.generator_class_count}, "
            f"classes_considered={self.classes_considered}, "
            f"unmodeled_class_count={self.unmodeled_class_count}, "
            f"unmodeled_contributor_count={self.unmodeled_contributor_count}, "
            f"warnings={len(self.warnings)})"
        )


@dataclass(frozen=True)
class ProductionContribution:
    """One built generator class with an exact scalar output behind it (CS-1059).

    The production twin of :class:`DrawContribution`, on its terms.

    Attributes:
        class_name: The built generator class.
        built_count: How many of that class are built.
        megawatts_each: The declared output of ONE, at the reference clock.
        megawatts_total: ``megawatts_each * built_count``, exactly.
    """

    class_name: str
    built_count: int
    megawatts_each: Fraction
    megawatts_total: Fraction


@dataclass(frozen=True)
class ProductionGap:
    """One built class that contributed NO NUMBER to the production capacity.

    **THERE IS DELIBERATELY NO MEGAWATTS FIELD ON THIS TYPE**, for the reason
    :class:`DrawGap` gives. ``tests/audit/test_production.py`` grades that off the
    declared fields.

    Attributes:
        class_name: The built class this gap is about.
        built_count: How many of that class are built.
        kind: One of :data:`PRODUCTION_GAP_KINDS`.
        reason: One line naming why.
    """

    class_name: str
    built_count: int
    kind: str
    reason: str


@dataclass(frozen=True, repr=False)
class WorldProduction:
    """The whole-world generation capacity, partitioned into known and not (CS-1059).

    THE BUILT CLASSES PARTITION THREE WAYS AND CONSERVE:
    ``len(contributions) + len(gaps) + non_generator_class_count ==
    classes_considered``, so a class this module dropped cannot be expressed.

    Attributes:
        contributions: One entry per built generator class with an exact
            scalar output, in sorted class-name order.
        gaps: One entry per built class that may generate and has no number,
            in the same order.
        capacity_megawatts: The exact Fraction sum over :attr:`contributions`,
            at the reference clock. A LOWER BOUND whenever :attr:`gaps` is
            non-empty.
        production_complete: Whether no built class is a gap.
        classes_considered: How many built classes were partitioned.
        non_generator_class_count: Built classes the consumer namespace carries
            and the generator namespace does not - known not to generate.
        unmodeled_class_count: ``len(gaps)``.
        unmodeled_contributor_count: The sum of :attr:`ProductionGap.built_count`.
        warnings: Everything flagged, in the ``WorldWarning`` idiom.
    """

    contributions: tuple[ProductionContribution, ...]
    gaps: tuple[ProductionGap, ...]
    capacity_megawatts: Fraction
    production_complete: bool
    classes_considered: int
    non_generator_class_count: int
    unmodeled_class_count: int
    unmodeled_contributor_count: int
    warnings: tuple[WorldWarning, ...]

    def __repr__(self) -> str:
        """Render counts and flags, and nothing about any member.

        Returns:
            The safe rendering.
        """
        return (
            f"{type(self).__name__}(contributions={len(self.contributions)}, "
            f"gaps={len(self.gaps)}, "
            f"production_complete={self.production_complete}, "
            f"classes_considered={self.classes_considered}, "
            f"non_generator_class_count={self.non_generator_class_count}, "
            f"unmodeled_contributor_count={self.unmodeled_contributor_count}, "
            f"warnings={len(self.warnings)})"
        )


@dataclass(frozen=True, repr=False)
class WorldStarvation:
    """Which machines have work to do and are not doing it, and what was unreadable.

    THE FOUR CATEGORIES PARTITION THE POPULATION AND CONSERVE against
    :attr:`machines_considered`, so a machine this module dropped cannot be
    expressed - the same control :class:`WorldDraw` puts on its own two buckets.

    Attributes:
        starved_indices: Positions into ``WorldMachines.machines``, ascending.
            A position and nothing else - see the module docstring.
        running_count: How many machines report producing.
        unconfigured_count: How many are not producing and carry no recipe. NOT
            STARVED: a machine nobody has set a recipe on has no work to be
            short of, and flagging it would bury the finding that matters.
        unknown_state_count: How many carried no producing flag at all. Never
            flagged and never counted as running, because None means this reader
            saw no such tag and never means the game's default.
        machines_considered: How many machines the input population held.
        producing_available: Carried verbatim from
            ``WorldMachines.producing_available``. False over a non-empty
            population means the empty starved set is a fact about this reader.
        warnings: Everything flagged, in the ``WorldWarning`` idiom.
    """

    starved_indices: tuple[int, ...]
    running_count: int
    unconfigured_count: int
    unknown_state_count: int
    machines_considered: int
    producing_available: bool
    warnings: tuple[WorldWarning, ...]

    def __repr__(self) -> str:
        """Render counts and flags, and none that a member could make raise.

        Returns:
            The safe rendering.
        """
        return (
            f"{type(self).__name__}(starved={len(self.starved_indices)}, "
            f"running_count={self.running_count}, "
            f"unconfigured_count={self.unconfigured_count}, "
            f"unknown_state_count={self.unknown_state_count}, "
            f"machines_considered={self.machines_considered}, "
            f"producing_available={self.producing_available}, "
            f"warnings={len(self.warnings)})"
        )


@dataclass(frozen=True, repr=False)
class WorldBalance:
    """Both halves of the power balance over one world, with what is absent named.

    Attributes:
        draw: The consumption half, at the reference clock over built counts.
        clocked_draw: The consumption half with every machine's own clock
            applied (CS-1263) - the figure that compares like with like against
            a solver plan.
        starvation: The inefficiency half.
        production_available: DERIVED - whether :attr:`production` was
            computed, and nothing else (CS-1059). False when no generator
            namespace was supplied, because a zero would be a lie.
        connected_edges_available: Whether a starved machine's upstream segment
            can be named. DERIVED from ``WorldNetwork.belt_topology_available``
            rather than asserted, so it answers True on its own the day belt
            topology lands.
        warnings: Every sub-model's warnings followed by this level's own, so a
            consumer holding this object never has to reach into a sub-model to
            find a flag.
        production: CS-1059. The generation half, or None when none was
            computed. Appended with a default so every existing construction
            stays valid.
    """

    draw: WorldDraw
    clocked_draw: WorldClockedDraw
    starvation: WorldStarvation
    production_available: bool
    connected_edges_available: bool
    warnings: tuple[WorldWarning, ...]
    production: WorldProduction | None = None

    def __repr__(self) -> str:
        """Render counts and flags, and nothing about any member.

        Returns:
            The safe rendering.
        """
        return (
            f"{type(self).__name__}(consumption_complete={self.draw.consumption_complete}, "
            f"starved={len(self.starvation.starved_indices)}, "
            f"production_available={self.production_available}, "
            f"connected_edges_available={self.connected_edges_available}, "
            f"warnings={len(self.warnings)})"
        )


def _warning(code: str, count: int = 1) -> WorldWarning:
    """Build one warning from this module's own fixed detail table.

    Args:
        code: One of this module's ``WARN_*`` constants.
        count: How many occurrences it aggregates.

    Returns:
        The warning.
    """
    return WorldWarning(
        source=SOURCE_BALANCE,
        code=code,
        detail=_WARNING_DETAIL[code],
        count=count,
    )


def _classify(class_name: str, count: int, entry: Building | None) -> DrawContribution | DrawGap:
    """Put one built class in exactly one bucket, and never in neither or both.

    ONE FUNCTION RETURNING ONE OF THE TWO BUCKET TYPES, rather than a predicate
    beside a separate value lookup. A predicate would leave the caller to
    re-derive the number for the classes it admitted, which is the same decision
    taken twice and the classic way two branches drift apart.

    THREE INDEPENDENT REFUSALS, AND THE ORDER IS LOAD-BEARING FOR ONE PAIR. An
    absent entry is decided first because there is nothing to ask otherwise. The
    exactness refusal comes AFTER the declaration is read, so an entry that
    declares no scalar at all is reported as undeclared rather than as inexact -
    None is not a float, and calling it one would name the wrong fault. The
    three declaration shapes are then whatever ``clockspeed/solve/power.py``
    says they are.

    Args:
        class_name: The built actor class.
        count: How many of it are built.
        entry: The registry entry, or None when the registry carries none.

    Returns:
        A contribution when the class has a modeled exact draw, and a gap of the
        kind that names what went missing otherwise.
    """
    if entry is None:
        return DrawGap(
            class_name=class_name,
            built_count=count,
            kind=GAP_NO_REGISTRY_ENTRY,
            reason=_GAP_REASON[GAP_NO_REGISTRY_ENTRY],
        )

    draw = declared_draw(entry)
    if not draw.modeled or draw.megawatts is None:
        return DrawGap(
            class_name=class_name,
            built_count=count,
            kind=draw.shape,
            reason=draw.reason,
        )

    if type(draw.megawatts) is not Fraction:
        return DrawGap(
            class_name=class_name,
            built_count=count,
            kind=GAP_DRAW_INEXACT,
            reason=_GAP_REASON[GAP_DRAW_INEXACT],
        )

    return DrawContribution(
        class_name=class_name,
        built_count=count,
        megawatts_each=draw.megawatts,
        megawatts_total=draw.megawatts * count,
    )


def draw_of(
    placement: WorldPlacement,
    buildings: Mapping[str, Building],
    *,
    generators: Mapping[str, Generator] | None = None,
) -> WorldDraw:
    """Compute the world power draw as the exact sum over the built counts.

    PURE, AND TOTAL. Every input produces a model: an empty world, a registry
    that models nothing, and a registry carrying a float draw all return a valid
    :class:`WorldDraw` carrying the flags and the named gaps that say so.
    Nothing here raises, because a power answer that refuses to render is
    strictly worse than one that reports what it has and names what it lost.

    Args:
        placement: The placement model whose ``built_counts`` this sums over.
            Read only; nothing here reads a save.
        buildings: The registry, keyed by the same bare class name the built
            counts are keyed by. Supplied by the caller - this module never
            builds one and never reads ``clockspeed/data/``.
        generators: CS-1059. The generator namespace, or None. A built class
            it carries is a generator, not a consumer, and is counted in
            :attr:`WorldDraw.generator_class_count` instead of partitioned.

    Returns:
        The draw, partitioned. The consumption total is the exact Fraction sum
        over the modeled contributors alone, and is a LOWER BOUND whenever any
        gap exists.
    """
    contributions: list[DrawContribution] = []
    gaps: list[DrawGap] = []
    total = Fraction(0)
    producers = generators or {}
    excluded = 0

    for class_name in sorted(placement.built_counts):
        if class_name in producers:
            excluded += 1
            continue
        count = placement.built_counts[class_name]
        bucket = _classify(class_name, count, buildings.get(class_name))
        if isinstance(bucket, DrawGap):
            gaps.append(bucket)
            continue
        contributions.append(bucket)
        total += bucket.megawatts_total

    unmodeled_contributors = sum(gap.built_count for gap in gaps)

    warnings: list[WorldWarning] = []
    if not placement.built_counts:
        warnings.append(_warning(WARN_BALANCE_NOTHING_BUILT))
    if unmodeled_contributors:
        warnings.append(_warning(WARN_BALANCE_DRAW_UNMODELED, unmodeled_contributors))

    return WorldDraw(
        contributions=tuple(contributions),
        gaps=tuple(gaps),
        consumption_megawatts=total,
        consumption_complete=not gaps,
        classes_considered=len(placement.built_counts) - excluded,
        unmodeled_class_count=len(gaps),
        unmodeled_contributor_count=unmodeled_contributors,
        warnings=tuple(warnings),
        generator_class_count=excluded,
    )


def _production_bucket(
    class_name: str, count: int, entry: Generator
) -> ProductionContribution | ProductionGap:
    """Put one built generator class in exactly one production bucket.

    The variable test comes FIRST: a variable generator's declared scalar is a
    real Fraction - zero on the measured geothermal entry - and would otherwise
    pass every later check and be summed.

    Args:
        class_name: The built class.
        count: How many of it are built.
        entry: Its generator entry.

    Returns:
        A contribution for an exact scalar output, and a named gap otherwise.
    """
    output = entry.power_production
    if entry.is_variable_production:
        kind = GAP_PRODUCTION_VARIABLE
    elif output is None:
        kind = GAP_PRODUCTION_UNDECLARED
    elif type(output) is not Fraction:
        kind = GAP_PRODUCTION_INEXACT
    else:
        return ProductionContribution(
            class_name=class_name,
            built_count=count,
            megawatts_each=output,
            megawatts_total=output * count,
        )
    return ProductionGap(
        class_name=class_name, built_count=count, kind=kind, reason=_GAP_REASON[kind]
    )


def production_of(
    placement: WorldPlacement,
    generators: Mapping[str, Generator],
    buildings: Mapping[str, Building],
) -> WorldProduction:
    """Compute the world generation capacity as the exact sum over built generators.

    CS-1059. PURE, AND TOTAL, on the terms :func:`draw_of` states.

    Args:
        placement: The placement model whose ``built_counts`` this sums over.
        generators: The generator namespace, keyed by bare class name.
        buildings: The consumer namespace. A built class it carries and the
            generator namespace does not is KNOWN not to generate; a class
            neither carries is a :data:`GAP_NO_REGISTRY_ENTRY` gap.

    Returns:
        The production model, partitioned with conservation. The capacity is
        the nameplate output at the reference clock, and a LOWER BOUND whenever
        any gap exists.
    """
    contributions: list[ProductionContribution] = []
    gaps: list[ProductionGap] = []
    non_generators = 0
    total = Fraction(0)

    for class_name in sorted(placement.built_counts):
        count = placement.built_counts[class_name]
        entry = generators.get(class_name)
        if entry is None:
            if class_name in buildings:
                non_generators += 1
                continue
            gaps.append(
                ProductionGap(
                    class_name=class_name,
                    built_count=count,
                    kind=GAP_NO_REGISTRY_ENTRY,
                    reason=_GAP_REASON[GAP_NO_REGISTRY_ENTRY],
                )
            )
            continue
        bucket = _production_bucket(class_name, count, entry)
        if isinstance(bucket, ProductionGap):
            gaps.append(bucket)
            continue
        contributions.append(bucket)
        total += bucket.megawatts_total

    unmodeled_contributors = sum(gap.built_count for gap in gaps)
    warnings = [_warning(WARN_BALANCE_PRODUCTION_NAMEPLATE)]
    if unmodeled_contributors:
        warnings.append(_warning(WARN_BALANCE_GENERATION_UNMODELED, unmodeled_contributors))

    result = WorldProduction(
        contributions=tuple(contributions),
        gaps=tuple(gaps),
        capacity_megawatts=total,
        production_complete=not gaps,
        classes_considered=len(placement.built_counts),
        non_generator_class_count=non_generators,
        unmodeled_class_count=len(gaps),
        unmodeled_contributor_count=unmodeled_contributors,
        warnings=tuple(warnings),
    )
    audit_exact(result, path="production")
    return result


@dataclass(frozen=True, repr=False)
class ClockedContribution:
    """One built class at one clock, with the clock-scaled draw behind it.

    ONE GROUP PER (CLASS, CLOCK), so every machine in it has the same draw and
    the per-machine ends are meaningful. Both ends are always populated and both
    are exact Fractions: equal when :attr:`bound` is :data:`BOUND_EXACT`, and a
    true bracket around an irrational draw when it is
    :data:`BOUND_EXPONENT_BRACKET`.

    ``repr`` renders the numbers and the bound kind and never the class name:
    the class here is read off ``MachineState.class_name``, which
    ``clockspeed/audit/machines.py`` checks against no closed set.

    Attributes:
        class_name: The machine's built class, as ``MachineState`` carries it.
        clock: The clock every machine in the group runs at, exact.
        clock_elided: Whether that clock is :data:`ELIDED_CLOCK_DEFAULT`
            standing in for an elided tag rather than a value read. Part of the
            group key, so an elided group never merges with a read one.
        machine_count: How many machines run that class at that clock.
        bound: One of :data:`BOUND_KINDS`.
        reason: One line naming why the draw is exact or bracketed.
        lower_each: The low end of one machine's draw.
        upper_each: The high end of one machine's draw.
        lower_total: ``lower_each * machine_count``, exactly.
        upper_total: ``upper_each * machine_count``, exactly.
    """

    class_name: str
    clock: Fraction
    clock_elided: bool
    machine_count: int
    bound: str
    reason: str
    lower_each: Fraction
    upper_each: Fraction
    lower_total: Fraction
    upper_total: Fraction

    def __repr__(self) -> str:
        """Render the numbers and the bound kind, and never the class name.

        Returns:
            The safe rendering.
        """
        return (
            f"{type(self).__name__}(clock={self.clock}, "
            f"clock_elided={self.clock_elided}, "
            f"machine_count={self.machine_count}, bound={self.bound}, "
            f"lower_total={self.lower_total}, upper_total={self.upper_total})"
        )


@dataclass(frozen=True, repr=False)
class ClockedGap:
    """Machines of one class that contributed NO NUMBER to the clocked draw, by kind.

    **NO MEGAWATTS FIELD, AND NO CLOCK FIELD.** The first for the reason
    :class:`DrawGap` gives; the second because a refused clock may be a float,
    and a gap must not carry the value it refused.

    Attributes:
        class_name: The machine's built class, as ``MachineState`` carries it.
        machine_count: How many machines of that class landed here by this kind.
        kind: One of :data:`CLOCKED_GAP_KINDS`.
        reason: One line naming why.
    """

    class_name: str
    machine_count: int
    kind: str
    reason: str

    def __repr__(self) -> str:
        """Render the count and the kind, and never the class name.

        Returns:
            The safe rendering.
        """
        return f"{type(self).__name__}(machine_count={self.machine_count}, kind={self.kind})"


@dataclass(frozen=True, repr=False)
class WorldClockedDraw:
    """The whole-world draw with every machine's clock applied, as an exact bracket.

    THE MACHINES PARTITION INTO GROUPS AND GAPS WITH CONSERVATION:
    ``sum(machine_count)`` over both equals :attr:`machines_considered`.

    Attributes:
        contributions: One group per (class, clock), sorted so two runs agree.
        gaps: One entry per (class, kind), sorted the same way.
        lower_megawatts: The exact sum of every group's low end.
        upper_megawatts: The exact sum of every group's high end. Both are over
            the groups alone, so both are FLOORS of their own kind whenever
            :attr:`gaps` is non-empty.
        exact: Whether the two ends are one number: no group is bracketed and
            no machine is a gap.
        complete: Whether every machine landed in a group.
        machines_considered: How many machines the input population held.
        bounded_machine_count: How many machines sit in a bracketed group.
        unread_clock_count: How many machines are :data:`GAP_CLOCK_UNREAD`.
        elided_clock_count: How many machines were priced at
            :data:`ELIDED_CLOCK_DEFAULT` because their clock tag was elided.
        unmodeled_machine_count: How many machines are any other gap kind.
        warnings: Everything flagged, in the ``WorldWarning`` idiom.
        generator_machine_count: CS-1059. How many machines were taken out of
            the population because the supplied generator namespace carries
            their class. Zero when no namespace was supplied.
    """

    contributions: tuple[ClockedContribution, ...]
    gaps: tuple[ClockedGap, ...]
    lower_megawatts: Fraction
    upper_megawatts: Fraction
    exact: bool
    complete: bool
    machines_considered: int
    bounded_machine_count: int
    unread_clock_count: int
    elided_clock_count: int
    unmodeled_machine_count: int
    warnings: tuple[WorldWarning, ...]
    # Appended with a default, so every existing construction stays valid.
    generator_machine_count: int = 0

    def __repr__(self) -> str:
        """Render counts and flags, and nothing about any member.

        Returns:
            The safe rendering.
        """
        return (
            f"{type(self).__name__}(contributions={len(self.contributions)}, "
            f"gaps={len(self.gaps)}, exact={self.exact}, complete={self.complete}, "
            f"machines_considered={self.machines_considered}, "
            f"bounded_machine_count={self.bounded_machine_count}, "
            f"unread_clock_count={self.unread_clock_count}, "
            f"elided_clock_count={self.elided_clock_count}, "
            f"unmodeled_machine_count={self.unmodeled_machine_count}, "
            f"generator_machine_count={self.generator_machine_count}, "
            f"warnings={len(self.warnings)})"
        )


def _whole_power(base: Fraction, exponent: int) -> Fraction:
    """Raise an exact base to a WHOLE exponent, exactly, without the ``**`` operator.

    Square-and-multiply over the exponent's bits, so the work is logarithmic in
    the exponent. ``Fraction ** Fraction`` returns a float for a non-whole
    exponent (``clockspeed/solve/power.py`` records the measurement), and
    keeping the operator out of this module entirely means no later edit can
    hand one a Fraction exponent by accident.

    Args:
        base: The base. Must be non-zero when the exponent is negative; the one
            caller guarantees it.
        exponent: The whole exponent, of either sign.

    Returns:
        ``base`` raised to ``exponent``, exactly.
    """
    result = Fraction(1)
    factor = base
    remaining = abs(exponent)
    while remaining:
        if remaining & 1:
            result *= factor
        factor *= factor
        remaining >>= 1
    return result if exponent >= 0 else 1 / result


def _bracket(clock: Fraction, exponent: Fraction) -> tuple[Fraction, Fraction]:
    """The exact low and high ends of ``clock ** exponent`` for a positive clock.

    ``clock ** x`` is monotone in ``x`` for every positive clock - falling for a
    clock below one, rising above it - so its value at the declared exponent
    lies between its values at the two whole exponents either side. Those two
    are exact. Which is the low end flips at the reference clock, and taking the
    minimum and maximum rather than assuming an order is what makes the overclock
    case right.

    Args:
        clock: The clock, strictly positive and exact.
        exponent: The declared exponent, exact and not whole.

    Returns:
        The low end and the high end, in that order.
    """
    below = _whole_power(clock, math.floor(exponent))
    above = _whole_power(clock, math.ceil(exponent))
    return min(below, above), max(below, above)


#: One priced machine: ``(bound, reason, clock, lower_each, upper_each)``.
_Priced = tuple[str, str, Fraction, Fraction, Fraction]

#: One machine that is a gap: ``(kind, reason)``.
_Refused = tuple[str, str]


def _refusal(class_name: str, clock: object, entry: Building | None) -> _Refused | None:
    """Name why one machine cannot be priced at its clock, or None when it can.

    THE REGISTRY SIDE IS DECIDED FIRST, by :func:`_classify` - the same
    function :func:`draw_of` uses - so the two draws can never disagree about
    which entries are modeled. Only then is the clock read, and a clock never
    read is a gap: it is not priced at the reference clock, which is the
    confident one this module refuses for the same reason it refuses the
    confident zero.

    Args:
        class_name: The machine's built class.
        clock: The machine's clock as ``MachineState.overclock`` carries it.
        entry: The registry entry, or None when the registry carries none.

    Returns:
        ``(kind, reason)`` for a gap, or None when :func:`_law` may price it.
    """
    bucket = _classify(class_name, 1, entry)
    if isinstance(bucket, DrawGap):
        return bucket.kind, bucket.reason
    if clock is None:
        return GAP_CLOCK_UNREAD, _GAP_REASON[GAP_CLOCK_UNREAD]
    exponent = None if entry is None else entry.power_exponent
    if type(clock) is not Fraction or (exponent is not None and type(exponent) is not Fraction):
        return GAP_LAW_INEXACT, _GAP_REASON[GAP_LAW_INEXACT]
    return None


def _at_zero_clock(exponent: Fraction) -> _Priced | _Refused:
    """Price a machine at a clock of exactly zero.

    Args:
        exponent: The declared exponent, exact.

    Returns:
        An exact zero under a positive exponent, and a named gap otherwise.
    """
    if exponent > 0:
        return BOUND_EXACT, _ZERO_CLOCK_REASON, Fraction(0), Fraction(0), Fraction(0)
    return OUTCOME_UNDEFINED, _ZERO_CLOCK_UNDEFINED_REASON


def _law(entry: Building, clock: Fraction, each: Fraction) -> _Priced | _Refused:
    """Apply the power law to one machine that :func:`_refusal` admitted.

    Args:
        entry: The registry entry, modeled and exact.
        clock: The machine's clock, exact.
        each: The entry's declared draw at the reference clock, exact.

    Returns:
        The exact value or the named bracket, or a gap carrying
        ``clockspeed/solve/power.py``'s own outcome word and reason.
    """
    if clock == REFERENCE_CLOCK:
        # Before the exponent is asked for: one raised to any power is one, so
        # an entry that is not clock-scalable still has an exact draw here.
        return BOUND_EXACT, _REFERENCE_CLOCK_REASON, clock, each, each

    drawn = draw_at_clock(entry, clock)
    exponent = entry.power_exponent
    if drawn.outcome != OUTCOME_DEFERRED or exponent is None:
        return drawn.outcome, drawn.reason
    if clock == 0:
        return _at_zero_clock(exponent)
    if exponent.denominator == 1:
        scaled = each * _whole_power(clock, exponent.numerator)
        return BOUND_EXACT, _WHOLE_EXPONENT_REASON, clock, scaled, scaled
    low, high = _bracket(clock, exponent)
    ends = sorted((each * low, each * high))
    return BOUND_EXPONENT_BRACKET, _BRACKET_REASON, clock, ends[0], ends[1]


def _clocked_outcome(class_name: str, clock: object, entry: Building | None) -> _Priced | _Refused:
    """Price one machine at its own clock, or name why it cannot be priced.

    Args:
        class_name: The machine's built class.
        clock: The machine's clock as ``MachineState.overclock`` carries it.
        entry: The registry entry, or None when the registry carries none.

    Returns:
        ``(bound, reason, clock, lower_each, upper_each)`` for a priced machine, or
        ``(kind, reason)`` for a gap.
    """
    refused = _refusal(class_name, clock, entry)
    # Past a None refusal the entry is present and the clock exact; the two
    # clauses after the first only narrow the types for the checker.
    if refused is not None or entry is None or type(clock) is not Fraction:
        return refused or (GAP_NO_REGISTRY_ENTRY, _GAP_REASON[GAP_NO_REGISTRY_ENTRY])
    each = declared_draw(entry).megawatts
    if type(each) is not Fraction:
        return GAP_DRAW_INEXACT, _GAP_REASON[GAP_DRAW_INEXACT]
    return _law(entry, clock, each)


def clocked_draw_of(
    machines: WorldMachines,
    buildings: Mapping[str, Building],
    *,
    generators: Mapping[str, Generator] | None = None,
) -> WorldClockedDraw:
    """Compute the world power draw with every machine's own clock applied (CS-1263).

    :func:`draw_of` prices BUILT COUNTS at the reference clock and never reads a
    clock; it stays, because a built count is a fact the placement model owns.
    This prices each MACHINE at the clock it actually runs at, which is the
    figure that compares like with like against a solver plan of fractional
    machine equivalents. A world has whole machines, so nothing here reads a
    fractional machine count.

    PURE, AND TOTAL, on the terms :func:`draw_of` states.

    Args:
        machines: The machines model, for each machine's class and clock.
        buildings: The registry, keyed by bare class name.
        generators: CS-1059. The generator namespace, or None. A machine whose
            class it carries is not a consumer and is counted apart.

    Returns:
        The clocked draw: an exact value per group where the power law yields
        one, a named bracket where it does not, and a named gap where no number
        exists at all.
    """
    priced: dict[tuple[str, Fraction, bool], tuple[str, str, Fraction, Fraction, int]] = {}
    gapped: dict[tuple[str, str], tuple[str, int]] = {}
    producers = generators or {}
    excluded = 0

    for state in machines.machines:
        if state.class_name in producers:
            excluded += 1
            continue
        entry = buildings.get(state.class_name)
        elided = state.overclock is None and state.overclock_elided
        read = ELIDED_CLOCK_DEFAULT if elided else state.overclock
        outcome = _clocked_outcome(state.class_name, read, entry)
        if len(outcome) == 2:  # noqa: PLR2004 - the gap shape is a pair
            kind, reason = outcome
            _held, count = gapped.get((state.class_name, kind), (reason, 0))
            gapped[(state.class_name, kind)] = (reason, count + 1)
            continue
        bound, reason, clock, low, high = outcome
        if elided:
            reason = _ELIDED_CLOCK_REASON
        key = (state.class_name, clock, elided)
        prior = priced.get(key, (bound, reason, low, high, 0))
        priced[key] = (bound, reason, low, high, prior[4] + 1)

    contributions = tuple(
        ClockedContribution(
            class_name=class_name,
            clock=clock,
            clock_elided=elided,
            machine_count=count,
            bound=bound,
            reason=reason,
            lower_each=low,
            upper_each=high,
            lower_total=low * count,
            upper_total=high * count,
        )
        for (class_name, clock, elided), (bound, reason, low, high, count) in sorted(priced.items())
    )
    gaps = tuple(
        ClockedGap(class_name=class_name, machine_count=count, kind=kind, reason=reason)
        for (class_name, kind), (reason, count) in sorted(gapped.items())
    )

    bounded = sum(
        group.machine_count for group in contributions if group.bound == BOUND_EXPONENT_BRACKET
    )
    unread = sum(gap.machine_count for gap in gaps if gap.kind == GAP_CLOCK_UNREAD)
    defaulted = sum(group.machine_count for group in contributions if group.clock_elided)
    unmodeled = sum(gap.machine_count for gap in gaps) - unread

    warnings: list[WorldWarning] = []
    if not machines.machines:
        warnings.append(_warning(WARN_BALANCE_NO_MACHINES_CLOCKED))
    if defaulted:
        warnings.append(_warning(WARN_BALANCE_CLOCK_ELIDED, defaulted))
    if unread:
        warnings.append(_warning(WARN_BALANCE_CLOCK_UNREAD, unread))
    if unmodeled:
        warnings.append(_warning(WARN_BALANCE_CLOCKED_DRAW_UNMODELED, unmodeled))
    if bounded:
        warnings.append(_warning(WARN_BALANCE_CLOCKED_DRAW_BOUNDED, bounded))

    result = WorldClockedDraw(
        contributions=contributions,
        gaps=gaps,
        lower_megawatts=sum((group.lower_total for group in contributions), Fraction(0)),
        upper_megawatts=sum((group.upper_total for group in contributions), Fraction(0)),
        exact=not bounded and not gaps,
        complete=not gaps,
        machines_considered=len(machines.machines) - excluded,
        bounded_machine_count=bounded,
        unread_clock_count=unread,
        elided_clock_count=defaulted,
        unmodeled_machine_count=unmodeled,
        warnings=tuple(warnings),
        generator_machine_count=excluded,
    )
    audit_exact(result, path="clocked_draw")
    return result


def starvation_of(machines: WorldMachines) -> WorldStarvation:
    """Flag every machine that carries a recipe and is not producing.

    PURE, AND TOTAL, on the same terms :func:`draw_of` states.

    Args:
        machines: The machines model. Read only.

    Returns:
        The starvation model, whose four categories partition the population.
    """
    starved: list[int] = []
    running = 0
    unconfigured = 0
    unknown = 0

    for index, state in enumerate(machines.machines):
        if state.producing is None:
            unknown += 1
        elif state.producing:
            running += 1
        elif state.recipe_class_name is None:
            unconfigured += 1
        else:
            starved.append(index)

    warnings: list[WorldWarning] = []
    if machines.machines and not machines.producing_available:
        warnings.append(_warning(WARN_BALANCE_PRODUCING_UNAVAILABLE))
    if unknown:
        warnings.append(_warning(WARN_BALANCE_MACHINE_STATE_UNREAD, unknown))

    return WorldStarvation(
        starved_indices=tuple(starved),
        running_count=running,
        unconfigured_count=unconfigured,
        unknown_state_count=unknown,
        machines_considered=len(machines.machines),
        producing_available=machines.producing_available,
        warnings=tuple(warnings),
    )


def balance_of(
    placement: WorldPlacement,
    buildings: Mapping[str, Building],
    machines: WorldMachines,
    network: WorldNetwork,
    *,
    generators: Mapping[str, Generator] | None = None,
) -> WorldBalance:
    """Compute both halves of one world's power balance.

    Args:
        placement: The placement model, for the built counts.
        buildings: The registry, keyed by bare class name.
        machines: The machines model, for the producing flag and the clocks.
        network: The network model, for whether an upstream cause can be named.
        generators: CS-1059. The generator namespace, or None. Production is
            computed only over a non-empty one.

    Returns:
        The balance, carrying every sub-model's warnings plus this level's own.
    """
    producers = generators or None
    draw = draw_of(placement, buildings, generators=producers)
    clocked_draw = clocked_draw_of(machines, buildings, generators=producers)
    starvation = starvation_of(machines)
    production = None if producers is None else production_of(placement, producers, buildings)

    warnings = [*draw.warnings, *clocked_draw.warnings, *starvation.warnings]
    if production is None:
        warnings.append(_warning(WARN_BALANCE_PRODUCTION_UNMODELED))
    else:
        warnings.extend(production.warnings)
    if not network.belt_topology_available:
        warnings.append(_warning(WARN_BALANCE_UPSTREAM_CAUSE_UNAVAILABLE))

    return WorldBalance(
        draw=draw,
        clocked_draw=clocked_draw,
        starvation=starvation,
        production_available=production is not None,
        connected_edges_available=network.belt_topology_available,
        warnings=tuple(warnings),
        production=production,
    )
