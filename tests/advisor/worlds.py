"""CS-500: a seeded generator of synthetic world states, plus naive rules to run on them.

WHY A SEEDED GENERATOR AND NOT A PROPERTY-TESTING LIBRARY. The merger ruled
for an in-repo generator over ``random.Random(seed)``: no new dependency, and
the same seed yields the same worlds on every machine, so a failure reproduces
from its seed alone.

THE RULES HERE ARE DELIBERATELY NAIVE. Each one recommends whenever its numeric
condition holds and never looks at the unlock set itself. That is the point:
the property test grades the ENGINE's precondition gate, so a rule that checked
its own unlocks would make the invariant hold for a reason the test cannot see.

Every name and value is invented. No world here was cut from a real save.

THE PLAN WORLD, CS-1382, IS THE OTHER HALF, FOR THE OPPOSITE REASON. The two plan rules are
not naive: the join in ``clockspeed/advisor/plans.py`` decides what they may offer, and the
engine's gate is only its second check. So they run as they ship, over one hand-authored
registry, against generated unlock sets, and what grades them reads these tables and no join.
:data:`PLAN_WORLD_RECIPES`, :data:`PLAN_WORLD_BUILD_PATHS` and :data:`PLAN_WORLD_EXTRACTORS`
state what the registry is built from, and :func:`plan_world_registry` builds it through the
real docs seam. The cases vary the target and so which raw items it eats, and how much of the
recipes, the machines and the extractors a world holds, each on its own density, so a world
holding a chain and nothing to dig for it is common and not a corner.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from fractions import Fraction
from typing import Final

from clockspeed.advisor.trace import (
    InputValue,
    Recommendation,
    RuleContext,
    RuleSpec,
    WorldInputs,
)
from clockspeed.data.registry import Registry, build_registry
from tests.data.synthetic import (
    KEY_CLASS_NAME,
    KEY_CLASSES,
    KEY_DISPLAY_NAME,
    KEY_DURATION,
    KEY_FORM,
    KEY_FULL_NAME,
    KEY_INGREDIENTS,
    KEY_MAX_POTENTIAL,
    KEY_NATIVE_CLASS,
    KEY_POWER_CONSUMPTION,
    KEY_POWER_EXPONENT,
    KEY_PRODUCED_IN,
    KEY_PRODUCT,
    amount_blob,
    class_path_blob,
)
from tests.solve.synthetic import (
    SOLVE_BUILD_GUN_PATH,
    building_path,
    document_from_groups,
    extractor_entry,
    extractor_group,
)

#: The synthetic unlock keys a generated world draws its unlock set from.
UNLOCK_UNIVERSE: tuple[str, ...] = (
    "feature:synthetic-overclock",
    "recipe:/Synthetic/Recipe_AltPlate",
    "recipe:/Synthetic/Recipe_AltRod",
    "schematic:/Synthetic/Schematic_TierTwo",
    "schematic:/Synthetic/Schematic_Trains",
)

#: The synthetic input names a generated world may carry, with their source.
INPUT_SOURCES: tuple[tuple[str, str], ...] = (
    ("synthetic.headroom", "synthetic.power"),
    ("synthetic.draw", "synthetic.power"),
    ("synthetic.purity", "synthetic.nodes"),
    ("synthetic.distance", "synthetic.nodes"),
)

#: The recipe a data-driven recommendation names, chosen by an input value.
_RECIPE_BY_PARITY: tuple[str, str] = (
    "recipe:/Synthetic/Recipe_AltPlate",
    "recipe:/Synthetic/Recipe_AltRod",
)


def generate_world(rng: random.Random) -> WorldInputs:
    """Draw one world: a random unlock subset and a random subset of inputs.

    An input may be absent, so the engine's missing-input path is exercised by
    the same population as its precondition gate. Every value is an exact
    Fraction drawn from integers - the generator never touches a float.
    """
    unlocks = frozenset(key for key in UNLOCK_UNIVERSE if rng.randrange(2))
    values: dict[str, InputValue] = {}
    for name, source in INPUT_SOURCES:
        if rng.randrange(5) == 0:
            continue
        values[name] = InputValue(Fraction(rng.randrange(0, 1000), rng.randrange(1, 60)), source)
    return WorldInputs(values=values, unlocks=unlocks)


def generate_worlds(seed: int, count: int) -> tuple[WorldInputs, ...]:
    """Draw ``count`` worlds from one seed, reproducibly."""
    rng = random.Random(seed)  # noqa: S311 - reproducible fixtures, not secrets
    return tuple(generate_world(rng) for _ in range(count))


def _overclock(ctx: RuleContext) -> Recommendation | None:
    headroom = ctx.read_exact("synthetic.headroom")
    draw = ctx.read_exact("synthetic.draw")
    spare = ctx.compute("spare", headroom - draw)
    if spare <= 0:
        ctx.reject("overclock", "no spare generation")
        return None
    return Recommendation(
        subject_key="synthetic-grid",
        action="Overclock the synthetic line",
        reason="spare generation available",
    )


def _claim_node(ctx: RuleContext) -> Recommendation | None:
    purity = ctx.read_exact("synthetic.purity")
    distance = ctx.read_exact("synthetic.distance")
    if purity < distance:
        ctx.reject("claim", "too far for its purity")
        return None
    return Recommendation(
        subject_key="synthetic-node",
        action="Claim the synthetic node",
        reason="purity outweighs distance",
    )


def _switch_recipe(ctx: RuleContext) -> Recommendation | None:
    """Recommend a recipe chosen from DATA, so its unlock is per-recommendation."""
    purity = ctx.read_exact("synthetic.purity")
    recipe = _RECIPE_BY_PARITY[purity.numerator % 2]
    return Recommendation(
        subject_key="synthetic-recipe",
        action="Switch to the alternate synthetic recipe",
        reason="the purity favours it",
        requires=(recipe,),
    )


def _rebalance(ctx: RuleContext) -> Recommendation | None:
    draw = ctx.read_exact("synthetic.draw")
    if draw == 0:
        return None
    return Recommendation(
        subject_key="synthetic-grid",
        action="Rebalance the synthetic grid",
        reason="draw is nonzero",
    )


#: Naive rules over the synthetic inputs - see the module docstring.
SYNTHETIC_RULES: tuple[RuleSpec, ...] = (
    RuleSpec(
        rule_id="synthetic.overclock",
        domain="power",
        inputs=("synthetic.headroom", "synthetic.draw"),
        unlocks=("feature:synthetic-overclock",),
        evaluate=_overclock,
    ),
    RuleSpec(
        rule_id="synthetic.claim-node",
        domain="nodes",
        inputs=("synthetic.purity", "synthetic.distance"),
        unlocks=("schematic:/Synthetic/Schematic_TierTwo", "schematic:/Synthetic/Schematic_Trains"),
        evaluate=_claim_node,
    ),
    RuleSpec(
        rule_id="synthetic.switch-recipe",
        domain="transport",
        inputs=("synthetic.purity",),
        unlocks=(),
        evaluate=_switch_recipe,
    ),
    RuleSpec(
        rule_id="synthetic.rebalance",
        domain="power",
        inputs=("synthetic.draw",),
        unlocks=(),
        evaluate=_rebalance,
    ),
)


# ---------------------------------------------------------------------------
# The plan world, CS-1382: see the module docstring
# ---------------------------------------------------------------------------

PLAN_WORLD_ORE: Final = "Desc_WorldOre_C"
PLAN_WORLD_COAL: Final = "Desc_WorldCoal_C"
PLAN_WORLD_WATER: Final = "Desc_WorldWater_C"

#: Declared raw, and no extractor names it, so it is flagged and never supplied.
PLAN_WORLD_SALT: Final = "Desc_WorldSalt_C"

PLAN_WORLD_PLATE: Final = "Desc_WorldPlate_C"
PLAN_WORLD_BEAM: Final = "Desc_WorldBeam_C"
PLAN_WORLD_FRAME: Final = "Desc_WorldFrame_C"
PLAN_WORLD_BRINE: Final = "Desc_WorldBrine_C"
PLAN_WORLD_ALLOY: Final = "Desc_WorldAlloy_C"
PLAN_WORLD_FEED: Final = "Desc_WorldFeed_C"
PLAN_WORLD_MEDAL: Final = "Desc_WorldMedal_C"
PLAN_WORLD_SHARD: Final = "Desc_WorldShard_C"
PLAN_WORLD_CRUST: Final = "Desc_WorldCrust_C"

PLAN_WORLD_SMELTER: Final = "Build_WorldSmelter_C"
PLAN_WORLD_ASSEMBLER: Final = "Build_WorldAssembler_C"
PLAN_WORLD_MINER: Final = "Build_WorldMiner_C"
PLAN_WORLD_MINER_TWO: Final = "Build_WorldMinerTwo_C"
PLAN_WORLD_PUMP: Final = "Build_WorldPump_C"

#: Extracts every solid by its docs and carries no model, so it can never supply anything.
PLAN_WORLD_DISPENSER: Final = "Equip_WorldDispenser_C"

#: Every item the resource group declares, with its form.
PLAN_WORLD_RAW: Final[tuple[tuple[str, str], ...]] = (
    (PLAN_WORLD_ORE, "RF_SOLID"),
    (PLAN_WORLD_COAL, "RF_SOLID"),
    (PLAN_WORLD_WATER, "RF_LIQUID"),
    (PLAN_WORLD_SALT, "RF_GAS"),
)

#: The machines each raw item can be dug by, as this fixture states it. The grader's table.
PLAN_WORLD_EXTRACTORS: Final[dict[str, tuple[str, ...]]] = {
    PLAN_WORLD_ORE: (PLAN_WORLD_MINER, PLAN_WORLD_MINER_TWO),
    PLAN_WORLD_COAL: (PLAN_WORLD_MINER, PLAN_WORLD_MINER_TWO),
    PLAN_WORLD_WATER: (PLAN_WORLD_PUMP,),
    PLAN_WORLD_SALT: (),
}

#: Every machine that has a build recipe. Sorted, so a generated subset is one order.
PLAN_WORLD_MACHINES: Final[tuple[str, ...]] = (PLAN_WORLD_ASSEMBLER, PLAN_WORLD_SMELTER)
PLAN_WORLD_EXTRACTOR_MACHINES: Final[tuple[str, ...]] = (
    PLAN_WORLD_MINER,
    PLAN_WORLD_MINER_TWO,
    PLAN_WORLD_PUMP,
)

#: The whole path of each machine's build recipe, which derives from no ClassName.
PLAN_WORLD_BUILD_PATHS: Final[dict[str, str]] = {
    PLAN_WORLD_SMELTER: "/Game/FactoryGame/Synthetic/World/Gun_Furnace.Gun_Furnace_C",
    PLAN_WORLD_ASSEMBLER: "/Game/FactoryGame/Synthetic/World/Gun_Bench.Gun_Bench_C",
    PLAN_WORLD_MINER: "/Game/FactoryGame/Synthetic/World/Gun_Drill.Gun_Drill_C",
    PLAN_WORLD_MINER_TWO: "/Game/FactoryGame/Synthetic/World/Gun_BigDrill.Gun_BigDrill_C",
    PLAN_WORLD_PUMP: "/Game/FactoryGame/Synthetic/World/Gun_Well.Gun_Well_C",
}


@dataclass(frozen=True)
class PlanWorldRecipe:
    """One recipe of the plan world, six seconds a cycle, every amount one.

    Attributes:
        name: Its ClassName.
        eats: The items it consumes.
        makes: The items it makes, the first of them its point.
        machines: The machines it runs on, in ``produced_in`` order.
        path: Its whole asset path, which derives from no ClassName.
    """

    name: str
    eats: tuple[str, ...]
    makes: tuple[str, ...]
    machines: tuple[str, ...]
    path: str


def _plan_world_recipe(
    name: str, eats: tuple[str, ...], makes: tuple[str, ...], *machines: str
) -> PlanWorldRecipe:
    """One recipe, at a path that holds an invented stem and no part of its ClassName."""
    stem = f"Asset{len(eats)}{len(makes)}{name.removeprefix('R_World')[::-1]}"
    return PlanWorldRecipe(
        name, eats, makes, machines, f"/Game/FactoryGame/Synthetic/World/{stem}.{stem}_C"
    )


#: Every recipe. Plate from either of two raw items, a chain over each, a machine choice, a
#: converter making a raw item, a loop that gives its raw item back, a raw byproduct, and a
#: recipe eating the raw item nothing digs.
PLAN_WORLD_RECIPES: Final[tuple[PlanWorldRecipe, ...]] = (
    _plan_world_recipe("R_WorldPlate", (PLAN_WORLD_ORE,), (PLAN_WORLD_PLATE,), PLAN_WORLD_SMELTER),
    _plan_world_recipe(
        "R_WorldCoalPlate", (PLAN_WORLD_COAL,), (PLAN_WORLD_PLATE,), PLAN_WORLD_ASSEMBLER
    ),
    _plan_world_recipe("R_WorldBeam", (PLAN_WORLD_COAL,), (PLAN_WORLD_BEAM,), PLAN_WORLD_SMELTER),
    _plan_world_recipe(
        "R_WorldFrame",
        (PLAN_WORLD_PLATE, PLAN_WORLD_BEAM),
        (PLAN_WORLD_FRAME,),
        PLAN_WORLD_ASSEMBLER,
    ),
    _plan_world_recipe(
        "R_WorldBrine",
        (PLAN_WORLD_WATER,),
        (PLAN_WORLD_BRINE,),
        PLAN_WORLD_SMELTER,
        PLAN_WORLD_ASSEMBLER,
    ),
    _plan_world_recipe(
        "R_WorldAlloy",
        (PLAN_WORLD_BRINE, PLAN_WORLD_PLATE),
        (PLAN_WORLD_ALLOY,),
        PLAN_WORLD_ASSEMBLER,
    ),
    _plan_world_recipe(
        "R_WorldOreFromBeam", (PLAN_WORLD_BEAM,), (PLAN_WORLD_ORE,), PLAN_WORLD_SMELTER
    ),
    _plan_world_recipe("R_WorldUp", (PLAN_WORLD_ORE,), (PLAN_WORLD_FEED,), PLAN_WORLD_ASSEMBLER),
    _plan_world_recipe(
        "R_WorldDown",
        (PLAN_WORLD_FEED,),
        (PLAN_WORLD_ORE, PLAN_WORLD_MEDAL),
        PLAN_WORLD_ASSEMBLER,
    ),
    _plan_world_recipe(
        "R_WorldCrack",
        (PLAN_WORLD_ORE,),
        (PLAN_WORLD_SHARD, PLAN_WORLD_WATER),
        PLAN_WORLD_SMELTER,
    ),
    _plan_world_recipe(
        "R_WorldSalted", (PLAN_WORLD_SALT,), (PLAN_WORLD_CRUST,), PLAN_WORLD_ASSEMBLER
    ),
)

#: What a case may target, each with the recipes that reach it, so its raw items vary: Ore or
#: Coal, Coal, both, Water, Water and Ore, Ore given back, Ore leaving Water over, and the raw
#: item nothing digs. A world holding Water's machine has no byproduct row, and one without it
#: does, so under the balanced policy only the route reads that chain: it is what reaches a route
#: with nothing locked in a world this small, which no cap ever cuts.
PLAN_WORLD_CLOSURES: Final[dict[str, tuple[str, ...]]] = {
    PLAN_WORLD_PLATE: ("R_WorldPlate", "R_WorldCoalPlate"),
    PLAN_WORLD_BEAM: ("R_WorldBeam",),
    PLAN_WORLD_FRAME: ("R_WorldFrame", "R_WorldPlate", "R_WorldCoalPlate", "R_WorldBeam"),
    PLAN_WORLD_BRINE: ("R_WorldBrine",),
    PLAN_WORLD_ALLOY: ("R_WorldAlloy", "R_WorldBrine", "R_WorldPlate", "R_WorldCoalPlate"),
    PLAN_WORLD_MEDAL: ("R_WorldDown", "R_WorldUp"),
    PLAN_WORLD_SHARD: ("R_WorldCrack",),
    PLAN_WORLD_CRUST: ("R_WorldSalted",),
}

#: The directions and policies a case states, spelled as the published door takes them.
_PLAN_WORLD_DIRECTIONS: Final[tuple[str, ...]] = ("raw", "buildings", "power")
_PLAN_WORLD_POLICIES: Final[tuple[str, ...]] = ("balanced", "sinkable")


@dataclass(frozen=True)
class PlanWorldCase:
    """One generated question: a target, how it is judged, and what the world holds.

    Attributes:
        target: The item to plan for.
        direction: The stated direction.
        policy: The stated byproduct policy.
        unlocked: The asset paths the world holds, sorted.
    """

    target: str
    direction: str
    policy: str
    unlocked: tuple[str, ...]


def _plan_world_group(short_name: str, entries: list[dict[str, str]]) -> dict[str, object]:
    """Wrap entries in the group shape the document uses.

    Args:
        short_name: The real group short name, which is what the loader dispatches on.
        entries: The entries.

    Returns:
        The group.
    """
    return {
        KEY_NATIVE_CLASS: f"/Script/CoreUObject.Class'/Script/FactoryGame.{short_name}'",
        KEY_CLASSES: entries,
    }


def _plan_world_machine(building: str) -> dict[str, str]:
    """One machine a recipe runs on, its draw exact and its clock readable."""
    return {
        KEY_CLASS_NAME: building,
        KEY_DISPLAY_NAME: building,
        KEY_POWER_CONSUMPTION: "10.000000",
        KEY_POWER_EXPONENT: "1.321929",
        KEY_MAX_POTENTIAL: "1.000000",
    }


def _plan_world_build_recipe(building: str) -> dict[str, str]:
    """One machine's build recipe, the measured build-gun shape, at the table's own path."""
    stem = building.removeprefix("Build_")
    return {
        KEY_CLASS_NAME: f"Recipe_{stem}",
        KEY_DISPLAY_NAME: stem,
        KEY_DURATION: "0.000000",
        KEY_INGREDIENTS: amount_blob([(PLAN_WORLD_PLATE, 1)]),
        KEY_PRODUCT: amount_blob([(f"Desc_{stem}", 1)]),
        KEY_PRODUCED_IN: class_path_blob([SOLVE_BUILD_GUN_PATH]),
        KEY_FULL_NAME: f"BlueprintGeneratedClass {PLAN_WORLD_BUILD_PATHS[building]}",
    }


def _plan_world_recipe_entry(recipe: PlanWorldRecipe) -> dict[str, str]:
    """One recipe of the table as docs text."""
    return {
        KEY_CLASS_NAME: recipe.name,
        KEY_DISPLAY_NAME: recipe.name,
        KEY_DURATION: "6.000000",
        KEY_INGREDIENTS: amount_blob([(item, 1) for item in recipe.eats]),
        KEY_PRODUCT: amount_blob([(item, 1) for item in recipe.makes]),
        KEY_PRODUCED_IN: class_path_blob([building_path(name) for name in recipe.machines]),
        KEY_FULL_NAME: f"BlueprintGeneratedClass {recipe.path}",
    }


def plan_world_registry() -> Registry:
    """Build the plan world through the real docs seam, from the tables above.

    Returns:
        The registry. Nothing in it was read from an install or a save.
    """
    items = (
        PLAN_WORLD_PLATE,
        PLAN_WORLD_BEAM,
        PLAN_WORLD_FRAME,
        PLAN_WORLD_BRINE,
        PLAN_WORLD_ALLOY,
        PLAN_WORLD_FEED,
        PLAN_WORLD_MEDAL,
        PLAN_WORLD_SHARD,
        PLAN_WORLD_CRUST,
    )
    every_machine = (*PLAN_WORLD_MACHINES, *PLAN_WORLD_EXTRACTOR_MACHINES)
    dispenser = {
        KEY_CLASS_NAME: PLAN_WORLD_DISPENSER,
        KEY_DISPLAY_NAME: PLAN_WORLD_DISPENSER,
        "mItemsPerCycle": "1",
        "mExtractCycleTime": "1.000000",
        "mAllowedResourceForms": "(RF_SOLID)",
    }
    groups: list[dict[str, object]] = [
        _plan_world_group(
            "FGItemDescriptor",
            [{KEY_CLASS_NAME: key, KEY_DISPLAY_NAME: key, KEY_FORM: "RF_SOLID"} for key in items],
        ),
        _plan_world_group(
            "FGResourceDescriptor",
            [
                {KEY_CLASS_NAME: key, KEY_DISPLAY_NAME: key, KEY_FORM: form}
                for key, form in PLAN_WORLD_RAW
            ],
        ),
        _plan_world_group(
            "FGBuildingDescriptor",
            [
                {
                    KEY_CLASS_NAME: f"Desc_{name.removeprefix('Build_')}",
                    KEY_DISPLAY_NAME: name,
                    KEY_FORM: "RF_INVALID",
                }
                for name in every_machine
            ],
        ),
        _plan_world_group(
            "FGBuildableManufacturer", [_plan_world_machine(name) for name in PLAN_WORLD_MACHINES]
        ),
        extractor_group(
            extractor_entry(PLAN_WORLD_MINER),
            extractor_entry(PLAN_WORLD_MINER_TWO),
            dispenser,
            extractor_entry(PLAN_WORLD_PUMP, forms="(RF_LIQUID)", only=(PLAN_WORLD_WATER,)),
        ),
        _plan_world_group(
            "FGRecipe",
            [
                *(_plan_world_recipe_entry(recipe) for recipe in PLAN_WORLD_RECIPES),
                *(_plan_world_build_recipe(name) for name in every_machine),
            ],
        ),
    ]
    return build_registry(document_from_groups(groups))


def _plan_world_subset(rng: random.Random, paths: tuple[str, ...], density: int) -> list[str]:
    """Each path independently, ``density`` chances in four.

    Args:
        rng: The generator, which only ever deals in ints here.
        paths: The paths to draw from.
        density: How many of four chances each one gets. Zero holds none, four holds all.

    Returns:
        The drawn paths.
    """
    return [path for path in paths if rng.randrange(4) < density]


def generate_plan_world_case(rng: random.Random) -> PlanWorldCase:
    """Draw one case: a target, a direction, a policy and an unlock set on three densities.

    The recipes come from the target's closure and one decoy, and not from the whole table,
    because the exhaustive backend's ascent over k held recipes solves up to ``(1 << (k + 1)) - 1``
    subsets. Over the whole table a no-plan costs a hundred offers' worth of a small one.

    Args:
        rng: The generator.

    Returns:
        The case.
    """
    machines = tuple(PLAN_WORLD_BUILD_PATHS[name] for name in PLAN_WORLD_MACHINES)
    extractors = tuple(PLAN_WORLD_BUILD_PATHS[name] for name in PLAN_WORLD_EXTRACTOR_MACHINES)
    target = rng.choice(tuple(PLAN_WORLD_CLOSURES))
    closure = PLAN_WORLD_CLOSURES[target]
    decoy = rng.choice(tuple(item.name for item in PLAN_WORLD_RECIPES if item.name not in closure))
    drawn = (*closure, decoy)
    recipes = tuple(item.path for item in PLAN_WORLD_RECIPES if item.name in drawn)
    direction = rng.choice(_PLAN_WORLD_DIRECTIONS)
    policy = rng.choice(_PLAN_WORLD_POLICIES)
    unlocked = (
        *_plan_world_subset(rng, recipes, rng.randrange(1, 5)),
        *_plan_world_subset(rng, machines, rng.randrange(1, 5)),
        *_plan_world_subset(rng, extractors, rng.randrange(5)),
    )
    return PlanWorldCase(target, direction, policy, tuple(sorted(unlocked)))


def generate_plan_world_cases(seed: int, count: int) -> tuple[PlanWorldCase, ...]:
    """Draw ``count`` cases from one seed, reproducibly.

    Args:
        seed: The seed.
        count: How many.

    Returns:
        The cases, the same on every machine for one seed.
    """
    rng = random.Random(seed)  # noqa: S311 - reproducible fixtures, not secrets
    return tuple(generate_plan_world_case(rng) for _ in range(count))
