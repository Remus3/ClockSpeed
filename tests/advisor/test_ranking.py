"""CS-1246 slice B: quick-win card ordering with an aging guard.

Graded here (docs/item_notes/phase5.md, CS-1246 acceptance): a fixture with one
large card and several small ones brings the large card to the top after the
configured number of evaluations, and the same ledger state gives the same
order. The aging is read from a plain mapping of deferral counts keyed by card
id - never from a clock - so every case below is a golden case over arguments
alone.

Every rule id outside the registry, every subject and every count here is
synthetic.
"""

from __future__ import annotations

import random
from collections.abc import Mapping

import pytest

from clockspeed.advisor.advise import AdvisedCard
from clockspeed.advisor.cards import Card
from clockspeed.advisor.ledger import CardState
from clockspeed.advisor.ranking import (
    AGING_EVALUATIONS,
    EFFORT_BY_RULE,
    EffortClass,
    effort_of,
    order_cards,
    order_shown,
    undeclared_rule_ids,
)
from clockspeed.advisor.rules import registered_rules
from clockspeed.advisor.trace import RuleSpec
from tests.advisor.test_cards import _forged

# A large rule that sorts BEFORE every quick one by identity, so the quick-win
# lead below is the effort class speaking and not the identity tie-break.
_LARGE_RULE = "plan.adopt"
_QUICK_RULE = "power.draw_incomplete"
_MIDDLE_RULE = "power.fuel_supply"
_UNLISTED_RULE = "synthetic.unlisted"
_SMALL_COUNT = 3
_ABSURD = 424242


def _advised(rule_id: str, subject: str, *, kind: str = "new", muted: bool = False) -> AdvisedCard:
    card = Card(_forged(rule_id=rule_id, subject=subject))
    return AdvisedCard(card=card, state=CardState(kind), muted=muted)


def _ids(cards: tuple[AdvisedCard, ...]) -> tuple[str, ...]:
    return tuple(advised.card.id for advised in cards)


def _fixture() -> tuple[AdvisedCard, tuple[AdvisedCard, ...]]:
    large = _advised(_LARGE_RULE, "the-big-build")
    small = tuple(_advised(_QUICK_RULE, f"small-{n}") for n in range(_SMALL_COUNT))
    return large, small


# ---------------------------------------------------------------------------
# the acceptance


def test_acceptance_one_large_card_and_several_small_ones_the_large_one_ages_to_the_top() -> None:
    large, small = _fixture()
    cards = (large, *small)

    # No deferrals: the quick wins lead and the large card is last.
    fresh = order_cards(cards, {})
    assert fresh[-1] is large
    assert set(_ids(fresh[:-1])) == {advised.card.id for advised in small}

    # The large card deferred the configured number of times comes FIRST.
    aged = order_cards(cards, {large.card.id: AGING_EVALUATIONS})
    assert aged[0] is large

    # The same ledger state gives the same order, whatever the input sequence.
    # Comparing two calls on the same sequence would be a tautology, so the
    # arm is the shuffle: the state decides the order, the input order does not.
    state = {large.card.id: AGING_EVALUATIONS, small[0].card.id: 1}
    shuffler = random.Random(1246)  # noqa: S311 - reproducible fixtures, not secrets
    for _ in range(8):
        shuffled = list(cards)
        shuffler.shuffle(shuffled)
        assert _ids(order_cards(shuffled, state)) == _ids(order_cards(cards, state))


def test_a_count_one_below_the_threshold_does_not_promote() -> None:
    large, small = _fixture()
    below = order_cards((large, *small), {large.card.id: AGING_EVALUATIONS - 1})
    assert below[-1] is large


def test_a_custom_threshold_replaces_the_default() -> None:
    large, small = _fixture()
    counts = {large.card.id: 2}
    assert order_cards((large, *small), counts, aging_evaluations=2)[0] is large
    assert order_cards((large, *small), counts, aging_evaluations=3)[-1] is large


def test_the_default_threshold_is_a_positive_int() -> None:
    assert type(AGING_EVALUATIONS) is int
    assert AGING_EVALUATIONS >= 1


def test_only_the_most_starved_card_is_promoted_and_the_rest_keep_the_base_order() -> None:
    """Three cards past the threshold promote ONE: the highest count, and only it."""
    large, small = _fixture()
    older, newer = small[0], small[1]
    counts = {
        older.card.id: AGING_EVALUATIONS + 5,
        newer.card.id: AGING_EVALUATIONS,
        large.card.id: AGING_EVALUATIONS + 9,
    }
    cards = (newer, older, large, small[2])
    ordered = order_cards(cards, counts)
    assert ordered[0] is large
    # Every other card keeps the order it would have had with no aging at all.
    base = order_cards(cards, {})
    assert ordered[1:] == tuple(advised for advised in base if advised is not large)


def test_equal_counts_promote_the_card_the_base_order_placed_lowest() -> None:
    """The documented tie-break: lowest-placed is the one being pushed down."""
    large, small = _fixture()
    cards = (large, *small)
    base = order_cards(cards, {})
    counts = {advised.card.id: AGING_EVALUATIONS for advised in cards}
    ordered = order_cards(cards, counts)
    assert ordered[0] is base[-1]
    assert ordered[1:] == base[:-1]


def test_the_identity_tie_break_holds_between_equal_effort_and_equal_count() -> None:
    _, small = _fixture()
    expected = tuple(sorted(small, key=lambda advised: (advised.card.rule_id, advised.card.id)))
    assert order_cards(reversed(small), {}) == expected
    # Equal counts move the lowest-placed card up and leave the rest in order.
    counts = {advised.card.id: AGING_EVALUATIONS for advised in small}
    assert order_cards(reversed(small), counts) == (expected[-1], *expected[:-1])


def test_identity_breaks_a_tie_between_two_rules_of_one_effort_class() -> None:
    one = _advised("power.fuel_supply", "tie")
    two = _advised("synthetic.tied-moderate", "tie")
    assert effort_of(one.card.rule_id) is effort_of(two.card.rule_id) is EffortClass.MIDDLE
    assert order_cards((two, one), {}) == (one, two)


def test_effort_orders_the_classes_cheapest_first() -> None:
    quick = _advised(_QUICK_RULE, "q")
    middle = _advised(_MIDDLE_RULE, "m")
    large = _advised(_LARGE_RULE, "l")
    assert order_cards((large, middle, quick), {}) == (quick, middle, large)


def test_an_equal_key_keeps_input_order() -> None:
    first = _advised(_QUICK_RULE, "twin")
    second = _advised(_QUICK_RULE, "twin")
    assert first.card.id == second.card.id
    assert order_cards((second, first), {}) == (second, first)
    assert order_cards((first, second), {}) == (first, second)


def test_a_rule_with_no_declared_effort_ranks_in_the_middle_class() -> None:
    assert _UNLISTED_RULE not in EFFORT_BY_RULE
    assert effort_of(_UNLISTED_RULE) is EffortClass.MIDDLE
    quick = _advised(_QUICK_RULE, "q")
    unlisted = _advised(_UNLISTED_RULE, "u")
    large = _advised(_LARGE_RULE, "l")
    assert order_cards((large, unlisted, quick), {}) == (quick, unlisted, large)


def test_a_missing_id_means_zero_and_the_input_is_not_mutated() -> None:
    large, small = _fixture()
    counts: dict[str, int] = {"not-a-card-id": AGING_EVALUATIONS}
    before = dict(counts)
    result = order_cards((large, *small), counts)
    assert result[-1] is large
    assert counts == before
    assert type(result) is tuple


def test_ordering_accepts_a_one_shot_iterable() -> None:
    large, small = _fixture()
    ordered = order_cards(iter((large, *small)), {large.card.id: AGING_EVALUATIONS})
    assert ordered[0] is large
    assert len(ordered) == len(small) + 1


# ---------------------------------------------------------------------------
# the visible subset


def test_order_shown_orders_only_what_is_visible_on_the_same_key() -> None:
    large, small = _fixture()
    hidden = _advised(_QUICK_RULE, "hidden", kind="dismissed")
    muted = _advised(_QUICK_RULE, "muted", muted=True)
    everything = (hidden, large, muted, *small)
    counts = {large.card.id: AGING_EVALUATIONS, hidden.card.id: AGING_EVALUATIONS + 4}
    shown = order_shown(everything, counts)
    assert hidden not in shown
    assert muted not in shown
    assert shown == tuple(advised for advised in order_cards(everything, counts) if advised.visible)
    assert shown[0] is large


# ---------------------------------------------------------------------------
# the declared effort table and its census


def test_every_registered_rule_declares_an_effort() -> None:
    assert undeclared_rule_ids() == frozenset()
    assert undeclared_rule_ids(registered_rules()) == frozenset()


def test_the_effort_table_names_no_rule_that_is_not_registered() -> None:
    registered = {spec.rule_id for spec in registered_rules()}
    assert set(EFFORT_BY_RULE) == registered


def test_the_census_reports_a_rule_with_no_declared_effort() -> None:
    gap = RuleSpec(
        rule_id=_UNLISTED_RULE, domain="power", inputs=(), unlocks=(), evaluate=lambda _ctx: None
    )
    assert undeclared_rule_ids((*registered_rules(), gap)) == frozenset({_UNLISTED_RULE})


def test_the_scale_is_three_coarse_classes_in_a_total_order() -> None:
    classes = list(EffortClass)
    assert len(classes) == 3  # noqa: PLR2004 - the scale is three classes by decision
    assert classes == sorted(classes)
    assert [int(member) for member in classes] == sorted({int(member) for member in classes})
    assert EffortClass.QUICK < EffortClass.MIDDLE < EffortClass.LARGE


def test_the_effort_table_is_immutable() -> None:
    assert isinstance(EFFORT_BY_RULE, Mapping)
    with pytest.raises(TypeError):
        EFFORT_BY_RULE["power.headroom"] = EffortClass.QUICK  # type: ignore[index]


# ---------------------------------------------------------------------------
# refusals


@pytest.mark.parametrize("bad", [0, -1, True, 1.5, "3", None])
def test_a_bad_threshold_is_refused_by_field_name(bad: object) -> None:
    large, small = _fixture()
    with pytest.raises((TypeError, ValueError)) as caught:
        order_cards((large, *small), {}, aging_evaluations=bad)  # type: ignore[arg-type]
    assert "aging threshold" in str(caught.value)


def test_a_threshold_message_never_carries_the_value() -> None:
    large, small = _fixture()
    with pytest.raises(ValueError, match="aging threshold") as caught:
        order_cards((large, *small), {}, aging_evaluations=-_ABSURD)
    assert str(_ABSURD) not in str(caught.value)


@pytest.mark.parametrize("bad", [-1, -_ABSURD, True, 1.5, "2", None])
def test_a_bad_count_is_refused_by_field_name(bad: object) -> None:
    large, small = _fixture()
    with pytest.raises((TypeError, ValueError)) as caught:
        order_cards((large, *small), {large.card.id: bad})  # type: ignore[dict-item]
    message = str(caught.value)
    assert "deferral count" in message
    assert str(_ABSURD) not in message
    assert large.card.id not in message


def test_a_bad_count_is_refused_even_for_an_id_no_card_carries() -> None:
    large, small = _fixture()
    with pytest.raises(ValueError, match="deferral count"):
        order_shown((large, *small), {"not-a-card-id": -1})


def test_a_non_mapping_of_counts_is_refused() -> None:
    large, small = _fixture()
    with pytest.raises(TypeError, match="deferral count"):
        order_cards((large, *small), [(large.card.id, 1)])  # type: ignore[arg-type]
