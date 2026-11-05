"""The handlers ``/api/advice`` and its derivation serve, over a structural double.

THE CLAIM. ``clockspeed/surface/api/advice.py`` turns an ``Advice`` from the
advisor (``clockspeed/advisor/advise.py``) into the two read bodies:
``/api/advice`` carries every card with tier 1 and tier 2 plus its resolved
ledger state and mute flag; ``/api/advice/<id>/derivation`` carries tier 3 for
one card. Both TRANSCRIBE - the endpoint computes nothing. These arms drive the
handlers directly; ``tests/surface/test_advice_source.py`` drives the real route
table through the real source.

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
no arm reads the repository's own ``data/`` and no arm reads a wall clock. It is
the one structural double of :class:`clockspeed.surface.api.advice.AdviceSource`.

A STATED TARGET (CS-1371). The stub's answers are planted, so these arms grade what the
HANDLER does with them: which door it takes in which order, what it hands each door, and
that it transcribes a :class:`clockspeed.advisor.rules.plan.PlanOutcome` field by field and
rewords nothing. Whether a real request fires a real card is the real table's arm.

Every token, id and number here is invented. No save and no install is read.
"""

from __future__ import annotations

from fractions import Fraction
from types import MappingProxyType
from typing import TYPE_CHECKING, Final

import pytest

from clockspeed.advisor.advise import Advice, advise
from clockspeed.advisor.ledger import CardState, Ledger, MuteStore
from clockspeed.advisor.plans import PlanParameters, PlanRequest
from clockspeed.advisor.rules import power
from clockspeed.advisor.rules.plan import PlanOutcome
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

#: The listing and the derivation, then the state write CS-1269 added - graded
#: in ``tests/surface/test_advice_source.py``.
EXPECTED_ROUTES: Final = 3

#: A card id no advice here carries. Well formed, so only membership refuses it.
UNKNOWN_CARD_ID: Final = "0" * 64


class _Source:
    """An advice source that hands back fixed answers and records what it saw."""

    def __init__(
        self,
        value: Advice | None,
        *,
        parameters: PlanParameters | None = None,
        request: PlanRequest | None = None,
        log: list[str] | None = None,
    ) -> None:
        """Hold the answers.

        Args:
            value: The advice, or None for an unreadable store.
            parameters: What :meth:`plan_parameters` answers, None refusing them.
            request: What :meth:`plan_request` answers, None refusing the target.
            log: Where each call names itself, so an arm can read the order of doors.
        """
        self._value = value
        self._parameters = parameters
        self._request = request
        self.log: list[str] = [] if log is None else log
        self.calls = 0
        self.requests: list[PlanRequest | None] = []
        self.stated: list[tuple[str, str, str]] = []
        self.asked: list[tuple[str, PlanParameters]] = []

    def advice(
        self, world: WorldModel, registry: Registry, *, plan_request: PlanRequest | None = None
    ) -> Advice | None:
        """Answer with the held advice.

        Args:
            world: Ignored beyond counting.
            registry: Ignored beyond counting.
            plan_request: Recorded, so an arm can read what was handed over.

        Returns:
            The held advice, or None.
        """
        del world, registry
        self.calls += 1
        self.requests.append(plan_request)
        self.log.append("advice")
        return self._value

    def plan_parameters(
        self, *, rate: str, direction: str, byproduct_policy: str
    ) -> PlanParameters | None:
        """Answer with the held parameters, recording what was stated.

        Returns:
            The held parameters, or None.
        """
        self.stated.append((rate, direction, byproduct_policy))
        self.log.append("plan_parameters")
        return self._parameters

    def plan_request(
        self, registry: Registry, target: str, parameters: PlanParameters
    ) -> PlanRequest | None:
        """Answer with the held request, recording what was asked.

        Returns:
            The held request, or None.
        """
        del registry
        self.asked.append((target, parameters))
        self.log.append("plan_request")
        return self._request

    def record(self, world: WorldModel, card_id: str, kind: str, until: int | None) -> bool | None:
        """Refuse to record: no arm here drives the state write.

        Returns:
            None, as for an unwritable store.
        """
        del world, card_id, kind, until
        return None


class _LoggedProviders:
    """A world and a registry provider in one, naming each read in the shared log."""

    def __init__(
        self, log: list[str], *, with_world: bool = True, with_registry: bool = True
    ) -> None:
        """Hold what to answer.

        Args:
            log: Where each read names itself.
            with_world: False stands for a machine with no save.
            with_registry: False stands for a machine with no install.
        """
        self._log = log
        self._model = map_fixtures.empty_world() if with_world else None
        self._registry = solve_synthetic.solve_registry() if with_registry else None

    def world(self) -> WorldModel | None:
        """Answer with the held world, or None."""
        self._log.append("world")
        return self._model

    def registry(self) -> Registry | None:
        """Answer with the held registry, or None."""
        self._log.append("registry")
        return self._registry


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


def test_the_module_publishes_the_two_reads_as_gets_and_the_write_as_a_post() -> None:
    published = advice_endpoint.routes(
        map_fixtures._Worlds(None),  # noqa: SLF001
        map_fixtures._Registries(None),  # noqa: SLF001
        _Source(None),
    )
    identities = sorted((route.method, route.template) for route in published)
    count = len(identities)
    assert count == EXPECTED_ROUTES
    assert identities == [
        ("GET", "/api/advice"),
        ("GET", "/api/advice/<id>/derivation"),
        ("POST", "/api/advice/<id>/state"),
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


# ---------------------------------------------------------------------------
# CS-1371: a stated target, each door in its order, over the double
# ---------------------------------------------------------------------------

#: The wire spelling of the four parameters, which the plan panel states. Spelled here and not
#: read from the module under test, so a rename reddens rather than being carried along.
TARGET: Final = "target"
RATE: Final = "rate"
DIRECTION: Final = "direction"
POLICY: Final = "byproduct_policy"

#: The values stated below. The double decides nothing about them, so only their text matters.
STATED: Final[Mapping[str, str]] = MappingProxyType(
    {TARGET: "Desc_Stated_C", RATE: "1/3", DIRECTION: "raw", POLICY: "balanced"}
)

#: What the double answers for a checked set, read by the handler as an opaque value.
PARAMETERS: Final = PlanParameters(
    rate=Fraction(1, 3), direction="raw", byproduct_policy="balanced"
)

#: What the double answers for a listed target.
REQUEST: Final = PlanRequest(
    targets=MappingProxyType({"Desc_Stated_C": Fraction(1, 3)}),
    raw_items=("Desc_Raw_C",),
    byproduct_policy="balanced",
    direction="raw",
)

#: A reason no module owns, so an endpoint that looked one up rather than copying it shows.
PLANTED_REASON: Final = "cs1371 planted reason the surface copies and never rewords"

#: A second planted word, apart from the first, so the two fields cannot be swapped unseen.
PLANTED_REDESIGN_REASON: Final = (
    "cs1380 planted redesign reason the surface copies and never rewords"
)

#: The three route templates, each as the ``(method, template)`` the table keys it by.
LISTING: Final = (advice_endpoint.METHOD_GET, advice_endpoint.ENDPOINT)
DERIVATION: Final = (advice_endpoint.METHOD_GET, advice_endpoint.DERIVATION_ENDPOINT)
STATE: Final = (advice_endpoint.METHOD_POST, advice_endpoint.STATE_ENDPOINT)
ROUTE_KEYS: Final = (LISTING, DERIVATION, STATE)

#: What each route needs beside the four, none of it naming a card the advice lists. A
#: card's own membership is the real table's arm: here the order of doors is what is read.
OWN_PARAMETERS: Final[Mapping[tuple[str, str], Mapping[str, str]]] = MappingProxyType(
    {
        LISTING: MappingProxyType({}),
        DERIVATION: MappingProxyType({advice_endpoint.ID_PARAMETER: UNKNOWN_CARD_ID}),
        STATE: MappingProxyType(
            {
                advice_endpoint.ID_PARAMETER: UNKNOWN_CARD_ID,
                advice_endpoint.STATE_PARAMETER: "accepted",
            }
        ),
    }
)


def _route_id(key: tuple[str, str]) -> str:
    """A test id for one route: its verb and its last path segment."""
    return f"{key[0]}-{key[1].rsplit('/', 1)[-1]}"


def _ask(
    key: tuple[str, str],
    source: _Source,
    providers: _LoggedProviders,
    parameters: Mapping[str, str] = STATED,
) -> contract.Response:
    """Ask one route through the module's own table, with what that route needs."""
    table = {
        (route.method, route.template): route.handler
        for route in advice_endpoint.routes(providers, providers, source)
    }
    return table[key]({**OWN_PARAMETERS[key], **parameters})


def _bare_advice(outcome: PlanOutcome | None = None) -> Advice:
    """An advice holding no card and no trace, and this outcome."""
    return Advice(traces=(), cards=(), new_world=True, plan_outcome=outcome)


def test_the_four_parameters_are_published_as_the_panel_states_them() -> None:
    assert advice_endpoint.TARGET_PARAMETER == TARGET
    assert advice_endpoint.RATE_PARAMETER == RATE
    assert advice_endpoint.DIRECTION_PARAMETER == DIRECTION
    assert advice_endpoint.BYPRODUCT_POLICY_PARAMETER == POLICY
    assert advice_endpoint.PLAN_PARAMETERS == (TARGET, RATE, DIRECTION, POLICY)


def test_the_double_satisfies_the_source_and_store_protocols() -> None:
    double = _Source(None)
    assert isinstance(double, advice_endpoint.AdviceSource)
    assert isinstance(double, advice_endpoint.AdviceStore)


def test_a_source_with_no_plan_door_is_no_advice_source() -> None:
    """The control for the arm above: the protocol does name the two new doors."""

    class _NoPlanDoors:
        def advice(self, world: object, registry: object) -> None:
            del world, registry

    satisfied = isinstance(_NoPlanDoors(), advice_endpoint.AdviceSource)
    assert not satisfied


@pytest.mark.parametrize("key", ROUTE_KEYS, ids=_route_id)
def test_a_stated_request_takes_each_door_in_its_order(key: tuple[str, str]) -> None:
    log: list[str] = []
    source = _Source(_bare_advice(), parameters=PARAMETERS, request=REQUEST, log=log)

    _ask(key, source, _LoggedProviders(log))

    assert log == ["plan_parameters", "world", "registry", "plan_request", "advice"]


@pytest.mark.parametrize("key", ROUTE_KEYS, ids=_route_id)
def test_the_rate_direction_and_policy_are_handed_on_as_the_text_received(
    key: tuple[str, str],
) -> None:
    """No float on the way in: the rate is text until the advisor parses it."""
    log: list[str] = []
    source = _Source(_bare_advice(), parameters=PARAMETERS, request=REQUEST, log=log)

    _ask(key, source, _LoggedProviders(log))

    assert source.stated == [("1/3", "raw", "balanced")]
    exact_str = type(source.stated[0][0]) is str
    assert exact_str


@pytest.mark.parametrize("key", ROUTE_KEYS, ids=_route_id)
def test_what_the_source_built_is_what_the_advice_is_asked_for(key: tuple[str, str]) -> None:
    """The target and the checked parameters go to one door, and that door's answer to the next."""
    log: list[str] = []
    source = _Source(_bare_advice(), parameters=PARAMETERS, request=REQUEST, log=log)

    _ask(key, source, _LoggedProviders(log))

    assert source.asked == [("Desc_Stated_C", PARAMETERS)]
    handed = len(source.requests) == 1 and source.requests[0] is REQUEST
    assert handed


@pytest.mark.parametrize("key", ROUTE_KEYS, ids=_route_id)
def test_a_refused_set_answers_400_and_reads_no_provider(key: tuple[str, str]) -> None:
    log: list[str] = []
    source = _Source(_bare_advice(), parameters=None, request=REQUEST, log=log)

    response = _ask(key, source, _LoggedProviders(log))

    assert response.http_status == contract.HTTP_BAD_REQUEST
    assert response.payload["reason"] == contract.REASON_INVALID_PARAMETER
    assert log == ["plan_parameters"]


@pytest.mark.parametrize("key", ROUTE_KEYS, ids=_route_id)
def test_a_target_off_the_list_answers_400_and_computes_no_advice(key: tuple[str, str]) -> None:
    log: list[str] = []
    source = _Source(_bare_advice(), parameters=PARAMETERS, request=None, log=log)

    response = _ask(key, source, _LoggedProviders(log))

    assert response.http_status == contract.HTTP_BAD_REQUEST
    assert response.payload["reason"] == contract.REASON_INVALID_PARAMETER
    assert log == ["plan_parameters", "world", "registry", "plan_request"]


@pytest.mark.parametrize("key", ROUTE_KEYS, ids=_route_id)
@pytest.mark.parametrize(
    ("with_world", "with_registry", "reason", "reads"),
    [
        (False, True, contract.REASON_NO_SAVE, ["plan_parameters", "world"]),
        (True, False, contract.REASON_NO_GAME_INSTALL, ["plan_parameters", "world", "registry"]),
    ],
    ids=["no-save", "no-install"],
)
def test_a_missing_input_answers_its_503_before_the_membership_test(
    key: tuple[str, str], with_world: bool, with_registry: bool, reason: str, reads: list[str]
) -> None:
    log: list[str] = []
    source = _Source(_bare_advice(), parameters=PARAMETERS, request=None, log=log)
    providers = _LoggedProviders(log, with_world=with_world, with_registry=with_registry)

    response = _ask(key, source, providers)

    assert response.http_status == contract.HTTP_UNAVAILABLE
    assert response.payload["reason"] == reason
    assert log == reads


@pytest.mark.parametrize("key", ROUTE_KEYS, ids=_route_id)
def test_an_unreadable_store_on_a_stated_request_is_the_same_503(key: tuple[str, str]) -> None:
    log: list[str] = []
    source = _Source(None, parameters=PARAMETERS, request=REQUEST, log=log)

    response = _ask(key, source, _LoggedProviders(log))

    assert response.http_status == contract.HTTP_UNAVAILABLE
    assert response.payload["reason"] == contract.REASON_ADVICE_STORE_UNREADABLE


@pytest.mark.parametrize("key", ROUTE_KEYS, ids=_route_id)
def test_an_unknown_name_beside_the_four_refuses_before_any_door(key: tuple[str, str]) -> None:
    planted = "zqxjname1371"
    log: list[str] = []
    source = _Source(_bare_advice(), parameters=PARAMETERS, request=REQUEST, log=log)

    response = _ask(key, source, _LoggedProviders(log), {**STATED, planted: "1"})

    assert response.http_status == contract.HTTP_BAD_REQUEST
    assert response.payload["reason"] == contract.REASON_UNKNOWN_PARAMETER
    assert log == []
    reflected = planted.encode("ascii") in contract.encode(response.payload)
    assert reflected is False


@pytest.mark.parametrize("key", ROUTE_KEYS, ids=_route_id)
@pytest.mark.parametrize("left_out", [TARGET, RATE, DIRECTION, POLICY])
def test_any_of_the_four_stated_without_the_others_is_missing_before_any_door(
    key: tuple[str, str], left_out: str
) -> None:
    log: list[str] = []
    source = _Source(_bare_advice(), parameters=PARAMETERS, request=REQUEST, log=log)
    partial = {name: value for name, value in STATED.items() if name != left_out}

    response = _ask(key, source, _LoggedProviders(log), partial)

    assert response.http_status == contract.HTTP_BAD_REQUEST
    assert response.payload["reason"] == contract.REASON_MISSING_PARAMETER
    assert log == []


def test_a_no_target_listing_asks_for_no_plan_and_carries_no_outcome_key(tmp_path: Path) -> None:
    found = _advice_on(tmp_path)
    source = _Source(found)
    listing, _derivation = _handlers(source)

    data = _data(listing({}))

    assert source.requests == [None]
    assert source.stated == []
    assert source.asked == []
    assert frozenset(data) == advice_endpoint.DATA_KEYS
    named = b"plan_outcome" in contract.encode(listing({}).payload)
    assert named is False


def test_the_stated_keys_are_the_listing_keys_and_the_one_outcome_key() -> None:
    assert advice_endpoint.DATA_KEYS | {"plan_outcome"} == advice_endpoint.STATED_DATA_KEYS
    wire_keys = frozenset({"status", "redesign", "reason", "redesign_reason", "trimmed", "unmade"})
    assert wire_keys == advice_endpoint.PLAN_OUTCOME_KEYS


@pytest.mark.parametrize(
    ("outcome", "wire"),
    [
        (
            PlanOutcome(
                status="ranked",
                reason=None,
                redesign="not-reached",
                redesign_reason=None,
                trimmed=(),
                unmade=None,
            ),
            {"status": "ranked", "redesign": "not-reached", "trimmed": []},
        ),
        (
            PlanOutcome(
                status="no-plan",
                reason=PLANTED_REASON,
                redesign="routed",
                redesign_reason=None,
                trimmed=("R_Dropped", "R_AlsoDropped"),
                unmade=None,
            ),
            {
                "status": "no-plan",
                "redesign": "routed",
                "reason": PLANTED_REASON,
                "trimmed": ["R_Dropped", "R_AlsoDropped"],
            },
        ),
        (
            PlanOutcome(
                status="no-plan",
                reason=PLANTED_REASON,
                redesign="no-route",
                redesign_reason=PLANTED_REDESIGN_REASON,
                trimmed=(),
                unmade=("Desc_Unmade_C",),
            ),
            {
                "status": "no-plan",
                "redesign": "no-route",
                "reason": PLANTED_REASON,
                "redesign_reason": PLANTED_REDESIGN_REASON,
                "trimmed": [],
                "unmade": ["Desc_Unmade_C"],
            },
        ),
        (
            PlanOutcome(
                status="no-plan",
                reason=PLANTED_REASON,
                redesign="no-route",
                redesign_reason=PLANTED_REDESIGN_REASON,
                trimmed=(),
                unmade=(),
            ),
            {
                "status": "no-plan",
                "redesign": "no-route",
                "reason": PLANTED_REASON,
                "redesign_reason": PLANTED_REDESIGN_REASON,
                "trimmed": [],
                "unmade": [],
            },
        ),
        (
            PlanOutcome(
                status="no-plan",
                reason=PLANTED_REASON,
                redesign="route-refused",
                redesign_reason=PLANTED_REDESIGN_REASON,
                trimmed=(),
                unmade=None,
            ),
            {
                "status": "no-plan",
                "redesign": "route-refused",
                "reason": PLANTED_REASON,
                "redesign_reason": PLANTED_REDESIGN_REASON,
                "trimmed": [],
            },
        ),
        (
            PlanOutcome(
                status="request-malformed",
                reason=PLANTED_REASON,
                redesign="not-reached",
                redesign_reason=None,
                trimmed=None,
                unmade=None,
            ),
            {"status": "request-malformed", "redesign": "not-reached", "reason": PLANTED_REASON},
        ),
        (
            PlanOutcome(
                status="solve-refused",
                reason=PLANTED_REASON,
                redesign="not-reached",
                redesign_reason=None,
                trimmed=("R_Dropped",),
                unmade=None,
            ),
            {
                "status": "solve-refused",
                "redesign": "not-reached",
                "reason": PLANTED_REASON,
                "trimmed": ["R_Dropped"],
            },
        ),
        (
            PlanOutcome(
                status="power-not-comparable",
                reason=PLANTED_REASON,
                redesign="not-reached",
                redesign_reason=None,
                trimmed=(),
                unmade=None,
            ),
            {
                "status": "power-not-comparable",
                "redesign": "not-reached",
                "reason": PLANTED_REASON,
                "trimmed": [],
            },
        ),
    ],
    ids=[
        "ranked",
        "no-plan",
        "no-route",
        "no-route-empty",
        "route-refused",
        "malformed",
        "refused",
        "power",
    ],
)
def test_the_outcome_is_transcribed_field_by_field_and_absent_is_never_null(
    outcome: PlanOutcome, wire: Mapping[str, object]
) -> None:
    log: list[str] = []
    source = _Source(_bare_advice(outcome), parameters=PARAMETERS, request=REQUEST, log=log)

    data = _data(_ask(LISTING, source, _LoggedProviders(log)))

    assert frozenset(data) == advice_endpoint.STATED_DATA_KEYS
    served = data["plan_outcome"]
    assert served == wire
    assert isinstance(served, dict)
    outside = sorted(frozenset(served) - advice_endpoint.PLAN_OUTCOME_KEYS)
    assert outside == []


@pytest.mark.parametrize("key", [DERIVATION, STATE], ids=_route_id)
def test_only_the_listing_carries_the_outcome(key: tuple[str, str]) -> None:
    """The control is the arm above: the same advice's outcome is on the listing."""
    outcome = PlanOutcome(
        status="ranked",
        reason=None,
        redesign="not-reached",
        redesign_reason=None,
        trimmed=(),
        unmade=None,
    )
    log: list[str] = []
    source = _Source(_bare_advice(outcome), parameters=PARAMETERS, request=REQUEST, log=log)

    # The double lists no card, so these two answer with the membership refusal.
    response = _ask(key, source, _LoggedProviders(log))

    assert response.http_status == contract.HTTP_BAD_REQUEST
    named = b"plan_outcome" in contract.encode(response.payload)
    assert named is False
