"""The per-type byte-order status, graded against what the oracles admit - CS-476.

WHY THIS MODULE EXISTS. :data:`objects.VALUE_BYTE_ORDER_STATUS` records, per
value type, whether that type's byte-order question is vacuous, anchored but not
uniquely settled, or scored by nothing at all. The VACUOUS half is derived from
the shipped width by :func:`objects._byte_order_status`, so a type whose width
stops being one byte stops being called vacuous on the same edit. The other half
was not derived from anything. Its population, ``objects._BYTE_ORDER_ANCHORED_VALUES``,
was a hand-written pair that no test read, so the shipped data could claim an
oracle backs a type nothing scores and the suite had no way to notice.

MEASURED BEFORE THIS MODULE EXISTED, and measured with a REAL SOURCE EDIT rather
than an in-process patch, because the status mapping is a comprehension over that
pair evaluated at import and an in-process patch of its input leaves the mapping
stale. Adding ``UInt32Property`` to the pair - so the shipped status reads
``anchored_not_unique`` for a four-byte type no scoring branch admits - left the
whole of ``tests/save`` green.

HOW THE ADMITTED POPULATION IS DERIVED, and it is derived BY EXECUTION rather
than by reading the dispatch's source. A type word is admitted by a byte-order
oracle exactly when changing a value's BYTES, holding the type word and the
value's Python shape fixed, changes something an oracle accumulates. The
bookkeeping an oracle site also keeps - how many values it saw, how many carried
a shape no measured type produces - turns on the shape and the word alone and
cannot move under that probe. So a difference under it is a byte-order judgement
and nothing else.

WHY EXECUTION RATHER THAN A SOURCE SCAN. A scan grades the SPELLING of a
comparison, and a branch written a second way reads to it as absent - which
makes the derivation a transcription of one expected phrasing, which is the
shape CS-476 was filed to remove. The probe grades behaviour instead, and it
carries its own control:
``tests/save/test_byte_order_status.py::test_the_grading_stops_holding_when_the_byte_order_tallies_are_neutered``
neuters the shipped byte-order tallies and requires the grading assertion to
STOP holding. A derivation reading something other than the oracles would
survive that.

WHAT IS GRADED, AND EACH WAY OUT WAS FOUND BY SOMEONE ATTACKING THE PREVIOUS
VERSION RATHER THAN BY DESIGN. Every route below was a real source edit that
left the whole of ``tests/save`` GREEN at the time it was tried, so none of them
is hypothetical.

  THE OVER-CLAIM, which is what CS-476 names. A type marked anchored that no
  oracle admits. Found by adding ``UInt32Property`` to the hand-written set.

  THE UNDER-CLAIM. A type an oracle does admit, left recorded as unscored. Not
  caught by the direction above and failing for the opposite reason.

  THE DELETION. Recording no status for a fixed-width type at all, which is the
  way OUT of both directions above: an absent word reads back as ``None``, and
  the pre-existing vacuity control accepts anything that is not vacuous for a
  type wider than one byte. Found by dropping ``UInt32Property`` from the
  mapping.

  THE SWALLOWED SET MEMBER. :func:`objects._byte_order_status` tests the
  one-byte width FIRST, so a one-byte word added to the hand-written set never
  reaches the mapping and no test over the mapping can see it. That set is
  therefore graded directly as well, not only through what it produces.

  THE VOCABULARY SWAP. Every control here and in ``test_value_anchoring``
  selects by SYMBOL, so exchanging the string values of two status words moves
  the data and the yardstick together. It ships ``anchored_not_unique`` against
  one-byte types and ``vacuous_one_byte`` against the scored ones. The spellings
  are pinned as literals for that reason and for no other.

  THE EXEMPTED KEY, which used no new status word at all and so tripped nothing
  that grades words. The key bound below exempts the types whose single byte
  rides in the TAG rather than in the fixed-width table, and that exemption was
  a hand-written 1-tuple this module read in exactly one assertion. MEASURED
  against this module and ``test_value_anchoring`` AS THEY STOOD BEFORE THIS
  DERIVATION EXISTED, at 31 passed: writing ``StrProperty`` into the shipped
  mapping AND into that tuple shipped ``vacuous_one_byte`` for a
  LENGTH-PREFIXED type whose payload opens with an int32 length - retiring that
  int32's byte-order question with no evidence - with every control green. The
  objects.py half of that edit was already caught on its own; the tuple was the
  second line, and the same second line served a FIFTH-WORD route. So the
  exemption is now ASKED OF THE SHIPPED CODE rather than listed. That is CS-480.

  ASKING THE READER ALONE WAS NOT ENOUGH AND AN ADVERSARY MEASURED IT, which is
  why this paragraph names two sites. :func:`objects._read_tag_header` returns
  the byte a tag carries as its fourth element - but it decides WHICH words get
  one by a literal of its own that nothing grades, so the two-line edit had
  merely moved: widening that literal to ``Int64Property`` and recording the
  word in the shipped mapping ships ``vacuous_one_byte`` for an EIGHT-byte type,
  GREEN at ``tests/save`` 1048 with the library present. A second route wrapped
  the reader so ``StrProperty`` reported a tag byte, which the library-backed
  anchors catch WITH a library and nothing catches without one. So the
  exemption now requires the reader AND :func:`objects._decode_value` to agree -
  the decoded value has to move with the tag byte and with no stored byte - and
  :func:`_value_is_the_tag_byte` is what asks. THE HONEST BOUND: an editor
  changing BOTH shipped sites still widens the exemption, and what is gone is
  every route that leaves the shipped decode untouched, plus any test-side line
  at all. Graded by
  :func:`test_the_tag_carried_one_byte_values_are_derived_from_the_tag_reader`
  - declining to read, coming back empty, and saturating are invisible from the
  bound they serve, and the decoder arm needs HAND-AUTHORED counters because on
  the shipped tree it and the reader arm admit the same single word.

  THE EXEMPTION IS ONE OF TWO SUBTRAHENDS AND ONLY THIS ONE IS DERIVED, WHICH A
  THIRD ADVERSARY ESTABLISHED AND WHICH IS RECORDED HERE RATHER THAN LEFT TO BE
  DISCOVERED AGAIN. The key bound subtracts the fixed-width table AND this
  exemption. Membership of the WIDTH TABLE is self-authorising: a word placed
  there needs no tag reader, no decoder agreement and no exemption, and
  :func:`objects._byte_order_status` calls any width-1 entry vacuous on
  arithmetic alone. MEASURED: three lines in ``objects.py`` - a width-1 entry
  for ``Int64Property``, its shipping-grounds entry, and holding it out of
  ``MEASURED_VALUE_TYPES`` - ship ``vacuous_one_byte`` for an EIGHT-byte type
  with ``tests/save`` at 1002 passed and 49 skipped ON A MACHINE WITH NO GAME,
  byte-identical to the clean tree there, this module included. With the
  operator's library it is red, by library-backed width oracles in other
  modules that skip without one. So the sentence this module is entitled to is
  narrow: NOTHING HERE BOUNDS THE WIDTH TABLE, and a wider type can still reach
  a byte-order status by being declared one byte wide rather than tag-carried.
  Filed as CS-481; do not read the exemption's derivation as covering it.

  THE FOURTH WORD, which is worse than everything above it and was found by an
  attacker after the spelling pin had already landed. Pinning three spellings
  does not BOUND the vocabulary. A new status word - measured with
  ``settled_uniquely`` against ``UInt32Property``, a type no oracle scores -
  ships a claim strictly stronger than the over-claim CS-476 names, and every
  graded direction here passes VACUOUSLY on it because they all select by the
  one anchored symbol. ``objects.BYTE_ORDER_STATUSES`` cannot close this: it is
  a hand-written set in the same file, extended by the same edit. So the shipped
  mapping's VALUES are bounded to :data:`_GRADED_STATUS_WORDS` as literals, and
  a genuinely new word - CS-421's remaining half will want one - has to be added
  there together with whatever grades it.

  THAT CASE ARRIVED AND THE BOUND BEHAVED AS DESIGNED. CS-421's route (b) needed
  ``oracle_cannot_separate``, and adding it to ``objects.py`` alone turned this
  module RED until the grading landed beside it. What grades it is split, and
  the split is not tidy: the VERDICT is library-backed and lives in
  ``test_value_anchoring``, so THIS MODULE CANNOT TELL THAT WORD FROM
  ``unscored`` at all. What it holds is the shape of the shipped set - see
  :func:`test_the_cannot_separate_set_is_bounded_without_a_library`.

THE DERIVATION ITSELF WAS REFUTED TWICE, BOTH TIMES BY SOMEONE OTHER THAN ITS
AUTHOR, AND THE SECOND REFUTATION LANDED AFTER THE FIRST REPAIR WAS BELIEVED
FINAL. The second found that the label set naming which oracles the reach count
requires was hand-written and graded by NOTHING: two lines inside this module -
reverting the probe pairs and dropping one label - restored the exact
previously-refuted state with the whole save suite green. That set is
read out of the dispatch bodies by :func:`_dispatched_tally_names` - WHICH IS
LESS THAN IT SOUNDS, and the sentence that stood here claiming a label could no
longer be dropped without editing the dispatch was itself REFUTED. See the limit
recorded on that function: the NAMES are derived, the BODIES are still listed.

ONE FINDING OF THAT SECOND PASS DID NOT SURVIVE RE-MEASUREMENT, recorded because
an unchecked refutation is as bad as an unchecked claim. It reported that nothing
grades the BALANCE of the two byte probe pairs on the coarseness population
filter - the property that stops census bookkeeping alone from admitting a word.
Measured: an unbalanced pair reddens
``test_the_grading_stops_holding_when_the_byte_order_tallies_are_neutered``,
because that control requires the derived population to be EMPTY with the
tallies dead and an unbalanced pair leaves a word admitted through the census.
The property is graded; the finding was wrong.

THE FIRST REFUTATION AND THE REPAIR IT FORCED, COUNTED RATHER THAN
DESCRIBED. An earlier version claimed to read all three shipped oracles and read
two: its byte probe used a single pair whose halves both carried EQUAL interior
stored bytes, which is exactly the population the mantissa-coarseness oracle
declines, and its two channels were joined by an early return that ran the byte
channel only for words the value channel had already declined. The coarseness
oracle was called ZERO times. Both faults left every other test here green,
because the one word that oracle scores is scored by a magnitude oracle too - so
the derived population came out right for the wrong reason. What closed it is a
CALL COUNT, not a sentence: see ``test_the_probe_reaches_all_three_shipped_oracles``.

THIS MODULE IS LIBRARY-FREE, and that is measured rather than asserted - an
interpreter audit hook over a run recorded no path event matching an install or
a save directory, and a run with every discovery root pointed at an empty
directory passes unchanged. Its probes are hand-authored Python values and
hand-authored bytes. It does IMPORT the save package, which is unavoidable for a
module grading that package's data; what it does not do is open a save,
decompress a chunk or touch the game install. So it runs on a machine with no
game installed, and it declares no library reach because it has none to declare.

WHAT IT DOES NOT COVER, stated rather than left to be inferred. It grades the tie
between the byte-order STATUS data and the oracles. The separate tie between
:data:`objects.EVIDENCE_FOR_VALUE_TYPE` and those same oracles is CS-459 and is
not touched here. It says nothing about whether an oracle's verdict is CORRECT -
only about which type words it passes judgement on at all, so a branch that
tallies byte-dependent nonsense about a type would read here as an oracle.

ONE BOUND ON THE SATURATION FLOOR, stated because it reads stronger than it is.
``test_the_oracles_score_something_and_do_not_score_everything`` requires the
derived population to be a PROPER subset of the words the status data carries,
which rules out a probe that admits everything. It counts candidate words and
not REACHABLE ones: of the words no oracle scores, the one-byte members can
never receive an anchored status through :func:`objects._byte_order_status` at
all, so the mapping-grading tests have fewer words that can actually fail them
than that floor's arithmetic suggests. Grading the hand-written set directly is
what covers the one-byte members; the floor is not what does it.
"""

from __future__ import annotations

import ast
import inspect
import struct
import textwrap
from collections import Counter
from collections.abc import Callable
from typing import Final

import pytest

from clockspeed.save import objects
from tests.save import test_properties, test_value_anchoring

#: The property name the probes decode under. It is joined on by the dispatch
#: under test, so it has to be the same key in both halves of a probe; nothing
#: else about it matters.
_PROBE_NAME: Final = "probe"

#: Pairs of four hand-authored bytes the coarseness dispatch is probed with.
#:
#: TWO PAIRS ARE NEEDED AND ONE WAS NOT ENOUGH, which was measured rather than
#: reasoned about. The first pair differs only in the two OUTER positions, which
#: is what the two magnitude oracles read. The mantissa-coarseness oracle admits
#: a value only when its INTERIOR stored bytes differ from each other - that is
#: the population the middle swap can move - and both halves of the first pair
#: carry equal interior bytes, so with that pair alone the coarseness oracle was
#: called ZERO times in a whole derivation and this module's claim to reach all
#: three oracles was false. The second pair carries differing interior bytes and
#: is what reaches it. Counted rather than asserted by
#: ``test_the_probe_reaches_all_three_shipped_oracles``.
_PROBE_BYTE_PAIRS: Final = (
    (b"\x01\x00\x00\x00", b"\x00\x00\x00\x01"),
    (b"\x00\x01\x00\x00", b"\x00\x00\x01\x00"),
)

#: The width the probe declares for its four bytes, which is what the shipped
#: fixed-width specs record for every four-byte value type.
_PROBE_WIDTH: Final = 4

#: Pairs of decoded values differing in their BYTES and identical in their
#: Python SHAPE. Same shape is the whole design: an oracle site's bookkeeping
#: turns on the shape, so holding it fixed leaves a byte-order judgement as the
#: only thing that can differ between the two halves of a pair.
#:
#: EVERY SHAPE THE MEASURED TYPES PRODUCE IS HERE - bool, int, float, str and a
#: 2-tuple of str - so the probe does not need to know which shape a given type
#: word yields. Knowing that would be one more transcription of the thing under
#: test. A type word is probed with all five and admitted if any pair moves.
#:
#: THIS TUPLE IS GRADED BY NOTHING AND THREE OF ITS FIVE PAIRS ARE INERT, both
#: measured: emptying it entirely leaves every test in this module green, because
#: the byte channel alone admits the same two words. It is kept because the reach
#: count needs the value channel to exercise the two magnitude tallies, and
#: because a future oracle keyed on a shape the byte channel cannot present would
#: need it. Filed as CS-477 with the dispatch-site seam.
_PROBE_VALUE_PAIRS: Final = (
    (1, 0x01000000),
    (1.0, 1e30),
    (True, False),
    ("a", "b"),
    (("a", "b"), ("c", "d")),
)

#: Zero bytes written after a synthetic tag's length-prefixed type word, in
#: place of every shape the tag grammar can put between the type word and the
#: value.
#:
#: ZEROS CARRY EVERY BRANCH TO A DEFINED ANSWER, which is the whole reason one
#: body can probe a word whose grammar this module does not know. A zero int32
#: reads as a declared size of nothing and as an empty length-prefixed string; a
#: zero flag byte reads as "this tag carries no property guid"; a zero declared
#: size leaves the value empty. So the reader reaches a verdict for a word
#: carrying extra strings, for one carrying a struct guid and for one carrying a
#: byte in its tag alike, WITHOUT this module choosing which of those a word is -
#: which is exactly the transcription CS-480 was filed to remove.
#:
#: TWO THINGS ZEROS DO NOT DO, BOTH MEASURED BY AN ADVERSARY WITH A LINE TRACE
#: AND BOTH RECORDED HERE BECAUSE THE SENTENCE ABOVE ONCE CLAIMED OTHERWISE. The
#: guid-PRESENT branch of :func:`objects._skip_guid_flag` is unreachable from a
#: zero-filled body by construction - a zero flag byte forces the absent path,
#: so that branch is never taken and this probe says nothing about it. And the
#: sixteen bytes a ``StructProperty`` tag carries are STEPPED OVER without being
#: inspected, so no branch reads them and zeros are doing nothing there; any
#: sixteen bytes would serve. What is claimed is a defined verdict, not branch
#: coverage.
#:
#: THE COUNT IS SLACK AND NOT A MEASUREMENT. It only has to outlast the longest
#: head the grammar can build, and nothing reads it back. Too short and the
#: reader returns None rather than a wrong answer - measured at 9, where
#: ``BoolProperty`` stops reading - and
#: :func:`test_the_tag_carried_one_byte_values_are_derived_from_the_tag_reader`
#: reddens on the unread word rather than quietly reporting it unscored.
_SYNTHETIC_TAG_SLACK: Final = 96

#: The two tag bytes the decoder is asked to turn into a value, and the two
#: payload fillers it is asked to ignore.
#:
#: 0 AND 1 ARE NOT ARBITRARY: the shipped decoder returns None for a tag byte
#: above 1, so a wider pair would report every word as undecodable and the arm
#: reading them would reject everything. Two payload fillers that differ in
#: every bit are what make "no stored byte contributes" a measurement rather
#: than a hope.
_TAG_BYTE_PROBES: Final = (0, 1)
_PAYLOAD_FILLERS: Final = (0x00, 0xFF)

#: The byte written into one body position at a time to find out which positions
#: the reader's returned tag byte actually depends on. 1 rather than 0xFF on
#: purpose: it is a legal guid flag and a small declared size, so perturbing a
#: field the tag byte does not use leaves the tag readable and the position
#: counts as "no effect" instead of being skipped as unreadable.
_POSITION_PROBE: Final = 0x01

#: The status words this module knows how to grade. PINNED AS LITERALS, which is
#: the one deliberate transcription here: these strings are the artifact's
#: interface to a reader outside this repository, and every control over the data
#: - this module's and ``test_value_anchoring``'s - selects by SYMBOL, so nothing
#: that follows a symbol can see a spelling change or a word added beside it.
#:
#: ``oracle_cannot_separate_readings`` ARRIVED WITH CS-421 AND IS THE CASE THIS
#: TUPLE WAS BUILT TO FORCE. The fourth-word route was measured by an attacker shipping
#: a made-up word for a type nothing scored, so the rule became: a new word is
#: added HERE, together with whatever grades it. What grades this one is split
#: across two modules on purpose, and neither half is the whole answer. The
#: verdict - that a shipped oracle was applied to that type's own values and
#: scored the as-stored and reversed readings identically - is LIBRARY-BACKED and
#: lives in ``test_value_anchoring``, because no hand-authored probe can stand in
#: for the operator's data. What is gradeable without a library is the shape of
#: the shipped set, and that is
#: :func:`test_the_cannot_separate_set_is_bounded_without_a_library`.
#: SO THIS MODULE CANNOT TELL THAT WORD FROM ``unscored``, and does not pretend
#: to: on a machine with no game the distinction is ungraded, which is CS-426.
_GRADED_STATUS_WORDS: Final = (
    "vacuous_one_byte",
    "anchored_not_unique",
    "oracle_cannot_separate_readings",
    "unscored",
)

#: The two functions the shipped byte-order dispatch runs through, as
#: ``(module, attribute)``. Named because the reach count has to patch them; the
#: SET OF TALLIES it requires is derived from their source rather than listed -
#: see :func:`_dispatched_tally_names`.
_DISPATCH_SITES: Final = (
    (test_properties, "_tally_decoded_values"),
    (test_value_anchoring, "_score_values_under_every_permutation"),
)


def _dispatched_tally_names() -> frozenset[str]:
    """The byte-order tallies the shipped dispatch sites actually call.

    THE NAMES ARE DERIVED; THE BODIES ARE STILL LISTED, and that is the whole
    limit. A hand-written label set was the previous version and it was graded by
    nothing: two lines inside this module restored the previously-refuted state
    with the save suite green. Reading the call names out of the dispatch bodies
    closes that particular two-line edit. It does NOT close the seam, and the
    claim that it did was measured false rather than argued away.

    TWO ROUTES REMAIN OPEN, BOTH MEASURED GREEN AT ``tests/save`` 1040 - filed as
    CS-477, not hidden here. Deleting one entry from :data:`_DISPATCH_SITES`
    drops every oracle that entry owns, and costs the probe nothing, because
    :func:`_coarseness_observation` reaches its dispatch directly rather than
    through the tuple. And an ordinary extract-method refactor inside a dispatch
    - moving a tally call into a helper - takes the call out of the scanned body
    while the oracle still runs, so the scan reports it unreached-by-absence
    rather than reporting it at all. A rename dropping the prefix IS caught, but
    only because the reach test's own patch raises on a missing attribute.

    Returns:
        Every ``_tally_``-prefixed name the two dispatch bodies call.
    """
    found: set[str] = set()
    for module, attribute in _DISPATCH_SITES:
        source = textwrap.dedent(inspect.getsource(getattr(module, attribute)))
        for node in ast.walk(ast.parse(source)):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", "")
            if name.startswith("_tally_"):
                found.add(name)
    return frozenset(found)


#: The words the shipped status data classifies. Read from the shipped mapping
#: rather than listed, so a type added to the status data is probed without this
#: module being edited.
_CANDIDATE_WORDS: Final = frozenset(objects.VALUE_BYTE_ORDER_STATUS)

#: The words the tag reader is asked about. The status data's own keys are the
#: population that needs a verdict; the fixed-width table is unioned in so the
#: saturation control below has something that MUST come back without a tag byte
#: even if a word is dropped from the mapping.
_PROBED_TAG_WORDS: Final = _CANDIDATE_WORDS | frozenset(objects._FIXED_WIDTH_VALUES)  # noqa: SLF001


def _synthetic_tag(word: str) -> bytes:
    """One hand-authored tag presenting a type word to the shipped reader.

    Args:
        word: The type word written into the tag.

    Returns:
        A body whose first byte is where :func:`objects._read_tag_header` begins,
        being just past a tag's name.
    """
    encoded = word.encode("ascii") + b"\x00"
    return struct.pack("<i", len(encoded)) + encoded + bytes(_SYNTHETIC_TAG_SLACK)


def _tag_reader_read(word: str) -> tuple[str, int, int, int | None] | None:
    """What the shipped tag reader makes of a synthetic tag for one word.

    Args:
        word: The type word to present.

    Returns:
        The reader's own four-tuple, or None if the tag does not read.
    """
    body = _synthetic_tag(word)
    return objects._read_tag_header(body, 0, len(body))  # noqa: SLF001


def _tag_byte_source_positions(word: str) -> list[int]:
    """Which body positions the reader's returned tag byte depends on.

    THE WIDTH OF THE TAG-CARRIED FIELD IS A DEPENDENCE COUNT AND NOTHING ELSE
    MEASURED IT, which an adversary showed by widening the read without moving
    the cursor. Replacing the reader's one-byte read with a two-byte one while
    leaving its advance at one byte left the whole save suite GREEN: the cursor
    arm saw its usual one-byte excess, the probe's own tag byte was 0 either
    way, and ``objects.VALUE_BYTE_ORDER_STATUS`` went on shipping
    ``vacuous_one_byte`` for a value that had become two bytes wide. A range
    check could not have caught it and neither could the cursor.

    HOW IT IS COUNTED. One body position at a time is set to
    :data:`_POSITION_PROBE` and the tag is re-read. A position counts when the
    re-read still yields THIS word and the tag byte it hands back differs. A
    perturbation that stops the tag reading, or that changes the type word
    itself, is skipped rather than counted - it says nothing about the field.

    Args:
        word: The type word to probe.

    Returns:
        The positions the returned tag byte moves with, empty when the word
        carries no tag byte at all.
    """
    body = bytearray(_synthetic_tag(word))
    baseline = objects._read_tag_header(bytes(body), 0, len(body))  # noqa: SLF001
    if baseline is None or baseline[3] is None:
        return []
    positions = []
    for index in range(len(body)):
        held = body[index]
        body[index] = _POSITION_PROBE
        got = objects._read_tag_header(bytes(body), 0, len(body))  # noqa: SLF001
        body[index] = held
        if got is not None and got[0] == word and got[3] != baseline[3]:
            positions.append(index)
    return positions


def _value_is_the_tag_byte(word: str, read: tuple[str, int, int, int | None]) -> bool:
    """Whether the shipped DECODER makes this type's value out of the tag byte alone.

    THIS ARM EXISTS BECAUSE THE READER ALONE WAS REFUTED, and the refutation is
    recorded here rather than summarised. Asking only
    :func:`objects._read_tag_header` whether it hands a value byte back moved the
    hand-written population across the seam instead of removing it: the reader
    decides by a literal of its own, that literal is graded by nothing, and
    MEASURED at 32 passed over this module and ``test_value_anchoring`` with the
    operator's library present, widening it to ``Int64Property`` and recording
    that word in the shipped mapping ships ``vacuous_one_byte`` - the word that
    says the byte-order question is retired BECAUSE THE VALUE IS ONE BYTE - for
    an EIGHT-byte type whose value encoding ``objects.py`` explicitly claims
    nothing about. The old two-line edit had become a new two-line edit.

    WHAT THE SECOND SITE BUYS, STATED AS A BOUND RATHER THAN AS A CLOSURE. The
    exemption now requires the reader AND the decoder to agree, and they are
    separate shipped functions: :func:`objects._decode_value` has to turn the tag
    byte into this type's value with no stored byte contributing. A word named in
    the reader and not decoded that way is rejected here. That is NOT a claim
    that no edit can widen the exemption - an edit to both sites still can, and
    it changes what the shipped parser DECODES rather than only what a test
    believes. What is gone is any route that leaves the shipped decode untouched.

    THE THREE ARMS, AND WHY EACH IS NEEDED. The value must decode at all, or an
    unmeasured type would pass by returning None twice and comparing equal. It
    must CHANGE with the tag byte, or a type whose value ignores that byte would
    qualify. And it must NOT change with the payload, or a length-prefixed type
    handed a tag byte would qualify on the strength of bytes the tag byte had no
    part in - which is the second refuted route exactly.

    THE ARMS RUN OVER THE FULL CROSS PRODUCT BECAUSE SAMPLING TWO SLICES OF IT
    WAS REFUTED. An earlier version held the payload at one filler while varying
    the tag byte and held the tag byte at one value while varying the filler, so
    the CROSS TERM - payload dependence at the tag byte that would actually carry
    data - was never sampled. MEASURED in process against the shipped helpers: a
    decoder returning a constant for tag byte 0 and a STORED byte for tag byte 1
    was accepted, which is the exact shape the payload arm exists to reject. Both
    arms are now required at every combination.

    TWO THINGS THE PROBE STANDS IN FOR, STATED BECAUSE THEY BOUND WHAT ANY
    VERDICT HERE MEANS. The declared size the reader hands back is always 0,
    because :func:`_synthetic_tag` writes zeros where that int32 lands - so a
    shipped branch gated on a zero size is fully visible here and invisible in a
    real save. And the payload body is UNIFORM, so a decoder reading two
    different payload offsets cannot be told from one reading none; what the
    payload arm detects is dependence on the payload's VALUE, not on its shape.

    Args:
        word: The type word being judged.
        read: What :func:`objects._read_tag_header` returned for it.

    Returns:
        True when the decoded value moves with the tag byte and with nothing else.
    """
    _, value_at, size, _ = read
    span = value_at + size + _SYNTHETIC_TAG_SLACK

    def decoded(tag_byte: int, filler: int) -> object:
        return objects._decode_value(  # noqa: SLF001
            bytes([filler]) * span, word, value_at, size, tag_byte
        )

    readings = {
        (tag_byte, filler): decoded(tag_byte, filler)
        for tag_byte in _TAG_BYTE_PROBES
        for filler in _PAYLOAD_FILLERS
    }
    if any(value is None for value in readings.values()):
        return False
    moves_with_the_tag = all(
        any(
            readings[(tag_byte, filler)] != readings[(_TAG_BYTE_PROBES[0], filler)]
            for tag_byte in _TAG_BYTE_PROBES[1:]
        )
        for filler in _PAYLOAD_FILLERS
    )
    ignores_the_payload = all(
        readings[(tag_byte, filler)] == readings[(tag_byte, _PAYLOAD_FILLERS[0])]
        for tag_byte in _TAG_BYTE_PROBES
        for filler in _PAYLOAD_FILLERS
    )
    return moves_with_the_tag and ignores_the_payload


def _tag_carried_one_byte_values() -> frozenset[str]:
    """The type words the shipped tag reader hands a value byte back for.

    THIS IS THE POPULATION CS-480 EXISTS TO DERIVE. It was a hand-written 1-tuple
    read by exactly one assertion. MEASURED at 31 passed over this module and
    ``test_value_anchoring`` AS THEY STOOD BEFORE THIS FUNCTION EXISTED, ON A
    MACHINE WITH THE OPERATOR'S LIBRARY - the same two modules skip a third of
    that on a machine with no game, which is why the figure is qualified:
    writing
    ``StrProperty`` into the shipped status mapping AND into that tuple shipped
    ``vacuous_one_byte`` for a LENGTH-PREFIXED type whose payload opens with an
    int32 length - retiring that int32's byte-order question with no evidence at
    all - with every control green. Its objects.py half was caught on its own;
    the tuple was the second line, and it made the key bound one transcription deep.

    WHAT MAKES A WORD TAG-CARRIED IS NOT ASSERTED HERE, IT IS ASKED - OF TWO
    SHIPPED SITES, BECAUSE ONE WAS REFUTED. :func:`objects._read_tag_header`
    returns the byte a tag carries as its fourth element and ``None`` when the
    tag carries none. That alone is not enough, and the reason is measured on
    :func:`_value_is_the_tag_byte`: the reader picks its own population by a
    literal nothing grades, so the exemption could still be widened by two lines
    - they had merely both moved into ``objects.py``. So a word also has to be
    one :func:`objects._decode_value` builds out of that byte alone.

    THE BOUND, STATED RATHER THAN LEFT TO BE READ AS A CLOSURE. An editor who
    changes BOTH shipped sites still widens the exemption. What no longer works
    is any route that leaves the shipped decode untouched, and there is no
    test-side line to add at all. A word that does not read reports no verdict
    and is not counted - a silent route to an empty population, graded by
    :func:`test_the_tag_carried_one_byte_values_are_derived_from_the_tag_reader`
    rather than assumed here.

    Returns:
        Every probed word the reader returns a tag-carried value byte for.
    """
    carried: set[str] = set()
    for word in _PROBED_TAG_WORDS:
        read = _tag_reader_read(word)
        if read is not None and read[3] is not None and _value_is_the_tag_byte(word, read):
            carried.add(word)
    return frozenset(carried)


def _magnitude_observation(word: str, value: object) -> tuple[object, ...]:
    """Everything the magnitude dispatch accumulates for one word and one value.

    Args:
        word: The tag type word the value is presented under.
        value: One decoded value.

    Returns:
        A comparable snapshot of the dispatch's whole accumulator.
    """
    tally = test_properties._DecodeTally(Counter(), set(), set())  # noqa: SLF001
    test_properties._tally_decoded_values(  # noqa: SLF001
        {_PROBE_NAME: value}, {_PROBE_NAME: word}, tally
    )
    return (
        tuple(sorted(tally.counts.items())),
        tuple(sorted(tally.measured_present)),
        tuple(sorted(tally.measured_yielding)),
    )


def _coarseness_observation(word: str, stored: bytes) -> tuple[object, ...]:
    """Everything the coarseness dispatch accumulates for one word and four bytes.

    THE WHOLE ACCUMULATOR IS SNAPSHOT, not a chosen field of it. Choosing which
    fields count would put the judgement back in this module, which is the
    transcription the derivation exists to avoid.

    Args:
        word: The tag type word the four bytes are presented under.
        stored: The four stored bytes, standing in for a payload body.

    Returns:
        A comparable snapshot of every accumulator the dispatch mutates, plus
        what it reports having scored.
    """
    permutations = test_value_anchoring._PERMUTATIONS  # noqa: SLF001
    tallies = {
        perm: test_properties._DecodeTally(Counter(), set(), set())  # noqa: SLF001
        for perm in permutations
    }
    coarseness: dict[tuple[int, ...], Counter[int]] = {perm: Counter() for perm in permutations}
    census = test_value_anchoring._CoarsenessCensus()  # noqa: SLF001
    scored = test_value_anchoring._score_values_under_every_permutation(  # noqa: SLF001
        stored, [(word, 0, _PROBE_WIDTH)], tallies, coarseness, census
    )
    return (
        scored,
        tuple((perm, tuple(sorted(tallies[perm].counts.items()))) for perm in permutations),
        tuple((perm, tuple(sorted(coarseness[perm].items()))) for perm in permutations),
        (census.admitted, census.graded, census.misread, census.inert),
    )


def _is_admitted(word: str) -> bool:
    """Whether any shipped byte-order oracle passes judgement on this type word.

    Args:
        word: A type word from the shipped status data.

    BOTH CHANNELS ARE EVALUATED AND NEITHER SHORT-CIRCUITS THE OTHER. An early
    return on the value channel is what kept the coarseness oracle at zero calls:
    the only word that channel admits is also the only word the coarseness oracle
    scores, so returning on the first hit meant the byte channel ran exclusively
    for words no oracle scores, where it can only ever report False. A cheap
    disjunction that never exercises half of what it claims to read is worse than
    an expensive one, and this module runs in a fraction of a second either way.

    Returns:
        True when changing a value's bytes, with the word and the value's Python
        shape held fixed, changes something an oracle accumulates.
    """
    by_value = any(
        _magnitude_observation(word, low) != _magnitude_observation(word, high)
        for low, high in _PROBE_VALUE_PAIRS
    )
    by_bytes = any(
        _coarseness_observation(word, low) != _coarseness_observation(word, high)
        for low, high in _PROBE_BYTE_PAIRS
    )
    return by_value or by_bytes


def _admitted_words() -> frozenset[str]:
    """The type words the shipped byte-order oracles actually score.

    Returns:
        Every candidate word :func:`_is_admitted` reports on.
    """
    return frozenset(word for word in _CANDIDATE_WORDS if _is_admitted(word))


def _marked_anchored() -> frozenset[str]:
    """The type words the shipped status data calls anchored but not unique.

    Returns:
        The words whose shipped status is
        :data:`objects.BYTE_ORDER_ANCHORED_NOT_UNIQUE`.
    """
    return frozenset(
        word
        for word, status in objects.VALUE_BYTE_ORDER_STATUS.items()
        if status == objects.BYTE_ORDER_ANCHORED_NOT_UNIQUE
    )


def test_no_type_is_marked_anchored_that_no_oracle_scores() -> None:
    overclaimed = sorted(_marked_anchored() - _admitted_words())
    assert not overclaimed, (
        f"{overclaimed} is recorded as {objects.BYTE_ORDER_ANCHORED_NOT_UNIQUE} in "
        "objects.VALUE_BYTE_ORDER_STATUS, and no shipped byte-order oracle passes "
        "judgement on it - changing such a value's bytes moves nothing any oracle "
        "accumulates. That status claims evidence the module does not have. Either "
        "an oracle scoring it is missing, in which case the honest status is "
        f"{objects.BYTE_ORDER_UNSCORED}, or an oracle scores it under a shape this "
        "module does not probe, in which case the probe pairs are what need widening."
    )


def test_no_type_an_oracle_scores_is_left_recorded_as_unscored() -> None:
    underclaimed = sorted(_admitted_words() - _marked_anchored())
    assert not underclaimed, (
        f"a shipped byte-order oracle scores {underclaimed} and "
        "objects.VALUE_BYTE_ORDER_STATUS does not record it as "
        f"{objects.BYTE_ORDER_ANCHORED_NOT_UNIQUE}. This is the opposite failure to "
        "the one above and is not caught by it: the status data understates what the "
        "running controls cover, so a reader is told a question is open that an "
        "oracle has already spoken on. A word here recorded "
        f"{objects.BYTE_ORDER_VACUOUS} is worse still - a one-byte value has one "
        "byte order, so an oracle scoring one means a width or a status is wrong."
    )


def test_every_fixed_width_type_the_module_decodes_carries_a_recorded_status() -> None:
    """A type can escape both graded directions above by not being recorded at all.

    MEASURED, not inferred: dropping ``UInt32Property`` from the shipped status
    mapping left the whole of ``tests/save`` green, this module included. The
    pre-existing vacuity control iterates the WIDTH table and asks whether each
    wider type is recorded as something other than vacuous - and an absent word
    reads back as ``None``, which is not vacuous, so it passes. That leaves
    deletion as a way to answer an over-claim, and deletion answers nothing.

    THE POPULATION IS THE WIDTH TABLE ITSELF, which is the table
    :func:`objects._decode_fixed_width` is driven from. A type this module
    decodes from a fixed number of stored bytes has a byte order by
    construction, so it has a byte-order question, so it needs a status.
    """
    decoded = frozenset(objects._FIXED_WIDTH_VALUES)  # noqa: SLF001
    assert decoded, "the shipped fixed-width table is empty, so this test grades nothing"

    unrecorded = sorted(decoded - _CANDIDATE_WORDS)
    assert not unrecorded, (
        f"{unrecorded} is decoded from a fixed number of stored bytes and carries no "
        "entry in objects.VALUE_BYTE_ORDER_STATUS at all. Its bytes have an order and "
        "the module says nothing about it, which reads as no question rather than as "
        "an open one. Deleting an entry is not a way to retire an over-claim - "
        f"{objects.BYTE_ORDER_UNSCORED} is."
    )

    ungoverned = sorted(_CANDIDATE_WORDS - decoded - _tag_carried_one_byte_values())
    assert not ungoverned, (
        f"objects.VALUE_BYTE_ORDER_STATUS records a byte order for {ungoverned}, which is "
        "not decoded from a fixed number of stored bytes and is not one the shipped tag "
        "reader hands a value byte back for. THE EXEMPTION IS DERIVED RATHER THAN LISTED - "
        "it used to be a hand-written tuple read by this line alone, and adding one word to "
        "it was the second line of the route below. THE POPULATION IS BOUNDED EXACTLY, and "
        "an earlier version of this "
        "assertion admitted any word in MEASURED_VALUE_TYPES - which shipped green while the "
        "mapping recorded vacuous_one_byte against StrProperty, a LENGTH-PREFIXED type whose "
        "payload carries an int32 length. That retires an int32 byte-order question with no "
        "evidence at all, using no new status word, so neither the vocabulary bound nor any "
        "graded direction fired. A status about a type this reader does not read from a fixed "
        "width is a claim with nothing behind it, whatever the word says."
    )


def test_the_tag_carried_one_byte_values_are_derived_from_the_tag_reader() -> None:
    """The exemption from the key bound is asked of the reader, not transcribed.

    WHAT THIS COVERS AND WHY IT IS A SEPARATE TEST FROM THE BOUND IT SERVES.
    :func:`test_every_fixed_width_type_the_module_decodes_carries_a_recorded_status`
    subtracts :func:`_tag_carried_one_byte_values` from the words the shipped
    mapping records, so a derivation that admitted too much would widen that
    exemption silently and a derivation that read nothing would narrow it into a
    false red. Neither failure is visible from inside that test, because both
    leave it asserting about a set it has no independent handle on.

    FOUR WAYS THE DERIVATION CAN BE WRONG, EACH GRADED BELOW RATHER THAN
    ASSUMED, AND THE COUNT WAS THREE UNTIL AN ADVERSARY SUPPLIED THE FOURTH. It
    can fail to READ - a synthetic tag the shipped grammar rejects returns
    ``None``, which reports as "no tag byte" and is indistinguishable from a
    real verdict. It can come back EMPTY, which retires the exemption
    altogether. It can SATURATE onto words whose bytes live in the fixed-width
    table. And it can admit a word that is in NEITHER - a length-prefixed type,
    which is CS-480's own defect and which the saturation arm cannot see,
    because such a word is not in the fixed-width table to intersect with. That
    fourth one is held by :func:`_value_is_the_tag_byte` rather than by an arm
    here, and by the two load-bearing controls beside this test.

    THE TWO WIDTH ARMS MEASURE DIFFERENT THINGS AND NEITHER SUBSUMES THE OTHER,
    which is recorded because a single arm was believed to cover both and did
    not. A byte read out of a body is in range by construction, so
    ``0 <= byte < 256`` grades nothing. The DEPENDENCE arm counts how many body
    positions the returned tag byte moves with, and one is the only honest
    answer for a one-byte field; a reader widening its read to two bytes was
    measured GREEN against every other control here, cursor included. The CURSOR
    arm counts how many bytes the tag-carried branch consumes past a plainly-read
    control word of the same length, which catches a byte inserted BESIDE the
    value rather than in it. The cursor arm says nothing about WHICH words are in
    the reader's set: the tag-carried branch bypasses the extra-string step and
    advances exactly one, so any word added to that set satisfies it
    automatically. What bounds the population is :func:`_value_is_the_tag_byte`,
    whose arms are graded by HAND-AUTHORED counters beside this test, because no
    word this module can reach distinguishes them on the shipped tree.
    """
    unread = sorted(word for word in _PROBED_TAG_WORDS if _tag_reader_read(word) is None)
    assert not unread, (
        f"the shipped tag reader declines the synthetic tag built for {unread}, so the "
        "derivation has no verdict for those words and counts them as carrying no tag "
        "byte. THAT IS INDISTINGUISHABLE FROM A REAL ANSWER at the call site and it is "
        "why this is checked here: a grammar change, or a head longer than "
        f"_SYNTHETIC_TAG_SLACK ({_SYNTHETIC_TAG_SLACK} bytes), silently empties the "
        "exemption instead of reddening. Lengthen the slack or fix the synthetic tag."
    )

    carried = _tag_carried_one_byte_values()
    assert carried, (
        "the shipped tag reader returns a tag-carried value byte for no probed word at "
        "all, so the exemption in the key bound is empty. Every word the status mapping "
        "records that is not in the fixed-width table would then read as ungoverned, "
        "which is a FALSE RED rather than a hole - but it means this derivation has "
        "stopped reading the reader and nothing downstream of it means anything."
    )

    saturated = sorted(carried & frozenset(objects._FIXED_WIDTH_VALUES))  # noqa: SLF001
    assert not saturated, (
        f"the derivation reports {saturated} as carrying its value byte in the TAG, and "
        "the shipped fixed-width table reads those same words from a counted run of "
        "stored bytes. Both cannot be true of one word, and the direction that matters "
        "is the exemption: a derivation admitting words it should not admit exempts "
        "them from the key bound, which is the CS-480 route reopened one layer along - "
        "a length-prefixed type shipping a byte-order status with nothing behind it."
    )

    for word in sorted(carried):
        plain = "Z" * len(word)
        plain_read = _tag_reader_read(plain)
        assert plain_read is not None, (
            f"the control word {plain!r} is the same length as {word!r} and exists only to "
            "put the reader's cursor where a plainly-read tag leaves it. The reader "
            "declined it, so there is no cursor to measure the tag-carried word against."
        )
        assert plain_read[3] is None, (
            f"the control word {plain!r} comes back carrying a tag byte of its own, so it "
            "is not a control: it takes the same branch as the word being measured and "
            "the difference below would be zero however wide that branch's field is."
        )
        read = _tag_reader_read(word)
        assert read is not None
        excess = read[1] - plain_read[1]
        assert excess == 1, (
            f"the shipped reader puts {word!r}'s value {excess} bytes further into the "
            f"body than it puts {plain!r}'s, and the two tags are identical up to the "
            "point where the tag-carried branch begins. THIS IS WHAT THE BRANCH CONSUMES "
            "AND NOT THE WIDTH OF THE VALUE - an adversary measured a mutant putting a "
            "padding byte in FRONT of a value that was still one byte, and this arm "
            "reported 2 while an earlier version of this message called that the value's "
            "own width. Either reading is a change to the tag grammar that has to be "
            "re-measured against real saves before any status word here still holds; the "
            "value's own width is the dependence count below."
        )

        positions = _tag_byte_source_positions(word)
        assert len(positions) == 1, (
            f"the tag byte the reader hands back for {word!r} moves with {len(positions)} "
            f"body positions, {positions}, and a one-byte field moves with exactly one. "
            "MEASURED: a reader reading two bytes at that offset while advancing one left "
            "every other control here green, the cursor arm included, with "
            "objects.VALUE_BYTE_ORDER_STATUS still shipping vacuous_one_byte for a value "
            "that had become two bytes wide. Zero positions means the returned byte does "
            "not come from the body at all; more than one means the status word claiming "
            "the byte-order question is retired BECAUSE the value is one byte is unbacked."
        )


#: The fixed-width word the arm controls forge against. Taken from the shipped
#: table rather than named, so it cannot go stale, and it is the RIGHT shape for
#: the job: a word already known to read its value from counted stored bytes, so
#: admitting it to the tag-carried exemption is unambiguously wrong.
_FORGERY_TARGET: Final = sorted(objects._FIXED_WIDTH_VALUES)[0]  # noqa: SLF001


def _tag_byte_decoder(target: str) -> Callable[..., object]:
    """A decoder that builds ``target``'s value out of the tag byte alone.

    Args:
        target: The word to answer for. Every other word is delegated.

    Returns:
        A stand-in for :func:`objects._decode_value`.
    """
    real = objects._decode_value  # noqa: SLF001

    def decode(body: bytes, type_word: str, at: int, size: int, in_tag_byte: int | None) -> object:
        if type_word != target:
            return real(body, type_word, at, size, in_tag_byte)
        return None if in_tag_byte is None else bool(in_tag_byte)

    return decode


def _tag_byte_reader(target: str) -> Callable[..., object]:
    """A reader that hands ``target`` a tag byte the shipped one does not.

    Args:
        target: The word to answer for. Every other word is delegated.

    Returns:
        A stand-in for :func:`objects._read_tag_header`.
    """
    real = objects._read_tag_header  # noqa: SLF001

    def read(body: bytes, at: int, end: int) -> tuple[str, int, int, int | None] | None:
        got = real(body, at, end)
        if got is None or got[0] != target:
            return got
        return (got[0], got[1], got[2], 0)

    return read


def test_the_reader_arm_of_the_exemption_is_load_bearing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A word only the DECODER treats as tag-carried is still not exempt.

    WHY THIS FORGES A WORD INSTEAD OF USING A SHIPPED ONE. On the shipped tree
    the reader arm and the decoder arm admit the SAME single word, so every word
    this module can reach agrees with both arms and a control built out of them
    passes with either arm deleted. MEASURED: four mutants came back MISSED
    against an earlier version of this control that called the predicate
    directly instead of exercising the derivation, and one of them was deleting
    the decoder arm from the derivation outright.

    WHAT IT WOULD MEAN IF THIS FAILED. The exemption from the key bound could be
    widened by an edit to :func:`objects._decode_value` alone, with
    :func:`objects._read_tag_header` never asked - and the word forged here is
    one the shipped fixed-width table already reads from counted stored bytes,
    so its byte order is a live question the exemption would silently retire.
    """
    monkeypatch.setattr(objects, "_decode_value", _tag_byte_decoder(_FORGERY_TARGET))
    assert _FORGERY_TARGET not in _tag_carried_one_byte_values(), (
        f"with the shipped decoder replaced by one that builds {_FORGERY_TARGET!r}'s value "
        "out of the tag byte alone, the derivation exempts it - so the exemption asks the "
        "decoder and not the reader, and the shipped reader hands that word no tag byte at "
        f"all. {_FORGERY_TARGET!r} is in objects._FIXED_WIDTH_VALUES, so this is not a "
        "hypothetical widening: it exempts a type whose value IS a counted run of stored "
        "bytes with a real byte order from the bound that requires one."
    )


def test_the_decoder_arm_of_the_exemption_is_load_bearing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A word only the READER treats as tag-carried is still not exempt.

    THIS IS THE REFUTED ROUTE, RUN IN PROCESS. An adversary widened the shipped
    reader's own literal to an eight-byte type and recorded that word in the
    status mapping: ``vacuous_one_byte`` - the word asserting the byte-order
    question is retired BECAUSE THE VALUE IS ONE BYTE - shipped for a type
    ``objects.py`` claims no value encoding for at all, GREEN over the whole of
    ``tests/save`` with the operator's library present. The reader decides its
    own population by a literal nothing grades, so asking only the reader had
    MOVED the two-line edit rather than removed it.

    The forgery here is that route with the source edit replaced by a patch,
    which is why the derivation requires both shipped sites to agree.
    """
    monkeypatch.setattr(objects, "_read_tag_header", _tag_byte_reader(_FORGERY_TARGET))
    assert _FORGERY_TARGET not in _tag_carried_one_byte_values(), (
        f"with the shipped reader replaced by one that hands {_FORGERY_TARGET!r} a tag byte, "
        "the derivation exempts it from the key bound - so the exemption asks the reader and "
        "nothing else, and a reader naming a wider or length-prefixed type then carries the "
        "whole claim on its own. The shipped decoder reads that word's value from counted "
        "stored bytes, which is exactly what the second arm is there to notice."
    )


def test_each_arm_of_the_tag_byte_predicate_rejects_its_own_counter() -> None:
    """The three arms are graded one at a time, by hand-authored decoders.

    NO SHIPPED WORD SEPARATES THESE ARMS, so the counters are fabricated
    decoders rather than type words - which is also the only way to grade them
    on a machine with no game. MEASURED against an earlier version that used
    shipped words as counters: dropping the tag-sensitivity arm left every test
    green, and so did dropping the payload-insensitivity arm, because the one
    usable shipped counter was rejected by the undecodable arm before either of
    them was ever consulted. A counter that fires the wrong arm grades nothing.

    THE ACCEPTING CASE IS PART OF THE CONTROL AND NOT A COURTESY. A predicate
    that says no to everything satisfies all three rejections and empties the
    exemption, which reads downstream as a false red rather than as a hole.
    """
    read = _tag_reader_read(_FORGERY_TARGET)
    assert read is not None, "the forgery target does not read, so no arm can be exercised"

    def undecodable(*_args: object) -> object:
        return None

    def ignores_the_tag(*_args: object) -> object:
        return True

    def moves_with_the_payload(
        body: bytes, _word: str, at: int, _size: int, in_tag_byte: int | None
    ) -> object:
        return (in_tag_byte, body[at])

    def payload_sourced_at_one_tag_byte(
        body: bytes, _word: str, at: int, _size: int, in_tag_byte: int | None
    ) -> object:
        if in_tag_byte == _TAG_BYTE_PROBES[0]:
            return False
        return int(body[at]) + 1

    counters = (
        (undecodable, "returns None, so the type is not decoded at all"),
        (ignores_the_tag, "ignores the tag byte, so that byte is not the value"),
        (
            moves_with_the_payload,
            "moves with a stored byte, so the tag byte is not the whole value",
        ),
        (
            payload_sourced_at_one_tag_byte,
            "sources its value from a stored byte at one tag byte and not the other, "
            "which two slices of the probe cannot see and which an adversary shipped "
            "past this predicate",
        ),
    )
    for fake, why in counters:
        with pytest.MonkeyPatch.context() as patch:
            patch.setattr(objects, "_decode_value", fake)
            assert not _value_is_the_tag_byte(_FORGERY_TARGET, read), (
                f"_value_is_the_tag_byte accepts a decoder that {why}. That arm is doing "
                "nothing, and with it gone the exemption admits a type whose value is not "
                "the byte the tag carries - which is the claim vacuous_one_byte makes and "
                "the reason this predicate exists."
            )

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(objects, "_decode_value", _tag_byte_decoder(_FORGERY_TARGET))
        assert _value_is_the_tag_byte(_FORGERY_TARGET, read), (
            "_value_is_the_tag_byte rejects a decoder that builds the value out of the tag "
            "byte and nothing else, which is the one shape it exists to accept. Every "
            "rejection above is vacuous in that state."
        )


def _reader_sourcing_the_tag_byte_from(
    target: str, positions: tuple[int, ...]
) -> Callable[..., object]:
    """A reader whose returned tag byte is built from named body positions.

    THE POSITIONS ARE COUNTED FROM THE END OF THE BODY, which is slack the tag
    grammar never reaches, so perturbing one of them changes the forged tag byte
    and nothing else about how the tag parses. That is what makes the count this
    produces a clean expectation rather than an artefact of the grammar.

    Args:
        target: The word to answer for. Every other word is delegated.
        positions: Offsets from the END of the body the forged byte is built from.

    Returns:
        A stand-in for :func:`objects._read_tag_header`.
    """
    real = objects._read_tag_header  # noqa: SLF001

    def read(body: bytes, at: int, end: int) -> tuple[str, int, int, int | None] | None:
        got = real(body, at, end)
        if got is None or got[0] != target:
            return got
        forged = 0
        for rank, offset in enumerate(positions):
            forged += body[len(body) - offset] << (8 * rank)
        return (got[0], got[1], got[2], forged)

    return read


def test_the_dependence_count_reports_a_wider_field_as_wider() -> None:
    """The width arm counts positions, and the counting itself is graded.

    WHY THIS IS A SEPARATE TEST. The dependence arm beside the cursor arm is the
    only thing in this module asserting how many body bytes the tag-carried
    value is built from, so nothing else reddens if that count stops being
    computed - MEASURED: weakening its assertion to a tautology leaves every
    test here green, which is the emptiness shape CS-473 owns rather than
    something this arm can close about itself. What CAN be graded is the counter,
    against readers whose answer is built from a known number of bytes.

    THE ONE-POSITION CASE IS NOT A COURTESY EITHER. A counter that always
    reported 2 would satisfy the widened case and fail the shipped tree, and one
    that always reported 0 would satisfy neither - but a counter that reported 1
    unconditionally would pass the shipped tree while calling a two-byte field
    one byte, which is the exact defect the arm exists to catch.
    """
    for positions, expected in (((), 0), ((1,), 1), ((1, 2), 2)):
        with pytest.MonkeyPatch.context() as patch:
            patch.setattr(
                objects,
                "_read_tag_header",
                _reader_sourcing_the_tag_byte_from(_FORGERY_TARGET, positions),
            )
            found = _tag_byte_source_positions(_FORGERY_TARGET)
            assert len(found) == expected, (
                f"a reader whose tag byte is built from {len(positions)} body position(s) is "
                f"reported as depending on {len(found)}, {found}. The count is what stands "
                "between a one-byte value and a wider one: a reader reading two bytes at the "
                "tag offset while advancing one was measured GREEN against every other "
                "control here, so a miscount reopens that route silently."
            )


def test_the_oracles_score_something_and_do_not_score_everything() -> None:
    admitted = _admitted_words()
    assert admitted, (
        "the probe reports that no type word at all is scored by a byte-order "
        "oracle. Both graded directions above pass vacuously in that state, because "
        "an empty derived population trivially contains no over-claim. Either every "
        "oracle has been deleted or the probe has stopped reaching them."
    )
    assert admitted < _CANDIDATE_WORDS, (
        "the probe reports EVERY word in objects.VALUE_BYTE_ORDER_STATUS as scored "
        f"by a byte-order oracle, and those words are {sorted(_CANDIDATE_WORDS)}. The "
        "over-claim direction is vacuous in that state: nothing can be marked "
        "anchored without the derivation admitting it. The probe has become "
        "sensitive to something that is not a byte-order judgement."
    )


def test_the_grading_stops_holding_when_the_byte_order_tallies_are_neutered(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The derivation reads the oracles, not something incidental beside them."""
    shipped = _marked_anchored()
    assert shipped <= _admitted_words(), (
        "this control assumes the graded relation holds as shipped, and it does not. "
        "Read test_no_type_is_marked_anchored_that_no_oracle_scores first - that is "
        "the failure, and this test cannot say anything until it is fixed."
    )

    monkeypatch.setattr(
        test_properties,
        "_tally_int32_byte_order",
        lambda value, tally: None,  # noqa: ARG005
    )
    monkeypatch.setattr(
        test_properties,
        "_tally_float32_byte_order",
        lambda value, tally: None,  # noqa: ARG005
    )
    monkeypatch.setattr(
        test_value_anchoring,
        "_tally_mantissa_coarseness",
        lambda reordered, counts: reordered,  # noqa: ARG005
    )

    surviving = sorted(_admitted_words())
    assert not surviving, (
        f"with all three shipped byte-order tallies neutered, {surviving} is still "
        "admitted by the derivation. The requirement here is EMPTINESS rather than "
        "mere shrinkage, and the difference is not pedantry: an assertion that the "
        "graded relation merely stops holding is satisfied when any single word "
        "drops out, so it would pass while a second word went on being admitted by "
        "something that is not an oracle. Whatever still admits these words has to "
        "be found before either graded direction means anything."
    )


def test_the_probe_reaches_all_three_shipped_oracles() -> None:
    """The derivation cannot grade an oracle it never runs.

    MEASURED, not inferred, and it is why this test exists rather than a sentence.
    The first version of this module probed the byte channel with one pair whose
    two halves both carried EQUAL interior stored bytes. The mantissa-coarseness
    oracle admits a value only when those bytes differ, so it was called ZERO
    times across a whole derivation while the module claimed to read all three
    oracles, and the neutering control's third patch was inert. A second fault
    hid behind the first: the two channels were combined with an early return, so
    the byte channel only ever ran for words the value channel had already
    declined - which are exactly the words no oracle scores.

    COUNTING THE CALLS IS THE POINT. Both faults leave every other test in this
    module green, because the one word the coarseness oracle scores is also
    scored by a magnitude oracle, so the derived population comes out right for
    the wrong reason. Only a count can tell a reached oracle from an unreached
    one.

    TWO LIMITS, BOTH MEASURED, NEITHER PAPERED OVER. First, this counts CALLS and
    not EFFECT: a tally gutted to return its input unchanged still registers, and
    this module stays green on it - other modules under ``tests/save`` are what
    catch that, so it is a real gap in THIS control rather than in the suite.
    Second, the coarseness oracle is reached but is NOT load-bearing for the
    derived population: neutering it alone changes the admitted set by nothing,
    because the one word it scores is scored by a magnitude oracle too. So this
    test establishes that the probe exercises every oracle, and NOT that every
    oracle earns its place in the result.
    """
    required = _dispatched_tally_names()
    assert required, (
        "no _tally_ call was found in either shipped dispatch body, so this test "
        "would require nothing of the probe. Either the dispatch was restructured "
        "or the derivation has stopped reading it."
    )

    owners = {
        name: module
        for name in required
        for module, _attribute in _DISPATCH_SITES
        if hasattr(module, name)
    }
    unowned = sorted(required - set(owners))
    assert not unowned, (
        f"the dispatch calls {unowned} and neither dispatch module defines it, so "
        "the reach count cannot patch it and cannot report on it."
    )

    calls: Counter[str] = Counter()

    def counted(name: str, wrapped: object) -> object:
        def call(*args: object) -> object:
            calls[name] += 1
            return wrapped(*args)  # type: ignore[operator]

        return call

    with pytest.MonkeyPatch.context() as patch:
        for name, module in owners.items():
            patch.setattr(module, name, counted(name, getattr(module, name)))
        _admitted_words()

    unreached = sorted(required - set(calls))
    assert not unreached, (
        f"the derivation ran without ever calling {unreached}, so it grades a "
        "population those oracles had no part in producing. An oracle the probe "
        "cannot reach reads as scoring nothing, which is a FALSE RED in the "
        f"under-claim direction and silent coverage loss in the over-claim one. "
        f"Calls observed: {dict(calls)}."
    )


def test_the_status_words_are_pinned_and_distinct() -> None:
    """A symbol-following control cannot see the word a reader actually sees.

    THIS IS THE ONE PLACE A LITERAL IS THE RIGHT CONTROL, and the reason is the
    artifact's purpose. The whole point of shipping byte-order status as DATA
    rather than prose is that something outside this repository can read it, and
    what such a reader sees is the STRING. Every other control here - this
    module's, and the vacuity control in ``test_value_anchoring`` - selects by
    SYMBOL, so the yardstick moves with the data and the swap is invisible.

    MEASURED: exchanging the string values of ``BYTE_ORDER_VACUOUS`` and
    ``BYTE_ORDER_ANCHORED_NOT_UNIQUE`` leaves the shipped mapping recording
    ``anchored_not_unique`` for two ONE-BYTE types that no oracle scores, and
    ``vacuous_one_byte`` for the two an oracle does - retiring the live question
    and inventing a settled one - with the whole of ``tests/save`` green.
    """
    assert objects.BYTE_ORDER_VACUOUS == "vacuous_one_byte"
    assert objects.BYTE_ORDER_ANCHORED_NOT_UNIQUE == "anchored_not_unique"
    assert objects.BYTE_ORDER_ORACLE_CANNOT_SEPARATE == "oracle_cannot_separate_readings"
    assert objects.BYTE_ORDER_UNSCORED == "unscored"

    words = (
        objects.BYTE_ORDER_VACUOUS,
        objects.BYTE_ORDER_ANCHORED_NOT_UNIQUE,
        objects.BYTE_ORDER_ORACLE_CANNOT_SEPARATE,
        objects.BYTE_ORDER_UNSCORED,
    )
    assert len(set(words)) == len(words), (
        f"two of the three status words are spelled the same: {words}. Every "
        "control over this data selects by symbol, so a collapse leaves each of "
        "them passing while the distinction the data exists to record is gone."
    )

    shipped = sorted(set(objects.VALUE_BYTE_ORDER_STATUS.values()) - set(_GRADED_STATUS_WORDS))
    assert not shipped, (
        f"objects.VALUE_BYTE_ORDER_STATUS ships the status word(s) {shipped}, which "
        "this module does not grade and therefore cannot judge. THIS IS THE HOLE THE "
        "SPELLING PIN ABOVE DOES NOT CLOSE, and it is strictly worse than the "
        "over-claim CS-476 was filed against: every graded direction here selects by "
        "SYMBOL, so a type carrying a word outside this set is invisible to all of "
        "them and passes VACUOUSLY. A fourth word was shown shipping "
        "'settled_uniquely' for a type no oracle scores at all, with the whole suite "
        "green. objects.BYTE_ORDER_STATUSES cannot close this - it is a hand-written "
        "set in the same file, so the edit that adds a word extends it too. If a new "
        "status word is genuinely needed - CS-421's remaining half will need one - "
        "then ADD IT HERE AND STATE HOW IT IS GRADED. Reddening until someone does "
        "that is the entire point."
    )

    assert frozenset(_GRADED_STATUS_WORDS) == objects.BYTE_ORDER_STATUSES, (
        f"objects.BYTE_ORDER_STATUSES is {sorted(objects.BYTE_ORDER_STATUSES)} and this "
        f"module grades {sorted(_GRADED_STATUS_WORDS)}. THE EXPORTED VOCABULARY IS A "
        "SEPARATE ARTIFACT FROM THE MAPPING'S VALUES and bounding one does not bound the "
        "other: that set is in __all__, it is what _byte_order_status's docstring says it "
        "returns a member of, and a word added to it ships as part of this module's public "
        "answer while no type carries it yet. Bounding only the values left that open."
    )


def test_the_hand_written_anchored_set_holds_no_unscored_type() -> None:
    """The graded mapping hides part of its own input from grading.

    MEASURED: adding ``Int8Property`` to ``objects._BYTE_ORDER_ANCHORED_VALUES``
    leaves the whole of ``tests/save`` green. :func:`objects._byte_order_status`
    tests the one-byte width FIRST and returns vacuous, so a one-byte word in
    that set never reaches the mapping and the tests over the mapping cannot see
    it. The set's own comment calls it the types an oracle actually scores, and
    that claim was true of only part of the set until this test existed.
    """
    unscored = sorted(objects._BYTE_ORDER_ANCHORED_VALUES - _admitted_words())  # noqa: SLF001
    assert not unscored, (
        f"objects._BYTE_ORDER_ANCHORED_VALUES names {unscored} as scored by a "
        "byte-order oracle and no oracle scores it. For a word wider than one byte "
        "this ships as a status claiming evidence that does not exist; for a "
        "one-byte word it ships as nothing at all, because the width branch "
        "answers first - which is what makes this a separate test from the one "
        "grading the mapping."
    )


def test_the_cannot_separate_set_is_bounded_without_a_library() -> None:
    """What can be held against the cannot-separate set without reading a save.

    THIS IS A BOUND AND NOT THE VERDICT, and the name says so because the
    distinction is the whole point of the word. Whether an oracle was applied to
    a type and came back undecided is a fact about the OPERATOR'S LIBRARY, and
    this module reads none - so nothing here can tell
    ``objects.BYTE_ORDER_ORACLE_CANNOT_SEPARATE`` from
    ``objects.BYTE_ORDER_UNSCORED``. The derivation that can is
    ``tests/save/test_value_anchoring.py::test_the_cannot_separate_status_is_derived_from_the_oracle``
    and it SKIPS on a machine with no game, which is CS-426's recorded gap. What
    is left here is the shape of the shipped set, and two ways it can be wrong on
    its face are invisible to every test that reads only the mapping.

    THE ONE-BYTE ROUTE IS THE SWALLOWED-MEMBER DEFECT AGAIN, one branch along.
    :func:`objects._byte_order_status` tests the width FIRST, so a one-byte word
    added to the set never reaches its own branch and never appears in the
    mapping - which is exactly what the anchored set needed its own test for.

    THE OVERLAP ROUTE IS NEW WITH THE THIRD BRANCH AND DID NOT EXIST BEFORE IT. A
    word in both named sets takes the earlier branch silently, so the shipped
    mapping reads ``anchored_not_unique`` while this set asserts the opposite
    about the same word, and nothing reading the mapping can see the disagreement.

    ONE EQUALITY COVERS BOTH, which is why they are not enumerated. Requiring the
    words the shipped mapping actually surfaces to equal the declared set routes
    the check through :func:`objects._byte_order_status` itself, so it grades what
    that function DOES rather than transcribing the order of its branches - and a
    branch reordered, a width changed or a word added to two sets all show up in
    the same place.

    WHAT IS DELIBERATELY NOT RESTATED HERE. Whether a word this set names is one
    the shipped dispatch already scores is governed by
    :func:`test_no_type_an_oracle_scores_is_left_recorded_as_unscored`, which
    requires every admitted word to be recorded anchored. Asserting it again here
    would put one fact in two places, and the copy is the one that goes stale.
    """
    declared = objects._BYTE_ORDER_CANNOT_SEPARATE_VALUES  # noqa: SLF001
    assert declared, (
        "objects._BYTE_ORDER_CANNOT_SEPARATE_VALUES is empty, so this test grades "
        "nothing and the status word ships with no type carrying it. A declared word "
        "no type carries is the state the vocabulary bound was written to catch."
    )

    surfaced = {
        word
        for word, status in objects.VALUE_BYTE_ORDER_STATUS.items()
        if status == objects.BYTE_ORDER_ORACLE_CANNOT_SEPARATE
    }
    assert surfaced == set(declared), (
        f"objects._BYTE_ORDER_CANNOT_SEPARATE_VALUES names {sorted(declared)} and the "
        f"shipped mapping surfaces {sorted(surfaced)} as "
        f"{objects.BYTE_ORDER_ORACLE_CANNOT_SEPARATE!r}. A word named and not surfaced "
        "was answered by an earlier branch: either it is one byte wide, in which case "
        "the width branch called it vacuous, or it is also in "
        "objects._BYTE_ORDER_ANCHORED_VALUES, in which case the mapping calls it "
        "anchored while this set says an oracle could not separate it. Both ship a "
        "false claim in a set no reader of the mapping can check. A word surfaced and "
        "not named means the mapping grew a route into this status that does not come "
        "from the declared set at all."
    )

    outside = sorted(set(declared) - set(objects._FIXED_WIDTH_VALUES))  # noqa: SLF001
    assert not outside, (
        f"{outside} is named as a type a byte-order oracle was applied to and could "
        "not separate, and it is not decoded from a fixed number of stored bytes at "
        "all. THE POPULATION IS BOUNDED EXACTLY for the reason the mapping's own bound "
        "records: a status about a type this reader does not read from a fixed width "
        "is a claim with nothing behind it, whatever the word says, and an earlier "
        "version of the mapping's bound shipped green while recording a byte order for "
        "a length-prefixed type."
    )
