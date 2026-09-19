"""The count-prefixed NAMED-TRANSFORM list inside a payload's trailing run - CS-828.

WHAT THIS MODULE GRADES.

CS-828 read the int32 the trailing run OPENS with; CS-1068 read one derived class
set's remainder as a count-prefixed item list; three later cycles read a bare TWO
reference pair, a zero-valued residual and a count-prefixed reference LIST. This
module grades the NEXT shape the remainder takes - an int32 COUNT followed by that
many entries, each a length-prefixed NAME, then a fixed number of fixed-width
SCALARS, then one flag byte - and the derivation that decides which classes carry
it and at which scalar width a body writes it.

**THE WIDTH IS DERIVED, NEVER OBSERVED, AND THAT IS THE WHOLE CLAUSE.** The
remainder's width is whatever the bytes are, so ANY partition of it sums to the
declared end and no reading of it could have failed - the defect that refuted
CS-830 after it had merged. Every width this reader consumes therefore comes out
of the bytes or out of a shipped constant: the count says how many entries there
are, each name's own length prefix says how wide it is, the scalar block is
:data:`clockspeed.save.objects.TRANSFORM_LIST_SCALARS` scalars of one of the
widths :data:`clockspeed.save.objects.TRANSFORM_LIST_SCALAR_WIDTHS` allows, and
the flag is :data:`clockspeed.save.objects.TRANSFORM_LIST_ENTRY_FLAG_BYTES` wide.
The declared end is a BOUND and a VALIDATION and never a source of width, and
:func:`test_the_width_is_derived_from_the_prefixes_and_not_from_the_declared_end`
is the arm that goes red when that is swapped.

**THE SCALAR WIDTH IS NOT A CONSTANT OF THE FORMAT, AND A READER THAT ASSUMED
ONE WOULD MIS-READ EVERY BODY OF THE OTHER.** Measured on this project's library
the carrying class writes the block as 4-byte scalars on one of the three pairs
CS-828 covers and as 8-byte scalars on the other two. So the WIDTH is derived per
body from the body's own records - every remainder-bearing record of a carrying
class must land at the SAME one - and a class whose records disagree derives
nothing rather than being read at whichever width happened to fit.

**AN AMBIGUOUS REMAINDER DERIVES NOTHING EITHER, FOR THE REASON
``tests/save/test_reference_list.py`` GIVES.** The two scalar widths make the
walk reach each entry's length prefix at DIFFERENT offsets, so nothing structural
forbids both landing on the declared end. The derivation therefore refuses a
remainder that reads at more than one width instead of taking the first, and
:func:`test_a_remainder_that_reads_at_both_widths_derives_nothing` holds it
against a run CONSTRUCTED to read at both - the shipped reader, not the fixture,
is what asserts the run is ambiguous.

**A COUNT OF ZERO IS REFUSED, AND THAT IS A FOURTH SIDE OF THE CS-1068
COLLISION.** Four zero bytes are an empty count-prefixed item list AND an empty
string AND the zero-valued residual :func:`clockspeed.save.objects.read_zero_remainder` reads AND an
empty list of this shape. Nothing in the run tells those apart, so this reader
claims none of them and requires at least one entry it can walk.

**THE CARRYING CLASSES ARE DERIVED FROM THE CORPUS, NEVER TRANSCRIBED.** A
hand-written vocabulary of game content is the thing that rots, and CS-829's note
forbids exactly that shape. What :func:`test_the_shipped_default_vocabulary_is_empty`
asserts is the weaker thing an arm can see: that the shipped DEFAULT is empty, so
a caller that has not derived is handed no class at all.

THE LIBRARY HALF REPORTS COUNTS ONLY, contained exactly as
``tests/save/test_reference_list.py`` contains its own: every step wrapped, every
failure reduced to a type NAME, and never a path, a body, a class path or a
decoded world string out. A class path read out of a save is game content and a
save path carries the platform account id (CLAUDE.md section 2, non-negotiable
3), so the derived classes below are COUNTED and never named.

THE SYNTHETIC HALF NEEDS NO SAVE LIBRARY and runs on a machine with no game
installed, which is where the reader's own arms live.
"""

from __future__ import annotations

import struct
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from types import MappingProxyType
from typing import Final

import pytest

from clockspeed.data import locate
from clockspeed.save import chunks, header, objects
from tests.save import reach_guard, synthetic

#: Reaches the save library and is graded for containment, name to what it does.
_GRADED_LIBRARY_REACH: Final = MappingProxyType(
    {
        "_library_save_paths": "resolves the save root and the account directory, and globs",
        "_sweep_transform_lists": "reads and parses every save in the library",
    }
)

#: Reaches or touches a primitive without being a grader-able library helper,
#: name to why. EMPTY, AND DELIBERATELY SO - see the same declaration in
#: ``tests/save/test_reference_list.py`` for why a placeholder here turns the
#: module red rather than green.
_EXEMPT_LIBRARY_REACH: Final[Mapping[str, str]] = MappingProxyType({})

_BODY_PREFIX: bytes = b"\xab" * 16

#: The object-type discriminator each kind is written with, DERIVED from the
#: shipped map rather than transcribed.
_OBJECT_TYPE_BY_KIND: dict[str, int] = {
    kind: value
    for value, kind in objects._KIND_BY_OBJECT_TYPE.items()  # noqa: SLF001
}

#: The class paths the synthetic records are written with. SYNTHETIC NAMES,
#: never real ones - test fixtures are hand-authored and never slices of real
#: game data (CLAUDE.md section 7).
_CARRIER_TYPE_PATH: Final = "/Synthetic/Carrier.Synthetic_TransformCarrier_C"
_OTHER_TYPE_PATH: Final = "/Synthetic/Other.Synthetic_TransformOther_C"

#: Invented entry names. None is read out of a real save.
_NAME_A: Final = "Synthetic_Socket_01"
_NAME_B: Final = "Synthetic_Socket_02"

#: The flag byte the synthetic entries carry. DELIBERATELY NOT ZERO and
#: deliberately not one: the library writes one on every entry measured, so a
#: fixture writing the same value would be satisfied by a reader returning a
#: constant instead of reading the byte.
_SYNTHETIC_FLAG: Final = 0x5A

#: How wide the deliberately unreadable remainder of the named-but-unreadable
#: fixture is. ANY width the grammar cannot read would do - what the arm grades
#: is that the width comes back untouched.
_OPAQUE_REMAINDER_BYTES: Final = 7


def _scalar_values(count: int) -> tuple[float, ...]:
    """Distinct, exactly representable scalar values for a fixture entry.

    EXACTLY REPRESENTABLE IN BOTH WIDTHS, so an arm comparing what came back
    against what went in grades the reader rather than float rounding. They are
    DISTINCT so a reader returning a constant fails.

    Args:
        count: How many values to produce.

    Returns:
        The values.
    """
    return tuple(float(index + 1) * 0.5 for index in range(count))


def _entry_bytes(
    name: str,
    *,
    scalar_width: int,
    flag: int = _SYNTHETIC_FLAG,
    scalars: Sequence[float] | None = None,
) -> bytes:
    """One entry, written the way the corpus writes one.

    Args:
        name: The entry's name.
        scalar_width: How wide each scalar is.
        flag: The trailing flag byte's value.
        scalars: The scalar values, defaulting to the distinct fixture set.

    Returns:
        The entry's bytes.
    """
    values = _scalar_values(objects.TRANSFORM_LIST_SCALARS) if scalars is None else scalars
    code = "<f" if scalar_width == objects.TRANSFORM_LIST_FLOAT_SCALAR_BYTES else "<d"
    block = b"".join(struct.pack(code, value) for value in values)
    return synthetic.fstring(name) + block + bytes((flag,))


def _list_bytes(
    *,
    scalar_width: int,
    names: Sequence[str] = (_NAME_A, _NAME_B),
    declared: int | None = None,
) -> bytes:
    """A whole count-prefixed transform list, in the width the caller asks for.

    Args:
        scalar_width: How wide each scalar is.
        names: The entry names, in file order.
        declared: What the leading count should CLAIM, defaulting to the truth.

    Returns:
        The remainder's bytes.
    """
    count = len(names) if declared is None else declared
    entries = b"".join(_entry_bytes(name, scalar_width=scalar_width) for name in names)
    return struct.pack("<i", count) + entries


def _derived_width(*, scalar_width: int, names: Sequence[str] = (_NAME_A, _NAME_B)) -> int:
    """The width the COUNT and the PREFIXES describe, computed the long way round.

    A SECOND ENUMERATION SHARING NO CONSTANT WITH THE READER's own arithmetic -
    it is summed from the fixture's own names here rather than read off the
    result, so an arm comparing the two grades the reader instead of itself.

    Args:
        scalar_width: How wide each scalar is.
        names: The entry names, in file order.

    Returns:
        The width in bytes.
    """
    return objects.INT32_SIZE + sum(
        objects.INT32_SIZE
        + len(name.encode("utf-8"))
        + 1
        + objects.TRANSFORM_LIST_SCALARS * scalar_width
        + objects.TRANSFORM_LIST_ENTRY_FLAG_BYTES
        for name in names
    )


def _width_from_observation(at: int, end: int) -> int:
    """THE FORBIDDEN READING, spelled out so an arm can be swapped onto it.

    This is the width a partition-by-arithmetic reader would take. It closes on
    every payload and no reading of it can fail, which is exactly why CS-828's
    clause asks for a width derived from the payload instead.

    Args:
        at: The remainder's first byte.
        end: The first byte past the payload.

    Returns:
        The observed width.
    """
    return end - at


def _record_for(
    payload: bytes, *, type_path: str = _CARRIER_TYPE_PATH, body_offset: int | None = None
) -> objects.ObjectRecord:
    """Build the record that attributes ``payload`` inside the synthetic body.

    Args:
        payload: The payload the body will carry.
        type_path: The class path the record declares.
        body_offset: Where the payload sits, defaulting to the prefix's end.

    Returns:
        The record.
    """
    kind = objects.KIND_COMPONENT
    return objects.ObjectRecord(
        kind=kind,
        type_path=type_path,
        root_object="Synthetic_Root",
        instance_name="Synthetic_Instance",
        transform=None,
        parent=None,
        object_type=_OBJECT_TYPE_BY_KIND[kind],
        was_placed_in_level=0,
        body_offset=len(_BODY_PREFIX) if body_offset is None else body_offset,
        body_length=len(payload),
    )


def _carrier_payload(*, scalar_width: int, names: Sequence[str] = (_NAME_A, _NAME_B)) -> bytes:
    """A terminated payload whose trailing run carries a lead and a list.

    Args:
        scalar_width: How wide each scalar is.
        names: The entry names, in file order.

    Returns:
        The payload's bytes.
    """
    return synthetic.tagged_property_payload(
        (),
        trailing=struct.pack("<i", 0) + _list_bytes(scalar_width=scalar_width, names=names),
    )


def _opaque_payload() -> bytes:
    """A terminated payload whose remainder no grammar here reads.

    Returns:
        The payload's bytes.
    """
    return synthetic.tagged_property_payload(
        (), trailing=struct.pack("<i", 0) + b"\xee" * _OPAQUE_REMAINDER_BYTES
    )


def _body_of(payloads: Sequence[bytes]) -> tuple[bytes, tuple[int, ...]]:
    """Lay payloads out back to back behind the prefix.

    Args:
        payloads: The payloads, in body order.

    Returns:
        The body and one body offset per payload.
    """
    offsets: list[int] = []
    cursor = len(_BODY_PREFIX)
    for payload in payloads:
        offsets.append(cursor)
        cursor += len(payload)
    return (_BODY_PREFIX + b"".join(payloads), tuple(offsets))


def _ambiguous_remainder() -> bytes:
    """A remainder CONSTRUCTED to read as a list at BOTH scalar widths.

    HOW IT IS BUILT, because the construction is the claim. The buffer is a
    correct two-entry list at the WIDE scalar width. The NARROW walk reaches its
    second entry's LENGTH PREFIX at an offset that falls inside the wide first
    entry's scalar block, where the bytes mean nothing to either reading, so
    FOUR BYTES ARE PLANTED THERE and nothing else is disturbed. They announce a
    name exactly long enough that the narrow walk's own scalar block and flag
    land on the buffer's last byte - the name it announces is simply the wide
    reading's own later bytes, read as text.

    NOTHING HERE ASSERTS THE AMBIGUITY - the arm does, by asking the shipped
    reader at both widths. A fixture that stopped being ambiguous would redden
    it rather than quietly proving nothing.

    Returns:
        The remainder's bytes.
    """
    wide = objects.TRANSFORM_LIST_DOUBLE_SCALAR_BYTES
    narrow = objects.TRANSFORM_LIST_FLOAT_SCALAR_BYTES
    scalars = objects.TRANSFORM_LIST_SCALARS
    flag = objects.TRANSFORM_LIST_ENTRY_FLAG_BYTES
    first = synthetic.fstring(_NAME_A)
    second = synthetic.fstring(_NAME_B)
    body = bytearray(
        struct.pack("<i", 2)
        + first
        + b"\x11" * (scalars * wide)
        + bytes((_SYNTHETIC_FLAG,))
        + second
        + b"\x22" * (scalars * wide)
        + bytes((_SYNTHETIC_FLAG,))
    )
    # Where the NARROW walk expects its second entry's length prefix, and how
    # many name bytes that entry must claim for the two walks to land together.
    planted_at = objects.INT32_SIZE + len(first) + scalars * narrow + flag
    claimed = len(body) - planted_at - (objects.INT32_SIZE + scalars * narrow + flag)
    body[planted_at : planted_at + objects.INT32_SIZE] = struct.pack("<i", claimed)
    return bytes(body)


# ---------------------------------------------------------------------------
# The reader itself, with no save library anywhere
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("scalar_width", objects.TRANSFORM_LIST_SCALAR_WIDTHS)
def test_the_width_is_derived_from_the_prefixes_and_not_from_the_declared_end(
    scalar_width: int,
) -> None:
    """The reported width is summed from the fixture's own prefixes.

    Args:
        scalar_width: The scalar width under test.
    """
    remainder = _list_bytes(scalar_width=scalar_width)
    read = objects.read_transform_list(remainder, 0, len(remainder), scalar_width=scalar_width)

    assert read is not None
    assert read.width == _derived_width(scalar_width=scalar_width)


@pytest.mark.parametrize("scalar_width", objects.TRANSFORM_LIST_SCALAR_WIDTHS)
def test_a_stretched_declared_end_is_refused_rather_than_read_to(scalar_width: int) -> None:
    """THE ANTI-ARITHMETIC ARM. A reader sized by the leftover would still read.

    Args:
        scalar_width: The scalar width under test.
    """
    remainder = _list_bytes(scalar_width=scalar_width) + b"\x00" * 8
    stretched = len(remainder)

    assert _width_from_observation(0, stretched) != _derived_width(scalar_width=scalar_width)
    assert objects.read_transform_list(remainder, 0, stretched, scalar_width=scalar_width) is None


@pytest.mark.parametrize("scalar_width", objects.TRANSFORM_LIST_SCALAR_WIDTHS)
def test_every_entry_name_is_read_out_of_its_own_prefix(scalar_width: int) -> None:
    """The names come back in file order, out of the bytes.

    Args:
        scalar_width: The scalar width under test.
    """
    remainder = _list_bytes(scalar_width=scalar_width)
    read = objects.read_transform_list(remainder, 0, len(remainder), scalar_width=scalar_width)

    assert read is not None
    assert tuple(entry.name for entry in read.entries) == (_NAME_A, _NAME_B)


@pytest.mark.parametrize("scalar_width", objects.TRANSFORM_LIST_SCALAR_WIDTHS)
def test_the_scalars_are_read_out_of_the_bytes(scalar_width: int) -> None:
    """A distinct scalar set comes back, so a constant-returning reader fails.

    Args:
        scalar_width: The scalar width under test.
    """
    remainder = _list_bytes(scalar_width=scalar_width, names=(_NAME_A,))
    read = objects.read_transform_list(remainder, 0, len(remainder), scalar_width=scalar_width)

    assert read is not None
    assert read.entries[0].scalars == _scalar_values(objects.TRANSFORM_LIST_SCALARS)


@pytest.mark.parametrize("scalar_width", objects.TRANSFORM_LIST_SCALAR_WIDTHS)
def test_the_entry_flag_byte_is_read_rather_than_assumed(scalar_width: int) -> None:
    """The flag comes back as the fixture's value, which the library never writes.

    Args:
        scalar_width: The scalar width under test.
    """
    remainder = _list_bytes(scalar_width=scalar_width, names=(_NAME_A,))
    read = objects.read_transform_list(remainder, 0, len(remainder), scalar_width=scalar_width)

    assert read is not None
    assert read.entries[0].flag == _SYNTHETIC_FLAG


@pytest.mark.parametrize("scalar_width", objects.TRANSFORM_LIST_SCALAR_WIDTHS)
def test_the_declared_count_is_reported_beside_the_entries(scalar_width: int) -> None:
    """The count the prefix carries travels with the reading.

    Args:
        scalar_width: The scalar width under test.
    """
    remainder = _list_bytes(scalar_width=scalar_width)
    read = objects.read_transform_list(remainder, 0, len(remainder), scalar_width=scalar_width)

    assert read is not None
    assert (read.declared_count, len(read.entries)) == (2, 2)


@pytest.mark.parametrize("scalar_width", objects.TRANSFORM_LIST_SCALAR_WIDTHS)
def test_the_scalar_width_travels_with_the_reading(scalar_width: int) -> None:
    """A consumer can tell which width the body was read at.

    Args:
        scalar_width: The scalar width under test.
    """
    remainder = _list_bytes(scalar_width=scalar_width)
    read = objects.read_transform_list(remainder, 0, len(remainder), scalar_width=scalar_width)

    assert read is not None
    assert read.scalar_bytes == scalar_width


def test_a_list_written_narrow_does_not_read_wide() -> None:
    """The widths are not interchangeable, which is why the form is derived."""
    remainder = _list_bytes(scalar_width=objects.TRANSFORM_LIST_FLOAT_SCALAR_BYTES)

    read = objects.read_transform_list(
        remainder, 0, len(remainder), scalar_width=objects.TRANSFORM_LIST_DOUBLE_SCALAR_BYTES
    )

    assert read is None


def test_a_list_written_wide_does_not_read_narrow() -> None:
    """The other direction of the same claim."""
    remainder = _list_bytes(scalar_width=objects.TRANSFORM_LIST_DOUBLE_SCALAR_BYTES)

    read = objects.read_transform_list(
        remainder, 0, len(remainder), scalar_width=objects.TRANSFORM_LIST_FLOAT_SCALAR_BYTES
    )

    assert read is None


def test_a_count_of_zero_is_refused() -> None:
    """THE CS-1068 COLLISION, DECLINED. Four zero bytes are four other things."""
    remainder = b"\x00\x00\x00\x00"

    read = objects.read_transform_list(
        remainder, 0, len(remainder), scalar_width=objects.TRANSFORM_LIST_DOUBLE_SCALAR_BYTES
    )

    assert read is None


def test_a_negative_count_is_refused() -> None:
    """A count read as a negative int32 reads as no list at all."""
    remainder = struct.pack("<i", -1) + _entry_bytes(
        _NAME_A, scalar_width=objects.TRANSFORM_LIST_DOUBLE_SCALAR_BYTES
    )

    read = objects.read_transform_list(
        remainder, 0, len(remainder), scalar_width=objects.TRANSFORM_LIST_DOUBLE_SCALAR_BYTES
    )

    assert read is None


def test_a_count_claiming_more_entries_than_the_region_holds_is_refused() -> None:
    """The count is a claim the walk checks, not an instruction it obeys."""
    width = objects.TRANSFORM_LIST_DOUBLE_SCALAR_BYTES
    remainder = _list_bytes(scalar_width=width, names=(_NAME_A,), declared=2)

    assert objects.read_transform_list(remainder, 0, len(remainder), scalar_width=width) is None


def test_an_entry_name_reaching_past_the_declared_end_is_refused() -> None:
    """A length prefix the region cannot hold reads as no list."""
    width = objects.TRANSFORM_LIST_DOUBLE_SCALAR_BYTES
    remainder = bytearray(_list_bytes(scalar_width=width, names=(_NAME_A,)))
    struct.pack_into("<i", remainder, objects.INT32_SIZE, len(remainder) * 2)

    assert (
        objects.read_transform_list(bytes(remainder), 0, len(remainder), scalar_width=width) is None
    )


def test_an_empty_entry_name_is_refused() -> None:
    """A run of zeroes must not read as a named entry."""
    width = objects.TRANSFORM_LIST_DOUBLE_SCALAR_BYTES
    scalars = objects.TRANSFORM_LIST_SCALARS
    remainder = (
        struct.pack("<i", 1)
        + struct.pack("<i", 0)
        + b"\x00" * (scalars * width)
        + bytes((_SYNTHETIC_FLAG,))
    )

    assert objects.read_transform_list(remainder, 0, len(remainder), scalar_width=width) is None


def test_a_walk_landing_short_of_the_declared_end_is_refused() -> None:
    """The walk must land exactly, which is what makes the reading falsifiable."""
    width = objects.TRANSFORM_LIST_DOUBLE_SCALAR_BYTES
    remainder = _list_bytes(scalar_width=width, names=(_NAME_A, _NAME_B), declared=1)

    assert objects.read_transform_list(remainder, 0, len(remainder), scalar_width=width) is None


def test_a_scalar_width_outside_the_allowed_set_is_refused() -> None:
    """The widths are a CLOSED set, so a caller cannot invent one that fits."""
    width = objects.TRANSFORM_LIST_DOUBLE_SCALAR_BYTES
    remainder = _list_bytes(scalar_width=width)

    invented = width + 1
    assert invented not in objects.TRANSFORM_LIST_SCALAR_WIDTHS
    assert objects.read_transform_list(remainder, 0, len(remainder), scalar_width=invented) is None


def test_a_region_reaching_past_the_buffer_is_refused_rather_than_raising() -> None:
    """Non-negotiable 7 - a disagreeing extent is reported, never fatal."""
    width = objects.TRANSFORM_LIST_DOUBLE_SCALAR_BYTES
    remainder = _list_bytes(scalar_width=width)

    assert objects.read_transform_list(remainder, 0, len(remainder) + 1, scalar_width=width) is None


def test_a_negative_offset_is_refused_rather_than_raising() -> None:
    """The other end of the same bound."""
    width = objects.TRANSFORM_LIST_DOUBLE_SCALAR_BYTES
    remainder = _list_bytes(scalar_width=width)

    assert objects.read_transform_list(remainder, -1, len(remainder), scalar_width=width) is None


def test_the_entry_repr_withholds_the_name() -> None:
    """A repr is an echo path - non-negotiable 12."""
    entry = objects.TransformListEntry(name=_NAME_A, scalars=(1.0,), flag=1)

    assert _NAME_A not in repr(entry)


def test_the_list_repr_renders_counts_and_widths_only() -> None:
    """The container withholds what its entries withhold."""
    width = objects.TRANSFORM_LIST_DOUBLE_SCALAR_BYTES
    remainder = _list_bytes(scalar_width=width)
    read = objects.read_transform_list(remainder, 0, len(remainder), scalar_width=width)

    assert read is not None
    assert _NAME_A not in repr(read)
    assert _NAME_B not in repr(read)


# ---------------------------------------------------------------------------
# The derivation, still with no save library anywhere
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("scalar_width", objects.TRANSFORM_LIST_SCALAR_WIDTHS)
def test_a_class_whose_records_agree_on_a_width_is_derived(scalar_width: int) -> None:
    """The consistency requirement admits a class that meets it.

    Args:
        scalar_width: The scalar width under test.
    """
    payloads = [
        _carrier_payload(scalar_width=scalar_width),
        _carrier_payload(scalar_width=scalar_width, names=(_NAME_A,)),
    ]
    body, offsets = _body_of(payloads)
    records = [
        _record_for(payload, body_offset=offset)
        for payload, offset in zip(payloads, offsets, strict=True)
    ]

    derived = objects.derive_transform_list_classes(body, records)

    assert derived == {objects.class_name_of(_CARRIER_TYPE_PATH): scalar_width}


def test_a_class_whose_records_disagree_on_a_width_derives_nothing() -> None:
    """THE ANTI-VACUITY PROPERTY. A mixture is arithmetic in a derivation's clothes."""
    payloads = [
        _carrier_payload(scalar_width=objects.TRANSFORM_LIST_FLOAT_SCALAR_BYTES),
        _carrier_payload(scalar_width=objects.TRANSFORM_LIST_DOUBLE_SCALAR_BYTES),
    ]
    body, offsets = _body_of(payloads)
    records = [
        _record_for(payload, body_offset=offset)
        for payload, offset in zip(payloads, offsets, strict=True)
    ]

    assert objects.derive_transform_list_classes(body, records) == {}


def test_a_class_with_one_unreadable_record_derives_nothing() -> None:
    """A class that only sometimes carries the shape is not a carrier."""
    payloads = [
        _carrier_payload(scalar_width=objects.TRANSFORM_LIST_DOUBLE_SCALAR_BYTES),
        _opaque_payload(),
    ]
    body, offsets = _body_of(payloads)
    records = [
        _record_for(payload, body_offset=offset)
        for payload, offset in zip(payloads, offsets, strict=True)
    ]

    assert objects.derive_transform_list_classes(body, records) == {}


def test_a_body_carrying_no_list_derives_nothing() -> None:
    """A body that stops demonstrating the grammar says so."""
    payloads = [_opaque_payload()]
    body, offsets = _body_of(payloads)
    records = [_record_for(payloads[0], body_offset=offsets[0])]

    assert objects.derive_transform_list_classes(body, records) == {}


def test_a_second_class_is_derived_independently_of_the_first() -> None:
    """Membership is per class, so one carrier does not vouch for another."""
    payloads = [
        _carrier_payload(scalar_width=objects.TRANSFORM_LIST_DOUBLE_SCALAR_BYTES),
        _opaque_payload(),
    ]
    body, offsets = _body_of(payloads)
    records = [
        _record_for(payloads[0], body_offset=offsets[0]),
        _record_for(payloads[1], type_path=_OTHER_TYPE_PATH, body_offset=offsets[1]),
    ]

    derived = objects.derive_transform_list_classes(body, records)

    assert derived == {
        objects.class_name_of(_CARRIER_TYPE_PATH): objects.TRANSFORM_LIST_DOUBLE_SCALAR_BYTES
    }


def test_a_remainder_that_reads_at_both_widths_derives_nothing() -> None:
    """AMBIGUITY IS DECLINED, NOT RESOLVED BY THE ORDER THE WIDTHS ARE LISTED IN.

    THE SHIPPED READER ASSERTS THE FIXTURE IS AMBIGUOUS, not this module: the
    two reads below are what make the third assertion mean anything.
    """
    remainder = _ambiguous_remainder()
    reads = tuple(
        width
        for width in objects.TRANSFORM_LIST_SCALAR_WIDTHS
        if objects.read_transform_list(remainder, 0, len(remainder), scalar_width=width) is not None
    )

    assert reads == objects.TRANSFORM_LIST_SCALAR_WIDTHS
    assert objects._transform_list_width_of(remainder, 0, len(remainder)) is None  # noqa: SLF001


def test_the_shipped_default_vocabulary_is_empty() -> None:
    """A caller that has not derived is handed no class at all."""
    assert dict(objects._NO_TRANSFORM_LIST_CLASSES) == {}  # noqa: SLF001


# ---------------------------------------------------------------------------
# The seam into read_properties
# ---------------------------------------------------------------------------


def test_a_derived_carrier_has_its_remainder_read_and_unread_falls_to_zero() -> None:
    """The reading reaches a consumer through the documented keyword."""
    width = objects.TRANSFORM_LIST_DOUBLE_SCALAR_BYTES
    payload = _carrier_payload(scalar_width=width)
    body, offsets = _body_of([payload])
    record = _record_for(payload, body_offset=offsets[0])
    derived = objects.derive_transform_list_classes(body, [record])

    result = objects.read_properties(body, record, transform_list_classes=derived)

    assert result.trailing_run is not None
    assert result.trailing_run.transform_list is not None
    assert result.trailing_run.unread == 0


def test_a_caller_that_passes_no_vocabulary_reads_what_cs828_left() -> None:
    """The default reads less, and that is why the sweep passes it explicitly."""
    width = objects.TRANSFORM_LIST_DOUBLE_SCALAR_BYTES
    payload = _carrier_payload(scalar_width=width)
    body, offsets = _body_of([payload])
    record = _record_for(payload, body_offset=offsets[0])

    result = objects.read_properties(body, record)

    assert result.trailing_run is not None
    assert result.trailing_run.transform_list is None
    assert result.trailing_run.unread > 0


def test_a_named_class_whose_bytes_do_not_read_comes_back_untouched() -> None:
    """THE VOCABULARY IS A GATE ON THE READING AND NEVER THE READING ITSELF."""
    payload = _opaque_payload()
    body, offsets = _body_of([payload])
    record = _record_for(payload, body_offset=offsets[0])
    named = MappingProxyType(
        {objects.class_name_of(_CARRIER_TYPE_PATH): objects.TRANSFORM_LIST_DOUBLE_SCALAR_BYTES}
    )

    result = objects.read_properties(body, record, transform_list_classes=named)

    assert result.trailing_run is not None
    assert result.trailing_run.transform_list is None
    assert result.trailing_run.unread == _OPAQUE_REMAINDER_BYTES


# ---------------------------------------------------------------------------
# The library half - COUNTS ONLY, skip-if-absent
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _ListSweep:
    """What the library sweep observed. Integers and type names only.

    Attributes:
        carriers: How many classes the derivation admitted, by version pair.
        read: How many payloads had their remainder read as this shape.
        failures: The type names of any unexpected failure.
    """

    carriers: MappingProxyType
    read: MappingProxyType
    failures: tuple[str, ...]


def _library_save_paths() -> tuple[Path, ...]:
    """Every save file on this machine, or an empty tuple.

    IT HOLDS EVERY ``Exception`` AND EVERY ``SystemExit``, and every discovery
    call sits INSIDE the ``try``: the account directory's NAME is the platform
    account id, and a failure unwinding through a frame that holds it is an
    echo path under non-negotiable 3.

    Returns:
        The save paths, sorted, or an empty tuple when there is no library.
    """
    try:
        root = locate.resolve_save_root()
        account = locate.resolve_account_dir(root) if root is not None else None
        return () if account is None else tuple(sorted(account.glob("*.sav")))
    except (Exception, SystemExit):
        return ()


@lru_cache(maxsize=1)
def _sweep_transform_lists() -> _ListSweep | None:
    """Derive and read this shape across every real save, COUNTS ONLY.

    Returns:
        The sweep, or None when no save library is reachable.
    """
    saves = _library_save_paths()
    if not saves:
        return None
    carriers: Counter[tuple[int, int]] = Counter()
    read: Counter[tuple[int, int]] = Counter()
    failures: list[str] = []
    for path in saves:
        try:
            data = path.read_bytes()
            parsed = header.parse_header(data)
        except (OSError, header.HeaderError):
            continue
        except (Exception, SystemExit) as exc:
            failures.append(type(exc).__name__)
            continue
        pair = (parsed.header_version, parsed.save_version)
        if pair not in objects.MEASURED_BODY_LAYOUTS:
            continue
        # BROAD BY DESIGN: a narrower catch lets an unexpected type escape
        # carrying the save bytes.
        try:
            body = chunks.decompress_body(
                data, parsed.body_offset, header_version=parsed.header_version
            ).payload
            table = objects.parse_body(
                body, save_version=parsed.save_version, header_version=parsed.header_version
            )
            derived = objects.derive_transform_list_classes(
                body,
                table.records,
                save_version=parsed.save_version,
                header_version=parsed.header_version,
            )
            carriers[pair] = max(carriers[pair], len(derived))
            for record in table.records:
                if not record.body_length:
                    continue
                result = objects.read_properties(
                    body,
                    record,
                    save_version=parsed.save_version,
                    header_version=parsed.header_version,
                    transform_list_classes=derived,
                )
                run = result.trailing_run
                if run is not None and run.transform_list is not None:
                    read[pair] += 1
        except (Exception, SystemExit) as exc:
            failures.append(type(exc).__name__)
            continue
    return _ListSweep(
        carriers=MappingProxyType(dict(carriers)),
        read=MappingProxyType(dict(read)),
        failures=tuple(sorted(set(failures))),
    )


def _sweep_or_skip() -> _ListSweep:
    """Fetch the sweep, skipping the arm when there is no library.

    Returns:
        The sweep.
    """
    sweep = _sweep_transform_lists()
    if sweep is None:
        pytest.skip("no save library on this machine")
    return sweep


def test_the_library_sweep_reports_no_unexpected_failure() -> None:
    """A sweep that fell over reports nothing trustworthy about the world."""
    sweep = _sweep_or_skip()

    assert sweep.failures == ()


def test_the_shape_is_read_on_at_least_one_payload_of_the_library() -> None:
    """The derivation is not vacuous on the corpus it was derived from."""
    sweep = _sweep_or_skip()

    assert sum(sweep.read.values()) > 0


def test_every_pair_that_derives_a_carrier_also_reads_a_payload() -> None:
    """A derived vocabulary that read nothing would be a gate admitting nobody."""
    sweep = _sweep_or_skip()

    barren = tuple(pair for pair, count in sweep.carriers.items() if count and not sweep.read[pair])

    assert barren == ()


def test_every_library_reaching_function_here_is_declared() -> None:
    """The reach guard, keyed on the RISKY primitives rather than the safe route.

    NEEDS NO SAVE LIBRARY - it is a claim about this module's source.
    """
    reach_guard._assert_library_reach_is_declared(  # noqa: SLF001
        Path(__file__), graded=_GRADED_LIBRARY_REACH, exempt=_EXEMPT_LIBRARY_REACH
    )
