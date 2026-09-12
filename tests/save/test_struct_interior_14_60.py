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

from typing import Final

from clockspeed.save import objects
from clockspeed.save.chunks import decompress_body
from clockspeed.save.header import parse_header
from tests.save import synthetic

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

    THE CONTAINER IS STILL PUBLISHED, UNDER A DERIVED WIDTH, AND THAT IS
    ASSERTED RATHER THAN HIDDEN. Two elements divide a region evenly, so
    ``ELEMENT_SHAPE_UNIFORM_WIDTH`` closes it whatever the bytes say - the limit
    ``objects.UNDISCRIMINATED_ELEMENT_SHAPES`` already records for CS-830. This
    arm therefore grades the GRAMMAR and states plainly that the fallback is
    not graded by it. Writing a fixture whose region failed to divide would
    make this arm green for an arithmetic reason of its own making, which is
    the same error one level down.
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
    container = result.properties[synthetic.TREE_ARRAY_NAME]
    assert isinstance(container, objects.ContainerValue)
    assert container.element_shape != objects.ELEMENT_SHAPE_SELF_DELIMITING, (
        "the element tag lists closed over an inner tag no (14,60) save writes, "
        "so the grammar is not what bounded them"
    )
    assert container.element_shape in objects.UNDISCRIMINATED_ELEMENT_SHAPES


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
