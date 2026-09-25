"""``/api/map`` - where everything in the world is, what it holds, and what it pulls.

Owns (BOOTSTRAP.md section 7.1): the JSON rendering of one
``clockspeed.audit.placement.WorldPlacement`` and one
``clockspeed.audit.inventory.WorldInventory``, joined against the normalized
registry for display names, extraction rates and the closed item-key
vocabulary, and nothing else. It computes
nothing, it opens nothing, and it obtains both inputs through the providers the
server binds into it rather than by reading a save or the install.

THIS IS A PII-CRITICAL ENDPOINT FOR THE SAME REASON ``/api/world`` IS. On this
machine the server auto-detects and loads the operator's own save at startup, so
every value named below is derived from a personal-data-bearing artifact
(non-negotiables 11 and 12) rather than from a hypothetical one.

THE BODY IS BUILT BY NAMING EVERY FIELD, ONE AT A TIME, AND THAT IS THE WHOLE
DESIGN. There is no ``dataclasses.asdict``, no ``astuple``, no ``vars()``, no
``__dict__`` read and no ``dataclasses.fields`` walk anywhere in this module, and
``tests/surface/test_map.py`` asserts that on the shipped AST - the twin of the
arm ``tests/surface/test_world.py`` applies to ``/api/world``. Naming fields
means adding a field is a decision somebody makes; walking them means it is a
decision nobody makes.

WHAT IS DELIBERATELY WITHHELD, AND WHY EACH ONE IS NOT AN OVERSIGHT. The list is
``clockspeed/surface/api/world.py``'s, unchanged, because CS-977 loosened exactly
one thing and it was not this: the raw world token, the header's ``map_name``,
both time fields, every instance name, every record index and byte offset, and
any filesystem path. ``masked_token`` is the only thing about the world's
identity that crosses this wire, and it answers the only question a reader has -
whether two responses are about the SAME world.

WHAT CS-977 DID LOOSEN, AND ON WHAT AUTHORITY. A node's COORDINATES and a built
actor's CLASS NAME now ship. ``world.py`` withheld them for two reasons braided
together, and they separate cleanly: an instance name is a census of the
operator's own factory, while a class name comes from the asset registry and
``clockspeed/save/usmap.py`` records that as publisher content; and a bare JSON
number is the IEEE double non-negotiable 6 keeps out of the answer path, which is
an objection to the WIRE TYPE rather than to the value. So the class names ship
and every coordinate ships as the exact decimal STRING
``clockspeed/audit/placement.py`` renders, never as a JSON number.

WHAT CS-1013 ADDED, ON THE SAME AUTHORITY AND NOT A BYTE MORE. EVERY placement's
ROTATION and SCALE now ship beside its coordinates - a node's exactly as much as
a building's. ``objects.Transform`` parsed all three blocks all along and two
seams below this one dropped two of them, so nothing on this map could be
oriented over data that had already been decoded. They are stored floats exactly
as a coordinate is, so they ship exactly as a coordinate does - as exact decimal
strings, never as JSON numbers - and they name nothing the operator authored, so
the withheld list above is unchanged by one entry. They ship as ARRAYS in file
order rather than as named components; :data:`PLACEMENT_KEYS` says why, and
:func:`_placements` says when each is null and why a null beats an invented
identity.

``node_orientation_available`` ships beside ``node_semantics_available`` and is
the exact counterpart of it: a declared capability, so a consumer branches on
the field rather than sniffing a row for a null and guessing what the null
meant. It is True and ``node_semantics_available`` is False, which is the whole
distinction this endpoint exists to keep straight - a node's GEOMETRY is
complete in the file, and its resource type and purity are not in the file at
all.

NODE SEMANTICS ARE UNAVAILABLE AND THE BODY SAYS SO TWICE.
``docs/adr/0003-s4-node-actors-in-save.md`` measured ``mPurity``,
``mResourceNodeType`` and ``mResourceClass`` at ZERO occurrences across three
worlds and four game builds, so this endpoint can say where every node is and
cannot say what any of them holds. It ships as a FIELD and as a warning: a
consumer reading one and not the other must still learn it.

THROUGHPUT SEPARATES WHAT WAS MEASURED FROM WHAT WAS ASSUMED, AND THAT IS THE
POINT OF THE ROW'S SHAPE. ``clockspeed/data/registry.py`` measured
``mItemsPerCycle`` and ``mExtractCycleTime`` exactly, so an items-per-minute
figure IS derivable and is served as :data:`THROUGHPUT_KEYS`'
``per_minute_normal``. It also measured that NO purity multiplier is exported by
the shipped document, and ADR 0003 measured that a node's purity is not in a save
either - so the three multipliers in ``purity_scaling`` are an ASSUMPTION this
project has not measured from any file on this machine.
``purity_scaling_measured`` being ``false`` beside them is what says so on the
wire rather than in a comment nobody reads, and ``purity_known`` stays a
PER-ROW field so the day a purity source exists one row can go true.

THE FIGURE IS NOT CONVERTED OUT OF THE DOCUMENT'S OWN UNITS, AND THE ALTERNATIVE
WAS NOT AVAILABLE. ``mItemsPerCycle`` is 1 on a solid miner and 2000 on a fluid
extractor, and the second number is LITRES;
``clockspeed/data/registry.py``'s ``Extractor`` states why it cannot divide by
``LITRES_PER_CUBIC_METRE`` itself - the resource is not known there, because
``allowed_forms`` is a SET and which resource an extractor actually pulls is a
property of the node it sits on, which ADR 0003 measured as absent from a save.
That argument binds this layer identically: the form cannot be resolved HERE
either, so there is nothing to divide by. The figure therefore ships in the
document's own units, with :data:`RATE_UNIT` naming them and the document's own
form tokens served verbatim beside it. Publishing 2 items per minute for a pump
the document says moves 2000 litres would be a wrong number wearing the right
type.

A MISSING RATE IS NULL AND IS NEVER A ZERO. Both operands are None on measured
entries, and ``extract_cycle_time`` can be a DECLARED zero, which
``clockspeed.solve.exact.per_minute`` calls undefined rather than infinite. Every
one of those three cases serves ``null`` and raises
:data:`WARN_EXTRACTION_RATE_UNAVAILABLE`. A null is honest; a zero is a lie a
power plan cannot detect.

AN AUDIT WARNING KEEPS ITS OWN SOURCE. ``clockspeed/audit/`` does not know an
endpoint exists, so its advisories arrive under the sources ``placement`` and
``inventory`` and are served with those verbatim. Remapping them to ``map`` would
destroy the one field that says which layer flagged the thing. Only a warning
THIS module raises carries :data:`SOURCE_MAP`, and the four it can raise are all
about the registry join, which is the only thing this module does that the layers
below cannot see.

AN ITEM KEY IS SERVED ONLY WHEN THE REGISTRY NAMES IT (CS-1189). An item key is
whatever string a save's ``ItemClass`` carried, reduced by
``clockspeed.audit.placement.class_name_of_path`` - which returns a DOTLESS
string unchanged, so a key shaped like a home path or a platform account id
survives as a "class name". :func:`closed_key` is a membership lookup against
the registry's closed vocabulary, the same kind of join as
:func:`display_name_of`: a key the registry names ships, and a key it does not
name is withheld with its row and counted under
:data:`WARN_ITEM_KEY_UNKNOWN` - flagged and skipped, the key text never echoed
(non-negotiable 7). With NO registry there is no vocabulary at all, so every key
is withheld and :data:`WARN_REGISTRY_UNAVAILABLE` says why: failing closed is
the only direction that cannot publish an account directory. A placement's
``class_name`` needs no second check here because ``clockspeed/audit/`` admits
one only through a closed allowlist of its own - measured, not assumed, in
``tests/surface/test_map_vocabulary.py``. ``MachineState.class_name`` is served
by no route, and the same file FAILS CLOSED the day any surface module reaches
``clockspeed.audit.machines`` by any import form: the first route to need it
adds one sanctioned accessor that passes every class name through
:func:`closed_key`, and admits exactly that accessor there.

NO WORLD IS 503, NEVER 501, for the reason ``clockspeed/surface/api/world.py``
states at length: the save layer is written and works, and what is absent is its
INPUT. A 501 would tell the operator the save reader has not been built. A
missing REGISTRY is not a refusal at all - the placement, the counts and the
bounds are all still true without one, so the body answers 200, and the
``registry-unavailable`` warning says why the throughput section is empty and
why every item total was withheld: with no closed vocabulary no item key can be
admitted, so the inventory section is empty by refusal, not by measurement.
"""

# SEAM DISCIPLINE (BOOTSTRAP.md section 6).
# Each layer consumes only the layer below it through a stated model.
# solve/ never reads a save. advisor/ never reads the raw docs file.
# surface/ never computes. A layer that reaches past its neighbor is a
# design bug.
#
# BOTH INPUTS ARRIVE THROUGH PROVIDERS, NEVER THROUGH A FILE. The package
# docstring forbids this package from opening anything at all, so neither
# `load_world` nor `build_registry` is called here and neither is imported.
#
# THE COMPUTATION IS `clockspeed.audit`'s AND THE ARITHMETIC IS
# `clockspeed.solve`'s. `placement_of` and `inventory_of` reduce one world model
# to the two frozen models this endpoint serializes, and
# `clockspeed.solve.exact.per_minute` turns a per-cycle amount into a per-minute
# rate - exactly, and with the zero-duration rule already decided there. Both
# packages sit BELOW this one (`clockspeed/surface/__init__.py` enumerates
# advisor, audit, progress and solve), so naming them is consuming a neighbour
# rather than reaching past one, and this module holds no arithmetic operator of
# its own. `tests/surface/test_map.py` asserts that on the shipped AST.
#
# The ONE runtime name taken from the save layer is `masked_token`, on the terms
# `clockspeed/surface/api/world.py` already argued: the mask is the redaction
# control `clockspeed/save/header.py` owns, and re-deriving a digest here would
# be the same fact written in two places.

from __future__ import annotations

from fractions import Fraction
from types import MappingProxyType
from typing import TYPE_CHECKING, Final

from clockspeed.audit import inventory as inventory_model
from clockspeed.audit import placement as placement_model
from clockspeed.save.header import masked_token
from clockspeed.solve import exact
from clockspeed.surface.api import contract

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from clockspeed.data.registry import Extractor, Registry
    from clockspeed.save.world import WorldModel, WorldWarning

__all__ = [
    "BOUNDS_KEYS",
    "DATA_KEYS",
    "ENDPOINT",
    "INVENTORY_KEYS",
    "METHOD_GET",
    "PLACEMENT_KEYS",
    "PURITIES",
    "PURITY_SCALING",
    "PURITY_SCALING_MEASURED",
    "RATE_UNIT",
    "SCHEMA",
    "SOURCE_MAP",
    "THROUGHPUT_KEYS",
    "WARNING_KEYS",
    "WARNING_SOURCES",
    "WARN_EXTRACTION_RATE_UNAVAILABLE",
    "WARN_ITEM_KEY_UNKNOWN",
    "WARN_NO_MODELLED_EXTRACTOR_BUILT",
    "WARN_REGISTRY_UNAVAILABLE",
    "closed_key",
    "display_name_of",
    "make_handler",
    "routes",
]

#: The route template this endpoint answers. A literal authored here, never a
#: path read off a request line.
ENDPOINT: Final = "/api/map"

#: The verb this route answers. Spelled HERE rather than in
#: ``clockspeed/surface/api/routes.py`` so a module that owns an endpoint owns
#: its method too, as ``clockspeed/surface/api/registry.py`` and
#: ``clockspeed/surface/api/solve.py`` already do.
METHOD_GET: Final = "GET"

#: The body's own version, so a panel can refuse a shape it does not know rather
#: than mis-render one. An INTEGER, because a count is exact.
SCHEMA: Final = 1

#: Which layer noticed a warning this module raised. The four codes below are
#: the only ones that carry it - see the module docstring on why an audit warning
#: keeps ``placement`` or ``inventory`` instead.
SOURCE_MAP: Final = "map"

#: Every source a warning in this body may carry. Published so a test can bind
#: the served set to it, and deliberately a SUPERSET of what this module raises:
#: the other two members are its neighbours' own, served verbatim.
WARNING_SOURCES: Final = (
    SOURCE_MAP,
    placement_model.SOURCE_PLACEMENT,
    inventory_model.SOURCE_INVENTORY,
)

#: There is no registry on this machine, so no rate and no display name could be
#: joined onto anything, and no item key can be shown to be publisher content -
#: so every item total is withheld (see :func:`closed_key`). The placement, the
#: counts and the bounds are all still true, which is why this is a warning
#: inside a 200 rather than a refusal.
WARN_REGISTRY_UNAVAILABLE: Final = "registry-unavailable"

#: A rate could not be derived. Raised when the registry is absent, and raised
#: with a count when a served row's operands were absent or its declared cycle
#: time was zero. An EMPTY throughput array with no warning would read as "you
#: have no extractors", which is a different fact and usually a false one.
WARN_EXTRACTION_RATE_UNAVAILABLE: Final = "extraction-rate-unavailable"

#: Nothing built is an extractor this build models. Distinct from the code above
#: because the remedy is different: this one is answered by building an extractor
#: or by modelling one, not by installing the game.
WARN_NO_MODELLED_EXTRACTOR_BUILT: Final = "no-modelled-extractor-built"

#: An item total's key is not in the registry's closed vocabulary, so the row
#: was withheld rather than served. Carries the count of withheld totals and
#: NEVER the key: an unknown key is exactly the string that may be a home path
#: or an account directory, so naming it here would be the leak this code flags.
WARN_ITEM_KEY_UNKNOWN: Final = "item-key-unknown"

#: The purity vocabulary, in ascending yield order so a consumer can render the
#: three in a fixed sequence without sorting strings.
PURITY_IMPURE: Final = "impure"
PURITY_NORMAL: Final = "normal"
PURITY_PURE: Final = "pure"
PURITIES: Final = (PURITY_IMPURE, PURITY_NORMAL, PURITY_PURE)

#: The multipliers a served rate would be scaled by, as exact ratios. HELD AS
#: FRACTIONS AND RENDERED, rather than authored as strings, so the values are
#: provably exact rather than merely spelled like it.
#:
#: NOT MEASURED ON THIS MACHINE. See the module docstring: neither the shipped
#: document nor a save carries a purity multiplier, so these three are this
#: project's stated assumption and :data:`PURITY_SCALING_MEASURED` is what says
#: so on the wire.
PURITY_SCALING: Final[Mapping[str, Fraction]] = MappingProxyType(
    {
        PURITY_IMPURE: Fraction(1, 2),
        PURITY_NORMAL: Fraction(1),
        PURITY_PURE: Fraction(2),
    }
)

#: Whether :data:`PURITY_SCALING` was measured from a file on this machine. It
#: was not. A constant rather than a literal in the builder, so the day a
#: measurement exists this flips in one place.
PURITY_SCALING_MEASURED: Final = False

#: What a served rate is expressed in. The document's own units: a plain count
#: for a solid form and LITRES for a fluid one, and the row's ``allowed_forms``
#: is what says which. See the module docstring for why this layer converts
#: neither.
RATE_UNIT: Final = "items-or-litres-per-minute"

#: Exactly the top-level keys a success body carries. Published so a test can
#: bind the shape to the builder and so neither can drift from the other.
DATA_KEYS: Final = (
    "schema",
    "masked_token",
    "coordinate_units",
    "node_semantics_available",
    "node_orientation_available",
    "bounds",
    "nodes",
    "node_counts",
    "built",
    "built_counts",
    "inventory",
    "throughput",
    "warnings",
)

#: The bounding box's keys. SIX FLAT AXES rather than three nested objects,
#: because a consumer drawing a viewport reads a minimum and a maximum per axis
#: and an extra level of nesting buys it nothing. Absent entirely - the whole
#: value is ``null`` - when no placement survived; see :func:`_bounds`.
BOUNDS_KEYS: Final = ("min_x", "max_x", "min_y", "max_y", "min_z", "max_z")

#: One placed thing's keys, and the complete list. NO INSTANCE NAME, NO INDEX,
#: NO OFFSET, NO PATH - ``clockspeed/audit/placement.py``'s ``Placement`` carries
#: none of those to begin with, and this tuple is why it never grows one.
#:
#: ``rotation`` and ``scale`` are ARRAYS of exact decimal strings, or ``null``.
#: Arrays rather than named-component objects because ``objects.Transform`` says
#: the quaternion is "in file order" and names no component; inventing ``i``,
#: ``j``, ``k`` and ``w`` here would publish a claim about the format this
#: project has not measured. See :func:`_placements` for when each is null.
PLACEMENT_KEYS: Final = ("class_name", "x", "y", "z", "rotation", "scale")

#: One item total's keys. A row is served only when the registry names its
#: ``item_key`` - see :func:`closed_key` - so ``display_name`` is the verbatim
#: descriptor name, which may be the empty string the document carries.
INVENTORY_KEYS: Final = ("item_key", "display_name", "count")

#: One throughput row's keys. ``per_minute_normal`` is exact and derived;
#: ``purity_scaling`` and ``purity_scaling_measured`` are the assumption and the
#: disclosure that it is one. See the module docstring for both.
THROUGHPUT_KEYS: Final = (
    "class_name",
    "display_name",
    "built",
    "per_minute_normal",
    "per_minute_unit",
    "allowed_forms",
    "purity_scaling",
    "purity_scaling_measured",
    "purity_known",
)

#: One carried advisory's keys, the shape ``/api/world`` publishes narrowed to
#: the three the frozen CS-977 contract froze. ``source`` is the layer that
#: flagged it, ``code`` is that layer's own vocabulary, and ``count`` is how many
#: occurrences the row aggregates.
WARNING_KEYS: Final = ("source", "code", "count")


def _exact_string(value: Fraction) -> str:
    """Render an exact ratio as the string the wire carries.

    ``Fraction.__str__`` writes a whole number as itself and everything else as
    ``a/b``, so the rendering is EXACT for every input and is never a decimal
    approximation. A float would be the IEEE double non-negotiable 6 keeps out of
    the answer path, and ``contract.encode`` refuses one outright.

    THIS TRANSCRIBES AND DOES NOT COMPUTE. Nothing here divides, rounds or
    reduces - ``Fraction`` normalises on construction, so the value arrives in
    lowest terms already.

    Args:
        value: The exact ratio.

    Returns:
        The rendering.
    """
    return str(value)


def _rate_of(extractor: Extractor) -> str | None:
    """The normal-purity items-per-minute figure, or None when it is unmeasured.

    THE ARITHMETIC IS ``clockspeed.solve.exact.per_minute``'s, WHICH IS A LAYER
    BELOW THIS ONE. That function also owns the zero-duration rule - a cycle of
    no duration has no rate, which is not the same fact as a very large one - so
    the refusal is transcribed here rather than re-decided, on the idiom
    ``contract.SOLVER_REFUSALS`` established.

    Args:
        extractor: The registry's entry for a built class.

    Returns:
        The rate as an exact string, or None when either operand is absent or
        the declared cycle time is zero. NEVER a zero standing in for an
        absence: ``clockspeed/data/registry.py`` records that a defaulted number
        is a confident rate the game never stated.
    """
    amount = extractor.items_per_cycle
    duration = extractor.extract_cycle_time
    if amount is None or duration is None:
        return None
    try:
        return _exact_string(exact.per_minute(amount, duration))
    except exact.UndefinedRateError:
        return None


def _scaling() -> dict[str, str]:
    """Render the purity multipliers, by naming each purity.

    Returns:
        The three factors as exact strings, keyed by :data:`PURITIES`.
    """
    return {purity: _exact_string(PURITY_SCALING[purity]) for purity in PURITIES}


def closed_key(vocabulary: Mapping[str, object] | None, key: str) -> str | None:
    """Admit a save-derived key only when a closed vocabulary names it.

    A MEMBERSHIP LOOKUP, THE SAME KIND OF JOIN AS :func:`display_name_of`, and
    never a computation: nothing is reduced, trimmed, matched by prefix or
    synthesised. A save's string is whatever the file carried, and on this
    machine that file is a personal-data-bearing artifact; only a key the
    registry itself publishes is known to be publisher content.

    Args:
        vocabulary: The registry's closed mapping for this kind of key - its
            ``items`` for an item key - or None when there is no registry.
        key: The key as the audit layer reduced it.

    Returns:
        The key when the vocabulary holds it, else None. None ALSO when there is
        no vocabulary at all: with nothing to check against, nothing is admitted.
    """
    if vocabulary is None or key not in vocabulary:
        return None
    return key


def display_name_of(registry: Registry | None, item_key: str) -> str | None:
    """Look one item's display name up in the registry.

    A JOIN, AND IT IS A LOOKUP RATHER THAN A COMPUTATION - the naming half of
    the two item joins this module performs, beside :func:`closed_key`. A name
    synthesised from the key would invent a fact the registry does not hold,
    which is the failure ``clockspeed/data/registry.py`` documents for a
    defaulted rate wearing a different hat.

    Args:
        registry: The normalized registry, or None when this machine has no
            install.
        item_key: The item's ClassName, as ``clockspeed/audit/inventory.py``
            reduced it.

    Returns:
        The verbatim display name, or None when there is no registry or no
        descriptor for that key. The empty string IS returned when the document
        carries an empty name, because that is the document's own fact and is
        different from having no descriptor at all.
    """
    if registry is None:
        return None
    item = registry.items.get(item_key)
    if item is None:
        return None
    return item.display_name


def _bounds(bounds: placement_model.WorldBounds | None) -> dict[str, str] | None:
    """Flatten the bounding box into six axes, or serve null when there is none.

    NULL RATHER THAN SIX SYNTHESISED KEYS. ``clockspeed/audit/placement.py``
    returns no box for a world where no placement survived and raises
    ``placement-bounds-undefined`` to say why; six nulls here would read as a box
    that was computed and came back empty, which is a different claim from
    "there was nothing to bound", and a zero box would be worse still.

    Args:
        bounds: The box, or None.

    Returns:
        The six axes keyed by :data:`BOUNDS_KEYS`, or None.
    """
    if bounds is None:
        return None
    return {
        "min_x": bounds.x.min_value,
        "max_x": bounds.x.max_value,
        "min_y": bounds.y.min_value,
        "max_y": bounds.y.max_value,
        "min_z": bounds.z.min_value,
        "max_z": bounds.z.max_value,
    }


def _placements(placements: Sequence[placement_model.Placement]) -> list[dict[str, object]]:
    """Render every placement by naming its six fields.

    THE ORIENTATION IS TRANSCRIBED AND NOT INTERPRETED. ``list()`` widens the
    model's tuple into the JSON array the encoder writes, and nothing here
    normalises a quaternion, converts one to Euler angles or multiplies a scale
    by anything - ``surface/`` never computes, and every one of those is a
    computation. A component arrives as the exact decimal string
    ``clockspeed/audit/placement.py`` rendered and leaves as that same string.

    ``null`` RATHER THAN AN IDENTITY when the model carries no block, and there
    is now exactly ONE reason it can be null: the stored block held a non-finite
    component, so the audit layer withheld it whole and kept the placement. That
    is flagged in ``warnings`` as ``placement-orientation-non-finite`` rather
    than guessed at here, and it applies to a node and a building alike.
    SERVING AN IDENTITY QUATERNION INSTEAD WOULD BE A CLAIM - that the thing is
    unrotated - and this layer has no basis for it; a consumer cannot tell an
    invented identity from a measured one, which is the silently-wrong half of
    non-negotiable 7.

    Args:
        placements: The placements, in the order the model carries them.

    Returns:
        One mapping per placement, keyed by :data:`PLACEMENT_KEYS`.
    """
    return [
        {
            "class_name": placed.class_name,
            "x": placed.x,
            "y": placed.y,
            "z": placed.z,
            "rotation": None if placed.rotation is None else list(placed.rotation),
            "scale": None if placed.scale is None else list(placed.scale),
        }
        for placed in placements
    ]


def _counts(counts: Mapping[str, int]) -> dict[str, int]:
    """Copy a per-class tally into a plain mapping the encoder can read.

    A PLAIN DICT RATHER THAN THE MODEL'S OWN MAPPING, and that is a wire
    requirement rather than a preference: ``clockspeed/audit/placement.py``
    publishes a ``MappingProxyType`` so nothing can mutate a model, and
    ``json.dumps`` refuses a mappingproxy outright - the reason
    ``contract.Response.payload`` is a plain mapping too.

    Args:
        counts: The tally, keyed by class name.

    Returns:
        The same tally, in a plain dict, iterating in the order it arrived.
    """
    return dict(counts)


def _inventory(
    items: Sequence[inventory_model.ItemTotal], registry: Registry | None
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    """Render every item total the registry names, with its display name joined on.

    THE KEY SERVED IS THE ONE :func:`closed_key` ADMITTED, never the model's own
    field read a second time. A total whose key the registry does not name is
    withheld whole - its count under an unnamed row would be a figure about
    nothing a reader can identify - and counted into one
    :data:`WARN_ITEM_KEY_UNKNOWN` advisory that carries no key text.

    NO REGISTRY WITHHOLDS EVERY TOTAL AND RAISES NOTHING HERE, because
    :func:`_throughput` already raises :data:`WARN_REGISTRY_UNAVAILABLE` for
    that world and a second copy would count one absence twice.

    Args:
        items: The totals, sorted by item key by the model that built them.
        registry: The normalized registry, or None.

    Returns:
        One mapping per admitted total, keyed by :data:`INVENTORY_KEYS`, and
        the advisories this module raises about the withheld ones.
    """
    if registry is None:
        return [], []
    vetted = [(closed_key(registry.items, total.item_key), total.count) for total in items]
    served: list[dict[str, object]] = [
        {
            "item_key": key,
            "display_name": display_name_of(registry, key),
            "count": count,
        }
        for key, count in vetted
        if key is not None
    ]
    withheld = [count for key, count in vetted if key is None]
    if withheld:
        return served, [_warning(WARN_ITEM_KEY_UNKNOWN, len(withheld))]
    return served, []


def _row(class_name: str, built: int, extractor: Extractor) -> dict[str, object]:
    """Render one throughput row by naming every field it carries.

    Args:
        class_name: The built class, which is also the registry key.
        built: How many of them stand in this world. An exact integer.
        extractor: The registry's entry for that class.

    Returns:
        The row, keyed by :data:`THROUGHPUT_KEYS`.
    """
    return {
        "class_name": class_name,
        "display_name": extractor.display_name,
        "built": built,
        "per_minute_normal": _rate_of(extractor),
        "per_minute_unit": RATE_UNIT,
        "allowed_forms": sorted(extractor.allowed_forms),
        "purity_scaling": _scaling(),
        "purity_scaling_measured": PURITY_SCALING_MEASURED,
        "purity_known": False,
    }


def _warning(code: str, count: int = 1) -> dict[str, object]:
    """Build one advisory this MODULE raises, under its own source.

    Args:
        code: One of this module's ``WARN_*`` constants.
        count: How many occurrences it aggregates.

    Returns:
        The advisory, keyed by :data:`WARNING_KEYS`.
    """
    return {"source": SOURCE_MAP, "code": code, "count": count}


def _carried(warnings: Sequence[WorldWarning]) -> list[dict[str, object]]:
    """Render every advisory a layer below raised, keeping its own source.

    THE SOURCE IS SERVED VERBATIM AND IS NEVER REMAPPED. ``clockspeed/audit/``
    does not know an endpoint exists, so its warnings say ``placement`` and
    ``inventory``; rewriting them to ``map`` would destroy the one field that
    says which layer flagged the thing.

    ``detail`` and ``subject`` are not served, which the frozen CS-977 contract
    decided: this body's warning shape is the three keys in
    :data:`WARNING_KEYS`. Both remain reachable through ``/api/world`` for a
    consumer that wants the sentence.

    Args:
        warnings: The advisories, in the order the model produced them.

    Returns:
        One mapping per advisory, keyed by :data:`WARNING_KEYS`.
    """
    return [
        {
            "source": warning.source,
            "code": warning.code,
            "count": warning.count,
        }
        for warning in warnings
    ]


def _throughput(
    placed: placement_model.WorldPlacement, registry: Registry | None
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    """Render one row per built class the registry models as an extractor.

    THREE OUTCOMES, EACH NAMED RATHER THAN COLLAPSED INTO AN EMPTY ARRAY. No
    registry, no modelled extractor among what is built, and a modelled extractor
    whose rate is unmeasured are three different facts with three different
    remedies, and an empty array alone would render all three as "you have no
    extractors".

    Args:
        placed: The placement model, whose ``built_counts`` is the population.
        registry: The normalized registry, or None.

    Returns:
        The rows, and the advisories this module raises about them.
    """
    if registry is None:
        return [], [
            _warning(WARN_REGISTRY_UNAVAILABLE),
            _warning(WARN_EXTRACTION_RATE_UNAVAILABLE),
        ]

    extractors = registry.extractors
    served = [
        _row(class_name, built, extractors[class_name])
        for class_name, built in placed.built_counts.items()
        if class_name in extractors
    ]
    if not served:
        return served, [_warning(WARN_NO_MODELLED_EXTRACTOR_BUILT)]

    unrated = [row for row in served if row["per_minute_normal"] is None]
    if unrated:
        return served, [_warning(WARN_EXTRACTION_RATE_UNAVAILABLE, len(unrated))]
    return served, []


def _body(model: WorldModel, registry: Registry | None) -> dict[str, object]:
    """Build the success body by naming every field it carries.

    THE TWO MODELS ARE COMPUTED BY ``clockspeed.audit``, NOT HERE. This function
    calls ``placement_of`` and ``inventory_of`` and then transcribes their
    fields; every geometric decision - the allowlist, the non-finite refusal, the
    decimal rendering, the bounding box - was made one layer down, where
    ``tests/audit/`` grades it.

    Args:
        model: The world.
        registry: The normalized registry, or None when this machine has no
            install. A missing registry costs the throughput section and the
            whole inventory section - every item total is withheld, because no
            key can be checked against a vocabulary that is not there - and
            nothing else: the placements, the tallies and the bounds still ship.

    Returns:
        The body, keyed by :data:`DATA_KEYS`.
    """
    placed = placement_model.placement_of(model)
    held = inventory_model.inventory_of(model)
    served, raised = _throughput(placed, registry)
    stocked, withheld = _inventory(held.items, registry)
    return {
        "schema": SCHEMA,
        "masked_token": masked_token(model.token),
        "coordinate_units": placed.coordinate_units,
        "node_semantics_available": placed.node_semantics_available,
        "node_orientation_available": placed.node_orientation_available,
        "bounds": _bounds(placed.bounds),
        "nodes": _placements(placed.node_placements),
        "node_counts": _counts(placed.node_counts),
        "built": _placements(placed.built_placements),
        "built_counts": _counts(placed.built_counts),
        "inventory": stocked,
        "throughput": served,
        "warnings": [
            *_carried(placed.warnings),
            *_carried(held.warnings),
            *raised,
            *withheld,
        ],
    }


def make_handler(
    worlds: contract.WorldProvider[WorldModel],
    registries: contract.RegistryProvider[Registry],
) -> contract.Handler:
    """Bind both providers and return the handler that answers this route.

    THE PROVIDERS ARE BOUND BY CLOSURE RATHER THAN PASSED PER REQUEST, which is
    the shape ``contract.Handler`` publishes: the server binds what an endpoint
    needs before registering it, so this module never imports the server and
    never learns how a world or a registry was obtained.

    Args:
        worlds: Whatever hands over the current world, or says there is not one.
        registries: Whatever hands over the registry, or says there is not one.

    Returns:
        The handler.
    """

    def handle(query: Mapping[str, str]) -> contract.Response:
        """Answer one request.

        Args:
            query: The parsed query parameters. This endpoint accepts none.

        Returns:
            200 with the map, 503 when this machine has no save to read, or 400
            when the request named a parameter. The 400 reflects NOTHING of what
            it refused - on this machine a query value can be a save path or an
            account directory. A missing REGISTRY is not a refusal: the body
            still answers 200 and says what it could not join.
        """
        if query:
            return contract.bad_request(ENDPOINT, contract.REASON_UNKNOWN_PARAMETER)
        model = worlds.world()
        if model is None:
            return contract.unavailable(ENDPOINT, contract.REASON_NO_SAVE)
        return contract.ok(ENDPOINT, _body(model, registries.registry()))

    return handle


def routes(
    worlds: contract.WorldProvider[WorldModel],
    registries: contract.RegistryProvider[Registry],
) -> tuple[contract.Route, ...]:
    """Publish this module's own route, with both providers bound in.

    Args:
        worlds: Whatever hands over the current world, or says there is not one.
        registries: Whatever hands over the registry, or says there is not one.

    Returns:
        The one route this module answers.
    """
    return (
        contract.Route(
            method=METHOD_GET,
            template=ENDPOINT,
            handler=make_handler(worlds, registries),
        ),
    )
