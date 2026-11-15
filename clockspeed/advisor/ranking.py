"""CS-1246: quick-win card ordering with an aging guard read from deferral counts.

WHAT THIS MODULE OWNS. The order a surface shows resolved cards in. It sits
ABOVE :mod:`clockspeed.advisor.advise` and changes nothing there: an
:class:`~clockspeed.advisor.advise.AdvisedCard` goes in, the same objects come
out in a different order. The EXISTING identity order of
:func:`clockspeed.advisor.cards.cards_for` - rule id, then card id - is
untouched and is this module's final tie-break.

THE SEAM. Aging is the per-world ledger's shown-and-deferred record, never a
timer, and this module never meets the ledger: :func:`order_cards` takes the
counts as a plain ``Mapping[str, int]`` keyed by card id, and a card the
mapping does not name has been deferred zero times. It imports no store, opens
no file and reads no clock, so the order is a pure function of its arguments
and every case is a golden case.

THE ORDER. The base order is EFFORT, cheapest first - the quick wins lead -
and then IDENTITY, ``(rule_id, card_id)``, the order :func:`cards_for` already
gives. On top of it the aging guard moves EXACTLY ONE card to the front: the
most starved card whose deferral count has reached the threshold
(:data:`AGING_EVALUATIONS`, overridable per call). Everything else keeps the
base order.

WHY ONE CARD AND NOT A BAND, because a band was built first and measured
wrong. Lifting every aged card above every unaged one fails twice: in steady
state nearly every card has been passed over, so the list inverts to
large-first and the quick-win order it exists to protect is gone; and inside
the band the cheapest-effort order is reproduced, so the large card the guard
was built for is starved inside the band as well. One promotion is a rotation
rather than an inversion - the starved card gets the top spot, and the ledger
clears its count because it has had its turn, so the next run promotes the next
most starved card instead of the same one for ever.

MOST STARVED means the highest deferral count, and among equal counts the card
the base order placed LOWEST - that is the one the quick-win preference has
been pushing down. Only a VISIBLE card is promoted: a hidden card is not being
shown at all, so the order is not what is starving it.

ONE EVALUATION is one advice run in which the card was shown BELOW the top card
and the player passed it over. A run at the top is a turn taken, not a
deferral, and clears the count. How that is counted is the ledger's business,
not this module's - :meth:`clockspeed.advisor.ledger.Ledger.reconcile` measures
it against the order it was handed.

THE EFFORT SCALE (:class:`EffortClass`) is three classes, coarse on purpose. A
precise effort figure would need construction costs priced from the game data,
and no layer here prices one. Widening the scale is a decision that needs an
ADR, not a tweak: three is the number CLAUDE.md section 7 settles for the
explain tiers and this project refuses scale creep.

THE EFFORT TABLE (:data:`EFFORT_BY_RULE`) is keyed by rule id, one entry per
registered rule: the rule that proposes an action is the authority on how big
that action is. An unlisted rule is NOT given a default entry. It is a declared
gap, and :func:`undeclared_rule_ids` is the census seam a test asserts empty
over the registry, so a rule family that lands without an effort class
reddens. At ordering time, though, a rule id the table does not name - a
synthetic rule in someone else's fixture - ranks as the MIDDLE class
(:func:`effort_of`), because refusing to order would make the advisor fail over
a world rather than advise about it (CLAUDE.md non-negotiable 7).

DETERMINISM. The sort is stable and its key holds only ints and strings from
the arguments. No set is iterated, ``hash()`` is never used and no clock is
read, so one ledger state gives one order. That order is independent of the
input sequence as far as the key separates the cards: two cards sharing a rule
id AND a card id are the same advice twice, and a stable sort then keeps them in
the order they arrived, which is the only sequence dependence left.

REFUSALS name the FIELD and never a value: a threshold that is not an ``int``
of at least 1, a counts argument that is not a mapping, and a count that is not
an ``int`` of at least 0. ``bool`` is not an ``int`` here.

PRIVACY. No world token, tier text or input value enters a message.

ZERO LANGUAGE MODEL, NO FILE I/O. The order is arithmetic over a declared
table.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from enum import IntEnum
from types import MappingProxyType
from typing import TYPE_CHECKING, Final

from clockspeed.advisor.rules import registered_rules

if TYPE_CHECKING:
    from clockspeed.advisor.advise import AdvisedCard
    from clockspeed.advisor.trace import RuleSpec

#: Deferrals at which a card counts as aged by default. One deferral is one
#: advice run in which the card was shown and the player passed it over.
AGING_EVALUATIONS: Final = 3


class EffortClass(IntEnum):
    """How big the action a rule proposes is - three classes, cheapest first.

    Coarse on purpose (see the module docstring). Widening it is a decision,
    not a tweak.

    Attributes:
        QUICK: The player finishes it in one visit - read or resolve something.
        MIDDLE: More than a visit, short of a build-out. Also the class an
            unlisted rule id ranks as.
        LARGE: A build-out: new generation, or adopting a whole plan.
    """

    QUICK = 1
    MIDDLE = 2
    LARGE = 3


#: The declared effort of every registered rule, keyed by rule id.
EFFORT_BY_RULE: Final[Mapping[str, EffortClass]] = MappingProxyType(
    {
        # Asks for a whole route: locked recipes, extractors and a production chain.
        "plan.adopt": EffortClass.LARGE,
        # Asks the player to plan toward a redesigned route, a build-out of the same size.
        "plan.redesign": EffortClass.LARGE,
        # Asks the player to go resolve unpriced machines before planning: data, one visit.
        "power.draw_incomplete": EffortClass.QUICK,
        # Asks the player to state or plan a fuel burn with no supply verdict: no construction.
        "power.fuel_demand": EffortClass.QUICK,
        # Asks for more fuel per minute: more than a visit, short of new generation.
        "power.fuel_supply": EffortClass.MIDDLE,
        # Asks for megawatts of new generation: a build-out.
        "power.headroom": EffortClass.LARGE,
    }
)


def effort_of(rule_id: str) -> EffortClass:
    """Return the declared effort class of a rule.

    Args:
        rule_id: The rule id of the card being ranked.

    Returns:
        The class :data:`EFFORT_BY_RULE` declares, or :attr:`EffortClass.MIDDLE`
        for an id it does not name - ordering stays total rather than failing.
        The gap itself is caught by :func:`undeclared_rule_ids`.
    """
    return EFFORT_BY_RULE.get(rule_id, EffortClass.MIDDLE)


def undeclared_rule_ids(rules: Iterable[RuleSpec] | None = None) -> frozenset[str]:
    """Return the rule ids that have no declared effort - the census seam.

    An unlisted rule is NOT given a default: it is a gap this function reports,
    for a test to assert empty over the registry.

    Args:
        rules: The rules to check. Defaults to :func:`registered_rules`.

    Returns:
        The rule ids absent from :data:`EFFORT_BY_RULE`; empty when every rule
        is covered.
    """
    specs = registered_rules() if rules is None else rules
    return frozenset(spec.rule_id for spec in specs if spec.rule_id not in EFFORT_BY_RULE)


def _check_threshold(aging_evaluations: int) -> None:
    if type(aging_evaluations) is not int:
        raise TypeError("the aging threshold must be an int")
    if aging_evaluations < 1:
        raise ValueError("the aging threshold must be at least 1")


def _check_counts(deferrals: Mapping[str, int]) -> None:
    if not isinstance(deferrals, Mapping):
        raise TypeError("the deferral counts must be a mapping")
    for count in deferrals.values():
        if type(count) is not int:
            raise TypeError("a deferral count must be an int")
        if count < 0:
            raise ValueError("a deferral count must be at least 0")


def _base_key(item: AdvisedCard) -> tuple[int, str, str]:
    """The order with no aging in it: cheapest effort, then identity."""
    card = item.card
    return (int(effort_of(card.rule_id)), card.rule_id, card.id)


def _most_starved(
    ordered: list[AdvisedCard],
    deferrals: Mapping[str, int],
    aging_evaluations: int,
) -> int | None:
    """The index in ``ordered`` of the one card the guard promotes, or None.

    The highest deferral count at or above the threshold wins; among equal
    counts the LATER index wins, because the base order placed that card lower
    and it is the one being pushed down. A hidden card is never promoted: it is
    not shown, so the order is not starving it.
    """
    best: tuple[int, int] | None = None
    for index, item in enumerate(ordered):
        if not item.visible:
            continue
        count = deferrals.get(item.card.id, 0)
        if count < aging_evaluations:
            continue
        candidate = (count, index)
        if best is None or candidate > best:
            best = candidate
    return None if best is None else best[1]


def order_cards(
    advised: Iterable[AdvisedCard],
    deferrals: Mapping[str, int],
    *,
    aging_evaluations: int = AGING_EVALUATIONS,
) -> tuple[AdvisedCard, ...]:
    """Order cards: cheapest effort, then identity, with one starved card promoted.

    Pure: the result depends on the arguments alone. The base sort is stable,
    so cards whose whole base key ties keep the order they came in.

    Args:
        advised: The cards to order, in any sequence.
        deferrals: How many times each card was shown below the top card and
            passed over, keyed by card id. An id the mapping does not name
            counts as zero.
        aging_evaluations: The count at which a card counts as starved.
            Defaults to :data:`AGING_EVALUATIONS`.

    Returns:
        The same cards as a tuple. The base order is ascending effort class (a
        rule id with no declared effort ranks as :attr:`EffortClass.MIDDLE`)
        then ``(rule_id, card_id)``; and if any VISIBLE card has reached
        ``aging_evaluations``, the most starved of them - highest count, and
        among equal counts the one the base order placed lowest - is moved to
        the front. At most one card is ever moved.

    Raises:
        TypeError: ``aging_evaluations`` is not an ``int``; ``deferrals`` is not
            a mapping; or a count in it is not an ``int``.
        ValueError: ``aging_evaluations`` is below 1, or a count is negative.
    """
    _check_threshold(aging_evaluations)
    _check_counts(deferrals)
    ordered = sorted(advised, key=_base_key)
    promoted = _most_starved(ordered, deferrals, aging_evaluations)
    if promoted is None:
        return tuple(ordered)
    return (ordered[promoted], *ordered[:promoted], *ordered[promoted + 1 :])


def order_shown(
    advised: Iterable[AdvisedCard],
    deferrals: Mapping[str, int],
    *,
    aging_evaluations: int = AGING_EVALUATIONS,
) -> tuple[AdvisedCard, ...]:
    """Order only the VISIBLE cards - exactly what a surface renders.

    Built on :func:`order_cards`: the same key, never a second ordering. A card
    that is muted or in a hidden state is dropped before ordering.

    Args:
        advised: The cards to order, in any sequence.
        deferrals: As :func:`order_cards` takes it.
        aging_evaluations: As :func:`order_cards` takes it.

    Returns:
        The visible cards, ordered.

    Raises:
        TypeError: as :func:`order_cards` raises it.
        ValueError: as :func:`order_cards` raises it.
    """
    return order_cards(
        (item for item in advised if item.visible),
        deferrals,
        aging_evaluations=aging_evaluations,
    )
