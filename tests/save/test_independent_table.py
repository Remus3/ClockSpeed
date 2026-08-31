"""CS-829 - the SECOND expression of the record table, and the guards that keep it second.

WHY THIS MODULE EXISTS. ``tests/save/test_struct_interior.py`` grades a
denominator that is independent of the TAG READER and NOT of the RECORD TABLE:
both readings in that sweep iterate one ``objects.parse_body(...).records`` and
consume the same three fields, so a defect in the record table moves both and
reddens nothing. ``tests/save/independent_table.py`` reads the same grammar
without calling a single shipped reader, and this module is what forces that
independence to stay true and what grades the reading against the shipped one.

THE ASSERTIONS ARE ONE-SIDED AND THAT IS DELIBERATE. The reading is allowed to
DECLINE anything - a level whose two counts disagree, a body that stops reading -
and it is never allowed to INVENT. So the claim graded against the real library
is "no record this reading accepts is refused by the shipped walk", never the
converse, and the acceptance ratio is reported rather than asserted at 1.

SYNTHETIC FIRST AND SYNTHETIC MOSTLY. Every arm but one builds its bytes in the
process and runs on a machine with no game installed and no save library, which
is CLAUDE.md section 7. The one library arm SKIPS when nothing is reachable and
reports COUNTS ONLY - no path, no world name, no account id, no type path.

THE PAIR KEY ORDER IS A LIVE TRAP. ``objects.BODY_LAYOUT_BY_PAIR`` and
``synthetic.LEVELLED_LAYOUTS`` are both keyed ``(header_version, save_version)``;
``test_struct_interior._SaveShape.pair`` is ``(save_version, header_version)``,
the OPPOSITE order. Every pair in this module is (header, save) and is unpacked
under those names at every site rather than indexed.
"""

from __future__ import annotations

import ast
import dataclasses
import struct
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING, Final

import pytest

from clockspeed.save import chunks, header, objects
from tests.save import independent_table, reach_guard, synthetic, test_properties

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

# ---------------------------------------------------------------------------
# Fixture material
# ---------------------------------------------------------------------------

#: Every pair with a measured body layout, in declaration order. Taken from the
#: shipped table so a fifth pair is in scope here the day it is measured, rather
#: than the day somebody remembers to widen a literal.
MEASURED_PAIRS: Final = tuple(objects.BODY_LAYOUT_BY_PAIR)

#: The simplest measured layout: no package summary, no grid preamble, 4-byte
#: section sizes, no data-entry lead, no trailer, no component pre-word, no
#: level tail. It is the pair the hand-built bodies below are written in, so a
#: body assembled by hand stays short enough to read.
HAND_BUILT_PAIR: Final = (objects.HEADER_VERSION_10, 36)

#: The object-type discriminator, RE-TRANSCRIBED rather than imported. Importing
#: ``objects._KIND_BY_OBJECT_TYPE`` would put the kind decision back on the
#: shipped side of the seam, and the counter-example this round exists to catch
#: is a RELABEL of exactly that decision.
#: ``test_the_object_type_transcription_matches_the_shipped_discriminator_table``
#: is what stops the two drifting apart in silence.
OBJECT_TYPE_ACTOR: Final = 1
OBJECT_TYPE_COMPONENT: Final = 0

#: A discriminator with no measured record grammar. Any value outside the two
#: above serves; this one is far enough from both to be obviously deliberate.
_UNMEASURED_OBJECT_TYPE: Final = 7

#: Synthetic content. Nothing here resembles a real world, account or player.
_ACTOR_A: Final = synthetic.SyntheticObject(
    class_path="/Synthetic/Test.TestActorA_C",
    root_object="Persistent_Level",
    instance_name="Persistent_Level:PersistentLevel.TestActorA_0",
)
_ACTOR_B: Final = synthetic.SyntheticObject(
    class_path="/Synthetic/Test.TestActorB_C",
    root_object="Persistent_Level",
    instance_name="Persistent_Level:PersistentLevel.TestActorB_0",
)
_ACTOR_C: Final = synthetic.SyntheticObject(
    class_path="/Synthetic/Test.TestActorC_C",
    root_object="Persistent_Level",
    instance_name="Persistent_Level:PersistentLevel.TestActorC_0",
)
_COMPONENT_A: Final = synthetic.SyntheticComponent(
    class_path="/Synthetic/Test.TestComponentA_C",
    root_object="Persistent_Level",
    instance_name="Persistent_Level:PersistentLevel.TestComponentA_0",
)
_COMPONENT_B: Final = synthetic.SyntheticComponent(
    class_path="/Synthetic/Test.TestComponentB_C",
    root_object="Persistent_Level",
    instance_name="Persistent_Level:PersistentLevel.TestComponentB_0",
)

#: Distinct per level, so a returned length names the level it came from and a
#: reader that pairs the wrong section is visible in the lengths alone.
_PAYLOAD_SIZE_FIRST: Final = 24
_PAYLOAD_SIZE_SECOND: Final = 36
_PAYLOAD_SIZE_PERSISTENT: Final = 48


def _fixture_levels() -> tuple[tuple[synthetic.SyntheticLevel, ...], synthetic.SyntheticLevel]:
    """Two named levels and the persistent one, mixing both record kinds.

    Both kinds appear in one level and the kinds are NOT in a single run across
    the whole body, so a reading that lost the kind discriminator entirely could
    not reproduce the flag sequence by accident.

    Returns:
        The named levels in file order, and the trailing unnamed level.
    """
    named = (
        synthetic.SyntheticLevel(
            name="Level_First",
            objects=(_ACTOR_A, _ACTOR_B),
            components=(_COMPONENT_A,),
            payload_size=_PAYLOAD_SIZE_FIRST,
        ),
        synthetic.SyntheticLevel(
            name="Level_Second",
            objects=(_ACTOR_C,),
            payload_size=_PAYLOAD_SIZE_SECOND,
        ),
    )
    persistent = synthetic.SyntheticLevel(
        name=None,
        objects=(_ACTOR_A,),
        components=(_COMPONENT_B,),
        payload_size=_PAYLOAD_SIZE_PERSISTENT,
    )
    return named, persistent


def _fixture_body(header_version: int, save_version: int) -> bytes:
    """One whole synthetic body of a measured pair, length prefix included.

    Args:
        header_version: Half of the layout key, and the prefix width.
        save_version: The other half.

    Returns:
        The body exactly as ``chunks.decompress_body`` would hand one over.
    """
    named, persistent = _fixture_levels()
    body = synthetic.build_levelled_body(
        named, persistent, header_version=header_version, save_version=save_version
    )
    return synthetic.body_with_prefix(body, header_version)


def _expected_flags() -> tuple[bool, ...]:
    """The ``is_actor`` sequence the fixture's records must come back in.

    Derived from the fixture's own declaration - a level encodes its actors
    first and its components after them - so it cannot drift from the bytes.

    Returns:
        One flag per record, in file order.
    """
    named, persistent = _fixture_levels()
    flags: list[bool] = []
    for level in (*named, persistent):
        flags.extend([True] * len(level.objects))
        flags.extend([False] * len(level.components))
    return tuple(flags)


def _expected_lengths() -> tuple[int, ...]:
    """The payload length each fixture record must report, in file order.

    Returns:
        One length per record.
    """
    named, persistent = _fixture_levels()
    lengths: list[int] = []
    for level in (*named, persistent):
        lengths.extend([level.payload_size] * level.record_count)
    return tuple(lengths)


# ---------------------------------------------------------------------------
# HAND-BUILT BODIES
#
# A THIRD EXPRESSION, and the only one in this module that pins an ABSOLUTE
# offset. The synthetic corpus is a writer rather than a reader, so grading the
# reading against it is already a real check - but the corpus computes its own
# section sizes and its payloads are zero filler, so it cannot say where in the
# body a given payload landed. These bodies carry DISTINCTIVE payload bytes,
# and the expectation is stated as "where those bytes actually are", found with
# ``bytes.index`` over the assembled body. That shares nothing with either
# reader.
#
# They are written in the (10,36) grammar because it is the shortest: no
# package summary, no grid preamble, no data-entry lead, no trailer, no
# component pre-word, no level tail.
# ---------------------------------------------------------------------------


def _i32(value: int) -> bytes:
    """Pack one signed 32-bit little-endian integer.

    Args:
        value: The value.

    Returns:
        Four bytes.
    """
    return struct.pack("<i", value)


def _text(value: str) -> bytes:
    """Encode one length-prefixed ASCII string, count including the null.

    Args:
        value: ASCII text, or the empty string.

    Returns:
        The encoded string.
    """
    if not value:
        return _i32(0)
    raw = value.encode("ascii")
    return _i32(len(raw) + 1) + raw + b"\x00"


def _hand_actor(tag: str) -> bytes:
    """One actor record in the (10,36) grammar.

    Args:
        tag: A short synthetic discriminator for the three name fields.

    Returns:
        The record bytes.
    """
    return b"".join(
        [
            _i32(OBJECT_TYPE_ACTOR),
            _text(f"/Synthetic/Hand.Actor{tag}_C"),
            _text("Persistent_Level"),
            _text(f"Persistent_Level:PersistentLevel.Actor{tag}_0"),
            bytes(objects.BODY_LAYOUT_BY_PAIR[HAND_BUILT_PAIR].transform_delta),
            bytes(objects.TRANSFORM_BYTES),
            _i32(1),
        ]
    )


def _hand_component(tag: str) -> bytes:
    """One component record in the (10,36) grammar, which carries no pre-word.

    Args:
        tag: A short synthetic discriminator for the name fields.

    Returns:
        The record bytes.
    """
    return b"".join(
        [
            _i32(OBJECT_TYPE_COMPONENT),
            _text(f"/Synthetic/Hand.Component{tag}_C"),
            _text("Persistent_Level"),
            _text(f"Persistent_Level:PersistentLevel.Component{tag}_0"),
            _text("Persistent_Level:PersistentLevel.ActorP_0"),
        ]
    )


def _hand_level(
    name: str | None, records: Sequence[bytes], payloads: Sequence[bytes], *, declared: int | None
) -> bytes:
    """One whole level in the (10,36) grammar.

    Both section sizes are computed from the bytes they cover, so a fixture
    cannot declare a size that disagrees with its own content. ``declared`` is
    the one field allowed to lie, and it lies about the DATA ENTRY COUNT alone -
    which is the exact condition ``_attribute_payloads`` refuses to pair on and
    the only way a fixture can reach that branch.

    Args:
        name: The level name, or None for the persistent level.
        records: Encoded records, in file order.
        payloads: One payload per entry, in file order.
        declared: What the data section claims its entry count is, or None to
            declare the truth.

    Returns:
        The level bytes.
    """
    header_section = _i32(len(records)) + b"".join(records)
    entries = b"".join(_i32(len(payload)) + payload for payload in payloads)
    count = len(payloads) if declared is None else declared
    data_section = _i32(count) + entries

    out: list[bytes] = []
    if name is not None:
        out.append(_text(name))
    out.append(_i32(len(header_section)))
    out.append(header_section)
    out.append(_i32(len(data_section)))
    out.append(data_section)
    # LEVEL_TAIL_NONE on this pair, and second_collectables_named is True, so
    # every level - named or not - closes with one collectable list.
    out.append(_i32(0))
    return b"".join(out)


def _hand_body(named: Sequence[bytes], persistent: bytes) -> bytes:
    """Assemble a whole (10,36) body, length prefix included.

    Args:
        named: The named levels, already encoded.
        persistent: The trailing unnamed level, already encoded.

    Returns:
        The prefixed body.
    """
    body = _i32(len(named)) + b"".join(named) + persistent + _i32(0)
    # Header 10 carries a NARROW prefix. The reading steps over it rather than
    # trusting it, so the declared value is written honestly and is not the
    # thing under test.
    return _i32(len(body)) + body


def _locate(body: bytes, payload: bytes) -> int:
    """Where a distinctive payload actually sits in an assembled body.

    Args:
        body: The whole body.
        payload: Bytes written exactly once into it.

    Returns:
        The payload's first byte.
    """
    assert body.count(payload) == 1, (
        "the hand-built expectation is only exact while each payload occurs "
        f"once; this one occurs {body.count(payload)} times"
    )
    return body.index(payload)


# ---------------------------------------------------------------------------
# The DECLINE contract - None and () are different answers
# ---------------------------------------------------------------------------


def test_an_unmeasured_version_pair_declines_with_none() -> None:
    unmeasured = (objects.HEADER_VERSION_14, 99)
    assert unmeasured not in objects.BODY_LAYOUT_BY_PAIR, (
        "this pair has acquired a measured layout, so it can no longer stand "
        "for the decline; pick another"
    )
    found = independent_table.independent_records(
        b"", save_version=unmeasured[1], header_version=unmeasured[0]
    )
    assert found is None


def test_a_measured_pair_with_no_records_reads_to_an_empty_tuple() -> None:
    body = _hand_body((), _hand_level(None, (), (), declared=None))
    found = independent_table.independent_records(
        body, save_version=HAND_BUILT_PAIR[1], header_version=HAND_BUILT_PAIR[0]
    )
    assert found == ()


def test_a_decline_and_an_empty_reading_are_not_the_same_answer() -> None:
    """memory/an-empty-population-satisfies-every-zero.md, asserted rather than believed.

    None means "this reading has nothing to say about the pair". ``()`` means
    "the body was read and it declares no record". A caller that collapsed the
    two would take a whole-save refusal as a measured zero, which is the shape
    that satisfies every threshold in the sweep this table feeds.
    """
    declined = independent_table.independent_records(b"", save_version=99, header_version=99)
    empty = independent_table.independent_records(
        _hand_body((), _hand_level(None, (), (), declared=None)),
        save_version=HAND_BUILT_PAIR[1],
        header_version=HAND_BUILT_PAIR[0],
    )
    assert declined is None
    assert empty is not None
    assert len(empty) == 0


# ---------------------------------------------------------------------------
# The reading itself, against synthetic bodies of every measured pair
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("pair", MEASURED_PAIRS)
def test_every_measured_pair_returns_one_record_per_payload_in_file_order(
    pair: tuple[int, int],
) -> None:
    header_version, save_version = pair
    body = _fixture_body(header_version, save_version)
    found = independent_table.independent_records(
        body, save_version=save_version, header_version=header_version
    )
    assert found is not None
    assert tuple(record.is_actor for record in found) == _expected_flags()
    assert tuple(record.body_length for record in found) == _expected_lengths()


@pytest.mark.parametrize("pair", MEASURED_PAIRS)
def test_every_extent_starts_one_length_prefix_past_its_own_declared_length(
    pair: tuple[int, int],
) -> None:
    """The offset pin that needs no absolute arithmetic.

    A payload's four preceding bytes ARE its declared length in every measured
    layout - the data-entry lead, where a pair has one, sits before the prefix
    and not between it and the payload. So a reading off by even one byte
    reports an offset whose preceding word is not the length it also reports.
    """
    header_version, save_version = pair
    body = _fixture_body(header_version, save_version)
    found = independent_table.independent_records(
        body, save_version=save_version, header_version=header_version
    )
    assert found is not None
    assert found, "an empty reading would satisfy the loop below vacuously"
    misplaced = sum(
        body[record.body_offset - objects.INT32_SIZE : record.body_offset]
        != struct.pack("<i", record.body_length)
        for record in found
    )
    assert misplaced == 0, f"{misplaced} of {len(found)} extents do not follow their own prefix"


@pytest.mark.parametrize("pair", MEASURED_PAIRS)
def test_the_reading_agrees_with_the_shipped_table_on_a_synthetic_body(
    pair: tuple[int, int],
) -> None:
    """The correctness arm, and the one that needs no game installed.

    Kind, offset and length are exactly the three fields
    ``test_struct_interior._sweep_one_record`` consumes, so agreeing on them is
    agreeing on everything the denominator is made of.
    """
    header_version, save_version = pair
    body = _fixture_body(header_version, save_version)
    table = objects.parse_body(body, save_version=save_version, header_version=header_version)
    shipped = tuple(
        (record.kind == objects.KIND_ACTOR, record.body_offset, record.body_length)
        for record in table.records
    )
    found = independent_table.independent_records(
        body, save_version=save_version, header_version=header_version
    )
    assert found is not None
    mine = tuple((record.is_actor, record.body_offset, record.body_length) for record in found)
    assert shipped, "the fixture declares no record, so this comparison would be vacuous"
    assert mine == shipped


# ---------------------------------------------------------------------------
# The hand-built arms - absolute offsets, and the pairing refusal
# ---------------------------------------------------------------------------


def _well_formed_hand_built() -> tuple[bytes, tuple[_Triple, ...]]:
    """One well-formed hand-built body and what its own bytes say is in it.

    The expectation is NOT computed from the assembly arithmetic - it is found
    with ``bytes.index`` over the finished body, which shares nothing with
    either reader or with the encoder's own offset bookkeeping.

    Returns:
        The prefixed body, and one triple per record in file order.
    """
    first = b"HAND-PAYLOAD-FIRST-0"
    second = b"HAND-PAYLOAD-SECOND"
    third = b"HAND-PAYLOAD-THIRD-XY"
    named = _hand_level(
        "Level_Hand",
        (_hand_actor("H"), _hand_component("H")),
        (first, second),
        declared=None,
    )
    persistent = _hand_level(None, (_hand_actor("P"),), (third,), declared=None)
    body = _hand_body((named,), persistent)
    return body, (
        (True, _locate(body, first), len(first)),
        (False, _locate(body, second), len(second)),
        (True, _locate(body, third), len(third)),
    )


def test_the_hand_built_body_yields_the_exact_offsets_its_bytes_declare() -> None:
    body, expected = _well_formed_hand_built()
    found = independent_table.independent_records(
        body, save_version=HAND_BUILT_PAIR[1], header_version=HAND_BUILT_PAIR[0]
    )
    assert found is not None
    assert (
        tuple((record.is_actor, record.body_offset, record.body_length) for record in found)
        == expected
    )


def test_the_shipped_walk_reads_the_hand_built_body_the_same_way() -> None:
    """THE ENCODER IS GRADED TOO, and by something that is not this module.

    Without this arm the hand-built case is one author's encoder read by the
    same author's reader: they could be wrong the same way and the ``bytes.index``
    expectation would not notice, because it locates the payload in whatever
    grammar the encoder happened to write. Putting the shipped walk over the
    same bytes is what makes the hand-built grammar a claim about the FORMAT
    rather than about this file.
    """
    body, expected = _well_formed_hand_built()
    table = objects.parse_body(
        body, save_version=HAND_BUILT_PAIR[1], header_version=HAND_BUILT_PAIR[0]
    )
    assert (
        tuple(
            (record.kind == objects.KIND_ACTOR, record.body_offset, record.body_length)
            for record in table.records
        )
        == expected
    )


def test_a_level_whose_entry_count_disagrees_with_its_record_count_is_not_paired() -> None:
    """``objects._attribute_payloads``'s count guard, re-expressed and refused the same way.

    Attribution is only DEFINED when the two counts agree. A walker that zipped
    the shorter list would pair some records with another record's payload and
    report it as fact. The level is DROPPED here rather than emitted with a zero
    extent, because a zero extent is an invented one.
    """
    kept = b"HAND-PAYLOAD-KEPT-01"
    dropped = b"HAND-PAYLOAD-DROPPED"
    # Two records, ONE entry. Both section sizes still cover their own content,
    # so the walk closes and only the pairing is impossible.
    named = _hand_level(
        "Level_Disagree",
        (_hand_actor("D"), _hand_component("D")),
        (dropped,),
        declared=None,
    )
    persistent = _hand_level(None, (_hand_actor("K"),), (kept,), declared=None)
    body = _hand_body((named,), persistent)

    found = independent_table.independent_records(
        body, save_version=HAND_BUILT_PAIR[1], header_version=HAND_BUILT_PAIR[0]
    )
    assert found is not None
    assert tuple((record.is_actor, record.body_offset, record.body_length) for record in found) == (
        (True, _locate(body, kept), len(kept)),
    )


def test_a_declared_entry_count_above_the_truth_is_refused_rather_than_padded() -> None:
    """The other direction of the same disagreement.

    A section whose declared count exceeds the entries it holds must not be
    completed with invented extents, and it must not silently truncate to what
    fits. Here the declared count is deliberately larger than the payload list,
    which desynchronises the data section against its own declared SIZE.
    """
    payload = b"HAND-PAYLOAD-OVERDECLARED"
    persistent = _hand_level(None, (_hand_actor("O"),), (payload,), declared=2)
    body = _hand_body((), persistent)
    found = independent_table.independent_records(
        body, save_version=HAND_BUILT_PAIR[1], header_version=HAND_BUILT_PAIR[0]
    )
    assert found is None


# ---------------------------------------------------------------------------
# Refusal, and the one-sidedness that makes the arm honest
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("pair", MEASURED_PAIRS)
@pytest.mark.parametrize("cut", [1, 3, 9, 41, 128])
def test_a_truncated_body_declines_rather_than_inventing_a_record(
    pair: tuple[int, int], cut: int
) -> None:
    header_version, save_version = pair
    body = _fixture_body(header_version, save_version)
    assert cut < len(body), "the truncation has to leave a body to read"
    found = independent_table.independent_records(
        body[:-cut], save_version=save_version, header_version=header_version
    )
    assert found is None


def test_an_impossible_object_type_declines_rather_than_guessing_a_kind() -> None:
    """A discriminator outside the measured two is an unknown GRAMMAR, not an unknown class.

    Non-negotiable 7 flags unknown CONTENT and skips it. A discriminator decides
    how many bytes the record occupies, so guessing one desynchronises the walk
    and everything after it is invention.

    ONE RECORD'S DISCRIMINATOR IS REWRITTEN AND NOT EVERY MATCHING WORD IN THE
    BODY. A blanket replace would also hit a transform value, a section size or
    a length prefix, and the walk would then decline for a reason that has
    nothing to do with the discriminator - an arm that passes for the wrong
    reason is an arm about nothing.
    """
    record = _hand_actor("X")
    payload = b"HAND-PAYLOAD-DISCRIMINATOR"
    body = _hand_body((), _hand_level(None, (record,), (payload,), declared=None))
    intact = independent_table.independent_records(
        body, save_version=HAND_BUILT_PAIR[1], header_version=HAND_BUILT_PAIR[0]
    )
    assert intact is not None, "the unpatched body must read, or the patch proves nothing"

    at = _locate(body, record)
    patched = bytearray(body)
    patched[at : at + objects.INT32_SIZE] = _i32(_UNMEASURED_OBJECT_TYPE)
    assert bytes(patched) != body, "the patch changed nothing, so this arm is vacuous"
    found = independent_table.independent_records(
        bytes(patched), save_version=HAND_BUILT_PAIR[1], header_version=HAND_BUILT_PAIR[0]
    )
    assert found is None


# ---------------------------------------------------------------------------
# The seam guards - what keeps this reading SECOND
# ---------------------------------------------------------------------------


def _module_source(path: Path) -> ast.Module:
    """Parse one of this repo's own tracked source files.

    Declared EXEMPT rather than graded: the paths it takes are module files
    inside the project tree, never a save path and never anything under an
    account directory.

    Args:
        path: The module file.

    Returns:
        Its parsed tree.
    """
    return ast.parse(path.read_text(encoding="utf-8"))


#: AST fields holding a type annotation. Skipped by the attribute scan below:
#: ``from __future__ import annotations`` makes every annotation a STRING at
#: runtime, so a name mentioned only there is never evaluated and can execute
#: nothing. The second reading annotates a parameter ``objects.BodyLayout``,
#: which is a class and therefore callable, and counting that as a reader would
#: force the module to hide its own types.
_ANNOTATION_FIELDS: Final = frozenset(("annotation", "returns"))


def _shipped_attribute_names() -> frozenset[str]:
    """Every ``objects.<name>`` the second reading EVALUATES.

    Returns:
        The attribute names outside annotation position, empty when it
        mentions none.
    """
    holder = objects.__name__.rpartition(".")[2]
    found: set[str] = set()
    pending: list[ast.AST] = [_module_source(Path(independent_table.__file__))]
    while pending:
        node = pending.pop()
        if (
            isinstance(node, ast.Attribute)
            and isinstance(node.value, ast.Name)
            and node.value.id == holder
        ):
            found.add(node.attr)
        for field, value in ast.iter_fields(node):
            if field in _ANNOTATION_FIELDS:
                continue
            items = value if isinstance(value, list) else [value]
            pending.extend(item for item in items if isinstance(item, ast.AST))
    return frozenset(found)


def _shipped_call_names() -> frozenset[str]:
    """Every ``objects.<name>(...)`` the second reading CALLS.

    Returns:
        The called attribute names, empty when it calls none - which is the
        only value this seam permits.
    """
    tree = _module_source(Path(independent_table.__file__))
    return frozenset(
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == objects.__name__.rpartition(".")[2]
    )


def test_the_second_reading_calls_no_function_of_the_shipped_module() -> None:
    """THE SEAM, forced statically rather than trusted.

    Constants yes, readers no - the same line ``_independent_tag_walk`` already
    draws in ``tests/save/test_struct_interior.py``. A reading that called one
    shipped reader would move with it under a planted defect, which is precisely
    the failure this whole item exists to close.
    """
    mentioned = _shipped_attribute_names()
    assert mentioned, (
        "the second reading mentions nothing from the shipped module, so this "
        "guard is vacuous - either it stopped importing it or the import was "
        "rebound under another name"
    )
    assert _shipped_call_names() == frozenset()


def test_every_shipped_name_the_second_reading_uses_is_data_and_not_a_reader() -> None:
    """The runtime half of the same seam, which the AST half cannot reach.

    An indirection - binding ``objects.parse_body`` to a local and calling the
    local - is invisible to a scan for ``objects.<name>(...)``. Asserting that
    every name it touches resolves to a NON-CALLABLE object closes that: a
    reader cannot be smuggled through a name that is not callable.
    """
    mentioned = sorted(_shipped_attribute_names())
    assert mentioned, "no shipped name is used, so this guard is vacuous"
    missing = [name for name in mentioned if not hasattr(objects, name)]
    assert missing == [], f"{len(missing)} names do not exist in the shipped module"
    callables = [name for name in mentioned if callable(getattr(objects, name))]
    assert callables == [], (
        f"{len(callables)} of {len(mentioned)} shipped names the second reading "
        "touches are callable, so it can execute shipped logic"
    )


def test_the_second_reading_imports_the_shipped_module_only_as_a_module() -> None:
    """``from clockspeed.save.objects import parse_body`` would defeat both guards above.

    So the import FORM is pinned too: the module may be imported, its members
    may not.
    """
    tree = _module_source(Path(independent_table.__file__))
    from_imports = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    }
    assert "clockspeed.save" in from_imports, (
        "the second reading no longer imports the shipped module by package, so "
        "this guard cannot see how it reaches it"
    )
    reached_into = sorted(name for name in from_imports if name.startswith("clockspeed.save."))
    assert reached_into == [], f"{len(reached_into)} imports reach INTO a shipped module"


def test_the_object_type_transcription_matches_the_shipped_discriminator_table() -> None:
    """The re-transcription's anti-drift control.

    The kind decision is deliberately NOT imported - see the constants above -
    so the two spellings could drift apart in silence. This is what stops that,
    and it grades DATA against DATA rather than a reading against a reading.
    """
    shipped = objects._KIND_BY_OBJECT_TYPE  # noqa: SLF001
    assert shipped[OBJECT_TYPE_ACTOR] == objects.KIND_ACTOR
    assert shipped[OBJECT_TYPE_COMPONENT] == objects.KIND_COMPONENT
    assert sorted(shipped) == sorted((OBJECT_TYPE_ACTOR, OBJECT_TYPE_COMPONENT))


def test_an_independent_record_can_carry_no_string_at_all() -> None:
    """Non-negotiable 12, enforced on the SHAPE rather than on each call site.

    A type path, an instance name, a root object and a parent path are all world
    content. The record holds three fields, all of them numbers, so there is no
    repr, no assertion message and no debug dump that can render one.
    """
    fields = dataclasses.fields(independent_table.IndependentRecord)
    assert tuple(field.name for field in fields) == ("is_actor", "body_offset", "body_length")
    assert sorted({str(field.type) for field in fields}) == ["bool", "int"]


# ---------------------------------------------------------------------------
# The library cross-check - SKIPPED where there is no library, COUNTS ONLY out
# ---------------------------------------------------------------------------


#: What both readings are reduced to before they are compared: the kind flag,
#: the payload's first byte and its declared length. A boolean and two numbers,
#: so a set difference over them can render no world content whatever it holds.
_Triple = tuple[bool, int, int]


@dataclasses.dataclass(frozen=True)
class _LibraryAgreement:
    """What one sweep of the real library measured. COUNTS ONLY.

    Attributes:
        saves: How many save files were reachable and read.
        bodies: How many decompressed to a body this sweep could offer both
            readings.
        shipped_records: Records the shipped walk accepted, over every body.
        independent_records: Records the second reading accepted, over the same.
        strangers: Records the second reading accepted that the shipped walk
            did NOT - a DEFECT in the second reading, never a finding about the
            shipped one.
        missing: Records the shipped walk accepted that the second reading did
            NOT. THE ANTI-MONOTONE DIRECTION, and the reason it is counted:
            CS-829's denominator rests on the second reading, so a reading that
            quietly accepts LESS shrinks the population every equality in
            ``test_struct_interior.py`` stands on, and that equality then holds
            over a smaller world instead of going red. That is the exact shape
            which refuted this item four times. Declining is cheap to do by
            accident and free to get away with under a subset claim.
        ordered_bodies: Bodies whose two readings agree ELEMENT FOR ELEMENT IN
            FILE ORDER. A set comparison cannot see order, and the re-seated
            denominator indexes this tuple positionally, so order is a load
            bearing property rather than a nicety.
        compared_bodies: Bodies where an order comparison was DEFINED - both
            readings returned the same number of records. The denominator
            ``ordered_bodies`` is graded against, so a run where every body
            disagreed on length cannot pass by leaving both at zero.
    """

    saves: int
    bodies: int
    shipped_records: int
    independent_records: int
    strangers: int
    missing: int
    ordered_bodies: int
    compared_bodies: int


def _shipped_triples(body: bytes, *, save_version: int, header_version: int) -> tuple[_Triple, ...]:
    """What the SHIPPED walk says one body's records are, as kind, offset and length.

    A REFUSED SAVE IS THE EMPTY SET AND NOT A SKIP. Everything the second
    reading accepts on a body the shipped walk refuses is then a stranger, which
    is a verdict the sweep has to be able to reach - skipping such a save would
    hide exactly the defect the count exists to catch.

    Args:
        body: The decompressed body. Held in this frame and never reported.
        save_version: From the header.
        header_version: From the header.

    Returns:
        One triple per record the shipped walk accepted, empty when it refused
        the body outright.
    """
    try:
        table = objects.parse_body(body, save_version=save_version, header_version=header_version)
    except (Exception, SystemExit):
        # `SystemExit` is named because it is NOT an `Exception`. NOTHING is
        # reported about the failure, not even a type name - the exception's own
        # message and frames both reach the save's bytes.
        return ()
    return tuple(
        (record.kind == objects.KIND_ACTOR, record.body_offset, record.body_length)
        for record in table.records
    )


def _sweep_the_library() -> _LibraryAgreement | None:
    """Read every save on this machine ONCE and reduce it to five integers.

    Contained as ``test_properties._sweep_payload_tags`` is: every step wrapped,
    every failure reduced to a COUNT inside this helper before it can reach a
    frame anyone renders. Not even a type name leaves, because the two channels
    that could carry one here - the discovery call and the read - both hold an
    absolute path under an account directory.

    EACH SAVE IS READ ONCE AND MEASURED TWICE. The operator plays this game
    while a session runs, so re-reading the library between the two readings
    would race a real autosave and the disagreement would be the race rather
    than the readers.

    Returns:
        The sweep, or None when no save library is reachable.
    """
    saves = test_properties._library_save_paths()  # noqa: SLF001
    if not saves:
        return None

    read = 0
    bodies = 0
    shipped_total = 0
    independent_total = 0
    strangers = 0
    missing = 0
    ordered = 0
    compared = 0
    for path in saves:
        opened: tuple[bytes, int, int] | None = None
        try:
            data = path.read_bytes()
            parsed = header.parse_header(data)
            opened = (
                chunks.decompress_body(
                    data, parsed.body_offset, header_version=parsed.header_version
                ).payload,
                parsed.save_version,
                parsed.header_version,
            )
        except (Exception, SystemExit):
            # `SystemExit` is named because it is NOT an `Exception`, and it
            # unwinds carrying the save path exactly as any other type would.
            # The sentinel carries the outcome instead of the control flow, so
            # this handler reports nothing and decides nothing.
            opened = None
        if opened is not None:
            read += 1
            body, save_version, header_version = opened
            shipped = _shipped_triples(
                body, save_version=save_version, header_version=header_version
            )
            found = independent_table.independent_records(
                body, save_version=save_version, header_version=header_version
            )
            if found is not None:
                bodies += 1
                mine = tuple(
                    (record.is_actor, record.body_offset, record.body_length) for record in found
                )
                shipped_total += len(shipped)
                independent_total += len(mine)
                strangers += len(frozenset(mine) - frozenset(shipped))
                missing += len(frozenset(shipped) - frozenset(mine))
                # ORDER IS COMPARED ONLY WHERE IT IS DEFINED. Two readings of
                # different lengths have no positional comparison, and zipping
                # the shorter one would call a truncated agreement an agreement
                # - the same refusal ``_attribute_payloads`` makes about pairing
                # a record with another record's payload.
                if len(shipped) == len(mine):
                    compared += 1
                    ordered += shipped == mine
    return _LibraryAgreement(
        saves=read,
        bodies=bodies,
        shipped_records=shipped_total,
        independent_records=independent_total,
        strangers=strangers,
        missing=missing,
        ordered_bodies=ordered,
        compared_bodies=compared,
    )


def test_the_second_reading_accepts_nothing_the_shipped_walk_refuses() -> None:
    """The one library-backed arm. SKIPS where there is no library; COUNTS ONLY out.

    ONE-SIDED BY CONSTRUCTION. Declining a record is always allowed and is not
    measured here as a failure - the acceptance ratio is reported through the
    message of the liveness assertion instead. Accepting one the shipped walk
    refuses is the defect, and it is the only thing asserted at zero.
    """
    swept = _sweep_the_library()
    if swept is None:
        pytest.skip("no save library is reachable on this machine, so there is nothing to sweep")
    # BOUND TO SCALARS BEFORE ASSERTING. pytest rewrites the asserted EXPRESSION
    # and renders it independently of the message, so an aggregate in the
    # expression is an echo path whatever the message says.
    strangers = swept.strangers
    accepted = swept.independent_records
    shipped = swept.shipped_records
    assert shipped > 0, (
        f"{swept.saves} saves read and {swept.bodies} bodies offered, but the "
        "shipped walk accepted no record at all, so this comparison is vacuous"
    )
    assert accepted > 0, (
        f"{swept.saves} saves read and the second reading accepted no record, so "
        "the subset claim below holds vacuously"
    )
    # THE ANTI-MONOTONE DIRECTION, ASSERTED AS AN EQUALITY AND NOT AS A FLOOR.
    # CS-829's acceptance says the population is graded by an equality "and not
    # as a floor", and `accepted > 0` above is exactly a floor - it is satisfied
    # by a reading that has decayed to one record. That matters more here than
    # anywhere else in this module: the re-seated denominator in
    # `test_struct_interior.py` rests on THIS reading, so a reading that quietly
    # accepts less shrinks the population every equality there stands on, and
    # those equalities then hold over a smaller world rather than going red.
    # Four refutations of this item were that shape. MEASURED at the merge: 20
    # of 20 bodies, 148668 records both sides, missing 0.
    missing = swept.missing
    assert missing == 0, (
        f"the shipped walk accepted {missing} records of {shipped} that the second "
        f"reading did not, while the second reading accepted {accepted}. A SUBSET "
        "CLAIM CANNOT SEE THIS: declining is always permitted one record at a time, "
        "and a reading that declines its way down still satisfies `strangers == 0` "
        "and any floor above zero. This is an equality because the denominator "
        "CS-829 rests on is this reading, and a denominator that shrinks quietly is "
        "the anti-monotone hole the item exists to close"
    )
    ordered = swept.ordered_bodies
    compared = swept.compared_bodies
    assert compared > 0, (
        f"{swept.bodies} bodies were offered to both readings and not one produced "
        "the same NUMBER of records under each, so no positional comparison was "
        "defined anywhere and the order claim below would hold vacuously"
    )
    assert ordered == compared, (
        f"{ordered} of {compared} comparable bodies have the two readings agreeing "
        "element for element in file order. A SET COMPARISON CANNOT SEE ORDER, and "
        "the re-seated denominator indexes this tuple POSITIONALLY - the k-th "
        "extent belongs to the k-th record, which is what `_attribute_payloads` "
        "measures and refuses to guess at. Two readings holding the same records in "
        "a different order would pair every site with the wrong record's payload "
        "and report it as fact"
    )
    assert strangers == 0, (
        f"{strangers} of {accepted} records the second reading accepted are "
        f"refused by the shipped walk, against {shipped} it accepts. THE COUNT "
        "ALONE DOES NOT SAY WHICH READING IS WRONG - on an unmodified tree it is "
        "a defect here and never a finding about the shipped walk, but the whole "
        "point of a second reading is that a defect planted in the shipped record "
        "table separates the two and lands here. Check what changed before "
        "deciding which side to repair"
    )


# ---------------------------------------------------------------------------
# Reach declarations - graded by the package-wide guard in test_reach_guard.py
# ---------------------------------------------------------------------------

#: Helpers that reach the real save library, name to why.
_GRADED_LIBRARY_REACH: Final = MappingProxyType(
    {_sweep_the_library.__name__: reach_guard.REACH_READS_THE_LIBRARY}
)

#: Touches a primitive WITHOUT consuming a real save path, name to why. EMPTY,
#: and that is a measurement rather than an omission. The one other primitive in
#: this module is :func:`_module_source`'s ``read_text``, and ``read_text`` is
#: excluded from the reach set by ``reach_guard._NOT_LIBRARY_REACH`` - it flags
#: repo-source reads, which is exactly what that helper does. An entry for it
#: here is an exemption describing a function the guard does not consider
#: reaching, and the guard says so by name.
_EXEMPT_LIBRARY_REACH: Final[Mapping[str, str]] = MappingProxyType({})
