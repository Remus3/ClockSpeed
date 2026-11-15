"""CS-1373: a plan may be stated for a schematic, and its cost items plan as one route.

Graded here, case by case, against CS-1373's acceptance in ``docs/item_notes/phase5.md``.
Cases 1, 2, 4 and 5 live here, through the advisor's own door; case 3 and the wire live in
``tests/surface/test_schematic_source.py``.

EVERY FIGURE IS A LITERAL WORKED HERE, NEVER READ BACK. The synthetic schematic costs 240
Relic and 120 Rare, and the completion budget is two hours, so the required rates are 2 and
1 a minute. Those are written below as ``Fraction(240, 120)`` and ``Fraction(120, 120)`` with
the 120 spelled in THIS file, because an expectation computed from the constant under test
moves with it and could never redden when the budget moves.

THE FIXTURE is the ascent world of ``tests/advisor/test_plan_world.py`` (Ore raw, Rare from
Ore, Relic from Rare or from Ore directly), so a schematic costing Relic and Rare plans over
recipes a world can hold. A catalog is hand-built from :class:`clockspeed.data.schematics.Schematic`
values: no install and no save is read, and no slice of real game data is checked in.
"""

from __future__ import annotations

import dataclasses
from fractions import Fraction
from types import MappingProxyType
from typing import TYPE_CHECKING, Final

import pytest

from clockspeed.advisor import plans as plans_module
from clockspeed.advisor.advise import Advice, advise_world
from clockspeed.advisor.cards import Card, card_id
from clockspeed.advisor.ledger import Ledger, MuteStore
from clockspeed.advisor.plans import (
    PlanRequest,
    SchematicRequest,
    plan_offer,
    schematic_parameters,
    schematic_request_from,
)
from clockspeed.data.schematics import CostLine, Schematic, SchematicCatalog
from clockspeed.progress import milestones
from clockspeed.solve.optimize import OBJECTIVE_RAW
from clockspeed.solve.ratio import BYPRODUCT_BALANCED
from tests.advisor import test_plan_world as pw
from tests.advisor.build_fixtures import docs_pin, game_pin
from tests.solve.synthetic import SOLVE_ORE_ITEM, SOLVE_RARE_ITEM, SOLVE_RELIC_ITEM

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping
    from pathlib import Path

    from clockspeed.data.registry import Registry
    from clockspeed.save.world import WorldModel

#: The completion budget in minutes, spelled here as the oracle.
TWO_HOURS: Final = 120

#: The schematic these arms plan, and its tier.
SCHEMATIC: Final = "Schematic_CsTierTwo_C"
MILESTONE_KIND: Final = "EST_Milestone"
TIER: Final = 2

#: What it costs, and so the rates a minute that complete it inside the budget.
RELIC_COST: Final = 240
RARE_COST: Final = 120
RELIC_RATE: Final = Fraction(RELIC_COST, TWO_HOURS)
RARE_RATE: Final = Fraction(RARE_COST, TWO_HOURS)

#: The closed vocabulary this slice adds, spelled here so a rename reddens here.
UNPLANNABLE: Final = "schematic-unplannable"
EMPTY_COST: Final = "empty-cost"
COST_UNREADABLE: Final = "cost-unreadable"
NONPOSITIVE_COST: Final = "nonpositive-cost"
UNRESOLVED_COST_ITEM: Final = "unresolved-cost-item"
ITEM_NOT_PLANNABLE: Final = "item-not-plannable"

#: A cost item the registry does not hold.
GHOST_ITEM: Final = "Desc_CsGhost_C"

ADOPT: Final = "plan.adopt"
REDESIGN: Final = "plan.redesign"


def _schematic(cost: Iterable[tuple[str, int]] | None, *, name: str = SCHEMATIC) -> Schematic:
    """One hand-built schematic."""
    lines = None if cost is None else tuple(CostLine(item, Fraction(n)) for item, n in cost)
    return Schematic(
        class_name=name,
        tech_tier=TIER,
        type_token=MILESTONE_KIND,
        cost=lines,
        purchase_dependencies=(),
        phase_dependency=None,
        dependencies_complete=True,
        asset_path=f"/Game/Synthetic/{name}.{name}",
    )


def _catalog(*schematics: Schematic) -> SchematicCatalog:
    """A catalog holding exactly these schematics."""
    return SchematicCatalog(
        schematics=MappingProxyType({s.class_name: s for s in schematics}),
        warnings=(),
        entries_offered=len(schematics),
        entries_skipped=0,
        costs_parsed=len(schematics),
        costs_flagged=0,
    )


def _two_item_catalog() -> SchematicCatalog:
    return _catalog(_schematic([(SOLVE_RELIC_ITEM, RELIC_COST), (SOLVE_RARE_ITEM, RARE_COST)]))


def _parameters() -> plans_module.SchematicParameters:
    found = schematic_parameters(direction=OBJECTIVE_RAW, byproduct_policy=BYPRODUCT_BALANCED)
    assert found is not None
    return found


def _request(catalog: SchematicCatalog, model: WorldModel, registry: Registry) -> SchematicRequest:
    found = schematic_request_from(catalog, registry, model.unlocks, SCHEMATIC, _parameters())
    assert found is not None
    return found


def _advise(
    directory: Path, model: WorldModel, registry: Registry, request: PlanRequest | None
) -> Advice:
    return advise_world(
        model,
        registry,
        pinned_changelist=game_pin(),
        pinned_docs_sha256=docs_pin(),
        ledger=Ledger(directory),
        mutes=MuteStore(directory),
        now=pw.NOW,
        plan_request=request,
    )


def _words(found: Advice) -> tuple[str, str | None]:
    """The outcome's status and reason as plain strings, so no assertion renders the outcome."""
    outcome = found.plan_outcome
    if outcome is None:
        pytest.fail("no plan outcome was carried")
    return outcome.status, outcome.reason


def _cards(found: Advice, rule: str) -> list[Card]:
    return [advised.card for advised in found.cards if advised.card.rule_id == rule]


def _plan_cards(found: Advice) -> list[Card]:
    return [*_cards(found, ADOPT), *_cards(found, REDESIGN)]


# --- case 1: one card, one search, the requirement's rates -----------------------------


def test_a_schematic_costing_two_items_reads_one_plan_card_at_the_requirements_rates(
    tmp_path: Path,
) -> None:
    model = pw._model(pw.ASCENT_PATHS)  # noqa: SLF001
    registry = pw._registry()  # noqa: SLF001
    request = _request(_two_item_catalog(), model, registry)

    assert dict(request.targets) == {SOLVE_RELIC_ITEM: RELIC_RATE, SOLVE_RARE_ITEM: RARE_RATE}
    found = _advise(tmp_path, model, registry, request)

    cards = _plan_cards(found)
    assert len(cards) == 1
    assert cards[0].rule_id == ADOPT
    plan = pw._card_read(cards[0], "plan.production")  # noqa: SLF001
    assert dict(plan.targets) == {SOLVE_RELIC_ITEM: RELIC_RATE, SOLVE_RARE_ITEM: RARE_RATE}  # type: ignore[attr-defined]


def test_one_request_makes_one_search_and_never_one_per_cost_item(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    searched: list[object] = []
    real = plans_module.optimize_within_bound

    def counting(*args: object, **kwargs: object) -> object:
        searched.append(args)
        return real(*args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(plans_module, "optimize_within_bound", counting)
    model = pw._model(pw.ASCENT_PATHS)  # noqa: SLF001
    registry = pw._registry()  # noqa: SLF001

    found = _advise(tmp_path, model, registry, _request(_two_item_catalog(), model, registry))

    status, _reason = _words(found)
    assert status == "ranked"
    assert len(searched) == 1


def test_a_no_plan_reads_one_marked_route_card_and_runs_one_route_derivation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    derived: list[object] = []
    real = plans_module.derived_route

    def counting(*args: object, **kwargs: object) -> object:
        derived.append(args)
        return real(*args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(plans_module, "derived_route", counting)
    model = pw._model(())  # noqa: SLF001
    registry = pw._registry()  # noqa: SLF001

    found = _advise(tmp_path, model, registry, _request(_two_item_catalog(), model, registry))

    cards = _plan_cards(found)
    assert [card.rule_id for card in cards] == [REDESIGN]
    assert len(derived) == 1


def test_the_rates_follow_the_requirement_when_its_budget_moves(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A rate is read from the requirement, never scaled or recomputed beside it."""
    monkeypatch.setattr(milestones, "COMPLETION_BUDGET_MINUTES", Fraction(60))
    model = pw._model(pw.ASCENT_PATHS)  # noqa: SLF001
    registry = pw._registry()  # noqa: SLF001

    request = _request(_two_item_catalog(), model, registry)

    assert dict(request.targets) == {
        SOLVE_RELIC_ITEM: Fraction(RELIC_COST, 60),
        SOLVE_RARE_ITEM: Fraction(RARE_COST, 60),
    }


# --- case 2: the card id ----------------------------------------------------------------


def test_the_card_id_is_the_section_5_2_hash_with_the_schematic_as_its_milestone(
    tmp_path: Path,
) -> None:
    model = pw._model(pw.ASCENT_PATHS)  # noqa: SLF001
    registry = pw._registry()  # noqa: SLF001

    found = _advise(tmp_path, model, registry, _request(_two_item_catalog(), model, registry))

    card = _plan_cards(found)[0]
    subject = f"plan:{SOLVE_RARE_ITEM}+{SOLVE_RELIC_ITEM}"
    assert card.target_milestone == SCHEMATIC
    assert card.id == card_id(ADOPT, subject, SCHEMATIC)


def test_the_same_schematic_over_two_saves_reads_the_same_id(tmp_path: Path) -> None:
    registry = pw._registry()  # noqa: SLF001
    first = pw._model(pw.ASCENT_PATHS)  # noqa: SLF001
    second = dataclasses.replace(first, token="Z" * len(first.token))

    one = _advise(tmp_path / "a", first, registry, _request(_two_item_catalog(), first, registry))
    two = _advise(tmp_path / "b", second, registry, _request(_two_item_catalog(), second, registry))

    assert _plan_cards(one)[0].id == _plan_cards(two)[0].id


def test_an_item_statement_at_the_same_targets_and_rates_reads_a_different_id(
    tmp_path: Path,
) -> None:
    model = pw._model(pw.ASCENT_PATHS)  # noqa: SLF001
    registry = pw._registry()  # noqa: SLF001
    stated = _request(_two_item_catalog(), model, registry)
    item_statement = PlanRequest(
        targets=MappingProxyType(dict(stated.targets)),
        raw_items=registry.resource_items,
        byproduct_policy=BYPRODUCT_BALANCED,
        direction=OBJECTIVE_RAW,
    )

    schematic_card = _plan_cards(_advise(tmp_path / "s", model, registry, stated))[0]
    item_card = _plan_cards(_advise(tmp_path / "i", model, registry, item_statement))[0]

    assert item_card.target_milestone is None
    assert item_card.id != schematic_card.id


# --- case 4: no rates, no card --------------------------------------------------------


def _unplannable_reason(tmp_path: Path, catalog: SchematicCatalog) -> str | None:
    """The reason an unplannable schematic reads, after checking its status and its no card."""
    model = pw._model(pw.ASCENT_PATHS)  # noqa: SLF001
    registry = pw._registry()  # noqa: SLF001
    found = _advise(tmp_path, model, registry, _request(catalog, model, registry))
    cards = len(_plan_cards(found))
    assert cards == 0
    status, reason = _words(found)
    assert status == UNPLANNABLE
    return reason


@pytest.mark.parametrize(
    ("cost", "word"),
    [
        (None, COST_UNREADABLE),
        ([(SOLVE_RELIC_ITEM, 0)], NONPOSITIVE_COST),
        ([(SOLVE_RELIC_ITEM, 10), (GHOST_ITEM, 5)], UNRESOLVED_COST_ITEM),
        ([], EMPTY_COST),
    ],
    ids=["cost-unreadable", "nonpositive-cost", "unresolved-cost-item", "empty-cost"],
)
def test_a_schematic_with_no_rates_reads_unplannable_with_its_reason_word_and_no_card(
    tmp_path: Path, cost: list[tuple[str, int]] | None, word: str
) -> None:
    reason = _unplannable_reason(tmp_path, _catalog(_schematic(cost)))

    assert reason == word


def test_a_cost_item_off_plan_targets_is_named_never_dropped(tmp_path: Path) -> None:
    """A raw resource beside a plannable item: no request with the raw item dropped."""
    catalog = _catalog(_schematic([(SOLVE_RELIC_ITEM, RELIC_COST), (SOLVE_ORE_ITEM, 60)]))

    reason = _unplannable_reason(tmp_path, catalog)

    assert reason == f"{ITEM_NOT_PLANNABLE}: {SOLVE_ORE_ITEM}"


def test_every_item_off_plan_targets_is_named_sorted(tmp_path: Path) -> None:
    catalog = _catalog(
        _schematic([(SOLVE_ORE_ITEM, 60), (SOLVE_RARE_ITEM, RARE_COST), (SOLVE_RELIC_ITEM, 10)])
    )
    model = pw._model(pw.ASCENT_PATHS)  # noqa: SLF001
    registry = pw._registry()  # noqa: SLF001
    bare = dataclasses.replace(registry, resource_items=(SOLVE_ORE_ITEM, SOLVE_RARE_ITEM))

    request = _request(catalog, model, bare)
    found = _advise(tmp_path, model, bare, request)

    status, reason = _words(found)
    assert status == UNPLANNABLE
    named = ", ".join(sorted((SOLVE_ORE_ITEM, SOLVE_RARE_ITEM)))
    assert reason == f"{ITEM_NOT_PLANNABLE}: {named}"


def test_a_schematic_the_catalog_does_not_hold_builds_no_request() -> None:
    model = pw._model(pw.ASCENT_PATHS)  # noqa: SLF001
    registry = pw._registry()  # noqa: SLF001

    absent = schematic_request_from(
        _two_item_catalog(), registry, model.unlocks, "Schematic_NeverDeclared_C", _parameters()
    )

    assert absent is None


@pytest.mark.parametrize(
    ("direction", "policy"),
    [("raw", "nonsense"), ("nonsense", BYPRODUCT_BALANCED)],
    ids=["policy", "direction"],
)
def test_a_direction_or_policy_the_advisor_refuses_is_refused_with_no_text(
    direction: str, policy: str
) -> None:
    assert schematic_parameters(direction=direction, byproduct_policy=policy) is None


# --- case 5: tier 3, from the trace -------------------------------------------------------


def test_tier_3_names_the_schematic_its_tier_each_amount_the_budget_and_each_rate(
    tmp_path: Path,
) -> None:
    model = pw._model(pw.ASCENT_PATHS)  # noqa: SLF001
    registry = pw._registry()  # noqa: SLF001
    found = _advise(tmp_path, model, registry, _request(_two_item_catalog(), model, registry))

    card = _plan_cards(found)[0]
    derivation = card.tier3

    assert f'"{SCHEMATIC}"' in derivation
    assert f"tech_tier={TIER}" in derivation
    assert f'"{SOLVE_RELIC_ITEM}": {RELIC_COST}' in derivation
    assert f'"{SOLVE_RARE_ITEM}": {RARE_COST}' in derivation
    assert f"budget_minutes={TWO_HOURS}" in derivation
    assert f'"{SOLVE_RELIC_ITEM}": {RELIC_RATE}' in derivation
    assert f'"{SOLVE_RARE_ITEM}": {RARE_RATE}' in derivation


def test_tiers_1_and_2_stay_one_line_each(tmp_path: Path) -> None:
    model = pw._model(pw.ASCENT_PATHS)  # noqa: SLF001
    registry = pw._registry()  # noqa: SLF001
    found = _advise(tmp_path, model, registry, _request(_two_item_catalog(), model, registry))

    card = _plan_cards(found)[0]

    assert "\n" not in card.tier1
    assert "\n" not in card.tier2


# --- the seams ----------------------------------------------------------------------------


def test_an_item_request_offers_no_schematic_and_reads_none() -> None:
    model = pw._model(pw.ASCENT_PATHS)  # noqa: SLF001
    registry = pw._registry()  # noqa: SLF001

    offered: Mapping[str, object] = plan_offer(model.unlocks, registry, pw._request())  # noqa: SLF001

    assert offered["plan.schematic"].value is None  # type: ignore[attr-defined]
