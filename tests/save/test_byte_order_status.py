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
import textwrap
from collections import Counter
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
#: measured: emptying it entirely leaves this module green at 8 passed, because
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

#: The value types whose single byte rides in the TAG rather than in the
#: fixed-width table, so no width can be derived for them. ``BoolProperty`` is
#: the whole set: :func:`objects._read_tag_header` takes its byte at a fixed
#: offset and hands it back separately, which is why ``objects.py`` writes it
#: into the status mapping explicitly instead of deriving it. Named here so the
#: key population can be bounded EXACTLY rather than left open to any measured
#: word - which is what let a length-prefixed type ship as one byte.
_TAG_CARRIED_ONE_BYTE_VALUES: Final = ("BoolProperty",)

#: The status words this module knows how to grade. PINNED AS LITERALS, which is
#: the one deliberate transcription here: these strings are the artifact's
#: interface to a reader outside this repository, and every control over the data
#: - this module's and ``test_value_anchoring``'s - selects by SYMBOL, so nothing
#: that follows a symbol can see a spelling change or a word added beside it.
_GRADED_STATUS_WORDS: Final = ("vacuous_one_byte", "anchored_not_unique", "unscored")

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

    ungoverned = sorted(_CANDIDATE_WORDS - decoded - frozenset(_TAG_CARRIED_ONE_BYTE_VALUES))
    assert not ungoverned, (
        f"objects.VALUE_BYTE_ORDER_STATUS records a byte order for {ungoverned}, which is "
        "not decoded from a fixed number of stored bytes and is not one of the tag-carried "
        "one-byte values. THE POPULATION IS BOUNDED EXACTLY, and an earlier version of this "
        "assertion admitted any word in MEASURED_VALUE_TYPES - which shipped green while the "
        "mapping recorded vacuous_one_byte against StrProperty, a LENGTH-PREFIXED type whose "
        "payload carries an int32 length. That retires an int32 byte-order question with no "
        "evidence at all, using no new status word, so neither the vocabulary bound nor any "
        "graded direction fired. A status about a type this reader does not read from a fixed "
        "width is a claim with nothing behind it, whatever the word says."
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
    assert objects.BYTE_ORDER_UNSCORED == "unscored"

    words = (
        objects.BYTE_ORDER_VACUOUS,
        objects.BYTE_ORDER_ANCHORED_NOT_UNIQUE,
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
