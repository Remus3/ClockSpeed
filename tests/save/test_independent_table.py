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
from itertools import zip_longest
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Final

import pytest

from clockspeed.save import chunks, header, objects
from tests.save import independent_table, reach_guard, synthetic, test_properties

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping, Sequence

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
#: reader that pairs the wrong section is visible in the lengths alone. Each is
#: a BASE that a per-case nonce is added to, so the three stay distinct from one
#: another while a dynamic case's body and its declared lengths both differ from
#: every other case's - see :func:`_case_nonce` for why that is load bearing.
_PAYLOAD_SIZE_FIRST: Final = 24
_PAYLOAD_SIZE_SECOND: Final = 36
_PAYLOAD_SIZE_PERSISTENT: Final = 48

#: How far each truncation arm cuts the fixture body back. Named rather than
#: written into the parametrize decorator alone, so
#: :func:`_bodies_the_other_arms_read` can enumerate the truncations that arm
#: reads instead of restating them - a second literal is a literal that drifts.
_TRUNCATIONS: Final = (1, 3, 9, 41, 128)


def _fixture_levels(
    nonce: int = 0,
) -> tuple[tuple[synthetic.SyntheticLevel, ...], synthetic.SyntheticLevel]:
    """Two named levels and the persistent one, mixing both record kinds.

    Both kinds appear in one level and the kinds are NOT in a single run across
    the whole body, so a reading that lost the kind discriminator entirely could
    not reproduce the flag sequence by accident.

    Args:
        nonce: Added to EVERY payload size. It moves the body's bytes and the
            extents the reading must report at the same time, which is the
            property :func:`_case_nonce` needs and a nonce buried in stepped-over
            filler would not have. Zero is the shape every arm outside the
            dynamic section reads.

    Returns:
        The named levels in file order, and the trailing unnamed level.
    """
    named = (
        synthetic.SyntheticLevel(
            name="Level_First",
            objects=(_ACTOR_A, _ACTOR_B),
            components=(_COMPONENT_A,),
            payload_size=_PAYLOAD_SIZE_FIRST + nonce,
        ),
        synthetic.SyntheticLevel(
            name="Level_Second",
            objects=(_ACTOR_C,),
            payload_size=_PAYLOAD_SIZE_SECOND + nonce,
        ),
    )
    persistent = synthetic.SyntheticLevel(
        name=None,
        objects=(_ACTOR_A,),
        components=(_COMPONENT_B,),
        payload_size=_PAYLOAD_SIZE_PERSISTENT + nonce,
    )
    return named, persistent


def _fixture_body(header_version: int, save_version: int, nonce: int = 0) -> bytes:
    """One whole synthetic body of a measured pair, length prefix included.

    Args:
        header_version: Half of the layout key, and the prefix width.
        save_version: The other half.
        nonce: Passed to :func:`_fixture_levels`. Distinct nonces give distinct
            bodies, which is what makes a dynamic case's body one no earlier
            call in the process has read.

    Returns:
        The body exactly as ``chunks.decompress_body`` would hand one over.
    """
    named, persistent = _fixture_levels(nonce)
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


def _expected_lengths(nonce: int = 0) -> tuple[int, ...]:
    """The payload length each fixture record must report, in file order.

    Args:
        nonce: The case's nonce, as :func:`_fixture_levels` takes it. The
            lengths MOVE with it, which is what defeats a cache keyed on the
            version pair alone rather than on the body.

    Returns:
        One length per record.
    """
    named, persistent = _fixture_levels(nonce)
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
# THE ONE-OFF HAND-BUILT BODIES, each built by a NAMED helper rather than
# inline in the arm that reads it.
#
# They were inline until CS-866. The reason they are not is
# :func:`_bodies_the_other_arms_read`: the dynamic section's freshness claim is
# that no dynamic case reads a body any other arm reads, and a body assembled
# inside an arm's own frame cannot be enumerated by anything. Extracting them
# is what turns that claim from an arrangement into a measurement. NO ARM'S
# ASSERTIONS MOVED with them - only where the bytes are assembled did.
# ---------------------------------------------------------------------------


def _empty_hand_built() -> bytes:
    """A body carrying exactly one level and no record at all.

    Returns:
        The prefixed body.
    """
    return _hand_body((), _hand_level(None, (), (), declared=None))


def _count_disagreeing_hand_built() -> tuple[bytes, bytes]:
    """A body whose first level declares two records and one payload.

    Both section sizes still cover their own content, so the walk closes and
    only the PAIRING is impossible.

    Returns:
        The prefixed body, and the payload of the one record that survives.
    """
    kept = b"HAND-PAYLOAD-KEPT-01"
    dropped = b"HAND-PAYLOAD-DROPPED"
    named = _hand_level(
        "Level_Disagree",
        (_hand_actor("D"), _hand_component("D")),
        (dropped,),
        declared=None,
    )
    persistent = _hand_level(None, (_hand_actor("K"),), (kept,), declared=None)
    return _hand_body((named,), persistent), kept


def _over_declared_hand_built() -> bytes:
    """A body whose data section declares more entries than it holds.

    The declared count is deliberately larger than the payload list, which
    desynchronises the data section against its own declared SIZE.

    Returns:
        The prefixed body.
    """
    payload = b"HAND-PAYLOAD-OVERDECLARED"
    return _hand_body((), _hand_level(None, (_hand_actor("O"),), (payload,), declared=2))


def _unmeasured_discriminator_hand_built() -> tuple[bytes, bytes]:
    """A readable body, and the same body with ONE discriminator rewritten.

    ONE RECORD'S DISCRIMINATOR IS REWRITTEN AND NOT EVERY MATCHING WORD IN THE
    BODY. A blanket replace would also hit a transform value, a section size or
    a length prefix, and the walk would then decline for a reason that has
    nothing to do with the discriminator.

    Returns:
        The intact body, and the patched one.
    """
    record = _hand_actor("X")
    payload = b"HAND-PAYLOAD-DISCRIMINATOR"
    body = _hand_body((), _hand_level(None, (record,), (payload,), declared=None))
    at = _locate(body, record)
    patched = bytearray(body)
    patched[at : at + objects.INT32_SIZE] = _i32(_UNMEASURED_OBJECT_TYPE)
    return body, bytes(patched)


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
    body = _empty_hand_built()
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
        _empty_hand_built(),
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


def _hand_payload(base: bytes, nonce: int) -> bytes:
    """One distinctive hand-built payload, WIDENED by the case's nonce.

    The three bases below have three different lengths and the same widening is
    applied to each, so the widened three stay distinct from one another exactly
    as the bases are. The widened length is strictly increasing in the nonce, so
    two cases can no more share a length than they can share a body.

    Args:
        base: The distinctive literal, unique to one payload slot.
        nonce: How many filler bytes to append. Zero returns the base
            unchanged, which is what every arm outside the dynamic section
            reads.

    Returns:
        The payload bytes.
    """
    return base + b"." * nonce


def _well_formed_hand_built(nonce: int = 0) -> tuple[bytes, tuple[_Triple, ...]]:
    """One well-formed hand-built body and what its own bytes say is in it.

    The expectation is NOT computed from the assembly arithmetic - it is found
    with ``bytes.index`` over the finished body, which shares nothing with
    either reader or with the encoder's own offset bookkeeping. IT FOLLOWS THE
    NONCE FOR FREE, because a widened payload is located and measured in the
    finished body rather than predicted from a literal.

    Args:
        nonce: Widens all three payloads, which moves both the body and the
            offsets and lengths the reading must report.

    Returns:
        The prefixed body, and one triple per record in file order.
    """
    first = _hand_payload(b"HAND-PAYLOAD-FIRST-0", nonce)
    second = _hand_payload(b"HAND-PAYLOAD-SECOND", nonce)
    third = _hand_payload(b"HAND-PAYLOAD-THIRD-XY", nonce)
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
    # Two records, ONE entry. Both section sizes still cover their own content,
    # so the walk closes and only the pairing is impossible.
    body, kept = _count_disagreeing_hand_built()

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
    body = _over_declared_hand_built()
    found = independent_table.independent_records(
        body, save_version=HAND_BUILT_PAIR[1], header_version=HAND_BUILT_PAIR[0]
    )
    assert found is None


# ---------------------------------------------------------------------------
# Refusal, and the one-sidedness that makes the arm honest
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("pair", MEASURED_PAIRS)
@pytest.mark.parametrize("cut", _TRUNCATIONS)
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
    body, patched = _unmeasured_discriminator_hand_built()
    intact = independent_table.independent_records(
        body, save_version=HAND_BUILT_PAIR[1], header_version=HAND_BUILT_PAIR[0]
    )
    assert intact is not None, "the unpatched body must read, or the patch proves nothing"

    assert patched != body, "the patch changed nothing, so this arm is vacuous"
    found = independent_table.independent_records(
        patched, save_version=HAND_BUILT_PAIR[1], header_version=HAND_BUILT_PAIR[0]
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
    so the spellings could drift apart in silence. This is what stops that, and
    it grades DATA against DATA rather than a reading against a reading.

    THERE ARE THREE COPIES, NOT TWO, AND THIS ARM USED TO GRADE THE WRONG ONE.
    The shipped table, the READING's own pair in
    :mod:`tests.save.independent_table`, and this module's fixture pair. Only
    the reading's pair decides what the second reading does, and this arm named
    itself their guard while comparing the FIXTURE's pair against the shipped
    table - so flipping the reading's own constants left it green. Measured
    twice, independently, by an adjudicator and by an adversary: the drifted
    reading returned None where the clean one returned records, and this arm
    passed. The reading's pair is graded FIRST below, and the fixture's pair is
    then pinned to the reading's, so no copy is left ungraded.
    """
    shipped = objects._KIND_BY_OBJECT_TYPE  # noqa: SLF001
    # THE CONSTANTS THE SECOND READING ACTUALLY EVALUATES. Read off the module
    # rather than imported at the top of this file, so no local binding can
    # stand in for them.
    reading_actor = independent_table._OBJECT_TYPE_ACTOR  # noqa: SLF001
    reading_component = independent_table._OBJECT_TYPE_COMPONENT  # noqa: SLF001
    # MEMBERSHIP FIRST, SO A DRIFTED VALUE FAILS WITH A MESSAGE. Indexing
    # straight into the shipped mapping raises `KeyError` on exactly the drift
    # this arm exists to catch, and a `KeyError` renders no explanation - the
    # arm reddens while saying nothing about why. The discriminators are
    # integers, so nothing here can render save content.
    assert sorted(shipped) == sorted((reading_actor, reading_component)), (
        "the second reading's object-type discriminators are not the key set of the "
        "shipped table, so at least one of them names no record kind at all"
    )
    assert shipped[reading_actor] == objects.KIND_ACTOR
    assert shipped[reading_component] == objects.KIND_COMPONENT
    # AND THE FIXTURE'S COPY IS PINNED TO THE READING'S. Without this the two
    # could drift apart and every synthetic body in this file would be built
    # with a discriminator the reading does not recognise, which reads as the
    # reading being broken rather than as the fixture being wrong.
    assert (reading_actor, reading_component) == (OBJECT_TYPE_ACTOR, OBJECT_TYPE_COMPONENT)


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
        failures: One TYPE NAME per save whose read, decompression or reading
            raised. A class name is not save content. It exists because the
            two reading calls used to sit OUTSIDE the handler with the body
            live in the frame, so an exception rendered save bytes into a
            traceback; the assertion that this is empty is what stops that
            regressing quietly to a swallowed count.
    """

    saves: int
    bodies: int
    shipped_records: int
    independent_records: int
    strangers: int
    missing: int
    ordered_bodies: int
    compared_bodies: int
    failures: tuple[str, ...]


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
    failures: list[str] = []
    for path in saves:
        # EVERY STEP THAT TOUCHES SAVE BYTES IS INSIDE THIS HANDLER, INCLUDING
        # BOTH READINGS. It did not used to be: the two reading calls sat after
        # the handler with `body` live in this frame, and pytest renders the
        # arguments of the first and the deepest traceback frame with NO opt-in
        # flag - no `--showlocals` needed. An adversary planted an exception in
        # that gap and read the transcript: 240 characters of a real
        # decompressed body, carrying a `/Game/...` asset path on 3 of this
        # machine's 20 saves. A type path is personal-data-adjacent world
        # content under non-negotiable 12, and an ECHO PATH is exactly what an
        # unwinding frame is. The docstring above claimed this containment
        # before the code had it.
        try:
            data = path.read_bytes()
            parsed = header.parse_header(data)
            body = chunks.decompress_body(
                data, parsed.body_offset, header_version=parsed.header_version
            ).payload
            read += 1
            shipped = _shipped_triples(
                body, save_version=parsed.save_version, header_version=parsed.header_version
            )
            found = independent_table.independent_records(
                body, save_version=parsed.save_version, header_version=parsed.header_version
            )
        except (Exception, SystemExit) as exc:
            # `SystemExit` is named because it is NOT an `Exception`, and it
            # unwinds carrying the save path exactly as any other type would.
            # ONLY THE TYPE NAME IS KEPT - a class name is not save content, and
            # it is what `test_properties._sweep_payload_tags` keeps. The
            # exception's own message and every frame it carries are dropped
            # here rather than reported.
            failures.append(type(exc).__name__)
            continue
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
        failures=tuple(failures),
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
    # NOTHING MAY HAVE RAISED. A raise inside the sweep is both a containment
    # question and a coverage one, and it is reported as a bare count of type
    # names rather than as anything carrying save content.
    failures = len(swept.failures)
    assert failures == 0, (
        f"{failures} of {swept.saves} saves raised inside the sweep. The type names are "
        "held but not rendered here; a save that raises is a save neither reading was "
        "measured over"
    )
    # EVERY SAVE READ MUST HAVE PRODUCED A BODY BOTH READINGS SAW. Without this
    # the equalities below range over the bodies the second reading chose not to
    # decline, which is not the same claim as ranging over the library. MEASURED
    # by an adversary: declining one whole version pair removed 8 of 20 bodies
    # and 18893 records from every count here and the whole suite stayed green,
    # because a declined body contributes to NEITHER side of `missing`.
    bodies = swept.bodies
    assert bodies == swept.saves, (
        f"{bodies} of {swept.saves} saves produced a body both readings measured. A "
        "DECLINED BODY LEAVES BOTH SIDES OF EVERY EQUALITY BELOW AT ONCE, so a reading "
        "that declines its way down the library satisfies all of them over whatever it "
        "kept. This is the arm that makes the word LIBRARY in those claims true"
    )
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
    # Four refutations of this item were that shape. NO COUNT IS QUOTED HERE:
    # the operator plays this game while a session runs and autosave rotation
    # alone changes how many saves are present, so a measured number written
    # into this file would be a lie with a timestamp on it (CLAUDE.md 4).
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
# THE DYNAMIC SEAM ARMS (CS-862) - the separator the static guards cannot be
#
# The three arms in "The seam guards" above are a SYNTACTIC scan plus a
# callable check over the names this module spells. An adversary graded them
# with five mutants and a two-level reach and a ``getattr`` call are caught by
# NEITHER (CS-864). Until this section existed no arm anywhere in
# ``tests/save/`` separated the second reading from the shipped one at RUN
# TIME: ``independent_records`` reimplemented as a wrapper over
# ``objects.parse_body``, reading not one byte of the body for itself, left the
# whole suite green at its pristine count.
#
# WHY EVERY OTHER ARM IS BLIND TO IT. Every library-backed claim about this
# reading is an AGREEMENT claim - ``missing == 0``, ``strangers == 0``,
# ``ordered == compared`` - and agreement is exactly what a wrapper maximises.
# Agreement can therefore never be the separator. DISAGREEMENT ON PURPOSE is:
# degrade the shipped record table in process and require this reading to stay
# RIGHT while it is degraded. A wrapper follows the degradation and reddens.
#
# THE PLANTS ARE THE SESSION-40 COUNTER-EXAMPLE - relabel every record's kind,
# and slide every payload start one byte with the extent END held. That is the
# pair of fields a record table exists to state, and it is the same degradation
# `tests/save/test_struct_interior.py` applies to the table's OUTPUT. Applying
# it at the SOURCE instead is the whole difference: the output form cannot reach
# a reading that never consults the output.
#
# THERE ARE FOUR, AND WHAT EACH ONE DOES TO THE SHIPPED WALK IS MEASURED
# RATHER THAN INTENDED. The first version of this section had two, and the
# discriminator-table plant was DOCUMENTED AS A RELABEL AND IS NOT ONE:
#
#   `_KIND_BY_OBJECT_TYPE`   the shipped walk REFUSES the body outright. The
#                            kind decides how many bytes a record occupies -
#                            an actor closes with a transform, a component with
#                            a parent path - so swapping the table
#                            desynchronises `_read_levelled_record` at once and
#                            it raises. It moves no field; it deletes them all.
#   `_read_levelled_record`  the TRUE relabel. The real reader consumes the
#                            correct bytes and only the returned record's kind
#                            is flipped, so the walk completes and `is_actor`
#                            alone moves.
#   `_read_data_entries`     the shift. `body_offset` and `body_length` move
#                            and nothing else does.
#   `_Cursor`                a SECOND REFUSAL, and it is written down as one.
#                            One byte of overrun on every string desynchronises
#                            the walk at its first level and `parse_body`
#                            raises on all four measured pairs and on the
#                            hand-built body. A cursor plant cannot be anything
#                            else here - see its docstring.
#
# THE TWO REFUSING PLANTS ARE KEPT DELIBERATELY, and not because a refusal is as
# good as a relabel. Each reaches a symbol nothing else here does.
# `_KIND_BY_OBJECT_TYPE` is the only shared DATA symbol planted, so it is the
# only one a reading that IMPORTS the discriminator follows - which
# `independent_table` deliberately does not do. `_Cursor` is the primitive every
# string, count and size in the shipped walk is read through, and CS-866
# measured a reading that delegates its string step to it passing all 63 arms
# this module had. See the mutant table below.
#
# THE GROUND TRUTH IS THE FIXTURE AND THE BYTES, NEVER THE PRISTINE READING.
# Asserting only that the second reading DID NOT MOVE is an equality between
# two calls of one function - the shape that refuted round 5's control - and it
# is satisfied outright by any reading that memoises its answer. What is
# asserted here is that the reading still matches what the fixture declared and
# what the body's own bytes say, and no plant can reach either.
#
# THE PLANT IS SHOWN TO FIRE BEFORE ANYTHING IS CONCLUDED FROM IT. The first
# plant written for this section wrapped ``objects._read_record``, which is the
# FLAT reader ``parse_object_headers`` uses; ``parse_body`` calls
# ``_read_levelled_record`` instead, so the shipped table did not move and the
# arm would have passed against every possible second reading including a
# verbatim wrapper. Each arm below establishes that the SHIPPED reading moved
# before it asserts that this one did not.
#
# GRADED WITH MUTANTS, pristine floor re-run and verified green after each.
# "Static" is the four arms in "The seam guards" - the three seam arms plus the
# discriminator anti-drift arm. "Dynamic" is the cases of the two arms below.
#
# MEASURED AT CS-862, when the two arms below collected 15 cases (12 plus 3):
#
#   mutant                                        static red    dynamic red
#   wrapper: `objects.parse_body(...)`              2 of 4        15 of 15
#   wrapper: `getattr(objects, "parse"+"_body")`    0 of 4        15 of 15
#   kind via `objects._KIND_BY_OBJECT_TYPE.get`     0 of 4         5 of 5 *
#   the SHIFT plant made inert                      0 of 4         5 of 5 *
#
#   * only the cases whose plant the mutant can reach. Row 3 is separated by
#     the discriminator plant alone and row 4 reddens exactly the shift plant's
#     own observability assertion - plus
#     `test_every_field_the_second_reading_reports_is_degraded_by_some_plant`,
#     which is the arm that notices a field has stopped being graded at all.
#
# ROWS 2 AND 3 ARE WHY THIS SECTION EXISTS. Both are routes CS-864 measured
# that NO static arm sees, and before this section nothing anywhere in
# `tests/save/` went red for either. Row 1 reddens only 2 of the 4 static arms
# even for the most obvious wrapper there is.
#
# AND THAT TABLE WAS NOT ENOUGH, WHICH IS CS-866. Two adversaries and then the
# merger substituted a MEMOISING wrapper for the second reading and left all 15
# green - row 2 with a `dict` in front of it. A third substitution routed the
# reading's string step through `objects._Cursor` and left all 63 arms green.
# Both are closed by the freshness section further down and by the `_Cursor`
# plant, and both were re-measured against the repaired module over the 20 cases
# the two arms now collect (16 plus 4):
#
#   mutant                                        static red    dynamic red
#   MEMOISING `getattr` wrapper                     0 of 4        20 of 20
#   recomputing `getattr` wrapper                   0 of 4        20 of 20
#   `_Reader.string` via `objects._Cursor`          0 of 4         5 of 5 *
#
#   * the five cases carrying the `_Cursor` plant, which is the only one that
#     reaches it. The mutant is a correct reading of the body everywhere else,
#     so the other 15 cases are right to stay green.
#
# THE FIRST ROW IS THE WHOLE OF CS-866's FIRST HALF. The same wrapper scored
# 0 of 4 static and 0 of 15 dynamic before the freshness repair - green on the
# entire module - because every case re-read a body an earlier arm had already
# read pristine. NOTHING ABOUT THE PLANTS CHANGED to close it.
#
# WHAT THESE ARMS STILL CANNOT SEPARATE, NAMED RATHER THAN IMPLIED AWAY. Every
# one of these is a route by which a reading could stop being second while this
# module stays green, and none of them is closed here:
#
#   A CAPTURE TAKEN AT IMPORT TIME. `monkeypatch.setattr` rebinds a name on the
#   shipped MODULE. A reading that binds `_Cursor` - or any other planted symbol
#   - to its own module-level name when it is imported and then calls that name
#   holds the PRISTINE object for the whole session, and no plant here can reach
#   it. MEASURED, not predicted: the `_Cursor` mutant in the table above,
#   changed only to capture `getattr(objects, "_Cursor")` at import time instead
#   of at each call, leaves all 70 arms of this module green. The plants keep
#   working through an import-time capture of `parse_body` ITSELF, because
#   `parse_body` resolves the symbols they replace as globals when it RUNS - so
#   it is the capture of a PLANTED symbol, not of the entry point, that escapes.
#
#   EVERY SHIPPED SYMBOL `parse_body` REACHES THAT IS NOT PLANTED. At least
#   `_read_bounded_count`, `_read_section_size`, `_attribute_payloads`,
#   `_read_level_tail`, `_read_grid_preamble`, `_read_collectables` and
#   `_check_section`. A reading rebuilt out of any of those is followed by no
#   plant in this mapping, exactly as a `_Cursor` reading was followed by none
#   before CS-866. The mapping is a POPULATION and it is not the whole surface.
#
#   BODIES BUILT OUTSIDE THIS MODULE. The freshness guard enumerates the bodies
#   THIS module builds. A body another module in the same session happens to
#   build identically is outside what it can see, and a cache is a process-wide
#   thing.
#
#   A THIRD DYNAMIC ARM THAT BUILDS ITS OWN BODY. The freshness guard walks
#   `_dynamic_case_identities`, which is derived from the plants and the pairs
#   but names the two arms below explicitly. An arm added tomorrow that calls
#   `_case_nonce` is covered the day it is written - the lookup REFUSES an
#   identity the enumeration does not carry. An arm that builds a body without
#   going through `_dynamic_case_body` is covered by nothing, and would read
#   whatever it built with no arm noticing that an earlier arm had read it
#   first. That is the same shape as this whole item, one level up.
#
#   ANY SHIPPED MODULE THAT IS NOT `objects`. Every plant here patches
#   `clockspeed.save.objects`. A reading that reached `chunks` or `header` is
#   untouched by all four.
# ---------------------------------------------------------------------------


#: How far a planted payload start moves. ONE BYTE, and the extent END is held
#: rather than shifted - the same choice ``test_struct_interior._degrade_one_record``
#: makes and for the same reason: a start and a length that both move keep the
#: payload the same width, which a bounds check alone could notice, while
#: holding the end makes the planted extent a strictly narrower window inside
#: the real one.
_PLANT_SHIFT: Final = 1


def _relabelled_discriminator_table(real: Any) -> Any:
    """Swap the two kinds the shipped object-type discriminator maps onto.

    WHAT IT DOES TO THE SHIPPED WALK IS REFUSE THE BODY, NOT RELABEL IT, and
    that is measured on all four pairs rather than intended. The kind decides
    how many bytes a record occupies, so a swapped table desynchronises
    ``_read_levelled_record`` at its first record and ``parse_body`` raises.
    An earlier version of this docstring called it a relabel; the relabel is
    :func:`_relabelled_record_reader`, which flips the kind AFTER the real
    reader has consumed the right bytes.

    IT IS KEPT ANYWAY, and for a reason no other plant here covers: it is the
    only one that plants a shared DATA symbol. ``independent_table``
    re-transcribes the discriminator rather than importing it, and until this
    plant existed nothing graded that decision - the anti-drift arm that guards
    it is an equality between two spellings, which a shared import satisfies
    trivially. A reading that reached
    ``objects._KIND_BY_OBJECT_TYPE.get(...)`` follows this plant and no other.

    It is DERIVED from the shipped table rather than transcribed, so a third
    discriminator measured tomorrow is swapped the day it is added instead of
    being silently left pristine by a hand-written literal.

    Args:
        real: The shipped mapping, object type to kind.

    Returns:
        The same keys, each carrying the other kind.
    """
    return MappingProxyType(
        {
            object_type: (
                objects.KIND_COMPONENT if kind == objects.KIND_ACTOR else objects.KIND_ACTOR
            )
            for object_type, kind in real.items()
        }
    )


def _with_the_other_kind(record: objects.ObjectRecord) -> objects.ObjectRecord:
    """Return one record carrying the kind it does not carry.

    THE RECORD IS BUILT FIELD BY FIELD RATHER THAN WITH ``dataclasses.replace``,
    for the reason :meth:`clockspeed.save.objects.ObjectRecord.with_payload`
    gives: ADR 0007's write gate scans for the NAME ``replace``, and no shipped
    method changes a record's kind, so there is nothing to call instead.
    ``tests/save/test_struct_interior.py::test_the_table_control_takes_its_window_from_the_body_not_the_degraded_record``
    builds its own relabel the same way.

    THE COST OF SPELLING TEN FIELDS is that a field added to
    :class:`clockspeed.save.objects.ObjectRecord` with a default would be
    silently reset here rather than carried, which would make this a coarser
    degradation than it claims to be.
    ``test_the_relabel_changes_the_kind_and_nothing_else`` is what stops that
    happening quietly.

    Args:
        record: The record the real reader returned. Frozen, and not mutated.

    Returns:
        The same record wearing the other kind.
    """
    return objects.ObjectRecord(
        kind=(objects.KIND_COMPONENT if record.kind == objects.KIND_ACTOR else objects.KIND_ACTOR),
        type_path=record.type_path,
        root_object=record.root_object,
        instance_name=record.instance_name,
        transform=record.transform,
        parent=record.parent,
        object_type=record.object_type,
        was_placed_in_level=record.was_placed_in_level,
        body_offset=record.body_offset,
        body_length=record.body_length,
    )


def _relabelled_record_reader(real: Any) -> Any:
    """Let the shipped reader consume the right bytes, then flip what it says.

    THIS IS THE RELABEL, and the distinction from
    :func:`_relabelled_discriminator_table` is the whole reason both exist. The
    discriminator table is consulted DURING the walk and deciding it wrongly
    desynchronises the walk; the returned record is consulted AFTER, so flipping
    it there leaves a complete, well-formed and WRONG record table - which is
    what a defective record table actually looks like.

    Args:
        real: The shipped levelled-record reader this replaces.

    Returns:
        The planted reader.
    """

    def planted(*args: Any, **kwargs: Any) -> objects.ObjectRecord:
        return _with_the_other_kind(real(*args, **kwargs))

    return planted


def _shifted_data_entries(real: Any) -> Any:
    """Slide every located payload one byte later, holding its end.

    The wrapper takes ``*args`` rather than restating the shipped signature. A
    restated signature is a second transcription that can rot, and a plant that
    fails to apply is indistinguishable from one that applied and was survived.

    Args:
        real: The shipped locator this replaces.

    Returns:
        The planted locator.
    """

    def planted(*args: Any, **kwargs: Any) -> list[tuple[int, int]]:
        return [
            (at + _PLANT_SHIFT, length - _PLANT_SHIFT) if length >= _PLANT_SHIFT else (at, length)
            for at, length in real(*args, **kwargs)
        ]

    return planted


def _cursor_that_overruns_every_string(real: Any) -> Any:
    """Hand the shipped walk a cursor that steps ONE BYTE PAST every string.

    IT KILLS RATHER THAN DEGRADES, AND THAT IS MEASURED. ``parse_body`` REFUSES
    the body outright under it on all four measured pairs and on the hand-built
    body - ``ObjectBudgetExceededError`` on three pairs and the hand-built body,
    ``ObjectFormatError`` on the fourth. It is not a relabel and it is not a
    shift, and session 52's finding is that calling a kill a degradation is how
    a plant ends up wearing a stronger claim than it earns: A PLANT THAT KILLS
    HAS NOT TESTED THE DEGRADATION. :func:`_relabelled_discriminator_table` is
    the precedent - ``_shipped_triples`` returns ``()`` for a refusal, which the
    callers' observability assertion reads as a plant that moved the walk, and
    ``test_every_field_the_second_reading_reports_is_degraded_by_some_plant``
    steps past it rather than crediting it with a field.

    WHY IT CANNOT BE A DEGRADATION HERE. The only fields this module compares
    are the kind, the payload offset and the payload length. A cursor plant that
    leaves the number of bytes a string consumes ALONE moves none of them - it
    can mangle the text, and the text reaches no triple - and one that changes
    that number desynchronises the walk at the first level. There is no third
    option, so the choice is between a plant that is inert and a plant that
    refuses. Inert is worse: an inert plant is indistinguishable from a plant
    that was survived.

    WHAT IT IS FOR, and no other plant here covers it. CS-866 measured a second
    reading whose string step delegates to ``getattr(objects, "_Cursor")(...)``
    and found all 63 arms of this module green - the residue CS-864's note named
    as covered by nothing. ``objects.parse_body`` reaches at least ``_Cursor``,
    ``_read_bounded_count``, ``_read_section_size``, ``_attribute_payloads``,
    ``_read_level_tail``, ``_read_grid_preamble``, ``_read_collectables`` and
    ``_check_section``, and the other three plants touch NONE of them. This one
    takes the first, which is the primitive every string, count and size in the
    shipped walk is read through.

    THE SUBCLASS IS THE POINT. The plant is a transform of the shipped class
    rather than a re-transcription of it, so every method it does not name stays
    exactly what ships - the same discipline the other three keep by wrapping
    ``real`` instead of copying it.

    Args:
        real: The shipped cursor class this replaces.

    Returns:
        The planted cursor class.
    """

    class Planted(real):
        """The shipped cursor, overrunning by :data:`_PLANT_SHIFT` on each string."""

        def string(self, field: str) -> str:
            """Read one string exactly as the shipped cursor does, then overrun it.

            Args:
                field: The field being read. Passed straight through, so the
                    shipped refusals still name the field they always named.

            Returns:
                The decoded text, unchanged. THE TEXT IS NOT THE DEGRADATION -
                the cursor position is, and the text is returned untouched so
                nothing downstream can be reading a mangled string instead.
            """
            text: str = super().string(field)
            self.offset += _PLANT_SHIFT
            return text

    return Planted


#: One degradation of the shipped record table each, keyed by the module
#: attribute it replaces. Every entry is HANDED the real attribute and returns
#: the planted one, so a plant is a transform of what ships rather than a second
#: copy of it.
#:
#: TWO OF THE FOUR KILL AND TWO DEGRADE, and which is which is measured rather
#: than intended - see each plant's own docstring. A kill is a usable
#: degradation for the two arms below, which require only that the shipped
#: reading MOVED, and it is not evidence that any particular field is graded,
#: which is why
#: ``test_every_field_the_second_reading_reports_is_degraded_by_some_plant``
#: steps past a plant that costs the walk whole records.
_SHIPPED_PLANTS: Final[Mapping[str, Callable[[Any], Any]]] = MappingProxyType(
    {
        "_KIND_BY_OBJECT_TYPE": _relabelled_discriminator_table,
        "_read_levelled_record": _relabelled_record_reader,
        "_read_data_entries": _shifted_data_entries,
        "_Cursor": _cursor_that_overruns_every_string,
    }
)

#: The fields the second reading reports, taken from the dataclass itself and
#: never listed here. A fourth field added tomorrow is in scope for
#: ``test_every_field_the_second_reading_reports_is_degraded_by_some_plant``
#: the day it is added, rather than the day somebody remembers to widen a
#: literal. Their ORDER is the order ``_Triple`` puts them in, which is what
#: makes the two comparable position by position.
_REPORTED_FIELDS: Final = tuple(
    field.name for field in dataclasses.fields(independent_table.IndependentRecord)
)


# ---------------------------------------------------------------------------
# CASE FRESHNESS (CS-866) - THE HALF THE PLANTS CANNOT SUPPLY
#
# A CACHE CAN ONLY RETURN AN ANSWER IT WAS ALREADY GIVEN. Two adversaries who
# produced no part of CS-862, working from different briefs, independently
# replaced ``independent_records`` with a MEMOISING ``getattr`` wrapper over
# ``objects.parse_body`` and left all 15 dynamic cases green; the merger
# reproduced it with a third script. Every dynamic case called the second
# reading exactly ONCE, after the plant, on a body an EARLIER arm in this same
# module had already read while the tree was pristine - the measured pairs'
# fixture bodies through
# ``test_the_reading_agrees_with_the_shipped_table_on_a_synthetic_body``, the
# hand-built body through
# ``test_the_hand_built_body_yields_the_exact_offsets_its_bytes_declare``. The
# memo handed back the pristine answer, which is exactly what the fixture
# declares and what the bytes say, so grading against the fixture rather than
# against the pristine reading - which WAS the right repair for provenance -
# bought nothing whatever against a cache.
#
# THE REPAIR IS TO ASK A QUESTION NEVER ASKED BEFORE. Every dynamic case reads
# a body no earlier call anywhere in this process has read, and expects an
# answer no other case expects. A memo then MISSES, computes through whatever
# shipped reader it wraps, and takes the degradation like any other wrapper.
#
# BYTES ALONE ARE NOT ENOUGH, which is why the nonce moves the payload SIZES
# rather than some stepped-over filler. A cache keyed on ``(save_version,
# header_version)`` and not on the body is defeated only by the correct ANSWER
# differing case to case, and the payload sizes are what the reading reports.
#
# THE NONCE IS DERIVED FROM THE POPULATIONS THE ARMS ARE PARAMETRIZED OVER, not
# from a literal table. A fourth plant or a fifth measured pair gets its own the
# day it is added rather than the day somebody widens a list.
#
# AND IT IS ASSERTED RATHER THAN ARRANGED.
# ``test_no_dynamic_case_reads_a_body_any_other_case_or_arm_in_this_module_reads``
# and ``test_no_two_dynamic_cases_expect_the_same_answer_from_the_second_reading``
# are what stop the property rotting the first time somebody reuses a body.
# Neither of them calls the second reading - an arm that populated the cache it
# exists to defeat would be worse than no arm at all.
# ---------------------------------------------------------------------------


#: Which of the two dynamic arms a case belongs to. Part of the case identity
#: because both arms cover ``HAND_BUILT_PAIR``, so the pair and the plant alone
#: do not separate a fixture case from a hand-built one.
_FIXTURE_ARM: Final = "fixture"
_HAND_BUILT_ARM: Final = "hand_built"

#: One dynamic case's identity: which arm, which version pair, which plant.
_DynamicCase = tuple[str, tuple[int, int], str]


def _dynamic_case_identities() -> tuple[_DynamicCase, ...]:
    """Every case the two dynamic arms collect, in one canonical order.

    DERIVED FROM THE SAME TWO POPULATIONS THE ARMS ARE PARAMETRIZED OVER -
    :data:`MEASURED_PAIRS` and :data:`_SHIPPED_PLANTS` - and in the same sorted
    plant order, so this cannot enumerate a case the arms do not collect or
    miss one they do.

    Returns:
        One identity per dynamic case.
    """
    plants = tuple(sorted(_SHIPPED_PLANTS))
    return tuple(
        (_FIXTURE_ARM, pair, plant) for pair in MEASURED_PAIRS for plant in plants
    ) + tuple((_HAND_BUILT_ARM, HAND_BUILT_PAIR, plant) for plant in plants)


#: One nonce per dynamic case, and ZERO IS RESERVED for every arm outside this
#: section. The value is an enumeration index rather than a hash: a digest could
#: collide and a collision is exactly the fault the two guard arms exist to
#: catch, so the derivation is made injective by construction instead of being
#: trusted and checked.
_NONCE_BY_CASE: Final[Mapping[_DynamicCase, int]] = MappingProxyType(
    {identity: index + 1 for index, identity in enumerate(_dynamic_case_identities())}
)


def _case_nonce(arm: str, pair: tuple[int, int], plant: str) -> int:
    """The nonce one dynamic case builds its body and its expectations with.

    Args:
        arm: :data:`_FIXTURE_ARM` or :data:`_HAND_BUILT_ARM`.
        pair: The version pair, (header, save).
        plant: Which shipped attribute the case degrades.

    Returns:
        The case's nonce, never zero.
    """
    nonce = _NONCE_BY_CASE.get((arm, pair, plant))
    assert nonce is not None, (
        f"the {arm} arm collected a case for plant {plant!r} that "
        "_dynamic_case_identities does not enumerate, so the freshness guards "
        "never graded its body and it may be reading one an earlier arm read"
    )
    return nonce


def _hand_built_dynamic_case(plant: str) -> tuple[bytes, tuple[_Triple, ...]]:
    """The body and the pinned triples ONE hand-built dynamic case reads.

    THE ONE PLACE THAT BODY IS BUILT, so the guard arms and the arm they guard
    cannot drift onto different bytes.

    Args:
        plant: Which shipped attribute the case degrades.

    Returns:
        The prefixed body, and one triple per record in file order.
    """
    return _well_formed_hand_built(_case_nonce(_HAND_BUILT_ARM, HAND_BUILT_PAIR, plant))


def _dynamic_case_body(arm: str, pair: tuple[int, int], plant: str) -> bytes:
    """The body one dynamic case hands the second reading.

    Args:
        arm: :data:`_FIXTURE_ARM` or :data:`_HAND_BUILT_ARM`.
        pair: The version pair, (header, save).
        plant: Which shipped attribute the case degrades.

    Returns:
        The prefixed body.
    """
    if arm == _HAND_BUILT_ARM:
        body, _pinned = _hand_built_dynamic_case(plant)
        return body
    header_version, save_version = pair
    return _fixture_body(header_version, save_version, _case_nonce(arm, pair, plant))


def _dynamic_case_answer(
    arm: str, pair: tuple[int, int], plant: str
) -> tuple[tuple[bool, int], ...]:
    """What the second reading MUST report for one dynamic case, kind and length.

    NOT TAKEN FROM THE READING. The fixture cases' answer is the fixture's own
    declaration and the hand-built cases' is what ``bytes.index`` found in the
    finished body, which is what the arms themselves grade against.

    The two families are reduced to the same shape so they can be compared with
    each other: both arms cover ``HAND_BUILT_PAIR``, so a cache keyed on the
    version pair sees their cases as one population and they have to be distinct
    ACROSS the two arms and not only within each.

    Args:
        arm: :data:`_FIXTURE_ARM` or :data:`_HAND_BUILT_ARM`.
        pair: The version pair, (header, save).
        plant: Which shipped attribute the case degrades.

    Returns:
        One ``(is_actor, body_length)`` per record, in file order.
    """
    if arm == _HAND_BUILT_ARM:
        _body, pinned = _hand_built_dynamic_case(plant)
        return tuple((is_actor, length) for is_actor, _at, length in pinned)
    return tuple(
        zip(_expected_flags(), _expected_lengths(_case_nonce(arm, pair, plant)), strict=True)
    )


def _bodies_no_dynamic_case_may_reuse() -> tuple[bytes, ...]:
    """Every body an arm OUTSIDE this section hands the second reading.

    ENUMERATED FROM THE HELPERS THAT BUILD THEM rather than from a list beside
    them, which is why the one-off hand-built bodies were lifted out of their
    arms' frames. The truncations come from :data:`_TRUNCATIONS`, which is the
    same tuple that arm is parametrized over.

    ONE BODY OUTSIDE THIS SECTION IS NOT HERE AND CANNOT BE: the real
    decompressed body :func:`_sweep_the_library` hands the second reading. It is
    personal-data-bearing and it never leaves that helper's frame, which is
    non-negotiable 12 and not an oversight. Nothing is claimed about it here
    beyond the obvious - a real body is a save's whole world and a synthetic
    fixture is a few hundred bytes of it, so a collision is not the shape this
    guard is watching for.

    Returns:
        The bodies, in no particular order and with duplicates possible.
    """
    bodies: list[bytes] = [b""]
    for header_version, save_version in MEASURED_PAIRS:
        body = _fixture_body(header_version, save_version)
        bodies.append(body)
        bodies.extend(body[:-cut] for cut in _TRUNCATIONS)
    bodies.append(_empty_hand_built())
    bodies.append(_well_formed_hand_built()[0])
    bodies.append(_count_disagreeing_hand_built()[0])
    bodies.append(_over_declared_hand_built())
    bodies.extend(_unmeasured_discriminator_hand_built())
    return tuple(bodies)


def test_no_dynamic_case_reads_a_body_any_other_case_or_arm_in_this_module_reads() -> None:
    """FRESHNESS, ASSERTED - the half of CS-866 no plant can supply.

    A memoising wrapper over the shipped record table is a function of
    ``(body, pair)`` that is not the second reading, and it satisfied all 15
    dynamic cases at the commit this arm was written against. It could, because
    every one of those cases re-read a body an earlier arm in this module had
    already read while the tree was pristine.

    THIS ARM CALLS NOTHING. It builds bytes and compares bytes. Calling the
    second reading here would populate the very cache the freshness exists to
    defeat, and the arm would then be the defect rather than its guard.
    """
    cases = _dynamic_case_identities()
    collected = len(cases)
    assert collected > 0, (
        "no dynamic case is enumerated at all, so this arm holds vacuously and "
        "the two arms below it are graded by nothing"
    )
    fresh = len({_dynamic_case_body(*identity) for identity in cases})
    assert fresh == collected, (
        f"{fresh} distinct bodies across {collected} dynamic cases. Two cases "
        "sharing a body let a reading that MEMOISES its answer hand the second "
        "one the answer it computed for the first - which was computed under a "
        "different plant, or under none"
    )
    stale = frozenset(_bodies_no_dynamic_case_may_reuse())
    reused = sum(1 for identity in cases if _dynamic_case_body(*identity) in stale)
    assert reused == 0, (
        f"{reused} of {collected} dynamic cases read a body some other arm in "
        "this module also reads. Those arms run BEFORE this section and they "
        "run on a pristine tree, so a cache is holding the right answer to this "
        "case's question before the plant is ever applied"
    )


def test_no_two_dynamic_cases_expect_the_same_answer_from_the_second_reading() -> None:
    """The other cache key: the VERSION PAIR rather than the body.

    A wrapper keyed on ``(save_version, header_version)`` alone is untouched by
    fresh bytes - it would answer every case for a pair with whatever it
    computed for the first. It is separated only by the CORRECT ANSWERS
    differing, which is why the nonce moves the payload sizes the reading
    reports rather than filler the reading steps over.

    Both dynamic arms cover ``HAND_BUILT_PAIR``, so their cases share a key and
    are compared against each other here rather than each within itself.
    """
    cases = _dynamic_case_identities()
    answers = [_dynamic_case_answer(*identity) for identity in cases]
    # BOUND TO SCALARS BEFORE ASSERTING, as the library arm above is. pytest
    # rewrites the asserted EXPRESSION and renders it independently of the
    # message, so `distinct == len(answers)` puts the whole answer list in the
    # transcript. These are synthetic fixture numbers rather than save content,
    # and the discipline is kept anyway - the habit is what makes it hold where
    # the population is not synthetic.
    total = len(answers)
    distinct = len(frozenset(answers))
    assert distinct == total, (
        f"{distinct} distinct expected answers across {total} dynamic "
        "cases. Two cases whose correct answer is the same are not separated by "
        "a reading that caches one answer per version pair"
    )
    baselines = frozenset(
        (
            tuple(zip(_expected_flags(), _expected_lengths(), strict=True)),
            tuple((is_actor, length) for is_actor, _at, length in _well_formed_hand_built()[1]),
        )
    )
    shared = sum(1 for answer in answers if answer in baselines)
    assert shared == 0, (
        f"{shared} of {total} dynamic cases expect the same answer an arm "
        "outside this section already asked for and got on a pristine tree"
    )


def _plant(monkeypatch: pytest.MonkeyPatch, name: str) -> None:
    """Replace one shipped record-table attribute with its degraded form.

    ``monkeypatch.setattr`` RAISES on a name the shipped module does not carry,
    which is the loud half of the spelling problem this mapping has by being
    keyed on strings. The quiet half - a name that still exists but that
    ``parse_body`` no longer reaches - is what every caller's observability
    assertion is for, and it has already caught one inert plant.

    Args:
        monkeypatch: The fixture. It restores the attribute at teardown, which
            is what keeps a plant from outliving the arm that set it.
        name: Which shipped attribute to degrade.
    """
    monkeypatch.setattr(objects, name, _SHIPPED_PLANTS[name](getattr(objects, name)))


def _records_the_plant_moved(before: Sequence[_Triple], after: Sequence[_Triple]) -> int:
    """Count the shipped reading's records the plant actually CHANGED.

    POSITIONAL, AND NOT A SET DIFFERENCE, which is the whole reason this is a
    function rather than an expression at each call site. A set intersection is
    smaller than the population whenever the population repeats an element, so
    ``len(pristine & degraded) < len(pristine)`` is satisfied by an INERT plant
    on any body carrying two identical triples - and an inert plant is precisely
    what every caller here exists to rule out.

    ``zip_longest`` rather than ``zip``, because a plant that costs the shipped
    walk whole records is a plant that moved it, and a plain ``zip`` would
    truncate to the shorter side and count that as agreement.

    Args:
        before: The shipped reading taken pristine.
        after: The same reading taken under the plant.

    Returns:
        How many positions differ. ONE SCALAR.
    """
    return sum(1 for was, now in zip_longest(before, after, fillvalue=None) if was != now)


def _fixture_faults(
    body: bytes, found: Sequence[independent_table.IndependentRecord], nonce: int
) -> tuple[int, int, int]:
    """Count the records that disagree with the FIXTURE and with the body's bytes.

    Nothing here consults a value the shipped WALK produced. The flags and the
    lengths come from the fixture's own declaration; the offset is graded by the
    rule
    ``tests/save/test_independent_table.py::test_every_extent_starts_one_length_prefix_past_its_own_declared_length``
    states - a payload's four preceding bytes ARE its declared length in every
    measured layout - so an offset off by one byte is visible in the body alone.

    Args:
        body: The synthetic body the reading was taken over.
        found: The second reading's records, in file order. Its length is the
            caller's to check; this counts nothing about a length it was not
            given.
        nonce: The case's nonce, so the DECLARED lengths are this case's own.
            Passing zero here while the body was built with a nonce would grade
            the reading against another case's fixture.

    Returns:
        Wrong flags, wrong lengths and misplaced offsets. THREE SCALARS,
        because pytest renders an asserted EXPRESSION independently of the
        message beside it and an aggregate in that position is an echo path.
    """
    wrong_flags = sum(
        record.is_actor != flag for record, flag in zip(found, _expected_flags(), strict=True)
    )
    wrong_lengths = sum(
        record.body_length != length
        for record, length in zip(found, _expected_lengths(nonce), strict=True)
    )
    misplaced = sum(
        body[record.body_offset - objects.INT32_SIZE : record.body_offset]
        != struct.pack("<i", record.body_length)
        for record in found
    )
    return wrong_flags, wrong_lengths, misplaced


def test_the_relabel_changes_the_kind_and_nothing_else() -> None:
    """The relabel is a RELABEL, and not a reconstruction that quietly drops a field.

    :func:`_with_the_other_kind` spells ten fields, because no shipped method
    changes a record's kind and ``dataclasses.replace`` is a name ADR 0007's
    write gate scans for. So a field added to
    :class:`clockspeed.save.objects.ObjectRecord` WITH A DEFAULT would be reset
    to that default here rather than carried, turning a one-field degradation
    into a wider one in silence - and a wider degradation is a weaker plant
    wearing a stronger claim, which is the exact fault the discriminator plant
    was found to have. The field set is read from the dataclass, so the day such
    a field is added is the day this goes red.
    """
    header_version, save_version = HAND_BUILT_PAIR
    body, _pinned = _well_formed_hand_built()
    table = objects.parse_body(body, save_version=save_version, header_version=header_version)
    assert table.records, "the hand-built body carries no record, so this arm is vacuous"
    names = tuple(field.name for field in dataclasses.fields(objects.ObjectRecord))
    changed: set[str] = set()
    for record in table.records:
        other = _with_the_other_kind(record)
        changed.update(name for name in names if getattr(other, name) != getattr(record, name))
    assert sorted(changed) == ["kind"], (
        f"the relabel moved {sorted(changed)} across {len(table.records)} records where it "
        f"is claimed to move only the kind, out of the {len(names)} fields a record carries"
    )


@pytest.mark.parametrize("plant", sorted(_SHIPPED_PLANTS))
@pytest.mark.parametrize("pair", MEASURED_PAIRS)
def test_the_second_reading_stays_right_while_the_shipped_record_table_is_degraded(
    pair: tuple[int, int], plant: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Every measured pair and every plant: the shipped reading moves and this one does not.

    THE ORDER OF THE THREE STEPS IS THE ARM. The shipped reading is taken
    pristine, the plant is applied and the shipped reading is shown to have
    MOVED, and only then is the second reading required to be right. Skipping
    the middle step is how a plant that never applied reads as a plant that was
    survived.

    WHAT GOES RED HERE. A second reading that delegates to any shipped reader
    ``parse_body`` reaches - the call, an alias, a two-level reach or a
    ``getattr`` - takes the degraded kinds or the shifted extents and fails the
    fixture. That is the wrapper the static arms above cannot see.

    AND THE BODY IS THIS CASE'S OWN. It is built with a nonce nothing else in
    this process uses, so a reading that MEMOISES cannot be holding the answer
    already - see the freshness section above. The body comes from
    ``_dynamic_case_body`` rather than from ``_fixture_body`` directly so that
    the arm and the guard over it cannot drift onto different bytes.
    """
    header_version, save_version = pair
    nonce = _case_nonce(_FIXTURE_ARM, pair, plant)
    body = _dynamic_case_body(_FIXTURE_ARM, pair, plant)
    pristine = _shipped_triples(body, save_version=save_version, header_version=header_version)
    declared = len(_expected_flags())
    assert len(pristine) == declared, (
        f"the shipped walk read {len(pristine)} of the fixture's {declared} records "
        "before anything was planted, so this pair's baseline is already wrong and "
        "the degradation below would be measured against it"
    )

    _plant(monkeypatch, plant)
    degraded = _shipped_triples(body, save_version=save_version, header_version=header_version)
    moved = _records_the_plant_moved(pristine, degraded)
    assert moved > 0, (
        f"not one of the shipped walk's {declared} records changed under the plant, so "
        "the shipped reading did not move and this arm would pass against every "
        "possible second reading. A PLANT THAT NEVER APPLIED AND ONE THAT WAS SURVIVED "
        "PRODUCE THE SAME OUTPUT"
    )

    found = independent_table.independent_records(
        body, save_version=save_version, header_version=header_version
    )
    assert found is not None, (
        "the second reading DECLINED the fixture body while the shipped record table "
        "was degraded. It reads the body itself and nothing it reads changed, so a "
        "decline here is the plant reaching it"
    )
    read = len(found)
    assert read == declared, (
        f"the second reading returned {read} records where the fixture declares "
        f"{declared}, while the shipped table was degraded. A reading that owes the "
        "shipped table nothing cannot change its count when that table is degraded"
    )
    wrong_flags, wrong_lengths, misplaced = _fixture_faults(body, found, nonce)
    assert wrong_flags == 0, (
        f"{wrong_flags} of {read} records came back with the wrong kind while the "
        "shipped record table was degraded. The kind is read from the body and "
        "re-transcribed rather than imported, so neither plant on the shipped kind - "
        "the discriminator table nor the record reader - can reach it"
    )
    assert wrong_lengths == 0, (
        f"{wrong_lengths} of {read} records came back with a length the fixture did "
        "not declare while the shipped payload locator was shifted"
    )
    assert misplaced == 0, (
        f"{misplaced} of {read} records report an offset whose four preceding bytes "
        "are not the length they also report. THE BODY ALONE SAYS SO - a reading "
        "taking its extents from the degraded shipped locator lands one byte late "
        "and every one of them misses"
    )


@pytest.mark.parametrize("plant", sorted(_SHIPPED_PLANTS))
def test_a_degraded_shipped_record_table_cannot_move_the_hand_built_offsets(
    plant: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The same claim against ABSOLUTE offsets rather than a length-prefix rule.

    The fixture arm above grades the offset by a relation the body carries at
    every payload. This one grades it against the one expectation in this module
    that shares nothing with either reader OR with the encoder's bookkeeping:
    ``bytes.index`` over distinctive payload literals in the finished body.
    ``test_the_shipped_walk_reads_the_hand_built_body_the_same_way`` is what
    keeps that expectation a claim about the FORMAT rather than about this file.

    THE PAYLOADS ARE WIDENED BY THIS CASE'S NONCE, so the body and the located
    offsets are both this case's own and no other call in the process has asked
    for them. ``bytes.index`` follows the widening for free, which is the whole
    reason the expectation is located rather than predicted.
    """
    body, expected = _hand_built_dynamic_case(plant)
    header_version, save_version = HAND_BUILT_PAIR
    pristine = _shipped_triples(body, save_version=save_version, header_version=header_version)
    assert pristine == expected, (
        "the shipped walk does not read the hand-built body correctly before "
        "anything is planted, so nothing below grades a degradation"
    )

    _plant(monkeypatch, plant)
    degraded = _shipped_triples(body, save_version=save_version, header_version=header_version)
    moved = _records_the_plant_moved(expected, degraded)
    assert moved > 0, (
        f"none of the {len(expected)} hand-built records changed in the SHIPPED "
        "reading under the plant, so nothing was degraded and this arm grades nothing"
    )

    found = independent_table.independent_records(
        body, save_version=save_version, header_version=header_version
    )
    assert found is not None, "the second reading declined a body it reads pristine"
    mine = tuple((record.is_actor, record.body_offset, record.body_length) for record in found)
    assert len(mine) == len(expected), (
        f"the second reading returned {len(mine)} records where the body's own bytes "
        f"carry {len(expected)}"
    )
    astray = sum(1 for got, want in zip(mine, expected, strict=True) if got != want)
    assert astray == 0, (
        f"{astray} of {len(expected)} records disagree with the offsets `bytes.index` "
        "found in the body itself, while the shipped record table was degraded. The "
        "expectation is located in the BYTES and no plant can move it, so a reading "
        "that misses it is reading the shipped table rather than the body"
    )


def test_every_field_the_second_reading_reports_is_degraded_by_some_plant(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The plant set is not blind to a field, and it is not EMPTY.

    An empty parametrize set collects no case and reports no failure, so the two
    arms above are exactly as strong as this mapping is populated - the shape
    ``memory/an-empty-population-satisfies-every-zero.md`` records. This is the
    positive fact that stands in for a hardcoded count: every field
    :class:`independent_table.IndependentRecord` reports is moved in the SHIPPED
    reading by at least one plant, so no field is graded by nothing.

    The field names come from the dataclass rather than from a literal here, so
    a fourth field is in scope the day it is added.
    """
    body, expected = _well_formed_hand_built()
    header_version, save_version = HAND_BUILT_PAIR
    assert len(_REPORTED_FIELDS) == len(expected[0]), (
        f"the second reading reports {len(_REPORTED_FIELDS)} fields and a shipped "
        f"triple carries {len(expected[0])}, so the two no longer line up position "
        "by position and nothing below is comparing like with like"
    )

    moved: set[str] = set()
    for name in sorted(_SHIPPED_PLANTS):
        _plant(monkeypatch, name)
        degraded = _shipped_triples(body, save_version=save_version, header_version=header_version)
        # UNDONE BETWEEN PLANTS SO EACH IS MEASURED ALONE, and taken from the
        # FIXTURE rather than from a bare `MonkeyPatch()` so a raise between the
        # plant and this line still restores the shipped module at teardown
        # instead of leaking a degraded reader into every test after this one.
        monkeypatch.undo()
        if len(degraded) != len(expected):
            # A PLANT THAT COST THE SHIPPED WALK WHOLE RECORDS CONTRIBUTES
            # NOTHING HERE, and an earlier version of this arm credited it with
            # every field at once. That is how the discriminator plant - which
            # makes `parse_body` REFUSE rather than relabel - was reported as
            # covering `is_actor` while no plant moved that field at all. A kill
            # is a degradation the arms above can use and it is not evidence
            # that any particular field is graded.
            continue
        for got, want in zip(degraded, expected, strict=True):
            moved.update(
                field for field, a, b in zip(_REPORTED_FIELDS, got, want, strict=True) if a != b
            )

    unmoved = sorted(frozenset(_REPORTED_FIELDS) - moved)
    assert unmoved == [], (
        f"{len(unmoved)} of {len(_REPORTED_FIELDS)} fields the second reading reports "
        f"are moved by no plant: {unmoved}. An arm parametrized over this mapping "
        "grades only the fields it degrades, and an EMPTY mapping collects no case at "
        "all while reporting nothing"
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
