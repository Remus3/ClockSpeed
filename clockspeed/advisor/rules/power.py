"""CS-500: the D4 power and fuel rule family, over the audit power balance.

WHAT THIS MODULE OWNS (BOOTSTRAP.md section 5.3, D4). Two rules and the
adapter that feeds them:

- :data:`HEADROOM_RULE` (``power.headroom``) compares the CLOCK-CORRECT draw
  against generation and, when the draw can exceed it, recommends adding
  generation with the shortfall named exactly - one figure when the clocked
  draw is exact, the exact bracket when the clock law brackets it, and "up to"
  the upper shortfall when generation sits inside the bracket (brownout risk).
- :data:`GAP_RULE` (``power.draw_incomplete``) names an incomplete clocked
  draw - machines whose clock was never read or whose draw is unmodeled - and
  says the total is a floor. The headroom rule REFUSES to advise on such a
  draw: a floor compared against generation would report spare headroom that
  may not exist, which is the confident zero ``clockspeed/audit/balance.py``
  is built against, one comparison later.

INDETERMINATE IS NOT A VERDICT (CS-1271). Every comparison the headroom rule
skips because an input is a floor or absent - an incomplete draw, no
generation figure, an incomplete generation figure - is recorded through
``RuleContext.indeterminate``, never ``reject``. Its step kind sits outside
``clockspeed/advisor/advise.py::SETTLED_STEP_KINDS``, so such a run does not
settle the rule and the ledger never completes an earlier headroom card on
it. Only a comparison made over complete inputs is a ``reject``.

WHICH DRAW. The headroom rule reads ``WorldBalance.clocked_draw`` - every
machine priced at its own clock (CS-1263) - and never
``WorldBalance.draw.consumption_megawatts``, which prices built counts at the
reference clock and so ignores every overclock and underclock in the world.
:func:`balance_inputs` does not even offer the clock-blind figure, so no rule
here can read it by mistake.

GENERATION IS THE AUDIT'S NAMEPLATE CAPACITY (CS-1059, CS-1271). When the
balance carries a production model, :func:`balance_inputs` offers its exact
``capacity_megawatts`` under :data:`IN_GENERATION` and its
``production_complete`` flag under :data:`IN_PRODUCTION_COMPLETE`; with no
model it offers neither, and ``production_available`` is False. The headroom
rule reads ``production_available`` first and, when it is False, records the
comparison as indeterminate and recommends nothing. It then reads the
completeness flag: a capacity with a built generator the registry gives no
output for is a LOWER BOUND, and a floor compared against the draw would
overstate any shortfall, so an incomplete figure is likewise indeterminate
and nothing is recommended.

AN ELIDED CLOCK IS NAMED, NEVER HIDDEN. A machine whose save omits its clock
tag is priced at ``ELIDED_CLOCK_DEFAULT`` by ``clockspeed/audit/balance.py`` and
so lands in the priced population, not in a gap. Both rules read
:data:`IN_ELIDED` on every firing path, so tier 3 always carries it as a read
step, and when it is above zero the one-line reason says the figure assumes
the default clock for that many machines.

WHAT "COMPLETE" COVERS, AND WHERE THE CROSS-CHECK LIVES (CS-1266).
``WorldClockedDraw.complete`` means every machine the audit CONSIDERED has a
priced draw AND every built power consumer was considered. The cross-check is
the audit's, like for like - ``clockspeed/audit/balance.py`` counts built power
consumers and considered ones over one predicate and names each omission - so
no rule here compares two populations itself. ``WorldBalance.draw``'s built
counts are still never compared: they cover the placement allowlist, a
different population. The gap rule reads :data:`IN_OMITTED` and counts every
omitted consumer as unpriced, so a draw incomplete by omission alone never
tells the operator to resolve nothing.

A TAGLESS CONSUMER IS CONSIDERED, NOT OMITTED (CS-1280). A built power
consumer that carried no machine tag on a cleanly read payload is priced by
``clockspeed/audit/balance.py`` at its class default, in a group of its own,
and counted in ``WorldClockedDraw.machines_considered`` - so
:data:`IN_CONSIDERED` holds it, :data:`IN_UNMODELED` holds it when its entry
has no number, and the gap rule's priced share stays a share of one
population with no rule-side change. Its own count,
``WorldClockedDraw.tagless_default_count``, is named by the audit's own
``WARN_BALANCE_TAGLESS_DEFAULT`` and is NOT offered here as a rule input, so
neither card's reason names it the way :data:`IN_ELIDED` names an elided
clock.

UNLOCKS. Neither rule declares an unlock key. "Add generation" names no
building and no recipe, and the first generator is available before any
schematic is bought, so any key declared here would be invented rather than
read from data - and an invented requirement would silence true advice. A
later rule that picks a generator class from data names that recipe in
``Recommendation.requires``, where the engine checks it against
:func:`clockspeed.advisor.trace.unlock_keys`.

NO WORLD TOKEN, NO PATH, NO FLOAT. Every source string names the audit field
the value came from. Every number is an exact ``Fraction`` or an ``int`` count;
text renders a Fraction through :func:`clockspeed.advisor.cards.render_value`,
which carries the exact ratio whenever display rounding lost information.
"""

from __future__ import annotations

from fractions import Fraction
from typing import TYPE_CHECKING, Final

from clockspeed.advisor.cards import render_value
from clockspeed.advisor.trace import InputValue, Recommendation, RuleContext, RuleSpec

if TYPE_CHECKING:
    from clockspeed.audit.balance import WorldBalance

#: The advice domain every rule here belongs to.
DOMAIN: Final = "power"

#: Input names. Each is offered by :func:`balance_inputs`;
#: :data:`IN_GENERATION` and :data:`IN_PRODUCTION_COMPLETE` only when the
#: balance carries a production model (CS-1271).
IN_COMPLETE: Final = "power.clocked_draw.complete"
IN_EXACT: Final = "power.clocked_draw.exact"
IN_LOWER: Final = "power.clocked_draw.lower_mw"
IN_UPPER: Final = "power.clocked_draw.upper_mw"
IN_CONSIDERED: Final = "power.clocked_draw.machines_considered"
IN_UNREAD: Final = "power.clocked_draw.unread_clock_count"
IN_UNMODELED: Final = "power.clocked_draw.unmodeled_machine_count"
IN_PRODUCTION_AVAILABLE: Final = "power.production_available"
IN_PRODUCTION_COMPLETE: Final = "power.production_complete"
IN_GENERATION: Final = "power.generation_mw"
IN_ELIDED: Final = "power.clocked_draw.elided_clock_count"
IN_OMITTED: Final = "power.clocked_draw.omitted_consumer_count"

_SOURCE_PREFIX: Final = "audit.balance."

#: Stable subject keys. They feed the card id, so they encode nothing volatile.
SUBJECT_HEADROOM: Final = "power:generation-headroom"
SUBJECT_GAP: Final = "power:clocked-draw-gaps"


def balance_inputs(balance: WorldBalance) -> dict[str, InputValue]:
    """Offer one world's power balance as rule inputs, each sourced to its audit field.

    Only the clock-correct draw is offered. The generation figure and its
    completeness are offered only when the balance carries a production model
    (see the module docstring). The caller wraps the
    result in a :class:`clockspeed.advisor.trace.WorldInputs` with its unlock
    set; a fresh dict is returned so a caller may add inputs from another layer.
    """
    clocked = balance.clocked_draw
    fields: tuple[tuple[str, str, object], ...] = (
        (IN_COMPLETE, "clocked_draw.complete", clocked.complete),
        (IN_EXACT, "clocked_draw.exact", clocked.exact),
        (IN_LOWER, "clocked_draw.lower_megawatts", clocked.lower_megawatts),
        (IN_UPPER, "clocked_draw.upper_megawatts", clocked.upper_megawatts),
        (IN_CONSIDERED, "clocked_draw.machines_considered", clocked.machines_considered),
        (IN_UNREAD, "clocked_draw.unread_clock_count", clocked.unread_clock_count),
        (IN_UNMODELED, "clocked_draw.unmodeled_machine_count", clocked.unmodeled_machine_count),
        (IN_ELIDED, "clocked_draw.elided_clock_count", clocked.elided_clock_count),
        (IN_OMITTED, "clocked_draw.omitted_consumer_count", clocked.omitted_consumer_count),
        (IN_PRODUCTION_AVAILABLE, "production_available", balance.production_available),
    )
    production = balance.production
    if production is not None:
        fields = (
            *fields,
            (
                IN_PRODUCTION_COMPLETE,
                "production.production_complete",
                production.production_complete,
            ),
            (IN_GENERATION, "production.capacity_megawatts", production.capacity_megawatts),
        )
    return {name: InputValue(value, _SOURCE_PREFIX + field) for name, field, value in fields}


def _read_flag(ctx: RuleContext, name: str) -> bool:
    """Read a declared boolean input; anything but exactly a bool is a rule error."""
    value = ctx.read(name)
    if type(value) is not bool:
        raise TypeError("a power flag input is not a bool")
    return value


def _read_count(ctx: RuleContext, name: str) -> int:
    """Read a declared count input; anything but exactly a non-negative int is a rule error."""
    value = ctx.read(name)
    if type(value) is not int or value < 0:
        raise TypeError("a power count input is not a non-negative int")
    return value


def _mw(value: Fraction) -> str:
    return render_value(value)


def _elision(elided: int) -> str:
    """The reason suffix naming machines priced at the default clock, or nothing."""
    if elided == 0:
        return ""
    machines = "machine" if elided == 1 else "machines"
    return f"; it assumes the default clock for {elided} {machines} whose save omits the clock tag"


def _generation_is_a_measurement(ctx: RuleContext) -> bool:
    """Whether a generation figure exists and counts every built generator.

    Records the comparison as indeterminate when it does not: no figure at
    all, or a capacity with an unmodelled generator, which is a floor
    (CS-1271).
    """
    if not _read_flag(ctx, IN_PRODUCTION_AVAILABLE):
        ctx.indeterminate(
            "compare the draw against generation",
            "generated power is not modelled, so there is no generation figure (CS-1059)",
        )
        return False
    if not _read_flag(ctx, IN_PRODUCTION_COMPLETE):
        ctx.indeterminate(
            "compare the draw against generation",
            "some built generators have no modelled output, so the capacity is a floor"
            " and not a measurement",
        )
        return False
    return True


def _evaluate_headroom(ctx: RuleContext) -> Recommendation | None:
    """Recommend generation when the clocked draw can exceed it."""
    if not _read_flag(ctx, IN_COMPLETE):
        ctx.indeterminate(
            "compare the draw against generation",
            "the clocked draw is incomplete, so its total is a floor and not a measurement",
        )
        return None
    if not _generation_is_a_measurement(ctx):
        return None
    lower = ctx.read_exact(IN_LOWER)
    upper = ctx.read_exact(IN_UPPER)
    exact = _read_flag(ctx, IN_EXACT)
    elided = _elision(_read_count(ctx, IN_ELIDED))
    generation = ctx.read_exact(IN_GENERATION)
    short_lower = ctx.compute("shortfall at the lower draw bound in MW", lower - generation)
    short_upper = ctx.compute("shortfall at the upper draw bound in MW", upper - generation)
    if short_upper <= 0:
        ctx.reject("add generation", "generation covers the upper bound of the clocked draw")
        return None
    if short_lower <= 0:
        ctx.reject(
            "hold generation as built",
            "the upper bound of the clocked draw exceeds generation",
        )
        return Recommendation(
            subject_key=SUBJECT_HEADROOM,
            action=f"Add up to {_mw(short_upper)} MW of generation",
            reason=(
                f"Generation of {_mw(generation)} MW sits inside the clocked draw of "
                f"{_mw(lower)} to {_mw(upper)} MW, a brownout risk{elided}"
            ),
        )
    ctx.reject(
        "hold generation as built",
        "the draw exceeds generation at both ends of the clock bracket",
    )
    if exact and lower == upper:
        return Recommendation(
            subject_key=SUBJECT_HEADROOM,
            action=f"Add {_mw(short_upper)} MW of generation",
            reason=(
                f"Clocked draw of {_mw(upper)} MW exceeds "
                f"{_mw(generation)} MW of generation{elided}"
            ),
        )
    ctx.reject(
        "quote one shortfall figure",
        "the clock law brackets the draw, so the shortfall is a range",
    )
    return Recommendation(
        subject_key=SUBJECT_HEADROOM,
        action=f"Add between {_mw(short_lower)} and {_mw(short_upper)} MW of generation",
        reason=(
            f"Clocked draw of {_mw(lower)} to {_mw(upper)} MW exceeds "
            f"{_mw(generation)} MW of generation{elided}"
        ),
    )


def _plural(count: int, singular: str, plural: str) -> str:
    return f"{count} {singular if count == 1 else plural}"


def _omission(omitted: int) -> str:
    """The reason suffix naming built consumers the draw never considered, or nothing."""
    if omitted == 0:
        return ""
    consumers = _plural(omitted, "built power consumer was", "built power consumers were")
    return f"; {consumers} never considered"


def _evaluate_gap(ctx: RuleContext) -> Recommendation | None:
    """Name an incomplete clocked draw and say its total is a floor."""
    if _read_flag(ctx, IN_COMPLETE):
        ctx.reject("name unpriced machines", "every machine the audit considered has a priced draw")
        return None
    considered = _read_count(ctx, IN_CONSIDERED)
    unread = _read_count(ctx, IN_UNREAD)
    unmodeled = _read_count(ctx, IN_UNMODELED)
    omitted = _read_count(ctx, IN_OMITTED)
    elided = _elision(_read_count(ctx, IN_ELIDED))
    lower = ctx.read_exact(IN_LOWER)
    upper = ctx.read_exact(IN_UPPER)
    # CS-1266. An omitted consumer is unpriced, and it sits outside the
    # considered population, so it joins the share's denominator too.
    unpriced = unread + unmodeled + omitted
    population = considered + omitted
    ctx.compute("unpriced machines", Fraction(unpriced))
    if population > 0:
        ctx.compute("priced share of machines", Fraction(population - unpriced, population))
    ctx.reject(
        "advise on the draw total as a measurement",
        "unpriced machines draw power the total does not count, so it is a floor",
    )
    return Recommendation(
        subject_key=SUBJECT_GAP,
        action=(
            f"Resolve {_plural(unpriced, 'unpriced machine', 'unpriced machines')} "
            "before planning power"
        ),
        reason=(
            f"The clocked draw is a floor of {_mw(lower)} to {_mw(upper)} MW: "
            f"{_plural(unread, 'clock', 'clocks')} unread and "
            f"{_plural(unmodeled, 'machine', 'machines')} unmodeled, of {considered}"
            f"{_omission(omitted)}{elided}"
        ),
    )


HEADROOM_RULE: Final = RuleSpec(
    rule_id="power.headroom",
    domain=DOMAIN,
    inputs=(
        IN_COMPLETE,
        IN_PRODUCTION_AVAILABLE,
        IN_PRODUCTION_COMPLETE,
        IN_LOWER,
        IN_UPPER,
        IN_EXACT,
        IN_ELIDED,
        IN_GENERATION,
    ),
    unlocks=(),
    evaluate=_evaluate_headroom,
)

GAP_RULE: Final = RuleSpec(
    rule_id="power.draw_incomplete",
    domain=DOMAIN,
    inputs=(
        IN_COMPLETE,
        IN_CONSIDERED,
        IN_UNREAD,
        IN_UNMODELED,
        IN_OMITTED,
        IN_ELIDED,
        IN_LOWER,
        IN_UPPER,
    ),
    unlocks=(),
    evaluate=_evaluate_gap,
)

#: Every rule this family registers, in rule-id order.
RULES: Final = (GAP_RULE, HEADROOM_RULE)
