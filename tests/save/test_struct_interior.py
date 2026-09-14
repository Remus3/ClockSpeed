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

NO EVIDENCE IS A SKIP, NOT A RED, AND THAT IS ENFORCED HERE RATHER THAN MEANT.
An arm that asserts a count is NON-ZERO is asserting that the operator's library
is LARGE ENOUGH, which is a proof fitted to one machine at one instant on the
same terms as a bound fitted to it. The operator plays this game while a session
runs; autosave rotation alone changes which saves are present. So every arm
below whose population can legitimately be empty SKIPS with a reason naming the
missing ingredient, and the ingredient is derived from what the arm NEEDS rather
than from which corpora were observed failing - a skip condition fitted to the
failing subsets is the same defect one level up.

WHAT SEPARATES A SKIP FROM A RED IS WHETHER THE BYTES SAY ANYTHING. A zero that
the byte census contradicts - struct type words sitting inside records the walk
opened while the walk reports no site - is EVIDENCE DESTROYED and stays an
assertion; :func:`_sweep_or_skip` draws that line and every library arm here
opens with it, including the three that measure their own population and used to
reach the library past it.

MEASURED, AND THE MEASUREMENT IS THE REASON THIS SHAPE IS ENFORCED. Run against
each save of this machine's library alone, against each version pair alone, and
against the library minus its newest save, the arms that bypassed the shared
guard went RED on the saves of one whole version pair while seventeen arms that
used it SKIPPED on the identical corpus for the identical reason.

ONE ARM IS EXEMPT AND THE EXEMPTION IS MEASURED RATHER THAN ASSUMED.
``_UNEXPLAINED_WORD_CEILING`` is a FITTED bound and it does redden on some
legitimate subsets of this library. Skipping its excess was built and REFUTED:
the corpus one version pair presents is structurally identical to a corpus where
a reading word was refused entirely, so the skip that spares the subset also
spares the defect - measured, at zero failures for the whole module under an
in-process mutant. It keeps its red, and the note on the constant says why.

NEEDS NO GAME FOR MOST OF WHAT IS HERE. Every synthetic case runs on a machine
with no install and no save library. The library cases skip there.
"""

from __future__ import annotations

import ast
import struct
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from types import MappingProxyType
from typing import Final, Protocol

import pytest

from clockspeed.save import chunks, header, objects, usmap
from tests.save import independent_table, reach_guard, test_decode_oracles, test_properties

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


# ---------------------------------------------------------------------------
# A SECOND EXPRESSION OF THE TAG-LIST GRAMMAR - CS-829's shaped-loss arm
#
# WHY A SECOND ONE EXISTS AT ALL. Every guard this module had over a refused
# record graded the SHAPE of the loss - is it whole-save, is it whole-pair - and
# an adversary measured that shape guards do nothing against SHAPED loss.
# Patching ``objects._payload_text`` to refuse for one version pair, filtered to
# the payload walk so the actor-head step still reads, deleted 8362 sites and
# 23046 further records with ``head_unread``, ``partial_saves`` and
# ``contested_pairs`` all zero and every arm green. Shaped loss is also the loss
# this corpus actually exhibits, so the guards were tuned against the one case
# they cannot see.
#
# The functions below read the same grammar and SHARE NO FUNCTION WITH IT. They
# call ``struct.unpack_from`` and slice bytes; the only things they take from
# the shipped module are CONSTANTS - widths, a terminator name and a tag-extra
# table - which are data rather than readers. A defect planted in any shipped
# reader therefore separates the two, which is precisely what no arm could do
# before.
#
# A CONSTANT IS NOT AUTOMATICALLY SAFE TO SHARE, WHICH COST THIS MODULE ITS
# GRADE ONCE - CS-863. A shared CEILING is a shared decision about which records
# leave the population, so making it stricter deleted the same records from both
# readings and every equality here stayed green while the denominator shrank.
# The tag ceiling is therefore no longer read here at all. The constants that
# remain are WIDTHS and NAMES, which a second reading of the same format cannot
# disagree with and still be reading that format; they are enumerated in
# :data:`TAG_READING_SHARED_SYMBOLS` and held to the source by a test, and a
# plant on each has been measured rather than assumed.
#
# THEY ARE DELIBERATELY CONSERVATIVE AND THE ASSERTION IS ONE-SIDED. Measured,
# they accept 87302 of 148668 records where the shipped walk accepts 129775, and
# they accept NOTHING the shipped walk refuses. So the claim graded is "no
# record this module can read for itself is refused by the shipped walk", never
# the converse - the records only the shipped walk accepts are outside this
# arm's reach, and a loss confined entirely to them would still escape it.
# ---------------------------------------------------------------------------


def _independent_string(body: bytes, at: int, end: int) -> tuple[str, int] | None:
    """One length-prefixed string, read without calling the shipped reader.

    Args:
        body: The decompressed body.
        at: Where the length prefix starts.
        end: The first byte past this payload.

    Returns:
        The text and the offset after it, or None when it does not read.
    """
    if at < 0 or at + objects.INT32_SIZE > end:
        return None
    (count,) = struct.unpack_from("<i", body, at)
    if count == 0:
        return ("", at + objects.INT32_SIZE)
    if count > 0:
        width, terminator, encoding = count, 1, "utf-8"
    else:
        width, terminator, encoding = -count * objects.UTF16_CHAR_SIZE, 2, "utf-16-le"
    if width > objects.MAX_STRING_BYTES or at + objects.INT32_SIZE + width > end:
        return None
    start = at + objects.INT32_SIZE
    try:
        text = body[start : start + width - terminator].decode(encoding)
    except UnicodeDecodeError:
        # Returned, never raised - a UnicodeDecodeError QUOTES the offending
        # bytes and exception context is an echo path (non-negotiable 12).
        return None
    return (text, start + width)


def _independent_actor_head(body: bytes, at: int, end: int) -> int | None:
    """Step an actor payload's head without calling the shipped reader.

    Args:
        body: The decompressed body.
        at: The payload's first byte.
        end: The first byte past the payload.

    Returns:
        Where the property tags begin, or None when the head does not read.
    """
    for _ in range(2):
        step = _independent_string(body, at, end)
        if step is None:
            return None
        at = step[1]
    if at + objects.INT32_SIZE > end:
        return None
    (count,) = struct.unpack_from("<i", body, at)
    at += objects.INT32_SIZE
    if count < 0 or count > objects.MAX_OBJECTS:
        return None
    for _ in range(2 * count):
        step = _independent_string(body, at, end)
        if step is None:
            return None
        at = step[1]
    return at


def _independent_tag_list(body: bytes, at: int, end: int) -> bool:
    """Whether a property tag list starts here and closes at its terminator.

    Args:
        body: The decompressed body.
        at: Where the first tag begins.
        end: The first byte past the payload.

    Returns:
        Whether this module's own reading of the grammar closes.
    """
    return _independent_tag_walk(body, at, end) is not None


def _independent_tag_walk(
    body: bytes, at: int, end: int
) -> tuple[tuple[int, int, str, int, int], ...] | None:
    """EVERY TAG IN ONE LIST, read without calling any shipped reader.

    THE BOOLEAN ABOVE COULD ONLY EVER GRADE A REFUSAL, AND THAT IS THE HOLE
    THIS FUNCTION CLOSES. ``_independent_tag_list`` is consulted only where the
    shipped walk returned None, so a record the shipped walk ACCEPTS while
    yielding fewer tags than it holds was outside every arm in this module. That
    is the loss class the third refutation of CS-829 measured: an early
    terminator verdict inside ``objects._payload_text`` leaves a record accepted,
    deletes struct sites from BOTH the sweep's own walk and
    ``read_properties``'s, and every count derived from either moves down
    together while the residue gets smaller.

    Returning the TAGS rather than a verdict is what lets the site total be
    taken from this reading instead, so the population stops being something a
    shipped reader can shorten.

    Args:
        body: The decompressed body.
        at: Where the first tag begins.
        end: The first byte past the payload.

    Returns:
        Each tag as its name offset, its type-word offset, its type word, its
        value's first byte and its value's declared extent - or None when this
        module's own reading of the grammar does not close.
    """
    tags: list[tuple[int, int, str, int, int]] = []
    cursor = at
    # THE LOOP BOUND COMES FROM THE EXTENT, NEVER FROM THE SHIPPED CEILING -
    # CS-863, and it is the whole of that item's repair. This loop used to run
    # `range(objects._MAX_TAGS_PER_PAYLOAD)`, which the SHIPPED walk also runs,
    # so a stricter ceiling deleted the same records from both readings and
    # every equality in this module stayed green while the population shrank.
    # Measured on this tree: at a pair-shaped ceiling of 12 the module showed
    # ONE failing arm and at 0 - strictly worse - it showed NONE and exited 0.
    #
    # THE BOUND IS ARITHMETIC OVER THE WINDOW AND IT CANNOT LOSE A REAL TAG. A
    # tag occupies at least `_MIN_INTERIOR_TAG_BYTES` before its value begins
    # and its value's declared extent is never negative, so the cursor advances
    # by at least that much every iteration and no more than this many tags can
    # fit between `at` and `end`. The one extra iteration is the terminator
    # read, which consumes no tag. Measured against the old bound across this
    # machine's library: 129775 records walked, ZERO disagreements, an observed
    # maximum of 31 tags in any one payload against a shipped ceiling of 16384.
    for _ in range(max(end - at, 0) // _MIN_INTERIOR_TAG_BYTES + 1):
        name = _independent_string(body, cursor, end)
        if name is None:
            return None
        if name[0] == objects._PAYLOAD_TERMINATOR:  # noqa: SLF001
            return tuple(tags)
        step = _independent_tag_header(body, name[1], end)
        if step is None:
            return None
        word, value_at, size = step
        tags.append((cursor, name[1], word, value_at, size))
        cursor = value_at + size
    return None


def _independent_tag_header(body: bytes, at: int, end: int) -> tuple[str, int, int] | None:
    """One tag's header, read without calling the shipped reader.

    Args:
        body: The decompressed body.
        at: Where the tag's type word begins.
        end: The first byte past the payload.

    Returns:
        The type word, the value's first byte and its declared extent, or None
        when the header does not read.
    """
    word = _independent_string(body, at, end)
    if word is None:
        return None
    cursor = word[1]
    if cursor + objects.INT32_SIZE + objects._TAG_INDEX_FIELD_BYTES > end:  # noqa: SLF001
        return None
    size = int(struct.unpack_from("<i", body, cursor)[0])
    cursor += objects.INT32_SIZE + objects._TAG_INDEX_FIELD_BYTES  # noqa: SLF001
    if word[0] == _BOOL_TYPE_WORD:
        cursor += 1
    else:
        for _extra in range(objects._TAG_EXTRA_STRINGS.get(word[0], 0)):  # noqa: SLF001
            extra = _independent_string(body, cursor, end)
            if extra is None:
                return None
            cursor = extra[1]
        # THE STRUCT GUID, AND ITS ABSENCE HERE IS WHY THIS READING GRADED
        # NOTHING. A struct tag carries a sixteen-byte guid after its struct
        # name, which ``objects._skip_tag_extra`` steps and this function did
        # not - so the reading desynchronised by exactly sixteen bytes at the
        # FIRST struct tag in a record and refused everything after it.
        # Measured on this corpus: it accepted 87302 of 148668 records and
        # found ZERO struct sites in any of them, while the shipped walk
        # accepted 129775 carrying 45208. The arm sold as the independent
        # corroboration of a refusal therefore covered zero per cent of the
        # population this item is about. With the step it accepts exactly the
        # 129775 the shipped walk does and finds exactly the same 45208.
        if word[0] == objects.STRUCT_TYPE_WORD:
            cursor += objects.GUID_BYTES
            if cursor > end:
                return None
    past_flag = _independent_guid_flag(body, cursor, end)
    if past_flag is None or size < 0 or past_flag + size > end:
        return None
    return (word[0], past_flag, size)


def _independent_guid_flag(body: bytes, at: int, end: int) -> int | None:
    """Step the property-guid flag, and the guid when it is set.

    Args:
        body: The decompressed body.
        at: Where the flag byte sits.
        end: The first byte past the payload.

    Returns:
        Where the value begins, or None when the flag is neither 0 nor 1.
    """
    if at + 1 > end:
        return None
    flag = body[at]
    if flag == 1:
        return at + 1 + objects.GUID_BYTES
    return at + 1 if flag == 0 else None


#: The one type word whose tag extra is a BYTE rather than a string run. Spelled
#: here because ``objects._read_tag_header`` spells it inline rather than
#: exporting it, and the reading above has to branch on the same thing.
_BOOL_TYPE_WORD: Final = "BoolProperty"


#: EVERY SYMBOL OF ``clockspeed.save.objects`` THE SECOND TAG READING EXECUTES -
#: CS-863, and the enumeration is the item as much as the ceiling repair was.
#:
#: WHAT IT IS FOR. The arms in this module that compare the two readings are
#: evidence about a shipped reader only to the extent the two readings do not
#: share it. Anything named here is shared, so a defect in it moves BOTH sides
#: and no agreement between them is evidence about it. That limit used to be a
#: docstring naming four symbols "among them", and a sample is not an
#: enumeration: the one shared symbol that had actually been disclosed anywhere
#: was ``BODY_LAYOUT_BY_PAIR``, over in :mod:`tests.save.independent_table`, and
#: it was the only one guarded.
#:
#: WHY A CEILING IS NOT IN IT ANY MORE. A shared CEILING is a shared decision
#: about which records leave the population, so a stricter one deleted the same
#: records from both readings and every equality here stayed green while the
#: denominator shrank. ``_MAX_TAGS_PER_PAYLOAD`` was that, and its absence from
#: this set is asserted by name below rather than left to the equality, because
#: a set that merely happens not to contain it today says nothing about
#: tomorrow.
#:
#: WHAT REMAINS IS WIDTHS AND NAMES, and their sharing is not the same defect.
#: A second reading of a format cannot disagree with the format's own field
#: widths and still be reading that format, so these are DATA the two readings
#: are obliged to hold in common. That is a limit rather than a hole, and it is
#: written down rather than argued away. What a plant on each one actually does
#: was MEASURED for CS-863 and recorded in `docs/LEDGER.md` - two of them behave
#: nothing like the ceiling, and one of them moves nothing at all.
#:
#: NO COUNT OF THESE NAMES IS WRITTEN IN PROSE anywhere; the set is the record
#: and ``len`` is how anyone asks. The idiom is
#: ``objects.REFERENCE_COUNT_COMMON_MODE``'s, which CS-835 established for the
#: same reason one level up.
TAG_READING_SHARED_SYMBOLS: Final = frozenset(
    {
        "GUID_BYTES",
        "INT32_SIZE",
        "MAX_OBJECTS",
        "MAX_STRING_BYTES",
        "STRUCT_TYPE_WORD",
        "UTF16_CHAR_SIZE",
        "_PAYLOAD_TERMINATOR",
        "_TAG_EXTRA_STRINGS",
        "_TAG_INDEX_FIELD_BYTES",
    }
)


#: The functions that ARE the second tag reading, named as the derivation's
#: seeds. :func:`_independent_sites_of` is the entry point every caller in this
#: module uses; the rest are reached from it and are named anyway so that a seed
#: going unreferenced is a red test rather than a silent narrowing of the
#: surface this claims to cover.
_TAG_READING_SEEDS: Final = (
    "_independent_sites_of",
    "_independent_actor_head",
    "_independent_tag_list",
    "_independent_tag_walk",
    "_independent_tag_header",
    "_independent_guid_flag",
    "_independent_string",
)

#: The AST node types a function definition can be.
_ANY_FUNCTION: Final = (ast.FunctionDef, ast.AsyncFunctionDef)


def _module_bindings(tree: ast.Module) -> dict[str, ast.AST]:
    """Map every module-level name to the node that would be EXECUTED for it.

    ASSIGNMENTS ARE INCLUDED AND THAT IS THE POINT. A constant such as
    ``_MIN_INTERIOR_TAG_BYTES`` is where several shipped widths are actually
    read, so a derivation that walked only function bodies would miss them and
    report a surface narrower than the real one - which is the exact fault this
    whole set exists to end.

    Args:
        tree: The parsed module.

    Returns:
        Name to the node to walk for it.
    """
    bindings: dict[str, ast.AST] = {}
    for node in tree.body:
        if isinstance(node, (*_ANY_FUNCTION, ast.ClassDef)):
            bindings[node.name] = node
            continue
        value = getattr(node, "value", None)
        if value is None:
            continue
        targets = list(getattr(node, "targets", ()) or ())
        annotated = getattr(node, "target", None)
        if annotated is not None:
            targets.append(annotated)
        for target in targets:
            if isinstance(target, ast.Name):
                bindings[target.id] = value
    return bindings


def _executed_nodes(scope: ast.AST) -> list[ast.AST]:
    """Every node under ``scope`` that RUNS, with annotations excluded.

    ANNOTATIONS ARE NOT EXECUTION. This module is under ``from __future__ import
    annotations``, where an annotation is never evaluated at all, so counting
    one would overstate the shared surface and make the record churn on a
    cosmetic type change - which is how a record stops being read.

    Args:
        scope: A function, a class or any expression node.

    Returns:
        The nodes, ``scope`` itself included when it is not a definition.
    """
    stack: list[ast.AST] = list(
        scope.body if isinstance(scope, (*_ANY_FUNCTION, ast.ClassDef)) else [scope]
    )
    seen: list[ast.AST] = []
    while stack:
        node = stack.pop()
        seen.append(node)
        for field_name, value in ast.iter_fields(node):
            if field_name in {"annotation", "returns"}:
                continue
            if field_name == "args" and isinstance(node, _ANY_FUNCTION):
                continue
            stack.extend(
                item
                for item in (value if isinstance(value, list) else [value])
                if isinstance(item, ast.AST)
            )
    return seen


@lru_cache(maxsize=1)
def _shared_tag_symbols() -> frozenset[str]:
    """Derive what the second tag reading reaches inside ``clockspeed.save.objects``.

    IT READS SOURCE, NOT BEHAVIOUR, and that is deliberate: the claim is about
    which symbols the two readings SHARE, and two readings agreeing at runtime is
    exactly the evidence that would be worthless here.

    QUALIFIED ACCESS ONLY. A bare attribute name would pick up ``record.kind``
    and every other attribute that happens to share a spelling with a shipped
    one, inflating the record with symbols nothing here touches.

    Returns:
        Every ``objects.<name>`` reachable from the seeds, closed over this
        module's own module-level bindings.
    """
    tree = ast.parse(Path(__file__).read_text(encoding="ascii"))
    bindings = _module_bindings(tree)

    reached: set[str] = set()
    seen: set[str] = set()
    stack = list(_TAG_READING_SEEDS)
    while stack:
        name = stack.pop()
        if name in seen:
            continue
        seen.add(name)
        node = bindings.get(name)
        if node is None:
            continue
        for used in _executed_nodes(node):
            if (
                isinstance(used, ast.Attribute)
                and isinstance(used.value, ast.Name)
                and used.value.id == "objects"
            ):
                reached.add(used.attr)
            elif isinstance(used, ast.Name) and used.id in bindings and used.id not in seen:
                stack.append(used.id)
    return frozenset(reached)


def test_every_shipped_symbol_the_second_tag_reading_shares_is_recorded() -> None:
    """CS-863. The limit is a recorded set, and this holds it to the real surface.

    A SYMBOL JOINING OR LEAVING THE SHARED SET REDDENS HERE, which is the whole
    of what recording it buys. Before this, what the two tag readings share
    lived in a docstring that named four symbols and said "among them" - and a
    docstring cannot notice a refactor that widens the surface it describes, nor
    that it was never complete in the first place.

    THE CEILING'S ABSENCE IS ASSERTED BY NAME, not merely observed. It is the
    one shared symbol measured to make this module's grade IMPROVE as the reader
    got strictly worse, so its return would be a regression rather than a
    widening, and an equality alone would report it in the same voice as any
    other drift.

    EVERY SEED IS REQUIRED TO EXIST. A seed silently renamed away would narrow
    the derived surface to nothing and leave this arm green over an empty claim,
    which is this project's most-repeated failure shape.

    NEEDS NO SAVE LIBRARY AND NO INSTALL - it is a claim about the repo.
    """
    derived = _shared_tag_symbols()

    assert derived == set(TAG_READING_SHARED_SYMBOLS), (
        "the recorded shared surface no longer matches what the second tag reading "
        f"actually reaches. joined since it was recorded: "
        f"{sorted(derived - TAG_READING_SHARED_SYMBOLS)}; left it: "
        f"{sorted(TAG_READING_SHARED_SYMBOLS - derived)}"
    )

    bindings = _module_bindings(ast.parse(Path(__file__).read_text(encoding="ascii")))
    missing = [seed for seed in _TAG_READING_SEEDS if seed not in bindings]
    assert not missing, (
        f"{missing} are named as the second tag reading and no longer exist in this "
        "module, so the derivation above closed over less than it claims to"
    )

    assert "_MAX_TAGS_PER_PAYLOAD" not in derived, (
        "the second tag reading consults the shipped tag ceiling again. THAT IS THE "
        "CS-863 DEFECT RETURNING: a shared ceiling is a shared decision about which "
        "records leave the population, so a stricter one deletes the same records from "
        "both readings and every equality in this module holds while the denominator "
        "shrinks. Measured before the repair, pair-shaped: at 12 this module showed one "
        "failing arm and at 0 - strictly worse - it showed none and exited 0"
    )
    for reader in ("parse_body", "read_properties", "_walk_payload", "_payload_text"):
        assert reader not in derived, (
            f"the second tag reading now reaches objects.{reader} - a shipped READER, not "
            "a constant - so it is no longer a second reading of anything and every "
            "equality in this module comparing the two is one reader stated twice"
        )

    for named in ("INT32_SIZE", "_PAYLOAD_TERMINATOR", "STRUCT_TYPE_WORD"):
        assert named in TAG_READING_SHARED_SYMBOLS, (
            f"{named} is a width or a name the second reading cannot avoid sharing and "
            "it is not in the recorded set, so the set understates the limit"
        )


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


@dataclass(frozen=True)
class _SaveCensus:
    """One save's counts, so the arms can be re-aggregated over a SUBSET.

    WHY IT EXISTS. The bound this module used to carry was fitted to one
    machine's save library at one instant, and an adversary reddened it in BOTH
    directions by dropping legitimate subsets - the saves of one version pair
    taking the figure to two, another pair's taking it to zero. Autosave
    rotation does that on its own, and the operator plays the game while a
    session runs. An assertion that only ever sees the whole library cannot
    know whether it is stating a property or a coincidence.

    So every count an arm needs is kept PER SAVE, and
    :func:`test_the_site_equality_survives_every_legitimate_subset` re-asserts
    the equality over every leave-one-out subset, every single save alone and
    every version pair alone. A property survives all of them; a fitted number
    does not survive the first.

    EVERY FIELD IS AN INTEGER AND ``pair_id`` IS AN ORDINAL. It is assigned in
    first-seen order at sweep time and is NOT a version number, so grouping by
    version pair costs this module no rendering of one - the discipline
    :class:`_SaveShape` states, kept while exposing the grouping.

    Attributes:
        pair_id: An ordinal standing for this save's version pair.
        records: How many records the save's table carried.
        shipped_reached: Records the shipped walk enumerated.
        independent_reached: Records this module's own reading enumerated.
        sites_seen: Struct sites the shipped walk reached here.
        independent_sites: Struct sites this module's own reading found here.
        census_records: Struct type words inside the records' declared extents.
        census_unreached: The same, over records the shipped walk never opened.
        independent_unreached_census: The same, over records this module's own
            reading never opened.
        site_disagreements: Records where the two site counts differ.
    """

    pair_id: int
    records: int
    shipped_reached: int
    independent_reached: int
    sites_seen: int
    independent_sites: int
    census_records: int
    census_unreached: int
    independent_unreached_census: int
    site_disagreements: int


#: How deep the census tiling will descend into a struct interior. A BOUND ON
#: THE WORK, not a measurement: a region past it lands in ``census_struct_values``
#: rather than being lost, so the accounting closes whatever the depth is.
_MAX_CENSUS_DEPTH: Final = 8


def _tile_independently(body: bytes, at: int, end: int, into: _StructTally, depth: int) -> bool:
    """Attribute EVERY struct type word in this span to a named class.

    THE ACCOUNTING THE THIRD REFUTATION ASKED FOR. ``_census_hits`` is the one
    number in this module no reader can move, and over the records the sweep
    reached it stands at far more than the site count - the difference used to
    be waved at as "nested interiors, container element words, coincidental
    bytes" without a count against any of them. An unaccounted difference is a
    place a site can go missing to, so the difference is TILED here: the span is
    partitioned into tag names, type words, tag headers, values and the tail,
    every partition is counted, and the sum is asserted against the census.

    IT READS WITH THIS MODULE'S OWN GRAMMAR AND NOT THE SHIPPED ONE, which is
    the whole point. A shipped tag-list reader that starts refusing cannot move
    a single number this function produces.

    NOTHING IS MUTATED ON A REFUSAL. The walk is taken before the loop, so a
    span this reading cannot follow leaves every counter exactly as it found
    them and the caller attributes the whole span to one class instead.

    Args:
        body: The decompressed body.
        at: Where the first tag begins.
        end: The first byte past the span.
        into: The accumulator, mutated in place.
        depth: How many interiors deep this span sits.

    Returns:
        Whether this reading walked the span - False leaves the counters
        untouched.
    """
    tags = _independent_tag_walk(body, at, end)
    if tags is None:
        return False
    cursor = at
    for _name_at, type_at, word, value_at, size in tags:
        into.census_names += _census_hits(body, cursor, type_at)
        is_struct = body.startswith(_STRUCT_WORD_LITERAL, type_at)
        if is_struct:
            if depth == 0:
                into.independent_sites += 1
            else:
                into.census_nested_sites += 1
            into.census_element_words += _census_hits(
                body, type_at + len(_STRUCT_WORD_LITERAL), value_at
            )
        else:
            into.census_element_words += _census_hits(body, type_at, value_at)
        inside = _census_hits(body, value_at, value_at + size)
        if inside:
            descended = (
                is_struct
                and depth < _MAX_CENSUS_DEPTH
                and _tile_independently(body, value_at, value_at + size, into, depth + 1)
            )
            if not descended:
                if word in objects.CONTAINER_TYPE_WORDS:
                    into.census_container_values += inside
                elif is_struct:
                    into.census_struct_values += inside
                else:
                    into.census_other_values += inside
        cursor = value_at + size
    into.census_tails += _census_hits(body, cursor, end)
    return True


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
        tags_seen: EVERY tag the walk yielded, of every type. The widest
            denominator this module has, and the one the struct classification
            below is graded against.
        reader_only_struct: Tags the TAG READER called a struct where the bytes
            at the type-word offset are not the struct literal.
        bytes_only_struct: Tags whose bytes ARE the struct literal and which
            the tag reader called something else. THE ARM THE SECOND
            REFUTATION DEMANDED.
        independent_walkable: Records this module's OWN reading accepts as a
            tag list, sharing no function with the shipped walk.
        refused_but_independent: Records the shipped walk refused that this
            module's own reading accepts. The graded residue for a refusal.
        sites_seen: Every tag whose BYTES carry the struct type word, counted
            BEFORE the tag extra is read and without asking the tag reader what
            type it is. THE DENOMINATOR THE REFUTATION DEMANDED - see
            :func:`_sweep_one_save` for why taking it from the reader is the
            defect.
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
        independent_only_refused: Records the shipped walk ACCEPTS and this
            module's own reading refuses. The converse of
            ``refused_but_independent``, and asserting both to zero is what
            makes the two readings one population rather than two.
        independent_sites: Top-level struct sites THIS MODULE'S OWN READING
            finds, over the records it accepts. THE DENOMINATOR NO SHIPPED
            TAG-LIST READER CAN SHORTEN - see
            :func:`test_the_site_total_is_pinned_by_a_reading_no_shipped_walk_can_shorten`.
        site_disagreements: Records where the two readings report a DIFFERENT
            struct site count. Asserted per record rather than only in the
            pool, because a pooled equality is met by offsetting errors.
        independent_unreached_census: Struct type words the BYTES carry inside
            records this module's own reading does not walk.
        census_nested_sites: Struct type words standing at a tag's type-word
            offset INSIDE a decoded interior - the nested class.
        census_element_words: Struct type words inside a tag's header past its
            type word - a container naming a struct as its element type.
        census_container_values: Struct type words inside a CONTAINER tag's
            value.
        census_struct_values: Struct type words inside a struct tag's value
            that does not itself walk as a tag list - the native class.
        census_other_values: Struct type words inside any other tag's value.
        census_head: Struct type words inside an actor payload's head.
        census_names: Struct type words inside a tag's NAME string.
        census_tails: Struct type words past a tag list's last tag.
        censuses: One per save, for the subset re-aggregation.
        pair_ids: Version pair to the ordinal that stands for it, so no version
            number leaves this frame.
    """

    saves: int = 0
    records: int = 0
    tags_seen: int = 0
    reader_only_struct: int = 0
    bytes_only_struct: int = 0
    independent_walkable: int = 0
    refused_but_independent: int = 0
    independent_only_refused: int = 0
    independent_sites: int = 0
    site_disagreements: int = 0
    independent_unreached_census: int = 0
    census_nested_sites: int = 0
    census_element_words: int = 0
    census_container_values: int = 0
    census_struct_values: int = 0
    census_other_values: int = 0
    census_head: int = 0
    census_names: int = 0
    census_tails: int = 0
    censuses: list[_SaveCensus] = field(default_factory=list)
    pair_ids: dict[tuple[int, int], int] = field(default_factory=dict)
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
        tags_seen: Every tag the walk yielded, of every type.
        reader_only_struct: Tags the tag reader called a struct where the bytes
            disagree.
        bytes_only_struct: Tags whose bytes are the struct literal and which
            the tag reader called something else.
        independent_walkable: Records this module's own reading accepts.
        refused_but_independent: Records the shipped walk refused that this
            module's own reading accepts.
        sites_seen: Every tag whose BYTES carry the struct type word, counted
            before the tag extra was read.
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
        independent_only_refused: Records the shipped walk accepts and this
            module's own reading refuses.
        independent_sites: Top-level struct sites this module's own reading
            found - THE DENOMINATOR NO SHIPPED TAG-LIST READER CAN SHORTEN.
        site_disagreements: Records where the two readings disagree about how
            many struct sites the record holds.
        independent_unreached_census: Struct type words inside records this
            module's own reading does not walk.
        census_nested_sites: Struct type words at a tag's type-word offset
            inside a decoded interior.
        census_element_words: Struct type words inside a tag's header past its
            own type word.
        census_container_values: Struct type words inside a container value.
        census_struct_values: Struct type words inside a struct value that does
            not itself walk as a tag list.
        census_other_values: Struct type words inside any other value.
        census_head: Struct type words inside an actor payload's head.
        census_names: Struct type words inside a tag's name string.
        census_tails: Struct type words past a tag list's last tag.
        censuses: One entry per save, for the subset re-aggregation.
    """

    saves: int
    records: int
    tags_seen: int
    reader_only_struct: int
    bytes_only_struct: int
    independent_walkable: int
    refused_but_independent: int
    independent_only_refused: int
    independent_sites: int
    site_disagreements: int
    independent_unreached_census: int
    census_nested_sites: int
    census_element_words: int
    census_container_values: int
    census_struct_values: int
    census_other_values: int
    census_head: int
    census_names: int
    census_tails: int
    censuses: tuple[_SaveCensus, ...]
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
            f"tags_seen={self.tags_seen}, "
            f"reader_only_struct={self.reader_only_struct}, "
            f"bytes_only_struct={self.bytes_only_struct}, "
            f"independent_walkable={self.independent_walkable}, "
            f"refused_but_independent={self.refused_but_independent}, "
            f"independent_only_refused={self.independent_only_refused}, "
            f"independent_sites={self.independent_sites}, "
            f"site_disagreements={self.site_disagreements}, "
            f"independent_unreached_census={self.independent_unreached_census}, "
            f"census_nested_sites={self.census_nested_sites}, "
            f"census_element_words={self.census_element_words}, "
            f"census_container_values={self.census_container_values}, "
            f"census_struct_values={self.census_struct_values}, "
            f"census_other_values={self.census_other_values}, "
            f"census_head={self.census_head}, census_names={self.census_names}, "
            f"census_tails={self.census_tails}, censuses={len(self.censuses)}, "
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


def _struct_word_at(body: bytes, type_at: int, end: int, into: _StructTally) -> str | None:
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
        type_at: Where the tag's TYPE WORD begins - just past its name.
        end: The first byte past the payload.
        into: The accumulator, mutated in place.

    Returns:
        The struct word, or None when a reader between the walk and the decoder
        refused - in which case the refusal has been counted.
    """
    words = objects._container_element_words(  # noqa: SLF001
        body, type_at, end, objects.STRUCT_TYPE_WORD
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


def _fold_one_tag(
    body: bytes,
    word: str,
    name_at: int,
    value_at: int,
    size: int,
    end: int,
    property_map: usmap.PropertyMap,
    into: _StructTally,
) -> None:
    """Fold one tag of ANY type, classifying it by its bytes rather than by word.

    EVERY TAG IS COUNTED, NOT EVERY STRUCT TAG, AND THAT IS THE REPAIR. The
    previous revision skipped in the sweep's loop unless the walk's type word
    said ``StructProperty`` - and that word comes from
    ``objects._read_tag_header``, a READER standing between the walk and the
    counting point. A site it mislabelled was deleted before anything could
    count it: no counter, no residue, no census, and the population graded
    better for the absence.

    MEASURED: making that reader report a different word for struct tags at even
    offsets on real bodies removed 22229 of 45208 sites, drove the
    size-compatible residue from 12 to 5, and both modules stayed green at exit
    0. The classification is taken from the BYTES here instead - a comparison
    against the length-prefixed literal at the tag's type-word offset - and what
    the reader says is graded against that in both directions.

    Args:
        body: The decompressed body.
        word: The type word the shipped tag reader reported.
        name_at: Where the tag's NAME begins - the walk's own cursor.
        value_at: Where the tag's value begins.
        size: The value's declared extent.
        end: The first byte past the payload.
        property_map: The parsed usmap.
        into: The accumulator, mutated in place.
    """
    into.tags_seen += 1
    name_read = objects._payload_text(body, name_at, end)  # noqa: SLF001
    if name_read is None:
        into.name_unread += 1
        return
    reader_says = word == objects.STRUCT_TYPE_WORD
    bytes_say = body.startswith(_STRUCT_WORD_LITERAL, name_read[1])
    if reader_says and not bytes_say:
        into.reader_only_struct += 1
    if bytes_say and not reader_says:
        into.bytes_only_struct += 1
    if not bytes_say:
        return
    # COUNTED HERE AND NOWHERE LATER. Every line below this one may refuse; none
    # of them may shrink the number this line just raised.
    into.sites_seen += 1
    if size == _TERMINATOR_ONLY_BYTES:
        into.bare_terminator_sites += 1
    struct_word = _struct_word_at(body, name_read[1], end, into)
    if struct_word is None:
        if _size_admits_a_tag_list(size):
            into.wordless_compatible += 1
        return
    _fold_one_struct_tag(body, struct_word, value_at, value_at + size, property_map, into)


def _pair_ordinal(into: _StructTally, pair: tuple[int, int]) -> int:
    """An ordinal standing for a save version pair, assigned in first-seen order.

    THE ORDINAL RATHER THAN THE PAIR IS WHAT LEAVES THIS FRAME. Grouping the
    subset re-aggregation by version pair needs only that two saves of the same
    pair get the same key - it does not need the pair's numbers, and this
    module's rule is that only counts leave. An exception argued case by case is
    how such a rule stops holding.

    Args:
        into: The accumulator, whose ordinal table is extended in place.
        pair: The save and header version.

    Returns:
        The ordinal for that pair.
    """
    return into.pair_ids.setdefault(pair, len(into.pair_ids))


@dataclass
class _SaveRun:
    """One save's running counters, so the per-save census can be exact.

    THEY ARE PER SAVE RATHER THAN DERIVED AT THE END because the subset
    re-aggregation has to be able to drop a save and re-assert, and a figure
    reconstructed from the pooled totals could not be dropped from them.

    Attributes:
        sites_before: The pooled site total when this save started.
        independent_before: The pooled independent site total when it started.
        records: Records seen in this save.
        unreached: Records the shipped walk never opened.
        independent_reached: Records this module's own reading opened.
        hits: Struct type words inside this save's record extents.
        unreached_hits: The same, over records the shipped walk never opened.
        independent_unreached_hits: The same, for this module's own reading.
        disagreements: Records where the two site counts differ.
    """

    sites_before: int
    independent_before: int
    records: int = 0
    unreached: int = 0
    independent_reached: int = 0
    hits: int = 0
    unreached_hits: int = 0
    independent_unreached_hits: int = 0
    disagreements: int = 0


def _sweep_one_record(
    body: bytes,
    record: objects.ObjectRecord,
    own: independent_table.IndependentRecord | None,
    property_map: usmap.PropertyMap,
    into: _StructTally,
    run: _SaveRun,
) -> None:
    """Fold ONE record into the accumulator, by both readings.

    THE TWO READINGS NOW ARRIVE SEPARATELY, which is CS-829 round 5. ``record``
    is the shipped table's; ``own`` is the second reading's own record for the
    SAME POSITION, taken from :mod:`tests.save.independent_table`, which reads
    the body's record framing without calling one function of
    ``clockspeed.save.objects``. Before this the independent reading took its
    start, its extent and its kind off ``record`` too, so the denominator rested
    on the very table it was meant to be independent of - measured, a degraded
    table moved both totals from 30642 sites to 0 and no arm went red. ``own``
    is None where the second reading declined the save or could not be paired,
    and the independent reading is then counted as UNREACHED rather than being
    quietly handed the shipped record's window.

    EVERY DROP IS COUNTED AND NOTHING LEAVES SILENTLY. Four readers stand
    between a record and a graded site: the actor-head step, the payload walk,
    the tag-name re-read and the tag extra. Each used to end in a bare
    ``continue``. Now each has a counter, the records the first two refuse are
    additionally measured IN BYTES by :func:`_census_hits`, and the site total
    is taken a SECOND time by a reading that shares no function with the walk.

    Args:
        body: The decompressed body.
        record: The record to fold, from the SHIPPED table.
        own: The SECOND reading's record for the same position, or None when it
            declined this save or the two readings could not be paired.
        property_map: The parsed usmap.
        into: The accumulator, mutated in place.
        run: This save's running counters, mutated in place.
    """
    into.records += 1
    run.records += 1
    end = record.body_offset + record.body_length
    hits = _census_hits(body, record.body_offset, end)
    into.census_records += hits
    run.hits += hits
    # THE SHIPPED READER'S OWN TOTALS, taken through an entry point this module
    # uses for nothing else. ``struct_tag_count`` is incremented in
    # ``objects._walk_payload`` BEFORE the struct word is read, so it is a
    # denominator no tag-extra defect can move - and it comes from a loop
    # written independently of the one below. WHAT IT CANNOT SEE is a defect in
    # a primitive BOTH loops call, which is why the reading below exists.
    shipped = objects.read_properties(body, record, property_map)
    into.shipped_tags += shipped.struct_tag_count
    into.shipped_interiors += len(shipped.struct_interiors)
    # THIS MODULE'S OWN READING OF THE SAME RECORD, taken BEFORE the shipped
    # walk and sharing no function with it - see :func:`_independent_tag_walk`.
    # IT IS THE DENOMINATOR, not merely a corroborator of a refusal. Counting
    # sites here is what the third refutation asked for: a record the shipped
    # walk ACCEPTS while yielding fewer tags than it holds used to be outside
    # every arm, because the only question ever asked of this reading was about
    # records the shipped walk had already refused.
    own_end = end if own is None else own.body_offset + own.body_length
    own_start = (
        None
        if own is None
        else (
            _independent_actor_head(body, own.body_offset, own_end)
            if own.is_actor
            else own.body_offset
        )
    )
    own_sites = into.independent_sites
    own_reads = own_start is not None and _tile_independently(body, own_start, own_end, into, 0)
    if own_reads and own_start is not None and own is not None:
        into.independent_walkable += 1
        run.independent_reached += 1
        into.census_head += _census_hits(body, own.body_offset, own_start)
    else:
        into.independent_unreached_census += hits
        run.independent_unreached_hits += hits
    own_sites = into.independent_sites - own_sites
    start: int | None = record.body_offset
    if record.kind == objects.KIND_ACTOR:
        start = objects._skip_actor_head(body, record.body_offset, end)  # noqa: SLF001
    walked = (
        None
        if start is None
        else test_decode_oracles._walk_with_the_shipped_reader(body, start, end)  # noqa: SLF001
    )
    if start is None or walked is None:
        into.head_unread += start is None
        into.unwalked += start is not None
        into.census_unreached += hits
        run.unreached_hits += hits
        into.refused_but_independent += own_reads
        run.unreached += 1
        return
    if not own_reads:
        into.independent_only_refused += 1
    shipped_sites = into.sites_seen
    at = start
    for _name, word, value_at, size in walked:
        head = at
        at = value_at + size
        _fold_one_tag(body, word, head, value_at, size, end, property_map, into)
    # PER RECORD, NEVER ONLY IN THE POOL. A pooled equality is met by
    # offsetting errors - a reader losing a site here and inventing one there
    # sums to zero - which is the shape CLAUDE.md section 5 and this repo's
    # pooled-guard finding both name as a threshold met by its strongest member.
    shipped_sites = into.sites_seen - shipped_sites
    if own_reads and shipped_sites != own_sites:
        into.site_disagreements += 1
        run.disagreements += 1


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

    THE PER-RECORD JUDGEMENT IS :func:`_sweep_one_record`, which is where every
    drop is counted; this function owns the save-level bookkeeping and the two
    per-save records the shape reduction and the subset re-aggregation need.

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
    # SNAPSHOTS, because the site totals are raised deep inside the fold and
    # the tiling rather than here, and the subset re-aggregation needs them PER
    # SAVE. Subtracting at the end of the loop is exact and costs two integers.
    run = _SaveRun(sites_before=into.sites_seen, independent_before=into.independent_sites)
    # THE SECOND READING OF THE RECORD FRAMING, taken ONCE per save and paired
    # POSITIONALLY - the k-th independent record against the k-th shipped one.
    # PAIRING IS ONLY DEFINED WHERE THE TWO AGREE ON HOW MANY RECORDS THERE ARE.
    # Where they do not, none is paired and every independent reading of this
    # save declines, on exactly the terms `objects._attribute_payloads` states
    # for a level whose record and payload counts disagree: zipping the shorter
    # list would pair a record with another record's window and report it as
    # fact, which is the silently wrong answer non-negotiable 7 forbids.
    # `tests/save/test_independent_table.py` asserts that agreement, in file
    # order, as an EQUALITY over this machine's whole library.
    mine = independent_table.independent_records(
        body, save_version=parsed.save_version, header_version=parsed.header_version
    )
    paired = mine if mine is not None and len(mine) == len(table.records) else None
    for index, record in enumerate(table.records):
        _sweep_one_record(
            body, record, None if paired is None else paired[index], property_map, into, run
        )
    into.shapes.append(
        _SaveShape(
            pair=(parsed.save_version, parsed.header_version),
            records=run.records,
            unreached=run.unreached,
        )
    )
    into.censuses.append(
        _SaveCensus(
            pair_id=_pair_ordinal(into, (parsed.save_version, parsed.header_version)),
            records=run.records,
            shipped_reached=run.records - run.unreached,
            independent_reached=run.independent_reached,
            sites_seen=into.sites_seen - run.sites_before,
            independent_sites=into.independent_sites - run.independent_before,
            census_records=run.hits,
            census_unreached=run.unreached_hits,
            independent_unreached_census=run.independent_unreached_hits,
            site_disagreements=run.disagreements,
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
    save whole makes its pair contested.

    A DEFECT SHAPED EXACTLY LIKE A WHOLE VERSION PAIR ESCAPES BOTH, AND THE
    SHIPPED CROSS-CHECK DOES NOT STAND IN FRONT OF IT. An earlier revision of
    this docstring said it did. An adversary measured that claim false: patching
    ``objects._payload_text`` to refuse for one version pair, filtered to the
    payload walk so the actor-head step still reads, deleted 8362 sites and
    23046 further records with ``head_unread``, ``partial_saves`` and
    ``contested_pairs`` all zero and both modules green. The cross-check misses
    it because the loss sits in a primitive BOTH loops call, so the two
    denominators move together.

    THE SHAPE GUARDS HERE WORK ON UN-SHAPED LOSS AND DO NOTHING AGAINST SHAPED
    LOSS - which is the shape this corpus actually exhibits, its one genuinely
    unreachable population being exactly a whole version pair. What grades that
    case is :func:`test_a_record_the_shipped_walk_refuses_is_refused_by_an_independent_reading`,
    which asks the BYTES why a record was refused rather than asking a reader.

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
        tags_seen=tally.tags_seen,
        reader_only_struct=tally.reader_only_struct,
        bytes_only_struct=tally.bytes_only_struct,
        independent_walkable=tally.independent_walkable,
        refused_but_independent=tally.refused_but_independent,
        independent_only_refused=tally.independent_only_refused,
        independent_sites=tally.independent_sites,
        site_disagreements=tally.site_disagreements,
        independent_unreached_census=tally.independent_unreached_census,
        census_nested_sites=tally.census_nested_sites,
        census_element_words=tally.census_element_words,
        census_container_values=tally.census_container_values,
        census_struct_values=tally.census_struct_values,
        census_other_values=tally.census_other_values,
        census_head=tally.census_head,
        census_names=tally.census_names,
        census_tails=tally.census_tails,
        censuses=tuple(tally.censuses),
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
#: entirely and stay green - and several of the reading words have few enough
#: sites that nothing else would have noticed. At one the bound has no headroom
#: left, so the loss of ANY reading word crosses it.
#:
#: IT IS A FITTED BOUND AND IT STAYS ONE, WHICH IS A KNOWN OPEN DEFECT RATHER
#: THAN AN OVERSIGHT. A word lands in the residue for two reasons - a decoder
#: that stopped reading it, or size-excluded siblings that live in saves this
#: run did not read - and nothing a single sweep computes separates them.
#: Measured: reading one version pair of this machine's library alone moves a
#: word that is overwhelmingly native by arithmetic across the whole library into
#: the residue, and reddens this bound on nothing but which saves were present.
#:
#: CONVERTING THAT RED INTO A SKIP WAS BUILT, MEASURED AND REJECTED. The corpus a
#: single version pair presents is structurally identical to a corpus where a
#: reading word was lost, so every condition that skips the one skips the other:
#: with the excess skipping, an in-process mutant refusing the WEAKEST reading
#: word outright at ``objects._decode_struct_interior`` - the function both
#: readings route through - left the whole module at zero failures. The bound
#: reddens on some legitimate subsets and that cost is paid deliberately.
#: De-fitting it needs per-word evidence independent of which saves are present,
#: which is CS-829's open problem rather than this arm's.
#:
#: A SENTENCE CLAIMING THE OBSERVED FIGURE WAS ASSERTED TO MEET THE BOUND EXACTLY
#: USED TO STAND HERE AND IS DELETED. The assertion it described had already been
#: removed at the call site - see the note there - so the constant's own
#: documentation was describing code that no longer existed.
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


def test_a_tag_is_classified_struct_by_its_bytes_not_by_the_tag_reader() -> None:
    """THE POPULATION IS TAKEN FROM THE BYTES - the second refutation answered.

    WHAT WAS WRONG AFTER THE FIRST REPAIR. The sweep counted a site the instant
    the walk reported a STRUCT-TYPED tag, and the qualifier did all the work.
    The type word came from ``objects._read_tag_header``, which is a READER
    standing between the walk and the counting point, so a site it mislabelled
    was deleted before any counter, residue or census could see it. The first
    repair moved the defect one function upstream rather than removing it.

    MEASURED. Making that reader report a different word for struct tags at even
    offsets on real bodies removed 22229 of 45208 sites, drove the
    size-compatible residue from 12 down to 5 and the unexplained sites from 8
    down to 3, and both modules reported green at exit 0 - the grade improving
    as the reader got worse, for the third time in this item's history.

    WHAT MAKES IT FAIL NOW. Struct-ness is decided by comparing the bytes at the
    tag's type-word offset against the length-prefixed literal, which no reader
    can move, and the site is folded on THAT. What the tag reader says is no
    longer the population - it is a claim graded against the bytes, in both
    directions, so a mislabel in either direction reddens here.
    """
    sweep = _sweep_or_skip()

    assert sweep.tags_seen > 0, (
        "the walk yielded no tag of any type in this whole library, so every count "
        "below ranges over nothing"
    )
    assert sweep.sites_seen > 0, (
        "not one tag in this library carries the struct type word in its bytes, so "
        "this item's population is empty and every equality over it holds vacuously"
    )
    assert sweep.sites_seen <= sweep.tags_seen, (
        f"{sweep.sites_seen} struct sites were counted out of {sweep.tags_seen} tags, "
        "which cannot be - the struct population is a subset of the tags it was drawn "
        "from, so one of the two counters is not counting what it says"
    )

    assert sweep.bytes_only_struct == 0, (
        f"{sweep.bytes_only_struct} tags carry the struct type word IN THEIR BYTES and "
        "the tag reader called them something else. THIS IS THE ARM THE SECOND "
        "REFUTATION ASKED FOR: before it, such a tag left the population silently and "
        "the remaining sites graded better for its absence. The site is now counted "
        "from the bytes and the disagreement is reported here instead"
    )
    assert sweep.reader_only_struct == 0, (
        f"{sweep.reader_only_struct} tags were called struct by the tag reader where "
        "the bytes at the type-word offset are not the struct literal. That direction "
        "cannot inflate the population - the fold is on the bytes - but it means the "
        "reader and the bytes disagree about where a tag's type word sits, and every "
        "offset this module derives from that reader is then suspect"
    )


def test_a_record_the_shipped_walk_refuses_is_refused_by_an_independent_reading() -> None:
    """SHAPED LOSS, WHICH EVERY SHAPE GUARD IN THIS MODULE MISSES.

    THE GUARDS ABOVE GRADE THE SHAPE OF A REFUSAL - whole save, whole version
    pair - and an adversary measured that shaped loss walks straight through
    them. Patching ``objects._payload_text`` for one version pair, filtered to
    the payload walk so the actor-head step still reads, deleted 8362 sites and
    23046 further records while ``head_unread``, ``partial_saves`` and
    ``contested_pairs`` all stayed at zero and ``census_body`` still equalled
    ``census_records``. Every arm green, exit 0. Shaped loss is also the only
    kind this corpus exhibits, so the shape guards were tuned against the single
    case they are blind to.

    WHAT THIS ASKS INSTEAD. Not what shape the loss has, but whether the refusal
    can be corroborated by a reading that shares no code with the one that
    refused - see the block above :func:`_independent_tag_list`. A record the
    shipped walk refuses AND this module cannot read either is a refusal with
    two independent sources. A record the shipped walk refuses and this module
    reads perfectly well is a reader that has stopped working.

    IT IS ONE-SIDED AND THE LIMIT IS REAL. The independent reading is
    conservative - it accepts fewer records than the shipped walk, not more -
    so nothing is claimed about records only the shipped walk accepts, and a
    loss confined entirely to those would still escape. What it does close is
    the measured mutant: that pair's records remain readable here while the
    shipped walk refuses them, and this reddens by five figures.
    """
    sweep = _sweep_or_skip()

    assert sweep.independent_walkable > 0, (
        "this module's own reading of the tag-list grammar accepts no record at all, "
        "so it corroborates nothing and this arm grades nothing. Either the grammar "
        "moved under it or the reading is broken"
    )

    assert sweep.refused_but_independent == 0, (
        f"the shipped walk refused {sweep.refused_but_independent} records that this "
        "module reads for itself as a closing tag list. Two readings of one grammar "
        "disagree, and the one that refused is the one this suite's whole population "
        "is drawn through - so its refusals are shrinking the denominator rather than "
        "landing in any residue. A refusal is gradeable only when something that did "
        "not refuse can be asked about it"
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


def test_the_site_total_is_pinned_by_a_reading_no_shipped_walk_can_shorten() -> None:
    """CS-829's THIRD REFUTATION, ANSWERED - the denominator moves out of reach.

    WHAT WAS STILL WRONG. Every denominator this module had came, one way or
    another, through ``objects._payload_text``. The sweep's own walk consumes
    its terminator verdict and so does ``read_properties``, so the two move
    TOGETHER: an early terminator leaves a record accepted, deletes struct sites
    from both loops at once, and every cross-check between them stays green
    while the residue gets SMALLER. Measured on this corpus by an adversary: a
    truncation that changed no record's accept status deleted 3549 sites and the
    residue improved from 12 to 11, exit 0; at a coarser modulus it deleted
    19668 of 45208 and the residue fell to 5. The check got BETTER as the reader
    got WORSE.

    WHAT MAKES IT FAIL NOW. ``independent_sites`` is counted by
    :func:`_independent_tag_walk`, which takes nothing from the shipped module
    but CONSTANTS - widths, a terminator name, a tag-extra table. No shipped
    tag-list reader can move it. The shipped side's total is then asserted
    EQUAL to it, so a shipped reader that loses sites opens a gap instead of
    shrinking a population.

    IT IS ASSERTED PER RECORD AS WELL AS IN THE POOL, because a pooled equality
    is met by offsetting errors and this repo has already shipped one guard that
    a population's strongest member satisfied on behalf of its weakest.

    THE LIMIT, STATED, AND IT MOVED AGAIN IN CS-863. The two readings no longer
    share the record table - the independent side takes its window and kind from
    :mod:`tests.save.independent_table`, which reads the body's record framing
    without calling one shipped reader - and they no longer share the TAG
    CEILING either. That one was the live hole: both walks ran
    ``range(objects._MAX_TAGS_PER_PAYLOAD)``, so a stricter ceiling deleted the
    same records from both sides and this equality held while the population
    shrank. Measured before the repair, pair-shaped: at 12 this module showed
    ONE failing arm, at 0 it showed NONE and exited 0.
    :func:`_independent_tag_walk` now takes its bound from the extent.

    WHAT IS STILL SHARED IS ENUMERATED RATHER THAN SAMPLED. Both readings still
    run ``chunks.decompress_body`` and both still read the shipped grammar
    constants - widths, a terminator name, a tag-extra table - which are DATA
    and which no second reading of the same format could disagree with and
    still be reading it. The full set is :data:`TAG_READING_SHARED_SYMBOLS`,
    derived from the source by
    :func:`test_every_shipped_symbol_the_second_tag_reading_shares_is_recorded`
    so it cannot drift, and what a plant on each one actually does is measured
    in `docs/LEDGER.md` under CS-863 rather than assumed from the ceiling.
    """
    sweep = _sweep_or_skip()

    assert sweep.independent_sites > 0, (
        "this module's own reading of the tag grammar finds no struct site anywhere "
        "in this library, so the denominator below is empty and the equality holds "
        "against any shipped reader at all - including one that refuses everything"
    )
    assert sweep.independent_walkable > 0, (
        "this module's own reading accepts no record at all, so it pins nothing"
    )

    assert sweep.sites_seen == sweep.independent_sites, (
        f"the shipped walk reached {sweep.sites_seen} struct sites where this module's "
        f"OWN reading of the same records finds {sweep.independent_sites}. The two "
        "share no tag-list function, so this is a reader losing or inventing sites "
        "rather than a smaller population - which is exactly the direction every "
        "count derived from the shipped walk cannot show on its own"
    )

    assert sweep.site_disagreements == 0, (
        f"{sweep.site_disagreements} records carry a different struct site count under "
        "the two readings. The pooled equality above can be met by a reader that loses "
        "a site in one record and invents one in another; this cannot"
    )

    assert sweep.refused_but_independent == 0, (
        f"the shipped walk refused {sweep.refused_but_independent} records that this "
        "module reads for itself as a closing tag list. Its refusals are then "
        "shrinking the denominator rather than landing in any residue"
    )
    assert sweep.independent_only_refused == 0, (
        f"this module's own reading refuses {sweep.independent_only_refused} records "
        "the shipped walk accepts. THE EQUALITY ABOVE NEEDS BOTH DIRECTIONS: a "
        "conservative second reading that covers only the easy records grades the easy "
        "records. Before this arm existed the second reading could not follow a single "
        "STRUCT tag - it did not step the struct guid - so it accepted 87302 records "
        "carrying no struct site at all and corroborated nothing this item is about"
    )


def test_every_struct_type_word_the_sweep_reached_falls_in_exactly_one_named_class() -> None:
    """THE DIFFERENCE BETWEEN THE CENSUS AND THE SITE TOTAL, ACCOUNTED FOR.

    ``_census_hits`` counts a fixed nineteen-byte literal and no reader can move
    it. Over the records the sweep reached it stands far above the site total,
    and the gap used to be waved at in prose - "nested interiors, container
    element words, coincidental bytes" - with no count against any of them. AN
    UNACCOUNTED DIFFERENCE IS SOMEWHERE A SITE CAN GO MISSING TO: a reader that
    loses sites can always be explained as a population that was smaller than it
    looked, because nothing says what the rest of the occurrences are.

    SO EVERY OCCURRENCE IS ATTRIBUTED. :func:`_tile_independently` partitions
    each reached record into tag names, type words, tag headers, values and the
    tail, descends into any struct value that itself walks as a tag list, and
    counts the literal in each partition. The classes are disjoint by
    construction and this asserts they are exhaustive.

    WHAT THIS IS AND IS NOT. The closure is an identity over a tiling - it says
    the partition covers the span, not that the reader is right. What it BUYS is
    that the difference now has names and numbers, so the classes a lost site
    would have to have moved into are counted, and the site total is pinned
    against the independent reading by the arm above rather than being whatever
    is left over.

    NO CLASS IS ASSERTED TO ANY PARTICULAR VALUE. Which classes a library
    exhibits is a property of that library - a tag NAME spelling the struct type
    word is rare rather than impossible - and a count fitted to today's corpus
    is the exact defect that reddened this module's previous bound in both
    directions under legitimate subsets.
    """
    sweep = _sweep_or_skip()

    reached = sweep.census_records - sweep.independent_unreached_census
    classified = (
        sweep.independent_sites
        + sweep.census_nested_sites
        + sweep.census_element_words
        + sweep.census_container_values
        + sweep.census_struct_values
        + sweep.census_other_values
        + sweep.census_head
        + sweep.census_names
        + sweep.census_tails
    )

    assert reached > 0, (
        "the records this module's own reading opened carry no struct type word at "
        "all, so there is nothing here to account for and every class below is empty"
    )
    assert classified == reached, (
        f"{reached} struct type words lie inside records this module's own reading "
        f"walked, and {classified} of them were attributed to a class. The partition "
        "does not cover the span, so an occurrence can sit in a region no class names "
        "- which is where a lost site becomes indistinguishable from a smaller "
        "population"
    )


def test_the_census_still_exceeds_the_top_level_site_total() -> None:
    """THE STALENESS HALF OF THE ACCOUNTING, SPLIT OUT SO ITS SKIP IS PRECISE.

    IT USED TO SIT BESIDE THE PARTITION ASSERTION AND COULD NOT BE SKIPPED
    THERE. The claim is that the census and the top-level site total still
    DIFFER, so the accounting above has something to account for. A corpus that
    carries no struct type word outside a top-level tag's type-word offset - no
    nested interior, no container element word, no coincidental byte - makes the
    two equal, and that is an absent population rather than a reading that
    improved. Skipping it where it stood would have taken the partition
    assertion with it, and the partition is the arm that can actually fail.

    THE INGREDIENT IS COUNTED FROM THE BYTES. The eight classes other than the
    site total are counted by literal byte match through :func:`_tile_independently`
    with no reader involved, so "this corpus has no non-top-level occurrence" is
    a statement about the save and not about anything that could have degraded.
    """
    sweep = _sweep_or_skip()

    reached = sweep.census_records - sweep.independent_unreached_census
    elsewhere = (
        sweep.census_nested_sites
        + sweep.census_element_words
        + sweep.census_container_values
        + sweep.census_struct_values
        + sweep.census_other_values
        + sweep.census_head
        + sweep.census_names
        + sweep.census_tails
    )
    if elsewhere == 0:
        pytest.skip(
            "the saves this run read carry no struct type word anywhere but at a "
            "TOP-LEVEL tag's type-word offset, so the census and the site total have "
            "nothing to differ by. That is a corpus with no nested or incidental "
            "occurrence rather than an accounting that has gone stale"
        )
    assert sweep.independent_sites < reached, (
        f"every one of {reached} struct type words in the reached records stands at a "
        "TOP-LEVEL tag's type-word offset, while the byte census attributes "
        f"{elsewhere} of them elsewhere. The two readings of the same bytes disagree "
        "about where the occurrences are"
    )


def test_the_records_no_reading_opened_are_the_same_under_both_readings() -> None:
    """``census_unreached`` GRADED - it was asserted against nothing at all.

    IT IS LOAD-BEARING AND IT WAS UNGRADED. Two increments, a constructor
    argument, a repr field and one skip guard, and not one assertion: the
    reached census that every arm here divides by is ``census_records`` minus
    this number, so a reader that starts refusing records raises it, lowers the
    reached population, and every grade computed over what is left improves. The
    one number in this module that no reader can move was being reduced by one
    that any reader can.

    WHAT GRADES IT. This module's own reading of the tag grammar shares no
    function with the shipped walk, so the records IT cannot open are an
    independent verdict on the same bytes. The two are asserted equal - both in
    RECORDS and in the CENSUS those records carry.

    THE UNREACHED POPULATION IS NOT DISJOINT FROM THIS ITEM AND IS NOT CLAIMED
    TO BE. Those records belong to a save version pair whose payload grammar
    this project has not measured, and struct type words sit inside them in
    quantity. They are UNREACHABLE here and they are CS-G05's territory; an
    arithmetic refusal under the three-pair grammar is the signature of a
    DIFFERENT grammar rather than evidence of absent struct content.
    """
    sweep = _sweep_or_skip()

    unreached_records = sweep.head_unread + sweep.unwalked
    own_unreached_records = sweep.records - sweep.independent_walkable

    assert unreached_records == own_unreached_records, (
        f"the shipped walk left {unreached_records} records unopened and this module's "
        f"own reading left {own_unreached_records}. One of the two is refusing records "
        "the other can read, and because the reached census is what every arm here "
        "divides by, the refusing one shrinks the population rather than failing"
    )
    assert sweep.census_unreached == sweep.independent_unreached_census, (
        f"{sweep.census_unreached} struct type words sit inside records the shipped "
        f"walk never opened, against {sweep.independent_unreached_census} inside the "
        "records this module's own reading never opened. The two readings disagree "
        "about which bytes are out of reach, so the reached population - the "
        "denominator of every equality in this module - rests on one reader's opinion"
    )
    assert sweep.census_unreached < sweep.census_records, (
        "every struct type word in this library sits inside a record no reading can "
        "open, so the reached population is empty and every arm here is vacuous"
    )


def _subset_faults(censuses: Sequence[_SaveCensus]) -> int:
    """How many of the site equalities fail over one subset of the library.

    Args:
        censuses: The per-save counts making up the subset.

    Returns:
        How many of the four equalities the subset violates - zero when it
        satisfies all of them.
    """
    faults = 0
    faults += sum(c.sites_seen for c in censuses) != sum(c.independent_sites for c in censuses)
    faults += sum(c.census_unreached for c in censuses) != sum(
        c.independent_unreached_census for c in censuses
    )
    faults += sum(c.shipped_reached for c in censuses) != sum(
        c.independent_reached for c in censuses
    )
    faults += sum(c.site_disagreements for c in censuses) != 0
    return faults


def _subset_grades(sweep: _StructSweep) -> tuple[int, int, int]:
    """Grade every legitimate subset of this library, returning COUNTS ONLY.

    The censuses and the subsets built from them never reach the caller's frame,
    so an assertion over these three numbers cannot render a save-derived value
    under -l/--showlocals. Binding a scalar BESIDE the aggregate would not
    achieve that: the aggregate's own local would stay in the frame and render
    whatever the assertion said. The remedy is to stop binding it in the scope
    that asserts. See CLAUDE.md non-negotiables 11 and 12, and the guard in
    tests/test_locals_rendering.py that reported this exact site.

    Args:
        sweep: The completed sweep, whose per-save censuses this reads.

    Returns:
        How many non-empty subsets were graded, how many of them faulted, and
        how many save version pairs the library holds.
    """
    censuses = sweep.censuses
    subsets: list[tuple[_SaveCensus, ...]] = []
    subsets.extend(tuple(c for j, c in enumerate(censuses) if j != i) for i in range(len(censuses)))
    subsets.extend((c,) for c in censuses)
    subsets.extend(
        tuple(c for c in censuses if c.pair_id == pid)
        for pid in sorted({c.pair_id for c in censuses})
    )
    graded = sum(1 for subset in subsets if subset)
    faulted = sum(1 for subset in subsets if subset and _subset_faults(subset))
    pairs = len({c.pair_id for c in censuses})
    return graded, faulted, pairs


def test_the_site_equality_survives_every_legitimate_subset_of_this_library() -> None:
    """THE TEST THE PREVIOUS BOUND FAILED, RUN AGAINST THE NEW ONE.

    THE BOUND THIS MODULE USED TO CARRY WAS FITTED TO ONE MACHINE'S LIBRARY AT
    ONE INSTANT, and an adversary reddened it in BOTH DIRECTIONS with no shipped
    function touched: dropping the saves of one version pair took the figure to
    two and failed, dropping another pair's took it to zero and failed. Autosave
    rotation does that on its own and the operator plays the game while a
    session runs, so that bound was going to redden on its own schedule.

    A PROPERTY SURVIVES A SUBSET; A FITTED NUMBER DOES NOT. The equalities this
    slice adds are between two readings of the SAME bytes, so they hold over any
    set of saves whatsoever - and this asserts that over every subset the
    library's own shape offers: each save dropped in turn, each save alone, and
    each version pair alone. Nothing here is chosen because it passes.

    IT IS ASSERTED PER SUBSET, NOT OVER THE POOL, for the reason a pooled
    threshold is met by its strongest member - which is how this repo has
    already shipped a guard whose weakest member went unmeasured.
    """
    graded, faulted, pairs = _subset_grades(_sweep_or_skip())

    assert graded > 0, (
        "no non-empty subset of this library could be formed, so this arm grades "
        "nothing about how the equalities behave when the corpus changes"
    )
    assert pairs > 0, "the sweep recorded no save version pair, so the grouping is empty"
    assert faulted == 0, (
        f"{faulted} of {graded} legitimate subsets of this library violate an equality "
        "the whole library satisfies. An assertion that holds over the corpus and "
        "fails over part of it is fitted to the corpus, which is the defect that "
        "reddened this module's previous bound in both directions on nothing but "
        "autosave rotation"
    )


@dataclass
class _EarlyTerminator:
    """A shipped tag-list degradation applied IN PROCESS and never on disk.

    IT IS THE MUTANT THE THIRD REFUTATION MEASURED, in the class that every arm
    this module carried was blind to. Claiming a tag NAME is the payload
    terminator makes the shipped walk CLOSE EARLY: the record is still
    ACCEPTED, its later tags are never enumerated, and ``objects._walk_payload``
    behind ``read_properties`` closes at the very same byte because both consume
    this one verdict. So ``sites_seen`` and ``shipped_tags`` fall together, the
    cross-check between them stays green, ``head_unread``, ``partial_saves``,
    ``contested_pairs`` and ``census_unreached`` do not move, and the residue
    gets SMALLER - the check improving as the reader gets worse.

    IN PROCESS RATHER THAN ON DISK, and that is not a preference. The harness
    Bash tool's timeout KILLS rather than unwinds, so a ``finally`` that would
    restore a mutated file never runs and the mutation survives to poison every
    later measurement in the session.

    Attributes:
        original: The shipped reader, called for every read.
        armed: Whether the degradation is currently active.
        fired: How many reads it actually altered - a COUNT, because a mutant
            that never applied and one that survived produce identical output.
    """

    original: Callable[[bytes, int, int], tuple[str, int] | None]
    armed: bool = False
    fired: int = 0

    def __call__(self, body: bytes, at: int, end: int) -> tuple[str, int] | None:
        """Read one string, sometimes claiming it is the payload terminator.

        Args:
            body: The decompressed body.
            at: Where the length prefix starts.
            end: The first byte past this payload.

        Returns:
            What the shipped reader returned, or a terminator verdict in its
            place.
        """
        read = self.original(body, at, end)
        if read is None or not self.armed:
            return read
        if read[0] == objects._PAYLOAD_TERMINATOR or at % _CONTROL_MODULUS:  # noqa: SLF001
            return read
        self.fired += 1
        return (objects._PAYLOAD_TERMINATOR, read[1])  # noqa: SLF001


#: Which string offsets the control degrades. A BOUND ON HOW OFTEN THE MUTANT
#: FIRES, not a measurement of anything: any modulus exercises the same loss
#: class, and the arm asserts the firing count rather than assuming it.
_CONTROL_MODULUS: Final = 16


def _shipped_sites_of(body: bytes, record: objects.ObjectRecord, end: int) -> tuple[bool, int]:
    """The SHIPPED walk's struct site count for one record.

    Args:
        body: The decompressed body.
        record: The record to walk.
        end: The first byte past the record's payload.

    Returns:
        Whether the shipped walk enumerated the record, and how many of its
        tags carry the struct type word in their bytes.
    """
    start: int | None = record.body_offset
    if record.kind == objects.KIND_ACTOR:
        start = objects._skip_actor_head(body, record.body_offset, end)  # noqa: SLF001
    if start is None:
        return (False, 0)
    walked = test_decode_oracles._walk_with_the_shipped_reader(body, start, end)  # noqa: SLF001
    if walked is None:
        return (False, 0)
    at = start
    found = 0
    for _name, _word, value_at, size in walked:
        head = at
        at = value_at + size
        name_read = objects._payload_text(body, head, end)  # noqa: SLF001
        if name_read is not None and body.startswith(_STRUCT_WORD_LITERAL, name_read[1]):
            found += 1
    return (True, found)


def _independent_sites_of(
    body: bytes, own: independent_table.IndependentRecord
) -> tuple[bool, int]:
    """THIS MODULE'S OWN struct site count for one record.

    IT TAKES ITS WINDOW AND ITS KIND FROM THE SECOND READING OF THE BODY, NEVER
    FROM THE SHIPPED RECORD, and that is CS-829 round 5. This helper used to be
    handed an ``objects.ObjectRecord`` and read ``record.kind`` and
    ``record.body_offset`` off it - so the shipped record table decided where
    this reading started and which of the two starts it took, and a defect there
    moved the numerator and the denominator together. Nothing here now consults
    a value the shipped walk produced.

    THE ARGUMENT IS THE RECORD ITSELF AND NEVER A KEY INTO A LOOKUP. Resolving
    the shipped record against the second reading by ``body_offset`` would put
    the shipped offset back in the path by the back door: the record-table
    control below slides every start by one byte, and an offset-keyed lookup
    would simply miss. Callers pair the two readings POSITIONALLY, which
    :func:`_sweep_one_save` establishes is defined before it pairs anything.

    Args:
        body: The decompressed body.
        own: The second reading's own record for this position.

    Returns:
        Whether this module's own reading enumerated the record, and how many
        of its tags carry the struct type word in their bytes.
    """
    end = own.body_offset + own.body_length
    own_start = (
        _independent_actor_head(body, own.body_offset, end) if own.is_actor else own.body_offset
    )
    if own_start is None:
        return (False, 0)
    tags = _independent_tag_walk(body, own_start, end)
    if tags is None:
        return (False, 0)
    return (True, sum(1 for tag in tags if body.startswith(_STRUCT_WORD_LITERAL, tag[1])))


@dataclass
class _ControlCounts:
    """What the degradation control observed. COUNTS ONLY.

    Attributes:
        records: Records measured under both readings.
        pristine_sites: Struct sites the shipped walk reached undegraded.
        degraded_sites: The same under the degradation.
        independent_pristine: Struct sites this module's own reading found
            while the degradation was disarmed.
        independent_degraded: The same while it was armed - it must not move,
            which is the entire claim.
        pristine_reached: Records the shipped walk enumerated undegraded.
        degraded_reached: The same under the degradation.
        still_accepted: Records the shipped walk enumerated BOTH times.
        lost_in_still_accepted: Sites deleted from records that stayed
            accepted. THE LOSS CLASS every other arm here is blind to.
    """

    records: int = 0
    pristine_sites: int = 0
    degraded_sites: int = 0
    independent_pristine: int = 0
    independent_degraded: int = 0
    pristine_reached: int = 0
    degraded_reached: int = 0
    still_accepted: int = 0
    lost_in_still_accepted: int = 0


def _run_degradation_control(probe: _EarlyTerminator) -> _ControlCounts | None:
    """Measure every record twice, with the degradation disarmed and armed.

    EACH SAVE IS READ ONCE AND MEASURED TWICE. The operator plays this game
    while a session runs, so re-reading the library between the two passes
    would race a real autosave and report the difference as a defect.

    Args:
        probe: The installed degradation, armed and disarmed around each pass.

    Returns:
        The counts, or None when no save library is reachable.
    """
    saves = test_properties._library_save_paths()  # noqa: SLF001
    if not saves:
        return None
    counts = _ControlCounts()
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
            # INSIDE THE HANDLER BECAUSE `body` IS LIVE IN THIS FRAME. It used
            # to sit after it, and pytest renders the arguments of the first
            # and the deepest traceback frame with no opt-in flag, so a raise
            # out there put real save bytes into a transcript.
            mine = independent_table.independent_records(
                body, save_version=parsed.save_version, header_version=parsed.header_version
            )
        except (Exception, SystemExit):  # noqa: S112 - reporting it IS the leak
            continue
        if mine is None or len(mine) != len(table.records):
            continue
        for index, record in enumerate(table.records):
            end = record.body_offset + record.body_length
            own_record = mine[index]
            counts.records += 1
            probe.armed = False
            pristine_ok, pristine = _shipped_sites_of(body, record, end)
            _own_ok, own_pristine = _independent_sites_of(body, own_record)
            probe.armed = True
            degraded_ok, degraded = _shipped_sites_of(body, record, end)
            _own_degraded_ok, own_degraded = _independent_sites_of(body, own_record)
            probe.armed = False
            counts.pristine_sites += pristine
            counts.degraded_sites += degraded
            counts.independent_pristine += own_pristine
            counts.independent_degraded += own_degraded
            counts.pristine_reached += pristine_ok
            counts.degraded_reached += degraded_ok
            if pristine_ok and degraded_ok:
                counts.still_accepted += 1
                counts.lost_in_still_accepted += max(pristine - degraded, 0)
    return counts


def test_degrading_the_shipped_tag_reader_cannot_improve_this_modules_grade(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """THE ANTI-MONOTONE CONTROL - the check must get WORSE when the reader does.

    THE HEADLINE FINDING THAT KEPT CS-829 OPEN was that this module's grade
    IMPROVED as the shipped reader was degraded, three times, at three different
    functions, each time after a repair at the previous one. A green run is
    worth nothing until something asserts that direction, so this asserts it
    directly rather than arguing it.

    FOUR THINGS ARE ASSERTED, because a mutant that NEVER APPLIED and one that
    SURVIVED produce identical output: that the patch LANDED, that it FIRED with
    a count, that the pristine floor was measured BEFORE it was armed, and that
    the revert LANDED.

    WHAT THE DEGRADATION DOES AND WHY IT IS THE RIGHT ONE. See
    :class:`_EarlyTerminator`: it leaves records ACCEPTED and deletes tags from
    inside them, which is the one loss class every shape guard, every cross-check
    against ``read_properties`` and every census in this module is blind to,
    because both walks consume the one verdict it moves.

    NO EVIDENCE IS A SKIP AND THAT IS WHY THIS OPENS WITH THE SWEEP GUARD. This
    arm used to reach the library through :func:`_run_degradation_control`
    alone, which skips only when there is no library AT ALL - so on a library
    holding nothing but saves of a version pair this project does not parse it
    went RED at ``pristine_sites > 0`` while seventeen sibling arms SKIPPED on
    the identical corpus, for the identical reason, through
    :func:`_sweep_or_skip`. Measured on this machine: every single save of one
    of the four version pairs present reddens three arms that bypass that guard
    and none of the seventeen that use it. Autosave rotation alone reaches that
    state, so the guard is shared rather than re-derived here.

    THE THREE SKIPS BELOW ARE INGREDIENTS, NOT OUTCOMES. Each names a thing the
    control needs before its comparison means anything - a record to measure, a
    site to take away, and a record that stayed accepted while losing one - and
    none of them is derived from which corpora were observed failing, which
    would be the fitted-proof defect one level up.
    """
    _sweep_or_skip()

    original = objects._payload_text  # noqa: SLF001
    probe = _EarlyTerminator(original=original)
    monkeypatch.setattr(objects, "_payload_text", probe)
    assert objects._payload_text is probe, (  # noqa: SLF001
        "the degradation was not installed, so everything measured below is the "
        "pristine reader twice and this control proves nothing"
    )

    counts = _run_degradation_control(probe)

    # THE REVERT IS ASSERTED BEFORE ANY SKIP CAN LEAVE, and the ordering is the
    # repair rather than a tidy-up. Every guard below is a skip, and a skip taken
    # while the module is still patched would leave the fourth of the four
    # mutation assertions - that the revert LANDED - unrun on exactly the corpora
    # that take it. The fixture's own teardown would still restore the reader;
    # what would be lost is the check that says so.
    monkeypatch.undo()
    assert objects._payload_text is original, (  # noqa: SLF001
        "the shipped reader was NOT restored, so every later measurement in this "
        "process is taken against a degraded module"
    )

    if counts is None:
        pytest.skip("no save library on this machine - the control has nothing to degrade")
    if counts.records == 0:
        pytest.skip(
            "no save this run read parses into a record table, so the control "
            "measured no record at all and a degradation has nothing to cost"
        )

    assert probe.fired > 0, (
        "the degradation never altered a single read. A mutant that did not apply and "
        "one that survived produce the same output, so this run says nothing about "
        "whether the arms above can see reader loss. THIS STAYS AN ASSERTION rather "
        "than joining the skips below: its population is the reads taken while the "
        "patch was armed, and the guard above has already established that records "
        "were measured, so a zero here is the patch being inert and not an absent "
        "corpus"
    )

    if counts.pristine_sites == 0:
        pytest.skip(
            "the undegraded reader found no struct site in the records this run read, "
            "so there is nothing for the degradation to take away and a fall below "
            "would measure an absent population rather than a loss"
        )
    if counts.lost_in_still_accepted == 0:
        pytest.skip(
            f"the degradation fired {probe.fired} times and deleted no struct site "
            "from a record that stayed ACCEPTED, so the one loss class this control "
            "exists to exercise is absent from the saves this run read. Either every "
            "degraded record here was refused outright - which other arms catch - or "
            "this corpus is too small to hold one, and nothing measured in a single "
            "run separates those two"
        )

    assert counts.independent_degraded == counts.independent_pristine, (
        f"this module's own reading found {counts.independent_pristine} struct sites "
        f"undegraded and {counts.independent_degraded} with the shipped reader "
        "degraded. IT MUST NOT MOVE: it is the denominator precisely because it takes "
        "nothing from the shipped module but constants, and if a shipped patch can "
        "move it then the equality above is two views of one reader again"
    )

    assert counts.degraded_sites < counts.pristine_sites, (
        f"the degraded shipped walk reached {counts.degraded_sites} struct sites where "
        f"the pristine one reached {counts.pristine_sites}. The degradation did not "
        "cost the shipped reader anything measurable, so this control is not "
        "exercising the direction it claims to"
    )
    assert counts.degraded_sites < counts.independent_degraded, (
        f"the shipped walk lost sites under degradation and the equality still holds "
        f"at {counts.degraded_sites} against {counts.independent_degraded}. THE CHECK "
        "IS STILL ANTI-MONOTONE: the population shrank with the reader instead of the "
        "grade going red, which is the exact shape that refuted this item three times"
    )


# ---------------------------------------------------------------------------
# THE SECOND ANTI-MONOTONE CONTROL - the RECORD TABLE, not the tag reader
#
# WHAT THE FIRST CONTROL CANNOT SEE. ``_EarlyTerminator`` degrades
# ``objects._payload_text``, which the shipped walk calls and this module's own
# reading does not, so the two SEPARATE under it and the equality can go red.
# THE RECORD TABLE IS THE SUBSTRATE THEY STILL SHARE: ``_sweep_one_record``
# takes ``record.body_offset``, ``record.body_length`` and ``record.kind`` off
# the same table for the independent reading as for the shipped one, so a defect
# THERE moves the numerator and the denominator by the same amount and reddens
# nothing.
#
# THE DEGRADATION IS APPLIED TO THE TABLE'S OUTPUT AND NEVER BY MONKEYPATCH.
# The degraded records are built in memory from the pristine ones, so nothing
# shipped is patched, there is no revert to assert and none to miss, and the
# harness Bash timeout - which KILLS rather than unwinds - has nothing to leave
# behind. That is the safer half of a trade the first control cannot make,
# because a tag reader has no output object to rewrite.
# ---------------------------------------------------------------------------


#: How far a degraded payload's first byte moves. ONE BYTE, because the point is
#: a start BOTH readings take together, not a start so wrong that only a bounds
#: check is being exercised. It is a constant rather than a literal so no
#: comparison below reads as a magic number.
_TABLE_CONTROL_SHIFT: Final = 1


def _degrade_one_record(record: objects.ObjectRecord) -> objects.ObjectRecord | None:
    """Relabel an actor and move the payload start, holding the extent END.

    THIS IS THE DEGRADATION THE SESSION-40 ADVERSARY RECORDED. A record's KIND
    selects which of two payload starts a reading takes - an actor's head is
    skipped, a component's is not - and its extent says where the payload lies.
    Both readings in this module take all three fields off the same record, so
    moving them moves the two site totals TOGETHER: a large share of the
    corpus's struct sites left the population, every arm stayed green and the
    residue IMPROVED. The share is re-measured by the arm below rather than
    transcribed here, because a number written into prose is a number that rots.

    THE END IS HELD RATHER THAN SHIFTED. A start and a length that both move
    keep the payload the same width, which a bounds check could notice; holding
    the end makes the degraded extent a strictly narrower window inside the real
    one, so no reading here reaches a byte the pristine record did not own.

    ``with_payload`` does the shift rather than ``dataclasses.replace``, for the
    reason given at
    :meth:`clockspeed.save.objects.ObjectRecord.with_payload` - ADR 0007's write
    gate scans for the NAME ``replace``. The relabel builds the record directly,
    because no shipped method changes a record's kind and this module does not
    add one.

    Args:
        record: The pristine record. It is frozen and is not mutated.

    Returns:
        The degraded record, or None when the payload is too short to shift -
        which is NOT a degradation and must never be counted as one.
    """
    if record.body_length < _TABLE_CONTROL_SHIFT:
        return None
    offset = record.body_offset + _TABLE_CONTROL_SHIFT
    length = record.body_length - _TABLE_CONTROL_SHIFT
    if record.kind != objects.KIND_ACTOR:
        return record.with_payload(offset, length)
    return objects.ObjectRecord(
        kind=objects.KIND_COMPONENT,
        type_path=record.type_path,
        root_object=record.root_object,
        instance_name=record.instance_name,
        transform=record.transform,
        parent=record.parent,
        object_type=record.object_type,
        was_placed_in_level=record.was_placed_in_level,
        body_offset=offset,
        body_length=length,
    )


@dataclass
class _TableReading:
    """What both readings found over ONE presentation of a record population.

    COUNTS ONLY. Every field is an integer, so the generated repr is countable
    output on the same terms as :class:`_ControlCounts` - no offset, no extent,
    no version pair and no string reaches it.

    Attributes:
        shipped_sites: Struct sites the SHIPPED walk reached.
        independent_sites: Struct sites THIS MODULE'S own reading reached.
        shipped_reached: Records the shipped walk enumerated.
        independent_reached: Records this module's own reading enumerated.
    """

    shipped_sites: int = 0
    independent_sites: int = 0
    shipped_reached: int = 0
    independent_reached: int = 0

    def add(
        self, body: bytes, record: objects.ObjectRecord, own: independent_table.IndependentRecord
    ) -> None:
        """Fold one record in - the shipped reading from ``record``, ours from ``own``.

        THAT SEPARATION IS THE WHOLE MECHANISM, and it is what the arm below
        grades. ``record`` is the shipped table's and is the thing degraded;
        ``own`` is the second reading's record for the same position and is
        taken from the BODY, so the degradation cannot reach it. If the
        independent total still moves, the two are one reading wearing two
        names. Before CS-829 round 5 both arguments were the same object and it
        moved every time.

        Args:
            body: The decompressed body.
            record: The shipped record to measure, pristine or degraded.
            own: The second reading's record for this position. THE SAME OBJECT
                is passed on the pristine and the degraded pass - degrading it
                too would be degrading the thing under test.
        """
        end = record.body_offset + record.body_length
        shipped_ok, shipped = _shipped_sites_of(body, record, end)
        own_ok, own_sites = _independent_sites_of(body, own)
        self.shipped_sites += shipped
        self.independent_sites += own_sites
        self.shipped_reached += shipped_ok
        self.independent_reached += own_ok


@dataclass
class _TableControlCounts:
    """One version pair's record table, measured pristine and degraded.

    Attributes:
        records: Records of this pair measured under both presentations.
        altered: Records the degradation actually CHANGED - the FIRING COUNT. A
            mutant that never applied and one that survived produce identical
            output, so this is asserted rather than assumed.
        census: Struct type words the BYTES carry inside these records' PRISTINE
            extents. No reader can move it, which is what separates "this pair
            carries no struct content" from "the reading destroyed the evidence
            that it does".
        pristine: Both readings over the table as ``objects.parse_body`` built
            it.
        degraded: Both readings over the degraded table.
    """

    records: int = 0
    altered: int = 0
    census: int = 0
    pristine: _TableReading = field(default_factory=_TableReading)
    degraded: _TableReading = field(default_factory=_TableReading)


# ---------------------------------------------------------------------------
# WHICH CORPUS A PAIR-SHAPED CONTROL GRADED - CS-1054
#
# THE DEFECT THIS REPLACES, MEASURED RATHER THAN REASONED. Both pair-shaped
# controls below chose their graded pair as "the pair carrying the most records
# of those that parsed". That rule reads a MUTABLE directory: the operator plays
# while a session runs, so the totals move between two runs at the SAME commit.
# Measured on this machine at 27482eb - 28 saves over four version pairs, and
# dropping the single newest save flipped the graded pair from one carrying
# 80801 records to one carrying 77263. One autosave is 7739 records and the
# margin was 3538, so a single autosave landing mid-session changed which pair
# either control graded, with nothing in this repository moving at all. That is
# exactly the green-then-red with a clean tree this item was filed for.
#
# AND THE PAIR IT FLIPPED TO IS ONE THIS MODULE'S SECOND READING DOES NOT
# IMPLEMENT. `objects.COMPLETE_TYPE_NAME_PAIRS` declares the pairs whose
# payloads carry `objects.PAYLOAD_TAG_LEAD_BYTES` before the first tag and the
# recursive complete type name in place of the legacy tag shape. The shipped
# reader steps both - `objects.read_properties` reads those payloads and warns
# only `unmeasured-property-type` on them - while `_independent_tag_walk` here
# and `test_decode_oracles._walk_with_the_shipped_reader` both read the LEGACY
# grammar and nothing else, so every record of such a pair comes back unreached.
# A corpus that gained a save in a newer format is a corpus that CHANGED. It is
# not evidence destroyed, and reporting it as evidence destroyed was the red.
#
# THE PARTITION IS TAKEN FROM THE SHIPPED DECLARATION AND NEVER FROM THE
# OUTCOME, which is the discipline `_size_admits_a_tag_list` states at length: a
# population an equality is asserted over may not be defined by the outcome that
# equality reports. Selecting on "the pairs whose sites came back non-zero"
# would be exactly that, and it would swallow a real destroyed-evidence red the
# day one happened. `objects.uses_complete_type_name` is a declaration about a
# GRAMMAR, decided before a single byte is read.
#
# THE SET-ASIDE IS NOT SILENT AND CANNOT ROT. The arms assert that the pairs set
# aside yield NO site to this module's own reading. The day the second reading
# learns the complete-type-name grammar, that goes RED and says the set-aside is
# stale rather than leaving a pair quietly ungraded forever.
# ---------------------------------------------------------------------------


class _HasRecords(Protocol):
    """A per-pair tally that states how many records it folded.

    Attributes:
        records: Records folded into this pair's tally.
    """

    records: int


def _the_second_reading_implements(pair: tuple[int, int]) -> bool:
    """Whether THIS MODULE'S own tag reading implements that pair's grammar.

    KEY ORDER, THE TRAP THIS MODULE ALREADY NAMES ONCE.
    ``objects.COMPLETE_TYPE_NAME_PAIRS`` and ``objects.uses_complete_type_name``
    are keyed ``(header_version, save_version)`` while every pair key in this
    module is ``(save_version, header_version)``, matching :class:`_SaveShape`.
    The unpacking below is where the two meet and it is the only place they do.

    Args:
        pair: The version pair, ``(save_version, header_version)``.

    Returns:
        True when the pair's payloads carry the legacy tag grammar, which is
        the only one the readings in this module express.
    """
    save_version, header_version = pair
    return not objects.uses_complete_type_name(header_version, save_version)


def _grade_the_pair_this_module_can_read(
    by_pair: Mapping[tuple[int, int], _HasRecords],
) -> tuple[tuple[int, int] | None, int, int]:
    """Pick the graded pair from those whose grammar this module reads.

    Ties are broken by the pair itself, as before, so the choice cannot depend
    on the order the library happens to be walked in.

    Args:
        by_pair: Every version pair that folded, to its tally.

    Returns:
        The graded pair or None when the library holds no pair this module's
        own reading implements, then how many pairs were set aside for their
        declared grammar and how many records those pairs carried.
    """
    readable = {
        pair: tally for pair, tally in by_pair.items() if _the_second_reading_implements(pair)
    }
    set_aside = [tally for pair, tally in by_pair.items() if pair not in readable]
    graded = (
        max(readable, key=lambda candidate: (readable[candidate].records, candidate))
        if readable
        else None
    )
    return graded, len(set_aside), sum(tally.records for tally in set_aside)


def _corpus_line(
    *,
    saves: int,
    pairs: int,
    library_records: int,
    graded_records: int,
    set_aside_pairs: int,
    set_aside_records: int,
) -> str:
    """State WHICH corpus this run measured, as integers and nothing else.

    THE RED THIS ITEM REPAIRS WAS UNATTRIBUTABLE, and that is what this fixes
    rather than the equality. Two runs at the same commit disagreed and neither
    message said which corpus it had read, so there was no way to tell a defect
    from a library that had moved underneath the run.

    Every argument is a count. No path, no world name, no account directory and
    no version pair reaches this string.

    Args:
        saves: Saves this run folded.
        pairs: Version pairs those saves covered.
        library_records: Records over every one of those pairs.
        graded_records: Records of the graded pair.
        set_aside_pairs: Pairs set aside for their declared payload grammar.
        set_aside_records: Records those set-aside pairs carried.

    Returns:
        A one-line counts-only statement of the corpus.
    """
    return (
        f"corpus: {saves} saves, {pairs} version pairs, {library_records} records, "
        f"{graded_records} of them in the graded pair, with {set_aside_pairs} pairs and "
        f"{set_aside_records} records set aside as a declared complete-type-name grammar"
    )


#: The graded pair carries records and this module's reading found sites in it.
_POPULATION_GRADED: Final = "graded"

#: Every pair the library holds uses a payload grammar declared in
#: ``objects.COMPLETE_TYPE_NAME_PAIRS``, which this module's own reading does not
#: express. THE CORPUS CHANGED - nothing here was destroyed.
_POPULATION_GRAMMAR_SET_ASIDE: Final = "grammar-set-aside"

#: No save this run read folded into a record table at all.
_POPULATION_NO_RECORD: Final = "no-record"

#: The graded pair's records carry no struct type word in their BYTES, so there
#: is no site for any degradation to take away.
_POPULATION_NO_STRUCT_IN_BYTES: Final = "no-struct-in-bytes"

#: The bytes carry struct type words inside the graded pair's records and this
#: module's reading found none. THE ONLY ONE OF THE FIVE THAT IS A RED.
_POPULATION_EVIDENCE_DESTROYED: Final = "evidence-destroyed"


def _classify_graded_population(
    *, graded_records: int, set_aside_records: int, census: int, independent_sites: int
) -> str:
    """Say what a pair-shaped control's population IS, from four counts.

    A PURE FUNCTION OF FOUR INTEGERS, DELIBERATELY, so both directions of the
    distinction this item exists for are gradeable with no game, no save and no
    library - see
    :func:`test_a_changed_corpus_and_destroyed_evidence_are_not_the_same_verdict`.
    The live arms below then do nothing but route on what it returns.

    THE ORDER OF THE TESTS IS THE DISTINCTION. A corpus that gained a pair this
    module's reading does not express is asked about BEFORE a zero reading is
    called destroyed evidence, because the first explains the second and the
    second is a red.

    Args:
        graded_records: Records of the graded pair.
        set_aside_records: Records of the pairs set aside by declared grammar.
        census: Struct type words the BYTES carry in the graded pair's records.
        independent_sites: Sites this module's own reading found in them.

    Returns:
        One of the five ``_POPULATION_*`` constants above.
    """
    if graded_records == 0:
        return _POPULATION_GRAMMAR_SET_ASIDE if set_aside_records > 0 else _POPULATION_NO_RECORD
    if census == 0 and independent_sites == 0:
        return _POPULATION_NO_STRUCT_IN_BYTES
    if independent_sites == 0:
        return _POPULATION_EVIDENCE_DESTROYED
    return _POPULATION_GRADED


@dataclass(frozen=True)
class _TableControlResult:
    """The library reduced to the one version pair the control grades.

    THE PAIR ITSELF NEVER LEAVES :func:`_run_table_degradation_control`.
    :class:`_SaveShape` states the rule this follows: a version pair is reduced
    to counts before it reaches anything a repr can render - not because a build
    number is personal data, but because "only counts leave" stops holding the
    first time it is argued case by case.

    Attributes:
        pairs: How many distinct version pairs parsed into a record table.
        library_records: Records over every one of them, graded or not.
        chosen: The graded pair's counts.
        failures: Saves whose fold raised. A COUNT, never a type name and never
            a path - this control feeds the shipped readers misaligned offsets
            on purpose, so a raise there is a containment question first and a
            coverage question second. The arm asserts it at zero, which is what
            keeps the handler from becoming a silent drop.
        saves: Saves this run folded. Part of the corpus statement CS-1054
            added, and the count that makes two runs comparable at all.
        set_aside_pairs: Version pairs excluded from the choice because
            ``objects.COMPLETE_TYPE_NAME_PAIRS`` declares a payload grammar this
            module's own reading does not express.
        set_aside_records: Records those pairs carried.
        set_aside_sites: Struct sites this module's own reading found inside
            them. ASSERTED AT ZERO by the arm: the set-aside rests on a
            declaration, and a site found in a set-aside pair means the
            declaration no longer describes this reading.
    """

    pairs: int
    library_records: int
    chosen: _TableControlCounts
    failures: int = 0
    saves: int = 0
    set_aside_pairs: int = 0
    set_aside_records: int = 0
    set_aside_sites: int = 0


def _fold_table_control(
    body: bytes,
    record: objects.ObjectRecord,
    own: independent_table.IndependentRecord,
    into: _TableControlCounts,
) -> None:
    """Measure ONE record twice - as the table presents it, and degraded.

    The two measurements are taken from the SAME read of the SAME body, back to
    back, so nothing between them can differ.

    ``own`` IS NOT DEGRADED AND THAT IS DELIBERATE. It is the second reading's
    own record, read from the body rather than from the shipped table, and it is
    the thing whose invariance is under test. Degrading it too would be
    degrading the measuring instrument along with the thing measured, and the
    arm would then be unable to fail.

    Args:
        body: The decompressed body.
        record: The pristine SHIPPED record.
        own: The second reading's record for the same position.
        into: The pair's accumulator, mutated in place.
    """
    into.records += 1
    end = record.body_offset + record.body_length
    into.census += _census_hits(body, record.body_offset, end)
    into.pristine.add(body, record, own)
    degraded = _degrade_one_record(record)
    # COUNTED BY WHETHER THE RECORD ACTUALLY CHANGED, NOT BY WHETHER A
    # DEGRADATION WAS ATTEMPTED. `degraded is not None` was the old test and it
    # is exactly the defect a firing count exists to prevent: an adversary made
    # `_degrade_one_record` return its argument unchanged and this counter still
    # reported the full population, so a degradation that altered nothing was
    # indistinguishable from one that altered everything - which is the sentence
    # in the arm's own docstring, turned on itself.
    into.altered += degraded is not None and degraded != record
    # A record too short to shift is measured AGAIN AS ITSELF rather than
    # dropped: both passes have to range over the same population, or the
    # comparison below is between two different worlds.
    into.degraded.add(body, record if degraded is None else degraded, own)


def _run_table_degradation_control() -> _TableControlResult | None:
    """Read each save ONCE, measure every record TWICE, and grade one pair.

    EACH SAVE IS READ ONCE AND MEASURED TWICE, for the reason
    :func:`_run_degradation_control` states: the operator plays this game while
    a session runs, so re-reading the library between two passes races a real
    autosave and reports the difference as a defect. The degraded records are
    built from the pristine ones already in hand.

    THE GRADED PAIR IS DERIVED AND NOT TRANSCRIBED, on the same terms as this
    module's struct vocabulary. It is the pair carrying the MOST records of
    those that parsed AND whose payload grammar this module's own reading
    expresses, ties broken by the pair itself so the choice cannot depend on the
    order the library happens to be walked in. A pair written into this file
    would be a hand-maintained list that rots the first time the operator's
    library gains or loses a save.

    THE GRAMMAR CLAUSE IS CS-1054 AND IT IS NOT A NARROWING. The block above
    :class:`_TableControlResult` states what was measured: without it this
    control graded a pair whose payloads neither reading here can walk, and
    reported "no site" as evidence destroyed. What was set aside is set aside by
    a SHIPPED DECLARATION, and the arm asserts those pairs yield no site, so the
    exclusion cannot grow or go stale in silence.

    THE COUNTS ARE KEPT PER PAIR RATHER THAN POOLED, and that is what makes this
    a ONE-pair degradation without a second read of anything: a save carries
    exactly one pair, so a pair's tally is exactly what degrading that pair
    alone would have produced.

    KEY ORDER, A TRAP THIS REPO HAS ALREADY PAID FOR.
    ``objects.BODY_LAYOUT_BY_PAIR`` is keyed ``(header_version, save_version)``
    while the key here is ``(save_version, header_version)``, matching
    :class:`_SaveShape`. Neither is ever indexed with the other.

    Returns:
        The reduction, or None when NO save library is reachable at all - which
        is a different claim from "the library holds nothing this project
        parses", and that one comes back as a result whose counts are zero.
    """
    saves = test_properties._library_save_paths()  # noqa: SLF001
    if not saves:
        return None
    by_pair: dict[tuple[int, int], _TableControlCounts] = {}
    failures = 0
    folded = 0
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
            # PAIRED POSITIONALLY, AND ONLY WHERE PAIRING IS DEFINED - the same
            # refusal `_sweep_one_save` makes. A save the second reading
            # declines contributes NOTHING here rather than a half-measured
            # record, because this control's whole claim is a comparison
            # between two readings and one of them would be missing.
            #
            # IT IS INSIDE THE HANDLER BECAUSE `body` IS LIVE IN THIS FRAME.
            # It used to sit after it. pytest renders the arguments of the
            # first and the deepest traceback frame with no opt-in flag, so an
            # exception raised out there put real save bytes into a transcript
            # - measured by an adversary at 240 rendered characters carrying a
            # `/Game/...` asset path on 3 of this machine's 20 saves.
            mine = independent_table.independent_records(
                body, save_version=parsed.save_version, header_version=parsed.header_version
            )
        except (Exception, SystemExit):  # noqa: S112 - reporting it IS the leak
            continue
        if mine is None or len(mine) != len(table.records):
            continue
        folded += 1
        counts = by_pair.setdefault(
            (parsed.save_version, parsed.header_version), _TableControlCounts()
        )
        # THE FOLD IS WRAPPED TOO, AND THAT IS NOT BELT AND BRACES. This control
        # hands the shipped readers DELIBERATELY MISALIGNED offsets - that is
        # what `_degrade_one_record` is for - so it drives `objects._payload_text`
        # and `objects._skip_actor_head` through inputs no other caller gives
        # them, with `body` live in this frame. An uncaught raise there renders
        # save bytes into a traceback. A failure is COUNTED and asserted at zero
        # by the arm rather than swallowed, so the containment cannot quietly
        # become a silent drop.
        try:
            for index, record in enumerate(table.records):
                _fold_table_control(body, record, mine[index], counts)
        except (Exception, SystemExit):
            # Counted, not swallowed - the arm asserts this at zero.
            failures += 1
    graded, set_aside_pairs, set_aside_records = _grade_the_pair_this_module_can_read(by_pair)
    return _TableControlResult(
        pairs=len(by_pair),
        library_records=sum(counts.records for counts in by_pair.values()),
        chosen=_TableControlCounts() if graded is None else by_pair[graded],
        failures=failures,
        saves=folded,
        set_aside_pairs=set_aside_pairs,
        set_aside_records=set_aside_records,
        set_aside_sites=sum(
            counts.pristine.independent_sites
            for pair, counts in by_pair.items()
            if not _the_second_reading_implements(pair)
        ),
    )


def test_a_changed_corpus_and_destroyed_evidence_are_not_the_same_verdict() -> None:
    """CS-1054's distinction, graded in BOTH DIRECTIONS with no save at all.

    THE TWO ARMS BELOW IT ARE LIBRARY-BACKED AND CANNOT GRADE THIS. They see
    whatever the operator's library happens to hold at the second they run, and
    the whole finding is that the library moves: at 9f4fe6d the same arm passed
    inside a whole-suite run and failed on the same commit with a clean tree
    twenty-five minutes later, because one autosave had landed and changed which
    version pair was graded. A distinction that only one of those two corpora
    exercises is a distinction nothing checks.

    :func:`_classify_graded_population` is a pure function of four integers
    precisely so this arm can drive both directions, here, on a machine with no
    game installed.

    THE FIRST DIRECTION IS THE ONE THAT WAS WRONG. A corpus whose every pair
    carries a payload grammar declared in ``objects.COMPLETE_TYPE_NAME_PAIRS``
    yields no site to a reading that expresses only the legacy grammar, and the
    bytes still carry the words. That is a corpus that CHANGED and it MUST NOT
    be a red.

    THE SECOND DIRECTION IS THE ONE THAT MUST STILL FIRE. A graded pair this
    reading DOES express, whose bytes carry struct words and in which the
    reading finds none, is evidence destroyed, and nothing added here may turn
    that into a skip.

    THE NUMBERS ARE THE MEASURED ONES from this machine at 27482eb - 172810
    census words over 80801 records in the set-aside pair, 91450 over 77263 in
    the largest pair this module reads - so the fixture is the real shape rather
    than a convenient one. They are counts, and counts are the only thing about
    a save this file is allowed to carry.
    """
    changed = _classify_graded_population(
        graded_records=0, set_aside_records=80801, census=172810, independent_sites=0
    )
    assert changed == _POPULATION_GRAMMAR_SET_ASIDE, (
        f"a corpus holding only pairs whose grammar this module does not express was "
        f"classified {changed!r}. The library gaining a save in a newer format is the "
        "corpus CHANGING, and calling that destroyed evidence is the red CS-1054 was "
        "filed for"
    )

    destroyed = _classify_graded_population(
        graded_records=77263, set_aside_records=80801, census=91450, independent_sites=0
    )
    assert destroyed == _POPULATION_EVIDENCE_DESTROYED, (
        f"a graded pair whose bytes carry 91450 struct type words across 77263 records, "
        f"in which this module's own reading found none, was classified {destroyed!r}. "
        "THAT MUST STAY A RED. An empty population satisfies every equality below it, "
        "which is why this arm is an assertion and never a skip"
    )

    # THE TWO REMAINING CLASSIFICATIONS, so the routing above cannot quietly
    # collapse into two answers. A pair with no struct word in its BYTES is an
    # absent population and not a loss; a run that folded nothing has no
    # population at all.
    absent = _classify_graded_population(
        graded_records=77263, set_aside_records=0, census=0, independent_sites=0
    )
    assert absent == _POPULATION_NO_STRUCT_IN_BYTES, (
        f"a graded pair whose bytes carry no struct type word was classified {absent!r} "
        "rather than an absent population, so a corpus holding nothing to lose would be "
        "reported as having lost it"
    )
    empty = _classify_graded_population(
        graded_records=0, set_aside_records=0, census=0, independent_sites=0
    )
    assert empty == _POPULATION_NO_RECORD, (
        f"a run that folded no record at all was classified {empty!r}"
    )
    graded = _classify_graded_population(
        graded_records=77263, set_aside_records=80801, census=91450, independent_sites=30642
    )
    assert graded == _POPULATION_GRADED, (
        f"a graded pair this reading found 30642 sites in was classified {graded!r}, so "
        "the ordinary case does not reach the comparisons this control exists for"
    )


def test_the_table_control_takes_its_window_from_the_body_not_the_degraded_record() -> None:
    """THE SECOND ANTI-MONOTONE CONTROL - the substrate BOTH readings share.

    WHY A SECOND CONTROL IS NOT A DUPLICATE OF THE FIRST.
    :func:`test_degrading_the_shipped_tag_reader_cannot_improve_this_modules_grade`
    degrades a reader this module's own walk does not call, so the two readings
    separate under it. They still share the RECORD TABLE: ``_sweep_one_record``
    takes each record's payload start, its extent and its KIND off that one
    table for the independent reading as for the shipped one. A defect there
    moves both, and no arm in this module can currently see it.

    WHAT THE DEGRADATION DOES AND WHY IT IS THE RIGHT ONE. See
    :func:`_degrade_one_record`: for one version pair it relabels every actor a
    component and slides every payload start one byte with the extent END held.
    Relabelling changes which start a reading takes and sliding changes where it
    takes it from, which is the pair of fields a record table exists to state -
    so a table that states them wrongly is exactly the defect this arm is for.

    WHAT THIS ARM DOES NOT PROVE, MEASURED AND STATED RATHER THAN LEFT TO BE
    INFERRED. It does NOT prove the second reading is independent, and an
    earlier version of this docstring said it did. :func:`_fold_table_control`
    hands the SAME ``body`` and the SAME ``own`` object to both passes, so the
    equality below is ``sum f(x) == sum f(x)`` over identical arguments - an
    adversary instrumented it and measured every one of the call pairs
    receiving arguments identical by IDENTITY, and the equality held under six
    deliberately garbage readings including one that was the shipped record
    table verbatim. What it grades is the WIRING: that ``own`` is not derived
    from the degraded record. That is one bit, it is worth having, and it is
    not a proof about :mod:`tests.save.independent_table`. That module's
    independence is graded elsewhere and by something else - the DYNAMIC SEAM
    ARMS this item's follow-up CS-862 added to
    ``tests/save/test_independent_table.py``, which degrade the shipped record
    table at its SOURCE rather than at its output and redden for a wrapper.

    AND THAT IS WHY THIS ARM IS NAMED FOR THE WIRING RATHER THAN FOR THE GRADE.
    A reader of a GREEN run sees the NAME and nothing else - no docstring, no
    assertion message - so a name claiming more than the arm grades is a claim
    made in the one place the narrowing above cannot reach. It used to be
    ``test_degrading_the_record_table_cannot_improve_this_modules_grade``.

    THE GRADED PAIR IS DERIVED, NEVER TRANSCRIBED, on the same terms as this
    module's struct vocabulary: it is the version pair carrying the most records
    of those that parsed. :func:`_run_table_degradation_control` states how, and
    the pair never leaves that function - only counts do.

    THREE GUARDS, EACH ALREADY PAID FOR IN THIS REPO. The FIRING COUNT is
    asserted, because a mutant that never applied and one that survived produce
    identical output. The population is asserted NON-EMPTY before anything
    ranges over it, because an empty population satisfies every equality - a
    finding born in this very item. And the empty case is split the way
    :func:`_sweep_or_skip` splits it: a zero the BYTE CENSUS contradicts is
    evidence destroyed and stays an assertion, while a zero the bytes agree with
    is a skip naming the ingredient it lacks.

    AND A FOURTH, WHICH IS CS-1054. The corpus is a directory the operator
    writes to while a session runs, so this arm now STATES which corpus it
    measured - saves, pairs, records, graded records, records set aside - in
    every message it can emit, and its graded pair is chosen only from pairs
    whose payload grammar this module's own reading expresses. Without that it
    graded whichever pair the last autosave made largest and reported a grammar
    it cannot walk as evidence destroyed. Measured at 9f4fe6d: green inside a
    whole-suite run, red on the same commit with a clean tree twenty-five
    minutes later, nothing in the repository moved. The set-aside is itself
    asserted at zero sites, and the changed-versus-destroyed distinction is
    graded synthetically in both directions by
    :func:`test_a_changed_corpus_and_destroyed_evidence_are_not_the_same_verdict`,
    because a library-backed arm can only ever see the one corpus it ran on.
    """
    _sweep_or_skip()

    result = _run_table_degradation_control()
    if result is None:
        pytest.skip("no save library on this machine - there is no record table to degrade")
    chosen = result.chosen
    corpus = _corpus_line(
        saves=result.saves,
        pairs=result.pairs,
        library_records=result.library_records,
        graded_records=chosen.records,
        set_aside_pairs=result.set_aside_pairs,
        set_aside_records=result.set_aside_records,
    )
    control_failures = result.failures
    assert control_failures == 0, (
        f"{control_failures} saves raised inside the fold. This control feeds the shipped "
        "readers misaligned offsets deliberately, so a raise there is contained rather "
        "than rendered - but it is asserted here so containment cannot become a silent "
        f"drop, which is the shape that has refuted this item repeatedly. {corpus}"
    )

    # THE SET-ASIDE IS ASSERTED, NOT ASSUMED - CS-1054. The pairs excluded from
    # the choice are excluded on a shipped DECLARATION about their grammar, and
    # a declaration nothing checks is a comment. A site found by this module's
    # own reading inside one of them means the reading now expresses a grammar
    # the exclusion still says it does not, and the pair belongs back in the
    # graded population. A RED HERE IS GOOD NEWS.
    set_aside_sites = result.set_aside_sites
    assert set_aside_sites == 0, (
        f"this module's own reading found {set_aside_sites} struct sites inside the "
        f"{result.set_aside_records} records of the {result.set_aside_pairs} version "
        "pairs set aside for carrying a declared complete-type-name payload grammar. "
        "The set-aside says this reading cannot express those payloads and it just "
        f"did, so the exclusion is STALE and those pairs must be graded. {corpus}"
    )

    census = chosen.census
    independent_pristine = chosen.pristine.independent_sites
    population = _classify_graded_population(
        graded_records=chosen.records,
        set_aside_records=result.set_aside_records,
        census=census,
        independent_sites=independent_pristine,
    )
    if population == _POPULATION_GRAMMAR_SET_ASIDE:
        pytest.skip(
            "every version pair this run read carries a payload grammar declared in "
            "objects.COMPLETE_TYPE_NAME_PAIRS, which this module's own tag reading does "
            "not express, so there is no pair it could grade. THE CORPUS CHANGED AND "
            f"NOTHING WAS DESTROYED - that is the distinction CS-1054 exists for. {corpus}"
        )
    if population == _POPULATION_NO_RECORD:
        pytest.skip(
            "no save this run read parses into a record table, so the control measured "
            f"no record at all and a degraded table has nothing to cost. {corpus}"
        )

    records = chosen.records
    altered = chosen.altered
    assert altered > 0, (
        f"the degradation changed none of the {records} records of the graded pair. A "
        "mutant that did not apply and one that survived produce the same output, so "
        "this run says nothing about whether a defect in the record table is visible "
        "here. THIS STAYS AN ASSERTION rather than joining the skips: its population is "
        "the graded pair's records, which the guard above has already established is "
        "non-empty, so a zero here is the degradation being inert and not an absent "
        f"corpus. {corpus}"
    )

    if population == _POPULATION_NO_STRUCT_IN_BYTES:
        pytest.skip(
            "the graded version pair's records carry no struct type word in their BYTES, "
            "so this pair holds no site a degraded table could take away and every "
            f"comparison over it would be measuring an absent population. {corpus}"
        )
    # THE ORIGINAL ASSERTION, UNCHANGED IN SHAPE AND IN STRENGTH. Everything
    # CS-1054 added above is ROUTING: the two skips it introduces are the
    # classifications this comparison never distinguished, and reaching this
    # line means the population is one this module's own reading expresses and
    # the bytes say carries struct content. A zero here is still destroyed
    # evidence and is still a red.
    assert independent_pristine > 0, (
        f"the byte census found {census} struct type words inside the graded pair's "
        f"{records} records while this module's own reading found no site in them at "
        "all. THAT IS EVIDENCE DESTROYED AND NOT AN ABSENT CORPUS - the line "
        "`_sweep_or_skip` draws - so it stays an assertion, because an empty population "
        "satisfies every equality below. The graded pair is one this reading DOES "
        f"express, so a changed corpus is not the explanation. {corpus}"
    )

    independent_degraded = chosen.degraded.independent_sites
    shipped_pristine = chosen.pristine.shipped_sites
    shipped_degraded = chosen.degraded.shipped_sites
    assert independent_degraded == independent_pristine, (
        f"graded {records} of {result.library_records} records over {result.pairs} "
        f"version pairs, degrading {altered} of them. This module's own reading found "
        f"{independent_pristine} struct sites over the pristine record table and "
        f"{independent_degraded} over the degraded one, opening "
        f"{chosen.pristine.independent_reached} records and then "
        f"{chosen.degraded.independent_reached}. The shipped walk read "
        f"{shipped_pristine} sites and then {shipped_degraded}. THE INDEPENDENT TOTAL "
        "MUST NOT MOVE. It is the denominator every equality in this module stands on, "
        "and it is meant to owe the shipped module nothing but constants - but it takes "
        "its start, its extent and its kind off the very record table degraded here, so "
        "a defect in that table moves the numerator and the denominator together and no "
        "grade can go red"
    )

    assert shipped_degraded < shipped_pristine, (
        f"the shipped walk reached {shipped_degraded} struct sites over the degraded "
        f"record table where it reached {shipped_pristine} over the pristine one. The "
        "degradation did not cost the shipped reader anything measurable, so this "
        "control is not exercising the direction it claims to"
    )
    assert shipped_degraded < independent_degraded, (
        f"the shipped walk lost sites under a degraded record table and the equality "
        f"still holds at {shipped_degraded} against {independent_degraded}. THE CHECK "
        "IS STILL ANTI-MONOTONE: the population shrank with the table instead of the "
        "grade going red, which is the exact shape that refuted this item repeatedly"
    )


# ---------------------------------------------------------------------------
# THE THIRD ANTI-MONOTONE CONTROL - the shared SCALAR CONSTANTS, not a reader
#
# WHAT THE FIRST TWO CANNOT SEE. ``_EarlyTerminator`` degrades a shipped READER
# this module's own reading does not call, and the table control degrades the
# record table's OUTPUT. Both separate the two readings, which is why either can
# go red. THE SHARED SCALARS SEPARATE NOTHING: both tag walks read the same
# ``objects`` module attribute at call time, so a defect there moves the
# numerator and the denominator by the same amount and every equality in this
# module stays green while the population shrinks underneath it.
#
# MEASURED ON THIS TREE BEFORE THIS CONTROL EXISTED, with the ceiling made
# stricter for ONE version pair's bodies: at 12 the module showed 1 failing arm;
# at 0 - a reader that refuses everything 12 refuses AND MORE - it showed NONE
# and exited 0. The check got BETTER as the reader got strictly WORSE. That is
# the fifth location of the signature that has refuted CS-829 five times.
#
# THE PLANT IS THE CONSTANT ITSELF AND NOT A FUNCTION, which is the whole point:
# a control that patched a reader would be the first control again. It is
# applied IN PROCESS and never on disk, for the reason :class:`_EarlyTerminator`
# states - the harness Bash timeout KILLS rather than unwinds, so a ``finally``
# that would restore a mutated file never runs.
# ---------------------------------------------------------------------------


#: How strict the shared tag ceiling is made while the control is armed. A BOUND
#: ON WHAT THE PLANT REFUSES, not a measurement of anything: any ceiling below
#: the corpus's own observed maximum exercises the same loss class, and the arm
#: asserts what the plant actually COST rather than assuming it. It is above one
#: so a refusal is a payload losing its tail rather than every payload dying at
#: its first tag, which would be a kill and not a degradation.
_CEILING_CONTROL_TAGS: Final = 8


@dataclass
class _CeilingCounts:
    """One version pair's tally under the shared-ceiling plant. COUNTS ONLY.

    Attributes:
        records: Records measured under both readings.
        shipped_pristine: Struct sites the shipped walk reached undegraded.
        shipped_degraded: The same under the stricter shared ceiling.
        independent_pristine: Struct sites this module's own reading found with
            the ceiling pristine.
        independent_degraded: The same with it planted. IT MUST NOT MOVE, and
            that it DID is the whole of what this control was built to catch.
        reached_pristine: Records the shipped walk enumerated undegraded.
        reached_degraded: The same under the plant.
        own_reached_pristine: Records this module's own reading enumerated
            undegraded.
        own_reached_degraded: The same under the plant.
    """

    records: int = 0
    shipped_pristine: int = 0
    shipped_degraded: int = 0
    independent_pristine: int = 0
    independent_degraded: int = 0
    reached_pristine: int = 0
    reached_degraded: int = 0
    own_reached_pristine: int = 0
    own_reached_degraded: int = 0


@dataclass(frozen=True, repr=False)
class _CeilingResult:
    """The reduction over the library. COUNTS ONLY, and no pair reaches a repr.

    Attributes:
        pairs: How many version pairs parsed into a tally.
        library_records: Records measured across every pair.
        chosen: The graded pair's tally - see :func:`_run_ceiling_control` for
            why grading ONE pair is what makes this plant pair-shaped.
        planted_reads: How many measurements ran while the plant was armed. A
            COUNT, because a plant that never applied and one that was survived
            produce identical output.
        saves: Saves this run folded - part of CS-1054's corpus statement.
        set_aside_pairs: Pairs excluded from the choice by the declared
            complete-type-name grammar. See the block above
            :class:`_TableControlResult`.
        set_aside_records: Records those pairs carried.
        set_aside_sites: Struct sites this module's own reading found in them,
            asserted at zero on the same terms as the table control.
    """

    pairs: int
    library_records: int
    chosen: _CeilingCounts
    planted_reads: int
    saves: int = 0
    set_aside_pairs: int = 0
    set_aside_records: int = 0
    set_aside_sites: int = 0


def _install_ceiling(value: int) -> None:
    """Install a tag ceiling on the shipped module, in process.

    ``setattr`` RATHER THAN AN ASSIGNMENT, and the reason is not style. The
    shipped constant is ``Final``, so a direct assignment is a type error - and
    that check is a real one worth keeping, because temporarily violating the
    constant is exactly what this control does and it should not be something a
    module can do by accident. The control asserts the revert landed.

    Args:
        value: The ceiling to install.
    """
    setattr(objects, "_MAX_TAGS_PER_PAYLOAD", value)  # noqa: B010 - see the docstring


def _fold_ceiling_control(
    body: bytes,
    record: objects.ObjectRecord,
    own: independent_table.IndependentRecord,
    counts: _CeilingCounts,
    *,
    degraded: bool,
) -> None:
    """Measure one record under whichever ceiling is currently installed.

    Args:
        body: The decompressed body.
        record: The shipped record, for the shipped walk's window.
        own: The second reading's own record for this position, paired
            POSITIONALLY and never resolved by offset, for the reason
            :func:`_independent_sites_of` states.
        counts: The pair's tally, updated in place.
        degraded: Which half of the comparison this call is filling in.
    """
    end = record.body_offset + record.body_length
    shipped_ok, shipped = _shipped_sites_of(body, record, end)
    own_ok, mine = _independent_sites_of(body, own)
    if degraded:
        counts.shipped_degraded += shipped
        counts.independent_degraded += mine
        counts.reached_degraded += shipped_ok
        counts.own_reached_degraded += own_ok
    else:
        counts.records += 1
        counts.shipped_pristine += shipped
        counts.independent_pristine += mine
        counts.reached_pristine += shipped_ok
        counts.own_reached_pristine += own_ok


def _run_ceiling_control(original: int) -> _CeilingResult | None:
    """Read each save ONCE, measure every record TWICE, and grade ONE pair.

    EACH SAVE IS READ ONCE AND MEASURED TWICE, for the reason
    :func:`_run_degradation_control` states: the operator plays this game while
    a session runs, so re-reading the library between the two passes races a
    real autosave and reports the difference as a defect.

    THE PLANT IS PAIR-SHAPED BY THE REDUCTION AND NOT BY THE ARMING, which is
    the construction :func:`_run_table_degradation_control` uses and for the
    same reason: a save carries exactly one version pair, so a pair's tally is
    exactly what planting that pair alone would have produced. A plant armed for
    the whole library instead is caught by the shape guards - ``partial_saves``,
    ``contested_pairs`` - and walking past those guards is what makes a
    pair-shaped plant the one worth grading.

    THE GRADED PAIR IS DERIVED AND NOT TRANSCRIBED: the pair carrying the most
    records of those that parsed AND whose payload grammar this module's own
    reading expresses, ties broken by the pair itself so the choice cannot
    depend on the order the library happens to be walked in.

    THE GRAMMAR CLAUSE IS CS-1054, AND THIS CONTROL IS WHERE THE DEFECT WAS
    WORSE THAN A RED. On the library measured at 27482eb the pair carrying the
    most records was one neither reading here can walk, so
    ``chosen.shipped_pristine`` was zero and this arm SKIPPED - the third
    anti-monotone control went vacuous and said so in a reason line nobody was
    reading. The table control at least went red about it.

    Args:
        original: The shipped ceiling, restored around each planted measurement.

    Returns:
        The reduction, or None when NO save library is reachable at all - which
        is a different claim from "the library holds nothing this project
        parses", and that one comes back as a result whose counts are zero.
    """
    saves = test_properties._library_save_paths()  # noqa: SLF001
    if not saves:
        return None
    by_pair: dict[tuple[int, int], _CeilingCounts] = {}
    planted_reads = 0
    folded = 0
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
            # INSIDE THE HANDLER BECAUSE `body` IS LIVE IN THIS FRAME. pytest
            # renders the arguments of the first and the deepest traceback frame
            # with no opt-in flag, so a raise out there puts real save bytes into
            # a transcript - measured at 240 rendered characters carrying an
            # asset path on 3 of this machine's 20 saves.
            mine = independent_table.independent_records(
                body, save_version=parsed.save_version, header_version=parsed.header_version
            )
        except (Exception, SystemExit):  # noqa: S112 - reporting it IS the leak
            continue
        if mine is None or len(mine) != len(table.records):
            continue
        folded += 1
        counts = by_pair.setdefault((parsed.save_version, parsed.header_version), _CeilingCounts())
        for index, record in enumerate(table.records):
            _install_ceiling(original)
            _fold_ceiling_control(body, record, mine[index], counts, degraded=False)
            _install_ceiling(_CEILING_CONTROL_TAGS)
            planted_reads += 1
            _fold_ceiling_control(body, record, mine[index], counts, degraded=True)
            _install_ceiling(original)
    graded, set_aside_pairs, set_aside_records = _grade_the_pair_this_module_can_read(by_pair)
    return _CeilingResult(
        pairs=len(by_pair),
        library_records=sum(tally.records for tally in by_pair.values()),
        chosen=_CeilingCounts() if graded is None else by_pair[graded],
        planted_reads=planted_reads,
        saves=folded,
        set_aside_pairs=set_aside_pairs,
        set_aside_records=set_aside_records,
        set_aside_sites=sum(
            tally.independent_pristine
            for pair, tally in by_pair.items()
            if not _the_second_reading_implements(pair)
        ),
    )


def test_a_stricter_shared_ceiling_cannot_improve_this_modules_grade(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """THE THIRD ANTI-MONOTONE CONTROL - a shared CONSTANT, not a reader.

    WHAT IT ADDS OVER THE FIRST TWO. Both of those degrade something ONE of the
    two readings uses, so the two separate and an equality can go red. This one
    degrades something they SHARE, which is the case where separation has to be
    BUILT rather than observed - and it was not built, so this module's grade
    IMPROVED as the reader got strictly worse.

    THE ASSERTION THAT CARRIES IT is that this module's own site total does not
    move under the plant. That total is the denominator precisely because it
    takes nothing from the shipped module a defect can travel through, and a
    shared ceiling was exactly such a thing.

    THE PLANT IS ASSERTED TO HAVE LANDED, TO HAVE FIRED AND TO HAVE BEEN
    REVERTED, because a plant that never applied and one that was survived
    produce identical output.

    NO EVIDENCE IS A SKIP, so this opens with the shared sweep guard for the
    reason
    :func:`test_degrading_the_shipped_tag_reader_cannot_improve_this_modules_grade`
    records: an arm reaching the library past that guard goes RED on a corpus
    where seventeen of its siblings SKIP, and autosave rotation alone reaches
    that corpus.
    """
    _sweep_or_skip()

    original = objects._MAX_TAGS_PER_PAYLOAD  # noqa: SLF001
    # REGISTERS THE UNDO AND CHANGES NOTHING. The control toggles the attribute
    # itself around each measurement, so what monkeypatch buys here is the
    # guaranteed restore on every exit path, including one taken by a raise
    # inside the fold.
    monkeypatch.setattr(objects, "_MAX_TAGS_PER_PAYLOAD", original)

    result = _run_ceiling_control(original)

    # THE REVERT IS ASSERTED BEFORE ANY SKIP CAN LEAVE, and the ordering is the
    # repair rather than a tidy-up: a skip taken while the module is still
    # planted would leave the revert unchecked on exactly the corpora that skip.
    monkeypatch.undo()
    assert original == objects._MAX_TAGS_PER_PAYLOAD, (  # noqa: SLF001
        "the shared tag ceiling was NOT restored, so every later measurement in this "
        "process is taken against a degraded module"
    )

    if result is None:
        pytest.skip("no save library on this machine - the control has nothing to plant")
    corpus = _corpus_line(
        saves=result.saves,
        pairs=result.pairs,
        library_records=result.library_records,
        graded_records=result.chosen.records,
        set_aside_pairs=result.set_aside_pairs,
        set_aside_records=result.set_aside_records,
    )
    # THE SET-ASIDE IS ASSERTED HERE TOO - see the table control's copy of this
    # guard and the block above `_TableControlResult` for why an exclusion that
    # nothing checks is a comment.
    ceiling_set_aside_sites = result.set_aside_sites
    assert ceiling_set_aside_sites == 0, (
        f"this module's own reading found {ceiling_set_aside_sites} struct sites inside "
        f"the {result.set_aside_records} records of the {result.set_aside_pairs} version "
        "pairs set aside for carrying a declared complete-type-name payload grammar, so "
        f"the exclusion is STALE and those pairs must be graded. {corpus}"
    )
    if result.chosen.records == 0 and result.set_aside_records > 0:
        pytest.skip(
            "every version pair this run read carries a payload grammar declared in "
            "objects.COMPLETE_TYPE_NAME_PAIRS, which this module's own tag reading does "
            "not express, so there is no pair it could plant against. THE CORPUS "
            f"CHANGED AND NOTHING WAS DESTROYED. {corpus}"
        )
    if result.chosen.records == 0:
        pytest.skip(
            "no save this run read parses into a record table this module's own reading "
            "can pair, so the control measured no record at all and a stricter ceiling "
            f"has nothing to cost. {corpus}"
        )

    assert result.planted_reads > 0, (
        "the plant was never armed for a single measurement. A plant that did not apply "
        "and one that was survived produce the same output, so this run says nothing "
        "about whether a shared constant can move this module's grade. THIS STAYS AN "
        "ASSERTION rather than joining the skips below: the guard above has already "
        "established that records were measured"
    )

    if result.chosen.shipped_pristine == 0:
        pytest.skip(
            "the shipped walk found no struct site in the graded pair's records, so "
            "there is nothing for a stricter ceiling to take away and a fall below "
            f"would measure an absent population rather than a loss. {corpus}"
        )
    if result.chosen.shipped_degraded == result.chosen.shipped_pristine:
        pytest.skip(
            f"a ceiling of {_CEILING_CONTROL_TAGS} refused no payload the graded pair "
            "carries, so this corpus holds no record long enough to exercise the loss "
            "class this control exists for. That is an absent population and not a "
            "reader that held up under it"
        )

    assert result.chosen.independent_degraded == result.chosen.independent_pristine, (
        f"this module's own reading found {result.chosen.independent_pristine} struct "
        f"sites under the shipped ceiling and {result.chosen.independent_degraded} under "
        "a stricter one. IT MUST NOT MOVE. A constant both tag walks read is a defect "
        "route the equalities in this module cannot show, because it moves the numerator "
        "and the denominator together - which is how a reader refusing EVERYTHING scores "
        "better here than one refusing a little"
    )
    assert result.chosen.own_reached_degraded == result.chosen.own_reached_pristine, (
        f"this module's own reading opened {result.chosen.own_reached_pristine} records "
        f"under the shipped ceiling and {result.chosen.own_reached_degraded} under a "
        "stricter one. The reached POPULATION moved with a shipped constant, so every "
        "grade computed over what is left is computed over a population the shipped "
        "module chose"
    )

    assert result.chosen.shipped_degraded < result.chosen.shipped_pristine, (
        f"the planted ceiling left the shipped walk at {result.chosen.shipped_degraded} "
        f"struct sites where it reached {result.chosen.shipped_pristine} pristine. The "
        "plant cost the shipped reader nothing measurable, so this control is not "
        "exercising the direction it claims to"
    )
    assert result.chosen.shipped_degraded < result.chosen.independent_degraded, (
        f"the shipped walk lost sites under a stricter shared ceiling and the equality "
        f"still holds at {result.chosen.shipped_degraded} against "
        f"{result.chosen.independent_degraded}. THE CHECK IS STILL ANTI-MONOTONE: the "
        "population shrank with the constant instead of the grade going red"
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
    decoded = sum(sweep.compatible_decoded.values())
    refused = sum(sweep.compatible_refused.values())

    assert compatible > 0, (
        "no site in this corpus has a size a tag list could take, so this equality "
        "ranges over an empty population and would pass on any decoder at all"
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


def test_the_corpus_still_classifies_a_native_site_by_arithmetic_alone() -> None:
    """THE ONLY POSITIVE EVIDENCE THIS MODULE HAS, SPLIT OUT SO IT CAN SKIP.

    A SIZE-EXCLUDED SITE IS THE ONE CLASSIFICATION NO READER MADE. Its declared
    width falls between a bare terminator and one minimal tag plus a terminator,
    which is a window no tag list can occupy whatever any decoder does - so a
    word holding one is native on arithmetic rather than on a refusal, and that
    is what keeps the equality above from resting entirely on the reader.

    THE WINDOW IS NARROW AND A SMALL CORPUS CAN MISS IT ENTIRELY. This used to
    be asserted beside the equality, where an empty result reddened and took the
    refusal ceiling, the wordless check and the per-word split down with it. A
    corpus carrying no site in that window has told this module nothing; it has
    not degraded. So it skips here, and the equality above keeps running.
    """
    sweep = _sweep_or_skip()

    excluded = sum(sweep.size_excluded.values())
    compatible = sum(sweep.size_compatible.values())
    if excluded == 0:
        pytest.skip(
            f"not one of {compatible} struct sites in the saves this run read declares "
            "a width inside the size-excluded window, so nothing here is classified "
            "native on arithmetic. The window is a few bytes wide and a corpus can "
            "carry no instance of it, which is an absent population rather than a "
            "classification that has stopped working"
        )
    # NO RESTATEMENT OF THE GUARD ABOVE AS AN ASSERTION. ``assert excluded > 0``
    # here could not fail, and a check that cannot fail is not a check - it is
    # the defect this module retracted the exact-close comparison for. What
    # follows is a claim the guard does not imply: that the pooled total and the
    # per-word classification account for the same sites.
    proven = len(sweep.words_proven_native_by_size)
    assert proven > 0, (
        f"{excluded} sites are size-excluded and not one struct word is credited with "
        "carrying them, so the per-word classification and the pooled total disagree "
        "about the same sites"
    )


def test_the_size_compatible_refusals_rest_on_the_reader_alone() -> None:
    """THE NARROWING, RECORDED AS THE ADVERSARY MEASURED IT.

    Nearly every native site in this corpus is native on ARITHMETIC: its
    declared width is one no tag list can take, so no reader's opinion is
    involved. A small residue is not. Those sites have a width a tag list could
    have taken, and the only thing saying they are not one is this module's own
    reader refusing them.

    THAT IS THE HONEST LIMIT OF THIS SLICE, and it is far narrower than the
    limit first shipped - which was the whole native class.

    AN EMPTY RESIDUE IS NOT A STALE RECORD - IT IS NO EVIDENCE, and the two used
    to be the same line here. "The day the residue empties, this record is
    stale" is true of the WHOLE library and false of a part of it: measured on
    this machine, four of the twenty saves carry no size-compatible refusal at
    all on their own, and one whole version pair carries none either. Autosave
    rotation produces exactly that, so the old assertion reddened on the
    operator playing the game. The emptiness now SKIPS and says which of the two
    readings it cannot distinguish.

    NO FIGURE IS WRITTEN HERE. The operator plays this game and the corpus moves
    on the next autosave; the counts are derived on every run.
    """
    sweep = _sweep_or_skip()

    refused = sum(sweep.compatible_refused.values())
    if refused == 0:
        pytest.skip(
            "every size-compatible site in the saves this run read decodes, so no "
            "residue formed and there is nothing here resting on the reader's refusal. "
            "Either the residue is gone from the corpus - which would make this record "
            "stale - or the saves this run read do not happen to carry one, and a "
            "single sweep cannot tell those apart"
        )

    # THE MAPPING IS NEVER BOUND TO A LOCAL, and that is a privacy fix on a
    # channel an assertion-expression audit structurally cannot see.
    # ``unexplained_refusals`` is keyed by struct words read out of the
    # operator's save. Bound to a local, a failure anywhere in this function
    # renders it under ``-l`` / ``--showlocals`` - a routine debugging flag
    # rather than a configured one - and tests/conftest.py's redactor covers
    # home paths and the account name only, so a struct word passes straight
    # through it (non-negotiables 11 and 12). Reading the property twice keeps
    # the mapping a temporary that no frame renderer reaches.
    unexplained_words = len(sweep.unexplained_refusals)
    unexplained_sites = sum(sweep.unexplained_refusals.values())
    # THIS ONE STAYS AN ASSERTION AND THE ATTEMPT TO MAKE IT A SKIP IS RECORDED
    # AS REFUTED. A word lands in the residue for two reasons - a decoder that
    # stopped reading it, or size-excluded siblings that live in saves this run
    # did not read - and MEASURED, THE TWO CORPORA ARE STRUCTURALLY IDENTICAL:
    # reading one version pair of this machine's library alone moves a word that
    # is overwhelmingly native by arithmetic across the whole library into the
    # residue, producing exactly the count a refused reading word produces. So
    # every condition that would skip the one also skips the other. Built and
    # measured: with the excess converted to a skip, an in-process mutant
    # refusing the WEAKEST reading word outright at
    # ``objects._decode_struct_interior`` - the function BOTH readings route
    # through, so no cross-check separates them - left the whole module at zero
    # failures. This assertion is the only arm that catches it. Converting it
    # would trade a red on a legitimate subset for a green on a real defect,
    # which is the wrong direction of the same disease. The bound remains FITTED
    # and reddens on some legitimate subsets; de-fitting it needs per-word
    # evidence independent of which saves are present, which is CS-829's open
    # problem rather than this arm's.
    assert unexplained_words <= _UNEXPLAINED_WORD_CEILING, (
        f"{unexplained_words} struct words hold a size-compatible refusal AND carry no "
        "size-excluded site at all, so nothing but this module's reader says they are "
        "native. A word refused entirely by a broken decoder lands here, which is what "
        "makes this bound worth having rather than a formality. IT ALSO REDDENS ON A "
        "CORPUS TOO SMALL TO CARRY A WORD'S SIZE-EXCLUDED SIBLINGS, and nothing "
        "computed in one sweep tells the two apart - read the note on the ceiling "
        "before treating a red here as a reading failure"
    )
    # AN EQUALITY AGAINST THIS BOUND USED TO STAND HERE AND IS REMOVED. It
    # asserted that the observed figure sat exactly ON the ceiling, so that no
    # slack remained - which reads well and was fitted to one machine's library
    # at one instant. An adversary measured it reddening on LEGITIMATE CORPUS
    # CHANGE in both directions with no shipped function touched: dropping the
    # saves of one version pair takes the count to two and fails, dropping
    # another pair's takes it to zero and fails. That is autosave rotation and
    # world deletion, which happen on their own. Its message compounded the
    # error by calling any red "the residue narrowing", when the first of those
    # two is the residue WIDENING - a bound that misdiagnoses its own condition
    # is worse than a loose one. It was also orthogonal to the defect it was
    # sold as covering: it sat at exactly one under both of the population
    # mutants above.
    #
    # WHAT REPLACES IT IS NOT A TIGHTER NUMBER. The per-word protection now
    # comes from the arms that grade the population itself - the byte
    # classification and the independent reading - which no corpus change can
    # satisfy by accident. THE RESIDUAL HOLE IS STATED RATHER THAN CLOSED: at
    # this bound one struct word carrying no size-excluded evidence can still
    # be refused outright without reddening here.
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

    total = sweep.field_hits + sweep.field_misses
    if total == 0:
        pytest.skip(
            "no interior decoded to a single tag name in the saves this run read, so "
            "there is no name for the shipped usmap to be joined against and both "
            "counts below range over an empty population"
        )
    assert sweep.field_hits > 0, (
        "not one decoded interior name is a field the shipped usmap declares for that "
        "struct, so the second oracle agrees with nothing and this test grades nothing. "
        "THE POPULATION IS NON-EMPTY BY THE GUARD ABOVE, so this is the two sources "
        "disagreeing rather than an absent corpus"
    )
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

    stepped = sum(sweep.interior_tags.get(word) or 0 for word in sweep.words_decoded_throughout)
    valued = sum(sweep.interior_values.get(word) or 0 for word in sweep.words_decoded_throughout)
    if stepped == 0:
        pytest.skip(
            "no interior tag was stepped over at all in the saves this run read, so "
            "there is no nested population here and both counts below are zero for the "
            "absence of one rather than for a gap in a reading"
        )
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
def _uniform_width_struct_words() -> tuple[int, int, int, int] | None:
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
        struct word, how many of those words this module reads at top level,
        and how many tags the tag reader and the bytes disagree about. None
        when no library or no usmap is reachable.
    """
    sweep = _sweep_the_library()
    saves = test_properties._library_save_paths()  # noqa: SLF001
    if sweep is None or not saves:
        return None

    seen = 0
    named = 0
    readable = 0
    disagreed = 0
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
            one = _uniform_containers_of(body, record, sweep)
            seen += one[0]
            named += one[1]
            readable += one[2]
            disagreed += one[3]
    return (seen, named, readable, disagreed)


def _uniform_containers_of(
    body: bytes, record: objects.ObjectRecord, sweep: _StructSweep
) -> tuple[int, int, int, int]:
    """Classify one record's uniform-width containers by their inner struct form.

    Args:
        body: The decompressed body.
        record: The record to walk.
        sweep: The library sweep, for the set of words read at top level.

    Returns:
        Uniform-width containers seen, how many named an inner struct word, how
        many of those words are read at top level, and how many tags the tag
        reader and the bytes disagree about.
    """
    end = record.body_offset + record.body_length
    start: int | None = record.body_offset
    if record.kind == objects.KIND_ACTOR:
        start = objects._skip_actor_head(body, record.body_offset, end)  # noqa: SLF001
    walked = (
        None
        if start is None
        else test_decode_oracles._walk_with_the_shipped_reader(body, start, end)  # noqa: SLF001
    )
    if start is None or walked is None:
        return (0, 0, 0, 0)
    seen = named = readable = disagreed = 0
    at = start
    for _name, word, value_at, size in walked:
        head = at
        at = value_at + size
        name_read = objects._payload_text(body, head, end)  # noqa: SLF001
        # THE CONTAINER IS CHOSEN BY ITS BYTES - the third site of the shape
        # repaired in ``_fold_one_tag``, and the second one that repair did not
        # sweep. Selecting on the tag reader's reported word deletes a
        # mislabelled container from this population before anything counts it,
        # and the arm below asserts a count is ZERO - so every deletion makes it
        # easier to satisfy.
        bytes_word = None if name_read is None else _container_word_at(body, name_read[1])
        if bytes_word is None or name_read is None:
            continue
        disagreed += bytes_word != word
        step = _uniform_container_at(body, bytes_word, head, value_at, size, end)
        if step is None:
            continue
        seen += 1
        if step.struct_word is None:
            continue
        named += 1
        readable += step.struct_word in sweep.words_decoded_throughout
    return (seen, named, readable, disagreed)


#: The container type words as they stand IN THE BYTES, length prefix and all.
#: DERIVED from the shipped set through the same fixture encoder the synthetic
#: cases build their payloads with, so no container word is transcribed here.
_CONTAINER_WORD_LITERALS: Final[Mapping[bytes, str]] = MappingProxyType(
    {_fstring(word): word for word in objects.CONTAINER_TYPE_WORDS}
)


def _container_word_at(body: bytes, at: int) -> str | None:
    """Which container type word the BYTES carry at this offset, if any.

    Args:
        body: The decompressed body.
        at: Where a tag's type word begins.

    Returns:
        The container word, or None when the bytes carry no container word
        here - which includes every non-container tag.
    """
    for literal, word in _CONTAINER_WORD_LITERALS.items():
        if body.startswith(literal, at):
            return word
    return None


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

    A RED IS PROGRESS AND AN EMPTY POPULATION IS NEITHER. If the readable count
    rises, the interior grammar has reached the partition and CS-843's first arm
    is live - that is the assertion at the end. If the uniform-width population
    is EMPTY, the undiscriminated shape is either gone from the corpus or absent
    from the saves this run happened to read, and no single sweep separates
    those: that is a SKIP naming the missing ingredient, not a red. It used to
    be a red, and it fired on every single save of one of this machine's four
    version pairs while seventeen sibling arms skipped on the identical corpus
    through :func:`_sweep_or_skip` - which this now opens with, for the same
    reason they do.
    """
    _sweep_or_skip()

    counts = _uniform_width_struct_words()
    if counts is None:
        pytest.skip("no save library or no shipped usmap on this machine")
    seen, named, readable, disagreed = counts

    # ASSERTED BEFORE THE INGREDIENT SKIPS, because it is decidable on any
    # corpus that walks a record at all: it compares two readings of the same
    # tag and does not need a uniform-width container to exist.
    assert disagreed == 0, (
        f"{disagreed} tags were called a container by the tag reader where the bytes at "
        "the type-word offset carry a different container word, or the other way round. "
        "The population below is taken from the BYTES for exactly that reason - before "
        "it was, a mislabelled container left this join silently and the zero asserted "
        "at the end got easier to satisfy for the loss"
    )

    if seen == 0:
        pytest.skip(
            "no container in the saves this run read is bounded by the derived uniform "
            "width, so the undiscriminated shape CS-843 is about has no instance here "
            "and there is nothing for this join to measure the reach of. Either the "
            "corpus has stopped carrying one, which would make this record stale, or "
            "this run read too few saves to hold one"
        )
    if named == 0:
        pytest.skip(
            f"{seen} containers were bounded by the derived width and not one names an "
            "inner struct word, so this join has nothing to join. That is an absent "
            "population rather than a disagreement between the two readings"
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
        name_unread: Sampled sites whose tag NAME would not re-read at the
            offset the walk reports the tag starting at.
        word_unread: Sampled sites whose struct word would not read.
    """

    sites: int = 0
    declared: int = 0
    early: int = 0
    late: int = 0
    seen: int = 0
    name_unread: int = 0
    word_unread: int = 0


def _sample_one_record(body: bytes, record: objects.ObjectRecord, state: _EndSample) -> None:
    """Sample the struct sites in one record, folding into the running state.

    THE SITE IS CHOSEN BY THE BYTES, NOT BY THE TAG READER'S WORD, and that is
    a SIBLING OF THE DEFECT REPAIRED IN :func:`_fold_one_tag` rather than a new
    finding. That repair was applied at one site; this function kept selecting
    on ``objects._read_tag_header``'s reported type word, so a site the reader
    mislabelled left this sample silently and the arm measuring how strongly the
    grammar pins an end graded whatever survived - the same
    grade-improves-as-the-reader-worsens shape, one function over. The
    classification here is now the same length-prefixed byte comparison the fold
    uses, and the two readers this function still needs are COUNTED rather than
    ending in a bare ``continue``.

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
    for _name, _word, value_at, size in walked:
        head = at
        at = value_at + size
        if size > _END_SAMPLE_MAX_SIZE:
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
        name_read = objects._payload_text(body, head, payload_end)  # noqa: SLF001
        if name_read is None:
            state.name_unread += 1
            continue
        if not body.startswith(_STRUCT_WORD_LITERAL, name_read[1]):
            continue
        state.seen += 1
        if state.seen % _END_SAMPLE_STRIDE or state.sites >= _END_SAMPLE_SITES:
            continue
        struct_word = objects._struct_word_of_tag(body, name_read[1], payload_end)  # noqa: SLF001
        if struct_word is None:
            state.word_unread += 1
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
def _end_freedom_sample() -> tuple[int, int, int, int, int, int] | None:
    """How many ends close at a sampled struct site, besides the declared one.

    Returns:
        Sites sampled, how many of them close at their DECLARED end, ends that
        closed BEFORE it, ends that closed AFTER it, and the two reader
        refusals the sampler now counts rather than skipping - a tag name that
        would not re-read and a struct word that would not read. None when no
        library is reachable.
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
    return (
        state.sites,
        state.declared,
        state.early,
        state.late,
        state.name_unread,
        state.word_unread,
    )


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

    A SAMPLE THAT EXAMINED NOTHING IS A SKIP. The two counts below are a
    STRENGTH measurement, and a strength measured over no site is not a weak
    result - it is no result. This used to assert the sample non-empty, which
    reddened on every single save of one of this machine's four version pairs
    while seventeen sibling arms skipped on the identical corpus through
    :func:`_sweep_or_skip`; that guard is now shared rather than re-derived.
    """
    _sweep_or_skip()

    sample = _end_freedom_sample()
    if sample is None:
        pytest.skip("no save library on this machine - end freedom is not gradeable here")
    sites, declared, early, late, name_unread, word_unread = sample

    # THE SAMPLER'S OWN REFUSALS, COUNTED RATHER THAN SKIPPED. Both used to end
    # in a bare ``continue``, so a reader failing here deleted the site from the
    # sample and the arm below graded whatever was left - the sibling of the
    # defect repaired in the sweep, at the one function the repair did not reach.
    assert name_unread == 0, (
        f"{name_unread} sampled struct sites have a tag NAME that will not re-read at "
        "the offset the walk reports the tag starting at, so this sampler and the walk "
        "disagree about where a tag begins"
    )
    assert word_unread == 0, (
        f"{word_unread} sampled struct sites carry a struct word that will not read, so "
        "the site left this sample without being measured and the counts below describe "
        "a smaller and easier sample"
    )

    if sites == 0:
        pytest.skip(
            "the sample examined no struct site in the saves this run read, so it "
            "grades nothing. Either the corpus carries none narrow enough to sample, "
            "or the stride skipped every one - and both are an absent population "
            "rather than a grammar that has stopped pinning the end"
        )
    if declared == 0:
        pytest.skip(
            f"not one of {sites} sampled sites closes at its DECLARED end. The sample "
            "is drawn by size arithmetic rather than by the decoder, so a run of native "
            "structs lands here legitimately - and the two counts below would then be "
            "measuring the absence of a reading rather than its strength"
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
        _run_degradation_control.__name__: reach_guard.REACH_READS_THE_LIBRARY,
        _run_table_degradation_control.__name__: reach_guard.REACH_READS_THE_LIBRARY,
        _run_ceiling_control.__name__: reach_guard.REACH_READS_THE_LIBRARY,
    }
)

#: Touches a primitive WITHOUT consuming a real save path, name to why. Empty:
#: every synthetic case in this module builds its bytes in the process and no
#: path-holding read is stubbed anywhere here.
_EXEMPT_LIBRARY_REACH: Final[Mapping[str, str]] = MappingProxyType({})
