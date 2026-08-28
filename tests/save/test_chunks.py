"""The chunk framing walker, proven against both measured framing variants.

WHAT THIS MODULE IS GUARDING AGAINST
------------------------------------
Three failure shapes, each of which produces a green suite and a wrong answer.

1. **A single fixed framing.** ``docs/adr/0007`` records the measurement: header
   versions 13 and 14 carry a non-zero marker and an explicit compression
   algorithm byte, header version 10 carries a zero marker and NO algorithm
   byte at all. A parser built from the unqualified claim fails on 3 of the
   operator's 14 saves and looks correct on the other 11. Both variants are
   walked here, from the corpus fixture for each header version.

2. **A walker that reads one chunk and stops.** Every fixture except
   ``SAVE_MULTICHUNK`` is single chunk, so a one-chunk walker passes the whole
   rest of the corpus and then silently reports a truncated world on every real
   save. ``test_the_multichunk_fixture_walks_every_chunk`` is the discriminator
   and its docstring states exactly how it discriminates.

3. **A bound applied after the allocation instead of before it.** A save is
   untrusted binary input. ``declared_chunk_bomb`` declares a terabyte from a
   few hundred bytes, and a parser that preallocates on the declared size dies
   in production rather than in this suite. The ordering is proven with a
   RECORDING spy plus a positive control that fires the same spy on a healthy
   save - a spy that never records anything would pass the bomb test
   vacuously, which is the failure ``CONVENTIONS.md`` records for the raising
   variant.

THE FRAMING IS DETECTED FROM THE MARKER, AND THAT IS A MEASUREMENT
------------------------------------------------------------------
``docs/adr/0007`` Decision item 3: whether the framing keys on the header
version, the save version or the build changelist is UNDETERMINED, because all
three predict it perfectly on the local corpus and no local file separates
them. Detection from the marker word is immune to which one is right.
``test_the_framing_follows_the_marker_and_not_the_header_version`` builds the
combination that no real file carries - header 10 bytes framed with the
marker-22 variant - so a parser keying off the version alone fails there and
only there.

NO REAL SAVE DATA, AND NO ECHO PATH
------------------------------------
Every byte parsed here comes from ``tests/save/synthetic.py``. The exception
taxonomy is asserted mechanically rather than by inspection: non-negotiable 12
makes an exception message an echo path, so
``test_every_raised_error_carries_only_taxonomy_fields`` pins the attribute set
and ``test_no_raised_message_echoes_the_bytes_that_caused_it`` pins the
rendering.
"""

from __future__ import annotations

import ast
import struct
import zlib
from collections.abc import Callable
from pathlib import Path
from typing import Final

import pytest

from clockspeed.save import chunks
from tests.save import synthetic

# ---------------------------------------------------------------------------
# Local constants, so no assertion compares against a bare literal
# ---------------------------------------------------------------------------

_INT64_WIDTH: Final = 8
_ONE_CHUNK: Final = 1
_ALGORITHM_BYTE_WIDTH: Final = 1

#: Offsets inside the duplicated size block, which the corpus builds in the
#: order (compressed, uncompressed, compressed, uncompressed).
_SECOND_COMPRESSED: Final = 16
_SECOND_UNCOMPRESSED: Final = 24

#: The corrupted values the corpus splices in. They are asserted ABSENT from
#: every rendered message, never present, so naming them here is the test and
#: not a leak - they are invented constants in a synthetic fixture.
_CORRUPT_MAGIC_HEX: Final = "11223344"
_CORRUPT_MARKER_HEX: Final = "deadbeef"

#: The union of every attribute an exception in this module is permitted to
#: carry. A byte offset, a field name, an expected/actual length or count, a
#: version scalar and a fixed reason string - nothing else. Never raw bytes,
#: never a decoded string, never a hex preview, never a path.
_ALLOWED_ERROR_ATTRIBUTES: Final = frozenset(
    {"reason", "field", "offset", "expected", "actual", "version"}
)

#: Every sibling module in ``clockspeed.save``. This slice takes bytes plus an
#: offset and imports none of them; that independence is what lets it be
#: written in parallel with the header parser.
_SIBLING_SAVE_MODULES: Final = ("header", "usmap", "workdir", "world")


def _mismatched_framing_blob() -> tuple[bytes, int]:
    """Build header-10 bytes framed with the marker-22 variant.

    This combination occurs in NO real file: the corpus measurement pairs
    header 10 with the zero marker and no algorithm byte. It is buildable only
    because :func:`synthetic.build_save` takes the framing as an independent
    parameter, and it is the one shape that separates "detected from the
    marker" from "assumed from the version".

    Returns:
        The blob and the offset of its first chunk.
    """
    header_kwargs: dict[str, object] = {
        "header_version": synthetic.HEADER_VERSION_10,
        "save_version": 36,
    }
    blob = synthetic.build_save(
        header_kwargs=header_kwargs,
        objects=(),
        framing=synthetic.FRAMING_MARKER22_ALGO,
    )
    header = synthetic.build_header(header_version=synthetic.HEADER_VERSION_10, save_version=36)
    return blob, len(header)


def _recording_inflate(calls: list[int]) -> Callable[[bytes, int], bytes]:
    """Build an inflate double that RECORDS every call and still does the work.

    Recording rather than raising is the point. A raising double proves nothing
    under fail-soft code - the code under test may swallow the raise and reach
    the same refusal by another route, and the test then passes for the wrong
    reason. A recorder that also performs the real inflate leaves behaviour
    unchanged, so the same double can be used on the healthy save as a positive
    control.

    Args:
        calls: The list every call appends its declared size to.

    Returns:
        The double, matching the signature of the seam it replaces.
    """

    def inflate(stream: bytes, expected_size: int) -> bytes:
        calls.append(expected_size)
        return zlib.decompress(stream, bufsize=max(expected_size, 1))

    return inflate


# ---------------------------------------------------------------------------
# The module constants agree with the corpus that produced the measurement
# ---------------------------------------------------------------------------


def test_the_framing_constants_match_the_corpus() -> None:
    """Cross-check the two independent transcriptions of one measurement.

    The corpus and this module each carry the framing constants, written by
    different slices. Equal values are the only evidence that neither slice
    mistyped the measurement in ``BOOTSTRAP.md`` section 3.1.
    """
    assert chunks.CHUNK_MAGIC == synthetic.CHUNK_MAGIC
    assert chunks.MARKER_WITH_ALGORITHM == synthetic.MARKER_22
    assert chunks.MARKER_WITHOUT_ALGORITHM == synthetic.MARKER_ZERO
    assert chunks.MAX_CHUNK_SIZE == synthetic.MAX_CHUNK_SIZE
    assert chunks.ALGORITHM_ZLIB == synthetic.ALGORITHM_ZLIB
    assert chunks.FRAME_SIZE_WITH_ALGORITHM == synthetic.ZLIB_OFFSET_WITH_ALGO
    assert chunks.FRAME_SIZE_WITHOUT_ALGORITHM == synthetic.ZLIB_OFFSET_WITHOUT_ALGO
    assert chunks.SIZES_OFFSET_WITH_ALGORITHM == synthetic.SIZES_OFFSET_WITH_ALGO
    assert chunks.SIZES_OFFSET_WITHOUT_ALGORITHM == synthetic.SIZES_OFFSET_WITHOUT_ALGO
    assert chunks.FRAMING_WITH_ALGORITHM == synthetic.FRAMING_MARKER22_ALGO
    assert chunks.FRAMING_WITHOUT_ALGORITHM == synthetic.FRAMING_ZERO_MARKER_NOALGO


def test_the_two_frame_sizes_differ_by_exactly_the_algorithm_byte() -> None:
    """The one-byte shift is the whole difference between the variants."""
    shift = chunks.FRAME_SIZE_WITH_ALGORITHM - chunks.FRAME_SIZE_WITHOUT_ALGORITHM
    assert shift == _ALGORITHM_BYTE_WIDTH
    block = chunks.SIZES_OFFSET_WITH_ALGORITHM - chunks.SIZES_OFFSET_WITHOUT_ALGORITHM
    assert block == _ALGORITHM_BYTE_WIDTH
    assert chunks.ALGORITHM_OFFSET == chunks.SIZES_OFFSET_WITHOUT_ALGORITHM


# ---------------------------------------------------------------------------
# ACCEPTANCE 1 - both framing variants read and walk
# ---------------------------------------------------------------------------


def test_read_frame_reads_the_marker22_algorithm_variant() -> None:
    """Header 14 - non-zero marker, algorithm byte present, stream at magic+49."""
    save = synthetic.SAVE_V60
    frame = chunks.read_frame(save.blob, save.chunk_offset)
    assert frame.magic == chunks.CHUNK_MAGIC
    assert frame.marker == chunks.MARKER_WITH_ALGORITHM
    assert frame.max_chunk_size == chunks.MAX_CHUNK_SIZE
    assert frame.algorithm == chunks.ALGORITHM_ZLIB
    assert frame.header_size == chunks.FRAME_SIZE_WITH_ALGORITHM
    assert frame.payload_offset == save.chunk_offset + chunks.FRAME_SIZE_WITH_ALGORITHM
    assert frame.framing == chunks.FRAMING_WITH_ALGORITHM
    assert frame.uncompressed_size == _INT64_WIDTH + len(save.body)
    assert frame.compressed_size == len(save.blob) - frame.payload_offset


def test_read_frame_reads_the_zero_marker_variant_with_no_algorithm_byte() -> None:
    """Header 10 - zero marker, NO algorithm byte, stream at magic+48.

    ``algorithm`` is None rather than 0. A parser reporting 0 would be claiming
    it read a field that is not in the file.
    """
    save = synthetic.SAVE_V36
    frame = chunks.read_frame(save.blob, save.chunk_offset)
    assert frame.magic == chunks.CHUNK_MAGIC
    assert frame.marker == chunks.MARKER_WITHOUT_ALGORITHM
    assert frame.max_chunk_size == chunks.MAX_CHUNK_SIZE
    assert frame.algorithm is None
    assert frame.header_size == chunks.FRAME_SIZE_WITHOUT_ALGORITHM
    assert frame.payload_offset == save.chunk_offset + chunks.FRAME_SIZE_WITHOUT_ALGORITHM
    assert frame.framing == chunks.FRAMING_WITHOUT_ALGORITHM
    # CS-404: header 10 carries an int32 body length prefix, not no prefix.
    assert frame.uncompressed_size == synthetic.body_prefix_width(10) + len(save.body)


def test_the_byte_at_magic_plus_16_is_size_data_on_the_zero_marker_variant() -> None:
    """The positive evidence that header 10 carries no algorithm byte.

    ``docs/adr/0007``: the byte at magic+16 takes values 2, 2 and 3 across the
    three header-10 saves. It VARIES, which is what the low byte of a
    compressed size does and what a fixed algorithm constant does not. This
    pins the same relationship in the corpus - the byte a naive parser would
    read as the algorithm is the first byte of the compressed size.
    """
    save = synthetic.SAVE_V36
    frame = chunks.read_frame(save.blob, save.chunk_offset)
    byte_at_16 = save.blob[save.chunk_offset + chunks.SIZES_OFFSET_WITHOUT_ALGORITHM]
    assert byte_at_16 == frame.compressed_size & 0xFF
    assert byte_at_16 != chunks.ALGORITHM_ZLIB


@pytest.mark.parametrize("save", synthetic.ALL_SAVES, ids=lambda s: s.name)
def test_every_corpus_fixture_walks_to_a_clean_end_of_file(save: synthetic.SyntheticSave) -> None:
    """ACCEPTANCE 1 - both variants, every header version the corpus carries.

    The walk is asserted to consume the blob EXACTLY: a walker that stopped
    early leaves bytes behind and one that over-read would have raised.
    """
    frames = list(chunks.iter_frames(save.blob, save.chunk_offset))
    assert len(frames) == save.chunk_count
    last = frames[-1]
    assert last.payload_offset + last.compressed_size == len(save.blob)


@pytest.mark.parametrize("save", synthetic.ALL_SAVES, ids=lambda s: s.name)
def test_every_corpus_fixture_decompresses_to_its_own_body(
    save: synthetic.SyntheticSave,
) -> None:
    """The payload is the fixture's body, prefix included where the version has one.

    Header 13 and 14 open the decompressed body with an int64 length and header
    10 opens with an int32 one, so the expected total is version dependent. This
    module never interprets that prefix - the body layer owns it - but the
    LENGTH is still the only honest assertion of a complete walk.
    """
    body = chunks.decompress_body(save.blob, save.chunk_offset)
    prefix = synthetic.body_prefix_width(save.header_version)
    assert len(body.payload) == prefix + len(save.body)
    assert body.payload[prefix:] == save.body
    assert body.chunk_count == save.chunk_count


def test_the_framing_follows_the_marker_and_not_the_header_version() -> None:
    """ACCEPTANCE - detection is from the marker word, per ADR 0007 Decision 3.

    Header-10 bytes are framed with the marker-22 variant, a combination that
    exists in no real file. A parser that dispatched on the header version
    would look for the zero-marker layout, read the algorithm byte as part of
    the compressed size, and land the zlib stream one byte early. A parser that
    dispatches on the marker reads it correctly and merely notes the
    disagreement.
    """
    blob, offset = _mismatched_framing_blob()
    frame = chunks.read_frame(blob, offset)
    assert frame.framing == chunks.FRAMING_WITH_ALGORITHM
    assert frame.algorithm == chunks.ALGORITHM_ZLIB
    assert frame.header_size == chunks.FRAME_SIZE_WITH_ALGORITHM
    assert frame.payload_offset + frame.compressed_size == len(blob)


def test_iter_frames_yields_frames_in_ascending_offset_order() -> None:
    """Each frame starts where the previous one's payload ended."""
    save = synthetic.SAVE_MULTICHUNK
    frames = list(chunks.iter_frames(save.blob, save.chunk_offset))
    at = save.chunk_offset
    for frame in frames:
        assert frame.payload_offset - frame.header_size == at
        at = frame.payload_offset + frame.compressed_size
    assert at == len(save.blob)


# ---------------------------------------------------------------------------
# ACCEPTANCE 2 - multi-chunk, and a test that fails if the walk stops at one
# ---------------------------------------------------------------------------


def test_the_multichunk_fixture_walks_every_chunk() -> None:
    """ACCEPTANCE 2 - the discriminator against a one-chunk walker.

    HOW IT DISCRIMINATES, stated as required. ``SAVE_MULTICHUNK`` is split at
    the real 131072-byte decompressed boundary and carries more than one chunk.
    A walker that read the first chunk and stopped would report
    ``chunk_count == 1`` against a fixture whose ``chunk_count`` is greater,
    and would return a payload of exactly ``MAX_CHUNK_SIZE`` bytes against an
    expected total that is strictly larger - because the first chunk of a
    multi-chunk save is always a FULL chunk. Both assertions below fail on that
    walker, and neither can be satisfied by a single-chunk read. The equality
    against the total is asserted rather than a mere "it parsed", which is the
    assertion a truncated walk would still pass.
    """
    save = synthetic.SAVE_MULTICHUNK
    assert save.chunk_count > _ONE_CHUNK, "the fixture must be multi-chunk or this proves nothing"

    body = chunks.decompress_body(save.blob, save.chunk_offset)

    assert body.chunk_count == save.chunk_count
    assert len(body.payload) == _INT64_WIDTH + len(save.body)
    assert len(body.payload) > chunks.MAX_CHUNK_SIZE


def test_the_multichunk_payload_carries_the_bytes_only_the_last_chunk_holds() -> None:
    """The second discriminator, on content rather than on length.

    The final chunk's decompressed bytes are the tail of the body. A walker
    that stopped at the first chunk never sees them, so this fails even if a
    length check were somehow satisfied by accident.
    """
    save = synthetic.SAVE_MULTICHUNK
    body = chunks.decompress_body(save.blob, save.chunk_offset)
    tail_start = chunks.MAX_CHUNK_SIZE * (save.chunk_count - 1)
    expected_tail = (struct.pack("<q", len(save.body)) + save.body)[tail_start:]
    assert body.payload[tail_start:] == expected_tail
    assert expected_tail


def test_every_chunk_but_the_last_decompresses_to_a_full_max_chunk() -> None:
    """The split is on the DECOMPRESSED size, which is what makes the walk resumable."""
    save = synthetic.SAVE_MULTICHUNK
    frames = list(chunks.iter_frames(save.blob, save.chunk_offset))
    for frame in frames[:-1]:
        assert frame.uncompressed_size == chunks.MAX_CHUNK_SIZE
    assert frames[-1].uncompressed_size <= chunks.MAX_CHUNK_SIZE


# ---------------------------------------------------------------------------
# ACCEPTANCE 3 and 4 - the frame's own integrity checks
# ---------------------------------------------------------------------------


def test_corrupt_magic_raises_a_framing_error() -> None:
    """ACCEPTANCE 3 - a wrong magic is refused on the field, not on a parse failure."""
    save = synthetic.SAVE_V60
    blob = synthetic.corrupt_magic(save)
    with pytest.raises(chunks.ChunkFramingError) as caught:
        chunks.read_frame(blob, save.chunk_offset)
    assert caught.value.field == "magic"
    assert caught.value.offset == save.chunk_offset


def test_corrupt_marker_raises_a_framing_error() -> None:
    """ACCEPTANCE 3 - 0xDEADBEEF is neither measured marker, so it selects no variant.

    A parser that defaulted to either framing here would be accepting anything
    and would then read the sizes from the wrong offset.
    """
    save = synthetic.SAVE_V60
    blob = synthetic.corrupt_marker(save)
    with pytest.raises(chunks.ChunkFramingError) as caught:
        chunks.read_frame(blob, save.chunk_offset)
    assert caught.value.field == "marker"


def test_corrupt_size_disagreement_raises_a_framing_error() -> None:
    """ACCEPTANCE 4 - the duplicated pair is the format's own checksum.

    The sizes are written twice from independent bytes. A parser reading the
    first pair and skipping the second throws away a free corruption detector,
    and nothing else in the frame would tell it.
    """
    save = synthetic.SAVE_V60
    blob = synthetic.corrupt_size_disagreement(save)
    with pytest.raises(chunks.ChunkFramingError) as caught:
        chunks.read_frame(blob, save.chunk_offset)
    assert caught.value.field == "compressed_size"
    assert caught.value.expected != caught.value.actual


def test_a_size_disagreement_is_caught_on_the_zero_marker_variant_too() -> None:
    """The checksum reads from magic+16 on header 10, not magic+17.

    A parser that hardcoded the with-algorithm offset would compare the wrong
    eight bytes and miss this entirely.
    """
    save = synthetic.SAVE_V36
    blob = synthetic.corrupt_size_disagreement(save)
    with pytest.raises(chunks.ChunkFramingError) as caught:
        chunks.read_frame(blob, save.chunk_offset)
    assert caught.value.field == "compressed_size"


def test_a_negative_declared_size_raises_a_framing_error() -> None:
    """The sizes are signed on the wire, so a negative one is reachable.

    It must be refused before it reaches a slice expression, where a negative
    length silently means "count from the end" rather than "malformed".
    """
    save = synthetic.SAVE_V60
    at = save.chunk_offset + chunks.SIZES_OFFSET_WITH_ALGORITHM
    negative = struct.pack("<q", -1)
    blob = save.blob[:at] + negative + save.blob[at + _INT64_WIDTH :]
    blob = blob[: at + _SECOND_COMPRESSED] + negative + blob[at + _SECOND_UNCOMPRESSED :]
    with pytest.raises(chunks.ChunkFramingError) as caught:
        chunks.read_frame(blob, save.chunk_offset)
    assert caught.value.field == "compressed_size"


# ---------------------------------------------------------------------------
# ACCEPTANCE 5 - a damaged stream is a ChunkDecompressError, never a zlib.error
# ---------------------------------------------------------------------------


def test_corrupt_zlib_stream_raises_a_decompress_error_not_a_zlib_error() -> None:
    """ACCEPTANCE 5 - the frame survives and the inflate fails.

    ``zlib.error`` escaping this layer would make every caller import zlib to
    handle a save problem, and would carry the library's own message - which is
    not one of this module's fixed reason strings.
    """
    save = synthetic.SAVE_V60
    blob = synthetic.corrupt_zlib_stream(save)
    with pytest.raises(chunks.ChunkDecompressError) as caught:
        chunks.decompress_body(blob, save.chunk_offset)
    assert caught.value.field == "payload"
    assert not isinstance(caught.value, zlib.error)


def test_a_zlib_error_does_not_escape_the_walk_on_the_zero_marker_variant() -> None:
    """The same guarantee on header 10, where the stream starts one byte earlier."""
    save = synthetic.SAVE_V36
    blob = synthetic.corrupt_zlib_stream(save)
    with pytest.raises(chunks.ChunkDecompressError):
        chunks.decompress_body(blob, save.chunk_offset)


def test_an_algorithm_that_is_not_zlib_raises_a_decompress_error() -> None:
    """An unmeasured algorithm is refused rather than fed to the zlib inflate.

    Non-negotiable 7 flags unknown content and skips it, but a body that cannot
    be decompressed at all is not skippable content - there would be no body to
    return. It is refused on the field so the message names the cause instead
    of surfacing as an unrelated inflate failure.
    """
    save = synthetic.SAVE_V60
    at = save.chunk_offset + chunks.ALGORITHM_OFFSET
    blob = (
        save.blob[:at]
        + bytes([chunks.ALGORITHM_ZLIB + 1])
        + save.blob[at + _ALGORITHM_BYTE_WIDTH :]
    )
    with pytest.raises(chunks.ChunkDecompressError) as caught:
        chunks.decompress_body(blob, save.chunk_offset)
    assert caught.value.field == "algorithm"


# ---------------------------------------------------------------------------
# ACCEPTANCE 6 - the bound precedes the allocation, proven with a recording spy
# ---------------------------------------------------------------------------


def test_the_declared_chunk_bomb_is_refused_before_any_inflate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """ACCEPTANCE 6 - refusal on the DECLARED size, before allocating.

    ``declared_chunk_bomb`` writes a terabyte into BOTH copies of the
    uncompressed size, so the format's own consistency check still passes and
    the parser cannot dodge the case by noticing a disagreement instead. The
    compressed size is left correct, so the frame is otherwise well formed.

    The ordering is proven by a RECORDING spy on the inflate seam, not by a
    timeout and not by a raising spy. ``calls == []`` is the assertion: the
    refusal happened with the allocation path never entered.
    ``test_the_recording_spy_observes_one_inflate_per_chunk`` is the positive
    control that makes this non-vacuous.
    """
    calls: list[int] = []
    monkeypatch.setattr(chunks, "_inflate", _recording_inflate(calls))

    save = synthetic.SAVE_V60
    blob = synthetic.declared_chunk_bomb(save)

    with pytest.raises(chunks.ChunkBudgetExceededError) as caught:
        chunks.decompress_body(blob, save.chunk_offset)

    assert calls == [], "the bound must be applied BEFORE the allocation path is entered"
    assert caught.value.field == "uncompressed_size"
    assert caught.value.actual == synthetic.CHUNK_BOMB_UNCOMPRESSED_SIZE


def test_the_recording_spy_observes_one_inflate_per_chunk(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The positive control for the bomb test above, and it is load-bearing.

    A spy that recorded nothing under any circumstance would satisfy
    ``calls == []`` in the bomb test while proving nothing at all. The SAME
    double is installed here on a healthy multi-chunk save and must record one
    call per chunk, so the empty list in the bomb test is evidence of a refusal
    rather than evidence of a broken double.
    """
    calls: list[int] = []
    monkeypatch.setattr(chunks, "_inflate", _recording_inflate(calls))

    save = synthetic.SAVE_MULTICHUNK
    body = chunks.decompress_body(save.blob, save.chunk_offset)

    assert len(calls) == save.chunk_count
    assert sum(calls) == len(body.payload)


def test_read_frame_alone_refuses_the_bomb() -> None:
    """The bound lives in the frame read, so no caller can route around it.

    ``read_frame`` never allocates a payload and never calls zlib. A budget
    failure raised from there is structurally incapable of following an
    allocation.
    """
    save = synthetic.SAVE_V60
    blob = synthetic.declared_chunk_bomb(save)
    with pytest.raises(chunks.ChunkBudgetExceededError):
        chunks.read_frame(blob, save.chunk_offset)


def test_the_bomb_is_refused_on_the_zero_marker_variant_too() -> None:
    """The declared size is read from magic+16 on header 10."""
    save = synthetic.SAVE_V36
    blob = synthetic.declared_chunk_bomb(save)
    with pytest.raises(chunks.ChunkBudgetExceededError) as caught:
        chunks.read_frame(blob, save.chunk_offset)
    assert caught.value.actual == synthetic.CHUNK_BOMB_UNCOMPRESSED_SIZE


def test_an_absurd_declared_max_chunk_size_is_refused() -> None:
    """The frame's own bound is itself bounded.

    ``uncompressed_size`` is checked against the frame's declared
    ``max_chunk_size``, so a corrupt file that inflated that field would
    otherwise raise its own ceiling and walk straight past the check.
    """
    save = synthetic.SAVE_V60
    at = save.chunk_offset + _INT64_WIDTH
    blob = (
        save.blob[:at]
        + struct.pack("<q", chunks.MAX_DECLARED_CHUNK_BYTES + 1)
        + save.blob[at + _INT64_WIDTH :]
    )
    with pytest.raises(chunks.ChunkBudgetExceededError) as caught:
        chunks.read_frame(blob, save.chunk_offset)
    assert caught.value.field == "max_chunk_size"


def test_the_total_body_ceiling_is_enforced(monkeypatch: pytest.MonkeyPatch) -> None:
    """The second bound, which no per-chunk check can reach.

    A file declaring many individually legal chunks passes every per-frame
    bound and still asks for unbounded memory in total. The ceiling is lowered
    here rather than a multi-gigabyte fixture being built, because an untested
    raise path is an unrun gate - the ceiling would otherwise be decoration
    that no run has ever reached.
    """
    save = synthetic.SAVE_MULTICHUNK
    monkeypatch.setattr(chunks, "MAX_TOTAL_BODY_BYTES", chunks.MAX_CHUNK_SIZE)

    with pytest.raises(chunks.ChunkBudgetExceededError) as caught:
        chunks.decompress_body(save.blob, save.chunk_offset)
    assert caught.value.field == "body_size"
    assert caught.value.expected == chunks.MAX_CHUNK_SIZE


def test_the_total_body_ceiling_is_checked_before_the_inflate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The total ceiling is a pre-allocation bound too, not only the per-chunk one.

    Measured during this slice: with the per-chunk bound removed, THIS check is
    what still refused the declared bomb. Both bounds precede the allocation,
    and that is asserted rather than assumed.
    """
    calls: list[int] = []
    monkeypatch.setattr(chunks, "_inflate", _recording_inflate(calls))
    monkeypatch.setattr(chunks, "MAX_TOTAL_BODY_BYTES", 0)

    save = synthetic.SAVE_V60
    with pytest.raises(chunks.ChunkBudgetExceededError):
        chunks.decompress_body(save.blob, save.chunk_offset)
    assert calls == []


def test_the_chunk_count_ceiling_is_enforced(monkeypatch: pytest.MonkeyPatch) -> None:
    """The stated resource bound on the walk length.

    Termination is already guaranteed by the refusal of a zero compressed size,
    so this ceiling is defence rather than the thing that makes the loop
    finite. It is still exercised: a bound nothing has ever tripped is a bound
    nobody knows is wired up.
    """
    save = synthetic.SAVE_MULTICHUNK
    monkeypatch.setattr(chunks, "MAX_CHUNKS", _ONE_CHUNK)

    with pytest.raises(chunks.ChunkBudgetExceededError) as caught:
        list(chunks.iter_frames(save.blob, save.chunk_offset))
    assert caught.value.field == "chunk_count"


def test_a_compressed_size_of_zero_is_refused_so_the_walk_cannot_stall() -> None:
    """The guarantee that makes :func:`iter_frames` terminate.

    A frame declaring zero compressed bytes would leave the walk offset
    unchanged and spin forever. It is refused in the frame read, which is what
    lets the loop be written without a separate progress check.
    """
    save = synthetic.SAVE_V60
    at = save.chunk_offset + chunks.SIZES_OFFSET_WITH_ALGORITHM
    zero = struct.pack("<q", 0)
    blob = save.blob[:at] + zero + save.blob[at + _INT64_WIDTH :]
    blob = blob[: at + _SECOND_COMPRESSED] + zero + blob[at + _SECOND_UNCOMPRESSED :]
    with pytest.raises(chunks.ChunkFramingError) as caught:
        chunks.read_frame(blob, save.chunk_offset)
    assert caught.value.field == "compressed_size"


# ---------------------------------------------------------------------------
# ACCEPTANCE 7 - truncation
# ---------------------------------------------------------------------------

_FILE_TRUNCATIONS: Final = tuple(
    point for point in synthetic.TRUNCATION_BOUNDARIES if point.scope == synthetic.SCOPE_FILE
)
_BODY_TRUNCATIONS: Final = tuple(
    point for point in synthetic.TRUNCATION_BOUNDARIES if point.scope == synthetic.SCOPE_BODY
)


def test_the_corpus_still_carries_the_truncation_points_this_module_walks() -> None:
    """Guard against the corpus changing shape under this module.

    If a later slice adds or removes a boundary, the parametrized test below
    silently changes what it covers. This pins the split so that change is
    visible as a failure here rather than as quiet coverage loss.
    """
    assert _FILE_TRUNCATIONS
    assert _BODY_TRUNCATIONS
    assert len(_FILE_TRUNCATIONS) + len(_BODY_TRUNCATIONS) == len(synthetic.TRUNCATION_BOUNDARIES)


@pytest.mark.parametrize("point", _FILE_TRUNCATIONS, ids=lambda p: p.label)
def test_a_file_truncation_raises_a_truncated_error(point: synthetic.TruncationPoint) -> None:
    """ACCEPTANCE 7 - every file-scope cut point, from inside the header to inside the stream.

    The first two points cut the file BEFORE the chunk offset, so the walk
    starts past the end of the buffer; the rest cut inside the magic, inside
    the duplicated size block, and inside the zlib stream. All five are
    truncation rather than corruption and all five must say so.
    """
    save = synthetic.SAVE_V60
    blob = synthetic.truncated_at(save.blob, point.offset)
    with pytest.raises(chunks.ChunkTruncatedError):
        chunks.decompress_body(blob, save.chunk_offset)


@pytest.mark.parametrize("point", _BODY_TRUNCATIONS, ids=lambda p: p.label)
def test_a_body_truncation_is_invisible_to_this_layer(point: synthetic.TruncationPoint) -> None:
    """ACCEPTANCE 7, BODY SCOPE - REFUTED AS WORDED, and pinned to what is true.

    The brief asked for ``ChunkTruncatedError`` here. It cannot hold, and the
    corpus says why in its own words: ``save_with_truncated_body`` rewrites the
    length prefix to the truncated length and RECOMPRESSES, "so the file is
    well formed all the way down to the record walk... the damage has to be
    reachable only after a successful inflate, or it is testing the framing
    again instead of the record walk."

    Measured on the fixture: magic and marker intact, the declared compressed
    size an exact fit for the bytes present, and the stream inflating cleanly.
    There is nothing at this layer to detect. Raising here would require this
    module to interpret the body's int64 length prefix - a header-version-keyed
    field this layer deliberately does not read, and one the corpus keeps
    CONSISTENT with the truncated body anyway, so even that would not fire.

    This test therefore pins the true behaviour: a clean walk. The case belongs
    to the record walker, which is a different slice.
    """
    save = synthetic.SAVE_V60
    blob = synthetic.save_with_truncated_body(save, point.offset)
    body = chunks.decompress_body(blob, save.chunk_offset)
    assert body.chunk_count == _ONE_CHUNK
    assert len(body.payload) == _INT64_WIDTH + point.offset


def test_an_offset_past_the_end_of_the_buffer_raises_a_truncated_error() -> None:
    """A walk that can find no chunk at all is a truncation, not an empty body.

    Returning zero chunks and an empty payload would be the worst available
    answer: a caller cannot tell it from a save that legitimately holds
    nothing.
    """
    save = synthetic.SAVE_V60
    with pytest.raises(chunks.ChunkTruncatedError):
        chunks.decompress_body(save.blob, len(save.blob))
    with pytest.raises(chunks.ChunkTruncatedError):
        chunks.decompress_body(save.blob, len(save.blob) + 1)


def test_a_declared_compressed_size_beyond_the_buffer_raises_a_truncated_error() -> None:
    """The bound is against the REMAINING buffer, not merely against a constant."""
    save = synthetic.SAVE_V60
    at = save.chunk_offset + chunks.SIZES_OFFSET_WITH_ALGORITHM
    oversize = struct.pack("<q", len(save.blob))
    blob = save.blob[:at] + oversize + save.blob[at + _INT64_WIDTH :]
    blob = blob[: at + 16] + oversize + blob[at + 24 :]
    with pytest.raises(chunks.ChunkTruncatedError) as caught:
        chunks.read_frame(blob, save.chunk_offset)
    assert caught.value.field == "compressed_size"


def test_a_negative_offset_is_a_caller_bug_and_not_a_chunk_error() -> None:
    """A negative offset is not file damage, so it is not a ChunkError."""
    save = synthetic.SAVE_V60
    with pytest.raises(ValueError, match="offset") as caught:
        chunks.read_frame(save.blob, -1)
    assert not isinstance(caught.value, chunks.ChunkError)


# ---------------------------------------------------------------------------
# ACCEPTANCE 8 - a marker/version disagreement warns and does not raise
# ---------------------------------------------------------------------------


def test_a_marker_version_disagreement_warns_and_does_not_raise() -> None:
    """ACCEPTANCE 8 - the cross-check is advisory, because the KEY is undetermined.

    ADR 0007 records three unrefuted candidate keys for the framing variant -
    header version, save version and build changelist - all of which predict it
    perfectly on the local corpus. A parser that raised on disagreement would
    be asserting that the header version is the key, which is precisely the
    claim the ADR refuses to make.
    """
    blob, offset = _mismatched_framing_blob()
    body = chunks.decompress_body(blob, offset, header_version=synthetic.HEADER_VERSION_10)
    codes = [warning.code for warning in body.warnings]
    assert chunks.WARN_MARKER_VERSION_DISAGREEMENT in codes
    assert body.chunk_count >= _ONE_CHUNK


@pytest.mark.parametrize("save", synthetic.ALL_SAVES, ids=lambda s: s.name)
def test_an_agreeing_header_version_produces_no_warning(save: synthetic.SyntheticSave) -> None:
    """Every corpus fixture agrees, so a warning on any of them is a false positive."""
    body = chunks.decompress_body(save.blob, save.chunk_offset, header_version=save.header_version)
    assert body.warnings == ()


def test_omitting_the_header_version_produces_no_warning() -> None:
    """The cross-check is opt-in. Nothing is inferred when the caller supplies nothing."""
    save = synthetic.SAVE_V60
    body = chunks.decompress_body(save.blob, save.chunk_offset)
    assert body.warnings == ()


def test_an_unmeasured_header_version_warns_rather_than_raising() -> None:
    """ADR 0007 Decision 3 - a combination outside the measured set is flagged, never guessed.

    The framing still comes from the marker, so the walk succeeds. What is
    reported is that no cross-check was possible.
    """
    save = synthetic.SAVE_V60
    body = chunks.decompress_body(
        save.blob,
        save.chunk_offset,
        header_version=synthetic.UNSUPPORTED_HEADER_VERSION,
    )
    codes = [warning.code for warning in body.warnings]
    assert chunks.WARN_UNMEASURED_HEADER_VERSION in codes
    assert len(body.payload) == _INT64_WIDTH + len(save.body)


def test_a_warning_is_aggregated_across_chunks_rather_than_repeated() -> None:
    """A 138-chunk save must not produce 138 identical lines.

    The multi-chunk fixture disagrees on every one of its chunks, so an
    unaggregated implementation returns one warning per chunk.
    """
    save = synthetic.SAVE_MULTICHUNK
    body = chunks.decompress_body(
        save.blob, save.chunk_offset, header_version=synthetic.HEADER_VERSION_10
    )
    disagreements = [
        warning
        for warning in body.warnings
        if warning.code == chunks.WARN_MARKER_VERSION_DISAGREEMENT
    ]
    assert len(disagreements) == _ONE_CHUNK
    assert disagreements[0].count == save.chunk_count


# ---------------------------------------------------------------------------
# The error taxonomy - non-negotiable 12
# ---------------------------------------------------------------------------


def _raising_cases() -> list[object]:
    """Every refusal this module can produce, one parametrized callable per case.

    Returns:
        ``pytest.param`` entries, each a zero-argument callable that must raise.
    """
    v60 = synthetic.SAVE_V60
    v36 = synthetic.SAVE_V36

    at = v60.chunk_offset + chunks.SIZES_OFFSET_WITH_ALGORITHM
    oversize = struct.pack("<q", len(v60.blob))
    over_blob = v60.blob[:at] + oversize + v60.blob[at + _INT64_WIDTH :]
    over_blob = (
        over_blob[: at + _SECOND_COMPRESSED] + oversize + over_blob[at + _SECOND_UNCOMPRESSED :]
    )

    algo_at = v60.chunk_offset + chunks.ALGORITHM_OFFSET
    bad_algo = (
        v60.blob[:algo_at]
        + bytes([chunks.ALGORITHM_ZLIB + 1])
        + v60.blob[algo_at + _ALGORITHM_BYTE_WIDTH :]
    )

    return [
        pytest.param(
            lambda: chunks.read_frame(synthetic.corrupt_magic(v60), v60.chunk_offset), id="magic"
        ),
        pytest.param(
            lambda: chunks.read_frame(synthetic.corrupt_marker(v60), v60.chunk_offset), id="marker"
        ),
        pytest.param(
            lambda: chunks.read_frame(synthetic.corrupt_size_disagreement(v60), v60.chunk_offset),
            id="size-disagreement",
        ),
        pytest.param(
            lambda: chunks.read_frame(synthetic.declared_chunk_bomb(v60), v60.chunk_offset),
            id="bomb",
        ),
        pytest.param(
            lambda: chunks.read_frame(synthetic.declared_chunk_bomb(v36), v36.chunk_offset),
            id="bomb-no-algo",
        ),
        pytest.param(
            lambda: chunks.decompress_body(synthetic.corrupt_zlib_stream(v60), v60.chunk_offset),
            id="zlib",
        ),
        pytest.param(
            lambda: chunks.decompress_body(bad_algo, v60.chunk_offset), id="bad-algorithm"
        ),
        pytest.param(
            lambda: chunks.read_frame(over_blob, v60.chunk_offset), id="compressed-beyond-buffer"
        ),
        pytest.param(
            lambda: chunks.read_frame(
                synthetic.truncated_at(v60.blob, v60.chunk_offset + 2), v60.chunk_offset
            ),
            id="truncated-mid-magic",
        ),
        pytest.param(lambda: chunks.decompress_body(v60.blob, len(v60.blob)), id="offset-past-end"),
    ]


@pytest.mark.parametrize("call", _raising_cases())
def test_every_raised_error_carries_only_taxonomy_fields(call: Callable[[], object]) -> None:
    """Non-negotiable 12, asserted mechanically rather than by reading the code.

    An exception may carry a field name, a byte offset, an expected/actual
    length or count, a version scalar and a fixed reason string. Anything else
    on the instance is a channel that could carry save content, so the
    attribute SET is pinned rather than the values.
    """
    with pytest.raises(chunks.ChunkError) as caught:
        call()
    assert set(vars(caught.value)) <= _ALLOWED_ERROR_ATTRIBUTES
    for name in ("offset", "expected", "actual", "version"):
        value = getattr(caught.value, name)
        assert value is None or isinstance(value, int)
    assert isinstance(caught.value.field, str)


@pytest.mark.parametrize("call", _raising_cases())
def test_every_raised_reason_is_a_declared_constant(call: Callable[[], object]) -> None:
    """The reason string cannot carry content if it is never built from content.

    Every reason is a module-level ``REASON_*`` constant. Collecting them from
    the module and asserting membership proves the property mechanically - an
    f-string interpolating a decoded save value could not pass this.
    """
    declared = {
        value
        for name, value in vars(chunks).items()
        if name.startswith("REASON_") and isinstance(value, str)
    }
    assert declared, "the module must declare its reason strings as constants"
    with pytest.raises(chunks.ChunkError) as caught:
        call()
    assert caught.value.reason in declared


@pytest.mark.parametrize("call", _raising_cases())
def test_no_raised_message_echoes_the_bytes_that_caused_it(call: Callable[[], object]) -> None:
    """A hex preview in an exception is a disclosure, so the rendering is pinned.

    The corrupted values spliced by the corpus are asserted ABSENT: a parser
    that helpfully reported "expected 0x9E2A83C1, got 0x11223344" would be
    echoing four bytes of the file, and the same habit applied to a header
    field echoes an operator's world name.
    """
    with pytest.raises(chunks.ChunkError) as caught:
        call()
    message = str(caught.value)

    assert message.isascii()
    assert "\\x" not in message
    assert "b'" not in message
    assert 'b"' not in message
    assert _CORRUPT_MAGIC_HEX not in message.lower()
    assert _CORRUPT_MARKER_HEX not in message.lower()
    assert "0x" not in message.lower()


def test_every_error_class_descends_from_the_base() -> None:
    """One catch clause covers the whole layer."""
    for cls in (
        chunks.ChunkFramingError,
        chunks.ChunkTruncatedError,
        chunks.ChunkDecompressError,
        chunks.ChunkBudgetExceededError,
    ):
        assert issubclass(cls, chunks.ChunkError)
    assert issubclass(chunks.ChunkError, Exception)


# ---------------------------------------------------------------------------
# Seam independence - this module takes bytes and an offset, and nothing else
# ---------------------------------------------------------------------------


def test_the_chunk_module_imports_no_sibling_save_module() -> None:
    """The independence that lets this slice be written beside the header parser.

    Asserted on the parsed import graph rather than on a substring search, so
    ``from clockspeed.save.header import parse_header`` is caught as an import
    and a mention inside a docstring is not.
    """
    source = Path(chunks.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)

    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported.add(node.module)
            imported.update(f"{node.module}.{alias.name}" for alias in node.names)

    for sibling in _SIBLING_SAVE_MODULES:
        assert f"clockspeed.save.{sibling}" not in imported

    assert not any(name.startswith("tests") for name in imported)


def test_the_chunk_module_reads_no_file_and_writes_none() -> None:
    """ADR 0007 Decision 6 - workdir.py will be the only writer in this package.

    This module takes ``bytes``. It must not open a path, which is what keeps
    that commitment mechanically checkable rather than merely intended.
    """
    source = Path(chunks.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    called = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert "open" not in called
    assert "Path" not in called


# ---------------------------------------------------------------------------
# CS-852 - the field vocabulary gate
#
# ``clockspeed/save/world.py`` wraps every failure from this module in a
# WorldLoadError with ``raise ... from exc``, which makes THIS module's message
# part of the world loader's formatted traceback. The paragraph there records
# what that is safe on: a field name from a CLOSED VOCABULARY. Until CS-852 the
# guarantee was stated in the ChunkError docstring and enforced by nothing but
# the habit of passing a literal at every raise site.
# ---------------------------------------------------------------------------

#: A value no field name could be, planted into the one text channel a
#: ChunkError carries besides its fixed reason. Obviously synthetic: never a
#: real field name, path, token or account id.
_PLANTED_FIELD: Final = "PLANTED_CS852_FIELD_zzz"


def _field_arguments_in(module_source: str) -> set[str]:
    """Every string literal this module hands to an error's ``field``.

    DERIVED FROM THE RAISE SITES rather than transcribed from the vocabulary,
    so the two cannot agree by having been copied from each other.

    Args:
        module_source: The parser module's text.

    Returns:
        The literal field names.
    """
    found: set[str] = set()
    for node in ast.walk(ast.parse(module_source)):
        if not isinstance(node, ast.Call):
            continue
        callee = getattr(node.func, "id", None) or getattr(node.func, "attr", None)
        if callee is None or not callee.endswith("Error"):
            continue
        for keyword in node.keywords:
            if (
                keyword.arg == "field"
                and isinstance(keyword.value, ast.Constant)
                and isinstance(keyword.value.value, str)
            ):
                found.add(keyword.value.value)
    return found


def test_the_field_vocabulary_matches_the_modules_own_raise_sites() -> None:
    """THE VOCABULARY IS DERIVED, NOT TRANSCRIBED, and asserted BOTH ways.

    A name in the set that no site raises is dead vocabulary; a name raised
    that the set does not hold would be refused at runtime and turn a parse
    failure into a ValueError. Equality is what keeps the closed set honest,
    and it is what makes a new raise site a deliberate decision.
    """
    raised = _field_arguments_in(Path(chunks.__file__).read_text(encoding="utf-8"))
    assert raised, "no field literal found at any raise site - this arm is measuring nothing"
    assert raised == set(chunks.FIELD_NAMES), (
        f"raised but not in the vocabulary: {sorted(raised - set(chunks.FIELD_NAMES))}; "
        f"in the vocabulary but never raised: {sorted(set(chunks.FIELD_NAMES) - raised)}"
    )


def test_a_planted_field_name_is_refused_before_it_reaches_the_message() -> None:
    """THE PLANTED-MARKER REFUSAL that ``clockspeed/save/world.py`` claims exists.

    ``field`` is the only parameter of this taxonomy that is text. Before
    CS-852 this construction SUCCEEDED and the planted value rendered through
    ``str()`` and ``repr()`` - ``BaseException`` renders ``args`` on both.
    """
    with pytest.raises(ValueError, match="is not one of the"):
        chunks.ChunkError(chunks.REASON_BAD_MAGIC, field=_PLANTED_FIELD, offset=0)


def test_the_refusal_does_not_echo_the_name_it_rejected() -> None:
    """The rejected value is the thing under suspicion, so it may not be echoed.

    A refusal that quoted the name it refused would be the disclosure the gate
    exists to prevent, arriving through the gate itself.
    """
    with pytest.raises(ValueError, match="is not one of the") as caught:
        chunks.ChunkError(chunks.REASON_BAD_MAGIC, field=_PLANTED_FIELD, offset=0)
    rendered = str(caught.value) + repr(caught.value)
    assert _PLANTED_FIELD not in rendered
    assert str(len(chunks.FIELD_NAMES)) in rendered


def test_every_subclass_inherits_the_refusal() -> None:
    """The four subclasses ship no ``__init__``, so the base is what governs them.

    A gate applied to the base only helps if nothing bypasses it, and every
    raise site in this module builds a SUBCLASS rather than the base.
    """
    for cls in (
        chunks.ChunkFramingError,
        chunks.ChunkTruncatedError,
        chunks.ChunkDecompressError,
        chunks.ChunkBudgetExceededError,
    ):
        with pytest.raises(ValueError, match="is not one of the"):
            cls(chunks.REASON_BAD_MAGIC, field=_PLANTED_FIELD, offset=0)


def test_a_legitimate_field_name_still_constructs() -> None:
    """THE NEGATIVE HALF. A gate that refused everything would pass the arms above.

    Without this, replacing the membership test with an unconditional raise
    would satisfy every refusal assertion in this section.
    """
    for name in sorted(chunks.FIELD_NAMES):
        error = chunks.ChunkError(chunks.REASON_BAD_MAGIC, field=name, offset=0)
        assert error.field == name
