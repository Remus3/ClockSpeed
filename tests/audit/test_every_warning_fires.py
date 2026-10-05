"""CS-1238: every audit warning code proves it can go red.

THE CLAIM. For every ``WARN_*`` code a module of ``clockspeed.audit`` DEFINES,
this module holds a minimal synthetic fixture and the one call over it that
must raise that code, and asserts the code is raised. A warning no fixture can
raise is a check nobody has seen fire, and a check nobody has seen fire is
indistinguishable from one wired to nothing - the silently-wrong half of
non-negotiable 7, one level up.

THE SET IS DERIVED, NEVER LISTED. The codes are the ones
``tests/audit/test_package_exports.py`` derives by walking the package and
parsing each module's source (the CS-1023 rule), so a code added to any audit
module reddens :func:`test_every_derived_code_has_a_firing_fixture` by name
until a fixture here raises it. The table below is hand-written because it
must be - a fixture is fixture code - and that arm is what grades it.

ONE CODE, ONE TEST ID. :func:`test_the_fixture_raises_its_code` is parametrised
over the table with the constant's name as the id, so a fixture that stops
firing reddens exactly the test that names its code.

REMOVING A FIXTURE REDDENS EXACTLY ONE TEST NAMING THE CODE.
:func:`test_dropping_any_one_fixture_is_named_alone` drops each entry in turn
and asserts the completeness predicate names that code and nothing else; the
parametrised arm loses that one id with it.

EVERY FIXTURE IS SYNTHETIC. Each is built from the helpers the per-module test
in this directory already authored (``tests/audit/__init__.py`` states the
rules they follow) and the synthetic solver corpus in ``tests/solve``; nothing
here reads a save, a docs file or a game install. Four codes are STANDING
advisories that their function raises on every world by design - production
unmodelled (on every balance given no generator model, CS-1059), absolute
extent and water regions unavailable, belt and circuit topology unavailable -
and their fixture is simply the smallest world the function accepts; when they
fire is graded by the owning module's own tests, not re-litigated here.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Iterable, Mapping
from fractions import Fraction
from typing import Final

import pytest

import clockspeed.audit as audit_package
from clockspeed.audit import (
    balance,
    collectibles,
    flow,
    footprint,
    inventory,
    machines,
    network,
    overlay,
    placement,
)
from clockspeed.data.registry import Building
from clockspeed.save import objects
from clockspeed.save.world import WorldWarning
from tests.audit import test_balance as balance_fx
from tests.audit import test_collectibles as collectibles_fx
from tests.audit import test_footprint as footprint_fx
from tests.audit import test_inventory as inventory_fx
from tests.audit import test_machines as machines_fx
from tests.audit import test_network as network_fx
from tests.audit import test_placement as placement_fx
from tests.audit import test_production as production_fx
from tests.audit.test_package_exports import defining_modules
from tests.solve import synthetic

#: One zero-argument call per code: build the fixture, run the audit, return
#: the warnings it raised.
Firing = Callable[[], Iterable[WorldWarning]]

#: A recipe the synthetic solver corpus never authored.
_UNKNOWN_RECIPE: Final = "R_SolveNeverAuthored"

#: A built class on neither the placement allowlist nor any footprint category.
_UNPLOTTED_BUILT_CLASS: Final = "Build_PowerLine_C"

#: A measured miner class, allowlisted by placement and footprint alike.
_MINER: Final = "Build_MinerMk1_C"

#: A measured resource-node class.
_NODE: Final = "BP_ResourceNode_C"


def _flow(*states: machines.MachineState) -> tuple[WorldWarning, ...]:
    """Run the flow audit over bare machine states and the synthetic recipes.

    Args:
        states: The machines.

    Returns:
        The warnings raised.
    """
    return flow.flow_of(list(states), dict(synthetic.solve_registry().recipes)).warnings


def _smelter(recipe: str | None, clock: Fraction | None = Fraction(1)) -> machines.MachineState:
    """One synthetic smelter, producing, so only the recipe and the clock decide the flow.

    Args:
        recipe: The recipe class name, or None for an unconfigured machine.
        clock: The overclock, or None for an unread one.

    Returns:
        The state.
    """
    return machines.MachineState(
        class_name=synthetic.SOLVE_SMELTER_BUILDING,
        producing=True,
        recipe_class_name=recipe,
        overclock=clock,
    )


def _overlay(*edits: overlay.OverlayEdit, priced: bool = False) -> tuple[WorldWarning, ...]:
    """Evaluate an overlay over one plate smelter, with no placement supplied.

    Args:
        edits: The overlay's edits.
        priced: Whether the synthetic buildings are supplied, so a clock can
            be checked against a base.

    Returns:
        The warnings raised.
    """
    states = (_smelter(synthetic.PLATE_RECIPE),)
    model = machines.WorldMachines(
        machines=states,
        producing_available=True,
        recipe_available=True,
        overclock_available=True,
        records_considered=len(states),
        unread_payload_count=0,
        refused_overclock_count=0,
        refused_recipe_count=0,
        warnings=(),
    )
    registry = synthetic.solve_registry()
    return overlay.evaluate_overlay(
        model,
        overlay.Overlay(edits=edits),
        dict(registry.recipes),
        buildings=dict(registry.buildings) if priced else None,
    ).warnings


def _balance_composite(*, belts: bool) -> tuple[WorldWarning, ...]:
    """The composite balance over a modelled world, with belts declared or not.

    Args:
        belts: Whether the network model declares belt topology.

    Returns:
        The warnings raised.
    """
    return balance.balance_of(
        balance_fx.built(balance_fx.modeled_counts()),
        balance_fx.modeled_registry(),
        balance_fx.world_machines(),
        balance_fx.world_network(belts=belts),
    ).warnings


def _clocked_draw(
    clock: Fraction | None,
    entries: Mapping[str, Building],
    class_name: str = balance_fx.FIXED_WHOLE,
) -> tuple[WorldWarning, ...]:
    """The clocked draw over one machine of one class at one clock.

    Args:
        clock: The machine's clock, or None for one never read.
        entries: The registry.
        class_name: The machine's class.

    Returns:
        The warnings raised.
    """
    return balance.clocked_draw_of(
        balance_fx.world_machines(balance_fx.clocked(class_name, clock)), entries
    ).warnings


def _collectibles(
    *records: objects.ObjectRecord,
    pairs: tuple[objects.Collectable, ...] = (),
    level_count: int = 1,
) -> tuple[WorldWarning, ...]:
    """Run the collectibles audit over a synthetic world.

    Args:
        records: The object records.
        pairs: The collected pairs.
        level_count: 0 for the flat reader's provenance.

    Returns:
        The warnings raised.
    """
    model = collectibles_fx.world_of(records, pairs, level_count=level_count)
    return collectibles.collectibles_of(model).warnings


def _footprint(*records: objects.ObjectRecord) -> tuple[WorldWarning, ...]:
    """Run the footprint audit over a synthetic world.

    Args:
        records: The object records.

    Returns:
        The warnings raised.
    """
    return footprint.footprint_of(footprint_fx.world(records)).warnings


def _undecoded_entry_world() -> tuple[WorldWarning, ...]:
    """One decoded stack beside one element the save layer did not decode.

    Returns:
        The warnings raised.
    """
    stacks = inventory_fx.container(inventory_fx.stack("Desc_OreIron_C", 4), None)
    held = inventory_fx.entry({"mSyntheticStacks": stacks})
    model = inventory_fx.world(by_record_index={0: held})
    return inventory.inventory_of(model).warnings


#: Code constant name to the call that must raise it. Keyed by NAME, the form
#: the derivation yields, so the parametrised id is the constant a reader greps.
FIXTURES: Final[Mapping[str, Firing]] = {
    # balance.py
    "WARN_BALANCE_DRAW_UNMODELED": lambda: (
        balance.draw_of(
            balance_fx.built(balance_fx.whole_world_counts()), balance_fx.whole_world_registry()
        ).warnings
    ),
    "WARN_BALANCE_NOTHING_BUILT": lambda: (
        balance.draw_of(balance_fx.built({}), balance_fx.modeled_registry()).warnings
    ),
    "WARN_BALANCE_PRODUCING_UNAVAILABLE": lambda: (
        balance.starvation_of(
            balance_fx.world_machines(balance_fx.machine(None, balance_fx.RECIPE_CLASS))
        ).warnings
    ),
    "WARN_BALANCE_MACHINE_STATE_UNREAD": lambda: (
        balance.starvation_of(
            balance_fx.world_machines(
                balance_fx.machine(True, balance_fx.RECIPE_CLASS),
                balance_fx.machine(None, balance_fx.RECIPE_CLASS),
            )
        ).warnings
    ),
    "WARN_BALANCE_CLOCK_ELIDED": lambda: (
        balance.clocked_draw_of(
            balance_fx.world_machines(balance_fx.elided(balance_fx.FIXED_WHOLE)),
            balance_fx.modeled_registry(),
        ).warnings
    ),
    "WARN_BALANCE_CLOCK_UNREAD": lambda: _clocked_draw(None, balance_fx.modeled_registry()),
    "WARN_BALANCE_CLOCKED_DRAW_UNMODELED": lambda: _clocked_draw(
        Fraction(1), balance_fx.registry()
    ),
    "WARN_BALANCE_CLOCKED_DRAW_BOUNDED": lambda: _clocked_draw(
        Fraction(1, 2), balance_fx.bracketed_registry(), balance_fx.FIXED_THIRD
    ),
    "WARN_BALANCE_NO_MACHINES_CLOCKED": lambda: (
        balance.clocked_draw_of(balance_fx.world_machines(), balance_fx.modeled_registry()).warnings
    ),
    "WARN_BALANCE_PRODUCTION_UNMODELED": lambda: _balance_composite(belts=True),
    "WARN_BALANCE_GENERATION_UNMODELED": lambda: (
        production_fx.production(
            production_fx.whole_world_counts(), production_fx.whole_world_generators()
        ).warnings
    ),
    "WARN_BALANCE_PRODUCTION_NAMEPLATE": lambda: (
        production_fx.production(
            production_fx.modeled_world_counts(), production_fx.modeled_generators()
        ).warnings
    ),
    "WARN_BALANCE_UPSTREAM_CAUSE_UNAVAILABLE": lambda: _balance_composite(belts=False),
    # collectibles.py
    "WARN_COLLECTED_STATE_UNAVAILABLE": lambda: _collectibles(
        collectibles_fx.actor(collectibles_fx.CRYSTAL_CLASS, (1.0, 2.0, 3.0)), level_count=0
    ),
    "WARN_COLLECTED_ENTRY_UNJOINABLE": lambda: _collectibles(
        collectibles_fx.actor(collectibles_fx.CRYSTAL_CLASS, (1.0, 2.0, 3.0), instance_name=""),
        pairs=(collectibles_fx.collected(""),),
    ),
    "WARN_COLLECTIBLE_CLASS_NOT_SERVED": lambda: _collectibles(
        collectibles_fx.actor(collectibles_fx.OFF_LIST_CLASS, (4.0, 5.0, 6.0))
    ),
    "WARN_COLLECTIBLE_TRANSFORM_ABSENT": lambda: _collectibles(
        collectibles_fx.actor(collectibles_fx.SHRINE_CLASS, None)
    ),
    "WARN_COLLECTIBLE_COORDINATE_NON_FINITE": lambda: _collectibles(
        collectibles_fx.actor(collectibles_fx.SHRINE_CLASS, (0.0, math.nan, 0.0))
    ),
    "WARN_COLLECTIBLE_NONE_SERVED": _collectibles,
    # flow.py
    "WARN_FLOW_NO_RECIPE": lambda: _flow(_smelter(None)),
    "WARN_FLOW_RECIPE_UNKNOWN": lambda: _flow(_smelter(_UNKNOWN_RECIPE)),
    "WARN_FLOW_RATE_UNDEFINED": lambda: _flow(_smelter(synthetic.ZERO_DURATION_RECIPE)),
    "WARN_FLOW_CLOCK_UNREAD": lambda: _flow(_smelter(synthetic.PLATE_RECIPE, None)),
    "WARN_FLOW_CLOCK_REFUSED": lambda: _flow(_smelter(synthetic.PLATE_RECIPE, Fraction(-1, 2))),
    "WARN_FLOW_NOTHING_FLOWING": _flow,
    # footprint.py
    "WARN_FOOTPRINT_CLASS_NOT_CATEGORISED": lambda: _footprint(
        footprint_fx.actor(footprint_fx.UNLISTED_BUILDABLE, (1.0, 0.0, 0.0))
    ),
    "WARN_FOOTPRINT_TRANSFORM_ABSENT": lambda: _footprint(footprint_fx.actor(_MINER, None)),
    "WARN_FOOTPRINT_COORDINATE_NON_FINITE": lambda: _footprint(
        footprint_fx.actor(_MINER, (0.0, math.nan, 0.0))
    ),
    "WARN_FOOTPRINT_EXTENT_UNAVAILABLE": lambda: _footprint(
        footprint_fx.actor(_MINER, (0.0, 0.0, 0.0), scale=(1.0, math.inf, 1.0))
    ),
    "WARN_FOOTPRINT_ABSOLUTE_EXTENT_UNAVAILABLE": lambda: _footprint(
        footprint_fx.actor(_MINER, (0.0, 0.0, 0.0))
    ),
    "WARN_FOOTPRINT_WATER_REGIONS_UNAVAILABLE": lambda: _footprint(
        footprint_fx.actor(_MINER, (0.0, 0.0, 0.0))
    ),
    "WARN_FOOTPRINT_NOTHING_PLOTTED": _footprint,
    # inventory.py
    "WARN_INVENTORY_TOTAL_EMPTY": lambda: inventory.inventory_of(inventory_fx.world()).warnings,
    "WARN_INVENTORY_PAYLOAD_UNREAD": lambda: (
        inventory.inventory_of(
            inventory_fx.world(by_record_index={0: inventory_fx.entry({}, payload_read=False)})
        ).warnings
    ),
    "WARN_INVENTORY_ENTRY_UNDECODED": _undecoded_entry_world,
    "WARN_INVENTORY_STACK_EXCLUDED": lambda: (
        inventory.inventory_of(
            inventory_fx.building_world(
                inventory_fx.full(inventory_fx.ORE_PATH, 2),
                inventory_fx.save_stack(**{inventory_fx.SAVE_COUNT_NAME: 0}),
            )
        ).warnings
    ),
    # machines.py
    "WARN_MACHINES_NONE_READ": lambda: (
        machines.machines_of(
            machines_fx.world(machines_fx.entry({"mSyntheticUnrelatedQx72": 7}))
        ).warnings
    ),
    "WARN_MACHINES_PAYLOAD_UNREAD": lambda: (
        machines.machines_of(
            machines_fx.world(
                machines_fx.entry({machines.PROPERTY_PRODUCING: True}, payload_read=False)
            )
        ).warnings
    ),
    "WARN_MACHINES_OVERCLOCK_REFUSED": lambda: (
        machines.machines_of(
            machines_fx.world(machines_fx.entry({machines.PROPERTY_OVERCLOCK: 0.1}))
        ).warnings
    ),
    "WARN_MACHINES_RECIPE_REFUSED": lambda: (
        machines.machines_of(
            machines_fx.world(
                machines_fx.entry({}, machines_fx.recipe_reference(machines_fx.FOREIGN_ASSET))
            )
        ).warnings
    ),
    # network.py
    "WARN_NETWORK_NO_NODE_JOINED": lambda: (
        network.network_of(
            network_fx.world(
                nodes=(
                    network_fx.node(network_fx.BARE_NODE_INSTANCE, network_fx.BARE_NODE_POSITION),
                ),
                records=(network_fx.record(network_fx.MINER_CLASS, network_fx.MINER_INSTANCE),),
                by_record_index={0: network_fx.entry()},
            )
        ).warnings
    ),
    "WARN_NETWORK_NO_NODE_POPULATION": lambda: network.network_of(network_fx.world()).warnings,
    "WARN_NETWORK_PAYLOAD_UNREAD": lambda: (
        network.network_of(
            network_fx.world(
                records=(network_fx.record(network_fx.MINER_CLASS, network_fx.MINER_INSTANCE),),
                by_record_index={0: network_fx.entry(payload_read=False)},
            )
        ).warnings
    ),
    "WARN_NETWORK_TOPOLOGY_UNAVAILABLE": lambda: network.network_of(network_fx.world()).warnings,
    # overlay.py
    "WARN_OVERLAY_EDIT_REFUSED": lambda: _overlay(
        overlay.RemoveMachines(recipe_class_name=synthetic.PLATE_RECIPE, count=2)
    ),
    "WARN_OVERLAY_RECIPE_UNKNOWN": lambda: _overlay(
        overlay.AddMachines(recipe_class_name=_UNKNOWN_RECIPE, count=1, clock=Fraction(1))
    ),
    "WARN_OVERLAY_DRAW_UNAVAILABLE": _overlay,
    "WARN_OVERLAY_CLOCK_ABOVE_BASE": lambda: _overlay(
        overlay.AddMachines(
            recipe_class_name=synthetic.PLATE_RECIPE, count=1, clock=Fraction(3, 2)
        ),
        priced=True,
    ),
    "WARN_OVERLAY_CLOCK_UNCHECKED": lambda: _overlay(
        overlay.AddMachines(recipe_class_name=synthetic.PLATE_RECIPE, count=1, clock=Fraction(1))
    ),
    # placement.py
    "WARN_BUILT_TRANSFORM_ABSENT": lambda: (
        placement.placement_of(
            placement_fx.world(records=(placement_fx.actor(_MINER, None),))
        ).warnings
    ),
    "WARN_PLACEMENT_COORDINATE_NON_FINITE": lambda: (
        placement.placement_of(
            placement_fx.world(nodes=(placement_fx.node(_NODE, (math.inf, 0.0, 0.0)),))
        ).warnings
    ),
    "WARN_PLACEMENT_BOUNDS_UNDEFINED": lambda: (
        placement.placement_of(placement_fx.world()).warnings
    ),
    "WARN_PLACEMENT_ORIENTATION_NON_FINITE": lambda: (
        placement.placement_of(
            placement_fx.world(
                nodes=(
                    placement_fx.node(_NODE, (1.0, 2.0, 3.0), rotation=(math.inf, 0.0, 0.0, 1.0)),
                )
            )
        ).warnings
    ),
    "WARN_BUILT_CLASS_NOT_PLOTTED": lambda: (
        placement.placement_of(
            placement_fx.world(
                records=(placement_fx.actor(_UNPLOTTED_BUILT_CLASS, (7.0, 8.0, 9.0)),)
            )
        ).warnings
    ),
}


def uncovered(table: Iterable[str], derived: Iterable[str]) -> list[str]:
    """The derived codes the table holds no fixture for, sorted.

    Args:
        table: The constant names the table covers.
        derived: The constant names the package defines.

    Returns:
        Every derived name absent from the table.
    """
    return sorted(set(derived) - set(table))


def orphaned(table: Iterable[str], derived: Iterable[str]) -> list[str]:
    """The table's names the package no longer defines, sorted.

    Args:
        table: The constant names the table covers.
        derived: The constant names the package defines.

    Returns:
        Every table name absent from the derived set.
    """
    return sorted(set(table) - set(derived))


def test_the_derived_set_is_not_vacuous() -> None:
    derived = defining_modules()
    assert derived, "the walk found no WARN_* code, so every arm below grades nothing"
    assert all(name.startswith("WARN_") for name in derived), sorted(derived)


def test_every_derived_code_has_a_firing_fixture() -> None:
    missing = uncovered(FIXTURES, defining_modules())
    assert missing == [], "no fixture fires: " + ", ".join(missing)


def test_every_fixture_names_a_code_the_package_defines() -> None:
    stale = orphaned(FIXTURES, defining_modules())
    assert stale == [], "fixture for a code no audit module defines: " + ", ".join(stale)


def test_dropping_any_one_fixture_is_named_alone() -> None:
    """Each drop adds exactly its own name to what the completeness arm reports.

    RELATIVE TO THE TABLE AS IT STANDS, not to an all-green table, so that a
    real gap reddens the completeness arm alone and never this one beside it.
    """
    derived = defining_modules()
    baseline = uncovered(FIXTURES, derived)
    assert len(FIXTURES) > 1, "a drop over a one-entry table proves nothing about the others"
    stale = orphaned(FIXTURES, derived)
    for name in sorted(set(FIXTURES) & set(derived)):
        remaining = [other for other in FIXTURES if other != name]
        assert uncovered(remaining, derived) == sorted({*baseline, name}), name
        assert orphaned(remaining, derived) == stale, name


@pytest.mark.parametrize("name", sorted(FIXTURES), ids=sorted(FIXTURES))
def test_the_fixture_raises_its_code(name: str) -> None:
    code = getattr(audit_package, name)
    raised = {warning.code for warning in FIXTURES[name]()}
    assert code in raised, f"{name} ({code}) did not fire; raised {sorted(raised)}"
