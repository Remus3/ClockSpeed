"""The object-header walk and the property resolution, proven fixture by fixture.

THE THREE FAILURE SHAPES THIS MODULE EXISTS TO CATCH
------------------------------------------------------
Each one produces a green suite and a wrong answer, which is why each has a
named discriminator here rather than a general assertion.

1. **One dispatch driving two decisions.** The body length prefix follows the
   HEADER version and the transform delta follows the SAVE version. Across the
   real library the two covary perfectly - header 10 with save 36 is (4, 4) and
   header 14 with save 60 is (8, 8) - so a parser reading both off one field
   passes every real-shaped fixture. ``synthetic.SAVE_CROSS`` is header 14 with
   save 36, a combination in no real file, and it is (8, 4). It is the only
   fixture that separates them, and
   ``test_save_cross_proves_the_two_dispatches_are_independent`` asserts the
   PAIR rather than either half, because either half alone is satisfied by a
   single-field parser.

2. **A prefix width assumed rather than dispatched.** ``CS-404`` corrected the
   corpus this session: header 10 opens the body with an int32, not with
   nothing. The direction that hides is a parser hardcoding the int64 and
   meeting a header-14 body with a 4-byte read - it recovers a plausible
   declared length from the low half and then reads the object count out of the
   HIGH half, which is zero. It reports an empty world and raises nothing.
   ``test_the_body_length_prefix_is_consumed_on_both_measured_widths`` asserts
   the record COUNT for that reason; asserting only the declared length would
   pass.

3. **An unmeasured save version defaulted instead of refused.** Save version 42
   is absent from the delta mapping deliberately, and 36 -> 4 beside 52 -> 8
   makes 4 or 6 look derived for it. That is ADR 0005's arithmetic route, which
   feels sound precisely because it uses only measured neighbours.
   ``test_a_save_version_absent_from_the_delta_mapping_raises`` pins the
   refusal, and ``test_the_delta_mapping_is_transcribed_from_the_corpus``
   pins the absence itself so nobody closes the gap by interpolation.

WHAT IS PROVEN AND WHAT IS ONLY EXERCISED, STATED PLAINLY
-----------------------------------------------------------
The transform DELTA is measured: ADR 0003 read 626 node actors with 626 valid
transforms out of real saves. Everything below is nonetheless proven against
the CORPUS and not against a real file, and two limits follow.

First, where the record table BEGINS. Every test ABOVE the CS-407 section hands
the walk a body whose first byte after the length prefix is the record count,
because that is what ``synthetic.build_body`` writes - and no real body is
shaped that way. A real body opens with a version-dependent preamble and then
carries a list of levels. So a green run in that part of this module is
evidence about DISPATCH and offset arithmetic, and is not evidence that
anything can read a save. The CS-407 section is what carries that second
claim, for the one pair whose layout is measured, and
``test_a_real_save_of_a_measured_pair_walks_to_the_end_of_its_body`` is the one
assertion here whose subject was produced by the game rather than by this
repository. It SKIPS with a reason on a machine with no save, which is every
CI machine.

Second, the PROPERTY PAYLOAD. The FLAT fixtures carry no object-data section -
``synthetic.SyntheticObject.encode`` emits a header record and stops - so every
test above the CS-407 section proves SCHEMA RESOLUTION and the flag-and-skip
contract around it, and nothing whatsoever about decoding a property value.

The LEVELLED fixture does carry a data section, and its CONTENT is opaque
filler rather than anything the game wrote. So it pins the extent arithmetic
CS-413 added - that the payloads tile their section and land on the right
record index - and it is incapable of corroborating the payload grammar
itself. Everything claimed about that grammar rests on the real-library sweeps,
which skip on a CI machine.

Neither limit is papered over, and neither is a reason to weaken an assertion:
the corpus is the stated contract for this wave, and a walk that is exactly
right about the corpus is the precondition for one that is right about a real
save.

THE PROPERTY MAP IS BUILT FROM ITS OWN PUBLIC TYPES, NOT FROM CORPUS BYTES
---------------------------------------------------------------------------
``synthetic.build_usmap``'s inner grammar for enums and schemas is a modelled
placeholder that does NOT match the shipped file - its own docstring says so,
and ``tests/save/test_usmap.py`` had to write a second encoder to reach the
real grammar. This slice consumes a :class:`usmap.PropertyMap`, never usmap
bytes, so it constructs that model directly from the public dataclasses.
Re-encoding the byte grammar here would be a third copy of a measurement this
module does not own.

NO REAL SAVE DATA, AND THE ECHO PATHS ARE PINNED MECHANICALLY
---------------------------------------------------------------
Every byte parsed here comes from ``tests/save/synthetic.py``. A save body
carries the world's contents and its actor names, so non-negotiable 12 makes
every exception an echo path.
``test_no_planted_fixture_string_reaches_any_exception_surface`` plants three
marker strings into a body, drives sixteen distinct failure paths through it,
and asserts the markers are absent from ``str``, ``args``, ``repr``,
``__notes__`` and the fully formatted traceback of every exception raised.
"""

from __future__ import annotations

import ast
import itertools
import struct
import traceback
from collections.abc import Callable, Mapping
from dataclasses import dataclass, replace
from pathlib import Path
from types import MappingProxyType
from typing import Final

import pytest

from clockspeed.data import locate
from clockspeed.save import chunks, header, objects, usmap
from tests.save import synthetic

# ---------------------------------------------------------------------------
# Local constants, so no assertion compares against a bare literal
# ---------------------------------------------------------------------------

_HEADER_10: Final = 10
_HEADER_13: Final = 13
_HEADER_14: Final = 14
_UNMEASURED_HEADER_VERSION: Final = 99

_SAVE_36: Final = 36
_SAVE_42: Final = 42
_SAVE_52: Final = 52
_SAVE_60: Final = 60
_UNMEASURED_SAVE_VERSION: Final = 97

_NARROW_PREFIX: Final = 4
_WIDE_PREFIX: Final = 8

_DELTA_36: Final = 4
_DELTA_42: Final = 4
_DELTA_60: Final = 8

#: A deliberately non-zero reserved word for the flag path. Its VALUE means
#: nothing - only that it is not the zero every real section carries.
_RESERVED_WORD_SET: Final = 1

_PAIR: Final = 2
_TRIPLE: Final = 3
_ONCE: Final = 1
_TWICE: Final = 2

#: Offset of the first record's class-path length prefix inside a body:
#: int32 object count, then the record's own int32 object type.
_FIRST_CLASS_PATH_LENGTH_AT: Final = 8

_ABSURD_STRING_LENGTH: Final = 1 << 30
_NEGATIVE_STRING_LENGTH: Final = -(1 << 30)
_UNMEASURED_OBJECT_TYPE: Final = 7

#: A UTF-16 character count UNDER the byte cap and a byte count OVER it. The
#: only band in which "cap the characters" and "cap the bytes" disagree.
_UTF16_CHARS_OVER_THE_BYTE_CAP: Final = 10_000

#: The union of every attribute an exception in this module may carry. A field
#: name, a byte offset, an expected/actual length or count, a version scalar
#: and a fixed reason string - nothing else.
_ALLOWED_ERROR_ATTRIBUTES: Final = frozenset(
    {"reason", "field", "offset", "expected", "actual", "version"}
)

#: Sibling save modules this one must NOT import. ``usmap`` is absent from the
#: list on purpose: docs/ARCHITECTURE.md makes the property mapping this
#: module's declared dependency. Reaching for the header parser or the chunk
#: walker instead of taking bytes and scalars would be the seam violation.
_FORBIDDEN_SIBLINGS: Final = ("header", "chunks", "workdir", "world")

# ---------------------------------------------------------------------------
# Planted markers. Invented, obviously synthetic, and asserted ABSENT from
# every exception surface - so naming them here is the test, not a leak.
# ---------------------------------------------------------------------------

_PLANTED_CLASS_PATH: Final = (
    "/Synthetic/Planted/Build_PlantedClassMarker.Build_PlantedClassMarker_C"
)
_PLANTED_ROOT: Final = "PlantedRootMarker:PersistentLevel"
_PLANTED_INSTANCE: Final = "PlantedInstanceMarker_0"
_PLANTED_TOKENS: Final = ("PlantedClassMarker", "PlantedRootMarker", "PlantedInstanceMarker")

#: A namespaced, mod-shaped path. BOOTSTRAP.md section 9: modded content is
#: tolerated, flagged, and never fatal.
_MOD_CLASS_PATH: Final = "/Mods/SyntheticMod/Build_SyntheticModded.Build_SyntheticModded_C"

#: A path carrying MORE THAN ONE dot. Every other path in this module has
#: exactly one, where splitting on the first dot and splitting on the last give
#: the same answer - so this is the only shape that separates them.
_NESTED_CLASS_PATH: Final = "/Mods/SyntheticMod/Pack.Outer.Build_SyntheticNested_C"

_KNOWN_CLASS_PATH_A: Final = "/Synthetic/Parts/Build_SyntheticSmelter.Build_SyntheticSmelter_C"
_KNOWN_CLASS_PATH_B: Final = "/Synthetic/Parts/Build_SyntheticBelt.Build_SyntheticBelt_C"

_ROOT: Final = "Persistent_Level:PersistentLevel"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _actor(class_path: str, instance_name: str, **extra: object) -> synthetic.SyntheticObject:
    """Build one synthetic record.

    Args:
        class_path: The record's class path.
        instance_name: The record's instance name.
        **extra: Forwarded to :class:`synthetic.SyntheticObject`.

    Returns:
        The record.
    """
    return synthetic.SyntheticObject(class_path, _ROOT, instance_name, **extra)  # type: ignore[arg-type]


def _payload_for(
    records: tuple[synthetic.SyntheticObject, ...], *, save_version: int, header_version: int
) -> bytes:
    """Build a body and prepend the version-appropriate length prefix.

    Goes through the corpus's own two functions rather than assembling a whole
    save, because most assertions below are about the record walk and a chunk
    round trip would only add a second thing that can fail.

    Args:
        records: The records to encode.
        save_version: Drives the transform delta.
        header_version: Drives the length prefix width.

    Returns:
        The payload, exactly as ``chunks.decompress_body`` would hand it over.
    """
    body = synthetic.build_body(records, save_version=save_version)
    return synthetic.body_with_prefix(body, header_version)


def _payload_of(save: synthetic.SyntheticSave) -> bytes:
    """Decompress a whole fixture through the real chunk walker.

    Args:
        save: The fixture.

    Returns:
        The decompressed payload, length prefix included.
    """
    walked = chunks.decompress_body(
        save.blob, save.chunk_offset, header_version=save.header_version
    )
    return walked.payload


def _table_of(save: synthetic.SyntheticSave, **extra: object) -> objects.ObjectTable:
    """Walk a whole fixture end to end: blob, chunk walk, object walk.

    Args:
        save: The fixture.
        **extra: Forwarded to :func:`objects.parse_object_headers`.

    Returns:
        The object table.
    """
    return objects.parse_object_headers(
        _payload_of(save),
        save_version=save.save_version,
        header_version=save.header_version,
        **extra,  # type: ignore[arg-type]
    )


def _splice(blob: bytes, offset: int, replacement: bytes) -> bytes:
    """Overwrite bytes in place without changing the length.

    Args:
        blob: The source.
        offset: Where to write.
        replacement: The new bytes.

    Returns:
        The spliced blob.
    """
    return blob[:offset] + replacement + blob[offset + len(replacement) :]


def _known(*class_paths: str) -> frozenset[str]:
    """Build a known-class container from full class paths.

    Args:
        *class_paths: The paths whose class names are modelled.

    Returns:
        The class names, in the shape a property map's schema keys take.
    """
    return frozenset(objects.class_name_of(path) for path in class_paths)


def _property_map(*schema_names: str) -> usmap.PropertyMap:
    """Build a property map from its own public types.

    See the module docstring: ``synthetic.build_usmap`` models an inner grammar
    that does not match the shipped file, and this module consumes the parsed
    model rather than usmap bytes.

    Args:
        *schema_names: The schema names the map resolves.

    Returns:
        The property map.
    """
    container = usmap.UsmapContainer(
        magic=usmap.USMAP_MAGIC,
        version=0,
        compression_method=usmap.COMPRESSION_NONE,
        compressed_size=0,
        decompressed_size=0,
        header_size=0,
    )
    schemas = {
        name: usmap.Schema(
            name=name,
            super_name=None,
            properties=(usmap.PropertyEntry(name="mSynthetic", slot=0, array_size=1, type_id=0),),
        )
        for name in schema_names
    }
    return usmap.PropertyMap(
        names=tuple(schema_names),
        enums=MappingProxyType({}),
        schemas=MappingProxyType(schemas),
        warnings=(),
        container=container,
        body_consumed=0,
    )


# ---------------------------------------------------------------------------
# 1 - the walk yields the expected records and transforms on every fixture
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "save",
    [synthetic.SAVE_V36, synthetic.SAVE_V52, synthetic.SAVE_V60, synthetic.SAVE_CROSS],
    ids=lambda save: save.name,
)
def test_the_walk_yields_the_expected_records_and_transforms(save: synthetic.SyntheticSave) -> None:
    """Acceptance 1, end to end: blob, chunk walk, object walk, per fixture.

    The transform values the corpus encodes are chosen to be exactly
    representable in float32, so an equality comparison here cannot fail for a
    rounding reason that merely looks like a parser bug.
    """
    table = _table_of(save)

    assert len(table.records) == len(save.objects)
    assert table.records != ()
    for expected, record in zip(save.objects, table.records, strict=True):
        assert record.type_path == expected.class_path
        assert record.root_object == expected.root_object
        assert record.instance_name == expected.instance_name
        assert record.kind == objects.KIND_ACTOR
        assert record.transform is not None
        assert record.transform.rotation == expected.rotation
        assert record.transform.translation == expected.translation
        assert record.transform.scale == expected.scale


@pytest.mark.parametrize(
    "save",
    [synthetic.SAVE_V36, synthetic.SAVE_V52, synthetic.SAVE_V60, synthetic.SAVE_CROSS],
    ids=lambda save: save.name,
)
def test_the_walk_consumes_the_whole_body_on_every_fixture(save: synthetic.SyntheticSave) -> None:
    """A walk that stops early yields the right prefix of the right records.

    Asserting the record count alone would pass a parser that read one record
    and stopped on a one-record fixture, so the byte accounting is asserted
    too: the table must account for every byte of the body it was handed.
    """
    table = _table_of(save)
    assert table.body_consumed == table.declared_body_length
    assert table.warnings == ()


def test_the_multichunk_fixture_walks_through_the_concatenated_body() -> None:
    """The body prefix counts every chunk, not this chunk.

    ``SAVE_MULTICHUNK`` is the only fixture whose body spans the real
    131072-byte split, so it is the only one where "this chunk's payload minus
    eight" and "the whole body" are different numbers.
    """
    save = synthetic.SAVE_MULTICHUNK
    assert save.chunk_count > _ONCE

    table = _table_of(save)
    assert len(table.records) == synthetic.MULTICHUNK_OBJECT_COUNT
    assert table.body_consumed == table.declared_body_length


# ---------------------------------------------------------------------------
# 2 - SAVE_CROSS proves the two dispatches are independent
# ---------------------------------------------------------------------------


def test_save_cross_proves_the_two_dispatches_are_independent() -> None:
    """Acceptance 2. How this fixture discriminates, stated exactly.

    ``SAVE_CROSS`` is header version 14 with save version 36, a combination
    present in NO real file. The two dispatches it separates are:

    - the body length prefix WIDTH, which follows the HEADER version, so 8;
    - the transform DELTA, which follows the SAVE version, so 4.

    The measured pair is therefore ``(8, 4)``. Every other fixture is
    ``(4, 4)`` or ``(8, 8)``, so a parser driving both decisions off the header
    version yields ``(8, 8)`` and one driving both off the save version yields
    ``(4, 4)`` - each passes every other fixture in the corpus and each fails
    here. Asserting the PAIR is what matters: either half on its own is
    satisfied by one of the two single-field parsers.
    """
    save = synthetic.SAVE_CROSS
    assert save.header_version == _HEADER_14
    assert save.save_version == _SAVE_36

    table = _table_of(save)
    assert (table.body_prefix_width, table.transform_delta) == (_WIDE_PREFIX, _DELTA_36)

    # The pair is unique to this fixture, which is the whole reason it exists.
    for other in (synthetic.SAVE_V36, synthetic.SAVE_V52, synthetic.SAVE_V60):
        table_other = _table_of(other)
        assert (table_other.body_prefix_width, table_other.transform_delta) != (
            _WIDE_PREFIX,
            _DELTA_36,
        )

    # And the records still decode, which is what a misdispatch would destroy.
    assert len(table.records) == len(save.objects)
    assert table.records[0].transform is not None
    assert table.records[0].transform.rotation == save.objects[0].rotation


def test_the_transform_delta_follows_the_save_version_alone() -> None:
    """The same body bytes, read under two header versions, give one delta.

    A parser that consulted the header version for the delta would disagree
    between these two calls; the delta is a function of the save version only.
    """
    records = (_actor(_KNOWN_CLASS_PATH_A, "SyntheticSmelter_0"),)
    deltas = {
        objects.parse_object_headers(
            _payload_for(records, save_version=_SAVE_36, header_version=header_version),
            save_version=_SAVE_36,
            header_version=header_version,
        ).transform_delta
        for header_version in (_HEADER_10, _HEADER_13, _HEADER_14)
    }
    assert deltas == {_DELTA_36}


def test_the_prefix_width_follows_the_header_version_alone() -> None:
    """The same save version, read under two header versions, gives two widths."""
    records = (_actor(_KNOWN_CLASS_PATH_A, "SyntheticSmelter_0"),)
    widths = {
        header_version: objects.parse_object_headers(
            _payload_for(records, save_version=_SAVE_36, header_version=header_version),
            save_version=_SAVE_36,
            header_version=header_version,
        ).body_prefix_width
        for header_version in (_HEADER_10, _HEADER_14)
    }
    assert widths == {_HEADER_10: _NARROW_PREFIX, _HEADER_14: _WIDE_PREFIX}


# ---------------------------------------------------------------------------
# 3 - an unmeasured save version raises rather than defaulting
# ---------------------------------------------------------------------------


def test_the_delta_mapping_agrees_with_the_corpus_on_every_shared_version() -> None:
    """Two independent transcriptions of one measurement, cross-checked.

    ``objects.py`` spells its own copy of the delta table rather than importing
    the corpus, matching ``chunks.py``: sharing the constant would make the
    suite a restatement of the module's own opinion instead of a check on it.

    THE COMPARISON IS A SUBSET RATHER THAN AN EQUALITY, AND THAT IS NOT A
    WEAKENING. The corpus's table serves the FLAT fixtures only; the levelled
    corpus keys its delta on the PAIR, in ``synthetic.LEVELLED_LAYOUTS``, and
    the pair-keyed cross-check below covers all four measured pairs including
    save 42. Between them the two assertions compare strictly more than the old
    equality did - the equality could not have covered a pair-keyed value at
    all.
    """
    for save_version, delta in synthetic.TRANSFORM_DELTA_BY_SAVE_VERSION.items():
        assert objects.TRANSFORM_DELTA_BY_SAVE_VERSION[save_version] == delta


def test_the_pair_keyed_delta_agrees_with_the_version_keyed_one_on_every_pair() -> None:
    """The two keyings must not disagree, and only a test can say so.

    ``objects.BODY_LAYOUT_BY_PAIR`` keys the delta on the pair because the KEY
    is undetermined - header version, save version and build changelist are all
    perfect predictors across the corpus. ``TRANSFORM_DELTA_BY_SAVE_VERSION``
    keys the same measurement on the save version for the flat walk. Two
    encodings of one number will drift the moment nothing compares them.
    """
    for (_header_version, save_version), parser_layout in objects.BODY_LAYOUT_BY_PAIR.items():
        assert parser_layout.transform_delta == objects.transform_delta(save_version)
    for (_header_version, save_version), corpus_layout in synthetic.LEVELLED_LAYOUTS.items():
        assert (
            objects.TRANSFORM_DELTA_BY_SAVE_VERSION[save_version] == corpus_layout.transform_delta
        )


def test_save_version_42_was_measured_rather_than_interpolated() -> None:
    """RESTATED UNDER CS-407. The absence used to be the assertion; now the KIND is.

    This asserted that 42 was absent from the delta table, so that nobody
    closed the gap by interpolation. 42 is now present with the value 4 - and
    4 is exactly what interpolating from 36 -> 4 and 52 -> 8 would have
    produced, so the value alone cannot distinguish a measurement from the
    guess this test was built to prevent.

    What distinguishes them is the KIND of evidence, and that is what is
    asserted here instead. The delta is corroborated INDEPENDENTLY of the
    section arithmetic that consumes it: every actor rotation in a real body is
    a unit quaternion, and all 17763 actors of the one real header-13 body give
    one at shift 4. So the guard that survives is against interpolation as a
    METHOD - a version with no measurement of any kind still raises.
    """
    assert objects.TRANSFORM_DELTA_BY_SAVE_VERSION[_SAVE_42] == _DELTA_42
    assert _UNMEASURED_SAVE_VERSION not in objects.TRANSFORM_DELTA_BY_SAVE_VERSION
    with pytest.raises(objects.UnsupportedSaveVersionError):
        objects.transform_delta(_UNMEASURED_SAVE_VERSION)


def test_a_save_version_absent_from_the_delta_mapping_raises() -> None:
    """Acceptance 3. An absent key raises; it never defaults.

    The refusal is EAGER - before a single record is read - for the same reason
    ``header.py`` checks its version before the string block: a check placed
    after the walk would let an empty-bodied save of an unmeasured version
    parse "successfully" and would fire only on a populated one, which is a
    version-dependent time bomb rather than a version check.
    """
    payload = _payload_for((), save_version=_SAVE_60, header_version=_HEADER_13)

    with pytest.raises(objects.UnsupportedSaveVersionError) as caught:
        objects.parse_object_headers(
            payload, save_version=_UNMEASURED_SAVE_VERSION, header_version=_HEADER_13
        )
    assert caught.value.version == _UNMEASURED_SAVE_VERSION


def test_the_empty_save_version_42_fixture_now_parses_through_the_flat_walk() -> None:
    """The other half of the correction, asserted rather than assumed.

    ``SAVE_V42`` was built with an EMPTY object section precisely because the
    delta was unmeasured, and this asserted it was refused. Retiring that
    refusal is only honest if the thing that used to be refused now works, so
    this asserts the parse instead.

    EMPTINESS IS STILL NOT SUPPORT, and the old test's point survives in the
    delta assertion: a lazy parser could walk zero records without ever
    consulting the delta, so the reported delta is what proves the version
    dispatch actually ran.
    """
    save = synthetic.SAVE_V42
    assert save.objects == ()

    table = _table_of(save)

    assert table.records == ()
    assert table.transform_delta == _DELTA_42
    assert table.save_version == _SAVE_42


# ---------------------------------------------------------------------------
# 4 and 5 - unknown and mod-shaped classes are flagged, and the walk continues
# ---------------------------------------------------------------------------


def test_an_unknown_type_path_is_flagged_and_the_walk_continues_past_it() -> None:
    """Acceptance 4. The unknown record sits in the MIDDLE, deliberately.

    ``synthetic.unknown_actor_class()`` puts its unknown record LAST, so a
    parser that stopped at the first unknown class would still return every
    earlier record and would pass a count assertion against it. Placing the
    unknown between two known records makes "the walk continued" an assertion
    about a record that could only exist if the walk resumed.
    """
    records = (
        _actor(_KNOWN_CLASS_PATH_A, "SyntheticSmelter_0"),
        _actor(synthetic.UNKNOWN_ACTOR_CLASS_PATH, "SyntheticUnknown_0"),
        _actor(_KNOWN_CLASS_PATH_B, "SyntheticBelt_0"),
    )
    payload = _payload_for(records, save_version=_SAVE_60, header_version=_HEADER_14)

    table = objects.parse_object_headers(
        payload,
        save_version=_SAVE_60,
        header_version=_HEADER_14,
        known_classes=_known(_KNOWN_CLASS_PATH_A, _KNOWN_CLASS_PATH_B),
    )

    assert table.contains_unmodeled_content
    flagged = {unknown.type_path: unknown for unknown in table.unknown_classes}
    assert set(flagged) == {synthetic.UNKNOWN_ACTOR_CLASS_PATH}
    assert flagged[synthetic.UNKNOWN_ACTOR_CLASS_PATH].count == _ONCE
    assert flagged[synthetic.UNKNOWN_ACTOR_CLASS_PATH].reason in objects.UNKNOWN_CLASS_REASONS

    # The walk reached the end of the table: three records, and the LAST one -
    # which only exists if parsing resumed after the unknown - decoded.
    assert len(table.records) == _TRIPLE
    assert table.records[-1].instance_name == "SyntheticBelt_0"
    assert table.records[-1].transform is not None


def test_the_corpus_unknown_actor_fixture_is_flagged_and_never_fatal() -> None:
    """The corpus's own unknown-class fixture, walked end to end.

    Its record is structurally VALID - the unknown-ness is in the class path
    alone - so a parser that rejected it would be rejecting it for the wrong
    reason while still looking correct.
    """
    save = synthetic.unknown_actor_class()
    table = _table_of(save, known_classes=_known(_KNOWN_CLASS_PATH_A))

    assert len(table.records) == len(save.objects)
    assert table.contains_unmodeled_content
    assert [unknown.type_path for unknown in table.unknown_classes] == [
        synthetic.UNKNOWN_ACTOR_CLASS_PATH
    ]


def test_a_namespaced_mod_class_path_is_flagged_and_never_fatal() -> None:
    """Acceptance 5, BOOTSTRAP.md section 9.

    A modded save must never produce a crash or a silently wrong number. It may
    produce an explicit "this world contains content I do not model", which is
    what ``contains_unmodeled_content`` is. The mod path is namespaced under
    ``/Mods/`` so it cannot collide with vanilla, and the walk treats it exactly
    as it treats any other unresolvable path - no mod-specific branch exists.
    """
    records = (
        _actor(_MOD_CLASS_PATH, "SyntheticModded_0"),
        _actor(_KNOWN_CLASS_PATH_A, "SyntheticSmelter_0"),
    )
    payload = _payload_for(records, save_version=_SAVE_60, header_version=_HEADER_14)

    table = objects.parse_object_headers(
        payload,
        save_version=_SAVE_60,
        header_version=_HEADER_14,
        known_classes=_known(_KNOWN_CLASS_PATH_A),
    )

    assert table.contains_unmodeled_content
    assert [unknown.type_path for unknown in table.unknown_classes] == [_MOD_CLASS_PATH]
    assert len(table.records) == _PAIR
    assert table.records[-1].instance_name == "SyntheticSmelter_0"


def test_repeated_unknown_classes_aggregate_into_one_entry_with_a_count() -> None:
    """A world with two hundred unmodeled belts has one problem, not two hundred."""
    records = (
        _actor(_MOD_CLASS_PATH, "SyntheticModded_0"),
        _actor(_MOD_CLASS_PATH, "SyntheticModded_1"),
        _actor(_KNOWN_CLASS_PATH_A, "SyntheticSmelter_0"),
    )
    payload = _payload_for(records, save_version=_SAVE_60, header_version=_HEADER_14)

    table = objects.parse_object_headers(
        payload,
        save_version=_SAVE_60,
        header_version=_HEADER_14,
        known_classes=_known(_KNOWN_CLASS_PATH_A),
    )

    assert len(table.unknown_classes) == _ONCE
    assert table.unknown_classes[0].count == _TWICE
    assert len(table.records) == _TRIPLE


def test_no_known_class_container_claims_nothing_is_unknown() -> None:
    """Absence of a registry is not evidence of unknown-ness.

    With no property map on the machine ``usmap.cached_usmap()`` returns None,
    and a walk that then flagged EVERY class as unmodeled would report a world
    of pure unknown content rather than a world it has not checked.
    """
    records = (_actor(_MOD_CLASS_PATH, "SyntheticModded_0"),)
    payload = _payload_for(records, save_version=_SAVE_60, header_version=_HEADER_14)

    table = objects.parse_object_headers(
        payload, save_version=_SAVE_60, header_version=_HEADER_14, known_classes=None
    )

    assert table.unknown_classes == ()
    assert not table.contains_unmodeled_content
    assert len(table.records) == _ONCE


def test_a_property_map_can_be_passed_straight_in_as_the_known_class_container() -> None:
    """The seam that makes the unknown-class rule free.

    ``PropertyMap.schemas`` is a mapping keyed by schema name, so it satisfies
    the container the walk wants without an adapter. If this stopped being
    true, the world layer would have to build a parallel registry.
    """
    property_map = _property_map(objects.class_name_of(_KNOWN_CLASS_PATH_A))
    records = (
        _actor(_KNOWN_CLASS_PATH_A, "SyntheticSmelter_0"),
        _actor(_MOD_CLASS_PATH, "SyntheticModded_0"),
    )
    payload = _payload_for(records, save_version=_SAVE_60, header_version=_HEADER_14)

    table = objects.parse_object_headers(
        payload,
        save_version=_SAVE_60,
        header_version=_HEADER_14,
        known_classes=property_map.schemas,
    )

    assert [unknown.type_path for unknown in table.unknown_classes] == [_MOD_CLASS_PATH]


# ---------------------------------------------------------------------------
# 6 - a payload the map cannot resolve is skipped and flagged, never raised
# ---------------------------------------------------------------------------


def test_a_type_path_the_property_map_cannot_resolve_is_flagged_never_raised() -> None:
    """Acceptance 6. Unresolvable is a reported state, not a failure."""
    property_map = _property_map(objects.class_name_of(_KNOWN_CLASS_PATH_A))
    records = (_actor(_MOD_CLASS_PATH, "SyntheticModded_0"),)
    payload = _payload_for(records, save_version=_SAVE_60, header_version=_HEADER_14)
    table = objects.parse_object_headers(payload, save_version=_SAVE_60, header_version=_HEADER_14)

    result = objects.read_properties(payload, table.records[0], property_map)

    assert not result.resolved
    assert result.properties == {}
    assert result.warnings != ()
    assert result.warnings[0].code == objects.WARN_UNRESOLVED_SCHEMA
    assert objects.parse_properties(payload, table.records[0], property_map) == {}


def test_a_resolvable_type_path_reports_the_schema_it_resolved_to() -> None:
    """The positive control for the test above.

    Without it, a resolver that returned "unresolved" for every input would
    pass the flag-and-skip test vacuously.
    """
    schema_name = objects.class_name_of(_KNOWN_CLASS_PATH_A)
    property_map = _property_map(schema_name)
    records = (_actor(_KNOWN_CLASS_PATH_A, "SyntheticSmelter_0"),)
    payload = _payload_for(records, save_version=_SAVE_60, header_version=_HEADER_14)
    table = objects.parse_object_headers(payload, save_version=_SAVE_60, header_version=_HEADER_14)

    result = objects.read_properties(payload, table.records[0], property_map)

    assert result.resolved
    assert result.schema_name == schema_name


def test_a_record_with_no_payload_extent_yields_no_properties_and_no_warning() -> None:
    """A record with no attributed extent yields nothing, and that is not an error.

    Every record from the FLAT walk is in this state, because that shape has no
    data section to attribute from. CS-413 narrowed what this test may claim:
    it once said an empty payload is "the NORMAL case for a large share of a
    real world's actors", and the real library disagrees - zero of the payloads
    in all 14 real saves are zero-length. So this pins the flag-and-skip
    contract for an unattributed record and says nothing about how common that
    is in a real world.
    """
    schema_name = objects.class_name_of(_KNOWN_CLASS_PATH_A)
    property_map = _property_map(schema_name)
    records = (_actor(_KNOWN_CLASS_PATH_A, "SyntheticSmelter_0"),)
    payload = _payload_for(records, save_version=_SAVE_60, header_version=_HEADER_14)
    table = objects.parse_object_headers(payload, save_version=_SAVE_60, header_version=_HEADER_14)

    assert table.records[0].body_length == 0
    result = objects.read_properties(payload, table.records[0], property_map)
    assert result.resolved
    assert result.properties == {}
    assert result.warnings == ()


def test_class_name_resolution_takes_the_object_name_after_the_final_dot() -> None:
    """The one rule that joins a class path to a usmap schema key.

    THE MULTI-DOT CASE IS THE ONLY DISCRIMINATING ONE, and it was added after a
    mutation survived without it. Every ordinary path carries exactly one dot,
    where taking the FIRST dot and taking the LAST are the same answer - so a
    parser splitting on the first passes every single-dot assertion and returns
    ``Outer.Build_Thing_C`` for a nested path, which resolves against no schema
    and would report a modded world as entirely unmodelled.
    """
    assert objects.class_name_of(_KNOWN_CLASS_PATH_A) == "Build_SyntheticSmelter_C"
    assert objects.class_name_of(_MOD_CLASS_PATH) == "Build_SyntheticModded_C"
    assert objects.class_name_of(_NESTED_CLASS_PATH) == "Build_SyntheticNested_C"
    assert objects.class_name_of("Build_Bare_C") == "Build_Bare_C"
    assert objects.class_name_of("") == ""


def test_a_nested_class_path_still_resolves_against_the_property_map() -> None:
    """The gap above, closed at the seam that actually consumes the rule."""
    property_map = _property_map("Build_SyntheticNested_C")
    records = (_actor(_NESTED_CLASS_PATH, "SyntheticNested_0"),)
    payload = _payload_for(records, save_version=_SAVE_60, header_version=_HEADER_14)

    table = objects.parse_object_headers(
        payload,
        save_version=_SAVE_60,
        header_version=_HEADER_14,
        known_classes=property_map.schemas,
    )

    assert table.unknown_classes == ()
    assert objects.read_properties(payload, table.records[0], property_map).resolved


# ---------------------------------------------------------------------------
# 7 - truncation inside the object table is one clean error
# ---------------------------------------------------------------------------


def test_truncation_inside_the_object_table_raises_object_truncated_error() -> None:
    """Acceptance 7. Every cut point, not a sampled few.

    The length prefix is rewritten to the truncated length at each cut, so the
    payload stays self-consistent and the damage is reachable ONLY inside the
    record walk - otherwise this would be re-testing the framing.
    ``pytest.raises`` on the module's own class is what proves no
    ``struct.error`` and no ``IndexError`` escapes: neither is a subclass.
    """
    records = (
        _actor(_KNOWN_CLASS_PATH_A, "SyntheticSmelter_0"),
        _actor(_KNOWN_CLASS_PATH_B, "SyntheticBelt_0"),
    )
    body = synthetic.build_body(records, save_version=_SAVE_60)
    assert len(body) > _PAIR

    for cut in range(len(body)):
        payload = synthetic.body_with_prefix(body[:cut], _HEADER_14)
        with pytest.raises(objects.ObjectTruncatedError):
            objects.parse_object_headers(payload, save_version=_SAVE_60, header_version=_HEADER_14)

    # The positive control: the uncut body parses. Without it every assertion
    # above would pass on a parser that raised unconditionally.
    whole = synthetic.body_with_prefix(body, _HEADER_14)
    assert (
        len(
            objects.parse_object_headers(
                whole, save_version=_SAVE_60, header_version=_HEADER_14
            ).records
        )
        == _PAIR
    )


def test_the_corpus_pinned_body_truncation_point_raises_a_truncation() -> None:
    """The corpus names one cut point as body-scope; this is it.

    ``synthetic.TRUNCATION_BOUNDARIES`` pins
    ``one-byte-short-of-an-object-record`` at body scope precisely because an
    object record lives inside the compressed stream and the damage cannot be
    expressed as a file offset at all.
    """
    pinned = next(
        point for point in synthetic.TRUNCATION_BOUNDARIES if point.scope == synthetic.SCOPE_BODY
    )
    save = synthetic.SAVE_V60
    payload = synthetic.body_with_prefix(save.body[: pinned.offset], save.header_version)

    with pytest.raises(objects.ObjectTruncatedError):
        objects.parse_object_headers(
            payload, save_version=save.save_version, header_version=save.header_version
        )


def test_a_truncated_length_prefix_is_a_truncation_not_a_struct_error() -> None:
    """The prefix itself is the first thing that can run short."""
    for keep in range(_WIDE_PREFIX):
        with pytest.raises(objects.ObjectTruncatedError):
            objects.parse_object_headers(
                bytes(keep), save_version=_SAVE_60, header_version=_HEADER_14
            )


def test_a_declared_string_length_above_the_cap_is_a_format_error() -> None:
    """Bound the DECLARATION, before the slice.

    A body declaring a gigabyte for one class path must be refused on the
    declaration rather than after an allocation attempt.
    """
    records = (_actor(_KNOWN_CLASS_PATH_A, "SyntheticSmelter_0"),)
    body = synthetic.build_body(records, save_version=_SAVE_60)
    damaged = _splice(body, _FIRST_CLASS_PATH_LENGTH_AT, struct.pack("<i", _ABSURD_STRING_LENGTH))
    payload = synthetic.body_with_prefix(damaged, _HEADER_14)

    with pytest.raises(objects.ObjectFormatError):
        objects.parse_object_headers(payload, save_version=_SAVE_60, header_version=_HEADER_14)


def test_a_negative_declared_string_length_is_refused_on_the_utf16_path() -> None:
    """A negative count selects UTF-16 and doubles the magnitude before the read.

    Not merely the previous case with a sign flipped: the multiply is what a
    parser does before it checks anything, so the cap has to be applied to the
    BYTE count rather than to the declared character count.
    """
    records = (_actor(_KNOWN_CLASS_PATH_A, "SyntheticSmelter_0"),)
    body = synthetic.build_body(records, save_version=_SAVE_60)
    damaged = _splice(body, _FIRST_CLASS_PATH_LENGTH_AT, struct.pack("<i", _NEGATIVE_STRING_LENGTH))
    payload = synthetic.body_with_prefix(damaged, _HEADER_14)

    with pytest.raises(objects.ObjectFormatError):
        objects.parse_object_headers(payload, save_version=_SAVE_60, header_version=_HEADER_14)


def test_the_utf16_cap_is_applied_to_the_byte_count_not_the_character_count() -> None:
    """The discriminating magnitude, added after a mutation survived without it.

    ``_UTF16_CHARS_OVER_THE_BYTE_CAP`` characters is UNDER the cap read as a
    character count and OVER it read as a byte count, which is the only band
    where the two differ. The test above uses a magnitude so large that both
    readings refuse, so it passed a parser that checked the wrong quantity.

    The cap has to bind the BYTE count because bytes are what gets allocated.
    A parser checking characters is refused here on the class it raises, not
    merely on whether it raises: the wrong-quantity variant sails past the cap
    and then trips the buffer bound, reporting a truncation - a short file -
    where the truth is a declaration above the stated ceiling.
    """
    records = (_actor(_KNOWN_CLASS_PATH_A, "SyntheticSmelter_0"),)
    body = synthetic.build_body(records, save_version=_SAVE_60)
    declared = -_UTF16_CHARS_OVER_THE_BYTE_CAP
    assert _UTF16_CHARS_OVER_THE_BYTE_CAP <= objects.MAX_STRING_BYTES
    assert _UTF16_CHARS_OVER_THE_BYTE_CAP * _PAIR > objects.MAX_STRING_BYTES

    damaged = _splice(body, _FIRST_CLASS_PATH_LENGTH_AT, struct.pack("<i", declared))
    payload = synthetic.body_with_prefix(damaged, _HEADER_14)

    with pytest.raises(objects.ObjectFormatError) as caught:
        objects.parse_object_headers(payload, save_version=_SAVE_60, header_version=_HEADER_14)
    assert caught.value.actual == _UTF16_CHARS_OVER_THE_BYTE_CAP * _PAIR
    assert caught.value.expected == objects.MAX_STRING_BYTES


def test_a_record_count_above_the_ceiling_is_refused_before_any_allocation() -> None:
    """A save is untrusted binary input; the count is bounded on the declaration."""
    body = struct.pack("<i", objects.MAX_OBJECTS + 1)
    payload = synthetic.body_with_prefix(body, _HEADER_14)

    with pytest.raises(objects.ObjectBudgetExceededError):
        objects.parse_object_headers(payload, save_version=_SAVE_60, header_version=_HEADER_14)


def test_a_negative_record_count_is_a_format_error() -> None:
    """A negative count would be read by a range as empty and by a slice as a tail."""
    body = struct.pack("<i", -1)
    payload = synthetic.body_with_prefix(body, _HEADER_14)

    with pytest.raises(objects.ObjectFormatError):
        objects.parse_object_headers(payload, save_version=_SAVE_60, header_version=_HEADER_14)


def test_an_unmeasured_object_type_discriminator_is_refused_rather_than_guessed() -> None:
    """A record whose GRAMMAR is unknown cannot be skipped, so it is refused.

    Non-negotiable 7 covers unknown CONTENT - a class this project does not
    model - and the walk flags and skips that. An unrecognised object-type
    discriminator is different in kind: the record carries no length, so there
    is no way to step over it and resume. Guessing the actor grammar for it
    would desynchronise the rest of the table silently.
    """
    records = (_actor(_KNOWN_CLASS_PATH_A, "Synth_0", object_type=_UNMEASURED_OBJECT_TYPE),)
    payload = _payload_for(records, save_version=_SAVE_60, header_version=_HEADER_14)

    with pytest.raises(objects.ObjectFormatError):
        objects.parse_object_headers(payload, save_version=_SAVE_60, header_version=_HEADER_14)


# ---------------------------------------------------------------------------
# 8 - the body length prefix is consumed correctly on BOTH widths
# ---------------------------------------------------------------------------


def test_the_body_length_prefix_is_consumed_on_both_measured_widths() -> None:
    """Acceptance 8. CS-404's correction, and the direction that hides.

    Header 10 opens the body with an int32 equal to the body length; headers 13
    and 14 open it with an int64. Save version 36 is used for both sides so the
    transform delta is held constant and the prefix width is the only variable.

    The RECORD COUNT is the load-bearing assertion. A parser hardcoding the
    int64 and meeting a header-14 body reads correctly. The same parser meeting
    a HEADER 10 body reads the count out of the middle of the first record and
    fails loudly, which is the easy direction. The dangerous direction is the
    reverse: a parser hardcoding the int32 against a header-14 body recovers a
    plausible declared length from the low four bytes and then reads the object
    count from the HIGH four bytes, which are zero. It returns an empty table
    and raises nothing. Only the count assertion catches that.
    """
    records = (
        _actor(_KNOWN_CLASS_PATH_A, "SyntheticSmelter_0"),
        _actor(_KNOWN_CLASS_PATH_B, "SyntheticBelt_0"),
    )
    body = synthetic.build_body(records, save_version=_SAVE_36)

    for header_version, expected_width in (
        (_HEADER_10, _NARROW_PREFIX),
        (_HEADER_13, _WIDE_PREFIX),
        (_HEADER_14, _WIDE_PREFIX),
    ):
        payload = synthetic.body_with_prefix(body, header_version)
        assert synthetic.body_prefix_width(header_version) == expected_width

        table = objects.parse_object_headers(
            payload, save_version=_SAVE_36, header_version=header_version
        )

        assert table.body_prefix_width == expected_width
        assert table.declared_body_length == len(payload) - expected_width
        assert table.declared_body_length == len(body)
        assert len(table.records) == _PAIR
        assert table.records[-1].instance_name == "SyntheticBelt_0"


def test_the_header_10_and_header_14_walks_agree_record_for_record() -> None:
    """The same records under both prefix widths decode identically.

    A width bug cannot survive this: the two walks read different byte offsets
    for everything after the prefix, so agreement across both is only possible
    when each width is right.
    """
    records = (
        _actor(_KNOWN_CLASS_PATH_A, "SyntheticSmelter_0"),
        _actor(_KNOWN_CLASS_PATH_B, "SyntheticBelt_0"),
    )
    body = synthetic.build_body(records, save_version=_SAVE_36)

    narrow = objects.parse_object_headers(
        synthetic.body_with_prefix(body, _HEADER_10),
        save_version=_SAVE_36,
        header_version=_HEADER_10,
    )
    wide = objects.parse_object_headers(
        synthetic.body_with_prefix(body, _HEADER_14),
        save_version=_SAVE_36,
        header_version=_HEADER_14,
    )

    assert narrow.records == wide.records
    assert narrow.body_prefix_width != wide.body_prefix_width


def test_an_unmeasured_header_version_is_flagged_and_never_fatal() -> None:
    """ADR 0007 decision 3: an unattested combination is flagged, never guessed.

    ``chunks.py`` sets the precedent - it warns rather than raising when a
    supplied header version is outside the measured set, because raising would
    assert that the header version is the key the framing follows, which the
    ADR explicitly refuses to claim.
    """
    records = (_actor(_KNOWN_CLASS_PATH_A, "SyntheticSmelter_0"),)
    payload = _payload_for(
        records, save_version=_SAVE_60, header_version=_UNMEASURED_HEADER_VERSION
    )

    table = objects.parse_object_headers(
        payload, save_version=_SAVE_60, header_version=_UNMEASURED_HEADER_VERSION
    )

    assert len(table.records) == _ONCE
    assert [warning.code for warning in table.warnings] == [objects.WARN_UNMEASURED_HEADER_VERSION]


def test_a_body_length_prefix_that_disagrees_is_flagged_and_never_fatal() -> None:
    """A disagreement is reported, not raised - the records are still there."""
    records = (_actor(_KNOWN_CLASS_PATH_A, "SyntheticSmelter_0"),)
    body = synthetic.build_body(records, save_version=_SAVE_60)
    payload = struct.pack("<q", len(body) - 1) + body

    table = objects.parse_object_headers(payload, save_version=_SAVE_60, header_version=_HEADER_14)

    assert len(table.records) == _ONCE
    assert objects.WARN_BODY_LENGTH_DISAGREEMENT in {warning.code for warning in table.warnings}


def test_bytes_left_after_the_record_table_are_flagged_as_unparsed() -> None:
    """The object DATA section is unmeasured, so its presence is reported.

    No corpus fixture carries one, which is exactly why its absence must not be
    mistaken for proof that the walk handles it. Trailing bytes are flagged and
    skipped rather than parsed against a grammar nobody here has measured.
    """
    records = (_actor(_KNOWN_CLASS_PATH_A, "SyntheticSmelter_0"),)
    body = synthetic.build_body(records, save_version=_SAVE_60) + bytes(16)
    payload = synthetic.body_with_prefix(body, _HEADER_14)

    table = objects.parse_object_headers(payload, save_version=_SAVE_60, header_version=_HEADER_14)

    assert len(table.records) == _ONCE
    assert objects.WARN_UNPARSED_DATA_SECTION in {warning.code for warning in table.warnings}


# ---------------------------------------------------------------------------
# 9 - no fixture string reaches any exception surface
# ---------------------------------------------------------------------------


def _planted_records() -> tuple[synthetic.SyntheticObject, ...]:
    """Records whose three strings are all planted markers.

    Returns:
        The records.
    """
    return (
        synthetic.SyntheticObject(_PLANTED_CLASS_PATH, _PLANTED_ROOT, _PLANTED_INSTANCE),
        synthetic.SyntheticObject(_PLANTED_CLASS_PATH, _PLANTED_ROOT, _PLANTED_INSTANCE + "_1"),
    )


def _planted_failures() -> list[Callable[[], object]]:
    """Every failure path reachable with planted strings in the buffer.

    Returns:
        Callables that each raise.
    """
    records = _planted_records()
    body = synthetic.build_body(records, save_version=_SAVE_60)

    def walk(payload: bytes, *, save_version: int = _SAVE_60) -> Callable[[], object]:
        def call() -> object:
            return objects.parse_object_headers(
                payload, save_version=save_version, header_version=_HEADER_14
            )

        return call

    cases: list[Callable[[], object]] = [
        walk(synthetic.body_with_prefix(body, _HEADER_14), save_version=_SAVE_42),
        walk(synthetic.body_with_prefix(body, _HEADER_14), save_version=_UNMEASURED_SAVE_VERSION),
        walk(
            synthetic.body_with_prefix(
                _splice(
                    body, _FIRST_CLASS_PATH_LENGTH_AT, struct.pack("<i", _ABSURD_STRING_LENGTH)
                ),
                _HEADER_14,
            )
        ),
        walk(
            synthetic.body_with_prefix(
                _splice(
                    body, _FIRST_CLASS_PATH_LENGTH_AT, struct.pack("<i", _NEGATIVE_STRING_LENGTH)
                ),
                _HEADER_14,
            )
        ),
        walk(synthetic.body_with_prefix(struct.pack("<i", -1) + body[4:], _HEADER_14)),
        walk(
            synthetic.body_with_prefix(
                struct.pack("<i", objects.MAX_OBJECTS + 1) + body[4:], _HEADER_14
            )
        ),
        walk(
            _payload_for(
                (
                    synthetic.SyntheticObject(
                        _PLANTED_CLASS_PATH,
                        _PLANTED_ROOT,
                        _PLANTED_INSTANCE,
                        object_type=_UNMEASURED_OBJECT_TYPE,
                    ),
                ),
                save_version=_SAVE_60,
                header_version=_HEADER_14,
            )
        ),
    ]
    # Ten truncation points spread across the planted body, so the markers are
    # partially present in the buffer at each one.
    step = max(len(body) // 10, 1)
    cases.extend(
        walk(synthetic.body_with_prefix(body[:cut], _HEADER_14))
        for cut in range(0, len(body), step)
    )
    return cases


def test_the_planted_failure_cases_all_actually_raise() -> None:
    """The positive control for the leak test below.

    A leak test over cases that silently succeed asserts nothing at all, and
    that is the exact shape of a test about nothing.
    """
    cases = _planted_failures()
    assert len(cases) > _TRIPLE
    for call in cases:
        with pytest.raises(objects.ObjectError):
            call()


def test_no_planted_fixture_string_reaches_any_exception_surface() -> None:
    """Acceptance 9. Non-negotiable 12, asserted over five surfaces.

    A save body holds the world's contents and its actor names, so an exception
    is an echo path. ``str``, ``args``, ``repr``, ``__notes__`` and the fully
    formatted traceback are checked, because a message can be clean while
    ``args`` carries the value and a traceback renders the chained cause.
    """
    for call in _planted_failures():
        with pytest.raises(objects.ObjectError) as caught:
            call()
        error = caught.value

        surfaces = [
            str(error),
            repr(error),
            repr(error.args),
            "".join(getattr(error, "__notes__", []) or []),
            "".join(traceback.format_exception(type(error), error, error.__traceback__)),
        ]
        for surface in surfaces:
            for token in _PLANTED_TOKENS:
                assert token not in surface
            assert surface.isascii()


@pytest.mark.parametrize("call", _planted_failures())
def test_every_raised_error_carries_only_taxonomy_fields(call: Callable[[], object]) -> None:
    """The attribute SET is pinned, not the values.

    Anything else on the instance is a channel through which save content could
    travel, so the set is asserted mechanically rather than by reading the code.
    """
    with pytest.raises(objects.ObjectError) as caught:
        call()
    assert set(vars(caught.value)) <= _ALLOWED_ERROR_ATTRIBUTES
    for name in ("offset", "expected", "actual", "version"):
        value = getattr(caught.value, name)
        assert value is None or isinstance(value, int)
    assert isinstance(caught.value.field, str)


@pytest.mark.parametrize("call", _planted_failures())
def test_every_raised_reason_is_a_declared_constant(call: Callable[[], object]) -> None:
    """A reason cannot carry content if it is never built from content."""
    declared = {
        value
        for name, value in vars(objects).items()
        if name.startswith("REASON_") and isinstance(value, str)
    }
    assert declared, "the module must declare its reason strings as constants"
    with pytest.raises(objects.ObjectError) as caught:
        call()
    assert caught.value.reason in declared


@pytest.mark.parametrize("call", _planted_failures())
def test_no_raised_message_previews_the_bytes_that_caused_it(call: Callable[[], object]) -> None:
    """A hex preview in an exception is a disclosure, so the rendering is pinned."""
    with pytest.raises(objects.ObjectError) as caught:
        call()
    message = str(caught.value)

    assert message.isascii()
    assert "\\x" not in message
    assert "b'" not in message
    assert 'b"' not in message
    assert "0x" not in message.lower()


def test_every_error_class_descends_from_the_base() -> None:
    """One catch clause covers the whole layer."""
    for cls in (
        objects.ObjectFormatError,
        objects.ObjectTruncatedError,
        objects.ObjectBudgetExceededError,
        objects.UnsupportedSaveVersionError,
    ):
        assert issubclass(cls, objects.ObjectError)
    assert issubclass(objects.ObjectError, Exception)


def test_the_record_repr_withholds_every_string_it_carries() -> None:
    """A repr is an echo path, and a test runner reprs objects into the log.

    ``header.py`` sets the precedent: the safe rendering has to stay safe even
    when the parse is wrong, so it emits structure and withholds content.
    """
    records = _planted_records()
    payload = _payload_for(records, save_version=_SAVE_60, header_version=_HEADER_14)

    # An EMPTY registry, so every planted class lands in unknown_classes and
    # the table's rendering of that collection is exercised rather than skipped.
    table = objects.parse_object_headers(
        payload,
        save_version=_SAVE_60,
        header_version=_HEADER_14,
        known_classes=frozenset(),
    )
    assert table.unknown_classes != ()

    for rendering in (repr(table), repr(table.records[0]), repr(table.records)):
        for token in _PLANTED_TOKENS:
            assert token not in rendering
        assert rendering.isascii()


# ---------------------------------------------------------------------------
# CS-407 - the LEVELLED body layout, which is what a real body actually is
#
# Everything above this line hands the walk a body whose first int32 after the
# length prefix is a record count. CS-407 measured that no real body is shaped
# that way, so everything above proves dispatch and offset arithmetic and
# proves nothing about reading a save. These tests carry that second claim, and
# only for the pairs in ``synthetic.LEVELLED_LAYOUT_PAIRS``.
# ---------------------------------------------------------------------------


def _levelled_payload() -> bytes:
    """Decompress the levelled fixture the way a caller would.

    Returns:
        The body, length prefix included.
    """
    return chunks.decompress_body(
        synthetic.SAVE_LEVELLED_V36.blob,
        synthetic.SAVE_LEVELLED_V36.chunk_offset,
        header_version=synthetic.SAVE_LEVELLED_V36.header_version,
    ).payload


def test_parse_body_consumes_the_levelled_layout_to_the_last_byte() -> None:
    """THE ORACLE, and the only assertion here that is hard to satisfy by accident.

    A grammar that is wrong anywhere does not end on the final byte - it ends
    early, late, or inside a string. Asserting the record COUNT alone would pass
    for a walker that read one level and stopped; asserting no unparsed
    remainder is what makes the count mean something.
    """
    fixture = synthetic.SAVE_LEVELLED_V36
    table = objects.parse_body(
        _levelled_payload(),
        save_version=fixture.save_version,
        header_version=fixture.header_version,
    )

    expected = sum(
        level.record_count for level in (*synthetic.LEVELLED_NAMED, synthetic.LEVELLED_PERSISTENT)
    )
    assert len(table.records) == expected
    assert table.level_count == len(synthetic.LEVELLED_NAMED) + 1
    assert not [w for w in table.warnings if w.code == objects.WARN_UNPARSED_DATA_SECTION]
    assert table.body_consumed == len(fixture.body)


def test_parse_body_reads_a_component_as_four_strings_and_no_transform() -> None:
    """The component branch, which was UNVERIFIED against a real file until CS-407.

    A component carries a parent path where an actor carries its filler and
    transform block. A walker that read the actor grammar for both desynchronises
    every byte after the first component, which is exactly how the real header-14
    walk fails today.
    """
    table = objects.parse_body(
        _levelled_payload(),
        save_version=synthetic.SAVE_LEVELLED_V36.save_version,
        header_version=synthetic.SAVE_LEVELLED_V36.header_version,
    )

    components = [r for r in table.records if r.kind == objects.KIND_COMPONENT]
    assert len(components) == 1
    assert components[0].transform is None
    assert components[0].parent is not None
    actors = [r for r in table.records if r.kind == objects.KIND_ACTOR]
    assert all(record.transform is not None for record in actors)
    assert all(record.parent is None for record in actors)


def test_parse_body_refuses_a_pair_whose_body_layout_is_unmeasured() -> None:
    """A pair outside the measured set is refused, not interpolated.

    All four REAL pairs now have a measured skeleton, so the fixture that
    carries this branch is the synthetic-only one: header 14 with save 36
    occurs in no real file and has no real body to have been measured. That is
    the honest remaining case - refusing it is what stops a later slice from
    quietly deriving a fifth layout from its neighbours, which is ADR 0005's
    refuted arithmetic route.
    """
    for header_version, save_version in ((_HEADER_14, _SAVE_36), (_HEADER_10, _SAVE_60)):
        assert (header_version, save_version) not in objects.MEASURED_BODY_LAYOUTS
        with pytest.raises(objects.UnsupportedBodyLayoutError):
            objects.parse_body(
                _levelled_payload(),
                save_version=save_version,
                header_version=header_version,
            )


def test_the_measured_layout_pairs_are_transcribed_from_the_corpus() -> None:
    """The parser's opinion and the corpus's opinion have to be the same opinion.

    Transcribed rather than imported, matching the delta mapping, so the suite
    is a check on the parser instead of a restatement of it. This is the only
    thing proving neither slice mistyped the set.
    """
    assert frozenset(synthetic.LEVELLED_LAYOUT_PAIRS) == objects.MEASURED_BODY_LAYOUTS
    for pair in synthetic.LEVELLED_LAYOUT_UNMEASURED:
        assert pair not in objects.MEASURED_BODY_LAYOUTS


# ---------------------------------------------------------------------------
# CS-407 wave 2 - the three remaining real pairs
#
# READ THE WORD SKELETON BEFORE READING ANY ASSERTION BELOW. Landing on the
# final byte of a body proves the FRAMING is right. It does not prove the body
# is understood: 69.5% to 77.7% of a real save-52 body and 12100463 of 18086289
# bytes of the real save-42 body are opaque property payload this grammar steps
# over by declared length. What is named here is a 1.8% to 2.7% skeleton plus
# its strings.
#
# These tests run against the CORPUS. The corpus can only ever agree with
# whoever wrote it, so the load-bearing evidence for these three pairs is
# ``test_every_real_save_of_a_measured_pair_walks_to_the_end_of_its_body``
# below, which skips on any machine without a save library.
# ---------------------------------------------------------------------------


def _levelled_body_of(fixture: synthetic.SyntheticSave) -> bytes:
    """Decompress one levelled fixture the way a caller would.

    Args:
        fixture: The levelled fixture.

    Returns:
        The body, length prefix included.
    """
    return chunks.decompress_body(
        fixture.blob, fixture.chunk_offset, header_version=fixture.header_version
    ).payload


def _expected_record_count(fixture: synthetic.SyntheticSave) -> int:
    """Derive the record count from the levels the fixture was built from.

    Written as a derivation rather than a literal so the count follows the
    corpus when a level is added instead of having to be recomputed by hand.

    Args:
        fixture: The levelled fixture.

    Returns:
        The count of actors plus components across every level.
    """
    named = synthetic.LEVELLED_NAMED_BY_PAIR[(fixture.header_version, fixture.save_version)]
    return sum(level.record_count for level in (*named, synthetic.LEVELLED_PERSISTENT))


@pytest.mark.parametrize("fixture", synthetic.LEVELLED_SAVES, ids=lambda save: save.name)
def test_every_measured_pair_walks_its_levelled_body_to_the_last_byte(
    fixture: synthetic.SyntheticSave,
) -> None:
    """THE ORACLE, now applied to all four pairs rather than one.

    A grammar that is wrong anywhere does not end on the final byte - it ends
    early, late, or inside a string. Asserting the record COUNT alone would pass
    for a walker that read one level and stopped; asserting that nothing is left
    over is what makes the count mean something.
    """
    table = objects.parse_body(
        _levelled_body_of(fixture),
        save_version=fixture.save_version,
        header_version=fixture.header_version,
    )

    named = synthetic.LEVELLED_NAMED_BY_PAIR[(fixture.header_version, fixture.save_version)]
    assert len(table.records) == _expected_record_count(fixture)
    assert table.level_count == len(named) + 1
    assert not [w for w in table.warnings if w.code == objects.WARN_UNPARSED_DATA_SECTION]
    assert table.body_consumed == len(fixture.body)


@pytest.mark.parametrize("fixture", synthetic.LEVELLED_SAVES, ids=lambda save: save.name)
def test_every_measured_pair_splits_actors_from_components(
    fixture: synthetic.SyntheticSave,
) -> None:
    """The component branch, which desynchronises a real body when it is wrong.

    A component carries a parent path where an actor carries its opaque run and
    transform block, and on the two header-14 pairs it carries 4 further opaque
    bytes first. A walker reading the actor grammar for both, or missing the
    pre-word, desynchronises every byte after the first component.
    """
    table = objects.parse_body(
        _levelled_body_of(fixture),
        save_version=fixture.save_version,
        header_version=fixture.header_version,
    )

    components = [r for r in table.records if r.kind == objects.KIND_COMPONENT]
    actors = [r for r in table.records if r.kind == objects.KIND_ACTOR]
    assert components, "every levelled fixture carries at least one component"
    assert all(record.transform is None for record in components)
    assert all(record.parent is not None for record in components)
    assert all(record.transform is not None for record in actors)
    assert all(record.parent is None for record in actors)


@pytest.mark.parametrize("fixture", synthetic.LEVELLED_SAVES, ids=lambda save: save.name)
def test_every_measured_pair_reports_its_own_transform_delta(
    fixture: synthetic.SyntheticSave,
) -> None:
    """The delta the walk actually used, per pair, not per neighbour.

    Save 42's delta is 4 and save 52's is 8 even though 42 sits between 36 and
    52 - which is exactly why it had to be measured rather than interpolated.
    """
    table = objects.parse_body(
        _levelled_body_of(fixture),
        save_version=fixture.save_version,
        header_version=fixture.header_version,
    )
    layout = synthetic.LEVELLED_LAYOUTS[(fixture.header_version, fixture.save_version)]

    assert table.transform_delta == layout.transform_delta


def test_the_layout_table_is_transcribed_from_the_corpus_field_by_field() -> None:
    """Two independent transcriptions of one grammar, compared element by element.

    ``objects.py`` spells its own copy rather than importing the corpus, so the
    suite is a check on the parser instead of a restatement of it. Comparing the
    PAIR SET alone would miss a mistyped field inside a pair that still parses
    the fixture the same slice wrote, which is the whole failure class this
    corpus exists to avoid.
    """
    mine = {
        pair: (
            layout.transform_delta,
            layout.section_size_width,
            layout.package_summary,
            layout.grid_preamble,
            layout.data_entry_lead,
            layout.data_entry_trailer,
            layout.component_pre_word,
            layout.level_tail,
            layout.second_collectables_named,
        )
        for pair, layout in synthetic.LEVELLED_LAYOUTS.items()
    }
    theirs = {
        pair: (
            layout.transform_delta,
            layout.section_size_width,
            layout.package_summary,
            layout.grid_preamble,
            layout.data_entry_lead,
            layout.data_entry_trailer,
            layout.component_pre_word,
            layout.level_tail,
            layout.second_collectables_named,
        )
        for pair, layout in objects.BODY_LAYOUT_BY_PAIR.items()
    }

    assert mine == theirs


def test_the_delta_is_keyed_on_the_pair_and_not_on_either_version_alone() -> None:
    """The KEY is undetermined, so the parser must not key on one field.

    Header version, save version and build changelist are all perfect
    predictors of every difference in the corpus, because each header version
    occurs with exactly one set of save versions. ADR 0007 records the same
    undetermined keying for the chunk marker. This asserts the parser agrees
    with the corpus PER PAIR, which is the only claim the evidence supports.
    """
    for (header_version, save_version), layout in synthetic.LEVELLED_LAYOUTS.items():
        table = objects.parse_body(
            _levelled_body_of(
                next(
                    save
                    for save in synthetic.LEVELLED_SAVES
                    if (save.header_version, save.save_version) == (header_version, save_version)
                )
            ),
            save_version=save_version,
            header_version=header_version,
        )
        assert table.transform_delta == layout.transform_delta
        assert table.header_version == header_version
        assert table.save_version == save_version


def test_a_non_zero_reserved_word_in_a_section_size_is_flagged_not_fatal() -> None:
    """Non-negotiable 7 on the one field the corpus can never decide.

    An 8-byte section size is read as an int32 size plus an int32 reserved word
    asserted zero, rather than as an int64. The two are byte-identical on every
    save that can physically exist - the largest real section is 0.45% of 2^31 -
    so the corpus cannot separate them and never will. The reading is chosen on
    asymmetric damage: an int64 reader meeting a non-zero high word computes an
    astronomical size and then reports a mismatch against the WRONG FIELD, while
    this one names the field that actually changed.

    The flag is the point. A crash here would refuse a save over a word whose
    meaning is unknown, and a silent pass would hide the first evidence anyone
    has ever had about it.
    """
    fixture = synthetic.SAVE_LEVELLED_V52
    layout = synthetic.LEVELLED_LAYOUTS[(fixture.header_version, fixture.save_version)]
    assert layout.section_size_width == synthetic.SECTION_SIZE_WIDTH_WIDE

    named = tuple(
        replace(level, reserved_word=_RESERVED_WORD_SET)
        for level in synthetic.LEVELLED_NAMED_BY_PAIR[
            (fixture.header_version, fixture.save_version)
        ]
    )
    body = synthetic.build_levelled_body(
        named,
        synthetic.LEVELLED_PERSISTENT,
        header_version=fixture.header_version,
        save_version=fixture.save_version,
        grids=synthetic.LEVELLED_GRIDS,
    )

    table = objects.parse_body(
        synthetic.body_with_prefix(body, fixture.header_version),
        save_version=fixture.save_version,
        header_version=fixture.header_version,
    )

    flagged = [w for w in table.warnings if w.code == objects.WARN_RESERVED_WORD_SET]
    assert flagged, "a non-zero reserved word was consumed without being flagged"
    assert len(table.records) == _expected_record_count(fixture)
    assert not [w for w in table.warnings if w.code == objects.WARN_UNPARSED_DATA_SECTION]


def test_the_opaque_spans_are_recorded_as_a_structure_a_later_slice_can_resume_from() -> None:
    """A partial recorded as prose is not resumable, so it is recorded as data.

    The pair map is now EMPTY - every real pair has a measured skeleton - and
    that is exactly when a project starts believing the format is understood.
    What remains unmeasured is no longer a pair but a set of spans inside pairs
    that do parse, and the largest of them is three quarters of every body.
    """
    assert synthetic.LEVELLED_LAYOUT_UNMEASURED == {}
    assert synthetic.LEVELLED_LAYOUT_OPAQUE_SPANS
    assert "object_data_payload" in synthetic.LEVELLED_LAYOUT_OPAQUE_SPANS
    assert "transform_delta" in synthetic.LEVELLED_LAYOUT_OPAQUE_SPANS


def test_the_flat_walk_is_untouched_by_the_levelled_walk() -> None:
    """``parse_object_headers`` is a consumed public surface and must not shift.

    A concurrent slice reads it. The levelled walk is ADDITIVE - a new entry
    point - and this pins that the old one still answers exactly as before on
    the flat corpus body.
    """
    payload = chunks.decompress_body(
        synthetic.SAVE_V36.blob,
        synthetic.SAVE_V36.chunk_offset,
        header_version=synthetic.SAVE_V36.header_version,
    ).payload
    table = objects.parse_object_headers(payload, save_version=36, header_version=10)
    assert len(table.records) == len(synthetic.SAVE_V36.objects)
    assert table.level_count == 0


# ---------------------------------------------------------------------------
# The real-save acceptance
#
# SKIPS WITH A REASON when no save is present. CI runs with no game install and
# no save directory, and the whole suite must stay green there (BOOTSTRAP.md
# section 5.4). Nothing below prints, asserts on, or otherwise renders a decoded
# string: a save body holds the world's contents and non-negotiables 11 and 12
# make every echo path a disclosure.
# ---------------------------------------------------------------------------


def _one_real_save_of_a_measured_pair() -> tuple[int, int, bytes] | None:
    """Find a real save whose body layout this project has measured.

    Returns:
        ``(header version, save version, decompressed body)``, or None when no
        such file is reachable. Never returns or logs a path.
    """
    root = locate.resolve_save_root()
    if root is None:
        return None
    account = locate.resolve_account_dir(root)
    if account is None:
        return None
    for path in sorted(account.glob("*.sav")):
        try:
            data = path.read_bytes()
            parsed = header.parse_header(data)
        except (OSError, header.HeaderError):
            continue
        if (parsed.header_version, parsed.save_version) not in objects.MEASURED_BODY_LAYOUTS:
            continue
        try:
            body = chunks.decompress_body(
                data, parsed.body_offset, header_version=parsed.header_version
            )
        except chunks.ChunkError:
            continue
        return (parsed.header_version, parsed.save_version, body.payload)
    return None


@dataclass(frozen=True)
class _RealSweep:
    """What a sweep of the real library observed, as scalars and nothing else.

    EVERY FIELD IS SAFE TO RENDER, and that is the point of the type. A save
    body holds the world's contents and a save header holds the account id and
    the world name, so non-negotiables 11 and 12 make any structure carrying
    them an echo path. This carries counts, version scalars and exception TYPE
    NAMES - no bytes, no strings from a save, no paths.

    Attributes:
        files: Saves whose header parsed.
        measured: Of those, saves whose pair has a measured body layout.
        walked: Of those, saves whose body walked to its exact final byte.
        pairs: The distinct pairs walked, as version scalars.
        failures: Exception type names from any save that did not walk.
    """

    files: int
    measured: int
    walked: int
    pairs: tuple[tuple[int, int], ...]
    failures: tuple[str, ...]


def _sweep_the_real_library() -> _RealSweep | None:
    """Walk every real save on this machine and return COUNTS ONLY.

    NOTHING RAISES WITH BYTES IN FLIGHT, and the containment is deliberate
    rather than habitual. pytest renders the ARGUMENTS of every frame in a
    failing traceback - no ``--showlocals``, no opt-in - so an exception
    escaping ``parse_body(body, ...)`` prints the head of a real save body into
    the test log. Measured on this machine by planting a marker in a bytes
    argument of a raising frame: it appeared twice in pytest's output.

    So every step is wrapped and every failure is reduced to a type NAME here,
    inside the helper, before it can reach a frame anyone renders. The broad
    catch is what makes that total: a narrower one would let an unexpected
    exception type escape carrying the bytes, which is the exact leak the guard
    exists to close. The type name is preserved, so a genuine defect is still
    diagnosable - it surfaces as ``walked`` short of ``measured`` with the type
    named, rather than as a traceback nobody may print.

    Returns:
        The sweep, or None when no save library is reachable. Never returns or
        logs a path, a body, or any decoded string.
    """
    root = locate.resolve_save_root()
    account = locate.resolve_account_dir(root) if root is not None else None
    if account is None:
        return None

    files = measured = walked = 0
    pairs: set[tuple[int, int]] = set()
    failures: list[str] = []
    for path in sorted(account.glob("*.sav")):
        try:
            data = path.read_bytes()
            parsed = header.parse_header(data)
        except (OSError, header.HeaderError):
            continue
        files += 1
        pair = (parsed.header_version, parsed.save_version)
        if pair not in objects.MEASURED_BODY_LAYOUTS:
            continue
        measured += 1
        try:
            body = chunks.decompress_body(
                data, parsed.body_offset, header_version=parsed.header_version
            ).payload
            table = objects.parse_body(
                body, save_version=parsed.save_version, header_version=parsed.header_version
            )
            exact = table.body_consumed == len(body) - table.body_prefix_width
        # BROAD BY DESIGN - see the docstring. A narrower catch would let an
        # unexpected exception type escape carrying the save bytes, which is the
        # leak this helper exists to close. The type NAME is preserved.
        except Exception as exc:
            failures.append(type(exc).__name__)
            continue
        if exact:
            walked += 1
            pairs.add(pair)
        else:
            failures.append("IncompleteWalk")
    return _RealSweep(
        files=files,
        measured=measured,
        walked=walked,
        pairs=tuple(sorted(pairs)),
        failures=tuple(sorted(set(failures))),
    )


def test_every_real_save_of_a_measured_pair_walks_to_the_end_of_its_body() -> None:
    """THE ACCEPTANCE FOR CS-407, and the only evidence here the corpus cannot fake.

    The synthetic corpus can only ever agree with whoever wrote it. These bytes
    were produced by the game, so this is the assertion that decides whether the
    grammar is right - and it sweeps the WHOLE library rather than one file,
    because a single file passing is what the previous wave already had.

    WHAT A GREEN RUN HERE MEANS, EXACTLY. Every real save walks its framing to
    the final byte with nothing left over. It does NOT mean the bodies are
    understood: roughly three quarters of every one of them is opaque property
    payload stepped over by declared length.

    Skip-if-absent, because CI has no save library, and COUNTS ONLY.
    """
    sweep = _sweep_the_real_library()
    if sweep is None:
        pytest.skip("no save library on this machine - the real-save sweep is not gradeable here")

    assert sweep.files > 0, "a save library was found but no header in it parsed"
    assert sweep.measured == sweep.files, (
        f"{sweep.files - sweep.measured} of {sweep.files} real saves have a pair with no "
        "measured body layout; every pair in the real library was measured under CS-407"
    )
    assert sweep.failures == (), (
        f"{len(sweep.failures)} distinct failure kinds walking real bodies: {sweep.failures}"
    )
    assert sweep.walked == sweep.measured, (
        f"only {sweep.walked} of {sweep.measured} real saves walked to their final byte"
    )
    assert len(sweep.pairs) == len(objects.MEASURED_BODY_LAYOUTS), (
        f"the sweep exercised {len(sweep.pairs)} of "
        f"{len(objects.MEASURED_BODY_LAYOUTS)} measured pairs: {sweep.pairs}"
    )


def test_a_real_save_of_a_measured_pair_walks_to_the_end_of_its_body() -> None:
    """The acceptance CS-400 states and no synthetic fixture can supply.

    The corpus can only ever agree with whoever wrote it. This is the one
    assertion in the module whose subject was produced by the game.
    """
    found = _one_real_save_of_a_measured_pair()
    if found is None:
        pytest.skip("no real save of a measured body-layout pair is present on this machine")
    header_version, save_version, body = found

    # THE PARSE IS GUARDED, and the guard is not defensive habit - it closes a
    # leak MEASURED on this machine. pytest renders the ARGUMENTS of every frame
    # in a failing traceback, without --showlocals and without any opt-in. So an
    # exception escaping `parse_body(body, ...)` prints the head of a REAL SAVE
    # BODY into the test log, and a save body holds the world's contents
    # (CLAUDE.md non-negotiables 11 and 12). Verified by planting a marker in a
    # bytes argument of a raising frame: it appeared twice in pytest's output.
    #
    # So nothing may raise with the bytes in flight. The failure is converted
    # here into two closed-vocabulary scalars, with no exception in flight and
    # pytrace suppressed.
    try:
        table = objects.parse_body(body, save_version=save_version, header_version=header_version)
    except objects.ObjectError as exc:
        reason = type(exc).__name__
        pytest.fail(
            f"a real save of a measured pair did not walk: header {header_version}, "
            f"save {save_version}, {reason}",
            pytrace=False,
        )

    assert table.records != ()
    assert table.level_count > 1
    assert not [w for w in table.warnings if w.code == objects.WARN_UNPARSED_DATA_SECTION]
    assert table.body_consumed == len(body) - table.body_prefix_width


# ---------------------------------------------------------------------------
# Seam discipline
# ---------------------------------------------------------------------------


def test_the_objects_module_reaches_for_no_sibling_but_the_property_map() -> None:
    """This module takes bytes, two version scalars and a parsed property map.

    Asserted on the parsed import graph rather than on a substring search, so
    ``from clockspeed.save.header import parse_header`` is caught as an import
    and a mention inside a docstring is not.
    """
    tree = ast.parse(Path(objects.__file__).read_text(encoding="utf-8"))

    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported.add(node.module)
            imported.update(f"{node.module}.{alias.name}" for alias in node.names)

    for sibling in _FORBIDDEN_SIBLINGS:
        assert f"clockspeed.save.{sibling}" not in imported


def test_the_module_never_opens_a_file() -> None:
    """Bytes in, model out. ``workdir.py`` is the only writer, and this reads none.

    ADR 0007 decision item 6 makes "no other save module writes" a static
    assertion; a module that never opens anything at all is trivially inside
    it, and this pins that property against a future convenience helper.
    """
    tree = ast.parse(Path(objects.__file__).read_text(encoding="utf-8"))
    called = {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    } | {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    for banned in ("open", "read_bytes", "write_bytes", "read_text", "write_text"):
        assert banned not in called


# ---------------------------------------------------------------------------
# CS-413 - ATTRIBUTING EACH PAYLOAD TO ITS RECORD
#
# CS-407 already LOCATED every payload: ``_read_level`` reads the object data
# section entry by entry and ``_check_section`` proves the extents tile it to
# the exact declared byte on all four real pairs. What it deliberately did NOT
# do is say WHICH record each extent belongs to, and it said so in as many
# words - "that the k-th payload belongs to the k-th record is an ASSUMPTION
# nothing has measured, so the seam stays 0 rather than carrying a plausible
# pairing".
#
# So the open question was never the framing. It was the ALIGNMENT, and the
# tests below are what turn it from an assumption into a measurement.
# ---------------------------------------------------------------------------


def test_every_record_carries_the_extent_of_its_own_payload() -> None:
    """The seam is populated, and the extents TILE the section without overlap.

    Corpus-only, so it pins the ARITHMETIC and claims nothing about the
    grammar - no fixture payload has real content in it. The tiling assertion
    is what makes this more than "the field is non-zero": a walker that handed
    every record the same extent, or extents in the wrong order, satisfies a
    non-zero check and fails here.
    """
    fixture = synthetic.SAVE_LEVELLED_V36
    body = _levelled_payload()
    table = objects.parse_body(
        body, save_version=fixture.save_version, header_version=fixture.header_version
    )

    assert table.records, "the levelled fixture must carry records"
    for record in table.records:
        assert record.body_length > 0, "every corpus payload has a non-zero declared extent"
        assert record.body_offset > 0, "a payload never starts at the body's first byte"
        assert record.body_offset + record.body_length <= len(body)

    extents = [(r.body_offset, r.body_length) for r in table.records]
    assert len(set(extents)) == len(extents), "no two records may share one payload"
    for (offset, length), (nxt, _) in itertools.pairwise(extents):
        assert offset + length <= nxt, "payload extents must not overlap and must ascend"


def _text(value: str) -> bytes:
    """Encode one length-prefixed UTF-8 string the way a body carries it.

    Local rather than borrowed from ``synthetic`` on purpose: the fixture this
    serves has to declare a count that DISAGREES with the bytes it writes, and
    ``SyntheticLevel.encode`` computes every size from its own content
    specifically so a fixture cannot do that.

    Args:
        value: The text.

    Returns:
        The int32 byte count, the text, and the null terminator.
    """
    raw = value.encode("ascii") + b"\x00"
    return struct.pack("<i", len(raw)) + raw


def _mismatched_entry_count_body(instance_name: str = "SyntheticThing_0") -> bytes:
    """A (10,36) body whose one level declares 1 record and 0 payload entries.

    THE SHAPE NO REAL SAVE HAS. Every level of every real save agrees on the two
    counts, so this is reachable only by construction - which is exactly why it
    is built here rather than left to a fixture. A level like this makes the
    k-th pairing UNDEFINED, and the walk must flag it rather than invent one.

    NO COUNT IS QUOTED HERE ON PURPOSE. An earlier revision of this docstring
    said "all 6173 levels", which was wrong by two and would have read as
    verified forever - CLAUDE.md section 4's "a hardcoded count in a doc is a
    lie with a timestamp on it", caught by an adversary. "Every level agrees" is
    the stronger claim anyway and it cannot go stale.

    Args:
        instance_name: The planted instance name. Varying it is what lets a
            caller prove the warning's detail does not depend on body content.

    Returns:
        The body, length prefix included.
    """
    record = (
        struct.pack("<i", 1)  # object_type: actor
        + _text("/Script/Synthetic.Build_Thing_C")
        + _text("SyntheticLevel")
        + _text(instance_name)
        + bytes(4)  # the save-36 transform delta
        + bytes(objects.TRANSFORM_BYTES)
        + struct.pack("<i", 0)  # was_placed_in_level
    )
    header_section = struct.pack("<i", 1) + record
    data_section = struct.pack("<i", 0)  # ZERO entries against ONE record
    level = (
        struct.pack("<i", len(header_section))
        + header_section
        + struct.pack("<i", len(data_section))
        + data_section
        + struct.pack("<i", 0)  # the persistent level's closing collectable block
    )
    body = struct.pack("<i", 0) + level + struct.pack("<i", 0)  # no named levels, then the trailer
    return struct.pack("<i", len(body)) + body


def test_a_level_whose_counts_disagree_is_flagged_and_attributes_nothing() -> None:
    """Undefined attribution is flagged and skipped, never invented (non-negotiable 7).

    The failure mode this closes is the quiet one. A walker that zipped the two
    lists would pair the records it could and drop the rest, reporting a world
    where some machines carry another machine's payload - a wrong answer with no
    warning on it. Refusing to pair at all is the only honest read, and it must
    not raise either, because the section still closes and the rest of the body
    is still walkable.
    """
    body = _mismatched_entry_count_body()

    table = objects.parse_body(body, save_version=_SAVE_36, header_version=_HEADER_10)

    assert len(table.records) == 1
    flagged = [w for w in table.warnings if w.code == objects.WARN_PAYLOAD_COUNT_DISAGREEMENT]
    assert len(flagged) == 1, "the level must be flagged exactly once"
    assert (flagged[0].expected, flagged[0].actual) == (1, 0)
    assert table.records[0].body_offset == 0, "an undefined pairing attributes nothing"
    assert table.records[0].body_length == 0
    assert not [w for w in table.warnings if w.code == objects.WARN_UNPARSED_DATA_SECTION], (
        "the body must still walk to its final byte"
    )


def test_the_payload_count_warning_detail_does_not_depend_on_body_content() -> None:
    """The new warning is an echo path like every other, so its text is pinned.

    ASSERTED AS INVARIANCE, NOT AS A SUBSTRING SEARCH. An earlier revision
    checked that the planted names were absent from the detail, which an
    adversary correctly called decoration: the detail is a module constant
    fetched by code, so that check can only fail if somebody edits the constant
    to contain the literal. Running the SAME level twice with DIFFERENT planted
    content and requiring an identical detail is a mechanism instead - it goes
    red for any detail built from the body, whatever the body happens to hold.
    """
    details = []
    for name in ("SyntheticThing_0", "CompletelyDifferentPlantedName_9"):
        table = objects.parse_body(
            _mismatched_entry_count_body(name),
            save_version=_SAVE_36,
            header_version=_HEADER_10,
        )
        # Selected by CODE, not by position: a warning appended ahead of this
        # one later would otherwise move the assertion onto a different string.
        # The unpacking is also the liveness control - it raises if the warning
        # never fired, so this cannot pass against a walk that flags nothing.
        (detail,) = [
            w.detail for w in table.warnings if w.code == objects.WARN_PAYLOAD_COUNT_DISAGREEMENT
        ]
        details.append(detail)

    assert details[0] == details[1], (
        "the warning detail changed when only the body content changed, so it is "
        "built from the body rather than from the fixed table - that is an echo path"
    )
    assert details[0].isascii()


def _read_text(body: bytes, at: int, end: int) -> tuple[str, int] | None:
    """Read one length-prefixed string, returning None rather than RAISING.

    A returning reader instead of a raising one is a privacy control, not a
    style choice. An exception raised mid-payload puts a frame holding the real
    save body on the traceback, and pytest renders the ARGUMENTS of every frame
    - so the cheapest way to guarantee no body reaches a log is to have no
    failure path that unwinds through one.

    Args:
        body: The decompressed body.
        at: Where the length prefix starts.
        end: The first byte past this payload.

    Returns:
        The text and the offset after it, or None if it does not read.
    """
    if at + 4 > end:
        return None
    (count,) = struct.unpack_from("<i", body, at)
    if count == 0:
        return ("", at + 4)
    if count < 0:
        width, terminator, encoding = -count * 2, 2, "utf-16-le"
    else:
        width, terminator, encoding = count, 1, "utf-8"
    if width > objects.MAX_STRING_BYTES or at + 4 + width > end:
        return None
    try:
        return (body[at + 4 : at + 4 + width - terminator].decode(encoding), at + 4 + width)
    except UnicodeDecodeError:
        return None


def _component_refs(body: bytes, offset: int, length: int) -> tuple[str, ...] | None:
    """Read the component reference list an ACTOR's payload opens with.

    MEASURED, not assumed: across the real library every actor payload opens
    ``[str][str][int32 n][n x (str, str)]``, and what follows is either the
    literal ``None`` terminator or a name paired with an Unreal property type
    word - 2481 of 2481 payloads in the two files this was first read on.

    Args:
        body: The decompressed body.
        offset: The payload's first byte.
        length: The payload's declared extent.

    Returns:
        The referenced instance names, or None if the head does not read.
    """
    end = offset + length
    at = offset
    # The parent reference: two strings, read only to step over them.
    for _ in range(2):
        step = _read_text(body, at, end)
        if step is None:
            return None
        at = step[1]
    if at + 4 > end:
        return None
    (count,) = struct.unpack_from("<i", body, at)
    at += 4
    if count < 0 or count > objects.MAX_OBJECTS:
        return None
    # Each reference is a PAIR of strings and only the second is the instance
    # name, so the pairs are read flat and the names sliced back out.
    flat: list[str] = []
    for _ in range(2 * count):
        step = _read_text(body, at, end)
        if step is None:
            return None
        flat.append(step[0])
        at = step[1]
    return tuple(flat[1::2])


@dataclass(frozen=True)
class _AttributionSweep:
    """What the attribution sweep observed, as scalars and nothing else.

    Every field is safe to render, for the reason :class:`_RealSweep` gives.

    Attributes:
        files: Saves of a measured pair whose body walked.
        records: Records seen across them.
        attributed: Of those, records carrying a payload extent inside the body.
        testable: Actor payloads that named at least one component, per shift.
        matched: Of those, ones whose every reference checks out, per shift.
        failures: Exception type names from any save that did not walk.
    """

    files: int
    records: int
    attributed: int
    testable: Mapping[int, int]
    matched: Mapping[int, int]
    failures: tuple[str, ...]


_SHIFTS: Final = (-1, 0, 1)


def _score_one_save(
    body: bytes,
    records: tuple[objects.ObjectRecord, ...],
    testable: dict[int, int],
    matched: dict[int, int],
) -> int:
    """Score one save's attribution at every shift, accumulating into the tallies.

    Args:
        body: The decompressed body.
        records: What the walk attributed.
        testable: Per-shift tally of actor payloads that named a component.
        matched: Per-shift tally of those whose references all check out.

    Returns:
        How many records carry an extent lying inside the body.
    """
    # Name to the SET of parents claiming it, so a reference only counts when
    # that set is exactly the one actor - a name claimed by two different
    # parents is ambiguous and must not resolve. Set-valued rather than
    # last-one-wins because two component records in the real library do share
    # a name (with the same parent), and collapsing them either way misreports.
    parents: dict[str, set[str | None]] = {}
    for record in records:
        if record.kind == objects.KIND_COMPONENT:
            parents.setdefault(record.instance_name, set()).add(record.parent)

    attributed = 0
    for index, record in enumerate(records):
        if record.body_offset > 0 and record.body_offset + record.body_length <= len(body):
            attributed += 1
        if record.kind != objects.KIND_ACTOR:
            continue
        for shift in _SHIFTS:
            other = index + shift
            if not 0 <= other < len(records):
                continue
            refs = _component_refs(body, records[other].body_offset, records[other].body_length)
            if not refs:
                continue
            testable[shift] += 1
            if all(parents.get(name) == {record.instance_name} for name in refs):
                matched[shift] += 1
    return attributed


def _sweep_payload_attribution() -> _AttributionSweep | None:
    """Cross-check the attributed alignment against the record table, per shift.

    THE ORACLE, and it is a cross-check between two regions of the file parsed
    INDEPENDENTLY of one another. The record table says which actor each
    component belongs to; the data section says which components each actor's
    payload lists. Neither derives from the other, so their agreement is
    evidence rather than a restatement - and running it at shifts -1 and +1 is
    what turns "the k-th pairing is consistent" into "the bytes REJECT every
    neighbouring pairing".

    Contained exactly as :func:`_sweep_the_real_library` is: every step wrapped,
    every failure reduced to a type NAME before it can reach a rendered frame,
    counts only out.

    Returns:
        The sweep, or None when no save library is reachable.
    """
    root = locate.resolve_save_root()
    account = locate.resolve_account_dir(root) if root is not None else None
    if account is None:
        return None

    files = seen = attributed = 0
    testable = dict.fromkeys(_SHIFTS, 0)
    matched = dict.fromkeys(_SHIFTS, 0)
    failures: list[str] = []
    for path in sorted(account.glob("*.sav")):
        try:
            data = path.read_bytes()
            parsed = header.parse_header(data)
        except (OSError, header.HeaderError):
            continue
        if (parsed.header_version, parsed.save_version) not in objects.MEASURED_BODY_LAYOUTS:
            continue
        # BROAD BY DESIGN, for the reason `_sweep_the_real_library` states: a
        # narrower catch lets an unexpected type escape carrying the bytes.
        try:
            body = chunks.decompress_body(
                data, parsed.body_offset, header_version=parsed.header_version
            ).payload
            records = objects.parse_body(
                body, save_version=parsed.save_version, header_version=parsed.header_version
            ).records
            attributed += _score_one_save(body, records, testable, matched)
            seen += len(records)
            files += 1
        except Exception as exc:
            failures.append(type(exc).__name__)
            continue
    return _AttributionSweep(
        files=files,
        records=seen,
        attributed=attributed,
        testable=MappingProxyType(testable),
        matched=MappingProxyType(matched),
        failures=tuple(sorted(set(failures))),
    )


def test_every_real_save_attributes_a_payload_extent_to_every_record() -> None:
    """THE FLOOR. Every record in every real save now points at its own payload.

    The corpus cannot carry this claim - its payloads are opaque filler - so
    this is the assertion that decides whether the seam is populated against
    bytes the game wrote.

    Skip-if-absent, because CI has no save library, and COUNTS ONLY.
    """
    sweep = _sweep_payload_attribution()
    if sweep is None:
        pytest.skip("no save library on this machine - the attribution sweep is not gradeable here")

    assert sweep.failures == (), (
        f"{len(sweep.failures)} distinct failure kinds walking real bodies: {sweep.failures}"
    )
    assert sweep.files > 0, "a save library was found but no measured pair walked"
    assert sweep.records > 0, "the real saves walked but produced no records"
    assert sweep.attributed == sweep.records, (
        f"only {sweep.attributed} of {sweep.records} real records carry a payload extent "
        "inside the body; the seam is populated for every record or the attribution is wrong"
    )


def test_the_payload_to_record_alignment_is_the_one_the_bytes_choose() -> None:
    """The alignment is MEASURED, and the neighbouring alignments are REJECTED.

    Without the shift controls this test says only "the pairing I chose is
    self-consistent", which is exactly the assumption CS-407 declined to make.
    With them it says the bytes discriminate: the k-th pairing satisfies the
    cross-check universally and both neighbours satisfy it never.

    A shift of one crosses a level boundary at each level's edges, so a stray
    match there would be honest noise rather than a defect - the assertion is
    written as zero because zero is what was observed, and a later save that
    produced one should be looked at rather than rounded away.
    """
    sweep = _sweep_payload_attribution()
    if sweep is None:
        pytest.skip("no save library on this machine - the attribution sweep is not gradeable here")

    assert sweep.testable[0] > 0, "no actor payload named a component, so nothing was tested"
    assert sweep.matched[0] == sweep.testable[0], (
        f"the k-th alignment checks out on only {sweep.matched[0]} of {sweep.testable[0]} "
        "actor payloads; it is the alignment the walk attributes, so it must hold universally"
    )
    for shift in (-1, 1):
        assert sweep.testable[shift] > 0, f"shift {shift:+d} tested nothing, so it is not a control"
        assert sweep.matched[shift] == 0, (
            f"shift {shift:+d} checks out on {sweep.matched[shift]} of {sweep.testable[shift]} "
            "actor payloads; a neighbouring alignment that also fits means the oracle does "
            "not discriminate and the attribution is not measured"
        )
