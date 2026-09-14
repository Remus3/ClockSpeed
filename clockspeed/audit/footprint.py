"""What each built thing in a world IS on a map - category, extent, elevation.

WHAT THIS MODULE OWNS
-----------------------
One pure function over one ``clockspeed.save.world.WorldModel``, returning a
frozen :class:`WorldFootprint`. It is the COMPUTATION half of a
category-differentiated engineering schematic, and it lives here for the reason
``clockspeed/audit/placement.py`` lives here: ``clockspeed/surface/`` never
computes (CLAUDE.md section 2.1) and ``audit/`` is the layer that consumes a
whole world model.

It reads no save, no docs file and no install. Its only input is the model.

WHY IT IS A SECOND MODULE AND NOT A WIDER ``placement.py``
-------------------------------------------------------------
``placement.py`` answers "where are the things a reader acts on", and its
allowlist is deliberately short for that reason - its own docstring names belts,
pipes, poles and foundations as what does NOT belong on it, because they are the
great majority of what is built and would bury the machines. THIS MODULE ANSWERS
THE OPPOSITE QUESTION. A schematic needs the scenery precisely because the
scenery is the floor plan: a map with the machines and no foundations shows
buildings floating in a void, and a map with no belts shows a factory with
nothing connecting it.

The two therefore carry different populations on purpose, and neither is a
better version of the other. ``placement.py`` is untouched by this module.

THE CATEGORY SET IS THE CONTRACT, AND IT IS A FIELD ON THE MODEL
--------------------------------------------------------------------
:data:`FOOTPRINT_CATEGORIES` is the closed set of visual classes the map draws,
and it is republished as :attr:`WorldFootprint.categories_declared` rather than
left as a constant a consumer must import. A consumer branches on the declared
capability instead of sniffing the served rows and inferring which layers exist
- which would make a world that happens to contain no towers indistinguishable
from a model that stopped publishing towers.

THE CATEGORY MAPPING IS AN ALLOWLIST AND A SUBSTRING RULE IS NOT ALLOWED
--------------------------------------------------------------------------
:data:`CLASSES_BY_CATEGORY` maps each category to a closed frozenset of class
names. It is deliberately not a rule over spellings. "If the name contains
Conveyor it is a conveyor" reads like an allowlist and is a DENYLIST WEARING A
DISGUISE: it is a claim about every name that does not exist yet, and this
project has measured one defect wearing four different spellings across four
green commits before an allowlist of good values held it. A class off the list
is counted under :data:`WARN_FOOTPRINT_CLASS_NOT_CATEGORISED` and never guessed
at.

NO SPELLING HERE WAS INVENTED FROM MEMORY. Every name below was read, once,
out of the shipped asset registry's own ``ClassName`` values, by native class
group - the same read-only measurement path that grew ``placement.py``'s list.
A class name is publisher content (``clockspeed/save/usmap.py``: a class path
comes from the asset registry and is not personal data); nothing here was read
out of a save.

WHY ``coal_plant`` AND ``generator`` ARE TWO CATEGORIES AND NOT ONE
----------------------------------------------------------------------
The operator named the coal plant specifically, because that is the tier they
are at and the map's whole purpose is to answer "what do I have and what do I
need next" - so collapsing coal into a generic power bucket would erase the one
thing they asked to see. ADJUDICATED RULING, session 85. The first cut of this
module had twelve categories and left every other generator in the skip bucket;
that was worse than either option, because a power view that silently omits a
power source is the non-negotiable-7 failure, and a bucket holding two fifths of
the shipped buildables is too large to be sure nothing load-bearing is inside
it. So ``generator`` carries every power SOURCE that is not the coal plant, and
``coal_plant`` keeps its own layer.

A power STORE and a power SWITCH are not generators and are not in it. Neither
produces, and drawing a battery in the generator layer would inflate a power
reading a reader takes off the map.

WHAT THE CATEGORY SET STILL DOES NOT COVER, AND WHERE THAT GOES
------------------------------------------------------------------
The thirteen categories are the operator's own plus that one ruling, and are not
widened further here. Measured content outside them - the walls and beams, the
signs and lights, the rail and vehicle buildables, the decorative pieces - is
COUNTED under :data:`WARN_FOOTPRINT_CLASS_NOT_CATEGORISED` rather than filed
under the nearest category that would fit. A class filed under a category it is
not would make the map's legend say something false, which is worse than a count
that says how much is not drawn.

AN EXTENT IS A MULTIPLE, NEVER A SIZE, AND SAYS WHICH IT IS
--------------------------------------------------------------
``objects.Transform`` carries a per-axis SCALE, which is a multiplier of a base
mesh whose dimensions live in the shipped assets. NOTHING IN THIS LAYER READS
THOSE ASSETS, so an absolute footprint in centimetres is not derivable here and
is not invented here. :attr:`Footprint.extent` is therefore the scale itself,
:data:`EXTENT_UNITS` says what that means, and
:attr:`WorldFootprint.absolute_extent_available` is False with
:data:`WARN_FOOTPRINT_ABSOLUTE_EXTENT_UNAVAILABLE` behind it. A consumer that
read a scale as centimetres would be wrong by a factor nothing in the numbers
reveals - the failure ``COORDINATE_UNITS`` exists to prevent, one field over.

WHERE THE SCALE ITSELF DID NOT SURVIVE - a non-finite component - the block is
withheld WHOLE and :attr:`Footprint.extent_available` is False. All three axes
or none: a partial scale is a shape claim nothing supports. This is
``placement.py``'s rule for the same block, and it is deliberately not the
coordinate rule: a bad scale costs an extent, not a building.

ELEVATION IS AN ORDERING KEY, AND THIS MODEL SAYS WHAT z ACTUALLY IS
-----------------------------------------------------------------------
The operator's requirement is that overlapping footprints at different heights
read as readable layers rather than merging into mud, so every footprint carries
:attr:`Footprint.elevation_order` - a dense ascending rank over the whole
published population, which a consumer paints in order.

**z IS THE TRANSFORM ORIGIN'S WORLD-FRAME VERTICAL COORDINATE AND NOTHING MORE.**
It is not a storey index, it is not the building's underside, and it is not its
height. WHERE THE ORIGIN SITS INSIDE A MESH IS UNMEASURED by this project, so
two classes reporting equal z are not thereby standing on the same floor, and a
difference of one foundation's thickness is not a claim this data supports.
:data:`ELEVATION_MEANING` is carried on the model so the reader of a rank is
told, rather than left to infer a floor number from an integer.

THE RANK'S TIE-BREAK IS TOTAL ON PURPOSE. Ordering on z alone leaves every
foundation on one level in an order the dict happened to produce, so two runs
over one world could paint them differently. The key continues into category,
class name and the two remaining coordinates, which are exactly the fields this
model already publishes - so the ordering is reproducible from the published
rows alone.

WATER REGIONS ARE UNAVAILABLE, AND THAT FLAG IS NOT A PLACEHOLDER
--------------------------------------------------------------------
**THE HARD-CODED FALSE IS A RULING AND NOT AN UNFINISHED FEATURE.**
``docs/adr/0019-the-map-underlay-and-the-purity-declaration.md`` measured
``FGWaterVolume.mCanPlaceExtractor`` - exactly the flag a water layer wants - as
``EditDefaultsOnly``, with ZERO water-volume type paths in a save. It then
rejects the tempting substitute BY NAME: publishing the built water pumps as
"water coverage" would imply that every unmarked shoreline is unusable, which is
a confident wrong answer rather than a missing one. That is the silently-wrong
half of non-negotiable 7. A later reader who finds this False and "fixes" it
from the pumps is re-introducing the defect that ADR by name forbids.
:attr:`WorldFootprint.water_regions_available` is False,
:data:`WARN_FOOTPRINT_WATER_REGIONS_UNAVAILABLE` says why, and no code path here
derives a region from anything.

WHAT NEVER LEAVES THIS MODULE
-------------------------------
An instance name, a record index, a byte offset, a filesystem path, a world
token and a float. The class name, the category, the coordinates, the extent
multiple and the rank are the whole output, on the terms ``placement.py`` states
at length: an instance name is a census of the operator's own factory and is
withheld, and a coordinate leaves as an exact decimal string because the wire
forbids a JSON float and a rounding done here cannot be undone by a consumer.
"""

# SEAM DISCIPLINE (BOOTSTRAP.md section 6).
# This module consumes ONE `clockspeed.save.world.WorldModel` and computes. It
# never opens a save and never reads the raw docs file. The two helpers it takes
# from `clockspeed.audit.placement` are SIBLINGS IN THIS LAYER, not a reach past
# a neighbour: `class_name_of_path` and `decimal_string` are this layer's own
# stated renderings, and importing them is what keeps the footprint view and the
# placement view from matching classes by two different rules.

from __future__ import annotations

import math
from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, Final

from clockspeed.audit.placement import class_name_of_path, decimal_string
from clockspeed.save.world import WorldWarning

if TYPE_CHECKING:
    from collections.abc import Mapping

    from clockspeed.save.world import WorldModel

__all__ = [
    "CATEGORY_AWESOME_SINK",
    "CATEGORY_COAL_PLANT",
    "CATEGORY_CONTAINER",
    "CATEGORY_CONVEYOR",
    "CATEGORY_FOUNDATION",
    "CATEGORY_GENERATOR",
    "CATEGORY_MACHINE",
    "CATEGORY_MINER",
    "CATEGORY_OF_CLASS",
    "CATEGORY_PIPE",
    "CATEGORY_POLE",
    "CATEGORY_SPECIAL_MACHINE",
    "CATEGORY_TOWER",
    "CATEGORY_WIRING",
    "CLASSES_BY_CATEGORY",
    "COORDINATE_UNITS",
    "ELEVATION_MEANING",
    "EXTENT_UNITS",
    "FOOTPRINT_CATEGORIES",
    "SOURCE_FOOTPRINT",
    "WARN_FOOTPRINT_ABSOLUTE_EXTENT_UNAVAILABLE",
    "WARN_FOOTPRINT_CLASS_NOT_CATEGORISED",
    "WARN_FOOTPRINT_COORDINATE_NON_FINITE",
    "WARN_FOOTPRINT_EXTENT_UNAVAILABLE",
    "WARN_FOOTPRINT_NOTHING_PLOTTED",
    "WARN_FOOTPRINT_TRANSFORM_ABSENT",
    "WARN_FOOTPRINT_WATER_REGIONS_UNAVAILABLE",
    "Footprint",
    "FootprintExtent",
    "WorldFootprint",
    "footprint_of",
]

#: The unit every coordinate in this model is expressed in. The same unit
#: ``placement.py`` publishes, and published here for the same reason: a map
#: that mixed units is wrong by a factor nothing in the numbers reveals.
COORDINATE_UNITS: Final = "centimetres"

#: What an extent means here. NOT a length. See the module docstring.
EXTENT_UNITS: Final = "per-axis multiple of the class base mesh, which this layer never reads"

#: What the published elevation IS in this data, carried on the model so a
#: consumer of a rank is told rather than left to infer a storey number.
ELEVATION_MEANING: Final = (
    "the transform origin's world-frame vertical coordinate; not a storey index,"
    " not the building's underside, and not its height - where the origin sits"
    " inside a mesh is unmeasured"
)

#: Which layer noticed a warning raised here.
SOURCE_FOOTPRINT: Final = "footprint"

#: The prefix every buildable class name carries. Used ONLY to count what the
#: allowlist skipped, never to admit anything - the idiom ``placement.py``
#: established, and safe for the same reason: a miscount is a wrong number in an
#: advisory and not a wrong mark on the map.
_BUILT_CLASS_PREFIX: Final = "Build_"

CATEGORY_FOUNDATION: Final = "foundation"
CATEGORY_MACHINE: Final = "machine"
CATEGORY_MINER: Final = "miner"
CATEGORY_CONVEYOR: Final = "conveyor"
CATEGORY_PIPE: Final = "pipe"
CATEGORY_WIRING: Final = "wiring"
CATEGORY_POLE: Final = "pole"
CATEGORY_TOWER: Final = "tower"
CATEGORY_COAL_PLANT: Final = "coal_plant"
CATEGORY_GENERATOR: Final = "generator"
CATEGORY_CONTAINER: Final = "container"
CATEGORY_SPECIAL_MACHINE: Final = "special_machine"
CATEGORY_AWESOME_SINK: Final = "awesome_sink"

#: The closed set of visual classes the map draws, in the order a legend reads
#: them - ground first, then what stands on it, then what connects it. THE
#: CONTRACT. Republished as :attr:`WorldFootprint.categories_declared`.
FOOTPRINT_CATEGORIES: Final = (
    CATEGORY_FOUNDATION,
    CATEGORY_MACHINE,
    CATEGORY_MINER,
    CATEGORY_CONVEYOR,
    CATEGORY_PIPE,
    CATEGORY_WIRING,
    CATEGORY_POLE,
    CATEGORY_TOWER,
    CATEGORY_COAL_PLANT,
    CATEGORY_GENERATOR,
    CATEGORY_CONTAINER,
    CATEGORY_SPECIAL_MACHINE,
    CATEGORY_AWESOME_SINK,
)

WARN_FOOTPRINT_CLASS_NOT_CATEGORISED: Final = "footprint-class-not-categorised"
WARN_FOOTPRINT_TRANSFORM_ABSENT: Final = "footprint-transform-absent"
WARN_FOOTPRINT_COORDINATE_NON_FINITE: Final = "footprint-coordinate-non-finite"
WARN_FOOTPRINT_EXTENT_UNAVAILABLE: Final = "footprint-extent-unavailable"
WARN_FOOTPRINT_ABSOLUTE_EXTENT_UNAVAILABLE: Final = "footprint-absolute-extent-unavailable"
WARN_FOOTPRINT_WATER_REGIONS_UNAVAILABLE: Final = "footprint-water-regions-unavailable"
WARN_FOOTPRINT_NOTHING_PLOTTED: Final = "footprint-nothing-plotted"

#: One fixed line per warning code raised here. Keyed rather than formatted, so
#: a detail can never be built from something read out of a save - the idiom
#: ``clockspeed/save/world.py`` established for the same reason.
_WARNING_DETAIL: Final[Mapping[str, str]] = MappingProxyType(
    {
        WARN_FOOTPRINT_CLASS_NOT_CATEGORISED: (
            "buildables were skipped because their class is on no category's allowlist;"
            " the category set is the map's legend and a class filed under the nearest"
            " category that fits would make the legend say something false"
        ),
        WARN_FOOTPRINT_TRANSFORM_ABSENT: (
            "a record of a categorised class carried no transform, so it was skipped"
            " rather than drawn at an invented origin; a building at the world origin"
            " because its transform did not read is indistinguishable from one that is"
            " genuinely there"
        ),
        WARN_FOOTPRINT_COORDINATE_NON_FINITE: (
            "a footprint carried a non-finite coordinate, so it was skipped rather than"
            " published as a position no consumer can parse"
        ),
        WARN_FOOTPRINT_EXTENT_UNAVAILABLE: (
            "a stored per-axis scale carried a non-finite component, so the extent was"
            " withheld whole while the footprint and its coordinates were kept; a"
            " partial scale is a shape claim nothing supports"
        ),
        WARN_FOOTPRINT_ABSOLUTE_EXTENT_UNAVAILABLE: (
            "an extent here is a per-axis multiple of a base mesh this layer never"
            " reads, never a length; a consumer that took it for centimetres would be"
            " wrong by a factor nothing in the numbers reveals"
        ),
        WARN_FOOTPRINT_WATER_REGIONS_UNAVAILABLE: (
            "water volume geometry is level data a save never writes, so no water region"
            " is published; drawing the built pumps as water coverage would imply that"
            " every unmarked shoreline is unusable, which is a confident wrong answer"
            " rather than a missing one"
        ),
        WARN_FOOTPRINT_NOTHING_PLOTTED: (
            "no footprint survived, so this view is empty; an empty answer with no flag"
            " is indistinguishable from a world in which nothing has been built"
        ),
    }
)

_AXIS_COUNT: Final = 3

#: Every measured class name, per category. See the module docstring for why
#: this is an allowlist of spellings rather than a rule over spellings, and for
#: where each spelling was read.
CLASSES_BY_CATEGORY: Final[Mapping[str, frozenset[str]]] = MappingProxyType(
    {
        CATEGORY_FOUNDATION: frozenset(
            {
                "Build_DownQuarterPipeInCorner_Asphalt_8x4_C",
                "Build_DownQuarterPipeInCorner_ConcretePolished_8x4_C",
                "Build_DownQuarterPipeInCorner_Concrete_8x4_C",
                "Build_DownQuarterPipeInCorner_Grip_8x4_C",
                "Build_DownQuarterPipeOutCorner_Asphalt_8x4_C",
                "Build_DownQuarterPipeOutCorner_ConcretePolished_8x4_C",
                "Build_DownQuarterPipeOutCorner_Concrete_8x4_C",
                "Build_DownQuarterPipeOutCorner_Grip_8x4_C",
                "Build_DownQuarterPipe_Asphalt_8x4_C",
                "Build_DownQuarterPipe_ConcretePolished_8x4_C",
                "Build_DownQuarterPipe_Concrete_8x4_C",
                "Build_DownQuarterPipe_Grip_8x4_C",
                "Build_Flat_Frame_01_C",
                "Build_FoundationGlass_01_C",
                "Build_Foundation_8x1_01_C",
                "Build_Foundation_8x2_01_C",
                "Build_Foundation_8x4_01_C",
                "Build_Foundation_Asphalt_8x1_C",
                "Build_Foundation_Asphalt_8x2_C",
                "Build_Foundation_Asphalt_8x4_C",
                "Build_Foundation_ConcretePolished_8x1_C",
                "Build_Foundation_ConcretePolished_8x2_2_C",
                "Build_Foundation_ConcretePolished_8x4_C",
                "Build_Foundation_Concrete_8x1_C",
                "Build_Foundation_Concrete_8x2_C",
                "Build_Foundation_Concrete_8x4_C",
                "Build_Foundation_Frame_01_C",
                "Build_Foundation_Metal_8x1_C",
                "Build_Foundation_Metal_8x2_C",
                "Build_Foundation_Metal_8x4_C",
                "Build_InvertedRamp_Asphalt_8x1_C",
                "Build_InvertedRamp_Asphalt_8x2_C",
                "Build_InvertedRamp_Asphalt_8x4_C",
                "Build_InvertedRamp_Concrete_8x1_C",
                "Build_InvertedRamp_Concrete_8x2_C",
                "Build_InvertedRamp_Concrete_8x4_C",
                "Build_InvertedRamp_DCorner_Asphalt_8x1_C",
                "Build_InvertedRamp_DCorner_Asphalt_8x2_C",
                "Build_InvertedRamp_DCorner_Asphalt_8x4_C",
                "Build_InvertedRamp_DCorner_Concrete_8x1_C",
                "Build_InvertedRamp_DCorner_Concrete_8x2_C",
                "Build_InvertedRamp_DCorner_Concrete_8x4_C",
                "Build_InvertedRamp_DCorner_Metal_8x1_C",
                "Build_InvertedRamp_DCorner_Metal_8x2_C",
                "Build_InvertedRamp_DCorner_Metal_8x4_C",
                "Build_InvertedRamp_DCorner_Polished_8x1_C",
                "Build_InvertedRamp_DCorner_Polished_8x2_C",
                "Build_InvertedRamp_DCorner_Polished_8x4_C",
                "Build_InvertedRamp_Metal_8x1_C",
                "Build_InvertedRamp_Metal_8x2_C",
                "Build_InvertedRamp_Metal_8x4_C",
                "Build_InvertedRamp_Polished_8x1_C",
                "Build_InvertedRamp_Polished_8x2_C",
                "Build_InvertedRamp_Polished_8x4_C",
                "Build_InvertedRamp_UCorner_Asphalt_8x1_C",
                "Build_InvertedRamp_UCorner_Asphalt_8x2_C",
                "Build_InvertedRamp_UCorner_Asphalt_8x4_C",
                "Build_InvertedRamp_UCorner_Concrete_8x1_C",
                "Build_InvertedRamp_UCorner_Concrete_8x2_C",
                "Build_InvertedRamp_UCorner_Concrete_8x4_C",
                "Build_InvertedRamp_UCorner_Metal_8x1_C",
                "Build_InvertedRamp_UCorner_Metal_8x2_C",
                "Build_InvertedRamp_UCorner_Metal_8x4_C",
                "Build_InvertedRamp_UCorner_Polished_8x1_C",
                "Build_InvertedRamp_UCorner_Polished_8x2_C",
                "Build_InvertedRamp_UCorner_Polished_8x4_C",
                "Build_QuarterPipeCorner_01_C",
                "Build_QuarterPipeCorner_02_C",
                "Build_QuarterPipeCorner_03_C",
                "Build_QuarterPipeCorner_04_C",
                "Build_QuarterPipeInCorner_Asphalt_8x4_C",
                "Build_QuarterPipeInCorner_ConcretePolished_8x4_C",
                "Build_QuarterPipeInCorner_Concrete_8x4_C",
                "Build_QuarterPipeInCorner_Grip_8x4_C",
                "Build_QuarterPipeMiddleInCorner_Asphalt_8x1_C",
                "Build_QuarterPipeMiddleInCorner_Asphalt_8x2_C",
                "Build_QuarterPipeMiddleInCorner_Asphalt_8x4_C",
                "Build_QuarterPipeMiddleInCorner_Concrete_8x1_C",
                "Build_QuarterPipeMiddleInCorner_Concrete_8x2_C",
                "Build_QuarterPipeMiddleInCorner_Concrete_8x4_C",
                "Build_QuarterPipeMiddleInCorner_Ficsit_8x1_C",
                "Build_QuarterPipeMiddleInCorner_Ficsit_8x2_C",
                "Build_QuarterPipeMiddleInCorner_Ficsit_8x4_C",
                "Build_QuarterPipeMiddleInCorner_Grip_8x1_C",
                "Build_QuarterPipeMiddleInCorner_Grip_8x2_C",
                "Build_QuarterPipeMiddleInCorner_Grip_8x4_C",
                "Build_QuarterPipeMiddleInCorner_PolishedConcrete_8x1_C",
                "Build_QuarterPipeMiddleInCorner_PolishedConcrete_8x2_C",
                "Build_QuarterPipeMiddleInCorner_PolishedConcrete_8x4_C",
                "Build_QuarterPipeMiddleOutCorner_Asphalt_4x1_C",
                "Build_QuarterPipeMiddleOutCorner_Asphalt_4x2_C",
                "Build_QuarterPipeMiddleOutCorner_Asphalt_4x4_C",
                "Build_QuarterPipeMiddleOutCorner_Concrete_4x1_C",
                "Build_QuarterPipeMiddleOutCorner_Concrete_4x2_C",
                "Build_QuarterPipeMiddleOutCorner_Concrete_4x4_C",
                "Build_QuarterPipeMiddleOutCorner_Ficsit_4x1_C",
                "Build_QuarterPipeMiddleOutCorner_Ficsit_4x2_C",
                "Build_QuarterPipeMiddleOutCorner_Ficsit_4x4_C",
                "Build_QuarterPipeMiddleOutCorner_Grip_4x1_C",
                "Build_QuarterPipeMiddleOutCorner_Grip_4x2_C",
                "Build_QuarterPipeMiddleOutCorner_Grip_4x4_C",
                "Build_QuarterPipeMiddleOutCorner_PolishedConcrete_4x1_C",
                "Build_QuarterPipeMiddleOutCorner_PolishedConcrete_4x2_C",
                "Build_QuarterPipeMiddleOutCorner_PolishedConcrete_4x4_C",
                "Build_QuarterPipeMiddle_Asphalt_8x1_C",
                "Build_QuarterPipeMiddle_Asphalt_8x2_C",
                "Build_QuarterPipeMiddle_Asphalt_8x4_C",
                "Build_QuarterPipeMiddle_Concrete_8x1_C",
                "Build_QuarterPipeMiddle_Concrete_8x2_C",
                "Build_QuarterPipeMiddle_Concrete_8x4_C",
                "Build_QuarterPipeMiddle_Ficsit_8x1_C",
                "Build_QuarterPipeMiddle_Ficsit_8x2_C",
                "Build_QuarterPipeMiddle_Ficsit_8x4_C",
                "Build_QuarterPipeMiddle_Grip_8x1_C",
                "Build_QuarterPipeMiddle_Grip_8x2_C",
                "Build_QuarterPipeMiddle_Grip_8x4_C",
                "Build_QuarterPipeMiddle_PolishedConcrete_8x1_C",
                "Build_QuarterPipeMiddle_PolishedConcrete_8x2_C",
                "Build_QuarterPipeMiddle_PolishedConcrete_8x4_C",
                "Build_QuarterPipeOutCorner_Asphalt_8x4_C",
                "Build_QuarterPipeOutCorner_ConcretePolished_8x4_C",
                "Build_QuarterPipeOutCorner_Concrete_8x4_C",
                "Build_QuarterPipeOutCorner_Grip_8x4_C",
                "Build_QuarterPipe_02_C",
                "Build_QuarterPipe_Asphalt_8x4_C",
                "Build_QuarterPipe_C",
                "Build_QuarterPipe_ConcretePolished_8x4_C",
                "Build_QuarterPipe_Concrete_8x4_C",
                "Build_QuarterPipe_Grip_8x4_C",
                "Build_RampDouble_8x1_C",
                "Build_RampDouble_Asphalt_8x1_C",
                "Build_RampDouble_Asphalt_8x2_C",
                "Build_RampDouble_Asphalt_8x4_C",
                "Build_RampDouble_C",
                "Build_RampDouble_Concrete_8x1_C",
                "Build_RampDouble_Concrete_8x2_C",
                "Build_RampDouble_Concrete_8x4_C",
                "Build_RampDouble_Metal_8x1_C",
                "Build_RampDouble_Metal_8x2_C",
                "Build_RampDouble_Metal_8x4_C",
                "Build_RampDouble_Polished_8x1_C",
                "Build_RampDouble_Polished_8x2_C",
                "Build_RampDouble_Polished_8x4_C",
                "Build_RampInverted_8x1_C",
                "Build_RampInverted_8x1_Corner_01_C",
                "Build_RampInverted_8x1_Corner_02_C",
                "Build_RampInverted_8x2_01_C",
                "Build_RampInverted_8x2_Corner_01_C",
                "Build_RampInverted_8x2_Corner_02_C",
                "Build_RampInverted_8x4_Corner_01_C",
                "Build_RampInverted_8x4_Corner_02_C",
                "Build_Ramp_8x1_01_C",
                "Build_Ramp_8x2_01_C",
                "Build_Ramp_8x4_01_C",
                "Build_Ramp_8x4_Inverted_01_C",
                "Build_Ramp_8x8x8_C",
                "Build_Ramp_Asphalt_8x1_C",
                "Build_Ramp_Asphalt_8x2_C",
                "Build_Ramp_Asphalt_8x4_C",
                "Build_Ramp_Concrete_8x1_C",
                "Build_Ramp_Concrete_8x2_C",
                "Build_Ramp_Concrete_8x4_C",
                "Build_Ramp_Diagonal_8x1_01_C",
                "Build_Ramp_Diagonal_8x1_02_C",
                "Build_Ramp_Diagonal_8x2_01_C",
                "Build_Ramp_Diagonal_8x2_02_C",
                "Build_Ramp_Diagonal_8x4_01_C",
                "Build_Ramp_Diagonal_8x4_02_C",
                "Build_Ramp_DownCorner_Asphalt_8x1_C",
                "Build_Ramp_DownCorner_Asphalt_8x2_C",
                "Build_Ramp_DownCorner_Asphalt_8x4_C",
                "Build_Ramp_DownCorner_Concrete_8x1_C",
                "Build_Ramp_DownCorner_Concrete_8x2_C",
                "Build_Ramp_DownCorner_Concrete_8x4_C",
                "Build_Ramp_DownCorner_Metal_8x1_C",
                "Build_Ramp_DownCorner_Metal_8x2_C",
                "Build_Ramp_DownCorner_Metal_8x4_C",
                "Build_Ramp_DownCorner_Polished_8x1_C",
                "Build_Ramp_DownCorner_Polished_8x2_C",
                "Build_Ramp_DownCorner_Polished_8x4_C",
                "Build_Ramp_Frame_01_C",
                "Build_Ramp_Frame_Inverted_01_C",
                "Build_Ramp_Metal_8x1_C",
                "Build_Ramp_Metal_8x2_C",
                "Build_Ramp_Metal_8x4_C",
                "Build_Ramp_Polished_8x1_C",
                "Build_Ramp_Polished_8x2_C",
                "Build_Ramp_Polished_8x4_C",
                "Build_Ramp_UpCorner_Asphalt_8x1_C",
                "Build_Ramp_UpCorner_Asphalt_8x2_C",
                "Build_Ramp_UpCorner_Asphalt_8x4_C",
                "Build_Ramp_UpCorner_Concrete_8x1_C",
                "Build_Ramp_UpCorner_Concrete_8x2_C",
                "Build_Ramp_UpCorner_Concrete_8x4_C",
                "Build_Ramp_UpCorner_Metal_8x1_C",
                "Build_Ramp_UpCorner_Metal_8x2_C",
                "Build_Ramp_UpCorner_Metal_8x4_C",
                "Build_Ramp_UpCorner_Polished_8x1_C",
                "Build_Ramp_UpCorner_Polished_8x2_C",
                "Build_Ramp_UpCorner_Polished_8x4_C",
                "Build_Roof_A_01_C",
                "Build_Roof_A_02_C",
                "Build_Roof_A_03_C",
                "Build_Roof_A_04_C",
                "Build_Roof_Orange_01_C",
                "Build_Roof_Orange_02_C",
                "Build_Roof_Orange_03_C",
                "Build_Roof_Orange_04_C",
                "Build_Roof_Tar_01_C",
                "Build_Roof_Tar_02_C",
                "Build_Roof_Tar_03_C",
                "Build_Roof_Tar_04_C",
                "Build_Roof_Window_01_C",
                "Build_Roof_Window_02_C",
                "Build_Roof_Window_03_C",
                "Build_Roof_Window_04_C",
                "Build_Stair_Asphalt_8x1_C",
                "Build_Stair_Asphalt_8x2_C",
                "Build_Stair_Asphalt_8x4_C",
                "Build_Stair_Concrete_8x1_C",
                "Build_Stair_Concrete_8x2_C",
                "Build_Stair_Concrete_8x4_C",
                "Build_Stair_FicsitSet_8x1_01_C",
                "Build_Stair_FicsitSet_8x2_01_C",
                "Build_Stair_FicsitSet_8x4_01_C",
                "Build_Stair_GripMetal_8x1_C",
                "Build_Stair_GripMetal_8x2_C",
                "Build_Stair_GripMetal_8x4_C",
                "Build_Stair_PolishedConcrete_8x1_C",
                "Build_Stair_PolishedConcrete_8x2_C",
                "Build_Stair_PolishedConcrete_8x4_C",
            }
        ),
        CATEGORY_MACHINE: frozenset(
            {
                "Build_AssemblerMk1_C",
                "Build_Blender_C",
                "Build_ConstructorMk1_C",
                "Build_FoundryMk1_C",
                "Build_ManufacturerMk1_C",
                "Build_OilRefinery_C",
                "Build_Packager_C",
                "Build_SmelterMk1_C",
                "Build_WorkBenchIntegrated_C",
                "Build_WorkBench_C",
                "Build_Workshop_C",
            }
        ),
        CATEGORY_MINER: frozenset(
            {
                "Build_FrackingExtractor_C",
                "Build_FrackingSmasher_C",
                "Build_MinerMk1_C",
                "Build_MinerMk2_C",
                "Build_MinerMk3_C",
                "Build_OilPump_C",
                "Build_WaterPump_C",
            }
        ),
        CATEGORY_CONVEYOR: frozenset(
            {
                "Build_ConveyorBeltMk1_C",
                "Build_ConveyorBeltMk2_C",
                "Build_ConveyorBeltMk3_C",
                "Build_ConveyorBeltMk4_C",
                "Build_ConveyorBeltMk5_C",
                "Build_ConveyorBeltMk6_C",
                "Build_ConveyorLiftMk1_C",
                "Build_ConveyorLiftMk2_C",
                "Build_ConveyorLiftMk3_C",
                "Build_ConveyorLiftMk4_C",
                "Build_ConveyorLiftMk5_C",
                "Build_ConveyorLiftMk6_C",
            }
        ),
        CATEGORY_PIPE: frozenset(
            {
                "Build_PipelineJunction_Cross_C",
                "Build_PipelineJunction_T_C",
                "Build_PipelineMK2_C",
                "Build_PipelineMK2_NoIndicator_C",
                "Build_PipelinePumpMk2_C",
                "Build_PipelinePump_C",
                "Build_Pipeline_C",
                "Build_Pipeline_NoIndicator_C",
                "Build_Valve_C",
            }
        ),
        CATEGORY_WIRING: frozenset(
            {
                "Build_PowerLine_C",
                "Build_XmassLightsLine_C",
            }
        ),
        CATEGORY_POLE: frozenset(
            {
                "Build_ConveyorCeilingAttachment_C",
                "Build_ConveyorPoleStackable_C",
                "Build_ConveyorPoleWall_C",
                "Build_ConveyorPole_C",
                "Build_HyperPoleStackable_C",
                "Build_PipeHyperSupport_C",
                "Build_PipeSupportStackable_C",
                "Build_PipelineSupportWallHole_C",
                "Build_PipelineSupportWall_C",
                "Build_PipelineSupport_C",
                "Build_PowerPoleMk1_C",
                "Build_PowerPoleMk2_C",
                "Build_PowerPoleMk3_C",
                "Build_PowerPoleWallDouble_C",
                "Build_PowerPoleWallDouble_Mk2_C",
                "Build_PowerPoleWallDouble_Mk3_C",
                "Build_PowerPoleWall_C",
                "Build_PowerPoleWall_Mk2_C",
                "Build_PowerPoleWall_Mk3_C",
                "Build_PowerTowerPlatform_C",
            }
        ),
        CATEGORY_TOWER: frozenset(
            {
                "Build_LookoutTower_C",
                "Build_PowerTower_C",
                "Build_RadarTower_C",
            }
        ),
        CATEGORY_COAL_PLANT: frozenset(
            {
                "Build_GeneratorCoal_C",
            }
        ),
        # EVERY POWER SOURCE THAT IS NOT THE COAL PLANT. A power store and a
        # power switch are deliberately absent: neither PRODUCES, and drawing a
        # battery in the generator layer would inflate a power reading a reader
        # takes off the map.
        CATEGORY_GENERATOR: frozenset(
            {
                "Build_AlienPowerBuilding_C",
                "Build_GeneratorBiomass_Automated_C",
                "Build_GeneratorFuel_C",
                "Build_GeneratorGeoThermal_C",
                "Build_GeneratorIntegratedBiomass_C",
                "Build_GeneratorNuclear_C",
            }
        ),
        CATEGORY_CONTAINER: frozenset(
            {
                "Build_CentralStorage_C",
                "Build_IndustrialTank_C",
                "Build_PipeStorageTank_C",
                "Build_StackableShelf_C",
                "Build_StorageContainerMk1_C",
                "Build_StorageContainerMk2_C",
                "Build_StorageHazard_C",
                "Build_StorageIntegrated_C",
                "Build_StorageMedkit_C",
                "Build_StoragePlayer_C",
            }
        ),
        CATEGORY_SPECIAL_MACHINE: frozenset(
            {
                "Build_Converter_C",
                "Build_HadronCollider_C",
                "Build_HubTerminal_C",
                "Build_Mam_C",
                "Build_QuantumEncoder_C",
                "Build_SpaceElevator_C",
                "Build_TradingPost_C",
            }
        ),
        CATEGORY_AWESOME_SINK: frozenset(
            {
                "Build_ResourceSinkShop_C",
                "Build_ResourceSink_C",
            }
        ),
    }
)

#: The flattened allowlist: one class name to exactly one category. Built from
#: :data:`CLASSES_BY_CATEGORY` rather than typed twice, and sorted so two runs
#: iterate identically. A class present in two categories would collide here and
#: ``tests/audit/test_footprint.py`` grades that it does not.
CATEGORY_OF_CLASS: Final[Mapping[str, str]] = MappingProxyType(
    {
        class_name: category
        for category in FOOTPRINT_CATEGORIES
        for class_name in sorted(CLASSES_BY_CATEGORY[category])
    }
)


@dataclass(frozen=True)
class FootprintExtent:
    """A footprint's per-axis extent, as a MULTIPLE and never as a length.

    Three exact decimal strings on the same terms as a coordinate: the wire
    forbids a JSON float and a rounding done here cannot be undone by a
    consumer. See :data:`EXTENT_UNITS` and the module docstring for why no
    absolute size is derivable in this layer.

    Attributes:
        x: The first axis' scale multiple.
        y: The second axis' scale multiple.
        z: The third axis' scale multiple.
    """

    x: str
    y: str
    z: str


@dataclass(frozen=True)
class Footprint:
    """One built thing as the map draws it: what class, what kind, where, how big.

    NO INSTANCE NAME, NO INDEX, NO OFFSET, NO PATH - the list
    ``clockspeed/audit/placement.py`` states and the reasons it states.

    Attributes:
        class_name: The actor class, reduced from the record's type path by
            ``placement.class_name_of_path``.
        category: One of :data:`FOOTPRINT_CATEGORIES`. The visual class the map
            draws this as.
        x: The first coordinate, as an exact decimal string.
        y: The second coordinate, as an exact decimal string.
        z: The third coordinate, as an exact decimal string. SEE
            :data:`ELEVATION_MEANING` before reading it as a height.
        extent: The per-axis scale multiple, or None when the stored scale held
            a non-finite component and the block was withheld whole.
        extent_available: Whether :attr:`extent` is present. A FIELD rather than
            a null to sniff for, so a consumer branches on a declared capability
            instead of guessing what a null meant.
        elevation_order: This footprint's dense ascending rank by elevation over
            the whole published population, tie-broken totally. Paint in
            ascending order and overlapping layers read as layers. NOT a storey
            number - see :data:`ELEVATION_MEANING`.
    """

    class_name: str
    category: str
    x: str
    y: str
    z: str
    extent: FootprintExtent | None
    extent_available: bool
    elevation_order: int


@dataclass(frozen=True, repr=False)
class WorldFootprint:
    """Everything this layer publishes about how one world is built.

    ``repr`` renders counts and flags only, the habit every published type in
    ``clockspeed/save/world.py`` keeps: a test runner reprs a value before a
    human chooses what to print, and a world's entire footprint list rendered
    into a pytest frame local is noise that buries the assertion.

    Attributes:
        footprints: One entry per categorised record that carried finite
            coordinates, in record order.
        categories_declared: :data:`FOOTPRINT_CATEGORIES`, carried on the model.
            THE CONTRACT, and a field rather than a constant so a consumer
            branches on what this model declares instead of importing a name.
        category_counts: How many footprints per category, keyed by category and
            iterating in sorted order so two runs agree. A category with none
            present is ABSENT here rather than zero - its declaration lives in
            ``categories_declared``, which is the honest place to learn that a
            layer exists and is empty.
        coordinate_units: :data:`COORDINATE_UNITS`.
        extent_units: :data:`EXTENT_UNITS`. Never a length.
        elevation_meaning: :data:`ELEVATION_MEANING`.
        absolute_extent_available: Always False today. An extent here is a
            multiple; the base mesh it multiplies lives in the shipped assets and
            no path in this layer reads them.
        water_regions_available: Always False, and NOT A PLACEHOLDER. Water
            volume geometry is level data a save never writes - see the module
            docstring and ``docs/adr/0019``.
        elevation_ordering_available: Whether every footprint carries a usable
            rank. True whenever a footprint was published at all.
        skipped_class_count: How many buildables were not drawn because their
            class is on no category's allowlist. PUBLISHED RATHER THAN
            DISCARDED, and carried as a field as well as a warning count so a
            consumer can show coverage without parsing an advisory.
        warnings: Everything flagged, in the ``WorldWarning`` idiom this project
            already uses.
    """

    footprints: tuple[Footprint, ...]
    categories_declared: tuple[str, ...]
    category_counts: Mapping[str, int]
    coordinate_units: str
    extent_units: str
    elevation_meaning: str
    absolute_extent_available: bool
    water_regions_available: bool
    elevation_ordering_available: bool
    skipped_class_count: int
    warnings: tuple[WorldWarning, ...]

    @property
    def by_elevation(self) -> tuple[Footprint, ...]:
        """The same footprints, in the order a painter draws them.

        Ascending by :attr:`Footprint.elevation_order`, which is already a dense
        total rank, so this is a reordering and never a re-derivation - a second
        sort key here would be a second ordering nothing reconciles.

        Returns:
            The footprints, lowest first.
        """
        return tuple(sorted(self.footprints, key=lambda placed: placed.elevation_order))

    def __repr__(self) -> str:
        """Render counts and flags, and nothing about any member.

        Returns:
            The safe rendering.
        """
        return (
            f"{type(self).__name__}(footprints={len(self.footprints)}, "
            f"categories_declared={len(self.categories_declared)}, "
            f"categories_served={len(self.category_counts)}, "
            f"skipped_class_count={self.skipped_class_count}, "
            f"absolute_extent_available={self.absolute_extent_available}, "
            f"water_regions_available={self.water_regions_available}, "
            f"elevation_ordering_available={self.elevation_ordering_available}, "
            f"warnings={len(self.warnings)})"
        )


def _warning(code: str, count: int = 1) -> WorldWarning:
    """Build one warning from this module's own fixed detail table.

    Args:
        code: One of this module's ``WARN_*`` constants.
        count: How many occurrences it aggregates.

    Returns:
        The warning.
    """
    return WorldWarning(
        source=SOURCE_FOOTPRINT,
        code=code,
        detail=_WARNING_DETAIL[code],
        count=count,
    )


def _extent_of(scale: tuple[float, float, float]) -> FootprintExtent | None:
    """Render a stored per-axis scale, or withhold the whole block.

    ALL THREE OR NONE. A partial scale is a shape claim nothing supports, and
    ``'inf'`` is not a decimal string a consumer can read as an extent. The
    footprint survives either way: an extent enters no ordering and no position,
    so refusing a building over one would hide it from the map over a field the
    map does not measure.

    Args:
        scale: The three stored components.

    Returns:
        The extent, or None when any component is not finite.
    """
    x, y, z = (float(part) for part in scale)
    if not (math.isfinite(x) and math.isfinite(y) and math.isfinite(z)):
        return None
    return FootprintExtent(x=decimal_string(x), y=decimal_string(y), z=decimal_string(z))


def _counts(footprints: tuple[Footprint, ...]) -> Mapping[str, int]:
    """Tally footprints per category in a deterministic order.

    Sorted rather than insertion ordered, so two runs over one model produce
    mappings that iterate identically as well as compare equal.

    Args:
        footprints: The published footprints.

    Returns:
        A read-only mapping from category to count.
    """
    tally: dict[str, int] = {}
    for placed in footprints:
        tally[placed.category] = tally.get(placed.category, 0) + 1
    return MappingProxyType(dict(sorted(tally.items())))


def _warnings_for(counted: tuple[tuple[str, int], ...]) -> list[WorldWarning]:
    """Raise one warning per code that actually has occurrences behind it.

    ORDER IS THE CALLER'S AND ZERO IS A SILENCE, on the terms
    ``clockspeed/audit/placement.py`` states: a warning that says "this happened
    zero times" is noise a consumer has to filter and is indistinguishable, at a
    glance, from one that happened.

    Args:
        counted: One ``(code, count)`` pair per advisory driven by a tally, in
            publication order.

    Returns:
        The warnings, in that order, for the codes with a non-zero count.
    """
    return [_warning(code, count) for code, count in counted if count]


def _elevation_key(entry: tuple[float, Footprint]) -> tuple[float, str, str, str, str]:
    """The total ordering a rank is assigned from.

    TOTAL ON PURPOSE. Ordering on elevation alone leaves every foundation on one
    level in whatever order the record table happened to carry, so two runs over
    one world could paint them differently. The key continues into fields this
    model already publishes, so the ordering is reproducible from the published
    rows alone rather than from a record index no consumer holds.

    Args:
        entry: The widened elevation and the footprint it belongs to.

    Returns:
        The sort key.
    """
    elevation, placed = entry
    return (elevation, placed.category, placed.class_name, placed.x, placed.y)


def _ranked(pending: list[tuple[float, Footprint]]) -> tuple[Footprint, ...]:
    """Assign every footprint its dense ascending elevation rank.

    Ranked from the WIDENED elevation rather than by re-parsing the published
    string. The round trip would be exact, but an ordering derived from its own
    rendering is one edit away from being derived from a rounded one.

    The returned tuple is in the caller's RECORD ORDER, not in rank order - the
    rank is a field and :attr:`WorldFootprint.by_elevation` is the reordering,
    so a consumer that wants either gets it without the model choosing for it.

    Args:
        pending: One ``(elevation, footprint)`` pair per surviving record, in
            record order.

    Returns:
        The footprints in record order, each carrying its rank.
    """
    order: dict[int, int] = {}
    for rank, entry in enumerate(sorted(pending, key=_elevation_key)):
        order[id(entry[1])] = rank
    return tuple(
        Footprint(
            class_name=placed.class_name,
            category=placed.category,
            x=placed.x,
            y=placed.y,
            z=placed.z,
            extent=placed.extent,
            extent_available=placed.extent_available,
            elevation_order=order[id(placed)],
        )
        for _, placed in pending
    )


def footprint_of(model: WorldModel) -> WorldFootprint:
    """Compute what every built thing in one world is on a map.

    PURE, AND TOTAL. Every input produces a model: an empty world, a world with
    no categorised class and a world whose every record was refused all return a
    valid :class:`WorldFootprint` carrying the flags that say so. Nothing here
    raises, because a map that refuses to render is strictly worse than a map
    that renders what it has and names what it lost.

    Args:
        model: The world to describe. Read only; nothing here mutates it and
            nothing here reads a save.

    Returns:
        The footprint model.
    """
    pending: list[tuple[float, Footprint]] = []
    not_categorised = 0
    transform_absent = 0
    coordinate_non_finite = 0
    extent_unavailable = 0

    for record in model.objects.records:
        class_name = class_name_of_path(record.type_path)
        category = CATEGORY_OF_CLASS.get(class_name)
        if category is None:
            # THE PREFIX TEST COUNTS AND NEVER ADMITS. See the module docstring:
            # a prefix rule is the denylist shape this module refuses for
            # admission, and it is safe here because a miscount is a wrong
            # number in an advisory and not a wrong mark on the map.
            if class_name.startswith(_BUILT_CLASS_PREFIX):
                not_categorised += 1
            continue
        if record.transform is None:
            transform_absent += 1
            continue
        x, y, z = (float(axis) for axis in record.transform.translation)
        if not (math.isfinite(x) and math.isfinite(y) and math.isfinite(z)):
            coordinate_non_finite += 1
            continue
        extent = _extent_of(record.transform.scale)
        if extent is None:
            extent_unavailable += 1
        pending.append(
            (
                z,
                Footprint(
                    class_name=class_name,
                    category=category,
                    x=decimal_string(x),
                    y=decimal_string(y),
                    z=decimal_string(z),
                    extent=extent,
                    extent_available=extent is not None,
                    elevation_order=0,
                ),
            )
        )

    footprints = _ranked(pending)
    warnings = _warnings_for(
        (
            (WARN_FOOTPRINT_CLASS_NOT_CATEGORISED, not_categorised),
            (WARN_FOOTPRINT_TRANSFORM_ABSENT, transform_absent),
            (WARN_FOOTPRINT_COORDINATE_NON_FINITE, coordinate_non_finite),
            (WARN_FOOTPRINT_EXTENT_UNAVAILABLE, extent_unavailable),
        )
    )
    # NOT IN THE TALLY LIST ABOVE, because none of these three is driven by a
    # count. The first two fire on a STANDING PROPERTY of this data - an extent
    # is a multiple and a save carries no water geometry - and they are raised on
    # every world deliberately, because a consumer holding this object and no
    # other must not have to go find either fact. The third fires on the ABSENCE
    # of a footprint, and its occurrence count is always one.
    warnings.append(_warning(WARN_FOOTPRINT_ABSOLUTE_EXTENT_UNAVAILABLE))
    warnings.append(_warning(WARN_FOOTPRINT_WATER_REGIONS_UNAVAILABLE))
    if not footprints:
        warnings.append(_warning(WARN_FOOTPRINT_NOTHING_PLOTTED))

    return WorldFootprint(
        footprints=footprints,
        categories_declared=FOOTPRINT_CATEGORIES,
        category_counts=_counts(footprints),
        coordinate_units=COORDINATE_UNITS,
        extent_units=EXTENT_UNITS,
        elevation_meaning=ELEVATION_MEANING,
        absolute_extent_available=False,
        water_regions_available=False,
        elevation_ordering_available=bool(footprints),
        skipped_class_count=not_categorised,
        warnings=tuple(warnings),
    )
