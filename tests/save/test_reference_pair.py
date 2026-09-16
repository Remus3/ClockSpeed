"""The object-reference pair inside a payload's trailing run - CS-828.

WHAT THIS MODULE GRADES.

CS-828 read the int32 the trailing run OPENS with; CS-1068 then read one derived
class set's remainder as a count-prefixed item list. This module grades the NEXT
shape the remainder takes - FOUR length-prefixed strings forming TWO object
references, optionally followed by a fixed-width tail - and the derivation that
decides which classes carry it and which of the two forms a body writes.

**THE WIDTH IS DERIVED, NEVER OBSERVED, AND THAT IS THE WHOLE CLAUSE.** The
remainder's width is whatever the bytes are, so ANY partition of it sums to the
declared end and no reading of it could have failed - the defect that refuted
CS-830 after it had merged. Every width this reader consumes therefore comes out
of the bytes or out of a shipped constant: each string's own length prefix says
how wide it is, and the tail is one of the two widths
:data:`clockspeed.save.objects.REFERENCE_PAIR_TAIL_WIDTHS` allows. The declared
end is a BOUND and a VALIDATION and never a source of width, and
:func:`test_the_width_is_derived_from_the_prefixes_and_not_from_the_declared_end`
is the arm that goes red when that is swapped.

**THE TAIL IS NOT AN UNCONDITIONAL SUFFIX, AND A READER THAT ASSUMED IT WAS
WOULD OVER-READ.** The prose CS-1068's ledger entry left behind describes this
shape as two references "followed by a 24-byte tail". Measured on this project's
library that is true of one schema and FALSE of two others, which write the same
two references and stop. So the FORM is derived per body from the body's own
records - every remainder-bearing record of a carrying class must land on the
SAME one of the two - and a class whose records disagree derives nothing rather
than being read at whichever width happened to fit.

**THE CARRYING CLASSES ARE DERIVED FROM THE CORPUS, NEVER TRANSCRIBED.** A
hand-written vocabulary of game content is the thing that rots, and CS-829's
note forbids exactly that shape.
:func:`test_no_class_vocabulary_is_transcribed_into_the_shipped_reader` holds the
shipped module to it.

THE LIBRARY HALF REPORTS COUNTS ONLY, contained exactly as
``tests/save/test_item_list.py`` contains its own: every step wrapped, every
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
        "_sweep_reference_pairs": "reads and parses every save in the library",
    }
)

#: Reaches or touches a primitive without being a grader-able library helper,
#: name to why. EMPTY, AND DELIBERATELY SO - see the same declaration in
#: ``tests/save/test_item_list.py`` for why a placeholder here turns the module
#: red rather than green.
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
_CARRIER_TYPE_PATH: Final = "/Synthetic/Carrier.Synthetic_RefCarrier_C"
_OTHER_TYPE_PATH: Final = "/Synthetic/Other.Synthetic_RefOther_C"

#: The generic level name a real body also carries. A GAME CONSTANT rather than
#: personal data, and reused here so the fixture has the shape of the thing.
_LEVEL: Final = synthetic.MAP_NAME

#: Two invented object paths. Neither is a real one.
_PATH_A: Final = "Persistent_Level:PersistentLevel.Synthetic_RefCarrier_C_0"
_PATH_B: Final = "Persistent_Level:PersistentLevel.Synthetic_RefCarrier_C_1"

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


def _pair_bytes(*, tail_bytes: int, paths: Sequence[str] = (_PATH_A, _PATH_B)) -> bytes:
    """A whole reference pair, with the tail form the caller asks for.

    Args:
        tail_bytes: How wide a tail to write after the references.
        paths: The two object paths, in file order.

    Returns:
        The remainder's bytes.
    """
    return (
        _reference_bytes(_LEVEL, paths[0])
        + _reference_bytes(_LEVEL, paths[1])
        + b"\x5a" * tail_bytes
    )


def _derived_width(*, tail_bytes: int, paths: Sequence[str] = (_PATH_A, _PATH_B)) -> int:
    """The width the PREFIXES describe, computed the long way round.

    A SECOND ENUMERATION SHARING NO CONSTANT WITH THE READER's own arithmetic -
    it is summed from the fixture's own strings here rather than read off the
    result, so an arm comparing the two grades the reader instead of itself.

    Args:
        tail_bytes: How wide a tail the fixture wrote.
        paths: The two object paths, in file order.

    Returns:
        The width in bytes.
    """
    strings = (_LEVEL, paths[0], _LEVEL, paths[1])
    return sum(objects.INT32_SIZE + len(text.encode("utf-8")) + 1 for text in strings) + tail_bytes


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


def _carrier_payload(*, tail_bytes: int, paths: Sequence[str] = (_PATH_A, _PATH_B)) -> bytes:
    """A terminated payload whose trailing run carries a lead and a pair.

    Args:
        tail_bytes: How wide a tail to write after the references.
        paths: The two object paths, in file order.

    Returns:
        The payload's bytes.
    """
    return synthetic.tagged_property_payload(
        (),
        trailing=struct.pack("<i", 0) + _pair_bytes(tail_bytes=tail_bytes, paths=paths),
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

    Where the declared end is where the prefixes say it is, the pair reads.
    Moved out past them, it is REFUSED - which is exactly the outcome that
    inverts when the derivation is swapped for :func:`_width_from_observation`.
    """
    run = _pair_bytes(tail_bytes=0)
    honest_end = len(run)
    stretched_end = honest_end + 8

    read = objects.read_reference_pair(run + b"\x00" * 8, 0, honest_end, tail_bytes=0)
    stretched = objects.read_reference_pair(run + b"\x00" * 8, 0, stretched_end, tail_bytes=0)

    assert read is not None
    assert read.width == _derived_width(tail_bytes=0)
    assert read.width != _width_from_observation(0, stretched_end)
    assert stretched is None


def test_a_pair_reads_both_references_out_of_their_own_prefixes() -> None:
    """The reading this cycle ships, on a run whose prefixes describe it exactly."""
    run = _pair_bytes(tail_bytes=0)

    read = objects.read_reference_pair(run, 0, len(run), tail_bytes=0)

    assert read is not None
    assert len(read.references) == objects.REFERENCE_PAIR_COUNT
    assert tuple(ref.object_path for ref in read.references) == (_PATH_A, _PATH_B)
    assert tuple(ref.level_reference for ref in read.references) == (_LEVEL, _LEVEL)
    assert read.tail_bytes == 0
    assert read.width == _derived_width(tail_bytes=0)


def test_the_tail_form_consumes_the_shipped_width_and_lands_exactly() -> None:
    """The other form: the same two references, then the fixed-width tail."""
    tail = objects.REFERENCE_PAIR_TAIL_BYTES
    run = _pair_bytes(tail_bytes=tail)

    read = objects.read_reference_pair(run, 0, len(run), tail_bytes=tail)

    assert read is not None
    assert read.tail_bytes == tail
    assert read.width == _derived_width(tail_bytes=tail)


def test_reading_the_tail_form_at_the_tailless_width_is_refused() -> None:
    """The two forms are not interchangeable, and the reader says so.

    A reader that took its width from the declared end would read BOTH, which
    is the whole reason the form is derived rather than observed.
    """
    tail = objects.REFERENCE_PAIR_TAIL_BYTES
    run = _pair_bytes(tail_bytes=tail)

    assert objects.read_reference_pair(run, 0, len(run), tail_bytes=0) is None


def test_reading_the_tailless_form_at_the_tail_width_is_refused() -> None:
    """And the same from the other side."""
    run = _pair_bytes(tail_bytes=0)

    read = objects.read_reference_pair(
        run, 0, len(run), tail_bytes=objects.REFERENCE_PAIR_TAIL_BYTES
    )

    assert read is None


def test_a_run_of_zero_bytes_is_not_four_empty_strings() -> None:
    """Sixteen zero bytes would read as four empty strings if empties were let through.

    That is the CS-1068 lesson transferred: an empty string is four zero bytes,
    so a reader admitting them would read a run of zeroes as a reference pair
    and `and nowhere else` would be false.
    """
    run = b"\x00" * (objects.INT32_SIZE * objects.REFERENCE_PAIR_STRINGS)

    assert objects.read_reference_pair(run, 0, len(run), tail_bytes=0) is None


def test_a_length_prefix_reaching_past_the_payload_is_refused() -> None:
    """A prefix claiming more than the payload holds is REPORTED, never raised."""
    run = _pair_bytes(tail_bytes=0)
    overlong = struct.pack("<i", len(run) * 4) + run[objects.INT32_SIZE :]

    assert objects.read_reference_pair(overlong, 0, len(overlong), tail_bytes=0) is None


def test_a_run_too_short_for_four_strings_is_refused() -> None:
    """Three strings and a stub is not a pair."""
    run = _reference_bytes(_LEVEL, _PATH_A) + synthetic.fstring(_LEVEL)

    assert objects.read_reference_pair(run, 0, len(run), tail_bytes=0) is None


def test_an_unaddressable_window_is_reported_rather_than_raised() -> None:
    """Non-negotiable 7: a window outside the buffer is no pair, not an exception."""
    run = _pair_bytes(tail_bytes=0)

    assert objects.read_reference_pair(run, -1, len(run), tail_bytes=0) is None
    assert objects.read_reference_pair(run, 0, len(run) + 1, tail_bytes=0) is None


def test_the_reading_withholds_its_strings_from_its_repr() -> None:
    """A reference read out of a save names game content, so the repr counts it.

    ``tests/save/test_item_list.py`` holds
    :class:`clockspeed.save.objects.ItemList` to the same rule, for the same
    reason.
    """
    run = _pair_bytes(tail_bytes=0)

    read = objects.read_reference_pair(run, 0, len(run), tail_bytes=0)

    assert read is not None
    rendered = repr(read)
    assert _PATH_A not in rendered
    assert _PATH_B not in rendered
    assert _LEVEL not in rendered
    assert str(read.width) in rendered


def test_each_reference_withholds_its_strings_from_its_own_repr() -> None:
    """A SEPARATE ARM, because the pair's repr does not recurse into its members.

    :meth:`clockspeed.save.objects.ReferencePair.__repr__` renders a COUNT of
    its references, so the arm above cannot see a member that leaked - an
    adversary found exactly that gap. This one reprs the member itself.
    """
    run = _pair_bytes(tail_bytes=0)
    read = objects.read_reference_pair(run, 0, len(run), tail_bytes=0)

    assert read is not None
    for reference in read.references:
        rendered = repr(reference)
        assert reference.level_reference not in rendered
        assert reference.object_path not in rendered
        assert type(reference).__name__ in rendered
        assert rendered != f"{type(reference).__name__}()"


# ---------------------------------------------------------------------------
# The derivation, which is what makes the form a measurement
# ---------------------------------------------------------------------------


def test_a_body_derives_the_form_its_own_records_demonstrate() -> None:
    """The form comes off the body, not off a transcribed version table."""
    tail = objects.REFERENCE_PAIR_TAIL_BYTES
    payloads = [_carrier_payload(tail_bytes=tail) for _ in range(3)]
    body, offsets = _body_of(payloads)
    records = tuple(
        _record_for(payload, body_offset=offset)
        for payload, offset in zip(payloads, offsets, strict=True)
    )

    derived = objects.derive_reference_pair_classes(body, records)

    assert derived == {objects.class_name_of(_CARRIER_TYPE_PATH): tail}


def test_a_tailless_body_derives_the_tailless_form() -> None:
    """The same derivation, on the schema that writes no tail."""
    payloads = [_carrier_payload(tail_bytes=0) for _ in range(3)]
    body, offsets = _body_of(payloads)
    records = tuple(
        _record_for(payload, body_offset=offset)
        for payload, offset in zip(payloads, offsets, strict=True)
    )

    derived = objects.derive_reference_pair_classes(body, records)

    assert derived == {objects.class_name_of(_CARRIER_TYPE_PATH): 0}


def test_a_class_whose_records_disagree_about_the_form_derives_nothing() -> None:
    """THE ANTI-VACUITY ARM. Consistency across the class is what makes it a form.

    A reader picking whichever width happened to fit each record would read both
    of these, which is arithmetic wearing a derivation's clothes. One class
    writes one form per body or it writes a form this reader does not know.
    """
    payloads = [
        _carrier_payload(tail_bytes=objects.REFERENCE_PAIR_TAIL_BYTES),
        _carrier_payload(tail_bytes=0),
    ]
    body, offsets = _body_of(payloads)
    records = tuple(
        _record_for(payload, body_offset=offset)
        for payload, offset in zip(payloads, offsets, strict=True)
    )

    derived = objects.derive_reference_pair_classes(body, records)

    assert derived == {}


def test_a_class_whose_remainder_is_not_a_pair_derives_nothing() -> None:
    """A body that stops carrying the shape says so rather than going green."""
    payload = synthetic.tagged_property_payload(
        (), trailing=struct.pack("<i", 0) + b"\x5a" * _OPAQUE_REMAINDER_BYTES
    )
    body, offsets = _body_of([payload])
    records = (_record_for(payload, body_offset=offsets[0]),)

    assert objects.derive_reference_pair_classes(body, records) == {}


def test_one_class_deriving_does_not_derive_another() -> None:
    """The vocabulary is per class, and a bystander is not swept in with a carrier."""
    carrier = _carrier_payload(tail_bytes=0)
    bystander = synthetic.tagged_property_payload(
        (), trailing=struct.pack("<i", 0) + b"\x5a" * _OPAQUE_REMAINDER_BYTES
    )
    body, offsets = _body_of([carrier, bystander])
    records = (
        _record_for(carrier, body_offset=offsets[0]),
        _record_for(bystander, type_path=_OTHER_TYPE_PATH, body_offset=offsets[1]),
    )

    derived = objects.derive_reference_pair_classes(body, records)

    assert derived == {objects.class_name_of(_CARRIER_TYPE_PATH): 0}


def test_naming_a_class_does_not_zero_a_remainder_that_does_not_read() -> None:
    """THE VOCABULARY IS A GATE ON THE READING AND NEVER THE READING ITSELF.

    A class named as a carrier whose bytes do not read comes back exactly as
    CS-828 left it. A derivation that named everything would close nothing, and
    that is what keeps the measurement a measurement.
    """
    payload = synthetic.tagged_property_payload(
        (), trailing=struct.pack("<i", 0) + b"\x5a" * _OPAQUE_REMAINDER_BYTES
    )
    body, offsets = _body_of([payload])
    record = _record_for(payload, body_offset=offsets[0])

    result = objects.read_properties(
        body, record, reference_pair_classes={objects.class_name_of(_CARRIER_TYPE_PATH): 0}
    )

    assert result.trailing_run is not None
    assert result.trailing_run.references is None
    assert result.trailing_run.unread == _OPAQUE_REMAINDER_BYTES


def test_a_derived_carrier_has_its_remainder_read_down_to_zero() -> None:
    """End to end: derive off the body, then read, and the remainder falls."""
    tail = objects.REFERENCE_PAIR_TAIL_BYTES
    payloads = [_carrier_payload(tail_bytes=tail) for _ in range(2)]
    body, offsets = _body_of(payloads)
    records = tuple(
        _record_for(payload, body_offset=offset)
        for payload, offset in zip(payloads, offsets, strict=True)
    )
    derived = objects.derive_reference_pair_classes(body, records)

    result = objects.read_properties(body, records[0], reference_pair_classes=derived)

    assert result.trailing_run is not None
    assert result.trailing_run.references is not None
    assert result.trailing_run.unread == 0


def test_an_undeclared_vocabulary_leaves_the_remainder_where_cs_828_left_it() -> None:
    """DEFAULTED EMPTY, so a caller that has not derived reads exactly as before."""
    tail = objects.REFERENCE_PAIR_TAIL_BYTES
    payload = _carrier_payload(tail_bytes=tail)
    body, offsets = _body_of([payload])
    record = _record_for(payload, body_offset=offsets[0])

    result = objects.read_properties(body, record)

    assert result.trailing_run is not None
    assert result.trailing_run.references is None
    assert result.trailing_run.unread == _derived_width(tail_bytes=tail)


def test_no_class_vocabulary_is_transcribed_into_the_shipped_reader() -> None:
    """CS-829's fence, applied here: the carriers are derived, never written down.

    The shipped module must not name a real game class. The check is the same
    one ``tests/save/test_item_list.py`` runs for the item-list vocabulary.
    """
    source = Path(objects.__file__).read_text(encoding="utf-8")

    assert "Build_PowerLine" not in source
    assert "FGConveyorChainActor" not in source


# ---------------------------------------------------------------------------
# The library half - skip-if-absent, COUNTS ONLY
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _PairSweep:
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
        tail_forms: How many distinct tail widths the corpus derived. Graded
            above one: a corpus deriving a single form everywhere would make
            the per-body derivation indistinguishable from a constant.
        failures: The type names of any unexpected failure.
    """

    derived_classes: int
    carrier_payloads: int
    carrier_unread: int
    other_payloads: int
    other_touched: int
    tail_forms: int
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
def _sweep_reference_pairs() -> _PairSweep | None:
    """Read every save's reference pairs, COUNTS ONLY.

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
    tail_forms: set[int] = set()
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
            carriers = objects.derive_reference_pair_classes(
                body,
                table.records,
                save_version=parsed.save_version,
                header_version=parsed.header_version,
            )
            derived_classes = max(derived_classes, len(carriers))
            tail_forms.update(carriers.values())
            for record in table.records:
                if not record.body_length:
                    continue
                result = objects.read_properties(
                    body,
                    record,
                    save_version=parsed.save_version,
                    header_version=parsed.header_version,
                    reference_pair_classes=carriers,
                )
                run = result.trailing_run
                if run is None or run.lead is None:
                    continue
                if objects.class_name_of(record.type_path) in carriers:
                    carrier_payloads += 1
                    carrier_unread += 1 if run.unread else 0
                elif run.references is not None:
                    other_payloads += 1
                    other_touched += 1
                elif run.width > objects.TRAILING_RUN_LEAD_BYTES:
                    other_payloads += 1
        except (Exception, SystemExit) as exc:
            failures.append(type(exc).__name__)
            continue
    return _PairSweep(
        derived_classes=derived_classes,
        carrier_payloads=carrier_payloads,
        carrier_unread=carrier_unread,
        other_payloads=other_payloads,
        other_touched=other_touched,
        tail_forms=len(tail_forms),
        failures=tuple(sorted(set(failures))),
    )


def _sweep_or_skip() -> _PairSweep:
    """The sweep, or a skip when this machine has no library.

    Returns:
        The sweep.
    """
    sweep = _sweep_reference_pairs()
    if sweep is None:
        pytest.skip("no save library on this machine")
    return sweep


def test_the_corpus_derives_at_least_one_carrier() -> None:
    """THE NON-VACUITY CONTROL. Every arm below is vacuous without this one."""
    sweep = _sweep_or_skip()

    assert sweep.failures == ()
    assert sweep.derived_classes >= 1
    assert sweep.carrier_payloads >= 1


def test_the_corpus_derives_more_than_one_tail_form() -> None:
    """THE ARM THAT MAKES THE DERIVATION WORTH HAVING.

    If every body derived the same width, a shipped constant would do and the
    per-body derivation would be ceremony. That the corpus derives EVERY width
    the shipped set allows is the measurement that says the form is a property
    of the body - and the expectation is read off that set rather than written
    down here, so widening the set without measuring it reddens this arm.
    """
    sweep = _sweep_or_skip()

    assert sweep.failures == ()
    assert sweep.tail_forms == len(objects.REFERENCE_PAIR_TAIL_WIDTHS)


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
