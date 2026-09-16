"""The count-prefixed item list inside a payload's trailing run - CS-1068.

WHAT THIS MODULE GRADES.

CS-828 read the int32 the trailing run OPENS with and left everything past it
carried as :attr:`clockspeed.save.objects.TrailingRun.unread`. That remainder is
CLASS-KEYED rather than pair-keyed: one class writes a count prefix followed by
that many records, another writes length-prefixed references, another writes
nothing at all. This module grades the first reading of one such class's
remainder - the COUNT-PREFIXED ITEM LIST - and the derivation that decides which
classes carry it.

**THE WIDTH IS DERIVED, NEVER OBSERVED, AND THAT IS THE WHOLE CLAUSE.** The
remainder's width is whatever the bytes are, so ANY partition of it sums to the
declared end and no reading of it could have failed - the defect that refuted
CS-830 after it had merged. Every width this reader consumes therefore comes out
of the bytes themselves: the count prefix says how many entries follow, each
entry's own length prefix says how wide its class path is, and the two
fixed-width fields are shipped constants. The declared end is used as a BOUND
and as a VALIDATION and never as a source of width, and
:func:`test_the_width_is_derived_from_the_prefixes_and_not_from_the_declared_end`
is the arm that goes red when that is swapped.

**THE CARRYING CLASSES ARE DERIVED FROM THE CORPUS, NEVER TRANSCRIBED.** A
hand-written vocabulary of game content is the thing that rots, and CS-829's
note forbids exactly that shape. The classes are picked off the save at read
time - a class that DEMONSTRATES the grammar with a non-empty list is a class
whose empty lists are then read too - so a corpus that stops carrying one says
so by deriving nothing rather than by going quietly green.
:func:`test_no_class_vocabulary_is_transcribed_into_the_shipped_reader` holds
the shipped module to it.

THE LIBRARY HALF REPORTS COUNTS ONLY, contained exactly as
``tests/save/test_trailing_run.py`` contains its own: every step wrapped, every
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
        "_sweep_item_lists": "reads and parses every save in the library",
    }
)

#: Reaches or touches a primitive without being a grader-able library helper,
#: name to why. EMPTY, AND DELIBERATELY SO - see the same declaration in
#: ``tests/save/test_trailing_run.py`` for why a placeholder here turns the
#: module red rather than green.
_EXEMPT_LIBRARY_REACH: Final[Mapping[str, str]] = MappingProxyType({})

_BODY_PREFIX: bytes = b"\xab" * 16
_BODY_SUFFIX: bytes = b"\xcd" * 16

#: The object-type discriminator each kind is written with, DERIVED from the
#: shipped map rather than transcribed.
_OBJECT_TYPE_BY_KIND: dict[str, int] = {
    kind: value
    for value, kind in objects._KIND_BY_OBJECT_TYPE.items()  # noqa: SLF001
}

#: The class path the synthetic carrier record is written with. A SYNTHETIC
#: NAME, never a real one - test fixtures are hand-authored and never slices of
#: real game data (CLAUDE.md section 7).
_CARRIER_TYPE_PATH: Final = "/Synthetic/Carrier.Synthetic_Carrier_C"
_BYSTANDER_TYPE_PATH: Final = "/Synthetic/Bystander.Synthetic_Bystander_C"

#: How wide the deliberately unreadable remainder of the named-but-unreadable
#: fixture is. ANY width the grammar cannot read would do - what the arm grades
#: is that the width comes back untouched.
_OPAQUE_REMAINDER_BYTES: Final = 12


def _entry_bytes(item_class: str) -> bytes:
    """One item-list entry, written the way the corpus writes one.

    Args:
        item_class: The entry's class path.

    Returns:
        The entry's bytes.
    """
    return (
        struct.pack("<i", 0)
        + synthetic.fstring(item_class)
        + b"\x00" * objects.ITEM_LIST_ENTRY_TAIL_BYTES
    )


def _item_list_bytes(item_classes: Sequence[str], *, declared: int | None = None) -> bytes:
    """A whole count-prefixed item list.

    Args:
        item_classes: One class path per entry.
        declared: The count to WRITE, when it should differ from the number of
            entries actually written. That divergence is what the derivation
            arms need: a reader taking its width from the declared end cannot
            tell the two apart.

    Returns:
        The list's bytes.
    """
    count = len(item_classes) if declared is None else declared
    return struct.pack("<i", count) + b"".join(_entry_bytes(name) for name in item_classes)


def _derived_width(item_classes: Sequence[str]) -> int:
    """The width the PREFIXES describe, computed the long way round.

    A SECOND ENUMERATION SHARING NO CONSTANT WITH THE READER's own arithmetic -
    it is summed from the fixture's own strings here rather than read off the
    result, so an arm comparing the two grades the reader instead of itself.

    Args:
        item_classes: One class path per entry.

    Returns:
        The width in bytes.
    """
    per_entry = sum(
        objects.INT32_SIZE
        + objects.INT32_SIZE
        + len(name.encode("utf-8"))
        + 1
        + objects.ITEM_LIST_ENTRY_TAIL_BYTES
        for name in item_classes
    )
    return objects.INT32_SIZE + per_entry


def _width_from_observation(at: int, end: int) -> int:
    """THE FORBIDDEN READING, spelled out so an arm can be swapped onto it.

    This is the width a partition-by-arithmetic reader would take. It closes on
    every payload and no reading of it can fail, which is exactly why CS-1068's
    clause asks for an arm that reddens when the derivation is replaced by it.

    Args:
        at: The remainder's first byte.
        end: The first byte past the payload.

    Returns:
        The observed width.
    """
    return end - at


def _record_for(payload: bytes, *, type_path: str = _CARRIER_TYPE_PATH) -> objects.ObjectRecord:
    """Build the record that attributes ``payload`` inside the synthetic body.

    Args:
        payload: The payload the body will carry.
        type_path: The class path the record declares.

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
        body_offset=len(_BODY_PREFIX),
        body_length=len(payload),
    )


def _carrier_payload(item_classes: Sequence[str], *, declared: int | None = None) -> bytes:
    """A terminated payload whose trailing run carries a lead and an item list.

    Args:
        item_classes: One class path per entry.
        declared: The count to write, when it differs from the entries written.

    Returns:
        The payload's bytes.
    """
    return synthetic.tagged_property_payload(
        (),
        trailing=struct.pack("<i", 0) + _item_list_bytes(item_classes, declared=declared),
    )


# ---------------------------------------------------------------------------
# The reader itself, with no save library anywhere
# ---------------------------------------------------------------------------


def test_a_count_prefixed_run_reads_every_entry() -> None:
    """The reading this item ships, on a run whose prefixes describe it exactly."""
    names = ("Synthetic_Alpha_C", "Synthetic_Beta_C")
    run = _item_list_bytes(names)

    read = objects.read_item_list(run, 0, len(run))

    assert read is not None
    assert read.declared_count == len(names)
    assert tuple(entry.item_class for entry in read.entries) == names
    assert read.width == _derived_width(names)


def test_an_empty_list_reads_the_prefix_and_nothing_else() -> None:
    """A count of zero is a COMPLETE reading of a four-byte remainder.

    It is also why the carrying class cannot be told from the bytes alone: an
    empty list and an unrelated class's four zero bytes are byte-identical,
    which is what makes the derivation below necessary rather than tidy.
    """
    run = _item_list_bytes(())

    read = objects.read_item_list(run, 0, len(run))

    assert read is not None
    assert read.declared_count == 0
    assert read.entries == ()
    assert read.width == objects.INT32_SIZE


def test_the_width_is_derived_from_the_prefixes_and_not_from_the_declared_end() -> None:
    """THE ARM CS-1068's CLAUSE NAMES, and it holds both directions.

    The same bytes are offered twice. Under the DERIVED width the run ends where
    its prefixes say it ends and reads; under a declared end moved out past
    them, a reader taking the width from the declared end would consume the
    padding happily and the shipped reader REFUSES. Swap the derivation for
    :func:`_width_from_observation` and the refusal below becomes a reading.
    """
    names = ("Synthetic_Alpha_C",)
    run = _item_list_bytes(names)
    padded = run + b"\x99" * 16

    assert objects.read_item_list(padded, 0, len(run)) is not None
    assert objects.read_item_list(padded, 0, len(padded)) is None
    # The control: the forbidden reading really would have taken the padding.
    assert _width_from_observation(0, len(padded)) == len(run) + 16


def test_a_declared_count_short_of_the_entries_written_is_refused() -> None:
    """The count PREFIX drives the walk, so a short count leaves bytes over.

    A reader whose width came from the declared end could not notice this at
    all - the bytes fill the run either way.
    """
    names = ("Synthetic_Alpha_C", "Synthetic_Beta_C")
    run = _item_list_bytes(names, declared=1)

    assert objects.read_item_list(run, 0, len(run)) is None


def test_a_declared_count_past_the_entries_written_is_refused() -> None:
    """A count claiming more than the run holds runs out of bytes and refuses."""
    run = _item_list_bytes(("Synthetic_Alpha_C",), declared=2)

    assert objects.read_item_list(run, 0, len(run)) is None


def test_a_negative_count_is_refused() -> None:
    """Nothing here raises - non-negotiable 7 flags and skips."""
    run = struct.pack("<i", -1) + b"\x00" * 16

    assert objects.read_item_list(run, 0, len(run)) is None


def test_a_count_above_the_refusal_ceiling_is_refused() -> None:
    """A ceiling stops a corrupt prefix from driving an unbounded walk.

    THE CEILING IS A REFUSAL, NOT A CLAIM about how many entries a real list
    holds - which is why nothing below compares a corpus count against it.
    """
    run = struct.pack("<i", objects.MAX_ITEM_LIST_ENTRIES + 1) + b"\x00" * 16

    assert objects.read_item_list(run, 0, len(run)) is None


def test_an_entry_whose_length_prefix_overruns_is_refused() -> None:
    """A length prefix reaching past the declared end yields no list."""
    run = struct.pack("<i", 1) + struct.pack("<i", 0) + struct.pack("<i", 4096)

    assert objects.read_item_list(run, 0, len(run)) is None


def test_an_empty_entry_class_is_refused() -> None:
    """A zero-length class path is not an entry.

    Reading one as an entry would make four zero bytes read as an entry
    wherever they appear, which is every class whose whole remainder is the
    lead field and four more.
    """
    run = struct.pack("<i", 1) + struct.pack("<i", 0) + struct.pack("<i", 0)

    assert objects.read_item_list(run, 0, len(run)) is None


def test_a_run_outside_the_buffer_is_refused() -> None:
    """A declared end past the buffer yields no list at all."""
    run = _item_list_bytes(())

    assert objects.read_item_list(run, 0, len(run) + 8) is None


def test_the_entry_repr_withholds_the_class_path() -> None:
    """An entry's class path is WORLD CONTENT and never renders.

    Same rule as :class:`clockspeed.save.objects.ObjectReference`: a repr is an
    echo path, so it carries a length and never a string.
    """
    entry = objects.ItemListEntry(item_class="Synthetic_Alpha_C")

    assert "Synthetic_Alpha_C" not in repr(entry)
    assert str(len("Synthetic_Alpha_C")) in repr(entry)


def test_the_list_repr_withholds_every_entry() -> None:
    """The container renders counts and widths only."""
    rendered = repr(objects.read_item_list(_item_list_bytes(("Synthetic_Alpha_C",)), 0, 33))

    assert "Synthetic_Alpha_C" not in rendered


# ---------------------------------------------------------------------------
# The plumbing - a correct reader nothing calls reads nothing
# ---------------------------------------------------------------------------


def test_the_run_stays_unread_when_the_class_is_not_a_derived_carrier() -> None:
    """THE DEFAULT IS UNCHANGED, which is what keeps `and nowhere else` true.

    Adding this reading could not change what any existing caller reads: with
    no derived vocabulary the remainder is exactly as open as CS-828 left it.
    """
    names = ("Synthetic_Alpha_C",)
    payload = _carrier_payload(names)
    body = _BODY_PREFIX + payload + _BODY_SUFFIX

    run = objects.read_properties(body, _record_for(payload)).trailing_run

    assert run is not None
    assert run.items is None
    assert run.unread == _derived_width(names)


def test_a_derived_carrier_reads_its_run_to_zero() -> None:
    """The remainder falls to zero on a class the derivation named."""
    names = ("Synthetic_Alpha_C", "Synthetic_Beta_C")
    payload = _carrier_payload(names)
    body = _BODY_PREFIX + payload + _BODY_SUFFIX

    run = objects.read_properties(
        body,
        _record_for(payload),
        item_list_classes=frozenset({objects.class_name_of(_CARRIER_TYPE_PATH)}),
    ).trailing_run

    assert run is not None
    assert run.items is not None
    assert run.items.declared_count == len(names)
    assert run.unread == 0


def test_a_named_class_whose_run_does_not_read_keeps_its_remainder() -> None:
    """Naming a class does not ZERO its remainder - the bytes still decide.

    Without this the vocabulary would be the reading rather than the gate on it,
    and a derivation that named everything would close the region by fiat.
    """
    payload = synthetic.tagged_property_payload((), trailing=struct.pack("<i", 0) + b"\x7f" * 12)
    body = _BODY_PREFIX + payload + _BODY_SUFFIX

    run = objects.read_properties(
        body,
        _record_for(payload),
        item_list_classes=frozenset({objects.class_name_of(_CARRIER_TYPE_PATH)}),
    ).trailing_run

    assert run is not None
    assert run.items is None
    assert run.unread == _OPAQUE_REMAINDER_BYTES


def test_the_derivation_names_only_a_class_that_demonstrated_a_non_empty_list() -> None:
    """THE DERIVATION'S OWN ARM, on a synthetic table with two classes.

    One class carries a non-empty list and is derived. The other carries a bare
    four-byte zero - byte-identical to an EMPTY list - and is not, because
    nothing in it demonstrates the grammar. That asymmetry is the whole reason
    the vocabulary is derived from demonstration rather than from a successful
    parse.
    """
    carrier = _carrier_payload(("Synthetic_Alpha_C",))
    bystander = synthetic.tagged_property_payload((), trailing=struct.pack("<ii", 0, 0))
    body = _BODY_PREFIX + carrier + bystander + _BODY_SUFFIX
    carrier_record = _record_for(carrier)
    bystander_record = objects.ObjectRecord(
        kind=objects.KIND_COMPONENT,
        type_path=_BYSTANDER_TYPE_PATH,
        root_object="Synthetic_Root",
        instance_name="Synthetic_Other",
        transform=None,
        parent=None,
        object_type=_OBJECT_TYPE_BY_KIND[objects.KIND_COMPONENT],
        was_placed_in_level=0,
        body_offset=len(_BODY_PREFIX) + len(carrier),
        body_length=len(bystander),
    )

    derived = objects.derive_item_list_classes(body, (carrier_record, bystander_record))

    assert derived == frozenset({objects.class_name_of(_CARRIER_TYPE_PATH)})


def test_the_derivation_is_empty_when_no_class_demonstrates_the_grammar() -> None:
    """A corpus that stops carrying it says so, rather than going green."""
    bystander = synthetic.tagged_property_payload((), trailing=struct.pack("<ii", 0, 0))
    body = _BODY_PREFIX + bystander + _BODY_SUFFIX

    assert objects.derive_item_list_classes(body, (_record_for(bystander),)) == frozenset()


def test_no_class_vocabulary_is_transcribed_into_the_shipped_reader() -> None:
    """DO NOT hand-write a carrier vocabulary - the item note's instruction.

    NEEDS NO SAVE LIBRARY - it is a claim about the repo. A class path read out
    of a save is game content; the shipped module derives the carriers at read
    time and a list of them in its source is the thing that rots.
    """
    source = Path(objects.__file__).read_text(encoding="utf-8")
    planted = [word for word in ("Build_Conveyor", "Build_PowerLine") if word in source]

    assert planted == [], (
        f"{len(planted)} game class names look transcribed into the shipped reader. The "
        "carrier vocabulary is derived from the corpus at read time - see "
        "derive_item_list_classes - and a list of names in this module is exactly the "
        "hand-maintained vocabulary CS-1068's note forbids"
    )


def test_the_region_entry_records_the_class_keyed_reading() -> None:
    """The shipped region table and this reading cannot drift apart.

    NEEDS NO SAVE LIBRARY - it is a claim about the repo.
    """
    entry = objects.UNMEASURED_PAYLOAD_REGIONS["trailing_run"]

    assert objects.read_item_list.__name__ in entry
    assert objects.derive_item_list_classes.__name__ in entry


# ---------------------------------------------------------------------------
# The library half - skip-if-absent, COUNTS ONLY
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
        other_zeroed: Of those, how many the reading zeroed. `AND NOWHERE ELSE`,
            so this too is graded at zero.
        failures: The type names of any unexpected failure.
    """

    derived_classes: int
    carrier_payloads: int
    carrier_unread: int
    other_payloads: int
    other_zeroed: int
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
def _sweep_item_lists() -> _ListSweep | None:
    """Read every save's item lists, COUNTS ONLY.

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
    other_zeroed = 0
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
            carriers = objects.derive_item_list_classes(
                body,
                table.records,
                save_version=parsed.save_version,
                header_version=parsed.header_version,
            )
            derived_classes = max(derived_classes, len(carriers))
            for record in table.records:
                if not record.body_length:
                    continue
                result = objects.read_properties(
                    body,
                    record,
                    save_version=parsed.save_version,
                    header_version=parsed.header_version,
                    item_list_classes=carriers,
                )
                run = result.trailing_run
                if run is None or run.lead is None:
                    continue
                if objects.class_name_of(record.type_path) in carriers:
                    carrier_payloads += 1
                    carrier_unread += 1 if run.unread else 0
                elif run.width > objects.TRAILING_RUN_LEAD_BYTES:
                    other_payloads += 1
                    other_zeroed += 0 if run.unread else 1
        except (Exception, SystemExit) as exc:
            failures.append(type(exc).__name__)
            continue
    return _ListSweep(
        derived_classes=derived_classes,
        carrier_payloads=carrier_payloads,
        carrier_unread=carrier_unread,
        other_payloads=other_payloads,
        other_zeroed=other_zeroed,
        failures=tuple(sorted(set(failures))),
    )


def _sweep_or_skip() -> _ListSweep:
    """The sweep, or a skip when this machine has no save library.

    Returns:
        The sweep.
    """
    sweep = _sweep_item_lists()
    if sweep is None:
        pytest.skip("no save library on this machine")
    return sweep


def test_every_library_reaching_function_here_is_declared() -> None:
    """The reach guard, keyed on the RISKY primitives rather than the safe route.

    NEEDS NO SAVE LIBRARY - it is a claim about this module's source.
    """
    reach_guard._assert_library_reach_is_declared(  # noqa: SLF001
        Path(__file__), graded=_GRADED_LIBRARY_REACH, exempt=_EXEMPT_LIBRARY_REACH
    )


def test_the_corpus_derives_at_least_one_carrier() -> None:
    """THE NON-VACUITY CONTROL, and it runs before every claim below.

    An arm whose population is empty passes for that reason alone. The clause
    asks for at least one class; a sweep that derived none grades nothing.
    """
    sweep = _sweep_or_skip()

    assert sweep.failures == ()
    assert sweep.derived_classes >= 1, (
        "no class in this corpus demonstrated a non-empty count-prefixed item list, so "
        "every claim below this line would pass over an empty population"
    )
    assert sweep.carrier_payloads > 0


def test_the_remainder_falls_to_zero_on_every_derived_carrier_payload() -> None:
    """The clause's first half, over the whole corpus."""
    sweep = _sweep_or_skip()

    assert sweep.carrier_unread == 0, (
        f"{sweep.carrier_unread} of {sweep.carrier_payloads} payloads of a derived carrier "
        "class still carry unread bytes, so the reading does not cover the class the "
        "derivation named"
    )


def test_the_remainder_falls_to_zero_nowhere_else() -> None:
    """The clause's second half - `and nowhere else`.

    A reader returning zero for everything would meet the first half and fail
    here, which is why the two are separate arms over separate populations.
    """
    sweep = _sweep_or_skip()

    assert sweep.other_payloads > 0, (
        "no payload outside the derived classes carries a remainder at all, so this arm "
        "grades an empty population and says nothing about `nowhere else`"
    )
    assert sweep.other_zeroed == 0, (
        f"{sweep.other_zeroed} of {sweep.other_payloads} payloads outside the derived "
        "carrier classes had their remainder zeroed, so the reading is wider than the "
        "class the derivation named"
    )
