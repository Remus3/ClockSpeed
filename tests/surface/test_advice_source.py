"""CS-1270: the advice routes are live, through a store-reading provider source.

THE CLAIM. :class:`clockspeed.surface.providers.StoreAdviceSource` satisfies
``advice.AdviceSource``: it hands one world and one registry to the advisor's
own :func:`clockspeed.advisor.advise.advise_world`, reading the per-world
ledger and the global mutes from one store directory with an INJECTED clock,
and answers None when either store is corrupt or unreadable. It writes no
store - a GET never records anything. ``routes.build_routes`` binds it, so
``GET /api/advice`` and ``GET /api/advice/<id>/derivation`` answer 200 over the
real route table, and ``pending`` no longer publishes either template.

THE SEAM. No surface module on the advice path imports ``clockspeed.audit``:
composing the audit models is the advisor's job, which is exactly what
``advise_world`` exists to own. Asserted on the AST of every shipped surface
module, with a planted-import control so the detector is shown to fire. The
importer set is pinned EXACTLY rather than asserted empty: ``api/map.py`` has
imported the audit placement and inventory models since CS-977, before CS-1270
was filed, so CS-1270's acceptance clause "no ``clockspeed/surface`` module
imports ``clockspeed.audit``" is false on the base this item started from and
is recorded as awaiting a ruling rather than met. A new importer reddens here.

Every token, id and number here is invented. No save and no install is read;
every store lives in a temporary directory.
"""

from __future__ import annotations

import ast
from dataclasses import replace
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING, Final

import pytest

from clockspeed.advisor.ledger import (
    LEDGER_FILENAME,
    MUTES_FILENAME,
    CardState,
    Ledger,
    MuteStore,
)
from clockspeed.advisor.rules import power
from clockspeed.save.world import WorldProperties
from clockspeed.surface import server
from clockspeed.surface.api import advice as advice_endpoint
from clockspeed.surface.api import contract, health, pending, routes
from clockspeed.surface.providers import StoreAdviceSource
from tests.advisor import test_world_advice as world_fixtures
from tests.audit import test_balance as balance_fixtures
from tests.surface import test_map as map_fixtures

if TYPE_CHECKING:
    from collections.abc import Mapping

    from clockspeed.advisor.advise import Advice
    from clockspeed.save.world import WorldModel

#: The instant the injected clock answers.
NOW: Final = 1000

#: How far past :data:`NOW` a planted snooze runs.
SNOOZE_SPAN: Final = 50

#: The shipped surface package, read as source.
SURFACE_ROOT: Final = Path(__file__).resolve().parents[2] / "clockspeed" / "surface"

#: The layer no advice-path surface module may import.
AUDIT_PACKAGE: Final = "clockspeed.audit"

#: The one surface module importing the audit layer, since CS-977 - it
#: serializes the placement and inventory models. Pinned, not tolerated.
AUDIT_IMPORTERS: Final = frozenset({"api/map.py"})

#: The surface modules CS-1270 wrote or rewired.
ADVICE_PATH: Final = frozenset({"api/advice.py", "api/routes.py", "providers.py"})


def _source(directory: Path, now: int = NOW) -> StoreAdviceSource:
    return StoreAdviceSource(directory, clock=lambda: now)


def _advice(directory: Path, now: int = NOW) -> Advice:
    found = _source(directory, now).advice(
        world_fixtures.gap_world(), world_fixtures.synthetic_registry()
    )
    assert found is not None
    return found


def _gap_id(found: Advice) -> str:
    ids = [a.card.id for a in found.cards if a.card.rule_id == power.GAP_RULE.rule_id]
    count = len(ids)
    assert count == 1
    return ids[0]


def _table(
    directory: Path, world: WorldModel | None = None
) -> Mapping[tuple[str, str], contract.Handler]:
    built = routes.build_routes(
        map_fixtures._Worlds(world_fixtures.gap_world() if world is None else world),  # noqa: SLF001
        map_fixtures._Registries(world_fixtures.synthetic_registry()),  # noqa: SLF001
        _source(directory),
    )
    return {(route.method, route.template): route.handler for route in built}


def _data(response: contract.Response) -> Mapping[str, object]:
    assert response.http_status == contract.HTTP_OK
    problems = contract.contract_problems(response)
    count = len(problems)
    assert count == 0, problems
    data = response.payload["data"]
    assert isinstance(data, dict)
    return data


# ---------------------------------------------------------------------------
# The source
# ---------------------------------------------------------------------------


def test_the_source_satisfies_the_advice_source_protocol(tmp_path: Path) -> None:
    assert isinstance(_source(tmp_path), advice_endpoint.AdviceSource)


def test_the_source_runs_the_advisor_over_the_world_it_is_handed(tmp_path: Path) -> None:
    found = _advice(tmp_path)

    assert found.new_world is True
    fired = [a.card.rule_id for a in found.cards]
    assert power.GAP_RULE.rule_id in fired


def test_the_source_reads_the_ledger(tmp_path: Path) -> None:
    gap_id = _gap_id(_advice(tmp_path))
    Ledger(tmp_path).set_state(world_fixtures.gap_world().token, gap_id, CardState.pinned())

    found = _advice(tmp_path)

    state = next(a.state.kind for a in found.cards if a.card.id == gap_id)
    assert state == "pinned"
    assert found.new_world is False


def test_the_source_reads_the_mutes(tmp_path: Path) -> None:
    MuteStore(tmp_path).mute(power.GAP_RULE.rule_id)

    found = _advice(tmp_path)

    muted = next(a.muted for a in found.cards if a.card.rule_id == power.GAP_RULE.rule_id)
    assert muted is True


def test_the_source_resolves_a_snooze_against_its_injected_clock(tmp_path: Path) -> None:
    gap_id = _gap_id(_advice(tmp_path))
    Ledger(tmp_path).set_state(
        world_fixtures.gap_world().token, gap_id, CardState.snoozed(NOW + SNOOZE_SPAN)
    )

    before = _advice(tmp_path, NOW)
    after = _advice(tmp_path, NOW + SNOOZE_SPAN)

    assert next(a.state.kind for a in before.cards if a.card.id == gap_id) == "snoozed"
    assert next(a.state.kind for a in after.cards if a.card.id == gap_id) == "new"


def test_the_source_answers_none_over_a_corrupt_ledger(tmp_path: Path) -> None:
    corrupt = b"{not json"
    (tmp_path / LEDGER_FILENAME).write_bytes(corrupt)

    found = _source(tmp_path).advice(
        world_fixtures.gap_world(), world_fixtures.synthetic_registry()
    )

    assert found is None
    unchanged = (tmp_path / LEDGER_FILENAME).read_bytes() == corrupt
    assert unchanged


def test_the_source_answers_none_over_corrupt_mutes(tmp_path: Path) -> None:
    corrupt = b'{"schema_version": 1, "rules": "not a list"}'
    (tmp_path / MUTES_FILENAME).write_bytes(corrupt)

    found = _source(tmp_path).advice(
        world_fixtures.gap_world(), world_fixtures.synthetic_registry()
    )

    assert found is None
    unchanged = (tmp_path / MUTES_FILENAME).read_bytes() == corrupt
    assert unchanged


def test_the_source_writes_no_store(tmp_path: Path) -> None:
    _advice(tmp_path)

    created = len(list(tmp_path.iterdir()))
    assert created == 0


def test_the_source_reads_no_clock_until_asked(tmp_path: Path) -> None:
    reads: list[int] = []

    def clock() -> int:
        reads.append(NOW)
        return NOW

    source = StoreAdviceSource(tmp_path, clock=clock)
    before = len(reads)
    source.advice(world_fixtures.gap_world(), world_fixtures.synthetic_registry())
    after = len(reads)

    assert before == 0
    assert after == 1


# ---------------------------------------------------------------------------
# The seam
# ---------------------------------------------------------------------------


def _audit_imports(tree: ast.AST) -> int:
    """Count the import statements in one module that name the audit package."""
    found = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found += sum(
                1
                for alias in node.names
                if alias.name == AUDIT_PACKAGE or alias.name.startswith(AUDIT_PACKAGE + ".")
            )
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            module = node.module
            if module == AUDIT_PACKAGE or module.startswith(AUDIT_PACKAGE + "."):
                found += 1
            elif module == "clockspeed":
                found += sum(1 for alias in node.names if alias.name == "audit")
    return found


def test_the_audit_import_detector_fires_on_each_planted_form() -> None:
    planted = (
        "import clockspeed.audit.balance",
        "from clockspeed.audit.machines import machines_of",
        "from clockspeed import audit",
        "from clockspeed.audit import placement",
    )
    for source in planted:
        hits = _audit_imports(ast.parse(source))
        assert hits == 1, source


def test_only_the_map_endpoint_imports_the_audit_layer() -> None:
    modules = sorted(SURFACE_ROOT.rglob("*.py"))
    count = len(modules)
    assert count > 0
    importers = frozenset(
        path.relative_to(SURFACE_ROOT).as_posix()
        for path in modules
        if _audit_imports(ast.parse(path.read_bytes().decode("ascii"))) > 0
    )
    assert importers == AUDIT_IMPORTERS
    overlap = len(importers & ADVICE_PATH)
    assert overlap == 0


# ---------------------------------------------------------------------------
# The real route table
# ---------------------------------------------------------------------------


def test_the_listing_answers_200_over_the_real_route_table(tmp_path: Path) -> None:
    table = _table(tmp_path)

    data = _data(table["GET", advice_endpoint.ENDPOINT]({}))

    assert frozenset(data) == advice_endpoint.DATA_KEYS
    cards = data["cards"]
    assert isinstance(cards, list)
    rule_ids = [card["rule_id"] for card in cards]
    assert power.GAP_RULE.rule_id in rule_ids


def test_the_derivation_answers_200_with_tier_three_over_the_real_route_table(
    tmp_path: Path,
) -> None:
    found = _advice(tmp_path)
    gap = next(a.card for a in found.cards if a.card.rule_id == power.GAP_RULE.rule_id)
    table = _table(tmp_path)

    data = _data(
        table["GET", advice_endpoint.DERIVATION_ENDPOINT]({advice_endpoint.ID_PARAMETER: gap.id})
    )

    assert frozenset(data) == advice_endpoint.DERIVATION_KEYS
    assert data["derivation"] == gap.tier3


def test_the_real_route_table_writes_no_store(tmp_path: Path) -> None:
    table = _table(tmp_path)
    table["GET", advice_endpoint.ENDPOINT]({})

    created = len(list(tmp_path.iterdir()))
    assert created == 0


def test_pending_publishes_neither_read_template() -> None:
    unbacked = {template for _method, template in pending.UNBACKED}

    assert advice_endpoint.ENDPOINT not in unbacked
    assert advice_endpoint.DERIVATION_ENDPOINT not in unbacked
    assert advice_endpoint.ENDPOINT not in pending.BLOCKERS
    assert advice_endpoint.DERIVATION_ENDPOINT not in pending.BLOCKERS
    assert "CS-1270" not in contract.OPEN_BLOCKERS


def test_health_reports_both_read_templates_live() -> None:
    assert routes.ENDPOINT_STATUS[advice_endpoint.ENDPOINT] == health.LIVE
    assert routes.ENDPOINT_STATUS[advice_endpoint.DERIVATION_ENDPOINT] == health.LIVE


def test_the_state_route_left_pending_when_cs_1269_closed() -> None:
    assert advice_endpoint.STATE_ENDPOINT not in pending.BLOCKERS


# ---------------------------------------------------------------------------
# CS-1269: POST /api/advice/<id>/state records a card state in the ledger
#
# CS-1269: ``POST /api/advice/<id>/state`` records a card state in the ledger.
#
# THE CLAIM. The state route is BACKED: ``clockspeed/surface/api/advice.py``
# publishes it with the two reads, and a POST naming a card the current advice
# lists records ``accepted``, ``dismissed``, ``pinned``, ``new`` (a restore) or a
# ``snoozed`` state with a future ``until`` through
# ``clockspeed/surface/providers.py::StoreAdviceSource.record`` - which hands the
# write to the advisor's own ``Ledger``. Every recorded state is READ BACK FROM
# DISK through a fresh ``Ledger`` over the same directory, never from the answer.
#
# THE REFUSALS. An unknown card, an unknown state kind, a missing state, an
# ``until`` on a kind that is not a snooze, a snooze with no ``until``, a
# non-decimal ``until`` and a snooze that does not end after now are each 400,
# reflect nothing, and leave the store directory empty. A GET on the template is
# 405 through the method-boundary route. ``pending`` no longer publishes the
# template and ``contract.OPEN_BLOCKERS`` no longer carries CS-1269.
#
# THE CROSS-ORIGIN REFUSAL IS THE SERVER'S, and is graded over a real listener in
# ``tests/surface/test_server.py`` - a handler sees query parameters only and
# cannot tell a form post from the dashboard.
#
# Every token, id and number here is invented. No save and no install is read;
# every store lives in a temporary directory, and the clock is injected.
# ---------------------------------------------------------------------------

#: A card id no advice here carries. Token-shaped, so a reflection would show.
UNKNOWN_CARD_ID: Final = "zqxjcard1269unknown"

#: A state kind the route does not record. Distinctive, so a reflection would show.
UNKNOWN_KIND: Final = "zqxjkind1269"

#: The kinds recorded without an ``until``.
PLAIN_KINDS: Final = ("accepted", "dismissed", "pinned")


def _state_source(directory: Path) -> StoreAdviceSource:
    return StoreAdviceSource(directory, clock=lambda: NOW)


def _state_table(directory: Path) -> Mapping[tuple[str, str], contract.Handler]:
    built = (
        *routes.build_routes(
            map_fixtures._Worlds(world_fixtures.gap_world()),  # noqa: SLF001
            map_fixtures._Registries(world_fixtures.synthetic_registry()),  # noqa: SLF001
            _state_source(directory),
        ),
        *routes.METHOD_BOUNDARY_ROUTES,
    )
    return {(route.method, route.template): route.handler for route in built}


def _state_post(directory: Path, parameters: Mapping[str, str]) -> contract.Response:
    return _state_table(directory)["POST", advice_endpoint.STATE_ENDPOINT](parameters)


def _state_gap_id(directory: Path) -> str:
    found = _state_source(directory).advice(
        world_fixtures.gap_world(), world_fixtures.synthetic_registry()
    )
    assert found is not None
    ids = [a.card.id for a in found.cards if a.card.rule_id == power.GAP_RULE.rule_id]
    count = len(ids)
    assert count == 1
    return ids[0]


def _state_stored(directory: Path, card_id: str) -> CardState:
    """The state a FRESH ledger over the directory reads back from disk."""
    return Ledger(directory).state(world_fixtures.gap_world().token, card_id, now=NOW)


def _state_assert_refused(response: contract.Response, reason: str, *planted: str) -> None:
    assert response.http_status == contract.HTTP_BAD_REQUEST
    assert response.payload["reason"] == reason
    problems = len(contract.contract_problems(response))
    assert problems == 0
    body = contract.encode(response.payload)
    reflected = sum(1 for value in planted if value.encode("ascii") in body)
    assert reflected == 0


def _state_assert_nothing_written(directory: Path) -> None:
    created = len(list(directory.iterdir()))
    assert created == 0


# ---------------------------------------------------------------------------
# Recording
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("kind", PLAIN_KINDS)
def test_a_post_records_a_plain_state_read_back_from_disk(tmp_path: Path, kind: str) -> None:
    card_id = _state_gap_id(tmp_path)

    response = _state_post(
        tmp_path,
        {advice_endpoint.ID_PARAMETER: card_id, advice_endpoint.STATE_PARAMETER: kind},
    )

    assert response.http_status == contract.HTTP_OK
    problems = len(contract.contract_problems(response))
    assert problems == 0
    data = response.payload["data"]
    assert isinstance(data, dict)
    assert frozenset(data) == advice_endpoint.STATE_KEYS
    assert data["state"] == kind
    assert data["snoozed_until"] is None
    assert _state_stored(tmp_path, card_id) == CardState(kind)


def test_a_post_records_a_future_snooze_read_back_from_disk(tmp_path: Path) -> None:
    card_id = _state_gap_id(tmp_path)
    until = NOW + SNOOZE_SPAN

    response = _state_post(
        tmp_path,
        {
            advice_endpoint.ID_PARAMETER: card_id,
            advice_endpoint.STATE_PARAMETER: "snoozed",
            advice_endpoint.UNTIL_PARAMETER: str(until),
        },
    )

    assert response.http_status == contract.HTTP_OK
    data = response.payload["data"]
    assert isinstance(data, dict)
    assert data["snoozed_until"] == until
    assert _state_stored(tmp_path, card_id) == CardState.snoozed(until)


def test_recording_new_restores_a_dismissed_card(tmp_path: Path) -> None:
    card_id = _state_gap_id(tmp_path)
    Ledger(tmp_path).set_state(world_fixtures.gap_world().token, card_id, CardState.dismissed())

    response = _state_post(
        tmp_path,
        {advice_endpoint.ID_PARAMETER: card_id, advice_endpoint.STATE_PARAMETER: "new"},
    )

    assert response.http_status == contract.HTTP_OK
    assert _state_stored(tmp_path, card_id) == CardState.new()


# ---------------------------------------------------------------------------
# Refusals - 400, reflect nothing, write nothing
# ---------------------------------------------------------------------------


def test_an_unknown_card_is_400_reflects_nothing_and_writes_nothing(tmp_path: Path) -> None:
    response = _state_post(
        tmp_path,
        {
            advice_endpoint.ID_PARAMETER: UNKNOWN_CARD_ID,
            advice_endpoint.STATE_PARAMETER: "dismissed",
        },
    )

    _state_assert_refused(response, contract.REASON_INVALID_PARAMETER, UNKNOWN_CARD_ID)
    _state_assert_nothing_written(tmp_path)


def test_an_unknown_state_kind_is_400_reflects_nothing_and_writes_nothing(
    tmp_path: Path,
) -> None:
    card_id = _state_gap_id(tmp_path)

    response = _state_post(
        tmp_path,
        {advice_endpoint.ID_PARAMETER: card_id, advice_endpoint.STATE_PARAMETER: UNKNOWN_KIND},
    )

    _state_assert_refused(response, contract.REASON_INVALID_PARAMETER, UNKNOWN_KIND)
    _state_assert_nothing_written(tmp_path)


def test_completed_is_not_a_state_a_client_records(tmp_path: Path) -> None:
    card_id = _state_gap_id(tmp_path)

    response = _state_post(
        tmp_path,
        {advice_endpoint.ID_PARAMETER: card_id, advice_endpoint.STATE_PARAMETER: "completed"},
    )

    _state_assert_refused(response, contract.REASON_INVALID_PARAMETER)
    _state_assert_nothing_written(tmp_path)


def test_a_missing_state_is_400(tmp_path: Path) -> None:
    card_id = _state_gap_id(tmp_path)

    response = _state_post(tmp_path, {advice_endpoint.ID_PARAMETER: card_id})

    _state_assert_refused(response, contract.REASON_MISSING_PARAMETER)
    _state_assert_nothing_written(tmp_path)


def test_an_unknown_parameter_is_400_and_reflects_nothing(tmp_path: Path) -> None:
    card_id = _state_gap_id(tmp_path)

    response = _state_post(
        tmp_path,
        {
            advice_endpoint.ID_PARAMETER: card_id,
            advice_endpoint.STATE_PARAMETER: "dismissed",
            UNKNOWN_KIND: "1",
        },
    )

    _state_assert_refused(response, contract.REASON_UNKNOWN_PARAMETER, UNKNOWN_KIND)
    _state_assert_nothing_written(tmp_path)


def test_a_snooze_without_until_is_400(tmp_path: Path) -> None:
    card_id = _state_gap_id(tmp_path)

    response = _state_post(
        tmp_path,
        {advice_endpoint.ID_PARAMETER: card_id, advice_endpoint.STATE_PARAMETER: "snoozed"},
    )

    _state_assert_refused(response, contract.REASON_MISSING_PARAMETER)
    _state_assert_nothing_written(tmp_path)


def test_an_until_on_a_kind_that_is_not_a_snooze_is_400(tmp_path: Path) -> None:
    card_id = _state_gap_id(tmp_path)

    response = _state_post(
        tmp_path,
        {
            advice_endpoint.ID_PARAMETER: card_id,
            advice_endpoint.STATE_PARAMETER: "dismissed",
            advice_endpoint.UNTIL_PARAMETER: str(NOW + SNOOZE_SPAN),
        },
    )

    _state_assert_refused(response, contract.REASON_INVALID_PARAMETER)
    _state_assert_nothing_written(tmp_path)


#: Arabic-Indic one and two: ``str.isdigit`` admits them and ``int`` parses them,
#: so only the ASCII check refuses them. Built from code points so this source
#: stays 7-bit.
NON_ASCII_DIGITS: Final = chr(0x661) + chr(0x662)


@pytest.mark.parametrize("raw", ["-5", "1.5", "zqxj", "", "+5", " 5", NON_ASCII_DIGITS])
def test_a_non_decimal_until_is_400_and_reflects_nothing(tmp_path: Path, raw: str) -> None:
    card_id = _state_gap_id(tmp_path)

    response = _state_post(
        tmp_path,
        {
            advice_endpoint.ID_PARAMETER: card_id,
            advice_endpoint.STATE_PARAMETER: "snoozed",
            advice_endpoint.UNTIL_PARAMETER: raw,
        },
    )

    assert response.http_status == contract.HTTP_BAD_REQUEST
    assert response.payload["reason"] == contract.REASON_INVALID_PARAMETER
    _state_assert_nothing_written(tmp_path)


@pytest.mark.parametrize("until", [NOW, NOW - SNOOZE_SPAN])
def test_a_snooze_that_does_not_end_after_now_is_400(tmp_path: Path, until: int) -> None:
    card_id = _state_gap_id(tmp_path)

    response = _state_post(
        tmp_path,
        {
            advice_endpoint.ID_PARAMETER: card_id,
            advice_endpoint.STATE_PARAMETER: "snoozed",
            advice_endpoint.UNTIL_PARAMETER: str(until),
        },
    )

    _state_assert_refused(response, contract.REASON_INVALID_PARAMETER)
    _state_assert_nothing_written(tmp_path)


def test_an_unwritable_store_is_503_and_leaves_the_store_unchanged(tmp_path: Path) -> None:
    card_id = _state_gap_id(tmp_path)
    corrupt = b"{not json"
    (tmp_path / LEDGER_FILENAME).write_bytes(corrupt)

    response = _state_post(
        tmp_path,
        {advice_endpoint.ID_PARAMETER: card_id, advice_endpoint.STATE_PARAMETER: "dismissed"},
    )

    assert response.http_status == contract.HTTP_UNAVAILABLE
    unchanged = (tmp_path / LEDGER_FILENAME).read_bytes() == corrupt
    assert unchanged


# ---------------------------------------------------------------------------
# The route table
# ---------------------------------------------------------------------------


def test_a_get_on_the_state_template_stays_405(tmp_path: Path) -> None:
    response = _state_table(tmp_path)["GET", advice_endpoint.STATE_ENDPOINT]({})

    assert response.http_status == contract.HTTP_METHOD_NOT_ALLOWED
    _state_assert_nothing_written(tmp_path)


def test_pending_and_the_open_blockers_lose_cs_1269() -> None:
    unbacked = {template for _method, template in pending.UNBACKED}

    assert advice_endpoint.STATE_ENDPOINT not in unbacked
    assert advice_endpoint.STATE_ENDPOINT not in pending.BLOCKERS
    assert "CS-1269" not in frozenset(pending.BLOCKERS.values())
    assert "CS-1269" not in contract.OPEN_BLOCKERS


def test_health_reports_the_state_template_live() -> None:
    assert routes.ENDPOINT_STATUS[advice_endpoint.STATE_ENDPOINT] == health.LIVE


#: Every published route answering a method that is not safe, and whether it
#: declares that it mutates. PINNED so a new POST route has to decide: one that
#: changes state and forgets ``mutates`` would be reachable by a cross-site form.
NON_SAFE_ROUTES: Final = frozenset(
    {
        ("POST", "/api/solve", False),
        ("POST", "/api/optimize", False),
        ("POST", "/api/advice/<id>/state", True),
    }
)


def test_every_non_safe_published_route_has_decided_whether_it_mutates() -> None:
    published = (*routes.SERVING_ROUTES,)
    count = len(published)
    assert count > len(NON_SAFE_ROUTES)
    non_safe = frozenset(
        (route.method, route.template, route.mutates)
        for route in published
        if route.method not in server.SAFE_METHODS
    )
    assert non_safe == NON_SAFE_ROUTES


def test_the_state_route_is_the_one_the_server_guards() -> None:
    guarded = server.mutating_routes(routes.SERVING_ROUTES)
    assert guarded == frozenset({(advice_endpoint.METHOD_POST, advice_endpoint.STATE_ENDPOINT)})


# ---------------------------------------------------------------------------
# CS-1266: GET /api/advice names a built consumer the clocked draw never considered
# ---------------------------------------------------------------------------
#
# ``world_fixtures.gap_world`` builds one record of a modeled consumer class that
# carries no machine tag at all, beside the producing machine no registry entry
# prices. The consumer never enters the machines population, so before CS-1266
# the served gap card counted the one unmodeled machine and said nothing of it.
#
# CS-1280 then ruled such a consumer PRICED at its class default when its payload
# read clean (the 2026-10-08 CS-1280 decision record in docs/LEDGER.md), and
# gap_world's consumer reads clean, so it is no omission any more. The ruling's
# carve-out keeps a consumer carrying a pending clock tag a no-machine-state
# omission, so the CS-1266 arm builds its omission out of that tag - as the audit
# arms do, from ``tests.audit.test_balance.PENDING`` - and a second arm pins the
# clean consumer priced over the same route table.

#: What the served reason must carry for the one omitted consumer.
OMISSION_WORDS: Final = "1 built power consumer was never considered"

#: The words the served reason carries only when some consumer was omitted.
NEVER_CONSIDERED: Final = "never considered"

#: The record index of gap_world's tagless consumer.
CONSUMER_INDEX: Final = 0


def _omission_world() -> WorldModel:
    """gap_world with its tagless consumer carrying a pending clock tag and nothing else."""
    base = world_fixtures.gap_world()
    entries = dict(base.properties.by_record_index)
    entries[CONSUMER_INDEX] = replace(entries[CONSUMER_INDEX], values=balance_fixtures.PENDING)
    return replace(base, properties=WorldProperties(by_record_index=MappingProxyType(entries)))


def _served_gap(world: WorldModel, directory: Path) -> Mapping[str, object]:
    """The one gap card GET /api/advice serves for ``world`` over the real route table."""
    data = _data(_table(directory, world)["GET", advice_endpoint.ENDPOINT]({}))
    cards = data["cards"]
    assert isinstance(cards, list)
    served = [card for card in cards if card["rule_id"] == power.GAP_RULE.rule_id]
    count = len(served)
    assert count == 1
    card = served[0]
    assert isinstance(card, dict)
    return card


def test_the_listing_names_an_omitted_consumer_over_the_real_route_table(
    tmp_path: Path,
) -> None:
    served = _served_gap(_omission_world(), tmp_path)

    assert served["headline"] == "Resolve 2 unpriced machines before planning power"
    reason = served["reason"]
    assert isinstance(reason, str)
    assert OMISSION_WORDS in reason


def test_a_clean_tagless_consumer_is_priced_over_the_real_route_table(tmp_path: Path) -> None:
    """CS-1280: only the unregistered machine stays unpriced; nothing is named omitted."""
    served = _served_gap(world_fixtures.gap_world(), tmp_path)

    assert served["headline"] == "Resolve 1 unpriced machine before planning power"
    reason = served["reason"]
    assert isinstance(reason, str)
    assert NEVER_CONSIDERED not in reason
