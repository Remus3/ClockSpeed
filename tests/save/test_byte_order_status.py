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
  :func:`_value_is_the_tag_byte` is what asks. THE HONEST BOUND AS CS-480 LEFT
  IT: what is gone is every route that leaves the shipped decode untouched, and
  an editor changing BOTH shipped sites still widened the exemption, at a price
  that disclosure never gave. THAT IS CS-487, and the arms that red on it are
  the saturation arm below and
  :func:`test_no_word_the_exemption_admits_is_one_the_module_declines_to_measure`,
  whose docstring is the one owner of the measured price. NO COUNT IS REPEATED
  HERE - two of them were wrong in a first draft precisely because they were
  written twice. Graded by
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
  modules that skip without one. THAT WAS CS-481 AND IT IS CLOSED ON ITS
  STATED ACCEPTANCE, not on the width table having become bounded. The two
  controls at the foot of this module are what red on the reproduction, plus
  the phase-4 no-install gate that re-runs the same suite behind them; the
  third control this work added, beside the split check in ``test_properties``,
  is GREEN on that reproduction and is named here because a count of three
  invites the wrong mapping. What a widening still costs, and the routes that
  still work, are written down where those controls live rather than claimed
  here - and one of them needs no width entry at all.

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
from tests.save import synthetic, test_properties, test_value_anchoring

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

    THE BOUND, STATED RATHER THAN LEFT TO BE READ AS A CLOSURE. What this
    derivation retires is any route that leaves the shipped decode untouched. An
    editor changing BOTH shipped sites still widens it, and this docstring used
    to price that residual at nothing at all - CS-487 measured it, narrowed it
    at the saturation arm below and at
    :func:`test_no_word_the_exemption_admits_is_one_the_module_declines_to_measure`,
    and left it OPEN rather than closed. That test owns the price and the
    surviving routes; no count is repeated here. A word that does not read
    reports no verdict
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
    altogether. It can SATURATE onto words the module reads out of the
    PAYLOAD. And it can admit a word that is in no shape table at all, which
    :func:`_value_is_the_tag_byte` holds rather than an arm here, together with
    the two load-bearing controls beside this test and with
    :func:`test_no_word_the_exemption_admits_is_one_the_module_declines_to_measure`.

    THE SATURATION ARM'S POPULATION WAS WIDENED BY CS-487 AND THE SENTENCE IT
    REPLACED WAS MEASURED FALSE. That arm intersected the fixed-width table
    alone, while this paragraph and the arm's own message both named A
    LENGTH-PREFIXED TYPE as the thing it guards against - which it could not
    see, because such a word is not in that table to intersect with. MEASURED by
    a refutation pass: widening both shipped tag-carried sites to a word already
    in :data:`objects.MEASURED_VALUE_TYPES` and reading it as one byte shipped
    ``vacuous_one_byte`` for a length-prefixed type with the tree green. The arm
    now intersects every table this module reads a value out of the payload
    from, and what that still does not reach is priced in
    :func:`test_no_word_the_exemption_admits_is_one_the_module_declines_to_measure`.

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

    read_from_the_payload = (
        frozenset(objects._FIXED_WIDTH_VALUES)  # noqa: SLF001
        | objects._ONE_STRING_VALUES  # noqa: SLF001
        | objects._TWO_STRING_VALUES  # noqa: SLF001
    )
    saturated = sorted(carried & read_from_the_payload)
    assert not saturated, (
        f"the derivation reports {saturated} as carrying its value byte in the TAG, and "
        "the shipped tables read those same words out of the PAYLOAD - from a counted "
        "run of stored bytes, or from one or two length-prefixed strings. Both cannot "
        "be true of one word, and the direction that matters is the exemption: a "
        "derivation admitting words it should not admit exempts them from the key "
        "bound, which is the CS-480 route reopened one layer along - a length-prefixed "
        "type shipping a byte-order status with nothing behind it. THE POPULATION USED "
        "TO BE THE FIXED-WIDTH TABLE ALONE while this message already named a "
        "length-prefixed type as what it guards, and that gap was measured rather than "
        "suspected - see CS-487."
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


def test_no_word_the_exemption_admits_is_one_the_module_declines_to_measure() -> None:
    """CS-487 - the tag-carried exemption's real cost, which CS-480 priced wrong.

    THE ROUTE THIS ARM CLOSES, RE-MEASURED IN A CLONE OF `8ec3dbb` WITHOUT THIS
    ARM BEFORE IT WAS WRITTEN. THREE LINES in ``objects.py`` and NO TEST-SIDE
    LINE AT ALL - a word written into the ``VALUE_BYTE_ORDER_STATUS`` literal
    beside the tag-carried entry, plus the two shipped tag-carried sites
    :func:`objects._read_tag_header` and :func:`objects._decode_value` widened to
    admit it - ship ``vacuous_one_byte`` for an EIGHT-byte Unreal type this repo
    names in no table at all, at ``tests/save`` 1059 passed and 49 skipped ON A
    MACHINE WITH NO GAME, the same counts that clone gives untouched. CS-480
    disclosed that an edit to BOTH shipped sites still widens the exemption
    without pricing what it costs. The prose sites that carried that pricing now
    point here, and THIS DOCSTRING IS THE ONE OWNER OF THE PRICE.

    THE COUNTING CONVENTION, STATED ONCE BECAUSE TWO DRAFTS OF THIS DOCSTRING
    DISAGREED WITHOUT IT.
    ``tests/save/test_phase4_gate.py::test_the_save_suite_passes_with_no_install_and_no_save``
    re-runs this whole suite, so it fails alongside whatever else fails and is
    EXCLUDED from every count below. A line count is EDITED LINES, added and
    modified alike, because widening a literal modifies a line rather than
    adding one and counting only additions understated one route by two.

    WHAT IT READS, AND WHY IT MUST BE A TABLE THE ROUTE DOES NOT TOUCH. The
    derivation above asks the shipped reader and the shipped decoder whether a
    word is tag-carried, and the route answers YES at both - it edits exactly
    those two sites, so no amount of asking them harder separates it.
    :data:`objects.MEASURED_VALUE_TYPES` is what :func:`objects._decode_payload`
    reads to decide whether a value that did not come back is unmodelled content
    or a walk that is no longer where it believes it is, and both tag-carried
    sites are function bodies, so neither can move it. A word the shipped
    decoder BUILDS A VALUE FOR is decoded by definition, so a word this
    exemption admits while that table declines to name it has the module
    recording a settled byte order for a type it also records as one it does not
    decode. MEASURED on the tree carrying this arm: the three-line route above
    reds this arm and nothing else.

    THAT TABLE IS DERIVED, NOT HAND-AUTHORED, AND THAT BOUNDS THIS ARM RATHER
    THAN BACKING IT. An earlier draft of this docstring called it hand-authored
    and a refutation pass measured that false: it is the union of
    ``objects._FIXED_WIDTH_VALUES`` with the two string-shaped sets and two
    written-in words, so A WORD ADDED TO THE WIDTH TABLE ENTERS IT FOR FREE.
    This arm is silent on that route - a width-table word is not tag-carried, so
    it never reaches the population here at all - and what it bounds is the
    TAG-CARRIED route and nothing else.

    THIS NARROWS THE EXEMPTION AND MUST NEVER BE LOOSENED INTO ADMITTING TO IT.
    An earlier version of the key bound ADMITTED any word in that table, and
    shipped green while the mapping recorded ``vacuous_one_byte`` against
    ``StrProperty``, a length-prefixed type - which is CS-480's own defect. This
    is a CONJUNCT on top of the derived exemption and never a disjunct beside
    it: a word still has to be one both shipped sites treat as tag-carried, and
    now also one the module records as measured. Rewriting it as
    ``carried | measured`` anywhere reopens that route.

    THIS ARM ALONE WAS NOT ENOUGH AND A REFUTATION PASS MEASURED IT, WHICH IS
    WHY THE SATURATION ARM ABOVE WAS WIDENED IN THE SAME WORK. Requiring the
    word to be in the measured set does nothing against an attacker who PICKS a
    word already in it rather than adding one, and six of the eleven are neither
    one byte wide nor in the fixed-width table. MEASURED: three shipped lines
    plus two in ``tests/save/test_properties.py``, naming a LENGTH-PREFIXED type
    already in the measured set, shipped ``vacuous_one_byte`` for it with the
    tree green at 1060 passed and 49 skipped - CS-480's own defect, reached
    again. The saturation arm now intersects every table this module reads a
    value out of the payload from, which reds that route, and the one measured
    word left in no shape table reds eight tests at three lines.

    WHAT IT DOES NOT CLOSE, PRICED RATHER THAN NAMED, BECAUSE STOPPING AT THE
    FIRST RED IS HOW THE LAST BOUND WAS OVERSTATED - and both routes below were
    taken all the way to green on the tree carrying both arms rather than left
    at the red they first hit. SEVEN EDITED LINES reach green at ``tests/save``
    1060 passed and 49 skipped, five in ``objects.py`` and two in
    ``tests/save/test_properties.py``: take a word already in the measured set,
    sever it from the shape table that reads it, re-declare it measured, widen
    both tag-carried sites and write the status entry, then move its fixture tag
    and expected value. A word the module has never NAMED costs EIGHT edited
    lines to the same green, five in ``objects.py`` and three in
    ``tests/save/test_properties.py``. So this exemption costs seven lines
    across two files rather than three lines in one file, and no route through
    it is closed.

    THE SURVIVING ROUTE IS CS-490 AND IT IS NOT CS-488'S. CS-488's acceptance is
    scoped to a WIDTH-TABLE entry and neither route above touches a width table,
    so satisfying CS-488 need not red either; an earlier draft handed this to
    CS-488 and a refutation pass measured that assignment wrong. What the three
    items share is the root none of them closes: a module that CLAIMS a type
    consistently everywhere contradicts itself nowhere, and every control here
    is keyed on a contradiction.

    THE POPULATION IS THE WORDS THE STATUS MAPPING NAMES, through
    :data:`_PROBED_TAG_WORDS`. A reader widened for a word that is never written
    into that mapping is not probed here, and it ships no byte-order claim
    either, which is the whole of what this module bounds.

    It needs no save library - it is a claim about the repo, not about a world.
    """
    carried = _tag_carried_one_byte_values()
    assert carried, (
        "the tag-carried exemption is empty, so this arm has nothing to grade and "
        "would pass on any module at all. The derivation test above owns that "
        "failure and reports it with the diagnosis; it is repeated here because a "
        "vacuous pass is indistinguishable from a real one at this call site."
    )

    undeclared = sorted(carried - objects.MEASURED_VALUE_TYPES)
    assert not undeclared, (
        f"{undeclared} are exempted from the key bound as tag-carried, so "
        "objects.VALUE_BYTE_ORDER_STATUS may record a byte order for them, and "
        "objects.MEASURED_VALUE_TYPES does not name them at all. The shipped decoder "
        "BUILDS A VALUE for each - that is what the exemption's own derivation just "
        "asked it - so the module is recording a settled byte order for a type it "
        "also records as one it does not decode. THE TWO HALVES ARE READ FROM "
        "DIFFERENT PLACES ON PURPOSE: the exemption comes from executing the two "
        "shipped tag-carried sites, and that table is what objects._decode_payload "
        "reads to tell unmodelled content from a walk that has lost its place, so "
        "an edit to those two sites cannot move it - both are function bodies. It "
        "is DERIVED and not hand-authored, which bounds this arm rather than "
        "backing it, and the docstring says where. Widening the measured set to "
        "silence this is not a fix - it is the rest of the route, and what it "
        "costs is written in this test's docstring."
    )


#: The fixed-width word the arm controls forge against. Taken from the shipped
#: table rather than named, so it cannot go stale, and it is the RIGHT shape for
#: the job: a word already known to read its value from counted stored bytes, so
#: admitting it to the tag-carried exemption is unambiguously wrong.
_FORGERY_TARGET: Final = min(objects._FIXED_WIDTH_VALUES)  # noqa: SLF001


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


# ---------------------------------------------------------------------------
# CS-481 - THE OTHER SUBTRAHEND. What bounds membership of the WIDTH TABLE.
#
# The key bound above subtracts two sets from the words the status mapping
# records: the fixed-width table, and the tag-carried exemption. CS-480 derived
# the exemption. THE WIDTH TABLE WAS SELF-AUTHORISING - a word placed there
# needed no reader, no decoder agreement and no exemption, because
# `objects._byte_order_status` calls any width-1 entry vacuous on arithmetic
# alone and the mapping is a comprehension over that table.
#
# THE REPRODUCTION, RE-MEASURED HERE BEFORE ANYTHING WAS WRITTEN. Three lines in
# `objects.py` - a `(1, "<b")` entry for `Int64Property`, its
# `WIDTH_SHIPPING_GROUNDS` entry, and holding the word out of
# `MEASURED_VALUE_TYPES` - ship `vacuous_one_byte` for an EIGHT-byte type whose
# value encoding that module explicitly claims nothing about, at `tests/save`
# 1055 passed and 49 skipped ON A MACHINE WITH NO GAME, byte-identical to the
# clean tree there. Each line is load-bearing and was measured alone: the width
# entry by itself reds four tests, the width entry plus its grounds reds three,
# and the width entry plus the severed measured set reds two. All three
# together red nothing.
#
# THE TWO ARMS BELOW, AND WHY NEITHER SUBSUMES THE OTHER. They are aimed at
# different lines of that edit and they read different things.
#
#   THE CLAIM ARM asks whether the module CONTRADICTS ITSELF. `objects.py`
#   carries its own record of what it claims nothing about, and that record is
#   hand-authored somewhere else entirely, for another purpose, with its own
#   graded relationships. A word cannot both carry a byte-order status and be
#   recorded as a region whose value encoding is unclaimed. The pre-existing
#   split control requires the UNION of the two halves to cover every word the
#   region table names; it never required the INTERSECTION to be empty, and the
#   reproduction lives in exactly that gap.
#
#   THE WALK ARM asks the SHIPPED PARSER instead of reading a set, and it is
#   what the third line of the reproduction is aimed past. Severing the width
#   table from `MEASURED_VALUE_TYPES` does not stop the parser decoding the
#   word - `objects._decode_value` dispatches on the width table directly - it
#   changes how `objects._decode_payload` COUNTS a disagreement. MEASURED on the
#   forged tree: a tag declaring a size the width table refuses comes back
#   counted as UNMEASURED CONTENT rather than as a walk that is not where it
#   believes it is. That is the CS-417 conflation the walk's own docstring names
#   as the half of non-negotiable 7 with no second chance, and it is visible
#   with no save library at all.
#
# WHAT THIS DOES NOT CLOSE. THREE REFUTATION PASSES ATTACKED THIS WORK AND ALL
# THREE SUCCEEDED, so everything below is measured rather than reasoned, and the
# drafts that were wrong are recorded rather than deleted.
#
#   THE FIRST DRAFT OF THIS PARAGRAPH claimed four shipped-data edits plus one
#   test-side line still widen the table, and stopped at a red it had measured
#   at
#   `test_properties.py::test_the_synthetic_fixture_exercises_every_measured_type_word`.
#   That red is real; the conclusion drawn from it was not. TWO SEPARATE PASSES
#   took the route two lines further and it goes GREEN. The "decodable instance
#   of the type" that red seemed to demand is, for a width-1 lie, one
#   `struct.pack("<b", ...)` fixture tag and one expected-value line. SIX
#   LINES - three in `objects.py`, three in `test_properties.py` - ship
#   `vacuous_one_byte` for an EIGHT-byte type with the whole tree green on a
#   machine with no game. What the module then does is CLAIM the type in five
#   places rather than contradict itself in two. That difference is what this
#   item's acceptance turns on and it is NOT a reason to call the route closed.
#
#   THE ROUTE THAT NEEDS NO WIDTH ENTRY AT ALL was cheaper still and was never
#   this item's mechanism. Writing a word straight into the
#   `VALUE_BYTE_ORDER_STATUS` literal beside `BoolProperty`, and widening the
#   two shipped tag-carried sites `_read_tag_header` and `_decode_value` to
#   admit it, shipped `vacuous_one_byte` for an eight-byte type in THREE lines,
#   all in `objects.py`, with no test-side line at all and the whole tree green.
#   That was CS-480's disclosed residual, priced there as "an edit to both
#   shipped sites" with no account of how cheap both sites are. THAT IS CS-487,
#   and the reproduction in this paragraph is DEAD, kept as the record of what
#   these two arms do not reach. A CHEAPER ROUTE THROUGH THE SAME EXEMPTION
#   SURVIVES and is filed as CS-490; do not read the death of this one as the
#   death of the mechanism. The arm that reds on it is
#   `test_no_word_the_exemption_admits_is_one_the_module_declines_to_measure`,
#   beside the exemption's derivation rather than here, and it owns the price.
#
#   WHAT PUTS A WORD IN REACH OF THESE CONTROLS IS THAT THE MODULE NAMES IT,
#   and the two arms differ on this. Both read tables keyed by type word, so a
#   type this module has never mentioned walks past the CLAIM arm, which has
#   nothing to intersect with. The WALK arm does not depend on the word being
#   named: measured, a never-named type declared one byte wide and severed from
#   the measured set reds it and nothing else in the suite. So the severance
#   line is bounded word-agnostically and the contradiction line is bounded
#   only for the words the region table names.
#
# WHAT IS GONE is the three-line route this item was filed on: an edit that
# leaves the module's own two-way classification contradicting itself while its
# walk reports a desynchronisation as unmodelled content.
# ---------------------------------------------------------------------------

#: The property name the payload probes below decode under. The walk joins on
#: it and nothing else about it turns anything, so it is spelled to be
#: unmistakably synthetic - a rendered failure here must never read as content
#: out of a world.
_PAYLOAD_PROBE_NAME: Final = "ClockspeedProbeProperty"

#: The name that ends a payload's tag run. It is a literal in
#: :func:`objects._decode_payload` and it is spelled here rather than imported
#: because there is nothing to import: the walk compares against this word
#: inline.
_PAYLOAD_TERMINATOR: Final = "None"

#: A tag's guid-present flag, absent. :func:`objects._skip_guid_flag` accepts 0
#: and 1 and refuses everything else, and 0 is the shape with no guid to step
#: over - which is what keeps the probe's value offset free of any arithmetic
#: this module would have to keep in step with that reader.
_NO_GUID_FLAG: Final = b"\x00"

#: The text written into each tag-extra string the probe has to present. Its
#: CONTENT turns nothing - :func:`objects._skip_tag_extra` steps over these
#: without reading them - so it is spelled to be unmistakably synthetic.
_PROBE_TAG_EXTRA: Final = "ClockspeedProbeTagExtra"

#: What a property type word ends in. Every one of them does, which is the
#: structural fact ``test_properties`` grades the whole vocabulary against; it
#: is used here only to tell a region-table key that names a TYPE from one that
#: names a run of bytes.
_TYPE_WORD_SUFFIX: Final = "Property"

#: The one type word whose tag data carries a guid the reader steps over rather
#: than reads. Spelled once here because two places below need it.
_STRUCT_WORD: Final = "StructProperty"

#: The size the unmeasured-word control declares. NOTHING TURNS ON THE NUMBER -
#: a word the walk does not measure is counted before any width is consulted.
#: It is four so the control presents the same tag shape a real four-byte
#: scalar does rather than a degenerate one.
_CONTROL_DECLARED_SIZE: Final = 4

#: WHAT ONE PROBED TAG DID TO THE SHIPPED WALK'S OWN BOOKKEEPING. These name
#: OUTCOMES rather than counters, because two of the counters mean opposite
#: things and collapsing them is the conflation
#: :func:`objects._decode_payload` documents: an unmeasured type is unmodelled
#: content and says nothing about the walk, while a measured type whose bytes
#: disagree means the reader is not where it believes it is and every value
#: after it in the payload is suspect.
_WALK_DECODED: Final = "decoded"
_WALK_DISAGREED: Final = "measured_type_whose_bytes_disagreed"
_WALK_UNMEASURED: Final = "unmeasured_type"
_WALK_SILENT: Final = "counted_as_nothing"
_WALK_BROKE: Final = "the_walk_did_not_reach_its_terminator"


def _one_tag_payload(word: str, declared_size: int, value: bytes) -> bytes:
    """One hand-authored payload carrying a single tag of one type word.

    HAND-AUTHORED BYTES, NOT A SLICE OF ANYTHING. Every field below is written
    here: a property name, a type word, the declared size, the tag's index
    field, an absent guid flag, the value bytes and the terminator name. The
    string framing comes from ``tests/save/synthetic.py`` rather than being
    re-rolled, so a change to the length-prefix shape is felt here too.

    THE VALUE BYTES ARE THE CALLER'S, AND WHAT THAT BUYS TODAY IS SMALLER THAN
    THE FIRST DRAFT OF THIS PARAGRAPH CLAIMED. It argued the parameter exists
    because a fixture writing zeros into a run the parser reads structurally can
    never fail the reader that reads them - which is true of this project and
    was refuted as a description of this function: EVERY call site below passes
    ``bytes(n)``, all zeros. So the parameter buys visibility at the call site
    and nothing else yet, and the zeros are sound here for a reason that does
    not generalise - none of the three arms turns on the value's CONTENT, only
    on whether a value came back at all.

    THE TAG-EXTRA SHAPE IS BUILT RATHER THAN AVOIDED, AND AN ADVERSARY IS WHY.
    The first version of this builder emitted no tag-extra strings, and the
    words that carry them were filtered out of the CONTROL population with that
    as the stated reason - while the GRADED arms iterated the width table raw
    and had no such filter. MEASURED by that pass against the shipped word
    ``ByteProperty``, which carries one tag-extra string and whose raw shape is
    genuinely one byte: the probe returned the broken-walk outcome at every
    size, so a later slice moving that word into the fixed-width table would
    have been reddened by a message blaming the width table for what was a
    defect in this builder. Asking :data:`objects._TAG_EXTRA_STRINGS` how many
    strings the word takes, and adding a StructProperty's stepped-over guid,
    removes the filter from both places instead of adding one.

    Args:
        word: The type word the tag declares.
        declared_size: The size the tag declares for its value.
        value: The value bytes laid down where the tag says the value begins.

    Returns:
        A payload beginning at its first tag name and ending at its terminator.
    """
    extras = objects._TAG_EXTRA_STRINGS.get(word, 0)  # noqa: SLF001
    stepped_guid = bytes(objects.GUID_BYTES) if word == _STRUCT_WORD else b""
    return (
        synthetic.fstring(_PAYLOAD_PROBE_NAME)
        + synthetic.fstring(word)
        + struct.pack("<i", declared_size)
        + bytes(objects._TAG_INDEX_FIELD_BYTES)  # noqa: SLF001
        + synthetic.fstring(_PROBE_TAG_EXTRA) * extras
        + stepped_guid
        + _NO_GUID_FLAG
        + value
        + synthetic.fstring(_PAYLOAD_TERMINATOR)
    )


def _walk_verdict(word: str, declared_size: int, value: bytes) -> str:
    """What the SHIPPED payload walk made of one probed tag.

    THE VERDICT IS READ OFF THE WALK'S OWN COUNTERS AND NOT OFF A SET. That is
    the whole reason this exists: whether a type is measured is decidable by
    reading ``objects.MEASURED_VALUE_TYPES``, and reading it would grade the
    constant against itself. What the walk DOES with a type is a different
    fact, and it is the one that reaches a caller.

    THE OUTCOMES ARE EXCLUSIVE BY CONSTRUCTION because the payload carries
    exactly one tag, so at most one of the walk's three channels can have
    moved. :data:`_WALK_SILENT` is reachable only if that stops being true, and
    it is named rather than folded into the broken case so a probe that
    stops presenting a tag at all is distinguishable from one whose tag was
    refused.

    Args:
        word: The type word the tag declares.
        declared_size: The size the tag declares for its value.
        value: The value bytes.

    Returns:
        One of the ``_WALK_*`` outcomes.
    """
    body = _one_tag_payload(word, declared_size, value)
    walked = objects._decode_payload(body, 0, len(body))  # noqa: SLF001
    if walked is None:
        return _WALK_BROKE
    decoded, unmeasured, disagreed, reached = walked
    if not reached:
        return _WALK_BROKE
    if decoded:
        return _WALK_DECODED
    if disagreed:
        return _WALK_DISAGREED
    if unmeasured:
        return _WALK_UNMEASURED
    return _WALK_SILENT


def _words_the_module_records_as_unclaimed() -> frozenset[str]:
    """The type words the region table names and the probe can present.

    DERIVED FROM THE SHIPPED REGION TABLE rather than listed, so a word moved
    into or out of it moves this population without this module being edited.
    ONE filter narrows it and it is about what a tag IS, not about what the
    probe can build: a key that is not a type word at all - the trailing run is
    one - has no tag to present.

    THERE WAS A SECOND FILTER AND AN ADVERSARY REMOVED IT, WHICH IS RECORDED
    BECAUSE THE FILTER WAS THE DEFECT. It held out the words carrying tag-extra
    strings, on the stated ground that :func:`_one_tag_payload` could not build
    their tag shape. The graded arms that this population controls carried no
    such filter, so the exclusion narrowed the CONTROL while leaving the arms
    exposed to exactly the words it admitted were unbuildable. The builder
    presents the tag-extra shape now, so four more words grade the probe here
    and no word has to be held out of either place.

    Returns:
        Every type word the region table records that the probe can present.
    """
    return frozenset(
        word for word in objects.UNMEASURED_PAYLOAD_REGIONS if word.endswith(_TYPE_WORD_SUFFIX)
    )


def test_the_walk_outcome_words_are_pinned_and_distinct() -> None:
    """The outcome words are what a failure message shows, and no control read them.

    A REFUTATION PASS FOUND THIS AS AN EQUIVALENT MUTANT AND IT IS THE SAME
    DEFECT THE STATUS WORDS ALREADY HAVE A PIN FOR. Exchanging the string
    values of :data:`_WALK_DISAGREED` and :data:`_WALK_UNMEASURED` leaves every
    control here green, because both the data and the yardstick are the same
    symbol. What it changes is the DIAGNOSTIC: a genuine desynchronisation then
    reports itself as unmeasured content in the rendered message, which is the
    exact conflation the arms below exist to refuse, moved from the code into
    the sentence a reader acts on.

    IT IS A WEAKER PIN THAN THE STATUS ONE AND THE DIFFERENCE IS WORTH STATING.
    A status word is shipped DATA that something outside this repository reads.
    These five are internal to this module and reach a reader only through a
    failure message. That is still a reader, and a control whose message says
    the opposite of what happened is worse than no message.

    NEEDS NO SAVE LIBRARY - it is a claim about this module.
    """
    assert _WALK_DECODED == "decoded"
    assert _WALK_DISAGREED == "measured_type_whose_bytes_disagreed"
    assert _WALK_UNMEASURED == "unmeasured_type"
    assert _WALK_SILENT == "counted_as_nothing"
    assert _WALK_BROKE == "the_walk_did_not_reach_its_terminator"

    outcomes = (_WALK_DECODED, _WALK_DISAGREED, _WALK_UNMEASURED, _WALK_SILENT, _WALK_BROKE)
    assert len(set(outcomes)) == len(outcomes), (
        f"two of the walk outcome words are spelled the same: {outcomes}. Every arm "
        "below compares a verdict against one of these symbols, so a collapse leaves "
        "each arm passing while two outcomes that mean opposite things become one."
    )


def test_no_word_carries_a_byte_order_status_the_module_records_as_unclaimed() -> None:
    """The width table's membership, held against the module's own other half.

    CS-481. A byte-order status is a claim about how a type's bytes are read,
    and ``objects.UNMEASURED_PAYLOAD_REGIONS`` is where this module records the
    types it claims nothing about. One word cannot honestly be in both, and
    until this test existed one could: the reproduction on that item puts
    ``Int64Property`` into the width table while its region entry goes on
    saying, in tracked source, that not a width, not a byte order and not an
    instance count is claimed for it.

    WHY THE PRE-EXISTING SPLIT CONTROL DOES NOT COVER THIS, which is the reason
    a whole test is spent on one intersection.
    ``tests/save/test_properties.py::test_every_type_word_the_module_names_is_on_one_side_of_its_own_split``
    requires every word the region table NAMES to sit in one half or the other.
    It is a UNION check. A word in BOTH halves satisfies it, and satisfies it
    more comfortably than a word in either.

    IT IS NOT A TRANSCRIPTION AND THE ASYMMETRY IS WHAT MAKES IT ONE SOURCE
    RATHER THAN TWO COPIES. Nothing here lists which words may carry a status.
    The two tables are authored for different jobs in different parts of the
    module - one drives a decoder, the other records what a later slice still
    has to measure - and this asserts only that they do not contradict each
    other.

    NEEDS NO SAVE LIBRARY - it is a claim about the repo, not about a world.
    """
    regions = objects.UNMEASURED_PAYLOAD_REGIONS
    assert regions, (
        "objects.UNMEASURED_PAYLOAD_REGIONS is empty, so this test grades nothing. An "
        "empty region table is also the cheapest way to satisfy it, which is why the "
        "emptiness is refused here rather than left to read as a clean result."
    )
    assert objects.VALUE_BYTE_ORDER_STATUS, (
        "objects.VALUE_BYTE_ORDER_STATUS is empty, so no word can be in both tables and "
        "this test grades nothing. Deleting the status data is not a way to satisfy it."
    )

    contradicted = sorted(frozenset(objects.VALUE_BYTE_ORDER_STATUS) & frozenset(regions))
    assert not contradicted, (
        f"objects.py records a byte-order status for {contradicted} and ALSO records the "
        "same word in UNMEASURED_PAYLOAD_REGIONS, where its entry says what this module "
        "does not claim about that type's value encoding. Both cannot be true. THE "
        "DIRECTION THAT MATTERS IS THE STATUS: a word reaches the status mapping by "
        "sitting in the fixed-width table, and membership of that table needs no reader, "
        "no decoder and no exemption - objects._byte_order_status calls any width-1 entry "
        f"{objects.BYTE_ORDER_VACUOUS} on arithmetic alone. So the cheap way to retire a "
        "byte-order question for a type nothing has measured is to declare it one byte "
        "wide, and this is what refuses it. Either the region entry is stale and the "
        "measurement that retired it should be cited where the width is shipped, or the "
        "width entry is a claim the module has not earned - do not delete the region "
        "entry to silence this."
    )


def test_every_fixed_width_word_is_one_the_shipped_walk_counts_as_measured() -> None:
    """A width table entry the walk does not treat as measured, asked of the walk.

    CS-481, the arm the reproduction's THIRD line is aimed past. Holding a word
    out of ``objects.MEASURED_VALUE_TYPES`` while leaving it in the width table
    does NOT stop the shipped parser decoding it - :func:`objects._decode_value`
    dispatches on the width table directly. What it changes is how
    :func:`objects._decode_payload` COUNTS a tag whose declared size the width
    table refuses. MEASURED on the forged tree: that tag comes back counted as
    unmeasured content, where every honest member of the table comes back
    counted as a measured type whose bytes disagreed. Those two counters mean
    opposite things - one is unmodelled content, the other is a walk that is
    not where it believes it is - and the walk's own docstring names collapsing
    them as the half of non-negotiable 7 that has no second chance.

    THE CONTROL RUNS FIRST, AND THE TWO SENTENCES THAT JUSTIFIED IT HERE WERE
    BOTH MEASURED FALSE BY REFUTATION PASSES. They said a constant probe "would
    satisfy two of the three" arms and that without the control a builder which
    stopped presenting a readable tag "would still be graded green". Neither
    holds: the three arms require three DISTINCT outcome words, so a constant
    probe satisfies at most ONE of them, enumerated over all five words; and a
    builder that stops presenting a tag cannot produce the DECODED outcome, so
    the agreeing arm reds on its own. Do not restore either sentence.

    WHAT THE ARM IS ACTUALLY FOR, measured two ways rather than argued. Sever
    the shipped walk from :data:`objects.MEASURED_VALUE_TYPES` - so a
    disagreement is counted as a disagreement unconditionally - AND neuter this
    arm, and the whole of this module comes back 16 passed: the disagreement arm
    alone cannot tell a walk that consults the measured set from one that does
    not, because at width + 1 both count the same way. This arm is what fails
    there. It also catches the reverse edit, a word added to a string-valued
    family while its region entry stands, which the arms below never see.

    WHY THE WIDTH IS PROBED AT TWO SIZES. At the declared width the value has
    to decode, or a table entry could name a width the walk can never reach and
    the disagreement arm would pass for the wrong reason. At one byte more it
    has to be REFUSED and counted as a disagreement, which is the arm the
    severed measured set fails.

    WHAT IS DELIBERATELY NOT ASSERTED HERE, AND A REFUTATION PASS MADE IT
    SHARPER THAN "NOT ASSERTED". Nothing here says the width is RIGHT - that
    rests on the operator's library and skips without one. Measured, both arms
    are narrower than they read. The agreeing arm takes the width out of the
    shipped table and :func:`objects._decode_fixed_width` tests the declared
    size against that same table, so NO self-consistent entry can fail it - an
    entry pairing a width of 1 with a code that unpacks eight bytes was
    measured passing. And at width + 1 the decode always returns None, so the
    disagreement arm reduces to asking whether the word is in
    :data:`objects.MEASURED_VALUE_TYPES`, which is DERIVED from the width
    table. The edit either arm can catch is an edit to that derivation - which
    is the reproduction's third line, and is exactly what the wider routes
    recorded in the block above decline to touch.

    NEEDS NO SAVE LIBRARY - the payloads are hand-authored in this file.
    """
    unclaimed = _words_the_module_records_as_unclaimed()
    assert unclaimed, (
        "objects.UNMEASURED_PAYLOAD_REGIONS names no type word this probe can present, "
        "so the control below grades nothing and the arms it serves are ungraded too. "
        "Either the region table has stopped naming type words, or every word it names "
        "now carries tag-extra strings the probe's tag shape does not build."
    )
    for word in sorted(unclaimed):
        verdict = _walk_verdict(word, _CONTROL_DECLARED_SIZE, bytes(_CONTROL_DECLARED_SIZE))
        assert verdict == _WALK_UNMEASURED, (
            f"objects.py records {word!r} as a payload region whose value encoding it "
            f"claims nothing about, and the shipped walk reports {verdict!r} for a tag "
            f"carrying it rather than {_WALK_UNMEASURED!r}. THIS IS THE CONTROL AND NOT "
            "A FINDING ABOUT THAT WORD: the arms below require this probe to distinguish "
            "a measured type from an unmeasured one, and a probe that cannot reach the "
            "unmeasured outcome at all grades them vacuously. Fix the probe before "
            "reading anything into the arms below."
        )

    widths = objects._FIXED_WIDTH_VALUES  # noqa: SLF001
    assert widths, "the shipped fixed-width table is empty, so this test grades nothing"

    for word, (width, _) in sorted(widths.items()):
        agreeing = _walk_verdict(word, width, bytes(width))
        assert agreeing == _WALK_DECODED, (
            f"the shipped fixed-width table gives {word!r} a width of {width}, and a tag "
            f"declaring exactly that size comes back {agreeing!r} rather than "
            f"{_WALK_DECODED!r}. A width the walk cannot reach a value through is not a "
            "measurement of anything, and the disagreement arm below would then pass "
            "for the wrong reason - it would be refusing a value that never decoded."
        )

        disagreeing = _walk_verdict(word, width + 1, bytes(width + 1))
        assert disagreeing == _WALK_DISAGREED, (
            f"a tag declaring {width + 1} bytes for {word!r}, one more than the width "
            f"this module ships for it, comes back {disagreeing!r} rather than "
            f"{_WALK_DISAGREED!r}. THE TWO OUTCOMES MEAN OPPOSITE THINGS and "
            "objects._decode_payload counts them separately for that reason: "
            f"{_WALK_UNMEASURED!r} says this project never measured the type and the "
            f"walk is fine, while {_WALK_DISAGREED!r} says the type IS measured and the "
            "reader is not where it believes it is. MEASURED: adding a width-1 entry for "
            "a type objects.py claims nothing about, and holding that word out of "
            "MEASURED_VALUE_TYPES, ships a byte-order status for it AND makes the walk "
            "report its desynchronisations as unmodelled content. The width table drives "
            "the decode directly, so severing it from the measured set does not stop the "
            "decode - it only stops the walk telling the truth about it."
        )
