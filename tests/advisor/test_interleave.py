"""CS-1247: a deterministic domain interleave in the top-N card list.

Graded here (docs/LEDGER.md, the CS-1247 CLOSED record): a fixture with ten
power cards and two milestone cards shows both milestone cards in the top five,
and the interleave is a pure function with golden cases.

THE RED THIS MODULE WAS WRITTEN AGAINST. The CS-1246 showing order is effort
then identity, so a domain holding ten cheap cards takes every one of the first
ten places and a domain holding two dearer ones is read eleventh and twelfth.
:func:`test_the_base_order_alone_monopolises_the_top_five_with_one_domain` is
that control, asserted here rather than described, so the acceptance arm below
cannot pass by accident on a fixture that never had the fault.

EVERY CASE IS A GOLDEN CASE. The interleave takes a sequence and returns a
permutation of it; it reads no clock, opens no file and holds no state, so an
exact expected order can be written down for each input and is.

Every rule id, domain and subject here is synthetic.
"""

from __future__ import annotations

from typing import Final

from clockspeed.advisor.advise import AdvisedCard
from clockspeed.advisor.cards import Card
from clockspeed.advisor.ledger import CardState
from clockspeed.advisor.ranking import (
    AGING_EVALUATIONS,
    interleave_domains,
    order_cards,
)
from clockspeed.advisor.trace import Recommendation, StepKind, Trace, TraceStep

#: The acceptance fixture's two domains and the rule id each card carries. The
#: power rule is a registered QUICK one and the milestone rule is unlisted, so
#: the base order places every power card above every milestone card - which is
#: the monopoly the interleave exists to break.
POWER_DOMAIN: Final = "power"
MILESTONE_DOMAIN: Final = "milestone"
POWER_RULE: Final = "power.draw_incomplete"
MILESTONE_RULE: Final = "progress.milestone_gap"

#: The acceptance fixture's shape, and the window it is graded in.
POWER_CARDS: Final = 10
MILESTONE_CARDS: Final = 2
TOP_WINDOW: Final = 5


def _trace(rule_id: str, domain: str, subject: str) -> Trace:
    """One well-formed rule-fired trace, hand-built so the domain is a parameter."""
    return Trace(
        rule_id=rule_id,
        domain=domain,
        steps=(TraceStep(kind=StepKind.RULE_FIRED, subject=subject),),
        recommendation=Recommendation(
            subject_key=subject,
            action="Act",
            reason="why",
            target_milestone=None,
        ),
    )


def _advised(rule_id: str, domain: str, subject: str, *, muted: bool = False) -> AdvisedCard:
    card = Card(_trace(rule_id, domain, subject))
    return AdvisedCard(card=card, state=CardState("new"), muted=muted)


def _domains(cards: tuple[AdvisedCard, ...]) -> tuple[str, ...]:
    return tuple(advised.card.domain for advised in cards)


def _subjects(cards: tuple[AdvisedCard, ...]) -> tuple[str, ...]:
    return tuple(advised.card.trace.steps[0].subject for advised in cards)


def _fixture() -> tuple[AdvisedCard, ...]:
    """Ten power cards and two milestone cards, in the acceptance's own shape."""
    power = tuple(_advised(POWER_RULE, POWER_DOMAIN, f"power-{n}") for n in range(POWER_CARDS))
    milestone = tuple(
        _advised(MILESTONE_RULE, MILESTONE_DOMAIN, f"milestone-{n}") for n in range(MILESTONE_CARDS)
    )
    return (*power, *milestone)


# ---------------------------------------------------------------------------
# the control, then the acceptance


def test_the_base_order_alone_monopolises_the_top_five_with_one_domain() -> None:
    """THE CONTROL. Without the interleave the fixture has the fault it is about."""
    ordered = order_cards(_fixture(), {})
    assert set(_domains(ordered[:TOP_WINDOW])) == {POWER_DOMAIN}
    assert set(_domains(ordered[-MILESTONE_CARDS:])) == {MILESTONE_DOMAIN}


def test_acceptance_both_milestone_cards_read_in_the_top_five_past_ten_power_cards() -> None:
    interleaved = interleave_domains(order_cards(_fixture(), {}))
    top = _domains(interleaved[:TOP_WINDOW])
    assert top.count(MILESTONE_DOMAIN) == MILESTONE_CARDS
    # Both of them, not one card read twice: the ids in the window are distinct.
    window = interleaved[:TOP_WINDOW]
    assert len({advised.card.id for advised in window}) == TOP_WINDOW


def test_acceptance_the_fixture_has_one_golden_order() -> None:
    """The whole permutation, written down - the acceptance's golden case."""
    interleaved = interleave_domains(order_cards(_fixture(), {}))
    assert _domains(interleaved) == (
        POWER_DOMAIN,
        MILESTONE_DOMAIN,
        POWER_DOMAIN,
        MILESTONE_DOMAIN,
        *((POWER_DOMAIN,) * (POWER_CARDS - 2)),
    )


# ---------------------------------------------------------------------------
# golden cases over the documented rule


def test_one_domain_is_the_identity() -> None:
    cards = tuple(_advised(POWER_RULE, POWER_DOMAIN, f"power-{n}") for n in range(4))
    assert interleave_domains(cards) == cards


def test_an_empty_sequence_orders_to_an_empty_tuple() -> None:
    assert interleave_domains(()) == ()


def test_three_domains_round_robin_in_their_arrival_order() -> None:
    a1 = _advised("a.rule", "alpha", "a-1")
    a2 = _advised("a.rule", "alpha", "a-2")
    a3 = _advised("a.rule", "alpha", "a-3")
    b1 = _advised("b.rule", "beta", "b-1")
    c1 = _advised("c.rule", "gamma", "c-1")
    assert interleave_domains((a1, a2, a3, b1, c1)) == (a1, b1, c1, a2, a3)


def test_an_exhausted_domain_is_skipped_rather_than_holding_its_slot() -> None:
    a1 = _advised("a.rule", "alpha", "a-1")
    a2 = _advised("a.rule", "alpha", "a-2")
    a3 = _advised("a.rule", "alpha", "a-3")
    b1 = _advised("b.rule", "beta", "b-1")
    assert interleave_domains((a1, a2, a3, b1)) == (a1, b1, a2, a3)


def test_the_arrival_order_breaks_a_tie_between_equally_served_domains() -> None:
    """The documented tie-break, pinned both ways round on the same cards."""
    a1 = _advised("a.rule", "alpha", "a-1")
    b1 = _advised("b.rule", "beta", "b-1")
    assert interleave_domains((a1, b1)) == (a1, b1)
    assert interleave_domains((b1, a1)) == (b1, a1)


# ---------------------------------------------------------------------------
# the properties the composition rests on


def test_the_tie_break_is_the_arrival_index_in_every_round_not_only_the_first() -> None:
    """The one mutant the first cut of this module let live.

    An implementation that breaks a tie on the grouping's INSERTION order
    instead of the arrival index of each domain's next card agrees with every
    other arm here, because in those fixtures the two answers coincide. It
    disagrees on this one: at the third place alpha and beta have each given
    one, and beta's next card arrived before alpha's, so beta gives again.
    The insertion-order mutant answers ``(a1, b1, a2, b2)``.
    """
    a1 = _advised("a.rule", "alpha", "a-1")
    b1 = _advised("b.rule", "beta", "b-1")
    b2 = _advised("b.rule", "beta", "b-2")
    a2 = _advised("a.rule", "alpha", "a-2")
    assert interleave_domains((a1, b1, b2, a2)) == (a1, b1, b2, a2)


def test_the_head_of_the_input_is_the_head_of_the_output() -> None:
    """Why the CS-1246 aging promotion survives the interleave, asserted directly."""
    promoted = _advised(MILESTONE_RULE, MILESTONE_DOMAIN, "milestone-aged")
    power = tuple(_advised(POWER_RULE, POWER_DOMAIN, f"power-{n}") for n in range(6))
    assert interleave_domains((promoted, *power))[0] is promoted


def test_the_aging_promotion_still_leads_once_the_interleave_is_applied() -> None:
    """The composition the surface would use: CS-1246's order, then this one."""
    cards = _fixture()
    aged = cards[-1]
    ordered = order_cards(cards, {aged.card.id: AGING_EVALUATIONS})
    assert ordered[0] is aged
    assert interleave_domains(ordered)[0] is aged


def test_the_result_is_a_permutation_of_its_input() -> None:
    cards = _fixture()
    interleaved = interleave_domains(cards)
    assert len(interleaved) == len(cards)
    assert sorted(_subjects(interleaved)) == sorted(_subjects(cards))


def test_the_order_within_one_domain_is_the_order_it_arrived_in() -> None:
    cards = _fixture()
    interleaved = interleave_domains(cards)
    for domain in (POWER_DOMAIN, MILESTONE_DOMAIN):
        arrived = tuple(a for a in cards if a.card.domain == domain)
        kept = tuple(a for a in interleaved if a.card.domain == domain)
        assert kept == arrived


def test_every_prefix_is_as_balanced_as_the_cards_allow() -> None:
    """Why there is no N parameter: each prefix, not one chosen window, is balanced."""
    interleaved = interleave_domains(order_cards(_fixture(), {}))
    for length in range(1, len(interleaved) + 1):
        counts = [
            _domains(interleaved[:length]).count(domain)
            for domain in (POWER_DOMAIN, MILESTONE_DOMAIN)
        ]
        remaining = [POWER_CARDS - counts[0], MILESTONE_CARDS - counts[1]]
        # A domain is read ahead of another only while the other has none left
        # to give, so no prefix is two or more cards out of balance while both
        # domains can still contribute.
        if all(left > 0 for left in remaining):
            assert max(counts) - min(counts) <= 1, length


def test_two_calls_on_one_sequence_agree_so_nothing_is_carried_between_them() -> None:
    """Not a tautology: an implementation holding a cursor across calls differs here."""
    cards = _fixture()
    assert interleave_domains(cards) == interleave_domains(cards)


def test_a_lone_domain_is_read_once_every_earlier_domain_has_given_one() -> None:
    """A third domain of one card waits its turn in the first round, not past it."""
    cards = _fixture()
    lone = _advised("z.rule", "zeta", "zeta-1")
    interleaved = interleave_domains((*cards, lone))
    assert interleaved[2] is lone


def test_a_hidden_card_is_interleaved_like_any_other() -> None:
    """The interleave is about DOMAIN, never about visibility - that is order_shown's."""
    muted = _advised(MILESTONE_RULE, MILESTONE_DOMAIN, "milestone-muted", muted=True)
    power = tuple(_advised(POWER_RULE, POWER_DOMAIN, f"power-{n}") for n in range(3))
    assert muted.visible is False
    assert interleave_domains((*power, muted))[1] is muted
