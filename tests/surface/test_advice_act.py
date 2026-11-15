"""CS-1397: ``POST /api/advice/act`` records each served advice act, once.

THE CLAIM. A served world records what the run implies exactly once per advice act. One
admitted ``POST /api/advice/act`` is one act: it calls the recording door
(``clockspeed.advisor.advise.advise_world_and_record``) once, through
``clockspeed.surface.providers.StoreAdviceSource.act``, and the per-world ledger is the only
store it writes. A refused request records nothing. No read path writes either store.

EVERY ARM DRIVES THE SURFACE. Each one asks the real route table
(``clockspeed.surface.api.routes.build_routes``) over the real source, the real advisor and
the real ledger in a temporary directory, never ``advise_and_record`` itself. The one arm that
needs a listener (the same-origin refusal) goes over TLS through the server.

THE FIXTURE. One LARGE card (``plan.adopt``, stated) beside one QUICK card
(``power.draw_incomplete``): the quick card leads the showing order, so the large card is
passed over by every act and its count is what the aging guard reads. The first act records
both cards at zero, so the threshold counts FURTHER acts (the session 157 adjudication).

Every token, id and number is invented. No save and no install is read.
"""

from __future__ import annotations

from dataclasses import replace
from types import MappingProxyType
from typing import TYPE_CHECKING, Final

import pytest

from clockspeed.advisor import ranking
from clockspeed.advisor.ledger import (
    LEDGER_FILENAME,
    MUTES_FILENAME,
    Ledger,
    StoreWriteError,
)
from clockspeed.advisor.rules import power
from clockspeed.surface import server
from clockspeed.surface.api import advice as advice_endpoint
from clockspeed.surface.api import contract, health, routes
from clockspeed.surface.providers import StoreAdviceSource
from tests.advisor import test_world_advice as world_fixtures
from tests.audit import test_balance as balance_fixtures
from tests.surface import test_advice_source as source_fixtures
from tests.surface import test_map as map_fixtures

# The listener fixtures are the server suite's own; importing them registers them here.
from tests.surface.test_server import cert_pair, cfg, request  # noqa: F401

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    from clockspeed.data.registry import Registry
    from clockspeed.save.world import WorldModel
    from clockspeed.surface import config

#: The instant the injected clock answers.
NOW: Final = 1000

#: The rule ids of the two cards the fixture holds.
LARGE_RULE: Final = "plan.adopt"
QUICK_RULE: Final = power.GAP_RULE.rule_id

#: The proof the dashboard sends.
PROOF: Final = {"X-Clockspeed-Request": "1"}

#: Two acts, one reconcile each.
TWO_ACTS: Final = 2

#: A parameter name no route takes, distinctive so a reflection would show.
UNKNOWN_NAME: Final = "zqxjname1397"

#: A rate value no route accepts, distinctive so a reflection would show.
BAD_RATE: Final = "zqxjrate1397"

#: The ledger and mute files, the whole of the advisor's persistence.
STORE_FILES: Final = (LEDGER_FILENAME, MUTES_FILENAME)


def _large_and_quick() -> tuple[WorldModel, Registry]:
    """A world firing one quick card of its own and, when a plan is stated, one large card."""
    base, plan_registry = source_fixtures._ascent()  # noqa: SLF001
    model = replace(world_fixtures.gap_world(), unlocks=base.unlocks)
    registry = replace(
        plan_registry,
        buildings=MappingProxyType(
            {**plan_registry.buildings, **dict(balance_fixtures.whole_world_registry())}
        ),
    )
    return model, registry


def _stated() -> dict[str, str]:
    """The four of a stated plan that ranks in the fixture."""
    return source_fixtures._stated()  # noqa: SLF001


def _source(directory: Path) -> StoreAdviceSource:
    return StoreAdviceSource(directory, clock=lambda: NOW)


def _table(
    directory: Path,
    model: WorldModel | None = None,
    registry: Registry | None = None,
    *,
    held: tuple[WorldModel | None, Registry | None] | None = None,
) -> Mapping[tuple[str, str], contract.Handler]:
    """The real route table, and the 405 boundary, over a real source in ``directory``."""
    if held is None:
        built_model, built_registry = _large_and_quick()
        held = (
            built_model if model is None else model,
            built_registry if registry is None else registry,
        )
    built = (
        *routes.build_routes(
            map_fixtures._Worlds(held[0]),  # noqa: SLF001
            map_fixtures._Registries(held[1]),  # noqa: SLF001
            _source(directory),
        ),
        *routes.METHOD_BOUNDARY_ROUTES,
    )
    return {(route.method, route.template): route.handler for route in built}


def _act(
    table: Mapping[tuple[str, str], contract.Handler], statement: Mapping[str, str] | None = None
) -> contract.Response:
    return table["POST", advice_endpoint.ACT_ENDPOINT]({} if statement is None else statement)


def _data(response: contract.Response) -> Mapping[str, object]:
    assert response.http_status == contract.HTTP_OK
    problems = len(contract.contract_problems(response))
    assert problems == 0
    data = response.payload["data"]
    assert isinstance(data, dict)
    return data


def _listing(
    table: Mapping[tuple[str, str], contract.Handler], statement: Mapping[str, str] | None = None
) -> Mapping[str, object]:
    return _data(table["GET", advice_endpoint.ENDPOINT]({} if statement is None else statement))


def _order(data: Mapping[str, object]) -> list[str]:
    """The rule ids of one listing body, in the order it lists them."""
    cards = data["cards"]
    assert isinstance(cards, list)
    return [str(card["rule_id"]) for card in cards]


def _card_ids(directory: Path) -> dict[str, str]:
    """Rule id to card id for the stated fixture, read through the read-only source."""
    model, registry = _large_and_quick()
    source = _source(directory)
    parameters = source.plan_parameters(rate="10", direction="raw", byproduct_policy="balanced")
    assert parameters is not None
    request_ = source.plan_request(registry, source_fixtures.SOLVE_RELIC_ITEM, parameters)
    found = source.advice(model, registry, plan_request=request_)
    assert found is not None
    return {advised.card.rule_id: advised.card.id for advised in found.cards}


def _token() -> str:
    return _large_and_quick()[0].token


def _counts(directory: Path) -> dict[str, int]:
    """The deferral counts a FRESH ledger over the directory reads back from disk."""
    return dict(Ledger(directory).deferrals(_token()))


def _snapshot(directory: Path) -> dict[str, bytes | None]:
    """Both store files' bytes, None for one that does not exist."""
    out: dict[str, bytes | None] = {}
    for name in STORE_FILES:
        path = directory / name
        out[name] = path.read_bytes() if path.is_file() else None
    return out


def _unchanged(before: dict[str, bytes | None], directory: Path) -> bool:
    return _snapshot(directory) == before


class _Reconciles:
    """Counts every call into the ledger's one write path, passing each straight on."""

    def __init__(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self.calls = 0
        real = Ledger.reconcile
        counter = self

        def counted(self_: Ledger, *args: object, **kwargs: object) -> object:
            counter.calls += 1
            return real(self_, *args, **kwargs)  # type: ignore[arg-type]

        monkeypatch.setattr(Ledger, "reconcile", counted)


# ---------------------------------------------------------------------------
# One admitted POST is one act
# ---------------------------------------------------------------------------


def test_one_act_raises_a_passed_over_cards_count_by_exactly_one(tmp_path: Path) -> None:
    table = _table(tmp_path)
    ids = _card_ids(tmp_path)
    large = ids[LARGE_RULE]

    _data(_act(table, _stated()))
    first = _counts(tmp_path).get(large, 0)
    _data(_act(table, _stated()))
    second = _counts(tmp_path).get(large, 0)

    assert first == 0
    assert second == 1


def test_one_admitted_post_calls_the_recording_door_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    spy = _Reconciles(monkeypatch)
    table = _table(tmp_path)

    _data(_act(table, _stated()))
    after_one = spy.calls
    _data(_act(table, _stated()))
    after_two = spy.calls

    assert after_one == 1
    assert after_two == TWO_ACTS


def test_a_read_never_calls_the_recording_door(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    spy = _Reconciles(monkeypatch)
    table = _table(tmp_path)
    ids = _card_ids(tmp_path)

    _listing(table)
    _listing(table, _stated())
    table["GET", advice_endpoint.DERIVATION_ENDPOINT](
        {advice_endpoint.ID_PARAMETER: ids[LARGE_RULE], **_stated()}
    )
    table["GET", advice_endpoint.ACT_ENDPOINT]({})

    assert spy.calls == 0


def test_the_response_is_the_listing_body_under_the_same_statement(tmp_path: Path) -> None:
    table = _table(tmp_path)
    _data(_act(table, _stated()))

    acted = _data(_act(table, _stated()))
    read = _listing(table, _stated())

    same = acted == read
    assert same
    assert frozenset(acted) == advice_endpoint.STATED_DATA_KEYS


def test_an_unstated_act_answers_the_unstated_listing_keys(tmp_path: Path) -> None:
    acted = _data(_act(_table(tmp_path)))

    assert frozenset(acted) == advice_endpoint.DATA_KEYS
    assert _order(acted) == [QUICK_RULE]


# ---------------------------------------------------------------------------
# The threshold, through served acts only
# ---------------------------------------------------------------------------


def test_a_first_recording_act_plus_the_threshold_of_further_acts_reaches_it(
    tmp_path: Path,
) -> None:
    table = _table(tmp_path)
    large = _card_ids(tmp_path)[LARGE_RULE]

    _data(_act(table, _stated()))
    for _ in range(ranking.AGING_EVALUATIONS):
        _data(_act(table, _stated()))

    reached = _counts(tmp_path)[large] >= ranking.AGING_EVALUATIONS
    assert reached


def test_one_further_act_fewer_does_not_reach_the_threshold(tmp_path: Path) -> None:
    table = _table(tmp_path)
    large = _card_ids(tmp_path)[LARGE_RULE]

    _data(_act(table, _stated()))
    for _ in range(ranking.AGING_EVALUATIONS - 1):
        _data(_act(table, _stated()))

    short = _counts(tmp_path)[large]
    assert short == ranking.AGING_EVALUATIONS - 1


def test_the_first_act_alone_does_not_count_toward_the_threshold(tmp_path: Path) -> None:
    table = _table(tmp_path)
    large = _card_ids(tmp_path)[LARGE_RULE]

    _data(_act(table, _stated()))

    recorded = large in _counts(tmp_path)
    assert not recorded


# ---------------------------------------------------------------------------
# No read-only path writes either store
# ---------------------------------------------------------------------------


def _seeded(
    tmp_path: Path,
) -> tuple[Mapping[tuple[str, str], contract.Handler], dict[str, bytes | None]]:
    """A table over a store two acts have written, and that store's bytes."""
    table = _table(tmp_path)
    _data(_act(table, _stated()))
    _data(_act(table, _stated()))
    return table, _snapshot(tmp_path)


def test_a_get_listing_leaves_both_stores_byte_identical(tmp_path: Path) -> None:
    table, before = _seeded(tmp_path)

    _listing(table)
    _listing(table, _stated())

    assert _unchanged(before, tmp_path)


def test_a_get_derivation_leaves_both_stores_byte_identical(tmp_path: Path) -> None:
    table, before = _seeded(tmp_path)
    ids = _card_ids(tmp_path)

    response = table["GET", advice_endpoint.DERIVATION_ENDPOINT](
        {advice_endpoint.ID_PARAMETER: ids[LARGE_RULE], **_stated()}
    )

    assert response.http_status == contract.HTTP_OK
    assert _unchanged(before, tmp_path)


def test_a_get_on_the_act_template_is_405_and_leaves_both_stores_byte_identical(
    tmp_path: Path,
) -> None:
    table, before = _seeded(tmp_path)

    response = table["GET", advice_endpoint.ACT_ENDPOINT]({})

    assert response.http_status == contract.HTTP_METHOD_NOT_ALLOWED
    assert response.payload["reason"] == contract.REASON_METHOD_NOT_ALLOWED
    assert _unchanged(before, tmp_path)


def test_the_reads_create_no_file_on_a_never_seen_token(tmp_path: Path) -> None:
    table = _table(tmp_path)
    ids = _card_ids(tmp_path)

    _listing(table)
    _listing(table, _stated())
    table["GET", advice_endpoint.DERIVATION_ENDPOINT](
        {advice_endpoint.ID_PARAMETER: ids[LARGE_RULE], **_stated()}
    )
    table["GET", advice_endpoint.ACT_ENDPOINT]({})

    created = len(list(tmp_path.iterdir()))
    assert created == 0


# ---------------------------------------------------------------------------
# A never-seen world is a new world, not a refusal (CLAUDE.md section 7)
# ---------------------------------------------------------------------------


def test_a_never_seen_world_token_is_a_new_world_not_a_refusal(tmp_path: Path) -> None:
    table = _table(tmp_path)

    first = _data(_act(table, _stated()))
    second = _data(_act(table, _stated()))

    assert first["new_world"] is True
    assert second["new_world"] is False
    assert (tmp_path / LEDGER_FILENAME).is_file()


# ---------------------------------------------------------------------------
# A stated act and then an unstated one
# ---------------------------------------------------------------------------


def test_an_unstated_act_after_a_stated_one_leaves_the_plan_card_not_completed(
    tmp_path: Path,
) -> None:
    table = _table(tmp_path)
    large = _card_ids(tmp_path)[LARGE_RULE]
    model = _large_and_quick()[0]

    _data(_act(table, _stated()))
    _data(_act(table))

    kind = Ledger(tmp_path).state(model.token, large, now=NOW).kind
    assert kind != "completed"
    relisted = _listing(table, _stated())
    cards = relisted["cards"]
    assert isinstance(cards, list)
    states = {str(card["rule_id"]): str(card["state"]) for card in cards}
    assert states[LARGE_RULE] == "new"


# ---------------------------------------------------------------------------
# Refusals record nothing
# ---------------------------------------------------------------------------


def _assert_refused(response: contract.Response, status: int, reason: str, *planted: str) -> None:
    assert response.http_status == status
    assert response.payload["reason"] == reason
    problems = len(contract.contract_problems(response))
    assert problems == 0
    body = contract.encode(response.payload)
    reflected = sum(1 for value in planted if value.encode("ascii") in body)
    assert reflected == 0


def test_an_unknown_parameter_is_400_before_any_provider_and_records_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    spy = _Reconciles(monkeypatch)
    model, registry = _large_and_quick()
    table, counted, source = source_fixtures._counted_table(tmp_path, model, registry)  # noqa: SLF001

    response = table["POST", advice_endpoint.ACT_ENDPOINT]({UNKNOWN_NAME: "1"})

    _assert_refused(
        response, contract.HTTP_BAD_REQUEST, contract.REASON_UNKNOWN_PARAMETER, UNKNOWN_NAME
    )
    assert counted.reads == 0
    assert source.computed == 0
    assert spy.calls == 0
    created = len(list(tmp_path.iterdir()))
    assert created == 0


@pytest.mark.parametrize("names", source_fixtures.PARTIAL_SETS)
def test_a_partial_statement_is_400_missing_parameter_and_records_nothing(
    tmp_path: Path, names: tuple[str, ...]
) -> None:
    full = _stated()
    model, registry = _large_and_quick()
    table, counted, _unused = source_fixtures._counted_table(tmp_path, model, registry)  # noqa: SLF001

    response = table["POST", advice_endpoint.ACT_ENDPOINT]({name: full[name] for name in names})

    _assert_refused(response, contract.HTTP_BAD_REQUEST, contract.REASON_MISSING_PARAMETER)
    assert counted.reads == 0
    created = len(list(tmp_path.iterdir()))
    assert created == 0


def test_an_invalid_rate_is_400_before_any_provider_and_reflects_nothing(tmp_path: Path) -> None:
    model, registry = _large_and_quick()
    table, counted, _unused = source_fixtures._counted_table(tmp_path, model, registry)  # noqa: SLF001

    response = table["POST", advice_endpoint.ACT_ENDPOINT]({**_stated(), "rate": BAD_RATE})

    _assert_refused(
        response, contract.HTTP_BAD_REQUEST, contract.REASON_INVALID_PARAMETER, BAD_RATE
    )
    assert counted.reads == 0
    created = len(list(tmp_path.iterdir()))
    assert created == 0


def test_a_target_off_the_list_is_400_and_records_nothing(tmp_path: Path) -> None:
    table = _table(tmp_path)

    response = _act(table, {**_stated(), "target": UNKNOWN_NAME})

    _assert_refused(
        response, contract.HTTP_BAD_REQUEST, contract.REASON_INVALID_PARAMETER, UNKNOWN_NAME
    )
    created = len(list(tmp_path.iterdir()))
    assert created == 0


def test_no_save_is_503_and_records_nothing(tmp_path: Path) -> None:
    table = _table(tmp_path, held=(None, _large_and_quick()[1]))

    response = _act(table, _stated())

    _assert_refused(response, contract.HTTP_UNAVAILABLE, contract.REASON_NO_SAVE)
    created = len(list(tmp_path.iterdir()))
    assert created == 0


def test_no_game_install_is_503_and_records_nothing(tmp_path: Path) -> None:
    table = _table(tmp_path, held=(_large_and_quick()[0], None))

    response = _act(table, _stated())

    _assert_refused(response, contract.HTTP_UNAVAILABLE, contract.REASON_NO_GAME_INSTALL)
    created = len(list(tmp_path.iterdir()))
    assert created == 0


@pytest.mark.parametrize("name", STORE_FILES)
def test_a_corrupt_store_is_503_unreadable_and_both_stores_stay_byte_identical(
    tmp_path: Path, name: str
) -> None:
    table = _table(tmp_path)
    (tmp_path / name).write_bytes(b"{not json")
    before = _snapshot(tmp_path)

    response = _act(table, _stated())

    _assert_refused(response, contract.HTTP_UNAVAILABLE, contract.REASON_ADVICE_STORE_UNREADABLE)
    assert _unchanged(before, tmp_path)


def test_a_token_that_is_not_a_world_token_is_503_unreadable_and_records_nothing(
    tmp_path: Path,
) -> None:
    model, registry = _large_and_quick()
    table = _table(tmp_path, held=(replace(model, token=""), registry))

    response = _act(table, _stated())

    _assert_refused(response, contract.HTTP_UNAVAILABLE, contract.REASON_ADVICE_STORE_UNREADABLE)
    created = len(list(tmp_path.iterdir()))
    assert created == 0


def test_a_store_that_cannot_be_written_is_503_unwritable_and_changes_no_byte(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    table = _table(tmp_path)
    _data(_act(table, _stated()))
    before = _snapshot(tmp_path)

    def refuse(*_args: object, **_kwargs: object) -> object:
        raise StoreWriteError("synthetic")

    monkeypatch.setattr(Ledger, "reconcile", refuse)
    response = _act(table, _stated())

    _assert_refused(response, contract.HTTP_UNAVAILABLE, contract.REASON_ADVICE_STORE_UNWRITABLE)
    assert _unchanged(before, tmp_path)


# ---------------------------------------------------------------------------
# The route table
# ---------------------------------------------------------------------------


def test_the_act_template_follows_the_state_template_in_the_published_order() -> None:
    templates = health.ENDPOINT_TEMPLATES
    after_state = templates[templates.index(advice_endpoint.STATE_ENDPOINT) + 1]
    assert after_state == advice_endpoint.ACT_ENDPOINT


def test_the_act_route_is_a_mutating_post_and_backed() -> None:
    mine = [route for route in routes.ROUTES if route.template == advice_endpoint.ACT_ENDPOINT]
    count = len(mine)
    assert count == 1
    assert mine[0].method == advice_endpoint.METHOD_POST
    assert mine[0].mutates is True
    assert routes.ENDPOINT_STATUS[advice_endpoint.ACT_ENDPOINT] == health.LIVE


def test_the_server_guards_the_act_route() -> None:
    guarded = server.mutating_routes(routes.SERVING_ROUTES)
    assert (advice_endpoint.METHOD_POST, advice_endpoint.ACT_ENDPOINT) in guarded


def test_the_act_door_words_are_the_providers_words() -> None:
    assert advice_endpoint.ACT_UNREADABLE == "unreadable"
    assert advice_endpoint.ACT_UNWRITABLE == "unwritable"


# ---------------------------------------------------------------------------
# The same-origin refusal, over a real listener
# ---------------------------------------------------------------------------


def _served_routes(directory: Path) -> tuple[contract.Route, ...]:
    model, registry = _large_and_quick()
    return (
        *routes.build_routes(
            map_fixtures._Worlds(model),  # noqa: SLF001
            map_fixtures._Registries(registry),  # noqa: SLF001
            _source(directory),
        ),
        *routes.METHOD_BOUNDARY_ROUTES,
    )


def _post_path() -> str:
    query = "&".join(f"{name}={value}" for name, value in _stated().items())
    return f"{advice_endpoint.ACT_ENDPOINT}?{query}"


@pytest.mark.parametrize(
    "headers",
    [
        {},
        {"X-Clockspeed-Request": "0"},
        {"Content-Type": "application/x-www-form-urlencoded"},
        {"X-Clockspeed-Request": "1", "Sec-Fetch-Site": "cross-site"},
    ],
)
def test_a_post_without_same_origin_proof_is_403_and_writes_nothing(
    cfg: config.ServerConfig,  # noqa: F811
    cert_pair: tuple[Path, Path],  # noqa: F811
    tmp_path: Path,
    headers: Mapping[str, str],
) -> None:
    cert, _key = cert_pair
    store = tmp_path / "store"
    store.mkdir()
    before = _snapshot(store)
    with server.serve(cfg, _served_routes(store)) as running:
        status, _headers, body = request(
            running.server_address[1], _post_path(), cert, method="POST", headers=headers
        )
    assert status == contract.HTTP_FORBIDDEN
    assert contract.REASON_CROSS_ORIGIN_REFUSED in body.decode("ascii")
    assert _unchanged(before, store)
    created = len(list(store.iterdir()))
    assert created == 0


def test_a_post_with_the_proof_records_one_act_over_a_real_listener(
    cfg: config.ServerConfig,  # noqa: F811
    cert_pair: tuple[Path, Path],  # noqa: F811
    tmp_path: Path,
) -> None:
    cert, _key = cert_pair
    store = tmp_path / "store"
    store.mkdir()
    with server.serve(cfg, _served_routes(store)) as running:
        status, _headers, _body = request(
            running.server_address[1],
            _post_path(),
            cert,
            method="POST",
            headers={**PROOF, "Sec-Fetch-Site": "same-origin"},
        )
    assert status == contract.HTTP_OK
    assert (store / LEDGER_FILENAME).is_file()
