"""Where everything in a world IS - the placement model behind an interactive map.

WHAT THIS MODULE OWNS
-----------------------
One pure function over one ``clockspeed.save.world.WorldModel``, returning a
frozen :class:`WorldPlacement`. It is the COMPUTATION half of an interactive
world map, and it lives here because ``clockspeed/surface/`` never computes
(CLAUDE.md section 2.1) and ``audit/`` is the layer that consumes a whole world
model (``docs/ARCHITECTURE.md`` section 1.1).

It reads no save, no docs file and no install. Its only input is the model.

A COORDINATE LEAVES AS AN EXACT DECIMAL STRING, NEVER AS A NUMBER
-------------------------------------------------------------------
``clockspeed/surface/api/world.py`` states the reason it withheld node
coordinates in the first place: "their coordinates are float32 and a bare JSON
number is the IEEE double non-negotiable 6 keeps out of the answer path". That
objection is to the WIRE TYPE and not to the value, so the fix is a rendering
rather than a refusal, and the rendering belongs here rather than in the
serializer for two reasons.

- ``surface/`` never computes, and choosing how a stored value is written down
  is a computation. A serializer that formatted a float would be the seam
  breach wearing a format string.
- **A ROUNDING DONE HERE CANNOT BE UNDONE BY A CONSUMER.** So the rendering is
  ``repr(float(value))`` - Python's shortest round-trip decimal for a double -
  which means ``float(published) == stored`` exactly, for every finite value.
  A fixed number of decimal places would be shorter, prettier and lossy, and
  the loss would be invisible in every test that compared the rendered text to
  a rendered expectation.

The unit is the game's own and is published as :data:`COORDINATE_UNITS` rather
than assumed by the reader, because a map that silently mixed centimetres with
metres is wrong by a factor no consumer can detect from the numbers.

A NON-FINITE COORDINATE IS SKIPPED AND FLAGGED, NOT PUBLISHED
---------------------------------------------------------------
``repr(float("inf"))`` is ``'inf'``, which is not a decimal string a consumer
can parse as a position, and one such value poisons a bounding box for the whole
world. So a placement carrying a non-finite component is skipped and counted
under :data:`WARN_PLACEMENT_COORDINATE_NON_FINITE`. Non-negotiable 7: flagged
and skipped, never fatal and never silently wrong - and a silently widened
bounding box is exactly the silently-wrong half.

THE BUILT POPULATION IS AN ALLOWLIST, AND THE DISTINCTION IS NOT COSMETIC
--------------------------------------------------------------------------
:data:`BUILT_CLASS_ALLOWLIST` is a closed frozenset of class names that MAY be
published. It is deliberately not a denylist of classes to hide. A denylist over
class names leaks by construction: it is a claim about every name that does not
exist yet, and this project has measured one defect wearing four different
fields across four green commits before an allowlist of good values held it.

WHAT IS ON IT TODAY IS EVERY ``Build_*_C`` SPELLING THIS PROJECT HAS MEASURED.
It began as nine names recovered from ``docs/_archive/spike-report-s1-s2-s3-s7.md``
and ``docs/LEDGER.md``, which were every spelling the TREE carried - and three of
those nine turned out to be the only three that exist in the world this project
develops against. A census of that world's own actor classes, read only and
reported as class names and counts, supplied the rest: extraction, power,
storage and the landmark buildings that are what make a plan view legible.

NO SPELLING HERE WAS INVENTED FROM MEMORY, and that rule is why the list grew by
measurement rather than by recall. A name that does not exist ships a filter
which silently matches nothing, and a world with no generators in it looks
exactly the same.

WHAT BELONGS HERE when somebody extends it: an extractor, a generator, a
production building, a store, or a landmark - the things whose placement a map
reader acts on. What does NOT belong: belts, pipes, foundations, walls, poles,
signs and lights. Those are present in enormous numbers, carry a transform each,
and would bury everything the operator asked about under the scenery. In the
development world they are the great majority of what is built.

WHAT IS SKIPPED IS COUNTED AND PUBLISHED, under
:data:`WARN_BUILT_CLASS_NOT_PLOTTED`. A filter that drops the rest in silence
renders a fraction of a factory and says nothing about the remainder, which is
the silently-wrong half of non-negotiable 7 wearing a filter.

WHAT NEVER LEAVES THIS MODULE
-------------------------------
An instance name, a record index, a byte offset and a filesystem path. The
class name and the coordinates are the whole output. ``ResourceNode`` withholds
its ``instance_name`` from its own repr because it is world content, and
``ObjectRecord`` withholds every string for the same reason; a model assembled
here that carried either would re-open the channel both of them closed. The
substitution is the one ``WorldProperties`` already makes one layer down: a
thing's place among its siblings is its index in a tuple the consumer holds.

NODE SEMANTICS ARE UNAVAILABLE, AND THIS MODEL SAYS SO ITSELF
---------------------------------------------------------------
``docs/adr/0003-s4-node-actors-in-save.md`` measured ``mPurity``,
``mResourceNodeType`` and ``mResourceClass`` at ZERO occurrences across three
worlds and four game builds: a save stores deltas from level defaults and a
node's resource type never changes from the level asset. So this model can say
where every node is and cannot say what any of them holds.

``load_world`` already raises that advisory into ``WorldModel.warnings``, and
this model RAISES IT AGAIN rather than leaving a consumer to go find it. A
consumer of :class:`WorldPlacement` holds this object and not the world model,
and the seam discipline's own rule is that a consumer must never reach into a
sub-model to find a flag. The CODE is imported from its owner
(``clockspeed.save.world.WARN_NODE_SEMANTICS_UNAVAILABLE``) rather than spelled
again here, so the two cannot drift; the DETAIL is authored here because it is
addressed to a reader looking at a map rather than at a load.

:attr:`WorldPlacement.node_semantics_available` is a FIELD rather than a module
constant for the same reason the wire contract makes ``purity_known`` a field:
the day an asset-extraction path exists, one model can go True without every
consumer having to be rewritten around a constant that used to be False.
"""

# SEAM DISCIPLINE (BOOTSTRAP.md section 6).
# Each layer consumes only the layer below it through a stated model.
# solve/ never reads a save. advisor/ never reads the raw docs file.
# surface/ never computes. A layer that reaches past its neighbor is a
# design bug.
#
# THE ONE MODEL BELOW THIS ONE IS `clockspeed.save.world.WorldModel`, and this
# module holds nothing else from that package at runtime except the two types
# it must name to read the model at all and the ONE warning code whose owner is
# there. `load_world` is not imported: this layer never opens a save.

from __future__ import annotations

import math
from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, Final

from clockspeed.save.world import WARN_NODE_SEMANTICS_UNAVAILABLE, WorldWarning

if TYPE_CHECKING:
    from collections.abc import Mapping

    from clockspeed.save.world import WorldModel

__all__ = [
    "BUILT_CLASS_ALLOWLIST",
    "COORDINATE_UNITS",
    "SOURCE_PLACEMENT",
    "WARN_BUILT_CLASS_NOT_PLOTTED",
    "WARN_BUILT_TRANSFORM_ABSENT",
    "WARN_PLACEMENT_BOUNDS_UNDEFINED",
    "WARN_PLACEMENT_COORDINATE_NON_FINITE",
    "AxisBounds",
    "Placement",
    "WorldBounds",
    "WorldPlacement",
    "class_name_of_path",
    "decimal_string",
    "placement_of",
]

#: The unit every coordinate in this model is expressed in. Published rather
#: than assumed: a map that mixed units is wrong by a factor nothing in the
#: numbers reveals.
COORDINATE_UNITS: Final = "centimetres"

#: Which layer noticed a warning raised here.
SOURCE_PLACEMENT: Final = "placement"

WARN_BUILT_TRANSFORM_ABSENT: Final = "built-transform-absent"

#: The prefix every buildable class name carries. Used ONLY to count what the
#: allowlist skipped, never to admit anything - a prefix test is the denylist
#: shape this module refuses for admission, and it is safe here precisely
#: because a miscount is a wrong number in an advisory and not a wrong mark on
#: the map.
_BUILT_CLASS_PREFIX: Final = "Build_"
WARN_PLACEMENT_COORDINATE_NON_FINITE: Final = "placement-coordinate-non-finite"
WARN_PLACEMENT_BOUNDS_UNDEFINED: Final = "placement-bounds-undefined"

#: The built classes this model MAY publish. See the module docstring for why
#: this is an allowlist rather than a denylist, for where each of these nine
#: spellings was measured, for why no generator spelling appears, and for what
#: belongs here when somebody extends it.
BUILT_CLASS_ALLOWLIST: Final = frozenset(
    {
        # Extraction.
        "Build_MinerMk1_C",
        "Build_WaterPump_C",
        # Production.
        "Build_SmelterMk1_C",
        "Build_ConstructorMk1_C",
        "Build_AssemblerMk1_C",
        "Build_ManufacturerMk1_C",
        "Build_Blender_C",
        "Build_Converter_C",
        "Build_HadronCollider_C",
        "Build_QuantumEncoder_C",
        # Power.
        "Build_GeneratorCoal_C",
        "Build_GeneratorBiomass_Automated_C",
        "Build_GeneratorIntegratedBiomass_C",
        # Storage - where a reader looks for what is held.
        "Build_StorageContainerMk1_C",
        "Build_StorageIntegrated_C",
        "Build_PipeStorageTank_C",
        # Landmarks, which are what makes a plan view legible at all.
        "Build_HubTerminal_C",
        "Build_SpaceElevator_C",
        "Build_TradingPost_C",
        "Build_Mam_C",
        "Build_WorkBenchIntegrated_C",
    }
)

#: How many built actors were NOT plotted because their class is off the list
#: above. PUBLISHED RATHER THAN DISCARDED. An allowlist that drops the rest in
#: silence renders a map of one tenth of a factory and says nothing about the
#: other nine, which is the silently-wrong half of non-negotiable 7 wearing a
#: filter. The count says how much of the world this view is not showing.
WARN_BUILT_CLASS_NOT_PLOTTED: Final = "built-class-not-plotted"

#: One fixed line per warning code raised here. Keyed rather than formatted, so
#: a detail can never be built from something read out of a save - the idiom
#: ``clockspeed/save/world.py`` established for the same reason.
_WARNING_DETAIL: Final[Mapping[str, str]] = MappingProxyType(
    {
        WARN_NODE_SEMANTICS_UNAVAILABLE: (
            "every node on this map is placement only; its resource type and purity are"
            " level defaults a save never writes, so an unlabelled node is unmeasured"
            " rather than unremarkable"
        ),
        WARN_BUILT_CLASS_NOT_PLOTTED: (
            "built actors were skipped because their class is not one this view"
            " plots; belts, pipes, poles and foundations are present in numbers"
            " that would bury everything a reader acts on"
        ),
        WARN_BUILT_TRANSFORM_ABSENT: (
            "a record of an allowlisted built class carried no transform, so it was"
            " skipped rather than placed at invented coordinates; the built list is short"
            " by this many"
        ),
        WARN_PLACEMENT_COORDINATE_NON_FINITE: (
            "a placement carried a non-finite coordinate, so it was skipped rather than"
            " published as a position no consumer can parse and rather than allowed to"
            " widen the world bounds without limit"
        ),
        WARN_PLACEMENT_BOUNDS_UNDEFINED: (
            "no placement survived, so this world has no bounding box; six null axes"
            " would read as a box that was computed and came back empty"
        ),
    }
)

_AXIS_COUNT: Final = 3


@dataclass(frozen=True)
class Placement:
    """One placed thing: what class it is, and where.

    NO INSTANCE NAME, NO INDEX, NO OFFSET, NO PATH. The class name is publisher
    content (``clockspeed/save/usmap.py`` records that a class path comes from
    the asset registry and is not personal data); an instance name is a census
    of the operator's own factory and is withheld, exactly as
    ``ResourceNode.__repr__`` and ``ObjectRecord.__repr__`` withhold it.

    Attributes:
        class_name: The actor class, reduced from the record's type path by
            :func:`class_name_of_path`.
        x: The first coordinate, as an exact decimal string.
        y: The second coordinate, as an exact decimal string.
        z: The third coordinate, as an exact decimal string.
    """

    class_name: str
    x: str
    y: str
    z: str


@dataclass(frozen=True)
class AxisBounds:
    """The extent of one axis over every published placement.

    Both ends are exact decimal strings, on the same terms and for the same
    reason as a coordinate: a consumer that reconstructs the box must get the
    same numbers the placements carry, and a rounded bound can put a placement
    outside its own world.

    Attributes:
        min_value: The lowest value on this axis.
        max_value: The highest value on this axis.
    """

    min_value: str
    max_value: str


@dataclass(frozen=True)
class WorldBounds:
    """The bounding box over every published placement, node and built alike.

    EXISTS ONLY WHEN AT LEAST ONE PLACEMENT SURVIVED. A box whose axes were all
    absent would read as a box that was computed over an empty world, which is a
    different claim from "there was nothing to bound" - so
    :attr:`WorldPlacement.bounds` is None in that case and
    :data:`WARN_PLACEMENT_BOUNDS_UNDEFINED` says why.

    Attributes:
        x: The first axis' extent.
        y: The second axis' extent.
        z: The third axis' extent.
    """

    x: AxisBounds
    y: AxisBounds
    z: AxisBounds


@dataclass(frozen=True, repr=False)
class WorldPlacement:
    """Where everything this layer may publish about one world is.

    ``repr`` renders counts and flags only. Not because any field here is unsafe
    - none is - but because a test runner reprs a value before a human chooses
    what to print, and a world's entire placement list rendered into a pytest
    frame local is noise that buries the assertion. The habit is the one every
    published type in ``clockspeed/save/world.py`` already keeps.

    Attributes:
        node_placements: One entry per ``WorldModel.nodes`` member whose
            coordinates were finite, in the order the model carries them.
        node_counts: How many nodes of each class, keyed by class name and
            iterating in sorted order so two runs agree.
        built_placements: One entry per record whose class is on
            :data:`BUILT_CLASS_ALLOWLIST` and which carried a finite transform,
            in record order.
        built_counts: How many built actors of each class, on the same terms as
            ``node_counts``.
        bounds: The bounding box over BOTH populations, or None when no
            placement survived. See :class:`WorldBounds`.
        coordinate_units: :data:`COORDINATE_UNITS`, carried on the model so a
            consumer never has to import a constant to read a number.
        node_semantics_available: Always False today, and a FIELD rather than a
            constant - see the module docstring.
        warnings: Everything flagged, in the ``WorldWarning`` idiom this project
            already uses. RAISED HERE EVEN WHEN THE WORLD MODEL ALSO RAISED IT,
            because a consumer holding this object must not have to reach into a
            sub-model to find a flag.
    """

    node_placements: tuple[Placement, ...]
    node_counts: Mapping[str, int]
    built_placements: tuple[Placement, ...]
    built_counts: Mapping[str, int]
    bounds: WorldBounds | None
    coordinate_units: str
    node_semantics_available: bool
    warnings: tuple[WorldWarning, ...]

    @property
    def total_placements(self) -> int:
        """How many placements this model publishes across both populations.

        Returns:
            The count.
        """
        return len(self.node_placements) + len(self.built_placements)

    def __repr__(self) -> str:
        """Render counts and flags, and nothing about any member.

        Returns:
            The safe rendering.
        """
        return (
            f"{type(self).__name__}(nodes={len(self.node_placements)}, "
            f"node_classes={len(self.node_counts)}, "
            f"built={len(self.built_placements)}, "
            f"built_classes={len(self.built_counts)}, "
            f"bounded={self.bounds is not None}, "
            f"node_semantics_available={self.node_semantics_available}, "
            f"warnings={len(self.warnings)})"
        )


def class_name_of_path(type_path: str) -> str:
    """Reduce a class path to the bare class name the allowlist is keyed by.

    THE SAME RULE ``clockspeed/save/objects.py`` ``class_name_of`` APPLIES, and
    it is written again here deliberately rather than imported. This layer
    consumes the world MODEL; reaching into the save package for a string helper
    would be the reach-past-your-neighbour the seam discipline forbids, for a
    one-line rule. The duplication is pinned instead of trusted:
    ``tests/audit/test_placement.py::test_the_local_class_name_rule_agrees_with_the_save_layers_own``
    is the only place in this package that imports the save layer's own helper,
    and it exists so the two rules cannot drift apart silently - which matters
    because a built actor matched by a different rule than the one the save
    layer matched a node with is a filter nobody can reason about.

    A path with no dot is already a bare name and comes back unchanged, which is
    what keeps a mod-authored or hand-written identifier from resolving to an
    empty string.

    Args:
        type_path: The class path as read, namespaced or bare.

    Returns:
        The text after the final dot, or the whole input when there is none.
    """
    return type_path.rpartition(".")[2] if "." in type_path else type_path


def decimal_string(value: float) -> str:
    """Render one stored coordinate as its shortest round-trip decimal string.

    ``repr`` of a double is the shortest decimal that reads back as the same
    double, so ``float(decimal_string(v)) == v`` for every finite ``v``. That
    exactness is the whole point: the wire forbids a JSON float and a rounding
    done here cannot be undone by a consumer.

    Args:
        value: The stored coordinate. A float32 widened to a double in practice,
            which is what ``objects.Transform`` carries.

    Returns:
        The decimal rendering.
    """
    return repr(float(value))


def _warning(code: str, count: int = 1) -> WorldWarning:
    """Build one warning from this module's own fixed detail table.

    Args:
        code: One of this module's ``WARN_*`` constants, or the imported node
            semantics code.
        count: How many occurrences it aggregates.

    Returns:
        The warning.
    """
    return WorldWarning(
        source=SOURCE_PLACEMENT,
        code=code,
        detail=_WARNING_DETAIL[code],
        count=count,
    )


def _placement_of(
    class_name: str, translation: tuple[float, float, float]
) -> tuple[Placement, tuple[float, float, float]] | None:
    """Build one placement, or refuse a non-finite one.

    THERE IS NO ARITY GUARD HERE ON PURPOSE. ``objects.Transform.translation``
    and ``ResourceNode.translation`` are both declared as three-tuples, so a
    length check is unreachable under the declared type and mypy says so; a
    guard the type system has already discharged is a branch no test can reach
    and therefore an untested claim about what the save layer does.

    Args:
        class_name: The already-reduced class name.
        translation: The three stored coordinates.

    Returns:
        The placement together with its widened coordinates, or None when any
        coordinate is not finite.
    """
    x, y, z = (float(axis) for axis in translation)
    if not (math.isfinite(x) and math.isfinite(y) and math.isfinite(z)):
        return None
    placement = Placement(
        class_name=class_name,
        x=decimal_string(x),
        y=decimal_string(y),
        z=decimal_string(z),
    )
    return placement, (x, y, z)


def _counts(placements: tuple[Placement, ...]) -> Mapping[str, int]:
    """Tally placements per class in a deterministic order.

    Sorted rather than insertion ordered, so two runs over one model produce
    mappings that iterate identically as well as compare equal.

    Args:
        placements: The published placements.

    Returns:
        A read-only mapping from class name to count.
    """
    tally: dict[str, int] = {}
    for placement in placements:
        tally[placement.class_name] = tally.get(placement.class_name, 0) + 1
    return MappingProxyType(dict(sorted(tally.items())))


def _bounds(triples: list[tuple[float, float, float]]) -> WorldBounds | None:
    """Compute the bounding box over every surviving placement.

    Computed from the WIDENED COORDINATES rather than by re-parsing the
    published strings. The round trip would be exact, but a bounding box derived
    from its own rendering is one edit away from being derived from a rounded
    one.

    Args:
        triples: One widened coordinate triple per published placement.

    Returns:
        The box, or None when there is nothing to bound.
    """
    if not triples:
        return None
    axes = [
        AxisBounds(
            min_value=decimal_string(min(triple[index] for triple in triples)),
            max_value=decimal_string(max(triple[index] for triple in triples)),
        )
        for index in range(_AXIS_COUNT)
    ]
    return WorldBounds(x=axes[0], y=axes[1], z=axes[2])


def placement_of(model: WorldModel) -> WorldPlacement:
    """Compute where everything publishable in one world is.

    PURE, AND TOTAL. Every input produces a model: an empty world, a world with
    no built actor and a world whose every placement was refused all return a
    valid :class:`WorldPlacement` carrying the flags that say so. Nothing here
    raises, because a map that refuses to render is strictly worse than a map
    that renders what it has and names what it lost.

    Args:
        model: The world to describe. Read only; nothing here mutates it and
            nothing here reads a save.

    Returns:
        The placement model.
    """
    node_placements: list[Placement] = []
    built_placements: list[Placement] = []
    triples: list[tuple[float, float, float]] = []
    non_finite = 0
    transform_absent = 0
    not_plotted = 0

    for node in model.nodes:
        built = _placement_of(node.class_name, node.translation)
        if built is None:
            non_finite += 1
            continue
        node_placements.append(built[0])
        triples.append(built[1])

    for record in model.objects.records:
        class_name = class_name_of_path(record.type_path)
        if class_name not in BUILT_CLASS_ALLOWLIST:
            if class_name.startswith(_BUILT_CLASS_PREFIX):
                not_plotted += 1
            continue
        if record.transform is None:
            transform_absent += 1
            continue
        placed = _placement_of(class_name, record.transform.translation)
        if placed is None:
            non_finite += 1
            continue
        built_placements.append(placed[0])
        triples.append(placed[1])

    bounds = _bounds(triples)
    warnings: list[WorldWarning] = []
    if node_placements:
        warnings.append(_warning(WARN_NODE_SEMANTICS_UNAVAILABLE, len(node_placements)))
    if not_plotted:
        warnings.append(_warning(WARN_BUILT_CLASS_NOT_PLOTTED, not_plotted))
    if transform_absent:
        warnings.append(_warning(WARN_BUILT_TRANSFORM_ABSENT, transform_absent))
    if non_finite:
        warnings.append(_warning(WARN_PLACEMENT_COORDINATE_NON_FINITE, non_finite))
    if bounds is None:
        warnings.append(_warning(WARN_PLACEMENT_BOUNDS_UNDEFINED))

    return WorldPlacement(
        node_placements=tuple(node_placements),
        node_counts=_counts(tuple(node_placements)),
        built_placements=tuple(built_placements),
        built_counts=_counts(tuple(built_placements)),
        bounds=bounds,
        coordinate_units=COORDINATE_UNITS,
        node_semantics_available=False,
        warnings=tuple(warnings),
    )
