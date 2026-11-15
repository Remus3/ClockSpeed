"""CS-1246: the aging guard, pinned through SERVED acts.

THE CLAIM. The card list the surface serves for a world reads the large card first after
``AGING_EVALUATIONS`` acts beyond the act that first records it, and not after one fewer. The
acts are ``POST /api/advice/act`` over the real route table, the real source, the real advisor
and the real ledger (``tests/surface/test_advice_act.py`` owns the fixture and the act itself),
never a test-only call into ``advise_and_record``.

THE FIXTURE. A stated plan card (``plan.adopt``, LARGE) beside one quick card
(``power.draw_incomplete``). Both are visible and ``new``, so no hidden card leads a listing and
the order a listing reads is the aging guard's alone. The identity order puts ``plan.adopt``
first and the showing order puts the quick card first, which is what makes the two arms below
able to tell the displayed order from the identity order.

THE TWO MUTANTS GRADED HERE, each green on the build and red under its mutant:

- ``Ledger.reconcile`` handed ``Advice.shown`` (identity order) rather than
  ``Advice.ranked_shown`` (the order the player was shown). Then the card that LED the
  showing is counted as passed over, and the card that sat below is credited with a turn.
- ``deferrals=`` dropped from the :class:`Advice` ``advise_and_record`` returns. Then the
  recording act answers in the order it started from, one act behind the ledger.

Every token, id and number is invented. No save and no install is read.
"""

from __future__ import annotations

from dataclasses import replace
from types import MappingProxyType
from typing import TYPE_CHECKING, Final

from clockspeed.advisor import ranking
from clockspeed.advisor.ledger import Ledger
from clockspeed.advisor.rules import fuel as fuel_rules
from clockspeed.audit.machines import PROPERTY_OVERCLOCK, PROPERTY_PRODUCING
from clockspeed.save.world import WorldProperties
from clockspeed.surface.api import advice as advice_endpoint
from clockspeed.surface.api import contract
from tests.advisor import test_world_advice as world_fixtures
from tests.audit import test_balance as balance_fixtures
from tests.audit import test_fuel as fuel_audit_fixtures
from tests.surface import test_advice_act as act_fixtures

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    from clockspeed.advisor.advise import Advice
    from clockspeed.data.registry import Registry
    from clockspeed.save.world import WorldModel

LARGE: Final = act_fixtures.LARGE_RULE
QUICK: Final = act_fixtures.QUICK_RULE


def _act_order(response_data: Mapping[str, object]) -> list[str]:
    return act_fixtures._order(response_data)  # noqa: SLF001


def _acts(directory: Path, count: int) -> list[list[str]]:
    """The rule-id order each of ``count`` stated acts answers, in order."""
    table = act_fixtures._table(directory)  # noqa: SLF001
    orders: list[list[str]] = []
    for _ in range(count):
        data = act_fixtures._data(act_fixtures._act(table, act_fixtures._stated()))  # noqa: SLF001
        orders.append(_act_order(data))
    return orders


def _listed(directory: Path) -> list[str]:
    """The rule-id order the stated GET listing serves over what the acts recorded."""
    table = act_fixtures._table(directory)  # noqa: SLF001
    data = act_fixtures._listing(table, act_fixtures._stated())  # noqa: SLF001
    cards = data["cards"]
    assert isinstance(cards, list)
    assert all(card["visible"] is True and card["state"] == "new" for card in cards), cards
    return _act_order(data)


def _stated_advice(directory: Path) -> Advice:
    """The READ-ONLY advice over the stated fixture, with the ledger as the acts left it."""
    model, registry = act_fixtures._large_and_quick()  # noqa: SLF001
    source = act_fixtures._source(directory)  # noqa: SLF001
    parameters = source.plan_parameters(rate="10", direction="raw", byproduct_policy="balanced")
    assert parameters is not None
    request = source.plan_request(
        registry, act_fixtures.source_fixtures.SOLVE_RELIC_ITEM, parameters
    )
    found = source.advice(model, registry, plan_request=request)
    assert found is not None
    return found


# ---------------------------------------------------------------------------
# The served listing, at and one short of the threshold
# ---------------------------------------------------------------------------


def test_the_served_listing_reads_the_large_card_first_after_the_threshold_of_further_acts(
    tmp_path: Path,
) -> None:
    _acts(tmp_path, 1 + ranking.AGING_EVALUATIONS)

    listed = _listed(tmp_path)

    assert listed[0] == LARGE
    assert listed[1:] == [QUICK]


def test_the_served_listing_does_not_read_the_large_card_first_one_further_act_short(
    tmp_path: Path,
) -> None:
    _acts(tmp_path, 1 + ranking.AGING_EVALUATIONS - 1)

    listed = _listed(tmp_path)

    assert listed[0] == QUICK
    assert listed[1:] == [LARGE]


def test_the_first_acts_listing_leads_with_the_quick_card_not_the_identity_order(
    tmp_path: Path,
) -> None:
    # The control that makes the two arms above able to fail: the identity order is the
    # other way round, so a list that never ranked would read the large card first here.
    advice = _stated_advice(tmp_path)

    identity = [advised.card.rule_id for advised in advice.cards]
    ranked = [advised.card.rule_id for advised in advice.ranked]
    assert identity[0] == LARGE
    assert ranked[0] == QUICK


# ---------------------------------------------------------------------------
# Mutant (b): the act's own answer carries the post-record deferrals
# ---------------------------------------------------------------------------


def test_the_act_that_reaches_the_threshold_answers_with_the_large_card_first(
    tmp_path: Path,
) -> None:
    orders = _acts(tmp_path, 1 + ranking.AGING_EVALUATIONS)

    before = orders[ranking.AGING_EVALUATIONS - 1]
    reaching = orders[ranking.AGING_EVALUATIONS]
    assert before[0] == QUICK
    assert reaching[0] == LARGE


def test_the_advice_an_act_returns_carries_nonzero_deferrals_equal_to_the_ledgers(
    tmp_path: Path,
) -> None:
    model, registry = act_fixtures._large_and_quick()  # noqa: SLF001
    source = act_fixtures._source(tmp_path)  # noqa: SLF001
    parameters = source.plan_parameters(rate="10", direction="raw", byproduct_policy="balanced")
    assert parameters is not None
    request = source.plan_request(
        registry, act_fixtures.source_fixtures.SOLVE_RELIC_ITEM, parameters
    )
    source.act(model, registry, plan_request=request)

    second = source.act(model, registry, plan_request=request)

    assert not isinstance(second, str)
    nonzero = len(second.deferrals) > 0
    assert nonzero
    same = dict(second.deferrals) == dict(Ledger(tmp_path).deferrals(model.token))
    assert same


# ---------------------------------------------------------------------------
# Mutant (a): the ranked leader is credited, the card below it is deferred
# ---------------------------------------------------------------------------


def test_the_showing_order_and_the_identity_order_lead_with_different_cards_in_the_fixture(
    tmp_path: Path,
) -> None:
    # The precondition of the arm below: with the two leaders equal, handing the ledger
    # either order would record the same counts and the mutant could not be told apart.
    advice = _stated_advice(tmp_path)

    shown_first = advice.shown[0].card.rule_id
    ranked_first = advice.ranked_shown[0].card.rule_id
    assert shown_first == LARGE
    assert ranked_first == QUICK


def test_a_further_act_clears_the_ranked_leader_and_ages_the_card_below_it(
    tmp_path: Path,
) -> None:
    ids = act_fixtures._card_ids(tmp_path)  # noqa: SLF001
    _acts(tmp_path, 2)

    counts = act_fixtures._counts(tmp_path)  # noqa: SLF001

    assert counts.get(ids[QUICK], 0) == 0
    assert counts.get(ids[LARGE], 0) == 1


def test_the_act_template_is_the_one_these_arms_drive() -> None:
    assert advice_endpoint.ACT_ENDPOINT == "/api/advice/act"


# ---------------------------------------------------------------------------
# One large card beside TWO small ones: the second small card ages too (CS-1246)
# ---------------------------------------------------------------------------

#: The second small card the three-card fixture adds: a solid burner with no supply read.
SECOND_SMALL: Final = fuel_rules.DEMAND_RULE.rule_id

#: The three cards the fixture holds.
THREE_CARDS: Final = 3


def _large_and_two_small() -> tuple[WorldModel, Registry]:
    """The stated plan card, the unpriced-machine card and a solid burner's fuel-demand card."""
    plan_model, plan_registry = act_fixtures.source_fixtures._ascent()  # noqa: SLF001
    fuel_registry = world_fixtures.fuel_registry()
    registry = replace(
        plan_registry,
        items=MappingProxyType({**plan_registry.items, **fuel_registry.items}),
        buildings=MappingProxyType(
            {
                **plan_registry.buildings,
                **dict(balance_fixtures.whole_world_registry()),
                **fuel_registry.buildings,
            }
        ),
        generators=MappingProxyType({**plan_registry.generators, **fuel_registry.generators}),
    )
    base = balance_fixtures.world_of(
        balance_fixtures.FIXED_WHOLE, world_fixtures.UNPRICED_MACHINE, fuel_audit_fixtures.GEN_COAL
    )
    entries = dict(base.properties.by_record_index)
    entries[1] = replace(entries[1], values=MappingProxyType({PROPERTY_PRODUCING: True}))
    entries[2] = replace(
        entries[2],
        values=MappingProxyType({PROPERTY_PRODUCING: True, PROPERTY_OVERCLOCK: 1.0}),
    )
    model = replace(
        base,
        properties=WorldProperties(by_record_index=MappingProxyType(entries)),
        unlocks=plan_model.unlocks,
    )
    return model, registry


def _three_table(directory: Path) -> Mapping[tuple[str, str], contract.Handler]:
    model, registry = _large_and_two_small()
    return act_fixtures._table(directory, model, registry)  # noqa: SLF001


def _three_acts(directory: Path, count: int) -> list[list[str]]:
    """The rule-id order each of ``count`` stated acts answers over the three-card world."""
    table = _three_table(directory)
    return [
        _act_order(act_fixtures._data(act_fixtures._act(table, act_fixtures._stated())))  # noqa: SLF001
        for _ in range(count)
    ]


def _three_listed(directory: Path) -> list[str]:
    data = act_fixtures._listing(_three_table(directory), act_fixtures._stated())  # noqa: SLF001
    cards = data["cards"]
    assert isinstance(cards, list)
    assert len(cards) == THREE_CARDS
    assert all(card["visible"] is True and card["state"] == "new" for card in cards)
    return _act_order(data)


def _three_counts(directory: Path) -> dict[str, int]:
    """Rule id to deferral count, read from a fresh ledger over the three-card world."""
    model, registry = _large_and_two_small()
    source = act_fixtures._source(directory)  # noqa: SLF001
    parameters = source.plan_parameters(rate="10", direction="raw", byproduct_policy="balanced")
    assert parameters is not None
    request = source.plan_request(
        registry, act_fixtures.source_fixtures.SOLVE_RELIC_ITEM, parameters
    )
    found = source.advice(model, registry, plan_request=request)
    assert found is not None
    held = dict(Ledger(directory).deferrals(model.token))
    return {advised.card.rule_id: held.get(advised.card.id, 0) for advised in found.cards}


def test_the_three_card_fixture_leads_with_the_small_cards_and_ends_with_the_large_one(
    tmp_path: Path,
) -> None:
    # The control for the arms below: the large card is LAST until it ages.
    first = _three_acts(tmp_path, 1)[0]

    assert first == [QUICK, SECOND_SMALL, LARGE]


def test_the_large_card_reads_first_past_two_small_cards_and_the_second_small_card_ages_too(
    tmp_path: Path,
) -> None:
    _three_acts(tmp_path, 1 + ranking.AGING_EVALUATIONS)

    listed = _three_listed(tmp_path)
    counts = _three_counts(tmp_path)

    # The second small card reached the threshold beside the large one and was NOT promoted:
    # one card moves, the most starved, and a tie goes to the one the base order put lowest.
    assert counts[SECOND_SMALL] == ranking.AGING_EVALUATIONS
    assert counts[LARGE] == ranking.AGING_EVALUATIONS
    assert counts[QUICK] == 0
    assert listed == [LARGE, QUICK, SECOND_SMALL]


def test_one_further_act_short_the_large_card_still_reads_last_past_two_small_cards(
    tmp_path: Path,
) -> None:
    _three_acts(tmp_path, 1 + ranking.AGING_EVALUATIONS - 1)

    listed = _three_listed(tmp_path)
    counts = _three_counts(tmp_path)

    assert counts[SECOND_SMALL] == ranking.AGING_EVALUATIONS - 1
    assert counts[LARGE] == ranking.AGING_EVALUATIONS - 1
    assert listed == [QUICK, SECOND_SMALL, LARGE]


def test_the_act_that_reaches_the_threshold_answers_large_first_past_two_small_cards(
    tmp_path: Path,
) -> None:
    orders = _three_acts(tmp_path, 1 + ranking.AGING_EVALUATIONS)

    assert orders[ranking.AGING_EVALUATIONS - 1] == [QUICK, SECOND_SMALL, LARGE]
    assert orders[ranking.AGING_EVALUATIONS] == [LARGE, QUICK, SECOND_SMALL]
