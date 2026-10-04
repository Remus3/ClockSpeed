"""Pillar 3: the whole-world audit of what is built against what should be.

Owns (BOOTSTRAP.md sections 4 and 6): idle and starved machines with their
upstream cause, overclock waste, belt and pipe saturation with the binding
segment, power headroom and brownout risk, under-extracted claimed nodes, and
achieved sink-point throughput.
"""

# SEAM DISCIPLINE (BOOTSTRAP.md section 6).
# Each layer consumes only the layer below it through a stated model.
# solve/ never reads a save. advisor/ never reads the raw docs file.
# surface/ never computes. A layer that reaches past its neighbor is a
# design bug.
#
# Below this layer are two stated models: the world model from
# clockspeed.save.world and the results of clockspeed.solve. This layer never
# opens a .sav and never opens the raw docs file - it diffs one model against
# the other and reports findings.
#
# A finding is a fact with a cause attached. "This machine is idle" is half an
# audit; "this machine is idle because the segment upstream is saturated" is
# the whole one. Reporting the symptom without the binding constraint pushes
# the work onto the operator, which is the one budget this project spends
# against (CONVENTIONS.md section 0).

# EXPORTS ONLY. The two models below are the layer's public surface for CS-978 -
# where everything in a world is, and what it holds - and they are re-exported
# here so a consumer names the LAYER rather than a module inside it. No logic
# lives in this file and none may: an __init__ that computes is one that runs on
# every import of anything in the package.
#
# THE WARNING-CODE RULE (CS-1023). Every ``WARN_*`` constant that a module in
# this package DEFINES - assigns at module level in its own source - is
# re-exported here, and no other ``WARN_*`` name is. "Defines" is the rule, not
# "has in its namespace": ``placement.py`` imports and raises the save layer's
# ``WARN_NODE_SEMANTICS_UNAVAILABLE``, and that code stays owned by
# ``clockspeed.save.world`` rather than being published a second time from this
# layer. ``tests/audit/test_package_exports.py`` derives the set by walking the
# package and holds this list equal to it, so a code added to any module here
# reddens that arm until it is re-exported.

from clockspeed.audit.balance import (
    WARN_BALANCE_DRAW_UNMODELED,
    WARN_BALANCE_MACHINE_STATE_UNREAD,
    WARN_BALANCE_NOTHING_BUILT,
    WARN_BALANCE_PRODUCING_UNAVAILABLE,
    WARN_BALANCE_PRODUCTION_UNMODELED,
    WARN_BALANCE_UPSTREAM_CAUSE_UNAVAILABLE,
)
from clockspeed.audit.collectibles import (
    WARN_COLLECTED_ENTRY_UNJOINABLE,
    WARN_COLLECTED_STATE_UNAVAILABLE,
    WARN_COLLECTIBLE_CLASS_NOT_SERVED,
    WARN_COLLECTIBLE_COORDINATE_NON_FINITE,
    WARN_COLLECTIBLE_NONE_SERVED,
    WARN_COLLECTIBLE_TRANSFORM_ABSENT,
)
from clockspeed.audit.flow import (
    GAP_FLOW_CLOCK_REFUSED,
    GAP_FLOW_CLOCK_UNREAD,
    GAP_FLOW_KINDS,
    GAP_FLOW_NO_RECIPE,
    GAP_FLOW_RATE_UNDEFINED,
    GAP_FLOW_RECIPE_UNKNOWN,
    SOURCE_FLOW,
    WARN_FLOW_CLOCK_REFUSED,
    WARN_FLOW_CLOCK_UNREAD,
    WARN_FLOW_NO_RECIPE,
    WARN_FLOW_NOTHING_FLOWING,
    WARN_FLOW_RATE_UNDEFINED,
    WARN_FLOW_RECIPE_UNKNOWN,
    FlowGap,
    ItemFlow,
    RecipeGroup,
    WorldFlow,
    flow_of,
)
from clockspeed.audit.footprint import (
    WARN_FOOTPRINT_ABSOLUTE_EXTENT_UNAVAILABLE,
    WARN_FOOTPRINT_CLASS_NOT_CATEGORISED,
    WARN_FOOTPRINT_COORDINATE_NON_FINITE,
    WARN_FOOTPRINT_EXTENT_UNAVAILABLE,
    WARN_FOOTPRINT_NOTHING_PLOTTED,
    WARN_FOOTPRINT_TRANSFORM_ABSENT,
    WARN_FOOTPRINT_WATER_REGIONS_UNAVAILABLE,
)
from clockspeed.audit.inventory import (
    EXCLUDED_COUNT_DISAGREES,
    EXCLUDED_COUNT_UNREAD,
    EXCLUDED_ITEM_ABSENT,
    EXCLUDED_ITEM_UNRECOGNISED,
    ITEM_COUNT_PROPERTY_NAMES,
    ITEM_KEY_PROPERTY_NAMES,
    SOURCE_INVENTORY,
    STACK_EXCLUSION_REASONS,
    WARN_INVENTORY_ENTRY_UNDECODED,
    WARN_INVENTORY_PAYLOAD_UNREAD,
    WARN_INVENTORY_STACK_EXCLUDED,
    WARN_INVENTORY_TOTAL_EMPTY,
    BuildingInventory,
    ItemTotal,
    WorldInventory,
    inventory_of,
)
from clockspeed.audit.machines import (
    WARN_MACHINES_NONE_READ,
    WARN_MACHINES_OVERCLOCK_REFUSED,
    WARN_MACHINES_PAYLOAD_UNREAD,
    WARN_MACHINES_RECIPE_REFUSED,
)
from clockspeed.audit.network import (
    WARN_NETWORK_NO_NODE_JOINED,
    WARN_NETWORK_NO_NODE_POPULATION,
    WARN_NETWORK_PAYLOAD_UNREAD,
    WARN_NETWORK_TOPOLOGY_UNAVAILABLE,
)
from clockspeed.audit.overlay import (
    KIND_ADD,
    KIND_DEMAND,
    KIND_REMOVE,
    KIND_SWAP,
    OUTCOME_APPLIED,
    OUTCOME_REFUSED,
    OUTCOME_SKIPPED,
    REFUSED_BUILDING_MISMATCH,
    REFUSED_BUILDING_UNKNOWN,
    REFUSED_BUILDING_UNRESOLVED,
    REFUSED_PLACEMENT_SHORT,
    REFUSED_SWAP_TO_SELF,
    REFUSED_TOO_FEW_MACHINES,
    SKIPPED_RECIPE_UNKNOWN,
    SOURCE_OVERLAY,
    WARN_OVERLAY_CLOCK_ABOVE_BASE,
    WARN_OVERLAY_CLOCK_UNCHECKED,
    WARN_OVERLAY_DRAW_UNAVAILABLE,
    WARN_OVERLAY_EDIT_REFUSED,
    WARN_OVERLAY_RECIPE_UNKNOWN,
    AddMachines,
    EditRecord,
    ItemDelta,
    Overlay,
    OverlayApplication,
    OverlayEditError,
    OverlayEvaluation,
    RemoveMachines,
    SetDemand,
    SwapRecipe,
    apply_overlay,
    evaluate_overlay,
)
from clockspeed.audit.placement import (
    BUILT_CLASS_ALLOWLIST,
    COORDINATE_UNITS,
    SOURCE_PLACEMENT,
    WARN_BUILT_CLASS_NOT_PLOTTED,
    WARN_BUILT_TRANSFORM_ABSENT,
    WARN_PLACEMENT_BOUNDS_UNDEFINED,
    WARN_PLACEMENT_COORDINATE_NON_FINITE,
    WARN_PLACEMENT_ORIENTATION_NON_FINITE,
    AxisBounds,
    Placement,
    WorldBounds,
    WorldPlacement,
    class_name_of_path,
    decimal_string,
    placement_of,
)

__all__ = [
    "BUILT_CLASS_ALLOWLIST",
    "COORDINATE_UNITS",
    "EXCLUDED_COUNT_DISAGREES",
    "EXCLUDED_COUNT_UNREAD",
    "EXCLUDED_ITEM_ABSENT",
    "EXCLUDED_ITEM_UNRECOGNISED",
    "GAP_FLOW_CLOCK_REFUSED",
    "GAP_FLOW_CLOCK_UNREAD",
    "GAP_FLOW_KINDS",
    "GAP_FLOW_NO_RECIPE",
    "GAP_FLOW_RATE_UNDEFINED",
    "GAP_FLOW_RECIPE_UNKNOWN",
    "ITEM_COUNT_PROPERTY_NAMES",
    "ITEM_KEY_PROPERTY_NAMES",
    "KIND_ADD",
    "KIND_DEMAND",
    "KIND_REMOVE",
    "KIND_SWAP",
    "OUTCOME_APPLIED",
    "OUTCOME_REFUSED",
    "OUTCOME_SKIPPED",
    "REFUSED_BUILDING_MISMATCH",
    "REFUSED_BUILDING_UNKNOWN",
    "REFUSED_BUILDING_UNRESOLVED",
    "REFUSED_PLACEMENT_SHORT",
    "REFUSED_SWAP_TO_SELF",
    "REFUSED_TOO_FEW_MACHINES",
    "SKIPPED_RECIPE_UNKNOWN",
    "SOURCE_FLOW",
    "SOURCE_INVENTORY",
    "SOURCE_OVERLAY",
    "SOURCE_PLACEMENT",
    "STACK_EXCLUSION_REASONS",
    "WARN_BALANCE_DRAW_UNMODELED",
    "WARN_BALANCE_MACHINE_STATE_UNREAD",
    "WARN_BALANCE_NOTHING_BUILT",
    "WARN_BALANCE_PRODUCING_UNAVAILABLE",
    "WARN_BALANCE_PRODUCTION_UNMODELED",
    "WARN_BALANCE_UPSTREAM_CAUSE_UNAVAILABLE",
    "WARN_BUILT_CLASS_NOT_PLOTTED",
    "WARN_BUILT_TRANSFORM_ABSENT",
    "WARN_COLLECTED_ENTRY_UNJOINABLE",
    "WARN_COLLECTED_STATE_UNAVAILABLE",
    "WARN_COLLECTIBLE_CLASS_NOT_SERVED",
    "WARN_COLLECTIBLE_COORDINATE_NON_FINITE",
    "WARN_COLLECTIBLE_NONE_SERVED",
    "WARN_COLLECTIBLE_TRANSFORM_ABSENT",
    "WARN_FLOW_CLOCK_REFUSED",
    "WARN_FLOW_CLOCK_UNREAD",
    "WARN_FLOW_NOTHING_FLOWING",
    "WARN_FLOW_NO_RECIPE",
    "WARN_FLOW_RATE_UNDEFINED",
    "WARN_FLOW_RECIPE_UNKNOWN",
    "WARN_FOOTPRINT_ABSOLUTE_EXTENT_UNAVAILABLE",
    "WARN_FOOTPRINT_CLASS_NOT_CATEGORISED",
    "WARN_FOOTPRINT_COORDINATE_NON_FINITE",
    "WARN_FOOTPRINT_EXTENT_UNAVAILABLE",
    "WARN_FOOTPRINT_NOTHING_PLOTTED",
    "WARN_FOOTPRINT_TRANSFORM_ABSENT",
    "WARN_FOOTPRINT_WATER_REGIONS_UNAVAILABLE",
    "WARN_INVENTORY_ENTRY_UNDECODED",
    "WARN_INVENTORY_PAYLOAD_UNREAD",
    "WARN_INVENTORY_STACK_EXCLUDED",
    "WARN_INVENTORY_TOTAL_EMPTY",
    "WARN_MACHINES_NONE_READ",
    "WARN_MACHINES_OVERCLOCK_REFUSED",
    "WARN_MACHINES_PAYLOAD_UNREAD",
    "WARN_MACHINES_RECIPE_REFUSED",
    "WARN_NETWORK_NO_NODE_JOINED",
    "WARN_NETWORK_NO_NODE_POPULATION",
    "WARN_NETWORK_PAYLOAD_UNREAD",
    "WARN_NETWORK_TOPOLOGY_UNAVAILABLE",
    "WARN_OVERLAY_CLOCK_ABOVE_BASE",
    "WARN_OVERLAY_CLOCK_UNCHECKED",
    "WARN_OVERLAY_DRAW_UNAVAILABLE",
    "WARN_OVERLAY_EDIT_REFUSED",
    "WARN_OVERLAY_RECIPE_UNKNOWN",
    "WARN_PLACEMENT_BOUNDS_UNDEFINED",
    "WARN_PLACEMENT_COORDINATE_NON_FINITE",
    "WARN_PLACEMENT_ORIENTATION_NON_FINITE",
    "AddMachines",
    "AxisBounds",
    "BuildingInventory",
    "EditRecord",
    "FlowGap",
    "ItemDelta",
    "ItemFlow",
    "ItemTotal",
    "Overlay",
    "OverlayApplication",
    "OverlayEditError",
    "OverlayEvaluation",
    "Placement",
    "RecipeGroup",
    "RemoveMachines",
    "SetDemand",
    "SwapRecipe",
    "WorldBounds",
    "WorldFlow",
    "WorldInventory",
    "WorldPlacement",
    "apply_overlay",
    "class_name_of_path",
    "decimal_string",
    "evaluate_overlay",
    "flow_of",
    "inventory_of",
    "placement_of",
]
