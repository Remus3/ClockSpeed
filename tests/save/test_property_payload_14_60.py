"""The (14,60) property payload grammar - CS-G05's repair.

WHAT THIS SUITE EXISTS TO STOP COMING BACK. ``docs/GATED.md`` recorded under
CS-G05 that every record of every (14,60) save decodes ZERO property tags and
that the pair was therefore "the CONTROL" - a save that could not exercise the
decoder at all. That premise was WRONG. A third-party map tool reads container
contents and machine settings out of the same file on the same machine, so the
property data is in the file and is decodable; the zero was a defect in this
reader, not a property of the format.

WHAT THE DEFECT WAS, at the two offsets that localised it:

- ONE OPAQUE BYTE stands between a payload's head and its first tag. On an
  actor that is just past the component list, on a component it is the
  payload's first byte. The reader stepped straight from the head to the tag
  name and read that byte as the top of a length prefix.
- THE TAG CARRIES A RECURSIVE TYPE NAME rather than a type word plus
  per-type extra strings, and closes with a FLAGS BYTE rather than a
  guid-present flag. ``ArrayProperty`` at this pair spells its element type as
  a nested type name, not as a string sitting between the index field and the
  guid flag - and there is no index field.

EVERY ARM HERE RUNS ON A SYNTHETIC FIXTURE. The suite must stay green on a
machine with no game and no save (``CLAUDE.md`` section 7), so the grading
population is ``synthetic.SAVE_LEVELLED_DECODABLE_TYPE_TREE`` - hand-authored
bytes, not a slice of anything real. The real-world probe that pinned the
grammar was a read-only measurement run OUTSIDE the suite and reported as
counts; its numbers are in the CS-G05 entry, not here, because a count in a
test is a count that goes stale.

THE LEGACY PAIRS ARE GRADED TOO, and that is the point of section 3. A repair
that made (14,60) read by changing what (14,52) does would be a regression
wearing a fix's clothes, so the (14,52) fixture is asserted to decode exactly
what it decoded before.
"""

from __future__ import annotations

from typing import Final

import pytest

from clockspeed.save import objects
from clockspeed.save.chunks import decompress_body
from clockspeed.save.header import parse_header
from clockspeed.save.world import load_world_from_bytes
from tests.save import synthetic

# ---------------------------------------------------------------------------
# Section 1. The walk, and what it hands the decoder
# ---------------------------------------------------------------------------

#: The pair under test, spelled once. Both scalars are threaded separately into
#: the reader - see ``world._walk_body`` on why deriving either from the other
#: is correct on every real file and wrong on a crossed fixture.
HEADER_VERSION: Final = 14
SAVE_VERSION: Final = 60

#: The raw object-type discriminator a COMPONENT record carries. Spelled here
#: because ``objects`` keeps the mapping private and exports no constant for it;
#: a record built by hand still has to state it.
_COMPONENT_DISCRIMINATOR: Final = 0


def _walked(save: synthetic.SyntheticSave) -> tuple[bytes, objects.ObjectTable]:
    """Decompress one fixture and walk its record table.

    Args:
        save: The fixture.

    Returns:
        The decompressed body and the walked table.
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
    return (body, table)


def _decoded(save: synthetic.SyntheticSave, instance: str) -> objects.PropertyResult:
    """Read one named record's properties under the fixture's own pair.

    Args:
        save: The fixture.
        instance: The instance name of the record to read.

    Returns:
        The result, diagnostics included.
    """
    body, table = _walked(save)
    record = next(rec for rec in table.records if rec.instance_name == instance)
    return objects.read_properties(
        body,
        record,
        None,
        save_version=table.save_version,
        header_version=table.header_version,
    )


def test_a_14_60_actor_payload_decodes_its_string_and_int_tags() -> None:
    """The two scalar tags come back, and no unparsed-payload warning does.

    THE ARM THAT FAILS FIRST. Before the repair this record reported
    ``WARN_UNPARSED_PROPERTY_PAYLOAD`` and an empty mapping, which is exactly
    what CS-G05 mistook for a property of the format.
    """
    result = _decoded(
        synthetic.SAVE_LEVELLED_DECODABLE_TYPE_TREE, synthetic.TREE_DECODABLE_INSTANCE
    )
    codes = {warning.code for warning in result.warnings}
    assert objects.WARN_UNPARSED_PROPERTY_PAYLOAD not in codes
    assert result.properties[synthetic.TREE_INT_NAME] == synthetic.TREE_INT_VALUE
    assert result.properties[synthetic.TREE_STR_NAME] == synthetic.TREE_STR_VALUE


def test_a_14_60_component_payload_decodes_with_no_actor_head() -> None:
    """A component's payload opens with the opaque byte and then its tags.

    THE OTHER BRANCH. An actor's head is stepped over before the byte; a
    component has no head at all, so the byte is the payload's first. Reading
    one kind as the other desynchronises on the first tag rather than failing
    at the head, which is why this is a separate arm.
    """
    result = _decoded(
        synthetic.SAVE_LEVELLED_DECODABLE_TYPE_TREE,
        synthetic.TREE_DECODABLE_COMPONENT_INSTANCE,
    )
    codes = {warning.code for warning in result.warnings}
    assert objects.WARN_UNPARSED_PROPERTY_PAYLOAD not in codes
    assert dict(result.properties) == dict(synthetic.TREE_COMPONENT_PROPERTIES)


def test_a_14_60_container_tag_yields_its_element_words_from_the_type_name() -> None:
    """The map's element words come from the NESTED type name, not a tag extra.

    THE ARM THAT DISTINGUISHES THIS REPAIR FROM AN OFF-BY-ONE. Skipping one
    byte is enough to reach the first tag NAME; it is not enough to read a
    container, whose key and value words no longer sit between the index field
    and the guid flag. A reader that only gained the byte returns no container
    value at all.
    """
    result = _decoded(
        synthetic.SAVE_LEVELLED_DECODABLE_TYPE_TREE, synthetic.TREE_DECODABLE_INSTANCE
    )
    container = result.properties[synthetic.TREE_MAP_NAME]
    assert isinstance(container, objects.ContainerValue)
    assert container.type_word == "MapProperty"
    assert container.element_words == synthetic.TREE_MAP_ELEMENT_WORDS
    assert container.element_count == 1


def test_the_opaque_lead_byte_is_load_bearing() -> None:
    """Removing the lead byte from the fixture breaks the walk.

    A FIXTURE THAT READS EITHER WAY GRADES NOTHING. If the payload decoded
    without its lead byte, the byte would be a claim this suite makes rather
    than one the bytes make - so the arm mutates the FIXTURE and asserts the
    reader refuses it.
    """
    payload = synthetic.TREE_DECODABLE_COMPONENT_PAYLOAD
    assert payload.startswith(synthetic.TYPE_TREE_PAYLOAD_LEAD)
    record = objects.ObjectRecord(
        kind=objects.KIND_COMPONENT,
        type_path=synthetic.TREE_DECODABLE_COMPONENT_CLASS_PATH,
        root_object=synthetic.TREE_DECODABLE_ROOT,
        instance_name=synthetic.TREE_DECODABLE_COMPONENT_INSTANCE,
        transform=None,
        parent=synthetic.TREE_DECODABLE_INSTANCE,
        object_type=_COMPONENT_DISCRIMINATOR,
        was_placed_in_level=0,
        body_offset=0,
        body_length=len(payload) - len(synthetic.TYPE_TREE_PAYLOAD_LEAD),
    )
    stripped = payload[len(synthetic.TYPE_TREE_PAYLOAD_LEAD) :]
    result = objects.read_properties(
        stripped, record, None, save_version=SAVE_VERSION, header_version=HEADER_VERSION
    )
    codes = {warning.code for warning in result.warnings}
    assert objects.WARN_UNPARSED_PROPERTY_PAYLOAD in codes
    assert not result.properties


# ---------------------------------------------------------------------------
# Section 2. The flags byte
# ---------------------------------------------------------------------------


def test_a_bool_tag_carries_its_true_value_in_the_flags_byte() -> None:
    """The 0x10 bit IS the bool's value, and there is no separate value byte.

    MEASURED ON THE REAL LIBRARY as 176 tags, all ``BoolProperty`` and all
    0x10, against 0 bools carrying any other nonzero flag - and a reading that
    gave the bool its own byte AND a flags byte desynchronises on the tag after
    it. The fixture writes both polarities so a reader that hardcoded either
    answer fails one of them.
    """
    result = _decoded(
        synthetic.SAVE_LEVELLED_DECODABLE_TYPE_TREE, synthetic.TREE_DECODABLE_INSTANCE
    )
    assert result.properties[synthetic.TREE_BOOL_TRUE_NAME] is True
    assert result.properties[synthetic.TREE_BOOL_FALSE_NAME] is False


@pytest.mark.parametrize("flags", [0x02, 0x04, 0x20, 0x40, 0x80])
def test_an_unmeasured_flags_bit_is_flagged_rather_than_guessed(flags: int) -> None:
    """A bit this project has not measured refuses the payload.

    NON-NEGOTIABLE 7, and the reason this is an arm rather than a comment. The
    real library sets only 0x01, 0x08 and 0x10 - 0x02 appears on NOT ONE of the
    9058 tags measured, so the width of whatever follows it is UNKNOWN. A
    reader that assumed a 16-byte guid there would publish values read from the
    wrong offset on the first save that carried one, which is the silently
    wrong answer the non-negotiable rules out.
    """
    assert flags & objects.MEASURED_TAG_FLAG_MASK != flags
    payload = synthetic.type_tree_payload_with_flags(flags)
    record = objects.ObjectRecord(
        kind=objects.KIND_COMPONENT,
        type_path=synthetic.TREE_DECODABLE_COMPONENT_CLASS_PATH,
        root_object=synthetic.TREE_DECODABLE_ROOT,
        instance_name=synthetic.TREE_DECODABLE_COMPONENT_INSTANCE,
        transform=None,
        parent=synthetic.TREE_DECODABLE_INSTANCE,
        object_type=_COMPONENT_DISCRIMINATOR,
        was_placed_in_level=0,
        body_offset=0,
        body_length=len(payload),
    )
    result = objects.read_properties(
        payload, record, None, save_version=SAVE_VERSION, header_version=HEADER_VERSION
    )
    codes = {warning.code for warning in result.warnings}
    assert objects.WARN_UNPARSED_PROPERTY_PAYLOAD in codes


def test_the_array_index_bit_consumes_four_bytes() -> None:
    """The 0x01 bit adds an int32 between the flags byte and the value.

    THE WEAKEST MEASUREMENT IN THIS SUITE, STATED AS SUCH. It rests on TWO
    real tags, both ``StructProperty`` at 0x09. What makes it more than a
    coincidence is that dropping the four bytes costs a whole record: the
    payload carrying them stops reading. The fixture reproduces that shape so
    the four bytes are graded on bytes this repository owns rather than only on
    a save that is not in it.
    """
    result = _decoded(
        synthetic.SAVE_LEVELLED_DECODABLE_TYPE_TREE, synthetic.TREE_DECODABLE_INSTANCE
    )
    codes = {warning.code for warning in result.warnings}
    assert objects.WARN_UNPARSED_PROPERTY_PAYLOAD not in codes
    assert result.properties[synthetic.TREE_INDEXED_NAME] == synthetic.TREE_INDEXED_VALUE


# ---------------------------------------------------------------------------
# Section 3. The legacy pairs are unchanged
# ---------------------------------------------------------------------------


def test_the_legacy_decodable_fixture_still_decodes_exactly_what_it_did() -> None:
    """(14,52) is untouched by the repair.

    THE REGRESSION GUARD. The new grammar is reached only through the pair
    table, so a dispatch mistake shows up here as the legacy fixture losing
    its values - which is the failure mode a repair to one pair is most likely
    to have.
    """
    result = _decoded(synthetic.SAVE_LEVELLED_DECODABLE, synthetic.DECODABLE_INSTANCE)
    codes = {warning.code for warning in result.warnings}
    assert objects.WARN_UNPARSED_PROPERTY_PAYLOAD not in codes
    assert dict(result.properties) == dict(synthetic.DECODABLE_PROPERTIES)


def test_a_caller_naming_no_pair_gets_the_legacy_grammar() -> None:
    """The version keywords are optional and default to the legacy reading.

    WHY IT MATTERS THAT THIS IS THE DEFAULT. Every existing caller passes
    three positional arguments, so a default that selected the new grammar
    would silently change what all of them read. The (14,60) fixture read
    WITHOUT its pair must therefore come back unparsed - the same answer the
    reader gave before the repair.
    """
    body, table = _walked(synthetic.SAVE_LEVELLED_DECODABLE_TYPE_TREE)
    record = next(
        rec
        for rec in table.records
        if rec.instance_name == synthetic.TREE_DECODABLE_COMPONENT_INSTANCE
    )
    codes = {warning.code for warning in objects.read_properties(body, record, None).warnings}
    assert objects.WARN_UNPARSED_PROPERTY_PAYLOAD in codes


def test_the_whole_world_model_publishes_the_14_60_properties() -> None:
    """The seam carries the pair from the walked table into the decode.

    THE ARM THAT GRADES THE PLUMBING RATHER THAN THE GRAMMAR. ``objects`` can
    read the pair perfectly and still publish nothing if ``world`` does not
    hand it over - the two facts only exist together in
    ``world._decode_properties``, which is the only scope holding both the
    decompressed body and the walked extents.
    """
    model = load_world_from_bytes(synthetic.SAVE_LEVELLED_DECODABLE_TYPE_TREE.blob)
    assert model.properties.unread_payload_count < len(model.properties.by_record_index)
    published = [
        entry
        for entry in model.properties.by_record_index.values()
        if synthetic.TREE_INT_NAME in entry.values
    ]
    assert len(published) == 1
    assert published[0].values[synthetic.TREE_INT_NAME] == synthetic.TREE_INT_VALUE
