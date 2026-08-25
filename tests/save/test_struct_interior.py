"""What a ``StructProperty``'s interior is, and which struct words this module reads - CS-829.

THE MEASUREMENT COMES BEFORE THE DECODER AND IS THE POINT OF THE MODULE. A
usmap schema names a struct's FIELDS. It says nothing about its SERIALIZATION
FORM, and Unreal writes some structs as a nested property tag list closed by
the same terminator a payload uses, and others as native raw bytes carrying no
tags at all. Which of the two a given struct word uses is not stated by any
shipped asset this project reads - so it is measured here, per word, over the
real library.

WHAT THE TWO FORMS ARE WORTH AS EVIDENCE IS NOT EQUAL, and that asymmetry is
the whole reason this module exists in the shape it does.

The TAG LIST form gives a reading that CAN FAIL. The interior is walked tag by
tag and its terminator must arrive EXACTLY at the byte the tag's declared size
points to. A wrong offset, a wrong tag grammar, a missing terminator or an
overrun all produce a refusal rather than a value. Nothing about that closure is
arithmetic, so a population of them closing is evidence.

The NATIVE form gives no such reading. Its width is whatever the bytes are, a
partition of it is admitted because a division came out even, and a check that
cannot fail is not a check. That is the exact defect that got CS-830 refuted
after it had already merged, and this module does not repeat it: the native
form is CLASSIFIED here and DECODED NOWHERE.

THE CLASSIFICATION IS THE FALSIFIABLE CLAIM, not the decode. A struct's
serialization form is a property of the struct TYPE and not of the instance, so
a word that classifies both ways in one corpus refutes it. That is what
:func:`test_no_struct_word_in_the_library_is_written_in_both_forms` asserts, and
it is the assertion the per-word equality below rests on - without it, an
equality over "the instances that decoded" would hold by construction.

GRADED PER WORD AND NEVER OVER THE POOL. A threshold summed over a population
is met by its strongest member: pooling the three container words is precisely
how CS-830 shipped a word with no element-grammar evidence at all behind a word
that had plenty. Every quantifier here that ranges over a set is also asserted
per member of that set.

THE VOCABULARY IS DERIVED AND NOT TRANSCRIBED. It comes from the shipped
``FactoryGame.usmap`` at run time, joined against the words the corpus actually
carries. No struct word is written into this file or into
:mod:`clockspeed.save.objects`, which is what keeps the population from being a
hand-maintained list that rots.

COUNTS ONLY LEAVE THIS MODULE. No assertion message renders a struct word, a
property name, a decoded value, a path, a world name or an account id. The
sweep types below hold integers keyed by strings and repr only the integers,
on the same terms as ``tests/save/test_container_elements.py``.

NEEDS NO GAME FOR MOST OF WHAT IS HERE. Every synthetic case runs on a machine
with no install and no save library. The library cases skip there.
"""

from __future__ import annotations

import struct
from collections.abc import Mapping
from dataclasses import dataclass, field
from functools import lru_cache
from types import MappingProxyType
from typing import Final

import pytest

from clockspeed.save import chunks, header, objects, usmap
from tests.save import reach_guard, test_decode_oracles, test_properties

# ---------------------------------------------------------------------------
# Synthetic fixtures - the tag grammar is IMPORTED rather than transcribed
# ---------------------------------------------------------------------------

#: A string that appears in no shipped constant, planted so that a repr
#: carrying it can only have got it from the fixture.
_LEAK_MARKER: Final = "ClockspeedStructInteriorLeakMarker"

#: A struct word this fixture invents. It is deliberately NOT a word any
#: shipped asset names: the synthetic cases grade the FORM, and borrowing a
#: real word would invite a reader to think they grade that struct.
_SYNTHETIC_STRUCT_WORD: Final = "SyntheticInteriorStruct"

#: A second invented word, so a case needing two of them says which is which.
_SYNTHETIC_INNER_STRUCT_WORD: Final = "SyntheticInnerStruct"

#: The value a synthetic interior's IntProperty carries. Chosen to be neither 0
#: nor 1 so a decoder returning a flag rather than the number is caught.
_INTERIOR_INT: Final = 7

#: A second, distinct value, so a two-field interior cannot pass by returning
#: one field twice.
_INTERIOR_SECOND_INT: Final = 11

#: How many bytes of raw payload the native fixture carries. It is not a
#: multiple of any tag grammar and its leading int32 is far too large to be a
#: string length, so no tag-list reading of it can close.
_NATIVE_BODY: Final = b"\xff\xff\xff\x7f" + bytes(range(12))


def _fstring(text: str) -> bytes:
    """One length-prefixed string, in the shape the payload reader takes.

    Args:
        text: ASCII text.

    Returns:
        The encoded string.
    """
    return test_properties._fstring(text)  # noqa: SLF001


def _struct_tag(name: str, struct_word: str, interior: bytes) -> bytes:
    """One ``StructProperty`` tag, its struct word and tag guid included.

    THE TAG SHAPE IS BUILT FROM THE SHIPPED GRAMMAR'S OWN CONSTANTS - the
    tag-extra string count and the guid width both come from
    :mod:`clockspeed.save.objects` - so this fixture cannot disagree with the
    reader about where a struct tag's value begins.

    Args:
        name: The property name.
        struct_word: The struct type word the tag carries.
        interior: The value bytes.

    Returns:
        The whole tag.
    """
    words = objects._TAG_EXTRA_STRINGS[objects.STRUCT_TYPE_WORD]  # noqa: SLF001
    extra = b"".join(_fstring(struct_word) for _ in range(words))
    extra += bytes(objects.GUID_BYTES)
    head = test_properties._tag_head(  # noqa: SLF001
        name, objects.STRUCT_TYPE_WORD, len(interior), extra
    )
    return head + interior


def _tag_list(*tags: bytes) -> bytes:
    """A nested property tag list, terminator included.

    Args:
        *tags: The encoded interior tags.

    Returns:
        The interior bytes.
    """
    return b"".join(tags) + _fstring(objects._PAYLOAD_TERMINATOR)  # noqa: SLF001


def _int_tag(name: str, value: int) -> bytes:
    """One IntProperty tag.

    Args:
        name: The property name.
        value: The int32 to carry.

    Returns:
        The whole tag.
    """
    return test_properties._scalar_tag(name, "IntProperty", struct.pack("<i", value))  # noqa: SLF001


def _read_payload_of(tags: bytes) -> objects.PropertyResult:
    """Decode a COMPONENT payload built from hand-written tags.

    A component payload opens directly with its tags, which keeps the fixture
    free of the actor head these cases have no use for.

    Args:
        tags: The encoded tags, the payload terminator excluded.

    Returns:
        The result.
    """
    payload = tags + _fstring(objects._PAYLOAD_TERMINATOR)  # noqa: SLF001
    body = test_properties._synthetic_body(payload)  # noqa: SLF001
    record = test_properties._synthetic_record(payload, actor=False)  # noqa: SLF001
    schema = test_properties._SYNTHETIC_SCHEMA  # noqa: SLF001
    return objects.read_properties(body, record, test_properties._synthetic_map(schema))  # noqa: SLF001


# ---------------------------------------------------------------------------
# The two forms, on synthetic bytes
# ---------------------------------------------------------------------------


def test_a_struct_written_as_a_tag_list_yields_its_decoded_interior() -> None:
    """The reading this module claims: a nested tag list, decoded by name.

    NEEDS NO SAVE LIBRARY.
    """
    interior = _tag_list(
        _int_tag("First", _INTERIOR_INT),
        _int_tag("Second", _INTERIOR_SECOND_INT),
    )

    result = _read_payload_of(_struct_tag("Body", _SYNTHETIC_STRUCT_WORD, interior))

    assert result.struct_tag_count == 1, (
        f"{result.struct_tag_count} struct tags were counted where the fixture wrote "
        "one, so the denominator this equality stands in is not the tag population"
    )
    assert len(result.struct_interiors) == 1, (
        f"{len(result.struct_interiors)} interiors came back for one struct tag whose "
        "interior is a well-formed tag list closing exactly at its declared end"
    )
    decoded = result.struct_interiors[0]
    assert decoded.struct_word == _SYNTHETIC_STRUCT_WORD
    assert decoded.form == objects.STRUCT_FORM_TAG_LIST
    assert dict(decoded.properties) == {
        "First": _INTERIOR_INT,
        "Second": _INTERIOR_SECOND_INT,
    }


def test_an_interior_whose_terminator_misses_the_declared_end_is_refused() -> None:
    """THE READING THAT CAN FAIL, made to fail.

    This is the case that separates a measurement from an arithmetic identity.
    The interior below is a PERFECTLY WELL-FORMED tag list - every tag reads,
    the terminator is present - and it is refused anyway, because it closes
    before the byte the tag's declared size points at. A decoder that returned
    what it could read would make the library equality hold by construction on
    any framing at all.

    NEEDS NO SAVE LIBRARY.
    """
    interior = _tag_list(_int_tag("First", _INTERIOR_INT))
    padded = interior + bytes(4)

    result = _read_payload_of(_struct_tag("Body", _SYNTHETIC_STRUCT_WORD, padded))

    assert result.struct_tag_count == 1, "the tag is still counted, decoded or not"
    assert result.struct_interiors == (), (
        f"{len(result.struct_interiors)} interiors came back for a tag list that "
        "terminates before its declared end. Returning the readable prefix is what "
        "would make every closure vacuous"
    )


def test_a_struct_written_as_native_bytes_is_flagged_and_never_raises() -> None:
    """Non-negotiable 7 at the struct level - unmeasured content is skipped.

    The native form is real, shipped, and NOT read here. What this asserts is
    that meeting one costs nothing: no exception, no value invented from a
    division, and the tag still counted in the denominator.

    NEEDS NO SAVE LIBRARY.
    """
    result = _read_payload_of(_struct_tag("Body", _SYNTHETIC_STRUCT_WORD, _NATIVE_BODY))

    assert result.struct_tag_count == 1
    assert result.struct_interiors == (), (
        "an interior came back for raw bytes carrying no tags at all, which means "
        "some reading was fitted to them rather than read out of them"
    )
    assert result.unmeasured_value_count == 1, (
        f"{result.unmeasured_value_count} tags were counted as unmodelled content "
        "where the fixture wrote one native struct. A struct this module cannot read "
        "is CONTENT IT HAS NOT MEASURED, not a walk that has lost its place - the "
        "top-level advance steps by the tag's own declared size and is unaffected"
    )


def test_the_two_forms_are_distinct_shipped_words() -> None:
    """A classification whose two labels collide records nothing.

    NEEDS NO SAVE LIBRARY - it is a claim about the repo.
    """
    forms = (objects.STRUCT_FORM_TAG_LIST, objects.STRUCT_FORM_NATIVE)
    assert len(set(forms)) == len(forms), (
        "the struct form words are not distinct, so a per-word classification "
        "keyed on them cannot separate the form that is read from the one that is not"
    )
    assert objects.STRUCT_FORM_TAG_LIST in objects.STRUCT_FORMS_READ
    assert objects.STRUCT_FORM_NATIVE not in objects.STRUCT_FORMS_READ, (
        "the native form is recorded as one this module READS, which would claim a "
        "reading whose only discriminator is that a division came out even"
    )


def test_a_struct_nested_inside_a_struct_decodes_to_its_own_interior() -> None:
    """Nesting is real in this format and the reader recurses into it.

    NEEDS NO SAVE LIBRARY.
    """
    inner = _tag_list(_int_tag("Deep", _INTERIOR_SECOND_INT))
    outer = _tag_list(
        _int_tag("First", _INTERIOR_INT),
        _struct_tag("Nested", _SYNTHETIC_INNER_STRUCT_WORD, inner),
    )

    result = _read_payload_of(_struct_tag("Body", _SYNTHETIC_STRUCT_WORD, outer))

    assert len(result.struct_interiors) == 1, "only the TOP-LEVEL tag is a top-level tag"
    top = result.struct_interiors[0]
    assert top.properties["First"] == _INTERIOR_INT
    nested = top.properties["Nested"]
    assert isinstance(nested, objects.StructValue), (
        "a nested struct tag came back as something other than a decoded interior, so "
        "the recursion either did not happen or returned a shape nothing models"
    )
    assert nested.struct_word == _SYNTHETIC_INNER_STRUCT_WORD
    assert dict(nested.properties) == {"Deep": _INTERIOR_SECOND_INT}


def test_nesting_stops_at_the_ceiling_and_reports_it_rather_than_recursing() -> None:
    """A depth ceiling, asserted by REACHING it rather than by reading it.

    THE FIRST DRAFT OF THIS TEST ASSERTED THE WRONG THING and the module was
    right. It expected the OUTERMOST interior to be refused when something deep
    inside it hit the ceiling. That would throw away a stack of exact,
    terminator-checked readings to avoid admitting one unread level, which is
    the opposite of non-negotiable 7: the too-deep struct is unmodelled content,
    it is flagged and skipped, and every reading above it is still a reading
    that closed at its own declared end.

    So what is asserted is the property that actually matters. The chain decodes
    down to the ceiling, the level AT the ceiling reports the one it would not
    open as unmeasured rather than opening it, and nothing raises.

    NEEDS NO SAVE LIBRARY.
    """
    interior = _tag_list(_int_tag("Deep", _INTERIOR_INT))
    for _ in range(objects.MAX_STRUCT_DEPTH + 1):
        interior = _tag_list(_struct_tag("Nested", _SYNTHETIC_INNER_STRUCT_WORD, interior))

    result = _read_payload_of(_struct_tag("Body", _SYNTHETIC_STRUCT_WORD, interior))

    assert len(result.struct_interiors) == 1, (
        "the outermost interior was refused because something far inside it hit the "
        "ceiling, which discards exact readings to avoid admitting one unread level"
    )
    current = result.struct_interiors[0]
    seen = 0
    while isinstance(current.properties.get("Nested"), objects.StructValue):
        nested = current.properties["Nested"]
        assert isinstance(nested, objects.StructValue)
        assert nested.depth == current.depth + 1, (
            f"a nested interior reports depth {nested.depth} inside one at depth "
            f"{current.depth}, so the ceiling is counted against the wrong number"
        )
        current = nested
        seen += 1
        assert seen <= objects.MAX_STRUCT_DEPTH, "the chain runs past the ceiling"

    assert current.depth == objects.MAX_STRUCT_DEPTH, (
        f"the chain stopped at depth {current.depth} rather than at the shipped "
        "ceiling, so the ceiling is not what bounded it"
    )
    assert current.unmeasured == 1, (
        f"the interior at the ceiling reports {current.unmeasured} unmeasured tags "
        "where it declined to open exactly one nested struct. A decline that moves no "
        "counter is a value dropped in silence, which is the half of non-negotiable 7 "
        "with no second chance"
    )


def test_no_repr_the_struct_decode_adds_renders_a_name_a_value_or_a_word() -> None:
    """Every rendering this slice adds is counts only.

    A test runner reprs a value BEFORE a human chooses what to print - pytest
    renders it as a frame local - so the quiet rendering has to be the only one
    available. The struct WORD is withheld on the same terms
    :class:`objects.ContainerValue` withholds it: it is read out of the save's
    own bytes, and what a repr owes is structure.

    NEEDS NO SAVE LIBRARY.
    """
    interior = _tag_list(_int_tag(f"{_LEAK_MARKER}_NAME", _INTERIOR_INT))
    result = _read_payload_of(_struct_tag("Body", f"{_LEAK_MARKER}_WORD", interior))

    assert len(result.struct_interiors) == 1, "the fixture decoded nothing, so this grades nothing"
    renderings = (
        repr(result),
        repr(result.struct_interiors),
        repr(result.struct_interiors[0]),
        str(result.struct_interiors[0]),
        f"{result.struct_interiors[0]}",
    )
    for rendering in renderings:
        assert _LEAK_MARKER not in rendering, (
            f"a struct-decode rendering carries a decoded name or a struct word:\n  {rendering}"
        )
    # Non-vacuity: a repr rendering nothing at all would pass the loop above
    # while telling an operator nothing.
    assert "properties=1" in repr(result.struct_interiors[0])


# ---------------------------------------------------------------------------
# The module's own record of what it does and does not read
# ---------------------------------------------------------------------------


def test_the_region_record_still_names_the_struct_interior_and_says_what_is_read() -> None:
    """A partial recorded as prose is not resumable - CS-412.

    The entry must SURVIVE this slice, because five of the words the corpus
    carries are still unread. What it may not do is go on saying that every
    byte of the region is unmeasured while a decoder ships for one of its two
    forms.

    NEEDS NO SAVE LIBRARY - it is a claim about the repo.
    """
    entry = objects.UNMEASURED_PAYLOAD_REGIONS.get(objects.STRUCT_TYPE_WORD)
    assert entry is not None, (
        "the StructProperty region entry is gone while the native form is still "
        "unread, which records the region as closed when it is not"
    )
    assert objects.STRUCT_FORM_NATIVE in entry, (
        "the region entry does not name the form that is still unread, so a later "
        "slice cannot tell from it what is left"
    )
    assert objects.STRUCT_FORM_TAG_LIST in entry, (
        "the region entry does not name the form that IS read, so it goes on "
        "describing the whole interior as opaque while a decoder ships for half of it"
    )


def test_the_declined_reading_records_that_a_discrimination_test_now_exists() -> None:
    """The decline is narrowed, not deleted - the native form still declines.

    NEEDS NO SAVE LIBRARY - it is a claim about the repo.
    """
    declined = objects.DECLINED_VALUE_READINGS.get(objects.STRUCT_TYPE_WORD)
    assert declined is not None, (
        "StructProperty left DECLINED_VALUE_READINGS while its native form is still "
        "unread, which claims a top-level value reading this module does not have"
    )
    assert objects.STRUCT_FORM_NATIVE in declined[1], (
        "the decline does not say WHICH form it declines, so it reads as a decline of "
        "the whole type while a discrimination test now ships for the tag-list form"
    )


def test_the_struct_word_is_not_transcribed_into_a_shipped_vocabulary() -> None:
    """DO NOT hand-write a struct vocabulary - the item note's own instruction.

    The module may name the two FORMS, which are this project's own
    classification words. It may not name a struct TYPE word, which is game
    content and would be the hand-maintained list this project has repeatedly
    recorded as the thing that rots.

    NEEDS NO SAVE LIBRARY - it is a claim about the repo.
    """
    shipped: set[str] = set()
    for name in dir(objects):
        if name.startswith(("STRUCT_WORDS", "_STRUCT_WORDS")):
            shipped.add(name)
    assert not shipped, (
        f"{len(shipped)} shipped names look like a transcribed struct vocabulary. The "
        "population is derived from the usmap and the corpus at run time, and a list "
        "in the module is a second, silent source of truth for it"
    )


# ---------------------------------------------------------------------------
# The real library - CS-829's acceptance
# ---------------------------------------------------------------------------


@dataclass
class _StructTally:
    """The sweep's running accumulators.

    COUNTS ONLY. Every value is an integer. The KEYS are struct words read out
    of the save, which is exactly why this type's repr renders none of them -
    see :class:`_StructSweep`.

    Attributes:
        saves: How many saves of a tagged pair were walked.
        records: How many records the reader was asked about.
        tags: Struct tags stepped over, by struct word.
        decoded: Struct tags that yielded an interior, by struct word.
        interior_tags: Interior tags STEPPED OVER, by struct word - decoded or
            not. The denominator, on the same terms as ``tags`` one level up.
        interior_values: Interior tags that yielded a VALUE, by struct word.
            SEPARATE FROM THE FIELD ABOVE, and the separation is a finding: a
            struct whose every interior tag is itself a NATIVE struct closes its
            framing exactly while decoding nothing at all. That is the extent
            versus content distinction CS-843 turns on, seen one level down.
        usmap_named: Struct words the shipped usmap declares a schema for.
        field_hits: Interior tag names the usmap declares for that struct.
        field_misses: Interior tag names it does not.
        miss_words: Struct words carrying at least one miss.
        failures: Exception TYPE NAMES, and nothing else about them.
    """

    saves: int = 0
    records: int = 0
    tags: dict[str, int] = field(default_factory=dict)
    decoded: dict[str, int] = field(default_factory=dict)
    interior_tags: dict[str, int] = field(default_factory=dict)
    interior_values: dict[str, int] = field(default_factory=dict)
    usmap_named: set[str] = field(default_factory=set)
    field_hits: int = 0
    field_misses: int = 0
    miss_words: set[str] = field(default_factory=set)
    failures: list[str] = field(default_factory=list)


@dataclass(frozen=True, repr=False)
class _StructSweep:
    """COUNTS ONLY. No field here reaches a repr carrying a word or a path.

    THE MAPPINGS ARE KEYED BY STRUCT WORD AND THE REPR RENDERS NEITHER THE KEYS
    NOR THE PAIRS. CS-830's sweep could repr its keys because a container word
    is a shipped constant; a struct word is read out of the save, so only the
    SIZE of each mapping and the SUM of its values leave here.

    Attributes:
        saves: How many saves of a tagged pair were walked.
        records: How many records the reader was asked about.
        tags: Struct tags stepped over, by struct word.
        decoded: Struct tags that yielded an interior, by struct word.
        interior_tags: Interior tags STEPPED OVER, by struct word.
        interior_values: Interior tags that yielded a value, by struct word.
        usmap_named: Struct words the shipped usmap declares a schema for.
        field_hits: Interior tag names the usmap declares for that struct.
        field_misses: Interior tag names it does not.
        miss_words: Struct words carrying at least one miss.
        failures: Exception TYPE NAMES, and nothing else about them.
    """

    saves: int
    records: int
    tags: Mapping[str, int]
    decoded: Mapping[str, int]
    interior_tags: Mapping[str, int]
    interior_values: Mapping[str, int]
    usmap_named: frozenset[str]
    field_hits: int
    field_misses: int
    miss_words: frozenset[str]
    failures: tuple[str, ...]

    def __repr__(self) -> str:
        """Render counts only, and withhold every struct word.

        Returns:
            The safe rendering.
        """
        return (
            f"{type(self).__name__}(saves={self.saves}, records={self.records}, "
            f"words={len(self.tags)}, tags={sum(self.tags.values())}, "
            f"decoded={sum(self.decoded.values())}, "
            f"interior_tags={sum(self.interior_tags.values())}, "
            f"interior_values={sum(self.interior_values.values())}, "
            f"usmap_named={len(self.usmap_named)}, "
            f"field_hits={self.field_hits}, field_misses={self.field_misses}, "
            f"miss_words={len(self.miss_words)}, failures={self.failures})"
        )

    @property
    def words_read(self) -> frozenset[str]:
        """The struct words every instance of which yielded an interior.

        Returns:
            The words whose whole population decoded.
        """
        return frozenset(w for w, n in self.tags.items() if self.decoded.get(w, 0) == n)

    @property
    def words_unread(self) -> frozenset[str]:
        """The struct words NO instance of which yielded an interior.

        Returns:
            The words whose whole population was refused.
        """
        return frozenset(w for w in self.tags if self.decoded.get(w, 0) == 0)

    @property
    def words_mixed(self) -> frozenset[str]:
        """The struct words that classified BOTH ways in one corpus.

        A non-empty answer refutes the claim the per-word equality rests on -
        that the serialization form is a property of the struct TYPE.

        Returns:
            The words carrying both a decoded and a refused instance.
        """
        return frozenset(self.tags) - self.words_read - self.words_unread


def _schema_field_names(property_map: usmap.PropertyMap, word: str) -> frozenset[str]:
    """Every property name the usmap declares for a struct, super chain included.

    CASE-FOLDED, and that is measured rather than tidy. Unreal compares an
    FName case-insensitively, and this corpus carries a field whose save
    spelling and whose usmap spelling differ only in the first letter's case.
    A case-SENSITIVE join reports that as a field the asset does not declare,
    which is a wrong answer to the question this cross-check asks.

    Args:
        property_map: The parsed mapping.
        word: The struct type word.

    Returns:
        The declared names, case-folded.
    """
    names: set[str] = set()
    seen: set[str] = set()
    current: str | None = word
    while current is not None and current not in seen and len(seen) < _MAX_SUPER_CHAIN:
        seen.add(current)
        schema = property_map.schemas.get(current)
        if schema is None:
            break
        for entry in schema.properties:
            names.add(entry.name.casefold())
        current = schema.super_name
    return frozenset(names)


#: A ceiling on the schema super chain, so a mapping whose super pointers cycle
#: cannot spin here. It bounds a walk; it is not a measurement of any chain.
_MAX_SUPER_CHAIN: Final = 64


def _fold_one_struct_tag(
    body: bytes,
    struct_word: str,
    at: int,
    end: int,
    property_map: usmap.PropertyMap,
    into: _StructTally,
) -> None:
    """Fold one top-level struct tag into the accumulator.

    SPLIT OUT OF THE SWEEP AND NOT INLINE, so the sweep's loop stays a loop
    over records and this stays the per-tag judgement. Only integers and set
    membership leave; the struct word and every interior name are keys and
    predicates here and reach no repr.

    Args:
        body: The decompressed body.
        struct_word: The struct type word the tag carried.
        at: The interior's first byte.
        end: The first byte past the interior.
        property_map: The parsed usmap.
        into: The accumulator, mutated in place.
    """
    into.tags[struct_word] = into.tags.get(struct_word, 0) + 1
    if struct_word in property_map.schemas:
        into.usmap_named.add(struct_word)
    decoded = objects.decode_struct_interior(body, struct_word, at, end)
    if decoded is None:
        return
    into.decoded[struct_word] = into.decoded.get(struct_word, 0) + 1
    # THE TAG TOTAL, NOT THE VALUE TOTAL. An interior tag carrying a type this
    # module does not decode is still a tag the walk stepped over, and folding
    # only the decoded ones made a struct whose every field is a NATIVE struct
    # look like a zero-tag interior.
    stepped = len(decoded.properties) + decoded.unmeasured + decoded.disagreed
    into.interior_tags[struct_word] = into.interior_tags.get(struct_word, 0) + stepped
    into.interior_values[struct_word] = into.interior_values.get(struct_word, 0) + len(
        decoded.properties
    )
    declared = _schema_field_names(property_map, struct_word)
    for interior_name in decoded.properties:
        if interior_name.casefold() in declared:
            into.field_hits += 1
        else:
            into.field_misses += 1
            into.miss_words.add(struct_word)


def _sweep_one_save(
    data: bytes, parsed: header.SaveHeader, property_map: usmap.PropertyMap, into: _StructTally
) -> None:
    """Walk one save and fold its top-level struct tags into the accumulator.

    THE CALLER HOLDS THE ``try``. This function is allowed to raise; its only
    call site is inside the sweep's broad handler, which reduces whatever comes
    out to a type name before any frame holding ``data`` or ``body`` is
    rendered.

    IT WALKS WITH THE SHIPPED READER AND DECODES WITH THE SHIPPED DECODER, so
    it grades neither. What it contributes is the POPULATION - a struct tag
    total taken OUTSIDE ``objects._walk_payload`` - and the equality that total
    stands in.

    Args:
        data: The save file's bytes.
        parsed: Its parsed header.
        property_map: The parsed usmap.
        into: The accumulator, mutated in place.
    """
    body = chunks.decompress_body(
        data, parsed.body_offset, header_version=parsed.header_version
    ).payload
    table = objects.parse_body(
        body, save_version=parsed.save_version, header_version=parsed.header_version
    )
    into.saves += 1
    for record in table.records:
        into.records += 1
        end = record.body_offset + record.body_length
        start: int | None = record.body_offset
        if record.kind == objects.KIND_ACTOR:
            start = objects._skip_actor_head(body, record.body_offset, end)  # noqa: SLF001
        if start is None:
            continue
        walked = test_decode_oracles._walk_with_the_shipped_reader(body, start, end)  # noqa: SLF001
        if walked is None:
            continue
        at = start
        for _name, word, value_at, size in walked:
            head = at
            at = value_at + size
            if word != objects.STRUCT_TYPE_WORD:
                continue
            name_read = objects._payload_text(body, head, end)  # noqa: SLF001
            if name_read is None:
                continue
            words = objects._container_element_words(  # noqa: SLF001
                body, name_read[1], end, objects.STRUCT_TYPE_WORD
            )
            if words is None or len(words) != 1:
                continue
            _fold_one_struct_tag(body, words[0], value_at, value_at + size, property_map, into)


@lru_cache(maxsize=1)
def _sweep_the_library() -> _StructSweep | None:
    """Walk every save on this machine once, or answer None when there is none.

    THE USMAP IS REQUIRED, not optional. The vocabulary this item is graded
    against is DERIVED from that shipped asset, so a machine without one cannot
    grade the acceptance and must skip rather than fall back to a list.

    Returns:
        The sweep, or None when no save library or no usmap is reachable.
    """
    saves = test_properties._library_save_paths()  # noqa: SLF001
    if not saves:
        return None
    try:
        usmap_path = usmap.default_usmap_path()
        property_map = None if usmap_path is None else usmap.load_usmap(usmap_path)
    except (Exception, SystemExit):
        # `SystemExit` is named because it is NOT an `Exception` - `except
        # Exception` alone lets it through, and it unwinds carrying the paths
        # these two calls hold exactly as any other type would.
        # Nothing is reported about this failure, not even a type name: the
        # discovery call and the load both hold an absolute path under a home
        # directory, and a traceback renderer showing locals prints it.
        property_map = None
    if property_map is None:
        return None

    tally = _StructTally()
    for path in saves:
        try:
            data = path.read_bytes()
            parsed = header.parse_header(data)
            _sweep_one_save(data, parsed, property_map, tally)
        except (Exception, SystemExit) as exc:
            # A TYPE NAME AND NOTHING ELSE. The library legitimately holds
            # saves of version pairs this project does not parse, and the
            # exception's own message and frames both reach the save's bytes.
            tally.failures.append(type(exc).__name__)
    return _StructSweep(
        saves=tally.saves,
        records=tally.records,
        tags=dict(tally.tags),
        decoded=dict(tally.decoded),
        interior_tags=dict(tally.interior_tags),
        interior_values=dict(tally.interior_values),
        usmap_named=frozenset(tally.usmap_named),
        field_hits=tally.field_hits,
        field_misses=tally.field_misses,
        miss_words=frozenset(tally.miss_words),
        failures=tuple(sorted(set(tally.failures))),
    )


def _sweep_or_skip() -> _StructSweep:
    """Fetch the sweep, skipping when this machine cannot grade it.

    THE FAILURE ASSERTION COMES FIRST so an unreadable library reddens rather
    than skipping quietly. Only an empty-but-clean walk skips, and "absent" has
    to be distinguishable from "present and broken".

    Returns:
        The sweep.
    """
    sweep = _sweep_the_library()
    if sweep is None:
        pytest.skip(
            "no save library or no shipped usmap on this machine - the struct "
            "vocabulary is derived from both and cannot be graded here"
        )
    assert not sweep.failures, (
        f"{len(sweep.failures)} save reads raised: {sweep.failures}. The type names are "
        "all that is reported - the message and the frames both reach the save's bytes"
    )
    if not sweep.tags:
        pytest.skip(
            "the save library holds no save of a version pair this project parses - "
            "there is no struct population here to grade"
        )
    return sweep


def test_every_struct_word_the_corpus_carries_is_named_by_the_shipped_usmap() -> None:
    """The vocabulary is DERIVED, and this is what makes that claim checkable.

    An EQUALITY, not a floor: the acceptance's population is "every struct type
    word the shipped vocabulary names", so a word the corpus carries that the
    usmap does NOT name would put an instance outside the population without
    anything saying so. Measured, the two sets coincide - and if a game update
    ships a struct the mapping does not declare, this is what says so.
    """
    sweep = _sweep_or_skip()

    unnamed = len(frozenset(sweep.tags) - sweep.usmap_named)
    assert unnamed == 0, (
        f"{unnamed} of {len(sweep.tags)} struct words the corpus carries are not "
        "declared by the shipped usmap, so the derived vocabulary does not cover the "
        "population this item is graded over. The words are deliberately not rendered"
    )


def test_no_struct_word_in_the_library_is_written_in_both_forms() -> None:
    """THE FALSIFIABLE CLAIM THIS WHOLE MODULE RESTS ON.

    The serialization form is a property of the struct TYPE, not of the
    instance. That is not arithmetic and it is not assumed: every instance is
    classified independently by whether its interior closes as a tag list at
    exactly its declared end, and a single word classifying both ways refutes
    it.

    WITHOUT THIS, THE PER-WORD EQUALITY BELOW WOULD BE VACUOUS. An equality
    over "the instances that decoded" holds by construction. It is this
    assertion that turns it into a claim about the format: every instance of a
    tag-list word decodes, so no member of that population is being quietly
    dropped from it.
    """
    sweep = _sweep_or_skip()

    mixed = len(sweep.words_mixed)
    assert mixed == 0, (
        f"{mixed} of {len(sweep.tags)} struct words are written BOTH as a tag list and "
        "as something that is not one. The serialization form is then not a property "
        "of the struct type, and the per-word equality this suite asserts is dropping "
        "members from its own population rather than reading them. The words are "
        "deliberately not rendered - they are read out of the save"
    )


def test_every_instance_of_every_tag_list_struct_word_yields_a_decoded_interior() -> None:
    """CS-829's acceptance, as an EQUALITY and asserted PER WORD.

    A POOLED THRESHOLD IS MET BY ITS STRONGEST MEMBER, which is exactly how
    CS-830 shipped a container word with no element-grammar evidence at all
    behind one that had plenty. So the equality is asserted twice: once over
    the pooled population, and once per member, and the per-member arm is the
    one that can actually fail.
    """
    sweep = _sweep_or_skip()

    read = sweep.words_read
    assert read, (
        "no struct word decoded on every instance, so this equality ranges over an "
        "empty set and would pass on a decoder that reads nothing at all"
    )

    pooled_tags = sum(sweep.tags[word] for word in read)
    pooled_decoded = sum(sweep.decoded.get(word, 0) for word in read)
    assert pooled_decoded == pooled_tags, (
        f"{pooled_decoded} interiors came back for {pooled_tags} tags of the words "
        "whose population is claimed read. A pooled equality is the WEAK arm here and "
        "it already fails, so the per-word arm below cannot hold either"
    )

    short = sum(1 for word in read if sweep.decoded.get(word, 0) != sweep.tags[word])
    assert short == 0, (
        f"{short} of {len(read)} struct words claimed read yielded fewer interiors than "
        "they carry tags. THE PER-WORD ARM IS THE ONE THAT MATTERS: a pooled total is "
        "met by its strongest member while its weakest goes unmeasured, which is the "
        "structural defect that refuted CS-830 after it had already merged"
    )

    barren = sum(1 for word in read if sweep.interior_tags.get(word, 0) == 0)
    assert barren == 0, (
        f"{barren} of {len(read)} struct words claimed read yield interiors holding no "
        "tags at all. A word whose every interior is a bare terminator is a word whose "
        "reading is 9 bytes of constant, and calling it decoded overstates it. ASSERTED "
        "PER WORD, never over the pool: a pooled tag total is met by its busiest word "
        "while a barren one goes unmeasured behind it"
    )

    values = sum(sweep.interior_values.get(word, 0) for word in read)
    assert values > 0, (
        f"{sum(sweep.interior_tags.get(w, 0) for w in read)} interior tags were stepped "
        "over and not one yielded a value, so the interiors close and decode nothing"
    )


def test_the_interiors_decode_to_fields_the_shipped_asset_declares() -> None:
    """A SECOND ORACLE THAT COULD HAVE DISAGREED, and one that partly does.

    The interior tag NAMES come out of the save's bytes. The field names come
    out of ``FactoryGame.usmap``. Nothing joins them but this test, so a wrong
    reading of the interior produces names the shipped asset does not declare -
    and two sources agreeing here is not two agents agreeing about one belief,
    which CLAUDE.md section 5 rules is no evidence at all.

    IT IS NOT ASSERTED AS AN EQUALITY, AND THAT IS MEASURED RATHER THAN
    CAUTIOUS. A residue of interior names is genuinely absent from this
    mapping: the save and the shipped usmap do not agree about every field of
    every struct. Asserting 100 per cent would be asserting something false, so
    what is asserted is that the residue stays CONFINED - a small, bounded set
    of words - and the day it spreads, this is what says so.
    """
    sweep = _sweep_or_skip()

    assert sweep.field_hits > 0, (
        "not one decoded interior name is a field the shipped usmap declares for that "
        "struct, so the second oracle agrees with nothing and this test grades nothing"
    )
    total = sweep.field_hits + sweep.field_misses
    assert sweep.field_misses * _MISS_RESIDUE_FACTOR < total, (
        f"{sweep.field_misses} of {total} decoded interior names are not fields the "
        "shipped usmap declares for their struct. A residue is expected and measured; "
        "this many means the interior reading and the shipped asset disagree about "
        "what these structs contain, which is the reading being wrong rather than the "
        "mapping being incomplete"
    )
    assert len(sweep.miss_words) < len(sweep.words_read), (
        f"{len(sweep.miss_words)} of {len(sweep.words_read)} words carry an interior "
        "name the usmap does not declare. CONFINEMENT IS THE CLAIM: a residue in a few "
        "words is a mapping that trails the build, where a residue in every word is a "
        "reading that is wrong everywhere and passing on a per-name percentage"
    )


#: How much of the cross-check may miss before the residue stops being one.
#: A BOUND, not a measurement: it is here so the assertion has a direction, and
#: the measured figure is far under it. Reading it as the observed rate would be
#: a restated number, which CLAUDE.md section 4 forbids.
_MISS_RESIDUE_FACTOR: Final = 20


def test_the_native_form_is_reached_from_inside_a_decoded_interior_too() -> None:
    """THE LIMIT IS NOT CONFINED TO THE TOP LEVEL, and that is measured.

    A struct word can close its framing EXACTLY - terminator on the declared
    byte, every tag stepped over - while decoding no values at all, because
    every field it holds is itself a struct written in the native form. The
    framing reading is real and the content reading is absent, which is the
    extent versus partition distinction CS-843 turns on, seen one level down.

    RECORDED RATHER THAN REPAIRED. Reading those fields needs the native form,
    and this slice does not have it. What this asserts is that the gap EXISTS,
    so the day it closes, this says the record is stale.
    """
    sweep = _sweep_or_skip()

    read = sweep.words_read
    stepped = sum(sweep.interior_tags.get(word) or 0 for word in read)
    valued = sum(sweep.interior_values.get(word) or 0 for word in read)
    assert valued < stepped, (
        f"every one of {stepped} interior tags now yields a value. THIS RECORD IS "
        "STALE: no interior tag is left carrying a type this module cannot read, so "
        "the nested half of the limit is closed and this test should go with it"
    )
    assert valued > 0, (
        "no interior tag yields a value at all, so this is not a gap in a reading - it "
        "is the absence of one, and recording it as a partial would overstate it"
    )


# ---------------------------------------------------------------------------
# What this finding does NOT reach - CS-843, measured rather than assumed
# ---------------------------------------------------------------------------


@lru_cache(maxsize=1)
def _uniform_width_struct_words() -> tuple[int, int, int] | None:
    """Classify every container the UNIFORM_WIDTH shape bounded, by struct form.

    THE UNIFORM_WIDTH SHAPE IS THE UNDISCRIMINATED ONE - CS-843. It divides a
    region by the declared count and is admitted because the division came out
    even, so the walk cannot fail while slots remain. What this asks is whether
    THIS slice's finding reaches it: an array of a TAG-LIST struct would have
    been bounded by the struct's own grammar instead, so any that reached the
    derived shape should be carrying a struct form this module does not read.

    IT DRIVES THE SHIPPED CONTAINER DECODER, so it grades neither that decoder
    nor this module's classifier - it JOINS them, and a join of two independent
    readings is the only place a disagreement can show up.

    Returns:
        How many uniform-width containers were seen, how many named an inner
        struct word, and how many of those words this module reads at top
        level. None when no library or no usmap is reachable.
    """
    sweep = _sweep_the_library()
    saves = test_properties._library_save_paths()  # noqa: SLF001
    if sweep is None or not saves:
        return None
    read_words = sweep.words_read

    seen = 0
    named = 0
    readable = 0
    for path in saves:
        try:
            data = path.read_bytes()
            parsed = header.parse_header(data)
            body = chunks.decompress_body(
                data, parsed.body_offset, header_version=parsed.header_version
            ).payload
            table = objects.parse_body(
                body, save_version=parsed.save_version, header_version=parsed.header_version
            )
        except (Exception, SystemExit):  # noqa: S112 - reporting it IS the leak
            # A save of a version pair this project does not parse. The sweep
            # above already reports the type names; nothing is added here,
            # because the frames reach the save's own bytes.
            continue
        for record in table.records:
            end = record.body_offset + record.body_length
            start: int | None = record.body_offset
            if record.kind == objects.KIND_ACTOR:
                start = objects._skip_actor_head(body, record.body_offset, end)  # noqa: SLF001
            if start is None:
                continue
            walked = test_decode_oracles._walk_with_the_shipped_reader(body, start, end)  # noqa: SLF001
            if walked is None:
                continue
            at = start
            for _name, word, value_at, size in walked:
                head = at
                at = value_at + size
                if word not in objects.CONTAINER_TYPE_WORDS:
                    continue
                step = _uniform_container_at(body, word, head, value_at, size, end)
                if step is None:
                    continue
                seen += 1
                if step.struct_word is None:
                    continue
                named += 1
                readable += 1 if step.struct_word in read_words else 0
    return (seen, named, readable)


def _uniform_container_at(
    body: bytes, word: str, name_at: int, value_at: int, size: int, end: int
) -> objects.ContainerValue | None:
    """The container at this tag, when the DERIVED width is what bounded it.

    Args:
        body: The decompressed body.
        word: The container type word.
        name_at: Where the tag's name begins.
        value_at: The value's first byte.
        size: The value's declared extent.
        end: The first byte past the payload.

    Returns:
        The container, or None when it did not decode or a stronger shape
        bounded it.
    """
    name_read = objects._payload_text(body, name_at, end)  # noqa: SLF001
    if name_read is None:
        return None
    element_words = objects._container_element_words(body, name_read[1], end, word)  # noqa: SLF001
    if element_words is None:
        return None
    got = objects._decode_container(body, word, element_words, value_at, size)  # noqa: SLF001
    if got is None or got.element_shape != objects.ELEMENT_SHAPE_UNIFORM_WIDTH:
        return None
    return got


def test_the_tag_list_finding_does_not_reach_the_undiscriminated_partition() -> None:
    """A MEASURED NEGATIVE, recorded so the next attempt does not repeat this one.

    CS-843 names three kinds of evidence that could settle a container's
    element partition, and the FIRST of them is the struct's own interior
    grammar - this slice. It does not reach: every container in this corpus
    that the derived uniform width bounded carries struct elements written in
    the form this module does NOT read, so the grammar that could have refuted
    a partition is absent from exactly the population that needs it.

    THE JOIN IS BETWEEN TWO INDEPENDENT READINGS AND COULD HAVE DISAGREED. The
    container decoder reaches the derived width only after the struct's own
    grammar has failed on that element; this module's classifier decides the
    same struct word's form from TOP-LEVEL tags in a different part of the
    save. A word this module reads at top level while an array of it falls back
    to a division would be a real contradiction, and this is what would say so.

    A RED HERE IS PROGRESS, IN EITHER DIRECTION. If the readable count rises,
    the interior grammar has reached the partition and CS-843's first arm is
    live. If the uniform-width population empties, the undiscriminated shape is
    gone from this corpus and the record is stale either way.
    """
    counts = _uniform_width_struct_words()
    if counts is None:
        pytest.skip("no save library or no shipped usmap on this machine")
    seen, named, readable = counts

    assert seen > 0, (
        "no container in this corpus is bounded by the derived uniform width any "
        "more. THIS RECORD IS STALE: the undiscriminated shape CS-843 is about is "
        "not present, so what this test measures the reach of no longer exists"
    )
    assert named > 0, (
        f"{seen} containers were bounded by the derived width and not one names an "
        "inner struct word, so this join has nothing to join and grades nothing"
    )
    assert readable == 0, (
        f"{readable} of {named} inner struct words are ones this module READS at top "
        "level, while an array of them was still bounded by dividing the region. THE "
        "TWO READINGS DISAGREE, and that is either the interior grammar now reaching "
        "CS-843's population - which is the item progressing - or the container "
        "fallback firing where a falsifiable reading was available, which is a defect. "
        "Establish which before changing this assertion"
    )


def test_a_struct_form_this_module_does_not_read_is_still_carried_by_the_corpus() -> None:
    """THE NARROWING, ASSERTED SO IT HAS A FAILURE DIRECTION - CS-829 is OPEN.

    CS-829's acceptance asks for an equality over EVERY struct word the shipped
    vocabulary names. This slice does not reach it: the words written as native
    raw bytes are classified here and decoded nowhere, because their width is
    whatever the bytes are and a partition of them would close by arithmetic.

    A CAVEAT IN A COMMENT ROTS; THIS DOES NOT. The narrowing is asserted, so the
    day the native form becomes readable - a shipped asset stating an element
    width, or any evidence that could have disagreed - this test goes RED and
    says the limit it records is stale. A RED HERE IS GOOD NEWS AND IS CS-829
    PROGRESSING.

    IT DELIBERATELY DOES NOT SAY HOW MANY WORDS OR WHICH. The operator plays
    this game and the corpus moves on the next autosave; what is asserted is
    that the unread population is NON-EMPTY, which is the shape of the limit
    rather than its size.
    """
    sweep = _sweep_or_skip()

    unread = sweep.words_unread
    assert unread, (
        "every struct word the corpus carries now yields a decoded interior on every "
        "instance. THIS TEST IS THE RECORD OF A NARROWING AND IT IS NOW STALE: the "
        "population CS-829's acceptance names is covered, so the item's equality can "
        "be asserted over the whole derived vocabulary and this test deleted with it. "
        "Check that the native form is READ rather than merely absent from this "
        "corpus before closing on it"
    )
    assert sweep.words_read, (
        "no struct word is read at all, so this is not a narrowing - it is the item "
        "untouched, and recording it as a limit would overstate what shipped"
    )


# ---------------------------------------------------------------------------
# The reach declaration - CS-471
#
# The package-wide guard in tests/save/test_reach_guard.py ENUMERATES this
# directory rather than waiting to be called, so a new library-reaching module
# is in scope the moment it exists. This module is one, and these two maps are
# what it owes.
# ---------------------------------------------------------------------------

#: Helpers that genuinely reach the save library, name to why each reaches. The
#: key is the function's own ``__name__`` and the reason comes from
#: ``reach_guard``, so a rename moves both together.
#:
#: ONE ENTRY, THOUGH THREE FUNCTIONS SWEEP, on the same terms as
#: ``tests/save/test_container_elements.py``. ``_sweep_the_library`` is the only
#: one that ever holds a save path or a usmap path; ``_sweep_one_save`` is
#: handed bytes and ``_sweep_or_skip`` takes a counts-only record back. Naming
#: either of them here would be an exemption outliving the code it described,
#: which is the failure the package-wide guard exists to catch.
_GRADED_LIBRARY_REACH: Final = MappingProxyType(
    {
        _sweep_the_library.__name__: reach_guard.REACH_READS_THE_LIBRARY,
        _uniform_width_struct_words.__name__: reach_guard.REACH_READS_THE_LIBRARY,
    }
)

#: Touches a primitive WITHOUT consuming a real save path, name to why. Empty:
#: every synthetic case in this module builds its bytes in the process and no
#: path-holding read is stubbed anywhere here.
_EXEMPT_LIBRARY_REACH: Final[Mapping[str, str]] = MappingProxyType({})
