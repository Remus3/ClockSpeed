"""CS-977 - ``GET /api/map``, the wire the dashboard's Map panel reads.

WHAT IS COVERED HERE, AND THE AUTHORITY FOR EACH ARM

a. THE BODY IS BUILT BY NAMING FIELDS, ASSERTED ON THE SHIPPED AST. This is the
   twin of ``tests/surface/test_world.py``'s arm (a):
   ``clockspeed/surface/api/map.py`` holds no ``asdict``, ``astuple``,
   ``vars()``, ``.__dict__`` and no ``dataclasses.fields`` walk. Every detector
   is run against a PLANTED POSITIVE, because a structural guard that matches
   nothing is green and grades nothing.
b. THE SURFACE PERFORMS NO ARITHMETIC. ``clockspeed/surface/api/__init__.py``
   states it outright - "An endpoint serializes a model and returns it. It
   performs no arithmetic" - so the module holds no arithmetic binary operator
   at all. The items-per-minute figure is produced by
   ``clockspeed.solve.exact.per_minute``, which is a layer BELOW this one and
   already owns the zero-duration rule.
c. THE PRIVACY SWEEP RUNS THROUGH THE REAL LOADER, IN BOTH DIRECTIONS. Distinct
   invented markers go into the save name, the map name, the options string, the
   session name, the world token and every record string; the bytes go through
   ``world.load_world_from_bytes``; the response is encoded; the marker count on
   the wire is asserted ZERO. That half alone passes on an empty response, so
   the same arm asserts the wire DOES carry ``masked_token(<the token canary>)``
   and DOES carry the two class names. A negative control plants a one-line
   leaky serializer and asserts the sweep FINDS it.
d. EVERY COORDINATE IS A STRING AND EVERY COUNT IS AN INTEGER. A bare JSON
   number is read by a browser as an IEEE double, which is what non-negotiable 6
   keeps out of the answer path; ``contract.encode`` refuses a float outright,
   so the arm asserts the TYPE as well as encoding successfully.
e. NO WORLD IS 503 AND NEVER 501. The save layer ships and works; what is absent
   is its input. See ``clockspeed/surface/api/contract.py``, "THE 501/503 SPLIT
   IS LOAD-BEARING".
f. AN AUDIT WARNING KEEPS ITS OWN SOURCE. ``clockspeed/audit/placement.py`` and
   ``clockspeed/audit/inventory.py`` raise warnings under the sources
   ``placement`` and ``inventory``. Remapping them to ``map`` would destroy the
   one field that says which layer flagged the thing. Only a warning THIS module
   raises carries ``map``.
g. THE THROUGHPUT ROW SEPARATES WHAT WAS MEASURED FROM WHAT WAS ASSUMED. The
   normal-purity figure is derived from two fields the shipped docs carry, so it
   ships as an exact rate. The purity multipliers are NOT measured anywhere on
   this machine - ``docs/adr/0003-s4-node-actors-in-save.md`` measured a node's
   purity absent from a save and ``clockspeed/data/registry.py`` records that no
   purity multiplier is exported - so they ship as a stated assumption with
   ``purity_scaling_measured`` false beside them.
h. A MISSING RATE IS NULL AND NEVER ZERO. ``Extractor.items_per_cycle`` and
   ``Extractor.extract_cycle_time`` are None on measured entries, and a zero
   there is a power plan nothing can detect as wrong.

Test-quality discipline (CONVENTIONS.md section 7.2). Every sweep binds its
population size to a scalar and asserts an expected count BEFORE it iterates,
and every leak count is bound to a scalar before it is asserted - pytest renders
the asserted EXPRESSION independently of the message.

NO REAL CONTENT REACHES THIS MODULE. Every canary is an invented ASCII marker,
every save is synthetic bytes driven through the real loader, and every registry
is a hand-built literal. The suite runs on a machine with no game installed and
no save present.
"""

from __future__ import annotations

import ast
import inspect
from fractions import Fraction
from types import MappingProxyType
from typing import TYPE_CHECKING, Final

import pytest

from clockspeed.audit import inventory as inventory_model
from clockspeed.audit import placement as placement_model
from clockspeed.data.registry import Extractor, Item, Registry
from clockspeed.save import usmap, world
from clockspeed.save.header import masked_token
from clockspeed.surface.api import contract
from clockspeed.surface.api import map as endpoint
from tests.save import synthetic

if TYPE_CHECKING:
    from collections.abc import Mapping

# ---------------------------------------------------------------------------
# The canaries. INVENTED MARKERS, never a value read off this machine. Each is
# distinct and shares no substring with another, so one marker's hit cannot be
# counted as another's.
# ---------------------------------------------------------------------------

CANARY_SAVE_NAME: Final = "MapCanarySaveNameYa01"
CANARY_MAP_NAME: Final = "MapCanaryMapNameYb02"
CANARY_OPTIONS: Final = "MapCanaryOptionsYc03"
CANARY_SESSION_NAME: Final = "MapCanarySessionYd04"
CANARY_TOKEN: Final = "MapCanaryTokenYe05"  # noqa: S105 - an invented marker, not a secret
CANARY_INSTANCE: Final = "MapCanaryInstanceYf06"
CANARY_ROOT: Final = "MapCanaryRootObjectYg07"

#: The five the HEADER carries.
HEADER_CANARIES: Final = (
    CANARY_SAVE_NAME,
    CANARY_MAP_NAME,
    CANARY_OPTIONS,
    CANARY_SESSION_NAME,
    CANARY_TOKEN,
)

#: Every marker that must NEVER reach the wire, and the size the sweep asserts
#: before it iterates. A sweep over an empty tuple passes vacuously.
WITHHELD_CANARIES: Final = (*HEADER_CANARIES, CANARY_INSTANCE, CANARY_ROOT)
EXPECTED_WITHHELD_CANARIES: Final = 7

NO_LEAKS: Final = 0
ONE_PLANTED_LEAK: Final = 1
THREE_PLANTED_TOKENS: Final = 3

#: How many of the two record markers must reach the record table, and how many
#: per-class tallies and refusal branches each sweep below grades.
BOTH_RECORD_MARKERS: Final = 2
EXPECTED_TALLIES: Final = 2
EXPECTED_BRANCHES: Final = 4
ONE_ROUTE: Final = 1

# ---------------------------------------------------------------------------
# The fixture world. One node class and one built class, each with a transform
# whose coordinates are exactly representable so the expectation is exact.
# ---------------------------------------------------------------------------

NODE_CLASS: Final = "BP_ResourceNode_C"
BUILT_CLASS: Final = "Build_MinerMk1_C"
UNLISTED_CLASS: Final = "Build_ConveyorBeltMk1_C"

NODE_PATH: Final = "/Synthetic/Nodes/" + NODE_CLASS + "." + NODE_CLASS
BUILT_PATH: Final = "/Synthetic/Build/" + BUILT_CLASS + "." + BUILT_CLASS
UNLISTED_PATH: Final = "/Synthetic/Build/" + UNLISTED_CLASS + "." + UNLISTED_CLASS

NODE_TRANSLATION: Final = (-1024.0, 512.0, -64.0)
BUILT_TRANSLATION: Final = (2048.0, -256.0, 128.0)

#: The built actor's ORIENTATION. Every component is exactly representable in
#: float32 and none of them is the identity, so an arm that graded a dropped
#: rotation against the default quaternion would fail rather than pass.
BUILT_ROTATION: Final = (0.5, -0.25, 0.125, 0.8125)
BUILT_SCALE: Final = (2.0, 0.5, -1.5)

#: The NODE's orientation, deliberately different from the building's in every
#: component. A seam that served one population the other's block, or that
#: served a shared default, fails rather than passing on a coincidence.
NODE_ROTATION: Final = (-0.75, 0.0625, -0.375, 0.25)
NODE_SCALE: Final = (0.25, -2.0, 4.0)

ROTATION_COMPONENTS: Final = 4
SCALE_COMPONENTS: Final = 3

#: One node and one built actor survive the allowlist; the third record is a
#: belt, which the allowlist deliberately excludes.
EXPECTED_NODES: Final = 1
EXPECTED_BUILT: Final = 1
EXPECTED_RECORDS: Final = 3
EXPECTED_PLACEMENTS: Final = 2

# ---------------------------------------------------------------------------
# The fixture registry. Hand-built literals; nothing here reads the install.
# ---------------------------------------------------------------------------

MINER_DISPLAY_NAME: Final = "Synthetic Miner"
ITEM_KEY: Final = "Desc_SyntheticOre_C"
ITEM_DISPLAY_NAME: Final = "Synthetic Ore"

#: One item per cycle over a one-second cycle is sixty per minute, exactly.
MINER_ITEMS_PER_CYCLE: Final = Fraction(1)
MINER_CYCLE_TIME: Final = Fraction(1)
MINER_PER_MINUTE: Final = "60"

#: The generic walkers. Any one of them turns "the fields this response names"
#: into "whatever the dataclass happens to hold".
GENERIC_WALKERS: Final = ("asdict", "astuple", "vars", "fields", "__dict__", "__dataclass_fields__")
EXPECTED_GENERIC_WALKERS: Final = 6

#: Formatting constructs. A response value built by interpolation is one edit
#: away from publishing whatever it was built from.
FORMATTING_NODES: Final = (ast.JoinedStr, ast.FormattedValue)

#: The arithmetic operators. ``BitOr`` is deliberately absent: ``Fraction | None``
#: in an annotation is an ``ast.BinOp`` and is not arithmetic.
ARITHMETIC_OPS: Final = (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow)

#: The node types an arithmetic operator can hide in. ``AugAssign`` is here
#: because ``total += 1`` is arithmetic no ``ast.BinOp`` sweep would see, and an
#: accumulator is the shape a counting loop naturally takes.
ARITHMETIC_NODES: Final = (ast.BinOp, ast.AugAssign)

#: The published key tuples, each with the size its arm asserts BEFORE it
#: compares a served body against it. A tuple that was silently emptied would
#: make every shape arm pass by comparing two empty sets - the exact vacuity
#: this file's own stub phase measured, and the one hole it found.
EXPECTED_DATA_KEYS: Final = 13
EXPECTED_BOUNDS_KEYS: Final = 6
EXPECTED_PLACEMENT_KEYS: Final = 6
EXPECTED_INVENTORY_KEYS: Final = 3
EXPECTED_THROUGHPUT_KEYS: Final = 9
EXPECTED_WARNING_KEYS: Final = 3
EXPECTED_WARNING_SOURCES: Final = 3
EXPECTED_PURITIES: Final = 3

#: Attribute names this module must never read off a header or a record. Named
#: explicitly so a reader sees the danger rather than inferring it from absence.
FORBIDDEN_ATTRIBUTE_READS: Final = frozenset(
    {
        "map_name",
        "datetime_ticks",
        "play_duration",
        "byte_after_datetime_ticks",
        "editor_object_version",
        "instance_name",
        "root_object",
        "body_offset",
        "body_length",
        "first_index",
    }
)
EXPECTED_FORBIDDEN_READS: Final = 10


# ---------------------------------------------------------------------------
# Providers and fixtures
# ---------------------------------------------------------------------------


class _Worlds:
    """A world provider that hands back whatever it was built with."""

    def __init__(self, model: world.WorldModel | None) -> None:
        """Hold the world this provider answers with.

        Args:
            model: The world, or None for the no-save case.
        """
        self._model = model

    def world(self) -> world.WorldModel | None:
        """Answer with the held world.

        Returns:
            The world, or None.
        """
        return self._model


class _Registries:
    """A registry provider that hands back whatever it was built with."""

    def __init__(self, value: Registry | None) -> None:
        """Hold the registry this provider answers with.

        Args:
            value: The registry, or None for the no-install case.
        """
        self._value = value

    def registry(self) -> Registry | None:
        """Answer with the held registry.

        Returns:
            The registry, or None.
        """
        return self._value


def empty_property_map() -> usmap.PropertyMap:
    """A mapping that models nothing at all.

    Passing an explicit mapping is not optional: ``None`` resolves the INSTALLED
    one, and this package's tests must pass on a machine that has never had the
    game on it.

    Returns:
        The mapping.
    """
    return usmap.PropertyMap(
        names=(),
        enums={},
        schemas={},
        warnings=(),
        container=usmap.UsmapContainer(
            magic=usmap.USMAP_MAGIC,
            version=0,
            compression_method=usmap.COMPRESSION_NONE,
            compressed_size=0,
            decompressed_size=0,
            header_size=0,
        ),
        body_consumed=0,
    )


def canary_blob() -> bytes:
    """Build a canary-laden synthetic save holding one node and two buildings.

    Returns:
        The whole blob.
    """
    return synthetic.build_save(
        header_kwargs={
            "save_name": CANARY_SAVE_NAME,
            "map_name": CANARY_MAP_NAME,
            "options": "?" + CANARY_OPTIONS,
            "session_name": CANARY_SESSION_NAME,
            "world_token": CANARY_TOKEN,
        },
        objects=(
            synthetic.SyntheticObject(
                NODE_PATH,
                CANARY_ROOT,
                CANARY_INSTANCE + "_0",
                translation=NODE_TRANSLATION,
                rotation=NODE_ROTATION,
                scale=NODE_SCALE,
            ),
            synthetic.SyntheticObject(
                BUILT_PATH,
                CANARY_ROOT,
                CANARY_INSTANCE + "_1",
                translation=BUILT_TRANSLATION,
                rotation=BUILT_ROTATION,
                scale=BUILT_SCALE,
            ),
            synthetic.SyntheticObject(
                UNLISTED_PATH, CANARY_ROOT, CANARY_INSTANCE + "_2", translation=BUILT_TRANSLATION
            ),
        ),
    )


def canary_world() -> world.WorldModel:
    """Drive the canary-laden save through the REAL loader.

    The FLAT body layout is named because the synthetic corpus is flat-bodied
    and the default is the levelled reader a real save has (CS-409).

    Returns:
        The loaded world.
    """
    return world.load_world_from_bytes(
        canary_blob(),
        property_map=empty_property_map(),
        body_layout=world.BODY_LAYOUT_FLAT,
    )


def empty_world() -> world.WorldModel:
    """Drive a record-free synthetic save through the REAL loader.

    Returns:
        The loaded world, which carries no placement at all.
    """
    return world.load_world_from_bytes(
        synthetic.build_save(objects=()),
        property_map=empty_property_map(),
        body_layout=world.BODY_LAYOUT_FLAT,
    )


def miner_extractor(
    *,
    items_per_cycle: Fraction | None = MINER_ITEMS_PER_CYCLE,
    cycle_time: Fraction | None = MINER_CYCLE_TIME,
) -> Extractor:
    """Build the fixture extractor, optionally with a missing or zero operand.

    Args:
        items_per_cycle: mItemsPerCycle, or None for the unmeasured case.
        cycle_time: mExtractCycleTime, or None on the same terms.

    Returns:
        The extractor.
    """
    return Extractor(
        key=BUILT_CLASS,
        display_name=MINER_DISPLAY_NAME,
        items_per_cycle=items_per_cycle,
        extract_cycle_time=cycle_time,
        allowed_forms=frozenset({"RF_SOLID"}),
    )


def fixture_registry(*, extractor: Extractor | None = None, with_item: bool = True) -> Registry:
    """Build a small synthetic registry holding one item and one extractor.

    Args:
        extractor: The extractor to publish, or None to publish none.
        with_item: Whether the item an inventory row names has a descriptor.

    Returns:
        The registry.
    """
    item = Item(
        key=ITEM_KEY,
        display_name=ITEM_DISPLAY_NAME,
        form="RF_SOLID",
        energy_value=None,
        sink_points=None,
        is_fluid=False,
    )
    return Registry(
        items=MappingProxyType({ITEM_KEY: item} if with_item else {}),
        recipes=MappingProxyType({}),
        buildings=MappingProxyType({}),
        warnings=(),
        unknown_groups=(),
        extractors=MappingProxyType({} if extractor is None else {extractor.key: extractor}),
    )


def answer(
    model: world.WorldModel | None,
    registry: Registry | None = None,
    query: Mapping[str, str] | None = None,
) -> contract.Response:
    """Answer one request from providers holding the given inputs.

    Args:
        model: The world the provider hands back, or None.
        registry: The registry the provider hands back, or None.
        query: The parsed query parameters.

    Returns:
        The response.
    """
    handler = endpoint.make_handler(_Worlds(model), _Registries(registry))
    return handler({} if query is None else query)


def body_of(response: contract.Response) -> Mapping[str, object]:
    """Pull the success data out of a response, asserting it is one.

    Args:
        response: The response.

    Returns:
        The data mapping.
    """
    assert response.http_status == contract.HTTP_OK, response.payload.get("reason")
    data = response.payload["data"]
    assert isinstance(data, dict), type(data).__name__
    return data


def rows(data: Mapping[str, object], key: str) -> list[Mapping[str, object]]:
    """Pull one list-of-mappings section out of a body.

    Args:
        data: The body.
        key: The section name.

    Returns:
        The rows.
    """
    section = data[key]
    assert isinstance(section, list), key + ": " + type(section).__name__
    for item in section:
        assert isinstance(item, dict), key + ": " + type(item).__name__
    return section


def mapping_of(data: Mapping[str, object], key: str) -> Mapping[str, object]:
    """Pull one mapping section out of a body.

    Args:
        data: The body.
        key: The section name.

    Returns:
        The mapping.
    """
    section = data[key]
    assert isinstance(section, dict), key + ": " + type(section).__name__
    return section


def endpoint_tree() -> ast.Module:
    """Parse the shipped endpoint module.

    Returns:
        The AST of the module as installed, not of a copy.
    """
    return ast.parse(inspect.getsource(endpoint))


def docstring_ids(tree: ast.AST) -> frozenset[int]:
    """The ids of every docstring constant node, so a sweep can skip them.

    Args:
        tree: A parsed module.

    Returns:
        The node ids.
    """
    holders = (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
    found: set[int] = set()
    for node in ast.walk(tree):
        if not isinstance(node, holders) or not node.body:
            continue
        first = node.body[0]
        if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant):
            found.add(id(first.value))
    return frozenset(found)


def code_tokens(tree: ast.AST) -> frozenset[str]:
    """Every name, attribute and non-docstring string constant in a tree.

    Args:
        tree: A parsed module.

    Returns:
        The tokens.
    """
    skip = docstring_ids(tree)
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            found.add(node.id)
        elif isinstance(node, ast.Attribute):
            found.add(node.attr)
        elif (
            isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in skip
        ):
            found.add(node.value)
    return frozenset(found)


def attribute_reads(tree: ast.AST) -> frozenset[str]:
    """Every attribute name read anywhere in a tree, at any depth.

    Args:
        tree: A parsed module.

    Returns:
        The attribute names.
    """
    return frozenset(node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute))


def arithmetic_ops(tree: ast.AST) -> list[str]:
    """Every arithmetic operator in a tree, by operator class name.

    BOTH SHAPES ARE SWEPT. ``a / b`` is an ``ast.BinOp`` and ``total += 1`` is an
    ``ast.AugAssign``, and a sweep over only the first is green over every
    counting loop in the module it grades.

    Args:
        tree: A parsed module.

    Returns:
        The operator names, which are a closed vocabulary from the ``ast``
        module rather than anything read off this machine.
    """
    return [
        type(node.op).__name__
        for node in ast.walk(tree)
        if isinstance(node, ARITHMETIC_NODES) and isinstance(node.op, ARITHMETIC_OPS)
    ]


def leak_count(blob: bytes) -> int:
    """How many withheld canaries appear in a rendering.

    THE COUNT IS THE RETURN VALUE AND THE MARKERS ARE NOT, so a failure report
    renders an int rather than the thing the sweep was hunting for.

    Args:
        blob: The encoded response.

    Returns:
        How many withheld markers are present.
    """
    return sum(1 for canary in WITHHELD_CANARIES if canary.encode("ascii") in blob)


# ---------------------------------------------------------------------------
# 1 - the AST arms (a) and (b), each with a planted positive
# ---------------------------------------------------------------------------


def test_the_endpoint_holds_no_generic_dataclass_walker() -> None:
    """A walker ships the next field somebody adds, with nobody deciding to."""
    walkers = len(GENERIC_WALKERS)
    assert walkers == EXPECTED_GENERIC_WALKERS, "the walker list holds " + str(walkers)

    present = sorted(frozenset(GENERIC_WALKERS) & code_tokens(endpoint_tree()))
    found = len(present)
    assert found == 0, "the endpoint reaches for a generic walker: " + str(present)


def test_the_walker_detector_finds_each_planted_walker() -> None:
    """The control for the arm above. A detector that matches nothing is green."""
    plants = (
        "import dataclasses\nx = dataclasses.asdict(m)\n",
        "import dataclasses\nx = dataclasses.astuple(m)\n",
        "x = vars(m)\n",
        "import dataclasses\nx = dataclasses.fields(m)\n",
        "x = m.__dict__\n",
        "x = m.__dataclass_fields__\n",
    )
    planted = len(plants)
    assert planted == EXPECTED_GENERIC_WALKERS, "plants: " + str(planted)

    caught = sum(
        1 for plant in plants if frozenset(GENERIC_WALKERS) & code_tokens(ast.parse(plant))
    )
    assert caught == planted, "the detector found " + str(caught) + " planted walkers"


def test_the_endpoint_performs_no_arithmetic_of_its_own() -> None:
    """The surface serializes and does not compute - the package docstring's rule.

    The items-per-minute figure comes from ``clockspeed.solve.exact.per_minute``,
    a layer below this one, which already owns the zero-duration rule.
    """
    operators = arithmetic_ops(endpoint_tree())
    found = len(operators)
    assert found == 0, "the endpoint performs arithmetic: " + str(operators)


def test_the_arithmetic_detector_finds_a_planted_division() -> None:
    """The control for the arm above."""
    found = len(arithmetic_ops(ast.parse("def f(a, b):\n    return a / b\n")))
    assert found == ONE_PLANTED_LEAK, "the detector found " + str(found) + " operations"


def test_the_arithmetic_detector_finds_a_planted_accumulator() -> None:
    """The second control. ``total += 1`` is arithmetic no BinOp sweep sees."""
    plant = "def f(xs):\n    t = 0\n    for x in xs:\n        t += 1\n    return t\n"
    found = len(arithmetic_ops(ast.parse(plant)))
    assert found == ONE_PLANTED_LEAK, "the detector found " + str(found) + " operations"


def test_the_arithmetic_detector_ignores_an_optional_annotation() -> None:
    """``Fraction | None`` is an ``ast.BinOp`` and is not arithmetic."""
    found = len(arithmetic_ops(ast.parse("def f(a: int | None) -> str | None:\n    return None\n")))
    assert found == 0, "the detector misread an annotation as arithmetic: " + str(found)


def test_the_endpoint_reads_no_withheld_attribute() -> None:
    """Neither a header string nor a record's own strings are read here."""
    forbidden = len(FORBIDDEN_ATTRIBUTE_READS)
    assert forbidden == EXPECTED_FORBIDDEN_READS, "the list holds " + str(forbidden)

    reached = sorted(FORBIDDEN_ATTRIBUTE_READS & attribute_reads(endpoint_tree()))
    found = len(reached)
    assert found == 0, "the endpoint reads a withheld attribute: " + str(reached)


def test_the_attribute_detector_finds_a_planted_read() -> None:
    """The control for the arm above."""
    planted = ast.parse("def f(model):\n    return model.header.map_name\n")
    hit = sorted(FORBIDDEN_ATTRIBUTE_READS & attribute_reads(planted))
    assert hit == ["map_name"], str(hit)


def test_the_endpoint_holds_no_formatting_site() -> None:
    """A response value built by interpolation publishes whatever built it."""
    tree = endpoint_tree()
    formatted = sum(1 for node in ast.walk(tree) if isinstance(node, FORMATTING_NODES))
    assert formatted == 0, "the endpoint holds " + str(formatted) + " formatting sites"


def test_the_formatting_detector_finds_a_planted_interpolation() -> None:
    """The control for the arm above."""
    planted = ast.parse('def f(name):\n    return f"leaked {name}"\n')
    found = sum(1 for node in ast.walk(planted) if isinstance(node, FORMATTING_NODES))
    assert found > 0, "the detector found no planted interpolation"


def test_the_token_detector_finds_a_planted_echo_path() -> None:
    """The control for the two token sweeps below, which share one detector."""
    planted = ast.parse("import logging\nlogging.getLogger(__name__)\nopen('x')\n")
    tokens = code_tokens(planted)
    reached = sorted({"logging", "getLogger", "open"} & tokens)
    assert len(reached) == THREE_PLANTED_TOKENS, "the detector found " + str(reached)


def test_the_endpoint_imports_no_logger_and_no_printer() -> None:
    """A log line is an echo path (non-negotiable 12)."""
    tokens = code_tokens(endpoint_tree())
    reached = sorted({"logging", "getLogger", "print", "warn"} & tokens)
    found = len(reached)
    assert found == 0, "the endpoint reaches for an echo path: " + str(reached)


def test_the_endpoint_opens_no_file() -> None:
    """This package opens nothing - not a save, not the docs, not the install."""
    tokens = code_tokens(endpoint_tree())
    reached = sorted({"open", "Path", "read_bytes", "read_text", "load_world", "locate"} & tokens)
    found = len(reached)
    assert found == 0, "the endpoint reaches for the filesystem: " + str(reached)


# ---------------------------------------------------------------------------
# 2 - the privacy sweep (c), through the REAL loader, in both directions
# ---------------------------------------------------------------------------


def test_the_fixture_really_carries_the_canaries_it_claims_to() -> None:
    """The vacuity control for the sweep. A sweep over a clean fixture is empty."""
    withheld = len(WITHHELD_CANARIES)
    assert withheld == EXPECTED_WITHHELD_CANARIES, "the canary list holds " + str(withheld)

    blob = canary_blob()
    in_header = sum(1 for canary in HEADER_CANARIES if canary.encode("ascii") in blob)
    assert in_header == len(HEADER_CANARIES), "header markers in the blob: " + str(in_header)

    model = canary_world()
    strings = {
        text
        for record in model.objects.records
        for text in (record.root_object, record.instance_name)
    }
    reached = sum(
        1 for marker in (CANARY_ROOT, CANARY_INSTANCE) if any(marker in text for text in strings)
    )
    assert reached == BOTH_RECORD_MARKERS, "record markers in the table: " + str(reached)


def test_the_fixture_really_holds_one_node_one_built_and_one_excluded_record() -> None:
    """The vacuity control for every shape arm below."""
    model = canary_world()
    records = len(model.objects.records)
    assert records == EXPECTED_RECORDS, "the fixture produced records: " + str(records)
    nodes = len(model.nodes)
    assert nodes == EXPECTED_NODES, "the fixture produced nodes: " + str(nodes)


def test_no_withheld_canary_reaches_the_wire() -> None:
    """Not one marker, in either direction."""
    withheld = len(WITHHELD_CANARIES)
    assert withheld == EXPECTED_WITHHELD_CANARIES, "the canary list holds " + str(withheld)

    blob = contract.encode(answer(canary_world(), fixture_registry()).payload)
    leaked = leak_count(blob)
    assert leaked == NO_LEAKS, "withheld markers on the wire: " + str(leaked)


def test_the_wire_carries_the_mask_and_the_class_names_so_the_sweep_is_not_vacuous() -> None:
    """The other direction. An empty body would pass the sweep above."""
    blob = contract.encode(answer(canary_world(), fixture_registry()).payload)
    assert masked_token(CANARY_TOKEN).encode("ascii") in blob, "the mask is absent"
    assert NODE_CLASS.encode("ascii") in blob, "the node class name is absent"
    assert BUILT_CLASS.encode("ascii") in blob, "the built class name is absent"


def test_the_sweep_finds_a_planted_leaky_serializer() -> None:
    """The negative control. A sweep that cannot find a leak grades nothing."""
    model = canary_world()
    response = answer(model, fixture_registry())
    payload = dict(response.payload)
    data = dict(mapping_of(payload, "data"))
    data["planted"] = model.objects.records[0].instance_name
    payload["data"] = data
    leaked = leak_count(contract.encode(payload))
    assert leaked == ONE_PLANTED_LEAK, "the sweep found " + str(leaked) + " of one planted leak"


# ---------------------------------------------------------------------------
# 3 - the body shape (d)
# ---------------------------------------------------------------------------


def test_a_world_answers_200_with_exactly_the_published_data_keys() -> None:
    """The shape is bound to the module's own published tuple, by equality."""
    published = len(endpoint.DATA_KEYS)
    assert published == EXPECTED_DATA_KEYS, "the key tuple holds " + str(published)

    data = body_of(answer(canary_world(), fixture_registry()))
    assert frozenset(data) == frozenset(endpoint.DATA_KEYS), sorted(data)


def test_every_coordinate_is_a_string_and_every_count_is_an_integer() -> None:
    """A bare JSON number is the IEEE double non-negotiable 6 keeps out."""
    data = body_of(answer(canary_world(), fixture_registry()))
    placements = rows(data, "nodes") + rows(data, "built")
    seen = len(placements)
    assert seen == EXPECTED_PLACEMENTS, "the body carries placements: " + str(seen)

    wrong = [
        axis
        for placement in placements
        for axis in ("x", "y", "z")
        if not isinstance(placement[axis], str)
    ]
    found = len(wrong)
    assert found == 0, "coordinates that are not strings: " + str(found)

    counts = dict(mapping_of(data, "node_counts"))
    counts.update(mapping_of(data, "built_counts"))
    tallies = len(counts)
    assert tallies == EXPECTED_TALLIES, "per-class tallies: " + str(tallies)
    non_integer = [key for key, value in counts.items() if not isinstance(value, int)]
    assert len(non_integer) == 0, "a count is not an integer: " + str(non_integer)


def test_every_placement_row_carries_exactly_the_published_keys() -> None:
    """No instance name, no index, no offset, no path - nothing but four fields."""
    named = len(endpoint.PLACEMENT_KEYS)
    assert named == EXPECTED_PLACEMENT_KEYS, "the key tuple holds " + str(named)

    data = body_of(answer(canary_world(), fixture_registry()))
    published = frozenset(endpoint.PLACEMENT_KEYS)
    placements = rows(data, "nodes") + rows(data, "built")
    seen = len(placements)
    assert seen == EXPECTED_PLACEMENTS, "the body carries placements: " + str(seen)
    for placement in placements:
        assert frozenset(placement) == published, sorted(placement)


def test_the_wire_carries_no_float_and_the_encoder_would_have_refused_one() -> None:
    """Both halves. The encoder's refusal is graded so the arm is not vacuous."""
    payload = answer(canary_world(), fixture_registry()).payload
    contract.encode(payload)

    planted = dict(payload)
    planted["planted"] = NODE_TRANSLATION[0]
    with pytest.raises(ValueError, match=contract.FLOAT_ON_THE_WIRE):
        contract.encode(planted)


def test_a_coordinate_round_trips_to_the_stored_value_exactly() -> None:
    """A rounding done below cannot be undone here, so the arm asserts exactness."""
    data = body_of(answer(canary_world(), fixture_registry()))
    node = rows(data, "nodes")[0]
    served = tuple(float(str(node[axis])) for axis in ("x", "y", "z"))
    assert served == NODE_TRANSLATION, str(served)


def test_the_bounds_are_six_flat_string_axes_when_a_placement_survived() -> None:
    """The panel reads ``min_x`` and not a nested axis object."""
    named = len(endpoint.BOUNDS_KEYS)
    assert named == EXPECTED_BOUNDS_KEYS, "the key tuple holds " + str(named)

    data = body_of(answer(canary_world(), fixture_registry()))
    bounds = mapping_of(data, "bounds")
    assert frozenset(bounds) == frozenset(endpoint.BOUNDS_KEYS), sorted(bounds)
    non_string = [key for key, value in bounds.items() if not isinstance(value, str)]
    assert len(non_string) == 0, "a bound is not a string: " + str(non_string)


def test_bounds_are_null_rather_than_a_synthesised_zero_box() -> None:
    """Slice CS-978 returns no box for a world with no placement, and says why.

    Six synthesised keys would read as a box that was computed and came back
    empty, which is a different claim from "there was nothing to bound".
    """
    data = body_of(answer(empty_world(), fixture_registry()))
    assert data["bounds"] is None, str(data["bounds"])

    codes = {str(row["code"]) for row in rows(data, "warnings")}
    assert placement_model.WARN_PLACEMENT_BOUNDS_UNDEFINED in codes, sorted(codes)


# ---------------------------------------------------------------------------
# 4 - the refusals (e)
# ---------------------------------------------------------------------------


def test_no_world_is_unavailable_and_never_unimplemented() -> None:
    """The 501/503 split. The save layer ships; its input is absent."""
    response = answer(None, fixture_registry())
    assert response.http_status == contract.HTTP_UNAVAILABLE, response.http_status
    assert response.http_status != contract.HTTP_NOT_IMPLEMENTED, "no world became a 501"
    assert response.payload["reason"] == contract.REASON_NO_SAVE, response.payload["reason"]
    assert response.payload["blocked_by"] is None, response.payload["blocked_by"]
    problems = contract.contract_problems(response)
    assert problems == (), str(problems)


def test_no_world_names_no_path_and_carries_no_canary() -> None:
    """A refusal body is exactly the surface that must stay safe."""
    leaked = leak_count(contract.encode(answer(None, fixture_registry()).payload))
    assert leaked == NO_LEAKS, "markers in a refusal body: " + str(leaked)


def test_an_unknown_parameter_is_a_400_that_reflects_nothing() -> None:
    """On this machine a query value can be a save path or an account directory."""
    response = answer(canary_world(), fixture_registry(), {"path": CANARY_OPTIONS})
    assert response.http_status == contract.HTTP_BAD_REQUEST, response.http_status
    assert response.payload["reason"] == contract.REASON_UNKNOWN_PARAMETER, response.payload
    blob = contract.encode(response.payload)
    assert CANARY_OPTIONS.encode("ascii") not in blob, "the 400 reflected what it refused"


def test_every_response_this_endpoint_can_build_conforms_to_the_envelope() -> None:
    """Graded by the envelope's own checker, in every branch this route has."""
    responses = (
        answer(canary_world(), fixture_registry()),
        answer(canary_world(), None),
        answer(None, fixture_registry()),
        answer(canary_world(), fixture_registry(), {"path": "x"}),
    )
    branches = len(responses)
    assert branches == EXPECTED_BRANCHES, "graded branches: " + str(branches)
    faults = {
        response.http_status: contract.contract_problems(response)
        for response in responses
        if contract.contract_problems(response)
    }
    assert faults == {}, str(faults)


# ---------------------------------------------------------------------------
# 5 - the warning sources (f)
# ---------------------------------------------------------------------------


def test_an_audit_warning_keeps_its_own_source_and_is_not_remapped_to_map() -> None:
    """The source is the one field that says which layer flagged the thing."""
    data = body_of(answer(canary_world(), fixture_registry()))
    warnings = rows(data, "warnings")
    raised = len(warnings)
    assert raised > 0, "the fixture raised no warning, so this arm grades nothing"

    named = len(endpoint.WARNING_SOURCES)
    assert named == EXPECTED_WARNING_SOURCES, "the source tuple holds " + str(named)

    sources = {str(row["source"]) for row in warnings}
    assert placement_model.SOURCE_PLACEMENT in sources, sorted(sources)
    assert inventory_model.SOURCE_INVENTORY in sources, sorted(sources)
    assert sources <= frozenset(endpoint.WARNING_SOURCES), sorted(sources)


def test_a_warning_carries_exactly_the_published_keys() -> None:
    """The ``/api/world`` warning shape, as the frozen contract states it."""
    named = len(endpoint.WARNING_KEYS)
    assert named == EXPECTED_WARNING_KEYS, "the key tuple holds " + str(named)

    published = frozenset(endpoint.WARNING_KEYS)
    data = body_of(answer(canary_world(), fixture_registry()))
    raised = len(rows(data, "warnings"))
    assert raised > 0, "the fixture raised no warning, so this arm grades nothing"
    for row in rows(data, "warnings"):
        assert frozenset(row) == published, sorted(row)
        assert isinstance(row["count"], int), type(row["count"]).__name__


def test_the_node_semantics_flag_is_served_as_a_field_and_as_a_warning() -> None:
    """ADR 0003 measured a node's resource type absent from every save."""
    data = body_of(answer(canary_world(), fixture_registry()))
    assert data["node_semantics_available"] is False, str(data["node_semantics_available"])
    codes = {str(row["code"]) for row in rows(data, "warnings")}
    assert world.WARN_NODE_SEMANTICS_UNAVAILABLE in codes, sorted(codes)


# ---------------------------------------------------------------------------
# 6 - throughput (g) and (h)
# ---------------------------------------------------------------------------


def test_a_built_extractor_yields_one_row_with_the_exact_normal_purity_rate() -> None:
    """One item over a one-second cycle is sixty a minute, exactly and as a string."""
    data = body_of(answer(canary_world(), fixture_registry(extractor=miner_extractor())))
    served = rows(data, "throughput")
    count = len(served)
    assert count == EXPECTED_BUILT, "throughput rows: " + str(count)

    named = len(endpoint.THROUGHPUT_KEYS)
    assert named == EXPECTED_THROUGHPUT_KEYS, "the key tuple holds " + str(named)

    row = served[0]
    assert frozenset(row) == frozenset(endpoint.THROUGHPUT_KEYS), sorted(row)
    assert row["class_name"] == BUILT_CLASS, str(row["class_name"])
    assert row["display_name"] == MINER_DISPLAY_NAME, str(row["display_name"])
    assert row["built"] == EXPECTED_BUILT, str(row["built"])
    assert row["per_minute_normal"] == MINER_PER_MINUTE, str(row["per_minute_normal"])


def test_the_purity_scaling_is_published_as_an_unmeasured_assumption() -> None:
    """It is not measured anywhere on this machine, and the wire says so.

    A comment nobody reads is not a disclosure. ``purity_scaling_measured``
    being false beside the numbers is.
    """
    data = body_of(answer(canary_world(), fixture_registry(extractor=miner_extractor())))
    row = rows(data, "throughput")[0]
    assert row["purity_scaling_measured"] is False, str(row["purity_scaling_measured"])
    assert row["purity_known"] is False, str(row["purity_known"])

    named = len(endpoint.PURITIES)
    assert named == EXPECTED_PURITIES, "the purity tuple holds " + str(named)

    scaling = row["purity_scaling"]
    assert isinstance(scaling, dict), type(scaling).__name__
    assert frozenset(scaling) == frozenset(endpoint.PURITIES), sorted(scaling)
    non_string = [key for key, value in scaling.items() if not isinstance(value, str)]
    assert len(non_string) == 0, "a scaling factor is not a string: " + str(non_string)
    exact = [Fraction(str(value)) for value in scaling.values()]
    assert len(exact) == len(endpoint.PURITIES), str(exact)


def test_a_missing_rate_operand_serves_null_and_never_zero() -> None:
    """A zero is a throughput claim the document never made."""
    variant = fixture_registry(extractor=miner_extractor(items_per_cycle=None))
    data = body_of(answer(canary_world(), variant))
    row = rows(data, "throughput")[0]
    assert row["per_minute_normal"] is None, str(row["per_minute_normal"])

    codes = {str(item["code"]) for item in rows(data, "warnings")}
    assert endpoint.WARN_EXTRACTION_RATE_UNAVAILABLE in codes, sorted(codes)


def test_a_declared_zero_cycle_time_serves_null_rather_than_an_infinite_rate() -> None:
    """The registry keeps a measured zero; the rate layer calls it undefined."""
    variant = fixture_registry(extractor=miner_extractor(cycle_time=Fraction(0)))
    data = body_of(answer(canary_world(), variant))
    row = rows(data, "throughput")[0]
    assert row["per_minute_normal"] is None, str(row["per_minute_normal"])

    codes = {str(item["code"]) for item in rows(data, "warnings")}
    assert endpoint.WARN_EXTRACTION_RATE_UNAVAILABLE in codes, sorted(codes)


def test_an_absent_registry_serves_no_throughput_and_says_why() -> None:
    """An empty array with no warning would read as having no extractors at all."""
    data = body_of(answer(canary_world(), None))
    served = rows(data, "throughput")
    assert len(served) == 0, "rows served with no registry: " + str(len(served))

    raised = [row for row in rows(data, "warnings") if row["source"] == endpoint.SOURCE_MAP]
    codes = {str(row["code"]) for row in raised}
    assert endpoint.WARN_EXTRACTION_RATE_UNAVAILABLE in codes, sorted(codes)
    assert endpoint.WARN_REGISTRY_UNAVAILABLE in codes, sorted(codes)


def test_a_registry_modelling_no_extractor_says_so_rather_than_answering_silently() -> None:
    """Nothing built is an extractor this build models, which is a stated fact."""
    data = body_of(answer(canary_world(), fixture_registry(extractor=None)))
    served = rows(data, "throughput")
    assert len(served) == 0, "rows served with no extractor modelled: " + str(len(served))
    codes = {str(row["code"]) for row in rows(data, "warnings")}
    assert endpoint.WARN_NO_MODELLED_EXTRACTOR_BUILT in codes, sorted(codes)


def test_the_rate_unit_is_stated_and_the_document_forms_are_served_verbatim() -> None:
    """A fluid figure is litres and a solid figure is items, and the wire says so.

    The form is NOT resolved here: ``Extractor.allowed_forms`` is a SET, and
    which resource a given extractor pulls is a property of the node it sits on,
    which ADR 0003 measured as absent from a save. So the figure is published in
    the document's own units with the forms beside it, unconverted.
    """
    data = body_of(answer(canary_world(), fixture_registry(extractor=miner_extractor())))
    row = rows(data, "throughput")[0]
    assert row["per_minute_unit"] == endpoint.RATE_UNIT, str(row["per_minute_unit"])
    assert row["allowed_forms"] == ["RF_SOLID"], str(row["allowed_forms"])


# ---------------------------------------------------------------------------
# 7 - inventory, and the one join this module performs
# ---------------------------------------------------------------------------


def test_an_inventory_row_carries_the_item_key_a_display_name_and_a_count() -> None:
    """The registry join is a NAMING and is the only join this module performs."""
    named = len(endpoint.INVENTORY_KEYS)
    assert named == EXPECTED_INVENTORY_KEYS, "the key tuple holds " + str(named)

    published = frozenset(endpoint.INVENTORY_KEYS)
    data = body_of(answer(canary_world(), fixture_registry()))
    for row in rows(data, "inventory"):
        assert frozenset(row) == published, sorted(row)
        assert isinstance(row["count"], int), type(row["count"]).__name__


def test_the_display_name_join_is_a_lookup_and_serves_null_for_an_unknown_key() -> None:
    """A synthesised name would invent a fact the registry does not hold."""
    served = endpoint.display_name_of(fixture_registry(), ITEM_KEY)
    assert served == ITEM_DISPLAY_NAME, str(served)
    assert endpoint.display_name_of(fixture_registry(with_item=False), ITEM_KEY) is None
    assert endpoint.display_name_of(None, ITEM_KEY) is None


# ---------------------------------------------------------------------------
# 8 - the route joins the published set
# ---------------------------------------------------------------------------


def test_the_endpoint_constant_is_a_route_template_this_repository_authors() -> None:
    """A literal, never a path read off a request line."""
    assert contract.ENDPOINT_PATTERN.fullmatch(endpoint.ENDPOINT) is not None, endpoint.ENDPOINT


def test_the_route_this_module_publishes_answers_get_on_its_own_template() -> None:
    """A module that owns an endpoint owns its method too."""
    published = endpoint.routes(_Worlds(None), _Registries(None))
    count = len(published)
    assert count == ONE_ROUTE, "the module published routes: " + str(count)
    route = published[0]
    assert route.template == endpoint.ENDPOINT, route.template
    assert route.method == endpoint.METHOD_GET, route.method


def test_the_provider_protocols_are_the_ones_the_contract_publishes() -> None:
    """The stubs above satisfy the published protocols, not a local lookalike."""
    assert isinstance(_Worlds(None), contract.WorldProvider), "the world stub is not a provider"
    assert isinstance(_Registries(None), contract.RegistryProvider), "the registry stub is not one"


# ---------------------------------------------------------------------------
# 9 - CS-1013: the orientation the audit seam used to drop
# ---------------------------------------------------------------------------


def test_a_built_row_carries_the_rotation_and_the_scale_as_arrays_of_strings() -> None:
    """``objects.Transform`` parsed three blocks and this wire published one.

    Every component is a STRING for the reason a coordinate is one: a bare JSON
    number is the IEEE double non-negotiable 6 keeps out of the answer path, and
    a rotation component is the same kind of stored float a coordinate is.
    """
    data = body_of(answer(canary_world(), fixture_registry()))
    built = rows(data, "built")
    seen = len(built)
    assert seen == EXPECTED_BUILT, "the body carries built rows: " + str(seen)

    rotation = built[0]["rotation"]
    scale = built[0]["scale"]
    assert isinstance(rotation, list), type(rotation).__name__
    assert isinstance(scale, list), type(scale).__name__
    assert len(rotation) == ROTATION_COMPONENTS, str(rotation)
    assert len(scale) == SCALE_COMPONENTS, str(scale)
    assert [item for item in rotation + scale if not isinstance(item, str)] == []


def test_an_orientation_component_round_trips_to_the_stored_value_exactly() -> None:
    """A rounding done below cannot be undone here, so the arm asserts exactness.

    This is also the arm that grades the DEFECT: the fixture's rotation is not
    the identity, so a wire that dropped the block and a wire that published a
    default would both fail here.
    """
    data = body_of(answer(canary_world(), fixture_registry()))
    built = rows(data, "built")[0]
    rotation = built["rotation"]
    scale = built["scale"]

    assert isinstance(rotation, list), type(rotation).__name__
    assert isinstance(scale, list), type(scale).__name__

    served_rotation = tuple(float(str(part)) for part in rotation)
    served_scale = tuple(float(str(part)) for part in scale)

    assert served_rotation == BUILT_ROTATION, str(served_rotation)
    assert served_scale == BUILT_SCALE, str(served_scale)


def test_a_node_row_carries_its_own_orientation_off_the_real_parser() -> None:
    """A node's rotation was dropped by ``_node_or_none``, not absent from the file.

    The fixture packs a DISTINCT quaternion into the node's float32 transform
    bytes, so this arm dies if either seam drops the block and dies again if a
    seam substitutes the building's.
    """
    data = body_of(answer(canary_world(), fixture_registry()))
    node_rows = rows(data, "nodes")
    seen = len(node_rows)
    assert seen == EXPECTED_NODES, "the body carries node rows: " + str(seen)

    rotation = node_rows[0]["rotation"]
    scale = node_rows[0]["scale"]
    assert isinstance(rotation, list), type(rotation).__name__
    assert isinstance(scale, list), type(scale).__name__

    served_rotation = tuple(float(str(part)) for part in rotation)
    served_scale = tuple(float(str(part)) for part in scale)
    assert served_rotation == NODE_ROTATION, str(served_rotation)
    assert served_scale == NODE_SCALE, str(served_scale)
    assert served_rotation != BUILT_ROTATION, "the node was served the building's rotation"


def test_the_orientation_capability_flag_is_served_and_the_rows_honour_it() -> None:
    """``node_orientation_available`` is the counterpart of ``node_semantics_available``.

    Asserted TOGETHER with the rows, because a True flag over null rows is a
    worse answer than no flag at all - a consumer that branched on it would
    build a rotation matrix out of nothing.
    """
    data = body_of(answer(canary_world(), fixture_registry()))

    assert data["node_orientation_available"] is True, str(data["node_orientation_available"])
    assert data["node_semantics_available"] is False, str(data["node_semantics_available"])

    node_rows = rows(data, "nodes")
    seen = len(node_rows)
    assert seen == EXPECTED_NODES, "the body carries node rows: " + str(seen)
    unoriented = [row for row in node_rows if row["rotation"] is None or row["scale"] is None]
    assert unoriented == [], "the flag claims an orientation these rows do not carry"


def test_an_orientation_never_reaches_the_wire_as_a_float() -> None:
    """The mutation goes into THE ORIENTATION THIS ENDPOINT BUILT, not beside it.

    The earlier cut of this arm planted a float under a brand new key and so
    graded pre-existing encoder behaviour - its oracle never observed a rotation
    at all, and it survived a mutant that reverted the row to four keys. This
    version reaches into the served body, finds the built row's own rotation
    array, and swaps one rendered string back to the float it came from. A
    response that carries no rotation cannot be mutated that way and fails at
    the control.
    """
    payload = answer(canary_world(), fixture_registry()).payload
    contract.encode(payload)

    data = body_of(answer(canary_world(), fixture_registry()))
    built = rows(data, "built")[0]
    rotation = built["rotation"]

    # The control. There must BE an orientation here to corrupt.
    assert isinstance(rotation, list), type(rotation).__name__
    assert len(rotation) == ROTATION_COMPONENTS, str(rotation)

    corrupted = dict(built)
    corrupted["rotation"] = [BUILT_ROTATION[0], *rotation[1:]]
    with pytest.raises(ValueError, match=contract.FLOAT_ON_THE_WIRE):
        contract.encode({"data": {"built": [corrupted]}})


def test_the_orientation_keys_are_published_and_the_emitter_actually_emits_them() -> None:
    """The tuple and the BUILDER are bound together, in both directions.

    The earlier cut asserted membership in the constant tuple alone and was
    blind to ``_placements``: a mutant that reverted the emitter to four keys
    left the tuple untouched and the arm green. A key tuple nothing emits is a
    published promise the wire does not keep, so the assertion below is over a
    row this endpoint really built.
    """
    published = frozenset(endpoint.PLACEMENT_KEYS)
    assert "rotation" in published, sorted(published)
    assert "scale" in published, sorted(published)

    data = body_of(answer(canary_world(), fixture_registry()))
    emitted = rows(data, "nodes") + rows(data, "built")
    seen = len(emitted)
    assert seen == EXPECTED_PLACEMENTS, "the body carries placements: " + str(seen)

    unkept = [key for key in endpoint.PLACEMENT_KEYS if any(key not in row for row in emitted)]
    assert unkept == [], "published keys the emitter never emits: " + str(unkept)


def test_no_withheld_canary_rides_in_on_the_orientation() -> None:
    """Widening the row must not widen what the row withholds.

    The sweep is over the SERVED BYTES, so a marker hidden in a nested array is
    caught as readily as one in a top-level string.
    """
    served = contract.encode(answer(canary_world(), fixture_registry()).payload).decode("ascii")
    planted = len(WITHHELD_CANARIES)
    assert planted == EXPECTED_WITHHELD_CANARIES, "canaries planted: " + str(planted)

    leaked = [marker for marker in WITHHELD_CANARIES if marker in served]
    assert len(leaked) == NO_LEAKS, "markers on the wire: " + str(len(leaked))
    assert str(BUILT_ROTATION[0]) in served, "the sweep found no orientation, so it is vacuous"
