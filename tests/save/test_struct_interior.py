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

The TAG LIST form gives a reading that CAN FAIL, and WHAT MAKES IT FAIL IS THE
TAG-GRAMMAR CHAIN rather than the closing comparison. Each interior tag's name,
type word, declared size and guid flag must read, and the cursor each one
computes must land on a tag that also reads, again and again, until a
terminator. An adversary measured the difference and it matters: loosening the
reader's exact close to "at or before the declared end" leaves this whole corpus
BIT-IDENTICAL, so that comparison is currently inert and is not the
discriminator an earlier version of this file claimed it was. The chain is,
and :func:`test_the_tag_grammar_pins_the_end_and_the_equality_is_not_what_discriminates`
measures its strength directly - of every end a sampled site's declared size
admits, exactly one closes.

The NATIVE form gives no such reading. Its width is whatever the bytes are, a
partition of it is admitted because a division came out even, and a check that
cannot fail is not a check. That is the exact defect that got CS-830 refuted
after it had already merged, and this module does not repeat it: the native
form is CLASSIFIED here and DECODED NOWHERE.

THE POPULATION IS DEFINED BY ARITHMETIC, NEVER BY THE DECODER'S OWN SUCCESS,
AND THAT IS THE CORRECTION TWO ADVERSARIES FORCED. The first version of this
module classified a struct word by whether the decoder read it, then asserted
that the decoder reads every instance of such a word. That is an IDENTITY: a
decoder refusing some word outright does not fail it, the word merely leaves the
class and is relabelled. It was proven mechanically against two hundred thousand
arbitrary wrong decoders, none of which it caught, and concretely by a mutant
that refuses the largest tag-list word entire - a majority of the whole struct
population - with the save suite still green.

The population is now every site whose DECLARED SIZE could hold a tag list at
all. A tag list is exactly a terminator wide when empty, and otherwise at least
one minimal tag plus a terminator; every width between those, and every width
below, is one no tag list can take. That criterion never calls the decoder, so a
word refused outright keeps its sites in the population and its refusals land in
a bounded residue - which is what makes the equality able to fail.

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

WHAT AN UPSTREAM WIDTH ERROR DOES HERE, STATED RATHER THAN GUARDED. This
module's population is the struct sites the SHIPPED payload walk reaches. A
mis-stated tag width desynchronises that walk, so the affected records stop
being walked at all and their sites leave the population instead of arriving in
it as refusals - the equality below then holds over a smaller world rather than
going red. Measured: mis-stating one container word's tag-extra width moves the
share of records the walk cannot follow by well under a factor of three, which
is too close to the share this corpus already carries - the version pair this
project does not parse - for any bound here to separate the two without
reddening the day the operator's library gains another such save. THE OWNER OF
THAT FAILURE IS THE WIDTH CENSUS IN ``tests/save/test_properties.py``, which
does redden and which caught a real defect in this slice's reader. It is
recorded here because a reader of this file would otherwise assume the equality
covers it.

COUNTS ONLY LEAVE THIS MODULE. No assertion message renders a struct word, a
property name, a decoded value, a path, a world name or an account id. The
sweep types below hold integers keyed by strings and repr only the integers,
on the same terms as ``tests/save/test_container_elements.py``.

NEEDS NO GAME FOR MOST OF WHAT IS HERE. Every synthetic case runs on a machine
with no install and no save library. The library cases skip there.
"""

from __future__ import annotations

import struct
from collections.abc import Mapping, Sequence
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


#: THE PROPERTY-GUID FLAG IS ONE BYTE. It is spelled here because
#: ``objects._skip_guid_flag`` spells it inline rather than exporting it; every
#: other term below comes from a shipped constant. A width this small cannot
#: drift silently - :func:`test_the_minimal_tag_list_widths_are_earned_not_asserted`
#: builds a tag of exactly this total and makes the SHIPPED reader consume it.
_GUID_FLAG_BYTES: Final = 1

#: The fewest bytes a length-prefixed string can occupy. A count of zero is a
#: WHOLE string to ``objects._payload_text`` - it returns the empty text and the
#: offset past the count - so the floor is the count field alone.
_MIN_PAYLOAD_STRING_BYTES: Final = objects.INT32_SIZE

#: The fewest bytes ONE interior tag can occupy: a name, a type word, the
#: declared size, the index field and a cleared property-guid flag. DERIVED from
#: the shipped grammar rather than counted by hand, and EARNED against the
#: shipped reader by the test named above.
_MIN_INTERIOR_TAG_BYTES: Final = (
    2 * _MIN_PAYLOAD_STRING_BYTES
    + objects.INT32_SIZE
    + objects._TAG_INDEX_FIELD_BYTES  # noqa: SLF001
    + _GUID_FLAG_BYTES
)

#: The exact width of an interior holding NOTHING - a bare terminator. Derived
#: from the shipped terminator name, and cross-checked against the fixture
#: encoder, which is a second expression of the same grammar.
_TERMINATOR_ONLY_BYTES: Final = objects.INT32_SIZE + len(objects._PAYLOAD_TERMINATOR) + 1  # noqa: SLF001

#: The fewest bytes an interior holding AT LEAST ONE tag can occupy.
_MIN_TAG_LIST_BYTES: Final = _MIN_INTERIOR_TAG_BYTES + _TERMINATOR_ONLY_BYTES


def _size_admits_a_tag_list(size: int) -> bool:
    """Whether a declared interior size COULD hold a tag list at all.

    THE POINT OF THIS FUNCTION IS WHAT IT DOES NOT LOOK AT. It never calls the
    decoder, never inspects a byte, and cannot know whether any reading
    succeeded. It is pure arithmetic over the shipped grammar: an interior is
    either exactly a bare terminator, or big enough for one minimal tag plus a
    terminator. Every width between those two, and every width below the
    terminator, is a size NO tag list can take.

    WHY IT HAS TO BE THIS WAY, AND IT IS THE WHOLE REPAIR. The first version of
    this module classified a struct word by whether the decoder succeeded on it,
    and then asserted that every instance of a successful word decodes. That is
    an IDENTITY - it holds for any decoder whatsoever, including one that
    refuses an arbitrary word outright, because such a word simply leaves the
    class and is relabelled. Two adversaries measured that mechanically and both
    refuted it. A population an equality is asserted over may not be defined by
    the outcome that equality reports.

    Args:
        size: The interior's declared extent, from the tag.

    Returns:
        Whether a tag list of that exact width is arithmetically possible.
    """
    return size == _TERMINATOR_ONLY_BYTES or size >= _MIN_TAG_LIST_BYTES


#: The struct tag's TYPE WORD as it appears in the bytes, length prefix and all.
#: DERIVED from the shipped constant through the fixture encoder that every
#: synthetic case in this module already builds its payloads with, so it is the
#: same grammar the shipped reader is made to consume in
#: :func:`test_the_minimal_tag_list_widths_are_earned_not_asserted` rather than a
#: second, silent transcription of the string layout.
_STRUCT_WORD_LITERAL: Final = _fstring(objects.STRUCT_TYPE_WORD)


def _census_hits(body: bytes, at: int, end: int) -> int:
    """How many struct tag type words the BYTES carry in this span.

    THE ONLY MEASUREMENT IN THIS MODULE THAT NO READER CAN MOVE, and that is
    its entire purpose. It calls no walk, no tag reader and no decoder: it
    counts occurrences of a fixed nineteen-byte literal. A reader that starts
    refusing everything changes every other number here and cannot change this
    one, which is what lets the arms below notice a population SHRINKING
    instead of quietly grading whatever survived.

    IT IS A SUPERSET AND IS NEVER USED AS AN EQUALITY AGAINST A SITE COUNT. The
    same literal stands at a nested interior tag, at a container's element type
    word, and inside any payload whose raw bytes happen to spell it, so the
    census total is far above the top-level site count and no arithmetic here
    pretends otherwise. What it is used for is CONSERVATION: which records the
    bytes say carry struct content, against which records the sweep reached.

    Args:
        body: The decompressed body.
        at: Where to start counting.
        end: The first byte past the span.

    Returns:
        How many times the literal occurs, counting overlaps as one each.
    """
    found = 0
    cursor = body.find(_STRUCT_WORD_LITERAL, at, end)
    while cursor != -1:
        found += 1
        cursor = body.find(_STRUCT_WORD_LITERAL, cursor + 1, end)
    return found


@dataclass
class _SaveShape:
    """One save's record outcome, in integers - the per-save reduction input.

    THE VERSION PAIR IS TWO INTEGERS OUT OF THE HEADER and is carried here
    because the reduction below needs to group by it. It is reduced to counts
    before it reaches :class:`_StructSweep`, so no pair ever reaches a repr -
    not because a build number is personal data, but because this module's rule
    is that only counts leave, and an exception argued case by case is how such
    a rule stops holding.

    Attributes:
        pair: The save and header version, in that order.
        records: How many records the save's table carried.
        unreached: How many of them the sweep never walked, for any reason.
    """

    pair: tuple[int, int]
    records: int
    unreached: int


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
        size_compatible: Sites whose DECLARED SIZE could hold a tag list, by
            word. THE POPULATION EVERY EQUALITY HERE IS ASSERTED OVER, and it is
            computed by :func:`_size_admits_a_tag_list` without consulting the
            decoder at all.
        size_excluded: Sites arithmetically incapable of being a tag list, by
            word. POSITIVE, INDEPENDENT EVIDENCE that a word is native - it owes
            nothing to any reader refusing anything.
        compatible_decoded: Size-compatible sites that decoded, by word.
        compatible_refused: Size-compatible sites that did NOT, by word. The
            residue, and the only place this suite's equality can fail.
        usmap_named: Struct words the shipped usmap declares a schema for.
        field_hits: Interior tag names the usmap declares for that struct.
        field_misses: Interior tag names it does not.
        miss_words: Struct words carrying at least one miss.
        failures: Exception TYPE NAMES, and nothing else about them.
        sites_seen: EVERY struct-typed tag the walk yielded, counted BEFORE the
            tag extra is read. THE DENOMINATOR THE REFUTATION DEMANDED - see
            :func:`_sweep_one_save` for why counting it any later is the defect.
        name_unread: Sites whose tag NAME would not re-read.
        word_unread: Sites whose tag EXTRA would not read, or read as a count
            the shipped tag-extra table does not state for a struct.
        wordless_compatible: How many of those two are size-compatible on
            arithmetic - so a reader failure lands in the residue with a size,
            rather than deleting a site that had one.
        bare_terminator_sites: Sites declaring exactly a bare terminator's
            width, which is the admission gate's empty-list disjunct. Counted
            from the walk's declared size alone, so no reader can move it.
        head_unread: Records whose ACTOR head would not step.
        unwalked: Records whose property walk broke before its terminator.
        census_body: Struct type words the BYTES carry, over the whole body.
        census_records: The same, summed over the records' declared extents.
        census_unreached: The same, over records the sweep never walked.
        shapes: One entry per save, for the per-save reduction.
        shipped_tags: The SHIPPED reader's OWN struct tag total, from
            ``PropertyResult.struct_tag_count`` - a denominator taken by a loop
            this module did not write, through an entry point it does not use
            for anything else here.
        shipped_interiors: The shipped reader's own decoded interior total.
    """

    saves: int = 0
    records: int = 0
    sites_seen: int = 0
    name_unread: int = 0
    word_unread: int = 0
    wordless_compatible: int = 0
    head_unread: int = 0
    unwalked: int = 0
    bare_terminator_sites: int = 0
    census_body: int = 0
    census_records: int = 0
    census_unreached: int = 0
    shipped_tags: int = 0
    shipped_interiors: int = 0
    shapes: list[_SaveShape] = field(default_factory=list)
    tags: dict[str, int] = field(default_factory=dict)
    decoded: dict[str, int] = field(default_factory=dict)
    interior_tags: dict[str, int] = field(default_factory=dict)
    interior_values: dict[str, int] = field(default_factory=dict)
    size_compatible: dict[str, int] = field(default_factory=dict)
    size_excluded: dict[str, int] = field(default_factory=dict)
    compatible_decoded: dict[str, int] = field(default_factory=dict)
    compatible_refused: dict[str, int] = field(default_factory=dict)
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
        size_compatible: Sites whose declared size could hold a tag list.
        size_excluded: Sites arithmetically incapable of being one.
        compatible_decoded: Size-compatible sites that decoded, by word.
        compatible_refused: Size-compatible sites that did not, by word.
        usmap_named: Struct words the shipped usmap declares a schema for.
        field_hits: Interior tag names the usmap declares for that struct.
        field_misses: Interior tag names it does not.
        miss_words: Struct words carrying at least one miss.
        failures: Exception TYPE NAMES, and nothing else about them.
        sites_seen: Every struct-typed tag the walk yielded, counted before the
            tag extra was read.
        name_unread: Sites whose tag name would not re-read.
        word_unread: Sites whose tag extra would not read.
        wordless_compatible: How many of those are size-compatible.
        head_unread: Records whose actor head would not step.
        unwalked: Records whose property walk broke.
        bare_terminator_sites: Sites whose declared size is EXACTLY a bare
            terminator - the empty-tag-list half of the admission gate.
        census_body: Struct type words the bytes carry, over the whole body.
        census_records: The same, over the records' declared extents.
        census_unreached: The same, over records the sweep never walked.
        partial_saves: Saves where SOME records walked and some did not.
        contested_pairs: Version pairs holding both a save the sweep walked
            entirely and a save it walked not at all.
        shipped_tags: The shipped reader's own struct tag total.
        shipped_interiors: The shipped reader's own decoded interior total.
    """

    saves: int
    records: int
    sites_seen: int
    name_unread: int
    word_unread: int
    wordless_compatible: int
    head_unread: int
    unwalked: int
    bare_terminator_sites: int
    census_body: int
    census_records: int
    census_unreached: int
    partial_saves: int
    contested_pairs: int
    shipped_tags: int
    shipped_interiors: int
    tags: Mapping[str, int]
    decoded: Mapping[str, int]
    interior_tags: Mapping[str, int]
    interior_values: Mapping[str, int]
    size_compatible: Mapping[str, int]
    size_excluded: Mapping[str, int]
    compatible_decoded: Mapping[str, int]
    compatible_refused: Mapping[str, int]
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
            f"sites_seen={self.sites_seen}, name_unread={self.name_unread}, "
            f"word_unread={self.word_unread}, "
            f"wordless_compatible={self.wordless_compatible}, "
            f"head_unread={self.head_unread}, unwalked={self.unwalked}, "
            f"bare_terminator_sites={self.bare_terminator_sites}, "
            f"census_body={self.census_body}, census_records={self.census_records}, "
            f"census_unreached={self.census_unreached}, "
            f"partial_saves={self.partial_saves}, "
            f"contested_pairs={self.contested_pairs}, "
            f"shipped_tags={self.shipped_tags}, "
            f"shipped_interiors={self.shipped_interiors}, "
            f"words={len(self.tags)}, tags={sum(self.tags.values())}, "
            f"decoded={sum(self.decoded.values())}, "
            f"interior_tags={sum(self.interior_tags.values())}, "
            f"interior_values={sum(self.interior_values.values())}, "
            f"size_compatible={sum(self.size_compatible.values())}, "
            f"size_excluded={sum(self.size_excluded.values())}, "
            f"compatible_decoded={sum(self.compatible_decoded.values())}, "
            f"compatible_refused={sum(self.compatible_refused.values())}, "
            f"usmap_named={len(self.usmap_named)}, "
            f"field_hits={self.field_hits}, field_misses={self.field_misses}, "
            f"miss_words={len(self.miss_words)}, failures={self.failures})"
        )

    @property
    def words_decoded_throughout(self) -> frozenset[str]:
        """The struct words every instance of which yielded an interior.

        THIS IS THE DECODER'S OWN SUCCESS SET AND IT MAY NEVER BE THE
        POPULATION OF AN EQUALITY ABOUT DECODING. Asserting "every instance of
        a word in this set decodes" is an IDENTITY that holds for any decoder at
        all: one that refuses some word outright does not fail the assertion, it
        simply drops that word out of the set. Two adversaries proved exactly
        that against the first version of this module. It survives only as ONE
        SIDE of the CS-843 join, where the other side is the container decoder's
        independent fallback and a disagreement is the whole point.

        Returns:
            The words whose whole population decoded.
        """
        return frozenset(w for w, n in self.tags.items() if self.decoded.get(w, 0) == n)

    @property
    def words_never_decoded(self) -> frozenset[str]:
        """The struct words NO instance of which yielded an interior.

        SUCCESS-DEFINED, on the same terms and with the same prohibition as
        :attr:`words_decoded_throughout`.

        Returns:
            The words whose whole population was refused.
        """
        return frozenset(w for w in self.tags if self.decoded.get(w, 0) == 0)

    @property
    def words_proven_native_by_size(self) -> frozenset[str]:
        """The struct words carrying a site NO tag list could occupy.

        POSITIVE EVIDENCE, AND THE ONLY KIND HERE THAT IS. A site whose declared
        size falls between a bare terminator and one minimal tag plus a
        terminator cannot be a tag list whatever any reader does, so a word
        holding one is native on arithmetic rather than on a refusal. This is
        what lets the equality below have a population the decoder did not
        choose.

        Returns:
            The words with at least one size-excluded site.
        """
        return frozenset(w for w, n in self.size_excluded.items() if n > 0)

    @property
    def words_mixed(self) -> frozenset[str]:
        """The struct words that classified BOTH ways in one corpus.

        A PER-INSTANCE DETECTOR, and it stays because it is a real one: an
        adversary measured it firing on a large share of width perturbations. It
        does NOT catch a failure that is total per word - the M5 counter-example
        below - and that is exactly why it cannot be the only guard.

        Returns:
            The words carrying both a decoded and a refused instance.
        """
        return frozenset(self.tags) - self.words_decoded_throughout - self.words_never_decoded

    @property
    def unexplained_refusals(self) -> Mapping[str, int]:
        """Size-compatible refusals in words with NO independent native evidence.

        THE HONEST RESIDUE. A size-compatible site that refuses is a site this
        module calls native on its READER'S WORD ALONE. Where the word also
        carries size-excluded sites, that word is independently native and the
        refusal is explained by its siblings. Where it does not, nothing but the
        reader says so - and that is the narrowing this slice records.

        Returns:
            Word to how many of its size-compatible sites refused, for words
            with no size-excluded site at all.
        """
        return {
            word: refused
            for word, refused in self.compatible_refused.items()
            if refused > 0 and self.size_excluded.get(word, 0) == 0
        }


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
    # THE CLASSIFICATION IS TAKEN BEFORE THE DECODER IS CALLED, and the order is
    # the repair rather than a style. Deciding the population from arithmetic
    # over the declared size, and only then asking whether the reading
    # succeeded, is what stops the equality below being a statement about its
    # own outcome.
    compatible = _size_admits_a_tag_list(end - at)
    bucket = into.size_compatible if compatible else into.size_excluded
    bucket[struct_word] = bucket.get(struct_word, 0) + 1
    decoded = objects.decode_struct_interior(body, struct_word, at, end)
    if compatible:
        landed = into.compatible_decoded if decoded is not None else into.compatible_refused
        landed[struct_word] = landed.get(struct_word, 0) + 1
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


def _struct_word_at(body: bytes, name_at: int, end: int, into: _StructTally) -> str | None:
    """The struct word one tag carries, COUNTING its own refusals on the way.

    THE WHOLE POINT IS THAT IT RETURNS None LOUDLY. Every reader between the
    walk and the decoder used to sit behind a bare ``continue`` in the sweep's
    loop, so a defect in any of them deleted the site from the denominator
    instead of landing it in the residue - and a grade computed over the
    survivors IMPROVES as the reader gets worse. Measured on this corpus: a
    four-line guard inside ``objects._container_element_words`` removed 22897 of
    45208 sites, dropped the size-compatible refusal count from 12 to 7, and the
    module still reported every arm green. Nothing about that loss was visible
    because nothing counted it.

    So the refusals are counted here and the caller keeps the site. The two are
    separated because they are different failures: a name that will not re-read
    means the walk and this module disagree about where the tag starts, and a
    tag extra that will not read means the struct word itself is unreachable.

    Args:
        body: The decompressed body.
        name_at: Where the tag's NAME begins - the walk's own cursor.
        end: The first byte past the payload.
        into: The accumulator, mutated in place.

    Returns:
        The struct word, or None when a reader between the walk and the decoder
        refused - in which case the refusal has been counted.
    """
    name_read = objects._payload_text(body, name_at, end)  # noqa: SLF001
    if name_read is None:
        into.name_unread += 1
        return None
    words = objects._container_element_words(  # noqa: SLF001
        body, name_read[1], end, objects.STRUCT_TYPE_WORD
    )
    if words is None or len(words) != _STRUCT_TAG_EXTRA_STRINGS:
        into.word_unread += 1
        return None
    return words[0]


#: How many strings a struct tag puts in its tag extra, READ OFF the shipped
#: table rather than written as ``1``. The census in ``tests/save/
#: test_properties.py`` mis-states that table's widths on the real module, and a
#: literal here would keep agreeing with itself while the shipped width moved.
_STRUCT_TAG_EXTRA_STRINGS: Final = objects._TAG_EXTRA_STRINGS[objects.STRUCT_TYPE_WORD]  # noqa: SLF001


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

    EVERY DROP IS COUNTED AND NOTHING LEAVES SILENTLY, which is the repair this
    revision exists for. Four readers stand between a record and a graded site:
    the actor-head step, the payload walk, the tag-name re-read and the tag
    extra. Each used to end in a bare ``continue``. Now each has a counter, and
    the records the first two refuse are additionally measured IN BYTES by
    :func:`_census_hits`, which no reader can move - so a record the sweep never
    opened still carries a number into the arms below.

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
    into.census_body += _census_hits(body, 0, len(body))
    records = 0
    unreached = 0
    for record in table.records:
        into.records += 1
        records += 1
        end = record.body_offset + record.body_length
        hits = _census_hits(body, record.body_offset, end)
        into.census_records += hits
        # THE SHIPPED READER'S OWN TOTALS, taken through an entry point this
        # module uses for nothing else. ``struct_tag_count`` is incremented in
        # ``objects._walk_payload`` BEFORE the struct word is read, so it is a
        # denominator no tag-extra defect can move - and it comes from a loop
        # written independently of the one below.
        shipped = objects.read_properties(body, record, property_map)
        into.shipped_tags += shipped.struct_tag_count
        into.shipped_interiors += len(shipped.struct_interiors)
        start: int | None = record.body_offset
        if record.kind == objects.KIND_ACTOR:
            start = objects._skip_actor_head(body, record.body_offset, end)  # noqa: SLF001
        if start is None:
            into.head_unread += 1
            into.census_unreached += hits
            unreached += 1
            continue
        walked = test_decode_oracles._walk_with_the_shipped_reader(body, start, end)  # noqa: SLF001
        if walked is None:
            into.unwalked += 1
            into.census_unreached += hits
            unreached += 1
            continue
        at = start
        for _name, word, value_at, size in walked:
            head = at
            at = value_at + size
            if word != objects.STRUCT_TYPE_WORD:
                continue
            # COUNTED HERE AND NOWHERE LATER. Every line below this one may
            # refuse; none of them may shrink the number this line just raised.
            into.sites_seen += 1
            if size == _TERMINATOR_ONLY_BYTES:
                into.bare_terminator_sites += 1
            struct_word = _struct_word_at(body, head, end, into)
            if struct_word is None:
                if _size_admits_a_tag_list(size):
                    into.wordless_compatible += 1
                continue
            _fold_one_struct_tag(body, struct_word, value_at, value_at + size, property_map, into)
    into.shapes.append(
        _SaveShape(
            pair=(parsed.save_version, parsed.header_version),
            records=records,
            unreached=unreached,
        )
    )


def _reduce_shapes(shapes: Sequence[_SaveShape]) -> tuple[int, int]:
    """Reduce the per-save outcomes to the two integers that grade them.

    WHY A RECORD LEAVING THE POPULATION NEEDS GRADING AT ALL. This corpus does
    carry records the payload walk refuses, and refusing them is CORRECT: they
    belong to a save version pair whose payload grammar this project has not
    measured, which ``objects.read_properties`` itself flags rather than parses.
    So "no record is ever unreached" is not assertable and pretending otherwise
    would assert something false.

    WHAT IS ASSERTABLE IS THE SHAPE OF THE LOSS, and it is far stronger than a
    ceiling. Measured over this library: refusal is all-or-nothing per SAVE -
    no save has some records walk and some refuse - and all-or-nothing per
    version PAIR - no pair holds both a save that walked entirely and one that
    did not. Those two facts are what a bad reader cannot fake. A defect that
    drops a fraction of records makes some save partial; a defect that drops one
    save whole makes its pair contested. Only a defect shaped exactly like a
    whole version pair escapes both, and
    :func:`test_the_sweep_reaches_every_struct_site_the_shipped_reader_counts`
    is what stands in front of that one.

    Args:
        shapes: One entry per save the sweep walked without raising.

    Returns:
        How many saves were reached only partially, and how many version pairs
        hold both a wholly-reached and a wholly-unreached save.
    """
    partial = sum(1 for shape in shapes if 0 < shape.unreached < shape.records)
    whole: set[tuple[int, int]] = set()
    none: set[tuple[int, int]] = set()
    for shape in shapes:
        if shape.records == 0:
            continue
        if shape.unreached == 0:
            whole.add(shape.pair)
        elif shape.unreached == shape.records:
            none.add(shape.pair)
    return (partial, len(whole & none))


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
    partial, contested = _reduce_shapes(tally.shapes)
    return _StructSweep(
        saves=tally.saves,
        records=tally.records,
        sites_seen=tally.sites_seen,
        name_unread=tally.name_unread,
        word_unread=tally.word_unread,
        wordless_compatible=tally.wordless_compatible,
        head_unread=tally.head_unread,
        unwalked=tally.unwalked,
        bare_terminator_sites=tally.bare_terminator_sites,
        census_body=tally.census_body,
        census_records=tally.census_records,
        census_unreached=tally.census_unreached,
        partial_saves=partial,
        contested_pairs=contested,
        shipped_tags=tally.shipped_tags,
        shipped_interiors=tally.shipped_interiors,
        tags=dict(tally.tags),
        decoded=dict(tally.decoded),
        interior_tags=dict(tally.interior_tags),
        interior_values=dict(tally.interior_values),
        size_compatible=dict(tally.size_compatible),
        size_excluded=dict(tally.size_excluded),
        compatible_decoded=dict(tally.compatible_decoded),
        compatible_refused=dict(tally.compatible_refused),
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
    if sweep.records == 0:
        pytest.skip(
            "the save library holds no save this project parses into a record table - "
            "there is no struct population here to grade"
        )
    # NO EVIDENCE IS A SKIP; EVIDENCE DESTROYED IS NOT, and the two used to be
    # the same line. The old form skipped whenever no struct word was collected,
    # which is the grade-improves-as-the-reader-worsens hole at its limit: a
    # reader refusing every site produced an empty vocabulary and a green run.
    # The BYTES decide instead. ``census_body`` counts struct type words with no
    # reader involved, so a library that genuinely carries none skips, and a
    # library that carries them inside records the sweep DID open must account
    # for them below rather than vanish.
    reached_hits = sweep.census_records - sweep.census_unreached
    if reached_hits == 0 and sweep.sites_seen == 0:
        pytest.skip(
            "every record this library holds belongs to a save version pair whose "
            "payload grammar this project does not read, so no struct site is "
            "reachable here and there is nothing to grade"
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


#: HOW MANY SIZE-COMPATIBLE SITES MAY REFUSE BEFORE THE READING IS IN DOUBT.
#: A BOUND WITH A DIRECTION, not a measurement: it is far above what this corpus
#: shows and far below what any of the counter-examples below produce. The M5
#: mutant - refusing the single largest tag-list word outright - puts tens of
#: thousands of sites here, so the bound is exceeded by orders of magnitude
#: rather than by a margin. Reading it as the observed figure would be a
#: restated count, which CLAUDE.md section 4 forbids.
_COMPATIBLE_REFUSAL_CEILING: Final = 64

#: A FLAT PER-WORD CEILING USED TO STAND HERE AT 16 AND IS DELETED RATHER THAN
#: RETUNED, because no value of it can grade the sentence it was written for.
#: The claim was "one word cannot hide behind the pooled total". To hold, the
#: ceiling must sit BELOW the size-compatible population of the smallest word
#: that reads - otherwise that word can be refused ENTIRELY and stay under it.
#: Measured on this corpus the smallest reading word has 5 such sites while the
#: largest refusal a genuinely native word contributes is 8, so any ceiling
#: above the residue is already above four of the seven reading words. The two
#: constraints are incompatible and a number cannot satisfy both.
#:
#: WHAT REPLACES IT IS RELATIVE, NOT ABSOLUTE. A word is graded against its OWN
#: population - every word that refuses at all must refuse ALL of its
#: size-compatible sites (:func:`test_every_size_compatible_struct_site_yields_a_decoded_interior`
#: asserts that partition), and a word that does so without independent
#: size-excluded evidence lands in :attr:`_StructSweep.unexplained_refusals`,
#: which the ceiling below now grades with NO headroom.

#: How many words may hold a refusal nothing but the reader explains.
#:
#: TIGHTENED FROM TWO TO ONE, AND THE ONE IS THE WHOLE POINT. Every word that
#: reads in this corpus carries ZERO size-excluded sites, so refusing any one of
#: them outright puts it here. At two, exactly one reading word could be lost
#: entirely and stay green - and four of the seven have few enough sites that
#: nothing else would have noticed. At one, with one word already observed
#: unexplained, the bound has no headroom left and the loss of ANY reading word
#: reddens. That the observed figure meets the bound exactly is asserted below
#: rather than left as a coincidence.
_UNEXPLAINED_WORD_CEILING: Final = 1


def test_the_minimal_tag_list_widths_are_earned_not_asserted() -> None:
    """The size criterion's two widths, EARNED against the shipped reader.

    A CRITERION MADE OF ARITHMETIC IS ONLY AS GOOD AS THE ARITHMETIC. These two
    widths decide the population every equality in this module is asserted
    over, so neither is taken on the derivation alone: a tag of exactly the
    minimal width is built and the SHIPPED reader is made to consume it, and one
    byte shorter is made to fail. The terminator width is cross-checked against
    the fixture encoder, which is a second expression of the same grammar.

    NEEDS NO SAVE LIBRARY - it is a claim about the grammar.
    """
    encoded = len(_fstring(objects._PAYLOAD_TERMINATOR))  # noqa: SLF001
    assert encoded == _TERMINATOR_ONLY_BYTES, (
        "the derived terminator width and the fixture encoder disagree, so one of "
        "them is not the grammar the reader implements"
    )

    minimal = struct.pack("<i", 0) * 4 + bytes(_GUID_FLAG_BYTES)
    assert len(minimal) == _MIN_INTERIOR_TAG_BYTES, (
        f"the fixture built {len(minimal)} bytes where the derivation says "
        f"{_MIN_INTERIOR_TAG_BYTES}, so the two do not describe the same tag"
    )
    name = objects._payload_text(minimal, 0, len(minimal))  # noqa: SLF001
    assert name is not None, "the minimal name did not read at all"
    assert name[0] == "", "the minimal name read as something other than the empty text"
    read = objects._read_tag_header(minimal, name[1], len(minimal))  # noqa: SLF001
    assert read is not None, (
        "the SHIPPED reader will not consume a tag of the width this module derives "
        "as minimal, so the derived floor is above the real one and the criterion "
        "excludes sizes that a tag list can in fact take"
    )
    assert read[1] == len(minimal), (
        f"the minimal tag's value begins at {read[1]} rather than at its end, so the "
        "derived width is not the width the reader actually consumes"
    )
    short = minimal[:-1]
    assert objects._read_tag_header(short, name[1], len(short)) is None, (  # noqa: SLF001
        "the shipped reader consumes a tag ONE BYTE SHORTER than the derived minimum, "
        "so the floor is too high and size-excluded sites are being excluded wrongly"
    )


def test_the_admission_gate_itself_is_earned_against_the_shipped_decoder() -> None:
    """THE GATE, NOT ITS INGREDIENTS - the arm that was missing.

    THE TEST ABOVE EARNS TWO WIDTHS AND STOPS SHORT OF WHAT THEY ARE FOR. It
    makes ``objects._read_tag_header`` consume a minimal tag and refuse one byte
    less, which earns the tag width - but the constant those widths add up to,
    and the gate that decides this module's whole population from it, were
    asserted rather than earned. An adversary measured the gap: raising the
    floor from its derived value to twice it reclassified 10506 sites with every
    arm still green, which is a constant no test was holding.

    SO THE GATE IS EARNED AGAINST THE THING THAT ACTUALLY CONSUMES IT. Both of
    its disjuncts are put to ``objects.decode_struct_interior`` - the shipped
    entry point the sweep grades through - at EXACTLY the width each names, and
    the floor is put to it one byte short. A gate that admits a width the
    decoder cannot read, or excludes one it can, fails here rather than silently
    reshaping the population.

    NEEDS NO SAVE LIBRARY - it is a claim about the grammar.
    """
    bare = _fstring(objects._PAYLOAD_TERMINATOR)  # noqa: SLF001
    assert len(bare) == _TERMINATOR_ONLY_BYTES, "the empty-list disjunct is not this width"
    assert _size_admits_a_tag_list(len(bare)), "the gate rejects its own empty-list width"
    empty = objects.decode_struct_interior(bare, _SYNTHETIC_STRUCT_WORD, 0, len(bare))
    assert empty is not None, (
        "the SHIPPED decoder refuses an interior of exactly the empty-list width the "
        "gate admits, so that disjunct lets in a size no tag list can actually take"
    )
    assert len(empty.properties) == 0, (
        "an interior of exactly a bare terminator's width decoded a property, so the "
        "width does not describe the empty tag list the gate says it does"
    )

    minimal = struct.pack("<i", 0) * 4 + bytes(_GUID_FLAG_BYTES) + bare
    assert len(minimal) == _MIN_TAG_LIST_BYTES, (
        f"the fixture built a {len(minimal)}-byte minimal tag list where the gate's "
        f"floor is {_MIN_TAG_LIST_BYTES}, so the two do not describe the same interior"
    )
    assert _size_admits_a_tag_list(len(minimal)), "the gate rejects its own floor"
    at_floor = objects.decode_struct_interior(minimal, _SYNTHETIC_STRUCT_WORD, 0, len(minimal))
    assert at_floor is not None, (
        "the SHIPPED decoder will not read an interior of exactly the gate's floor, so "
        "the floor is ABOVE the real one and every site between the two is being "
        "called native on arithmetic that is wrong"
    )
    trimmed = minimal[:-1]
    assert not _size_admits_a_tag_list(len(trimmed)), (
        "the gate admits one byte BELOW its own floor, so the floor is not what the "
        "gate is computing"
    )
    assert (
        objects.decode_struct_interior(trimmed, _SYNTHETIC_STRUCT_WORD, 0, len(trimmed)) is None
    ), (
        "the shipped decoder reads an interior ONE BYTE SHORTER than the gate's floor, "
        "so the floor is too high and sites a tag list can occupy are being excluded"
    )


def test_the_gates_empty_list_disjunct_is_inert_on_this_corpus_and_says_so() -> None:
    """DEAD CODE THAT ANNOUNCES ITSELF, rather than dead code nobody knows about.

    THE ADVERSARY'S FINDING, KEPT RATHER THAN ARGUED AWAY. No site in this
    corpus declares exactly a bare terminator's width, so the gate's empty-list
    disjunct never fires and deleting it would redden nothing. That is precisely
    the shape this module honourably retracted for the exact-close comparison -
    and the difference the finding named is that the exact-close now ASSERTS its
    own inertness and this did not.

    IT IS NOT DELETED, AND THE REASON IS THE TEST ABOVE. The disjunct is earned:
    the shipped decoder really does read an interior of exactly that width, so
    the arithmetic is right about the grammar even though this corpus carries no
    instance. Deleting a correct disjunct because today's saves do not exercise
    it would make the gate wrong the day one does, and nothing would say so.

    A RED HERE IS GOOD NEWS. It means the corpus has begun to carry an empty
    struct interior, the disjunct has started doing work, and the sentence above
    calling it inert is stale.
    """
    sweep = _sweep_or_skip()

    assert sweep.bare_terminator_sites == 0, (
        f"{sweep.bare_terminator_sites} of {sweep.sites_seen} struct sites now declare "
        "exactly a bare terminator's width. The gate's empty-list disjunct is no "
        "longer inert, so this record is stale - and every arm that treats the floor "
        "as the only live half of the gate should be re-read before it is trusted"
    )


def test_no_struct_site_leaves_the_population_between_the_walk_and_the_decoder() -> None:
    """THE SITES THE READER NEVER REACHED, GRADED - the surviving refutation.

    WHAT WAS WRONG AFTER THE LAST REPAIR. The criterion below became arithmetic
    - a site is graded when its declared size could hold a tag list, decided
    without calling the decoder - but the POPULATION that criterion ranged over
    was still whatever three readers upstream happened to hand it. Each sat
    behind a bare ``continue``. A defect in any one of them DELETED sites from
    the denominator instead of landing them in the residue, so the grade
    improved as the reader got worse.

    MEASURED, NOT ARGUED. A guard inside
    ``objects._container_element_words``, fenced to fire only on a real body,
    removed 22897 of 45208 sites; the size-compatible refusal count FELL from 12
    to 7 - the grade IMPROVED for the loss - and every arm this module then
    carried stayed green at exit 0. The refutation that found this reports the
    complementary half, which is not re-measured here: the identical loss placed
    inside the DECODER reddens two arms, and that asymmetry between an upstream
    reader and the decoder is the whole finding.

    WHAT MAKES IT FAIL NOW. ``sites_seen`` is incremented the instant the walk
    reports a struct-typed tag and BEFORE any of those readers is called, so it
    is a denominator none of them can move. Every refusal past that point is
    counted by name. The conservation line is an identity by construction and is
    asserted anyway, because it is what says the counters below partition the
    population rather than sampling it - and the three that follow are the ones
    that can actually fail.
    """
    sweep = _sweep_or_skip()

    assert sweep.sites_seen > 0, (
        "the walk reported no struct-typed tag anywhere in this library, so every "
        "equality in this module ranges over an empty population and would hold "
        "against any decoder at all"
    )

    folded = sum(sweep.tags.values())
    accounted = folded + sweep.name_unread + sweep.word_unread
    assert accounted == sweep.sites_seen, (
        f"{sweep.sites_seen} struct sites were seen and {accounted} accounted for. The "
        "counters below do not partition the population, so a site can still go "
        "missing between them and this module cannot see it happen"
    )

    assert sweep.name_unread == 0, (
        f"{sweep.name_unread} of {sweep.sites_seen} struct sites have a tag NAME that "
        "will not re-read at the offset the walk reports the tag starting at. The walk "
        "and this module therefore disagree about where a tag begins, and every site "
        "past the first disagreement is being read at a guessed offset"
    )

    assert sweep.word_unread == 0, (
        f"{sweep.word_unread} of {sweep.sites_seen} struct sites carry a tag extra that "
        "will not read, so their struct word is unreachable and the decoder is never "
        "asked about them. THIS IS THE ARM THE REFUTATION ASKED FOR: the site stays in "
        "the denominator and the refusal is reported here, instead of the site "
        "disappearing and the remaining population grading better for its absence"
    )

    assert sweep.wordless_compatible == 0, (
        f"{sweep.wordless_compatible} sites whose declared size COULD hold a tag list "
        "were lost before the decoder saw them. Their size says they are exactly the "
        "population this item is graded over, so losing them upstream removes the only "
        "sites capable of failing the equality below"
    )


def test_the_sweep_reaches_every_struct_site_the_shipped_reader_counts() -> None:
    """A DENOMINATOR FROM A LOOP THIS MODULE DID NOT WRITE.

    THE ARM ABOVE CANNOT SEE A WHOLE RECORD VANISH. Its denominator comes from
    the walk, so a defect that makes the walk refuse a record takes the sites
    and the count of them away together and the equality still holds. This is
    the second denominator, and it comes from ``objects._walk_payload`` through
    ``read_properties`` - a different entry point, a different loop, and a
    counter incremented before the struct word is read there too.

    IT IS NOT TWO AGENTS AGREEING. CLAUDE.md section 5 rules agreement no
    evidence when both sides derive from one belief, and the point here is the
    opposite: these two totals are produced by loops that share their PRIMITIVES
    but not their control flow, so a defect in either loop separates them. What
    it does NOT catch is a defect in a primitive both call - that limit is real
    and is recorded here rather than in a comment nobody reads.

    THE SECOND ASSERTION IS THE DECODED SIDE, and it is deliberately not folded
    into the first. A reader failure moves the two denominators apart; a decoder
    failure moves the two numerators apart; reporting them as one number would
    lose which of those happened.
    """
    sweep = _sweep_or_skip()

    assert sweep.shipped_tags > 0, (
        "the shipped reader counts no struct tag in this whole library, so this "
        "cross-check has no population and grades nothing"
    )
    assert sweep.sites_seen == sweep.shipped_tags, (
        f"this module reached {sweep.sites_seen} struct sites where the SHIPPED reader "
        f"counts {sweep.shipped_tags} over the same records. One of the two walks is "
        "losing tags, and because the sweep's own arms are computed over its walk, the "
        "loss would otherwise show up as a smaller population rather than as a failure"
    )

    decoded = sum(sweep.decoded.values())
    assert decoded == sweep.shipped_interiors, (
        f"this module decoded {decoded} interiors where the shipped reader decoded "
        f"{sweep.shipped_interiors} from the same tags. The two disagree about what "
        "reads, which is a real disagreement between two readings rather than a "
        "population effect - the denominators above already agreed"
    )


def test_a_record_leaves_the_population_only_with_its_whole_version_pair() -> None:
    """RECORDS THE SWEEP NEVER OPENED, COUNTED IN BYTES AND GRADED.

    THIS CORPUS DOES CARRY RECORDS THE PAYLOAD WALK REFUSES and refusing them is
    correct - ``objects.read_properties`` flags them rather than parsing them,
    because their save version pair's payload grammar is unmeasured. So the
    honest claim is not that no record is lost. It is that loss has a SHAPE no
    defective reader can imitate.

    THE SHAPE, MEASURED. Refusal is all-or-nothing per save: not one save in
    this library has some records walk and others refuse. And it is
    all-or-nothing per version pair: no pair holds both a save walked entirely
    and a save walked not at all. A defect that drops a fraction of records
    makes a save partial. A defect that drops one save whole makes its pair
    contested. Both are equalities against zero, and neither can be satisfied by
    a reader that has merely got worse.

    THE BYTES ARE WHAT MAKE THE UNREACHED RECORDS COUNTABLE. ``census_body``
    counts struct type words by literal byte match - no walk, no tag reader, no
    decoder - so a record the sweep never opened still contributes a number. The
    final equality says every one of those occurrences lies inside some record's
    declared extent, which is what rules out a struct site that no walk could
    ever have reached because no record claims the bytes it sits in.
    """
    sweep = _sweep_or_skip()

    assert sweep.head_unread == 0, (
        f"{sweep.head_unread} actor records will not step past their own head, so "
        "their tags are never enumerated at all. Unlike the payload walk this has no "
        "measured version-pair explanation in this corpus - every actor head reads"
    )

    assert sweep.partial_saves == 0, (
        f"{sweep.partial_saves} saves had SOME records walked and others refused. "
        "Refusal is a property of the save's version pair in this corpus, so a save "
        "split down the middle is a reader failing on individual records - which is "
        "exactly the loss that used to leave no trace but a smaller population"
    )

    assert sweep.contested_pairs == 0, (
        f"{sweep.contested_pairs} save version pairs hold both a save walked entirely "
        "and a save walked not at all. The pair's payload grammar cannot be both read "
        "and unread, so one of those saves is being refused for a reason that is not "
        "its format"
    )

    assert sweep.census_body == sweep.census_records, (
        f"the bytes carry {sweep.census_body} struct type words but only "
        f"{sweep.census_records} of them lie inside a record's declared extent. The "
        "difference is struct content no record claims, which no walk could reach "
        "however good it got, and which would sit outside every population here"
    )


def test_every_size_compatible_struct_site_yields_a_decoded_interior() -> None:
    """CS-829's acceptance, over a population the DECODER DID NOT CHOOSE.

    THE FIRST VERSION OF THIS TEST WAS AN IDENTITY AND TWO ADVERSARIES PROVED
    IT MECHANICALLY. It defined the population as the words the decoder
    succeeded on, then asserted that the decoder succeeds on them. Fed two
    hundred thousand arbitrary wrong decoders, it failed zero times. The
    counter-example that made it concrete refuses the single largest tag-list
    word outright - a majority of the whole struct population - and the entire
    save suite stayed green, because the word simply left the class and was
    relabelled native. That is CS-830's disease exactly one layer up.

    THE POPULATION HERE IS ARITHMETIC. A site is in it when its DECLARED SIZE
    could hold a tag list at all - see :func:`_size_admits_a_tag_list`, which
    never calls the decoder. A word refused outright now KEEPS its sites in the
    population and its refusals land in the residue, so the counter-example
    above turns this red by orders of magnitude.

    WHAT IS STILL NOT PROVEN, and it is the narrowing:
    :func:`test_the_size_compatible_refusals_rest_on_the_reader_alone` records
    the sites this equality has to except.
    """
    sweep = _sweep_or_skip()

    compatible = sum(sweep.size_compatible.values())
    excluded = sum(sweep.size_excluded.values())
    decoded = sum(sweep.compatible_decoded.values())
    refused = sum(sweep.compatible_refused.values())

    assert compatible > 0, (
        "no site in this corpus has a size a tag list could take, so this equality "
        "ranges over an empty population and would pass on any decoder at all"
    )
    assert excluded > 0, (
        "no site is size-excluded, so nothing here is classified native on arithmetic "
        "and the whole population rests on the reader - which is the shape this test "
        "exists to avoid"
    )
    assert decoded > 0, "not one size-compatible site decoded, so the reading is absent"

    assert refused <= _COMPATIBLE_REFUSAL_CEILING, (
        f"{refused} of {compatible} size-compatible sites did NOT yield an interior. "
        "These sites can hold a tag list on arithmetic, so a refusal is either a "
        "reading that has failed or a native struct whose width happens to be "
        "admissible - and at this scale it is the former. THE POPULATION IS NOT THE "
        "DECODER'S SUCCESS SET, which is why this can fail at all"
    )

    wordless = sweep.wordless_compatible
    assert wordless == 0, (
        f"{wordless} sites with a size a tag list could take never reached the decoder "
        "at all, because a reader between the walk and the decode refused first. They "
        "belong in the population this equality ranges over, so their absence would "
        "make the numbers above describe a smaller and easier corpus"
    )

    # A COUNT, NEVER THE WORDS. pytest renders the asserted expression, so a
    # collection of struct words bound here would be printed by the runner on
    # failure - which is the one path this module's counts-only rule cannot
    # control from a message string. Measured: an earlier draft of the residue
    # assertion below did exactly that under a planted mutant.
    split = sum(
        1
        for word, seen in sweep.size_compatible.items()
        if 0 < sweep.compatible_decoded.get(word, 0) < seen
    )
    assert split == 0, (
        f"{split} struct words decode SOME of their size-compatible sites and "
        "refuse others. The serialization form is then not a property of the struct "
        "type, and this suite's per-word reasoning does not describe the format. The "
        "words are deliberately not rendered - they are read out of the save"
    )


def test_the_size_compatible_refusals_rest_on_the_reader_alone() -> None:
    """THE NARROWING, RECORDED AS THE ADVERSARY MEASURED IT.

    Nearly every native site in this corpus is native on ARITHMETIC: its
    declared width is one no tag list can take, so no reader's opinion is
    involved. A small residue is not. Those sites have a width a tag list could
    have taken, and the only thing saying they are not one is this module's own
    reader refusing them.

    THAT IS THE HONEST LIMIT OF THIS SLICE, and it is far narrower than the
    limit first shipped - which was the whole native class. It is asserted so it
    has a failure direction: the day the residue empties, this record is stale.

    NO FIGURE IS WRITTEN HERE. The operator plays this game and the corpus moves
    on the next autosave; the counts are derived on every run.
    """
    sweep = _sweep_or_skip()

    refused = sum(sweep.compatible_refused.values())
    assert refused > 0, (
        "every size-compatible site now decodes. THIS RECORD IS STALE: nothing in the "
        "native class rests on the reader's refusal any more, so the residue this "
        "test exists to record is gone and the narrowing it states should go with it"
    )

    unexplained = sweep.unexplained_refusals
    unexplained_words = len(unexplained)
    unexplained_sites = sum(unexplained.values())
    assert unexplained_words <= _UNEXPLAINED_WORD_CEILING, (
        f"{unexplained_words} struct words hold a size-compatible refusal AND carry no "
        "size-excluded site at all, so nothing but this module's reader says they are "
        "native. A word refused entirely by a broken decoder lands here, which is what "
        "makes this bound worth having rather than a formality"
    )
    # THE BOUND IS ASSERTED TO BE TIGHT, not merely satisfied. A ceiling with
    # headroom is a ceiling that admits exactly as much silent failure as its
    # slack, and the previous value had room for a whole struct word - measured,
    # four of the seven that read are small enough that nothing else would have
    # noticed. With the observed figure sitting ON the bound, the loss of any
    # reading word raises it past and reddens. This line is what stops the slack
    # creeping back in unremarked: if the residue ever empties, the ceiling has
    # become slack again and must come down with it.
    assert unexplained_words == _UNEXPLAINED_WORD_CEILING, (
        f"{unexplained_words} words hold a refusal nothing but the reader explains, "
        f"where the bound above allows {_UNEXPLAINED_WORD_CEILING}. Below the bound "
        "there is headroom, and headroom here is exactly the room for one struct word "
        "to be refused outright with every other arm still green. Bring the bound down "
        "to what the corpus now shows - a red here is the residue narrowing, which is "
        "this item progressing"
    )
    assert unexplained_sites <= _COMPATIBLE_REFUSAL_CEILING, (
        f"{unexplained_sites} sites are called native on the reader's word "
        "alone. At this scale that is a reading that has stopped working rather than a "
        "residue"
    )

    explained = refused - unexplained_sites
    assert explained >= 0, "the residue partition does not add up, so one arm is wrong"


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
    # BOUND TO A SCALAR BEFORE THE COMPARISON, AND THIS IS A PRIVACY FIX RATHER
    # THAN A STYLE ONE. pytest rewrites an assertion into a rendering of its
    # SUBEXPRESSIONS, independently of the message the author wrote: with
    # ``len(sweep.miss_words)`` in the compared expression, a failure prints the
    # frozenset's own repr - struct words read out of the operator's save -
    # straight past the counts-only ``__repr__`` this sweep carries precisely to
    # stop that (non-negotiables 11 and 12). A plain name renders as the integer
    # it holds. Every assertion in this module compares scalars for that reason.
    miss_words = len(sweep.miss_words)
    assert miss_words <= _MISS_WORD_CEILING, (
        f"{miss_words} struct words carry an interior name the usmap does"
        "not declare. CONFINEMENT IS THE CLAIM: a residue in one or two words is a "
        "mapping that trails the build, where a residue spread across the words is a "
        "reading that is wrong everywhere. THE OLD FORM OF THIS ASSERTION WAS NEARLY "
        "VACUOUS - it compared the miss-word count against the count of words read, "
        "and an adversary measured it passing with EVERY name missing, because six is "
        "less than seven. An absolute ceiling grades what the sentence claims"
    )


#: How much of the cross-check may miss before the residue stops being one.
#: A BOUND, not a measurement, so the assertion has a direction.
#:
#: TIGHTENED BY FIFTY TIMES AFTER AN ADVERSARY MEASURED THE OLD ONE. At the
#: previous value the arm permitted a degradation of several HUNDRED times what
#: this corpus shows while its own docstring called the residue small and
#: bounded - a bound that does not grade what its sentence claims. At this value
#: the headroom is around one order of magnitude, and a reading that had stopped
#: agreeing with the shipped asset fails it by three.
_MISS_RESIDUE_FACTOR: Final = 1000

#: How many struct words may carry an unresolved interior name at all.
_MISS_WORD_CEILING: Final = 2


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

    read = sweep.words_decoded_throughout
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
    read_words = sweep.words_decoded_throughout

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


#: How many struct sites the end-freedom sample examines, and how wide a site it
#: will take. BOUNDS ON THE WORK, not on the finding: every candidate end inside
#: a site is tried, so the cost is quadratic in the site width and a census would
#: run the length of the corpus. A SAMPLE IS STATED AS A SAMPLE - this arm does
#: not claim the property holds at every site, only that it holds wherever it
#: looked, and it looks somewhere different the moment the corpus changes.
_END_SAMPLE_SITES: Final = 150
_END_SAMPLE_MAX_SIZE: Final = 256
_END_SAMPLE_STRIDE: Final = 37

#: How far PAST the declared end a candidate is still tried. The old sampler
#: looked only inside the tag's own extent, which made "no early close" and "no
#: alternative end" the same set by construction - see :class:`_EndSample`.
_END_SAMPLE_OVERRUN: Final = 256


@dataclass
class _EndSample:
    """The end-freedom sampler's running state. COUNTS ONLY.

    IT USED TO REPORT ONE INTEGER AS TWO MEASUREMENTS. The sampler carried a
    single ``early`` counter and its return handed the same value back in two
    positions, which the test unpacked as separate quantities and asserted with
    two contradictory messages. They could not disagree: every candidate came
    from ``range(at, true_end)``, so every alternative end was necessarily an
    early one. The overrun below is what makes the second measurement a second
    measurement - a candidate PAST the declared end is a different question, and
    on this corpus it has a different and independently checkable answer.

    Attributes:
        sites: Struct sites actually examined.
        declared: Sampled sites whose DECLARED end closes. Reported rather than
            required, because the sample is drawn by arithmetic now and a
            native struct that happens to sit in it should not be excluded for
            failing to decode - excluding it is the circularity this fixes.
        early: Candidate ends BEFORE the declared one that also closed.
        late: Candidate ends AFTER the declared one that also closed, within
            the stated overrun.
        seen: Sampling-eligible sites passed over, which drives the stride.
    """

    sites: int = 0
    declared: int = 0
    early: int = 0
    late: int = 0
    seen: int = 0


def _sample_one_record(body: bytes, record: objects.ObjectRecord, state: _EndSample) -> None:
    """Sample the struct sites in one record, folding into the running state.

    Args:
        body: The decompressed body.
        record: The record to walk.
        state: The sampler state, mutated in place.
    """
    payload_end = record.body_offset + record.body_length
    start: int | None = record.body_offset
    if record.kind == objects.KIND_ACTOR:
        start = objects._skip_actor_head(body, record.body_offset, payload_end)  # noqa: SLF001
    if start is None:
        return
    walked = test_decode_oracles._walk_with_the_shipped_reader(body, start, payload_end)  # noqa: SLF001
    if walked is None:
        return
    at = start
    for _name, word, value_at, size in walked:
        head = at
        at = value_at + size
        if word != objects.STRUCT_TYPE_WORD or size > _END_SAMPLE_MAX_SIZE:
            continue
        # THE SAMPLE IS DRAWN BY ARITHMETIC, NOT BY THE DECODER. It used to skip
        # every site the decoder refused, which made the population the
        # decoder's own success set - the exact circularity the rest of this
        # module is built to avoid, left standing in the one arm that measures
        # how strongly the grammar pins an offset. Eligibility is now the same
        # size test the acceptance uses, and whether the declared end closes is
        # COUNTED rather than used as a filter.
        if not _size_admits_a_tag_list(size):
            continue
        state.seen += 1
        if state.seen % _END_SAMPLE_STRIDE or state.sites >= _END_SAMPLE_SITES:
            continue
        name_read = objects._payload_text(body, head, payload_end)  # noqa: SLF001
        if name_read is None:
            continue
        struct_word = objects._struct_word_of_tag(body, name_read[1], payload_end)  # noqa: SLF001
        if struct_word is None:
            continue
        true_end = value_at + size
        state.sites += 1
        if objects.decode_struct_interior(body, struct_word, value_at, true_end) is not None:
            state.declared += 1
        state.early += _ends_that_close(body, struct_word, value_at, value_at, true_end)
        state.late += _ends_that_close(
            body,
            struct_word,
            value_at,
            true_end + 1,
            min(payload_end, true_end + _END_SAMPLE_OVERRUN) + 1,
        )


def _ends_that_close(body: bytes, struct_word: str, at: int, first: int, stop: int) -> int:
    """How many candidate ends in a half-open range close at this site.

    EVERY CANDIDATE IN THE RANGE IS TRIED, not a sampled few: the question is
    whether the tag-grammar chain pins the end, and a partial scan could miss
    the one alternative that answers it.

    IT TAKES THE RANGE RATHER THAN DERIVING IT, which is what lets the caller
    ask two genuinely different questions with one implementation - the ends
    before the declared one and the ends after it. The previous shape hard-coded
    the before-range and the caller then reported its single answer twice.

    Args:
        body: The decompressed body.
        struct_word: The struct type word the tag carried.
        at: The interior's first byte.
        first: The first candidate end to try.
        stop: One past the last candidate end to try.

    Returns:
        How many of those candidate ends close.
    """
    return sum(
        1
        for candidate in range(first, stop)
        if objects.decode_struct_interior(body, struct_word, at, candidate) is not None
    )


@lru_cache(maxsize=1)
def _end_freedom_sample() -> tuple[int, int, int, int] | None:
    """How many ends close at a sampled struct site, besides the declared one.

    Returns:
        Sites sampled, how many of them close at their DECLARED end, ends that
        closed BEFORE it and ends that closed AFTER it. None when no library is
        reachable.
    """
    saves = test_properties._library_save_paths()  # noqa: SLF001
    if not saves:
        return None
    state = _EndSample()
    for path in saves:
        if state.sites >= _END_SAMPLE_SITES:
            break
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
            continue
        for record in table.records:
            if state.sites >= _END_SAMPLE_SITES:
                break
            _sample_one_record(body, record, state)
    return (state.sites, state.declared, state.early, state.late)


def test_the_tag_grammar_pins_the_end_and_the_equality_is_not_what_discriminates() -> None:
    """WHAT ACTUALLY MAKES THIS READING FALSIFIABLE - corrected after refutation.

    THE FIRST VERSION OF THIS SLICE CLAIMED THE EXACT CLOSE WAS THE
    DISCRIMINATOR, and an adversary measured the claim false. Loosening the
    reader's ``terminator lands exactly at end`` to ``at or before end`` leaves
    this corpus BIT-IDENTICAL - every count, every classification, every
    cross-check. The comparison never fires, because the walk stops at the first
    terminator and on this corpus the first terminator is always the last byte.
    The only thing that reddened under the loosening was a synthetic fixture
    authored beside the implementation, which is the circularity that got CS-830
    refuted and is not evidence about the format.

    WHAT DOES DISCRIMINATE IS THE TAG-GRAMMAR CHAIN. Each interior tag's name,
    type word, declared size and guid flag must read, and the cursor each one
    computes must land on a tag that also reads, over and over, until a
    terminator. That chain is what refuses a wrong offset, and this measures its
    strength directly: at a sampled site, of every end the declared size admits,
    how many close? The answer measured here is exactly one - the true one.

    A RED IS INFORMATIVE IN BOTH DIRECTIONS. Alternative ends appearing means
    the grammar has slack this module has been treating as certainty. The early
    count rising above zero means the corpus has begun to discriminate the exact
    close, and the sentence above about it being inert is stale.

    WHAT THIS DOES NOT SAY. It is a SAMPLE, not a census, and it says nothing
    about WIDTHS - ``tests/save/test_properties.py`` owns that census, and it
    measures real freedom there: a large majority of payload terminators still
    land exactly under a mis-stated tag width. Offsets inside an interior are
    pinned; the grammar's constants are not equally so.
    """
    sample = _end_freedom_sample()
    if sample is None:
        pytest.skip("no save library on this machine - end freedom is not gradeable here")
    sites, declared, early, late = sample

    assert sites > 0, (
        "the sample examined no struct site at all, so it grades nothing. Either the "
        "corpus carries none narrow enough to sample or the stride skipped every one"
    )
    assert declared > 0, (
        f"not one of {sites} sampled sites closes at its DECLARED end. The sample is "
        "drawn by size arithmetic rather than by the decoder, so a run of native "
        "structs could land here legitimately - but none of them closing means the two "
        "counts below are measuring the absence of a reading rather than its strength"
    )
    assert early == 0, (
        f"{early} candidate ends BEFORE the declared one close across {sites} sampled "
        "sites. The reader's exact-close comparison is therefore no longer inert, and "
        "the docstring above saying it never fires is stale - which is good news, "
        "because it means the corpus has started to discriminate something it could not"
    )
    assert late == 0, (
        f"{late} candidate ends AFTER the declared one close across {sites} sampled "
        "sites, so the tag-grammar chain does not pin the end from above and the "
        "declared size is doing work the grammar cannot check. THIS IS A SECOND "
        "MEASUREMENT, not a restatement of the one before it: the previous version of "
        "this arm handed the same integer back twice and asserted it under two "
        "contradictory messages, because every candidate it tried was an early one"
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

    # SCALARS, FOR THE REASON GIVEN AT THE MISS-WORD ASSERTION ABOVE. These two
    # are safe TODAY only by accident: each fails exactly when its set is empty,
    # so the repr pytest renders happens to be an empty frozenset. Reverse
    # either comparison and it prints struct words read out of a save. Binding
    # the count first removes the accident.
    unread = len(sweep.words_never_decoded)
    read = len(sweep.words_decoded_throughout)
    assert unread > 0, (
        "every struct word the corpus carries now yields a decoded interior on every "
        "instance. THIS TEST IS THE RECORD OF A NARROWING AND IT IS NOW STALE: the "
        "population CS-829's acceptance names is covered, so the item's equality can "
        "be asserted over the whole derived vocabulary and this test deleted with it. "
        "Check that the native form is READ rather than merely absent from this "
        "corpus before closing on it"
    )
    assert read > 0, (
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
        _end_freedom_sample.__name__: reach_guard.REACH_READS_THE_LIBRARY,
    }
)

#: Touches a primitive WITHOUT consuming a real save path, name to why. Empty:
#: every synthetic case in this module builds its bytes in the process and no
#: path-holding read is stubbed anywhere here.
_EXEMPT_LIBRARY_REACH: Final[Mapping[str, str]] = MappingProxyType({})
