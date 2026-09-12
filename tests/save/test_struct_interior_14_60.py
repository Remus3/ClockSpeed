"""The (14,60) tag grammar INSIDE a value - struct interiors and container elements.

WHAT THIS SUITE OWNS AND WHAT IT DOES NOT. Commit 1cad17d threaded the
complete-type-name grammar through the TOP-LEVEL payload walk and stopped
there, deliberately: everything a tag's declared size covers was still read by
the LEGACY tag reader. This suite grades the MECHANISM that carries the same
grammar inside a value - a struct interior written as a nested tag list, a
container sitting inside one, and the inner tag an array of struct writes ahead
of its elements.

IT DOES NOT CLOSE CS-829 AND CLAIMS NOTHING ABOUT ANY POPULATION. CS-829 asks
for an equality over every site whose declared size could hold a tag list,
derived rather than transcribed, and the fences on that item in
``docs/GATED.md`` are untouched by anything here. What these arms establish is
narrower and is stated as such: the reader that already reads a (14,60) tag at
the top level now reads one inside a value, and the legacy pairs still read
what they read.

EVERY ARM RUNS ON A SYNTHETIC FIXTURE (``CLAUDE.md`` section 7). The struct
words in it are INVENTED - they appear in no save anywhere - which is the arm
that catches a reader keying on a transcribed vocabulary of observed words.

THE INTERIOR FIXTURE IS ITS OWN RECORD. The arms in
``tests/save/test_property_payload_14_60.py`` assert against the scalar actor
and the component by name, and growing either would move assertions this file
does not own.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from types import MappingProxyType
from typing import Final

import pytest

from clockspeed.save import objects
from clockspeed.save.chunks import decompress_body
from clockspeed.save.header import HeaderError, SaveHeader, parse_header
from tests.save import reach_guard, synthetic, test_properties

#: The pair under test, spelled once.
HEADER_VERSION: Final = 14
SAVE_VERSION: Final = 60


def _read(save: synthetic.SyntheticSave, instance: str) -> objects.PropertyResult:
    """Decode one named record of a fixture under the fixture's own pair.

    Args:
        save: The fixture.
        instance: The instance name of the record to read.

    Returns:
        The result, diagnostics included.
    """
    parsed = parse_header(save.blob)
    body = decompress_body(
        save.blob, parsed.body_offset, header_version=parsed.header_version
    ).payload
    table = objects.parse_body(
        body,
        save_version=parsed.save_version,
        header_version=parsed.header_version,
        known_classes=None,
        registry_incomplete=False,
    )
    record = next(rec for rec in table.records if rec.instance_name == instance)
    return objects.read_properties(
        body,
        record,
        None,
        save_version=table.save_version,
        header_version=table.header_version,
    )


def _struct_result() -> objects.PropertyResult:
    """The (14,60) record carrying the struct and the array of struct.

    Returns:
        Its decoded result.
    """
    return _read(synthetic.SAVE_LEVELLED_DECODABLE_TYPE_TREE, synthetic.TREE_STRUCT_INSTANCE)


# ---------------------------------------------------------------------------
# Section 1. A struct interior at (14,60)
# ---------------------------------------------------------------------------


def test_a_14_60_struct_interior_decodes_its_nested_tags() -> None:
    """THE ARM THAT FAILS FIRST. The interior walk read the legacy tag shape.

    ``_walk_struct_tags`` called ``_read_tag_header`` unconditionally, so an
    interior written in the complete-type-name grammar reached a parameter
    count where the legacy reader expected an int32 size and a guid flag. The
    tag still read at the TOP level, so the payload did not break - the
    interior simply never came back, which is the silent half.
    """
    result = _struct_result()
    assert result.struct_tag_count == 1, "one top-level struct tag in this fixture"
    assert len(result.struct_interiors) == 1, "its interior did not read"
    interior = result.struct_interiors[0]
    assert interior.struct_word == synthetic.TREE_STRUCT_WORD
    assert interior.form == objects.STRUCT_FORM_TAG_LIST
    assert interior.properties[synthetic.TREE_STRUCT_INT_NAME] == synthetic.TREE_STRUCT_INT_VALUE
    assert interior.properties[synthetic.TREE_STRUCT_STR_NAME] == synthetic.TREE_STRUCT_STR_VALUE


def test_a_14_60_struct_interior_reports_no_disagreement() -> None:
    """The redundancy oracle stays quiet on a fixture the reader reads.

    A DISAGREEMENT IS THE ORACLE FIRING, not a cosmetic count: it says the
    reader is not where it believes it is. An interior repair that raised it
    would have made something worse, so the count is asserted rather than
    watched.
    """
    result = _struct_result()
    assert result.disagreeing_value_count == 0
    interior = result.struct_interiors[0]
    assert interior.disagreed == 0
    assert interior.unmeasured == 0


def test_a_container_inside_a_14_60_struct_interior_reads_its_element_words() -> None:
    """The element words come from the NESTED type name inside an interior too.

    THE ARM THAT DISTINGUISHES THIS FROM A TAG-HEADER FIX. An interior whose
    tag headers read correctly still returns no container value if the element
    words are re-read from the legacy tag-extra run, because at this pair that
    run is the type name's parameter count.
    """
    interior = _struct_result().struct_interiors[0]
    container = interior.properties[synthetic.TREE_STRUCT_MAP_NAME]
    assert isinstance(container, objects.ContainerValue)
    assert container.type_word == synthetic.TREE_MAP_TYPE_WORD
    assert container.element_words == synthetic.TREE_MAP_ELEMENT_WORDS
    assert container.element_count == 1


def test_a_struct_nested_inside_a_14_60_interior_decodes_at_depth_one() -> None:
    """Depth 2 of the walk - a struct inside a struct.

    THE STRUCT WORD IS A TYPE-NAME PARAMETER AT EVERY DEPTH, so an interior
    that reached its nested struct through ``_struct_word_of_tag`` would read a
    parameter count as a string length prefix. ``_fold_struct_tag``'s docstring
    already names that as the dangerous case at the top level; this asserts the
    same thing one level in.
    """
    interior = _struct_result().struct_interiors[0]
    nested = interior.properties[synthetic.TREE_NESTED_STRUCT_NAME]
    assert isinstance(nested, objects.StructValue)
    assert nested.struct_word == synthetic.TREE_NESTED_STRUCT_WORD
    assert nested.depth == 1
    assert nested.properties[synthetic.TREE_NESTED_INT_NAME] == synthetic.TREE_NESTED_INT_VALUE


# ---------------------------------------------------------------------------
# Section 2. An array of struct at (14,60)
# ---------------------------------------------------------------------------


def test_a_14_60_array_of_struct_carries_no_inner_tag() -> None:
    """The elements follow the count directly, and no struct word is published.

    THE BRIEF THIS SLICE WAS DISPATCHED WITH SAID THE OPPOSITE - that the inner
    tag is present at this pair as a recursive type name whose one parameter is
    the struct word. It is not present at all. Measured read-only over every
    (14,60) save in the library: 6198 array-of-struct tags, of which walking
    ``count`` element tag lists from the byte after the count closes the value
    exactly on 6187, where reading an inner tag of EITHER grammar reads 0.

    ``struct_word`` IS THEREFORE None AND THAT IS THE HONEST ANSWER. The word
    is in the bytes, one level below ``StructProperty`` in the tag's own type
    name, and reading a struct word out of a type name is CS-829's measurement
    rather than this slice's - ``_read_type_name`` hands back only the top
    level for exactly that reason.
    """
    result = _struct_result()
    container = result.properties[synthetic.TREE_ARRAY_NAME]
    assert isinstance(container, objects.ContainerValue)
    assert container.type_word == synthetic.TREE_ARRAY_TYPE_WORD
    assert container.element_words == (synthetic.TREE_STRUCT_TYPE_WORD,)
    assert container.struct_word is None
    assert container.element_count == len(synthetic.TREE_ARRAY_ELEMENTS)


def test_a_14_60_array_of_struct_carrying_an_inner_tag_is_not_read_by_grammar() -> None:
    """THE NEGATIVE CONTROL, AND WHAT IT DOES NOT ESTABLISH.

    The fixture writes the inner tag the legacy grammar carries, spelled in the
    tree grammar - the shape this slice's brief predicted. No real (14,60)
    array carries one, so the element tag lists must NOT close over it, and
    ``ELEMENT_SHAPE_SELF_DELIMITING`` is the shape whose closing is evidence
    about bytes rather than about arithmetic.

    THE CONTAINER IS NOW REFUSED OUTRIGHT, AND THIS ASSERTION WAS CHANGED
    RATHER THAN REPAIRED AROUND. Its first version asserted that the container
    was STILL PUBLISHED, under a derived width, and called that stating the
    limit plainly. The limit was worse than stated: the fixture's tag carries
    the native-serialize bit, so the save's own writer had said the value did
    not go through the tagged-property path - and the decode published an
    element partition derived by dividing the region by the declared count
    anyway, with no warning and no count. Nothing distinguished that width from
    one read out of the bytes. ``objects._decode_container`` now refuses it,
    which is non-negotiable 7's flag and skip.

    WHAT STILL GRADES THE GRAMMAR IS THE PAIR OF FIXTURES, not this arm alone:
    ``tests/save/test_element_framing_refusals.py`` writes these same bytes
    with the bit CLEAR and requires the derived width to publish there, so the
    refusal below is evidence about the bit and the closing is evidence about
    the grammar.
    """
    payload = synthetic.type_tree_array_payload_with_an_inner_tag()
    record = objects.ObjectRecord(
        kind=objects.KIND_COMPONENT,
        type_path=synthetic.TREE_DECODABLE_COMPONENT_CLASS_PATH,
        root_object=synthetic.TREE_DECODABLE_ROOT,
        instance_name=synthetic.TREE_DECODABLE_COMPONENT_INSTANCE,
        transform=None,
        parent=synthetic.TREE_DECODABLE_INSTANCE,
        object_type=0,
        was_placed_in_level=0,
        body_offset=0,
        body_length=len(payload),
    )
    result = objects.read_properties(
        payload, record, None, save_version=SAVE_VERSION, header_version=HEADER_VERSION
    )
    assert synthetic.TREE_ARRAY_NAME not in result.properties, (
        "the element tag lists closed over an inner tag no (14,60) save writes, "
        "or a derived width published a partition the tag said was not there"
    )
    assert result.unmeasured_value_count == 1, (
        "the refusal was not flagged, so the container was skipped in silence"
    )
    assert objects.WARN_UNMEASURED_PROPERTY_TYPE in {warning.code for warning in result.warnings}


def test_a_14_60_struct_element_is_bounded_by_its_own_tag_list() -> None:
    """The elements close by GRAMMAR, not by division - CS-830's distinction.

    ``ELEMENT_SHAPE_SELF_DELIMITING`` is the only one of the three shapes whose
    closing is evidence about the bytes. The fixture writes two elements of
    DIFFERENT lengths precisely so a uniform width could not rescue a wrong
    reading and be mistaken for one.
    """
    container = _struct_result().properties[synthetic.TREE_ARRAY_NAME]
    assert isinstance(container, objects.ContainerValue)
    assert container.element_shape == objects.ELEMENT_SHAPE_SELF_DELIMITING
    lengths = [element.length for element in container.elements]
    assert len(lengths) == len(synthetic.TREE_ARRAY_ELEMENTS)
    assert lengths[0] != lengths[1], "the fixture's two elements must differ in length"
    assert all(element.value is None for element in container.elements), (
        "a struct element comes back BOUNDED and UNREAD - reading it is a claim "
        "about the struct's own encoding, which the container framing does not earn"
    )


def test_a_bounded_14_60_struct_element_decodes_through_the_stated_seam() -> None:
    """``decode_struct_interior`` reads an element interior when told the pair.

    THE SEAM IS WHERE A CALLER HOLDING AN ELEMENT'S OWN BOUNDS ASKS. The
    container publishes the element bounded and unread; a caller that wants the
    interior asks here, and at this pair it has to be able to say which grammar
    the bytes are in.
    """
    save = synthetic.SAVE_LEVELLED_DECODABLE_TYPE_TREE
    parsed = parse_header(save.blob)
    body = decompress_body(
        save.blob, parsed.body_offset, header_version=parsed.header_version
    ).payload
    container = _struct_result().properties[synthetic.TREE_ARRAY_NAME]
    assert isinstance(container, objects.ContainerValue)
    decoded = [
        objects.decode_struct_interior(
            body,
            synthetic.TREE_ELEMENT_STRUCT_WORD,
            element.start,
            element.start + element.length,
            type_tree=True,
        )
        for element in container.elements
    ]
    assert all(one is not None for one in decoded), "an element interior did not read"
    values = [one.properties[synthetic.TREE_ELEMENT_INT_NAME] for one in decoded if one is not None]
    assert tuple(values) == synthetic.TREE_ELEMENT_INT_VALUES


def test_a_struct_nested_inside_a_14_60_element_interior_decodes() -> None:
    """Depth 2 INSIDE a container element, which a prototype reported empty.

    THE MERGER'S PROTOTYPE MEASURED ZERO NESTED STRUCTS INSIDE ELEMENT
    INTERIORS on the real world and could not say whether that was the corpus
    or the prototype. This arm settles what the READER does: given bytes that
    carry one, it reads it. It says nothing about how many the real world has.
    """
    save = synthetic.SAVE_LEVELLED_DECODABLE_TYPE_TREE
    parsed = parse_header(save.blob)
    body = decompress_body(
        save.blob, parsed.body_offset, header_version=parsed.header_version
    ).payload
    container = _struct_result().properties[synthetic.TREE_ARRAY_NAME]
    assert isinstance(container, objects.ContainerValue)
    last = container.elements[-1]
    interior = objects.decode_struct_interior(
        body,
        synthetic.TREE_ELEMENT_STRUCT_WORD,
        last.start,
        last.start + last.length,
        type_tree=True,
    )
    assert interior is not None
    nested = interior.properties[synthetic.TREE_NESTED_STRUCT_NAME]
    assert isinstance(nested, objects.StructValue)
    assert nested.properties[synthetic.TREE_NESTED_INT_NAME] == synthetic.TREE_NESTED_INT_VALUE


# ---------------------------------------------------------------------------
# Section 3. The legacy grammar is the default, and is unchanged
# ---------------------------------------------------------------------------


def test_the_stated_seam_still_defaults_to_the_legacy_grammar() -> None:
    """A caller naming no pair reads the legacy interior shape.

    WHY THE DEFAULT IS LOAD-BEARING rather than tidy: every caller of
    ``decode_struct_interior`` that predates this slice passes four positional
    arguments, so a default selecting the new grammar would silently change
    what all of them read. The (14,60) element read WITHOUT the keyword must
    therefore come back None.
    """
    save = synthetic.SAVE_LEVELLED_DECODABLE_TYPE_TREE
    parsed = parse_header(save.blob)
    body = decompress_body(
        save.blob, parsed.body_offset, header_version=parsed.header_version
    ).payload
    container = _struct_result().properties[synthetic.TREE_ARRAY_NAME]
    assert isinstance(container, objects.ContainerValue)
    first = container.elements[0]
    assert (
        objects.decode_struct_interior(
            body,
            synthetic.TREE_ELEMENT_STRUCT_WORD,
            first.start,
            first.start + first.length,
        )
        is None
    )


def test_the_14_60_scalar_record_is_untouched_by_the_interior_repair() -> None:
    """The record the top-level repair graded reads exactly what it did.

    THE REGRESSION GUARD FOR THE SIBLING SUITE'S POPULATION. An interior repair
    that moved what the scalar record publishes would be changing the thing
    commit 1cad17d measured, in the same breath as extending it.
    """
    result = _read(synthetic.SAVE_LEVELLED_DECODABLE_TYPE_TREE, synthetic.TREE_DECODABLE_INSTANCE)
    codes = {warning.code for warning in result.warnings}
    assert objects.WARN_UNPARSED_PROPERTY_PAYLOAD not in codes
    for name, value in synthetic.TREE_SCALAR_PROPERTIES.items():
        assert result.properties[name] == value


# ---------------------------------------------------------------------------
# Section 4. The library measurement this suite's fixtures were built from,
# RE-MEASURED rather than quoted
# ---------------------------------------------------------------------------
#
# WHY THIS SECTION EXISTS. Everything above runs on synthetic bytes, and the
# measurement that decided their SHAPE - that a (14,60) array of struct writes
# its elements straight after the count and carries no inner tag - lived only
# in a docstring and a comment. Nothing went red if the corpus answered
# differently. A fixture built from a measurement grades the reader against the
# fixture; it does not grade the measurement, and the measurement is the part
# that can go stale.
#
# COUNTS ONLY, AND SKIP-IF-ABSENT. No path, no world name, no instance name, no
# property name, no string, no value and no byte leaves the sweep - it returns
# integers and the type NAMES of any failure. The suite must pass on a machine
# with no game and no save, so an unreachable library skips.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _ArraySweep:
    """What one walk of the library's (14,60) arrays of struct counted.

    Attributes:
        saves: How many saves of this pair were walked.
        population: Array-of-struct tags whose container head opened.
        closed_at_zero: Of those, how many had their element tag lists close
            the value EXACTLY when walked from the byte after the count.
        refused: How many did not.
        inner_tag_accounted: How many carried a tree-grammar inner tag at that
            byte whose declared extent accounted for the element region.
        failures: The type names of anything that went wrong, judged and
            reduced to a name inside the sweep.
    """

    saves: int
    population: int
    closed_at_zero: int
    refused: int
    inner_tag_accounted: int
    failures: tuple[str, ...]


def _inner_tag_accounts_for_region(body: bytes, at: int, end: int) -> bool:
    """Whether a TREE-grammar inner tag at ``at`` covers the element region.

    THE LEGACY SHAPE SPELLED IN THIS PAIR'S GRAMMAR - a property name, a type
    name whose ``StructProperty`` carries the struct word, an int32 extent and
    a flags byte. ``objects._read_array_struct_tag`` reads the legacy spelling
    and is not called at this pair; this is the other spelling, asked directly.

    Args:
        body: The decompressed body.
        at: The byte after the container's declared element count.
        end: The first byte past the element region.

    Returns:
        Whether such a tag reads there AND accounts for the region exactly.
    """
    name = objects._payload_text(body, at, end)  # noqa: SLF001
    if name is None:
        return False
    read = objects._read_tag_and_words(body, name[1], end, type_tree=True)  # noqa: SLF001
    if read is None:
        return False
    return read[1] + read[2] == end


def _array_of_struct_sites(body: bytes, at: int, end: int) -> tuple[tuple[int, int, int], ...]:
    """Every top-level array-of-struct in one payload, as element-region bounds.

    IT WALKS WITH THE SHIPPED READER AND HOLDS NO WIDTH OF ITS OWN. The name
    read, the tag header, the container head and the tag-count ceiling are all
    shipped symbols; what this contributes is the loop.

    Args:
        body: The decompressed body.
        at: Where the payload's first tag begins.
        end: The first byte past the payload.

    Returns:
        One ``(count, elements_at, region_end)`` per array of struct whose
        container head opened. Empty when the walk breaks before a terminator.
    """
    sites: list[tuple[int, int, int]] = []
    cursor = at
    for _ in range(objects._MAX_TAGS_PER_PAYLOAD):  # noqa: SLF001
        name = objects._payload_text(body, cursor, end)  # noqa: SLF001
        if name is None:
            return tuple(sites)
        if name[0] == objects._PAYLOAD_TERMINATOR:  # noqa: SLF001
            return tuple(sites)
        read = objects._read_tag_and_words(body, name[1], end, type_tree=True)  # noqa: SLF001
        if read is None:
            return tuple(sites)
        type_word, value_at, size, _bit, words, _struct, _native = read
        if type_word == synthetic.TREE_ARRAY_TYPE_WORD and words == (
            synthetic.TREE_STRUCT_TYPE_WORD,
        ):
            opened = objects._open_container(body, type_word, words, value_at, size)  # noqa: SLF001
            if opened is not None:
                sites.append(opened)
        cursor = value_at + size
    return tuple(sites)


def _elements_close_from(body: bytes, count: int, at: int, end: int) -> bool:
    """Whether ``count`` element tag lists consume ``at`` to ``end`` exactly.

    Args:
        body: The decompressed body.
        count: The element count the container declared.
        at: Where the walk starts.
        end: The first byte past the element region.

    Returns:
        Whether the walk closed exactly.
    """
    return (
        objects._walk_elements(  # noqa: SLF001
            body,
            (synthetic.TREE_STRUCT_TYPE_WORD,),
            at,
            end,
            count,
            (None,),
            type_tree=True,
        )
        is not None
    )


def _payload_start(body: bytes, record: objects.ObjectRecord) -> int | None:
    """Where one (14,60) record's first property tag begins.

    Args:
        body: The decompressed body.
        record: The record.

    Returns:
        The offset, or None when the head does not read.
    """
    end = record.body_offset + record.body_length
    if record.body_length == 0:
        return None
    start = (
        objects._skip_actor_head(body, record.body_offset, end)  # noqa: SLF001
        if record.kind == objects.KIND_ACTOR
        else record.body_offset
    )
    if start is None:
        return None
    lead = start + objects.PAYLOAD_TAG_LEAD_BYTES
    return lead if lead <= end else None


def _tally_one_save(data: bytes, parsed: SaveHeader, into: list[int]) -> None:
    """Walk one save's records, adding to the running counts.

    Args:
        data: The whole save blob.
        parsed: Its parsed header.
        into: The four running counts, mutated in place.
    """
    body = decompress_body(data, parsed.body_offset, header_version=parsed.header_version).payload
    table = objects.parse_body(
        body,
        save_version=parsed.save_version,
        header_version=parsed.header_version,
        known_classes=None,
        registry_incomplete=False,
    )
    for record in table.records:
        start = _payload_start(body, record)
        if start is None:
            continue
        end = record.body_offset + record.body_length
        for count, elements_at, region_end in _array_of_struct_sites(body, start, end):
            into[0] += 1
            if _elements_close_from(body, count, elements_at, region_end):
                into[1] += 1
            else:
                into[2] += 1
            if _inner_tag_accounts_for_region(body, elements_at, region_end):
                into[3] += 1


def _sweep_the_library_arrays() -> _ArraySweep | None:
    """Walk every (14,60) save once and return COUNTS ONLY.

    IT CONTAINS ``Exception`` AND ``SystemExit``, AND STOPS THERE, on the terms
    ``tests/save/test_container_elements.py`` argues at length: a save path, a
    body and a property name are things pytest renders out of a frame it
    unwinds, and ``path.read_bytes()`` is a bound method whose ``self`` IS the
    save path. ``KeyboardInterrupt`` is deliberately left free to unwind.

    Returns:
        The sweep, or None when no save library is reachable.
    """
    saves = test_properties._library_save_paths()  # noqa: SLF001
    if not saves:
        return None

    walked = 0
    counts = [0, 0, 0, 0]
    failures: list[str] = []
    for path in saves:
        try:
            data = path.read_bytes()
            parsed = parse_header(data)
        except (OSError, HeaderError):
            # The two EXPECTED failures - an unreadable file, and a save of a
            # version this project does not parse. The library holds both.
            continue
        except (Exception, SystemExit) as exc:
            failures.append(type(exc).__name__)
            continue
        if (parsed.header_version, parsed.save_version) != (HEADER_VERSION, SAVE_VERSION):
            continue
        try:
            _tally_one_save(data, parsed, counts)
        except (Exception, SystemExit) as exc:
            # BROAD BY DESIGN: a narrower catch lets an unexpected type escape
            # carrying the save bytes, which is the leak this containment closes.
            failures.append(type(exc).__name__)
            continue
        walked += 1
    return _ArraySweep(
        saves=walked,
        population=counts[0],
        closed_at_zero=counts[1],
        refused=counts[2],
        inner_tag_accounted=counts[3],
        failures=tuple(sorted(set(failures))),
    )


@lru_cache(maxsize=1)
def _array_sweep() -> _ArraySweep | None:
    """The sweep, walked once per session.

    Returns:
        The sweep, or None when no save library is reachable.
    """
    return _sweep_the_library_arrays()


def _sweep_or_skip() -> _ArraySweep:
    """Fetch the sweep, skipping when this machine cannot grade it.

    THE FAILURE ASSERTION COMES FIRST so an unreadable library reddens rather
    than skipping quietly, and "absent" has to mean absent of anything
    gradeable rather than absent of files.

    Returns:
        The sweep.
    """
    sweep = _array_sweep()
    if sweep is None:
        pytest.skip("no save library on this machine - the (14,60) arrays are not gradeable here")
    assert sweep.failures == (), f"failures walking real bodies: {sweep.failures}"
    if sweep.saves == 0:
        pytest.skip("the save library holds no save of this pair - not gradeable here")
    return sweep


def test_the_inner_tag_reader_finds_one_when_a_payload_carries_one() -> None:
    """THE CONTROL THE LIBRARY ZERO BELOW IS WORTHLESS WITHOUT.

    An oracle that cannot observe its subject reports absence for that reason
    alone, and "the inner-tag read found none" and "the inner-tag read never
    worked" are the same output. This runs the same two helpers over the
    synthetic payload that DOES carry an inner tag, so the zero below is a
    statement about the corpus rather than about the helper.

    NEEDS NO SAVE LIBRARY.
    """
    payload = synthetic.type_tree_array_payload_with_an_inner_tag()
    sites = _array_of_struct_sites(payload, objects.PAYLOAD_TAG_LEAD_BYTES, len(payload))
    assert len(sites) == 1, "the control payload's one array of struct was not found"
    count, elements_at, region_end = sites[0]
    assert _inner_tag_accounts_for_region(payload, elements_at, region_end), (
        "the inner-tag reader did not find the inner tag this payload writes, so "
        "the library zero below would be a measurement of the reader"
    )
    assert not _elements_close_from(payload, count, elements_at, region_end), (
        "the element tag lists closed over an inner tag, so the two readings do "
        "not discriminate and neither result means anything"
    )


def test_the_library_14_60_arrays_of_struct_are_shaped_the_way_the_fixtures_say() -> None:
    """The measurement the fixtures above were built from, RE-MEASURED.

    THREE CLAIMS, EACH GUARDED AGAINST BEING VACUOUS. The population must be
    non-empty. The offset-zero walk must close on some of it - that is the
    known-good control for the walk itself, and it is what makes the third
    claim mean anything. And no array may carry a tree-grammar inner tag whose
    extent accounts for the element region, which is the shape this pair was
    predicted to have and measured not to.

    NO COUNT IS ASSERTED AND NONE IS WRITTEN HERE. The operator plays this
    game, so every figure moves on the next autosave - ``CLAUDE.md`` section 4.
    What is held is the SHAPE: a partition that covers the population, a
    non-empty strong side, and a zero with a live control behind it.

    WHAT THE OFFSET-ZERO CLOSE IS AND IS NOT EVIDENCE FOR, measured on the run
    that filed this arm and stated here because the docstrings around it invite
    the stronger reading. Starting the SAME walk at a later tag boundary inside
    the first element also closes exactly, on much of the population - a tag
    list walked from any of its own tag boundaries still ends on the same
    terminator, so shifting the start by a whole tag is invisible to a walk that
    only has to land on the end. The close is therefore evidence that the
    elements ARE tag lists. It is NOT evidence that they begin where the walk
    began, and this arm claims only the first.

    SKIP-IF-ABSENT, COUNTS ONLY.
    """
    sweep = _sweep_or_skip()

    assert sweep.population > 0, (
        "the library holds no (14,60) array of struct at all, so every claim "
        "below is vacuous. Either the walk stopped reaching them or the "
        "population is gone"
    )
    assert sweep.closed_at_zero > 0, (
        "not one array's element tag lists closed when walked from the byte "
        "after the count, so the shape every fixture in this file is built on "
        "is not the shape the corpus writes"
    )
    assert sweep.closed_at_zero + sweep.refused == sweep.population, (
        "the closings and the refusals do not partition the population, so the "
        "sweep is counting something twice or dropping something"
    )
    assert sweep.inner_tag_accounted == 0, (
        "an array of struct carries a tree-grammar inner tag accounting for its "
        "element region, which is the shape this pair was measured NOT to write "
        "- the reader skips it, so its elements would be read one tag late"
    )


def test_the_reach_guard_catches_a_spliced_uncontained_helper(tmp_path: Path) -> None:
    """The guard's POWER over THIS module, forced rather than asserted about.

    THE SUITE-WIDE TEST PROVES THE GUARD IS APPLIED HERE; THIS PROVES IT BITES
    HERE. The two are not the same claim, and a module that satisfied the first
    by pasting declarations at its foot would look identical to one the guard
    can actually catch something in.

    THE SPLICE IS THE KNOWN-BAD SHAPE - the locators and the glob outside every
    ``try``, so a failure unwinds through a frame holding the account
    directory, whose NAME is a platform account id (``CLAUDE.md`` section 2,
    non-negotiable 3). It is run against a COPY in ``tmp_path``, so nothing
    mutates a tracked file and no restore is needed.

    NEEDS NO SAVE LIBRARY - it is a claim about this file's source.
    """
    spliced = tmp_path / "spliced.py"
    spliced.write_text(
        Path(__file__).read_text(encoding="utf-8") + "\n\ndef _spliced_uncontained_helper():\n"
        '    """A helper carrying the known-bad shape."""\n'
        "    root = locate.resolve_save_root()\n"
        "    account = locate.resolve_account_dir(root)\n"
        '    for path in sorted(account.glob("*.sav")):\n'
        "        try:\n"
        "            return parse_header(path.read_bytes())\n"
        "        except (OSError, HeaderError):\n"
        "            continue\n"
        "    return None\n",
        encoding="utf-8",
    )

    with pytest.raises(AssertionError) as caught:
        reach_guard._assert_library_reach_is_declared(  # noqa: SLF001
            spliced, graded=_GRADED_LIBRARY_REACH, exempt=_EXEMPT_LIBRARY_REACH
        )
    assert "_spliced_uncontained_helper" in str(caught.value)

    # THE POSITIVE CONTROL. The same guard over the unspliced source passes, so
    # the red above is the splice and not a guard that rejects everything.
    reach_guard._assert_library_reach_is_declared(  # noqa: SLF001
        Path(__file__), graded=_GRADED_LIBRARY_REACH, exempt=_EXEMPT_LIBRARY_REACH
    )


# ---------------------------------------------------------------------------
# The library-reach declarations - CS-471. The guard is owned by ``reach_guard``
# and applied across this package by the suite-wide test in ``test_reach_guard``,
# which walks the package DIRECTORY rather than a list, so this module came into
# scope the moment its sweep held a save path.
# ---------------------------------------------------------------------------

#: The one helper here that holds a real save path. Keyed by the function's own
#: ``__name__`` rather than by a string, so a rename moves the declaration with
#: it instead of leaving a reason for a function that no longer exists.
_GRADED_LIBRARY_REACH: Final = MappingProxyType(
    {_sweep_the_library_arrays.__name__: reach_guard.REACH_READS_THE_LIBRARY}
)

#: Touches a primitive WITHOUT consuming a real save path, name to why. EMPTY,
#: and the emptiness is asserted rather than assumed: every primitive call in
#: this module is the one read inside the sweep above.
_EXEMPT_LIBRARY_REACH: Final[Mapping[str, str]] = MappingProxyType({})
