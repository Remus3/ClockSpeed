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
element width, a wrong inner-tag shape - because the decode is refused rather
than approximated when the region does not close. It does NOT catch a record the
walk skipped: the tag total and the decode total are both taken inside the same
sweep off the same walk, so a payload that never reaches the walk moves neither.
That is the same limit CS-831 records for its own partition, and it is written
here rather than left for a reader to discover.

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
        shapes: How many containers each element shape bounded.
        single_slot: Containers bounded by a DERIVED shape over a single slot,
            where the division is the identity and grades nothing.
        failures: Exception TYPE NAMES, and nothing else about them.
    """

    saves: int
    records: int
    tags: Mapping[str, int]
    decoded: Mapping[str, int]
    elements: Mapping[str, int]
    declared: Mapping[str, int]
    shapes: Mapping[str, int]
    single_slot: int
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
            f"single_slot={self.single_slot}, failures={self.failures})"
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
        single_slot: Derived bounds taken over a single slot.
        tags: Container tags stepped over, by container word.
        decoded: Container tags that yielded elements, by container word.
        elements: Element halves bounded, by container word.
        declared: Slots the containers themselves declared, by container word.
        shapes: How many containers each element shape bounded.
    """

    saves: int = 0
    records: int = 0
    single_slot: int = 0
    tags: dict[str, int] = field(default_factory=dict)
    decoded: dict[str, int] = field(default_factory=dict)
    elements: dict[str, int] = field(default_factory=dict)
    declared: dict[str, int] = field(default_factory=dict)
    shapes: dict[str, int] = field(default_factory=dict)


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
            shapes[value.element_shape] = shapes.get(value.element_shape, 0) + 1
            if value.element_shape != objects.ELEMENT_SHAPE_SELF_DELIMITING and (
                value.element_count * len(value.element_words) <= 1
            ):
                into.single_slot += 1


@lru_cache(maxsize=1)
def _sweep_containers() -> _ContainerSweep | None:
    """Walk each real save once and return COUNTS ONLY.

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
        single_slot=into.single_slot,
        failures=tuple(sorted(set(failures))),
    )


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
    """A second derivation of the same total, off the containers' own count fields.

    The equality above counts CONTAINERS. This counts ELEMENTS, against the
    element counts the containers declared rather than against the list the
    framing produced - so a framing that bounded the wrong NUMBER of elements
    while still closing the region moves one side and not the other.

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
    SHAPE: that each shape word was exercised, and that the weaker derived
    readings did not quietly become the majority.

    SKIP-IF-ABSENT, COUNTS ONLY.
    """
    sweep = _sweep_or_skip()

    assert sweep.records > 0, "no record was walked"
    assert sweep.shapes, "no element shape was recorded, so nothing was bounded"

    unknown = sorted(frozenset(sweep.shapes) - objects.ELEMENT_SHAPES)
    assert not unknown, f"the sweep recorded element shapes the module does not ship: {unknown}"

    total = sum(sweep.shapes.values())
    self_delimiting = sweep.shapes.get(objects.ELEMENT_SHAPE_SELF_DELIMITING, 0)
    assert self_delimiting * 2 > total, (
        f"{self_delimiting} of {total} containers were bounded by the element's own "
        "grammar and the rest by a DERIVED width. The derived readings are the weaker "
        "evidence and were never meant to carry the population; if they now do, the "
        "self-delimiting reading has stopped closing somewhere"
    )
    assert sweep.single_slot < total, (
        "every derived bound in the library was taken over a single slot, where the "
        "division is the identity and grades nothing"
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
_GRADED_LIBRARY_REACH: Final = MappingProxyType(
    {_sweep_containers.__name__: reach_guard.REACH_READS_THE_LIBRARY}
)

#: Touches a primitive WITHOUT consuming a real save path, name to why. Empty
#: for the reason ``tests/save/test_reference_resolution.py`` records: the
#: containment case replaces the discovery with a synthetic value before
#: breaking any read, so it reaches nothing.
_EXEMPT_LIBRARY_REACH: Final[Mapping[str, str]] = MappingProxyType({})
