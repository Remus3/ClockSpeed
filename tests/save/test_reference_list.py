"""The count-prefixed object-reference list inside a payload's trailing run - CS-828.

WHAT THIS MODULE GRADES.

CS-828 read the int32 the trailing run OPENS with; CS-1068 read one derived class
set's remainder as a count-prefixed item list; CS-828's third and fourth cycles
read a bare TWO-reference pair and a zero-valued residual. This module grades the
NEXT shape the remainder takes - an int32 COUNT followed by that many object
references, each optionally preceded by a fixed-width per-entry prefix - and the
derivation that decides which classes carry it and which of the two forms a body
writes.

**THE WIDTH IS DERIVED, NEVER OBSERVED, AND THAT IS THE WHOLE CLAUSE.** The
remainder's width is whatever the bytes are, so ANY partition of it sums to the
declared end and no reading of it could have failed - the defect that refuted
CS-830 after it had merged. Every width this reader consumes therefore comes out
of the bytes or out of a shipped constant: the count says how many entries there
are, each string's own length prefix says how wide it is, and the per-entry
prefix is one of the two widths
:data:`clockspeed.save.objects.REFERENCE_LIST_ENTRY_PREFIX_WIDTHS` allows. The
declared end is a BOUND and a VALIDATION and never a source of width, and
:func:`test_the_width_is_derived_from_the_prefixes_and_not_from_the_declared_end`
is the arm that goes red when that is swapped.

**THE PER-ENTRY PREFIX IS NOT AN UNCONDITIONAL FIELD, AND A READER THAT ASSUMED
IT WAS WOULD MIS-READ EVERY BODY OF THE OTHER FORM.** Measured on this project's
library, one carrying class writes a scalar ahead of every reference and two
write the reference alone. So the FORM is derived per body from the body's own
records - every remainder-bearing record of a carrying class must land on the
SAME one of the two - and a class whose records disagree derives nothing rather
than being read at whichever width happened to fit.

**AN AMBIGUOUS REMAINDER DERIVES NOTHING EITHER, WHICH IS WEAKER THAN THE PAIR
READER CAN CLAIM AND IS STATED RATHER THAN ROUNDED UP.**
:func:`clockspeed.save.objects.read_reference_pair` can argue that at most one
tail width reaches the declared end, because its string walk is fixed and only
the tail moves. Here the two forms start their walks at DIFFERENT offsets, so
nothing structural forbids both landing. The derivation therefore refuses a
remainder that reads at more than one width instead of taking the first, and
:func:`test_a_remainder_that_reads_at_both_forms_derives_nothing` holds it.

**THE CARRYING CLASSES ARE DERIVED FROM THE CORPUS, NEVER TRANSCRIBED.** A
hand-written vocabulary of game content is the thing that rots, and CS-829's
note forbids exactly that shape. **NO ARM HERE HOLDS THE SHIPPED MODULE TO
THAT, AND A FIRST DRAFT OF THIS SENTENCE CLAIMED ONE DID** - this cycle's
verifier measured the claim false and it is corrected rather than quietly
dropped. What :func:`test_the_shipped_default_vocabulary_is_empty` asserts is
the weaker thing it can: that the shipped DEFAULT is empty, so a caller that
has not derived is handed no class at all. A module that added a transcribed
allowlist beside it would still pass, and until an arm can see one, the fence
is doctrine rather than a mechanism.

THE LIBRARY HALF REPORTS COUNTS ONLY, contained exactly as
``tests/save/test_reference_pair.py`` contains its own: every step wrapped, every
failure reduced to a type NAME, and never a path, a body, a class path or a
decoded world string out. A class path read out of a save is game content and a
save path carries the platform account id (CLAUDE.md section 2, non-negotiable
3), so the derived classes below are COUNTED and never named.

THE SYNTHETIC HALF NEEDS NO SAVE LIBRARY and runs on a machine with no game
installed, which is where the reader's own arms live.
"""

from __future__ import annotations

import struct
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
        "_sweep_reference_lists": "reads and parses every save in the library",
    }
)

#: Reaches or touches a primitive without being a grader-able library helper,
#: name to why. EMPTY, AND DELIBERATELY SO - see the same declaration in
#: ``tests/save/test_reference_pair.py`` for why a placeholder here turns the
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
_CARRIER_TYPE_PATH: Final = "/Synthetic/Carrier.Synthetic_ListCarrier_C"
_OTHER_TYPE_PATH: Final = "/Synthetic/Other.Synthetic_ListOther_C"

#: The generic level name a real body also carries. A GAME CONSTANT rather than
#: personal data, and reused here so the fixture has the shape of the thing.
_LEVEL: Final = synthetic.MAP_NAME

#: Invented object paths. None is a real one.
_PATH_A: Final = "Persistent_Level:PersistentLevel.Synthetic_ListCarrier_C_0"
_PATH_B: Final = "Persistent_Level:PersistentLevel.Synthetic_ListCarrier_C_1"
_PATH_C: Final = "Persistent_Level:PersistentLevel.Synthetic_ListCarrier_C_2"

#: The value the synthetic per-entry prefix carries. ARBITRARY - what the arms
#: grade is the WIDTH it occupies, which is the thing a partition-by-arithmetic
#: reader would have taken from the leftover instead.
_ENTRY_PREFIX_VALUE: Final = 1

#: How wide the deliberately unreadable remainder of the named-but-unreadable
#: fixture is. ANY width the grammar cannot read would do - what the arm grades
#: is that the width comes back untouched.
_OPAQUE_REMAINDER_BYTES: Final = 7


def _reference_bytes(level_reference: str, object_path: str) -> bytes:
    """One object reference, written the way the corpus writes one.

    Args:
        level_reference: The level the reference names.
        object_path: The object the reference names.

    Returns:
        The reference's bytes.
    """
    return synthetic.fstring(level_reference) + synthetic.fstring(object_path)


def _list_bytes(*, entry_prefix_bytes: int, paths: Sequence[str] = (_PATH_A, _PATH_B)) -> bytes:
    """A whole count-prefixed reference list, in the form the caller asks for.

    Args:
        entry_prefix_bytes: How wide a scalar to write ahead of each reference.
        paths: The object paths, in file order.

    Returns:
        The remainder's bytes.
    """
    prefix = struct.pack("<i", _ENTRY_PREFIX_VALUE)[:entry_prefix_bytes]
    entries = b"".join(prefix + _reference_bytes(_LEVEL, path) for path in paths)
    return struct.pack("<i", len(paths)) + entries


def _derived_width(*, entry_prefix_bytes: int, paths: Sequence[str] = (_PATH_A, _PATH_B)) -> int:
    """The width the COUNT and the PREFIXES describe, computed the long way round.

    A SECOND ENUMERATION SHARING NO CONSTANT WITH THE READER's own arithmetic -
    it is summed from the fixture's own strings here rather than read off the
    result, so an arm comparing the two grades the reader instead of itself.

    Args:
        entry_prefix_bytes: How wide a scalar the fixture wrote per entry.
        paths: The object paths, in file order.

    Returns:
        The width in bytes.
    """
    strings = tuple(text for path in paths for text in (_LEVEL, path))
    return (
        objects.INT32_SIZE
        + len(paths) * entry_prefix_bytes
        + sum(objects.INT32_SIZE + len(text.encode("utf-8")) + 1 for text in strings)
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


def _carrier_payload(
    *, entry_prefix_bytes: int, paths: Sequence[str] = (_PATH_A, _PATH_B)
) -> bytes:
    """A terminated payload whose trailing run carries a lead and a list.

    Args:
        entry_prefix_bytes: How wide a scalar to write ahead of each reference.
        paths: The object paths, in file order.

    Returns:
        The payload's bytes.
    """
    return synthetic.tagged_property_payload(
        (),
        trailing=struct.pack("<i", 0)
        + _list_bytes(entry_prefix_bytes=entry_prefix_bytes, paths=paths),
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


# ---------------------------------------------------------------------------
# The reader itself, with no save library anywhere
# ---------------------------------------------------------------------------


def test_the_width_is_derived_from_the_prefixes_and_not_from_the_declared_end() -> None:
    """THE ARM CS-828's CLAUSE NAMES. The same bytes, two declared ends.

    Where the declared end is where the count and the prefixes say it is, the
    list reads. Moved out past them, it is REFUSED - which is exactly the
    outcome that inverts when the derivation is swapped for
    :func:`_width_from_observation`.
    """
    run = _list_bytes(entry_prefix_bytes=0)
    honest_end = len(run)
    stretched_end = honest_end + 8

    read = objects.read_reference_list(run + b"\x00" * 8, 0, honest_end, entry_prefix_bytes=0)
    stretched = objects.read_reference_list(
        run + b"\x00" * 8, 0, stretched_end, entry_prefix_bytes=0
    )

    assert read is not None
    assert read.width == _derived_width(entry_prefix_bytes=0)
    assert read.width != _width_from_observation(0, stretched_end)
    assert stretched is None


def test_a_list_reads_every_reference_out_of_its_own_prefixes() -> None:
    """The reading this cycle ships, on a run whose count and prefixes describe it."""
    run = _list_bytes(entry_prefix_bytes=0, paths=(_PATH_A, _PATH_B, _PATH_C))

    read = objects.read_reference_list(run, 0, len(run), entry_prefix_bytes=0)

    assert read is not None
    assert tuple(ref.object_path for ref in read.references) == (_PATH_A, _PATH_B, _PATH_C)
    assert tuple(ref.level_reference for ref in read.references) == (_LEVEL, _LEVEL, _LEVEL)
    assert read.entry_prefix_bytes == 0
    assert read.width == _derived_width(entry_prefix_bytes=0, paths=(_PATH_A, _PATH_B, _PATH_C))


def test_the_prefixed_form_consumes_the_shipped_width_and_lands_exactly() -> None:
    """The other form: a scalar ahead of every reference, then the reference."""
    prefix = objects.REFERENCE_LIST_ENTRY_PREFIX_BYTES
    paths = (_PATH_A, _PATH_B)
    run = _list_bytes(entry_prefix_bytes=prefix, paths=paths)

    read = objects.read_reference_list(run, 0, len(run), entry_prefix_bytes=prefix)

    assert read is not None
    assert read.entry_prefix_bytes == prefix
    assert read.width == _derived_width(entry_prefix_bytes=prefix, paths=paths)
    assert len(read.references) == len(paths)


def test_reading_the_prefixed_form_at_the_bare_width_is_refused() -> None:
    """The two forms are not interchangeable, and the reader says so.

    A reader that took its width from the declared end would read BOTH, which
    is the whole reason the form is derived rather than observed.
    """
    run = _list_bytes(entry_prefix_bytes=objects.REFERENCE_LIST_ENTRY_PREFIX_BYTES)

    assert objects.read_reference_list(run, 0, len(run), entry_prefix_bytes=0) is None


def test_reading_the_bare_form_at_the_prefixed_width_is_refused() -> None:
    """And the same from the other side."""
    run = _list_bytes(entry_prefix_bytes=0)

    read = objects.read_reference_list(
        run, 0, len(run), entry_prefix_bytes=objects.REFERENCE_LIST_ENTRY_PREFIX_BYTES
    )

    assert read is None


def test_a_width_outside_the_shipped_set_is_refused() -> None:
    """The per-entry width is a SHIPPED CONSTANT, so an invented one reads nothing."""
    run = _list_bytes(entry_prefix_bytes=0)
    invented = max(objects.REFERENCE_LIST_ENTRY_PREFIX_WIDTHS) + 1

    assert objects.read_reference_list(run, 0, len(run), entry_prefix_bytes=invented) is None


def test_a_run_of_zero_bytes_is_not_an_empty_list_of_empty_strings() -> None:
    """A run of zeroes reads a count of zero, and a count of zero is REFUSED.

    That is the CS-1068 lesson transferred twice over. Four zero bytes are an
    empty count-prefixed list AND an empty string, so a reader admitting either
    would read a run of zeroes as a reference list and `and nowhere else` would
    be false. The zero-valued residual that shape collides with is
    :func:`clockspeed.save.objects.read_zero_remainder`'s subject and stays
    there.
    """
    run = b"\x00" * (objects.INT32_SIZE * 5)

    assert objects.read_reference_list(run, 0, len(run), entry_prefix_bytes=0) is None
    assert objects.read_reference_list(run, 0, objects.INT32_SIZE, entry_prefix_bytes=0) is None


def test_an_empty_string_inside_an_entry_is_refused() -> None:
    """An empty path is four zero bytes, so admitting one admits any zero run."""
    run = struct.pack("<i", 1) + synthetic.fstring(_LEVEL) + struct.pack("<i", 0)

    assert objects.read_reference_list(run, 0, len(run), entry_prefix_bytes=0) is None


def test_a_count_claiming_more_entries_than_the_payload_holds_is_refused() -> None:
    """A count is a width the bytes supply, and it is VALIDATED against the bound."""
    run = _list_bytes(entry_prefix_bytes=0)
    overcounted = struct.pack("<i", 9) + run[objects.INT32_SIZE :]

    assert (
        objects.read_reference_list(overcounted, 0, len(overcounted), entry_prefix_bytes=0) is None
    )


def test_a_negative_count_is_refused() -> None:
    """A negative count is REPORTED as no list, never raised - non-negotiable 7."""
    run = _list_bytes(entry_prefix_bytes=0)
    negative = struct.pack("<i", -2) + run[objects.INT32_SIZE :]

    assert objects.read_reference_list(negative, 0, len(negative), entry_prefix_bytes=0) is None


def test_a_length_prefix_reaching_past_the_payload_is_refused() -> None:
    """A prefix claiming more than the payload holds is REPORTED, never raised."""
    run = _list_bytes(entry_prefix_bytes=0)
    head = run[: objects.INT32_SIZE]
    overlong = head + struct.pack("<i", len(run) * 4) + run[objects.INT32_SIZE * 2 :]

    assert objects.read_reference_list(overlong, 0, len(overlong), entry_prefix_bytes=0) is None


def test_a_run_landing_short_of_the_declared_end_is_refused() -> None:
    """Landing short is as fatal as landing long - the walk must land ON the end."""
    run = _list_bytes(entry_prefix_bytes=0)

    assert (
        objects.read_reference_list(run + b"\x00" * 4, 0, len(run) + 4, entry_prefix_bytes=0)
        is None
    )


def test_a_remainder_reaching_past_the_body_is_refused() -> None:
    """The bound is the BODY as well as the declared end."""
    run = _list_bytes(entry_prefix_bytes=0)

    assert objects.read_reference_list(run, 0, len(run) + 1, entry_prefix_bytes=0) is None
    assert objects.read_reference_list(run, -1, len(run), entry_prefix_bytes=0) is None


# ---------------------------------------------------------------------------
# The derivation, which is what decides the form and the membership
# ---------------------------------------------------------------------------


def test_a_body_derives_the_form_its_own_records_demonstrate() -> None:
    """The prefixed form, derived off a body that writes it and nothing else."""
    prefix = objects.REFERENCE_LIST_ENTRY_PREFIX_BYTES
    payloads = (
        _carrier_payload(entry_prefix_bytes=prefix),
        _carrier_payload(entry_prefix_bytes=prefix, paths=(_PATH_B, _PATH_C)),
    )
    body, offsets = _body_of(payloads)
    records = tuple(
        _record_for(payload, body_offset=offset)
        for payload, offset in zip(payloads, offsets, strict=True)
    )

    derived = objects.derive_reference_list_classes(body, records)

    assert dict(derived) == {objects.class_name_of(_CARRIER_TYPE_PATH): prefix}


def test_a_bare_body_derives_the_bare_form() -> None:
    """And the other form, from a body that writes only that one."""
    payloads = (
        _carrier_payload(entry_prefix_bytes=0),
        _carrier_payload(entry_prefix_bytes=0, paths=(_PATH_B, _PATH_C)),
    )
    body, offsets = _body_of(payloads)
    records = tuple(
        _record_for(payload, body_offset=offset)
        for payload, offset in zip(payloads, offsets, strict=True)
    )

    derived = objects.derive_reference_list_classes(body, records)

    assert dict(derived) == {objects.class_name_of(_CARRIER_TYPE_PATH): 0}


def test_a_class_whose_records_disagree_about_the_form_derives_nothing() -> None:
    """THE ANTI-VACUITY PROPERTY. One class writes one form per body, or none.

    A reader taking each record at whichever width happened to fit would admit
    every mixture, which is arithmetic wearing a derivation's clothes.
    """
    payloads = (
        _carrier_payload(entry_prefix_bytes=0),
        _carrier_payload(entry_prefix_bytes=objects.REFERENCE_LIST_ENTRY_PREFIX_BYTES),
    )
    body, offsets = _body_of(payloads)
    records = tuple(
        _record_for(payload, body_offset=offset)
        for payload, offset in zip(payloads, offsets, strict=True)
    )

    assert dict(objects.derive_reference_list_classes(body, records)) == {}


def test_a_class_whose_remainder_is_not_a_list_derives_nothing() -> None:
    """A body that stops demonstrating the grammar says so rather than going green."""
    payload = synthetic.tagged_property_payload(
        (), trailing=struct.pack("<i", 0) + b"\x5a" * _OPAQUE_REMAINDER_BYTES
    )
    body, offsets = _body_of((payload,))
    records = (_record_for(payload, body_offset=offsets[0]),)

    assert dict(objects.derive_reference_list_classes(body, records)) == {}


def test_a_remainder_that_reads_at_both_forms_derives_nothing() -> None:
    """AMBIGUITY IS REFUSED RATHER THAN RESOLVED BY ORDER.

    Unlike the reference PAIR, whose string walk is fixed so at most one tail
    width can reach the declared end, the two forms here start their walks at
    different offsets and nothing structural forbids both landing. This run is
    CONSTRUCTED so that both do - and the SHIPPED reader is what says so, in
    the two assertions below, so the arm cannot pass because the construction
    stopped working. The derivation then takes neither.
    """
    run = _ambiguous_run()
    reads = tuple(
        width
        for width in objects.REFERENCE_LIST_ENTRY_PREFIX_WIDTHS
        if objects.read_reference_list(run, 0, len(run), entry_prefix_bytes=width) is not None
    )
    assert reads == objects.REFERENCE_LIST_ENTRY_PREFIX_WIDTHS

    payload = synthetic.tagged_property_payload((), trailing=struct.pack("<i", 0) + run)
    body, offsets = _body_of((payload,))
    records = (_record_for(payload, body_offset=offsets[0]),)

    assert dict(objects.derive_reference_list_classes(body, records)) == {}


def _ambiguous_run() -> bytes:
    """A remainder the shipped reader admits at BOTH shipped widths.

    HOW IT WORKS, because a magic byte string in a fixture is unreadable. Read
    at the BARE width the entry's first string starts at byte 4 and is nine
    bytes wide; read at the PREFIXED width those first four bytes are skipped
    as the scalar and the string starts at byte 8, five bytes wide. Both walks
    arrive at the SAME offset for the second string, so both land exactly on
    the same declared end. Every length here is written into the bytes rather
    than assumed by either reader, which is precisely why order alone cannot
    decide between them.

    Returns:
        The ambiguous run's bytes.
    """
    inner = struct.pack("<i", 5) + b"abcd\x00"
    first = struct.pack("<i", len(inner)) + inner
    second = struct.pack("<i", 6) + b"efghi\x00"
    return struct.pack("<i", 1) + first + second


def test_one_class_deriving_does_not_derive_another() -> None:
    """`AND NOWHERE ELSE`, on the derivation rather than on the reading."""
    carrier = _carrier_payload(entry_prefix_bytes=0)
    other = synthetic.tagged_property_payload(
        (), trailing=struct.pack("<i", 0) + b"\x5a" * _OPAQUE_REMAINDER_BYTES
    )
    body, offsets = _body_of((carrier, other))
    records = (
        _record_for(carrier, body_offset=offsets[0]),
        _record_for(other, type_path=_OTHER_TYPE_PATH, body_offset=offsets[1]),
    )

    derived = objects.derive_reference_list_classes(body, records)

    assert objects.class_name_of(_CARRIER_TYPE_PATH) in derived
    assert objects.class_name_of(_OTHER_TYPE_PATH) not in derived


# ---------------------------------------------------------------------------
# The seam - the vocabulary is a gate on the reading and never the reading
# ---------------------------------------------------------------------------


def test_naming_a_class_does_not_zero_a_remainder_that_does_not_read() -> None:
    """A derivation that named everything would close nothing."""
    payload = synthetic.tagged_property_payload(
        (), trailing=struct.pack("<i", 0) + b"\x5a" * _OPAQUE_REMAINDER_BYTES
    )
    body, offsets = _body_of((payload,))
    record = _record_for(payload, body_offset=offsets[0])

    result = objects.read_properties(
        body, record, reference_list_classes={objects.class_name_of(_CARRIER_TYPE_PATH): 0}
    )

    assert result.trailing_run is not None
    assert result.trailing_run.reference_list is None
    assert result.trailing_run.unread == _OPAQUE_REMAINDER_BYTES


def test_a_derived_carrier_has_its_remainder_read_down_to_zero() -> None:
    """THE CLAUSE, on one synthetic carrier."""
    payload = _carrier_payload(entry_prefix_bytes=0)
    body, offsets = _body_of((payload,))
    record = _record_for(payload, body_offset=offsets[0])

    result = objects.read_properties(
        body, record, reference_list_classes={objects.class_name_of(_CARRIER_TYPE_PATH): 0}
    )

    assert result.trailing_run is not None
    assert result.trailing_run.reference_list is not None
    assert result.trailing_run.unread == 0


def test_an_undeclared_vocabulary_leaves_the_remainder_where_cs_828_left_it() -> None:
    """THE DEFAULT MEANS `READ LESS`, and it is graded so nobody rediscovers it.

    A caller that has not derived reads exactly what CS-828 left, which is why
    the library sweep in ``tests/save/test_trailing_run.py`` takes every
    vocabulary as a REQUIRED keyword.
    """
    payload = _carrier_payload(entry_prefix_bytes=0)
    body, offsets = _body_of((payload,))
    record = _record_for(payload, body_offset=offsets[0])

    result = objects.read_properties(body, record)

    assert result.trailing_run is not None
    assert result.trailing_run.reference_list is None
    assert result.trailing_run.unread > 0


def test_the_shipped_default_vocabulary_is_empty() -> None:
    """The three shipped names exist and the DEFAULT vocabulary names no class.

    **THIS IS NOT THE NO-TRANSCRIPTION FENCE AND MUST NOT BE CITED AS IT.** It
    cannot see a hand-written allowlist added beside the default; what it sees
    is that the default itself is empty, which is what makes `a caller that has
    not derived reads what CS-828 left` a checked statement rather than a
    promise.

    NEEDS NO SAVE LIBRARY - it is a claim about the shipped module's source.
    """
    source = Path(objects.__file__).read_text(encoding="utf-8")
    shipped = {
        name
        for name in (
            "_NO_REFERENCE_LIST_CLASSES",
            "REFERENCE_LIST_ENTRY_PREFIX_WIDTHS",
            "REFERENCE_LIST_ENTRY_PREFIX_BYTES",
        )
        if name in source
    }

    assert shipped == {
        "_NO_REFERENCE_LIST_CLASSES",
        "REFERENCE_LIST_ENTRY_PREFIX_WIDTHS",
        "REFERENCE_LIST_ENTRY_PREFIX_BYTES",
    }
    assert dict(objects._NO_REFERENCE_LIST_CLASSES) == {}  # noqa: SLF001


# ---------------------------------------------------------------------------
# The library half. COUNTS ONLY, and it skips where there is no library.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _ListSweep:
    """What the library sweep observed. INTEGERS ONLY, never a class name.

    Attributes:
        derived_classes: How many classes the corpus derived as carriers.
        carrier_payloads: Payloads of a derived class that had a remainder.
        carrier_unread: Of those, how many still carry unread bytes. THE CLAUSE:
            the remainder falls to zero on that class's payloads, so this is
            graded at zero.
        other_payloads: Payloads of every other class that had a remainder.
        other_touched: Of those, how many the reading touched. `AND NOWHERE
            ELSE`, so this too is graded at zero.
        entry_forms: How many distinct per-entry prefix widths the corpus
            derived. Graded above one: a corpus deriving a single form
            everywhere would make the per-body derivation indistinguishable
            from a constant.
        failures: The type names of any unexpected failure.
    """

    derived_classes: int
    carrier_payloads: int
    carrier_unread: int
    other_payloads: int
    other_touched: int
    entry_forms: int
    failures: tuple[str, ...]


def _library_save_paths() -> tuple[Path, ...]:
    """Every save file on this machine, or an empty tuple.

    IT HOLDS EVERY ``Exception`` AND EVERY ``SystemExit``, and every discovery
    call sits INSIDE the ``try``: the account directory's NAME is the platform
    account id, and a failure unwinding through a frame that holds it is an echo
    path under non-negotiable 3.

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
def _sweep_reference_lists() -> _ListSweep | None:
    """Read every save's reference lists, COUNTS ONLY.

    Returns:
        The sweep, or None when no save library is reachable.
    """
    saves = _library_save_paths()
    if not saves:
        return None

    derived_classes = 0
    carrier_payloads = 0
    carrier_unread = 0
    other_payloads = 0
    other_touched = 0
    entry_forms: set[int] = set()
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
        if pair not in objects.MEASURED_BODY_LAYOUTS or pair not in objects.TRAILING_RUN_PAIRS:
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
            carriers = objects.derive_reference_list_classes(
                body,
                table.records,
                save_version=parsed.save_version,
                header_version=parsed.header_version,
            )
            derived_classes = max(derived_classes, len(carriers))
            entry_forms.update(carriers.values())
            for record in table.records:
                if not record.body_length:
                    continue
                result = objects.read_properties(
                    body,
                    record,
                    save_version=parsed.save_version,
                    header_version=parsed.header_version,
                    reference_list_classes=carriers,
                )
                run = result.trailing_run
                if run is None or run.lead is None:
                    continue
                if objects.class_name_of(record.type_path) in carriers:
                    carrier_payloads += 1
                    carrier_unread += 1 if run.unread else 0
                elif run.reference_list is not None:
                    other_payloads += 1
                    other_touched += 1
                elif run.width > objects.TRAILING_RUN_LEAD_BYTES:
                    other_payloads += 1
        except (Exception, SystemExit) as exc:
            failures.append(type(exc).__name__)
            continue
    return _ListSweep(
        derived_classes=derived_classes,
        carrier_payloads=carrier_payloads,
        carrier_unread=carrier_unread,
        other_payloads=other_payloads,
        other_touched=other_touched,
        entry_forms=len(entry_forms),
        failures=tuple(sorted(set(failures))),
    )


def _sweep_or_skip() -> _ListSweep:
    """The sweep, or a skip when this machine has no library.

    Returns:
        The sweep.
    """
    sweep = _sweep_reference_lists()
    if sweep is None:
        pytest.skip("no save library on this machine")
    return sweep


def test_the_corpus_derives_at_least_one_carrier() -> None:
    """THE NON-VACUITY CONTROL. Every arm below is vacuous without this one."""
    sweep = _sweep_or_skip()

    assert sweep.failures == ()
    assert sweep.derived_classes >= 1
    assert sweep.carrier_payloads >= 1


def test_the_corpus_derives_more_than_one_entry_form() -> None:
    """THE ARM THAT MAKES THE DERIVATION WORTH HAVING.

    If every body derived the same width, a shipped constant would do and the
    per-body derivation would be ceremony. That the corpus derives EVERY width
    the shipped set allows is the measurement that says the form is a property
    of the body - and the expectation is read off that set rather than written
    down here, so widening the set without measuring it reddens this arm.
    """
    sweep = _sweep_or_skip()

    assert sweep.failures == ()
    assert sweep.entry_forms == len(objects.REFERENCE_LIST_ENTRY_PREFIX_WIDTHS)


def test_every_derived_carrier_payload_has_its_remainder_read() -> None:
    """THE CLAUSE, on the population the derivation names."""
    sweep = _sweep_or_skip()

    assert sweep.failures == ()
    assert sweep.carrier_unread == 0


def test_no_payload_outside_the_derived_classes_is_touched() -> None:
    """AND NOWHERE ELSE - the half that makes the reading falsifiable."""
    sweep = _sweep_or_skip()

    assert sweep.failures == ()
    assert sweep.other_payloads >= 1
    assert sweep.other_touched == 0


# ---------------------------------------------------------------------------
# Containment
# ---------------------------------------------------------------------------


def test_every_library_reaching_function_here_is_declared() -> None:
    """The reach guard, keyed on the RISKY primitives rather than the safe route.

    NEEDS NO SAVE LIBRARY - it is a claim about this module's source.
    """
    reach_guard._assert_library_reach_is_declared(  # noqa: SLF001
        Path(__file__), graded=_GRADED_LIBRARY_REACH, exempt=_EXEMPT_LIBRARY_REACH
    )
