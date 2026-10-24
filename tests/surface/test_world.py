"""CS-601 slice S3 - ``/api/world``, the endpoint a real save reaches the wire through.

THIS IS THE PII-CRITICAL ENDPOINT ON THIS MACHINE. The server auto-detects and
loads the operator's own save at startup, so every value this endpoint names is
derived from a personal-data-bearing artifact (non-negotiables 11 and 12), not
from a hypothetical one. What is covered, and the authority for each arm:

a. THE BODY IS BUILT BY NAMING FIELDS, AND THAT IS ASSERTED ON THE AST RATHER
   THAN READ OFF THE OUTPUT. ``clockspeed/surface/api/world.py`` holds no
   ``asdict``, ``astuple``, ``vars()``, ``.__dict__`` and no
   ``dataclasses.fields`` - the generic walkers, any one of which would ship the
   next field added to ``SaveHeader`` without anyone deciding to. A second arm
   pins the COMPLETE set of attribute names the module reads, anywhere, to a
   published allow-list by EQUALITY. Equality is strictly stronger than the
   subset the slice brief asked for: adding ``map_options`` to ``SaveHeader``
   tomorrow and reading it here turns this red with nobody remembering to, and
   so does silently dropping a field the response is supposed to carry.
b. THE TWO READS THAT CANNOT BE JUDGED BY NAME ALONE ARE JUDGED BY SITE.
   ``token`` is read, and must reach ``masked_token`` and nothing else
   (``clockspeed/save/world.py`` declares it PERSONAL DATA). ``records`` and
   ``nodes`` are read, and must reach ``len`` and nothing else - a record
   carries the operator's own actor names (``clockspeed/save/objects.py``,
   whose ``ObjectRecord.__repr__`` withholds every string for that reason) and
   a node carries its instance name.
c. EVERY DETECTOR ABOVE IS RUN AGAINST A PLANTED POSITIVE. A structural guard
   that matches nothing is green and grades nothing, which is the failure class
   ``memory/test-quality-failure-classes.md`` records and the one the most
   recent commit before this slice was filed about.
d. THE CANARY SWEEP RUNS THROUGH THE REAL LOADER, IN BOTH DIRECTIONS. Distinct
   markers are planted in the save name, the map name, the options string, the
   session name, the world token and three object strings; the bytes go through
   ``world.load_world_from_bytes``; the response is encoded; and the count of
   markers on the wire is asserted ZERO. That half alone passes on an empty
   response, so the same arm asserts the wire DOES carry
   ``masked_token(<the token canary>)``. A negative control plants a one-line
   leaky serializer and asserts the sweep FINDS it.
e. THE ONE DELIBERATE ASYMMETRY IS TESTED AS AN ASYMMETRY. A modelled class
   path must not reach the wire; an UNMODELLED one must, because reporting
   unmodelled content is what non-negotiable 7 requires. Asserting only the
   absence would be satisfied by an endpoint that reports nothing at all.
f. NO WORLD IS 503 AND NEVER 501. The save layer is written and works; its
   input is absent. Rendering that as 501 would tell the operator the save
   reader is unwritten (``clockspeed/surface/api/contract.py``, "THE 501/503
   SPLIT IS LOAD-BEARING").

Test-quality discipline (CONVENTIONS.md section 7.2, and this package's own
``__init__``). Every sweep binds its population size to a scalar and asserts an
expected count BEFORE it iterates, and every leak count is bound to a scalar
before it is asserted - pytest renders the asserted EXPRESSION independently of
the message, so ``assert not leaked`` prints the leaked values into the report.

NO REAL CONTENT REACHES THIS MODULE. Every canary below is an invented ASCII
marker and every fixture is synthetic save BYTES driven through the real
loader. A hand-built ``WorldModel`` literal would agree with this module's own
idea of the shape by construction and would prove nothing about the real one.
"""

from __future__ import annotations

import ast
import inspect
from typing import Final

import pytest

from clockspeed.save import objects, usmap, world
from clockspeed.save.header import masked_token
from clockspeed.surface.api import contract
from clockspeed.surface.api import world as endpoint
from tests.save import synthetic
from tests.surface.test_health import HOME_SHAPED, planted_reflection, reflected_in

# ---------------------------------------------------------------------------
# The canaries. INVENTED MARKERS, never a value read off this machine.
#
# Each is distinct, so a sweep cannot report one marker's absence as evidence
# about another, and each is pure ASCII with no substring shared with any
# other - a shared prefix would make one hit look like two.
# ---------------------------------------------------------------------------

CANARY_SAVE_NAME: Final = "CanarySaveNameZa01"
CANARY_MAP_NAME: Final = "CanaryMapNameZb02"
CANARY_OPTIONS: Final = "CanaryOptionsZc03"
CANARY_SESSION_NAME: Final = "CanarySessionZd04"
CANARY_TOKEN: Final = "CanaryWorldTokenZe05"  # noqa: S105 - an invented marker, not a secret
CANARY_INSTANCE: Final = "CanaryInstanceZf06"
CANARY_ROOT: Final = "CanaryRootObjectZg07"
CANARY_MODELLED_NAME: Final = "Build_CanaryModelledZh08_C"

#: The class path whose name the fixture's property map DOES model, so it is a
#: class this project understands and its path has no business on the wire.
CANARY_MODELLED_PATH: Final = f"/Canary/Parts/{CANARY_MODELLED_NAME}.{CANARY_MODELLED_NAME}"

#: The class path nothing models. Its presence on the wire is REQUIRED - see
#: arm (e) and non-negotiable 7.
CANARY_UNMODELLED_NAME: Final = "Build_CanaryUnmodelledZi09_C"
CANARY_UNMODELLED_PATH: Final = f"/Canary/Parts/{CANARY_UNMODELLED_NAME}.{CANARY_UNMODELLED_NAME}"

#: The five the HEADER carries. The header is uncompressed, so these are
#: findable in the save blob itself.
HEADER_CANARIES: Final = (
    CANARY_SAVE_NAME,
    CANARY_MAP_NAME,
    CANARY_OPTIONS,
    CANARY_SESSION_NAME,
    CANARY_TOKEN,
)
EXPECTED_HEADER_CANARIES: Final = 5

#: The three the RECORD TABLE carries. The body is zlib-framed, so these are
#: not findable in the blob and are checked in the parsed table instead.
EXPECTED_RECORD_CANARIES: Final = 3

#: Every marker that must NEVER reach the wire, and the count the sweep asserts
#: before it iterates. A sweep over an empty tuple passes vacuously.
WITHHELD_CANARIES: Final = (
    *HEADER_CANARIES,
    CANARY_INSTANCE,
    CANARY_ROOT,
    CANARY_MODELLED_PATH,
)
EXPECTED_WITHHELD_CANARIES: Final = 8

#: No marker at all may appear.
NO_LEAKS: Final = 0

#: What the negative control plants: exactly one leaky field.
ONE_PLANTED_LEAK: Final = 1


# ---------------------------------------------------------------------------
# The allow-list, asserted on the shipped AST
# ---------------------------------------------------------------------------

#: The generic walkers. Any one of them turns "the fields this response names"
#: into "whatever the dataclass happens to hold", which is precisely how the
#: header options string ships the day someone adds it to ``SaveHeader``.
GENERIC_WALKERS: Final = ("asdict", "astuple", "vars", "fields", "__dict__", "__dataclass_fields__")
EXPECTED_GENERIC_WALKERS: Final = 6

#: EVERY attribute name ``clockspeed/surface/api/world.py`` reads, anywhere, at
#: any depth. A flat set rather than a per-root one on purpose: a per-root
#: detector that keys on ``Attribute.value`` being a bare ``Name`` misses
#: ``model.header.map_name``, whose outer node's value is another ``Attribute``.
#: This set is asserted EQUAL to what the module reads, so a read that is not
#: here is red and a member nothing reads any more is red too.
ALLOWED_ATTRIBUTE_READS: Final = frozenset(
    {
        # The envelope this endpoint answers through.
        "Handler",
        "Response",
        "WorldProvider",
        "REASON_NO_SAVE",
        "REASON_UNKNOWN_PARAMETER",
        "bad_request",
        "ok",
        "unavailable",
        # The provider protocol's own method, called on the bound provider.
        "world",
        # The world model. ``token`` is judged by SITE below, not by name.
        "token",
        "header",
        "objects",
        "unlocks",
        "nodes",
        "warnings",
        "contains_unmodeled_content",
        # The header. Note what is absent: map_name, datetime_ticks,
        # play_duration, byte_after_datetime_ticks, editor_object_version.
        "header_version",
        "save_version",
        "build_changelist",
        "body_offset",
        "is_modded",
        # The object table. ``records`` is judged by SITE below.
        "records",
        "level_count",
        "unknown_classes",
        # The unlock state.
        "purchased_schematics",
        "recipes",
        "scanned_resources",
        "current_game_phase",
        "feature_flags",
        "is_empty",
        "items",
        # One carried warning.
        "source",
        "code",
        "detail",
        "subject",
        "count",
        # One unmodelled class. ``type_path`` HERE is the asymmetry - see arm
        # (e) and the endpoint's own module docstring.
        "type_path",
        "reason",
        "first_index",
        # CS-1240: the save layer's sighting report, and the optional provider
        # method its history comes from. ``stable_id`` is the same class path
        # as ``type_path`` above, so it rides the same asymmetry.
        "EMPTY_HISTORY",
        "SightingHistory",
        "sighting_history",
        "report",
        "checked",
        "this_save",
        "saves_read",
        "sightings",
        "stable_id",
        "first_seen",
    }
)

#: Named explicitly so a reader of this file sees the danger rather than
#: inferring it from an absence. ``map_name`` leads the list because it is a
#: game constant, is documented as one, LOOKS safe, and is still withheld:
#: ``SaveHeader.__repr__`` omits it because its POSITION is version dependent,
#: so a dispatch bug puts an operator-authored string in it, and a response
#: body is exactly the surface that has to stay safe when the parse is wrong.
FORBIDDEN_ATTRIBUTE_READS: Final = frozenset(
    {
        "map_name",
        "datetime_ticks",
        "play_duration",
        "byte_after_datetime_ticks",
        "editor_object_version",
        "instance_name",
        "root_object",
        "parent",
        "transform",
        "translation",
        "class_name",
        "root",
        "path",
        "parts",
    }
)
EXPECTED_FORBIDDEN_READS: Final = 14

#: Reads that name a real risk and cannot be judged by name, because the name
#: is legitimately read: the attribute, and the ONLY call it may be an argument
#: of.
SITE_JUDGED_READS: Final = (("token", "masked_token"), ("records", "len"), ("nodes", "len"))
EXPECTED_SITE_JUDGED_READS: Final = 3

#: Formatting constructs. A ``detail`` line, an error message and a response
#: value are all one interpolation away from a caller's hand, so the module
#: holds no formatting site at all - the structural version of the promise
#: ``contract.py`` and ``clockspeed/save/world.py`` both state in prose.
FORMATTING_NODES: Final = (ast.JoinedStr, ast.FormattedValue)


# ---------------------------------------------------------------------------
# Detectors. Each is run against the shipped module AND against a planted
# positive, so "found nothing" is distinguishable from "looks for nothing".
# ---------------------------------------------------------------------------


def docstring_ids(tree: ast.AST) -> frozenset[int]:
    """The identity of every docstring node in a tree.

    NEEDED BECAUSE A SUBSTRING SWEEP OVER THE SOURCE GRADES THE PROSE. The
    endpoint's own docstring names all six generic walkers, in order to say that
    it holds none of them, and a raw ``"asdict" in source`` reported that
    sentence as the defect it describes.

    Args:
        tree: A parsed module.

    Returns:
        The ``id()`` of each docstring constant node.
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
    """Every identifier and non-docstring string literal a tree actually uses.

    A string literal counts because ``getattr(model, "__dict__")`` is a generic
    walk spelled without ever naming the attribute as an attribute.

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
    """Every attribute name read anywhere in a tree, at any chain depth.

    Args:
        tree: A parsed module.

    Returns:
        The attribute names.
    """
    return frozenset(node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute))


def call_names(tree: ast.AST) -> frozenset[str]:
    """Every simple name called in a tree, plus every called attribute name.

    Args:
        tree: A parsed module.

    Returns:
        The callee names.
    """
    found: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name):
            found.add(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            found.add(node.func.attr)
    return frozenset(found)


def reads_outside_call(tree: ast.AST, attribute: str, callee: str) -> int:
    """How many reads of ``attribute`` are NOT a direct argument of ``callee``.

    Args:
        tree: A parsed module.
        attribute: The attribute name to judge by site.
        callee: The only call it may be a direct argument of.

    Returns:
        The count of reads at any other site. Zero is the passing answer.
    """
    permitted: set[int] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        named = node.func.id if isinstance(node.func, ast.Name) else None
        if named is None and isinstance(node.func, ast.Attribute):
            named = node.func.attr
        if named != callee:
            continue
        permitted.update(id(argument) for argument in node.args)
    reads = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Attribute) and node.attr == attribute
    ]
    return sum(1 for node in reads if id(node) not in permitted)


def endpoint_tree() -> ast.Module:
    """Parse the shipped endpoint module.

    Returns:
        Its AST.
    """
    return ast.parse(inspect.getsource(endpoint))


# ---------------------------------------------------------------------------
# Fixtures. Synthetic BYTES through the REAL loader, never a hand-built model.
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


def canary_property_map() -> usmap.PropertyMap:
    """A mapping that models the modelled canary class and nothing else.

    Built directly rather than round-tripped through ``synthetic.build_usmap``,
    which is what ``tests/save/test_world.py`` does and why. Passing an explicit
    mapping is not optional here: ``None`` resolves the INSTALLED one, and this
    package's tests must pass on a machine that has never had the game on it.

    Returns:
        The mapping.
    """
    name = CANARY_MODELLED_NAME
    return usmap.PropertyMap(
        names=(name,),
        enums={},
        schemas={name: usmap.Schema(name=name, super_name=None, properties=())},
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
    """Build a canary-laden synthetic save.

    Every one of the five header strings ``synthetic.build_header`` accepts
    carries a distinct marker, and both object records carry markers in all
    three of their strings.

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
            synthetic.SyntheticObject(CANARY_MODELLED_PATH, CANARY_ROOT, CANARY_INSTANCE + "_0"),
            synthetic.SyntheticObject(CANARY_UNMODELLED_PATH, CANARY_ROOT, CANARY_INSTANCE + "_1"),
        ),
    )


def canary_world() -> world.WorldModel:
    """Drive the canary-laden save through the REAL loader.

    The FLAT body layout is named explicitly because the synthetic corpus is
    flat-bodied and the default is the levelled reader a real save has (CS-409).

    Returns:
        The loaded world.
    """
    return world.load_world_from_bytes(
        canary_blob(),
        property_map=canary_property_map(),
        body_layout=world.BODY_LAYOUT_FLAT,
    )


def record_canary_count(model: world.WorldModel) -> int:
    """How many of the three record markers actually reached the record table.

    THE COUNT IS THE RETURN VALUE AND THE STRINGS ARE NOT, for the same reason
    :func:`leak_count` returns an int: a caller asserts on this, so the failure
    report renders an int rather than a record's own strings.

    Args:
        model: The loaded world.

    Returns:
        How many of the three markers are present in some record string.
    """
    seen = {
        text
        for record in model.objects.records
        for text in (record.type_path, record.root_object, record.instance_name)
    }
    markers = (CANARY_INSTANCE, CANARY_ROOT, CANARY_MODELLED_PATH)
    return sum(1 for marker in markers if any(marker in text for text in seen))


def wire_bytes(model: world.WorldModel | None) -> bytes:
    """Answer one request from a provider holding ``model`` and encode the body.

    Args:
        model: The world the provider hands back, or None.

    Returns:
        The exact bytes that would go on the wire.
    """
    handler = endpoint.make_handler(_Worlds(model))
    return contract.encode(handler({}).payload)


def leak_count(blob: bytes) -> int:
    """How many withheld canaries appear in a rendering.

    THE COUNT IS THE RETURN VALUE AND THE MARKERS ARE NOT. A caller asserts on
    an int, so the failure report renders an int - the sweep itself cannot be
    the thing that publishes what it found.

    Args:
        blob: The encoded response.

    Returns:
        How many withheld markers are present.
    """
    return sum(1 for canary in WITHHELD_CANARIES if canary.encode("ascii") in blob)


# ---------------------------------------------------------------------------
# 1 - the allow-list, on the shipped AST (arm a)
# ---------------------------------------------------------------------------


def test_the_endpoint_holds_no_generic_dataclass_walker() -> None:
    """A walker ships the next field added to SaveHeader with nobody deciding to.

    Graded on the tokens the module USES rather than on its source text: the
    docstring names all six in order to say it holds none of them, and a raw
    substring sweep reported that sentence as the defect it describes.
    """
    assert len(GENERIC_WALKERS) == EXPECTED_GENERIC_WALKERS
    present = sorted(set(GENERIC_WALKERS) & code_tokens(endpoint_tree()))
    assert present == []


def test_the_walker_detector_finds_each_planted_walker() -> None:
    """The negative control. Six plants, six detections, one arm.

    ``getattr(model, "__dict__")`` is in the list because it is the generic walk
    spelled without naming the attribute as an attribute - a detector reading
    only ``ast.Attribute`` would miss it and stay green.
    """
    plants = (
        "import dataclasses\nd = dataclasses.asdict(model)\n",
        "import dataclasses\nd = dataclasses.astuple(model)\n",
        "d = vars(model)\n",
        "import dataclasses\nd = dataclasses.fields(model)\n",
        "d = getattr(model, '__dict__')\n",
        "d = model.__dataclass_fields__\n",
    )
    assert len(plants) == EXPECTED_GENERIC_WALKERS
    caught = sum(1 for plant in plants if set(GENERIC_WALKERS) & code_tokens(ast.parse(plant)))
    assert caught == EXPECTED_GENERIC_WALKERS


def test_the_endpoint_reads_exactly_the_published_allow_list() -> None:
    """Equality, which is strictly stronger than the subset the brief asked for.

    A read that is not on the list turns this red without anyone remembering to,
    and a member nothing reads any more is red too - so the list cannot quietly
    outlive the response it describes.
    """
    read = attribute_reads(endpoint_tree())
    assert read == ALLOWED_ATTRIBUTE_READS


def test_the_allow_list_names_none_of_the_withheld_fields() -> None:
    """The danger is named here rather than inferred from an absence."""
    assert len(FORBIDDEN_ATTRIBUTE_READS) == EXPECTED_FORBIDDEN_READS
    overlap = sorted(ALLOWED_ATTRIBUTE_READS & FORBIDDEN_ATTRIBUTE_READS)
    assert overlap == []


def test_the_attribute_detector_finds_a_planted_chained_read() -> None:
    """The negative control for the arm above.

    ``model.header.map_name`` is the shape a per-root detector misses, because
    the outer node's value is another ``Attribute`` rather than a ``Name``. If
    this detector could not see it, the arm above would be green over a hole.
    """
    planted = ast.parse("def f(model):\n    return model.header.map_name\n")
    found = attribute_reads(planted)
    assert "map_name" in found


# ---------------------------------------------------------------------------
# 2 - the two reads judged by SITE (arm b)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(("attribute", "callee"), SITE_JUDGED_READS)
def test_a_site_judged_read_reaches_only_its_one_permitted_call(
    attribute: str, callee: str
) -> None:
    """``token`` reaches masked_token; ``records`` and ``nodes`` reach len."""
    assert len(SITE_JUDGED_READS) == EXPECTED_SITE_JUDGED_READS
    stray = reads_outside_call(endpoint_tree(), attribute, callee)
    assert stray == 0


def test_the_site_detector_finds_a_planted_bare_read() -> None:
    """The negative control. A detector that matched nothing would pass above."""
    planted = ast.parse("def f(model):\n    return model.token\n")
    stray = reads_outside_call(planted, "token", "masked_token")
    assert stray == ONE_PLANTED_LEAK


def test_the_site_detector_accepts_the_wrapped_form() -> None:
    """The other half of the control: a wrapped read must NOT be reported."""
    planted = ast.parse("def f(model):\n    return masked_token(model.token)\n")
    stray = reads_outside_call(planted, "token", "masked_token")
    assert stray == 0


def test_the_endpoint_actually_calls_the_mask() -> None:
    """A module that never calls it satisfies every site arm above vacuously."""
    called = call_names(endpoint_tree())
    assert "masked_token" in called


# ---------------------------------------------------------------------------
# 3 - the canary sweep, BOTH directions (arm d)
# ---------------------------------------------------------------------------


def test_no_withheld_canary_reaches_the_wire() -> None:
    """Eight markers through the real loader, and none of them on the wire."""
    assert len(WITHHELD_CANARIES) == EXPECTED_WITHHELD_CANARIES
    leaked = leak_count(wire_bytes(canary_world()))
    assert leaked == NO_LEAKS


def test_the_wire_carries_the_masked_token_so_the_sweep_is_not_vacuous() -> None:
    """The half without which the arm above passes on an empty response.

    The presence is bound to a bool before it is asserted: asserting the
    membership expression directly renders the whole response body into the
    failure report, which is the one thing this module must not do.
    """
    present = masked_token(CANARY_TOKEN).encode("ascii") in wire_bytes(canary_world())
    assert present is True


def test_the_sweep_finds_a_planted_leaky_serializer() -> None:
    """The negative control for the sweep itself.

    One line - the raw token, the exact leak ``clockspeed/save/world.py``
    forbids - and the sweep must find it. Without this arm the two above are
    green when the sweep is broken, and a guard that is green because it graded
    nothing is the failure class the commit before this slice recorded.
    """
    model = canary_world()
    handler = endpoint.make_handler(_Worlds(model))
    payload = dict(handler({}).payload)
    data = dict(payload["data"])  # type: ignore[call-overload]
    data["token"] = model.token
    payload["data"] = data
    leaked = leak_count(contract.encode(payload))
    assert leaked == ONE_PLANTED_LEAK


# ---------------------------------------------------------------------------
# 4 - the deliberate asymmetry (arm e)
# ---------------------------------------------------------------------------


def test_an_unmodelled_class_path_is_reported_and_a_modelled_one_is_not() -> None:
    """A class path is asset registry content; an instance list is a census.

    Asserted as a DIFFERENCE between two paths in one response, not as an
    absence alone: an endpoint that reported nothing at all would satisfy the
    absence half and would violate non-negotiable 7.
    """
    blob = wire_bytes(canary_world())
    unmodelled_present = CANARY_UNMODELLED_PATH.encode("ascii") in blob
    modelled_present = CANARY_MODELLED_PATH.encode("ascii") in blob
    assert unmodelled_present is True
    assert modelled_present is False


def test_the_endpoint_docstring_states_the_asymmetry() -> None:
    """A refuter reading the module must find the answer without deriving it."""
    docstring = inspect.getdoc(endpoint) or ""
    assert "UnknownClass" in docstring
    assert "ObjectRecord" in docstring


# ---------------------------------------------------------------------------
# 5 - the shape of a success body
# ---------------------------------------------------------------------------


def test_a_world_answers_200_with_the_published_data_keys() -> None:
    """Every key the allow-list contract names, and no other."""
    response = endpoint.make_handler(_Worlds(canary_world()))({})
    data = response.payload["data"]
    assert response.http_status == contract.HTTP_OK
    assert contract.contract_problems(response) == ()
    assert isinstance(data, dict)
    assert sorted(data) == sorted(endpoint.DATA_KEYS)


def test_the_counts_are_counts_and_not_the_things_counted() -> None:
    """Two records went in, so two records are counted and neither is named."""
    response = endpoint.make_handler(_Worlds(canary_world()))({})
    data = response.payload["data"]
    assert isinstance(data, dict)
    counts = data["counts"]
    assert isinstance(counts, dict)
    assert sorted(counts) == sorted(endpoint.COUNT_KEYS)
    assert counts["objects"] == len(canary_world().objects.records)


def test_the_wire_carries_no_float_and_the_encoder_would_have_refused_one() -> None:
    """A node's translation is float32, and a bare JSON number is an IEEE double.

    ``contract.encode`` refuses a float outright (non-negotiable 6), so a
    successful encode of this payload IS the assertion. The planted half is what
    keeps that from being a statement about an encoder that refuses nothing.
    """
    response = endpoint.make_handler(_Worlds(canary_world()))({})
    payload = dict(response.payload)
    assert len(contract.encode(payload)) > 0

    payload["data"] = {"translation": 0.5}
    with pytest.raises(ValueError, match=contract.FLOAT_ON_THE_WIRE):
        contract.encode(payload)


# ---------------------------------------------------------------------------
# 6 - no world is 503, never 501 (arm f)
# ---------------------------------------------------------------------------


def test_no_world_is_unavailable_and_not_unimplemented() -> None:
    """The layer exists and works; its input is absent on this machine."""
    response = endpoint.make_handler(_Worlds(None))({})
    assert response.http_status == contract.HTTP_UNAVAILABLE
    assert response.payload["reason"] == contract.REASON_NO_SAVE
    assert contract.contract_problems(response) == ()


def test_no_world_names_no_path_and_carries_no_canary() -> None:
    """A 503 body is an echo path exactly as a 200 body is."""
    leaked = leak_count(wire_bytes(None))
    assert leaked == NO_LEAKS


def test_an_unknown_parameter_is_a_400_that_reflects_nothing() -> None:
    """This endpoint takes no parameters, and reflects none of what it refused.

    The refused value is the health suite's home-path-shaped string, ASSEMBLED
    FROM FRAGMENTS there: a tracked file may not carry an absolute path under a
    user home directory (non-negotiable 3).
    """
    reflected = HOME_SHAPED
    response = endpoint.make_handler(_Worlds(None))({"path": reflected})
    blob = contract.encode(response.payload)
    present = reflected_in(blob, reflected)
    planted = reflected_in(planted_reflection(response.payload, reflected), reflected)
    assert planted is True, "the oracle cannot find the path in a body that reflects it"
    assert response.http_status == contract.HTTP_BAD_REQUEST
    assert response.payload["reason"] == contract.REASON_UNKNOWN_PARAMETER
    assert present is False


# ---------------------------------------------------------------------------
# 7 - the module cannot reach a log or an error channel (arm M4)
# ---------------------------------------------------------------------------


def test_the_endpoint_holds_no_formatting_site() -> None:
    """No f-string, no ``.format``, no percent-formatting, and no ``raise``.

    ``clockspeed/save/world.py`` carries the cause TYPE rather than a message
    for the same reason: a message is where a value gets interpolated. This
    module has nowhere for one to land at all.
    """
    tree = endpoint_tree()
    formatted = sum(1 for node in ast.walk(tree) if isinstance(node, FORMATTING_NODES))
    raised = sum(1 for node in ast.walk(tree) if isinstance(node, ast.Raise))
    assert formatted == 0
    assert raised == 0
    assert "format" not in call_names(tree)


def test_the_endpoint_imports_no_logger_and_no_printer() -> None:
    """The response body is the only channel this module writes to."""
    source = inspect.getsource(endpoint)
    assert "logging" not in source
    assert "print(" not in source


def test_the_endpoint_opens_no_file() -> None:
    """The package docstring forbids it outright, so the module names no opener."""
    called = call_names(endpoint_tree())
    openers = sorted(called & {"open", "read_text", "read_bytes", "load_world", "load"})
    assert openers == []


# ---------------------------------------------------------------------------
# 8 - the premise every arm above rests on
# ---------------------------------------------------------------------------


def test_the_fixture_really_carries_the_canaries_it_claims_to() -> None:
    """The premise. Markers absent from the SAVE prove nothing by their absence.

    THE TWO HALVES ARE CHECKED IN DIFFERENT PLACES BECAUSE THE FILE PUTS THEM
    THERE. The header is uncompressed, so its five markers are findable in the
    blob itself; the body is zlib-framed, so the three record markers are NOT,
    and asserting on the blob for those would have been an assertion about
    compression. They are checked where the endpoint could actually read them -
    in the parsed record table.

    ``map_name`` and ``token`` are checked as BOOLS rather than by comparing the
    fields directly: both are fields whose own class declared them unsafe to
    render by shipping a ``__repr__`` that withholds them, and a rewritten
    assert renders whatever its sub-expressions read (CS-850).
    """
    planted = sum(1 for canary in HEADER_CANARIES if canary.encode("ascii") in canary_blob())
    model = canary_world()
    map_name_planted = model.header.map_name == CANARY_MAP_NAME
    token_planted = model.token == CANARY_TOKEN
    assert planted == EXPECTED_HEADER_CANARIES
    assert record_canary_count(model) == EXPECTED_RECORD_CANARIES
    assert map_name_planted is True
    assert token_planted is True


def test_the_fixture_really_produced_an_unmodelled_class() -> None:
    """Without one, the asymmetry arm's positive half proves nothing."""
    model = canary_world()
    paths = sorted(entry.type_path for entry in model.objects.unknown_classes)
    assert paths == [CANARY_UNMODELLED_PATH]
    assert model.contains_unmodeled_content is True
    assert objects.class_name_of(CANARY_MODELLED_PATH) == CANARY_MODELLED_NAME


def test_the_provider_protocol_is_the_one_the_contract_publishes() -> None:
    """The endpoint consumes a world through the seam, not through an import.

    The provider this module hands the handler satisfies the protocol
    ``contract`` publishes, so these arms are about the seam the server will
    actually bind across rather than about a shape invented here.
    """
    assert isinstance(_Worlds(None), contract.WorldProvider)
