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

from clockspeed.audit.inventory import (
    ITEM_COUNT_PROPERTY_NAMES,
    ITEM_KEY_PROPERTY_NAMES,
    SOURCE_INVENTORY,
    WARN_INVENTORY_ENTRY_UNDECODED,
    WARN_INVENTORY_PAYLOAD_UNREAD,
    WARN_INVENTORY_TOTAL_EMPTY,
    ItemTotal,
    WorldInventory,
    inventory_of,
)
from clockspeed.audit.placement import (
    BUILT_CLASS_ALLOWLIST,
    COORDINATE_UNITS,
    SOURCE_PLACEMENT,
    WARN_BUILT_TRANSFORM_ABSENT,
    WARN_PLACEMENT_BOUNDS_UNDEFINED,
    WARN_PLACEMENT_COORDINATE_NON_FINITE,
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
    "ITEM_COUNT_PROPERTY_NAMES",
    "ITEM_KEY_PROPERTY_NAMES",
    "SOURCE_INVENTORY",
    "SOURCE_PLACEMENT",
    "WARN_BUILT_TRANSFORM_ABSENT",
    "WARN_INVENTORY_ENTRY_UNDECODED",
    "WARN_INVENTORY_PAYLOAD_UNREAD",
    "WARN_INVENTORY_TOTAL_EMPTY",
    "WARN_PLACEMENT_BOUNDS_UNDEFINED",
    "WARN_PLACEMENT_COORDINATE_NON_FINITE",
    "AxisBounds",
    "ItemTotal",
    "Placement",
    "WorldBounds",
    "WorldInventory",
    "WorldPlacement",
    "class_name_of_path",
    "decimal_string",
    "inventory_of",
    "placement_of",
]
