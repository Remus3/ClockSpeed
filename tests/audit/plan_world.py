"""CS-1235: turn a solved ``ProductionPlan`` into the synthetic world that builds it.

WHY THIS IS A TEST HELPER AND NOT AN AUDIT FUNCTION
-----------------------------------------------------
A materialised world is a FICTION: every machine on a step runs at the same
clock, every one reports producing, and none of it was read out of a save. The
audit layer publishes models of what a world IS; a function there that minted a
``WorldMachines`` nothing measured would be the one model in the package whose
``producing_available`` and ``overclock_available`` flags are true by assertion
rather than by reading. Nothing in the product consumes one either - the only
caller is the round-trip proof. So it lives beside that proof, and the seams
stay as they are: ``solve/`` imports neither ``save/`` nor ``audit/``, and
``audit/`` gains no dependency on ``solve.ratio``.

THE SPLIT IS EXACT. A step of ``m`` machines becomes ``ceil(m)`` machines, each
at clock ``m / ceil(m)``, so the clocks sum to ``m`` exactly and every machine
runs at or below the reference clock - which is also at or below the corpus's
un-sharded base, so no clock here needs a power shard. A zero-machine step
builds nothing.
"""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass
from fractions import Fraction
from types import MappingProxyType
from typing import TYPE_CHECKING

from clockspeed.audit.machines import MachineState, WorldMachines
from clockspeed.audit.placement import COORDINATE_UNITS, WorldPlacement

if TYPE_CHECKING:
    from clockspeed.data.registry import Registry
    from clockspeed.solve.ratio import ProductionPlan


@dataclass(frozen=True)
class MaterialisedWorld:
    """The two audit-layer models a solved plan builds.

    Attributes:
        machines: One ``MachineState`` per built machine, steps in plan order.
        placement: Built counts per building class, for ``balance.draw_of``.
    """

    machines: WorldMachines
    placement: WorldPlacement


def building_of(registry: Registry, recipe_key: str) -> str:
    """Name the one building a recipe is produced in.

    Args:
        registry: The registry the plan was solved against.
        recipe_key: The recipe.

    Returns:
        The building class name.

    Raises:
        ValueError: The recipe names no building or more than one, so no
            single machine class can be materialised for it.
    """
    producers = registry.recipes[recipe_key].produced_in
    if len(producers) != 1:
        raise ValueError(f"{recipe_key} names {len(producers)} buildings, not exactly one")
    return producers[0]


def machines_model(states: tuple[MachineState, ...]) -> WorldMachines:
    """Wrap states in the shape ``machines_of`` publishes.

    Args:
        states: The machines.

    Returns:
        The model, with availability derived from the states.
    """
    return WorldMachines(
        machines=states,
        producing_available=any(state.producing is not None for state in states),
        recipe_available=any(state.recipe_class_name is not None for state in states),
        overclock_available=any(state.overclock is not None for state in states),
        records_considered=len(states),
        unread_payload_count=0,
        refused_overclock_count=0,
        refused_recipe_count=0,
        warnings=(),
    )


def placement_model(states: tuple[MachineState, ...]) -> WorldPlacement:
    """Count the built machines per class, the way ``placement_of`` keys them.

    Args:
        states: The machines.

    Returns:
        A placement carrying built counts and nothing else.
    """
    counts = Counter(state.class_name for state in states)
    return WorldPlacement(
        node_placements=(),
        node_counts=MappingProxyType({}),
        built_placements=(),
        built_counts=MappingProxyType({key: counts[key] for key in sorted(counts)}),
        bounds=None,
        coordinate_units=COORDINATE_UNITS,
        node_semantics_available=False,
        node_orientation_available=True,
        warnings=(),
    )


def materialise(registry: Registry, plan: ProductionPlan) -> MaterialisedWorld:
    """Build the synthetic world a plan describes.

    Args:
        registry: The registry the plan was solved against.
        plan: The plan.

    Returns:
        The machines and the placement.
    """
    states: list[MachineState] = []
    for step in plan.steps:
        built = math.ceil(step.machines)
        if built == 0:
            continue
        clock = step.machines / built
        building = building_of(registry, step.recipe_key)
        states.extend(
            MachineState(
                class_name=building,
                producing=True,
                recipe_class_name=step.recipe_key,
                overclock=clock,
            )
            for _ in range(built)
        )
    frozen = tuple(states)
    return MaterialisedWorld(machines=machines_model(frozen), placement=placement_model(frozen))


def without_one(world: MaterialisedWorld, recipe_key: str) -> MaterialisedWorld:
    """Drop exactly one machine running ``recipe_key`` - the planted shortfall.

    Args:
        world: The materialised world.
        recipe_key: The recipe whose group loses a machine.

    Returns:
        The world with the FIRST machine on that recipe removed.

    Raises:
        ValueError: No machine runs that recipe.
    """
    states = list(world.machines.machines)
    for index, state in enumerate(states):
        if state.recipe_class_name == recipe_key:
            del states[index]
            frozen = tuple(states)
            return MaterialisedWorld(
                machines=machines_model(frozen), placement=placement_model(frozen)
            )
    raise ValueError(f"no machine runs {recipe_key}")


def built_count(step_machines: Fraction) -> int:
    """How many machines a step of ``step_machines`` materialises to.

    Args:
        step_machines: The plan's exact machine count.

    Returns:
        ``ceil(step_machines)``.
    """
    return math.ceil(step_machines)
