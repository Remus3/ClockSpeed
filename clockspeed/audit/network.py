"""Which resource nodes the world is actually mining, joined by REFERENCE.

WHAT THIS MODULE OWNS
-----------------------
One pure function over one ``clockspeed.save.world.WorldModel``, returning a
frozen :class:`WorldNetwork`: one entry per published resource node saying
whether any record in the world names that node's instance. It is the
COMPUTATION half of "which node is a miner sitting on", and it lives here
because ``clockspeed/surface/`` never computes and ``audit/`` is the layer that
consumes a whole world model.

It reads no save, no docs file and no install. Its only input is the model.

A PROXIMITY FALLBACK IS FORBIDDEN, BY NAME
--------------------------------------------
Non-negotiable 7 forbids it: nearest-neighbour renders a wrong answer that reads
like a right one, and a miner standing between two nodes is the ordinary case
rather than the corner one. The join here is the TYPED reference population and
nothing else, and no coordinate is read at any point below. The arm that grades
it is built on a fixture where the two answers disagree on every node -
``tests/audit/test_network.py::test_a_bare_node_reads_unmined`` - beside a
discrimination control that computes the proximity answer in the test and
asserts the published one differs.

THE PROPERTY NAME IS NOT MEASURED, SO NO FILTER IS BUILT FROM ONE
--------------------------------------------------------------------
CS-1041's item line asserts as fact that a miner carries an ObjectProperty
naming its node actor, and names the property. ``docs/adr/0003-s4-node-actors-in-save.md``
measured ``mExtractResourceNode`` at ZERO occurrences in any save examined,
across three worlds and four game builds - so that name is not merely unverified
here, it is measured absent. A filter keyed on it would return an empty join on
every real world and report it as "no node is mined", which is the confident
wrong answer the rule exists to forbid.

So the join is NAME-AGNOSTIC: every top-level reference tag on every walked
record is a candidate, and what decides is whether its object path names a
published node. The per-tag denominators below are what let a later session
measure the name from real data without changing this file.

WHICH POPULATION A REFERENCE IS IN, DECIDED STRUCTURALLY
-----------------------------------------------------------
``clockspeed/save/objects.py`` ``ObjectReference`` states that nothing in that
population structurally separates a shipped asset path from a record instance
path - both are strings on the same attribute. ADR 0016 measured one population
that is ENTIRELY asset paths: not one unlock array element joined a record's
``instance_name``. So "it is a reference, therefore it names a record" is false,
and this module does not assume it.

:data:`INSTANCE_SEPARATOR` is the structural tell, and it is the save layer's
own: a shipped asset path never carries one and a record instance path always
does. The rule is RESTATED here rather than imported, on exactly the terms
``clockspeed/audit/placement.py`` ``class_name_of_path`` restates the class-name
rule - reaching into the save package for a one-character constant would be the
reach-past-your-neighbour the seam discipline forbids. It is pinned instead of
trusted by this arm:

``tests/audit/test_network.py::test_the_local_instance_separator_agrees_with_the_save_layers_own``

which is the only place in this package that imports the save layer's own
constant, and it exists so the two cannot drift apart silently.

WHAT THIS MODEL DOES NOT ANSWER, DECLARED RATHER THAN DROPPED
----------------------------------------------------------------
CS-1041's item LINE names FOUR questions and its filed acceptance grades TWO.
Two have no acceptance clause at all: **which belt feeds which machine**, and
**which connections share a power circuit**. Neither is computed here.

They are declared on the model as :attr:`WorldNetwork.belt_topology_available`
and :attr:`WorldNetwork.circuit_topology_available`, both False, and every
result carries :data:`WARN_NETWORK_TOPOLOGY_UNAVAILABLE`. That is not decoration:
a consumer holding a network model with no edges in it cannot otherwise tell a
world with no belts from a model that never looked, and shipping the silent
version is how an item that answered two of four questions would read as
answering all four. The two are re-filed rather than implemented, because an
implementation no clause grades is a feature nothing measures.

THE POSITION IS THE KEY, AND NO INDEX IS PUBLISHED
-----------------------------------------------------
:attr:`WorldNetwork.nodes` holds ONE ENTRY PER ``WorldModel.nodes`` MEMBER IN
THE SAME ORDER, which is the idiom ``clockspeed/audit/placement.py``
``WorldPlacement.node_placements`` already established. A consumer joins by
position against a population it already has, so no instance name, no record
index and no byte offset has to cross - the three things ``tests/audit/__init__.py``
names as never publishable from this layer.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, Final

from clockspeed.save.world import WorldWarning

if TYPE_CHECKING:  # pragma: no cover - import-time typing only
    from collections.abc import Mapping

    from clockspeed.save.world import WorldModel

__all__ = [
    "INSTANCE_SEPARATOR",
    "SOURCE_NETWORK",
    "WARN_NETWORK_NO_NODE_JOINED",
    "WARN_NETWORK_NO_NODE_POPULATION",
    "WARN_NETWORK_PAYLOAD_UNREAD",
    "WARN_NETWORK_TOPOLOGY_UNAVAILABLE",
    "NodeUse",
    "WorldNetwork",
    "names_a_record_instance",
    "network_of",
]

#: Which layer noticed a warning raised here, for ``WorldWarning.source``.
SOURCE_NETWORK: Final = "network"

#: The character an object path uses to separate its LEVEL from the object
#: inside it - ``Persistent_Level:PersistentLevel.Thing_C_0``. A shipped asset
#: path never carries one and a record instance path always does. Restated from
#: the save layer's own rule and PINNED by an arm rather than trusted - see the
#: module docstring for why it is restated and not imported.
INSTANCE_SEPARATOR: Final = ":"

#: This world published resource nodes and NOT ONE of them was named by any
#: reference. Flagged rather than reported as a measured zero: the property name
#: a miner uses is not measured in this tree (ADR 0003 measured the one the item
#: line names at zero occurrences), so an empty join is at least as likely to
#: mean "the reference tag is spelled some way nothing here has seen" as it is
#: to mean "nothing is being mined". Those two are different facts.
WARN_NETWORK_NO_NODE_JOINED: Final = "network-no-node-joined"

#: This model published no resource node at all, so mined-ness was computed over
#: an empty population. Separate from the code above because an empty answer
#: over nothing and an empty answer over something are different facts, and a
#: single code would make them indistinguishable.
WARN_NETWORK_NO_NODE_POPULATION: Final = "network-no-node-population"

#: This many walked records had a property payload that never read, so their
#: reference tags were never available to join with.
WARN_NETWORK_PAYLOAD_UNREAD: Final = "network-payload-unread"

#: Belt-to-machine feeding and power-circuit membership are NOT answered by this
#: model. Raised on EVERY result, unconditionally, on the terms
#: ``clockspeed/save/world.py`` raises its unlock-grammar code: a consumer that
#: reads an absent edge set as "this world has no belts" is wrong, and the flag
#: is the only thing standing between those two readings.
WARN_NETWORK_TOPOLOGY_UNAVAILABLE: Final = "network-topology-unavailable"

#: One fixed line per warning code raised here. Keyed rather than formatted, so
#: a detail can never be built from something read out of a save - the idiom
#: ``clockspeed/save/world.py`` established for the same reason.
_WARNING_DETAIL: Final[Mapping[str, str]] = MappingProxyType(
    {
        WARN_NETWORK_NO_NODE_JOINED: (
            "no published resource node was named by any record's reference, which is not"
            " the same fact as no node being mined; the property name a miner uses to name"
            " its node is not measured in this project, so an empty join may mean the tag"
            " was spelled some way this reader has never seen"
        ),
        WARN_NETWORK_NO_NODE_POPULATION: (
            "this model published no resource node at all, so mined-ness below was computed"
            " over an empty population; that is a fact about the model rather than about"
            " the world, and the save layer flags its own reasons separately"
        ),
        WARN_NETWORK_PAYLOAD_UNREAD: (
            "this many walked records had a property payload that never read, so whatever"
            " references they carry were never available to join with; the mined set below"
            " is short by whatever those records name"
        ),
        WARN_NETWORK_TOPOLOGY_UNAVAILABLE: (
            "which belt feeds which machine and which connections share a power circuit are"
            " not computed by this model; an absent edge set here is this reader not having"
            " looked and is never a world with no belts and no circuits in it"
        ),
    }
)


def names_a_record_instance(path: str) -> bool:
    """Whether one decoded object path names a RECORD rather than a shipped asset.

    THE STRUCTURAL TELL AND NOTHING ELSE. This does not ask whether the record
    exists - :func:`network_of` asks that separately, against the published node
    population - because the two questions fail differently. A path that is not
    a record path at all must never be looked up, and a record path that looks
    up to nothing is a fact worth counting rather than a malformed input.

    Args:
        path: The object path half of a decoded reference.

    Returns:
        True when the path carries :data:`INSTANCE_SEPARATOR`.
    """
    return INSTANCE_SEPARATOR in path


@dataclass(frozen=True)
class NodeUse:
    """One published resource node, and whether anything names it.

    NO INSTANCE NAME, NO INDEX, NO OFFSET, NO PATH - the position of this entry
    in :attr:`WorldNetwork.nodes` is the join key, and it is the same position
    the entry holds in ``WorldModel.nodes`` and in
    ``clockspeed/audit/placement.py`` ``WorldPlacement.node_placements``. The
    class name is publisher content, on the terms ``Placement`` already states.

    Attributes:
        class_name: The node's actor class, carried verbatim from
            ``clockspeed.save.world.ResourceNode.class_name``, which is one of
            that module's measured node classes.
        mined: Whether at least one walked record carried a top-level reference
            whose object path is this node's instance. FALSE IS NOT "IDLE" AND
            IS NOT "UNCLAIMED" - it is "nothing this reader could see named it",
            and :data:`WARN_NETWORK_NO_NODE_JOINED` is what says so when the
            whole population reads false.
    """

    class_name: str
    mined: bool


@dataclass(frozen=True, repr=False)
class WorldNetwork:
    """Which nodes are mined, the denominators that bound that, and what is absent.

    ``repr`` renders counts and flags only, for the reason
    ``clockspeed/audit/inventory.py`` ``WorldInventory`` gives: a test runner
    reprs a value before a human chooses what to print, and a repr that reads a
    field off every member raises on a model holding a planted value.

    Attributes:
        nodes: One entry per ``WorldModel.nodes`` member, IN THAT ORDER. The
            order is the contract - see :class:`NodeUse`.
        nodes_considered: How many nodes that population held. Equal to
            ``len(nodes)`` by construction, and worth asking rather than
            deriving, for the reason ``WorldProperties.total`` gives.
        records_considered: How many walked records had an entry in
            ``WorldModel.properties``. Total over the record table by
            construction.
        unread_payload_count: How many of those records' payloads never read,
            carried verbatim from ``WorldProperties.unread_payload_count`` - the
            honest denominator its own docstring names.
        reference_tags_considered: How many top-level reference tags were
            examined, across every record. The outer denominator of the join: a
            zero here and a zero mined count mean the join had no terms, which
            is a different fact from a join that had terms and matched none.
        instance_references_considered: How many of those tags carried a path
            that names a RECORD rather than a shipped asset, by
            :func:`names_a_record_instance`. The inner denominator, and the one
            that separates "no reference looked like a record path" from "they
            did and named no node".
        belt_topology_available: ALWAYS FALSE, and a FIELD rather than an
            omission - see the module docstring. Which belt feeds which machine
            is one of the two questions CS-1041's line names and its acceptance
            does not grade.
        circuit_topology_available: ALWAYS FALSE, on identical terms. Which
            connections share a power circuit is the other one.
        warnings: Everything flagged, in the ``WorldWarning`` idiom.
    """

    nodes: tuple[NodeUse, ...]
    nodes_considered: int
    records_considered: int
    unread_payload_count: int
    reference_tags_considered: int
    instance_references_considered: int
    belt_topology_available: bool
    circuit_topology_available: bool
    warnings: tuple[WorldWarning, ...]

    @property
    def mined_count(self) -> int:
        """How many published nodes read mined.

        Returns:
            The count.
        """
        return sum(1 for use in self.nodes if use.mined)

    def __repr__(self) -> str:
        """Render counts and flags, and none that a member could make raise.

        ``mined_count`` IS DELIBERATELY ABSENT, on the terms
        ``clockspeed/audit/inventory.py`` ``WorldInventory.__repr__`` states: it
        reads a field off every member, so a repr rendering it raises on a model
        holding a planted value - which is exactly the state a forced arm puts
        this class in.

        Returns:
            The safe rendering.
        """
        return (
            f"{type(self).__name__}(nodes={len(self.nodes)}, "
            f"records_considered={self.records_considered}, "
            f"unread_payload_count={self.unread_payload_count}, "
            f"reference_tags_considered={self.reference_tags_considered}, "
            f"instance_references_considered={self.instance_references_considered}, "
            f"belt_topology_available={self.belt_topology_available}, "
            f"circuit_topology_available={self.circuit_topology_available}, "
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
        source=SOURCE_NETWORK,
        code=code,
        detail=_WARNING_DETAIL[code],
        count=count,
    )


def network_of(model: WorldModel) -> WorldNetwork:
    """Join every walked record's references against the published node population.

    NO COORDINATE IS READ ANYWHERE IN THIS FUNCTION, and that is the whole
    design rather than an implementation detail - see the module docstring.

    Args:
        model: The world model.

    Returns:
        One :class:`NodeUse` per published node, in that population's order,
        with the denominators that bound the answer and the flags naming what
        was not computed.
    """
    slots: dict[str, list[int]] = {}
    for index, node in enumerate(model.nodes):
        slots.setdefault(node.instance_name, []).append(index)

    mined = [False] * len(model.nodes)
    reference_tags = 0
    instance_references = 0
    for entry in model.properties.by_record_index.values():
        for reference in entry.references:
            reference_tags += 1
            if not names_a_record_instance(reference.object_path):
                continue
            instance_references += 1
            for index in slots.get(reference.object_path, ()):
                mined[index] = True

    nodes = tuple(
        NodeUse(class_name=node.class_name, mined=mined[index])
        for index, node in enumerate(model.nodes)
    )

    warnings = [_warning(WARN_NETWORK_TOPOLOGY_UNAVAILABLE)]
    if not nodes:
        warnings.append(_warning(WARN_NETWORK_NO_NODE_POPULATION))
    elif not any(mined):
        warnings.append(_warning(WARN_NETWORK_NO_NODE_JOINED))
    unread = model.properties.unread_payload_count
    if unread:
        warnings.append(_warning(WARN_NETWORK_PAYLOAD_UNREAD, unread))

    return WorldNetwork(
        nodes=nodes,
        nodes_considered=len(nodes),
        records_considered=model.properties.total,
        unread_payload_count=unread,
        reference_tags_considered=reference_tags,
        instance_references_considered=instance_references,
        belt_topology_available=False,
        circuit_topology_available=False,
        warnings=tuple(warnings),
    )
