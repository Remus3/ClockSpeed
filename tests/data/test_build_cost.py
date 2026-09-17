"""CS-930 - build cost, reachable from a Building through a graded seam.

Build cost is PRESENT in the shipped data and was modelled nowhere, so
``BOOTSTRAP.md``'s promised ``total build cost`` output lacked a JOIN rather
than a data source. This module grades that join.

WHAT THE JOIN IS, MEASURED BEFORE ANY OF THIS WAS WRITTEN
---------------------------------------------------------
A buildable's cost is carried on a BUILD GUN RECIPE - a recipe whose
``mProducedIn`` names the build gun and nothing a registry models. Its single
product is the building DESCRIPTOR, and the descriptor entry carries no pointer
back to the buildable, so the join is on the class name:
``Build_X_C`` takes ``Desc_X_C``, and a key that is already a descriptor takes
itself.

THE TRAP THIS MODULE EXISTS TO HOLD, AND IT WAS MEASURED THE HARD WAY
---------------------------------------------------------------------
**There is more than one spelling of the build gun token.** The pinned build
ships ``BP_BuildGun_C`` on the overwhelming majority and ``FGBuildGun`` on
exactly one recipe. A first probe written for this item transcribed the common
spelling alone, lost that recipe, and measured a join one building short - and
the miss looked exactly like a building the game ships no cost for. So the
selector matches the MARKER rather than either transcription, and
:func:`test_the_second_build_gun_token_spelling_is_not_lost` is the arm that
keeps it that way.

THE THREE BUILDINGS THAT DO NOT JOIN ARE NOT A BUG TO BE WIDENED AWAY
----------------------------------------------------------------------
Two buildables share one descriptor shipped under a third name, and one
buildable has no build-gun recipe in the document at all. Publishing a zero or
an empty cost for those is the confident-zero trap
``Building.power_consumption`` documents at length: a caller cannot tell a
building that costs nothing from one whose cost this project failed to find.
They are ``None``, and :func:`buildings_without_build_cost` enumerates them so
the failure is reportable rather than silent (non-negotiable 7).

WHAT READS THE REAL INSTALL, AND WHAT DOES NOT
-----------------------------------------------
Every unit arm below builds its Registry from material hand-authored in THIS
file, so it runs on a machine that has never had the game on it - the CS-200
criterion ``tests/data/__init__.py`` states. The single real-install arm SKIPS
explicitly when no install resolves and reports COUNTS ONLY.
"""

from __future__ import annotations

from fractions import Fraction
from types import MappingProxyType
from typing import Final

import pytest

from clockspeed.data.docs_extract import load_document, read_docs_text
from clockspeed.data.locate import resolve_game_dir
from clockspeed.data.registry import (
    BUILD_GUN_MARKER,
    BuildCost,
    Building,
    Item,
    Recipe,
    RecipeIO,
    Registry,
    build_cost,
    build_gun_recipes,
    build_registry,
    buildings_without_build_cost,
)

# ---------------------------------------------------------------------------
# The hand-authored corpus. Spelled out as literals beside the assertions that
# read them, deliberately: a fixture importing the implementation's own join
# rule would stay green through a rename of that rule, which is the defect a
# fixture exists to catch.
# ---------------------------------------------------------------------------

#: A buildable whose cost is carried on a recipe using the common token.
SMELTER: Final = "Build_Smelter_C"
SMELTER_DESCRIPTOR: Final = "Desc_Smelter_C"
SMELTER_RECIPE: Final = "Recipe_Smelter_C"

#: A buildable whose cost is carried on a recipe using the RARE token. The
#: pinned build ships exactly one of these and losing it is invisible.
ELEVATOR: Final = "Build_Elevator_C"
ELEVATOR_DESCRIPTOR: Final = "Desc_Elevator_C"
ELEVATOR_RECIPE: Final = "Recipe_Elevator_C"

#: A modelled buildable whose OWN key is already a descriptor. The pinned build
#: ships one, so the join cannot assume a ``Build_`` prefix.
LOCOMOTIVE: Final = "Desc_Locomotive_C"
LOCOMOTIVE_RECIPE: Final = "Recipe_Locomotive_C"

#: A modelled buildable the document ships no build-gun recipe for.
HOVERPACK: Final = "Equip_HoverPack_C"

#: A buildable whose descriptor is shipped under a THIRD name, so no
#: substitution rule reaches it.
JUMPPAD: Final = "Build_JumpPad_C"

#: A descriptor produced by an AUTOMATED recipe. A selector that joins on the
#: product alone would report this as a build cost.
DECOY: Final = "Build_Decoy_C"
DECOY_DESCRIPTOR: Final = "Desc_Decoy_C"
DECOY_RECIPE: Final = "Recipe_Decoy_C"

IRON_PLATE: Final = "Desc_IronPlate_C"
WIRE: Final = "Desc_Wire_C"
CONCRETE: Final = "Desc_Cement_C"

#: The two producer-class spellings measured in the pinned build's document.
COMMON_BUILD_GUN_CLASS: Final = "BP_BuildGun_C"
RARE_BUILD_GUN_CLASS: Final = "FGBuildGun"

#: A hand-craft producer class that is NOT a build gun.
WORKBENCH_CLASS: Final = "BP_WorkBenchComponent_C"


def _item(key: str) -> Item:
    """Build the minimum Item the join needs.

    Args:
        key: The item's ClassName.

    Returns:
        An Item carrying that key.
    """
    return Item(
        key=key,
        display_name=key,
        form="RF_SOLID",
        energy_value=None,
        sink_points=None,
        is_fluid=False,
    )


def _building(key: str) -> Building:
    """Build the minimum Building the join needs.

    Args:
        key: The buildable's ClassName.

    Returns:
        A Building carrying that key and no power claim.
    """
    return Building(
        key=key,
        display_name=key,
        power_consumption=Fraction(4),
        power_exponent=None,
        estimated_min_power=None,
        estimated_max_power=None,
        is_variable_power=False,
    )


def _recipe(
    key: str,
    product: str,
    ingredients: tuple[tuple[str, int], ...],
    *,
    produced_in: tuple[str, ...] = (),
    unresolved: tuple[str, ...] = (),
) -> Recipe:
    """Build one recipe with an exact-rational ingredient side.

    Args:
        key: The recipe's ClassName.
        product: The single product's item ClassName.
        ingredients: ``(item key, whole amount)`` pairs, in source order.
        produced_in: ClassNames of modelled producers.
        unresolved: Producer tokens that resolved to nothing.

    Returns:
        The recipe.
    """
    return Recipe(
        key=key,
        display_name=key,
        duration=Fraction(1),
        inputs=tuple(RecipeIO(item_key=name, amount=Fraction(n)) for name, n in ingredients),
        outputs=(RecipeIO(item_key=product, amount=Fraction(1)),),
        produced_in=produced_in,
        variable_power_constant=None,
        variable_power_factor=None,
        unresolved_produced_in=unresolved,
    )


@pytest.fixture
def registry() -> Registry:
    """The hand-authored registry every unit arm here reads.

    Returns:
        A Registry carrying five modelled buildings and four recipes.
    """
    buildings = {
        key: _building(key) for key in (SMELTER, ELEVATOR, LOCOMOTIVE, HOVERPACK, JUMPPAD, DECOY)
    }
    recipes = {
        SMELTER_RECIPE: _recipe(
            SMELTER_RECIPE,
            SMELTER_DESCRIPTOR,
            ((IRON_PLATE, 5), (WIRE, 8)),
            unresolved=(COMMON_BUILD_GUN_CLASS,),
        ),
        ELEVATOR_RECIPE: _recipe(
            ELEVATOR_RECIPE,
            ELEVATOR_DESCRIPTOR,
            ((CONCRETE, 500),),
            unresolved=(RARE_BUILD_GUN_CLASS,),
        ),
        LOCOMOTIVE_RECIPE: _recipe(
            LOCOMOTIVE_RECIPE,
            LOCOMOTIVE,
            ((WIRE, 3),),
            unresolved=(COMMON_BUILD_GUN_CLASS, WORKBENCH_CLASS),
        ),
        DECOY_RECIPE: _recipe(
            DECOY_RECIPE,
            DECOY_DESCRIPTOR,
            ((IRON_PLATE, 1),),
            produced_in=(SMELTER,),
            unresolved=(WORKBENCH_CLASS,),
        ),
    }
    items = {
        key: _item(key)
        for key in (
            SMELTER_DESCRIPTOR,
            ELEVATOR_DESCRIPTOR,
            LOCOMOTIVE,
            DECOY_DESCRIPTOR,
            IRON_PLATE,
            WIRE,
            CONCRETE,
        )
    }
    return Registry(
        items=MappingProxyType(items),
        recipes=MappingProxyType(recipes),
        buildings=MappingProxyType(buildings),
        warnings=(),
        unknown_groups=(),
    )


# ---------------------------------------------------------------------------
# The seam
# ---------------------------------------------------------------------------


def test_a_building_reaches_its_build_cost_through_the_seam(registry: Registry) -> None:
    cost = build_cost(registry, SMELTER)
    assert cost is not None
    assert cost.building_key == SMELTER
    assert cost.recipe_key == SMELTER_RECIPE
    assert tuple((io.item_key, io.amount) for io in cost.ingredients) == (
        (IRON_PLATE, Fraction(5)),
        (WIRE, Fraction(8)),
    )


def test_the_second_build_gun_token_spelling_is_not_lost(registry: Registry) -> None:
    # The pinned build ships ONE recipe under the rare spelling. A selector
    # transcribing the common token alone loses it, and the loss is
    # indistinguishable from a building the game ships no cost for.
    cost = build_cost(registry, ELEVATOR)
    assert cost is not None
    assert cost.recipe_key == ELEVATOR_RECIPE


def test_both_measured_spellings_carry_the_marker_the_selector_matches() -> None:
    # The arm above is only worth something if the two literals it uses really
    # are the two shapes the marker was derived from.
    assert BUILD_GUN_MARKER in COMMON_BUILD_GUN_CLASS
    assert BUILD_GUN_MARKER in RARE_BUILD_GUN_CLASS
    assert BUILD_GUN_MARKER not in WORKBENCH_CLASS


def test_a_building_whose_key_is_already_a_descriptor_joins_by_identity(
    registry: Registry,
) -> None:
    cost = build_cost(registry, LOCOMOTIVE)
    assert cost is not None
    assert cost.recipe_key == LOCOMOTIVE_RECIPE


def test_a_build_gun_recipe_naming_a_hand_craft_token_too_is_still_a_build_recipe(
    registry: Registry,
) -> None:
    assert {recipe.key for recipe in build_gun_recipes(registry)} == {
        SMELTER_RECIPE,
        ELEVATOR_RECIPE,
        LOCOMOTIVE_RECIPE,
    }


def test_an_automated_recipe_producing_a_descriptor_is_not_a_build_cost(
    registry: Registry,
) -> None:
    # Joining on the product alone would report the automated recipe's inputs
    # as this building's cost.
    assert build_cost(registry, DECOY) is None


# ---------------------------------------------------------------------------
# What the seam refuses to guess
# ---------------------------------------------------------------------------


def test_a_building_with_no_build_recipe_is_none_rather_than_a_zero_cost(
    registry: Registry,
) -> None:
    # A confident empty cost is exactly what a build plan cannot detect.
    assert build_cost(registry, HOVERPACK) is None


def test_a_building_whose_descriptor_is_shipped_under_a_third_name_is_none(
    registry: Registry,
) -> None:
    assert build_cost(registry, JUMPPAD) is None


def test_the_unjoined_buildings_are_enumerable_rather_than_silent(
    registry: Registry,
) -> None:
    assert buildings_without_build_cost(registry) == (HOVERPACK, JUMPPAD, DECOY)


def test_a_key_that_is_not_a_modelled_building_raises(registry: Registry) -> None:
    # "no cost known" and "you asked about something that is not a building"
    # are different answers and must not share one.
    with pytest.raises(KeyError):
        build_cost(registry, "Build_NotModelled_C")


def test_every_amount_is_an_exact_fraction(registry: Registry) -> None:
    cost = build_cost(registry, SMELTER)
    assert cost is not None
    kinds = {type(io.amount) for io in cost.ingredients}
    assert kinds == {Fraction}


def test_the_cost_record_is_frozen(registry: Registry) -> None:
    cost = build_cost(registry, SMELTER)
    assert isinstance(cost, BuildCost)
    with pytest.raises(AttributeError):
        cost.recipe_key = "Recipe_Other_C"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# The real install. COUNTS ONLY, and it skips where there is no install.
# ---------------------------------------------------------------------------

#: The modelled buildings the pinned build ships no reachable build cost for,
#: named rather than counted so that a fourth one cannot arrive unnoticed
#: inside a threshold. Each is exempt for a stated reason:
#:
#: - the two jump pads share one descriptor shipped under a third name;
#: - the hover pack has no build-gun recipe in the document at all.
EXEMPT_FROM_BUILD_COST: Final = frozenset(
    {"Build_JumpPad_C", "Build_JumpPadTilted_C", "Equip_HoverPack_C"}
)


@pytest.fixture(scope="module")
def real_registry() -> Registry:
    """Build the registry from the real install once, or skip.

    Module-scoped deliberately: parsing the shipped document is the expensive
    half of this module and every arm below reads the same build.

    Returns:
        The registry built from the shipped document.
    """
    game_dir, source = resolve_game_dir()
    if game_dir is None:
        pytest.skip(f"no game install on this machine; the resolver reported: {source}")
    docs = game_dir / "CommunityResources" / "Docs" / "en-US.json"
    if not docs.is_file():
        pytest.skip("this install ships no en-US docs file, so there is nothing to join")
    return build_registry(load_document(read_docs_text(docs)))


@pytest.mark.slow
def test_every_modelled_building_joins_a_build_cost_or_is_declared_exempt(
    real_registry: Registry,
) -> None:
    real = real_registry
    unjoined = frozenset(buildings_without_build_cost(real))
    # COUNTS ONLY past this line: the equality is over NAMES this file already
    # carries, and the report is a count.
    assert unjoined == EXEMPT_FROM_BUILD_COST, (
        f"{len(unjoined)} modelled buildings carry no reachable build cost; "
        f"{len(EXEMPT_FROM_BUILD_COST)} are declared exempt"
    )
    joined = len(real.buildings) - len(unjoined)
    assert joined > 0, f"{joined} of {len(real.buildings)} modelled buildings joined"


@pytest.mark.slow
def test_no_descriptor_is_produced_by_more_than_one_build_recipe(
    real_registry: Registry,
) -> None:
    # If one were, the seam would have to choose, and choosing silently is how
    # a cost gets reported for the wrong recipe.
    real = real_registry
    seen: dict[str, int] = {}
    for recipe in build_gun_recipes(real):
        for product in recipe.outputs:
            seen[product.item_key] = seen.get(product.item_key, 0) + 1
    contested = sum(1 for count in seen.values() if count > 1)
    assert contested == 0, f"{contested} descriptors are produced by more than one recipe"
