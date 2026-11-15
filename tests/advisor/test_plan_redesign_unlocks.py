"""CS-1374: a redesign card names each locked recipe's schematic and tech tier.

Graded here, against CS-1374's acceptance in ``docs/item_notes/phase5.md``, at the advisor: the
join of a schematic catalog and a registry, the preferred set it hands the route, and the
``plan.redesign.unlocks`` input the rule reads and tier 3 renders from the trace. The data layer's
reading of ``mUnlocks`` is ``tests/data/test_schematics.py``'s, and the count the preferred set
breaks is ``tests/solve/test_bound.py``'s.

EVERY WORLD IS THE SYNTHETIC ONE ``tests/advisor/test_plan_redesign.py`` builds, and every
catalog is hand-authored here through the real docs seam, so nothing reads an install. The
alternate ``mType`` token is spelled through the module's one constant and never typed here, so
the arms hold whatever the closing read-back confirms it to be.

THE SHAPE OF A NEGATIVE. Each arm that says a choice did not move carries a control on the same
fixture, run with no schematic source, where it does.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Iterable, Sequence
from typing import Any, Final

import pytest

from clockspeed.advisor.advise import inputs_of
from clockspeed.advisor.cards import Card, card_for
from clockspeed.advisor.plans import PlanRequest, plan_offer
from clockspeed.advisor.rules.plan import (
    IN_REDESIGN_LOCKED,
    IN_REDESIGN_UNLOCKS,
    REDESIGN_RULE,
    UNLOCK_NAMED,
    UNLOCK_NONE,
    UNLOCK_UNKNOWN,
    LockedUnlock,
    RedesignUnlocks,
    UnlockingSchematic,
)
from clockspeed.advisor.trace import StepKind, Trace, WorldInputs, run_rule
from clockspeed.data.registry import Registry
from clockspeed.data.schematics import ALTERNATE_TYPE_TOKEN, SchematicCatalog, normalize_schematics
from clockspeed.save.world import WorldModel
from tests.advisor import test_plan_redesign as worlds
from tests.advisor.build_fixtures import docs_pin, game_pin
from tests.data import synthetic
from tests.data.test_schematics import (
    KEY_UNLOCK_CLASS,
    KEY_UNLOCK_RECIPES,
    KEY_UNLOCKS,
    OTHER_UNLOCK_CLASS_PATH,
    RECIPE_UNLOCK_CLASS_PATH,
    UNKNOWN_RECIPES_KEY,
    UNKNOWN_UNLOCK_CLASS_PATH,
    schematic_document,
    schematic_entry,
)
from tests.solve.synthetic import (
    SOLVE_ASSEMBLER_BUILDING,
    SOLVE_ORE_ITEM,
    SOLVE_RARE_ITEM,
    SOLVE_RELIC_ITEM,
    machine_build_path,
)

#: The ordinary milestone ``mType`` token, which is the alternate's opposite on every arm here.
MILESTONE: Final = "EST_Milestone"


class _Source:
    """A schematic source that counts how often it is asked."""

    def __init__(self, catalog: SchematicCatalog | None) -> None:
        self._catalog = catalog
        self.calls = 0

    def catalog(self) -> SchematicCatalog | None:
        """Publish the catalog this source was built over, and count the ask."""
        self.calls += 1
        return self._catalog


def _unlock(paths: Iterable[str]) -> dict[str, str]:
    """One recipe-unlock element naming these whole paths."""
    return {
        KEY_UNLOCK_CLASS: RECIPE_UNLOCK_CLASS_PATH,
        KEY_UNLOCK_RECIPES: synthetic.class_path_blob(list(paths)),
    }


def _schematic(
    name: str,
    *,
    tier: str | None = "1",
    kind: str = MILESTONE,
    recipes: Sequence[str] = (),
    unlocks: object = None,
) -> dict[str, Any]:
    """One schematic entry unlocking these recipes by name, or carrying this raw unlock value."""
    value = [_unlock(worlds._path(recipe) for recipe in recipes)] if unlocks is None else unlocks  # noqa: SLF001
    return schematic_entry(name, mTechTier=tier, mType=kind, **{KEY_UNLOCKS: value})


def _catalog(*entries: dict[str, Any]) -> SchematicCatalog:
    """The normalized catalog of these entries, through the real docs seam."""
    return normalize_schematics(schematic_document(list(entries)))


def _world(
    held: Iterable[str],
    registry: Registry,
    request: PlanRequest,
    source: _Source | None,
    *,
    machines: Iterable[str] | None = None,
) -> WorldInputs:
    """The advisor's inputs for one world, with a schematic source handed in."""
    model: WorldModel = (
        worlds._model(held)  # noqa: SLF001
        if machines is None
        else worlds._model(held, machines=machines)  # noqa: SLF001
    )
    return inputs_of(
        model,
        registry,
        pinned_changelist=game_pin(),
        pinned_docs_sha256=docs_pin(),
        plan_request=request,
        schematics=source,
    )


def _card(world: WorldInputs) -> Card:
    """The plan.redesign card of one world, which must fire."""
    card = card_for(run_rule(REDESIGN_RULE, world))
    assert card is not None
    return card


def _offered(world: WorldInputs, name: str) -> object:
    """What a world offers for one input, so an assertion never renders the withheld mapping."""
    return world.values[name].value


def _unlocks_of(world: WorldInputs) -> RedesignUnlocks:
    """What a world offers for the route's unlockers, which must be a reading."""
    return _as_unlocks(_offered(world, IN_REDESIGN_UNLOCKS))


def _as_unlocks(value: object) -> RedesignUnlocks:
    """A value read as the reading it must be."""
    assert type(value) is RedesignUnlocks
    return value


def _locked_of(world: WorldInputs) -> tuple[str, ...]:
    """The route's locked stages a world offers."""
    return _as_names(_offered(world, IN_REDESIGN_LOCKED))


def _as_names(value: object) -> tuple[str, ...]:
    """A value read as the tuple of names it must be."""
    assert type(value) is tuple
    return value


def _order(reading: RedesignUnlocks) -> tuple[str, ...]:
    """The stages of a reading, in the order it lists them."""
    return tuple(entry.recipe for entry in reading.locked)


def _entry(reading: RedesignUnlocks, recipe: str) -> LockedUnlock:
    """One stage's entry."""
    found = [entry for entry in reading.locked if entry.recipe == recipe]
    assert len(found) == 1
    return found[0]


def _errors(trace: Trace) -> list[str]:
    """The rule-error subjects a trace recorded."""
    return [step.subject for step in trace.steps if step.kind is StepKind.RULE_ERROR]


def _three() -> tuple[Registry, PlanRequest]:
    """The world three locked stages out: R_A2, R_A3 and R_A4 locked, R_A1 held."""
    registry = worlds._three_locked_registry()  # noqa: SLF001
    return registry, worlds._request(registry)  # noqa: SLF001


def _three_world(*entries: dict[str, Any]) -> WorldInputs:
    """The three-locked world over a catalog of these schematics."""
    registry, request = _three()
    return _world((worlds.HELD_STAGE,), registry, request, _Source(_catalog(*entries)))


# ---------------------------------------------------------------------------
# Case 1 and 2 - the route takes the preferred recipe on a tie, and never at a cost in locked count
# ---------------------------------------------------------------------------


def _tie_registry() -> Registry:
    """Two locked producers of Relic, the hard-drive alternate first in registry order."""
    return worlds._registry(  # noqa: SLF001
        [
            worlds._recipe("R_AltFirst", [SOLVE_ORE_ITEM], [SOLVE_RELIC_ITEM]),  # noqa: SLF001
            worlds._recipe("R_PrefSecond", [SOLVE_ORE_ITEM], [SOLVE_RELIC_ITEM]),  # noqa: SLF001
        ]
    )


def test_two_locked_producers_tie_on_locked_count_and_the_route_takes_the_preferred_one() -> None:
    registry = _tie_registry()
    request = worlds._request(registry)  # noqa: SLF001
    catalog = _catalog(
        _schematic("Schematic_Alt_C", kind=ALTERNATE_TYPE_TOKEN, recipes=("R_AltFirst",)),
        _schematic("Schematic_Pref_C", recipes=("R_PrefSecond",)),
    )

    # Control: with no source the count is today's, and the tie goes to registry order.
    control = _world((), registry, request, None)
    assert _locked_of(control) == ("R_AltFirst",)

    chosen = _world((), registry, request, _Source(catalog))
    assert _locked_of(chosen) == ("R_PrefSecond",)
    assert _order(_unlocks_of(chosen)) == ("R_PrefSecond",)


def test_a_recipe_all_of_whose_unlockers_are_alternates_is_not_preferred() -> None:
    registry = _tie_registry()
    request = worlds._request(registry)  # noqa: SLF001
    both_alternate = _catalog(
        _schematic("Schematic_AltOne_C", kind=ALTERNATE_TYPE_TOKEN, recipes=("R_AltFirst",)),
        _schematic("Schematic_AltTwo_C", kind=ALTERNATE_TYPE_TOKEN, recipes=("R_PrefSecond",)),
    )
    mixed = _catalog(
        _schematic("Schematic_AltOne_C", kind=ALTERNATE_TYPE_TOKEN, recipes=("R_AltFirst",)),
        _schematic("Schematic_Plain_C", recipes=("R_AltFirst",)),
        _schematic("Schematic_AltTwo_C", kind=ALTERNATE_TYPE_TOKEN, recipes=("R_PrefSecond",)),
    )

    # Neither is preferred, so nothing breaks the tie. Control: one ordinary unlocker is enough to
    # prefer the first, which keeps the first in both worlds.
    assert _locked_of(_world((), registry, request, _Source(both_alternate))) == ("R_AltFirst",)
    assert _locked_of(_world((), registry, request, _Source(mixed))) == ("R_AltFirst",)


def test_an_alternate_with_fewer_locked_recipes_is_still_taken() -> None:
    registry = worlds._registry(  # noqa: SLF001
        [
            worlds._recipe("R_AltShort", [SOLVE_ORE_ITEM], [SOLVE_RELIC_ITEM]),  # noqa: SLF001
            worlds._recipe("R_PrefTop", [SOLVE_RARE_ITEM], [SOLVE_RELIC_ITEM]),  # noqa: SLF001
            worlds._recipe("R_PrefRare", [SOLVE_ORE_ITEM], [SOLVE_RARE_ITEM]),  # noqa: SLF001
        ]
    )
    request = worlds._request(registry)  # noqa: SLF001
    catalog = _catalog(
        _schematic("Schematic_Alt_C", kind=ALTERNATE_TYPE_TOKEN, recipes=("R_AltShort",)),
        _schematic("Schematic_Pref_C", recipes=("R_PrefTop", "R_PrefRare")),
    )

    assert _locked_of(_world((), registry, request, _Source(catalog))) == ("R_AltShort",)


# ---------------------------------------------------------------------------
# Case 3 - a recipe two schematics unlock names both, lower tier first
# ---------------------------------------------------------------------------


def test_a_recipe_two_schematics_unlock_names_both_lower_tier_first() -> None:
    world = _three_world(
        _schematic("Schematic_Alpha_C", tier="7", recipes=("R_A2",)),
        _schematic("Schematic_Zeta_C", tier="2", recipes=("R_A2",)),
    )

    entry = _entry(_unlocks_of(world), "R_A2")

    # The tier orders them, never the ClassName: Alpha sorts first and is the higher tier.
    assert entry.reading == UNLOCK_NAMED
    assert entry.schematics == (
        UnlockingSchematic("Schematic_Zeta_C", 2),
        UnlockingSchematic("Schematic_Alpha_C", 7),
    )


def test_equal_tiers_order_by_class_name_and_an_unknown_tier_is_last() -> None:
    world = _three_world(
        _schematic("Schematic_Unread_C", tier="not-a-tier", recipes=("R_A2",)),
        _schematic("Schematic_High_C", tier="9", recipes=("R_A2",)),
        _schematic("Schematic_Zeta_C", tier="3", recipes=("R_A2",)),
        _schematic("Schematic_Beta_C", tier="3", recipes=("R_A2",)),
    )

    assert _entry(_unlocks_of(world), "R_A2").schematics == (
        UnlockingSchematic("Schematic_Beta_C", 3),
        UnlockingSchematic("Schematic_Zeta_C", 3),
        UnlockingSchematic("Schematic_High_C", 9),
        UnlockingSchematic("Schematic_Unread_C", None),
    )


def test_tier_three_names_every_unlocking_schematic_in_that_order_from_the_trace() -> None:
    world = _three_world(
        _schematic("Schematic_Alpha_C", tier="7", recipes=("R_A2",)),
        _schematic("Schematic_Zeta_C", tier="2", recipes=("R_A2",)),
    )

    text = _card(world).tier3

    # Both are named, the lower tier first, and the line is the trace's own input-read step.
    assert text.index("Schematic_Zeta_C") < text.index("Schematic_Alpha_C")
    assert "Read plan.redesign.unlocks = " in text
    assert "tech_tier=2" in text


# ---------------------------------------------------------------------------
# Case 4 - the locked recipes list by ascending lowest tier, unknown last
# ---------------------------------------------------------------------------


def test_the_locked_list_orders_by_ascending_lowest_tier_with_unknown_last() -> None:
    world = _three_world(
        _schematic("Schematic_Five_C", tier="5", recipes=("R_A2",)),
        _schematic("Schematic_Two_C", tier="2", recipes=("R_A3",)),
        _schematic("Schematic_Unread_C", tier="x", recipes=("R_A4",)),
    )

    reading = _unlocks_of(world)

    # Registry order is A2, A3, A4 and would put A2 first. The locked list the card lists agrees.
    assert _order(reading) == ("R_A3", "R_A2", "R_A4")
    assert _locked_of(world) == ("R_A3", "R_A2", "R_A4")


def test_a_recipe_no_schematic_names_lists_after_every_known_tier() -> None:
    world = _three_world(
        _schematic("Schematic_Three_C", tier="3", recipes=("R_A3",)),
        _schematic("Schematic_One_C", tier="1", recipes=("R_A4",)),
    )

    reading = _unlocks_of(world)

    assert _order(reading) == ("R_A4", "R_A3", "R_A2")
    assert _entry(reading, "R_A2").reading == UNLOCK_NONE


def test_equal_lowest_tiers_keep_the_routes_registry_order() -> None:
    world = _three_world(
        _schematic("Schematic_Four_C", tier="4", recipes=("R_A3", "R_A2")),
        _schematic("Schematic_One_C", tier="1", recipes=("R_A4",)),
    )

    assert _order(_unlocks_of(world)) == ("R_A4", "R_A2", "R_A3")


def test_the_lowest_of_a_recipes_tiers_places_it_not_the_first_named() -> None:
    world = _three_world(
        _schematic("Schematic_Nine_C", tier="9", recipes=("R_A2", "R_A3")),
        _schematic("Schematic_Two_C", tier="2", recipes=("R_A3",)),
        _schematic("Schematic_Six_C", tier="6", recipes=("R_A4",)),
    )

    assert _order(_unlocks_of(world)) == ("R_A3", "R_A4", "R_A2")


# ---------------------------------------------------------------------------
# Case 5 - a stage held with its machine locked names the machine's schematic
# ---------------------------------------------------------------------------


def _machine_locked_world(entries: Sequence[dict[str, Any]]) -> WorldInputs:
    """R_Direct held, the Assembler that runs it not held, over a catalog of these."""
    registry = worlds._registry(  # noqa: SLF001
        [worlds._recipe("R_Direct", [SOLVE_ORE_ITEM], [SOLVE_RELIC_ITEM])]  # noqa: SLF001
    )
    request = worlds._request(registry)  # noqa: SLF001
    return _world(("R_Direct",), registry, request, _Source(_catalog(*entries)), machines=())


def test_a_stage_held_with_its_machine_locked_names_the_machines_schematic() -> None:
    machine_path = machine_build_path(SOLVE_ASSEMBLER_BUILDING)
    own_path_recipe = _schematic("Schematic_OwnRecipe_C", tier="1", recipes=("R_Direct",))
    machine_schematic = {
        **schematic_entry("Schematic_Machine_C", mTechTier="4", mType=MILESTONE),
        KEY_UNLOCKS: [_unlock([machine_path])],
    }

    world = _machine_locked_world([own_path_recipe, machine_schematic])

    entry = _entry(_unlocks_of(world), "R_Direct")
    # The recipe's own schematic is not what locks it: the world holds the recipe.
    assert _locked_of(world) == ("R_Direct",)
    assert entry.machine == SOLVE_ASSEMBLER_BUILDING
    assert entry.reading == UNLOCK_NAMED
    assert entry.schematics == (UnlockingSchematic("Schematic_Machine_C", 4),)


def test_a_stage_whose_recipe_is_locked_names_the_recipes_own_schematics_and_no_machine() -> None:
    registry = worlds._registry(  # noqa: SLF001
        [worlds._recipe("R_Direct", [SOLVE_ORE_ITEM], [SOLVE_RELIC_ITEM])]  # noqa: SLF001
    )
    request = worlds._request(registry)  # noqa: SLF001
    catalog = _catalog(_schematic("Schematic_OwnRecipe_C", tier="1", recipes=("R_Direct",)))

    world = _world((), registry, request, _Source(catalog))

    entry = _entry(_unlocks_of(world), "R_Direct")
    assert entry.machine is None
    assert entry.schematics == (UnlockingSchematic("Schematic_OwnRecipe_C", 1),)


# ---------------------------------------------------------------------------
# Case 6 - an unknown shape carrying recipes flags and reads unknown
# ---------------------------------------------------------------------------


def _unknown_shape_unlock(recipes: Iterable[str]) -> list[dict[str, str]]:
    """One element of a shape the data layer does not know, carrying a recipe list."""
    return [
        {
            KEY_UNLOCK_CLASS: UNKNOWN_UNLOCK_CLASS_PATH,
            UNKNOWN_RECIPES_KEY: synthetic.class_path_blob(
                [worlds._path(recipe) for recipe in recipes]  # noqa: SLF001
            ),
        }
    ]


def test_an_unknown_shape_element_carrying_recipes_reads_unknown_never_none() -> None:
    entries = (
        _schematic("Schematic_Two_C", tier="2", recipes=("R_A3",)),
        _schematic("Schematic_Odd_C", unlocks=_unknown_shape_unlock(("R_A2",))),
    )

    reading = _unlocks_of(_three_world(*entries))

    # R_A2 is named by nothing read, and a schematic whose unlocks were not read in full may.
    assert _entry(reading, "R_A2").reading == UNLOCK_UNKNOWN
    assert _entry(reading, "R_A2").schematics == ()
    assert _entry(reading, "R_A3").reading == UNLOCK_NAMED
    assert _order(reading) == ("R_A3", "R_A2", "R_A4")


def test_with_every_unlock_list_read_in_full_an_unnamed_recipe_reads_none() -> None:
    entries = (
        _schematic("Schematic_Two_C", tier="2", recipes=("R_A3",)),
        _schematic("Schematic_Info_C", unlocks=[{KEY_UNLOCK_CLASS: OTHER_UNLOCK_CLASS_PATH}]),
    )

    reading = _unlocks_of(_three_world(*entries))

    # Control for the arm above: the same world with nothing unreadable reads none.
    assert _entry(reading, "R_A2").reading == UNLOCK_NONE
    assert _entry(reading, "R_A4").reading == UNLOCK_NONE


# ---------------------------------------------------------------------------
# Case 7 - an unlocked path that joins no recipe is counted
# ---------------------------------------------------------------------------

#: A path no recipe of the registry carries, which a schematic nonetheless unlocks.
ORPHAN_PATH: Final = "/Game/FactoryGame/Synthetic/Orphan/Asset_Orphan.Asset_Orphan_C"


def test_an_unlocked_path_joining_no_recipe_is_counted_never_dropped() -> None:
    entries = (
        _schematic("Schematic_Two_C", tier="2", recipes=("R_A3",)),
        _schematic(
            "Schematic_Orphan_C",
            unlocks=[_unlock([ORPHAN_PATH, worlds._path("R_A2")])],  # noqa: SLF001
        ),
        _schematic("Schematic_OrphanToo_C", unlocks=[_unlock([ORPHAN_PATH])]),
    )

    reading = _unlocks_of(_three_world(*entries))

    # Two schematics unlock one orphan, and it is one path, so it counts once. The path that
    # does join is not counted.
    assert reading.unmatched == 1
    assert _entry(reading, "R_A2").schematics == (UnlockingSchematic("Schematic_Orphan_C", 1),)


def test_a_path_equal_to_a_recipes_trailing_token_alone_joins_nothing() -> None:
    # The class token of R_A2's path, without its package: a join by token would find R_A2.
    token = worlds._path("R_A2").rpartition(".")[2]  # noqa: SLF001
    assert token != worlds._path("R_A2")  # noqa: SLF001
    entries = (_schematic("Schematic_Token_C", unlocks=[_unlock([token])]),)

    reading = _unlocks_of(_three_world(*entries))

    assert _entry(reading, "R_A2").reading == UNLOCK_NONE
    assert reading.unmatched == 1


def test_no_unmatched_path_means_a_count_of_zero() -> None:
    reading = _unlocks_of(_three_world(_schematic("Schematic_Two_C", recipes=("R_A3",))))

    assert reading.unmatched == 0


# ---------------------------------------------------------------------------
# What is read, and when
# ---------------------------------------------------------------------------


def test_no_source_and_no_catalog_offer_no_reading_and_leave_the_card_as_it_was() -> None:
    registry, request = _three()
    catalog_less = _world((worlds.HELD_STAGE,), registry, request, _Source(None))
    no_source = _world((worlds.HELD_STAGE,), registry, request, None)

    assert catalog_less.values[IN_REDESIGN_UNLOCKS].value is None
    assert no_source.values[IN_REDESIGN_UNLOCKS].value is None
    assert _locked_of(catalog_less) == worlds.LOCKED_STAGES
    assert _card(catalog_less).tier2 == _card(no_source).tier2


def test_the_source_is_asked_only_where_a_route_is_derived() -> None:
    registry = worlds._registry(  # noqa: SLF001
        [worlds._recipe("R_Direct", [SOLVE_ORE_ITEM], [SOLVE_RELIC_ITEM])]  # noqa: SLF001
    )
    request = worlds._request(registry)  # noqa: SLF001
    ranked_source = _Source(_catalog())
    routed_source = _Source(_catalog())

    ranked = _world(("R_Direct",), registry, request, ranked_source)
    routed = _world((), registry, request, routed_source)

    # A plan is ranked for the first, so no route was derived and nothing asked the source.
    assert ranked.values[IN_REDESIGN_UNLOCKS].value is None
    assert ranked_source.calls == 0
    assert routed.values[IN_REDESIGN_UNLOCKS].value is not None
    assert routed_source.calls == 1


def test_plan_offer_with_no_source_is_the_offer_it_was() -> None:
    registry, request = _three()
    model = worlds._model((worlds.HELD_STAGE,))  # noqa: SLF001

    offered = plan_offer(model.unlocks, registry, request)

    assert offered[IN_REDESIGN_UNLOCKS].value is None
    assert offered[IN_REDESIGN_LOCKED].value == worlds.LOCKED_STAGES


def test_the_offer_names_where_the_unlocks_came_from() -> None:
    world = _three_world(_schematic("Schematic_Two_C", recipes=("R_A3",)))

    assert (
        world.values[IN_REDESIGN_UNLOCKS].source == "advisor.plans.redesign.schematic_unlock_join"
    )


# ---------------------------------------------------------------------------
# A forged reading is a rule error, never a short list passing for the whole
# ---------------------------------------------------------------------------


def _forged(world: WorldInputs, value: object) -> WorldInputs:
    """The same world with the unlocks input replaced."""
    return worlds._with_value(world, IN_REDESIGN_UNLOCKS, value)  # noqa: SLF001


def _forged_cases(reading: RedesignUnlocks) -> dict[str, object]:
    """Readings that each break one thing the rule checks."""
    first = reading.locked[0]
    return {
        "a-stage-is-missing": dataclasses.replace(reading, locked=reading.locked[1:]),
        "a-stage-is-repeated": dataclasses.replace(reading, locked=(*reading.locked, first)),
        "the-stages-are-reordered": dataclasses.replace(
            reading, locked=tuple(reversed(reading.locked))
        ),
        "a-reading-outside-the-vocabulary": dataclasses.replace(
            reading, locked=(dataclasses.replace(first, reading="maybe"), *reading.locked[1:])
        ),
        "named-with-no-schematic": dataclasses.replace(
            reading,
            locked=(
                dataclasses.replace(first, reading=UNLOCK_NAMED, schematics=()),
                *reading.locked[1:],
            ),
        ),
        "a-negative-unmatched-count": dataclasses.replace(reading, unmatched=-1),
        "a-plain-tuple": reading.locked,
    }


@pytest.mark.parametrize(
    "case",
    [
        "a-stage-is-missing",
        "a-stage-is-repeated",
        "the-stages-are-reordered",
        "a-reading-outside-the-vocabulary",
        "named-with-no-schematic",
        "a-negative-unmatched-count",
        "a-plain-tuple",
    ],
)
def test_a_forged_unlock_reading_is_a_rule_error_and_no_card(case: str) -> None:
    world = _three_world(_schematic("Schematic_Two_C", tier="2", recipes=("R_A3",)))
    control = run_rule(REDESIGN_RULE, world)
    assert control.recommendation is not None

    trace = run_rule(REDESIGN_RULE, _forged(world, _forged_cases(_unlocks_of(world))[case]))

    assert trace.recommendation is None
    assert _errors(trace) != []


def test_a_status_that_offers_no_route_offers_no_unlock_reading() -> None:
    registry = worlds._registry(  # noqa: SLF001
        [worlds._recipe("R_Direct", [SOLVE_ORE_ITEM], [SOLVE_RELIC_ITEM])]  # noqa: SLF001
    )
    request = worlds._request(registry)  # noqa: SLF001
    # A plan is ranked here, so the route is genuinely not reached and the statuses agree.
    ranked = _world(("R_Direct",), registry, request, _Source(_catalog()))
    control = run_rule(REDESIGN_RULE, ranked)
    assert control.recommendation is None
    assert _errors(control) == []

    planted = RedesignUnlocks(locked=(), unmatched=0)
    trace = run_rule(REDESIGN_RULE, _forged(ranked, planted))

    assert trace.recommendation is None
    assert _errors(trace) != []
