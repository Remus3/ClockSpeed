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
touches the int32 not at all, leaves that oracle green and scoring BETTER than
the correct read. Its as-read majority survives at -2, -1, +2, +3 and +4.

SO A ROTATION CONTROL TESTING ONLY PLUS OR MINUS ONE WOULD PASS AND PROVE
NOTHING, and this module is built knowing that. What it adds is the ANCHORING
the value oracles lack, plus a census over the whole permutation group of a
four-byte field. It does NOT re-prove the byte order and it does NOT repair the
oracle it describes; both remain where they are.

THE THREE MEASUREMENTS HERE ARE ABOUT THREE DIFFERENT THINGS, and conflating
them is the failure this module is written to avoid.

  THE EXTENT ANCHOR asks whether a decoded fixed-width value depends on any
  byte outside the extent the tag declared for it. It compares the shipped
  decoder reading in place against the SAME decoder reading an isolated copy of
  exactly those bytes, surrounded by poison. Under a displacement the isolated
  read walks into poison and the two disagree, which is the detection the
  two-bit oracle has no way to make.

  THE SIZE-FIELD CENSUS asks which byte order the tag's DECLARED SIZE is read
  in, graded by how many payloads still reach their terminator. That is a
  different field, read by a different reader, and what it licenses is written
  at the test rather than left for a reader to infer.

  THE SURVIVOR DERIVATION asks which permutations the two shipped VALUE oracles
  are unable to separate from the identity, and ties the answer to the shipped
  candidate set. It is the anti-overclaim control: it is what stops the shipped
  data drifting into claiming the value byte order is settled when the oracles
  behind that claim do not settle it.

WHAT THE ANCHOR DOES NOT COVER, stated here and again at each test that uses
it, because attributing a gap to a control unable to fire on it is a mistake
this project's history records twice. A decoder replaced by a CONSTANT depends
on no bytes at all, so its in-place read and its isolated read agree and the
anchor stays green - that gap is CS-455 and it is not this module's. The
LOCATOR is shared between the two readings, so a fault in where the tag header
believes the value starts moves both together and is invisible here. And the
population is the FIXED-WIDTH types alone. All three limits are written beside
the test rather than left to be discovered.

PRIVACY, non-negotiables 11 and 12. COUNTS ONLY leave a sweep. No property
name, no decoded value, no file path and no body byte reaches a failure
message, an assertion, a print or an exception raised out of this module. Every
walk over real bytes sits inside a ``try`` that reduces anything raised to an
exception type NAME before a frame holding a body or a path can be rendered,
which is the containment ``test_decode_oracles`` describes at length. The two
discovery helpers are IMPORTED from ``test_properties`` rather than
transcribed, on the same reasoning that module's siblings give: the discovery
calls that resolve the account directory sit inside their own ``try``, and a
further transcription of that containment is a further place to get it subtly
wrong.

NO OBSERVED COUNT IS WRITTEN INTO AN ASSERTION OR A DOCSTRING HERE. The corpus
is the operator's live save library and it grows on every autosave, so a
payload total, a tag total or a mismatch total is stale before it can be
committed - and a constant sitting at an observed value going red on a correct
tree is CS-432, already open. The assertions are structural: zero, nonzero,
strict argmax, majority. A count may be interpolated into a failure MESSAGE,
where it is derived in the same run that reports it.
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

#: The displacement the anchor control fires under. FOUR, NOT ONE, and the
#: choice is the refutation's own finding rather than a preference: the value
#: oracles in ``test_properties`` survive a displacement of -2, -1, +2, +3 and
#: +4, so a control moving the read by one would be graded against an oracle
#: that already tolerates it and would demonstrate nothing about the extent
#: question. At +4 the in-place read leaves the int32 entirely and lands on the
#: following tag's name-length prefix, which is the exact displacement the
#: refutation showed scoring BETTER than the correct read.
_ANCHOR_DISPLACEMENT: Final = 4

#: Bytes in the tag's declared-size field, and in a four-byte value. The two
#: are separate fields read by separate readers; the width they share is why
#: one permutation group serves both censuses.
_FOUR_BYTES: Final = 4

#: Every ordering of four stored bytes, including the identity.
_PERMUTATIONS: Final = tuple(itertools.permutations(range(_FOUR_BYTES)))

#: The as-stored ordering, named so the argmax assertion and the survivor
#: derivation index the same tuple.
_IDENTITY: Final = (0, 1, 2, 3)

#: The width, in the shipped fixed-width table, that no byte order can move.
_ONE_BYTE: Final = 1

#: The two type words the shipped value oracles score, and the keys their
#: tallies are read back out of. Transcribed for the reason
#: ``test_properties`` gives at its own copy: importing the constant under test
#: would assert only that the module equals itself.
_INT_WORD: Final = "IntProperty"
_FLOAT_WORD: Final = "FloatProperty"
_BOOL_WORD: Final = "BoolProperty"

#: A hand-authored pattern for the rebind self-check. Sixteen ascending bytes,
#: so a four-byte read at 0 and one at +4 differ, and no save is touched.
_SELF_CHECK_PATTERN: Final = bytes(range(16))


@dataclass(frozen=True)
class _AnchorSweep:
    """What one anchoring pass over the real library measured. COUNTS ONLY.

    Attributes:
        payloads: Records seen in a save of a pair this grammar reads.
        reached: Those whose payload reached its terminator.
        tags_by_type: Fixed-width tags by type word. The keys are INTERSECTED
            with the shipped table inside the sweep, so no word that is not
            already in tracked source can leave it.
        fixed_width_tags: How many fixed-width tags the anchor graded.
        mismatches: Tags whose in-place read and isolated read disagreed, or
            where either call raised.
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
    mismatches: int
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
        scored_values: How many values the survivor derivation scored under the
            identity, so an empty population cannot pass as agreement.
        bodies_restored: Whether every in-place size-field permutation was put
            back, so the census graded permutations rather than a body it had
            progressively corrupted.
        failures: Exception type NAMES.
    """

    reach: Mapping[tuple[int, ...], int]
    int_oracle_holds: frozenset[tuple[int, ...]]
    float_oracle_holds: frozenset[tuple[int, ...]]
    scored_values: int
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
        read = objects._read_tag_header(mutable, name[1], end)  # type: ignore[arg-type]  # noqa: SLF001
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


def _tagged_saves() -> tuple[list[tuple[bytes, header.SaveHeader]], tuple[str, ...]]:
    """Read every save of a pair this grammar reads, contained.

    Every read sits inside the ``try`` here, and nothing about a failure leaves
    beyond an exception type NAME - a save path is what ``read_bytes`` binds as
    its ``self``, and pytest renders the arguments of an unwound frame with no
    opt-in flag.

    Returns:
        Save bytes paired with the parsed header for the readable pairs, and
        the type names of anything unexpected that was contained.
    """
    out: list[tuple[bytes, header.SaveHeader]] = []
    failures: list[str] = []
    for path in test_properties._library_save_paths():  # noqa: SLF001
        try:
            data = path.read_bytes()
            parsed = header.parse_header(data)
        except (OSError, header.HeaderError):
            # The two EXPECTED failures - an unreadable file and a save of a
            # version this project does not parse - stay silent skips, because
            # the library legitimately holds both and the callers treat any
            # recorded failure as fatal.
            continue
        except (Exception, SystemExit) as exc:
            # THE BACKSTOP. Anything unexpected escaping here unwinds through
            # `path.read_bytes()`, whose bound `self` IS the save path.
            # SystemExit is named because it is not an Exception and was
            # measured elsewhere in this package to render a path under `-q`
            # alone. KeyboardInterrupt is deliberately left free to unwind.
            failures.append(type(exc).__name__)
            continue
        if (parsed.header_version, parsed.save_version) in test_properties.TAGGED_PAIRS:
            out.append((data, parsed))
    return out, tuple(sorted(set(failures)))


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
    width = int_spec[0]
    (undisplaced,) = struct.unpack_from(int_spec[1], _SELF_CHECK_PATTERN, 0)
    (float_undisplaced,) = struct.unpack_from(float_spec[1], _SELF_CHECK_PATTERN, 0)
    moved = objects._decode_fixed_width(_SELF_CHECK_PATTERN, 0, width, int_spec)  # noqa: SLF001
    still = objects._decode_fixed_width(  # noqa: SLF001
        _SELF_CHECK_PATTERN, 0, float_spec[0], float_spec
    )
    return (not _agrees(moved, int(undisplaced)), _agrees(still, float(float_undisplaced)))


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
    saves, read_failures = _tagged_saves()
    if not saves:
        return None

    restore: Callable[[], None] | None = None
    changed: bool | None = None
    confined: bool | None = None
    payloads = reached = graded = mismatches = 0
    by_type: Counter[str] = Counter()
    failures: list[str] = list(read_failures)
    try:
        if delta is not None:
            restore = _install_displaced_int_decoder(delta)
            changed, confined = _self_check_the_rebind()
        for data, parsed in saves:
            # BROAD BY DESIGN: a narrower catch lets an unexpected type escape
            # carrying the save bytes, which is the leak this containment
            # closes. SystemExit for the reason `_tagged_saves` records.
            try:
                extents = _extents_of(data, parsed)
                payloads += extents.records
                for start, end in extents.spans:
                    tags = _walk_with_the_shipped_reader(extents.body, start, end)
                    if tags is None:
                        continue
                    reached += 1
                    for type_word, value_at, size in tags:
                        spec = objects._FIXED_WIDTH_VALUES.get(type_word)  # noqa: SLF001
                        if spec is None:
                            continue
                        by_type[type_word] += 1
                        graded += 1
                        if not _anchored(extents.body, value_at, size, spec):
                            mismatches += 1
            except (Exception, SystemExit) as exc:
                failures.append(type(exc).__name__)
                continue
    finally:
        if restore is not None:
            restore()
    return _AnchorSweep(
        payloads=payloads,
        reached=reached,
        # INTERSECTED WITH THE SHIPPED TABLE, so no word that is not already
        # written down in tracked source can leave the sweep.
        tags_by_type=MappingProxyType(
            {
                word: count
                for word, count in by_type.items()
                if word in objects._FIXED_WIDTH_VALUES  # noqa: SLF001
            }
        ),
        fixed_width_tags=graded,
        mismatches=mismatches,
        rebind_changed_the_int_read=changed,
        rebind_left_the_float_read_alone=confined,
        failures=tuple(sorted(set(failures))),
    )


def _anchored(body: bytes, value_at: int, size: int, spec: tuple[int, str]) -> bool:
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
        True when the two readings agree.
    """
    try:
        in_place = objects._decode_fixed_width(body, value_at, size, spec)  # noqa: SLF001
    except (Exception, SystemExit):
        return False
    isolated_bytes = _POISON + bytes(body[value_at : value_at + size]) + _POISON
    try:
        isolated = objects._decode_fixed_width(isolated_bytes, _PAD, size, spec)  # noqa: SLF001
    except (Exception, SystemExit):
        return False
    return _agrees(in_place, isolated)


def _oracle_verdicts(
    tallies: Mapping[tuple[int, ...], test_properties._DecodeTally],
) -> tuple[frozenset[tuple[int, ...]], frozenset[tuple[int, ...]]]:
    """Apply the two shipped VALUE oracles to each permutation's tally.

    THE PREDICATES ARE THE SHIPPED ASSERTIONS RE-EXPRESSED, not new ones: a
    non-empty population, a MAJORITY carrying the signature as read, and a
    MINORITY carrying it under the swapped reading. The tallies themselves come
    from ``test_properties``, so the judgement is that module's own.

    Args:
        tallies: One tally per permutation of the value's four stored bytes.

    Returns:
        The permutations the int32 oracle still passes, and those the float32
        oracle still passes.
    """
    ints: set[tuple[int, ...]] = set()
    floats: set[tuple[int, ...]] = set()
    for perm, tally in tallies.items():
        counts = tally.counts
        seen_int = counts["int32"]
        seen_float = counts["float32"]
        if (
            seen_int > 0
            and counts["int32_high_zero"] * 2 > seen_int
            and counts["int32_high_zero_swapped"] * 2 < seen_int
        ):
            ints.add(perm)
        if (
            seen_float > 0
            and counts["float32_plausible"] * 2 > seen_float
            and counts["float32_plausible_swapped"] * 2 < seen_float
        ):
            floats.add(perm)
    return frozenset(ints), frozenset(floats)


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

    ONE DECOMPRESSION PER SAVE, with every permutation walked while that body is
    alive, so the peak cost is one body rather than the whole library.

    Contained exactly as :func:`_sweep_anchor` is.

    Returns:
        The sweep, or None when no save library is reachable.
    """
    saves, read_failures = _tagged_saves()
    if not saves:
        return None

    reach: Counter[tuple[int, ...]] = Counter()
    tallies = {
        perm: test_properties._DecodeTally(Counter(), set(), set())  # noqa: SLF001
        for perm in _PERMUTATIONS
    }
    scored = 0
    restored = True
    failures: list[str] = list(read_failures)
    for data, parsed in saves:
        # BROAD BY DESIGN, for the reason `_sweep_anchor` records.
        try:
            extents = _extents_of(data, parsed)
            mutable = bytearray(extents.body)
            for perm in _PERMUTATIONS:
                reach[perm] += sum(
                    1
                    for start, end in extents.spans
                    if _reaches_with_a_permuted_size(mutable, start, end, perm)
                )
            # THE RESTORATION IS A CONTROL, not housekeeping. Every permutation
            # is applied in place and put back; if one were not, later
            # permutations would be graded against a progressively corrupted
            # body and the census would be measuring damage rather than order.
            restored = restored and bytes(mutable) == extents.body
            for start, end in extents.spans:
                tags = _walk_with_the_shipped_reader(extents.body, start, end)
                if tags is not None:
                    scored += _score_values_under_every_permutation(extents.body, tags, tallies)
        except (Exception, SystemExit) as exc:
            failures.append(type(exc).__name__)
            continue
    ints, floats = _oracle_verdicts(tallies)
    return _PermutationSweep(
        reach=MappingProxyType(dict(reach)),
        int_oracle_holds=ints,
        float_oracle_holds=floats,
        scored_values=scored,
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
    every tag says the decoded value is a function of its own declared extent
    and of nothing beside it. That is the property the stored-high-byte oracle
    cannot check at all: reducing a value to two bits leaves it green under a
    displacement that never touches the int32.

    STATED LIMIT ONE, AND IT IS NOT CS-455's. A decoder replaced by a CONSTANT
    depends on no bytes at all, so its in-place read and its isolated read are
    the same constant and this control stays GREEN. That was forced rather than
    reasoned: a decoder returning 1 leaves this test green. Fabrication is
    CS-455 and this test does not cover it, does not narrow it, and must not be
    cited as if it did. Attributing a gap to a control unable to fire on it is a
    mistake this package's history records twice.

    STATED LIMIT TWO - THE LOCATOR IS SHARED, so this is anchoring against the
    DECLARATION and not against the truth. Both readings take ``value_at`` and
    ``size`` from ONE ``objects._read_tag_header`` call, and the isolated copy
    is sliced at that same offset, so a fault in where the tag header BELIEVES
    the value starts moves both readings together and this control cannot see
    it. What it grades is whether the decoder honours the extent it was handed,
    which is a different question from whether that extent is the right one. The
    tag walk's own synchronisation is what bounds the second question, and it is
    graded elsewhere by terminator reach rather than here.

    STATED LIMIT THREE - THE POPULATION IS THE FIXED-WIDTH TYPES. BoolProperty
    carries its value in the tag and the string and reference decoders are read
    by different functions, so none of them is anchored by this test and its
    green says nothing about any of them.

    THE FIRST TWO ASSERTIONS ARE LIVENESS. A zero mismatch count is satisfied
    trivially by a sweep that graded nothing, so the walk and the population are
    both asserted non-empty beside it.
    """
    sweep = _anchor_or_skip(None)

    assert sweep.reached > 0, (
        "no payload reached a terminator anywhere in this library, so the anchor "
        "graded nothing and its zero below is the vacuous kind"
    )
    assert sweep.fixed_width_tags > 0, (
        "no fixed-width tag was found in a library of "
        f"{sweep.payloads} payloads, so there was nothing to anchor"
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

    WHY FOUR AND NOT ONE. The refutation of the stored-high-byte oracle measured
    that oracle surviving at -2, -1, +2, +3 and +4, so a control moving the read
    by a single byte would be graded against a value oracle that already
    tolerates it - the weaker choice, and the one that would let this test read
    as evidence while demonstrating nothing about the extent question. At +4 the
    in-place read leaves the int32 entirely and lands on the following tag's
    name-length prefix, which is where the refutation found the displaced tree
    scoring BETTER than the correct one.

    THE SELF-CHECK RUNS FIRST AND IS ASSERTED. A rebind that silently failed to
    install would leave this test measuring the shipped tree and reporting the
    mutant's verdict, which is the exact false-green this whole module exists to
    close one layer up. Both halves are checked on a hand-authored pattern that
    no save contributed: the int32 read moved, and a non-int32 spec did not.

    SAME STATED LIMIT AS THE TEST ABOVE. This forces a DISPLACEMENT, so it
    demonstrates the control fires on a read taken from the wrong place. It
    demonstrates nothing about a decoder that reads no place at all, which is
    CS-455.
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
    assert sweep.mismatches > 0, (
        f"reading every int32 {_ANCHOR_DISPLACEMENT} bytes past its declared start "
        f"produced {sweep.mismatches} disagreements over {sweep.fixed_width_tags} "
        "fixed-width tags. The anchor cannot see a value read from outside its own "
        "extent, so the zero it reports on the shipped tree means nothing"
    )


# ---------------------------------------------------------------------------
# The size-field census
# ---------------------------------------------------------------------------


def test_the_declared_size_field_is_read_in_exactly_one_of_its_twenty_four_byte_orders() -> None:
    """The tag's DECLARED SIZE, censused over the whole permutation group.

    Each payload is walked once per ordering of the size field's four stored
    bytes, and each ordering is graded by how many payloads still reach their
    terminator. A size read in the wrong order desynchronises the walk, so the
    ordering the format actually uses is the one that reaches most - and the
    assertion is a STRICT argmax rather than a threshold, because a threshold
    sitting at an observed number goes red on a correct grammar as soon as the
    library grows, which is CS-432.

    THE HONEST LIMIT, AND THIS TEST DOES NOT CROSS IT. What is censused here is
    the DECLARED SIZE FIELD, read by ``objects._read_tag_header``. That is a
    DIFFERENT FIELD READ BY A DIFFERENT READER than the property value, which
    ``objects._decode_fixed_width`` reads. So this licenses NO statement about
    the byte order of a property VALUE. Getting from one to the other needs the
    premise that the format uses a single byte order for every int32 field it
    stores, and that premise is UNMEASURED here - it is not implied by anything
    below, and it is not asserted anywhere in this module.

    THE RESTORATION IS ASSERTED BESIDE THE ARGMAX. The permutations are applied
    to a writable copy in place and put back after each tag; a copy that came
    back changed would mean later orderings were graded against a body the
    earlier ones had corrupted, and the ranking would be measuring damage.
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

    identity = sweep.reach[_IDENTITY]
    assert identity > 0, (
        "the as-stored ordering reached no terminator at all, so the ranking "
        "below is over an empty measurement"
    )
    beaten = {perm: hits for perm, hits in sweep.reach.items() if perm != _IDENTITY}
    runner_up = max(beaten.values())
    assert identity > runner_up, (
        f"the as-stored ordering reached {identity} payloads and some other "
        f"ordering of the same four bytes reached {runner_up}. The size field is "
        "then not discriminated by reach, and a walk that resynchronises under a "
        "reordered length field is not reading that field the way it believes"
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

    STATED LIMIT. The derivation grades the ORACLES, not the format. A candidate
    surviving here is one the two oracles do not rule out; it is not a claim
    that the format could plausibly use it. Ruling the survivors down to one
    needs evidence these two oracles do not contain.
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

    Two shapes count: a bare ``pass``, and a bare expression that is a string
    or an ellipsis - the second is what a docstring becomes once it is the only
    thing left, and what a stubbed body is usually written as.

    Args:
        statement: One statement from a function body.

    Returns:
        True when the statement performs no check.
    """
    if isinstance(statement, _INERT):
        return True
    return isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Constant)


def _hollow_tests(tree: ast.Module) -> list[str]:
    """Every test in a module whose body performs no check at all.

    THE SHAPE ``test_properties._gutted_tests`` STATES IT DOES NOT COVER. That
    guard reports an early terminator with dead statements after it, and its own
    docstring records that a body emptied to ``pass`` or to a docstring leaves
    no unreachable statement and goes undetected. This one reports exactly that
    remainder, and the consumer below runs both, so the two shapes are covered
    by two named checks rather than by one that claims both.

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
        "docstring or to pass passes for the same reason an empty one does, and "
        "leaves the name in the suite listing where a reader still counts it"
    )
    # The sibling shape, run here so this module is covered by both rather than
    # by whichever one its author happened to think of.
    assert not test_properties._gutted_tests(tree), (  # noqa: SLF001
        f"these tests are cut short and everything after the cut is dead: "
        f"{test_properties._gutted_tests(tree)}"  # noqa: SLF001
    )


def test_no_test_in_this_module_is_emptied_to_a_docstring_or_a_pass() -> None:
    """CS-433, widened to the shape the sibling guard states it misses."""
    _assert_no_test_is_hollow(Path(__file__))


def test_the_emptiness_guard_catches_a_spliced_hollow_body(tmp_path: Path) -> None:
    """THE GUARD'S POWER, forced rather than asserted about.

    A guard returning an empty list on everything would pass on every module and
    read exactly like this one. Both emptied shapes are spliced onto a COPY in
    ``tmp_path``, so nothing tracked is mutated: one body emptied to a docstring
    and one emptied to ``pass``. The unspliced source is then re-graded as a
    positive control, so the red above is the splice rather than a guard that
    rejects whatever it is handed.
    """
    source = Path(__file__).read_text(encoding="utf-8")
    for label, body in (
        ("docstring", '    """A test emptied to a docstring."""\n'),
        ("pass", '    """A test emptied to a pass."""\n    pass\n'),
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
