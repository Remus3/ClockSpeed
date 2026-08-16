"""The world-state model, and the one entry point that produces it.

WHAT THIS MODULE OWNS
-----------------------
``docs/ARCHITECTURE.md`` section 1.1: **the world model is the only save-layer
type any higher layer is allowed to hold.** ``audit/`` and ``progress/`` consume
it; nothing above this layer sees save bytes, a chunk frame or a property map.

It owns one more thing that nothing else can own: **the two version scalars.**
``chunks.decompress_body`` discards both the header version and the save
version, and every reader in ``objects`` needs both. This module is the only
place that holds them at once, so threading them is not plumbing - it is the
seam, and getting it wrong is the defect the corpus was built to catch.

THE COMPOSITION, IN ORDER
---------------------------
``workdir.copy_for_read`` -> ``header.parse_header`` -> ``chunks.decompress_body``
-> ``usmap.cached_usmap`` -> ``objects.parse_body`` -> :class:`WorldModel`.

Nothing here re-implements any of them. Each sibling was proven separately and
this module is deliberately thin: every byte-level decision lives one layer
down, where it has its own fixtures and its own error taxonomy.

TWO DISPATCHES, THREADED SEPARATELY AND NEVER DERIVED
-------------------------------------------------------
The body length prefix width follows the HEADER version; the transform delta
follows the SAVE version. Across the entire real library the two covary, so a
composer that read one scalar and derived the other is correct on every real
file and on every real-shaped fixture. Both are passed through explicitly, and
``tests/save/test_world.py::test_save_cross_proves_the_composer_threads_both_scalars``
asserts the PAIR against ``synthetic.SAVE_CROSS``, whose pair occurs in no real
file and which is therefore the only fixture that can separate them.

AN ABSENT PROPERTY MAP IS THE DEFAULT PATH, NOT AN EDGE CASE
--------------------------------------------------------------
``usmap.cached_usmap()`` returns None on a machine with no install and NEVER
raises for absence. CI and every fresh clone run in exactly that state, so the
None branch is the common one. It is recorded as a warning and the load
continues with no property map: ``objects.parse_object_headers`` takes
``known_classes=None`` to mean "no registry was supplied", and a walk that
flagged every class in that state would report a world of pure unknown content
rather than a world it has not checked.

``objects.parse_properties`` takes a NON-OPTIONAL ``PropertyMap``, which is the
trap in the seam: a composer that called it unconditionally is a ``TypeError``
on every machine that has never had the game installed. **This module does not
call it at all**, and the reason is not the None case.

WHAT EITHER PROPERTY READER CAN DECODE IS ``objects``' FACT, and it is stated
at ``objects.read_properties`` rather than a second time here. A capability
restated in a second module is one that goes stale in the second module, which
is precisely what happened to this paragraph: it named a reason - the data
section's grammar - that had since been measured, while the conclusion it was
attached to stayed true and kept the whole sentence reading as current.

WHAT THIS MODULE STATES IS NARROWER AND IS ITS OWN. No property value reaches
:class:`WorldModel`, because nothing here asks for one.
``tests/save/test_world.py::test_the_world_layer_states_no_property_capability_it_does_not_own``
asserts that from the AST rather than from this sentence, so it stays true
whatever the readers one layer down later learn to decode - and the day this
module wants a value, that test is what turns red and sends the author here.

A mapping that is PRESENT and unreadable is a different thing entirely and does
raise, because collapsing the two would hide a shipped-format change behind the
same value that means "no install".

UNLOCK STATE IS HONESTLY EMPTY, AND SAYS SO
---------------------------------------------
ADR 0004 measured WHICH unlock fields exist in a mature world - 246 schematic
paths including the alt-recipe purchases, 360 recipe paths, the game phase, the
research trees, the scanned resources and the feature booleans. It did **not**
measure their serialized grammar, and :func:`_read_unlocks` - the single
producer of the published state - returns :data:`EMPTY_UNLOCK_STATE` with no
read of its own. So :class:`UnlockState` is published EMPTY with a warning
saying the unlock grammar is unmeasured, per non-negotiable 7 - unknown content
is flagged and skipped, never fatal and never silently wrong.

That is not a placeholder to be quietly filled in by inference. ADR 0004's
single most important engineering consequence is that **an absent unlock array
means EMPTY, never missing and never an error.** A reader that assumes presence
either crashes on a fresh onboarding world or reports a mature world's state for
a new one, and the second failure produces confident wrong advice. An empty
unlock set that says so is correct; a fabricated one is not.

WHICH SAVES THIS CAN ACTUALLY READ - ALL FOUR PAIRS, AS A SKELETON
--------------------------------------------------------------------
**A green test suite here does NOT mean "the save reader reads saves."** Read
this paragraph before believing one. The limit MOVED under CS-407; it did not
go away, and the new one is easier to overlook than the old one.

``load_world`` reads a body whose ``(header version, save version)`` pair is in
``objects.MEASURED_BODY_LAYOUTS``. That set now holds all four pairs the
operator's real library contains, and each walks a real body of its pair to the
exact final byte with nothing left over:

- **header 10** with **save 36**
- **header 13** with **save 42**
- **header 14** with **save 52**
- **header 14** with **save 60**

**WHAT IS MEASURED IS THE SKELETON, NOT THE BODY.** Roughly three quarters of
every real body is opaque property payload this walk steps over by declared
length - 69.5% to 77.7% across the eight real save-52 files, and 12100463 of
18086289 bytes on the one real save-42 file. What the grammar names is a 1.8%
to 2.7% framing skeleton plus its length-prefixed strings. So a record COUNT
out of this module is trustworthy and a record's PROPERTIES do not exist yet.

A pair outside the measured set is still refused EAGERLY with a
:class:`WorldLoadError` whose cause is ``objects.UnsupportedBodyLayoutError``,
before a byte of the body is walked. ``synthetic.SAVE_CROSS`` - header 14 with
save 36 - is such a pair, and deliberately: it occurs in no real file, so no
real body of it can ever be measured, and it is exactly the case where deriving
a layout from a neighbour sharing one version scalar looks reasonable. A layout
guessed that way produces a walk that is confidently WRONG rather than one that
fails, and non-negotiable 7 forbids exactly that: unknown content is flagged
and skipped, never fatal, and NEVER SILENTLY WRONG. An empty or wrong world is
worse than a refusal, because nothing downstream can tell.

CS-407 also measured that a real body is not a flat record table at all: it
opens with a version-dependent preamble and then carries a LIST OF LEVELS, each
with its own record table, collectable list and payload section.

THE BODY LAYOUT IS AN EXPLICIT CHOICE, AND ITS DEFAULT IS THE REAL ONE
------------------------------------------------------------------------
``objects`` exposes two readers, and this module routes between them on the
caller's ``body_layout`` argument rather than on a probe of the bytes:

- :data:`BODY_LAYOUT_LEVELLED`, **the default**, calls ``objects.parse_body`` -
  the layout a real save actually has.
- :data:`BODY_LAYOUT_FLAT` calls ``objects.parse_object_headers`` - the single
  flat table the synthetic corpus is built on. It pins the offset arithmetic and
  the two-scalar version dispatch, ``synthetic.SAVE_CROSS`` above all, which is
  a header/save pair that exists in no real file and therefore has no real body
  to be levelled.

**A silent try-flat-then-levelled fallback is refused.** It would keep every
corpus fixture green while hiding the wrong-shape defect this routing exists to
remove: a real body that failed the levelled walk would quietly fall through to
a reader that returns a wrong count instead of an error. Sniffing the bytes for
a shape is the same defect wearing a probe. So the choice is named, it is the
caller's, and the value a caller gets by not thinking about it is the one that
is correct for a REAL save.

An unrecognised layout is a CALLER bug, not a bad save, so it raises
``ValueError`` and deliberately NOT :class:`WorldLoadError` - a caller catching
the load error to tolerate a corrupt save must not thereby swallow its own typo.

Resource-node SEMANTICS are likewise unavailable, and that is a measurement
rather than a gap. ADR 0003: a save stores deltas from level defaults, so a
node's purity and resource type - which never change from the level asset - are
never written to the save at all. Geometry is exact and free; semantics need
the asset-extraction path. :class:`ResourceNode` carries placement and nothing
else, and says so.

Geometry is free only for a record that HAS a transform, and CS-430 is the case
where one does not. A record whose class is a measured node class but which
carries no transform is skipped - inventing coordinates for it would be the
confident wrong answer non-negotiable 7 forbids - and it is now also FLAGGED
with :data:`WARN_NODE_TRANSFORM_ABSENT`. The skip was always right; the silence
was the defect, because a node list short by one is indistinguishable from a
world that holds one fewer node.

IT IS A RECURRING SHAPE IN THIS PACKAGE rather than a one-off, which is the
reason to state it here rather than in a comment: a check that was missing
(CS-417), a check that discarded without flagging (CS-419), and a filter that
dropped without flagging (CS-430) are the same defect wearing three
mechanisms. Every one of them satisfies the "never fatal" half of
non-negotiable 7 - which is the half satisfied by accident - and fails the
"never silently wrong" half, which has to be satisfied on purpose because the
failure renders as a success. No count is written here on purpose; the shape is
what a reader needs, and a tally in prose is a number with no owner.

THE ERROR TAXONOMY, AND THE COUPLING THAT MAKES IT SAFE
---------------------------------------------------------
Every sibling failure is wrapped in :class:`WorldLoadError` with
``raise ... from exc``. That chain makes the CAUSE's own text part of this
module's formatted traceback, so wrapping WIDENS the echo path that
non-negotiable 12 governs.

**It is safe here only because every sibling already guarantees its exception
text is clean** - a field name from a closed vocabulary, a byte offset, an
expected and an actual length, a version scalar, a fixed reason, and nothing
else. ``header.py``, ``chunks.py``, ``objects.py`` and ``usmap.py`` each state
that guarantee and each pin it with a planted-marker test;
``workdir.py`` renders a path only through ``locate.redact()``. **Weakening any
one of those taxonomies silently converts every wrapped error here into a
leak**, and this paragraph is the record of what that guarantee is holding up,
so nobody relaxes one without seeing the load it carries.

This module adds no message content of its own beyond a stage name from a
closed set and the cause's CLASS NAME, both of which are module-defined
vocabulary rather than anything read out of a save.

THE WORLD TOKEN IS PERSONAL DATA
----------------------------------
It identifies a world, and the advice ledger keys on it. It is legal in memory
and in the gitignored ledger, and FORBIDDEN in every tracked file, every log
line and every error message. :class:`WorldModel` therefore hand-writes its
``__repr__`` to emit counts and version scalars with the token MASKED through
``header.masked_token`` - the mask that already exists, rather than a second
one. This is the widest repr in the layer, because every consumer above holds
one of these.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Final

from clockspeed.save.chunks import ChunkError, DecompressedBody, decompress_body
from clockspeed.save.header import HeaderError, SaveHeader, masked_token, parse_header
from clockspeed.save.objects import (
    ObjectError,
    ObjectRecord,
    ObjectTable,
    class_name_of,
    parse_body,
    parse_object_headers,
)
from clockspeed.save.usmap import PropertyMap, UsmapError, cached_usmap
from clockspeed.save.workdir import WorkDirError, copy_for_read

__all__ = [
    "BODY_LAYOUTS",
    "BODY_LAYOUT_FLAT",
    "BODY_LAYOUT_LEVELLED",
    "EMPTY_UNLOCK_STATE",
    "NODE_CLASS_NAMES",
    "SOURCE_CHUNKS",
    "SOURCE_HEADER",
    "SOURCE_OBJECTS",
    "SOURCE_USMAP",
    "SOURCE_WORLD",
    "STAGES",
    "STAGE_CHUNKS",
    "STAGE_COPY",
    "STAGE_HEADER",
    "STAGE_OBJECTS",
    "STAGE_USMAP",
    "WARN_NODE_SEMANTICS_UNAVAILABLE",
    "WARN_NODE_TRANSFORM_ABSENT",
    "WARN_NO_PROPERTY_MAP",
    "WARN_UNLOCK_GRAMMAR_UNMEASURED",
    "ResourceNode",
    "UnlockState",
    "WorldLoadError",
    "WorldModel",
    "WorldWarning",
    "load_world",
    "load_world_from_bytes",
]

# ---------------------------------------------------------------------------
# The closed vocabularies
# ---------------------------------------------------------------------------

#: The stage a load failed at. A closed set, because a stage name travels into
#: an exception message and anything built from file content would be an echo
#: path.
STAGE_COPY: Final = "copy"
STAGE_HEADER: Final = "header"
STAGE_CHUNKS: Final = "chunks"
STAGE_USMAP: Final = "usmap"
STAGE_OBJECTS: Final = "objects"

STAGES: Final = (STAGE_COPY, STAGE_HEADER, STAGE_CHUNKS, STAGE_USMAP, STAGE_OBJECTS)

#: Which body reader a load uses. See the module docstring for why this is the
#: caller's explicit choice rather than a probe of the bytes.
#:
#: :data:`BODY_LAYOUT_LEVELLED` is the DEFAULT because it is what a real save
#: needs, and a default is what a caller gets by not thinking about it. The flat
#: reader is correct only for the synthetic corpus, so making IT the default
#: would mean the safe path had to be opted into - which is the arrangement that
#: produced the defect CS-409 removed.
BODY_LAYOUT_LEVELLED: Final = "levelled"
BODY_LAYOUT_FLAT: Final = "flat"

BODY_LAYOUTS: Final = (BODY_LAYOUT_LEVELLED, BODY_LAYOUT_FLAT)

#: Which layer noticed a warning. The same five names, because a caller asking
#: "where did this come from" is asking about the same layers.
SOURCE_HEADER: Final = STAGE_HEADER
SOURCE_CHUNKS: Final = STAGE_CHUNKS
SOURCE_USMAP: Final = STAGE_USMAP
SOURCE_OBJECTS: Final = STAGE_OBJECTS
SOURCE_WORLD: Final = "world"

WARN_NO_PROPERTY_MAP: Final = "no-property-map"
WARN_UNLOCK_GRAMMAR_UNMEASURED: Final = "unlock-grammar-unmeasured"
WARN_NODE_SEMANTICS_UNAVAILABLE: Final = "node-semantics-unavailable"
WARN_NODE_TRANSFORM_ABSENT: Final = "node-transform-absent"

#: One fixed line per warning code. Keyed rather than formatted, so a detail can
#: never be built from something read out of a save.
_WARNING_DETAIL: Final[Mapping[str, str]] = MappingProxyType(
    {
        WARN_NO_PROPERTY_MAP: (
            "no property mapping is available, so no class was checked against a registry;"
            " absence of a registry claims nothing about unmodelled content"
        ),
        WARN_UNLOCK_GRAMMAR_UNMEASURED: (
            "unlock state is empty because its serialized grammar has never been measured;"
            " ADR 0004 measured which fields exist and not how they are written"
        ),
        WARN_NODE_SEMANTICS_UNAVAILABLE: (
            "resource nodes carry placement only; purity and resource type are level"
            " defaults that a save never writes, so node semantics need asset extraction"
        ),
        WARN_NODE_TRANSFORM_ABSENT: (
            "a record of a measured resource-node class carried no transform, so it was"
            " skipped rather than published with invented coordinates; the node list is"
            " short by this many and their placement is unrecoverable from this save"
        ),
    }
)

#: The resource-node actor classes ADR 0003 MEASURED in a real world - 459, 118,
#: 31, 17 and 1 instance of them respectively, every one carrying a valid
#: transform. Matched on the CLASS NAME rather than on the full path, so a
#: namespaced or mod-authored path reaches the same branch.
NODE_CLASS_NAMES: Final = frozenset(
    {
        "BP_ResourceNode_C",
        "BP_FrackingSatellite_C",
        "BP_ResourceNodeGeyser_C",
        "BP_FrackingCore_C",
        "BP_ResourceDeposit_C",
    }
)


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class WorldLoadError(Exception):
    """A save could not be loaded, named by the stage that refused it.

    Deliberately NOT a subclass of any sibling error: a caller that catches this
    to tolerate a bad save must not thereby swallow a ``HeaderError`` raised by
    some other path.

    The original is attached with ``raise ... from`` rather than dropped,
    because the sibling taxonomies carry the structural detail - the field, the
    offset, the expected and actual lengths - and re-deriving it here would mean
    inventing it. See the module docstring for the guarantee that makes chaining
    safe, and for what breaks if a sibling relaxes it.

    Attributes:
        stage: One of :data:`STAGES`.
        cause_type: The class name of the wrapped error. Module-defined
            vocabulary, never a value read out of a save.
    """

    def __init__(self, stage: str, cause_type: str) -> None:
        """Build the one-line message from the two closed-vocabulary fields.

        Args:
            stage: One of :data:`STAGES`.
            cause_type: The wrapped error's class name.
        """
        self.stage = stage
        self.cause_type = cause_type
        super().__init__(f"save load failed at the {stage} stage: {cause_type}")


# ---------------------------------------------------------------------------
# The models
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class WorldWarning:
    """One thing a layer flagged and carried anyway.

    Every layer's advisories are normalised into this one stream so a consumer
    never has to reach into a sub-model to find a flag - which would be exactly
    the reach-past-your-neighbour the seam discipline forbids.

    Only the CODE and the fixed detail travel up. The scalars a sub-warning
    carries - a version pair, a byte offset, a type id - stay on the sub-warning
    and are reachable through :attr:`WorldModel.header` and
    :attr:`WorldModel.objects`, because promoting them would mean giving one
    field four different meanings depending on which layer filled it in.

    Attributes:
        source: Which layer noticed it, from the ``SOURCE_*`` constants.
        code: The originating layer's own warning code.
        detail: One fixed line naming the consequence. Never built from content.
        count: How many occurrences this aggregates.
    """

    source: str
    code: str
    detail: str
    count: int = 1


@dataclass(frozen=True)
class UnlockState:
    """What the player has unlocked.

    EMPTY ON EVERY PATH TODAY, AND THAT IS A MEASURED POSITION RATHER THAN A
    STUB. ADR 0004 established that unlock state IS recoverable from a save and
    named the fields; it did not measure their serialized grammar. Nor does this
    module hold a path by which a purchased schematic could arrive:
    :func:`_read_unlocks` is the only producer of this type and returns
    :data:`EMPTY_UNLOCK_STATE` with no read of its own. A non-empty collection
    here would therefore be an invented one.

    The load carries :data:`WARN_UNLOCK_GRAMMAR_UNMEASURED` for exactly that
    reason: an empty unlock set with no warning is indistinguishable from a
    world that genuinely has nothing unlocked, and the difference between those
    two is the difference between honest silence and confident wrong advice.

    When the grammar is measured, the absent-array rule is the one to preserve:
    an array that is not present in the file is EMPTY, never missing and never
    an error. Arrays that are still empty are simply not written.

    Attributes:
        purchased_schematics: Schematic paths bought, including the
            ``Schematic_Alternate_*`` entries that are pillar 2's alt-recipe
            purchase state.
        recipes: Unlocked recipe paths, including ``Recipe_Alternate_*``.
        current_game_phase: The phase index, or None when it was not read.
        feature_flags: Feature-level unlocks as discrete booleans - blueprints,
            building overclock, building efficiency, the map, the customizer.
            Overclock availability is a direct precondition for power and clock
            advice, so a rule requiring it declares the flag and cannot fire
            without it.
        scanned_resources: The scanned-resource state, which is the input that
            keeps ADR 0003's degraded node mode viable.
    """

    purchased_schematics: frozenset[str]
    recipes: frozenset[str]
    current_game_phase: int | None
    feature_flags: Mapping[str, bool]
    scanned_resources: frozenset[str]

    @property
    def is_empty(self) -> bool:
        """Whether nothing at all was recovered.

        Returns:
            True when every collection is empty and no phase was read.
        """
        return not (
            self.purchased_schematics
            or self.recipes
            or self.feature_flags
            or self.scanned_resources
            or self.current_game_phase is not None
        )


#: The one shape any load produces today. A module-level constant rather than a
#: fresh instance per load, because it is immutable and identical every time.
EMPTY_UNLOCK_STATE: Final = UnlockState(
    purchased_schematics=frozenset(),
    recipes=frozenset(),
    current_game_phase=None,
    feature_flags=MappingProxyType({}),
    scanned_resources=frozenset(),
)


@dataclass(frozen=True, repr=False)
class ResourceNode:
    """One resource-node actor: where it is, and nothing about what it holds.

    ADR 0003 measured both halves of that sentence. 626 node actors with 626
    valid transforms - geometry is exact and free. And ``mPurity``,
    ``mResourceNodeType`` and ``mResourceClass`` occur ZERO times in any save
    examined across three worlds and four game builds, because a save stores
    deltas from level defaults and a node's resource type never changes from
    the level asset. Semantics are not missing from this type by omission; they
    are not in the file.

    ``repr`` withholds the instance name, which is world content, and renders
    the class name, which is a game constant ADR 0003 already publishes.

    Attributes:
        class_name: The actor class, from :data:`NODE_CLASS_NAMES`.
        instance_name: The instance name, verbatim.
        translation: World coordinates, from the record's transform.
    """

    class_name: str
    instance_name: str
    translation: tuple[float, float, float]

    def __repr__(self) -> str:
        """Render the class and the coordinates, and withhold the instance name.

        Returns:
            The safe rendering.
        """
        return f"{type(self).__name__}(class_name={self.class_name!r}, at={self.translation})"


@dataclass(frozen=True, repr=False)
class WorldModel:
    """Everything above the save layer is allowed to know about a world.

    THE ONLY SAVE-LAYER TYPE A HIGHER LAYER HOLDS (``docs/ARCHITECTURE.md``
    section 1.1). ``audit/`` and ``progress/`` consume this and never save
    bytes.

    Attributes:
        token: The header's save identifier - the stable, filename-independent
            world key the advice ledger is keyed by. PERSONAL DATA: legal in
            memory and in the gitignored ledger, forbidden in every tracked
            file, log line and error message.
        header: The parsed header, carrying its own warnings and scalars.
        objects: The walked record table, carrying its own warnings and the two
            version scalars the walk was dispatched on.
        unlocks: What the player has unlocked. Empty on every path today - see
            :class:`UnlockState`.
        nodes: Resource-node actors with their placement. Geometry only.
        warnings: Every layer's advisories, normalised into one stream.
    """

    token: str
    header: SaveHeader
    objects: ObjectTable
    unlocks: UnlockState
    nodes: tuple[ResourceNode, ...]
    warnings: tuple[WorldWarning, ...]

    @property
    def contains_unmodeled_content(self) -> bool:
        """Whether this world holds content the project does not model.

        Delegated rather than recomputed, so the answer cannot drift from the
        table it is about. False when no registry was supplied: absence of a
        registry claims nothing.

        Returns:
            True when at least one class path went unresolved.
        """
        return self.objects.contains_unmodeled_content

    def __repr__(self) -> str:
        """Render counts and version scalars, with the token MASKED.

        The widest repr in the layer - every consumer above holds one of these,
        and a test runner or a logger reprs an object before a human chooses
        what to print. The map name is omitted for the same reason
        ``SaveHeader`` omits it: its POSITION is version dependent, so a
        dispatch bug would put an operator-authored string in it, and this
        rendering has to stay safe even when the parse is wrong.

        Returns:
            The safe rendering.
        """
        return (
            f"{type(self).__name__}(token={masked_token(self.token)!r}, "
            f"header_version={self.header.header_version}, "
            f"save_version={self.header.save_version}, "
            f"objects={len(self.objects.records)}, "
            f"nodes={len(self.nodes)}, "
            f"unmodelled_classes={len(self.objects.unknown_classes)}, "
            f"warnings={len(self.warnings)})"
        )


# ---------------------------------------------------------------------------
# Assembly
# ---------------------------------------------------------------------------


def _warning(source: str, code: str, count: int = 1) -> WorldWarning:
    """Build one world warning from this module's own fixed detail table.

    Args:
        source: One of the ``SOURCE_*`` constants.
        code: One of this module's ``WARN_*`` constants.
        count: How many occurrences it aggregates.

    Returns:
        The warning.
    """
    return WorldWarning(source=source, code=code, detail=_WARNING_DETAIL[code], count=count)


def _resolve_property_map(
    supplied: PropertyMap | None,
) -> tuple[PropertyMap | None, list[WorldWarning]]:
    """Take the caller's mapping, or find the installed one.

    Args:
        supplied: A mapping to use as-is, or None to resolve one.

    Returns:
        The mapping or None, and any warnings raised in getting there.

    Raises:
        WorldLoadError: A mapping file exists but could not be read or parsed.
            Absence is NOT this case and never raises.
    """
    if supplied is not None:
        return supplied, []
    try:
        found = cached_usmap()
    except UsmapError as exc:
        raise WorldLoadError(STAGE_USMAP, type(exc).__name__) from exc
    if found is None:
        return None, [_warning(SOURCE_USMAP, WARN_NO_PROPERTY_MAP)]
    return found, []


def _nodes_from(table: ObjectTable) -> tuple[tuple[ResourceNode, ...], list[WorldWarning]]:
    """Pick the resource-node actors out of a walked record table.

    THE SKIP IS CORRECT AND THE SILENCE WAS NOT (CS-430). A record whose class
    IS a measured node class but which carries no transform is still skipped -
    publishing it would mean inventing coordinates, which is the confident-wrong
    answer non-negotiable 7 exists to forbid. What changed is that the loss is
    now NAMED. Dropped silently, a world short one node is indistinguishable
    from a world that genuinely holds that many, and nothing downstream can tell
    which it is holding.

    :func:`_node_or_none` answers one question - is this a publishable node -
    and returns None for two unrelated reasons. The condition this warning names
    is therefore re-derived from the record by :func:`_untransformed_node_class`
    rather than inferred from that None, so a third future reason for None
    cannot be quietly reported as a missing transform.

    Args:
        table: The walked table.

    Returns:
        One :class:`ResourceNode` per publishable record, in file order, and the
        warning naming how many measured node records were skipped for want of a
        transform. The warning list is empty when none were.
    """
    nodes: list[ResourceNode] = []
    untransformed = 0
    for record in table.records:
        node = _node_or_none(record)
        if node is not None:
            nodes.append(node)
        elif _untransformed_node_class(record):
            untransformed += 1
    warnings = (
        [_warning(SOURCE_WORLD, WARN_NODE_TRANSFORM_ABSENT, untransformed)] if untransformed else []
    )
    return tuple(nodes), warnings


def _node_or_none(record: ObjectRecord) -> ResourceNode | None:
    """Convert one record to a node, or return None when it is not one.

    Args:
        record: The record to inspect.

    Returns:
        The node, or None when the class is not a measured node class or the
        record carried no transform.
    """
    name = class_name_of(record.type_path)
    if name not in NODE_CLASS_NAMES or record.transform is None:
        return None
    return ResourceNode(
        class_name=name,
        instance_name=record.instance_name,
        translation=record.transform.translation,
    )


def _untransformed_node_class(record: ObjectRecord) -> bool:
    """Whether this record is a measured node class that carried no transform.

    The exact condition :data:`WARN_NODE_TRANSFORM_ABSENT` names, stated once
    and asked of the record directly. A record of a class this project does not
    model is NOT this case: it is already reported through
    ``ObjectTable.unknown_classes``, and counting it here would turn every
    ordinary record in a world into a lost-node warning.

    Args:
        record: The record to inspect.

    Returns:
        True when the class name is in :data:`NODE_CLASS_NAMES` and the record
        carries no transform.
    """
    return class_name_of(record.type_path) in NODE_CLASS_NAMES and record.transform is None


def _read_unlocks() -> tuple[UnlockState, list[WorldWarning]]:
    """Recover the unlock state, which today means reporting that it cannot be.

    A function rather than a constant reference at the call site, so the place
    the real reader goes is already named and the warning cannot be dropped
    without deleting a line that says why it exists.

    Returns:
        The empty state and the warning that makes the emptiness honest.
    """
    return EMPTY_UNLOCK_STATE, [_warning(SOURCE_WORLD, WARN_UNLOCK_GRAMMAR_UNMEASURED)]


def _checked_layout(body_layout: str) -> str:
    """Refuse an unrecognised body layout before anything is parsed.

    A caller bug is not a bad save, so this is a ``ValueError`` and NOT a
    :class:`WorldLoadError` - a caller catching the load error to tolerate a
    corrupt save must not thereby swallow its own typo.

    The message renders the ALLOWED set and never the supplied value. A layout
    string is caller-supplied rather than read out of a save, so echoing it is
    not a leak today; it is withheld because "echo the argument back" is the
    habit that eventually echoes an argument holding save content, and this
    module's whole error taxonomy is built on not having that habit.

    Args:
        body_layout: The caller's choice.

    Returns:
        The layout, unchanged, when it is one of :data:`BODY_LAYOUTS`.

    Raises:
        ValueError: It is not.
    """
    if body_layout not in BODY_LAYOUTS:
        raise ValueError(f"body_layout must be one of {BODY_LAYOUTS}")
    return body_layout


def _walk_body(
    payload: bytes,
    parsed: SaveHeader,
    mapping: PropertyMap | None,
    body_layout: str,
) -> ObjectTable:
    """Route the body to the reader the caller chose.

    NO FALLBACK, BY DESIGN. Whichever reader is chosen either produces a table
    or raises; a second attempt with the other reader would turn a wrong-shape
    body into a wrong ANSWER, which is the one outcome non-negotiable 7 rules
    out. See the module docstring.

    Args:
        payload: The decompressed body, length prefix included.
        parsed: The header, for the two version scalars.
        mapping: The property map, or None when none was resolved.
        body_layout: One of :data:`BODY_LAYOUTS`, already checked.

    Returns:
        The walked table.

    Raises:
        ObjectError: The chosen reader refused the body. Includes
            ``UnsupportedBodyLayoutError`` for a pair with no measured layout -
            which since CS-407 means a pair occurring in no real save, every
            real one having been measured.
    """
    # THE SEAM. Both scalars are threaded SEPARATELY into either reader:
    # header_version drives the body length prefix width and nothing else,
    # save_version drives the transform delta and nothing else. Deriving either
    # from the other is correct on every real file and wrong on SAVE_CROSS.
    reader = parse_body if body_layout == BODY_LAYOUT_LEVELLED else parse_object_headers
    return reader(
        payload,
        save_version=parsed.save_version,
        header_version=parsed.header_version,
        known_classes=None if mapping is None else mapping.schemas,
    )


def load_world_from_bytes(
    data: bytes,
    *,
    property_map: PropertyMap | None = None,
    body_layout: str = BODY_LAYOUT_LEVELLED,
) -> WorldModel:
    """Parse a whole save out of bytes already in memory.

    The composition the module docstring describes, minus the copy: the caller
    has the bytes, so there is nothing to copy and nothing to open.

    WHICH ``(header version, save version)`` PAIRS ARE READABLE IS NOT WRITTEN
    DOWN HERE. ``objects.MEASURED_BODY_LAYOUTS`` is that set and the only place
    the pairs are listed; a body whose pair is outside it is refused before the
    walk. THIS SENTENCE USED TO LIST THEM AND WENT STALE THE DAY THE SET GREW,
    which is what a second copy of a fact does. See the module docstring before
    reading a green result as "this reads saves" - what is measured is a
    SKELETON.

    Args:
        data: A whole save file's bytes.
        property_map: A parsed property mapping to check class paths against.
            None resolves the installed one through ``usmap.cached_usmap``,
            which returns None rather than raising when there is no install.
        body_layout: Which body reader to use, from :data:`BODY_LAYOUTS`.
            Defaults to :data:`BODY_LAYOUT_LEVELLED`, the layout a REAL save
            has. :data:`BODY_LAYOUT_FLAT` reads the synthetic corpus's single
            flat table and is never right for a real file.

    Returns:
        The world model.

    Raises:
        WorldLoadError: Any sibling refused the bytes - including a body whose
            version pair has no measured layout. The original is attached as
            the cause.
        ValueError: ``body_layout`` is not one of :data:`BODY_LAYOUTS`. Raised
            before anything is parsed, and NOT a ``WorldLoadError``.
    """
    _checked_layout(body_layout)

    try:
        parsed = parse_header(data)
    except HeaderError as exc:
        raise WorldLoadError(STAGE_HEADER, type(exc).__name__) from exc

    try:
        body = decompress_body(data, parsed.body_offset, header_version=parsed.header_version)
    except ChunkError as exc:
        raise WorldLoadError(STAGE_CHUNKS, type(exc).__name__) from exc

    mapping, warnings = _resolve_property_map(property_map)

    try:
        table = _walk_body(body.payload, parsed, mapping, body_layout)
    except ObjectError as exc:
        raise WorldLoadError(STAGE_OBJECTS, type(exc).__name__) from exc

    unlocks, unlock_warnings = _read_unlocks()
    nodes, node_warnings = _nodes_from(table)

    warnings.extend(unlock_warnings)
    if nodes:
        warnings.append(_warning(SOURCE_WORLD, WARN_NODE_SEMANTICS_UNAVAILABLE, len(nodes)))
    warnings.extend(node_warnings)

    return WorldModel(
        token=parsed.world_token,
        header=parsed,
        objects=table,
        unlocks=unlocks,
        nodes=nodes,
        warnings=(*_carried(parsed, body, mapping, table), *warnings),
    )


def _carried(
    parsed: SaveHeader,
    body: DecompressedBody,
    mapping: PropertyMap | None,
    table: ObjectTable,
) -> tuple[WorldWarning, ...]:
    """Normalise every sub-layer's advisories into the one stream.

    Args:
        parsed: The header, for its warnings.
        body: The decompressed body, for its warnings.
        mapping: The property map, for its warnings. May be None.
        table: The object table, for its warnings.

    Returns:
        Every carried warning, header first and in layer order.
    """
    out: list[WorldWarning] = [
        WorldWarning(source=SOURCE_HEADER, code=item.code, detail=item.detail)
        for item in parsed.warnings
    ]
    out.extend(
        WorldWarning(source=SOURCE_CHUNKS, code=item.code, detail=item.detail, count=item.count)
        for item in body.warnings
    )
    if mapping is not None:
        out.extend(
            WorldWarning(source=SOURCE_USMAP, code=item.code, detail=item.detail, count=item.count)
            for item in mapping.warnings
        )
    out.extend(
        WorldWarning(source=SOURCE_OBJECTS, code=item.code, detail=item.detail)
        for item in table.warnings
    )
    return tuple(out)


def load_world(
    path: Path | str,
    *,
    property_map: PropertyMap | None = None,
    body_layout: str = BODY_LAYOUT_LEVELLED,
) -> WorldModel:
    """Copy a save out of harm's way, then parse it.

    THE COPY IS NOT A COURTESY. The game holds handles during autosave, so
    parsing in place eventually meets a locked or half-written file.
    ``workdir.copy_for_read`` owns that copy and is the ONLY module in this
    package with a write - which is what makes "no other save module writes" a
    static assertion rather than a rule reviewers have to remember.

    This function opens for READ ONLY, in binary, and nothing else. The save
    directory is never opened for write for any reason (non-negotiable 1).

    Args:
        path: The save to load. May be the save in place; it is copied first.
        property_map: As :func:`load_world_from_bytes`.
        body_layout: As :func:`load_world_from_bytes`.

    Returns:
        The world model.

    Raises:
        WorldLoadError: The copy failed, or any sibling refused the bytes.
        ValueError: ``body_layout`` is not one of :data:`BODY_LAYOUTS`. Checked
            HERE as well as downstream, so a caller's typo is not paid for with
            a file copy first and is not masked by a copy that fails for its own
            unrelated reason.
    """
    _checked_layout(body_layout)

    try:
        copy = copy_for_read(Path(path))
    except WorkDirError as exc:
        raise WorldLoadError(STAGE_COPY, type(exc).__name__) from exc

    with copy.open("rb") as handle:
        data = handle.read()

    return load_world_from_bytes(data, property_map=property_map, body_layout=body_layout)
