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

WHICH DRAW. The headroom rule reads ``WorldBalance.clocked_draw`` - every
machine priced at its own clock (CS-1263) - and never
``WorldBalance.draw.consumption_megawatts``, which prices built counts at the
reference clock and so ignores every overclock and underclock in the world.
:func:`balance_inputs` does not even offer the clock-blind figure, so no rule
here can read it by mistake.

GENERATION IS NOT MODELLED AT HEAD (CS-1059). ``WorldBalance`` publishes
``production_available`` False and no production figure, so
:func:`balance_inputs` offers the flag and never a generation number. The
headroom rule reads the flag first and, when it is False, records the
comparison as a rejected alternative and recommends nothing. The day a
production figure lands, the adapter offers it under :data:`IN_GENERATION` and
the rule starts firing without an edit.

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

#: Input names. Each is offered by :func:`balance_inputs` except
#: :data:`IN_GENERATION`, which no audit model publishes yet (CS-1059).
IN_COMPLETE: Final = "power.clocked_draw.complete"
IN_EXACT: Final = "power.clocked_draw.exact"
IN_LOWER: Final = "power.clocked_draw.lower_mw"
IN_UPPER: Final = "power.clocked_draw.upper_mw"
IN_CONSIDERED: Final = "power.clocked_draw.machines_considered"
IN_UNREAD: Final = "power.clocked_draw.unread_clock_count"
IN_UNMODELED: Final = "power.clocked_draw.unmodeled_machine_count"
IN_PRODUCTION_AVAILABLE: Final = "power.production_available"
IN_GENERATION: Final = "power.generation_mw"

_SOURCE_PREFIX: Final = "audit.balance."

#: Stable subject keys. They feed the card id, so they encode nothing volatile.
SUBJECT_HEADROOM: Final = "power:generation-headroom"
SUBJECT_GAP: Final = "power:clocked-draw-gaps"


def balance_inputs(balance: WorldBalance) -> dict[str, InputValue]:
    """Offer one world's power balance as rule inputs, each sourced to its audit field.

    Only the clock-correct draw is offered. A generation figure is not, because
    the balance carries none (see the module docstring). The caller wraps the
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
        (IN_PRODUCTION_AVAILABLE, "production_available", balance.production_available),
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


def _evaluate_headroom(ctx: RuleContext) -> Recommendation | None:
    """Recommend generation when the clocked draw can exceed it."""
    if not _read_flag(ctx, IN_COMPLETE):
        ctx.reject(
            "compare the draw against generation",
            "the clocked draw is incomplete, so its total is a floor and not a measurement",
        )
        return None
    if not _read_flag(ctx, IN_PRODUCTION_AVAILABLE):
        ctx.reject(
            "compare the draw against generation",
            "generated power is not modelled, so there is no generation figure (CS-1059)",
        )
        return None
    lower = ctx.read_exact(IN_LOWER)
    upper = ctx.read_exact(IN_UPPER)
    exact = _read_flag(ctx, IN_EXACT)
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
                f"{_mw(lower)} to {_mw(upper)} MW, a brownout risk"
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
            reason=f"Clocked draw of {_mw(upper)} MW exceeds {_mw(generation)} MW of generation",
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
            f"{_mw(generation)} MW of generation"
        ),
    )


def _plural(count: int, singular: str, plural: str) -> str:
    return f"{count} {singular if count == 1 else plural}"


def _evaluate_gap(ctx: RuleContext) -> Recommendation | None:
    """Name an incomplete clocked draw and say its total is a floor."""
    if _read_flag(ctx, IN_COMPLETE):
        ctx.reject("name unpriced machines", "every machine's draw is priced")
        return None
    considered = _read_count(ctx, IN_CONSIDERED)
    unread = _read_count(ctx, IN_UNREAD)
    unmodeled = _read_count(ctx, IN_UNMODELED)
    lower = ctx.read_exact(IN_LOWER)
    upper = ctx.read_exact(IN_UPPER)
    unpriced = unread + unmodeled
    ctx.compute("unpriced machines", Fraction(unpriced))
    if considered > 0:
        ctx.compute("priced share of machines", Fraction(considered - unpriced, considered))
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
        ),
    )


HEADROOM_RULE: Final = RuleSpec(
    rule_id="power.headroom",
    domain=DOMAIN,
    inputs=(IN_COMPLETE, IN_PRODUCTION_AVAILABLE, IN_LOWER, IN_UPPER, IN_EXACT, IN_GENERATION),
    unlocks=(),
    evaluate=_evaluate_headroom,
)

GAP_RULE: Final = RuleSpec(
    rule_id="power.draw_incomplete",
    domain=DOMAIN,
    inputs=(IN_COMPLETE, IN_CONSIDERED, IN_UNREAD, IN_UNMODELED, IN_LOWER, IN_UPPER),
    unlocks=(),
    evaluate=_evaluate_gap,
)

#: Every rule this family registers, in rule-id order.
RULES: Final = (GAP_RULE, HEADROOM_RULE)
