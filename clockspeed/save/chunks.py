"""The compressed chunk framing: read one frame, walk them all, inflate the body.

This module takes ``bytes`` and an offset. It imports no sibling module in
``clockspeed.save`` and reads no file, which is what lets it be written and
tested independently of the header parser and what makes ADR 0007 Decision 6 -
``workdir.py`` is the only writer in this package - mechanically checkable here.

THE FRAMING IS VERSION DEPENDENT, AND THE VARIANT IS DETECTED FROM THE MARKER
-----------------------------------------------------------------------------
``docs/adr/0007`` and ``BOOTSTRAP.md`` section 3.1 own the measurement. Both
variants open with the same magic and declare the same 131072-byte maximum
chunk size, and then they diverge:

- **Marker 0x22222222** (measured on header versions 13 and 14): an int8
  compression algorithm byte follows the maximum chunk size, so the duplicated
  size block starts at magic+17 and the zlib stream at magic+49.
- **Marker 0x00000000** (measured on header version 10): there is **no
  algorithm byte at all**. The size block starts at magic+16 and the stream at
  magic+48.

The positive evidence that header 10 really has no such byte, rather than one
this project failed to notice: the byte at magic+16 takes the values 2, 2 and 3
across the three measured header-10 saves. It VARIES, which is what the low
byte of a compressed size does and what a fixed algorithm constant does not.

**The variant is selected by the marker word and never by a version field.**
ADR 0007 Decision item 3 records why: whether the framing keys on the header
version, the save version or the build changelist is UNDETERMINED, because all
three predict it perfectly across the local corpus and no available file
separates them. Marker detection is immune to which one is right, which is
exactly why it is the design. When a caller supplies ``header_version`` it is
used as a CROSS-CHECK, and a disagreement produces a warning rather than an
exception - raising would assert that the header version is the key, which is
the claim the ADR refuses to make.

THREE THINGS THIS MODULE REFUSES TO DO
--------------------------------------
1. **Read one chunk and stop.** Real saves split the body across many chunks of
   131072 decompressed bytes each, 11 to 138 across the measured library. A
   walker that reads the first chunk passes every single-chunk fixture and then
   silently reports a truncated world on every real save. :func:`iter_frames`
   walks to a clean end of file and :func:`decompress_body` concatenates.

2. **Trust one copy of a size.** The compressed and uncompressed sizes are each
   written TWICE from independent bytes. That duplication is the format's own
   checksum and it is free; a parser reading the first pair and skipping the
   second throws away a corruption detector that nothing else in the frame
   provides. A disagreement raises.

3. **Allocate before bounding.** A save is untrusted binary input. Every
   declared size is validated against a stated ceiling AND against the
   remaining buffer BEFORE any allocation and before any zlib call.
   :func:`read_frame` performs the whole validation and never touches
   :func:`_inflate`, so a budget refusal is structurally incapable of following
   an allocation rather than merely ordered ahead of one.

WHAT THIS MODULE DELIBERATELY DOES NOT KNOW
-------------------------------------------
Header versions 13 and 14 open the DECOMPRESSED body with an int64 length and
header version 10 does not. That prefix belongs to the body, not to the
framing, so :attr:`DecompressedBody.payload` carries it verbatim and this
module never interprets it. Two consequences, both intended: the walk is
correct without knowing the header version at all, and a truncation confined to
the body - one that leaves the frame well formed and the stream inflating
cleanly - is invisible here and is the record walker's to detect.

THE ERROR TAXONOMY IS A PRIVACY CONTROL, NOT A STYLE
-----------------------------------------------------
Non-negotiable 12: a save body carries the world's contents, so an exception
message is an echo path. Every error raised here may carry only a field name, a
byte offset, an expected/actual length or count, a version scalar and a FIXED
reason string drawn from the ``REASON_*`` constants below. Never raw bytes,
never a decoded string, never a hex preview, never a path. A message reading
"expected 0x9E2A83C1, got 0x11223344" would be echoing four bytes of the file,
and the same habit applied one layer up echoes an operator's world name.
"""

from __future__ import annotations

import struct
import zlib
from collections.abc import Iterator, Sized
from dataclasses import dataclass
from typing import Final

__all__ = [
    "ALGORITHM_OFFSET",
    "ALGORITHM_ZLIB",
    "CHUNK_MAGIC",
    "FIELD_NAMES",
    "FRAME_SIZE_WITHOUT_ALGORITHM",
    "FRAME_SIZE_WITH_ALGORITHM",
    "FRAMING_WITHOUT_ALGORITHM",
    "FRAMING_WITH_ALGORITHM",
    "MARKER_WITHOUT_ALGORITHM",
    "MARKER_WITH_ALGORITHM",
    "MAX_CHUNKS",
    "MAX_CHUNK_SIZE",
    "MAX_DECLARED_CHUNK_BYTES",
    "MAX_TOTAL_BODY_BYTES",
    "SIZES_OFFSET_WITHOUT_ALGORITHM",
    "SIZES_OFFSET_WITH_ALGORITHM",
    "WARN_MARKER_VERSION_DISAGREEMENT",
    "WARN_UNMEASURED_HEADER_VERSION",
    "ChunkBudgetExceededError",
    "ChunkDecompressError",
    "ChunkError",
    "ChunkFrame",
    "ChunkFramingError",
    "ChunkTruncatedError",
    "ChunkWarning",
    "DecompressedBody",
    "decompress_body",
    "iter_frames",
    "read_frame",
]

# ---------------------------------------------------------------------------
# The measured framing constants
#
# BOOTSTRAP.md section 3.1 and docs/adr/0007 own these measurements. They are
# transcribed here rather than imported because this package must not depend on
# the test corpus; tests/save/test_chunks.py cross-checks the two
# transcriptions against each other, which is the only evidence that neither
# slice mistyped the table.
# ---------------------------------------------------------------------------

#: Opens every chunk frame, on every measured header version.
CHUNK_MAGIC: Final = 0x9E2A83C1

#: Measured on header versions 13 and 14. Selects the variant carrying an
#: explicit int8 compression algorithm byte.
MARKER_WITH_ALGORITHM: Final = 0x22222222

#: Measured on header version 10. Selects the variant with NO algorithm byte.
MARKER_WITHOUT_ALGORITHM: Final = 0x00000000

#: The decompressed bytes each chunk carries, declared by the frame itself and
#: measured identical on every save in the local library.
MAX_CHUNK_SIZE: Final = 131072

#: The only compression algorithm measured in the field.
ALGORITHM_ZLIB: Final = 3

#: Names for the two variants, matching the corpus so a cross-check is possible.
FRAMING_WITH_ALGORITHM: Final = "marker22-algo"
FRAMING_WITHOUT_ALGORITHM: Final = "zero-marker-noalgo"

#: Bytes from the magic to the first byte of the zlib stream.
#: With the algorithm byte:  4 + 4 + 8 + 1 + 8 * 4 = 49.
#: Without it:               4 + 4 + 8 +     8 * 4 = 48.
FRAME_SIZE_WITH_ALGORITHM: Final = 49
FRAME_SIZE_WITHOUT_ALGORITHM: Final = 48

#: Offset from the magic to the duplicated size block, per variant.
SIZES_OFFSET_WITH_ALGORITHM: Final = 17
SIZES_OFFSET_WITHOUT_ALGORITHM: Final = 16

#: Offset from the magic to the algorithm byte, on the variant that has one.
#: Numerically equal to :data:`SIZES_OFFSET_WITHOUT_ALGORITHM`, and that is the
#: whole point: the byte one variant reads as the algorithm is the byte the
#: other reads as the low byte of the compressed size.
ALGORITHM_OFFSET: Final = 16

#: Offset from the magic to the int64 maximum chunk size.
_MAX_CHUNK_SIZE_OFFSET: Final = 8

#: Offset from the magic to the marker word.
_MARKER_OFFSET: Final = 4

_INT32_WIDTH: Final = 4
_INT64_WIDTH: Final = 8

#: The four int64s of the duplicated size block, in the order the corpus builds
#: them: compressed, uncompressed, compressed, uncompressed.
_SIZE_BLOCK_FORMAT: Final = "<qqqq"
_SIZE_BLOCK_WIDTH: Final = 32

# ---------------------------------------------------------------------------
# Stated resource ceilings
#
# Every one of these is a REFUSAL BOUND applied to a DECLARED value before any
# allocation. They are deliberately generous against the measurement and
# deliberately finite: an unbounded declared length read from an untrusted file
# is the whole attack.
# ---------------------------------------------------------------------------

#: Ceiling on the frame's own declared maximum chunk size. Sixteen times the
#: measured 131072. Without it a corrupt file could raise its own ceiling and
#: walk straight past the per-chunk check below, which is stated against the
#: declared maximum rather than against a constant.
MAX_DECLARED_CHUNK_BYTES: Final = 1 << 21

#: Ceiling on the whole concatenated body. The largest measured save is 138
#: chunks, roughly 18 MB decompressed, so this is about fifty times the
#: observed maximum. It bounds a file that declares many individually legal
#: chunks, which no per-chunk check can catch.
MAX_TOTAL_BODY_BYTES: Final = 1 << 30

#: Ceiling on the chunk count. Termination is already guaranteed - a frame must
#: declare a strictly positive compressed size, so the walk offset strictly
#: increases inside a finite buffer - and this is the stated resource bound on
#: top of that guarantee.
MAX_CHUNKS: Final = 1 << 16

# ---------------------------------------------------------------------------
# Warning codes and their fixed detail lines
# ---------------------------------------------------------------------------

#: The marker selected one variant and the supplied header version was measured
#: with the other. Advisory: see the module docstring on the undetermined key.
WARN_MARKER_VERSION_DISAGREEMENT: Final = "marker-version-disagreement"

#: The supplied header version is outside the measured set, so no cross-check
#: was possible. ADR 0007 Decision 3: an unknown combination is flagged, never
#: guessed. The walk itself is unaffected - it follows the marker.
WARN_UNMEASURED_HEADER_VERSION: Final = "unmeasured-header-version"

_WARNING_DETAIL: Final[dict[str, str]] = {
    WARN_MARKER_VERSION_DISAGREEMENT: (
        "the marker selects a framing the supplied header version was not measured with; "
        "the marker wins and the walk is unaffected"
    ),
    WARN_UNMEASURED_HEADER_VERSION: (
        "the supplied header version is outside the measured set, so the framing "
        "cross-check was skipped; the marker still selects the variant"
    ),
}

#: The measured pairing of header version to framing variant. Used ONLY to
#: cross-check, never to select. ``BOOTSTRAP.md`` section 3.1 owns the table.
_FRAMING_BY_HEADER_VERSION: Final[dict[int, str]] = {
    10: FRAMING_WITHOUT_ALGORITHM,
    13: FRAMING_WITH_ALGORITHM,
    14: FRAMING_WITH_ALGORITHM,
}

# ---------------------------------------------------------------------------
# Fixed reason strings
#
# Every raised message is built from one of these. A test collects them from
# this module and asserts that each raised reason is a member, which proves
# mechanically that no decoded file content can reach an exception message.
# ---------------------------------------------------------------------------

REASON_BAD_MAGIC: Final = "does not match the measured chunk magic"
REASON_BAD_MARKER: Final = "is neither measured framing marker, so no variant is selected"
REASON_SIZE_PAIR_DISAGREES: Final = "disagrees with its own duplicate copy"
REASON_NEGATIVE_SIZE: Final = "declares a length below zero, which no frame can carry"
REASON_EMPTY_COMPRESSED: Final = "declares no compressed bytes, so the walk could not advance"
REASON_ABOVE_DECLARED_MAXIMUM: Final = "exceeds the maximum chunk size the frame itself declares"
REASON_ABOVE_CEILING: Final = "exceeds the stated ceiling for this field"
REASON_SHORT_BUFFER: Final = "extends past the end of the supplied buffer"
REASON_NO_CHUNK_AT_OFFSET: Final = "there are no bytes to read a chunk frame from"
REASON_INFLATE_FAILED: Final = "could not be inflated as a zlib stream"
REASON_INFLATE_SHORT: Final = "inflated to a different length than the frame declared"
REASON_UNKNOWN_ALGORITHM: Final = "names a compression algorithm this reader cannot inflate"


#: Every field name this module may report. THE ONE PARAMETER OF THE
#: TAXONOMY THAT IS TEXT, so it is the only one that could carry a decoded
#: value into a message, and :func:`_checked_field` is what stops it.
#:
#: DERIVED FROM THIS MODULE'S OWN RAISE SITES, not transcribed from a report,
#: and ``tests/save/test_chunks.py`` asserts the two agree in BOTH directions.
FIELD_NAMES: Final = frozenset(
    {
        "algorithm",
        "body_size",
        "chunk_count",
        "compressed_size",
        "frame",
        "magic",
        "marker",
        "max_chunk_size",
        "payload",
        "uncompressed_size",
    }
)


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


def _checked_field(name: str) -> str:
    """Confirm a field name is in the closed vocabulary before it enters a message.

    The static half of the taxonomy gate proves the parameter is a ``str``.
    This is the runtime half: it proves the ``str`` was drawn from
    :data:`FIELD_NAMES`, so the one parameter allowed to be text cannot smuggle
    a decoded value into an error message.

    Mirrors ``clockspeed/save/objects.py``. Before CS-852 this module stated
    the guarantee in the :class:`ChunkError` docstring and enforced it with
    nothing, so a caller could hand it any string at all.

    Args:
        name: The candidate field name.

    Returns:
        ``name``, unchanged.

    Raises:
        ValueError: The name is not in :data:`FIELD_NAMES`. The message states
            the count of known names rather than echoing the rejected value,
            because the rejected value is exactly the thing under suspicion.
    """
    if name not in FIELD_NAMES:
        raise ValueError(
            f"field name is not one of the {len(FIELD_NAMES)} names this module may report"
        )
    return name


class ChunkError(Exception):
    """Base class for every refusal this module raises.

    A plain :class:`Exception` rather than a :class:`ValueError`, matching
    ``clockspeed/data/docs_extract.py`` - the other parser layer in this
    project. A caller wrapping a broad input handler around a save read should
    have to name this layer to swallow it.

    THE ATTRIBUTE SET IS A PRIVACY CONTROL. Non-negotiable 12 makes an
    exception an echo path for a personal-data-bearing artifact, so an instance
    carries only the five channels below plus the fixed reason. A test pins the
    set with ``vars(exc)`` rather than trusting review.

    Attributes:
        reason: One of the module's ``REASON_*`` constants. Never built from
            file content.
        field: The name of the frame field at fault, from :data:`FIELD_NAMES`.
            A name from this module's own vocabulary, never a value read from
            the file - enforced by :func:`_checked_field` rather than stated.
        offset: The byte offset the fault was found at.
        expected: An expected length or count, or None.
        actual: The declared or observed length or count, or None.
        version: A version scalar, or None.
    """

    def __init__(
        self,
        reason: str,
        *,
        field: str,
        offset: int,
        expected: int | None = None,
        actual: int | None = None,
        version: int | None = None,
    ) -> None:
        """Render a message from the taxonomy fields and nothing else.

        Args:
            reason: One of the ``REASON_*`` constants.
            field: The frame field at fault.
            offset: The byte offset.
            expected: An expected length or count.
            actual: An observed or declared length or count.
            version: A version scalar.
        """
        checked = _checked_field(field)
        super().__init__(_render(reason, checked, offset, expected, actual, version))
        self.reason = reason
        self.field = checked
        self.offset = offset
        self.expected = expected
        self.actual = actual
        self.version = version


class ChunkFramingError(ChunkError):
    """The bytes at this offset are not a frame this reader recognizes.

    Covers a wrong magic, a marker that is neither measured value, a size that
    disagrees with its own duplicate copy, and a size that is structurally
    impossible - negative, or a compressed length of zero that would leave the
    walk unable to advance.
    """


class ChunkTruncatedError(ChunkError):
    """The frame or its payload extends past the end of the supplied buffer.

    Distinct from :class:`ChunkFramingError` on purpose: the bytes present are
    consistent as far as they go, and what is wrong is that there are not
    enough of them. A caller can retry a truncated read; it cannot retry a
    malformed one.
    """


class ChunkDecompressError(ChunkError):
    """The frame was well formed and the payload could not be inflated.

    Also raised when the frame names an algorithm this reader has never
    measured. That case is NOT flag-and-skip under non-negotiable 7: skipping
    would leave no body to return at all, so it is refused on the field where
    the message can name the cause.

    A :class:`zlib.error` never escapes this module. Letting it through would
    make every caller import zlib to handle a save problem and would surface
    the library's own message, which is not one of this module's fixed reasons.
    """


class ChunkBudgetExceededError(ChunkError):
    """A declared size or count exceeds a stated ceiling.

    Always raised on the DECLARED value, before any allocation and before any
    zlib call. ``tests/save/test_chunks.py`` proves the ordering with a
    recording spy on the inflate seam plus a positive control that fires the
    same spy on a healthy save.
    """


def _render(
    reason: str,
    field: str,
    offset: int,
    expected: int | None,
    actual: int | None,
    version: int | None,
) -> str:
    """Build the message from taxonomy fields only.

    Decimal throughout, deliberately. A hex rendering of an observed value is
    the exact shape non-negotiable 12 forbids, and a habit that reads as
    helpful here becomes a disclosure one layer up.

    Args:
        reason: One of the ``REASON_*`` constants.
        field: The frame field at fault.
        offset: The byte offset.
        expected: An expected length or count.
        actual: An observed or declared length or count.
        version: A version scalar.

    Returns:
        The rendered message.
    """
    parts = [f"chunk field {field} at byte {offset} {reason}"]
    if expected is not None:
        parts.append(f"expected {expected}")
    if actual is not None:
        parts.append(f"got {actual}")
    if version is not None:
        parts.append(f"header version {version}")
    return "; ".join(parts)


# ---------------------------------------------------------------------------
# The models
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ChunkFrame:
    """One chunk's frame, read but not yet inflated.

    Attributes:
        magic: Always :data:`CHUNK_MAGIC` on a frame that read successfully.
        marker: The word the variant was selected from.
        max_chunk_size: The decompressed ceiling the frame declares. Measured
            at 131072 on every save in the local library.
        algorithm: The int8 algorithm byte, or None on the variant that carries
            no such byte. None rather than 0, because reporting 0 would claim a
            field the file does not contain.
        compressed_size: The declared compressed length, agreed by both copies.
        uncompressed_size: The declared decompressed length, agreed by both
            copies.
        header_size: 49 with the algorithm byte, 48 without it.
        payload_offset: Absolute offset of the first byte of the zlib stream.
        framing: :data:`FRAMING_WITH_ALGORITHM` or
            :data:`FRAMING_WITHOUT_ALGORITHM`, selected from the marker.
    """

    magic: int
    marker: int
    max_chunk_size: int
    algorithm: int | None
    compressed_size: int
    uncompressed_size: int
    header_size: int
    payload_offset: int
    framing: str

    @property
    def frame_offset(self) -> int:
        """Absolute offset of the magic that opened this frame.

        Returns:
            The offset.
        """
        return self.payload_offset - self.header_size

    @property
    def next_offset(self) -> int:
        """Absolute offset the following frame starts at.

        Returns:
            The offset one past this frame's payload.
        """
        return self.payload_offset + self.compressed_size


@dataclass(frozen=True)
class ChunkWarning:
    """Something worth reporting that is not worth failing over.

    Aggregated by code rather than emitted per chunk: a 138-chunk save whose
    header version disagrees with its marker has one problem, not 138.

    Attributes:
        code: One of the module's ``WARN_*`` constants.
        detail: A fixed line, keyed by code. Never built from file content.
        offset: The byte offset of the FIRST occurrence.
        version: The header version the caller supplied, or None.
        count: How many chunks this warning aggregates.
    """

    code: str
    detail: str
    offset: int
    version: int | None = None
    count: int = 1


def _rendered_length(value: object) -> str:
    """A length for a value that has one, and a placeholder for one that does not.

    A ``__repr__`` THAT RAISES FAILS EXACTLY WHEN SOMETHING HAS ALREADY GONE
    WRONG, which is the one moment it exists for. The first CS-852 draft called
    ``len`` straight onto the field and an adversary constructed the type with
    ``payload=None``, turning the safe rendering into a ``TypeError`` where the
    GENERATED repr it replaced had been total.

    ``payload`` ITSELF DOES NOT USE THIS HELPER, and the reason is a second
    guard rather than a preference. The phase-4 absence gate declares
    ``retained-bytes-are-never-rendered`` over this module and derives its
    needles from the retained attributes; it excludes ``len(...)`` as a count
    that cannot disclose a byte, but it cannot see through a named helper, so
    routing the buffer here read as a rendering. ``payload`` is therefore
    counted by a bare ``len`` under a ``TypeError`` guard, which satisfies both
    checks at once.

    Args:
        value: The field value, whatever a caller actually put there.

    Returns:
        The length, or ``?`` for a value that cannot report one.
    """
    return str(len(value)) if isinstance(value, Sized) else "?"


@dataclass(frozen=True, repr=False)
class DecompressedBody:
    """The concatenated body of every chunk, and what was noticed on the way.

    Attributes:
        payload: Every chunk's decompressed bytes, in order, concatenated. On
            header versions 13 and 14 this OPENS with the body's own int64
            length prefix, carried verbatim: that field belongs to the body
            layer and this module never interprets it.
        chunk_count: How many frames were walked. Always at least one - a walk
            that finds no frame raises rather than returning an empty body,
            because an empty body is indistinguishable from a save that
            legitimately holds nothing.
        warnings: Aggregated advisories, empty when nothing was noticed.
    """

    payload: bytes
    chunk_count: int
    warnings: tuple[ChunkWarning, ...] = ()

    def __repr__(self) -> str:
        """Render the frame count and the payload's SIZE, never its bytes.

        ``payload`` is the concatenated body of a real save and carries type
        paths and instance names. A dataclass with no ``__repr__`` generates one
        that renders every field, so this type disclosed the body wholesale
        until CS-852 - and non-negotiable 12 counts a debug dump, a log line and
        a failure report as echo paths, which makes the safe rendering the one
        that has to be the DEFAULT rather than an opt-in.

        Returns:
            The safe rendering.
        """
        try:
            payload_bytes: object = len(self.payload)
        except TypeError:
            payload_bytes = "?"
        return (
            f"{type(self).__name__}(payload_bytes={payload_bytes}, "
            f"chunk_count={self.chunk_count}, warnings={_rendered_length(self.warnings)})"
        )


# ---------------------------------------------------------------------------
# Frame reading
# ---------------------------------------------------------------------------


def _select_variant(marker: int, offset: int) -> tuple[str, int, int]:
    """Choose the framing variant from the marker word alone.

    This is the design point of the whole module. See the module docstring and
    ADR 0007 Decision item 3: the key the framing actually follows is
    undetermined, and detection from the marker is immune to which candidate is
    right.

    Args:
        marker: The word read at magic+4.
        offset: The frame's own offset, for the error.

    Returns:
        The framing name, the frame header size and the size-block offset.

    Raises:
        ChunkFramingError: The marker is neither measured value.
    """
    if marker == MARKER_WITH_ALGORITHM:
        return (
            FRAMING_WITH_ALGORITHM,
            FRAME_SIZE_WITH_ALGORITHM,
            SIZES_OFFSET_WITH_ALGORITHM,
        )
    if marker == MARKER_WITHOUT_ALGORITHM:
        return (
            FRAMING_WITHOUT_ALGORITHM,
            FRAME_SIZE_WITHOUT_ALGORITHM,
            SIZES_OFFSET_WITHOUT_ALGORITHM,
        )
    raise ChunkFramingError(
        REASON_BAD_MARKER,
        field="marker",
        offset=offset + _MARKER_OFFSET,
    )


def _read_size_pair(data: bytes, at: int) -> tuple[int, int]:
    """Read the duplicated size block and enforce its own checksum.

    The compressed and uncompressed sizes are each written twice from
    independent bytes. Comparing the copies is free corruption detection that
    nothing else in the frame provides, and a parser that reads only the first
    copy cannot notice the damage at all.

    Structural validation happens here too, before either value is used as a
    length: a negative size would be read by a slice expression as "count from
    the end", and a compressed size of zero would leave the walk unable to
    advance.

    Args:
        data: The whole buffer.
        at: Absolute offset of the size block.

    Returns:
        The agreed compressed and uncompressed sizes.

    Raises:
        ChunkFramingError: The copies disagree, or a size is structurally
            impossible.
    """
    first_compressed, first_uncompressed, second_compressed, second_uncompressed = (
        struct.unpack_from(_SIZE_BLOCK_FORMAT, data, at)
    )

    if first_compressed != second_compressed:
        raise ChunkFramingError(
            REASON_SIZE_PAIR_DISAGREES,
            field="compressed_size",
            offset=at,
            expected=first_compressed,
            actual=second_compressed,
        )
    if first_uncompressed != second_uncompressed:
        raise ChunkFramingError(
            REASON_SIZE_PAIR_DISAGREES,
            field="uncompressed_size",
            offset=at + _INT64_WIDTH,
            expected=first_uncompressed,
            actual=second_uncompressed,
        )

    if first_compressed < 0:
        raise ChunkFramingError(
            REASON_NEGATIVE_SIZE, field="compressed_size", offset=at, actual=first_compressed
        )
    if first_compressed == 0:
        raise ChunkFramingError(
            REASON_EMPTY_COMPRESSED, field="compressed_size", offset=at, actual=first_compressed
        )
    if first_uncompressed < 0:
        raise ChunkFramingError(
            REASON_NEGATIVE_SIZE,
            field="uncompressed_size",
            offset=at + _INT64_WIDTH,
            actual=first_uncompressed,
        )

    return first_compressed, first_uncompressed


def read_frame(data: bytes, offset: int) -> ChunkFrame:
    """Read and fully validate one chunk frame, allocating nothing.

    NOTHING IS ALLOCATED AND ZLIB IS NEVER CALLED HERE. Every declared size is
    bounded against the frame's own maximum, against this module's stated
    ceilings and against the remaining buffer before this function returns, so
    a budget refusal cannot follow an allocation - there is no allocation for
    it to follow. :func:`decompress_body` is the only caller that inflates, and
    it does so only from a frame this function has already accepted.

    Args:
        data: The whole buffer. Typically a whole ``.sav``.
        offset: Absolute offset of the chunk magic.

    Returns:
        The validated frame.

    Raises:
        ValueError: The offset is negative, which is a caller bug rather than
            file damage and so is deliberately not a :class:`ChunkError`.
        ChunkTruncatedError: The frame or its payload runs past the buffer.
        ChunkFramingError: The magic, the marker or a size is malformed.
        ChunkBudgetExceededError: A declared size exceeds a stated ceiling.
    """
    if offset < 0:
        raise ValueError(f"offset must not be negative, got {offset}")

    available = max(len(data) - offset, 0)
    if available < _INT32_WIDTH:
        raise ChunkTruncatedError(
            REASON_NO_CHUNK_AT_OFFSET,
            field="magic",
            offset=offset,
            expected=_INT32_WIDTH,
            actual=available,
        )

    (magic,) = struct.unpack_from("<I", data, offset)
    if magic != CHUNK_MAGIC:
        raise ChunkFramingError(REASON_BAD_MAGIC, field="magic", offset=offset)

    if available < _MARKER_OFFSET + _INT32_WIDTH:
        raise ChunkTruncatedError(
            REASON_SHORT_BUFFER,
            field="marker",
            offset=offset + _MARKER_OFFSET,
            expected=_MARKER_OFFSET + _INT32_WIDTH,
            actual=available,
        )
    (marker,) = struct.unpack_from("<I", data, offset + _MARKER_OFFSET)
    framing, header_size, sizes_offset = _select_variant(marker, offset)

    if available < header_size:
        raise ChunkTruncatedError(
            REASON_SHORT_BUFFER,
            field="frame",
            offset=offset,
            expected=header_size,
            actual=available,
        )

    (max_chunk_size,) = struct.unpack_from("<q", data, offset + _MAX_CHUNK_SIZE_OFFSET)
    if max_chunk_size <= 0:
        raise ChunkFramingError(
            REASON_NEGATIVE_SIZE,
            field="max_chunk_size",
            offset=offset + _MAX_CHUNK_SIZE_OFFSET,
            actual=max_chunk_size,
        )
    if max_chunk_size > MAX_DECLARED_CHUNK_BYTES:
        raise ChunkBudgetExceededError(
            REASON_ABOVE_CEILING,
            field="max_chunk_size",
            offset=offset + _MAX_CHUNK_SIZE_OFFSET,
            expected=MAX_DECLARED_CHUNK_BYTES,
            actual=max_chunk_size,
        )

    algorithm = data[offset + ALGORITHM_OFFSET] if framing == FRAMING_WITH_ALGORITHM else None

    compressed_size, uncompressed_size = _read_size_pair(data, offset + sizes_offset)

    # THE BOUND, ON THE DECLARED VALUE, BEFORE ANY ALLOCATION. The frame states
    # its own decompressed ceiling and every measured chunk honours it, so the
    # tightest correct check is against that field - itself already bounded
    # above, so a corrupt file cannot raise its own ceiling to escape.
    if uncompressed_size > max_chunk_size:
        raise ChunkBudgetExceededError(
            REASON_ABOVE_DECLARED_MAXIMUM,
            field="uncompressed_size",
            offset=offset + sizes_offset + _INT64_WIDTH,
            expected=max_chunk_size,
            actual=uncompressed_size,
        )

    payload_offset = offset + header_size
    remaining = max(len(data) - payload_offset, 0)
    if compressed_size > remaining:
        raise ChunkTruncatedError(
            REASON_SHORT_BUFFER,
            field="compressed_size",
            offset=payload_offset,
            expected=compressed_size,
            actual=remaining,
        )

    return ChunkFrame(
        magic=magic,
        marker=marker,
        max_chunk_size=max_chunk_size,
        algorithm=algorithm,
        compressed_size=compressed_size,
        uncompressed_size=uncompressed_size,
        header_size=header_size,
        payload_offset=payload_offset,
        framing=framing,
    )


def iter_frames(data: bytes, offset: int) -> Iterator[ChunkFrame]:
    """Walk every chunk frame from ``offset`` to a clean end of file.

    THE WALK CONTINUES. Real saves carry 11 to 138 chunks across the measured
    library, and a walker that stops after the first passes every single-chunk
    fixture while silently reporting a truncated world on every real file.

    Termination is guaranteed by :func:`read_frame`, which refuses a compressed
    size of zero: each frame therefore advances the offset by at least one byte
    inside a finite buffer. :data:`MAX_CHUNKS` is the stated resource ceiling
    on top of that guarantee, not the thing that makes the loop finite.

    Args:
        data: The whole buffer.
        offset: Absolute offset of the first chunk magic.

    Yields:
        Each frame, in file order.

    Raises:
        ValueError: The offset is negative.
        ChunkTruncatedError: There is no frame at ``offset`` at all.
        ChunkBudgetExceededError: More than :data:`MAX_CHUNKS` frames.
    """
    if offset < 0:
        raise ValueError(f"offset must not be negative, got {offset}")
    if offset >= len(data):
        raise ChunkTruncatedError(
            REASON_NO_CHUNK_AT_OFFSET,
            field="magic",
            offset=offset,
            expected=_INT32_WIDTH,
            actual=max(len(data) - offset, 0),
        )

    at = offset
    seen = 0
    while at < len(data):
        frame = read_frame(data, at)
        seen += 1
        if seen > MAX_CHUNKS:
            raise ChunkBudgetExceededError(
                REASON_ABOVE_CEILING,
                field="chunk_count",
                offset=at,
                expected=MAX_CHUNKS,
                actual=seen,
            )
        yield frame
        at = frame.next_offset


def _inflate(stream: bytes, expected_size: int) -> bytes:
    """Inflate one chunk's zlib stream.

    THE ALLOCATION SEAM, isolated for exactly one reason: it is the thing a
    declared-size bomb would make enormous, and ``tests/save/test_chunks.py``
    replaces it with a RECORDING double to prove that a refusal happened before
    any call reached here. A recorder rather than a raiser, because a raising
    double proves nothing under fail-soft code - the code under test could
    swallow the raise and refuse by another route, passing the test for the
    wrong reason.

    ``expected_size`` is passed as the initial output buffer, which is safe
    only because :func:`read_frame` has already bounded it against the frame's
    declared maximum and against this module's ceiling.

    Args:
        stream: The compressed bytes, already bounded against the buffer.
        expected_size: The declared decompressed length, already bounded.

    Returns:
        The inflated bytes.
    """
    return zlib.decompress(stream, bufsize=max(expected_size, 1))


def _cross_check(frame: ChunkFrame, header_version: int | None) -> str | None:
    """Compare the marker-selected framing against a supplied header version.

    ADVISORY BY DESIGN. ADR 0007 Decision item 3 records three unrefuted
    candidate keys for the framing variant - header version, save version and
    build changelist - each of which predicts it perfectly on the measured
    corpus. Raising on a disagreement would assert that the header version is
    the key, which is the claim the ADR explicitly refuses to make.

    Args:
        frame: The frame as read from the marker.
        header_version: The caller's cross-check input, or None to skip.

    Returns:
        A ``WARN_*`` code, or None when nothing is worth reporting.
    """
    if header_version is None:
        return None
    expected = _FRAMING_BY_HEADER_VERSION.get(header_version)
    if expected is None:
        return WARN_UNMEASURED_HEADER_VERSION
    if expected != frame.framing:
        return WARN_MARKER_VERSION_DISAGREEMENT
    return None


def decompress_body(
    data: bytes, offset: int, *, header_version: int | None = None
) -> DecompressedBody:
    """Walk every chunk and concatenate the decompressed body.

    The payload is returned VERBATIM, including the int64 body length prefix
    that header versions 13 and 14 carry and header version 10 does not. That
    field belongs to the body layer; interpreting it here would key this module
    to a header version it otherwise never needs to know.

    Args:
        data: The whole buffer.
        offset: Absolute offset of the first chunk magic.
        header_version: Optional cross-check input. Supplying it enables the
            marker-versus-version comparison, which can only ever WARN.

    Returns:
        The concatenated body, the chunk count and any aggregated warnings.

    Raises:
        ValueError: The offset is negative.
        ChunkTruncatedError: A frame or payload runs past the buffer.
        ChunkFramingError: A frame is malformed.
        ChunkDecompressError: A stream would not inflate, inflated to the wrong
            length, or names an algorithm this reader cannot handle.
        ChunkBudgetExceededError: A declared size or the running total exceeds
            a stated ceiling.
    """
    parts: list[bytes] = []
    counts: dict[str, int] = {}
    firsts: dict[str, int] = {}
    chunk_count = 0
    total = 0

    for frame in iter_frames(data, offset):
        chunk_count += 1

        code = _cross_check(frame, header_version)
        if code is not None:
            counts[code] = counts.get(code, 0) + 1
            firsts.setdefault(code, frame.frame_offset)

        if frame.algorithm is not None and frame.algorithm != ALGORITHM_ZLIB:
            raise ChunkDecompressError(
                REASON_UNKNOWN_ALGORITHM,
                field="algorithm",
                offset=frame.frame_offset + ALGORITHM_OFFSET,
                expected=ALGORITHM_ZLIB,
                actual=frame.algorithm,
                version=header_version,
            )

        total += frame.uncompressed_size
        if total > MAX_TOTAL_BODY_BYTES:
            raise ChunkBudgetExceededError(
                REASON_ABOVE_CEILING,
                field="body_size",
                offset=frame.frame_offset,
                expected=MAX_TOTAL_BODY_BYTES,
                actual=total,
            )

        stream = data[frame.payload_offset : frame.next_offset]
        try:
            inflated = _inflate(stream, frame.uncompressed_size)
        except zlib.error:
            # The library's own message is not one of this module's fixed
            # reasons and could quote stream bytes, so the cause is dropped
            # rather than chained.
            raise ChunkDecompressError(
                REASON_INFLATE_FAILED, field="payload", offset=frame.payload_offset
            ) from None

        if len(inflated) != frame.uncompressed_size:
            raise ChunkDecompressError(
                REASON_INFLATE_SHORT,
                field="uncompressed_size",
                offset=frame.payload_offset,
                expected=frame.uncompressed_size,
                actual=len(inflated),
            )
        parts.append(inflated)

    warnings = tuple(
        ChunkWarning(
            code=code,
            detail=_WARNING_DETAIL[code],
            offset=firsts[code],
            version=header_version,
            count=count,
        )
        for code, count in counts.items()
    )
    return DecompressedBody(payload=b"".join(parts), chunk_count=chunk_count, warnings=warnings)
