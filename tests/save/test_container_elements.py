"""CS-830 - decoding an ELEMENT off the three container type words.

WHAT WAS MISSING. ``ArrayProperty``, ``SetProperty`` and ``MapProperty`` reached
``clockspeed/save/objects.py`` only as CURSOR widths: the tag-extra count was
measured, so the walk stepped over a container to the right place, and nothing
inside was read. That made ``ArrayProperty`` the second-largest opaque region in
the module's own accounting while being the region a building's inventory sits
in. This module grades the element framing that now ships.

THE POPULATION IS THE TAG, NOT THE SUCCESSFUL DECODE, for the reason CS-831
gives one item over: a population drawn from the decoder's own successes lets
the decoder pick its own denominator, so a framing that lost its place would
SHRINK the population rather than fail the equality. Every container TAG the
shipped walk steps over enters the count, and the acceptance is an EQUALITY
between that total and the decodes - not a floor. THE FLOOR IS THE DEFECT THIS
ITEM WAS REWRITTEN FOR: its first wording was closeable by three single
decodes while every array holding an inventory stayed unmeasured.

WHAT AN ELEMENT DECODE CLAIMS, AND WHAT IT REFUSES TO CLAIM. It claims the
container's element COUNT, its element type word or words, and the EXTENT of
every element - where each one starts and how many bytes it spans - and it
claims those only when the elements so bounded consume the tag's declared size
EXACTLY. It claims a VALUE only for an element whose own type word this module
already decodes at top level. A ``StructProperty`` element comes back as a
bounded, typed region carrying no value at all, because the struct INTERIOR is
CS-829 and reading it here would be this project publishing a guess. That seam
is asserted below rather than promised.

THE THREE ELEMENT SHAPES ARE ORDERED BY STRENGTH AND THE ORDER IS LOAD-BEARING.
A SELF-DELIMITING reading - a stated width, a length-prefixed string, or a
nested tag list closed by the terminator name - is the element's OWN grammar
saying where it ends, and it is falsifiable: get it wrong and the region does
not close. A UNIFORM width is DERIVED by dividing the element region by the
element count, and a SOLVED width is derived by requiring the region to close
and admitting the answer only when exactly one width does. The derived pair are
weaker, so they are tried only where the self-delimiting reading does not close.
MEASURED, and this is why the order is not a preference: taking them as
alternatives rather than as a fallback made both close on a large majority of
the struct arrays, because a container holding ONE element is divided by one and
any width closes it. That population is counted separately below rather than
described, so what rests on the weaker reading is visible instead of averaged in.

WHAT THE EQUALITY CATCHES AND WHAT IT CANNOT. It catches an element framing that
stops closing on any part of the population - a wrong lead-field count, a wrong
element width where the word's own grammar states one, a wrong inner-tag shape -
because the decode is refused rather than approximated when the region does not
close. It does NOT catch a record the walk skipped: the tag total and the decode
total are both taken inside the same sweep off the same walk, so a payload that
never reaches the walk moves neither. That is the same limit CS-831 records for
its own partition, and it is written here rather than left for a reader to
discover.

AND IT DOES NOT CATCH A WRONG PARTITION OF A REGION THAT CLOSES - CS-830 WAS
MERGED AND THEN REFUTED ON EXACTLY THIS, AND THE ITEM IS NARROWED RATHER THAN
RESTATED. Where an element word has no grammar of its own, the region is divided
by the DECLARED count and admitted because the division came out even. Any other
partition summing to the span closes identically, the element total is unchanged
because the walk computes it from the same declared count, and neither equality
above can see the difference. Measured here rather than reasoned about, by
running a deliberately wrong partition through both:
``test_a_provably_wrong_partition_survives_every_library_backed_equality``.

SO THE EVIDENCE IS GRADED PER CONTAINER WORD AND NO LONGER POOLED. The pooled
majority assertion this module used to make was true of the whole population and
false of one word inside it, which is the shape of error pooling produces. What
each word rests on is now asserted against that word's own instances, and a word
resting entirely on a derived reading is named in a shipped table rather than
averaged away. The undiscriminated remainder is filed as its own item; this
module records the limit and does not claim to have closed it.

COUNTS ONLY, on the terms ``tests/save/test_decode_oracles.py`` sets out. An
element's bytes, a property name and a save path are world content under
non-negotiables 11 and 12. Every call that touches a real path or a real body
sits inside a handler that reduces whatever comes out of it to an exception type
NAME, and no field of the sweep below can hold anything but an integer. The
synthetic cases are free to hold strings, because a synthetic fixture is nobody's
save.

NEEDS NO GAME FOR MOST OF WHAT IS HERE. Every case but the library sweep runs on
hand-authored fixtures, so the framing is graded on a machine with no install and
no save library. The library cases skip there.
"""

from __future__ import annotations

import struct
from collections.abc import Mapping
from dataclasses import dataclass, field
from functools import lru_cache
from types import MappingProxyType
from typing import Final

import pytest

from clockspeed.save import chunks, header, objects
from tests.save import reach_guard, test_decode_oracles, test_properties

# ---------------------------------------------------------------------------
# Synthetic fixtures
#
# THE TAG GRAMMAR IS IMPORTED RATHER THAN TRANSCRIBED, for the reason
# ``tests/save/test_reference_resolution.py`` gives: a second copy of that
# grammar is a second place to get it subtly wrong, and two copies of one belief
# are not two pieces of evidence (CLAUDE.md section 5). What this module adds is
# the ELEMENT grammar, which no other fixture builds.
# ---------------------------------------------------------------------------

#: A string that appears in no shipped constant, planted in a fixture so a repr
#: containing it can only have got it from the fixture.
_LEAK_MARKER: Final = "ClockspeedContainerLeakMarker"

#: The synthetic containers' element counts, named so an assertion says which
#: count it is checking rather than carrying a bare literal.
_ARRAY_ELEMENTS: Final = 3
_SET_ELEMENTS: Final = 2
_MAP_ELEMENTS: Final = 2

#: A struct element width the fixture uses for a set, chosen so the region
#: divides by the count and the division is not the identity - a set of ONE
#: element divides by one whatever the width is, which grades nothing.
_SET_ELEMENT_BYTES: Final = 6

#: How many halves a map entry carries. The map is the only container whose
#: entry is a pair, and that asymmetry is what the shipped table records.
_MAP_ENTRY_HALVES: Final = 2

#: An inner type word this module has no element grammar for, planted so
#: "flagged and skipped" is exercised rather than described.
_UNMODELLED_INNER_WORD: Final = "SyntheticUnmodelledProperty"

#: A save version pair the fixture record is built against.
_SYNTHETIC_SAVE_VERSION: Final = 52
_SYNTHETIC_HEADER_VERSION: Final = 14

#: The fewest slots a region needs before an ALTERNATIVE partition of it exists.
#: One element admits exactly one partition, so mutating it is a no-op that would
#: inflate a landed-mutation count with cases grading nothing.
_SLOTS_WITH_AN_ALTERNATIVE_PARTITION: Final = 2


def _array_value(inner: str, elements: bytes, count: int) -> bytes:
    """An ArrayProperty value - an element count followed by its elements.

    Args:
        inner: The inner type word, which rides in the tag rather than here.
        elements: The encoded elements.
        count: How many elements to declare.

    Returns:
        The value bytes.
    """
    del inner
    return struct.pack("<i", count) + elements


def _container_tag(name: str, word: str, extra_words: tuple[str, ...], value: bytes) -> bytes:
    """One container tag, its extra type words included.

    Args:
        name: The property name.
        word: The container type word.
        extra_words: The element type words the tag carries.
        value: The encoded value.

    Returns:
        The whole tag.
    """
    extra = b"".join(test_properties._fstring(text) for text in extra_words)  # noqa: SLF001
    return test_properties._tag_head(name, word, len(value), extra) + value  # noqa: SLF001


def _set_value(elements: bytes, count: int) -> bytes:
    """A SetProperty value - a lead field, an element count, then the elements.

    Args:
        elements: The encoded elements.
        count: How many elements to declare.

    Returns:
        The value bytes.
    """
    return struct.pack("<i", 0) + struct.pack("<i", count) + elements


def _map_value(entries: bytes, count: int) -> bytes:
    """A MapProperty value - a lead field, an entry count, then the entries.

    Args:
        entries: The encoded key and value halves.
        count: How many entries to declare.

    Returns:
        The value bytes.
    """
    return struct.pack("<i", 0) + struct.pack("<i", count) + entries


def _read_payload_of(tags: bytes) -> objects.PropertyResult:
    """Decode a COMPONENT payload built from hand-written tags.

    A component payload opens directly with its tags, which keeps the fixture
    free of the actor head these cases have no use for.

    Args:
        tags: The encoded tags, terminator excluded.

    Returns:
        The result.
    """
    payload = tags + test_properties._fstring("None")  # noqa: SLF001
    body = test_properties._synthetic_body(payload)  # noqa: SLF001
    record = test_properties._synthetic_record(payload, actor=False)  # noqa: SLF001
    schema = test_properties._SYNTHETIC_SCHEMA  # noqa: SLF001
    return objects.read_properties(body, record, test_properties._synthetic_map(schema))  # noqa: SLF001


# ---------------------------------------------------------------------------
# What the module claims about the three words, and about the words next to them
# ---------------------------------------------------------------------------


def test_the_three_container_words_are_measured_and_no_longer_recorded_as_opaque() -> None:
    """The promotion, held against the module's own two-way classification.

    A word decoded here while its region entry still says the module claims
    nothing about it would leave the module asserting both, which is the
    contradiction ``tests/save/test_properties.py`` and
    ``tests/save/test_byte_order_status.py`` each grade one intersection of.

    NEEDS NO SAVE LIBRARY - it is a claim about the repo.
    """
    words = objects.CONTAINER_TYPE_WORDS
    assert words, "objects.CONTAINER_TYPE_WORDS is empty, so this test grades nothing"

    undecoded = sorted(words - objects.MEASURED_VALUE_TYPES)
    assert not undecoded, (
        f"{undecoded} are container words this module decodes an element off and "
        "MEASURED_VALUE_TYPES does not name them, so the shipped walk counts a "
        "refused decode as unmodelled content rather than as a walk that has lost "
        "its place"
    )

    still_opaque = sorted(words & frozenset(objects.UNMEASURED_PAYLOAD_REGIONS))
    assert not still_opaque, (
        f"{still_opaque} are decoded AND recorded in UNMEASURED_PAYLOAD_REGIONS as "
        "regions this module claims nothing about. Both cannot be true"
    )

    still_declined = sorted(words & frozenset(objects.DECLINED_VALUE_READINGS))
    assert not still_declined, (
        f"{still_declined} carry a decline under the width rule and are decoded, so "
        "the module records the reading as both settled and refused"
    )


def test_the_container_candidate_set_is_derived_and_every_member_is_owned() -> None:
    """CS-830's second acceptance arm - the transcription is guarded, not trusted.

    THE THREE WORDS ARE NAMED RATHER THAN DERIVED, DELIBERATELY. No shipped
    table equals that triple: every candidate over-includes ``StructProperty``,
    whose interior is CS-829, or ``TextProperty``, which is CS-832. So the
    naming cannot be replaced by a derivation, and what a derivation CAN do is
    catch a fourth word arriving in the shipped tables with no item behind it.

    THE CANDIDATE SET IS COMPUTED FROM FOUR TABLES THIS MODULE DOES NOT OWN -
    the tag-extra widths, the measured set, the container set and the declines -
    so a word entering any one of them without an owner reddens here.

    NEEDS NO SAVE LIBRARY - it is a claim about the repo.
    """
    candidates = objects.container_candidate_words()
    assert candidates, "the candidate derivation is empty, so this test grades nothing"

    owners = objects.CONTAINER_ADJACENT_OWNERS
    assert owners, (
        "objects.CONTAINER_ADJACENT_OWNERS is empty. It is what records which item "
        "owns a candidate this module does not decode, and emptying it is the "
        "cheapest way to satisfy the assertion below"
    )

    unowned = sorted(candidates - objects.CONTAINER_TYPE_WORDS - frozenset(owners))
    assert not unowned, (
        f"{unowned} are derived from the shipped tables as words carrying a "
        "container-shaped interior, are not among the three CS-830 decodes, and no "
        "item is recorded as owning them. Decode the word here, or record the item "
        "that owns it in CONTAINER_ADJACENT_OWNERS - do not widen the triple"
    )

    for word, item in sorted(owners.items()):
        assert item.startswith("CS-"), (
            f"the owner recorded for {word} is {item!r}, which is not an item id. An "
            "owner that is not an item id is a sentence rather than a route"
        )


def test_the_candidate_set_strictly_over_includes_the_three_it_cannot_derive() -> None:
    """The control on the arm above - a derivation that EQUALLED the triple would be one.

    If the candidate set ever came to equal ``CONTAINER_TYPE_WORDS``, the arm
    above would be comparing a set with itself and the naming would have become
    derivable. That is a real possibility rather than a hypothetical: it happens
    the moment CS-829 and CS-832 close and drop their entries. This says so out
    loud instead of letting the guard go quietly vacuous.

    NEEDS NO SAVE LIBRARY.
    """
    candidates = objects.container_candidate_words()

    assert candidates > objects.CONTAINER_TYPE_WORDS, (
        "the derived candidate set no longer STRICTLY includes the three container "
        "words. Either a word left the shipped tables or the triple widened; if the "
        "adjacent items have closed, this module's naming is now derivable and the "
        "arm above has become a set compared with itself"
    )


def test_the_element_shape_words_are_pinned_and_distinct() -> None:
    """The shape words are shipped data a later slice reads, so exchanging two must red.

    They record WHICH reading bounded a container's elements, and the whole
    point of recording that is that the derived readings are weaker than the
    self-delimiting one. Two shape words that collapse to one string make that
    distinction unreadable while every count stays right.

    NEEDS NO SAVE LIBRARY.
    """
    shapes = (
        objects.ELEMENT_SHAPE_SELF_DELIMITING,
        objects.ELEMENT_SHAPE_UNIFORM_WIDTH,
        objects.ELEMENT_SHAPE_SOLVED_WIDTH,
    )

    assert len(frozenset(shapes)) == len(shapes), f"the element shape words collide: {shapes}"
    assert frozenset(shapes) == objects.ELEMENT_SHAPES, (
        "objects.ELEMENT_SHAPES does not hold exactly the three shape words, so a "
        "shape can be produced that the shipped set does not admit"
    )


# ---------------------------------------------------------------------------
# The element framing, on fixtures
# ---------------------------------------------------------------------------


def test_an_array_of_a_fixed_width_inner_word_yields_one_element_per_declared_count() -> None:
    """The simplest element grammar, and the count is the tag's own.

    NEEDS NO SAVE LIBRARY.
    """
    elements = b"".join(struct.pack("<i", value) for value in (7, 9, 11))
    tag = _container_tag(
        "mSyntheticIntArray",
        "ArrayProperty",
        ("IntProperty",),
        _array_value("IntProperty", elements, _ARRAY_ELEMENTS),
    )

    result = _read_payload_of(tag)
    decoded = result.properties["mSyntheticIntArray"]

    assert isinstance(decoded, objects.ContainerValue)
    assert decoded.type_word == "ArrayProperty"
    assert decoded.element_words == ("IntProperty",)
    assert decoded.element_count == _ARRAY_ELEMENTS
    assert len(decoded.elements) == _ARRAY_ELEMENTS
    assert decoded.element_shape == objects.ELEMENT_SHAPE_SELF_DELIMITING
    assert tuple(element.value for element in decoded.elements) == (7, 9, 11)
    assert result.unmeasured_value_count == 0, (
        "a decoded container was counted as unmodelled content"
    )
    assert result.disagreeing_value_count == 0


def test_an_array_element_region_that_does_not_close_is_refused_rather_than_truncated() -> None:
    """The discriminator. A framing that does not consume the declared size exactly fails.

    THIS IS THE ONE THAT MAKES THE LIBRARY EQUALITY MEAN SOMETHING. Without a
    refusal here, a decode could return whatever it managed to read and the
    equality would hold by construction on any framing at all.

    NEEDS NO SAVE LIBRARY.
    """
    elements = b"".join(struct.pack("<i", value) for value in (7, 9, 11))
    tag = _container_tag(
        "mSyntheticShortArray",
        "ArrayProperty",
        ("IntProperty",),
        # FOUR declared, THREE present - the region cannot close.
        _array_value("IntProperty", elements, _ARRAY_ELEMENTS + 1),
    )

    result = _read_payload_of(tag)

    assert "mSyntheticShortArray" not in result.properties
    assert result.disagreeing_value_count == 1, (
        "an ArrayProperty whose elements do not account for its declared size came "
        "back as something other than a measured type whose bytes disagreed"
    )
    assert result.unmeasured_value_count == 0


def test_a_set_element_width_is_derived_from_the_region_and_the_count() -> None:
    """The UNIFORM shape - no element grammar, a width divided out of the region.

    NEEDS NO SAVE LIBRARY.
    """
    elements = bytes(_SET_ELEMENTS * _SET_ELEMENT_BYTES)
    tag = _container_tag(
        "mSyntheticSet",
        "SetProperty",
        ("StructProperty",),
        _set_value(elements, _SET_ELEMENTS),
    )

    result = _read_payload_of(tag)
    decoded = result.properties["mSyntheticSet"]

    assert isinstance(decoded, objects.ContainerValue)
    assert decoded.element_count == _SET_ELEMENTS
    assert decoded.element_shape == objects.ELEMENT_SHAPE_UNIFORM_WIDTH
    assert len(decoded.elements) == _SET_ELEMENTS
    assert all(element.length == _SET_ELEMENT_BYTES for element in decoded.elements)
    assert all(element.value is None for element in decoded.elements), (
        "a StructProperty element came back carrying a VALUE. The struct interior is "
        "CS-829 and reading it here would publish a guess"
    )


def test_a_set_region_that_does_not_divide_by_its_count_is_refused() -> None:
    """The UNIFORM shape's own discriminator, which is the division being exact.

    NEEDS NO SAVE LIBRARY.
    """
    tag = _container_tag(
        "mSyntheticRaggedSet",
        "SetProperty",
        ("StructProperty",),
        _set_value(bytes(_SET_ELEMENTS * _SET_ELEMENT_BYTES + 1), _SET_ELEMENTS),
    )

    result = _read_payload_of(tag)

    assert "mSyntheticRaggedSet" not in result.properties
    assert result.disagreeing_value_count == 1


# ---------------------------------------------------------------------------
# CS-830, NARROWED - what the UNIFORM shape does NOT discriminate.
#
# The cases below are the ones an adversary used to REFUTE the merged item, kept
# as tests rather than paraphrased in a note. Each one records a limit that
# still stands; none of them claims it has been repaired.
# ---------------------------------------------------------------------------


def test_the_element_shapes_whose_partition_is_not_discriminated_are_recorded() -> None:
    """The module ships WHICH readings leave the internal division underdetermined.

    A consumer handed a bounded element list cannot tell from the list whether
    the boundaries were read off the bytes or divided out of a span. The shape
    word already travels on the value; what was missing is the module saying
    which shape words carry a partition nothing checked.

    NEEDS NO SAVE LIBRARY - it is a claim about the repo.
    """
    undiscriminated = objects.UNDISCRIMINATED_ELEMENT_SHAPES

    assert undiscriminated, (
        "objects.UNDISCRIMINATED_ELEMENT_SHAPES is empty, so the module records no "
        "limit at all and this test grades nothing"
    )
    unknown = sorted(undiscriminated - objects.ELEMENT_SHAPES)
    assert not unknown, f"{unknown} are recorded as shapes the module does not ship"
    assert objects.ELEMENT_SHAPE_UNIFORM_WIDTH in undiscriminated, (
        "the uniform shape divides a span by a count and admits the answer because "
        "the division came out even. That is a property of two integers and not of "
        "the bytes between them, so it has to be recorded as underdetermined"
    )
    assert objects.ELEMENT_SHAPE_SELF_DELIMITING not in undiscriminated, (
        "the self-delimiting reading IS the element's own grammar saying where it "
        "ends, and recording it as underdetermined would erase the one distinction "
        "the shape words exist to carry"
    )


def test_a_uniform_region_is_partitioned_by_a_declared_count_nothing_cross_checks() -> None:
    """The defect CS-830 caught in its own first draft, alive in the shape it permits.

    A region genuinely holding a few wide elements, declared as one slot per
    BYTE, divides exactly and is published as that many one-byte elements. The
    region closes, the count agrees with the declaration, and every element
    extent is wrong. Nothing in the container cross-checks the declared count
    against the bytes, so this is not caught and is not claimed to be.

    NEEDS NO SAVE LIBRARY.
    """
    carried = 3
    width = 9
    region = bytes(carried * width)
    declared = len(region)
    tag = _container_tag(
        "mSyntheticMisdeclaredSet",
        "SetProperty",
        ("StructProperty",),
        _set_value(region, declared),
    )

    result = _read_payload_of(tag)
    decoded = result.properties["mSyntheticMisdeclaredSet"]

    assert isinstance(decoded, objects.ContainerValue)
    assert decoded.element_shape == objects.ELEMENT_SHAPE_UNIFORM_WIDTH
    assert len(decoded.elements) == declared, (
        "the region did not partition by the DECLARED count, which is the whole of "
        "what this case records"
    )
    assert all(bounded.length == 1 for bounded in decoded.elements), (
        "the declared count divided the span into one-byte elements and the decode "
        "published them. This assertion is a RECORD of that, not an endorsement"
    )
    assert result.disagreeing_value_count == 0, (
        "the decode was accepted rather than refused, which is what makes the "
        "misdeclaration invisible to every equality taken over accepted decodes"
    )
    assert decoded.element_shape in objects.UNDISCRIMINATED_ELEMENT_SHAPES, (
        "the shape this decode came back under is not recorded as one whose "
        "partition nothing discriminates, so a consumer reading these extents has "
        "no way to learn they were divided out rather than read"
    )


def test_the_element_total_holds_by_construction_whatever_the_widths_are() -> None:
    """The count equality is an IDENTITY, and saying so is worth a test.

    ``_walk_elements`` appends exactly one entry per ``count x words`` step and
    returns None otherwise, so its length is ``count * len(words)`` for EVERY
    width tuple that closes the region. Any equality between the bounded total
    and the declared total therefore holds however the region was partitioned -
    it grades the walk's arithmetic and nothing about the element widths.

    NEEDS NO SAVE LIBRARY.
    """
    span = 24
    body = bytes(span)
    words = ("StructProperty",)
    closing = [width for width in range(1, span + 1) if span % width == 0]
    assert len(closing) > 1, "one closing width grades no alternative, so this is vacuous"

    for width in closing:
        count = span // width
        found = objects._walk_elements(body, words, 0, span, count, (width,))  # noqa: SLF001
        assert found is not None, "a width dividing the span exactly failed to close"
        assert len(found) == count * len(words), (
            "the walk returned a length other than count x words, which would mean "
            "the identity this test records is not one"
        )
        assert sum(bounded.length for bounded in found) == span


def test_a_map_yields_a_key_half_and_a_value_half_for_every_entry() -> None:
    """The map is the only container whose entry is a pair, and both halves are bounded.

    NEEDS NO SAVE LIBRARY.
    """
    entries = b"".join(
        test_properties._fstring(level)  # noqa: SLF001
        + test_properties._fstring(path)  # noqa: SLF001
        + struct.pack("<i", number)
        for level, path, number in (
            ("Persistent_Level", "Persistent_Level:PersistentLevel.SyntheticA_0", 3),
            ("Persistent_Level", "Persistent_Level:PersistentLevel.SyntheticB_0", 5),
        )
    )
    tag = _container_tag(
        "mSyntheticMap",
        "MapProperty",
        ("ObjectProperty", "IntProperty"),
        _map_value(entries, _MAP_ELEMENTS),
    )

    result = _read_payload_of(tag)
    decoded = result.properties["mSyntheticMap"]

    assert isinstance(decoded, objects.ContainerValue)
    assert decoded.element_words == ("ObjectProperty", "IntProperty")
    assert decoded.element_count == _MAP_ELEMENTS
    assert len(decoded.elements) == _MAP_ELEMENTS * _MAP_ENTRY_HALVES
    assert decoded.element_shape == objects.ELEMENT_SHAPE_SELF_DELIMITING

    words = tuple(element.type_word for element in decoded.elements)
    assert words == ("ObjectProperty", "IntProperty", "ObjectProperty", "IntProperty"), (
        "the map's halves did not alternate key, value, key, value"
    )
    assert tuple(element.value for element in decoded.elements)[1::2] == (3, 5)


def test_a_container_whose_element_word_has_no_grammar_is_flagged_and_never_raises() -> None:
    """Non-negotiable 7 at the element level - unknown content is skipped, not fatal.

    THE COUNTER IT LANDS IN IS THE POINT, not merely that nothing raised. A
    container this module cannot bound is UNMODELLED CONTENT; a container it CAN
    bound whose bytes then disagree is a walk that has lost its place. Those two
    mean opposite things, and ``objects._walk_payload`` records that collapsing
    them is the half of non-negotiable 7 with no second chance.

    NEEDS NO SAVE LIBRARY.
    """
    # Deliberately NOT divisible by the count, so the derived shapes cannot
    # rescue a word whose own grammar is unknown.
    tag = _container_tag(
        "mSyntheticAlienArray",
        "ArrayProperty",
        (_UNMODELLED_INNER_WORD,),
        _array_value(_UNMODELLED_INNER_WORD, bytes(7), _ARRAY_ELEMENTS),
    )

    result = _read_payload_of(tag)

    assert "mSyntheticAlienArray" not in result.properties
    assert result.unmeasured_value_count == 1, (
        "a container whose element word this module has no grammar for was counted "
        "as a measured type whose bytes disagreed. That reports unmodelled content "
        "as a desynchronised walk"
    )
    assert result.disagreeing_value_count == 0


def test_an_array_of_struct_bounds_each_element_without_claiming_its_interior() -> None:
    """The seam with CS-829, exercised rather than promised.

    An array of ``StructProperty`` carries an inner tag naming the struct and
    bounding the whole element region; the elements inside it are nested tag
    lists. This module bounds each one and hands back no value for any of them.

    NEEDS NO SAVE LIBRARY.
    """
    element = (
        test_properties._tag_head("mInner", "IntProperty", 4, b"")  # noqa: SLF001
        + struct.pack("<i", 12)
        + test_properties._fstring("None")  # noqa: SLF001
    )
    region = element * _SET_ELEMENTS
    inner_tag = (
        test_properties._fstring("mSyntheticStructArray")  # noqa: SLF001
        + test_properties._fstring("StructProperty")  # noqa: SLF001
        + struct.pack("<i", len(region))
        + struct.pack("<i", 0)
        + test_properties._fstring("SyntheticInnerStruct")  # noqa: SLF001
        + bytes(objects.GUID_BYTES)
        + b"\x00"
    )
    tag = _container_tag(
        "mSyntheticStructArray",
        "ArrayProperty",
        ("StructProperty",),
        struct.pack("<i", _SET_ELEMENTS) + inner_tag + region,
    )

    result = _read_payload_of(tag)
    decoded = result.properties["mSyntheticStructArray"]

    assert isinstance(decoded, objects.ContainerValue)
    assert decoded.element_count == _SET_ELEMENTS
    assert len(decoded.elements) == _SET_ELEMENTS
    assert decoded.element_shape == objects.ELEMENT_SHAPE_SELF_DELIMITING
    assert all(bounded.length == len(element) for bounded in decoded.elements), (
        "an element was bounded at some length other than the nested tag list's own"
    )
    assert all(bounded.value is None for bounded in decoded.elements)
    assert decoded.struct_word == "SyntheticInnerStruct", (
        "the inner struct's own type word was not carried out. It is what CS-829 "
        "needs to read the interior this decode deliberately leaves alone"
    )


def test_no_repr_the_container_decode_adds_renders_an_element_s_bytes() -> None:
    """Non-negotiables 11 and 12 - a container holds world content and its repr must not.

    NEEDS NO SAVE LIBRARY.
    """
    marker = test_properties._fstring(_LEAK_MARKER)  # noqa: SLF001
    elements = marker * _ARRAY_ELEMENTS
    tag = _container_tag(
        "mSyntheticLeakArray",
        "ArrayProperty",
        ("StrProperty",),
        _array_value("StrProperty", elements, _ARRAY_ELEMENTS),
    )

    result = _read_payload_of(tag)
    decoded = result.properties["mSyntheticLeakArray"]

    assert isinstance(decoded, objects.ContainerValue)
    assert _LEAK_MARKER not in repr(decoded), "the container repr rendered an element value"
    for element in decoded.elements:
        assert _LEAK_MARKER not in repr(element), "the element repr rendered its own value"
    assert _LEAK_MARKER not in repr(result), "the property result repr rendered a container"


# ---------------------------------------------------------------------------
# The real library - CS-830's first acceptance arm
# ---------------------------------------------------------------------------


@dataclass(frozen=True, repr=False)
class _ContainerSweep:
    """COUNTS ONLY. No field here can hold a path, a name, a word or a value.

    Attributes:
        saves: How many saves of a tagged pair were walked.
        records: How many records the reader was asked about.
        tags: Container TAGS the second pass stepped over, by container word.
        decoded: Container tags that yielded a bounded element list, by word.
        elements: Element halves bounded, by container word.
        declared: The element counts the containers themselves declared, by
            word, multiplied out by how many halves an entry carries. Held
            against ``elements`` so a bounded list of the wrong length is
            caught by something other than the framing that produced it.
        shapes: How many containers each element shape bounded, keyed by
            (CONTAINER WORD, shape word). THE CONTAINER WORD IS HALF THE KEY
            AND ITS ABSENCE WAS A DEFECT: pooled on the shape word alone, a
            word with no grammar evidence at all was invisible behind a word
            that had plenty, and the guard over the pooled total passed.
        single_slot: Containers bounded by a DERIVED shape over a single slot,
            where the division is the identity and grades nothing, by
            container word.
        failures: Exception TYPE NAMES, and nothing else about them.
    """

    saves: int
    records: int
    tags: Mapping[str, int]
    decoded: Mapping[str, int]
    elements: Mapping[str, int]
    declared: Mapping[str, int]
    shapes: Mapping[tuple[str, str], int]
    single_slot: Mapping[str, int]
    failures: tuple[str, ...]

    def __repr__(self) -> str:
        """Render counts only.

        Returns:
            The safe rendering.
        """
        return (
            f"{type(self).__name__}(saves={self.saves}, records={self.records}, "
            f"tags={dict(sorted(self.tags.items()))}, "
            f"decoded={dict(sorted(self.decoded.items()))}, "
            f"elements={dict(sorted(self.elements.items()))}, "
            f"declared={dict(sorted(self.declared.items()))}, "
            f"shapes={dict(sorted(self.shapes.items()))}, "
            f"single_slot={dict(sorted(self.single_slot.items()))}, "
            f"failures={self.failures})"
        )


@dataclass
class _ContainerTally:
    """The sweep's running accumulators, gathered so the folder takes one.

    COUNTS ONLY, on the same terms as :class:`_ContainerSweep`. Every value is
    an integer and every KEY is a shipped constant - a container type word or an
    element shape word - so nothing read out of a save can reach a repr through
    this type either.

    IT IS A TYPED RECORD RATHER THAN A ``dict[str, object]``, and that is worth
    a line because the dict came first: it needed eight ``type: ignore``
    comments to get past the mypy gate, and every one of them was a place a
    genuine type error could hide behind an ignore that was there for an
    unrelated reason.

    Attributes:
        saves: How many saves of a tagged pair were walked.
        records: How many records the reader was asked about.
        single_slot: Derived bounds over a single slot, by container word.
        tags: Container tags stepped over, by container word.
        decoded: Container tags that yielded elements, by container word.
        elements: Element halves bounded, by container word.
        declared: Slots the containers themselves declared, by container word.
        shapes: How many containers each shape bounded, keyed by (container
            word, shape word).
    """

    saves: int = 0
    records: int = 0
    single_slot: dict[str, int] = field(default_factory=dict)
    tags: dict[str, int] = field(default_factory=dict)
    decoded: dict[str, int] = field(default_factory=dict)
    elements: dict[str, int] = field(default_factory=dict)
    declared: dict[str, int] = field(default_factory=dict)
    shapes: dict[tuple[str, str], int] = field(default_factory=dict)


def _sweep_one_save(data: bytes, parsed: header.SaveHeader, into: _ContainerTally) -> None:
    """Walk one save and fold its container tags into the accumulator.

    THE CALLER HOLDS THE ``try``. This function is allowed to raise; its only
    call site is inside the sweep's broad handler, which reduces whatever comes
    out to a type name before any frame holding ``data`` or ``body`` is
    rendered.

    IT WALKS WITH THE SHIPPED READER AND DECODES WITH THE SHIPPED DECODER, so it
    grades neither. What it contributes is the POPULATION - a tag total taken
    outside ``_walk_payload`` - and the equality that total stands in.

    Args:
        data: The save file's bytes.
        parsed: Its parsed header.
        into: The accumulator, mutated in place.
    """
    body = chunks.decompress_body(
        data, parsed.body_offset, header_version=parsed.header_version
    ).payload
    table = objects.parse_body(
        body, save_version=parsed.save_version, header_version=parsed.header_version
    )
    into.saves += 1
    tags = into.tags
    decoded = into.decoded
    elements = into.elements
    declared = into.declared
    shapes = into.shapes
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
            if word not in objects.CONTAINER_TYPE_WORDS:
                continue
            tags[word] = tags.get(word, 0) + 1
            after_name = objects._payload_text(body, head, end)  # noqa: SLF001
            if after_name is None:
                continue
            element_words = objects._container_element_words(  # noqa: SLF001
                body, after_name[1], end, word
            )
            if element_words is None:
                continue
            value = objects._decode_value(  # noqa: SLF001
                body, word, value_at, size, None, element_words
            )
            if not isinstance(value, objects.ContainerValue):
                continue
            decoded[word] = decoded.get(word, 0) + 1
            elements[word] = elements.get(word, 0) + len(value.elements)
            declared[word] = declared.get(word, 0) + value.element_count * len(value.element_words)
            key = (word, value.element_shape)
            shapes[key] = shapes.get(key, 0) + 1
            if value.element_shape != objects.ELEMENT_SHAPE_SELF_DELIMITING and (
                value.element_count * len(value.element_words) <= 1
            ):
                into.single_slot[word] = into.single_slot.get(word, 0) + 1


def _sweep_the_library() -> _ContainerSweep | None:
    """Walk each real save once and return COUNTS ONLY.

    IT IS UNCACHED AND THE CACHE SITS ON ITS CALLER, so a pass that has to run
    under a patched decoder gets its own walk without evicting the pristine
    one. Sharing a cache between the two would make the pristine floor and the
    mutated run each other's cost, and a floor that is re-derived under a patch
    is not a floor.

    IT CONTAINS ``Exception`` AND ``SystemExit``, AND STOPS THERE, on the terms
    ``tests/save/test_decode_oracles.py`` argues at length: a save path, a body
    and a property name are things pytest renders out of a frame it unwinds, and
    ``path.read_bytes()`` is a bound method whose ``self`` IS the save path.
    ``KeyboardInterrupt`` is deliberately left free to unwind.

    Returns:
        The sweep, or None when no save library is reachable.
    """
    saves = test_properties._library_save_paths()  # noqa: SLF001
    if not saves:
        return None

    into = _ContainerTally()
    failures: list[str] = []
    for path in saves:
        try:
            data = path.read_bytes()
            parsed = header.parse_header(data)
        except (OSError, header.HeaderError):
            # The two EXPECTED failures - an unreadable file, and a save of a
            # version this project does not parse. The library legitimately
            # holds both, and any recorded failure is treated as fatal below.
            continue
        except (Exception, SystemExit) as exc:
            failures.append(type(exc).__name__)
            continue
        if (parsed.header_version, parsed.save_version) not in test_properties.TAGGED_PAIRS:
            continue
        try:
            _sweep_one_save(data, parsed, into)
        except (Exception, SystemExit) as exc:
            # BROAD BY DESIGN: a narrower catch lets an unexpected type escape
            # carrying the save bytes, which is the leak this containment closes.
            failures.append(type(exc).__name__)
            continue
    # The names and the paths are JUDGED here and discarded here.
    return _ContainerSweep(
        saves=into.saves,
        records=into.records,
        tags=MappingProxyType(dict(into.tags)),
        decoded=MappingProxyType(dict(into.decoded)),
        elements=MappingProxyType(dict(into.elements)),
        declared=MappingProxyType(dict(into.declared)),
        shapes=MappingProxyType(dict(into.shapes)),
        single_slot=MappingProxyType(dict(into.single_slot)),
        failures=tuple(sorted(set(failures))),
    )


@lru_cache(maxsize=1)
def _sweep_containers() -> _ContainerSweep | None:
    """The pristine sweep, walked once per session.

    Returns:
        The sweep, or None when no save library is reachable.
    """
    return _sweep_the_library()


@lru_cache(maxsize=1)
def _sweep_with_a_wrong_partition() -> tuple[_ContainerSweep, int]:
    """Re-walk the library with the even division replaced by a WRONG one.

    THE MUTANT. Wherever the shipped decoder would divide an element region
    evenly, the first element takes the whole span less one byte per remaining
    slot and every other element takes exactly one. The region still closes and
    the element total is unchanged, because neither of those facts depends on
    where the boundaries fall - which is the point being measured.

    IT PATCHES AND RESTORES IN A ``finally``, and it counts the applications so
    a patch that never landed cannot be read as a partition nothing detected.
    Those two outcomes produce identical green, and this project has a recorded
    incident of exactly that confusion.

    A SINGLE SLOT IS LEFT ALONE. There is no alternative partition of one
    element, so mutating it would be a no-op recorded as an application and
    would inflate the landed count with cases that grade nothing.

    Returns:
        The mutated sweep and how many containers the wrong partition was
        applied to.
    """
    applied = 0
    real = objects._bound_container_elements  # noqa: SLF001

    def _mutated(
        body: bytes, words: tuple[str, ...], at: int, end: int, count: int
    ) -> tuple[str, tuple[objects.ContainerElement, ...]] | None:
        nonlocal applied
        bounded = real(body, words, at, end, count)
        if bounded is None or bounded[0] != objects.ELEMENT_SHAPE_UNIFORM_WIDTH:
            return bounded
        slots = count * len(words)
        span = end - at
        if slots < _SLOTS_WITH_AN_ALTERNATIVE_PARTITION or span < slots:
            return bounded
        widths = [span - (slots - 1)] + [1] * (slots - 1)
        found: list[objects.ContainerElement] = []
        cursor = at
        halves = [half for _ in range(count) for half in words]
        for position, half in enumerate(halves):
            found.append(
                objects.ContainerElement(
                    type_word=half,
                    start=cursor,
                    length=widths[position],
                    value=None,
                )
            )
            cursor += widths[position]
        if cursor != end:
            return bounded
        applied += 1
        return (objects.ELEMENT_SHAPE_UNIFORM_WIDTH, tuple(found))

    objects._bound_container_elements = _mutated  # noqa: SLF001
    try:
        sweep = _sweep_the_library()
    finally:
        objects._bound_container_elements = real  # noqa: SLF001
    assert objects._bound_container_elements is real, (  # noqa: SLF001
        "the shipped decoder was not put back, so every later test in this "
        "session would grade a patched module"
    )
    assert sweep is not None, "the pristine floor was taken first, so a library was reachable"
    return (sweep, applied)


def _sweep_or_skip() -> _ContainerSweep:
    """Fetch the sweep, skipping when this machine cannot grade it.

    THE FAILURE ASSERTION COMES FIRST so an unreadable library reddens rather
    than skipping quietly. Only an empty-but-clean walk skips, and "absent" has
    to mean absent of anything gradeable rather than absent of files - the same
    class of gate ``tests/save/test_reference_resolution.py`` records this
    project getting wrong once already.

    Returns:
        The sweep.
    """
    sweep = _sweep_containers()
    if sweep is None:
        pytest.skip("no save library on this machine - container elements are not gradeable here")
    assert sweep.failures == (), f"failures walking real bodies: {sweep.failures}"
    if sweep.saves == 0:
        pytest.skip(
            "the save library holds no save of a version pair this project parses - "
            "container elements are not gradeable here"
        )
    return sweep


def test_every_container_instance_in_the_library_yields_a_decoded_element() -> None:
    """CS-830's acceptance, as an EQUALITY over the tag population.

    ONE CLAUSE PER WORD, AND EVERY WORD PRESENT MUST BE COVERED. A single
    equality over the summed totals would let a shortfall on one word be paid
    for by a surplus on another, which cannot happen today and would be
    undetectable if it ever did.

    SKIP-IF-ABSENT, COUNTS ONLY. Nothing rendered by a failure here came out of
    a save: the words are shipped constants and the numbers are integers.
    """
    sweep = _sweep_or_skip()

    assert sweep.tags, (
        "the library holds no container tag at all, so this equality grades "
        "nothing. Either the walk stopped reaching them or the population is gone"
    )
    uncovered = sorted(frozenset(sweep.tags) - objects.CONTAINER_TYPE_WORDS)
    assert not uncovered, (
        f"{uncovered} were counted as container tags and are not among the words "
        "this item owns, so the sweep and the shipped set disagree about the population"
    )

    for word in sorted(sweep.tags):
        assert sweep.decoded.get(word, 0) == sweep.tags[word], (
            f"{word}: {sweep.decoded.get(word, 0)} of {sweep.tags[word]} instances "
            "yielded a decoded element. The acceptance is an EQUALITY over the whole "
            "population and not a floor - a shortfall is an element framing that "
            "stops closing somewhere, and the containers it stops closing on are "
            "exactly the ones nobody has looked at"
        )
        assert sweep.elements.get(word, 0) > 0, (
            f"{word}: every instance decoded and not one element came back, so the "
            "equality above is being satisfied by empty element lists"
        )


def test_the_bounded_elements_agree_with_the_counts_the_containers_declared() -> None:
    """The walk's arithmetic, held against the containers' own count fields.

    WHAT THIS DOES NOT CATCH, CORRECTED. Its first wording claimed a framing
    that bounded the wrong NUMBER of elements would move one side and not the
    other. THAT IS FALSE AND WAS FALSE WHEN WRITTEN. ``_walk_elements`` appends
    exactly one entry per ``count x words`` step or returns None, so both sides
    are computed from the same declared count and the equality is an IDENTITY -
    it moves both sides together or neither. The identity is exercised directly
    in ``test_the_element_total_holds_by_construction_whatever_the_widths_are``.

    WHAT IT IS STILL WORTH. An identity over the walk is a real check on the
    FOLD around it: a sweep that double-counted a half, dropped a container
    between the two tallies, or mismatched the map's two-halves-per-entry
    arithmetic would break it. It grades the accounting, not the widths, and the
    difference is the whole reason the sentence above was corrected rather than
    deleted.

    SKIP-IF-ABSENT, COUNTS ONLY.
    """
    sweep = _sweep_or_skip()

    assert sweep.elements, "no element was bounded at all, so this grades nothing"
    for word in sorted(sweep.elements):
        assert sweep.elements[word] == sweep.declared.get(word, 0), (
            f"{word}: {sweep.elements[word]} element halves were bounded and the "
            f"containers declared {sweep.declared.get(word, 0)}. A framing that "
            "closes the region with the wrong number of elements is a framing that "
            "has the element width wrong and the region right"
        )


def test_the_library_container_counts_are_recorded_for_the_ledger() -> None:
    """What this run measured, printed rather than written into a tracked file.

    NO FIGURE FROM THIS RUN GOES INTO PROSE. The operator plays this game, so
    every count here changes on the next autosave and a number copied into a
    docstring is false on a timer - CLAUDE.md section 4. What is asserted is the
    SHAPE: that every shipped shape word was exercised somewhere in the corpus.

    THE POOLED MAJORITY ASSERTION THAT STOOD HERE IS GONE, and its removal is
    the item's narrowing rather than a simplification. Summed over the three
    container words it read as evidence about all of them while being evidence
    about the largest one, and a word with no grammar evidence at all passed
    behind it. It is replaced by the per-word form in
    ``test_the_shape_evidence_is_graded_per_container_word_and_not_pooled``,
    which grades each word against its own population.

    SKIP-IF-ABSENT, COUNTS ONLY.
    """
    sweep = _sweep_or_skip()

    assert sweep.records > 0, "no record was walked"
    assert sweep.shapes, "no element shape was recorded, so nothing was bounded"

    seen = frozenset(shape for _word, shape in sweep.shapes)
    unknown = sorted(seen - objects.ELEMENT_SHAPES)
    assert not unknown, f"the sweep recorded element shapes the module does not ship: {unknown}"


def test_the_shape_evidence_is_graded_per_container_word_and_not_pooled() -> None:
    """CS-830, NARROWED - one word's grammar evidence may not stand in for another's.

    THE POOLED FORM OF THIS GUARD WAS THE DEFECT. Summed over all three words,
    the strong reading is the large majority and the assertion passed while one
    container word had NOT ONE instance bounded by the element's own grammar.
    Pooling let the word with the evidence answer for the word without it, and
    the failure was silent because both figures went into one total.

    WHAT THE SPLIT ASSERTS. Each word is graded against its OWN population, and
    a word carried entirely by a derived reading has to be named in
    ``objects.CONTAINER_WORDS_WITHOUT_ELEMENT_GRAMMAR_EVIDENCE``. The record is
    held EQUAL to what this run measures, so it reddens in both directions: a
    word losing its grammar evidence reddens, and a word gaining it reddens too
    and asks for the record to be narrowed.

    SKIP-IF-ABSENT, COUNTS ONLY. Every word rendered here is a shipped constant
    and every number is an integer.
    """
    sweep = _sweep_or_skip()
    assert sweep.shapes, "no element shape was recorded, so nothing was bounded"

    unknown = sorted(
        (word, shape)
        for word, shape in sweep.shapes
        if word not in objects.CONTAINER_TYPE_WORDS or shape not in objects.ELEMENT_SHAPES
    )
    assert not unknown, f"the sweep recorded pairs the module does not ship: {unknown}"

    recorded = objects.CONTAINER_WORDS_WITHOUT_ELEMENT_GRAMMAR_EVIDENCE
    measured: set[str] = set()
    for word in sorted(sweep.decoded):
        total = sum(count for (this, _shape), count in sweep.shapes.items() if this == word)
        assert total > 0, f"{word}: decoded instances recorded no shape at all"
        grammar = sweep.shapes.get((word, objects.ELEMENT_SHAPE_SELF_DELIMITING), 0)
        if grammar == 0:
            measured.add(word)
            continue
        assert grammar * 2 > total, (
            f"{word}: {grammar} of {total} of THIS WORD's containers were bounded by "
            "the element's own grammar and the rest by a DERIVED width. The derived "
            "readings are the weaker evidence and were never meant to carry a word's "
            "population - and this is the per-word form precisely so another word's "
            "surplus cannot pay for it"
        )

    assert measured == set(recorded), (
        f"this run measures {sorted(measured)} as container words with NO instance "
        f"bounded by the element's own grammar, and the module records {sorted(recorded)}. "
        "A word that gained grammar evidence should leave the record; a word that lost "
        "it must join. The record is held equal rather than as a floor so it cannot "
        "quietly describe a corpus that has moved"
    )

    for word in sorted(recorded):
        single = sweep.single_slot.get(word, 0)
        derived = sum(
            count
            for (this, shape), count in sweep.shapes.items()
            if this == word and shape != objects.ELEMENT_SHAPE_SELF_DELIMITING
        )
        assert single < derived, (
            f"{word}: every derived bound was taken over a single slot, where the "
            "division is the identity and grades nothing at all"
        )


def test_a_provably_wrong_partition_survives_every_library_backed_equality() -> None:
    """The refutation, kept as a MEASUREMENT rather than settled by argument.

    THE MUTANT. Where the shipped decoder divides an element region evenly, this
    run takes the first element as the whole span less one byte per remaining
    slot and every other element as exactly one byte. It is wrong on any reading
    of the format, it closes the region, and it yields the same number of
    elements. Both library-backed equalities stay green under it.

    A RED HERE IS GOOD NEWS AND MEANS THE RECORD MUST BE NARROWED. This asserts
    that the corpus does NOT discriminate the partition, so the day something in
    it does, this test is what says so and
    ``objects.UNDISCRIMINATED_ELEMENT_SHAPES`` is what gets corrected. Asserting
    the limit is the only way to stop the limit being quietly overstated later.

    THE MUTATION IS ASSERTED TO HAVE LANDED. A patch that never applied and a
    partition the equalities cannot see produce the same green, and this project
    has recorded being caught by exactly that.

    SKIP-IF-ABSENT, COUNTS ONLY.
    """
    _sweep_or_skip()
    mutated, applied = _sweep_with_a_wrong_partition()

    assert applied > 0, (
        "the wrong partition was never applied to a single container, so this run "
        "grades nothing - a mutant that did not land and a mutant the tests cannot "
        "see are the same green"
    )
    assert mutated.failures == (), f"failures walking real bodies: {mutated.failures}"
    assert mutated.tags, "the mutated sweep bounded no container at all"

    for word in sorted(mutated.tags):
        assert mutated.decoded.get(word, 0) == mutated.tags[word], (
            f"{word}: the wrong partition changed how many instances decoded. If that "
            "is real the region-closing check now discriminates it, and the recorded "
            "limit is too wide"
        )
    for word in sorted(mutated.elements):
        assert mutated.elements[word] == mutated.declared.get(word, 0), (
            f"{word}: the wrong partition moved the bounded total off the declared "
            "total. That equality is an identity over the walk, so this would mean "
            "the walk changed rather than the widths"
        )

    assert objects.ELEMENT_SHAPE_UNIFORM_WIDTH in objects.UNDISCRIMINATED_ELEMENT_SHAPES, (
        "a wrong partition just survived every equality this project has, and the "
        "module does not record that shape's partition as underdetermined"
    )


def test_an_unexpected_read_failure_does_not_unwind_through_the_container_sweep(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The containment, exercised rather than described.

    A forced failure inside the per-save read has to be reduced to a type name
    before any frame holding the save path can be rendered. The discovery is
    replaced with a synthetic value FIRST, so this needs no library and depends
    on no test ordering - the shape ``tests/save/test_reference_resolution.py``
    records CI's ``-n auto`` load distribution as requiring.

    NEEDS NO SAVE LIBRARY AND NO GAME INSTALL.
    """

    class _PlantedError(Exception):
        """A type name the sweep must reduce to."""

    def _boom(_self: object) -> bytes:
        raise _PlantedError(_LEAK_MARKER)

    monkeypatch.setattr(
        "tests.save.test_properties._library_save_paths",
        lambda: (test_properties._SYNTHETIC_SAVE,),  # noqa: SLF001
    )
    monkeypatch.setattr("pathlib.Path.read_bytes", _boom)
    _sweep_containers.cache_clear()
    try:
        sweep = _sweep_containers()
    finally:
        _sweep_containers.cache_clear()

    assert sweep is not None
    assert sweep.failures == ("_PlantedError",)
    assert sweep.saves == 0, "a save was walked despite every read raising"
    assert _LEAK_MARKER not in repr(sweep)


def test_the_container_surface_is_on_the_module_s_stated_public_surface() -> None:
    """A consumer reads these, so they are exported rather than reached for privately.

    NEEDS NO SAVE LIBRARY.
    """
    for name in (
        "CONTAINER_ADJACENT_OWNERS",
        "CONTAINER_TYPE_WORDS",
        "ContainerElement",
        "ContainerValue",
        "ELEMENT_SHAPES",
        "ELEMENT_SHAPE_SELF_DELIMITING",
        "ELEMENT_SHAPE_SOLVED_WIDTH",
        "ELEMENT_SHAPE_UNIFORM_WIDTH",
        "container_candidate_words",
    ):
        assert name in objects.__all__, f"{name} is not on the stated public surface"
        assert getattr(objects, name, None) is not None


# ---------------------------------------------------------------------------
# CS-471 - THIS MODULE'S LIBRARY REACH, DECLARED.
#
# The guard is owned by ``reach_guard`` and applied across this package by the
# suite-wide test in ``test_reach_guard``, which walks the package directory
# rather than waiting to be called. A new library-reaching module is in scope
# the moment it exists.
# ---------------------------------------------------------------------------

#: Helpers that genuinely reach the save library, name to why each reaches. The
#: key is the function's own ``__name__`` and the reason comes from
#: ``reach_guard``, so a rename moves both together.
#:
#: ONE ENTRY, THOUGH THREE FUNCTIONS SWEEP. Splitting the cached wrapper off the
#: walk moved the reach: ``_sweep_the_library`` is the only one that ever holds a
#: save path, and its two callers take a COUNTS-ONLY record back from it. Listing
#: them here as reaching was tried and the package-wide guard REFUSED IT - a
#: declaration that names a function which no longer reaches is an exemption
#: outliving the code it described, which is the failure that guard exists to
#: catch. The containment grader below still forces its failure through this
#: entry, because it drives the walk by way of the cached wrapper.
_GRADED_LIBRARY_REACH: Final = MappingProxyType(
    {_sweep_the_library.__name__: reach_guard.REACH_READS_THE_LIBRARY}
)

#: Touches a primitive WITHOUT consuming a real save path, name to why. Empty
#: for the reason ``tests/save/test_reference_resolution.py`` records: the
#: containment case replaces the discovery with a synthetic value before
#: breaking any read, so it reaches nothing.
_EXEMPT_LIBRARY_REACH: Final[Mapping[str, str]] = MappingProxyType({})
