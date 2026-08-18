"""Anchoring for the decoded fixed-width VALUE, and a census of the size field.

WHY THIS MODULE EXISTS. CS-421 clause 3 asked for the byte order of decoded
property values to be settled against something that is not this project's own
writer. The answer shipped in ``test_properties`` was
``test_the_int32_byte_order_is_discriminated_by_the_stored_high_byte``, and it
was adjudicated REFUTED in session 14 for a reason worth restating rather than
citing: that oracle reduces each decoded value to TWO BITS - whether the stored
high byte is zero and whether the low byte is zero - and it owns no control
tying either bit to the value's OWN four bytes. Displacing the IntProperty
value start by +4, so the decode reads the next tag's name-length prefix and
touches the int32 not at all, leaves that oracle GREEN and scoring BETTER than
the correct read.

WHY +4 IS THE DISPLACEMENT WORTH CONTROLLING WITH, and this module derives it
rather than asserting it - see
``test_the_displacement_the_value_oracle_tolerates_is_the_one_the_anchor_catches``.
That oracle is a CONJUNCTION of two assertions: a majority carrying the
small-magnitude signature as read, and a MINORITY carrying it under the swapped
reading. The as-read majority does survive several displacements. The second
half does not, and treating the first half's survival as the whole oracle's
survival is a widening that stood in this docstring and was measured false.
Across a displacement of up to one whole value width either way, +4 is the only
one the conjunction survives - which is exactly what makes it the control worth
having, and is asserted here rather than written down.

THE THREE MEASUREMENTS HERE ARE ABOUT THREE DIFFERENT THINGS, and conflating
them is the failure this module is written to avoid.

  THE EXTENT ANCHOR asks WHICH BYTES a decoded fixed-width value is read from.
  It compares the shipped decoder reading in place against the SAME decoder
  reading an isolated copy of exactly the declared bytes, surrounded by poison.
  Under a displacement the isolated read walks into poison and the two
  disagree, which is the detection the two-bit oracle has no way to make.

  THE SIZE-FIELD CENSUS asks which byte order the tag's DECLARED SIZE is read
  in, graded by how many payloads still reach their terminator. That is a
  different field, read by a different reader, and what it licenses is written
  at the test rather than left for a reader to infer.

  THE SURVIVOR DERIVATION asks which permutations the VALUE oracles are unable
  to separate from the identity, and ties the answer to the shipped candidate
  set. It is the anti-overclaim control: it is what stops the shipped data
  drifting into claiming the value byte order is settled when the oracles behind
  that claim do not settle it. THREE ORACLES FEED IT. Two are shipped in
  ``test_properties``; the third is the mantissa-coarseness oracle owned here,
  which is CS-469 and is the one that separates the middle pair.

THE TWO CENSUSES NO LONGER END THE SAME WAY, and the asymmetry is now the
honest reading rather than the symmetry that preceded it. The SIZE field
narrows to the as-stored ordering and the one that swaps its two HIGH bytes,
which are indistinguishable on every declared size small enough to leave those
bytes zero; that narrowing is not closed here and its separating population is
small enough that saying so matters. The VALUE narrows to the as-stored
ordering alone.

WHAT CHANGED WAS THE PREDICATE AND NOT THE CORPUS, which is worth stating
because the opposite was ruled once and refuted. The two shipped value oracles
left the middle swap standing while the census's admitted population - the
float32 values whose middle bytes differ - is reported by the run that measures
it. The evidence was there and the shipped float oracle's magnitude band was too
wide to use it. THE VALUE RESULT LICENSES
NOTHING ABOUT THE SIZE FIELD. They are different fields read by different
readers, and the boundary is written down beside the shipped constant rather
than crossed.

WHAT THE ANCHOR DOES NOT COVER, stated here and again at each test that uses
it, because attributing a gap to a control unable to fire on it is a mistake
this project's history records twice.

  IT ESTABLISHES WHICH BYTES ARE READ, NOT WHAT FUNCTION THEY GO THROUGH. Both
  readings hand the same declared bytes to the same decoder, so ANY pure
  function of the declared extent agrees with itself and the anchor stays
  green. A constant is the degenerate case of that class and is CS-455's; a
  data-dependent transform of the right bytes is the same blind spot at full
  width, and was measured leaving every test here green while thousands of
  values decoded wrong.

  THE LOCATOR IS SHARED between the two readings, so a fault in where the tag
  header believes the value starts moves both together and is invisible here.

  THE POPULATION IS THE FIXED-WIDTH TYPES ALONE.

PRIVACY, non-negotiables 11 and 12. COUNTS ONLY leave a sweep. No property
name, no decoded value, no file path and no body byte reaches a failure
message, an assertion, a print or an exception raised out of this module.

THE CONTAINMENT IS STATED AS WHAT THE CODE DELIVERS RATHER THAN AS WHAT WOULD
BE REASSURING, because an earlier revision of this paragraph claimed every read
sat inside a ``try`` while the statement appending the read save to a list sat
outside one, in a frame holding both the path and the raw bytes. Forced under a
mutant with ``pytest -l``, that frame rendered the save-tree account directory,
a world-derived save name and raw header bytes - and the redactor in
``tests/conftest.py`` does not catch those, because it works from the Windows
account name and the home prefix and never from the save-tree account
directory. That is CS-466's recorded gap. So: ONE save is read at a time by
:func:`_read_tagged_save`, whose every statement including its returns is
inside its ``try``; each sweep's whole loop body is inside its own handler; and
no list of save bytes is accumulated, so a rendered frame can hold at most the
one save being walked. The two discovery helpers are IMPORTED from
``test_properties`` rather than transcribed, on the same reasoning that
module's siblings give.

THE CONTAINMENT STOPS AT ``BaseException``. ``Exception`` and ``SystemExit``
are held; ``KeyboardInterrupt`` is deliberately left free to unwind, on the
terms ``test_decode_oracles`` sets out and for the same reason.

NO OBSERVED COUNT IS WRITTEN INTO AN ASSERTION OR A DOCSTRING HERE. The corpus
is the operator's live save library and it grows on every autosave, so a
payload total, a tag total or a mismatch total is stale before it can be
committed - and a constant sitting at an observed value going red on a correct
tree is CS-432, already open. The assertions are structural: zero, nonzero,
equality with a population, argmax, majority, set equality. A count may be
interpolated into a failure MESSAGE, where it is derived in the same run that
reports it.
"""

from __future__ import annotations

import ast
import itertools
import math
import struct
from collections import Counter
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from functools import cache, lru_cache
from pathlib import Path
from types import MappingProxyType
from typing import Final

import pytest

from clockspeed.save import chunks, header, objects

# IMPORTED RATHER THAN COPIED, for the reason ``test_decode_oracles`` gives at
# its own import of this module: ``_library_save_paths`` and
# ``_cached_usmap_or_none`` each close a leak their docstrings describe, and the
# two value-oracle tallies are the SUBJECT of the survivor derivation below, so
# a transcription of either would grade a copy instead of the shipped judgement.
from tests.save import test_properties

#: The property terminator, as the shipped walk spells it. A TRANSCRIPTION, and
#: the only one this module holds: ``objects`` exports no name for it - the
#: literal is bare at its one site inside the shipped payload walk - so there is
#: no name to import without editing that module. ``test_decode_oracles`` holds
#: the same transcription for the same reason, and both walks stop on the same
#: word, so a change in the shipped reader alone strands both.
_TERMINATOR: Final = "None"

#: Filler surrounding an isolated value slice. NON-ZERO AND LOAD-BEARING, not
#: cosmetic, and the reason is measured rather than argued.
#:
#: With a bare four-byte slice and no padding, ``struct.unpack_from`` reads a
#: NEGATIVE offset as counting from the END of the buffer. At a displacement of
#: -4 that wraps to offset 0, the isolated read returns the true value, and the
#: control was measured to AGREE on thousands of IntProperty tags where the
#: padded form disagrees on all of them. At -1 the same bare form raises
#: ``struct.error`` on every tag instead, and an exception escaping the sweep
#: unwinds through frames holding the body, which is non-negotiable 12. Padding
#: both sides puts every displacement this control uses inside a real buffer,
#: and each call is wrapped in its own ``try`` regardless.
_POISON: Final = b"\xa5" * 8

#: Where the isolated value sits inside its padded buffer.
_PAD: Final = len(_POISON)

#: The displacement the anchor control fires under. FOUR, AND THE GROUND FOR IT
#: IS DERIVED RATHER THAN WRITTEN HERE - see
#: ``test_the_displacement_the_value_oracle_tolerates_is_the_one_the_anchor_catches``,
#: which asserts over :data:`_CANDIDATE_DISPLACEMENTS` that this is the one the
#: refuted value oracle still passes. A control at a displacement the old oracle
#: ALSO catches would demonstrate nothing about what the anchor adds.
#:
#: An earlier revision justified this number by claiming the value oracle
#: survives at -2, -1, +2, +3 and +4. That was measured FALSE: the oracle is a
#: conjunction and its second half fails at four of those five. The claim came
#: from widening "the as-read majority survives" into "the oracle survives".
#: Nothing is written down in its place; the relation is asserted instead.
_ANCHOR_DISPLACEMENT: Final = 4

#: Bytes in the tag's declared-size field, and in a four-byte value. The two
#: are separate fields read by separate readers; the width they share is why
#: one permutation group serves both censuses.
_FOUR_BYTES: Final = 4

#: The displacements the choice above is derived against: every non-zero shift
#: of up to ONE WHOLE VALUE WIDTH either way. A range fixed by the width of the
#: thing being displaced rather than by what the corpus happened to reward, so
#: it is not a set fitted to an answer.
_CANDIDATE_DISPLACEMENTS: Final = tuple(
    delta for delta in range(-_FOUR_BYTES, _FOUR_BYTES + 1) if delta != 0
)

#: Every ordering of four stored bytes, including the identity.
_PERMUTATIONS: Final = tuple(itertools.permutations(range(_FOUR_BYTES)))

#: The as-stored ordering, named so the argmax assertion and the survivor
#: derivation index the same tuple.
_IDENTITY: Final = (0, 1, 2, 3)

#: How many low output positions a declared size below :data:`_HIGH_SIZE_FLOOR`
#: leaves carrying a non-zero byte.
_LOW_SIZE_POSITIONS: Final = 2

#: The smallest declared size needing a byte above the low two output positions.
#: DERIVED FROM THE FIELD'S SHAPE, not from the corpus: below it the two high
#: bytes of a little-endian size are both zero, so any ordering that agrees with
#: the as-stored one on the low two positions reads the identical value.
_HIGH_SIZE_FLOOR: Final = 1 << (8 * _LOW_SIZE_POSITIONS)

#: The orderings the size census CANNOT separate on a small declared size,
#: derived from the permutation group rather than read off a ranking: those
#: agreeing with the as-stored ordering on the low output positions. What is
#: left in the high positions is then zero either way.
_SIZE_ORDERINGS_ALIKE_BELOW_THE_FLOOR: Final = tuple(
    perm for perm in _PERMUTATIONS if perm[:_LOW_SIZE_POSITIONS] == _IDENTITY[:_LOW_SIZE_POSITIONS]
)

#: The width, in the shipped fixed-width table, that no byte order can move.
_ONE_BYTE: Final = 1

#: The two type words the shipped value oracles score, and the keys their
#: tallies are read back out of. Transcribed for the reason
#: ``test_properties`` gives at its own copy: importing the constant under test
#: would assert only that the module equals itself.
_INT_WORD: Final = "IntProperty"
_FLOAT_WORD: Final = "FloatProperty"
_BOOL_WORD: Final = "BoolProperty"

#: The shipped width and struct code for a float32, taken from the table under
#: test so the layout facts below move with it rather than beside it.
_FLOAT_SPEC: Final = objects._FIXED_WIDTH_VALUES[_FLOAT_WORD]  # noqa: SLF001


def _stored_pattern(value: float) -> int:
    """One float32's stored bytes, read back as an integer.

    Args:
        value: The float to store.

    Returns:
        The little-endian stored pattern.
    """
    return int.from_bytes(struct.pack(_FLOAT_SPEC[1], value), "little")


#: THE MANTISSA WIDTH, MEASURED FROM THE FORMAT. ``1.0`` has an all-zero
#: mantissa field, so the bits BELOW its pattern's lowest set bit are exactly
#: the mantissa. Nothing here spells 23.
_MANTISSA_BITS: Final = (_stored_pattern(1.0) & -_stored_pattern(1.0)).bit_length() - 1

#: The whole stored pattern's width in bits, measured the same way. ``-0.0`` sets
#: exactly one bit, the sign, and the sign is the pattern's most significant bit.
_VALUE_BITS: Final = _stored_pattern(-0.0).bit_length()

#: What one stored byte carries, derived from the two above and the shipped
#: value width rather than written as a literal 8.
_BITS_PER_STORED_BYTE: Final = _VALUE_BITS // _FLOAT_SPEC[0]

#: THE BOUNDARY THE TIE PREDICTION RESTS ON, and it is a consequence of the
#: layout rather than a number anybody chose: the mantissa bits living in stored
#: byte ZERO. The middle swap does not move stored byte zero, so a coarseness
#: confined to those bits reads identically under an ordering and under its
#: swapped partner and can discriminate nothing.
#:
#: THAT IS A PREDICTION MADE BEFORE ANY SAVE IS READ, which is what keeps the
#: oracle below out of the fitted-threshold shape. Where the corpus confirms it
#: is
#: ``test_the_mantissa_bits_inside_the_low_stored_byte_separate_no_ordering_from_its_swap``.
_MANTISSA_BITS_IN_STORED_BYTE_ZERO: Final = min(_MANTISSA_BITS, _BITS_PER_STORED_BYTE)

#: Every mantissa width the coarseness oracle scores. QUANTIFIED RATHER THAN
#: CHOSEN: the verdict is a statement about ALL of them at once, so there is no
#: width to tune and nothing that could be narrowed until it happened to
#: separate this corpus - which is the ``_JOIN_WORD_FLOOR`` shape CS-432 exists
#: to remove.
_COARSENESS_WIDTHS: Final = tuple(range(1, _MANTISSA_BITS + 1))

#: The widths that CANNOT tell an ordering from its swapped partner, split from
#: the ones that can at the boundary above rather than at an observed crossover.
_TIED_WIDTHS: Final = tuple(
    width for width in _COARSENESS_WIDTHS if width <= _MANTISSA_BITS_IN_STORED_BYTE_ZERO
)
_DISCRIMINATING_WIDTHS: Final = tuple(
    width for width in _COARSENESS_WIDTHS if width > _MANTISSA_BITS_IN_STORED_BYTE_ZERO
)

#: The interior output positions - those that are neither the low nor the high
#: one. Derived from the width, so nothing here says "one and two".
_INTERIOR_POSITIONS: Final = tuple(range(1, _FOUR_BYTES - 1))

#: THE MIDDLE SWAP: the identity with its interior reversed, which at this width
#: is the exchange of the two middle stored bytes. DERIVED FROM THE WIDTH rather
#: than transcribed from the result it is used to attack - it is defined here
#: without reference to which orderings the shipped oracles happen to leave
#: standing.
_MIDDLE_SWAP: Final[tuple[int, ...]] = (
    *_IDENTITY[:1],
    *reversed(_IDENTITY[1 : _FOUR_BYTES - 1]),
    *_IDENTITY[_FOUR_BYTES - 1 :],
)

#: A hand-authored pattern for the rebind self-check, touching no save. Every
#: byte differs from its neighbours, so a four-byte read moved by any candidate
#: displacement reads a different value.
_SELF_CHECK_PATTERN: Final = bytes(range(4 * _FOUR_BYTES))

#: Where the self-check reads from. INTERIOR, with a whole value width of slack
#: either side, so a NEGATIVE candidate displacement lands inside the buffer
#: rather than wrapping to its end - which is the same ``unpack_from`` behaviour
#: the poison padding exists to defeat, and it would silently make the
#: self-check read the wrong thing rather than raise.
_SELF_CHECK_AT: Final = 2 * _FOUR_BYTES


@dataclass(frozen=True)
class _AnchorSweep:
    """What one anchoring pass over the real library measured. COUNTS ONLY.

    Attributes:
        payloads: Records seen in a save of a pair this grammar reads.
        reached: Those whose payload reached its terminator.
        tags_by_type: Fixed-width tags by type word. The keys are INTERSECTED
            with the shipped table inside the sweep, so no word that is not
            already in tracked source can leave it.
        fixed_width_tags: How many fixed-width tags the anchor graded. Counted
            by TYPE WORD, before any decode, which is why it cannot stand as
            the liveness figure on its own - see ``decoded_values``.
        decoded_values: How many of those tags the in-place read actually
            returned a value for. THE ONE THAT MATTERS FOR LIVENESS: a fault
            that makes every read return None leaves ``fixed_width_tags``
            untouched while ``_agrees(None, None)`` hands back a free agreement
            on every tag, so a zero mismatch count over a fully undecoded
            population would otherwise read as a clean pass.
        mismatches: Tags whose in-place read and isolated read disagreed, or
            where either call raised.
        int_oracle_holds: Whether the REFUTED value oracle in
            ``test_properties`` still returns its green verdict under this
            configuration. Carried so the choice of displacement is derived
            rather than asserted in prose.
        rebind_changed_the_int_read: Whether the displaced decoder returned
            something other than the shipped one on the hand-authored pattern.
            None when nothing was rebound.
        rebind_left_the_float_read_alone: Whether the same displacement left a
            non-IntProperty spec untouched. None when nothing was rebound.
        failures: Exception type NAMES, not the exceptions themselves.
    """

    payloads: int
    reached: int
    tags_by_type: Mapping[str, int]
    fixed_width_tags: int
    decoded_values: int
    mismatches: int
    int_oracle_holds: bool
    rebind_changed_the_int_read: bool | None
    rebind_left_the_float_read_alone: bool | None
    failures: tuple[str, ...]


@dataclass
class _CoarsenessCensus:
    """What the coarseness census admitted and what it graded. COUNTS ONLY.

    THE CENSUS SLICES THE BODY ITSELF, and until this existed nothing graded
    that slice. Displacing it alone by -2 left every test in this module green
    while the census scored two framing bytes and two value bytes - and it
    scored them CLEANER than the real ones, because the byte before a float
    tag's value is zero on every float tag in the library, so a displaced read
    manufactures low-mantissa zeros. THE FAULT MADE THE ORACLE GREENER, which is
    why a displacement-collapse control of the kind the extent anchor uses
    cannot catch it and an EQUALITY control is what does.

    THIS IS NOT THE EXTENT ANCHOR'S BLIND SPOT AND IT IS NOT COVERED BY IT. That
    blind spot is the SHARED LOCATOR - a tag header pointing both readings at
    the wrong place moves them together and is invisible to any comparison
    between them. This is the census's OWN offset, private to this module, and
    it is graded here against the shipped decoder reading in place at the tag's
    own reported start. A shared-locator fault remains outside both.

    Attributes:
        admitted: Values entering the census.
        graded: Admitted values whose TALLIED bytes were checked. Asserted equal
            to ``admitted`` rather than merely non-zero, because a check that
            silently stops running reports the same zero as a check that passes.
        misread: Admitted values whose tallied bytes decode to something other
            than the shipped decoder's in-place read at the tag's own offset.
        inert: Admitted values the middle swap does not change. THE POPULATION
            CLAUSE OF CS-469 LIVES HERE - this is computed at the census's own
            call site from the swap itself, not from the admission helper, so
            neutering the call site's filter is caught even though the helper
            stays honest.
    """

    admitted: int = 0
    graded: int = 0
    misread: int = 0
    inert: int = 0


@dataclass(frozen=True)
class _PermutationSweep:
    """What the two permutation censuses measured. COUNTS ONLY.

    Attributes:
        reach: Payloads reaching a terminator, by size-field permutation.
        int_oracle_holds: Permutations under which the shipped int32 oracle
            still returns its green verdict over the permuted VALUE bytes.
        float_oracle_holds: The same for the shipped float32 oracle.
        coarse_oracle_holds: Permutations that out-coarsen the ordering swapping
            their two interior stored bytes - CS-469's discriminator, and the
            only one of the three that separates the identity from the middle
            swap.
        coarseness: Per-ordering counts of values whose low mantissa bits are
            all zero, keyed by width. Carried out of the sweep so the tie
            region and the discriminating region are graded as measured facts
            of the run that reports them rather than summarised into a verdict.
        coarseness_population: Float32 values admitted to that census - those
            whose interior stored bytes differ, so the swap changes what is
            read. Identical for every ordering by construction, because it is
            decided on the AS-STORED bytes alone.
        coarseness_graded: Admitted values whose tallied bytes were checked
            against the shipped in-place read.
        coarseness_misread: Admitted values whose tallied bytes are not the
            value's own - the census's private offset, graded.
        coarseness_inert_admissions: Admitted values the middle swap does not
            change - the census's private population filter, graded.
        payloads: Payload extents the census walked, per ordering.
        scored_values: How many values the survivor derivation scored under the
            identity, so an empty population cannot pass as agreement.
        tags_above_the_size_floor: Tags declaring a size big enough to need a
            byte above the low two output positions. THE ONLY POPULATION THAT
            CAN SEPARATE the as-stored ordering from the one swapping the two
            high size bytes, which is why the census gates on it rather than
            asserting a separation the corpus may be unable to supply.
        bodies_restored: Whether every in-place size-field permutation was put
            back, so the census graded permutations rather than a body it had
            progressively corrupted.
        failures: Exception type NAMES.
    """

    reach: Mapping[tuple[int, ...], int]
    int_oracle_holds: frozenset[tuple[int, ...]]
    float_oracle_holds: frozenset[tuple[int, ...]]
    coarse_oracle_holds: frozenset[tuple[int, ...]]
    coarseness: Mapping[tuple[int, ...], Mapping[int, int]]
    coarseness_population: int
    coarseness_graded: int
    coarseness_misread: int
    coarseness_inert_admissions: int
    payloads: int
    scored_values: int
    tags_above_the_size_floor: int
    bodies_restored: bool
    failures: tuple[str, ...]


@dataclass
class _Extents:
    """One save's readable payload extents, gathered so a sweep takes one list.

    Attributes:
        body: The decompressed body.
        spans: First tag offset and first byte past the payload, per record
            whose head resolved.
        records: How many records the table held.
    """

    body: bytes
    spans: list[tuple[int, int]] = field(default_factory=list)
    records: int = 0


def _agrees(left: object, right: object) -> bool:
    """Whether two decoded values are the same reading of the same bytes.

    NOT BARE EQUALITY, and the exception is float32 NaN. A save's float fields
    legitimately hold one, ``nan != nan`` by IEEE rule, and counting that as a
    mismatch would report a disagreement the bytes do not contain - inflating
    the very count the shipped anchor asserts is zero.

    Args:
        left: The in-place read.
        right: The isolated read.

    Returns:
        True when the two readings agree.
    """
    if type(left) is not type(right):
        return False
    if isinstance(left, float) and isinstance(right, float):
        return (math.isnan(left) and math.isnan(right)) or left == right
    return bool(left == right)


def _walk_with_the_shipped_reader(
    body: bytes, start: int, end: int
) -> list[tuple[str, int, int]] | None:
    """Walk one payload's tags using the SHIPPED reader and no local width.

    It holds no width of its own. The name read, the tag header and the tag-count
    ceiling are shipped symbols, and the cursor advances by the extent that
    shipped header read reported. The one transcribed literal is the terminator
    comparison on the line below.

    Args:
        body: The decompressed body.
        start: Where the first tag begins.
        end: The first byte past the payload.

    Returns:
        Type word, value start and declared size per tag, or None when the walk
        broke before reaching a terminator.
    """
    tags: list[tuple[str, int, int]] = []
    at = start
    for _ in range(objects._MAX_TAGS_PER_PAYLOAD):  # noqa: SLF001
        name = objects._payload_text(body, at, end)  # noqa: SLF001
        if name is None:
            return None
        if name[0] == _TERMINATOR:
            return tags
        read = objects._read_tag_header(body, name[1], end)  # noqa: SLF001
        if read is None:
            return None
        type_word, value_at, size, _in_tag_byte = read
        tags.append((type_word, value_at, size))
        at = value_at + size
    return None


def _reaches_with_a_permuted_size(
    mutable: bytearray, start: int, end: int, perm: tuple[int, ...]
) -> bool:
    """Walk one payload with the tag's DECLARED SIZE read in a permuted order.

    THE PERMUTATION IS APPLIED TO THE BYTES AND THE SHIPPED READER IS THEN
    ASKED, rather than a local size read being written here. The four size
    bytes are reordered in place, ``objects._read_tag_header`` reads them where
    it always does, and they are put back immediately - so every other field the
    walk touches is the save's own, and what varies is one field's byte order.

    THE RESTORE IS A ``finally``, not a following statement. As a bare statement
    it was skipped whenever the shipped header read raised, leaving the caller's
    buffer permuted for every ordering walked after it - which turns the census
    into a measurement of accumulated damage rather than of byte order.

    Args:
        mutable: A writable copy of the decompressed body, restored on exit.
        start: Where the first tag begins.
        end: The first byte past the payload.
        perm: The ordering to read the size field's four stored bytes in.

    Returns:
        True when the walk reached its terminator.
    """
    # A ``bytearray`` WHERE THE SHIPPED READERS ANNOTATE ``bytes``, and the
    # widening is deliberate rather than sloppy. The permutation has to be
    # applied in place - copying a body per tag would be the same measurement at
    # an unusable cost - and only a mutable buffer allows that. Every operation
    # those readers perform is one both types support: slicing, indexing,
    # decoding a slice, and `struct.unpack_from`. The ignores below are coded
    # rather than blanket, so the next error on the same line still shows.
    at = start
    for _ in range(objects._MAX_TAGS_PER_PAYLOAD):  # noqa: SLF001
        name = objects._payload_text(mutable, at, end)  # type: ignore[arg-type]  # noqa: SLF001
        if name is None:
            return False
        if name[0] == _TERMINATOR:
            return True
        # The size field sits immediately past the tag's TYPE WORD, which is
        # where the shipped header read finds it too. Reading the word here is
        # what locates the field; the shipped read below repeats it.
        type_read = objects._payload_text(mutable, name[1], end)  # type: ignore[arg-type]  # noqa: SLF001
        if type_read is None:
            return False
        after = type_read[1]
        if after + _FOUR_BYTES > end or after + _FOUR_BYTES > len(mutable):
            return False
        keep = bytes(mutable[after : after + _FOUR_BYTES])
        mutable[after : after + _FOUR_BYTES] = bytes(keep[index] for index in perm)
        try:
            read = objects._read_tag_header(mutable, name[1], end)  # type: ignore[arg-type]  # noqa: SLF001
        finally:
            mutable[after : after + _FOUR_BYTES] = keep
        if read is None:
            return False
        _type_word, value_at, size, _in_tag_byte = read
        at = value_at + size
    return False


def _extents_of(data: bytes, parsed: header.SaveHeader) -> _Extents:
    """Decompress one save and list every payload extent in it.

    THE CALLER HOLDS THE ``try``. This function is allowed to raise; each call
    site sits inside a handler that reduces whatever comes out to a type name
    before a frame holding ``data`` or the body is rendered.

    Args:
        data: The save file's bytes.
        parsed: Its parsed header.

    Returns:
        The body and its readable spans.
    """
    body = chunks.decompress_body(
        data, parsed.body_offset, header_version=parsed.header_version
    ).payload
    table = objects.parse_body(
        body, save_version=parsed.save_version, header_version=parsed.header_version
    )
    out = _Extents(body=body, records=len(table.records))
    for record in table.records:
        end = record.body_offset + record.body_length
        start: int | None = record.body_offset
        if record.kind == objects.KIND_ACTOR:
            start = objects._skip_actor_head(body, record.body_offset, end)  # noqa: SLF001
        if start is not None:
            out.spans.append((start, end))
    return out


def _read_tagged_save(path: Path) -> tuple[tuple[bytes, header.SaveHeader] | None, str | None]:
    """Read ONE save, if it is of a pair this grammar reads. Fully contained.

    ONE SAVE, NOT A LIST, and that is a lifetime decision rather than a style
    one. An earlier revision accumulated every tagged save's raw bytes into a
    list held for the whole sweep, so any frame rendered while walking held the
    entire library. Returning one save at a time means the largest thing a
    caller can be holding is the save it is walking.

    EVERY STATEMENT IS INSIDE THE ``try``, INCLUDING THE RETURNS AND THE VERSION
    TEST. In the earlier revision the version test and the list append sat
    outside it with ``path`` and ``data`` both bound, and that frame was forced
    under a mutant with ``pytest -l``: it rendered the save-tree account
    directory, a world-derived save name and raw header bytes. The redactor in
    ``tests/conftest.py`` did not catch any of them, because it is built from
    the Windows account name and the home prefix and knows nothing of the
    save-tree account directory - CS-466's recorded gap, whose own stated bound
    is that discovery sits inside a ``try``.

    Args:
        path: One save file.

    Returns:
        The bytes and parsed header when this save is readable and of a tagged
        pair, otherwise None; paired with an exception type NAME when something
        unexpected was contained, otherwise None.
    """
    try:
        data = path.read_bytes()
        parsed = header.parse_header(data)
        if (parsed.header_version, parsed.save_version) not in test_properties.TAGGED_PAIRS:
            return None, None
        return (data, parsed), None
    except (OSError, header.HeaderError):
        # The two EXPECTED failures - an unreadable file and a save of a
        # version this project does not parse - stay silent skips, because the
        # library legitimately holds both and the callers treat any recorded
        # failure as fatal.
        return None, None
    except (Exception, SystemExit) as exc:
        # THE BACKSTOP. Anything unexpected escaping here unwinds through
        # `path.read_bytes()`, whose bound `self` IS the save path. SystemExit
        # is named because it is not an Exception and was measured elsewhere in
        # this package to render a path under `-q` alone. KeyboardInterrupt is
        # deliberately left free to unwind.
        return None, type(exc).__name__


def _install_displaced_int_decoder(delta: int) -> Callable[[], None]:
    """Rebind the shipped fixed-width decoder to displace ONLY the int32 spec.

    NO PRODUCTION FILE IS EDITED. ``objects._decode_fixed_width`` is a module
    global, so replacing the attribute is a real fault in the real decoder that
    both call sites of the anchor control follow - which is the whole mechanism
    behind the control firing.

    Args:
        delta: How far to displace the value start, in bytes.

    Returns:
        A callable restoring the shipped decoder, for a ``finally``.
    """
    shipped = objects._decode_fixed_width  # noqa: SLF001
    int_spec = objects._FIXED_WIDTH_VALUES[_INT_WORD]  # noqa: SLF001

    def displaced(body: bytes, at: int, size: int, spec: tuple[int, str]) -> object | None:
        """Read an IntProperty from the wrong place and everything else as shipped.

        Args:
            body: The buffer to read from.
            at: The value's first byte, as the caller located it.
            size: The value's declared extent.
            spec: The measured width and its struct code.

        Returns:
            Whatever the shipped decoder returns at the displaced offset.
        """
        return (
            shipped(body, at + delta, size, spec)
            if spec == int_spec
            else shipped(body, at, size, spec)
        )

    objects._decode_fixed_width = displaced  # noqa: SLF001

    def restore() -> None:
        """Put the shipped decoder back."""
        objects._decode_fixed_width = shipped  # noqa: SLF001

    return restore


def _self_check_the_rebind() -> tuple[bool, bool]:
    """Prove the rebind is live and confined, on bytes no save contributed.

    Called while the displacement is installed and BEFORE anything is graded,
    so a control that silently failed to install reports as such rather than
    measuring a shipped tree and calling it a mutant.

    Returns:
        Whether the int32 read moved, and whether a non-int32 spec did not.
    """
    int_spec = objects._FIXED_WIDTH_VALUES[_INT_WORD]  # noqa: SLF001
    float_spec = objects._FIXED_WIDTH_VALUES[_FLOAT_WORD]  # noqa: SLF001
    at = _SELF_CHECK_AT
    (undisplaced,) = struct.unpack_from(int_spec[1], _SELF_CHECK_PATTERN, at)
    (float_undisplaced,) = struct.unpack_from(float_spec[1], _SELF_CHECK_PATTERN, at)
    moved = objects._decode_fixed_width(_SELF_CHECK_PATTERN, at, int_spec[0], int_spec)  # noqa: SLF001
    still = objects._decode_fixed_width(  # noqa: SLF001
        _SELF_CHECK_PATTERN, at, float_spec[0], float_spec
    )
    return (not _agrees(moved, int(undisplaced)), _agrees(still, float(float_undisplaced)))


def _tally_int_value(
    body: bytes,
    value_at: int,
    size: int,
    spec: tuple[int, str],
    tally: test_properties._DecodeTally,
) -> None:
    """Score one int32 the way the REFUTED value oracle scores it.

    Fed from the same read the anchor grades, so the two verdicts in one anchor
    sweep are about one configuration rather than about two walks that might
    disagree.

    Args:
        body: The decompressed body.
        value_at: The value's first byte, as the shipped tag header reported.
        size: Its declared extent.
        spec: The shipped width and struct code.
        tally: The accumulator, mutated in place.
    """
    try:
        value = objects._decode_fixed_width(body, value_at, size, spec)  # noqa: SLF001
    except (Exception, SystemExit):
        return
    if isinstance(value, int) and not isinstance(value, bool):
        test_properties._tally_int32_byte_order(value, tally)  # noqa: SLF001


def _with_the_middle_swapped(perm: tuple[int, ...]) -> tuple[int, ...]:
    """The ordering that reads this one's interior stored bytes the other way.

    Composition on the RIGHT by :data:`_MIDDLE_SWAP`, which is an involution, so
    the permutation group falls into pairs. THE TWO MEMBERS OF A PAIR AGREE ON
    WHICH STORED BYTE REACHES OUTPUT POSITION ZERO, and that single fact is what
    makes the tie prediction hold for every pair rather than only for the
    identity's.

    Args:
        perm: One ordering of the value's stored bytes.

    Returns:
        Its swapped partner.
    """
    return tuple(perm[position] for position in _MIDDLE_SWAP)


def _the_interior_stored_bytes_differ(stored: bytes) -> bool:
    """Whether the MIDDLE SWAP changes this value's bytes.

    THE SCORED POPULATION IS DERIVED FROM THE SWAP, NOT THRESHOLDED. Admission
    turns on the AS-STORED interior bytes, so the population is exactly the
    values on which the identity and the middle swap differ. For that ONE PAIR,
    an excluded value reads the same under both orderings and would add the same
    number to both sides of every comparison - widening the population while
    narrowing no margin.

    THE CLAIM IS ABOUT THAT PAIR AND NOT ABOUT THE GROUP, and an earlier
    revision of this docstring widened it into the group and was measured FALSE.
    A general ordering ``P`` differs from its partner at ``stored[P[1]]`` versus
    ``stored[P[2]]``, which is NOT this criterion: on the hand-authored pattern
    ``[0, 5, 5, 9]`` this function admits nothing while most orderings in the
    group still read differently from their partners. So the population is
    tailored to the identity's pair and to no other.

    WHY THAT IS ENOUGH, and it is a structural reason rather than a hopeful one.
    The survivor derivation INTERSECTS this oracle with the two shipped ones, so
    only an ordering surviving both of those can change what it produces, and
    ``test_the_shipped_candidate_set_is_what_the_value_oracles_cannot_separate``
    asserts that those are exactly the identity and its middle-swapped partner.
    A verdict this oracle returns on any other ordering is scored on a
    population not tailored to it, and no shipped constant depends on it.

    Args:
        stored: The value's stored bytes.

    Returns:
        True when the middle swap changes these bytes.
    """
    return len({stored[position] for position in _INTERIOR_POSITIONS}) > 1


def _tally_mantissa_coarseness(reordered: bytes, counts: Counter[int]) -> bytes:
    """Score one reading of one value for how few mantissa bits it uses.

    AUTHORED FLOATS ARE COARSE, and that is the structure this looks for. A
    clock speed of 1.0, a snapped coordinate, a fraction a designer typed - each
    is representable in few significant mantissa bits, so its low mantissa bits
    are zero. Reading the same bytes in the wrong order puts exponent and
    high-mantissa bits where those zeros were and destroys the structure.

    WHY THIS SUCCEEDS WHERE THE SHIPPED MAGNITUDE BAND CANNOT, POINTED AT
    RATHER THAN ARGUED. That the band cannot separate the middle pair is a
    DERIVED fact of this module: the middle swap is a member of
    ``_PermutationSweep.float_oracle_holds``, and
    ``test_the_mantissa_coarseness_oracle_separates_the_middle_swap_from_the_identity``
    asserts it. The suite reddens if it ever stops being true.

    NO NUMBER IS CITED FOR IT HERE, AND THAT IS DELIBERATE. Three numeric or
    mechanical justifications were offered for this one conclusion in successive
    revisions of this work and ALL THREE WERE MEASURED FALSE - two bounds on how
    far the swap can move a magnitude, then an appeal to a shipped count that
    measures the whole-word REVERSAL rather than the middle swap. The conclusion
    survived every one of them because it never rested on them. Coarseness is
    not a band at all: it counts a structure authored data has and permuted data
    does not.

    Args:
        reordered: The value's stored bytes under one ordering.
        counts: That ordering's accumulator, mutated in place. Keyed by width
            and counting values whose low mantissa bits are all zero to AT LEAST
            that width, so one value contributes to every width it satisfies.

    Returns:
        THE BYTES IT ACTUALLY SCORED. Returned rather than assumed so the census
        control grades what this function consumed instead of what the call site
        meant to hand it - a slice displaced at the call site is otherwise
        invisible to a check sited on the variable the call site did not use.
    """
    mantissa = int.from_bytes(reordered, "little") & ((1 << _MANTISSA_BITS) - 1)
    zeros = _MANTISSA_BITS if mantissa == 0 else (mantissa & -mantissa).bit_length() - 1
    for width in range(1, zeros + 1):
        counts[width] += 1
    return reordered


def _coarse_oracle_holds(
    coarseness: Mapping[tuple[int, ...], Mapping[int, int]], perm: tuple[int, ...]
) -> bool:
    """Whether an ordering out-coarsens the one that swaps its interior bytes.

    ONE OWNER FOR THE PREDICATE, as the two shipped oracles above have, so the
    survivor derivation and every control here ask the same question.

    IT IS ANTISYMMETRIC BY CONSTRUCTION. A strict win at any width for one
    member of a swapped pair is a strict loss for the other, so at most one of a
    pair can pass; a pair tied at every width passes neither. That is what lets
    it remove a candidate rather than merely rank one.

    IT QUANTIFIES OVER THE WIDTH RATHER THAN PICKING ONE. Domination has to hold
    at EVERY width the mantissa admits, with a strict win somewhere. There is no
    width to tune, so the verdict cannot have been fitted to a corpus.

    Args:
        coarseness: Per-ordering counts, keyed by mantissa width.
        perm: The ordering under judgement.

    Returns:
        True when this ordering dominates its partner everywhere and beats it
        somewhere.
    """
    mine = coarseness[perm]
    theirs = coarseness[_with_the_middle_swapped(perm)]
    strict = False
    for width in _COARSENESS_WIDTHS:
        if mine.get(width, 0) < theirs.get(width, 0):
            return False
        if mine.get(width, 0) > theirs.get(width, 0):
            strict = True
    return strict


def _int_oracle_holds(tally: test_properties._DecodeTally) -> bool:
    """Whether the shipped int32 value oracle returns its green verdict.

    ONE OWNER FOR THE PREDICATE, consumed by the displacement derivation and by
    the survivor derivation alike, so the two cannot drift into asking slightly
    different questions and reporting one answer.

    IT IS A CONJUNCTION, and that is the whole point of writing it out. The
    as-read majority is only the first half; the second requires the swapped
    reading to be a MINORITY. Reading the first half as the oracle's verdict is
    the widening that put a false sentence in this module's docstring.

    Args:
        tally: An accumulator the shipped int32 scorer has been fed.

    Returns:
        True when the oracle passes on this population.
    """
    counts = tally.counts
    seen = counts["int32"]
    return (
        seen > 0
        and counts["int32_high_zero"] * 2 > seen
        and counts["int32_high_zero_swapped"] * 2 < seen
    )


def _float_oracle_holds(tally: test_properties._DecodeTally) -> bool:
    """Whether the shipped float32 value oracle returns its green verdict.

    Args:
        tally: An accumulator the shipped float32 scorer has been fed.

    Returns:
        True when the oracle passes on this population.
    """
    counts = tally.counts
    seen = counts["float32"]
    return (
        seen > 0
        and counts["float32_plausible"] * 2 > seen
        and counts["float32_plausible_swapped"] * 2 < seen
    )


@dataclass
class _AnchorTally:
    """What one anchoring sweep folds into, mutated in place.

    Bundled rather than passed as loose counters so the per-save walker keeps a
    signature a reader can hold, and so adding a measurement does not change a
    call site.

    Attributes:
        payloads: Records seen.
        reached: Those whose payload reached its terminator.
        graded: Fixed-width tags matched by type word.
        decoded: Those whose in-place read returned a value.
        mismatches: Those whose two readings disagreed.
        by_type: Fixed-width tags by type word.
        tally: The shipped int32 scorer's accumulator, for the oracle verdict.
    """

    payloads: int = 0
    reached: int = 0
    graded: int = 0
    decoded: int = 0
    mismatches: int = 0
    by_type: Counter[str] = field(default_factory=Counter)
    tally: test_properties._DecodeTally = field(
        default_factory=lambda: test_properties._DecodeTally(Counter(), set(), set())  # noqa: SLF001
    )


def _anchor_one_save(extents: _Extents, into: _AnchorTally) -> None:
    """Fold one save's fixed-width tags into the anchoring accumulators.

    THE CALLER HOLDS THE ``try``. This function is allowed to raise; its only
    call site sits inside the sweep's broad handler, which reduces whatever comes
    out to a type name before a frame holding a body is rendered.

    Args:
        extents: One save's body and its readable payload spans.
        into: The accumulators, mutated in place.
    """
    into.payloads += extents.records
    for start, end in extents.spans:
        tags = _walk_with_the_shipped_reader(extents.body, start, end)
        if tags is None:
            continue
        into.reached += 1
        for type_word, value_at, size in tags:
            spec = objects._FIXED_WIDTH_VALUES.get(type_word)  # noqa: SLF001
            if spec is None:
                continue
            into.by_type[type_word] += 1
            into.graded += 1
            agreed, got_a_value = _anchored(extents.body, value_at, size, spec)
            into.decoded += 1 if got_a_value else 0
            if not agreed:
                into.mismatches += 1
            if type_word == _INT_WORD:
                _tally_int_value(extents.body, value_at, size, spec, into.tally)


@cache
def _sweep_anchor(delta: int | None) -> _AnchorSweep | None:
    """Grade the extent anchor over the real library. COUNTS ONLY.

    KEYED ON ``delta`` SO THE MEMOISATION CANNOT REPLAY A MUTANT. The decode
    sweeps in this package are cached, and looping mutants through one cached
    entry silently replays the first mutant's verdict for every later one - an
    error that cost a previous session real time and produced a false
    conclusion. One cache entry per configuration is what stops it here.

    Args:
        delta: A displacement to install on the int32 spec, or None to grade
            the shipped tree.

    Returns:
        The sweep, or None when no save library is reachable.
    """
    paths = test_properties._library_save_paths()  # noqa: SLF001
    if not paths:
        return None

    restore: Callable[[], None] | None = None
    changed: bool | None = None
    confined: bool | None = None
    into = _AnchorTally()
    failures: list[str] = []
    seen_a_save = False
    try:
        if delta is not None:
            # CONTAINED, and it was not on the first draft of these lines. Both
            # calls read `objects._FIXED_WIDTH_VALUES`, so dropping a word from
            # that shipped table - exactly the edit a sibling module grades -
            # raises `KeyError` here, and a raise from this position unwinds
            # out of the sweep entirely. Reduced to a type name, which
            # `_anchor_or_skip` treats as fatal, and the self-check flags stay
            # None so the consuming test reds on those first.
            try:
                restore = _install_displaced_int_decoder(delta)
                changed, confined = _self_check_the_rebind()
            except (Exception, SystemExit) as exc:
                failures.append(type(exc).__name__)
        for path in paths:
            # BROAD BY DESIGN: a narrower catch lets an unexpected type escape
            # carrying the save bytes, which is the leak this containment
            # closes. SystemExit for the reason `_read_tagged_save` records.
            # THE WHOLE BODY IS INSIDE IT, `path` included.
            try:
                read, failure = _read_tagged_save(path)
                if failure is not None:
                    failures.append(failure)
                if read is None:
                    continue
                seen_a_save = True
                _anchor_one_save(_extents_of(*read), into)
            except (Exception, SystemExit) as exc:
                failures.append(type(exc).__name__)
                continue
    finally:
        if restore is not None:
            restore()
    # A SKIP ONLY WHEN THERE IS GENUINELY NOTHING TO GRADE, never when something
    # failed. Returning None on an empty result alone would turn a library whose
    # every save raised into a silent skip, which is the shape where a green
    # suite and a broken reader are indistinguishable. With a failure recorded
    # the sweep is returned so `_anchor_or_skip` reddens on it.
    if not seen_a_save and not failures:
        return None
    return _AnchorSweep(
        payloads=into.payloads,
        reached=into.reached,
        # INTERSECTED WITH THE SHIPPED TABLE, so no word that is not already
        # written down in tracked source can leave the sweep.
        tags_by_type=MappingProxyType(
            {
                word: count
                for word, count in into.by_type.items()
                if word in objects._FIXED_WIDTH_VALUES  # noqa: SLF001
            }
        ),
        fixed_width_tags=into.graded,
        decoded_values=into.decoded,
        mismatches=into.mismatches,
        int_oracle_holds=_int_oracle_holds(into.tally),
        rebind_changed_the_int_read=changed,
        rebind_left_the_float_read_alone=confined,
        failures=tuple(sorted(set(failures))),
    )


def _anchored(body: bytes, value_at: int, size: int, spec: tuple[int, str]) -> tuple[bool, bool]:
    """Whether one value reads the same in place and in isolation.

    BOTH CALLS GO THROUGH THE SHIPPED MODULE GLOBAL, which is what makes the
    control fire: a rebind displacing the decoder follows both call sites, the
    in-place read lands on neighbouring payload bytes, and the isolated read
    lands in poison.

    Each call carries its own ``try``, and a raise counts as a mismatch. An
    escaping exception would unwind through a frame holding the body, which is
    non-negotiable 12, and a displacement large enough to leave the padded
    buffer is exactly the case that raises.

    Args:
        body: The decompressed body.
        value_at: The value's first byte, as the shipped tag header reported.
        size: The value's declared extent, from the same read.
        spec: The shipped width and struct code for this type word.

    Returns:
        Whether the two readings agree, and whether the in-place read returned
        a value at all. THE SECOND HALF IS NOT DECORATION: the shipped decoder
        returns None on anything it declines, and ``_agrees(None, None)`` is a
        free agreement, so a fault making every read decline would report a
        perfectly clean anchor over a population that decoded nothing.
    """
    try:
        in_place = objects._decode_fixed_width(body, value_at, size, spec)  # noqa: SLF001
    except (Exception, SystemExit):
        return False, False
    isolated_bytes = _POISON + bytes(body[value_at : value_at + size]) + _POISON
    try:
        isolated = objects._decode_fixed_width(isolated_bytes, _PAD, size, spec)  # noqa: SLF001
    except (Exception, SystemExit):
        return False, in_place is not None
    return _agrees(in_place, isolated), in_place is not None


def _oracle_verdicts(
    tallies: Mapping[tuple[int, ...], test_properties._DecodeTally],
    coarseness: Mapping[tuple[int, ...], Mapping[int, int]],
) -> tuple[frozenset[tuple[int, ...]], frozenset[tuple[int, ...]], frozenset[tuple[int, ...]]]:
    """Apply the three VALUE oracles to each permutation's tally.

    TWO OF THE THREE PREDICATES ARE THE SHIPPED ASSERTIONS RE-EXPRESSED, not new
    ones, and they have ONE owner each - :func:`_int_oracle_holds` and
    :func:`_float_oracle_holds` - shared with the displacement derivation. Those
    tallies come from ``test_properties``, so the judgement is that module's own.

    THE THIRD IS THIS MODULE'S OWN AND HAS NO COPY ANYWHERE. CS-469 asked for a
    discriminator the float32 population can actually carry, and
    :func:`_coarse_oracle_holds` is it. It is owned here outright rather than
    restated from a sibling, which is the shape CS-474 asks for.

    Args:
        tallies: One tally per permutation of the value's four stored bytes.
        coarseness: One width-keyed count per permutation, over the derived
            differing-interior float32 population.

    Returns:
        The permutations the int32 oracle still passes, those the float32
        magnitude oracle still passes, and those the mantissa-coarseness oracle
        passes.
    """
    return (
        frozenset(perm for perm, tally in tallies.items() if _int_oracle_holds(tally)),
        frozenset(perm for perm, tally in tallies.items() if _float_oracle_holds(tally)),
        frozenset(perm for perm in coarseness if _coarse_oracle_holds(coarseness, perm)),
    )


def _score_values_under_every_permutation(
    body: bytes,
    tags: list[tuple[str, int, int]],
    tallies: Mapping[tuple[int, ...], test_properties._DecodeTally],
    coarseness: Mapping[tuple[int, ...], Counter[int]],
    census: _CoarsenessCensus,
) -> int:
    """Decode each scored value once per permutation of its own stored bytes.

    THE COARSENESS POPULATION IS ADMITTED ON THE AS-STORED READING ALONE, which
    is what makes the comparison a comparison. Membership turns on the stored
    bytes and on the shipped decoder returning a float for them, neither of
    which depends on the ordering under judgement - so every ordering is scored
    over the SAME values, and a verdict cannot come from one reading having been
    handed a different population than its partner.

    Args:
        body: The decompressed body.
        tags: The payload's tags, from the unrotated shipped walk.
        tallies: One tally per permutation, mutated in place.
        coarseness: One width-keyed counter per permutation, mutated in place.
        census: The coarseness census's own accumulator, mutated in place.

    Returns:
        How many values were scored under the identity permutation.
    """
    specs = objects._FIXED_WIDTH_VALUES  # noqa: SLF001
    scored = 0
    for type_word, value_at, size in tags:
        if type_word not in (_INT_WORD, _FLOAT_WORD):
            continue
        spec = specs[type_word]
        if size != spec[0] or value_at + size > len(body):
            continue
        stored = bytes(body[value_at : value_at + size])
        scored += 1
        in_population = type_word == _FLOAT_WORD and _the_interior_stored_bytes_differ(stored)
        # A guard testing that the shipped decoder returned a float for these
        # bytes stood here and was measured DEAD - the width was already checked
        # one line above, and the shipped float branch returns a value for every
        # four-byte input. It is replaced by the census grading below, which can
        # fire.
        census.admitted += int(in_population)
        for perm in _PERMUTATIONS:
            reordered = bytes(stored[index] for index in perm)
            if in_population:
                scored_bytes = _tally_mantissa_coarseness(reordered, coarseness[perm])
                if perm == _IDENTITY:
                    # GRADED ON WHAT THE TALLY REPORTS HAVING SCORED, not on the
                    # variable this call site meant to pass. A slice displaced at
                    # the call site is invisible to a check sited on the unused
                    # variable, which is why the tally hands its bytes back.
                    census.graded += 1
                    if not _agrees(
                        objects._decode_fixed_width(scored_bytes, 0, size, spec),  # noqa: SLF001
                        objects._decode_fixed_width(body, value_at, size, spec),  # noqa: SLF001
                    ):
                        census.misread += 1
                    if bytes(scored_bytes[index] for index in _MIDDLE_SWAP) == scored_bytes:
                        census.inert += 1
            value = objects._decode_fixed_width(reordered, 0, size, spec)  # noqa: SLF001
            if type_word == _INT_WORD and isinstance(value, int):
                test_properties._tally_int32_byte_order(value, tallies[perm])  # noqa: SLF001
            elif type_word == _FLOAT_WORD and isinstance(value, float):
                test_properties._tally_float32_byte_order(value, tallies[perm])  # noqa: SLF001
    return scored


@lru_cache(maxsize=1)
def _sweep_permutations() -> _PermutationSweep | None:
    """Census both four-byte fields over the whole permutation group. COUNTS ONLY.

    ONE SAVE AT A TIME AND ONE DECOMPRESSION PER SAVE, with every permutation
    walked while that body is alive. The claim that used to stand here - that
    the peak cost is one body rather than the whole library - was true of the
    decompressed bodies and FALSE of the library, because a list of every
    tagged save's raw bytes was built before the first walk. It is true now
    because :func:`_read_tagged_save` hands back one save.

    A SAVE THAT RAISES MID-CENSUS CONTRIBUTES NOTHING, and that is a correctness
    fix rather than tidiness. Folding straight into the shared counter banked
    whatever orderings had already run and dropped the rest - and since the
    identity is walked first, a mid-loop raise biased the ranking toward exactly
    the ordering under test. The per-save counts are held aside and folded in
    only when the whole group completed.

    Contained exactly as :func:`_sweep_anchor` is.

    Returns:
        The sweep, or None when no save library is reachable.
    """
    paths = test_properties._library_save_paths()  # noqa: SLF001
    if not paths:
        return None

    reach: Counter[tuple[int, ...]] = Counter()
    tallies = {
        perm: test_properties._DecodeTally(Counter(), set(), set())  # noqa: SLF001
        for perm in _PERMUTATIONS
    }
    coarseness: dict[tuple[int, ...], Counter[int]] = {perm: Counter() for perm in _PERMUTATIONS}
    census = _CoarsenessCensus()
    payloads = scored = big = 0
    restored = True
    seen_a_save = False
    failures: list[str] = []
    for path in paths:
        # BROAD BY DESIGN, for the reason `_sweep_anchor` records, and the whole
        # body including `path` is inside it.
        try:
            read, failure = _read_tagged_save(path)
            if failure is not None:
                failures.append(failure)
            if read is None:
                continue
            seen_a_save = True
            extents = _extents_of(*read)
            mutable = bytearray(extents.body)
            local: Counter[tuple[int, ...]] = Counter()
            try:
                for perm in _PERMUTATIONS:
                    local[perm] = sum(
                        1
                        for start, end in extents.spans
                        if _reaches_with_a_permuted_size(mutable, start, end, perm)
                    )
            finally:
                # A ``finally`` because the ``except`` below jumps straight past
                # any following statement, so the flag never saw the one case it
                # exists to catch.
                restored = restored and bytes(mutable) == extents.body
            reach.update(local)
            payloads += len(extents.spans)
            for start, end in extents.spans:
                tags = _walk_with_the_shipped_reader(extents.body, start, end)
                if tags is None:
                    continue
                big += sum(1 for _w, _v, size in tags if size >= _HIGH_SIZE_FLOOR)
                scored += _score_values_under_every_permutation(
                    extents.body, tags, tallies, coarseness, census
                )
        except (Exception, SystemExit) as exc:
            failures.append(type(exc).__name__)
            continue
    # A skip only when there is genuinely nothing to grade - see the same guard
    # in :func:`_sweep_anchor` for why a failure must not become a skip.
    if not seen_a_save and not failures:
        return None
    frozen_coarseness = MappingProxyType(
        {perm: MappingProxyType(dict(counts)) for perm, counts in coarseness.items()}
    )
    ints, floats, coarse = _oracle_verdicts(tallies, frozen_coarseness)
    return _PermutationSweep(
        reach=MappingProxyType(dict(reach)),
        int_oracle_holds=ints,
        float_oracle_holds=floats,
        coarse_oracle_holds=coarse,
        coarseness=frozen_coarseness,
        coarseness_population=census.admitted,
        coarseness_graded=census.graded,
        coarseness_misread=census.misread,
        coarseness_inert_admissions=census.inert,
        payloads=payloads,
        scored_values=scored,
        tags_above_the_size_floor=big,
        bodies_restored=restored,
        failures=tuple(sorted(set(failures))),
    )


def _anchor_or_skip(delta: int | None) -> _AnchorSweep:
    """Fetch an anchor sweep, skipping when this machine has no library.

    Args:
        delta: The displacement, or None for the shipped tree.

    Returns:
        The sweep.
    """
    sweep = _sweep_anchor(delta)
    if sweep is None:
        pytest.skip("no save library on this machine - the extent anchor is not gradeable here")
    assert sweep.failures == (), f"failures walking real bodies: {sweep.failures}"
    return sweep


def _permutations_or_skip() -> _PermutationSweep:
    """Fetch the permutation census, skipping when this machine has no library.

    Returns:
        The sweep.
    """
    sweep = _sweep_permutations()
    if sweep is None:
        pytest.skip("no save library on this machine - the byte-order census is not gradeable here")
    assert sweep.failures == (), f"failures walking real bodies: {sweep.failures}"
    return sweep


# ---------------------------------------------------------------------------
# The extent anchor
# ---------------------------------------------------------------------------


def test_no_fixed_width_value_depends_on_a_byte_outside_its_declared_extent() -> None:
    """CS-421 clause 3 - the anchoring the two-bit value oracles do not have.

    WHAT IS COMPARED. For each fixed-width tag the shipped decoder reads the
    value where the shipped tag header put it, and then reads an ISOLATED copy
    of exactly the bytes the tag declared, surrounded by poison. Agreement on
    every tag says the decoded value is read FROM its own declared extent and
    from nothing beside it. That is the property the stored-high-byte oracle
    cannot check at all: reducing a value to two bits leaves it green under a
    displacement that never touches the int32.

    STATED LIMIT ONE - IT ESTABLISHES WHICH BYTES ARE READ, NOT WHAT FUNCTION
    THEY GO THROUGH, and the limit is at that width rather than at the narrower
    one this paragraph first claimed. Both readings hand the same declared bytes
    to the same decoder, so ANY pure function of the declared extent agrees with
    itself and this test stays GREEN. Two points in that class were forced: a
    decoder returning a constant, and a decoder that zeroes one stored byte
    before unpacking - the second is data-dependent, is no kind of constant, and
    left every test in this module green while thousands of values decoded
    wrong. Fabrication is CS-455's; this test does not cover it, does not narrow
    it, and must not be cited as if it did.

    STATED LIMIT TWO - THE LOCATOR IS SHARED, so this anchors against the
    DECLARATION and not against the truth. Both readings take ``value_at`` and
    ``size`` from ONE ``objects._read_tag_header`` call, and the isolated copy
    is sliced at that same offset, so a fault in where the tag header BELIEVES
    the value starts moves both readings together and this control cannot see
    it. NOTHING IN THIS SUITE IS NAMED AS BOUNDING THAT. A sentence here used to
    say terminator reach did; it was measured false, because a locator fault
    reporting a moved value start with a compensating size leaves
    ``value_at + size`` unchanged, so the walk stays synchronised and the reach
    is untouched while the headers are wrong.

    STATED LIMIT THREE - THE POPULATION IS THE FIXED-WIDTH TYPES. BoolProperty
    carries its value in the tag and the string and reference decoders are read
    by different functions, so none of them is anchored by this test and its
    green says nothing about any of them.

    THE FIRST THREE ASSERTIONS ARE LIVENESS, and the middle one is the one that
    was missing. Tags are counted by TYPE WORD before any decode, so a fault
    making every read return None leaves that count untouched while
    ``_agrees(None, None)`` hands back a free agreement on every tag. Reach is
    asserted as EQUALITY with the population rather than as a floor, because a
    floor was measured surviving a fault that silently discarded most of the
    library - the same reasoning ``test_decode_oracles`` gives for its own.
    """
    sweep = _anchor_or_skip(None)

    assert sweep.payloads > 0, (
        "no payload was walked anywhere in this library, so the anchor graded "
        "nothing and its zero below is the vacuous kind"
    )
    assert sweep.reached == sweep.payloads, (
        f"{sweep.reached} of {sweep.payloads} payloads reached a terminator. A "
        "floor here would pass while most of the library went silently ungraded, "
        "so this is equality: every payload of a pair this grammar reads is "
        "walked, or the population below is a self-selecting remnant"
    )
    assert sweep.decoded_values > 0, (
        f"none of {sweep.fixed_width_tags} fixed-width tags yielded a value. The "
        "tag count is taken from the TYPE WORD before any decode, so a decoder "
        "declining everything leaves it untouched while every comparison below "
        "agrees None with None"
    )
    assert sweep.mismatches == 0, (
        f"{sweep.mismatches} of {sweep.fixed_width_tags} fixed-width values read "
        "differently in place and in isolation. A value that changes when the "
        "bytes outside its declared extent are replaced is being read from "
        "outside that extent, whatever byte order it is read in"
    )


def test_the_extent_anchor_control_catches_a_displaced_fixed_width_read() -> None:
    """THE CONTROL'S POWER, forced rather than asserted about.

    A control that agreed on everything would report zero mismatches on a
    displaced tree exactly as it does on the shipped one, and would read the
    same in the file. So the shipped decoder is rebound - in a ``try/finally``,
    with no production file edited, because ``_decode_fixed_width`` is a module
    global - to read an IntProperty four bytes past where the tag header put it.

    WHY FOUR AND NOT ONE IS NOT ARGUED HERE - it is DERIVED by
    ``test_the_displacement_the_value_oracle_tolerates_is_the_one_the_anchor_catches``,
    which is the test to read next. The ground this paragraph used to give was
    that the value oracle survives at -2, -1, +2, +3 and +4; that was measured
    false, and the correct fact is stronger: across a displacement of up to one
    whole value width either way, +4 is the ONLY one the oracle tolerates. At +4
    the in-place read leaves the int32 entirely and lands on the following tag's
    name-length prefix.

    THE SELF-CHECK RUNS FIRST AND IS ASSERTED. A rebind that silently failed to
    install would leave this test measuring the shipped tree and reporting the
    mutant's verdict, which is the exact false-green this whole module exists to
    close one layer up. Both halves are checked on a hand-authored pattern that
    no save contributed: the int32 read moved, and a non-int32 spec did not.

    SAME STATED LIMITS AS THE TEST ABOVE. This forces a DISPLACEMENT, so it
    demonstrates the control fires on a read taken from the wrong PLACE. It
    demonstrates nothing about a decoder reading the right place through the
    wrong function.
    """
    sweep = _anchor_or_skip(_ANCHOR_DISPLACEMENT)

    assert sweep.rebind_changed_the_int_read is True, (
        "the displaced decoder returned what the shipped one returns on the "
        "hand-authored pattern, so the rebind did not take and everything below "
        "would be a measurement of the shipped tree wearing a mutant's label"
    )
    assert sweep.rebind_left_the_float_read_alone is True, (
        "the displacement moved a spec other than the int32 one, so a mismatch "
        "below could come from a type this control did not claim to displace"
    )
    assert sweep.fixed_width_tags > 0, (
        "the displaced sweep graded no fixed-width tag, so its mismatch count is "
        "a claim about an empty population"
    )
    assert sweep.decoded_values > 0, (
        "the displaced sweep decoded no value at all, so its disagreements would "
        "be comparisons between two declined reads rather than between two values"
    )
    assert sweep.mismatches > 0, (
        f"reading every int32 {_ANCHOR_DISPLACEMENT} bytes past its declared start "
        f"produced {sweep.mismatches} disagreements over {sweep.fixed_width_tags} "
        "fixed-width tags. The anchor cannot see a value read from outside its own "
        "extent, so the zero it reports on the shipped tree means nothing"
    )


def test_the_displacement_the_value_oracle_tolerates_is_the_one_the_anchor_catches() -> None:
    """WHY +4, DERIVED - and it is the sentence this module got wrong first.

    The refuted oracle in ``test_properties`` is a CONJUNCTION: a non-empty
    population, a MAJORITY carrying the small-magnitude signature as read, and a
    MINORITY carrying it under the swapped reading. An earlier revision of this
    module justified its displacement by saying that oracle survives at -2, -1,
    +2, +3 and +4. What survives all five is the as-read MAJORITY - the first
    conjunct alone - and widening that into the oracle's verdict is how a false
    sentence got written down twice in one file.

    SO THE RELATION IS ASSERTED INSTEAD OF NARRATED. Over every non-zero
    displacement of up to one whole value width either way, this derives which
    ones the old oracle still passes, and requires the module's chosen
    displacement to be exactly that set. If it is ever not the unique member,
    the choice stops being the interesting one and this test says so rather than
    leaving a paragraph asserting it.

    WHAT THE PAIRING BUYS is the module's whole reason to exist, and it is
    asserted here in one place: at this displacement the OLD oracle is green and
    the anchor is RED. A control at a displacement the old oracle also catches
    would demonstrate nothing that was not already covered.

    ONE SWEEP PER DISPLACEMENT, each its own cache entry, because a memoised
    sweep replayed across mutants reports the first mutant's verdict for all of
    them - an error this package has already paid for once.
    """
    shipped = _anchor_or_skip(None)
    assert shipped.int_oracle_holds, (
        "the refuted value oracle does not pass on the undisplaced tree, so "
        "everything below compares displacements against a baseline that is "
        "already red and the comparison means nothing"
    )

    tolerated = []
    for delta in _CANDIDATE_DISPLACEMENTS:
        sweep = _anchor_or_skip(delta)
        assert sweep.rebind_changed_the_int_read is True, (
            f"the rebind at displacement {delta} did not take, so its verdict is "
            "a measurement of the shipped tree wearing a mutant's label"
        )
        if sweep.int_oracle_holds:
            tolerated.append(delta)

    assert tolerated == [_ANCHOR_DISPLACEMENT], (
        f"the refuted value oracle tolerates displacements {tolerated} out of "
        f"{list(_CANDIDATE_DISPLACEMENTS)}, and this module controls at "
        f"{_ANCHOR_DISPLACEMENT}. The control is worth having exactly where the "
        "old oracle is blind, so if that is no longer the one blind spot, the "
        "displacement is chosen against a fact that has moved"
    )

    displaced = _anchor_or_skip(_ANCHOR_DISPLACEMENT)
    assert displaced.int_oracle_holds, (
        "the old oracle catches this displacement after all, so the anchor below "
        "is not adding a detection - it is duplicating one"
    )
    assert displaced.mismatches > 0, (
        "the anchor is green at the one displacement the old oracle tolerates, "
        "so nothing in this suite catches it"
    )


# ---------------------------------------------------------------------------
# The size-field census
# ---------------------------------------------------------------------------


def test_the_declared_size_field_census_narrows_the_byte_orders_to_two() -> None:
    """The tag's DECLARED SIZE, censused - AND IT NARROWS TO TWO, NOT TO ONE.

    Each payload is walked once per ordering of the size field's four stored
    bytes, graded by how many payloads still reach their terminator. A size read
    in the wrong order desynchronises the walk, so a wrong ordering costs reach.

    THE CENSUS DOES NOT SETTLE THE ORDER, and the earlier name of this test -
    which said the field is read in exactly one of its twenty-four byte
    orders - claimed that it did. What the reach ranking DECISIVELY rejects is
    the twenty-two orderings that disturb the low output positions. The two that
    remain are the as-stored one and the one swapping its two HIGH bytes, and
    those are derived here from the permutation group rather than read off a
    ranking: below :data:`_HIGH_SIZE_FLOOR` both high bytes of a little-endian
    size are zero, so the two orderings read every such size IDENTICALLY. They
    are separated only by the tags declaring a size at or above that floor, and
    the census reports how many of those it found in the same run that grades
    them. Several of the rejected orderings still leave a MAJORITY of payloads
    reaching, which is why the argument is made on a ranking rather than on a
    majority.

    THE SEPARATION IS GATED ON ITS OWN POPULATION, and without that gate this
    test would be red on a correct grammar. A library holding no tag at or above
    the floor makes the two orderings genuinely indistinguishable, and asserting
    a strict inequality would be asserting something the corpus cannot supply -
    the CS-432 shape, arriving in the argmax that the earlier version of this
    docstring invoked CS-432 to justify. The gate is a derived population, not a
    tuned threshold, which is the same shape as the value oracles' own
    non-empty-population guard.

    THE ASYMMETRY THIS RESOLVES. The value censuses in this module decline to
    settle their question on a small discriminating subpopulation. This one
    rests on a subpopulation of the same order, and an earlier revision settled
    it anyway. Both are now stated as narrowings to two.

    THE HONEST LIMIT, AND THIS TEST DOES NOT CROSS IT. What is censused here is
    the DECLARED SIZE FIELD, read by ``objects._read_tag_header``. That is a
    DIFFERENT FIELD READ BY A DIFFERENT READER than the property value, which
    ``objects._decode_fixed_width`` reads. So this licenses NO statement about
    the byte order of a property VALUE. Getting from one to the other needs the
    premise that the format uses a single byte order for every int32 field it
    stores, and that premise is UNMEASURED here.

    THE RESTORATION IS ASSERTED BESIDE THE RANKING. The permutations are applied
    to a writable copy in place and put back; a copy that came back changed
    would mean later orderings were graded against a body the earlier ones had
    corrupted, and the ranking would be measuring damage.
    """
    sweep = _permutations_or_skip()

    assert sweep.bodies_restored, (
        "a permuted size field was not put back, so every ordering after the "
        "first was graded against a corrupted body rather than against a "
        "reordering of the save's own bytes"
    )
    assert len(sweep.reach) == len(_PERMUTATIONS), (
        f"the census scored {len(sweep.reach)} orderings and there are "
        f"{len(_PERMUTATIONS)} of four bytes, so it did not walk the whole group"
    )
    assert len(_SIZE_ORDERINGS_ALIKE_BELOW_THE_FLOOR) == _LOW_SIZE_POSITIONS, (
        f"the orderings indistinguishable on a small declared size derive to "
        f"{sorted(_SIZE_ORDERINGS_ALIKE_BELOW_THE_FLOOR)}, which is not the pair "
        "this test is written around. The derivation has changed meaning"
    )

    identity = sweep.reach[_IDENTITY]
    assert identity > 0, (
        "the as-stored ordering reached no terminator at all, so the ranking "
        "below is over an empty measurement"
    )
    assert identity == sweep.payloads, (
        f"the as-stored ordering reached {identity} of {sweep.payloads} payloads. "
        "It is the reading the module ships, so anything short of all of them "
        "means the census is grading a grammar that is already failing"
    )

    # THE DECISIVE HALF: every ordering that disturbs the low output positions.
    rejected = {
        perm: hits
        for perm, hits in sweep.reach.items()
        if perm not in _SIZE_ORDERINGS_ALIKE_BELOW_THE_FLOOR
    }
    assert rejected, "the derivation left no ordering to reject, so this half is vacuous"
    assert max(rejected.values()) < identity, (
        f"an ordering disturbing the low bytes of the declared size reached "
        f"{max(rejected.values())} payloads against the as-stored ordering's "
        f"{identity}. Those orderings change the size on all but the smallest "
        "tags, so a walk that survives one is not reading the field it believes"
    )

    # THE FRAGILE HALF: the one ordering that differs only in the high bytes.
    (twin,) = (perm for perm in _SIZE_ORDERINGS_ALIKE_BELOW_THE_FLOOR if perm != _IDENTITY)
    if sweep.tags_above_the_size_floor == 0:
        pytest.skip(
            "no tag in this library declares a size needing its high bytes, so "
            "the two surviving orderings are indistinguishable here and the "
            "narrowing stops at two without a separation to grade"
        )
    assert sweep.reach[twin] < identity, (
        f"the ordering swapping the two high bytes of the declared size reached "
        f"{sweep.reach[twin]} payloads against {identity}, with "
        f"{sweep.tags_above_the_size_floor} tags declaring a size big enough to "
        "tell them apart. With a separating population present the two must "
        "separate, or the high bytes are not being read where this walk thinks"
    )


# ---------------------------------------------------------------------------
# The mantissa-coarseness oracle - CS-469
#
# WHAT THIS ORACLE DOES NOT CLOSE, written here rather than left in a session
# report, because a limit that lives outside the artifact is a limit the next
# reader will not find.
#
#   IT SCORES FLOAT32 VALUES ONLY, and the narrowing to one candidate is JOINT.
#   Measured over the whole permutation group: the float32 oracles between them
#   still leave more than one ordering standing, and so do the int32 oracle's
#   survivors intersected with this one. Only all three together reach one. So
#   this does not settle any single type word's byte order on that type's own
#   evidence, which is why VALUE_BYTE_ORDER_STATUS still records what it does.
#
#   IT COMPARES AN ORDERING ONLY WITH ITS MIDDLE-SWAPPED PARTNER. It is not a
#   ranking over the group and it says nothing about two orderings that are not
#   related by that swap. It removes the candidate the other two leave; it does
#   not independently rule out the twenty-two they already rule out.
#
#   THE SHARED LOCATOR IS STILL OUTSIDE IT. Coarseness is a property of the
#   bytes the tag header pointed at, so it speaks to WHICH ORDER those bytes are
#   read in and not to the header having pointed at the right ones. That is the
#   extent anchor's question and it is a different one.
#
#   ITS OWN OFFSET IS NOT OUTSIDE IT, AND AN EARLIER REVISION OF THIS COMMENT
#   SAID IT WAS. The census slices the body privately, and that slice is a
#   DIFFERENT hole from the shared locator: displacing it alone by -2 left every
#   test here green while the census scored two framing bytes, and it scored
#   them cleaner than real values because the byte before a float value is zero
#   on every float tag in this library. It is now graded by
#   test_the_coarseness_census_reads_the_value_the_shipped_decoder_reads, by
#   equality against the shipped in-place read rather than by collapse under
#   displacement - which would not have worked, the fault being GREENER.
#
#   THE SKIP SET WIDENED. Library-free, this module skipped five of eight tests
#   before this work and skips more now, because the library-backed additions
#   join the legitimate-skip population that a body gutted to a bare
#   pytest.skip() hides among. That is CS-473's class rather than a new defect,
#   and it is recorded here rather than closed here.
#
#   IT SKIPS WHERE THERE IS NO LIBRARY. Everything below that touches a save
#   skips on a machine with no game, so the shipped singleton is ungraded on
#   CI - CS-426's recorded gap, unchanged by this work. The boundary
#   derivation, the predicate control and the population control are
#   library-free and do run there.
#
# HOW THE CONTROLS BELOW WERE GRADED, and the limit of that grading. Each
# mutant was a real source edit run in a FRESHLY LAUNCHED interpreter, one
# process per mutant, with a self-check executed in that same process before
# pytest was invoked - because the constants here are module-level and the
# sweep is lru_cache-memoised, so a mutant applied in-process would be graded
# against a stale derivation or a replayed verdict.
#
# GRADED LIVE AND DETECTED: the survivor derivation with the coarseness term
# removed; the predicate returning a verdict without comparing; the predicate
# with its strictness dropped; the predicate made WIDTH-BLIND by comparing
# totals; the admission helper stopping deriving its population; the tie
# boundary moved one bit either way; the census's slice displaced by -2 with the
# magnitude tallies untouched; the population filter neutered at the census's
# own call site with the helper left honest; a BIG-ENDIAN assembly inside the
# tally; and the four-line bypass below.
#
# THE BYPASSES ARE WHY THE STRUCTURAL CONTROL EXISTS, AND WHY IT IS THREE RULES.
# Two revisions graded the census by VALUE - first on the local the call site
# passed, then on the bytes the tally reported back. Both fell the same way:
# take a SECOND, displaced slice, hand it to the tally, rebind the graded local
# to the honest one. Four lines, whole suite green, census scoring two framing
# bytes - and scoring them CLEANER than real values, because the byte before a
# float value is zero on every float tag in this library. A value grade and a
# value tally are two statements, and a mutation can always separate two
# statements.
#
# COUNTING CUTS THEN FELL TOO, and this comment claimed it could not. Six lines,
# ONE cut, nothing unaccounted: call the allowlisted decoder at a displaced
# offset and pack its result back to bytes. The freedom had moved from which
# local the grade reads to which OFFSET the reader is called at - so the offset
# is constrained as well.
#
# AND CONSTRAINING THE OFFSET EXPRESSION FELL TO A REBIND, which this author
# built before shipping the rule rather than after: save value_at, displace it,
# read, restore. Every offset expression stays the bare name and the AST walk
# sees nothing. The binding count closes it.
#
# THEN THE BINDING COUNT FELL TO A SCOPE SHADOW, because a PARAMETER is an
# ast.arg and not an ast.Name with a Store context. A five-line nested def -
# or a lambda, or a comprehension - taking the offset name as its own parameter
# scored one cut, every offset a bare name and one binding, with the census
# fully displaced and the whole suite green. Parameters are counted now too.
#
# EACH OF THE THREE RULES, AND EACH WIDENING OF THE THIRD, EXISTS BECAUSE WHAT
# CAME BEFORE IT WAS WORKED AROUND AND MEASURED TO BE. Every time the closure
# was believed final it was not, so the standing claim here is the enumerated
# one and not an absolute.
#
# ONE MUTANT IS EQUIVALENT AND IS NOT A GAP: widening the coarseness mask by one
# bit, to take in the exponent's lowest bit. Proven rather than judged. The
# scored quantity is the index of the lowest set bit, capped at the mantissa
# width when the masked value is zero, and it therefore depends only on the low
# mantissa-width-plus-one bits of the pattern; sweeping every one of those
# exhaustively gives an identical result under both masks. A wider mask cannot
# change any width this module scores.
#
# THAT WAS A SNAPSHOT OF FIVE RUNS AND IS NOT A STANDING CONTROL - nothing in
# the suite re-grades those mutants, and a later edit can reopen any of them.
#
# THE TWO CONTROLS ARE COMPLEMENTARY AND NEITHER IS SPARE, measured rather than
# assumed. Neutering the population filter is AST-CLEAN and only the value grade
# reds it; a second cut, an unallowlisted route and a displaced offset are all
# value-clean and only the structural control reds them.
#
# TWO SHAPES ARE KNOWN NOT TO BE CAUGHT AND ARE NOT THIS SECTION'S TO CLOSE.
# Gutting any control here to a bare return or to a lone pytest.skip() leaves it
# green; those are the two shapes _hollow_tests records as its own blind spots
# and they are CS-473's. And displacing the tag's OWN reported offset moves the
# census and the shipped decode it is graded against together - the SHARED
# LOCATOR, which is the extent anchor's question and is answered nowhere here.
# ---------------------------------------------------------------------------


def _mantissa_bits_by_stored_byte() -> Counter[int]:
    """Which stored byte carries each mantissa bit, measured by toggling it.

    A SECOND AND INDEPENDENT DERIVATION of the boundary the constants compute
    from the mantissa width and the pattern width. This one sets one pattern bit
    at a time and reads off which stored byte it landed in, so the two routes
    can only agree by describing the same layout.

    Returns:
        Stored byte index mapped to how many mantissa bits it carries.
    """
    where: Counter[int] = Counter()
    for bit in range(_MANTISSA_BITS):
        stored = (1 << bit).to_bytes(_FLOAT_SPEC[0], "little")
        where[next(index for index, byte in enumerate(stored) if byte)] += 1
    return where


def test_the_coarseness_tie_boundary_is_the_mantissa_that_fits_in_the_low_stored_byte() -> None:
    """THE PREDICTION, MADE FROM THE LAYOUT AND BEFORE ANY SAVE IS READ.

    The mantissa's low bits ARE stored byte zero, and the middle swap does not
    move stored byte zero. So a coarseness confined to those bits is identical
    under an ordering and under its swapped partner, and the oracle below cannot
    discriminate anything there however the corpus falls. THAT IS WHAT MAKES THE
    RESULT NOT A FITTED ONE: the parameter has a region where it is predicted to
    be useless, the corpus is asked whether it is, and the answer is checked
    rather than assumed.

    THE BOUNDARY IS DERIVED TWICE, BY TWO ROUTES, and asserted equal. The
    constants compute it from the mantissa width and the pattern width; this
    test recomputes it by setting one mantissa bit at a time and reading off
    which stored byte it lands in. Neither route is a literal.

    IT READS NO SAVE, so this half runs on CI, where CS-426 records that the
    library-backed evidence is unavailable.
    """
    where = _mantissa_bits_by_stored_byte()

    assert sum(where.values()) == _MANTISSA_BITS, (
        f"the toggle walk placed {sum(where.values())} bits and the mantissa is "
        f"{_MANTISSA_BITS} wide, so one of the two derivations is not describing "
        "this format"
    )
    assert where[_IDENTITY[0]] == _MANTISSA_BITS_IN_STORED_BYTE_ZERO, (
        f"stored byte zero carries {where[_IDENTITY[0]]} mantissa bits and the "
        f"constants say {_MANTISSA_BITS_IN_STORED_BYTE_ZERO}. The tie region below "
        "is that boundary, so the two derivations disagreeing means the region the "
        "oracle claims cannot discriminate is not the region that cannot"
    )
    assert _MIDDLE_SWAP != _IDENTITY, (
        "the middle swap equals the identity, so it moves nothing and the whole "
        "derivation is comparing an ordering with itself"
    )
    assert _MIDDLE_SWAP[0] == _IDENTITY[0], (
        f"the middle swap sends stored byte {_MIDDLE_SWAP[0]} to the low output "
        "position rather than leaving stored byte zero there. The tie prediction "
        "rests on it leaving that byte alone, so it does not follow"
    )
    assert _TIED_WIDTHS, (
        "no width falls inside the low stored byte, so the oracle has no region "
        "it is predicted to be useless in and the tie prediction grades nothing"
    )
    assert _DISCRIMINATING_WIDTHS, (
        "no width falls above the low stored byte, so the oracle has no region "
        "it can discriminate in and its verdict is empty rather than green"
    )


def test_the_coarseness_predicate_cannot_pass_both_readings_of_a_swapped_pair() -> None:
    """THE PREDICATE'S OWN CONTROL, on hand-authored counts and no save at all.

    Three shapes, and each kills a different way of writing the predicate
    wrong. Domination with one strict win must pass exactly one member of the
    pair - a predicate dropping the strictness would pass both. A pair tied at
    every width must pass NEITHER - a predicate testing only ``>=`` would pass
    both and rule out nothing. A pair where each side wins somewhere must pass
    neither - a predicate reading one width and calling it the verdict, or one
    SUMMING the widths, would pick a winner from a corpus that has not chosen
    one.

    THE MIXED FIXTURE'S TOTALS ARE DELIBERATELY UNEQUAL, and an earlier
    revision's were not. With totals of three against three a width-blind
    predicate returning ``sum(mine) > sum(theirs)`` answered False for both
    members and slipped through this test unchanged - measured, one process per
    mutant. The totals below differ, so that mutant now elects a winner here and
    is caught.

    IT READS NO SAVE, so this runs on CI alongside the boundary derivation.
    """
    assert _DISCRIMINATING_WIDTHS, "no discriminating width, so these cases grade nothing"
    first, last = _DISCRIMINATING_WIDTHS[0], _DISCRIMINATING_WIDTHS[-1]
    assert first != last, "one discriminating width only, so the mixed case below is unbuildable"

    dominant: Mapping[tuple[int, ...], Mapping[int, int]] = {
        _IDENTITY: {first: 2},
        _MIDDLE_SWAP: {first: 1},
    }
    assert _coarse_oracle_holds(dominant, _IDENTITY), (
        "an ordering beating its partner at a width and losing nowhere does not "
        "pass, so the predicate rules out the reading the evidence favours"
    )
    assert not _coarse_oracle_holds(dominant, _MIDDLE_SWAP), (
        "both members of a swapped pair pass, so the predicate removes no "
        "candidate and cannot narrow the survivor set at all"
    )

    tied: Mapping[tuple[int, ...], Mapping[int, int]] = {
        _IDENTITY: {first: 2},
        _MIDDLE_SWAP: {first: 2},
    }
    assert not any(_coarse_oracle_holds(tied, perm) for perm in tied), (
        "a pair tied at every width passes the predicate, so a corpus that "
        "separates nothing would still be reported as separating something"
    )

    mixed: Mapping[tuple[int, ...], Mapping[int, int]] = {
        _IDENTITY: {first: 3, last: 1},
        _MIDDLE_SWAP: {first: 1, last: 2},
    }
    assert not any(_coarse_oracle_holds(mixed, perm) for perm in mixed), (
        "a pair where each side wins at some width passes the predicate, so the "
        "verdict is being taken from one width rather than from all of them - "
        "which is the fitted-threshold shape this oracle exists to avoid"
    )


def test_the_coarseness_census_reads_the_value_the_shipped_decoder_reads() -> None:
    """THE CENSUS'S OWN SLICE AND ITS OWN POPULATION, graded at the call site.

    WHAT WAS UNGRADED. The census slices the body privately and admits values
    privately, and neither the tally, nor the predicate control, nor the
    survivor derivation could see either. Measured: displacing the census's
    slice alone by -2 left every test in this module green while it scored two
    framing bytes and two value bytes, and neutering the admission filter at its
    call site - leaving the helper honest - silently widened the population to
    every float32 in the library with the module still reporting green.

    THE DISPLACEMENT MADE THE ORACLE GREENER, NOT REDDER, which is why the
    collapse-under-displacement shape the extent anchor uses does not work here.
    The byte before a float tag's value is zero on every float tag in this
    library, so a displaced read manufactures low-mantissa zeros and reports a
    cleaner separation than the real values do. AN EQUALITY CONTROL IS WHAT
    CATCHES IT: the bytes the tally consumed must decode to what the shipped
    decoder reads in place at the tag's own reported offset.

    ``graded`` IS ASSERTED EQUAL TO THE POPULATION AND NOT MERELY NON-ZERO,
    because a check that quietly stops running reports the same zero as a check
    that passes.

    WHAT THIS STILL DOES NOT COVER, and it is a different hole from the one
    above. The tag header's own offset is SHARED by the census and by the
    in-place read compared against it, so a header pointing both at the wrong
    place moves them together and is invisible here. That is the extent
    anchor's question and it is not answered by anything in this section.
    """
    sweep = _permutations_or_skip()

    assert sweep.coarseness_population > 0, (
        "the coarseness census admitted nothing, so every count below is zero "
        "for want of a population rather than for want of a fault"
    )
    assert sweep.coarseness_graded == sweep.coarseness_population, (
        f"{sweep.coarseness_graded} of {sweep.coarseness_population} admitted "
        "values were graded. The two counts diverging means the check below ran "
        "on some other number of values than the census scored, so a zero from it "
        "is not a statement about the census"
    )
    assert sweep.coarseness_misread == 0, (
        f"{sweep.coarseness_misread} of {sweep.coarseness_population} admitted "
        "values were tallied from bytes that do not decode to what the shipped "
        "decoder reads in place at the tag's own offset. The census is scoring "
        "something other than the value, and a displaced read of this format "
        "scores CLEANER than a correct one, so this cannot be left to a "
        "collapse-under-displacement control"
    )
    assert sweep.coarseness_inert_admissions == 0, (
        f"{sweep.coarseness_inert_admissions} of {sweep.coarseness_population} "
        "admitted values are ones the middle swap does not change. Those read "
        "the same under both orderings of the pair the singleton rests on, so "
        "they add the same number to both sides and widen the population without "
        "widening the evidence - which is the clause CS-469 asks for by name"
    )


def test_the_scored_population_is_exactly_what_the_middle_swap_changes() -> None:
    """THE POPULATION IS DERIVED FROM THE SWAP, and this is what says so.

    A value belongs in the coarseness census when and only when the middle swap
    changes its bytes. That is not a threshold and not a filter chosen to make a
    margin look better - it is the definition of the values on which the two
    readings under comparison differ at all. This asserts the two descriptions
    coincide on hand-authored patterns rather than trusting that they do.

    WITHOUT THIS THE DERIVATION IS UNGRADED. Admitting the whole float32
    population instead adds the same count to both sides of every comparison, so
    the verdict survives and no library-backed test notices - measured, one
    process per mutant. The clause CS-469 asks for is about the population being
    derived, so the population needs a control of its own.

    IT READS NO SAVE, and every pattern below is hand-authored.
    """
    assert _INTERIOR_POSITIONS, "no interior position, so the swap moves nothing"

    patterns = (
        bytes(range(_FOUR_BYTES)),
        bytes([0] * _FOUR_BYTES),
        bytes([0xFF] * _FOUR_BYTES),
        bytes([1, 2, 2, 3]),
        bytes([9, 2, 7, 9]),
        bytes([0, 0, 1, 0]),
    )
    for stored in patterns:
        reordered = bytes(stored[index] for index in _MIDDLE_SWAP)
        assert _the_interior_stored_bytes_differ(stored) == (reordered != stored), (
            f"the population test and the middle swap disagree on {list(stored)}: "
            f"admitted={_the_interior_stored_bytes_differ(stored)} while the swap "
            f"{'changes' if reordered != stored else 'leaves'} the bytes. For the "
            "identity and the middle swap - the pair the shipped singleton rests "
            "on - a value the swap does not change reads the same under both, so "
            "admitting it adds the same number to both sides; excluding one the "
            "swap DOES change discards evidence"
        )


def test_the_mantissa_bits_inside_the_low_stored_byte_separate_no_ordering_from_its_swap() -> None:
    """THE CORPUS CONFIRMING THE PREDICTION, over the WHOLE permutation group.

    Every ordering and its swapped partner agree on which stored byte reaches
    output position zero, so at every width inside that byte their counts must
    be EXACTLY equal - not close, equal.

    THIS TEST CANNOT FAIL ON ANY CORPUS, AND SAYING SO IS THE POINT. Below the
    boundary the count depends only on ``stored[perm[0]]``, and the middle swap
    fixes output position zero, so equality holds by construction whatever the
    bytes are - it was measured true on uniform random noise and on garbage
    windows alike. AN EARLIER REPORT OF THIS WORK CALLED IT "the non-circularity
    argument and the strongest thing here" AND THAT WAS WRONG. A test that no
    data can red is not evidence about data.

    WHAT IT DOES GRADE IS THE BOUNDARY, and only jointly with a neighbour.
    Measured: moving the boundary one bit UP reds this test, and one bit DOWN
    reds the strict-width test instead, so the pair of them pins it from both
    sides and neither does it alone.

    IT DOES NOT GRADE THE ASSEMBLY, AND AN EARLIER REVISION CLAIMED IT DID. A
    big-endian assembly inside the tally leaves this test PASSING - it reds
    three others - because :func:`_with_the_middle_swapped` fixes the last
    output position exactly as it fixes the first, so a big-endian low byte ties
    between partners for the same reason a little-endian one does. The non-circularity
    that matters is that the boundary is DERIVED from the layout twice over
    before any save is read, which is
    ``test_the_coarseness_tie_boundary_is_the_mantissa_that_fits_in_the_low_stored_byte``.
    """
    sweep = _permutations_or_skip()

    assert sweep.coarseness_population > 0, (
        "no float32 value in this library carries differing interior stored "
        "bytes, so the coarseness census ran over an empty population and every "
        "comparison below is between two zeroes"
    )
    assert _TIED_WIDTHS, "no width falls inside the low stored byte, so this grades nothing"

    for perm in sorted(sweep.coarseness):
        partner = _with_the_middle_swapped(perm)
        mine, theirs = sweep.coarseness[perm], sweep.coarseness[partner]
        for width in _TIED_WIDTHS:
            assert mine.get(width, 0) == theirs.get(width, 0), (
                f"ordering {perm} counts {mine.get(width, 0)} values coarse to "
                f"{width} mantissa bits and its swapped partner {partner} counts "
                f"{theirs.get(width, 0)}. Those bits are stored byte "
                f"{perm[_IDENTITY[0]]} under both readings and the swap does not "
                "move it, so a difference means the count is not reading the bits "
                "this module believes it is"
            )


def test_the_coarseness_verdict_does_not_depend_on_which_mantissa_width_it_scores() -> None:
    """THE DISCRIMINATING REGION, QUANTIFIED so no width had to be chosen.

    Above the low stored byte the swap replaces mantissa bits with bytes that
    carried exponent and high-mantissa information, so the parameter CAN
    discriminate there. It is asserted to discriminate the same way at EVERY
    such width - the as-stored reading strictly coarser, never tied, never
    reversed. A result holding at one width and not another would be a result
    that depended on picking the width, and this says it does not.

    THAT IS THE ANSWER TO THE FITTED-THRESHOLD OBJECTION, and it is made by
    quantifying rather than by arguing. There is no width in this module that
    could be narrowed until the corpus separated.

    A RECORDED FALSE-RED RISK, AND IT IS NOT THE SHIPPED RESULT'S RISK. STRICT
    at every width is a stronger claim than the predicate deciding the shipped
    constant needs - :func:`_coarse_oracle_holds` requires domination everywhere
    and strictness only SOMEWHERE. Measured: on a synthetic population of purely
    authored floats the two counts TIE at the first discriminating width, so a
    corpus of that character would red this test while the byte order it grades
    stayed correct. That is CS-432's shape and it is recorded here rather than
    engineered away, because weakening the assertion to match the predicate
    would make this test a restatement of the headline one and retire the
    per-width visibility that is its whole content. IF THIS REDS, READ IT AS A
    STATEMENT ABOUT THE CORPUS'S CHARACTER: the shipped constant rests on
    :func:`_coarse_oracle_holds`, which such a corpus would still satisfy.
    """
    sweep = _permutations_or_skip()

    assert sweep.coarseness_population > 0, (
        "the coarseness census scored no value, so the comparisons below are "
        "between two empty counts and would hold for any byte order at all"
    )
    assert _DISCRIMINATING_WIDTHS, "no width above the low stored byte, so this grades nothing"

    as_stored = sweep.coarseness[_IDENTITY]
    swapped = sweep.coarseness[_MIDDLE_SWAP]
    for width in _DISCRIMINATING_WIDTHS:
        assert as_stored.get(width, 0) > swapped.get(width, 0), (
            f"at {width} mantissa bits the as-stored reading is coarse on "
            f"{as_stored.get(width, 0)} values and the middle swap on "
            f"{swapped.get(width, 0)}. The result is asserted at every width "
            "precisely so it cannot rest on one, and a width where it fails or "
            "ties is a width at which the separation is not there"
        )


def test_the_mantissa_coarseness_oracle_separates_the_middle_swap_from_the_identity() -> None:
    """CS-469 - THE DISCRIMINATOR THE FLOAT32 POPULATION CAN ACTUALLY CARRY.

    WHAT WAS BLOCKING THIS, stated exactly, because the wrong diagnosis was
    ruled once and refuted. The two shipped value oracles leave the identity and
    the middle swap standing, and the library holds the evidence to separate
    them: the census's admitted population is exactly the float32 values whose
    middle bytes differ, and the run that measures it reports how many. What
    could not use that evidence is the shipped float32 oracle's magnitude band,
    and that it cannot is DERIVED rather than described: the assertion below
    requires the middle swap to be a member of ``float_oracle_holds``, so the
    band demonstrably does not rule it out. NO NUMBER AND NO MECHANISM IS
    OFFERED BESIDE IT - three were, in successive revisions, and all three were
    measured false. THE DISCRIMINATION WAS LOST IN THE PREDICATE, NOT ABSENT
    FROM THE DATA.

    WHAT THIS ORACLE ASKS INSTEAD is how many values keep the low-mantissa zeros
    that an authored float has and a wrongly ordered read destroys. Coarseness
    has no width to survive being doubled, which is precisely why it bites where
    the band cannot.

    THE MIDDLE SWAP MUST STILL PASS THE OTHER TWO, and that is asserted rather
    than assumed. It is what makes this oracle the one doing the removing: if
    either shipped oracle had already ruled the swap out, the narrowing below
    would be someone else's and this would be decoration.
    """
    sweep = _permutations_or_skip()

    assert sweep.coarseness_population > 0, (
        "the coarseness census scored no value, so its verdict is a claim about "
        "an empty population and every ordering would tie with its partner"
    )
    assert _MIDDLE_SWAP in sweep.int_oracle_holds & sweep.float_oracle_holds, (
        "the middle swap does not survive both shipped value oracles on this "
        "library, so it is not the candidate this oracle exists to remove and "
        "the narrowing below is not the one CS-469 asked for"
    )
    assert _IDENTITY in sweep.coarse_oracle_holds, (
        "the as-stored ordering does not out-coarsen the middle swap, so the "
        "evidence favours a reading the module does not ship - which is a finding "
        "about the decoder and not about this oracle"
    )
    assert _MIDDLE_SWAP not in sweep.coarse_oracle_holds, (
        "the middle swap also passes the coarseness oracle. The predicate is "
        "antisymmetric, so both members of a pair passing means it is returning a "
        "verdict without comparing anything"
    )


# ---------------------------------------------------------------------------
# The survivor derivation - what three oracles between them leave standing
# ---------------------------------------------------------------------------


def test_the_shipped_candidate_set_is_what_the_value_oracles_cannot_separate() -> None:
    """WHAT THE VALUE ORACLES LEAVE OPEN, derived rather than asserted about.

    Each scored value is decoded once per ordering of its OWN four stored bytes,
    and three oracles are then applied to each ordering. Two are the shipped
    ones, applied exactly as ``test_properties`` applies them - a non-empty
    population, a majority carrying the signature as read, a minority carrying
    it swapped. The third is this module's mantissa-coarseness oracle. An
    ordering all three still pass is one they cannot separate from the as-stored
    reading.

    THE SHIPPED SET IS WHATEVER THIS INTERSECTION IS, AND ONLY THAT. It is
    derived here from the library and asserted equal to the constant, in that
    direction: the constant narrows when the derivation narrows, never the other
    way round. Deleting an oracle widens what survives and turns this red rather
    than quietly leaving a stronger claim on the books.

    HOW THE THREE ORACLES DIVIDE THE WORK, which is why the intersection lands
    where it does. The int32 signature constrains only which stored byte reaches
    the LOW output position. The float32 magnitude band constrains only which
    reaches the HIGH one. NEITHER SAYS ANYTHING ABOUT THE TWO IN THE MIDDLE,
    which is why they leave a pair rather than one. The coarseness oracle is
    exactly the one that speaks to the middle pair, and it is CS-469.

    THE RESULT IS JOINT AND NO SINGLE POPULATION PRODUCES IT. The coarseness
    oracle scores float32 values only, and float32 evidence alone still leaves
    more than one ordering standing; so does int32 evidence alone. What narrows
    to one is the intersection of all three, so the per-type status words in
    ``objects.VALUE_BYTE_ORDER_STATUS`` continue to record what a single type's
    own oracles settle, which is less than this.

    STATED LIMIT, AND IT IS STILL ABOUT THE ORACLES RATHER THAN THE CORPUS. A
    candidate surviving here is one these three do not rule out; that is not a
    claim that the format could plausibly use it. And the corpus was never the
    obstacle: the coarseness census admits the float32 values whose interior
    stored bytes differ, and the run that measures it reports how many, so the
    evidence was in the library the whole time. Do not write, here or
    downstream, that the question was blocked by the data.

    WHAT SIZE THAT POPULATION IS, IS NOT GRADED HERE and no assertion in this
    module claims it. The only thing asserted is that it is non-empty. A floor
    on its size would be a corpus-coupled constant that the operator's next
    session could red for no defect at all - CS-432's shape - so the module
    declines to carry one, and any stronger word for the population is an
    observation of a run rather than a claim the suite checks.
    """
    sweep = _permutations_or_skip()

    assert sweep.scored_values > 0, (
        "no int32 or float32 value was scored anywhere in this library, so both "
        "oracles ran over an empty population and every ordering would survive"
    )
    assert _IDENTITY in sweep.int_oracle_holds, (
        "the as-stored ordering does not pass the shipped int32 oracle on this "
        "library, so the survivor set below is derived from an oracle that "
        "disagrees with the reading the module ships"
    )
    assert _IDENTITY in sweep.float_oracle_holds, (
        "the as-stored ordering does not pass the shipped float32 oracle on this "
        "library, so the survivor set below is derived from an oracle that "
        "disagrees with the reading the module ships"
    )
    assert _IDENTITY in sweep.coarse_oracle_holds, (
        "the as-stored ordering does not pass the mantissa-coarseness oracle on "
        "this library, so the survivor set below is derived from an oracle that "
        "disagrees with the reading the module ships"
    )

    shipped_two = sweep.int_oracle_holds & sweep.float_oracle_holds
    assert shipped_two <= {_IDENTITY, _MIDDLE_SWAP}, (
        f"the two shipped oracles leave {sorted(shipped_two)} standing, which is "
        "more than the identity and its middle-swapped partner. The coarseness "
        "oracle's population is tailored to THAT PAIR - it is the set of values "
        "the middle swap changes - so a third ordering reaching this intersection "
        "would have its coarseness verdict decided on a population not tailored "
        "to it, and the narrowing below would rest on a comparison this module "
        "does not license"
    )

    derived = sweep.int_oracle_holds & sweep.float_oracle_holds & sweep.coarse_oracle_holds
    shipped = objects.BYTE_ORDER_SURVIVING_CANDIDATES

    assert frozenset(derived) == frozenset(shipped), (
        f"the three value oracles fail to separate {sorted(derived)} from the "
        f"as-stored ordering, and the module records {sorted(shipped)}. A shipped "
        "set NARROWER than the derived one claims a discrimination the oracles do "
        "not make; a WIDER one leaves a candidate on the books that they do rule out"
    )


# ---------------------------------------------------------------------------
# The one-byte types - LIBRARY-FREE, so this half runs on CI
# ---------------------------------------------------------------------------


def test_every_one_byte_value_type_is_recorded_as_byte_order_vacuous() -> None:
    """A one-byte value has no byte order, and the module has to say so.

    THE POPULATION IS DERIVED FROM THE SHIPPED TABLE rather than listed here, so
    a one-byte entry added later is covered without anyone remembering to add
    it. The question is not whether the recorded status is TRUE of the format -
    for a single byte that is arithmetic - but whether the module records it,
    because a type left unrecorded is one a later reader has to re-derive.

    IT READS NO SAVE, which is the point of siting it here. The rest of this
    module skips on a machine with no game and no library; this half runs on CI,
    where CS-426 records that the library-backed evidence is unavailable.
    """
    statuses = objects.BYTE_ORDER_STATUSES
    recorded = objects.VALUE_BYTE_ORDER_STATUS
    vacuous = objects.BYTE_ORDER_VACUOUS
    fixed = objects._FIXED_WIDTH_VALUES  # noqa: SLF001

    one_byte = {word for word, (width, _code) in fixed.items() if width == _ONE_BYTE}
    wider = {word for word, (width, _code) in fixed.items() if width > _ONE_BYTE}
    assert one_byte, "no one-byte entry in the shipped table, so this test grades nothing"
    assert wider, "no wider entry in the shipped table, so the contrast below is vacuous"

    for word in sorted(one_byte | {_BOOL_WORD}):
        assert recorded.get(word) == vacuous, (
            f"{word} carries a one-byte value and is recorded as "
            f"{recorded.get(word)!r} rather than {vacuous!r}. One byte has no "
            "order to get wrong, so a status implying an open question about it "
            "is a question nothing can answer"
        )
    for word in sorted(wider):
        assert recorded.get(word) != vacuous, (
            f"{word} carries a value wider than one byte and is recorded as "
            f"{vacuous!r}. Its bytes have an order, and calling that vacuous "
            "retires a question this project has not answered"
        )
    unknown = {word: status for word, status in recorded.items() if status not in statuses}
    assert not unknown, (
        f"these type words carry a status the module does not declare: {unknown}. "
        "A status outside the declared set is one no reader can interpret and no "
        "test can grade"
    )


# ---------------------------------------------------------------------------
# The emptiness guard - and its paired control
# ---------------------------------------------------------------------------

#: Statements that leave a function body doing nothing at all.
_INERT: Final = (ast.Pass,)


def _is_inert(statement: ast.stmt) -> bool:
    """Whether one statement leaves the body doing nothing.

    Three shapes count: a bare ``pass``; a bare expression that is a constant,
    which is what a docstring becomes once it is the only thing left and what a
    stubbed body is usually written as; and an ``assert`` on a literal constant,
    which is the shape the sibling guard names as its own blind spot.

    Args:
        statement: One statement from a function body.

    Returns:
        True when the statement performs no check.
    """
    if isinstance(statement, _INERT):
        return True
    if isinstance(statement, ast.Assert):
        return isinstance(statement.test, ast.Constant) and bool(statement.test.value)
    return isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Constant)


def _hollow_tests(tree: ast.Module) -> list[str]:
    """Every test in a module whose body performs no check at all.

    WHAT THE SIBLING GUARD SAYS ABOUT ITSELF, quoted rather than paraphrased,
    because an earlier revision of this docstring paraphrased it wrongly.
    ``test_properties._gutted_tests`` reports an early terminator with dead
    statements after it, and its own docstring records that "A test emptied to
    ``pass``, or one whose assertions are rewritten to ``assert True``, leaves
    no unreachable statement and is not detected here." It names ``pass`` and
    ``assert True``. It does not name a body emptied to a docstring, which the
    earlier paraphrase here attributed to it.

    THIS GUARD DOES NOT COVER THE WHOLE REMAINDER, and the claim that it covered
    "exactly that remainder" was false. It reports three shapes - ``pass``, a
    body that is only a constant expression, and an ``assert`` on a literal
    constant. SHAPES NEITHER GUARD CATCHES, recorded rather than left to be
    discovered: a body that is a single bare ``return`` with nothing after it,
    since the sibling only inspects statements BEFORE the last one; a body that
    is a single ``pytest.skip()`` call, which is camouflaged in this module
    because several tests here skip legitimately; and an assertion on a
    non-literal expression that is always true, such as a comparison of a value
    with itself. The consumer below runs both guards, so what is covered is the
    union of two named checks and not the whole class.

    Args:
        tree: The parsed module.

    Returns:
        ``name at line N`` for each test whose body is entirely inert.
    """
    found: list[str] = []
    for node in test_properties._scanned_functions(tree).values():  # noqa: SLF001
        if not node.name.startswith("test_"):
            continue
        if all(_is_inert(statement) for statement in node.body):
            found.append(f"{node.name} at line {node.lineno}")
    return found


#: The names the coarseness census is allowed to read ``body`` through, besides
#: its ONE slice, mapped to the argument position carrying the OFFSET - or None
#: for a reader that takes no offset at all. A read outside this set is a second
#: route to the bytes; a read inside it at the wrong offset is a second VALUE,
#: and the control below forbids both.
_BODY_READERS: Final[Mapping[str, int | None]] = MappingProxyType(
    {"len": None, "_decode_fixed_width": 1}
)

#: The one offset the census may reach the body at: the start the SHIPPED walk
#: reported for the tag under scrutiny. Anything else locates a different value.
_VALUE_OFFSET_NAME: Final = "value_at"


def _offset_label(node: ast.expr | None) -> str:
    """Name one offset expression for a failure message. COUNTS AND NAMES ONLY.

    Args:
        node: The offset expression, or None where a slice omits its bound.

    Returns:
        The bare name where it is one, and the node kind otherwise. NEVER the
        expression's value - this runs over source, and a rendered constant from
        a body index is still a number about a save.
    """
    if node is None:
        return "<absent>"
    if isinstance(node, ast.Name):
        return node.id
    return f"<{type(node).__name__}>"


def _body_reads(function: ast.FunctionDef) -> tuple[int, int, tuple[str, ...], int]:
    """Measure how a function reaches the decompressed body: route, and offset.

    THIS IS THE CONTROL THAT MAKES SINGLE-SLICE OWNERSHIP A PROPERTY RATHER THAN
    A CONVENTION. A grader sited beside a slice can always be pointed at a
    different local than the tally consumes - that was measured, and the bypass
    was four lines.

    COUNTING CUTS ALONE WAS NOT ENOUGH EITHER, and an earlier revision of this
    docstring claimed it could not be worked around. IT WAS. The allowlist
    admits the shipped decoder, which is a general read-the-value-at-any-offset
    primitive whose result packs straight back to bytes - so a census could
    reach displaced bytes with ONE cut and no unaccounted read at all. The
    degree of freedom had simply moved from which local the grade reads to which
    OFFSET the allowlisted reader is called at.

    SO THE OFFSET IS CONSTRAINED TOO, and the name it must be is
    :data:`_VALUE_OFFSET_NAME`. Reaching the body anywhere but at the offset the
    shipped walk reported is reaching a different value, whatever route is used.

    AND THAT NAME MAY BE BOUND ONLY ONCE. Requiring the offset EXPRESSION to be
    a bare name is defeated by rebinding the name itself - displace it, read,
    restore - which this author built and measured before shipping the
    constraint. The binding count closes it: the census takes ``value_at`` from
    the tag tuple and never assigns it again.

    Args:
        function: The census function's syntax tree.

    Returns:
        Slices taken of ``body``; reads of ``body`` that are neither a slice nor
        an argument to a reader in :data:`_BODY_READERS`; the offset each
        body-reaching read used, named; and how many times the offset name is
        BOUND in this function.
    """
    slices = 0
    accounted: set[int] = set()
    offsets: list[str] = []
    for node in ast.walk(function):
        if (
            isinstance(node, ast.Subscript)
            and isinstance(node.value, ast.Name)
            and node.value.id == "body"
            and isinstance(node.slice, ast.Slice)
        ):
            slices += 1
            accounted.add(id(node.value))
            offsets.append(_offset_label(node.slice.lower))
        if isinstance(node, ast.Call):
            name = None
            if isinstance(node.func, ast.Attribute):
                name = node.func.attr
            elif isinstance(node.func, ast.Name):
                name = node.func.id
            if name is None or name not in _BODY_READERS:
                continue
            at = _BODY_READERS[name]
            for argument in node.args:
                if isinstance(argument, ast.Name) and argument.id == "body":
                    accounted.add(id(argument))
                    if at is not None:
                        offsets.append(
                            _offset_label(node.args[at] if at < len(node.args) else None)
                        )
    loose = sum(
        1
        for node in ast.walk(function)
        if isinstance(node, ast.Name) and node.id == "body" and id(node) not in accounted
    )
    bindings = sum(
        1
        for node in ast.walk(function)
        if isinstance(node, ast.Name)
        and node.id == _VALUE_OFFSET_NAME
        and isinstance(node.ctx, ast.Store)
    ) + sum(
        # A PARAMETER IS NOT AN ``ast.Name``. A nested def or a lambda taking the
        # offset name shadows it in its own scope, and the walk above cannot see
        # that - measured: a five-line nested reader scored one cut, every offset
        # a bare name and one binding, with the census fully displaced.
        1
        for node in ast.walk(function)
        if isinstance(node, ast.arg) and node.arg == _VALUE_OFFSET_NAME
    )
    return slices, loose, tuple(offsets), bindings


def _named_function(tree: ast.Module, name: str) -> ast.FunctionDef:
    """Fetch one module-level function's tree by name.

    Args:
        tree: The parsed module.
        name: The function's name.

    Returns:
        Its definition node.
    """
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise AssertionError(f"{name} is not defined at module scope in this module")


def test_the_coarseness_census_cuts_the_body_exactly_once() -> None:
    """SINGLE-SLICE OWNERSHIP, ENFORCED AGAINST EVERY SHAPE SO FAR MEASURED.

    THE HEADLINE USED TO SAY THE CENSUS "cannot be pointed elsewhere" AND THAT
    WAS FALSIFIED. Each rule below closed the bypass that defeated the one
    before it, and each time the closing was believed final. The honest claim is
    the enumerated one: these three rules, and the shapes named as residuals.

    WHY A VALUE-EQUALITY GRADE WAS NOT ENOUGH, measured rather than supposed. An
    earlier revision graded the bytes the tally REPORTED having scored, on the
    reasoning that a grader reading a call-site local could be handed a
    different one. That reasoning was right and the fix was not: the report is
    itself a call-site local, and rebinding it after a second, displaced slice
    restored the whole original defect in four lines with the entire suite still
    green. AS LONG AS THE CALL SITE CUTS AND THE GRADER COMPARES, A MUTATION CAN
    SEPARATE THE TWO. The degree of freedom has to go, not be guarded.

    SO THE RULE IS STRUCTURAL, AND IT IS THREE RULES RATHER THAN ONE - each
    added because the one before it was worked around and measured to be.

      ONE CUT. The census reads the body through exactly one slice, and every
      other read is an argument to a named reader. A second cut is a second
      route to the bytes whatever local it lands in.

      ONE OFFSET. Every body-reaching read - the cut, and each allowlisted
      reader - locates the value at the offset the SHIPPED WALK reported and at
      no other. Counting cuts alone was defeated: the allowlisted decoder reads
      a value at any offset and its result packs straight back to bytes, so a
      displaced census needed one cut, no unaccounted read, and six lines.

      ONE BINDING. That offset name is bound once, from the tag tuple. Requiring
      the offset EXPRESSION to be a bare name is defeated by rebinding the name
      around the read - this author built that bypass before shipping the rule.
      A BINDING IS NOT ONLY AN ASSIGNMENT: a nested ``def`` or a ``lambda``
      taking the offset name as a PARAMETER shadows it in its own scope, and a
      parameter is an ``ast.arg`` rather than an ``ast.Name``, so the assignment
      walk alone did not see it. Both are counted.

    WHAT IT STILL DOES NOT COVER, stated at the reach the walk actually has.
    Displacing the tag's own reported offset at its single binding moves the
    slice AND the shipped decode it is compared with, together - that is the
    SHARED LOCATOR, it is the extent anchor's question, and nothing in this
    section answers it. (It is not silent in practice: with one shared cut,
    displacing it also displaces the magnitude tallies, and both shipped oracles
    collapse.) Reaching the body through ``locals()`` or a frame walk names it
    nowhere and is not counted; that is control rewriting rather than a census
    fault, and it is CS-473's class.

    A HELPER THIS MODULE DOES NOT DEFINE IS **NOT** IN THAT GAP, and an earlier
    revision of this paragraph said it was. Handing ``body`` to any call outside
    :data:`_BODY_READERS` makes it a LOOSE read and reds this test - measured on
    ``bytes(body)`` and on ``memoryview(body)`` alike. Understating a control's
    reach misleads the next reader as surely as overstating it.

    IT READS NO SAVE - it parses this module's own source, so it runs on CI.
    """
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    census = _named_function(tree, "_score_values_under_every_permutation")
    tally = _named_function(tree, "_tally_mantissa_coarseness")

    slices, loose, offsets, bindings = _body_reads(census)
    assert slices == 1, (
        f"the census cuts the decompressed body {slices} times. Exactly one cut "
        "is the whole defence: a second one can be handed to the tally while the "
        "grade keeps reading the first, which was measured to restore a displaced "
        "census with every test in this module still passing"
    )
    assert loose == 0, (
        f"the census reads the body {loose} times outside its one slice and "
        f"outside {sorted(_BODY_READERS)}. An unaccounted read is another route "
        "to the bytes, and the count above cannot see what it is used for"
    )
    assert offsets, (
        "the census reaches the body at no offset this walk can see, so the "
        "constraint below grades nothing"
    )
    wrong = sorted({name for name in offsets if name != _VALUE_OFFSET_NAME})
    assert not wrong, (
        f"the census reaches the body at {wrong} as well as at "
        f"{_VALUE_OFFSET_NAME!r}. ONE CUT IS NOT ENOUGH ON ITS OWN: the "
        "allowlisted decoder reads a value at any offset and packs straight back "
        "to bytes, so a displaced census can be built with one cut and nothing "
        "unaccounted. A read at another offset is a read of another value"
    )
    assert bindings == 1, (
        f"{_VALUE_OFFSET_NAME!r} is bound {bindings} times in the census. It is "
        "taken from the tag tuple and never assigned again, because rebinding it "
        "around a read defeats the offset rule above while every offset "
        "expression stays a bare name"
    )

    tally_slices, tally_loose, tally_offsets, _ = _body_reads(tally)
    assert (tally_slices, tally_loose, tally_offsets) == (0, 0, ()), (
        f"the coarseness tally reaches the body itself - {tally_slices} slices, "
        f"{tally_loose} other reads, offsets {list(tally_offsets)}. It is handed "
        "the bytes to score precisely so the cut has one owner, and a read in "
        "here is one the census's grade never sees"
    )


def _assert_no_test_is_hollow(module_path: Path) -> None:
    """Assert no test in a module is emptied, by either known shape.

    Args:
        module_path: The consuming module's own file.
    """
    tree = ast.parse(module_path.read_text(encoding="utf-8"))
    tests = [name for name in test_properties._scanned_functions(tree) if name.startswith("test_")]  # noqa: SLF001
    assert tests, f"{module_path.name} defines no test, so this guard is vacuous"

    hollow = _hollow_tests(tree)
    assert not hollow, (
        f"these tests perform no check at all: {hollow}. A body emptied to a "
        "docstring, to pass, or to an assertion on a literal passes for the same "
        "reason an empty one does, and leaves the name in the suite listing "
        "where a reader still counts it"
    )
    # The sibling shape, run here so this module is covered by both rather than
    # by whichever one its author happened to think of.
    assert not test_properties._gutted_tests(tree), (  # noqa: SLF001
        f"these tests are cut short and everything after the cut is dead: "
        f"{test_properties._gutted_tests(tree)}"  # noqa: SLF001
    )


def test_no_test_in_this_module_is_emptied_to_a_docstring_or_a_pass() -> None:
    """CS-433. Covers three emptied shapes, and :func:`_hollow_tests` records what it does not."""
    _assert_no_test_is_hollow(Path(__file__))


def test_the_emptiness_guard_catches_a_spliced_hollow_body(tmp_path: Path) -> None:
    """THE GUARD'S POWER, forced rather than asserted about.

    A guard returning an empty list on everything would pass on every module and
    read exactly like this one. Every shape the guard claims is spliced onto a
    COPY in ``tmp_path``, so nothing tracked is mutated: a body emptied to a
    docstring, one emptied to ``pass``, and one whose only assertion is on a
    literal - the shape the sibling guard names as its own blind spot. The
    unspliced source is then re-graded as a positive control, so the reds above
    are the splices rather than a guard that rejects whatever it is handed.

    THE CLAIMED SHAPES ARE FORCED AND THE UNCLAIMED ONES ARE NOT. What neither
    guard catches is recorded in :func:`_hollow_tests` rather than half-covered
    by a splice here, because a control that forced a shape the guard was never
    written to see would be red for the wrong reason.
    """
    source = Path(__file__).read_text(encoding="utf-8")
    for label, body in (
        ("docstring", '    """A test emptied to a docstring."""\n'),
        ("pass", '    """A test emptied to a pass."""\n    pass\n'),
        ("literal", '    """A test whose only assertion is on a literal."""\n    assert True\n'),
    ):
        spliced = tmp_path / f"hollow_{label}.py"
        spliced.write_text(
            f"{source}\n\ndef test_spliced_hollow_{label}_case() -> None:\n{body}",
            encoding="utf-8",
        )
        with pytest.raises(AssertionError) as caught:
            _assert_no_test_is_hollow(spliced)
        assert f"test_spliced_hollow_{label}_case" in str(caught.value), (
            f"the {label} splice was not the finding reported, so the guard "
            "reddened on something other than the shape it was handed"
        )

    _assert_no_test_is_hollow(Path(__file__))

# ---------------------------------------------------------------------------
# What the int32 oracle CANNOT separate, per type - CS-421 clause 3, route (b)
# ---------------------------------------------------------------------------


#: The ordering the byte-order question is ABOUT. Every other member of the group
#: is some rearrangement; this one is the endianness swap itself, and it is the
#: reading a status word claiming "no verdict" has to be silent about.
_REVERSAL: Final[tuple[int, ...]] = tuple(reversed(_IDENTITY))


@dataclass(frozen=True)
class _SeparabilitySweep:
    """What the shipped int32 oracle can and cannot tell apart. COUNTS ONLY.

    NO STORED BYTE AND NO DECODED VALUE LEAVES THIS SWEEP, for the reason every
    other sweep in this module gives: what crosses the boundary is counts,
    booleans and repo-literal type words, so a frame rendered under ``pytest -l``
    on any caller holds none of the library.

    Attributes:
        applied: Per four-byte type word, how many of that type's OWN values the
            shipped int32 tally actually accumulated. Zero means the oracle was
            never applied at all rather than applied and undecided - and the two
            must not be confused, because separating them is the entire reason
            the status word exists. ``FloatProperty`` is a live instance of the
            first: its values decode to a float, which that tally never sees.
        indistinguishable: Per type word, how many of the twenty-four orderings
            leave the oracle's whole accumulator equal to the as-stored one.
            REPORTED, NEVER ASSERTED ON. It is what makes the strength of the
            result legible to a reader - the oracle narrows one type's population
            to a pair of orderings and another's to half the group - and no
            threshold is placed on it anywhere, because a threshold on it would
            be exactly the floor-shaped reasoning this item must avoid.
        oracle_holds: Per type word, whether :func:`_int_oracle_holds` returns
            its green verdict on that type's own population.
        cannot_separate_the_reversal: The type words the oracle was APPLIED to
            and which it scored IDENTICALLY as stored and reversed. THIS IS THE
            DERIVED POPULATION the shipped status word is graded against.
        saves_read: Saves of a pair this grammar reads.
        failures: Exception type NAMES, not the exceptions themselves.
    """

    applied: Mapping[str, int]
    indistinguishable: Mapping[str, int]
    oracle_holds: Mapping[str, bool]
    cannot_separate_the_reversal: tuple[str, ...]
    saves_read: int
    failures: tuple[str, ...]


def _score_population(
    spec: tuple[int, str], population: Counter[bytes], perm: tuple[int, ...]
) -> test_properties._DecodeTally:
    """Feed one type's whole population to the SHIPPED int32 tally, reordered.

    THE DECODE IS THE SHIPPED ONE AND SO IS THE TALLY. Neither is reimplemented
    here, which is what makes this an application of the oracle rather than a
    transcription of what the oracle is believed to do - the same reasoning the
    survivor derivation above gives for importing both rather than copying them.

    Args:
        spec: The shipped fixed-width spec for this type word.
        population: The type's stored patterns, counted.
        perm: The ordering to read each stored pattern under.

    Returns:
        The accumulator the shipped int32 scorer filled.
    """
    tally = test_properties._DecodeTally(Counter(), set(), set())  # noqa: SLF001
    for stored, count in population.items():
        reordered = bytes(stored[index] for index in perm)
        value = objects._decode_fixed_width(reordered, 0, spec[0], spec)  # noqa: SLF001
        # KEYED ON THE DECODED SHAPE, and ``bool`` is excluded explicitly for the
        # same reason the shipped dispatch excludes it: it is a subclass of int.
        if not isinstance(value, int) or isinstance(value, bool):
            continue
        for _ in range(count):
            test_properties._tally_int32_byte_order(value, tally)  # noqa: SLF001
    return tally


def _collect_stored_patterns(
    extents: _Extents,
    specs: Mapping[str, tuple[int, str]],
    populations: Mapping[str, Counter[bytes]],
) -> None:
    """Fold one save's fixed-width stored patterns into the running census.

    SPLIT OUT OF THE SWEEP RATHER THAN INLINED, and the reason is a house one:
    the sweep was over the branch budget with this inside it. The split is not
    free of meaning either - this is the only frame that ever holds a body and a
    stored pattern together, and it returns nothing, so the sweep above it never
    binds either.

    EVERY TAG IS OFFERED AND THE SHIPPED TABLE DECIDES, which is what keeps a
    type word out of this census that the reader does not decode from a fixed
    width. The width is checked against the shipped spec rather than trusted from
    the tag, so a tag declaring a size the table disagrees with is skipped rather
    than censused at the wrong width.

    Args:
        extents: One decompressed body and its readable spans.
        specs: The shipped fixed-width table.
        populations: Per type word, the stored patterns seen so far. Mutated in
            place.
    """
    for start, end in extents.spans:
        tags = _walk_with_the_shipped_reader(extents.body, start, end)
        if tags is None:
            continue
        for word, value_at, size in tags:
            spec = specs.get(word)
            if spec is None or size != spec[0] or value_at + size > len(extents.body):
                continue
            populations[word][bytes(extents.body[value_at : value_at + size])] += 1


@dataclass(frozen=True)
class _Scored:
    """What scoring the whole census produced. COUNTS ONLY.

    Attributes:
        applied: Per type word, values the shipped int32 tally accumulated.
        indistinguishable: Per type word, orderings whose whole accumulator
            equals the as-stored one.
        oracle_holds: Per type word, the shipped predicate's verdict.
        blind: The type words applied to and scored identically under reversal.
    """

    applied: Mapping[str, int]
    indistinguishable: Mapping[str, int]
    oracle_holds: Mapping[str, bool]
    blind: tuple[str, ...]


def _census_stored_patterns(
    specs: Mapping[str, tuple[int, str]],
    populations: Mapping[str, Counter[bytes]],
) -> tuple[int, int, tuple[str, ...]]:
    """Walk the library once, folding every save's stored patterns in.

    THE WHOLE LOOP BODY IS INSIDE THE HANDLER, including ``path`` and the read
    result, for the reason :func:`_sweep_anchor` records: this frame is the only
    one that ever binds a save path and a whole save's bytes together, so it is
    the one frame that must never escape to a renderer.

    Args:
        specs: The shipped fixed-width table.
        populations: Per type word, the stored patterns seen. Mutated in place.

    Returns:
        Paths discovered, saves read, and exception type NAMES.
    """
    paths = test_properties._library_save_paths()  # noqa: SLF001
    saves_read = 0
    failures: list[str] = []
    for path in paths:
        # BROAD BY DESIGN, for the reason :func:`_sweep_anchor` records, and the
        # whole body including ``path`` is inside it.
        try:
            read, failure = _read_tagged_save(path)
            if failure is not None:
                failures.append(failure)
            if read is None:
                continue
            saves_read += 1
            _collect_stored_patterns(_extents_of(*read), specs, populations)
        except (Exception, SystemExit) as exc:
            failures.append(type(exc).__name__)
            continue
    return len(paths), saves_read, tuple(sorted(set(failures)))


def _carries_the_signature_both_ways(tally: test_properties._DecodeTally) -> bool:
    """Whether EVERY value scored carries the int32 signature under BOTH readings.

    THIS IS THE SANCTIONED REASON AND IT IS NARROWER THAN INVARIANCE, which is the
    distinction the whole status word turns on. An accumulator unchanged by the
    reversal has its two signature counters EQUAL - and they are equal when both
    are ZERO just as much as when both are total. A population carrying the
    signature under NEITHER reading is therefore invariant while being nothing
    like undecided, and a read of this census displaced by one byte produces
    exactly that state.

    IT IS A NAMED FUNCTION SO THAT IT CAN BE GRADED WITHOUT THE LIBRARY. Gutting
    this test to a tautology changed NOTHING any test could see, because on the
    operator's corpus the universal and the invariance conjunct beside it admit
    the same single word - so the corpus cannot tell them apart and a control that
    needs it never will. Hand-authored counters can, and
    :func:`test_the_signature_predicate_refuses_a_population_that_carries_neither`
    is what does.

    Args:
        tally: An accumulator the shipped int32 scorer has been fed.

    Returns:
        True when the population is non-empty and every value in it carried a
        zero high byte as stored AND as reversed.
    """
    seen = tally.counts["int32"]
    return bool(
        seen
        and tally.counts["int32_high_zero"] == seen
        and tally.counts["int32_high_zero_swapped"] == seen
    )


def _score_every_four_byte_type(
    specs: Mapping[str, tuple[int, str]],
    populations: Mapping[str, Counter[bytes]],
) -> _Scored:
    """Apply the shipped int32 oracle to each four-byte type under every ordering.

    Args:
        specs: The shipped fixed-width table.
        populations: Per type word, the censused stored patterns.

    Returns:
        The counts, the verdicts and the derived blind set.
    """
    applied: dict[str, int] = {}
    indistinguishable: dict[str, int] = {}
    holds: dict[str, bool] = {}
    blind: list[str] = []
    for word, spec in specs.items():
        if spec[0] != _FOUR_BYTES:
            continue
        population = populations[word]
        base = _score_population(spec, population, _IDENTITY)
        applied[word] = base.counts["int32"]
        holds[word] = _int_oracle_holds(base)
        indistinguishable[word] = sum(
            1
            for perm in _PERMUTATIONS
            if _score_population(spec, population, perm).counts == base.counts
        )
        # THE UNIVERSAL, NOT AN EQUALITY BETWEEN THE TWO COUNTERS, AND THE
        # DIFFERENCE WAS FOUND BY AN ADVERSARY RATHER THAN BY THE AUTHOR. Equal
        # counters make the accumulator invariant under the reversal, which is
        # what an earlier version tested - but they are equal when BOTH are zero
        # as well as when both are total. A population carrying the small-magnitude
        # signature under NEITHER reading therefore derived as "applied and
        # undecided", and a probe displacing this read by one byte produced exactly
        # that state and was still admitted. The sanctioned reason is narrower and
        # is what is implemented: EVERY value carries a zero high byte under BOTH
        # readings. That implies the invariance; the invariance does not imply it.
        # THE SECOND CONJUNCT IS IMPLIED BY THE FIRST AND IS KEPT ANYWAY, because
        # it is the READING THE STATUS WORD NAMES. The universal is counter
        # arithmetic; this scores the population under the reversal itself. If the
        # two ever disagreed the word's spelling would no longer describe its own
        # derivation, and a conjunction reddens where a comment would not.
        if _carries_the_signature_both_ways(base) and (
            _score_population(spec, population, _REVERSAL).counts == base.counts
        ):
            blind.append(word)
    return _Scored(
        applied=MappingProxyType(applied),
        indistinguishable=MappingProxyType(indistinguishable),
        oracle_holds=MappingProxyType(holds),
        blind=tuple(sorted(blind)),
    )


def _derive_separability() -> _SeparabilitySweep | None:
    """Apply the shipped int32 oracle to EVERY four-byte type's own values.

    WHY THIS IS A SEPARATE WALK FROM THE PERMUTATION CENSUS ABOVE. That census
    scores ``IntProperty`` and ``FloatProperty`` and skips every other type word
    by design - which is precisely why ``UInt32Property`` was scored by nothing
    for as long as it was. Widening it would change the population the CS-469
    result was derived from, so this asks its own question on its own walk.

    EVERY FRAME THAT CAN HOLD LIBRARY DATA IS CONTAINED, AND THE FIRST DRAFT OF
    THIS FUNCTION WAS NOT. It ran the whole scoring phase after the per-save
    loop, in the frame that still bound the path list, the last save's raw bytes
    and its parsed header - so any raise inside the shipped decoder or the
    shipped tally rendered a save path, the save-tree ACCOUNT DIRECTORY, a world
    name and the plaintext header options string, which is non-negotiable 12.
    An adversary demonstrated it three ways, one of them needing NO opt-in flag
    at all, because :func:`_score_population` takes the census as a PARAMETER and
    pytest renders a crashing frame's arguments by default. The repair is
    structural rather than careful: no frame in this function binds a path or a
    save, and the two helpers that do are called from inside the handler.

    WHAT IS HELD, STATED EXACTLY RATHER THAN FLATTERINGLY. One decompressed body
    is alive at a time, and beside it a counter of DISTINCT four-byte stored
    patterns which accumulates across the WHOLE library - those are raw body
    bytes, and there is no fixed bound on how many distinct ones a library
    yields. That is why the containment above is the control and the size is not.

    IT IS UNCACHED ON PURPOSE - see :func:`_sweep_separability` for the wrapper
    the graders use and why the two are separate.

    Returns:
        The sweep, or None when no save library is reachable.
    """
    specs = objects._FIXED_WIDTH_VALUES  # noqa: SLF001
    populations: dict[str, Counter[bytes]] = {word: Counter() for word in specs}
    saves_read = 0
    failures: tuple[str, ...] = ()
    scored: _Scored | None = None
    try:
        discovered, saves_read, failures = _census_stored_patterns(specs, populations)
        if not discovered:
            return None
        scored = _score_every_four_byte_type(specs, populations)
    except (Exception, SystemExit) as exc:
        # THE BACKSTOP, and it is what makes the containment above total. A raise
        # escaping here would unwind through a frame binding `populations`, which
        # is library-wide raw body bytes.
        failures = tuple(sorted({*failures, type(exc).__name__}))

    # A skip only when there is genuinely nothing to grade - see the same guard
    # in :func:`_sweep_anchor` for why a failure must not become a skip.
    if not saves_read and not failures:
        return None

    empty: Mapping[str, int] = MappingProxyType({})
    return _SeparabilitySweep(
        applied=scored.applied if scored else empty,
        indistinguishable=scored.indistinguishable if scored else empty,
        oracle_holds=scored.oracle_holds if scored else MappingProxyType({}),
        cannot_separate_the_reversal=scored.blind if scored else (),
        saves_read=saves_read,
        failures=failures,
    )


#: The memoised sweep, held in a list so that "nothing cached yet" and "cached a
#: real sweep" are the only two states it can be in. A None is never stored - see
#: :func:`_sweep_separability`.
_SEPARABILITY_CACHE: list[_SeparabilitySweep] = []


def _sweep_separability() -> _SeparabilitySweep | None:
    """The memoised derivation the graders read.

    A ``None`` IS NEVER CACHED, AND THAT IS THE ENTIRE CONTENT OF THIS FUNCTION.
    An earlier revision was an `lru_cache` over the whole result and its docstring
    claimed, in prose, that there was no cache to poison. THAT WAS FALSE and an
    adversary demonstrated it against the committed artifact: one earlier call
    made with library discovery patched empty cached the ``None``, and because
    nothing in the repository ever calls `cache_clear` on it, ALL FOUR
    library-backed graders of the status word skipped for the rest of the session
    - `tests/save` green at exit 0 with four skips, and
    `oracle_cannot_separate_readings` indistinguishable from `unscored`. The
    vector is not hypothetical: sibling modules that collect earlier already
    monkeypatch `_library_save_paths`, and the no-install gate accepts a skip by
    design.

    CACHING ONLY A REAL SWEEP REMOVES THE STATE RATHER THAN POLICING IT. When
    there is genuinely no library, :func:`_derive_separability` returns almost
    immediately - discovery comes back empty and no save is opened - so there is
    nothing worth memoising in that branch and a great deal to lose by doing it.

    Returns:
        The sweep, or None when no save library is reachable.
    """
    if _SEPARABILITY_CACHE:
        return _SEPARABILITY_CACHE[0]
    sweep = _derive_separability()
    if sweep is not None:
        _SEPARABILITY_CACHE.append(sweep)
    return sweep


def _separability_or_skip() -> _SeparabilitySweep:
    """Fetch a separability sweep, skipping when this machine has no library.

    Returns:
        The sweep.
    """
    sweep = _sweep_separability()
    if sweep is None:
        pytest.skip(
            "no save library on this machine - what the int32 oracle can separate "
            "is not gradeable here"
        )
    return sweep


def test_the_cannot_separate_status_is_derived_from_the_oracle() -> None:
    """The status word is derived from the oracle meeting the data - CS-421 (b).

    WHAT THE WORD CLAIMS, AND IT IS THREE THINGS RATHER THAN ONE. That a shipped
    oracle exists which can be applied to this type's values at all; that it WAS
    applied, to this type's own population out of the operator's library; and
    that it scored the as-stored reading and the reversed one IDENTICALLY, so it
    prefers neither and no verdict can be read out of it.

    THE THIRD CLAUSE IS A UNIVERSAL AND NOT A TUNED FRACTION: every value in the
    population carries the small-magnitude signature under BOTH readings, so the
    two counters the shipped predicate discriminates on are not merely equal but
    total, and no assignment of thresholds to a majority and a minority can
    separate readings that scored alike on every value.

    IT IS NOT THRESHOLD-FREE AND AN EARLIER REVISION OF THIS DOCSTRING SAID IT
    WAS. That sentence was measured FALSE by an adversary and is recorded here
    rather than quietly deleted: the derivation DOES count values - it requires
    the population to be non-empty and compares each counter against the count -
    and a ``> 0`` liveness clause is a floor this project has already recorded as
    not being a control. What is true is narrower: no threshold is placed on the
    RELATION between the two readings, which is the quantity the byte-order
    question turns on.

    WHAT THIS DOES NOT ESTABLISH, AND THE HONEST STATEMENT IS UNCOMFORTABLE. The
    verdict is a fact about this library's values and not a structural property of
    the oracle meeting the type. Measured by an adversary over a population of the
    same size and shape as this type's own: of the 65535 values a nine-copy
    single-pattern population could carry, 65280 would drive this same shipped
    machinery to a GREEN endianness verdict, and only 255 - the multiples of 256
    below the high byte - reach the undecided state recorded here. Injecting a
    single further value with a nonzero low byte empties the derived set and turns
    this test RED. That is why CS-421 does NOT close on this: an artifact that
    records what the oracle says today is worth shipping, and a CLOSE resting on
    which number this type happens to carry is the anecdote CS-432 exists to
    delete.

    THIS DERIVATION DOES NOT ANCHOR ITSELF, AND IT INHERITS ANCHORING RATHER THAN
    REPEATING IT. Measured by displacing this census's own read: at deltas of -3,
    -1, +2 and +3 the displaced bytes still carry the signature under both
    readings and are still admitted, so five of seven offsets in [-3, +3] survive
    - the tightening above kills only +1 and -2. What constrains WHICH bytes are
    read is
    :func:`test_no_fixed_width_value_depends_on_a_byte_outside_its_declared_extent`,
    which grades every fixed-width tag through :func:`_anchored`, this type
    included, and reddens when the shipped reader's value start moves. A
    displacement applied to THIS code alone would not be caught here, and that is
    a bound on this control rather than on the suite.

    WHAT "APPLIED" MEANS HERE IS NOT WHAT ``_admitted_words`` MEANS BY IT, and the
    two must not be collapsed. That probe asks which type words a shipped DISPATCH
    branches on, keyed on the TAG WORD. This asks whether the oracle's arithmetic
    was run over this type's own bytes, and it reaches the tally through the
    decoded shape. ``UInt32Property`` is outside the first and inside the second,
    which is exactly the gap the status word reports - but the two definitions
    never meet in one assertion, and nothing today would notice if they
    disagreed.

    THE SEAM IS WHY THE WORD SHIPS IN ``objects.py`` AND IS DERIVED HERE. That
    module cannot read the library without breaking the layering, so it ships the
    word and this test derives the verdict - the pattern CS-476 established for
    this same artifact. On a machine with no game this SKIPS, which is CS-426's
    recorded gap and is not closed by this item.
    """
    sweep = _separability_or_skip()
    derived = frozenset(sweep.cannot_separate_the_reversal)
    recorded = frozenset(
        word
        for word, status in objects.VALUE_BYTE_ORDER_STATUS.items()
        if status == objects.BYTE_ORDER_ORACLE_CANNOT_SEPARATE
    )
    assert derived == recorded, (
        f"the shipped int32 oracle scores {sorted(derived)} identically as stored and "
        f"reversed, while objects.VALUE_BYTE_ORDER_STATUS records {sorted(recorded)} as "
        f"{objects.BYTE_ORDER_ORACLE_CANNOT_SEPARATE!r}. THE EQUALITY IS ASSERTED IN "
        "BOTH DIRECTIONS ON PURPOSE. A word derived and not recorded ships a status "
        f"weaker than the evidence supports - most likely {objects.BYTE_ORDER_UNSCORED!r}, "
        "which says nothing looked when something did. A word recorded and not derived "
        "is the over-claim CS-476 was filed against wearing a new spelling: it asserts "
        "an oracle was applied and came back undecided when no such application "
        f"happened. Applied counts per type were {dict(sweep.applied)}, and the "
        "orderings each population cannot be told from the as-stored one were "
        f"{dict(sweep.indistinguishable)} of {len(_PERMUTATIONS)}."
    )


def test_the_int32_oracle_still_separates_a_type_it_can_separate() -> None:
    """A derivation that finds everything undecided has stopped reading an oracle.

    THIS IS THE FLOOR THE EQUALITY ABOVE CANNOT PROVIDE FOR ITSELF. Were the
    oracle to go blind on every population at once, the derived set would grow to
    hold every four-byte word and the equality would simply report a different
    set - it has no way to notice that the REASON changed from "this population
    cannot tell them apart" to "this oracle no longer tells anything apart". So a
    type the oracle does separate is required to exist. The strength of the
    contrast is reported in the message rather than asserted on, because a
    threshold on it would be a floor and floors are what this item must not ship.
    """
    sweep = _separability_or_skip()
    separated = sorted(
        word
        for word, applied in sweep.applied.items()
        if applied and word not in sweep.cannot_separate_the_reversal
    )
    assert separated, (
        "the shipped int32 oracle scores EVERY four-byte type identically as stored "
        "and reversed, so it separates nothing anywhere and the derivation above is "
        "reporting a property of the oracle rather than of any population. Applied "
        f"counts were {dict(sweep.applied)} and the indistinguishable orderings were "
        f"{dict(sweep.indistinguishable)} of {len(_PERMUTATIONS)}."
    )
    assert any(sweep.oracle_holds.values()), (
        "no four-byte type's population makes the shipped int32 predicate return its "
        "green verdict, so the oracle whose silence the status word records has "
        f"nothing to say anywhere. Verdicts were {dict(sweep.oracle_holds)}."
    )


def test_the_derivation_stops_holding_when_the_int32_tally_is_neutered(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The derived set reads the shipped oracle rather than something beside it.

    EMPTINESS IS THE REQUIREMENT, not mere change. An assertion that the derived
    set merely differs under a dead oracle is satisfied the moment one word drops
    out, so it would pass while a second word went on being admitted by something
    that is not an oracle at all. With the tally dead nothing is applied to any
    population, so the applied clause has to empty the set outright.

    IT CALLS THE UNCACHED DERIVATION, AND THAT IS THE POINT RATHER THAN A DETAIL.
    An earlier version drove the memoised :func:`_sweep_separability`, clearing
    its cache on both sides of the mutation - and that cache takes no argument,
    so it cannot be keyed on the mutation the way :func:`_sweep_anchor` is keyed
    on its displacement. Its correctness rested entirely on this test remembering
    a ``finally``; a fourth caller that forgot one would poison every later test
    in the session, and nothing graded that. Calling
    :func:`_derive_separability` removes the degree of freedom instead of
    policing it.
    """
    live = _separability_or_skip()
    assert live.cannot_separate_the_reversal, (
        "this control assumes the derivation admits something as shipped, and it does "
        "not. Read the equality test above first - that is the failure, and this test "
        "can say nothing until it is fixed."
    )

    monkeypatch.setattr(
        test_properties,
        "_tally_int32_byte_order",
        lambda value, tally: None,  # noqa: ARG005
    )
    neutered = _derive_separability()
    assert neutered is not None, (
        "the uncached derivation found no library while the memoised one did, so the "
        "two are not reading the same machine and this control grades nothing."
    )
    assert not neutered.cannot_separate_the_reversal, (
        "with the shipped int32 tally dead, "
        f"{sorted(neutered.cannot_separate_the_reversal)} is still derived as a type "
        "the oracle cannot separate. Nothing was applied to any population, so "
        "whatever still admits these words is not the oracle - and the shipped "
        f"status word is being graded against it. Applied counts were "
        f"{dict(neutered.applied)}."
    )


def test_a_raise_in_the_scoring_phase_carries_nothing_out_of_the_walk(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A fault in the scoring phase must not unwind through a frame holding a save.

    THIS CONTROL EXISTS BECAUSE THE FIRST VERSION OF THE SWEEP FAILED IT, and it
    was found by an adversary rather than by its author. The scoring phase ran
    outside every handler, in the frame that still bound the discovered path
    list, the last save's whole raw bytes and its parsed header. A raise from the
    shipped decoder or the shipped tally therefore rendered a save path, the
    save-tree ACCOUNT DIRECTORY, a world name and the plaintext header options
    string. That is non-negotiable 12, and the redactor in ``tests/conftest.py``
    does not cover the account directory - CS-466's recorded gap.

    ONE OF THE THREE DEMONSTRATED ROUTES NEEDED NO OPT-IN FLAG. pytest renders a
    crashing frame's ARGUMENTS by default, and :func:`_score_population` takes
    the whole census as a parameter, so an ordinary rename in a sibling test
    module dumped the operator's raw body bytes with a plain ``-q``.

    WHAT IS ASSERTED IS CONTAINMENT, WHICH IS THE PROPERTY THAT MAKES THE REST
    UNREACHABLE. If nothing escapes the walk there is no frame for a renderer to
    reach, so this does not have to enumerate what a traceback would have shown -
    it requires that there be no traceback. The failure is recorded rather than
    swallowed, so a library that scored nothing still reddens the graders above.
    """
    _separability_or_skip()

    def explode(*_args: object) -> object:
        raise RuntimeError("scoring fault planted by this control")

    monkeypatch.setattr(
        "tests.save.test_value_anchoring._score_population",
        explode,
    )
    contained = _derive_separability()

    assert contained is not None, (
        "the derivation returned None with a library present, so it reported the "
        "planted fault as an absent library. A failure must never become a skip - "
        "that is how a broken walk reads as an ungraded machine."
    )
    assert "RuntimeError" in contained.failures, (
        f"the planted scoring fault is not recorded in {contained.failures}. Either it "
        "never reached the handler or the handler swallowed its identity, and a fault "
        "reduced to nothing is one the graders above cannot see."
    )
    assert not contained.cannot_separate_the_reversal, (
        f"{sorted(contained.cannot_separate_the_reversal)} was derived as a type the "
        "oracle cannot separate while the scoring phase was raising on every call. "
        "Whatever produced that set did not come from scoring anything."
    )

    reachable = (
        list(contained.applied)
        + list(contained.indistinguishable)
        + list(contained.oracle_holds)
        + list(contained.cannot_separate_the_reversal)
        + list(contained.failures)
    )
    leaked = [item for item in reachable if not isinstance(item, str)]
    assert not leaked, (
        f"the sweep carries {len(leaked)} non-string key(s) out of the walk. Everything "
        "crossing this boundary is a count, a boolean or a repo-literal type word, so "
        "that a frame rendered on any caller holds none of the library."
    )


# ---------------------------------------------------------------------------
# The separability predicate - LIBRARY-FREE, so this half runs on CI
# ---------------------------------------------------------------------------


def _tally_of(seen: int, high_zero: int, high_zero_swapped: int) -> test_properties._DecodeTally:
    """A hand-authored accumulator, standing in for a population nobody has.

    Args:
        seen: Values scored.
        high_zero: Those carrying a zero high byte as stored.
        high_zero_swapped: Those carrying one under the reversed reading.

    Returns:
        The accumulator.
    """
    tally = test_properties._DecodeTally(Counter(), set(), set())  # noqa: SLF001
    tally.counts["int32"] = seen
    tally.counts["int32_high_zero"] = high_zero
    tally.counts["int32_high_zero_swapped"] = high_zero_swapped
    return tally


def test_the_signature_predicate_refuses_a_population_that_carries_neither() -> None:
    """Invariance is not the sanctioned reason, and the corpus cannot tell them apart.

    MEASURED, AND IT IS WHY THIS TEST IS HAND-AUTHORED RATHER THAN LIBRARY-BACKED.
    Replacing the universal in :func:`_carries_the_signature_both_ways` with a
    tautology left the whole of ``tests/save`` GREEN, because on the operator's
    corpus that clause and the reversal-invariance conjunct beside it admit the
    same single type word. A control resting on the corpus therefore cannot grade
    the difference between them, and the difference is the entire content of the
    status word: a population carrying the signature under NEITHER reading has two
    EQUAL counters, so it is invariant under the reversal, while being the exact
    opposite of a population that cannot tell the readings apart.

    THE BOTH-ZERO ROW IS NOT HYPOTHETICAL. Displacing this census's own read by
    one byte produces (9, 0, 0) against this type's real population - equal
    counters, fully invariant, and admitted by the predicate this replaced.
    """
    both_total = _tally_of(9, 9, 9)
    both_zero = _tally_of(9, 0, 0)

    assert _carries_the_signature_both_ways(both_total), (
        "a population every value of which carries the signature under both readings "
        "is the sanctioned undecided state, and the predicate refuses it."
    )
    assert not _carries_the_signature_both_ways(both_zero), (
        "a population carrying the signature under NEITHER reading was admitted as "
        "undecided. Its two counters are equal, so it is invariant under the reversal "
        "- which is exactly why invariance is not the test. This is the state a read "
        "displaced by one byte produces, and admitting it means the derivation cannot "
        "tell an undecided oracle from one that was handed the wrong bytes."
    )
    assert not _carries_the_signature_both_ways(_tally_of(9, 9, 0)), (
        "a population the oracle SEPARATES - total one way, zero the other - was "
        "admitted as undecided. That is the discriminating case the oracle exists for."
    )
    assert not _carries_the_signature_both_ways(_tally_of(0, 0, 0)), (
        "an empty population was admitted as undecided. Nothing was applied to it, so "
        "the honest status is unscored, and this is the confusion the word exists to "
        "prevent."
    )

    assert both_zero.counts["int32_high_zero"] == both_zero.counts["int32_high_zero_swapped"], (
        "this test's own premise has gone: the both-zero row is meant to have EQUAL "
        "counters, which is what makes it invariant under the reversal and what makes "
        "the contrast above worth drawing."
    )


def test_a_library_less_call_does_not_switch_the_graders_off_for_the_session() -> None:
    """A cached absence would disarm every library-backed grader of the status word.

    MEASURED AGAINST THE COMMITTED ARTIFACT BY AN ADVERSARY, NOT BY THE AUTHOR,
    and the author's docstring asserted the opposite in prose at the time. With
    the sweep memoised through an `lru_cache`, appending a single test that
    patched `_library_save_paths` empty and called it once left `tests/save` GREEN
    at exit 0 with FOUR SKIPS - every library-backed grader of
    `oracle_cannot_separate_readings` switched off for the whole session, leaving
    the word indistinguishable from `unscored`. Nothing in the repository calls
    `cache_clear` on that sweep, so the poisoning was permanent.

    THE ORDER HERE IS THE TEST. A cold cache is taken deliberately, because the
    defect only exists on the first call - a run that happens to reach a real
    library first is immune, which is exactly why an ordering-dependent hole
    survives a suite that usually passes.
    """
    _separability_or_skip()
    _SEPARABILITY_CACHE.clear()

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(test_properties, "_library_save_paths", tuple)
        assert _sweep_separability() is None, (
            "with discovery patched empty the sweep reported a library anyway, so this "
            "control cannot reach the state it exists to grade."
        )

    restored = _sweep_separability()
    assert restored is not None, (
        "a single call made while no library was reachable has left the sweep "
        "returning None on a machine that HAS one. Every library-backed grader of the "
        "byte-order status word now skips for the rest of the session, so the shipped "
        "word is graded by nothing while the suite stays green - which is worse than a "
        "red, because a skip reads as an ungraded machine rather than as a defect."
    )
