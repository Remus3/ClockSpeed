"""CS-1373: the surface states a plan for a schematic, through a concrete catalog source.

Two halves, both over synthetic data with no install and no save:

- :class:`clockspeed.surface.providers.InstalledSchematicSource` reads the docs file
  :class:`~clockspeed.surface.providers.InstalledRegistryProvider` reads, and publishes None
  on each failure that provider answers None on;
- the advice routes admit ``schematic`` with ``direction`` and ``byproduct_policy`` in place of
  ``target`` and ``rate``, refuse in the order the clause names (case 3), and hand the advisor
  ONE request for the schematic's whole cost.

The rates are literals: 240 Relic and 120 Rare over a two hour budget spelled here.
"""

from __future__ import annotations

import ast
import json
from fractions import Fraction
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Final

import pytest

from clockspeed.advisor.advise import Advice
from clockspeed.advisor.cards import card_id
from clockspeed.advisor.plans import SchematicRequest
from clockspeed.data import version
from clockspeed.data.schematics import CostLine, Schematic, SchematicCatalog
from clockspeed.solve.optimize import OBJECTIVE_RAW
from clockspeed.solve.ratio import BYPRODUCT_BALANCED
from clockspeed.surface import providers
from clockspeed.surface.api import advice as advice_endpoint
from clockspeed.surface.api import contract, routes
from clockspeed.surface.providers import InstalledSchematicSource
from tests.advisor import test_plan_world as pw
from tests.data import synthetic
from tests.solve.synthetic import SOLVE_RARE_ITEM, SOLVE_RELIC_ITEM

if TYPE_CHECKING:
    from collections.abc import Mapping

    from clockspeed.data.registry import Registry

SCHEMATIC: Final = "Schematic_CsWireTierTwo_C"
MILESTONE_KIND: Final = "EST_Milestone"
TWO_HOURS: Final = 120
RELIC_RATE: Final = Fraction(240, TWO_HOURS)
RARE_RATE: Final = Fraction(120, TWO_HOURS)

#: The parameter names this slice adds, spelled here independently of the module.
SCHEMATIC_PARAMETER: Final = "schematic"

STATE_ENDPOINT: Final = "/api/advice/<id>/state"
DERIVATION_ENDPOINT: Final = "/api/advice/<id>/derivation"
ENDPOINT: Final = "/api/advice"


def _entry(name: str, cost: list[tuple[str, int]]) -> dict[str, Any]:
    return {
        synthetic.KEY_CLASS_NAME: name,
        "mDisplayName": "Synthetic",
        "mCost": synthetic.amount_blob(cost),
        "mTechTier": "2",
        "mType": "EST_Milestone",
        "mSchematicDependencies": [],
    }


def _docs_bytes() -> bytes:
    group = {
        synthetic.KEY_NATIVE_CLASS: (
            f"/Script/CoreUObject.Class'/Script/FactoryGame.{synthetic.SCHEMATIC_GROUP}'"
        ),
        synthetic.KEY_CLASSES: [
            _entry(SCHEMATIC, [(SOLVE_RELIC_ITEM, 240), (SOLVE_RARE_ITEM, 120)])
        ],
    }
    return json.dumps([group]).encode("utf-16")


def _catalog() -> SchematicCatalog:
    held = Schematic(
        class_name=SCHEMATIC,
        tech_tier=2,
        type_token=MILESTONE_KIND,
        cost=(CostLine(SOLVE_RELIC_ITEM, Fraction(240)), CostLine(SOLVE_RARE_ITEM, Fraction(120))),
        purchase_dependencies=(),
        phase_dependency=None,
        dependencies_complete=True,
        asset_path="/Game/Synthetic/Wire.Wire",
    )
    return SchematicCatalog(
        schematics=MappingProxyType({SCHEMATIC: held}),
        warnings=(),
        entries_offered=1,
        entries_skipped=0,
        costs_parsed=1,
        costs_flagged=0,
    )


class _Catalogs:
    """A catalog provider that counts its reads."""

    def __init__(self, held: SchematicCatalog | None) -> None:
        self._held = held
        self.reads = 0

    def catalog(self) -> SchematicCatalog | None:
        self.reads += 1
        return self._held


class _Worlds:
    """A world provider that may hold none."""

    def __init__(self, held: object | None) -> None:
        self._held = held

    def world(self) -> Any:
        return self._held


class _Registries:
    """A registry provider that may hold none."""

    def __init__(self, held: Registry | None) -> None:
        self._held = held

    def registry(self) -> Registry | None:
        return self._held


def _table(
    tmp_path: Path,
    *,
    world: object | None = "world",
    registry: Registry | None = None,
    catalogs: _Catalogs | None = None,
    unlocked: bool = True,
) -> Mapping[tuple[str, str], contract.Handler]:
    model = pw._model(pw.ASCENT_PATHS if unlocked else ())  # noqa: SLF001
    held = model if world == "world" else world
    source = providers.StoreAdviceSource(tmp_path, clock=lambda: pw.NOW)
    built = routes.build_routes(
        _Worlds(held),
        _Registries(pw._registry() if registry is None else registry),  # noqa: SLF001
        source,
        _Catalogs(_catalog()) if catalogs is None else catalogs,
    )
    return {(route.method, route.template): route.handler for route in built}


def _query(**overrides: str | None) -> dict[str, str]:
    base: dict[str, str] = {
        SCHEMATIC_PARAMETER: SCHEMATIC,
        advice_endpoint.DIRECTION_PARAMETER: OBJECTIVE_RAW,
        advice_endpoint.BYPRODUCT_POLICY_PARAMETER: BYPRODUCT_BALANCED,
    }
    for key, value in overrides.items():
        if value is None:
            base.pop(key, None)
        else:
            base[key] = value
    return base


def _reason(response: contract.Response) -> object:
    return response.payload.get("reason")


def _card_ids(response: contract.Response) -> list[str]:
    data = response.payload["data"]
    assert isinstance(data, dict)
    return [card["id"] for card in data["cards"] if card["rule_id"].startswith("plan.")]


# --- InstalledSchematicSource ----------------------------------------------------------


def test_the_source_reads_the_docs_file_the_registry_provider_reads(tmp_path: Path) -> None:
    read: list[Path] = []

    def reading(path: Path) -> bytes:
        read.append(path)
        return _docs_bytes()

    found = InstalledSchematicSource(
        find_install=lambda: (tmp_path, "test"), read_docs_bytes=reading
    ).catalog()

    assert found is not None
    assert set(found.schematics) == {SCHEMATIC}
    assert read == [tmp_path.joinpath(*version.DOCS_RELATIVE_PARTS)]


def test_a_text_reader_builds_the_same_catalog(tmp_path: Path) -> None:
    found = InstalledSchematicSource(
        find_install=lambda: (tmp_path, "test"),
        read_docs=lambda _path: _docs_bytes().decode("utf-16"),
    ).catalog()

    assert found is not None
    assert set(found.schematics) == {SCHEMATIC}


def test_no_install_answers_none() -> None:
    assert InstalledSchematicSource(find_install=lambda: (None, "none")).catalog() is None


def test_a_failing_install_lookup_answers_none() -> None:
    def failing() -> tuple[Path | None, str]:
        raise OSError

    assert InstalledSchematicSource(find_install=failing).catalog() is None


@pytest.mark.parametrize("failure", [OSError, ValueError], ids=["os", "value"])
def test_a_byte_reader_that_fails_answers_none(tmp_path: Path, failure: type[Exception]) -> None:
    def refusing(_path: Path) -> bytes:
        raise failure

    source = InstalledSchematicSource(
        find_install=lambda: (tmp_path, "test"), read_docs_bytes=refusing
    )

    assert source.catalog() is None


@pytest.mark.parametrize("failure", [OSError, ValueError], ids=["os", "value"])
def test_a_text_reader_that_fails_answers_none(tmp_path: Path, failure: type[Exception]) -> None:
    def refusing(_path: Path) -> str:
        raise failure

    source = InstalledSchematicSource(find_install=lambda: (tmp_path, "test"), read_docs=refusing)

    assert source.catalog() is None


def test_bytes_that_will_not_parse_answer_none(tmp_path: Path) -> None:
    source = InstalledSchematicSource(
        find_install=lambda: (tmp_path, "test"), read_docs_bytes=lambda _p: b"not a docs document"
    )

    assert source.catalog() is None


def test_a_byte_reader_returning_text_raises_and_never_answers_none(tmp_path: Path) -> None:
    source = InstalledSchematicSource(
        find_install=lambda: (tmp_path, "test"),
        read_docs_bytes=lambda _p: "text",  # type: ignore[arg-type,return-value]
    )

    with pytest.raises(TypeError):
        source.catalog()


def test_the_source_opens_no_second_file_path() -> None:
    """The class reads through the data layer's own decode and normalize, nothing else."""
    tree = ast.parse(Path(providers.__file__).read_text(encoding="ascii"))
    cls = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef) and node.name == "InstalledSchematicSource"
    )
    called = {node.attr for node in ast.walk(cls) if isinstance(node, ast.Attribute)}
    assert "normalize_schematics" in called


# --- case 3: the refusals, in the clause's order -----------------------------------------


@pytest.mark.parametrize("beside", ["target", "rate"])
@pytest.mark.parametrize("endpoint", [ENDPOINT, DERIVATION_ENDPOINT])
def test_a_rate_or_a_target_beside_a_schematic_is_invalid_parameter(
    tmp_path: Path, beside: str, endpoint: str
) -> None:
    table = _table(tmp_path)
    handler = table[("GET", endpoint)]
    query = _query(**{beside: SOLVE_RELIC_ITEM if beside == "target" else "1"})
    if endpoint == DERIVATION_ENDPOINT:
        query["id"] = "x"

    refused = handler(query)

    assert refused.http_status == contract.HTTP_BAD_REQUEST
    assert _reason(refused) == contract.REASON_INVALID_PARAMETER


def test_a_rate_beside_a_schematic_refuses_before_any_provider_is_read(tmp_path: Path) -> None:
    catalogs = _Catalogs(_catalog())
    table = _table(tmp_path, world=None, catalogs=catalogs)

    refused = table[("GET", ENDPOINT)](_query(rate="1"))

    assert _reason(refused) == contract.REASON_INVALID_PARAMETER
    assert catalogs.reads == 0


def test_a_schematic_the_catalog_does_not_hold_is_invalid_parameter(tmp_path: Path) -> None:
    table = _table(tmp_path)

    refused = table[("GET", ENDPOINT)](_query(schematic="Schematic_NeverDeclared_C"))

    assert refused.http_status == contract.HTTP_BAD_REQUEST
    assert _reason(refused) == contract.REASON_INVALID_PARAMETER


def test_an_unknown_schematic_is_refused_after_both_providers(tmp_path: Path) -> None:
    unknown = _query(schematic="Schematic_NeverDeclared_C")

    no_world = _table(tmp_path, world=None)[("GET", ENDPOINT)](unknown)
    assert no_world.http_status == contract.HTTP_UNAVAILABLE
    assert _reason(no_world) == contract.REASON_NO_SAVE

    class _NoRegistry:
        def registry(self) -> None:
            return None

    built = routes.build_routes(
        _Worlds(pw._model(pw.ASCENT_PATHS)),  # noqa: SLF001
        _NoRegistry(),
        providers.StoreAdviceSource(tmp_path, clock=lambda: pw.NOW),
        _Catalogs(_catalog()),
    )
    handler = next(r.handler for r in built if r.template == ENDPOINT)
    no_install = handler(unknown)
    assert no_install.http_status == contract.HTTP_UNAVAILABLE
    assert _reason(no_install) == contract.REASON_NO_GAME_INSTALL


def test_a_source_publishing_no_catalog_is_no_game_install(tmp_path: Path) -> None:
    table = _table(tmp_path, catalogs=_Catalogs(None))

    refused = table[("GET", ENDPOINT)](_query())

    assert refused.http_status == contract.HTTP_UNAVAILABLE
    assert _reason(refused) == contract.REASON_NO_GAME_INSTALL


def test_a_direction_or_policy_missing_beside_a_schematic_is_missing_parameter(
    tmp_path: Path,
) -> None:
    table = _table(tmp_path)

    for missing in (
        advice_endpoint.DIRECTION_PARAMETER,
        advice_endpoint.BYPRODUCT_POLICY_PARAMETER,
    ):
        refused = table[("GET", ENDPOINT)](_query(**{missing: None}))
        assert refused.http_status == contract.HTTP_BAD_REQUEST
        assert _reason(refused) == contract.REASON_MISSING_PARAMETER


def test_a_direction_the_advisor_refuses_is_invalid_parameter(tmp_path: Path) -> None:
    table = _table(tmp_path)

    refused = table[("GET", ENDPOINT)](_query(direction="sideways"))

    assert _reason(refused) == contract.REASON_INVALID_PARAMETER


# --- case 1 on the wire: one request ---------------------------------------------------------


def test_a_schematic_hands_the_advisor_one_request_holding_every_cost_item(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    seen: list[Any] = []
    real = providers.advise_world

    def spy(*args: Any, **kwargs: Any) -> Advice:
        seen.append(kwargs["plan_request"])
        return real(*args, **kwargs)

    monkeypatch.setattr(providers, "advise_world", spy)
    table = _table(tmp_path)

    response = table[("GET", ENDPOINT)](_query())

    assert response.http_status == contract.HTTP_OK
    assert len(seen) == 1
    request = seen[0]
    assert type(request) is SchematicRequest
    assert dict(request.targets) == {SOLVE_RELIC_ITEM: RELIC_RATE, SOLVE_RARE_ITEM: RARE_RATE}
    assert len(_card_ids(response)) == 1
    data = response.payload["data"]
    assert isinstance(data, dict)
    assert data["plan_outcome"]["status"] == "ranked"


def test_an_unplannable_schematic_serves_its_reason_word_and_no_card(tmp_path: Path) -> None:
    empty = Schematic(
        class_name=SCHEMATIC,
        tech_tier=2,
        type_token=MILESTONE_KIND,
        cost=(),
        purchase_dependencies=(),
        phase_dependency=None,
        dependencies_complete=True,
    )
    catalogs = _Catalogs(
        SchematicCatalog(
            schematics=MappingProxyType({SCHEMATIC: empty}),
            warnings=(),
            entries_offered=1,
            entries_skipped=0,
            costs_parsed=1,
            costs_flagged=0,
        )
    )
    table = _table(tmp_path, catalogs=catalogs)

    response = table[("GET", ENDPOINT)](_query())

    assert response.http_status == contract.HTTP_OK
    assert _card_ids(response) == []
    data = response.payload["data"]
    assert isinstance(data, dict)
    outcome = data["plan_outcome"]
    assert outcome["status"] == "schematic-unplannable"
    assert outcome["reason"] == "empty-cost"
    assert set(outcome) <= advice_endpoint.PLAN_OUTCOME_KEYS


def test_an_item_off_plan_targets_is_served_by_name(tmp_path: Path) -> None:
    raw = Schematic(
        class_name=SCHEMATIC,
        tech_tier=2,
        type_token=MILESTONE_KIND,
        cost=(CostLine(pw.SOLVE_ORE_ITEM, Fraction(60)),),
        purchase_dependencies=(),
        phase_dependency=None,
        dependencies_complete=True,
    )
    catalogs = _Catalogs(
        SchematicCatalog(
            schematics=MappingProxyType({SCHEMATIC: raw}),
            warnings=(),
            entries_offered=1,
            entries_skipped=0,
            costs_parsed=1,
            costs_flagged=0,
        )
    )
    table = _table(tmp_path, catalogs=catalogs)

    response = table[("GET", ENDPOINT)](_query())

    data = response.payload["data"]
    assert isinstance(data, dict)
    assert data["plan_outcome"]["reason"] == f"item-not-plannable: {pw.SOLVE_ORE_ITEM}"


# --- the derivation and state routes admit the same statement ---------------------------------


def test_the_derivation_route_serves_the_schematic_card(tmp_path: Path) -> None:
    table = _table(tmp_path)
    listing = table[("GET", ENDPOINT)](_query())
    ids = _card_ids(listing)
    assert len(ids) == 1

    derived = table[("GET", DERIVATION_ENDPOINT)]({**_query(), "id": ids[0]})

    assert derived.http_status == contract.HTTP_OK
    data = derived.payload["data"]
    assert isinstance(data, dict)
    assert SCHEMATIC in str(data["derivation"])


def test_the_state_route_records_the_schematic_card(tmp_path: Path) -> None:
    table = _table(tmp_path)
    listing = table[("GET", ENDPOINT)](_query())
    ids = _card_ids(listing)

    recorded = table[("POST", STATE_ENDPOINT)]({**_query(), "id": ids[0], "state": "pinned"})

    assert recorded.http_status == contract.HTTP_OK
    again = table[("GET", ENDPOINT)](_query())
    data = again.payload["data"]
    assert isinstance(data, dict)
    states = {card["id"]: card["state"] for card in data["cards"]}
    assert states[ids[0]] == "pinned"


def test_the_card_id_has_the_schematic_as_its_milestone_on_the_wire(tmp_path: Path) -> None:
    table = _table(tmp_path)

    ids = _card_ids(table[("GET", ENDPOINT)](_query()))

    subject = f"plan:{SOLVE_RARE_ITEM}+{SOLVE_RELIC_ITEM}"
    assert ids == [card_id("plan.adopt", subject, SCHEMATIC)]


def test_an_item_statement_still_needs_the_four_and_reaches_no_catalog(tmp_path: Path) -> None:
    catalogs = _Catalogs(_catalog())
    table = _table(tmp_path, catalogs=catalogs)

    item = table[("GET", ENDPOINT)](
        {
            advice_endpoint.TARGET_PARAMETER: SOLVE_RELIC_ITEM,
            advice_endpoint.RATE_PARAMETER: "10",
            advice_endpoint.DIRECTION_PARAMETER: OBJECTIVE_RAW,
            advice_endpoint.BYPRODUCT_POLICY_PARAMETER: BYPRODUCT_BALANCED,
        }
    )

    assert item.http_status == contract.HTTP_OK
    assert catalogs.reads == 0


# --- production wiring: the installed source is what a server serves with ----------------------


class _SpySource(_Catalogs):
    """A stand-in for the installed source, built with no arguments, counting its reads."""

    built: list[_SpySource] = []  # noqa: RUF012 - reset by each arm that reads it

    def __init__(self) -> None:
        super().__init__(_catalog())
        type(self).built.append(self)


def test_build_routes_with_no_schematics_serves_the_installed_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Left unbound, the route table must build the installed source and ask it for the catalog.

    A default that left the catalog unbound would answer every schematic request 503, which
    only a table built WITHOUT a catalog argument can show.
    """
    _SpySource.built = []
    monkeypatch.setattr(routes, "InstalledSchematicSource", _SpySource)
    source = providers.StoreAdviceSource(tmp_path, clock=lambda: pw.NOW)
    built = routes.build_routes(
        _Worlds(pw._model(pw.ASCENT_PATHS)),  # noqa: SLF001
        _Registries(pw._registry()),  # noqa: SLF001
        source,
    )
    listing = next(route.handler for route in built if route.template == ENDPOINT)

    response = listing(_query())

    assert response.http_status == contract.HTTP_OK
    made = len(_SpySource.built)
    assert made == 1
    assert _SpySource.built[0].reads == 1


def test_the_default_route_table_binds_the_real_installed_source() -> None:
    """The table the server module builds reads its catalog from the real installed source."""
    bound = [
        cell.cell_contents
        for route in routes.ROUTES
        if route.template == ENDPOINT
        for cell in (route.handler.__closure__ or ())
        if isinstance(cell.cell_contents, InstalledSchematicSource)
    ]
    count = len(bound)
    assert count == 1


def test_main_builds_its_routes_with_the_installed_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """``main`` hands the route build an InstalledSchematicSource, and starts no listener."""
    from clockspeed.surface import __main__ as entry  # noqa: PLC0415

    seen: dict[str, object] = {}
    real = entry.build_routes

    def recording(*args: Any, **kwargs: Any) -> Any:
        seen.update(kwargs)
        return real(*args, **kwargs)

    def not_serving(*_args: object, **_kwargs: object) -> int:
        return 0

    monkeypatch.setattr(entry, "build_routes", recording)
    monkeypatch.setattr(entry.server, "run", not_serving)

    code = entry.main(["--port", "8999", "--cert-dir", str(tmp_path), entry.NO_WORLD_FLAG])

    assert code == 0
    wired = isinstance(seen.get("schematics"), InstalledSchematicSource)
    assert wired
