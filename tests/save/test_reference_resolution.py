"""CS-831 - following an ObjectProperty reference to the record it names.

WHAT WAS MISSING AND WHY IT WAS NOT OBVIOUS. ``_decode_object_reference``
already returned the pair, and ``tests/save/test_decode_oracles.py`` already
counted how many of them landed on a record - so a reader could be forgiven for
thinking the join existed. It did not. That tally is a RATE ORACLE: it resolves
a reference, adds one to a counter and discards the record. Nothing under
``clockspeed/`` shipped a resolver at all, so no consumer could ask which record
a reference names. This module grades the one that now ships.

THE POPULATION IS THE TAG, NOT THE SUCCESSFUL DECODE. Every ``ObjectProperty``
TAG the shipped walk steps over enters the count, including one whose value
bytes disagreed with its declared size and yielded no pair. Choosing the other
population - only the tags the decoder returned a pair for - would let the
decoder pick its own denominator, and a walk that lost its place would shrink
the population rather than fail the equality. The partition is therefore three
ways, and every tag lands in exactly one bucket:

  RESOLVED    the object path is borne by at least one record in the same save.
  UNRESOLVED  the pair decoded and no record bears that path. EXPECTED AND
              BENIGN - non-negotiable 7 says to flag and skip rather than fail.
              IT IS NOT ONE THING, and a sentence here said it was: it said
              such references name ASSETS rather than saved objects, as a
              universal over the whole bucket. CS-833 withdrew that. The bucket
              is partitioned by ``objects.classify_unresolved`` into paths in
              the content-tree shape, paths in the SAVED-OBJECT shape that no
              record bears, and references carrying no path at all - and the
              sweep below measures every one of the three inhabited on this
              machine's library. No count of them is written here; the shapes
              are the claim and the counts are derived on each run.
  UNDECODED   the tag is an ``ObjectProperty`` and its bytes yielded no pair.

THE PARTITION EQUALITY IS AN IDENTITY, AND SAYING SO IS THIS MODULE'S CORRECTION
OF ITSELF. The sentence that stood here claimed the sum related four numbers
written at four separate sites and so could be false. It cannot.
``objects._walk_payload`` increments the tag total and the refusal counter in
the SAME iteration off the SAME exhaustive if/else with no ``continue`` between
them, so ``reference_tags == undecoded + len(references)`` is a loop invariant;
``objects.resolve_references`` then does exactly one of ``resolved += 1`` or
``unresolved += 1`` per member. The sum reduces to ``len(refs) + undecoded ==
len(refs) + undecoded``. MEASURED: two landed mutants that gut the join - one
dropping every component from the index, one calling every resolution ambiguous
- left this equality and every other assertion in this file green.

The equality is KEPT because it is cheap and it does pin the shape, and it is no
longer the only thing asserted. What grades the join now is the SECOND JOIN
below, and what grades the refusal counter is the synthetic case
``test_a_reference_tag_whose_bytes_yield_no_pair_is_counted_rather_than_dropped``,
which is where deleting that counter actually reddens.

WHAT THE SECOND PASS IS, STATED WITHOUT THE WORD INDEPENDENT. It walks every
payload again with the shipped tag reader, decodes with the shipped decoder, and
then makes ITS OWN JOIN against a multiset of instance names counted straight
off ``table.records`` with a ``Counter``. So it never consults
``index_records`` or ``resolve_references``, which is precisely where the join
lives and precisely what the two mutants above break - and it shares the walk,
the advance and the decoder with pass one, so it grades none of those. Two
derivations off one decoder are not two pieces of evidence about that decoder
(CLAUDE.md section 5), and the fence is written here rather than left implied.

THE AMENDED CLAUSE ASKS THE TOTAL TO COME FROM A SOURCE THE BUCKET LOOP CANNOT
MOVE, AND HOW FAR THAT IS MET IS WRITTEN DOWN RATHER THAN ASSERTED AWAY. The
partition equality is now stated against ``walked_tags``, filled by a loop in
:func:`_second_join` that neither ``_walk_payload`` nor ``resolve_references``
can reach - so the clause is met in its own terms. It is NOT met in the stronger
sense of a total independent of the shipped reader, and no such total exists to
reach for. The one grammar-free count available - a byte scan for the
length-prefixed type word across a whole body - runs well ahead of the walk,
because the word also occurs inside values the top-level walk steps over.
Restricted to the offsets the walk reports it agrees exactly, but performing
that restriction requires the grammar whose reader is under test. So the scan
can bound the population and can never equal it, and the equality is deliberately
NOT asserted: a clause carrying that much slack would be one more assertion that
reads as protection and grades nothing, which is the defect this file is being
repaired for. THE SCAN IS NO LONGER ONLY DESCRIBED, THOUGH - the DIFFERENCE is
now derived on every run and asserted positive, which is CS-834 and the case
``test_the_type_word_occurrences_the_top_level_walk_does_not_reach_are_counted``.
The scope fact behind it is not a defect in the resolver: CS-831's population is
the top-level tag, and ``objects.resolve_references`` now states that boundary
where the resolver is defined and names the classes of reference outside it.

THE FIGURES THAT STOOD IN THAT PARAGRAPH ARE DELETED RATHER THAN CORRECTED, AND
THE DELETION IS THE POINT. They apportioned the scan's excess between tags
nested inside opaque values and occurrences falling outside every record's
payload extent, and re-measurement did not support the apportionment. NO
FIGURE REPLACES THEM, AND NEITHER DOES A FRESH SPLIT. Re-measured again after
CS-830 - which decoded container element FRAMING and so changed which values the
walk can say anything about - the named regions still do not account for the
difference. It is carried as ONE number for that reason. Every count of this kind
is taken over the operator's own live library, which grows on each autosave, so a
corpus number written into a docstring is false on a timer even where it starts
true - CLAUDE.md section 4 forbids restating a measured number in prose for
exactly that reason, and a docstring is prose. What the corpus says on any given
day is derived on every run by the sweep below instead.

TWO CLAIMS THAT STOOD HERE WERE FALSE AND ARE CORRECTED RATHER THAN DELETED.
They said "a record the reader skipped, or an early return that abandoned a
payload, moves one side and not the other". Neither does. Pass two bails on the
SAME two conditions pass one bails on - ``_skip_actor_head`` refusing, and the
tag walk breaking - and abandons the same record, so both sides move together
and neither condition is detectable by this equality. MEASURED over every
payload of every tagged save in this machine's library: the actor head was
refused on no record, and neither pass bailed on any payload, so that mirrored
path is unexercised as well as undetecting. What the population equality DOES
catch is a population widened to the other two-string type word, because pass
two counts one type word where a widened pass one would count two.

THE SCOPE FENCE IS GRADED RATHER THAN PROMISED. ``SoftObjectProperty`` carries
the identical two-string shape and decodes to an identical ``tuple[str, str]``,
so a resolver reading ``PropertyResult.properties`` by SHAPE cannot tell the two
apart and would silently widen the population. That is why the references travel
as their own typed field rather than being recovered from the value map. The
synthetic case indexes the soft reference's target as a record and asserts it
still does not resolve; the library case catches the same widening through the
population equality, because the second pass counts one type word. MEASURED:
widening the shipped filter to the pair reddens both, the second by exactly the
soft tags the library holds.

WHERE THE LIBRARY CANNOT GRADE, SAID PLAINLY. The undecoded bucket is empty on
this corpus, so no library assertion moves when the counter behind it is
deleted. Its reachability is graded on a fixture instead, and
``test_the_synthetic_broken_tag_would_be_caught_by_the_library_assertion`` is
the control that keeps the zero from being a count nothing increments.

COUNTS ONLY, on the terms ``tests/save/test_decode_oracles.py`` sets out. An
instance name, an object path and a save path are world content under
non-negotiables 11 and 12. Every call that touches a real path or a real body
sits inside a handler that reduces whatever comes out of it to an exception type
NAME, and the join itself is judged inside the sweep and discarded there - no
frame below that line holds a path or a name to render. The synthetic cases are
free to hold strings, because a synthetic fixture is nobody's save.

NEEDS NO GAME FOR MOST OF WHAT IS HERE. Every case but the library sweep runs on
hand-authored fixtures, so the resolver's logic is graded on a machine with no
install and no save library. The library case skips there.
"""

from __future__ import annotations

import ast
import struct
from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from types import MappingProxyType
from typing import Final

import pytest

from clockspeed.save import chunks, header, objects
from tests.save import reach_guard, test_decode_oracles, test_properties

# ---------------------------------------------------------------------------
# Synthetic fixtures
#
# IMPORTED RATHER THAN TRANSCRIBED. ``tests/save/test_properties.py`` already
# encodes the tag grammar and already builds a payload carrying one
# ObjectProperty and one SoftObjectProperty, which is exactly the pair this
# module needs to tell apart. A fourth copy of that grammar here would be a
# fourth place to get it subtly wrong, and two copies of one belief are not two
# pieces of evidence (CLAUDE.md section 5).
# ---------------------------------------------------------------------------

#: The property name the synthetic payload gives its ObjectProperty tag.
_OBJECT_TAG_NAME: Final = "mSyntheticObject"

#: A record table needs the scalars a real one carries. None of them is read by
#: the join; they are here so the fixture is a whole ObjectTable rather than a
#: stub the shipped type would not accept.
_SYNTHETIC_SAVE_VERSION: Final = 52
_SYNTHETIC_HEADER_VERSION: Final = 14
_SYNTHETIC_PREFIX_WIDTH: Final = 8
_SYNTHETIC_TRANSFORM_DELTA: Final = 8

#: Padding appended past an ObjectProperty's two strings so the tag's DECLARED
#: size exceeds what those strings account for. That is the one condition under
#: which the shipped decoder returns no pair for a reference tag.
_DISAGREEMENT_PADDING: Final = 6

#: A string that appears in no shipped constant, planted in a fixture so a repr
#: containing it can only have got it from the fixture.
_LEAK_MARKER: Final = "ClockspeedReferenceLeakMarker"

#: How many reference tags the two-tag fixtures below carry, and how many names
#: the two-record index below holds. Named rather than written twice as a
#: literal, because a bare 2 in an assertion says nothing about which 2 it is.
_TWO_REFERENCE_TAGS: Final = 2
_TWO_INDEXED_NAMES: Final = 2

#: Two reference tags planted in a KNOWN order, so a walk that hands them back
#: in any other order is detectable. BOTH HALVES DIFFER between the two: an
#: assertion over the names alone would survive a swap that moved only the
#: paths, and vice versa.
_FIRST_TAG_NAME: Final = "mFirstSyntheticObject"
_SECOND_TAG_NAME: Final = "mSecondSyntheticObject"
_FIRST_TARGET: Final = "Persistent_Level:PersistentLevel.SyntheticFirstTarget_0"
_SECOND_TARGET: Final = "Persistent_Level:PersistentLevel.SyntheticSecondTarget_0"

#: THE THREE SHAPES THE UNRESOLVED BUCKET ACTUALLY HOLDS - CS-833. One tag name
#: and one path per shape, so a fixture carrying all three drives all three
#: counters and a collapse of the three into one is detectable without a game
#: installed.
#:
#: The ASSET path is sourced from the sibling module's own fixture rather than
#: transcribed, so the shape this file calls asset-shaped and the shape that
#: file plants under a SoftObjectProperty cannot drift apart.
_ASSET_TAG_NAME: Final = "mSyntheticAssetShaped"
_ASSET_SHAPED_PATH: Final = test_properties._SYNTHETIC_ASSET  # noqa: SLF001

#: A path in the SAVED-OBJECT shape - the same shape every resolving reference
#: in a real save carries - that NO record in the fixture table bears. THIS IS
#: THE CLASS THE ASSET GLOSS DENIED EXISTED, and it is measured to be inhabited
#: on this project's own library by the sweep below.
_UNBORNE_TAG_NAME: Final = "mSyntheticUnborneObject"
_UNBORNE_SAVE_OBJECT_PATH: Final = "Persistent_Level:PersistentLevel.SyntheticUnborne_0"

#: The EMPTY object path. A reference whose second string is zero length decodes
#: like any other - the decoder checks that the two strings consume the declared
#: size, and a zero-length string consumes its own prefix exactly - so it is a
#: member of the population and needs a landing place. It names no asset and no
#: saved object; it names nothing.
_EMPTY_TAG_NAME: Final = "mSyntheticEmptyPath"
_EMPTY_OBJECT_PATH: Final = ""

#: How many shapes the unresolved bucket is partitioned into.
_UNRESOLVED_SHAPE_COUNT: Final = 3


def _record(
    instance_name: str,
    *,
    offset: int = 0,
    length: int = 0,
    kind: str = objects.KIND_ACTOR,
) -> objects.ObjectRecord:
    """Build one record bearing a given instance name.

    THE KIND IS A PARAMETER BECAUSE EVERY FIXTURE HERE USED TO BE AN ACTOR, and
    that is exactly what let a landed mutant dropping every non-actor record
    from the index leave this whole file green - see
    ``test_a_component_record_is_indexed_and_can_be_the_target_of_a_reference``
    for what that costs on the real library.

    A COMPONENT IS BUILT TO ITS OWN SHAPE rather than to an actor's with a
    different label: ``objects.ObjectRecord`` records that a component carries a
    parent path where an actor carries a transform block, and that the raw
    discriminator differs.

    Args:
        instance_name: The name the join reads.
        offset: The record's payload offset.
        length: The record's payload length.
        kind: :data:`objects.KIND_ACTOR` or :data:`objects.KIND_COMPONENT`.

    Returns:
        The record.
    """
    component = kind == objects.KIND_COMPONENT
    return objects.ObjectRecord(
        kind=kind,
        type_path=test_properties._SYNTHETIC_CLASS_PATH,  # noqa: SLF001
        root_object=test_properties._SYNTHETIC_ROOT,  # noqa: SLF001
        instance_name=instance_name,
        transform=None,
        parent=test_properties._SYNTHETIC_ROOT if component else None,  # noqa: SLF001
        object_type=0 if component else 1,
        was_placed_in_level=0,
        body_offset=offset,
        body_length=length,
    )


def _table(*records: objects.ObjectRecord) -> objects.ObjectTable:
    """Wrap records in a whole ObjectTable.

    Args:
        *records: The records the table holds.

    Returns:
        The table.
    """
    return objects.ObjectTable(
        records=records,
        unknown_classes=(),
        warnings=(),
        declared_body_length=0,
        body_consumed=0,
        body_prefix_width=_SYNTHETIC_PREFIX_WIDTH,
        transform_delta=_SYNTHETIC_TRANSFORM_DELTA,
        save_version=_SYNTHETIC_SAVE_VERSION,
        header_version=_SYNTHETIC_HEADER_VERSION,
    )


def _read_synthetic() -> objects.PropertyResult:
    """Decode the shared synthetic actor payload through the shipped reader.

    Returns:
        The result, carrying one ObjectProperty and one SoftObjectProperty.
    """
    payload = test_properties._synthetic_payload(actor=True)  # noqa: SLF001
    body = test_properties._synthetic_body(payload)  # noqa: SLF001
    record = test_properties._synthetic_record(payload)  # noqa: SLF001
    schema = test_properties._SYNTHETIC_SCHEMA  # noqa: SLF001
    return objects.read_properties(body, record, test_properties._synthetic_map(schema))  # noqa: SLF001


def _broken_reference_tag(name: str, level: str, path: str) -> bytes:
    """An ObjectProperty whose declared size exceeds what its strings account for.

    The walk still steps over it correctly, because it steps by the DECLARED
    size - which is exactly why this condition is silent unless it is counted.

    Args:
        name: The property name.
        level: The level reference.
        path: The object path.

    Returns:
        The whole tag.
    """
    fstring = test_properties._fstring  # noqa: SLF001
    value = fstring(level) + fstring(path) + bytes(_DISAGREEMENT_PADDING)
    return test_properties._tag_head(name, "ObjectProperty", len(value), b"") + value  # noqa: SLF001


def _read_payload_of(tags: bytes) -> objects.PropertyResult:
    """Decode a COMPONENT payload built from hand-written tags.

    A component payload opens directly with its tags, which keeps the fixture
    free of the actor head this case has no use for.

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
# The typed population - what enters the join and what does not
# ---------------------------------------------------------------------------


def test_the_decoder_hands_back_the_object_reference_under_its_own_property_name() -> None:
    """The reference travels typed, not recovered from the value map by shape.

    NEEDS NO SAVE LIBRARY.
    """
    result = _read_synthetic()

    assert [reference.property_name for reference in result.references] == [_OBJECT_TAG_NAME]
    reference = result.references[0]
    assert reference.level_reference == test_properties._SYNTHETIC_LEVEL  # noqa: SLF001
    assert reference.object_path == test_properties._SYNTHETIC_TARGET  # noqa: SLF001
    assert result.undecoded_reference_count == 0
    assert result.reference_tag_count == 1


def test_two_reference_tags_arrive_in_the_order_their_tags_were_walked() -> None:
    """``references`` is ONE PER TAG AND IN TAG ORDER, and now that is graded.

    ``clockspeed/save/objects.py`` states that contract on the field itself and
    NOTHING IN THIS SUITE HELD IT. Every other fixture here carries exactly one
    ``ObjectProperty``, and a sequence of one is its own reverse, so a landed
    mutant returning ``tuple(reversed(references))`` from ``_walk_payload``
    left the whole suite green while falsifying the contract on every record
    carrying two or more.

    THE LIBRARY CANNOT STAND IN FOR THIS, which is why the fixture is the
    grading and not a convenience. Both joins over the real library reduce each
    payload to COUNTS, and a count is order-insensitive by construction - so
    the corpus can carry as many multi-reference records as it likes and still
    not notice a reversal. Only a payload whose order is known before the walk
    runs can.

    THE TWO TAGS DIFFER IN BOTH HALVES a reversal would move: the property
    names differ and the object paths differ, so neither assertion can pass on
    an accident the other one catches.

    THE PAIRING IS GRADED WITH THEM. This is the only case in this file that
    resolves two distinct references at once, so it is also the only one where
    a join could hand a reference the OTHER reference's record and be believed.

    NEEDS NO SAVE LIBRARY.
    """
    tags = test_properties._reference_tag(  # noqa: SLF001
        _FIRST_TAG_NAME,
        objects.REFERENCE_TYPE_WORD,
        test_properties._SYNTHETIC_LEVEL,  # noqa: SLF001
        _FIRST_TARGET,
    ) + test_properties._reference_tag(  # noqa: SLF001
        _SECOND_TAG_NAME,
        objects.REFERENCE_TYPE_WORD,
        test_properties._SYNTHETIC_LEVEL,  # noqa: SLF001
        _SECOND_TARGET,
    )
    first = _record(_FIRST_TARGET, offset=64, length=32)
    second = _record(_SECOND_TARGET, offset=128, length=32)

    result = _read_payload_of(tags)
    resolution = objects.resolve_references(objects.index_records(_table(first, second)), result)

    assert result.reference_tag_count == _TWO_REFERENCE_TAGS, "the fixture lost a tag"
    assert result.undecoded_reference_count == 0, "the fixture stopped decoding"
    assert [reference.property_name for reference in result.references] == [
        _FIRST_TAG_NAME,
        _SECOND_TAG_NAME,
    ], "the references are not in tag order"
    assert [reference.object_path for reference in result.references] == [
        _FIRST_TARGET,
        _SECOND_TARGET,
    ], "the references are not in tag order"
    assert resolution.resolved == _TWO_REFERENCE_TAGS
    assert resolution.targets[_FIRST_TAG_NAME] == (first,)
    assert resolution.targets[_SECOND_TAG_NAME] == (second,)


def test_the_soft_object_reference_is_outside_the_population_it_shares_a_shape_with() -> None:
    """CS-831 names one type word, and the identical shape of the other is the trap.

    Both decode to a ``tuple[str, str]``, so a resolver reading the value map by
    shape would take both. The soft reference's target is INDEXED AS A RECORD
    here, so a widened population would resolve two rather than one - the
    assertion fails on the count, not on a promise about intent.

    NEEDS NO SAVE LIBRARY.
    """
    result = _read_synthetic()
    table = _table(
        _record(test_properties._SYNTHETIC_TARGET),  # noqa: SLF001
        _record(test_properties._SYNTHETIC_ASSET),  # noqa: SLF001
    )

    resolution = objects.resolve_references(objects.index_records(table), result)

    assert resolution.total == 1
    assert resolution.resolved == 1
    assert resolution.unresolved == 0


# ---------------------------------------------------------------------------
# The join - following a reference to the record it names
# ---------------------------------------------------------------------------


def test_a_resolved_reference_hands_back_the_record_it_names() -> None:
    """THE CAPABILITY CS-831 IS ABOUT. A count is not a join.

    IT ALSO CARRIES THE ZERO END OF THE AMBIGUITY COUNTER, and that pairing is
    the repair rather than a flourish.
    ``test_a_path_borne_by_two_records_resolves_to_both_rather_than_to_a_guess``
    asserted ``ambiguous == 1`` and NOTHING in this file asserted the count was
    ever zero, so a landed mutant widening ``len(found) > 1`` to ``>= 1`` - every
    resolution ambiguous - left the whole file green and the whole save suite
    with it. One record bears this path, so the answer here is zero.

    NEEDS NO SAVE LIBRARY.
    """
    result = _read_synthetic()
    target = _record(test_properties._SYNTHETIC_TARGET, offset=64, length=32)  # noqa: SLF001
    index = objects.index_records(_table(_record("SomethingElse_0"), target))

    resolution = objects.resolve_references(index, result)

    assert resolution.targets[_OBJECT_TAG_NAME] == (target,)
    assert index.records_for(test_properties._SYNTHETIC_TARGET) == (target,)  # noqa: SLF001
    assert resolution.resolved == 1
    assert resolution.ambiguous == 0, "one record bears the path, so nothing is ambiguous"
    assert index.ambiguous_name_count == 0


def test_a_component_record_is_indexed_and_can_be_the_target_of_a_reference() -> None:
    """THE MOTIVATING CASE, and the one every fixture here used to miss.

    ``clockspeed/save/objects.py`` states that EVERY RECORD IS INDEXED and names
    a building's ``mStorageInventory`` as the reference a consumer needs to
    follow - and an inventory is a COMPONENT. Every record fixture in this file
    was an actor, so a landed mutant putting ``if record.kind != KIND_ACTOR:
    continue`` in front of the index left all of it green. Under that mutant the
    library's resolved count collapses to the actor-borne remainder: components
    carry the bulk of the join, and all of it goes silently, with the shipped
    docstring still claiming every record is indexed.

    THE FIGURES THAT STOOD HERE ARE DELETED, AND THE REASON IS A DEFECT RATHER
    THAN TIDINESS. They set a resolved-REFERENCE count beside a resolved-TARGET-
    RECORD count as though the two shared a denominator. They do not: an
    ambiguous resolution is one reference and more than one record, so the two
    populations differ by exactly the ambiguous margin, and the pair as written
    did not add up to the total written beside it. NO CORRECTED FIGURE REPLACES
    THEM - a count over the operator's own growing library is false on a timer
    wherever it is written down (CLAUDE.md section 4).

    What is asserted is the contract: a component is indexed, and a reference
    naming one resolves to it. That is what has to hold on a machine with no
    library at all, which is where this defect must die.

    NEEDS NO SAVE LIBRARY - which matters, because the library case skips on a
    machine with no game installed and this defect must die there too.
    """
    result = _read_synthetic()
    component = _record(
        test_properties._SYNTHETIC_TARGET,  # noqa: SLF001
        offset=64,
        length=32,
        kind=objects.KIND_COMPONENT,
    )
    table = _table(_record("SomeActor_0"), component)

    index = objects.index_records(table)
    resolution = objects.resolve_references(index, result)

    assert component.kind == objects.KIND_COMPONENT, "the fixture stopped being a component"
    assert index.name_count == _TWO_INDEXED_NAMES, "a record left the index"
    assert sum(len(found) for found in index.records_by_name.values()) == len(table.records)
    assert index.records_for(test_properties._SYNTHETIC_TARGET) == (component,)  # noqa: SLF001
    assert resolution.resolved == 1
    assert resolution.unresolved == 0
    assert resolution.targets[_OBJECT_TAG_NAME] == (component,)


def test_a_reference_naming_no_record_is_flagged_unresolved_and_never_raises() -> None:
    """Unresolved is the NORMAL case - the reference names an asset.

    Non-negotiable 7: flagged and skipped, never fatal.

    NEEDS NO SAVE LIBRARY.
    """
    result = _read_synthetic()
    index = objects.index_records(_table(_record("SomethingElse_0")))

    resolution = objects.resolve_references(index, result)

    assert resolution.total == 1
    assert resolution.resolved == 0
    assert resolution.unresolved == 1
    assert resolution.targets == {}
    assert index.records_for(test_properties._SYNTHETIC_TARGET) == ()  # noqa: SLF001


def test_an_empty_record_table_resolves_nothing_and_still_partitions() -> None:
    """The degenerate table. The equality has to hold where the join is empty.

    NEEDS NO SAVE LIBRARY.
    """
    result = _read_synthetic()

    resolution = objects.resolve_references(objects.index_records(_table()), result)

    assert resolution.resolved + resolution.unresolved + resolution.undecoded == resolution.total
    assert resolution.total == 1


# ---------------------------------------------------------------------------
# What the unresolved bucket actually holds - CS-833 and CS-836
#
# NEEDS NO GAME AT ALL. Every case in this section runs on hand-authored tags,
# which is what CS-836 asks for: the resolver dropping a reference has to be
# catchable on a machine with no install and no save library, because that is
# the machine CI runs on and a drop there is silent by construction.
# ---------------------------------------------------------------------------


def _unresolvable_payload() -> objects.PropertyResult:
    """One component payload carrying one reference tag of each unresolved shape.

    ALL THREE IN ONE PAYLOAD ON PURPOSE. Three separate fixtures would each
    drive one counter, and three counters each shown to move once is not the
    same claim as three counters shown to move APART - collapsing them into one
    accumulator leaves three single-shape fixtures entirely green.

    Returns:
        The decoded result, carrying three references and nothing else.
    """
    reference_tag = test_properties._reference_tag  # noqa: SLF001
    level = test_properties._SYNTHETIC_LEVEL  # noqa: SLF001
    return _read_payload_of(
        reference_tag(_ASSET_TAG_NAME, "ObjectProperty", level, _ASSET_SHAPED_PATH)
        + reference_tag(_UNBORNE_TAG_NAME, "ObjectProperty", level, _UNBORNE_SAVE_OBJECT_PATH)
        + reference_tag(_EMPTY_TAG_NAME, "ObjectProperty", level, _EMPTY_OBJECT_PATH)
    )


def test_a_reference_whose_object_path_is_empty_is_bucketed_rather_than_skipped() -> None:
    """CS-836. A resolver that SKIPS a reference loses it silently, and here it cannot.

    THE EMPTY PATH IS THE ONE A SKIP LOOKS REASONABLE FOR. Nothing can bear it,
    so a ``continue`` before the lookup reads like an optimisation rather than a
    defect - and on a machine with no save library nothing else in this file
    would have said otherwise. That is the whole reason this case is synthetic.

    WHAT REDDENS AND WHY IT IS NOT THE IDENTITY BEING CIRCULAR. ``total`` comes
    from ``_walk_payload``'s tag counter, which counts the tag when the walk
    steps over it and knows nothing about what the join later does with it. A
    skip inside ``resolve_references`` moves the buckets and leaves ``total``
    where it was, so the sum parts company with it. That is the ONE defect class
    the identity does catch, and it is exactly this one.

    NEEDS NO SAVE LIBRARY AND NO INSTALL.
    """
    result = _read_payload_of(
        test_properties._reference_tag(  # noqa: SLF001
            _EMPTY_TAG_NAME,
            "ObjectProperty",
            test_properties._SYNTHETIC_LEVEL,  # noqa: SLF001
            _EMPTY_OBJECT_PATH,
        )
    )
    index = objects.index_records(_table(_record(_FIRST_TARGET)))

    resolution = objects.resolve_references(index, result)

    assert result.reference_tag_count == 1, (
        "the fixture stopped carrying exactly one reference tag, so every count "
        "below is about a different population than the one this case describes"
    )
    assert resolution.total == 1
    assert resolution.resolved + resolution.unresolved + resolution.undecoded == resolution.total, (
        f"resolved {resolution.resolved} plus unresolved {resolution.unresolved} plus "
        f"undecoded {resolution.undecoded} does not account for the {resolution.total} tags "
        "the walk stepped over, so a reference was skipped rather than bucketed"
    )
    assert resolution.unresolved == 1, (
        "an empty object path landed somewhere other than the unresolved bucket"
    )
    assert resolution.unresolved_empty_path == 1, (
        "an empty object path was counted as some other unresolved shape"
    )


def test_the_unresolved_bucket_counts_its_three_shapes_apart() -> None:
    """CS-833. The three shapes are counted APART, and a collapse reddens here.

    WHY THIS IS THE CASE THAT GRADES THE SPLIT rather than the library sweep.
    Collapsing the three counters back into one leaves every SUM green - the
    three still add to ``unresolved`` - so a sum is not evidence the split
    exists. What dies under a collapse is three counters each holding ONE while
    the payload carries one tag of each shape, and that is asserted here.

    THE ASSET GLOSS IS FALSIFIED BY CONSTRUCTION HERE AND BY MEASUREMENT IN THE
    SWEEP. Two of these three references name no asset: one carries a path in
    the same shape every resolving reference carries and simply finds no bearer,
    and one carries no path at all.

    NEEDS NO SAVE LIBRARY AND NO INSTALL.
    """
    result = _unresolvable_payload()
    index = objects.index_records(_table(_record(_FIRST_TARGET)))

    resolution = objects.resolve_references(index, result)

    assert resolution.total == _UNRESOLVED_SHAPE_COUNT
    assert resolution.unresolved == _UNRESOLVED_SHAPE_COUNT
    assert resolution.resolved == 0
    assert resolution.unresolved_asset_shaped == 1, (
        "the asset-shaped reference did not land in its own counter"
    )
    assert resolution.unresolved_save_object_shaped == 1, (
        "a path in the saved-object shape that no record bears did not land in "
        "its own counter - this is the class the asset gloss denied existed"
    )
    assert resolution.unresolved_empty_path == 1, (
        "the empty object path did not land in its own counter"
    )


def test_the_three_unresolved_shapes_partition_the_bucket_and_leave_nothing_over() -> None:
    """The split is TOTAL. A fourth shape has a home or this equality says so.

    A CLASSIFIER THAT SILENTLY DROPS AN UNRECOGNISED SHAPE would reproduce, one
    layer down, exactly the defect CS-833 is about: a reference counted in a
    bucket whose stated meaning does not cover it. The shipped classifier is
    total by construction - its last branch is unconditional - and this holds
    the three counters to the bucket they refine so that stops being a promise.

    NEEDS NO SAVE LIBRARY AND NO INSTALL.
    """
    result = _unresolvable_payload()
    index = objects.index_records(_table(_record(_FIRST_TARGET)))

    resolution = objects.resolve_references(index, result)
    shapes = (
        resolution.unresolved_asset_shaped,
        resolution.unresolved_save_object_shaped,
        resolution.unresolved_empty_path,
    )

    assert sum(shapes) == resolution.unresolved, (
        f"the three unresolved shapes {shapes} do not account for the "
        f"{resolution.unresolved} references in the bucket they refine"
    )
    assert len(objects.UNRESOLVED_SHAPES) == _UNRESOLVED_SHAPE_COUNT
    assert set(objects.UNRESOLVED_SHAPES) == {
        objects.UNRESOLVED_ASSET_SHAPED,
        objects.UNRESOLVED_SAVE_OBJECT_SHAPED,
        objects.UNRESOLVED_EMPTY_PATH,
    }


def test_the_unresolved_classifier_names_a_shape_for_every_string_it_is_given() -> None:
    """The classifier is TOTAL over strings, including ones no save produces.

    IT IS A SHAPE TEST AND NOT A CLAIM ABOUT WHAT THE REFERENCE NAMES, which is
    the distinction CS-833 exists to restore. Asking it about a string that is
    neither is therefore a fair question with an answer, not an error - and the
    answer has to be one of the three shipped shapes rather than None, because a
    None here is the silent drop one layer down.

    NEEDS NO SAVE LIBRARY AND NO INSTALL.
    """
    for path in (
        _EMPTY_OBJECT_PATH,
        _ASSET_SHAPED_PATH,
        _UNBORNE_SAVE_OBJECT_PATH,
        _FIRST_TARGET,
        "not-a-path-in-any-shape",
        "/",
    ):
        shape = objects.classify_unresolved(path)
        assert shape in objects.UNRESOLVED_SHAPES, (
            f"the classifier returned {shape!r}, which is not a shipped shape"
        )


# ---------------------------------------------------------------------------
# The two conditions a naive join gets silently wrong
# ---------------------------------------------------------------------------


def test_a_reference_tag_whose_bytes_yield_no_pair_is_counted_rather_than_dropped() -> None:
    """The population is the TAG. A decoder that returns nothing may not shrink it.

    NEEDS NO SAVE LIBRARY.
    """
    tags = test_properties._reference_tag(  # noqa: SLF001
        _OBJECT_TAG_NAME,
        "ObjectProperty",
        test_properties._SYNTHETIC_LEVEL,  # noqa: SLF001
        test_properties._SYNTHETIC_TARGET,  # noqa: SLF001
    ) + _broken_reference_tag(
        "mBrokenReference",
        test_properties._SYNTHETIC_LEVEL,  # noqa: SLF001
        test_properties._SYNTHETIC_TARGET,  # noqa: SLF001
    )
    result = _read_payload_of(tags)
    index = objects.index_records(
        _table(_record(test_properties._SYNTHETIC_TARGET))  # noqa: SLF001
    )

    resolution = objects.resolve_references(index, result)

    assert resolution.total == _TWO_REFERENCE_TAGS, "the undecoded tag left the population"
    assert resolution.undecoded == 1
    assert resolution.resolved == 1
    assert resolution.unresolved == 0
    assert resolution.resolved + resolution.unresolved + resolution.undecoded == resolution.total


def test_a_path_borne_by_two_records_resolves_to_both_rather_than_to_a_guess() -> None:
    """An instance name is NOT unique - measured, on the operator's own library.

    Picking one silently is a wrong answer that reads like a right one, so the
    index hands back what it found and the resolution counts the ambiguity.

    NEEDS NO SAVE LIBRARY.
    """
    result = _read_synthetic()
    first = _record(test_properties._SYNTHETIC_TARGET, offset=64, length=32)  # noqa: SLF001
    second = _record(test_properties._SYNTHETIC_TARGET, offset=128, length=32)  # noqa: SLF001
    index = objects.index_records(_table(first, second))

    resolution = objects.resolve_references(index, result)

    assert index.ambiguous_name_count == 1
    assert index.records_for(test_properties._SYNTHETIC_TARGET) == (first, second)  # noqa: SLF001
    assert resolution.resolved == 1, "an ambiguous name is still a name a record bears"
    assert resolution.ambiguous == 1
    assert resolution.targets[_OBJECT_TAG_NAME] == (first, second)


# ---------------------------------------------------------------------------
# Non-negotiable 12 - every new type renders counts and scalars only
# ---------------------------------------------------------------------------


def test_no_repr_the_resolver_adds_renders_a_path_or_a_name() -> None:
    """A resolved reference carries world content in both halves.

    pytest reprs a frame local before a human chooses what to print, so the safe
    rendering has to be the only one available.

    NEEDS NO SAVE LIBRARY.
    """
    reference = objects.ObjectReference(
        property_name=_LEAK_MARKER,
        level_reference=_LEAK_MARKER,
        object_path=_LEAK_MARKER,
    )
    index = objects.index_records(_table(_record(_LEAK_MARKER)))
    resolution = objects.ReferenceResolution(
        targets={_LEAK_MARKER: index.records_for(_LEAK_MARKER)},
        resolved=1,
        unresolved=0,
        undecoded=0,
        ambiguous=0,
        total=1,
    )
    result = objects.PropertyResult(
        properties={},
        schema_name=_LEAK_MARKER,
        resolved=True,
        warnings=(),
        references=(reference,),
        reference_tag_count=1,
    )

    for rendered in (repr(reference), repr(index), repr(resolution), repr(result)):
        assert _LEAK_MARKER not in rendered, "a repr rendered fixture content verbatim"


# ---------------------------------------------------------------------------
# The real library - skip-if-absent, counts only
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _ReferenceSweep:
    """COUNTS ONLY. No field here can hold a path, a name or a value.

    THE ``walked_*`` HALF IS THE SECOND JOIN, and it exists because the first
    half's own equality is an identity - see the module docstring. Each
    ``walked_*`` field is derived without consulting ``index_records`` or
    ``resolve_references``, so the pair of them is what a defect in the join
    has to move.

    Attributes:
        saves: How many saves of a tagged pair were walked.
        records: How many records the reader was asked about.
        indexed_records: How many records the INDEX holds, summed. Held against
            ``records``, because ``index_records`` states that every record is
            indexed and a mutant dropping a whole kind broke nothing else.
        walked_tags: ObjectProperty tags counted by the second pass.
        walked_resolved: References the SECOND join landed on a record.
        walked_unresolved: References the second join landed on nothing.
        walked_undecoded: Tags the second pass decoded to no pair.
        walked_ambiguous: Second-join landings on a name borne more than once,
            counted off a plain multiset of ``table.records``.
        scanned_type_words: Every occurrence of the length-prefixed reference
            TYPE WORD in the decompressed body, found by a byte scan that knows
            no grammar at all. It is a BOUND on the population and never an
            equal - see the case that reads it for why, and CS-834.
        total: The population the shipped resolver reported, summed.
        resolved: References landing on a record in the same save.
        unresolved: References landing on nothing. THE BUCKET IS NOT ONE THING -
            it is refined by the three fields below, which is CS-833.
        unresolved_asset_shaped: Unresolved references whose path is in the
            content-tree shape.
        unresolved_save_object_shaped: Unresolved references whose path is in
            the SAME shape a resolving reference carries and which no record in
            that save bears.
        unresolved_empty_path: Unresolved references carrying no path at all.
        undecoded: ObjectProperty tags whose bytes yielded no pair.
        ambiguous: Resolutions onto a path borne by more than one record.
        failures: Exception TYPE NAMES, and nothing else about them.
    """

    saves: int
    records: int
    indexed_records: int
    walked_tags: int
    walked_resolved: int
    walked_unresolved: int
    walked_undecoded: int
    walked_ambiguous: int
    scanned_type_words: int
    total: int
    resolved: int
    unresolved: int
    unresolved_asset_shaped: int
    unresolved_save_object_shaped: int
    unresolved_empty_path: int
    undecoded: int
    ambiguous: int
    failures: tuple[str, ...]


#: The reference type word as it appears in a body: a little-endian int32 byte
#: length that INCLUDES the NUL terminator, the ASCII bytes, then the NUL.
#: Derived from the shipped constant rather than typed out, so the scan cannot
#: end up hunting a word the module no longer calls a reference.
_TYPE_WORD_NEEDLE: Final = (
    struct.pack("<i", len(objects.REFERENCE_TYPE_WORD) + 1)
    + objects.REFERENCE_TYPE_WORD.encode("ascii")
    + b"\x00"
)


def _scan_type_words(body: bytes) -> int:
    """Count every occurrence of the length-prefixed type word in a whole body.

    THE ONE COUNT IN THIS FILE THAT KNOWS NO GRAMMAR. It does not walk, it does
    not consult a record extent and it cannot tell a tag from a coincidence - it
    finds a byte pattern. That is exactly its value and exactly its limit: it
    reaches regions no walk visits, so it BOUNDS the population from above and
    can never equal it. See the case that reads it.

    Args:
        body: The decompressed body.

    Returns:
        How many times the pattern occurs. COUNTS ONLY - no offset is returned
        and no byte of the body leaves this frame.
    """
    found = 0
    at = body.find(_TYPE_WORD_NEEDLE)
    while at != -1:
        found += 1
        at = body.find(_TYPE_WORD_NEEDLE, at + 1)
    return found


def _second_join(
    body: bytes, record: objects.ObjectRecord, borne: Mapping[str, int], into: dict[str, int]
) -> None:
    """Walk one payload again and make the join a SECOND time, into ``into``.

    IT CONSULTS NEITHER ``index_records`` NOR ``resolve_references``. The
    multiset it joins against is counted straight off ``table.records`` by the
    caller, and the multiplicity test is done here, so a defect in either of
    those two functions moves the shipped counts and not these.

    WHAT IT SHARES WITH PASS ONE, SAID PLAINLY: the tag walk, the cursor
    advance, the value decoder and the reference narrowing are all the shipped
    ones. This grades the JOIN and nothing underneath it.

    IT MIRRORS PASS ONE'S TWO BAIL CONDITIONS, deliberately and uselessly: the
    actor head refusing and the tag walk breaking abandon the same record in
    both passes, so neither is detectable by any equality over these counts.
    That is recorded rather than fixed here because the fix is a different
    oracle, not a different accumulator.

    THE CALLER HOLDS THE ``try``, on the same terms as :func:`_sweep_one_save`.

    Args:
        body: The decompressed body.
        record: The record whose payload to walk.
        borne: Instance name to how many records bear it, counted by the caller.
        into: The accumulator, mutated in place.
    """
    end = record.body_offset + record.body_length
    start: int | None = record.body_offset
    if record.kind == objects.KIND_ACTOR:
        start = objects._skip_actor_head(body, record.body_offset, end)  # noqa: SLF001
    if start is None:
        return
    tags = test_decode_oracles._walk_with_the_shipped_reader(body, start, end)  # noqa: SLF001
    if tags is None:
        return
    for name, word, at, size in tags:
        if word != objects.REFERENCE_TYPE_WORD:
            continue
        into["walked_tags"] += 1
        value = objects._decode_value(body, word, at, size, None)  # noqa: SLF001
        reference = objects._as_reference(name, value)  # noqa: SLF001
        if reference is None:
            into["walked_undecoded"] += 1
            continue
        bearers = borne.get(reference.object_path, 0)
        if bearers == 0:
            into["walked_unresolved"] += 1
            continue
        into["walked_resolved"] += 1
        if bearers > 1:
            into["walked_ambiguous"] += 1


def _sweep_one_save(
    data: bytes, parsed: header.SaveHeader, property_map: object, into: dict[str, int]
) -> None:
    """Walk one save and fold it into the accumulator.

    THE CALLER HOLDS THE ``try``. This function is allowed to raise; its only
    call site is inside the sweep's broad handler, which reduces whatever comes
    out to a type name before any frame holding ``data`` or ``body`` is
    rendered.

    Args:
        data: The save file's bytes.
        parsed: Its parsed header.
        property_map: The shipped mapping, which this sweep supplies on purpose.
            ``read_properties`` accepts None since CS-960 - see the caller's
            ``Returns`` clause for why this sweep does not take that path.
        into: The accumulator, mutated in place.
    """
    body = chunks.decompress_body(
        data, parsed.body_offset, header_version=parsed.header_version
    ).payload
    table = objects.parse_body(
        body, save_version=parsed.save_version, header_version=parsed.header_version
    )
    index = objects.index_records(table)
    into["saves"] += 1
    into["scanned_type_words"] += _scan_type_words(body)
    into["indexed_records"] += sum(len(found) for found in index.records_by_name.values())
    # PASS TWO'S OWN VIEW OF THE TABLE, counted here with a plain multiset rather
    # than read back out of the index under test. That is the whole reason a
    # defect in `index_records` moves one side of the join and not the other.
    borne = Counter(entry.instance_name for entry in table.records)
    for record in table.records:
        into["records"] += 1
        # PASS ONE - the shipped reader and the shipped join, under test.
        result = objects.read_properties(body, record, property_map)  # type: ignore[arg-type]
        resolution = objects.resolve_references(index, result)
        into["total"] += resolution.total
        into["resolved"] += resolution.resolved
        into["unresolved"] += resolution.unresolved
        into["unresolved_asset_shaped"] += resolution.unresolved_asset_shaped
        into["unresolved_save_object_shaped"] += resolution.unresolved_save_object_shaped
        into["unresolved_empty_path"] += resolution.unresolved_empty_path
        into["undecoded"] += resolution.undecoded
        into["ambiguous"] += resolution.ambiguous
        # PASS TWO - the same tags reached again and joined against `borne`,
        # consulting neither `index_records` nor `resolve_references`.
        _second_join(body, record, borne, into)


@lru_cache(maxsize=1)
def _sweep_references() -> _ReferenceSweep | None:
    """Walk each real save once and return COUNTS ONLY.

    IT CONTAINS ``Exception`` AND ``SystemExit``, AND STOPS THERE, on the terms
    ``tests/save/test_decode_oracles.py`` argues at length: a save path, a body
    and an instance name are things pytest renders out of a frame it unwinds,
    and ``path.read_bytes()`` is a bound method whose ``self`` IS the save path.
    ``KeyboardInterrupt`` is deliberately left free to unwind.

    Returns:
        The sweep, or None when no save library is reachable or the shipped
        property mapping did not load. SINCE CS-960 THAT SECOND CONDITION IS A
        CHOICE THIS SWEEP MAKES RATHER THAN A REQUIREMENT IT INHERITS:
        ``read_properties`` decodes with no map at all, but it then reports
        resolution against no registry, and a sweep whose subject is what
        resolved may not quietly change what it resolved against.
    """
    saves = test_properties._library_save_paths()  # noqa: SLF001
    if not saves:
        return None
    try:
        property_map = test_properties._cached_usmap_or_none()  # noqa: SLF001
    except (Exception, SystemExit):
        # Contained for the reason the sweep in test_decode_oracles gives: the
        # load opens a file under the game install, so an uncontained type here
        # unwinds through a frame holding that path.
        property_map = None
    if property_map is None:
        return None

    into = dict.fromkeys(
        (
            "saves",
            "records",
            "indexed_records",
            "walked_tags",
            "walked_resolved",
            "walked_unresolved",
            "walked_undecoded",
            "walked_ambiguous",
            "scanned_type_words",
            "total",
            "resolved",
            "unresolved",
            "unresolved_asset_shaped",
            "unresolved_save_object_shaped",
            "unresolved_empty_path",
            "undecoded",
            "ambiguous",
        ),
        0,
    )
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
            _sweep_one_save(data, parsed, property_map, into)
        except (Exception, SystemExit) as exc:
            # BROAD BY DESIGN: a narrower catch lets an unexpected type escape
            # carrying the save bytes, which is the leak this containment closes.
            failures.append(type(exc).__name__)
            continue
    # The names and the paths are JUDGED here and discarded here.
    return _ReferenceSweep(failures=tuple(sorted(set(failures))), **into)


def _sweep_or_skip() -> _ReferenceSweep:
    """Fetch the sweep, skipping when this machine cannot grade it.

    THREE MACHINE SHAPES SKIP, NOT ONE, and the third was FAILING rather than
    skipping. A library can hold saves and hold not one of a version pair this
    project parses: ``clockspeed/save/objects.py`` records that (14, 60) reaches
    a property terminator on no payload, so as that pair accumulates a machine
    with a real library walks nothing. The acceptance says skip-if-absent, and
    "absent" has to mean absent of anything gradeable rather than absent of
    files - the same class of gate this project already got wrong once by
    gating on the SAVE library while the data came from the INSTALL.

    THE FAILURE ASSERTION COMES FIRST so an unreadable library reddens rather
    than skipping quietly. Only an empty-but-clean walk skips.

    Returns:
        The sweep.
    """
    sweep = _sweep_references()
    if sweep is None:
        pytest.skip(
            "no save library or no shipped property mapping on this machine - "
            "reference resolution is not gradeable here"
        )
    assert sweep.failures == (), f"failures walking real bodies: {sweep.failures}"
    if sweep.saves == 0:
        pytest.skip(
            "the save library holds no save of a version pair this project "
            "parses - reference resolution is not gradeable here"
        )
    return sweep


def test_every_object_property_reference_in_the_library_resolves_or_is_flagged() -> None:
    """CS-831's acceptance, as an EQUALITY over the tag population.

    WHAT EACH CLAUSE HERE CAN AND CANNOT CATCH, corrected against what this
    docstring used to claim. See the module docstring for the measurement.

    The POPULATION equality catches a population widened to the other
    two-string type word, and a reader that stopped counting tags. It does NOT
    catch a skipped record or an abandoned payload: pass two mirrors pass one's
    two bail conditions and abandons the same record, so both sides move.

    The PARTITION equality is what the acceptance asks for in so many words -
    every reference either resolved or is flagged, nothing dropped - and it is
    an IDENTITY that no defect in the join can violate. It is asserted because
    it pins the shape cheaply, never as evidence the join works. That is graded
    by ``test_the_library_join_agrees_with_a_second_join_the_resolver_did_not_make``.

    The NON-ZERO clause is the one an adjudicator already refused a wording
    without. A join that resolves nothing and flags everything unresolved
    satisfies both equalities above, which is why the count that would be zero
    under it is asserted on its own.

    SKIPS on a machine with no save library, no shipped property mapping, or no
    save of a version pair this project parses. Reports COUNTS ONLY.
    """
    sweep = _sweep_or_skip()

    assert sweep.walked_tags > 0, (
        f"no reference population at all over {sweep.saves} saves and "
        f"{sweep.records} records, so every equality below is vacuous"
    )
    assert sweep.walked_tags == sweep.total, (
        f"the reader reported {sweep.total} ObjectProperty references where a "
        f"second walk of the same payloads counted {sweep.walked_tags} tags"
    )
    # THE TOTAL ON THE RIGHT IS `walked_tags`, NOT `total`, and that is the
    # amended acceptance rather than a cosmetic swap. `total` is
    # `_walk_payload`'s own `reference_tags`, incremented in the same exhaustive
    # if/else as the undecoded counter, so against it this line reduces to
    # `len(refs) + undecoded == len(refs) + undecoded`. `walked_tags` is filled
    # by a loop in `_second_join` that neither `_walk_payload` nor
    # `resolve_references` can reach. WHAT THAT BUYS IS BOUNDED AND SAID SO:
    # given the clause above, this one carries no detection the population
    # equality does not already carry. The detection lives in the second JOIN.
    assert sweep.resolved + sweep.unresolved + sweep.undecoded == sweep.walked_tags, (
        f"resolved {sweep.resolved} plus unresolved {sweep.unresolved} plus "
        f"undecoded {sweep.undecoded} does not account for the {sweep.walked_tags} "
        "tags the second pass counted, so references were dropped between the two"
    )
    assert sweep.resolved > 0, (
        f"nothing resolved across {sweep.walked_tags} references in {sweep.saves} saves; "
        "a join that flags everything unresolved satisfies the equalities and "
        "delivers no capability"
    )


def test_the_library_join_agrees_with_a_second_join_the_resolver_did_not_make() -> None:
    """WHERE THE DETECTION ACTUALLY LIVES. The partition equality is an identity.

    Every clause in the case above held while TWO landed mutants gutted the
    join: one dropping every non-actor record from the index, one calling every
    resolution ambiguous. Both moved counts this case now holds against a second
    join that consults neither ``index_records`` nor ``resolve_references``.

    THE INDEX CLAUSE GRADES A DOCSTRING. ``index_records`` states that EVERY
    RECORD IS INDEXED, and until this line nothing checked it - the shipped
    sentence and the shipped behaviour could part company silently, which is
    exactly what the first mutant did.

    WHAT THIS DOES NOT GRADE, so the next reader does not over-read it: the tag
    walk, the cursor advance, the value decoder and the reference narrowing are
    shipped and shared by both joins, so a defect in any of them moves both
    sides together. This case is about the index and the join alone.

    SKIPS on a machine with no save library, no shipped property mapping, or no
    save of a version pair this project parses. Reports COUNTS ONLY.
    """
    sweep = _sweep_or_skip()

    assert sweep.indexed_records == sweep.records, (
        f"the index holds {sweep.indexed_records} of the {sweep.records} records the "
        "reader was asked about, and index_records states that every record is indexed"
    )
    assert sweep.walked_resolved == sweep.resolved, (
        f"the shipped join resolved {sweep.resolved} references where a second join "
        f"against a plain multiset of the same records resolved {sweep.walked_resolved}"
    )
    assert sweep.walked_unresolved == sweep.unresolved, (
        f"the shipped join flagged {sweep.unresolved} unresolved where the second "
        f"join flagged {sweep.walked_unresolved}"
    )
    assert sweep.walked_undecoded == sweep.undecoded, (
        f"the shipped reader refused {sweep.undecoded} reference tags where the "
        f"second pass refused {sweep.walked_undecoded}"
    )
    assert sweep.walked_ambiguous == sweep.ambiguous, (
        f"the shipped join called {sweep.ambiguous} resolutions ambiguous where a "
        f"second count off the record multiset found {sweep.walked_ambiguous}"
    )


def test_the_library_reference_counts_are_recorded_for_the_ledger() -> None:
    """The acceptance asks for the resolved count to be RECORDED, not just asserted.

    It is recorded HERE - derived on every run rather than transcribed into a
    doc, because the corpus is the operator's own live library and it grows on
    each autosave, so a total written down is stale before it can be committed.
    NOTHING HERE IS PINNED AT AN OBSERVED FIGURE for the same reason: this
    project has a live incident where a floor pinned at a measured count goes
    red on correct code the next time the operator plays.

    SKIPS on a machine with no save library, no shipped property mapping, or no
    save of a version pair this project parses. Reports COUNTS ONLY.
    """
    sweep = _sweep_or_skip()

    recorded = {
        "saves": sweep.saves,
        "records": sweep.records,
        "indexed": sweep.indexed_records,
        "references": sweep.total,
        "resolved": sweep.resolved,
        "unresolved": sweep.unresolved,
        "undecoded": sweep.undecoded,
        "ambiguous": sweep.ambiguous,
    }
    assert recorded["references"] == sweep.walked_tags, (
        f"the recorded counts disagree with the second walk: {recorded} "
        f"against {sweep.walked_tags} tags"
    )
    assert recorded["resolved"] == sweep.walked_resolved, (
        f"the recorded resolved count disagrees with the second join: {recorded} "
        f"against {sweep.walked_resolved} resolved"
    )
    assert recorded["resolved"] > 0, f"nothing to record: {recorded}"


def test_the_undecoded_bucket_is_reachable_rather_than_dead_on_the_library() -> None:
    """The third bucket is EMPTY on this corpus, and that is a measurement.

    A bucket that is empty everywhere is a bucket nothing grades, so its
    reachability is proven on the synthetic fixture instead - see
    ``test_a_reference_tag_whose_bytes_yield_no_pair_is_counted_rather_than_dropped``.
    This case pins what the LIBRARY says about it, so the day a real save
    produces one it is a red rather than a silent change of meaning.

    SKIPS on a machine with no save library. Reports COUNTS ONLY.
    """
    sweep = _sweep_or_skip()

    assert sweep.undecoded == 0, (
        f"{sweep.undecoded} of {sweep.total} real ObjectProperty tags no longer decode; "
        "every tag in this population decoded when this case was written, so this is "
        "either a walk that has lost its place or a grammar change worth an item"
    )


def test_the_type_word_occurrences_the_top_level_walk_does_not_reach_are_counted() -> None:
    """CS-834. The population is TOP-LEVEL tags, and the rest is counted rather than denied.

    ONE NUMBER, DELIBERATELY. The count derived here is the grammar-free scan
    minus the tags the top-level walk reached, and it is left as a single
    difference. AN EARLIER ATTEMPT AT THIS ITEM SPLIT IT IN TWO - nested inside
    opaque values against falling outside every payload - and the two halves
    summed to a total that was itself correct, which is precisely why the split
    read as measured when it was invented. Re-measured on this library the named
    regions do NOT account for the difference, so any apportionment written here
    would be a fresh version of the same false sentence. The difference is the
    measurement; where every member of it lives is not claimed.

    WHAT REDDENS. This asserts the count is positive, so the day anyone asserts
    it is zero - that the top-level walk reaches every occurrence of the word -
    this case says otherwise. That claim is what CS-834 was filed against.

    WHY IT CANNOT BE DRIVEN TO ZERO BY FIXING ANYTHING. The scan matches a byte
    pattern with no grammar, so it also matches the word wherever it appears
    inside a value the walk steps over as opaque bytes, and a walk that chased
    every match would be reading offsets its own grammar never gave it. The
    boundary is a property of the population CS-831 chose, and
    ``objects.resolve_references`` now states it where the resolver is defined.

    SKIPS on a machine with no save library, no shipped property mapping, or no
    save of a version pair this project parses. Reports COUNTS ONLY.
    """
    sweep = _sweep_or_skip()
    unreached = sweep.scanned_type_words - sweep.walked_tags

    assert sweep.scanned_type_words > 0, (
        "the grammar-free scan found no occurrence of the reference type word at "
        f"all across {sweep.saves} saves, so the bound below is vacuous"
    )
    assert unreached > 0, (
        f"the grammar-free scan found {sweep.scanned_type_words} occurrences of the "
        f"reference type word and the top-level walk reached {sweep.walked_tags} of "
        "them, leaving nothing unreached. CS-831's population is top-level tags only "
        "and the word is measured to occur below that level, so a zero here means "
        "the scan or the walk stopped measuring rather than that the gap closed"
    )
    assert sweep.walked_tags < sweep.scanned_type_words, (
        "the walk reached at least as many tags as a scan that also matches the word "
        "inside opaque values, which cannot be true of a bound"
    )


def test_the_library_unresolved_bucket_holds_more_than_one_kind_of_thing() -> None:
    """CS-833. The asset gloss is falsified on this project's own library.

    WHAT THE SHIPPED SENTENCES USED TO SAY was that a reference resolving to no
    record NAMES AN ASSET - stated as a universal over the whole bucket, at
    three sites. It is not universal. Two other shapes are measured to be
    inhabited here: a path in the SAME shape every resolving reference carries
    that simply no record bears, and a reference carrying no path at all.

    THIS IS A PRESENCE FLOOR AND THAT IS SAID PLAINLY. It asserts the non-asset
    remainder is non-empty rather than pinning any count, because the corpus is
    the operator's live library and grows on every autosave. A presence floor
    can in principle go red on correct code the day the library holds nothing
    but asset-shaped misses - but the claim under test IS a presence claim, and
    the collapse this item is really about is graded without a library at all by
    ``test_the_unresolved_bucket_counts_its_three_shapes_apart``.

    SKIPS on a machine with no save library, no shipped property mapping, or no
    save of a version pair this project parses. Reports COUNTS ONLY.
    """
    sweep = _sweep_or_skip()
    shapes = (
        sweep.unresolved_asset_shaped,
        sweep.unresolved_save_object_shaped,
        sweep.unresolved_empty_path,
    )

    assert sweep.unresolved > 0, (
        f"nothing was unresolved across {sweep.walked_tags} references, so the "
        "partition of the unresolved bucket is vacuous here"
    )
    assert sum(shapes) == sweep.unresolved, (
        f"the three unresolved shapes {shapes} do not account for the "
        f"{sweep.unresolved} references in the bucket they refine"
    )
    assert sweep.unresolved_asset_shaped < sweep.unresolved, (
        f"all {sweep.unresolved} unresolved references are asset-shaped, which is "
        "the universal three shipped sentences used to state. Either the corpus "
        "changed shape or the three counters were collapsed back into one"
    )


def test_the_synthetic_broken_tag_would_be_caught_by_the_library_assertion() -> None:
    """The CONTROL for the case above. An assertion pinned at zero needs one.

    ``test_the_undecoded_bucket_is_reachable_rather_than_dead_on_the_library``
    asserts a count is zero, and a count that is zero because nothing ever
    increments it is indistinguishable from one that is zero because the corpus
    is clean. This drives the same counter off a fixture and shows it moving.

    NEEDS NO SAVE LIBRARY.
    """
    clean = _read_payload_of(
        test_properties._reference_tag(  # noqa: SLF001
            _OBJECT_TAG_NAME,
            "ObjectProperty",
            test_properties._SYNTHETIC_LEVEL,  # noqa: SLF001
            test_properties._SYNTHETIC_TARGET,  # noqa: SLF001
        )
    )
    broken = _read_payload_of(
        _broken_reference_tag(
            _OBJECT_TAG_NAME,
            test_properties._SYNTHETIC_LEVEL,  # noqa: SLF001
            test_properties._SYNTHETIC_TARGET,  # noqa: SLF001
        )
    )
    index = objects.index_records(_table())

    assert objects.resolve_references(index, clean).undecoded == 0
    assert objects.resolve_references(index, broken).undecoded == 1


# ---------------------------------------------------------------------------
# CS-835 - the common mode, recorded rather than argued away
#
# WHICH ARM OF THE ACCEPTANCE THIS IS, SAID PLAINLY. CS-835 offers two: a second
# reference count obtained WITHOUT the shipped primitives, or the common-mode
# limit recorded as a shipped constant a test holds against the real shared
# surface. THIS IS THE SECOND ARM. The first was measured impossible without a
# second reader of the save grammar, which this project has declined to build
# and has recorded declining - a grammar-free count can bound the population and
# never equal it, which is the measurement CS-834 above now ships. Recording the
# limit is therefore not a weaker version of the first arm; it is the honest
# statement of what the second pass is, and it turns a fact that lived in a
# docstring into one a test holds.
#
# THE DERIVATION READS SOURCE, NOT BEHAVIOUR, and that is deliberate: the claim
# is about which symbols the two passes SHARE, and two passes agreeing at
# runtime is exactly the evidence that would be worthless here.
# ---------------------------------------------------------------------------

#: The AST node types a function definition can be.
_ANY_FUNCTION: Final = (ast.FunctionDef, ast.AsyncFunctionDef)


def _definitions_of(tree: ast.Module) -> dict[str, ast.AST]:
    """Map every module-level function and class to its node.

    Args:
        tree: The parsed module.

    Returns:
        Name to definition node.
    """
    return {
        node.name: node for node in tree.body if isinstance(node, (*_ANY_FUNCTION, ast.ClassDef))
    }


def _module_universe(tree: ast.Module) -> frozenset[str]:
    """Every name bound at a module's top level - definitions and assignments.

    Args:
        tree: The parsed module.

    Returns:
        The names.
    """
    names = set(_definitions_of(tree))
    for node in tree.body:
        for target in getattr(node, "targets", ()) or ():
            if isinstance(target, ast.Name):
                names.add(target.id)
        annotated = getattr(node, "target", None)
        if isinstance(annotated, ast.Name):
            names.add(annotated.id)
    return frozenset(names)


def _executed_nodes(scope: ast.AST) -> list[ast.AST]:
    """Every node under ``scope`` that RUNS, with annotations excluded.

    ANNOTATIONS ARE NOT EXECUTION AND COUNTING THEM WOULD OVERSTATE THE LIMIT.
    A parameter typed ``ObjectRecord`` does not make the record walker part of
    what a pass runs, and this module is under ``from __future__ import
    annotations`` where such a name is never evaluated at all. Including them
    would also make the shipped record churn on a cosmetic type change, which is
    how a record stops being read.

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
        for field, value in ast.iter_fields(node):
            if field in {"annotation", "returns"}:
                continue
            if field == "args" and isinstance(node, _ANY_FUNCTION):
                continue
            stack.extend(
                item
                for item in (value if isinstance(value, list) else [value])
                if isinstance(item, ast.AST)
            )
    return seen


def _local_names(scope: ast.AST, universe: frozenset[str]) -> set[str]:
    """The module-level names of ``universe`` that ``scope`` executes.

    Args:
        scope: The node to read.
        universe: The defining module's own top-level names.

    Returns:
        The names used.
    """
    return {
        node.id
        for node in _executed_nodes(scope)
        if isinstance(node, ast.Name) and node.id in universe
    }


def _objects_attributes(scope: ast.AST, universe: frozenset[str]) -> set[str]:
    """The ``objects.<name>`` attributes ``scope`` executes.

    QUALIFIED ACCESS ONLY. Matching a bare attribute name would pick up
    ``record.kind`` and every other attribute that happens to share a spelling
    with a module-level name, which would inflate the recorded limit with
    symbols neither pass touches.

    Args:
        scope: The node to read.
        universe: ``objects``' own top-level names.

    Returns:
        The attribute names used.
    """
    return {
        node.attr
        for node in _executed_nodes(scope)
        if isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and node.value.id == objects.__name__.rsplit(".", 1)[-1]
        and node.attr in universe
    }


def _objects_closure(
    seeds: set[str], definitions: Mapping[str, ast.AST], universe: frozenset[str]
) -> frozenset[str]:
    """Close a seed set over ``objects``' own call graph.

    Args:
        seeds: The names a pass reaches directly.
        definitions: ``objects``' module-level definitions.
        universe: ``objects``' top-level names.

    Returns:
        Every name reachable from a seed, the seeds included.
    """
    seen: set[str] = set()
    stack = list(seeds)
    while stack:
        name = stack.pop()
        if name in seen:
            continue
        seen.add(name)
        node = definitions.get(name)
        if node is not None:
            stack.extend(_local_names(node, universe) - seen)
    return frozenset(seen)


@lru_cache(maxsize=1)
def _shared_reference_symbols() -> tuple[frozenset[str], frozenset[str], frozenset[str]]:
    """Derive what each reference-counting pass reaches inside ``objects``.

    Returns:
        Pass one's reach, pass two's reach, and their intersection.
    """
    tree = ast.parse(Path(objects.__file__).read_text(encoding="ascii"))
    definitions = _definitions_of(tree)
    universe = _module_universe(tree)

    here = _definitions_of(ast.parse(Path(__file__).read_text(encoding="ascii")))
    oracles = _definitions_of(
        ast.parse(Path(test_decode_oracles.__file__).read_text(encoding="ascii"))
    )

    first = _objects_closure(
        _objects_attributes(here["_sweep_one_save"], universe), definitions, universe
    )
    second = _objects_closure(
        _objects_attributes(here["_second_join"], universe)
        | _objects_attributes(oracles["_walk_with_the_shipped_reader"], universe),
        definitions,
        universe,
    )
    return first, second, first & second


def test_the_common_mode_the_second_count_cannot_escape_is_recorded_and_accurate() -> None:
    """CS-835. The limit is a shipped constant, and this holds it to the real set.

    A SYMBOL LEAVING OR JOINING THE SHARED SET REDDENS HERE, which is the whole
    of what the recorded-limit arm buys. Before this, the fact that both passes
    run the same reader lived in a docstring, and a docstring cannot notice a
    refactor that widens or narrows the surface it describes.

    WHAT THE CONSTANT MEANS. Every name in it is a symbol of
    ``clockspeed/save/objects.py`` that BOTH reference counts execute. A defect
    in any of them moves both counts the same way, so no agreement between them
    is evidence about it. It is deliberately not a short list - the discomfort is
    the finding.

    NEEDS NO SAVE LIBRARY AND NO INSTALL - it is a claim about the repo.
    """
    first, second, shared = _shared_reference_symbols()
    recorded = set(objects.REFERENCE_COUNT_COMMON_MODE)

    assert shared == recorded, (
        "the recorded common mode no longer matches the shared surface. "
        f"joined since it was recorded: {sorted(shared - recorded)}; "
        f"left it: {sorted(recorded - shared)}"
    )
    assert second - first == frozenset(), (
        "the second count reaches something the first does not, which would make "
        f"it partly independent: {sorted(second - first)}"
    )
    assert second == shared, (
        "the second count's whole reach is no longer inside the common mode, so "
        "the recorded limit understates what the two passes share"
    )
    for named in ("_payload_text", "_read_tag_header", "_decode_value", "_skip_actor_head"):
        assert named in objects.REFERENCE_COUNT_COMMON_MODE, (
            f"{named} is one of the four primitives CS-835 names and it is not in "
            "the recorded common mode"
        )


def test_the_reference_type_word_the_oracles_transcribe_is_the_one_the_module_ships() -> None:
    """CS-831 ships the word as a module constant, which is what a swap needed.

    ``tests/save/test_decode_oracles.py`` records its own copy as a
    transcription whose re-expression against the shipped set was open work: the
    only shipped name carrying the word was ``_TWO_STRING_VALUES``, and sourcing
    from it would widen the population back to the PAIR. A constant naming the
    one word is that re-expression, and this holds the two together so the
    transcription cannot drift from what ships.

    NEEDS NO SAVE LIBRARY - it is a claim about the repo.
    """
    assert objects.REFERENCE_TYPE_WORD == test_decode_oracles._REFERENCE_WORD  # noqa: SLF001
    assert objects.REFERENCE_TYPE_WORD in objects._TWO_STRING_VALUES  # noqa: SLF001
    assert objects.REFERENCE_TYPE_WORD in objects.MEASURED_VALUE_TYPES
    assert "REFERENCE_TYPE_WORD" in objects.__all__


def test_the_resolver_is_on_the_module_s_stated_public_surface() -> None:
    """A capability nothing exports is a capability no consumer may use.

    ``clockspeed/save/world.py`` is the intended consumer, and it reads
    ``objects.__all__`` as the seam. A resolver defined and never exported
    leaves the layer above with nothing to call.

    NEEDS NO SAVE LIBRARY - it is a claim about the repo.
    """
    for name in (
        "ObjectReference",
        "RecordIndex",
        "ReferenceResolution",
        "index_records",
        "resolve_references",
    ):
        assert name in objects.__all__, f"{name} is not on the stated public surface"
        assert getattr(objects, name, None) is not None


def test_an_unexpected_read_failure_does_not_unwind_through_the_reference_sweep(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The containment, exercised rather than described.

    A forced failure inside the per-save read has to be reduced to a type name
    before any frame holding the save path can be rendered.

    IT STUBS BOTH DEPENDENCIES, WHICH IS THE REPAIR. This case used to gate a
    skip on the SAVE library alone and then reach the real INSTALL through
    ``_cached_usmap_or_none``, so on a machine with saves and no install the
    sweep declined, returned None, and this went red instead of grading
    anything. Worse, it went red in ISOLATION on a machine with both: the usmap
    module cache was cold, the planted read error was swallowed by the loader's
    own containment, and it passed only when ``test_properties`` happened to
    sort earlier and warm that cache. CI runs ``-n auto``, whose load
    distribution promises no such ordering. The shape here is the one
    ``test_properties`` already ships for the same job: replace the discovery
    and the mapping with synthetic values FIRST, then break every read.

    NEEDS NO SAVE LIBRARY AND NO GAME INSTALL, and depends on no test ordering.
    """

    class _PlantedError(Exception):
        """A type name the sweep must reduce to."""

    def _boom(_self: object) -> bytes:
        raise _PlantedError(_LEAK_MARKER)

    monkeypatch.setattr(
        "tests.save.test_properties._library_save_paths",
        lambda: (test_properties._SYNTHETIC_SAVE,),  # noqa: SLF001
    )
    monkeypatch.setattr(
        "tests.save.test_properties._cached_usmap_or_none",
        lambda: test_properties._synthetic_map(test_properties._SYNTHETIC_SCHEMA),  # noqa: SLF001
    )
    monkeypatch.setattr("pathlib.Path.read_bytes", _boom)
    _sweep_references.cache_clear()
    try:
        sweep = _sweep_references()
    finally:
        _sweep_references.cache_clear()

    assert sweep is not None
    assert sweep.failures == ("_PlantedError",)
    assert sweep.saves == 0, "a save was walked despite every read raising"
    assert _LEAK_MARKER not in repr(sweep)


def test_the_synthetic_fixture_carries_exactly_one_of_each_two_string_type_word() -> None:
    """The fixture's own precondition. Both cases above rest on it.

    A fixture that stopped carrying the soft reference would leave
    ``test_the_soft_object_reference_is_outside_the_population_it_shares_a_shape_with``
    green and vacuous, so what the fixture holds is asserted rather than assumed.

    NEEDS NO SAVE LIBRARY.
    """
    payload = test_properties._synthetic_payload(actor=True)  # noqa: SLF001
    body = test_properties._synthetic_body(payload)  # noqa: SLF001
    record = test_properties._synthetic_record(payload)  # noqa: SLF001
    end = record.body_offset + record.body_length
    start = objects._skip_actor_head(body, record.body_offset, end)  # noqa: SLF001
    assert start is not None
    tags = test_decode_oracles._walk_with_the_shipped_reader(body, start, end)  # noqa: SLF001
    assert tags is not None

    words = [word for _name, word, _at, _size in tags]

    assert words.count("ObjectProperty") == 1
    assert words.count("SoftObjectProperty") == 1


def test_the_index_is_built_from_the_record_table_rather_than_from_a_body() -> None:
    """The seam. The resolver joins the table and the decoded value, nothing else.

    A resolver that needed the body would make the join a third parse of the
    save rather than a join, and would put a body in one more frame.

    NEEDS NO SAVE LIBRARY - it is a claim about the signature.
    """
    index = objects.index_records(_table(_record("A_0"), _record("B_0")))

    assert index.name_count == _TWO_INDEXED_NAMES
    assert index.ambiguous_name_count == 0
    assert index.records_for("A_0") != ()
    assert index.records_for("Nothing_0") == ()


# ---------------------------------------------------------------------------
# CS-471 - THIS MODULE'S LIBRARY REACH, DECLARED.
#
# The guard is owned by ``reach_guard`` and applied across this package by the
# suite-wide test in ``test_reach_guard``, which walks the package directory
# rather than waiting to be called. A new library-reaching module is therefore
# in scope the moment it exists, which is how this block came to be written -
# the guard reddened on the first run of this file rather than after somebody
# remembered it.
# ---------------------------------------------------------------------------

#: Helpers that genuinely reach the save library, name to why each reaches. The
#: key is the function's own ``__name__`` and the reason comes from
#: ``reach_guard``, so a rename moves both together.
_GRADED_LIBRARY_REACH: Final = MappingProxyType(
    {_sweep_references.__name__: reach_guard.REACH_READS_THE_LIBRARY}
)

#: Touches a primitive WITHOUT consuming a real save path, name to why.
#: Asserted still reaching, so a stale exemption reddens the guard.
#:
#: EMPTY, AND THAT IS A RESULT RATHER THAN AN OVERSIGHT. It held
#: ``test_an_unexpected_read_failure_does_not_unwind_through_the_reference_sweep``
#: for as long as that case called the REAL discovery to decide whether to skip.
#: It no longer calls it - the discovery and the property mapping are replaced
#: with synthetic values before any read is broken - so the case reaches
#: nothing, and the guard said so the moment the exemption stopped describing
#: live code. Naming a primitive as an ARGUMENT in order to break it is not
#: callee position and has never been reach; see ``reach_guard._calls_any``.
_EXEMPT_LIBRARY_REACH: Final[Mapping[str, str]] = MappingProxyType({})
