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

  THE SURVIVOR DERIVATION asks which permutations the two shipped VALUE oracles
  are unable to separate from the identity, and ties the answer to the shipped
  candidate set. It is the anti-overclaim control: it is what stops the shipped
  data drifting into claiming the value byte order is settled when the oracles
  behind that claim do not settle it.

BOTH CENSUSES END IN A NARROWING TO TWO, NOT IN A SETTLED ANSWER, and the
symmetry is the honest reading of this module rather than a coincidence. The
size field narrows to the as-stored ordering and the one that swaps its two
HIGH bytes, which are indistinguishable on every declared size small enough to
leave those bytes zero. The value narrows to the as-stored ordering and the one
that swaps its two MIDDLE bytes. Neither narrowing is closed here, and the
separating populations behind them are small enough that saying so matters.

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


@dataclass(frozen=True)
class _PermutationSweep:
    """What the two permutation censuses measured. COUNTS ONLY.

    Attributes:
        reach: Payloads reaching a terminator, by size-field permutation.
        int_oracle_holds: Permutations under which the shipped int32 oracle
            still returns its green verdict over the permuted VALUE bytes.
        float_oracle_holds: The same for the shipped float32 oracle.
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
) -> tuple[frozenset[tuple[int, ...]], frozenset[tuple[int, ...]]]:
    """Apply the two shipped VALUE oracles to each permutation's tally.

    THE PREDICATES ARE THE SHIPPED ASSERTIONS RE-EXPRESSED, not new ones, and
    they have ONE owner each - :func:`_int_oracle_holds` and
    :func:`_float_oracle_holds` - shared with the displacement derivation. The
    tallies themselves come from ``test_properties``, so the judgement is that
    module's own.

    Args:
        tallies: One tally per permutation of the value's four stored bytes.

    Returns:
        The permutations the int32 oracle still passes, and those the float32
        oracle still passes.
    """
    return (
        frozenset(perm for perm, tally in tallies.items() if _int_oracle_holds(tally)),
        frozenset(perm for perm, tally in tallies.items() if _float_oracle_holds(tally)),
    )


def _score_values_under_every_permutation(
    body: bytes,
    tags: list[tuple[str, int, int]],
    tallies: Mapping[tuple[int, ...], test_properties._DecodeTally],
) -> int:
    """Decode each scored value once per permutation of its own stored bytes.

    Args:
        body: The decompressed body.
        tags: The payload's tags, from the unrotated shipped walk.
        tallies: One tally per permutation, mutated in place.

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
        for perm in _PERMUTATIONS:
            reordered = bytes(stored[index] for index in perm)
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
                scored += _score_values_under_every_permutation(extents.body, tags, tallies)
        except (Exception, SystemExit) as exc:
            failures.append(type(exc).__name__)
            continue
    # A skip only when there is genuinely nothing to grade - see the same guard
    # in :func:`_sweep_anchor` for why a failure must not become a skip.
    if not seen_a_save and not failures:
        return None
    ints, floats = _oracle_verdicts(tallies)
    return _PermutationSweep(
        reach=MappingProxyType(dict(reach)),
        int_oracle_holds=ints,
        float_oracle_holds=floats,
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
# The survivor derivation - the anti-overclaim tie
# ---------------------------------------------------------------------------


def test_the_shipped_candidate_set_is_what_the_value_oracles_cannot_separate() -> None:
    """WHAT THE VALUE ORACLES LEAVE OPEN, derived rather than asserted about.

    Each scored value is decoded once per ordering of its OWN four stored bytes,
    and the two shipped value oracles are then applied to each ordering's tally
    exactly as ``test_properties`` applies them - a non-empty population, a
    majority carrying the signature as read, a minority carrying it swapped. An
    ordering both oracles still pass is one they cannot separate from the
    as-stored reading.

    THIS IS THE TIE THAT STOPS THE SHIPPED DATA OVERCLAIMING. The module under
    test records a CANDIDATE SET rather than a settled order, and this test is
    what keeps that set honest: derived here from the library, asserted equal to
    the shipped constant, so narrowing the constant without narrowing what the
    oracles actually distinguish turns the suite red instead of shipping a
    stronger claim than the evidence.

    HOW THE TWO ORACLES DIVIDE THE WORK, which is why the survivor set has the
    size it has. The int32 signature constrains only which stored byte reaches
    the LOW output position; the float32 magnitude band constrains only which
    reaches the HIGH one. Neither says anything about the two in the middle, so
    what survives both is the pair differing only there.

    STATED LIMIT, AND IT IS ABOUT THE ORACLES AND NOT ABOUT THE CORPUS. A
    candidate surviving here is one these two oracles do not rule out; it is not
    a claim that the format could plausibly use it, and it is NOT a claim that
    the library lacks the evidence to separate them. The library has that
    evidence in quantity: the two survivors differ only in the middle two stored
    bytes, and while few int32 values carry differing middle bytes, the great
    majority of float32 values do. What blocks the separation is the shipped
    float oracle's plausible-magnitude band, which spans dozens of octaves and
    admits almost every byte-swapped value as well. That is a weakness of the
    ORACLE. Do not write, here or downstream, that the question is blocked by
    the data.
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

    derived = sweep.int_oracle_holds & sweep.float_oracle_holds
    shipped = objects.BYTE_ORDER_SURVIVING_CANDIDATES

    assert frozenset(derived) == frozenset(shipped), (
        f"the two value oracles fail to separate {sorted(derived)} from the "
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
