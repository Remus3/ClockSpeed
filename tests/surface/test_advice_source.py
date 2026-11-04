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

A STATED TARGET (CS-1371) has its own section at the end of this file: all three routes,
through the real route table, the real source, the real advisor and the real ledger.

Every token, id and number here is invented. No save and no install is read;
every store lives in a temporary directory.
"""

from __future__ import annotations

import ast
import itertools
import subprocess
import sys
from dataclasses import replace
from fractions import Fraction
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Final

import pytest

from clockspeed.advisor.advise import advise_world, settled_rules
from clockspeed.advisor.ledger import (
    LEDGER_FILENAME,
    MUTES_FILENAME,
    CardState,
    Ledger,
    MuteStore,
)
from clockspeed.advisor.rules import fuel as fuel_rules
from clockspeed.advisor.rules import power, registered_rules
from clockspeed.advisor.trace import StepKind, run_rules
from clockspeed.audit.build import WARN_BUILD_MISMATCH
from clockspeed.audit.machines import PROPERTY_OVERCLOCK, PROPERTY_PRODUCING
from clockspeed.data.registry import plan_targets
from clockspeed.save.world import WorldProperties
from clockspeed.surface import providers as providers_module
from clockspeed.surface import server
from clockspeed.surface.api import advice as advice_endpoint
from clockspeed.surface.api import contract, health, pending, routes
from clockspeed.surface.providers import StoreAdviceSource
from tests.advisor import test_plan_redesign as redesign_fixtures
from tests.advisor import test_plan_world as plan_fixtures
from tests.advisor import test_world_advice as world_fixtures
from tests.advisor.build_fixtures import OFF_PIN_OFFSETS, docs_pin, game_pin
from tests.audit import test_balance as balance_fixtures
from tests.audit import test_fuel as fuel_fixtures
from tests.audit import test_production as production_fixtures
from tests.solve.synthetic import (
    SOLVE_ORE_ITEM,
    SOLVE_ORPHAN_ITEM,
    SOLVE_RARE_ITEM,
    SOLVE_RELIC_ITEM,
    SOLVE_ROD_ITEM,
)
from tests.surface import test_map as map_fixtures

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator, Mapping

    from clockspeed.advisor.advise import Advice
    from clockspeed.advisor.plans import PlanRequest
    from clockspeed.data.registry import Registry
    from clockspeed.save.world import WorldModel

#: The instant the injected clock answers.
NOW: Final = 1000

#: How far past :data:`NOW` a planted snooze runs.
SNOOZE_SPAN: Final = 50

#: The shipped surface package, read as source.
SURFACE_ROOT: Final = Path(__file__).resolve().parents[2] / "clockspeed" / "surface"

#: The layer no advice-path surface module may import.
AUDIT_PACKAGE: Final = "clockspeed.audit"

#: The surface modules importing the audit layer, pinned, not tolerated:
#: ``api/map.py`` since CS-977 - it serializes the placement and inventory
#: models - and ``api/provenance.py`` since CS-1315 slice B, which copies the
#: audit's registry check into the three pricing doors' bodies.
AUDIT_IMPORTERS: Final = frozenset({"api/map.py", "api/provenance.py"})

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
    directory: Path, world: WorldModel | None = None, registry: Registry | None = None
) -> Mapping[tuple[str, str], contract.Handler]:
    built = routes.build_routes(
        map_fixtures._Worlds(world_fixtures.gap_world() if world is None else world),  # noqa: SLF001
        map_fixtures._Registries(  # noqa: SLF001
            world_fixtures.synthetic_registry() if registry is None else registry
        ),
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


# ---------------------------------------------------------------------------
# CS-1285 slice D: GET /api/advice carries the fuel trace, and nothing halts
# ---------------------------------------------------------------------------
#
# THE CLAIM. The fuel family is registered beside ``inputs_of`` offering its
# inputs (the slice C ruling G6), so over the real route table and the
# store-reading source, GET /api/advice serves both fuel cards on the
# synthetic fuel world and GET /api/advice/<id>/derivation serves each one's
# tier 3, generated from a trace that reads the fuel audit's own fields.
#
# THE TRAP. A wiring change can halt a rule that was silent before: a
# registered rule offered no input stops on ``input-missing``, and an audit
# that raises takes the whole listing down. So every world the surface tests
# serve is driven end to end - the listing answers 200, every registered rule
# leaves exactly one trace, no trace holds an input-missing, input-refused,
# precondition-unmet or rule-error step, and every rule that settled over the
# balance-only inputs offered before slice D still settles.
#
# The figures are worked by hand in ``tests/advisor/test_world_advice.py``;
# the display names are the fuel audit fixtures' own invented ones.

#: The step kinds that mean a rule halted rather than decided.
HALTING_KINDS: Final = frozenset(
    {
        StepKind.INPUT_MISSING,
        StepKind.INPUT_REFUSED,
        StepKind.PRECONDITION_UNMET,
        StepKind.RULE_ERROR,
    }
)

#: The supply card's headline on the fuel world: 10 m3 a minute short.
FUEL_SUPPLY_HEADLINE: Final = (
    f"Supply 10.00 m3 more Synthetic {fuel_fixtures.FUEL} per minute"
    f" to Synthetic {fuel_fixtures.GEN_FUEL} x1"
)

#: The demand card's headline on the fuel world: 15 items a minute of coal.
FUEL_DEMAND_HEADLINE: Final = (
    f"Plan 15.00 items of Synthetic {fuel_fixtures.COAL} per minute"
    f" for Synthetic {fuel_fixtures.GEN_COAL} x1"
)

#: The audit field the fuel rules' verdict input is sourced to.
VERDICT_SOURCE: Final = "audit.fuel.verdicts.verdict"


def _coal_world(*, tagged: int, untagged: int) -> WorldModel:
    """Built coal generators: ``tagged`` running at clock one, ``untagged`` with no machine tag.

    An untagged record is a built generator the save never recorded as a
    running machine, so the machines model never admits it and the fuel audit
    counts it as omitted (CS-1285 fix round 2).
    """
    base = balance_fixtures.world_of(*([fuel_fixtures.GEN_COAL] * (tagged + untagged)))
    entries = dict(base.properties.by_record_index)
    running = MappingProxyType(
        {PROPERTY_PRODUCING: True, PROPERTY_OVERCLOCK: world_fixtures.CLOCK_ONE}
    )
    for index in range(tagged):
        entries[index] = replace(entries[index], values=running)
    return replace(base, properties=WorldProperties(by_record_index=MappingProxyType(entries)))


def _one_coal_untagged() -> WorldModel:
    return _coal_world(tagged=1, untagged=1)


def _every_coal_untagged() -> WorldModel:
    return _coal_world(tagged=0, untagged=2)


def _generator_world() -> WorldModel:
    """The CS-1271 world: one built liquid generator whose fuels the registry never lists."""
    return balance_fixtures.world_of(production_fixtures.FUEL)


#: Every world the surface tests serve, with the registry each is served over.
#: Every registry here is VERIFIED - stamped as built from the pinned docs bytes
#: by ``tests.advisor.build_fixtures.pinned_source`` (CS-1315) - so no served
#: card carries a registry code and every expected text below is unchanged.
SERVED_WORLDS: Final[dict[str, tuple[Callable[[], WorldModel], Callable[[], Registry]]]] = {
    "fuel": (world_fixtures.fuel_world, world_fixtures.fuel_registry),
    "gap": (world_fixtures.gap_world, world_fixtures.synthetic_registry),
    "generator": (_generator_world, world_fixtures.generator_registry),
    "omission": (_omission_world, world_fixtures.synthetic_registry),
    "coal-one-untagged": (_one_coal_untagged, world_fixtures.fuel_registry),
    "coal-all-untagged": (_every_coal_untagged, world_fixtures.fuel_registry),
}


@pytest.mark.parametrize("world_name", sorted(SERVED_WORLDS))
def test_every_served_registry_is_verified_against_the_docs_pin(world_name: str) -> None:
    """CS-1315: the fixtures serve verified registries, so no card names a registry code."""
    _make_world, make_registry = SERVED_WORLDS[world_name]
    verified = make_registry().source_sha256 == docs_pin()
    assert verified


def _fuel_cards(directory: Path) -> dict[str, Mapping[str, object]]:
    """The fuel cards GET /api/advice serves on the fuel world, by rule id."""
    table = _table(directory, world_fixtures.fuel_world(), world_fixtures.fuel_registry())
    data = _data(table["GET", advice_endpoint.ENDPOINT]({}))
    cards = data["cards"]
    assert isinstance(cards, list)
    fuel_ids = (fuel_rules.DEMAND_RULE.rule_id, fuel_rules.SUPPLY_RULE.rule_id)
    served = {card["rule_id"]: card for card in cards if card["rule_id"] in fuel_ids}
    assert sorted(served) == sorted(fuel_ids)
    return served


def test_the_listing_serves_both_fuel_cards_over_the_real_route_table(tmp_path: Path) -> None:
    served = _fuel_cards(tmp_path)

    supply = served[fuel_rules.SUPPLY_RULE.rule_id]
    demand = served[fuel_rules.DEMAND_RULE.rule_id]
    assert supply["headline"] == FUEL_SUPPLY_HEADLINE
    assert demand["headline"] == FUEL_DEMAND_HEADLINE
    assert supply["domain"] == demand["domain"] == fuel_rules.DOMAIN
    assert supply["state"] == demand["state"] == "new"


@pytest.mark.parametrize(
    "rule_id",
    [fuel_rules.DEMAND_RULE.rule_id, fuel_rules.SUPPLY_RULE.rule_id],
)
def test_the_derivation_serves_a_fuel_cards_trace_over_the_real_route_table(
    tmp_path: Path, rule_id: str
) -> None:
    card_id = _fuel_cards(tmp_path)[rule_id]["id"]
    assert isinstance(card_id, str)
    found = _source(tmp_path).advice(world_fixtures.fuel_world(), world_fixtures.fuel_registry())
    assert found is not None
    expected = next(a.card for a in found.cards if a.card.id == card_id)
    table = _table(tmp_path, world_fixtures.fuel_world(), world_fixtures.fuel_registry())

    data = _data(
        table["GET", advice_endpoint.DERIVATION_ENDPOINT]({advice_endpoint.ID_PARAMETER: card_id})
    )

    derivation = data["derivation"]
    assert isinstance(derivation, str)
    assert derivation == expected.tier3
    assert VERDICT_SOURCE in derivation
    assert fuel_rules.IN_VERDICTS in derivation


@pytest.mark.parametrize("world_name", sorted(SERVED_WORLDS))
def test_no_rule_halts_on_a_served_world(tmp_path: Path, world_name: str) -> None:
    make_world, make_registry = SERVED_WORLDS[world_name]
    model = make_world()
    registry = make_registry()

    data = _data(_table(tmp_path, model, registry)["GET", advice_endpoint.ENDPOINT]({}))
    found = _source(tmp_path).advice(model, registry)

    assert found is not None
    # Each read of the withheld traces is reduced inline to a flag or a count,
    # so no local holds them when an assertion fails (CS-850, CS-851).
    one_trace_per_rule = [trace.rule_id for trace in found.traces] == [
        spec.rule_id for spec in registered_rules()
    ]
    assert one_trace_per_rule
    halted = sum(1 for trace in found.traces for step in trace.steps if step.kind in HALTING_KINDS)
    assert halted == 0
    balanced = world_fixtures.balance_by_hand(
        model, registry, pinned_changelist=game_pin(), pinned_docs_sha256=docs_pin()
    )
    before = settled_rules(run_rules(power.RULES, balanced))
    after = settled_rules(found.traces)
    assert sorted(before - after) == []
    cards = data["cards"]
    assert isinstance(cards, list)
    served = sorted(card["rule_id"] for card in cards)
    assert served == sorted(advised.card.rule_id for advised in found.cards)


# CS-1285 fix round 2: a built generator the save never recorded as a running
# machine still counts. Two built coal generators, one or both untagged: the
# demand card names both, and says how many were never read - never "x1" and
# never "x0".

_UNREAD_COAL: Final = f"Synthetic {fuel_fixtures.GEN_COAL}"


@pytest.mark.parametrize(
    ("make_world", "headline", "note"),
    [
        (
            _one_coal_untagged,
            f"Resolve the fuel burn of {_UNREAD_COAL} x2 (1 never read) before planning its fuel",
            "; 1 built generator was never read",
        ),
        (
            _every_coal_untagged,
            f"Resolve the fuel burn of {_UNREAD_COAL} x2 (2 never read) before planning its fuel",
            "; 2 built generators were never read",
        ),
    ],
    ids=["one-untagged", "all-untagged"],
)
def test_the_listing_states_the_built_generator_count_over_the_real_route_table(
    tmp_path: Path, make_world: Callable[[], WorldModel], headline: str, note: str
) -> None:
    table = _table(tmp_path, make_world(), world_fixtures.fuel_registry())

    data = _data(table["GET", advice_endpoint.ENDPOINT]({}))

    cards = data["cards"]
    assert isinstance(cards, list)
    served = [card for card in cards if card["rule_id"] == fuel_rules.DEMAND_RULE.rule_id]
    count = len(served)
    assert count == 1
    card = served[0]
    assert isinstance(card, dict)
    assert card["headline"] == headline
    reason = card["reason"]
    assert isinstance(reason, str)
    assert reason.endswith(note)
    assert "x0" not in f"{headline} {reason}"


# ---------------------------------------------------------------------------
# CS-1288: GET /api/advice states an off-pin build (the session 138 rulings
# F1, F2 and F5)
# ---------------------------------------------------------------------------
#
# THE CLAIM. The store-reading source hands the advisor the pin as it reads
# at call time, so over the real route table every card served for a save
# another build wrote carries the mismatch code and both builds in its reason
# (tier 2) and its derivation (tier 3), and no card served for a save the
# pinned build wrote mentions a build at all. A source that handed no pin
# would serve every on-pin card as uncompared, which the on-pin arm refuses.

#: The served worlds the build arms run over; each serves at least one card.
BUILD_WORLDS: Final = ("fuel", "gap", "omission")


def _served_texts(directory: Path, model: WorldModel, registry: Registry) -> list[tuple[str, str]]:
    """Each card GET /api/advice serves for a world: its reason, and its derivation."""
    table = _table(directory, model, registry)
    cards = _data(table["GET", advice_endpoint.ENDPOINT]({}))["cards"]
    assert isinstance(cards, list)
    texts: list[tuple[str, str]] = []
    for card in cards:
        assert isinstance(card, dict)
        derivation = _data(
            table["GET", advice_endpoint.DERIVATION_ENDPOINT](
                {advice_endpoint.ID_PARAMETER: card["id"]}
            )
        )["derivation"]
        reason = card["reason"]
        assert isinstance(reason, str)
        assert isinstance(derivation, str)
        texts.append((reason, derivation))
    return texts


def _built_by(model: WorldModel, changelist: int) -> WorldModel:
    """The same world as a save whose header declares ``changelist``."""
    return replace(model, header=replace(model.header, build_changelist=changelist))


def _side(offset: int) -> str:
    """A test id for an offset: the side of the pin the save sits on."""
    return "after" if offset > 0 else "before"


@pytest.mark.parametrize("offset", OFF_PIN_OFFSETS, ids=_side)
@pytest.mark.parametrize("world_name", BUILD_WORLDS)
def test_off_the_pin_the_listing_and_derivation_name_both_builds(
    tmp_path: Path, world_name: str, offset: int
) -> None:
    """Both sides of the pin, the build after it and the build before it.

    A save OLDER than the pin is the item's motivating case (CS-1288 fix round
    1), so a source whose caveat compared builds by order would serve one side
    no card at all.
    """
    pin = game_pin()
    save = pin + offset
    assert save > 0, "the off-pin save build is not a positive changelist"
    make_world, make_registry = SERVED_WORLDS[world_name]
    words = (WARN_BUILD_MISMATCH, f"priced at the pinned build {pin},", f"save build {save}")

    texts = _served_texts(tmp_path, _built_by(make_world(), save), make_registry())

    served = len(texts)
    unnamed = sum(
        1 for reason, derivation in texts if not all(w in reason and w in derivation for w in words)
    )
    assert served > 0
    assert unnamed == 0


@pytest.mark.parametrize("world_name", BUILD_WORLDS)
def test_on_the_pin_the_listing_and_derivation_name_no_build(
    tmp_path: Path, world_name: str
) -> None:
    make_world, make_registry = SERVED_WORLDS[world_name]

    texts = _served_texts(tmp_path, make_world(), make_registry())

    served = len(texts)
    mentioning = sum(
        1 for reason, derivation in texts if "build-" in reason or "build-" in derivation
    )
    assert served > 0
    assert mentioning == 0


# ---------------------------------------------------------------------------
# CS-1371: a stated target through the real route table and the real advisor
# ---------------------------------------------------------------------------
#
# THE CLAIM. The three routes take a target, a rate, a direction and a byproduct policy.
# Stated, the listing carries a plan card and what the request came to, the derivation
# carries that card's tier 3 and the state route records that card, each through the same
# stated advice. Not stated, each route answers as it did before this item. Every arm here
# runs through ``routes.build_routes``, the real ``StoreAdviceSource``, the real advisor and
# the real ledger, over the synthetic worlds of ``tests/advisor/test_plan_world.py`` and
# ``tests/advisor/test_plan_redesign.py``, whose figures are worked by hand there.
#
# THE ORDER. Unknown name, then a partial set, then a bad rate, direction or policy, all
# before any provider is read; then no save and no install; then the target's membership;
# then the advice. A refused value reaches no solve and comes back in no byte.
#
# THE CONTROL. A 400 from a route that answers 400 to everything grades nothing, so
# :func:`control_card` shows the four good values answer 200 on all three routes, on the
# same world, before any refusal below is believed.

#: The rules a stated target can fire, spelled so a rename reddens here.
ADOPT_ID: Final = "plan.adopt"
REDESIGN_ID: Final = "plan.redesign"

#: The wire spelling of the four parameters, spelled for the same reason.
TARGET: Final = "target"
RATE: Final = "rate"
DIRECTION: Final = "direction"
POLICY: Final = "byproduct_policy"
FOUR: Final = (TARGET, RATE, DIRECTION, POLICY)

#: The three routes, by what they are for.
LISTING: Final = "listing"
DERIVATION: Final = "derivation"
STATE: Final = "state"
ROUTE_NAMES: Final = (LISTING, DERIVATION, STATE)

#: The kind the state arms record.
ACCEPTED: Final = "accepted"

#: The closed-vocabulary reasons the wire reads, spelled so a rewording reddens here.
NO_PLAN_REASON: Final = (
    "the search found no plan over the unlocked automated recipes it kept,"
    " under the stated byproduct policy"
)
MALFORMED_REASON: Final = "the stated request cannot be asked as a question"

#: The tier 2 clauses of a route card, spelled for the same reason.
MUST_UNLOCK: Final = "; the locked recipes must unlock first on this route"
NO_UNLOCK: Final = "; this route needs no unlock and the capped search did not find it"
NOT_CHOSEN: Final = (
    "; the stated direction did not choose this route and it was never compared with what is built"
)

#: The badge's whole read in the derivation of the ascent world's card, worked by hand in
#: ``tests/advisor/test_plan_world.py``: it clears within-raw and neither other rung.
BADGE_READ: Final = (
    'Read plan.badge = StrategyBadge(strongest="within-raw", cleared=("within-raw"), checks=('
    'ThresholdCheck(strategy="within-raw", cleared=true, score=10.00, reference=10.00, '
    'bound=1.00, reason=""), '
    'ThresholdCheck(strategy="within-buildings", cleared=false, score=2.00, reference=1.00, '
    'bound=1.00, reason="over-bound"), '
    'ThresholdCheck(strategy="within-power", cleared=false, score=30.00, reference=15.00, '
    'bound=1.00, reason="over-bound"))) from solve.strategy.ranked_plan.badge'
)

#: A value carried in every position a refusal could reflect it from.
PLANTED: Final = "zqxjplanted1371"

#: Every rate refused, none of them above zero in an admitted spelling.
BAD_RATES: Final = (
    "0",
    "0.0",
    "00",
    "0/5",
    "-1",
    "-0.5",
    "-1/2",
    "1/0",
    "1e3",
    "1E3",
    "abc",
    "",
    " 10",
    "10 ",
    "10\n",
    "+10",
    "1.5.5",
    "1/2/3",
    ".5",
    "5.",
    "0x10",
    "NaN",
    "inf",
    "1_000",
    NON_ASCII_DIGITS,
    "9" * 65,
)

#: Every direction refused: near misses of the closed vocabulary, by case and by padding.
BAD_DIRECTIONS: Final = ("", "RAW", "raw ", "sideways", "weighted", "raw,power")

#: Every policy refused, for the same reason.
BAD_POLICIES: Final = ("", "BALANCED", "balanced ", "whatever", "sink")

#: Each proper non-empty subset of the four: every way of stating some without the rest.
PARTIAL_SETS: Final = tuple(
    names for size in range(1, len(FOUR)) for names in itertools.combinations(FOUR, size)
)

#: How many ways there are of stating some of the four, by hand: four ones, six twos and
#: four threes.
PARTIAL_SET_COUNT: Final = 14

#: The provider reads of a request that got as far as the membership test: one of each.
ONE_WORLD_AND_ONE_REGISTRY: Final = 2

#: What the determinism children print.
CHILD_SOURCE: Final = """
import sys
from pathlib import Path

from tests.surface.test_advice_source import stated_bodies

print(stated_bodies(Path(sys.argv[1])))
"""

#: The two hash seeds the determinism arm compares.
HASH_SEEDS: Final = ("0", "1")

#: Child process bound. Generous: each child builds registries and runs two searches.
CHILD_TIMEOUT_SECONDS: Final = 300

#: The repository root, each child's working directory.
REPO_ROOT: Final = Path(__file__).resolve().parents[2]


def _stated(
    target: str = SOLVE_RELIC_ITEM,
    *,
    rate: str = "10",
    direction: str = "raw",
    policy: str = "balanced",
) -> dict[str, str]:
    """The four parameters, as a query carries them."""
    return {TARGET: target, RATE: rate, DIRECTION: direction, POLICY: policy}


class _CountedProviders:
    """A world and a registry provider in one, either possibly absent, counting each read."""

    def __init__(self, model: WorldModel | None, registry: Registry | None) -> None:
        """Hold what to answer.

        Args:
            model: The world, or None for a machine with no save.
            registry: The registry, or None for a machine with no install.
        """
        self._model = model
        self._registry = registry
        self.reads = 0

    def world(self) -> WorldModel | None:
        """Answer with the held world, counting the read."""
        self.reads += 1
        return self._model

    def registry(self) -> Registry | None:
        """Answer with the held registry, counting the read."""
        self.reads += 1
        return self._registry


class _CountedSource(StoreAdviceSource):
    """The real source, counting each time advice is computed."""

    def __init__(self, directory: Path) -> None:
        """Wire the real source to one store directory and the fixed clock.

        Args:
            directory: Where both stores live.
        """
        super().__init__(directory, clock=lambda: NOW)
        self.computed = 0

    def advice(
        self, world: WorldModel, registry: Registry, *, plan_request: PlanRequest | None = None
    ) -> Advice | None:
        """Count the call and run the real advisor."""
        self.computed += 1
        return super().advice(world, registry, plan_request=plan_request)


def _counted_table(
    directory: Path, model: WorldModel | None, registry: Registry | None
) -> tuple[Mapping[tuple[str, str], contract.Handler], _CountedProviders, _CountedSource]:
    """The real route table over counted providers and a counted real source."""
    counted = _CountedProviders(model, registry)
    source = _CountedSource(directory)
    built = routes.build_routes(counted, counted, source)
    return {(route.method, route.template): route.handler for route in built}, counted, source


def _ascent() -> tuple[WorldModel, Registry]:
    """The world whose stated Relic ranks, every recipe unlocked."""
    return (
        plan_fixtures._model(plan_fixtures.ASCENT_PATHS),  # noqa: SLF001
        plan_fixtures._registry(),  # noqa: SLF001
    )


def _route_world(held: tuple[str, ...]) -> WorldModel:
    """A world holding these recipes of the marked-route fixtures, and no machine."""
    return redesign_fixtures._model(held)  # noqa: SLF001


def _three_locked() -> tuple[WorldModel, Registry]:
    """The world whose every route to Relic runs at least three locked stages."""
    held = (redesign_fixtures.HELD_STAGE,)
    return _route_world(held), redesign_fixtures._three_locked_registry()  # noqa: SLF001


def _listing(
    table: Mapping[tuple[str, str], contract.Handler], parameters: Mapping[str, str]
) -> Mapping[str, object]:
    """The body the listing answers, which must be 200."""
    return _data(table["GET", advice_endpoint.ENDPOINT](parameters))


def _cards_of(data: Mapping[str, object], rule_id: str) -> list[Mapping[str, object]]:
    """Every card one rule has on a listing body."""
    cards = data["cards"]
    assert isinstance(cards, list)
    return [card for card in cards if card["rule_id"] == rule_id]


def _one_card(data: Mapping[str, object], rule_id: str) -> Mapping[str, object]:
    """The one card one rule has on a listing body."""
    cards = _cards_of(data, rule_id)
    count = len(cards)
    assert count == 1
    return cards[0]


def _card_id(data: Mapping[str, object], rule_id: str) -> str:
    """The id of the one card one rule has on a listing body."""
    found = _one_card(data, rule_id)["id"]
    assert isinstance(found, str)
    return found


def _outcome_on(data: Mapping[str, object]) -> Mapping[str, object]:
    """What a stated listing says the request came to, read from the wire body."""
    assert frozenset(data) == advice_endpoint.STATED_DATA_KEYS
    outcome = data["plan_outcome"]
    assert isinstance(outcome, dict)
    return outcome


def _derivation_text(
    table: Mapping[tuple[str, str], contract.Handler],
    card_id: str,
    parameters: Mapping[str, str],
) -> str:
    """The tier 3 the derivation route answers, which must be 200, read from the wire body."""
    data = _data(
        table["GET", advice_endpoint.DERIVATION_ENDPOINT](
            {advice_endpoint.ID_PARAMETER: card_id, **parameters}
        )
    )
    assert frozenset(data) == advice_endpoint.DERIVATION_KEYS
    text = data["derivation"]
    assert isinstance(text, str)
    return text


def _ask(
    table: Mapping[tuple[str, str], contract.Handler],
    route: str,
    card_id: str,
    parameters: Mapping[str, str],
) -> contract.Response:
    """Ask one of the three routes, with what that route needs beside these parameters."""
    if route == LISTING:
        return table["GET", advice_endpoint.ENDPOINT](parameters)
    if route == DERIVATION:
        return table["GET", advice_endpoint.DERIVATION_ENDPOINT](
            {advice_endpoint.ID_PARAMETER: card_id, **parameters}
        )
    return table["POST", advice_endpoint.STATE_ENDPOINT](
        {
            advice_endpoint.ID_PARAMETER: card_id,
            advice_endpoint.STATE_PARAMETER: ACCEPTED,
            **parameters,
        }
    )


def _recorded_kind(directory: Path, model: WorldModel, card_id: str) -> str:
    """The state a FRESH ledger over the directory reads back from disk."""
    return Ledger(directory).state(model.token, card_id, now=NOW).kind


@pytest.fixture(scope="module")
def control_card(tmp_path_factory: pytest.TempPathFactory) -> str:
    """The four good values answer 200 on all three routes, so a 400 below is the value's.

    Returns:
        The id of the ascent world's stated card, so a refusal can name a card that is really
        on the stated listing and only the parameter can be what refused it.
    """
    table, _counted, _source = _counted_table(tmp_path_factory.mktemp("control"), *_ascent())
    card_id = _card_id(_listing(table, _stated()), ADOPT_ID)
    answered = [
        _ask(table, route, card_id, _stated()).http_status == contract.HTTP_OK
        for route in ROUTE_NAMES
    ]
    assert answered == [True, True, True]
    return card_id


def _refused_before_any_provider(
    response: contract.Response,
    reason: str,
    counted: _CountedProviders,
    source: _CountedSource,
    directory: Path,
) -> None:
    """A 400 of this reason, reaching no provider, no advice and no store."""
    assert response.http_status == contract.HTTP_BAD_REQUEST
    assert response.payload["reason"] == reason
    problems = len(contract.contract_problems(response))
    assert problems == 0
    assert counted.reads == 0
    assert source.computed == 0
    _state_assert_nothing_written(directory)


# ---------------------------------------------------------------------------
# Arm 1: the three routes read one stated card
# ---------------------------------------------------------------------------


def test_a_stated_target_lists_a_plan_adopt_card_and_reads_ranked(tmp_path: Path) -> None:
    model, registry = _ascent()

    data = _listing(_table(tmp_path, model, registry), _stated())

    card = _one_card(data, ADOPT_ID)
    assert frozenset(card) == advice_endpoint.CARD_KEYS
    assert card["headline"] == f"Build the planned production chain for {SOLVE_RELIC_ITEM}"
    assert card["reason"] == (
        f"It makes 10.00 per minute of {SOLVE_RELIC_ITEM} with 2.00 machine equivalents"
    )
    assert card["state"] == "new"
    assert card["visible"] is True
    assert _outcome_on(data) == {"status": "ranked", "redesign": "not-reached", "trimmed": []}


def test_the_same_four_on_the_derivation_return_tier_3_with_the_badges_rungs(
    tmp_path: Path,
) -> None:
    model, registry = _ascent()
    table = _table(tmp_path, model, registry)
    card_id = _card_id(_listing(table, _stated()), ADOPT_ID)

    derivation = _derivation_text(table, card_id, _stated())

    carried = BADGE_READ in derivation
    assert carried
    opened = derivation.startswith("Derivation of rule plan.adopt")
    assert opened


def test_the_same_four_on_the_state_route_record_that_card_through_the_real_ledger(
    tmp_path: Path,
) -> None:
    model, registry = _ascent()
    table = _table(tmp_path, model, registry)
    card_id = _card_id(_listing(table, _stated()), ADOPT_ID)

    response = _ask(table, STATE, card_id, _stated())

    data = _data(response)
    assert frozenset(data) == advice_endpoint.STATE_KEYS
    assert data["state"] == ACCEPTED
    assert data["snoozed_until"] is None
    assert _recorded_kind(tmp_path, model, card_id) == ACCEPTED
    # And the next stated listing reads it, so the ledger's card is the listing's card.
    relisted = _one_card(_listing(table, _stated()), ADOPT_ID)
    assert relisted["state"] == ACCEPTED


def test_a_snooze_on_a_stated_card_records_its_instant(tmp_path: Path) -> None:
    model, registry = _ascent()
    table = _table(tmp_path, model, registry)
    card_id = _card_id(_listing(table, _stated()), ADOPT_ID)
    until = NOW + SNOOZE_SPAN

    response = table["POST", advice_endpoint.STATE_ENDPOINT](
        {
            advice_endpoint.ID_PARAMETER: card_id,
            advice_endpoint.STATE_PARAMETER: "snoozed",
            advice_endpoint.UNTIL_PARAMETER: str(until),
            **_stated(),
        }
    )

    assert _data(response)["snoozed_until"] == until
    assert _recorded_kind(tmp_path, model, card_id) == "snoozed"


def test_the_state_route_resolves_one_world_for_the_card_and_the_write(tmp_path: Path) -> None:
    """The same rule as with no target: the record lands where the card was checked."""
    model, registry = _ascent()
    table, counted, _source = _counted_table(tmp_path, model, registry)
    card_id = _card_id(_listing(table, _stated()), ADOPT_ID)
    before = counted.reads

    _data(_ask(table, STATE, card_id, _stated()))

    # Nothing asked a provider a second time, so the card checked is the world recorded in.
    assert counted.reads - before == ONE_WORLD_AND_ONE_REGISTRY


@pytest.mark.parametrize("route", [DERIVATION, STATE])
def test_without_the_four_the_card_is_400_and_the_same_request_with_them_answers(
    tmp_path: Path, route: str
) -> None:
    """Pinned against the same request: only the four move the answer.

    Without them the advice is the no-target advice, which lists no plan card, so this is the
    parent commit's refusal of a card the current advice does not carry.
    """
    model, registry = _ascent()
    table = _table(tmp_path, model, registry)
    card_id = _card_id(_listing(table, _stated()), ADOPT_ID)

    without = _ask(table, route, card_id, {})

    _state_assert_refused(without, contract.REASON_INVALID_PARAMETER, card_id)
    _state_assert_nothing_written(tmp_path)
    _data(_ask(table, route, card_id, _stated()))


def test_a_no_target_listing_on_the_same_world_reads_no_plan_card_and_no_outcome_key(
    tmp_path: Path,
) -> None:
    model, registry = _ascent()

    response = _table(tmp_path, model, registry)["GET", advice_endpoint.ENDPOINT]({})

    data = _data(response)
    assert frozenset(data) == advice_endpoint.DATA_KEYS
    assert _cards_of(data, ADOPT_ID) == []
    assert _cards_of(data, REDESIGN_ID) == []
    named = b"plan_outcome" in contract.encode(response.payload)
    assert named is False


def test_a_card_another_family_fires_answers_with_and_without_the_four(tmp_path: Path) -> None:
    """A stated target adds a plan family answer, and takes no other family's card away."""
    registry = world_fixtures.fuel_registry()
    table = _table(tmp_path, world_fixtures.fuel_world(), registry)
    targets = plan_targets(registry)
    count = len(targets)
    assert count > 0
    card_id = _fuel_cards(tmp_path)[fuel_rules.SUPPLY_RULE.rule_id]["id"]
    assert isinstance(card_id, str)

    without = _data(_ask(table, DERIVATION, card_id, {}))
    stated = _data(_ask(table, DERIVATION, card_id, _stated(targets[0])))

    same = stated == without
    assert same


# ---------------------------------------------------------------------------
# Arm 3: what the request came to, one arm per marked-route status
# ---------------------------------------------------------------------------


def test_a_ranked_request_reads_not_reached_and_no_route_card(tmp_path: Path) -> None:
    model, registry = _ascent()

    data = _listing(_table(tmp_path, model, registry), _stated())

    assert _outcome_on(data)["redesign"] == "not-reached"
    assert _cards_of(data, REDESIGN_ID) == []


def test_a_routed_request_reads_its_card_through_the_listing_and_the_derivation(
    tmp_path: Path,
) -> None:
    model, registry = _three_locked()
    table = _table(tmp_path, model, registry)

    data = _listing(table, _stated())

    assert _outcome_on(data) == {
        "status": "no-plan",
        "reason": NO_PLAN_REASON,
        "redesign": "routed",
        "trimmed": [],
    }
    assert _cards_of(data, ADOPT_ID) == []
    card = _one_card(data, REDESIGN_ID)
    headline = card["headline"]
    reason = card["reason"]
    assert headline == f"Plan toward {SOLVE_RELIC_ITEM}"
    assert reason == f"This route runs 3 locked and 1 held recipe(s){MUST_UNLOCK}{NOT_CHOSEN}"
    assert isinstance(headline, str)
    assert isinstance(reason, str)
    named = [name for name in redesign_fixtures.LOCKED_STAGES if name in headline + reason]
    assert named == []

    card_id = card["id"]
    assert isinstance(card_id, str)
    derivation = _derivation_text(table, card_id, _stated())
    locked_line = (
        'Read plan.redesign.locked = ("R_A2", "R_A3", "R_A4") from advisor.plans.redesign.locked'
    )
    carried = locked_line in derivation
    assert carried
    every_stage = (redesign_fixtures.HELD_STAGE, *redesign_fixtures.LOCKED_STAGES)
    absent = [
        stage
        for stage in every_stage
        if f'PlanStep(recipe_key="{stage}", machines=1.00)' not in derivation
    ]
    assert absent == []
    badge = "StrategyBadge" in derivation
    assert not badge


def test_a_route_card_records_through_the_state_route(tmp_path: Path) -> None:
    model, registry = _three_locked()
    table = _table(tmp_path, model, registry)
    card_id = _card_id(_listing(table, _stated()), REDESIGN_ID)

    _data(_ask(table, STATE, card_id, _stated()))

    assert _recorded_kind(tmp_path, model, card_id) == ACCEPTED


def test_a_no_route_request_names_the_item_on_the_wire(tmp_path: Path) -> None:
    registry = redesign_fixtures._orphan_registry()  # noqa: SLF001

    data = _listing(_table(tmp_path, _route_world(()), registry), _stated())

    assert _outcome_on(data) == {
        "status": "no-plan",
        "reason": NO_PLAN_REASON,
        "redesign": "no-route",
        "trimmed": [],
        "unmade": [SOLVE_ORPHAN_ITEM],
    }
    assert _cards_of(data, REDESIGN_ID) == []
    assert _cards_of(data, ADOPT_ID) == []


def test_the_same_no_route_request_fires_where_the_group_holds_the_item(tmp_path: Path) -> None:
    """The control for the arm above: only the group's word moves it, so the arm is live."""
    registry = redesign_fixtures._orphan_registry(orphan_raw=True)  # noqa: SLF001

    data = _listing(_table(tmp_path, _route_world(()), registry), _stated())

    assert _outcome_on(data)["redesign"] == "routed"
    _one_card(data, REDESIGN_ID)


def test_a_route_refused_request_fires_under_the_other_policy_on_the_wire(tmp_path: Path) -> None:
    registry = redesign_fixtures._byproduct_registry()  # noqa: SLF001
    table = _table(tmp_path, _route_world(()), registry)

    refused = _listing(table, _stated(policy="balanced"))
    fired = _listing(table, _stated(policy="sinkable"))

    assert _outcome_on(refused) == {
        "status": "no-plan",
        "reason": NO_PLAN_REASON,
        "redesign": "route-refused",
        "trimmed": [],
    }
    assert _cards_of(refused, REDESIGN_ID) == []
    assert _outcome_on(fired)["redesign"] == "routed"
    _one_card(fired, REDESIGN_ID)


def test_a_no_plan_reads_its_reason_scoped_to_the_kept_set_and_the_trim_on_the_wire(
    tmp_path: Path,
) -> None:
    """Thirteen required stages, all held. The cap keeps twelve, so the search reads no-plan."""
    registry = redesign_fixtures._chain_registry()  # noqa: SLF001
    names = redesign_fixtures._chain_names()  # noqa: SLF001

    data = _listing(_table(tmp_path, _route_world(names), registry), _stated())

    assert _outcome_on(data) == {
        "status": "no-plan",
        "reason": NO_PLAN_REASON,
        "redesign": "routed",
        "trimmed": [names[0]],
    }
    scoped = "it kept" in NO_PLAN_REASON
    assert scoped
    assert _one_card(data, REDESIGN_ID)["reason"] == (
        f"This route runs 0 locked and 13 held recipe(s){NO_UNLOCK}{NOT_CHOSEN}"
    )


def test_an_empty_resource_group_reads_request_malformed_with_no_trim_key(tmp_path: Path) -> None:
    """No search ran, so the offer carries no word on what the bound dropped."""
    registry = redesign_fixtures._registry(  # noqa: SLF001
        [redesign_fixtures._recipe("R_Direct", [SOLVE_ORE_ITEM], [SOLVE_RELIC_ITEM])],  # noqa: SLF001
        resources=(),
    )

    data = _listing(_table(tmp_path, _route_world(("R_Direct",)), registry), _stated())

    assert _outcome_on(data) == {
        "status": "request-malformed",
        "reason": MALFORMED_REASON,
        "redesign": "not-reached",
    }
    assert _cards_of(data, ADOPT_ID) == []
    assert _cards_of(data, REDESIGN_ID) == []


def test_a_save_path_reaches_no_body_and_neither_does_the_world_token(tmp_path: Path) -> None:
    """Every stated body, ranked and routed, against a path the save holds and the token."""
    save_only = redesign_fixtures.SAVE_ONLY_PATH
    model, registry = _three_locked()
    unlocks = replace(model.unlocks, recipes=model.unlocks.recipes | {save_only})
    held = replace(model, unlocks=unlocks)
    table = _table(tmp_path, held, registry)
    listing = table["GET", advice_endpoint.ENDPOINT](_stated())
    card_id = _card_id(_data(listing), REDESIGN_ID)
    derivation = table["GET", advice_endpoint.DERIVATION_ENDPOINT](
        {advice_endpoint.ID_PARAMETER: card_id, **_stated()}
    )
    state = _ask(table, STATE, card_id, _stated())
    bodies = [contract.encode(response.payload) for response in (listing, derivation, state)]

    needles = (save_only.encode("ascii"), held.token.encode("ascii"))
    leaked = sum(1 for body in bodies for needle in needles if needle in body)

    assert leaked == 0
    planted = contract.encode({"status": "ok", "planted": save_only})
    detected = needles[0] in planted
    assert detected


# ---------------------------------------------------------------------------
# Arm 5: every refusal, in its order
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("route", ROUTE_NAMES)
def test_an_unknown_name_beside_the_four_is_400_and_reads_no_provider(
    tmp_path: Path, route: str, control_card: str
) -> None:
    table, counted, source = _counted_table(tmp_path, *_ascent())

    response = _ask(table, route, control_card, {**_stated(), PLANTED: "1"})

    _refused_before_any_provider(
        response, contract.REASON_UNKNOWN_PARAMETER, counted, source, tmp_path
    )


@pytest.mark.parametrize("route", ROUTE_NAMES)
@pytest.mark.parametrize("names", PARTIAL_SETS, ids="+".join)
def test_some_of_the_four_without_the_rest_is_missing_and_reads_no_provider(
    tmp_path: Path, route: str, names: tuple[str, ...], control_card: str
) -> None:
    table, counted, source = _counted_table(tmp_path, *_ascent())
    stated = _stated()

    response = _ask(table, route, control_card, {name: stated[name] for name in names})

    _refused_before_any_provider(
        response, contract.REASON_MISSING_PARAMETER, counted, source, tmp_path
    )


def test_every_partial_set_is_graded() -> None:
    """Counted by hand, so a shrunken sweep cannot pass."""
    assert len(PARTIAL_SETS) == PARTIAL_SET_COUNT


@pytest.mark.parametrize("route", ROUTE_NAMES)
@pytest.mark.parametrize("rate", BAD_RATES)
def test_a_bad_rate_is_invalid_and_reads_no_provider(
    tmp_path: Path, route: str, rate: str, control_card: str
) -> None:
    table, counted, source = _counted_table(tmp_path, *_ascent())

    response = _ask(table, route, control_card, _stated(rate=rate))

    _refused_before_any_provider(
        response, contract.REASON_INVALID_PARAMETER, counted, source, tmp_path
    )


@pytest.mark.parametrize("route", ROUTE_NAMES)
@pytest.mark.parametrize("direction", BAD_DIRECTIONS)
def test_a_bad_direction_is_invalid_and_reads_no_provider(
    tmp_path: Path, route: str, direction: str, control_card: str
) -> None:
    table, counted, source = _counted_table(tmp_path, *_ascent())

    response = _ask(table, route, control_card, _stated(direction=direction))

    _refused_before_any_provider(
        response, contract.REASON_INVALID_PARAMETER, counted, source, tmp_path
    )


@pytest.mark.parametrize("route", ROUTE_NAMES)
@pytest.mark.parametrize("policy", BAD_POLICIES)
def test_a_bad_policy_is_invalid_and_reads_no_provider(
    tmp_path: Path, route: str, policy: str, control_card: str
) -> None:
    table, counted, source = _counted_table(tmp_path, *_ascent())

    response = _ask(table, route, control_card, _stated(policy=policy))

    _refused_before_any_provider(
        response, contract.REASON_INVALID_PARAMETER, counted, source, tmp_path
    )


@pytest.mark.parametrize("route", ROUTE_NAMES)
def test_a_bad_rate_is_400_with_no_save_and_no_install_either(
    tmp_path: Path, route: str, control_card: str
) -> None:
    """The precedent of ``clockspeed/surface/api/solve.py``: the shape first, then the providers."""
    table, counted, source = _counted_table(tmp_path, None, None)

    response = _ask(table, route, control_card, _stated(rate="-1"))

    _refused_before_any_provider(
        response, contract.REASON_INVALID_PARAMETER, counted, source, tmp_path
    )


@pytest.mark.parametrize("route", ROUTE_NAMES)
@pytest.mark.parametrize(
    "target",
    [SOLVE_ORE_ITEM, SOLVE_ROD_ITEM, "Desc_NeverHeardOf_C", "", plan_fixtures.RELIC_FROM_RARE],
    ids=["raw-item", "unmade-item", "unknown-item", "blank", "a-recipe-name"],
)
def test_a_target_off_the_list_is_invalid_after_the_providers_and_computes_nothing(
    tmp_path: Path, route: str, target: str, control_card: str
) -> None:
    model, registry = _ascent()
    listed = target in plan_targets(registry)
    assert not listed
    table, counted, source = _counted_table(tmp_path, model, registry)

    response = _ask(table, route, control_card, _stated(target))

    assert response.http_status == contract.HTTP_BAD_REQUEST
    assert response.payload["reason"] == contract.REASON_INVALID_PARAMETER
    problems = len(contract.contract_problems(response))
    assert problems == 0
    assert counted.reads == ONE_WORLD_AND_ONE_REGISTRY
    assert source.computed == 0
    _state_assert_nothing_written(tmp_path)


@pytest.mark.parametrize("route", ROUTE_NAMES)
@pytest.mark.parametrize(
    ("has_world", "has_registry", "reason", "reads"),
    [
        (False, True, contract.REASON_NO_SAVE, 1),
        (True, False, contract.REASON_NO_GAME_INSTALL, 2),
    ],
    ids=["no-save", "no-install"],
)
def test_a_good_rate_and_an_unknown_target_still_answer_the_missing_inputs_503(
    tmp_path: Path, route: str, has_world: bool, has_registry: bool, reason: str, reads: int
) -> None:
    model, registry = _ascent()
    table, counted, source = _counted_table(
        tmp_path, model if has_world else None, registry if has_registry else None
    )

    response = _ask(table, route, UNKNOWN_CARD_ID, _stated("Desc_NeverHeardOf_C"))

    assert response.http_status == contract.HTTP_UNAVAILABLE
    assert response.payload["reason"] == reason
    assert counted.reads == reads
    assert source.computed == 0


@pytest.mark.parametrize("route", ROUTE_NAMES)
def test_a_corrupt_ledger_on_a_stated_request_is_the_store_refusal(
    tmp_path: Path, route: str, control_card: str
) -> None:
    corrupt = b"{not json"
    (tmp_path / LEDGER_FILENAME).write_bytes(corrupt)
    table = _table(tmp_path, *_ascent())

    response = _ask(table, route, control_card, _stated())

    assert response.http_status == contract.HTTP_UNAVAILABLE
    assert response.payload["reason"] == contract.REASON_ADVICE_STORE_UNREADABLE
    unchanged = (tmp_path / LEDGER_FILENAME).read_bytes() == corrupt
    assert unchanged


def _planted_requests() -> Iterator[tuple[str, dict[str, str]]]:
    """Every shape of refused request, each carrying the planted value somewhere it could echo."""
    yield "unknown-name", {**_stated(), PLANTED: "1"}
    yield "unknown-value", {**_stated(), PLANTED: PLANTED}
    yield "rate", _stated(rate=PLANTED)
    yield "direction", _stated(direction=PLANTED)
    yield "policy", _stated(policy=PLANTED)
    yield "target", _stated(PLANTED)
    yield "partial", {TARGET: PLANTED}


@pytest.mark.parametrize("route", ROUTE_NAMES)
@pytest.mark.parametrize(
    "parameters",
    [parameters for _name, parameters in _planted_requests()],
    ids=[name for name, _parameters in _planted_requests()],
)
def test_no_refusal_reflects_what_it_refused(
    tmp_path: Path, route: str, parameters: dict[str, str], control_card: str
) -> None:
    table = _table(tmp_path, *_ascent())

    response = _ask(table, route, control_card, parameters)

    _state_assert_refused(response, str(response.payload["reason"]), PLANTED)
    _state_assert_nothing_written(tmp_path)


def test_the_reflection_detector_detects_the_planted_value() -> None:
    """The control for the arm above: this needle in a body is seen, so its absence means one."""
    planted = contract.encode({"status": "ok", "planted": PLANTED})
    detected = PLANTED.encode("ascii") in planted
    assert detected


@pytest.mark.parametrize("route", ROUTE_NAMES)
def test_a_refused_request_reaches_no_solve_and_the_good_one_does(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, route: str, control_card: str
) -> None:
    """Every door out of the advisor's plan module refuses, so reaching one cannot be mistaken."""
    redesign_fixtures._refuse_every_door(monkeypatch)  # noqa: SLF001
    table = _table(tmp_path, *_ascent())
    refused = [parameters for _name, parameters in _planted_requests()]
    refused.append(_stated(rate="0"))

    statuses = [_ask(table, route, control_card, parameters).http_status for parameters in refused]

    wrong = sum(1 for status in statuses if status != contract.HTTP_BAD_REQUEST)
    assert wrong == 0
    with pytest.raises(redesign_fixtures._DoorReachedError):  # noqa: SLF001
        _ask(table, route, control_card, _stated())


def test_no_target_reaches_no_solve(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    redesign_fixtures._refuse_every_door(monkeypatch)  # noqa: SLF001
    table = _table(tmp_path, *_ascent())

    data = _listing(table, {})

    assert frozenset(data) == advice_endpoint.DATA_KEYS


@pytest.mark.parametrize(
    ("rate", "exact"),
    [("10", Fraction(10)), ("0.1", Fraction(1, 10)), ("1/3", Fraction(1, 3))],
)
def test_a_stated_rate_reaches_the_request_exact_and_never_through_a_float(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, rate: str, exact: Fraction
) -> None:
    """A tenth through a float would read 3602879701896397/36028797018963968, not one tenth."""
    seen: list[PlanRequest | None] = []

    def spy(*args: Any, **kwargs: Any) -> Advice:
        seen.append(kwargs["plan_request"])
        return advise_world(*args, **kwargs)

    monkeypatch.setattr(providers_module, "advise_world", spy)
    model, registry = _ascent()

    _listing(_table(tmp_path, model, registry), _stated(rate=rate))

    count = len(seen)
    assert count == 1
    request = seen[0]
    assert request is not None
    held = request.targets[SOLVE_RELIC_ITEM]
    assert held == exact
    exact_type = type(held) is Fraction
    assert exact_type
    assert Fraction(0.1) != Fraction(1, 10)


def test_the_request_holds_what_was_stated_and_the_groups_raw_items(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """No surface module chooses a raw item: the group is the only source there is."""
    seen: list[PlanRequest | None] = []

    def spy(*args: Any, **kwargs: Any) -> Advice:
        seen.append(kwargs["plan_request"])
        return advise_world(*args, **kwargs)

    monkeypatch.setattr(providers_module, "advise_world", spy)
    model, registry = _ascent()

    _listing(
        _table(tmp_path, model, registry),
        _stated(SOLVE_RARE_ITEM, direction="buildings", policy="sinkable"),
    )

    request = seen[0]
    assert request is not None
    assert dict(request.targets) == {SOLVE_RARE_ITEM: Fraction(10)}
    assert request.raw_items == registry.resource_items
    assert request.raw_items == (SOLVE_ORE_ITEM,)
    assert request.direction == "buildings"
    assert request.byproduct_policy == "sinkable"


def test_the_source_doors_read_no_clock_and_no_store(tmp_path: Path) -> None:
    """The two checking doors run before and beside the providers, and touch neither store."""
    reads: list[int] = []

    def clock() -> int:
        reads.append(NOW)
        return NOW

    source = StoreAdviceSource(tmp_path, clock=clock)
    parameters = source.plan_parameters(rate="10", direction="raw", byproduct_policy="balanced")
    assert parameters is not None
    _model, registry = _ascent()

    request = source.plan_request(registry, SOLVE_RELIC_ITEM, parameters)

    assert request is not None
    off_list = source.plan_request(registry, SOLVE_ORE_ITEM, parameters)
    assert off_list is None
    refused = source.plan_parameters(rate="0", direction="raw", byproduct_policy="balanced")
    assert refused is None
    assert reads == []
    _state_assert_nothing_written(tmp_path)


# ---------------------------------------------------------------------------
# Arm 6: byte-same, two requests and two processes
# ---------------------------------------------------------------------------


def stated_bodies(directory: Path) -> str:
    """Every stated body over the two worlds where an order could come from a set.

    Public because :data:`CHILD_SOURCE` imports it, so the children build this very world.

    Args:
        directory: Where the advice stores live. Empty, and nothing here writes one.

    Returns:
        The listing and the derivation of a ranked world holding save-only unlock paths and a
        recipe past the cap, then of a world whose route holds several recipes, as text.
    """
    save_only = redesign_fixtures.SAVE_ONLY_PATH
    ranked = plan_fixtures._model(  # noqa: SLF001
        (*plan_fixtures._padded_paths(), save_only, save_only + "A", save_only + "B")  # noqa: SLF001
    )
    routed = _route_world((redesign_fixtures.HELD_STAGE, "R_B1", "R_B2"))
    worlds = (
        (ranked, plan_fixtures._padded_registry(), ADOPT_ID),  # noqa: SLF001
        (routed, redesign_fixtures._three_locked_registry(), REDESIGN_ID),  # noqa: SLF001
    )
    bodies: list[bytes] = []
    for model, registry, rule_id in worlds:
        table = _table(directory, model, registry)
        listing = table["GET", advice_endpoint.ENDPOINT](_stated())
        derivation = table["GET", advice_endpoint.DERIVATION_ENDPOINT](
            {advice_endpoint.ID_PARAMETER: _card_id(_data(listing), rule_id), **_stated()}
        )
        bodies.extend(contract.encode(response.payload) for response in (listing, derivation))
    return b"\n".join(bodies).decode("ascii")


def test_two_requests_with_no_ledger_write_between_them_are_byte_same(tmp_path: Path) -> None:
    model, registry = _ascent()
    table = _table(tmp_path, model, registry)
    card_id = _card_id(_listing(table, _stated()), ADOPT_ID)

    listings = [
        contract.encode(table["GET", advice_endpoint.ENDPOINT](_stated()).payload) for _ in range(2)
    ]
    derivations = [
        contract.encode(_ask(table, DERIVATION, card_id, _stated()).payload) for _ in range(2)
    ]

    same_listing = listings[0] == listings[1]
    assert same_listing
    same_derivation = derivations[0] == derivations[1]
    assert same_derivation
    _state_assert_nothing_written(tmp_path)


def test_a_second_table_over_the_same_world_answers_byte_same(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    first.mkdir()
    second.mkdir()

    same = stated_bodies(first) == stated_bodies(second)

    assert same
    _state_assert_nothing_written(first)
    _state_assert_nothing_written(second)


def test_a_ledger_write_between_two_requests_moves_the_body(tmp_path: Path) -> None:
    """The control for byte-same: the state on a body is read, so the arm above can go red."""
    model, registry = _ascent()
    table = _table(tmp_path, model, registry)
    before = table["GET", advice_endpoint.ENDPOINT](_stated())
    card_id = _card_id(_data(before), ADOPT_ID)

    _data(_ask(table, STATE, card_id, _stated()))
    after = table["GET", advice_endpoint.ENDPOINT](_stated())

    moved = contract.encode(before.payload) != contract.encode(after.payload)
    assert moved


def test_two_processes_under_different_hash_seeds_answer_byte_same(tmp_path: Path) -> None:
    """A set deciding an order is stable within a process, so this takes two."""
    printed: list[str] = []
    for seed in HASH_SEEDS:
        directory = tmp_path / seed
        directory.mkdir()
        child = subprocess.run(
            [sys.executable, "-s", "-B", "-c", CHILD_SOURCE, str(directory)],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=CHILD_TIMEOUT_SECONDS,
            env={"PYTHONHASHSEED": seed, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"},
            check=False,
        )
        # Bound to a plain int first: pytest would otherwise render the whole
        # CompletedProcess, whose argv holds absolute paths.
        exit_code = child.returncode
        assert exit_code == 0, f"the child under PYTHONHASHSEED={seed} failed"
        printed.append(child.stdout.strip())
        _state_assert_nothing_written(directory)

    opened = printed[0].startswith("{")
    assert opened
    agreed = printed[0] == printed[1]
    assert agreed


def test_the_hash_seed_bodies_hold_what_a_set_could_order(tmp_path: Path) -> None:
    """The control for the arm above: a trim, a route and held recipes are on those bodies."""
    text = stated_bodies(tmp_path)

    trimmed = '"trimmed":["R_Pad9"]' in text
    assert trimmed
    # Holding R_B1 and R_B2 moves the route to R_B, by hand in test_plan_redesign.py, and the
    # encoded body escapes each quote.
    route_held = 'plan.redesign.held = (\\"R_B2\\", \\"R_B1\\")' in text
    assert route_held
    both_rules = '"rule_id":"plan.adopt"' in text and '"rule_id":"plan.redesign"' in text
    assert both_rules


# ---------------------------------------------------------------------------
# The seam the stated path crosses
# ---------------------------------------------------------------------------


def _run_time_imports(node: ast.AST) -> Iterator[str]:
    """Every module a tree imports when it runs: an ``if TYPE_CHECKING`` block names types only."""
    for child in ast.iter_child_nodes(node):
        if (
            isinstance(child, ast.If)
            and isinstance(child.test, ast.Name)
            and child.test.id == "TYPE_CHECKING"
        ):
            continue
        if isinstance(child, ast.Import):
            yield from (alias.name for alias in child.names)
        elif isinstance(child, ast.ImportFrom) and child.module is not None:
            yield child.module
        else:
            yield from _run_time_imports(child)


def test_the_run_time_import_reader_tells_a_typing_import_from_a_real_one() -> None:
    typing_only = "if TYPE_CHECKING:\n    from clockspeed.advisor.plans import PlanRequest\n"
    real = "def f():\n    from clockspeed.advisor.plans import plan_offer\n"
    assert frozenset(_run_time_imports(ast.parse(typing_only))) == frozenset()
    assert frozenset(_run_time_imports(ast.parse(real))) == {"clockspeed.advisor.plans"}


def test_the_advice_endpoint_reaches_the_advisor_only_through_the_source() -> None:
    """The advisor import stays in ``providers.py``: this module names its models for typing."""
    tree = ast.parse((SURFACE_ROOT / "api" / "advice.py").read_bytes().decode("ascii"))
    imported = frozenset(_run_time_imports(tree))
    assert imported == {"__future__", "typing", "clockspeed.surface.api"}


def test_the_registry_endpoint_imports_the_data_layers_one_function() -> None:
    tree = ast.parse((SURFACE_ROOT / "api" / "registry.py").read_bytes().decode("ascii"))
    imported = frozenset(_run_time_imports(tree))
    assert imported == {
        "__future__",
        "typing",
        "clockspeed.surface.api",
        "clockspeed.data.registry",
    }
    # Named one at a time, so the build step this module may not run stays out of reach.
    froms = [
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module == "clockspeed.data.registry"
        for alias in node.names
    ]
    assert "plan_targets" in froms
    assert "build_registry" not in froms
