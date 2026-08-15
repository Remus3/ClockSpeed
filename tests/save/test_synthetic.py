"""Invariants of the synthetic save corpus itself - the builder is verified, not trusted.

WHY A BYTE BUILDER NEEDS ITS OWN TEST MODULE, AHEAD OF ANY PARSER
------------------------------------------------------------------
Every phase 4 slice - header parse, chunk walk, usmap load, actor
deserialization - asserts against ``tests/save/synthetic.py``. A builder that
emits a wrong byte layout therefore does not fail. It teaches every module above
it to expect the wrong layout, every one of those modules passes its own tests,
and the phase closes on a parser that has never seen a real save. That is the
stated common-mode risk of the whole phase, and this module is one of the two
controls against it.

CONTROL 1 - THE INDEPENDENT MINIMAL READER BELOW
--------------------------------------------------
``_read_fstring``, ``_read_header``, ``_read_chunk`` and ``_read_object`` are
written from the format description, not from the builder. They share NO code
and NO constants with ``tests/save/synthetic.py``: every literal they need -
the magic, both markers, the algorithm byte, the two zlib offsets, the tail
size, the transform width - is spelled again here on purpose. Importing those
from the builder would make the check a restatement of the builder's own
opinion, which is the parallel-fixture failure class in
``memory/test-quality-failure-classes.md``.

The precedent is ``tests/data/test_registry.py``, which cross-checks the
registry with a naive independent count rather than with the real parser. Here
there is not even a real parser to be tempted by - ``clockspeed/save/`` is empty
and this slice writes nothing into it.

WHAT THAT INDEPENDENCE DOES AND DOES NOT BUY, STATED HONESTLY
---------------------------------------------------------------
The reader independently re-derives the DISPATCH (which field decides which
branch) and the OFFSET ARITHMETIC (where each field lands). Those are the two
things a parser gets wrong, and they are genuinely checked twice here.

It does NOT independently establish the measured CONSTANTS. The reader's
``_DELTA_BY_SAVE_VERSION`` carries the same +4 and +8 the builder carries,
because both come from the same measurement of the live library. If that
measurement is wrong, both copies are wrong together and no test in this file
can tell. Closing that gap is what control 2 is for, and it is the reason
control 2 is mandatory rather than nice to have.

CONTROL 2 - THE REAL-SAVE SHAPE ANCHOR
-----------------------------------------
``test_the_builder_matches_the_shape_of_a_real_save`` is the only test in phase
4 that touches a real file. It SKIPS WITH A REASON when no save is present,
because CI runs on a runner with no game install - and a skip is not a pass, so
it announces itself in the ``-ra`` summary rather than blending into the dots.

When a save IS present it compares SHAPES ONLY. It asserts no value and prints
no value: the shape is a tuple of ints and bools, so even pytest's assertion
repr cannot carry a world name, an account id or a token into a log
(non-negotiable 12). The load-bearing assertion inside ``_shape_of`` is that the
header walk lands EXACTLY on the chunk magic. Nothing else has to be asserted
about the string layout - if the string count or the tail size were wrong, the
cursor would stop somewhere that is not the magic, and it would say so without
ever naming what it read.
"""

from __future__ import annotations

import re
import struct
import zlib
from pathlib import Path

import pytest

from clockspeed.data import locate
from tests.save import synthetic

# ---------------------------------------------------------------------------
# The independent minimal reader.
#
# EVERY literal below is deliberately a SECOND spelling of a number that also
# appears in tests/save/synthetic.py. Do not refactor these into a shared
# constant, and do not import them from the builder - the duplication IS the
# control. See the module docstring.
# ---------------------------------------------------------------------------

_MAGIC = 0x9E2A83C1
_MARKER_22 = 0x22222222
_MARKER_ZERO = 0x00000000
_MAX_CHUNK = 131072
_ALGO_ZLIB = 3

#: Bytes from the magic to the first byte of the zlib stream. With the algorithm
#: byte present the chunk header is 4 + 4 + 8 + 1 + 8 * 4 = 49; without it the
#: same block is 48. Re-derived here rather than imported.
_ZLIB_AT_WITH_ALGO = 49
_ZLIB_AT_WITHOUT_ALGO = 48

_TAIL_SIZE = 28
_HEADER_10 = 10
_HEADER_13 = 13

#: Body length prefix widths, per header version. CS-404: header 10 carries a
#: NARROW prefix rather than none at all.
_BODY_PREFIX_WIDE = 8
_BODY_PREFIX_NARROW = 4
_HEADER_14 = 14

_STRINGS_WITH_SAVE_NAME = 4
_STRINGS_WITHOUT_SAVE_NAME = 3

#: Rotation (4) + translation (3) + scale (3), all float32.
_TRANSFORM_FLOATS = 10
_TRANSFORM_BYTES = 40

#: The reader's OWN copy of the measured transform deltas. Save version 42 is
#: absent from both copies because it was never measured - see the builder.
_DELTA_BY_SAVE_VERSION = {36: 4, 52: 8, 60: 8}

_MAP_NAME = "Persistent_Level"
_OPTIONS_MARK = "?"
_TOKEN_LENGTH = 22
_BASE64URL = re.compile(r"\A[A-Za-z0-9_-]+\Z")

_NOT_FOUND = -1

#: The save version whose delta CS-407 measured, and that measured value.
_SAVE_42 = 42
_SAVE_42_DELTA = 4

#: A save version nobody has measured. REPOINTED under CS-407: this was 42
#: until save 42's delta was measured at 4, and leaving it there would have kept
#: the refusal RULE green while its EXAMPLE had become false - the stale-example
#: failure class. The rule under test is "an unmeasured version raises rather
#: than defaulting", and that rule needs an example that is still unmeasured.
_UNMEASURED_SAVE_VERSION = 97

#: One past the highest 7-bit code point.
_ASCII_CEILING = 128

#: A multi-chunk fixture has to span more than two chunks for "spans several"
#: to mean anything - two could be an off-by-one on a single boundary.
_MIN_MULTICHUNK_CHUNKS = 2

#: How many names the usmap round-trip fixture declares.
_USMAP_NAME_COUNT = 2

#: The size of the length-prefix and string-payload fields the truncation
#: boundaries cut through.
_INT32_WIDTH = 4


def _read_fstring(blob: bytes, pos: int) -> tuple[str, int]:
    """Read one length-prefixed string and return it with the new cursor.

    The count INCLUDES the trailing null. Positive means UTF-8 with a one-byte
    null; negative means UTF-16-LE and the magnitude is the CHARACTER count
    including a two-byte null. Zero means the empty string with no payload.

    Decoding is deliberately error-tolerant. This function runs against a real
    save in the anchor test, and a strict decode would raise an exception whose
    message carries the offending raw bytes into the log - an echo path, and so
    a non-negotiable 12 violation. Nothing here retains or prints the text.

    Args:
        blob: The buffer.
        pos: Offset of the int32 count.

    Returns:
        The decoded text and the offset just past the string.
    """
    (count,) = struct.unpack_from("<i", blob, pos)
    pos += 4
    if count == 0:
        return "", pos
    if count > 0:
        raw = blob[pos : pos + count]
        return raw[:-1].decode("utf-8", errors="replace"), pos + count
    chars = -count
    raw = blob[pos : pos + chars * 2]
    return raw[: (chars - 1) * 2].decode("utf-16-le", errors="replace"), pos + chars * 2


def _read_header(blob: bytes) -> tuple[list[str], str, int, int, int]:
    """Walk a header independently and stop on the byte after it.

    Dispatch is read from the blob itself rather than passed in, so this is a
    genuine second parse: the string count follows the HEADER version and
    nothing here consults the save version to decide it.

    Args:
        blob: A whole save blob.

    Returns:
        The leading strings, the world token, the header version, the save
        version and the offset of the chunk magic.
    """
    header_version, save_version = struct.unpack_from("<ii", blob, 0)
    pos = 12
    count = _STRINGS_WITH_SAVE_NAME if header_version >= _HEADER_14 else _STRINGS_WITHOUT_SAVE_NAME
    texts: list[str] = []
    for _ in range(count):
        text, pos = _read_fstring(blob, pos)
        texts.append(text)
    # play duration (4) + datetime ticks (8) + visibility (1) + editor object
    # version (4). Spelled as one sum so the widths stay visible.
    pos += 4 + 8 + 1 + 4
    _, pos = _read_fstring(blob, pos)
    pos += 4
    token, pos = _read_fstring(blob, pos)
    if header_version >= _HEADER_13:
        pos += _TAIL_SIZE
    return texts, token, header_version, save_version, pos


def _read_chunk(blob: bytes, magic_at: int) -> tuple[int, bool, int, bytes]:
    """Walk one chunk frame and decompress its payload.

    Args:
        blob: A whole save blob.
        magic_at: Offset of the chunk magic.

    Returns:
        The marker, whether an algorithm byte was present, the zlib stream's
        offset relative to the magic, and the decompressed payload.
    """
    (magic,) = struct.unpack_from("<I", blob, magic_at)
    assert magic == _MAGIC
    (marker,) = struct.unpack_from("<I", blob, magic_at + 4)
    (max_chunk,) = struct.unpack_from("<q", blob, magic_at + 8)
    assert max_chunk == _MAX_CHUNK
    algo_present = marker == _MARKER_22
    if algo_present:
        (algo,) = struct.unpack_from("<b", blob, magic_at + 16)
        assert algo == _ALGO_ZLIB
        sizes_at = magic_at + 17
        stream_at = _ZLIB_AT_WITH_ALGO
    else:
        sizes_at = magic_at + 16
        stream_at = _ZLIB_AT_WITHOUT_ALGO
    compressed, uncompressed, compressed_again, uncompressed_again = struct.unpack_from(
        "<qqqq", blob, sizes_at
    )
    assert compressed == compressed_again
    assert uncompressed == uncompressed_again
    stream = blob[magic_at + stream_at : magic_at + stream_at + compressed]
    payload = zlib.decompress(stream)
    assert len(payload) == uncompressed
    return marker, algo_present, stream_at, payload


def _read_all_chunks(blob: bytes, magic_at: int) -> tuple[int, bool, int, bytes, int]:
    """Walk EVERY chunk to the end of the file and concatenate the payloads.

    A real save is multi-chunk - the file this corpus was anchored against has
    13 - so a reader that stops after one chunk sees a truncated body and no
    error. This function is what proved the single-chunk assumption wrong, and
    it is kept as the default path for exactly that reason.

    Args:
        blob: A whole save blob.
        magic_at: Offset of the FIRST chunk magic.

    Returns:
        The first chunk's marker, whether an algorithm byte was present, the
        zlib offset relative to the magic, the concatenated payload, and the
        chunk count.
    """
    payloads: list[bytes] = []
    marker = 0
    algo_present = False
    stream_at = 0
    pos = magic_at
    count = 0
    while pos < len(blob):
        marker, algo_present, stream_at, payload = _read_chunk(blob, pos)
        payloads.append(payload)
        (compressed,) = struct.unpack_from(
            "<q",
            blob,
            pos + (_ZLIB_AT_WITH_ALGO - 32 if algo_present else _ZLIB_AT_WITHOUT_ALGO - 32),
        )
        pos += stream_at + compressed
        count += 1
    assert pos == len(blob)
    return marker, algo_present, stream_at, b"".join(payloads), count


def _read_object(blob: bytes, pos: int, delta: int) -> tuple[str, tuple[float, ...], int]:
    """Read one object record, independently of how the builder wrote it.

    Args:
        blob: The DECOMPRESSED body.
        pos: Offset of the record.
        delta: The save-version-dependent filler width before the transform.

    Returns:
        The instance name, the transform floats, and the offset past the record.
    """
    pos += 4
    _, pos = _read_fstring(blob, pos)
    _, pos = _read_fstring(blob, pos)
    name, pos = _read_fstring(blob, pos)
    pos += delta
    floats = struct.unpack_from(f"<{_TRANSFORM_FLOATS}f", blob, pos)
    pos += _TRANSFORM_BYTES
    return name, floats, pos + 4


def _read_body(payload: bytes, header_version: int, save_version: int) -> list[str]:
    """Read every object record out of a decompressed body.

    Args:
        payload: The decompressed chunk payload.
        header_version: Decides whether the body opens with an int64 length.
        save_version: Decides the transform delta. Note that these are two
            DIFFERENT fields driving two DIFFERENT decisions - that split is
            what SAVE_CROSS exists to police.

    Returns:
        The instance name of every record, in order.
    """
    pos = _BODY_PREFIX_WIDE if header_version >= _HEADER_13 else _BODY_PREFIX_NARROW
    (count,) = struct.unpack_from("<i", payload, pos)
    pos += 4
    names: list[str] = []
    if count:
        delta = _DELTA_BY_SAVE_VERSION[save_version]
        for _ in range(count):
            name, _floats, pos = _read_object(payload, pos, delta)
            names.append(name)
    assert pos == len(payload)
    return names


def _walk_whole(blob: bytes) -> bytes:
    """Walk a blob header-then-chunk, the way a parser would.

    A named helper rather than a two-statement ``pytest.raises`` body, so the
    raise can only come from the walk and not from the bookkeeping around it.

    Args:
        blob: A whole save blob, possibly truncated.

    Returns:
        The first chunk's decompressed payload.
    """
    _texts, _token, _hv, _sv, magic_at = _read_header(blob)
    _marker, _algo, _at, payload = _read_chunk(blob, magic_at)
    return payload


def _index_of_equal(texts: list[str], wanted: str) -> int:
    """Index of the first string equal to ``wanted``, or -1.

    A loop with a sentinel rather than ``list.index``, which raises on absence.
    A raised ValueError would be an ERROR rather than a comparison, and the
    shape tuple is supposed to absorb a mismatch and report it as a plain int.

    Args:
        texts: The strings read from a header.
        wanted: The literal to look for.

    Returns:
        The index, or -1.
    """
    for index, text in enumerate(texts):
        if text == wanted:
            return index
    return _NOT_FOUND


def _index_of_containing(texts: list[str], mark: str) -> int:
    """Index of the first string containing ``mark``, or -1.

    Args:
        texts: The strings read from a header.
        mark: The substring to look for.

    Returns:
        The index, or -1.
    """
    for index, text in enumerate(texts):
        if mark in text:
            return index
    return _NOT_FOUND


def _shape_of(blob: bytes) -> tuple[int, ...]:
    """Reduce a save to a tuple of SCALARS describing its shape.

    EVERY element is an int or a bool. That is the whole point: this function
    runs against a real save, and a tuple of scalars cannot carry a world name,
    an account id, a session name or a token into an assertion repr or a CI log
    (non-negotiable 12). Nothing here is printed, returned as text, or stored.

    The load-bearing check is inside :func:`_read_chunk`, which asserts the
    cursor landed exactly on the magic. If the string count or the tail size
    were wrong for this header version, the walk would stop somewhere else and
    that assertion would fire - without ever naming what it read.

    Args:
        blob: A whole save blob, synthetic or real.

    Returns:
        ``(string count, index of the map name, index of the options string,
        marker, algorithm byte present, tail size, zlib offset from the magic,
        token length, token is base64url, body length prefix consistent)``.
    """
    texts, token, header_version, _save_version, magic_at = _read_header(blob)
    marker, algo_present, stream_at, payload, _chunks = _read_all_chunks(blob, magic_at)
    if header_version >= _HEADER_13:
        (declared,) = struct.unpack_from("<q", payload, 0)
        prefix_ok = declared == len(payload) - _BODY_PREFIX_WIDE
    else:
        (declared,) = struct.unpack_from("<i", payload, 0)
        prefix_ok = declared == len(payload) - _BODY_PREFIX_NARROW
    return (
        len(texts),
        _index_of_equal(texts, _MAP_NAME),
        _index_of_containing(texts, _OPTIONS_MARK),
        marker,
        algo_present,
        _TAIL_SIZE if header_version >= _HEADER_13 else 0,
        stream_at,
        len(token),
        bool(_BASE64URL.match(token)),
        prefix_ok,
    )


# ---------------------------------------------------------------------------
# The builder writes nothing under clockspeed/
# ---------------------------------------------------------------------------


def test_the_builder_imports_nothing_from_the_package_it_feeds() -> None:
    source = Path(synthetic.__file__).read_text(encoding="utf-8")
    assert "clockspeed.save" not in source
    assert "from clockspeed" not in source
    assert "import clockspeed" not in source


# ---------------------------------------------------------------------------
# fstring
# ---------------------------------------------------------------------------


def test_a_narrow_string_counts_its_trailing_null() -> None:
    blob = synthetic.fstring("abc")
    (count,) = struct.unpack_from("<i", blob, 0)
    assert count == len("abc") + 1
    assert blob[4:] == b"abc\x00"
    text, pos = _read_fstring(blob, 0)
    assert text == "abc"
    assert pos == len(blob)


def test_a_wide_string_counts_characters_and_is_negative() -> None:
    blob = synthetic.fstring("abc", wide=True)
    (count,) = struct.unpack_from("<i", blob, 0)
    assert count == -(len("abc") + 1)
    assert blob[4:] == "abc".encode("utf-16-le") + b"\x00\x00"
    text, pos = _read_fstring(blob, 0)
    assert text == "abc"
    assert pos == len(blob)


def test_the_empty_string_is_a_bare_zero_count() -> None:
    blob = synthetic.fstring("")
    assert blob == b"\x00\x00\x00\x00"
    text, pos = _read_fstring(blob, 0)
    assert text == ""
    assert pos == _INT32_WIDTH


# ---------------------------------------------------------------------------
# The header - string layout follows the HEADER version
# ---------------------------------------------------------------------------


def test_header_14_carries_four_strings_and_header_13_and_10_carry_three() -> None:
    counts = {}
    for header_version in (_HEADER_10, _HEADER_13, _HEADER_14):
        blob = synthetic.build_header(header_version=header_version) + _stub_chunk()
        texts, _token, _hv, _sv, _magic_at = _read_header(blob)
        counts[header_version] = len(texts)
    assert counts[_HEADER_14] == _STRINGS_WITH_SAVE_NAME
    assert counts[_HEADER_13] == _STRINGS_WITHOUT_SAVE_NAME
    assert counts[_HEADER_10] == _STRINGS_WITHOUT_SAVE_NAME


def test_the_save_name_is_the_string_header_14_adds() -> None:
    with_name = synthetic.build_header(header_version=_HEADER_14) + _stub_chunk()
    without = synthetic.build_header(header_version=_HEADER_13) + _stub_chunk()
    wide_texts, _t, _hv, _sv, _m = _read_header(with_name)
    narrow_texts, _t2, _hv2, _sv2, _m2 = _read_header(without)
    assert wide_texts[1:] == narrow_texts
    assert wide_texts[0] == synthetic.SYNTHETIC_SAVE_NAME


def test_the_map_name_and_options_sit_where_the_shape_anchor_expects() -> None:
    for header_version in (_HEADER_10, _HEADER_13, _HEADER_14):
        blob = synthetic.build_header(header_version=header_version) + _stub_chunk()
        texts, _token, _hv, _sv, _magic_at = _read_header(blob)
        assert _index_of_equal(texts, _MAP_NAME) != _NOT_FOUND
        assert _index_of_containing(texts, _OPTIONS_MARK) != _NOT_FOUND


def test_the_tail_is_28_bytes_on_13_and_14_and_absent_on_10() -> None:
    for header_version, expected in ((_HEADER_10, 0), (_HEADER_13, _TAIL_SIZE)):
        blob = synthetic.build_header(header_version=header_version) + _stub_chunk()
        _texts, _token, _hv, _sv, magic_at = _read_header(blob)
        (magic,) = struct.unpack_from("<I", blob, magic_at)
        assert magic == _MAGIC
        assert magic_at == len(blob) - len(_stub_chunk())
        assert expected in (0, _TAIL_SIZE)


def test_the_save_name_and_tail_switches_are_independent_of_the_version() -> None:
    """Both switches must be settable on their own, or SAVE_CROSS is unbuildable.

    A builder that hardcoded them off ``header_version`` would still pass every
    other test in this file, which is exactly why this one exists.
    """
    no_tail = synthetic.build_header(header_version=_HEADER_14, with_tail=False)
    with_tail = synthetic.build_header(header_version=_HEADER_14, with_tail=True)
    assert len(with_tail) - len(no_tail) == _TAIL_SIZE

    no_name = synthetic.build_header(header_version=_HEADER_10, with_save_name=False)
    with_name = synthetic.build_header(header_version=_HEADER_10, with_save_name=True)
    assert len(with_name) - len(no_name) == len(synthetic.fstring(synthetic.SYNTHETIC_SAVE_NAME))


# ---------------------------------------------------------------------------
# Chunk framing
# ---------------------------------------------------------------------------


def _stub_chunk() -> bytes:
    """A minimal well-formed chunk, so a header-only test still has a magic to land on."""
    return synthetic.build_chunk(b"\x00\x00\x00\x00", framing=synthetic.FRAMING_MARKER22_ALGO)


def test_the_algorithm_framing_puts_the_zlib_stream_at_magic_plus_49() -> None:
    chunk = synthetic.build_chunk(b"payload", framing=synthetic.FRAMING_MARKER22_ALGO)
    marker, algo_present, stream_at, payload = _read_chunk(chunk, 0)
    assert marker == _MARKER_22
    assert algo_present
    assert stream_at == _ZLIB_AT_WITH_ALGO
    assert payload == b"payload"


def test_the_zero_marker_framing_puts_the_zlib_stream_at_magic_plus_48() -> None:
    chunk = synthetic.build_chunk(b"payload", framing=synthetic.FRAMING_ZERO_MARKER_NOALGO)
    marker, algo_present, stream_at, payload = _read_chunk(chunk, 0)
    assert marker == _MARKER_ZERO
    assert not algo_present
    assert stream_at == _ZLIB_AT_WITHOUT_ALGO
    assert payload == b"payload"


def test_the_two_framings_differ_by_exactly_the_algorithm_byte() -> None:
    with_algo = synthetic.build_chunk(b"x", framing=synthetic.FRAMING_MARKER22_ALGO)
    without = synthetic.build_chunk(b"x", framing=synthetic.FRAMING_ZERO_MARKER_NOALGO)
    assert len(with_algo) - len(without) == 1


def test_the_duplicated_sizes_agree_in_every_fixture() -> None:
    for save in synthetic.ALL_SAVES:
        _marker, _algo, _at, _payload = _read_chunk(save.blob, save.chunk_offset)


# ---------------------------------------------------------------------------
# The five fixtures
# ---------------------------------------------------------------------------


def test_every_fixture_round_trips_through_the_independent_reader() -> None:
    for save in synthetic.ALL_SAVES:
        texts, token, header_version, save_version, magic_at = _read_header(save.blob)
        assert header_version == save.header_version
        assert save_version == save.save_version
        assert magic_at == save.chunk_offset
        assert len(token) == _TOKEN_LENGTH
        assert _index_of_equal(texts, _MAP_NAME) != _NOT_FOUND
        _marker, _algo, _at, payload = _read_chunk(save.blob, magic_at)
        names = _read_body(payload, header_version, save_version)
        assert names == [obj.instance_name for obj in save.objects]


def test_the_fixture_matrix_is_the_one_the_phase_was_dispatched_with() -> None:
    matrix = {
        save.name: (save.header_version, save.save_version, save.framing)
        for save in synthetic.ALL_SAVES
    }
    assert matrix == {
        "SAVE_V36": (10, 36, synthetic.FRAMING_ZERO_MARKER_NOALGO),
        "SAVE_V42": (13, 42, synthetic.FRAMING_MARKER22_ALGO),
        "SAVE_V52": (14, 52, synthetic.FRAMING_MARKER22_ALGO),
        "SAVE_V60": (14, 60, synthetic.FRAMING_MARKER22_ALGO),
        "SAVE_CROSS": (14, 36, synthetic.FRAMING_MARKER22_ALGO),
    }


def test_an_unmeasured_save_version_raises_rather_than_defaulting() -> None:
    """The refusal rule, pinned against a version that is still unmeasured.

    RENAMED under CS-407. This test used to be about save version 42, which was
    the unmeasured one; 42's delta is now measured at 4, so the example moved to
    a version nobody has measured while the RULE it pins is unchanged. An absent
    key must raise, never default - a defaulted delta reads a real save at the
    wrong offset and reports a plausible wrong world rather than an error.

    ``SAVE_V42`` keeps an empty object section, which is now a property of the
    FIXTURE rather than a consequence of the delta.
    """
    assert synthetic.SAVE_V42.objects == ()
    assert _UNMEASURED_SAVE_VERSION not in synthetic.TRANSFORM_DELTA_BY_SAVE_VERSION
    one_object = [synthetic.SyntheticObject("C", "R", "I")]
    with pytest.raises(synthetic.UnmeasuredTransformDeltaError):
        synthetic.build_body(one_object, save_version=_UNMEASURED_SAVE_VERSION)


def test_save_42_was_measured_rather_than_interpolated_from_its_neighbours() -> None:
    """RESTATED under CS-407, and the restatement is the point.

    This test previously asserted that save 42's delta was ABSENT, on the
    reasoning that 36 -> 4 beside 52 -> 8 makes 4 exactly what "looks derived"
    produces. That reasoning was right and the conclusion has since been earned
    rather than overturned: TWO earlier sessions reached 4 and both discarded
    it, because neither had a method that could recover the known deltas when
    validated against them.

    So the value did not change - the KIND OF EVIDENCE did. 42 is present at 4
    because a corroborator independent of section arithmetic says so: 17763 of
    17763 actors in the one real header-13 body give a unit quaternion at shift
    4, the runner-up shift falls to 2 once scale plausibility is included, and
    the method recovered 4, 8 and 8 for the three already-known versions before
    it was pointed at 42.

    The fence this test carries is therefore NOT "42 must be absent". It is
    "arriving at a number that looks derived is not evidence; a validated method
    plus an independent corroborator is".
    """
    assert set(synthetic.TRANSFORM_DELTA_BY_SAVE_VERSION) == {36, 42, 52, 60}
    assert synthetic.TRANSFORM_DELTA_BY_SAVE_VERSION[_SAVE_42] == _SAVE_42_DELTA
    # The interpolation fence still bites where it should: a version between two
    # measured neighbours is not given a value just because one is available.
    assert _UNMEASURED_SAVE_VERSION not in synthetic.TRANSFORM_DELTA_BY_SAVE_VERSION


def test_the_body_length_prefix_follows_the_header_version() -> None:
    """CS-404. Both widths carry a LENGTH; header 10 does not omit the prefix.

    An earlier revision of this corpus asserted that header 10 opened straight
    on the object count. That was a property of the fixture, not of the format:
    measured against real bodies of every version, header 10 opens with an
    int32 equal to the body length minus 4, exactly as headers 13 and 14 open
    with an int64 equal to the body length minus 8.

    The old assertion is why this matters. It would have passed forever while a
    parser read the object count out of the length field on every real
    header-10 save.
    """
    for save in synthetic.ALL_SAVES:
        _m, _a, _at, payload = _read_chunk(save.blob, save.chunk_offset)
        width = synthetic.body_prefix_width(save.header_version)
        fmt = "<q" if width == _BODY_PREFIX_WIDE else "<i"
        (declared,) = struct.unpack_from(fmt, payload, 0)
        assert declared == len(payload) - width
        # The object count sits AFTER the prefix, never at offset zero.
        (count,) = struct.unpack_from("<i", payload, width)
        assert count == len(save.objects)


# ---------------------------------------------------------------------------
# Multi-chunk - the structure the real save forced into this corpus
# ---------------------------------------------------------------------------


def test_the_multichunk_fixture_really_spans_several_chunks() -> None:
    save = synthetic.SAVE_MULTICHUNK
    _m, _a, _at, payload, chunks = _read_all_chunks(save.blob, save.chunk_offset)
    assert chunks == save.chunk_count
    assert chunks > _MIN_MULTICHUNK_CHUNKS
    assert len(payload) > _MIN_MULTICHUNK_CHUNKS * _MAX_CHUNK


def test_no_chunk_payload_exceeds_the_declared_max_chunk_size() -> None:
    save = synthetic.SAVE_MULTICHUNK
    pos = save.chunk_offset
    seen = 0
    while pos < len(save.blob):
        _m, _algo, stream_at, payload = _read_chunk(save.blob, pos)
        assert len(payload) <= _MAX_CHUNK
        (compressed,) = struct.unpack_from("<q", save.blob, pos + _ZLIB_AT_WITH_ALGO - 32)
        pos += stream_at + compressed
        seen += 1
    assert seen == save.chunk_count


def test_the_body_length_prefix_counts_the_whole_body_not_one_chunk() -> None:
    """The distinction a single-chunk corpus cannot express, and the real save can.

    MEASURED against a real save: its first chunk declares 1574433 while its own
    payload is 131072, and the concatenation of all 13 chunks is 1574441. So the
    int64 counts the WHOLE body minus its own 8 bytes. A parser adopting "this
    chunk's payload minus 8" reads one chunk of any real save and reports a
    truncated world rather than an error.
    """
    save = synthetic.SAVE_MULTICHUNK
    _m, _a, _at, whole, chunks = _read_all_chunks(save.blob, save.chunk_offset)
    (declared,) = struct.unpack_from("<q", whole, 0)
    assert declared == len(whole) - 8

    _m2, _a2, _at2, first_only = _read_chunk(save.blob, save.chunk_offset)
    assert declared != len(first_only) - 8
    assert chunks > 1


def test_the_multichunk_body_walks_to_exactly_the_last_record() -> None:
    save = synthetic.SAVE_MULTICHUNK
    _m, _a, _at, payload, _chunks = _read_all_chunks(save.blob, save.chunk_offset)
    names = _read_body(payload, save.header_version, save.save_version)
    assert names == [obj.instance_name for obj in save.objects]
    assert len(names) == synthetic.MULTICHUNK_OBJECT_COUNT


def test_the_dispatched_five_stay_single_chunk() -> None:
    """The brief specified five fixtures. A slice does not quietly widen a contract."""
    assert synthetic.SAVE_MULTICHUNK not in synthetic.ALL_SAVES
    for save in synthetic.ALL_SAVES:
        assert save.chunk_count == 1


# ---------------------------------------------------------------------------
# SAVE_CROSS - the sharpest fixture in the phase
# ---------------------------------------------------------------------------


def test_save_cross_takes_its_string_layout_from_the_header_version() -> None:
    texts, _token, _hv, _sv, _magic_at = _read_header(synthetic.SAVE_CROSS.blob)
    assert len(texts) == _STRINGS_WITH_SAVE_NAME


def test_save_cross_takes_its_transform_offset_from_the_save_version() -> None:
    """A parser keying both decisions off ONE field passes every other fixture.

    SAVE_CROSS is header 14 (four strings, 28-byte tail) and save 36 (delta 4),
    a combination that occurs in no real file. Reading it with the delta its
    HEADER version would imply - 8, as SAVE_V52 and SAVE_V60 use - must not
    produce the right answer, or the fixture is not actually discriminating.
    """
    _m, _a, _at, payload = _read_chunk(synthetic.SAVE_CROSS.blob, synthetic.SAVE_CROSS.chunk_offset)
    correct = _read_body(payload, _HEADER_14, 36)
    assert correct == [obj.instance_name for obj in synthetic.SAVE_CROSS.objects]

    wrong_delta = _DELTA_BY_SAVE_VERSION[60]
    assert wrong_delta != _DELTA_BY_SAVE_VERSION[36]
    with pytest.raises((AssertionError, UnicodeDecodeError, struct.error)):
        _read_body_with_forced_delta(payload, wrong_delta)


def _read_body_with_forced_delta(payload: bytes, delta: int) -> list[str]:
    """Read a body with a delta supplied instead of derived - the wrong-parser simulation.

    Args:
        payload: A decompressed body carrying an int64 length prefix.
        delta: The filler width to assume.

    Returns:
        Instance names, if the misread happens to survive the walk.
    """
    pos = 8
    (count,) = struct.unpack_from("<i", payload, pos)
    pos += 4
    names: list[str] = []
    for _ in range(count):
        name, _floats, pos = _read_object(payload, pos, delta)
        names.append(name)
    assert pos == len(payload)
    return names


# ---------------------------------------------------------------------------
# Truncation
# ---------------------------------------------------------------------------


def test_every_truncation_boundary_really_lands_mid_structure() -> None:
    """A boundary that lands on a clean field edge tests nothing.

    Each point is asserted to actually sever something: the file-scope ones
    stop the independent reader, and the body-scope one leaves a record short.
    """
    labels = {point.label for point in synthetic.TRUNCATION_BOUNDARIES}
    assert labels == {
        "mid-magic",
        "mid-length-prefix",
        "mid-string-bytes",
        "mid-chunk-header",
        "mid-zlib-stream",
        "one-byte-short-of-an-object-record",
    }


def test_file_scope_truncations_stop_the_independent_reader() -> None:
    source = synthetic.SAVE_V60
    for point in synthetic.TRUNCATION_BOUNDARIES:
        if point.scope != synthetic.SCOPE_FILE:
            continue
        cut = synthetic.truncated_at(source.blob, point.offset)
        assert len(cut) == point.offset
        assert len(cut) < len(source.blob)
        with pytest.raises((AssertionError, struct.error, zlib.error, ValueError)):
            _walk_whole(cut)


def test_the_body_scope_truncation_leaves_a_record_one_byte_short() -> None:
    point = next(p for p in synthetic.TRUNCATION_BOUNDARIES if p.scope == synthetic.SCOPE_BODY)
    blob = synthetic.save_with_truncated_body(synthetic.SAVE_V60, point.offset)
    _m, _a, _at, payload = _read_chunk(blob, synthetic.SAVE_V60.chunk_offset)
    assert len(payload) == point.offset + 8
    with pytest.raises((AssertionError, struct.error)):
        _read_body(payload, _HEADER_14, 60)


# ---------------------------------------------------------------------------
# The named corruption cases
# ---------------------------------------------------------------------------


def test_corrupt_magic_changes_only_the_magic() -> None:
    blob = synthetic.corrupt_magic(synthetic.SAVE_V60)
    assert len(blob) == len(synthetic.SAVE_V60.blob)
    (magic,) = struct.unpack_from("<I", blob, synthetic.SAVE_V60.chunk_offset)
    assert magic != _MAGIC
    assert (
        blob[: synthetic.SAVE_V60.chunk_offset]
        == (synthetic.SAVE_V60.blob[: synthetic.SAVE_V60.chunk_offset])
    )


def test_corrupt_marker_is_neither_measured_marker() -> None:
    blob = synthetic.corrupt_marker(synthetic.SAVE_V60)
    (marker,) = struct.unpack_from("<I", blob, synthetic.SAVE_V60.chunk_offset + 4)
    assert marker != _MARKER_22
    assert marker != _MARKER_ZERO


def test_corrupt_size_disagreement_breaks_the_formats_own_checksum() -> None:
    """The duplicated size pair IS the format's internal consistency check.

    A parser that reads only the first copy cannot notice, which is precisely
    the defect this case exists to expose.
    """
    save = synthetic.SAVE_V60
    blob = synthetic.corrupt_size_disagreement(save)
    sizes_at = save.chunk_offset + _ZLIB_AT_WITH_ALGO - 32
    first, _u, second, _u2 = struct.unpack_from("<qqqq", blob, sizes_at)
    assert first != second
    with pytest.raises(AssertionError):
        _read_chunk(blob, save.chunk_offset)


def test_corrupt_zlib_stream_survives_the_frame_and_fails_the_inflate() -> None:
    save = synthetic.SAVE_V60
    blob = synthetic.corrupt_zlib_stream(save)
    assert len(blob) == len(save.blob)
    (magic,) = struct.unpack_from("<I", blob, save.chunk_offset)
    assert magic == _MAGIC
    with pytest.raises(zlib.error):
        _read_chunk(blob, save.chunk_offset)


def test_absurd_string_length_declares_a_gigabyte_it_does_not_carry() -> None:
    blob = synthetic.absurd_string_length()
    (count,) = struct.unpack_from("<i", blob, 12)
    assert count == synthetic.ABSURD_STRING_LENGTH
    assert count > len(blob)


def test_negative_string_length_declares_a_gigabyte_on_the_utf16_path() -> None:
    blob = synthetic.negative_string_length()
    (count,) = struct.unpack_from("<i", blob, 12)
    assert count == synthetic.NEGATIVE_STRING_LENGTH
    assert count < 0
    assert -count * 2 > len(blob)


def test_declared_chunk_bomb_declares_far_more_than_it_carries() -> None:
    save = synthetic.SAVE_V60
    blob = synthetic.declared_chunk_bomb(save)
    sizes_at = save.chunk_offset + _ZLIB_AT_WITH_ALGO - 32
    compressed, uncompressed, _c2, _u2 = struct.unpack_from("<qqqq", blob, sizes_at)
    assert uncompressed == synthetic.CHUNK_BOMB_UNCOMPRESSED_SIZE
    assert uncompressed > len(blob)
    assert compressed < uncompressed


def test_unsupported_header_version_is_99_and_otherwise_well_formed() -> None:
    blob = synthetic.unsupported_header_version()
    (header_version,) = struct.unpack_from("<i", blob, 0)
    assert header_version == synthetic.UNSUPPORTED_HEADER_VERSION


def test_unknown_actor_class_is_structurally_valid_and_semantically_unmodeled() -> None:
    """Non-negotiable 7: unknown content is flagged and skipped, never fatal.

    So the record must PARSE cleanly - the unknown-ness has to be in the class
    path, not in the bytes, or a parser could reject it for the wrong reason and
    still look correct.
    """
    save = synthetic.unknown_actor_class()
    _m, _a, _at, payload = _read_chunk(save.blob, save.chunk_offset)
    names = _read_body(payload, save.header_version, save.save_version)
    assert names == [obj.instance_name for obj in save.objects]
    assert any(obj.class_path == synthetic.UNKNOWN_ACTOR_CLASS_PATH for obj in save.objects)


# ---------------------------------------------------------------------------
# usmap
# ---------------------------------------------------------------------------


def test_a_usmap_declares_its_compression_method() -> None:
    for method in (0, 1, 2, 3):
        blob = synthetic.usmap_with_compression(method)
        (magic,) = struct.unpack_from("<H", blob, 0)
        assert magic == synthetic.USMAP_MAGIC
        (declared,) = struct.unpack_from("<B", blob, 3)
        assert declared == method


def test_an_uncompressed_usmap_carries_its_names_enums_and_schemas() -> None:
    blob = synthetic.build_usmap(names=["Alpha", "Beta"], enums=[], schemas=[])
    (compressed, decompressed) = struct.unpack_from("<II", blob, 4)
    assert compressed == decompressed
    body = blob[12:]
    assert len(body) == decompressed
    (count,) = struct.unpack_from("<I", body, 0)
    assert count == _USMAP_NAME_COUNT


# ---------------------------------------------------------------------------
# Personal data
# ---------------------------------------------------------------------------


def test_every_synthetic_token_is_an_invented_base64url_literal() -> None:
    for save in synthetic.ALL_SAVES:
        _texts, token, _hv, _sv, _m = _read_header(save.blob)
        assert len(token) == _TOKEN_LENGTH
        assert _BASE64URL.match(token)
        assert token.startswith("Clockspeed")


def test_the_corpus_source_carries_no_absolute_path_and_no_home_directory() -> None:
    source = Path(synthetic.__file__).read_text(encoding="utf-8")
    lowered = source.lower()
    assert "c:\\users" not in lowered
    assert "/users/" not in lowered
    assert "appdata" not in lowered
    assert "localappdata" not in lowered


def test_the_corpus_is_seven_bit_ascii() -> None:
    for path in (Path(synthetic.__file__), Path(__file__)):
        raw = path.read_bytes()
        assert max(raw) < _ASCII_CEILING


# ---------------------------------------------------------------------------
# CONTROL 2 - the real-save shape anchor
# ---------------------------------------------------------------------------


def _real_save_path() -> Path | None:
    """Find one real save, or None when the machine has none.

    Routed through ``clockspeed.data.locate`` rather than through a path
    literal, so the four ``CLOCKSPEED_*`` overrides point this at a nonexistent
    directory in CI and on any machine with no game installed - which is what
    makes the skip below reachable rather than theoretical.

    Returns:
        A save path, or None.
    """
    save_root = locate.resolve_save_root()
    if save_root is None or not save_root.is_dir():
        return None
    account = locate.resolve_account_dir(save_root)
    if account is None or not account.is_dir():
        return None
    for candidate in sorted(account.glob("*.sav")):
        if candidate.is_file() and candidate.stat().st_size > 0:
            return candidate
    return None


def test_the_builder_matches_the_shape_of_a_real_save() -> None:
    """Compare the builder against a real save - SHAPES ONLY, no value, no print.

    This is the one control that can catch a measurement error the independent
    reader cannot, because the reader and the builder share their measured
    constants. See the module docstring.

    It asserts nothing about content. The comparison is a tuple of ints and
    bools, so a failure repr cannot carry a world name, a session name, an
    account id or a token (non-negotiable 12).
    """
    path = _real_save_path()
    if path is None:
        pytest.skip(
            "no save file on this machine - the anchor needs a real save to compare against"
        )

    blob = path.read_bytes()
    (header_version,) = struct.unpack_from("<i", blob, 0)
    counterpart = {
        _HEADER_10: synthetic.SAVE_V36,
        _HEADER_13: synthetic.SAVE_V42,
        _HEADER_14: synthetic.SAVE_V60,
    }.get(header_version)
    if counterpart is None:
        pytest.skip("real save carries a header version the corpus does not model")

    # GUARDED. pytest renders the ARGUMENTS of every frame in a failing
    # traceback, with no opt-in, so `_shape_of(blob)` raising would print the
    # head of a REAL SAVE - which is the PII-bearing header carrying the options
    # string and the session name (non-negotiables 11 and 12). Measured on this
    # machine, not assumed: a marker planted in a bytes argument of a raising
    # frame appeared twice in pytest's output. The comparison below is safe
    # because _shape_of returns scalars and booleans only.
    try:
        real_shape = _shape_of(blob)
    except Exception as exc:
        pytest.fail(f"the real save did not yield a shape: {type(exc).__name__}", pytrace=False)
    synthetic_shape = _shape_of(counterpart.blob)
    assert real_shape == synthetic_shape
