"""CS-1270 groundwork - the handlers ``/api/advice`` and its derivation will serve.

THE CLAIM. ``clockspeed/surface/api/advice.py`` turns an ``Advice`` from the
advisor (``clockspeed/advisor/advise.py``) into the two read bodies:
``/api/advice`` carries every card with tier 1 and tier 2 plus its resolved
ledger state and mute flag; ``/api/advice/<id>/derivation`` carries tier 3 for
one card. Both TRANSCRIBE - the endpoint computes nothing. The PUBLISHED table
still answers both with 501 naming CS-1270, graded in
``tests/surface/test_pending.py``: the advisor has no function building its
inputs from a world yet, and the surface may not compose the audit models
itself (CS-1189's machines seam). These arms drive the handlers directly.

THE REFUSALS ARE THE OTHER ROUTES' REFUSALS. No world is 503 ``no_save``, no
install is 503 ``no_game_install``, an advice store the provider could not read
is 503 ``advice_store_unreadable``, an unknown parameter is 400 and a card id the
current advice does not carry is 400 ``invalid_parameter`` - and no 400 reflects
what it refused.

PRIVACY. The world token reaches the advice source and goes no further: the
served bytes are asserted not to carry it, through a scalar so pytest's assert
rewriting cannot render it.

THE SOURCE IS A STUB. Every arm hands the handlers an ``Advice`` the real
advisor produced over a temporary store directory with an injected instant, so
no arm reads the repository's own ``data/`` and no arm reads a wall clock. The
concrete source that reads the real stores is CS-1270's to write.

Every token, id and number here is invented. No save and no install is read.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

import pytest

from clockspeed.advisor.advise import Advice, advise
from clockspeed.advisor.ledger import CardState, Ledger, MuteStore
from clockspeed.advisor.rules import power
from clockspeed.surface.api import advice as advice_endpoint
from clockspeed.surface.api import contract
from tests.advisor import test_advise as advise_fixtures
from tests.solve import synthetic as solve_synthetic
from tests.surface import test_map as map_fixtures

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    from clockspeed.data.registry import Registry
    from clockspeed.save.world import WorldModel

#: The instant every resolution here reads. Injected, never a clock.
NOW: Final = 1000

#: The listing and the derivation. The state write is not this module's.
EXPECTED_READ_ROUTES: Final = 2

#: A card id no advice here carries. Well formed, so only membership refuses it.
UNKNOWN_CARD_ID: Final = "0" * 64


class _Source:
    """An advice source that hands back a fixed answer and records what it saw."""

    def __init__(self, value: Advice | None) -> None:
        """Hold the answer.

        Args:
            value: The advice, or None for an unreadable store.
        """
        self._value = value
        self.calls = 0

    def advice(self, world: WorldModel, registry: Registry) -> Advice | None:
        """Answer with the held advice.

        Args:
            world: Ignored beyond counting.
            registry: Ignored beyond counting.

        Returns:
            The held advice, or None.
        """
        del world, registry
        self.calls += 1
        return self._value


def _advice_on(directory: Path) -> Advice:
    """Run the real advisor over the synthetic gap world on a temporary store."""
    return advise(
        advise_fixtures.TOKEN_A,
        advise_fixtures._first_load(),  # noqa: SLF001 - the shared synthetic world
        ledger=Ledger(directory),
        mutes=MuteStore(directory),
        now=NOW,
    )


def _gap_card_id(found: Advice) -> str:
    ids = [a.card.id for a in found.cards if a.card.rule_id == power.GAP_RULE.rule_id]
    count = len(ids)
    assert count == 1
    return ids[0]


def _handlers(
    source: _Source,
    *,
    with_world: bool = True,
    with_registry: bool = True,
) -> tuple[contract.Handler, contract.Handler]:
    worlds = map_fixtures._Worlds(  # noqa: SLF001 - the shared stub provider
        map_fixtures.empty_world() if with_world else None
    )
    registries = map_fixtures._Registries(  # noqa: SLF001 - the shared stub provider
        solve_synthetic.solve_registry() if with_registry else None
    )
    published = advice_endpoint.routes(worlds, registries, source)
    by_template = {route.template: route.handler for route in published}
    count = len(by_template)
    assert count == len(published)
    return (
        by_template[advice_endpoint.ENDPOINT],
        by_template[advice_endpoint.DERIVATION_ENDPOINT],
    )


def _data(response: contract.Response) -> Mapping[str, object]:
    assert response.http_status == contract.HTTP_OK
    problems = contract.contract_problems(response)
    count = len(problems)
    assert count == 0, problems
    data = response.payload["data"]
    assert isinstance(data, dict)
    return data


def _cards(data: Mapping[str, object]) -> list[Mapping[str, object]]:
    cards = data["cards"]
    assert isinstance(cards, list)
    return cards


# ---------------------------------------------------------------------------
# The route table
# ---------------------------------------------------------------------------


def test_the_module_publishes_the_two_read_routes_as_gets() -> None:
    published = advice_endpoint.routes(
        map_fixtures._Worlds(None),  # noqa: SLF001
        map_fixtures._Registries(None),  # noqa: SLF001
        _Source(None),
    )
    identities = sorted((route.method, route.template) for route in published)
    count = len(identities)
    assert count == EXPECTED_READ_ROUTES
    assert identities == [
        ("GET", "/api/advice"),
        ("GET", "/api/advice/<id>/derivation"),
    ]


# ---------------------------------------------------------------------------
# /api/advice
# ---------------------------------------------------------------------------


def test_advice_answers_200_with_tier_one_and_two_per_card(tmp_path: Path) -> None:
    found = _advice_on(tmp_path)
    expected = len(found.cards)
    assert expected > 0, "the synthetic world fires no rule, so the sweep would be vacuous"

    listing, _derivation = _handlers(_Source(found))
    data = _data(listing({}))

    assert frozenset(data) == advice_endpoint.DATA_KEYS
    cards = _cards(data)
    count = len(cards)
    assert count == expected
    for served, advised in zip(cards, found.cards, strict=True):
        assert frozenset(served) == advice_endpoint.CARD_KEYS
        assert served["id"] == advised.card.id
        assert served["rule_id"] == advised.card.rule_id
        assert served["domain"] == advised.card.domain
        assert served["headline"] == advised.card.tier1
        assert served["reason"] == advised.card.tier2
        assert served["state"] == advised.state.kind
        assert served["muted"] is advised.muted
        assert served["visible"] is advised.visible
    assert data["new_world"] is found.new_world


def test_advice_never_carries_tier_three(tmp_path: Path) -> None:
    found = _advice_on(tmp_path)
    listing, _derivation = _handlers(_Source(found))
    encoded = contract.encode(listing({}).payload)
    derivations = [a.card.tier3 for a in found.cards]
    count = len(derivations)
    assert count > 0
    carried = sum(1 for text in derivations if text.encode("ascii") in encoded)
    assert carried == 0


def test_a_dismissed_card_is_served_hidden_with_its_state(tmp_path: Path) -> None:
    first = _advice_on(tmp_path)
    gap = _gap_card_id(first)
    Ledger(tmp_path).set_state(advise_fixtures.TOKEN_A, gap, CardState.dismissed())
    second = _advice_on(tmp_path)

    listing, _derivation = _handlers(_Source(second))
    cards = [card for card in _cards(_data(listing({}))) if card["id"] == gap]
    count = len(cards)
    assert count == 1
    assert cards[0]["state"] == "dismissed"
    assert cards[0]["visible"] is False
    assert cards[0]["snoozed_until"] is None


def test_a_snoozed_card_serves_its_until_instant(tmp_path: Path) -> None:
    first = _advice_on(tmp_path)
    gap = _gap_card_id(first)
    Ledger(tmp_path).snooze(advise_fixtures.TOKEN_A, gap, until=NOW + 60, now=NOW)
    second = _advice_on(tmp_path)

    listing, _derivation = _handlers(_Source(second))
    cards = [card for card in _cards(_data(listing({}))) if card["id"] == gap]
    assert cards[0]["state"] == "snoozed"
    assert cards[0]["snoozed_until"] == NOW + 60
    assert cards[0]["visible"] is False


def test_the_world_token_never_reaches_the_wire(tmp_path: Path) -> None:
    found = _advice_on(tmp_path)
    listing, derivation = _handlers(_Source(found))
    gap = _gap_card_id(found)
    bodies = (
        contract.encode(listing({}).payload),
        contract.encode(derivation({advice_endpoint.ID_PARAMETER: gap}).payload),
    )
    needle = advise_fixtures.TOKEN_A.encode("ascii")
    leaked = sum(1 for body in bodies if needle in body)
    assert leaked == 0


def test_the_token_detector_detects_a_planted_token() -> None:
    needle = advise_fixtures.TOKEN_A.encode("ascii")
    planted = contract.encode({"status": "ok", "planted": advise_fixtures.TOKEN_A})
    leaked = sum(1 for body in (planted,) if needle in body)
    assert leaked == 1


def test_advice_with_no_world_is_503_no_save() -> None:
    source = _Source(None)
    listing, _derivation = _handlers(source, with_world=False)
    response = listing({})
    assert response.http_status == contract.HTTP_UNAVAILABLE
    assert response.payload["reason"] == contract.REASON_NO_SAVE
    assert source.calls == 0


def test_advice_with_no_install_is_503_no_game_install() -> None:
    source = _Source(None)
    listing, _derivation = _handlers(source, with_registry=False)
    response = listing({})
    assert response.http_status == contract.HTTP_UNAVAILABLE
    assert response.payload["reason"] == contract.REASON_NO_GAME_INSTALL
    assert source.calls == 0


def test_advice_with_an_unreadable_store_is_503_and_names_it() -> None:
    listing, _derivation = _handlers(_Source(None))
    response = listing({})
    problems = contract.contract_problems(response)
    count = len(problems)
    assert count == 0
    assert response.http_status == contract.HTTP_UNAVAILABLE
    assert response.payload["reason"] == contract.REASON_ADVICE_STORE_UNREADABLE


def test_advice_refuses_a_parameter_and_reflects_none_of_it(tmp_path: Path) -> None:
    planted = "planted-value-never-echoed"
    listing, _derivation = _handlers(_Source(_advice_on(tmp_path)))
    response = listing({"x": planted})
    assert response.http_status == contract.HTTP_BAD_REQUEST
    assert response.payload["reason"] == contract.REASON_UNKNOWN_PARAMETER
    reflected = planted.encode("ascii") in contract.encode(response.payload)
    assert reflected is False


# ---------------------------------------------------------------------------
# /api/advice/<id>/derivation
# ---------------------------------------------------------------------------


def test_derivation_answers_tier_three_for_the_named_card(tmp_path: Path) -> None:
    found = _advice_on(tmp_path)
    gap = _gap_card_id(found)
    _listing, derivation = _handlers(_Source(found))
    data = _data(derivation({advice_endpoint.ID_PARAMETER: gap}))
    expected = next(a.card for a in found.cards if a.card.id == gap)
    assert frozenset(data) == advice_endpoint.DERIVATION_KEYS
    assert data["id"] == gap
    assert data["rule_id"] == expected.rule_id
    assert data["derivation"] == expected.tier3


def test_derivation_serves_a_hidden_card_too(tmp_path: Path) -> None:
    first = _advice_on(tmp_path)
    gap = _gap_card_id(first)
    Ledger(tmp_path).set_state(advise_fixtures.TOKEN_A, gap, CardState.dismissed())
    MuteStore(tmp_path).mute(power.GAP_RULE.rule_id)
    second = _advice_on(tmp_path)
    _listing, derivation = _handlers(_Source(second))
    response = derivation({advice_endpoint.ID_PARAMETER: gap})
    assert response.http_status == contract.HTTP_OK


def test_derivation_of_an_unknown_card_is_400_and_reflects_nothing(tmp_path: Path) -> None:
    _listing, derivation = _handlers(_Source(_advice_on(tmp_path)))
    response = derivation({advice_endpoint.ID_PARAMETER: UNKNOWN_CARD_ID})
    assert response.http_status == contract.HTTP_BAD_REQUEST
    assert response.payload["reason"] == contract.REASON_INVALID_PARAMETER
    reflected = UNKNOWN_CARD_ID.encode("ascii") in contract.encode(response.payload)
    assert reflected is False


def test_derivation_refuses_an_extra_parameter(tmp_path: Path) -> None:
    found = _advice_on(tmp_path)
    _listing, derivation = _handlers(_Source(found))
    response = derivation({advice_endpoint.ID_PARAMETER: _gap_card_id(found), "x": "1"})
    assert response.http_status == contract.HTTP_BAD_REQUEST
    assert response.payload["reason"] == contract.REASON_UNKNOWN_PARAMETER


def test_derivation_without_an_id_is_400_missing_parameter() -> None:
    _listing, derivation = _handlers(_Source(None))
    response = derivation({})
    assert response.http_status == contract.HTTP_BAD_REQUEST
    assert response.payload["reason"] == contract.REASON_MISSING_PARAMETER


@pytest.mark.parametrize(
    ("with_world", "with_registry", "reason"),
    [
        (False, True, contract.REASON_NO_SAVE),
        (True, False, contract.REASON_NO_GAME_INSTALL),
        (True, True, contract.REASON_ADVICE_STORE_UNREADABLE),
    ],
)
def test_derivation_refuses_as_the_listing_does(
    with_world: bool, with_registry: bool, reason: str
) -> None:
    _listing, derivation = _handlers(
        _Source(None), with_world=with_world, with_registry=with_registry
    )
    response = derivation({advice_endpoint.ID_PARAMETER: UNKNOWN_CARD_ID})
    assert response.http_status == contract.HTTP_UNAVAILABLE
    assert response.payload["reason"] == reason
