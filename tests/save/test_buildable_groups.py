"""The count-prefixed BUILDABLE GROUP LIST inside a payload's trailing run - CS-828.

WHAT THIS MODULE GRADES.

CS-828 read the int32 the trailing run OPENS with; five later cycles read a
count-prefixed item list, a bare two-reference pair, a zero-valued residual, a
count-prefixed reference LIST and a count-prefixed NAMED-TRANSFORM list. This
module grades the NEXT shape the remainder takes, and it is the widest region in
the run rather than the most populous: an int32 VERSION, an int32 GROUP COUNT,
and then that many groups, each a flag, a length-prefixed CLASS PATH, an int32
INSTANCE COUNT and that many instances.

**AN INSTANCE IS NOT A FIXED-WIDTH RECORD AND THAT IS WHERE THE READING EARNS
ITSELF.** It writes a fixed block, a length-prefixed reference, a second fixed
block, a second length-prefixed reference, a two-string object reference and an
int32 flag - and when that flag is set, a whole further structure whose own
declared size says how wide it is. So the walk's width comes from the two
counts, from four length prefixes per instance - five when the extra-data flag is
set - from one declared size and from the two shipped fixed blocks, and never
from what was left over.

**THE WIDTH IS DERIVED, NEVER OBSERVED, AND THAT IS THE WHOLE CLAUSE.** The
remainder's width is whatever the bytes are, so ANY partition of it sums to the
declared end and no reading of it could have failed - the defect that refuted
CS-830 after it had merged. The declared end is a BOUND and a VALIDATION here
and never a source of width, and
:func:`test_a_stretched_declared_end_is_refused_rather_than_read_to` is the arm
that holds it: a reader sized by the leftover passes that arm only by reading a
region it must refuse.

**AN EMPTY GROUP LIST IS READ, WHICH THE FOUR SIBLING READERS REFUSE, AND THE
GATE IS THE DERIVATION RATHER THAN THE READER.** Four zero bytes are an empty
count-prefixed list AND an empty string AND the zero-valued residual, so every
sibling refuses a count of zero outright. This shape opens with a VERSION word
ahead of its count, so an empty list here is eight bytes rather than four - but
eight bytes are still eight bytes, and a reader admitting them on its own would
claim any class whose remainder happened to be that wide. What keeps it honest
is that :func:`clockspeed.save.objects.derive_buildable_group_classes` admits a
class only when a record of that class DEMONSTRATES the grammar in the very body
being read, by carrying a NON-EMPTY list that walks exactly onto its declared
end - the same rule :func:`clockspeed.save.objects.derive_item_list_classes`
stands on, and
:func:`test_a_body_whose_only_record_carries_an_empty_list_derives_nothing`
is what holds it.

**THE CARRYING CLASSES ARE DERIVED FROM THE CORPUS, NEVER TRANSCRIBED.** A
hand-written vocabulary of game content is the thing that rots, and CS-829's
note forbids exactly that shape.
:func:`test_the_shipped_default_vocabulary_is_empty` asserts the weaker thing an
arm can see: that the shipped DEFAULT is empty, so a caller that has not derived
is handed no class at all.

THIS MODULE REACHES NO SAVE LIBRARY AT ALL, and that is a deliberate departure
from its five siblings rather than an omission. The library half of this reading
is graded by ``tests/save/test_trailing_run.py``, whose sweep passes every
derived vocabulary into ``read_properties`` and counts the payloads a derivation
read - so a second sweep here would re-walk the same library to report the same
population under another name. Every fixture below is hand-authored and runs on
a machine with no game installed.
"""

from __future__ import annotations

import struct
from collections.abc import Sequence
from typing import Final

import pytest

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
_CARRIER_TYPE_PATH: Final = "/Synthetic/Carrier.Synthetic_GroupCarrier_C"
_OTHER_TYPE_PATH: Final = "/Synthetic/Other.Synthetic_GroupOther_C"

#: Invented content paths. None is read out of a real save.
_GROUP_PATH: Final = "/Synthetic/Build/Synthetic_Panel.Synthetic_Panel_C"
_SWATCH: Final = "/Synthetic/Swatch/Synthetic_Slot.Synthetic_Slot_C"
_RECIPE: Final = "/Synthetic/Recipe/Synthetic_Panel.Synthetic_Panel_C"
_LEVEL: Final = "Synthetic_Level"
_REFERENCE: Final = "Synthetic_Level:SyntheticLevel.Synthetic_Proxy_1"
_EXTRA_TYPE: Final = "/Synthetic/Data.Synthetic_ExtraData"

#: The version word the fixture writes. DELIBERATELY NOT ZERO AND NOT ONE: a
#: reader returning a constant instead of reading the word fails on it.
_VERSION: Final = 7

#: The group flag the fixture writes, and the value a carried instance's flag
#: takes. Distinct from each other so a reader crossing the two fails.
_GROUP_FLAG: Final = 3
_EXTRA_FLAG: Final = 9

#: The bytes an extra-data block declares. ODD ON PURPOSE - a reader rounding
#: the declared size up to a word boundary would land wrong.
_EXTRA_PAYLOAD: Final = b"\x5a" * 13

#: How many instances the fixture group writes.
_FIXTURE_INSTANCES: Final = 2

#: How wide the deliberately unreadable remainder of the named-but-unreadable
#: fixture is. ANY width the grammar cannot read would do - what the arm grades
#: is that the width comes back untouched.
_OPAQUE_REMAINDER_BYTES: Final = 7


def _instance_bytes(
    *,
    swatch: str = _SWATCH,
    recipe: str = _RECIPE,
    level: str = "",
    reference: str = "",
    extra: bool = False,
) -> bytes:
    """One instance, written the way the corpus writes one.

    Args:
        swatch: The first length-prefixed reference.
        recipe: The second length-prefixed reference.
        level: The object reference's level string.
        reference: The object reference's path string.
        extra: Whether the instance carries a declared extra-data block.

    Returns:
        The instance's bytes.
    """
    head = b"\x11" * objects.BUILDABLE_INSTANCE_HEAD_BYTES
    mid = b"\x22" * objects.BUILDABLE_INSTANCE_MID_BYTES
    body = (
        head
        + synthetic.fstring(swatch)
        + mid
        + synthetic.fstring(recipe)
        + synthetic.fstring(level)
        + synthetic.fstring(reference)
    )
    if not extra:
        return body + struct.pack("<i", 0)
    return (
        body
        + struct.pack("<i", _EXTRA_FLAG)
        + struct.pack("<i", 0)
        + synthetic.fstring(_EXTRA_TYPE)
        + struct.pack("<i", len(_EXTRA_PAYLOAD))
        + _EXTRA_PAYLOAD
    )


def _group_bytes(*, instances: Sequence[bytes], declared: int | None = None) -> bytes:
    """One whole group - its flag, its class path, its count and its instances.

    Args:
        instances: The instances, in file order.
        declared: What the instance count should CLAIM, defaulting to the truth.

    Returns:
        The group's bytes.
    """
    count = len(instances) if declared is None else declared
    return (
        struct.pack("<i", _GROUP_FLAG)
        + synthetic.fstring(_GROUP_PATH)
        + struct.pack("<i", count)
        + b"".join(instances)
    )


def _list_bytes(*, groups: Sequence[bytes], declared: int | None = None) -> bytes:
    """A whole buildable group list, version word and all.

    Args:
        groups: The groups, in file order.
        declared: What the group count should CLAIM, defaulting to the truth.

    Returns:
        The remainder's bytes.
    """
    count = len(groups) if declared is None else declared
    return struct.pack("<ii", _VERSION, count) + b"".join(groups)


def _one_group_list(*, extra: bool = False) -> bytes:
    """The fixture list this module reads in most of its arms.

    Args:
        extra: Whether the second instance carries an extra-data block.

    Returns:
        The remainder's bytes.
    """
    return _list_bytes(
        groups=(
            _group_bytes(
                instances=(_instance_bytes(), _instance_bytes(extra=extra)),
            ),
        )
    )


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


def _carrier_payload(*, remainder: bytes) -> bytes:
    """A terminated payload whose trailing run carries a lead and ``remainder``.

    Args:
        remainder: The bytes past the lead field.

    Returns:
        The payload's bytes.
    """
    return synthetic.tagged_property_payload((), trailing=struct.pack("<i", 0) + remainder)


def _body_of(payloads: Sequence[bytes]) -> tuple[bytes, tuple[int, ...]]:
    """Lay payloads out back to back behind the prefix.

    Args:
        payloads: The payloads, in body order.

    Returns:
        The body and one body offset per payload.
    """
    offsets: list[int] = []
    body = bytearray(_BODY_PREFIX)
    for payload in payloads:
        offsets.append(len(body))
        body.extend(payload)
    return (bytes(body), tuple(offsets))


def _read(remainder: bytes, *, stretch: int = 0) -> objects.BuildableGroupList | None:
    """Read ``remainder`` as a group list, optionally stretching the declared end.

    Args:
        remainder: The remainder's bytes.
        stretch: How many extra bytes to hang past the list's own end.

    Returns:
        What the reader returned.
    """
    body = _BODY_PREFIX + remainder + b"\xee" * stretch
    return objects.read_buildable_group_list(body, len(_BODY_PREFIX), len(body))


# ---------------------------------------------------------------------------
# The reader itself, with no save library anywhere
# ---------------------------------------------------------------------------


def test_a_group_list_reads_its_version_its_groups_and_its_instances() -> None:
    """The whole shape comes back, decoded out of the bytes."""
    read = _read(_one_group_list())
    assert read is not None
    assert read.version == _VERSION
    assert read.declared_count == 1
    assert len(read.groups) == 1
    group = read.groups[0]
    assert group.class_path == _GROUP_PATH
    assert group.declared_count == _FIXTURE_INSTANCES
    assert tuple(instance.swatch for instance in group.instances) == (_SWATCH, _SWATCH)
    assert tuple(instance.recipe for instance in group.instances) == (_RECIPE, _RECIPE)


def test_the_reported_width_is_the_sum_of_its_own_prefixes() -> None:
    """The width a consumer is handed is summed from the fixture's own bytes.

    **THIS ARM DOES NOT GRADE THE ANTI-CS-830 PROPERTY AND MUST NOT BE CITED FOR
    IT.** On any fixture the reader ACCEPTS, the landing check has already made
    the walk's cursor and ``end - at`` equal, so swapping one spelling for the
    other is an EQUIVALENT mutant and no value can kill it. A draft of this
    docstring claimed the arm saw the difference and the cycle's verifier
    measured that false - the same sentence its sibling module deleted one
    commit earlier. What grades the refusal is
    :func:`test_a_stretched_declared_end_is_refused_rather_than_read_to`; what
    this arm grades is the figure a consumer is handed.
    """
    remainder = _one_group_list()
    read = _read(remainder)
    assert read is not None
    assert read.width == len(remainder)


def test_an_instance_carrying_extra_data_reads_its_declared_size() -> None:
    """The flagged block's own size is what the walk steps by, and it is reported."""
    read = _read(_one_group_list(extra=True))
    assert read is not None
    carried = read.groups[0].instances[1]
    assert carried.extra_type == _EXTRA_TYPE
    assert carried.extra_bytes == len(_EXTRA_PAYLOAD)


def test_an_instance_without_extra_data_reports_none_for_it() -> None:
    """An unset flag is read as no block rather than as a zero-width one."""
    read = _read(_one_group_list())
    assert read is not None
    assert read.groups[0].instances[0].extra_type is None


def test_an_instances_object_reference_reads_both_of_its_strings() -> None:
    """The two-string reference is carried, not stepped over."""
    remainder = _list_bytes(
        groups=(
            _group_bytes(
                instances=(_instance_bytes(level=_LEVEL, reference=_REFERENCE),),
            ),
        )
    )
    read = _read(remainder)
    assert read is not None
    instance = read.groups[0].instances[0]
    assert (instance.reference_level, instance.reference_path) == (_LEVEL, _REFERENCE)


def test_an_empty_group_list_reads_its_two_prefixes_and_nothing_else() -> None:
    """A count of zero is a list of no groups, and its width is the two prefixes."""
    read = _read(_list_bytes(groups=()))
    assert read is not None
    assert read.groups == ()
    assert read.width == (
        objects.BUILDABLE_GROUP_LIST_VERSION_BYTES + objects.BUILDABLE_GROUP_LIST_COUNT_BYTES
    )


def test_a_stretched_declared_end_is_refused_rather_than_read_to() -> None:
    """THE ANTI-CS-830 ARM. A reader sized by the leftover would read this."""
    assert _read(_one_group_list(), stretch=5) is None


def test_a_list_short_of_its_declared_end_is_refused() -> None:
    """A walk that lands short of ``end`` is refused, not rounded up."""
    remainder = _one_group_list()
    body = _BODY_PREFIX + remainder
    assert objects.read_buildable_group_list(body, len(_BODY_PREFIX), len(body) - 3) is None


def test_a_negative_group_count_is_refused() -> None:
    """A count below zero is reported as no list rather than raising."""
    assert _read(struct.pack("<ii", _VERSION, -1)) is None


def test_a_group_count_larger_than_the_remainder_can_hold_is_refused() -> None:
    """A count claiming more groups than the bytes can carry is refused."""
    assert _read(struct.pack("<ii", _VERSION, 1 << 20)) is None


def test_a_negative_instance_count_is_refused() -> None:
    """A group declaring a count below zero is refused."""
    assert _read(_list_bytes(groups=(_group_bytes(instances=(), declared=-1),))) is None


def test_an_instance_count_the_group_cannot_carry_is_refused() -> None:
    """A group claiming more instances than it wrote is refused."""
    remainder = _list_bytes(groups=(_group_bytes(instances=(_instance_bytes(),), declared=2),))
    assert _read(remainder) is None


def test_an_empty_group_class_path_is_refused() -> None:
    """Four zero bytes where a class path belongs is not a group."""
    remainder = _list_bytes(
        groups=(struct.pack("<i", _GROUP_FLAG) + synthetic.fstring("") + struct.pack("<i", 0),)
    )
    assert _read(remainder) is None


def test_a_remainder_shorter_than_the_two_prefixes_is_refused() -> None:
    """A remainder too narrow to carry a version and a count reads as nothing."""
    assert _read(struct.pack("<i", _VERSION)) is None


def test_an_extra_block_declaring_a_negative_size_is_refused() -> None:
    """A declared size below zero is refused rather than subtracted."""
    head = b"\x11" * objects.BUILDABLE_INSTANCE_HEAD_BYTES
    mid = b"\x22" * objects.BUILDABLE_INSTANCE_MID_BYTES
    instance = (
        head
        + synthetic.fstring(_SWATCH)
        + mid
        + synthetic.fstring(_RECIPE)
        + synthetic.fstring("")
        + synthetic.fstring("")
        + struct.pack("<i", _EXTRA_FLAG)
        + struct.pack("<i", 0)
        + synthetic.fstring(_EXTRA_TYPE)
        + struct.pack("<i", -1)
    )
    assert _read(_list_bytes(groups=(_group_bytes(instances=(instance,)),))) is None


def test_the_reader_raises_on_nothing_it_is_given() -> None:
    """Non-negotiable 7 - a run outside the body is reported, never raised."""
    body = _BODY_PREFIX
    assert objects.read_buildable_group_list(body, -1, len(body)) is None
    assert objects.read_buildable_group_list(body, 0, len(body) + 1) is None


def test_the_repr_withholds_every_decoded_world_string() -> None:
    """Non-negotiable 12 - a repr is an echo path, so it renders counts only."""
    read = _read(_one_group_list(extra=True))
    assert read is not None
    rendered = repr(read) + repr(read.groups[0]) + repr(read.groups[0].instances[1])
    for secret in (_GROUP_PATH, _SWATCH, _RECIPE, _EXTRA_TYPE):
        assert secret not in rendered


# ---------------------------------------------------------------------------
# The derivation, and the vocabulary gate it feeds
# ---------------------------------------------------------------------------


def test_the_shipped_default_vocabulary_is_empty() -> None:
    """A caller that has not derived is handed no class at all."""
    payload = _carrier_payload(remainder=_one_group_list())
    body, offsets = _body_of((payload,))
    record = _record_for(payload, body_offset=offsets[0])
    result = objects.read_properties(body, record)
    assert result.trailing_run is not None
    assert result.trailing_run.buildable_groups is None


def test_the_walk_carries_the_group_list_onto_the_result() -> None:
    """With the class derived, the remainder reads and ``unread`` falls to zero."""
    payload = _carrier_payload(remainder=_one_group_list())
    body, offsets = _body_of((payload,))
    record = _record_for(payload, body_offset=offsets[0])
    derived = objects.derive_buildable_group_classes(body, (record,))
    result = objects.read_properties(body, record, buildable_group_classes=derived)
    run = result.trailing_run
    assert run is not None
    assert run.buildable_groups is not None
    assert run.unread == 0


def test_the_derivation_admits_a_class_that_demonstrates_the_grammar() -> None:
    """A non-empty list landing exactly on the declared end earns the class."""
    payload = _carrier_payload(remainder=_one_group_list())
    body, offsets = _body_of((payload,))
    record = _record_for(payload, body_offset=offsets[0])
    derived = objects.derive_buildable_group_classes(body, (record,))
    assert objects.class_name_of(_CARRIER_TYPE_PATH) in derived


def test_a_body_whose_only_record_carries_an_empty_list_derives_nothing() -> None:
    """THE ANTI-VACUITY ARM. An empty list is eight bytes and demonstrates nothing."""
    payload = _carrier_payload(remainder=_list_bytes(groups=()))
    body, offsets = _body_of((payload,))
    record = _record_for(payload, body_offset=offsets[0])
    assert objects.derive_buildable_group_classes(body, (record,)) == frozenset()


def test_a_class_whose_remainder_no_grammar_reads_derives_nothing() -> None:
    """A class the derivation never saw the grammar from stays out of it."""
    payload = _carrier_payload(remainder=b"\xee" * _OPAQUE_REMAINDER_BYTES)
    body, offsets = _body_of((payload,))
    record = _record_for(payload, type_path=_OTHER_TYPE_PATH, body_offset=offsets[0])
    assert objects.derive_buildable_group_classes(body, (record,)) == frozenset()


def test_a_named_class_whose_bytes_do_not_read_comes_back_untouched() -> None:
    """The vocabulary is a GATE on the reading and never the reading itself."""
    payload = _carrier_payload(remainder=b"\xee" * _OPAQUE_REMAINDER_BYTES)
    body, offsets = _body_of((payload,))
    record = _record_for(payload, body_offset=offsets[0])
    result = objects.read_properties(
        body,
        record,
        buildable_group_classes=frozenset({objects.class_name_of(_CARRIER_TYPE_PATH)}),
    )
    run = result.trailing_run
    assert run is not None
    assert run.buildable_groups is None
    assert run.unread == _OPAQUE_REMAINDER_BYTES


@pytest.mark.parametrize("extra", [False, True])
def test_the_derivation_reads_both_instance_forms(extra: bool) -> None:
    """Both the plain and the extra-data instance form earn the class."""
    payload = _carrier_payload(remainder=_one_group_list(extra=extra))
    body, offsets = _body_of((payload,))
    record = _record_for(payload, body_offset=offsets[0])
    derived = objects.derive_buildable_group_classes(body, (record,))
    assert objects.class_name_of(_CARRIER_TYPE_PATH) in derived
