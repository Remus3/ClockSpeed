"""The zero-valued residual that closes a payload's trailing run - CS-828.

WHAT THIS MODULE GRADES.

CS-828 read the int32 the trailing run OPENS with. CS-1068 then read one derived
class set's remainder as a count-prefixed item list, and a later cycle read
another's as two object references. This module grades the shape that carries
the REST of the open population on this project's library: a remainder that is
exactly one int32 wide and reads ZERO.

**THE WIDTH IS A SHIPPED CONSTANT AND THE VALUE IS READ OUT OF THE BYTES, WHICH
IS WHAT KEEPS THIS FROM BEING ARITHMETIC.** The remainder's width is whatever
the bytes are, so ANY partition of it sums to the declared end and no reading of
it could have failed - the defect that refuted CS-830 after it had merged. This
reader therefore consumes :data:`clockspeed.save.objects.ZERO_REMAINDER_BYTES`
and nothing else, and REFUSES when the declared end is anywhere but there.
:func:`test_the_width_is_a_shipped_constant_and_never_the_declared_end` is the
arm that inverts when that is swapped.

**AND IT REFUSES ON A NON-ZERO VALUE, WHICH IS THE SECOND HALF OF THE SAME
PROPERTY.** A reader that consumed four bytes whatever they said would succeed on
every four-byte remainder in existence and could not fail. The claim being made
is that the remainder is an EMPTY structure - a zero count or a zero length - so
bytes that say otherwise are a DIFFERENT shape and must not be swallowed.
:func:`test_a_non_zero_remainder_at_the_shipped_width_is_refused` holds it.

**WHAT THIS READING DOES NOT CLAIM, and the disclaimer is the point rather than
modesty.** Four zero bytes are BYTE-IDENTICAL to an empty count-prefixed item
list, which is CS-1068's root cause seen from the other side. Nothing here says
which of those the region IS, and no reading of the run can: only the class's
own corpus behaviour could, and CS-1119 owns that question. What is read is the
VALUE at a DERIVED landing point, exactly as the lead field is.

**THE CARRYING CLASSES ARE DERIVED FROM THE CORPUS, NEVER TRANSCRIBED.** A
hand-written vocabulary of game content is the thing that rots, and CS-829's
note forbids exactly that shape.
:func:`test_no_class_vocabulary_is_transcribed_into_the_shipped_reader` holds the
shipped module to it.

THIS MODULE NEEDS NO SAVE LIBRARY AND REACHES NOTHING, and that is deliberate
rather than an omission. The library half of this reading is counted by the
sweep in ``tests/save/test_trailing_run.py``, which already walks every save
once; a second full-library walk here would triple the cost of the suite to
re-measure a population that sweep already reports.
"""

from __future__ import annotations

import struct
from collections.abc import Sequence
from typing import Final

from clockspeed.save import objects
from tests.save import synthetic

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
_CARRIER_TYPE_PATH: Final = "/Synthetic/Carrier.Synthetic_ZeroCarrier_C"
_OTHER_TYPE_PATH: Final = "/Synthetic/Other.Synthetic_ZeroOther_C"

#: A remainder width the grammar cannot read. ANY width other than the shipped
#: one would do - what the arms grade is that it comes back untouched.
_OPAQUE_REMAINDER_BYTES: Final = 7

#: A non-zero value written where the shape says zero. ANY non-zero integer
#: would do.
_NON_ZERO_VALUE: Final = 1


def _zero_remainder_bytes() -> bytes:
    """The remainder this reading closes, written the way the corpus writes it.

    Returns:
        The remainder's bytes.
    """
    return struct.pack("<i", objects.ZERO_REMAINDER_VALUE)


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


def _payload_with(remainder: bytes) -> bytes:
    """A terminated payload whose trailing run carries a lead and ``remainder``.

    Args:
        remainder: The bytes past the lead field.

    Returns:
        The payload's bytes.
    """
    return synthetic.tagged_property_payload(
        (), trailing=struct.pack("<i", objects.TRAILING_RUN_LEAD_MEASURED_VALUE) + remainder
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


def _records_for(
    payloads: Sequence[bytes], type_paths: Sequence[str]
) -> tuple[bytes, tuple[objects.ObjectRecord, ...]]:
    """Build a whole synthetic body and its record table.

    Args:
        payloads: The payloads, in body order.
        type_paths: One class path per payload.

    Returns:
        The body and its records.
    """
    body, offsets = _body_of(payloads)
    records = tuple(
        _record_for(payload, type_path=path, body_offset=offset)
        for payload, path, offset in zip(payloads, type_paths, offsets, strict=True)
    )
    return (body, records)


# ---------------------------------------------------------------------------
# The reader itself
# ---------------------------------------------------------------------------


def test_the_width_is_a_shipped_constant_and_never_the_declared_end() -> None:
    """THE ARM CS-828's CLAUSE NAMES. The same bytes, two declared ends.

    Where the declared end is exactly the shipped width away, the remainder
    reads. Moved past it, it is REFUSED - the outcome that inverts the moment
    the width is taken from :func:`_width_from_observation` instead.
    """
    run = _zero_remainder_bytes() + b"\x00" * 8
    honest_end = objects.ZERO_REMAINDER_BYTES
    stretched_end = honest_end + 8

    read = objects.read_zero_remainder(run, 0, honest_end)
    stretched = objects.read_zero_remainder(run, 0, stretched_end)

    assert read is not None
    assert read.width == objects.ZERO_REMAINDER_BYTES
    assert read.width != _width_from_observation(0, stretched_end)
    assert stretched is None


def test_the_value_is_read_out_of_the_bytes() -> None:
    """The reading this cycle ships, on a remainder the shape describes exactly."""
    run = _zero_remainder_bytes()

    read = objects.read_zero_remainder(run, 0, len(run))

    assert read is not None
    assert read.value == objects.ZERO_REMAINDER_VALUE
    assert read.width == objects.ZERO_REMAINDER_BYTES


def test_a_non_zero_remainder_at_the_shipped_width_is_refused() -> None:
    """THE FALSIFIABILITY ARM. The width alone never admits a remainder.

    A reader consuming four bytes whatever they said would succeed on every
    four-byte remainder in existence and could not fail. The claim is that the
    region is an EMPTY structure, so bytes that say otherwise are refused.
    """
    run = struct.pack("<i", _NON_ZERO_VALUE)

    assert objects.read_zero_remainder(run, 0, len(run)) is None


def test_a_remainder_narrower_than_the_shipped_width_is_refused() -> None:
    """A region too small to hold the field is no reading of it."""
    run = _zero_remainder_bytes()

    assert objects.read_zero_remainder(run, 0, objects.ZERO_REMAINDER_BYTES - 1) is None


def test_a_remainder_reaching_past_the_buffer_is_refused() -> None:
    """NOTHING HERE RAISES - non-negotiable 7, reported rather than fatal."""
    run = _zero_remainder_bytes()

    assert objects.read_zero_remainder(run, 0, len(run) + 1) is None
    assert objects.read_zero_remainder(run, -1, len(run)) is None


# ---------------------------------------------------------------------------
# The derivation
# ---------------------------------------------------------------------------


def test_a_class_whose_every_remainder_is_the_shape_is_derived() -> None:
    """The membership rule, on a body whose carrier is consistent."""
    payloads = (_payload_with(_zero_remainder_bytes()), _payload_with(_zero_remainder_bytes()))
    body, records = _records_for(payloads, (_CARRIER_TYPE_PATH, _CARRIER_TYPE_PATH))

    derived = objects.derive_zero_remainder_classes(body, records)

    assert objects.class_name_of(_CARRIER_TYPE_PATH) in derived


def test_a_class_whose_records_disagree_in_width_derives_nothing() -> None:
    """THE ANTI-VACUITY PROPERTY, and the reason the derivation is per body.

    A reader taking each record at whichever width happened to fit would admit
    every mixture, which is arithmetic wearing a derivation's clothes. One class
    writes one form per body, or it derives nothing.
    """
    payloads = (
        _payload_with(_zero_remainder_bytes()),
        _payload_with(b"\x5a" * _OPAQUE_REMAINDER_BYTES),
    )
    body, records = _records_for(payloads, (_CARRIER_TYPE_PATH, _CARRIER_TYPE_PATH))

    derived = objects.derive_zero_remainder_classes(body, records)

    assert objects.class_name_of(_CARRIER_TYPE_PATH) not in derived


def test_a_class_whose_remainder_is_the_shipped_width_but_non_zero_derives_nothing() -> None:
    """Agreeing on a WIDTH is not enough - the bytes have to say the shape too."""
    payloads = (_payload_with(struct.pack("<i", _NON_ZERO_VALUE)),)
    body, records = _records_for(payloads, (_CARRIER_TYPE_PATH,))

    derived = objects.derive_zero_remainder_classes(body, records)

    assert objects.class_name_of(_CARRIER_TYPE_PATH) not in derived


def test_a_class_with_no_remainder_at_all_is_not_derived() -> None:
    """A class whose run IS the lead field carries no remainder to name."""
    payloads = (_payload_with(b""),)
    body, records = _records_for(payloads, (_CARRIER_TYPE_PATH,))

    derived = objects.derive_zero_remainder_classes(body, records)

    assert objects.class_name_of(_CARRIER_TYPE_PATH) not in derived


def test_one_class_deriving_nothing_leaves_its_neighbour_derived() -> None:
    """Membership is per class, so an unreadable neighbour is not contagious."""
    payloads = (
        _payload_with(_zero_remainder_bytes()),
        _payload_with(b"\x5a" * _OPAQUE_REMAINDER_BYTES),
    )
    body, records = _records_for(payloads, (_CARRIER_TYPE_PATH, _OTHER_TYPE_PATH))

    derived = objects.derive_zero_remainder_classes(body, records)

    assert objects.class_name_of(_CARRIER_TYPE_PATH) in derived
    assert objects.class_name_of(_OTHER_TYPE_PATH) not in derived


def test_no_class_vocabulary_is_transcribed_into_the_shipped_reader() -> None:
    """The derivation reads the body. Nothing names a game class in the module.

    CS-829's note forbids a hand-written struct vocabulary by name, and the same
    fence covers this one: a derived membership that quietly fell back to a
    transcribed list would rot the moment the game shipped a class.
    """
    derived = objects.derive_zero_remainder_classes(_BODY_PREFIX, ())

    assert dict.fromkeys(derived) == {}


# ---------------------------------------------------------------------------
# The seam - what a caller of read_properties actually sees
# ---------------------------------------------------------------------------


def test_the_walk_carries_the_remainder_onto_the_result() -> None:
    """The reading reaches a consumer, and ``unread`` falls by what it read."""
    payloads = (_payload_with(_zero_remainder_bytes()),)
    body, records = _records_for(payloads, (_CARRIER_TYPE_PATH,))
    derived = objects.derive_zero_remainder_classes(body, records)

    result = objects.read_properties(body, records[0], zero_remainder_classes=derived)

    run = result.trailing_run
    assert run is not None
    assert run.zero_remainder is not None
    assert run.zero_remainder.value == objects.ZERO_REMAINDER_VALUE
    assert run.unread == 0


def test_an_underived_class_keeps_its_remainder_unread() -> None:
    """THE VOCABULARY IS A GATE ON THE READING AND NEVER THE READING ITSELF.

    The same bytes, with no vocabulary passed, come back exactly as CS-828 left
    them - which is what makes the default safe for every other caller.
    """
    payloads = (_payload_with(_zero_remainder_bytes()),)
    body, records = _records_for(payloads, (_CARRIER_TYPE_PATH,))

    result = objects.read_properties(body, records[0])

    run = result.trailing_run
    assert run is not None
    assert run.zero_remainder is None
    assert run.unread == objects.ZERO_REMAINDER_BYTES


def test_naming_a_class_whose_bytes_do_not_read_closes_nothing() -> None:
    """A derivation that named everything would still close nothing.

    That is what keeps the membership a measurement rather than a definition.
    """
    payloads = (_payload_with(b"\x5a" * _OPAQUE_REMAINDER_BYTES),)
    body, records = _records_for(payloads, (_CARRIER_TYPE_PATH,))

    result = objects.read_properties(
        body, records[0], zero_remainder_classes=(objects.class_name_of(_CARRIER_TYPE_PATH),)
    )

    run = result.trailing_run
    assert run is not None
    assert run.zero_remainder is None
    assert run.unread == _OPAQUE_REMAINDER_BYTES
