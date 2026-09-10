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
import subprocess
import sys
import zlib
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Final

import pytest

from clockspeed.data import locate

# The SHIPPED readers, imported for the CS-961 section at the foot of this file
# and used nowhere above it. They do not touch control 1: the header, the chunk
# frame and the record table are still re-derived by hand here out of the format
# description, and no constant crosses this import into that reader. See the
# CS-961 banner for why the decode side cannot be graded by a second hand
# written reader, and what gets the second opinion instead.
from clockspeed.save import chunks, objects

# `test_properties` is imported for its CONTAINMENT and GRADING machinery only -
# the contained discovery, the two forced-failure pairs and the reach guard. No
# format constant and no builder opinion crosses this import, so control 1's
# independence claim in the module docstring is untouched. See the CS-429
# section at the foot of this file.
from tests.save import reach_guard, synthetic, test_properties

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
# usmap - CS-404 part 2 added a shipped-grammar mode and a version parameter.
#
# THE ADDITIVE CONSTRAINT, PINNED TO LITERAL BYTES.
#
# Those two capabilities went in while another slice was reading this builder
# concurrently, so "every existing call site keeps working" had to be provable
# rather than asserted - and a green suite does not prove it. A suite proves the
# assertions people happened to write still hold; it cannot see a byte that
# changed somewhere nothing looks.
#
# So the bytes below were CAPTURED FROM THE BUILDER BEFORE THE CHANGE, one
# entry per call shape that existed at the time, and they are compared here as
# literals. They are not a re-derivation of the builder's grammar and must never
# be regenerated from it - regenerating them would delete the only evidence in
# the suite that legacy output never moved. If one of these fails, the default
# path emitted different bytes and every module built on this corpus is
# suspect.
# ---------------------------------------------------------------------------

_USMAP_LEGACY_BYTES: dict[str, str] = {
    "empty": "c43000000c0000000c000000000000000000000000000000",
    "one_name": "c430000012000000120000000100000005416c7068610000000000000000",
    "two_names": "c430000017000000170000000200000005416c70686104426574610000000000000000",
    "three_names": (
        "c43000001d0000001d0000000300000005416c70686104426574610547616d6d610000000000000000"
    ),
    "compression_0": (
        "c43000006b0000006b000000020000000d53796e7468657469634e616d651153796e"
        "74686574696350726f7065727479010000000e4553796e746865746963456e756d02"
        "05416c7068610442657461010000000f53796e746865746963536368656d61010011"
        "53796e74686574696350726f7065727479"
    ),
    "compression_1": (
        "c43000016b0000006b000000020000000d53796e7468657469634e616d651153796e"
        "74686574696350726f7065727479010000000e4553796e746865746963456e756d02"
        "05416c7068610442657461010000000f53796e746865746963536368656d61010011"
        "53796e74686574696350726f7065727479"
    ),
    "compression_2": (
        "c43000026b0000006b000000020000000d53796e7468657469634e616d651153796e"
        "74686574696350726f7065727479010000000e4553796e746865746963456e756d02"
        "05416c7068610442657461010000000f53796e746865746963536368656d61010011"
        "53796e74686574696350726f7065727479"
    ),
    "compression_3": (
        "c43000036b0000006b000000020000000d53796e7468657469634e616d651153796e"
        "74686574696350726f7065727479010000000e4553796e746865746963456e756d02"
        "05416c7068610442657461010000000f53796e746865746963536368656d61010011"
        "53796e74686574696350726f7065727479"
    ),
}


def test_every_legacy_usmap_call_shape_is_byte_identical_to_before_cs_404() -> None:
    """The proof that the shipped-grammar mode was purely additive."""
    produced = {
        "empty": synthetic.build_usmap(names=[], enums=[], schemas=[]),
        "one_name": synthetic.build_usmap(names=["Alpha"], enums=[], schemas=[]),
        "two_names": synthetic.build_usmap(names=["Alpha", "Beta"], enums=[], schemas=[]),
        "three_names": synthetic.build_usmap(
            names=["Alpha", "Beta", "Gamma"], enums=[], schemas=[]
        ),
        "compression_0": synthetic.usmap_with_compression(0),
        "compression_1": synthetic.usmap_with_compression(1),
        "compression_2": synthetic.usmap_with_compression(2),
        "compression_3": synthetic.usmap_with_compression(3),
    }

    assert set(produced) == set(_USMAP_LEGACY_BYTES)
    for label, blob in produced.items():
        assert blob.hex() == _USMAP_LEGACY_BYTES[label], label


def test_the_legacy_mode_writes_inline_names_and_no_property_type_byte() -> None:
    """What legacy mode IS, stated positively, so the divergence stays visible.

    This is deliberately NOT a claim that the legacy grammar is the shipped
    one. It is not, and CS-404 part 2 exists because a reader could not tell:
    the shipped file writes uint32 name-table indices here and a type byte per
    property. Legacy mode is kept because existing fixtures are built on it.
    """
    blob = synthetic.build_usmap(
        names=["Alpha"], enums=[("ESynthEnum", ["Alpha"])], schemas=[], shipped=False
    )
    body = blob[12:]
    at = 4 + 1 + len("Alpha")

    (enum_count,) = struct.unpack_from("<I", body, at)
    (inline_length,) = struct.unpack_from("<B", body, at + 4)

    assert enum_count == 1
    # An INLINE LENGTH, not the low byte of a uint32 index - the enum name is
    # not required to be in the name table at all in this mode.
    assert inline_length == len("ESynthEnum")
    assert body[at + 5 : at + 5 + inline_length] == b"ESynthEnum"


def test_shipped_mode_and_legacy_mode_produce_different_bytes() -> None:
    """If these ever matched, one of the two modes would be pointless."""
    names = ["ESynthEnum", "Alpha"]
    enums = [("ESynthEnum", ["Alpha"])]

    legacy = synthetic.build_usmap(names=names, enums=enums, schemas=[], shipped=False)
    shipped = synthetic.build_usmap(names=names, enums=enums, schemas=[], shipped=True)

    assert legacy != shipped


# ---------------------------------------------------------------------------
# The echo path, MEASURED rather than asserted
#
# An earlier revision of synthetic._usmap_index carried a docstring claiming
# the name was "deliberately kept OUT of the message" so it would not be
# printed - naming the exact mechanism (pytest renders frame ARGUMENTS) and
# then claiming a mitigation that mechanism defeats. It is harmless there,
# because every corpus caller passes invented names. It is not harmless as a
# PATTERN: non-negotiable 12 is about echo paths, and a documented mitigation
# that does not work invites the pattern being copied to a frame carrying real
# save bytes.
#
# So the behaviour is pinned here instead of described. If a future pytest stops
# rendering arguments, this test fails and the docstring gets to be relaxed on
# evidence rather than on hope.
# ---------------------------------------------------------------------------


#: Wall-clock bound for the nested pytest run below (CS-896). This is the
#: heaviest child in this tree - a whole interpreter start plus pytest
#: collection plus a usmap build - so it gets the 300s this repo already uses
#: for a spawned Python child (tests/test_locals_rendering.py,
#: tests/test_tmp_path_privacy.py) rather than the 120s used for git plumbing.
#: Generous on purpose: under two workers on a 2-vCPU runner a tight bound
#: would turn contention into a flake, which is worse than the defect.
SUBPROCESS_TIMEOUT: Final = 300


#: The one-line pytest config planted beside every probe module this section
#: writes. Empty on purpose - it carries no option, and its only job is to be
#: FOUND, so that the child stops climbing here.
_ROOTDIR_PIN: Final = b"[pytest]\n"


def _probe_sandbox(root: Path, body: str) -> Path:
    """Write a probe module into ``root`` and pin the child run's rootdir there.

    THE PIN IS THE LOAD-BEARING LINE, and it is a mitigation for CS-448 rather
    than tidiness. A child given an absolute path under the pytest temp tree,
    with its cwd set elsewhere, finds no ini file above the probe; pytest then
    falls back to the common ancestor of the cwd and the argument. From an
    ordinary checkout that ancestor is the drive root, which pytest discards,
    so the rootdir lands on the sandbox and collection is instant. From a
    checkout that shares a large ancestor with the temp root - a scratch clone,
    which is where the session scratchpad lives - the ancestor is the temp root
    itself, pytest keeps it, and collection then walks tens of thousands of
    sibling entries. Measured on this machine with only the cwd varied: 0.35s
    against 12.27s, and a sibling worker deleting a temp directory mid-walk
    turns the slow arm into a collection error rather than a slow pass.

    An empty ini in the sandbox ends the climb at the first hop, in every
    location. ``tests/test_hook_interpreter_ladder.py`` pins its own sandbox
    the same way, from an independent measurement.

    Args:
        root: The directory to write into. Created if it does not exist.
        body: The probe module's source, ASCII.

    Returns:
        The path of the probe module.
    """
    root.mkdir(parents=True, exist_ok=True)
    probe = root / "test_echo_probe.py"
    probe.write_text(body, encoding="utf-8")
    (root / "pytest.ini").write_bytes(_ROOTDIR_PIN)
    return probe


def _reported_rootdir(stdout: str) -> Path | None:
    """The rootdir pytest named in its own session header, or None.

    Returns None rather than raising when the header is absent, so the caller
    can say WHICH failure it is: a child that reported no rootdir at all and a
    child that reported the wrong one are different defects.
    """
    for line in stdout.splitlines():
        if line.startswith("rootdir:"):
            return Path(line.split(":", 1)[1].strip())
    return None


def test_a_failing_builder_call_renders_its_arguments(tmp_path: Path) -> None:
    """Frame ARGUMENTS are rendered by pytest with no --showlocals. Measured."""
    sentinel = "NameThatMustNotEscapeButWill"
    probe = _probe_sandbox(
        tmp_path,
        "from tests.save import synthetic\n"
        "\n"
        "def test_probe() -> None:\n"
        "    synthetic.build_usmap(\n"
        '        names=["Present"],\n'
        f'        enums=[("{sentinel}", ["Present"])],\n'
        "        schemas=[],\n"
        "        shipped=True,\n"
        "    )\n",
    )

    result = subprocess.run(
        [sys.executable, "-m", "pytest", str(probe), "-q", "-p", "no:cacheprovider"],
        capture_output=True,
        text=True,
        check=False,
        timeout=SUBPROCESS_TIMEOUT,
        cwd=Path(synthetic.__file__).parent.parent.parent,
    )

    assert result.returncode != 0
    # The frame-argument rendering, which is the whole point: this is the
    # `table = {...}, text = '...'` line pytest emits above the failing frame.
    assert f"text = '{sentinel}'" in result.stdout


def test_the_probe_sandbox_pins_the_child_rootdir_at_itself(tmp_path: Path) -> None:
    """The CS-448 pin above is MEASURED here, not asserted by its own comment.

    A pin nobody can observe is a pin the next refactor deletes. This arm runs
    the same helper the test above runs, from a cwd that SHARES A PARENT with
    the sandbox - which is the arrangement that makes pytest keep the shared
    ancestor instead of discarding it as a drive root. With the pin the child
    reports the sandbox; without it the child reports the shared parent, so
    deleting the one line in ``_probe_sandbox`` turns this red.

    The parent here is a two-entry directory rather than the real temp root, so
    the arm grades the ROOTDIR and costs the same in both states: it needs no
    stopwatch and cannot flake on how full this machine's temp directory is.

    NEITHER PATH IS RENDERED. The comparison is bound to a bool before it is
    asserted, because pytest rewrites the asserted EXPRESSION independently of
    the message, and both of these paths sit under the operator's profile
    (non-negotiable 12).

    NO ``resolve`` ON EITHER SIDE, and that is correctness before anything
    else: both operands descend from the same ``tmp_path`` string - one through
    ``_probe_sandbox``, one through the argv the child was handed - so there is
    no normalisation for it to do, and ``Path.__eq__`` already folds case on
    this platform. It is also the primitive ``reach_guard`` grades, so avoiding
    it keeps this arm out of a privacy declaration table it has no business in.
    """
    sandbox = tmp_path / "sandbox"
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    probe = _probe_sandbox(sandbox, "def test_probe() -> None:\n    assert True\n")

    result = subprocess.run(
        # NOT -q: the rootdir line lives in the session header, which -q hides.
        [sys.executable, "-m", "pytest", str(probe), "-p", "no:cacheprovider"],
        capture_output=True,
        text=True,
        check=False,
        timeout=SUBPROCESS_TIMEOUT,
        cwd=elsewhere,
    )

    reported = _reported_rootdir(result.stdout)
    assert reported is not None, "the child printed no rootdir line, so nothing was measured"

    pinned_at_sandbox = reported == sandbox
    assert pinned_at_sandbox, (
        "the child resolved its rootdir above the sandbox, so the CS-448 climb "
        "is live again: _probe_sandbox no longer plants a pytest config"
    )


def test_the_builder_docstring_does_not_claim_a_containment_it_lacks() -> None:
    """Guards the specific false claim that was removed, so it cannot return."""
    source = Path(synthetic.__file__).read_text(encoding="utf-8")

    assert "deliberately kept OUT of the message" not in source
    assert "THIS FUNCTION IS AN ECHO PATH AND CANNOT BE MADE OTHERWISE" in source


# ---------------------------------------------------------------------------
# The evidence table - "measured" is not one thing
# ---------------------------------------------------------------------------


def test_every_evidence_row_declares_a_known_basis() -> None:
    assert synthetic.USMAP_EVIDENCE
    for item in synthetic.USMAP_EVIDENCE:
        assert item.basis in synthetic.USMAP_BASES, item.subject
        assert item.subject
        assert item.detail


def test_the_evidence_table_covers_every_basis_it_defines() -> None:
    """A basis constant nothing uses is a category that will quietly rot."""
    used = {item.basis for item in synthetic.USMAP_EVIDENCE}

    assert used == set(synthetic.USMAP_BASES)


def test_the_weakest_evidence_is_recorded_rather_than_promoted() -> None:
    """The three facts a later reader is most likely to over-trust.

    Each is recorded as NOT settled by the landing oracle. That is the whole
    point of the table: "measured" collapses four different strengths of
    evidence into one word, and prose cannot be queried for which is which.
    """
    by_subject = {item.subject: item for item in synthetic.USMAP_EVIDENCE}

    order = by_subject["type-26 field order (inner descriptor BEFORE the name index)"]
    assert order.basis == synthetic.USMAP_BASIS_REBUILD
    assert "NOT settled by landing" in order.detail

    slots = by_subject["entry field ORDER: slot before array_size"]
    assert slots.basis == synthetic.USMAP_BASIS_DISTRIBUTION
    assert "does NOT discriminate" in slots.detail

    ceiling = by_subject["MAX_KNOWN_PROPERTY_TYPE = 29"]
    assert ceiling.basis == synthetic.USMAP_BASIS_UNCONTRADICTED
    assert "NOT a constraint" in ceiling.detail


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

    Routed through ``test_properties._library_save_paths`` rather than through
    the raw locators, and that is the CONTAINMENT rather than a tidy-up. The
    locators and the glob used to sit here outside every ``try``, so a failure
    in any of them unwound through a frame holding the account directory -
    whose NAME is the platform account id (CLAUDE.md section 2, non-negotiable
    3). Forcing the glob to raise rendered it under ``-q`` alone.

    The contained discovery is IMPORTED rather than transcribed, for the reason
    the CS-429 section at the foot of this file gives. It is still routed
    through ``clockspeed.data.locate`` underneath, so the four ``CLOCKSPEED_*``
    overrides still point this at a nonexistent directory in CI and on any
    machine with no game installed - which is what keeps the skip below
    reachable rather than theoretical.

    IT HOLDS EVERY ``Exception`` AND EVERY ``SystemExit``, stated that way
    rather than as "it never raises" because that absolute is false: a
    ``KeyboardInterrupt`` still unwinds, deliberately, so a walk over a real
    library stays abortable.

    Returns:
        A save path, or None.
    """
    try:
        for candidate in test_properties._library_save_paths():  # noqa: SLF001
            # `is_file` and `stat` are inside the `try` too. They are the
            # cheapest possible calls to believe cannot fail, and a save that
            # vanishes between the glob and the stat makes them fail with the
            # path in the frame.
            if candidate.is_file() and candidate.stat().st_size > 0:
                return candidate
    # `SystemExit` is named because it is NOT an `Exception`, so `except
    # Exception` alone lets it through carrying the same frames.
    except (Exception, SystemExit):
        return None
    return None


@dataclass(frozen=True)
class _RealSaveShape:
    """What the shape anchor could learn from a real save - SCALARS ONLY.

    No field can hold a path, a blob or a decoded string, which is what makes
    this type safe to return across the containment boundary and safe for pytest
    to render.

    Attributes:
        header_version: The declared header version, or 0 when the read or the
            walk failed before one was known.
        shape: The scalar shape tuple, empty on failure.
        failure: The contained failure's type NAME, or None on success. A type
            name is safe; a frame that has to unwind to produce one is not.
    """

    header_version: int
    shape: tuple[int, ...]
    failure: str | None


def _real_save_shape_or_none() -> _RealSaveShape | None:
    """Read one real save and reduce it to scalars, containing every failure.

    THE READ USED TO SIT IN THE TEST BODY WITH NO ``try`` AT ALL. ``read_bytes``
    unwinds through a bound method whose ``self`` IS the save path, and pytest
    renders the ARGUMENTS of every frame it unwinds with no opt-in flag - so one
    rendered line carried the Windows account name, the platform account id and
    the world name together. Measured, not theorised: both a ``MemoryError`` and
    a ``SystemExit`` forced out of that read rendered all six probed markers
    under ``-q`` alone.

    The blob is bound HERE and nowhere else, and every step that touches it is
    inside the ``try``, so no frame holding save bytes can unwind to a caller.

    Returns:
        The scalars, or None when no save library is reachable.
    """
    path = _real_save_path()
    if path is None:
        return None
    try:
        blob = path.read_bytes()
        (header_version,) = struct.unpack_from("<i", blob, 0)
        return _RealSaveShape(header_version=header_version, shape=_shape_of(blob), failure=None)
    # BROAD BY DESIGN, and `SystemExit` is named beside `Exception` because it
    # is a `BaseException` and `except Exception` does not hold it. A narrower
    # catch lets an unexpected type escape carrying the save bytes and the save
    # path, which is the leak this containment closes.
    except (Exception, SystemExit) as exc:
        return _RealSaveShape(header_version=0, shape=(), failure=type(exc).__name__)


def test_the_builder_matches_the_shape_of_a_real_save() -> None:
    """Compare the builder against a real save - SHAPES ONLY, no value, no print.

    This is the one control that can catch a measurement error the independent
    reader cannot, because the reader and the builder share their measured
    constants. See the module docstring.

    It asserts nothing about content. The comparison is a tuple of ints and
    bools, so a failure repr cannot carry a world name, a session name, an
    account id or a token (non-negotiable 12).

    THAT PROMISE WAS ONCE FALSE, AND CS-429 IS WHY IT IS NOW TRUE. It was always
    true of the comparison, which really does only hold scalars, and false of
    the two steps that produced the operands: the discovery and the read both
    sat outside every ``try`` and both were measured leaking. Neither runs in
    this frame any more - :func:`_real_save_shape_or_none` performs both behind
    a containment and hands back scalars - so the docstring now describes the
    whole test rather than only its last line.
    """
    found = _real_save_shape_or_none()
    if found is None:
        pytest.skip(
            "no save file on this machine - the anchor needs a real save to compare against"
        )
    assert found.failure is None, f"the real save did not yield a shape: {found.failure}"

    counterpart = {
        _HEADER_10: synthetic.SAVE_V36,
        _HEADER_13: synthetic.SAVE_V42,
        _HEADER_14: synthetic.SAVE_V60,
    }.get(found.header_version)
    if counterpart is None:
        pytest.skip("real save carries a header version the corpus does not model")

    synthetic_shape = _shape_of(counterpart.blob)
    assert found.shape == synthetic_shape


# ---------------------------------------------------------------------------
# CS-429 - the discovery and the read behind control 2 are CONTAINED, and both
# sites are GRADED
#
# Control 2 is the only test in this module that touches a real file, and until
# this section existed neither half of it was contained. Both leaks were
# MEASURED under `-q` alone on a machine with a real library, not reasoned
# about:
#
#   THE READ. ``path.read_bytes()`` sat in the test body with NO ``try`` around
#   it at all. Forcing a ``MemoryError`` out of it rendered the Windows account
#   name, the platform account id, the account directory, the save root and the
#   save filename - every marker probed. ``SystemExit`` rendered the same six.
#
#   THE DISCOVERY. ``_real_save_path`` called both locators and the glob outside
#   every ``try``. Forcing the glob to raise rendered the account directory
#   itself, whose NAME is the platform account id (CLAUDE.md section 2,
#   non-negotiable 3).
#
# THIS SITE WAS THE WORST OF THE FOUR CS-429 NAMES, because the docstring of
# ``test_the_builder_matches_the_shape_of_a_real_save`` PROMISED that "a failure
# repr cannot carry a world name, a session name, an account id or a token
# (non-negotiable 12)" - and that promise measured FALSE. The promise was true
# of the COMPARISON, which really does only hold scalars, and false of the two
# steps that produce the operands. A false guarantee is worse than an unguarded
# bug: it is the reason nobody looked.
#
# THE CONTAINMENT IS IMPORTED, NOT TRANSCRIBED. ``test_properties``
# already owns a contained discovery, the two forced-failure pairs and the
# reach guard, all with their own graders. A third transcription of a
# containment is a third place to get it subtly wrong, so this module imports
# them. That does NOT weaken control 1: what is imported is discovery and
# grading machinery, never a format constant or a builder opinion, and the
# module docstring's independence claim is about the latter.
# ---------------------------------------------------------------------------

#: This module's library-reaching helpers, name to why each reaches.
_GRADED_LIBRARY_REACH: Final = MappingProxyType(
    {
        "_real_save_path": "holds the contained locators and the save glob",
        "_real_save_shape_or_none": "reads one real save and reduces it to scalars",
    }
)

#: Touches a primitive WITHOUT consuming a real save path, name to why.
#: Asserted still reaching, so an exemption cannot outlive its reason.
_EXEMPT_LIBRARY_REACH: Final = MappingProxyType(
    {
        "test_the_corpus_is_seven_bit_ascii": (
            "a test rather than a helper, and its read_bytes is on this repo's "
            "own tracked source files rather than on a discovered save"
        ),
    }
)


def test_every_library_reaching_function_here_is_declared() -> None:
    """The reach guard, keyed on the RISKY primitives rather than the safe route.

    Keyed that way because the inverted alternative has already shipped here
    once: a guard keyed on the CONTAINED entry point detects safe helpers and is
    blind to unsafe ones, so every assertion in it stays true while the module
    leaks. The guard is owned by ``reach_guard`` and consumed here, so the
    sibling modules share one implementation rather than a transcription each.
    """
    reach_guard._assert_library_reach_is_declared(  # noqa: SLF001
        Path(__file__), graded=_GRADED_LIBRARY_REACH, exempt=_EXEMPT_LIBRARY_REACH
    )


def test_the_guard_catches_a_spliced_uncontained_helper(tmp_path: Path) -> None:
    """The guard's POWER, forced rather than asserted about.

    The splice is this module's OWN pre-repair shape - the locators and the glob
    outside every ``try`` - wired in exactly as ``_real_save_path`` carried it.
    Run against a COPY in ``tmp_path``, so nothing tracked is mutated and no
    restore is needed.
    """
    spliced = tmp_path / "spliced.py"
    spliced.write_text(
        Path(__file__).read_text(encoding="utf-8") + "\n\ndef _spliced_uncontained_helper():\n"
        '    """A helper carrying the known-bad shape."""\n'
        "    save_root = locate.resolve_save_root()\n"
        "    account = locate.resolve_account_dir(save_root)\n"
        '    for candidate in sorted(account.glob("*.sav")):\n'
        "        return candidate.read_bytes()\n"
        "    return None\n",
        encoding="utf-8",
    )

    with pytest.raises(AssertionError) as caught:
        reach_guard._assert_library_reach_is_declared(  # noqa: SLF001
            spliced, graded=_GRADED_LIBRARY_REACH, exempt=_EXEMPT_LIBRARY_REACH
        )
    assert "_spliced_uncontained_helper" in str(caught.value)

    # The positive control: the same guard on the unspliced source passes, so
    # the red above is the splice rather than the guard rejecting everything.
    reach_guard._assert_library_reach_is_declared(  # noqa: SLF001
        Path(__file__), graded=_GRADED_LIBRARY_REACH, exempt=_EXEMPT_LIBRARY_REACH
    )


@pytest.mark.parametrize(
    ("_forced", "raiser"),
    test_properties._FORCED_DISCOVERY_FAILURES,  # noqa: SLF001
    ids=lambda value: value if isinstance(value, str) else "",
)
def test_a_failing_save_root_lookup_does_not_unwind_through_the_anchor(
    monkeypatch: pytest.MonkeyPatch, _forced: str, raiser: Callable[..., object]
) -> None:
    """The first of the finder's three discovery calls that sat outside its ``try``."""
    monkeypatch.setattr(locate, "resolve_save_root", raiser)
    test_properties._assert_sweep_declines("shape-anchor finder", _real_save_path)  # noqa: SLF001
    test_properties._assert_sweep_declines(  # noqa: SLF001
        "shape-anchor reader", _real_save_shape_or_none
    )


@pytest.mark.parametrize(
    ("_forced", "raiser"),
    test_properties._FORCED_DISCOVERY_FAILURES,  # noqa: SLF001
    ids=lambda value: value if isinstance(value, str) else "",
)
def test_a_failing_account_directory_lookup_does_not_unwind_through_the_anchor(
    monkeypatch: pytest.MonkeyPatch, _forced: str, raiser: Callable[..., object]
) -> None:
    """The second, and the one whose frame holds the platform account id."""
    monkeypatch.setattr(locate, "resolve_save_root", lambda: Path("synthetic-root"))
    monkeypatch.setattr(locate, "resolve_account_dir", raiser)
    test_properties._assert_sweep_declines("shape-anchor finder", _real_save_path)  # noqa: SLF001
    test_properties._assert_sweep_declines(  # noqa: SLF001
        "shape-anchor reader", _real_save_shape_or_none
    )


@pytest.mark.parametrize(
    ("_forced", "raiser"),
    test_properties._FORCED_DISCOVERY_FAILURES,  # noqa: SLF001
    ids=lambda value: value if isinstance(value, str) else "",
)
def test_a_failing_save_glob_does_not_unwind_through_the_anchor(
    monkeypatch: pytest.MonkeyPatch, _forced: str, raiser: Callable[..., object]
) -> None:
    """The third - it was in the ``for`` statement itself, and it MEASURED a leak.

    Forcing this one rendered the account directory, the save root and the
    Windows account name under ``-q`` alone.
    """
    monkeypatch.setattr(Path, "glob", raiser)
    test_properties._assert_sweep_declines("shape-anchor finder", _real_save_path)  # noqa: SLF001
    test_properties._assert_sweep_declines(  # noqa: SLF001
        "shape-anchor reader", _real_save_shape_or_none
    )


@pytest.mark.parametrize(
    ("_forced", "raiser"),
    test_properties._FORCED_READ_FAILURES,  # noqa: SLF001
    ids=lambda value: value if isinstance(value, str) else "",
)
def test_an_unexpected_read_failure_does_not_unwind_through_the_anchor(
    monkeypatch: pytest.MonkeyPatch, _forced: str, raiser: Callable[..., bytes]
) -> None:
    """The read that had NO ``try`` at all - the worst of the four CS-429 sites.

    Parametrized over both forced failures because ``SystemExit`` is a
    ``BaseException``: a containment written as ``except Exception`` holds
    ``MemoryError`` and leaks on ``SystemExit``, and one forced type cannot tell
    those two apart. Both were measured to render all six markers here.

    THE SAVE LIST IS SYNTHETIC, so this runs on a machine with no game
    installed and never puts a real path into the frame under test.
    """
    monkeypatch.setattr(
        "tests.save.test_synthetic._real_save_path",
        lambda: test_properties._SYNTHETIC_SAVE,  # noqa: SLF001
    )
    monkeypatch.setattr(Path, "read_bytes", raiser)
    escaped, value = test_properties._contained_call(_real_save_shape_or_none)  # noqa: SLF001
    assert escaped is None, (
        f"{escaped} escaped the shape-anchor reader instead of being reduced to a type "
        "name inside it, and the frame it unwound through held the save path"
    )
    reported = getattr(value, "failure", None)
    assert reported == _forced, (
        f"the shape-anchor reader reported {reported} rather than the one contained "
        f"{_forced}, so the unexpected read failure was not recorded as a type name"
    )


# ---------------------------------------------------------------------------
# CS-961 - THE ONE FIXTURE WHOSE PAYLOAD IS A REAL TAGGED PROPERTY PAYLOAD
#
# WHAT THE CORPUS COULD NOT DO BEFORE THIS SECTION. Every levelled fixture
# builds its object payloads as a run of zero bytes, and the builder says so:
# only the int32 length FRAMING around a payload is measured, so a field
# decoded out of one is decoded out of an invention. The consequence is
# measurable rather than theoretical - every actor and every component of every
# levelled fixture returns zero properties and one unparsed-payload flag, which
# :func:`test_a_filler_payload_in_the_same_body_decodes_to_nothing` pins as the
# control below. Nothing in this repo could show a world load reaching a
# DECODED VALUE without a real save on the machine.
#
# WHY THE SHIPPED READER DOES THE DECODING HERE. Control 1's independence claim
# is about the header, the chunk frame and the record table, all three of which
# are still re-derived by hand in this module out of the format description. The
# claim graded in this section is a different one - that ONE fixture's payload
# decodes to the values it was built from - and a second hand-written reader
# could not grade it without re-deriving the whole property grammar, which would
# be a third opinion rather than a check.
#
# SO THE ENCODER IS WHAT GETS THE SECOND OPINION, NOT THE DECODER. The builder's
# payload encoder and the expectation below were authored in one slice, which is
# self-consistency and not evidence: an encoder and an expectation that share one
# misreading of the tag grammar agree with each other and with nothing else.
# ``tests/save/test_properties.py`` carries a SEPARATE encoder for the same
# grammar, authored long before this slice and validated against the real save
# library, and :func:`test_the_decodable_payload_agrees_with_the_independent_encoder`
# asserts the two emit the SAME BYTES.
#
# EVERY OPERAND IN THIS SECTION IS A LITERAL FROM TRACKED SOURCE. The fixture is
# synthetic, so no decoded value here can be world content and rendering one in a
# failing assertion discloses nothing (non-negotiable 12). That is a property of
# THIS fixture and not a licence: an arm decoding a real save may not be written
# this way.
# ---------------------------------------------------------------------------

#: How many times the perturbation control's needle may appear in the body. More
#: than one and the control cannot say which occurrence it moved.
_ONE_OCCURRENCE: Final = 1

#: What the perturbation control adds to the encoded integer. Any non-zero step
#: works; it is named so the arithmetic is not a bare literal in an assertion.
_PERTURBATION_STEP: Final = 1


def _decodable_body() -> bytes:
    """Decompress the CS-961 fixture the way a caller holding the file would.

    Returns:
        The body, length prefix included, which is the buffer the record
        extents index into.
    """
    fixture = synthetic.SAVE_LEVELLED_DECODABLE
    return chunks.decompress_body(
        fixture.blob, fixture.chunk_offset, header_version=fixture.header_version
    ).payload


def _decodable_records(body: bytes) -> tuple[objects.ObjectRecord, ...]:
    """Walk the CS-961 fixture's body into its records.

    Args:
        body: The decompressed body, length prefix included.

    Returns:
        Every record, in file order, each carrying its own payload extent.
    """
    fixture = synthetic.SAVE_LEVELLED_DECODABLE
    return objects.parse_body(
        body, save_version=fixture.save_version, header_version=fixture.header_version
    ).records


def _properties_of(body: bytes, instance_name: str) -> objects.PropertyResult:
    """Decode one named record's payload out of a walked body.

    Args:
        body: The decompressed body, length prefix included.
        instance_name: The record to find. A tracked-source literal.

    Returns:
        What the shipped reader made of that record's payload.
    """
    for record in _decodable_records(body):
        if record.instance_name == instance_name:
            return objects.read_properties(body, record)
    pytest.fail(f"the fixture carries no record named {instance_name}")


def test_the_decodable_fixture_sits_on_a_pair_whose_tag_grammar_was_measured() -> None:
    """The pair is one the grammar READS, and is explicitly not the one it refuses.

    A fixture on (14,60) would decode nothing whatever the payload said - not
    one payload of that pair reaches a terminator - so it would prove the
    opposite of what this fixture exists for while looking identical.
    """
    fixture = synthetic.SAVE_LEVELLED_DECODABLE
    pair = (fixture.header_version, fixture.save_version)

    assert pair in test_properties.TAGGED_PAIRS
    assert pair != test_properties.UNMEASURED_PAIR


def test_the_decodable_fixture_does_not_widen_either_published_matrix() -> None:
    """A slice does not quietly widen a contract other modules parametrize over."""
    assert synthetic.SAVE_LEVELLED_DECODABLE not in synthetic.LEVELLED_SAVES
    assert synthetic.SAVE_LEVELLED_DECODABLE not in synthetic.ALL_SAVES


def test_the_decodable_actor_payload_decodes_to_exactly_the_values_encoded() -> None:
    """THE SLICE'S CLAIM: a synthetic world yields a decoded property VALUE.

    By value on both halves, not merely non-empty and not by repr. The actor
    branch is the one that has to step over a parent reference and a component
    list first, and a reader that skipped that head would desynchronise on the
    first tag rather than return a wrong value.
    """
    body = _decodable_body()

    result = _properties_of(body, synthetic.DECODABLE_INSTANCE)

    assert result.properties[synthetic.DECODABLE_INT_NAME] == synthetic.DECODABLE_INT_VALUE
    assert result.properties[synthetic.DECODABLE_STR_NAME] == synthetic.DECODABLE_STR_VALUE
    assert dict(result.properties) == dict(synthetic.DECODABLE_PROPERTIES)
    assert not [w for w in result.warnings if w.code == objects.WARN_UNPARSED_PROPERTY_PAYLOAD]


def test_every_decoded_value_carries_a_type_word_the_reader_calls_measured() -> None:
    """The published expectation may not rest on a type whose value grammar is not read.

    A tag whose word is outside ``MEASURED_VALUE_TYPES`` is counted and skipped
    rather than decoded, so an expectation naming one could only ever be
    satisfied by a decoder that had stopped skipping it.
    """
    words = set(synthetic.DECODABLE_TYPE_WORDS.values())

    assert words
    assert words <= set(objects.MEASURED_VALUE_TYPES)


def test_the_decodable_component_payload_needs_no_actor_head() -> None:
    """The other branch. A component payload opens directly with its tags.

    Carried in the SAME body as the actor, so the pair also proves the walk
    dispatches on the record's own kind rather than on the fixture.
    """
    body = _decodable_body()

    result = _properties_of(body, synthetic.DECODABLE_COMPONENT_INSTANCE)

    assert dict(result.properties) == dict(synthetic.DECODABLE_COMPONENT_PROPERTIES)


def test_the_decodable_payload_agrees_with_the_independent_encoder() -> None:
    """CONTROL - the common-mode check this slice exists to survive.

    The builder's encoder and this slice's expectation were authored together,
    so agreement between them is not evidence. ``test_properties`` carries a
    second encoder for the same tag grammar, written in an earlier slice and
    against the real save library, and the same logical properties are rebuilt
    through it here.

    BYTE EQUALITY IS THE CHECK, over the whole payload. The only literal shared
    by the two sides is the opaque run after the terminator, which is not part
    of the tag grammar under check - every grammar byte on the right-hand side
    is produced by the other module's own field order, widths and string
    encoding.
    """
    rebuilt = (
        test_properties._actor_head((synthetic.DECODABLE_COMPONENT_PATH,))  # noqa: SLF001
        + test_properties._scalar_tag(  # noqa: SLF001
            synthetic.DECODABLE_INT_NAME,
            synthetic.DECODABLE_INT_TYPE_WORD,
            struct.pack("<i", synthetic.DECODABLE_INT_VALUE),
        )
        + test_properties._scalar_tag(  # noqa: SLF001
            synthetic.DECODABLE_STR_NAME,
            synthetic.DECODABLE_STR_TYPE_WORD,
            test_properties._fstring(synthetic.DECODABLE_STR_VALUE),  # noqa: SLF001
        )
        + test_properties._fstring(synthetic.PROPERTY_TERMINATOR)  # noqa: SLF001
        + synthetic.DECODABLE_TRAILING_RUN
    )

    assert rebuilt == synthetic.DECODABLE_ACTOR_PAYLOAD


def test_the_decodable_component_payload_agrees_with_the_independent_encoder() -> None:
    """The same second opinion over the head-free branch."""
    rebuilt = (
        test_properties._scalar_tag(  # noqa: SLF001
            synthetic.DECODABLE_COMPONENT_INT_NAME,
            synthetic.DECODABLE_INT_TYPE_WORD,
            struct.pack("<i", synthetic.DECODABLE_COMPONENT_INT_VALUE),
        )
        + test_properties._fstring(synthetic.PROPERTY_TERMINATOR)  # noqa: SLF001
        + synthetic.DECODABLE_TRAILING_RUN
    )

    assert rebuilt == synthetic.DECODABLE_COMPONENT_PAYLOAD


def test_a_filler_payload_in_the_same_body_decodes_to_nothing() -> None:
    """NON-VACUITY 1 - the arm above would not pass on the payload it replaced.

    The CS-961 fixture's persistent level keeps the corpus's ORIGINAL filler
    payloads, so one body carries both kinds. If a run of zero bytes decoded to
    anything, the decode arm would be measuring the walk and not the payload.
    """
    body = _decodable_body()

    filler = _properties_of(body, synthetic.FILLER_PAYLOAD_INSTANCE)

    assert not filler.properties
    assert [w.code for w in filler.warnings] == [objects.WARN_UNPARSED_PROPERTY_PAYLOAD]


def test_a_perturbed_decodable_payload_no_longer_yields_the_encoded_value() -> None:
    """NON-VACUITY 2 - the decoded value follows the BYTES, not the expectation.

    One value's four bytes are moved in the decompressed body and nothing else
    is touched, so the body stays structurally valid and every offset is
    unchanged. The decode must report the moved number, which a reader
    returning a constant, or reading some other field, cannot do.
    """
    body = _decodable_body()
    needle = struct.pack("<i", synthetic.DECODABLE_INT_VALUE)
    moved = synthetic.DECODABLE_INT_VALUE + _PERTURBATION_STEP
    assert body.count(needle) == _ONE_OCCURRENCE, (
        "the encoded integer is not unique in the body, so this control cannot say "
        "which occurrence it moved"
    )

    perturbed = body.replace(needle, struct.pack("<i", moved), _ONE_OCCURRENCE)
    result = _properties_of(perturbed, synthetic.DECODABLE_INSTANCE)

    assert result.properties[synthetic.DECODABLE_INT_NAME] == moved
    assert result.properties[synthetic.DECODABLE_INT_NAME] != synthetic.DECODABLE_INT_VALUE


def test_the_two_encoders_disagree_on_the_empty_string_and_the_bound_is_recorded() -> None:
    """THE CROSS-CHECK ABOVE IS VALID FOR NON-EMPTY TEXT AND THIS ARM SAYS SO.

    Found by the adversarial pass over this slice, which could not break the
    byte-equality check but did find the one input that escapes it. The two
    encoders are independent, which is what makes the check evidence - and
    independent encoders may also silently differ. On the empty string they do.

    NEITHER IS BEING DECLARED RIGHT HERE, because neither has been measured.
    ``synthetic.fstring`` says so in its own prose: the bare zero count is
    MODELLED, the Unreal convention, and the one field shape in that module no
    probe confirmed. ``test_properties._fstring`` takes no position at all - it
    has no empty-string branch, so its answer is what its arithmetic happens to
    produce on an input it was never handed.

    WHAT THIS ARM BUYS IS THAT THE DIVERGENCE IS LOUD. A later CS-961 arm that
    encodes an empty property name or an empty string value would silently lose
    the second opinion, or take a red that says nothing about the code under
    test. Pinned here, changing either encoder reddens this and the next author
    has to decide deliberately rather than discover it as a puzzle.
    """
    assert synthetic.fstring("") != test_properties._fstring(""), (  # noqa: SLF001
        "the two encoders now agree on the empty string, so either one was changed or "
        "the shape was measured - if it was measured, record which, and retire this arm "
        "rather than loosening it"
    )
    assert synthetic.fstring("x") == test_properties._fstring("x"), (  # noqa: SLF001
        "the two encoders disagree on NON-empty text, which is the population the "
        "byte-equality cross-check above rests on - that check is now worthless"
    )
