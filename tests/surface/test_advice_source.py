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
from pathlib import Path
from typing import TYPE_CHECKING, Final

from clockspeed.advisor.ledger import (
    LEDGER_FILENAME,
    MUTES_FILENAME,
    CardState,
    Ledger,
    MuteStore,
)
from clockspeed.advisor.rules import power
from clockspeed.surface.api import advice as advice_endpoint
from clockspeed.surface.api import contract, health, pending, routes
from clockspeed.surface.providers import StoreAdviceSource
from tests.advisor import test_world_advice as world_fixtures
from tests.surface import test_map as map_fixtures

if TYPE_CHECKING:
    from collections.abc import Mapping

    from clockspeed.advisor.advise import Advice

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


def _table(directory: Path) -> Mapping[tuple[str, str], contract.Handler]:
    built = routes.build_routes(
        map_fixtures._Worlds(world_fixtures.gap_world()),  # noqa: SLF001
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


def test_the_state_route_stays_blocked_on_cs_1269() -> None:
    assert pending.BLOCKERS[pending.ADVICE_STATE_ENDPOINT] == "CS-1269"
