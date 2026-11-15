"""CS-1374: ``StoreAdviceSource`` hands the schematic source on, and reads nothing itself.

The surface computes nothing here. :class:`~clockspeed.surface.providers.StoreAdviceSource`
carries a schematic source to the advisor, which asks it only where it derives a route. The
join, the order and the preferred set are ``tests/advisor/test_plan_redesign_unlocks.py``'s.
"""

from __future__ import annotations

from pathlib import Path

from clockspeed.advisor.advise import Advice
from clockspeed.advisor.rules.plan import IN_REDESIGN_UNLOCKS, RedesignUnlocks
from clockspeed.advisor.trace import StepKind
from clockspeed.data.schematics import SchematicCatalog, normalize_schematics
from clockspeed.surface.providers import InstalledSchematicSource, StoreAdviceSource
from tests.advisor import test_plan_redesign as worlds
from tests.data.test_schematics import schematic_document, schematic_entry

NOW = 1000


class _Source:
    """A schematic source that counts how often it is asked."""

    def __init__(self, catalog: SchematicCatalog | None) -> None:
        self._catalog = catalog
        self.calls = 0

    def catalog(self) -> SchematicCatalog | None:
        """Publish the catalog, and count the ask."""
        self.calls += 1
        return self._catalog


def _no_plan_advice(source: _Source, directory: Path) -> Advice | None:
    """The advice of a world that reads no-plan, through the surface's own source."""
    registry = worlds._three_locked_registry()  # noqa: SLF001
    request = worlds._request(registry)  # noqa: SLF001
    advising = StoreAdviceSource(directory, clock=lambda: NOW, schematics=source)
    return advising.advice(
        worlds._model((worlds.HELD_STAGE,)),  # noqa: SLF001
        registry,
        plan_request=request,
    )


def _unlock_read_types(advice: Advice) -> list[type]:
    """The type of each route-unlocks value the redesign traces read, so no value is rendered."""
    return [
        type(step.value)
        for trace in advice.traces
        if trace.rule_id == "plan.redesign"
        for step in trace.steps
        if step.kind is StepKind.INPUT_READ and step.subject == IN_REDESIGN_UNLOCKS
    ]


def test_the_source_it_was_given_reaches_the_advisors_route_unlocks(tmp_path: Path) -> None:
    catalog = normalize_schematics(schematic_document([schematic_entry("Schematic_One_C")]))
    source = _Source(catalog)

    advice = _no_plan_advice(source, tmp_path)

    assert advice is not None
    types = _unlock_read_types(advice)
    assert source.calls == 1
    assert types == [RedesignUnlocks]


def test_construction_reads_nothing_and_the_default_is_the_installed_source() -> None:
    source = _Source(None)

    StoreAdviceSource(schematics=source)
    default = StoreAdviceSource()

    assert source.calls == 0
    assert type(default._schematics) is InstalledSchematicSource  # noqa: SLF001


def test_a_call_with_no_target_never_asks_the_source(tmp_path: Path) -> None:
    source = _Source(None)
    advising = StoreAdviceSource(tmp_path, clock=lambda: NOW, schematics=source)

    advising.advice(worlds._model(()), worlds._three_locked_registry())  # noqa: SLF001

    assert source.calls == 0
