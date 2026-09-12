"""What the element and type-name grammars REFUSE, one arm per refusal.

EVERY ARM HERE WAS WRITTEN AGAINST A MUTATION THAT SURVIVED THE WHOLE SAVE
SUITE. A refusal is the half of a decoder nothing exercises by accident: the
happy path is walked by every fixture in the corpus, where the branch that says
"these bytes are not the ones I can read" is reached only by bytes somebody
wrote on purpose. Four mutations of that half were applied to
``clockspeed/save/objects.py`` and the save suite stayed green on three of them,
so the lines they changed were carrying the (14,60) element result with nothing
holding them up.

THE ARMS ARE NAMED FOR THE PROPERTY, NOT FOR THE MUTANT, and each docstring
names the mutation it was written to kill. A test named after a mutant stops
making sense the day the code around it is refactored; a test named after the
property it asserts survives the refactor and still kills the mutant.

EVERY NEGATIVE HAS A KNOWN-GOOD CONTROL BESIDE IT. An assertion that some bytes
are refused passes for free if the machinery under it is broken or if the bytes
are malformed for a second reason nobody intended, so each refusal arm asserts
the CLOSEST WELL-FORMED NEIGHBOUR reads. That neighbour is what makes the
refusal evidence about the one thing that was changed.

EVERY ARM IS SYNTHETIC - ``CLAUDE.md`` section 7 - and runs on a machine with
no game and no save. NOTHING HERE CLAIMS A POPULATION. The library-backed
re-measurement of the array-of-struct closings lives in
``tests/save/test_struct_interior_14_60.py``, beside the measurement it grades.
"""

from __future__ import annotations

import struct
from typing import Final

from clockspeed.save import objects
from tests.save import synthetic

#: The pair whose tag grammar this file exercises, spelled once.
HEADER_VERSION: Final = 14
SAVE_VERSION: Final = 60

#: A type word no save writes, for the arms that need an UNMEASURED type. It is
#: INVENTED rather than borrowed from a real unmeasured word, so the arm cannot
#: quietly stop grading the unmeasured route on the day some later slice
#: measures the word it borrowed.
UNMEASURED_WORD: Final = "SyntheticUnmeasuredProperty"

#: Names for the synthetic tags below. Invented, like every string here.
ARRAY_NAME: Final = "mSyntheticRefusalArray"
STRUCT_NAME: Final = "mSyntheticRefusalStruct"
STRUCT_WORD: Final = "SyntheticRefusalEntry"
DISAGREEING_NAME: Final = "mSyntheticRefusalDisagrees"
UNMEASURED_NAME: Final = "mSyntheticRefusalUnmeasured"

#: One element of an `IntProperty` array, and a region holding a whole one.
_INT_ELEMENT_BYTES: Final = 4


def _component_record(payload: bytes) -> objects.ObjectRecord:
    """A component record covering one whole synthetic payload.

    Args:
        payload: The payload bytes the record describes.

    Returns:
        The record, with the payload as its entire body.
    """
    return objects.ObjectRecord(
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


def _read_at_the_pair(payload: bytes) -> objects.PropertyResult:
    """Decode one synthetic (14,60) payload.

    Args:
        payload: The payload bytes.

    Returns:
        The result, diagnostics included.
    """
    return objects.read_properties(
        payload,
        _component_record(payload),
        None,
        save_version=SAVE_VERSION,
        header_version=HEADER_VERSION,
    )


def _int_array_payload(slack: int) -> bytes:
    """A (14,60) payload holding one `ArrayProperty` of one `IntProperty`.

    THE SLACK IS THE WHOLE VARIABLE. At zero the one element consumes the
    declared region exactly; above zero the region is longer than the element
    grammar accounts for, and `IntProperty` has no second element shape, so
    nothing may derive a width to cover the difference.

    Args:
        slack: How many bytes beyond the element the value declares.

    Returns:
        The payload bytes.
    """
    value = struct.pack("<i", 1) + b"\x00" * (_INT_ELEMENT_BYTES + slack)
    return synthetic.type_tree_property_payload(
        (
            synthetic.type_tree_property_tag(
                ARRAY_NAME,
                synthetic.type_name_tree(
                    synthetic.TREE_ARRAY_TYPE_WORD, ((synthetic.TREE_INT_TYPE_WORD, ()),)
                ),
                value,
                flags=synthetic.TAG_FLAGS_NONE,
            ),
        ),
        trailing=synthetic.DECODABLE_TRAILING_RUN,
    )


def _type_name_bytes(word: str, count: int, params: tuple[bytes, ...] = ()) -> bytes:
    """One recursive type name whose declared parameter count is STATED.

    ``synthetic.type_name_tree`` derives the count from the parameters it is
    given, which is the right rule for a fixture describing a real save and the
    wrong one for an arm about the count FIELD. This states the two separately
    so an arm can write a count the bytes do not back.

    Args:
        word: The type word.
        count: The int32 to write as the parameter count.
        params: The encoded nested names to write after it.

    Returns:
        The encoded name.
    """
    return synthetic.fstring(word) + struct.pack("<i", count) + b"".join(params)


def _scalar_name() -> bytes:
    """One well-formed nested name carrying no parameters of its own.

    Returns:
        The encoded name.
    """
    return _type_name_bytes(synthetic.TREE_INT_TYPE_WORD, 0)


# ---------------------------------------------------------------------------
# Section 1. An element walk must consume its region EXACTLY
# ---------------------------------------------------------------------------


def test_an_element_walk_that_stops_short_of_the_region_is_refused() -> None:
    """``_walk_elements`` closes on equality, and the equality is the whole result.

    THE MUTATION THIS KILLS: ``cursor == end`` loosened to ``cursor <= end`` at
    the end of ``objects._walk_elements``. It survived the entire save suite,
    and the function's own docstring says THE EXACT CLOSE IS THE WHOLE
    DISCRIMINATOR - every element framing this module accepts by grammar rests
    on a walk that had to land on the last byte and did.

    Under ``<=`` the short walk below comes back with one element and a region
    twice its length, which is the published-a-wrong-partition outcome
    non-negotiable 7 rules out.
    """
    region = b"\x00" * (_INT_ELEMENT_BYTES * 2)
    short = objects._walk_elements(  # noqa: SLF001
        region, (synthetic.TREE_INT_TYPE_WORD,), 0, len(region), 1, (None,)
    )
    assert short is None, (
        "one four-byte element was walked over an eight-byte region and the walk "
        "accepted it, so the element boundaries no longer have to agree with the "
        "region the tag declared"
    )

    exact = objects._walk_elements(  # noqa: SLF001
        region, (synthetic.TREE_INT_TYPE_WORD,), 0, _INT_ELEMENT_BYTES, 1, (None,)
    )
    assert exact is not None, "the control did not walk, so the refusal above grades nothing"
    assert len(exact) == 1


def test_a_container_whose_elements_stop_short_of_its_value_is_not_published() -> None:
    """The same refusal at the seam a consumer actually reads.

    THE ARM ABOVE CALLS THE WALK DIRECTLY AND THIS ONE DOES NOT, which is the
    reason both are here. A private-function arm pins the line; this pins the
    OUTCOME - that a container whose elements do not account for its declared
    value never reaches ``PropertyResult.properties`` at all.

    ``IntProperty`` is the element word deliberately: it has exactly one
    element shape, so the derived widths are not reachable and the refusal can
    only come from the walk. See ``objects._RAW_SHAPE_ELEMENT_WORDS``.
    """
    result = _read_at_the_pair(_int_array_payload(slack=_INT_ELEMENT_BYTES))
    assert ARRAY_NAME not in result.properties, (
        "a container whose one element covers half its declared region was published"
    )
    assert result.disagreeing_value_count == 1, (
        "the refusal was not routed to the disagreement counter, so a container "
        "framing that lost its place is being reported as unmodelled content"
    )

    control = _read_at_the_pair(_int_array_payload(slack=0))
    published = control.properties[ARRAY_NAME]
    assert isinstance(published, objects.ContainerValue), (
        "the control container did not decode, so the refusal above is not evidence about the slack"
    )
    assert published.element_shape == objects.ELEMENT_SHAPE_SELF_DELIMITING
    assert control.disagreeing_value_count == 0


# ---------------------------------------------------------------------------
# Section 2. A nested tag list must REFUSE a tag that does not read
# ---------------------------------------------------------------------------


def test_a_nested_tag_list_holding_a_tag_that_does_not_read_is_refused() -> None:
    """``_element_tag_list_end`` returns None rather than the offset it reached.

    THE MUTATION THIS KILLS: the ``if header is None: return None`` branch of
    ``objects._element_tag_list_end`` replaced by ``return cursor``. It
    survived the entire save suite, and it is a line THIS PAIR'S REPAIR
    CHANGED - the element tag list is the grammar the (14,60) array of struct
    closes on, so a tag list that reported a position for bytes it could not
    read would hand the element walk a boundary derived from nothing.

    THE BYTES: an int32 that a property name read takes as a two-byte string,
    then a single byte where a type name has to begin. The name reads; the tag
    after it cannot.
    """
    broken = struct.pack("<i", 2) + b"A\x00" + b"\xff"
    for type_tree in (False, True):
        assert (
            objects._element_tag_list_end(  # noqa: SLF001
                broken, 0, len(broken), type_tree=type_tree
            )
            is None
        ), (
            f"type_tree={type_tree}: a tag list reported a close for a tag that "
            "did not read, so the position it hands back came from nowhere"
        )

    closing = synthetic.type_tree_tag_list(
        (
            synthetic.type_tree_property_tag(
                synthetic.TREE_INT_NAME,
                synthetic.type_name_tree(synthetic.TREE_INT_TYPE_WORD),
                struct.pack("<i", synthetic.TREE_INT_VALUE),
            ),
        )
    )
    assert objects._element_tag_list_end(  # noqa: SLF001
        closing, 0, len(closing), type_tree=True
    ) == len(closing), "the control tag list did not close, so the refusals above grade nothing"


# ---------------------------------------------------------------------------
# Section 3. A type name's parameter count is BOUNDED in both directions
# ---------------------------------------------------------------------------


def test_a_type_name_declaring_a_negative_parameter_count_is_refused() -> None:
    """A negative count is refused rather than read as no parameters at all.

    THE MUTATION THIS KILLS: dropping ``count < 0`` from the guard in
    ``objects._read_type_name``. ``range`` of a negative number is empty, so
    without the guard a negative count reads as a scalar type name and the
    reader carries on from four bytes that said something it did not
    understand. Its status against the whole save suite was UNKNOWN when this
    arm was written - it had only ever been run against a narrow selection.
    """
    assert (
        objects._read_type_name(  # noqa: SLF001
            _type_name_bytes(synthetic.TREE_ARRAY_TYPE_WORD, -1),
            0,
            len(_type_name_bytes(synthetic.TREE_ARRAY_TYPE_WORD, -1)),
        )
        is None
    ), "a type name declaring a negative parameter count was read as a scalar name"

    zero = _type_name_bytes(synthetic.TREE_ARRAY_TYPE_WORD, 0)
    read = objects._read_type_name(zero, 0, len(zero))  # noqa: SLF001
    assert read is not None, "the control name did not read, so the refusal grades nothing"
    assert read[0] == synthetic.TREE_ARRAY_TYPE_WORD
    assert read[1] == ()


def test_a_type_name_declaring_more_parameters_than_the_bound_is_refused() -> None:
    """The upper bound refuses a name whose parameters are all WELL FORMED.

    THE MUTATION THIS KILLS: dropping ``count > _MAX_TYPE_NAME_PARAMS`` from
    the same guard. A truncated name refuses for a second reason, so an arm
    that wrote a huge count over short bytes would pass with the bound gone.
    This writes every declared parameter out in full, so the ONLY thing
    refusing the first name is the bound, and the control one under it proves
    the bytes themselves are readable.
    """
    cap = objects._MAX_TYPE_NAME_PARAMS  # noqa: SLF001

    over = _type_name_bytes(
        synthetic.TREE_ARRAY_TYPE_WORD, cap + 1, tuple(_scalar_name() for _ in range(cap + 1))
    )
    assert objects._read_type_name(over, 0, len(over)) is None, (  # noqa: SLF001
        "a type name nested one parameter past the bound was read, so the bound "
        "no longer stops a corrupt count from spinning"
    )

    at_cap = _type_name_bytes(
        synthetic.TREE_ARRAY_TYPE_WORD, cap, tuple(_scalar_name() for _ in range(cap))
    )
    read = objects._read_type_name(at_cap, 0, len(at_cap))  # noqa: SLF001
    assert read is not None, (
        "the name AT the bound did not read, so the refusal above is about the "
        "bytes rather than about the bound"
    )
    assert len(read[1]) == cap
    assert read[2] == len(at_cap)


# ---------------------------------------------------------------------------
# Section 4. A struct interior sorts its refusals into the RIGHT counter
# ---------------------------------------------------------------------------


def _interior_payload() -> bytes:
    """A (14,60) payload whose struct interior holds one refusal of each kind.

    ONE FIXTURE CARRIES BOTH so the two counters are graded against each other
    rather than one at a time. A routing mutation moves a tag from one counter
    to the other, and a fixture holding only one kind is satisfied by the
    counter that absorbed it.

    Returns:
        The payload bytes.
    """
    interior = synthetic.type_tree_tag_list(
        (
            # A MEASURED type whose bytes disagree: the string accounts for six
            # of the eight bytes the tag declares, which is the shipped
            # redundancy oracle firing.
            synthetic.type_tree_property_tag(
                DISAGREEING_NAME,
                synthetic.type_name_tree(synthetic.TREE_STR_TYPE_WORD),
                synthetic.fstring("x") + b"\x00\x00",
            ),
            # An UNMEASURED type. Its bytes are fine; this module simply has no
            # reading for the word, which is what non-negotiable 7 calls
            # unknown content and asks to be flagged and skipped.
            synthetic.type_tree_property_tag(
                UNMEASURED_NAME,
                synthetic.type_name_tree(UNMEASURED_WORD),
                b"\x01\x02\x03\x04",
            ),
        )
    )
    return synthetic.type_tree_property_payload(
        (synthetic.type_tree_struct_tag(STRUCT_NAME, STRUCT_WORD, interior),),
        trailing=synthetic.DECODABLE_TRAILING_RUN,
    )


def test_an_interior_sorts_a_disagreement_and_an_unmeasured_type_into_different_counters() -> None:
    """The interior routing, graded at a pair for the first time.

    THE MUTATION THIS KILLS: ``elif _refusal_is_unmodelled_content(...)``
    replaced by ``elif True`` in ``objects._walk_struct_tags``. It survived the
    entire save suite because NO ARM AT ANY PAIR asserted the interior counters
    against a fixture carrying both kinds - the counter was reachable, moved on
    real bodies, and nothing looked at it.

    THE TWO MEAN OPPOSITE THINGS. An unmeasured type is content this project
    has not modelled; a MEASURED type whose bytes did not account for the
    declared size is the reader not being where it believes it is. Collapsing
    them reports a lost walk as new game content, which is the direction with
    no second chance.
    """
    result = _read_at_the_pair(_interior_payload())
    assert len(result.struct_interiors) == 1, "the interior did not read"
    interior = result.struct_interiors[0]
    assert interior.disagreed == 1, (
        "the interior tag whose MEASURED value disagreed with its declared size "
        "was not counted as a disagreement, so a walk that lost its place is "
        "being reported as unmodelled content"
    )
    assert interior.unmeasured == 1, (
        "the interior tag carrying an unmeasured type was not counted as "
        "unmodelled content, so new game content is being reported as a broken reader"
    )
    assert len(interior.properties) == 0, "neither refused tag should have published a value"


def _empty_interior_payload() -> bytes:
    """The same struct tag over an interior holding no tags at all.

    THE CONTROL FOR THE ARM BELOW. It differs from the fixture above in exactly
    the two interior tags, so a record-level counter that moved between the two
    would be one the interior is feeding.

    Returns:
        The payload bytes.
    """
    return synthetic.type_tree_property_payload(
        (
            synthetic.type_tree_struct_tag(
                STRUCT_NAME, STRUCT_WORD, synthetic.type_tree_tag_list(())
            ),
        ),
        trailing=synthetic.DECODABLE_TRAILING_RUN,
    )


def test_an_interior_refusal_count_stays_off_the_record_level_counters() -> None:
    """WHY THE INTERIOR COUNTERS ARE NOT FOLDED UP, asserted rather than assumed.

    ``PropertyResult.disagreeing_value_count`` partitions the TOP-LEVEL TAG
    population, and CS-831 grades an identity against that total. Folding an
    interior's count into it would move one side of that identity by a number
    taken from a different population - interior tags are not top-level tags,
    and no walk counts them as such.

    SO THE COUNT LIVES ON THE INTERIOR THAT PRODUCED IT, where a consumer
    reaches it through ``struct_interiors``. The arm above is what stops that
    from being a counter nobody ever reads: the two together say the number is
    produced correctly AND is deliberately kept out of the record total.

    IT IS ASSERTED AS A DIFFERENCE RATHER THAN AS A ZERO, and the first draft
    got that wrong. The record's ``unmeasured_value_count`` is NOT zero here
    and never was: a top-level ``StructProperty`` tag carries a type whose own
    value encoding is unmeasured, so the tag itself is flagged - by the walk
    that read it, not by anything inside it. A bare zero would have been
    asserting something false about a counter this arm does not own. What the
    non-folding claim actually needs is that the two records agree DESPITE
    their interiors disagreeing, which is what is checked.
    """
    carrying = _read_at_the_pair(_interior_payload())
    empty = _read_at_the_pair(_empty_interior_payload())

    assert carrying.struct_interiors[0].disagreed == 1
    assert carrying.struct_interiors[0].unmeasured == 1
    assert empty.struct_interiors[0].disagreed == 0, "the control interior is not empty"
    assert empty.struct_interiors[0].unmeasured == 0, "the control interior is not empty"

    assert carrying.disagreeing_value_count == empty.disagreeing_value_count, (
        "the record-level disagreement count moved with the interior's, so an "
        "interior tag is being counted in a partition over TOP-LEVEL tags"
    )
    assert carrying.unmeasured_value_count == empty.unmeasured_value_count, (
        "the record-level unmeasured count moved with the interior's, on the same terms"
    )


# ---------------------------------------------------------------------------
# Section 5. A NATIVE-SERIALIZED container may not be published under a
# DERIVED width - non-negotiable 7
# ---------------------------------------------------------------------------


def _array_of_struct_payload(*, native: bool, inner_tag: bool) -> bytes:
    """A (14,60) payload holding one array of struct, with two dials.

    THE TWO DIALS ARE THE WHOLE EXPERIMENT. ``inner_tag`` decides whether the
    element grammar can close the region - no real (14,60) array carries one,
    so writing it is what forces the decode down to a DERIVED width.
    ``native`` decides only what the tag DECLARES about itself. Holding one
    fixed while the other moves is what makes each arm below evidence about
    the dial it names rather than about the fixture.

    THE PROPERTY NAME IS BORROWED FROM THE SHIPPED FIXTURE AND THAT IS LOAD
    BEARING, not tidiness. The inner tag repeats the property name inside the
    element region, so the name's LENGTH decides the region's parity - and the
    uniform width is admitted only when the region divides evenly by the slots.
    Written first with a name of this file's own, the control below refused for
    that arithmetic reason and the arm above passed VACUOUSLY, with both halves
    of the experiment refusing and the flags byte deciding nothing. Reusing the
    name the shipped array fixture already uses pins the region to one another
    arm in this suite has proved divides.

    Args:
        native: Set the native-serialize bit in the tag's flags byte.
        inner_tag: Write the inner tag the LEGACY grammar carries.

    Returns:
        The payload bytes.
    """
    return synthetic.type_tree_property_payload(
        (
            synthetic.type_tree_array_of_struct_tag(
                synthetic.TREE_ARRAY_NAME,
                synthetic.TREE_ELEMENT_STRUCT_WORD,
                synthetic.TREE_ARRAY_ELEMENTS,
                inner_tag=inner_tag,
                flags=(
                    synthetic.TAG_FLAGS_NATIVE_SERIALIZE if native else synthetic.TAG_FLAGS_NONE
                ),
            ),
        ),
        trailing=synthetic.DECODABLE_TRAILING_RUN,
    )


def test_a_native_serialized_container_is_not_published_under_a_derived_width() -> None:
    """THE ARM THAT FAILS FIRST, and the defect it is written against.

    Before this repair, ALL of the (14,60) containers whose tag set the
    native-serialize bit decoded. They came back with an element count and an
    element width DERIVED by dividing the region by the count - no warning, no
    unmeasured count, no disagreement. On the corpus the derived width happened
    to equal the true one, which is precisely the hazard: a plausible reading
    and a correct one are indistinguishable when nothing checks.

    THE BIT WAS DEFINED AND CONSULTED BY NOTHING. ``TAG_FLAG_NATIVE_SERIALIZE``
    existed, was folded into the measured mask and was stepped over, and a grep
    over the package and the suite found its two definition lines and no use.
    It is the writer's own statement that the value did not go through the
    tagged-property path, which is exactly the statement a derived partition
    needs to be refused by.
    """
    result = _read_at_the_pair(_array_of_struct_payload(native=True, inner_tag=True))
    assert synthetic.TREE_ARRAY_NAME not in result.properties, (
        "a container whose tag declared a native-serialized value was published "
        "under a width derived by division, with nothing on the value to tell a "
        "consumer that width apart from one read out of the bytes"
    )


def test_the_same_container_without_the_native_bit_still_takes_the_derived_width() -> None:
    """THE CONTROL, AND THE FENCE. The derived branch is narrowed, not deleted.

    IDENTICAL BYTES BUT FOR THE FLAGS BYTE. If this published too, the arm
    above would be evidence about the inner tag rather than about the bit; if
    this refused too, the repair would have deleted a reading other pairs still
    depend on. It has to publish, and under a shape the module already records
    as undiscriminated.
    """
    result = _read_at_the_pair(_array_of_struct_payload(native=False, inner_tag=True))
    container = result.properties[synthetic.TREE_ARRAY_NAME]
    assert isinstance(container, objects.ContainerValue), (
        "the derived-width branch stopped publishing for a tag that made no "
        "native-serialize claim, so the repair removed a reading rather than "
        "narrowing one"
    )
    assert container.element_shape in objects.UNDISCRIMINATED_ELEMENT_SHAPES


def test_a_native_serialized_container_is_flagged_as_unmodelled_content() -> None:
    """FLAGGED AND SKIPPED, which is the whole of non-negotiable 7.

    THE COUNTER IT LANDS IN IS THE POINT. A refusal routed to the disagreement
    counter would fire the redundancy oracle - "the reader is not where it
    believes it is, distrust everything after this" - over content the save
    itself said was written by a native serializer. That reports new game
    content as a broken reader, which is the direction with no second chance.
    """
    result = _read_at_the_pair(_array_of_struct_payload(native=True, inner_tag=True))
    assert result.unmeasured_value_count == 1, (
        "the refused native-serialized container was not counted as unmodelled content"
    )
    assert result.disagreeing_value_count == 0, (
        "a native-serialized container was reported as a walk that lost its place"
    )
    codes = {warning.code for warning in result.warnings}
    assert objects.WARN_UNMEASURED_PROPERTY_TYPE in codes, (
        "nothing was flagged, so the container was skipped SILENTLY - which is "
        "the half of non-negotiable 7 that has no second chance"
    )
    assert objects.WARN_MEASURED_VALUE_DISAGREED not in codes


def test_a_native_serialized_container_closing_by_grammar_is_still_published() -> None:
    """WHERE THE RULE STOPS, asserted rather than left to the reader.

    A SELF-DELIMITING CLOSE IS FALSIFIABLE ELEMENT BY ELEMENT: a wrong reading
    does not close, so the closing is evidence about the bytes. The refusal
    above is about a width DERIVED BY ARITHMETIC and nothing else, and an
    implementation that refused every native-serialized container would be
    discarding the strong reading along with the weak one. This fixture is the
    combination that separates them - the bit set, and the element tag lists
    closing the region exactly.
    """
    result = _read_at_the_pair(_array_of_struct_payload(native=True, inner_tag=False))
    container = result.properties[synthetic.TREE_ARRAY_NAME]
    assert isinstance(container, objects.ContainerValue), (
        "a container whose elements closed by their own grammar was refused for "
        "carrying a bit that says nothing about a reading that could have failed"
    )
    assert container.element_shape == objects.ELEMENT_SHAPE_SELF_DELIMITING
    assert result.unmeasured_value_count == 0
    assert result.disagreeing_value_count == 0
